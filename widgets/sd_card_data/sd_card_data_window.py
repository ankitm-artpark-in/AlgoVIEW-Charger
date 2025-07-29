from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                             QMenu, QComboBox, QCheckBox, QPushButton, QFileDialog,
                             QFrame, QScrollArea, QListWidget, QListWidgetItem,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QDialog, QDialogButtonBox, QTextEdit, QTabWidget,
                             QAbstractItemView)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QBrush, QColor, QIcon
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
import re
from collections import defaultdict, deque

from serial_utils.send_frame import send_battery_query
from ..color_display_box import ColorBoxComboBox, ColorBoxDelegate
from dialogs import PasswordDialog
from dialogs import DataViewerDialog

class SDCardDataWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.charger_info_labels = {}
        self.saved_data = {}
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)
        
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # create left panel
        left_panel = self.create_left_panel()
        main_layout.addWidget(left_panel)

    def create_left_panel(self):
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_panel.setFixedWidth(550)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_panel.setLayout(left_layout)

        self.create_files_section(left_layout)
        self.create_charger_info_section(left_layout)
        self.create_saved_files_section(left_layout)
        left_layout.setStretchFactor(self.files_tree, 1)
        left_layout.setStretchFactor(self.charger_tree, 1)
        left_layout.setStretchFactor(self.saved_files_table, 1)
        
        return left_panel
    
    def create_saved_files_section(self, layout):
        # Header with import button
        saved_header_layout = QHBoxLayout()
        saved_header = QLabel("Saved Files")
        saved_header_layout.addWidget(saved_header)
        
        # Add Import CSV button
        self.import_btn = QPushButton("Import CSV")
        self.import_btn.setMaximumWidth(100)

        self.import_btn.clicked.connect(self.import_csv_file)
        saved_header_layout.addWidget(self.import_btn)
        saved_header_layout.addStretch()
        
        saved_header_widget = QWidget()
        saved_header_widget.setLayout(saved_header_layout)
        layout.addWidget(saved_header_widget)
        
        self.saved_files_table = QTableWidget()
        self.saved_files_table.setColumnCount(4)  # Added one more column for file source
        self.saved_files_table.setHorizontalHeaderLabels(["Battery ID", "Cycle", "Source", "Download Time"])
        
        header = self.saved_files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.saved_files_table.setColumnWidth(0, 80)
        self.saved_files_table.setColumnWidth(1, 60)
        self.saved_files_table.setColumnWidth(2, 80)
        
        self.saved_files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.saved_files_table.setSelectionMode(QTableWidget.SelectionMode.MultiSelection)
        self.saved_files_table.setAlternatingRowColors(True)
        
        self.saved_files_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.saved_files_table.customContextMenuRequested.connect(self.show_saved_files_context_menu)
        
        # Connect double-click to the data viewer
        self.saved_files_table.itemDoubleClicked.connect(self.view_saved_data)
        
        layout.addWidget(self.saved_files_table)

    def create_files_section(self, layout):
        files_header = QLabel("SD Card Files")
        files_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        layout.addWidget(files_header)
        
        self.files_tree = QTreeWidget()
        self.files_tree.setHeaderLabels(["File/Folder", "Cycle Count"])
        self.files_tree.setColumnWidth(0, 250)
        self.files_tree.setColumnWidth(1, 100)
        self.files_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.files_tree.customContextMenuRequested.connect(self.show_files_context_menu)

        self.populate_files_tree()
        layout.addWidget(self.files_tree)

    def create_charger_info_section(self, layout):
        charger_header = QLabel("Charger Info")
        charger_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; margin-top: 10px;")
        layout.addWidget(charger_header)
        
        self.charger_tree = QTreeWidget()
        self.charger_tree.setHeaderLabels(["Parameter", "Value"])
        self.charger_tree.setColumnWidth(0, 200)
        self.charger_tree.setColumnWidth(1, 150)
        
        self.populate_charger_info_tree()
        layout.addWidget(self.charger_tree)

    def populate_charger_info_tree(self):
        self.charger_info_labels.clear()
        self.charger_tree.clear()

        # CHARGER_INFO
        charger_info_params = ["Hardware Version", "Product ID", "Serial Number", "Firmware Version"]
        
        for param in charger_info_params:
            param_item = QTreeWidgetItem([param])
            self.charger_tree.addTopLevelItem(param_item)
            
            value_label = QLabel("--")
            value_label.setMinimumWidth(120)
            value_label.setStyleSheet("color: #2196F3;")
            value_label.setAlignment(Qt.AlignCenter)
            font = QFont()
            font.setBold(True)
            font.setPointSize(11)
            value_label.setFont(font)
            
            key = f"CHARGER_INFO_{param}"
            self.charger_info_labels[key] = value_label
            self.charger_tree.setItemWidget(param_item, 1, value_label)
        
        self.charger_tree.expandAll()

    def populate_files_tree(self):
        self.files_tree.clear()
        
        battery_ids = getattr(self.main_window, 'battery_ids', [])
        cycle_counts = getattr(self.main_window, 'cycle_counts', {})
        
        battery_root = QTreeWidgetItem(["Battery Data", ""])
        battery_root.setForeground(0, Qt.black)
        font = QFont()
        font.setBold(True)
        battery_root.setFont(0, font)
        self.files_tree.addTopLevelItem(battery_root)
        
        for battery_id in battery_ids:
            folder_name = f"Battery {battery_id}"
            battery_folder = QTreeWidgetItem([folder_name, ""])
            battery_root.addChild(battery_folder)
            
            if battery_id in cycle_counts:
                try:
                    cycle_count = int(cycle_counts[battery_id])
                    
                    if cycle_count > 0:
                        cycle_widget = QWidget()
                        cycle_layout = QHBoxLayout(cycle_widget)
                        cycle_layout.setContentsMargins(0, 0, 0, 0)
                        cycle_layout.setSpacing(5)
                        
                        cycle_combo = QComboBox()
                        cycle_combo.addItems([str(i) for i in range(1, cycle_count + 1)])
                        cycle_layout.addWidget(cycle_combo)
                        
                        download_btn = QPushButton("⬇")
                        download_btn.setMaximumWidth(30)
                        download_btn.clicked.connect(lambda checked, bid=battery_id, combo=cycle_combo: 
                                                self.download_cycle_data(bid, combo.currentText()))
                        cycle_layout.addWidget(download_btn)
                        
                        battery_folder.setText(1, "")
                        self.files_tree.setItemWidget(battery_folder, 1, cycle_widget)
                    else:
                        battery_folder.setText(1, "0")
                        battery_folder.setTextAlignment(1, Qt.AlignCenter)
                        
                except (ValueError, TypeError) as e:
                    print(f"Error converting cycle count for battery {battery_id}: {e}")
                    battery_folder.setText(1, "Error")
        
        self.files_tree.expandAll()

    def parse_csv_filename(self, filename):
        """Parse the CSV filename to extract battery ID, cycle number, and timestamp"""
        # Pattern: Battery_{battery_id}_Cycle_{cycle_number}_{timestamp}.csv
        pattern = r'Battery_(\d+)_Cycle_(\d+)_(.+)\.csv'
        match = re.match(pattern, filename)
        
        if match:
            battery_id = match.group(1)
            cycle_number = match.group(2)
            timestamp = match.group(3)
            return battery_id, cycle_number, timestamp
        return None, None, None

    def import_csv_file(self):
        """Import CSV file and add it to saved files"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self,
            "Import CSV File",
            "",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                # Extract filename from path
                filename = os.path.basename(file_path)
                
                # Parse filename to get battery ID, cycle number, and timestamp
                battery_id, cycle_number, timestamp = self.parse_csv_filename(filename)
                
                if battery_id is None or cycle_number is None:
                    # If filename doesn't match expected pattern, ask user for details
                    reply = QMessageBox.question(
                        self,
                        "Filename Format",
                        f"The filename '{filename}' doesn't match the expected format.\n"
                        "Expected format: Battery_{{ID}}_Cycle_{{Number}}_{{timestamp}}.csv\n\n"
                        "Do you want to continue with manual entry?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.Yes:
                        # Create a simple dialog for manual entry
                        from PySide6.QtWidgets import QInputDialog
                        battery_id, ok1 = QInputDialog.getText(self, "Battery ID", "Enter Battery ID:")
                        if not ok1 or not battery_id:
                            return
                        
                        cycle_number, ok2 = QInputDialog.getText(self, "Cycle Number", "Enter Cycle Number:")
                        if not ok2 or not cycle_number:
                            return
                        
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                    else:
                        return
                
                # Check if data already exists
                if self.is_data_already_saved(battery_id, cycle_number):
                    reply = QMessageBox.question(
                        self,
                        "Data Exists",
                        f"Data for Battery {battery_id} - Cycle {cycle_number} already exists.\n"
                        "Do you want to replace it?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    
                    if reply == QMessageBox.StandardButton.No:
                        return
                    else:
                        # Remove existing entry
                        self.remove_saved_data(battery_id, cycle_number)
                
                # Read CSV file
                df = pd.read_csv(file_path)
                
                # Convert DataFrame to dictionary format similar to downloaded data
                csv_data = {
                    'csv_data': df,
                    'import_time': datetime.now().isoformat(),
                    'import_filename': filename,
                    'file_path': file_path
                }
                
                # Add to saved data
                key = (str(battery_id), str(cycle_number))
                self.saved_data[key] = csv_data
                
                # Add entry to saved files table
                self.add_saved_file_entry_from_import(battery_id, cycle_number, timestamp)
                
                QMessageBox.information(
                    self,
                    "Import Successful",
                    f"Successfully imported data for Battery {battery_id} - Cycle {cycle_number}"
                )
                
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "Import Error",
                    f"Failed to import CSV file:\n{str(e)}"
                )

    def remove_saved_data(self, battery_id, cycle_number):
        """Remove existing saved data entry"""
        key = (str(battery_id), str(cycle_number))
        if key in self.saved_data:
            del self.saved_data[key]
        
        # Remove from table
        for row in range(self.saved_files_table.rowCount()):
            if (self.saved_files_table.item(row, 0).text() == str(battery_id) and 
                self.saved_files_table.item(row, 1).text() == str(cycle_number)):
                self.saved_files_table.removeRow(row)
                break

    def add_saved_file_entry_from_import(self, battery_id, cycle_number, timestamp):
        """Add entry to saved files table for imported data"""
        row_count = self.saved_files_table.rowCount()
        self.saved_files_table.insertRow(row_count)
        
        self.saved_files_table.setItem(row_count, 0, QTableWidgetItem(str(battery_id)))
        self.saved_files_table.setItem(row_count, 1, QTableWidgetItem(str(cycle_number)))
        self.saved_files_table.setItem(row_count, 2, QTableWidgetItem("Imported"))
        
        # Format timestamp for display
        try:
            # Try to parse timestamp and format it nicely
            if '_' in timestamp:
                # Format: YYYYMMDD_HHMMSS
                dt = datetime.strptime(timestamp, '%Y%m%d_%H%M%S')
                display_time = dt.strftime('%Y-%m-%d %H:%M:%S')
            else:
                display_time = timestamp
        except:
            display_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.saved_files_table.setItem(row_count, 3, QTableWidgetItem(display_time))
        
        # Center align the first three columns
        self.saved_files_table.item(row_count, 0).setTextAlignment(Qt.AlignCenter)
        self.saved_files_table.item(row_count, 1).setTextAlignment(Qt.AlignCenter)
        self.saved_files_table.item(row_count, 2).setTextAlignment(Qt.AlignCenter)
        
        # Color code imported files differently
        for col in range(4):
            item = self.saved_files_table.item(row_count, col)
            item.setBackground(QColor(230, 255, 230))  # Light green background for imported files

    def is_data_already_saved(self, battery_id, cycle_number):
        # Checks if combination already exists
        key = (str(battery_id), str(cycle_number))
        return key in self.saved_data

    def add_saved_file_entry(self, battery_id, cycle_number, data=None):
        # Add entry to saved files (for downloaded data)
        if self.is_data_already_saved(battery_id, cycle_number):
            return False
        
        # Add to saved_data dictionary
        key = (str(battery_id), str(cycle_number))
        self.saved_data[key] = data or {}
        
        row_count = self.saved_files_table.rowCount()
        self.saved_files_table.insertRow(row_count)
        
        self.saved_files_table.setItem(row_count, 0, QTableWidgetItem(str(battery_id)))
        self.saved_files_table.setItem(row_count, 1, QTableWidgetItem(str(cycle_number)))
        self.saved_files_table.setItem(row_count, 2, QTableWidgetItem("Downloaded"))
        self.saved_files_table.setItem(row_count, 3, QTableWidgetItem(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        self.saved_files_table.item(row_count, 0).setTextAlignment(Qt.AlignCenter)
        self.saved_files_table.item(row_count, 1).setTextAlignment(Qt.AlignCenter)
        self.saved_files_table.item(row_count, 2).setTextAlignment(Qt.AlignCenter)
        
        return True

    def view_saved_data(self, item):
        """Open data viewer dialog when double-clicking on saved file"""
        row = item.row()
        battery_id = self.saved_files_table.item(row, 0).text()
        cycle_number = self.saved_files_table.item(row, 1).text()
        
        key = (battery_id, cycle_number)
        if key in self.saved_data:
            # Open the data viewer dialog as non-modal
            dialog = DataViewerDialog(battery_id, cycle_number, self.saved_data[key], self.main_window, self)
            dialog.setModal(False)  # Make dialog non-modal
            dialog.show()  # Use show() instead of exec() for non-modal
        else:
            QMessageBox.warning(
                self,
                "Data Not Found",
                f"No data found for Battery {battery_id} - Cycle {cycle_number}"
            )
        
    def show_saved_files_context_menu(self, position):
        menu = QMenu()
        row = self.saved_files_table.rowAt(position.y())
        
        if row >= 0:
            view_action = menu.addAction("View Data")
            delete_action = menu.addAction("Delete")
            menu.addSeparator()
            
        import_action = menu.addAction("Import CSV")
        clear_all_action = menu.addAction("Clear All")
        
        action = menu.exec_(self.saved_files_table.viewport().mapToGlobal(position))
        
        if action:
            if action.text() == "View Data" and row >= 0:
                # Create a dummy item to pass to view_saved_data
                dummy_item = type('', (), {'row': lambda: row})()
                self.view_saved_data(dummy_item)
            elif action.text() == "Delete" and row >= 0:
                self.delete_saved_file_row(row)
            elif action.text() == "Import CSV":
                self.import_csv_file()
            elif action.text() == "Clear All":
                self.clear_all_saved_files()

    def delete_saved_file_row(self, row):
        if row >= 0 and row < self.saved_files_table.rowCount():
            battery_id = self.saved_files_table.item(row, 0).text()
            cycle_number = self.saved_files_table.item(row, 1).text()
            
            key = (battery_id, cycle_number)
            if key in self.saved_data:
                del self.saved_data[key]
            
            self.saved_files_table.removeRow(row)

    def clear_all_saved_files(self):
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear all saved files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.saved_data.clear()
            self.saved_files_table.setRowCount(0)

    def show_files_context_menu(self, position):
        menu = QMenu()
        item = self.files_tree.itemAt(position)
        
        if item:
            if item.parent() is None:
                refresh_action = menu.addAction("Refresh Folder")
            else:  # File item
                open_action = menu.addAction("Open")
                delete_action = menu.addAction("Delete")
        else:
            refresh_action = menu.addAction("Refresh")
            
        action = menu.exec_(self.files_tree.viewport().mapToGlobal(position))
        
        if item and action:
            if action.text() == "Open":
                pass
            elif action.text() == "Delete":
                pass
            elif action.text() == "Refresh" or action.text() == "Refresh Folder":
                self.populate_files_tree()
            
    def download_cycle_data(self, battery_id, cycle_number):
        """Download cycle data and immediately show data viewer dialog"""
        serial_obj = self.get_serial_obj()
        if serial_obj and serial_obj.is_open:
            try:
                # Query additional data via serial
                data = send_battery_query(serial_obj, self, battery_id, cycle_number)
                
                if data is None:
                    data = {}
                
                # Add export time metadata
                data['export_time'] = datetime.now().isoformat()
                
                # Immediately show the data viewer dialog as non-modal
                dialog = DataViewerDialog(battery_id, cycle_number, data, self.main_window, self)
                dialog.setModal(False)  # Make dialog non-modal
                dialog.show()  # Use show() instead of exec() for non-modal
                
            except Exception as e:
                QMessageBox.warning(self, "Download Error", f"Failed to download data: {str(e)}")
        else:
            QMessageBox.warning(self, "Connection Error", "Serial connection is not available.")
            
    def update_files_tree(self):
        if hasattr(self, 'files_tree'):
            self.populate_files_tree()
            
    def get_serial_obj(self):
        return self.main_window.serial_obj
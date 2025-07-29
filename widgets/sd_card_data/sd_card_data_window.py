from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                             QMenu, QComboBox, QCheckBox, QPushButton, QFileDialog,
                             QFrame, QScrollArea, QListWidget, QListWidgetItem,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
                             QDialog, QDialogButtonBox, QTextEdit, QTabWidget,
                             QAbstractItemView)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QBrush, QColor, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import os
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
        self.saved_data = {}  # To store saved data
        self.file_checkboxes = {}  # To store checkbox references
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)
        
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Create left and right panels
        left_panel = self.create_left_panel()
        # right_panel = self.create_right_panel()

        main_layout.addWidget(left_panel)
        # main_layout.addWidget(right_panel, stretch=1)

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
        saved_header = QLabel("Saved Files")
        saved_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; margin-top: 10px;")
        layout.addWidget(saved_header)
        
        self.saved_files_table = QTableWidget()
        self.saved_files_table.setColumnCount(4)  # Added one more column for checkbox
        self.saved_files_table.setHorizontalHeaderLabels(["Select", "Battery ID", "Cycle", "Download Time"])
        
        header = self.saved_files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.saved_files_table.setColumnWidth(0, 60)
        self.saved_files_table.setColumnWidth(1, 80)
        self.saved_files_table.setColumnWidth(2, 60)
        
        self.saved_files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
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

    def create_right_panel(self):
        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        controls_layout = self.create_plot_controls()
        right_layout.addLayout(controls_layout)

        self.create_plot_canvas()
        right_layout.addWidget(self.canvas)
        
        return right_panel

    def create_plot_controls(self):
        controls_layout = QHBoxLayout()
        
        # X-axis dropdown
        x_label = QLabel("X-axis:")
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.setMinimumWidth(150)
        self.x_axis_combo.currentTextChanged.connect(self.update_plot)
        
        # Y-axis dropdown
        y_label = QLabel("Y-axis:")
        self.y_axis_combo = QComboBox()
        self.y_axis_combo.setMinimumWidth(150)
        self.y_axis_combo.currentTextChanged.connect(self.update_plot)
        
        # Plot button
        self.plot_btn = QPushButton("Plot")
        self.plot_btn.clicked.connect(self.update_plot)
        
        # Clear button
        self.clear_btn = QPushButton("Clear Plot")
        self.clear_btn.clicked.connect(self.clear_data)
        
        controls_layout.addWidget(x_label)
        controls_layout.addWidget(self.x_axis_combo)
        controls_layout.addWidget(y_label)
        controls_layout.addWidget(self.y_axis_combo)
        controls_layout.addWidget(self.plot_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addStretch()
        
        # Initialize with common parameter names as placeholders
        self.initialize_default_parameters()
        
        return controls_layout

    def initialize_default_parameters(self):
        """Initialize dropdowns with common battery parameter names"""
        # Common battery monitoring parameters
        default_params = [
            "voltage", "current", "temperature", "capacity", "charge_level",
            "time", "timestamp", "cycle_count", "resistance", "power",
            "energy", "soc", "cell_voltage", "pack_voltage", "cell_temp"
        ]
        
        self.x_axis_combo.addItems(default_params)
        self.y_axis_combo.addItems(default_params)
        
        # Set reasonable defaults
        if "time" in default_params:
            self.x_axis_combo.setCurrentText("time")
        if "voltage" in default_params:
            self.y_axis_combo.setCurrentText("voltage")

    def create_plot_canvas(self):
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Parameter Value')
        self.ax.set_title('SD Card Data Parameter Monitoring')
        self.ax.grid(True, alpha=0.3)
        
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

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

    def is_data_already_saved(self, battery_id, cycle_number):
        # Checks if combination already exists
        key = (str(battery_id), str(cycle_number))
        return key in self.saved_data

    def add_saved_file_entry(self, battery_id, cycle_number, data=None):
        # Add entry to saved files
        if self.is_data_already_saved(battery_id, cycle_number):
            return False
        
        # Add to saved_data dictionary
        key = (str(battery_id), str(cycle_number))
        self.saved_data[key] = data or {}
        
        row_count = self.saved_files_table.rowCount()
        self.saved_files_table.insertRow(row_count)
        
        # Add checkbox in first column
        checkbox = QCheckBox()
        checkbox.stateChanged.connect(self.on_checkbox_changed)
        self.saved_files_table.setCellWidget(row_count, 0, checkbox)
        self.file_checkboxes[key] = checkbox
        
        self.saved_files_table.setItem(row_count, 1, QTableWidgetItem(str(battery_id)))
        self.saved_files_table.setItem(row_count, 2, QTableWidgetItem(str(cycle_number)))
        self.saved_files_table.setItem(row_count, 3, QTableWidgetItem(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        self.saved_files_table.item(row_count, 1).setTextAlignment(Qt.AlignCenter)
        self.saved_files_table.item(row_count, 2).setTextAlignment(Qt.AlignCenter)
        
        # Update dropdown options with actual data parameters
        self.update_dropdown_options()
        
        return True

    def on_checkbox_changed(self):
        """Called when any checkbox state changes"""
        self.update_dropdown_options()

    def get_selected_files_data(self):
        """Get data from all selected (checked) files"""
        selected_data = {}
        for key, checkbox in self.file_checkboxes.items():
            if checkbox.isChecked() and key in self.saved_data:
                selected_data[key] = self.saved_data[key]
        return selected_data

    def get_all_column_headers(self, selected_data):
        """Get all unique column headers from selected data, excluding timestamp parameters"""
        headers = set()
        timestamp_keywords = ['time', 'timestamp', 'date', 'export_time']
        
        for data in selected_data.values():
            if isinstance(data, dict):
                # Filter out timestamp-related keys
                filtered_keys = [key for key in data.keys() 
                               if not any(keyword in key.lower() for keyword in timestamp_keywords)]
                headers.update(filtered_keys)
            elif isinstance(data, pd.DataFrame):
                # Filter out timestamp-related columns
                filtered_columns = [col for col in data.columns.tolist() 
                                  if not any(keyword in col.lower() for keyword in timestamp_keywords)]
                headers.update(filtered_columns)
        return sorted(list(headers))

    def update_dropdown_options(self):
        """Update dropdown options based on selected files"""
        selected_data = self.get_selected_files_data()
        
        if not selected_data:
            # If no files are selected, keep the default parameters
            return
            
        headers = self.get_all_column_headers(selected_data)
        
        if headers:
            # Store current selections
            current_x = self.x_axis_combo.currentText()
            current_y = self.y_axis_combo.currentText()
            
            # Clear and update dropdowns
            self.x_axis_combo.clear()
            self.y_axis_combo.clear()
            
            self.x_axis_combo.addItems(headers)
            self.y_axis_combo.addItems(headers)
            
            # Restore previous selections if they still exist
            x_index = self.x_axis_combo.findText(current_x)
            y_index = self.y_axis_combo.findText(current_y)
            
            if x_index >= 0:
                self.x_axis_combo.setCurrentIndex(x_index)
            elif headers:
                self.x_axis_combo.setCurrentIndex(0)
                
            if y_index >= 0:
                self.y_axis_combo.setCurrentIndex(y_index)
            elif len(headers) > 1:
                self.y_axis_combo.setCurrentIndex(1)

    def update_plot(self):
        """Update the plot based on selected dropdowns and checked files"""
        x_column = self.x_axis_combo.currentText()
        y_column = self.y_axis_combo.currentText()
        
        if not x_column or not y_column:
            return
            
        selected_data = self.get_selected_files_data()
        if not selected_data:
            # Show message that no files are selected
            self.ax.clear()
            self.ax.text(0.5, 0.5, 'No files selected for plotting.\nCheck files in the Saved Files section.', 
                        horizontalalignment='center', verticalalignment='center', 
                        transform=self.ax.transAxes, fontsize=12)
            self.ax.set_xlabel(x_column)
            self.ax.set_ylabel(y_column)
            self.ax.set_title(f'{y_column} vs {x_column}')
            self.canvas.draw()
            return
            
        self.ax.clear()
        
        colors = ['blue', 'red', 'green', 'orange', 'purple', 'brown', 'pink', 'gray']
        color_idx = 0
        plots_created = False
        
        for key, data in selected_data.items():
            battery_id, cycle = key
            
            try:
                if isinstance(data, dict):
                    if x_column in data and y_column in data:
                        x_data = data[x_column]
                        y_data = data[y_column]
                        
                        # Skip if data contains timestamp strings
                        if self.is_timestamp_data(x_data) or self.is_timestamp_data(y_data):
                            print(f"Skipping timestamp data for {key}: {x_column} vs {y_column}")
                            continue
                        
                        # Convert to numpy arrays if they're lists
                        if isinstance(x_data, list):
                            x_data = np.array(x_data)
                        if isinstance(y_data, list):
                            y_data = np.array(y_data)
                            
                        # Ensure data is numeric
                        try:
                            x_data = np.asarray(x_data, dtype=float)
                            y_data = np.asarray(y_data, dtype=float)
                        except (ValueError, TypeError):
                            print(f"Skipping non-numeric data for {key}: {x_column} vs {y_column}")
                            continue
                            
                        label = f"Battery {battery_id} - Cycle {cycle}"
                        color = colors[color_idx % len(colors)]
                        self.ax.plot(x_data, y_data, label=label, color=color, marker='o', markersize=2)
                        color_idx += 1
                        plots_created = True
                        
                elif isinstance(data, pd.DataFrame):
                    if x_column in data.columns and y_column in data.columns:
                        x_data = data[x_column]
                        y_data = data[y_column]
                        
                        # Skip if data contains timestamp strings
                        if self.is_timestamp_data(x_data) or self.is_timestamp_data(y_data):
                            print(f"Skipping timestamp data for {key}: {x_column} vs {y_column}")
                            continue
                            
                        # Ensure data is numeric
                        try:
                            x_data = pd.to_numeric(x_data, errors='coerce')
                            y_data = pd.to_numeric(y_data, errors='coerce')
                            
                            # Remove NaN values
                            mask = ~(x_data.isna() | y_data.isna())
                            x_data = x_data[mask]
                            y_data = y_data[mask]
                            
                            if len(x_data) == 0:
                                print(f"No valid numeric data for {key}: {x_column} vs {y_column}")
                                continue
                                
                        except Exception:
                            print(f"Skipping non-numeric data for {key}: {x_column} vs {y_column}")
                            continue
                        
                        label = f"Battery {battery_id} - Cycle {cycle}"
                        color = colors[color_idx % len(colors)]
                        self.ax.plot(x_data, y_data, label=label, color=color, marker='o', markersize=2)
                        color_idx += 1
                        plots_created = True
                        
            except Exception as e:
                print(f"Error plotting data for {key}: {e}")
                continue
        
        self.ax.set_xlabel(x_column)
        self.ax.set_ylabel(y_column)
        self.ax.set_title(f'{y_column} vs {x_column}')
        self.ax.grid(True, alpha=0.3)
        
        # Only show legend if there are plots
        if plots_created:
            self.ax.legend()
        else:
            # Show message when no valid data found
            self.ax.text(0.5, 0.5, f'No valid numeric data found for\n{x_column} vs {y_column}', 
                        horizontalalignment='center', verticalalignment='center', 
                        transform=self.ax.transAxes, fontsize=12)
            
        self.canvas.draw()

    def is_timestamp_data(self, data):
        """Check if data contains timestamp strings"""
        if isinstance(data, (list, np.ndarray)):
            if len(data) > 0:
                sample = data[0] if isinstance(data, (list, np.ndarray)) else data
                if isinstance(sample, str):
                    # Check if it looks like a timestamp
                    timestamp_patterns = ['T', ':', '-', 'Z']
                    return any(pattern in str(sample) for pattern in timestamp_patterns) and len(str(sample)) > 10
        elif isinstance(data, pd.Series):
            if len(data) > 0:
                sample = data.iloc[0]
                if isinstance(sample, str):
                    timestamp_patterns = ['T', ':', '-', 'Z']
                    return any(pattern in str(sample) for pattern in timestamp_patterns) and len(str(sample)) > 10
        elif isinstance(data, str):
            timestamp_patterns = ['T', ':', '-', 'Z']
            return any(pattern in data for pattern in timestamp_patterns) and len(data) > 10
        return False

    def view_saved_data(self, item):
        """Open data viewer dialog when double-clicking on saved file"""
        row = item.row()
        battery_id = self.saved_files_table.item(row, 1).text()
        cycle_number = self.saved_files_table.item(row, 2).text()
        
        key = (battery_id, cycle_number)
        if key in self.saved_data:
            # Open the data viewer dialog
            dialog = DataViewerDialog(battery_id, cycle_number, self.saved_data[key], self.main_window, self)
            dialog.exec()
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
            
        clear_all_action = menu.addAction("Clear All")
        
        action = menu.exec_(self.saved_files_table.viewport().mapToGlobal(position))
        
        if action:
            if action.text() == "View Data" and row >= 0:
                # Create a dummy item to pass to view_saved_data
                dummy_item = type('', (), {'row': lambda: row})()
                self.view_saved_data(dummy_item)
            elif action.text() == "Delete" and row >= 0:
                self.delete_saved_file_row(row)
            elif action.text() == "Clear All":
                self.clear_all_saved_files()

    def delete_saved_file_row(self, row):
        if row >= 0 and row < self.saved_files_table.rowCount():
            battery_id = self.saved_files_table.item(row, 1).text()
            cycle_number = self.saved_files_table.item(row, 2).text()
            
            key = (battery_id, cycle_number)
            if key in self.saved_data:
                del self.saved_data[key]
            if key in self.file_checkboxes:
                del self.file_checkboxes[key]
            
            self.saved_files_table.removeRow(row)
            self.update_dropdown_options()

    def clear_all_saved_files(self):
        reply = QMessageBox.question(
            self,
            "Clear All",
            "Are you sure you want to clear all saved files?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            self.saved_data.clear()
            self.file_checkboxes.clear()
            self.saved_files_table.setRowCount(0)
            # Reset to default parameters
            self.x_axis_combo.clear()
            self.y_axis_combo.clear()
            self.initialize_default_parameters()

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

    def on_mouse_move(self, event):
        pass

    def clear_data(self):
        """Clear the plot"""
        self.ax.clear()
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Parameter Value')
        self.ax.set_title('SD Card Data Parameter Monitoring')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
            
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
                
                # Immediately show the data viewer dialog
                dialog = DataViewerDialog(battery_id, cycle_number, data, self.main_window, self)
                dialog.exec()
                
            except Exception as e:
                QMessageBox.warning(self, "Download Error", f"Failed to download data: {str(e)}")
        else:
            QMessageBox.warning(self, "Connection Error", "Serial connection is not available.")
            
    def update_files_tree(self):
        if hasattr(self, 'files_tree'):
            self.populate_files_tree()
            
    def get_serial_obj(self):
        return self.main_window.serial_obj
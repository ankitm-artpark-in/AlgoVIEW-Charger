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


class DataViewerDialog(QDialog):
    """Dialog to display saved data in tabular format"""
    
    def __init__(self, battery_id, cycle_number, data, parent=None):
        super().__init__(parent)
        self.battery_id = battery_id
        self.cycle_number = cycle_number
        self.data = data
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Data Viewer - Battery {self.battery_id} - Cycle {self.cycle_number}")
        self.setModal(True)
        self.resize(800, 600)
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Header info
        header_label = QLabel(f"Battery ID: {self.battery_id} | Cycle: {self.cycle_number}")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px; background-color: #f0f0f0;")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # Create tab widget for different data views
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)
        
        # Load and display data
        self.load_data_tabs()
        
        # Button box
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.close)
        
        # Add export button
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_current_tab)
        button_box.addButton(export_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
        
    def load_data_tabs(self):
        """Load data into different tabs based on data structure"""
        if not self.data:
            self.add_empty_tab("No Data Available")
            return
            
        # Check if CSV file exists and load it
        csv_file = self.data.get('csv_file')
        if csv_file and os.path.exists(csv_file):
            self.add_csv_data_tab(csv_file)
        
        # Add serial query data tab if available
        serial_data = {k: v for k, v in self.data.items() 
                      if k not in ['csv_file', 'export_time']}
        if serial_data:
            self.add_serial_data_tab(serial_data)
            
        # Add metadata tab
        self.add_metadata_tab()
        
    def add_csv_data_tab(self, csv_file):
        """Add tab with CSV data"""
        try:
            df = pd.read_csv(csv_file)
            table_widget = self.create_table_from_dataframe(df)
            self.tab_widget.addTab(table_widget, f"CSV Data ({len(df)} rows)")
        except Exception as e:
            error_widget = QTextEdit()
            error_widget.setPlainText(f"Error loading CSV file: {str(e)}")
            error_widget.setReadOnly(True)
            self.tab_widget.addTab(error_widget, "CSV Data (Error)")
            
    def add_serial_data_tab(self, serial_data):
        """Add tab with serial query data"""
        if not serial_data:
            return
            
        # Convert serial data to tabular format
        table_widget = QTableWidget()
        
        # Flatten nested dictionaries and lists
        flattened_data = self.flatten_data(serial_data)
        
        if flattened_data:
            table_widget.setRowCount(len(flattened_data))
            table_widget.setColumnCount(2)
            table_widget.setHorizontalHeaderLabels(["Parameter", "Value"])
            
            for row, (key, value) in enumerate(flattened_data.items()):
                table_widget.setItem(row, 0, QTableWidgetItem(str(key)))
                table_widget.setItem(row, 1, QTableWidgetItem(str(value)))
                
            # Resize columns
            table_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            table_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            
            # Make read-only
            table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
            table_widget.setAlternatingRowColors(True)
            
        self.tab_widget.addTab(table_widget, f"Serial Data ({len(flattened_data)} params)")
        
    def add_metadata_tab(self):
        """Add tab with file metadata"""
        metadata_widget = QTableWidget()
        metadata_items = [
            ("Battery ID", self.battery_id),
            ("Cycle Number", self.cycle_number),
            ("CSV File", self.data.get('csv_file', 'N/A')),
            ("Export Time", self.data.get('export_time', 'N/A')),
            ("File Size", self.get_file_size()),
            ("Data Keys", ', '.join(self.data.keys()) if self.data else 'None')
        ]
        
        metadata_widget.setRowCount(len(metadata_items))
        metadata_widget.setColumnCount(2)
        metadata_widget.setHorizontalHeaderLabels(["Property", "Value"])
        
        for row, (key, value) in enumerate(metadata_items):
            metadata_widget.setItem(row, 0, QTableWidgetItem(str(key)))
            metadata_widget.setItem(row, 1, QTableWidgetItem(str(value)))
            
        metadata_widget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        metadata_widget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        metadata_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        
        self.tab_widget.addTab(metadata_widget, "Metadata")
        
    def add_empty_tab(self, message):
        """Add tab with empty message"""
        empty_widget = QTextEdit()
        empty_widget.setPlainText(message)
        empty_widget.setReadOnly(True)
        empty_widget.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(empty_widget, "No Data")
        
    def create_table_from_dataframe(self, df):
        """Create QTableWidget from pandas DataFrame"""
        table_widget = QTableWidget()
        table_widget.setRowCount(len(df))
        table_widget.setColumnCount(len(df.columns))
        table_widget.setHorizontalHeaderLabels(df.columns.tolist())
        
        # Populate table
        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                if pd.isna(value):
                    value = ""
                table_widget.setItem(row, col, QTableWidgetItem(str(value)))
                
        # Configure table
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_widget.setAlternatingRowColors(True)
        table_widget.setSortingEnabled(True)
        
        return table_widget
        
    def flatten_data(self, data, parent_key='', sep='_'):
        """Flatten nested dictionaries and lists"""
        items = []
        
        if isinstance(data, dict):
            for k, v in data.items():
                new_key = f"{parent_key}{sep}{k}" if parent_key else k
                if isinstance(v, (dict, list)):
                    items.extend(self.flatten_data(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        elif isinstance(data, list):
            for i, v in enumerate(data):
                new_key = f"{parent_key}{sep}{i}" if parent_key else str(i)
                if isinstance(v, (dict, list)):
                    items.extend(self.flatten_data(v, new_key, sep=sep).items())
                else:
                    items.append((new_key, v))
        else:
            items.append((parent_key or 'value', data))
            
        return dict(items)
        
    def get_file_size(self):
        """Get file size if CSV file exists"""
        csv_file = self.data.get('csv_file')
        if csv_file and os.path.exists(csv_file):
            size = os.path.getsize(csv_file)
            if size < 1024:
                return f"{size} bytes"
            elif size < 1024 * 1024:
                return f"{size / 1024:.1f} KB"
            else:
                return f"{size / (1024 * 1024):.1f} MB"
        return "N/A"
        
    def export_current_tab(self):
        """Export current tab data to CSV"""
        current_index = self.tab_widget.currentIndex()
        current_widget = self.tab_widget.widget(current_index)
        tab_name = self.tab_widget.tabText(current_index)
        
        if isinstance(current_widget, QTableWidget):
            self.export_table_to_csv(current_widget, tab_name)
        else:
            QMessageBox.information(self, "Export", "Current tab cannot be exported as CSV.")
            
    def export_table_to_csv(self, table_widget, tab_name):
        """Export table widget data to CSV"""
        filename, _ = QFileDialog.getSaveFileName(
            self,
            f"Export {tab_name}",
            f"Battery_{self.battery_id}_Cycle_{self.cycle_number}_{tab_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if filename:
            try:
                data = []
                headers = []
                
                # Get headers
                for col in range(table_widget.columnCount()):
                    headers.append(table_widget.horizontalHeaderItem(col).text())
                    
                # Get data
                for row in range(table_widget.rowCount()):
                    row_data = []
                    for col in range(table_widget.columnCount()):
                        item = table_widget.item(row, col)
                        row_data.append(item.text() if item else "")
                    data.append(row_data)
                    
                # Create DataFrame and save
                df = pd.DataFrame(data, columns=headers)
                df.to_csv(filename, index=False)
                
                QMessageBox.information(self, "Export Successful", f"Data exported to:\n{filename}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{str(e)}")


class SDCardDataWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.charger_info_labels = {}
        self.saved_data = {}  # To store saved data
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)
        
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Create left and right panels
        left_panel = self.create_left_panel()
        right_panel = self.create_right_panel()

        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)

    def create_left_panel(self):
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_panel.setFixedWidth(400)
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_panel.setLayout(left_layout)

        self.create_files_section(left_layout)
        self.create_charger_info_section(left_layout)
        self.create_saved_files_section(left_layout)
        left_layout.setStretchFactor(self.files_tree, 3)
        left_layout.setStretchFactor(self.charger_tree, 1)
        left_layout.setStretchFactor(self.saved_files_table, 2)
        
        return left_panel
    
    def create_saved_files_section(self, layout):
        saved_header = QLabel("Saved Files")
        saved_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px; margin-top: 10px;")
        layout.addWidget(saved_header)
        
        self.saved_files_table = QTableWidget()
        self.saved_files_table.setColumnCount(3)
        self.saved_files_table.setHorizontalHeaderLabels(["Battery ID", "Cycle", "Download Time"])
        
        header = self.saved_files_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.saved_files_table.setColumnWidth(0, 80)
        self.saved_files_table.setColumnWidth(1, 60)
        
        self.saved_files_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.saved_files_table.setAlternatingRowColors(True)
        
        self.saved_files_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.saved_files_table.customContextMenuRequested.connect(self.show_saved_files_context_menu)
        
        # Connect double-click to the new data viewer
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
        
        self.zoom_in_btn = QPushButton("Zoom In")
        self.zoom_out_btn = QPushButton("Zoom Out")
        self.reset_zoom_btn = QPushButton("Reset Zoom")
        self.save_btn = QPushButton("Save Plot")
        self.clear_btn = QPushButton("Clear Data")
        
        self.zoom_in_btn.clicked.connect(self.zoom_in)
        self.zoom_out_btn.clicked.connect(self.zoom_out)
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        self.save_btn.clicked.connect(self.save_plot)
        self.clear_btn.clicked.connect(self.clear_data)
        
        controls_layout.addWidget(self.zoom_in_btn)
        controls_layout.addWidget(self.zoom_out_btn)
        controls_layout.addWidget(self.reset_zoom_btn)
        controls_layout.addWidget(self.save_btn)
        controls_layout.addWidget(self.clear_btn)
        controls_layout.addStretch()
        
        return controls_layout

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
        
    def save_as_csv_file(self, battery_id, cycle_number):
        """Save data_frames_1_buffer and data_frames_2_buffer to a CSV file with timestamp-based merging"""
        data_frames_1_buffer = getattr(self.main_window, 'data_frames_1_buffer', None)
        data_frames_2_buffer = getattr(self.main_window, 'data_frames_2_buffer', None)
        
        # Check if buffers have data
        if not data_frames_1_buffer and not data_frames_2_buffer:
            QMessageBox.warning(self, "No Data", "No data available to save.")
            return None
            
        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"Battery_{battery_id}_Cycle_{cycle_number}_{timestamp}.csv"
        
        # Let user choose filename and directory
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Save Battery Data as CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return None  # User cancelled
            
        try:
            # Create dictionaries to store data by timestamp
            buffer1_data = {}
            buffer2_data = {}
            all_timestamps = set()
            
            # Process buffer 1 data
            if data_frames_1_buffer and isinstance(data_frames_1_buffer, list):
                for i, frame in enumerate(data_frames_1_buffer):
                    timestamp_key = None
                    frame_data = {}
                    
                    if isinstance(frame, dict):
                        # Look for timestamp fields (common names)
                        timestamp_fields = ['timestamp', 'time', 'Timestamp', 'Time', 'ts', 'datetime']
                        for ts_field in timestamp_fields:
                            if ts_field in frame:
                                timestamp_key = frame[ts_field]
                                break
                        
                        # Add all fields without prefix
                        for key, value in frame.items():
                            if key not in timestamp_fields:  # Don't duplicate timestamp
                                frame_data[key] = value
                            else:
                                frame_data['Timestamp'] = value
                                
                    elif isinstance(frame, (list, tuple)):
                        # Assume first element is timestamp for lists
                        if len(frame) > 0:
                            timestamp_key = frame[0]
                            frame_data['Timestamp'] = frame[0]
                            for j, value in enumerate(frame[1:], 1):
                                frame_data[f'Value_{j}'] = value
                    else:
                        # Use index as timestamp for other types
                        timestamp_key = i
                        frame_data['Timestamp'] = i
                        frame_data['Data'] = str(frame)
                    
                    if timestamp_key is not None:
                        buffer1_data[timestamp_key] = frame_data
                        all_timestamps.add(timestamp_key)
            
            # Process buffer 2 data
            if data_frames_2_buffer and isinstance(data_frames_2_buffer, list):
                for i, frame in enumerate(data_frames_2_buffer):
                    timestamp_key = None
                    frame_data = {}
                    
                    if isinstance(frame, dict):
                        # Look for timestamp fields
                        timestamp_fields = ['timestamp', 'time', 'Timestamp', 'Time', 'ts', 'datetime']
                        for ts_field in timestamp_fields:
                            if ts_field in frame:
                                timestamp_key = frame[ts_field]
                                break
                        
                        # Add all fields without prefix
                        for key, value in frame.items():
                            if key not in timestamp_fields:  # Don't duplicate timestamp
                                frame_data[key] = value
                                
                    elif isinstance(frame, (list, tuple)):
                        # Assume first element is timestamp for lists
                        if len(frame) > 0:
                            timestamp_key = frame[0]
                            for j, value in enumerate(frame[1:], 1):
                                frame_data[f'Value_{j}'] = value
                    else:
                        # Use index as timestamp for other types
                        timestamp_key = i
                        frame_data['Data'] = str(frame)
                    
                    if timestamp_key is not None:
                        buffer2_data[timestamp_key] = frame_data
                        all_timestamps.add(timestamp_key)
            
            if not all_timestamps:
                QMessageBox.warning(self, "No Data", "No valid data found after processing.")
                return None
            
            # Combine data based on timestamps
            combined_data = []
            
            # Sort timestamps for consistent output
            sorted_timestamps = sorted(all_timestamps)
            
            for ts in sorted_timestamps:
                row = {'Timestamp': ts}
                
                # Add buffer 1 data if exists
                if ts in buffer1_data:
                    row.update(buffer1_data[ts])
                
                # Add buffer 2 data if exists (will overwrite buffer1 data if same keys exist)
                if ts in buffer2_data:
                    row.update(buffer2_data[ts])
                
                combined_data.append(row)
            
            # Create DataFrame and save to CSV
            df = pd.DataFrame(combined_data)
            
            # Fill NaN values with empty strings for better readability
            df = df.fillna('')
            
            # Save directly to CSV without metadata
            df.to_csv(filename, index=False)
            
            QMessageBox.information(
                self,
                "Export Successful",
                f"Data successfully saved to:\n{filename}\n\n"
                f"Total rows: {len(combined_data)}\n"
                f"File size: {os.path.getsize(filename)} bytes"
            )
            
            return filename
            
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to save CSV file:\n{str(e)}"
            )
            return None

    def is_data_already_saved(self, battery_id, cycle_number):
        # Checks if combination already exists
        key = (str(battery_id), str(cycle_number))
        return key in self.saved_data

    def add_saved_file_entry(self, battery_id, cycle_number, data=None):
        # Add entry to saved files
        if self.is_data_already_saved(battery_id, cycle_number):
            QMessageBox.information(
                self, 
                "Duplicate Data", 
                f"Data for Battery {battery_id} - Cycle {cycle_number} is already saved."
            )
            return False
        
        # Add to saved_data dictionary
        key = (str(battery_id), str(cycle_number))
        self.saved_data[key] = data or {}
        
        row_count = self.saved_files_table.rowCount()
        self.saved_files_table.insertRow(row_count)
        
        self.saved_files_table.setItem(row_count, 0, QTableWidgetItem(str(battery_id)))
        self.saved_files_table.setItem(row_count, 1, QTableWidgetItem(str(cycle_number)))
        self.saved_files_table.setItem(row_count, 2, QTableWidgetItem(datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        
        self.saved_files_table.item(row_count, 0).setTextAlignment(Qt.AlignCenter)
        self.saved_files_table.item(row_count, 1).setTextAlignment(Qt.AlignCenter)
        
        return True

    def view_saved_data(self, item):
        """Open data viewer dialog when double-clicking on saved file"""
        row = item.row()
        battery_id = self.saved_files_table.item(row, 0).text()
        cycle_number = self.saved_files_table.item(row, 1).text()
        
        key = (battery_id, cycle_number)
        if key in self.saved_data:
            # Open the data viewer dialog
            dialog = DataViewerDialog(battery_id, cycle_number, self.saved_data[key], self)
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
                self.view_saved_data(self.saved_files_table.item(row, 0))
            elif action.text() == "Delete" and row >= 0:
                self.delete_saved_file_row(row)
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

    def on_mouse_move(self, event):
        pass

    def zoom_in(self):
        """Zoom in on the plot"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        
        x_range = (xlim[1] - xlim[0]) * 0.4
        y_range = (ylim[1] - ylim[0]) * 0.4
        
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.canvas.draw()

    def zoom_out(self):
        """Zoom out on the plot"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        
        x_range = (xlim[1] - xlim[0]) * 1.25
        y_range = (ylim[1] - ylim[0]) * 1.25
        
        self.ax.set_xlim(x_center - x_range/2, x_center + x_range/2)
        self.ax.set_ylim(y_center - y_range/2, y_center + y_range/2)
        self.canvas.draw()

    def reset_zoom(self):
        """Reset zoom to show all data"""
        self.ax.relim()
        self.ax.autoscale_view()
        self.canvas.draw()

    def save_plot(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, 
            "Save Plot", 
            f"sd_card_parameter_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)"
        )
        if filename:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')

    def clear_data(self):
        """Clear any data if needed"""
        self.ax.clear()
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Parameter Value')
        self.ax.set_title('SD Card Data Parameter Monitoring')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
            
    def download_cycle_data(self, battery_id, cycle_number):
        if self.is_data_already_saved(battery_id, cycle_number):
            QMessageBox.information(
                self, 
                "Duplicate Data", 
                f"Data for Battery {battery_id} - Cycle {cycle_number} is already saved."
            )
            return
        
        serial_obj = self.get_serial_obj()
        if serial_obj and serial_obj.is_open:
            try:
                # Save the buffer data to CSV file
                saved_filename = self.save_as_csv_file(battery_id, cycle_number)
                
                if saved_filename:
                    # Query additional data via serial
                    data = send_battery_query(serial_obj, self, battery_id, cycle_number)
                    
                    # Add metadata about the saved file
                    if data is None:
                        data = {}
                    data['csv_file'] = saved_filename
                    data['export_time'] = datetime.now().isoformat()
                    
                    self.add_saved_file_entry(battery_id, cycle_number, data)
                
            except Exception as e:
                QMessageBox.warning(self, "Download Error", f"Failed to download data: {str(e)}")
        else:
            QMessageBox.warning(self, "Connection Error", "Serial connection is not available.")
            
    def update_files_tree(self):
        if hasattr(self, 'files_tree'):
            self.populate_files_tree()
            
    def get_serial_obj(self):
        return self.main_window.serial_obj
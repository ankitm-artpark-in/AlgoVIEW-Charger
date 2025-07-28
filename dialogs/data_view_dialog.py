from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QTabWidget, QPushButton, QDialogButtonBox, QTextEdit, QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, QAbstractItemView, QFileDialog
from PySide6.QtCore import Qt
import pandas as pd
import csv
import os
from datetime import datetime


class DataViewerDialog(QDialog):
    """Dialog to display saved data in tabular format"""
    
    def __init__(self, battery_id, cycle_number, data, main_window, parent=None):
        super().__init__(parent)
        self.battery_id = battery_id
        self.cycle_number = cycle_number
        self.data = data
        self.main_window = main_window
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
        export_btn.clicked.connect(self.export_data_to_csv)
        button_box.addButton(export_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        # Add save button (saves to the saved files list)
        save_btn = QPushButton("Save Data")
        save_btn.clicked.connect(self.save_data_to_list)
        button_box.addButton(save_btn, QDialogButtonBox.ButtonRole.ActionRole)
        
        layout.addWidget(button_box)
        
    def load_data_tabs(self):
        """Load data into different tabs based on data structure"""
        # Load buffer data from main window
        self.load_buffer_data_tab()
        
        # Add serial query data tab if available
        serial_data = {k: v for k, v in self.data.items() 
                      if k not in ['csv_file', 'export_time']}
        if serial_data:
            self.add_serial_data_tab(serial_data)
            
        # Add metadata tab
        self.add_metadata_tab()
        
    def load_buffer_data_tab(self):
        """Add tab with buffer data from main window"""
        try:
            combined_data = self.get_combined_buffer_data()
            if combined_data:
                df = pd.DataFrame(combined_data)
                table_widget = self.create_table_from_dataframe(df)
                self.tab_widget.addTab(table_widget, f"Buffer Data ({len(combined_data)} rows)")
            else:
                self.add_empty_tab("No Buffer Data Available")
        except Exception as e:
            error_widget = QTextEdit()
            error_widget.setPlainText(f"Error loading buffer data: {str(e)}")
            error_widget.setReadOnly(True)
            self.tab_widget.addTab(error_widget, "Buffer Data (Error)")
            
    def get_combined_buffer_data(self):
        """Get combined data from both buffers similar to save_as_csv_file logic"""
        data_frames_1_buffer = getattr(self.main_window, 'data_frames_1_buffer', None)
        data_frames_2_buffer = getattr(self.main_window, 'data_frames_2_buffer', None)
        
        if not data_frames_1_buffer and not data_frames_2_buffer:
            return []
            
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
                    # Look for timestamp fields
                    timestamp_fields = ['timestamp', 'time', 'Timestamp', 'Time', 'ts', 'datetime']
                    for ts_field in timestamp_fields:
                        if ts_field in frame:
                            timestamp_key = frame[ts_field]
                            break
                    
                    # Add all fields
                    for key, value in frame.items():
                        if key not in timestamp_fields:
                            frame_data[key] = value
                        else:
                            frame_data['Timestamp'] = value
                            
                elif isinstance(frame, (list, tuple)):
                    if len(frame) > 0:
                        timestamp_key = frame[0]
                        frame_data['Timestamp'] = frame[0]
                        for j, value in enumerate(frame[1:], 1):
                            frame_data[f'Value_{j}'] = value
                else:
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
                    timestamp_fields = ['timestamp', 'time', 'Timestamp', 'Time', 'ts', 'datetime']
                    for ts_field in timestamp_fields:
                        if ts_field in frame:
                            timestamp_key = frame[ts_field]
                            break
                    
                    for key, value in frame.items():
                        if key not in timestamp_fields:
                            frame_data[key] = value
                            
                elif isinstance(frame, (list, tuple)):
                    if len(frame) > 0:
                        timestamp_key = frame[0]
                        for j, value in enumerate(frame[1:], 1):
                            frame_data[f'Value_{j}'] = value
                else:
                    timestamp_key = i
                    frame_data['Data'] = str(frame)
                
                if timestamp_key is not None:
                    buffer2_data[timestamp_key] = frame_data
                    all_timestamps.add(timestamp_key)
        
        # Combine data based on timestamps
        combined_data = []
        sorted_timestamps = sorted(all_timestamps)
        
        for ts in sorted_timestamps:
            row = {'Timestamp': ts}
            
            if ts in buffer1_data:
                row.update(buffer1_data[ts])
            
            if ts in buffer2_data:
                row.update(buffer2_data[ts])
            
            combined_data.append(row)
        
        return combined_data
            
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
            ("Export Time", datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
            ("Data Keys", ', '.join(self.data.keys()) if self.data else 'Buffer Data Only')
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
        
    def export_data_to_csv(self):
        """Export current data to CSV file"""
        # Generate default filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"Battery_{self.battery_id}_Cycle_{self.cycle_number}_{timestamp}.csv"
        
        # Let user choose filename and directory
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Battery Data as CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return  # User cancelled
            
        try:
            # Get combined buffer data
            combined_data = self.get_combined_buffer_data()
            
            if combined_data:
                # Create DataFrame and save
                df = pd.DataFrame(combined_data)
                df = df.fillna('')  # Fill NaN values with empty strings
                df.to_csv(filename, index=False)
                
                QMessageBox.information(
                    self,
                    "Export Successful",
                    f"Data successfully exported to:\n{filename}\n\n"
                    f"Total rows: {len(combined_data)}\n"
                    f"File size: {os.path.getsize(filename)} bytes"
                )
            else:
                QMessageBox.warning(self, "No Data", "No data available to export.")
                
        except Exception as e:
            QMessageBox.critical(
                self,
                "Export Error",
                f"Failed to export CSV file:\n{str(e)}"
            )
            
    def save_data_to_list(self):
        """Save data to the main window's saved files list"""
        parent_window = self.parent()
        if hasattr(parent_window, 'add_saved_file_entry'):
            # Prepare data to save
            data_to_save = self.data.copy() if self.data else {}
            data_to_save['export_time'] = datetime.now().isoformat()
            
            success = parent_window.add_saved_file_entry(
                self.battery_id, 
                self.cycle_number, 
                data_to_save
            )
            
            if success:
                QMessageBox.information(
                    self,
                    "Data Saved",
                    f"Data for Battery {self.battery_id} - Cycle {self.cycle_number} has been saved to the list."
                )
            else:
                QMessageBox.information(
                    self,
                    "Already Saved",
                    f"Data for Battery {self.battery_id} - Cycle {self.cycle_number} is already in the saved list."
                )
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QTabWidget, 
                             QPushButton, QTextEdit, QTableWidget, 
                             QTableWidgetItem, QHeaderView, QMessageBox, QInputDialog, 
                             QAbstractItemView, QFileDialog, QComboBox, QWidget,
                             QSplitter, QFrame, QListWidget, QListWidgetItem, QCheckBox)
from PySide6.QtCore import Qt
import pandas as pd
import csv
import os
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import numpy as np


class DataViewerDialog(QDialog):    
    def __init__(self, battery_id, cycle_number, data, main_window, parent=None):
        super().__init__(parent)
        self.battery_id = battery_id
        self.cycle_number = cycle_number
        self.data = data
        self.main_window = main_window
        self.combined_data = None  # combined buffer data --> all data
        self.imported_csv_data = None  # imported CSV data
        self.current_df = None     # dataframe for plotting
        self.color_palette = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd', 
                              '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf']
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"Data Viewer - Battery {self.battery_id} - Cycle {self.cycle_number}")
        # self.setModal(True)
        self.resize(1000, 750)  # layout size
        
        layout = QVBoxLayout()
        self.setLayout(layout)
        header_label = QLabel(f"Battery ID: {self.battery_id} | Cycle: {self.cycle_number}")
        header_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(header_label)
        
        # splitter for main content (data tabs + plot)
        main_splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(main_splitter)
        
        # Left panel: Data display
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        self.tab_widget = QTabWidget()
        left_layout.addWidget(self.tab_widget)
        
        main_splitter.addWidget(left_widget)
        
        # Right panel: Plot controls and graph
        right_widget = self.create_plot_widget()
        main_splitter.addWidget(right_widget)
        self.load_data_tabs()
        
        # (50% : 50% display division)
        main_splitter.setSizes([600, 600])
        button_layout = QHBoxLayout()
        
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_data_to_csv)
        button_layout.addWidget(export_btn)
        
        save_btn = QPushButton("Save Data")
        save_btn.clicked.connect(self.save_data_to_list)
        button_layout.addWidget(save_btn)
        button_layout.addStretch()
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        
    def create_plot_widget(self):
        plot_widget = QWidget()
        plot_layout = QVBoxLayout(plot_widget)
        
        # Plot controls
        controls_frame = QFrame()
        controls_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        controls_layout = QVBoxLayout(controls_frame)
        
        plot_title = QLabel("Data Plotting")
        plot_title.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(plot_title)
        
        # Data source selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("Data Source:"))
        self.data_source_combo = QComboBox()
        self.data_source_combo.currentTextChanged.connect(self.on_data_source_changed)
        source_layout.addWidget(self.data_source_combo)
        controls_layout.addLayout(source_layout)
        
        # X-axis selection
        x_layout = QHBoxLayout()
        x_layout.addWidget(QLabel("X-axis:"))
        self.x_axis_combo = QComboBox()
        self.x_axis_combo.setMinimumWidth(120)
        x_layout.addWidget(self.x_axis_combo)
        controls_layout.addLayout(x_layout)
        
        # Y-axis selection
        y_layout = QVBoxLayout()
        y_layout.addWidget(QLabel("Y-axis:"))
        self.y_axis_list = QListWidget()
        self.y_axis_list.setMaximumHeight(150)
        self.y_axis_list.itemChanged.connect(self.on_y_axis_selection_changed)
        y_layout.addWidget(self.y_axis_list)
        
        controls_layout.addLayout(y_layout)
        
        # Plot type selection
        plot_type_layout = QHBoxLayout()
        plot_type_layout.addWidget(QLabel("Plot Type:"))
        self.plot_type_combo = QComboBox()
        self.plot_type_combo.addItems(["Line Plot", "Scatter Plot", "Line + Markers"])
        self.plot_type_combo.currentTextChanged.connect(self.on_plot_settings_changed)
        plot_type_layout.addWidget(self.plot_type_combo)
        controls_layout.addLayout(plot_type_layout)
        
        # Plot and clear buttons
        button_layout = QHBoxLayout()
        self.plot_btn = QPushButton("Update Plot")
        self.plot_btn.clicked.connect(self.update_plot)
        self.clear_plot_btn = QPushButton("Clear Plot")
        self.clear_plot_btn.clicked.connect(self.clear_plot)
        
        button_layout.addWidget(self.plot_btn)
        button_layout.addWidget(self.clear_plot_btn)
        controls_layout.addLayout(button_layout)
        
        plot_layout.addWidget(controls_frame)
        self.figure = Figure(figsize=(10, 8))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        self.ax.set_title('Select data and axes to create plot')
        self.ax.grid(True, alpha=0.3)
        
        plot_layout.addWidget(self.canvas)
        return plot_widget
        
    def load_data_tabs(self):
        # load data into different tabs based on data structure and also check for imported data
        if 'csv_data' in self.data and isinstance(self.data['csv_data'], pd.DataFrame):
            self.imported_csv_data = self.data['csv_data']
            self.load_imported_csv_tab()
        else:
            # Load buffer data from main window
            self.load_buffer_data_tab()
        
        serial_data = {k: v for k, v in self.data.items() 
                      if k not in ['csv_data', 'csv_file', 'export_time', 'import_time', 'import_filename', 'file_path']}
        if serial_data:
            self.add_serial_data_tab(serial_data)
            
        self.add_metadata_tab()
        if hasattr(self, 'data_source_combo'):
            self.initialize_plot_controls()
    
    def load_imported_csv_tab(self):
        try:
            if self.imported_csv_data is not None and not self.imported_csv_data.empty:
                table_widget = self.create_table_from_dataframe(self.imported_csv_data)
                
                source_info = ""
                if 'import_filename' in self.data:
                    source_info = f" (from {self.data['import_filename']})"
                elif 'file_path' in self.data:
                    source_info = f" (from {os.path.basename(self.data['file_path'])})"
                
                tab_name = f"CSV Data ({len(self.imported_csv_data)} rows){source_info}"
                self.tab_widget.addTab(table_widget, tab_name)
            else:
                self.add_empty_tab("No CSV Data Available")
        except Exception as e:
            error_widget = QTextEdit()
            error_widget.setPlainText(f"Error loading CSV data: {str(e)}")
            error_widget.setReadOnly(True)
            self.tab_widget.addTab(error_widget, "CSV Data (Error)")
        
    def initialize_plot_controls(self):
        self.data_source_combo.clear()
        if self.imported_csv_data is not None and not self.imported_csv_data.empty:
            self.data_source_combo.addItem("CSV Data")
        
        if self.combined_data:
            self.data_source_combo.addItem("Buffer Data")
        
        serial_data = {k: v for k, v in self.data.items() 
                      if k not in ['csv_data', 'csv_file', 'export_time', 'import_time', 'import_filename', 'file_path']}
        if serial_data:
            self.data_source_combo.addItem("Serial Data")

        if self.data_source_combo.count() > 0:
            self.on_data_source_changed(self.data_source_combo.currentText())
        
    def on_data_source_changed(self, source_name):
        self.x_axis_combo.clear()
        self.y_axis_list.clear()
        
        if source_name == "CSV Data" and self.imported_csv_data is not None:
            df = self.imported_csv_data
            self.current_df = df

            columns = df.columns.tolist()
            self.x_axis_combo.addItems(columns)
            
            for col in columns:
                is_numeric = pd.api.types.is_numeric_dtype(df[col])
                
                item = QListWidgetItem(col)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Unchecked)

                if is_numeric:
                    item.setText(f"{col} (numeric)")
                
                self.y_axis_list.addItem(item)

            if len(columns) > 0:
                # time-related column for X-axis
                time_columns = [col for col in columns if any(time_word in col.lower() 
                               for time_word in ['time', 'timestamp', 'date', 'datetime', 'hour', 'minute', 'second'])]
                if time_columns:
                    self.x_axis_combo.setCurrentText(time_columns[0])

                numeric_cols = [col for col in columns if pd.api.types.is_numeric_dtype(df[col])]
                for i, col in enumerate(numeric_cols[:3]):
                    for j in range(self.y_axis_list.count()):
                        item = self.y_axis_list.item(j)
                        if col in item.text():
                            item.setCheckState(Qt.CheckState.Checked)
                            break
                            
        elif source_name == "Buffer Data" and self.combined_data:
            df = pd.DataFrame(self.combined_data)
            self.current_df = df
            
            numeric_columns = []
            for col in df.columns:
                try:
                    pd.to_numeric(df[col], errors='raise')
                    numeric_columns.append(col)
                except:
                    if 'time' in col.lower() or 'timestamp' in col.lower():
                        numeric_columns.append(col)
            
            if numeric_columns:
                self.x_axis_combo.addItems(numeric_columns)
                
                for col in numeric_columns:
                    item = QListWidgetItem(col)
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                    item.setCheckState(Qt.CheckState.Unchecked)
                    self.y_axis_list.addItem(item)
                    
        elif source_name == "Serial Data":
            serial_data = {k: v for k, v in self.data.items() 
                          if k not in ['csv_data', 'csv_file', 'export_time', 'import_time', 'import_filename', 'file_path']}
            if serial_data:
                flattened = self.flatten_data(serial_data)
                data_list = []
                for key, value in flattened.items():
                    try:
                        numeric_value = float(value)
                        data_list.append({'Parameter': key, 'Value': numeric_value})
                    except:
                        continue
                
                if data_list:
                    df = pd.DataFrame(data_list)
                    self.current_df = df
                    
                    columns = df.columns.tolist()
                    self.x_axis_combo.addItems(columns)
                    
                    for col in columns:
                        item = QListWidgetItem(col)
                        item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                        item.setCheckState(Qt.CheckState.Unchecked)
                        self.y_axis_list.addItem(item)
                    
                    if 'Parameter' in columns and 'Value' in columns:
                        self.x_axis_combo.setCurrentText('Parameter')
    
    def get_selected_y_columns(self):
        # list of selected Y-axis columns
        selected_columns = []
        for i in range(self.y_axis_list.count()):
            item = self.y_axis_list.item(i)
            if item.checkState() == Qt.CheckState.Checked:
                col_name = item.text().replace(" (numeric)", "")
                selected_columns.append(col_name)
        return selected_columns
    
    def on_y_axis_selection_changed(self):
        self.update_plot()
    
    def on_plot_settings_changed(self):
        self.update_plot()
    
    def update_plot(self):
        if self.current_df is None or self.current_df.empty:
            self.clear_plot()
            return
            
        x_column = self.x_axis_combo.currentText()
        y_columns = self.get_selected_y_columns()
        
        if not x_column or not y_columns:
            self.clear_plot()
            return
        
        try:
            self.ax.clear()
            
            plot_type = self.plot_type_combo.currentText()
            for i, y_column in enumerate(y_columns):
                df = self.current_df
                color = self.color_palette[i % len(self.color_palette)]
                if x_column not in df.columns or y_column not in df.columns:
                    continue
                
                # prepare data for plotting
                x_data = df[x_column]
                y_data = df[y_column]
                
                # handle timestamp data
                if self.is_timestamp_column(x_column):
                    try:
                        x_data = pd.to_datetime(x_data)
                    except:
                        try:
                            x_data = pd.to_numeric(x_data, errors='coerce')
                        except:
                            x_data = range(len(x_data))
                else:
                    try:
                        x_data = pd.to_numeric(x_data, errors='coerce')
                    except:
                        x_data = range(len(x_data))
                
                try:
                    y_data = pd.to_numeric(y_data, errors='coerce')
                except:
                    continue
                
                if isinstance(x_data, pd.Series):
                    mask = ~(x_data.isna() | y_data.isna())
                    x_data = x_data[mask]
                    y_data = y_data[mask]
                else:
                    mask = ~y_data.isna()
                    x_data = [x_data[i] for i in range(len(y_data)) if mask.iloc[i]]
                    y_data = y_data[mask]
                
                if len(x_data) == 0 or len(y_data) == 0:
                    continue
                
                # ploting based on type of plot selected
                label = y_column
                
                if plot_type == "Line Plot":
                    self.ax.plot(x_data, y_data, color=color, linewidth=2, label=label)
                elif plot_type == "Scatter Plot":
                    self.ax.scatter(x_data, y_data, color=color, alpha=0.7, s=30, label=label)
                elif plot_type == "Line + Markers":
                    self.ax.plot(x_data, y_data, color=color, linewidth=2, marker='o', 
                               markersize=4, alpha=0.8, label=label)
            
            # labels and title
            self.ax.set_xlabel(x_column)
            self.ax.set_ylabel('Values')
            self.ax.set_title(f'Battery {self.battery_id} - Cycle {self.cycle_number}\n{", ".join(y_columns)} vs {x_column}')
            
            # adding legends for different plots in single graph
            if len(y_columns) > 1:
                self.ax.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
                self.figure.tight_layout()
            
            self.ax.grid(True, alpha=0.3)
            
            # auto-format x-axis
            if (self.current_df is not None and 
                x_column in self.current_df.columns and
                hasattr(self.current_df[x_column], 'dtype') and 
                'datetime' in str(self.current_df[x_column].dtype)):
                self.figure.autofmt_xdate()
            
            self.canvas.draw()
            
        except Exception as e:
            self.clear_plot()
    
    def clear_plot(self):
        self.ax.clear()
        self.ax.set_title('Select data and axes to create plot')
        self.ax.grid(True, alpha=0.3)
        self.canvas.draw()
        
    def is_timestamp_column(self, column_name):
        timestamp_keywords = ['time', 'timestamp', 'date', 'datetime', 'hour', 'minute', 'second']
        return any(keyword in column_name.lower() for keyword in timestamp_keywords)
        
    def load_buffer_data_tab(self):
        try:
            self.combined_data = self.get_combined_buffer_data()
            if self.combined_data:
                df = pd.DataFrame(self.combined_data)
                table_widget = self.create_table_from_dataframe(df)
                self.tab_widget.addTab(table_widget, f"Buffer Data ({len(self.combined_data)} rows)")
            else:
                self.add_empty_tab("No Buffer Data Available")
        except Exception as e:
            error_widget = QTextEdit()
            error_widget.setPlainText(f"Error loading buffer data: {str(e)}")
            error_widget.setReadOnly(True)
            self.tab_widget.addTab(error_widget, "Buffer Data (Error)")
            
    def get_combined_buffer_data(self):
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
                    timestamp_fields = ['timestamp', 'time', 'Timestamp', 'Time', 'ts', 'datetime']
                    for ts_field in timestamp_fields:
                        if ts_field in frame:
                            timestamp_key = frame[ts_field]
                            break
                    
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
        if not serial_data:
            return
            
        # Convert serial data to tabular format
        table_widget = QTableWidget()
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
        metadata_widget = QTableWidget()
        metadata_items = [
            ("Battery ID", self.battery_id),
            ("Cycle Number", self.cycle_number),
        ]
        
        # Add different metadata based on data source
        if 'import_time' in self.data:
            metadata_items.append(("Import Time", self.data.get('import_time', 'Unknown')))
            metadata_items.append(("Original Filename", self.data.get('import_filename', 'Unknown')))
            metadata_items.append(("File Path", self.data.get('file_path', 'Unknown')))
            metadata_items.append(("Data Source", "Imported CSV"))
        else:
            metadata_items.append(("Export Time", self.data.get('export_time', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))))
            metadata_items.append(("Data Source", "Downloaded"))
            
        metadata_items.append(("Data Keys", ', '.join(self.data.keys()) if self.data else 'Buffer Data Only'))
        
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
        # creates empty tab with message
        empty_widget = QTextEdit()
        empty_widget.setPlainText(message)
        empty_widget.setReadOnly(True)
        empty_widget.setAlignment(Qt.AlignCenter)
        self.tab_widget.addTab(empty_widget, "No Data")
        
    def create_table_from_dataframe(self, df):
        # create pandas dataframe to table widget
        table_widget = QTableWidget()
        table_widget.setRowCount(len(df))
        table_widget.setColumnCount(len(df.columns))
        table_widget.setHorizontalHeaderLabels(df.columns.tolist())
        
        # make table 
        for row in range(len(df)):
            for col in range(len(df.columns)):
                value = df.iloc[row, col]
                if pd.isna(value):
                    value = ""
                table_widget.setItem(row, col, QTableWidgetItem(str(value)))
                
        # read only tables
        table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
        table_widget.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        table_widget.setAlternatingRowColors(True)
        table_widget.setSortingEnabled(True)
        
        return table_widget
        
    def flatten_data(self, data, parent_key='', sep='_'):
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
        # generate default file_name
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        default_filename = f"Battery_{self.battery_id}_Cycle_{self.cycle_number}_{timestamp}.csv"
        
        filename, _ = QFileDialog.getSaveFileName(
            self,
            "Export Battery Data as CSV",
            default_filename,
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if not filename:
            return
            
        try:
            # fetch combined buffer data
            combined_data = self.get_combined_buffer_data()
            
            if combined_data:
                df = pd.DataFrame(combined_data)
                df = df.fillna('')
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
        parent_window = self.parent()
        if hasattr(parent_window, 'add_saved_file_entry'):
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
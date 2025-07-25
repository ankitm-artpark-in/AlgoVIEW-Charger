from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                             QMenu, QComboBox, QCheckBox, QPushButton, QFileDialog,
                             QFrame, QScrollArea, QListWidget, QListWidgetItem,
                             QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox)
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, Signal
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QBrush, QColor, QIcon
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque

from serial_utils.send_frame import send_battery_query
from ..color_display_box import ColorBoxComboBox, ColorBoxDelegate
from dialogs import PasswordDialog

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
        row = item.row()
        battery_id = self.saved_files_table.item(row, 0).text()
        cycle_number = self.saved_files_table.item(row, 1).text()
        
        key = (battery_id, cycle_number)
        if key in self.saved_data:
            QMessageBox.information(
                self,
                "Saved Data",
                f"Viewing data for Battery {battery_id} - Cycle {cycle_number}\n\n"
                f"Data keys: {list(self.saved_data[key].keys()) if self.saved_data[key] else 'No data'}"
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
                data = send_battery_query(serial_obj, self, battery_id, cycle_number)
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
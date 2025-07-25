from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                             QMenu, QComboBox, QCheckBox, QPushButton, QFileDialog,
                             QFrame, QScrollArea, QListWidget, QListWidgetItem)
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

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)

    def create_left_panel(self):
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_panel.setFixedWidth(400)  # Fixed width for parameter panel
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        left_panel.setLayout(left_layout)

        self.create_files_section(left_layout)
        self.create_charger_info_section(left_layout)
        left_layout.setStretchFactor(self.files_tree, 2)
        left_layout.setStretchFactor(self.charger_tree, 1)
        # left_layout.setStretchFactor(self.saved_files, 2)
        
        return left_panel

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
        
        # Configure the plot
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Parameter Value')
        self.ax.set_title('SD Card Data Parameter Monitoring')
        self.ax.grid(True, alpha=0.3)
        
        # Format x-axis for time display
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Enable interactive features
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)

    def populate_charger_info_tree(self):
        self.charger_info_labels.clear()
        self.charger_tree.clear()

        # CHARGER_INFO parameters
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

    def show_files_context_menu(self, position):
        """Show context menu for files tree"""
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
        """Save the current plot to file"""
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
        serial_obj = self.get_serial_obj()
        if serial_obj and serial_obj.is_open:
            try:
                send_battery_query(serial_obj, self, battery_id, cycle_number)
            except Exception as e:
                pass
        else:
            pass
            
    def update_files_tree(self):
        if hasattr(self, 'files_tree'):
            self.populate_files_tree()
            
    def get_serial_obj(self):
        return self.main_window.serial_obj
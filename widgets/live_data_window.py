from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                             QMenu, QComboBox, QCheckBox, QPushButton, QFileDialog)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QBrush, QColor
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, deque
from .color_display_box import ColorBoxComboBox, ColorBoxDelegate
from dialogs import PasswordDialog


class LiveDataWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.parameter_labels = {}  # Store labels for each parameter
        self.parameter_color_combos = {}  # Store color combo boxes for each parameter
        self.parameter_checkboxes = {}  # Store checkboxes for each parameter
        self.debug_unlocked = False  # Track if debug messages are unlocked
        self.color_names = [
            "Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "Black", "Orange", "Purple", "Pink", "Brown", "Gray", "White", "Lime", "Navy", "Teal", "Olive",
            "Maroon", "Gold", "Silver", "Coral", "Turquoise", "Indigo", "Violet", "Salmon", "Khaki", "Plum", "Azure", "Mint", "Beige", "Lavender", "Crimson"
        ]
        self.color_values = [
            "#FF0000", "#008000", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF", "#000000", "#FFA500", "#800080", "#FFC0CB", "#A52A2A", "#808080", "#FFFFFF", "#00FF00", "#000080", "#008080", "#808000",
            "#800000", "#FFD700", "#C0C0C0", "#FF7F50", "#40E0D0", "#4B0082", "#EE82EE", "#FA8072", "#F0E68C", "#DDA0DD", "#007FFF", "#98FF98", "#F5F5DC", "#E6E6FA", "#DC143C"
        ]
        self.selected_colors = {}  # key: param_key, value: color hex
        
        # Data storage for plotting
        self.parameter_data = defaultdict(lambda: {'timestamps': deque(maxlen=1000), 'values': deque(maxlen=1000)})
        self.start_time = datetime.now()
        
        # Debug flags
        self.debug_visible = False
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)

        # Create main horizontal layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        # Left panel for tree widget
        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_panel.setFixedWidth(400)  # Fixed width for parameter panel
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Create tree widget with parameter dropdowns
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Parameter", "Value", "Color", "Enable"])
        self.tree.setColumnWidth(0, 200)
        self.tree.setColumnWidth(1, 50)
        self.tree.setColumnWidth(2, 120)
        self.tree.setColumnWidth(3, 30)
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.populate_tree()
        left_layout.addWidget(self.tree)

        # Right panel for plotting
        right_panel = QWidget()
        right_panel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        # Plot controls
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
        
        right_layout.addLayout(controls_layout)

        # Create matplotlib figure and canvas
        self.figure = Figure(figsize=(10, 6))
        self.canvas = FigureCanvas(self.figure)
        self.ax = self.figure.add_subplot(111)
        
        # Configure the plot
        self.ax.set_xlabel('Time')
        self.ax.set_ylabel('Parameter Value')
        self.ax.set_title('Real-time Parameter Monitoring')
        self.ax.grid(True, alpha=0.3)
        
        # Format x-axis for time display
        self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        self.ax.xaxis.set_major_locator(mdates.AutoDateLocator())
        
        # Enable interactive features
        self.canvas.mpl_connect('motion_notify_event', self.on_mouse_move)
        
        # Store plot lines
        self.plot_lines = {}
        
        right_layout.addWidget(self.canvas)

        # Add panels to main layout
        main_layout.addWidget(left_panel)
        main_layout.addWidget(right_panel, stretch=1)

        # Timer for updating plot
        self.plot_timer = QTimer()
        self.plot_timer.timeout.connect(self.update_plot)
        self.plot_timer.start(1000)  # Update every 100ms

    def populate_tree(self):
        self.message_structure = {
            "CHARGER_VIT": ["Voltage", "Current", "Temperature", "AC Value"],
            "CHARGER_INT_TEMP_DATA": ["Voltage Max", "Voltage Average", "Ambient Temperature"],
            "CHARGER_Brick_A": ["Cell 1", "Cell 2", "Cell 3", "Cell 4"],
            "CHARGER_Brick_B": ["Cell 5", "Cell 6", "Cell 7", "Cell 8"],
            "CHARGER_INFO": ["Hardware Version", "Product ID", "Serial Number", "Firmware Version"]
        }
        self.debug_message_structure = {
            "DEBUG_MESSAGE_1": ["Cell Count", "Charger On Status", "Current Count",
                            "Voltage Count", "Cell Balance Status"],
            "DEBUG_MESSAGE_2": ["Charger Safety Off", "Battery Voltage Read Value",
                            "Charger State", "Charger Op On", "Volta Heart Beat",
                            "Charger Error Flag"]
        }
        self.parameter_color_combos.clear()
        self.parameter_checkboxes.clear()
        self.selected_colors.clear()
        self.parameter_labels.clear()
        self.tree.clear()

        for message_type, parameters in self.message_structure.items():
            message_item = QTreeWidgetItem([message_type, "", "", ""])
            message_item.setForeground(0, Qt.black)
            self.tree.addTopLevelItem(message_item)

            for param in parameters:
                param_item = QTreeWidgetItem([param])
                message_item.addChild(param_item)
                value_label = QLabel("--")
                value_label.setMinimumWidth(80)
                value_label.setStyleSheet("color: #2196F3;")
                value_label.setAlignment(Qt.AlignCenter)
                font = QFont()
                font.setBold(True)
                font.setPointSize(11)
                value_label.setFont(font)
                key = f"{message_type}_{param}"
                self.parameter_labels[key] = value_label
                self.tree.setItemWidget(param_item, 1, value_label)

                # Color dropdown for each parameter
                color_combo = ColorBoxComboBox()
                color_combo.setFont(self.font())
                color_combo.setMinimumWidth(120)
                for name, hex_color in zip(self.color_names, self.color_values):
                    color_combo.addItem(name)
                    idx = color_combo.count() - 1
                    color_combo.setItemData(idx, hex_color, Qt.UserRole)
                color_combo.setCurrentIndex(-1)
                color_combo.currentIndexChanged.connect(lambda idx, k=key: self.on_color_changed(k))
                self.tree.setItemWidget(param_item, 2, color_combo)
                self.parameter_color_combos[key] = color_combo

                # Enable checkbox for each parameter
                checkbox = QCheckBox()
                checkbox.setFont(self.font())
                checkbox.stateChanged.connect(lambda state, k=key: self.on_checkbox_changed(k, state))
                enable_widget = QWidget()
                enable_layout = QHBoxLayout(enable_widget)
                enable_layout.addStretch()
                enable_layout.addWidget(checkbox)
                enable_layout.addStretch()
                enable_layout.setContentsMargins(0, 0, 0, 0)
                self.tree.setItemWidget(param_item, 3, enable_widget)
                self.parameter_checkboxes[key] = checkbox

        if self.debug_visible:
            self.add_debug_items_to_tree()
        self.tree.expandAll()

    def on_color_changed(self, changed_key):
        combo = self.parameter_color_combos[changed_key]
        idx = combo.currentIndex()
        color = combo.itemData(idx, Qt.UserRole) if idx >= 0 else None
        prev_color = self.selected_colors.get(changed_key)
        
        if prev_color == color:
            return
            
        if prev_color:
            del self.selected_colors[changed_key]
        if color:
            self.selected_colors[changed_key] = color
            
        self.update_color_combos_optimized(changed_key)
        self.update_plot_visibility()

    def on_checkbox_changed(self, param_key, state):
        self.update_plot_visibility()

    def update_plot_visibility(self):
        """Update which parameters are plotted based on checkbox state and color selection"""
        for param_key in self.parameter_checkboxes:
            checkbox = self.parameter_checkboxes[param_key]
            is_checked = checkbox.isChecked()
            has_color = param_key in self.selected_colors
            
            if is_checked and has_color:
                # Should be plotted
                if param_key not in self.plot_lines:
                    # Create new plot line
                    color = self.selected_colors[param_key]
                    line, = self.ax.plot([], [], color=color, label=param_key.replace('_', ' '), linewidth=2)
                    self.plot_lines[param_key] = line
            else:
                # Should not be plotted
                if param_key in self.plot_lines:
                    # Remove plot line
                    self.plot_lines[param_key].remove()
                    del self.plot_lines[param_key]
        
        # Update legend
        if self.plot_lines:
            self.ax.legend(loc='upper left', bbox_to_anchor=(0.02, 0.98))
        else:
            if self.ax.get_legend():
                self.ax.get_legend().remove()
        
        self.canvas.draw()

    def update_color_combos_optimized(self, changed_key):
        used_colors = set(self.selected_colors.values())
        for key, combo in self.parameter_color_combos.items():
            current_color = self.selected_colors.get(key)
            if key == changed_key or (current_color is None and key != changed_key):
                combo.blockSignals(True)
                combo.clear()
                for name, hex_color in zip(self.color_names, self.color_values):
                    if hex_color not in used_colors or hex_color == current_color:
                        combo.addItem(name)
                        idx = combo.count() - 1
                        combo.setItemData(idx, hex_color, Qt.UserRole)
                        if hex_color == current_color:
                            combo.setCurrentIndex(idx)
                if not current_color:
                    combo.setCurrentIndex(-1)
                combo.blockSignals(False)

    def update_all_color_combos(self):
        used_colors = set(self.selected_colors.values())
        for key, combo in self.parameter_color_combos.items():
            current_color = self.selected_colors.get(key)
            combo.blockSignals(True)
            combo.clear()
            for name, hex_color in zip(self.color_names, self.color_values):
                if hex_color not in used_colors or hex_color == current_color:
                    combo.addItem(name)
                    idx = combo.count() - 1
                    combo.setItemData(idx, hex_color, Qt.UserRole)
                    if hex_color == current_color:
                        combo.setCurrentIndex(idx)
            if not current_color:
                combo.setCurrentIndex(-1)
            combo.blockSignals(False)

    def update_parameter_value(self, message_type, parameter, value):
        """Update the label value for a specific parameter and store data for plotting"""
        key = f"{message_type}_{parameter}"
        if key not in self.parameter_labels:
            return
        if message_type in ["DEBUG_MESSAGE_1", "DEBUG_MESSAGE_2"]:
            if not self.debug_visible or not self.debug_unlocked:
                return
        
        # Update label
        self.parameter_labels[key].setText(str(value))
        
        # Store data for plotting if it's numeric
        try:
            numeric_value = float(value)
            current_time = datetime.now()
            
            # Store timestamp and value
            self.parameter_data[key]['timestamps'].append(current_time)
            self.parameter_data[key]['values'].append(numeric_value)
            
        except (ValueError, TypeError):
            # Skip non-numeric values
            pass

    def update_plot(self):
        """Update the plot with current data"""
        if not self.plot_lines:
            return
            
        for param_key, line in self.plot_lines.items():
            if param_key in self.parameter_data:
                data = self.parameter_data[param_key]
                if data['timestamps'] and data['values']:
                    timestamps = list(data['timestamps'])
                    values = list(data['values'])
                    line.set_data(timestamps, values)
        
        # Auto-scale the plot
        if any(self.parameter_data[key]['timestamps'] for key in self.plot_lines.keys()):
            self.ax.relim()
            self.ax.autoscale_view()
            
            # Format x-axis
            self.figure.autofmt_xdate()
        
        self.canvas.draw()

    def on_mouse_move(self, event):
        """Show data values when mouse hovers over the plot"""
        if event.inaxes != self.ax:
            return
            
        # Find closest data point
        if not self.plot_lines:
            return
            
        closest_info = None
        min_distance = float('inf')
        
        for param_key, line in self.plot_lines.items():
            if param_key in self.parameter_data:
                data = self.parameter_data[param_key]
                if not data['timestamps'] or not data['values']:
                    continue
                    
                timestamps = np.array([mdates.date2num(t) for t in data['timestamps']])
                values = np.array(data['values'])
                
                if len(timestamps) == 0:
                    continue
                    
                # Convert mouse position to data coordinates
                mouse_x = mdates.date2num(mdates.num2date(event.xdata)) if event.xdata else 0
                
                # Find closest point
                distances = np.sqrt((timestamps - mouse_x)**2 + 
                                  ((values - event.ydata) / (self.ax.get_ylim()[1] - self.ax.get_ylim()[0]))**2)
                min_idx = np.argmin(distances)
                
                if distances[min_idx] < min_distance:
                    min_distance = distances[min_idx]
                    closest_info = {
                        'param': param_key,
                        'time': data['timestamps'][min_idx],
                        'value': data['values'][min_idx]
                    }
        
        # Update title with hover info
        if closest_info and min_distance < 0.1:  # Within reasonable distance
            title = f"Real-time Parameter Monitoring | {closest_info['param']}: {closest_info['value']:.2f} at {closest_info['time'].strftime('%H:%M:%S')}"
            self.ax.set_title(title)
        else:
            self.ax.set_title("Real-time Parameter Monitoring")
        
        self.canvas.draw_idle()

    def zoom_in(self):
        """Zoom in on the plot"""
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()
        
        x_center = (xlim[0] + xlim[1]) / 2
        y_center = (ylim[0] + ylim[1]) / 2
        
        x_range = (xlim[1] - xlim[0]) * 0.4  # 40% of current range
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
        
        x_range = (xlim[1] - xlim[0]) * 1.25  # 125% of current range
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
            f"parameter_plot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
            "PNG Files (*.png);;PDF Files (*.pdf);;SVG Files (*.svg)"
        )
        if filename:
            self.figure.savefig(filename, dpi=300, bbox_inches='tight')

    def clear_data(self):
        """Clear all stored data and reset the plot"""
        self.parameter_data.clear()
        for line in self.plot_lines.values():
            line.set_data([], [])
        self.ax.set_title("Real-time Parameter Monitoring")
        self.canvas.draw()

    # Debug message methods remain the same
    def unlock_debug_messages(self):
        dialog = PasswordDialog(self)
        if dialog.exec_():
            self.debug_unlocked = True
            for key, label in self.parameter_labels.items():
                if key.startswith("DEBUG_MESSAGE"):
                    label.setText("--")
                    label.setCursor(Qt.ArrowCursor)
                    label.mousePressEvent = None
            root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                if "DEBUG_MESSAGE" in item.text(0):
                    msg_name = item.text(0).split(' ')[1] if '🔒' in item.text(0) else item.text(0)
                    if 'DEBUG_MESSAGE' in msg_name:
                        item.setText(0, f"{msg_name}")
                        item.setForeground(0, Qt.black)
            return True
        return False

    def lock_debug_messages(self):
        self.debug_unlocked = False
        for key, label in self.parameter_labels.items():
            if key.startswith("DEBUG_MESSAGE"):
                label.setText("[LOCKED]")
                label.setCursor(Qt.PointingHandCursor)
                label.mousePressEvent = lambda event, label=label: self.unlock_debug_messages()
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if "DEBUG_MESSAGE" in item.text(0):
                msg_name = item.text(0).split(' ')[1] if '🔒' in item.text(0) else item.text(0)
                if 'DEBUG_MESSAGE' in msg_name:
                    item.setText(0, f"{msg_name} (Private)")
                    item.setForeground(0, Qt.darkGray)

    def add_debug_items_to_tree(self):
        for message_type, parameters in self.debug_message_structure.items():
            message_item = QTreeWidgetItem([message_type, "", "", ""])
            message_item.setForeground(0, Qt.black)
            self.tree.addTopLevelItem(message_item)
            for param in parameters:
                param_item = QTreeWidgetItem([param])
                message_item.addChild(param_item)
                value_label = QLabel("--")
                value_label.setMinimumWidth(100)
                value_label.setStyleSheet("color: #2196F3;")
                font = QFont()
                font.setBold(True)
                font.setPointSize(11)
                value_label.setFont(font)
                key = f"{message_type}_{param}"
                self.parameter_labels[key] = value_label
                self.tree.setItemWidget(param_item, 1, value_label)
                
                color_combo = ColorBoxComboBox()
                color_combo.setFont(self.font())
                color_combo.setMinimumWidth(120)
                for name, hex_color in zip(self.color_names, self.color_values):
                    color_combo.addItem(name)
                    idx = color_combo.count() - 1
                    color_combo.setItemData(idx, hex_color, Qt.UserRole)
                color_combo.setCurrentIndex(-1)
                color_combo.currentIndexChanged.connect(lambda idx, k=key: self.on_color_changed(k))
                self.tree.setItemWidget(param_item, 2, color_combo)
                self.parameter_color_combos[key] = color_combo
                
                checkbox = QCheckBox()
                checkbox.setFont(self.font())
                checkbox.stateChanged.connect(lambda state, k=key: self.on_checkbox_changed(k, state))
                enable_widget = QWidget()
                enable_layout = QHBoxLayout(enable_widget)
                enable_layout.addStretch()
                enable_layout.addWidget(checkbox)
                enable_layout.addStretch()
                enable_layout.setContentsMargins(0, 0, 0, 0)
                self.tree.setItemWidget(param_item, 3, enable_widget)
                self.parameter_checkboxes[key] = checkbox

    def remove_debug_items_from_tree(self):
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount() - 1, -1, -1):
            item = root.child(i)
            if "DEBUG_MESSAGE" in item.text(0):
                root.removeChild(item)
                message_type = item.text(0)
                for param in self.debug_message_structure.get(message_type, []):
                    key = f"{message_type}_{param}"
                    if key in self.parameter_labels:
                        del self.parameter_labels[key]
                    if key in self.parameter_color_combos:
                        del self.parameter_color_combos[key]
                    if key in self.parameter_checkboxes:
                        del self.parameter_checkboxes[key]
                    if key in self.selected_colors:
                        del self.selected_colors[key]
                    if key in self.plot_lines:
                        self.plot_lines[key].remove()
                        del self.plot_lines[key]

    def show_context_menu(self, position):
        menu = QMenu()
        item = self.tree.itemAt(position)
        if self.debug_visible:
            hide_action = menu.addAction("Hide Debug Messages")
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            if action == hide_action:
                self.debug_visible = False
                self.remove_debug_items_from_tree()
                self.debug_unlocked = False
        else:
            show_action = menu.addAction("Show Debug Messages")
            action = menu.exec_(self.tree.viewport().mapToGlobal(position))
            if action == show_action:
                if not self.debug_unlocked:
                    if self.unlock_debug_messages():
                        self.debug_visible = True
                        self.add_debug_items_to_tree()
                else:
                    self.debug_visible = True
                    self.add_debug_items_to_tree()

    def get_serial_obj(self):
        return self.main_window.serial_obj
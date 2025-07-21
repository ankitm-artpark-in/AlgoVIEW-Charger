from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                             QMenu, QComboBox, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QBrush, QColor
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
        # self.parameter_data removed (was used for plotting)
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)

        # Create main horizontal layout (left panel only, fixed width)
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)

        left_panel = QWidget()
        left_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)
        left_panel.setFixedWidth(int(self.width() * 0.75))  # 75% of window width
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Create tree widget with parameter dropdowns
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Parameter", "Value", "Color", "Enable"])  # four columns
        self.tree.setColumnWidth(0, 200)  # Set width for parameter column
        self.tree.setColumnWidth(1, 50)  # Set width for value column
        self.tree.setColumnWidth(2, 120)  # Set width for color column
        self.tree.setColumnWidth(3, 30)   # Set width for enable column
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.debug_unlocked = False
        self.debug_visible = False  # New flag to track visibility of debug messages
        self.populate_tree()
        left_layout.addWidget(self.tree)
        main_layout.addWidget(left_panel)
        main_layout.addStretch(1)  # Left-align the left panel

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
                color_combo.setCurrentIndex(-1)  # No color selected by default
                color_combo.currentIndexChanged.connect(lambda idx, k=key: self.on_color_changed(k))
                self.tree.setItemWidget(param_item, 2, color_combo)
                self.parameter_color_combos[key] = color_combo

                # Enable checkbox for each parameter (centered)
                checkbox = QCheckBox()
                checkbox.setFont(self.font())
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
        # Update selected_colors dict
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
        # self.update_graph() removed

    def update_color_combos_optimized(self, changed_key):
        # Only update the changed combo and those that have a color conflict
        used_colors = set(self.selected_colors.values())
        for key, combo in self.parameter_color_combos.items():
            current_color = self.selected_colors.get(key)
            # Only update combos that are not the changed one and do not have the selected color
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
        # Get all selected colors except for the current combo
        used_colors = set(self.selected_colors.values())
        for key, combo in self.parameter_color_combos.items():
            current_color = self.selected_colors.get(key)
            combo.blockSignals(True)
            combo.clear()
            for name, hex_color in zip(self.color_names, self.color_values):
                # Only add color if not used elsewhere, or if it's the current selection for this combo
                if hex_color not in used_colors or hex_color == current_color:
                    combo.addItem(name)
                    idx = combo.count() - 1
                    combo.setItemData(idx, hex_color, Qt.UserRole)
                    if hex_color == current_color:
                        combo.setCurrentIndex(idx)
            # If no color is selected for this parameter, set to '--' (first item)
            if not current_color:
                combo.setCurrentIndex(-1)
            combo.blockSignals(False)

    def update_parameter_value(self, message_type, parameter, value):
        """Update the label value for a specific parameter and update the graph data"""
        key = f"{message_type}_{parameter}"
        if key not in self.parameter_labels:
            return
        if message_type in ["DEBUG_MESSAGE_1", "DEBUG_MESSAGE_2"]:
            if not self.debug_visible or not self.debug_unlocked:
                return
        self.parameter_labels[key].setText(str(value))
        # Plotting code removed

    # update_graph removed (graph functionality eliminated)

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
                msg_name = item.text(0).split(' ')[1] if '�' in item.text(0) else item.text(0)
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
                self.tree.setItemWidget(param_item, 3, checkbox)
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

    def unlock_debug_messages(self):
        dialog = PasswordDialog(self)
        if dialog.exec_():
            self.debug_unlocked = True
            return True
        return False

    def get_serial_obj(self):
        return self.main_window.serial_obj

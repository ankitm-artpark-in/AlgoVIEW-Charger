from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                             QLabel, QTreeWidget, QTreeWidgetItem, QSizePolicy,
                             QMenu, QComboBox, QCheckBox)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QStandardItemModel, QStandardItem, QBrush, QColor
from color_display_box import ColorBoxDelegate
from password_dialog import PasswordDialog

class LiveDataWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.parameter_labels = {}  # Store labels for each parameter
        self.section_color_combos = {}  # Store color combo boxes for each section
        self.section_checkboxes = {}  # Store checkboxes for each section
        self.debug_unlocked = False  # Track if debug messages are unlocked
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)

        # Create main horizontal layout
        main_layout = QHBoxLayout()
        self.setLayout(main_layout)
        
        # Create left panel (40% width)
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
        self.tree.setColumnWidth(2, 75)  # Set width for color column
        self.tree.setColumnWidth(3, 30)   # Set width for enable column
        self.tree.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self.show_context_menu)
        self.debug_unlocked = False
        self.debug_visible = False  # New flag to track visibility of debug messages
        self.populate_tree()
        left_layout.addWidget(self.tree)
        
        # Add left panel to main layout
        main_layout.addWidget(left_panel)
        
        # Right panel (60% width)
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)
        
        # Add right panel to main layout
        main_layout.addWidget(right_panel)
        
        # Set stretch factors for panels (40:60 ratio)
        main_layout.setStretchFactor(left_panel, 0)
        main_layout.setStretchFactor(right_panel, 1)
        
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
        color_names = ["Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "Black"]
        color_values = ["#FF0000", "#008000", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF", "#000000"]

        for message_type, parameters in self.message_structure.items():
            message_item = QTreeWidgetItem([message_type, "", "", ""])
            message_item.setForeground(0, Qt.black)
            self.tree.addTopLevelItem(message_item)

            # Color dropdown with colored box using ColorBoxDelegate
            color_combo = QComboBox()
            color_combo.setFont(self.font())
            model = QStandardItemModel()
            for name, hex_color in zip(color_names, color_values):
                item = QStandardItem(name)
                item.setData(hex_color, Qt.UserRole)
                item.setForeground(QBrush(QColor(hex_color)))
                model.appendRow(item)
            color_combo.setModel(model)
            color_combo.setItemDelegate(ColorBoxDelegate(color_combo))
            color_combo.setCurrentIndex(0)
            self.tree.setItemWidget(message_item, 2, color_combo)
            self.section_color_combos[message_type] = color_combo

            checkbox = QCheckBox()
            checkbox.setFont(self.font())
            self.tree.setItemWidget(message_item, 3, checkbox)
            self.section_checkboxes[message_type] = checkbox

            for param in parameters:
                param_item = QTreeWidgetItem([param])
                message_item.addChild(param_item)
                value_label = QLabel("--")
                value_label.setMinimumWidth(80)
                value_label.setStyleSheet("color: #2196F3;")
                font = QFont()
                font.setBold(True)
                font.setPointSize(11)
                value_label.setFont(font)
                key = f"{message_type}_{param}"
                self.parameter_labels[key] = value_label
                self.tree.setItemWidget(param_item, 1, value_label)

        if self.debug_visible:
            self.add_debug_items_to_tree()
        self.tree.expandAll()
        
    def update_parameter_value(self, message_type, parameter, value):
        """Update the label value for a specific parameter"""
        key = f"{message_type}_{parameter}"
        
        # Don't update if the parameter doesn't exist in our labels
        if key not in self.parameter_labels:
            return
            
        # For debug messages, only update if they're visible and unlocked
        if message_type in ["DEBUG_MESSAGE_1", "DEBUG_MESSAGE_2"]:
            if not self.debug_visible or not self.debug_unlocked:
                return
                
        self.parameter_labels[key].setText(str(value))
        
    def unlock_debug_messages(self):
        """Show password dialog and unlock debug messages if correct"""
        dialog = PasswordDialog(self)
        if dialog.exec_():
            self.debug_unlocked = True
            # Update all debug message values to show actual values
            for key, label in self.parameter_labels.items():
                if key.startswith("DEBUG_MESSAGE"):
                    label.setText("--")  # Reset to default, will be updated by next message
                    label.setCursor(Qt.ArrowCursor)  # Reset cursor
                    label.mousePressEvent = None  # Remove click handler
            
            # Update tree items to show unlocked state
            root = self.tree.invisibleRootItem()
            for i in range(root.childCount()):
                item = root.child(i)
                if "DEBUG_MESSAGE" in item.text(0):
                    msg_name = item.text(0).split(' ')[1] if '🔒' in item.text(0) else item.text(0)
                    if 'DEBUG_MESSAGE' in msg_name:
                        item.setText(0, f"{msg_name}")
                        item.setForeground(0, Qt.black)
                    
    def lock_debug_messages(self):
        """Lock the debug messages"""
        self.debug_unlocked = False
        
        # Update all debug message values to show locked state
        for key, label in self.parameter_labels.items():
            if key.startswith("DEBUG_MESSAGE"):
                label.setText("[LOCKED]")
                label.setCursor(Qt.PointingHandCursor)
                label.mousePressEvent = lambda event, label=label: self.unlock_debug_messages()
        
        # Update tree items to show locked state
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount()):
            item = root.child(i)
            if "DEBUG_MESSAGE" in item.text(0):
                msg_name = item.text(0).split(' ')[1] if '�' in item.text(0) else item.text(0)
                if 'DEBUG_MESSAGE' in msg_name:
                    item.setText(0, f"{msg_name} (Private)")
                    item.setForeground(0, Qt.darkGray)
                    
    def add_debug_items_to_tree(self):
        """Add debug message items to the tree widget"""
        for message_type, parameters in self.debug_message_structure.items():
            message_item = QTreeWidgetItem([message_type, "", "", ""])
            message_item.setForeground(0, Qt.black)
            self.tree.addTopLevelItem(message_item)
            
            # Add color dropdown for section
            color_combo = QComboBox()
            color_combo.setFont(self.font())
            
            color_names = ["Red", "Green", "Blue", "Yellow", "Cyan", "Magenta", "Black"]
            color_values = ["#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#00FFFF", "#FF00FF", "#000000"]
            
            model = QStandardItemModel()
            for name, hex_color in zip(color_names, color_values):
                item = QStandardItem(name)
                item.setForeground(QBrush(QColor(hex_color)))
                model.appendRow(item)
            color_combo.setModel(model)
            color_combo.setCurrentIndex(0)
            self.tree.setItemWidget(message_item, 2, color_combo)
            self.section_color_combos[message_type] = color_combo

            # Add checkbox for section
            checkbox = QCheckBox()
            checkbox.setFont(self.font())
            self.tree.setItemWidget(message_item, 3, checkbox)
            self.section_checkboxes[message_type] = checkbox
            
            # Add parameters as children with value labels
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

    def remove_debug_items_from_tree(self):
        """Remove debug message items from the tree widget"""
        root = self.tree.invisibleRootItem()
        for i in range(root.childCount() - 1, -1, -1):  # Iterate backwards to safely remove items
            item = root.child(i)
            if "DEBUG_MESSAGE" in item.text(0):
                root.removeChild(item)
                # Remove the corresponding labels from our dictionary
                message_type = item.text(0)
                for param in self.debug_message_structure.get(message_type, []):
                    key = f"{message_type}_{param}"
                    if key in self.parameter_labels:
                        del self.parameter_labels[key]

    def show_context_menu(self, position):
        """Show context menu for right-click"""
        menu = QMenu()
        item = self.tree.itemAt(position)

        # Add debug visibility options
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
                    if self.unlock_debug_messages():  # Only show if password is correct
                        self.debug_visible = True
                        self.add_debug_items_to_tree()
                else:
                    self.debug_visible = True
                    self.add_debug_items_to_tree()

    def unlock_debug_messages(self):
        """Show password dialog and unlock debug messages if correct"""
        dialog = PasswordDialog(self)
        if dialog.exec_():
            self.debug_unlocked = True
            return True
        return False

    def get_serial_obj(self):
        return self.main_window.serial_obj

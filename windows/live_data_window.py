
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QPushButton


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from message_parser import parse_message

class live_data_window(QWidget):
    def __init__(self, send_command_callback=None):
        super().__init__()
        self.setWindowTitle('Live Data')
        self.send_command_callback = send_command_callback
        self.groups = {
            "Brick A": ["Cell 1", "Cell 2", "Cell 3", "Cell 4"],
            "Brick B": ["Cell 5", "Cell 6", "Cell 7", "Cell 8"],
            "Charger ViT": ["Charger Voltage", "Charger Current", "Charger Temp", "Charger AC Value"],
            "Temp Data": ["Volta Max Temp", "Volta Avg Temp", "Ambient Temp"],
            "Debug Messages": ["Cell Count", "Charger On Status", "Current Count", "Voltage Count", "Cell Balance Status"],
            "Debug Messages 2": ["Charger Safety Off", "Battery Vtg read value", "Charger state", "Charger O/P On", "Volta Heartbeat", "Charger Error Flag"]
        }
        self.selected_params = set()
        self.latest_data = {}
        self.param_labels = {}  # (group, param): QLabel
        self.display_rows = []  # Store table rows for cleanup
        self.setup_ui()

    def update_live_data(self, message):
        parsed = parse_message(message)
        msg_type = parsed['type']
        data = parsed['data']
        self.latest_data.update(data)
        self.refresh_selected_data()

    def refresh_selected_data(self):
        # Remove all rows from the table
        self.data_table.setRowCount(0)
        self.param_labels.clear()
        row = 0
        for group, params in self.groups.items():
            for param in params:
                if (group, param) in self.selected_params:
                    value = self.latest_data.get(param, "-")
                    self.data_table.insertRow(row)
                    from PyQt5.QtWidgets import QTableWidgetItem
                    group_item = QTableWidgetItem(group)
                    param_item = QTableWidgetItem(param)
                    value_item = QTableWidgetItem(str(value))
                    self.data_table.setItem(row, 0, group_item)
                    self.data_table.setItem(row, 1, param_item)
                    self.data_table.setItem(row, 2, value_item)
                    self.param_labels[(group, param)] = value_item
                    row += 1


    def setup_ui(self):
        from PyQt5.QtGui import QFont
        from PyQt5.QtWidgets import QComboBox, QCheckBox, QTreeWidget, QTreeWidgetItem, QHBoxLayout, QSizePolicy, QWidget, QVBoxLayout, QLabel
        main_layout = QVBoxLayout(self)

        # --- Transmission Control Group (fixed at top) ---
        default_font = QFont()
        default_font.setPointSize(10)
        transmission_group = QGroupBox('Transmission Control')
        transmission_group.setFont(default_font)
        transmission_layout = QHBoxLayout()
        transmission_layout.setContentsMargins(10, 5, 10, 5)

        self.reception_on_button = QPushButton('Reception ON')
        self.reception_on_button.setFont(default_font)
        self.reception_off_button = QPushButton('Reception OFF')
        self.reception_off_button.setFont(default_font)
        self.reception_once_button = QPushButton('Reception ONCE')
        self.reception_once_button.setFont(default_font)

        if self.send_command_callback:
            self.reception_on_button.clicked.connect(lambda: self.send_command_callback("Reception_ON"))
            self.reception_off_button.clicked.connect(lambda: self.send_command_callback("Reception_OFF"))
            self.reception_once_button.clicked.connect(lambda: self.send_command_callback("Reception_ONCE"))

        transmission_layout.addWidget(self.reception_on_button)
        transmission_layout.addWidget(self.reception_off_button)
        transmission_layout.addWidget(self.reception_once_button)
        transmission_group.setLayout(transmission_layout)
        main_layout.addWidget(transmission_group)

        # --- Group/Parameter selection area (in a fixed-width container) ---
        tree_container = QWidget()
        tree_layout = QVBoxLayout(tree_container)
        tree_layout.setContentsMargins(0, 0, 0, 0)
        tree_layout.setSpacing(0)

        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Group", "Parameter"])
        self.tree.setColumnCount(2)
        self.tree.setRootIsDecorated(False)
        self.tree.setAlternatingRowColors(True)
        self.tree.setSelectionMode(QTreeWidget.NoSelection)
        self.tree.setMaximumHeight(350)

        for group, params in self.groups.items():
            group_item = QTreeWidgetItem([group, ""])
            for param in params:
                param_item = QTreeWidgetItem(["", param])
                param_item.setCheckState(0, 0)  # Unchecked
                group_item.addChild(param_item)
            self.tree.addTopLevelItem(group_item)
            group_item.setExpanded(False)  # Keep collapsed by default

        self.tree.itemChanged.connect(self.on_tree_item_changed)
        tree_layout.addWidget(self.tree)

        # Set the width policy to take 30% of the parent width
        tree_container.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        tree_container.setMinimumWidth(200)
        tree_container.setMaximumWidth(400)


        # --- Data display area (table) ---
        from PyQt5.QtWidgets import QTableWidget, QHeaderView
        self.data_table = QTableWidget(0, 3)
        self.data_table.setMinimumHeight(300)
        self.data_table.setHorizontalHeaderLabels(["Group", "Parameter", "Value"])
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.data_table.verticalHeader().setVisible(False)
        self.data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.data_table.setSelectionMode(QTableWidget.NoSelection)

        # --- Main horizontal layout for selection and data display ---
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)
        h_layout.addWidget(tree_container, 1)
        h_layout.addWidget(self.data_table, 2)
        main_layout.addLayout(h_layout)
        main_layout.addStretch(1)

    def on_tree_item_changed(self, item, column):
        # Update selected_params set based on checkbox state
        if item.parent() is not None:
            group = item.parent().text(0)
            param = item.text(1)
            checked = item.checkState(0) == 2
            if checked:
                self.selected_params.add((group, param))
            else:
                self.selected_params.discard((group, param))
            self.refresh_selected_data()

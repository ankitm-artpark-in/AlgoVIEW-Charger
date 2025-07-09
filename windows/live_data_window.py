
from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout, QGroupBox, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QScrollArea, QPushButton


import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from message_parser import parse_message

class live_data_window(QWidget):
    def __init__(self, send_command_callback=None):
        super().__init__()
        self.setWindowTitle('Live Data')
        self.tables = {}  # Store tables by group/parameter
        self.send_command_callback = send_command_callback
        self.setup_ui()

    def update_live_data(self, message):
        parsed = parse_message(message)
        msg_type = parsed['type']
        data = parsed['data']
        # Map message type to table and update values
        if msg_type == 'Brick_A':
            self.update_table('Brick A', data)
        elif msg_type == 'Brick_B':
            self.update_table('Brick B', data)
        elif msg_type == 'Charger_VIT':
            self.update_table('Charger ViT', data)
        elif msg_type == 'TEMP_DATA':
            self.update_table('Temp Data', data)
        elif msg_type == 'Debug_Message_1':
            self.update_table('Debug Messages', data)
        elif msg_type == 'Debug_Message_2':
            self.update_table('Debug Messages 2', data)
        # Add more as needed

    def update_table(self, group, data):
        table = self.tables.get(group)
        if not table:
            return
        for i in range(table.rowCount()):
            param = table.item(i, 0).text()
            if param in data:
                table.setItem(i, 1, QTableWidgetItem(str(data[param])))

    def setup_ui(self):
        from PyQt5.QtGui import QFont
        def create_group_box(title, parameters):
            box = QGroupBox(title)
            layout = QVBoxLayout()
            table = QTableWidget(len(parameters), 2)
            table.setHorizontalHeaderLabels(['Parameter', 'Data'])
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            table.verticalHeader().setVisible(False)
            table.setEditTriggers(QTableWidget.NoEditTriggers)
            table.setSelectionMode(QTableWidget.NoSelection)
            table.setStyleSheet("QTableWidget::item { padding-left: 2px; padding-right: 2px; }")
            for i, param in enumerate(parameters):
                table.setItem(i, 0, QTableWidgetItem(param))
                table.setItem(i, 1, QTableWidgetItem(""))
            layout.addWidget(table)
            box.setLayout(layout)
            self.tables[title] = table
            return box

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
        # self.reception_on_button.setEnabled(False)
        self.reception_off_button = QPushButton('Reception OFF')
        self.reception_off_button.setFont(default_font)
        # self.reception_off_button.setEnabled(False)
        self.reception_once_button = QPushButton('Reception ONCE')
        self.reception_once_button.setFont(default_font)
        # self.reception_once_button.setEnabled(False)

        if self.send_command_callback:
            self.reception_on_button.clicked.connect(lambda: self.send_command_callback("Reception_ON"))
            self.reception_off_button.clicked.connect(lambda: self.send_command_callback("Reception_OFF"))
            self.reception_once_button.clicked.connect(lambda: self.send_command_callback("Reception_ONCE"))

        transmission_layout.addWidget(self.reception_on_button)
        transmission_layout.addWidget(self.reception_off_button)
        transmission_layout.addWidget(self.reception_once_button)
        transmission_group.setLayout(transmission_layout)
        main_layout.addWidget(transmission_group)

        # --- Main Data Area (scrollable) ---
        h_layout = QHBoxLayout()

        brick_a_box = create_group_box("Brick A", ["Cell 1", "Cell 2", "Cell 3", "Cell 4"])
        brick_b_box = create_group_box("Brick B", ["Cell 5", "Cell 6", "Cell 7", "Cell 8"])
        charger_box = create_group_box("Charger ViT", ["Charger Voltage", "Charger Current", "Charger Temp", "Charger AC Value"])
        temp_box = create_group_box("Temp Data", ["Volta Max Temp", "Volta Avg Temp", "Ambient Temp"])
        debug_msg_1 = create_group_box("Debug Messages", ["Cell Count", "Charger On Status", "Current Count", "Voltage Count", "Cell Balance Status"])
        debug_msg_2 = create_group_box("Debug Messages 2", ["Charger Safety Off", "Battery Vtg read value", "Charger state", "Charger O/P On", "Volta Heartbeat", "Charger Error Flag"])

        left_layout = QVBoxLayout()
        left_layout.addWidget(brick_a_box)
        left_layout.addWidget(brick_b_box)
        left_layout.addWidget(charger_box)
        left_layout.addWidget(temp_box)
        left_layout.addWidget(debug_msg_1)
        left_layout.addWidget(debug_msg_2)

        left_widget = QWidget()
        left_widget.setLayout(left_layout)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(left_widget)
        h_layout.addWidget(scroll_area, stretch=1)

        # Placeholder for the rest of the window (right side)
        right_placeholder = QLabel('Live Data Display Area')
        h_layout.addWidget(right_placeholder, stretch=3)

        main_layout.addLayout(h_layout)

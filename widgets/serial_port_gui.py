from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QGridLayout, QLabel, QHeaderView, QPushButton, QTableWidget, QTableWidgetItem
from PySide6.QtGui import QFont
from widgets import ConnectionSettings, CenterScreen
from utils.data_management import import_data_dialog, save_data_buffer

class SerialPortGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoX-VIEW")
        self.serial_obj = None
        self.buffer = bytearray()
        self.layout = QVBoxLayout()

        # Buffer for saved data frames
        self.saved_data_buffers = {}  # key: buffer_name, value: list of dicts

        # Table for displaying saved data info (moved to bottom, with timestamp and status)
        self.saved_data_table = QTableWidget()
        self.saved_data_table.setColumnCount(4)
        self.saved_data_table.setHorizontalHeaderLabels(["Battery ID", "Cycle Count", "Timestamp", "Status"])
        self.saved_data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.saved_data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.saved_data_table.setSelectionMode(QTableWidget.SingleSelection)
        self.saved_data_table.setFixedHeight(180)
        header = self.saved_data_table.horizontalHeader()
        for i in range(self.saved_data_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.saved_data_table.cellClicked.connect(self.handle_saved_data_table_click)

        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)

        # Charger Info Section
        self.charger_info_box = QGroupBox("Charger Info")
        self.charger_info_layout = QGridLayout()
        self.charger_hw_label = QLabel("-")
        self.charger_product_id_label = QLabel("-")
        self.charger_serial_label = QLabel("-")
        self.charger_fw_label = QLabel("-")
        self.charger_info_layout.addWidget(QLabel("HW Version:"), 0, 0)
        self.charger_info_layout.addWidget(self.charger_hw_label, 0, 1)
        self.charger_info_layout.addWidget(QLabel("Product ID:"), 0, 2)
        self.charger_info_layout.addWidget(self.charger_product_id_label, 0, 3)
        self.charger_info_layout.addWidget(QLabel("Serial No:"), 1, 0)
        self.charger_info_layout.addWidget(self.charger_serial_label, 1, 1)
        self.charger_info_layout.addWidget(QLabel("FW Version:"), 1, 2)
        self.charger_info_layout.addWidget(self.charger_fw_label, 1, 3)
        self.charger_info_box.setLayout(self.charger_info_layout)
        self.layout.addWidget(self.charger_info_box)
        self.connection_settings = ConnectionSettings(self)
        self.layout.addWidget(self.connection_settings)
        self.center_screen_widget = CenterScreen(self)
        self.layout.addWidget(self.center_screen_widget)
        self.import_btn = QPushButton("Import Data")
        self.import_btn.clicked.connect(lambda: import_data_dialog(self))
        self.layout.addWidget(self.import_btn)
        self.layout.addWidget(self.saved_data_table)
        self.setLayout(self.layout)

        self.connection_settings.refresh_clicked.connect(self.refresh_ports)
        self.connection_settings.connect_clicked.connect(self.connect_port)
        self.connection_settings.disconnect_clicked.connect(self.disconnect_port)

    def update_charger_info(self, hw_version, product_id, serial_no, fw_major, fw_minor):
        self.charger_hw_label.setText(str(hw_version))
        self.charger_product_id_label.setText(str(product_id))
        self.charger_serial_label.setText(str(serial_no))
        self.charger_fw_label.setText(f"{fw_major}.{fw_minor}")

    def refresh_ports(self):
        from serial_utils import refresh_ports
        refresh_ports(self.connection_settings.port_combo, self)

    def connect_port(self):
        from serial_utils import connect_serial
        self.buffer.clear()
        self.serial_obj = connect_serial(self.connection_settings.port_combo, self.connection_settings, self)

    def disconnect_port(self):
        from serial_utils import disconnect_serial
        self.serial_obj = disconnect_serial(self.serial_obj, self.connection_settings, self)

    def read_serial_data(self):
        from serial_utils import read_serial
        read_serial(self.serial_obj, self.buffer, self, self.connection_settings)

    def save_data_buffer(self, buffer_name, data_frames):
        save_data_buffer(self, buffer_name, data_frames)

    def handle_saved_data_table_click(self, row, column):
        bat_id_item = self.saved_data_table.item(row, 0)
        cycle_count_item = self.saved_data_table.item(row, 1)
        if not bat_id_item or not cycle_count_item:
            return
        buffer_name = f"b_{bat_id_item.text()}_c_{cycle_count_item.text()}"
        if buffer_name in self.saved_data_buffers:
            self.show_data_view_dialog(buffer_name, self.saved_data_buffers[buffer_name])
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Not Found", f"No data found for {buffer_name}")

    def show_data_view_dialog(self, buffer_name, data_frames):
        from widgets.data_view_dialog import DataViewDialog
        dlg = DataViewDialog(self, buffer_name, data_frames)
        dlg.exec()

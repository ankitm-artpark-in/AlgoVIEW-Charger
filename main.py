import sys
sys.dont_write_bytecode = True

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget
)

from PySide6.QtGui import QFont
from PySide6.QtCore import QTimer

# local file imports
from serial_utils import refresh_ports, connect_serial, disconnect_serial, handle_disconnect, read_serial
from widgets import ConnectionSettings, CenterScreen

class SerialPortGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoX-VIEW")
        self.serial_obj = None
        self.buffer = bytearray()
        self.layout = QVBoxLayout()

        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)

        # Charger Info Section
        from PySide6.QtWidgets import QGroupBox, QGridLayout, QLabel
        self.charger_info_box = QGroupBox("Charger Info")
        self.charger_info_layout = QGridLayout()
        self.charger_hw_label = QLabel("-")
        self.charger_product_id_label = QLabel("-")
        self.charger_serial_label = QLabel("-")
        self.charger_fw_label = QLabel("-")
        # 2x2 grid: (0,0) HW, (0,1) Product, (1,0) Serial, (1,1) FW
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

        # Set the layout
        self.setLayout(self.layout)

        # Connect signals to buttons
        self.connection_settings.refresh_clicked.connect(self.refresh_ports)
        self.connection_settings.connect_clicked.connect(self.connect_port)
        self.connection_settings.disconnect_clicked.connect(self.disconnect_port)

    def update_charger_info(self, hw_version, product_id, serial_no, fw_major, fw_minor):
        self.charger_hw_label.setText(str(hw_version))
        self.charger_product_id_label.setText(str(product_id))
        self.charger_serial_label.setText(str(serial_no))
        self.charger_fw_label.setText(f"{fw_major}.{fw_minor}")

    def refresh_ports(self):
        refresh_ports(self.connection_settings.port_combo, self)

    def connect_port(self):
        self.buffer.clear()
        self.serial_obj = connect_serial(self.connection_settings.port_combo, self.connection_settings, self)
        # if self.serial_obj and self.serial_obj.is_open:
            # self.timer.start()

    def disconnect_port(self):
        # self.timer.stop()
        self.serial_obj = disconnect_serial(self.serial_obj, self.connection_settings, self)

    def read_serial_data(self):
        read_serial(self.serial_obj, self.buffer, self, self.connection_settings)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    default_font = QFont()
    default_font.setPointSize(11)
    
    window = SerialPortGUI()
    window.setFixedWidth(600)
    window.setFont(default_font)
    window.show()
    sys.exit(app.exec())

import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMessageBox, QGroupBox, QHBoxLayout, QComboBox, QPushButton, QLabel, QSizePolicy
)

from PySide6.QtGui import QFont
from PySide6.QtCore import Signal, QTimer

from refresh_ports import refresh_ports
from connect_serial import connect_serial
from disconnect_serial import disconnect_serial
from handle_disconnect import handle_disconnect
from connection_settings import ConnectionSettings
from read_serial import read_serial

# Tabs below connection settings
from PySide6.QtWidgets import QTabWidget
from live_data_window import LiveDataWindow
from sd_card_data_window import SDCardDataWindow
from saved_data_window import SavedDataWindow

class SerialPortGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoX-VIEW")
        self.serial_obj = None
        self.buffer = bytearray()
        self.layout = QVBoxLayout()

        # Set up timer for serial reading
        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)
        self.timer.setInterval(100)  # 100ms interval

        # Connection settings at the top
        self.connection_settings = ConnectionSettings(self)
        self.layout.addWidget(self.connection_settings)

        self.tabs = QTabWidget()
        self.live_data = LiveDataWindow(self)
        self.sd_card_data = SDCardDataWindow(self)
        self.saved_data = SavedDataWindow(self)
        self.tabs.addTab(self.live_data, "Live Data")
        self.tabs.addTab(self.sd_card_data, "SD Card Data")
        self.tabs.addTab(self.saved_data, "Saved Data")
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

        # Connect signals to slots
        self.connection_settings.refresh_clicked.connect(self.refresh_ports)
        self.connection_settings.connect_clicked.connect(self.connect_port)
        self.connection_settings.disconnect_clicked.connect(self.disconnect_port)

        self.refresh_ports()
        self.showMaximized()

    def refresh_ports(self):
        refresh_ports(self.connection_settings.port_combo, self)

    def connect_port(self):
        self.serial_obj = connect_serial(self.connection_settings.port_combo, self.connection_settings, self)
        if self.serial_obj and self.serial_obj.is_open:
            self.timer.start()

    def disconnect_port(self):
        self.timer.stop()
        self.serial_obj = disconnect_serial(self.serial_obj, self.connection_settings, self)

    def read_serial_data(self):
        read_serial(self.serial_obj, self.buffer, self, self.connection_settings)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SerialPortGUI()
    window.show()
    sys.exit(app.exec())

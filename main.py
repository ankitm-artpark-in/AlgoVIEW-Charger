import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QMessageBox, QGroupBox, QHBoxLayout, QComboBox, QPushButton, QLabel, QSizePolicy
)

from PySide6.QtGui import QFont
from PySide6.QtCore import Signal, QTimer

from serial_utils import refresh_ports, connect_serial, disconnect_serial, handle_disconnect, read_serial
from settings import ConnectionSettings

# Tabs below connection settings
from PySide6.QtWidgets import QTabWidget
from widgets import LiveDataWindow, SDCardDataWindow, SavedDataWindow

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

        self.timer = QTimer()
        self.timer.timeout.connect(self.read_serial_data)
        self.timer.setInterval(100)

        self.connection_settings = ConnectionSettings(self)
        self.layout.addWidget(self.connection_settings)

        self.tabs = QTabWidget()
        self.tabs.setFont(default_font)
        self.live_data = LiveDataWindow(self)
        self.live_data.setFont(default_font)
        self.sd_card_data = SDCardDataWindow(self)
        self.sd_card_data.setFont(default_font)
        self.saved_data = SavedDataWindow(self)
        self.saved_data.setFont(default_font)
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
    default_font = QFont()
    default_font.setPointSize(11)
    window = SerialPortGUI()
    window.setFont(default_font)
    window.show()
    sys.exit(app.exec())

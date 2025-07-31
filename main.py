import sys
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget
)

from PySide6.QtGui import QFont
from PySide6.QtCore import QTimer

# local file imports
from serial_utils import refresh_ports, connect_serial, disconnect_serial, handle_disconnect, read_serial
from settings import ConnectionSettings
from widgets import SDCardDataWindow

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
        self.timer.setInterval(1000)

        self.connection_settings = ConnectionSettings(self)
        self.layout.addWidget(self.connection_settings)

        self.tabs = QTabWidget()
        self.tabs.setFont(default_font)
        # self.live_data = LiveDataWindow(self)
        # self.live_data.setFont(default_font)
        self.sd_card_data = SDCardDataWindow(self)
        self.sd_card_data.setFont(default_font)
        # self.tabs.addTab(self.live_data, "Live Data")
        self.tabs.addTab(self.sd_card_data, "SD Card Data")
        self.layout.addWidget(self.tabs)

        self.setLayout(self.layout)

        # Connect signals to buttons
        self.connection_settings.refresh_clicked.connect(self.refresh_ports)
        self.connection_settings.connect_clicked.connect(self.connect_port)
        self.connection_settings.disconnect_clicked.connect(self.disconnect_port)

    def refresh_ports(self):
        refresh_ports(self.connection_settings.port_combo, self)

    def connect_port(self):
        self.buffer.clear()
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
    window.setFixedWidth(600)
    window.setFont(default_font)
    window.show()
    sys.exit(app.exec())

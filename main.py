from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QTabWidget
from widgets.connection_settings import ConnectionSettings
from windows.live_data_window import live_data_window
from windows.sd_card_data_window import sd_card_data_window
from windows.database_window import DatabaseWindow
import sys
from serial_utils.refresh_ports import refresh_ports
from serial_utils.connect_serial import connect_serial
from serial_utils.disconnect_serial import disconnect_serial
from widgets.more_menu import create_more_menu


from PyQt5.QtCore import QTimer

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('AlgoVIEW-Charger')
        self.current_device = 0x01  # Default device, can be set elsewhere
        self.buffer = bytearray()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.read_serial)
        self.timer.start(100)  # Poll every 100 ms
        self.setup_ui()

    def read_serial(self):
        # Use the modular read_serial to fill self.buffer and extract messages
        if not hasattr(self, 'serial_port') or not self.serial_port:
            return
        try:
            if self.serial_port.is_open:
                import serial
                if self.serial_port.in_waiting:
                    self.buffer.extend(self.serial_port.read(self.serial_port.in_waiting))
                    # Process all complete messages (15 bytes, 0x01 start, 0x02 end)
                    while len(self.buffer) >= 15:
                        if self.buffer[0] == 0x01 and self.buffer[14] == 0x02:
                            msg = self.buffer[:15]
                            # Update live data window if open
                            if self.live_data_view and self.live_data_view.isVisible():
                                self.live_data_view.update_live_data(msg)
                            self.buffer = self.buffer[15:]
                        else:
                            self.buffer = self.buffer[1:]
        except (Exception,) as e:
            # Optionally handle disconnect or error
            pass

    def send_command(self, command):
        if hasattr(self, 'serial_port') and self.serial_port and self.serial_port.is_open:
            if command == "Reception_ON":
                msg = bytes([self.current_device, 0xAA, 0x00, 0xA1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            elif command == "Reception_OFF":
                msg = bytes([self.current_device, 0xAA, 0x00, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            elif command == "Reception_ONCE":
                msg = bytes([self.current_device, 0xAA, 0x00, 0xAE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            else:
                return
            # Import and call send_raw_message from serial_utils
            from serial_utils.send_raw_message import send_raw_message
            send_raw_message(self, msg)

    def setup_ui(self):
        # --- Connection Settings Section ---
        self.connection_settings = ConnectionSettings()

        # Create the tab widget
        self.tabs = QTabWidget()
        # Create the tab pages (screens)
        self.live_data_tab = QWidget()
        self.sd_card_tab = QWidget()
        self.database_tab = QWidget()

        # Add tabs
        self.tabs.addTab(self.live_data_tab, "Live Data")
        self.tabs.addTab(self.sd_card_tab, "SD Card Data")
        self.tabs.addTab(self.database_tab, "Database")

        # Layout for each tab (remove margins and paddings)
        self.live_data_view = live_data_window(send_command_callback=self.send_command)
        live_data_layout = QVBoxLayout()
        live_data_layout.setContentsMargins(0, 0, 0, 0)
        live_data_layout.setSpacing(0)
        live_data_layout.addWidget(self.live_data_view)
        self.live_data_tab.setLayout(live_data_layout)

        self.sd_card_data_view = sd_card_data_window()
        sd_card_layout = QVBoxLayout()
        sd_card_layout.setContentsMargins(0, 0, 0, 0)
        sd_card_layout.setSpacing(0)
        sd_card_layout.addWidget(self.sd_card_data_view)
        self.sd_card_tab.setLayout(sd_card_layout)

        self.database_view = DatabaseWindow()
        database_layout = QVBoxLayout()
        database_layout.setContentsMargins(0, 0, 0, 0)
        database_layout.setSpacing(0)
        database_layout.addWidget(self.database_view)
        self.database_tab.setLayout(database_layout)

        # Main layout: connection settings always on top
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.connection_settings)

        main_layout.addSpacing(16)  # vertical space between connection settings and tabs
        main_layout.addWidget(self.tabs)
        self.setCentralWidget(main_widget)

        # Connect button signals to methods
        self.connection_settings.refresh_clicked.connect(self.refresh_ports)
        self.connection_settings.connect_clicked.connect(self.connect_serial)
        self.connection_settings.disconnect_clicked.connect(self.disconnect_serial)

    # --- Connection Settings Functionalities ---
    def refresh_ports(self):
        refresh_ports(self.connection_settings.port_combo)

    def connect_serial(self):
        if not hasattr(self, 'serial_port'):
            self.serial_port = None
            
        connect_serial(
            self.connection_settings.connect_button,
            self.connection_settings.disconnect_button,
            self.connection_settings.port_combo,
            self.connection_settings.refresh_button,
            parent=self
        )

    def disconnect_serial(self):
        disconnect_serial(
            self.connection_settings.connect_button,
            self.connection_settings.disconnect_button,
            self.connection_settings.port_combo,
            self.connection_settings.refresh_button,
            parent=self
        )
        
    # --- Window Management ---
    # No popups, all screens are tabs now

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

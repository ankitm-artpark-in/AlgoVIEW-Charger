from PyQt5.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget, QToolBar, QAction
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
        self.live_data_view = None
        self.sd_card_data_view = None
        self.database_view = None
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
        toolbar = QToolBar("Toolbar")
        self.addToolBar(toolbar)

        live_data_action = QAction('Live Data', self)
        sd_card_action = QAction('SD Card Data', self)
        database_action = QAction('Database', self)

        live_data_action.triggered.connect(self.live_data_window)
        sd_card_action.triggered.connect(self.sd_card_data_window)
        database_action.triggered.connect(self.database_window)

        toolbar.addAction(live_data_action)
        toolbar.addAction(sd_card_action)
        toolbar.addAction(database_action)

        # Three dots menu
        more_button, admin_action = create_more_menu(self)
        toolbar.addWidget(more_button)

        # --- Connection Settings Section ---
        self.connection_settings = ConnectionSettings()
        central_widget = QWidget()
        central_layout = QVBoxLayout(central_widget)
        central_layout.addWidget(self.connection_settings)

        self.central_placeholder = QWidget()
        central_layout.addWidget(self.central_placeholder)
        self.setCentralWidget(central_widget)

        self.central_layout = central_layout

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
    def live_data_window(self):
        if self.live_data_view is None or not self.live_data_view.isVisible():
            self.live_data_view = live_data_window(send_command_callback=self.send_command)
        self.live_data_view.show()

    def sd_card_data_window(self):
        if self.sd_card_data_view is None or not self.sd_card_data_view.isVisible():
            self.sd_card_data_view = sd_card_data_window()
        self.sd_card_data_view.show()

    def database_window(self):
        # Toggle database view
        if hasattr(self, 'database_widget_item') and self.database_widget_item is not None:
            self.central_layout.removeWidget(self.database_widget_item)
            self.database_widget_item.setParent(None)
            self.database_widget_item = None
            return

        self.database_view = DatabaseWindow()
        self.central_layout.addWidget(self.database_view)
        self.database_widget_item = self.database_view

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

from PyQt5.QtWidgets import QMessageBox

def handle_disconnect(self, message):
    if self.serial_port and self.serial_port.is_open:
        try:
            self.serial_port.close()
        except:
            pass
    self.serial_port = None
    self.connect_button.setEnabled(True)
    self.disconnect_button.setEnabled(False)
    self.port_combo.setEnabled(True)
    if self.is_logging:
        self.stop_logging()
    QMessageBox.warning(self, "Connection Error", message)

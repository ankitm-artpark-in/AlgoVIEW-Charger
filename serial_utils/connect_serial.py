import serial
from PySide6.QtWidgets import QMessageBox

def connect_serial(dropdown, connection_settings, parent_widget):
    port = dropdown.currentText()
    if port:
        try:
            ser = serial.Serial(port, baudrate=115200, timeout=1)
            QMessageBox.information(parent_widget, "Connected", f"Connected to {port}")
            # Enable disconnect, disable connect
            connection_settings.disconnect_button.setEnabled(True)
            connection_settings.connect_button.setEnabled(False)
            return ser
        except serial.SerialException as e:
            QMessageBox.critical(parent_widget, "Error", f"Failed to connect to {port}: {e}")
            return None
    else:
        QMessageBox.warning(parent_widget, "No Port Selected", "Please select a port.")
        return None

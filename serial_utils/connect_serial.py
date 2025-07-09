import serial
from PyQt5.QtWidgets import QMessageBox

def connect_serial(
    connect_button, disconnect_button, port_combo, refresh_button,
    parent=None,
):
    try:
        port = port_combo.currentText()
        parent.serial_port = serial.Serial(port, 115200, timeout=0.1)
        connect_button.setEnabled(False)
        disconnect_button.setEnabled(True)
        port_combo.setEnabled(False)
        refresh_button.setEnabled(False)

    except serial.SerialException as e:
        QMessageBox.critical(parent, "Connection Error", f"Failed to connect: {str(e)}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Unexpected error: {str(e)}")

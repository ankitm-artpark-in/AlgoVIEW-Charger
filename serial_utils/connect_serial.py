
import serial
from PyQt5.QtWidgets import QMessageBox
import sys
import importlib

def connect_serial(
    connect_button, disconnect_button, port_combo, refresh_button,
    parent=None,
):
    try:
        port = port_combo.currentText()
        # Dynamically import the serial_global module and set serial_port
        serial_global = importlib.import_module('serial_utils.serial_global')
        serial_global.serial_port = serial.Serial(port, 115200, timeout=0.1)
        print(f"Connected to {port}")
        connect_button.setEnabled(False)
        disconnect_button.setEnabled(True)
        port_combo.setEnabled(False)
        refresh_button.setEnabled(False)

    except serial.SerialException as e:
        QMessageBox.critical(parent, "Connection Error", f"Failed to connect: {str(e)}")
    except Exception as e:
        QMessageBox.critical(parent, "Error", f"Unexpected error: {str(e)}")

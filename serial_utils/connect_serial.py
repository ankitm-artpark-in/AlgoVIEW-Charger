import time
import serial
from PySide6.QtWidgets import QMessageBox

from serial_utils.read_serial import read_serial
from .send_frame import send_frame

def connect_serial(dropdown, connection_settings, parent_widget):
    if port := dropdown.currentText():
        try:
            ser = serial.Serial(port, baudrate=115200, timeout=1)
            QMessageBox.information(parent_widget, "Connected", f"Connected to {port}")
            
            # Enable disconnect, disable connect
            connection_settings.disconnect_button.setEnabled(True)
            connection_settings.connect_button.setEnabled(False)
            
            parent_widget.buffer.clear()
            send_frame(ser, "Reception_ONCE", parent_widget)
            read_serial(ser, parent_widget.buffer, parent_widget, connection_settings)
            
            parent_widget.buffer.clear()
            send_frame(ser, "Recent_Data", parent_widget)
            read_serial(ser, parent_widget.buffer, parent_widget, connection_settings)
            parent_widget.buffer.clear()
            time.sleep(2)
            
            send_frame(ser, "Cycle_Count_Data", parent_widget)
            read_serial(ser, parent_widget.buffer, parent_widget, connection_settings)
            parent_widget.buffer.clear()
            
            return ser
        
        except serial.SerialException as e:
            QMessageBox.critical(parent_widget, "Error", f"Failed to connect to {port}: {e}")
            return None
    else:
        QMessageBox.warning(parent_widget, "No Port Selected", "Please select a port.")
        return None
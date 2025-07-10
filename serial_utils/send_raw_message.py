
import serial
from PyQt5.QtWidgets import QMessageBox
from .serial_global import serial_port

def send_raw_message(self, msg):
    global serial_port
    if not serial_port or not serial_port.is_open:
        QMessageBox.warning(self, "Error", "Serial port not connected")
        return

    try:
        serial_port.write(msg)
        hex_data = ' '.join([f'{b:02X}' for b in msg])
    except (serial.SerialException, OSError) as e:
        QMessageBox.warning(self, "Error", "Device disconnected while sending message")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to send message: {str(e)}")

import serial
from PyQt5.QtWidgets import QMessageBox

def send_raw_message(self, msg):
    if not self.serial_port or not self.serial_port.is_open:
        QMessageBox.warning(self, "Error", "Serial port not connected")
        return

    try:
        self.serial_port.write(msg)
        hex_data = ' '.join([f'{b:02X}' for b in msg])
    except (serial.SerialException, OSError) as e:
        self.handle_disconnect("Device disconnected while sending message")
    except Exception as e:
        QMessageBox.critical(self, "Error", f"Failed to send message: {str(e)}")

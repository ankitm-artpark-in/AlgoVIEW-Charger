from PySide6.QtWidgets import QMessageBox
from .send_raw_msg import send_raw_msg

def send_frame(serial_obj, command, parent_widget):
    if serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open:
        try:
            if command == "Reception_ON":
                msg = bytes([0x30, 0xAA, 0x00, 0xA1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            elif command == "Reception_OFF":
                msg = bytes([0x30, 0xAA, 0x00, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
            else:
                return
            
            send_raw_msg(serial_obj, msg, parent_widget)
            QMessageBox.information(parent_widget, "Message Sent", "Command sent successfully.")
            
        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Error during sending command: {e}")
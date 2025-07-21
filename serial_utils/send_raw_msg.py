from PySide6.QtWidgets import QMessageBox
import serial_utils
from .handle_disconnect import handle_disconnect

def send_raw_msg(serial_obj, msg, parent_widget):
    if not (serial_obj or hasattr(serial_obj, 'is_open') and serial_obj.is_open):
        QMessageBox.warning(parent_widget, "Error", "Serial port not connected")
        return
    
    try:
        serial_obj.write(msg)
        hex_data = ' '.join([f'{b:02X}' for b in msg])
        
    except (serial_utils.SerialException, OSError) as e:
        handle_disconnect("Device disconnected while sending message")
    except Exception as e:
        QMessageBox.critical(parent_widget, "Error", f"Failed to send message: {str(e)}")
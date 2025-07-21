import serial_utils
from PySide6.QtWidgets import QMessageBox
from parsers.message_parser import process_message
from .handle_disconnect import handle_disconnect

def read_serial(serial_obj, buffer, parent_widget, connection_settings):
    if not (serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open):
        return
    try:
        if serial_obj.is_open:
            if serial_obj.in_waiting:
                buffer.extend(serial_obj.read(serial_obj.in_waiting))
                while len(buffer) >= 15:
                    if buffer[0] == 0x01 and buffer[14] == 0x02:
                        process_message(parent_widget, buffer[:15])
                        buffer = buffer[15:]
                    else:
                        buffer = buffer[1:]
    except (serial_utils.SerialException, OSError) as e:
        handle_disconnect(serial_obj, connection_settings, parent_widget, str(e))
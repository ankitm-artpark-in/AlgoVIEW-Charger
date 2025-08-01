import serial
from PySide6.QtWidgets import QMessageBox
from parsers.message_parser import process_message_15, process_message_21
from .handle_disconnect import handle_disconnect

def read_serial_15(serial_obj, buffer, parent_widget, connection_settings):
    if not (serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open):
        return
    try:
        if serial_obj.is_open and serial_obj.in_waiting:
            buffer.extend(serial_obj.read(serial_obj.in_waiting))
            while len(buffer) >= 15:
                if buffer[0] == 0x01 and buffer[14] == 0x02:
                    process_message_15(parent_widget, buffer[:15])
                    buffer = buffer[15:]
                else:
                    buffer = buffer[1:]
    except (serial.SerialException, OSError) as e:
        handle_disconnect(serial_obj, connection_settings, parent_widget, str(e))
        
def read_serial_21(serial_obj, buffer, parent_widget, connection_settings):
    if not (serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open):
        return
    try:
        if serial_obj.is_open and serial_obj.in_waiting:
            buffer.extend(serial_obj.read(serial_obj.in_waiting))
            while len(buffer) >= 21:
                if buffer[0] == 0x01 and buffer[20] == 0x02:
                    process_message_21(parent_widget, buffer[:21])
                    buffer = buffer[21:]
                else:
                    buffer = buffer[1:]
    except (serial.SerialException, OSError) as e:
        handle_disconnect(serial_obj, connection_settings, parent_widget, str(e))
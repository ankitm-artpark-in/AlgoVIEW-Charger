import serial
from PySide6.QtWidgets import QMessageBox
from message_parser import process_message

def read_serial(serial_obj, buffer, parent_widget):
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
    except (serial.SerialException, OSError) as e:
        QMessageBox.critical(parent_widget, "Error", f"Device disconnected unexpectedly: {e}")
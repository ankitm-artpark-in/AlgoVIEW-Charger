
import serial
from PyQt5.QtWidgets import QMessageBox
from .serial_global import serial_port

def read_serial(self):
    global serial_port
    if not serial_port:
        return
    try:
        if serial_port.is_open:
            if serial_port.in_waiting:
                self.buffer.extend(serial_port.read(serial_port.in_waiting))
                while len(self.buffer) >= 15:
                    if self.buffer[0] == 0x01 and self.buffer[14] == 0x02:
                        self.process_message(self.buffer[:15])
                        self.buffer = self.buffer[15:]
                    else:
                        self.buffer = self.buffer[1:]
    except (serial.SerialException, OSError) as e:
        self.handle_disconnect("Device disconnected unexpectedly")

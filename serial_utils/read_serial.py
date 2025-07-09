import serial
from PyQt5.QtWidgets import QMessageBox

def read_serial(self):
    if not self.serial_port:
        return
    try:
        if self.serial_port.is_open:
            if self.serial_port.in_waiting:
                self.buffer.extend(self.serial_port.read(self.serial_port.in_waiting))
                while len(self.buffer) >= 15:
                    if self.buffer[0] == 0x01 and self.buffer[14] == 0x02:
                        self.process_message(self.buffer[:15])
                        self.buffer = self.buffer[15:]
                    else:
                        self.buffer = self.buffer[1:]
    except (serial.SerialException, OSError) as e:
        self.handle_disconnect("Device disconnected unexpectedly")

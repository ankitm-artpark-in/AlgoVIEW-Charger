
from .serial_global import serial_port

def disconnect_serial(
    connect_button, disconnect_button, port_combo, refresh_button,
    parent=None
):
    global serial_port
    if serial_port:
        try:
            if serial_port.is_open:
                serial_port.close()
                print("Disconnected from serial port")
        except:
            pass
        serial_port = None
    connect_button.setEnabled(True)
    disconnect_button.setEnabled(False)
    port_combo.setEnabled(True)
    refresh_button.setEnabled(True)

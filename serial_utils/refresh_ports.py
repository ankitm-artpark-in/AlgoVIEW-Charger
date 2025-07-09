import serial.tools.list_ports

def refresh_ports(port_combo):
    port_combo.clear()
    ports = serial.tools.list_ports.comports()
    for port in ports:
        port_combo.addItem(port.device)

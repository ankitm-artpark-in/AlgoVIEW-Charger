import serial.tools.list_ports
from PySide6.QtWidgets import QMessageBox

def get_available_ports():
    return [port.device for port in serial.tools.list_ports.comports()]

def refresh_ports(dropdown, parent_widget):
    dropdown.clear()
    if ports := get_available_ports():
        dropdown.addItems(ports)

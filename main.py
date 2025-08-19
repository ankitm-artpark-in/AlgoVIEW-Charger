import sys
sys.dont_write_bytecode = True
import os

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont, QIcon
from widgets.serial_port_gui import SerialPortGUI

if __name__ == "__main__":
    app = QApplication(sys.argv)
    logo_path = os.path.join(os.path.dirname(__file__), 'assets', 'logo.png')
    app_icon = QIcon(logo_path)
    app.setWindowIcon(app_icon)
    
    default_font = QFont()
    default_font.setPointSize(11)
    window = SerialPortGUI()
    window.setFixedWidth(600)
    window.setFont(default_font)
    window.show()
    sys.exit(app.exec())

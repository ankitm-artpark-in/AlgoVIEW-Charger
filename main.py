
import sys
sys.dont_write_bytecode = True

from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QFont
from widgets.serial_port_gui import SerialPortGUI



if __name__ == "__main__":
    app = QApplication(sys.argv)
    default_font = QFont()
    default_font.setPointSize(11)
    window = SerialPortGUI()
    window.setFixedWidth(600)
    window.setFont(default_font)
    window.show()
    sys.exit(app.exec())

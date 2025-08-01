from PySide6.QtWidgets import (QWidget, QHBoxLayout)
from PySide6.QtGui import QFont

class CenterScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QHBoxLayout()
        
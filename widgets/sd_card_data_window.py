from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class SDCardDataWindow(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.addWidget(QLabel("SD Card Data"))
        self.setLayout(layout)

    def get_serial_obj(self):
        return self.main_window.serial_obj

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel

class TabTwoScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Tab 2 Screen"))
        self.setLayout(layout)

    def get_serial_obj(self):
        return self.main_window.serial_obj

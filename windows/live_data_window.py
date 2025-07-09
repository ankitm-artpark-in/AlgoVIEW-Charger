from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class live_data_window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Window One')
        layout = QVBoxLayout()
        label = QLabel('This is Window One')
        layout.addWidget(label)
        self.setLayout(layout)

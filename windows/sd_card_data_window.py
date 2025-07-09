from PyQt5.QtWidgets import QWidget, QLabel, QVBoxLayout

class sd_card_data_window(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Window Two')
        layout = QVBoxLayout()
        label = QLabel('This is Window Two')
        layout.addWidget(label)
        self.setLayout(layout)

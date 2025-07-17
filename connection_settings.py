from PySide6.QtWidgets import QGroupBox, QHBoxLayout, QComboBox, QPushButton, QLabel, QSizePolicy
from PySide6.QtGui import QFont
from PySide6.QtCore import Signal

class ConnectionSettings(QGroupBox):
    connect_clicked = Signal()
    disconnect_clicked = Signal()
    refresh_clicked = Signal()

    def __init__(self, parent=None):
        super().__init__('Connection Settings', parent)
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMaximumHeight(120)
        self.setMinimumHeight(120)

        layout = QHBoxLayout()
        layout.setSpacing(15)
        port_label = QLabel('Port:')
        port_label.setFont(default_font)
        self.port_combo = QComboBox()
        self.refresh_button = QPushButton('Refresh')
        self.refresh_button.setFont(default_font)
        self.connect_button = QPushButton('Connect')
        self.connect_button.setFont(default_font)
        self.disconnect_button = QPushButton('Disconnect')
        self.disconnect_button.setFont(default_font)
        self.disconnect_button.setEnabled(False)

        layout.addWidget(port_label)
        layout.addWidget(self.port_combo, 1)
        layout.addWidget(self.refresh_button)
        layout.addWidget(self.connect_button)
        layout.addWidget(self.disconnect_button)
        self.setLayout(layout)

        self.refresh_button.clicked.connect(self.refresh_clicked.emit)
        self.connect_button.clicked.connect(self.connect_clicked.emit)
        self.disconnect_button.clicked.connect(self.disconnect_clicked.emit)

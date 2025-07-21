from PySide6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QPushButton, QLabel, QMessageBox
from PySide6.QtCore import Qt

class PasswordDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Debug Access")
        self.setModal(True)
        
        # Set fixed size
        self.setFixedSize(300, 150)
        
        layout = QVBoxLayout()
        
        # Add description label
        description = QLabel("Enter password to view debug messages:")
        layout.addWidget(description)
        
        # Add password field
        self.password_field = QLineEdit()
        self.password_field.setEchoMode(QLineEdit.Password)
        layout.addWidget(self.password_field)
        
        # Add unlock button
        unlock_button = QPushButton("Unlock")
        unlock_button.clicked.connect(self.check_password)
        layout.addWidget(unlock_button)
        
        self.setLayout(layout)
        
        # Set the correct password (you should change this to something more secure)
        self.correct_password = "algofet"
        
    def check_password(self):
        if self.password_field.text() == self.correct_password:
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "Incorrect password")
            self.password_field.clear()

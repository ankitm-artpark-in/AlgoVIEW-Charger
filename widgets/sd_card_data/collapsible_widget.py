from PySide6.QtWidgets import QWidget, QVBoxLayout, QPushButton, QMessageBox


class CollapsibleSection(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.title = title
        self.is_collapsed = False
        
        # Main layout
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setLayout(self.main_layout)
        
        # Header
        self.header = QPushButton()
        self.header.setText(f"▼ {self.title}")
        self.header.setFlat(True)

        self.header.clicked.connect(self.toggle_collapsed)
        self.main_layout.addWidget(self.header)
        
        # Content area
        self.content_area = QWidget()
        self.content_layout = QVBoxLayout()
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_area.setLayout(self.content_layout)
        self.main_layout.addWidget(self.content_area)
        
    def toggle_collapsed(self):
        self.is_collapsed = not self.is_collapsed
        
        if self.is_collapsed:
            self.header.setText(f"▶ {self.title}")
            self.content_area.hide()
        else:
            self.header.setText(f"▼ {self.title}")
            self.content_area.show()
    
    def add_widget(self, widget):
        self.content_layout.addWidget(widget)
    
    def set_collapsed(self, collapsed):
        if self.is_collapsed != collapsed:
            self.toggle_collapsed()
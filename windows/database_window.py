from PyQt5.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem

class DatabaseWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Database Table')
        layout = QVBoxLayout()
        table = QTableWidget(10, 5)  # 10 rows, 5 columns as an example
        table.setHorizontalHeaderLabels([f'Column {i+1}' for i in range(5)])
        for row in range(10):
            for col in range(5):
                table.setItem(row, col, QTableWidgetItem(f'Item {row+1},{col+1}'))
        layout.addWidget(table)
        self.setLayout(layout)

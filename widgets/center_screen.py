from PySide6.QtWidgets import (QWidget, QHBoxLayout, QTableWidgetItem, QTableWidget, QVBoxLayout, QLabel, QPushButton, QHeaderView)
from PySide6.QtGui import QFont

from serial_utils.send_frame import send_battery_query

class CenterScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        # Title label
        title_label = QLabel("Battery IDs and Cycle Counts")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        main_layout.addWidget(title_label)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Battery ID", "Cycle Count", "Send Query"])
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        # Stretch columns to fit window width
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        header.setSectionResizeMode(1, QHeaderView.Stretch)
        header.setSectionResizeMode(2, QHeaderView.Stretch)
        main_layout.addWidget(self.table)

        self.setLayout(main_layout)
        self.refresh_table()

    def refresh_table(self):
        from PySide6.QtWidgets import QComboBox, QPushButton
        from serial_utils.send_frame import send_battery_query
        battery_ids = getattr(self.main_window, 'battery_ids', [])
        cycle_counts = getattr(self.main_window, 'cycle_counts', {})
        self.table.setRowCount(len(battery_ids))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Battery ID", "Cycle Count", "Send Query"])
        for row, bat_id in enumerate(battery_ids):
            self.table.setItem(row, 0, QTableWidgetItem(str(bat_id)))
            # Cycle count dropdown for this battery id
            cc_combo = QComboBox()
            cc = cycle_counts.get(bat_id)
            if cc is not None and isinstance(cc, int) and cc > 0:
                for i in range(1, cc + 1):
                    cc_combo.addItem(str(i))
            else:
                cc_combo.addItem("1")
            self.table.setCellWidget(row, 1, cc_combo)
            # Send Query button for this row
            send_btn = QPushButton("Send Query")
            def make_send_handler(bid, combo):
                return lambda: send_battery_query(
                    getattr(self.main_window, 'serial_obj', None),
                    self,
                    bid,
                    combo.currentText() if combo.currentText().isdigit() else 0
                )
            send_btn.clicked.connect(make_send_handler(bat_id, cc_combo))
            self.table.setCellWidget(row, 2, send_btn)

    # Removed update_cycle_count_combo, as dropdowns are now per-row

    # Removed handle_send_battery_query, as send query is now per-row

    # (Removed duplicate refresh_table)
        
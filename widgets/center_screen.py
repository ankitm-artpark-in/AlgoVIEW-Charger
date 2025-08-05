from PySide6.QtWidgets import (QWidget, QHBoxLayout, QTableWidgetItem, QTableWidget, QVBoxLayout, QLabel, QPushButton, QHeaderView, QComboBox, QPushButton)
from PySide6.QtGui import QFont

from serial_utils.read_serial import read_serial_15, read_serial_21
from serial_utils.send_frame import send_battery_query
from .connection_settings import ConnectionSettings

class CenterScreen(QWidget):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
        self.default_font = QFont()
        self.default_font.setPointSize(11)
        self.setFont(self.default_font)
        
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout()
        # Title label
        title_label = QLabel("Saved Logs")
        title_label.setFont(self.default_font)
        main_layout.addWidget(title_label)

        # Table setup
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Battery ID", "Cycle Count", "Download Data"])
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
        battery_ids = getattr(self.main_window, 'battery_ids', [])
        cycle_counts = getattr(self.main_window, 'cycle_counts', {})
        
        self.table.setRowCount(len(battery_ids))
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Battery ID", "Cycle Count", "Download Data"])
        
        for row, bat_id in enumerate(battery_ids):
            self.table.setItem(row, 0, QTableWidgetItem(str(bat_id)))
            
            # Cycle count dropdown for this battery id
            cycle_count_combo = QComboBox()
            cyclecount = cycle_counts.get(bat_id)
            if cyclecount is not None and isinstance(cyclecount, int) and cyclecount > 0:
                for i in range(1, cyclecount + 1):
                    cycle_count_combo.addItem(str(i))
            else:
                cycle_count_combo.addItem("1")
            self.table.setCellWidget(row, 1, cycle_count_combo)
            
            # Send Query button for this row
            send_btn = QPushButton("Download Data")
            
            def make_send_handler(bid, combo):
                def handler():
                    send_battery_query(
                        getattr(self.main_window, 'serial_obj', None),
                        self,
                        bid,
                        combo.currentText() if combo.currentText().isdigit() else 0
                    )
                    
                    read_serial_15(
                        getattr(self.main_window, 'serial_obj', None),
                        self.main_window.buffer,
                        self.main_window,
                        self.main_window.connection_settings,
                    )
                return handler

            send_btn.clicked.connect(make_send_handler(bat_id, cycle_count_combo))
            
            self.table.setCellWidget(row, 2, send_btn)        
import sys
sys.dont_write_bytecode = True

from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QTabWidget, QGroupBox, QGridLayout, QLabel, QTableWidget, QHeaderView, QComboBox, QPushButton, QTableWidgetItem
)

from PySide6.QtGui import QFont
from PySide6.QtCore import QTimer

# local file imports
from serial_utils import refresh_ports, connect_serial, disconnect_serial, handle_disconnect, read_serial
from widgets import ConnectionSettings, CenterScreen

class SerialPortGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AlgoX-VIEW")
        self.serial_obj = None
        self.buffer = bytearray()
        self.layout = QVBoxLayout()

        # Buffer for saved data frames
        self.saved_data_buffers = {}  # key: buffer_name, value: list of dicts

        # Table for displaying saved data info (moved to bottom, with timestamp and status)
        from PySide6.QtWidgets import QTableWidget
        self.saved_data_table = QTableWidget()
        self.saved_data_table.setColumnCount(4)
        self.saved_data_table.setHorizontalHeaderLabels(["Battery ID", "Cycle Count", "Timestamp", "Status"])
        self.saved_data_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.saved_data_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.saved_data_table.setSelectionMode(QTableWidget.SingleSelection)
        self.saved_data_table.setFixedHeight(180)
        # Stretch columns to fill width
        header = self.saved_data_table.horizontalHeader()
        for i in range(self.saved_data_table.columnCount()):
            header.setSectionResizeMode(i, QHeaderView.Stretch)
        self.saved_data_table.cellClicked.connect(self.handle_saved_data_table_click)

        default_font = QFont()
        default_font.setPointSize(11)
        self.setFont(default_font)

        # Charger Info Section
        self.charger_info_box = QGroupBox("Charger Info")
        self.charger_info_layout = QGridLayout()
        self.charger_hw_label = QLabel("-")
        self.charger_product_id_label = QLabel("-")
        self.charger_serial_label = QLabel("-")
        self.charger_fw_label = QLabel("-")
        # 2x2 grid: (0,0) HW, (0,1) Product, (1,0) Serial, (1,1) FW
        
        self.charger_info_layout.addWidget(QLabel("HW Version:"), 0, 0)
        self.charger_info_layout.addWidget(self.charger_hw_label, 0, 1)
        self.charger_info_layout.addWidget(QLabel("Product ID:"), 0, 2)
        self.charger_info_layout.addWidget(self.charger_product_id_label, 0, 3)
        self.charger_info_layout.addWidget(QLabel("Serial No:"), 1, 0)
        self.charger_info_layout.addWidget(self.charger_serial_label, 1, 1)
        self.charger_info_layout.addWidget(QLabel("FW Version:"), 1, 2)
        self.charger_info_layout.addWidget(self.charger_fw_label, 1, 3)
        self.charger_info_box.setLayout(self.charger_info_layout)
        self.layout.addWidget(self.charger_info_box)
        self.connection_settings = ConnectionSettings(self)
        self.layout.addWidget(self.connection_settings)
        self.center_screen_widget = CenterScreen(self)
        self.layout.addWidget(self.center_screen_widget)
        # Add saved data table at the bottom
        # Add import data button above the saved data table
        from PySide6.QtWidgets import QPushButton
        self.import_btn = QPushButton("Import Data")
        self.import_btn.clicked.connect(self.import_data_dialog)
        self.layout.addWidget(self.import_btn)
        
        
        self.layout.addWidget(self.saved_data_table)
        # Set the layout
        self.setLayout(self.layout)

        # Connect signals to buttons
        self.connection_settings.refresh_clicked.connect(self.refresh_ports)
        self.connection_settings.connect_clicked.connect(self.connect_port)
        self.connection_settings.disconnect_clicked.connect(self.disconnect_port)
        
    def import_data_dialog(self):
        from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QTableWidgetItem
        import pandas as pd
        from datetime import datetime
        # Ask for file
        file_path, _ = QFileDialog.getOpenFileName(self, "Import Data File", "", "Data Files (*.csv *.xlsx)")
        if not file_path:
            return
        # Read file
        try:
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to read file: {e}")
            return
        # Check columns
        expected_cols = ["timestamp", "charge_voltage", "charge_current", "rel_time", "error_flags"]
        if len(df.columns) != 5 or list(df.columns) != expected_cols:
            QMessageBox.warning(self, "Invalid File", "Invalid file selected. File must have exactly 5 columns: timestamp, charge_voltage, charge_current, rel_time, error_flags.")
            return
        # Ask for battery id
        bat_id, ok = QInputDialog.getText(self, "Battery ID", "Enter Battery ID for imported data:")
        if not ok or not bat_id:
            return
        # Use cycle count as '--' for import
        buffer_name = f"b_{bat_id}_c_--"
        # Convert DataFrame to list of dicts
        data_frames = df.to_dict(orient='records')
        # Save in buffer
        self.saved_data_buffers[buffer_name] = data_frames
        # Add to table (cycle count as '--', status as 'IMPORTED')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        found = False
        for row in range(self.saved_data_table.rowCount()):
            if (self.saved_data_table.item(row, 0) and self.saved_data_table.item(row, 0).text() == str(bat_id)
                and self.saved_data_table.item(row, 1) and self.saved_data_table.item(row, 1).text() == "--"):
                # Update timestamp and status if already present
                self.saved_data_table.setItem(row, 2, QTableWidgetItem(timestamp))
                self.saved_data_table.setItem(row, 3, QTableWidgetItem("IMPORTED"))
                found = True
                break
        if not found:
            row = self.saved_data_table.rowCount()
            self.saved_data_table.insertRow(row)
            self.saved_data_table.setItem(row, 0, QTableWidgetItem(str(bat_id)))
            self.saved_data_table.setItem(row, 1, QTableWidgetItem("--"))
            self.saved_data_table.setItem(row, 2, QTableWidgetItem(timestamp))
            self.saved_data_table.setItem(row, 3, QTableWidgetItem("IMPORTED"))
        self.show_data_view_dialog(buffer_name, data_frames)

    def update_charger_info(self, hw_version, product_id, serial_no, fw_major, fw_minor):
        self.charger_hw_label.setText(str(hw_version))
        self.charger_product_id_label.setText(str(product_id))
        self.charger_serial_label.setText(str(serial_no))
        self.charger_fw_label.setText(f"{fw_major}.{fw_minor}")

    def refresh_ports(self):
        refresh_ports(self.connection_settings.port_combo, self)

    def connect_port(self):
        self.buffer.clear()
        self.serial_obj = connect_serial(self.connection_settings.port_combo, self.connection_settings, self)
        # if self.serial_obj and self.serial_obj.is_open:
            # self.timer.start()

    def disconnect_port(self):
        # self.timer.stop()
        self.serial_obj = disconnect_serial(self.serial_obj, self.connection_settings, self)

    def read_serial_data(self):
        read_serial(self.serial_obj, self.buffer, self, self.connection_settings)

    def save_data_buffer(self, buffer_name, data_frames):
        """Save data in the GUI for later viewing and update the saved data table."""
        import re
        from PySide6.QtWidgets import QTableWidgetItem
        from datetime import datetime
        self.saved_data_buffers[buffer_name] = data_frames
        # Parse battery id and cycle count from buffer_name
        m = re.match(r"b_(.+)_c_(.+)", buffer_name)
        if m:
            bat_id, cycle_count = m.group(1), m.group(2)
        else:
            bat_id, cycle_count = buffer_name, "-"
        # Timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # Check if already present
        found = False
        for row in range(self.saved_data_table.rowCount()):
            if (self.saved_data_table.item(row, 0) and self.saved_data_table.item(row, 0).text() == str(bat_id)
                and self.saved_data_table.item(row, 1) and self.saved_data_table.item(row, 1).text() == str(cycle_count)):
                # Update timestamp and status if already present
                self.saved_data_table.setItem(row, 2, QTableWidgetItem(timestamp))
                self.saved_data_table.setItem(row, 3, QTableWidgetItem("DOWNLOADED"))
                found = True
                break
        if not found:
            row = self.saved_data_table.rowCount()
            self.saved_data_table.insertRow(row)
            self.saved_data_table.setItem(row, 0, QTableWidgetItem(str(bat_id)))
            self.saved_data_table.setItem(row, 1, QTableWidgetItem(str(cycle_count)))
            self.saved_data_table.setItem(row, 2, QTableWidgetItem(timestamp))
            self.saved_data_table.setItem(row, 3, QTableWidgetItem("DOWNLOADED"))
        # Table is always shown now
    def handle_saved_data_table_click(self, row, column):
        """Show the data view dialog for the selected saved data."""
        bat_id_item = self.saved_data_table.item(row, 0)
        cycle_count_item = self.saved_data_table.item(row, 1)
        if not bat_id_item or not cycle_count_item:
            return
        buffer_name = f"b_{bat_id_item.text()}_c_{cycle_count_item.text()}"
        if buffer_name in self.saved_data_buffers:
            self.show_data_view_dialog(buffer_name, self.saved_data_buffers[buffer_name])
        else:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Not Found", f"No data found for {buffer_name}")

    def show_data_view_dialog(self, buffer_name, data_frames):
        from widgets.data_view_dialog import DataViewDialog
        dlg = DataViewDialog(self, buffer_name, data_frames)
        dlg.exec()

    # Removed show_saved_data_dialog and its usages

if __name__ == "__main__":
    app = QApplication(sys.argv)
    default_font = QFont()
    default_font.setPointSize(11)
    
    window = SerialPortGUI()
    window.setFixedWidth(600)
    window.setFont(default_font)
    window.show()
    sys.exit(app.exec())

from PySide6.QtWidgets import QFileDialog, QInputDialog, QMessageBox, QTableWidgetItem
import pandas as pd
from datetime import datetime
import re

def import_data_dialog(self):
    file_path, _ = QFileDialog.getOpenFileName(self, "Import Data File", "", "Data Files (*.csv *.xlsx)")
    if not file_path:
        return
    try:
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
        else:
            df = pd.read_excel(file_path)
    except Exception as e:
        QMessageBox.warning(self, "Error", f"Failed to read file: {e}")
        return
    # Required columns for plotting and display
    required_cols = [
        'rel_time', 'charge_voltage', 'charge_current', 'error_flags',
        'set_c_rate1', 'set_c_rate2', 'max_volta_temp', 'avg_volta_temp'
    ]
    # Add missing columns as '--'
    for col in required_cols:
        if col not in df.columns:
            df[col] = '--'
    # Reorder columns for consistency
    df = df[required_cols]
    bat_id, ok = QInputDialog.getText(self, "Battery ID", "Enter Battery ID for imported data:")
    if not ok or not bat_id:
        return
    buffer_name = f"b_{bat_id}_c_--"
    data_frames = df.to_dict(orient='records')
    self.saved_data_buffers[buffer_name] = data_frames
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    found = False
    for row in range(self.saved_data_table.rowCount()):
        if (self.saved_data_table.item(row, 0) and self.saved_data_table.item(row, 0).text() == str(bat_id)
            and self.saved_data_table.item(row, 1) and self.saved_data_table.item(row, 1).text() == "--"):
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

def save_data_buffer(self, buffer_name, data_frames):
    self.saved_data_buffers[buffer_name] = data_frames
    m = re.match(r"b_(.+)_c_(.+)", buffer_name)
    if m:
        bat_id, cycle_count = m.group(1), m.group(2)
    else:
        bat_id, cycle_count = buffer_name, "-"
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    found = False
    for row in range(self.saved_data_table.rowCount()):
        if (self.saved_data_table.item(row, 0) and self.saved_data_table.item(row, 0).text() == str(bat_id)
            and self.saved_data_table.item(row, 1) and self.saved_data_table.item(row, 1).text() == str(cycle_count)):
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

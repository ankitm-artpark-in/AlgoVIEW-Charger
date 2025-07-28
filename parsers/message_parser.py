from datetime import datetime
from PySide6.QtWidgets import QMessageBox

DEVICE_6S_BMS = 0x01

MESSAGE_IDS = {
    (0x01, 0xA1): "CHARGER_VIT",
    (0x03, 0xC1): "CHARGER_INT_TEMP_DATA",
    (0x01, 0xB0): "CHARGER_Brick_A",
    (0x02, 0xB0): "CHARGER_Brick_B",
    (0x07, 0xE0): "CHARGER_INFO",
    (0xB1, 0xDE): "DEBUG_MESSAGE_1",
    (0xB2, 0xDE): "DEBUG_MESSAGE_2",
    # (0x10, 0x5D): "RECENT_DATA",
    (0x03, 0xE0): "RECENT_DATA",
    # (0x06, 0x5D): "CYCLE_COUNT_DATA",
    (0x04, 0xE0): "CYCLE_COUNT_DATA",
    (0x01, 0x5D): "DATA_FRAME_1",
    (0x02, 0x5D): "DATA_FRAME_2",
}

def process_message(self, message):
    hex_data = ' '.join([f'{b:02X}' for b in message])
    msg_id = (message[2], message[3])
    msg_type = MESSAGE_IDS.get(msg_id, "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    # print(f"Received message: {hex_data} | Type: {msg_type} | Timestamp: {timestamp}")

    message_handlers = {
        "CHARGER_VIT": handle_charger_vit,
        "CHARGER_INT_TEMP_DATA": handle_charger_int_temp_data,
        "CHARGER_Brick_A": handle_charger_brick_a,
        "CHARGER_Brick_B": handle_charger_brick_b,
        "CHARGER_INFO": handle_charger_info,
        "DEBUG_MESSAGE_1": handle_debug_message_1,
        "DEBUG_MESSAGE_2": handle_debug_message_2,
        "RECENT_DATA": handle_recent_data,
        "CYCLE_COUNT_DATA": handle_cycle_count_data,
        "DATA_FRAME_1": handle_data_frame_1,
        "DATA_FRAME_2": handle_data_frame_2,
    }

    handler = message_handlers.get(msg_type)
    if handler:
        handler(self, message, timestamp)

def handle_charger_vit(self, message, timestamp):
    voltage = (message[5] << 8 | message[4])
    current = (message[7] << 8 | message[6])
    temp = (message[9] << 8 | message[8])
    ac_value = (message[11] << 8 | message[10])
    
    # Update live data window
    # self.live_data.update_parameter_value("CHARGER_VIT", "Voltage", f"{voltage}")
    # self.live_data.update_parameter_value("CHARGER_VIT", "Current", f"{current}")
    # self.live_data.update_parameter_value("CHARGER_VIT", "Temperature", f"{temp}")
    # self.live_data.update_parameter_value("CHARGER_VIT", "AC Value", str(ac_value))

def handle_charger_int_temp_data(self, message, timestamp):
    volta_max = (message[5] << 8 | message[4])
    volta_avg = (message[7] << 8 | message[6])
    ambient_temp = (message[9] << 8 | message[8])
    
    # Update live data window
    # self.live_data.update_parameter_value("CHARGER_INT_TEMP_DATA", "Voltage Max", f"{volta_max}")
    # self.live_data.update_parameter_value("CHARGER_INT_TEMP_DATA", "Voltage Average", f"{volta_avg}")
    # self.live_data.update_parameter_value("CHARGER_INT_TEMP_DATA", "Ambient Temperature", f"{ambient_temp}")

def handle_charger_brick_a(self, message, timestamp):
    cell_1 = (message[5] << 8 | message[4])
    cell_2 = (message[7] << 8 | message[6])
    cell_3 = (message[9] << 8 | message[8])
    cell_4 = (message[11] << 8 | message[10])
    
    # Update live data window
    # self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 1", f"{cell_1}")
    # self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 2", f"{cell_2}")
    # self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 3", f"{cell_3}")
    # self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 4", f"{cell_4}")

def handle_charger_brick_b(self, message, timestamp):
    cell_5 = (message[5] << 8 | message[4])
    cell_6 = (message[7] << 8 | message[6])
    cell_7 = (message[9] << 8 | message[8])
    cell_8 = (message[11] << 8 | message[10])
    
    # Update live data window
    # self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 5", f"{cell_5}")
    # self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 6", f"{cell_6}")
    # self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 7", f"{cell_7}")
    # self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 8", f"{cell_8}")

def handle_charger_info(self, message, timestamp):
    hw_version = message[4]
    product_id = message[5]
    serial_no = '.'.join([f'{b:02X}' for b in message[6:10]])
    fw_major = message[10]
    fw_minor = message[11]
    
    # Update live data window
    # self.live_data.update_parameter_value("CHARGER_INFO", "Hardware Version", str(hw_version))
    # self.live_data.update_parameter_value("CHARGER_INFO", "Product ID", str(product_id))
    # self.live_data.update_parameter_value("CHARGER_INFO", "Serial Number", serial_no)
    # self.live_data.update_parameter_value("CHARGER_INFO", "Firmware Version", f"{fw_major}.{fw_minor}")
    
    self.sd_card_data.charger_info_labels["CHARGER_INFO_Hardware Version"].setText(str(hw_version))
    self.sd_card_data.charger_info_labels["CHARGER_INFO_Product ID"].setText(str(product_id))
    self.sd_card_data.charger_info_labels["CHARGER_INFO_Serial Number"].setText(serial_no)
    self.sd_card_data.charger_info_labels["CHARGER_INFO_Firmware Version"].setText(f"{fw_major}.{fw_minor}")
    
    
def handle_debug_message_1(self, message, timestamp):
    cell_count = message[4]
    charger_on_status = message[5]
    current_count = (message[7] << 8 | message[6])
    voltage_count = (message[9] << 8 | message[8])
    cell_balance_status = (message[11] << 8 | message[10])
    
    # Update live data window
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Cell Count", str(cell_count))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Charger On Status", str(charger_on_status))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Current Count", str(current_count))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Voltage Count", str(voltage_count))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Cell Balance Status", str(cell_balance_status))
    
def handle_debug_message_2(self, message, timestamp):
    charger_safety_off = message[4]
    bat_vtg_read_value = (message[6] << 8 | message[5])
    charger_state = message[7]
    charger_op_on = message[8]
    volta_heart_beat = message[9]
    charger_error_flag = message[10]
    
    # Update live data window
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger Safety Off", str(charger_safety_off))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Battery Voltage Read Value", f"{bat_vtg_read_value}V")
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger State", str(charger_state))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger Op On", str(charger_op_on))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Volta Heart Beat", str(volta_heart_beat))
    # self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger Error Flag", str(charger_error_flag))
    
def handle_recent_data(self, message, timestamp):
    battery_id = (message[5] << 8 | message[4])
    if not hasattr(self, 'battery_ids'):
        self.battery_ids = []
    if battery_id not in self.battery_ids:
        self.battery_ids.append(battery_id)
        self.sd_card_data.update_files_tree()
    
def handle_cycle_count_data(self, message, timestamp):
    battery_id = (message[5] << 8 | message[4])
    cycle_count = (message[7] << 8 | message[6]) + 2
    if not hasattr(self, 'cycle_counts'):
        self.cycle_counts = {}
    self.cycle_counts[battery_id] = cycle_count
    self.sd_card_data.update_files_tree()
    
def handle_data_frame_1(self, message, timestamp):
    charge_voltage = (message[5] << 8 | message[4])
    charge_current = (message[7] << 8 | message[6])
    rel_time = (message[9] << 8 | message[8])
    error_flags = (message[11] << 8 | message[10])
    
def handle_data_frame_2(self, message, timestamp):
    set_c_rate1 = (message[5] << 8 | message[4])
    set_c_rate2 = (message[7] << 8 | message[6])
    max_volta_temp = (message[9] << 8 | message[8])
    avg_volta_temp = (message[11] << 8 | message[10])
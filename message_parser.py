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
}

def process_message(self, message):
    hex_data = ' '.join([f'{b:02X}' for b in message])
    msg_id = (message[2], message[3])
    msg_type = MESSAGE_IDS.get(msg_id, "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"Received message: {hex_data} | Type: {msg_type} | Timestamp: {timestamp}")

    # Process different message types
    message_handlers = {
        "CHARGER_VIT": handle_charger_vit,
        "CHARGER_INT_TEMP_DATA": handle_charger_int_temp_data,
        "CHARGER_Brick_A": handle_charger_brick_a,
        "CHARGER_Brick_B": handle_charger_brick_b,
        "CHARGER_INFO": handle_charger_info,
        # "DEBUG_MESSAGE_1": handle_debug_message_1,
        # "DEBUG_MESSAGE_2": handle_debug_message_2,
    }

    handler = message_handlers.get(msg_type)
    if handler:
        handler(self, message, timestamp)

# Individual message handlers
def handle_charger_vit(self, message, timestamp):
    voltage = (message[5] << 8 | message[4])
    current = (message[7] << 8 | message[6])
    temp = (message[9] << 8 | message[8])
    ac_value = (message[11] << 8 | message[10])
    
    # Update live data window
    self.live_data.update_parameter_value("CHARGER_VIT", "Voltage", f"{voltage}V")
    self.live_data.update_parameter_value("CHARGER_VIT", "Current", f"{current}A")
    self.live_data.update_parameter_value("CHARGER_VIT", "Temperature", f"{temp}°C")
    self.live_data.update_parameter_value("CHARGER_VIT", "AC Value", str(ac_value))

def handle_charger_int_temp_data(self, message, timestamp):
    volta_max = (message[5] << 8 | message[4])
    volta_avg = (message[7] << 8 | message[6])
    ambient_temp = (message[9] << 8 | message[8])
    
    # Update live data window
    self.live_data.update_parameter_value("CHARGER_INT_TEMP_DATA", "Voltage Max", f"{volta_max}V")
    self.live_data.update_parameter_value("CHARGER_INT_TEMP_DATA", "Voltage Average", f"{volta_avg}V")
    self.live_data.update_parameter_value("CHARGER_INT_TEMP_DATA", "Ambient Temperature", f"{ambient_temp}°C")

def handle_charger_brick_a(self, message, timestamp):
    cell_1 = (message[5] << 8 | message[4])
    cell_2 = (message[7] << 8 | message[6])
    cell_3 = (message[9] << 8 | message[8])
    cell_4 = (message[11] << 8 | message[10])
    
    # Update live data window
    self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 1", f"{cell_1}V")
    self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 2", f"{cell_2}V")
    self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 3", f"{cell_3}V")
    self.live_data.update_parameter_value("CHARGER_Brick_A", "Cell 4", f"{cell_4}V")

def handle_charger_brick_b(self, message, timestamp):
    cell_5 = (message[5] << 8 | message[4])
    cell_6 = (message[7] << 8 | message[6])
    cell_7 = (message[9] << 8 | message[8])
    cell_8 = (message[11] << 8 | message[10])
    
    # Update live data window
    self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 5", f"{cell_5}V")
    self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 6", f"{cell_6}V")
    self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 7", f"{cell_7}V")
    self.live_data.update_parameter_value("CHARGER_Brick_B", "Cell 8", f"{cell_8}V")

def handle_charger_info(self, message, timestamp):
    hw_version = message[4]
    product_id = message[5]
    serial_no = '.'.join([f'{b:02X}' for b in message[6:10]])
    fw_major = message[10]
    fw_minor = message[11]
    
    # Update live data window
    self.live_data.update_parameter_value("CHARGER_INFO", "Hardware Version", str(hw_version))
    self.live_data.update_parameter_value("CHARGER_INFO", "Product ID", str(product_id))
    self.live_data.update_parameter_value("CHARGER_INFO", "Serial Number", serial_no)
    self.live_data.update_parameter_value("CHARGER_INFO", "Firmware Version", f"{fw_major}.{fw_minor}")

def handle_debug_message_1(self, message, timestamp):
    cell_count = message[4]
    charger_on_status = message[5]
    current_count = (message[7] << 8 | message[6])
    voltage_count = (message[9] << 8 | message[8])
    cell_balance_status = (message[11] << 8 | message[10])
    
    # Update live data window
    self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Cell Count", str(cell_count))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Charger On Status", str(charger_on_status))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Current Count", str(current_count))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Voltage Count", str(voltage_count))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_1", "Cell Balance Status", str(cell_balance_status))
    
def handle_debug_message_2(self, message, timestamp):
    charger_safety_off = message[4]
    bat_vtg_read_value = (message[6] << 8 | message[5])
    charger_state = message[7]
    charger_op_on = message[8]
    volta_heart_beat = message[9]
    charger_error_flag = message[10]
    
    # Update live data window
    self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger Safety Off", str(charger_safety_off))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Battery Voltage Read Value", f"{bat_vtg_read_value}V")
    self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger State", str(charger_state))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger Op On", str(charger_op_on))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Volta Heart Beat", str(volta_heart_beat))
    self.live_data.update_parameter_value("DEBUG_MESSAGE_2", "Charger Error Flag", str(charger_error_flag))
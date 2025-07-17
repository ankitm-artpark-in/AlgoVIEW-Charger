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

    # Process different message types
    message_handlers = {
        "CHARGER_VIT": handle_charger_vit,
        "CHARGER_INT_TEMP_DATA": handle_charger_int_temp_data,
        "CHARGER_Brick_A": handle_charger_brick_a,
        "CHARGER_Brick_B": handle_charger_brick_b,
        "CHARGER_INFO": handle_charger_info,
        "DEBUG_MESSAGE_1": handle_debug_message_1,
        "DEBUG_MESSAGE_2": handle_debug_message_2,
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
    print(f"Charger VIT - Voltage: {voltage}, Current: {current}, Temp: {temp}, AC Value: {ac_value} | Timestamp: {timestamp}")

def handle_charger_int_temp_data(self, message, timestamp):
    volta_max = (message[5] << 8 | message[4])
    volta_avg = (message[7] << 8 | message[6])
    ambient_temp = (message[9] << 8 | message[8])
    print(f"Charger Int Temp Data - Max: {volta_max}, Avg: {volta_avg}, Ambient: {ambient_temp} | Timestamp: {timestamp}")

def handle_charger_brick_a(self, message, timestamp):
    cell_1 = (message[5] << 8 | message[4])
    cell_2 = (message[7] << 8 | message[6])
    cell_3 = (message[9] << 8 | message[8])
    cell_4 = (message[11] << 8 | message[10])
    print(f"Charger Brick A - Cell 1: {cell_1}, Cell 2: {cell_2}, Cell 3: {cell_3}, Cell 4: {cell_4} | Timestamp: {timestamp}")

def handle_charger_brick_b(self, message, timestamp):
    cell_5 = (message[5] << 8 | message[4])
    cell_6 = (message[7] << 8 | message[6])
    cell_7 = (message[9] << 8 | message[8])
    cell_8 = (message[11] << 8 | message[10])
    print(f"Charger Brick B - Cell 5: {cell_5}, Cell 6: {cell_6}, Cell 7: {cell_7}, Cell 8: {cell_8} | Timestamp: {timestamp}")

def handle_charger_info(self, message, timestamp):
    hw_version = message[4]
    product_id = message[5]
    serial_no = message[6:10]
    fw_major = message[10]
    fw_minor = message[11]
    print(f"Charger Info - HW Version: {hw_version}, Product ID: {product_id}, Serial No: {serial_no}, FW Version: {fw_major}.{fw_minor} | Timestamp: {timestamp}")

def handle_debug_message_1(self, message, timestamp):
    cell_count = message[4]
    charger_on_status = message[5]
    current_count = (message[7] << 8 | message[6])
    voltage_count = (message[9] << 8 | message[8])
    cell_balance_status = (message[11] << 8 | message[10])
    print(f"Debug Message 1 - Cell Count: {cell_count}, Charger On Status: {charger_on_status}, Current Count: {current_count}, Voltage Count: {voltage_count}, Cell Balance Status: {cell_balance_status} | Timestamp: {timestamp}")
    
def handle_debug_message_2(self, message, timestamp):
    charger_safety_off = message[4]
    bat_vtg_read_value = (message[6] << 8 | message[5])
    charger_state = message[7]
    charger_op_on = message[8]
    volta_heart_beat = message[9]
    charger_error_flag = message[10]
    print(f"Debug Message 2 - Charger Safety Off: {charger_safety_off}, Bat Vtg Read Value: {bat_vtg_read_value}, Charger State: {charger_state}, Charger Op On: {charger_op_on}, Volta Heart Beat: {volta_heart_beat}, Charger Error Flag: {charger_error_flag} | Timestamp: {timestamp}")
from datetime import datetime
from PySide6.QtWidgets import QMessageBox

MESSAGE_IDS_15 = {
    (0x01, 0xA1): "CHARGER_VIT",
    (0x03, 0xC1): "CHARGER_INT_TEMP_DATA",
    (0x01, 0xB0): "CHARGER_Brick_A",
    (0x02, 0xB0): "CHARGER_Brick_B",
    (0x07, 0xE0): "CHARGER_INFO",
    (0xB1, 0xDE): "DEBUG_MESSAGE_1",
    (0xB2, 0xDE): "DEBUG_MESSAGE_2",
    
    (0x06, 0x5D): "DISPLAY_DATA",
    (0x01, 0x5D): "DATA_FRAME",
}

MESSAGE_IDS_21 = {
    (0x05, 0x5D): "DATA_FRAME",
}

def process_message_15(self, message, battery_ids=None, cycle_counts=None):
    hex_data = ' '.join([f'{b:02X}' for b in message])
    msg_id = (message[2], message[3])
    msg_type = MESSAGE_IDS_15.get(msg_id, "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"Received message: {hex_data} | Type: {msg_type} | Timestamp: {timestamp}")

    message_handlers = {
        "CHARGER_VIT": handle_charger_vit,
        "CHARGER_INT_TEMP_DATA": handle_charger_int_temp_data,
        "CHARGER_Brick_A": handle_charger_brick_a,
        "CHARGER_Brick_B": handle_charger_brick_b,
        "CHARGER_INFO": handle_charger_info,
        "DEBUG_MESSAGE_1": handle_debug_message_1,
        "DEBUG_MESSAGE_2": handle_debug_message_2,

        "DISPLAY_DATA": handle_display_data,
        # "DATA_FRAME": handle_data_frame,
    }

    if handler := message_handlers.get(msg_type):
        handler(self, message, timestamp)
        
    if msg_type == "DATA_FRAME":
        handle_data_frame(self, message, timestamp, battery_ids, cycle_counts)
        
def process_message_21(self, message):
    hex_data = ' '.join([f'{b:02X}' for b in message])
    msg_id = (message[2], message[3])
    msg_type = MESSAGE_IDS_21.get(msg_id, "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    print(f"Received message: {hex_data} | Type: {msg_type} | Timestamp: {timestamp}")
    
    message_handlers = {
        "DATA_FRAME" : handle_data_frame
    }
    
    if handler := message_handlers.get(msg_type):
        handler(self, message, timestamp)

def handle_charger_vit(self, message, timestamp):
    voltage = (message[5] << 8 | message[4])
    current = (message[7] << 8 | message[6])
    temp = (message[9] << 8 | message[8])
    ac_value = (message[11] << 8 | message[10])

def handle_charger_int_temp_data(self, message, timestamp):
    volta_max = (message[5] << 8 | message[4])
    volta_avg = (message[7] << 8 | message[6])
    ambient_temp = (message[9] << 8 | message[8])

def handle_charger_brick_a(self, message, timestamp):
    cell_1 = (message[5] << 8 | message[4])
    cell_2 = (message[7] << 8 | message[6])
    cell_3 = (message[9] << 8 | message[8])
    cell_4 = (message[11] << 8 | message[10])

def handle_charger_brick_b(self, message, timestamp):
    cell_5 = (message[5] << 8 | message[4])
    cell_6 = (message[7] << 8 | message[6])
    cell_7 = (message[9] << 8 | message[8])
    cell_8 = (message[11] << 8 | message[10])

def handle_charger_info(self, message, timestamp):
    hw_version = message[4]
    product_id = message[5]
    serial_no = '.'.join([f'{b:02X}' for b in message[6:10]])
    fw_major = message[10]
    fw_minor = message[11]

    # Update the charger info in the GUI if the method exists
    if hasattr(self, 'update_charger_info'):
        self.update_charger_info(hw_version, product_id, serial_no, fw_major, fw_minor)
    
def handle_debug_message_1(self, message, timestamp):
    cell_count = message[4]
    charger_on_status = message[5]
    current_count = (message[7] << 8 | message[6])
    voltage_count = (message[9] << 8 | message[8])
    cell_balance_status = (message[11] << 8 | message[10])
    
def handle_debug_message_2(self, message, timestamp):
    charger_safety_off = message[4]
    bat_vtg_read_value = (message[6] << 8 | message[5])
    charger_state = message[7]
    charger_op_on = message[8]
    volta_heart_beat = message[9]
    charger_error_flag = message[10]
    
def handle_display_data(self, message, timestamp):
    if (message[4] == 0x00 and message[5] == 0x00 and message[6] == 0x00 and message[7] == 0x00):
        battery_id = (message[10] << 8 | message[9])
        if not hasattr(self, "battery_ids"):
            self.battery_ids = []
        if battery_id not in self.battery_ids:
            self.battery_ids.append(battery_id)
        self.center_screen_widget.refresh_table()

    if (message[9] == 0x00 and message[10] == 0x00):
        bat_id = (message[5] << 8 | message[4])
        cycle_count = (message[7] << 8 | message[6])
        if not hasattr(self, 'cycle_counts'):
            self.cycle_counts = {}
        self.cycle_counts[bat_id] = cycle_count
        self.center_screen_widget.refresh_table()
    
def handle_data_frame(self, message, timestamp, battery_id, cycle_counts):
    charge_voltage = (message[5] << 8 | message[4])
    charge_current = (message[7] << 8 | message[6])
    rel_time = (message[9] << 8 | message[8])
    error_flags = (message[11] << 8 | message[10])
    # set_c_rate_1 = (message[13] << 8 | message[12])
    # set_c_rate_2 = (message[15] << 8 | message[14])
    # max_volta_temp = (message[17] << 8 | message[16])
    # avg_volta_temp = (message[19] << 8 | message[18])
    
    buffer_name = f'b_{battery_id}_c_{cycle_counts}'
    
    if not hasattr(self, 'data_frames_buffer'):
        self.data_frames_buffer = {}
        
    if buffer_name not in self.data_frames_buffer:
        self.data_frames_buffer[buffer_name] = []
        
    self.data_frames_buffer[buffer_name].append(
        {
            "timestamp": timestamp,
            "charge_voltage": charge_voltage,
            "charge_current": charge_current,
            "rel_time": rel_time,
            "error_flags": error_flags,
            # "set_c_rate_1": set_c_rate_1,
            # "set_c_rate_2": set_c_rate_2,
            # "max_volta_temp": max_volta_temp,
            # "avg_volta_temp": avg_volta_temp,
            
        }
    )
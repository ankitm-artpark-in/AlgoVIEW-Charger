from constants import MESSAGE_IDS
from datetime import datetime


def parse_message(message):
    msg_id = (message[2], message[3])
    msg_type = MESSAGE_IDS.get(msg_id, "Unknown")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")
    data = {}

    if msg_type == "Charger_VIT":
        data['Charger Voltage'] = (message[5] << 8 | message[4]) / 100.0
        data['Charger Current'] = (message[7] << 8 | message[6]) / 100.0
        data['Charger Temp'] = (message[9] << 8 | message[8]) / 100.0
        data['Charger AC Value'] = (message[11] << 8 | message[10]) / 100.0
    elif msg_type == "TEMP_DATA":
        data['Volta Max Temp'] = (message[5] << 8 | message[4]) / 100.0
        data['Volta Avg Temp'] = (message[7] << 8 | message[6]) / 100.0
        data['Ambient Temp'] = (message[9] << 8 | message[8]) / 100.0
    elif msg_type == "Brick_A":
        data['Cell 1'] = (message[5] << 8 | message[4]) / 1000.0
        data['Cell 2'] = (message[7] << 8 | message[6]) / 1000.0
        data['Cell 3'] = (message[9] << 8 | message[8]) / 1000.0
        data['Cell 4'] = (message[11] << 8 | message[10]) / 1000.0
    elif msg_type == "Brick_B":
        data['Cell 5'] = (message[5] << 8 | message[4]) / 1000.0
        data['Cell 6'] = (message[7] << 8 | message[6]) / 1000.0
        data['Cell 7'] = (message[9] << 8 | message[8]) / 1000.0
        data['Cell 8'] = (message[11] << 8 | message[10]) / 1000.0
    elif msg_type == "Debug_Message_1":
        data['Cell Count'] = message[4]
        data['Charger On Status'] = message[5]
        data['Current Count'] = (message[7] << 8 | message[6])
        data['Voltage Count'] = message[9] << 8 | message[8]
        data['Cell Balance Status'] = message[11] << 8 | message[10]
    elif msg_type == "Debug_Message_2":
        data['Charger Safety Off'] = message[4]
        data['Battery Vtg read value'] = (message[6] << 8 | message[5]) / 100.0
        data['Charger state'] = message[7]
        data['Charger O/P On'] = message[8]
        data['Volta Heartbeat'] = message[9]
        data['Charger Error Flag'] = message[10]
    elif msg_type == "System_Info":
        data['HW Version'] = message[4]
        data['Product ID'] = message[5]
        data['Serial Number'] = (message[6] << 24) | (message[7] << 16) | (message[8] << 8) | message[9]
        data['Firmware Version Major'] = message[10]
        data['Firmware Version Minor'] = message[11]
    else:
        data['raw'] = message

    return {
        "type": msg_type,
        "timestamp": timestamp,
        "data": data,
        "raw": message
    }

from PySide6.QtWidgets import QMessageBox
from .send_raw_msg import send_raw_msg

def send_frame(serial_obj, command, parent_widget):
    if serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open:
        try:
            if command == "Reception_ON":
                # msg = bytes([0x30, 0xAA, 0x00, 0xA1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                msg = bytes([0x01, 0xAA, 0x00, 0xA1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                
            elif command == "Reception_OFF":
                # msg = bytes([0x30, 0xAA, 0x00, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                msg = bytes([0x01, 0xAA, 0x00, 0xA0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                
            elif command == "Reception_ONCE":
                # msg = bytes([0x30, 0xAA, 0x00, 0xAE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                msg = bytes([0x01, 0xAA, 0x00, 0xAE, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                
            elif command == "Recent_Data":
                # msg = bytes([0x30, 0xAA, 0x00, 0xB0, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                msg = bytes([0x01, 0xAA, 0x00, 0xB1, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                
            elif command == "Cycle_Count_Data":
                # msg = bytes([0x30, 0xAA, 0x00, 0xB2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                msg = bytes([0x01, 0xAA, 0x00, 0xB2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00])
                
            else:
                return
            
            send_raw_msg(serial_obj, msg, parent_widget)
            QMessageBox.information(parent_widget, "Message Sent", "Command sent successfully.")
            
        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Error during sending command: {e}")
            
def send_battery_query(serial_obj, parent_widget, battery_id, cycle_count):
    if serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open:
        try:
            battery_id = int(battery_id)
            cycle_count = int(cycle_count)
            # msg = bytes([0x30, 0xAA, 0x00, 0xB3, 
            #             (battery_id >> 8) & 0xFF, battery_id & 0xFF,
            #             (cycle_count >> 8) & 0xFF, cycle_count & 0xFF,
            #             0x00, 0x00])
            
            msg = bytes([0x01, 0xAA, 0x00, 0xB3, 
                        (battery_id >> 8) & 0xFF, battery_id & 0xFF,
                        (cycle_count >> 8) & 0xFF, cycle_count & 0xFF,
                        0x00, 0x00])
            
            send_raw_msg(serial_obj, msg, parent_widget)
            # QMessageBox.information(parent_widget, "Message Sent", "Battery query sent successfully.")
            
        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Error during sending battery query: {e}")
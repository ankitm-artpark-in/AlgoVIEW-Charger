from PySide6.QtWidgets import QMessageBox, QDialog, QVBoxLayout, QLabel
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QPainter
from .send_raw_msg import send_raw_msg

class LoadingDialog(QDialog):
    def __init__(self, parent=None, message="Loading...", window_title="Loading", close_timer_ms=5000):
        super().__init__(parent)
        self.setWindowTitle(window_title)
        self.setFixedSize(150, 100)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        self.setModal(True)
        
        # Create layout
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)
        
        # Create spacer for the spinning circle area
        self.loading_area = QLabel()
        self.loading_area.setFixedSize(60, 60)
        self.loading_area.setAlignment(Qt.AlignCenter)
        
        # Create message label
        self.message_label = QLabel(message)
        self.message_label.setAlignment(Qt.AlignCenter)
        self.message_label.setStyleSheet("font-size: 12px; margin: 10px;")
        
        layout.addWidget(self.loading_area, 0, Qt.AlignCenter)
        layout.addWidget(self.message_label, 0, Qt.AlignCenter)
        self.setLayout(layout)
        
        # Timer for rotation animation
        self.rotation_angle = 0
        self.rotation_timer = QTimer()
        self.rotation_timer.timeout.connect(self.rotate_loading)
        self.rotation_timer.start(50)  # Update every 50ms for smooth animation
        
        # Timer to close dialog after specified time
        self.close_timer = QTimer()
        self.close_timer.timeout.connect(self.accept)
        self.close_timer.setSingleShot(True)
        self.close_timer.start(close_timer_ms)
    
    def rotate_loading(self):
        self.rotation_angle = (self.rotation_angle + 10) % 360
        self.update()
    
    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Calculate the center of the loading area
        loading_area_pos = self.loading_area.pos()
        center_x = loading_area_pos.x() + self.loading_area.width() // 2
        center_y = loading_area_pos.y() + self.loading_area.height() // 2
        
        # Save the painter state
        painter.save()
        
        # Move to center and rotate
        painter.translate(center_x, center_y)
        painter.rotate(self.rotation_angle)
        
        # Draw the spinning circle (like a loading spinner)
        from PySide6.QtGui import QPen
        pen = QPen(Qt.blue)
        pen.setWidth(3)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)
        
        # Draw an arc that spins
        painter.drawArc(-20, -20, 40, 40, 0, 270 * 16)  # 270 degree arc
        
        # Restore painter state
        painter.restore()
        
    def closeEvent(self, event):
        self.rotation_timer.stop()
        self.close_timer.stop()
        super().closeEvent(event)

def show_loading_dialog(parent_widget, message="Command sent successfully", window_title="Loading", close_timer_ms=5000):
    dialog = LoadingDialog(parent_widget, message, window_title, close_timer_ms)
    dialog.exec()

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
            print(f"Sent command: {command} and msg: {' '.join(f'{b:02X}' for b in msg)}")
            
            # Show loading dialog instead of QMessageBox
            show_loading_dialog(parent_widget, "Please Wait", "Getting File Structure", 3000)
            
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
            print(f"Sent battery query: {' '.join(f'{b:02X}' for b in msg)}")
            
            # Show loading dialog instead of QMessageBox
            show_loading_dialog(parent_widget, "Please Wait", "Download file", 15000)
            
        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Error during sending battery query: {e}")
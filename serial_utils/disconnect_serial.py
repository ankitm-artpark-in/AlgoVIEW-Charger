from PySide6.QtWidgets import QMessageBox
from .send_frame import send_frame

def disconnect_serial(serial_obj, connection_settings, parent_widget):
    if serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open:
        try:
            send_frame(serial_obj, "Reception_OFF", parent_widget)
            serial_obj.close()
            QMessageBox.information(parent_widget, "Disconnected", "Disconnected successfully.")
            
            # Enable connect, disable disconnect
            connection_settings.disconnect_button.setEnabled(False)
            connection_settings.connect_button.setEnabled(True)
        except Exception as e:
            QMessageBox.critical(parent_widget, "Error", f"Error during disconnect: {e}")
    else:
        QMessageBox.warning(parent_widget, "Not Connected", "No active connection to disconnect.")
        
        # Enable connect, disable disconnect
        connection_settings.disconnect_button.setEnabled(False)
        connection_settings.connect_button.setEnabled(True)

    return None

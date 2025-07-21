from PySide6.QtWidgets import QMessageBox

def handle_disconnect(serial_obj, connection_settings, parent_widget, message):
    if serial_obj and hasattr(serial_obj, 'is_open') and serial_obj.is_open:
        try:
            serial_obj.close()
        except:
            pass
    serial_obj = None
    # Use connection_settings for button and combo state
    connection_settings.connect_button.setEnabled(True)
    connection_settings.disconnect_button.setEnabled(False)
    connection_settings.port_combo.setEnabled(True)
    
    QMessageBox.warning(parent_widget, "Connection Error", message)

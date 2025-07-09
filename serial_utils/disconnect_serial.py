def disconnect_serial(
    connect_button, disconnect_button, port_combo, refresh_button,
    parent=None
):
    if hasattr(parent, 'serial_port') and parent.serial_port:
        try:
            if parent.serial_port.is_open:
                parent.serial_port.close()
        except:
            pass
    connect_button.setEnabled(True)
    disconnect_button.setEnabled(False)
    port_combo.setEnabled(True)
    refresh_button.setEnabled(True)

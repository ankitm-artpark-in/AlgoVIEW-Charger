from PyQt5.QtWidgets import QMenu, QToolButton, QAction
from PyQt5.QtGui import QIcon

def create_more_menu(parent):
    more_button = QToolButton()
    more_button.setIcon(QIcon.fromTheme('dots-horizontal') or QIcon('...'))
    more_button.setPopupMode(QToolButton.InstantPopup)
    more_menu = QMenu()
    admin_action = QAction('Admin Access', parent)
    more_menu.addAction(admin_action)
    more_button.setMenu(more_menu)
    return more_button, admin_action

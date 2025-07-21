import sys
from PySide6.QtWidgets import QStyledItemDelegate
from PySide6.QtGui import QFont, QColor, QPainter
from PySide6.QtCore import Qt, QRect

class ColorBoxDelegate(QStyledItemDelegate):
    """Custom delegate to draw a colored box next to each color name in a QComboBox."""
    def paint(self, painter, option, index):
        color_hex = index.data(Qt.UserRole)
        rect = option.rect
        # Draw the colored box
        if color_hex:
            color = QColor(color_hex)
            box_rect = QRect(rect.left() + 4, rect.top() + (rect.height() - 16) // 2, 16, 16)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(color)
            painter.setPen(Qt.black)
            painter.drawRect(box_rect)
            painter.restore()
            # Draw the text next to the box
            text_rect = QRect(box_rect.right() + 8, rect.top(), rect.width() - 28, rect.height())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, index.data(Qt.DisplayRole))
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 22))
        return size
    
    def displayText(self, value, locale):
        return str(value)
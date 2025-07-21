import sys
from PySide6.QtWidgets import QStyledItemDelegate, QComboBox, QStyleOptionViewItem, QStyle, QStyleOptionComboBox
from PySide6.QtGui import QFont, QColor, QPainter
from PySide6.QtCore import Qt, QRect

class ColorBoxDelegate(QStyledItemDelegate):
    """Delegate to draw a color box next to color names in QComboBox."""
    def paint(self, painter, option, index):
        color_hex = index.data(Qt.UserRole)
        rect = option.rect
        if color_hex:
            color = QColor(color_hex)
            box_rect = QRect(rect.left() + 4, rect.top() + (rect.height() - 16) // 2, 16, 16)
            painter.save()
            painter.setRenderHint(QPainter.Antialiasing)
            painter.setBrush(color)
            painter.setPen(Qt.black)
            painter.drawRect(box_rect)
            painter.restore()
            text_rect = QRect(box_rect.right() + 8, rect.top(), rect.width() - 28, rect.height())
            painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, index.data(Qt.DisplayRole))
        else:
            super().paint(painter, option, index)

    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        size.setHeight(max(size.height(), 22))
        return size

class ColorBoxComboBox(QComboBox):
    """QComboBox that shows a color box in both the dropdown and the selected area."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setItemDelegate(ColorBoxDelegate(self))

    def paintEvent(self, event):
        if not self.isEnabled():
            # Use default paint event for disabled state
            super().paintEvent(event)
            return
        painter = QPainter(self)
        opt = QStyleOptionComboBox()
        self.initStyleOption(opt)
        opt.rect = self.rect()

        # Draw the combo box frame and arrow
        style = self.style()
        combo_opt = QStyleOptionViewItem()
        combo_opt.rect = self.rect()
        style.drawComplexControl(QStyle.CC_ComboBox, opt, painter, self)

        # Draw the selected item with color box
        idx = self.currentIndex()
        if idx >= 0:
            color_hex = self.itemData(idx, Qt.UserRole)
            text = self.itemText(idx)
            rect = self.rect().adjusted(4, 0, -20, 0)
            if color_hex:
                color = QColor(color_hex)
                box_rect = QRect(rect.left(), rect.top() + (rect.height() - 16) // 2, 16, 16)
                painter.save()
                painter.setRenderHint(QPainter.Antialiasing)
                painter.setBrush(color)
                painter.setPen(Qt.black)
                painter.drawRect(box_rect)
                painter.restore()
                text_rect = QRect(box_rect.right() + 8, rect.top(), rect.width() - 28, rect.height())
                painter.drawText(text_rect, Qt.AlignVCenter | Qt.AlignLeft, text)
            else:
                painter.drawText(rect, Qt.AlignVCenter | Qt.AlignLeft, text)
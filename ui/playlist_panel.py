from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
    QLabel,
    QListWidget,
    QPushButton,
    QVBoxLayout,
    QWidget,
)


class PlaylistPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("playlistPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setMinimumWidth(220)
        self.setMaximumWidth(360)
        self.setStyleSheet(
            "#playlistPanel {"
            "background-color: rgba(20, 22, 27, 215);"
            "border: 1px solid rgba(255, 255, 255, 45);"
            "border-radius: 8px;"
            "}"
            "#playlistPanel QLabel { color: #f1f1f1; }"
            "#playlistPanel QListWidget {"
            "background-color: rgba(10, 12, 15, 190);"
            "color: #f1f1f1;"
            "border: 1px solid rgba(255, 255, 255, 35);"
            "}"
        )

        self.label = QLabel("Плейлист")
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(220)
        self.list_widget.setVerticalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAsNeeded
        )
        self.list_widget.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.list_widget.setVerticalScrollMode(
            QAbstractItemView.ScrollMode.ScrollPerPixel
        )
        self.list_widget.setTextElideMode(
            Qt.TextElideMode.ElideMiddle
        )
        self.list_widget.setToolTip(
            "Подвійне натискання запускає вибране медіа"
        )

        self.add_button = QPushButton("Додати медіа")
        self.add_button.setToolTip(
            "Додати файли до плейлиста"
        )

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(8, 8, 8, 8)
        self._layout.addWidget(self.label)
        self._layout.addWidget(self.list_widget)
        self._layout.addWidget(self.add_button)

    def add_item(self, display_name, source):
        self.list_widget.addItem(display_name)
        item = self.list_widget.item(
            self.list_widget.count() - 1
        )
        item.setToolTip(source)
        self.list_widget.scrollToBottom()

    def select(self, index):
        self.list_widget.setCurrentRow(index)
        item = self.list_widget.item(index)

        if item is not None:
            self.list_widget.scrollToItem(item)

    def set_overlay_bottom_margin(self, margin):
        margins = self._layout.contentsMargins()
        self._layout.setContentsMargins(
            margins.left(),
            margins.top(),
            margins.right(),
            max(0, int(margin)),
        )

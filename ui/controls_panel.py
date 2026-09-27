from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QLabel,
    QPushButton,
    QStyle,
    QVBoxLayout,
    QWidget,
)


PANEL_STYLE = """
#controlsPanel {
    background-color: rgba(16, 18, 22, 165);
    border: 1px solid rgba(255, 255, 255, 45);
    border-radius: 8px;
}
"""


class ControlsPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        self.setObjectName("controlsPanel")
        self.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground)
        self.setStyleSheet(PANEL_STYLE)

        self.media_label = QLabel("Медіафайл не вибрано")
        self.play_pause_button = QPushButton()

        style = self.style()
        self.play_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaPlay
        )
        self.pause_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaPause
        )

        self.play_pause_button.setIcon(self.play_icon)
        self.play_pause_button.setIconSize(QSize(24, 24))
        self.play_pause_button.setFixedSize(QSize(32, 30))
        self.play_pause_button.setToolTip("Відтворити")
        self.play_pause_button.setEnabled(False)

        controls_layout = QGridLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setColumnStretch(0, 1)
        controls_layout.setColumnStretch(2, 1)
        controls_layout.addWidget(
            self.play_pause_button,
            0,
            1,
            Qt.AlignmentFlag.AlignHCenter,
        )

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(6)
        self._layout.addWidget(self.media_label)
        self._layout.addLayout(controls_layout)

    def set_media(self, display_name, source):
        self.media_label.setText(display_name)
        self.media_label.setToolTip(source)
        self.play_pause_button.setEnabled(True)
        self.set_playing(False)

    def set_playing(self, playing, restart=False):
        if playing:
            self.play_pause_button.setIcon(self.pause_icon)
            self.play_pause_button.setToolTip("Пауза")
            return

        self.play_pause_button.setIcon(self.play_icon)
        self.play_pause_button.setToolTip(
            "Відтворити спочатку" if restart else "Відтворити"
        )

    def height_hint(self):
        margins = self._layout.contentsMargins()
        return (
            margins.top()
            + margins.bottom()
            + self.media_label.sizeHint().height()
            + self.play_pause_button.sizeHint().height()
            + self._layout.spacing()
        )

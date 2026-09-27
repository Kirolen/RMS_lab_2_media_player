from PySide6.QtCore import QSize, Qt
from PySide6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QStyle,
    QVBoxLayout,
    QWidget,
)

from utils.time_utils import format_time


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
        self.current_time_label = QLabel("00:00")
        self.total_time_label = QLabel("00:00")
        self.progress_slider = QSlider(
            Qt.Orientation.Horizontal
        )
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setEnabled(False)
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

        timeline_layout = QHBoxLayout()
        timeline_layout.addWidget(self.current_time_label)
        timeline_layout.addWidget(
            self.progress_slider,
            stretch=1,
        )
        timeline_layout.addWidget(self.total_time_label)

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(12, 8, 12, 8)
        self._layout.setSpacing(6)
        self._layout.addWidget(self.media_label)
        self._layout.addLayout(timeline_layout)
        self._layout.addLayout(controls_layout)

    def set_media(self, display_name, source):
        self.media_label.setText(display_name)
        self.media_label.setToolTip(source)
        self.play_pause_button.setEnabled(True)
        self.progress_slider.setEnabled(True)
        self.current_time_label.setText("00:00")
        self.total_time_label.setText("00:00")
        self.progress_slider.setValue(0)
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

    def update_progress(self, current_ms, total_ms, position):
        self.current_time_label.setText(format_time(current_ms))
        self.total_time_label.setText(format_time(total_ms))

        if not self.progress_slider.isSliderDown():
            self.progress_slider.setValue(int(position * 1000))

    def set_finished(self, total_ms):
        formatted_time = format_time(total_ms)
        self.current_time_label.setText(formatted_time)
        self.total_time_label.setText(formatted_time)
        self.progress_slider.setValue(1000)
        self.set_playing(False, restart=True)

    def height_hint(self):
        margins = self._layout.contentsMargins()
        timeline_height = max(
            self.current_time_label.sizeHint().height(),
            self.progress_slider.sizeHint().height(),
            self.total_time_label.sizeHint().height(),
        )
        return (
            margins.top()
            + margins.bottom()
            + self.media_label.sizeHint().height()
            + timeline_height
            + self.play_pause_button.sizeHint().height()
            + self._layout.spacing() * 2
        )

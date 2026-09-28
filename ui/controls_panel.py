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
        self.playlist_toggle_button = QPushButton("Плейлист")
        self.playlist_toggle_button.setCheckable(True)
        self.previous_button = QPushButton()
        self.play_pause_button = QPushButton()
        self.next_button = QPushButton()
        self.mute_button = QPushButton()
        self.fullscreen_button = QPushButton()
        self.volume_slider = QSlider(
            Qt.Orientation.Horizontal
        )
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_value_label = QLabel("70%")

        style = self.style()
        self.previous_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaSkipBackward
        )
        self.play_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaPlay
        )
        self.pause_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaPause
        )
        self.next_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaSkipForward
        )
        self.fullscreen_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_TitleBarMaxButton
        )
        self.exit_fullscreen_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_TitleBarNormalButton
        )
        self.volume_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaVolume
        )
        self.muted_icon = style.standardIcon(
            QStyle.StandardPixmap.SP_MediaVolumeMuted
        )

        for button, icon in (
            (self.previous_button, self.previous_icon),
            (self.play_pause_button, self.play_icon),
            (self.next_button, self.next_icon),
        ):
            button.setIcon(icon)
            button.setIconSize(QSize(24, 24))
            button.setFixedSize(QSize(32, 30))

        self.previous_button.setToolTip(
            "Попередній елемент плейлиста"
        )
        self.play_pause_button.setToolTip("Відтворити")
        self.play_pause_button.setEnabled(False)
        self.next_button.setToolTip(
            "Наступний елемент плейлиста"
        )
        self.set_navigation_enabled(False, False)

        self.playlist_toggle_button.setFixedWidth(105)
        self.playlist_toggle_button.setToolTip(
            "Показати або сховати плейлист"
        )

        self.mute_button.setIcon(self.volume_icon)
        self.mute_button.setIconSize(QSize(24, 24))
        self.mute_button.setFixedSize(QSize(32, 30))
        self.mute_button.setToolTip("Вимкнути звук")
        self.fullscreen_button.setIcon(self.fullscreen_icon)
        self.fullscreen_button.setIconSize(QSize(24, 24))
        self.fullscreen_button.setFixedSize(QSize(32, 30))
        self.fullscreen_button.setToolTip("На весь екран")
        self.volume_slider.setFixedWidth(65)
        self.volume_slider.setToolTip("Гучність")
        self.volume_value_label.setFixedWidth(30)

        self.left_controls = QWidget()
        left_layout = QHBoxLayout(self.left_controls)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)
        left_layout.addWidget(self.playlist_toggle_button)

        self.center_controls = QWidget()
        center_layout = QHBoxLayout(self.center_controls)
        center_layout.setContentsMargins(0, 0, 0, 0)
        center_layout.setSpacing(4)
        center_layout.addWidget(self.previous_button)
        center_layout.addWidget(self.play_pause_button)
        center_layout.addWidget(self.next_button)

        self.right_controls = QWidget()
        right_layout = QHBoxLayout(self.right_controls)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)
        right_layout.addWidget(self.mute_button)
        right_layout.addWidget(self.volume_slider)
        right_layout.addWidget(self.volume_value_label)
        right_layout.addWidget(self.fullscreen_button)

        side_width = max(
            self.left_controls.sizeHint().width(),
            self.right_controls.sizeHint().width(),
        )
        controls_layout = QGridLayout()
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setHorizontalSpacing(4)
        controls_layout.setColumnMinimumWidth(0, side_width)
        controls_layout.setColumnMinimumWidth(2, side_width)
        controls_layout.setColumnStretch(0, 1)
        controls_layout.setColumnStretch(2, 1)
        controls_layout.addWidget(
            self.left_controls,
            0,
            0,
            Qt.AlignmentFlag.AlignLeft,
        )
        controls_layout.addWidget(
            self.center_controls,
            0,
            1,
            Qt.AlignmentFlag.AlignHCenter,
        )
        controls_layout.addWidget(
            self.right_controls,
            0,
            2,
            Qt.AlignmentFlag.AlignRight,
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

    def set_navigation_enabled(self, previous, next_):
        self.previous_button.setEnabled(previous)
        self.next_button.setEnabled(next_)

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

    def set_volume_state(self, volume, muted):
        self.volume_value_label.setText(f"{volume}%")
        self.mute_button.setIcon(
            self.muted_icon if muted else self.volume_icon
        )
        self.mute_button.setToolTip(
            "Увімкнути звук" if muted else "Вимкнути звук"
        )

    def set_fullscreen_state(self, fullscreen):
        self.fullscreen_button.setIcon(
            self.exit_fullscreen_icon
            if fullscreen
            else self.fullscreen_icon
        )
        self.fullscreen_button.setToolTip(
            "Вийти з повноекранного режиму (Escape)"
            if fullscreen
            else "На весь екран"
        )

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
            + max(
                self.left_controls.sizeHint().height(),
                self.center_controls.sizeHint().height(),
                self.right_controls.sizeHint().height(),
            )
            + self._layout.spacing() * 2
        )

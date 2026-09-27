import logging
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, QTimer, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from player.media_player import MediaPlayer
from ui.controls_panel import ControlsPanel
from ui.menu_bar import setup_menu_bar
from utils.logger import log_call
from utils.media_sources import is_valid_media_url


MEDIA_FILTER = (
    "Медіафайли "
    "(*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav);;"
    "Усі файли (*)"
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    @log_call
    def __init__(self):
        super().__init__()

        self.current_media_source = None
        self._playback_finished = False
        self._playback_error_shown = False
        self.setWindowTitle("Media Player")
        self.resize(960, 640)
        self.setMinimumSize(720, 480)

        self.menu_actions = setup_menu_bar(self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(12, 12, 12, 12)

        self.video_frame = QFrame()
        self.video_frame.setObjectName("videoFrame")
        self.video_frame.setMinimumSize(320, 180)
        self.video_frame.setAttribute(
            Qt.WidgetAttribute.WA_NativeWindow
        )
        self.video_frame.setStyleSheet(
            "#videoFrame { background-color: #111111; }"
        )
        self.main_layout.addWidget(self.video_frame, stretch=1)

        self.controls = ControlsPanel(central_widget)
        self.controls.raise_()

        self.player = MediaPlayer()
        self.player.set_video_output(
            int(self.video_frame.winId())
        )

        self.menu_actions.open_file.triggered.connect(
            self._open_file
        )
        self.menu_actions.open_url.triggered.connect(
            self._open_url
        )
        self.controls.play_pause_button.clicked.connect(
            self._toggle_playback
        )
        self.controls.progress_slider.sliderReleased.connect(
            self._seek
        )
        self.controls.volume_slider.valueChanged.connect(
            self._change_volume
        )
        self.controls.volume_slider.sliderReleased.connect(
            self._finish_volume_change
        )
        self.controls.mute_button.clicked.connect(
            self._toggle_mute
        )

        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(250)
        self.playback_timer.timeout.connect(
            self._update_playback_state
        )
        self.playback_timer.start()

        self.player.set_volume(
            self.controls.volume_slider.value()
        )
        self._sync_volume_state()

        QTimer.singleShot(0, self._position_controls_panel)

    @log_call
    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть медіафайл",
            "",
            MEDIA_FILTER,
        )

        if file_path:
            self.load_media(file_path)

    @log_call
    def _open_url(self):
        url, confirmed = QInputDialog.getText(
            self,
            "Відкрити URL",
            "Введіть пряме посилання на медіафайл:",
        )
        url = url.strip()

        if not confirmed or not url:
            return

        if not is_valid_media_url(url):
            self._show_error(
                "Некоректний URL",
                "Введіть повне посилання, яке починається "
                "з http:// або https://.",
            )
            return

        self.load_media(url, url)

    @log_call
    def load_media(self, media_source, display_name=None):
        self.current_media_source = media_source
        self._playback_finished = False
        self._playback_error_shown = False
        self.player.load(media_source)
        self.controls.set_media(
            display_name or Path(media_source).name,
            media_source,
        )

        if self.player.play():
            self._playback_finished = False
            self.controls.set_playing(True)
        else:
            self._show_playback_error()

    @log_call
    def _seek(self):
        position = self.controls.progress_slider.value() / 1000
        self.player.set_position(position)
        self._playback_finished = False
        self._update_playback_state()

    def _change_volume(self, volume):
        self.player.set_volume(
            volume,
            remember=(
                not self.controls.volume_slider.isSliderDown()
            ),
        )
        self.controls.set_volume_state(
            self.player.get_volume(),
            self.player.is_muted(),
        )

    def _finish_volume_change(self):
        self.player.set_volume(
            self.controls.volume_slider.value()
        )
        self._sync_volume_state()

    @log_call
    def _toggle_mute(self):
        self.player.toggle_mute()
        self._sync_volume_state()

    def _sync_volume_state(self):
        slider = self.controls.volume_slider
        blocker = QSignalBlocker(slider)
        slider.setValue(self.player.get_volume())
        del blocker
        self.controls.set_volume_state(
            self.player.get_volume(),
            self.player.is_muted(),
        )

    @log_call
    def _toggle_playback(self):
        if self.current_media_source is None:
            return

        if self.player.is_playing():
            self.player.pause()
            self.controls.set_playing(False)
            return

        if self.player.play():
            self._playback_finished = False
            self.controls.set_playing(True)

    def _update_playback_state(self):
        if self.current_media_source is None:
            return

        if self.player.has_error():
            self._show_playback_error()
            return

        if self.player.has_ended():
            if not self._playback_finished:
                self._playback_finished = True
                self.controls.set_finished(
                    self.player.get_length()
                )
            return

        self.controls.update_progress(
            self.player.get_time(),
            self.player.get_length(),
            self.player.get_position(),
        )

    def _show_playback_error(self):
        if self._playback_error_shown:
            return

        self._playback_error_shown = True
        self.controls.set_playing(False)
        self._show_error(
            "Помилка відтворення",
            "Не вдалося відкрити медіа. Перевірте файл або URL.",
        )

    def _show_error(self, title, message):
        logger.error("%s | %s", title, message)
        QMessageBox.critical(self, title, message)

    def _position_controls_panel(self):
        central_widget = self.centralWidget()

        if central_widget is None:
            return

        margins = self.main_layout.contentsMargins()
        panel_width = max(
            0,
            central_widget.width()
            - margins.left()
            - margins.right(),
        )
        panel_height = self.controls.height_hint()
        panel_y = max(
            margins.top(),
            central_widget.height()
            - margins.bottom()
            - panel_height,
        )
        self.controls.setGeometry(
            margins.left(),
            panel_y,
            panel_width,
            panel_height,
        )
        self.controls.raise_()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._position_controls_panel()

    @log_call
    def closeEvent(self, event):
        self.playback_timer.stop()
        self.player.release()
        event.accept()

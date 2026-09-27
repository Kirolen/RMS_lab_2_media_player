from pathlib import Path

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

from player.media_player import MediaPlayer
from ui.controls_panel import ControlsPanel
from ui.menu_bar import setup_menu_bar
from utils.logger import log_call


MEDIA_FILTER = (
    "Медіафайли "
    "(*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav);;"
    "Усі файли (*)"
)


class MainWindow(QMainWindow):
    @log_call
    def __init__(self):
        super().__init__()

        self.current_media_source = None
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
        self.controls.play_pause_button.clicked.connect(
            self._toggle_playback
        )

        self.playback_timer = QTimer(self)
        self.playback_timer.setInterval(250)
        self.playback_timer.timeout.connect(
            self._update_playback_state
        )
        self.playback_timer.start()

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
    def load_media(self, file_path):
        self.current_media_source = file_path
        self.player.load(file_path)
        self.controls.set_media(
            Path(file_path).name,
            file_path,
        )

        if self.player.play():
            self.controls.set_playing(True)

    @log_call
    def _toggle_playback(self):
        if self.current_media_source is None:
            return

        if self.player.is_playing():
            self.player.pause()
            self.controls.set_playing(False)
            return

        if self.player.play():
            self.controls.set_playing(True)

    def _update_playback_state(self):
        if self.player.has_ended():
            self.controls.set_playing(False, restart=True)

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

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from player.media_player import MediaPlayer
from utils.logger import log_call


class MainWindow(QMainWindow):
    @log_call
    def __init__(self):
        super().__init__()

        self.setWindowTitle("Media Player")
        self.resize(960, 640)
        self.setMinimumSize(720, 480)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        title_label = QLabel("Медіаплеєр")
        title_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )
        title_label.setStyleSheet(
            "font-size: 18px; font-weight: 600;"
        )

        self.video_frame = QFrame()
        self.video_frame.setObjectName("videoFrame")
        self.video_frame.setMinimumSize(320, 180)
        self.video_frame.setAttribute(
            Qt.WidgetAttribute.WA_NativeWindow
        )
        self.video_frame.setStyleSheet(
            "#videoFrame {"
            "background-color: #111111;"
            "border: 1px solid #333333;"
            "}"
        )

        self.media_label = QLabel(
            "Медіафайл не вибрано"
        )
        self.media_label.setAlignment(
            Qt.AlignmentFlag.AlignCenter
        )

        self.open_button = QPushButton("Відкрити файл")
        self.open_button.clicked.connect(self._open_file)

        media_row = QHBoxLayout()
        media_row.addWidget(self.open_button)
        media_row.addWidget(self.media_label, stretch=1)

        layout.addWidget(title_label)
        layout.addWidget(self.video_frame, stretch=1)
        layout.addLayout(media_row)

        self.player = MediaPlayer()
        self.player.set_video_output(
            int(self.video_frame.winId())
        )

    @log_call
    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть медіафайл",
            "",
            (
                "Медіафайли "
                "(*.mp4 *.mkv *.avi *.mov *.webm *.mp3 *.wav);;"
                "Усі файли (*)"
            ),
        )

        if file_path:
            self.load_media(file_path)

    @log_call
    def load_media(self, file_path):
        self.player.load(file_path)
        self.player.play()
        self.media_label.setText(Path(file_path).name)
        self.setWindowTitle(
            f"Media Player — {Path(file_path).name}"
        )

    @log_call
    def closeEvent(self, event):
        self.player.release()
        event.accept()


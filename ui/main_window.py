from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QMainWindow,
    QVBoxLayout,
    QWidget,
)

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

        layout.addWidget(title_label)
        layout.addWidget(self.video_frame, stretch=1)
        layout.addWidget(self.media_label)


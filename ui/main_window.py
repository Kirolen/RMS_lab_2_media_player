import logging
from pathlib import Path

from PySide6.QtCore import QEvent, QSignalBlocker, QTimer, Qt
from PySide6.QtGui import QCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QInputDialog,
    QMainWindow,
    QMessageBox,
    QVBoxLayout,
    QWidget,
)

from player.media_player import MediaPlayer
from player.playlist import Playlist
from ui.controls_panel import ControlsPanel
from ui.menu_bar import setup_menu_bar
from ui.playlist_panel import PlaylistPanel
from utils.logger import log_call
from utils.media_sources import (
    get_media_file_filter,
    is_supported_media_file,
    is_valid_media_url,
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    @log_call
    def __init__(self):
        super().__init__()

        self.current_media_source = None
        self._playback_finished = False
        self._playback_error_shown = False
        self._was_maximized_before_fullscreen = False
        self._playlist_was_visible_before_fullscreen = False
        self._last_mouse_position = None
        self.setWindowTitle("Media Player")
        self.resize(960, 640)
        self.setMinimumSize(720, 480)
        self.setAcceptDrops(True)

        self.menu_actions = setup_menu_bar(self)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        self.main_layout = QVBoxLayout(central_widget)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

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

        self.playlist_panel = PlaylistPanel(central_widget)
        self.playlist_panel.hide()
        self.controls = ControlsPanel(central_widget)
        self.playlist_panel.raise_()
        self.controls.raise_()

        self.player = MediaPlayer()
        self.playlist = Playlist()
        self.player.set_video_output(
            int(self.video_frame.winId())
        )

        self.menu_actions.open_file.triggered.connect(
            self._open_file
        )
        self.menu_actions.open_url.triggered.connect(
            self._open_url
        )
        self.playlist_panel.add_button.clicked.connect(
            self._add_files_to_playlist
        )
        self.playlist_panel.list_widget.itemDoubleClicked.connect(
            self._play_playlist_item
        )
        self.controls.playlist_toggle_button.clicked.connect(
            self._toggle_playlist_panel
        )
        self.controls.previous_button.clicked.connect(
            self._play_previous
        )
        self.controls.play_pause_button.clicked.connect(
            self._toggle_playback
        )
        self.controls.next_button.clicked.connect(
            self._play_next
        )
        self.controls.fullscreen_button.clicked.connect(
            self._toggle_fullscreen
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

        self.controls_hide_timer = QTimer(self)
        self.controls_hide_timer.setSingleShot(True)
        self.controls_hide_timer.setInterval(5_000)
        self.controls_hide_timer.timeout.connect(
            self._hide_inactive_controls
        )

        self.mouse_activity_timer = QTimer(self)
        self.mouse_activity_timer.setInterval(150)
        self.mouse_activity_timer.timeout.connect(
            self._check_mouse_activity
        )

        self.layout_update_timer = QTimer(self)
        self.layout_update_timer.setSingleShot(True)
        self.layout_update_timer.setInterval(0)
        self.layout_update_timer.timeout.connect(
            self._apply_layout_update
        )

        self.player.set_volume(
            self.controls.volume_slider.value()
        )
        self._sync_volume_state()

        self.setMouseTracking(True)
        for widget in self.findChildren(QWidget):
            widget.setMouseTracking(True)

        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)

        self._schedule_layout_update()

    def eventFilter(self, watched, event):
        if (
            watched is self.video_frame
            and event.type() == QEvent.Type.Resize
        ):
            self._schedule_layout_update()

        if (
            event.type() == QEvent.Type.MouseMove
            and self.isFullScreen()
            and isinstance(watched, QWidget)
            and (watched is self or self.isAncestorOf(watched))
        ):
            mouse_position = event.globalPosition().toPoint()

            if mouse_position != self._last_mouse_position:
                self._last_mouse_position = mouse_position
                self._show_fullscreen_controls()

        return super().eventFilter(watched, event)

    @log_call
    def _open_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Виберіть медіафайл",
            "",
            get_media_file_filter(),
        )

        if not file_path:
            return

        if not is_supported_media_file(file_path):
            self._show_error(
                "Непідтримуваний файл",
                "Вибраний файл не є підтримуваним медіа.",
            )
            return

        index = self._add_to_playlist(
            file_path,
            Path(file_path).name,
        )
        self._load_playlist_index(index)

    @log_call
    def _add_files_to_playlist(self):
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Додати медіафайли до плейлиста",
            "",
            get_media_file_filter(),
        )
        invalid_files_count = 0

        for file_path in file_paths:
            if not is_supported_media_file(file_path):
                invalid_files_count += 1
                continue

            self._add_to_playlist(
                file_path,
                Path(file_path).name,
            )

        if invalid_files_count:
            self._show_error(
                "Непідтримувані файли",
                "Частину вибраних файлів не додано, "
                "оскільки їх формат не підтримується.",
            )

    def _get_dropped_media_files(self, mime_data):
        if not mime_data.hasUrls():
            return []

        return [
            str(Path(url.toLocalFile()))
            for url in mime_data.urls()
            if url.isLocalFile()
            and is_supported_media_file(url.toLocalFile())
        ]

    def dragEnterEvent(self, event):
        if self._get_dropped_media_files(event.mimeData()):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        file_paths = self._get_dropped_media_files(
            event.mimeData()
        )

        if not file_paths:
            event.ignore()
            return

        first_index = None

        for file_path in file_paths:
            index = self._add_to_playlist(
                file_path,
                Path(file_path).name,
            )
            if first_index is None:
                first_index = index

        self._load_playlist_index(first_index)
        event.acceptProposedAction()

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

        index = self._add_to_playlist(url, url)
        self._load_playlist_index(index)

    def _add_to_playlist(self, source, display_name):
        index = self.playlist.add(source, display_name)
        self.playlist_panel.add_item(display_name, source)
        self._sync_navigation_state()
        return index

    def _load_playlist_index(self, index):
        item = self.playlist.select(index)

        if item is None:
            return False

        self.playlist_panel.select(index)
        self.load_media(item.source, item.display_name)
        self._sync_navigation_state()
        return True

    def _play_playlist_item(self, item):
        index = self.playlist_panel.list_widget.row(item)
        self._load_playlist_index(index)

    @log_call
    def _play_previous(self):
        index = self.playlist.get_previous_index()

        if index is not None:
            self._load_playlist_index(index)

    @log_call
    def _play_next(self):
        index = self.playlist.get_next_index()

        if index is not None:
            self._load_playlist_index(index)

    def _sync_navigation_state(self):
        current_index = self.playlist.get_current_index()
        last_index = self.playlist.count() - 1
        self.controls.set_navigation_enabled(
            current_index > 0,
            0 <= current_index < last_index,
        )

    @log_call
    def _toggle_playlist_panel(self):
        show_playlist = self.playlist_panel.isHidden()
        self.playlist_panel.setVisible(show_playlist)
        self.controls.playlist_toggle_button.setChecked(
            show_playlist
        )

        if self.isFullScreen():
            self._playlist_was_visible_before_fullscreen = (
                show_playlist
            )

        self._schedule_layout_update()
        self.controls.raise_()

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
            self._schedule_layout_update()
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
                next_index = self.playlist.get_next_index()

                if next_index is not None:
                    self._load_playlist_index(next_index)
                    return

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

    def _schedule_layout_update(self):
        if hasattr(self, "layout_update_timer"):
            self.layout_update_timer.start()

    def _apply_layout_update(self):
        self._position_playlist_panel()
        self._position_controls_panel()
        self._update_video_aspect_ratio()

    def _position_playlist_panel(self):
        central_widget = self.centralWidget()

        if central_widget is None:
            return

        video_position = self.video_frame.mapTo(
            central_widget,
            self.video_frame.rect().topLeft(),
        )
        playlist_width = min(260, self.video_frame.width())
        self.playlist_panel.setGeometry(
            video_position.x(),
            video_position.y(),
            playlist_width,
            self.video_frame.height(),
        )
        self.playlist_panel.raise_()

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
        self.playlist_panel.set_overlay_bottom_margin(
            panel_height + 6
        )
        self.controls.raise_()

    def _update_video_aspect_ratio(self):
        video_size = self.video_frame.size()
        self.player.set_video_aspect_ratio(
            video_size.width(),
            video_size.height(),
        )

    def _show_fullscreen_controls(self):
        self.controls.show()
        self._position_controls_panel()
        self.controls.raise_()
        self.controls_hide_timer.start()

    def _check_mouse_activity(self):
        if not self.isFullScreen():
            return

        mouse_position = QCursor.pos()

        if mouse_position != self._last_mouse_position:
            self._last_mouse_position = mouse_position
            self._show_fullscreen_controls()

    def _hide_inactive_controls(self):
        if self.isFullScreen():
            self.controls.hide()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._schedule_layout_update()

    @log_call
    def _toggle_fullscreen(self):
        if self.isFullScreen():
            self._leave_fullscreen()
        else:
            self._enter_fullscreen()

    def _enter_fullscreen(self):
        self._was_maximized_before_fullscreen = self.isMaximized()
        self._playlist_was_visible_before_fullscreen = (
            self.playlist_panel.isVisible()
        )
        self.playlist_panel.hide()
        self.controls.playlist_toggle_button.setChecked(False)
        self.menuBar().hide()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.showFullScreen()

        self._last_mouse_position = QCursor.pos()
        self.mouse_activity_timer.start()
        self.controls.set_fullscreen_state(True)
        self._show_fullscreen_controls()
        self._schedule_layout_update()

    def _leave_fullscreen(self):
        self.controls_hide_timer.stop()
        self.mouse_activity_timer.stop()
        self._last_mouse_position = None
        self.menuBar().show()
        self.controls.show()
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)
        self.playlist_panel.setVisible(
            self._playlist_was_visible_before_fullscreen
        )
        self.controls.playlist_toggle_button.setChecked(
            self._playlist_was_visible_before_fullscreen
        )

        if self._was_maximized_before_fullscreen:
            self.showMaximized()
        else:
            self.showNormal()

        self.controls.set_fullscreen_state(False)
        self._schedule_layout_update()

    def keyPressEvent(self, event):
        if (
            event.key() == Qt.Key.Key_Escape
            and self.isFullScreen()
        ):
            self._toggle_fullscreen()
            event.accept()
            return

        super().keyPressEvent(event)

    @log_call
    def closeEvent(self, event):
        for timer in (
            self.playback_timer,
            self.controls_hide_timer,
            self.mouse_activity_timer,
            self.layout_update_timer,
        ):
            timer.stop()

        application = QApplication.instance()
        if application is not None:
            application.removeEventFilter(self)

        self.player.release()
        event.accept()

import logging
from pathlib import Path

from PySide6.QtCore import QEvent, QSignalBlocker, Qt, QTimer
from PySide6.QtGui import QCursor, QKeySequence, QShortcut
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
from player.playback_controller import PlaybackController
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
        self._was_maximized_before_fullscreen = False
        self._playlist_was_visible_before_fullscreen = False
        self._last_mouse_position = None

        self.setWindowTitle("Media Player")
        self.resize(960, 640)
        self.setMinimumSize(720, 480)
        self.setAcceptDrops(True)

        self._setup_ui()

        self.player = MediaPlayer()
        self.playlist = Playlist()
        self.playback = PlaybackController(
            self.player,
            self.playlist,
            self,
        )

        self._connect_signals()
        self._setup_shortcuts()
        self._setup_timers()
        self._setup_mouse_tracking()

        self.player.set_video_output(
            int(self.video_frame.winId())
        )
        self.playback.set_volume(
            self.controls.volume_slider.value()
        )
        self._schedule_layout_update()

    def _setup_ui(self):
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

        self.playlist_panel = PlaylistPanel(central_widget)
        self.playlist_panel.hide()

        self.controls = ControlsPanel(central_widget)

        self.main_layout.addWidget(
            self.video_frame,
            stretch=1,
        )
        self.playlist_panel.raise_()
        self.controls.raise_()

    def _connect_signals(self):
        controls = self.controls

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

        controls.playlist_toggle_button.clicked.connect(
            self._toggle_playlist_panel
        )
        controls.previous_button.clicked.connect(
            self.playback.play_previous
        )
        controls.backward_button.clicked.connect(
            lambda: self.playback.seek_relative(-10_000)
        )
        controls.play_pause_button.clicked.connect(
            self.playback.toggle_playback
        )
        controls.forward_button.clicked.connect(
            lambda: self.playback.seek_relative(10_000)
        )
        controls.next_button.clicked.connect(
            self.playback.play_next
        )
        controls.fullscreen_button.clicked.connect(
            self._toggle_fullscreen
        )
        controls.speed_combo.currentIndexChanged.connect(
            self._change_playback_rate
        )
        controls.progress_slider.sliderReleased.connect(
            self._seek
        )
        controls.volume_slider.valueChanged.connect(
            self._change_volume
        )
        controls.volume_slider.sliderReleased.connect(
            self._finish_volume_change
        )
        controls.mute_button.clicked.connect(
            self.playback.toggle_mute
        )

        self.playback.media_loaded.connect(
            self._on_media_loaded
        )
        self.playback.navigation_changed.connect(
            controls.set_navigation_enabled
        )
        self.playback.playing_changed.connect(
            controls.set_playing
        )
        self.playback.progress_changed.connect(
            controls.update_progress
        )
        self.playback.playback_finished.connect(
            controls.set_finished
        )
        self.playback.volume_changed.connect(
            self._on_volume_changed
        )
        self.playback.error_occurred.connect(
            self._show_error
        )

    def _setup_shortcuts(self):
        bindings = (
            ("Space", self.playback.toggle_playback, False),
            (
                "Left",
                lambda: self.playback.seek_relative(-10_000),
                True,
            ),
            (
                "Right",
                lambda: self.playback.seek_relative(10_000),
                True,
            ),
            ("Up", self._increase_volume, True),
            ("Down", self._decrease_volume, True),
            ("M", self.playback.toggle_mute, False),
            ("F", self._toggle_fullscreen, False),
            ("Ctrl+Left", self.playback.play_previous, False),
            ("Ctrl+Right", self.playback.play_next, False),
        )
        self.shortcuts = []

        for sequence, handler, auto_repeat in bindings:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(
                Qt.ShortcutContext.WindowShortcut
            )
            shortcut.setAutoRepeat(auto_repeat)
            shortcut.activated.connect(handler)
            self.shortcuts.append(shortcut)

    def _setup_timers(self):
        self.progress_timer = QTimer(self)
        self.progress_timer.setInterval(250)
        self.progress_timer.timeout.connect(self.playback.poll)
        self.progress_timer.start()

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

    def _setup_mouse_tracking(self):
        self.setMouseTracking(True)

        for widget in self.findChildren(QWidget):
            widget.setMouseTracking(True)

        application = QApplication.instance()
        if application is not None:
            application.installEventFilter(self)

    def eventFilter(self, watched, event):
        if (
            watched is self.video_frame
            and event.type() == QEvent.Type.MouseButtonPress
            and event.button() == Qt.MouseButton.LeftButton
        ):
            self.playback.toggle_playback()

            if self.isFullScreen():
                self._show_fullscreen_controls()

            event.accept()
            return True

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
        if not hasattr(self, "player"):
            return

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

        self.playback.play_index(first_index)
        event.acceptProposedAction()

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
        self.playback.load_index(index)

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
        self.playback.load_index(index)

    def _add_to_playlist(self, source, display_name):
        index = self.playback.add_to_playlist(
            source,
            display_name,
        )
        self.playlist_panel.add_item(display_name, source)
        return index

    def _play_playlist_item(self, item):
        index = self.playlist_panel.list_widget.row(item)
        self.playback.play_index(index)

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

    def _on_media_loaded(self, index, display_name, source):
        self.current_media_source = source
        self.playlist_panel.select(index)
        self.controls.set_media(display_name, source)
        self._schedule_layout_update()

    def _seek(self):
        self.playback.seek_to(
            self.controls.progress_slider.value() / 1000
        )

    def _change_playback_rate(self, index):
        rate = self.controls.speed_combo.itemData(index)

        if rate is not None:
            self.playback.set_playback_rate(rate)

    def _increase_volume(self):
        slider = self.controls.volume_slider
        slider.setValue(min(100, slider.value() + 5))

    def _decrease_volume(self):
        slider = self.controls.volume_slider
        slider.setValue(max(0, slider.value() - 5))

    def _change_volume(self, volume):
        self.playback.set_volume(
            volume,
            remember=(
                not self.controls.volume_slider.isSliderDown()
            ),
        )

    def _finish_volume_change(self):
        self.playback.set_volume(
            self.controls.volume_slider.value()
        )

    def _on_volume_changed(self, volume, muted):
        slider = self.controls.volume_slider
        blocker = QSignalBlocker(slider)
        slider.setValue(volume)
        del blocker
        self.controls.set_volume_state(volume, muted)

    def _show_error(self, title, message):
        logger.error("%s | %s", title, message)
        QMessageBox.critical(self, title, message)

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
            self.progress_timer,
            self.controls_hide_timer,
            self.mouse_activity_timer,
            self.layout_update_timer,
        ):
            timer.stop()

        application = QApplication.instance()
        if application is not None:
            application.removeEventFilter(self)

        self.playback.release()
        event.accept()

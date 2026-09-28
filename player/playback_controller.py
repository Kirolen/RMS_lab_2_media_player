import logging

from PySide6.QtCore import QObject, Signal


logger = logging.getLogger(__name__)


class PlaybackController(QObject):
    media_loaded = Signal(int, str, str)
    navigation_changed = Signal(bool, bool)
    playing_changed = Signal(bool)
    progress_changed = Signal(int, int, float)
    playback_finished = Signal(int)
    volume_changed = Signal(int, bool)
    error_occurred = Signal(str, str)

    def __init__(self, player, playlist, parent=None):
        super().__init__(parent)
        self.player = player
        self.playlist = playlist
        self.current_source = None
        self._media_end_handled = False
        self._media_error_handled = False

    def add_to_playlist(self, source, display_name):
        index = self.playlist.add(source, display_name)
        self._emit_navigation_state()
        return index

    def load_index(self, index):
        item = self.playlist.get(index)

        if item is None:
            return False

        try:
            self.player.load(item.source)
        except Exception:
            logger.exception(
                "Не вдалося завантажити медіа: %s",
                item.source,
            )
            self.error_occurred.emit(
                "Помилка відкриття",
                "Не вдалося відкрити медіа. Перевірте "
                "файл або URL.",
            )
            return False

        self.playlist.select(index)
        self.current_source = item.source
        self._media_end_handled = False
        self._media_error_handled = False
        self.media_loaded.emit(
            index,
            item.display_name,
            item.source,
        )
        self.playing_changed.emit(False)
        self._emit_navigation_state()
        return True

    def play_index(self, index):
        return self.load_index(index) and self._start_playback()

    def play_previous(self):
        index = self.playlist.get_previous_index()
        return index is not None and self.play_index(index)

    def play_next(self):
        index = self.playlist.get_next_index()
        return index is not None and self.play_index(index)

    def toggle_playback(self):
        if self.current_source is None:
            return False

        if self.player.is_playing():
            self.player.pause()
            self.playing_changed.emit(False)
            return True

        if self._media_end_handled:
            current_index = self.playlist.get_current_index()

            if current_index >= 0:
                if not self.load_index(current_index):
                    return False
            else:
                self.player.set_position(0)
                self._media_end_handled = False

        return self._start_playback()

    def _start_playback(self):
        if not self.player.play():
            self.error_occurred.emit(
                "Помилка відтворення",
                "Не вдалося запустити вибране медіа.",
            )
            return False

        self.playing_changed.emit(True)
        return True

    def poll(self):
        if self.current_source is None:
            return

        if self.player.has_error():
            if not self._media_error_handled:
                self._media_error_handled = True
                self.playing_changed.emit(False)
                self.error_occurred.emit(
                    "Помилка відтворення",
                    "VLC не зміг відтворити медіа. Перевірте "
                    "доступність файла або прямого URL.",
                )
            return

        if self.player.has_ended():
            if not self._media_end_handled:
                self._media_end_handled = True
                self._handle_media_ended()
            return

        self.progress_changed.emit(
            self.player.get_time(),
            self.player.get_length(),
            self.player.get_position(),
        )

    def _handle_media_ended(self):
        next_index = self.playlist.get_next_index()

        if next_index is not None:
            self.play_index(next_index)
            return

        self.playing_changed.emit(False)
        self.playback_finished.emit(self.player.get_length())

    def seek_to(self, position):
        if self.current_source is not None:
            self.player.set_position(position)

    def seek_relative(self, offset_ms):
        if self.current_source is not None:
            self.player.seek_relative(offset_ms)

    def set_playback_rate(self, rate):
        if self.current_source is not None:
            self.player.set_playback_rate(rate)

    def set_volume(self, volume, remember=True):
        self.player.set_volume(volume, remember=remember)
        self._emit_volume_state()

    def toggle_mute(self):
        self.player.toggle_mute()
        self._emit_volume_state()

    def _emit_navigation_state(self):
        current_index = self.playlist.get_current_index()
        last_index = self.playlist.count() - 1
        self.navigation_changed.emit(
            current_index > 0,
            0 <= current_index < last_index,
        )

    def _emit_volume_state(self):
        self.volume_changed.emit(
            self.player.get_volume(),
            self.player.is_muted(),
        )

    def release(self):
        self.player.release()

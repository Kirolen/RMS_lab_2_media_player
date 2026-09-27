import sys

import vlc

from utils.logger import log_call


class MediaPlayer:
    @log_call
    def __init__(self):
        self._vlc_instance = vlc.Instance(
            "--no-video-title-show",
            "--quiet",
        )
        self._player = self._vlc_instance.media_player_new()
        self._media = None
        self._window_id = None
        self._is_released = False

    def set_video_output(self, window_id):
        self._window_id = window_id

        if sys.platform.startswith("win"):
            self._player.set_hwnd(window_id)
        elif sys.platform.startswith("linux"):
            self._player.set_xwindow(window_id)
        elif sys.platform == "darwin":
            self._player.set_nsobject(window_id)

    @log_call
    def load(self, file_path):
        if self._is_released:
            return

        new_media = self._vlc_instance.media_new(file_path)
        self._player.set_media(new_media)

        old_media = self._media
        self._media = new_media

        if old_media is not None:
            old_media.release()

        if self._window_id is not None:
            self.set_video_output(self._window_id)

    @log_call
    def play(self):
        if self._is_released or self._media is None:
            return False

        if self.has_ended():
            self._player.set_time(0)

        return self._player.play() != -1

    @log_call
    def pause(self):
        if self._is_released or self._media is None:
            return False

        self._player.set_pause(1)
        return True

    def is_playing(self):
        return (
            not self._is_released
            and bool(self._player.is_playing())
        )

    def has_ended(self):
        return (
            not self._is_released
            and self._player.get_state() == vlc.State.Ended
        )

    def get_time(self):
        if self._is_released:
            return 0

        return max(0, self._player.get_time())

    def get_length(self):
        if self._is_released:
            return 0

        return max(0, self._player.get_length())

    def get_position(self):
        if self._is_released:
            return 0.0

        position = self._player.get_position()
        return min(1.0, max(0.0, position))

    @log_call
    def set_position(self, position):
        if self._is_released or self._media is None:
            return

        position = min(1.0, max(0.0, position))
        self._player.set_position(position)

    @log_call
    def release(self):
        if self._is_released:
            return

        self._is_released = True
        media = self._media
        player = self._player
        instance = self._vlc_instance
        self._media = None
        self._player = None
        self._vlc_instance = None

        if media is not None:
            media.release()
        if player is not None:
            player.release()
        if instance is not None:
            instance.release()

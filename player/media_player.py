import logging
from math import gcd
import sys

import vlc

from utils.logger import log_call


logger = logging.getLogger(__name__)


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
        self._volume = 70
        self._last_volume = 70
        self._is_muted = False
        self._playback_rate = 1.0
        self._is_released = False

    def set_video_output(self, window_id):
        self._window_id = window_id
        self._apply_video_output()

    def set_video_aspect_ratio(self, width, height):
        if (
            self._is_released
            or self._media is None
            or width <= 0
            or height <= 0
        ):
            return

        divisor = gcd(width, height)
        aspect_ratio = (
            f"{width // divisor}:{height // divisor}"
        )
        try:
            self._player.video_set_aspect_ratio(aspect_ratio)
        except OSError:
            logger.debug(
                "VLC відхилив зміну співвідношення сторін",
                exc_info=True,
            )

    def _apply_video_output(self):
        if self._is_released or self._window_id is None:
            return

        if sys.platform.startswith("win"):
            self._player.set_hwnd(self._window_id)
        elif sys.platform.startswith("linux"):
            self._player.set_xwindow(self._window_id)
        elif sys.platform == "darwin":
            self._player.set_nsobject(self._window_id)

        self._player.video_set_mouse_input(False)
        self._player.video_set_key_input(False)

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

        self._apply_video_output()

        self._player.audio_set_volume(self._volume)

    @log_call
    def play(self):
        if self._is_released or self._media is None:
            return False

        if self.has_ended():
            self._player.set_time(0)

        if self._player.play() == -1:
            return False

        self._player.set_rate(self._playback_rate)
        return True

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

    def has_error(self):
        return (
            not self._is_released
            and self._player.get_state() == vlc.State.Error
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
    def seek_relative(self, offset_ms):
        if self._is_released or self._media is None:
            return

        total_time = self.get_length()

        if total_time <= 0:
            return

        new_time = self.get_time() + int(offset_ms)
        new_time = min(total_time, max(0, new_time))
        self._player.set_time(new_time)

    @log_call
    def set_playback_rate(self, rate):
        rate = float(rate)

        if rate not in (0.5, 1.0, 1.5, 2.0):
            return False

        self._playback_rate = rate

        if self._is_released:
            return False

        return self._player.set_rate(rate) != -1

    def get_playback_rate(self):
        return self._playback_rate

    @log_call
    def set_volume(self, volume, remember=True):
        self._volume = min(100, max(0, int(volume)))

        if remember and self._volume > 0:
            self._last_volume = self._volume

        self._is_muted = self._volume == 0

        if not self._is_released:
            self._player.audio_set_volume(self._volume)

    @log_call
    def toggle_mute(self):
        volume = self._last_volume if self._is_muted else 0
        self.set_volume(volume)
        return self._is_muted

    def get_volume(self):
        return self._volume

    def is_muted(self):
        return self._is_muted

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

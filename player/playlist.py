from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PlaylistItem:
    source: str
    display_name: str


class Playlist:
    def __init__(self):
        self._items = []
        self._current_index = -1

    def add(self, source, display_name):
        item = PlaylistItem(
            source=str(source),
            display_name=str(display_name),
        )
        self._items.append(item)
        return len(self._items) - 1

    def get(self, index):
        if not 0 <= index < len(self._items):
            return None

        return self._items[index]

    def select(self, index):
        item = self.get(index)

        if item is None:
            return None

        self._current_index = index
        return item

    def get_current_index(self):
        return self._current_index

    def get_previous_index(self):
        if self._current_index <= 0:
            return None

        return self._current_index - 1

    def get_next_index(self):
        next_index = self._current_index + 1

        if next_index >= len(self._items):
            return None

        return next_index

    def count(self):
        return len(self._items)

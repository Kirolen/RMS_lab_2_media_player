from pathlib import Path
from urllib.parse import urlparse


SUPPORTED_MEDIA_EXTENSIONS = frozenset(
    {
        ".mp3",
        ".wav",
        ".flac",
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".webm",
    }
)


def get_media_file_filter():
    return (
        "Медіафайли "
        "(*.mp3 *.wav *.flac *.mp4 *.avi *.mkv *.mov *.webm);;"
        "Аудіофайли (*.mp3 *.wav *.flac);;"
        "Відеофайли (*.mp4 *.avi *.mkv *.mov *.webm);;"
        "Усі файли (*)"
    )


def is_supported_media_file(file_path):
    path = Path(file_path)
    return (
        path.is_file()
        and path.suffix.lower() in SUPPORTED_MEDIA_EXTENSIONS
    )


def is_valid_media_url(url):
    parsed_url = urlparse(url)
    return (
        parsed_url.scheme in ("http", "https")
        and bool(parsed_url.netloc)
    )

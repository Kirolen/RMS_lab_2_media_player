from hashlib import sha256
from pathlib import Path
from urllib.parse import urlparse

from PySide6.QtCore import (
    QDir,
    QObject,
    QTemporaryDir,
    QTimer,
    QUrl,
    Signal,
)
from PySide6.QtNetwork import (
    QNetworkAccessManager,
    QNetworkReply,
    QNetworkRequest,
)


class RemoteMediaCache(QObject):
    media_ready = Signal(str, str)
    download_failed = Signal(str, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._directory = QTemporaryDir(
            f"{QDir.tempPath()}/media-player-XXXXXX"
        )
        self._network = QNetworkAccessManager(self)
        self._cached_paths = {}
        self._downloads = {}
        self._pending_urls = set()

        if not self._directory.isValid():
            raise RuntimeError(
                "Не вдалося створити тимчасову папку для медіа"
            )

    def fetch(self, url):
        cached_path = self._cached_paths.get(url)

        if cached_path and Path(cached_path).is_file():
            QTimer.singleShot(
                0,
                lambda: self.media_ready.emit(url, cached_path),
            )
            return

        if url in self._pending_urls:
            return

        request = QNetworkRequest(QUrl(url))
        request.setTransferTimeout(30_000)
        request.setAttribute(
            QNetworkRequest.Attribute.RedirectPolicyAttribute,
            QNetworkRequest.RedirectPolicy.NoLessSafeRedirectPolicy,
        )

        reply = self._network.get(request)
        self._pending_urls.add(url)
        file_path = self._build_file_path(url)
        file_handle = open(file_path, "wb")
        self._downloads[reply] = (url, file_path, file_handle)

        reply.readyRead.connect(
            lambda current_reply=reply: self._write_available(
                current_reply
            )
        )
        reply.finished.connect(
            lambda current_reply=reply: self._finish_download(
                current_reply
            )
        )

    def _build_file_path(self, url):
        suffix = Path(urlparse(url).path).suffix.lower()

        if not suffix or len(suffix) > 10:
            suffix = ".media"

        file_name = f"{sha256(url.encode()).hexdigest()}{suffix}"
        return self._directory.filePath(file_name)

    def _write_available(self, reply):
        download = self._downloads.get(reply)

        if download is None:
            return

        download[2].write(bytes(reply.readAll()))

    def _finish_download(self, reply):
        download = self._downloads.pop(reply, None)

        if download is None:
            reply.deleteLater()
            return

        url, file_path, file_handle = download
        self._pending_urls.discard(url)
        self._write_remaining(reply, file_handle)
        file_handle.close()

        status_code = reply.attribute(
            QNetworkRequest.Attribute.HttpStatusCodeAttribute
        )
        failed = (
            reply.error() != QNetworkReply.NetworkError.NoError
            or (status_code is not None and int(status_code) >= 400)
            or not Path(file_path).is_file()
            or Path(file_path).stat().st_size == 0
        )

        if failed:
            Path(file_path).unlink(missing_ok=True)
            message = reply.errorString()
            self.download_failed.emit(url, message)
        else:
            self._cached_paths[url] = file_path
            self.media_ready.emit(url, file_path)

        reply.deleteLater()

    @staticmethod
    def _write_remaining(reply, file_handle):
        remaining_data = bytes(reply.readAll())

        if remaining_data:
            file_handle.write(remaining_data)

    def release(self):
        downloads = list(self._downloads.items())
        self._downloads.clear()

        for reply, (_, file_path, file_handle) in downloads:
            reply.abort()
            file_handle.close()
            Path(file_path).unlink(missing_ok=True)
            reply.deleteLater()

        self._cached_paths.clear()
        self._pending_urls.clear()
        self._directory.remove()

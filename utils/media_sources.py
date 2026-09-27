from urllib.parse import urlparse


def is_valid_media_url(url):
    parsed_url = urlparse(url)
    return (
        parsed_url.scheme in ("http", "https")
        and bool(parsed_url.netloc)
    )

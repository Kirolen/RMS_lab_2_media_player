import logging
from datetime import datetime
from functools import wraps
from pathlib import Path


def configure_logging(debug_enabled):
    if not debug_enabled:
        logging.disable(logging.CRITICAL)
        return None

    logging.disable(logging.NOTSET)

    logs_directory = Path("logs")
    logs_directory.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime(
        "%Y-%m-%d_%H-%M-%S"
    )
    log_file = logs_directory / (
        f"media_player_{timestamp}.log"
    )

    formatter = logging.Formatter(
        (
            "%(asctime)s | %(levelname)s | "
            "%(name)s | %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(
        log_file,
        encoding="utf-8",
    )
    file_handler.setFormatter(formatter)

    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[console_handler, file_handler],
        force=True,
    )

    logging.getLogger(__name__).debug(
        "Debug logging enabled | file=%s",
        log_file.resolve(),
    )

    return log_file


def log_call(function):
    @wraps(function)
    def wrapper(*args, **kwargs):
        logger = logging.getLogger(function.__module__)

        if not logger.isEnabledFor(logging.DEBUG):
            return function(*args, **kwargs)

        function_name = function.__qualname__
        logged_args = args[1:] if "." in function_name else args

        logger.debug(
            "START %s | args=%r | kwargs=%r",
            function_name,
            logged_args,
            kwargs,
        )

        try:
            result = function(*args, **kwargs)
        except Exception:
            logger.exception("ERROR %s", function_name)
            raise

        logger.debug(
            "END %s | result=%r",
            function_name,
            result,
        )
        return result

    return wrapper

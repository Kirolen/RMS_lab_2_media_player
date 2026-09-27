import logging
import sys

from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from utils.logger import configure_logging


def main():
    debug_enabled = "--debug" in sys.argv
    qt_arguments = [
        argument
        for argument in sys.argv
        if argument != "--debug"
    ]

    configure_logging(debug_enabled)

    logger = logging.getLogger(__name__)
    logger.debug("START main | debug=%s", debug_enabled)

    application = QApplication(qt_arguments)
    window = MainWindow()
    window.show()

    exit_code = application.exec()
    logger.debug("END main | exit_code=%s", exit_code)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())


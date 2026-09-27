from dataclasses import dataclass

from PySide6.QtGui import QAction, QKeySequence


MENU_STYLE = """
QMenuBar {
    background-color: #20242c;
    color: #b8bbc2;
    padding: 3px 6px;
}
QMenuBar::item {
    padding: 5px 10px;
    background: transparent;
}
QMenuBar::item:selected {
    background-color: #343943;
    color: white;
}
QMenu {
    background-color: #20242c;
    color: #e4e5e8;
    border: 1px solid #454b57;
}
QMenu::item {
    padding: 7px 28px;
}
QMenu::item:selected {
    background-color: #3b82f6;
}
"""


@dataclass(frozen=True, slots=True)
class MenuActions:
    open_file: QAction
    open_url: QAction


def setup_menu_bar(window):
    menu_bar = window.menuBar()
    menu_bar.setNativeMenuBar(False)
    menu_bar.setStyleSheet(MENU_STYLE)

    file_menu = menu_bar.addMenu("Файл")
    open_file = QAction("Відкрити медіафайл...", window)
    open_file.setShortcut(QKeySequence("Ctrl+O"))

    open_url = QAction("Відкрити URL...", window)

    file_menu.addAction(open_file)
    file_menu.addAction(open_url)

    return MenuActions(
        open_file=open_file,
        open_url=open_url,
    )

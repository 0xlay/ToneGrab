"""Main entry point for ToneGrab application."""

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from utils.system import get_resource_path


def main():
    """Initialize and run the application."""
    app = QApplication(sys.argv)
    app.setApplicationName("ToneGrab")
    app.setOrganizationName("ToneGrab")
    
    # Set application icon
    icon_path = get_resource_path("assets/icons/icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

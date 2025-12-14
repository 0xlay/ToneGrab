"""Main entry point for ToneGrab application."""

import logging
import sys
from pathlib import Path

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from ui.main_window import MainWindow
from utils.system import get_resource_path


def setup_logging():
    """Setup logging for the application."""
    # Create logs directory in user's home
    if sys.platform == "darwin":
        log_dir = Path.home() / "Library" / "Logs" / "ToneGrab"
    elif sys.platform == "win32":
        log_dir = Path.home() / "AppData" / "Local" / "ToneGrab" / "Logs"
    else:
        log_dir = Path.home() / ".local" / "share" / "ToneGrab" / "logs"
    
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "tonegrab.log"
    
    # Configure logging
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, mode='a', encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logging.info("=" * 60)
    logging.info("ToneGrab started")
    logging.info(f"Log file: {log_file}")
    logging.info(f"Platform: {sys.platform}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        logging.info(f"sys._MEIPASS: {sys._MEIPASS}")
    logging.info("=" * 60)


def main():
    """Initialize and run the application."""
    setup_logging()
    
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

"""Main entry point for ToneGrab application."""

import logging
import sys
from pathlib import Path

from PySide6.QtCore import QTimer, Qt
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
    
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # If can't create in standard location, try home directory
        log_dir = Path.home()
        print(f"Warning: Could not create log directory, using {log_dir}: {e}")
    
    log_file = log_dir / "tonegrab.log"
    
    # Remove any existing handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create file handler with immediate flush
    file_handler = logging.FileHandler(log_file, mode='a', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    
    # Configure root logger
    logging.root.setLevel(logging.DEBUG)
    logging.root.addHandler(file_handler)
    
    # Only add stream handler if not frozen (avoid issues with GUI apps)
    if not getattr(sys, 'frozen', False):
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.DEBUG)
        stream_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        logging.root.addHandler(stream_handler)
    
    # Force immediate write
    logging.info("=" * 60)
    logging.info("ToneGrab started")
    logging.info(f"Log file: {log_file}")
    logging.info(f"Platform: {sys.platform}")
    logging.info(f"Python version: {sys.version}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
    if getattr(sys, 'frozen', False):
        logging.info(f"sys._MEIPASS: {sys._MEIPASS}")
        logging.info(f"sys.executable: {sys.executable}")
    logging.info("=" * 60)
    
    # Flush immediately
    for handler in logging.root.handlers:
        handler.flush()



def main():
    """Initialize and run the application."""
    setup_logging()
    
    # Enable hardware acceleration for faster rendering
    QApplication.setAttribute(Qt.AA_ShareOpenGLContexts, True)
    
    app = QApplication(sys.argv)
    
    app.setApplicationName("ToneGrab")
    app.setOrganizationName("ToneGrab")
    
    # Set application icon
    icon_path = get_resource_path("assets/icons/icon.ico")
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    
    # Force Qt to process events to display window faster
    app.processEvents()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()

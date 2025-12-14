"""Main window for ToneGrab application."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from core.config import AppConfig
from ui.download_worker import DownloadWorker
from utils.helpers import is_valid_url
from utils.system import check_ffmpeg, get_resource_path


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self):
        """Initialize the main window."""
        super().__init__()
        
        self.setWindowTitle("ToneGrab - Audio Downloader")
        self.setMinimumSize(900, 700)
        
        # Set window icon
        icon_path = get_resource_path("assets/icons/icon.ico")
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        # Load configuration
        self.config = AppConfig.load()

        # Download workers list (support multiple simultaneous downloads)
        self.download_workers = []
        self.download_id_counter = 0

        self._setup_ui()
        self._apply_styles()
        self._check_dependencies()

    def _check_dependencies(self):
        """Check system dependencies and warn if missing."""
        ffmpeg_available, ffmpeg_info = check_ffmpeg()
        
        if not ffmpeg_available:
            # Get log file location for debugging
            if sys.platform == "darwin":
                log_file = Path.home() / "Library" / "Logs" / "ToneGrab" / "tonegrab.log"
            elif sys.platform == "win32":
                log_file = Path.home() / "AppData" / "Local" / "ToneGrab" / "Logs" / "tonegrab.log"
            else:
                log_file = Path.home() / ".local" / "share" / "ToneGrab" / "logs" / "tonegrab.log"
            
            if not log_file.exists():
                log_file = Path.home() / "tonegrab.log"
            
            msg = (
                "⚠️ FFmpeg not detected!\n\n"
                "FFmpeg is required to convert audio files.\n"
                f"Error: {ffmpeg_info}\n\n"
                "The app will work for downloading, but conversion may fail.\n\n"
                f"For debugging, check log file:\n{log_file}\n\n"
                "Installation instructions:\n"
                "• Windows: Download from https://ffmpeg.org/download.html\n"
                "• macOS: Run 'brew install ffmpeg' in Terminal\n"
                "• Linux: Run 'sudo apt install ffmpeg'\n\n"
                "Do you want to continue anyway?"
            )
            
            reply = QMessageBox.warning(
                self,
                "FFmpeg Not Found",
                msg,
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes
            )
            
            if reply == QMessageBox.StandardButton.No:
                self.close()
            else:
                self._log_message(f"⚠️ Warning: FFmpeg not found - {ffmpeg_info}")
        else:
            self._log_message(f"✅ FFmpeg detected: {ffmpeg_info}")

    def _setup_ui(self):
        """Set up the user interface."""
        # Disable updates during UI construction for faster initialization
        self.setUpdatesEnabled(False)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Title
        title_label = QLabel("🎵 ToneGrab")
        title_label.setStyleSheet(
            "font-size: 32px; font-weight: bold; color: #14a085; margin-bottom: 10px;"
        )
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title_label)

        subtitle_label = QLabel("Download audio from YouTube, SoundCloud, and more")
        subtitle_label.setStyleSheet("font-size: 14px; color: #888; margin-bottom: 20px;")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(subtitle_label)

        # URL Input Section
        url_label = QLabel("Video/Audio URL:")
        url_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        main_layout.addWidget(url_label)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText(
            "Paste URL here (e.g., https://www.youtube.com/watch?v=... or playlist URL)"
        )
        self.url_input.setMinimumHeight(40)
        self.url_input.textChanged.connect(self._on_url_changed)
        main_layout.addWidget(self.url_input)
        
        # Playlist info label
        self.playlist_info_label = QLabel("")
        self.playlist_info_label.setStyleSheet("font-size: 12px; color: #14a085; margin-top: 5px;")
        self.playlist_info_label.setVisible(False)
        main_layout.addWidget(self.playlist_info_label)

        # Format and Quality Section
        settings_layout = QHBoxLayout()

        # Audio Format
        format_layout = QVBoxLayout()
        format_label = QLabel("Audio Format:")
        format_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        format_layout.addWidget(format_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP3", "FLAC", "WAV", "M4A", "OPUS"])
        self.format_combo.setCurrentText(self.config.audio_format.upper())
        self.format_combo.setMinimumHeight(35)
        format_layout.addWidget(self.format_combo)
        settings_layout.addLayout(format_layout)

        # Audio Quality
        quality_layout = QVBoxLayout()
        quality_label = QLabel("Quality (bitrate):")
        quality_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        quality_layout.addWidget(quality_label)

        self.quality_combo = QComboBox()
        self.quality_combo.addItems(["128 kbps", "192 kbps", "256 kbps", "320 kbps"])
        self.quality_combo.setCurrentText(f"{self.config.audio_quality} kbps")
        self.quality_combo.setMinimumHeight(35)
        quality_layout.addWidget(self.quality_combo)
        settings_layout.addLayout(quality_layout)

        main_layout.addLayout(settings_layout)

        # Output Directory Section
        output_layout = QHBoxLayout()
        output_label = QLabel("Save to:")
        output_label.setStyleSheet("font-size: 12px; font-weight: bold;")
        output_layout.addWidget(output_label)

        self.output_path_label = QLineEdit()
        self.output_path_label.setText(self.config.output_directory)
        self.output_path_label.setReadOnly(True)
        self.output_path_label.setMinimumHeight(35)
        output_layout.addWidget(self.output_path_label)

        self.browse_button = QPushButton("Browse...")
        self.browse_button.setMinimumHeight(35)
        self.browse_button.setMaximumWidth(100)
        self.browse_button.clicked.connect(self._browse_output_directory)
        output_layout.addWidget(self.browse_button)

        main_layout.addLayout(output_layout)

        # Download Button
        self.download_button = QPushButton("⬇ Add to Queue")
        self.download_button.setMinimumHeight(50)
        self.download_button.setStyleSheet(
            """
            QPushButton {
                background-color: #14a085;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #0d7377;
            }
            QPushButton:pressed {
                background-color: #0a5f62;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """
        )
        self.download_button.clicked.connect(self._start_download)
        main_layout.addWidget(self.download_button)

        # Active Downloads Section
        downloads_label = QLabel("Active Downloads:")
        downloads_label.setStyleSheet("font-size: 14px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(downloads_label)
        
        # Scrollable container for download items
        self.downloads_scroll = QScrollArea()
        self.downloads_scroll.setWidgetResizable(True)
        self.downloads_scroll.setMaximumHeight(300)
        self.downloads_scroll.setMinimumHeight(150)
        
        self.downloads_container = QWidget()
        self.downloads_layout = QVBoxLayout(self.downloads_container)
        self.downloads_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.downloads_layout.setSpacing(5)
        self.downloads_scroll.setWidget(self.downloads_container)
        main_layout.addWidget(self.downloads_scroll)

        # Status/Log Area
        log_label = QLabel("Download Log:")
        log_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(120)
        self.log_text.setMaximumHeight(16777215)  # Allow unlimited expansion
        self.log_text.setPlaceholderText("Download status will appear here...")
        main_layout.addWidget(self.log_text, 1)  # stretch factor = 1 (растягивается)
        
        # Add a small spacer at bottom to prevent log from touching window edge
        main_layout.addStretch(0)  # No stretch, just maintains spacing
        
        # Re-enable updates after UI is fully constructed
        self.setUpdatesEnabled(True)

    def _apply_styles(self):
        """Apply global styles to the window."""
        self.setStyleSheet(
            """
            QMainWindow {
                background-color: #1e1e1e;
            }
            QWidget {
                background-color: #1e1e1e;
                color: #e0e0e0;
            }
            QLabel {
                color: #e0e0e0;
            }
            QLineEdit, QComboBox, QTextEdit {
                background-color: #2d2d2d;
                color: #e0e0e0;
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                padding: 5px;
            }
            QLineEdit:focus, QComboBox:focus {
                border: 2px solid #14a085;
            }
            QPushButton {
                background-color: #3d3d3d;
                color: #e0e0e0;
                border: none;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #4d4d4d;
            }
            QPushButton:pressed {
                background-color: #2d2d2d;
            }
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                background-color: #2d2d2d;
            }
            QProgressBar::chunk {
                background-color: #14a085;
                border-radius: 3px;
            }
        """
        )

    def _on_url_changed(self, text: str):
        """Handle URL input changes to detect playlists."""
        # Simple check for playlist indicators in URL
        if text and ('playlist' in text.lower() or 'list=' in text.lower() or '/sets/' in text.lower()):
            self.playlist_info_label.setText("🎵 Playlist detected! All tracks will be downloaded.")
            self.playlist_info_label.setVisible(True)
        else:
            self.playlist_info_label.setVisible(False)
    
    def _browse_output_directory(self):
        """Open directory browser for output path selection."""
        directory = QFileDialog.getExistingDirectory(
            self, "Select Output Directory", self.config.output_directory
        )
        if directory:
            self.output_path_label.setText(directory)
            self.config.output_directory = directory
            self.config.save()
            self._log_message(f"Output directory changed to: {directory}")

    def _start_download(self):
        """Add download to queue and start it."""
        url = self.url_input.text().strip()

        # Validation
        if not url:
            self._show_error("Please enter a URL")
            return

        if not is_valid_url(url):
            self._show_error("Please enter a valid URL (must start with http:// or https://)")
            return

        # Get selected format and quality
        audio_format = self.format_combo.currentText().lower()
        quality = self.quality_combo.currentText().split()[0]  # Extract number from "192 kbps"
        output_dir = self.output_path_label.text()
        
        # Generate unique download ID
        download_id = self.download_id_counter
        self.download_id_counter += 1

        self._log_message(f"📥 Added to queue #{download_id + 1}: {url}")
        self._log_message(f"📁 Format: {audio_format.upper()}, Quality: {quality} kbps")

        # Create download item widget
        download_widget = self._create_download_widget(download_id, url, audio_format, quality)
        self.downloads_layout.addWidget(download_widget)

        # Create and start worker thread
        worker = DownloadWorker(
            url=url,
            output_dir=output_dir,
            audio_format=audio_format,
            quality=quality,
        )
        
        # Store worker with its ID and widget
        worker_data = {
            'id': download_id,
            'worker': worker,
            'widget': download_widget,
            'url': url
        }
        self.download_workers.append(worker_data)

        # Connect signals with download ID
        worker.progress.connect(lambda p, d, wd=worker_data: self._update_download_progress(wd, p, d))
        worker.status.connect(self._log_message)
        worker.finished.connect(lambda fp, wd=worker_data: self._download_finished(wd, fp))
        worker.error.connect(lambda msg, wd=worker_data: self._download_error(wd, msg))
        worker.playlist_item.connect(lambda c, t, title, wd=worker_data: self._update_playlist_progress(wd, c, t, title))

        # Start download
        worker.start()
        
        # Clear URL input for next download
        self.url_input.clear()

    def _create_download_widget(self, download_id: int, url: str, audio_format: str, quality: str) -> QWidget:
        """Create a widget for displaying download progress."""
        container = QFrame()
        container.setObjectName(f"download_{download_id}")
        container.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Raised)
        container.setStyleSheet("""
            QFrame {
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
        layout = QVBoxLayout(container)
        layout.setSpacing(5)
        
        # Title and URL
        title_label = QLabel(f"#{download_id + 1}: {url[:60]}...")
        title_label.setStyleSheet("font-weight: bold; color: #14a085;")
        layout.addWidget(title_label)
        
        # Format and quality info
        info_label = QLabel(f"Format: {audio_format.upper()} | Quality: {quality} kbps")
        info_label.setStyleSheet("font-size: 11px; color: #888;")
        layout.addWidget(info_label)
        
        # Progress bar
        progress_bar = QProgressBar()
        progress_bar.setObjectName(f"progress_{download_id}")
        progress_bar.setMaximum(100)
        progress_bar.setValue(0)
        progress_bar.setTextVisible(True)
        progress_bar.setFormat("%p% - Initializing...")
        layout.addWidget(progress_bar)
        
        # Buttons row
        buttons_layout = QHBoxLayout()
        
        # Status label
        status_label = QLabel("⏳ Starting...")
        status_label.setObjectName(f"status_{download_id}")
        status_label.setStyleSheet("color: #e0e0e0;")
        buttons_layout.addWidget(status_label)
        
        buttons_layout.addStretch()
        
        # Cancel button
        cancel_btn = QPushButton("❌ Cancel")
        cancel_btn.setObjectName(f"cancel_{download_id}")
        cancel_btn.setMaximumWidth(80)
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-size: 11px;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #a93226;
            }
        """)
        cancel_btn.clicked.connect(lambda: self._cancel_download(download_id))
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        return container

    def _update_download_progress(self, worker_data: dict, progress: int, description: str):
        """Update progress for a specific download."""
        download_id = worker_data['id']
        widget = worker_data['widget']
        
        # Update progress bar
        progress_bar = widget.findChild(QProgressBar, f"progress_{download_id}")
        if progress_bar:
            progress_bar.setValue(progress)
            progress_bar.setFormat(f"%p% - {description}")
        
        # Update status label
        status_label = widget.findChild(QLabel, f"status_{download_id}")
        if status_label:
            if progress >= 100:
                status_label.setText("✅ Completed")
                status_label.setStyleSheet("color: #14a085;")
            else:
                status_label.setText(f"⏳ {description}")

    def _update_playlist_progress(self, worker_data: dict, current: int, total: int, title: str):
        """Update progress for playlist downloads."""
        download_id = worker_data['id']
        status_label = worker_data['widget'].findChild(QLabel, f"status_{download_id}")
        if status_label:
            status_label.setText(f"📼 Playlist: {current}/{total}")

    def _log_message(self, message: str):
        """Add a message to the log area."""
        self.log_text.append(message)

    def _download_finished(self, worker_data: dict, file_path: str = ""):
        """Handle successful download completion."""
        download_id = worker_data['id']
        widget = worker_data['widget']
        
        self._log_message(f"🎉 Download #{download_id + 1} completed!")
        if file_path:
            self._log_message(f"📁 Saved to: {file_path}")
        
        # Update widget status
        status_label = widget.findChild(QLabel, f"status_{download_id}")
        if status_label:
            status_label.setText("✅ Completed")
            status_label.setStyleSheet("color: #14a085; font-weight: bold;")
        
        # Hide cancel button
        cancel_btn = widget.findChild(QPushButton, f"cancel_{download_id}")
        if cancel_btn:
            cancel_btn.setVisible(False)
        
        # Remove from active workers list
        self.download_workers = [w for w in self.download_workers if w['id'] != download_id]

    def _download_error(self, worker_data: dict, error_message: str):
        """Handle download error."""
        download_id = worker_data['id']
        widget = worker_data['widget']
        
        self._log_message(f"❌ Download #{download_id + 1} failed: {error_message}")
        
        # Update widget status
        status_label = widget.findChild(QLabel, f"status_{download_id}")
        if status_label:
            status_label.setText("❌ Failed")
            status_label.setStyleSheet("color: #c0392b; font-weight: bold;")
        
        # Update progress bar
        progress_bar = widget.findChild(QProgressBar, f"progress_{download_id}")
        if progress_bar:
            progress_bar.setFormat("Failed!")
        
        # Hide cancel button
        cancel_btn = widget.findChild(QPushButton, f"cancel_{download_id}")
        if cancel_btn:
            cancel_btn.setVisible(False)
        
        # Remove from active workers list
        self.download_workers = [w for w in self.download_workers if w['id'] != download_id]

    def _cancel_download(self, download_id: int):
        """Cancel a specific download."""
        # Find worker by ID
        worker_data = next((w for w in self.download_workers if w['id'] == download_id), None)
        if not worker_data:
            return
        
        worker = worker_data['worker']
        widget = worker_data['widget']
        
        if worker.isRunning():
            self._log_message(f"🛑 Cancelling download #{download_id + 1}...")
            worker.stop()
            worker.wait(3000)  # Wait up to 3 seconds
            
            if worker.isRunning():
                worker.terminate()  # Force terminate if needed
                self._log_message(f"⚠️ Download #{download_id + 1} force terminated")
            
            # Update widget status
            status_label = widget.findChild(QLabel, f"status_{download_id}")
            if status_label:
                status_label.setText("❌ Cancelled")
                status_label.setStyleSheet("color: #888;")
            
            # Hide cancel button
            cancel_btn = widget.findChild(QPushButton, f"cancel_{download_id}")
            if cancel_btn:
                cancel_btn.setVisible(False)
            
            self._log_message(f"❌ Download #{download_id + 1} cancelled by user")
            
            # Remove from active workers list
            self.download_workers = [w for w in self.download_workers if w['id'] != download_id]


    def _show_error(self, message: str):
        """Show error message box."""
        QMessageBox.warning(self, "Error", message)

"""Main window for ToneGrab application."""

import sys
from pathlib import Path

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
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

        # Download worker
        self.download_worker = None
        
        # Progress bar animation
        self.progress_animation = None

        self._setup_ui()
        self._apply_styles()
        self._check_dependencies()

    def _check_dependencies(self):
        """Check system dependencies and warn if missing."""
        import logging
        from pathlib import Path
        
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

        # Buttons Layout (Download and Cancel)
        buttons_layout = QHBoxLayout()
        
        # Download Button
        self.download_button = QPushButton("⬇ Download Audio")
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
        buttons_layout.addWidget(self.download_button)
        
        # Cancel Button
        self.cancel_button = QPushButton("⏹ Cancel")
        self.cancel_button.setMinimumHeight(50)
        self.cancel_button.setMaximumWidth(150)
        self.cancel_button.setStyleSheet(
            """
            QPushButton {
                background-color: #c0392b;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #a93226;
            }
            QPushButton:pressed {
                background-color: #922b21;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #999;
            }
        """
        )
        self.cancel_button.clicked.connect(self._cancel_download)
        self.cancel_button.setEnabled(False)  # Disabled by default
        self.cancel_button.setVisible(False)  # Hidden by default
        buttons_layout.addWidget(self.cancel_button)
        
        main_layout.addLayout(buttons_layout)

        # Progress Bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimumHeight(25)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)

        # Status/Log Area
        log_label = QLabel("Download Log:")
        log_label.setStyleSheet("font-size: 12px; font-weight: bold; margin-top: 10px;")
        main_layout.addWidget(log_label)

        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMinimumHeight(200)
        self.log_text.setMaximumHeight(16777215)  # Allow unlimited expansion
        self.log_text.setPlaceholderText("Download status will appear here...")
        main_layout.addWidget(self.log_text, 1)  # stretch factor = 1 (растягивается)
        
        # Add a small spacer at bottom to prevent log from touching window edge
        main_layout.addStretch(0)  # No stretch, just maintains spacing

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
        """Start the download process."""
        url = self.url_input.text().strip()

        # Validation
        if not url:
            self._show_error("Please enter a URL")
            return

        if not is_valid_url(url):
            self._show_error("Please enter a valid URL (must start with http:// or https://)")
            return

        # Check if download is already in progress
        if self.download_worker and self.download_worker.isRunning():
            self._show_error("Download is already in progress")
            return

        # Get selected format and quality
        audio_format = self.format_combo.currentText().lower()
        quality = self.quality_combo.currentText().split()[0]  # Extract number from "192 kbps"
        output_dir = self.output_path_label.text()

        # Clear log and reset progress
        self.log_text.clear()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(True)

        self._log_message(f"🔍 Preparing to download from: {url}")
        self._log_message(f"📁 Format: {audio_format.upper()}, Quality: {quality} kbps")
        self._log_message(f"💾 Saving to: {output_dir}")

        # Update buttons state
        self.download_button.setEnabled(False)
        self.download_button.setText("⏳ Downloading...")
        self.cancel_button.setEnabled(True)
        self.cancel_button.setVisible(True)

        # Create and start worker thread
        self.download_worker = DownloadWorker(
            url=url,
            output_dir=output_dir,
            audio_format=audio_format,
            quality=quality,
        )

        # Connect signals
        self.download_worker.progress.connect(self._update_progress)
        self.download_worker.status.connect(self._log_message)
        self.download_worker.finished.connect(self._download_finished)
        self.download_worker.error.connect(self._download_error)
        self.download_worker.playlist_item.connect(self._update_playlist_progress)

        # Start download
        self.download_worker.start()

    def _update_playlist_progress(self, current: int, total: int, title: str):
        """Update progress for playlist downloads."""
        # Update progress bar to show playlist progress
        playlist_percent = int((current / total) * 100)
        self.progress_bar.setValue(playlist_percent)
        
        # Update button text
        self.download_button.setText(f"⏳ Downloading {current}/{total}...")

    def _log_message(self, message: str):
        """Add a message to the log area."""
        self.log_text.append(message)

    def _update_progress(self, value: int):
        """Update the progress bar with smooth animation."""
        # Cancel any existing animation
        if self.progress_animation and self.progress_animation.state() == QPropertyAnimation.State.Running:
            self.progress_animation.stop()
        
        # Don't animate if the change is small or backwards
        current_value = self.progress_bar.value()
        if value <= current_value or abs(value - current_value) < 2:
            self.progress_bar.setValue(value)
            return
        
        # Create smooth animation
        self.progress_animation = QPropertyAnimation(self.progress_bar, b"value")
        self.progress_animation.setDuration(200)  # 200ms animation
        self.progress_animation.setStartValue(current_value)
        self.progress_animation.setEndValue(value)
        self.progress_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.progress_animation.start()


    def _download_finished(self, file_path: str):
        """Handle successful download completion."""
        self._log_message(f"🎉 Success! File saved to: {file_path}")
        self._log_message("=" * 60)

        # Re-enable download button and hide cancel
        self.download_button.setEnabled(True)
        self.download_button.setText("⬇ Download Audio")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)

        # Show success message
        QMessageBox.information(
            self,
            "Download Complete",
            f"Audio downloaded successfully!\n\nSaved to:\n{file_path}",
        )

    def _download_error(self, error_message: str):
        """Handle download error."""
        self._log_message(f"❌ Error: {error_message}")
        self._log_message("=" * 60)

        # Re-enable download button and hide cancel
        self.download_button.setEnabled(True)
        self.download_button.setText("⬇ Download Audio")
        self.cancel_button.setEnabled(False)
        self.cancel_button.setVisible(False)
        self.progress_bar.setVisible(False)

        # Show error message
        self._show_error(f"Download failed:\n{error_message}")

    def _cancel_download(self):
        """Cancel the current download."""
        if self.download_worker and self.download_worker.isRunning():
            self._log_message("🛑 Cancelling download...")
            self.download_worker.stop()
            self.download_worker.wait(3000)  # Wait up to 3 seconds
            
            if self.download_worker.isRunning():
                self.download_worker.terminate()  # Force terminate if needed
                self._log_message("⚠️ Download force terminated")
            
            # Reset UI
            self.download_button.setEnabled(True)
            self.download_button.setText("⬇ Download Audio")
            self.cancel_button.setEnabled(False)
            self.cancel_button.setVisible(False)
            self.progress_bar.setVisible(False)
            self._log_message("❌ Download cancelled by user")

    def _show_error(self, message: str):
        """Show error message box."""
        QMessageBox.warning(self, "Error", message)

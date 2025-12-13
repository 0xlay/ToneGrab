"""Worker thread for downloading audio."""

import re
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from core.downloader import AudioDownloader


class DownloadWorker(QThread):
    """Worker thread for downloading audio without blocking the UI."""

    # Signals
    progress = Signal(int)  # Progress percentage (0-100)
    status = Signal(str)  # Status message
    finished = Signal(str)  # Finished with file path
    error = Signal(str)  # Error message

    def __init__(
        self,
        url: str,
        output_dir: str,
        audio_format: str,
        quality: str,
    ):
        """
        Initialize the download worker.

        Args:
            url: URL to download from
            output_dir: Directory to save the file
            audio_format: Audio format (mp3, flac, etc.)
            quality: Audio quality/bitrate
        """
        super().__init__()
        self.url = url
        self.output_dir = Path(output_dir)
        self.audio_format = audio_format
        self.quality = quality
        self.downloader = AudioDownloader(self.output_dir)

    def run(self):
        """Run the download process."""
        try:
            self.status.emit("🔍 Fetching video information...")

            # Get video info first
            info = self.downloader.get_video_info(self.url)
            if not info:
                self.error.emit("Failed to fetch video information")
                return

            title = info.get("title", "Unknown")
            duration = info.get("duration", 0)
            uploader = info.get("uploader", "Unknown")

            self.status.emit(f"📹 Title: {title}")
            self.status.emit(f"👤 Uploader: {uploader}")
            
            # Format duration if available
            if duration:
                self.status.emit(
                    f"⏱ Duration: {self._format_duration(duration)}"
                )
            self.status.emit("⬇ Starting download...")

            # Download with progress callback
            result = self.downloader.download(
                url=self.url,
                audio_format=self.audio_format,
                quality=self.quality,
                progress_callback=self._progress_hook,
            )

            if result:
                self.status.emit(f"✅ Download completed: {Path(result).name}")
                self.finished.emit(result)
            else:
                self.error.emit("Download failed")

        except Exception as e:
            import traceback
            error_msg = str(e)
            
            # Check for common errors and provide helpful messages
            if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
                self.error.emit(
                    "FFmpeg is not installed or not found in PATH.\n\n"
                    "Please install FFmpeg:\n"
                    "• Windows: Download from https://ffmpeg.org/download.html\n"
                    "• macOS: Run 'brew install ffmpeg'\n"
                    "• Linux: Run 'sudo apt install ffmpeg'\n\n"
                    f"Original error: {error_msg}"
                )
            else:
                error_details = traceback.format_exc()
                self.error.emit(f"{error_msg}\n\nDetails:\n{error_details}")

    def _progress_hook(self, d: dict):
        """
        Hook for yt-dlp progress updates.

        Args:
            d: Progress dictionary from yt-dlp
        """
        if d["status"] == "downloading":
            # Extract progress percentage - try multiple methods
            percent = 0
            
            # Method 1: Use _percent_str
            percent_str = d.get("_percent_str", "")
            if percent_str:
                try:
                    percent = float(self._strip_ansi(percent_str).strip().replace("%", ""))
                except (ValueError, AttributeError):
                    pass
            
            # Method 2: Calculate from bytes if available
            if percent == 0:
                downloaded = d.get("downloaded_bytes", 0)
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                if total > 0:
                    percent = (downloaded / total) * 100
            
            # Method 3: Use fragment info if available
            if percent == 0:
                fragment_index = d.get("fragment_index", 0)
                fragment_count = d.get("fragment_count", 0)
                if fragment_count > 0:
                    percent = (fragment_index / fragment_count) * 100
            
            # Emit progress
            if percent > 0:
                self.progress.emit(int(percent))

            # Build status message with download info
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            speed_bytes = d.get("speed", 0)
            speed_str = d.get("_speed_str", "")
            eta_str = d.get("_eta_str", "")
            
            # Calculate ETA if we have all necessary data
            eta_display = None
            if speed_bytes and speed_bytes > 0 and total > 0 and downloaded > 0:
                remaining_bytes = total - downloaded
                eta_seconds = remaining_bytes / speed_bytes
                # Only show ETA if it's more than 1 second
                if eta_seconds > 1:
                    eta_display = self._format_eta(eta_seconds)
                elif eta_seconds > 0:
                    eta_display = "< 1s"
            
            # Build status message
            status_msg = "⬇ Downloading..."
            
            # Add size info if available
            if downloaded > 0:
                downloaded_mb = downloaded / (1024 * 1024)
                if total > 0:
                    total_mb = total / (1024 * 1024)
                    status_msg += f" {downloaded_mb:.1f}MB / {total_mb:.1f}MB"
                else:
                    status_msg += f" {downloaded_mb:.1f}MB"
            
            # Add speed
            if speed_str:
                speed_clean = self._strip_ansi(speed_str)
                status_msg += f" | Speed: {speed_clean}"
            
            # Add ETA
            if eta_display:
                status_msg += f" | ETA: {eta_display}"
            
            self.status.emit(status_msg)

        elif d["status"] == "finished":
            self.status.emit("🔄 Processing audio...")
            self.progress.emit(100)

    @staticmethod
    def _strip_ansi(text: str) -> str:
        """
        Remove ANSI escape codes from text.

        Args:
            text: Text with potential ANSI codes

        Returns:
            Clean text without ANSI codes
        """
        # Pattern to match ANSI escape codes
        ansi_pattern = re.compile(r'\x1b\[[0-9;]*m')
        return ansi_pattern.sub('', text)

    @staticmethod
    def _format_duration(seconds: float | int | None) -> str:
        """
        Format duration in HH:MM:SS or MM:SS format.

        Args:
            seconds: Duration in seconds (can be float, int, or None)

        Returns:
            Formatted duration string
        """
        if seconds is None:
            return "Unknown"
        
        # Convert to int (round if float)
        total_seconds = int(round(seconds))
        
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        secs = total_seconds % 60

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"

    @staticmethod
    def _format_eta(seconds: float) -> str:
        """
        Format ETA in human-readable format.

        Args:
            seconds: ETA in seconds

        Returns:
            Formatted ETA string
        """
        if seconds <= 0:
            return "0s"
        
        total_seconds = int(round(seconds))
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        
        minutes = total_seconds // 60
        secs = total_seconds % 60
        
        if minutes < 60:
            return f"{minutes:02d}:{secs:02d}"
        
        hours = minutes // 60
        minutes = minutes % 60
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"

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
    playlist_item = Signal(int, int, str)  # Current item, total items, title

    def __init__(
        self,
        url: str,
        output_dir: str,
        audio_format: str,
        quality: str,
        download_playlist: bool = False,
    ):
        """
        Initialize the download worker.

        Args:
            url: URL to download from
            output_dir: Directory to save the file
            audio_format: Audio format (mp3, flac, etc.)
            quality: Audio quality/bitrate
            download_playlist: Whether to download entire playlist
        """
        super().__init__()
        self.url = url
        self.output_dir = Path(output_dir)
        self.audio_format = audio_format
        self.quality = quality
        self.download_playlist = download_playlist
        self.downloader = AudioDownloader(self.output_dir)
        self._stop_requested = False
        
        # Progress smoothing
        self._last_progress = 0
        self._last_progress_time = 0
        self._progress_update_interval = 0.1  # Update every 100ms
        self._last_status_time = 0
        self._status_update_interval = 0.5  # Update status text every 500ms (less frequent)

    def stop(self):
        """Request the worker to stop downloading."""
        self._stop_requested = True
        self.status.emit("🛑 Stopping download...")

    def run(self):
        """Run the download process."""
        try:
            self.status.emit("🔍 Checking URL type...")

            # Check if URL is a playlist
            is_playlist = self.downloader.is_playlist(self.url)
            
            if is_playlist:
                self._download_playlist()
            else:
                self._download_single()

        except Exception as e:
            import traceback
            error_msg = str(e)
            
            # Ignore cancellation errors - already handled
            if "cancelled by user" in error_msg.lower() or self._stop_requested:
                return
            
            # Check for common errors and provide helpful messages
            if "ffmpeg" in error_msg.lower() or "ffprobe" in error_msg.lower():
                self.error.emit(
                    "FFmpeg is not installed or not found in PATH.\\n\\n"
                    "Please install FFmpeg:\\n"
                    "• Windows: Download from https://ffmpeg.org/download.html\\n"
                    "• macOS: Run 'brew install ffmpeg'\\n"
                    "• Linux: Run 'sudo apt install ffmpeg'\\n\\n"
                    f"Original error: {error_msg}"
                )
            else:
                # Clean up the error message
                if "Download failed:" in error_msg and error_msg.count("Download failed:") > 1:
                    # Remove duplicate "Download failed:" prefix
                    parts = error_msg.split("Download failed:")
                    error_msg = "Download failed:" + parts[-1]
                
                error_details = traceback.format_exc()
                self.error.emit(f"{error_msg}\\n\\nDetails:\\n{error_details}")

    def _download_single(self):
        """Download a single video/audio."""
        if self._stop_requested:
            self.error.emit("Download cancelled by user")
            return
            
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
        
        if self._stop_requested:
            self.error.emit("Download cancelled by user")
            return
            
        self.status.emit("⬇ Starting download...")

        # Download with progress callback - with retry for transient errors
        max_retries = 2
        retry_count = 0
        result = None
        
        while retry_count <= max_retries:
            result = self.downloader.download(
                url=self.url,
                audio_format=self.audio_format,
                quality=self.quality,
                progress_callback=self._progress_hook,
            )
            
            # Check if we should retry
            if not result.success and result.error_message:
                error_lower = result.error_message.lower()
                # Retry for transient ffprobe errors
                if ("unable to obtain file audio codec" in error_lower or 
                    "ffprobe" in error_lower) and retry_count < max_retries:
                    retry_count += 1
                    self.status.emit(f"⚠️ Temporary error detected. Retrying... (attempt {retry_count + 1}/{max_retries + 1})")
                    continue
            
            # Success or non-retryable error
            break

        if result and result.success and result.file_path:
            self.status.emit(f"✅ Download completed: {Path(result.file_path).name}")
            self.finished.emit(result.file_path)
        else:
            self.error.emit(result.error_message if result else "Download failed")

    def _download_playlist(self):
        """Download entire playlist."""
        if self._stop_requested:
            self.error.emit("Download cancelled by user")
            return
            
        self.status.emit("🎵 Detected playlist! Fetching playlist information...")

        # Get playlist info
        info = self.downloader.get_video_info(self.url)
        if not info:
            self.error.emit("Failed to fetch playlist information")
            return

        playlist_title = info.get("title", "Unknown Playlist")
        playlist_uploader = info.get("uploader", "Unknown")
        entries = info.get("entries", [])
        total_items = len(entries)

        self.status.emit(f"📋 Playlist: {playlist_title}")
        self.status.emit(f"👤 Uploader: {playlist_uploader}")
        self.status.emit(f"📊 Total tracks: {total_items}")
        self.status.emit("=" * 60)

        # Download all items
        try:
            results = self.downloader.download_playlist(
                url=self.url,
                audio_format=self.audio_format,
                quality=self.quality,
                progress_callback=self._progress_hook,
                item_callback=self._playlist_item_callback,
            )
        except Exception as e:
            # Handle cancellation or other errors
            if "cancelled" in str(e).lower() or self._stop_requested:
                self.status.emit("🛑 Playlist download cancelled")
                self.error.emit("Playlist download cancelled by user")
                return
            else:
                self.error.emit(f"Playlist download failed: {str(e)}")
                return
        
        # Check if cancelled after download
        if self._stop_requested:
            self.status.emit("🛑 Playlist download cancelled")
            self.error.emit("Playlist download cancelled by user")
            return

        # Summary
        successful = sum(1 for r in results if r.success)
        failed = len(results) - successful

        self.status.emit("=" * 60)
        self.status.emit(f"🎉 Playlist download complete!")
        self.status.emit(f"✅ Successful: {successful}/{total_items}")
        
        if failed > 0:
            self.status.emit(f"❌ Failed: {failed}/{total_items}")
        
        # Consider it complete if at least one track was downloaded
        if successful > 0:
            self.finished.emit(f"Downloaded {successful} tracks to {self.output_dir}")
        else:
            self.error.emit(f"Failed to download any tracks from playlist")

    def _smooth_progress_update(self, new_progress: int):
        """Update progress with smoothing and rate limiting."""
        import time
        
        current_time = time.time()
        time_diff = current_time - self._last_progress_time
        
        # Skip update if too soon and progress hasn't changed much
        if time_diff < self._progress_update_interval:
            progress_diff = abs(new_progress - self._last_progress)
            if progress_diff < 5:  # Skip if less than 5% change
                return
        
        # Apply smoothing for small changes
        if self._last_progress > 0:
            progress_diff = abs(new_progress - self._last_progress)
            
            # If jump is too large (>20%), smooth it
            if progress_diff > 20:
                # Take average of last and new
                smoothed = int((self._last_progress + new_progress) / 2)
                new_progress = smoothed
        
        # Ensure progress only increases (never goes backward)
        if new_progress >= self._last_progress:
            self._last_progress = new_progress
            self._last_progress_time = current_time
            self.progress.emit(new_progress)
    
    def _playlist_item_callback(self, current: int, total: int, title: str):
        """Callback for playlist item progress."""
        # Check if stop was requested - raise exception to stop playlist download
        if self._stop_requested:
            import yt_dlp
            raise yt_dlp.utils.DownloadCancelled("Playlist download cancelled by user")
            
        self.playlist_item.emit(current, total, title)
        self.status.emit(f"\n📥 [{current}/{total}] Downloading: {title}")
        # Reset progress tracking for new item
        self._last_progress = 0
        self._last_progress_time = 0
        self._last_status_time = 0
        self.progress.emit(0)  # Reset progress for new item

    def _progress_hook(self, d: dict):
        """
        Hook for yt-dlp progress updates.

        Args:
            d: Progress dictionary from yt-dlp
        """
        # Check if stop was requested - abort download
        if self._stop_requested:
            import yt_dlp
            raise yt_dlp.utils.DownloadCancelled("Download cancelled by user")
            
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
            
            # Emit progress with smoothing
            if percent > 0:
                self._smooth_progress_update(int(percent))

            # Build status message with download info
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
            speed_bytes = d.get("speed", 0)
            speed_str = d.get("_speed_str", "")
            eta_str = d.get("_eta_str", "")
            
            # Throttle status message updates to reduce overhead
            import time
            current_time = time.time()
            if current_time - self._last_status_time < self._status_update_interval:
                return  # Skip status update to improve performance
            self._last_status_time = current_time
            
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
            
            # Build status message (only when we actually update)
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

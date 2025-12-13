"""
Refactored audio downloader with SOLID principles.

This module implements:
- Single Responsibility Principle: Each class has one clear responsibility
- Open/Closed Principle: Extensible through inheritance/composition
- Liskov Substitution Principle: Interfaces are clearly defined
- Interface Segregation Principle: Small, focused interfaces
- Dependency Inversion Principle: Depends on abstractions, not concretions

Design Patterns:
- Strategy Pattern: For different download strategies
- Builder Pattern: For configuring download options
- Template Method: For download workflow
"""

from abc import ABC, abstractmethod
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yt_dlp

from utils.system import find_ffmpeg


# ============================================================================
# Interfaces and Abstract Classes (Dependency Inversion Principle)
# ============================================================================


class IDownloadStrategy(ABC):
    """Interface for download strategies."""

    @abstractmethod
    def download(self, url: str, options: dict[str, Any]) -> str | None:
        """Execute download with given options."""
        pass


class IProgressReporter(ABC):
    """Interface for progress reporting."""

    @abstractmethod
    def report(self, progress_data: dict[str, Any]) -> None:
        """Report progress data."""
        pass


class IVideoInfoExtractor(ABC):
    """Interface for extracting video information."""

    @abstractmethod
    def extract_info(self, url: str) -> dict[str, Any] | None:
        """Extract video information without downloading."""
        pass


# ============================================================================
# Value Objects (immutable data holders)
# ============================================================================


@dataclass(frozen=True)
class AudioFormat:
    """Value object for audio format specification."""

    codec: str
    quality: str
    extension: str

    @staticmethod
    def mp3(quality: str = "192") -> "AudioFormat":
        """Create MP3 format."""
        return AudioFormat(codec="mp3", quality=quality, extension="mp3")

    @staticmethod
    def flac() -> "AudioFormat":
        """Create FLAC format (lossless)."""
        return AudioFormat(codec="flac", quality="best", extension="flac")

    @staticmethod
    def wav() -> "AudioFormat":
        """Create WAV format (lossless)."""
        return AudioFormat(codec="wav", quality="best", extension="wav")

    @staticmethod
    def m4a(quality: str = "256") -> "AudioFormat":
        """Create M4A format."""
        return AudioFormat(codec="aac", quality=quality, extension="m4a")

    @staticmethod
    def opus(quality: str = "128") -> "AudioFormat":
        """Create OPUS format."""
        return AudioFormat(codec="opus", quality=quality, extension="opus")


@dataclass(frozen=True)
class DownloadResult:
    """Value object for download result."""

    success: bool
    file_path: str | None = None
    error_message: str | None = None

    @staticmethod
    def success_result(file_path: str) -> "DownloadResult":
        """Create successful result."""
        return DownloadResult(success=True, file_path=file_path)

    @staticmethod
    def failure_result(error: str) -> "DownloadResult":
        """Create failure result."""
        return DownloadResult(success=False, error_message=error)


# ============================================================================
# Builder Pattern: Download Options Builder
# ============================================================================


@dataclass
class DownloadOptions:
    """Download options configuration (Builder Pattern)."""

    url: str
    output_dir: Path
    audio_format: AudioFormat = field(default_factory=AudioFormat.mp3)
    ffmpeg_location: Path | None = None
    progress_callback: Callable[[dict[str, Any]], None] | None = None
    quiet: bool = False
    no_color: bool = True
    playlist_title: str | None = None  # For organizing playlist downloads
    playlist_index: int | None = None  # For unique filenames in playlists

    def to_ydl_opts(self) -> dict[str, Any]:
        """Convert to yt-dlp options dictionary."""
        # Determine output template based on whether it's a playlist
        if self.playlist_title:
            # Create subdirectory for playlist items with index prefix for uniqueness
            if self.playlist_index is not None:
                # Use custom index for guaranteed uniqueness
                output_template = str(self.output_dir / self.playlist_title / f"{self.playlist_index:03d} - %(title)s.%(ext)s")
            else:
                # Fallback to yt-dlp's playlist_index if available
                output_template = str(self.output_dir / self.playlist_title / "%(playlist_index)03d - %(title)s.%(ext)s")
        else:
            # Single video - save directly to output_dir
            output_template = str(self.output_dir / "%(title)s.%(ext)s")
        
        opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.audio_format.codec,
                    "preferredquality": self.audio_format.quality,
                }
            ],
            "outtmpl": output_template,
            "quiet": self.quiet,
            "no_warnings": self.quiet,
            "no_color": self.no_color,
            # Overwrite existing files (important for interrupted downloads)
            "overwrites": True,
            # Ensure proper audio extraction
            "keepvideo": False,
            "postprocessor_args": {
                "ffmpeg": [
                    "-vn",  # No video
                    "-threads", "0",  # Use all CPU cores for FFmpeg
                ],
            },
            # Prefer formats that work well with audio extraction
            "format_sort": ["acodec:opus", "acodec:aac", "acodec:mp3"],
            # Performance optimizations
            "concurrent_fragment_downloads": 5,  # Download 5 fragments in parallel
            "http_chunk_size": 10485760,  # 10MB chunks for better buffering
            "retries": 10,  # More retries for unstable connections
            "fragment_retries": 10,  # Retry failed fragments
            "skip_unavailable_fragments": False,  # Don't skip fragments
            "buffersize": 16384,  # 16KB buffer for network operations
            "continuedl": True,  # Resume incomplete downloads
            "noprogress": False,  # We need progress for our callbacks
            # Network optimizations
            "socket_timeout": 30,  # 30 seconds timeout
            "source_address": None,  # Use default network interface
        }

        if self.ffmpeg_location:
            opts["ffmpeg_location"] = str(self.ffmpeg_location.parent)

        if self.progress_callback:
            opts["progress_hooks"] = [self.progress_callback]

        return opts


class DownloadOptionsBuilder:
    """Builder for DownloadOptions (Builder Pattern)."""

    def __init__(self):
        """Initialize builder with default values."""
        self._url = ""
        self._output_dir = Path.cwd()
        self._audio_format = AudioFormat.mp3()
        self._ffmpeg_location = None
        self._progress_callback = None
        self._quiet = False
        self._no_color = True
        self._playlist_title = None
        self._playlist_index = None

    def with_url(self, url: str) -> "DownloadOptionsBuilder":
        """Set URL."""
        self._url = url
        return self

    def with_output_dir(self, output_dir: Path) -> "DownloadOptionsBuilder":
        """Set output directory."""
        self._output_dir = output_dir
        return self

    def with_audio_format(self, format_name: str = "mp3", quality: str = "192") -> "DownloadOptionsBuilder":
        """Set audio format by name and quality."""
        format_map = {
            "mp3": lambda: AudioFormat.mp3(quality),
            "flac": lambda: AudioFormat.flac(),
            "wav": lambda: AudioFormat.wav(),
            "m4a": lambda: AudioFormat.m4a(quality),
            "opus": lambda: AudioFormat.opus(quality),
        }
        factory = format_map.get(format_name.lower(), lambda: AudioFormat.mp3(quality))
        self._audio_format = factory()
        return self

    def with_ffmpeg_location(self, location: Path) -> "DownloadOptionsBuilder":
        """Set FFmpeg location."""
        self._ffmpeg_location = location
        return self

    def with_progress_callback(
        self, callback: Callable[[dict[str, Any]], None] | None
    ) -> "DownloadOptionsBuilder":
        """Set progress callback."""
        self._progress_callback = callback
        return self

    def with_quiet_mode(self, quiet: bool = True) -> "DownloadOptionsBuilder":
        """Set quiet mode."""
        self._quiet = quiet
        return self

    def with_playlist_title(self, title: str | None) -> "DownloadOptionsBuilder":
        """Set playlist title for subdirectory creation."""
        self._playlist_title = title
        return self

    def with_playlist_index(self, index: int | None) -> "DownloadOptionsBuilder":
        """Set playlist index for unique filenames."""
        self._playlist_index = index
        return self

    def build(self) -> DownloadOptions:
        """Build DownloadOptions instance."""
        return DownloadOptions(
            url=self._url,
            output_dir=self._output_dir,
            audio_format=self._audio_format,
            ffmpeg_location=self._ffmpeg_location,
            progress_callback=self._progress_callback,
            quiet=self._quiet,
            no_color=self._no_color,
            playlist_title=self._playlist_title,
            playlist_index=self._playlist_index,
        )


# ============================================================================
# Strategy Pattern: Download Strategies
# ============================================================================


class YtDlpDownloadStrategy(IDownloadStrategy):
    """Strategy for downloading using yt-dlp (Strategy Pattern)."""

    def download(self, url: str, options: dict[str, Any]) -> str | None:
        """
        Execute download using yt-dlp.

        Args:
            url: URL to download
            options: yt-dlp options dictionary

        Returns:
            Path to downloaded file or None if failed
        """
        try:
            with yt_dlp.YoutubeDL(options) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    filename = ydl.prepare_filename(info)
                    # Get audio format from options
                    audio_format = options["postprocessors"][0]["preferredcodec"]
                    filename = filename.rsplit(".", 1)[0] + f".{audio_format}"
                    return filename
        except yt_dlp.utils.DownloadCancelled:
            # Re-raise cancellation without wrapping
            raise
        except Exception as e:
            error_msg = str(e)
            # Clean up ffmpeg/ffprobe errors
            if "Invalid data found" in error_msg or "Error opening input" in error_msg:
                raise DownloadError(
                    "Audio conversion failed. The downloaded file may be corrupted or incomplete. "
                    "This can happen if the download was interrupted or if there's an issue with the source."
                ) from e
            elif "unable to obtain file audio codec" in error_msg or "ffprobe" in error_msg.lower():
                raise DownloadError(
                    "Failed to analyze audio file. This might be a temporary issue with the source. "
                    "Try downloading again or try a different video/audio source."
                ) from e
            raise DownloadError(f"Download failed: {error_msg}") from e


class VideoInfoExtractor(IVideoInfoExtractor):
    """Extractor for video information."""

    def extract_info(self, url: str) -> dict[str, Any] | None:
        """
        Extract video information without downloading.

        Args:
            url: URL of the video

        Returns:
            Dictionary with video information or None if error
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "no_color": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            raise VideoInfoError(f"Failed to extract video info: {str(e)}") from e


# ============================================================================
# Custom Exceptions (explicit error handling)
# ============================================================================


class DownloadError(Exception):
    """Exception raised when download fails."""

    pass


class VideoInfoError(Exception):
    """Exception raised when video info extraction fails."""

    pass


# ============================================================================
# Main Service Class (Facade Pattern + Template Method)
# ============================================================================


class AudioDownloader:
    """
    Main audio downloader service (Facade Pattern).

    This class provides a simplified interface to the download subsystem,
    coordinating between different strategies and components.

    Responsibilities (Single Responsibility Principle):
    - Coordinate download process
    - Manage output directory
    - Delegate to appropriate strategies
    """

    def __init__(
        self,
        output_dir: Path | None = None,
        download_strategy: IDownloadStrategy | None = None,
        info_extractor: IVideoInfoExtractor | None = None,
    ):
        """
        Initialize audio downloader.

        Args:
            output_dir: Directory for downloaded files
            download_strategy: Strategy for downloading (DI)
            info_extractor: Strategy for extracting info (DI)
        """
        self.output_dir = output_dir or Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Dependency Injection: use provided or default strategies
        self._download_strategy = download_strategy or YtDlpDownloadStrategy()
        self._info_extractor = info_extractor or VideoInfoExtractor()

    def download(
        self,
        url: str,
        audio_format: str = "mp3",
        quality: str = "192",
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        ffmpeg_location: Path | None = None,
    ) -> DownloadResult:
        """
        Download audio from URL (Template Method Pattern).

        Args:
            url: URL to download
            audio_format: Audio format (mp3, flac, wav, m4a, opus)
            quality: Quality/bitrate
            progress_callback: Progress reporting callback
            ffmpeg_location: Optional FFmpeg location

        Returns:
            DownloadResult with success status and file path or error
        """
        try:
            # Auto-detect ffmpeg if not provided
            if ffmpeg_location is None:
                ffmpeg_path = find_ffmpeg()
                if ffmpeg_path:
                    ffmpeg_location = Path(ffmpeg_path)
            
            # Build options using Builder Pattern
            builder = (
                DownloadOptionsBuilder()
                .with_url(url)
                .with_output_dir(self.output_dir)
                .with_audio_format(audio_format, quality)
                .with_progress_callback(progress_callback)
            )
            
            if ffmpeg_location:
                builder = builder.with_ffmpeg_location(ffmpeg_location)
            
            options = builder.build()

            # Execute download using strategy
            file_path = self._download_strategy.download(url, options.to_ydl_opts())

            if file_path:
                return DownloadResult.success_result(file_path)
            else:
                return DownloadResult.failure_result("Download returned no file")

        except DownloadError as e:
            return DownloadResult.failure_result(str(e))
        except Exception as e:
            # Check if it's a cancellation
            if "DownloadCancelled" in str(type(e).__name__) or "cancelled" in str(e).lower():
                return DownloadResult.failure_result("Download cancelled by user")
            return DownloadResult.failure_result(f"Unexpected error: {str(e)}")

    def get_video_info(self, url: str) -> dict[str, Any] | None:
        """
        Get video information without downloading.

        Args:
            url: URL of the video

        Returns:
            Video information dictionary or None if failed
        """
        try:
            return self._info_extractor.extract_info(url)
        except VideoInfoError:
            return None

    def is_playlist(self, url: str) -> bool:
        """
        Check if URL is a playlist.

        Args:
            url: URL to check

        Returns:
            True if URL is a playlist
        """
        try:
            info = self.get_video_info(url)
            if info:
                return info.get('_type', 'video') == 'playlist'
            return False
        except Exception:
            return False

    def download_playlist(
        self,
        url: str,
        audio_format: str = "mp3",
        quality: str = "192",
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
        item_callback: Callable[[int, int, str], None] | None = None,
        ffmpeg_location: Path | None = None,
    ) -> list[DownloadResult]:
        """
        Download all items from a playlist.

        Args:
            url: Playlist URL
            audio_format: Audio format (mp3, flac, wav, m4a, opus)
            quality: Quality/bitrate
            progress_callback: Progress reporting callback for individual items
            item_callback: Callback for playlist item progress (current, total, title)
            ffmpeg_location: Optional FFmpeg location

        Returns:
            List of DownloadResult for each item
        """
        results = []
        
        try:
            # Auto-detect ffmpeg if not provided
            if ffmpeg_location is None:
                ffmpeg_path = find_ffmpeg()
                if ffmpeg_path:
                    ffmpeg_location = Path(ffmpeg_path)
            
            # Get playlist info
            info = self.get_video_info(url)
            if not info or info.get('_type') != 'playlist':
                return [DownloadResult.failure_result("URL is not a playlist")]
            
            entries = info.get('entries', [])
            total_items = len(entries)
            
            if total_items == 0:
                return [DownloadResult.failure_result("Playlist is empty")]
            
            # Download each item
            for idx, entry in enumerate(entries, 1):
                if entry is None:
                    results.append(DownloadResult.failure_result(f"Item {idx}: Invalid entry"))
                    continue
                
                # Get entry information - prefer webpage_url for full context
                entry_url = entry.get('webpage_url') or entry.get('url') or entry.get('id')
                entry_title = entry.get('title', f'Track {idx}')
                entry_id = entry.get('id', f'unknown_{idx}')
                
                if not entry_url:
                    results.append(DownloadResult.failure_result(f"Item {idx}: No URL found"))
                    continue
                
                # If we only have ID, construct the URL
                if entry_url == entry_id and 'youtube.com' in url:
                    entry_url = f"https://www.youtube.com/watch?v={entry_id}"
                elif entry_url == entry_id and 'youtu.be' in url:
                    entry_url = f"https://www.youtube.com/watch?v={entry_id}"
                
                # Notify about current item
                if item_callback:
                    item_callback(idx, total_items, entry_title)
                
                # Get playlist title for subdirectory
                playlist_title = info.get('title', 'Playlist')
                # Sanitize title for use as directory name
                import re
                playlist_title = re.sub(r'[<>:"/\\|?*]', '_', playlist_title)
                
                # Download single item with playlist context
                builder = (
                    DownloadOptionsBuilder()
                    .with_url(entry_url)
                    .with_output_dir(self.output_dir)
                    .with_audio_format(audio_format, quality)
                    .with_progress_callback(progress_callback)
                    .with_playlist_title(playlist_title)  # Add playlist title
                    .with_playlist_index(idx)  # Add index for unique filename
                )
                
                if ffmpeg_location:
                    builder = builder.with_ffmpeg_location(ffmpeg_location)
                
                options = builder.build()
                
                # Execute download using strategy
                try:
                    file_path = self._download_strategy.download(entry_url, options.to_ydl_opts())
                    if file_path:
                        result = DownloadResult.success_result(file_path)
                    else:
                        result = DownloadResult.failure_result("Download returned no file")
                except DownloadError as e:
                    result = DownloadResult.failure_result(str(e))
                except Exception as e:
                    if "DownloadCancelled" in str(type(e).__name__) or "cancelled" in str(e).lower():
                        # User cancelled - stop the entire playlist download
                        results.append(DownloadResult.failure_result("Download cancelled by user"))
                        break  # Exit the loop immediately
                    else:
                        result = DownloadResult.failure_result(f"Unexpected error: {str(e)}")
                results.append(result)
            
            return results
            
        except Exception as e:
            return [DownloadResult.failure_result(f"Playlist download failed: {str(e)}")]

    @staticmethod
    def _create_audio_format(format_name: str, quality: str) -> AudioFormat:
        """
        Factory method for creating AudioFormat instances.

        Args:
            format_name: Format name (mp3, flac, etc.)
            quality: Quality/bitrate

        Returns:
            AudioFormat instance
        """
        format_map = {
            "mp3": lambda: AudioFormat.mp3(quality),
            "flac": lambda: AudioFormat.flac(),
            "wav": lambda: AudioFormat.wav(),
            "m4a": lambda: AudioFormat.m4a(quality),
            "opus": lambda: AudioFormat.opus(quality),
        }

        factory = format_map.get(format_name.lower())
        if factory:
            return factory()
        else:
            # Default to MP3
            return AudioFormat.mp3(quality)

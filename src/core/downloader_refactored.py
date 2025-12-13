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

    def to_ydl_opts(self) -> dict[str, Any]:
        """Convert to yt-dlp options dictionary."""
        opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": self.audio_format.codec,
                    "preferredquality": self.audio_format.quality,
                }
            ],
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "quiet": self.quiet,
            "no_warnings": self.quiet,
            "no_color": self.no_color,
        }

        if self.ffmpeg_location:
            opts["ffmpeg_location"] = str(self.ffmpeg_location)

        if self.progress_callback:
            opts["progress_hooks"] = [self.progress_callback]

        return opts


class DownloadOptionsBuilder:
    """Builder for DownloadOptions (Builder Pattern)."""

    def __init__(self, url: str, output_dir: Path):
        """Initialize builder with required parameters."""
        self._url = url
        self._output_dir = output_dir
        self._audio_format = AudioFormat.mp3()
        self._ffmpeg_location = None
        self._progress_callback = None
        self._quiet = False
        self._no_color = True

    def with_audio_format(self, audio_format: AudioFormat) -> "DownloadOptionsBuilder":
        """Set audio format."""
        self._audio_format = audio_format
        return self

    def with_ffmpeg_location(self, location: Path) -> "DownloadOptionsBuilder":
        """Set FFmpeg location."""
        self._ffmpeg_location = location
        return self

    def with_progress_callback(
        self, callback: Callable[[dict[str, Any]], None]
    ) -> "DownloadOptionsBuilder":
        """Set progress callback."""
        self._progress_callback = callback
        return self

    def with_quiet_mode(self, quiet: bool = True) -> "DownloadOptionsBuilder":
        """Set quiet mode."""
        self._quiet = quiet
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
        except Exception as e:
            raise DownloadError(f"Download failed: {str(e)}") from e


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
            # Build options using Builder Pattern
            audio_fmt = self._create_audio_format(audio_format, quality)
            options = (
                DownloadOptionsBuilder(url, self.output_dir)
                .with_audio_format(audio_fmt)
                .with_progress_callback(progress_callback)
                .with_ffmpeg_location(ffmpeg_location)
                .build()
            )

            # Execute download using strategy
            file_path = self._download_strategy.download(url, options.to_ydl_opts())

            if file_path:
                return DownloadResult.success_result(file_path)
            else:
                return DownloadResult.failure_result("Download returned no file")

        except DownloadError as e:
            return DownloadResult.failure_result(str(e))
        except Exception as e:
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

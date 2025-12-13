"""Audio downloader using yt-dlp."""

from collections.abc import Callable
from pathlib import Path
from typing import Any

import yt_dlp

from utils.system import find_ffmpeg


class AudioDownloader:
    """Handle audio downloading from various platforms."""

    def __init__(self, output_dir: Path | None = None):
        """
        Initialize the audio downloader.

        Args:
            output_dir: Directory to save downloaded files. Defaults to current directory.
        """
        self.output_dir = output_dir or Path.cwd()
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def download(
        self,
        url: str,
        audio_format: str = "mp3",
        quality: str = "192",
        progress_callback: Callable[[dict[str, Any]], None] | None = None,
    ) -> str | None:
        """
        Download audio from the given URL.

        Args:
            url: URL of the video/audio to download
            audio_format: Output audio format (mp3, flac, wav, m4a)
            quality: Audio quality (bitrate for mp3, e.g., "192", "320")
            progress_callback: Callback function to report download progress

        Returns:
            Path to the downloaded file, or None if download failed
        """
        # Try to find ffmpeg (bundled or system)
        ffmpeg_location = find_ffmpeg()
        
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": audio_format,
                    "preferredquality": quality,
                }
            ],
            "outtmpl": str(self.output_dir / "%(title)s.%(ext)s"),
            "quiet": False,
            "no_warnings": False,
            "no_color": True,  # Disable ANSI color codes
        }
        
        # Set ffmpeg location if found
        if ffmpeg_location:
            ydl_opts["ffmpeg_location"] = str(Path(ffmpeg_location).parent)

        if progress_callback:
            ydl_opts["progress_hooks"] = [progress_callback]

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                if info:
                    filename = ydl.prepare_filename(info)
                    # Replace extension with the audio format
                    filename = filename.rsplit(".", 1)[0] + f".{audio_format}"
                    return filename
        except Exception as e:
            print(f"Error downloading: {e}")
            return None

    def get_video_info(self, url: str) -> dict[str, Any] | None:
        """
        Get information about a video without downloading.

        Args:
            url: URL of the video

        Returns:
            Dictionary with video information or None if error
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(url, download=False)
        except Exception as e:
            print(f"Error getting video info: {e}")
            return None

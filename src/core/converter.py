"""Audio converter using ffmpeg."""

import subprocess
from pathlib import Path


class AudioConverter:
    """Handle audio conversion using ffmpeg."""

    def __init__(self, ffmpeg_path: str | None = None):
        """
        Initialize the audio converter.

        Args:
            ffmpeg_path: Path to ffmpeg binary. If None, assumes ffmpeg is in PATH.
        """
        self.ffmpeg_path = ffmpeg_path or "ffmpeg"

    def convert(
        self,
        input_file: Path,
        output_file: Path,
        audio_format: str = "mp3",
        bitrate: str = "192k",
    ) -> bool:
        """
        Convert audio file to specified format.

        Args:
            input_file: Input audio file path
            output_file: Output audio file path
            audio_format: Output format (mp3, flac, wav, m4a)
            bitrate: Audio bitrate for lossy formats

        Returns:
            True if conversion successful, False otherwise
        """
        cmd = [
            self.ffmpeg_path,
            "-i",
            str(input_file),
            "-vn",  # No video
            "-acodec",
            self._get_codec(audio_format),
            "-b:a",
            bitrate,
            "-y",  # Overwrite output file
            str(output_file),
        ]

        try:
            subprocess.run(cmd, check=True, capture_output=True)
            return True
        except subprocess.CalledProcessError as e:
            print(f"Conversion error: {e}")
            return False

    def _get_codec(self, audio_format: str) -> str:
        """
        Get appropriate codec for the given format.

        Args:
            audio_format: Audio format

        Returns:
            Codec name
        """
        codecs = {
            "mp3": "libmp3lame",
            "flac": "flac",
            "wav": "pcm_s16le",
            "m4a": "aac",
            "opus": "libopus",
        }
        return codecs.get(audio_format.lower(), "libmp3lame")

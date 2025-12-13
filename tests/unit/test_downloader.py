"""Unit tests for refactored downloader module."""

from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest
from core.downloader_refactored import (
    AudioDownloader,
    AudioFormat,
    DownloadOptions,
    DownloadOptionsBuilder,
    DownloadResult,
    YtDlpDownloadStrategy,
    VideoInfoExtractor,
    DownloadError,
    VideoInfoError,
)


class TestAudioFormat:
    """Tests for AudioFormat value object."""

    def test_mp3_format_creation(self):
        """Test MP3 format creation."""
        fmt = AudioFormat.mp3("320")
        assert fmt.codec == "mp3"
        assert fmt.quality == "320"
        assert fmt.extension == "mp3"

    def test_flac_format_creation(self):
        """Test FLAC format creation."""
        fmt = AudioFormat.flac()
        assert fmt.codec == "flac"
        assert fmt.quality == "best"
        assert fmt.extension == "flac"

    def test_wav_format_creation(self):
        """Test WAV format creation."""
        fmt = AudioFormat.wav()
        assert fmt.codec == "wav"
        assert fmt.extension == "wav"

    def test_m4a_format_creation(self):
        """Test M4A format creation."""
        fmt = AudioFormat.m4a("256")
        assert fmt.codec == "aac"
        assert fmt.quality == "256"
        assert fmt.extension == "m4a"

    def test_opus_format_creation(self):
        """Test OPUS format creation."""
        fmt = AudioFormat.opus("128")
        assert fmt.codec == "opus"
        assert fmt.extension == "opus"

    def test_audio_format_immutability(self):
        """Test that AudioFormat is immutable."""
        fmt = AudioFormat.mp3()
        with pytest.raises(Exception):  # FrozenInstanceError
            fmt.quality = "320"


class TestDownloadResult:
    """Tests for DownloadResult value object."""

    def test_success_result_creation(self):
        """Test successful result creation."""
        result = DownloadResult.success_result("/path/to/file.mp3")
        assert result.success is True
        assert result.file_path == "/path/to/file.mp3"
        assert result.error_message is None

    def test_failure_result_creation(self):
        """Test failure result creation."""
        result = DownloadResult.failure_result("Download failed")
        assert result.success is False
        assert result.file_path is None
        assert result.error_message == "Download failed"

    def test_download_result_immutability(self):
        """Test that DownloadResult is immutable."""
        result = DownloadResult.success_result("/path/to/file.mp3")
        with pytest.raises(Exception):  # FrozenInstanceError
            result.success = False


class TestDownloadOptionsBuilder:
    """Tests for DownloadOptionsBuilder (Builder Pattern)."""

    def test_builder_with_defaults(self):
        """Test builder with default values."""
        builder = DownloadOptionsBuilder("https://example.com", Path("/tmp"))
        options = builder.build()

        assert options.url == "https://example.com"
        assert options.output_dir == Path("/tmp")
        assert options.audio_format.codec == "mp3"
        assert options.quiet is False
        assert options.no_color is True

    def test_builder_with_audio_format(self):
        """Test builder with custom audio format."""
        fmt = AudioFormat.flac()
        options = (
            DownloadOptionsBuilder("https://example.com", Path("/tmp"))
            .with_audio_format(fmt)
            .build()
        )

        assert options.audio_format.codec == "flac"

    def test_builder_with_ffmpeg_location(self):
        """Test builder with FFmpeg location."""
        options = (
            DownloadOptionsBuilder("https://example.com", Path("/tmp"))
            .with_ffmpeg_location(Path("/usr/bin/ffmpeg"))
            .build()
        )

        assert options.ffmpeg_location == Path("/usr/bin/ffmpeg")

    def test_builder_with_progress_callback(self):
        """Test builder with progress callback."""
        callback = Mock()
        options = (
            DownloadOptionsBuilder("https://example.com", Path("/tmp"))
            .with_progress_callback(callback)
            .build()
        )

        assert options.progress_callback == callback

    def test_builder_with_quiet_mode(self):
        """Test builder with quiet mode."""
        options = (
            DownloadOptionsBuilder("https://example.com", Path("/tmp"))
            .with_quiet_mode(True)
            .build()
        )

        assert options.quiet is True

    def test_builder_chaining(self):
        """Test method chaining in builder."""
        options = (
            DownloadOptionsBuilder("https://example.com", Path("/tmp"))
            .with_audio_format(AudioFormat.mp3("320"))
            .with_ffmpeg_location(Path("/usr/bin/ffmpeg"))
            .with_quiet_mode(True)
            .build()
        )

        assert options.audio_format.quality == "320"
        assert options.ffmpeg_location == Path("/usr/bin/ffmpeg")
        assert options.quiet is True

    def test_to_ydl_opts_conversion(self):
        """Test conversion to yt-dlp options."""
        options = (
            DownloadOptionsBuilder("https://example.com", Path("/tmp"))
            .with_audio_format(AudioFormat.mp3("192"))
            .build()
        )

        ydl_opts = options.to_ydl_opts()

        assert "format" in ydl_opts
        assert "postprocessors" in ydl_opts
        assert ydl_opts["postprocessors"][0]["preferredcodec"] == "mp3"
        assert ydl_opts["postprocessors"][0]["preferredquality"] == "192"


class TestYtDlpDownloadStrategy:
    """Tests for YtDlpDownloadStrategy."""

    @patch("core.downloader_refactored.yt_dlp.YoutubeDL")
    def test_successful_download(self, mock_ydl_class):
        """Test successful download."""
        # Setup mock
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {"title": "test_video"}
        mock_ydl.prepare_filename.return_value = "/tmp/test_video.webm"

        strategy = YtDlpDownloadStrategy()
        options = {"postprocessors": [{"preferredcodec": "mp3"}]}

        result = strategy.download("https://example.com", options)

        assert result == "/tmp/test_video.mp3"
        mock_ydl.extract_info.assert_called_once()

    @patch("core.downloader_refactored.yt_dlp.YoutubeDL")
    def test_download_failure(self, mock_ydl_class):
        """Test download failure handling."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Network error")

        strategy = YtDlpDownloadStrategy()
        options = {"postprocessors": [{"preferredcodec": "mp3"}]}

        with pytest.raises(DownloadError) as exc_info:
            strategy.download("https://example.com", options)

        assert "Download failed" in str(exc_info.value)


class TestVideoInfoExtractor:
    """Tests for VideoInfoExtractor."""

    @patch("core.downloader_refactored.yt_dlp.YoutubeDL")
    def test_successful_info_extraction(self, mock_ydl_class):
        """Test successful video info extraction."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.return_value = {
            "title": "Test Video",
            "duration": 180,
            "uploader": "Test User",
        }

        extractor = VideoInfoExtractor()
        info = extractor.extract_info("https://example.com")

        assert info["title"] == "Test Video"
        assert info["duration"] == 180
        mock_ydl.extract_info.assert_called_once_with("https://example.com", download=False)

    @patch("core.downloader_refactored.yt_dlp.YoutubeDL")
    def test_info_extraction_failure(self, mock_ydl_class):
        """Test video info extraction failure."""
        mock_ydl = MagicMock()
        mock_ydl_class.return_value.__enter__.return_value = mock_ydl
        mock_ydl.extract_info.side_effect = Exception("Video not found")

        extractor = VideoInfoExtractor()

        with pytest.raises(VideoInfoError):
            extractor.extract_info("https://example.com")


class TestAudioDownloader:
    """Tests for AudioDownloader main class."""

    def test_initialization_with_defaults(self, tmp_path):
        """Test downloader initialization with defaults."""
        downloader = AudioDownloader(output_dir=tmp_path)
        assert downloader.output_dir == tmp_path
        assert downloader.output_dir.exists()

    def test_initialization_creates_directory(self, tmp_path):
        """Test that output directory is created if it doesn't exist."""
        output_dir = tmp_path / "downloads"
        downloader = AudioDownloader(output_dir=output_dir)
        assert output_dir.exists()

    def test_dependency_injection(self, tmp_path):
        """Test dependency injection of strategies."""
        mock_strategy = Mock()
        mock_extractor = Mock()

        downloader = AudioDownloader(
            output_dir=tmp_path,
            download_strategy=mock_strategy,
            info_extractor=mock_extractor,
        )

        assert downloader._download_strategy == mock_strategy
        assert downloader._info_extractor == mock_extractor

    @patch("core.downloader_refactored.YtDlpDownloadStrategy.download")
    def test_successful_download(self, mock_download, tmp_path):
        """Test successful download through main interface."""
        mock_download.return_value = str(tmp_path / "test_video.mp3")

        downloader = AudioDownloader(output_dir=tmp_path)
        result = downloader.download(
            url="https://example.com",
            audio_format="mp3",
            quality="192",
        )

        assert result.success is True
        assert result.file_path == str(tmp_path / "test_video.mp3")
        assert result.error_message is None

    @patch("core.downloader_refactored.YtDlpDownloadStrategy.download")
    def test_download_failure(self, mock_download, tmp_path):
        """Test download failure handling."""
        mock_download.side_effect = DownloadError("Network error")

        downloader = AudioDownloader(output_dir=tmp_path)
        result = downloader.download(url="https://example.com")

        assert result.success is False
        assert result.file_path is None
        assert "Network error" in result.error_message

    def test_create_audio_format_factory(self):
        """Test audio format factory method."""
        mp3_fmt = AudioDownloader._create_audio_format("mp3", "320")
        assert mp3_fmt.codec == "mp3"
        assert mp3_fmt.quality == "320"

        flac_fmt = AudioDownloader._create_audio_format("flac", "best")
        assert flac_fmt.codec == "flac"

        # Test unknown format defaults to MP3
        unknown_fmt = AudioDownloader._create_audio_format("unknown", "192")
        assert unknown_fmt.codec == "mp3"

    @patch("core.downloader_refactored.VideoInfoExtractor.extract_info")
    def test_get_video_info(self, mock_extract, tmp_path):
        """Test get video info method."""
        mock_extract.return_value = {
            "title": "Test Video",
            "duration": 180,
        }

        downloader = AudioDownloader(output_dir=tmp_path)
        info = downloader.get_video_info("https://example.com")

        assert info["title"] == "Test Video"
        assert info["duration"] == 180

    @patch("core.downloader_refactored.VideoInfoExtractor.extract_info")
    def test_get_video_info_failure(self, mock_extract, tmp_path):
        """Test get video info failure handling."""
        mock_extract.side_effect = VideoInfoError("Video not found")

        downloader = AudioDownloader(output_dir=tmp_path)
        info = downloader.get_video_info("https://example.com")

        assert info is None

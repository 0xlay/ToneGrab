"""Unit tests for utils.helpers module."""

import pytest
from utils.helpers import (
    sanitize_filename,
    format_size,
    format_duration,
    is_valid_url,
)


class TestSanitizeFilename:
    """Tests for sanitize_filename function."""

    def test_removes_invalid_characters(self):
        """Test that invalid characters are removed."""
        filename = 'test/file:name*with?invalid"chars<>|'
        result = sanitize_filename(filename)
        assert "/" not in result
        assert ":" not in result
        assert "*" not in result
        assert "?" not in result
        assert '"' not in result
        assert "<" not in result
        assert ">" not in result
        assert "|" not in result

    def test_handles_empty_string(self):
        """Test handling of empty string."""
        result = sanitize_filename("")
        assert result == "untitled"

    def test_handles_only_invalid_chars(self):
        """Test handling of string with only invalid characters."""
        result = sanitize_filename("???***")
        assert result == "untitled"

    def test_preserves_valid_characters(self):
        """Test that valid characters are preserved."""
        filename = "valid_filename-123.mp3"
        result = sanitize_filename(filename)
        assert result == filename

    def test_handles_unicode(self):
        """Test handling of Unicode characters."""
        filename = "Песня_с_кириллицей_2025"
        result = sanitize_filename(filename)
        assert "Песня" in result or len(result) > 0

    def test_replaces_spaces(self):
        """Test that spaces are handled correctly."""
        filename = "test file name"
        result = sanitize_filename(filename)
        # Spaces should be preserved or replaced with underscore
        assert result in ["test file name", "test_file_name"]


class TestFormatSize:
    """Tests for format_size function."""

    def test_formats_bytes(self):
        """Test formatting bytes."""
        assert format_size(500) == "500.00 B"

    def test_formats_kilobytes(self):
        """Test formatting kilobytes."""
        assert format_size(1024) == "1.00 KB"
        assert format_size(1536) == "1.50 KB"

    def test_formats_megabytes(self):
        """Test formatting megabytes."""
        assert format_size(1024 * 1024) == "1.00 MB"
        assert format_size(5 * 1024 * 1024) == "5.00 MB"

    def test_formats_gigabytes(self):
        """Test formatting gigabytes."""
        assert format_size(1024 * 1024 * 1024) == "1.00 GB"

    def test_handles_zero(self):
        """Test handling of zero bytes."""
        assert format_size(0) == "0.00 B"

    def test_handles_negative(self):
        """Test handling of negative values."""
        result = format_size(-100)
        # Should handle gracefully (return 0 or abs value)
        assert isinstance(result, str)


class TestFormatDuration:
    """Tests for format_duration function."""

    def test_formats_seconds_only(self):
        """Test formatting duration with only seconds."""
        assert format_duration(45) == "00:45"

    def test_formats_minutes_and_seconds(self):
        """Test formatting duration with minutes and seconds."""
        assert format_duration(125) == "02:05"

    def test_formats_hours_minutes_seconds(self):
        """Test formatting duration with hours."""
        assert format_duration(3661) == "01:01:01"

    def test_handles_zero(self):
        """Test handling of zero duration."""
        assert format_duration(0) == "00:00"

    def test_handles_none(self):
        """Test handling of None value."""
        assert format_duration(None) == "Unknown"

    def test_handles_float(self):
        """Test handling of float values."""
        assert format_duration(125.7) == "02:05"  # Truncates to 125 seconds

    def test_formats_large_duration(self):
        """Test formatting large duration (days)."""
        seconds = 90000  # 25 hours
        result = format_duration(seconds)
        assert result.startswith("25:")


class TestIsValidUrl:
    """Tests for is_valid_url function."""

    def test_validates_http_url(self):
        """Test validation of HTTP URL."""
        assert is_valid_url("http://example.com") is True

    def test_validates_https_url(self):
        """Test validation of HTTPS URL."""
        assert is_valid_url("https://example.com") is True

    def test_validates_youtube_url(self):
        """Test validation of YouTube URL."""
        assert is_valid_url("https://www.youtube.com/watch?v=dQw4w9WgXcQ") is True

    def test_validates_soundcloud_url(self):
        """Test validation of SoundCloud URL."""
        assert is_valid_url("https://soundcloud.com/artist/track") is True

    def test_rejects_invalid_protocol(self):
        """Test rejection of invalid protocol."""
        assert is_valid_url("ftp://example.com") is False

    def test_rejects_no_protocol(self):
        """Test rejection of URL without protocol."""
        assert is_valid_url("example.com") is False

    def test_rejects_empty_string(self):
        """Test rejection of empty string."""
        assert is_valid_url("") is False

    def test_rejects_none(self):
        """Test rejection of None value."""
        assert is_valid_url(None) is False

    def test_rejects_malformed_url(self):
        """Test rejection of malformed URL."""
        assert is_valid_url("https://") is False
        assert is_valid_url("http://invalid url with spaces") is False

"""Unit tests for configuration module."""

import json
from pathlib import Path

import pytest

from core.config import AppConfig


class TestAppConfig:
    """Test suite for AppConfig class."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        config = AppConfig()
        assert config.output_directory == str(Path.home() / "Music" / "ToneGrab")
        assert config.audio_format == "mp3"
        assert config.audio_quality == "192"
        assert config.theme == "dark"
        assert config.language == "en"

    def test_init_with_custom_values(self):
        """Test initialization with custom values."""
        config = AppConfig(
            output_directory="/custom/path",
            audio_format="flac",
            audio_quality="320",
            theme="light",
            language="ru",
        )
        assert config.output_directory == "/custom/path"
        assert config.audio_format == "flac"
        assert config.audio_quality == "320"
        assert config.theme == "light"
        assert config.language == "ru"

    def test_asdict_conversion(self):
        """Test conversion to dict using asdict."""
        from dataclasses import asdict

        config = AppConfig()
        config_dict = asdict(config)
        assert "output_directory" in config_dict
        assert "audio_format" in config_dict
        assert "audio_quality" in config_dict
        assert "theme" in config_dict
        assert "language" in config_dict

    def test_from_dict(self):
        """Test creating config from dict."""
        data = {
            "output_directory": "/test/path",
            "audio_format": "wav",
            "audio_quality": "256",
            "theme": "light",
            "language": "ru",
        }
        config = AppConfig(**data)
        assert config.output_directory == "/test/path"
        assert config.audio_format == "wav"

    def test_from_dict_with_missing_keys(self):
        """Test creating config from dict with missing keys (uses defaults)."""
        data = {"audio_format": "opus"}
        config = AppConfig(**data)
        assert config.audio_format == "opus"
        assert config.audio_quality == "192"  # default

    def test_save_config(self, tmp_path):
        """Test saving configuration to file."""
        config = AppConfig(audio_format="flac")
        config_file = tmp_path / "config.json"

        result = config.save(config_file)
        assert result is True
        assert config_file.exists()

        # Verify content
        with open(config_file, encoding="utf-8") as f:
            data = json.load(f)
        assert data["audio_format"] == "flac"

    def test_load_config(self, tmp_path):
        """Test loading configuration from file."""
        # Create a config file
        config_data = {
            "output_directory": "/test/path",
            "audio_format": "flac",
            "audio_quality": "320",
            "theme": "light",
            "language": "ru",
        }
        config_file = tmp_path / "config.json"
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config_data, f)

        # Load config
        config = AppConfig.load(config_file)
        assert config.output_directory == "/test/path"
        assert config.audio_format == "flac"
        assert config.audio_quality == "320"

    def test_load_config_file_not_exists(self, tmp_path):
        """Test loading config when file doesn't exist (returns defaults)."""
        config_file = tmp_path / "nonexistent.json"
        config = AppConfig.load(config_file)
        # Should return default config
        assert config.audio_format == "mp3"
        assert config.audio_quality == "192"

    def test_config_path_creation(self, tmp_path):
        """Test that config directory is created when saving."""
        config = AppConfig()
        config_file = tmp_path / "deep" / "nested" / "path" / "config.json"

        result = config.save(config_file)
        assert result is True
        assert config_file.parent.exists()
        assert config_file.exists()

    def test_validation_audio_format(self):
        """Test audio format validation."""
        # Valid formats
        config = AppConfig(audio_format="mp3")
        assert config.audio_format == "mp3"

        config = AppConfig(audio_format="flac")
        assert config.audio_format == "flac"

    def test_validation_audio_quality(self):
        """Test audio quality validation."""
        config = AppConfig(audio_quality="320")
        assert config.audio_quality == "320"

        config = AppConfig(audio_quality="128")
        assert config.audio_quality == "128"

    def test_default_config_path(self):
        """Test getting default config path."""
        path = AppConfig.get_default_config_path()
        assert isinstance(path, Path)
        assert "ToneGrab" in str(path)
        assert "config.json" in str(path)

    def test_get_default_config_path_returns_path(self):
        """Test that get_default_config_path returns a Path object."""
        path = AppConfig.get_default_config_path()
        assert isinstance(path, Path)
        expected = Path.home() / ".config" / "ToneGrab" / "config.json"
        assert path == expected

    def test_save_uses_default_path_when_none(self, monkeypatch, tmp_path):
        """Test that save uses default path when config_path is None."""
        # Mock get_default_config_path to return tmp_path
        test_config_path = tmp_path / "test_config.json"

        # Static method needs to be mocked differently
        monkeypatch.setattr(
            AppConfig,
            "get_default_config_path",
            staticmethod(lambda: test_config_path),
        )

        config = AppConfig(audio_format="opus")
        result = config.save(None)

        assert result is True
        assert test_config_path.exists()

        with open(test_config_path, encoding="utf-8") as f:
            data = json.load(f)
        assert data["audio_format"] == "opus"

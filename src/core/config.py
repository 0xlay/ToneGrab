"""Configuration management for ToneGrab."""

import json
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class AppConfig:
    """Application configuration."""

    output_directory: str = str(Path.home() / "Music" / "ToneGrab")
    audio_format: str = "mp3"
    audio_quality: str = "192"
    theme: str = "dark"
    language: str = "en"

    @classmethod
    def load(cls, config_path: Path | None = None) -> "AppConfig":
        """
        Load configuration from file.

        Args:
            config_path: Path to config file. If None, uses default location.

        Returns:
            AppConfig instance
        """
        if config_path is None:
            config_path = cls.get_default_config_path()

        if config_path.exists():
            try:
                with open(config_path, encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**data)
            except Exception as e:
                print(f"Error loading config: {e}")
                return cls()

        return cls()

    def save(self, config_path: Path | None = None) -> bool:
        """
        Save configuration to file.

        Args:
            config_path: Path to config file. If None, uses default location.

        Returns:
            True if save successful, False otherwise
        """
        if config_path is None:
            config_path = self.get_default_config_path()

        config_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config: {e}")
            return False

    @staticmethod
    def get_default_config_path() -> Path:
        """Get default configuration file path."""
        config_dir = Path.home() / ".config" / "ToneGrab"
        return config_dir / "config.json"

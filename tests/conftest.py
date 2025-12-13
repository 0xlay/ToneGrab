"""Pytest configuration and fixtures."""

import sys
from pathlib import Path

import pytest

# Add src to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary output directory for tests."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_video_info():
    """Sample video info dict for testing."""
    return {
        "id": "test_video_123",
        "title": "Test Video Title",
        "uploader": "Test Uploader",
        "duration": 180,  # 3 minutes
        "webpage_url": "https://example.com/video/test",
        "ext": "webm",
    }


@pytest.fixture
def sample_config():
    """Sample configuration for testing."""
    return {
        "output_dir": str(Path.home() / "Downloads"),
        "audio_format": "mp3",
        "audio_quality": "192",
    }

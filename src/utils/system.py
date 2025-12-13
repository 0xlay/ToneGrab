"""System utilities for checking dependencies."""

import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple


def get_resource_path(relative_path: str) -> Path:
    """
    Get absolute path to resource, works for dev and PyInstaller.

    Args:
        relative_path: Relative path to resource (e.g., 'assets/icons/icon.ico')

    Returns:
        Absolute path to resource
    """
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running as script
        base_path = Path(__file__).parent.parent.parent

    return base_path / relative_path


def get_bundled_ffmpeg_path() -> Path | None:
    """
    Get path to bundled ffmpeg executable.

    Returns:
        Path to ffmpeg if found, None otherwise
    """
    # Determine the base path (works for both dev and bundled)
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
    else:
        # Running as script
        base_path = Path(__file__).parent.parent.parent

    # Determine platform
    if sys.platform == "win32":
        ffmpeg_name = "ffmpeg.exe"
        platform = "windows"
    elif sys.platform == "darwin":
        ffmpeg_name = "ffmpeg"
        platform = "macos"
    else:
        ffmpeg_name = "ffmpeg"
        platform = "linux"

    # Check bundled location
    bundled_path = base_path / "ffmpeg" / platform / "bin" / ffmpeg_name

    if bundled_path.exists():
        return bundled_path

    return None


def find_ffmpeg() -> str | None:
    """
    Find ffmpeg executable. Checks bundled location first, then system PATH.

    Returns:
        Path to ffmpeg or None if not found
    """
    # First check bundled version
    bundled = get_bundled_ffmpeg_path()
    if bundled:
        return str(bundled)

    # Then check system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        return system_ffmpeg

    return None


def check_ffmpeg() -> Tuple[bool, str]:
    """
    Check if ffmpeg is available in the system.

    Returns:
        Tuple of (is_available, version_or_error)
    """
    try:
        # Try to find ffmpeg (bundled or system)
        ffmpeg_path = find_ffmpeg()
        
        if not ffmpeg_path:
            return False, "FFmpeg not found in PATH or bundled location"

        # Get version
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
        )

        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split("\n")[0]
            return True, version_line
        else:
            return False, "FFmpeg found but unable to get version"

    except subprocess.TimeoutExpired:
        return False, "FFmpeg check timed out"
    except Exception as e:
        return False, f"Error checking FFmpeg: {str(e)}"


def check_dependencies() -> dict:
    """
    Check all system dependencies.

    Returns:
        Dictionary with dependency status
    """
    ffmpeg_available, ffmpeg_info = check_ffmpeg()

    return {
        "ffmpeg": {
            "available": ffmpeg_available,
            "info": ffmpeg_info,
        }
    }

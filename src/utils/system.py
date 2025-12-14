"""System utilities for checking dependencies."""

import logging
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Tuple

# Setup logging for debugging ffmpeg search
logger = logging.getLogger(__name__)


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

    # Determine the base path (works for both dev and bundled)
    if getattr(sys, "frozen", False):
        # Running as compiled executable
        base_path = Path(sys._MEIPASS)
        
        # For macOS .app bundle with --onefile, PyInstaller extracts to temp dir
        # Check standard bundled location
        bundled_path = base_path / "ffmpeg" / platform / "bin" / ffmpeg_name
        
        if bundled_path.exists() and os.access(bundled_path, os.X_OK):
            return bundled_path
        
        # Fallback: check other possible locations
        if sys.platform == "darwin":
            possible_paths = [
                base_path / ffmpeg_name,  # Root of temp extraction
                base_path / ".." / "Resources" / "ffmpeg" / platform / "bin" / ffmpeg_name,
                base_path / "bin" / ffmpeg_name,
            ]
            
            for path in possible_paths:
                resolved = path.resolve()
                if resolved.exists() and os.access(resolved, os.X_OK):
                    return resolved
            
        return None
    else:
        # Running as script
        base_path = Path(__file__).parent.parent.parent

    # Check bundled location
    bundled_path = base_path / "ffmpeg" / platform / "bin" / ffmpeg_name

    if bundled_path.exists():
        return bundled_path

    return None


def find_ffmpeg() -> str | None:
    """
    Find ffmpeg executable. Checks bundled location first, then system PATH,
    then common Homebrew locations on macOS.

    Returns:
        Path to ffmpeg or None if not found
    """
    # First check bundled version
    bundled = get_bundled_ffmpeg_path()
    if bundled:
        logger.info(f"Found bundled ffmpeg at: {bundled}")
        return str(bundled)
    else:
        logger.warning("Bundled ffmpeg not found")
        if getattr(sys, "frozen", False):
            logger.debug(f"sys._MEIPASS: {sys._MEIPASS}")
            logger.debug(f"sys.executable: {sys.executable}")

    # Then check system PATH
    system_ffmpeg = shutil.which("ffmpeg")
    if system_ffmpeg:
        logger.info(f"Found system ffmpeg at: {system_ffmpeg}")
        return system_ffmpeg
    
    # On macOS, check common Homebrew installation paths
    if sys.platform == "darwin":
        homebrew_paths = [
            "/opt/homebrew/bin/ffmpeg",  # Apple Silicon (ARM64)
            "/usr/local/bin/ffmpeg",     # Intel (x86_64)
            "/opt/homebrew/Cellar/ffmpeg",  # Cellar directory
        ]
        
        for path in homebrew_paths:
            if path.endswith("Cellar/ffmpeg"):
                # Check Cellar directory for any version
                from pathlib import Path
                cellar = Path(path)
                if cellar.exists():
                    # Find the latest version
                    versions = sorted(cellar.iterdir(), reverse=True)
                    if versions:
                        ffmpeg_bin = versions[0] / "bin" / "ffmpeg"
                        if ffmpeg_bin.exists():
                            logger.info(f"Found Homebrew ffmpeg in Cellar at: {ffmpeg_bin}")
                            return str(ffmpeg_bin)
            else:
                # Direct path check
                if os.path.exists(path) and os.access(path, os.X_OK):
                    logger.info(f"Found Homebrew ffmpeg at: {path}")
                    return path
        
        logger.warning("FFmpeg not found in Homebrew locations (/opt/homebrew or /usr/local)")
    
    logger.error("ffmpeg not found in bundled location, system PATH, or Homebrew")
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
            logger.error("check_ffmpeg: ffmpeg_path is None")
            return False, "FFmpeg not found in PATH or bundled location"
        
        logger.info(f"check_ffmpeg: Attempting to run: {ffmpeg_path} -version")
        
        # Check if file exists and is executable
        from pathlib import Path
        ffmpeg_file = Path(ffmpeg_path)
        if not ffmpeg_file.exists():
            logger.error(f"check_ffmpeg: File does not exist: {ffmpeg_path}")
            return False, f"FFmpeg file not found: {ffmpeg_path}"
        
        # Log file stats
        try:
            stat_info = os.stat(ffmpeg_path)
            logger.info(f"check_ffmpeg: File size: {stat_info.st_size} bytes")
            logger.info(f"check_ffmpeg: File mode: {oct(stat_info.st_mode)}")
            logger.info(f"check_ffmpeg: Is executable: {os.access(ffmpeg_path, os.X_OK)}")
        except Exception as stat_error:
            logger.warning(f"check_ffmpeg: Could not stat file: {stat_error}")
        
        # Check file type on macOS to verify it's the right architecture
        if sys.platform == "darwin":
            try:
                file_result = subprocess.run(
                    ["file", ffmpeg_path],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                logger.info(f"check_ffmpeg: File type: {file_result.stdout.strip()}")
                
                # Check dynamic library dependencies
                otool_result = subprocess.run(
                    ["otool", "-L", ffmpeg_path],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                logger.info(f"check_ffmpeg: Dynamic libraries:\n{otool_result.stdout}")
            except Exception as file_error:
                logger.warning(f"check_ffmpeg: Could not check file type: {file_error}")
        
        if not os.access(ffmpeg_path, os.X_OK):
            logger.error(f"check_ffmpeg: File not executable: {ffmpeg_path}")
            # Try to make it executable on Unix systems
            if sys.platform in ["darwin", "linux"]:
                try:
                    os.chmod(ffmpeg_path, 0o755)
                    logger.info(f"check_ffmpeg: Set executable permissions on {ffmpeg_path}")
                    # Verify chmod worked
                    logger.info(f"check_ffmpeg: After chmod, is executable: {os.access(ffmpeg_path, os.X_OK)}")
                except Exception as chmod_error:
                    logger.error(f"check_ffmpeg: Failed to chmod: {chmod_error}")
                    return False, f"FFmpeg found but not executable: {ffmpeg_path}"

        # Get version
        # On macOS, set environment to help with dynamic library loading
        env = os.environ.copy()
        if sys.platform == "darwin" and getattr(sys, 'frozen', False):
            # In frozen app, add _MEIPASS to library search path
            meipass = sys._MEIPASS
            env['DYLD_LIBRARY_PATH'] = f"{meipass}:{env.get('DYLD_LIBRARY_PATH', '')}"
            env['DYLD_FALLBACK_LIBRARY_PATH'] = f"/usr/lib:/usr/local/lib:{meipass}"
            logger.info(f"check_ffmpeg: Set DYLD_LIBRARY_PATH to include {meipass}")
        else:
            env = None
        
        result = subprocess.run(
            [ffmpeg_path, "-version"],
            capture_output=True,
            text=True,
            timeout=5,
            env=env,
        )
        
        logger.info(f"check_ffmpeg: returncode={result.returncode}")
        if result.returncode != 0:
            logger.error(f"check_ffmpeg: stderr={result.stderr}")
            logger.error(f"check_ffmpeg: stdout={result.stdout}")

        if result.returncode == 0:
            # Extract version from first line
            version_line = result.stdout.split("\n")[0]
            logger.info(f"check_ffmpeg: Success - {version_line}")
            return True, version_line
        else:
            return False, f"FFmpeg found but unable to get version (code {result.returncode})"

    except subprocess.TimeoutExpired:
        logger.error("check_ffmpeg: Timeout expired")
        return False, "FFmpeg check timed out"
    except Exception as e:
        logger.error(f"check_ffmpeg: Exception - {type(e).__name__}: {str(e)}")
        import traceback
        logger.error(f"check_ffmpeg: Traceback:\n{traceback.format_exc()}")
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

"""Build script for creating standalone Linux executable."""

import os
import sys
from pathlib import Path

import PyInstaller.__main__

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
ASSETS_DIR = PROJECT_ROOT / "assets"
ICON_PATH = PROJECT_ROOT / "assets" / "icons" / "icon.png"
FFMPEG_DIR = PROJECT_ROOT / "ffmpeg" / "linux" / "bin"

# Build configuration
APP_NAME = "ToneGrab"
MAIN_SCRIPT = str(SRC_DIR / "main.py")


def build_linux():
    """Build Linux executable with PyInstaller."""
    print("=" * 60)
    print(f"Building {APP_NAME} for Linux...")
    print("=" * 60)

    # PyInstaller arguments
    args = [
        MAIN_SCRIPT,
        f"--name={APP_NAME}",
        "--onefile",  # Single executable file
        f"--distpath={DIST_DIR}",
        f"--workpath={BUILD_DIR / 'temp'}",
        f"--specpath={BUILD_DIR}",
        # Add source directories to Python path
        f"--paths={SRC_DIR}",
        # Hidden imports (if needed)
        "--hidden-import=PySide6.QtCore",
        "--hidden-import=PySide6.QtGui",
        "--hidden-import=PySide6.QtWidgets",
        "--hidden-import=yt_dlp",
        # Collect data files
        f"--add-data={SRC_DIR}:src",
        f"--add-data={ASSETS_DIR}:assets",
    ]

    # Add ffmpeg binaries if they exist
    if FFMPEG_DIR.exists():
        ffmpeg_exe = FFMPEG_DIR / "ffmpeg"
        ffprobe_exe = FFMPEG_DIR / "ffprobe"
        
        if ffmpeg_exe.exists():
            args.append(f"--add-binary={ffmpeg_exe}:ffmpeg/linux/bin")
            print(f"[OK] Including ffmpeg from: {ffmpeg_exe}")
        else:
            print(f"[WARNING] ffmpeg not found in {FFMPEG_DIR}")
        
        if ffprobe_exe.exists():
            args.append(f"--add-binary={ffprobe_exe}:ffmpeg/linux/bin")
            print(f"[OK] Including ffprobe from: {ffprobe_exe}")
        else:
            print(f"[WARNING] ffprobe not found in {FFMPEG_DIR}")
    else:
        print(f"[WARNING] FFmpeg directory not found: {FFMPEG_DIR}")

    # Add icon if exists
    if ICON_PATH.exists():
        args.append(f"--icon={ICON_PATH}")

    # Clean previous builds
    print("\nCleaning previous builds...")
    if DIST_DIR.exists():
        import shutil

        for item in DIST_DIR.iterdir():
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                shutil.rmtree(item)

    # Run PyInstaller
    print("\nRunning PyInstaller...")
    PyInstaller.__main__.run(args)

    print("\n" + "=" * 60)
    print(f"Build complete! Executable: {DIST_DIR / APP_NAME}")
    print("=" * 60)
    print("\nNote: To create an AppImage, use tools like appimagetool or linuxdeploy")


def main():
    """Main build function."""
    if sys.platform not in ("linux", "linux2"):
        print("Warning: This script is designed for Linux.")
        print("Building anyway, but the result may not work correctly.")

    build_linux()


if __name__ == "__main__":
    main()

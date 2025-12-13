"""Build script for creating standalone macOS application."""

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
ICON_PATH = PROJECT_ROOT / "assets" / "icons" / "icon.png"  # Use PNG for now
FFMPEG_DIR = PROJECT_ROOT / "ffmpeg" / "macos" / "bin"

# Build configuration
APP_NAME = "ToneGrab"
MAIN_SCRIPT = str(SRC_DIR / "main.py")


def build_macos():
    """Build macOS application with PyInstaller."""
    print("=" * 60)
    print(f"Building {APP_NAME} for macOS...")
    print("=" * 60)

    # PyInstaller arguments
    args = [
        MAIN_SCRIPT,
        f"--name={APP_NAME}",
        "--onefile",  # Single executable file
        "--windowed",  # .app bundle
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
        # macOS specific
        "--target-arch=universal2",  # Universal binary for Intel and Apple Silicon
    ]

    # Add ffmpeg binaries if they exist
    if FFMPEG_DIR.exists():
        ffmpeg_exe = FFMPEG_DIR / "ffmpeg"
        ffprobe_exe = FFMPEG_DIR / "ffprobe"
        
        if ffmpeg_exe.exists():
            args.append(f"--add-binary={ffmpeg_exe}:ffmpeg/macos/bin")
            print(f"✓ Including ffmpeg from: {ffmpeg_exe}")
        else:
            print(f"⚠ Warning: ffmpeg not found in {FFMPEG_DIR}")
        
        if ffprobe_exe.exists():
            args.append(f"--add-binary={ffprobe_exe}:ffmpeg/macos/bin")
            print(f"✓ Including ffprobe from: {ffprobe_exe}")
        else:
            print(f"⚠ Warning: ffprobe not found in {FFMPEG_DIR}")
    else:
        print(f"⚠ Warning: FFmpeg directory not found: {FFMPEG_DIR}")

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
    print(f"Build complete! Application: {DIST_DIR / f'{APP_NAME}.app'}")
    print("=" * 60)


def main():
    """Main build function."""
    if sys.platform != "darwin":
        print("Warning: This script is designed for macOS.")
        print("Building anyway, but the result may not work correctly.")

    build_macos()


if __name__ == "__main__":
    main()

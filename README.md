# ToneGrab

<div align="center">
  <h3>🎵 Cross-platform Audio Downloader</h3>
  <p>Download audio from YouTube, SoundCloud, and more with a beautiful UI</p>
</div>

## Features

- 🎯 **Multi-platform Support** - Download from YouTube, SoundCloud, and many other platforms
- 🎨 **Modern UI** - Clean and intuitive interface built with PySide6
- 🎵 **Multiple Formats** - MP3, FLAC, WAV, M4A, OPUS support
- 📋 **Playlist Support** - Download entire playlists automatically
- ⚡ **Fast & Efficient** - Powered by yt-dlp and bundled ffmpeg
- 🖥️ **Cross-platform** - Windows, macOS, and Linux
- 📦 **Standalone** - No need to install Python or other dependencies (FFmpeg bundled)
- 🔄 **Real-time Progress** - Watch download progress in real-time with size, speed, and ETA
- 🎛️ **Quality Control** - Choose audio quality from 128 to 320 kbps

## Quick Start

### Option 1: Download Binary (Easiest)

Download the latest release for your platform:
- **Windows**: `ToneGrab.exe`
- **macOS**: `ToneGrab.app`
- **Linux**: `ToneGrab`

Just download and run - no installation needed!

### Option 2: Run from Source

1. **Clone and setup**:
```bash
git clone https://github.com/0xlay/ToneGrab.git
cd ToneGrab
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

pip install -r requirements.txt
```

2. **Run**:
```bash
python src/main.py
```

## Usage

1. Launch ToneGrab
2. Paste a URL from YouTube, SoundCloud, or other supported platforms
   - **Single video/track**: `https://www.youtube.com/watch?v=...`
   - **Playlist**: `https://www.youtube.com/playlist?list=...`
   - **SoundCloud set**: `https://soundcloud.com/artist/sets/playlist`
3. Select audio format (MP3, FLAC, WAV, M4A, OPUS) and quality
4. Click "Download"
5. Watch real-time progress with size, speed, and ETA
6. For playlists, all tracks will be downloaded automatically with progress tracking
7. Find your audio in the output directory

### Playlist Downloads

ToneGrab automatically detects playlist URLs and downloads all tracks:
- ✅ YouTube playlists
- ✅ SoundCloud sets/playlists
- ✅ Bandcamp albums
- ✅ And more platforms supported by yt-dlp

The application shows:
- Total number of tracks
- Current track being downloaded
- Overall progress
- Individual track progress

### Supported Platforms

Over 1000+ sites supported via yt-dlp, including:
- YouTube, SoundCloud, Bandcamp, Vimeo, Mixcloud
- Full list: [yt-dlp supported sites](https://github.com/yt-dlp/yt-dlp/blob/master/supportedsites.md)

## Development

### Prerequisites

- Python 3.10+
- Git

### Setup Development Environment

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Format code
black src/

# Lint code
ruff check src/

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest --cov=src --cov-report=html
```

### Running Tests

```bash
# All tests
python run_tests.py

# Unit tests only
python run_tests.py unit

# Integration tests only
python run_tests.py integration

# With coverage report
python run_tests.py coverage
```

## Building Standalone Executable

### Prerequisites for Building

Before building, you need to download FFmpeg binaries and place them in the correct directory structure:

1. **Download FFmpeg** for your platform:
   - **Windows**: https://github.com/BtbN/FFmpeg-Builds/releases (download `ffmpeg-master-latest-win64-gpl.zip`)
   - **macOS**: https://evermeet.cx/ffmpeg/ or https://github.com/eugeneware/ffmpeg-static/releases
   - **Linux**: https://johnvansickle.com/ffmpeg/ or https://github.com/eugeneware/ffmpeg-static/releases

2. **Extract and organize** FFmpeg binaries into the following structure:
   ```
   ffmpeg/
   ├── windows/
   │   ├── bin/
   │   │   ├── ffmpeg.exe
   │   │   ├── ffplay.exe
   │   │   └── ffprobe.exe
   │   └── LICENSE.txt
   ├── macos/
   │   ├── bin/
   │   │   ├── ffmpeg
   │   │   ├── ffplay
   │   │   └── ffprobe
   │   └── LICENSE.txt
   └── linux/
       ├── bin/
       │   ├── ffmpeg
       │   ├── ffplay
       │   └── ffprobe
       └── LICENSE.txt
   ```

3. **Make binaries executable** (macOS/Linux):
   ```bash
   chmod +x ffmpeg/macos/bin/*
   chmod +x ffmpeg/linux/bin/*
   ```

### Windows

```powershell
python build\build_windows.py
```

**Result**: `dist\ToneGrab.exe`

### 🐧 Linux

1. **Setup environment**:
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt install python3-pip python3-venv libxcb-xinerama0 libxcb-cursor0

# Create venv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt pyinstaller
```

2. **Build**:
```bash
python build/build_linux.py
```

**Result**: `dist/ToneGrab`

### 🍎 macOS

1. **Setup environment**:
```bash
# Install dependencies
brew install python@3.13

# Create venv and install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install pyinstaller
```

2. **Build**:
```bash
python build/build_macos.py
```

**Result**: `dist/ToneGrab.app`

---

## 📦 Build Scripts Overview

All platforms use similar PyInstaller-based build scripts:

| Platform | Script | Output | Size | Notes |
|----------|--------|--------|------|-------|
| Windows | `build/build_windows.py` | `ToneGrab.exe` | ~185 MB | Includes .ico icon |
| Linux | `build/build_linux.py` | `ToneGrab` | ~180-200 MB | Can create AppImage |
| macOS | `build/build_macos.py` | `ToneGrab.app` | ~200-220 MB | Universal2 (Intel + ARM) |

**All builds include:**
- Python runtime
- PySide6 (Qt framework)
- yt-dlp
- FFmpeg + FFprobe (bundled)
- Application assets (icons)

---

## CI/CD

ToneGrab uses GitHub Actions for automated building across all platforms and architectures:

### Supported Build Targets

| Platform | Architecture | Runner | Artifact Name |
|----------|-------------|--------|---------------|
| Windows | x64 | `windows-latest` | `ToneGrab-windows-x64-{version}.zip` |
| Windows | ARM64 | `windows-latest` | `ToneGrab-windows-arm64-{version}.zip` |
| Linux | x64 | `ubuntu-latest` | `ToneGrab-linux-x64-{version}.zip` |
| Linux | ARM64 | `ubuntu-latest` | `ToneGrab-linux-arm64-{version}.zip` |
| macOS | Apple Silicon (M1/M2/M3/M4) | `macos-latest` | `ToneGrab-macos-apple-silicon-arm64-{version}.zip` |

### Automated Workflows

**Build Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Git tags starting with `v*` (e.g., `v1.0.0`)
- Manual workflow dispatch

**What happens during build:**
1. Sets up Python environment
2. Installs dependencies
3. Downloads FFmpeg binaries for target platform
4. Builds standalone executable with PyInstaller
5. Packages into platform-specific ZIP archive
6. Uploads artifacts (30-day retention)
7. Creates GitHub Release (for version tags)

**Creating a Release:**
```bash
# Tag your version
git tag -a v1.0.0 -m "Release version 1.0.0"
git push origin v1.0.0

# GitHub Actions will automatically:
# - Build all platform variants
# - Create a GitHub Release
# - Attach all ZIP archives to the release
```

## Contributing

Contributions welcome! To contribute:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Format code: `black src/`
5. Lint: `ruff check src/`
6. Test your changes
7. Commit: `git commit -am 'Add feature'`
8. Push: `git push origin feature-name`
9. Open a Pull Request

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The amazing download engine
- [PySide6](https://www.qt.io/qt-for-python) - Qt for Python
- [ffmpeg](https://ffmpeg.org/) - Audio/video processing
- [PyInstaller](https://pyinstaller.org/) - Executable packaging

## Links

- **Repository**: [GitHub](https://github.com/0xlay/ToneGrab)
- **Issues**: [GitHub Issues](https://github.com/0xlay/ToneGrab/issues)
- **Releases**: [GitHub Releases](https://github.com/0xlay/ToneGrab/releases)

## License

MIT License - Copyright (c) 2025 [0xlay](https://github.com/0xlay)

---

Made with ❤️ by [0xlay](https://github.com/0xlay)

# Detailed Installation Guide

This guide provides step-by-step instructions for setting up Discord TTS App from source.

## Prerequisites

1. **Python 3.7 or higher**
   - Download from [python.org](https://www.python.org/downloads/)
   - During installation, check "Add Python to PATH"

2. **FFmpeg**
   - Download the static build from [ffmpeg.org](https://ffmpeg.org/download.html) or [gyan.dev](https://www.gyan.dev/ffmpeg/builds/)
   - We recommend the "essentials" build for Windows
   - Extract `ffmpeg.exe` and `ffprobe.exe` to your project directory

3. **VB-Cable Virtual Audio Device**
   - Download from [VB-Audio website](https://vb-audio.com/Cable/)
   - Run the installer as administrator

## Installation Steps

### Step 1: Clone or Download the Repository

```bash
git clone https://github.com/username/discord-tts.git
cd discord-tts
```

Or download the ZIP file from GitHub and extract it.

### Step 2: Set Up a Virtual Environment (Recommended)

```bash
python -m venv venv
```

Activate the virtual environment:
- Windows: `venv\Scripts\activate`
- macOS/Linux: `source venv/bin/activate`

### Step 3: Install Required Packages

```bash
pip install -r requirements.txt
```

### Step 4: Place FFmpeg Files

Copy `ffmpeg.exe` and `ffprobe.exe` to the same directory as `discord_tts_app.py`.

### Step 5: Run the Application

```bash
python discord_tts_app.py
```

## Setting Up with Discord

1. Open Discord and join a voice channel
2. Open Discord Settings → Voice & Video
3. Set Input Device to "CABLE Output (VB-Audio Virtual Cable)"
4. Make sure Discord is set to Voice Activity mode (not Push-to-Talk)

## Troubleshooting

### Application Won't Start

- Ensure all required dependencies are installed: `pip install -r requirements.txt`
- Confirm that Python is in your PATH
- Check if you're using the correct Python version (3.7+)

### Missing FFmpeg Errors

- Verify that `ffmpeg.exe` and `ffprobe.exe` are in the same directory as the application
- Ensure they are correctly named and executable

### No Audio in Discord

- Make sure VB-Cable is properly installed
- Check that Discord is using "CABLE Output" as its input device
- Ensure Discord voice activity is enabled rather than push-to-talk

### Voice Loading Issues

- Check your internet connection (voices are loaded from Microsoft's servers)
- Try restarting the application
- Make sure Edge TTS is properly installed: `pip install edge-tts --upgrade` 
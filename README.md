# Discord TTS App

A desktop application that allows users to convert text to speech and route it to Discord voice channels, perfect for users without a microphone or those who prefer typing over speaking.

![Discord TTS App](https://raw.githubusercontent.com/user/discord-tts/main/screenshot.png)

## Features

- **Text-to-Speech with Microsoft Edge TTS**: High-quality, natural-sounding voices
- **Multi-language Support**: English, Chinese, Japanese, Korean, Spanish, French, German, Russian, and more
- **Voice Selection**: Multiple voice options for each language
- **Speech Rate Control**: Adjust the speaking speed
- **Message History**: Access previously sent messages
- **Audio Monitoring**: Listen to the output before sending to Discord
- **Simple and Modern UI**: Clean interface powered by CustomTkinter

## How It Works

This application uses Microsoft Edge TTS to generate speech from text, then routes the audio to Discord through a virtual audio device. Discord receives this audio as if it were coming from a microphone.

## Prerequisites

- Windows 10/11
- Python 3.7 or higher
- VB-Cable Virtual Audio Device (included in installer)
- FFmpeg (required for audio processing)

## Installation

### Option 1: Pre-built Installer (Windows)

1. Download the latest installer from the [Releases](https://github.com/username/discord-tts/releases) page
2. Run the installer, which will:
   - Install the application
   - Set up the VB-Cable virtual audio device
   - Create start menu shortcuts

### Option 2: From Source

1. Clone this repository:
   ```
   git clone https://github.com/username/discord-tts.git
   cd discord-tts
   ```

2. Create and activate a virtual environment (recommended):
   ```
   python -m venv venv
   venv\Scripts\activate
   ```

3. Install required packages:
   ```
   pip install -r requirements.txt
   ```

4. Download required external dependencies:
   - **FFmpeg**: Download the static build from [ffmpeg.org](https://ffmpeg.org/download.html) or [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and extract `ffmpeg.exe` and `ffprobe.exe` to the project directory
   - **VB-Cable**: Install from [VB-Audio website](https://vb-audio.com/Cable/)

5. Run the application:
   ```
   python discord_tts_app.py
   ```

## Setting Up with Discord

1. Open Discord and join a voice channel
2. Open Discord Settings → Voice & Video
3. Set Input Device to "CABLE Output (VB-Audio Virtual Cable)"
4. Make sure Discord is set to Voice Activity mode (not Push-to-Talk)

## Usage

1. Launch Discord TTS App
2. Select your audio devices:
   - Discord Output: Set to CABLE Input (VB-Audio Virtual Cable)
   - Monitor Output: Set to your headphones/speakers
3. Choose your preferred language and voice
4. Type your message in the text box
5. Click "Speak in Discord" or press Enter to send the audio to Discord

## Project Structure

Key files in this repository:
- `discord_tts_app.py` - Main application file
- `subprocess_wrapper.py` - Helper for hiding console windows
- `requirements.txt` - Python dependencies
- `icon.ico` - Application icon
- `build.bat` - Simple build script for PyInstaller

You'll need to obtain the following files separately (not included due to size):
- `ffmpeg.exe` - For audio processing 
- `ffprobe.exe` - For audio file analysis

## Building from Source

To create a standalone executable:

```
pip install pyinstaller
pyinstaller --onefile --windowed --icon=icon.ico --name discord_tts_app --add-binary "ffmpeg.exe;." --add-binary "ffprobe.exe;." --add-data "subprocess_wrapper.py;." --add-data "icon.ico;." discord_tts_app.py
```

Alternatively, you can use the included `build.bat` script.

## Troubleshooting

- **No audio in Discord**: Make sure VB-Cable is installed and you've selected the correct devices in both Discord and this app
- **Missing FFmpeg**: Make sure you've downloaded and placed `ffmpeg.exe` and `ffprobe.exe` in the same directory as the application
- **Laggy audio**: Try adjusting the buffer size in the settings
- **Application crashes**: Ensure you have all the required dependencies installed

## License

This project is released under the MIT License. See the LICENSE file for details.

## Acknowledgements

- [Microsoft Edge TTS](https://github.com/rany2/edge-tts) for the TTS engine
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the modern UI
- [VB-Audio](https://vb-audio.com) for the virtual audio device
- [FFmpeg](https://ffmpeg.org/) for audio processing 
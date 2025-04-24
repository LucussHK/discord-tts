# Discord TTS App

A desktop application that converts text into speech and routes it to Discord voice chat.  
Perfect for users who don’t have a microphone, can’t speak at the moment, or simply prefer typing over talking — this app helps everyone stay part of the voice chat experience.

While designed with Discord in mind, the app can be used with **any application that accepts voice input**, thanks to its flexible audio routing options.

![Discord TTS App](https://github.com/user-attachments/assets/351b3f2d-7918-4f60-9d4c-0e428e8cd50f)

## Features

- **Text-to-Speech with Microsoft Edge TTS**: High-quality, natural-sounding voices
- **Multilanguage Support**: English and Chinese (Simplified, Traditional, Hong Kong). You can easily add more languages by editing the `supported_locales` list in the source code.
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

1. Download the latest installer from the [Releases](https://github.com/LucussHK/discord-tts/releases) page
2. Run the installer, which will:
   - Install the application
   - Set up the VB-Cable virtual audio device
   - Create start menu shortcuts

### Option 2: From Source

1. Clone this repository:
   ```
   git clone https://github.com/LucussHK/discord-tts.git
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

## 🎙️ Important Audio Setup Note

To make sure your voice is sent to Discord correctly:

- In **Discord**, go to **Settings → Voice & Video**
- Under **Input Device**, select:

  ![Discord Input Device](https://github.com/user-attachments/assets/80917fcb-4de3-49ac-a27a-986091a6670b)  
  *(Default (CABLE Output (VB-Audio Virtual Cable)))*

> ⚠️ **Important:** Do **not** change the **"Output Device"** in Discord unless you know exactly what you’re doing.  
> It should remain your regular speakers or headphones so you can still hear others clearly during voice chats.

💡 Bonus Tip: This app can also be used in **any other application that accepts voice input**, such as **Zoom**, **Skype**, or **VRChat** — just select the **VB-Cable** as your microphone input.


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

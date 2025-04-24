# Discord TTS Full Installer Guide

This guide explains how to build a complete installer for Discord TTS that includes the application and VB-Cable drivers.

## Prerequisites

1. **Python Environment**: Make sure you have all the required Python packages installed:
   ```
   pip install -r requirements.txt
   ```

2. **Inno Setup**: You must have Inno Setup 6 installed on your system. You can download it from:
   [https://jrsoftware.org/isdl.php](https://jrsoftware.org/isdl.php)

3. **VB-Cable**: The VBCABLE directory with all required drivers must be present in the project folder.

4. **FFmpeg and FFprobe**: Both files must be present in the same directory as your Python script.

## Building the Installer

Running the installer build process is simple:

1. Just run the `build_with_installer.bat` script:
   ```
   build_with_installer.bat
   ```

2. The script will:
   - Clean up previous builds
   - Build an optimized single-file executable using PyInstaller
   - Create an Inno Setup script
   - Compile the installer that includes the application and VB-Cable drivers

3. When complete, you'll find `DiscordTTS_Installer.exe` in your project directory.

## What the Installer Does

When users run the installer:

1. It will install Discord TTS to the Program Files folder
2. Install VB-Cable virtual audio device drivers
3. Create start menu and desktop shortcuts
4. Offer to launch the application immediately after installation

## Troubleshooting

If you encounter issues:

- **Missing FFmpeg**: Make sure ffmpeg.exe and ffprobe.exe are in the same directory as discord_tts_app.py
- **Missing VB-Cable**: Ensure the VBCABLE directory contains all the required driver files
- **Inno Setup Not Found**: Make sure Inno Setup is installed and either in your PATH or in the default Program Files location
- **Build Failures**: Check the console output for specific error messages

### Common Runtime Errors

- **ModuleNotFoundError: No module named '_tkinter'**: If you get this error when running the installed application, it means Tkinter modules were excluded during packaging. Fix the build script by removing '_tkinter' and 'Tkinter' from the excludes list in the script, then rebuild.

- **ModuleNotFoundError: No module named 'PIL'**: This error occurs because the CTkMessagebox component requires the Python Imaging Library (Pillow). To fix this:
  1. Remove 'PIL' from the excluded modules list in the build script
  2. Add 'PIL', 'PIL._imagingtk', 'PIL._tkinter_finder', and 'pillow' to the hidden imports
  3. Make sure Pillow is installed in your Python environment (`pip install pillow`)
  4. Rebuild the installer with the updated script

- **Missing DLLs**: Make sure you're using the latest version of the build script, which includes all necessary hidden imports.

## Distribution

The final installer:

- Is fully self-contained
- Requires administrator privileges (for driver installation)
- Works on Windows 10/11 (x64)
- Includes all necessary dependencies
- Will install VB-Cable automatically

## Customization

If you want to customize the installer:

- Edit the `build_with_installer.bat` file to change the Inno Setup script parameters
- Modify the application icon by placing an `app_icon.ico` file in the project directory
- Change the version number by editing the `AppVersion` value in the generated setup script 
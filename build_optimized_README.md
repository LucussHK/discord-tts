# Discord TTS Build Optimization

This README explains the optimized build process for the Discord TTS application.

## What does `build_optimized.bat` do?

The batch script creates an optimized PyInstaller package that:

1. Builds a single-file executable for easier distribution
2. Properly includes FFmpeg and FFprobe
3. Eliminates console flashing
4. Minimizes application size by excluding unnecessary modules
5. Improves startup performance
6. Includes all necessary dependencies

## Key Optimizations

- **Single-file Build**: Creates a single executable instead of a directory of files
- **Subprocess Handling**: FFmpeg console windows are suppressed (already handled in the main code)
- **Hidden Imports**: Includes critical numpy random modules
- **Module Exclusion**: Removes unused modules (Tkinter, enchant, twisted, etc.)
- **UPX Compression**: Enables binary compression for smaller file size
- **Icon Support**: Includes app icon if available
- **No Console**: Disables console window completely
- **Environment Integration**: Automatically activates virtual environment if present

## Usage

1. Make sure you have PyInstaller installed:
   ```
   pip install pyinstaller
   ```

2. Make sure FFmpeg and FFprobe are in the same directory as the script

3. Run the batch file:
   ```
   build_optimized.bat
   ```

4. The optimized executable will be created at:
   ```
   dist/Discord TTS.exe
   ```

## Troubleshooting

If the build fails:

1. Check that all dependencies are installed in your Python environment
2. Ensure FFmpeg and FFprobe are present in the correct location
3. Review any error messages in the console output
4. Make sure the virtual environment is activated (if using one)

## Additional Notes

- The script generates a new spec file called `discord_tts_optimized.spec`
- Existing build folders are cleared before running to prevent conflicts
- The script checks for and includes an app icon file if available

This optimized build significantly improves startup time and eliminates any console flashing that might occur during FFmpeg operations. 
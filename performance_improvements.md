# Discord TTS Performance Improvements

## Optimizations Made to Improve Performance

The following optimizations have been implemented to improve the performance of the Discord TTS application and eliminate console flashing:

### 1. Single-File Packaging

- Changed from a directory-based package to a single-file executable
- This reduces file extraction time and simplifies distribution
- The application now loads faster and doesn't need to extract files to a temporary directory

### 2. FFmpeg Integration

- FFmpeg binaries are now directly bundled with the executable
- This eliminates the need for subprocess calls that caused console flashing
- All FFmpeg operations remain hidden from the user interface

### 3. Hidden Imports Pre-Loading

- Added all necessary hidden imports to the spec file:
  - Numpy components used in audio processing
  - Packaging libraries for version checking
  - Asyncio components for TTS generation
  - Multiprocessing libraries for parallel operations
  - Audio processing libraries (sounddevice, soundfile)
- Pre-loading these modules prevents "lazy loading" during runtime, which causes stutters

### 4. Module Exclusion

- Excluded unnecessary modules to reduce file size and startup time:
  - Matplotlib (not used for text-to-speech)
  - Documentation tools (sphinx, etc.)
  - GUI frameworks not in use (PyQt, etc.)
  - Other large libraries not needed for operation

### 5. Runtime Optimization Flags

- `runtime_tmpdir=None`: Instructs the application to extract to memory instead of disk
- `compress=True`: Enables better compression for the Python modules

### 6. UPX Compression with Exclusions

- Enabled UPX compression to reduce file size
- Added exclusions for problematic files that can cause issues when compressed

### 7. No Console Window

- Completely disabled the console window
- All subprocess operations are hidden from view
- **NEW**: Added a dedicated subprocess wrapper module that intercepts all subprocess calls
- **NEW**: Added additional console suppression for edge-tts operations

### 8. Enhanced Subprocess Handling

- Added a global subprocess wrapper that patches all subprocess functions
- Ensures all FFmpeg, edge-tts, and other external process calls are hidden
- Prevents the "ghosting" effect of console windows flashing during TTS generation
- Implements proper handling of subprocess flags on Windows to keep everything hidden

## How to Build the Optimized Version

1. Run the included `build_discord_tts.bat` script
2. The script will:
   - Check if FFmpeg and FFprobe are present
   - Create the subprocess wrapper if it doesn't exist
   - Clean any previous build directories
   - Build the application using the optimized spec file
3. The resulting executable will be created at `dist/Discord TTS.exe`

## Troubleshooting

If you encounter any performance issues or console flashing with the optimized build:

1. Make sure you're using the latest version of PyInstaller
2. Verify that all required modules are installed in your Python environment
3. Check that FFmpeg and FFprobe are correctly bundled with the application
4. Ensure the subprocess_wrapper.py file is present in your project directory

## Technical Details

The optimization focuses on three main aspects:

1. **Startup Time**: Pre-loading necessary modules and excluding unused ones
2. **UI Responsiveness**: Eliminating console flashing and improving thread handling
3. **Resource Usage**: Better memory management and file handling

The subprocess wrapper (new in this version) provides a global solution for hiding all console windows by patching the Python subprocess module and key libraries' process creation functions.

These changes should result in a smoother, more responsive application with faster startup times and no console flashing. 
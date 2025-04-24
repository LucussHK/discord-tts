@echo off
setlocal enableextensions

REM ----------------------------------------
REM Build script for Discord TTS App
REM ----------------------------------------

REM Jump to the script folder
cd /d "%~dp0"

REM Activate venv if present
if exist "venv\Scripts\activate.bat" (
  echo Activating virtual environment...
  call "venv\Scripts\activate.bat"
) else (
  echo WARNING: venv not found, using system Python
)

REM Clean old builds
if exist build rd /s /q build
if exist dist  rd /s /q dist

REM Build single-file EXE with icon.ico bundled
echo Building Discord TTS executable...
pyinstaller ^
  --clean ^
  --onefile ^
  --windowed ^
  --name discord_tts_app ^
  --icon "icon.ico" ^
  --add-data "icon.ico;."          ^
  --add-binary "ffmpeg.exe;."      ^
  --add-binary "ffprobe.exe;."     ^
  --add-data "subprocess_wrapper.py;." ^
  discord_tts_app.py
if errorlevel 1 (
  echo PyInstaller build FAILED.
  pause
  exit /b 1
)

REM Verify the EXE exists
if not exist "dist\discord_tts_app.exe" (
  echo ERROR: dist\discord_tts_app.exe not found.
  pause
  exit /b 1
)

echo.
echo ================================================
echo   🎉 Build complete!
echo.
echo   • Executable: dist\discord_tts_app.exe
echo ================================================
pause 
@echo off
echo ==============================================================
echo  Cleaning up project directory for GitHub
echo ==============================================================
echo.

echo Removing build directories...
if exist build rd /s /q build
if exist dist rd /s /q dist
echo.

echo Removing spec files...
del /f /q *.spec 2>nul
echo.

echo Removing installer files...
del /f /q DiscordTTS_Installer.exe 2>nul
del /f /q setup.iss 2>nul
del /f /q setup_optimized.iss 2>nul
echo.

echo Removing unused build scripts...
del /f /q build_discord_tts.bat 2>nul
del /f /q build_optimized.bat 2>nul
del /f /q build_with_installer.bat 2>nul
del /f /q check_pyinstaller.bat 2>nul
del /f /q simple_build.bat 2>nul
echo.

echo Removing Python cache files...
if exist __pycache__ rd /s /q __pycache__
echo.

echo Retaining essential files:
echo  - discord_tts_app.py (main application)
echo  - subprocess_wrapper.py (helper module) 
echo  - icon.ico (application icon)
echo  - requirements.txt (dependencies)
echo  - build.bat (simple build script)
echo  - README.md, LICENSE, .gitignore
echo.

echo ==============================================================
echo NOTE: The following essential files are EXCLUDED from git:
echo  - ffmpeg.exe and ffprobe.exe 
echo  - These must be downloaded separately as described in README
echo ==============================================================
echo.

pause 
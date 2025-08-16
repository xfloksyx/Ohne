@echo off
cd /d "%~dp0"

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Add current folder to PATH so ffmpeg/yt-dlp can be found
set PATH=%CD%;%PATH%

REM Run the app
python app.py
pause

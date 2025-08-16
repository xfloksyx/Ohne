@echo off
REM -----------------------------
REM Ohne - Only Vocals
REM -----------------------------

REM Change to script directory
cd /d "%~dp0"

REM Add current folder to PATH so ffmpeg/yt-dlp can be found
set PATH=%CD%;%PATH%

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the app
python app.py
pause

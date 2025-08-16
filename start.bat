@echo off
REM -----------------------------
REM Ohne - Only Vocals Installer
REM -----------------------------

cd /d "%~dp0"

echo 🎵 Ohne - Only Vocals Setup
echo ==========================

REM -----------------------------
REM Step 1: Create virtual environment
REM -----------------------------
echo [1/5] Creating virtual environment...
python -m venv venv

REM -----------------------------
REM Step 2: Activate virtual environment
REM -----------------------------
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat

REM -----------------------------
REM Step 3: Install Python requirements
REM -----------------------------
echo [3/5] Installing Python requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

REM -----------------------------
REM Step 4: Download ffmpeg and yt-dlp binaries
REM -----------------------------
echo [4/5] Downloading dependencies...

if not exist ffmpeg.exe (
    echo Downloading ffmpeg...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'"
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath '.' -Force"
    move ffmpeg-master-latest-win64-gpl\bin\ffmpeg.exe .
    move ffmpeg-master-latest-win64-gpl\bin\ffprobe.exe .
    rmdir /s /q ffmpeg-master-latest-win64-gpl
    del ffmpeg.zip
    echo ✅ FFmpeg installed
) else (
    echo ✅ FFmpeg already exists
)

if not exist yt-dlp.exe (
    echo Downloading yt-dlp...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe' -OutFile 'yt-dlp.exe'"
    echo ✅ yt-dlp installed
) else (
    echo ✅ yt-dlp already exists
)

REM -----------------------------
REM Step 5: Create run script
REM -----------------------------
echo [5/5] Creating run script...
echo @echo off > run.bat
echo cd /d "%%~dp0" >> run.bat
echo call venv\Scripts\activate.bat >> run.bat
echo python app.py >> run.bat

echo.
echo 🎉 Installation complete!
echo.
echo To start the app:
echo   run.bat
echo.
echo Or manually:
echo   venv\Scripts\activate.bat
echo   python app.py

pause

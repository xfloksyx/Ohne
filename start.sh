#!/bin/bash
# -----------------------------
# Ohne - Only Vocals Starter
# -----------------------------

cd "$(dirname "$0")"

# -----------------------------
# Step 1: Create virtual environment
# -----------------------------
echo "[1/5] Creating virtual environment..."
python3 -m venv venv

# -----------------------------
# Step 2: Activate virtual environment
# -----------------------------
echo "[2/5] Activating virtual environment..."
source venv/bin/activate

# -----------------------------
# Step 3: Install Python requirements
# -----------------------------
echo "[3/5] Installing Python requirements..."
pip install --upgrade pip
pip install -r requirements.txt

# -----------------------------
# Step 4: Download ffmpeg and yt-dlp binaries
# -----------------------------
echo "[4/5] Downloading ffmpeg and yt-dlp binaries..."

# FFmpeg
# FFmpeg
if [ ! -f ffmpeg ]; then
    echo "Downloading ffmpeg..."
    wget -O ffmpeg-release.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
    # Extract ffmpeg binary using wildcards
    tar -xJf ffmpeg-release.tar.xz --strip-components=1 --wildcards '*/ffmpeg'
    rm ffmpeg-release.tar.xz
    chmod +x ffmpeg
else
    echo "ffmpeg already exists"
fi

# yt-dlp
if [ ! -f yt-dlp ]; then
    echo "Downloading yt-dlp..."
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp
    chmod +x yt-dlp
else
    echo "yt-dlp already exists"
fi

# -----------------------------
# Step 5: Start the app
# -----------------------------
echo "[5/5] Starting Ohne app..."
python3 app.py

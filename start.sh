#!/bin/bash
# -----------------------------
# Ohne - Only Vocals Installer
# -----------------------------

set -e
cd "$(dirname "$0")"

echo "🎵 Ohne - Only Vocals Setup"
echo "=========================="

# -----------------------------
# Step 0: Install system dependencies
# -----------------------------
echo "[0/6] Checking system dependencies..."

# Check if we're on Ubuntu/Debian and install required packages
if command -v apt-get >/dev/null 2>&1; then
    echo "Detected Debian/Ubuntu system. Installing required packages..."
    
    # Update package list
    sudo apt-get update
    
    # Install required system packages including tkinter
    sudo apt-get install -y python3-venv python3-pip python3-tk curl wget unzip
    
    echo "✅ System packages installed"
elif command -v yum >/dev/null 2>&1; then
    echo "Detected Red Hat/CentOS system. Installing required packages..."
    sudo yum install -y python3-venv python3-pip python3-tkinter curl wget unzip
    echo "✅ System packages installed"
elif command -v brew >/dev/null 2>&1; then
    echo "Detected macOS with Homebrew. Ensuring dependencies..."
    brew install python3 curl wget
    echo "✅ System packages verified"
else
    echo "⚠️  Could not detect package manager. Please ensure python3-venv is installed."
fi

# -----------------------------
# Step 1: Create virtual environment
# -----------------------------
echo "[1/6] Creating virtual environment..."
python3 -m venv venv

# -----------------------------
# Step 2: Activate virtual environment
# -----------------------------
echo "[2/6] Activating virtual environment..."
source venv/bin/activate

# -----------------------------
# Step 3: Install Python requirements
# -----------------------------
echo "[3/6] Installing Python requirements..."
pip install --upgrade pip

# Install requirements with better error handling
if ! pip install -r requirements.txt; then
    echo "❌ Failed to install some requirements. Trying alternative approach..."
    
    # Install core dependencies individually
    pip install "customtkinter>=5.2.0,<6.0.0"
    pip install "Pillow>=9.0.0,<11.0.0"
    pip install "yt-dlp>=2023.7.6"
    
    # Install PyTorch with CPU-only version for better compatibility
    pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    
    # Install demucs
    pip install "demucs>=4.0.0,<5.0.0"
    
    echo "✅ Requirements installed with fallback method"
else
    echo "✅ Requirements installed successfully"
fi

# -----------------------------
# Step 4: Download ffmpeg and yt-dlp binaries
# -----------------------------
echo "[4/6] Downloading dependencies..."

# Create downloads directory
mkdir -p downloads

# ffmpeg + ffprobe
if [ ! -f ffmpeg ] || [ ! -f ffprobe ]; then
    echo "Downloading ffmpeg..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        curl -L https://evermeet.cx/ffmpeg/ffmpeg-5.1.2.zip -o downloads/ffmpeg.zip
        unzip -o downloads/ffmpeg.zip -d downloads/
        mv downloads/ffmpeg .
        curl -L https://evermeet.cx/ffmpeg/ffprobe-5.1.2.zip -o downloads/ffprobe.zip
        unzip -o downloads/ffprobe.zip -d downloads/
        mv downloads/ffprobe .
    else
        # Linux
        wget -O downloads/ffmpeg-release.tar.xz https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz
        tar -xf downloads/ffmpeg-release.tar.xz -C downloads/
        mv downloads/ffmpeg-*-amd64-static/ffmpeg .
        mv downloads/ffmpeg-*-amd64-static/ffprobe .
        rm -rf downloads/ffmpeg-*-amd64-static
    fi
    chmod +x ffmpeg ffprobe
    echo "✅ FFmpeg installed"
else
    echo "✅ FFmpeg already exists"
fi
export PATH="$(pwd):$PATH"
# yt-dlp
if [ ! -f yt-dlp ]; then
    echo "Downloading yt-dlp..."
    curl -L https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp -o yt-dlp
    chmod +x yt-dlp
    echo "✅ yt-dlp installed"
else
    echo "✅ yt-dlp already exists"
fi

# Clean up downloads
rm -rf downloads/

# -----------------------------
# Step 5: Create run script
# -----------------------------
echo "[5/6] Creating run script..."
cat > run.sh << 'EOF'
#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
export PATH="$(pwd):$PATH"
python3 app.py
EOF
chmod +x run.sh

# -----------------------------
# Step 6: Verify installation
# -----------------------------
echo "[6/6] Verifying installation..."
if [ -f "app.py" ] && [ -f "ffmpeg" ] && [ -f "yt-dlp" ] && [ -d "venv" ]; then
    echo "✅ All components verified"
else
    echo "⚠️  Some components may be missing. Check the installation."
fi

echo ""
echo "🎉 Installation complete!"
echo ""
echo "To start the app:"
echo "  ./run.sh"
echo ""
echo "Or manually:"
echo "  source venv/bin/activate"
echo "  python3 app.py"

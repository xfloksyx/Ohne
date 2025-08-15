#!/bin/bash
cd "$(dirname "$0")"

# --- Check for tkinter ---
if ! python3 -c "import tkinter" &> /dev/null; then
    echo "[0/3] tkinter not found. Installing..."
    if [ -x "$(command -v apt)" ]; then
        sudo apt update
        sudo apt install -y python3-tk
    elif [ -x "$(command -v dnf)" ]; then
        sudo dnf install -y python3-tkinter
    elif [ -x "$(command -v pacman)" ]; then
        sudo pacman -S --noconfirm tk
    else
        echo "Package manager not found. Please install tkinter manually."
        exit 1
    fi
fi

echo "[1/3] Creating virtual environment..."
python3 -m venv venv

echo "[2/3] Installing requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/3] Starting application..."
python3 app.py

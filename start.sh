#!/bin/bash
cd "$(dirname "$0")"

echo "[1/3] Creating virtual environment..."
python3 -m venv venv

echo "[2/3] Installing requirements..."
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "[3/3] Starting application..."
python3 app.py

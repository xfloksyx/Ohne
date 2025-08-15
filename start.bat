@echo off
cd /d "%~dp0"

echo [1/3] Creating virtual environment...
python -m venv venv

echo [2/3] Installing requirements...
call venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt

echo [3/3] Starting application...
python app.py

pause

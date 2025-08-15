@echo off
title Ohne App
echo =======================================
echo   Starting Ohne Application...
echo =======================================
echo.

REM Step 1: Check if virtual environment exists
if not exist venv (
    echo Creating virtual environment...
    python -m venv venv
)

REM Step 2: Activate venv
call venv\Scripts\activate

REM Step 3: Install dependencies
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

REM Step 4: Run the application
echo Running application...
python app.py

REM Keep console open after closing app
pause

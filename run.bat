@echo off
setlocal enabledelayedexpansion

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed. Please install Python and add it to PATH.
    exit /b 1
)

REM Check if Git is installed
git --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Git is not installed. Please install Git and add it to PATH.
    exit /b 1
)

REM Check for updates
echo Checking for updates...
git pull

REM Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
) else (
    echo Virtual environment already exists.
)

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Check if requirements.txt exists
if exist requirements.txt (
    echo Installing dependencies...
    pip install -r requirements.txt
) else (
    echo requirements.txt does not exist. Skipping dependency installation.
)

echo "Setup complete."
echo "Please make sure you have created OpenRouter API key and set it in the environment variables. (.env file)"

REM Run src/ui.py
if exist src\ui.py (
    echo Running src/ui.py...
    python src\ui.py
) else (
    echo src\ui.py does not exist. Please make sure the file exists.
)

REM Deactivate virtual environment
deactivate

pause

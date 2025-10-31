#!/bin/bash

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python is not installed. Please install Python 3."
    exit 1
fi

# Check if Git is installed
if ! command -v git &> /dev/null; then
    echo "Git is not installed. Please install Git."
    exit 1
fi

# Check for updates
echo "Checking for updates..."
git pull

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
else
    echo "Virtual environment already exists."
fi

# Activate virtual environment
source .venv/bin/activate

# Check if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
else
    echo "requirements.txt does not exist. Skipping dependency installation."
fi

echo "Setup complete."
echo "Please make sure you have created Google Cloud Vision API key and OpenRouter API key and set them in the environment variables. (.env file)"

# Run src/ui.py
if [ -f "src/ui.py" ]; then
    echo "Running src/ui.py..."
    python src/ui.py
else
    echo "src/ui.py does not exist. Please make sure the file exists."
fi

# Deactivate virtual environment
deactivate


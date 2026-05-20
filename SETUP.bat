@echo off
title TCE Engine - First Time Setup
color 1F

echo.
echo  ==================================================
echo    TCE Financial Statement Engine - SETUP
echo    TrustFactON Compliance Engine
echo  ==================================================
echo.

cd /d "%~dp0"

echo  [1/4] Checking Python...
python --version
if errorlevel 1 (
    echo.
    echo  ERROR: Python not found. Please install Python first.
    echo  Download from: https://www.python.org/downloads/
    echo  IMPORTANT: Check "Add python.exe to PATH" during install!
    echo.
    pause
    exit /b 1
)

echo.
echo  [2/4] Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo  ERROR: pip install failed. Check your internet connection.
    pause
    exit /b 1
)

echo.
echo  [3/4] Creating data directories...
if not exist "data" mkdir data
if not exist "output" mkdir output

echo.
echo  [4/4] Creating Desktop shortcut...
python create_shortcut.py

echo.
echo  ==================================================
echo    SETUP COMPLETE!
echo.
echo    To start TCE Engine:
echo      Option A: Double-click "TCE Engine" on Desktop
echo      Option B: Double-click "TCE Engine.bat" in this folder
echo.
echo    First run will seed 248 CoA codes automatically.
echo  ==================================================
echo.
pause

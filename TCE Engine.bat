@echo off
title TCE Financial Statement Engine - TrustFactON
color 1F

echo.
echo  ==================================================
echo    TCE Financial Statement Engine v3.0
echo    TrustFactON Compliance Engine
echo    Evenset Consultancy Services OPC Pvt Ltd
echo  ==================================================
echo.
echo  Starting server...
echo  Dashboard will open in your browser automatically.
echo.
echo  To stop: Press Ctrl+C or close this window.
echo  ==================================================
echo.

cd /d "%~dp0"
python run.py

pause

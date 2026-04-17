@echo off
title Glory Car Racing Server
echo Installing dependencies...
pip install -r requirements.txt -q
echo.
echo Starting server...
python server.py
pause

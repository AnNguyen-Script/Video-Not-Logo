@echo off
setlocal EnableExtensions
chcp 65001 >nul
title Tool Tai Video PRO MAX - GUI Launcher
cd /d "%~dp0"

py --version >nul 2>&1
if not errorlevel 1 (
    start "" py gui_downloader.py
    exit /b 0
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    start "" py -3 gui_downloader.py
    exit /b 0
)

python --version >nul 2>&1
if not errorlevel 1 (
    start "" python gui_downloader.py
    exit /b 0
)

echo [LOI] Khong tim thay Python tren he thong!
echo Hay thu chay start.bat de duoc huong dan chi tiet.
pause
exit /b 1

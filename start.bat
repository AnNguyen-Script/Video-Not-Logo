@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Tool Tai Video PRO MAX v4.0 - (c) An Nguyen
cd /d "%~dp0"

echo.
echo ============================================================
echo    TOOL TAI VIDEO PRO MAX v4.0 - AN NGUYEN (c) 2026
echo    YouTube * TikTok * Facebook * Instagram * Douyin * 1000+
echo ============================================================
echo.

REM --- BUOC 1: KIEM TRA PYTHON ---
echo [....] Dang kiem tra Python...
set "PYTHON="

py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=py"
    goto :python_ok
)

py -3 --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=py -3"
    goto :python_ok
)

python --version >nul 2>&1
if not errorlevel 1 (
    python -c "import sys" >nul 2>&1
    if not errorlevel 1 set "PYTHON=python"
)

if not defined PYTHON goto :no_python

:python_ok
for /f "tokens=*" %%v in ('%PYTHON% --version 2^>^&1') do set "PYVER=%%v"
echo [OK]   Tim thay %PYVER%

REM --- BUOC 2: KIEM TRA THU VIEN ---
echo [....] Dang kiem tra cac thu vien can thiet...
%PYTHON% -c "import yt_dlp, rich, requests, fastapi, uvicorn, websockets" >nul 2>&1
if not errorlevel 1 (
    echo [OK]   Thu vien da day du.
    goto :check_ffmpeg
)

echo [SETUP] Thieu thu vien. Dang tu dong cai dat/nang cap...
%PYTHON% -m pip install --upgrade -r requirements.txt
if errorlevel 1 (
    echo [CANH BAO] Pip gap loi, thu tu sua bang ensurepip...
    %PYTHON% -m ensurepip --upgrade >nul 2>&1
    %PYTHON% -m pip install --upgrade -r requirements.txt
    if errorlevel 1 goto :pip_fail
)
echo [OK]   Cai dat thu vien thanh cong!

REM --- BUOC 3: KIEM TRA FFMPEG ---
:check_ffmpeg
echo [....] Dang kiem tra bo giai ma FFmpeg...
if exist "bin\ffmpeg.exe" (
    echo [OK]   FFmpeg Portable noi bo da san sang (bin\ffmpeg.exe).
    goto :ready_menu
)

where ffmpeg >nul 2>&1
if not errorlevel 1 (
    echo [OK]   FFmpeg trong he thong PATH da san sang.
    goto :ready_menu
)

if exist "%LOCALAPPDATA%\Microsoft\WinGet\Links\ffmpeg.exe" (
    echo [OK]   FFmpeg WinGet da san sang.
    goto :ready_menu
)

echo [!]    Chua phat hien FFmpeg tren may.
echo        (Tool van chay duoc nhung se khong gop duoc video 4K/1080p va MP3)

:ready_menu
echo.
REM Neu co tham so truyen vao tu dong chay truc tiep CLI
if not "%~1"=="" (
    %PYTHON% video_downloader.py %*
    goto :end_app
)

echo ------------------------------------------------------------
echo  CHON CHE DO KHOI CHAY:
echo ------------------------------------------------------------
echo   [1] WEB APP (Cuc bo / Mang LAN WiFi)
echo   [2] WEB APP - LINK CONG KHAI (Chia se Internet toan cau)
echo   [3] Giao dien Dong lenh (CLI Rich Console)
echo   [4] Giao dien Do hoa Cua so (GUI PySide Desktop)
echo   [5] Tu dong tai FFmpeg Portable vao thu muc bin\
echo   [6] Cap nhat bo thu vien moi nhat (yt-dlp, rich...)
echo   [7] Thoat
echo ------------------------------------------------------------
set /p "CHOICE= Nhap lua chon cua ban [1-7] (Mac dinh: 1): "
if "%CHOICE%"=="" set "CHOICE=1"

if "%CHOICE%"=="1" (
    cls
    start_web.bat
    goto :end_app
)

if "%CHOICE%"=="2" (
    cls
    start_public_web.bat
    goto :end_app
)

if "%CHOICE%"=="3" (
    cls
    %PYTHON% video_downloader.py
    goto :end_app
)

if "%CHOICE%"=="4" (
    echo Dang mo giao dien do hoa...
    start "" %PYTHON% gui_downloader.py
    exit /b 0
)

if "%CHOICE%"=="5" (
    %PYTHON% -c "import engine; engine.download_portable_ffmpeg()"
    pause
    cls
    goto :check_ffmpeg
)

if "%CHOICE%"=="6" (
    echo Dang cap nhat thu vien...
    %PYTHON% -m pip install --upgrade -r requirements.txt
    pause
    cls
    goto :ready_menu
)

if "%CHOICE%"=="7" exit /b 0

cls
start_web.bat

:end_app
set "RC=%errorlevel%"
if "%RC%"=="0" (
    echo.
    echo [OK] Tool da hoan tat.
    timeout /t 3 >nul
    exit /b 0
)

echo.
echo ============================================================
echo  [LOI] CHUONG TRINH DUNG LAI VOI MA LOI: %RC%
echo ============================================================
pause
exit /b %RC%

:no_python
echo.
echo ============================================================
echo  [LOI] KHONG TIM THAY PYTHON TREN MAY!
echo ============================================================
echo  Vui long tai va cai dat Python tai: https://www.python.org/downloads/
echo  LUU Y: Khi cai dat, nho tich chon "Add Python to PATH"
echo.
pause
exit /b 1

:pip_fail
echo.
echo ============================================================
echo  [LOI] CAI DAT THU VIEN THAT BAI!
echo ============================================================
echo  Kiem tra ket noi internet va thu chay thu cong lenh:
echo  py -m pip install -U -r requirements.txt
echo.
pause
exit /b 1

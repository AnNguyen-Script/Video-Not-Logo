@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Tool Tai Video PRO MAX v3.0.0 ULTRA STUDIO - (c) An Nguyen
cd /d "%~dp0"

echo.
echo ============================================================
echo    TOOL TAI VIDEO PRO MAX v3.0.0 - ULTRA STUDIO EDITION
echo    (c) Ban quyen: An Nguyen (2026)
echo    Atria AI Media Studio * Re-Up Engine * 1000+ Platforms
echo ============================================================
echo.

REM --- KIEM TRA PYTHON ---
set "PYTHON="
py --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=py"
    goto :py_ready
)
python --version >nul 2>&1
if not errorlevel 1 (
    set "PYTHON=python"
    goto :py_ready
)

echo [LOI] Khong tim thay Python tren he thong!
echo Vui long cai dat Python tai: https://www.python.org/
echo LUU Y: Nho tich chon "Add Python to PATH" khi cai dat.
echo.
pause
exit /b 1

:py_ready
echo [....] Dang kiem tra thu vien he thong...
%PYTHON% -c "import fastapi, uvicorn, websockets, yt_dlp, rich" >nul 2>&1
if errorlevel 1 (
    echo [SETUP] Dang tu dong cai dat thu vien can thiet...
    %PYTHON% -m pip install -r requirements.txt
    if errorlevel 1 (
        echo [CANH BAO] Cai dat thu vien gap loi. Thu chay thu cong: py -m pip install -r requirements.txt
        pause
    )
)

echo [OK]   Moi truong da san sang!

REM Tu dong giai phong cong 5000 neu co phien ban cu dang chay
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ------------------------------------------------------------
echo  MAY CHU WEB DANG KHOI DONG TAI CONG 5000...
echo  Trinh duyet se tu dong mo: http://localhost:5000
echo  Nhan Ctrl+C de dung may chu khi khong su dung.
echo ------------------------------------------------------------
echo.

REM Khoi chay FastAPI server (Python se tu dong mo trinh duyet)
%PYTHON% web_app.py

if errorlevel 1 (
    echo.
    echo ============================================================
    echo  [LOI] May chu dung lai voi ma loi: %errorlevel%
    echo ============================================================
    pause
)

@echo off
setlocal EnableExtensions EnableDelayedExpansion
title Tool Tai Video PRO MAX v3.0.0 ULTRA - PUBLIC INTERNET EDITION
cd /d "%~dp0"

echo.
echo ============================================================
echo    TOOL TAI VIDEO PRO MAX v3.0.0 - LINK CONG KHAI TOAN CAU
echo    (c) Ban quyen: An Nguyen (2026)
echo    Tu dong tao link HTTPS online de chia se cho ban be
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
pause
exit /b 1

:py_ready
echo [OK]   Moi truong san sang!

REM Tu dong giai phong cong 5000 neu co tien trinh cu
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5000" ^| findstr "LISTENING"') do (
    taskkill /F /PID %%a >nul 2>&1
)

echo.
echo ------------------------------------------------------------
echo  DANG KHOI DONG SERVER VA TAO LINK CONG KHAI CLOUDFLARE...
echo  Vao the "Mang LAN & QR" tren Web de xem va sao chep link.
echo ------------------------------------------------------------
echo.

%PYTHON% web_app.py --public

if errorlevel 1 (
    echo.
    echo ============================================================
    echo  [LOI] May chu dung lai voi ma loi: %errorlevel%
    echo ============================================================
    pause
)

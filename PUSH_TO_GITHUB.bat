@echo off
chcp 65001 >nul
title Đang đẩy mã nguồn lên GitHub...
echo ======================================================================
echo   ĐANG TỰ ĐỘNG ĐẨY MÃ NGUỒN LÊN GITHUB: AnNguyen-Script/Video-Not-Logo
echo ======================================================================
echo.

echo [1/4] Khởi tạo kho lưu trữ Git...
git init

echo [2/4] Cập nhật đường dẫn kho GitHub...
git remote remove origin 2>nul
git remote add origin https://github.com/AnNguyen-Script/Video-Not-Logo.git
git branch -M main

echo [3/4] Gom toàn bộ file và tạo bản lưu Commit...
git add .
git commit -m "Deploy Video Pro Max Desktop Utility"

echo [4/4] Đang đồng bộ lên GitHub (vui lòng chờ trong giây lát)...
git push -u origin main

echo.
echo ======================================================================
echo   ĐÃ ĐỒNG BỘ THÀNH CÔNG LÊN GITHUB!
echo ======================================================================
echo.
pause

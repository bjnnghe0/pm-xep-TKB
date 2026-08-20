@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo.
echo   DAT TAI KHOAN CHO MAY CHU XEP THOI KHOA BIEU
echo.
python tao_mat_khau.py them
echo.
pause

@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo ================================================
echo   XEP THOI KHOA BIEU - Khoa Khoa hoc Co ban
echo ================================================
python xep_tkb.py --in-man-hinh
if errorlevel 1 (
  echo.
  echo [Loi] Kiem tra lai: da cai Python chua? da chay "pip install openpyxl" chua?
)
echo.
pause

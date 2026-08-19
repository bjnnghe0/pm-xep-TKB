@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"

echo ======================================================================
echo   ĐƯA THỜI KHÓA BIỂU LÊN MẠNG
echo ======================================================================

where git >nul 2>&1
if errorlevel 1 (
  echo.
  echo  DỪNG LẠI — máy chưa cài git
  echo    Tải git tại https://git-scm.com rồi cài, sau đó chạy lại tệp này.
  echo    Hoặc làm cách tải tệp bằng tay, xem DUA_LEN_MANG.md phần A bước 6.
  echo.
  pause
  exit /b 1
)

git rev-parse --git-dir >nul 2>&1
if errorlevel 1 (
  echo.
  echo  DỪNG LẠI — thư mục này chưa phải kho git
  echo    Chạy:  git init -b main
  echo    Rồi làm tiếp DUA_LEN_MANG.md PHẦN A.
  echo.
  pause
  exit /b 1
)

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo.
  echo  DỪNG LẠI — chưa nối với kho trên GitHub
  echo    Chưa có kho từ xa tên "origin", nên không biết đẩy đi đâu.
  echo.
  echo    Làm PHẦN A trong DUA_LEN_MANG.md trước — bạn phải tự làm vì
  echo    cần tài khoản GitHub của bạn. Xong bước đó thì chạy:
  echo.
  echo        git remote add origin https://github.com/^<tên tài khoản^>/^<tên kho^>.git
  echo.
  echo    rồi chạy lại tệp này.
  echo.
  pause
  exit /b 1
)

echo   [1/4] Đang xếp thời khóa biểu (khoảng 50 giây)...
python xep_tkb.py --xuat-html
if errorlevel 1 (
  echo.
  echo  DỪNG LẠI — xếp thời khóa biểu không xong
  echo    Xem thông báo lỗi ở trên. Thường là do quy tắc trong cauhinh.json
  echo    mâu thuẫn nhau — sửa rồi chạy lại.
  echo.
  pause
  exit /b 1
)

if not exist tkb_web.html (
  echo  DỪNG LẠI — không thấy tkb_web.html
  pause
  exit /b 1
)

echo   [2/4] Chép sang docs\index.html ...
if not exist docs mkdir docs
copy /y tkb_web.html docs\index.html >nul
type nul > docs\.nojekyll

echo   [3/4] Ghi vào git ...
git add docs/index.html docs/.nojekyll
git diff --cached --quiet
if not errorlevel 1 (
  echo.
  echo   Thời khóa biểu không có gì đổi so với lần trước, không cần đẩy lên.
  echo.
  pause
  exit /b 0
)
git commit -q -m "Cap nhat thoi khoa bieu"

echo   [4/4] Đang đẩy lên GitHub ...
for /f "delims=" %%b in ('git rev-parse --abbrev-ref HEAD') do set NHANH=%%b
git push origin %NHANH%
if errorlevel 1 (
  echo.
  echo  DỪNG LẠI — đẩy lên không xong
  echo    Thường do một trong ba nguyên nhân:
  echo      - Máy chưa đăng nhập GitHub. Lần đầu git sẽ hỏi tên tài khoản và
  echo        mật khẩu — chỗ mật khẩu phải dán Personal Access Token, xem
  echo        DUA_LEN_MANG.md PHẦN A bước 5.
  echo      - Máy không có mạng.
  echo      - Sai địa chỉ kho. Kiểm bằng:  git remote -v
  echo.
  pause
  exit /b 1
)

echo.
echo ======================================================================
echo   XONG. Đợi 1-2 phút rồi mở link GitHub Pages của bạn, dạng:
echo       https://^<tên tài khoản^>.github.io/tkb-khoi12/
echo   Trên trang có dòng "Xuất lúc ..." — xem ngày giờ có đúng lần vừa
echo   chạy không. Đúng là đã lên.
echo ======================================================================
echo.
pause

#!/usr/bin/env bash
# ==========================================================================
#  ĐƯA THỜI KHÓA BIỂU LÊN MẠNG  —  chạy hằng tuần
#  Xếp TKB -> xuất trang web -> chép sang docs/ -> đẩy lên GitHub.
#  Xem từng bước cài đặt lần đầu trong DUA_LEN_MANG.md (PHẦN A).
# ==========================================================================
set -u
cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"
command -v "$PYTHON" >/dev/null 2>&1 || PYTHON=python

vach() { printf '%s\n' "======================================================================"; }
dung() { echo; vach; echo " DỪNG LẠI — $1"; vach; shift; for d in "$@"; do echo "  $d"; done; echo; exit 1; }

vach
echo "  ĐƯA THỜI KHÓA BIỂU LÊN MẠNG"
vach

# ---- 1. kiểm tra đủ điều kiện trước, đừng xếp 50 giây rồi mới báo thiếu ----
command -v git >/dev/null 2>&1 || dung "máy chưa cài git" \
  "Tải git tại https://git-scm.com rồi cài, sau đó chạy lại." \
  "Hoặc làm cách tải file bằng tay, xem DUA_LEN_MANG.md phần A bước 6."

git rev-parse --git-dir >/dev/null 2>&1 || dung "thư mục này chưa phải kho git" \
  "Chạy:  git init -b main" \
  "Rồi làm tiếp DUA_LEN_MANG.md PHẦN A."

if ! git remote get-url origin >/dev/null 2>&1; then
  dung "chưa nối với kho trên GitHub" \
    "Chưa có kho từ xa tên 'origin', nên không biết đẩy đi đâu." \
    "" \
    "Làm PHẦN A trong DUA_LEN_MANG.md trước — bạn phải tự làm vì cần" \
    "tài khoản GitHub của bạn. Xong bước đó thì chạy lệnh nối kho:" \
    "" \
    "    git remote add origin https://github.com/<tên tài khoản>/<tên kho>.git" \
    "" \
    "rồi chạy lại tệp này."
fi

echo "  Kho từ xa : $(git remote get-url origin)"
echo "  Python    : $PYTHON"
echo

# ---- 2. xếp thời khoá biểu và xuất trang web ----
echo "  [1/4] Đang xếp thời khoá biểu (khoảng 50 giây)..."
"$PYTHON" xep_tkb.py --xuat-html || dung "xếp thời khoá biểu không xong" \
  "Xem thông báo lỗi ở trên. Thường là do quy tắc trong cauhinh.json" \
  "mâu thuẫn nhau — sửa rồi chạy lại."

[ -f tkb_web.html ] || dung "không thấy tkb_web.html" \
  "Lẽ ra bước trên phải sinh ra tệp này."

# ---- 3. chép sang thư mục sẽ đưa lên mạng ----
echo "  [2/4] Chép sang docs/index.html ..."
mkdir -p docs
cp tkb_web.html docs/index.html
: > docs/.nojekyll                # bảo GitHub Pages đừng xử lý lại tệp

# ---- 4. ghi vào git ----
echo "  [3/4] Ghi vào git ..."
git add docs/index.html docs/.nojekyll
if git diff --cached --quiet; then
  echo
  echo "  Thời khoá biểu không có gì đổi so với lần trước, không cần đẩy lên."
  exit 0
fi
TUAN=$(grep -o '"tuan"[^,]*' cauhinh.json | head -1 | cut -d'"' -f4)
git commit -q -m "Cập nhật thời khoá biểu: ${TUAN:-tuần mới}" || \
  dung "git commit không xong" "Xem thông báo ở trên."

# ---- 5. đẩy lên ----
echo "  [4/4] Đang đẩy lên GitHub ..."
NHANH=$(git rev-parse --abbrev-ref HEAD)
if ! git push origin "$NHANH"; then
  dung "đẩy lên không xong" \
    "Thường là do một trong ba nguyên nhân:" \
    "  - Máy chưa đăng nhập GitHub. Lần đầu git sẽ hỏi tên tài khoản và" \
    "    mật khẩu — chỗ mật khẩu phải dán Personal Access Token, xem" \
    "    DUA_LEN_MANG.md PHẦN A bước 5." \
    "  - Máy không có mạng." \
    "  - Sai địa chỉ kho. Kiểm bằng:  git remote -v"
fi

XA=$(git remote get-url origin)
echo
vach
echo "  XONG. Đợi 1-2 phút rồi mở link."
case "$XA" in
  *github.com*)
    URL=$(printf '%s' "$XA" | sed -e 's#.*github\.com[:/]##' -e 's#\.git$##')
    TK=${URL%%/*}; KHO=${URL#*/}
    echo "      https://$TK.github.io/$KHO/"
    ;;
  *)
    echo "      (kho từ xa không phải GitHub nên không đoán được link)"
    ;;
esac
echo
echo "  Trên trang có dòng \"Xuất lúc ...\" — xem ngày giờ ở đó có đúng"
echo "  lần vừa chạy không. Đúng là đã lên."
vach

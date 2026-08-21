#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: MỌI DÒNG HƯỚNG DẪN GÕ LỆNH ĐỀU LÀ "python3", KHÔNG PHẢI "python"
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_lenh_chay.py

 VÌ SAO CÓ TỆP NÀY. Máy Linux đang dùng KHÔNG có lệnh "python" — chỉ có
 "python3" (xem CLAUDE.md, mục "Môi trường Python trên máy này"). Mỗi dòng
 hướng dẫn mở đầu bằng "python" trần rồi tới tên tệp là một dòng thầy cô chép
 vào cửa sổ dòng lệnh rồi nhận "command not found", và không có ca thử nào của
 dự án đỏ vì chuyện đó: những dòng ấy nằm trong docstring, chú thích, tài liệu
 .md và câu thông báo lỗi — chỗ mà không bộ thử nào ngó tới.

 (Chính tệp này cũng bị CA 1 quét, nên nó không được chứa mẫu vi phạm nào. Chỗ
 nào cần viết ra mẫu đó thì ghép chuỗi — xem biến P trong CA 0 và CA 2.)

 NGOẠI LỆ CÓ CHỦ Ý VỚI MỘT BẤT BIẾN. Kỷ luật ca thử của dự án ghi:
 "Ca thử KHÔNG khẳng định trên VĂN BẢN MÃ NGUỒN. Khẳng định trên HÀNH VI."
 Ở đây văn bản CHÍNH LÀ sản phẩm giao cho người dùng, nên CA 1 cố ý quét văn
 bản. Hai hệ quả phải nhớ:
   1. Ca này TUYỆT ĐỐI KHÔNG lột chú thích trước khi quét (khác thu_web.py
      CA 6 và thu_an_ninh.py CA A10) — vì chú thích và docstring chính là chỗ
      chứa phần lớn các dòng cần bắt.
   2. Vì quét văn bản là bằng chứng yếu, CA 2 bù lại bằng HÀNH VI THẬT: chạy
      tiến trình con và bắn HTTP thật để đọc đúng những câu lỗi ấy khi chúng
      hiện ra trước mặt người dùng.

 CA 0 là mục quan trọng nhất: nó khẳng định HAI CHIỀU rằng bộ dò biết bắt và
 biết bỏ qua. Thiếu nó thì một regex hỏng cho ra ca thử XANH GIẢ trong khi cả
 kho đầy lệnh sai, hoặc một đợt sửa hàng loạt phá hỏng những chuỗi đang đúng
 (nhất là '/usr/lib/python' — chuỗi mà thu_an_ninh.py CA A3 dò để bắt rò rỉ
 đường dẫn thư viện).
==========================================================================
"""
import os
import re
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import GOC_TM, MayChuTam, cau_hinh_tam      # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def dat_dong_ho_canh(giay=120):
    """Bộ thử không bao giờ được phép TREO — hết giờ thì ĐỎ. Xem CLAUDE.md."""
    def bao():
        time.sleep(giay)
        hong = [m for ok, m in KQ if not ok]
        print(f'\n  [LỖI] BỘ THỬ TREO quá {giay} giây.')
        print('=' * 74)
        print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ) + 1} mục ĐẠT.')
        print('  LỖI: bộ thử treo, không chạy hết được')
        sys.stdout.flush()
        os._exit(1)
    threading.Thread(target=bao, daemon=True).start()


# ==========================================================================
# BỘ DÒ — ba mảnh, mỗi mảnh có việc riêng
# ==========================================================================
#   (?<![\w/.$~=-])  loại ĐƯỜNG DẪN và BIẾN SHELL: ~/.venvs/.../bin/python,
#                    /usr/lib/python, $PYTHON, PYTHON=python
#   (?!3)            loại python3 — thứ đã đúng rồi
#   [ \t]+(?=...)    đòi thứ theo sau phải TRÔNG NHƯ ĐỐI SỐ dòng lệnh: một cờ
#                    (-c, -m), một tệp .py, hoặc một đường dẫn (/ hay ~). Nên
#                    loại được thẻ ngôn ngữ của khối mã Markdown, python.org,
#                    và — quan trọng nhất — VĂN XUÔI TIẾNG VIỆT kiểu
#                    "python của venv": bản đầu chỉ đòi [-\w"'] nên chữ "của"
#                    cũng khớp, và ca thử ĐỎ OAN vì một dòng chú thích đúng.
# Phân biệt HOA/THƯỜNG: "Python" viết hoa là tên ngôn ngữ trong văn xuôi, không
# phải lệnh gõ vào máy.
MAU = re.compile(r'(?<![\w/.$~=-])python(?!3)[ \t]+(?=-\S|\S*\.py\b|[/~])')

# Danh sách loại trừ — mỗi mục kèm LÝ DO, và CA 1 in ra để nhìn thấy được.
BO_QUA_THU_MUC = {
    '.git': 'kho lịch sử: mọi bản CŨ của mọi tệp nằm trong đó, quét vào thì '
            'không bao giờ xanh được nữa',
    '__pycache__': 'tệp .pyc chứa hằng chuỗi đã biên dịch của bản CŨ — đỏ vì '
                   'rác build chứ không vì lỗi thật',
    'docs': 'thư mục GitHub Pages, do dua_len.sh ghi đè mỗi lượt; sửa tay là vô '
            'nghĩa nên một mục đỏ ở đây không ai chữa được bằng cách đúng',
    '.venv': 'môi trường ảo, không phải mã của dự án',
    'venv': 'môi trường ảo, không phải mã của dự án',
}
BO_QUA_TEP = {
    'cauhinh.khoi12.goc.json': 'tệp ĐÓNG BĂNG ở tag v1.0-khoi12 — CLAUDE.md ghi '
                               'thẳng "KHÔNG được sửa"; giá trị của nó nằm ở chỗ '
                               'nó là bản sao Y NGUYÊN, sửa một ký tự là mất',
    'tkb_web.html': 'tệp SINH RA bởi xuat_html.py mỗi lượt xếp; muốn đổi thì '
                    'phải sửa xuat_html.py, mà tệp đó VẪN bị quét',
}
BO_QUA_DUOI = {
    '.bat': 'chạy trên Windows của nhà trường — ở đó bản cài từ python.org CHỈ '
            'tạo lệnh tên "python", gõ "python3" sẽ mở nhầm Microsoft Store',
    '.xlsx': 'tệp nhị phân', '.pyc': 'tệp nhị phân', '.pyo': 'tệp nhị phân',
    '.png': 'tệp nhị phân', '.jpg': 'tệp nhị phân', '.pdf': 'tệp nhị phân',
    '.zip': 'tệp nhị phân',
}


def quet_kho():
    """Duyệt cả kho. Trả (vi_pham, so_tep_da_quet, cac_tep_bo_qua)."""
    vi_pham, da_quet, bo_qua = [], [], []
    for goc, thu_muc, tep in os.walk(GOC_TM):
        thu_muc[:] = [t for t in thu_muc if t not in BO_QUA_THU_MUC]
        for t in sorted(tep):
            dd = os.path.join(goc, t)
            rel = os.path.relpath(dd, GOC_TM)
            if t in BO_QUA_TEP or os.path.splitext(t)[1] in BO_QUA_DUOI:
                bo_qua.append(rel)
                continue
            try:
                with open(dd, encoding='utf-8') as f:
                    noi = f.read()
            except (UnicodeDecodeError, OSError):
                # Không được để một tệp lạ làm VỠ bộ thử giữa chừng — bất biến
                # "biết ĐỎ, không biết VỠ".
                bo_qua.append(rel + ' (không đọc được bằng utf-8)')
                continue
            da_quet.append(rel)
            for i, dong in enumerate(noi.split('\n'), 1):
                if MAU.search(dong):
                    vi_pham.append(f'{rel}:{i}: {dong.strip()[:90]}')
    return vi_pham, da_quet, bo_qua


# ==========================================================================
def ca_0_bo_do_biet_bat_va_biet_bo_qua():
    print('\nCA 0 — bộ dò: biết BẮT và biết BỎ QUA (điều kiện tiên quyết)')
    print('-' * 74)

    # Ghép chuỗi để chính tệp ca thử này KHÔNG chứa mẫu vi phạm — nếu viết
    # thẳng thì CA 1 sẽ đỏ vì chính nó, và cách chữa duy nhất là tự loại trừ
    # mình ra, tức đục một lỗ ngay giữa bộ thử.
    P = 'py' + 'thon'

    can_bat = [
        (P + ' xep_tkb.py', 'lệnh trần trong khối mã'),
        ('Chạy: ' + P + ' web.py --port 8080', 'lệnh nằm giữa câu tiếng Việt'),
        (P + ' -c "import openpyxl"', 'lệnh KHÔNG có tệp .py theo sau'),
        ('`' + P + ' tu_kiem_tra.py`', 'lệnh trong dấu nháy ngược của Markdown'),
        ('<code>' + P + ' tao_mat_khau.py doi</code>', 'lệnh trong thẻ HTML'),
        ('      ' + P + '\ttu_kiem_tra.py', 'ngăn cách bằng Tab'),
    ]
    sot = [n for c, n in can_bat if not MAU.search(c)]
    kiem(not sot, f'BẮT được cả {len(can_bat)} dạng lệnh trần — sót: {sot}')

    can_bo_qua = [
        ('python3 xep_tkb.py', 'đã đúng rồi'),
        ('~/.venvs/xeptkb/bin/' + P + ' xep_tkb.py', 'đường dẫn tệp trong venv'),
        ('PYTHON=~/.venvs/xeptkb/bin/' + P + ' ./dua_len.sh', 'gán biến bằng đường dẫn'),
        ("('/usr/lib/" + P + "', 'đường dẫn thư viện Python'),",
         'chuỗi mà thu_an_ninh.py CA A3 dò — đổi nó là HỎNG một bất biến an ninh'),
        ('#!/usr/bin/env python3', 'shebang'),
        ('```' + P, 'thẻ ngôn ngữ của khối mã Markdown'),
        ('PYTHONHASHSEED=0', 'biến môi trường VIẾT HOA'),
        ('Cài Python tại ' + P + '.org', 'tên miền, và tên ngôn ngữ viết hoa'),
        ('command -v "$PYTHON" || PYTHON=' + P, 'nhánh dự phòng của dua_len.sh'),
        ('không trả dấu vết lỗi Python ra ngoài', 'tên ngôn ngữ trong văn xuôi'),
        ('gõ `' + P + '`, không có chữ số 3', 'nhắc TÊN lệnh, không phải gõ lệnh'),
        ('PHẢI là ' + P + ' của venv, không phải /usr/bin/python3',
         'VĂN XUÔI tiếng Việt — sau chữ python là một TỪ, không phải đối số'),
        ('dùng ' + P + ' nào cũng chạy được', 'văn xuôi, theo sau là từ tiếng Việt'),
    ]
    bat_nham = [n for c, n in can_bo_qua if MAU.search(c)]
    kiem(not bat_nham,
         f'BỎ QUA đúng cả {len(can_bo_qua)} dạng không phải lệnh — bắt nhầm: '
         f'{bat_nham}')

    # Loại trừ .bat phải là DO DANH SÁCH LOẠI TRỪ, không phải do bộ dò yếu.
    # Nếu bộ dò vốn đã không bắt được dòng trong chay.bat thì loại trừ kia là
    # thừa, và ta đang tin vào một thứ không làm gì cả.
    with open(os.path.join(GOC_TM, 'chay.bat'), encoding='utf-8') as f:
        bat = f.read()
    kiem(MAU.search(bat),
         'Bộ dò VẪN bắt được dòng lệnh trong chay.bat — nghĩa là thứ tha cho '
         'tệp .bat là DANH SÁCH LOẠI TRỪ, không phải một bộ dò yếu')


# ==========================================================================
def ca_1_quet_kho():
    print('\nCA 1 — quét cả kho: không còn dòng hướng dẫn nào gõ lệnh trần')
    print('-' * 74)
    vi_pham, da_quet, bo_qua = quet_kho()

    # Guard chống XANH GIẢ: phép duyệt hỏng thì vòng lặp chạy rỗng và mọi mục
    # dưới đây xanh trong khi kho đầy lỗi.
    kiem(len(da_quet) >= 25,
         f'Đã thật sự đọc được kho — {len(da_quet)} tệp (không phải duyệt rỗng)')
    kiem(os.path.join('tests', 'thu_lenh_chay.py') in da_quet,
         'Và CHÍNH TỆP CA THỬ NÀY cũng bị quét — không tự loại trừ mình')
    thieu = [t for t in ('CLAUDE.md', 'HUONG_DAN.md', 'QUY_TAC.md',
                         'DUA_LEN_MANG.md', 'web.py', 'quy_tac.py',
                         'xep_tkb.py', 'tai_khoan.py', 'tao_mat_khau.py',
                         'cauhinh.json', 'tai_khoan.json.mau', '.gitignore',
                         'dua_len.sh', os.path.join('web', 'index.html'))
              if t not in da_quet]
    kiem(not thieu, f'Mọi tệp từng chứa lệnh trần đều nằm trong tầm quét — '
                    f'thiếu: {thieu}')

    print(f'  ... bỏ qua {len(bo_qua)} tệp: {", ".join(sorted(bo_qua)[:8])}'
          f'{" ..." if len(bo_qua) > 8 else ""}')

    # MỘT mục duy nhất cho toàn bộ vi phạm: kiem() trong vòng lặp sẽ làm số mục
    # trong "Tổng: N/N" nhảy theo số lỗi, và bảng "Trạng thái đã kiểm chứng"
    # của CLAUDE.md không ghim được con số nào.
    kiem(not vi_pham,
         f'Không tệp nào (ngoài danh sách loại trừ) còn dòng hướng dẫn gõ lệnh '
         f'trần — {len(vi_pham)} chỗ' +
         (':\n        ' + '\n        '.join(vi_pham[:20]) if vi_pham else ''))


# ==========================================================================
def ca_2_hanh_vi_that(tm):
    """Phần bù bắt buộc cho CA 1: đọc đúng những câu ấy KHI CHÚNG HIỆN RA."""
    print('\nCA 2 — hành vi thật: câu lỗi người dùng nhìn thấy nói "python3"')
    print('-' * 74)
    P = 'py' + 'thon'

    def sach(chu, nhan, phai_co):
        kiem(phai_co in chu, f'{nhan}: có "{phai_co}"')
        kiem(not MAU.search(chu),
             f'{nhan}: và KHÔNG còn lệnh trần nào — '
             f'{MAU.findall(chu) or "sạch"}')

    # --- 2a. Khai báo sai trong cauhinh.json -> quy_tac.bao_loi() ------------
    tmx = os.path.join(tm, 'l2a')
    os.makedirs(tmx, exist_ok=True)

    def hong(cfg):
        cfg['quy_tac'].append({'loai': 'khong_xep_thu',
                               'loc': {'mon': 'Toán'}, 'thu': [99]})
    dd = cau_hinh_tam(tmx, sua=hong)
    r = subprocess.run([sys.executable, os.path.join(GOC_TM, 'xep_tkb.py'),
                        '--cauhinh', dd],
                       capture_output=True, text=True, timeout=90, cwd=tmx)
    ra = r.stdout + r.stderr
    kiem(r.returncode != 0 and '[LỖI]' in ra,
         f'Khai sai "thu": [99] -> chương trình DỪNG kèm [LỖI] — mã {r.returncode}')
    sach(ra, 'Câu lỗi khai báo sai (quy_tac.bao_loi)', 'python3 xep_tkb.py')

    # --- 2b. Sổ tài khoản rỗng -> 503 qua HTTP THẬT -------------------------
    tmb = os.path.join(tm, 'l2b')
    os.makedirs(tmb, exist_ok=True)
    ddb = cau_hinh_tam(tmb)
    with MayChuTam(ddb, tai_khoan=False, dang_nhap=False) as (k, _):
        ma, than = k.get('/api/quy-tac')
        kiem(ma == 503, f'Sổ tài khoản rỗng -> 503 qua HTTP thật — {ma}')
        sach(than, 'Câu 503 "chưa cài xong" (web.py)', 'python3 tao_mat_khau.py')

    # --- 2c. Thiếu tai_khoan.json -> web.py TỪ CHỐI KHỞI ĐỘNG ---------------
    r = subprocess.run([sys.executable, os.path.join(GOC_TM, 'web.py'),
                        '--port', '20995', '--cauhinh', ddb,
                        '--tai-khoan', os.path.join(tmb, 'khong-co.json')],
                       capture_output=True, text=True, timeout=90)
    ra = r.stdout + r.stderr
    kiem(r.returncode != 0 and 'Mở trình duyệt vào' not in ra,
         f'Thiếu tai_khoan.json -> máy chủ KHÔNG khởi động — mã {r.returncode}')
    sach(ra, 'Câu lỗi thiếu tài khoản (tai_khoan._loi)',
         'python3 tao_mat_khau.py them')

    # --- 2d. Bảng danh mục quy tắc in ra màn hình ---------------------------
    r = subprocess.run([sys.executable, os.path.join(GOC_TM, 'xep_tkb.py'),
                        '--quy-tac'],
                       capture_output=True, text=True, timeout=90, cwd=GOC_TM)
    ra = r.stdout + r.stderr
    kiem(r.returncode == 0 and len(ra) > 2000,
         f'--quy-tac in được bảng danh mục — {len(ra)} ký tự')
    kiem(not MAU.search(ra),
         f'Và bảng đó không dạy ai gõ lệnh trần — {MAU.findall(ra) or "sạch"}')

    # Guard hai chiều cho chính hàm sach(): nếu MAU hỏng thì mọi mục trên đều
    # xanh giả. Đưa cho nó một câu CÓ lệnh trần và đòi nó phải thấy.
    kiem(bool(MAU.search('      Sửa lại rồi chạy: ' + P + ' xep_tkb.py')),
         'Và bộ dò VẪN thấy lỗi khi câu lỗi bị lùi về bản cũ (không xanh giả)')


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ: MỌI DÒNG HƯỚNG DẪN GÕ LỆNH ĐỀU LÀ "python3"')
    print('=' * 74)
    dat_dong_ho_canh(120)
    ca_0_bo_do_biet_bat_va_biet_bo_qua()
    ca_1_quet_kho()
    with tempfile.TemporaryDirectory() as tm:
        ca_2_hanh_vi_that(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

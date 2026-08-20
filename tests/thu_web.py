#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ GIAO DIỆN WEB
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_web.py

 Ba điều đáng lo nhất ở web.py, kiểm hết:

 1. web.py và xep_tkb.main() phải chọn ra CÙNG một phương án. Việc tìm
    phương án đã gộp về X.tim_phuong_an(), nhưng phần còn lại của _chay()
    — dựng cấu hình, tắt quy tắc tạm, xuất Excel — vẫn có thể lệch.
    Ca thử chạy cả hai với cùng cấu hình và so TỪNG Ô của file Excel.
 2. Khai báo sai làm chương trình gốc gọi sys.exit. Trong web thì phải
    bắt lại, nếu không máy chủ chết. Đây là đường đi thường gặp.
 3. Mỗi lúc chỉ một lượt xếp; bấm nữa phải bị chặn.

 MỌI CA ĐI QUA HTTP THẬT — xem tests/tien_ich_web.py để biết vì sao.
 Tóm tắt: gọi thẳng hàm Python thì bỏ qua đúng tầng sắp đặt cổng đăng
 nhập, ca thử sẽ vẫn xanh dù cổng đó hỏng hoàn toàn.

 Mọi thứ chạy trong thư mục tạm, không đụng cauhinh.json thật.
==========================================================================
"""
import io
import json
import os
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import (GOC_TM, MayChuTam, cau_hinh_tam,   # noqa: E402
                          doc_o_excel, doi_trang_thai)
import xep_tkb as X          # noqa: E402
import tai_khoan as TK       # noqa: E402
import web                   # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


# --------------------------------------------------------------------------
def ca_1_giong_dong_lenh(tm):
    print('\nCA 1 — web.py và xep_tkb.main() chọn ra CÙNG một phương án')
    print('-' * 74)
    dd = cau_hinh_tam(tm)
    xuat = os.path.join(tm, 'TKB_Khoi12.xlsx')

    argv = sys.argv
    sys.argv = ['xep_tkb.py', '--cauhinh', dd]
    man = io.StringIO()
    try:
        with redirect_stdout(man):
            X.main()
    finally:
        sys.argv = argv
    ra_cli = man.getvalue()
    o_cli = doc_o_excel(xuat)
    shutil.copy(xuat, os.path.join(tm, 'cli.xlsx'))
    os.remove(xuat)

    # ---- đường web: qua HTTP thật, không gọi thẳng web._chay() ----
    with MayChuTam(dd) as (k, _):
        ma, _ = k.js('/api/xep', {})
        kiem(ma == 200, f'POST /api/xep nhận lệnh — {ma}')
        t = doi_trang_thai(k)

    o_web = doc_o_excel(xuat)
    log = '\n'.join(t.get('log_moi') or [])

    kiem(t.get('loi') is None, f'Lượt xếp qua HTTP trót lọt — {t.get("loi")}')
    lech = [x for x in o_cli if o_cli[x] != o_web.get(x)]
    kiem(not lech,
         f'Từng ô của vùng D8:I32 giống hệt nhau — {len(o_cli)} ô, {len(lech)} lệch')

    m1 = re.search(r'Điểm cao nhất: (-?\d+)', ra_cli)
    kiem(m1 and t.get('diem') == int(m1.group(1)),
         f'Điểm mềm bằng nhau: dòng lệnh {m1.group(1) if m1 else "?"} '
         f'= web {t.get("diem")}')
    m2 = re.search(r'Tổng: (\d+)/(\d+) quy tắc ĐẠT', ra_cli)
    dat_web = len(t.get('bang') or []) - (t.get('so_loi') or 0)
    kiem(m2 and (int(m2.group(1)), int(m2.group(2)))
         == (dat_web, len(t.get('bang') or [])),
         f'Bảng đối chiếu bằng nhau: {m2.group(0) if m2 else "?"} '
         f'= web {dat_web}/{len(t.get("bang") or [])}')
    kiem('ĐỐI CHIẾU QUY TẮC' in log and 'Đã xuất file' in log,
         'Khung nhật ký có đúng những phần chương trình vẫn in ra')
    luoi = t.get('luoi')
    kiem(luoi and len(luoi['hang']) == 25 and luoi['tong'] == [24] * 6,
         'Lưới TKB đủ 25 hàng, mỗi lớp 24 tiết')
    gv = t.get('gv')
    kiem(gv and len(gv['gv']) == 28,
         f'Lịch giáo viên đủ 28 người — {len(gv["gv"]) if gv else 0}')


def ca_2_bat_system_exit(tm):
    print('\nCA 2 — khai báo sai: bắt SystemExit, máy chủ phải SỐNG TIẾP')
    print('-' * 74)
    tm2 = os.path.join(tm, 'sai')
    os.makedirs(tm2, exist_ok=True)

    def lam_hong(cfg):
        cfg['quy_tac'][1]['tiet_trong_buoi'] = [9, 10]      # buổi chỉ có 5 tiết
    dd = cau_hinh_tam(tm2, lam_hong)

    with MayChuTam(dd) as (k, _):
        ma, _ = k.js('/api/xep', {})
        kiem(ma == 200, f'Máy chủ nhận lệnh xếp — {ma}')
        t = doi_trang_thai(k)
        kiem(t.get('loi') and 'Khai báo sai' in t['loi'],
             f'Trạng thái có ghi lỗi — {str(t.get("loi"))[:40]}')
        log = '\n'.join(t.get('log_moi') or [])
        kiem('tiet_trong_buoi' in log
             and 'Có phải bạn định dùng khoá "tiet"' in log,
             'Nhật ký giữ NGUYÊN VĂN thông báo lỗi, cả dòng gợi ý')
        kiem(t.get('dang_chay') is False and t.get('xong') is True,
             'Cờ trạng thái về đúng: hết chạy, đã xong')
        # điều đáng giá nhất của ca này: SAU khi khai báo sai, máy chủ còn sống
        ma2, than2 = k.get('/')
        kiem(ma2 == 200 and '<title>' in than2,
             f'Máy chủ VẪN SỐNG sau khi gặp khai báo sai — {ma2}')
        ma3, d3 = k.js('/api/quy-tac')
        kiem(ma3 == 200 and d3, 'Vẫn phục vụ được đường API khác')


def ca_3_may_chu(tm):
    print('\nCA 3 — máy chủ HTTP')
    print('-' * 74)
    dd = cau_hinh_tam(tm)
    with MayChuTam(dd) as (k, (dia, _cong)):
        kiem(dia == '127.0.0.1', f'Chỉ bind 127.0.0.1, không mở ra mạng — {dia}')

        ma, than = k.get('/')
        kiem(ma == 200 and '<title>' in than and 'Xếp thời khoá biểu' in than,
             'GET / trả trang HTML tiếng Việt')
        for f in ('style.css', 'app.js'):
            kiem(k.get('/web/' + f)[0] == 200, f'GET /web/{f}')
        kiem('http://' not in than.replace('http://127.0.0.1', '')
             and 'https://' not in than,
             'Trang không gọi ra ngoài Internet (không CDN)')
        for xau in ('/web/../web.py', '/web/cauhinh.json', '/api/lung-tung'):
            kiem(k.get(xau)[0] == 404, f'Chặn đường dẫn lạ {xau}')

        ma, d = k.js('/api/quy-tac')
        # So với chính TỆP, không so với một số cứng. Ghim "== 13" ở đây đã vỡ
        # đúng một lần: thầy cô thêm quy tắc qua giao diện là ca thử đỏ, mà mã
        # thì không sai một dòng nào. CLAUDE.md đã cấm ghim số kiểu này.
        with io.open(dd, encoding='utf-8') as f:
            so_trong_tep = len(json.load(f)['quy_tac'])
        kiem(ma == 200 and len(d['quy_tac']) == so_trong_tep,
             f'GET /api/quy-tac liệt kê đủ số quy tắc của tệp — '
             f'{len(d["quy_tac"])}/{so_trong_tep}')
        kiem(all({'i', 'loai', 'ghi_chu', 'bat'} <= set(r) for r in d['quy_tac']),
             'Mỗi dòng có đủ ghi_chu + loai + cờ bật/tắt')

        ma, _ = k.js('/api/xep', {'so_lan': '3', 'tat': []})
        kiem(ma == 200, 'POST /api/xep nhận lệnh')
        ma2, d2 = k.js('/api/xep', {'tat': []})
        kiem(ma2 == 409 and 'Đang xếp' in (d2 or {}).get('loi', ''),
             f'Bấm lần nữa lúc đang chạy bị chặn — {ma2}')

        t = doi_trang_thai(k)
        kiem(t.get('xong') and not t.get('dang_chay'), 'Hỏi trạng thái tới lúc xong')
        kiem(t['log_het'] > 10 and len(t['log_moi']) == t['log_het'],
             'Nhật ký lấy được theo lô, có đánh dấu đã đọc tới đâu')
        _, t2 = k.js('/api/trang-thai?tu=%d' % t['log_het'])
        kiem(t2['log_moi'] == [],
             'Hỏi tiếp từ vị trí cũ thì không trả lại dòng đã đọc')
        ma, than = k.get_nhi_phan('/api/tai-ve')
        kiem(ma == 200 and than[:2] == b'PK' and len(than) > 10000,
             f'Tải được file .xlsx thật ({len(than)} byte, đúng chữ ký ZIP)')


def ca_4_trang_tinh():
    print('\nCA 4 — trang tĩnh: JS và HTML khớp nhau')
    print('-' * 74)
    html = io.open(os.path.join(GOC_TM, 'web', 'index.html'),
                   encoding='utf-8').read()
    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    css = io.open(os.path.join(GOC_TM, 'web', 'style.css'), encoding='utf-8').read()

    co = set(re.findall(r'\bid="([^"]+)"', html))
    goi = set(re.findall(r"\$\('([^']+)'\)", js)) \
        | set(re.findall(r"getElementById\('([^']+)'\)", js))
    thieu = sorted(goi - co)
    kiem(not thieu, f'Mọi id JS gọi đều có trong HTML — thiếu: {thieu}')

    man = set(re.findall(r'data-man="([^"]+)"', html))
    kiem(man <= co, f'Mọi màn hình trong thanh tab đều tồn tại — {sorted(man)}')
    kiem(len(man) == 4, f'Đủ 4 màn hình — {len(man)}')

    ngoai = re.findall(r'(?:src|href)="(https?://[^"]+)"', html)
    kiem(not ngoai, f'HTML không tải gì từ mạng — {ngoai}')
    kiem(not re.search(r'https?://(?!127\.0\.0\.1)', js + css),
         'JS và CSS cũng không gọi ra ngoài')
    kiem('charset="utf-8"' in html and 'lang="vi"' in html,
         'Khai báo utf-8 và tiếng Việt')
    for chu in ('Xếp thời khoá biểu', 'Quy tắc', 'Lịch giáo viên',
                'Lưu vào cauhinh.json', 'Tải file .xlsx'):
        kiem(chu in html, f'Có nhãn tiếng Việt có dấu: "{chu}"')
    # Đừng ghim cứng danh sách: thêm một đường API là ca thử vỡ dù không sai gì.
    # Điều cần khẳng định là JS và web.py khớp nhau — cả hai chiều.
    # [DI TRÚ 2A-1] app.js nay gọi API qua PHỄU goi()/goiCu() chứ không fetch()
    # rải rác — cả tệp chỉ còn ĐÚNG MỘT chữ fetch(, nằm trong phễu. Bắt theo tên
    # phễu, và giữ luôn mẫu fetch( cũ phòng khi có ai gọi thẳng.
    duong = set(re.findall(r"goi\w*\('(/api/[^'?]+)", js)) \
        | set(re.findall(r"fetch\('(/api/[^'?]+)", js)) \
        | set(re.findall(r"location = '(/api/[^']+)'", js))
    may = io.open(os.path.join(GOC_TM, 'web.py'), encoding='utf-8').read()
    co = set(re.findall(r"duong == '(/api/[^']+)'", may))
    kiem(duong and not (duong - co),
         f'Mọi đường API mà JS gọi đều có trong web.py — '
         f'{len(duong)} đường, thừa: {sorted(duong - co)}')
    kiem(not (co - duong),
         f'Không có đường API nào trong web.py bị bỏ quên không dùng — '
         f'{sorted(co - duong)}')


def ca_5_luu_quy_tac(tm):
    print('\nCA 5 — lưu quy tắc vào cauhinh.json (qua HTTP)')
    print('-' * 74)
    tm4 = os.path.join(tm, 'luu')
    os.makedirs(tm4, exist_ok=True)
    dd = cau_hinh_tam(tm4)
    truoc = X.doc_cau_hinh(dd)

    with MayChuTam(dd) as (k, _):
        ma, kq = k.js('/api/luu-quy-tac', {'tat': [4, 5]})
        kiem(ma == 200 and kq and 'doi' in kq,
             f'POST /api/luu-quy-tac trả về số dòng đã đổi — {ma} {kq}')

        bak = os.path.join(tm4, 'cauhinh.bak.json')
        kiem(os.path.exists(bak), 'Có sao lưu thành cauhinh.bak.json')
        kiem(X.doc_cau_hinh(bak) == truoc, 'Bản sao lưu đúng là nội dung cũ')

        sau = X.doc_cau_hinh(dd)
        kiem(list(sau) == list(truoc), 'Thứ tự khoá cấp cao nhất giữ nguyên')
        kiem(list(sau['quy_tac'][0]) == list(truoc['quy_tac'][0]),
             'Thứ tự khoá bên trong quy tắc giữ nguyên')
        kiem([i for i, r in enumerate(sau['quy_tac']) if r.get('bat') is False]
             == [4, 5], f'Đúng 2 quy tắc bị tắt, {kq["doi"]} dòng đổi')
        kiem({x: v for x, v in sau.items() if x != 'quy_tac'}
             == {x: v for x, v in truoc.items() if x != 'quy_tac'},
             'Mọi mục khác của file y nguyên')

        k.js('/api/luu-quy-tac', {'tat': []})
        lai = X.doc_cau_hinh(dd)
        kiem(all('bat' not in r for r in lai['quy_tac']),
             'Bật lại thì khoá "bat" biến mất hẳn, không để rác')
        kiem(lai['_quy_tac_de_san_chua_bat'] == truoc['_quy_tac_de_san_chua_bat']
             and all(r['bat'] is False for r in lai['_quy_tac_de_san_chua_bat']),
             'Không đụng tới mục _quy_tac_de_san_chua_bat')


def ca_6_moi_ca_qua_http():
    print('\nCA 6 — chính tệp ca thử này không được gọi tắt vào hàm Python')
    print('-' * 74)
    ma = io.open(os.path.abspath(__file__), encoding='utf-8').read()
    ma = ma.split('"""', 2)[-1]                       # bỏ phần chú thích đầu tệp
    than = '\n'.join(d for d in ma.split('\n')        # bỏ mọi dòng chú thích
                     if not d.lstrip().startswith('#'))
    than = than.split("if __name__ ==")[0]
    for goi in ('web._chay(', 'web.luu_quy_tac(', 'web.them_quy_tac(',
                'web.xoa_quy_tac(', 'web.thu_quy_tac('):
        kiem(goi not in than,
             f'Không gọi tắt {goi[:-1]} — mọi ca phải đi qua HTTP')
    kiem('MayChuTam' in than, 'Có dựng máy chủ HTTP thật')
    kiem(than.count('MayChuTam(') >= 4,
         f'Ít nhất 4 ca dựng máy chủ thật — {than.count("MayChuTam(")}')


def ca_7_o_chi_doc(tm):
    """Ổ CHỈ ĐỌC là lỗi im lặng nhất của cả phần mềm.

       Máy có Windows cài song song (đã đo: efibootmgr thấy "Windows Boot
       Manager"), thư mục dự án nằm trên NTFS. Windows tắt kiểu "khởi động
       nhanh" là ngủ đông chứ không tắt hẳn -> phân vùng còn BẨN -> Linux gắn
       CHỈ ĐỌC. Phần mềm chạy ngon, xếp ngon, tới lúc bấm Lưu mới hỏng — và
       nguyên nhân thật nằm ở một cái tắt máy sai cách hôm trước, trên hệ điều
       hành khác. Không có gì trong phần mềm chỉ ra điều đó.
    """
    print('\nCA 7 — thư mục dự án KHÔNG ghi được: máy chủ phải TỪ CHỐI khởi động')
    print('-' * 74)
    import subprocess
    import stat as _stat

    # --- hàm kiểm nói ĐÚNG ở cả hai chiều ---
    ok, loi = web.kiem_ghi_duoc(tm)
    kiem(ok and loi is None, f'Thư mục ghi được -> (True, None) — {ok}, {loi}')
    ok, loi = web.kiem_ghi_duoc(os.path.join(tm, 'khong-co-thu-muc-nay'))
    kiem(not ok and 'khởi động nhanh' in (loi or ''),
         'Thư mục không ghi được -> False, và câu lỗi chỉ đích danh nguyên nhân '
         'hay gặp nhất')
    # Không dùng os.access(W_OK): nó chỉ hỏi bit quyền, mà tình huống đang lo
    # là hệ tệp gắn CHỈ ĐỌC — lúc đó bit quyền vẫn nói "được ghi".
    kiem(not os.path.exists(os.path.join(tm, f'.thu-ghi-{os.getpid()}.tam')),
         'Và tệp thử đã được dọn, không để rác lại trong thư mục dự án')

    # --- TẦNG THẬT: chạy web.py bằng tiến trình con, thư mục chỉ đọc ---
    ro = os.path.join(tm, 'chi-doc')
    os.makedirs(ro, exist_ok=True)
    shutil.copy(os.path.join(GOC_TM, 'cauhinh.json'),
                os.path.join(ro, 'cauhinh.json'))
    dd_tk = os.path.join(tm, 'tk-cho-ca7.json')
    TK.ghi(dd_tk, [TK.ban_ghi_moi('nguoithu', MayChuTam.MAT_KHAU)])
    os.chmod(ro, 0o500)
    try:
        ghi_duoc_that = web.kiem_ghi_duoc(ro)[0]
        try:
            r = subprocess.run(
                [sys.executable, os.path.join(GOC_TM, 'web.py'),
                 '--port', '20994',
                 '--cauhinh', os.path.join(ro, 'cauhinh.json'),
                 '--tai-khoan', dd_tk],
                capture_output=True, text=True, timeout=25)
            ma_ra, ra = r.returncode, (r.stdout or '') + (r.stderr or '')
        except subprocess.TimeoutExpired as e:
            # Lùi bản vá ra thì máy chủ KHỞI ĐỘNG ĐƯỢC và serve_forever() chạy
            # mãi -> subprocess.run ném TimeoutExpired. Bắt lấy và biến thành
            # một mục ĐỎ: bộ thử phải biết đỏ, không phải biết vỡ. Bản đầu của
            # ca này không bắt, và nó VỠ đúng kiểu hỏng số 2.
            ma_ra = 0
            ra = ((e.stdout or b'').decode('utf-8', 'replace')
                  + (e.stderr or b'').decode('utf-8', 'replace')
                  if isinstance(e.stdout, bytes) or isinstance(e.stderr, bytes)
                  else (e.stdout or '') + (e.stderr or ''))
    finally:
        os.chmod(ro, 0o700)

    if ghi_duoc_that:
        # Chạy bằng root thì chmod không chặn được -> ca thử mất khả năng phân
        # biệt. Nói thẳng ra chứ đừng âm thầm xanh.
        kiem(False,
             'Không dựng được thư mục chỉ-đọc (đang chạy bằng root?) — mục này '
             'mất khả năng phân biệt, đừng tin nó')
    else:
        kiem(ma_ra != 0,
             f'Thư mục chỉ đọc -> máy chủ thoát với mã != 0 — {ma_ra} '
             f'(0 nghĩa là nó CHẠY TIẾP, hoặc chạy mãi tới hết giờ)')
        kiem('Mở trình duyệt vào' not in ra,
             'Và CHƯA HỀ in dòng "Mở trình duyệt vào" — không mời ai vào một '
             'máy chủ sẽ hỏng lúc bấm Lưu')
        kiem('KHÔNG GHI ĐƯỢC' in ra and 'khởi động nhanh' in ra,
             f'Câu lỗi nói rõ chuyện gì và chữa thế nào — {ra.strip()[:90]!r}')


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ GIAO DIỆN WEB')
    print('=' * 74)
    with tempfile.TemporaryDirectory() as tm:
        ca_1_giong_dong_lenh(tm)
        ca_2_bat_system_exit(tm)
        ca_3_may_chu(tm)
        ca_4_trang_tinh()
        ca_5_luu_quy_tac(tm)
        ca_6_moi_ca_qua_http()
        ca_7_o_chi_doc(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

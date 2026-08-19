#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ GIAO DIỆN WEB
--------------------------------------------------------------------------
 Chạy:  python tests/thu_web.py

 Ba điều đáng lo nhất ở web.py, kiểm hết:

 1. web.py CHÉP LẠI vòng lặp tìm phương án của xep_tkb.main() (vì main()
    không báo tiến độ, mà một lượt xếp mất ~50 giây). Chép lại thì có
    nguy cơ hai bên lệch nhau. Ca thử chạy cả hai với cùng cấu hình và
    so TỪNG Ô của file Excel xuất ra.
 2. Khai báo sai làm chương trình gốc gọi sys.exit. Trong web thì phải
    bắt lại, nếu không máy chủ chết. Đây là đường đi thường gặp.
 3. Mỗi lúc chỉ một lượt xếp; bấm nữa phải bị chặn.

 Mọi thứ chạy trong thư mục tạm, không đụng cauhinh.json thật.
==========================================================================
"""
import copy
import io
import json
import os
import shutil
import sys
import tempfile
import threading
import time
import urllib.error
import urllib.request
from contextlib import redirect_stdout
from http.server import ThreadingHTTPServer

GOC_TM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_TM)

import xep_tkb as X          # noqa: E402
import web                   # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def cau_hinh_tam(thu_muc, sua=None):
    """Chép cauhinh.json + mau_tkb.xlsx sang thư mục tạm, khoá chặt tim_kiem
       để hai lần chạy cho ra đúng cùng một dãy phương án."""
    cfg = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
    cfg['tim_kiem'] = {'so_lan_thu': 8, 'gioi_han_buoc': 30000,
                       'gioi_han_giay_moi_lan': 10,
                       'gioi_han_tong_giay': 3600, 'seed': 2027}
    if sua:
        sua(cfg)
    dd = os.path.join(thu_muc, 'cauhinh.json')
    with io.open(dd, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False)
    shutil.copy(os.path.join(GOC_TM, 'mau_tkb.xlsx'),
                os.path.join(thu_muc, 'mau_tkb.xlsx'))
    return dd


def o_excel(duong_dan):
    import openpyxl
    ws = openpyxl.load_workbook(duong_dan)['Khối 12']
    return {(r, c): ws.cell(r, c).value
            for r in range(8, 33) for c in range(4, 10)}


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
    o_cli = o_excel(xuat)
    shutil.copy(xuat, os.path.join(tm, 'cli.xlsx'))
    os.remove(xuat)

    web.DUONG_DAN_CAUHINH = dd
    web.dat_lai_trang_thai()
    web._chay(None, None, None, [])
    o_web = o_excel(xuat)
    log = '\n'.join(web.TT['log'])

    kiem(web.TT['loi'] is None, 'Luồng web chạy trót lọt, không lỗi')
    lech = [k for k in o_cli if o_cli[k] != o_web.get(k)]
    kiem(not lech,
         f'Từng ô của vùng D8:I32 giống hệt nhau — {len(o_cli)} ô, {len(lech)} lệch')

    import re
    m1 = re.search(r'Điểm cao nhất: (-?\d+)', ra_cli)
    kiem(m1 and web.TT['diem'] == int(m1.group(1)),
         f'Điểm mềm bằng nhau: dòng lệnh {m1.group(1) if m1 else "?"} '
         f'= web {web.TT["diem"]}')
    m2 = re.search(r'Tổng: (\d+)/(\d+) quy tắc ĐẠT', ra_cli)
    dat_web = len(web.TT['bang']) - web.TT['so_loi']
    kiem(m2 and (int(m2.group(1)), int(m2.group(2)))
         == (dat_web, len(web.TT['bang'])),
         f'Bảng đối chiếu bằng nhau: {m2.group(0) if m2 else "?"} '
         f'= web {dat_web}/{len(web.TT["bang"])}')
    kiem('ĐỐI CHIẾU QUY TẮC' in log and 'Đã xuất file' in log,
         'Khung nhật ký có đúng những phần chương trình vẫn in ra')
    kiem(web.TT['luoi'] and len(web.TT['luoi']['hang']) == 25
         and web.TT['luoi']['tong'] == [24] * 6,
         'Lưới TKB đủ 25 hàng, mỗi lớp 24 tiết')
    kiem(web.TT['gv'] and len(web.TT['gv']['gv']) == 28,
         f'Lịch giáo viên đủ 28 người — {len(web.TT["gv"]["gv"])}')


def ca_2_bat_system_exit(tm):
    print('\nCA 2 — khai báo sai: bắt SystemExit, máy chủ phải sống')
    print('-' * 74)
    tm2 = os.path.join(tm, 'sai')
    os.makedirs(tm2, exist_ok=True)

    def lam_hong(cfg):
        cfg['quy_tac'][1]['tiet_trong_buoi'] = [9, 10]      # buổi chỉ có 5 tiết
    dd = cau_hinh_tam(tm2, lam_hong)

    web.DUONG_DAN_CAUHINH = dd
    web.dat_lai_trang_thai()
    no = None
    try:
        web._chay(None, None, None, [])
    except BaseException as e:                              # kể cả SystemExit
        no = repr(e)
    kiem(no is None, f'_chay() KHÔNG ném gì ra ngoài — {no}')
    kiem(web.TT['loi'] and 'Khai báo sai' in web.TT['loi'],
         'Trạng thái có ghi lỗi')
    log = '\n'.join(web.TT['log'])
    kiem('tiet_trong_buoi' in log and 'Có phải bạn định dùng khoá "tiet"' in log,
         'Nhật ký giữ NGUYÊN VĂN thông báo lỗi, cả dòng gợi ý')
    kiem(web.TT['dang_chay'] is False and web.TT['xong'] is True,
         'Cờ trạng thái về đúng: hết chạy, đã xong')


def ca_3_may_chu(tm):
    print('\nCA 3 — máy chủ HTTP')
    print('-' * 74)
    dd = cau_hinh_tam(tm)
    web.DUONG_DAN_CAUHINH = dd
    web.dat_lai_trang_thai()
    may = ThreadingHTTPServer(('127.0.0.1', 0), web.May)
    may.daemon_threads = True
    threading.Thread(target=may.serve_forever, daemon=True).start()
    dia, cong = may.server_address
    B = f'http://127.0.0.1:{cong}'
    kiem(dia == '127.0.0.1', f'Chỉ bind 127.0.0.1, không mở ra mạng — {dia}')

    def lay(duong, than=None, chu=True):
        """chu=False khi nội dung trả về là nhị phân (file .xlsx)."""
        yc = urllib.request.Request(B + duong, method='POST' if than else 'GET')
        if than is not None:
            yc.add_header('Content-Type', 'application/json')
            than = json.dumps(than).encode()
        try:
            with urllib.request.urlopen(yc, than, timeout=20) as t:
                d = t.read()
                return t.status, d.decode('utf-8') if chu else d
        except urllib.error.HTTPError as e:
            d = e.read()
            return e.code, d.decode('utf-8', 'replace') if chu else d

    ma, than = lay('/')
    kiem(ma == 200 and '<title>' in than and 'Xếp thời khoá biểu' in than,
         'GET / trả trang HTML tiếng Việt')
    for f in ('style.css', 'app.js'):
        kiem(lay('/web/' + f)[0] == 200, f'GET /web/{f}')
    kiem('http://' not in than.replace('http://127.0.0.1', '')
         and 'https://' not in than,
         'Trang không gọi ra ngoài Internet (không CDN)')
    for xau in ('/web/../web.py', '/web/cauhinh.json', '/api/lung-tung'):
        kiem(lay(xau)[0] == 404, f'Chặn đường dẫn lạ {xau}')

    ma, than = lay('/api/quy-tac')
    d = json.loads(than)
    kiem(ma == 200 and len(d['quy_tac']) == 13,
         f'GET /api/quy-tac liệt kê {len(d["quy_tac"])} quy tắc')
    kiem(all({'i', 'loai', 'ghi_chu', 'bat'} <= set(r) for r in d['quy_tac']),
         'Mỗi dòng có đủ ghi_chu + loai + cờ bật/tắt')

    ma, _ = lay('/api/xep', {'so_lan': '3', 'tat': []})
    kiem(ma == 200, 'POST /api/xep nhận lệnh')
    ma2, than2 = lay('/api/xep', {'tat': []})
    kiem(ma2 == 409 and 'Đang xếp' in than2,
         f'Bấm lần nữa lúc đang chạy bị chặn — {ma2} {json.loads(than2).get("loi")}')

    for _ in range(200):
        t = json.loads(lay('/api/trang-thai?tu=0')[1])
        if t['xong']:
            break
        time.sleep(0.2)
    kiem(t['xong'] and not t['dang_chay'], 'Hỏi trạng thái tới lúc xong')
    kiem(t['log_het'] > 10 and len(t['log_moi']) == t['log_het'],
         'Nhật ký lấy được theo lô, có đánh dấu đã đọc tới đâu')
    kiem(json.loads(lay('/api/trang-thai?tu=%d' % t['log_het'])[1])['log_moi'] == [],
         'Hỏi tiếp từ vị trí cũ thì không trả lại dòng đã đọc')
    ma, than = lay('/api/tai-ve', chu=False)
    kiem(ma == 200 and than[:2] == b'PK' and len(than) > 10000,
         f'Tải được file .xlsx thật ({len(than)} byte, đúng chữ ký ZIP)')
    may.shutdown()


def ca_4_trang_tinh():
    print('\nCA 4 — trang tĩnh: JS và HTML khớp nhau')
    print('-' * 74)
    import re
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
    duong = set(re.findall(r"fetch\('(/api/[^'?]+)", js)) \
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
    print('\nCA 5 — lưu quy tắc vào cauhinh.json')
    print('-' * 74)
    tm4 = os.path.join(tm, 'luu')
    os.makedirs(tm4, exist_ok=True)
    dd = cau_hinh_tam(tm4)
    web.DUONG_DAN_CAUHINH = dd
    truoc = X.doc_cau_hinh(dd)

    kq = web.luu_quy_tac({4, 5})
    bak = os.path.join(tm4, 'cauhinh.bak.json')
    kiem(os.path.exists(bak), 'Có sao lưu thành cauhinh.bak.json')
    kiem(X.doc_cau_hinh(bak) == truoc, 'Bản sao lưu đúng là nội dung cũ')

    sau = X.doc_cau_hinh(dd)
    kiem(list(sau) == list(truoc), 'Thứ tự khoá cấp cao nhất giữ nguyên')
    kiem(list(sau['quy_tac'][0]) == list(truoc['quy_tac'][0]),
         'Thứ tự khoá bên trong quy tắc giữ nguyên')
    kiem([i for i, r in enumerate(sau['quy_tac']) if r.get('bat') is False]
         == [4, 5], f'Đúng 2 quy tắc bị tắt, {kq["doi"]} dòng đổi')
    kiem({k: v for k, v in sau.items() if k != 'quy_tac'}
         == {k: v for k, v in truoc.items() if k != 'quy_tac'},
         'Mọi mục khác của file y nguyên')

    web.luu_quy_tac(set())
    lai = X.doc_cau_hinh(dd)
    kiem(all('bat' not in r for r in lai['quy_tac']),
         'Bật lại thì khoá "bat" biến mất hẳn, không để rác')
    kiem(len(lai['_quy_tac_de_san_chua_bat']) == 7
         and all(r['bat'] is False for r in lai['_quy_tac_de_san_chua_bat']),
         'Không đụng tới mục _quy_tac_de_san_chua_bat')


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
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

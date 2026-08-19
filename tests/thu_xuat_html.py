#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: TRANG WEB TĨNH tkb_web.html
--------------------------------------------------------------------------
 Chạy:  python tests/thu_xuat_html.py

 Trang này đưa lên Internet cho giáo viên và học sinh xem, mà cũng phải
 mở được bằng cách bấm đúp file từ USB khi trường mất mạng. Nên hai điều
 phải chắc:
   - Tự chứa hoàn toàn: không CDN, không font ngoài, không gọi mạng.
   - Dữ liệu trong trang khớp TỪNG Ô với file Excel đem in.
==========================================================================
"""
import copy
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

GOC_TM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_TM)

import xep_tkb as X          # noqa: E402
import xuat_html as XH       # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def dung(tm):
    """Xếp một lượt trong thư mục tạm, xuất cả .xlsx lẫn .html."""
    cfg = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
    cfg['tim_kiem'] = {'so_lan_thu': 6, 'gioi_han_buoc': 30000,
                       'gioi_han_giay_moi_lan': 10,
                       'gioi_han_tong_giay': 3600, 'seed': 2027}
    shutil.copy(os.path.join(GOC_TM, 'mau_tkb.xlsx'),
                os.path.join(tm, 'mau_tkb.xlsx'))
    bt = X.BaiToan(cfg)
    kqt = X.tim_phuong_an(bt, cfg['tim_kiem'])
    assert kqt.tot is not None, 'không xếp được, ca thử không chạy tiếp được'
    xlsx = X.xuat_excel(bt, kqt.tot, os.path.join(tm, 'mau_tkb.xlsx'),
                        os.path.join(tm, 'TKB.xlsx'))
    html = XH.xuat_html(bt, kqt.tot, os.path.join(tm, 'tkb_web.html'))
    return bt, kqt.tot, xlsx, io.open(html, encoding='utf-8').read()


def tach(trang):
    d = re.search(r'<script id="du-lieu" type="application/json">(.*?)</script>',
                  trang, re.S).group(1)
    js = re.search(r'/\*JS-BAT-DAU\*/(.*?)/\*JS-KET-THUC\*/', trang, re.S).group(1)
    return json.loads(d.replace('<\\/', '</')), js


# --------------------------------------------------------------------------
def ca_1_tu_chua(trang, js):
    print('\nCA 1 — tự chứa hoàn toàn, mở bằng file:// vẫn chạy')
    print('-' * 74)
    ngoai = re.findall(r'https?://[^\s"\'<>)]+', trang)
    kiem(not ngoai, f'Không có địa chỉ http:// hay https:// nào — {ngoai[:3]}')
    tai = re.findall(r'<(?:script|link|img|iframe)[^>]*(?:src|href)="([^"]+)"', trang)
    kiem(not tai, f'Không tải tệp ngoài nào — {tai}')
    for tu in ('fetch(', 'XMLHttpRequest', 'localStorage', 'sessionStorage',
               '@import', 'fonts.googleapis'):
        kiem(tu not in trang, f'Không dùng {tu}')
    kiem(trang.lstrip().startswith('<!DOCTYPE html>')
         and 'charset="utf-8"' in trang, 'Là một file HTML đầy đủ, khai utf-8')
    kiem('name="viewport"' in trang, 'Có thẻ viewport cho điện thoại')
    kiem('system-ui' in trang and '@font-face' not in trang,
         'Dùng font hệ thống, không nhúng font')
    kiem('@media (max-width: 560px)' in trang, 'Có phần CSS riêng cho màn hình hẹp')
    kiem('overflow-x: auto' in trang, 'Bảng cả khối cuộn ngang được')
    kiem(len(trang) < 400_000, f'File gọn, {len(trang) // 1024} KB')


def ca_2_khop_tung_o(bt, pa, xlsx, d):
    print('\nCA 2 — dữ liệu trong trang khớp TỪNG Ô với file Excel')
    print('-' * 74)
    import openpyxl
    ws = openpyxl.load_workbook(xlsx)['Khối 12']
    LOP, THU, TIET = d['lop'], d['cac_thu'], d['cac_tiet']

    tu_excel = {}
    for r in range(8, 33):
        for c in range(4, 10):
            v = ws.cell(r, c).value
            if v:
                tu_excel[(LOP[c - 4], (r - 8) // 5, (r - 8) % 5)] = v
    tu_html = {(o[0], o[1], o[2]): f'{o[3]} ({o[4]})' for o in d['o']}

    kiem(len(tu_excel) == 144 and len(tu_html) == 144,
         f'Cùng 144 ô có tiết trong vùng D8:I32 — Excel {len(tu_excel)}, '
         f'HTML {len(tu_html)}')
    so_o = len(LOP) * len(THU) * len(TIET)
    lech = [k for k in set(tu_excel) | set(tu_html)
            if tu_excel.get(k) != tu_html.get(k)]
    kiem(not lech and so_o == 150,
         f'So đủ {so_o} ô của vùng D8:I32 (6 lớp x 5 ngày x 5 tiết): '
         f'{len(lech)} lệch')
    if lech:
        for k in lech[:5]:
            print(f'      {k}: Excel={tu_excel.get(k)!r} HTML={tu_html.get(k)!r}')


def ca_3_du_lop_du_gv(bt, d):
    print('\nCA 3 — đủ lớp, đủ giáo viên, đúng số tiết')
    print('-' * 74)
    kiem(d['lop'] == list(bt.lop) and len(d['lop']) == 6,
         f'Đủ 6 lớp — {d["lop"]}')
    kiem(all(d['gvcn'].get(l) for l in d['lop']), 'Lớp nào cũng có tên GVCN')

    that = sorted({c.gv for c in bt.cac_cum if not c.la_trong})
    kiem(d['gv'] == that, f'Đủ {len(that)} giáo viên, đúng danh sách')

    dem_that = {}
    for c in bt.cac_cum:
        if not c.la_trong:
            dem_that[c.gv] = dem_that.get(c.gv, 0) + c.size
    dem_html = {}
    for o in d['o']:
        dem_html[o[4]] = dem_html.get(o[4], 0) + 1
    sai = {g: (dem_that[g], dem_html.get(g)) for g in dem_that
           if dem_that[g] != dem_html.get(g)}
    kiem(not sai, f'Mỗi giáo viên đúng số tiết — {len(sai)} người sai {sai}')

    dem_lop = {}
    for o in d['o']:
        dem_lop[o[0]] = dem_lop.get(o[0], 0) + 1
    kiem(set(dem_lop.values()) == {24}, f'Mỗi lớp đúng 24 tiết — {dem_lop}')
    kiem(d['tuan'] == bt.cfg['thong_tin']['tuan'] and d['xuat_luc'],
         f'Có tên tuần và thời điểm xuất — "{d["tuan"]}", xuất {d["xuat_luc"]}')


def ca_4_ba_che_do_va_dia_chi(trang, js):
    print('\nCA 4 — ba chế độ xem và ghi lựa chọn vào địa chỉ trang')
    print('-' * 74)
    for che in ('lop', 'gv', 'khoi'):
        kiem(f'data-che="{che}"' in trang, f'Có nút chế độ "{che}"')
    for ten in ('Theo lớp', 'Theo giáo viên', 'Cả khối'):
        kiem(ten in trang, f'Nhãn tiếng Việt có dấu: "{ten}"')
    kiem('veTheoLop' in js and 'veTheoGV' in js and 'veCaKhoi' in js,
         'Có đủ ba hàm vẽ ba chế độ')
    kiem('location.hash' in js and re.search(r"\(lop\|gv\)=", js),
         'Lựa chọn ghi vào địa chỉ trang dạng #lop=12B3')
    kiem('onhashchange' in js, 'Đổi địa chỉ trang thì vẽ lại, tải lại không mất')


def ca_5_cu_phap_js(tm, js):
    print('\nCA 5 — cú pháp JS')
    print('-' * 74)
    node = shutil.which('node') or shutil.which('nodejs')
    if not node:
        kiem(True, 'Bỏ qua node --check: máy này không có node '
                   '(ca thử không bắt buộc phải có)')
        return
    dd = os.path.join(tm, 'kiem.js')
    io.open(dd, 'w', encoding='utf-8').write(js)
    r = subprocess.run([node, '--check', dd], capture_output=True, text=True)
    kiem(r.returncode == 0,
         f'node --check: {"hợp lệ" if r.returncode == 0 else r.stderr.strip()[:120]}')


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ TRANG WEB TĨNH tkb_web.html')
    print('=' * 74)
    with tempfile.TemporaryDirectory() as tm:
        bt, pa, xlsx, trang = dung(tm)
        d, js = tach(trang)
        ca_1_tu_chua(trang, js)
        ca_2_khop_tung_o(bt, pa, xlsx, d)
        ca_3_du_lop_du_gv(bt, d)
        ca_4_ba_che_do_va_dia_chi(trang, js)
        ca_5_cu_phap_js(tm, js)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

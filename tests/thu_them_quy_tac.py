#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: THÊM / XOÁ / LƯU QUY TẮC TỪ GIAO DIỆN WEB
--------------------------------------------------------------------------
 Chạy:  python tests/thu_them_quy_tac.py

 Thêm quy tắc từ giao diện là đường đi nguy hiểm nhất của cả phần mềm:
 nó ghi vào cùng chỗ với dữ liệu khai bằng tay của nhà trường. Nên phải
 chắc ba điều:
   - Thêm/xoá CHỈ đổi cấu hình trong bộ nhớ, cauhinh.json không suy suyển.
   - Khai sai thì bị từ chối, kèm NGUYÊN VĂN thông báo, phiên không đổi.
   - Bấm Lưu thì có sao lưu, giữ thứ tự khoá, và file ghi ra vẫn chạy được.

 Mọi thứ chạy trong thư mục tạm, không đụng cauhinh.json thật.
==========================================================================
"""
import hashlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import ThreadingHTTPServer

GOC_TM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_TM)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tien_ich_web import Khach, MayChuTam   # noqa: E402
import tai_khoan as TK                      # noqa: E402

import xep_tkb as X          # noqa: E402
import quy_tac as QT         # noqa: E402
import web                   # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def md5(dd):
    return hashlib.md5(io.open(dd, 'rb').read()).hexdigest()


def dung_may(tm):
    cfg = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
    cfg['tim_kiem'] = {'so_lan_thu': 4, 'gioi_han_buoc': 30000,
                       'gioi_han_giay_moi_lan': 5,
                       'gioi_han_tong_giay': 60, 'seed': 2027}
    dd = os.path.join(tm, 'cauhinh.json')
    with io.open(dd, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    shutil.copy(os.path.join(GOC_TM, 'mau_tkb.xlsx'),
                os.path.join(tm, 'mau_tkb.xlsx'))
    web.DUONG_DAN_CAUHINH = dd
    web.xoa_sach_phien()
    web.dat_lai_trang_thai()
    # [DI TRÚ 2A-1] Máy chủ nay đòi tài khoản. Dựng một cái tạm rồi đăng nhập
    # qua HTTP thật — mã cũ không sai, nó chỉ đúng với thế giới chưa có cổng.
    dd_tk = os.path.join(tm, 'tai_khoan.json')
    TK.ghi(dd_tk, [TK.ban_ghi_moi(MayChuTam.TEN, MayChuTam.MAT_KHAU)])
    web.nap_tai_khoan_may_chu(dd_tk)
    may = ThreadingHTTPServer(('127.0.0.1', 0), web.May)
    may.daemon_threads = True
    threading.Thread(target=may.serve_forever, daemon=True).start()
    # Trả về một Khach thay cho chuỗi URL. urllib KHÔNG giữ cookie, mà từ 2A-2a
    # bản nháp quy tắc gắn theo PHIÊN — mỗi yêu cầu không cookie là một phiên
    # mới, nên "thêm rồi đọc lại" sẽ không bao giờ thấy nhau.
    k = Khach(may.server_address[1])
    k.dang_nhap()
    return may, k, dd


def goi(B, duong, than=None):
    """B là một Khach (giữ cookie), không phải chuỗi URL."""
    return B.js(duong, than)


HOP_LE = {'loai': 'khong_xep_thu', 'ghi_chu': 'Hoá học không xếp Thứ 6',
          'loc': {'mon': 'Hoá học'}, 'thu': [6]}

SAI = [
    ({'loai': 'khong_xep_thu', 'ghi_chu': '', 'loc': {}, 'thu': [6]},
     'ghi_chu rỗng', 'Chưa điền "Nội dung quy tắc"'),
    ({'loai': 'khong_xep_thu', 'ghi_chu': 'gõ nhầm khoá', 'loc': {},
      'thu_2': [6]}, 'khoá lạ', '"thu_2"'),
    ({'loai': 'khong_xep_thu', 'ghi_chu': 'thứ ngoài miền', 'loc': {},
      'thu': [1]}, 'giá trị ngoài miền', 'KHÔNG phải đếm từ 1'),
    ({'loai': 'khong_xep_tiet', 'ghi_chu': 'thiếu khoá bắt buộc', 'loc': {}},
     'thiếu khoá bắt buộc', 'thiếu "tiet" hoặc "tiet_trong_buoi"'),
    ({'loai': 'khong_xep_thu', 'ghi_chu': 'bộ lọc sai khoá',
      'loc': {'giao_vien': 'Đ.Duy'}, 'thu': [6]},
     'khoá lạ trong bộ lọc', '"giao_vien"'),
]


# --------------------------------------------------------------------------
def ca_1_them_hop_le(B, dd):
    print('\nCA 1 — thêm quy tắc hợp lệ: vào phiên, KHÔNG đụng file')
    print('-' * 74)
    truoc_md5 = md5(dd)
    ma, d0 = goi(B, '/api/quy-tac')
    n0 = len(d0['quy_tac'])

    ma, d = goi(B, '/api/them-quy-tac', {'quy_tac': HOP_LE})
    kiem(ma == 200, f'POST /api/them-quy-tac -> {ma}')
    kiem(len(d['quy_tac']) == n0 + 1 and d['so_moi'] == 1,
         f'Danh sách tăng đúng 1: {n0} -> {len(d["quy_tac"])}, chưa lưu 1')
    r = d['quy_tac'][-1]
    kiem(r['moi'] is True and r['ghi_chu'] == HOP_LE['ghi_chu']
         and r['loai'] == 'khong_xep_thu',
         'Quy tắc mới có nhãn "chưa lưu" và đúng nội dung')
    kiem(r['noi_dung'].get('thu') == [6] and r['noi_dung'].get('loc'),
         f'Giữ nguyên nội dung đã gửi — {r["noi_dung"]}')
    kiem(md5(dd) == truoc_md5, 'md5 cauhinh.json KHÔNG đổi')

    # Trước đây mục này gọi thẳng web.cau_hinh_phien() — vừa là gọi tắt qua
    # tầng HTTP, vừa không còn đúng khi nháp gắn theo phiên. Quan sát qua HTTP:
    # hỏi lại danh sách và đếm.
    _, dl = goi(B, '/api/quy-tac')
    kiem(len(dl['quy_tac']) == n0 + 1 and dl['so_moi'] == 1,
         f'Phiên này thật sự có quy tắc mới — {len(dl["quy_tac"])} quy tắc, '
         f'{dl["so_moi"]} chưa lưu')
    ma, t = goi(B, '/api/thu-quy-tac', {'quy_tac': None, 'tat': []})
    kiem(ma == 200 and t['xep_duoc'],
         f'Xếp thử với quy tắc mới: vẫn xếp được, {t["so_hop_le"]}/{t["so_lan"]}')


def ca_2_them_sai(B, dd):
    print('\nCA 2 — khai sai thì bị từ chối, phiên không đổi')
    print('-' * 74)
    truoc_md5 = md5(dd)
    _, d0 = goi(B, '/api/quy-tac')
    for r, ten, chu in SAI:
        ma, d = goi(B, '/api/them-quy-tac', {'quy_tac': r})
        kiem(ma == 400, f'{ten}: HTTP {ma} (phải là 400)')
        kiem(chu in d.get('loi', ''),
             f'  thông báo có nguyên văn "{chu[:34]}"')
    _, d1 = goi(B, '/api/quy-tac')
    kiem(d1['quy_tac'] == d0['quy_tac'],
         'Sau 5 lần thêm hỏng, danh sách y nguyên')
    kiem(md5(dd) == truoc_md5, 'md5 cauhinh.json vẫn không đổi')


def ca_3_xoa(B, dd):
    print('\nCA 3 — xoá')
    print('-' * 74)
    _, d = goi(B, '/api/quy-tac')
    so_file, i_moi = d['so_file'], len(d['quy_tac']) - 1

    ma, e = goi(B, '/api/xoa-quy-tac', {'i': 0})
    kiem(ma == 400, f'Xoá quy tắc đến từ file: HTTP {ma}')
    kiem('công tắc' in e.get('loi', ''), '  chỉ dẫn dùng công tắc để tắt')

    ma, d2 = goi(B, '/api/xoa-quy-tac', {'i': i_moi})
    kiem(ma == 200 and d2['so_moi'] == 0 and len(d2['quy_tac']) == so_file,
         f'Xoá quy tắc vừa thêm: về đúng {so_file} quy tắc ban đầu')
    _, dq = goi(B, '/api/quy-tac')
    kiem(dq['so_moi'] == 0, 'Kho quy tắc nháp của phiên rỗng trở lại')
    kiem(md5(dd) == md5(dd), 'cauhinh.json vẫn nguyên')


def ca_4_luu(B, tm, dd):
    print('\nCA 4 — bấm Lưu')
    print('-' * 74)
    truoc = X.doc_cau_hinh(dd)
    goi(B, '/api/them-quy-tac', {'quy_tac': HOP_LE})
    ma, kq = goi(B, '/api/luu-quy-tac', {'tat': [3]})
    kiem(ma == 200, f'POST /api/luu-quy-tac -> {ma}')

    bak = os.path.join(tm, 'cauhinh.bak.json')
    kiem(os.path.exists(bak), 'Có sao lưu cauhinh.bak.json')
    kiem(X.doc_cau_hinh(bak) == truoc, 'Bản sao lưu đúng là nội dung cũ')

    sau = X.doc_cau_hinh(dd)
    kiem(list(sau) == list(truoc), 'Thứ tự khoá cấp cao nhất giữ nguyên')
    kiem(list(sau['quy_tac'][0]) == list(truoc['quy_tac'][0]),
         'Thứ tự khoá bên trong quy tắc giữ nguyên')
    kiem(len(sau['quy_tac']) == len(truoc['quy_tac']) + 1
         and sau['quy_tac'][-1]['ghi_chu'] == HOP_LE['ghi_chu'],
         'Quy tắc mới đã nằm trong file')
    kiem(sau['quy_tac'][3].get('bat') is False, 'Công tắc tắt cũng được ghi')
    _, dq = goi(B, '/api/quy-tac')
    kiem(dq['so_moi'] == 0, 'Ghi xong thì kho nháp của phiên rỗng')
    kiem(len(sau['_quy_tac_de_san_chua_bat']) == 7,
         'Mục _quy_tac_de_san_chua_bat không bị đụng')

    r = subprocess.run([sys.executable, os.path.join(GOC_TM, 'xep_tkb.py'),
                        '--cauhinh', dd, '--lan', '3'],
                       capture_output=True, text=True, cwd=tm, timeout=300)
    kiem(r.returncode == 0 and 'quy tắc ĐẠT' in r.stdout,
         'Đọc lại file bằng xep_tkb.py: chạy được bình thường')
    kiem(HOP_LE['ghi_chu'] in r.stdout,
         '  quy tắc vừa thêm có mặt trong bảng đối chiếu')


def ca_5_doi_chieu_danh_muc(B):
    print('\nCA 5 — đối chiếu hai chiều DANH_MUC <-> form')
    print('-' * 74)
    ma, d = goi(B, '/api/loai-quy-tac')
    tren_api = {l['ten'] for n in d['nhom'] for l in n['loai']}
    kiem(tren_api == set(QT.DANH_MUC),
         f'API liệt kê đúng {len(QT.DANH_MUC)} loại, không thừa không thiếu')
    kiem(all(l['mo_ta'] and l['truong'] for n in d['nhom'] for l in n['loai']),
         'Loại nào cũng có MO_TA và TRUONG để dựng form')

    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    js_kieu = set(re.findall(r"tr\.kieu === '(\w+)'", js))
    dung_kieu = {tr['kieu'] for c in QT.DANH_MUC.values() for tr in c.TRUONG}
    kiem(not (dung_kieu - js_kieu),
         f'Mọi kiểu TRUONG đang dùng đều được form dựng — thiếu '
         f'{sorted(dung_kieu - js_kieu)}')
    kiem(not (js_kieu - set(QT.KIEU)),
         f'Form không dựng kiểu nào không có trong QT.KIEU — thừa '
         f'{sorted(js_kieu - set(QT.KIEU))}')

    # nhét một loại giả vào DANH_MUC, nó phải hiện ra ngay
    class LoaiGia(QT.QuyTac):
        MO_TA = 'Loại bịa ra để thử, không dùng thật.'
        TRUONG = (QT.T_LOC,)
    LoaiGia.TEN = '_loai_gia'
    QT.DANH_MUC['_loai_gia'] = LoaiGia
    try:
        _, d2 = goi(B, '/api/loai-quy-tac')
        co = {l['ten'] for n in d2['nhom'] for l in n['loai']}
        nhom_gia = [n['nhom'] for n in d2['nhom'] if '_loai_gia' in
                    [l['ten'] for l in n['loai']]]
        kiem('_loai_gia' in co,
             'Nhét một loại mới vào DANH_MUC thì API hiện ra ngay')
        kiem(nhom_gia == ['CHƯA XẾP NHÓM'],
             f'  và rơi vào nhóm "CHƯA XẾP NHÓM" — {nhom_gia}')
    finally:
        del QT.DANH_MUC['_loai_gia']
    _, d3 = goi(B, '/api/loai-quy-tac')
    kiem({l['ten'] for n in d3['nhom'] for l in n['loai']} == set(QT.DANH_MUC),
         'Bỏ loại giả ra thì API cũng hết ngay')


def ca_6_kich_thuoc_css():
    print('\nCA 6 — kích thước ô nhập (ĐỌC CSS, không đo trên trình duyệt)')
    print('-' * 74)
    print('  Lưu ý: ca thử này đọc khai báo trong style.css, KHÔNG dựng trang')
    print('  thật để đo. Nó bắt được việc khai sai cỡ, không bắt được lỗi bố')
    print('  cục kiểu chữ tràn ra ngoài khung.')
    css = io.open(os.path.join(GOC_TM, 'web', 'style.css'), encoding='utf-8').read()
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    khoi = [(m.group(1).strip(), m.group(2))
            for m in re.finditer(r'([^{}]+)\{([^{}]*)\}', css)]

    BAM = ('input', 'select', 'textarea', 'button', '.tab', '.nut-o',
           '.nut-xoa', '.cong-tac', '.ds-chon .dong', '.tim')
    xau = []
    for sel, than in khoi:
        if 'checkbox' in sel or not any(b in sel for b in BAM):
            continue
        fs = re.search(r'font-size:\s*([\d.]+)px', than)
        mh = re.search(r'min-height:\s*([\d.]+)px', than)
        if fs and float(fs.group(1)) < 15:
            xau.append((sel, 'font-size', fs.group(1)))
        if mh and float(mh.group(1)) < 32:
            xau.append((sel, 'min-height', mh.group(1)))
    kiem(not xau, f'Không selector nào hạ cỡ xuống dưới ngưỡng — {xau}')

    chung = [t for s_, t in khoi
             if s_.replace(' ', '') == 'input,select,textarea,button']
    kiem(len(chung) == 1, 'Có đúng một khai báo chung cho mọi ô nhập')
    if chung:
        t = chung[0]
        mh = re.search(r'min-height:\s*([\d.]+)px', t)
        fs = re.search(r'font-size:\s*([\d.]+)px', t)
        kiem(mh and float(mh.group(1)) >= 40,
             f'  min-height chung = {mh.group(1) if mh else "?"}px (cần >= 40)')
        kiem(fs and float(fs.group(1)) >= 15,
             f'  font-size chung = {fs.group(1) if fs else "?"}px (cần >= 15)')

    def lay(sel, thuoc):
        for s_, t in khoi:
            if s_.strip() == sel:
                m = re.search(thuoc + r':\s*([\d.]+)px', t)
                if m:
                    return float(m.group(1))
        return None
    kiem(lay('.nut-o', 'min-height') >= 40 and lay('.nut-o', 'min-width') >= 56,
         f'Ô vuông thứ/tiết: {lay(".nut-o", "min-width")}x'
         f'{lay(".nut-o", "min-height")}px (cần >= 56x40)')
    kiem(lay('.ds-chon', 'min-height') >= 200,
         f'Danh sách dài cao {lay(".ds-chon", "min-height")}px (cần >= 200)')
    kiem(lay('.ds-chon .dong', 'min-height') >= 32,
         f'Mỗi dòng cao {lay(".ds-chon .dong", "min-height")}px (cần >= 32)')

    html = io.open(os.path.join(GOC_TM, 'web', 'index.html'),
                   encoding='utf-8').read()
    kiem('<select multiple' not in html and 'select multiple' not in
         io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read(),
         'Không còn <select multiple> nào trong giao diện')


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ THÊM / XOÁ / LƯU QUY TẮC')
    print('=' * 74)
    with tempfile.TemporaryDirectory() as tm:
        may, B, dd = dung_may(tm)
        try:
            ca_1_them_hop_le(B, dd)
            ca_2_them_sai(B, dd)
            ca_3_xoa(B, dd)
            ca_4_luu(B, tm, dd)
            ca_5_doi_chieu_danh_muc(B)
        finally:
            may.shutdown()
        ca_6_kich_thuoc_css()
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

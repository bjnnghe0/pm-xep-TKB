#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: THÊM / XOÁ / LƯU QUY TẮC TỪ GIAO DIỆN WEB
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_them_quy_tac.py

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
    # .get() chứ không r['noi_dung'] trần: bản hỏng cần bắt ở đây là bản
    # KHÔNG chở 'noi_dung' về nữa, và trên bản đó phép bóc trần ném KeyError —
    # ca thử VỠ ngay ở CA 1, mọi ca sau không bao giờ chạy.
    nd = r.get('noi_dung')
    kiem(isinstance(nd, dict) and nd.get('thu') == [6] and nd.get('loc'),
         f'Giữ nguyên nội dung đã gửi — {nd if nd is not None else "KHÔNG CÓ khoá noi_dung"}')
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
    kiem(sau['_quy_tac_de_san_chua_bat'] == truoc['_quy_tac_de_san_chua_bat'],
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
        NHAN = 'Nhãn bịa để thử'
        MAU_CAU = '{loc} — loại bịa để thử.'
        TRUONG = (QT.T_LOC,)
    LoaiGia.TEN = '_loai_gia'
    # NHÉT THẲNG vào DANH_MUC, cố ý đi vòng @dang_ky: mục này thử cái LƯỚI ĐỠ
    # lúc chạy (nhóm "CHƯA XẾP NHÓM"), không thử cửa ép lúc nạp mô-đun. Hai
    # thứ khác nhau, và dự án cần cả hai — cửa ép chặn người thêm loại thứ 18,
    # lưới đỡ chặn mọi đường vòng còn lại.
    QT.DANH_MUC['_loai_gia'] = LoaiGia
    try:
        _, d2 = goi(B, '/api/loai-quy-tac')
        if not isinstance(d2, dict) or 'nhom' not in d2:
            # ĐỎ chứ không VỠ: bản đầu để KeyError bay lên và cả ca thử chết
            # giữa chừng, mọi mục sau không bao giờ chạy.
            kiem(False, f'/api/loai-quy-tac không trả danh mục — {str(d2)[:80]}')
            d2 = {'nhom': []}
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

    # ---- THẺ QUY TẮC (Đợt 3 phần 1): chữ thầy cô ĐỌC phải >= 15px ----
    # Khai TỪNG TÊN chứ không quét cả tệp: lưới TKB và khung nhật ký cố ý dùng
    # cỡ nhỏ hơn để nhét vừa bảng, đó là đánh đổi khác. Danh sách này là những
    # dòng chữ trên màn hình Quy tắc — thứ thầy cô đọc để hiểu quy tắc làm gì.
    THE = ('.the-chu', '.the-loai', '.the-so', '.nhom-ten', '.nhom-dem',
           '.trong-rong')
    thieu, nho = [], []
    for ten in THE:
        m = re.search(re.escape(ten) + r'\s*\{([^{}]*)\}', css)
        if not m:
            thieu.append(ten)
            continue
        fs = re.search(r'font-size:\s*([\d.]+)px', m.group(1))
        if not fs:
            thieu.append(ten + ' (không khai font-size)')
        elif float(fs.group(1)) < 15:
            nho.append((ten, fs.group(1)))
    kiem(not thieu, f'Mọi lớp chữ của thẻ quy tắc đều có khai cỡ — thiếu {thieu}')
    kiem(not nho, f'và không lớp nào dưới 15px — {nho}')

    # Lớp cũ của BẢNG quy tắc phải biến mất hẳn cùng lúc với bảng. Để lại một
    # khai báo mồ côi là để dành cái bẫy: người sau gõ class="mem" tưởng còn ăn.
    moc = [t for t in ('.mem', '.moi', '.loai')
           if re.search(r'(^|\n)' + re.escape(t) + r'\s*\{', css)]
    kiem(not moc, f'Không còn lớp CSS mồ côi của bảng cũ — {moc}')

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


def ca_7_kiem_nhanh_sau_luu(tm):
    """Cảnh báo sớm sau khi Lưu — và bất biến QUAN TRỌNG NHẤT của nó:
       máy chủ KHÔNG BAO GIỜ được khẳng định "vô nghiệm" khi nó chỉ hết giờ.

       Một giây không đủ để chứng minh vô nghiệm. Nói quá dù chỉ một lần là
       thầy cô thôi tin mọi cảnh báo sau — thà nói "đáng ngờ, chưa kết luận
       được" còn hơn nói chắc rồi sai.
    """
    print('\nCA 7 — kiểm nhanh sau khi Lưu: nhanh, và KHÔNG nói quá')
    print('-' * 74)
    import time as _t
    from tien_ich_web import cau_hinh_tam

    # --- (a) cấu hình LÀNH: phải ra lời giải, phải nhanh, và KHÔNG vet_can ---
    tmx = os.path.join(tm, 'q7a')
    os.makedirs(tmx, exist_ok=True)
    dd_a = cau_hinh_tam(tmx)
    with MayChuTam(dd_a) as (k, _):
        t0 = _t.perf_counter()
        ma, kq = k.js('/api/thu-quy-tac', {'nhanh': True, 'tat': []})
        giay = _t.perf_counter() - t0
        kiem(ma == 200 and kq.get('co_loi_giai') is True,
             f'Cấu hình lành: kiểm nhanh tìm được phương án — {ma}, {kq}')
        kiem(kq.get('so_lan') == 1,
             f'Đúng MỘT lần thử, không phải 30 như đường thử quy tắc — '
             f'{kq.get("so_lan")}')
        kiem(giay < 3,
             f'Và trả lời trong {giay:.2f}s — nút Lưu không được biến thành '
             f'chỗ đợi')
        kiem(kq.get('vet_can') is False,
             f'vet_can=False khi CÓ lời giải — không bao giờ được khẳng định '
             f'vô nghiệm lúc vừa tìm ra phương án. {kq.get("vet_can")!r}')

        # Bắn 5 lần: cờ vet_can phải ổn định, không chớp.
        cac = [k.js('/api/thu-quy-tac', {'nhanh': True, 'tat': []})[1]
               .get('vet_can') for _ in range(5)]
        kiem(set(cac) == {False},
             f'5 lần liên tiếp đều vet_can=False, không chớp — {cac}')

    # --- (b) cấu hình VÔ NGHIỆM THẬT (nhỏ, vét cạn được): vet_can phải True --
    def teo_lai(cfg):
        """Bài toán tí hon vừa khít số ô nhưng bí về tổ hợp: 1 lớp, 2 ngày,
           hai môn bị ép chung vào MỘT ngày."""
        mot = cfg['lop'][0]['ten']
        cfg['lop'] = [cfg['lop'][0]]
        cfg['phan_cong'] = {'_doc': cfg['phan_cong']['_doc'],
                            mot: [['Toán học', 'M.Hạnh', 6],
                                  ['Ngữ văn', 'H.Trang', 4]]}
        cfg['khung_gio'] = {'cac_thu': [2, 3], 'buoi': 'Chiều',
                            'cac_tiet': [6, 7, 8, 9, 10]}
        cfg['quy_tac'] = [
            {'loai': 'chi_xep_thu', 'ghi_chu': 'Văn dồn vào Thứ 2',
             'loc': {'mon': 'Ngữ văn'}, 'thu': [2]},
            {'loai': 'chi_xep_thu', 'ghi_chu': 'Toán dồn vào Thứ 2',
             'loc': {'mon': 'Toán học'}, 'thu': [2]}]

    tmb = os.path.join(tm, 'q7b')
    os.makedirs(tmb, exist_ok=True)
    dd_b = cau_hinh_tam(tmb, sua=teo_lai)
    with MayChuTam(dd_b) as (k, _):
        ma, kq = k.js('/api/thu-quy-tac', {'nhanh': True, 'tat': []})
        kiem(ma == 200 and kq.get('co_loi_giai') is False,
             f'Cấu hình vô nghiệm: không ra lời giải — {ma}, {kq}')
        kiem(kq.get('vet_can') is True,
             f'Và vet_can=True — bộ giải VÉT CẠN được, nên lần này khẳng định '
             f'"chắc chắn" là đúng. {kq.get("vet_can")!r}')

    # --- (c) HẠN GIỜ chứ không vô nghiệm: vet_can phải là False -------------
    # Bài toán thật (90 cụm) không bao giờ vét cạn nổi trong một giây. Ép nó
    # không tìm ra bằng một quy tắc mâu thuẫn, rồi đòi máy chủ THÚ NHẬN là nó
    # chỉ hết giờ chứ không chứng minh được gì.
    tmc = os.path.join(tm, 'q7c')
    os.makedirs(tmc, exist_ok=True)

    def bi_nhung_to(cfg):
        """Ép ba môn vào ba ngày. ĐÚNG hình dạng lỗi thật của thầy cô: mỗi cụm
           vẫn còn ô hợp lệ (nên _kiem_tra_so_bo cho qua), nhưng không xếp
           chung được — và không gian 90 cụm thì một giây không vét cạn nổi."""
        mon = [m for m in cfg['dinh_muc_mon'] if not m.startswith('_')][:3]
        cfg['quy_tac'].append(
            {'loai': 'chi_xep_thu', 'ghi_chu': 'ép ba môn vào ba ngày',
             'loc': {'mon': mon}, 'thu': cfg['khung_gio']['cac_thu'][:3]})

    dd_c = cau_hinh_tam(tmc, sua=bi_nhung_to)
    with MayChuTam(dd_c) as (k, _):
        ma, kq = k.js('/api/thu-quy-tac', {'nhanh': True, 'tat': []})
        kiem(ma == 200,
             f'Cấu hình bí kiểu TỔ HỢP đi lọt _kiem_tra_so_bo — {ma}. '
             f'(Nếu mục này đỏ nghĩa là dữ liệu đã đổi tới mức ca thử không còn '
             f'dựng được đúng vùng cần thử, phải chỉnh lại bi_nhung_to.)')
        kiem(kq and kq.get('co_loi_giai') is False,
             f'Bài toán to và bí: không ra lời giải — {kq}')
        kiem(kq and kq.get('vet_can') is False,
             f'NHƯNG vet_can=False: máy chủ THÚ NHẬN nó chỉ HẾT GIỜ, không '
             f'chứng minh được vô nghiệm. Đây là nhánh đúng với lỗi thật của '
             f'thầy cô, và là chỗ dễ nói quá nhất — {kq.get("vet_can") if kq else "?"!r}')

    # --- (d) giao diện có đủ ba mảnh, và nút gỡ nhanh nằm SẴN trong HTML ----
    html = io.open(os.path.join(GOC_TM, 'web', 'index.html'),
                   encoding='utf-8').read()
    thieu = [i for i in ('canh-bao-luu', 'canh-bao-chu', 'nut-go-nhanh')
             if f'id="{i}"' not in html]
    kiem(not thieu, f'Khung cảnh báo có đủ ba mảnh trong HTML — thiếu {thieu}')


def ca_8_nhan_ban(B, dd):
    """Đợt 3 việc 4 — "Tạo giống quy tắc này".

       Nút này CHỈ điền form, không thêm thẳng. Nên phần máy chủ cần canh là
       cửa chặn TRÙNG CÂU, và phần giao diện là: có nút, và veTruong() điền
       được từ nguồn khác VI_DU.
    """
    print('\nCA 8 — nhân bản quy tắc, và cửa chặn trùng câu "Nội dung"')
    print('-' * 74)
    ma, d = B.js('/api/quy-tac')
    if not (isinstance(d, dict) and d.get('quy_tac')):
        kiem(False, f'Không đọc được danh sách quy tắc — mã {ma}, {str(d)[:70]}')
        return
    truoc = len(d['quy_tac'])
    r0 = d['quy_tac'][0]

    # (a) /api/quy-tac phải CHỞ ĐỦ thân quy tắc, không chỉ ghi_chu — nếu không
    #     thì không có gì để nhân bản.
    kiem(isinstance(r0.get('noi_dung'), dict) and r0['noi_dung'],
         f'Danh sách chở đủ thân quy tắc để nhân bản — '
         f'{sorted(r0.get("noi_dung") or {})}')

    # (b) nhân bản Y NGUYÊN phải bị CHẶN
    ban = dict(r0.get('noi_dung') or {},
               loai=r0.get('loai'), ghi_chu=r0.get('ghi_chu'))
    ma, kq = B.js('/api/them-quy-tac', {'quy_tac': ban})
    loi = str((kq or {}).get('loi', ''))
    kiem(ma == 400, f'Nhân bản Y NGUYÊN bị từ chối — mã {ma}')
    kiem('Nội dung' in loi and r0['ghi_chu'] in loi,
         f'Câu từ chối nhắc lại ĐÚNG câu bị trùng — {loi[:70]!r}')
    kiem('im lặng' in loi or 'MẤT một dòng' in loi,
         'và nói rõ hậu quả: bảng Excel mất một dòng, sai trong im lặng')
    kiem('Hãy sửa' in loi or 'sửa câu' in loi,
         'và nói rõ cách chữa')

    ma, d2 = B.js('/api/quy-tac')
    kiem(len(d2['quy_tac']) == truoc,
         f'Lần bị từ chối KHÔNG để lại gì trong phiên — '
         f'{len(d2["quy_tac"])} (trước {truoc})')

    # (c) sửa câu đi thì nhận
    ban2 = dict(ban, ghi_chu=r0['ghi_chu'] + ' — bản sao')
    ma, kq = B.js('/api/them-quy-tac', {'quy_tac': ban2})
    kiem(ma == 200 and len((kq or {}).get('quy_tac', [])) == truoc + 1,
         f'Sửa câu "Nội dung" rồi thì nhận — mã {ma}, '
         f'{len((kq or {}).get("quy_tac", []))} quy tắc')

    # (d) và bản sao GIỐNG HỆT bản gốc ở mọi khoá khác
    if ma == 200:
        moi_ = kq['quy_tac'][-1]
        kiem(moi_.get('loai') == r0.get('loai')
             and moi_.get('noi_dung') == r0.get('noi_dung'),
             'Bản sao giữ NGUYÊN loại và toàn bộ thân quy tắc')
        B.js('/api/xoa-quy-tac', {'i': moi_['i']})

    # (e) khoảng trắng thừa KHÔNG lách được cửa chặn
    ma, kq = B.js('/api/them-quy-tac',
                  {'quy_tac': dict(ban, ghi_chu='  ' + r0['ghi_chu'] + '  ')})
    kiem(ma == 400, f'Thêm khoảng trắng hai đầu không lách được — mã {ma}')

    # (f) cauhinh.json vẫn không suy suyển
    kiem(len(json.load(io.open(dd, encoding='utf-8'))['quy_tac']) == truoc,
         'cauhinh.json trên đĩa không đổi suốt cả ca thử')

    # (g) giao diện: có nút, và veTruong() nhận nguồn giá trị khác VI_DU
    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
    js = re.sub(r'^\s*//.*$', '', js, flags=re.M)      # LỘT CHÚ THÍCH TRƯỚC
    kiem('data-nhan-ban' in js and 'function nhanBan' in js,
         'app.js có nút "Tạo giống" và hàm nhanBan()')
    kiem(re.search(r'function veTruong\(\s*\w+\s*\)', js),
         'veTruong() nhận nguồn giá trị — MỘT hàm vẽ, không phải hai')
    kiem(len(re.findall(r'function veTruong\(', js)) == 1,
         'và chỉ có ĐÚNG MỘT hàm vẽ ô nhập')
    css = io.open(os.path.join(GOC_TM, 'web', 'style.css'),
                  encoding='utf-8').read()
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    m = re.search(r'\.nut-nhan-ban\s*\{([^{}]*)\}', css)
    mh = re.search(r'min-height:\s*([\d.]+)px', m.group(1)) if m else None
    kiem(mh and float(mh.group(1)) >= 40,
         f'Nút "Tạo giống" đủ to để bấm — '
         f'{mh.group(1) + "px" if mh else "KHÔNG KHAI"}')


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
            ca_8_nhan_ban(B, dd)
        finally:
            may.shutdown()
        ca_6_kich_thuoc_css()
        ca_7_kiem_nhanh_sau_luu(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

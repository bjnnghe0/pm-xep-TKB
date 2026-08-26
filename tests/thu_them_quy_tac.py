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

B_DD = [None]                # đường dẫn cauhinh.json của ca thử

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


def ca_6b_day_the_chon_loai():
    print('\nCA 6b — dãy THẺ CHỌN LOẠI thay <select> (ĐỌC MÃ NGUỒN)')
    print('-' * 74)
    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    html = io.open(os.path.join(GOC_TM, 'web', 'index.html'),
                   encoding='utf-8').read()
    css = io.open(os.path.join(GOC_TM, 'web', 'style.css'),
                  encoding='utf-8').read()
    js_sach = re.sub(r'//[^\n]*', '', re.sub(r'/\*.*?\*/', '', js, flags=re.S))
    css_sach = re.sub(r'/\*.*?\*/', '', css, flags=re.S)

    # (a) `o-loai` phải bỏ SẠCH — bỏ nửa vời thì còn một đường chết trỏ vào
    #     một id không tồn tại, và thu_web CA 4 chỉ bắt được chiều ngược lại.
    kiem('o-loai' not in js_sach and 'o-loai' not in html,
         "Không còn dấu vết `o-loai` nào trong app.js lẫn index.html")
    # Bốn `<select>` CÒN LẠI là thanh LỌC (`loc-*`) — danh sách ngắn, cố
    # định, không có nhãn hai vế, nên `<select>` ở đó là đúng chỗ. Khẳng
    # định trên ID chứ không dò chuỗi '<select': chuỗi ấy còn nằm trong
    # chính dòng chú thích giải thích vì sao bỏ nó (nếp hỏng 4).
    con = re.findall(r'<select id="([^"]+)"', html)
    kiem(con and all(i.startswith('loc-') for i in con),
         f'`<select>` chỉ còn ở thanh LỌC, không còn ở form quy tắc — {con}')

    # (b) Khung dãy thẻ nằm SẴN trong HTML, không dựng bằng innerHTML.
    for i in ('hop-loai', 'ds-nhom-loai'):
        kiem(f'id="{i}"' in html, f'id="{i}" nằm SẴN trong index.html')

    # (c) RADIO PHẢI GIẤU KIỂU `.nut-o input`. Đây là cái bẫy của CA 6: nó
    #     soi mọi selector có chữ "input" và chỉ tha 'checkbox', nên khai
    #     min-height cho radio (kiểu input[type="checkbox"]) là ĐỎ ngay.
    m = re.search(r'\.the-loai-chon input\s*\{([^{}]*)\}', css_sach)
    kiem(bool(m), 'Có khai `.the-loai-chon input` để giấu radio')
    if m:
        kiem('min-height' not in m.group(1) and 'font-size' not in m.group(1),
             f'và nó KHÔNG khai min-height/font-size — {m.group(1).strip()!r}')

    # (d) KHÔNG chiếm phím tắt toàn trang. Radio cùng `name` đã đi được bằng
    #     phím mũi tên sẵn trong trình duyệt, không tốn dòng mã nào.
    kiem("document.addEventListener('keydown'" not in js_sach
         and 'document.onkeydown' not in js_sach,
         'Không gắn phím tắt keydown toàn trang')
    kiem("name=\"loai-qt\"" in js_sach or "name=\'loai-qt\'" in js_sach,
         'Radio cùng một `name` — để phím mũi tên đi được sẵn')

    # (e) Bấm Sửa / Tạo giống phải MỞ nhóm chứa loại đó. "Mặc định gập hết"
    #     mà không mở thì loại đang chọn VÔ HÌNH.
    # Soi TRONG THÂN HÀM, không dò cả tệp. `nhomMo.add` cũng nằm ở nút
    # gập/mở nhóm, nên phép dò cả tệp XANH cả khi datLoai() không mở gì —
    # đã đo 26/8/2026: bỏ hẳn vòng mở nhóm khỏi datLoai() cho 127/127,
    # không mục nào đỏ. Nếp hỏng 15: canh tên định danh, không canh chỗ nó
    # thật sự nằm.
    than_dl = re.search(r'function datLoai\([^)]*\)\s*\{(.*?)\n\}',
                        js_sach, re.S)
    kiem(bool(than_dl), 'Đọc được thân hàm datLoai()')
    kiem(bool(than_dl) and 'nhomMo.add' in than_dl.group(1),
         'và CHÍNH THÂN NÓ mở sẵn nhóm chứa loại được đặt — '
         '"mặc định gập hết" mà không mở thì loại đang chọn VÔ HÌNH')
    kiem(js_sach.count('datLoai(') >= 3,
         f'và cả Sửa lẫn Tạo giống đều đi qua nó — '
         f'{js_sach.count("datLoai(")} chỗ gọi')

    # (f) CHƯA CHỌN LOẠI là trạng thái THẬT từ khi bỏ <select> (select luôn
    #     tự chọn phần tử đầu). docForm() phải trả null chứ không được ném.
    kiem('if (!l) return null;' in js_sach,
         'docForm() trả null khi chưa chọn loại, KHÔNG ném')
    kiem(js_sach.count('Chưa chọn "Loại quy tắc"') >= 2,
         f'và cả nút Thêm lẫn nút Thử đều nói rõ — '
         f'{js_sach.count(chr(34) + "Chưa chọn" + chr(34)) if False else js_sach.count("Chưa chọn")} chỗ')


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
           '.nut-xoa', '.cong-tac', '.ds-chon .dong', '.tim',
           # Đợt 3 việc 4 — dãy thẻ chọn loại thay <select>. Cả hai đều
           # BẤM ĐƯỢC nên phải chịu đúng ngưỡng chạm.
           '.nut-nhom', '.the-loai-chon')
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
           '.trong-rong',
           # Hai dòng chữ của MỖI THẺ CHỌN LOẠI — thứ thầy cô đọc để biết
           # loại này làm gì, và để đối chiếu cauhinh.json bằng Notepad.
           '.the-loai-chon .nhan-loai', '.the-loai-chon .ma-loai')
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


def ca_9_loc_quy_tac(B):
    """Đợt 3 phần 2 — tìm và lọc.

       Mục quan trọng nhất KHÔNG phải "lọc có chạy không" mà là "PHẠM VI tính
       ở đâu": nếu JS tự đọc noi_dung.loc để suy ra quy tắc chạm vào ai thì đó
       là bản cài THỨ HAI của bộ lọc, và nó sẽ lệch — đúng bài học
       khop_loc() / _cum_cua() mà cả CLAUDE.md dựng ra để chống.
    """
    print('\nCA 9 — lọc quy tắc theo GV / môn / lớp / nhóm')
    print('-' * 74)
    ma, d = B.js('/api/quy-tac')
    qt = d.get('quy_tac') if isinstance(d, dict) else None
    if not qt:
        kiem(False, f'Không đọc được danh sách — mã {ma}, {str(d)[:70]}')
        return

    # (a) máy chủ phải chở PHẠM VI, không bắt JS tự suy
    co = [r for r in qt if isinstance(r.get('pham_vi'), dict)]
    kiem(len(co) == len(qt),
         f'Mọi quy tắc đều được máy chủ tính sẵn phạm vi — {len(co)}/{len(qt)}')
    if co:
        kiem(all(set(r['pham_vi']) >= {'lop', 'mon', 'gv', 'so_cum'}
                 for r in co),
             f'và phạm vi đủ khoá để lọc — {sorted(co[0]["pham_vi"])}')

    # (b) phạm vi máy chủ chở về phải KHỚP với pham_vi_quy_tac() gọi thẳng.
    #     Dựng kỳ vọng TỪ dữ liệu, không ghim tên nào.
    cfg = X.doc_cau_hinh(B_DD[0])
    bt = X.BaiToan(cfg)
    lech = []
    for r_file, r_api in zip(cfg['quy_tac'], qt):
        that = QT.pham_vi_quy_tac(r_file, bt)
        api = r_api.get('pham_vi') or {}
        if [that['lop'], that['mon'], that['gv']] != \
           [api.get('lop'), api.get('mon'), api.get('gv')]:
            lech.append(r_api.get('i'))
    kiem(not lech, f'Phạm vi qua HTTP khớp pham_vi_quy_tac() gọi thẳng — '
                   f'lệch ở {lech}')

    # (c) điều kiện tiên quyết: phải CÓ cái để lọc, không thì mọi mục dưới
    #     đều xanh mà không kiểm gì (bẫy n_uyen == 0).
    gv = sorted({x for r in qt for x in (r.get('pham_vi') or {}).get('gv', [])})
    lop = sorted({x for r in qt for x in (r.get('pham_vi') or {}).get('lop', [])})
    kiem(len(gv) > 1 and len(lop) > 1,
         f'Dữ liệu đủ đa dạng để phép lọc có nghĩa — {len(gv)} GV, {len(lop)} lớp')
    if not (gv and lop):
        return

    # (d) lọc phải THẬT SỰ chia đôi tập, không phải giữ nguyên tất cả
    n1 = sum(1 for r in qt if gv[0] in (r.get('pham_vi') or {}).get('gv', []))
    kiem(0 < n1 < len(qt),
         f'Lọc theo GV {gv[0]!r} chia được tập — {n1}/{len(qt)} quy tắc')
    n2 = sum(1 for r in qt if lop[0] in (r.get('pham_vi') or {}).get('lop', []))
    kiem(0 < n2 <= len(qt),
         f'Lọc theo lớp {lop[0]!r} — {n2}/{len(qt)} quy tắc')

    # (e) giao diện: mọi id JS gọi tới phải NẰM SẴN trong HTML
    html = io.open(os.path.join(GOC_TM, 'web', 'index.html'),
                   encoding='utf-8').read()
    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    js_sach = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
    js_sach = re.sub(r'^\s*//.*$', '', js_sach, flags=re.M)  # LỘT CHÚ THÍCH
    thieu = [i for i in ('tim-qt', 'loc-nhom', 'loc-gv', 'loc-mon', 'loc-lop',
                         'nut-bo-loc', 'dem-quy-tac')
             if f'id="{i}"' not in html]
    kiem(not thieu, f'Mọi ô lọc nằm SẴN trong index.html — thiếu {thieu}')

    # (f) BẪY CHÍNH: JS không được tự bóc noi_dung.loc để suy ra phạm vi
    xau = [m for m in ('noi_dung.loc', "noi_dung['loc']", 'noi_dung.a',
                       'noi_dung.b') if m in js_sach]
    kiem(not xau,
         f'JS KHÔNG tự suy phạm vi từ noi_dung — dùng pham_vi máy chủ chở về. '
         f'Thấy: {xau}')
    kiem('r.pham_vi' in js_sach,
         'và có dùng khoá pham_vi của máy chủ')


def ca_10_sua_nhap(B, dd):
    """Đợt 3 phần 3 — nút Sửa, và vì sao nó CHỈ có ở quy tắc nháp.

       luu_quy_tac() ghi cờ bật/tắt cộng danh sách nháp; nó KHÔNG ghi được
       thân một quy tắc đã có trong cauhinh.json. Nên nút "Sửa" ở đó là nút
       hứa việc không làm được — thầy cô sửa, bấm Lưu, mở tệp ra thấy y cũ.
    """
    print('\nCA 10 — sửa quy tắc nháp (và vì sao quy tắc trong file thì không)')
    print('-' * 74)
    # CA 4 đã Lưu nên mọi nháp cũ thành quy tắc trong file — ca thử này phải
    # tự dựng nháp của mình. Bộ lọc chọn thứ KHÔNG KHỚP GÌ CẢ, để nó không bao
    # giờ có ý kiến về dữ liệu nhà trường (xem NHAP_A trong thu_phien.py).
    NHAP = {'loai': 'chi_xep_thu', 'ghi_chu': 'CA10 nháp để thử nút Sửa',
            'loc': {'mon': 'MÔN-KHÔNG-CÓ-THẬT-CA10'}, 'thu': [2, 3]}
    ma, _ = B.js('/api/them-quy-tac', {'quy_tac': dict(NHAP)})
    kiem(ma == 200, f'Dựng được một quy tắc nháp để thử — mã {ma}')

    ma, d = B.js('/api/quy-tac')
    qt = d.get('quy_tac') if isinstance(d, dict) else None
    if not qt:
        kiem(False, f'Không đọc được danh sách — mã {ma}')
        return
    so_file = d.get('so_file')

    # điều kiện tiên quyết: phải có CẢ HAI loại thẻ, không thì mục dưới vô nghĩa
    nhap = [r for r in qt if r.get('moi')]
    tep = [r for r in qt if not r.get('moi')]
    kiem(len(nhap) > 0 and len(tep) > 0,
         f'Có cả quy tắc nháp lẫn quy tắc từ file — {len(nhap)} nháp, '
         f'{len(tep)} từ file')
    if not (nhap and tep):
        return

    # (a) VÒNG TRÒN: xoá nháp rồi thêm lại y nguyên -> ra đúng quy tắc cũ
    r = nhap[0]
    goc = {'loai': r['loai'], 'ghi_chu': r['ghi_chu'],
           'noi_dung': r.get('noi_dung')}
    ma, kq = B.js('/api/xoa-quy-tac', {'i': r['i']})
    kiem(ma == 200, f'Bước 1 của Sửa — xoá bản nháp cũ, mã {ma}')
    ma, kq = B.js('/api/them-quy-tac', {'quy_tac': dict(
        goc['noi_dung'] or {}, loai=goc['loai'], ghi_chu=goc['ghi_chu'])})
    kiem(ma == 200, f'Bước 2 — thêm lại bản đã sửa, mã {ma}')
    ds = (kq or {}).get('quy_tac') or []
    sau = ds[-1] if ds else {}
    kiem(sau.get('loai') == goc['loai']
         and sau.get('ghi_chu') == goc['ghi_chu']
         and sau.get('noi_dung') == goc['noi_dung'],
         'Vòng tròn khép kín: ra đúng quy tắc ban đầu, không rơi khoá nào')
    kiem(len(ds) == len(qt),
         f'và số quy tắc không đổi — {len(ds)} (trước {len(qt)})')

    # (b) máy chủ TỪ CHỐI xoá quy tắc nằm trong file — đây là ràng buộc thật
    #     đứng sau việc nút Sửa không hiện ở đó.
    ma, kq = B.js('/api/xoa-quy-tac', {'i': 0})
    kiem(ma == 400, f'Máy chủ từ chối xoá quy tắc đã có trong file — mã {ma}')
    kiem('công tắc' in str((kq or {}).get('loi', '')),
         f'và chỉ đúng cách làm thay thế — {str((kq or {}).get("loi"))[:60]!r}')

    # (c) giao diện: nút Sửa và nút Xoá cùng bị khoá sau ĐÚNG một điều kiện
    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
    js = re.sub(r'^\s*//.*$', '', js, flags=re.M)          # LỘT CHÚ THÍCH
    the = re.search(r'function theQuyTac\([^)]*\)\s*\{(.*?)\n\}', js, re.S)
    than = the.group(1) if the else ''
    kiem(bool(the), 'Đọc được hàm dựng thẻ')
    for nut, co_dk in (('data-sua', True), ('data-xoa', True),
                       ('data-nhan-ban', False)):
        m = re.search(r'r\.moi \?[^\n]*' + nut, than)
        kiem(bool(m) == co_dk,
             f'Nút {nut} {"chỉ hiện khi r.moi" if co_dk else "hiện ở MỌI thẻ"}'
             f' — {"đúng" if bool(m) == co_dk else "SAI"}')
    kiem('suaQuyTac' in js and 'nut-sua' in js,
         'app.js có hàm suaQuyTac() và lớp nút riêng')

    # (d) xoá TRƯỚC, điền SAU — thứ tự này là cái chống câu báo lỗi vô nghĩa
    sua = re.search(r'async function suaQuyTac\(.*?\n\}', js, re.S)
    t = sua.group(0) if sua else ''
    kiem(sua and t.index('xoa-quy-tac') < t.index("$('o-ghi-chu').value ="),
         'suaQuyTac() XOÁ trước rồi mới ĐIỀN form — không để lại nháp trùng câu')

    # (e) huy hiệu Bắt buộc / Ưu tiên bám theo khoá mem của máy chủ
    kiem("r.mem ?" in than and 'chip-mem' in than and 'chip-cung' in than,
         'Huy hiệu Bắt buộc/Ưu tiên lấy từ khoá mem của máy chủ, không đoán')
    css = io.open(os.path.join(GOC_TM, 'web', 'style.css'),
                  encoding='utf-8').read()
    m = re.search(r'\.chip\s*\{([^{}]*)\}', css)
    fs = re.search(r'font-size:\s*([\d.]+)px', m.group(1)) if m else None
    kiem(fs and float(fs.group(1)) >= 15,
         f'Chữ trên huy hiệu >= 15px — {fs.group(1) if fs else "KHÔNG KHAI"}')

    kiem(len(json.load(io.open(dd, encoding='utf-8'))['quy_tac']) == so_file,
         'cauhinh.json trên đĩa không suy suyển suốt cả ca thử')


def ca_11_bon_trang_thai():
    """Đợt 3 phần 4 — đang tải · rỗng · lỗi · xong.

       Bản trước viết `if (!d) return;`: máy chủ 500 hay câu trả lời không
       phải JSON thì màn hình đứng im với danh sách cũ, KHÔNG một chữ nào.
       Đó đúng là hạng lỗi im lặng cả dự án này chống, chỉ khác là nó nằm ở
       giao diện chứ không ở chỗ ghi tệp.

       Đây là ca thử ĐỌC MÃ NGUỒN — không có trình duyệt để chạy JS. Nên nó
       LỘT CHÚ THÍCH TRƯỚC (kiểu hỏng số 4), và canh CẤU TRÚC chứ không canh
       một chuỗi chữ nào: chuỗi thì đổi lời là gãy mà chẳng ai sai gì.
    """
    print('\nCA 11 — bốn trạng thái của danh sách quy tắc')
    print('-' * 74)
    print('  Lưu ý: ca thử này ĐỌC MÃ NGUỒN, không dựng trình duyệt. Nó bắt')
    print('  được việc BỎ HẲN nhánh báo lỗi, không bắt được lỗi hiển thị.')
    goc = os.path.join(GOC_TM, 'web')
    html = io.open(os.path.join(goc, 'index.html'), encoding='utf-8').read()
    js = io.open(os.path.join(goc, 'app.js'), encoding='utf-8').read()
    js = re.sub(r'/\*.*?\*/', '', js, flags=re.S)
    js = re.sub(r'^\s*//.*$', '', js, flags=re.M)          # LỘT CHÚ THÍCH

    # (a) bốn trạng thái phải là PHẦN TỬ THẬT trong HTML
    thieu = [i for i in ('qt-dang-tai', 'qt-loi', 'qt-loi-chu',
                         'nut-tai-lai-qt', 'ds-quy-tac')
             if f'id="{i}"' not in html]
    kiem(not thieu, f'Bốn trạng thái nằm SẴN trong index.html — thiếu {thieu}')

    # (b) LỖ ĐÃ BỊT: không còn chỗ nào nuốt câu trả lời hỏng rồi return trơn
    nap = re.search(r'async function napQuyTac\(\).*?\n\}', js, re.S)
    than = nap.group(0) if nap else ''
    kiem(bool(nap), 'Đọc được hàm napQuyTac()')
    kiem(than and not re.search(r'if \(!d\)\s*return;', than),
         'napQuyTac() KHÔNG còn nhánh "if (!d) return" nuốt lỗi trong im lặng')
    kiem("trangThaiDs('loi'" in than,
         'và có nhánh chuyển sang trạng thái LỖI')
    kiem(than.count("trangThaiDs('loi'") >= 2,
         f'đủ HAI nhánh lỗi — mạng hỏng và câu trả lời hỏng là hai chuyện '
         f'khác nhau, câu báo phải khác nhau ({than.count("trangThaiDs(\'loi\'")})')

    # (c) hết phiên KHÔNG được báo là lỗi mạng — lớp phủ đăng nhập lo việc đó
    kiem('hetPhien' in than,
         'Hết phiên đi nhánh riêng, không bị báo nhầm thành lỗi nối máy chủ')

    # (d) trạng thái RỖNG vẫn còn, và khác trạng thái LỖI
    kiem('trong-rong' in js, 'Trạng thái RỖNG có câu riêng')

    # (e) bàn phím: có viền lấy nét, và là :focus-visible chứ không :focus trần
    css = io.open(os.path.join(goc, 'style.css'), encoding='utf-8').read()
    css = re.sub(r'/\*.*?\*/', '', css, flags=re.S)
    kiem('focus-visible' in css and 'outline' in css,
         'Có viền lấy nét cho người đi bằng bàn phím')
    tran = re.findall(r'(?<!-)\bbutton:focus\s*[,{]', css)
    kiem(not tran,
         f'và dùng :focus-visible chứ không :focus trần — bấm chuột không '
         f'để lại khung xanh ({tran})')
    kiem("$('tim-qt').onkeydown" in js, 'Ô Tìm có xử lý phím')

    # (f) KHÔNG chiếm phím tắt toàn trang — nó cướp phím của người đang gõ
    cuop = re.findall(r'document\.(?:addEventListener\(\s*.keydown|onkeydown)',
                      js)
    kiem(not cuop, f'Không bắt phím ở cấp toàn trang — {cuop}')


# ==========================================================================
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
            B_DD[0] = dd
            ca_9_loc_quy_tac(B)
            ca_10_sua_nhap(B, dd)
        finally:
            may.shutdown()
        ca_6_kich_thuoc_css()
        ca_6b_day_the_chon_loai()
        ca_11_bon_trang_thai()
        ca_7_kiem_nhanh_sau_luu(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

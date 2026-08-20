#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ CỔNG ĐĂNG NHẬP  (Đợt 2A-1)
--------------------------------------------------------------------------
 Chạy:  python tests/thu_dang_nhap.py

 Tách khỏi thu_an_ninh.py vì HAI TỆP CÓ TIỀN ĐỀ NGƯỢC NHAU: mọi ca trong
 thu_an_ninh giả định khách ĐÃ có quyền (MayChuTam tự đăng nhập sẵn), mọi ca ở
 đây giả định khách CHƯA có quyền. Trộn hai tiền đề vào một tệp chính là nguồn
 sinh ra ca thử xanh giả.

 CHỖ NGUY HIỂM NHẤT — CỐ ĐỊNH PHIÊN. Sau 2A-2a, mã phiên vô danh được cấp tự
 động cho mọi khách. Nếu 2A-1 "nâng cấp tại chỗ" phiên đó thành phiên đã đăng
 nhập thì kẻ tấn công chỉ cần gieo sẵn một mã vào trình duyệt người khác rồi
 chờ họ đăng nhập — xong là dùng chung phiên. Ở đây kẻ tấn công là người trong
 tailnet, tức đúng mô hình đe doạ đang chống. Vì vậy phải SINH MÃ MỚI và HUỶ
 HẲN mã cũ; ba mục ở CA 3 canh đúng điều đó.

 Theo bất biến kỷ luật ca thử: quan sát HÀNH VI qua HTTP thật, không khẳng định
 trên văn bản mã nguồn, phải biết ĐỎ chứ không biết VỠ, và có ĐỒNG HỒ CANH.
==========================================================================
"""
import io
import json
import os
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import (GOC_TM, MayChuTam, Khach,        # noqa: E402
                          cau_hinh_tam)
import tai_khoan as TK       # noqa: E402
import web as W              # noqa: E402

KQ = []
MK = MayChuTam.MAT_KHAU
TEN = MayChuTam.TEN


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def dat_dong_ho_canh(giay=240):
    """Bộ thử không bao giờ được phép TREO — hết giờ thì ĐỎ. Xem CLAUDE.md."""
    def bao():
        time.sleep(giay)
        hong = [m for ok, m in KQ if not ok]
        print(f'\n  [LỖI] BỘ THỬ TREO quá {giay} giây.')
        print('=' * 74)
        print(f'Tổng: {len(KQ) - len(hong) - 1}/{len(KQ) + 1} mục ĐẠT.')
        print('  LỖI: bộ thử treo, không chạy hết được')
        sys.stdout.flush()
        os._exit(1)
    threading.Thread(target=bao, daemon=True).start()


def dung(tm, ten_thu, **kw):
    tmx = os.path.join(tm, ten_thu)
    os.makedirs(tmx, exist_ok=True)
    return cau_hinh_tam(tmx), tmx


# ==========================================================================
def ca_1_dang_nhap_dung(tm):
    print('\nCA 1 — đăng nhập đúng: 200 và cookie đủ cờ')
    print('-' * 74)
    dd, tmx = dung(tm, 'd1')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        ma, td, t = k.post_td('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
        kiem(ma == 200, f'Mật khẩu đúng -> 200 — {ma}')
        c = (td.get('set-cookie') or [''])[0]
        kiem('HttpOnly' in c, f'Cookie có HttpOnly — {c[:70]}')
        kiem('SameSite=Lax' in c, 'Cookie có SameSite=Lax (khai TƯỜNG MINH)')
        kiem('Path=/' in c, 'Cookie có Path=/')
        kiem('Max-Age' not in c and 'Expires' not in c,
             'Cookie KIỂU PHIÊN — đóng trình duyệt là đăng xuất (QĐ 2)')
        # Secure chỉ có ở đường TLS; đường loopback mà có Secure thì trình duyệt
        # vứt cookie đi và không ai đăng nhập được.
        kiem('Secure' not in c,
             'Đường http tại chỗ: KHÔNG có Secure (nếu có, trình duyệt vứt đi)')
        kiem(k.ma_phien(), f'Và khách giữ được mã phiên — {k.ma_phien()[:12]}…')

        ma, d = k.js('/api/quy-tac')
        kiem(ma == 200 and d and 'quy_tac' in d,
             f'Đăng nhập xong thì vào được đường cần quyền — {ma}')
        ma, d = k.js('/api/toi-la-ai')
        kiem(ma == 200 and d.get('dang_nhap') is True and d.get('ten') == TEN,
             f'/api/toi-la-ai báo đúng tên — {d}')


# ==========================================================================
def ca_2_dang_nhap_sai(tm):
    print('\nCA 2 — đăng nhập sai: MỘT câu duy nhất, không lộ tài khoản nào có thật')
    print('-' * 74)
    dd, tmx = dung(tm, 'd2')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        cac = [('tên có thật, mật khẩu sai', {'ten': TEN, 'mat_khau': 'sai' * 6}),
               ('tên KHÔNG tồn tại', {'ten': 'khongcoai', 'mat_khau': 'sai' * 6}),
               ('tên sai cú pháp', {'ten': 'A B!@#', 'mat_khau': 'sai' * 6}),
               ('tên rỗng', {'ten': '', 'mat_khau': 'sai' * 6}),
               ('thiếu hẳn khoá mật khẩu', {'ten': TEN})]
        thay = []
        for nhan, than in cac:
            ma, t = k.post('/api/dang-nhap', than)
            thay.append((nhan, ma, t))
        kiem(all(m == 401 for _, m, _ in thay),
             f'Mọi nhánh sai đều 401 — {[(n, m) for n, m, _ in thay]}')
        than_khac = {t for _, _, t in thay}
        kiem(len(than_khac) == 1,
             f'Và thân giống nhau TỪNG BYTE ở mọi nhánh — {len(than_khac)} câu '
             f'khác nhau: {sorted(than_khac)}')
        kiem(TEN not in list(than_khac)[0],
             'Câu trả lời KHÔNG nhắc lại tên vừa gõ')
        # Khách VẪN có cookie — đó là phiên VÔ DANH của 2A-2a, đúng như thiết
        # kế. Thứ phải khẳng định là phiên đó CHƯA XÁC THỰC, và cách đúng để
        # khẳng định là hỏi hành vi chứ không nhìn cái jar.
        _, d = k.js('/api/toi-la-ai')
        kiem(d == {'dang_nhap': False, 'ten': None},
             f'Sai mật khẩu -> phiên vẫn là VÔ DANH, chưa xác thực — {d}')
        ma, _ = k.js('/api/quy-tac')
        kiem(ma == 401, f'Và vẫn không vào được đường cần quyền — {ma}')

        # tài khoản bị TẮT cũng phải rơi vào đúng câu chung đó
        dd_tk = os.path.join(tmx, 'tai_khoan.json')
        ds = TK.doc_tho(dd_tk)
        ds.append(dict(TK.ban_ghi_moi('nguoitat', MK), bat=False))
        TK.ghi(dd_tk, ds)
        W.nap_tai_khoan_may_chu(dd_tk)
        ma, t = k.post('/api/dang-nhap', {'ten': 'nguoitat', 'mat_khau': MK})
        kiem(ma == 401 and t == list(than_khac)[0],
             'Tài khoản đã TẮT: đúng câu chung đó, không lộ là nó có tồn tại')


# ==========================================================================
def ca_3_xoay_ma_phien(tm):
    print('\nCA 3 — CHỐNG CỐ ĐỊNH PHIÊN: mã phải ĐỔI, mã cũ phải chết')
    print('-' * 74)
    dd, tmx = dung(tm, 'd3')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        # 1) lấy một mã VÔ DANH (2A-2a cấp tự động cho mọi khách)
        k.get('/')
        ma_truoc = k.ma_phien()
        kiem(bool(ma_truoc), f'Trước khi đăng nhập đã có mã vô danh — '
                             f'{ma_truoc[:12]}…')

        # 2) đăng nhập
        ma, _ = k.post('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
        ma_sau = k.ma_phien()
        kiem(ma == 200, f'Đăng nhập thành công — {ma}')

        # ---- MỤC 1 bác yêu cầu: mã TRƯỚC/SAU phải KHÁC ----
        kiem(ma_truoc != ma_sau,
             f'Mã phiên ĐỔI sau khi đăng nhập — {ma_truoc[:12]}… -> '
             f'{ma_sau[:12]}…')

        # ---- MỤC 2 bác yêu cầu: dùng lại mã CŨ phải bị từ chối ----
        # Gửi TAY mã cũ, kèm cookie=False — nếu để jar tự ghép thì yeu_cau()
        # gửi HAI dòng Cookie, mà máy chủ chỉ đọc dòng đầu: ca thử sẽ xanh giả.
        kh_cu = Khach(cong)
        ma_hd, _ = kh_cu.yeu_cau('GET', '/api/quy-tac', cookie=False,
                                 them={'Cookie': f'{W.TEN_COOKIE}={ma_truoc}'})[0:2]
        kiem(ma_hd == 401,
             f'Mã CŨ dùng lại sau khi đăng nhập -> bị từ chối — {ma_hd}')

        # ---- và mã cũ không còn trong sổ phiên ----
        kiem(ma_truoc not in W.CAC_PHIEN,
             'Mã cũ bị HUỶ HẲN khỏi sổ, không chỉ là bị bỏ qua')

        # ---- Mã do KHÁCH BỊA cũng không bao giờ được nâng cấp ----
        BIA = 'Z' * 43
        kh2 = Khach(cong)
        ma2, td, _ = kh2.yeu_cau('POST', '/api/dang-nhap',
                                 json.dumps({'ten': TEN, 'mat_khau': MK}).encode(),
                                 cookie=False,
                                 them={'Cookie': f'{W.TEN_COOKIE}={BIA}'})
        cap = (td.get('set-cookie') or [''])[0]
        kiem(ma2 == 200 and BIA not in cap,
             f'Gieo sẵn một mã BỊA rồi đăng nhập -> máy chủ cấp mã KHÁC HẲN, '
             f'không nhận nuôi mã gieo — {cap[:60]}')
        kiem(BIA not in W.CAC_PHIEN,
             'Và mã gieo không bao giờ có mặt trong sổ phiên')

        # ---- MỤC 3 bác yêu cầu: nháp gắn mã cũ xử lý thế nào ----
        # Quyết: CHUYỂN sang mã mới. Thứ kẻ tấn công cần là mã SAU khi đăng
        # nhập, mà mã đã xoay thì hắn không có — nháp chuyển hay không không
        # đụng tới tính chất đó. Bỏ nháp thì làm mất việc của người dùng.
        k.post('/api/them-quy-tac', {'quy_tac': {
            'loai': 'khong_xep_thu', 'ghi_chu': 'NHAP-TRUOC-KHI-VAO-LAI',
            'loc': {'lop': '12B1'}, 'thu': [2]}})
        _, d = k.js('/api/quy-tac')
        kiem(d['so_moi'] == 1, 'Dựng sẵn: đang có 1 nháp')
        ma_g1 = k.ma_phien()
        k.post('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})   # đăng nhập LẠI
        ma_g2 = k.ma_phien()
        kiem(ma_g1 != ma_g2, 'Đăng nhập lại: mã vẫn ĐỔI (xoay mọi lần)')
        _, d = k.js('/api/quy-tac')
        kiem(d['so_moi'] == 1,
             f'Và nháp được CHUYỂN sang mã mới, không mất — {d["so_moi"]}')


# ==========================================================================
def ca_4_khong_cookie(tm):
    print('\nCA 4 — không cookie: mọi đường cần quyền đều 401, KHÔNG trả dữ liệu')
    print('-' * 74)
    dd, tmx = dung(tm, 'd4')
    import re as _re
    ma_nguon = io.open(os.path.join(GOC_TM, 'web.py'), encoding='utf-8').read()
    duong_api = sorted(set(_re.findall(r"duong == '(/api/[a-z-]+)'", ma_nguon)))
    MO = sorted(W.DUONG_MO)
    # Guard: phép bóc hỏng thì vòng dưới chạy rỗng và XANH GIẢ.
    kiem(len(duong_api) >= 14,
         f'Bóc được danh sách đường từ web.py — {len(duong_api)} đường')
    kiem(len(MO) == 8,
         f'Danh sách MỞ đúng 8 đường (5 tĩnh + 3 xác thực) — {MO}')

    THAN = {'/api/xep': {'tat': []}, '/api/luu-quy-tac': {'tat': []},
            '/api/them-quy-tac': {'quy_tac': {'loai': 'khong_xep_thu',
                                              'ghi_chu': 'x', 'thu': [2]}},
            '/api/xoa-quy-tac': {'i': 0}, '/api/thu-quy-tac': {'tat': []},
            '/api/dang-nhap': {'ten': 'x', 'mat_khau': 'y'},
            '/api/dang-xuat': {}}

    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        lot = []
        for d in duong_api:
            if d in W.DUONG_MO:
                continue
            kh = Khach(cong)
            ma, t = (kh.post(d, THAN[d]) if d in THAN else kh.get(d))
            if ma != 401:
                lot.append(f'{d}:{ma}')
            elif '"quy_tac"' in t or '"lop"' in t or '"luoi"' in t:
                lot.append(f'{d}: LỘ DỮ LIỆU')
        kiem(not lot,
             f'Mọi đường cần quyền đều 401 và không lộ dữ liệu — lọt: {lot}')

        # đường không tồn tại: 401 TRƯỚC 404, để không tiết lộ đường nào có thật
        ma, _ = Khach(cong).get('/api/khong-co-duong-nay')
        kiem(ma == 401, f'Đường không tồn tại cũng 401, không phải 404 — {ma}')

        # đường MỞ vẫn phải phục vụ, nếu không thì không có chỗ hiện ô mật khẩu
        chan = []
        for d in MO:
            if d in ('/api/dang-nhap', '/api/dang-xuat'):
                continue
            ma, _ = Khach(cong).get(d)
            if ma != 200:
                chan.append(f'{d}:{ma}')
        kiem(not chan, f'Đường tĩnh + /api/toi-la-ai vẫn mở — chặn nhầm: {chan}')
        ma, d = Khach(cong).js('/api/toi-la-ai')
        kiem(d == {'dang_nhap': False, 'ten': None},
             f'/api/toi-la-ai chưa đăng nhập: đúng hai khoá, không kèm dữ liệu '
             f'— {d}')


# ==========================================================================
def ca_5_cookie_gia_va_het_han(tm):
    print('\nCA 5 — cookie giả / hết hạn: cũng 401')
    print('-' * 74)
    dd, tmx = dung(tm, 'd5')
    nghi = W.GIAY_NGHI_PHIEN
    try:
        with MayChuTam(dd) as (k, (dia, cong)):
            for nhan, c in (('mã bịa', 'Q' * 43), ('mã rỗng', ''),
                            ('mã có ký tự lạ', 'ab"cd')):
                ma, _ = Khach(cong).yeu_cau('GET', '/api/quy-tac', cookie=False,
                                            them={'Cookie':
                                                  f'{W.TEN_COOKIE}={c}'})[0:2]
                kiem(ma == 401, f'Cookie {nhan} -> 401 — {ma}')

            kiem(k.js('/api/quy-tac')[0] == 200, 'Khách hợp lệ vẫn 200')
            W.GIAY_NGHI_PHIEN = 0.4
            time.sleep(0.8)
            ma, _ = k.js('/api/quy-tac')
            kiem(ma == 401, f'Phiên hết hạn -> 401 — {ma}')
    finally:
        W.GIAY_NGHI_PHIEN = nghi


# ==========================================================================
def ca_6_dang_xuat(tm):
    print('\nCA 6 — đăng xuất: mã cũ dùng lại KHÔNG được')
    print('-' * 74)
    dd, tmx = dung(tm, 'd6')
    with MayChuTam(dd) as (k, (dia, cong)):
        ma_cu = k.ma_phien()
        kiem(k.js('/api/quy-tac')[0] == 200, 'Trước khi đăng xuất: vào được')

        ma, _ = k.post('/api/dang-xuat', {})
        kiem(ma == 200, f'Đăng xuất -> 200 — {ma}')

        # CẠM BẪY ĐÃ BIẾT: jar của Khach tự nuốt Set-Cookie rỗng, nên yêu cầu
        # sau sẽ gửi mã RỖNG và nhận 401 — ca thử sẽ XANH cả khi xoa_phien()
        # không làm gì. Phải gửi TAY đúng mã cũ, và cookie=False để yeu_cau()
        # không ghép thêm một dòng Cookie thứ hai (máy chủ chỉ đọc dòng đầu).
        kh = Khach(cong)
        ma, _ = kh.yeu_cau('GET', '/api/quy-tac', cookie=False,
                           them={'Cookie': f'{W.TEN_COOKIE}={ma_cu}'})[0:2]
        kiem(ma == 401, f'Gửi TAY mã cũ sau khi đăng xuất -> 401 — {ma}')
        kiem(ma_cu not in W.CAC_PHIEN,
             'Bản ghi phía máy chủ bị xoá TRƯỚC, không chỉ xoá cookie')

        # luỹ đẳng: bấm đăng xuất lần nữa vẫn 200, không 401
        ma, _ = k.post('/api/dang-xuat', {})
        kiem(ma == 200, f'Đăng xuất lần hai vẫn 200 (luỹ đẳng) — {ma}')


# ==========================================================================
def ca_7_hai_tai_khoan(tm):
    print('\nCA 7 — hai tài khoản: tắt một KHÔNG ảnh hưởng cái kia')
    print('-' * 74)
    dd, tmx = dung(tm, 'd7')
    dd_tk = os.path.join(tmx, 'tai_khoan.json')
    TK.ghi(dd_tk, [TK.ban_ghi_moi('nguoimot', MK),
                   TK.ban_ghi_moi('nguoihai', MK + '-khac')])
    with MayChuTam(dd, tai_khoan=dd_tk, dang_nhap=False) as (k, (dia, cong)):
        k1, k2 = Khach(cong), Khach(cong)
        kiem(k1.post('/api/dang-nhap',
                     {'ten': 'nguoimot', 'mat_khau': MK})[0] == 200,
             'Người một đăng nhập được')
        kiem(k2.post('/api/dang-nhap',
                     {'ten': 'nguoihai', 'mat_khau': MK + '-khac'})[0] == 200,
             'Người hai đăng nhập được, bằng mật khẩu KHÁC')
        kiem(k1.ma_phien() != k2.ma_phien(), 'Hai phiên riêng biệt')
        kiem(k1.post('/api/dang-nhap',
                     {'ten': 'nguoimot', 'mat_khau': MK + '-khac'})[0] == 401,
             'Mật khẩu của người kia KHÔNG mở được tài khoản này')

        # tắt người hai
        ds = TK.doc_tho(dd_tk)
        for bg in ds:
            if bg['ten_dang_nhap'] == 'nguoihai':
                bg['bat'] = False
        TK.ghi(dd_tk, ds)
        W.nap_tai_khoan_may_chu(dd_tk)

        kiem(Khach(cong).post('/api/dang-nhap',
                              {'ten': 'nguoihai',
                               'mat_khau': MK + '-khac'})[0] == 401,
             'Người hai bị TẮT thì không đăng nhập được nữa')
        kiem(k1.js('/api/quy-tac')[0] == 200,
             'Người một KHÔNG bị ảnh hưởng, vẫn dùng bình thường')
        # QĐ 3: tắt có hiệu lực NGAY, phiên đang mở của người đó chết theo
        kiem(k2.js('/api/quy-tac')[0] == 401,
             'Và phiên ĐANG MỞ của người hai chết theo ngay, '
             'không phải đợi khởi động lại (QĐ 3)')


# ==========================================================================
def ca_8_thoi_gian_bang_nhau(tm):
    print('\nCA 8 — tên có thật / không có thật: cùng một lần scrypt')
    print('-' * 74)
    dd, tmx = dung(tm, 'd8')

    # Đo SỐ LỜI GỌI scrypt, không đo đồng hồ. Đếm là bằng chứng XÁC ĐỊNH; đo
    # thời gian thì phụ thuộc tải máy và sẽ chớp đỏ ngẫu nhiên trên máy trường.
    that = TK.bam
    dem = {'n': 0}
    khoa = threading.Lock()

    def bam_dem(*a, **kw):
        with khoa:
            dem['n'] += 1
        return that(*a, **kw)

    TK.bam = bam_dem
    try:
        with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
            for nhan, ten in (('tên CÓ thật', TEN),
                              ('tên KHÔNG có', 'khongcoainay'),
                              ('tên sai cú pháp', '!!!'),
                              ('tên rỗng', '')):
                dem['n'] = 0
                t0 = time.perf_counter()
                k.post('/api/dang-nhap', {'ten': ten, 'mat_khau': 'saibetnhe'})
                giay = time.perf_counter() - t0
                kiem(dem['n'] == 1,
                     f'{nhan}: chạy ĐÚNG 1 lần scrypt — {dem["n"]} lần '
                     f'({giay * 1000:.0f} ms)')
    finally:
        TK.bam = that

    # Guard chống "bỏ scrypt ở CẢ HAI nhánh": nếu ai đó thay scrypt bằng sha256
    # thì mọi phép so bằng-nhau ở trên vẫn xanh, mà thời gian tụt xuống ~0.
    t0 = time.perf_counter()
    TK.bam('mat-khau-nao-do', 'ab' * 16)
    ms = (time.perf_counter() - t0) * 1000
    kiem(ms >= 8,
         f'Và bam() thật sự đắt (>= 8 ms) — {ms:.0f} ms. Mục này bắt lỗi '
         f'"thay scrypt bằng hàm băm rẻ tiền", thứ mà phép so bằng-nhau '
         f'không bao giờ thấy')


# ==========================================================================
def ca_9_thieu_tai_khoan(tm):
    print('\nCA 9 — thiếu/hỏng tai_khoan.json: máy chủ TỪ CHỐI KHỞI ĐỘNG')
    print('-' * 74)
    dd, tmx = dung(tm, 'd9')

    # TẦNG 1 — main() thật, chạy bằng tiến trình con. Đây là tầng mà MayChuTam
    # KHÔNG đi qua, nên nếu chỉ thử qua MayChuTam thì ai xoá lời gọi trong
    # main() cũng không làm đỏ được gì.
    for nhan, noi in (('không có tệp', None),
                      ('JSON hỏng', '{ hong'),
                      ('rỗng', '{"phien_ban":1,"tai_khoan":[]}'),
                      ('sai kiểu', '{"phien_ban":1,"tai_khoan":"x"}')):
        dd_tk = os.path.join(tmx, f'tk-{nhan[:4]}.json')
        if noi is not None:
            io.open(dd_tk, 'w', encoding='utf-8').write(noi)
        r = subprocess.run(
            [sys.executable, os.path.join(GOC_TM, 'web.py'),
             '--port', '20997', '--cauhinh', dd, '--tai-khoan', dd_tk],
            capture_output=True, text=True, timeout=60)
        ra = r.stdout + r.stderr
        kiem(r.returncode != 0,
             f'[{nhan}] máy chủ thoát với mã != 0 — {r.returncode}')
        kiem('Mở trình duyệt vào' not in ra,
             f'[{nhan}] và CHƯA HỀ in dòng "Mở trình duyệt vào"')
        kiem('[LỖI]' in ra and 'tao_mat_khau.py' in ra,
             f'[{nhan}] câu lỗi chỉ đúng lệnh cần gõ')

    # TẦNG 2 — máy chủ dựng thẳng, sổ tài khoản rỗng: 503 cho mọi đường
    with MayChuTam(dd, tai_khoan=False, dang_nhap=False) as (k, (dia, cong)):
        kiem(not W.TAI_KHOAN, 'Dựng máy chủ mà không nạp được tài khoản nào')
        ma, t = k.js('/api/quy-tac')
        kiem(ma == 503,
             f'Sổ rỗng -> 503 "chưa cài xong", KHÔNG phải 401 "chưa đăng '
             f'nhập" — {ma}')
        kiem('tao_mat_khau' in str(t), 'Và câu trả lời chỉ đúng lệnh cần gõ')
        kiem(k.get('/')[0] == 200,
             'Đường tĩnh vẫn 200 để trang còn hiện được câu giải thích')
        ma, _ = k.post('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
        kiem(ma == 401,
             f'Và không ai đăng nhập được (sổ rỗng, không mật khẩu mặc '
             f'định) — {ma}')


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ CỔNG ĐĂNG NHẬP (2A-1)')
    print('=' * 74)
    dat_dong_ho_canh(240)
    with tempfile.TemporaryDirectory() as tm:
        ca_1_dang_nhap_dung(tm)
        ca_2_dang_nhap_sai(tm)
        ca_3_xoay_ma_phien(tm)
        ca_4_khong_cookie(tm)
        ca_5_cookie_gia_va_het_han(tm)
        ca_6_dang_xuat(tm)
        ca_7_hai_tai_khoan(tm)
        ca_8_thoi_gian_bang_nhau(tm)
        ca_9_thieu_tai_khoan(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

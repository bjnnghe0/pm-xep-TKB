#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ HẠ TẦNG PHIÊN  (Đợt 2A-2a — CHƯA CÓ ĐĂNG NHẬP)
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_phien.py

 Ở bước này phiên trả lời đúng MỘT câu: "bản nháp quy tắc này là của TRÌNH
 DUYỆT nào". Chưa có mật khẩu, chưa có tên người. Đăng nhập (2A-1) lắp lên
 đúng hạ tầng này.

 LỖI ĐANG HỎNG MÀ ĐỢT NÀY BỊT — đo được trước khi sửa:
   Thầy A thêm một quy tắc nháp (chưa Lưu). Cô B bấm Lưu. Tệp đi từ 13 lên
   14 quy tắc: quy tắc CHƯA AI DUYỆT của A vào thẳng cauhinh.json, còn A vẫn
   thấy nháp của mình là "chưa lưu". Im lặng cả hai chiều. Không cần hai
   người — mở phần mềm trên máy bàn và trên điện thoại đã là hai trình duyệt.

   Dấu bản của cauhinh.json KHÔNG bắt được: lúc B tải danh sách về thì tệp
   trên đĩa chưa hề đổi. Đây là lỗ ở BỘ NHỚ, không phải ở TỆP.

 Theo bất biến kỷ luật ca thử: mọi mục quan sát HÀNH VI qua HTTP thật, không
 khẳng định trên văn bản mã nguồn, và phải biết ĐỎ chứ không biết VỠ.
==========================================================================
"""
import io
import json
import os
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import MayChuTam, Khach, cau_hinh_tam   # noqa: E402
import xep_tkb as X          # noqa: E402
import web as W              # noqa: E402

KQ = []


def dat_dong_ho_canh(giay=180):
    """Bộ thử TREO thì phải báo ĐỎ, không được treo mãi.

       Vì sao cần: một trong những cách hỏng của chính đợt này là khoá không
       tái nhập — doc_phien() gọi bản tự khoá trong khi đang giữ KHOA_PHIEN.
       Đã thử lùi đúng lỗi đó: bộ thử KHÔNG đỏ mà TREO CỨNG, hết 240 giây vẫn
       không xong (MayChuTam.__exit__ gọi may.shutdown(), mà shutdown() chờ mãi
       một luồng xử lý đang kẹt trong khoá).

       Bất biến của dự án là "ca thử phải biết ĐỎ, không phải biết VỠ" — treo
       còn tệ hơn vỡ, vì nó cũng chặn luôn mọi bộ thử chạy sau. Đồng hồ canh này
       biến MỌI deadlock tương lai thành một dòng đỏ, không riêng cái đã biết.
    """
    def bao_treo():
        time.sleep(giay)
        hong = [m for ok, m in KQ if not ok]
        print(f'\n  [LỖI] BỘ THỬ TREO quá {giay} giây — gần như chắc chắn là '
              f'deadlock.')
        print('=' * 74)
        print(f'Tổng: {len(KQ) - len(hong) - 1}/{len(KQ) + 1} mục ĐẠT.')
        print('  LỖI: bộ thử treo, không chạy hết được')
        sys.stdout.flush()
        os._exit(1)
    threading.Thread(target=bao_treo, daemon=True).start()


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def so_qt(dd):
    """Số quy tắc trong tệp trên đĩa; hỏng thì trả None chứ không ném."""
    try:
        return len(X.doc_cau_hinh(dd)['quy_tac'])
    except BaseException:
        return None


def ten_qt(dd):
    try:
        return [r.get('ghi_chu', '') for r in X.doc_cau_hinh(dd)['quy_tac']]
    except BaseException:
        return []


NHAP_A = {'loai': 'khong_xep_thu', 'ghi_chu': 'NHAP-CUA-A-CHUA-DUYET',
          'loc': {'lop': '12B1'}, 'thu': [2]}


# ==========================================================================
def ca_1_moi_trinh_duyet_mot_phien(tm):
    print('\nCA 1 — mỗi trình duyệt được cấp một phiên RIÊNG')
    print('-' * 74)
    tmx = os.path.join(tm, 'p1')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    with MayChuTam(dd) as (kA, (dia, cong)):
        # Khách MỚI TINH, chưa đăng nhập: đây mới là "yêu cầu đầu tiên".
        # kA đã được MayChuTam đăng nhập sẵn nên không dùng để thử việc này.
        k0 = Khach(cong)
        ma, td, _ = k0.yeu_cau('GET', '/')
        kiem(ma == 200 and td.get('set-cookie'),
             f'Yêu cầu đầu tiên được cấp cookie phiên — {td.get("set-cookie")}')
        kB = Khach(cong)
        kB.dang_nhap()
        maA = kA.ma_phien()
        maB = kB.ma_phien()
        kiem(maA and maB and maA != maB,
             f'Hai trình duyệt, hai mã khác nhau — {maA[:12]}… / {maB[:12]}…')
        kiem(len(maA) >= 32, f'Mã đủ dài (token_urlsafe(32)) — {len(maA)} ký tự')

        # đã có cookie thì KHÔNG cấp lại
        ma, td, _ = kA.yeu_cau('GET', '/api/quy-tac')
        kiem(not td.get('set-cookie'),
             'Yêu cầu sau, đã có cookie hợp lệ -> KHÔNG cấp lại phiên mới')
        kiem(kA.ma_phien() == maA, 'Và mã giữ nguyên')


# ==========================================================================
def ca_2_nhap_tach_theo_phien(tm):
    print('\nCA 2 — bản nháp tách theo phiên (ĐÂY LÀ LỖ ĐANG HỎNG)')
    print('-' * 74)
    tmx = os.path.join(tm, 'p2')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    with MayChuTam(dd) as (kA, (dia, cong)):
        kB = Khach(cong)
        kB.dang_nhap()
        n0 = so_qt(dd)
        kiem(n0 and n0 > 0, f'Tệp ban đầu có {n0} quy tắc')

        ma, _ = kA.post('/api/them-quy-tac', {'quy_tac': NHAP_A})
        kiem(ma == 200, f'A thêm một quy tắc nháp — {ma}')
        kiem(so_qt(dd) == n0, 'Tệp trên đĩa CHƯA đổi (nháp chỉ nằm trong bộ nhớ)')

        _, dA = kA.js('/api/quy-tac')
        kiem(dA['so_moi'] == 1, f'A thấy 1 quy tắc chưa lưu — {dA["so_moi"]}')

        _, dB = kB.js('/api/quy-tac')
        kiem(dB['so_moi'] == 0,
             f'B KHÔNG thấy nháp của A — B có {dB["so_moi"]} quy tắc chưa lưu')
        kiem(not any(r['ghi_chu'] == NHAP_A['ghi_chu'] for r in dB['quy_tac']),
             'Và nháp của A không hề xuất hiện trong danh sách của B')

        # ---- CHÍNH LỖI: B bấm Lưu ----
        ma, _ = kB.js('/api/luu-quy-tac', {'tat': []})
        kiem(ma == 200, f'B bấm Lưu — {ma}')
        kiem(so_qt(dd) == n0,
             f'Tệp VẪN {n0} quy tắc: nháp chưa duyệt của A KHÔNG bị B ghi xuống '
             f'đĩa — thực tế {so_qt(dd)}')
        kiem(NHAP_A['ghi_chu'] not in ten_qt(dd),
             'Và tên nháp của A không có trong tệp')

        # nháp của A phải còn nguyên
        _, dA2 = kA.js('/api/quy-tac')
        kiem(dA2['so_moi'] == 1,
             f'Nháp của A vẫn còn nguyên sau khi B lưu — {dA2["so_moi"]}')

        # ---- A tự lưu thì nháp của A MỚI vào tệp ----
        ma, kq = kA.js('/api/luu-quy-tac', {'tat': []})
        kiem(ma == 200 and so_qt(dd) == n0 + 1,
             f'A tự bấm Lưu thì nháp của A mới vào tệp — {so_qt(dd)}')
        _, dA3 = kA.js('/api/quy-tac')
        kiem(dA3['so_moi'] == 0, 'Lưu xong thì kho nháp của A rỗng')


# ==========================================================================
def ca_3_cookie_dung_che_do(tm):
    print('\nCA 3 — hai tên cookie, mỗi đường một tên, đọc ĐÚNG MỘT tên')
    print('-' * 74)
    tmx = os.path.join(tm, 'p3')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)
    mc = os.path.join(tmx, 'cauhinh_may_chu.json')
    TEN = 'admin.tail7dc28e.ts.net'

    with MayChuTam(dd, may_chu=mc) as (k, (dia, cong)):
        with io.open(mc, 'w', encoding='utf-8') as f:
            json.dump({'host_cho_phep': [f'127.0.0.1:{cong}', TEN],
                       'origin_cho_phep': [f'http://127.0.0.1:{cong}',
                                           'https://' + TEN]}, f)
        W.nap_cau_hinh_may_chu(mc)

        # --- đường TẠI CHỖ (http) ---
        k1 = Khach(cong)
        _, td, _ = k1.yeu_cau('GET', '/',
                              them={'Host': f'127.0.0.1:{cong}'})
        c1 = (td.get('set-cookie') or [''])[0]
        kiem(c1.startswith(W.TEN_COOKIE + '='),
             f'Tại chỗ: dùng tên trơn {W.TEN_COOKIE} — {c1[:60]}')
        kiem('Secure' not in c1,
             'Tại chỗ: KHÔNG có cờ Secure (http thì trình duyệt sẽ vứt cookie đi)')
        kiem('HttpOnly' in c1 and 'SameSite=Lax' in c1 and 'Path=/' in c1,
             f'Tại chỗ: đủ HttpOnly · SameSite=Lax · Path=/ — {c1[:80]}')

        # --- đường QUA PROXY (https) ---
        k2 = Khach(cong)
        _, td, _ = k2.yeu_cau('GET', '/', them={'Host': TEN})
        c2 = (td.get('set-cookie') or [''])[0]
        kiem(c2.startswith(W.TEN_COOKIE_BM + '='),
             f'Qua proxy: dùng tên {W.TEN_COOKIE_BM} — {c2[:60]}')
        kiem('Secure' in c2, 'Qua proxy: CÓ cờ Secure')
        kiem('SameSite=Lax' in c2,
             'Qua proxy: SameSite=Lax, khai TƯỜNG MINH (bỏ trống KHÔNG giống Lax '
             'vì Chrome có ngoại lệ Lax+POST 2 phút cho cookie không khai)')

        # --- CẢ HAI đường phải độc lập chạy được, không đường nào kẹt ---
        for nhan, host, kh in (('tại chỗ', f'127.0.0.1:{cong}', k1),
                               ('qua proxy', TEN, k2)):
            kh.dang_nhap(them={'Host': host})
            ma, _ = kh.post('/api/them-quy-tac', {'quy_tac': NHAP_A},
                            them={'Host': host})
            _, d = kh.js('/api/quy-tac', them={'Host': host})
            kiem(ma == 200 and d['so_moi'] == 1,
                 f'{nhan}: thêm nháp rồi đọc lại thấy đúng nháp của mình '
                 f'— {ma}, so_moi={d["so_moi"]}')

        # --- CHỈ đọc một tên: gửi tên của chế độ KIA thì không được nhận ---
        k3 = Khach(cong)
        k3.dang_nhap(them={'Host': f'127.0.0.1:{cong}'})
        ma_tron = k3.cookie[W.TEN_COOKIE]
        k3.post('/api/them-quy-tac', {'quy_tac': NHAP_A},
                them={'Host': f'127.0.0.1:{cong}'})
        # đưa ĐÚNG mã đó sang đường proxy nhưng dưới tên TRƠN -> phải bị bỏ qua
        ma, td, t = k3.yeu_cau('GET', '/api/quy-tac', cookie=False,
                               them={'Host': TEN,
                                     'Cookie': f'{W.TEN_COOKIE}={ma_tron}'})
        kiem(ma == 401,
             f'Gửi cookie tên TRƠN vào đường proxy -> KHÔNG được nhận, thành '
             f'chưa đăng nhập — {ma}')
        kiem(td.get('set-cookie') and
             td['set-cookie'][0].startswith(W.TEN_COOKIE_BM),
             'Và phiên mới cấp dưới đúng tên __Host-')

    W.nap_cau_hinh_may_chu(os.path.join(tmx, 'khong-co.json'))


# ==========================================================================
def ca_4_cookie_di_dang(tm):
    print('\nCA 4 — cookie dị dạng: cấp phiên mới, KHÔNG vỡ')
    print('-' * 74)
    tmx = os.path.join(tm, 'p4')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    with MayChuTam(dd) as (k, (dia, cong)):
        DI_DANG = ['', '   ', 'khong-co-dau-bang', f'{W.TEN_COOKIE}=',
                   f'{W.TEN_COOKIE}=ma"co-nhay', f'{W.TEN_COOKIE}=' + 'A' * 500,
                   f'{W.TEN_COOKIE}=ma;;;;', 'tenkhac=abc',
                   f'{W.TEN_COOKIE}=khong-ton-tai-trong-so']
        hong = []
        for c in DI_DANG:
            ma, td, t = Khach(cong).yeu_cau('GET', '/', cookie=False,
                                            them={'Cookie': c})
            if ma != 200:
                hong.append((c[:28], ma))
        kiem(not hong, f'Mọi cookie dị dạng vẫn cho 200 và cấp phiên mới — {hong}')

        # hai dòng Cookie -> 400, cùng lý lẽ với Host/Origin
        ma, _, _ = k.tho_dong('GET', '/',
                              [('Host', f'127.0.0.1:{cong}'),
                               ('Cookie', f'{W.TEN_COOKIE}=a'),
                               ('Cookie', f'{W.TEN_COOKIE}=b'),
                               ('Connection', 'close')])
        kiem(ma == 400, f'Hai dòng Cookie -> 400 — {ma}')

        # không bao giờ nhận nuôi mã do khách bịa (chống cố định phiên)
        BIA = 'B' * 43
        kh = Khach(cong)
        ma, td, _ = kh.yeu_cau('GET', '/', cookie=False,
                               them={'Cookie': f'{W.TEN_COOKIE}={BIA}'})
        cap = (td.get('set-cookie') or [''])[0]
        kiem(BIA not in cap,
             f'Mã khách BỊA ra KHÔNG bao giờ thành mã phiên thật — {cap[:60]}')


# ==========================================================================
def ca_5_het_han_va_tran(tm):
    print('\nCA 5 — hết hạn, trần phiên, và khoá không tái nhập')
    print('-' * 74)
    tmx = os.path.join(tm, 'p5')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    nghi, toi_da, tran = W.GIAY_NGHI_PHIEN, W.GIAY_TOI_DA_PHIEN, W.TRAN_PHIEN
    try:
        with MayChuTam(dd) as (k, (dia, cong)):
            k.post('/api/them-quy-tac', {'quy_tac': NHAP_A})
            _, d = k.js('/api/quy-tac')
            kiem(d['so_moi'] == 1, 'Dựng sẵn: có 1 nháp')

            # --- hết hạn NGHỈ ---
            W.GIAY_NGHI_PHIEN = 0.4
            time.sleep(0.8)
            ma, _ = k.get('/api/quy-tac')
            kiem(ma == 401,
                 f'Quá hạn NGHỈ -> phiên chết, phải đăng nhập lại — {ma}')
            W.GIAY_NGHI_PHIEN = nghi

            # Chỗ này chính là phép thử khoá-không-tái-nhập: tao_phien() gọi
            # _don_phien_da_khoa() TRONG KHI đang giữ KHOA_PHIEN. Nếu ai đó đổi
            # sang gọi bản tự khoá thì máy chủ TREO CỨNG ngay tại đây, và mục
            # dưới sẽ hết giờ chứ không đỏ — nên đo bằng đồng hồ.
            t0 = time.time()
            ma, _ = k.get('/')
            kiem(ma == 200 and time.time() - t0 < 5,
                 f'Dọn phiên hết hạn KHÔNG treo (khoá không tái nhập) — '
                 f'{time.time() - t0:.2f}s')

            # --- hết hạn TUYỆT ĐỐI, không gia hạn được ---
            k2 = Khach(cong)
            k2.dang_nhap()
            k2.post('/api/them-quy-tac', {'quy_tac': NHAP_A})
            W.GIAY_TOI_DA_PHIEN = 0.4
            for _ in range(4):                # cứ hỏi liên tục để làm tươi cham_*
                time.sleep(0.15)
                k2.get('/api/quy-tac')
            ma, _ = k2.get('/api/quy-tac')
            kiem(ma == 401,
                 f'Hạn TUYỆT ĐỐI không gia hạn được dù hỏi liên tục — {ma}')
            W.GIAY_TOI_DA_PHIEN = toi_da

            # --- trần phiên: ĐUỔI cái cũ nhất, KHÔNG từ chối người mới ---
            W.xoa_sach_phien()
            W.TRAN_PHIEN = 4
            ma_cuoi = []
            for i in range(8):
                kh = Khach(cong)
                ma, _ = kh.get('/')
                ma_cuoi.append(ma)
            kiem(all(m == 200 for m in ma_cuoi),
                 f'Vượt trần vẫn phục vụ người mới, không từ chối ai — {ma_cuoi}')
            kiem(len(W.CAC_PHIEN) <= 4,
                 f'Và sổ phiên không phình quá trần — {len(W.CAC_PHIEN)} mục')
    finally:
        W.GIAY_NGHI_PHIEN, W.GIAY_TOI_DA_PHIEN, W.TRAN_PHIEN = nghi, toi_da, tran


# ==========================================================================
def ca_6_khong_hoi_quy(tm):
    print('\nCA 6 — không làm hồi quy bất biến cũ')
    print('-' * 74)
    tmx = os.path.join(tm, 'p6')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    with MayChuTam(dd) as (k, (dia, cong)):
        # A1 vẫn phải chặn Host lạ — cấp phiên KHÔNG được đi trước cổng A1
        ma, td, _ = k.yeu_cau('GET', '/api/quy-tac', them={'Host': 'evil.com'})
        kiem(ma == 400, f'A1: Host lạ vẫn 400 — {ma}')
        kiem(not td.get('set-cookie'),
             'Và yêu cầu bị A1 chặn thì KHÔNG được cấp phiên (cổng A1 đi trước)')

        # A10: Set-Cookie phải đi qua đúng phễu _tra_byte
        ma_nguon = io.open(os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            'web.py'), encoding='utf-8').read()
        than = ma_nguon.split('def _tra_byte')[1].split('# ---------------- tiện ích')[0]
        ngoai = ma_nguon.replace(than, '')
        kiem(ngoai.count('self.send_header(') == 0,
             'A10: ngoài _tra_byte vẫn không còn chỗ nào gọi send_header')

        # đường tải tệp cũng phải cấp được phiên và không vỡ
        ma, _ = k.get('/api/tai-web')
        kiem(ma in (200, 404), f'Đường tải tệp vẫn phục vụ bình thường — {ma}')


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ HẠ TẦNG PHIÊN (2A-2a — chưa có đăng nhập)')
    print('=' * 74)
    dat_dong_ho_canh(180)
    with tempfile.TemporaryDirectory() as tm:
        ca_1_moi_trinh_duyet_mot_phien(tm)
        ca_2_nhap_tach_theo_phien(tm)
        ca_3_cookie_dung_che_do(tm)
        ca_4_cookie_di_dang(tm)
        ca_5_het_han_va_tran(tm)
        ca_6_khong_hoi_quy(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

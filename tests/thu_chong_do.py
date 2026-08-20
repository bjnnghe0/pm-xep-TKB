#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ 2B — CHỐNG DÒ MẬT KHẨU  (QĐ 6)
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_chong_do.py

 QĐ 6: sai 5 lần -> khoá 15 phút, đếm theo TÀI KHOẢN, cửa sổ quên 30 phút.
 Đếm theo tài khoản chứ không theo IP là bắt buộc, không phải lựa chọn: sau
 Tailscale Serve mọi yêu cầu đều mang 127.0.0.1, nên đếm theo IP là đếm tất cả
 mọi người vào chung một ô.

 HAI ĐIỀU KIỆN ĐÃ CHỐT, và cả hai đều được đo bằng cách ĐẾM SỐ LỜI GỌI scrypt
 chứ không đo đồng hồ (đo thời gian thì phụ thuộc tải máy và sẽ chớp đỏ ngẫu
 nhiên trên máy của trường):
   1. Thời gian trả lời như nhau dù tài khoản có tồn tại hay không — CA 3.
   2. NHÁNH BỊ KHOÁ VẪN PHẢI CHẠY ĐỦ MỘT LƯỢT SCRYPT — CA 2. Thoát sớm ở đó là
      đổi 27 ms lấy một kênh đo: gõ bậy 5 lần rồi xem lần thứ 6 trả lời nhanh
      hay chậm là biết tài khoản có thật hay không.

 CA 9 là mục khó nhất và cũng đáng giá nhất: bắn một loạt yêu cầu CÙNG LÚC để
 bắt lỗi tách "kiểm" và "tăng" ra hai lần giữ khoá. Đó đúng là lỗi A4 mà
 gianh_luot() đã giải một lần cho cờ "đang chạy".

 Theo bất biến kỷ luật ca thử: quan sát HÀNH VI qua HTTP thật, có ĐỒNG HỒ CANH,
 và mỗi mục phải biết ĐỎ chứ không biết VỠ.
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

from tien_ich_web import GOC_TM, MayChuTam, Khach, cau_hinh_tam   # noqa: E402
import tai_khoan as TK       # noqa: E402
import web as W              # noqa: E402

KQ = []
MK = MayChuTam.MAT_KHAU
TEN = MayChuTam.TEN
SAI = 'mat-khau-sai-be-bet'
NGUONG = TK.SO_LAN_SAI_TOI_DA


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
        print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ) + 1} mục ĐẠT.')
        print('  LỖI: bộ thử treo, không chạy hết được')
        sys.stdout.flush()
        os._exit(1)
    threading.Thread(target=bao, daemon=True).start()


def dung(tm, ten_thu):
    tmx = os.path.join(tm, ten_thu)
    os.makedirs(tmx, exist_ok=True)
    return cau_hinh_tam(tmx), tmx


def dd_so(tmx):
    return TK.duong_dan_khoa(os.path.join(tmx, 'tai_khoan.json'))


RONG = {'sai': 0, 'lan_cuoi': 0.0, 'khoa_den': 0.0}


def doc_so(tmx):
    """Đọc sổ trên đĩa. HÀM TOÀN PHẦN — thiếu tệp / tệp hỏng thì trả {}.

       Bắt buộc phải toàn phần: mọi bản HỎNG đang thử ở đây đều có thể làm sổ
       biến mất (gỡ hẳn 2B, hay đem sổ vào RAM). Nếu hàm này ném thì bộ thử
       CHẾT GIỮA CHỪNG thay vì báo đỏ, và mọi ca sau nó không bao giờ chạy —
       đúng bẫy số 2 trong bảng kỷ luật ca thử của CLAUDE.md. Đã dính một lần.
    """
    try:
        with io.open(dd_so(tmx), encoding='utf-8') as f:
            so = json.load(f)['khoa']
        return so if isinstance(so, dict) else {}
    except (OSError, ValueError, KeyError, TypeError):
        return {}


def muc(tmx, ten=None):
    """Bản ghi của một tài khoản trong sổ; chưa có thì trả bản RỖNG."""
    return dict(RONG, **doc_so(tmx).get(ten or TEN, {}))


def ghi_so(tmx, so):
    """Sửa thẳng sổ trên đĩa — đây là cách hợp lệ để dời đồng hồ.

       Không vá đè time.time(): tai_khoan.py dùng đồng hồ treo tường CHÍNH VÌ
       hai tiến trình phải đọc chung, nên tệp mới là giao diện thật giữa chúng —
       lệnh mo-khoa cũng sửa đúng tệp này. Vá đồng hồ thì phải vá cho cả tiến
       trình con, và ta sẽ đo một thứ không tồn tại ngoài đời.
    """
    with io.open(dd_so(tmx), 'w', encoding='utf-8') as f:
        json.dump({'phien_ban': TK.PHIEN_BAN, 'khoa': so}, f)


def dem_bam():
    """Vá đè TK.bam bằng bản có bộ đếm. Trả (dict đếm, hàm trả lại bản gốc)."""
    that, dem, khoa = TK.bam, {'n': 0}, threading.Lock()

    def bam_dem(*a, **kw):
        with khoa:
            dem['n'] += 1
        return that(*a, **kw)
    TK.bam = bam_dem
    return dem, (lambda: setattr(TK, 'bam', that))


def sai_may_lan(k, lan, ten=TEN):
    """Gõ sai `lan` lần. Trả danh sách (mã, thân)."""
    return [k.js('/api/dang-nhap', {'ten': ten, 'mat_khau': SAI})
            for _ in range(lan)]


# ==========================================================================
def ca_1_khoa_sau_dung_nguong(tm):
    print(f'\nCA 1 — {NGUONG} lần sai vẫn được thử, lần thứ {NGUONG + 1} bị chặn')
    print('-' * 74)
    dd, tmx = dung(tm, 'c1')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        ma = [m for m, _ in sai_may_lan(k, NGUONG)]
        kiem(ma == [401] * NGUONG,
             f'{NGUONG} lần sai đầu đều 401 "sai mật khẩu", chưa khoá — {ma}')

        m6, t6 = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': SAI})
        kiem(m6 == 429,
             f'Lần thứ {NGUONG + 1} -> 429 (không phải 401) — {m6}')
        cau = (t6 or {}).get('loi', '')
        kiem('khoá tạm' in cau, f'Câu trả lời nói rõ ĐANG BỊ KHOÁ — {cau[:60]!r}')
        kiem('phút' in cau and any(f'còn {p} phút' in cau for p in range(1, 16)),
             f'Và nói RÕ CÒN BAO NHIÊU PHÚT — {cau.splitlines()[0]!r}')
        kiem(f'mo-khoa {TEN}' in cau,
             'Và nhắc gỡ được TẠI MÁY, kèm nguyên câu lệnh phải gõ')
        kiem('python3 tao_mat_khau.py' in cau,
             'Câu lệnh ấy viết python3, đúng máy Linux đang chạy')

        # Ba mục canh: 429 KHÔNG được cấp phiên, và không lộ mật khẩu/bản băm.
        kiem(k.ma_phien() is None or W.doc_phien(k.ma_phien()) is None
             or W.doc_phien(k.ma_phien()).get('ten') is None,
             'Bị khoá thì KHÔNG có phiên đã đăng nhập nào được cấp')
        kiem(MK not in cau and SAI not in cau,
             'Câu trả lời không nhắc lại mật khẩu vừa gõ')


# ==========================================================================
def ca_2_nhanh_khoa_van_chay_scrypt(tm):
    print('\nCA 2 — ĐIỀU KIỆN 2: nhánh BỊ KHOÁ vẫn chạy ĐỦ MỘT lượt scrypt')
    print('-' * 74)
    dd, tmx = dung(tm, 'c2')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG)                    # đẩy tới ngưỡng
        dem, tra_lai = dem_bam()
        try:
            for i in range(3):
                dem['n'] = 0
                ma, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': SAI})
                kiem(ma == 429 and dem['n'] == 1,
                     f'Lần bị khoá thứ {i + 1}: mã {ma}, chạy ĐÚNG '
                     f'{dem["n"]} lần scrypt (phải là 1)')
            # Và cả khi mật khẩu ĐÚNG: vẫn một lần scrypt, vẫn bị chặn.
            dem['n'] = 0
            ma, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
            kiem(ma == 429 and dem['n'] == 1,
                 f'Đang khoá mà gõ ĐÚNG mật khẩu: vẫn 429 và vẫn 1 lần '
                 f'scrypt — mã {ma}, {dem["n"]} lần')
        finally:
            tra_lai()

    # Guard chống "bỏ scrypt ở CẢ HAI nhánh": thay bằng hàm băm rẻ tiền thì mọi
    # phép so bằng-nhau ở trên vẫn xanh, mà thời gian tụt xuống ~0.
    t0 = time.perf_counter()
    TK.bam('mat-khau-nao-do', 'ab' * 16)
    ms = (time.perf_counter() - t0) * 1000
    kiem(ms >= 8, f'Và bam() thật sự đắt (>= 8 ms) — {ms:.0f} ms')


# ==========================================================================
def ca_3_moi_nhanh_mot_lan_scrypt(tm):
    print('\nCA 3 — ĐIỀU KIỆN 1: mọi loại tên đều đúng MỘT lần scrypt, kể cả '
          'khi tài khoản thật ĐANG bị khoá')
    print('-' * 74)
    dd, tmx = dung(tm, 'c3')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG + 1)                # tài khoản thật ĐANG bị khoá
        kiem(k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': SAI})[0] == 429,
             'Điều kiện tiên quyết: tài khoản thật đang bị khoá')

        dem, tra_lai = dem_bam()
        try:
            for nhan, ten in (('tên CÓ thật (đang khoá)', TEN),
                              ('tên KHÔNG có', 'khongcoainay'),
                              ('tên sai cú pháp', '!!!'),
                              ('tên rỗng', '')):
                dem['n'] = 0
                k.js('/api/dang-nhap', {'ten': ten, 'mat_khau': SAI})
                kiem(dem['n'] == 1,
                     f'{nhan}: chạy ĐÚNG 1 lần scrypt — {dem["n"]} lần')
        finally:
            tra_lai()

        # Tên KHÔNG có thật thì KHÔNG BAO GIỜ vào sổ. Hai lý do, và mục này
        # canh cả hai:
        #  · Sổ chỉ nhận tên do TAI_KHOAN xác nhận, nên khách không điều khiển
        #    được kích thước sổ — nếu không thì mười triệu tên bịa là mười
        #    triệu mục, và /api/dang-nhap là đường CHƯA XÁC THỰC.
        #  · Không có mục thì không có gì để đuổi. Bản nào "cũng đếm tên bịa
        #    cho công bằng" đều phải kèm trần + phép đuổi, và phép đuổi ấy
        #    CHÍNH LÀ đường lách khoá: bắn đủ tên bịa là đẩy mục thật ra ngoài.
        for i in range(NGUONG + 3):
            k.js('/api/dang-nhap', {'ten': 'khongcoainay', 'mat_khau': SAI})
        so = doc_so(tmx)
        kiem(list(so) == [TEN],
             f'Sổ khoá tạm CHỈ chứa tài khoản có thật — {list(so)}')
        ma, _ = k.js('/api/dang-nhap', {'ten': 'khongcoainay', 'mat_khau': SAI})
        kiem(ma == 401,
             f'Tên bịa gõ sai bao nhiêu lần cũng chỉ 401, không bao giờ khoá '
             f'— {ma}. (ĐÁNH ĐỔI CÓ CHỦ Ý: ai chịu gõ sai đủ {NGUONG} lần thì '
             f'phân biệt được tên có thật qua 429 vs 401. Bịt chiều đó thì phải '
             f'đếm cả tên bịa, mà như vậy là mở đường lách khoá bằng cách bắn '
             f'cho tràn sổ. Đổi lại được câu báo dùng được cho thầy cô.)')


# ==========================================================================
def ca_4_dang_nhap_dung_xoa_bo_dem(tm):
    print('\nCA 4 — đăng nhập ĐÚNG xoá sạch bộ đếm')
    print('-' * 74)
    dd, tmx = dung(tm, 'c4')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG - 1)
        kiem(muc(tmx)['sai'] == NGUONG - 1,
             f'Sai {NGUONG - 1} lần: sổ ghi {muc(tmx)['sai']}')
        ma, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
        kiem(ma == 200,
             f'Lần thứ {NGUONG} gõ ĐÚNG thì vào được, không bị chặn oan — {ma}')
        kiem(TEN not in doc_so(tmx),
             f'Và sổ sạch trơn — {doc_so(tmx)}')

        # Nếu bộ đếm không được xoá thì vài lần lỡ tay rải rác trong ngày sẽ
        # cộng dồn thành khoá oan. Đo lại từ đầu để chắc.
        k2 = Khach(cong)
        ma = [m for m, _ in sai_may_lan(k2, NGUONG)]
        kiem(ma == [401] * NGUONG,
             f'Đếm lại từ 0: {NGUONG} lần sai nữa vẫn chưa khoá — {ma}')


# ==========================================================================
def ca_5_go_them_khong_keo_dai_khoa(tm):
    print('\nCA 5 — gõ thêm lúc đang khoá KHÔNG kéo dài thời gian khoá')
    print('-' * 74)
    dd, tmx = dung(tm, 'c5')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG + 1)
        den1 = muc(tmx)['khoa_den']
        sai1 = muc(tmx)['sai']
        sai_may_lan(k, 6)                       # người sốt ruột bấm lại
        den2 = muc(tmx)['khoa_den']
        kiem(den2 == den1,
             f'Bấm thêm 6 lần: mốc hết khoá KHÔNG dời — {den1} vs {den2}')
        kiem(muc(tmx)['sai'] == sai1,
             f'Và bộ đếm cũng không phình thêm — {sai1} -> '
             f'{muc(tmx)['sai']}')
        kiem(den1 - time.time() <= TK.GIAY_KHOA + 1,
             f'Khoá đúng {TK.GIAY_KHOA // 60} phút, không hơn — '
             f'còn {int(den1 - time.time())}s')


# ==========================================================================
def ca_6_het_gio_va_cua_so_quen(tm):
    print('\nCA 6 — hết 15 phút thì tự mở; cửa sổ quên 30 phút xoá bộ đếm cũ')
    print('-' * 74)
    dd, tmx = dung(tm, 'c6')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG + 1)
        kiem(k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})[0] == 429,
             'Điều kiện tiên quyết: đang bị khoá, mật khẩu đúng cũng không vào')

        # Dời mốc hết khoá về quá khứ — y như đã đợi đủ 15 phút.
        so = doc_so(tmx)
        so.setdefault(TEN, dict(RONG))['khoa_den'] = time.time() - 1
        ghi_so(tmx, so)
        ma, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
        kiem(ma == 200, f'Hết khoá thì vào lại được ngay — {ma}')

        # Cửa sổ quên: sai gần đủ ngưỡng, im lặng hơn 30 phút, rồi sai một lần
        # nữa -> phải đếm lại từ đầu chứ không khoá.
        k2 = Khach(cong)
        sai_may_lan(k2, NGUONG - 1)
        so = doc_so(tmx)
        so.setdefault(TEN, dict(RONG))['lan_cuoi'] = time.time() - TK.GIAY_QUEN - 60
        ghi_so(tmx, so)
        ma = [m for m, _ in sai_may_lan(k2, NGUONG)]
        kiem(ma == [401] * NGUONG,
             f'Sau {TK.GIAY_QUEN // 60} phút im lặng, bộ đếm quên sạch — {ma}')
        kiem(muc(tmx)['sai'] == NGUONG,
             f'Sổ đếm lại từ 1 — {muc(tmx)['sai']}')


# ==========================================================================
def ca_7_mo_khoa_tu_tien_trinh_khac(tm):
    print('\nCA 7 — mo-khoa từ TIẾN TRÌNH KHÁC gỡ được cho máy chủ ĐANG CHẠY')
    print('-' * 74)
    dd, tmx = dung(tm, 'c7')
    dd_tk = os.path.join(tmx, 'tai_khoan.json')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG + 1)
        kiem(k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})[0] == 429,
             'Điều kiện tiên quyết: đang bị khoá')

        # Đây là LÝ DO sổ khoá tạm phải nằm trong TỆP chứ không trong RAM của
        # web.py: lệnh gỡ khoá chạy ở một tiến trình HOÀN TOÀN KHÁC.
        r = subprocess.run(
            [sys.executable, os.path.join(GOC_TM, 'tao_mat_khau.py'),
             'mo-khoa', TEN, '--tep', dd_tk],
            capture_output=True, text=True, timeout=60)
        ra = r.stdout + r.stderr
        kiem(r.returncode == 0 and 'Đã gỡ khoá' in ra,
             f'Lệnh mo-khoa chạy xong — mã {r.returncode}')
        kiem('phút' in ra, f'Và nói rõ trước đó còn bao lâu — {ra.strip()[-160:]!r}')

        ma, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
        kiem(ma == 200,
             f'Máy chủ ĐANG CHẠY nhận ra ngay, không phải khởi động lại — {ma}')

        # Gỡ khoá cho một tên không tồn tại phải báo rõ, không im lặng "xong".
        r = subprocess.run(
            [sys.executable, os.path.join(GOC_TM, 'tao_mat_khau.py'),
             'mo-khoa', 'khongcoainay', '--tep', dd_tk],
            capture_output=True, text=True, timeout=60)
        kiem(r.returncode != 0 and 'Không có tài khoản' in (r.stdout + r.stderr),
             f'mo-khoa cho tên không tồn tại -> báo lỗi rõ, mã {r.returncode}')


# ==========================================================================
def ca_8_loat_ban_don(tm):
    print('\nCA 8 — bắn dồn: kiểm và tăng phải trong CÙNG một lần giữ khoá')
    print('-' * 74)
    dd, tmx = dung(tm, 'c8')
    SO_LUONG = 40
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        ma = [None] * SO_LUONG
        vao_cuoc = threading.Barrier(SO_LUONG)

        def ban(i):
            kh = Khach(cong)
            try:
                vao_cuoc.wait(timeout=30)       # đồng loạt, không lần lượt
                ma[i] = kh.js('/api/dang-nhap',
                              {'ten': TEN, 'mat_khau': SAI})[0]
            except Exception as e:              # đỏ, không vỡ
                ma[i] = repr(e)[:40]

        luong = [threading.Thread(target=ban, args=(i,), daemon=True)
                 for i in range(SO_LUONG)]
        [t.start() for t in luong]
        [t.join(timeout=60) for t in luong]

        so_401 = sum(1 for m in ma if m == 401)
        so_429 = sum(1 for m in ma if m == 429)
        kiem(so_401 + so_429 == SO_LUONG,
             f'Cả {SO_LUONG} yêu cầu đều được trả lời — 401:{so_401} '
             f'429:{so_429} khác:{[m for m in ma if m not in (401, 429)]}')
        # ĐÂY là mục đáng giá: nếu "kiểm" và "tăng" tách ra hai lần giữ khoá thì
        # cả 40 yêu cầu đều đọc thấy "chưa khoá" trước khi bộ đếm kịp lên tới
        # ngưỡng, và lọt cả 40. Đúng lỗi A4 mà gianh_luot() đã giải một lần.
        kiem(so_401 <= NGUONG,
             f'Nhiều nhất {NGUONG} yêu cầu lọt qua, phần còn lại bị chặn — '
             f'lọt {so_401}')
        kiem(so_429 >= SO_LUONG - NGUONG,
             f'Và ít nhất {SO_LUONG - NGUONG} yêu cầu nhận 429 — {so_429}')


# ==========================================================================
def ca_9_so_ben_va_khong_chua_bi_mat(tm):
    print('\nCA 9 — sổ khoá tạm: sống sót qua khởi động lại, không chứa bí mật')
    print('-' * 74)
    dd, tmx = dung(tm, 'c9')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG + 1)

    try:
        tho = io.open(dd_so(tmx), encoding='utf-8').read()
    except OSError as e:
        tho = ''
        kiem(False, f'Sổ khoá tạm phải nằm TRÊN ĐĨA để tiến trình khác đọc '
                    f'được — không mở nổi: {e}')
    kiem(bool(tho) and MK not in tho and SAI not in tho,
         'Sổ không chứa mật khẩu nào')
    ban_ghi = TK.doc_tho(os.path.join(tmx, 'tai_khoan.json'))[0]
    kiem(ban_ghi['bam'] not in tho and ban_ghi['muoi'] not in tho,
         'Sổ không chứa bản băm hay muối')
    if os.name == 'posix':
        try:
            che = oct(os.stat(dd_so(tmx)).st_mode & 0o777)
        except OSError:
            che = 'KHÔNG CÓ TỆP'
        kiem(che == '0o600', f'Quyền tệp 600, đặt ngay lúc tạo — {che}')

    # Dựng lại máy chủ mà KHÔNG xoá sổ: khởi động lại web.py không phải là
    # đường lách khoá. (CAC_PHIEN nằm trong RAM nên mất; sổ khoá thì không.)
    with MayChuTam(dd, dang_nhap=False, xoa_so_khoa=False) as (k, (dia, cong)):
        ma, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
        kiem(ma == 429,
             f'Khởi động lại máy chủ KHÔNG gỡ khoá — {ma}')


# ==========================================================================
def ca_10_so_hong_thi_fail_open_va_keu_to(tm):
    print('\nCA 10 — sổ hỏng: coi như chưa ai bị khoá, và KÊU TO ra dòng lệnh')
    print('-' * 74)
    dd, tmx = dung(tm, 'c10')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        sai_may_lan(k, NGUONG + 1)
        kiem(k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})[0] == 429,
             'Điều kiện tiên quyết: đang bị khoá')

        try:
            io.open(dd_so(tmx), 'w', encoding='utf-8').write('{ hong be bet')
        except OSError as e:
            kiem(False, f'Không làm hỏng được sổ để thử: {e}')
        cu, sys.stderr = sys.stderr, io.StringIO()
        try:
            ma, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
            keu = sys.stderr.getvalue()
        finally:
            sys.stderr = cu
        kiem(ma == 200,
             f'Sổ hỏng -> KHÔNG khoá ai cả, mật khẩu đúng vẫn vào được — {ma}. '
             f'Chiều kia ("hỏng thì khoá hết") biến một byte lỗi thành cảnh cả '
             f'khoa bị nhốt ngoài, mà lớp phòng thủ chính là mật khẩu thì vẫn '
             f'nguyên')
        kiem('[CẢNH BÁO]' in keu,
             f'Nhưng KÊU TO ra cửa sổ dòng lệnh — {keu.strip()[:90]!r}')

        # Và bộ đếm lên đạn lại ngay ở lần gõ sai kế tiếp.
        sai_may_lan(k, NGUONG + 1)
        kiem(k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': SAI})[0] == 429,
             'Lần gõ sai kế tiếp ghi lại sổ mới, khoá lại chạy như thường')


# ==========================================================================
def ca_11_khong_ghi_duoc_so(tm):
    print('\nCA 11 — ghi sổ KHÔNG ĐƯỢC: kêu to, nhưng cổng đăng nhập vẫn chạy')
    print('-' * 74)
    dd, tmx = dung(tm, 'c11')
    with MayChuTam(dd, dang_nhap=False) as (k, (dia, cong)):
        # Trỏ sổ vào một thư mục KHÔNG TỒN TẠI. Không cần đụng tới quyền tệp,
        # nên ca thử cho cùng kết quả dù chạy bằng người dùng thường hay root.
        cu_dd, W.DUONG_DAN_SO_KHOA = (W.DUONG_DAN_SO_KHOA,
                                      '/khong-co-thu-muc-nay-dau/so.json')
        cu_err, sys.stderr = sys.stderr, io.StringIO()
        try:
            ma_sai = [m for m, _ in sai_may_lan(k, NGUONG + 2)]
            ma_dung, _ = k.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})
            keu = sys.stderr.getvalue()
        finally:
            sys.stderr = cu_err
            W.DUONG_DAN_SO_KHOA = cu_dd

        kiem(set(ma_sai) == {401},
             f'Gõ sai vẫn nhận 401 tử tế, KHÔNG phải 500 mã sự cố — {ma_sai}')
        kiem(ma_dung == 200,
             f'Và mật khẩu ĐÚNG vẫn vào được — {ma_dung}. Sổ hỏng không được '
             f'phép làm hỏng cổng đăng nhập: khoá tạm là lớp phòng thủ THÊM')
        kiem('[CẢNH BÁO]' in keu and 'KHOÁ TẠM KHÔNG CÓ TÁC DỤNG' in keu,
             f'Nhưng kêu to, và nói thẳng là khoá tạm đang mất tác dụng — '
             f'{keu.strip().splitlines()[:1]}')

        # Trỏ lại chỗ cũ thì khoá chạy như thường ngay, không cần khởi động lại.
        k2 = Khach(cong)
        sai_may_lan(k2, NGUONG + 1)
        kiem(k2.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': SAI})[0] == 429,
             'Ghi lại được thì khoá tạm chạy lại ngay')


# ==========================================================================
def ca_12_khong_dung_toi_duong_khac(tm):
    print('\nCA 12 — 2B chỉ gác /api/dang-nhap, không đụng tới ai khác')
    print('-' * 74)
    dd, tmx = dung(tm, 'c12')
    with MayChuTam(dd) as (k, (dia, cong)):        # k đã đăng nhập sẵn
        kh = Khach(cong)
        sai_may_lan(kh, NGUONG + 2)                # người khác gõ sai tới khoá
        kiem(kh.js('/api/dang-nhap', {'ten': TEN, 'mat_khau': MK})[0] == 429,
             'Điều kiện tiên quyết: tài khoản đã bị khoá')
        kiem(k.js('/api/quy-tac')[0] == 200,
             'Người ĐÃ đăng nhập từ trước vẫn làm việc bình thường — khoá tạm '
             'chặn CỔNG VÀO, không đá ai đang ở trong ra ngoài')
        kiem(k.js('/api/gia-tri')[0] == 200 and k.get('/')[0] == 200,
             'Các đường khác cũng không bị vạ lây')
        ma, _ = k.post('/api/dang-xuat', {})
        kiem(ma == 200, f'Và vẫn đăng xuất được — {ma}')


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ 2B — CHỐNG DÒ MẬT KHẨU (QĐ 6)')
    print('=' * 74)
    print(f' Ngưỡng {NGUONG} lần · khoá {TK.GIAY_KHOA // 60} phút · '
          f'cửa sổ quên {TK.GIAY_QUEN // 60} phút')
    dat_dong_ho_canh(240)
    with tempfile.TemporaryDirectory() as tm:
        ca_1_khoa_sau_dung_nguong(tm)
        ca_2_nhanh_khoa_van_chay_scrypt(tm)
        ca_3_moi_nhanh_mot_lan_scrypt(tm)
        ca_4_dang_nhap_dung_xoa_bo_dem(tm)
        ca_5_go_them_khong_keo_dai_khoa(tm)
        ca_6_het_gio_va_cua_so_quen(tm)
        ca_7_mo_khoa_tu_tien_trinh_khac(tm)
        ca_8_loat_ban_don(tm)
        ca_9_so_ben_va_khong_chua_bi_mat(tm)
        ca_10_so_hong_thi_fail_open_va_keu_to(tm)
        ca_11_khong_ghi_duoc_so(tm)
        ca_12_khong_dung_toi_duong_khac(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

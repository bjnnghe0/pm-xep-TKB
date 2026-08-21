#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ 2C — DẤU BẢN, CHỐNG MẤT BẢN SỬA  (QĐ 7 và QĐ 4)
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_dau_ban.py

 HAI TẦNG, HAI LỖ KHÁC NHAU — đừng gộp:

 QĐ 7 · dấu bản của cauhinh.json
   Thầy A mở màn hình Quy tắc. Cô B sửa và bấm Lưu. A bấm Lưu theo danh sách
   CŨ của mình -> phần sửa của B mất sạch, im lặng cả hai chiều.

 QĐ 4 · dấu bản của KẾT QUẢ XẾP
   Cô B bấm Xếp, đè hai tệp kết quả. Thầy A đang mở màn hình cũ bấm Tải về và
   nhận tệp của B mà không biết. Dấu bản của QĐ 7 KHÔNG bắt được cái này —
   lúc đó cauhinh.json không hề đổi. Cùng một lỗi, khác tầng.

 DÁN TÊN để BIẾT, DẤU BẢN để CHẶN — cần cả hai, và ca thử đo cả hai.

 CHỖ DỄ LÀM SAI NHẤT, có mục riêng: kiểm dấu phải nằm TRONG khoá ghi. Kiểm ở
 ngoài rồi mới vào khoá là đúng lỗi A4 một lần nữa — hai người cùng bấm Lưu sẽ
 CÙNG thấy dấu khớp, rồi lần lượt ghi đè nhau.
==========================================================================
"""
import io
import json
import os
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import (GOC_TM, MayChuTam, Khach,        # noqa: E402
                          cau_hinh_tam, doi_trang_thai)
import web as W              # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def dat_dong_ho_canh(giay=300):
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


def dung(tm, ten):
    tmx = os.path.join(tm, ten)
    os.makedirs(tmx, exist_ok=True)
    return cau_hinh_tam(tmx), tmx


def so_tat(dd):
    """Danh sách chỉ số quy tắc đang tắt. Tệp hỏng -> None để ca thử ĐỎ chứ
       không VỠ giữa chừng."""
    try:
        with io.open(dd, encoding='utf-8-sig') as f:
            return [i for i, r in enumerate(json.load(f)['quy_tac'])
                    if r.get('bat') is False]
    except (OSError, ValueError, KeyError, TypeError):
        return None


# ==========================================================================
def ca_1_dau_phat_ra_va_doi_theo_tep(tm):
    print('\nCA 1 — dấu bản phát ra ở /api/quy-tac và ĐỔI THEO NỘI DUNG TỆP')
    print('-' * 74)
    dd, tmx = dung(tm, 'b1')
    with MayChuTam(dd) as (k, _):
        ma, d = k.js('/api/quy-tac')
        d1 = (d or {}).get('dau')
        kiem(ma == 200 and isinstance(d1, str) and len(d1) >= 8,
             f'/api/quy-tac phát dấu bản — {d1!r}')

        ma, d = k.js('/api/quy-tac')
        kiem((d or {}).get('dau') == d1,
             'Đọc lại mà tệp không đổi thì dấu Y NGUYÊN (không phải mã ngẫu nhiên)')

        ma, kq = k.js('/api/luu-quy-tac', {'tat': [1]})
        kiem(ma == 200, f'Lưu được — {ma}')
        d2 = (kq or {}).get('dau')
        kiem(isinstance(d2, str) and d2 != d1,
             f'Lưu xong thì dấu ĐỔI, và trả về ngay trong câu trả lời — {d2!r}')
        kiem(k.js('/api/quy-tac')[1]['dau'] == d2,
             'Dấu trả về khớp với dấu đọc lại từ /api/quy-tac')

        # ĐÂY là lý do băm NỘI DUNG chứ không dùng mã ngẫu nhiên trong bộ nhớ:
        # thầy cô được quyền sửa cauhinh.json bằng Notepad, và đó là đường dùng
        # CHÍNH của dự án.
        with io.open(dd, encoding='utf-8-sig') as f:
            cfg = json.load(f)
        cfg['thong_tin']['tuan'] = 'TUẦN SỬA TAY BẰNG NOTEPAD'
        with io.open(dd, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False)
        d3 = k.js('/api/quy-tac')[1]['dau']
        kiem(d3 != d2,
             f'SỬA TAY bằng Notepad cũng làm dấu đổi — {d2[:8]}… -> {d3[:8]}…. '
             f'Mã ngẫu nhiên giữ trong bộ nhớ sẽ KHÔNG biết lần sửa này')


# ==========================================================================
def ca_2_hai_nguoi_de_nhau(tm):
    print('\nCA 2 — QĐ 7: A không được đè mất bản sửa của B')
    print('-' * 74)
    dd, tmx = dung(tm, 'b2')
    with MayChuTam(dd, dang_nhap=False) as (k0, (dia, cong)):
        kA, kB = Khach(cong), Khach(cong)
        kA.dang_nhap()
        kB.dang_nhap()

        # A mở màn hình Quy tắc -> giữ dấu CŨ
        dau_cua_A = kA.js('/api/quy-tac')[1]['dau']
        kiem(bool(dau_cua_A), 'A mở danh sách, giữ dấu bản lúc đó')

        # B sửa và lưu
        ma, _ = kB.js('/api/luu-quy-tac', {'tat': [2, 3]})
        kiem(ma == 200 and so_tat(dd) == [2, 3],
             f'B bấm Lưu, tệp thành {so_tat(dd)}')

        # A bấm Lưu theo danh sách CŨ -> phải bị chặn
        ma, t = kA.js('/api/luu-quy-tac', {'tat': [5]}, dau=dau_cua_A)
        kiem(ma == 409,
             f'A bấm Lưu bằng dấu CŨ -> 409, không phải 200 hay 400 — {ma}')
        cau = (t or {}).get('loi', '')
        kiem('đã đổi' in cau and 'Tải lại danh sách' in cau,
             f'Câu trả lời nói rõ chuyện gì và bấm gì tiếp — {cau[:70]!r}')
        kiem(so_tat(dd) == [2, 3],
             f'Và tệp VẪN là bản của B, không suy suyển — {so_tat(dd)}')

        # A tải lại rồi lưu -> được
        dau_moi = kA.js('/api/quy-tac')[1]['dau']
        ma, _ = kA.js('/api/luu-quy-tac', {'tat': [5]}, dau=dau_moi)
        kiem(ma == 200 and so_tat(dd) == [5],
             f'A tải lại danh sách rồi Lưu thì được — {ma}, {so_tat(dd)}')

        # Lưu hai lần liên tiếp: dấu trả về cho phép lưu tiếp, khỏi tải lại
        ma, kq = kA.js('/api/luu-quy-tac', {'tat': [6]})
        kiem(ma == 200, 'Và lưu tiếp lần nữa cũng được (dấu mới trả về ngay)')


# ==========================================================================
def ca_3_thieu_dau_thi_tu_choi(tm):
    print('\nCA 3 — thiếu "dau" thì TỪ CHỐI GHI, không ghi bừa')
    print('-' * 74)
    dd, tmx = dung(tm, 'b3')
    with MayChuTam(dd) as (k, _):
        truoc = so_tat(dd)
        # dau=False -> KHÔNG gửi khoá "dau" nào cả (xem Khach.yeu_cau)
        ma, t = k.js('/api/luu-quy-tac', {'tat': [7]}, dau=False)
        kiem(ma == 400,
             f'Thiếu "dau" -> 400 (yêu cầu sai), không phải 409 — {ma}')
        kiem('dau' in str(t), f'Câu lỗi chỉ đích danh khoá thiếu — {str(t)[:70]}')
        kiem(so_tat(dd) == truoc,
             f'Và tệp KHÔNG bị đụng — {so_tat(dd)} vs {truoc}')

        ma, t = k.js('/api/luu-quy-tac', {'tat': [7]}, dau='sai-be-bet')
        kiem(ma == 409, f'Dấu sai bét -> 409 — {ma}')
        kiem(so_tat(dd) == truoc, 'Tệp vẫn không bị đụng')


# ==========================================================================
def ca_4_kiem_dau_nam_trong_khoa_ghi(tm):
    print('\nCA 4 — kiểm dấu nằm TRONG khoá ghi (đúng lỗi A4, lần thứ hai)')
    print('-' * 74)
    dd, tmx = dung(tm, 'b4')
    SO = 12
    with MayChuTam(dd, dang_nhap=False) as (k0, (dia, cong)):
        k0.dang_nhap()
        dau_chung = k0.js('/api/quy-tac')[1]['dau']
        kiem(bool(dau_chung), 'Mười hai người cùng cầm MỘT dấu bản')

        ma = [None] * SO
        vao_cuoc = threading.Barrier(SO)

        def ban(i):
            kh = Khach(cong)
            try:
                kh.dang_nhap()
                vao_cuoc.wait(timeout=60)
                ma[i] = kh.js('/api/luu-quy-tac',
                              {'tat': [i]}, dau=dau_chung)[0]
            except Exception as e:                 # đỏ, không vỡ
                ma[i] = repr(e)[:40]

        ls = [threading.Thread(target=ban, args=(i,), daemon=True)
              for i in range(SO)]
        [t.start() for t in ls]
        [t.join(timeout=120) for t in ls]

        so_200 = sum(1 for m in ma if m == 200)
        so_409 = sum(1 for m in ma if m == 409)
        kiem(so_200 + so_409 == SO,
             f'Cả {SO} yêu cầu đều được trả lời — 200:{so_200} 409:{so_409} '
             f'khác:{[m for m in ma if m not in (200, 409)]}')
        # ĐÂY là mục đáng giá: kiểm dấu ở NGOÀI khoá ghi thì cả 12 cùng thấy
        # dấu khớp rồi lần lượt ghi đè nhau -> 12 lần 200, mất 11 bản sửa.
        kiem(so_200 == 1,
             f'ĐÚNG MỘT người ghi được, {SO - 1} người còn lại bị 409 — '
             f'lọt {so_200}')
        kiem(so_tat(dd) is not None and len(so_tat(dd)) == 1,
             f'Và tệp mang đúng một thay đổi, không lẫn — {so_tat(dd)}')


# ==========================================================================
def ca_5_dau_ket_qua_xep(tm):
    print('\nCA 5 — QĐ 4: kết quả xếp có dấu bản, và DÁN TÊN người xếp')
    print('-' * 74)
    dd, tmx = dung(tm, 'b5')
    with MayChuTam(dd) as (k, _):
        _, t0 = k.js('/api/trang-thai?tu=0')
        kiem(t0.get('dau') is None,
             f'Chưa xếp lần nào: dấu là None — {t0.get("dau")!r}')
        # NGOẠI LỆ CÓ CHỦ Ý: chưa có dấu thì cho tải (tệp của lượt chạy trước).
        ma, _ = k.get('/api/tai-ve')
        kiem(ma in (200, 404),
             f'Và tải KHÔNG bị chặn bằng 409 — {ma} (404 = chưa có tệp, chấp nhận)')

        kiem(k.js('/api/xep', {'tat': []})[0] == 200, 'Bấm Xếp')
        t = doi_trang_thai(k)
        kiem(bool(t.get('dau')), f'Xếp xong sinh dấu mới — {t.get("dau")!r}')
        kiem(t.get('nguoi') == MayChuTam.TEN,
             f'Và DÁN TÊN người xếp — {t.get("nguoi")!r}')

        ma, _ = k.get_nhi_phan('/api/tai-ve?dau=' + t['dau'])
        kiem(ma == 200, f'Dấu khớp thì tải được — {ma}')
        ma, than = k.get('/api/tai-ve?dau=sai-be-bet')
        kiem(ma == 409, f'Dấu lệch thì CHẶN bằng 409 — {ma}')
        kiem(MayChuTam.TEN in than and 'xem lại trước khi tải' in than,
             f'Câu chặn nhắc TÊN người vừa xếp đè — {than[:80]!r}')
        ma, than = k.get('/api/tai-ve')
        kiem(ma == 409,
             f'Không gửi dấu, trong khi máy chủ ĐÃ có dấu -> cũng chặn — {ma}')
        ma, than = k.get('/api/tai-web?dau=sai-be-bet')
        kiem(ma == 409 and 'text/plain' not in than,
             f'/api/tai-web cũng chặn — {ma}')

        # Xếp lượt thứ hai -> dấu phải đổi, dấu cũ hết dùng được
        dau_cu = t['dau']
        kiem(k.js('/api/xep', {'tat': []})[0] == 200, 'Bấm Xếp lượt thứ hai')
        t2 = doi_trang_thai(k)
        kiem(t2.get('dau') and t2['dau'] != dau_cu,
             f'Lượt mới sinh dấu KHÁC — {dau_cu[:8]}… -> {str(t2.get("dau"))[:8]}…')
        kiem(k.get('/api/tai-ve?dau=' + dau_cu)[0] == 409,
             'Dấu của lượt CŨ không tải được nữa — đúng lỗ QĐ 4 định bịt')


# ==========================================================================
def ca_6_giao_dien_du_manh(tm):
    print('\nCA 6 — giao diện có đủ chỗ hiện tên và nút Tải lại danh sách')
    print('-' * 74)
    html = io.open(os.path.join(GOC_TM, 'web', 'index.html'),
                   encoding='utf-8').read()
    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    thieu = [i for i in ('chu-nguoi-xep', 'nut-tai-lai-ds')
             if f'id="{i}"' not in html]
    kiem(not thieu, f'HTML có đủ hai mảnh mới — thiếu {thieu}')
    kiem("dau: dauCauHinh" in js,
         'app.js gửi dấu bản của cauhinh.json khi bấm Lưu')
    kiem("r.ma === 409" in js,
         'và xử riêng mã 409 (không trộn vào nhánh lỗi chung)')
    kiem("dauKetQua" in js and "'?dau='" in js,
         'Hai nút tải đính dấu bản của lượt xếp đang hiện')


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ 2C — DẤU BẢN, CHỐNG MẤT BẢN SỬA')
    print('=' * 74)
    dat_dong_ho_canh(300)
    import tempfile
    with tempfile.TemporaryDirectory() as tm:
        ca_1_dau_phat_ra_va_doi_theo_tep(tm)
        ca_2_hai_nguoi_de_nhau(tm)
        ca_3_thieu_dau_thi_tu_choi(tm)
        ca_4_kiem_dau_nam_trong_khoa_ghi(tm)
        ca_5_dau_ket_qua_xep(tm)
        ca_6_giao_dien_du_manh(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

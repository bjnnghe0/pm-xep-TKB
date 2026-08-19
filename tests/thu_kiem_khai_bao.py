#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: CHƯƠNG TRÌNH PHẢI TỰ BẮT LỖI KHAI SAI THỨ / TIẾT
--------------------------------------------------------------------------
 Chạy:  python tests/thu_kiem_khai_bao.py

 Có hai cách ghi tiết, lệch nhau đúng một khoảng:
     "tiet_trong_buoi"  thứ tự trong buổi, 1..5
     "tiet"             số hiệu tiết in trên TKB, 6..10
 Ghi nhầm khoá này sang khoá kia thì giá trị rơi ra ngoài miền hợp lệ.
 Trước đây chương trình LẶNG LẼ bỏ qua -> quy tắc không cấm gì mà vẫn báo
 ĐẠT. Giờ phải DỪNG hẳn kèm thông báo chỉ ra khoá đáng lẽ phải dùng.

 Bảng 4 tổ hợp cần khẳng định:
     tiet_trong_buoi=[4,5]   -> chạy, cấm vị trí [3, 4]
     tiet=[9,10]             -> chạy, cấm vị trí [3, 4]   (y hệt)
     tiet=[4,5]              -> DỪNG, gợi ý dùng "tiet_trong_buoi"
     tiet_trong_buoi=[9,10]  -> DỪNG, gợi ý dùng "tiet"

 Khoá "thu" cũng cùng một kiểu bẫy: ghi theo SỐ HIỆU THỨ (Thứ 2 là 2),
 không phải đếm từ 1. Ghi "thu": [1] hay [7] (chưa khai trong cac_thu)
 trước đây cũng bị lặng lẽ bỏ qua.
==========================================================================
"""
import copy
import io
import os
import sys

GOC_TM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_TM)

import xep_tkb as X          # noqa: E402
import quy_tac as QT         # noqa: E402

GOC = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
NEN = X.BaiToan(copy.deepcopy(GOC))       # bài toán nền, dùng để dựng quy tắc lẻ

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def bat_loi(ham):
    """Chạy ham(), trả về thông báo SystemExit nếu có, None nếu chạy trót lọt."""
    try:
        ham()
        return None
    except SystemExit as e:
        return str(e)


def dung_quy_tac(r):
    return QT.DANH_MUC[r['loai']](r, NEN)


def dung_bai_toan(r):
    cfg = copy.deepcopy(GOC)
    cfg['quy_tac'].append(r)
    X.BaiToan(cfg)


GHI_CHU = 'Sử cô Ngọc Uyên không xếp 2 tiết cuối buổi'


def qt(khoa, gt, loai='khong_xep_tiet'):
    return {'loai': loai, 'ghi_chu': GHI_CHU,
            'loc': {'gv': 'N.Uyên', 'nhom_mon': 'Sử'}, khoa: gt}


# --------------------------------------------------------------------------
def ca_1_hai_to_hop_dung():
    print('\nCA 1 — hai cách ghi ĐÚNG vẫn chạy và cho cùng một kết quả')
    print('-' * 74)
    for khoa, gt in (('tiet_trong_buoi', [4, 5]), ('tiet', [9, 10])):
        loi = bat_loi(lambda: dung_quy_tac(qt(khoa, gt)))
        kiem(loi is None, f'"{khoa}": {gt} — không bị chặn oan')
        if loi is None:
            v = sorted(dung_quy_tac(qt(khoa, gt)).tap_tiet())
            kiem(v == [3, 4], f'"{khoa}": {gt} — cấm đúng vị trí [3, 4], được {v}')
    kiem(sorted(dung_quy_tac(qt('tiet_trong_buoi', [4, 5])).tap_tiet())
         == sorted(dung_quy_tac(qt('tiet', [9, 10])).tap_tiet()),
         'Hai cách ghi cho ra CÙNG một tập tiết bị cấm')
    kiem(bat_loi(lambda: dung_bai_toan(qt('tiet', [9, 10]))) is None,
         'Dựng nguyên bài toán với quy tắc đúng: chạy bình thường')


def ca_2_hai_to_hop_sai():
    print('\nCA 2 — hai cách ghi SAI phải DỪNG, kèm gợi ý khoá thay thế')
    print('-' * 74)
    for khoa, gt, khoa_dung in (('tiet', [4, 5], 'tiet_trong_buoi'),
                                ('tiet_trong_buoi', [9, 10], 'tiet')):
        loi = bat_loi(lambda: dung_quy_tac(qt(khoa, gt)))
        kiem(loi is not None, f'"{khoa}": {gt} — DỪNG chứ không lặng lẽ bỏ qua')
        if not loi:
            continue
        kiem(GHI_CHU in loi, f'  nêu ghi_chu của quy tắc sai')
        kiem(f'"{khoa}"' in loi, f'  nêu đúng khoá sai: "{khoa}"')
        kiem(all(str(x) in loi for x in gt), f'  nêu giá trị sai: {gt}')
        kiem('Miền hợp lệ' in loi, '  nêu miền hợp lệ hiện tại')
        kiem(f'"{khoa_dung}"' in loi and 'Có phải bạn định dùng' in loi,
             f'  gợi ý đúng khoá thay thế: "{khoa_dung}"')

    print('  -- bắt lỗi NGAY lúc dựng bài toán, không đợi tới lúc chấm điểm --')
    for loai in ('khong_xep_tiet', 'chi_xep_tiet', 'uu_tien_o'):
        r = qt('tiet_trong_buoi', [9, 10], loai=loai)
        if loai == 'uu_tien_o':
            r['diem'] = 3        # chỉ loại mềm mới nhận khoá "diem"
        loi = bat_loi(lambda: dung_bai_toan(r))
        kiem(loi is not None and 'Khai báo sai' in loi,
             f'{loai}: BaiToan() dừng ngay khi dựng quy tắc')


def ca_3_khong_xep_o():
    print('\nCA 3 — khoá "o" của khong_xep_o cũng được kiểm')
    print('-' * 74)
    def o(cap):
        return {'loai': 'khong_xep_o', 'ghi_chu': 'Thầy Nam bận họp',
                'loc': {'gv': 'H.Nam'}, 'o': cap}

    kiem(bat_loi(lambda: dung_quy_tac(o([[4, 6], [4, 7]]))) is None,
         'Ô đúng [[4, 6], [4, 7]] — chạy bình thường')
    kiem(sorted(dung_quy_tac(o([[4, 6], [4, 7]]))._tap_o()) == [(2, 0), (2, 1)],
         'Ô đúng quy ra đúng (ngày 2, vị trí 0) và (ngày 2, vị trí 1)')

    loi = bat_loi(lambda: dung_quy_tac(o([[4, 4]])))
    kiem(loi is not None, 'Tiết 4 (không có trong buổi chiều) — DỪNG')
    kiem(loi and 'phần TIẾT' in loi and 'tiết 9' in loi,
         '  gợi ý quy đổi thẳng: "tiết thứ 4 của buổi" phải ghi là tiết 9')

    loi = bat_loi(lambda: dung_quy_tac(o([[8, 6]])))
    kiem(loi is not None and 'phần THỨ' in loi, 'Thứ 8 không có — DỪNG')
    kiem(loi and '2, 3, 4, 5, 6' in loi, '  liệt kê các thứ hợp lệ')

    loi = bat_loi(lambda: dung_quy_tac(o([[4, 6, 7]])))
    kiem(loi is not None and '[thứ, tiết]' in loi,
         'Ô ghi sai dạng [4, 6, 7] — DỪNG, nhắc đúng dạng [thứ, tiết]')


def ca_4_khoa_thu():
    print('\nCA 4 — khoá "thu" cũng được kiểm')
    print('-' * 74)

    def r_thu(loai, gt, **them):
        r = {'loai': loai, 'ghi_chu': 'Vật lý 12B1, 12B2 chỉ Thứ 2 hoặc Thứ 3',
             'loc': {'mon': 'Vật lý'}, 'thu': gt}
        r.update(them)
        return r

    kiem(bat_loi(lambda: dung_quy_tac(r_thu('chi_xep_thu', [2, 3]))) is None,
         '"thu": [2, 3] đúng — chạy bình thường')
    kiem(sorted(dung_quy_tac(r_thu('chi_xep_thu', [2, 3])).tap_ngay()) == [0, 1],
         '"thu": [2, 3] quy ra đúng chỉ số ngày [0, 1]')
    kiem(bat_loi(lambda: dung_bai_toan(
        r_thu('khong_xep_thu', [5], loc={'gv': 'Đ.Duy'}))) is None,
         'Dựng nguyên bài toán với "thu" đúng: chạy bình thường')

    loi = bat_loi(lambda: dung_quy_tac(r_thu('chi_xep_thu', [1, 2])))
    kiem(loi is not None, '"thu": [1] (đếm từ 1) — DỪNG chứ không lặng lẽ bỏ qua')
    kiem(loi and '2, 3, 4, 5, 6' in loi, '  nêu miền hợp lệ 2, 3, 4, 5, 6')
    kiem(loi and 'KHÔNG phải đếm từ 1' in loi,
         '  nói thẳng: thu ghi theo số hiệu thứ, không phải đếm từ 1')
    kiem(loi and 'phải ghi là 2' in loi,
         '  quy đổi giúp: ngày học thứ 1 của tuần chính là Thứ 2')

    loi = bat_loi(lambda: dung_quy_tac(r_thu('khong_xep_thu', [7])))
    kiem(loi is not None, '"thu": [7] khi cac_thu chưa có Thứ 7 — DỪNG')
    kiem(loi and 'cac_thu' in loi and 'thêm 7 vào đó' in loi,
         '  nhắc phải thêm 7 vào khung_gio.cac_thu trước')

    loi = bat_loi(lambda: dung_bai_toan(
        {'loai': 'co_dinh', 'ghi_chu': 'Ghim SHCN 12B1',
         'loc': {'mon': 'SHCN', 'lop': '12B1'}, 'thu': 1, 'tiet': 10}))
    kiem(loi is not None and 'KHÔNG phải đếm từ 1' in loi,
         'co_dinh ghi "thu": 1 dạng số lẻ — DỪNG')

    loi = bat_loi(lambda: dung_quy_tac(
        {'loai': 'khong_xep_o', 'ghi_chu': 'Thầy Nam bận họp',
         'loc': {'gv': 'H.Nam'}, 'o': [[1, 6]]}))
    kiem(loi is not None and 'phần THỨ' in loi and 'KHÔNG phải đếm từ 1' in loi,
         'khong_xep_o ghi "o": [[1, 6]] — DỪNG, cùng một thông báo')


def ca_5_khong_hoi_quy():
    print('\nCA 5 — không hồi quy')
    print('-' * 74)
    kiem(bat_loi(lambda: X.BaiToan(copy.deepcopy(GOC))) is None,
         'cauhinh.json thật vẫn dựng được, không báo lỗi oan')
    cd = {'loai': 'co_dinh', 'ghi_chu': 'Ghim SHCN 12B1 Thứ 6 tiết 10',
          'loc': {'mon': 'SHCN', 'lop': '12B1'}, 'thu': 6, 'tiet': 10}
    kiem(bat_loi(lambda: dung_bai_toan(cd)) is None,
         'co_dinh ghi "tiet" là số lẻ (không phải danh sách) vẫn chạy')
    cd_sai = dict(cd, tiet=4)
    loi = bat_loi(lambda: dung_bai_toan(cd_sai))
    kiem(loi is not None and 'tiet_trong_buoi' in loi,
         'co_dinh ghi "tiet": 4 — DỪNG, gợi ý "tiet_trong_buoi"')


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ KIỂM TRA MIỀN GIÁ TRỊ CỦA KHOÁ THỨ / TIẾT')
    print('=' * 74)
    print(f'  Khung giờ đang dùng: buổi {NEN.buoi}, tiết {NEN.cac_tiet} '
          f'-> tiet_trong_buoi 1..{NEN.SO_TIET}')
    ca_1_hai_to_hop_dung()
    ca_2_hai_to_hop_sai()
    ca_3_khong_xep_o()
    ca_4_khoa_thu()
    ca_5_khong_hoi_quy()
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: KHOÁ "tru" TRONG BỘ LỌC
--------------------------------------------------------------------------
 Chạy:  python tests/thu_loc_tru.py

 "tru" diễn tả "áp cho tất cả TRỪ trường hợp này":
     "loc": { "nhom_mon": "SHCN", "tru": { "gv": "N.Uyên" } }
 Cách này an toàn hơn liệt kê tay các lớp còn lại: thêm lớp mới thì lớp
 đó tự động bị ràng buộc, không rơi vào cảnh "không cấm gì mà báo ĐẠT".

 Có HAI chỗ lọc riêng biệt trong mã, cả hai đều phải hiểu "tru":
     quy_tac.QuyTac.khop()     dùng cho mọi loại quy tắc
     xep_tkb.BaiToan._cum_cua()  bản cài riêng của gom_tiet, chạy trước
                                 khi có đối tượng Cum nên không gọi khop()
==========================================================================
"""
import copy
import os
import sys

GOC_TM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_TM)

import xep_tkb as X          # noqa: E402
import quy_tac as QT         # noqa: E402

GOC = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
NEN = X.BaiToan(copy.deepcopy(GOC))

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def bat_loi(ham):
    try:
        ham()
        return None
    except SystemExit as e:
        return str(e)


def qt(loc, loai='chi_xep_tiet', **them):
    r = {'loai': loai, 'ghi_chu': 'SHCN ở tiết cuối buổi', 'loc': loc,
         'tiet_trong_buoi': [5]}
    r.update(them)
    return QT.DANH_MUC[loai](r, NEN)


def lop_bi_ap(loc):
    return sorted(c.lop for c in qt(loc).cac_cum())


def bai_toan_voi(r):
    cfg = copy.deepcopy(GOC)
    cfg['quy_tac'].append(r)
    return X.BaiToan(cfg)


# --------------------------------------------------------------------------
def ca_1_loai_dung_cum():
    print('\nCA 1 — "tru" loại đúng cụm cần loại, không đụng cụm khác')
    print('-' * 74)
    het = lop_bi_ap({'nhom_mon': 'SHCN'})
    kiem(het == ['12B1', '12B2', '12B3', '12B4', '12B5', '12B6'],
         f'Không có "tru": áp cho cả 6 lớp — {het}')

    con = lop_bi_ap({'nhom_mon': 'SHCN', 'tru': {'gv': 'N.Uyên'}})
    kiem(con == ['12B1', '12B2', '12B3', '12B4', '12B5'],
         f'"tru" theo gv: rụng đúng 12B6 (lớp cô N.Uyên) — {con}')
    kiem(len(het) - len(con) == 1, 'Chỉ rụng đúng MỘT cụm, không rụng thừa')

    kiem(lop_bi_ap({'nhom_mon': 'SHCN', 'tru': {'lop': ['12B1', '12B2']}})
         == ['12B3', '12B4', '12B5', '12B6'], '"tru" theo lop, nhận danh sách')

    # cụm ngoài bộ lọc chính thì "tru" không được đụng tới
    tat_ca = len([c for c in NEN.cac_cum if not c.la_trong])
    v = len(qt({'tru': {'gv': 'N.Uyên'}}).cac_cum())
    n_uyen = len([c for c in NEN.cac_cum if c.gv == 'N.Uyên'])
    kiem(v == tat_ca - n_uyen,
         f'"loc" rỗng + "tru" gv: giữ {v} = {tat_ca} - {n_uyen} cụm của cô N.Uyên')

    cd = lop_bi_ap({'nhom_mon': 'Toán', 'tru': {'la_chuyen_de': True}})
    kiem(len(qt({'nhom_mon': 'Toán', 'tru': {'la_chuyen_de': True}}).cac_cum())
         == len([c for c in NEN.cac_cum if c.nhom == 'Toán' and not c.la_cd]),
         '"tru" theo la_chuyen_de: bỏ hết cụm chuyên đề Toán')

    r = {'loai': 'khac_ngay', 'ghi_chu': 'thử a/b',
         'a': {'nhom_mon': 'Sử', 'tru': {'gv': 'N.Uyên'}}, 'b': {'gv': 'M.Hùng'}}
    q = QT.DANH_MUC['khac_ngay'](r, NEN)
    ben_a = sorted({c.gv for c in NEN.cac_cum if 'a' in q._ben(c)})
    kiem(ben_a == ['N.Xuân'], f'"tru" dùng được trong bộ lọc "a" — còn {ben_a}')


def ca_2_tru_sai_thi_dung():
    print('\nCA 2 — "tru" khai sai phải DỪNG, không được lặng lẽ loại hết')
    print('-' * 74)
    for gt, ten in (({}, '"tru": {} (rỗng)'), ([], '"tru": [] (không phải dict)'),
                    ('N.Uyên', '"tru": "N.Uyên" (chuỗi trần)')):
        loi = bat_loi(lambda: qt({'nhom_mon': 'SHCN', 'tru': gt}))
        kiem(loi is not None, f'{ten} — DỪNG')
        kiem(loi and 'loại trừ TẤT CẢ' in loi, '  nói rõ hậu quả: loại trừ tất cả')
        kiem(loi and '"bat": false' in loi, '  chỉ cách tắt quy tắc cho đúng')

    loi = bat_loi(lambda: qt({'nhom_mon': 'SHCN', 'tru': {'giao_vien': 'N.Uyên'}}))
    kiem(loi is not None and 'giao_vien' in loi,
         '"tru" có khoá lạ (giao_vien) — DỪNG, nêu đích danh khoá lạ')
    kiem(loi and 'mon / nhom_mon / gv / lop' in loi, '  liệt kê các khoá dùng được')

    loi = bat_loi(lambda: bai_toan_voi(
        {'loai': 'chi_xep_tiet', 'ghi_chu': 'SHCN tiết cuối',
         'loc': {'nhom_mon': 'SHCN', 'tru': {}}, 'tiet_trong_buoi': [5]}))
    kiem(loi is not None, 'Lỗi lộ ra NGAY lúc dựng BaiToan')


def ca_3_gom_tiet_hieu_tru():
    print('\nCA 3 — gom_tiet (bộ lọc cài riêng trong xep_tkb) cũng hiểu "tru"')
    print('-' * 74)
    bt = bai_toan_voi({'loai': 'gom_tiet', 'ghi_chu': 'Tách Hoá 2 buổi, trừ 12B1',
                       'loc': {'mon': 'Hoá học', 'tru': {'lop': '12B1'}},
                       'cum': [1, 1]})
    kiem(bt.mong_doi[('12B1', 'Hoá học')] == [2],
         f'12B1 bị "tru" nên giữ cách gom cũ [2] — {bt.mong_doi[("12B1", "Hoá học")]}')
    khac = {lop: bt.mong_doi[(lop, 'Hoá học')] for lop in
            ('12B2', '12B3', '12B4', '12B5', '12B6')}
    kiem(all(v == [1, 1] for v in khac.values()),
         f'5 lớp còn lại tách thành [1, 1] — {khac}')

    bt2 = bai_toan_voi({'loai': 'gom_tiet', 'ghi_chu': 'Tách Hoá 2 buổi',
                        'loc': {'mon': 'Hoá học'}, 'cum': [1, 1]})
    kiem(bt2.mong_doi[('12B1', 'Hoá học')] == [1, 1],
         'Bỏ "tru" thì 12B1 cũng tách — chứng tỏ khác biệt là do "tru"')

    loi = bat_loi(lambda: bai_toan_voi(
        {'loai': 'gom_tiet', 'ghi_chu': 'Tách Hoá 2 buổi',
         'loc': {'mon': 'Hoá học', 'tru': {}}, 'cum': [1, 1]}))
    kiem(loi is not None and 'loại trừ TẤT CẢ' in loi,
         'gom_tiet với "tru" rỗng cũng DỪNG, cùng một thông báo')


def ca_4_khong_hoi_quy():
    print('\nCA 4 — không hồi quy')
    print('-' * 74)
    kiem(bat_loi(lambda: X.BaiToan(copy.deepcopy(GOC))) is None,
         'cauhinh.json thật vẫn dựng được')
    kiem(lop_bi_ap({'nhom_mon': 'SHCN'})
         == ['12B1', '12B2', '12B3', '12B4', '12B5', '12B6'],
         'Bộ lọc không có "tru" hoạt động y như cũ')


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ KHOÁ "tru" TRONG BỘ LỌC')
    print('=' * 74)
    ca_1_loai_dung_cum()
    ca_2_tru_sai_thi_dung()
    ca_3_gom_tiet_hieu_tru()
    ca_4_khong_hoi_quy()
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: MỘT BỘ LỌC DUY NHẤT CHO CẢ HAI CHỖ
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_gop_bo_loc.py

 Trước đây có HAI bản cài bộ lọc:
   quy_tac.QuyTac.khop()        dùng cho mọi loại quy tắc  — hiểu la_chuyen_de
   xep_tkb.BaiToan._cum_cua()   bản riêng của gom_tiet     — KHÔNG hiểu
 nên cùng một "loc" cho hai kết quả khác nhau, im lặng. Đo được: bộ lọc
 {"la_chuyen_de": true} khớp 24 cụm chuyên đề ở chỗ 1, nhưng ở chỗ 2 lại
 đụng 48 cặp (lớp, môn) thuộc 9 môn KHÔNG phải chuyên đề.

 Nay cả hai cùng gọi quy_tac.khop_loc(dk, mon, nhom, gv, lop, la_cd) —
 hàm thuần, nhận tham số RỜI vì gom_tiet chạy trong _tao_cum(), lúc chưa
 có đối tượng Cum nào.
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
DM = GOC['dinh_muc_mon']

# Kỳ vọng dựng TỪ dữ liệu, không viết cứng — xem ghi chú dài ở thu_loc_tru.py.
MOI_LOP = sorted(l['ten'] for l in GOC['lop'])
# Một môn THƯỜNG (không chuyên đề) được dạy ở MỌI lớp, chọn từ chính dữ liệu.
_THEO_MON = {}
for _c in NEN.cac_cum:
    if not _c.la_trong and not _c.la_cd:
        _THEO_MON.setdefault(_c.mon, set()).add(_c.lop)
MON_MOI_LOP = sorted(m for m, s in _THEO_MON.items() if s == set(MOI_LOP))

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


def qt_voi(loc, ghi_chu='thử bộ lọc'):
    return QT.DANH_MUC['chi_xep_tiet'](
        {'loai': 'chi_xep_tiet', 'ghi_chu': ghi_chu, 'loc': loc,
         'tiet_trong_buoi': [1, 2, 3, 4, 5]}, NEN)


def bt_voi(r):
    cfg = copy.deepcopy(GOC)
    cfg['quy_tac'].append(r)
    return X.BaiToan(cfg)


def doi_gom_tiet(loc, cum):
    """Những cặp (lớp, môn) bị một quy tắc gom_tiet đổi cách chia cụm."""
    goc = X.BaiToan(copy.deepcopy(GOC)).mong_doi
    moi = bt_voi({'loai': 'gom_tiet', 'ghi_chu': 'thử gom', 'loc': loc,
                  'cum': cum}).mong_doi
    return {k: (goc[k], moi[k]) for k in goc if goc[k] != moi[k]}


BO_LOC = [
    {},
    {'nhom_mon': 'SHCN'},
    {'la_chuyen_de': True},
    {'la_chuyen_de': False},
    {'mon': 'Hoá học', 'lop': ['12B1', '12B2']},
    {'gv': 'N.Uyên'},
    {'nhom_mon': 'SHCN', 'tru': {'gv': 'N.Uyên'}},
    {'nhom_mon': 'Toán', 'tru': {'la_chuyen_de': True}},
    {'tru': {'lop': '12B1', 'tru': {'mon': 'Hoá học'}}},
]


# --------------------------------------------------------------------------
def ca_1_tuong_duong():
    print('\nCA 1 — hai đường gọi cho kết quả GIỐNG HỆT trên mọi cụm')
    print('-' * 74)
    cum = [c for c in NEN.cac_cum if not c.la_trong]
    for dk in BO_LOC:
        q = qt_voi(dk)
        lech = []
        for c in cum:
            a = q.khop(c, dk)
            b = QT.khop_loc(dk, c.mon, c.nhom, c.gv, c.lop,
                            DM[c.mon].get('la_chuyen_de', False))
            if a != b:
                lech.append((c.lop, c.mon, a, b))
        kiem(not lech, f'{str(dk)[:52]:<54} 0/{len(cum)} lệch')


def ca_2_gom_tiet_hieu_la_chuyen_de():
    print('\nCA 2 — gom_tiet nay hiểu la_chuyen_de (trước đây thì không)')
    print('-' * 74)
    doi = doi_gom_tiet({'la_chuyen_de': True}, [1])
    thuong = sorted({k[1] for k in doi if not DM[k[1]].get('la_chuyen_de')})
    kiem(not thuong,
         f'"la_chuyen_de": true KHÔNG đụng môn thường — đụng {len(thuong)} môn '
         f'(trước khi gộp: 9 môn / 48 cặp)')
    kiem(len(doi) == 0, f'Tổng cộng 0 cặp bị đổi, được {len(doi)}')

    q = qt_voi({'la_chuyen_de': True})
    kiem(len(q.cac_cum()) == 24 and all(c.la_cd for c in q.cac_cum()),
         f'Cùng bộ lọc đó ở QuyTac.khop(): đúng 24 cụm và đều là chuyên đề')

    mon = MON_MOI_LOP[0]
    doi = doi_gom_tiet({'la_chuyen_de': False, 'mon': mon}, [1, 1])
    kiem(sorted({k[1] for k in doi}) == [mon] and len(doi) == len(MOI_LOP),
         f'"la_chuyen_de": false + mon "{mon}": đổi đúng {len(MOI_LOP)} lớp '
         f'môn đó — {len(doi)} cặp')


def ca_3_gom_tiet_hieu_tru_long_nhau():
    print('\nCA 3 — gom_tiet hiểu "tru" lồng nhau y như khop()')
    print('-' * 74)
    mon = MON_MOI_LOP[0]
    l1, l2 = MOI_LOP[0], MOI_LOP[1]
    loc = {'mon': mon, 'tru': {'lop': [l1, l2], 'tru': {'lop': l1}}}
    # tru loại l1+l2, nhưng tru-lồng lại kéo l1 ra khỏi diện loại
    # => rốt cuộc chỉ l2 bị loại
    doi = doi_gom_tiet(loc, [1, 1])
    lop_doi = sorted(k[0] for k in doi)
    kiem(lop_doi == [l for l in MOI_LOP if l != l2],
         f'gom_tiet: chỉ {l2} bị loại — đổi {lop_doi}')

    q = qt_voi(loc)
    lop_khop = sorted(c.lop for c in q.cac_cum())
    kiem(lop_khop == lop_doi,
         f'QuyTac.khop() cho ra ĐÚNG danh sách đó — {lop_khop}')


def ca_4_khoa_la_hai_cho_cung_thong_bao():
    print('\nCA 4 — khoá lạ ở cả hai chỗ đều DỪNG với cùng một thông báo')
    print('-' * 74)
    GC = 'quy tắc có khoá lạ'
    loc = {'nhom_mon': 'SHCN', 'giao_vien': 'N.Uyên'}

    a = bat_loi(lambda: bt_voi({'loai': 'chi_xep_tiet', 'ghi_chu': GC,
                                'loc': loc, 'tiet_trong_buoi': [5]}))
    b = bat_loi(lambda: bt_voi({'loai': 'gom_tiet', 'ghi_chu': GC,
                                'loc': loc, 'cum': [1, 1]}))
    kiem(a is not None, 'Quy tắc thường có khoá lạ — DỪNG')
    kiem(b is not None, 'gom_tiet có khoá lạ — DỪNG')
    kiem(a == b, 'Thông báo hai chỗ giống hệt nhau từng chữ')
    kiem(a and 'giao_vien' in a and 'áp cho TẤT CẢ' in a,
         '  nêu đích danh khoá lạ và hậu quả')

    loc2 = {'nhom_mon': 'SHCN', 'tru': {}}
    a = bat_loi(lambda: bt_voi({'loai': 'chi_xep_tiet', 'ghi_chu': GC,
                                'loc': loc2, 'tiet_trong_buoi': [5]}))
    b = bat_loi(lambda: bt_voi({'loai': 'gom_tiet', 'ghi_chu': GC,
                                'loc': loc2, 'cum': [1, 1]}))
    kiem(a is not None and a == b, '"tru" rỗng cũng vậy: cả hai DỪNG, cùng lời')


def ca_5_khong_hoi_quy():
    print('\nCA 5 — không hồi quy')
    print('-' * 74)
    kiem(bat_loi(lambda: X.BaiToan(copy.deepcopy(GOC))) is None,
         'cauhinh.json thật vẫn dựng được')
    md = X.BaiToan(copy.deepcopy(GOC)).mong_doi
    # So với chính dinh_muc_mon, không với [2,1] / [3] viết cứng: đổi cách gom
    # tiết trong cauhinh.json là việc hợp lệ của thầy cô, không phải hồi quy.
    lech = sorted(k for k, v in md.items()
                  if v != DM.get(k[1], {}).get('cum', v))
    kiem(not lech,
         f'Cách gom tiết khớp đúng "cum" khai trong dinh_muc_mon — lệch: {lech[:4]}')
    kiem(sorted(c.lop for c in qt_voi({'nhom_mon': 'SHCN'}).cac_cum()) == MOI_LOP,
         'Bộ lọc thường vẫn hoạt động y như cũ')


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ GỘP HAI CHỖ LỌC LÀM MỘT')
    print('=' * 74)
    ca_1_tuong_duong()
    ca_2_gom_tiet_hieu_la_chuyen_de()
    ca_3_gom_tiet_hieu_tru_long_nhau()
    ca_4_khoa_la_hai_cho_cung_thong_bao()
    ca_5_khong_hoi_quy()
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

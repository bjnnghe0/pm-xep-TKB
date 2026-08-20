#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: KHOÁ "tru" TRONG BỘ LỌC
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_loc_tru.py

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

# --------------------------------------------------------------------------
# MỌI KỲ VỌNG DƯỚI ĐÂY DỰNG TỪ cauhinh.json, KHÔNG VIẾT CỨNG.
# Bản cũ ghim thẳng ['12B1'...'12B6'] và 'N.Uyên'. Hai cái hại khác nhau:
#   · ghim danh sách lớp -> thêm một lớp là ca thử đỏ dù mã không sai gì;
#   · ghim tên giáo viên -> cô ấy nghỉ dạy thì n_gv thành 0, phép trừ hoá ra
#     "giữ nguyên tất cả", và ca thử XANH trong khi không còn kiểm gì cả.
#     Dạng thứ hai nguy hiểm hơn hẳn, nên có mục canh điều kiện tiên quyết.
MOI_LOP = sorted(l['ten'] for l in GOC['lop'])
# "SHCN" và "Sử" ở hai dòng dưới là ĐẦU VÀO của phép lọc đang thử, không phải
# kỳ vọng — cả tệp này viết ra để thử bộ lọc trên đúng hai nhóm môn đó.
# ghim-co-y: tên nhóm môn dùng làm đầu vào, không phải giá trị được khẳng định.
_SHCN = [c for c in NEN.cac_cum if c.nhom == 'SHCN']  # ghim-co-y: đầu vào
_DEM_SHCN = {}
for _c in _SHCN:
    _DEM_SHCN[_c.gv] = _DEM_SHCN.get(_c.gv, 0) + 1
# Chọn một GV dạy SHCN cho ĐÚNG MỘT lớp, để "tru" theo gv rụng đúng một cụm.
# Mọi phép lấy phần tử đều có ĐƯỜNG LÙI: dữ liệu đổi tới mức không còn chọn
# được thì mục "điều kiện tiên quyết" ở CA 1 phải báo ĐỎ, chứ bộ thử tuyệt đối
# không được VỠ ở mức module — vỡ ở đây là cả tệp không chạy được mục nào.
GV_MOT_LOP = (sorted(g for g, n in _DEM_SHCN.items() if n == 1) or [''])[0]
LOP_CUA_GV = sorted(c.lop for c in _SHCN if c.gv == GV_MOT_LOP)
LOP_CON_LAI = [l for l in MOI_LOP if l not in LOP_CUA_GV]
HAI_LOP_DAU = MOI_LOP[:2]
# Hai giáo viên khác nhau cùng dạy nhóm môn Sử, để phép "tru" trong bộ lọc "a"
# còn lại ÍT NHẤT một người — nếu không thì mục đó cũng xanh giả.
GV_SU = sorted({c.gv for c in NEN.cac_cum if c.nhom == 'Sử'})  # ghim-co-y: đầu vào

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
    # ĐIỀU KIỆN TIÊN QUYẾT: dữ liệu phải còn đủ để phép trừ nói lên điều gì đó.
    kiem(len(MOI_LOP) >= 3 and len(LOP_CUA_GV) == 1 and len(GV_SU) >= 2,
         f'Dữ liệu đủ để phân biệt: {len(MOI_LOP)} lớp, GV "{GV_MOT_LOP}" dạy '
         f'SHCN đúng {len(LOP_CUA_GV)} lớp, {len(GV_SU)} GV nhóm Sử')

    het = lop_bi_ap({'nhom_mon': 'SHCN'})
    kiem(het == MOI_LOP, f'Không có "tru": áp cho cả {len(MOI_LOP)} lớp — {het}')

    con = lop_bi_ap({'nhom_mon': 'SHCN', 'tru': {'gv': GV_MOT_LOP}})
    kiem(con == LOP_CON_LAI,
         f'"tru" theo gv: rụng đúng {LOP_CUA_GV} (lớp của {GV_MOT_LOP}) — {con}')
    kiem(len(het) - len(con) == 1, 'Chỉ rụng đúng MỘT cụm, không rụng thừa')

    kiem(lop_bi_ap({'nhom_mon': 'SHCN', 'tru': {'lop': HAI_LOP_DAU}})
         == MOI_LOP[2:], '"tru" theo lop, nhận danh sách')

    # cụm ngoài bộ lọc chính thì "tru" không được đụng tới
    tat_ca = len([c for c in NEN.cac_cum if not c.la_trong])
    v = len(qt({'tru': {'gv': GV_MOT_LOP}}).cac_cum())
    n_gv = len([c for c in NEN.cac_cum if c.gv == GV_MOT_LOP])
    kiem(n_gv > 0 and v == tat_ca - n_gv,
         f'"loc" rỗng + "tru" gv: giữ {v} = {tat_ca} - {n_gv} cụm của {GV_MOT_LOP}')

    cd = lop_bi_ap({'nhom_mon': 'Toán', 'tru': {'la_chuyen_de': True}})
    kiem(len(qt({'nhom_mon': 'Toán', 'tru': {'la_chuyen_de': True}}).cac_cum())
         == len([c for c in NEN.cac_cum if c.nhom == 'Toán' and not c.la_cd]),
         '"tru" theo la_chuyen_de: bỏ hết cụm chuyên đề Toán')

    if len(GV_SU) < 2:
        kiem(False, 'Không đủ 2 giáo viên nhóm Sử để thử "tru" trong bộ lọc "a"')
        return
    bo, con_lai = GV_SU[0], GV_SU[1:]
    r = {'loai': 'khac_ngay', 'ghi_chu': 'thử a/b',
         'a': {'nhom_mon': 'Sử', 'tru': {'gv': bo}}, 'b': {'gv': GV_SU[-1]}}
    q = QT.DANH_MUC['khac_ngay'](r, NEN)
    ben_a = sorted({c.gv for c in NEN.cac_cum if 'a' in q._ben(c)})
    kiem(ben_a == con_lai,
         f'"tru" dùng được trong bộ lọc "a": bỏ {bo}, còn {ben_a}')


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
    kiem(lop_bi_ap({'nhom_mon': 'SHCN'}) == MOI_LOP,
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chạy thử từng loại quy tắc để chắc chắn tất cả đều hoạt động.
   Dùng khi vừa thêm một loại quy tắc mới vào quy_tac.py:
       python3 tu_kiem_tra.py
"""
import copy
import json
import random
import time

import xep_tkb as X
import quy_tac as QT

GOC = X.doc_cau_hinh('cauhinh.json')

THU = [
    {"loai": "gom_tiet", "ghi_chu": "Tách Hoá 2 buổi",
     "loc": {"mon": "Hoá học"}, "cum": [1, 1]},
    {"loai": "khong_xep_o", "ghi_chu": "Thầy Nam bận Thứ 4 tiết 6,7",
     "loc": {"gv": "H.Nam"}, "o": [[4, 6], [4, 7]]},
    {"loai": "co_dinh", "ghi_chu": "SHCN 12B1 ghim Thứ 6 tiết 10",
     "loc": {"mon": "SHCN", "lop": "12B1"}, "thu": 6, "tiet": 10},
    {"loai": "toi_da_ngay_moi_tuan", "ghi_chu": "Cô Uyên ≤ 4 buổi/tuần",
     "loc": {"gv": "N.Uyên"}, "theo": "gv", "so": 4},
    {"loai": "toi_da_tiet_moi_ngay", "ghi_chu": "GV ≤ 4 tiết/buổi",
     "loc": {}, "theo": "gv", "so": 4},
    {"loai": "khong_ke_nhau", "ghi_chu": "Toán không sát Lý",
     "a": {"nhom_mon": "Toán"}, "b": {"nhom_mon": "Lý"}},
    {"loai": "cung_ngay", "ghi_chu": "CĐ Toán học đúng ngày có Toán chính",
     "a": {"mon": "Chuyên đề Toán"},
     "b": {"mon": "Toán học"}},
    {"loai": "phai_ke_nhau", "ghi_chu": "CĐ Địa phải sát Địa chính",
     "a": {"mon": "Chuyên đề Địa lí"}, "b": {"mon": "Địa lí"}},
    {"loai": "chi_xep_thu", "ghi_chu": "GDKT-PL chỉ Thứ 4, 5, 6",
     "loc": {"mon": "GDKT-PL"}, "thu": [4, 5, 6]},
    {"loai": "khong_xep_tiet", "ghi_chu": "HĐTN không vào tiết đầu buổi",
     "loc": {"nhom_mon": "HĐTN"}, "tiet_trong_buoi": [1]},
    {"loai": "uu_tien_o", "ghi_chu": "Ưu tiên Toán/Văn 2 tiết đầu",
     "loc": {"nhom_mon": ["Toán", "Văn"]}, "tiet_trong_buoi": [1, 2],
     "diem": 3},
]


def chay(cfg, so_lan=60):
    bt = X.BaiToan(cfg)
    tot, diem = None, None
    t0 = time.time()
    for i in range(so_lan):
        if time.time() - t0 > 25:
            break
        pa = X.BoGiai(bt, random.Random(2027 + i), 30000, 2.0).giai()
        if pa is None:
            continue
        _, loi = X.hau_kiem(bt, pa)
        if loi:
            continue
        d = X.cham_diem(bt, pa)
        if diem is None or d > diem:
            diem, tot = d, pa
    return bt, tot, diem


print('Các loại quy tắc đã đăng ký:', len(QT.DANH_MUC))
print('=' * 68)

bt, pa, d = chay(copy.deepcopy(GOC))
print(f'{"CƠ SỞ (không thêm gì)":<42} {"OK" if pa else "HỎNG":<6} điểm={d}')

for r in THU:
    cfg = copy.deepcopy(GOC)
    cfg['quy_tac'].append(r)
    try:
        bt, pa, d = chay(cfg)
        if pa is None:
            kq, ghi = 'KHÔNG XẾP ĐƯỢC', ''
        else:
            bc, loi = X.hau_kiem(bt, pa)
            dong = [x for x in bc if r['ghi_chu'] in x[1]]
            kq = 'OK' if loi == 0 else 'CÒN LỖI'
            ghi = f'điểm={d}' + (f' | {dong[0][0]}' if dong else '')
    except SystemExit as e:
        kq, ghi = 'CHẶN HẾT Ô', str(e)[:40]
    print(f'{r["loai"] + " — " + r["ghi_chu"]:<42.42} {kq:<16} {ghi}')

print('=' * 68)

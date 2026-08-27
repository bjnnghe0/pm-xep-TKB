#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Chạy thử từng loại quy tắc để chắc chắn tất cả đều hoạt động.
   Dùng khi vừa thêm một loại quy tắc mới vào quy_tac.py:
       python3 -B tu_kiem_tra.py

   ┌──────────────────────────────────────────────────────────────────────┐
   │ MÃ THOÁT LÀ PHÁN QUYẾT. 0 = mọi quy tắc thử đều ĐẠT; khác 0 = có     │
   │ chuyện, và dòng cuối nói rõ chuyện gì.                               │
   │                                                                      │
   │ Trước 27/8/2026 tệp này **LUÔN THOÁT 0** — không `sys.exit`, không   │
   │ dòng "Tổng", không một phép khẳng định nào. Đo được: đổi `"gv":      │
   │ "H.Nam"` thành một tên KHÔNG CÓ THẬT thì khác biệt duy nhất là       │
   │ `điểm=-46` thành `điểm=-49`, cả hai đều in `OK … | ĐẠT`, cả hai      │
   │ đều thoát 0. Mà "Điều cấm" của CLAUDE.md lại bảo *đừng báo xong khi  │
   │ chưa chạy sạch tu_kiem_tra.py* — không có định nghĩa máy đọc được    │
   │ của chữ "sạch" thì câu ấy chỉ là một lời nhắc.                       │
   │                                                                      │
   │ ĐIỂM MỀM KHÔNG PHẢI PHÁN QUYẾT và không được biến thành cổng.        │
   │ Nó là tiêu chí SO SÁNH giữa các phương án, không phải ranh giới      │
   │ đúng/sai. Phán quyết chỉ hỏi: có quy tắc nào HỎNG không.             │
   └──────────────────────────────────────────────────────────────────────┘
"""
import copy
import json
import random
import sys
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

HONG = []          # câu mô tả từng chỗ hỏng. Rỗng = thoát 0.

bt_goc, pa, d = chay(copy.deepcopy(GOC))
print(f'{"CƠ SỞ (không thêm gì)":<42} {"OK" if pa else "HỎNG":<6} điểm={d}')
if pa is None:
    HONG.append('CƠ SỞ: cauhinh.json hiện tại KHÔNG xếp được — mọi dòng '
                'dưới đây vô nghĩa')

for r in THU:
    cfg = copy.deepcopy(GOC)
    cfg['quy_tac'].append(r)
    ten = r['loai'] + ' — ' + r['ghi_chu']
    # PHẠM VI TRƯỚC ĐÃ. Một quy tắc khớp 0 cụm thì `loi == 0` (không có gì
    # để vi phạm) nên hậu kiểm báo ĐẠT — nó "không cấm gì mà vẫn ĐẠT",
    # đúng bẫy `n_uyen == 0`. Phải bắt ở đây, trước khi chạy bộ giải.
    try:
        pv = QT.pham_vi_quy_tac(r, bt_goc)
    except Exception as e:                              # noqa: BLE001
        pv = None
        HONG.append(f'{ten}: không tính được phạm vi — {type(e).__name__}: {e}')
    if pv is not None:
        la = {k: v for k, v in (pv.get('ten_la') or {}).items() if v}
        if la:
            HONG.append(f'{ten}: bộ lọc khai TÊN KHÔNG CÓ THẬT — {la}')
        elif not pv.get('so_cum'):
            HONG.append(f'{ten}: khớp 0 cụm — quy tắc này KHÔNG CẤM GÌ, '
                        'mà hậu kiểm vẫn sẽ báo ĐẠT')
    try:
        bt, pa, d = chay(cfg)
        if pa is None:
            kq, ghi = 'KHÔNG XẾP ĐƯỢC', ''
            HONG.append(f'{ten}: KHÔNG XẾP ĐƯỢC')
        else:
            bc, loi = X.hau_kiem(bt, pa)
            dong = [x for x in bc if r['ghi_chu'] in x[1]]
            kq = 'OK' if loi == 0 else 'CÒN LỖI'
            ghi = f'điểm={d}' + (f' | {dong[0][0]}' if dong else '')
            if loi:
                HONG.append(f'{ten}: CÒN LỖI — {loi} quy tắc vi phạm')
    except SystemExit as e:
        kq, ghi = 'CHẶN HẾT Ô', str(e)[:40]
        HONG.append(f'{ten}: CHẶN HẾT Ô — {str(e)[:60]}')
    if pv is not None and kq == 'OK':
        ghi += f' | {pv.get("so_cum")} cụm'
    print(f'{ten:<42.42} {kq:<16} {ghi}')

print('=' * 68)
print(f'Tổng: {len(THU) - len(HONG)}/{len(THU)} quy tắc thử ĐẠT.'
      if not HONG else
      f'Tổng: {len(THU)} quy tắc thử, {len(HONG)} CHỖ HỎNG.')
for c in HONG:
    print('  HỎNG:', c)
sys.exit(1 if HONG else 0)

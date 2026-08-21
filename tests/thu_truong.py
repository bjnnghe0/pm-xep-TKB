#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: KHAI BÁO TRUONG CỦA TỪNG LOẠI QUY TẮC
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_truong.py

 TRUONG liệt kê các khoá cấp cao nhất mà mỗi loại quy tắc chấp nhận.
 Nó phục vụ hai chỗ cùng lúc — bảng "python3 xep_tkb.py --quy-tac" và
 form nhập trên giao diện web — nên chép lại sang JS là chắc chắn lệch.

 Trước khi có TRUONG, đo được: cả 17/17 loại đều cho khoá bịa lọt qua.
 Gõ nhầm "thu" thành "thu_2" thì quy tắc KHÔNG cấm gì mà bảng đối chiếu
 vẫn ghi ĐẠT. Cùng một họ bẫy với các lỗi im lặng đã vá.
==========================================================================
"""
import copy
import io
import os
import sys
from contextlib import redirect_stdout

GOC_TM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_TM)

import xep_tkb as X          # noqa: E402
import quy_tac as QT         # noqa: E402

GOC = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
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


def dung(r):
    cfg = copy.deepcopy(GOC)
    cfg['quy_tac'] = [r]
    X.BaiToan(cfg)


def mau(ten):
    """Một khai báo hợp lệ của loại `ten`, lấy thẳng từ VI_DU."""
    r = copy.deepcopy(QT.DANH_MUC[ten].VI_DU)
    r['loai'] = ten
    r.setdefault('ghi_chu', 'thử ' + ten)
    return r


# --------------------------------------------------------------------------
def ca_1_moi_loai_deu_co():
    print('\nCA 1 — mọi loại trong DANH_MUC đều khai TRUONG')
    print('-' * 74)
    thieu = [t for t, c in QT.DANH_MUC.items() if not c.TRUONG]
    kiem(not thieu, f'{len(QT.DANH_MUC)} loại, không loại nào thiếu — {thieu}')

    sai_kieu, sai_khoa = [], []
    for t, c in QT.DANH_MUC.items():
        for tr in c.TRUONG:
            if not {'ten', 'kieu', 'nhan', 'bat_buoc'} <= set(tr):
                sai_khoa.append((t, tr))
            if tr['kieu'] not in QT.KIEU:
                sai_kieu.append((t, tr['ten'], tr['kieu']))
    kiem(not sai_khoa, f'Trường nào cũng có đủ ten/kieu/nhan/bat_buoc — {sai_khoa}')
    kiem(not sai_kieu, f'Mọi kiểu đều nằm trong QT.KIEU — {sai_kieu}')
    kiem(all(tr['nhan'] for c in QT.DANH_MUC.values() for tr in c.TRUONG),
         'Trường nào cũng có nhãn tiếng Việt để hiện trên form')
    kiem(all(c.MO_TA for c in QT.DANH_MUC.values()),
         'Loại nào cũng có MO_TA để hiện dưới ô chọn loại')

    co_chon = [(t, tr['ten']) for t, c in QT.DANH_MUC.items() for tr in c.TRUONG
               if tr['kieu'] == 'chon' and not tr.get('chon')]
    kiem(not co_chon, f'Kiểu "chon" nào cũng liệt kê sẵn giá trị — {co_chon}')


def ca_2_vi_du_khop_truong():
    print('\nCA 2 — mọi khoá trong VI_DU đều nằm trong TRUONG')
    print('-' * 74)
    sai = []
    for t, c in QT.DANH_MUC.items():
        hop_le = set(QT.KHOA_CHUNG) | {tr['ten'] for tr in c.TRUONG}
        thua = [k for k in c.VI_DU if k not in hop_le]
        if thua:
            sai.append((t, thua))
    kiem(not sai, f'VI_DU không dùng khoá nào ngoài TRUONG — {sai}')

    hong = []
    for t in QT.DANH_MUC:
        loi = bat_loi(lambda: dung(mau(t)))
        if loi:
            hong.append((t, loi.splitlines()[1:4]))
    kiem(not hong, f'Chép thẳng VI_DU vào cauhinh.json là chạy được — {hong}')


def ca_3_khoa_la_thi_dung():
    print('\nCA 3 — khoá lạ ở cấp cao nhất thì DỪNG (trước đây lọt hết 17/17)')
    print('-' * 74)
    lot = []
    for t in QT.DANH_MUC:
        r = mau(t)
        r['khoa_bia_ra'] = 123
        if bat_loi(lambda: dung(r)) is None:
            lot.append(t)
    kiem(not lot, f'Cả {len(QT.DANH_MUC)} loại đều chặn khoá bịa — lọt: {lot}')

    r = mau('khong_xep_thu')
    del r['thu']
    r['thu_2'] = [2]                       # gõ nhầm tên khoá
    loi = bat_loi(lambda: dung(r))
    kiem(loi is not None, 'Gõ nhầm "thu" thành "thu_2" — DỪNG')
    kiem(loi and 'thu_2' in loi, '  nêu đích danh khoá gõ nhầm')
    kiem(loi and 'KHÔNG cấm gì cả mà vẫn báo ĐẠT' in loi,
         '  nói rõ hậu quả nếu bỏ qua')
    kiem(loi and 'các khoá dùng được cho loại "khong_xep_thu"' in loi,
         '  liệt kê đúng các khoá loại đó nhận')

    r = mau('khong_xep_thu')
    r['_ghi_chu_rieng'] = 'ghi chú của tôi'
    kiem(bat_loi(lambda: dung(r)) is None,
         'Khoá bắt đầu bằng "_" vẫn được bỏ qua (quy ước ghi chú)')


def ca_4_thieu_khoa_bat_buoc():
    print('\nCA 4 — thiếu khoá bắt buộc thì DỪNG')
    print('-' * 74)
    r = mau('khong_xep_o')
    del r['o']
    loi = bat_loi(lambda: dung(r))
    kiem(loi is not None and 'thiếu "o"' in loi, 'khong_xep_o thiếu "o" — DỪNG')

    r = mau('khac_ngay')
    del r['b']
    kiem((bat_loi(lambda: dung(r)) or '').count('thiếu "b"') == 1,
         'khac_ngay thiếu nhóm "b" — DỪNG')

    r = mau('khong_xep_tiet')
    del r['tiet_trong_buoi']
    loi = bat_loi(lambda: dung(r))
    kiem(loi is not None and 'thay thế nhau' in loi,
         'khong_xep_tiet không có cả "tiet" lẫn "tiet_trong_buoi" — DỪNG')

    r = mau('khong_xep_tiet')
    del r['tiet_trong_buoi']
    r['tiet'] = [9, 10]
    kiem(bat_loi(lambda: dung(r)) is None,
         'Ghi khoá thay thế ("tiet") thì chạy bình thường')


def ca_5_danh_muc_in_ra():
    print('\nCA 5 — "--quy-tac" đọc TRUONG, không suy từ VI_DU')
    print('-' * 74)
    man = io.StringIO()
    with redirect_stdout(man):
        QT.in_danh_muc()
    ra = man.getvalue()
    thieu = [t for t in QT.DANH_MUC if f'▸ {t}' not in ra]
    kiem(not thieu, f'Danh mục in đủ {len(QT.DANH_MUC)} loại — thiếu {thieu}')
    thieu_nhan = [tr['nhan'] for c in QT.DANH_MUC.values() for tr in c.TRUONG
                  if tr['nhan'] not in ra]
    kiem(not thieu_nhan, f'In đủ nhãn của mọi trường — thiếu {thieu_nhan[:3]}')
    kiem('Dấu * = khoá bắt buộc' in ra, 'Có chú thích dấu * cho khoá bắt buộc')


def ca_6_khong_hoi_quy():
    print('\nCA 6 — không hồi quy')
    print('-' * 74)
    kiem(bat_loi(lambda: X.BaiToan(copy.deepcopy(GOC))) is None,
         'cauhinh.json thật vẫn dựng được')
    cfg = copy.deepcopy(GOC)
    r = [x for x in cfg['quy_tac'] if '_doc' in x]
    kiem(r, 'cauhinh.json có quy tắc mang khoá ghi chú "_doc" — vẫn qua được')


def ca_7_loai_thu_18_khong_lot():
    """ĐIỀU KIỆN 2 của người dùng: "CHƯA XẾP NHÓM" phải ĐỎ, không được im.

       Tôi từng nói loại mới "thừa hưởng nhóm CHƯA XẾP NHÓM nên không phải khai
       thêm" — và người dùng chỉ ra ngay: đó CHÍNH LÀ dạng lỗi im lặng mà cả
       tài liệu này viết ra để chống. Nhóm quyết định loại đó hiện ở đâu trên ô
       chọn, và quyết định luôn bộ từ khoá dùng so với ghi chú người gõ; rơi
       vào một nhóm vô danh nghĩa là mất cả hai mà không ai biết.

       HAI TẦNG, và ca thử này canh cả hai:
         · cửa ÉP lúc nạp mô-đun (@dang_ky + phép kiểm sau NHOM_LOAI)
         · lưới ĐỠ lúc chạy (nhom_danh_muc trả nhóm "CHƯA XẾP NHÓM")
    """
    print('\nCA 7 — loại thứ 18 KHÔNG LỌT: phải có NHAN + MO_TA + mặt trong NHOM_LOAI')
    print('-' * 74)
    thieu_nhan = [t for t, c in QT.DANH_MUC.items()
                  if not str(getattr(c, 'NHAN', '')).strip()]
    kiem(not thieu_nhan,
         f'{len(QT.DANH_MUC)} loại đều có NHAN — thiếu: {thieu_nhan}')
    thieu_mo_ta = [t for t, c in QT.DANH_MUC.items()
                   if not str(getattr(c, 'MO_TA', '')).strip()]
    kiem(not thieu_mo_ta, f'…và đều có MO_TA — thiếu: {thieu_mo_ta}')

    da_xep = {x for _, ds in QT.NHOM_LOAI for x in ds}
    ngoai = sorted(t for t in QT.DANH_MUC if t not in da_xep)
    kiem(not ngoai, f'…và đều có mặt trong NHOM_LOAI — ngoài nhóm: {ngoai}')

    thua = sorted(t for t in da_xep if t not in QT.DANH_MUC)
    kiem(not thua,
         f'NHOM_LOAI không nhắc tên loại đã bị xoá — thừa: {thua}')

    # Nhãn phải NÓI RÕ CHIỀU: bật một trong bốn chữ chỉ hướng lên.
    HUONG = ('CHỈ', 'KHÔNG', 'PHẢI', 'NÊN', 'GHIM', 'MỖI', 'Chia')
    mo_ho = [t for t, c in QT.DANH_MUC.items()
             if not any(h in c.NHAN for h in HUONG)]
    kiem(not mo_ho,
         f'Nhãn nào cũng bật một chữ chỉ hướng ({"/".join(HUONG)}) — mờ: '
         f'{mo_ho}. Cạm bẫy của chi_xep_thu là chữ "CHỈ"; nhãn không nói rõ '
         f'chiều thì thầy cô chọn nhầm loại y như ngày 20/8')

    nhan = {}
    for t, c in QT.DANH_MUC.items():
        nhan.setdefault(' '.join(c.NHAN.split()), []).append(t)
    trung = [ds for x, ds in nhan.items() if len(ds) > 1]
    kiem(not trung, f'17 nhãn khác nhau đôi một — trùng: {trung}')

    # CỬA ÉP: thiếu NHAN thì @dang_ky phải DỪNG ngay lúc nạp mô-đun.
    try:
        @QT.dang_ky('_loai_thu_thieu_nhan')
        class ThuThieuNhan(QT.QuyTac):
            MO_TA = 'x'
            MAU_CAU = 'x {loc}'
            TRUONG = (QT.T_LOC,)
        chan = False
    except SystemExit as e:
        chan = 'NHAN' in str(e)
    finally:
        QT.DANH_MUC.pop('_loai_thu_thieu_nhan', None)
    kiem(chan, 'Đăng ký loại THIẾU NHAN thì DỪNG ngay lúc nạp mô-đun')


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ KHAI BÁO TRUONG')
    print('=' * 74)
    ca_1_moi_loai_deu_co()
    ca_2_vi_du_khop_truong()
    ca_3_khoa_la_thi_dung()
    ca_4_thieu_khoa_bat_buoc()
    ca_5_danh_muc_in_ra()
    ca_6_khong_hoi_quy()
    ca_7_loai_thu_18_khong_lot()
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ NHÁNH DỰ PHÒNG CỦA xep_tkb.main()
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_du_phong.py

 Nhánh dự phòng là nhánh chạy khi MỌI lời giải đều trượt hậu kiểm. Bộ quy
 tắc thật không bao giờ chạm tới nhánh này, nên ở đây phải tự ép nó xảy ra
 bằng một lớp quy tắc DÙNG MỘT LẦN, chỉ cài hau_kiem() và cố tình báo lỗi
 những cụm đã biết trước. Lớp này chỉ được đăng ký trong tiến trình thử,
 KHÔNG có mặt trong DANH_MUC của bản chạy thật.

 Hai điều cần chứng minh:
   CA 1  nhánh dự phòng giữ phương án ÍT VI PHẠM NHẤT, kể cả khi phương án
         đó có điểm mềm THẤP HƠN một phương án nhiều lỗi hơn; và in thẳng
         ra màn hình các quy tắc đang bị vi phạm.
   CA 2  nhánh có phương án hợp lệ KHÔNG hồi quy — vẫn chỉ so theo điểm mềm.
==========================================================================
"""
import copy
import io
import json
import os
import random
import re
import shutil
import sys
import tempfile
from contextlib import redirect_stdout

GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC)

import xep_tkb as X          # noqa: E402
import quy_tac as QT         # noqa: E402

TEN_THU = '_thu_bat_loi'


# --------------------------------------------------------------------------
# Lớp quy tắc DÙNG MỘT LẦN — chỉ sống trong file thử này
# --------------------------------------------------------------------------

class QuyTacThuBatLoi(QT.QuyTac):
    """Không ràng buộc gì lúc giải, chỉ báo lỗi sau khi giải: mọi cụm khớp
       bộ lọc mà rơi vào các tiết liệt kê đều bị tính là vi phạm.
       Nhờ vậy bộ giải vẫn xếp thoải mái rồi mới trượt hậu kiểm — đúng tình
       huống mà nhánh dự phòng sinh ra để xử lý.

       TRUONG phải khai đủ các khoá loại này nhận, y như mọi loại quy tắc
       thật — không khai thì kiem_khoa_quy_tac() chặn ngay lúc dựng."""

    TRUONG = (QT.T_LOC, QT.T_TIET, QT.T_TIET_BUOI)

    def hau_kiem(self):
        cam = self.tap_tiet()
        return [self.ten_o(c) for c in self.cac_cum()
                if set(range(c.vitri, c.vitri + c.size)) & cam]


QuyTacThuBatLoi.TEN = TEN_THU
QT.DANH_MUC[TEN_THU] = QuyTacThuBatLoi        # chỉ trong tiến trình thử


# --------------------------------------------------------------------------
# Tiện ích
# --------------------------------------------------------------------------

def cau_hinh_goc():
    return X.doc_cau_hinh(os.path.join(GOC, 'cauhinh.json'))


def dat_tim_kiem(cfg, so_lan, seed=2027):
    """Khoá chặt tham số tìm kiếm để lần chạy lặp lại được y hệt: giới hạn
       giây đặt rất rộng nên không có lần thử nào bị cắt giữa chừng."""
    cfg['tim_kiem'] = {'so_lan_thu': so_lan, 'gioi_han_buoc': 30000,
                       'gioi_han_giay_moi_lan': 10, 'gioi_han_tong_giay': 3600,
                       'seed': seed}
    return cfg


def cac_phuong_an(cfg):
    """Chạy lại đúng dãy seed mà main() dùng -> [(số quy tắc lỗi, điểm mềm)]."""
    bt = X.BaiToan(copy.deepcopy(cfg))
    tk = cfg['tim_kiem']
    ds = []
    for i in range(tk['so_lan_thu']):
        pa = X.BoGiai(bt, random.Random(tk['seed'] + i),
                      tk['gioi_han_buoc'], tk['gioi_han_giay_moi_lan']).giai()
        if pa is None:
            continue
        d = X.cham_diem(bt, pa)
        _, loi = X.hau_kiem(bt, pa)
        ds.append((loi, d))
    return ds


def chay_main(cfg, thu_muc):
    """Ghi cấu hình ra thư mục tạm rồi gọi thẳng main(), thu lại màn hình."""
    duong_dan = os.path.join(thu_muc, 'cauhinh_thu.json')
    with io.open(duong_dan, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False)
    shutil.copy(os.path.join(GOC, 'mau_tkb.xlsx'),
                os.path.join(thu_muc, 'mau_tkb.xlsx'))

    argv = sys.argv
    sys.argv = ['xep_tkb.py', '--cauhinh', duong_dan, '--xuat', 'TKB_thu.xlsx']
    man_hinh = io.StringIO()
    try:
        with redirect_stdout(man_hinh):
            X.main()
    except SystemExit as e:
        man_hinh.write(f'\n[SystemExit {e.code}]\n')
    finally:
        sys.argv = argv
    return man_hinh.getvalue()


KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


# --------------------------------------------------------------------------
# CA 1 — nhánh dự phòng phải chọn theo SỐ LỖI trước, điểm mềm sau
# --------------------------------------------------------------------------

def ca_1_du_phong(thu_muc):
    print('\nCA 1 — nhánh dự phòng: ít vi phạm nhất thắng, điểm mềm chỉ là phụ')
    print('-' * 70)
    cfg = dat_tim_kiem(cau_hinh_goc(), so_lan=30)

    # (a) một quy tắc thử LUÔN LUÔN lỗi -> ép mọi lời giải đều trượt hậu kiểm
    cfg['quy_tac'].append(
        {'loai': TEN_THU, 'ghi_chu': '[THỬ] SHCN ở đâu cũng tính là lỗi',
         'loc': {'mon': 'SHCN'}, 'tiet_trong_buoi': [1, 2, 3, 4, 5]})

    # (b) mỗi lớp một quy tắc thử: lỗi nếu Toán/Văn của lớp đó rơi vào 2 tiết
    #     đầu buổi -> số quy tắc lỗi thay đổi theo từng phương án
    for lop in [l['ten'] for l in cfg['lop']]:
        cfg['quy_tac'].append(
            {'loai': TEN_THU,
             'ghi_chu': f'[THỬ] {lop}: Toán/Văn không được vào 2 tiết đầu buổi',
             'loc': {'nhom_mon': ['Toán', 'Văn'], 'lop': lop},
             'tiet_trong_buoi': [1, 2]})

    # (c) tiêu chí mềm kéo NGƯỢC lại: thưởng rất đậm cho Toán/Văn 2 tiết đầu
    #     -> phương án điểm mềm cao nhất chính là phương án nhiều lỗi nhất
    cfg['quy_tac'].append(
        {'loai': 'uu_tien_o', 'ghi_chu': '[THỬ] Toán/Văn vào 2 tiết đầu buổi',
         'loc': {'nhom_mon': ['Toán', 'Văn']}, 'tiet_trong_buoi': [1, 2],
         'diem': 50})

    ds = cac_phuong_an(cfg)
    loi_min = min(l for l, _ in ds)
    diem_cua_it_loi_nhat = max(d for l, d in ds if l == loi_min)
    diem_max = max(d for _, d in ds)
    loi_cua_diem_cao_nhat = min(l for l, d in ds if d == diem_max)
    print(f'  {len(ds)} lời giải thu được | số lỗi {loi_min}..'
          f'{max(l for l, _ in ds)} | điểm mềm {min(d for _, d in ds)}..{diem_max}')

    # Điều kiện tiên quyết: ca thử phải THỰC SỰ phân biệt được hai cách xếp hạng
    kiem(loi_min > 0, 'Mọi lời giải đều vi phạm (bắt buộc rơi vào nhánh dự phòng)')
    kiem(diem_cua_it_loi_nhat < diem_max,
         f'Phương án ít lỗi nhất có điểm mềm THẤP HƠN ({diem_cua_it_loi_nhat} '
         f'< {diem_max}) — nếu xếp hạng theo điểm mềm sẽ chọn sai')
    kiem(loi_cua_diem_cao_nhat > loi_min,
         f'Phương án điểm mềm cao nhất lại nhiều lỗi hơn '
         f'({loi_cua_diem_cao_nhat} > {loi_min})')

    out = chay_main(cfg, thu_muc)
    kiem('[CẢNH BÁO]' in out, 'Có in [CẢNH BÁO] khi phải dùng dự phòng')

    m = re.search(r'ÍT VI PHẠM NHẤT: (\d+) quy tắc lỗi, điểm mềm (-?\d+)', out)
    kiem(m is not None, 'Có in số quy tắc vi phạm và điểm mềm ra màn hình')
    if m:
        kiem(int(m.group(1)) == loi_min,
             f'Chọn đúng phương án ít vi phạm nhất: {m.group(1)} = {loi_min}')
        kiem(int(m.group(2)) == diem_cua_it_loi_nhat,
             f'Điểm mềm đúng của phương án đó: {m.group(2)} '
             f'= {diem_cua_it_loi_nhat}')
        kiem(int(m.group(2)) != diem_max,
             'KHÔNG chọn phương án điểm mềm cao nhất (bằng chứng đã đổi tiêu chí)')

    m2 = re.search(r'Các quy tắc đang bị vi phạm \((\d+)\):', out)
    kiem(m2 is not None and int(m2.group(1)) == loi_min,
         'Liệt kê đủ tên từng quy tắc vi phạm, đúng bằng số lỗi')
    kiem(out.count('\n             • ') == loi_min,
         'Mỗi quy tắc vi phạm một dòng riêng')
    kiem('[THỬ] SHCN ở đâu cũng tính là lỗi' in out,
         'Tên quy tắc vi phạm hiện nguyên văn ghi_chu của người dùng')
    kiem(re.search(r'• \[.*?\].*?-->.*?Thứ', out) is not None,
         'Có kèm phần chi tiết do hau_kiem() trả về')
    kiem('nới đúng những quy tắc vừa liệt kê ở trên' in out,
         'Có dòng gợi ý nên nới quy tắc nào')

    m3 = re.search(r'lần thử trong \d+s\. (.+)', out)
    kiem(m3 is not None and 'cao nhất' not in m3.group(1),
         'Dòng tổng kết KHÔNG dùng chữ "cao nhất" ở nhánh dự phòng')
    kiem(m3 is not None and m3.group(1).startswith('Phương án ít vi phạm nhất:'),
         'Dòng tổng kết nói đúng tiêu chí đã dùng để chọn')


# --------------------------------------------------------------------------
# CA 2 — nhánh có phương án hợp lệ phải giữ nguyên hành vi cũ
# --------------------------------------------------------------------------

def ca_2_khong_hoi_quy(thu_muc):
    print('\nCA 2 — nhánh hợp lệ: vẫn chỉ so theo điểm mềm, không hồi quy')
    print('-' * 70)
    cfg = dat_tim_kiem(cau_hinh_goc(), so_lan=12)

    ds = cac_phuong_an(cfg)
    diem_max = max(d for _, d in ds)
    print(f'  {len(ds)} lời giải thu được | điểm mềm '
          f'{min(d for _, d in ds)}..{diem_max}')
    kiem(all(l == 0 for l, _ in ds), 'Mọi lời giải đều hợp lệ (không có lỗi)')

    out = chay_main(cfg, thu_muc)
    kiem('[CẢNH BÁO]' not in out, 'Không đụng tới nhánh dự phòng')
    m = re.search(r'Điểm cao nhất: (-?\d+)', out)
    kiem(m is not None and int(m.group(1)) == diem_max,
         f'Vẫn giữ phương án điểm mềm CAO NHẤT: {m.group(1) if m else "?"} '
         f'= {diem_max}')
    # Đừng ghim cứng con số: thêm một quy tắc vào cauhinh.json là vỡ ngay.
    # Điều cần khẳng định là MỌI quy tắc đều ĐẠT, bao nhiêu cái cũng được.
    m3 = re.search(r'Tổng: (\d+)/(\d+) quy tắc ĐẠT', out)
    kiem(m3 is not None and m3.group(1) == m3.group(2),
         f'Mọi quy tắc đều ĐẠT — {m3.group(0) if m3 else "không tìm thấy dòng Tổng"}')


# --------------------------------------------------------------------------

if __name__ == '__main__':
    print('=' * 70)
    print(' THỬ NHÁNH DỰ PHÒNG — xep_tkb.main()')
    print('=' * 70)

    nguon = io.open(os.path.join(GOC, 'quy_tac.py'), encoding='utf-8').read()
    kiem(TEN_THU not in nguon,
         f'Loại quy tắc thử "{TEN_THU}" KHÔNG có trong quy_tac.py thật')

    with tempfile.TemporaryDirectory() as thu_muc:
        ca_1_du_phong(thu_muc)
        ca_2_khong_hoi_quy(thu_muc)

    print('=' * 70)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

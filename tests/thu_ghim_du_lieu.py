#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ GHIM LUẬT: KHÔNG CA THỬ NÀO ĐƯỢC SO BẰNG VỚI HẰNG SỐ LẤY TỪ DỮ LIỆU
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_ghim_du_lieu.py

 CLAUDE.md đã ghi luật này từ lâu:
     "22 dòng hậu kiểm ... ĐỪNG ghim con số này vào ca thử — thêm một quy tắc
      vào cauhinh.json là vỡ. Khẳng định Tổng: N/N (hai số bằng nhau) thay vì
      so với số cụ thể."
 Rồi vẫn có BA chỗ ghim, và cả ba cùng vỡ một lượt khi thầy cô thêm bốn quy tắc
 qua giao diện:
     tests/thu_web.py       len(d['quy_tac']) == 13     (tệp đã có 17)
     tests/thu_an_ninh.py   so_tat(dd) == []            (đã có quy tắc bị tắt)
     tests/thu_phien.py     quy tắc nháp lọc "lop": "12B1" + "thu": [2]
                            -> đụng quy tắc mới "Vật lý 12B1 chỉ Thứ 2",
                            Vật lý 12B1 hết sạch ngày, máy chủ chặn ĐÚNG,
                            và ca thử đỏ vì máy chủ làm đúng.

 LUẬT VIẾT RA KHÔNG TỰ THI HÀNH. Tệp này biến luật đó thành một mục đỏ.

 Bắt LỚP lỗi, không bắt một lần lỗi — cùng kiểu với ca_a1c (bóc danh sách
 đường thẳng từ web.py) và CA 11 của thu_dang_nhap (không lớp CSS nào khai hai
 lần). Nghĩa là: nó KHÔNG dò ba chuỗi đã biết, mà dựng TỪ VỰNG từ chính
 cauhinh.json rồi soi cây cú pháp của mọi tệp ca thử.

 HAI BỘ DÒ:
   D1 — SỐ:  so sánh mà một vế chạm vào khoá dữ liệu (quy_tac, lop, gvcn...)
             còn vế kia là một số viết cứng.
   D2 — TÊN: so sánh mà một vế là chuỗi viết cứng TRÙNG với một giá trị có
             thật trong cauhinh.json (tên lớp, tên GVCN, tên môn, tên GV...).

 NGOẠI LỆ CÓ CHỦ Ý: thêm "ghim-co-y" vào chú thích cuối dòng thì bỏ qua, và
 CA 1 in ra tổng số chỗ đang dùng ngoại lệ — để nó không lặng lẽ phình ra.

 Đây là ca thử ĐỌC MÃ NGUỒN, giống thu_lenh_chay.py: ngoại lệ có chủ ý với bất
 biến "khẳng định trên hành vi". Khác chỗ này: nó đọc CÂY CÚ PHÁP chứ không dò
 chuỗi, nên chú thích và docstring không bao giờ lọt vào — tức là nó miễn nhiễm
 với kiểu hỏng số 4 (khớp phải dòng chú thích).
==========================================================================
"""
import ast
import io
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import GOC_TM      # noqa: E402

KQ = []
DAU_NGOAI_LE = 'ghim-co-y'

# Trần của cửa thoát hiểm. ĐẾM **HẰNG ĐƯỢC THA**, KHÔNG đếm NÚT được tha —
# xem nếp hỏng 16 trong CLAUDE.md. Bản đầu đếm nút, và đo được 26/8/2026:
# nới MỘT dòng "ghim-co-y" CÓ SẴN từ `c.nhom == 'Sử'` thành
# `c.nhom in [bảy tên môn]` làm 1 hằng thành 7 mà bộ đếm ĐỨNG YÊN — trần
# vẫn đúng, cửa vẫn mở. Một cái bao chở được vô hạn ruột.
TRAN_HANG_THA = 3


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


# ==========================================================================
# TỪ VỰNG — dựng từ chính cauhinh.json, không chép tay
# ==========================================================================

# Khoá dữ liệu: chạm vào một trong những khoá này rồi so bằng với số viết cứng
# thì gần như chắc chắn là ghim. Mỗi khoá kèm lý do, và đây là danh sách CÓ CHỦ
# ĐÍCH chứ không phải "mọi khoá trong tệp" — 'bat', 'loai', 'thu' quá chung,
# gom vào sẽ đỏ oan hàng loạt.
KHOA_DU_LIEU = {
    'quy_tac': 'số quy tắc — đúng chỗ đã vỡ ở thu_web.py',
    'lop': 'danh sách lớp',
    'gvcn': 'tên giáo viên chủ nhiệm',
    'gvcn_vt': 'tên viết tắt GVCN',
    'phan_cong': 'phân công giáo viên',
    'dinh_muc_mon': 'định mức tiết theo môn',
    'khung_gio': 'khung giờ học',
    'cac_thu': 'các thứ trong tuần',
    'cac_tiet': 'các tiết trong buổi',
    'tieu_de': 'tiêu đề in trên TKB',
}


def tu_vung(cfg):
    """Mọi CHUỖI là dữ liệu nhà trường: tên lớp, GVCN, môn, giáo viên, tuần.

       Bỏ chuỗi quá ngắn (< 3 ký tự): 'a', 'b' là tên nhóm trong quy tắc
       khac_ngay, so bằng với chúng là chuyện bình thường của mã.
    """
    ra = set()
    for l in cfg.get('lop', []):
        for k in ('ten', 'gvcn', 'gvcn_vt'):
            if isinstance(l.get(k), str):
                ra.add(l[k])
    ra |= {m for m in cfg.get('dinh_muc_mon', {}) if not m.startswith('_')}
    # phan_cong: lop -> [[tên môn, giáo viên viết tắt, số tiết/tuần], ...]
    for lop, cac in (cfg.get('phan_cong') or {}).items():
        if lop.startswith('_') or not isinstance(cac, list):
            continue
        for muc in cac:
            if isinstance(muc, list):
                ra |= {x for x in muc if isinstance(x, str)}
    ti = cfg.get('thong_tin') or {}
    ra |= {ti.get(k) for k in ('tieu_de', 'tuan', 'ten_sheet')
           if isinstance(ti.get(k), str)}
    return {x for x in ra if isinstance(x, str) and len(x) >= 3}


# ==========================================================================
# BỘ DÒ — đi trên CÂY CÚ PHÁP, không dò chuỗi
# ==========================================================================

def _cac_chuoi_cung(nut):
    """Mọi chuỗi VIẾT CỨNG trong một vế: chuỗi lẻ, hoặc danh sách/tuple/tập
       toàn hằng. Danh sách hằng mới là dạng nguy hiểm nhất — nó ghim cả TÊN
       lẫn SỐ LƯỢNG cùng lúc."""
    if isinstance(nut, ast.Constant):
        return [nut.value] if isinstance(nut.value, str) else []
    if isinstance(nut, (ast.List, ast.Tuple, ast.Set)):
        ra = []
        for p in nut.elts:
            ra += _cac_chuoi_cung(p)
        return ra
    return []


def _doan(nguon, nut):
    d = ast.get_source_segment(nguon, nut)
    return ' '.join((d or '').split())[:70]


def soi(dd, khoa, gia_tri):
    """Trả (vi phạm, SỐ HẰNG được tha, số phép so đã soi, số NÚT khai tha).

       ⚠ Phần tử thứ hai đếm **HẰNG**, không đếm **NÚT**. Một dòng khai
       `ghim-co-y` ghim được bao nhiêu tên cũng được — `x in ['12B1', …,
       '12B6']` vẫn là MỘT nút mà tha SÁU tên lớp. Đếm nút thì cái trần
       không chặn gì (nếp hỏng 16), nên nút bị tha vẫn phải ĐI QUA ĐÚNG
       BỘ DÒ như mọi nút khác — chỉ khác chỗ đổ kết quả.
    """
    with io.open(dd, encoding='utf-8') as f:
        nguon = f.read()
    dong = nguon.split('\n')
    cay = ast.parse(nguon, filename=dd)
    rel = os.path.relpath(dd, GOC_TM)
    vi_pham, hang_tha, da_soi, nut_tha = [], 0, 0, 0

    for nut in ast.walk(cay):
        if not isinstance(nut, ast.Compare):
            continue
        da_soi += 1
        # KHÔNG `continue` ở đây. Nút được tha vẫn soi hết, chỉ đổi chỗ đổ.
        tha = DAU_NGOAI_LE in dong[nut.lineno - 1]
        if tha:
            nut_tha += 1
        ve = [nut.left] + list(nut.comparators)
        for i, a in enumerate(ve):
            for b in ve[i + 1:]:
                for x, y in ((a, b), (b, a)):
                    # D1 — vế x chạm khoá dữ liệu, vế y là số viết cứng.
                    #
                    # TRỪ SÀN KHÁC-RỖNG: phép so THỨ TỰ với 0 hoặc 1
                    # (> 0, >= 1, > 1, <= 1...) không ghim con số nào của nhà
                    # trường — nó khẳng định "có ít nhất một" / "có nhiều hơn
                    # một". CLAUDE.md BẮT BUỘC phải viết câu đó trước khi dùng
                    # một số đếm từ dữ liệu (bẫy n_uyen == 0), nên bắt luôn cả
                    # nó là bắt oan đúng cái mẫu mình đòi hỏi.
                    #
                    # Ranh giới hẹp và giải thích được: chỉ 0 và 1, và chỉ với
                    # toán tử thứ tự. "== 1" vẫn bị bắt (ghim đúng một), "> 5"
                    # vẫn bị bắt (5 rất có thể là số lớp trừ một).
                    san = (isinstance(nut.ops[0], (ast.Lt, ast.LtE, ast.Gt,
                                                   ast.GtE))
                           and isinstance(y, ast.Constant)
                           and y.value in (0, 1)
                           and not isinstance(y.value, bool))
                    if (not san and isinstance(y, ast.Constant)
                            and isinstance(y.value, int)
                            and not isinstance(y.value, bool)):
                        cham = [k for k in khoa
                                if k in (_doan(nguon, x) or '')]
                        if cham and tha:
                            hang_tha += 1
                        elif cham:
                            vi_pham.append(
                                (rel, nut.lineno, 'D1',
                                 f'{_doan(nguon, nut)}   <- chạm '
                                 f'"{cham[0]}" rồi so với số cứng {y.value}'))
                    # D2 — vế y là chuỗi viết cứng trùng dữ liệu nhà trường.
                    # Nhận cả DANH SÁCH hằng: == ['12B1', '12B2', ...] cũng là
                    # ghim tên lớp, mà lại ghim luôn cả SỐ LƯỢNG lớp.
                    trung = [c for c in _cac_chuoi_cung(y) if c in gia_tri]
                    if trung and tha:
                        # ĐẾM HẾT, KHÔNG `break`. Đây chính là chỗ nếp hỏng
                        # 16 nằm: `break` sau tên đầu tiên biến một danh
                        # sách 50 tên lớp thành đúng MỘT đơn vị bị đếm.
                        hang_tha += len(trung)
                    elif trung:
                        vi_pham.append(
                            (rel, nut.lineno, 'D2',
                             f'{_doan(nguon, nut)}   <- so bằng với '
                             f'"{trung[0]}" lấy thẳng từ cauhinh.json'))
    return vi_pham, hang_tha, da_soi, nut_tha


def cac_tep_ca_thu():
    ra = [os.path.join(GOC_TM, 'tu_kiem_tra.py')]
    tm = os.path.join(GOC_TM, 'tests')
    ra += [os.path.join(tm, t) for t in sorted(os.listdir(tm))
           if t.endswith('.py')]
    return [d for d in ra if os.path.exists(d)]


# ==========================================================================
def ca_0_tu_vung_dung_tu_du_lieu_that():
    print('\nCA 0 — từ vựng dựng từ chính cauhinh.json (chống soi rỗng)')
    print('-' * 74)
    cfg = json.load(io.open(os.path.join(GOC_TM, 'cauhinh.json'),
                            encoding='utf-8'))
    gt = tu_vung(cfg)
    kiem(len(gt) >= 20,
         f'Bóc được {len(gt)} chuỗi dữ liệu nhà trường (lớp/GVCN/môn/GV)')
    ten_lop = {l['ten'] for l in cfg['lop']}
    kiem(ten_lop <= gt, f'Trong đó có đủ tên lớp — {sorted(ten_lop)}')
    kiem(any(l['gvcn'] in gt for l in cfg['lop']), 'và có tên GVCN')
    kiem('quy_tac' in KHOA_DU_LIEU, 'Khoá "quy_tac" nằm trong danh sách canh')
    return gt


def ca_1_hai_chieu(gt):
    print('\nCA 1 — bộ dò: biết BẮT và biết BỎ QUA (điều kiện tiên quyết)')
    print('-' * 74)
    lop = sorted(gt & {'12B1', '12B2', '12B3'}) or [sorted(gt)[0]]
    L = lop[0]

    can_bat = [
        (f"kiem(len(d['quy_tac']) == 13, 'x')", 'D1 — số quy tắc viết cứng'),
        (f"kiem(so_tat(dd) == [], 'x')  # noqa", None),   # xử riêng bên dưới
        (f"kiem(d['lop'][0] == '{L}', 'x')", 'D2 — tên lớp viết cứng'),
        (f"kiem(con == ['{L}', 'ABC'], 'x')", 'D2 — DANH SÁCH tên lớp viết cứng'),
        (f"assert len(cfg['dinh_muc_mon']) == 15", 'D1 — số môn viết cứng'),
        (f"kiem(len(cfg['khung_gio']['cac_thu']) != 5, 'x')",
         'D1 — số thứ trong tuần'),
        # Sàn khác-rỗng chỉ tha 0 và 1, và chỉ với toán tử THỨ TỰ. Ba dòng này
        # canh đúng ba mép của ranh giới đó — thiếu chúng thì cửa "sàn" mở
        # rộng ra thành cửa chính lúc nào không hay.
        (f"kiem(len(d['quy_tac']) == 1, 'x')", 'D1 — "== 1" vẫn phải bắt'),
        (f"kiem(len(d['lop']) > 5, 'x')", 'D1 — "> 5" vẫn phải bắt'),
        (f"kiem(len(d['lop']) != 1, 'x')", 'D1 — "!= 1" vẫn phải bắt'),
    ]
    sot = []
    for ma, nhan in can_bat:
        if nhan is None:
            continue
        vp = _soi_chuoi(ma, gt)
        if not vp:
            sot.append(nhan)
    kiem(not sot, f'BẮT được {len(can_bat) - 1} dạng ghim — sót: {sot}')

    can_bo_qua = [
        ("kiem(len(than_khac) == 1, 'x')", 'đếm thứ do CHÍNH ca thử dựng ra'),
        ("kiem(so_qt(dd) == n0 + 1, 'x')", 'so với trạng thái chụp trước đó'),
        ("kiem(so_tat(dd) == tat_ban_dau, 'x')", 'so với biến, không với hằng'),
        ("kiem(ma == 200, 'x')", 'mã HTTP — không phải dữ liệu nhà trường'),
        ("kiem(len(hong) == 0, 'x')", 'đếm mục lỗi của chính bộ thử'),
        # SÀN KHÁC-RỖNG — điều kiện tiên quyết mà CLAUDE.md bắt buộc phải có
        ("kiem(len(d['lop']) > 0, 'x')", 'sàn: có ít nhất một lớp'),
        ("kiem(len(d['quy_tac']) > 1, 'x')", 'sàn: có hơn một quy tắc'),
        ("kiem(len(gv) >= 1, 'x')", 'sàn: danh sách gv không rỗng'),
        ("kiem(bg['ten_dang_nhap'] == 'nguoihai', 'x')",
         'tên tài khoản thử, không có trong cauhinh.json'),
        (f"r = {{'loc': {{'lop': '{L}'}}}}", 'DỰNG dữ liệu, không phải so bằng'),
        (f"kiem(x == '{L}', 'x')  # {DAU_NGOAI_LE}: có lý do",
         'đã khai ngoại lệ có chủ ý'),
    ]
    bat_nham = [n for ma, n in can_bo_qua if _soi_chuoi(ma, gt)]
    kiem(not bat_nham,
         f'BỎ QUA đúng {len(can_bo_qua)} dạng hợp lệ — bắt nhầm: {bat_nham}')

    # ------------------------------------------------------------------
    # BỘ ĐẾM NGOẠI LỆ ĐẾM **HẰNG**, KHÔNG ĐẾM **NÚT** — nếp hỏng 16.
    #
    # Không mục nào khác canh được chuyện này: bản đếm-nút và bản đếm-hằng
    # cho CÙNG một con số trên mã hôm nay (mỗi ngoại lệ đang tha đúng một
    # hằng), nên CA 2 xanh y hệt ở cả hai bản. Chỉ phép thử "thêm ruột vào
    # một cái bao CÓ SẴN" mới tách được chúng ra.
    nhieu = sorted(gt & {'12B1', '12B2', '12B3', '12B4', '12B5', '12B6'})
    kiem(len(nhieu) > 2,
         f'Điều kiện tiên quyết: dựng được một danh sách {len(nhieu)} tên '
         f'thật để nhét vào MỘT nút')
    if len(nhieu) > 2:
        ds = ', '.join(repr(x) for x in nhieu)
        h1, n1 = _dem_tha(f"kiem(x == {nhieu[0]!r}, 'y')  # {DAU_NGOAI_LE}", gt)
        hN, nN = _dem_tha(f"kiem(x in [{ds}], 'y')  # {DAU_NGOAI_LE}", gt)
        kiem((h1, n1) == (1, 1),
             f'Một ngoại lệ tha MỘT tên -> đếm (1 hằng, 1 nút), đo ({h1}, {n1})')
        kiem((hN, nN) == (len(nhieu), 1),
             f'CÙNG MỘT NÚT tha {len(nhieu)} tên -> đếm ({len(nhieu)} hằng, '
             f'1 nút), đo ({hN}, {nN}) — số HẰNG phải nhảy theo, số NÚT thì không')
        h0, n0 = _dem_tha(f"kiem(ma == 200, 'y')  # {DAU_NGOAI_LE}", gt)
        kiem((h0, n0) == (0, 1),
             f'Ngoại lệ khai mà KHÔNG ghim gì -> tốn 0 hằng, đo ({h0}, {n0}) — '
             f'ngân sách chỉ tiêu vào chỗ thật sự ghim')


def _dem_tha(ma, gt):
    """(số hằng được tha, số nút khai tha) của một mẩu mã. Dùng cho CA 1."""
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.py', encoding='utf-8',
                                     delete=False) as f:
        f.write(ma + '\n')
        t = f.name
    try:
        _, h, _, n = soi(t, KHOA_DU_LIEU, gt)
        return h, n
    finally:
        os.unlink(t)


def _soi_chuoi(ma, gt):
    """Chạy bộ dò trên một mẩu mã trong bộ nhớ. Dùng cho CA 1."""
    import tempfile
    with tempfile.NamedTemporaryFile('w', suffix='.py', encoding='utf-8',
                                     delete=False) as f:
        f.write(ma + '\n')
        t = f.name
    try:
        return soi(t, KHOA_DU_LIEU, gt)[0]
    finally:
        os.unlink(t)


def ca_2_quet_that(gt):
    print('\nCA 2 — quét mọi tệp ca thử: không còn chỗ nào ghim')
    print('-' * 74)
    tep = cac_tep_ca_thu()
    kiem(len(tep) >= 14, f'Soi {len(tep)} tệp ca thử (không phải soi rỗng)')
    kiem(any(t.endswith('thu_ghim_du_lieu.py') for t in tep),
         'Và CHÍNH TỆP NÀY cũng bị soi — không tự loại trừ mình')

    vi_pham, hang_tha, da_soi, nut_tha = [], 0, 0, 0
    for d in tep:
        v, h, s, n = soi(d, KHOA_DU_LIEU, gt)
        vi_pham += v
        hang_tha += h
        da_soi += s
        nut_tha += n
    kiem(da_soi >= 300,
         f'Đã đi qua {da_soi} phép so sánh — bộ dò thật sự có chạy')
    print(f'  ... {nut_tha} nút khai "{DAU_NGOAI_LE}", '
          f'tha {hang_tha} HẰNG')

    # MỘT mục cho toàn bộ vi phạm: kiem() trong vòng lặp làm số mục trong
    # "Tổng: N/N" nhảy theo số lỗi, và CLAUDE.md không ghim được con số nào.
    kiem(not vi_pham,
         f'Không ca thử nào so bằng với hằng số lấy từ cauhinh.json — '
         f'{len(vi_pham)} chỗ' +
         (':\n        ' + '\n        '.join(
             f'{t}:{d} [{k}] {c}' for t, d, k, c in vi_pham[:15])
          if vi_pham else ''))
    # ĐẾM HẰNG, KHÔNG ĐẾM NÚT. Nút là cái BAO, hằng là cái RUỘT — và thứ
    # gây hại nằm trong ruột. Xem nếp hỏng 16.
    kiem(hang_tha <= TRAN_HANG_THA,
         f'Cửa thoát hiểm "{DAU_NGOAI_LE}" đang tha {hang_tha} HẰNG '
         f'(trần {TRAN_HANG_THA}), rải trên {nut_tha} nút — đếm HẰNG chứ '
         f'không đếm NÚT, vì một nút tha được bao nhiêu hằng cũng được')


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ: KHÔNG GHIM HẰNG SỐ LẤY TỪ cauhinh.json VÀO CA THỬ')
    print('=' * 74)
    gt = ca_0_tu_vung_dung_tu_du_lieu_that()
    ca_1_hai_chieu(gt)
    ca_2_quet_that(gt)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: cauhinh.json KHỚP BỘ SỐ PHÂN CÔNG TUẦN 1 ĐÃ ĐỐI CHIẾU
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_phan_cong_tuan1.py

 Ca thử này bắt đúng MỘT chuyện: **tuần sau có ai sửa `cauhinh.json` mà
 không ai biết**. Nó đỏ khi khai báo phân công đi lệch khỏi bộ số đã đối
 chiếu với bản TKB thật của trường ngày 26/8/2026.

 ┌──────────────────────────────────────────────────────────────────────┐
 │ HAI VẾ PHẢI ĐỘC LẬP NHAU — nếu không thì nó không canh gì cả.        │
 │                                                                      │
 │   vế A = `cauhinh.json`        (thứ đang bị canh)                    │
 │   vế B = `phan_cong_tuan1.json` (mốc, ĐÓNG BĂNG, đọc ra từ bản TKB   │
 │                                  thật của trường — KHÔNG từ vế A)    │
 │                                                                      │
 │ Vì vậy tệp này **KHÔNG** `import doc_tkb`, `bang_ten`, `kho_tuan`,   │
 │ `sinh_dang`, `doi_chieu`, và **KHÔNG** đọc `luu_tru/`. Dựng lại vế B │
 │ lúc chạy là để nới bảng gộp dịch được CẢ HAI vế — nếp hỏng 12, và    │
 │ khi đó lùi bản vá ra sẽ KHÔNG mục nào đỏ. CA 4 tự soi chính tệp này  │
 │ bằng cây cú pháp để luật đó không trôi.                              │
 │                                                                      │
 │ Hệ quả tốt: chạy được trên máy vừa `git clone` — chỉ cần hai tệp     │
 │ `.json`, không cần `luu_tru/` (đã gitignore).                        │
 └──────────────────────────────────────────────────────────────────────┘

 KỲ VỌNG DỰNG BẰNG CÁCH ĐÈ, KHÔNG PHẢI BẰNG CÁCH BỎ QUA. Mốc ghi con số
 ĐỌC THÔ từ tệp trường, rồi `ngoai_le` ghi con số ĐÚNG. Ca thử lấy thô rồi
 đè bằng đúng — nên không khoá nào bị bỏ ra ngoài phép so. Bỏ qua khoá là
 mở một lỗ: sửa `cauhinh.json` đúng chỗ được tha thì không mục nào đỏ.

 KHI MỤC NÀY ĐỎ, ĐỪNG SỬA SỐ CHO KHỚP. Nó nói `cauhinh.json` ĐÃ ĐỔI so với
 mốc. Đổi có chủ ý thì cập nhật mốc kèm ngày + người + lý do.

 NĂM BẤT BIẾN ĐƯỢC CANH:
   CA 1  Điều kiện tiên quyết: hai tệp đọc được, khác rỗng, cùng bộ lớp
   CA 2  Trục (lớp, môn): số tiết và tên GV khớp, trừ ĐÚNG ngoại lệ đã khai
   CA 3  Trục (lớp, GV): KHÔNG ngoại lệ nào, không bịt miệng được
   CA 4  Chính tệp này không dựng lại vế B (soi cây cú pháp)
   CA 5  Mốc sinh dưới ĐÚNG bảng tên đang dùng, và ngoại lệ có chữ ký
==========================================================================
"""
import ast
import io
import json
import os
import sys

GOC_DA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

KQ = []

# Trần số ngoại lệ. Ghim literal ở đây là ĐÚNG, cùng lẽ với `TRUONG_O`:
# nó không phải dữ liệu nhà trường mà là một QUYẾT ĐỊNH VỀ MỨC THA THỨ.
# Cả điểm của nó là: ai muốn khai thêm ngoại lệ thì phải sửa dòng này và
# giải thích vì sao — chứ không lặng lẽ nới cho ca thử xanh lại.
TRAN_NGOAI_LE = 1
# Và trần số SỬA, đếm riêng. Không có nó thì `TRAN_NGOAI_LE` không chặn gì:
# một object ngoại lệ chở được bao nhiêu mục `sua` cũng được, và mỗi mục là
# một chỗ `cauhinh.json` được tha. Đo 26/8/2026: sửa lén 12B3 Toán 3->4 làm
# ca thử 19/21; lén thêm ĐÚNG MỘT mục `sua` vào ngoại lệ CÓ SẴN thì về lại
# 21/21, mà CA 1 vẫn in "Số ngoại lệ còn ít (1) — trần là 1".
TRAN_SUA = 2

# Tên thư mục kho, ghép từ hai mẩu: viết thẳng thì chính bộ dò của CA 4
# sẽ bắt được dòng khai này, và câu báo lỗi thành vô nghĩa.
NEO_KHO = 'luu' + '_tru'
_TEN_HAM_NAY = 'ca_4_khong_dung_lai_ve_B'

# Năm mô-đun mà tệp này KHÔNG được nhắc tới — xem khối chữ đầu tệp.
CAM_NHAP = {'doc_tkb', 'bang_ten', 'kho_tuan', 'sinh_dang', 'doi_chieu'}


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def _doc(ten):
    """Đọc một tệp .json ở gốc dự án. Hỏng -> None, không ném."""
    try:
        with io.open(os.path.join(GOC_DA, ten), encoding='utf-8-sig') as f:
            return json.load(f)
    except Exception:                                    # noqa: BLE001
        return None


def _tu_moc(moc, ap_ngoai_le=True):
    """Mốc -> {(khối, môn): (số tiết, GV)}. Thô RỒI ĐÈ bằng ngoại lệ.

       `ap_ngoai_le=False` trả về con số ĐỌC THÔ từ tệp trường, chưa tha gì.
       CA 3 dùng dạng đó — xem docstring của nó.

       Mọi phép bóc chịu được hình dạng hỏng: một mốc rách phải làm ca thử
       ĐỎ chứ không VỠ (kiểu hỏng số 2).
    """
    ra = {}
    tho = moc.get('doc_tu_tep') if isinstance(moc, dict) else None
    for khoi, cac in (tho or {}).items():
        if not isinstance(cac, list):
            continue
        for muc in cac:
            if isinstance(muc, list) and len(muc) >= 3:
                ra[(khoi, muc[0])] = (muc[2], muc[1])
    for x in ((moc.get('ngoai_le') or []) if (ap_ngoai_le and isinstance(moc, dict))
              else []):
        for s in (x.get('sua') or []) if isinstance(x, dict) else []:
            if not isinstance(s, dict):
                continue
            k = (s.get('lop'), s.get('mon'))
            cu = ra.get(k)
            ra[k] = (s.get('dung_la'), s.get('gv') or (cu[1] if cu else None))
    return {k: v for k, v in ra.items() if v[0]}


def _tu_cau_hinh(cfg):
    """cauhinh.json -> cùng hình dạng. Không ném."""
    ra = {}
    for khoi, cac in ((cfg or {}).get('phan_cong') or {}).items():
        if khoi.startswith('_') or not isinstance(cac, list):
            continue
        for muc in cac:
            if isinstance(muc, list) and len(muc) >= 3:
                ra[(khoi, muc[0])] = (muc[2], muc[1])
    return ra


def _theo_nguoi(bang):
    """{(khối, môn): (tiết, GV)} -> {(khối, GV): tổng tiết}."""
    ra = {}
    for (khoi, _), (n, t) in bang.items():
        if t and isinstance(n, int):
            ra[(khoi, t)] = ra.get((khoi, t), 0) + n
    return ra


# ==========================================================================
def ca_1_dieu_kien_tien_quyet(moc, cfg):
    print('\nCA 1 — điều kiện tiên quyết: có hai vế để so không')
    print('-' * 74)
    kiem(isinstance(moc, dict) and isinstance(cfg, dict),
         'Đọc được cả phan_cong_tuan1.json lẫn cauhinh.json')
    if not (isinstance(moc, dict) and isinstance(cfg, dict)):
        return {}, {}
    a, b = _tu_moc(moc), _tu_cau_hinh(cfg)
    kiem(len(a) > 0, f'Mốc có {len(a)} cặp (khối, môn) — không so rỗng')
    kiem(len(b) > 0, f'cauhinh.json có {len(b)} cặp — không so rỗng')
    ka = {k[0] for k in a}
    kb = {k[0] for k in b}
    kiem(ka == kb,
         f'Hai vế cùng một bộ khối/lớp — mốc thừa {sorted(ka - kb)}, '
         f'thiếu {sorted(kb - ka)}')
    ng = moc.get('ngoai_le') or []
    kiem(len(ng) <= TRAN_NGOAI_LE,
         f'Số ngoại lệ trong mốc còn ít ({len(ng)}) — trần là '
         f'{TRAN_NGOAI_LE}. Mục này để cửa thoát hiểm không lặng lẽ phình '
         'thành cửa chính')
    so_sua = sum(len(x.get('sua') or []) for x in ng if isinstance(x, dict))
    kiem(so_sua <= TRAN_SUA,
         f'Và số chỗ được THA còn ít ({so_sua}) — trần là {TRAN_SUA}. Đếm '
         'riêng, vì một ngoại lệ chở được bao nhiêu mục "sua" cũng được')
    return a, b


def ca_2_truc_lop_mon(a, b):
    print('\nCA 2 — trục (lớp, môn): số tiết và tên giáo viên')
    print('-' * 74)
    if not a or not b:
        kiem(False, 'Không có gì để so — xem CA 1')
        return
    thua = sorted(set(b) - set(a))
    thieu = sorted(set(a) - set(b))
    kiem(not thua and not thieu,
         f'Hai vế cùng một bộ cặp (khối, môn) — cauhinh thừa {thua[:4]}, '
         f'thiếu {thieu[:4]}')
    lech_tiet = [(k, a[k][0], b[k][0]) for k in sorted(set(a) & set(b))
                 if a[k][0] != b[k][0]]
    kiem(not lech_tiet,
         'Số tiết mỗi (khối, môn) khớp mốc — '
         f'{len(lech_tiet)} chỗ lệch: {lech_tiet[:4]}')
    lech_ten = [(k, a[k][1], b[k][1]) for k in sorted(set(a) & set(b))
                if a[k][1] != b[k][1]]
    kiem(not lech_ten,
         'Tên giáo viên mỗi (khối, môn) khớp mốc — '
         f'{len(lech_ten)} chỗ lệch: {lech_ten[:4]}')
    if lech_tiet or lech_ten or thua or thieu:
        print('\n        cauhinh.json ĐÃ ĐỔI so với mốc tuần 1 đối chiếu')
        print('        ngày 26/8/2026 (người duyệt: Anh Lân).')
        print('        Đổi có chủ ý thì cập nhật phan_cong_tuan1.json kèm')
        print('        ngày + người + lý do. ĐỪNG SỬA SỐ CHO KHỚP.')


def ca_3_truc_lop_gv(moc, b):
    """Trục (lớp, GV), dựng từ con số ĐỌC THÔ — KHÔNG áp ngoại lệ nào.

       Bản đầu dùng bảng ĐÃ ĐÈ ngoại lệ, nên câu "không bịt miệng được" là
       SAI: lén thêm một mục `sua` là CA 2 lẫn CA 3 cùng im (đo 26/8/2026,
       19/21 -> 21/21). Nay CA 3 không nhìn `ngoai_le` một lần nào.

       Dùng được con số thô là nhờ một tính chất của chính khuyết tật 12B1:
       cả hai chỗ sửa đều là CÙNG MỘT CÔ (N.Dung), 3 = 2 + 1, nên tổng theo
       (lớp, GV) không đổi. Ngoại lệ nào làm đổi tổng đó sẽ làm mục này ĐỎ —
       và đó là ĐÚNG: nó không còn là "chỉ ghi thiếu một cái nhãn" nữa.
    """
    print('\nCA 3 — trục (lớp, GV): dựng từ SỐ THÔ, không tha gì')
    print('-' * 74)
    a = _tu_moc(moc, ap_ngoai_le=False)
    if not a or not b:
        kiem(False, 'Không có gì để so — xem CA 1')
        return
    x, y = _theo_nguoi(a), _theo_nguoi(b)
    kiem(len(x) > 0 and len(y) > 0,
         f'Có {len(x)} cặp (khối, GV) ở mốc và {len(y)} ở cauhinh')
    lech = [(k, x.get(k), y.get(k)) for k in sorted(set(x) | set(y))
            if x.get(k) != y.get(k)]
    kiem(not lech,
         'Mỗi giáo viên dạy mỗi khối ĐÚNG số tiết ĐỌC THÔ từ tệp trường — '
         f'{len(lech)} chỗ lệch: {lech[:4]}')
    print('        Mục này dựng vế mốc từ con số THÔ, KHÔNG áp một ngoại')
    print('        lệ nào — nên khai thêm ngoại lệ ở CA 2 không bịt miệng')
    print('        được nó. Việc bản của trường ghi thiếu một cái NHÃN MÔN')
    print('        không đụng tới câu "cô này dạy khối này mấy tiết".')


def ca_4_khong_dung_lai_ve_B():
    print('\nCA 4 — chính tệp này KHÔNG dựng lại vế B (soi cây cú pháp)')
    print('-' * 74)
    dd = os.path.abspath(__file__)
    with io.open(dd, encoding='utf-8') as f:
        nguon = f.read()
    try:
        cay = ast.parse(nguon, filename=dd)
    except SyntaxError as e:
        kiem(False, f'Phân tích được chính tệp này -> {e}')
        return
    kiem(True, 'Phân tích được cây cú pháp của chính tệp này')

    nhap = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Import):
            nhap |= {x.name.split('.')[0] for x in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            nhap.add(n.module.split('.')[0])
    dinh = sorted(CAM_NHAP & nhap)
    kiem(not dinh,
         f'KHÔNG nhập mô-đun nào dựng lại được vế B — thấy {dinh}')

    # Hằng chuỗi trỏ vào kho. Hai chỗ phải loại ra, và loại đúng chúng
    # chứ không loại bừa:
    #   · docstring — soi CÂY CÚ PHÁP nên docstring cũng là ast.Constant;
    #   · thân CHÍNH HÀM NÀY — nó chứa tên thư mục kho trong câu thông báo
    #     và trong mẩu mã tự thử, nên không loại thì bộ dò tự bắt mình.
    #     Cái giá phải biết: bộ dò KHÔNG soi được thân hàm này. Chấp nhận,
    #     vì phép kiểm `import` ở trên vẫn phủ cả tệp, và đường thật để
    #     chạm vào kho là nhập mô-đun chứ không phải ghép chuỗi đường dẫn.
    bo_qua = {id(x.value) for x in ast.walk(cay)
              if isinstance(x, ast.Expr) and isinstance(x.value, ast.Constant)}
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == _TEN_HAM_NAY:
            bo_qua |= {id(x) for x in ast.walk(n)
                       if isinstance(x, ast.Constant)}
    kho = [n.value for n in ast.walk(cay)
           if isinstance(n, ast.Constant) and isinstance(n.value, str)
           and id(n) not in bo_qua and NEO_KHO in n.value]
    kiem(not kho, f'KHÔNG có hằng chuỗi trỏ vào thư mục kho — {kho}')

    # Điều kiện tiên quyết: bộ dò phải BIẾT BẮT, không chỉ biết trả rỗng.
    thu = ast.parse('import kho_tuan\nx = "' + NEO_KHO + '/abc"\n')
    n2 = {x.name.split('.')[0] for m in ast.walk(thu)
          if isinstance(m, ast.Import) for x in m.names}
    c2 = [n.value for n in ast.walk(thu)
          if isinstance(n, ast.Constant) and isinstance(n.value, str)
          and NEO_KHO in n.value]
    kiem(bool(CAM_NHAP & n2) and bool(c2),
         'Và bộ dò thật sự bắt được một tệp cố tình vi phạm')


def ca_5_moc_sinh_duoi_dung_bang_ten(moc):
    print('\nCA 5 — mốc sinh dưới ĐÚNG bảng tên đang dùng')
    print('-' * 74)
    if not isinstance(moc, dict):
        kiem(False, 'Không đọc được mốc')
        return
    da_dung = moc.get('gop_da_dung')
    kiem(isinstance(da_dung, dict) and set(da_dung) == {'mon', 'gv'},
         f'Mốc có ghi lại bảng gộp nó được sinh dưới — {type(da_dung).__name__}')
    if not isinstance(da_dung, dict):
        return

    # So SNAPSHOT trong mốc với hai tệp bảng ĐANG DÙNG. Đọc thẳng .json chứ
    # không import bang_ten — vẫn giữ được luật CA 4, mà vẫn bắt được việc
    # ai đó nới bảng gộp rồi quên sinh lại mốc.
    for khoa, ten in (('mon', 'bang_ten_mon.json'), ('gv', 'bang_ten_gv.json')):
        b = _doc(ten) or {}
        hien = {k: (v.get('chuan') if isinstance(v, dict) else v)
                for k, v in (b.get('gop') or {}).items()}
        cu = da_dung.get(khoa)
        kiem(isinstance(cu, dict) and cu == hien,
             f'{ten}: bảng gộp hiện tại KHỚP bảng mốc được sinh dưới — '
             f'mốc {len(cu or {})} cặp, tệp {len(hien)} cặp')

    ng = moc.get('ngoai_le') or []
    kiem(len(ng) > 0, f'Mốc có {len(ng)} ngoại lệ để soi chữ ký')
    thieu = []
    for x in ng:
        if not isinstance(x, dict):
            thieu.append(x)
            continue
        for k in ('ly_do', 'nguoi_duyet', 'ngay', 'mo_ta'):
            if not (isinstance(x.get(k), str) and x[k].strip()):
                thieu.append((x.get('ma'), k))
    kiem(not thieu,
         f'Mọi ngoại lệ có đủ mô tả + lý do + người duyệt + ngày — {thieu}')

    d = moc.get('duyet') or {}
    kiem(bool((d.get('nguoi') or '').strip())
         and bool((d.get('ngay') or '').strip()),
         f'Cả bộ số có chữ ký người duyệt và ngày — {d.get("nguoi")!r} · '
         f'{d.get("ngay")!r}')
    ngn = moc.get('nguon') or {}
    kiem(bool(ngn.get('sha256')) and bool(ngn.get('ban')),
         'và ghi rõ nó đọc ra từ BẢN NÀO (sha256 + tên tệp)')


# ==========================================================================
def main():
    print('=' * 74)
    print(' THỬ: cauhinh.json KHỚP BỘ SỐ PHÂN CÔNG TUẦN 1 ĐÃ ĐỐI CHIẾU')
    print('=' * 74)
    moc = _doc('phan_cong_tuan1.json')
    cfg = _doc('cauhinh.json')
    a, b = ca_1_dieu_kien_tien_quyet(moc, cfg)
    ca_2_truc_lop_mon(a, b)
    ca_3_truc_lop_gv(moc, b)
    ca_4_khong_dung_lai_ve_B()
    ca_5_moc_sinh_duoi_dung_bang_ten(moc)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
    return 1 if hong else 0


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: TRA BẢNG TÊN LÀ SO CHUỖI ĐÚNG Y HỆT — KHÔNG BAO GIỜ "GẦN ĐÚNG"
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_bang_ten.py

 CÁI BẪY THẬT trong dữ liệu nhà trường: khoa có **H.Hiền** (Địa lí, GVCN
 12B2) VÀ **T.T.Hiền** (Sinh học) — hai người khác nhau, cùng phần sau dấu
 chấm cuối. Gộp nhầm là ghi tiết của cô này dưới tên cô kia, trên tờ TKB
 treo ở trường. Cùng hạng bẫy ở bảng môn: `Lịch sử` với `Chuyên đề Lịch sử`.

 ┌──────────────────────────────────────────────────────────────────────┐
 │ VÌ SAO MỤC CANH CHÍNH LÀ **BẢNG BẪY TỔNG HỢP** CHỨ KHÔNG PHẢI CẶP    │
 │ TÊN THẬT — có số đo, và số đo này đã bác bản thiết kế đầu:           │
 │                                                                      │
 │ `chuan(s) = gop.get(chuan_hoa(s), s)`: MỌI phép chuẩn hoá sai chỉ    │
 │ đụng **khoá tra**. `H.Hiền` và `T.T.Hiền` đều KHÔNG phải khoá `gop`  │
 │ nên cả hai rơi vào nhánh `else` và trả về chính nó — hai kết quả vẫn │
 │ khác nhau, **cái bẫy im**. Đo trên 10 bản cài sai: mục "cặp tên      │
 │ thật" bắt được **1**, bảng bẫy tổng hợp bắt được **9**.              │
 │                                                                      │
 │ Nên cặp tên thật vẫn giữ, nhưng ĐỔI VAI: nó canh việc **bảng viết    │
 │ tay có gộp nhầm hai người có thật không** — thứ bảng tổng hợp không  │
 │ bắt được. Hai mục canh hai thứ khác nhau, giữ cả hai.                │
 └──────────────────────────────────────────────────────────────────────┘

 MỐC SO ĐỘC LẬP (nếp hỏng 12): tên thật lấy từ `cauhinh.json`, đích giả do
 chính ca thử đặt. **Không vế nào sinh ra từ `bang_ten.py` hay hai tệp
 bảng**, nên nới `gop` thật không dịch được vế nào.

 KHÔNG GHIM MỘT TÊN LỚP / MÔN / GV NÀO. Mọi tên đọc ra từ `cauhinh.json`
 và hai tệp bảng lúc chạy — xem `tests/thu_ghim_du_lieu.py`.

 SÁU BẤT BIẾN ĐƯỢC CANH:
   CA 1  Điều kiện tiên quyết: có tên thật, có luật gộp, bảng nạp sạch
   CA 2  BẢNG BẪY TỔNG HỢP — không tên thật nào bị kéo về đích giả
   CA 3  `chuan()` không gọi phép biến đổi chuỗi nào (soi cây cú pháp)
   CA 4  Bảng THẬT không gộp nhầm hai tên có thật thành một
   CA 5  Nạp bảng hỏng thì ĐỎ chứ không im: thiếu chữ ký, nối chuỗi, ...
   CA 6  Vế CHUẨN của mọi luật gộp phải là tên CÓ THẬT (`ten_la`)
==========================================================================
"""
import ast
import io
import json
import os
import sys
import tempfile
import unicodedata

GOC_DA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, GOC_DA)

import bang_ten as BT                                            # noqa: E402

KQ = []
DICH_GIA = 'ĐÍCH GIẢ KHÔNG CÓ THẬT '
NGUOI_THU = 'người thử'
NGAY_THU = '2026-01-01'


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


# ==========================================================================
# VỐN TỪ — đọc ra lúc chạy, không chép một tên nào vào đây
# ==========================================================================
def _bo_dau(s):
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                   if unicodedata.category(c) != 'Mn')


# Mỗi phép biến đổi tương ứng MỘT bản cài `chuan()` sai đã từng thấy trong
# đời thật. Tên phép nằm ở vế trái để câu báo lỗi nói được cái gì hỏng.
BIEN_THE = [
    ('khoảng trắng cuối', lambda s: s + ' '),
    ('khoảng trắng đầu', lambda s: ' ' + s),
    ('hạ hoa-thường', lambda s: s.lower()),
    ('nâng hoa', lambda s: s.upper()),
    ('chuẩn hoá NFD', lambda s: unicodedata.normalize('NFD', s)),
    ('bỏ dấu', _bo_dau),
    ('bỏ dấu chấm', lambda s: s.replace('.', '')),
    ('bỏ khoảng trắng giữa', lambda s: s.replace(' ', '')),
    ('phần sau chấm cuối', lambda s: s.split('.')[-1]),
    ('phần trước chấm đầu', lambda s: s.split('.')[0]),
    ('cắt ký tự đầu', lambda s: s[1:]),
    ('cắt ký tự cuối', lambda s: s[:-1]),
]


def ten_that():
    """Mọi tên môn và tên viết tắt GV có thật, đọc từ cauhinh.json."""
    with io.open(os.path.join(GOC_DA, 'cauhinh.json'), encoding='utf-8') as f:
        cfg = json.load(f)
    ra = set()
    for khoi, cac in (cfg.get('phan_cong') or {}).items():
        if khoi.startswith('_') or not isinstance(cac, list):
            continue
        for muc in cac:
            if isinstance(muc, list):
                ra |= {x for x in muc if isinstance(x, str) and x}
    return sorted(ra)


def bang_bay(cac_ten):
    """Sinh bảng bẫy: mọi biến thể của mọi tên thật -> một ĐÍCH GIẢ.

       Bản cài đúng phải trả tên thật về nguyên vẹn (biến thể không phải
       tên thật), và trả đúng đích giả cho từng khoá đã khai. Bản cài nào
       chuẩn hoá khoá tra sẽ kéo tên thật về đích giả -> ĐỎ.

       Trả (dict khoá -> đích, dict tên phép -> số khoá góp được).
    """
    co = set(cac_ten)
    gop, gop_theo_phep = {}, {}
    for ten_phep, phep in BIEN_THE:
        dem = 0
        for t in cac_ten:
            try:
                v = phep(t)
            except Exception:                            # noqa: BLE001
                continue
            # Bỏ biến thể trùng chính nó, trùng một tên thật khác, hoặc rỗng:
            # ba trường hợp đó làm phép khẳng định mất nghĩa chứ không phải
            # bắt được lỗi.
            if not v or v == t or v in co or v in gop:
                continue
            gop[v] = DICH_GIA + str(len(gop))
            dem += 1
        gop_theo_phep[ten_phep] = dem
    return gop, gop_theo_phep


def ghi_bang(tm, ten_tep, gop, biet=(), day_du=True):
    """Ghi một tệp bảng rồi nạp lại QUA `bang_ten.nap_mot()` THẬT.

       Dựng `Bang()` bằng tay là bỏ qua cả tầng kiểm lúc nạp — đúng kiểu
       hỏng số 1 (gọi tắt, bỏ qua tầng cần canh).
    """
    muc = {}
    for k, v in gop.items():
        m = {'chuan': v}
        if day_du:
            m['nguoi_duyet'] = NGUOI_THU
            m['ngay'] = NGAY_THU
        muc[k] = m
    dd = os.path.join(tm, ten_tep)
    with io.open(dd, 'w', encoding='utf-8') as f:
        json.dump({'biet': list(biet), 'gop': muc}, f, ensure_ascii=False)
    return BT.nap_mot(dd, ten_tep)


def cap_dinh_bay(cac_ten):
    """Cặp tên THẬT mà một phép so gần đúng sẽ gộp làm một.

       ⚠ Mục dùng danh sách này CÓ THỂ MẤT KHẢ NĂNG PHÂN BIỆT khi phân
       công đổi (cô H.Hiền hoặc cô T.T.Hiền rời khối 12 là cặp đó biến
       mất). Vì vậy CA 1 khẳng định danh sách khác rỗng, và mục canh chính
       là bảng bẫy tổng hợp chứ không phải danh sách này.
    """
    ra = []
    for i, x in enumerate(cac_ten):
        for y in cac_ten[i + 1:]:
            vi = []
            if x.split('.')[-1] == y.split('.')[-1]:
                vi.append('cùng phần sau chấm cuối')
            if x.endswith(y) or y.endswith(x):
                vi.append('một cái là hậu tố của cái kia')
            if x.replace('.', '') == y.replace('.', ''):
                vi.append('bỏ dấu chấm thì trùng')
            if _bo_dau(x).lower() == _bo_dau(y).lower():
                vi.append('bỏ dấu rồi hạ hoa-thường thì trùng')
            if vi:
                ra.append((x, y, ' · '.join(vi)))
    return ra


# ==========================================================================
def ca_1_dieu_kien_tien_quyet(cac_ten, bm, bg):
    print('\nCA 1 — điều kiện tiên quyết: có gì để canh không')
    print('-' * 74)
    kiem(len(cac_ten) > 0,
         f'Đọc được {len(cac_ten)} tên môn + tên GV từ cauhinh.json')
    kiem(len(bm.gop) > 0 and len(bg.gop) > 0,
         f'Hai bảng thật có luật gộp — môn {len(bm.gop)} · GV {len(bg.gop)}')
    kiem(bm.loi == [] and bg.loi == [],
         f'Hai bảng thật nạp SẠCH — nếu hỏng thì mọi mục dưới đây vô nghĩa. '
         f'môn {bm.loi} · GV {bg.loi}')
    cap = cap_dinh_bay(cac_ten)
    kiem(len(cap) > 0,
         f'Trong dữ liệu thật có {len(cap)} cặp tên dính bẫy so gần đúng — '
         'không có cặp nào thì CA 4 mất khả năng phân biệt')
    for x, y, vi in cap:
        print(f'        {x!r} ~ {y!r}   ({vi})')
    return cap


def ca_2_bang_bay_tong_hop(tm, cac_ten):
    print('\nCA 2 — BẢNG BẪY TỔNG HỢP: tên thật phải đi qua NGUYÊN VẸN')
    print('-' * 74)
    gop, theo_phep = bang_bay(cac_ten)
    b = ghi_bang(tm, 'bay.json', gop)

    kiem(b.loi == [],
         f'Bảng bẫy nạp sạch qua bang_ten.nap_mot() — {b.loi}')
    kiem(len(b.gop) > 0, f'Bảng bẫy có {len(b.gop)} khoá (không soi rỗng)')

    thieu = sorted(k for k, v in theo_phep.items() if v < 1)
    kiem(not thieu,
         f'MỌI phép biến đổi đều góp được khoá bẫy — thiếu: {thieu}')
    for k in sorted(theo_phep):
        print(f'        {k:<24} {theo_phep[k]:>3} khoá')

    # Mục 1: tên THẬT không được kéo về đích giả. Đây là mục bắt mọi phép
    # chuẩn hoá khoá tra.
    hut = [(t, b.chuan(t)) for t in cac_ten if b.chuan(t) != t]
    kiem(not hut,
         f'Không tên thật nào bị kéo về đích giả — {len(hut)} chỗ'
         + (': ' + str(hut[:5]) if hut else ''))

    # Mục 2: khoá đã khai vẫn phải tra ra đúng đích. Thiếu mục này thì một
    # bản cài `chuan()` trả về `s` luôn cũng xanh — nó không kéo ai đi đâu.
    # Bóc bằng `.get()`, KHÔNG `gop[k]`: `b.gop` là khoá do BẢN CÀI (có thể
    # hỏng) đẻ ra, còn `gop` là dict của ca thử. Một bản cài chuẩn hoá khoá
    # LÚC NẠP làm hai bộ khoá lệch nhau, và `gop[k]` khi đó ném KeyError —
    # ca thử VỠ chứ không ĐỎ, CA 3..6 không bao giờ chạy (kiểu hỏng số 2,
    # đo 26/8/2026).
    thieu = sorted(set(gop) - set(b.gop))
    kiem(not thieu,
         f'Mọi khoá khai vào đều còn nguyên sau khi nạp — {len(thieu)} mất'
         + (': ' + str(thieu[:5]) if thieu else ''))
    truot = [k for k in b.gop if b.chuan(k) != gop.get(k)]
    kiem(not truot,
         f'Mọi khoá đã khai đều tra ra đúng đích — {len(truot)} trượt'
         + (': ' + str(truot[:5]) if truot else ''))


def ca_3_chuan_khong_bien_doi_chuoi():
    print('\nCA 3 — chuan() không gọi phép biến đổi chuỗi nào')
    print('-' * 74)
    dd = os.path.join(GOC_DA, 'bang_ten.py')
    with io.open(dd, encoding='utf-8') as f:
        nguon = f.read()
    cay = ast.parse(nguon, filename=dd)
    than = [n for n in ast.walk(cay)
            if isinstance(n, ast.FunctionDef) and n.name == 'chuan']
    kiem(len(than) == 1, f'Tìm thấy đúng một hàm chuan() — {len(than)}')
    if not than:
        return
    # Soi CÂY CÚ PHÁP, không dò chuỗi: chú thích và docstring không lọt vào,
    # nên miễn nhiễm với kiểu hỏng số 4 (khớp phải dòng chú thích).
    goi = set()
    for n in ast.walk(than[0]):
        if isinstance(n, ast.Attribute):
            goi.add(n.attr)
        elif isinstance(n, ast.Name):
            goi.add(n.id)
    cam = {'strip', 'lstrip', 'rstrip', 'lower', 'upper', 'casefold',
           'title', 'replace', 'split', 'rsplit', 'normalize',
           'unicodedata', 'startswith', 'endswith', 'translate', 'difflib',
           'get_close_matches', 'SequenceMatcher'}
    dinh = sorted(cam & goi)
    kiem(not dinh,
         f'chuan() không nhắc tới phép biến đổi/so gần đúng nào — {dinh}')


def ca_4_bang_that_khong_gop_nham(cap, bm, bg):
    print('\nCA 4 — bảng THẬT không gộp nhầm hai tên có thật thành một')
    print('-' * 74)
    nham = []
    for x, y, vi in cap:
        for b in (bm, bg):
            if b.chuan(x) == b.chuan(y):
                nham.append((b.ten, x, y, vi))
    kiem(not nham,
         f'Không cặp nào bị gộp làm một — {len(nham)} cặp'
         + (': ' + str(nham) if nham else ''))
    # Điều kiện tiên quyết riêng của CA này: phải có cặp để hỏi.
    kiem(len(cap) > 0,
         f'Và có {len(cap)} cặp để hỏi — 0 cặp là mục trên xanh mà không '
         'canh gì')


def ca_5_bang_hong_thi_do_chu_khong_im(tm, cac_ten):
    print('\nCA 5 — bảng hỏng thì ĐỎ chứ không im lặng')
    print('-' * 74)
    mau = cac_ten[0] if cac_ten else 'x'
    mau2 = cac_ten[1] if len(cac_ten) > 1 else 'y'

    b = ghi_bang(tm, 'thieu.json', {mau + '~': mau2}, day_du=False)
    kiem(b.loi and not b.gop,
         f'Thiếu chữ ký người duyệt -> bảng RỖNG và có lỗi ({len(b.loi)} câu)')

    b = ghi_bang(tm, 'noi.json', {mau + '~': mau + '~~', mau + '~~': mau2})
    kiem(b.loi and not b.gop,
         f'Gộp NỐI CHUỖI (a->b, b->c) -> RỖNG và có lỗi ({len(b.loi)} câu)')

    b = ghi_bang(tm, 'vong.json', {mau + '~': mau + '~'})
    kiem(b.loi and not b.gop,
         f'Mục trỏ về chính nó -> RỖNG và có lỗi ({len(b.loi)} câu)')

    dd = os.path.join(tm, 'rach.json')
    io.open(dd, 'w', encoding='utf-8').write('{ đây không phải JSON')
    b = BT.nap_mot(dd, 'rach.json')
    kiem(b.loi and not b.gop and not b.biet,
         'Tệp rách -> RỖNG và có lỗi, KHÔNG NÉM')

    dd = os.path.join(tm, 'day.json')
    io.open(dd, 'w', encoding='utf-8').write('[1, 2, 3]')
    b = BT.nap_mot(dd, 'day.json')
    kiem(b.loi and not b.gop, 'Gốc tệp là một dãy -> RỖNG và có lỗi')

    b = BT.nap_mot(os.path.join(tm, 'khong-he-co.json'), 'khong-he-co.json')
    kiem(not b.loi and not b.gop and not b.biet,
         'THIẾU TỆP thì im lặng và rỗng — đây là cài đặt thường, không lỗi')


def ca_6_ve_chuan_phai_co_that(cac_ten, bm, bg):
    print('\nCA 6 — vế CHUẨN của mọi luật gộp phải là tên CÓ THẬT')
    print('-' * 74)
    co = set(cac_ten)
    la = sorted(set(bm.ten_la(co)) | set(bg.ten_la(co)))
    kiem(not la,
         'Mọi vế chuẩn đều có trong cauhinh.json — '
         f'{len(la)} tên không có thật: {la}')
    # Điều kiện tiên quyết: bộ dò phải BIẾT BẮT, không chỉ biết trả rỗng.
    bia = BT.Bang('thử', gop={(cac_ten[0] if cac_ten else 'x') + '~':
                              'TÊN KHÔNG CÓ THẬT'})
    kiem(bia.ten_la(co) == ['TÊN KHÔNG CÓ THẬT'],
         'Và ten_la() thật sự bắt được một vế chuẩn bịa ra')

    # VẾ LẠ cũng phải soi, không chỉ vế chuẩn. Một luật mà vế LẠ lại là tên
    # CÓ THẬT thì nó XOÁ SỔ một môn / một giáo viên ở mọi lượt đọc — đo
    # 26/8/2026: thêm '"Toán học" -> "Chuyên đề Toán"' làm tệp tuần 1 tụt từ
    # 77 xuống 71 cặp, mà bốn bộ thử vẫn xanh trọn (chỉ cần cập nhật
    # gop_da_dung là hết dấu vết).
    xoa_so = sorted({k for b2 in (bm, bg) for k in b2.gop if k in co})
    kiem(not xoa_so,
         'Không luật gộp nào lấy một tên CÓ THẬT làm vế lạ — '
         f'{len(xoa_so)} tên bị xoá sổ: {xoa_so}')


# ==========================================================================
def ca_7_ghim_khoa_duyet(tm):
    print('\nCA 7 — GHIM LITERAL `KHOA_DUYET`: chữ ký người duyệt gộp tên')
    print('-' * 74)
    # Ghim literal. `KHOA_DUYET` là lý do DUY NHẤT khiến một mục gộp phải là
    # object chứ không phải cặp chuỗi: không phép đo nào chứng minh được
    # `T.Hiền` với `T.T.Hiền` là một người — chỉ có chữ ký người duyệt.
    # Đó là một QUYẾT ĐỊNH VỀ TRÁCH NHIỆM, không phải chi tiết kỹ thuật.
    DUYET_DA_CHOT = ('nguoi_duyet', 'ngay')
    kiem(tuple(BT.KHOA_DUYET) == DUYET_DA_CHOT,
         f'KHOA_DUYET ĐÚNG BẰNG bộ đã chốt — {tuple(BT.KHOA_DUYET)}')

    # VÀ HÀNH VI, cho TỪNG khoá một. Mục ghim ở trên bắt được việc GỌT
    # DANH SÁCH; mục dưới bắt được việc bỏ phép kiểm mà vẫn giữ danh sách.
    # Bản cũ chỉ có một mục "thiếu chữ ký -> bảng rỗng", và nó chỉ ĐỎ khi
    # xoá SẠCH cả hai khoá: đo 26/8/2026, bỏ riêng `'ngay'` cho 23/23,
    # không mục nào đỏ. Bắt được khi xoá sạch, không bắt được khi gọt dần.
    sot = []
    for thieu in DUYET_DA_CHOT:
        muc = {'chuan': 'Tên Chuẩn Thử', 'nguoi_duyet': 'người thử',
               'ngay': '2026-08-26'}
        muc.pop(thieu)
        dd = os.path.join(tm, f'thieu-{thieu}.json')
        with io.open(dd, 'w', encoding='utf-8') as f:
            json.dump({'biet': [], 'gop': {'chuỗi lạ thử': muc}}, f,
                      ensure_ascii=False)
        b = BT.nap_mot(dd, 'bảng thử')
        if not (b.loi and not b.gop):
            sot.append(thieu)
    kiem(not sot,
         f'Thiếu BẤT KỲ khoá nào trong {len(DUYET_DA_CHOT)} khoá -> bảng '
         f'RỖNG và có lỗi — chưa bắt được: {sot}')


def main():
    print('=' * 74)
    print(' THỬ: TRA BẢNG TÊN — SO CHUỖI ĐÚNG Y HỆT, KHÔNG "GẦN ĐÚNG"')
    print('=' * 74)
    cac_ten = ten_that()
    bm, bg = BT.nap(GOC_DA)
    with tempfile.TemporaryDirectory(prefix='thu_bang_ten_') as tm:
        cap = ca_1_dieu_kien_tien_quyet(cac_ten, bm, bg)
        ca_2_bang_bay_tong_hop(tm, cac_ten)
        ca_3_chuan_khong_bien_doi_chuoi()
        ca_4_bang_that_khong_gop_nham(cap, bm, bg)
        ca_5_bang_hong_thi_do_chu_khong_im(tm, cac_ten)
        ca_6_ve_chuan_phai_co_that(cac_ten, bm, bg)
        ca_7_ghim_khoa_duyet(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
    return 1 if hong else 0


if __name__ == '__main__':
    sys.exit(main())

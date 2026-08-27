#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: BỘ ĐỌC TKB (doc_tkb.py) VÀ KHO TUẦN (kho_tuan.py)
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_kho_tuan.py

 CA THỬ TỰ DỰNG MỌI TỆP .xlsx CỦA MÌNH, không đụng tệp nào của trường và
 không đọc `cauhinh.json` để lấy tên. Tên lớp/môn/GV trong đây là tên BỊA
 (`9Z1`, `Môn Thử`, `T.Thử`) — cố ý KHÔNG khớp gì trong dữ liệu nhà trường,
 để ca thử không bao giờ có ý kiến về dữ liệu thật. Xem `NHAP_A` trong
 `tests/thu_phien.py` và `tests/thu_ghim_du_lieu.py`.

 SÁU BẤT BIẾN ĐƯỢC CANH:
   CA 1  Đọc đúng: ô -> (lớp, thứ, tiết, môn, GV), tách ở ngoặc CUỐI CÙNG
   CA 2  Tệp HỎNG THẬT -> `loi` có nội dung, phần còn lại RỖNG, KHÔNG NÉM
   CA 3  Định nghĩa `loi`: Thứ 7 / lệch ngày / lệch đếm / tên lạ KHÔNG vào `loi`
   CA 4  KHÔNG BAO GIỜ ĐÈ, và trùng SHA-256 thì TỪ CHỐI không ghi một chữ
   CA 5  Dấu bộ đọc đi theo từng bản tách
   CA 6  Phiếu hỏng thì DỪNG, không ghi đè lên nó
   CA 7  Bản "sai" KHÔNG BAO GIỜ ra được đường đăng, dù gõ đúng mã tuần
   CA 8  So một tệp với một bản đã lưu — chỉ đọc, đếm đúng số ô khác
   CA 9  Lệnh `so` in VỪA MÀN HÌNH ĐIỆN THOẠI: hẹp, cắt ở 20 ô
   CA 10 Khuyết tật ĐÃ BIẾT: NỐI THÊM, không đè; không đụng tệp gốc
   CA 11 Lệnh `doi-chieu`: CHỈ ĐỌC, có áp bảng tên, thấy đúng chỗ lệch
==========================================================================
"""
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import doc_tkb as D                                              # noqa: E402
import kho_tuan as K                                             # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def dat_dong_ho_canh(giay=180):
    """Bộ thử không bao giờ được phép TREO — hết giờ thì ĐỎ. Xem CLAUDE.md."""
    def bao():
        time.sleep(giay)
        print(f'\n[HẾT GIỜ] Quá {giay} giây — coi như ĐỎ, thoát.', flush=True)
        os._exit(1)
    threading.Thread(target=bao, daemon=True).start()


# ==========================================================================
# DỰNG TỆP .xlsx TỐI THIỂU — đủ để doc_tkb.py đọc, và bẻ được từng mảnh
# ==========================================================================
CT = '''<?xml version="1.0" encoding="UTF-8"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
</Types>'''

REL_GOC = '''<?xml version="1.0" encoding="UTF-8"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>
</Relationships>'''

NS_M = 'http://schemas.openxmlformats.org/spreadsheetml/2006/main'
NS_RR = 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'


def _thoat(s):
    return (s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))


def dung_xlsx(duong_dan, o, sheet='Khối 12', sheet_them=None,
              bo_shared=False, bo_sheet_xml=False, rac=False):
    """Dựng một .xlsx tối thiểu. `o` = {'D8': 'Môn Thử (T.Thử)', 'D43': '=COUNTA(D8:D42)'}.

       Giá trị bắt đầu bằng '=' thành CÔNG THỨC, còn lại thành chuỗi dùng chung.
       Các cờ `bo_*` để bẻ tệp cho CA 2.
    """
    chuoi, chi_so = [], {}
    for v in o.values():
        if not str(v).startswith('=') and v not in chi_so:
            chi_so[v] = len(chuoi)
            chuoi.append(v)

    theo_hang = {}
    for ten, v in o.items():
        h = int(''.join(c for c in ten if c.isdigit()))
        theo_hang.setdefault(h, []).append((ten, v))
    hang = []
    for h in sorted(theo_hang):
        oo = ''
        for ten, v in sorted(theo_hang[h]):
            if str(v).startswith('='):
                oo += f'<c r="{ten}"><f>{_thoat(str(v)[1:])}</f><v>0</v></c>'
            else:
                oo += f'<c r="{ten}" t="s"><v>{chi_so[v]}</v></c>'
        hang.append(f'<row r="{h}">{oo}</row>')
    sheet_xml = (f'<?xml version="1.0" encoding="UTF-8"?><worksheet '
                 f'xmlns="{NS_M}"><sheetData>{"".join(hang)}</sheetData></worksheet>')

    ss = (f'<?xml version="1.0" encoding="UTF-8"?><sst xmlns="{NS_M}" '
          f'count="{len(chuoi)}" uniqueCount="{len(chuoi)}">'
          + ''.join(f'<si><t>{_thoat(c)}</t></si>' for c in chuoi) + '</sst>')

    ds = [(sheet, 'rId1')]
    if sheet_them:
        ds.append((sheet_them, 'rId2'))
    wb = (f'<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="{NS_M}" '
          f'xmlns:r="{NS_RR}"><sheets>'
          + ''.join(f'<sheet name="{_thoat(n)}" sheetId="{i+1}" r:id="{r}"/>'
                    for i, (n, r) in enumerate(ds))
          + '</sheets></workbook>')
    rels = (f'<?xml version="1.0" encoding="UTF-8"?><Relationships '
            f'xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            + ('<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/'
               'officeDocument/2006/relationships/worksheet" '
               'Target="worksheets/sheet2.xml"/>' if sheet_them else '')
            + '<Relationship Id="rId9" Type="http://schemas.openxmlformats.org/'
            'officeDocument/2006/relationships/sharedStrings" '
            'Target="sharedStrings.xml"/></Relationships>')

    with zipfile.ZipFile(duong_dan, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CT)
        z.writestr('_rels/.rels', REL_GOC)
        z.writestr('xl/workbook.xml', wb)
        z.writestr('xl/_rels/workbook.xml.rels', rels)
        if not bo_sheet_xml:
            z.writestr('xl/worksheets/sheet1.xml',
                       'khong-phai-xml <<<' if rac else sheet_xml)
        if sheet_them:
            z.writestr('xl/worksheets/sheet2.xml', sheet_xml)
        if not bo_shared:
            z.writestr('xl/sharedStrings.xml', ss)
    return duong_dan


def o_mau(so_tiet=3, tuan='TUẦN 9 (05/1/2026-10/1/2026)', dong_dau=8):
    """Một bộ ô đủ dùng: vài tiết ở cột D, và sáu ô tổng đúng chuẩn."""
    o = {'A3': 'THỜI KHÓA BIỂU THỬ', 'A4': tuan}
    for i in range(so_tiet):
        o[f'D{dong_dau + i}'] = f'Môn Thử {i + 1} (T.Thử)'
    for c in 'DEFGHI':
        o[f'{c}43'] = f'=COUNTA({c}8:{c}42)'
    return o


# ==========================================================================
def ca_1_doc_dung(tm):
    print('\nCA 1 — đọc đúng ô, tách môn/GV ở ngoặc CUỐI CÙNG')
    print('-' * 74)
    t = dung_xlsx(os.path.join(tm, 'a.xlsx'), o_mau(so_tiet=3))
    r = D.doc(t)
    kiem(isinstance(r, dict), f'doc() trả dict — {type(r).__name__}')
    kiem(r.get('loi') == [], f'Tệp lành thì loi RỖNG — {r.get("loi")}')
    o = r.get('o') or []
    kiem(len(o) > 1, f'Đọc được {len(o)} ô')
    if o:
        d = o[0]
        kiem(d.get('thu') == 2 and d.get('tiet') == 6,
             f'Ô đầu vùng là Thứ 2 tiết 6 — thứ {d.get("thu")} tiết {d.get("tiet")}')
        kiem(d.get('gv') == 'T.Thử', f'Tách được GV — {d.get("gv")!r}')
        kiem(d.get('tho') and '(' in d['tho'],
             'và giữ NGUYÊN VĂN chuỗi gốc ở khoá "tho"')

    # ngoặc cuối cùng, kể cả khi thiếu dấu cách hoặc có ngoặc trong tên
    for chuoi, mon, gv in (
            ('Địa lí(H.Thử)', 'Địa lí', 'H.Thử'),
            ('Ngữ văn (H.Thử)', 'Ngữ văn', 'H.Thử'),
            ('Môn (có ngoặc) (T.Thử)', 'Môn (có ngoặc)', 'T.Thử'),
            ('SHCN', 'SHCN', None)):
        a, b = D.tach_mon_gv(chuoi)
        kiem((a, b) == (mon, gv), f'{chuoi!r} -> ({a!r}, {b!r})')

    kiem(D.tach_khoang_ngay('TUẦN 9 (05/1/2026-10/1/2026)').get('tu')
         == '2026-01-05', 'Đọc được ngày đầu từ chuỗi tuần')
    kiem(D.tach_khoang_ngay('').get('tho') == '',
         'Chuỗi tuần rỗng -> vẫn trả dict, không ném')
    kiem(D.tach_khoang_ngay('TUẦN 9 (chưa điền ngày)').get('tu') is None,
         'Chuỗi tuần không có ngày -> tu = None, không đoán')


def ca_2_tep_hong_thi_do_chu_khong_nem(tm):
    print('\nCA 2 — tệp HỎNG THẬT: loi có nội dung, phần còn lại RỖNG, KHÔNG NÉM')
    print('-' * 74)

    def thu(ten, dung_tep, mo_ta):
        try:
            r = dung_tep()
        except BaseException as e:                      # noqa: BLE001
            kiem(False, f'{mo_ta} -> NÉM {type(e).__name__}: {e}')
            return
        if not isinstance(r, dict):
            kiem(False, f'{mo_ta} -> trả {type(r).__name__}, không phải dict')
            return
        loi = r.get('loi')
        kiem(isinstance(loi, list) and len(loi) > 0,
             f'{mo_ta} -> loi có nội dung ({len(loi or [])} câu)')
        rong = all(not (r.get(k) or []) for k in
                   ('o', 'ngoai_mo_hinh', 'o_tong', 'lech_dem', 'ten_mon_la'))
        kiem(rong, f'{mo_ta} -> mọi trường dữ liệu RỖNG')
        if loi:
            print(f'         "{loi[0][:96]}"')

    # (c) — đúng ca người dùng đòi: zip THIẾU sharedStrings
    thu('a', lambda: D.doc(dung_xlsx(os.path.join(tm, 'b1.xlsx'), o_mau(),
                                     bo_shared=True, bo_sheet_xml=True)),
        'zip thiếu sharedStrings VÀ thiếu sheet xml')

    p = os.path.join(tm, 'b2.xlsx')
    io.open(p, 'w', encoding='utf-8').write('đây không phải zip')
    thu('b', lambda: D.doc(p), 'tệp không phải zip')

    thu('c', lambda: D.doc(os.path.join(tm, 'khong-co-that.xlsx')),
        'tệp không tồn tại')

    thu('d', lambda: D.doc(dung_xlsx(os.path.join(tm, 'b3.xlsx'), o_mau(),
                                     sheet='Sheet1')),
        'không có sheet "Khối 12"')

    thu('e', lambda: D.doc(dung_xlsx(os.path.join(tm, 'b4.xlsx'), o_mau(),
                                     rac=True)),
        'sheet xml là rác, không phân tích được')

    p = os.path.join(tm, 'b5.xlsx')
    with zipfile.ZipFile(p, 'w') as z:
        z.writestr('linh/tinh.txt', 'zip hợp lệ nhưng không phải bảng tính')
    thu('f', lambda: D.doc(p), 'zip hợp lệ nhưng thiếu xl/workbook.xml')

    # Câu từ chối phải CHỈ RA sheet nào đang có — không thì người dùng mù
    r = D.doc(dung_xlsx(os.path.join(tm, 'b6.xlsx'), o_mau(), sheet='Sheet1'))
    kiem(any('Sheet1' in x for x in (r.get('loi') or [])),
         'Câu từ chối nêu ĐÍCH DANH sheet đang có trong tệp')

    # zip thiếu sharedStrings NHƯNG sheet còn: đọc được công thức -> KHÔNG phải lỗi
    r = D.doc(dung_xlsx(os.path.join(tm, 'b7.xlsx'), o_mau(), bo_shared=True))
    kiem(isinstance(r, dict) and r.get('loi') == [],
         'Thiếu sharedStrings mà sheet còn công thức -> vẫn đọc được, không kêu oan')


def ca_3_dinh_nghia_loi(tm):
    print('\nCA 3 — Thứ 7 / lệch ngày / lệch đếm / tên lạ KHÔNG được vào `loi`')
    print('-' * 74)
    o = o_mau(so_tiet=2)
    o['D35'] = 'Môn Thử 9 (T.Thử)'          # vùng Thứ 7, mô hình không có
    o['D43'] = '=COUNTA(D10:D42)'           # vùng đếm sai kiểu tệp của trường
    t = dung_xlsx(os.path.join(tm, 'c.xlsx'), o, sheet_them='SỔ RIÊNG')
    r = D.doc(t, ten_mon_biet={'Một Môn Khác Hẳn'})

    kiem(r.get('loi') == [],
         f'`loi` vẫn RỖNG — đây là định nghĩa của trường đó. loi={r.get("loi")}')
    kiem(len(r.get('ngoai_mo_hinh') or []) > 0,
         f'Chữ ở vùng Thứ 7 vào `ngoai_mo_hinh` — '
         f'{len(r.get("ngoai_mo_hinh") or [])} ô')
    kiem(any('D35' == x.get('o') for x in (r.get('ngoai_mo_hinh') or [])),
         'và chỉ đích danh ô D35')
    kiem(len(r.get('lech_dem') or []) > 0,
         f'Vùng COUNTA sai vào `lech_dem` — {len(r.get("lech_dem") or [])} chỗ')
    kiem(any('bỏ sót 2 dòng' in x for x in (r.get('lech_dem') or [])),
         'và nói đúng bỏ sót MẤY dòng')
    kiem(len(r.get('ten_mon_la') or []) > 0,
         f'Tên môn chưa duyệt vào `ten_mon_la` — {r.get("ten_mon_la")}')
    kiem((r.get('sheet_khac') or []) == ['SỔ RIÊNG'],
         f'Sheet khác được nêu ra — {r.get("sheet_khac")}')

    # KHÔNG gộp: chuỗi lạ vẫn nằm nguyên trong `o`
    mon = {x.get('mon') for x in (r.get('o') or [])}
    kiem(all(m in mon for m in (r.get('ten_mon_la') or [])),
         'Tên lạ vẫn nằm NGUYÊN VĂN trong dữ liệu, không bị gộp hay bỏ')

    # không truyền bảng tên -> không kêu tên lạ (chưa có gì để so)
    r2 = D.doc(t)
    kiem((r2.get('ten_mon_la') or []) == [],
         'Không đưa bảng tên môn -> không kêu tên lạ oan')


def ca_4_khong_de_va_tu_choi_trung(tm):
    print('\nCA 4 — KHÔNG BAO GIỜ ĐÈ, và trùng SHA-256 thì TỪ CHỐI')
    print('-' * 74)
    goc = os.path.join(tm, 'kho')
    t = dung_xlsx(os.path.join(tm, 'd.xlsx'), o_mau())
    MA = '2026-01-05'                       # một Thứ Hai, không dính dữ liệu thật

    ok, cau = K.kiem_ma_tuan(MA)
    kiem(ok and not cau, f'Mã tuần {MA} hợp lệ và đúng Thứ Hai — {cau}')
    ok2, cau2 = K.kiem_ma_tuan('2026-01-04')
    kiem(ok2 and cau2, 'Ngày KHÔNG phải Thứ Hai -> vẫn cho, nhưng CẢNH BÁO')
    kiem(K.kiem_ma_tuan('TUẦN 1')[0] is False,
         'Nhãn chữ "TUẦN 1" KHÔNG được dùng làm mã tuần')
    kiem(K.kiem_ma_tuan('2026-02-30')[0] is False, 'Ngày không có thật -> chặn')

    a = K.them_ban(goc, MA, t, 'người thử', 'lần đầu')
    kiem(a.get('ok') is True, f'Lưu được bản đầu — {a.get("cau")}')

    b = K.them_ban(goc, MA, t, 'người khác', 'nạp lại y hệt')
    kiem(b.get('ok') is False, 'Nạp lại tệp TRÙNG -> TỪ CHỐI')
    kiem('TỪ CHỐI' in (b.get('cau') or ''), 'và nói rõ là từ chối')
    tr = b.get('trung') or {}
    kiem(tr.get('nguoi_luu') == 'người thử',
         f'và chỉ ra bản trùng là của ai — {tr.get("nguoi_luu")!r}')
    kiem(tr.get('gio_luu'), f'và lưu lúc nào — {tr.get("gio_luu")}')

    p, _ = K.doc_phieu_ky(goc, MA)
    kiem(isinstance(p, dict) and len(p.get('ban') or []) == 1,
         f'Phiếu vẫn ĐÚNG MỘT bản — không ghi thêm một chữ nào '
         f'({len(((p or {}).get("ban")) or [])})')

    # tệp KHÁC nội dung thì lưu được, và KHÔNG đè lên bản cũ
    t2 = dung_xlsx(os.path.join(tm, 'e.xlsx'), o_mau(so_tiet=4))
    c = K.them_ban(goc, MA, t2, 'người thử', 'bản sửa')
    kiem(c.get('ok') is True, 'Tệp khác nội dung -> lưu được')
    p, _ = K.doc_phieu_ky(goc, MA)
    ban = (p or {}).get('ban') or []
    kiem(len(ban) == 2, f'Phiếu nay có 2 bản — {len(ban)}')
    ten = [x.get('tep') for x in ban]
    kiem(len(set(ten)) == len(ten), f'Hai bản HAI TÊN KHÁC NHAU — {ten}')
    con = os.listdir(os.path.join(goc, MA, 'ban'))
    kiem(len(con) == 2, f'Và trên đĩa có đúng 2 tệp, không cái nào bị đè — {len(con)}')

    # --- ĐƯỜNG VA CHẠM TÊN: cùng một GIỜ LƯU và cùng một TÊN GỐC ---
    # Bản đầu của ca này XANH cả khi bỏ vòng chống va chạm, vì hai tệp trên
    # có tên gốc khác nhau nên tên đích vốn đã khác. Phải ép cho TRÙNG tên
    # mới chạm được vào vòng đó. `khi=` ghim luôn giây, không trông vào việc
    # máy chạy đủ nhanh — ca thử không được phụ thuộc tốc độ máy.
    import datetime
    KHI = datetime.datetime(2026, 1, 5, 8, 0, 0)
    va = os.path.join(tm, 'va')
    os.makedirs(os.path.join(va, 'x1'), exist_ok=True)
    os.makedirs(os.path.join(va, 'x2'), exist_ok=True)
    v1 = dung_xlsx(os.path.join(va, 'x1', 'cung_ten.xlsx'), o_mau(so_tiet=6))
    v2 = dung_xlsx(os.path.join(va, 'x2', 'cung_ten.xlsx'), o_mau(so_tiet=7))
    g1 = K.them_ban(goc, MA, v1, 'người thử', khi=KHI)
    g2 = K.them_ban(goc, MA, v2, 'người thử', khi=KHI)
    kiem(g1.get('ok') and g2.get('ok'),
         'Hai tệp CÙNG TÊN GỐC, CÙNG GIÂY, khác nội dung -> lưu được cả hai')
    n1, n2 = (g1.get('ban') or {}).get('tep'), (g2.get('ban') or {}).get('tep')
    kiem(n1 and n2 and n1 != n2,
         f'và nhận HAI TÊN KHÁC NHAU — {n1} / {n2}')
    if n1 and n2:
        d1 = os.path.join(goc, MA, n1)
        d2 = os.path.join(goc, MA, n2)
        kiem(os.path.exists(d1) and os.path.exists(d2),
             'Cả hai tệp còn trên đĩa')
        kiem(os.path.exists(d1) and os.path.exists(d2)
             and os.path.getsize(d1) != os.path.getsize(d2),
             'và nội dung KHÁC nhau — bản trước KHÔNG bị đè')
    con2 = os.listdir(os.path.join(goc, MA, 'ban'))
    kiem(len(con2) == 4, f'Thư mục ban/ nay có đúng 4 tệp — {len(con2)}')

    kiem(K.them_ban(goc, MA, t2, '')['ok'] is False,
         'Thiếu tên người lưu -> từ chối')
    kiem(K.them_ban(goc, MA, os.path.join(tm, 'khong-co.xlsx'), 'ai đó')['ok']
         is False, 'Tệp không tồn tại -> từ chối, không ném')
    kiem(K.them_ban(goc, 'TUẦN 1', t2, 'ai đó')['ok'] is False,
         'Mã tuần sai dạng -> từ chối, không ném')

    # Số bản KHÔNG ghim cứng: suy từ chính phiếu, để thêm mục thử ở trên
    # không làm dòng này đỏ oan.
    p2, _ = K.doc_phieu_ky(goc, MA)
    cho_doi = len((p2 or {}).get('ban') or [])
    ds = K.liet_ke(goc)
    kiem(cho_doi > 1, f'Phiếu có {cho_doi} bản (phải > 1 thì phép so mới có nghĩa)')
    kiem(len(ds) == 1 and ds[0].get('so_ban') == cho_doi,
         f'liet_ke() đếm khớp phiếu — {[(x["ma_tuan"], x["so_ban"]) for x in ds]}')
    kiem(K.liet_ke(os.path.join(tm, 'kho-chua-co')) == [],
         'Kho chưa tồn tại -> liet_ke() trả [], không ném')


def ca_5_dau_bo_doc(tm):
    print('\nCA 5 — mỗi bản tách mang DẤU của bộ đọc đã sinh ra nó')
    print('-' * 74)
    d = D.dau_bo_doc()
    kiem(isinstance(d, dict) and d.get('phien_ban'),
         f'dau_bo_doc() có phiên bản — {d.get("phien_ban")!r}')
    kiem(d.get('bam_ma') and len(d['bam_ma']) > 1,
         f'và băm mã nguồn — {d.get("bam_ma")!r}')

    goc = os.path.join(tm, 'kho2')
    t = dung_xlsx(os.path.join(tm, 'f.xlsx'), o_mau())
    r = D.doc(t)
    a = K.them_ban(goc, '2026-01-05', t, 'người thử', tach=r)
    kiem(a.get('ok') is True, 'Lưu kèm bản tách')
    ban = (a.get('ban') or {})
    kiem((ban.get('bo_doc') or {}).get('bam_ma') == d.get('bam_ma'),
         'Phiếu ghi đúng dấu bộ đọc')
    dt = ban.get('tach')
    kiem(dt, f'Phiếu trỏ tới tệp tách — {dt}')
    if dt:
        pt = os.path.join(goc, '2026-01-05', dt)
        kiem(os.path.exists(pt), 'Tệp tách có thật trên đĩa')
        try:
            with io.open(pt, encoding='utf-8') as f:
                x = json.load(f)
            kiem((x.get('bo_doc') or {}).get('bam_ma') == d.get('bam_ma'),
                 'và trong tệp tách cũng có dấu đó')
        except Exception as e:                          # noqa: BLE001
            kiem(False, f'Đọc lại tệp tách -> {type(e).__name__}: {e}')

    b = K.them_ban(goc, '2026-01-05', t, 'người thử')
    kiem(b.get('ok') is False and (b.get('ban') is None),
         'Không truyền tach -> vẫn từ chối vì trùng, không sinh tệp tách')


def ca_6_phieu_hong_thi_dung(tm):
    print('\nCA 6 — phiếu HỎNG thì DỪNG, tuyệt đối không ghi đè lên nó')
    print('-' * 74)
    goc = os.path.join(tm, 'kho3')
    MA = '2026-01-05'
    t = dung_xlsx(os.path.join(tm, 'g.xlsx'), o_mau())
    kiem(K.them_ban(goc, MA, t, 'người thử').get('ok') is True, 'Lưu bản đầu')

    dd = K.duong_phieu(goc, MA)
    truoc = io.open(dd, encoding='utf-8').read()
    io.open(dd, 'w', encoding='utf-8').write('{ đây không phải JSON')

    p, loi = K.doc_phieu_ky(goc, MA)
    kiem(p is None and loi, f'doc_phieu_ky() báo hỏng, không ném — {bool(loi)}')
    kiem(K.doc_phieu(goc, MA) is None, 'doc_phieu() trả None, không ném')

    t2 = dung_xlsx(os.path.join(tm, 'h.xlsx'), o_mau(so_tiet=5))
    r = K.them_ban(goc, MA, t2, 'người thử')
    kiem(r.get('ok') is False, 'them_ban() DỪNG khi phiếu hỏng')
    kiem('KHÔNG ghi đè' in (r.get('cau') or ''), 'và nói rõ vì sao dừng')
    kiem(io.open(dd, encoding='utf-8').read() != truoc
         and 'JSON' in io.open(dd, encoding='utf-8').read(),
         'Phiếu hỏng còn NGUYÊN — không bị ghi đè')

    ds = K.liet_ke(goc)
    kiem(len(ds) == 1 and ds[0].get('loi'),
         'liet_ke() vẫn chạy và KHAI ra tuần có phiếu hỏng')

    # sai cấu trúc (JSON hợp lệ nhưng không phải phiếu) cũng phải chặn
    io.open(dd, 'w', encoding='utf-8').write('[1, 2, 3]')
    kiem(K.them_ban(goc, MA, t2, 'người thử').get('ok') is False,
         'Phiếu là JSON hợp lệ nhưng sai cấu trúc -> vẫn DỪNG')


# ==========================================================================
def ca_7_ban_sai_khong_ra_duoc_duong_dang(tm):
    print('\nCA 7 — bản "sai" KHÔNG ra được đường đăng, dù gõ ĐÚNG mã tuần')
    print('-' * 74)
    goc = os.path.join(tm, 'kho7')
    MA = '2026-01-05'
    t1 = dung_xlsx(os.path.join(tm, 'k1.xlsx'), o_mau(so_tiet=3))
    t2 = dung_xlsx(os.path.join(tm, 'k2.xlsx'), o_mau(so_tiet=4))

    # --- mặc định là "chua_ro", và "chua_ro" cũng KHÔNG ra được ---
    a = K.them_ban(goc, MA, t1, 'người thử')
    kiem(a.get('ok') is True, 'Lưu bản đầu')
    kiem(K.trang_thai_cua(a.get('ban') or {}) == K.TRANG_THAI_MAC_DINH,
         f'Bản mới mặc định là {K.TRANG_THAI_MAC_DINH!r} — '
         f'{K.trang_thai_cua(a.get("ban") or {})!r}')
    ds, tu_choi = K.ban_de_dang(goc, MA)
    kiem(ds == [] and bool(tu_choi),
         'Chưa đánh dấu -> cửa đăng TỪ CHỐI (fail-closed), không phải cho qua')
    kiem('chua_ro' in (tu_choi or ''), 'và nói rõ đang có mấy bản, trạng thái gì')

    # --- ly_do BẮT BUỘC ---
    kiem(K.kiem_trang_thai('sai', '')[0] is False, 'Đánh dấu "sai" mà thiếu ly_do -> chặn')
    kiem(K.kiem_trang_thai('dung', '  ')[0] is False, 'ly_do toàn khoảng trắng -> chặn')
    kiem(K.kiem_trang_thai('chua_ro', '')[0] is True, '"chua_ro" thì không đòi ly_do')
    kiem(K.kiem_trang_thai('linh tinh', 'x')[0] is False, 'Trạng thái lạ -> chặn')
    kiem(K.danh_dau_ban(goc, MA, 1, 'sai', '')['ok'] is False,
         'danh_dau_ban cũng đòi ly_do, không ném')
    kiem(K.danh_dau_ban(goc, MA, 99, 'sai', 'x')['ok'] is False,
         'Số thứ tự ngoài khoảng -> từ chối, không ném')

    # --- đánh dấu SAI: vẫn phải bị chặn ---
    r = K.danh_dau_ban(goc, MA, 1, 'sai', 'ca thử: cố tình đánh dấu sai')
    kiem(r.get('ok') is True, f'Đánh dấu bản 1 là "sai" — {r.get("cau")}')
    ds, tu_choi = K.ban_de_dang(goc, MA)
    kiem(ds == [] and bool(tu_choi),
         'Tuần CHỈ có bản "sai" -> cửa đăng trả RỖNG, dù mã tuần gõ đúng')
    kiem('sai' in (tu_choi or ''), 'và câu từ chối nói có bản sai')

    # --- bản sai KHÔNG bị xoá: nó là bằng chứng ---
    p, _ = K.doc_phieu_ky(goc, MA)
    kiem(len((p or {}).get('ban') or []) == 1, 'Bản "sai" VẪN nằm trong phiếu')
    b0 = ((p or {}).get('ban') or [{}])[0]
    kiem(os.path.exists(os.path.join(goc, MA, b0.get('tep', 'x'))),
         'và tệp của nó VẪN còn trên đĩa — không xoá bằng chứng')
    kiem((b0.get('ly_do') or '').strip() != '', 'và lý do được ghi lại')

    # --- thêm một bản ĐÚNG: chỉ bản đó ra được ---
    b = K.them_ban(goc, MA, t2, 'người thử')
    kiem(b.get('ok') is True, 'Lưu bản thứ hai')
    K.danh_dau_ban(goc, MA, 2, 'dung', 'ca thử: bản này dùng được')
    ds, tu_choi = K.ban_de_dang(goc, MA)
    kiem(tu_choi is None and len(ds) == 1,
         f'Cửa đăng trả ĐÚNG MỘT bản — {len(ds)}')
    if ds:
        kiem(K.trang_thai_cua(ds[0]) == 'dung', 'và đó là bản "dung"')
        kiem(ds[0].get('tep') != b0.get('tep'),
             'và KHÔNG phải bản đã đánh dấu sai')

    # --- bản ghi CŨ thiếu khoá thì coi như chưa xét, KHÔNG coi là dùng được ---
    p, _ = K.doc_phieu_ky(goc, MA)
    for x in (p or {}).get('ban') or []:
        x.pop('trang_thai', None)
    io.open(K.duong_phieu(goc, MA), 'w', encoding='utf-8').write(
        json.dumps(p, ensure_ascii=False))
    ds, tu_choi = K.ban_de_dang(goc, MA)
    kiem(ds == [] and bool(tu_choi),
         'Phiếu CŨ thiếu khoá trang_thai -> coi như chưa xét, KHÔNG cho đăng')

    # --- phiếu hỏng thì cũng không đăng ---
    io.open(K.duong_phieu(goc, MA), 'w', encoding='utf-8').write('{ hỏng')
    ds, tu_choi = K.ban_de_dang(goc, MA)
    kiem(ds == [] and bool(tu_choi), 'Phiếu HỎNG -> cửa đăng từ chối, không ném')
    kiem(K.ban_de_dang(goc, '2026-01-12')[0] == [],
         'Tuần chưa có -> trả rỗng, không ném')


def ca_8_so_tep_voi_ban_da_luu(tm):
    print('\nCA 8 — so một tệp với một bản đã lưu')
    print('-' * 74)
    goc = os.path.join(tm, 'kho8')
    MA = '2026-01-05'
    t1 = dung_xlsx(os.path.join(tm, 's1.xlsx'), o_mau(so_tiet=3))
    a = K.them_ban(goc, MA, t1, 'người thử')
    kiem(a.get('ok') is True, 'Lưu một bản')

    ban, loi = K.chon_ban(goc, MA, None)
    kiem(ban is None and bool(loi),
         'Chưa bản nào "dung" -> KHÔNG tự chọn, bắt gõ --ban')
    K.danh_dau_ban(goc, MA, 1, 'dung', 'ca thử')
    ban, loi = K.chon_ban(goc, MA, None)
    kiem(ban is not None and loi is None, 'Có đúng một bản "dung" -> tự chọn được')

    dd = K.duong_ban(goc, MA, ban)
    kiem(dd and os.path.exists(dd), f'Truy được đường dẫn tệp gốc — {bool(dd)}')
    kiem(K.duong_ban(goc, MA, {}) is None, 'Bản ghi rỗng -> trả None, không ném')
    kiem(K.bam_tep(dd) == K.bam_tep(t1), 'Tệp trong kho khớp SHA-256 với tệp gốc')

    # đếm ô khác đúng: dựng một tệp lệch ĐÚNG MỘT ô
    o = o_mau(so_tiet=3)
    o['D8'] = 'Môn Khác Hẳn (T.Khác)'
    t2 = dung_xlsx(os.path.join(tm, 's2.xlsx'), o)
    A, B = D.doc(dd), D.doc(t2)
    kiem(A.get('loi') == [] and B.get('loi') == [], 'Đọc được cả hai bên')
    key = lambda x: (x['lop'], x['thu'], x['tiet'])
    da = {key(x): x for x in A.get('o') or []}
    db = {key(x): x for x in B.get('o') or []}
    khac = [k for k in set(da) | set(db)
            if (da.get(k) or {}).get('mon') != (db.get(k) or {}).get('mon')]
    kiem(len(khac) == 1, f'Lệch đúng MỘT ô thì đếm ra 1 — {len(khac)}')
    kiem(K.bam_tep(dd) != K.bam_tep(t2), 'và SHA-256 hai tệp khác nhau')

    # chọn bản khi có NHIỀU bản "dung" -> không đoán
    t3 = dung_xlsx(os.path.join(tm, 's3.xlsx'), o_mau(so_tiet=5))
    K.them_ban(goc, MA, t3, 'người thử')
    K.danh_dau_ban(goc, MA, 2, 'dung', 'ca thử: bản thứ hai cũng dùng được')
    ban2, loi2 = K.chon_ban(goc, MA, None)
    kiem(ban2 is None and bool(loi2),
         'HAI bản "dung" -> KHÔNG đoán, bắt gõ --ban')
    kiem(K.chon_ban(goc, MA, 2)[0] is not None, 'Gõ --ban 2 thì chọn được')
    kiem(K.chon_ban(goc, MA, 0)[0] is None, '--ban 0 -> từ chối, không ném')
    kiem(K.chon_ban(goc, '2026-01-12', None)[0] is None,
         'Tuần chưa có -> từ chối, không ném')


# ==========================================================================
def ca_9_lenh_so_in_vua_dien_thoai(tm):
    print('\nCA 9 — lệnh `so` in VỪA màn hình điện thoại')
    print('-' * 74)
    GOC_DA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    goc = os.path.join(tm, 'kho9')
    MA = '2026-01-05'

    # dựng hai tệp lệch NHIỀU hơn trần in (mỗi lớp 25 ô, đổi hết cột D)
    o1 = o_mau(so_tiet=25)
    t1 = dung_xlsx(os.path.join(tm, 'p1.xlsx'), o1)
    o2 = dict(o1)
    for r in range(8, 33):
        o2[f'D{r}'] = f'Môn Khác {r} (T.Khác)'
    t2 = dung_xlsx(os.path.join(tm, 'p2.xlsx'), o2)

    import doc_tkb as D
    K.them_ban(goc, MA, t1, 'người thử', tach=D.doc(t1))
    K.danh_dau_ban(goc, MA, 1, 'dung', 'ca thử')

    def chay(*co):
        r = subprocess.run(
            [sys.executable, os.path.join(GOC_DA, 'luu_tuan.py'),
             '--kho', goc, 'so', t2, '--tuan', MA] + list(co),
            cwd=GOC_DA, capture_output=True, text=True, timeout=60)
        return r

    TRAN = 20            # người dùng chốt 22/8/2026
    r = chay()
    kiem(r.returncode == 0, f'Chạy được dạng mặc định — {r.returncode}')
    dong = r.stdout.split('\n')
    rong = max((len(x) for x in dong), default=0)
    kiem(rong <= 60,
         f'Dạng MẶC ĐỊNH hẹp: dòng rộng nhất {rong} cột (phải <= 60)')
    kiem('còn' in r.stdout and '--het' in r.stdout,
         'Quá trần thì nói còn bao nhiêu ô và chỉ cách in hết')
    kiem('kho:' in r.stdout and 'so :' in r.stdout,
         'Mỗi ô khác in thành khối ngắn kho/so, không kẻ bảng')
    kiem('-' * 30 not in r.stdout, 'và KHÔNG có đường kẻ bảng dài')

    dem = r.stdout.count('     kho: ')
    kiem(dem == TRAN, f'In đúng {TRAN} ô đầu — đếm được {dem}')

    r2 = chay('--het')
    dem2 = r2.stdout.count('     kho: ')
    kiem(dem2 > dem, f'--het in nhiều hơn — {dem} -> {dem2}')
    kiem('--het để in hết' not in r2.stdout,
         'và không còn câu nhắc --het nữa')

    r3 = chay('--rong')
    rong3 = max((len(x) for x in r3.stdout.split('\n')), default=0)
    kiem(rong3 > rong, f'--rong in bảng rộng hơn — {rong} -> {rong3}')
    kiem('-' * 30 in r3.stdout, 'và CÓ đường kẻ bảng')
    kiem('TRÁI (kho)' in r3.stdout, 'với tiêu đề cột TRÁI/PHẢI')

    r4 = chay('--rong', '--het')
    kiem(r4.returncode == 0 and r4.stdout.count('T2 tiết') >= 1,
         'Hai cờ đi cùng nhau vẫn chạy')

    # CHỈ ĐỌC: kho không đổi sau mọi lượt so
    p, _ = K.doc_phieu_ky(goc, MA)
    kiem(len((p or {}).get('ban') or []) == 1,
         'Sau bốn lượt `so`, kho vẫn ĐÚNG MỘT bản — lệnh chỉ đọc')


# ==========================================================================
def _doc_tach(goc, ma_tuan, ban):
    """Nội dung thô của bản tách, hoặc None. Chịu được mọi hình dạng hỏng —
       dòng khẳng định không bao giờ được ném (kiểu hỏng số 2)."""
    if not isinstance(ban, dict) or not ban.get('tach'):
        return None
    dd = os.path.join(K.thu_muc_tuan(goc, ma_tuan), ban['tach'])
    try:
        with io.open(dd, 'rb') as f:
            return f.read()
    except OSError:
        return None


def _dau_kho(goc):
    """Dấu của cả kho: đường dẫn + nội dung mọi tệp. Dùng để khẳng định
       một lệnh KHÔNG ghi một byte nào."""
    ra = []
    for tm2, _, ts in os.walk(goc):
        for t in sorted(ts):
            dd = os.path.join(tm2, t)
            try:
                with io.open(dd, 'rb') as f:
                    ra.append((os.path.relpath(dd, goc), f.read()))
            except OSError:
                ra.append((os.path.relpath(dd, goc), None))
    return sorted(ra)


def ca_10_khuyet_tat_noi_them_khong_de(tm):
    print('\nCA 10 — khuyết tật đã biết: NỐI THÊM, không bao giờ gán đè')
    print('-' * 74)
    goc = os.path.join(tm, 'kho10')
    MA = '2026-02-02'
    t1 = dung_xlsx(os.path.join(tm, 'm1.xlsx'), o_mau(so_tiet=3))
    # Truyền `tach=` vào: bản đầu tôi bỏ trống nên `ban['tach']` là None và
    # ca thử VỠ ở dòng bóc khoá đó thay vì báo đỏ — đúng kiểu hỏng số 2.
    a = K.them_ban(goc, MA, t1, 'người thử', tach=D.doc(t1))
    kiem(a.get('ok') is True and isinstance(a.get('ban'), dict),
         'Lưu một bản (kèm bản tách) để có chỗ ghi khuyết tật')
    if not (a.get('ok') and isinstance(a.get('ban'), dict)):
        return
    dd_ban = K.duong_ban(goc, MA, a['ban'])
    bam_truoc = K.bam_tep(dd_ban)
    tt_truoc = (K.trang_thai_cua(a['ban']), a['ban'].get('ly_do'))
    tach_truoc = _doc_tach(goc, MA, a['ban'])
    kiem(tach_truoc is not None, 'và bản tách có mặt trên đĩa để so về sau')

    kiem(K.khuyet_tat_cua(a['ban']) == [],
         'Bản mới chưa có khuyết tật nào')
    kiem(K.khuyet_tat_cua(None) == [] and K.khuyet_tat_cua({}) == [],
         'khuyet_tat_cua() TOÀN PHẦN: None và dict rỗng -> [], không ném')

    # --- hai khoá BẮT BUỘC ---
    kiem(K.ghi_khuyet_tat(goc, MA, 1, '   ', 'người thử')['ok'] is False,
         'Thiếu mô tả -> từ chối, không ném')
    kiem(K.ghi_khuyet_tat(goc, MA, 1, 'có chữ', '  ')['ok'] is False,
         'Thiếu tên người xác nhận -> từ chối, không ném')
    kiem(K.ghi_khuyet_tat(goc, MA, 99, 'có chữ', 'người thử')['ok'] is False,
         'Số thứ tự ngoài khoảng -> từ chối, không ném')

    # --- NỐI THÊM: hai lần ghi phải ra HAI mục, mục cũ còn nguyên ---
    r1 = K.ghi_khuyet_tat(goc, MA, 1, 'chỗ hỏng thứ nhất', 'người thử',
                          o_excel=['D11'])
    r2 = K.ghi_khuyet_tat(goc, MA, 1, 'chỗ hỏng thứ hai', 'người khác')
    kiem(r1.get('ok') is True and r2.get('ok') is True,
         'Ghi được hai khuyết tật')
    p = K.doc_phieu(goc, MA) or {}
    cac_ban = p.get('ban') or [{}]
    ds = K.khuyet_tat_cua(cac_ban[0])
    kiem(len(ds) == 2,
         f'Ghi hai lần ra HAI mục, không đè — {len(ds)} mục')
    mo = [x.get('mo_ta') for x in ds]
    kiem(len(set(mo)) == 2 and all(isinstance(x, str) and x for x in mo),
         f'Mục cũ còn nguyên, không bị mục mới nuốt — {mo}')
    kiem((ds[0].get('o_excel') or []) == ['D11'],
         f'Ô Excel đi theo đúng mục của nó — {ds[0].get("o_excel")}')
    kiem(all((x.get('ngay') or '').count('-') == 2 for x in ds),
         'Mỗi mục tự mang NGÀY — không phải một ngày chung cho cả phiếu')

    # --- CHỈ đụng phiếu ---
    b = cac_ban[0]
    kiem(K.bam_tep(dd_ban) == bam_truoc,
         'Tệp GỐC trong ban/ không bị đụng một byte')
    kiem(tach_truoc is not None and _doc_tach(goc, MA, b) == tach_truoc,
         'Bản TÁCH trong tach/ không bị đụng một byte')
    # Mốc so là GIÁ TRỊ TRƯỚC, không phải "khác None". Bản đầu viết
    # `b.get('trang_thai') is not None` nên chỉ bắt được việc XOÁ khoá: vá
    # cho ghi_khuyet_tat() đặt luôn trang_thai='sai' thì bộ thử vẫn
    # 152/152 (đo 26/8/2026), mà hậu quả thật là bản tuột khỏi đường đăng.
    kiem(b.get('sha256') == bam_truoc,
         f'sha256 của bản không đổi — {b.get("sha256") == bam_truoc}')
    kiem((K.trang_thai_cua(b), b.get('ly_do')) == tt_truoc,
         f'trang_thai và ly_do KHÔNG đổi — trước {tt_truoc}, '
         f'sau {(K.trang_thai_cua(b), b.get("ly_do"))}')

    # --- khuyết tật KHÔNG phải trạng thái: bản vẫn ra được đường đăng ---
    K.danh_dau_ban(goc, MA, 1, 'dung', 'ca thử: bản này dùng được')
    de, tu_choi = K.ban_de_dang(goc, MA)
    kiem(len(de) == 1 and not tu_choi,
         'Bản mang khuyết tật vẫn ĐĂNG ĐƯỢC — khuyết tật != trạng thái')

    # --- phiếu hỏng thì DỪNG, không ghi đè ---
    dd_phieu = K.duong_phieu(goc, MA)
    io.open(dd_phieu + '.giu', 'w', encoding='utf-8').write(
        io.open(dd_phieu, encoding='utf-8').read())
    io.open(dd_phieu, 'w', encoding='utf-8').write('{ hỏng')
    r = K.ghi_khuyet_tat(goc, MA, 1, 'x', 'y')
    kiem(r['ok'] is False and 'hỏng' in (r['cau'] or ''),
         'Phiếu hỏng -> DỪNG, không ghi đè lên nó')
    kiem(io.open(dd_phieu, encoding='utf-8').read() == '{ hỏng',
         'Và phiếu hỏng còn NGUYÊN, không bị ghi đè')


def ca_11_doi_chieu_chi_doc_va_thay_dung_cho_lech(tm):
    print('\nCA 11 — lệnh `doi-chieu`: CHỈ ĐỌC, và thấy đúng chỗ lệch')
    print('-' * 74)
    GOC_DA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    goc = os.path.join(tm, 'kho11')
    MA = '2026-04-06'

    # Mọi tên ở đây là tên BỊA, cố ý KHÔNG khớp gì trong cauhinh.json —
    # ca thử này không bao giờ được có ý kiến về dữ liệu nhà trường.
    LOP, GV, GV_LA = '9Z1', 'T.Thử', 'T.Thử.Viết.Tắt.Khác'
    o = {'A3': 'THỬ', 'A4': 'TUẦN 9 (06/4/2026-11/4/2026)'}
    for i in range(4):
        o[f'D{8 + i}'] = f'Môn Thử A ({GV_LA})'
    for i in range(2):
        o[f'D{12 + i}'] = f'Môn Thử B La ({GV})'
    for c in 'DEFGHI':
        o[f'{c}43'] = f'=COUNTA({c}8:{c}42)'
    t1 = dung_xlsx(os.path.join(tm, 'dc.xlsx'), o)

    import doc_tkb as D
    K.them_ban(goc, MA, t1, 'người thử', tach=D.doc(t1))
    K.danh_dau_ban(goc, MA, 1, 'dung', 'ca thử: bản này dùng được')

    # cauhinh BỊA: khai tên CHUẨN, còn tệp viết kiểu khác -> phải cần bảng tên
    dd_cfg = os.path.join(tm, 'cauhinh_thu.json')
    with io.open(dd_cfg, 'w', encoding='utf-8') as f:
        json.dump({'phan_cong': {LOP: [['Môn Thử A', GV, 4],
                                       ['Môn Thử B', GV, 2]]}},
                  f, ensure_ascii=False)

    def chay(bang=None):
        moi = dict(os.environ)
        r = subprocess.run(
            [sys.executable, os.path.join(GOC_DA, 'luu_tuan.py'),
             '--kho', goc, 'doi-chieu', '--tuan', MA, '--cauhinh', dd_cfg],
            cwd=bang or GOC_DA, capture_output=True, text=True, timeout=120,
            env=moi)
        return r.stdout + r.stderr

    truoc = _dau_kho(goc)
    ra = chay()
    kiem('Traceback' not in ra, 'Chạy được, KHÔNG ném')
    kiem(_dau_kho(goc) == truoc,
         'Sau một lượt doi-chieu, kho không đổi MỘT BYTE nào — chỉ đọc')

    # Bản tách ghi lớp theo BỐ CỤC của trường (12B1...), còn cauhinh bịa ghi
    # 9Z1 — nên mọi cặp đều lệch. Điều cần canh không phải con số, mà là:
    # có thấy lệch, và có in ra tên chuỗi lạ.
    kiem('(a) TÊN MÔN' in ra and '(b) SỐ TIẾT' in ra
         and '(c) GIÁO VIÊN' in ra and '(d) TRỤC' in ra,
         'In đủ BỐN bảng')
    kiem('Môn Thử B La' in ra,
         'Tên môn chỉ có ở tệp hiện ra ở bảng (a) — bộ dò thật sự có chạy')
    kiem(GV_LA in ra,
         'Tên GV lạ hiện ra — bảng tên rỗng thì KHÔNG gộp gì, đúng như khai')

    # --- có áp bảng tên: khai hai luật gộp thì hai chuỗi lạ biến mất ---
    bang = os.path.join(tm, 'bang11')
    os.makedirs(bang, exist_ok=True)
    for ten, gop in (('bang_ten_mon.json', {'Môn Thử B La': 'Môn Thử B'}),
                     ('bang_ten_gv.json', {GV_LA: GV})):
        with io.open(os.path.join(bang, ten), 'w', encoding='utf-8') as f:
            json.dump({'biet': [], 'gop': {k: {'chuan': v,
                                               'nguoi_duyet': 'người thử',
                                               'ngay': '2026-01-01'}
                                           for k, v in gop.items()}},
                      f, ensure_ascii=False)
    # `luu_tuan.py` nạp bảng từ THƯ MỤC CỦA CHÍNH NÓ, nên phải chép nó sang
    # thư mục có bảng thử thì mới đổi được bảng mà không đụng bảng thật.
    for t in ('luu_tuan.py', 'bang_ten.py', 'doc_tkb.py', 'kho_tuan.py',
              'ghi_ben.py', 'sinh_dang.py', 'doi_chieu.py'):
        shutil.copy(os.path.join(GOC_DA, t), os.path.join(bang, t))
    r = subprocess.run(
        [sys.executable, os.path.join(bang, 'luu_tuan.py'),
         '--kho', goc, 'doi-chieu', '--tuan', MA, '--cauhinh', dd_cfg],
        cwd=bang, capture_output=True, text=True, timeout=120)
    ra2 = r.stdout + r.stderr
    kiem('Traceback' not in ra2, 'Chạy với bảng tên thử: KHÔNG ném')
    kiem('Môn Thử B La' not in ra2 and GV_LA not in ra2,
         'Khai luật gộp thì hai chuỗi lạ BIẾN MẤT khỏi báo cáo — bảng tên '
         'CÓ được áp lúc đối chiếu')
    kiem(_dau_kho(goc) == truoc,
         'Và kho vẫn không đổi một byte nào')


def _them_doc_props(duong, **the):
    """Nhét một `docProps/core.xml` vào tệp .xlsx đã dựng.

       `dung_xlsx()` KHÔNG sinh docProps (đã kiểm) — mà docProps mới là thứ
       CA 12 cần thử, nên phải nối thêm vào chính tệp zip đó. Nối chứ không
       sửa `dung_xlsx`: mọi ca thử khác đang dùng nó, và không ca nào cần
       docProps.

       Thứ tự thẻ CỐ Ý xáo trộn: hai bản thật của trường có thứ tự thẻ KHÁC
       NHAU (bản 18/8 mở đầu bằng `dcterms:created`, bản 21/8 bằng
       `dc:creator`), nên bộ đọc nào bám vào vị trí sẽ đúng ở tệp này và
       sai ở tệp kia.
    """
    import zipfile as _z
    ns = ('xmlns:cp="http://schemas.openxmlformats.org/package/2006/'
          'metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/'
          '1.1/" xmlns:dcterms="http://purl.org/dc/terms/"')
    than = ''.join(f'<{k}>{v}</{k}>' for k, v in the.items())
    with _z.ZipFile(duong, 'a') as z:
        z.writestr('docProps/core.xml',
                   f'<?xml version="1.0" encoding="UTF-8"?>'
                   f'<cp:coreProperties {ns}>{than}</cp:coreProperties>')
    return duong


def ca_12_ten_nguoi_trong_docprops_khong_bao_gio_ra(tm):
    print('\nCA 12 — TÊN NGƯỜI trong docProps KHÔNG ra khỏi doc_tkb')
    print('-' * 74)
    # Ba chuỗi bịa, KHÔNG trùng gì trong cauhinh.json lẫn trong tệp thử.
    NGUOI_TAO = 'NGUOI-TAO-KHONG-DUOC-RA'
    NGUOI_SUA = 'NGUOI-SUA-CUOI-KHONG-DUOC-RA'
    NGAY = '2026-08-18T17:06:19Z'

    t = dung_xlsx(os.path.join(tm, 'docprops.xlsx'), o_mau(so_tiet=3))
    _them_doc_props(
        t,
        **{'dcterms:created': '2023-08-30T02:39:09Z',
           'dc:creator': NGUOI_TAO,
           'cp:lastPrinted': '2026-08-18T04:38:12Z',
           'dcterms:modified': NGAY,
           'cp:lastModifiedBy': NGUOI_SUA,
           'cp:revision': '1'})

    r = D.doc(t)
    kiem(not r['loi'], f'Đọc được tệp có docProps — lỗi: {r["loi"]}')

    # (a) ĐIỀU KIỆN TIÊN QUYẾT: hai tên người THẬT SỰ có trong tệp. Không
    #     có mục này thì bản vá "bỏ hẳn docProps đi" cũng làm mục (c) xanh.
    with zipfile.ZipFile(t) as z:
        xml = z.read('docProps/core.xml').decode('utf-8')
    kiem(NGUOI_TAO in xml and NGUOI_SUA in xml,
         'Điều kiện tiên quyết: cả hai tên người NẰM THẬT trong tệp')

    # (b) Ngày thì PHẢI ra, nguyên văn, không đổi múi giờ.
    kiem(r.get('ngay_truong_sua') == NGAY,
         f'Lấy được dcterms:modified NGUYÊN VĂN — {r.get("ngay_truong_sua")!r}')

    # (c) Còn hai tên người thì KHÔNG, ở BẤT KỲ ĐÂU trong dict trả về.
    tho = json.dumps(r, ensure_ascii=False)
    ro = [x for x in (NGUOI_TAO, NGUOI_SUA) if x in tho]
    kiem(not ro, f'KHÔNG tên người nào ra khỏi doc_tkb.doc() — rò: {ro}')

    # (d) Và cả những thẻ KHÔNG PHẢI tên người cũng không tự đi theo:
    #     danh sách trắng MỘT phần tử, không phải "đọc hết rồi lọc".
    theo = [x for x in ('2023-08-30T02:39:09Z', '2026-08-18T04:38:12Z')
            if x in tho]
    kiem(not theo,
         f'và thẻ khác trong cùng tệp XML cũng không đi theo — {theo}')

    # (e) Thiếu docProps thì TRỐNG, không ném, không bịa.
    t2 = dung_xlsx(os.path.join(tm, 'khong-docprops.xlsx'), o_mau(so_tiet=3))
    r2 = D.doc(t2)
    kiem(not r2['loi'] and r2.get('ngay_truong_sua') is None,
         f'Tệp KHÔNG có docProps -> ngày là None, không ném — '
         f'{r2.get("ngay_truong_sua")!r}')

    # (f) docProps rách / ngày không đúng khuôn -> TRỐNG, không nhận bừa.
    t3 = dung_xlsx(os.path.join(tm, 'docprops-rach.xlsx'), o_mau(so_tiet=3))
    _them_doc_props(t3, **{'dcterms:modified': 'sáng thứ Ba tuần trước'})
    r3 = D.doc(t3)
    kiem(not r3['loi'] and r3.get('ngay_truong_sua') is None,
         f'Ngày KHÔNG đúng khuôn ISO -> None, không nhận bừa — '
         f'{r3.get("ngay_truong_sua")!r}')

    # (g) Dấu bộ đọc PHẢI đổi theo — bump PHIEN_BAN là một lời hứa.
    kiem(D.dau_bo_doc().get('phien_ban') != '1',
         f'PHIEN_BAN đã bump khỏi "1" — nay {D.dau_bo_doc().get("phien_ban")!r}')

    # (h) GHIM LITERAL danh sách trắng. Mục (c) ở trên KHÔNG thay được mục
    #     này: đo 26/8/2026, thêm `dc:creator` vào CUỐI `THE_DOC_PROPS` thì
    #     `modified` vẫn đứng trước nên hàm vẫn trả đúng ngày, (c) XANH, và
    #     bộ thử chỉ tụt vì một mục KHÁC — đỏ nhầm chỗ, nếp hỏng 19.
    #     Chỉ phép so literal mới bắt được việc NỚI danh sách, bất kể thẻ
    #     mới đứng ở đâu.
    #
    #     Ghim literal ở đây là ĐÚNG chứ không phạm luật "đừng ghim hằng
    #     số": `THE_DOC_PROPS` không phải dữ liệu nhà trường mà là một
    #     QUYẾT ĐỊNH VỀ PHẠM VI — cùng hạng với `TRUONG_O` và
    #     `TRAN_NGOAI_LE`. Cả điểm của mục này là bắt người nới nó phải
    #     dừng lại và giải thích: cùng tệp XML đó có `dc:creator` và
    #     `cp:lastModifiedBy`, đều là tên người.
    DA_DUYET = ('{http://purl.org/dc/terms/}modified',)
    kiem(tuple(D.THE_DOC_PROPS) == DA_DUYET,
         f'THE_DOC_PROPS ĐÚNG BẰNG bộ đã duyệt — thừa '
         f'{sorted(set(D.THE_DOC_PROPS) - set(DA_DUYET))}, thiếu '
         f'{sorted(set(DA_DUYET) - set(D.THE_DOC_PROPS))}')


def ca_13_doc_lai_khong_them_ban_khong_doi_quyet_dinh(tm):
    print('\nCA 13 — ĐỌC LẠI: không thêm bản, không đổi quyết định của người')
    print('-' * 74)
    goc, MA = os.path.join(tm, 'kho13'), '2026-07-06'
    NGAY = '2026-08-18T17:06:19Z'

    # Bản lưu bằng bộ đọc "đời cũ": tệp KHÔNG có docProps, nên bản tách
    # không có `ngay_truong_sua` — đúng cảnh của bản tuần 1 trong kho thật.
    t = dung_xlsx(os.path.join(tm, 'doc-lai.xlsx'), o_mau(so_tiet=4))
    K.them_ban(goc, MA, t, 'người thử', tach=D.doc(t))
    K.danh_dau_ban(goc, MA, 1, 'dung', 'ca thử: bản này dùng được')
    K.ghi_khuyet_tat(goc, MA, 1, 'khuyết tật của ca thử', 'người thử')

    # Ép dấu bộ đọc của bản này về ĐỜI CŨ. Không có bước này thì bản thử
    # mang sẵn dấu của bộ đọc HIỆN TẠI, `bo_doc` trước và sau bằng nhau, và
    # mục "dấu bộ đọc đã đổi theo" ĐỎ vì kỳ vọng sai chứ không vì mã sai —
    # ca thử mất khả năng phân biệt đúng chỗ nó cần phân biệt nhất.
    dd_phieu = os.path.join(K.thu_muc_tuan(goc, MA), 'phieu.json')
    with io.open(dd_phieu, encoding='utf-8') as f:
        _p = json.load(f)
    _p['ban'][0]['bo_doc'] = {'phien_ban': '0', 'bam_ma': 'doi-cu'}
    with io.open(dd_phieu, 'w', encoding='utf-8') as f:
        json.dump(_p, f, ensure_ascii=False)

    p0, _ = K.doc_phieu_ky(goc, MA)
    b0 = dict((p0.get('ban') or [])[0])
    kiem((b0.get('bo_doc') or {}).get('phien_ban') != D.PHIEN_BAN,
         f'Điều kiện tiên quyết: bản mang dấu bộ đọc ĐỜI CŨ — '
         f'{(b0.get("bo_doc") or {}).get("phien_ban")!r} vs nay {D.PHIEN_BAN!r}')
    tm_t = K.thu_muc_tuan(goc, MA)
    tach_cu = b0.get('tach')
    kiem(bool(tach_cu) and os.path.exists(os.path.join(tm_t, tach_cu)),
         f'Điều kiện tiên quyết: bản có sẵn một tệp tách — {tach_cu}')
    with io.open(os.path.join(tm_t, tach_cu), encoding='utf-8') as f:
        noi_dung_cu = f.read()
    ban_truoc = sorted(os.listdir(os.path.join(tm_t, 'ban')))

    # Nay tệp gốc CÓ ngày — mô phỏng bộ đọc mới đọc ra thứ bộ đọc cũ không
    # thấy. Vá thẳng vào tệp trong kho: đúng cảnh "cùng tệp gốc, bộ đọc mới".
    _them_doc_props(os.path.join(tm_t, b0['tep']),
                    **{'dcterms:modified': NGAY})
    t2 = D.doc(os.path.join(tm_t, b0['tep']))
    kiem(t2.get('ngay_truong_sua') == NGAY,
         f'Bộ đọc mới đọc ra ngày mà bản tách cũ không có — '
         f'{t2.get("ngay_truong_sua")!r}')

    r = K.doc_lai_ban(goc, MA, 1, t2)
    kiem(r.get('ok') is True, f'Đọc lại được — {r.get("cau")}')
    if not r.get('ok'):
        return
    p1, _ = K.doc_phieu_ky(goc, MA)
    b1 = (p1.get('ban') or [])[0]

    # (1) KHÔNG thêm bản mới — cả trong phiếu lẫn trong thư mục ban/.
    kiem(len(p1.get('ban') or []) == len(p0.get('ban') or []),
         f'Số bản trong phiếu KHÔNG đổi — {len(p1.get("ban") or [])}')
    kiem(sorted(os.listdir(os.path.join(tm_t, 'ban'))) == ban_truoc,
         'Thư mục ban/ KHÔNG có tệp nào mới')
    kiem(b1.get('sha256') == b0.get('sha256') and b1.get('tep') == b0.get('tep'),
         'Vẫn đúng tệp gốc đó — sha256 và đường dẫn không đổi')

    # (2) KHÔNG đè bản tách cũ — nó là bằng chứng bộ đọc đời đó đọc ra gì.
    kiem(os.path.exists(os.path.join(tm_t, tach_cu)),
         f'Bản tách CŨ vẫn còn trên đĩa — {tach_cu}')
    with io.open(os.path.join(tm_t, tach_cu), encoding='utf-8') as f:
        kiem(f.read() == noi_dung_cu,
             'và nội dung nó KHÔNG đổi một ký tự')
    kiem(b1.get('tach') != tach_cu,
         f'Phiếu trỏ sang bản tách MỚI — {b1.get("tach")}')
    with io.open(os.path.join(tm_t, b1['tach']), encoding='utf-8') as f:
        kiem(json.load(f).get('ngay_truong_sua') == NGAY,
             'và bản tách mới CÓ ngày trường sửa')

    # (3) KHÔNG đụng trang_thai / ly_do — quyết định của NGƯỜI.
    #     Mốc so là GIÁ TRỊ CHỤP TRƯỚC, không phải "khác rỗng" (nếp hỏng 13).
    kiem(b1.get('trang_thai') == b0.get('trang_thai'),
         f'trang_thai KHÔNG đổi — vẫn {b1.get("trang_thai")!r}')
    kiem(b1.get('ly_do') == b0.get('ly_do'),
         'ly_do KHÔNG đổi')

    # (4) KHÔNG đụng những khoá nói về LẦN LƯU, và không nuốt khuyết tật.
    lech = [k for k in ('nguoi_luu', 'ghi_chu', 'ten_goc', 'gio_luu',
                        'khuyet_tat')
            if b0.get(k) != b1.get(k)]
    kiem(not lech, f'Các khoá của LẦN LƯU không đổi — lệch: {lech}')

    # (5) Bản vẫn ĐĂNG ĐƯỢC, và dấu bộ đọc đã đổi.
    ds, tu_choi = K.ban_de_dang(goc, MA)
    kiem(len(ds or []) == 1 and not tu_choi,
         f'Bản vẫn ra được đường đăng — {tu_choi}')
    kiem(b1.get('bo_doc') != b0.get('bo_doc'),
         'Dấu bộ đọc ĐÃ đổi theo')

    # (6) Đọc lại LẦN NỮA cũng không đè tệp tách vừa sinh.
    r2 = K.doc_lai_ban(goc, MA, 1, t2)
    p2, _ = K.doc_phieu_ky(goc, MA)
    b2 = (p2.get('ban') or [])[0]
    kiem(r2.get('ok') is True and b2.get('tach') != b1.get('tach'),
         f'Đọc lại lần hai sinh tệp KHÁC, không đè — {b2.get("tach")}')
    kiem(os.path.exists(os.path.join(tm_t, b1['tach'])),
         'và tệp của lần một vẫn còn')

    # (7) Số thứ tự bậy thì TỪ CHỐI, không ném.
    for xau in (0, 99, 'một', None):
        rr = K.doc_lai_ban(goc, MA, xau, t2)
        if rr.get('ok'):
            kiem(False, f'Số thứ tự {xau!r} đáng lẽ phải bị từ chối')
            break
    else:
        kiem(True, 'Số thứ tự bậy -> từ chối gọn, không ném')


def ca_14_ghim_hai_danh_sach_trang(tm):
    print('\nCA 14 — GHIM LITERAL hai danh sách trắng của kho')
    print('-' * 74)

    # --- (a) CHO_PHEP_SUA_TUAN ------------------------------------------
    # Ghim literal, cùng hạng `TRUONG_O` / `THE_DOC_PROPS`: một QUYẾT ĐỊNH
    # VỀ PHẠM VI GHI, không phải chi tiết kỹ thuật. Nối thẳng vào phạm vi
    # công khai — `sua_tuan()` là đường DUY NHẤT ghi được bốn trường chữ tự
    # do mà `sinh_dang.KHUON_TUAN` sau đó cho ra trang công khai.
    SUA_DA_DUYET = ('tu_ngay', 'den_ngay', 'nhan', 'nam_hoc', 'hoc_ky',
                    'ghi_chu')
    kiem(tuple(sorted(K.CHO_PHEP_SUA_TUAN)) == tuple(sorted(SUA_DA_DUYET)),
         f'CHO_PHEP_SUA_TUAN ĐÚNG BẰNG bộ đã duyệt — thừa '
         f'{sorted(set(K.CHO_PHEP_SUA_TUAN) - set(SUA_DA_DUYET))}, thiếu '
         f'{sorted(set(SUA_DA_DUYET) - set(K.CHO_PHEP_SUA_TUAN))}')
    kiem('tieu_de' not in K.CHO_PHEP_SUA_TUAN,
         "`tieu_de` KHÔNG sửa được — nó là ô A3 NGUYÊN VĂN của trường, và "
         "nó nguyên vẹn được là vì KHÔNG AI SỬA ĐƯỢC, không phải vì có ai "
         "canh nội dung nó")

    # Và HÀNH VI: khoá ngoài danh sách phải bị từ chối, không lặng lẽ ghi.
    goc, MA = os.path.join(tm, 'kho14'), '2026-09-07'
    t = dung_xlsx(os.path.join(tm, 'k14.xlsx'), o_mau(so_tiet=3))
    K.them_ban(goc, MA, t, 'người thử', tach=D.doc(t))
    r = K.sua_tuan(goc, MA, tieu_de='TIÊU ĐỀ BỊA ĐÈ LÊN CHỮ CỦA TRƯỜNG')
    kiem(r.get('ok') is False and 'tieu_de' in (r.get('cau') or ''),
         f'sua_tuan TỪ CHỐI khoá ngoài danh sách, gọi đích danh — '
         f'{(r.get("cau") or "")[:56]!r}')
    p, _ = K.doc_phieu_ky(goc, MA)
    kiem('tieu_de' not in (p or {}),
         'và KHÔNG ghi một chữ nào vào phiếu')

    # --- (b) MAU_BAN ----------------------------------------------------
    # Danh sách trắng KÝ TỰ được giữ trong tên tệp bản lưu.
    kiem(K.MAU_BAN.pattern == r'[^0-9A-Za-zÀ-ỹ._-]+',
         f'MAU_BAN ĐÚNG BẰNG khuôn đã duyệt — {K.MAU_BAN.pattern!r}')
    xau = K._ten_ban('2026-01-01T00-00-00', '../../../etc/kho ác.xlsx')
    kiem('/' not in xau and '..' not in xau,
         f'và tên tệp dựng ra không mang / hay .. — {xau!r}')

    # ⚠ SỰ THẬT ĐO ĐƯỢC 26/8/2026, KHÁC VỚI ĐIỀU TÔI ĐÃ VIẾT LẦN TRƯỚC.
    # Tôi ghi "basename() là lớp chắn thứ nhất, MAU_BAN là lớp thứ hai, hôm
    # nay chưa thủng" — câu đó chưa ai đo. Đo rồi thì:
    #
    #  · MAU_BAN MỘT MÌNH ĐÃ CHẶN ĐƯỢC. Nó xoá MỌI dấu phân cách (cả `/`
    #    lẫn `\`, đều nằm ngoài lớp cho phép). `..` sống sót thành hai dấu
    #    chấm trong tên tệp, nhưng KHÔNG CÒN dấu phân cách thì không ra
    #    khỏi thư mục được.
    #  · Và có một cảnh mà MAU_BAN là LỚP DUY NHẤT, không phải lớp thứ hai:
    #    đường kiểu Windows `..\..\windows\x.xlsx`. Trên Linux
    #    `os.path.basename()` KHÔNG coi `\` là dấu phân cách nên nó trả về
    #    NGUYÊN CHUỖI — một mình MAU_BAN làm hết việc.
    #
    # Vòng dưới đo lại điều đó mỗi lần chạy, để câu trên không thành một
    # lời khẳng định chép tay nữa.
    khong_chan = []
    for t in ('../../../etc/passwd.xlsx', '/etc/shadow.xlsx',
              'a/../../b.xlsx', '..\\..\\windows\\x.xlsx',
              '....//....//x.xlsx'):
        mot_minh = K.MAU_BAN.sub('_', t)          # KHÔNG qua basename()
        if '/' in mot_minh or '\\' in mot_minh:
            khong_chan.append((t, mot_minh))
    kiem(not khong_chan,
         f'MAU_BAN MỘT MÌNH (bỏ basename ra) xoá sạch dấu phân cách — '
         f'chưa chặn: {khong_chan}')

    win = '..\\..\\windows\\x.xlsx'
    kiem(os.path.basename(win) == win,
         f'ĐỐI CHỨNG: với đường kiểu Windows, basename() trên Linux KHÔNG '
         f'cắt gì — {os.path.basename(win)!r}. Ở cảnh đó MAU_BAN là lớp '
         f'DUY NHẤT, không phải lớp thứ hai')

    # --- (c) TÊN TỆP KIỂU WINDOWS — đường đi THẬT, hằng tuần ------------
    # Tệp .xlsx Khoa gửi sang đến từ máy Windows. Tên kiểu Windows là
    # BÌNH THƯỜNG, không phải dấu hiệu tệp lạ. Mỗi cảnh một mục, và mỗi
    # mục đòi MAU_BAN chặn được MỘT MÌNH (không nhờ basename).
    CANH = [
        ('dấu \\ đơn', '..\\..\\windows\\x.xlsx'),
        ('đường UNC', '\\\\may-khoa\\tkb\\Tuần 1.xlsx'),
        ('ổ C: kiểu Windows', 'C:\\Users\\Khoa\\TKB Tuần 1.xlsx'),
        ('ký tự Windows cấm', 'TKB<Tuần>1:"|?*.xlsx'),
        ('toàn ký tự cấm', '<>:"|?*'),
        ('chuỗi rỗng', ''),
    ]
    con = []
    for nhan, t in CANH:
        mot_minh = K.MAU_BAN.sub('_', t)        # KHÔNG qua basename()
        if '/' in mot_minh or '\\' in mot_minh:
            con.append((nhan, mot_minh))
    kiem(not con,
         f'MAU_BAN MỘT MÌNH xoá sạch dấu phân cách ở cả {len(CANH)} cảnh '
         f'Windows — còn: {con}')
    for nhan, t in CANH:
        ra = K._ten_ban('2026-01-01T00-00-00', t)
        sach = ('/' not in ra and '\\' not in ra
                and ra.startswith('2026-01-01') and len(ra) > 20)
        kiem(sach, f'  · {nhan}: dựng ra {ra[:52]!r}')
    kiem(K._ten_ban('2026-01-01T00-00-00', '') .endswith('TKB.xlsx'),
         'Tên rỗng / toàn ký tự cấm -> lùi về "TKB.xlsx", không ra tên rỗng')

    # --- (d) TÊN QUÁ DÀI: MAU_BAN KHÔNG chặn — và đó là SỰ THẬT ---------
    # MAU_BAN là danh sách trắng KÝ TỰ; nó không cắt được độ dài, và
    # `_ten_ban()` còn CỘNG THÊM 20 ký tự dấu thời gian ở đầu. Nên một
    # tên nguồn HỢP LỆ 240 byte cho ra tên đích 260 byte > 255 byte mà
    # hệ tệp cho phép.
    #
    # ⚠ NGƯỠNG PHỤ THUỘC HỆ TỆP, VÀ KHÁC NHAU BA LẦN VỚI TÊN TIẾNG VIỆT.
    # Đo 26/8/2026, MÁY A, cùng một phép dò nhị phân:
    #     ext4  (/tmp)          255 BYTE  -> tên có dấu tối đa  85 ký tự
    #     ntfs3 (luu_tru/)      255 KÝ TỰ -> tên có dấu tối đa 255 ký tự
    # Kho THẬT nằm trên **ntfs3**, còn bộ thử này chạy trong `/tmp` tức
    # **ext4** — hai nền khác nhau, đừng lấy số của nền này nói về nền kia.
    # Đo `them_ban` NGAY TRÊN `luu_tru/` với tên kiểu Khoa hay đặt (có
    # dấu): nguồn 235 ký tự -> đích 255 -> ok=True; nguồn 236 -> đích 256
    # -> ok=False. Ngưỡng thật của kho là **236 KÝ TỰ**, không phải byte.
    #
    # Vì vậy mục dưới dùng tên THUẦN ASCII: nó vượt ngưỡng trên CẢ HAI
    # nền, nên ca thử cho cùng kết quả dù chạy ở đâu.
    # Mục này KHÔNG đòi MAU_BAN chặn — nó đòi kho HỎNG CHO TỬ TẾ.
    kiem(len(K._ten_ban('2026-01-01T00-00-00', 'T' * 240 + '.xlsx')) > 255,
         'ĐỐI CHỨNG: tên nguồn dài hợp lệ + 20 ký tự dấu thời gian vượt '
         '255 byte — MAU_BAN KHÔNG cắt độ dài, và không định cắt')
    dai = 'T' * 235 + '.xlsx'
    nguon = dung_xlsx(os.path.join(tm, 'nguon-dai.xlsx'), o_mau(so_tiet=3))
    p = os.path.join(tm, dai)
    try:
        shutil.copy(nguon, p)
        dung_duoc = True
    except OSError:
        # Hệ tệp không tạo nổi tên dài này thì KHÔNG kiểm được cảnh đó.
        # In [BỎ QUA] chứ KHÔNG `kiem(True, ...)` — nếp hỏng 21.
        dung_duoc = False
        print(f'  [BỎ QUA] hệ tệp này không tạo nổi tệp tên {len(dai)} byte '
              f'nên cảnh "tên quá dài" CHƯA được thử')
    if dung_duoc:
        r = K.them_ban(os.path.join(tm, 'kho-dai'), '2026-10-05', p,
                       'người thử', tach=D.doc(p))
        kiem(r.get('ok') is False,
             f'Tên quá dài -> them_ban TỪ CHỐI GỌN, không ném — '
             f'{(r.get("cau") or "")[:70]!r}')
        kiem('too long' in (r.get('cau') or '').lower()
             or 'quá dài' in (r.get('cau') or '').lower(),
             'và câu từ chối nói ĐÚNG lý do, không phải một mã lỗi trần')
        kiem(not os.path.exists(os.path.join(tm, 'kho-dai', '2026-10-05',
                                             'phieu.json')),
             'và KHÔNG ghi một byte nào vào kho')


def ca_15_moi_lenh_con_chay_duoc(tm):
    print('\nCA 15 — MỌI lệnh con của luu_tuan.py chạy được qua DÒNG LỆNH')
    print('-' * 74)
    # Vì sao cần: bộ thử cũ chỉ gọi `so` và `doi-chieu` qua tiến trình con,
    # nên một lỗi ở nhánh khác của `main()` KHÔNG AI THẤY. Đã dính thật —
    # `7f209f6` thêm `import doc_tkb as D` bên trong nhánh `doc-lai`, biến
    # `D` thành biến CỤC BỘ của cả `main()` và che mất bản ở mức module.
    # `xem` và `them` VỠ bằng UnboundLocalError, im lặng suốt một ngày, mà
    # `them` chính là lệnh nạp tệp Khoa gửi mỗi tuần.
    #
    # Mục này đi qua TỪNG lệnh con, mỗi lệnh một lượt `subprocess`, và đòi
    # KHÔNG lệnh nào ném. Nó KHÔNG kiểm nội dung đầu ra — việc đó là của
    # các CA khác; nó chỉ canh "mọi nhánh của main() còn nhập được".
    GOC_DA = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    goc, MA = os.path.join(tm, 'kho15'), '2026-12-07'
    t = dung_xlsx(os.path.join(tm, 'k15.xlsx'), o_mau(so_tiet=3))
    t2 = dung_xlsx(os.path.join(tm, 'k15b.xlsx'), o_mau(so_tiet=4))
    dd_cfg = os.path.join(GOC_DA, 'cauhinh.json')

    def goi(*a):
        r = subprocess.run(
            [sys.executable, '-B', os.path.join(GOC_DA, 'luu_tuan.py'),
             '--kho', goc] + list(a),
            capture_output=True, text=True, timeout=180)
        return r

    # Thứ tự CỐ Ý: `them` trước để các lệnh sau có bản mà đọc.
    BUOC = [
        ('them', ('them', t, '--tuan', MA, '--nguoi', 'người thử')),
        ('xem', ('xem', t)),
        ('liet-ke', ('liet-ke',)),
        ('danh-dau', ('danh-dau', '--tuan', MA, '--ban', '1',
                      '--trang-thai', 'dung', '--ly-do', 'ca thử')),
        ('khuyet-tat', ('khuyet-tat', '--tuan', MA, '--ban', '1',
                        '--mo-ta', 'ca thử', '--nguoi', 'người thử')),
        ('de-dang', ('de-dang', '--tuan', MA)),
        ('so', ('so', t2, '--tuan', MA)),
        ('doi-chieu', ('doi-chieu', '--tuan', MA, '--cauhinh', dd_cfg)),
        ('doc-lai', ('doc-lai', '--tuan', MA)),
        ('dang-thu', ('dang-thu', '--tuan', MA)),
    ]
    vo = []
    for nhan, a in BUOC:
        r = goi(*a)
        if 'Traceback' in r.stderr:
            cuoi = (r.stderr.strip().splitlines() or [''])[-1][:70]
            vo.append(f'{nhan}: {cuoi}')
    kiem(not vo, f'KHÔNG lệnh con nào NÉM — {len(BUOC)} lệnh đã đi qua; '
                 f'vỡ: {vo}')

    # ĐỐI CHỨNG: nếu mục trên xanh nhờ "chẳng chạy gì", thì đây bắt được.
    kiem(goi('lenh-khong-co-that').returncode != 0,
         'ĐỐI CHỨNG: lệnh con bịa ra thì THOÁT KHÁC 0 — bộ gọi có hoạt động')
    kiem(goi('liet-ke').returncode == 0,
         'và một lệnh có thật thì thoát 0')

    # `import ... as D` bên trong main() là ĐÚNG cái đã cắn. Ghim bằng cây
    # cú pháp: trong `main()` không được có lệnh import nào.
    import ast
    cay = ast.parse(io.open(os.path.join(GOC_DA, 'luu_tuan.py'),
                            encoding='utf-8').read())
    trong_main = []
    for n in ast.walk(cay):
        if isinstance(n, ast.FunctionDef) and n.name == 'main':
            for m in ast.walk(n):
                if isinstance(m, (ast.Import, ast.ImportFrom)):
                    trong_main.append(
                        [x.asname or x.name for x in m.names])
    kiem(not trong_main,
         f'main() KHÔNG có lệnh `import` nào bên trong — một `import X as D` '
         f'ở đây biến D thành biến CỤC BỘ của cả hàm: {trong_main}')


def main():
    dat_dong_ho_canh(180)
    print('=' * 74)
    print(' THỬ: bộ đọc TKB và kho tuần')
    print('=' * 74)
    tm = tempfile.mkdtemp(prefix='thu_kho_tuan_')
    try:
        ca_1_doc_dung(tm)
        ca_2_tep_hong_thi_do_chu_khong_nem(tm)
        ca_3_dinh_nghia_loi(tm)
        ca_4_khong_de_va_tu_choi_trung(tm)
        ca_5_dau_bo_doc(tm)
        ca_6_phieu_hong_thi_dung(tm)
        ca_7_ban_sai_khong_ra_duoc_duong_dang(tm)
        ca_8_so_tep_voi_ban_da_luu(tm)
        ca_9_lenh_so_in_vua_dien_thoai(tm)
        ca_10_khuyet_tat_noi_them_khong_de(tm)
        ca_11_doi_chieu_chi_doc_va_thay_dung_cho_lech(tm)
        ca_12_ten_nguoi_trong_docprops_khong_bao_gio_ra(tm)
        ca_13_doc_lai_khong_them_ban_khong_doi_quyet_dinh(tm)
        ca_14_ghim_hai_danh_sach_trang(tm)
        ca_15_moi_lenh_con_chay_duoc(tm)
    finally:
        shutil.rmtree(tm, ignore_errors=True)

    dat = sum(1 for ok, _ in KQ if ok)
    print('\n' + '=' * 74)
    print(f'Tổng: {dat}/{len(KQ)} mục ĐẠT.')
    return 0 if dat == len(KQ) else 1


if __name__ == '__main__':
    sys.exit(main())

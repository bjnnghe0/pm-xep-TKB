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
    finally:
        shutil.rmtree(tm, ignore_errors=True)

    dat = sum(1 for ok, _ in KQ if ok)
    print('\n' + '=' * 74)
    print(f'Tổng: {dat}/{len(KQ)} mục ĐẠT.')
    return 0 if dat == len(KQ) else 1


if __name__ == '__main__':
    sys.exit(main())

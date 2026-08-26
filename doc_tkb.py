#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 ĐỌC MỘT TỆP TKB .xlsx CỦA TRƯỜNG → MỘT DICT
--------------------------------------------------------------------------
 Chỉ thư viện chuẩn: `zipfile` + `xml.etree`. KHÔNG dùng openpyxl.

 CHỈ ĐỌC. Mô-đun này không ghi một byte nào xuống đĩa, không biết thư mục
 `luu_tru/` tồn tại, không biết `cauhinh.json` tồn tại. Cắt như vậy để Đợt 4
 (trang xem tuần cũ) dùng lại y nguyên — đúng ràng buộc kiến trúc "viết
 thành hàm rời nhận một dict" mà Đợt 3 đã đặt.

 ┌──────────────────────────────────────────────────────────────────────┐
 │ ĐỊNH NGHĨA CỦA TRƯỜNG `loi` — MỘT DÒNG, ĐỌC KỸ:                      │
 │                                                                      │
 │   `loi` CHỈ chứa LỖI CHÍ MẠNG, tức tệp KHÔNG ĐỌC ĐƯỢC.               │
 │                                                                      │
 │ Thứ 7 có chữ · lệch ngày A4 · lệch số đếm dòng 43 · tên môn lạ       │
 │ ĐỀU KHÔNG PHẢI LỖI. Chúng đã có trường riêng, người gọi tự xem.      │
 │ Nhét chúng vào `loi` là bắt người gọi phân loại lại bằng cách đọc     │
 │ chuỗi — đúng kiểu mã sẽ hỏng trong im lặng khi ai đó đổi câu chữ.     │
 └──────────────────────────────────────────────────────────────────────┘

 KHÔNG BAO GIỜ NÉM. Tệp lạ, tệp rách, zip thiếu mục → `loi` có nội dung và
 mọi trường còn lại RỖNG. Ca thử có một mục dựng tệp hỏng thật để canh.

 TUYỆT ĐỐI KHÔNG TỰ GỘP TÊN MÔN. Đo trên hai tệp tuần 1 thật của trường
 (22/8/2026): **19 chuỗi môn khác nhau** cho khoảng 12 môn — `GDKT-PL` và
 `GDKTPL`, `Chuyên đề Ngữ văn` và `Chuyên đề Ngữ Văn`, `Chuyên đề Lịch sử`
 và `Chuyên đề sử`, `Chuyên đề Địa lí` / `Chuyên đề địa lí` / `chuyên đề
 Địa lí`. Gộp ngầm là im lặng nuốt mất một khác biệt có thể có thật. Chuỗi
 lạ đi vào `ten_mon_la` và được giữ NGUYÊN VĂN suốt chuỗi xử lý.
==========================================================================
"""
import hashlib
import io
import os
import re
import re
import zipfile
import xml.etree.ElementTree as ET

NS = '{http://schemas.openxmlformats.org/spreadsheetml/2006/main}'
NS_R = '{http://schemas.openxmlformats.org/officeDocument/2006/relationships}'

# Phiên bản BỘ ĐỌC. Bump khi đổi cách tách/cách đọc — xem `dau_bo_doc()`.
#   '1' -> '2' (26/8/2026): đọc thêm `ngay_truong_sua` từ docProps.
PHIEN_BAN = '2'

# ==========================================================================
# docProps/core.xml — ĐỌC ĐÚNG MỘT THẺ, VÀ ĐÂY LÀ DANH SÁCH TRẮNG
# ==========================================================================
# Ô `docProps/core.xml` của tệp Excel chứa cả **tên người**. Đo trên hai bản
# thật của tuần 2026-08-24 (26/8/2026):
#     dc:creator          -> CÓ TÊN NGƯỜI ở CẢ HAI bản
#     cp:lastModifiedBy   -> rỗng ở bản 18/8, CÓ TÊN NGƯỜI ở bản 21/8
#     dcterms:modified    -> 2026-08-18T17:06:19Z · 2026-08-21T11:44:31Z
#     cp:lastPrinted · dcterms:created · cp:revision · dc:language ...
#
# Vì vậy đây là DANH SÁCH TRẮNG MỘT PHẦN TỬ, không phải "đọc core.xml rồi
# lọc bớt". Lọc bớt thì thẻ mới của một phiên bản Excel khác sẽ tự đi vào;
# danh sách trắng thì không.
THE_DOC_PROPS = ('{http://purl.org/dc/terms/}modified',)

# Ngày phải đúng khuôn ISO thì mới nhận. `core.xml` là XML của tệp NGƯỜI
# TA gửi tới — không có gì bảo đảm nội dung nó là một ngày.
MAU_NGAY_ISO = r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?(Z|[+-]\d{2}:\d{2})?$'

# Bố cục tờ TKB in của trường. KHÔNG suy từ cauhinh.json: mô-đun này đọc tệp
# CỦA TRƯỜNG, tệp đó có bố cục riêng và không việc gì phải khớp cấu hình của
# ta. Muốn đọc một tờ khác bố cục thì truyền `bo_cuc=` chứ đừng sửa ở đây.
BO_CUC = {
    'sheet': 'Khối 12',
    'hang_dau': 8,               # dòng đầu vùng dữ liệu
    'cot': ['D', 'E', 'F', 'G', 'H', 'I'],
    'lop': ['12B1', '12B2', '12B3', '12B4', '12B5', '12B6'],
    'cac_thu': [2, 3, 4, 5, 6],  # 5 ngày, mỗi ngày 5 tiết liên tiếp
    'cac_tiet': [6, 7, 8, 9, 10],
    'hang_tong': 43,             # dòng "TỔNG SỐ TIẾT/TUẦN"
    'o_tuan': 'A4',              # ô chứa chuỗi tuần + khoảng ngày
    'o_tieu_de': 'A3',
}


def _ngay_truong_sua(z):
    """Ngày nhà trường sửa tệp lần cuối — `dcterms:modified`, NGUYÊN VĂN.

       Trả chuỗi ISO, hoặc None. KHÔNG BAO GIỜ NÉM.

       ┌──────────────────────────────────────────────────────────────────┐
       │ CHỈ LẤY MỘT THẺ. `cp:lastModifiedBy` và `dc:creator` nằm ngay     │
       │ cạnh trong cùng tệp XML và ĐỀU LÀ TÊN NGƯỜI — đã đo, không phải  │
       │ lo xa. Chúng KHÔNG BAO GIỜ được ra khỏi hàm này.                 │
       │ `tests/thu_kho_tuan.py` CA 12 canh trên HÀNH VI: nhét tên người  │
       │ vào cả hai thẻ rồi đòi chúng không xuất hiện ở bất kỳ đâu trong  │
       │ dict mà `doc()` trả về.                                          │
       └──────────────────────────────────────────────────────────────────┘

       GIỮ NGUYÊN VĂN, KHÔNG ĐỔI MÚI GIỜ. Excel ghi `...T17:06:19Z`, và
       người vận hành đã đọc chuỗi đó theo nghĩa đen rồi gõ "17:06" vào ghi
       chú. Tự đổi sang giờ Việt Nam sẽ ra "00:06 ngày 19/8" và **âm thầm
       mâu thuẫn** với mọi ghi chú cũ. Ai cần giờ địa phương thì đổi ở tầng
       hiển thị, đừng đổi ở tầng đọc.
    """
    try:
        if 'docProps/core.xml' not in set(z.namelist()):
            return None
        goc = ET.fromstring(z.read('docProps/core.xml'))
    except Exception:                                   # noqa: BLE001
        return None
    for the in THE_DOC_PROPS:
        for nut in goc.iter(the):
            gt = (nut.text or '').strip()
            if re.match(MAU_NGAY_ISO, gt):
                return gt
    return None


def dau_bo_doc():
    """Dấu của chính bộ đọc này: phiên bản người đặt + băm mã nguồn.

       VÌ SAO CẢ HAI. Phiên bản là thứ người đọc hiểu được, nhưng người sửa
       mã có thể quên bump. Băm mã nguồn thì không quên được. Không có dấu
       này thì sáu tháng sau không phân biệt nổi "tuần đó xếp đúng như vậy
       thật" với "bộ đọc hồi đó đọc sai".
    """
    try:
        with open(os.path.abspath(__file__), 'rb') as f:
            bam = hashlib.sha256(f.read()).hexdigest()[:16]
    except OSError:
        bam = None
    return {'phien_ban': PHIEN_BAN, 'bam_ma': bam}


# ==========================================================================
# Đọc xlsx bằng zipfile + xml.etree
# ==========================================================================
def _chuoi_chung(z):
    """Bảng chuỗi dùng chung. Thiếu mục -> dãy rỗng (tệp vẫn có thể đọc được
       nếu mọi ô đều là inlineStr), KHÔNG ném."""
    try:
        x = z.read('xl/sharedStrings.xml')
    except KeyError:
        return []
    try:
        root = ET.fromstring(x)
    except ET.ParseError:
        return []
    ra = []
    for si in root.iter(NS + 'si'):
        ra.append(''.join(t.text or '' for t in si.iter(NS + 't')))
    return ra


def _duong_sheet(z, ten):
    """Tên sheet -> đường dẫn trong zip. Không có -> (None, danh sách tên có)."""
    try:
        wb = ET.fromstring(z.read('xl/workbook.xml'))
        rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    except (KeyError, ET.ParseError):
        return None, []
    dich = {r.get('Id'): (r.get('Target') or '') for r in rels}
    # Duyệt HẾT rồi mới trả về: `co` phải là danh sách ĐẦY ĐỦ mọi sheet, kể cả
    # những sheet đứng SAU sheet cần tìm. Bản đầu `return` ngay khi khớp nên
    # `sheet_khac` luôn rỗng — đo được trên tệp tuần 1 bản 21/8 của trường:
    # nó có sheet "THEO DÕI BÙ TBK" đứng sau "Khối 12", và sheet đó chứa lý do
    # nghỉ của học sinh. Bỏ sót nó là bỏ sót đúng thứ Việc 4 phải KHÔNG đăng.
    duong, co = None, []
    for s in wb.iter(NS + 'sheet'):
        n = s.get('name')
        co.append(n)
        if n == ten and duong is None:
            t = (dich.get(s.get(NS_R + 'id'), '') or '').lstrip('/')
            if t:
                duong = t if t.startswith('xl/') else 'xl/' + t
    return duong, co


def _doc_o(z, duong, chuoi):
    """Trả (giá trị chữ theo ô, công thức theo ô). Ô rỗng thì không có mặt."""
    gt, ct = {}, {}
    try:
        root = ET.fromstring(z.read(duong))
    except (KeyError, ET.ParseError):
        return gt, ct
    for c in root.iter(NS + 'c'):
        r = c.get('r')
        if not r:
            continue
        f = c.find(NS + 'f')
        if f is not None and f.text:
            ct[r] = f.text
        t = c.get('t')
        if t == 'inlineStr':
            v = ''.join(x.text or '' for x in c.iter(NS + 't'))
        else:
            e = c.find(NS + 'v')
            if e is None or e.text is None:
                continue
            if t == 's':
                try:
                    v = chuoi[int(e.text)]
                except (ValueError, IndexError):
                    v = ''
            else:
                v = e.text
        v = (v or '').strip()
        if v:
            gt[r] = v
    return gt, ct


# ==========================================================================
# Tách "Môn (GV)"
# ==========================================================================
# Ngoặc CUỐI CÙNG, và chỉ ngoặc không lồng. `Địa lí(H.Hoàng)` thiếu dấu cách
# vẫn tách được; `Ngữ văn (H.Trang)` cũng vậy.
MAU_GV = re.compile(r'^(.*)\(([^()]*)\)\s*$', re.S)


def tach_mon_gv(chuoi):
    """'Ngữ văn (H.Trang)' -> ('Ngữ văn', 'H.Trang').

       Không có ngoặc -> (nguyên chuỗi, None). KHÔNG đoán, không sửa chính tả,
       không hạ hoa-thường. Chuỗi trả về giữ NGUYÊN VĂN.
    """
    s = (chuoi or '').strip()
    m = MAU_GV.match(s)
    if not m:
        return s, None
    return m.group(1).strip(), (m.group(2) or '').strip() or None


# ==========================================================================
# Khoảng ngày trong ô A4
# ==========================================================================
MAU_NGAY = re.compile(r'(\d{1,2})\s*/\s*(\d{1,2})(?:\s*/\s*(\d{2,4}))?')


def tach_khoang_ngay(tho):
    """'TUẦN 1 (23/8/2026-29/8/2026)' -> dict, luôn giữ chuỗi gốc ở 'tho'.

       KHÔNG QUYẾT HỘ. Trả về đúng thứ đọc được; việc đối chiếu với mã tuần
       là của người gọi, và người gọi phải hỏi người dùng khi lệch.
    """
    tho = (tho or '').strip()
    ra = {'tho': tho, 'tu': None, 'den': None, 'nhan': None}
    if not tho:
        return ra
    m = re.match(r'^\s*([^(]+?)\s*[\(\[]', tho)
    ra['nhan'] = m.group(1).strip() if m else None
    ds = MAU_NGAY.findall(tho)
    def dung(t):
        d, thg, n = int(t[0]), int(t[1]), t[2]
        if not n:
            return None
        n = int(n)
        if n < 100:
            n += 2000
        try:
            import datetime
            return datetime.date(n, thg, d).isoformat()
        except ValueError:
            return None
    if len(ds) >= 1:
        ra['tu'] = dung(ds[0])
    if len(ds) >= 2:
        ra['den'] = dung(ds[1])
    return ra


# ==========================================================================
# Vùng của công thức COUNTA ở dòng tổng
# ==========================================================================
# Bản cài này phục vụ MÃ CHẠY. `tests/thu_o_tong.py` cố ý giữ một bộ dò
# ĐỘC LẬP — xem lời giải thích trong tệp ca thử đó. Đừng "dọn trùng lặp".
MAU_COUNTA = re.compile(
    r'^COUNTA\(\s*\$?([A-Z]{1,3})\$?(\d{1,7})\s*:\s*\$?([A-Z]{1,3})\$?(\d{1,7})\s*\)$',
    re.IGNORECASE)


def _vung_counta(ct):
    m = MAU_COUNTA.match((ct or '').strip().lstrip('='))
    if not m:
        return None
    return {'cot_dau': m.group(1).upper(), 'hang_dau': int(m.group(2)),
            'cot_cuoi': m.group(3).upper(), 'hang_cuoi': int(m.group(4))}


# ==========================================================================
# HÀM CHÍNH
# ==========================================================================
def doc(duong_dan, bo_cuc=None, ten_mon_biet=None):
    """Đọc một tệp TKB .xlsx. KHÔNG BAO GIỜ NÉM.

       `ten_mon_biet` = tập chuỗi môn đã được người dùng duyệt tay (từ
       `bang_ten_mon.json`). Chuỗi ngoài tập đó vào `ten_mon_la` — KHÔNG bị
       sửa, KHÔNG bị gộp, vẫn nằm nguyên trong `o`.
    """
    bc = dict(BO_CUC)
    if bo_cuc:
        bc.update(bo_cuc)
    biet = set(ten_mon_biet or ())

    ra = {
        'bo_doc': dau_bo_doc(), 'tep': os.path.basename(duong_dan),
        'o': [], 'tuan_A4': None, 'tieu_de': None, 'ngay_truong_sua': None,
        'ngoai_mo_hinh': [], 'o_tong': [], 'dem_tach_duoc': {},
        'lech_dem': [], 'ten_mon_la': [], 'sheet_khac': [], 'loi': [],
    }

    def chiu(cau):
        ra['loi'].append(cau)
        return ra

    if not os.path.exists(duong_dan):
        return chiu(f'Không có tệp: {duong_dan}')
    if not zipfile.is_zipfile(duong_dan):
        return chiu('Không phải tệp .xlsx — tệp này không phải một kho zip. '
                    'Tệp .xls đời cũ hay .csv đổi đuôi đều rơi vào đây; '
                    'hãy mở bằng Excel rồi "Lưu thành" định dạng .xlsx.')
    try:
        z = zipfile.ZipFile(duong_dan)
    except Exception as e:                              # noqa: BLE001
        return chiu(f'Không mở được tệp: {type(e).__name__}: {e}')

    with z:
        muc = set(z.namelist())
        if 'xl/workbook.xml' not in muc:
            return chiu('Thiếu xl/workbook.xml — tệp zip này không phải một '
                        'bảng tính Excel.')
        duong, co = _duong_sheet(z, bc['sheet'])
        ra['sheet_khac'] = [n for n in co if n != bc['sheet']]
        if not duong:
            return chiu(
                f'Không có sheet {bc["sheet"]!r}. '
                + (f'Tệp này có: {co}.' if co else 'Tệp này không có sheet nào.')
                + ' Đổi tên sheet cho đúng rồi nạp lại.')
        if duong not in muc:
            return chiu(f'Sheet {bc["sheet"]!r} trỏ tới {duong} mà mục đó '
                        'không có trong tệp — tệp hỏng.')
        ra['ngay_truong_sua'] = _ngay_truong_sua(z)
        chuoi = _chuoi_chung(z)
        gt, ct = _doc_o(z, duong, chuoi)
        if not gt and not ct:
            return chiu(f'Đọc được sheet {bc["sheet"]!r} nhưng không có một ô '
                        'nào — tệp rỗng hoặc hỏng phần nội dung.')

    ra['tieu_de'] = gt.get(bc['o_tieu_de'])
    ra['tuan_A4'] = tach_khoang_ngay(gt.get(bc['o_tuan']))

    # --- vùng dữ liệu ---
    h0, nt = bc['hang_dau'], len(bc['cac_tiet'])
    dem = {l: 0 for l in bc['lop']}
    la = []
    for j, cot in enumerate(bc['cot']):
        lop = bc['lop'][j] if j < len(bc['lop']) else cot
        for i, thu in enumerate(bc['cac_thu']):
            for k, tiet in enumerate(bc['cac_tiet']):
                o = f'{cot}{h0 + i * nt + k}'
                v = gt.get(o)
                if not v:
                    continue
                mon, gv = tach_mon_gv(v)
                ra['o'].append({'lop': lop, 'thu': thu, 'tiet': tiet,
                                'mon': mon, 'gv': gv, 'o_excel': o, 'tho': v})
                dem[lop] += 1
                if biet and mon not in biet and mon not in la:
                    la.append(mon)
    ra['dem_tach_duoc'] = dem
    ra['ten_mon_la'] = la

    # --- dòng 33-42: Thứ 7, mô hình hiện KHÔNG có. BÁO, đừng nuốt. ---
    h_cuoi = h0 + len(bc['cac_thu']) * nt - 1
    for cot in bc['cot']:
        for r in range(h_cuoi + 1, bc['hang_tong']):
            v = gt.get(f'{cot}{r}')
            if v:
                ra['ngoai_mo_hinh'].append({'o': f'{cot}{r}', 'chu': v})

    # --- dòng tổng: công thức, vùng, và LỆCH so với số đếm được ---
    for j, cot in enumerate(bc['cot']):
        lop = bc['lop'][j] if j < len(bc['lop']) else cot
        o = f'{cot}{bc["hang_tong"]}'
        c = ct.get(o)
        vung = _vung_counta(c) if c else None
        m = {'lop': lop, 'o': o, 'cong_thuc': c, 'vung': vung,
             'so_excel_hien': gt.get(o)}
        ra['o_tong'].append(m)
        if vung and vung['hang_dau'] != h0:
            ra['lech_dem'].append(
                f'{lop}: ô {o} đếm từ dòng {vung["hang_dau"]}, mà dữ liệu bắt '
                f'đầu ở dòng {h0} — bỏ sót {vung["hang_dau"] - h0} dòng đầu '
                f'bảng. Số in ra sẽ THIẾU {vung["hang_dau"] - h0} tiết.')
        if vung and vung['hang_cuoi'] < h_cuoi:
            ra['lech_dem'].append(
                f'{lop}: ô {o} dừng ở dòng {vung["hang_cuoi"]}, chưa phủ hết '
                f'dòng {h_cuoi}.')
        if not c:
            ra['lech_dem'].append(f'{lop}: ô {o} không có công thức COUNTA nào.')

    return ra

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 KHO TKB THEO TUẦN — lưu bản thật của từng tuần, sau xem lại được
--------------------------------------------------------------------------
 MÔ-ĐUN NÀY KHÔNG BIẾT EXCEL LÀ GÌ. Nó nhận một ĐƯỜNG DẪN TỆP và (tuỳ chọn)
 một DICT đã tách sẵn; nó không mở tệp ra đọc nội dung. Việc đọc là của
 `doc_tkb.py`. Cắt như vậy để đổi định dạng tệp sau này không phải sửa kho,
 và để Đợt 4 dùng lại `doc_tkb.py` mà không kéo theo cả kho.

 BỐ CỤC:
     luu_tru/                              <- GITIGNORE
       2026-08-24/                         <- MÃ TUẦN = ngày Thứ Hai
         phieu.json
         ban/  2026-08-22T09-10-05_<tên>.xlsx     tệp GỐC
         tach/ 2026-08-22T09-10-05.json           dữ liệu ĐÃ TÁCH

 BỐN LUẬT KHÔNG ĐƯỢC PHÁ:

 1. KHÔNG BAO GIỜ ĐÈ. Tên tệp mang giờ lưu; trùng giây thì thêm hậu tố.
    Không có đường nào trong mô-đun này ghi lên một tệp `ban/` đã tồn tại.

 2. NẠP LẠI TỆP TRÙNG (cùng SHA-256) thì TỪ CHỐI, và nói rõ trùng bản nào,
    lưu lúc nào. KHÔNG ghi thêm gì vào `phieu.json` — kể cả một dòng nhật ký.

 3. `phieu.json` GHI NGUYÊN TỬ + fsync (`ghi_ben.ghi_nguyen_tu(..., ben=True)`).
    Nó là MỤC LỤC: hỏng nó là mất lịch sử cả tuần, trong khi các tệp `ban/`
    vẫn nằm đó mà không ai biết chúng là của tuần nào.

 4. KHOÁ TUẦN LÀ NGÀY, KHÔNG PHẢI NHÃN. `"TUẦN 1"` lặp lại mỗi học kỳ nên
    không bao giờ được dùng làm khoá; nó chỉ là `nhan`, một chuỗi để đọc.

 ⚠ `luu_tru/` ĐÃ GITIGNORE — git KHÔNG phải bản sao lưu của kho này. Mất ổ
 là mất cả năm học. Lệnh chép sang ổ khác ghi ở `CHAY_CUNG_MAY.md` mục 10.
==========================================================================
"""
import datetime
import hashlib
import io
import json
import os
import re
import shutil

import ghi_ben as GB

TEN_KHO = 'luu_tru'
TEN_PHIEU = 'phieu.json'
MAU_MA_TUAN = re.compile(r'^\d{4}-\d{2}-\d{2}$')
# Tên tệp an toàn: bỏ mọi thứ có thể đi ra khỏi thư mục hoặc phá vỏ lệnh.
MAU_BAN = re.compile(r'[^0-9A-Za-zÀ-ỹ._-]+')

# --------------------------------------------------------------------------
# TRẠNG THÁI CỦA MỘT BẢN — "bản này có dùng được không"
# --------------------------------------------------------------------------
# Vì sao phải có: một tuần có thể có NHIỀU bản mâu thuẫn nhau, và phiếu phải
# ghi được bản nào dùng được. Đã xảy ra thật — tuần 2026-08-24 có hai bản, bản
# 21/8 bỏ mất 6 tiết chuyên đề Sử và đổi giáo viên; Khoa xác nhận 22/8/2026 là
# bản đó SAI. Không có trường này thì cả hai bản nằm cạnh nhau, trông như nhau.
#
# KHÔNG XOÁ BẢN SAI. Nó là bằng chứng, và là ca thử thật duy nhất đang có.
TRANG_THAI = ('dung', 'sai', 'chua_ro')
TRANG_THAI_MAC_DINH = 'chua_ro'


def kiem_trang_thai(tt, ly_do):
    """Trả (ok, câu). `ly_do` BẮT BUỘC khi nói "dung" hoặc "sai".

       Vì sao bắt buộc: một bản bị đánh dấu SAI mà không nói vì sao thì sáu
       tháng nữa không ai dám tin cái dấu đó, và sẽ có người gỡ nó ra.
    """
    if tt not in TRANG_THAI:
        return False, (f'trang_thai phải là một trong {TRANG_THAI}, '
                       f'nhận được {tt!r}.')
    if tt in ('dung', 'sai') and not (ly_do or '').strip():
        return False, (f'Đánh dấu {tt!r} thì PHẢI ghi ly_do. Một bản bị đánh '
                       'dấu mà không nói vì sao thì cái dấu đó không đáng tin.')
    return True, None


def goc_mac_dinh():
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), TEN_KHO)


# ==========================================================================
def kiem_ma_tuan(ma):
    """Trả (ok, câu giải thích). Mã tuần PHẢI là một ngày có thật.

       KHÔNG tự sửa, KHÔNG tự suy ra Thứ Hai gần nhất. Nếu người dùng đưa một
       ngày không phải Thứ Hai thì đây CẢNH BÁO chứ không chặn — trường có thể
       tính tuần từ Chủ Nhật (tệp tuần 1 của trường ghi 23/8/2026, và 23/8 là
       CHỦ NHẬT). Câu hỏi đó chưa ai trả lời, nên mô-đun này không quyết hộ.
    """
    if not isinstance(ma, str) or not MAU_MA_TUAN.match(ma):
        return False, ('Mã tuần phải có dạng NĂM-THÁNG-NGÀY, ví dụ 2026-08-24. '
                       f'Nhận được: {ma!r}')
    try:
        d = datetime.date.fromisoformat(ma)
    except ValueError:
        return False, f'{ma!r} không phải một ngày có thật.'
    if d.weekday() != 0:
        T = ['Thứ Hai', 'Thứ Ba', 'Thứ Tư', 'Thứ Năm', 'Thứ Sáu',
             'Thứ Bảy', 'Chủ Nhật']
        return True, (f'Lưu ý: {ma} là {T[d.weekday()]}, không phải Thứ Hai. '
                      'Thiết kế đang lấy ngày Thứ Hai làm khoá tuần — nếu '
                      'trường tính tuần từ ngày khác thì đây là điều cần '
                      'thống nhất trước, không phải chuyện phần mềm tự quyết.')
    return True, None


def thu_muc_tuan(goc, ma_tuan):
    return os.path.join(goc, ma_tuan)


def duong_phieu(goc, ma_tuan):
    return os.path.join(thu_muc_tuan(goc, ma_tuan), TEN_PHIEU)


def bam_tep(duong_dan):
    """SHA-256 của cả tệp. Đọc theo mẩu để tệp to không ngốn bộ nhớ."""
    h = hashlib.sha256()
    with open(duong_dan, 'rb') as f:
        for mau in iter(lambda: f.read(1 << 20), b''):
            h.update(mau)
    return h.hexdigest()


def doc_phieu(goc, ma_tuan):
    """Trả dict phiếu, hoặc None nếu chưa có. TOÀN PHẦN: hỏng -> None.

       Hỏng thì trả None chứ không ném, nhưng người gọi PHẢI phân biệt được
       "chưa có tuần này" với "phiếu hỏng" — nên dùng `doc_phieu_ky()`.
    """
    ra, _ = doc_phieu_ky(goc, ma_tuan)
    return ra


def doc_phieu_ky(goc, ma_tuan):
    """Trả (phiếu|None, lỗi|None). Chưa có tuần -> (None, None)."""
    dd = duong_phieu(goc, ma_tuan)
    if not os.path.exists(dd):
        return None, None
    try:
        with io.open(dd, encoding='utf-8-sig') as f:
            p = json.load(f)
    except Exception as e:                              # noqa: BLE001
        return None, f'{dd} hỏng, không đọc được: {type(e).__name__}: {e}'
    if not isinstance(p, dict) or not isinstance(p.get('ban'), list):
        return None, (f'{dd} sai cấu trúc: phải là một object có khoá "ban" '
                      'là một dãy.')
    return p, None


def _ten_ban(gio, ten_goc):
    """Tên tệp trong ban/: giờ lưu đứng trước để xếp theo thứ tự thời gian."""
    goc = MAU_BAN.sub('_', os.path.basename(ten_goc or 'TKB.xlsx')).strip('_')
    return f'{gio}_{goc or "TKB.xlsx"}'


def _gio_ten(khi):
    """Giờ lưu dạng dùng được trong tên tệp (không có dấu ':')."""
    return khi.strftime('%Y-%m-%dT%H-%M-%S')


# ==========================================================================
def them_ban(goc, ma_tuan, duong_tep, nguoi, ghi_chu='', tach=None,
             nhan=None, tu_ngay=None, den_ngay=None, nam_hoc=None,
             hoc_ky=None, khi=None, trang_thai=None, ly_do=''):
    """Thêm MỘT bản vào tuần. Trả dict kết quả. KHÔNG BAO GIỜ NÉM.

       Kết quả luôn có khoá `ok` (bool) và `cau` (câu tiếng Việt cho người
       dùng). `ok=False` thì KHÔNG có gì được ghi xuống đĩa.

       `tach` là dict do `doc_tkb.doc()` trả về — mô-đun này không tự đọc tệp.
       Truyền None thì chỉ lưu tệp gốc, không lưu bản tách.
    """
    ra = {'ok': False, 'cau': '', 'canh_bao': [], 'ban': None}

    ok, cau = kiem_ma_tuan(ma_tuan)
    if not ok:
        ra['cau'] = cau
        return ra
    if cau:
        ra['canh_bao'].append(cau)

    if not duong_tep or not os.path.exists(duong_tep):
        ra['cau'] = f'Không có tệp để lưu: {duong_tep!r}'
        return ra
    if not os.path.isfile(duong_tep):
        ra['cau'] = f'{duong_tep!r} không phải một tệp.'
        return ra
    trang_thai = trang_thai or TRANG_THAI_MAC_DINH
    ok, cau = kiem_trang_thai(trang_thai, ly_do)
    if not ok:
        ra['cau'] = cau
        return ra

    if not (nguoi or '').strip():
        ra['cau'] = ('Phải ghi TÊN NGƯỜI LƯU. Không có tên thì phiếu không nói '
                     'được ai đưa bản này vào, và đó là cả điểm của việc lưu.')
        return ra

    phieu, loi = doc_phieu_ky(goc, ma_tuan)
    if loi:
        ra['cau'] = (loi + '\n      KHÔNG ghi đè lên phiếu hỏng — sửa hoặc '
                     'đổi tên nó rồi chạy lại, để không mất danh sách bản cũ.')
        return ra

    # --- LUẬT 2: trùng SHA-256 thì TỪ CHỐI, không ghi một chữ nào ---
    try:
        bam = bam_tep(duong_tep)
    except OSError as e:
        ra['cau'] = f'Không đọc được tệp: {e}'
        return ra
    if phieu:
        for b in phieu.get('ban') or []:
            if isinstance(b, dict) and b.get('sha256') == bam:
                ra['cau'] = (
                    f'TỪ CHỐI — tệp này y hệt bản đã lưu.\n'
                    f'      Trùng với : {b.get("tep")}\n'
                    f'      Lưu lúc   : {b.get("gio_luu")}\n'
                    f'      Người lưu : {b.get("nguoi_luu")}\n'
                    f'      SHA-256   : {bam}\n'
                    f'      Không ghi gì thêm vào phiếu.')
                ra['trung'] = b
                return ra

    khi = khi or datetime.datetime.now().astimezone()
    gio = _gio_ten(khi)
    tm = thu_muc_tuan(goc, ma_tuan)
    tm_ban, tm_tach = os.path.join(tm, 'ban'), os.path.join(tm, 'tach')
    try:
        os.makedirs(tm_ban, exist_ok=True)
        os.makedirs(tm_tach, exist_ok=True)
    except OSError as e:
        ra['cau'] = f'Không tạo được thư mục kho: {e}'
        return ra

    # --- LUẬT 1: KHÔNG BAO GIỜ ĐÈ ---
    ten = _ten_ban(gio, duong_tep)
    dich = os.path.join(tm_ban, ten)
    k = 1
    while os.path.exists(dich):
        k += 1
        ten = _ten_ban(f'{gio}-{k}', duong_tep)
        dich = os.path.join(tm_ban, ten)
        if k > 500:
            ra['cau'] = 'Quá nhiều bản trùng tên trong cùng một giây — dừng.'
            return ra
    try:
        GB.chep_ben(duong_tep, dich)
    except OSError as e:
        ra['cau'] = f'Không chép được tệp vào kho: {e}'
        return ra

    ten_tach = None
    if tach is not None:
        ten_tach = os.path.splitext(ten)[0] + '.json'
        try:
            GB.ghi_nguyen_tu(os.path.join(tm_tach, ten_tach),
                             json.dumps(tach, ensure_ascii=False, indent=1),
                             ben=True)
        except OSError as e:
            ra['canh_bao'].append(f'Lưu được tệp gốc nhưng KHÔNG lưu được bản '
                                  f'tách: {e}')
            ten_tach = None

    ban = {'tep': f'ban/{ten}', 'tach': f'tach/{ten_tach}' if ten_tach else None,
           'gio_luu': khi.isoformat(timespec='seconds'), 'sha256': bam,
           'nguoi_luu': nguoi.strip(), 'ghi_chu': (ghi_chu or '').strip(),
           'ten_goc': os.path.basename(duong_tep),
           'trang_thai': trang_thai, 'ly_do': (ly_do or '').strip()}
    if tach is not None:
        ban['bo_doc'] = tach.get('bo_doc')

    if phieu is None:
        phieu = {'ma_tuan': ma_tuan, 'nhan': nhan, 'tu_ngay': tu_ngay,
                 'den_ngay': den_ngay, 'nam_hoc': nam_hoc, 'hoc_ky': hoc_ky,
                 'ban': []}
    else:
        # Khai báo tuần đã có thì GIỮ NGUYÊN, chỉ điền chỗ còn trống.
        for k2, v in (('nhan', nhan), ('tu_ngay', tu_ngay),
                      ('den_ngay', den_ngay), ('nam_hoc', nam_hoc),
                      ('hoc_ky', hoc_ky)):
            if phieu.get(k2) in (None, '') and v not in (None, ''):
                phieu[k2] = v
            elif v not in (None, '') and phieu.get(k2) != v:
                ra['canh_bao'].append(
                    f'Phiếu đang ghi {k2} = {phieu.get(k2)!r}, lần này đưa vào '
                    f'{v!r} — GIỮ giá trị cũ. Muốn đổi thì sửa phiếu tay.')
    phieu['ban'].append(ban)

    try:
        GB.ghi_nguyen_tu(duong_phieu(goc, ma_tuan),
                         json.dumps(phieu, ensure_ascii=False, indent=1) + '\n',
                         ben=True)
    except OSError as e:
        ra['cau'] = (f'Đã chép tệp vào {dich} nhưng KHÔNG ghi được phiếu: {e}\n'
                     '      Tệp còn đó, nhưng phiếu chưa biết tới nó.')
        return ra

    ra['ok'] = True
    ra['ban'] = ban
    ra['cau'] = f'Đã lưu {ban["tep"]} vào tuần {ma_tuan}.'
    return ra


def trang_thai_cua(ban):
    """Trạng thái của một bản, TOÀN PHẦN. Bản ghi cũ thiếu khoá -> "chua_ro".

       Thiếu khoá KHÔNG được coi là "dung". Phiếu ghi từ trước khi có trường
       này thì đúng là chưa ai xét, và chưa xét thì chưa dùng được.
    """
    if not isinstance(ban, dict):
        return TRANG_THAI_MAC_DINH
    tt = ban.get('trang_thai')
    return tt if tt in TRANG_THAI else TRANG_THAI_MAC_DINH


def ban_de_dang(goc, ma_tuan):
    """CỬA CHẶN ĐƯỜNG ĐĂNG. Trả (danh sách bản dùng được, câu từ chối|None).

       ┌────────────────────────────────────────────────────────────────────┐
       │ MỌI ĐƯỜNG ĐĂNG PHẢI ĐI QUA ĐÂY. Đừng đọc thẳng `phieu['ban']` rồi  │
       │ tự lọc — đó là bản cài thứ hai, và bản thứ hai sẽ lệch.            │
       └────────────────────────────────────────────────────────────────────┘

       CHỈ trả bản `trang_thai == "dung"`. Hai trạng thái kia đều bị chặn:

         "sai"     — đã biết là sai. Hiển nhiên.
         "chua_ro" — CHƯA AI XÉT. Cũng chặn, và đây là chỗ dễ cãi nhất:
                     mặc định của một bản mới là "chua_ro", nên nếu cho nó
                     qua thì cửa này KHÔNG chặn gì cả trong trường hợp
                     thường gặp nhất. Fail-closed: chưa biết đúng thì chưa
                     đăng. Cái giá là phải đánh dấu tay một lần mỗi tuần —
                     rẻ hơn nhiều so với đăng nhầm một bản sai, vì trang
                     công khai thì cả trường đọc, và git thì nhớ vĩnh viễn.
    """
    p, loi = doc_phieu_ky(goc, ma_tuan)
    if loi:
        return [], f'Phiếu tuần {ma_tuan} hỏng: {loi}'
    if p is None:
        return [], f'Kho chưa có tuần {ma_tuan}.'
    ds = [b for b in (p.get('ban') or []) if trang_thai_cua(b) == 'dung']
    if ds:
        return ds, None
    dem = {}
    for b in p.get('ban') or []:
        t = trang_thai_cua(b)
        dem[t] = dem.get(t, 0) + 1
    return [], (
        f'Tuần {ma_tuan} KHÔNG có bản nào đánh dấu "dung" — không đăng gì cả.\n'
        f'      Đang có: {dem or "(không bản nào)"}.\n'
        '      Đánh dấu bằng: luu_tuan.py danh-dau --tuan <mã> --ban <n> '
        '--trang-thai dung --ly-do "..."')


def danh_dau_ban(goc, ma_tuan, chi_so, trang_thai, ly_do=''):
    """Đặt trạng thái cho MỘT bản đã lưu. `chi_so` đếm từ 1. KHÔNG BAO GIỜ NÉM.

       KHÔNG xoá bản nào, không đụng tệp `ban/` — chỉ sửa phiếu.
    """
    ra = {'ok': False, 'cau': '', 'ban': None}
    ok, cau = kiem_trang_thai(trang_thai, ly_do)
    if not ok:
        ra['cau'] = cau
        return ra
    p, loi = doc_phieu_ky(goc, ma_tuan)
    if loi:
        ra['cau'] = loi + '\n      KHÔNG ghi đè lên phiếu hỏng.'
        return ra
    if p is None:
        ra['cau'] = f'Kho chưa có tuần {ma_tuan}.'
        return ra
    ds = p.get('ban') or []
    if not isinstance(chi_so, int) or not (1 <= chi_so <= len(ds)):
        ra['cau'] = (f'Số thứ tự bản phải từ 1 đến {len(ds)}, '
                     f'nhận được {chi_so!r}.')
        return ra
    b = ds[chi_so - 1]
    cu = trang_thai_cua(b)
    b['trang_thai'] = trang_thai
    b['ly_do'] = (ly_do or '').strip()
    try:
        GB.ghi_nguyen_tu(duong_phieu(goc, ma_tuan),
                         json.dumps(p, ensure_ascii=False, indent=1) + '\n',
                         ben=True)
    except OSError as e:
        ra['cau'] = f'Không ghi được phiếu: {e}'
        return ra
    ra['ok'] = True
    ra['ban'] = b
    ra['cau'] = (f'Bản {chi_so} ({b.get("tep")}) : {cu} -> {trang_thai}.')
    return ra


def sua_tuan(goc, ma_tuan, **doi):
    """Sửa khai báo cấp TUẦN (tu_ngay, den_ngay, nhan, nam_hoc, hoc_ky,
       ghi_chu). KHÔNG đụng danh sách bản. KHÔNG BAO GIỜ NÉM."""
    CHO_PHEP = ('tu_ngay', 'den_ngay', 'nhan', 'nam_hoc', 'hoc_ky', 'ghi_chu')
    ra = {'ok': False, 'cau': '', 'doi': {}}
    la = [k for k in doi if k not in CHO_PHEP]
    if la:
        ra['cau'] = f'Khoá lạ: {la}. Chỉ sửa được {CHO_PHEP}.'
        return ra
    p, loi = doc_phieu_ky(goc, ma_tuan)
    if loi:
        ra['cau'] = loi + '\n      KHÔNG ghi đè lên phiếu hỏng.'
        return ra
    if p is None:
        ra['cau'] = f'Kho chưa có tuần {ma_tuan}.'
        return ra
    for k, v in doi.items():
        if v is not None:
            ra['doi'][k] = (p.get(k), v)
            p[k] = v
    if not ra['doi']:
        ra['cau'] = 'Không có gì để sửa.'
        return ra
    try:
        GB.ghi_nguyen_tu(duong_phieu(goc, ma_tuan),
                         json.dumps(p, ensure_ascii=False, indent=1) + '\n',
                         ben=True)
    except OSError as e:
        ra['cau'] = f'Không ghi được phiếu: {e}'
        return ra
    ra['ok'] = True
    ra['cau'] = ' · '.join(f'{k}: {a!r} -> {b!r}' for k, (a, b) in ra['doi'].items())
    return ra


def duong_ban(goc, ma_tuan, ban):
    """Đường dẫn thật tới tệp gốc của một bản. TOÀN PHẦN: thiếu -> None."""
    if not isinstance(ban, dict) or not ban.get('tep'):
        return None
    return os.path.join(thu_muc_tuan(goc, ma_tuan), ban['tep'])


def chon_ban(goc, ma_tuan, chi_so=None):
    """Chọn MỘT bản để đối chiếu. Trả (bản|None, câu lỗi|None).

       `chi_so` None thì lấy bản duy nhất đánh dấu "dung". KHÔNG đoán khi có
       nhiều lựa chọn — bắt người gõ `--ban`.
    """
    p, loi = doc_phieu_ky(goc, ma_tuan)
    if loi:
        return None, loi
    if p is None:
        return None, f'Kho chưa có tuần {ma_tuan}.'
    ds = p.get('ban') or []
    if not ds:
        return None, f'Tuần {ma_tuan} chưa có bản nào.'
    if chi_so is not None:
        if not isinstance(chi_so, int) or not (1 <= chi_so <= len(ds)):
            return None, f'Số thứ tự bản phải từ 1 đến {len(ds)}.'
        return ds[chi_so - 1], None
    dung = [b for b in ds if trang_thai_cua(b) == 'dung']
    if len(dung) == 1:
        return dung[0], None
    if not dung:
        return None, (f'Tuần {ma_tuan} chưa có bản nào đánh dấu "dung", nên '
                      'không tự chọn được. Gõ thêm --ban <n> để chỉ rõ. '
                      f'Đang có {len(ds)} bản.')
    return None, (f'Tuần {ma_tuan} có {len(dung)} bản đánh dấu "dung" — không '
                  'tự chọn được. Gõ thêm --ban <n>.')


def liet_ke(goc):
    """Mọi tuần trong kho, mới nhất trước. TOÀN PHẦN: kho chưa có -> []."""
    if not os.path.isdir(goc):
        return []
    ra = []
    for ten in sorted(os.listdir(goc), reverse=True):
        if not MAU_MA_TUAN.match(ten):
            continue
        p, loi = doc_phieu_ky(goc, ten)
        ds = (p.get('ban') or []) if p else []
        dem = {}
        for b in ds:
            t = trang_thai_cua(b)
            dem[t] = dem.get(t, 0) + 1
        ra.append({'ma_tuan': ten, 'phieu': p, 'loi': loi,
                   'so_ban': len(ds), 'theo_trang_thai': dem})
    return ra

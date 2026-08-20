#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 TÀI KHOẢN ĐĂNG NHẬP CHO MÁY CHỦ QUẢN TRỊ
--------------------------------------------------------------------------
 Tệp này CHỈ lo việc đọc/ghi tai_khoan.json và băm mật khẩu. Nó không biết
 gì về HTTP, phiên hay cookie — web.py gọi vào đây.

 Tách hẳn ra một tệp riêng để hai việc khác nhau không lẫn: tao_mat_khau.py
 (chạy tay, có bàn phím) và web.py (chạy nền) cùng dùng ĐÚNG MỘT bản cài của
 phép băm và phép chuẩn hoá tên. Chép hai bản là kiểu lệch đã trả giá một lần
 ở khop_loc() / _cum_cua().

 TỆP tai_khoan.json BỊ GITIGNORE. Bản mẫu tai_khoan.json.mau thì được commit,
 để cài lại máy còn biết cấu trúc.
==========================================================================
"""
import hashlib
import hmac
import json
import os
import re
import secrets
import sys
import threading
import time

# --------------------------------------------------------------------------
# Tham số băm — CHỈ MỘT BỘ, không có bảng kẹp miền.
#
# Đã đo trên máy này: n=2**15 và n=2**16 đều ném ValueError "memory limit
# exceeded" với maxmem mặc định của OpenSSL. Nên "cho phép một miền rộng" mà
# không truyền maxmem tường minh là một lời hứa suông — người sửa tệp thành
# n=32768 sẽ làm máy chủ hỏng ở MỖI lần đăng nhập, mà thông báo lại là một mã
# sự cố 6 ký tự vô nghĩa.
#
# Chỉ nhận đúng một bộ thì "mọi tài khoản chung tham số" đúng THEO CẤU TRÚC,
# không phải một luật phải nhớ. Đổi tham số sau này = tăng PHIEN_BAN và viết
# đường nâng cấp tử tế.
THAM_SO = {'thuat_toan': 'scrypt', 'n': 16384, 'r': 8, 'p': 1, 'dklen': 32}
MAXMEM = 132 * 16384 * 8                 # tường minh, không dựa vào mặc định
PHIEN_BAN = 1

DAI_MAT_KHAU_TOI_THIEU = 12              # QĐ 5
MAU_TEN = re.compile(r'[a-z0-9._-]{3,32}')


def chuan_ten(ten):
    """Chuẩn hoá tên đăng nhập, hoặc None nếu không hợp lệ.

       Giới hạn ASCII thường: nếu cho tên có dấu thì "Quản Trị" gõ trên hai máy
       có thể ra hai chuỗi byte khác nhau (NFC/NFD), và .lower() trên Unicode
       tiếng Việt cũng không ổn định — hậu quả là KHÔNG AI ĐĂNG NHẬP ĐƯỢC mà
       thông báo lại là câu chung "tên hoặc mật khẩu không đúng", nên thầy cô sẽ
       đi đổi mật khẩu mãi mà không ra.

       TRẢ None chứ không ném: trên đường đăng nhập, tên sai cú pháp phải đi
       tiếp vào nhánh bản-ghi-giả để tốn đúng một lần scrypt như mọi nhánh khác.
       Ném ở đây là tạo một lối thoát nhanh, tức là một kênh đo thời gian.
    """
    if not isinstance(ten, str):
        return None
    t = ten.strip().lower()
    return t if MAU_TEN.fullmatch(t) else None


def bam(mat_khau, muoi_hex):
    """Băm mật khẩu. Trả chuỗi hex 64 ký tự.

       Đây là hàm TỐN TIỀN của cả hệ thống: đo được 27,3 ms và cấp phát 16 MB
       mỗi lần gọi, mà scrypt NHẢ GIL nên nhiều lời gọi chạy song song thật.
       Người gọi phải tự lo chặn số lần chạy cùng lúc.
    """
    if not isinstance(mat_khau, str):
        mat_khau = ''
    d = hashlib.scrypt(mat_khau.encode('utf-8'), salt=bytes.fromhex(muoi_hex),
                       n=THAM_SO['n'], r=THAM_SO['r'], p=THAM_SO['p'],
                       dklen=THAM_SO['dklen'], maxmem=MAXMEM)
    return d.hex()


def ban_ghi_moi(ten, mat_khau):
    muoi = secrets.token_bytes(16).hex()
    return {'ten_dang_nhap': ten, 'muoi': muoi, 'bam': bam(mat_khau, muoi),
            'ngay_tao': time.strftime('%Y-%m-%dT%H:%M:%S'), 'bat': True}


def ban_ghi_gia():
    """Bản ghi GIẢ để nhánh "tên không tồn tại" vẫn chạy đúng một lần scrypt.

       Muối ngẫu nhiên, sinh MỘT LẦN lúc khởi động, KHÔNG ghi ra tệp. Thời gian
       chạy scrypt phụ thuộc n/r/p chứ không phụ thuộc muối, nên muối gì cũng
       được — nhưng cố định trong một lần chạy thì phản ánh đúng cấu trúc bên
       thật, và đỡ một lần os.urandom mỗi yêu cầu.
    """
    muoi = secrets.token_bytes(16).hex()
    return {'ten_dang_nhap': '\x00khong-ton-tai', 'muoi': muoi,
            'bam': secrets.token_bytes(32).hex(), 'ngay_tao': '', 'bat': False}


def kiem_mat_khau(mat_khau):
    """None = đạt; ngược lại trả câu tiếng Việt nói rõ sai chỗ nào."""
    if not isinstance(mat_khau, str) or len(mat_khau) < DAI_MAT_KHAU_TOI_THIEU:
        n = len(mat_khau) if isinstance(mat_khau, str) else 0
        return (f'Mật khẩu phải dài ít nhất {DAI_MAT_KHAU_TOI_THIEU} ký tự '
                f'(đang có {n}).\n'
                f'Gợi ý: ghép 3–4 từ dễ nhớ, ví dụ "khoa-co-ban-da-lat".')
    de_doan = {'123456789012', 'matkhaucuatoi', 'thoikhoabieu', 'khoahoccoban',
               'password1234', 'quantriquantri', 'aaaaaaaaaaaa'}
    if mat_khau.strip().lower() in de_doan:
        return 'Mật khẩu này quá dễ đoán. Hãy chọn mật khẩu khác.'
    return None


# ==========================================================================
# ĐỌC TỆP — FAIL-CLOSED BỐN NHÁNH
# ==========================================================================

def _loi(cau):
    raise SystemExit(
        f'[LỖI] {cau}\n'
        f'      Máy chủ KHÔNG khởi động khi chưa có tài khoản hợp lệ.\n'
        f'      Đặt tài khoản một lần bằng:\n'
        f'          python3 tao_mat_khau.py them\n'
        f'          (trên Windows: bấm đúp tao_tai_khoan.bat)')


def nap(duong_dan):
    """Đọc tai_khoan.json. Trả dict {ten: bản ghi} của tài khoản ĐANG BẬT.

       NÉM SystemExit ở cả bốn nhánh hỏng — không có / hỏng / rỗng / sai kiểu.
       Tuyệt đối không tự đặt mật khẩu mặc định, không lặng lẽ bỏ qua.

       Hàm này THUẦN (chỉ đọc, chỉ ném) để dễ thử. Người gọi quyết định làm gì
       với ngoại lệ: web.main() in ra rồi sys.exit(1), ca thử thì bắt lấy.
    """
    if not os.path.exists(duong_dan):
        _loi(f'Chưa có tệp {os.path.basename(duong_dan)}.\n'
             f'      Đang tìm ở: {duong_dan}')
    try:
        with open(duong_dan, encoding='utf-8-sig') as f:
            cfg = json.load(f)
    except (OSError, ValueError) as e:
        _loi(f'Không đọc được {os.path.basename(duong_dan)}: {e}')

    if not isinstance(cfg, dict):
        _loi(f'{os.path.basename(duong_dan)} phải là một khối {{ ... }}')
    if cfg.get('phien_ban') != PHIEN_BAN:
        _loi(f'{os.path.basename(duong_dan)} khai "phien_ban": '
             f'{cfg.get("phien_ban")!r}, bản này chỉ hiểu {PHIEN_BAN}.')
    ds = cfg.get('tai_khoan')
    if not isinstance(ds, list):
        _loi(f'Trong {os.path.basename(duong_dan)}, mục "tai_khoan" phải là '
             f'một DÃY [ ... ] — mỗi người một bản ghi.')

    ra = {}
    for i, bg in enumerate(ds):
        cho = f'tài khoản thứ {i + 1}'
        if not isinstance(bg, dict):
            _loi(f'{cho} không phải một khối {{ ... }}')
        ten = chuan_ten(bg.get('ten_dang_nhap'))
        if ten is None:
            _loi(f'{cho} có "ten_dang_nhap" không hợp lệ: '
                 f'{bg.get("ten_dang_nhap")!r}\n'
                 f'      Tên chỉ gồm a-z 0-9 . _ - và dài 3–32 ký tự.')
        for khoa, dai in (('muoi', 32), ('bam', 64)):
            gt = bg.get(khoa)
            # Kiểm ĐỘ DÀI CHUỖI trước khi fromhex: đã đo bytes.fromhex('ab cd')
            # cho ra abcd, tức nó bỏ qua khoảng trắng — nên chỉ fromhex không
            # đủ để bắt một tệp bị Notepad làm hỏng.
            if not isinstance(gt, str) or len(gt) != dai:
                _loi(f'{cho}: khoá "{khoa}" phải là chuỗi hex {dai} ký tự.')
            try:
                bytes.fromhex(gt)
            except ValueError:
                _loi(f'{cho}: khoá "{khoa}" không phải chữ số hex.')
        if not isinstance(bg.get('bat', True), bool):
            _loi(f'{cho}: khoá "bat" phải là true hoặc false.')
        if ten in ra:
            _loi(f'{cho}: tên "{ten}" bị khai hai lần.')
        ra[ten] = dict(bg, ten_dang_nhap=ten)

    dang_bat = {t: b for t, b in ra.items() if b.get('bat', True)}
    if not dang_bat:
        _loi(f'{os.path.basename(duong_dan)} không có tài khoản nào ĐANG BẬT '
             f'({len(ra)} tài khoản, tất cả đều "bat": false).')
    return dang_bat


# ==========================================================================
# GHI TỆP — nguyên tử + fsync + quyền 600
# ==========================================================================

def ghi(duong_dan, ds):
    """Ghi danh sách tài khoản. Nguyên tử, có fsync, quyền 600 trên POSIX.

       CỐ Ý KHÔNG sao lưu xoay vòng (ngược hẳn A7 của cauhinh.json): bản sao lưu
       của tệp mật khẩu chỉ là rải thêm bí mật ra đĩa. Mất tệp thì đặt lại mất
       mười giây; mất cauhinh.json thì mất hàng giờ khai báo. Hai đánh đổi ngược
       chiều nhau, có chủ ý.

       Tên tệp tạm kèm PID: một lần sập giữa chừng không được phép chặn vĩnh
       viễn mọi lần đổi mật khẩu sau đó.
    """
    _ghi_nguyen_tu(duong_dan,
                   json.dumps({'phien_ban': PHIEN_BAN, 'tai_khoan': ds},
                              ensure_ascii=False, indent=2) + '\n',
                   ben=True)


def _ghi_nguyen_tu(duong_dan, chuoi, ben):
    """Ghi đè một tệp nhỏ: tệp tạm -> os.replace. Quyền 600 ngay lúc tạo.

       `ben=True` thì fsync cả tệp lẫn thư mục cha — dành cho tai_khoan.json,
       tệp mà mất là không ai đăng nhập được nữa. `ben=False` bỏ fsync, dành cho
       sổ khoá tạm: nội dung của nó VỨT ĐI ĐƯỢC (mất thì mọi người được thử lại
       từ đầu, không ai bị khoá oan), mà nó lại bị ghi ở đường CHƯA XÁC THỰC nên
       không đáng để một người gõ sai mật khẩu ép được ta fsync.

       Tên tệp tạm kèm PID: một lần sập giữa chừng không được phép chặn vĩnh
       viễn mọi lần ghi sau đó. Hai tiến trình (web.py và tao_mat_khau.py) cùng
       ghi cũng không đụng nhau vì mỗi bên một tên tạm.
    """
    tam = f'{duong_dan}.tam.{os.getpid()}.json'
    # O_EXCL + 0o600: quyền đặt NGAY LÚC TẠO, không để hở một khe nào ở 644.
    fd = os.open(tam, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(chuoi)
            f.flush()
            if ben:
                os.fsync(f.fileno())
        os.replace(tam, duong_dan)
    except BaseException:
        try:
            os.remove(tam)
        except OSError:
            pass
        raise
    if ben and os.name == 'posix':
        try:
            fdt = os.open(os.path.dirname(os.path.abspath(duong_dan)),
                          os.O_RDONLY)
            try:
                os.fsync(fdt)
            finally:
                os.close(fdt)
        except OSError:
            pass


def doc_tho(duong_dan):
    """Đọc danh sách thô để tao_mat_khau.py sửa. Không có tệp -> dãy rỗng.

       Khác nap(): hàm này KHÔNG kiểm chặt và KHÔNG lọc theo "bat", vì script
       cần thấy cả tài khoản đang tắt để bật lại.
    """
    if not os.path.exists(duong_dan):
        return []
    with open(duong_dan, encoding='utf-8-sig') as f:
        cfg = json.load(f)
    ds = cfg.get('tai_khoan') if isinstance(cfg, dict) else None
    return ds if isinstance(ds, list) else []


def so_khop(a, b):
    """So hai bản băm. hmac.compare_digest, không bao giờ ==."""
    return hmac.compare_digest(str(a), str(b))


# ==========================================================================
# SỔ KHOÁ TẠM — 2B CHỐNG DÒ MẬT KHẨU (QĐ 6)
# --------------------------------------------------------------------------
#  Sai SO_LAN_SAI_TOI_DA lần liên tiếp thì khoá GIAY_KHOA giây. Đếm theo TÀI
#  KHOẢN, không theo địa chỉ IP: sau Tailscale Serve mọi yêu cầu đều tới từ
#  127.0.0.1, nên đếm theo IP là đếm tất cả vào chung một ô.
#
#  VÌ SAO ĐỂ Ở ĐÂY chứ không ở web.py: hai tiến trình cần chung một sổ.
#  web.py ghi vào sổ mỗi lần có người gõ sai; tao_mat_khau.py đọc sổ cho lệnh
#  "liet-ke" và xoá mục cho lệnh "mo-khoa". Trạng thái nằm trong RAM của web.py
#  thì tiến trình kia không có đường nào chạm tới — mà lệnh gỡ khoá tại máy là
#  cửa thoát hiểm bắt buộc khi cả khoa dùng chung MỘT tài khoản.
#
#  TỆP RIÊNG, KHÔNG nhét vào tai_khoan.json: sổ này bị ghi từ /api/dang-nhap —
#  đường CHƯA XÁC THỰC. Không có lý do gì để một người gõ sai mật khẩu chạm được
#  vào tệp chứa bản băm. Sổ cũng KHÔNG chứa bí mật nào: tên tài khoản (đã có
#  trong tai_khoan.json), một bộ đếm, hai mốc thời gian.
#
#  ĐỒNG HỒ TREO TƯỜNG, không phải monotonic. Khác hẳn phiên trình duyệt (web.py
#  dùng CẢ HAI đồng hồ): monotonic của tiến trình này vô nghĩa với tiến trình
#  kia, mà cả điểm của sổ là hai tiến trình cùng đọc. Giá phải trả là đồng hồ
#  nhảy; _kep_khoa_den() chặn chiều nguy hiểm (nhảy LÙI làm khoá dài vô hạn).
# ==========================================================================

# QĐ 6 đặt 5, đã nâng lên 10 sau khi đo — vì cả khoa dùng CHUNG một tài khoản
# nên số lần gõ sai của ba người CỘNG DỒN vào một ô. Đo được (mô phỏng 200.000
# ngày, 3 người, 2%/người/ngày rơi vào cảnh nhớ nhầm mật khẩu):
#     ngưỡng  5 -> khoá oan ~7 lần/năm học,   tốc độ dò tối đa 20 lần/giờ
#     ngưỡng 10 -> khoá oan ~0,15 lần/năm,    tốc độ dò tối đa 40 lần/giờ
# Khoá oan giảm 48 lần, an ninh giảm 2 lần, và vẫn chậm hơn bản KHÔNG khoá
# 6.282 lần (đo trên máy này: scrypt 27,0 ms, KHOA_BAM=2 -> 69,8 lần/giây).
# Trên 10 thì khoá oan không giảm thêm mà an ninh vẫn tiếp tục giảm tuyến tính.
SO_LAN_SAI_TOI_DA = 10                   # QĐ 6, đã duyệt nâng từ 5
GIAY_KHOA = 15 * 60                      # QĐ 6
GIAY_QUEN = 30 * 60                      # QĐ 6 — cửa sổ quên
TRAN_SO_KHOA = 64                        # trần sổ, xem _don_so()
TEN_TEP_KHOA = 'khoa_dang_nhap.json'

# Khoá TRONG MỘT TIẾN TRÌNH: đọc-sửa-ghi phải liền một mạch. Xem ghi chú dài ở
# ghi_nhan_thu() về vì sao tách kiểm và tăng ra hai lần giữ khoá là một lỗ.
_KHOA_SO = threading.Lock()


def duong_dan_khoa(dd_tai_khoan):
    """Sổ khoá tạm nằm CẠNH tai_khoan.json, suy ra từ đường dẫn của nó.

       Suy ra chứ không khai riêng: web.py có cờ --tai-khoan cho ca thử, và mọi
       ca thử dựng máy chủ trong thư mục tạm. Khai một đường dẫn thứ hai là mở
       đường cho ca thử này ghi đè sổ của ca thử kia — kiểu phụ thuộc THỨ TỰ
       CHẠY đã trả giá một lần ở nap_cau_hinh_may_chu().
    """
    return os.path.join(os.path.dirname(os.path.abspath(dd_tai_khoan)),
                        TEN_TEP_KHOA)


def _kep_khoa_den(den, bay_gio):
    """Chặn mốc hết khoá nhảy quá xa về tương lai.

       Đồng hồ treo tường nhảy LÙI (NTP chỉnh, người dùng đổi múi giờ) thì một
       mốc ghi lúc trước bỗng thành "còn 3 tiếng nữa mới hết khoá". Kẹp lại
       GIAY_KHOA là chặn đúng chiều nguy hiểm; chiều kia (nhảy TỚI làm hết khoá
       sớm) chỉ mất một phần của 15 phút, không đáng đổi lấy thêm cơ chế.
    """
    den = float(den or 0)
    if den <= 0:
        return 0.0
    return min(den, bay_gio + GIAY_KHOA)


def _doc_so(dd):
    """Đọc sổ. Hỏng / thiếu / sai kiểu -> sổ RỖNG và KÊU TO ra cửa sổ lệnh.

       FAIL-OPEN CÓ CHỦ Ý, ngược với nap() ở trên — và đây là lý do:
         · Chiều kia ("hỏng thì coi như khoá hết") biến một byte lỗi thành cảnh
           cả khoa không ai vào được, mà cách chữa duy nhất là ra tận máy. Khoá
           tạm là lớp phòng thủ THÊM; lớp chính là chính mật khẩu, và nó vẫn
           nguyên vẹn khi sổ hỏng.
         · Kẻ tấn công KHÔNG gây được hỏng: chỉ web.py ghi tệp này, và ghi
           nguyên tử. Hỏng nghĩa là đĩa lỗi hoặc có người sửa tay.
         · Lần gõ sai kế tiếp ghi đè sổ, nên bộ đếm tự lên đạn lại ngay.
    """
    if not os.path.exists(dd):
        return {}
    try:
        with open(dd, encoding='utf-8-sig') as f:
            cfg = json.load(f)
        so = cfg['khoa'] if isinstance(cfg, dict) else None
        if not isinstance(so, dict):
            raise ValueError('thiếu mục "khoa" dạng { ... }')
        ra = {}
        for ten, bg in so.items():
            if not isinstance(bg, dict):
                raise ValueError(f'mục "{ten}" không phải một khối {{ ... }}')
            ra[str(ten)] = {'sai': int(bg.get('sai', 0)),
                            'lan_cuoi': float(bg.get('lan_cuoi', 0)),
                            'khoa_den': float(bg.get('khoa_den', 0))}
        return ra
    except (OSError, ValueError, TypeError, KeyError) as e:
        print(f'[CẢNH BÁO] Không đọc được sổ khoá tạm {dd}: {e}\n'
              f'           Coi như chưa ai bị khoá. Lần gõ sai kế tiếp sẽ ghi '
              f'lại sổ mới.', file=sys.stderr)
        return {}


def _don_so(so, bay_gio):
    """Dọn mục đã quên, rồi kẹp trần. Gọi ngay trước mỗi lần ghi.

       Khoá theo tên tài khoản CÓ THẬT nên sổ vốn không thể phình theo ý khách.
       Trần vẫn phải có: xoá bớt người trong tai_khoan.json thì mục cũ nằm lại
       mãi. Đuổi mục KHÔNG đang khoá trước — đuổi mục đang khoá là tự tay gỡ
       khoá hộ kẻ đang dò.
    """
    ra = {t: b for t, b in so.items()
          if _kep_khoa_den(b['khoa_den'], bay_gio) > bay_gio
          or bay_gio - b['lan_cuoi'] <= GIAY_QUEN}
    while len(ra) > TRAN_SO_KHOA:
        cu = min(ra, key=lambda t: (_kep_khoa_den(ra[t]['khoa_den'],
                                                  bay_gio) > bay_gio,
                                    ra[t]['lan_cuoi']))
        ra.pop(cu)
    return ra


def _ghi_so(dd, so, bay_gio):
    """Ghi sổ. Ghi KHÔNG ĐƯỢC thì kêu to rồi đi tiếp, KHÔNG ném.

       Cùng một lẽ với _doc_so(): thư mục chỉ-đọc, đĩa đầy, quyền sai — không
       có cái nào là lý do để KHÔNG AI ĐĂNG NHẬP ĐƯỢC NỮA. Ném ra ở đây thì
       ngoại lệ chạy suốt lên tầng HTTP và mọi lần gõ mật khẩu, kể cả mật khẩu
       ĐÚNG, đều nhận mã sự cố 6 ký tự vô nghĩa. Khoá tạm là lớp phòng thủ
       THÊM; hỏng nó không được phép làm hỏng cổng đăng nhập.
    """
    try:
        _ghi_nguyen_tu(dd, json.dumps(
            {'_doc': 'Sổ khoá tạm của cổng đăng nhập — do web.py ghi, KHÔNG '
                     'sửa tay. Gỡ khoá bằng: '
                     'python3 tao_mat_khau.py mo-khoa <tên>',
             'phien_ban': PHIEN_BAN, 'khoa': _don_so(so, bay_gio)},
            ensure_ascii=False, indent=2) + '\n', ben=False)
        return True
    except OSError as e:
        print(f'[CẢNH BÁO] Không ghi được sổ khoá tạm {dd}: {e}\n'
              f'           Cổng đăng nhập vẫn chạy, nhưng KHOÁ TẠM KHÔNG CÓ '
              f'TÁC DỤNG cho tới khi ghi lại được.', file=sys.stderr)
        return False


def ghi_nhan_thu(dd, ten, bay_gio=None):
    """Ghi nhận MỘT lần thử của `ten`. Trả số GIÂY còn bị khoá (0 = cho thử).

       KIỂM và TĂNG trong CÙNG một lần giữ khoá. Tách ra hai lần giữ khoá là
       đúng lỗi A4 mà gianh_luot() đã giải: bắn 200 yêu cầu cùng lúc thì cả 200
       đều đọc thấy "chưa khoá" trước khi bộ đếm kịp lên tới ngưỡng, và lọt cả
       200. Đã đo được kiểu đó một lần với cờ "đang chạy".

       Nhánh `truoc >= SO_LAN_SAI_TOI_DA` bên dưới là CHỐT CHẶN cho đúng tình
       huống ấy: mốc hết khoá bình thường do ghi_nhan_sai() đặt (sau khi biết
       mật khẩu sai), nhưng trong một loạt bắn dồn thì mọi yêu cầu còn đang chờ
       scrypt, chưa ai kịp gọi ghi_nhan_sai(). Đặt ở đây nữa thì yêu cầu thứ 6
       trở đi bị chặn ngay, không phải đợi.

       KHÔNG tăng bộ đếm khi đang khoá: gõ thêm trong lúc bị khoá không được
       phép kéo dài thời gian khoá, nếu không thì người sốt ruột bấm lại vài lần
       là tự nhốt mình vô hạn.
    """
    t = time.time() if bay_gio is None else float(bay_gio)
    with _KHOA_SO:
        so = _doc_so(dd)
        bg = so.get(ten) or {'sai': 0, 'lan_cuoi': t, 'khoa_den': 0.0}
        den = _kep_khoa_den(bg['khoa_den'], t)
        if den and t >= den:
            bg, den = {'sai': 0, 'lan_cuoi': t, 'khoa_den': 0.0}, 0.0
        elif not den and t - bg['lan_cuoi'] > GIAY_QUEN:
            bg['sai'] = 0                       # cửa sổ quên 30 phút (QĐ 6)
        if not den:
            truoc = bg['sai']
            bg['sai'] = truoc + 1
            if truoc >= SO_LAN_SAI_TOI_DA:      # chốt chặn, xem docstring
                den = t + GIAY_KHOA
        bg['lan_cuoi'], bg['khoa_den'] = t, den
        so[ten] = bg
        _ghi_so(dd, so, t)
        return max(0, int(den - t + 0.999)) if den else 0


def ghi_nhan_sai(dd, ten, bay_gio=None):
    """Mật khẩu sai. Đủ ngưỡng thì bấm giờ khoá NGAY TỪ LẦN SAI THỨ N.

       Bấm giờ ở đây chứ không đợi lần thử kế tiếp: người sai 5 lần rồi bỏ đi
       hai mươi phút, quay lại mà mới bắt đầu đếm 15 phút thì đó là khoá 35 phút
       chứ không phải 15 — vừa sai lời hứa vừa khó chịu vô cớ.

       Idempotent: đã có mốc rồi thì KHÔNG dời. Dời mốc mỗi lần sai là biến
       "khoá 15 phút" thành "khoá tới khi kẻ dò chán", tức tự tay trao cho hắn
       cái nút nhốt cả khoa ở ngoài.
    """
    t = time.time() if bay_gio is None else float(bay_gio)
    with _KHOA_SO:
        so = _doc_so(dd)
        bg = so.get(ten)
        if bg is None:
            return 0
        den = _kep_khoa_den(bg['khoa_den'], t)
        if not den and bg['sai'] >= SO_LAN_SAI_TOI_DA:
            den = t + GIAY_KHOA
        bg['lan_cuoi'], bg['khoa_den'] = t, den
        so[ten] = bg
        _ghi_so(dd, so, t)
        return max(0, int(den - t + 0.999)) if den else 0


def xoa_khoa(dd, ten, bay_gio=None):
    """Xoá sạch mục của `ten`. Trả True nếu có mục để xoá.

       Ba chỗ gọi: đăng nhập ĐÚNG (bốn lần lỡ tay rải rác trong ngày không được
       cộng dồn thành khoá oan), lệnh "mo-khoa", và lệnh "doi" mật khẩu.
    """
    t = time.time() if bay_gio is None else float(bay_gio)
    with _KHOA_SO:
        so = _doc_so(dd)
        co = so.pop(ten, None) is not None
        if co:
            _ghi_so(dd, so, t)
        return co


def xem_khoa(dd, bay_gio=None):
    """Trả {tên: (số lần sai, số giây còn khoá)} — cho lệnh "liet-ke".

       CHỈ ĐỌC, không ghi: chạy "liet-ke" không được phép làm xê dịch bộ đếm
       của ai.
    """
    t = time.time() if bay_gio is None else float(bay_gio)
    ra = {}
    with _KHOA_SO:
        for ten, bg in _doc_so(dd).items():
            den = _kep_khoa_den(bg['khoa_den'], t)
            con = max(0, int(den - t + 0.999)) if den else 0
            if con or (bg['sai'] and t - bg['lan_cuoi'] <= GIAY_QUEN):
                ra[ten] = (bg['sai'], con)
    return ra

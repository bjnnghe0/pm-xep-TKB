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
        f'          python tao_mat_khau.py them\n'
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
    chuoi = json.dumps({'phien_ban': PHIEN_BAN, 'tai_khoan': ds},
                       ensure_ascii=False, indent=2) + '\n'
    tam = f'{duong_dan}.tam.{os.getpid()}.json'
    # O_EXCL + 0o600: quyền đặt NGAY LÚC TẠO, không để hở một khe nào ở 644.
    fd = os.open(tam, os.O_CREAT | os.O_WRONLY | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(chuoi)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tam, duong_dan)
    except BaseException:
        try:
            os.remove(tam)
        except OSError:
            pass
        raise
    if os.name == 'posix':
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

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 GIAO DIỆN WEB CHO PHẦN MỀM XẾP THỜI KHÓA BIỂU
--------------------------------------------------------------------------
 Chạy:
     python3 web.py                 rồi mở http://127.0.0.1:20266
     python3 web.py --port 8080     đổi cổng
     python3 web.py --cauhinh khac.json

 Tắt: bấm Ctrl+C ở cửa sổ dòng lệnh, hoặc đóng cửa sổ đó.

 CHỈ CHẠY CỤC BỘ trên chính máy này (bind 127.0.0.1), máy khác trong
 mạng KHÔNG vào được. Không dùng thư viện ngoài, không tải gì từ mạng.

 File này chỉ gọi vào xep_tkb.py và quy_tac.py, không sửa gì trong đó.
==========================================================================
"""
import argparse
import copy
import hashlib
import json
import os
import re
import secrets
import shutil
import sys
import threading
import time
import traceback
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import quy_tac as QT
import tai_khoan as TK
import xep_tkb as X

THU_MUC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_WEB = os.path.join(THU_MUC, 'web')
TINH = {'index.html': 'text/html', 'style.css': 'text/css',
        'app.js': 'application/javascript'}

DUONG_DAN_CAUHINH = os.path.join(THU_MUC, 'cauhinh.json')

# --------------------------------------------------------------------------
# Cấu hình MẠNG của máy chủ — tệp RIÊNG, cố ý không nằm trong cauhinh.json.
#
# Vì sao tách hẳn ra: cauhinh.json là tệp thầy cô mở bằng Notepad để sửa dữ
# liệu nhà trường, và nó có thể được đem đi chỗ khác. Tên máy trong mạng riêng
# (ví dụ tên .ts.net của Tailscale) không phải dữ liệu nhà trường, mỗi máy một
# khác, và không việc gì phải đi theo tệp dữ liệu.
#
# Đường dẫn CỐ ĐỊNH cạnh web.py, KHÔNG đi theo --cauhinh: nếu không thì
# "--cauhinh khac.json" sẽ âm thầm đổi luôn cả danh sách máy được phép gọi vào.
DUONG_DAN_MAY_CHU = os.path.join(THU_MUC, 'cauhinh_may_chu.json')

# None = chưa nạp, hoặc tệp thiếu/hỏng/rỗng -> dùng MẶC ĐỊNH loopback.
# Đây là trạng thái ĐÓNG, không phải mở: mặc định chỉ cho chính máy này.
HOST_CHO_PHEP = None
ORIGIN_CHO_PHEP = None

# --------------------------------------------------------------------------
# Trần kích thước thân yêu cầu (bất biến A9).
#
# MỘT hằng duy nhất, không lập bảng theo từng đường. Thân lớn nhất mà giao
# diện từng gửi là {"tat":[...]} cho vài chục quy tắc — khoảng 200 byte; một
# quy tắc mới cỡ 1 KB. 256 KB đã rộng gấp hàng trăm lần, mà chỉ còn đúng một
# con số phải giải thích. Bảng nhiều mức chỉ mua được câu lỗi đẹp hơn, đổi lại
# một bảng phải bảo trì mỗi lần thêm đường.
TRAN_THAN = 256 * 1024

# Sau khi trả 413 thì đọc bỏ phần thân còn lại, NHƯNG CÓ CHẶN — xem _doc_bo().
TRAN_DOC_BO = 256 * 1024
GIAY_DOC_BO = 0.5

# Một kết nối im lặng giữa chừng sẽ giữ luồng bao lâu. Đo được:
# BaseHTTPRequestHandler.timeout mặc định là None, tức GIỮ MÃI MÃI.
GIAY_CHO_KET_NOI = 30


class ThanQuaLon(Exception):
    """Thân yêu cầu vượt trần -> 413.

       Phải là ngoại lệ RIÊNG, không mượn SystemExit: SystemExit đã bị ánh xạ
       cứng thành 400 ở cả do_GET lẫn do_POST, mượn nó là mất mã 413.
    """


def dau_ban_cau_hinh(duong_dan=None):
    """Dấu bản của cauhinh.json = BĂM NỘI DUNG TỆP (2C / QĐ 7).

       VÌ SAO BĂM NỘI DUNG chứ không phải một mã ngẫu nhiên sinh mỗi lần ghi:
       thầy cô được quyền mở cauhinh.json bằng Notepad và sửa tay — đó là
       đường dùng CHÍNH, ghi ngay ở đầu tài liệu. Một mã ngẫu nhiên giữ trong
       bộ nhớ sẽ KHÔNG hề biết lần sửa tay đó, nên hai người vẫn đè mất bài của
       nhau y như cũ, mà lần này còn kèm một cái dấu bản trông có vẻ an toàn.
       Băm nội dung thì bắt được mọi kiểu đổi: qua giao diện, sửa tay, khôi
       phục từ bản sao lưu, hay máy chủ vừa khởi động lại.

       Tệp không đọc được -> chuỗi rỗng. Không ném: đây là thứ đi kèm mọi câu
       trả lời, hỏng nó không được phép làm hỏng cả trang.
    """
    try:
        with open(duong_dan or DUONG_DAN_CAUHINH, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except OSError:
        return ''


class XungDotBanSua(Exception):
    """Dấu bản lệch — 409, KHÔNG phải 400. Hai mã nói hai chuyện khác nhau:
       400 = "bạn gửi sai", 409 = "bạn gửi đúng nhưng thế giới vừa đổi".
       Giao diện chỉ hiện nút "Tải lại danh sách" cho đúng mã 409."""


def thu_muc_cauhinh():
    """File mẫu và file kết quả nằm cạnh cauhinh.json — y như xep_tkb.main()."""
    return os.path.dirname(os.path.abspath(DUONG_DAN_CAUHINH))


def kiem_ghi_duoc(thu_muc):
    """Thư mục dự án có GHI được không? Trả (ok, câu lỗi hoặc None).

       VÌ SAO PHẢI KIỂM LÚC KHỞI ĐỘNG, không đợi tới lúc bấm Lưu:
       máy này có Windows cài song song (đã đo: efibootmgr thấy "Windows Boot
       Manager"), mà thư mục dự án nằm trên một phân vùng NTFS. Windows tắt
       kiểu "khởi động nhanh" là ngủ đông chứ không tắt hẳn, nên phân vùng còn
       ở trạng thái BẨN; Linux thấy vậy sẽ gắn CHỈ ĐỌC để khỏi làm hỏng dữ
       liệu. Hậu quả: phần mềm chạy bình thường, xếp bình thường, tới lúc bấm
       Lưu thì hỏng — và nguyên nhân thật (một cái tắt máy sai cách từ hôm
       trước, trên hệ điều hành khác) không hiện ra ở đâu trong phần mềm cả.

       Kiểm bằng cách GHI THẬT rồi xoá. Không dùng os.access(W_OK): nó chỉ hỏi
       bit quyền, mà tình huống đang lo là hệ tệp gắn CHỈ ĐỌC — bit quyền vẫn
       nói "được ghi" trong khi mọi lần ghi đều nổ.
    """
    dd = os.path.join(thu_muc, f'.thu-ghi-{os.getpid()}.tam')
    try:
        with open(dd, 'w', encoding='utf-8') as f:
            f.write('thu ghi')
        os.remove(dd)
        return True, None
    except OSError as e:
        try:
            os.remove(dd)
        except OSError:
            pass
        return False, (
            f'[LỖI] KHÔNG GHI ĐƯỢC vào thư mục dự án:\n'
            f'      {thu_muc}\n'
            f'      Lý do hệ điều hành đưa ra: {e}\n'
            f'\n'
            f'      Máy chủ DỪNG ở đây thay vì chạy tiếp, vì chạy tiếp nghĩa là\n'
            f'      thầy cô xếp xong 50 giây rồi mới phát hiện không Lưu được.\n'
            f'\n'
            f'      Nếu thư mục nằm trên ổ NTFS và máy có Windows cài song song:\n'
            f'      hầu như chắc chắn là Windows tắt kiểu "khởi động nhanh"\n'
            f'      (fast startup) nên ổ còn ở trạng thái bẩn, và Linux gắn ổ\n'
            f'      CHỈ ĐỌC. Cách chữa: vào Windows, tắt "khởi động nhanh"\n'
            f'      (Control Panel > Power Options > Choose what the power\n'
            f'      buttons do > bỏ tick "Turn on fast startup"), rồi Shut down\n'
            f'      hẳn — đừng Restart, đừng đóng nắp máy.')


# ==========================================================================
# 1. TRẠNG THÁI DÙNG CHUNG GIỮA CÁC LUỒNG
# ==========================================================================

KHOA = threading.Lock()
# Khoá RIÊNG cho việc ghi cauhinh.json. Tách khỏi KHOA (vốn chỉ giữ TT trong
# tích tắc) vì việc ghi tệp lâu hơn nhiều — dùng chung một khoá sẽ làm thanh
# tiến độ đứng hình mỗi lần có người bấm Lưu.
KHOA_GHI = threading.Lock()
# Khoá cho /api/thu-quy-tac, đường DUY NHẤT cố ý giải ngay trong luồng HTTP.
# Tách riêng vì nó không được đụng vào TT (làm vậy là xoá mất kết quả đang hiện
# trên màn hình người khác), mà vẫn phải là một-lúc-một-người.
KHOA_THU = threading.Semaphore(1)
TT = {}

# Quy tắc người dùng thêm ở màn hình Quy tắc — CHỈ nằm trong bộ nhớ của phiên
# này. Ghi xuống cauhinh.json vẫn chỉ qua nút "Lưu vào cauhinh.json".
# ==========================================================================
#  PHIÊN TRÌNH DUYỆT (2A-2a) — CHƯA CÓ XÁC THỰC
# ==========================================================================
#  Ở bước này phiên chỉ trả lời đúng một câu: "bản nháp quy tắc này là của
#  TRÌNH DUYỆT nào". Chưa có mật khẩu, chưa có tên người. Đăng nhập (2A-1) lắp
#  lên đúng hạ tầng này, không phải dựng lại.
#
#  VÌ SAO PHẢI LÀM TRƯỚC, và vì sao nó không phải việc "để dành cho sau":
#  bản nháp đang là MỘT danh sách toàn cục, nên đã đo được — thầy A thêm một
#  quy tắc nháp, cô B bấm Lưu, và quy tắc CHƯA AI DUYỆT của A đi thẳng vào
#  cauhinh.json (13 -> 14 quy tắc), còn A thì vẫn thấy nháp của mình là "chưa
#  lưu". Im lặng cả hai chiều. Không cần tới hai người: mở phần mềm trên máy
#  bàn và trên điện thoại đã là hai trình duyệt khác nhau.
#
#  Dấu bản của cauhinh.json KHÔNG bắt được lỗi này — lúc B tải danh sách về thì
#  tệp trên đĩa chưa hề đổi, dấu bản khớp hoàn hảo. Đây là lỗ ở BỘ NHỚ, không
#  phải ở TỆP, nên phải chữa bằng cách tách theo phiên.

CAC_PHIEN = {}                       # ma -> {'tao_m','tao_w','cham_m','cham_w'}
PHIEN_THEM = {}                      # ma -> [quy tắc nháp của riêng phiên đó]
KHOA_PHIEN = threading.Lock()

# Danh sách MỞ. Mặc định là CẤM: chỉ những đường ghi ở đây mới đi lọt khi chưa
# đăng nhập, mọi thứ còn lại — kể cả đường không tồn tại — đều 401.
#
# So BẰNG NHAU, không dùng startswith('/web/'): tiền tố mở ra một lớp đường
# không đếm được, còn phép so bằng thì kiểm được chính xác cả hai chiều.
#
# Bốn tệp tĩnh mở là quyết định CÓ ĐO: web/index.html, app.js, style.css đã nằm
# trong kho GitHub Public bjnnghe0/pm-xep-TKB. Gác chúng không giấu thêm byte nào,
# mà lại không còn chỗ nào hiện ô mật khẩu.
DUONG_MO = frozenset({'/', '/index.html',
                      '/api/dang-nhap', '/api/dang-xuat', '/api/toi-la-ai'}
                     | {'/web/' + t for t in TINH})

DUONG_DAN_TAI_KHOAN = os.path.join(THU_MUC, 'tai_khoan.json')
TAI_KHOAN = {}                       # ten -> bản ghi. RỖNG = máy chủ chưa cài xong
BAM_GIA = None                       # bản ghi giả cho nhánh "tên không tồn tại"
# Sổ khoá tạm (2B). SUY RA từ đường dẫn tai_khoan.json trong nap_tai_khoan_may_chu()
# chứ không khai riêng — xem TK.duong_dan_khoa().
DUONG_DAN_SO_KHOA = TK.duong_dan_khoa(DUONG_DAN_TAI_KHOAN)

# QĐ 3 — "tắt tài khoản có hiệu lực NGAY". Trước đây nap_tai_khoan_may_chu()
# CHỈ được gọi một lần trong main(), nên ngoài đời QĐ 3 SAI: chạy
# "python3 tao_mat_khau.py tat <tên>" không có tác dụng gì cho tới khi khởi
# động lại web.py. Ca thử ru ngủ điều đó vì nó gọi TAY hàm nạp ngay trước khi
# khẳng định — nó chứng minh HỆ QUẢ (phiên chết) mà bỏ qua CÁI CÒ.
#
# Chữa theo đúng cách sổ khoá tạm của 2B đã làm: ĐỌC LẠI THEO TỆP. Đo được
# trên chính ổ ntfs3 của dự án: os.replace() đổi st_ino mỗi lần, 5 lần ghi
# liên tiếp cho 5 mốc mtime phân biệt, và os.stat tốn 0,78 µs — rẻ hơn bốn bậc
# so với một lượt scrypt, nên soi ở mỗi yêu cầu là chuyện không phải cân nhắc.
DUONG_DAN_TK_DANG_DUNG = DUONG_DAN_TAI_KHOAN
DAU_TEP_TAI_KHOAN = None             # (ino, mtime_ns, size) của lần nạp gần nhất
DAU_DA_KEU = None                    # dấu tệp đã kêu rồi — đừng kêu lại mỗi yêu cầu
KHOA_NAP_TK = threading.Lock()

# scrypt cấp phát 16 MB và NHẢ GIL, nên nhiều lời gọi chạy song song THẬT —
# đã đo 32 lần cùng lúc đẩy tiến trình lên 537 MB. /api/dang-nhap là đường
# CHƯA XÁC THỰC duy nhất tốn kém như vậy, nên phải chặn số lần chạy cùng lúc,
# nếu không chính cổng đăng nhập thành chỗ hạ máy chủ.
KHOA_BAM = threading.Semaphore(2)

TEN_COOKIE = 'phien_tkb'             # đường http tại chỗ
TEN_COOKIE_BM = '__Host-phien_tkb'   # đường có TLS (qua proxy)
TRAN_PHIEN = 32
GIAY_NGHI_PHIEN = 8 * 3600           # QĐ 1
GIAY_TOI_DA_PHIEN = 12 * 3600        # QĐ 1 — không gia hạn được


def _trang_thai_moi():
    return {
        'dang_chay': False, 'xong': False, 'loi': None,
        'log': [], 'da_thu': 0, 'so_lan': 0, 'hop_le': 0,
        'con_giay': 0, 'bat_dau': 0,
        'bang': [], 'diem_mem': {}, 'diem': None, 'so_loi': 0,
        'luoi': None, 'gv': None, 'file_xuat': None, 'file_web': None,
        # QĐ 4 — DÁN TÊN để BIẾT, DẤU BẢN để CHẶN. Cần cả hai:
        #   nguoi = ai vừa xếp (hiện trên màn hình, không chặn ai)
        #   dau   = dấu của lượt xếp hiện có trên đĩa. None = máy chủ chưa xếp
        #           lần nào kể từ khi bật, nhưng tệp hôm qua vẫn có thể còn.
        'nguoi': None, 'dau': None,
    }


def dat_lai_trang_thai():
    with KHOA:
        TT.clear()
        TT.update(_trang_thai_moi())


def gianh_luot():
    """Giành quyền chạy MỘT lượt xếp. True = giành được, False = đang bận.

       Điểm mấu chốt: KIỂM cờ, XOÁ trạng thái cũ và ĐẶT cờ đều nằm trong CÙNG
       một lần giữ khoá. Trước đây ba việc đó tách rời:

           with KHOA:                  <- chỉ ĐỌC cờ, rồi nhả khoá ngay
               dang = TT['dang_chay']
           ...12 dòng đọc thân yêu cầu...
           dat_lai_trang_thai()        <- lại đặt cờ về False
           dat(dang_chay=True)         <- mãi tới đây mới ĐẶT

       nên hai yêu cầu tới gần nhau (bấm đúp, hai tab, hai người) đều thấy
       False và cùng khởi động một luồng giải. Đã đo: 8 người bấm cùng lúc,
       4 trên 6 vòng có 2 lượt cùng chạy — hai luồng cùng ghi TKB_Khoi12.xlsx
       và cùng trộn vào một khung nhật ký, người này thấy kết quả người kia.
    """
    with KHOA:
        if TT.get('dang_chay'):
            return False
        TT.clear()
        TT.update(_trang_thai_moi())
        TT['dang_chay'] = True
        return True


dat_lai_trang_thai()


def ghi(dong=''):
    """Ghi một dòng vào khung log — đúng những gì chương trình in ra."""
    with KHOA:
        TT['log'].append(dong)


def dat(**kw):
    with KHOA:
        TT.update(kw)


def _bao_su_co(noi=''):
    """In dấu vết lỗi ra CỬA SỔ DÒNG LỆNH của máy chủ, trả về mã ngắn.

       Trước đây mọi lỗi không lường trước đều trả nguyên traceback về trình
       duyệt. Đo được: GET /api/trang-thai?tu=abc cho 500 kèm đường dẫn tuyệt
       đối "/media/adminnam/NAM MEO/projects/PM xep tkb/web.py", số dòng, và
       cả tên đăng nhập máy. Không cần đăng nhập, không cần thủ đoạn gì.

       Nay người dùng chỉ thấy một mã 6 ký tự; chi tiết nằm ở cửa sổ dòng lệnh
       — nơi chỉ người đang chạy máy chủ mới đọc được. Có mã thì vẫn ghép được
       hai bên với nhau khi cần gỡ lỗi.
    """
    ma = secrets.token_hex(3)
    print(f'\n[SỰ CỐ {ma}] {noi}'.rstrip(), file=sys.stderr)
    traceback.print_exc(file=sys.stderr)
    sys.stderr.flush()
    return ma


def _loi_su_co(ma):
    return (f'[LỖI] Máy chủ gặp sự cố bất ngờ (mã sự cố {ma}).\n'
            f'      Chi tiết đã ghi ra cửa sổ dòng lệnh đang chạy web.py.')


# ==========================================================================
# 1a. DANH SÁCH TÊN MÁY / NGUỒN GỐC ĐƯỢC PHÉP
# ==========================================================================

def _het_han(p, bay_gio_m, bay_gio_w):
    """Phiên đã hết hiệu lực chưa? Hết khi MỘT TRONG HAI đồng hồ vượt.

       Vì sao phải hai đồng hồ, không phải một:
         monotonic  KHÔNG đếm lúc máy ngủ. Gập laptop qua đêm rồi mở ra thì
                    phiên "12 giờ" vẫn còn sống sang hôm sau.
         time()     nhảy khi NTP chỉnh giờ hoặc người dùng đổi múi giờ.
       Ghi cả hai mốc, hết hạn theo cái nào tới trước — fail-closed với cả hai
       kiểu hỏng, giá phải trả là hai số thực mỗi phiên.
    """
    return (bay_gio_m - p['cham_m'] > GIAY_NGHI_PHIEN
            or bay_gio_w - p['cham_w'] > GIAY_NGHI_PHIEN
            or bay_gio_m - p['tao_m'] > GIAY_TOI_DA_PHIEN
            or bay_gio_w - p['tao_w'] > GIAY_TOI_DA_PHIEN)


def _don_phien_da_khoa(bay_gio_m, bay_gio_w):
    """Dọn phiên hết hạn. NGƯỜI GỌI PHẢI ĐANG GIỮ KHOA_PHIEN.

       Tách hàm này ra khỏi bản có tự khoá là chuyện sống còn: threading.Lock
       KHÔNG tái nhập, nên một hàm đã giữ khoá mà gọi sang hàm tự khoá là TREO
       CỨNG máy chủ ngay phiên hết hạn đầu tiên — giáo viên chỉ còn đường Ctrl+C
       mà không hiểu vì sao. Đừng chữa bằng RLock: RLock giấu mất chỗ nào đang
       giữ khoá bao lâu.
    """
    chet = [m for m, p in CAC_PHIEN.items() if _het_han(p, bay_gio_m, bay_gio_w)]
    for m in chet:
        CAC_PHIEN.pop(m, None)
        PHIEN_THEM.pop(m, None)
    return len(chet)


def tao_phien(ten=None):
    """Cấp một phiên MỚI. Trả (ma, ban_ghi). ten=None nghĩa là CHƯA đăng nhập.

       Mã do secrets.token_urlsafe(32) sinh ra ở ĐÂY — không bao giờ nhận nuôi
       mã do khách gửi lên. Đó chính là cách chống cố định phiên, và nó phải
       đúng ngay từ bước chưa có mật khẩu: 2A-1 sẽ cấp lại mã mới một lần nữa
       sau khi mật khẩu đúng.
    """
    m, w = time.monotonic(), time.time()
    with KHOA_PHIEN:
        _don_phien_da_khoa(m, w)
        if len(CAC_PHIEN) >= TRAN_PHIEN:
            # Đầy thì đuổi cái ngồi không lâu nhất. KHÔNG từ chối người mới —
            # từ chối là biến một cái trần kỹ thuật thành cánh cửa đóng sập vào
            # mặt người dùng hợp lệ.
            cu = min(CAC_PHIEN, key=lambda x: CAC_PHIEN[x]['cham_m'])
            CAC_PHIEN.pop(cu, None)
            PHIEN_THEM.pop(cu, None)
        ma = secrets.token_urlsafe(32)
        CAC_PHIEN[ma] = {'tao_m': m, 'tao_w': w, 'cham_m': m, 'cham_w': w,
                         'ten': ten}
        PHIEN_THEM[ma] = []
        return ma, CAC_PHIEN[ma]


def doc_phien(ma):
    """Tra phiên còn hiệu lực. Hết hạn thì XOÁ rồi trả None.

       NƠI DUY NHẤT quyết định "phiên này còn dùng được không" — nên cũng là
       nơi duy nhất phải soi lại sổ tài khoản. Đặt tuoi_tai_khoan() ở đây chứ
       không rải ra do_GET/do_POST: phép kiểm QĐ 3 ("tài khoản còn trong sổ
       không") nằm ngay bên dưới, hai thứ đó phải đi liền một mạch, nếu tách ra
       là đẻ ra một khe hở tính bằng số yêu cầu.

       Gọi TRƯỚC khi lấy KHOA_PHIEN, và tuoi_tai_khoan() có khoá riêng
       (KHOA_NAP_TK) — hai khoá KHÔNG BAO GIỜ lồng nhau. threading.Lock không
       tái nhập, và dự án đã trả giá một lần cho bài học đó.
    """
    tuoi_tai_khoan()
    if not ma:
        return None
    m, w = time.monotonic(), time.time()
    with KHOA_PHIEN:
        _don_phien_da_khoa(m, w)
        p = CAC_PHIEN.get(ma)
        if p is None:
            return None
        # QĐ 3: tắt một tài khoản có hiệu lực NGAY, không phải khởi động lại.
        # Kiểm ở đây vì đây là nơi duy nhất quyết định "phiên còn dùng được
        # không" — đặt chỗ khác là đẻ ra bản cài thứ hai của cùng một luật.
        if p.get('ten') is not None and p['ten'] not in TAI_KHOAN:
            CAC_PHIEN.pop(ma, None)
            PHIEN_THEM.pop(ma, None)
            return None
        p['cham_m'], p['cham_w'] = m, w      # mọi yêu cầu qua cổng đều làm tươi
        return p


def xoa_phien(ma):
    with KHOA_PHIEN:
        co = CAC_PHIEN.pop(ma, None) is not None
        PHIEN_THEM.pop(ma, None)
        return co


def xoa_sach_phien():
    """Đường công khai cho ca thử dựng lại trạng thái sạch."""
    with KHOA_PHIEN:
        CAC_PHIEN.clear()
        PHIEN_THEM.clear()


def ten_cua_phien(ma):
    """Tên người đang giữ mã phiên này, hoặc None. Chỉ để DÁN TÊN (QĐ 4).

       Đọc thẳng CAC_PHIEN chứ không gọi doc_phien(): _chay() chạy ở luồng
       nền, có thể kéo dài 60 giây, và doc_phien() sẽ LÀM TƯƠI mốc "chạm" của
       phiên. Một lượt xếp không được phép giữ cho phiên sống mãi — hạn nghỉ
       8 giờ phải tính theo thao tác của NGƯỜI, không theo việc máy đang bận.
    """
    with KHOA_PHIEN:
        p = CAC_PHIEN.get(ma)
        return (p or {}).get('ten')


def nhap_cua(ma):
    """Danh sách quy tắc nháp của riêng phiên này (không bao giờ trả None)."""
    with KHOA_PHIEN:
        return PHIEN_THEM.setdefault(ma, [])


def nap_tai_khoan_may_chu(duong_dan=None):
    """Nạp tai_khoan.json vào TAI_KHOAN. Trả (ok, ghi_chu).

       TK.nap() NÉM SystemExit ở cả bốn nhánh hỏng; hàm này BẮT lấy, đặt sổ về
       RỖNG, và trả câu để người gọi in ra. Chỉ main() được sys.exit(1) —
       ca thử dựng máy chủ thẳng thì không được phép giết cả tiến trình.

       Sổ rỗng KHÔNG có nghĩa là "cho qua": _chan_neu_chua_dang_nhap() trả 503
       cho mọi đường. Trạng thái "chưa cài xong" phải là ĐÓNG.
    """
    global TAI_KHOAN, BAM_GIA, DUONG_DAN_SO_KHOA
    global DUONG_DAN_TK_DANG_DUNG, DAU_TEP_TAI_KHOAN, DAU_DA_KEU
    dd = duong_dan or DUONG_DAN_TAI_KHOAN
    DUONG_DAN_SO_KHOA = TK.duong_dan_khoa(dd)
    DUONG_DAN_TK_DANG_DUNG = dd
    DAU_TEP_TAI_KHOAN = _dau_tep(dd)
    DAU_DA_KEU = None
    if BAM_GIA is None:
        BAM_GIA = TK.ban_ghi_gia()
    try:
        TAI_KHOAN = TK.nap(dd)
        return True, None
    except SystemExit as e:
        TAI_KHOAN = {}
        return False, str(e)


def _dau_tep(dd):
    """Dấu nhận biết "tệp đã đổi chưa". None nếu không stat được.

       Ba thành phần chứ không chỉ mtime: TK.ghi() ghi ra tệp tạm rồi
       os.replace(), nên st_ino đổi MỖI lần ghi — dấu hiệu chắc chắn nhất, không
       phụ thuộc độ mịn đồng hồ của hệ tệp.
    """
    try:
        st = os.stat(dd)
        return (st.st_ino, st.st_mtime_ns, st.st_size)
    except OSError:
        return None


def tuoi_tai_khoan():
    """Nạp lại tai_khoan.json NẾU tệp đã đổi. Trả True nếu vừa nạp lại.

       GIỮ SỔ CŨ KHI ĐỌC KHÔNG ĐƯỢC — khác hẳn lúc khởi động, và có lý do:
       lúc khởi động chưa có sổ nào để giữ, nên từ chối chạy là đúng. Đang chạy
       mà tệp hỏng thì đó là một SỰ CỐ MỚI (đĩa lỗi, ai đó sửa tay), không phải
       một quyết định về quyền. Đổ sổ về rỗng lúc đó là tự tay cho cả khoa nghỉ
       việc giữa buổi vì một byte lỗi; giữ sổ cũ thì KHÔNG AI được thêm quyền
       nào — người vừa hợp lệ một giây trước vẫn hợp lệ.

       Hệ quả phải biết: sổ hỏng thì lệnh "tat" chưa có hiệu lực. Đúng — tệp
       hỏng không phải là một lệnh tắt. Và tao_mat_khau.py không cho tắt/xoá
       tài khoản BẬT cuối cùng, nên trạng thái "tắt hết" chỉ tới được bằng cách
       sửa tay.

       KHÔNG cập nhật dấu tệp khi hỏng -> yêu cầu sau vẫn thử lại. Nhưng chỉ
       KÊU MỘT LẦN cho mỗi dấu, nếu không thì một tệp hỏng làm ngập cửa sổ dòng
       lệnh với 1,4 dòng mỗi giây (trang hỏi trạng thái mỗi 0,7 giây).
    """
    global TAI_KHOAN, DAU_TEP_TAI_KHOAN, DAU_DA_KEU
    dau = _dau_tep(DUONG_DAN_TK_DANG_DUNG)
    if dau == DAU_TEP_TAI_KHOAN:
        return False
    with KHOA_NAP_TK:
        # Soi lại TRONG khoá: hai yêu cầu cùng thấy tệp đổi thì chỉ một cái nạp.
        dau = _dau_tep(DUONG_DAN_TK_DANG_DUNG)
        if dau == DAU_TEP_TAI_KHOAN:
            return False
        try:
            moi = TK.nap(DUONG_DAN_TK_DANG_DUNG)
        except SystemExit as e:
            if dau != DAU_DA_KEU:
                DAU_DA_KEU = dau
                print(f'[CẢNH BÁO] tai_khoan.json vừa đổi nhưng đọc KHÔNG '
                      f'được:\n{e}\n'
                      f'           Giữ nguyên danh sách tài khoản đang có. '
                      f'Sửa xong tệp là máy chủ tự nhận, không phải chạy lại.',
                      file=sys.stderr)
            return False
        cu_ds, TAI_KHOAN = set(TAI_KHOAN), moi
        DAU_TEP_TAI_KHOAN, DAU_DA_KEU = dau, None
        if cu_ds != set(moi):
            print(f'[TÀI KHOẢN] Đã đọc lại tai_khoan.json — đang bật: '
                  f'{", ".join(sorted(moi)) or "(không ai)"}', file=sys.stderr)
        return True


def dang_nhap(ma_cu, ten_tho, mat_khau):
    """Đối chiếu mật khẩu. Trả (ma_moi, ten, giay_khoa).

       Ba nhánh, phân biệt bằng ĐÚNG hai giá trị đầu:
         (ma, ten, 0)      đúng mật khẩu — ma là mã phiên MỚI
         (None, None, 0)   sai, và không bị khoá   -> một câu chung
         (None, ten, > 0)  ĐANG BỊ KHOÁ TẠM (2B)   -> câu nói rõ còn mấy phút
       Nhánh ba trả `ten` vì câu trả lời cần nhắc đúng tên để gõ lệnh mo-khoa;
       trả tên ở đây KHÔNG lộ thêm gì, vì chỉ tài khoản CÓ THẬT mới vào sổ khoá.

       XOAY MÃ PHIÊN — chống cố định phiên. Mã cũ bị HUỶ HẲN, mã mới do
       tao_phien() sinh ra. Không bao giờ nâng cấp tại chỗ một phiên vô danh:
       nếu kẻ tấn công gieo được mã vào trình duyệt nạn nhân rồi đợi họ đăng
       nhập, nâng cấp tại chỗ là trao luôn phiên đã xác thực cho hắn. Ở đây kẻ
       tấn công là người trong tailnet — đúng mô hình đe doạ đang chống.

       Nháp thì CHUYỂN sang mã mới, không bỏ: thứ kẻ tấn công cần là mã sau khi
       đăng nhập, mà mã đã xoay thì hắn không có. Nháp chuyển hay không KHÔNG
       đụng tới tính chất đó. Và phiên vô danh vốn không thể có nháp (mọi đường
       tạo nháp đều đòi xác thực), nên lần đăng nhập đầu chuyển một danh sách
       rỗng. Trường hợp có nháp là người đã đăng nhập lại POST đăng nhập lần
       nữa — bỏ nháp lúc đó là làm mất việc của họ mà chẳng đổi lấy gì.

       MỘT lần scrypt ở MỌI nhánh, kể cả tên không tồn tại và tên sai cú pháp.
       Thoát sớm ở bất kỳ nhánh nào là mở một kênh đo thời gian để dò xem tài
       khoản nào có thật. NHÁNH BỊ KHOÁ CŨNG VẬY — nó nằm SAU lời gọi TK.bam(),
       không phải trước. Chặn trước cho "đỡ tốn CPU" là đổi 27 ms lấy một kênh
       đo: gõ bậy 5 lần rồi xem lần thứ 6 trả lời nhanh hay chậm là biết tài
       khoản có thật hay không. Hệ quả phải chấp nhận: khoá tạm KHÔNG giảm được
       chút tải CPU nào — nó chống DÒ MẬT KHẨU, không chống làm nghẽn máy chủ.

       ĐANG KHOÁ THÌ ĐÚNG MẬT KHẨU CŨNG KHÔNG VÀO. Cho vào là bỏ hẳn tác dụng
       của khoá: kẻ dò cứ đoán tiếp trong lúc bị khoá, tới lúc trúng thì vào.
    """
    ten = TK.chuan_ten(ten_tho)
    bg = TAI_KHOAN.get(ten) if ten else None
    that = bg is not None
    if bg is None:
        bg = BAM_GIA
    # Ghi nhận lần thử TRƯỚC khi băm, và kiểm+tăng trong cùng một lần giữ khoá.
    # Xem docstring của TK.ghi_nhan_thu(): tách ra sau khi băm thì một loạt bắn
    # dồn sẽ lọt hết, vì mọi yêu cầu đều đọc bộ đếm xong mới xếp hàng ở KHOA_BAM.
    khoa, khoa_that = (TK.ghi_nhan_thu(DUONG_DAN_SO_KHOA, ten) if that
                       else (0, False))
    with KHOA_BAM:
        d = TK.bam(mat_khau if isinstance(mat_khau, str) else '', bg['muoi'])
    dung = TK.so_khop(d, bg['bam']) and that
    if khoa > 0 and khoa_that:
        return None, ten, khoa           # khoá THẬT: chặn cả mật khẩu đúng
    if not dung:
        if that:
            TK.ghi_nhan_sai(DUONG_DAN_SO_KHOA, ten)
        if khoa > 0:
            # CHỐT CHẶN loạt bắn dồn — chỉ áp cho mật khẩu SAI. Mật khẩu ĐÚNG
            # đi thẳng xuống dưới: chặn nó không mua được gì về an ninh (kẻ
            # đoán trúng thì đã thắng), mà lại khoá oan 11 người đăng nhập
            # đúng cùng lúc. Đã đo bằng 12 khách song song.
            return None, ten, khoa
        return None, None, 0
    TK.xoa_khoa(DUONG_DAN_SO_KHOA, ten)     # vào được là bộ đếm về 0

    nhap_cu = list(nhap_cua(ma_cu)) if ma_cu else []
    if ma_cu:
        xoa_phien(ma_cu)                 # HUỶ HẲN mã cũ
    ma_moi, _ = tao_phien(ten)           # mã HOÀN TOÀN MỚI
    if nhap_cu:
        nhap_cua(ma_moi).extend(nhap_cu)
    return ma_moi, ten, 0


def _chuan_ten_may(gt):
    """Chuẩn hoá một giá trị Host/Origin TRƯỚC khi so khớp.

       CHỈ hạ chữ thường, vì tên miền vốn không phân biệt hoa thường (DNS).

       Cố ý KHÔNG cắt khoảng trắng. Đã đo: bộ phân tích tiêu đề của thư viện
       chuẩn tự bỏ khoảng trắng ĐẦU nhưng GIỮ NGUYÊN khoảng trắng cuối —
       'Host: 127.0.0.1:20266   ' cho ra '127.0.0.1:20266   '. Thêm .strip()
       vào đây là tự nới phép so khớp "cho dễ khớp", đúng loại nới lỏng mà cả
       bảng ca thử Host được viết ra để canh. Trình duyệt không bao giờ gửi
       khoảng trắng thừa; ai gửi thì đáng bị từ chối.
    """
    return gt.lower()


def _kiem_ky_tu_dieu_khien(ten, gt):
    """Giá trị tiêu đề có ký tự điều khiển thì DỪNG, kèm câu nói rõ.

       Không phải để "chặn thêm" — phép so khớp chính xác vốn đã loại chúng
       rồi. Là để câu trả lời nói đúng chuyện gì đã xảy ra thay vì một câu
       "tên máy lạ" khó hiểu. Dạng lọt vào được là obs-fold (dòng nối tiếp bắt
       đầu bằng khoảng trắng): đã đo, 'Host: a\\r\\n evil.com' cho ra MỘT giá
       trị 'a\\r\\n evil.com'.
    """
    for c in gt:
        if ord(c) < 0x20 or ord(c) == 0x7F:
            raise SystemExit(
                f'[LỖI] Tiêu đề "{ten}" có ký tự điều khiển ({c!r}).\n'
                f'      Máy chủ không nhận tiêu đề gấp dòng.')


def _ds_ten_may(cfg, khoa, duong_dan):
    """Lấy một danh sách chuỗi từ cấu hình máy chủ. Sai kiểu thì DỪNG."""
    gt = cfg.get(khoa, [])
    if not isinstance(gt, list):
        raise SystemExit(
            f'[LỖI] Trong {os.path.basename(duong_dan)}, mục "{khoa}" phải là '
            f'một dãy [ ... ]')
    ra = set()
    for x in gt:
        if not isinstance(x, str) or not x.strip():
            raise SystemExit(
                f'[LỖI] Trong {os.path.basename(duong_dan)}, mục "{khoa}" có '
                f'giá trị không phải chuỗi: {x!r}')
        _kiem_ky_tu_dieu_khien(khoa, x)
        ra.add(_chuan_ten_may(x))
    return ra


def nap_cau_hinh_may_chu(duong_dan=None):
    """Nạp danh sách Host/Origin được phép từ cauhinh_may_chu.json.

       Trả về (host, origin, ghi_chu) — hai tập chuỗi (hoặc None), và một câu
       để in ra màn hình.

       BỐN đường vào, cả bốn đều FAIL-CLOSED (thiếu gì thì về mặc định chỉ cho
       chính máy này, KHÔNG BAO GIỜ mở rộng ra):

         không có tệp     -> mặc định loopback, im lặng (đây là cài đặt thường)
         tệp hỏng         -> mặc định loopback, KÊU TO ra cửa sổ dòng lệnh
         danh sách rỗng   -> mặc định loopback, kêu to
         hợp lệ           -> dùng đúng danh sách đó, và IN RA cho người dùng thấy

       Vì sao tệp hỏng phải kêu to thay vì im: thầy cô sửa tệp, gõ nhầm một dấu
       phẩy, rồi không vào được bằng địa chỉ Tailscale nữa mà không hiểu vì sao.
       Im lặng lùi về mặc định là đúng về an ninh nhưng độc về cách dùng — nên
       lùi thì lùi, mà phải nói.
    """
    global HOST_CHO_PHEP, ORIGIN_CHO_PHEP
    dd = duong_dan or DUONG_DAN_MAY_CHU
    HOST_CHO_PHEP = ORIGIN_CHO_PHEP = None

    if not os.path.exists(dd):
        return None, None, None

    try:
        with open(dd, encoding='utf-8-sig') as f:
            cfg = json.load(f)
        if not isinstance(cfg, dict):
            raise ValueError('nội dung phải là một khối { ... }')
        host = _ds_ten_may(cfg, 'host_cho_phep', dd)
        org = _ds_ten_may(cfg, 'origin_cho_phep', dd)
    except SystemExit as e:
        return None, None, (f'{e}\n'
                            f'      -> Tạm thời CHỈ cho 127.0.0.1 như khi chưa '
                            f'có tệp này.')
    except (OSError, ValueError) as e:
        return None, None, (
            f'[LỖI] Không đọc được {os.path.basename(dd)}: {e}\n'
            f'      -> Tạm thời CHỈ cho 127.0.0.1 như khi chưa có tệp này.')

    if not host and not org:
        return None, None, (
            f'[LỖI] {os.path.basename(dd)} có nhưng cả hai danh sách đều rỗng.\n'
            f'      -> Tạm thời CHỈ cho 127.0.0.1 như khi chưa có tệp này.')

    HOST_CHO_PHEP = frozenset(host) if host else None
    ORIGIN_CHO_PHEP = frozenset(org) if org else None
    ghi = [f'  Cấu hình mạng:       {dd}']
    ghi.append('    Tên máy cho phép : ' +
               (', '.join(sorted(host)) if host else '(mặc định — chỉ 127.0.0.1)'))
    ghi.append('    Nguồn gốc cho phép: ' +
               (', '.join(sorted(org)) if org else '(mặc định — chỉ 127.0.0.1)'))
    return HOST_CHO_PHEP, ORIGIN_CHO_PHEP, '\n'.join(ghi)


# ==========================================================================
# 1b. TIÊU ĐỀ HTTP — MỘT PHỄU DUY NHẤT (bất biến A10)
# ==========================================================================
#  Đây là _dat_o() của xep_tkb.py, đặt ở tầng HTTP. Cùng một lý lẽ: rất nhiều
#  chỗ ghi, chỉ một chỗ kiểm.
#
#  Vì sao phải có: send_header() của thư viện chuẩn nối thẳng chuỗi
#      ("%s: %s\r\n" % (keyword, value)).encode('latin-1', 'strict')
#  KHÔNG lọc \r \n gì cả. Đã đo trên máy chủ thật: đặt
#      thong_tin.file_xuat = 'TKB.xlsx"\r\nX-Chen-Vao: co-that\r\nSet-Cookie: a=b'
#  rồi GET /api/tai-ve thì phản hồi mọc ra ĐÚNG hai tiêu đề đó, kể cả Set-Cookie.
#
#  Và 'latin-1' STRICT còn gây một lỗi thứ hai, KHÔNG cần kẻ tấn công nào —
#  đây mới là lỗi hay gặp: cô giáo đổi file_xuat thành tên có dấu tiếng Việt
#      thong_tin.file_xuat = 'TKB_Khối12.xlsx'
#  thì send_header ném UnicodeEncodeError ở GIỮA CHỪNG, khi dòng trạng thái 200
#  đã nằm trong _headers_buffer. except Exception lại gọi _json(...500), tức
#  send_response(500) NỐI THÊM một dòng trạng thái nữa vào cùng bộ đệm. Đã đo:
#  máy chủ trả mã 200 với server/date/content-type mỗi thứ HAI LẦN, và trình
#  duyệt tải về một tệp .xlsx thật ra chứa câu báo lỗi JSON. Không một chữ
#  giải thích.
#
#  => Luật rút ra, và là lý do _tra_byte() nhận CẢ DANH SÁCH tiêu đề:
#     MỌI KIỂM TRA PHẢI XONG TRƯỚC LỜI GỌI send_response() ĐẦU TIÊN.
#     Bọc từng lời gọi send_header() là chưa đủ — lúc đó đã muộn rồi.

def _kiem_tieu_de(ten, gt):
    """Giá trị này có đặt vào tiêu đề HTTP được không? Không thì DỪNG."""
    gt = str(gt)
    for c in gt:
        if ord(c) < 0x20 or ord(c) == 0x7F:
            raise SystemExit(
                f'[LỖI] Giá trị của tiêu đề "{ten}" có ký tự điều khiển '
                f'({c!r}).\n'
                f'      Ký tự xuống dòng trong tiêu đề HTTP cho phép chèn thêm '
                f'tiêu đề giả,\n'
                f'      nên máy chủ từ chối hẳn chứ không lặng lẽ bỏ ký tự đi.\n'
                f'      Hãy mở cauhinh.json, sửa mục "thong_tin".')
    try:
        gt.encode('latin-1')
    except UnicodeEncodeError:
        # Chốt chặn cuối. Mọi đường đi đúng đều đã đổi chữ có dấu sang dạng
        # RFC 5987 trước khi tới đây, nên gặp lỗi này là mã sai — nhưng thà
        # dừng sạch bằng một câu tiếng Việt còn hơn để lọt vào send_header
        # rồi nhận về phản hồi hai-dòng-trạng-thái.
        raise SystemExit(
            f'[LỖI] Giá trị của tiêu đề "{ten}" có chữ không thuộc bảng mã '
            f'latin-1.\n'
            f'      Tiêu đề HTTP không mang được chữ có dấu ở dạng thô.')
    return gt


def _ten_tep_an_toan(ten, khoa='thong_tin.file_xuat'):
    """Dựng giá trị Content-Disposition an toàn cho một tên tệp.

       Trả về chuỗi đã ghép sẵn, mang HAI tham số như RFC 6266 khuyến nghị:

           attachment; filename="TKB_Kh_i12.xlsx";
                       filename*=UTF-8''TKB_Kh%E1%BB%91i12.xlsx

       - filename=  bản dự phòng, chỉ [A-Za-z0-9._-], cho máy cũ.
       - filename*= bản thật, giữ nguyên dấu tiếng Việt. Mọi trình duyệt hiện
         đại ưu tiên tham số này.

       Hai loại ký tự, hai cách xử KHÁC NHAU, có chủ ý:

       - Ký tự điều khiển và dấu nháy kép -> DỪNG HẲN. Không có cách viết đúng
         nào cho chúng ở đây, mà lọc âm thầm là sửa dữ liệu người dùng rồi vẫn
         phục vụ — giấu mất cái sai trong cauhinh.json (quy ước số 3).
       - Chữ có dấu tiếng Việt -> KHÔNG từ chối, mã hoá RFC 5987. Tên tệp có
         dấu là hợp lệ và nhà trường sẽ dùng; từ chối ở đây là bắt giáo viên bỏ
         dấu, tức bắt nhầm người.

       (Khác _dat_o() của Excel ở đúng chỗ này: ở Excel còn một "cách lưu" khác
       giữ nguyên được từng ký tự, ở HTTP thì không.)
    """
    ten = os.path.basename(str(ten))
    for c in ten:
        if ord(c) < 0x20 or ord(c) == 0x7F or c == '"':
            raise SystemExit(
                f'[LỖI] Tên tệp khai ở "{khoa}" có ký tự không dùng được: {c!r}\n'
                f'      Tên tệp không được chứa dấu nháy kép hay ký tự xuống '
                f'dòng — chúng cho phép\n'
                f'      chèn thêm tiêu đề giả vào phản hồi HTTP.\n'
                f'      Hãy mở cauhinh.json và sửa lại mục "{khoa}".')
    du_phong = ''.join(c if (c.isascii() and (c.isalnum() or c in '._-')) else '_'
                       for c in ten)
    du_phong = du_phong.strip('_') or 'tai-ve'
    ma_hoa = urllib.parse.quote(ten, safe='')
    return f"attachment; filename=\"{du_phong}\"; filename*=UTF-8''{ma_hoa}"


# ==========================================================================
# 1c. GHI TỆP BỀN (bất biến A11)
# ==========================================================================
#  os.replace() nguyên tử về CÁI TÊN, nhưng không nói gì về việc DỮ LIỆU đã
#  xuống đĩa hay chưa. Mất điện ngay sau đó thì cái tên đã trỏ sang tệp mới mà
#  nội dung còn nằm trong bộ nhớ đệm của hệ điều hành -> cauhinh.json thành 0
#  byte. Đúng thứ mà A7 đã bỏ công bảo vệ, chỉ ở tầng thấp hơn một bậc.
#
#  Đo được: cả mẫu ghi nguyên tử ĐẦY ĐỦ (ghi + fsync tệp + replace + fsync thư
#  mục) mất trung vị 1,1 ms cho tệp ~4 KB — nút Lưu không chậm đi.

def _dong_bo_tep(f):
    """Ép nội dung tệp đang mở xuống đĩa thật."""
    f.flush()
    os.fsync(f.fileno())


def _dong_bo_thu_muc(tm):
    """Ép CÁI TÊN vừa đổi xuống đĩa. Trả True nếu đã làm được.

       Trả về bool chứ không nuốt im lặng, để ca thử khẳng định được.

       Trên Windows os.open() không mở được thư mục nên bước này bỏ qua —
       nói thẳng ra đây chứ không giấu: phần đổi tên trên NTFS đi qua nhật ký
       siêu dữ liệu nên tương đối bền, còn RỦI RO CÒN LẠI thì vẫn còn. Bước
       fsync tệp tạm ở trên mới là bước quan trọng nhất, và bước đó chạy trên
       cả hai hệ điều hành.
    """
    if os.name != 'posix':
        return False
    try:
        fd = os.open(tm, os.O_RDONLY)
    except OSError:
        return False
    try:
        os.fsync(fd)
        return True
    except OSError:
        return False                 # vài hệ tệp không cho fsync thư mục
    finally:
        os.close(fd)


def _chep_ben(nguon, dich):
    """shutil.copy() nhưng ép xuống đĩa.

       Vì sao bản sao lưu cũng phải fsync: mất điện ngay sau khi bấm Lưu thì
       cauhinh.json mới đã bền, nhưng cauhinh.bak.json có thể rỗng — tức mất
       đúng cái phao cứu sinh, trong khi người dùng đinh ninh là có. Đó là kiểu
       hỏng tệ nhất của dự án này: im lặng và mất dữ liệu.
    """
    with open(nguon, 'rb') as f:
        dl = f.read()
    with open(dich, 'wb') as f:
        f.write(dl)
        _dong_bo_tep(f)


# ==========================================================================
# 2. LUỒNG XẾP THỜI KHÓA BIỂU
# ==========================================================================
#  Việc tìm phương án nằm ở X.tim_phuong_an() — CHUNG với xep_tkb.main(),
#  không chép lại dòng nào. Web chỉ truyền thêm hàm gọi lại để báo tiến
#  độ; dòng lệnh truyền None nên im lặng y như trước.
#  tests/thu_web.py vẫn so từng ô của file Excel giữa hai đường chạy.

def _chay(ma_phien, tuan, seed, so_lan, tat):
    try:
        dat(nguoi=ten_cua_phien(ma_phien))
        cfg, _ = cau_hinh_phien(ma_phien)
        if tuan:
            cfg['thong_tin']['tuan'] = tuan
        for i in tat:                       # tắt quy tắc cho riêng lượt này
            if 0 <= i < len(cfg.get('quy_tac', [])):
                cfg['quy_tac'][i]['bat'] = False

        bt = X.BaiToan(cfg)

        goc = cfg.get('tim_kiem', {})
        tk = X.gop_tim_kiem(goc, so_lan_thu=so_lan, seed=seed)

        cung = [q for q in bt.quy_tac if not q.TEN.startswith('uu_tien')]
        mem = [q for q in bt.quy_tac if q.TEN.startswith('uu_tien')]
        ghi('=' * 70)
        ghi(' XẾP THỜI KHÓA BIỂU'.center(70))
        ghi('=' * 70)
        ghi(f'Số lớp        : {len(bt.lop)}  ({", ".join(bt.lop)})')
        ghi(f'Khung giờ     : Thứ {bt.cac_thu} | buổi {bt.buoi} | '
            f'tiết {bt.cac_tiet[0]}–{bt.cac_tiet[-1]}')
        ghi(f'Tuần          : {cfg["thong_tin"]["tuan"]}')
        ghi(f'Cụm tiết      : {len([c for c in bt.cac_cum if not c.la_trong])} '
            f'(+{len([c for c in bt.cac_cum if c.la_trong])} ô trống)')
        ghi(f'Quy tắc nạp   : {len(cung)} quy tắc cứng, {len(mem)} tiêu chí mềm')
        if tat:
            ghi(f'Đã tắt tạm    : {len(tat)} quy tắc (chỉ cho lượt chạy này)')
        ghi(f'Đang tìm phương án ({tk["so_lan_thu"]} lần thử, '
            f'seed={tk["seed"]}) ...')
        dat(so_lan=tk['so_lan_thu'], bat_dau=time.time(),
            con_giay=tk['gioi_han_tong_giay'])

        def tien_do(da_thu, so_lan_thu, hop_le, con_giay):
            dat(da_thu=da_thu, so_lan=so_lan_thu, hop_le=hop_le,
                con_giay=con_giay)

        kqt = X.tim_phuong_an(bt, tk, tien_do)
        tot, diem_tot, dung_du_phong = kqt.tot, kqt.diem, False

        if tot is None and kqt.du_phong is None:
            ghi('')
            ghi('[KHÔNG XẾP ĐƯỢC] Các quy tắc đang mâu thuẫn nhau.')
            ghi('Gợi ý: tăng "so_lan_thu"/"gioi_han_tong_giay" trong mục "tim_kiem",')
            ghi('       hoặc tạm tắt bớt quy tắc ở màn hình "Quy tắc".')
            dat(loi='Các quy tắc đang mâu thuẫn nhau, không tìm được lời giải nào.')
            return

        if tot is None:
            tot, diem_tot, dung_du_phong = kqt.du_phong, kqt.diem_dp, True
            ghi('')
            ghi('[CẢNH BÁO] Không có phương án nào thoả HẾT quy tắc cứng.')
            ghi(f'           Đây là phương án ÍT VI PHẠM NHẤT: {kqt.loi_dp} '
                f'quy tắc lỗi, điểm mềm {kqt.diem_dp}.')

        ket = (f'Phương án ít vi phạm nhất: {kqt.loi_dp} quy tắc lỗi, '
               f'điểm mềm {diem_tot}.' if dung_du_phong
               else f'Điểm cao nhất: {diem_tot}.')
        ghi(f'-> {kqt.so_hop_le} phương án hợp lệ / {kqt.so_ok} lời giải / '
            f'{kqt.da_thu} lần thử trong {kqt.giay:.0f}s. {ket}')

        _, ct = X.cham_diem(bt, tot, chi_tiet=True)
        if ct:
            ghi('')
            ghi('ĐIỂM CÁC TIÊU CHÍ MỀM')
            ghi('-' * 70)
            for k, v in ct.items():
                ghi(f'  {v:>6}   {k}')

        bc, so_loi = X.hau_kiem(bt, tot)
        ghi('')
        ghi('ĐỐI CHIẾU QUY TẮC')
        ghi('-' * 70)
        for kq, ten, c in bc:
            ghi(f'  [{kq}] {ten}' + (f'  --> {c}' if c else ''))
        ghi('-' * 70)
        ghi(f'Tổng: {len(bc) - so_loi}/{len(bc)} quy tắc ĐẠT.')

        tt = cfg['thong_tin']
        tm = thu_muc_cauhinh()
        fx = X.xuat_excel(bt, tot,
                          os.path.join(tm, tt['file_mau']),
                          os.path.join(tm, tt['file_xuat']))
        import xuat_html as XH
        fh = XH.xuat_html(bt, tot, os.path.join(tm, 'tkb_web.html'))
        ghi('')
        ghi(f'Đã xuất file: {fx}')
        ghi(f'Đã xuất trang web: {fh}')

        dat(bang=[{'kq': a, 'ten': b, 'ghi_chu': c} for a, b, c in bc],
            diem_mem=dict(ct), diem=diem_tot, so_loi=so_loi,
            luoi=luoi_tkb(bt, tot, cfg), gv=lich_gv(bt),
            file_xuat=os.path.basename(fx), file_web=os.path.basename(fh),
            # Dấu mới CHỈ sinh khi đã ghi xong hai tệp kết quả. Sinh sớm hơn là
            # phát một dấu cho một tệp chưa tồn tại.
            dau=secrets.token_hex(8))

    except SystemExit as e:
        # Khai báo sai trong cauhinh.json -> chương trình gốc gọi sys.exit.
        # Trong web thì phải bắt lại, nếu không máy chủ chết theo.
        ghi('')
        for d in str(e).split('\n'):
            ghi(d)
        dat(loi=str(e))
    except Exception:
        # Khác hẳn nhánh SystemExit ở trên: đó là lỗi KHAI BÁO của người dùng,
        # phải hiện nguyên văn. Còn đây là lỗi của phần mềm — dấu vết chỉ có
        # ích cho người viết mã, mà lại lộ đường dẫn máy chủ, nên đẩy ra cửa
        # sổ dòng lệnh và chỉ đưa người dùng một mã đối chiếu.
        ma_sc = _bao_su_co('trong lúc xếp thời khoá biểu')
        ghi('')
        for d in _loi_su_co(ma_sc).split('\n'):
            ghi(d)
        dat(loi=_loi_su_co(ma_sc))
    finally:
        dat(dang_chay=False, xong=True)


def luoi_tkb(bt, pa, cfg):
    """Lưới TKB đúng bố cục sheet Excel: ngày x tiết x lớp."""
    X.nap(bt, pa)
    o = {}
    for c in bt.cac_cum:
        if c.la_trong:
            continue
        for p in range(c.vitri, c.vitri + c.size):
            o[(c.lop, c.ngay, p)] = {'mon': c.mon, 'gv': c.gv,
                                     'dau': p == c.vitri, 'size': c.size}
    hang = []
    for d in range(bt.SO_NGAY):
        for p in range(bt.SO_TIET):
            hang.append({
                'thu': bt.cac_thu[d], 'buoi': bt.buoi, 'tiet': bt.cac_tiet[p],
                'dau_ngay': p == 0,
                'o': [o.get((l, d, p)) for l in bt.lop]})
    return {'lop': bt.lop, 'hang': hang, 'tuan': cfg['thong_tin']['tuan'],
            'tieu_de': cfg['thong_tin']['tieu_de'],
            'gvcn': [bt.thong_tin_lop[l]['gvcn'] for l in bt.lop],
            'tong': [sum(1 for h in hang if h['o'][j]) for j in range(len(bt.lop))]}


def lich_gv(bt):
    """Bảng như sheet "TKB giáo viên"."""
    cot = [f'T{bt.cac_thu[d]}/t{bt.cac_tiet[p]}'
           for d in range(bt.SO_NGAY) for p in range(bt.SO_TIET)]
    ds = []
    for gv in sorted({c.gv for c in bt.cac_cum if not c.la_trong}):
        cum = [c for c in bt.cac_cum if c.gv == gv and not c.la_trong]
        luoi = {}
        for c in cum:
            for p in range(c.vitri, c.vitri + c.size):
                luoi[(c.ngay, p)] = {'lop': c.lop, 'mon': c.mon}
        ds.append({'gv': gv, 'so_tiet': sum(c.size for c in cum),
                   'so_buoi': len({c.ngay for c in cum}),
                   'o': [luoi.get((d, p))
                         for d in range(bt.SO_NGAY) for p in range(bt.SO_TIET)]})
    return {'cot': cot, 'gv': ds}


# ==========================================================================
# 3. ĐỌC / GHI QUY TẮC
# ==========================================================================

def cau_hinh_phien(ma_phien):
    """cauhinh.json + các quy tắc nháp CỦA RIÊNG phiên này. Không đụng file.

       Tham số ma_phien là BẮT BUỘC, không có giá trị mặc định — cố ý. Để mặc
       định thì chỗ nào quên truyền sẽ lặng lẽ đọc nháp của người khác, đúng lỗi
       vừa bịt; thiếu tham số thì vỡ ngay bằng TypeError lúc chạy.
    """
    cfg = X.doc_cau_hinh(DUONG_DAN_CAUHINH)
    tu_file = [r for r in cfg.get('quy_tac', []) if isinstance(r, dict)]
    cfg['quy_tac'] = tu_file + [copy.deepcopy(r) for r in nhap_cua(ma_phien)]
    return cfg, len(tu_file)


def doc_quy_tac(ma_phien):
    cfg, so_file = cau_hinh_phien(ma_phien)
    ds = []
    for i, r in enumerate(cfg['quy_tac']):
        ds.append({'i': i, 'loai': r.get('loai', '?'),
                   'ghi_chu': r.get('ghi_chu', ''),
                   'bat': bool(r.get('bat', True)),
                   'mem': str(r.get('loai', '')).startswith('uu_tien'),
                   'moi': i >= so_file,          # chưa lưu xuống file
                   'noi_dung': {k: v for k, v in r.items()
                                if k not in ('loai', 'ghi_chu', 'bat')}})
    return {'quy_tac': ds, 'so_file': so_file,
            'so_moi': len(nhap_cua(ma_phien)),
            'dau': dau_ban_cau_hinh(),
            'tuan': cfg['thong_tin']['tuan'],
            'tim_kiem': cfg.get('tim_kiem', {})}


def danh_muc_loai():
    """Danh mục loại quy tắc, sinh thẳng từ QT.DANH_MUC — không chép tay."""
    ra = []
    for ten_nhom, ds in QT.nhom_danh_muc():
        ra.append({'nhom': ten_nhom, 'loai': [
            {'ten': t, 'mo_ta': QT.DANH_MUC[t].MO_TA,
             'truong': [dict(x) for x in QT.DANH_MUC[t].TRUONG],
             'vi_du': QT.DANH_MUC[t].VI_DU,
             'mem': t.startswith('uu_tien')} for t in ds]})
    return {'nhom': ra, 'kieu': QT.KIEU, 'khoa_loc': list(QT.KHOA_LOC)}


def gia_tri_chon():
    """Các giá trị chọn được, đọc thẳng từ cauhinh.json."""
    cfg = X.doc_cau_hinh(DUONG_DAN_CAUHINH)
    pc = {k: v for k, v in cfg['phan_cong'].items() if not k.startswith('_')}
    dm = {k: v for k, v in cfg['dinh_muc_mon'].items() if k != '_doc'}
    kg = cfg['khung_gio']
    return {
        'lop': [l['ten'] for l in cfg['lop']],
        'gv': sorted({g for ds in pc.values() for _, g, _ in ds}),
        'mon': sorted({m for ds in pc.values() for m, _, _ in ds}),
        'nhom_mon': sorted({v['nhom'] for v in dm.values()}),
        'thu': list(kg['cac_thu']),
        'tiet': list(kg['cac_tiet']),
        'tiet_trong_buoi': list(range(1, len(kg['cac_tiet']) + 1)),
    }


def them_quy_tac(ma_phien, r):
    """Dựng thử BaiToan trước khi nhận. Khai sai thì SystemExit bay lên trên
       và người gọi hiện nguyên văn ra trang."""
    if not isinstance(r, dict):
        raise SystemExit('[LỖI] Quy tắc phải là một khối { ... }')
    if not str(r.get('ghi_chu', '')).strip():
        raise SystemExit('[LỖI] Chưa điền "Nội dung quy tắc"\n'
                         '      Câu này hiện nguyên văn trên bảng đối chiếu '
                         'và trên sheet "Kiểm tra quy tắc", nên không được '
                         'để trống.')
    cfg, _ = cau_hinh_phien(ma_phien)
    cfg['quy_tac'].append(copy.deepcopy(r))
    X.BaiToan(cfg)                     # ném SystemExit nếu khai sai
    nhap_cua(ma_phien).append(copy.deepcopy(r))
    return doc_quy_tac(ma_phien)


def xoa_quy_tac(ma_phien, i):
    _, so_file = cau_hinh_phien(ma_phien)
    if i < so_file:
        raise SystemExit(
            '[LỖI] Chỉ xoá được quy tắc vừa thêm trong phiên này.\n'
            '      Quy tắc đã có trong cauhinh.json thì dùng công tắc để tắt, '
            'rồi bấm "Lưu vào cauhinh.json".')
    j = i - so_file
    nhap = nhap_cua(ma_phien)
    if not 0 <= j < len(nhap):
        raise SystemExit('[LỖI] Không có quy tắc thứ %d để xoá.' % i)
    nhap.pop(j)
    return doc_quy_tac(ma_phien)


def doc_lai_quy_tac(r):
    """Câu ĐỌC LẠI + cảnh báo ghi chú, cho một quy tắc đang gõ dở.

       Đợt 3 việc 1. RẺ: chỉ ghép chuỗi, không dựng BaiToan, không giải, không
       đụng tệp nào — nên gọi được sau mỗi lần gõ.

       CÂU ĐỌC LẠI HIỆN LUÔN LUÔN, kể cả khi không có cảnh báo nào. Từ khoá chỉ
       quyết định có tô cảnh báo hay không: thầy cô viết "Sử với Toán đừng dính
       nhau" thì không từ khoá nào khớp, và đúng lúc đó câu đọc lại lại càng
       cần thiết.
    """
    if not isinstance(r, dict) or not r.get('loai'):
        return {'cau': '', 'canh_bao': None,
                'loi': 'Chưa chọn loại quy tắc.'}
    if r['loai'] not in QT.DANH_MUC:
        return {'cau': '', 'canh_bao': None,
                'loi': f'Không có loại quy tắc "{r["loai"]}".'}
    return {'cau': QT.cau_doc_lai(r),
            'canh_bao': QT.so_ghi_chu(r),
            'loi': None}


def thu_quy_tac(ma_phien, r, tat, nhanh=False):
    """Xếp thử rút gọn để xem thêm quy tắc này còn xếp được không.
       Chạy thẳng trong luồng HTTP vì đã chặn cứng 30 lần thử / 8 giây —
       khác hẳn lượt xếp thật (~50 giây) nên không được làm như vậy ở /api/xep.

       nhanh=True: KIỂM SAU KHI LƯU. Ngân sách 1 lần thử / 1 giây, vì câu hỏi
       lúc đó chỉ là "còn xếp được không", KHÔNG phải "xếp tối ưu chưa". Đo
       được: cấu hình lành cho lời giải trong 0,1 giây; cấu hình hỏng đốt hết
       1,1 giây mà không ra gì. Chiều đánh đổi thuận — lúc mọi thứ ổn thì gần
       như không tốn gì, chỉ chậm đúng lúc có chuyện.
    """
    cfg, _ = cau_hinh_phien(ma_phien)
    if r:
        cfg['quy_tac'].append(copy.deepcopy(r))
    for i in tat:
        if 0 <= i < len(cfg['quy_tac']):
            cfg['quy_tac'][i]['bat'] = False
    bt = X.BaiToan(cfg)
    goc = cfg.get('tim_kiem', {})
    # che_do_tai_lap=False là CỐ Ý, kể cả khi cauhinh.json bật nó: đường này
    # giải NGAY trong luồng HTTP nên bắt buộc phải giữ chặn bằng đồng hồ, không
    # thì một lượt thử quy tắc có thể giữ luồng rất lâu.
    tk = (X.gop_tim_kiem(goc, so_lan_thu=1, gioi_han_giay_moi_lan=1,
                         gioi_han_tong_giay=4, che_do_tai_lap=False) if nhanh
          else X.gop_tim_kiem(goc, so_lan_thu=30, gioi_han_giay_moi_lan=2,
                              gioi_han_tong_giay=8, che_do_tai_lap=False))
    kqt = X.tim_phuong_an(bt, tk)
    pa = kqt.tot or kqt.du_phong
    vi_pham = []
    if pa is not None:
        vi_pham = [{'ten': t, 'ghi_chu': c}
                   for kq, t, c in X.hau_kiem(bt, pa)[0] if kq == 'LỖI']
    return {'xep_duoc': kqt.tot is not None, 'co_loi_giai': pa is not None,
            'so_hop_le': kqt.so_hop_le, 'so_lan': kqt.da_thu,
            'giay': round(kqt.giay, 1), 'diem': kqt.diem,
            'vi_pham': vi_pham,
            # CHẮC CHẮN vô nghiệm (đã vét cạn) hay chỉ là "thử mãi không ra"?
            # Giao diện KHÔNG được nói "vô nghiệm" khi cờ này False — một giây
            # không đủ để khẳng định điều đó, và nói quá một lần là thầy cô
            # thôi tin mọi cảnh báo sau.
            'vet_can': bool(kqt.vet_can)}


def _tap_chi_so(ds):
    """Đổi danh sách chỉ số người dùng gửi lên thành tập số nguyên.
       Giá trị lạ thì DỪNG kèm thông báo, không im lặng bỏ qua — bỏ qua âm
       thầm ở đường ghi tệp nghĩa là ghi sai mà vẫn báo thành công."""
    if not isinstance(ds, list):
        raise SystemExit('[LỖI] Danh sách "tat" phải là một dãy [ ... ]')
    ra = set()
    for x in ds:
        try:
            ra.add(int(x))
        except (TypeError, ValueError):
            raise SystemExit(f'[LỖI] Danh sách "tat" có giá trị không phải '
                             f'số: {x!r}')
    return ra


def _gon_json(cfg):
    """In JSON dễ đọc, gom các danh sách toàn số/chuỗi lại một dòng cho
       giống cách file đang được viết tay."""
    s = json.dumps(cfg, ensure_ascii=False, indent=2)
    return re.sub(r'\[\s+([^\[\]{}]*?)\s+\]',
                  lambda m: '[' + ', '.join(x.strip()
                                            for x in m.group(1).split(',')) + ']',
                  s, flags=re.S)


SO_BAN_SAO_LUU = 5          # số bản sao lưu xoay vòng, ngoài bản gốc


def _xoay_sao_luu(tm):
    """Đẩy các bản sao lưu lùi một bậc rồi cất bản hiện tại vào cauhinh.bak.json.

       Trước đây chỉ có ĐÚNG MỘT khe: shutil.copy(cauhinh.json, cauhinh.bak.json).
       Lỡ tay tắt nhầm rồi bấm Lưu, nhận ra sai bấm Lưu lần nữa để sửa —
       chính thao tác sửa đó chép bản đã hỏng đè lên bản sao lưu. Bản gốc mất
       vĩnh viễn. Đã đo: sau 2 lần lưu, cauhinh.bak.json mang đúng nội dung đã
       hỏng chứ không còn nội dung ban đầu.

       Nay: cauhinh.bak.goc.json giữ bản ĐẦU TIÊN, chỉ ghi một lần và không bao
       giờ bị đè — dù bấm Lưu bao nhiêu lần vẫn lùi về được. Cộng thêm 5 bản
       xoay vòng cauhinh.bak.1..5.json cho các bước gần đây.
    """
    goc = os.path.join(tm, 'cauhinh.bak.goc.json')
    if not os.path.exists(goc):                       # chỉ ghi MỘT LẦN
        _chep_ben(DUONG_DAN_CAUHINH, goc)
    for i in range(SO_BAN_SAO_LUU, 1, -1):
        cu = os.path.join(tm, f'cauhinh.bak.{i - 1}.json')
        if os.path.exists(cu):
            shutil.move(cu, os.path.join(tm, f'cauhinh.bak.{i}.json'))
    bak = os.path.join(tm, 'cauhinh.bak.json')
    if os.path.exists(bak):
        shutil.move(bak, os.path.join(tm, 'cauhinh.bak.1.json'))
    # Chỉ hai bản này đi qua _chep_ben (sinh dữ liệu mới nên phải ép xuống đĩa).
    # cauhinh.bak.1..5 chỉ là shutil.move, tức đổi tên — phần siêu dữ liệu đó do
    # lần _dong_bo_thu_muc() ở cuối luu_quy_tac() lo, không cần fsync riêng.
    _chep_ben(DUONG_DAN_CAUHINH, bak)
    return bak


def luu_quy_tac(ma_phien, tat, dau=None):
    """Ghi cờ bật/tắt vào cauhinh.json. Sao lưu trước, giữ nguyên thứ tự khoá.

       Ghi NGUYÊN TỬ. Trước đây thứ tự là:
           open(cauhinh.json, 'w')      <- CẮT CỤT tệp về 0 byte ngay tại đây
           f.write(_gon_json(cfg))      <- rồi mới dựng chuỗi
       nên bất cứ lỗi nào lúc dựng chuỗi là mất trắng toàn bộ khai báo dữ liệu,
       người dùng chỉ thấy một trang báo lỗi. Đã đo: tệp còn 0 byte.

       Nay theo đúng thứ tự an toàn: dựng chuỗi -> ghi ra tệp tạm -> đọc lại
       tệp tạm để chắc chắn hợp lệ -> sao lưu -> os.replace(). os.replace()
       là thao tác nguyên tử trên cả Linux lẫn Windows, nên cauhinh.json hoặc
       là bản cũ nguyên vẹn, hoặc là bản mới nguyên vẹn, không có ở giữa.

       Cả hàm nằm trong KHOA_GHI: hai người cùng bấm Lưu thì lần lượt, không
       còn cảnh hai luồng cùng mở tệp ở chế độ 'w'.
    """
    with KHOA_GHI:
        # 2C — CHỐNG MẤT BẢN SỬA. Kiểm dấu bản BÊN TRONG khoá ghi: kiểm ở ngoài
        # rồi mới vào khoá là đúng lỗi A4 một lần nữa — hai người cùng bấm Lưu
        # sẽ cùng thấy dấu khớp, rồi lần lượt ghi đè nhau.
        bay_gio = dau_ban_cau_hinh()
        if dau != bay_gio:
            raise XungDotBanSua(
                'Tệp cauhinh.json đã đổi từ lúc bạn tải danh sách này về.\n'
                'Có thể người khác vừa bấm Lưu, hoặc tệp vừa được sửa tay.\n'
                'Bấm "Tải lại danh sách" rồi làm lại — nếu ghi đè bây giờ thì '
                'phần sửa của người kia mất sạch mà không ai biết.')
        cfg, so_file = cau_hinh_phien(ma_phien)     # dict giữ thứ tự khoá
        nhap = nhap_cua(ma_phien)
        so_nhap = len(nhap)          # CHỤP số lượng ngay lúc dựng cfg
        n = so_nhap                  # n đếm SỐ THAY ĐỔI, không phải số nháp
        for i, r in enumerate(cfg['quy_tac']):
            muon_bat = i not in tat
            if i < so_file and bool(r.get('bat', True)) != muon_bat:
                n += 1
            if muon_bat:
                r.pop('bat', None)                    # bật = bỏ hẳn khoá "bat"
            else:
                r['bat'] = False

        # 1. dựng xong chuỗi TRƯỚC, chưa đụng vào tệp nào
        chuoi = _gon_json(cfg) + '\n'

        # 2. ghi ra tệp tạm, ÉP XUỐNG ĐĨA, rồi đọc lại — hỏng thì bỏ tệp tạm,
        #    tệp thật y nguyên.
        #
        #    fsync phải nằm ở ĐÂY, trước os.replace ở bước 4. Đọc lại bằng
        #    doc_cau_hinh() KHÔNG thay thế được nó: phép đọc đó đi qua bộ nhớ
        #    đệm của hệ điều hành nên chỉ khẳng định "chuỗi hợp lệ", không
        #    khẳng định "đã nằm trên đĩa".
        tm = thu_muc_cauhinh()
        tam = os.path.join(tm, 'cauhinh.tam.json')
        with open(tam, 'w', encoding='utf-8') as f:
            f.write(chuoi)
            _dong_bo_tep(f)
        try:
            X.doc_cau_hinh(tam)
        except BaseException:
            os.remove(tam)
            raise

        # 3. sao lưu xoay vòng, rồi 4. thay thế nguyên tử
        sao_luu = _xoay_sao_luu(tm)
        os.replace(tam, DUONG_DAN_CAUHINH)

        # 5. ép CÁI TÊN vừa đổi xuống đĩa nốt
        _dong_bo_thu_muc(tm)

        # Xoá ĐÚNG số phần tử đã chụp ở đầu hàm, không .clear(): cùng một người
        # mở hai tab thì tab kia có thể vừa thêm nháp trong lúc hàm này chạy, và
        # .clear() sẽ nuốt mất bản nháp đó trong im lặng.
        del nhap[:so_nhap]
        # Dấu MỚI trả về ngay, để người vừa lưu bấm Lưu tiếp được mà không phải
        # tải lại danh sách.
        return {'doi': n, 'sao_luu': os.path.basename(sao_luu),
                'dau': dau_ban_cau_hinh()}


# ==========================================================================
# 4. MÁY CHỦ HTTP
# ==========================================================================

class May(BaseHTTPRequestHandler):
    server_version = 'XepTKB'
    sys_version = ''            # đừng khoe 'Python/3.12.3' ra ngoài
    timeout = GIAY_CHO_KET_NOI  # StreamRequestHandler.setup() tự gọi settimeout

    def log_message(self, *a):
        pass                                          # đừng làm bẩn màn hình

    def version_string(self):
        # Mặc định là server_version + ' ' + sys_version, tức 'XepTKB ' với
        # một dấu cách thừa khi sys_version rỗng. Trả thẳng cho gọn.
        return self.server_version

    # ---------------- PHỄU PHÁT PHẢN HỒI ----------------
    # ---------------- PHIÊN ----------------
    def _di_qua_tls(self):
        """Yêu cầu này tới bằng đường có TLS không? SUY TỪ Host, không từ cấu hình.

           Vì sao không làm một khoá `cookie_secure` trong tệp cấu hình như thói
           quen: mọi giá trị mặc định của cái cờ đó đều có một trạng thái hỏng,
           và hỏng TRONG IM LẶNG — đăng nhập trả 200, trình duyệt vứt cookie
           `Secure` đi vì trang đang chạy http, yêu cầu kế 401, quay lại ô mật
           khẩu, không một chữ giải thích. Bật nhầm thì hỏng đường chạy tại chỗ;
           quên bật thì hỏng đường qua proxy. Suy từ Host thì không có trạng
           thái nào sai được.

           Tin được vì Host đã đi qua danh sách trắng A1 NGAY TRƯỚC ĐÓ.
           Tập loopback ở đây là CỐ ĐỊNH, không phải danh sách cho phép — câu
           hỏi là "đường này có TLS không", khác câu "tên này có được phép không".
        """
        host = _chuan_ten_may(self._mot_dong_duy_nhat('Host') or '')
        cong = self.server.server_address[1]
        return host not in {f'127.0.0.1:{cong}', f'localhost:{cong}',
                            f'[::1]:{cong}', '127.0.0.1', 'localhost'}

    def _ten_cookie(self):
        """ĐÚNG MỘT tên cookie cho chế độ hiện tại — không bao giờ thử cả hai.

           Tiền tố __Host- đòi phải có cờ Secure, mà Secure trên http:// thì
           trình duyệt vứt đi; nên đường tại chỗ buộc phải dùng tên trơn.

           Vì sao __Host- đáng có ở đường TLS: ts.net nằm trong Public Suffix
           List, nên tail7dc28e.ts.net là một tên ĐĂNG KÝ ĐƯỢC — một máy khác
           trong cùng tailnet đặt được cookie Domain=tail7dc28e.ts.net và trình
           duyệt sẽ GỬI NÓ SANG máy quản trị này. Tiền tố __Host- cấm thuộc tính
           Domain nên bịt đúng đường đó.

           Và vì sao chỉ đọc MỘT tên: viết "thử __Host- trước, không có thì thử
           tên trơn" là tự mở lại đúng cái lỗ vừa bịt — kẻ kia chỉ cần đặt tên
           trơn là được đọc.
        """
        return TEN_COOKIE_BM if self._di_qua_tls() else TEN_COOKIE

    def _ma_phien(self):
        """Mã phiên khách gửi lên, hoặc None. HÀM TOÀN PHẦN — không bao giờ ném.

           Không dùng http.cookies.SimpleCookie: gặp một mẩu dị dạng là nó nuốt
           luôn phần còn lại hoặc ném CookieError, mà ở đây dị dạng phải cho ra
           "không có phiên" chứ không phải 500.
        """
        dong = self._mot_dong_duy_nhat('Cookie')
        if not dong:
            return None
        can = self._ten_cookie()
        for mau in dong.split(';'):
            if '=' not in mau:
                continue
            ten, _, gt = mau.partition('=')
            if ten.strip() == can:
                gt = gt.strip()
                # token_urlsafe chỉ sinh [A-Za-z0-9_-]; lọc ở đây để chuỗi rác
                # không bao giờ thành khoá tra bảng.
                return gt if gt and re.fullmatch(r'[A-Za-z0-9_-]{1,128}', gt) else None
        return None

    def _phien(self):
        """Phiên của trình duyệt này; chưa có thì CẤP MỚI (vô danh).

           Cấp ở đây chứ không ở một đường riêng, để mọi đường đều có phiên ngay
           từ yêu cầu đầu tiên — kể cả người vào thẳng /api/quy-tac.
        """
        if self._ph is None:
            ma = self._ma_phien()
            p = doc_phien(ma)
            if p is None:
                ma, p = tao_phien()
                self._cookie_moi = ma      # _tra_byte sẽ đính Set-Cookie
            self._ph = (ma, p)
        return self._ph[0]

    def _ten_dang_nhap(self):
        """Tên tài khoản của phiên hiện tại, hoặc None nếu chưa đăng nhập."""
        self._phien()
        return (self._ph[1] or {}).get('ten')

    def _chan_neu_chua_dang_nhap(self, duong):
        """True = ĐÃ trả lời xong (401/503), người gọi phải return ngay.

           Tên hàm nói đúng việc nó làm: nó CHẶN và TRẢ LỜI, không phải chỉ
           kiểm rồi để người gọi tự xử.
        """
        if duong in DUONG_MO:
            return False
        if not TAI_KHOAN:
            # 503 chứ không 401: đây không phải "bạn chưa đăng nhập" mà là
            # "máy chủ chưa cài xong". Nói sai thì người vận hành đi tìm mật
            # khẩu thay vì đi tạo tài khoản.
            self._bao_loi(duong,
                          '[LỖI] Máy chủ chưa có tài khoản nào.\n'
                          '      Chạy: python3 tao_mat_khau.py them', 503)
            return True
        if self._ten_dang_nhap() is None:
            self._bao_loi(duong, 'Bạn cần đăng nhập để dùng chức năng này.', 401)
            return True
        return False

    def _dong_cookie(self, ma):
        """Dòng Set-Cookie. SameSite=Lax khai TƯỜNG MINH — xem ghi chú."""
        phan = [f'{self._ten_cookie()}={ma}', 'Path=/', 'HttpOnly',
                # Khai Lax TƯỜNG MINH, đừng bỏ trống cho "giống mặc định":
                # Chrome có ngoại lệ "Lax+POST 2 phút" cho phép POST cross-site
                # cấp cao nhất mang theo cookie, và ngoại lệ đó CHỈ áp cho cookie
                # KHÔNG khai SameSite. Bỏ trống không giống khai Lax.
                'SameSite=Lax']
        if self._di_qua_tls():
            phan.append('Secure')          # __Host- đòi Secure, và đã có TLS thật
        return '; '.join(phan)

    def _tra_byte(self, ma, tieu_de, than):
        """Nơi DUY NHẤT được gọi send_response() và send_header().

           tieu_de là danh sách [(tên, giá trị), ...] — nhận cả danh sách chứ
           không nhận từng cái, vì phải KIỂM XONG HẾT rồi mới được phát dòng
           trạng thái đầu tiên. Xem ghi chú dài ở mục 1b: kiểm sau send_response
           là để lại một phản hồi có HAI dòng trạng thái.

           Ca thử canh bất biến này bằng grep: trong cả web.py không được còn
           self.send_header( LẪN self.send_response( nào ngoài thân hàm này.
        """
        if isinstance(than, str):
            than = than.encode('utf-8')
        dong = list(tieu_de)
        if self._cookie_moi:
            # Đính ở ĐÂY để cookie cũng đi qua đúng phễu kiểm tiêu đề (A10),
            # thay vì gọi thẳng send_header ở chỗ khác.
            dong.append(('Set-Cookie', self._dong_cookie(self._cookie_moi)))
        dong += [('Content-Length', str(len(than)))]
        for ten, gt in dong:                 # 1. KIỂM HẾT — có thể ném
            _kiem_tieu_de(ten, gt)
        self.send_response(ma)               # 2. giờ mới phát dòng trạng thái
        for ten, gt in dong:                 # 3.
            self.send_header(ten, gt)
        self.end_headers()                   # 4.
        self.wfile.write(than)

    # ---------------- tiện ích ----------------
    def _tra(self, ma, kieu, than):
        self._tra_byte(ma, [('Content-Type', f'{kieu}; charset=utf-8'),
                            ('Cache-Control', 'no-store')], than)

    def _json(self, obj, ma=200):
        self._tra(ma, 'application/json',
                  json.dumps(obj, ensure_ascii=False))

    def _bao_loi(self, duong, chu, ma=400):
        """Trả một câu lỗi, ĐÚNG KIỂU cho từng đường.

           Hai đường tải tệp được mở bằng ĐIỀU HƯỚNG CẢ TRANG
           (app.js: window.location = '/api/tai-ve'), không phải fetch. Trả JSON
           ở đó là đẩy giáo viên ra một tab trắng chỉ có {"loi": ...} trần, mất
           luôn màn hình đang xem và không có nút quay lại rõ ràng.
        """
        if duong in ('/api/tai-ve', '/api/tai-web'):
            return self._tra(ma, 'text/plain', chu)
        return self._json({'loi': chu}, ma)

    # ---------------- chỉ nhận yêu cầu phát từ CHÍNH TRANG NÀY ----------------
    def _ten_may_cho_phep(self):
        """Tên máy được phép. Có cauhinh_may_chu.json thì danh sách đó là
           DUY NHẤT — nó THAY THẾ mặc định chứ không cộng thêm vào.

           Vì sao thay thế: đặt máy chủ sau một proxy có TLS rồi mà vẫn để
           '[::1]:20266' hay 'localhost' lọt qua là giữ lại đúng những cửa mình
           tưởng đã đóng. Ai cần chúng thì viết vào tệp — một chỗ, nhìn là thấy.
        """
        if HOST_CHO_PHEP:
            return HOST_CHO_PHEP
        cong = self.server.server_address[1]
        return {f'127.0.0.1:{cong}', f'localhost:{cong}', f'[::1]:{cong}',
                '127.0.0.1', 'localhost'}

    def _nguon_cho_phep(self):
        """Nguồn gốc được phép — bảng RIÊNG, không suy ra từ bảng tên máy.

           Origin có giao thức đằng trước, Host thì không. Tự ghép
           'https://' + host để đỡ phải khai hai lần nghe thì tiện, nhưng nó
           tự tay chấp nhận cả https lẫn http cho cùng một tên, tức mở lại đúng
           cái mà việc đặt sau TLS định đóng. Hai bảng, khai hai lần.
        """
        if ORIGIN_CHO_PHEP:
            return ORIGIN_CHO_PHEP
        cong = self.server.server_address[1]
        return {f'http://127.0.0.1:{cong}', f'http://localhost:{cong}',
                f'http://[::1]:{cong}'}

    def _kiem_nguon_goc(self, co_than):
        """Chặn trang web lạ sai khiến máy chủ này.

           Đã đo trên máy chủ thật: một trang bất kỳ mà thầy cô mở chỉ cần
           chạy fetch('/api/luu-quy-tac', {method:'POST',
           headers:{'Content-Type':'text/plain'}, body:'{"tat":[0,...,9]}'})
           là tắt sạch 10 quy tắc cứng và GHI ĐÈ cauhinh.json — máy chủ trả
           200. 'text/plain' là "simple request" nên trình duyệt gửi thẳng,
           không hỏi preflight; máy chủ lại json.loads bất kể Content-Type.

           Thêm đăng nhập bằng cookie sẽ làm lỗ này NẶNG HƠN chứ không nhẹ
           đi — cookie tự đính kèm, trang lạ mượn luôn quyền của người đang
           đăng nhập. Vì vậy phải vá TRƯỚC khi đặt cổng đăng nhập.

           Ba lớp, mỗi lớp chặn một kiểu:
             Host        — chặn DNS rebinding (tên miền lạ trỏ về 127.0.0.1)
             Origin      — chặn yêu cầu phát từ trang khác
             Content-Type— buộc application/json, kiểu này KHÔNG gửi được
                           bằng "simple request", phải qua preflight, mà
                           preflight lại mang Origin nên bị lớp trên chặn.
        """
        tho_host = self._mot_dong_duy_nhat('Host') or ''
        _kiem_ky_tu_dieu_khien('Host', tho_host)
        host = _chuan_ten_may(tho_host)
        if host not in self._ten_may_cho_phep():
            raise SystemExit(
                f'[LỖI] Yêu cầu gửi tới tên máy lạ: {host!r}\n'
                f'      Máy chủ này chỉ nhận các tên đã khai: '
                f'{", ".join(sorted(self._ten_may_cho_phep()))}\n'
                f'      Thêm tên mới thì sửa cauhinh_may_chu.json rồi chạy lại '
                f'web.py.')

        # Cookie cũng chỉ được đúng một dòng: hai dòng thì headers.get() lấy
        # dòng đầu, mà một công cụ trung gian có thể chọn dòng khác ta — đúng
        # kiểu lệch-cách-hiểu mà A1 sinh ra để chặn.
        self._mot_dong_duy_nhat('Cookie')

        tho_org = self._mot_dong_duy_nhat('Origin')
        if tho_org is not None:
            _kiem_ky_tu_dieu_khien('Origin', tho_org)
            if _chuan_ten_may(tho_org) not in self._nguon_cho_phep():
                raise SystemExit(
                    f'[LỖI] Yêu cầu phát đi từ một trang khác: {tho_org!r}\n'
                    f'      Máy chủ chỉ nhận lệnh từ chính trang xếp thời khoá '
                    f'biểu, không nhận từ trang web nào khác.\n'
                    f'      Nguồn gốc đã khai: '
                    f'{", ".join(sorted(self._nguon_cho_phep()))}')

        if co_than:
            kieu = (self.headers.get('Content-Type') or '')
            kieu = kieu.split(';')[0].strip().lower()
            if kieu != 'application/json':
                raise SystemExit(
                    f'[LỖI] Kiểu nội dung không nhận được: {kieu or "(trống)"}\n'
                    f'      Đường này chỉ nhận "application/json".')

    def _mot_dong_duy_nhat(self, ten):
        """Tiêu đề này chỉ được xuất hiện ĐÚNG MỘT LẦN. Trả về giá trị, hoặc None.

           Đã đo: gửi hai dòng "Host" (dòng thật trước, dòng giả sau) thì máy chủ
           cho 200 — vì self.headers.get() chỉ lấy dòng ĐẦU TIÊN. Hôm nay chưa
           khai thác được (HTTP/1.0, không keep-alive, không proxy), nhưng đây
           đúng là kiểu lệch-cách-hiểu mà A1 sinh ra để chặn: một công cụ trung
           gian có thể chọn dòng khác với dòng ta chọn.

           Áp cho cả Content-Length vì tiêu đề đó trùng lặp chính là nền của
           request smuggling, nếu ngày nào đó ai bật HTTP/1.1.
        """
        ds = self.headers.get_all(ten) or []
        if len(ds) > 1:
            raise SystemExit(
                f'[LỖI] Yêu cầu mang {len(ds)} dòng "{ten}".\n'
                f'      Tiêu đề này chỉ được xuất hiện đúng một lần.')
        return ds[0] if ds else None

    def _doc_than_co_tran(self, n):
        """Đọc đúng n byte thân, theo từng mẩu 64 KB, không bao giờ quá trần.

           Đây là LỚP THỨ HAI. Lớp thứ nhất — so Content-Length với trần trước
           khi đọc — đã chặn được mọi ca hôm nay và là lớp rẻ nhất. Lớp này vẫn
           phải có vì nó là bất biến sống sót qua thay đổi: ngày nào đó ai mở
           lại Transfer-Encoding hoặc thêm một đường tải tệp lên, lớp thứ nhất
           lặng lẽ thành vô nghĩa còn lớp này vẫn đúng.
        """
        goi = bytearray()
        con = n
        while con > 0:
            m = self.rfile.read(min(65536, con))
            if not m:
                break
            goi += m
            con -= len(m)
            if len(goi) > TRAN_THAN:
                raise ThanQuaLon(
                    f'[LỖI] Thân yêu cầu vượt quá {TRAN_THAN // 1024} KB.')
        return bytes(goi)

    def _doc_bo(self):
        """Sau khi trả 413: đọc bỏ phần thân còn lại, NHƯNG CÓ CHẶN.

           Vì sao phải đọc bỏ chút ít: đóng socket trong lúc bên kia còn đang
           ghi sẽ gây RST, và nhiều client (kể cả trình duyệt) MẤT LUÔN phản hồi
           413 — người dùng chỉ thấy "network error", không thấy câu tiếng Việt
           mình vừa viết.

           Vì sao không đọc hết: đọc hết là thua ngay mục đích, 20 MB vẫn phải
           nuốt. Chặn ở 256 KB / 0,5 giây là đủ để bộ đệm gửi của người lỡ tay
           thoát ra, còn kẻ tấn công thì không ép được ta đọc thêm.

           Đọc thẳng từ self.connection chứ không qua self.rfile: rfile là
           BufferedReader, một lần đọc hết giờ giữa chừng làm mất số byte đã
           đệm và không lấy lại được — ca thử sẽ đo ra số lung tung.
        """
        da, t0, cu = 0, time.monotonic(), None
        try:
            cu = self.connection.gettimeout()
            self.connection.settimeout(0.1)
            while da < TRAN_DOC_BO and time.monotonic() - t0 < GIAY_DOC_BO:
                try:
                    m = self.connection.recv(65536)
                except OSError:
                    break
                if not m:
                    break
                da += len(m)
        except OSError:
            pass
        finally:
            try:
                self.connection.settimeout(cu)
            except OSError:
                pass
        return da

    def _than_json(self, bat_buoc=False):
        """Đọc thân JSON của yêu cầu.

           bat_buoc=True dành cho các đường GHI XUỐNG TỆP: thiếu thân là DỪNG,
           tuyệt đối không được coi là "thân rỗng".

           Vì sao phải chặt như vậy: trước đây chỉ có
               n = int(self.headers.get('Content-Length') or 0)
           nên một yêu cầu gửi kiểu "Transfer-Encoding: chunked" (hợp lệ với
           HTTP, và KHÔNG kèm Content-Length) cho n = 0 -> trả {} ->
           /api/luu-quy-tac hiểu thành "không tắt quy tắc nào" -> bỏ khoá "bat"
           của MỌI quy tắc rồi ghi đè cauhinh.json, mà vẫn trả 200 báo thành
           công. Đã đo: 10 quy tắc cứng bị bật lại, người dùng không hề biết.
        """
        if self.headers.get('Transfer-Encoding'):
            raise SystemExit(
                '[LỖI] Máy chủ không nhận yêu cầu kiểu "Transfer-Encoding".\n'
                '      Hãy gửi kèm "Content-Length".')
        tho = self._mot_dong_duy_nhat('Content-Length')
        if tho is None or str(tho).strip() == '':
            if bat_buoc:
                raise SystemExit(
                    '[LỖI] Yêu cầu thiếu phần thân.\n'
                    '      Đường này ghi xuống tệp nên bắt buộc phải có thân.')
            return {}
        # int() của Python quá dễ dãi để dùng cho một con số quyết định việc
        # cấp phát bộ nhớ. Đã đo: int('1_0') = 10, int(' +10 ') = 10, và
        # int('١٠') = 10 (chữ số Ả Rập). Ép đúng dạng chữ số ASCII.
        if not re.fullmatch(r'[0-9]{1,15}', str(tho).strip()):
            raise SystemExit(f'[LỖI] "Content-Length" không phải số: {tho!r}')
        n = int(str(tho).strip())
        if n == 0:
            if bat_buoc:
                raise SystemExit(
                    '[LỖI] Yêu cầu thiếu phần thân.\n'
                    '      Đường này ghi xuống tệp nên bắt buộc phải có thân.')
            return {}
        # LỚP 1: chặn theo lời khai, TRƯỚC khi đọc một byte nào.
        # Đây là chỗ quyết định của bất biến A9. Đã đo trên bản cũ: thân
        # 20.000.022 byte cho 200 OK, vì rfile.read(n) cấp phát n byte trước
        # mọi kiểm tra.
        if n > TRAN_THAN:
            raise ThanQuaLon(
                f'[LỖI] Thân yêu cầu quá lớn: {n:,} byte.\n'
                f'      Máy chủ chỉ nhận tối đa {TRAN_THAN // 1024} KB.')
        try:
            d = json.loads(self._doc_than_co_tran(n).decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as e:
            raise SystemExit(f'[LỖI] Thân yêu cầu không phải JSON hợp lệ: {e}')
        if not isinstance(d, dict):
            raise SystemExit('[LỖI] Thân yêu cầu phải là một khối { ... }')
        return d

    # ---------------- GET ----------------
    def _bat_dau(self):
        """Đặt lại trạng thái cho MỘT yêu cầu. Gọi ở đầu do_GET/do_POST."""
        self._ph = None
        self._cookie_moi = None

    def do_GET(self):
        duong = self.path.split('?')[0]
        self._bat_dau()
        try:
            self._kiem_nguon_goc(co_than=False)
            self._phien()                 # cấp phiên vô danh nếu chưa có
            # Cổng nằm SAU A1 (Host lạ phải vẫn là 400, không phải 401) và
            # TRƯỚC khi đọc thân (khách lạ không được ép ta cấp phát 256 KB).
            if self._chan_neu_chua_dang_nhap(duong):
                return
            if duong == '/api/toi-la-ai':
                return self._json({'dang_nhap': self._ten_dang_nhap() is not None,
                                   'ten': self._ten_dang_nhap()})
            if duong in ('/', '/index.html'):
                return self._tinh('index.html')
            if duong.startswith('/web/'):
                return self._tinh(duong[5:])
            if duong == '/api/trang-thai':
                return self._trang_thai()
            if duong == '/api/quy-tac':
                return self._json(doc_quy_tac(self._phien()))
            if duong == '/api/loai-quy-tac':
                return self._json(danh_muc_loai())
            if duong == '/api/gia-tri':
                return self._json(gia_tri_chon())
            if duong == '/api/tai-ve':
                return self._tai_ve()
            if duong == '/api/tai-web':
                return self._tai_web()
            self._tra(404, 'text/plain', 'Không có trang này')
        except SystemExit as e:
            # Khai báo sai là lỗi của dữ liệu người dùng gửi lên -> 400,
            # không phải máy chủ hỏng.
            self._bao_loi(duong, str(e), 400)
        except (TimeoutError, ConnectionError):
            # Kết nối im lặng hoặc bị ngắt giữa chừng KHÔNG phải sự cố phần
            # mềm. Để nó rơi vào except Exception là mỗi lần lại in nguyên một
            # traceback kèm mã sự cố ra cửa sổ dòng lệnh của cô giáo — màn hình
            # đầy chữ đỏ, tưởng phần mềm hỏng.
            return
        except Exception:
            self._json({'loi': _loi_su_co(_bao_su_co(f'{self.command} {duong}'))},
                       500)

    def _tinh(self, ten):
        if ten not in TINH:
            return self._tra(404, 'text/plain', 'Không có tệp này')
        with open(os.path.join(THU_MUC_WEB, ten), 'rb') as f:
            self._tra(200, TINH[ten], f.read())

    def _trang_thai(self):
        tu = 0
        if '?' in self.path:
            for phan in self.path.split('?', 1)[1].split('&'):
                if phan.startswith('tu='):
                    tho = phan[3:]
                    if tho == '':
                        continue
                    try:
                        tu = max(0, int(tho))
                    except ValueError:
                        raise SystemExit(
                            f'[LỖI] Tham số "tu" phải là số: {tho!r}')
        with KHOA:
            t = dict(TT)
            log = t.pop('log')
        t['log_moi'] = log[tu:]
        t['log_het'] = len(log)
        return self._json(t)

    def _chan_neu_lech_dau(self, duong):
        """QĐ 4 — kết quả xếp cũng có dấu bản. True = ĐÃ trả lời xong (409).

           Lỗ đang bịt: cô B bấm Xếp đè kết quả thầy A đang mở; A bấm Tải về và
           nhận tệp của B mà không hề biết. Dấu bản của 2C canh cauhinh.json,
           KHÔNG canh kết quả xếp — cùng một lỗi, khác tầng.

           NGOẠI LỆ CÓ CHỦ Ý: máy chủ vừa khởi động lại thì TT['dau'] là None,
           mà tệp kết quả hôm qua vẫn nằm trên đĩa. Lúc đó CHO TẢI. Từ chối là
           từ chối oan — người dùng không làm gì sai, chỉ là máy vừa bật lại.
        """
        with KHOA:
            dau_may = TT.get('dau')
            nguoi = TT.get('nguoi')
        if not dau_may:
            return False                      # ngoại lệ: chưa xếp lần nào
        dau_khach = urllib.parse.parse_qs(
            urllib.parse.urlparse(self.path).query).get('dau', [''])[0]
        if dau_khach == dau_may:
            return False
        self._bao_loi(
            duong,
            f'Kết quả đã bị thay bởi lượt xếp của '
            f'{nguoi or "một người khác"}, xem lại trước khi tải.\n'
            f'Bấm "Xem TKB" để tải lại màn hình, rồi tải lần nữa.', 409)
        return True

    def _tai_ve(self):
        if self._chan_neu_lech_dau('/api/tai-ve'):
            return
        ten = X.doc_cau_hinh(DUONG_DAN_CAUHINH)['thong_tin']['file_xuat']
        # Dựng giá trị tiêu đề TRƯỚC khi mở tệp: khai sai thì dừng sạch bằng
        # một câu tiếng Việt, đừng để lọt tới lúc đã phát dòng trạng thái.
        bo_tri = _ten_tep_an_toan(ten)
        dd = os.path.join(thu_muc_cauhinh(), os.path.basename(ten))
        if not os.path.exists(dd):
            return self._tra(404, 'text/plain',
                             'Chưa có file kết quả. Hãy xếp thời khoá biểu trước.')
        with open(dd, 'rb') as f:
            than = f.read()
        self._tra_byte(200, [
            ('Content-Type', 'application/vnd.openxmlformats-'
                             'officedocument.spreadsheetml.sheet'),
            ('Content-Disposition', bo_tri),
            ('Cache-Control', 'no-store')], than)

    def _tai_web(self):
        if self._chan_neu_lech_dau('/api/tai-web'):
            return
        dd = os.path.join(thu_muc_cauhinh(), 'tkb_web.html')
        if not os.path.exists(dd):
            return self._tra(404, 'text/plain',
                             'Chưa có trang web. Hãy xếp thời khoá biểu trước.')
        with open(dd, 'rb') as f:
            than = f.read()
        # Tên ở đây là HẰNG CHUỖI nên vốn không có lỗ. Vẫn đi qua đúng phễu như
        # mọi đường khác — biến cái may thành cấu trúc.
        self._tra_byte(200, [
            ('Content-Type', 'text/html; charset=utf-8'),
            ('Content-Disposition', _ten_tep_an_toan('tkb_web.html')),
            ('Cache-Control', 'no-store')], than)

    # ---------------- POST ----------------
    def do_POST(self):
        duong = self.path.split('?')[0]
        self._bat_dau()
        try:
            self._kiem_nguon_goc(co_than=True)
            self._phien()                 # cấp phiên vô danh nếu chưa có
            if self._chan_neu_chua_dang_nhap(duong):
                return
            if duong == '/api/dang-nhap':
                return self._dang_nhap()
            if duong == '/api/dang-xuat':
                return self._dang_xuat()
            if duong == '/api/xep':
                return self._xep()
            if duong == '/api/luu-quy-tac':
                return self._luu()
            if duong == '/api/them-quy-tac':
                return self._json(them_quy_tac(
                    self._phien(),
                    self._than_json(bat_buoc=True).get('quy_tac')))
            if duong == '/api/xoa-quy-tac':
                return self._json(xoa_quy_tac(self._phien(), self._chi_so()))
            if duong == '/api/thu-quy-tac':
                return self._thu()
            self._tra(404, 'text/plain', 'Không có trang này')
        except ThanQuaLon as e:
            # Trả 413 TRƯỚC, rồi mới đọc bỏ chút ít — xem _doc_bo().
            self._json({'loi': str(e)}, 413)
            self._doc_bo()
        except XungDotBanSua as e:
            # 409, không phải 400 — xem docstring của XungDotBanSua.
            self._bao_loi(duong, str(e), 409)
        except SystemExit as e:
            self._bao_loi(duong, str(e), 400)
        except (TimeoutError, ConnectionError):
            return
        except Exception:
            self._json({'loi': _loi_su_co(_bao_su_co(f'{self.command} {duong}'))},
                       500)

    def _cau_bi_khoa(self, ten, giay):
        """Câu báo bị khoá tạm. Nói RÕ còn mấy phút, và cách gỡ ngay tại máy.

           Cố ý KHÔNG dùng câu chung "tên hoặc mật khẩu không đúng": người bị
           khoá gần như luôn là thầy cô gõ nhầm, và câu chung sẽ đẩy họ đi thử
           lại thêm chục lần rồi đi đổi mật khẩu — trong khi thứ họ cần biết là
           "đợi 12 phút". Cái giá của việc nói thật: ai chịu gõ sai đủ ngưỡng
           thì biết được tên đó có tồn tại. Với một tài khoản dùng chung mang
           tên khoa thì đó không phải bí mật, và đổi lại là một câu dùng được.

           LÀM TRÒN LÊN: "còn 0 phút" là câu vô nghĩa với người đang đợi.
        """
        phut = max(1, -(-giay // 60))
        return (f'Tài khoản "{ten}" đang bị khoá tạm — còn {phut} phút nữa mới '
                f'thử lại được.\n'
                f'Gõ sai mật khẩu {TK.SO_LAN_SAI_TOI_DA} lần liên tiếp thì khoá '
                f'{TK.GIAY_KHOA // 60} phút; gõ thêm lúc này KHÔNG làm dài thêm.\n'
                f'Cần vào ngay thì ra máy đang chạy phần mềm, mở cửa sổ dòng '
                f'lệnh và gõ:\n'
                f'    python3 tao_mat_khau.py mo-khoa {ten}')

    def _dang_nhap(self):
        d = self._than_json(bat_buoc=True)
        ma_cu = self._phien()
        ma_moi, ten, khoa = dang_nhap(ma_cu, d.get('ten'), d.get('mat_khau'))
        if ma_moi is None and khoa > 0:
            # 429 chứ không 401: đây không phải "sai mật khẩu" mà là "thôi, đợi
            # đã". Giao diện hiện thẳng câu này, không đẩy về ô mật khẩu trống.
            print(f'[ĐĂNG NHẬP BỊ KHOÁ] {ascii(ten)} còn {khoa}s',
                  file=sys.stderr)
            return self._json({'loi': self._cau_bi_khoa(ten, khoa)}, 429)
        if ma_moi is None:
            # MỘT câu duy nhất cho mọi nhánh sai, giống nhau từng byte: sai mật
            # khẩu · tên không tồn tại · tên sai cú pháp · tài khoản đã tắt.
            # Mã HTTP cũng phải giống nhau, khác mã cũng là một kênh rò rỉ.
            print(f'[ĐĂNG NHẬP SAI] {ascii(str(d.get("ten"))[:64])}',
                  file=sys.stderr)
            return self._json(
                {'loi': 'Tên đăng nhập hoặc mật khẩu không đúng.'}, 401)
        self._cookie_moi = ma_moi        # _tra_byte đính Set-Cookie mã MỚI
        self._ph = (ma_moi, CAC_PHIEN.get(ma_moi))
        print(f'[ĐĂNG NHẬP] {ascii(ten)}', file=sys.stderr)
        return self._json({'ok': True, 'ten': ten})

    def _dang_xuat(self):
        # Xoá bản ghi phía máy chủ TRƯỚC, rồi mới trả cookie rỗng. Bản ghi máy
        # chủ mới là quyền lực; cookie chỉ là cái vé. Xoá cookie mà giữ bản ghi
        # là vô nghĩa.
        ma = self._phien()
        xoa_phien(ma)
        self._ph = (None, None)
        self._cookie_moi = None
        than = json.dumps({'ok': True}, ensure_ascii=False)
        return self._tra_byte(200, [
            ('Content-Type', 'application/json; charset=utf-8'),
            ('Cache-Control', 'no-store'),
            ('Set-Cookie', f'{self._ten_cookie()}=; Path=/; HttpOnly; '
                           f'SameSite=Lax; Max-Age=0'
                           + ('; Secure' if self._di_qua_tls() else ''))], than)

    def _xep(self):
        # Đọc và kiểm thân TRƯỚC khi giành chỗ: yêu cầu hỏng thì phải trả lỗi
        # mà không chiếm mất lượt của người khác.
        d = self._than_json()
        tuan = (d.get('tuan') or '').strip() or None
        seed = d.get('seed')
        so_lan = d.get('so_lan')
        tat = sorted(_tap_chi_so(d.get('tat', [])))
        seed = int(seed) if str(seed).strip() not in ('', 'None', 'null') else None
        so_lan = int(so_lan) if str(so_lan).strip() not in ('', 'None', 'null') else None

        if not gianh_luot():
            return self._json({'loi': 'Đang xếp, vui lòng đợi.'}, 409)
        try:
            threading.Thread(target=_chay,
                             args=(self._phien(), tuan, seed, so_lan, tat),
                             daemon=True).start()
        except BaseException:
            dat(dang_chay=False, xong=True)     # nhả chỗ, đừng kẹt mãi
            raise
        return self._json({'ok': True})

    def _thu(self):
        # NHÁNH RẼ SỚM cho câu đọc lại — TRƯỚC cả phép kiểm "đang xếp" lẫn
        # KHOA_THU. Câu đọc lại chỉ ghép chuỗi, không giải gì; bắt nó xếp hàng
        # sau một lượt xếp thử 8 giây (hoặc sau một lượt xếp thật 50 giây) thì
        # ô nhập đứng hình đúng lúc người dùng đang gõ.
        d0 = self._than_json()
        if d0.get('doc_lai'):
            return self._json(doc_lai_quy_tac(d0.get('quy_tac')))
        with KHOA:
            ban = TT['dang_chay']
        if ban:
            return self._json({'loi': 'Đang xếp, vui lòng đợi.'}, 409)
        d = d0
        # Dùng CHUNG _tap_chi_so() với bốn đường kia. Trước đây đường này tự
        # viết [int(x) for x in ...], nên {"tat":["a"]} cho 500 kèm mã sự cố,
        # trong khi đúng dữ liệu đó ở /api/luu-quy-tac lại cho 400 kèm câu
        # tiếng Việt chỉ đích danh chỗ sai.
        tat = sorted(_tap_chi_so(d.get('tat', [])))
        # Đường này GIẢI NGAY trong luồng HTTP. Cờ dang_chay ở trên chỉ ngăn nó
        # chồng lên một lượt xếp thật, KHÔNG ngăn hai lời gọi thử chồng nhau —
        # mà bộ giải là Python thuần nên hai bộ giải cùng chạy chỉ chia đôi một
        # lõi, cả hai cùng chậm. Một chỗ duy nhất được thử tại một thời điểm.
        if not KHOA_THU.acquire(blocking=False):
            return self._json({'loi': 'Đang thử một quy tắc khác, đợi vài giây '
                                      'rồi bấm lại.'}, 409)
        try:
            return self._json(thu_quy_tac(self._phien(), d.get('quy_tac'),
                                          tat, nhanh=bool(d.get('nhanh'))))
        finally:
            KHOA_THU.release()

    def _luu(self):
        d = self._than_json(bat_buoc=True)
        if 'tat' not in d:
            raise SystemExit(
                '[LỖI] Yêu cầu lưu thiếu danh sách "tat".\n'
                '      Không có danh sách này thì không biết quy tắc nào bị '
                'tắt — ghi bừa xuống tệp là bật lại hết.')
        if 'dau' not in d:
            raise SystemExit(
                '[LỖI] Yêu cầu lưu thiếu "dau" (dấu bản của cauhinh.json).\n'
                '      Dấu này lấy từ /api/quy-tac. Thiếu nó thì không cách gì '
                'biết tệp có bị người khác đổi từ lúc bạn tải danh sách về '
                'hay không, nên máy chủ từ chối ghi.')
        return self._json(luu_quy_tac(self._phien(), _tap_chi_so(d['tat']),
                                      d.get('dau')))

    def _chi_so(self):
        d = self._than_json(bat_buoc=True)
        if 'i' not in d:
            raise SystemExit('[LỖI] Yêu cầu xoá thiếu số thứ tự "i".')
        try:
            return int(d['i'])
        except (TypeError, ValueError):
            raise SystemExit(f'[LỖI] Số thứ tự "i" không phải số: {d["i"]!r}')


# ==========================================================================
# 5. HÀM MAIN
# ==========================================================================

def main():
    global DUONG_DAN_CAUHINH
    ap = argparse.ArgumentParser(description='Giao diện web cho phần mềm xếp TKB')
    ap.add_argument('--port', type=int, default=20266)
    ap.add_argument('--cauhinh', default=DUONG_DAN_CAUHINH)
    ap.add_argument('--tai-khoan', dest='tai_khoan',
                    default=DUONG_DAN_TAI_KHOAN,
                    help='đường dẫn tai_khoan.json (dành cho ca thử)')
    args = ap.parse_args()
    DUONG_DAN_CAUHINH = os.path.abspath(args.cauhinh)

    # Nạp TRƯỚC khi bind cổng: hỏng thì phải kêu trước dòng "Mở trình duyệt
    # vào...", không thì người dùng đọc lướt qua tưởng đã chạy ngon.
    host, org, ghi_chu = nap_cau_hinh_may_chu()

    # Nạp tài khoản TRƯỚC khi bind cổng, và trước cả dòng "Mở trình duyệt vào".
    # Chết sau khi bind thì để lại một cổng nửa vời; in lỗi SAU dòng đó thì
    # người dùng đọc lướt qua tưởng đã chạy được.
    ok_tk, loi_tk = nap_tai_khoan_may_chu(os.path.abspath(args.tai_khoan))
    if not ok_tk:
        print(loi_tk, file=sys.stderr)
        raise SystemExit(1)

    # Ghi thử TRƯỚC khi bind cổng, và trước cả dòng "Mở trình duyệt vào".
    # Ổ chỉ-đọc là lỗi im lặng nhất trong cả phần mềm: mọi thứ chạy ngon cho
    # tới đúng lúc bấm Lưu. Xem ghi chú dài ở kiem_ghi_duoc().
    ok_ghi, loi_ghi = kiem_ghi_duoc(thu_muc_cauhinh())
    if not ok_ghi:
        print(loi_ghi, file=sys.stderr)
        raise SystemExit(1)

    dia_chi = ('127.0.0.1', args.port)                # CHỈ máy này, không mở ra mạng
    may = ThreadingHTTPServer(dia_chi, May)
    may.daemon_threads = True
    print('=' * 70)
    print(' XẾP THỜI KHÓA BIỂU — GIAO DIỆN WEB'.center(70))
    print('=' * 70)
    print(f'  Mở trình duyệt vào:  http://127.0.0.1:{args.port}')
    print(f'  Cấu hình đang dùng:  {DUONG_DAN_CAUHINH}')
    print(f'  Tài khoản            :  {len(TAI_KHOAN)} người '
          f'({", ".join(sorted(TAI_KHOAN))})')
    if ghi_chu:
        print(ghi_chu)
    if host or org:
        # Có khai tên ngoài loopback -> máy khác TRONG MẠNG RIÊNG vào được
        # (qua proxy), nên đừng in câu "máy khác không vào được" nữa.
        print('  Máy chủ vẫn chỉ nghe 127.0.0.1; đường vào từ ngoài là do')
        print('  proxy chuyển tiếp. Sửa danh sách thì phải chạy lại web.py.')
    else:
        print('  Chỉ chạy trên máy này, máy khác trong mạng không vào được.')
    print('  Tắt: bấm Ctrl+C ở cửa sổ này.')
    print('=' * 70)
    try:
        may.serve_forever()
    except KeyboardInterrupt:
        print('\nĐã tắt máy chủ.')
    finally:
        may.server_close()


if __name__ == '__main__':
    main()

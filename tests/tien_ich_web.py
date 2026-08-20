#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 TIỆN ÍCH DÙNG CHUNG CHO CÁC CA THỬ GIAO DIỆN WEB
--------------------------------------------------------------------------
 Vì sao có tệp này: trước đây tests/thu_web.py gọi THẲNG hàm Python
 (web._chay, web.luu_quy_tac) cho ba trong năm ca. Cách đó bỏ qua hẳn tầng
 HTTP — tức là bỏ qua đúng chỗ sắp đặt cổng đăng nhập. Ca thử kiểu đó sẽ
 vẫn XANH dù cổng đăng nhập hỏng hoàn toàn: xanh giả, nguy hiểm hơn là đỏ.

 Từ nay mọi ca đi qua HTTP thật, bằng đúng lớp May của web.py.

 Ba thứ ở đây:
   cau_hinh_tam()  — dựng cauhinh.json + mau_tkb.xlsx trong thư mục tạm
   MayChuTam       — bật máy chủ thật trên cổng tự chọn, tắt sạch khi xong
   Khach           — khách HTTP: giữ cookie, và gửi được cả yêu cầu DỊ DẠNG
                     (sai Content-Type, thiếu Content-Length, chunked...)
                     mà urllib không gửi nổi
==========================================================================
"""
import io
import json
import os
import shutil
import socket
import sys
import threading
from http.server import ThreadingHTTPServer

GOC_TM = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if GOC_TM not in sys.path:
    sys.path.insert(0, GOC_TM)

import xep_tkb as X          # noqa: E402
import tai_khoan as TK       # noqa: E402
import web                   # noqa: E402


def cau_hinh_tam(thu_muc, sua=None):
    """Chép cauhinh.json + mau_tkb.xlsx sang thư mục tạm, khoá chặt tim_kiem
       để hai lần chạy cho ra đúng cùng một dãy phương án."""
    cfg = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
    cfg['tim_kiem'] = {'so_lan_thu': 8, 'gioi_han_buoc': 30000,
                       'gioi_han_giay_moi_lan': 10,
                       'gioi_han_tong_giay': 3600, 'seed': 2027}
    if sua:
        sua(cfg)
    dd = os.path.join(thu_muc, 'cauhinh.json')
    with io.open(dd, 'w', encoding='utf-8') as f:
        json.dump(cfg, f, ensure_ascii=False)
    shutil.copy(os.path.join(GOC_TM, 'mau_tkb.xlsx'),
                os.path.join(thu_muc, 'mau_tkb.xlsx'))
    return dd


class MayChuTam:
    """Máy chủ thật, dựng y như web.main() nhưng cổng để hệ điều hành chọn.

       Dùng:
           with MayChuTam(duong_dan_cauhinh) as (k, dia_chi):
               ma, than = k.get('/api/quy-tac')
    """

    MAT_KHAU = 'matkhau-thu-that-dai'
    TEN = 'khcbcddl'

    def __init__(self, duong_dan_cauhinh, may_chu=None, tai_khoan=True,
                 dang_nhap=True):
        self.dd = duong_dan_cauhinh
        self.may_chu = may_chu          # đường dẫn cauhinh_may_chu.json, hoặc None
        # tai_khoan: True = dựng một tài khoản tạm; False = KHÔNG có tài khoản
        # nào (để thử nhánh máy-chủ-chưa-cài-xong); hoặc một đường dẫn sẵn.
        self.tai_khoan = tai_khoan
        self.dang_nhap = dang_nhap

    def __enter__(self):
        web.DUONG_DAN_CAUHINH = os.path.abspath(self.dd)
        web.xoa_sach_phien()
        web.dat_lai_trang_thai()
        # LUÔN nạp lại, kể cả khi không truyền gì: nap_cau_hinh_may_chu() tự
        # đặt hai danh sách về None trước. Thiếu dòng này thì danh sách của ca
        # trước còn sót lại, và kết quả ca sau phụ thuộc THỨ TỰ chạy — đỏ oan,
        # hoặc tệ hơn là xanh giả.
        self.ghi_chu = web.nap_cau_hinh_may_chu(self.may_chu or os.path.join(
            os.path.dirname(os.path.abspath(self.dd)), 'khong-co-tep-nay.json'))[2]
        thu_muc = os.path.dirname(os.path.abspath(self.dd))
        if self.tai_khoan is True:
            dd_tk = os.path.join(thu_muc, 'tai_khoan.json')
            if not os.path.exists(dd_tk):
                TK.ghi(dd_tk, [TK.ban_ghi_moi(self.TEN, self.MAT_KHAU)])
        elif self.tai_khoan is False:
            dd_tk = os.path.join(thu_muc, 'khong-co-tai-khoan.json')
        else:
            dd_tk = self.tai_khoan
        web.nap_tai_khoan_may_chu(dd_tk)

        self.may = ThreadingHTTPServer(('127.0.0.1', 0), web.May)
        self.may.daemon_threads = True
        self.luong = threading.Thread(target=self.may.serve_forever, daemon=True)
        self.luong.start()
        self.dia, self.cong = self.may.server_address
        k = Khach(self.cong)
        if self.dang_nhap and self.tai_khoan is not False:
            # Đăng nhập QUA HTTP THẬT, rồi KHẲNG ĐỊNH là nó thành công. Trả ra
            # một Khach chưa đăng nhập mà im lặng thì mọi ca thử cũ vẫn xanh
            # trong khi cổng đăng nhập hỏng hoàn toàn — đúng bẫy xanh giả.
            ma, _ = k.post('/api/dang-nhap',
                           {'ten': self.TEN, 'mat_khau': self.MAT_KHAU})
            if ma != 200 or not k.cookie:
                raise RuntimeError(
                    f'MayChuTam: đăng nhập tự động THẤT BẠI (mã {ma}, '
                    f'cookie {k.cookie})')
        return k, (self.dia, self.cong)

    def __exit__(self, *a):
        self.may.shutdown()
        self.may.server_close()
        return False


class Khach:
    """Khách HTTP tự viết bằng socket trần.

       Cố ý KHÔNG dùng urllib: ca thử an ninh cần gửi được những yêu cầu mà
       urllib không cho gửi — thiếu Content-Length, Content-Length nói dối,
       Transfer-Encoding: chunked, Content-Type lạ, Origin của trang khác.
       Có socket trần rồi thì mọi ca đều gửi bằng một đường, khỏi hai lối.
    """

    def __init__(self, cong, host='127.0.0.1'):
        self.cong = cong
        self.host = host
        self.cookie = {}

    # ---------------- lõi ----------------
    def tho(self, tho_bytes, doc_het=True, cho=15):
        """Gửi đúng chuỗi byte này, trả về (ma, tieu_de, than)."""
        s = socket.create_connection((self.host, self.cong), timeout=cho)
        self.gay_khi_gui = False
        try:
            try:
                s.sendall(tho_bytes)
            except (BrokenPipeError, ConnectionResetError):
                # Máy chủ đã trả lời và đóng trước khi ta gửi xong — chuyện
                # BÌNH THƯỜNG khi thân vượt trần (nó cố ý không nuốt hết).
                # Vẫn đọc tiếp: phản hồi có thể đã nằm sẵn trong bộ đệm nhận.
                self.gay_khi_gui = True
            goi = b''
            while True:
                try:
                    m = s.recv(65536)
                except socket.timeout:
                    break
                if not m:
                    break
                goi += m
                if not doc_het and b'\r\n\r\n' in goi:
                    break
        finally:
            s.close()
        if b'\r\n\r\n' not in goi:
            return None, {}, goi
        dau, than = goi.split(b'\r\n\r\n', 1)
        dong = dau.decode('utf-8', 'replace').split('\r\n')
        ma = int(dong[0].split()[1]) if len(dong[0].split()) > 1 else None
        td = {}
        for d in dong[1:]:
            if ':' in d:
                k, v = d.split(':', 1)
                td.setdefault(k.strip().lower(), []).append(v.strip())
        for v in td.get('set-cookie', []):
            c = v.split(';')[0]
            if '=' in c:
                k, gt = c.split('=', 1)
                self.cookie[k.strip()] = gt.strip()
        return ma, td, than

    def yeu_cau(self, cach, duong, than=None, kieu='application/json',
                them=None, cookie=True, doc_het=True):
        """Yêu cầu bình thường, có thể chèn thêm tiêu đề tuỳ ý."""
        if isinstance(than, (dict, list)):
            than = json.dumps(than, ensure_ascii=False).encode()
        elif isinstance(than, str):
            than = than.encode()
        them = dict(them or {})
        # cho phép ca thử tự đặt Host (ca DNS rebinding) — đừng gửi hai dòng Host
        host = them.pop('Host', f'{self.host}:{self.cong}')
        d = [f'{cach} {duong} HTTP/1.1', f'Host: {host}', 'Connection: close']
        if than is not None:
            d.append(f'Content-Length: {len(than)}')
            if kieu:
                d.append(f'Content-Type: {kieu}')
        if cookie and self.cookie:
            d.append('Cookie: ' + '; '.join(f'{k}={v}'
                                            for k, v in self.cookie.items()))
        for k, v in (them or {}).items():
            d.append(f'{k}: {v}')
        goi = ('\r\n'.join(d) + '\r\n\r\n').encode() + (than or b'')
        return self.tho(goi, doc_het=doc_het)

    # ---------------- tiện ----------------
    def get(self, duong, **kw):
        ma, _, than = self.yeu_cau('GET', duong, **kw)
        return ma, than.decode('utf-8', 'replace')

    def get_nhi_phan(self, duong, **kw):
        ma, _, than = self.yeu_cau('GET', duong, **kw)
        return ma, than

    def post(self, duong, than=None, **kw):
        ma, _, t = self.yeu_cau('POST', duong, than, **kw)
        return ma, t.decode('utf-8', 'replace')

    def post_td(self, duong, than=None, **kw):
        """Như post() nhưng trả cả tiêu đề."""
        ma, td, t = self.yeu_cau('POST', duong, than, **kw)
        return ma, td, t.decode('utf-8', 'replace')

    def js(self, duong, than=None, **kw):
        """Không có thân thì GET, có thân thì POST; tự đọc JSON.
           Trả (ma, đối tượng) — không đọc được JSON thì đối tượng là None."""
        ma, t = (self.get(duong, **kw) if than is None
                 else self.post(duong, than, **kw))
        try:
            return ma, json.loads(t)
        except ValueError:
            return ma, None

    def dong_cookie(self):
        """Dòng 'Cookie: …' của jar hiện tại, hoặc None."""
        if not self.cookie:
            return None
        return ('Cookie', '; '.join(f'{k}={v}' for k, v in self.cookie.items()))

    def tho_dong(self, cach, duong, dong, than=None, doc_het=True):
        """Gửi yêu cầu với DANH SÁCH dòng tiêu đề, cho phép TRÙNG TÊN.

           yeu_cau() nhận `them` là dict nên không thể gửi hai dòng "Host" hay
           hai dòng "Content-Length" — mà đó đúng là thứ cần thử. Hàm này nhận
           danh sách cặp (tên, giá trị) nên gửi được bao nhiêu dòng tuỳ ý, kể cả
           trùng tên. Người gọi tự lo mọi dòng, kể cả Host.
        """
        if isinstance(than, (dict, list)):
            than = json.dumps(than, ensure_ascii=False).encode()
        elif isinstance(than, str):
            than = than.encode()
        d = [f'{cach} {duong} HTTP/1.1']
        # Tự thêm Cookie nếu người gọi chưa tự đặt: từ 2A-1 mọi đường nghiệp vụ
        # đều đòi đăng nhập, mà các ca thử dị dạng vẫn cần đi tới ĐÚNG chỗ kiểm
        # của mình (400/413) chứ không dừng sớm ở 401.
        dong = list(dong)
        if not any(k.lower() == 'cookie' for k, _ in dong):
            c = self.dong_cookie()
            if c:
                dong.append(c)
        d += [f'{k}: {v}' for k, v in dong]
        goi = ('\r\n'.join(d) + '\r\n\r\n').encode() + (than or b'')
        return self.tho(goi, doc_het=doc_het)

    def dang_nhap(self, ten=None, mat_khau=None, **kw):
        """Đăng nhập QUA HTTP THẬT rồi khẳng định là thành công.

           Trả về mã phiên mới. Im lặng nuốt lỗi ở đây là để mọi ca thử sau đó
           xanh giả trong khi cổng đăng nhập hỏng.
        """
        ma, t = self.post('/api/dang-nhap',
                          {'ten': ten or MayChuTam.TEN,
                           'mat_khau': mat_khau or MayChuTam.MAT_KHAU}, **kw)
        if ma != 200:
            raise RuntimeError(f'Khach.dang_nhap THẤT BẠI: mã {ma} — {t[:90]}')
        return self.ma_phien()

    def ma_phien(self):
        """Mã phiên đang giữ, dù cookie mang tên nào."""
        for ten in (web.TEN_COOKIE, web.TEN_COOKIE_BM):
            if self.cookie.get(ten):
                return self.cookie[ten]
        return None

    # ---------------- yêu cầu DỊ DẠNG (dành cho ca thử an ninh) ----------------
    def chunked(self, duong, than, kieu='application/json'):
        """POST bằng Transfer-Encoding: chunked, KHÔNG có Content-Length."""
        if isinstance(than, (dict, list)):
            than = json.dumps(than, ensure_ascii=False).encode()
        elif isinstance(than, str):
            than = than.encode()
        c = self.dong_cookie()
        them_c = f'{c[0]}: {c[1]}\r\n' if c else ''
        goi = (f'POST {duong} HTTP/1.1\r\nHost: {self.host}:{self.cong}\r\n'
               f'Content-Type: {kieu}\r\nTransfer-Encoding: chunked\r\n'
               f'{them_c}Connection: close\r\n\r\n').encode()
        goi += hex(len(than))[2:].encode() + b'\r\n' + than + b'\r\n0\r\n\r\n'
        ma, _, t = self.tho(goi)
        return ma, t.decode('utf-8', 'replace')

    def khong_do_dai(self, duong, than=b''):
        """POST không có Content-Length và cũng không chunked."""
        c = self.dong_cookie()
        them_c = f'{c[0]}: {c[1]}\r\n' if c else ''
        goi = (f'POST {duong} HTTP/1.1\r\nHost: {self.host}:{self.cong}\r\n'
               f'Content-Type: application/json\r\n'
               f'{them_c}Connection: close\r\n\r\n').encode() + than
        ma, _, t = self.tho(goi)
        return ma, t.decode('utf-8', 'replace')


def doc_o_excel(duong_dan, sheet='Khối 12', vung=(8, 33, 4, 10)):
    """Đọc vùng ô của sheet, trả dict {(hàng, cột): giá trị}."""
    import openpyxl
    ws = openpyxl.load_workbook(duong_dan)[sheet]
    r1, r2, c1, c2 = vung
    return {(r, c): ws.cell(r, c).value
            for r in range(r1, r2) for c in range(c1, c2)}


def doi_trang_thai(k, cho=400):
    """Hỏi /api/trang-thai tới lúc HẾT CHẠY. Trả về trạng thái cuối.

       Đợi 'dang_chay' về False chứ không đợi cờ 'xong': lúc chưa chạy lần
       nào thì 'xong' vẫn là False, đợi nó sẽ treo hết thời gian cho phép."""
    import time
    t = {}
    for _ in range(cho):
        ma, t = k.js('/api/trang-thai?tu=0')
        if t and not t.get('dang_chay'):
            return t
        time.sleep(0.1)
    return t

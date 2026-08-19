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

    def __init__(self, duong_dan_cauhinh):
        self.dd = duong_dan_cauhinh

    def __enter__(self):
        web.DUONG_DAN_CAUHINH = os.path.abspath(self.dd)
        web.PHIEN['them'].clear()
        web.dat_lai_trang_thai()
        self.may = ThreadingHTTPServer(('127.0.0.1', 0), web.May)
        self.may.daemon_threads = True
        self.luong = threading.Thread(target=self.may.serve_forever, daemon=True)
        self.luong.start()
        self.dia, self.cong = self.may.server_address
        return Khach(self.cong), (self.dia, self.cong)

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
        try:
            s.sendall(tho_bytes)
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

    # ---------------- yêu cầu DỊ DẠNG (dành cho ca thử an ninh) ----------------
    def chunked(self, duong, than, kieu='application/json'):
        """POST bằng Transfer-Encoding: chunked, KHÔNG có Content-Length."""
        if isinstance(than, (dict, list)):
            than = json.dumps(than, ensure_ascii=False).encode()
        elif isinstance(than, str):
            than = than.encode()
        goi = (f'POST {duong} HTTP/1.1\r\nHost: {self.host}:{self.cong}\r\n'
               f'Content-Type: {kieu}\r\nTransfer-Encoding: chunked\r\n'
               f'Connection: close\r\n\r\n').encode()
        goi += hex(len(than))[2:].encode() + b'\r\n' + than + b'\r\n0\r\n\r\n'
        ma, _, t = self.tho(goi)
        return ma, t.decode('utf-8', 'replace')

    def khong_do_dai(self, duong, than=b''):
        """POST không có Content-Length và cũng không chunked."""
        goi = (f'POST {duong} HTTP/1.1\r\nHost: {self.host}:{self.cong}\r\n'
               f'Content-Type: application/json\r\n'
               f'Connection: close\r\n\r\n').encode() + than
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

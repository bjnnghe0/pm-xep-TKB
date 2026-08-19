#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ AN NINH GIAO DIỆN WEB
--------------------------------------------------------------------------
 Chạy:  python tests/thu_an_ninh.py

 Bảy lỗi tìm được khi rà soát web.py trước lúc thêm đăng nhập. Tất cả đều
 HỎNG NGAY hôm nay khi chạy cục bộ, không đợi tới lúc mở ra Internet.

   A2  Gửi thân kiểu chunked -> máy chủ coi là RỖNG -> /api/luu-quy-tac
       hiểu thành "không tắt quy tắc nào" -> bật lại hết rồi ghi đè
       cauhinh.json, vẫn báo 200. Mất dữ liệu trong im lặng.
   A1  Không kiểm Content-Type / Origin / Host -> trang web bất kỳ mà thầy
       cô mở đều sai khiến được máy chủ ghi đè cauhinh.json.
   A7  Chỉ một khe sao lưu -> bấm Lưu lần thứ hai là đè mất bản gốc.
   --  Ghi cauhinh.json không nguyên tử: open('w') cắt cụt tệp TRƯỚC khi
       biết có dựng nổi chuỗi JSON hay không.
   A4  Khoá "một lượt" của /api/xep đọc cờ rồi mới đặt cờ ở hai lần khoá
       khác nhau -> nhiều lượt cùng chạy, cùng ghi một tệp Excel.
   A3  Lỗi bất ngờ trả nguyên traceback ra trình duyệt, kèm đường dẫn
       tuyệt đối và tên đăng nhập máy.
   A8  Chuỗi bắt đầu bằng '=' ghi vào ô Excel thành CÔNG THỨC. Văn thư mở
       tệp, Excel hỏi cho phép liên kết ngoài, bấm Có là chạy lệnh.

 Mọi ca đi qua HTTP thật, trong thư mục tạm, không đụng cauhinh.json thật.
==========================================================================
"""
import io
import json
import os
import sys
import tempfile
import threading

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import (GOC_TM, MayChuTam, Khach, cau_hinh_tam,   # noqa: E402
                          doi_trang_thai)
import xep_tkb as X          # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def so_tat(dd):
    """Danh sách chỉ số quy tắc đang bị tắt trong tệp cấu hình.
       Tệp chưa có thì trả None — để ca thử báo ĐỎ chứ không vỡ giữa chừng."""
    cfg = doc_an_toan(dd)
    if cfg is None:
        return None
    return [i for i, r in enumerate(cfg['quy_tac']) if r.get('bat') is False]


def doc_an_toan(dd):
    """Đọc cấu hình, không có hoặc hỏng thì trả None thay vì ném."""
    try:
        return X.doc_cau_hinh(dd)
    except BaseException:
        return None


# ==========================================================================
def ca_a2_than_di_dang(tm):
    print('\nCA A2 — thân yêu cầu dị dạng KHÔNG được coi là thân rỗng')
    print('-' * 74)
    tmx = os.path.join(tm, 'a2')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    with MayChuTam(dd) as (k, _):
        # dựng trạng thái: tắt 10 quy tắc rồi lưu xuống tệp
        k.js('/api/luu-quy-tac', {'tat': list(range(10))})
        kiem(so_tat(dd) == list(range(10)),
             f'Dựng sẵn trạng thái: 10 quy tắc bị tắt — {so_tat(dd)}')

        # 1. Transfer-Encoding: chunked, KHÔNG có Content-Length
        ma, than = k.chunked('/api/luu-quy-tac', {'tat': list(range(10))})
        kiem(ma == 400,
             f'Gửi chunked bị TỪ CHỐI bằng 400 — máy chủ trả {ma}')
        kiem(so_tat(dd) == list(range(10)),
             f'Tệp cấu hình KHÔNG bị đổi sau yêu cầu chunked — {so_tat(dd)}')

        # 2. POST không có Content-Length và cũng không chunked
        ma, than = k.khong_do_dai('/api/luu-quy-tac', b'{"tat":[]}')
        kiem(ma == 400,
             f'Gửi thiếu Content-Length bị TỪ CHỐI bằng 400 — {ma}')
        kiem(so_tat(dd) == list(range(10)),
             f'Tệp cấu hình vẫn KHÔNG bị đổi — {so_tat(dd)}')

        # 3. Content-Length không phải số
        ma, than = k.yeu_cau('POST', '/api/luu-quy-tac', b'{"tat":[]}')[0], None
        ma2, _, t2 = k.yeu_cau('POST', '/api/luu-quy-tac', None,
                               them={'Content-Length': 'abc'})
        kiem(ma2 == 400, f'Content-Length không phải số -> 400 — {ma2}')
        kiem('Traceback' not in t2.decode('utf-8', 'replace'),
             'Và không kèm traceback')

        # 4. thân rỗng hẳn cũng phải bị từ chối ở đường GHI TỆP
        ma, _ = k.post('/api/luu-quy-tac', b'')
        kiem(ma == 400, f'Thân rỗng ở đường ghi tệp -> 400 — {ma}')

        # 5. đường ghi tệp phải đòi đúng khoá "tat"
        ma, _ = k.js('/api/luu-quy-tac', {'khong_phai_tat': [1]})
        kiem(ma == 400, f'Thiếu khoá "tat" -> 400 — {ma}')

        # 6. yêu cầu ĐÚNG vẫn phải chạy được như cũ
        ma, kq = k.js('/api/luu-quy-tac', {'tat': [3]})
        kiem(ma == 200 and so_tat(dd) == [3],
             f'Yêu cầu đúng vẫn lưu được bình thường — {ma}, {so_tat(dd)}')


# ==========================================================================
def ca_a1_nguon_goc(tm):
    print('\nCA A1 — chỉ nhận yêu cầu từ chính trang này')
    print('-' * 74)
    tmx = os.path.join(tm, 'a1')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    with MayChuTam(dd) as (k, (dia, cong)):
        k.js('/api/luu-quy-tac', {'tat': [1, 2]})
        goc = so_tat(dd)
        kiem(goc == [1, 2], f'Dựng sẵn trạng thái: quy tắc {goc} bị tắt')

        # --- Content-Type: ba kiểu "simple request" phải bị chặn hết ---
        for kieu in ('text/plain', 'application/x-www-form-urlencoded',
                     'multipart/form-data; boundary=x'):
            ma, _ = k.post('/api/luu-quy-tac', {'tat': []}, kieu=kieu)
            kiem(ma == 400, f'Content-Type {kieu.split(";")[0]} bị chặn — {ma}')
            kiem(so_tat(dd) == goc, f'  tệp không đổi sau khi bị chặn')

        ma, _ = k.post('/api/luu-quy-tac', {'tat': []}, kieu=None)
        kiem(ma == 400, f'Không khai Content-Type cũng bị chặn — {ma}')

        # --- Origin của trang khác phải bị chặn ---
        for org in ('https://trang-quang-cao.example', 'http://127.0.0.1:1',
                    'null'):
            ma, _ = k.post('/api/luu-quy-tac', {'tat': []},
                           them={'Origin': org})
            kiem(ma == 400, f'Origin lạ {org[:32]} bị chặn — {ma}')
            kiem(so_tat(dd) == goc, '  tệp không đổi sau khi bị chặn')

        # --- Host lạ (DNS rebinding) phải bị chặn, cả GET ---
        for h in ('trang-la.example', 'trang-la.example:%d' % cong):
            ma, _ = k.get('/api/gia-tri', them={'Host': h})
            kiem(ma == 400, f'Host lạ "{h}" bị chặn ở GET — {ma}')
        ma, _ = k.post('/api/luu-quy-tac', {'tat': []},
                       them={'Host': 'trang-la.example'})
        kiem(ma == 400 and so_tat(dd) == goc, 'Host lạ bị chặn ở POST')

        # --- những thứ ĐÚNG vẫn phải chạy được ---
        ma, _ = k.post('/api/luu-quy-tac', {'tat': [4]},
                       kieu='application/json; charset=utf-8')
        kiem(ma == 200 and so_tat(dd) == [4],
             f'Content-Type có charset vẫn nhận — {ma}, {so_tat(dd)}')
        ma, _ = k.post('/api/luu-quy-tac', {'tat': [5]},
                       them={'Origin': f'http://127.0.0.1:{cong}'})
        kiem(ma == 200 and so_tat(dd) == [5],
             f'Origin của chính trang này vẫn nhận — {ma}')
        ma, _ = k.post('/api/luu-quy-tac', {'tat': [6]},
                       them={'Host': f'localhost:{cong}',
                             'Origin': f'http://localhost:{cong}'})
        kiem(ma == 200 and so_tat(dd) == [6],
             f'Vào bằng localhost vẫn dùng được — {ma}')
        kiem(k.get('/')[0] == 200, 'GET / bình thường vẫn 200')
        kiem(k.get('/api/gia-tri')[0] == 200, 'GET /api/gia-tri vẫn 200')
        ma, _ = k.get('/api/tai-ve')
        kiem(ma in (200, 404),
             f'Đường tải tệp (điều hướng cả trang, không có Origin) vẫn qua — {ma}')


# ==========================================================================
def ca_a7_sao_luu_xoay_vong(tm):
    print('\nCA A7 — sao lưu xoay vòng, và ghi cauhinh.json phải NGUYÊN TỬ')
    print('-' * 74)
    tmx = os.path.join(tm, 'a7')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)
    goc = X.doc_cau_hinh(dd)

    def bak(ten):
        return os.path.join(tmx, ten)

    with MayChuTam(dd) as (k, _):
        for lan, t in enumerate([[1], [2], [3], [4]], start=1):
            ma, _kq = k.js('/api/luu-quy-tac', {'tat': t})
            kiem(ma == 200, f'Lưu lần {lan} (tắt quy tắc {t}) — {ma}')

        # 1. bản GỐC phải còn nguyên sau 4 lần lưu
        kiem(os.path.exists(bak('cauhinh.bak.goc.json')),
             'Có bản gốc cauhinh.bak.goc.json')
        kiem(doc_an_toan(bak('cauhinh.bak.goc.json')) == goc,
             'Bản gốc SAU 4 LẦN LƯU vẫn đúng là nội dung ban đầu')

        # 2. các bản xoay vòng phải giữ đúng thứ tự lùi dần
        kiem(so_tat(bak('cauhinh.bak.json')) == [3],
             f'cauhinh.bak.json = ngay trước lần lưu cuối — '
             f'{so_tat(bak("cauhinh.bak.json"))}')
        kiem(so_tat(bak('cauhinh.bak.1.json')) == [2],
             f'cauhinh.bak.1.json lùi thêm một bậc — '
             f'{so_tat(bak("cauhinh.bak.1.json"))}')
        kiem(so_tat(bak('cauhinh.bak.2.json')) == [1],
             f'cauhinh.bak.2.json lùi thêm bậc nữa — '
             f'{so_tat(bak("cauhinh.bak.2.json"))}')
        kiem(so_tat(dd) == [4], f'Tệp thật đang ở trạng thái mới nhất — {so_tat(dd)}')

        # 3. NGUYÊN TỬ: dựng chuỗi JSON hỏng thì tệp thật phải Y NGUYÊN
        import web as W
        truoc = io.open(dd, encoding='utf-8').read()
        that = W._gon_json

        def hong(cfg):
            raise RuntimeError('cố ý làm hỏng lúc dựng chuỗi JSON')
        W._gon_json = hong
        try:
            ma, _ = k.js('/api/luu-quy-tac', {'tat': [0]})
        finally:
            W._gon_json = that
        sau = io.open(dd, encoding='utf-8').read()
        kiem(ma == 500, f'Dựng chuỗi hỏng thì báo lỗi — {ma}')
        kiem(sau == truoc,
             f'cauhinh.json KHÔNG bị cắt cụt, còn nguyên {len(sau)} byte '
             f'(trước {len(truoc)})')
        kiem(len(sau) > 1000 and doc_an_toan(dd) is not None,
             'Và vẫn đọc được như một tệp JSON hợp lệ')

        # 4. hai người bấm Lưu cùng lúc: tệp phải luôn đọc được
        loi = []

        def ban(i):
            try:
                k2 = Khach(k.cong)
                k2.js('/api/luu-quy-tac', {'tat': [i]})
            except Exception as e:          # pragma: no cover
                loi.append(repr(e))
        ts = [threading.Thread(target=ban, args=(i,)) for i in range(6)]
        for t in ts:
            t.start()
        for t in ts:
            t.join()
        kiem(not loi, f'6 người bấm Lưu cùng lúc, không ai lỗi — {loi[:1]}')
        cuoi = doc_an_toan(dd)
        kiem(cuoi is not None,
             'Sau khi 6 người lưu đồng thời, tệp vẫn đọc được')
        kiem(cuoi and len(cuoi.get('quy_tac', [])) == len(goc['quy_tac']),
             'Và không mất quy tắc nào')


# ==========================================================================
def chay_het(tm):
    ca_a2_than_di_dang(tm)
    ca_a1_nguon_goc(tm)
    ca_a7_sao_luu_xoay_vong(tm)


if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ AN NINH GIAO DIỆN WEB')
    print('=' * 74)
    with tempfile.TemporaryDirectory() as tm:
        chay_het(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

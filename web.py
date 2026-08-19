#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 GIAO DIỆN WEB CHO PHẦN MỀM XẾP THỜI KHÓA BIỂU
--------------------------------------------------------------------------
 Chạy:
     python web.py                 rồi mở http://127.0.0.1:20266
     python web.py --port 8080     đổi cổng
     python web.py --cauhinh khac.json

 Tắt: bấm Ctrl+C ở cửa sổ dòng lệnh, hoặc đóng cửa sổ đó.

 CHỈ CHẠY CỤC BỘ trên chính máy này (bind 127.0.0.1), máy khác trong
 mạng KHÔNG vào được. Không dùng thư viện ngoài, không tải gì từ mạng.

 File này chỉ gọi vào xep_tkb.py và quy_tac.py, không sửa gì trong đó.
==========================================================================
"""
import argparse
import copy
import json
import os
import re
import shutil
import threading
import time
import traceback
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import quy_tac as QT
import xep_tkb as X

THU_MUC = os.path.dirname(os.path.abspath(__file__))
THU_MUC_WEB = os.path.join(THU_MUC, 'web')
TINH = {'index.html': 'text/html', 'style.css': 'text/css',
        'app.js': 'application/javascript'}

DUONG_DAN_CAUHINH = os.path.join(THU_MUC, 'cauhinh.json')


def thu_muc_cauhinh():
    """File mẫu và file kết quả nằm cạnh cauhinh.json — y như xep_tkb.main()."""
    return os.path.dirname(os.path.abspath(DUONG_DAN_CAUHINH))


# ==========================================================================
# 1. TRẠNG THÁI DÙNG CHUNG GIỮA CÁC LUỒNG
# ==========================================================================

KHOA = threading.Lock()
TT = {}

# Quy tắc người dùng thêm ở màn hình Quy tắc — CHỈ nằm trong bộ nhớ của phiên
# này. Ghi xuống cauhinh.json vẫn chỉ qua nút "Lưu vào cauhinh.json".
PHIEN = {'them': []}


def dat_lai_trang_thai():
    with KHOA:
        TT.clear()
        TT.update({
            'dang_chay': False, 'xong': False, 'loi': None,
            'log': [], 'da_thu': 0, 'so_lan': 0, 'hop_le': 0,
            'con_giay': 0, 'bat_dau': 0,
            'bang': [], 'diem_mem': {}, 'diem': None, 'so_loi': 0,
            'luoi': None, 'gv': None, 'file_xuat': None, 'file_web': None,
        })


dat_lai_trang_thai()


def ghi(dong=''):
    """Ghi một dòng vào khung log — đúng những gì chương trình in ra."""
    with KHOA:
        TT['log'].append(dong)


def dat(**kw):
    with KHOA:
        TT.update(kw)


# ==========================================================================
# 2. LUỒNG XẾP THỜI KHÓA BIỂU
# ==========================================================================
#  Việc tìm phương án nằm ở X.tim_phuong_an() — CHUNG với xep_tkb.main(),
#  không chép lại dòng nào. Web chỉ truyền thêm hàm gọi lại để báo tiến
#  độ; dòng lệnh truyền None nên im lặng y như trước.
#  tests/thu_web.py vẫn so từng ô của file Excel giữa hai đường chạy.

def _chay(tuan, seed, so_lan, tat):
    try:
        cfg, _ = cau_hinh_phien()
        if tuan:
            cfg['thong_tin']['tuan'] = tuan
        for i in tat:                       # tắt quy tắc cho riêng lượt này
            if 0 <= i < len(cfg.get('quy_tac', [])):
                cfg['quy_tac'][i]['bat'] = False

        bt = X.BaiToan(cfg)

        goc = cfg.get('tim_kiem', {})
        tk = {'so_lan_thu': so_lan or goc.get('so_lan_thu', 300),
              'seed': seed if seed is not None else goc.get('seed', 0),
              'gioi_han_buoc': goc.get('gioi_han_buoc', 30000),
              'gioi_han_giay_moi_lan': goc.get('gioi_han_giay_moi_lan', 3.0),
              'gioi_han_tong_giay': goc.get('gioi_han_tong_giay', 60)}

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
            file_xuat=os.path.basename(fx), file_web=os.path.basename(fh))

    except SystemExit as e:
        # Khai báo sai trong cauhinh.json -> chương trình gốc gọi sys.exit.
        # Trong web thì phải bắt lại, nếu không máy chủ chết theo.
        ghi('')
        for d in str(e).split('\n'):
            ghi(d)
        dat(loi=str(e))
    except Exception:
        ghi('')
        ghi('[LỖI BẤT NGỜ] Chi tiết cho người viết phần mềm:')
        for d in traceback.format_exc().split('\n'):
            ghi(d)
        dat(loi='Lỗi bất ngờ, xem khung nhật ký.')
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

def cau_hinh_phien():
    """cauhinh.json + các quy tắc vừa thêm trong phiên. Không đụng file."""
    cfg = X.doc_cau_hinh(DUONG_DAN_CAUHINH)
    tu_file = [r for r in cfg.get('quy_tac', []) if isinstance(r, dict)]
    cfg['quy_tac'] = tu_file + [copy.deepcopy(r) for r in PHIEN['them']]
    return cfg, len(tu_file)


def doc_quy_tac():
    cfg, so_file = cau_hinh_phien()
    ds = []
    for i, r in enumerate(cfg['quy_tac']):
        ds.append({'i': i, 'loai': r.get('loai', '?'),
                   'ghi_chu': r.get('ghi_chu', ''),
                   'bat': bool(r.get('bat', True)),
                   'mem': str(r.get('loai', '')).startswith('uu_tien'),
                   'moi': i >= so_file,          # chưa lưu xuống file
                   'noi_dung': {k: v for k, v in r.items()
                                if k not in ('loai', 'ghi_chu', 'bat')}})
    return {'quy_tac': ds, 'so_file': so_file, 'so_moi': len(PHIEN['them']),
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


def them_quy_tac(r):
    """Dựng thử BaiToan trước khi nhận. Khai sai thì SystemExit bay lên trên
       và người gọi hiện nguyên văn ra trang."""
    if not isinstance(r, dict):
        raise SystemExit('[LỖI] Quy tắc phải là một khối { ... }')
    if not str(r.get('ghi_chu', '')).strip():
        raise SystemExit('[LỖI] Chưa điền "Nội dung quy tắc"\n'
                         '      Câu này hiện nguyên văn trên bảng đối chiếu '
                         'và trên sheet "Kiểm tra quy tắc", nên không được '
                         'để trống.')
    cfg, _ = cau_hinh_phien()
    cfg['quy_tac'].append(copy.deepcopy(r))
    X.BaiToan(cfg)                     # ném SystemExit nếu khai sai
    PHIEN['them'].append(copy.deepcopy(r))
    return doc_quy_tac()


def xoa_quy_tac(i):
    _, so_file = cau_hinh_phien()
    if i < so_file:
        raise SystemExit(
            '[LỖI] Chỉ xoá được quy tắc vừa thêm trong phiên này.\n'
            '      Quy tắc đã có trong cauhinh.json thì dùng công tắc để tắt, '
            'rồi bấm "Lưu vào cauhinh.json".')
    j = i - so_file
    if not 0 <= j < len(PHIEN['them']):
        raise SystemExit('[LỖI] Không có quy tắc thứ %d để xoá.' % i)
    PHIEN['them'].pop(j)
    return doc_quy_tac()


def thu_quy_tac(r, tat):
    """Xếp thử rút gọn để xem thêm quy tắc này còn xếp được không.
       Chạy thẳng trong luồng HTTP vì đã chặn cứng 30 lần thử / 8 giây —
       khác hẳn lượt xếp thật (~50 giây) nên không được làm như vậy ở /api/xep."""
    cfg, _ = cau_hinh_phien()
    if r:
        cfg['quy_tac'].append(copy.deepcopy(r))
    for i in tat:
        if 0 <= i < len(cfg['quy_tac']):
            cfg['quy_tac'][i]['bat'] = False
    bt = X.BaiToan(cfg)
    goc = cfg.get('tim_kiem', {})
    tk = {'so_lan_thu': 30, 'gioi_han_buoc': goc.get('gioi_han_buoc', 30000),
          'gioi_han_giay_moi_lan': 2, 'gioi_han_tong_giay': 8,
          'seed': goc.get('seed', 0)}
    kqt = X.tim_phuong_an(bt, tk)
    pa = kqt.tot or kqt.du_phong
    vi_pham = []
    if pa is not None:
        vi_pham = [{'ten': t, 'ghi_chu': c}
                   for kq, t, c in X.hau_kiem(bt, pa)[0] if kq == 'LỖI']
    return {'xep_duoc': kqt.tot is not None, 'co_loi_giai': pa is not None,
            'so_hop_le': kqt.so_hop_le, 'so_lan': kqt.da_thu,
            'giay': round(kqt.giay, 1), 'diem': kqt.diem,
            'vi_pham': vi_pham}


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


def luu_quy_tac(tat):
    """Ghi cờ bật/tắt vào cauhinh.json. Sao lưu trước, giữ nguyên thứ tự khoá."""
    cfg, so_file = cau_hinh_phien()                 # dict giữ thứ tự khoá
    n = len(PHIEN['them'])
    for i, r in enumerate(cfg['quy_tac']):
        muon_bat = i not in tat
        if i < so_file and bool(r.get('bat', True)) != muon_bat:
            n += 1
        if muon_bat:
            r.pop('bat', None)                        # bật = bỏ hẳn khoá "bat"
        else:
            r['bat'] = False
    sao_luu = os.path.join(thu_muc_cauhinh(), 'cauhinh.bak.json')
    shutil.copy(DUONG_DAN_CAUHINH, sao_luu)
    with open(DUONG_DAN_CAUHINH, 'w', encoding='utf-8') as f:
        f.write(_gon_json(cfg) + '\n')
    X.doc_cau_hinh(DUONG_DAN_CAUHINH)                 # đọc lại, hỏng thì báo ngay
    PHIEN['them'].clear()                             # đã nằm trong file rồi
    return {'doi': n, 'sao_luu': os.path.basename(sao_luu)}


# ==========================================================================
# 4. MÁY CHỦ HTTP
# ==========================================================================

class May(BaseHTTPRequestHandler):
    server_version = 'XepTKB'

    def log_message(self, *a):
        pass                                          # đừng làm bẩn màn hình

    # ---------------- tiện ích ----------------
    def _tra(self, ma, kieu, than):
        if isinstance(than, str):
            than = than.encode('utf-8')
        self.send_response(ma)
        self.send_header('Content-Type', f'{kieu}; charset=utf-8')
        self.send_header('Content-Length', str(len(than)))
        self.send_header('Cache-Control', 'no-store')
        self.end_headers()
        self.wfile.write(than)

    def _json(self, obj, ma=200):
        self._tra(ma, 'application/json',
                  json.dumps(obj, ensure_ascii=False))

    # ---------------- chỉ nhận yêu cầu phát từ CHÍNH TRANG NÀY ----------------
    def _ten_may_cho_phep(self):
        cong = self.server.server_address[1]
        return {f'127.0.0.1:{cong}', f'localhost:{cong}', f'[::1]:{cong}',
                '127.0.0.1', 'localhost'}

    def _nguon_cho_phep(self):
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
        host = (self.headers.get('Host') or '').strip().lower()
        if host not in self._ten_may_cho_phep():
            raise SystemExit(
                f'[LỖI] Yêu cầu gửi tới tên máy lạ: {host!r}\n'
                f'      Máy chủ này chỉ phục vụ 127.0.0.1 và localhost.\n'
                f'      Hãy mở bằng http://127.0.0.1:'
                f'{self.server.server_address[1]}')

        org = self.headers.get('Origin')
        if org is not None and org.strip().lower() not in self._nguon_cho_phep():
            raise SystemExit(
                f'[LỖI] Yêu cầu phát đi từ một trang khác: {org!r}\n'
                f'      Máy chủ chỉ nhận lệnh từ chính trang xếp thời khoá '
                f'biểu, không nhận từ trang web nào khác.')

        if co_than:
            kieu = (self.headers.get('Content-Type') or '')
            kieu = kieu.split(';')[0].strip().lower()
            if kieu != 'application/json':
                raise SystemExit(
                    f'[LỖI] Kiểu nội dung không nhận được: {kieu or "(trống)"}\n'
                    f'      Đường này chỉ nhận "application/json".')

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
        tho = self.headers.get('Content-Length')
        if tho is None or str(tho).strip() == '':
            if bat_buoc:
                raise SystemExit(
                    '[LỖI] Yêu cầu thiếu phần thân.\n'
                    '      Đường này ghi xuống tệp nên bắt buộc phải có thân.')
            return {}
        try:
            n = int(tho)
            if n < 0:
                raise ValueError
        except ValueError:
            raise SystemExit(f'[LỖI] "Content-Length" không phải số: {tho!r}')
        if n == 0:
            if bat_buoc:
                raise SystemExit(
                    '[LỖI] Yêu cầu thiếu phần thân.\n'
                    '      Đường này ghi xuống tệp nên bắt buộc phải có thân.')
            return {}
        try:
            d = json.loads(self.rfile.read(n).decode('utf-8'))
        except (ValueError, UnicodeDecodeError) as e:
            raise SystemExit(f'[LỖI] Thân yêu cầu không phải JSON hợp lệ: {e}')
        if not isinstance(d, dict):
            raise SystemExit('[LỖI] Thân yêu cầu phải là một khối { ... }')
        return d

    # ---------------- GET ----------------
    def do_GET(self):
        duong = self.path.split('?')[0]
        try:
            self._kiem_nguon_goc(co_than=False)
            if duong in ('/', '/index.html'):
                return self._tinh('index.html')
            if duong.startswith('/web/'):
                return self._tinh(duong[5:])
            if duong == '/api/trang-thai':
                return self._trang_thai()
            if duong == '/api/quy-tac':
                return self._json(doc_quy_tac())
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
            self._json({'loi': str(e)}, 400)
        except Exception:
            self._json({'loi': traceback.format_exc()}, 500)

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
                    tu = int(phan[3:] or 0)
        with KHOA:
            t = dict(TT)
            log = t.pop('log')
        t['log_moi'] = log[tu:]
        t['log_het'] = len(log)
        return self._json(t)

    def _tai_ve(self):
        ten = X.doc_cau_hinh(DUONG_DAN_CAUHINH)['thong_tin']['file_xuat']
        dd = os.path.join(thu_muc_cauhinh(), os.path.basename(ten))
        if not os.path.exists(dd):
            return self._tra(404, 'text/plain',
                             'Chưa có file kết quả. Hãy xếp thời khoá biểu trước.')
        with open(dd, 'rb') as f:
            than = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'application/vnd.openxmlformats-'
                                         'officedocument.spreadsheetml.sheet')
        self.send_header('Content-Disposition',
                         f'attachment; filename="{os.path.basename(dd)}"')
        self.send_header('Content-Length', str(len(than)))
        self.end_headers()
        self.wfile.write(than)

    def _tai_web(self):
        dd = os.path.join(thu_muc_cauhinh(), 'tkb_web.html')
        if not os.path.exists(dd):
            return self._tra(404, 'text/plain',
                             'Chưa có trang web. Hãy xếp thời khoá biểu trước.')
        with open(dd, 'rb') as f:
            than = f.read()
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self.send_header('Content-Disposition',
                         'attachment; filename="tkb_web.html"')
        self.send_header('Content-Length', str(len(than)))
        self.end_headers()
        self.wfile.write(than)

    # ---------------- POST ----------------
    def do_POST(self):
        duong = self.path.split('?')[0]
        try:
            self._kiem_nguon_goc(co_than=True)
            if duong == '/api/xep':
                return self._xep()
            if duong == '/api/luu-quy-tac':
                return self._luu()
            if duong == '/api/them-quy-tac':
                return self._json(them_quy_tac(
                    self._than_json(bat_buoc=True).get('quy_tac')))
            if duong == '/api/xoa-quy-tac':
                return self._json(xoa_quy_tac(self._chi_so()))
            if duong == '/api/thu-quy-tac':
                return self._thu()
            self._tra(404, 'text/plain', 'Không có trang này')
        except SystemExit as e:
            # Khai báo sai là lỗi của dữ liệu người dùng gửi lên -> 400,
            # không phải máy chủ hỏng.
            self._json({'loi': str(e)}, 400)
        except Exception:
            self._json({'loi': traceback.format_exc()}, 500)

    def _xep(self):
        with KHOA:
            if TT['dang_chay']:
                dang = True
            else:
                dang = False
        if dang:
            return self._json({'loi': 'Đang xếp, vui lòng đợi.'}, 409)

        d = self._than_json()
        tuan = (d.get('tuan') or '').strip() or None
        seed = d.get('seed')
        so_lan = d.get('so_lan')
        tat = [int(x) for x in d.get('tat', [])]
        seed = int(seed) if str(seed).strip() not in ('', 'None', 'null') else None
        so_lan = int(so_lan) if str(so_lan).strip() not in ('', 'None', 'null') else None

        dat_lai_trang_thai()
        dat(dang_chay=True)
        threading.Thread(target=_chay, args=(tuan, seed, so_lan, tat),
                         daemon=True).start()
        return self._json({'ok': True})

    def _thu(self):
        with KHOA:
            ban = TT['dang_chay']
        if ban:
            return self._json({'loi': 'Đang xếp, vui lòng đợi.'}, 409)
        d = self._than_json()
        tat = [int(x) for x in d.get('tat', [])]
        return self._json(thu_quy_tac(d.get('quy_tac'), tat))

    def _luu(self):
        d = self._than_json(bat_buoc=True)
        if 'tat' not in d:
            raise SystemExit(
                '[LỖI] Yêu cầu lưu thiếu danh sách "tat".\n'
                '      Không có danh sách này thì không biết quy tắc nào bị '
                'tắt — ghi bừa xuống tệp là bật lại hết.')
        return self._json(luu_quy_tac(_tap_chi_so(d['tat'])))

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
    args = ap.parse_args()
    DUONG_DAN_CAUHINH = os.path.abspath(args.cauhinh)

    dia_chi = ('127.0.0.1', args.port)                # CHỈ máy này, không mở ra mạng
    may = ThreadingHTTPServer(dia_chi, May)
    may.daemon_threads = True
    print('=' * 70)
    print(' XẾP THỜI KHÓA BIỂU — GIAO DIỆN WEB'.center(70))
    print('=' * 70)
    print(f'  Mở trình duyệt vào:  http://127.0.0.1:{args.port}')
    print(f'  Cấu hình đang dùng:  {DUONG_DAN_CAUHINH}')
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

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


def dat_lai_trang_thai():
    with KHOA:
        TT.clear()
        TT.update({
            'dang_chay': False, 'xong': False, 'loi': None,
            'log': [], 'da_thu': 0, 'so_lan': 0, 'hop_le': 0,
            'con_giay': 0, 'bat_dau': 0,
            'bang': [], 'diem_mem': {}, 'diem': None, 'so_loi': 0,
            'luoi': None, 'gv': None, 'file_xuat': None,
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
        cfg = X.doc_cau_hinh(DUONG_DAN_CAUHINH)
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
        ghi('')
        ghi(f'Đã xuất file: {fx}')

        dat(bang=[{'kq': a, 'ten': b, 'ghi_chu': c} for a, b, c in bc],
            diem_mem=dict(ct), diem=diem_tot, so_loi=so_loi,
            luoi=luoi_tkb(bt, tot, cfg), gv=lich_gv(bt),
            file_xuat=os.path.basename(fx))

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

def doc_quy_tac():
    cfg = X.doc_cau_hinh(DUONG_DAN_CAUHINH)
    ds = []
    for i, r in enumerate(cfg.get('quy_tac', [])):
        if not isinstance(r, dict):
            continue
        ds.append({'i': i, 'loai': r.get('loai', '?'),
                   'ghi_chu': r.get('ghi_chu', ''),
                   'bat': bool(r.get('bat', True)),
                   'mem': str(r.get('loai', '')).startswith('uu_tien')})
    return {'quy_tac': ds, 'tuan': cfg['thong_tin']['tuan'],
            'tim_kiem': cfg.get('tim_kiem', {})}


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
    cfg = X.doc_cau_hinh(DUONG_DAN_CAUHINH)          # dict giữ thứ tự khoá
    n = 0
    for i, r in enumerate(cfg.get('quy_tac', [])):
        if not isinstance(r, dict):
            continue
        muon_bat = i not in tat
        if bool(r.get('bat', True)) != muon_bat:
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

    def _than_json(self):
        n = int(self.headers.get('Content-Length') or 0)
        if not n:
            return {}
        return json.loads(self.rfile.read(n).decode('utf-8'))

    # ---------------- GET ----------------
    def do_GET(self):
        duong = self.path.split('?')[0]
        try:
            if duong in ('/', '/index.html'):
                return self._tinh('index.html')
            if duong.startswith('/web/'):
                return self._tinh(duong[5:])
            if duong == '/api/trang-thai':
                return self._trang_thai()
            if duong == '/api/quy-tac':
                return self._json(doc_quy_tac())
            if duong == '/api/tai-ve':
                return self._tai_ve()
            self._tra(404, 'text/plain', 'Không có trang này')
        except SystemExit as e:
            self._json({'loi': str(e)}, 500)
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

    # ---------------- POST ----------------
    def do_POST(self):
        duong = self.path.split('?')[0]
        try:
            if duong == '/api/xep':
                return self._xep()
            if duong == '/api/luu-quy-tac':
                return self._luu()
            self._tra(404, 'text/plain', 'Không có trang này')
        except SystemExit as e:
            self._json({'loi': str(e)}, 500)
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

    def _luu(self):
        d = self._than_json()
        tat = {int(x) for x in d.get('tat', [])}
        return self._json(luu_quy_tac(tat))


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

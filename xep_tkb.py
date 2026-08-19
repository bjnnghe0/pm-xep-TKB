#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 PHẦN MỀM XẾP THỜI KHÓA BIỂU  --  Khoa Khoa học Cơ bản
 Trường Cao đẳng Đà Lạt
--------------------------------------------------------------------------
 Cách dùng:
     python xep_tkb.py                     chạy với cauhinh.json
     python xep_tkb.py --quy-tac           xem danh mục quy tắc có thể dùng
     python xep_tkb.py --in-man-hinh       xem luôn TKB trên màn hình
     python xep_tkb.py --seed 99           ra một phương án khác
     python xep_tkb.py --xuat TKB_T3.xlsx  đổi tên file kết quả
     python xep_tkb.py --tuan "TUẦN 3"    đổi dòng chữ tuần in trên TKB

 Dữ liệu và quy tắc nằm hết trong cauhinh.json.
 Định nghĩa các loại quy tắc nằm trong quy_tac.py.
 File này chỉ lo phần giải bài toán và xuất Excel — hầu như không cần sửa.
==========================================================================
"""

import json
import time
import random
import argparse
import shutil
import sys
import os
from collections import defaultdict

import quy_tac as QT


# ==========================================================================
# 1. ĐỌC CẤU HÌNH
# ==========================================================================

def doc_cau_hinh(duong_dan):
    with open(duong_dan, encoding='utf-8') as f:
        return json.load(f)


def chuyen_doi_cau_hinh_cu(cfg):
    """Nhận cả file cấu hình kiểu cũ (mục "rang_buoc") lẫn kiểu mới
       (mục "quy_tac"). Kiểu cũ được dịch tự động sang kiểu mới."""
    ds = [r for r in cfg.get('quy_tac', []) if isinstance(r, dict)]

    rb = cfg.get('rang_buoc', {})
    for loai in ('chi_xep_thu', 'khong_xep_thu', 'chi_xep_tiet',
                 'khong_xep_tiet'):
        for r in rb.get(loai, []):
            moi = {'loai': loai, 'ghi_chu': r.get('_ghichu', ''), 'loc': {}}
            for k in ('mon', 'nhom_mon', 'gv', 'lop'):
                if k in r:
                    moi['loc'][k] = r[k]
            for k in ('thu', 'tiet', 'tiet_trong_buoi'):
                if k in r:
                    moi[k] = r[k]
            ds.append(moi)
    for r in rb.get('khac_ngay', []):
        ds.append({'loai': 'khac_ngay', 'ghi_chu': r.get('_ghichu', ''),
                   'a': r['a'], 'b': r['b']})

    lc = rb.get('luat_chung', {})
    if lc.get('shcn_tiet_cuoi'):
        ds.append({'loai': 'chi_xep_tiet',
                   'ghi_chu': 'SHCN luôn ở tiết cuối buổi',
                   'loc': {'nhom_mon': 'SHCN'},
                   'tiet_trong_buoi': [len(cfg['khung_gio']['cac_tiet'])]})

    ut = cfg.get('uu_tien', {})
    if ut.get('chuyen_de_ke_tiet_chinh'):
        ds.append({'loai': 'uu_tien_ke_nhau',
                   'ghi_chu': 'Nên xếp chuyên đề nối tiếp tiết chính',
                   'a': {'la_chuyen_de': True}, 'b': {'la_chuyen_de': False},
                   'cung_nhom_mon': True,
                   'diem': ut['chuyen_de_ke_tiet_chinh']})
    if ut.get('giam_so_ngay_den_truong_cua_gv'):
        ds.append({'loai': 'uu_tien_it_buoi',
                   'ghi_chu': 'Dồn buổi để giáo viên ít phải lên lớp',
                   'loc': {}, 'diem': ut['giam_so_ngay_den_truong_cua_gv']})
    if ut.get('trai_deu_mon_trong_tuan'):
        ds.append({'loai': 'uu_tien_trai_deu',
                   'ghi_chu': 'Các buổi cùng một môn nên cách nhau ≥ 2 ngày',
                   'loc': {}, 'cach': 2, 'diem': ut['trai_deu_mon_trong_tuan']})

    return [r for r in ds if r.get('bat', True)]


# ==========================================================================
# 2. MÔ HÌNH DỮ LIỆU
# ==========================================================================

class Cum:
    """Một 'cụm tiết': nhóm tiết liên tiếp của cùng 1 môn, 1 GV, 1 lớp."""

    __slots__ = ('ma', 'lop', 'mon', 'nhom', 'gv', 'size', 'la_cd', 'la_trong',
                 'ngay_ok', 'vitri_ok', 'o_cam', 'ngay', 'vitri', 'qt', 'qt_gy')

    def __init__(self, ma, lop, mon, nhom, gv, size,
                 la_cd=False, la_trong=False):
        self.ma = ma
        self.lop = lop
        self.mon = mon
        self.nhom = nhom
        self.gv = gv
        self.size = size
        self.la_cd = la_cd
        self.la_trong = la_trong
        self.ngay_ok = set()
        self.vitri_ok = set()
        self.o_cam = set()
        self.ngay = None
        self.vitri = None
        self.qt = []          # quy tắc cần kiểm tra trong lúc giải
        self.qt_gy = []       # quy tắc có gợi ý thứ tự thử ô

    def nhan(self):
        return '' if self.la_trong else f'{self.mon} ({self.gv})'

    def __repr__(self):
        return f'<{self.lop} {self.mon} {self.gv} x{self.size}>'


def chia_cum(so_tiet, mau_cum):
    cum, con = [], so_tiet
    for k in mau_cum:
        if con <= 0:
            break
        cum.append(min(k, con))
        con -= min(k, con)
    while con > 0:
        cum.append(1)
        con -= 1
    return cum


class BaiToan:

    def __init__(self, cfg):
        self.cfg = cfg
        kg = cfg['khung_gio']
        self.cac_thu = kg['cac_thu']
        self.cac_tiet = kg['cac_tiet']
        self.buoi = kg['buoi']
        self.SO_NGAY = len(self.cac_thu)
        self.SO_TIET = len(self.cac_tiet)
        self.thu2idx = {t: i for i, t in enumerate(self.cac_thu)}
        self.tiet2idx = {t: i for i, t in enumerate(self.cac_tiet)}

        self.lop = [l['ten'] for l in cfg['lop']]
        self.thong_tin_lop = {l['ten']: l for l in cfg['lop']}
        self.dinh_muc = cfg['dinh_muc_mon']
        self.luat = cfg.get('rang_buoc', {}).get('luat_chung', {})
        self.luat.update(cfg.get('luat_chung', {}))

        self.khai_bao_qt = chuyen_doi_cau_hinh_cu(cfg)
        self._tao_cum()
        self._tao_quy_tac()
        self._kiem_tra_so_bo()

    # ---------------- danh sách cụm ----------------
    def _map_gom_tiet(self):
        """Các quy tắc gom_tiet phải xử lý TRƯỚC khi cắt cụm."""
        ds = []
        for r in self.khai_bao_qt:
            if r.get('loai') == 'gom_tiet':
                ds.append((r.get('loc', {}), r['cum']))
        return ds

    def _cum_cua(self, lop, mon, gv, ghi_de):
        for loc, cum in ghi_de:
            def co(k, v):
                if k not in loc:
                    return True
                x = loc[k]
                return v in (x if isinstance(x, list) else [x])
            if (co('lop', lop) and co('mon', mon) and co('gv', gv)
                    and co('nhom_mon', self.dinh_muc[mon]['nhom'])):
                return cum
        return self.dinh_muc[mon]['cum']

    def _tao_cum(self):
        ghi_de = self._map_gom_tiet()
        self.cac_cum = []
        self.mong_doi = {}          # (lớp, môn) -> cách chia cụm thực tế
        ma = 0
        for lop in self.lop:
            tong = 0
            for mon, gv, st in self.cfg['phan_cong'][lop]:
                if mon not in self.dinh_muc:
                    raise SystemExit(f'[LỖI] Môn "{mon}" chưa khai báo trong '
                                     f'"dinh_muc_mon" (lớp {lop}).')
                dm = self.dinh_muc[mon]
                mau = chia_cum(st, self._cum_cua(lop, mon, gv, ghi_de))
                self.mong_doi[(lop, mon)] = mau
                for size in mau:
                    self.cac_cum.append(
                        Cum(ma, lop, mon, dm['nhom'], gv, size,
                            la_cd=dm.get('la_chuyen_de', False)))
                    ma += 1
                tong += st

            so_o = self.SO_NGAY * self.SO_TIET
            trong = so_o - tong
            if trong < 0:
                raise SystemExit(
                    f'[LỖI] Lớp {lop} có {tong} tiết/tuần nhưng TKB chỉ có '
                    f'{so_o} ô. Giảm số tiết hoặc mở thêm buổi trong "khung_gio".')
            if trong > 0:
                self.cac_cum.append(Cum(ma, lop, '', 'TRỐNG', '', trong,
                                        la_trong=True))
                ma += 1

    # ---------------- dựng quy tắc ----------------
    def _tao_quy_tac(self):
        for c in self.cac_cum:
            c.ngay_ok = set(range(self.SO_NGAY))
            c.vitri_ok = set(range(self.SO_TIET - c.size + 1))
            c.o_cam = set()
            c.qt = []
            c.qt_gy = []

        # ô trống luôn dồn về cuối buổi -> không có tiết trống chen giữa
        if self.luat.get('khong_tiet_trong_giua_buoi', True):
            for c in self.cac_cum:
                if c.la_trong:
                    c.vitri_ok = {self.SO_TIET - c.size}

        self.quy_tac = []
        for r in self.khai_bao_qt:
            loai = r.get('loai')
            if loai == 'gom_tiet':
                continue                       # đã xử lý ở bước tạo cụm
            if loai not in QT.DANH_MUC:
                raise SystemExit(
                    f'[LỖI] Không có loại quy tắc "{loai}".\n'
                    f'       Chạy: python xep_tkb.py --quy-tac  để xem danh mục.')
            self.quy_tac.append(QT.DANH_MUC[loai](r, self))

        for q in self.quy_tac:
            q.thu_hep_mien()
        for q in self.quy_tac:
            for c in self.cac_cum:
                if c.la_trong or not q.lien_quan(c):
                    continue
                if q.CAN_TRONG_KHI_GIAI:
                    c.qt.append(q)
                if q.CO_GOI_Y:
                    c.qt_gy.append(q)

    def _kiem_tra_so_bo(self):
        loi = [c for c in self.cac_cum if not c.ngay_ok or not c.vitri_ok]
        if loi:
            print('[LỖI] Các cụm sau bị quy tắc chặn hết mọi ô:')
            for c in loi:
                print('   -', c, '| ngày còn lại:', sorted(c.ngay_ok),
                      '| tiết còn lại:', sorted(c.vitri_ok))
            raise SystemExit('Hãy nới lỏng quy tắc liên quan trong cauhinh.json.')


# ==========================================================================
# 3. BỘ GIẢI (quay lui + heuristic + khởi động lại ngẫu nhiên)
# ==========================================================================

class BoGiai:

    def __init__(self, bt: BaiToan, rnd: random.Random,
                 gioi_han_buoc=30000, gioi_han_giay=3.0):
        self.bt = bt
        self.rnd = rnd
        self.gioi_han = gioi_han_buoc
        self.gioi_han_giay = gioi_han_giay

    def _khoi_tao(self):
        bt = self.bt
        self.lich = {l: [[None] * bt.SO_TIET for _ in range(bt.SO_NGAY)]
                     for l in bt.lop}
        self.gv_ban = defaultdict(lambda: [[None] * bt.SO_TIET
                                           for _ in range(bt.SO_NGAY)])
        self.mon_ngay = defaultdict(int)
        self.buoc = 0
        for q in bt.quy_tac:
            q.dat_lai()                      # xoá sạch bộ đếm riêng của quy tắc
        self.bt = bt

    def dat_duoc(self, c: Cum, ngay, vitri):
        bt = self.bt
        if ngay not in c.ngay_ok or vitri not in c.vitri_ok:
            return False
        hang_lop = self.lich[c.lop][ngay]
        for p in range(vitri, vitri + c.size):
            if hang_lop[p] is not None:
                return False
        if c.la_trong:
            return True
        hang_gv = self.gv_ban[c.gv][ngay]
        for p in range(vitri, vitri + c.size):
            if hang_gv[p] is not None:
                return False
        if c.o_cam:
            for p in range(vitri, vitri + c.size):
                if (ngay, p) in c.o_cam:
                    return False
        if bt.luat.get('mot_cum_moi_mon_moi_ngay', True):
            if self.mon_ngay[(c.lop, c.mon, ngay)] >= 1:
                return False
        for q in c.qt:
            if not q.cho_phep(self, c, ngay, vitri):
                return False
        return True

    def dat(self, c, ngay, vitri):
        c.ngay, c.vitri = ngay, vitri
        for p in range(vitri, vitri + c.size):
            self.lich[c.lop][ngay][p] = c
            if not c.la_trong:
                self.gv_ban[c.gv][ngay][p] = c
        if not c.la_trong:
            self.mon_ngay[(c.lop, c.mon, ngay)] += 1
            for q in c.qt:
                q.dat(self, c)

    def go(self, c):
        ngay, vitri = c.ngay, c.vitri
        if not c.la_trong:
            for q in c.qt:
                q.go(self, c)
            self.mon_ngay[(c.lop, c.mon, ngay)] -= 1
        for p in range(vitri, vitri + c.size):
            self.lich[c.lop][ngay][p] = None
            if not c.la_trong:
                self.gv_ban[c.gv][ngay][p] = None
        c.ngay = c.vitri = None

    def lua_chon(self, c):
        return [(d, v) for d in c.ngay_ok for v in c.vitri_ok
                if self.dat_duoc(c, d, v)]

    def _sap_ung_vien(self, c, lc):
        """Ô nào được nhiều quy tắc 'thích' thì thử trước."""
        self.rnd.shuffle(lc)
        if not c.qt_gy:
            return lc
        return sorted(lc, key=lambda x: -sum(
            1 for q in c.qt_gy if q.thich(self, c, x[0], x[1])))

    def _hoan(self, c):
        return any(q.hoan(self, c) for q in c.qt_gy)

    def _quay_lui(self, con_lai):
        if not con_lai:
            return True
        self.buoc += 1
        if self.buoc > self.gioi_han:
            raise TimeoutError
        if self.buoc % 512 == 0 and time.time() - self.moc_gio > self.gioi_han_giay:
            raise TimeoutError

        tot, tot_lc, tot_k = None, None, None
        for c in con_lai:
            lc = self.lua_chon(c)
            if not lc:
                return False
            k = (len(lc), self._hoan(c), c.la_cd, -c.size)
            if tot is None or k < tot_k:
                tot, tot_lc, tot_k = c, lc, k
                if len(lc) == 1:
                    break

        con_lai.remove(tot)
        for (d, v) in self._sap_ung_vien(tot, tot_lc):
            if self.dat_duoc(tot, d, v):
                self.dat(tot, d, v)
                if self._quay_lui(con_lai):
                    return True
                self.go(tot)
        con_lai.append(tot)
        return False

    def giai(self):
        self.moc_gio = time.time()
        self._khoi_tao()
        for c in self.bt.cac_cum:
            c.ngay = c.vitri = None
        con_lai = list(self.bt.cac_cum)
        con_lai.sort(key=lambda c: (len(c.ngay_ok) * len(c.vitri_ok), -c.size))
        try:
            if not self._quay_lui(con_lai):
                return None
        except TimeoutError:
            return None
        return {c.ma: (c.ngay, c.vitri) for c in self.bt.cac_cum}


# ==========================================================================
# 4. NẠP LẠI PHƯƠNG ÁN / CHẤM ĐIỂM / HẬU KIỂM
# ==========================================================================

def nap(bt, pa):
    theo_ma = {c.ma: c for c in bt.cac_cum}
    for ma, (d, v) in pa.items():
        theo_ma[ma].ngay, theo_ma[ma].vitri = d, v


def cham_diem(bt, pa, chi_tiet=False):
    nap(bt, pa)
    d, ct = 0, {}
    for q in bt.quy_tac:
        x = q.diem()
        if x:
            d += x
            ct[q.ghi_chu or q.TEN] = x
    return (d, ct) if chi_tiet else d


def hau_kiem(bt, pa):
    """Trả về (danh_sách_dòng_báo_cáo, số_lỗi)."""
    nap(bt, pa)
    bc, loi = [], 0

    def ghi(ten, ds_loi):
        nonlocal loi
        ds_loi = list(ds_loi)
        if ds_loi:
            loi += 1
        ct = '; '.join(str(x) for x in ds_loi[:8])
        if len(ds_loi) > 8:
            ct += f' ... (+{len(ds_loi) - 8})'
        bc.append(('ĐẠT' if not ds_loi else 'LỖI', ten, ct))

    ten_thu = lambda i: f'Thứ {bt.cac_thu[i]}'

    # --- kiểm tra nền, luôn chạy ---
    ban = defaultdict(list)
    for c in bt.cac_cum:
        if not c.la_trong:
            for p in range(c.vitri, c.vitri + c.size):
                ban[(c.gv, c.ngay, p)].append(c)
    ghi('Không giáo viên nào bị trùng 2 lớp cùng lúc',
        [f'{k[0]} {ten_thu(k[1])} tiết {bt.cac_tiet[k[2]]}'
         for k, v in ban.items() if len(v) > 1])

    dem = defaultdict(int)
    for c in bt.cac_cum:
        if not c.la_trong:
            dem[(c.lop, c.mon)] += c.size
    ghi('Đủ định mức tiết cho mỗi lớp / mỗi môn',
        [f'{lop}/{mon}: {dem[(lop, mon)]}≠{st}'
         for lop, ds in bt.cfg['phan_cong'].items() if not lop.startswith('_')
         for mon, gv, st in ds if dem[(lop, mon)] != st])

    ho = []
    for lop in bt.lop:
        for d in range(bt.SO_NGAY):
            hang = [None] * bt.SO_TIET
            for c in bt.cac_cum:
                if c.lop == lop and c.ngay == d and not c.la_trong:
                    for p in range(c.vitri, c.vitri + c.size):
                        hang[p] = c
            day = [i for i, x in enumerate(hang) if x is not None]
            if day and day != list(range(len(day))):
                ho.append(f'{lop} {ten_thu(d)}')
    ghi('Không có tiết trống chen giữa buổi', ho)

    # --- gom tiết: đối chiếu với cách chia cụm thực tế của từng lớp ---
    thuc = defaultdict(list)
    for c in bt.cac_cum:
        if not c.la_trong:
            thuc[(c.lop, c.mon)].append(c.size)
    theo_mon = defaultdict(lambda: [set(), []])
    for (lop, mon), mau in bt.mong_doi.items():
        if max(mau) < 2:
            continue
        theo_mon[mon][0].add('+'.join(str(x) for x in sorted(mau, reverse=True)))
        if sorted(thuc[(lop, mon)], reverse=True) != sorted(mau, reverse=True):
            theo_mon[mon][1].append(lop)
    for mon in sorted(theo_mon):
        kieu, xau = theo_mon[mon]
        ghi(f'{mon}: gom tiết theo kiểu {" / ".join(sorted(kieu))} tiết', xau)

    # --- từng quy tắc tự kiểm tra lại ---
    for q in bt.quy_tac:
        if q.TEN.startswith('uu_tien'):
            continue
        ghi(f'[{q.TEN}] {q.ghi_chu}', q.hau_kiem())

    return bc, loi


# ==========================================================================
# 5. XUẤT EXCEL (ghi đè lên file mẫu, giữ nguyên 100% định dạng)
# ==========================================================================

def xuat_excel(bt, pa, file_mau, file_xuat):
    try:
        import openpyxl
        from openpyxl.styles import Font, Alignment, Border, Side
    except ImportError:
        raise SystemExit('[LỖI] Thiếu thư viện openpyxl. Chạy: pip install openpyxl')

    if not os.path.exists(file_mau):
        raise SystemExit(f'[LỖI] Không tìm thấy file mẫu: {file_mau}')
    shutil.copy(file_mau, file_xuat)

    tt = bt.cfg['thong_tin']
    vt = tt['vi_tri_bang']
    wb = openpyxl.load_workbook(file_xuat)
    ws = wb[tt['ten_sheet']]

    ws.cell(vt['hang_tieu_de'], 1).value = tt['tieu_de']
    ws.cell(vt['hang_tuan'], 1).value = tt['tuan']
    for j, lop in enumerate(bt.lop):
        ws.cell(vt['hang_gvcn'], vt['cot_bat_dau'] + j).value = \
            bt.thong_tin_lop[lop]['gvcn']

    nap(bt, pa)
    for c in bt.cac_cum:
        if c.la_trong:
            continue
        cot = vt['cot_bat_dau'] + bt.lop.index(c.lop)
        for p in range(c.vitri, c.vitri + c.size):
            ws.cell(vt['hang_bat_dau'] + c.ngay * bt.SO_TIET + p,
                    cot).value = c.nhan()

    _sheet_giao_vien(wb, bt, Font, Alignment, Border, Side)
    _sheet_kiem_tra(wb, bt, pa, Font, Alignment, Border, Side)
    wb.save(file_xuat)
    return file_xuat


def _khung(Border, Side):
    m = Side(style='thin')
    return Border(left=m, right=m, top=m, bottom=m)


def _cot(idx):
    from openpyxl.utils import get_column_letter
    return get_column_letter(idx)


def _sheet_giao_vien(wb, bt, Font, Alignment, Border, Side):
    ten = 'TKB giáo viên'
    if ten in wb.sheetnames:
        del wb[ten]
    ws = wb.create_sheet(ten)
    kh = _khung(Border, Side)
    tit = Font(name='Times New Roman', size=11, bold=True)
    thg = Font(name='Times New Roman', size=10)
    giua = Alignment(horizontal='center', vertical='center', wrap_text=True)

    ws.cell(1, 1).value = 'THỜI KHÓA BIỂU THEO GIÁO VIÊN — ' + \
        bt.cfg['thong_tin']['tuan']
    ws.cell(1, 1).font = Font(name='Times New Roman', size=13, bold=True)

    for j, h in enumerate(['Giáo viên', 'Số tiết'], start=1):
        o = ws.cell(3, j, h); o.font = tit; o.border = kh; o.alignment = giua
    cot = 3
    for d in range(bt.SO_NGAY):
        for p in range(bt.SO_TIET):
            o = ws.cell(3, cot, f'T{bt.cac_thu[d]}\nt{bt.cac_tiet[p]}')
            o.font = tit; o.alignment = giua; o.border = kh
            ws.column_dimensions[_cot(cot)].width = 11
            cot += 1
    ws.column_dimensions['A'].width = 14
    ws.column_dimensions['B'].width = 7

    hang = 4
    for gv in sorted({c.gv for c in bt.cac_cum if not c.la_trong}):
        ds = [c for c in bt.cac_cum if c.gv == gv and not c.la_trong]
        o = ws.cell(hang, 1, gv); o.font = thg; o.border = kh; o.alignment = giua
        o = ws.cell(hang, 2, sum(c.size for c in ds))
        o.font = tit; o.border = kh; o.alignment = giua
        luoi = {}
        for c in ds:
            for p in range(c.vitri, c.vitri + c.size):
                luoi[(c.ngay, p)] = f'{c.lop}\n{c.mon}'
        cot = 3
        for d in range(bt.SO_NGAY):
            for p in range(bt.SO_TIET):
                o = ws.cell(hang, cot, luoi.get((d, p), ''))
                o.font = thg; o.alignment = giua; o.border = kh
                cot += 1
        ws.row_dimensions[hang].height = 26
        hang += 1
    ws.freeze_panes = 'C4'


def _sheet_kiem_tra(wb, bt, pa, Font, Alignment, Border, Side):
    from openpyxl.styles import PatternFill
    ten = 'Kiểm tra quy tắc'
    for x in ('Kiểm tra quy tắc', 'Kiểm tra ràng buộc'):
        if x in wb.sheetnames:
            del wb[x]
    ws = wb.create_sheet(ten)
    kh = _khung(Border, Side)
    tit = Font(name='Times New Roman', size=11, bold=True)
    thg = Font(name='Times New Roman', size=11)
    xanh = PatternFill('solid', fgColor='C6EFCE')
    do = PatternFill('solid', fgColor='FFC7CE')
    tren = Alignment(wrap_text=True, vertical='top')

    ws.cell(1, 1, 'BẢNG ĐỐI CHIẾU QUY TẮC').font = Font(
        name='Times New Roman', size=13, bold=True)
    for j, h in enumerate(['Kết quả', 'Nội dung quy tắc', 'Ghi chú'], start=1):
        o = ws.cell(3, j, h); o.font = tit; o.border = kh
    ws.column_dimensions['A'].width = 10
    ws.column_dimensions['B'].width = 66
    ws.column_dimensions['C'].width = 55

    bc, _ = hau_kiem(bt, pa)
    hang = 4
    for kq, ten_rb, ct in bc:
        o = ws.cell(hang, 1, kq); o.font = tit; o.border = kh
        o.fill = xanh if kq == 'ĐẠT' else do
        o.alignment = Alignment(horizontal='center')
        o = ws.cell(hang, 2, ten_rb); o.font = thg; o.border = kh; o.alignment = tren
        o = ws.cell(hang, 3, ct); o.font = thg; o.border = kh; o.alignment = tren
        hang += 1

    hang += 1
    ws.cell(hang, 1, 'ĐIỂM CÁC TIÊU CHÍ MỀM').font = Font(
        name='Times New Roman', size=12, bold=True)
    hang += 1
    _, ct = cham_diem(bt, pa, chi_tiet=True)
    for k, v in ct.items():
        ws.cell(hang, 2, k).font = thg
        ws.cell(hang, 2).border = kh
        ws.cell(hang, 3, v).font = tit
        ws.cell(hang, 3).border = kh
        hang += 1

    hang += 1
    ws.cell(hang, 1, 'SỐ TIẾT / SỐ BUỔI CỦA TỪNG GIÁO VIÊN').font = Font(
        name='Times New Roman', size=12, bold=True)
    hang += 1
    tk = defaultdict(lambda: [0, set()])
    for c in bt.cac_cum:
        if not c.la_trong:
            tk[c.gv][0] += c.size
            tk[c.gv][1].add(c.ngay)
    for j, h in enumerate(['Giáo viên', 'Số tiết/tuần', 'Số buổi lên lớp'], start=1):
        o = ws.cell(hang, j, h); o.font = tit; o.border = kh
    hang += 1
    for gv in sorted(tk):
        st, ng = tk[gv]
        for j, val in enumerate([gv, st, len(ng)], start=1):
            o = ws.cell(hang, j, val); o.font = thg; o.border = kh
        hang += 1


# ==========================================================================
# 6. IN RA MÀN HÌNH
# ==========================================================================

def in_tkb(bt, pa):
    nap(bt, pa)
    rong = 26
    print('\nTHỜI KHÓA BIỂU — ' + bt.cfg['thong_tin']['tuan'])
    print('Thứ  Tiết ' + ''.join(l.ljust(rong) for l in bt.lop))
    vach = '-' * (10 + rong * len(bt.lop))
    print(vach)
    for d in range(bt.SO_NGAY):
        for p in range(bt.SO_TIET):
            dong = f'{bt.cac_thu[d] if p == 0 else "":<5}{bt.cac_tiet[p]:<5}'
            for lop in bt.lop:
                o = ''
                for c in bt.cac_cum:
                    if (c.lop == lop and c.ngay == d and not c.la_trong
                            and c.vitri <= p < c.vitri + c.size):
                        o = c.nhan()
                        break
                dong += o.ljust(rong)
            print(dong)
        print(vach)


# ==========================================================================
# 7. HÀM MAIN
# ==========================================================================

def main():
    ap = argparse.ArgumentParser(description='Xếp thời khóa biểu')
    ap.add_argument('--cauhinh', default='cauhinh.json')
    ap.add_argument('--xuat', default=None)
    ap.add_argument('--tuan', default=None,
                    help='đổi dòng chữ tuần in trên TKB, ghi đè "tuan" '
                         'trong cauhinh.json (file không bị sửa)')
    ap.add_argument('--seed', type=int, default=None)
    ap.add_argument('--lan', type=int, default=None)
    ap.add_argument('--in-man-hinh', action='store_true')
    ap.add_argument('--quy-tac', action='store_true',
                    help='in danh mục các loại quy tắc rồi thoát')
    args = ap.parse_args()

    if args.quy_tac:
        QT.in_danh_muc()
        return

    cfg = doc_cau_hinh(args.cauhinh)
    if args.tuan:
        cfg['thong_tin']['tuan'] = args.tuan      # chỉ đổi trong bộ nhớ
    thu_muc = os.path.dirname(os.path.abspath(args.cauhinh))
    bt = BaiToan(cfg)

    tk = cfg.get('tim_kiem', {})
    so_lan = args.lan or tk.get('so_lan_thu', 300)
    seed = args.seed if args.seed is not None else tk.get('seed', 0)
    gh = tk.get('gioi_han_buoc', 30000)
    gh_giay = tk.get('gioi_han_giay_moi_lan', 3.0)
    tong_giay = tk.get('gioi_han_tong_giay', 60)

    cung = [q for q in bt.quy_tac if not q.TEN.startswith('uu_tien')]
    mem = [q for q in bt.quy_tac if q.TEN.startswith('uu_tien')]
    print('=' * 70)
    print(' XẾP THỜI KHÓA BIỂU'.center(70))
    print('=' * 70)
    print(f'Số lớp        : {len(bt.lop)}  ({", ".join(bt.lop)})')
    print(f'Khung giờ     : Thứ {bt.cac_thu} | buổi {bt.buoi} | '
          f'tiết {bt.cac_tiet[0]}–{bt.cac_tiet[-1]}')
    print(f'Cụm tiết      : {len([c for c in bt.cac_cum if not c.la_trong])} '
          f'(+{len([c for c in bt.cac_cum if c.la_trong])} ô trống)')
    print(f'Quy tắc nạp   : {len(cung)} quy tắc cứng, {len(mem)} tiêu chí mềm')
    print(f'Đang tìm phương án ({so_lan} lần thử, seed={seed}) ...')

    t0 = time.time()
    tot, diem_tot, so_ok, so_hop_le, da_thu = None, None, 0, 0, 0
    du_phong, diem_dp, loi_dp, dung_du_phong = None, None, None, False
    for i in range(so_lan):
        if time.time() - t0 > tong_giay:
            break
        da_thu += 1
        pa = BoGiai(bt, random.Random(seed + i), gh, gh_giay).giai()
        if pa is None:
            continue
        so_ok += 1
        d = cham_diem(bt, pa)
        _, loi = hau_kiem(bt, pa)
        if loi:
            # Dự phòng: ÍT VI PHẠM NHẤT trước, điểm mềm chỉ là tiêu chí phụ
            # khi số quy tắc lỗi bằng nhau.
            if loi_dp is None or (loi, -d) < (loi_dp, -diem_dp):
                du_phong, diem_dp, loi_dp = dict(pa), d, loi
            continue
        so_hop_le += 1
        if diem_tot is None or d > diem_tot:
            diem_tot, tot = d, dict(pa)

    if tot is None and du_phong is None:
        print('\n[KHÔNG XẾP ĐƯỢC] Các quy tắc đang mâu thuẫn nhau.')
        print('Gợi ý: tăng "so_lan_thu"/"gioi_han_tong_giay" trong mục "tim_kiem",')
        print('       hoặc tạm tắt bớt quy tắc bằng cách thêm  "bat": false.')
        sys.exit(1)
    if tot is None:
        tot, diem_tot, dung_du_phong = du_phong, diem_dp, True
        print('\n[CẢNH BÁO] Không có phương án nào thoả HẾT quy tắc cứng.')
        print(f'           Đây là phương án ÍT VI PHẠM NHẤT: {loi_dp} quy tắc lỗi, '
              f'điểm mềm {diem_dp}.')
        ds_loi = [(t, ct) for kq, t, ct in hau_kiem(bt, tot)[0] if kq == 'LỖI']
        print(f'           Các quy tắc đang bị vi phạm ({len(ds_loi)}):')
        for t, ct in ds_loi:
            print(f'             • {t}' + (f'  --> {ct}' if ct else ''))
        print('           Gợi ý: nới đúng những quy tắc vừa liệt kê ở trên trong')
        print('                  cauhinh.json (thêm "bat": false để tạm tắt), hoặc')
        print('                  tăng "so_lan_thu"/"gioi_han_tong_giay".')

    ket = (f'Phương án ít vi phạm nhất: {loi_dp} quy tắc lỗi, điểm mềm {diem_tot}.'
           if dung_du_phong else f'Điểm cao nhất: {diem_tot}.')
    print(f'-> {so_hop_le} phương án hợp lệ / {so_ok} lời giải / {da_thu} lần thử '
          f'trong {time.time() - t0:.0f}s. {ket}')

    _, ct = cham_diem(bt, tot, chi_tiet=True)
    if ct:
        print('\nĐIỂM CÁC TIÊU CHÍ MỀM')
        print('-' * 70)
        for k, v in ct.items():
            print(f'  {v:>6}   {k}')

    bc, loi = hau_kiem(bt, tot)
    print('\nĐỐI CHIẾU QUY TẮC')
    print('-' * 70)
    for kq, ten, c in bc:
        print(f'  [{kq}] {ten}' + (f'  --> {c}' if c else ''))
    print('-' * 70)
    print(f'Tổng: {len(bc) - loi}/{len(bc)} quy tắc ĐẠT.')

    if args.in_man_hinh:
        in_tkb(bt, tot)

    tt = cfg['thong_tin']
    fx = xuat_excel(bt, tot,
                    os.path.join(thu_muc, tt['file_mau']),
                    os.path.join(thu_muc, args.xuat or tt['file_xuat']))
    print(f'\nĐã xuất file: {fx}')
    print('   • Sheet "Khối 12"          : TKB chính (đúng mẫu tuần 1)')
    print('   • Sheet "TKB giáo viên"    : lịch dạy từng thầy cô')
    print('   • Sheet "Kiểm tra quy tắc" : bảng đối chiếu ĐẠT/LỖI')


if __name__ == '__main__':
    main()

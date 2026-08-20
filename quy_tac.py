#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 DANH MỤC QUY TẮC XẾP THỜI KHÓA BIỂU
--------------------------------------------------------------------------
 Mỗi quy tắc là 1 lớp Python được "đăng ký" vào DANH_MUC bằng @dang_ky.
 Muốn thêm loại quy tắc mới -> copy 1 lớp có sẵn, đổi tên, sửa 1-2 hàm.
 Không phải đụng vào xep_tkb.py.

 Mỗi quy tắc có tối đa 5 "móc nối" (hook), cài cái nào cần thì cài:

   thu_hep_mien()            chạy 1 LẦN trước khi giải — cắt bớt ngày/tiết
                             mà cụm được phép vào. Nhanh nhất, ưu tiên dùng.
   cho_phep(gs, c, ngay, v)  chạy TRONG lúc giải — trả False để chặn nước đi.
   dat(gs, c) / go(gs, c)    cập nhật bộ đếm riêng khi đặt/gỡ 1 cụm.
   hau_kiem()                chạy SAU khi giải — trả list mô tả chỗ vi phạm.
   diem()                    điểm mềm — càng cao càng được ưu tiên chọn.
   thich(gs, c, ngay, v)     True = "ô này đẹp" -> chương trình thử ô đó trước.
   hoan(gs, c)               True = "khoan hãy xếp cụm này, chờ cụm khác đã".

 Mỗi đối tượng quy tắc chỉ được tạo 1 lần rồi dùng lại cho MỌI lần thử (seed).
 Vì vậy mọi bộ đếm riêng phải khởi tạo trong __init__ -- bộ giải gọi dat_lai()
 một lần trước mỗi lần thử để xoá sạch chúng.

 Cụm (Cum) = nhóm tiết liên tiếp của cùng 1 môn / 1 GV / 1 lớp.
   c.lop c.mon c.nhom c.gv c.size c.la_cd c.ngay c.vitri
   ngay  = chỉ số ngày 0,1,2...  (0 = thứ đầu tiên trong "cac_thu")
   vitri = chỉ số tiết trong buổi 0,1,2... (0 = tiết đầu buổi)
==========================================================================
"""

from collections import defaultdict

DANH_MUC = {}

# Các khoá hợp lệ trong một bộ lọc ("loc", "a", "b", và "tru" lồng bên trong).
KHOA_LOC = ('mon', 'nhom_mon', 'gv', 'lop', 'la_chuyen_de', 'tru')

# Khoá cấp cao nhất mà quy tắc NÀO cũng nhận. Ngoài ra khoá bắt đầu bằng
# dấu gạch dưới luôn được bỏ qua — đó là quy ước ghi chú trong cauhinh.json.
KHOA_CHUNG = ('loai', 'ghi_chu', 'bat')

# Các kiểu dữ liệu dùng trong TRUONG. Form web dựa vào đây để biết nên
# hiện ô nhập kiểu gì, nên đừng đổi tên kiểu mà không sửa web/app.js.
KIEU = {
    'loc':          'bộ lọc: mon / nhom_mon / gv / lop / la_chuyen_de / tru',
    'ds_thu':       'danh sách thứ, vd [2, 3]',
    'ds_tiet':      'danh sách số hiệu tiết in trên TKB, vd [9, 10]',
    'ds_tiet_buoi': 'danh sách thứ tự tiết trong buổi, vd [4, 5]',
    'so_thu':       'một thứ, vd 6',
    'so_tiet':      'một số hiệu tiết, vd 10',
    'so_tiet_buoi': 'một thứ tự tiết trong buổi, vd 5',
    'ds_o':         'danh sách ô [thứ, tiết], vd [[4, 6], [4, 7]]',
    'ds_so':        'danh sách số, vd [2, 1]',
    'so':           'một số nguyên',
    'chon':         'chọn một trong các giá trị liệt kê ở khoá "chon"',
    'dung_sai':     'true hoặc false',
}


def truong(ten, kieu, nhan, bat_buoc=False, **them):
    """Mô tả một khoá cấp cao nhất của quy tắc, dùng cho cả --quy-tac lẫn
       form nhập trên giao diện web."""
    d = {'ten': ten, 'kieu': kieu, 'nhan': nhan, 'bat_buoc': bat_buoc}
    d.update(them)
    return d


T_LOC = truong('loc', 'loc', 'Áp cho những tiết nào')
T_A = truong('a', 'loc', 'Nhóm A', True)
T_B = truong('b', 'loc', 'Nhóm B', True)
T_DIEM = truong('diem', 'so', 'Điểm cộng mỗi lần thoả', True)
# "tiet" và "tiet_trong_buoi" thay thế nhau: phải có ít nhất một trong hai.
T_TIET = truong('tiet', 'ds_tiet', 'Theo số hiệu tiết', True, nhom='tiet')
T_TIET_BUOI = truong('tiet_trong_buoi', 'ds_tiet_buoi',
                     'Theo thứ tự tiết trong buổi', True, nhom='tiet')


def kiem_khoa_quy_tac(r, cls, ghi_chu):
    """Khoá lạ ở cấp cao nhất thì DỪNG. Bỏ qua lặng lẽ sẽ biến quy tắc
       thành quy tắc không cấm gì mà vẫn báo ĐẠT."""
    hop_le = set(KHOA_CHUNG) | {t['ten'] for t in cls.TRUONG}
    la = [k for k in r if k not in hop_le and not str(k).startswith('_')]
    if la:
        bao_loi(ghi_chu, 'quy tắc ' + cls.TEN, [f'"{k}"' for k in la],
                f'các khoá dùng được cho loại "{cls.TEN}": '
                + ' / '.join(sorted(hop_le)),
                goi_y=('      => Khoá lạ bị bỏ qua, nên quy tắc hoá ra KHÔNG cấm '
                       'gì cả mà vẫn báo ĐẠT.',
                       '         Xem danh mục đầy đủ: python3 xep_tkb.py --quy-tac'))
    nhom = {}
    for t in cls.TRUONG:
        if t.get('nhom'):
            nhom.setdefault(t['nhom'], []).append(t)
        elif t['bat_buoc'] and t['ten'] not in r:
            bao_loi(ghi_chu, 'quy tắc ' + cls.TEN, [f'thiếu "{t["ten"]}"'],
                    f'{t["nhan"]} — {KIEU.get(t["kieu"], t["kieu"])}',
                    goi_y=(f'      => Loại "{cls.TEN}" bắt buộc phải có khoá '
                           f'"{t["ten"]}".',))
    for ten_nhom, ds in nhom.items():
        if any(t['bat_buoc'] for t in ds) and not any(t['ten'] in r for t in ds):
            bao_loi(ghi_chu, 'quy tắc ' + cls.TEN,
                    ['thiếu ' + ' hoặc '.join(f'"{t["ten"]}"' for t in ds)],
                    'phải có ít nhất một trong hai khoá đó',
                    goi_y=(f'      => Hai khoá này thay thế nhau, ghi khoá nào '
                           f'cũng được.',))


def bao_loi(ghi_chu, khoa, sai, mo_ta_mien,
            khoa_kia=None, mien_kia=(), mo_ta_kia='', goi_y=()):
    """Dừng chương trình, nói đủ để người dùng tự sửa cauhinh.json.
       Để ở mức module vì xep_tkb.py cũng cần báo lỗi đúng khuôn này."""
    ds = ', '.join(str(x) for x in sai)
    dong = ['[LỖI] Khai báo sai trong cauhinh.json',
            f'      Quy tắc : {ghi_chu}',
            f'      Khoá    : "{khoa}"',
            f'      Giá trị : {ds}   -> KHÔNG hợp lệ',
            f'      Miền hợp lệ: {mo_ta_mien}']
    if khoa_kia and all(x in mien_kia for x in sai):
        dong.append(f'      => Có phải bạn định dùng khoá "{khoa_kia}" không? '
                    f'Giá trị {ds} hợp lệ với khoá đó.')
        dong.append(f'         Miền của "{khoa_kia}": {mo_ta_kia}')
    dong.extend(goi_y)
    dong.append('      Sửa lại rồi chạy: python3 xep_tkb.py')
    raise SystemExit('\n'.join(dong))


def khop_loc(dk, mon, nhom, gv, lop, la_cd):
    """BỘ LỌC CHUẨN — nơi DUY NHẤT định nghĩa "một tiết có thoả bộ lọc không".

       Nhận tham số RỜI chứ không nhận đối tượng Cum, vì gom_tiet phải lọc
       ngay trong BaiToan._tao_cum(), tức lúc chưa có cụm nào được tạo ra.
       Hàm này chỉ so khớp, không kiểm khai báo — kiểm là việc của
       kiem_bo_loc(), chạy 1 lần lúc dựng, để vòng quay lui khỏi trả giá.
    """
    if not dk:
        return True

    def co(khoa, gt):
        if khoa not in dk:
            return True
        ds = dk[khoa]
        if not isinstance(ds, list):
            ds = [ds]
        return gt in ds

    if not (co('mon', mon) and co('nhom_mon', nhom)
            and co('gv', gv) and co('lop', lop)):
        return False
    if 'la_chuyen_de' in dk and bool(dk['la_chuyen_de']) != la_cd:
        return False
    # "tru": khớp bộ lọc con này thì coi như KHÔNG khớp
    if 'tru' in dk and khop_loc(dk['tru'], mon, nhom, gv, lop, la_cd):
        return False
    return True


def kiem_bo_loc(dk, ghi_chu, ten='loc'):
    """Kiểm một bộ lọc lúc dựng. Gọi từ QuyTac.__init__ và từ
       BaiToan._map_gom_tiet(), nên khai sai ở chỗ nào cũng báo y hệt nhau."""
    if dk is None:
        return
    if not isinstance(dk, dict):
        bao_loi(ghi_chu, ten, [repr(dk)],
                'phải là một khối { ... } gồm ' + ' / '.join(KHOA_LOC))
    la = [k for k in dk if k not in KHOA_LOC]
    if la:
        bao_loi(ghi_chu, ten, [f'"{k}"' for k in la],
                'các khoá dùng được: ' + ' / '.join(KHOA_LOC),
                goi_y=('      => Khoá lạ bị bỏ qua, nên bộ lọc hoá ra áp cho '
                       'TẤT CẢ — gần như chắc chắn không phải ý bạn.',))
    if 'tru' in dk:
        tru = dk['tru']
        if not isinstance(tru, dict) or not tru:
            bao_loi(ghi_chu, ten + '.tru', [repr(tru)],
                    'phải nêu ít nhất một trong: '
                    + ' / '.join(k for k in KHOA_LOC if k != 'tru'),
                    goi_y=('      => "tru" rỗng thì loại trừ TẤT CẢ, tức quy tắc '
                           'không áp cho ai cả.',
                           '         Muốn tắt hẳn quy tắc thì thêm "bat": false, '
                           'đừng để "tru" rỗng.'))
        kiem_bo_loc(tru, ghi_chu, ten + '.tru')


def dang_ky(ten):
    def deco(cls):
        cls.TEN = ten
        DANH_MUC[ten] = cls
        return cls
    return deco


# ==========================================================================
# LỚP NỀN
# ==========================================================================

class QuyTac:
    TEN = ''
    MO_TA = ''
    VI_DU = {}
    TRUONG = ()                      # các khoá cấp cao nhất loại này nhận
    CAN_TRONG_KHI_GIAI = False       # True nếu có dùng cho_phep()/dat()/go()
    CO_GOI_Y = False                 # True nếu có dùng thich()/hoan()

    def __init__(self, r, bt):
        self.r = r
        self.bt = bt
        self.ghi_chu = r.get('ghi_chu') or r.get('_ghichu') or self.MO_TA
        kiem_khoa_quy_tac(r, type(self), self.ghi_chu)
        for k in ('loc', 'a', 'b'):
            if k in r:
                kiem_bo_loc(r[k], self.ghi_chu, k)
        if 'thu' in r:
            self._kiem_thu()         # bắt lỗi ngay, đừng đợi tới lúc chấm điểm
        if 'tiet' in r or 'tiet_trong_buoi' in r:
            self._kiem_tiet()
        if 'o' in r:
            self._kiem_o()

    def dat_lai(self):
        """Xoá sạch trạng thái riêng, chạy 1 lần trước MỖI lần thử (mỗi seed).
           Mặc định là dựng lại quy tắc từ đầu, nên mọi bộ đếm riêng chỉ cần
           khởi tạo trong __init__ là tự động được xoá. Chỉ ghi đè hàm này khi
           việc dựng lại quá tốn kém, và khi đó phải tự xoá hết bộ đếm.
           Bắt buộc sửa TẠI CHỖ trên chính đối tượng này, KHÔNG được tạo đối
           tượng mới, vì c.qt và c.qt_gy đang giữ tham chiếu tới đối tượng cũ."""
        self.__init__(self.r, self.bt)

    # ---------------- tiện ích dùng chung ----------------
    def loc(self, khoa='loc'):
        return self.r.get(khoa, {})

    def khop(self, c, dk=None):
        """Cụm c có thoả bộ lọc dk không? Việc so khớp nằm ở khop_loc() —
           đúng bộ lọc mà gom_tiet trong xep_tkb.py cũng dùng."""
        if c.la_trong:
            return False
        if dk is None:
            dk = self.loc()
        return khop_loc(dk, c.mon, c.nhom, c.gv, c.lop, c.la_cd)

    def cac_cum(self, dk=None):
        return [c for c in self.bt.cac_cum if self.khop(c, dk)]

    def tap_ngay(self, khoa='thu'):
        self._kiem_thu(khoa)
        return {self.bt.thu2idx[t] for t in self._ds(khoa)}

    def tap_tiet(self):
        """Gộp 'tiet' (số hiệu tiết thật) và 'tiet_trong_buoi' (thứ tự trong buổi).
           Giá trị ngoài miền hợp lệ làm DỪNG chương trình chứ không bị bỏ qua:
           lặng lẽ bỏ qua là biến một quy tắc sai thành quy tắc không cấm gì,
           vẫn báo ĐẠT — kiểu lỗi khó phát hiện nhất."""
        self._kiem_tiet()
        v = {t - 1 for t in self._ds('tiet_trong_buoi')}
        v |= {self.bt.tiet2idx[t] for t in self._ds('tiet')}
        return v

    # ------- kiểm giá trị người dùng khai trong cauhinh.json -------
    def _ds(self, khoa):
        """Đọc một khoá, chấp nhận cả 1 giá trị lẻ lẫn 1 danh sách."""
        gt = self.r.get(khoa, [])
        return gt if isinstance(gt, (list, tuple)) else [gt]

    def _mien_thu(self):
        thu = list(self.bt.cac_thu)
        return thu, ('số hiệu thứ trong tuần: '
                     + ', '.join(str(x) for x in thu))

    def _goi_y_thu(self, sai):
        """Hai kiểu nhầm hay gặp: đếm từ 1, và dùng thứ chưa khai trong cac_thu."""
        thu = list(self.bt.cac_thu)
        gy = ['      => "thu" ghi theo SỐ HIỆU THỨ in trên lịch (Thứ 2 ghi là 2), '
              'KHÔNG phải đếm từ 1.']
        for t in sai:
            if isinstance(t, int) and 1 <= t <= len(thu):
                gy.append(f'         Nếu bạn định nói ngày học thứ {t} của tuần '
                          f'thì phải ghi là {thu[t - 1]} (Thứ {thu[t - 1]}).')
            elif isinstance(t, int) and 2 <= t <= 8:
                gy.append(f'         Thứ {t} chưa được khai trong "khung_gio" -> '
                          f'"cac_thu". Muốn xếp thì thêm {t} vào đó trước.')
        return tuple(gy)

    def _kiem_thu(self, khoa='thu'):
        thu, mo_ta = self._mien_thu()
        sai = [t for t in self._ds(khoa) if t not in thu]
        if sai:
            self._bao_loi(khoa, sai, mo_ta, goi_y=self._goi_y_thu(sai))

    def _mien_tiet(self):
        """Hai cách ghi tiết và miền hợp lệ của mỗi cách."""
        tb = list(range(1, self.bt.SO_TIET + 1))
        that = list(self.bt.cac_tiet)
        mo_ta_tb = (f'{tb[0]}..{tb[-1]} (thứ tự trong buổi, 1 = tiết đầu buổi '
                    f'{self.bt.buoi})')
        mo_ta_that = ('số hiệu tiết in trên TKB: '
                      + ', '.join(str(x) for x in that))
        return tb, that, mo_ta_tb, mo_ta_that

    def _bao_loi(self, *a, **k):
        bao_loi(self.ghi_chu, *a, **k)

    def _kiem_tiet(self):
        tb, that, mo_ta_tb, mo_ta_that = self._mien_tiet()
        sai = [t for t in self._ds('tiet_trong_buoi') if t not in tb]
        if sai:
            self._bao_loi('tiet_trong_buoi', sai, mo_ta_tb,
                          'tiet', that, mo_ta_that)
        sai = [t for t in self._ds('tiet') if t not in that]
        if sai:
            self._bao_loi('tiet', sai, mo_ta_that,
                          'tiet_trong_buoi', tb, mo_ta_tb)

    def _kiem_o(self):
        """Khoá "o" ghi từng ô cụ thể: [[thứ, tiết], ...]"""
        tb, that, mo_ta_tb, mo_ta_that = self._mien_tiet()
        thu, mo_ta_thu = self._mien_thu()
        for i, cap in enumerate(self.r.get('o', []), start=1):
            if not isinstance(cap, (list, tuple)) or len(cap) != 2:
                raise SystemExit(
                    '[LỖI] Khai báo sai trong cauhinh.json\n'
                    f'      Quy tắc : {self.ghi_chu}\n'
                    f'      Khoá "o", ô thứ {i}: phải ghi [thứ, tiết], '
                    f'ví dụ [[4, 6], [4, 7]].\n'
                    f'      Đang ghi: {cap!r}')
            t, ti = cap
            if t not in thu:
                self._bao_loi(f'o — ô thứ {i}, phần THỨ', [t], mo_ta_thu,
                              goi_y=self._goi_y_thu([t]))
            if ti not in that:
                gy = ()
                if ti in tb:
                    gy = (f'      => Trong khoá "o" phải ghi SỐ HIỆU TIẾT in trên '
                          f'TKB, không phải thứ tự trong buổi.',
                          f'         Nếu bạn định nói "tiết thứ {ti} của buổi" '
                          f'thì phải ghi là tiết {that[ti - 1]}.')
                self._bao_loi(f'o — ô thứ {i}, phần TIẾT', [ti], mo_ta_that,
                              goi_y=gy)

    def ten_o(self, c):
        return (f'{c.lop}/{c.mon} Thứ {self.bt.cac_thu[c.ngay]} '
                f'tiết {self.bt.cac_tiet[c.vitri]}')

    # ---------------- các móc nối ----------------
    def thu_hep_mien(self):
        pass

    def lien_quan(self, c):
        return self.khop(c)

    def cho_phep(self, gs, c, ngay, vitri):
        return True

    def dat(self, gs, c):
        pass

    def go(self, gs, c):
        pass

    def hau_kiem(self):
        return []

    def diem(self):
        return 0

    def thich(self, gs, c, ngay, vitri):
        return False

    def hoan(self, gs, c):
        return False

    # --- tiện ích cho các quy tắc kiểu "hai nhóm a / b" ---
    def _ben(self, c):
        v = []
        if self.khop(c, self.r.get('a', {})):
            v.append('a')
        if self.khop(c, self.r.get('b', {})):
            v.append('b')
        return v

    def _ke(self, c, ngay, vitri, k):
        return k.ngay == ngay and (k.vitri + k.size == vitri
                                   or vitri + c.size == k.vitri)


# ==========================================================================
# NHÓM 1 — GIỚI HẠN NGÀY / TIẾT   (cắt miền, chạy 1 lần, rất nhanh)
# ==========================================================================

@dang_ky('chi_xep_thu')
class ChiXepThu(QuyTac):
    MO_TA = 'Chỉ được xếp vào những thứ liệt kê.'
    VI_DU = {"loai": "chi_xep_thu",
             "ghi_chu": "Vật lý 12B1, 12B2 chỉ Thứ 2 hoặc Thứ 3",
             "loc": {"mon": "Vật lý", "lop": ["12B1", "12B2"]},
             "thu": [2, 3]}
    TRUONG = (T_LOC,
              truong('thu', 'ds_thu', 'Chỉ được xếp vào các thứ', True))

    def thu_hep_mien(self):
        ok = self.tap_ngay()
        for c in self.cac_cum():
            c.ngay_ok &= ok

    def hau_kiem(self):
        ok = self.tap_ngay()
        return [self.ten_o(c) for c in self.cac_cum() if c.ngay not in ok]


@dang_ky('khong_xep_thu')
class KhongXepThu(QuyTac):
    MO_TA = 'Cấm xếp vào những thứ liệt kê.'
    VI_DU = {"loai": "khong_xep_thu",
             "ghi_chu": "Văn cô Duy không xếp Thứ 2",
             "loc": {"gv": "Đ.Duy"},
             "thu": [2]}
    TRUONG = (T_LOC,
              truong('thu', 'ds_thu', 'Cấm các thứ', True))

    def thu_hep_mien(self):
        cam = self.tap_ngay()
        for c in self.cac_cum():
            c.ngay_ok -= cam

    def hau_kiem(self):
        cam = self.tap_ngay()
        return [self.ten_o(c) for c in self.cac_cum() if c.ngay in cam]


@dang_ky('chi_xep_tiet')
class ChiXepTiet(QuyTac):
    MO_TA = 'Chỉ được xếp vào những tiết liệt kê (cả cụm phải nằm gọn trong đó).'
    VI_DU = {"loai": "chi_xep_tiet",
             "ghi_chu": "GDKT-PL luôn ở 2 tiết cuối buổi",
             "loc": {"mon": "GDKT-PL"},
             "tiet_trong_buoi": [4, 5]}
    TRUONG = (T_LOC, T_TIET, T_TIET_BUOI)

    def thu_hep_mien(self):
        ok = self.tap_tiet()
        for c in self.cac_cum():
            c.vitri_ok = {v for v in c.vitri_ok
                          if set(range(v, v + c.size)) <= ok}

    def hau_kiem(self):
        ok = self.tap_tiet()
        return [self.ten_o(c) for c in self.cac_cum()
                if not set(range(c.vitri, c.vitri + c.size)) <= ok]


@dang_ky('khong_xep_tiet')
class KhongXepTiet(QuyTac):
    MO_TA = ('Cấm những tiết liệt kê. "tiet_trong_buoi": 1 = tiết đầu buổi. '
             '"tiet": ghi số hiệu tiết thật (6, 7, 8...).')
    VI_DU = {"loai": "khong_xep_tiet",
             "ghi_chu": "Sử cô Ngọc Uyên không xếp tiết 4 và tiết 5 của buổi",
             "loc": {"gv": "N.Uyên", "nhom_mon": "Sử"},
             "tiet_trong_buoi": [4, 5]}
    TRUONG = (T_LOC, T_TIET, T_TIET_BUOI)

    def thu_hep_mien(self):
        cam = self.tap_tiet()
        for c in self.cac_cum():
            c.vitri_ok = {v for v in c.vitri_ok
                          if not (set(range(v, v + c.size)) & cam)}

    def hau_kiem(self):
        cam = self.tap_tiet()
        return [self.ten_o(c) for c in self.cac_cum()
                if set(range(c.vitri, c.vitri + c.size)) & cam]


@dang_ky('khong_xep_o')
class KhongXepO(QuyTac):
    MO_TA = ('Cấm từng ô cụ thể (thứ + tiết). Dùng khi giáo viên bận cố định '
             'một vài buổi. Ghi "o": [[thứ, tiết], [thứ, tiết], ...]')
    VI_DU = {"loai": "khong_xep_o",
             "ghi_chu": "Thầy Nam bận họp Thứ 4 tiết 6, 7",
             "loc": {"gv": "H.Nam"},
             "o": [[4, 6], [4, 7]]}
    TRUONG = (T_LOC,
              truong('o', 'ds_o', 'Các ô bị cấm (thứ + tiết)', True))

    def _tap_o(self):
        self._kiem_o()
        return {(self.bt.thu2idx[thu], self.bt.tiet2idx[tiet])
                for thu, tiet in self.r.get('o', [])}

    def thu_hep_mien(self):
        cam = self._tap_o()
        for c in self.cac_cum():
            c.o_cam |= cam

    def hau_kiem(self):
        cam = self._tap_o()
        return [self.ten_o(c) for c in self.cac_cum()
                if any((c.ngay, p) in cam
                       for p in range(c.vitri, c.vitri + c.size))]


@dang_ky('co_dinh')
class CoDinh(QuyTac):
    MO_TA = ('Ghim cứng vào đúng 1 ô (thứ + tiết). Nếu bộ lọc khớp nhiều cụm '
             'thì chỉ cụm đầu tiên của mỗi lớp bị ghim.')
    VI_DU = {"loai": "co_dinh",
             "ghi_chu": "SHCN 12B1 cố định Thứ 6 tiết 10",
             "loc": {"mon": "SHCN", "lop": "12B1"},
             "thu": 6, "tiet": 10}
    TRUONG = (T_LOC,
              truong('thu', 'so_thu', 'Ghim vào thứ', True),
              truong('tiet', 'so_tiet', 'Ghim vào tiết (số hiệu thật)',
                     True, nhom='tiet'),
              truong('tiet_trong_buoi', 'so_tiet_buoi',
                     'Ghim vào tiết thứ mấy của buổi', True, nhom='tiet'))

    def thu_hep_mien(self):
        bt = self.bt
        d = bt.thu2idx.get(self.r.get('thu'))
        if 'tiet' in self.r:
            v = bt.tiet2idx.get(self.r['tiet'])
        else:
            v = self.r.get('tiet_trong_buoi', 1) - 1
        if d is None or v is None:
            return
        da_ghim = set()
        for c in self.cac_cum():
            if c.lop in da_ghim:
                continue
            da_ghim.add(c.lop)
            c.ngay_ok = {d} & c.ngay_ok
            c.vitri_ok = {v} & c.vitri_ok


# ==========================================================================
# NHÓM 2 — QUAN HỆ GIỮA CÁC TIẾT   (kiểm tra trong lúc giải)
# ==========================================================================

@dang_ky('khac_ngay')
class KhacNgay(QuyTac):
    MO_TA = ('Hai nhóm tiết không được rơi vào cùng một ngày. '
             '"pham_vi": "toan_truong" (mặc định) hoặc "moi_lop" (chỉ xét '
             'trong phạm vi từng lớp).')
    VI_DU = {"loai": "khac_ngay",
             "ghi_chu": "Sử cô Lê Xuân không cùng ngày với lịch thầy Hùng",
             "a": {"gv": "N.Xuân"},
             "b": {"gv": "M.Hùng"},
             "pham_vi": "toan_truong"}
    TRUONG = (T_A, T_B,
              truong('pham_vi', 'chon', 'Xét trong phạm vi',
                     chon=('toan_truong', 'moi_lop')))
    CAN_TRONG_KHI_GIAI = True

    def __init__(self, r, bt):
        super().__init__(r, bt)
        self.theo_lop = r.get('pham_vi') == 'moi_lop'
        self.dem = defaultdict(int)

    def lien_quan(self, c):
        return bool(self._ben(c))

    def _khoa(self, ben, c, ngay):
        return (ben, c.lop if self.theo_lop else '*', ngay)

    def cho_phep(self, gs, c, ngay, vitri):
        for ben in self._ben(c):
            doi = 'b' if ben == 'a' else 'a'
            if self.dem[self._khoa(doi, c, ngay)] > 0:
                return False
        return True

    def dat(self, gs, c):
        for ben in self._ben(c):
            self.dem[self._khoa(ben, c, c.ngay)] += 1

    def go(self, gs, c):
        for ben in self._ben(c):
            self.dem[self._khoa(ben, c, c.ngay)] -= 1

    def hau_kiem(self):
        na, nb = defaultdict(set), defaultdict(set)
        for c in self.bt.cac_cum:
            k = c.lop if self.theo_lop else '*'
            if self.khop(c, self.r['a']):
                na[k].add(c.ngay)
            if self.khop(c, self.r['b']):
                nb[k].add(c.ngay)
        loi = []
        for k in na:
            for d in na[k] & nb[k]:
                loi.append(f'{k} Thứ {self.bt.cac_thu[d]}')
        return loi


@dang_ky('cung_ngay')
class CungNgay(QuyTac):
    MO_TA = ('Mọi tiết của nhóm a phải rơi vào ngày mà nhóm b cũng có tiết '
             '(vd: chuyên đề học đúng ngày có tiết chính).')
    VI_DU = {"loai": "cung_ngay",
             "ghi_chu": "Chuyên đề Toán học đúng ngày có tiết Toán chính",
             "a": {"mon": "Chuyên đề Toán"},
             "b": {"mon": "Toán học"}}
    TRUONG = (T_A, T_B)
    CAN_TRONG_KHI_GIAI = True
    CO_GOI_Y = True

    def __init__(self, r, bt):
        super().__init__(r, bt)
        self.cum_b = [c for c in bt.cac_cum if self.khop(c, r['b'])]

    def lien_quan(self, c):
        return bool(self._ben(c))

    def _b_cung_lop(self, c):
        return [k for k in self.cum_b if k.lop == c.lop]

    def cho_phep(self, gs, c, ngay, vitri):
        if 'a' not in self._ben(c):
            return True
        bs = self._b_cung_lop(c)
        if not bs or any(k.ngay is None for k in bs):
            return True                      # chưa đủ dữ kiện, chưa kết luận
        return ngay in {k.ngay for k in bs}

    def hoan(self, gs, c):
        return ('a' in self._ben(c)
                and any(k.ngay is None for k in self._b_cung_lop(c)))

    def thich(self, gs, c, ngay, vitri):
        if 'a' not in self._ben(c):
            return False
        return ngay in {k.ngay for k in self._b_cung_lop(c) if k.ngay is not None}

    def hau_kiem(self):
        loi = []
        for c in self.bt.cac_cum:
            if 'a' not in self._ben(c):
                continue
            ng = {k.ngay for k in self._b_cung_lop(c)}
            if ng and c.ngay not in ng:
                loi.append(self.ten_o(c))
        return loi


@dang_ky('toi_da_tiet_moi_ngay')
class ToiDaTietMoiNgay(QuyTac):
    MO_TA = ('Giới hạn số tiết trong 1 ngày. "theo": "gv" | "lop" | "mon_lop" '
             '(số tiết của cùng 1 môn trong 1 lớp).')
    VI_DU = {"loai": "toi_da_tiet_moi_ngay",
             "ghi_chu": "Mỗi giáo viên dạy tối đa 4 tiết/buổi",
             "loc": {}, "theo": "gv", "so": 4}
    TRUONG = (T_LOC,
              truong('theo', 'chon', 'Đếm theo', True,
                     chon=('gv', 'lop', 'mon_lop')),
              truong('so', 'so', 'Tối đa bao nhiêu tiết/ngày', True))
    CAN_TRONG_KHI_GIAI = True

    def __init__(self, r, bt):
        super().__init__(r, bt)
        self.theo = r.get('theo', 'gv')
        self.so = r.get('so', 5)
        self.dem = defaultdict(int)

    def _khoa(self, c):
        if self.theo == 'gv':
            return c.gv
        if self.theo == 'lop':
            return c.lop
        return (c.lop, c.mon)

    def cho_phep(self, gs, c, ngay, vitri):
        return self.dem[(self._khoa(c), ngay)] + c.size <= self.so

    def dat(self, gs, c):
        self.dem[(self._khoa(c), c.ngay)] += c.size

    def go(self, gs, c):
        self.dem[(self._khoa(c), c.ngay)] -= c.size

    def hau_kiem(self):
        d = defaultdict(int)
        for c in self.cac_cum():
            d[(self._khoa(c), c.ngay)] += c.size
        return [f'{k} Thứ {self.bt.cac_thu[n]}: {v} tiết'
                for (k, n), v in d.items() if v > self.so]


@dang_ky('toi_da_ngay_moi_tuan')
class ToiDaNgayMoiTuan(QuyTac):
    MO_TA = ('Giới hạn số buổi phải lên lớp trong tuần. '
             '"theo": "gv" (mặc định) | "lop".')
    VI_DU = {"loai": "toi_da_ngay_moi_tuan",
             "ghi_chu": "Cô Ngọc Uyên chỉ lên lớp tối đa 3 buổi/tuần",
             "loc": {"gv": "N.Uyên"}, "theo": "gv", "so": 3}
    TRUONG = (T_LOC,
              truong('theo', 'chon', 'Đếm theo', True, chon=('gv', 'lop')),
              truong('so', 'so', 'Tối đa bao nhiêu buổi/tuần', True))
    CAN_TRONG_KHI_GIAI = True

    def __init__(self, r, bt):
        super().__init__(r, bt)
        self.theo = r.get('theo', 'gv')
        self.so = r.get('so', 5)
        self.dem = defaultdict(int)

    def _khoa(self, c):
        return c.gv if self.theo == 'gv' else c.lop

    def cho_phep(self, gs, c, ngay, vitri):
        k = self._khoa(c)
        if self.dem[(k, ngay)] > 0:
            return True
        return sum(1 for (kk, _), n in self.dem.items()
                   if kk == k and n > 0) < self.so

    def dat(self, gs, c):
        self.dem[(self._khoa(c), c.ngay)] += 1

    def go(self, gs, c):
        self.dem[(self._khoa(c), c.ngay)] -= 1

    def hau_kiem(self):
        d = defaultdict(set)
        for c in self.cac_cum():
            d[self._khoa(c)].add(c.ngay)
        return [f'{k}: {len(v)} buổi' for k, v in d.items() if len(v) > self.so]


@dang_ky('khong_ke_nhau')
class KhongKeNhau(QuyTac):
    MO_TA = 'Hai nhóm môn của cùng một lớp không được xếp sát nhau (liền tiết).'
    VI_DU = {"loai": "khong_ke_nhau",
             "ghi_chu": "Không xếp Toán ngay sát Vật lý",
             "a": {"nhom_mon": "Toán"},
             "b": {"nhom_mon": "Lý"}}
    TRUONG = (T_A, T_B)
    CAN_TRONG_KHI_GIAI = True

    def lien_quan(self, c):
        return bool(self._ben(c))

    def cho_phep(self, gs, c, ngay, vitri):
        ben = self._ben(c)
        if not ben:
            return True
        hang = gs.lich[c.lop][ngay]
        for p in (vitri - 1, vitri + c.size):
            if 0 <= p < self.bt.SO_TIET:
                k = hang[p]
                if k is None or k.la_trong:
                    continue
                kb = self._ben(k)
                if ('a' in ben and 'b' in kb) or ('b' in ben and 'a' in kb):
                    return False
        return True

    def hau_kiem(self):
        loi = []
        for c in self.bt.cac_cum:
            if 'a' not in self._ben(c):
                continue
            for k in self.bt.cac_cum:
                if k.lop != c.lop or k.ngay != c.ngay or 'b' not in self._ben(k):
                    continue
                if k.vitri + k.size == c.vitri or c.vitri + c.size == k.vitri:
                    loi.append(self.ten_o(c))
        return loi


@dang_ky('phai_ke_nhau')
class PhaiKeNhau(QuyTac):
    MO_TA = ('Mọi tiết của nhóm a phải nằm sát nhóm b, cùng lớp cùng buổi '
             '(vd: chuyên đề luôn nối tiếp tiết chính). Đây là quy tắc CỨNG — '
             'nếu quá khó xếp hãy đổi sang "uu_tien_ke_nhau".')
    VI_DU = {"loai": "phai_ke_nhau",
             "ghi_chu": "Chuyên đề Toán phải nối tiếp tiết Toán chính",
             "a": {"mon": "Chuyên đề Toán"},
             "b": {"mon": "Toán học"}}
    TRUONG = (T_A, T_B)
    CAN_TRONG_KHI_GIAI = True
    CO_GOI_Y = True

    def __init__(self, r, bt):
        super().__init__(r, bt)
        self.cum_b = [c for c in bt.cac_cum if self.khop(c, r['b'])]

    def lien_quan(self, c):
        return bool(self._ben(c))

    def _b_cung_lop(self, c):
        return [k for k in self.cum_b if k.lop == c.lop]

    def cho_phep(self, gs, c, ngay, vitri):
        if 'a' not in self._ben(c):
            return True
        bs = self._b_cung_lop(c)
        if not bs or any(k.ngay is None for k in bs):
            return True                      # chờ nhóm b xếp xong đã
        return any(self._ke(c, ngay, vitri, k) for k in bs)

    def hoan(self, gs, c):
        return ('a' in self._ben(c)
                and any(k.ngay is None for k in self._b_cung_lop(c)))

    def thich(self, gs, c, ngay, vitri):
        if 'a' not in self._ben(c):
            return False
        return any(self._ke(c, ngay, vitri, k)
                   for k in self._b_cung_lop(c) if k.ngay is not None)

    def hau_kiem(self):
        loi = []
        for c in self.bt.cac_cum:
            if 'a' not in self._ben(c):
                continue
            bs = [k for k in self._b_cung_lop(c)]
            if not any(self._ke(c, c.ngay, c.vitri, k) for k in bs):
                loi.append(self.ten_o(c))
        return loi


# ==========================================================================
# NHÓM 3 — GOM TIẾT (xử lý ngay lúc tạo cụm, xem xep_tkb.py)
# ==========================================================================

@dang_ky('gom_tiet')
class GomTiet(QuyTac):
    MO_TA = ('Đổi cách chia cụm cho riêng một môn/lớp, đè lên "dinh_muc_mon". '
             '[2] = 2 tiết dính liền; [1,1] = tách 2 buổi; [2,1] = 1 buổi 2 '
             'tiết + 1 buổi 1 tiết.')
    VI_DU = {"loai": "gom_tiet",
             "ghi_chu": "Riêng 12B5, 12B6 tách Hoá ra 2 buổi",
             "loc": {"mon": "Hoá học", "lop": ["12B5", "12B6"]},
             "cum": [1, 1]}
    TRUONG = (T_LOC,
              truong('cum', 'ds_so', 'Cách chia cụm, vd [2, 1]', True))


# ==========================================================================
# NHÓM 4 — TIÊU CHÍ MỀM (không bắt buộc, chỉ cộng/trừ điểm)
# ==========================================================================

@dang_ky('uu_tien_o')
class UuTienO(QuyTac):
    MO_TA = ('Cộng điểm nếu xếp đúng thứ/tiết mong muốn (điểm âm = tránh). '
             'Không bắt buộc, chỉ dùng để chọn phương án đẹp hơn.')
    VI_DU = {"loai": "uu_tien_o",
             "ghi_chu": "Ưu tiên Toán, Văn vào 2 tiết đầu buổi",
             "loc": {"nhom_mon": ["Toán", "Văn"]},
             "tiet_trong_buoi": [1, 2],
             "diem": 3}
    TRUONG = (T_LOC,
              truong('thu', 'ds_thu', 'Ưu tiên các thứ'),
              dict(T_TIET, bat_buoc=False),
              dict(T_TIET_BUOI, bat_buoc=False),
              T_DIEM)

    def diem(self):
        ng = self.tap_ngay() if 'thu' in self.r else None
        ti = self.tap_tiet() if ('tiet' in self.r or
                                 'tiet_trong_buoi' in self.r) else None
        d, dv = 0, self.r.get('diem', 1)
        for c in self.cac_cum():
            if ng is not None and c.ngay not in ng:
                continue
            if ti is not None and not (set(range(c.vitri, c.vitri + c.size)) & ti):
                continue
            d += dv * c.size
        return d


@dang_ky('uu_tien_ke_nhau')
class UuTienKeNhau(QuyTac):
    MO_TA = 'Cộng điểm khi nhóm a nằm sát nhóm b trong cùng lớp, cùng buổi.'
    VI_DU = {"loai": "uu_tien_ke_nhau",
             "ghi_chu": "Nên xếp chuyên đề nối tiếp tiết chính",
             "a": {"la_chuyen_de": True},
             "b": {"la_chuyen_de": False},
             "cung_nhom_mon": True,
             "diem": 12}
    TRUONG = (T_A, T_B,
              truong('cung_nhom_mon', 'dung_sai',
                     'Chỉ tính khi cùng một nhóm môn'),
              T_DIEM)
    CO_GOI_Y = True

    def _hop(self, c, k):
        if not self.khop(k, self.r['b']):
            return False
        return not (self.r.get('cung_nhom_mon', False) and k.nhom != c.nhom)

    def thich(self, gs, c, ngay, vitri):
        if not self.khop(c, self.r['a']):
            return False
        hang = gs.lich[c.lop][ngay]
        for p in (vitri - 1, vitri + c.size):
            if 0 <= p < self.bt.SO_TIET:
                k = hang[p]
                if k is not None and not k.la_trong and self._hop(c, k):
                    return True
        return False

    def hoan(self, gs, c):
        if not self.khop(c, self.r['a']):
            return False
        return any(k.ngay is None for k in gs.bt.cac_cum
                   if k.lop == c.lop and k is not c and self._hop(c, k))

    def diem(self):
        dv = self.r.get('diem', 1)
        cung = self.r.get('cung_nhom_mon', False)
        d = 0
        for c in self.bt.cac_cum:
            if not self.khop(c, self.r['a']):
                continue
            for k in self.bt.cac_cum:
                if k is c or k.lop != c.lop or k.ngay != c.ngay:
                    continue
                if not self.khop(k, self.r['b']):
                    continue
                if cung and k.nhom != c.nhom:
                    continue
                if k.vitri + k.size == c.vitri or c.vitri + c.size == k.vitri:
                    d += dv
                    break
        return d


@dang_ky('uu_tien_it_buoi')
class UuTienItBuoi(QuyTac):
    MO_TA = ('Trừ điểm theo tổng số buổi giáo viên phải lên lớp — càng dồn '
             'buổi cho thầy cô càng được điểm cao.')
    VI_DU = {"loai": "uu_tien_it_buoi", "loc": {}, "diem": 4}
    TRUONG = (T_LOC, T_DIEM)

    def diem(self):
        ng = defaultdict(set)
        for c in self.cac_cum():
            ng[c.gv].add(c.ngay)
        return -self.r.get('diem', 1) * sum(len(v) for v in ng.values())


@dang_ky('uu_tien_trai_deu')
class UuTienTraiDeu(QuyTac):
    MO_TA = ('Cộng điểm khi hai buổi học của cùng một môn (trong cùng lớp) '
             'cách nhau từ "cach" ngày trở lên.')
    VI_DU = {"loai": "uu_tien_trai_deu", "loc": {}, "cach": 2, "diem": 3}
    TRUONG = (T_LOC,
              truong('cach', 'so', 'Cách nhau ít nhất mấy ngày', True),
              T_DIEM)

    def diem(self):
        cach = self.r.get('cach', 2)
        dv = self.r.get('diem', 1)
        nh = defaultdict(list)
        for c in self.cac_cum():
            if not c.la_cd:
                nh[(c.lop, c.mon)].append(c.ngay)
        d = 0
        for ds in nh.values():
            ds.sort()
            for i in range(len(ds) - 1):
                if ds[i + 1] - ds[i] >= cach:
                    d += dv
        return d


# ==========================================================================
# IN DANH MỤC RA MÀN HÌNH
# ==========================================================================

# Xếp 17 loại vào nhóm cho dễ tra. Loại nào quên xếp vẫn hiện, xem nhom_danh_muc().
NHOM_LOAI = (
    ('GIỚI HẠN NGÀY / TIẾT',
     ['chi_xep_thu', 'khong_xep_thu', 'chi_xep_tiet', 'khong_xep_tiet',
      'khong_xep_o', 'co_dinh']),
    ('QUAN HỆ GIỮA CÁC TIẾT',
     ['khac_ngay', 'cung_ngay', 'toi_da_tiet_moi_ngay',
      'toi_da_ngay_moi_tuan', 'khong_ke_nhau', 'phai_ke_nhau']),
    ('GOM TIẾT', ['gom_tiet']),
    ('TIÊU CHÍ MỀM (chỉ cộng/trừ điểm)',
     ['uu_tien_o', 'uu_tien_ke_nhau', 'uu_tien_it_buoi', 'uu_tien_trai_deu']),
)


def nhom_danh_muc():
    """Danh mục đã xếp nhóm, KÈM nhóm "CHƯA XẾP NHÓM" cho loại mới thêm mà
       quên xếp. Dùng chung cho in_danh_muc() và cho giao diện web — khai một
       chỗ, hai nơi khỏi lệch."""
    ds = [(ten, [t for t in ds_t if t in DANH_MUC]) for ten, ds_t in NHOM_LOAI]
    da = {t for _, ds_t in ds for t in ds_t}
    con = sorted(t for t in DANH_MUC if t not in da)
    if con:
        ds.append(('CHƯA XẾP NHÓM', con))
    return [(ten, ds_t) for ten, ds_t in ds if ds_t]


def in_danh_muc():
    import json
    nhom = nhom_danh_muc()
    print('=' * 74)
    print(' DANH MỤC QUY TẮC — chép mẫu bên dưới vào mục "quy_tac" của cauhinh.json')
    print('=' * 74)
    for ten_nhom, ds in nhom:
        _in_nhom(ten_nhom, ds)
    print('\n' + '=' * 74)
    print(' Dấu * = khoá bắt buộc. Khoá nào không có trong danh sách trên thì')
    print(' chương trình DỪNG chứ không bỏ qua — bỏ qua sẽ thành quy tắc rỗng.')
    print(' Bộ lọc "loc" dùng chung: mon / nhom_mon / gv / lop / la_chuyen_de / tru.')
    print(' Mỗi khoá nhận 1 giá trị hoặc 1 danh sách. Bỏ trống = áp cho tất cả.')
    print(' Thêm "bat": false để tạm tắt một quy tắc mà không cần xoá.')
    print('=' * 74)


def _in_nhom(ten_nhom, ds):
    print(f'\n### {ten_nhom}')
    for t in ds:
        cls = DANH_MUC[t]
        print(f'\n  ▸ {t}')
        for dong in _xuong_dong(cls.MO_TA, 68):
            print(f'      {dong}')
        for tr in cls.TRUONG:          # đọc thẳng TRUONG, không suy từ VI_DU
            dau = '*' if tr['bat_buoc'] else ' '
            mo = KIEU.get(tr['kieu'], tr['kieu'])
            if tr.get('chon'):
                mo = 'một trong: ' + ' / '.join(tr['chon'])
            if tr.get('nhom'):
                mo += '  (thay thế được cho khoá cùng nhóm)'
            print(f'      {dau} "{tr["ten"]}"  —  {tr["nhan"]}')
            print(f'          {mo}')
        print('      ' + _gon(cls.VI_DU).replace('\n', '\n      '))


def _gon(obj):
    """In JSON dễ đọc: mỗi khoá 1 dòng, riêng danh sách thì gom lại 1 dòng."""
    import json
    import re
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    s = re.sub(r'\[\s+([^\[\]{}]*?)\s+\]',
               lambda m: '[' + ', '.join(x.strip() for x in
                                         m.group(1).split(',')) + ']',
               s, flags=re.S)
    return s


def _xuong_dong(s, rong):
    tu, dong, ds = s.split(), '', []
    for t in tu:
        if len(dong) + len(t) + 1 > rong:
            ds.append(dong)
            dong = t
        else:
            dong = (dong + ' ' + t).strip()
    if dong:
        ds.append(dong)
    return ds


if __name__ == '__main__':
    in_danh_muc()

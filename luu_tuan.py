#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 LƯU MỘT TUẦN TKB VÀO KHO — dòng lệnh cho thầy cô
--------------------------------------------------------------------------
   python3 luu_tuan.py xem     <tệp.xlsx>
   python3 luu_tuan.py them    <tệp.xlsx> --tuan 2026-08-24 --nguoi "..."
   python3 luu_tuan.py liet-ke
   python3 luu_tuan.py danh-dau --tuan 2026-08-24 --ban 2 \\
                       --trang-thai sai --ly-do "..."
   python3 luu_tuan.py de-dang  --tuan 2026-08-24
   python3 luu_tuan.py khuyet-tat --tuan 2026-08-24 --ban 1 \\
                       --mo-ta "..." --nguoi "..." [--o D11 --o D18]
   python3 luu_tuan.py so       <tệp.xlsx> --tuan 2026-08-24 [--ban N]
                                # mặc định in HẸP cho điện thoại;
                                # --rong = bảng 84 cột, --het = in hết
   python3 luu_tuan.py dang-thu --tuan 2026-08-24 [--ra <thư mục>]
   python3 luu_tuan.py doi-chieu --tuan 2026-08-24 [--ban N]
                                # phan_cong trong cauhinh.json có khớp
                                # bản TKB thật không — CHỈ ĐỌC

 `xem` CHỈ ĐỌC, không ghi một byte nào — dùng để ngó trước khi lưu.

 KHÔNG TỰ QUYẾT KHI LỆCH. Ô A4 nói một khoảng ngày, `--tuan` nói một mã
 khác thì lệnh này HIỆN CẢ HAI rồi DỪNG. Muốn lưu thì gõ lại kèm
 `--dong-y-lech`, tức người quyết chứ không phải máy đoán.
==========================================================================
"""
import argparse
import io
import json
import os
import sys

import bang_ten as BT
import doc_tkb as D
import doi_chieu as DC
import kho_tuan as K
import sinh_dang as SD

GOC = os.path.dirname(os.path.abspath(__file__))

# Số ô in ra trước khi dừng. 132 ô đổ ra màn hình điện thoại thì bằng
# không in gì — người dùng chốt 22/8/2026.
TRAN_O = 20


def _keu_bang(*cac_bang):
    """In lỗi bảng tên ra màn hình. Trả True nếu có bảng nào hỏng.

       KÊU TO chứ không nuốt: `doc_tkb.doc()` tắt hẳn phần "tên môn lạ" khi
       `ten_mon_biet` rỗng, nên một bảng hỏng làm bản báo cáo hiện "0 chuỗi
       lạ" — trông y hệt "đã kiểm và sạch". Đúng bẫy `n_uyen == 0`, lần này
       ở phía thầy cô.
    """
    hong = False
    for b in cac_bang:
        for x in b.loi:
            print(f'[CẢNH BÁO] {x}')
            hong = True
    if hong:
        print('           Coi như chưa có tên nào được duyệt.')
    return hong


def _in_bao_cao(r, lech_bang=None, bang_mon=None):
    """In mọi thứ người dùng cần ngó. Trả True nếu tệp đọc được."""
    if r['loi']:
        print('\n[KHÔNG ĐỌC ĐƯỢC TỆP]')
        for x in r['loi']:
            print(f'   {x}')
        return False

    t = r['tuan_A4'] or {}
    print(f'\n   Tệp        : {r["tep"]}')
    print(f'   Tiêu đề A3 : {r["tieu_de"]}')
    print(f'   Chuỗi A4   : {t.get("tho")!r}')
    print(f'   -> đọc ra  : {t.get("tu")} → {t.get("den")}   nhãn {t.get("nhan")!r}')
    print(f'   Bộ đọc     : phiên bản {r["bo_doc"].get("phien_ban")} · '
          f'mã {r["bo_doc"].get("bam_ma")}')
    print(f'   Số ô đọc   : {len(r["o"])}')
    print(f'   Số tiết/lớp: {r["dem_tach_duoc"]}')

    if lech_bang:
        print(f'\n   [LỆCH NGÀY — MÁY KHÔNG ĐOÁN, MỜI THẦY CÔ CHỌN]')
        for x in lech_bang:
            print(f'      {x}')

    if r['sheet_khac']:
        print(f'\n   [SHEET KHÁC trong tệp] {r["sheet_khac"]}')
        print('      Kho lưu NGUYÊN tệp gốc nên các sheet này cũng được lưu.')
        print('      ⚠ Chúng KHÔNG được đăng ra trang công khai — sheet theo')
        print('        dõi bù thường kèm lý do nghỉ của học sinh.')

    if r['ngoai_mo_hinh']:
        print(f'\n   [CÓ CHỮ Ở VÙNG THỨ 7] {len(r["ngoai_mo_hinh"])} ô — '
              'mô hình hiện KHÔNG có Thứ 7, nên phần này KHÔNG được tách:')
        for x in r['ngoai_mo_hinh'][:10]:
            print(f'      {x["o"]}: {x["chu"]}')
        if len(r['ngoai_mo_hinh']) > 10:
            print(f'      … và {len(r["ngoai_mo_hinh"]) - 10} ô nữa')

    if r['lech_dem']:
        print(f'\n   [Ô TỔNG DÒNG 43 ĐẾM SAI] {len(r["lech_dem"])} chỗ:')
        for x in r['lech_dem']:
            print(f'      {x}')

    # HAI KHỐI, KHÔNG PHẢI MỘT. Bộ đọc chỉ biết khoá "biet", nên mọi chuỗi
    # đã có luật gộp vẫn nằm trong `ten_mon_la` — và đó là ĐÚNG: bản tách ghi
    # vào kho phải đóng băng đúng những chuỗi tệp đã viết. Việc phân loại
    # "chưa ai xét" / "đã có người quyết" là việc của tầng báo cáo này.
    gop = bang_mon.gop if bang_mon else {}
    chua_ai_xet = [x for x in r['ten_mon_la'] if x not in gop]
    da_co_luat = [x for x in r['ten_mon_la'] if x in gop]

    if bang_mon is not None and not bang_mon.biet:
        print('\n   [KHÔNG KIỂM ĐƯỢC TÊN MÔN] bang_ten_mon.json rỗng hoặc '
              'hỏng,')
        print('      nên bộ đọc KHÔNG soi tên môn lần này. "0 chuỗi lạ" dưới '
              'đây')
        print('      nghĩa là CHƯA KIỂM, không phải là SẠCH.')

    if chua_ai_xet:
        print(f'\n   [TÊN MÔN LẠ — CHƯA AI DUYỆT] {len(chua_ai_xet)} chuỗi '
              'chưa có trong bang_ten_mon.json — phần mềm KHÔNG tự gộp:')
        for x in chua_ai_xet:
            print(f'      {x!r}')
        print('      Duyệt tay: thêm vào "biet" (tên đúng) hoặc "gop"')
        print('      (chuỗi lạ -> tên chuẩn) trong bang_ten_mon.json.')

    if da_co_luat:
        print(f'\n   [TÊN MÔN LẠ — ĐÃ CÓ LUẬT GỘP] {len(da_co_luat)} chuỗi. '
              'Tệp gốc')
        print('      giữ nguyên chữ nhà trường gõ; việc gộp CHỈ áp lúc đối '
              'chiếu:')
        for x in da_co_luat:
            ng, ngay = bang_mon.ai_duyet(x)
            print(f'      {x!r} -> {bang_mon.chuan(x)!r}   ({ng} · {ngay})')
    return True


def _in_khuyet_tat(ban, thut='      '):
    """In khuyết tật ĐÃ BIẾT của một bản. Không có thì không in gì."""
    ds = K.khuyet_tat_cua(ban)
    if not ds:
        return
    print(f'{thut}[KHUYẾT TẬT ĐÃ BIẾT] {len(ds)} chỗ — bản này vẫn dùng '
          'được, nhưng:')
    for x in ds:
        o = ', '.join(x.get('o_excel') or []) or '(không ghi ô)'
        print(f'{thut}   · {x.get("mo_ta")}')
        print(f'{thut}     ô {o} · {x.get("nguoi")} xác nhận {x.get("ngay")}')


def _lech_ngay(r, ma_tuan):
    t = r.get('tuan_A4') or {}
    if not ma_tuan or not t.get('tu') or t['tu'] == ma_tuan:
        return []
    return [f'Ô A4 trong tệp nói tuần bắt đầu : {t["tu"]}   ({t.get("tho")!r})',
            f'Còn --tuan thầy cô gõ vào là     : {ma_tuan}',
            'Hai cái này KHÁC NHAU. Máy không chọn hộ.',
            'Đúng cái nào thì gõ lại với --tuan <ngày đúng> --dong-y-lech.']


def _so(goc, a, bang_mon):
    """So tệp `a.tep` với một bản trong kho. CHỈ ĐỌC, không ghi một byte nào."""
    ban, loi = K.chon_ban(goc, a.tuan, a.ban)
    if loi:
        print(f'[DỪNG] {loi}')
        return 1
    kho = K.duong_ban(goc, a.tuan, ban)
    if not kho or not os.path.exists(kho):
        print(f'[DỪNG] Bản trong phiếu trỏ tới {ban.get("tep")!r} mà tệp đó '
              'không có trên đĩa.')
        return 1

    # CHỈ `biet`, KHÔNG kèm `gop` — xem khối chữ đầu bang_ten.py.
    biet = bang_mon.biet
    A = D.doc(kho, ten_mon_biet=biet)          # TRÁI  = bản trong kho
    B = D.doc(a.tep, ten_mon_biet=biet)        # PHẢI  = tệp đang cầm
    for ten, r in (('bản trong kho', A), ('tệp đang so', B)):
        if r['loi']:
            print(f'[DỪNG] Không đọc được {ten}:')
            for x in r['loi']:
                print(f'   {x}')
            return 1

    if a.rong:
        print(f'   TRÁI  (kho)  : {ban.get("tep")}')
        print(f'                  lưu {ban.get("gio_luu")} · '
              f'trạng thái {K.trang_thai_cua(ban)!r}')
        print(f'   PHẢI  (so)   : {a.tep}')
        print(f'   Bộ đọc       : {A["bo_doc"].get("bam_ma")}')
    else:
        print(f'  kho: {os.path.basename(ban.get("tep") or "")[:34]}')
        print(f'       {(ban.get("gio_luu") or "")[:19]} · '
              f'{K.trang_thai_cua(ban)}')
        print(f'  so : {os.path.basename(a.tep)[:34]}')
    if A['bo_doc'] != B['bo_doc']:
        print('   ⚠ hai bên đọc bằng HAI bộ đọc khác nhau')

    if K.bam_tep(kho) == K.bam_tep(a.tep):
        print('\n   HAI TỆP GIỐNG HỆT NHAU TỪNG BYTE (SHA-256 trùng).')
        return 0

    key = lambda o: (o['lop'], o['thu'], o['tiet'])
    da = {key(o): o for o in A['o']}
    db = {key(o): o for o in B['o']}
    mo = lambda o: (f'{o["mon"]} ({o["gv"]})' if o and o.get('gv')
                    else (o['mon'] if o else '(TRỐNG)'))
    khac = []
    for k in sorted(set(da) | set(db)):
        x, y = da.get(k), db.get(k)
        if mo(x) != mo(y):
            o = (x or y).get('o_excel')
            khac.append((k[0], k[1], k[2], o, mo(x), mo(y)))
    print(f'\n   {len(khac)} ô KHÁC NHAU '
          f'(kho {len(A["o"])} ô · so {len(B["o"])} ô)\n')

    tran = len(khac) if a.het else TRAN_O
    if a.rong:
        if khac:
            print(f'   {"lớp":<7}{"khi nào":<14}{"ô":<6}'
                  f'{"TRÁI (kho)":<30}PHẢI (so)')
            print('   ' + '-' * 84)
        for lop, thu, tiet, o, cu, moi in khac[:tran]:
            print(f'   {lop:<7}T{thu} tiết {tiet:<6}{o:<6}{cu:<30}{moi}')
    else:
        # Dạng HẸP — mặc định. Người dùng đọc trên ĐIỆN THOẠI là chính, và
        # một bảng 84 cột đổ ra màn hình hẹp thì bằng không in gì.
        lop_truoc = None
        for lop, thu, tiet, o, cu, moi in khac[:tran]:
            if lop != lop_truoc:
                print(f'  ── {lop} ──')
                lop_truoc = lop
            print(f'  T{thu} tiết {tiet}  ({o})')
            print(f'     kho: {cu}')
            print(f'     so : {moi}')
    if len(khac) > tran:
        print(f'\n   … còn {len(khac) - tran} ô nữa, thêm --het để in hết.')

    print()
    if a.rong:
        for ten, r in (('kho', A), ('so', B)):
            if r['dem_tach_duoc']:
                print(f'   số tiết/lớp ({ten:<3}): {r["dem_tach_duoc"]}')
    else:
        da, db2 = A['dem_tach_duoc'], B['dem_tach_duoc']
        moi_lop = sorted(set(da) | set(db2))
        if moi_lop:
            print('  số tiết/lớp   kho   so')
            for l in moi_lop:
                x, y = da.get(l, 0), db2.get(l, 0)
                dau = '' if x == y else f'  {y - x:+d}'
                print(f'  {l:<12}{x:>4}{y:>6}{dau}')
    print(f'\n  TỔNG: {len(khac)} ô khác.')
    return 0


def _doi_chieu(goc, a, bang_mon, bang_gv):
    """So `phan_cong` của cauhinh.json với một bản đã lưu. CHỈ ĐỌC."""
    ban, loi = K.chon_ban(goc, a.tuan, a.ban)
    if loi:
        print(f'[DỪNG] {loi}')
        return 1
    dt = ban.get('tach')
    if not dt:
        print(f'[DỪNG] Bản {ban.get("tep")!r} không có bản tách — chưa có gì '
              'để đối chiếu.')
        return 1
    dd = os.path.join(K.thu_muc_tuan(goc, a.tuan), dt)
    try:
        with io.open(dd, encoding='utf-8-sig') as f:
            tach = json.load(f)
    except Exception as e:                              # noqa: BLE001
        print(f'[DỪNG] Không đọc được bản tách {dt}: {type(e).__name__}: {e}')
        return 1
    try:
        with io.open(a.cauhinh, encoding='utf-8-sig') as f:
            cfg = json.load(f)
    except Exception as e:                              # noqa: BLE001
        print(f'[DỪNG] Không đọc được {a.cauhinh}: {type(e).__name__}: {e}')
        return 1

    # Cắt ở 30 để cả dòng vừa 39 cột — thầy cô đọc trên ĐIỆN THOẠI.
    print(f'  kho: {os.path.basename(ban.get("tep") or "")[:30]}')
    print(f'       {(ban.get("gio_luu") or "")[:19]} · '
          f'{K.trang_thai_cua(ban)}')
    print(f'  với: {os.path.basename(a.cauhinh)[:30]}')
    print(f'  bảng tên: môn {len(bang_mon.gop)} cặp · GV {len(bang_gv.gop)} cặp')
    _in_khuyet_tat(ban, '  ')

    kq = DC.so(*DC.tu_ban_tach(tach, bang_mon, bang_gv), *DC.tu_cau_hinh(cfg))
    DC.in_hep(kq)
    print('\n  (chỉ đọc — không ghi một byte nào)')
    return 0


def _dang_thu(goc, a):
    """Sinh JSON một tuần để đăng, ghi vào thư mục TẠM. KHÔNG ghi vào docs/."""
    import tempfile
    ra = a.ra or tempfile.mkdtemp(prefix='dang_thu_')
    that = os.path.realpath(ra)
    cam = os.path.realpath(os.path.join(GOC, 'docs'))
    if that == cam or that.startswith(cam + os.sep):
        print('[DỪNG] KHÔNG ghi vào docs/. Thư mục đó là thứ GitHub Pages')
        print('       phục vụ ra Internet, và git thì nhớ vĩnh viễn. Lệnh này')
        print('       chỉ sinh thử; việc đăng thật là quyết định của người.')
        return 1

    d, tu_choi = SD.du_lieu_dang(goc, a.tuan)
    if tu_choi:
        print('[KHÔNG ĐĂNG ĐƯỢC] ' + tu_choi)
        return 1

    os.makedirs(ra, exist_ok=True)
    dd = os.path.join(ra, f'{a.tuan}.json')
    io.open(dd, 'w', encoding='utf-8').write(
        json.dumps(d, ensure_ascii=False, indent=1) + '\n')
    print(f'[XONG] {dd}')
    print(f'   tuần      : {d.get("ma_tuan")}  {d.get("nhan")!r}  '
          f'{d.get("tu_ngay")} → {d.get("den_ngay")}')
    print(f'   trường ra : {d.get("truong_o")}')
    print(f'   {len(d.get("o") or [])} ô · {len(d.get("lop") or [])} lớp · '
          f'{len(d.get("gv") or [])} giáo viên')
    ng = d.get('nguon') or {}
    print(f'   nguồn     : bản lưu {ng.get("gio_luu")}')
    print(f'               lý do đánh dấu "dung": {ng.get("ly_do_dung")}')
    print('\n   Đây là THƯ MỤC TẠM. Không có gì được ghi vào docs/.')
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(
        description='Lưu và xem kho TKB theo tuần.')
    ap.add_argument('--kho', default=None, help='thư mục kho (mặc định luu_tru/)')
    sub = ap.add_subparsers(dest='lenh', required=True)

    p = sub.add_parser('xem', help='đọc thử một tệp, KHÔNG ghi gì')
    p.add_argument('tep')
    p.add_argument('--tuan', default=None)

    p = sub.add_parser('them', help='lưu một tệp vào kho')
    p.add_argument('tep')
    p.add_argument('--tuan', required=True, help='mã tuần, ví dụ 2026-08-24')
    p.add_argument('--nguoi', required=True, help='tên người lưu')
    p.add_argument('--ghi-chu', default='')
    p.add_argument('--nhan', default=None, help='ví dụ "TUẦN 1"')
    p.add_argument('--nam-hoc', default=None)
    p.add_argument('--hoc-ky', default=None)
    p.add_argument('--dong-y-lech', action='store_true',
                   help='xác nhận đã biết A4 lệch với --tuan')

    p = sub.add_parser('danh-dau', help='đánh dấu một bản dùng được hay không')
    p.add_argument('--tuan', required=True)
    p.add_argument('--ban', type=int, required=True, help='số thứ tự, đếm từ 1')
    p.add_argument('--trang-thai', required=True, choices=list(K.TRANG_THAI))
    p.add_argument('--ly-do', default='',
                   help='BẮT BUỘC khi trạng thái là dung hoặc sai')

    p = sub.add_parser('khuyet-tat',
                       help='ghi nhận một chỗ ghi SAI đã biết của một bản')
    p.add_argument('--tuan', required=True)
    p.add_argument('--ban', type=int, required=True, help='số thứ tự, đếm từ 1')
    p.add_argument('--mo-ta', required=True, help='hỏng chỗ nào, vì sao biết')
    p.add_argument('--nguoi', required=True, help='ai xác nhận')
    p.add_argument('--o', action='append', default=[],
                   help='ô Excel liên quan, gõ nhiều lần: --o D11 --o D18')

    p = sub.add_parser('de-dang', help='bản nào của tuần này ĐĂNG ĐƯỢC')
    p.add_argument('--tuan', required=True)

    p = sub.add_parser('so', help='so một tệp với một bản đã lưu — CHỈ ĐỌC')
    p.add_argument('tep')
    p.add_argument('--tuan', required=True)
    p.add_argument('--ban', type=int, default=None,
                   help='số thứ tự bản; bỏ trống thì lấy bản đánh dấu "dung"')
    p.add_argument('--rong', action='store_true',
                   help='in bảng rộng 84 cột; mặc định in dạng HẸP cho điện thoại')
    p.add_argument('--het', action='store_true',
                   help=f'in hết, không dừng ở {TRAN_O} ô đầu')

    p = sub.add_parser('dang-thu',
                       help='sinh JSON một tuần để đăng — ghi vào thư mục TẠM')
    p.add_argument('--tuan', required=True)
    p.add_argument('--ra', default=None,
                   help='thư mục ra; bỏ trống thì dùng thư mục tạm. KHÔNG nhận docs/')

    p = sub.add_parser('doi-chieu',
                       help='phan_cong trong cauhinh.json có khớp bản thật '
                            'không — CHỈ ĐỌC')
    p.add_argument('--tuan', required=True)
    p.add_argument('--ban', type=int, default=None,
                   help='số thứ tự bản; bỏ trống thì lấy bản đánh dấu "dung"')
    p.add_argument('--cauhinh', default=os.path.join(GOC, 'cauhinh.json'))

    sub.add_parser('liet-ke', help='các tuần đang có trong kho')
    a = ap.parse_args(argv)
    goc = a.kho or K.goc_mac_dinh()
    # Nạp ĐÚNG MỘT LẦN ở điểm vào rồi truyền đối tượng Bang xuống. Để mỗi nơi
    # tự nạp là cách bản cài thứ hai ra đời — xem khop_loc() / _cum_cua().
    bang_mon, bang_gv = BT.nap(GOC)

    if a.lenh == 'danh-dau':
        r = K.danh_dau_ban(goc, a.tuan, a.ban, a.trang_thai, a.ly_do)
        print(('[XONG] ' if r['ok'] else '[DỪNG] ') + r['cau'])
        return 0 if r['ok'] else 1

    if a.lenh == 'khuyet-tat':
        r = K.ghi_khuyet_tat(goc, a.tuan, a.ban, a.mo_ta, a.nguoi, a.o)
        print(('[XONG] ' if r['ok'] else '[DỪNG] ') + r['cau'])
        if r['ok']:
            _in_khuyet_tat(r['ban'], '   ')
        return 0 if r['ok'] else 1

    if a.lenh == 'de-dang':
        ds, tu_choi = K.ban_de_dang(goc, a.tuan)
        if tu_choi:
            print('[KHÔNG ĐĂNG ĐƯỢC] ' + tu_choi)
            return 1
        print(f'{len(ds)} bản ĐĂNG ĐƯỢC của tuần {a.tuan}:')
        for b in ds:
            print(f'   {b.get("tep")}')
            print(f'      lý do đánh dấu "dung": {b.get("ly_do")}')
            _in_khuyet_tat(b)
        return 0

    if a.lenh == 'doi-chieu':
        _keu_bang(bang_mon, bang_gv)
        return _doi_chieu(goc, a, bang_mon, bang_gv)

    if a.lenh == 'dang-thu':
        return _dang_thu(goc, a)

    if a.lenh == 'so':
        _keu_bang(bang_mon)
        return _so(goc, a, bang_mon)

    if a.lenh == 'liet-ke':
        ds = K.liet_ke(goc)
        if not ds:
            print(f'Kho {goc} chưa có tuần nào.')
            return 0
        print(f'{len(ds)} tuần trong {goc}:')
        for x in ds:
            p2 = x['phieu'] or {}
            tt = x.get('theo_trang_thai') or {}
            mo = ' '.join(f'{k}={v}' for k, v in sorted(tt.items())) or '-'
            kt = sum(len(K.khuyet_tat_cua(b)) for b in (p2.get('ban') or []))
            print(f'   {x["ma_tuan"]}  {x["so_ban"]} bản  [{mo}]  '
                  f'{(p2.get("nhan") or "")!r}'
                  + (f'  [{kt} khuyết tật]' if kt else '')
                  + (f'   [PHIẾU HỎNG] {x["loi"]}' if x['loi'] else ''))
            if p2.get('ghi_chu'):
                print(f'      ghi chú tuần: {p2["ghi_chu"]}')
        return 0

    _keu_bang(bang_mon)
    # CHỈ `biet`. Dict `r` dưới đây bị ghi vĩnh viễn vào luu_tru/<tuần>/tach/
    # ở nhánh `them`, mà dau_bo_doc() chỉ băm MÃ NGUỒN doc_tkb.py chứ không
    # băm đối số — nới chỗ này là đổi nội dung bản tách trong khi dấu bộ đọc
    # không đổi một ký tự.
    r = D.doc(a.tep, ten_mon_biet=bang_mon.biet)
    lech = _lech_ngay(r, a.tuan)
    if not _in_bao_cao(r, lech, bang_mon):
        return 1

    if a.lenh == 'xem':
        print('\n   (chế độ xem — không ghi gì xuống đĩa)')
        return 0

    ok, cau = K.kiem_ma_tuan(a.tuan)
    if not ok:
        print(f'\n[DỪNG] {cau}')
        return 1
    if cau:
        print(f'\n[LƯU Ý] {cau}')
    if lech and not a.dong_y_lech:
        print('\n[DỪNG] Chưa lưu gì cả — xem mục LỆCH NGÀY ở trên.')
        return 1

    kq = K.them_ban(
        goc, a.tuan, a.tep, a.nguoi, a.ghi_chu, tach=r, nhan=a.nhan,
        tu_ngay=(r.get('tuan_A4') or {}).get('tu'),
        den_ngay=(r.get('tuan_A4') or {}).get('den'),
        nam_hoc=a.nam_hoc, hoc_ky=a.hoc_ky)
    for x in kq['canh_bao']:
        print(f'[LƯU Ý] {x}')
    print(('\n[XONG] ' if kq['ok'] else '\n[DỪNG] ') + kq['cau'])
    return 0 if kq['ok'] else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 LƯU MỘT TUẦN TKB VÀO KHO — dòng lệnh cho thầy cô
--------------------------------------------------------------------------
   python3 luu_tuan.py xem     <tệp.xlsx>
   python3 luu_tuan.py them    <tệp.xlsx> --tuan 2026-08-24 --nguoi "..."
   python3 luu_tuan.py liet-ke

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

import doc_tkb as D
import kho_tuan as K

GOC = os.path.dirname(os.path.abspath(__file__))


def _bang_ten_mon():
    """Trả (tập chuỗi đã duyệt, câu lỗi|None). Thiếu tệp -> tập rỗng."""
    dd = os.path.join(GOC, 'bang_ten_mon.json')
    if not os.path.exists(dd):
        return set(), None
    try:
        with io.open(dd, encoding='utf-8-sig') as f:
            b = json.load(f)
    except Exception as e:                              # noqa: BLE001
        return set(), f'bang_ten_mon.json hỏng: {type(e).__name__}: {e}'
    ds = b.get('biet') if isinstance(b, dict) else None
    return (set(ds) if isinstance(ds, list) else set()), None


def _in_bao_cao(r, lech_bang=None):
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

    if r['ten_mon_la']:
        print(f'\n   [TÊN MÔN LẠ] {len(r["ten_mon_la"])} chuỗi chưa có trong '
              'bang_ten_mon.json — phần mềm KHÔNG tự gộp:')
        for x in r['ten_mon_la']:
            print(f'      {x!r}')
        print('      Duyệt tay: thêm vào "biet" (tên đúng) hoặc "gop"')
        print('      (chuỗi lạ -> tên chuẩn) trong bang_ten_mon.json.')
    return True


def _lech_ngay(r, ma_tuan):
    t = r.get('tuan_A4') or {}
    if not ma_tuan or not t.get('tu') or t['tu'] == ma_tuan:
        return []
    return [f'Ô A4 trong tệp nói tuần bắt đầu : {t["tu"]}   ({t.get("tho")!r})',
            f'Còn --tuan thầy cô gõ vào là     : {ma_tuan}',
            'Hai cái này KHÁC NHAU. Máy không chọn hộ.',
            'Đúng cái nào thì gõ lại với --tuan <ngày đúng> --dong-y-lech.']


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

    sub.add_parser('liet-ke', help='các tuần đang có trong kho')
    a = ap.parse_args(argv)
    goc = a.kho or K.goc_mac_dinh()

    if a.lenh == 'liet-ke':
        ds = K.liet_ke(goc)
        if not ds:
            print(f'Kho {goc} chưa có tuần nào.')
            return 0
        print(f'{len(ds)} tuần trong {goc}:')
        for x in ds:
            p2 = x['phieu'] or {}
            print(f'   {x["ma_tuan"]}  {x["so_ban"]} bản  '
                  f'{(p2.get("nhan") or "")!r}'
                  + (f'   [PHIẾU HỎNG] {x["loi"]}' if x['loi'] else ''))
        return 0

    biet, loi_bang = _bang_ten_mon()
    if loi_bang:
        print(f'[CẢNH BÁO] {loi_bang}')
        print('           Coi như chưa có tên môn nào được duyệt.')

    r = D.doc(a.tep, ten_mon_biet=biet)
    lech = _lech_ngay(r, a.tuan)
    if not _in_bao_cao(r, lech):
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

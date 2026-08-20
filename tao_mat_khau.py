#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 ĐẶT TÀI KHOẢN CHO MÁY CHỦ QUẢN TRỊ XẾP THỜI KHOÁ BIỂU
--------------------------------------------------------------------------
 Chạy tay, cần bàn phím. Trên Windows: bấm đúp tao_tai_khoan.bat

     python tao_mat_khau.py them              thêm người mới
     python tao_mat_khau.py doi   <tên>       đổi mật khẩu
     python tao_mat_khau.py tat   <tên>       tạm khoá một người
     python tao_mat_khau.py bat   <tên>       mở lại
     python tao_mat_khau.py xoa   <tên>       xoá hẳn
     python tao_mat_khau.py liet-ke           xem có những ai

 KHÔNG có tuỳ chọn --mat-khau, và đó là cố ý: mọi thứ gõ trên dòng lệnh đều
 vào lịch sử shell và hiện ra trong "ps aux" cho mọi người dùng khác trên máy.
 Mật khẩu chỉ nhập qua getpass, không hiện lên màn hình.

 TỆP NÀY ĐƯỢC COMMIT. Nó là mã nguồn, không chứa bí mật nào — bí mật nằm ở
 tai_khoan.json mà nó sinh ra, và tệp đó đã bị .gitignore. Giấu luôn script đi
 thì người cài lại máy sẽ không tạo nổi tài khoản, mà máy chủ lại TỪ CHỐI KHỞI
 ĐỘNG khi thiếu tai_khoan.json — tức là tự khoá mình ra ngoài.
==========================================================================
"""
import argparse
import getpass
import os
import sys

THU_MUC = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, THU_MUC)

import tai_khoan as TK          # noqa: E402

MAC_DINH = os.path.join(THU_MUC, 'tai_khoan.json')


def _dung(cau):
    print(f'\n[LỖI] {cau}\n      Chưa thay đổi gì cả.', file=sys.stderr)
    raise SystemExit(1)


def _hoi_ten(ten):
    if ten is None:
        ten = input('  Tên đăng nhập: ').strip()
    t = TK.chuan_ten(ten)
    if t is None:
        _dung(f'Tên đăng nhập không hợp lệ: {ten!r}\n'
              f'      Chỉ dùng a-z 0-9 . _ - và dài 3–32 ký tự '
              f'(không dấu, không khoảng trắng).')
    if t != str(ten).strip():
        print(f'  (tên được ghi thành "{t}")')
    return t


def _hoi_mat_khau():
    """Hỏi hai lần. Gõ mù nên sai một phím là tự khoá mình khỏi máy chủ."""
    if not sys.stdin.isatty():
        _dung('Cần gõ mật khẩu trực tiếp bằng bàn phím.\n'
              '      Không có bàn phím thì getpass sẽ đọc từ đầu vào và mật '
              'khẩu HIỆN RA màn hình.')
    for _ in range(3):
        mk = getpass.getpass('  Mật khẩu mới: ')
        loi = TK.kiem_mat_khau(mk)
        if loi:
            print(f'  [!] {loi}')
            continue
        if mk != getpass.getpass('  Gõ lại mật khẩu: '):
            print('  [!] Hai lần gõ không giống nhau. Thử lại.')
            continue
        return mk
    _dung('Đã thử 3 lần không xong.')


def _ghi(dd, ds, cau):
    TK.ghi(dd, ds)
    print(f'\n{cau}')
    print(f'  Tệp: {dd}')
    print('  Tệp này chứa mật khẩu đã băm — ĐỪNG gửi cho ai, ĐỪNG đưa lên '
          'GitHub.')
    print('  (nó đã được .gitignore chặn sẵn)')
    print('\n  Bây giờ chạy:  python web.py')


def _tim(ds, ten):
    for i, bg in enumerate(ds):
        if TK.chuan_ten(bg.get('ten_dang_nhap')) == ten:
            return i
    return -1


def lam(viec, ten, dd):
    ds = TK.doc_tho(dd)

    if viec == 'liet-ke':
        if not ds:
            print('Chưa có tài khoản nào. Chạy: python tao_mat_khau.py them')
            return
        print(f'{len(ds)} tài khoản trong {dd}:\n')
        print(f'  {"TÊN ĐĂNG NHẬP":<24}{"TRẠNG THÁI":<12}NGÀY TẠO')
        print('  ' + '-' * 58)
        for bg in ds:
            tt = 'đang bật' if bg.get('bat', True) else 'ĐANG TẮT'
            print(f'  {bg.get("ten_dang_nhap", "?"):<24}{tt:<12}'
                  f'{bg.get("ngay_tao", "?")}')
        so_bat = sum(1 for b in ds if b.get('bat', True))
        print(f'\n  {so_bat} tài khoản đang bật.')
        if not so_bat:
            print('  [!] KHÔNG có tài khoản nào bật — máy chủ sẽ không khởi '
                  'động được.')
        return

    ten = _hoi_ten(ten)
    i = _tim(ds, ten)

    if viec == 'them':
        if i >= 0:
            _dung(f'Đã có tài khoản "{ten}".\n'
                  f'      Muốn đổi mật khẩu thì dùng: '
                  f'python tao_mat_khau.py doi {ten}')
        print(f'\n  Đặt mật khẩu cho "{ten}".')
        print('  Mật khẩu sẽ KHÔNG hiện ra khi gõ — cứ gõ rồi bấm Enter.')
        ds.append(TK.ban_ghi_moi(ten, _hoi_mat_khau()))
        # Thêm người KHÔNG đụng tới ai khác: ds là danh sách, chỉ append.
        _ghi(dd, ds, f'Đã thêm tài khoản "{ten}". '
                     f'Tổng cộng {len(ds)} tài khoản.')
        return

    if i < 0:
        _dung(f'Không có tài khoản nào tên "{ten}".\n'
              f'      Xem danh sách: python tao_mat_khau.py liet-ke')

    if viec == 'doi':
        print(f'\n  Đổi mật khẩu cho "{ten}".')
        ds[i] = TK.ban_ghi_moi(ten, _hoi_mat_khau())
        ds[i]['ngay_tao'] = ds[i].get('ngay_tao')
        _ghi(dd, ds, f'Đã đổi mật khẩu cho "{ten}".')

    elif viec in ('tat', 'bat'):
        muon = (viec == 'bat')
        if bool(ds[i].get('bat', True)) == muon:
            print(f'Tài khoản "{ten}" vốn đã {"bật" if muon else "tắt"} rồi. '
                  f'Không đổi gì.')
            return
        if not muon and sum(1 for b in ds if b.get('bat', True)) <= 1:
            _dung(f'"{ten}" là tài khoản BẬT cuối cùng.\n'
                  f'      Tắt nó thì máy chủ sẽ không khởi động lại được nữa.\n'
                  f'      Hãy thêm một tài khoản khác trước.')
        ds[i]['bat'] = muon
        _ghi(dd, ds, f'Đã {"bật" if muon else "TẮT"} tài khoản "{ten}". '
                     f'Các tài khoản khác không đổi.')

    elif viec == 'xoa':
        if sum(1 for b in ds if b.get('bat', True)) <= 1 and \
                ds[i].get('bat', True):
            _dung(f'"{ten}" là tài khoản BẬT cuối cùng.\n'
                  f'      Xoá nó thì máy chủ sẽ không khởi động lại được nữa.')
        ds.pop(i)
        _ghi(dd, ds, f'Đã xoá tài khoản "{ten}". Còn {len(ds)} tài khoản.')


def main():
    ap = argparse.ArgumentParser(
        description='Đặt tài khoản cho máy chủ quản trị xếp thời khoá biểu')
    ap.add_argument('viec', choices=['them', 'doi', 'tat', 'bat', 'xoa',
                                     'liet-ke'])
    ap.add_argument('ten', nargs='?', default=None)
    ap.add_argument('--tep', default=MAC_DINH,
                    help='đường dẫn tai_khoan.json (dành cho ca thử)')
    a = ap.parse_args()
    print('=' * 62)
    print(' ĐẶT TÀI KHOẢN — MÁY CHỦ XẾP THỜI KHOÁ BIỂU'.center(62))
    print('=' * 62)
    lam(a.viec, a.ten, os.path.abspath(a.tep))


if __name__ == '__main__':
    main()

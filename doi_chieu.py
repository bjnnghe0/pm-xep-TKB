#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 ĐỐI CHIẾU PHÂN CÔNG: cauhinh.json  ↔  MỘT BẢN TKB THẬT CỦA TRƯỜNG
--------------------------------------------------------------------------
 Chạy:  python3 luu_tuan.py doi-chieu --tuan 2026-08-24

 CHỈ ĐỌC. Mô-đun này không ghi một byte nào, không sửa `cauhinh.json`,
 không sửa tệp trong `luu_tru/`, không biết `docs/` tồn tại.

 KHÁC `luu_tuan._so()`, đừng nhập hai cái làm một:
   `_so()`      khoá `(lớp, thứ, tiết)` — so TỪNG Ô, hỏi "ô này đổi chưa".
   `doi_chieu`  khoá `(lớp, môn)`       — so SỐ TIẾT/TUẦN và TÊN GIÁO VIÊN,
                hỏi "khai báo trong cauhinh.json có khớp thực tế không".
 `phan_cong` không có `thu`/`tiet` nên không dùng lại được khoá của `_so`.

 CÓ ÁP BẢNG TÊN (`bang_ten.py`), vì đây là ĐỐI CHIẾU. Tệp gốc giữ nguyên
 chữ nhà trường gõ — việc gộp chỉ xảy ra trong bộ nhớ, lúc so.

 BA BẢNG, VÀ RANH GIỚI GIỮA CHÚNG LÀ CÓ CHỦ Ý:
   (a) TÊN MÔN   — chuỗi nào chỉ một bên có (sau khi áp bảng gộp)
   (b) SỐ TIẾT   — mỗi (lớp, môn), chỉ in dòng lệch
   (c) GIÁO VIÊN — mỗi (lớp, môn) **có ở CẢ HAI bên** mà tên GV khác

 Vì sao (c) chỉ hỏi những cặp có ở cả hai bên: một cặp chỉ một bên có thì
 bên kia KHÔNG CÓ giáo viên nào để so — đó là sự kiện của bảng (b), và kể
 lại nó ở (c) là đếm một chuyện hai lần. Số cặp lệch-một-bên vẫn được in
 ra, kèm câu trỏ về (b), để không có gì bị giấu.
==========================================================================
"""
import collections

# Khoá của một dòng phân công. Đổi nó là đổi cả ba bảng.
KHOA = ('lop', 'mon')


def _mot_gv(cac):
    """Tập GV của một (lớp, môn) -> chuỗi để in. Rỗng -> None."""
    return '/'.join(sorted(cac)) if cac else None


def tu_ban_tach(tach, bang_mon, bang_gv):
    """Bản tách của một tuần -> (số tiết theo (lớp,môn), GV theo (lớp,môn)).

       ĐÂY LÀ BẢN CÀI DUY NHẤT của phép gộp "bản tách -> đếm tiết theo
       khoá". Ba nơi cần nó: lệnh `doi-chieu`, việc sinh tệp mốc
       `phan_cong_tuan1.json`, và bất cứ ai sau này muốn hỏi cùng câu hỏi.
       Chép bản thứ hai là đúng bài học `khop_loc()` / `_cum_cua()`.

       KHÔNG BAO GIỜ NÉM: ô sai hình dạng thì bỏ qua chứ không làm vỡ cả
       lượt đối chiếu — bản tách hỏng là đầu vào mong đợi ở đây.
    """
    dem = collections.Counter()
    gv = collections.defaultdict(set)
    for o in (tach.get('o') or []) if isinstance(tach, dict) else []:
        if not isinstance(o, dict):
            continue
        lop = o.get('lop')
        mon = bang_mon.chuan(o.get('mon'))
        if not lop or not mon:
            continue
        k = (lop, mon)
        dem[k] += 1
        t = o.get('gv')
        if t:
            gv[k].add(bang_gv.chuan(t))
    return dict(dem), {k: set(v) for k, v in gv.items()}


def tu_cau_hinh(cfg):
    """`cauhinh.json` -> cùng hai dict như `tu_ban_tach()`.

       `phan_cong` là dict: lớp -> [[tên môn, GV viết tắt, số tiết/tuần]].
       KHÔNG áp bảng tên ở đây — `cauhinh.json` LÀ dạng chuẩn.
    """
    dem, gv = {}, {}
    pc = (cfg or {}).get('phan_cong') or {}
    for lop, cac in pc.items():
        if lop.startswith('_') or not isinstance(cac, list):
            continue
        for muc in cac:
            if not isinstance(muc, list) or len(muc) < 3:
                continue
            mon, ten_gv, so = muc[0], muc[1], muc[2]
            if not isinstance(mon, str) or not isinstance(so, int):
                continue
            dem[(lop, mon)] = so
            gv[(lop, mon)] = {ten_gv} if ten_gv else set()
    return dem, gv


def so(dem_tep, gv_tep, dem_cfg, gv_cfg):
    """Ba bảng. Trả dict thuần — không in, không ghi, không ném."""
    mon_tep = {m for _, m in dem_tep}
    mon_cfg = {m for _, m in dem_cfg}
    chung = mon_tep & mon_cfg
    moi_khoa = sorted(set(dem_tep) | set(dem_cfg))

    a_tep = sorted(mon_tep - mon_cfg)
    a_cfg = sorted(mon_cfg - mon_tep)

    b = [{'lop': l, 'mon': m,
          'tep': dem_tep.get((l, m)), 'cfg': dem_cfg.get((l, m))}
         for l, m in moi_khoa if dem_tep.get((l, m)) != dem_cfg.get((l, m))]

    c, mot_ben = [], []
    for l, m in moi_khoa:
        co_tep, co_cfg = (l, m) in dem_tep, (l, m) in dem_cfg
        if not (co_tep and co_cfg):
            mot_ben.append({'lop': l, 'mon': m,
                            'ben': 'tệp' if co_tep else 'cauhinh'})
            continue
        x, y = gv_tep.get((l, m), set()), gv_cfg.get((l, m), set())
        if x != y:
            c.append({'lop': l, 'mon': m,
                      'tep': _mot_gv(x), 'cfg': _mot_gv(y)})

    # TRỤC THỨ HAI, và nó KHÔNG có ngoại lệ nào. Trục (lớp, môn) có thể bị
    # bịt miệng bằng cách khai thêm ngoại lệ; trục (lớp, GV) thì không —
    # nó hỏi "cô này dạy lớp này mấy tiết", một câu mà việc ghi thiếu nhãn
    # môn không đụng tới. Sạch ở đây là bằng chứng ĐỘC LẬP rằng các luật
    # gộp tên là đúng: sai một luật thôi thì con số đã không sạch.
    def theo_lop_gv(dem, gv):
        ra = collections.Counter()
        for k, n in dem.items():
            for t in gv.get(k) or ():
                ra[(k[0], t)] += n
        return ra
    lg_tep, lg_cfg = theo_lop_gv(dem_tep, gv_tep), theo_lop_gv(dem_cfg, gv_cfg)
    lg = [{'lop': l, 'gv': t, 'tep': lg_tep.get((l, t)), 'cfg': lg_cfg.get((l, t))}
          for l, t in sorted(set(lg_tep) | set(lg_cfg))
          if lg_tep.get((l, t)) != lg_cfg.get((l, t))]

    return {
        'a_chi_tep': a_tep, 'a_chi_cauhinh': a_cfg,
        'b_so_tiet': b, 'c_giao_vien': c, 'mot_ben': mot_ben,
        'lop_gv': lg,
        'so_cap_tep': len(dem_tep), 'so_cap_cauhinh': len(dem_cfg),
        'so_tiet_tep': sum(dem_tep.values()),
        'so_tiet_cauhinh': sum(dem_cfg.values()),
        'so_mon_chung': len(chung),
    }


# ==========================================================================
def in_hep(kq, rong=39):
    """In ba bảng, dạng HẸP cho điện thoại. Trả tổng số dòng lệch."""
    r = int(rong)
    print(f'\n  {kq["so_cap_tep"]} cặp (lớp,môn) ở tệp · '
          f'{kq["so_cap_cauhinh"]} ở cauhinh')
    print(f'  {kq["so_tiet_tep"]} tiết ở tệp · '
          f'{kq["so_tiet_cauhinh"]} ở cauhinh')

    print('\n(a) TÊN MÔN')
    if not kq['a_chi_tep'] and not kq['a_chi_cauhinh']:
        print('  (không lệch)')
    for nhan, ds in (('chỉ TỆP có:', kq['a_chi_tep']),
                     ('chỉ cauhinh có:', kq['a_chi_cauhinh'])):
        if ds:
            print(f'  {nhan}')
            for m in ds:
                print(f'    {m[:r - 4]}')

    print('\n(b) SỐ TIẾT   tệp/cauhinh')
    if not kq['b_so_tiet']:
        print('  (không lệch)')
    for x in kq['b_so_tiet']:
        t = '-' if x['tep'] is None else x['tep']
        c = '-' if x['cfg'] is None else x['cfg']
        print(f'  {x["lop"]:<5}{x["mon"][:19]:<20}{t}/{c}')

    print('\n(c) GIÁO VIÊN')
    print('    (cặp có ở CẢ HAI bên)')
    if not kq['c_giao_vien']:
        print('  (không lệch)')
    for x in kq['c_giao_vien']:
        print(f'  {x["lop"]} {x["mon"][:19]}')
        print(f'    tệp    : {x["tep"]}')
        print(f'    cauhinh: {x["cfg"]}')
    if kq['mot_ben']:
        print(f'  {len(kq["mot_ben"])} cặp chỉ MỘT bên có, nên')
        print('  không có GV để so — xem bảng (b):')
        for x in kq['mot_ben']:
            print(f'    {x["lop"]} {x["mon"][:16]}')
            print(f'      (chỉ {x["ben"]} có)')

    print('\n(d) TRỤC (lớp, GV) — không ngoại lệ')
    if not kq['lop_gv']:
        print('  (không lệch)')
    for x in kq['lop_gv']:
        print(f'  {x["lop"]} {x["gv"]}: {x["tep"]}/{x["cfg"]}')

    n = (len(kq['a_chi_tep']) + len(kq['a_chi_cauhinh'])
         + len(kq['b_so_tiet']) + len(kq['c_giao_vien']) + len(kq['lop_gv']))
    print(f'\n  TỔNG: {n} dòng lệch.')
    return n

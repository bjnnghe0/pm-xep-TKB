#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ: BỘ SINH DỮ LIỆU ĐĂNG — KHÔNG CÓ LỐI VÒNG QUA CỬA
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_sinh_dang.py

 CA 2 LÀ CA QUAN TRỌNG NHẤT, VÀ NÓ CANH KIẾN TRÚC CHỨ KHÔNG CANH KẾT QUẢ.

 Vì sao phải canh kiến trúc: một lối vòng (`phieu['ban'][0]`) cho ra kết
 quả ĐÚNG trong mọi tuần chỉ có một bản — tức gần như mọi tuần. Nó chỉ sai
 đúng vào hôm có bản SAI, mà hôm đó thì hậu quả là đăng nhầm ra cho cả
 trường đọc, và git nhớ vĩnh viễn. Ca thử canh kết quả sẽ XANH suốt cho tới
 đúng hôm đó. Vì vậy phải canh chính con đường.

 NGOẠI LỆ CÓ CHỦ Ý VỚI MỘT BẤT BIẾN. Kỷ luật ca thử ghi "KHÔNG khẳng định
 trên VĂN BẢN MÃ NGUỒN". Ở đây điều cần canh CHÍNH LÀ hình dạng của mã —
 "không có đường nào khác dẫn tới dữ liệu" là một mệnh đề về mã, không
 phải về hành vi. Bù lại, CA 2 đi trên **cây cú pháp** (`ast`) chứ không
 khớp chuỗi, nên chú thích không đánh lừa được nó — khác hẳn nếp hỏng 4.
==========================================================================
"""
import ast
import inspect
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
GOC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(GOC, 'tests'))

import kho_tuan as K                                             # noqa: E402
import sinh_dang as SD                                           # noqa: E402
from thu_kho_tuan import dung_xlsx, o_mau, _them_doc_props       # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def dat_dong_ho_canh(giay=180):
    """Bộ thử không bao giờ được phép TREO — hết giờ thì ĐỎ. Xem CLAUDE.md."""
    def bao():
        time.sleep(giay)
        print(f'\n[HẾT GIỜ] Quá {giay} giây — coi như ĐỎ, thoát.', flush=True)
        os._exit(1)
    threading.Thread(target=bao, daemon=True).start()


def _dung_tuan(goc, ma, tt, ly_do, so_tiet=3, tm=None):
    """Dựng một tuần có đúng một bản, đánh dấu sẵn. Trả kết quả them_ban."""
    import doc_tkb as D
    t = dung_xlsx(os.path.join(tm, f'{ma}-{tt}-{so_tiet}.xlsx'),
                  o_mau(so_tiet=so_tiet))
    a = K.them_ban(goc, ma, t, 'người thử', tach=D.doc(t))
    if a.get('ok') and tt != K.TRANG_THAI_MAC_DINH:
        p, _ = K.doc_phieu_ky(goc, ma)
        K.danh_dau_ban(goc, ma, len((p or {}).get('ban') or []), tt, ly_do)
    return a


# ==========================================================================
def ca_1_hanh_vi(tm):
    print('\nCA 1 — HÀNH VI: chỉ bản "dung" mới ra được dữ liệu')
    print('-' * 74)
    goc = os.path.join(tm, 'kho1')

    _dung_tuan(goc, '2026-01-05', 'sai', 'ca thử: bản này sai', 3, tm)
    d, tu_choi = SD.du_lieu_dang(goc, '2026-01-05')
    kiem(d is None and bool(tu_choi),
         'Tuần CHỈ có bản "sai" -> KHÔNG sinh được gì')
    kiem('sai' in (tu_choi or ''), 'và câu từ chối nói rõ đang có bản sai')

    _dung_tuan(goc, '2026-01-12', K.TRANG_THAI_MAC_DINH, '', 3, tm)
    d, tu_choi = SD.du_lieu_dang(goc, '2026-01-12')
    kiem(d is None and bool(tu_choi),
         'Tuần chỉ có bản "chua_ro" -> cũng KHÔNG sinh được gì (fail-closed)')

    _dung_tuan(goc, '2026-01-19', 'dung', 'ca thử: bản này dùng được', 4, tm)
    d, tu_choi = SD.du_lieu_dang(goc, '2026-01-19')
    kiem(isinstance(d, dict) and tu_choi is None,
         f'Tuần có bản "dung" -> sinh được — {type(d).__name__}')
    if isinstance(d, dict):
        kiem(len(d.get('o') or []) > 1, f'Có {len(d.get("o") or [])} ô')
        kiem(d.get('ma_tuan') == '2026-01-19', 'Ghi đúng mã tuần')
        ng = d.get('nguon') or {}
        kiem(bool(ng.get('sha256')) and bool(ng.get('gio_luu')),
             'Kèm nguồn: SHA-256 và giờ lưu — hai giá trị MÁY SINH')
        kiem('ly_do_dung' not in ng and 'ly_do' not in ng,
             f'và KHÔNG kèm lý do — chữ tự do dừng ở phiếu; nguồn còn '
             f'{sorted(ng)}')

    kiem(SD.du_lieu_dang(goc, '2026-02-02')[0] is None,
         'Tuần chưa có -> trả None, không ném')
    kiem(SD.du_lieu_dang(os.path.join(tm, 'khong-co'), '2026-01-19')[0] is None,
         'Kho chưa có -> trả None, không ném')

    # hai bản "dung" -> KHÔNG đoán
    _dung_tuan(goc, '2026-01-19', 'dung', 'ca thử: bản thứ hai', 5, tm)
    d, tu_choi = SD.du_lieu_dang(goc, '2026-01-19')
    kiem(d is None and bool(tu_choi),
         'HAI bản "dung" -> KHÔNG đoán bản nào, từ chối sinh')


def ca_1b_khuyet_tat_khong_ro_ra_cong_khai(tm):
    print('\nCA 1b — khuyết tật của bản KHÔNG rò ra dữ liệu công khai')
    print('-' * 74)
    goc, MA = os.path.join(tm, 'kho1b'), '2026-03-02'
    _dung_tuan(goc, MA, 'dung', 'ca thử: bản này dùng được', 3, tm)
    r = K.ghi_khuyet_tat(goc, MA, 1,
                         'CHỮ TỰ DO KHÔNG ĐƯỢC RA CÔNG KHAI', 'người thử')
    kiem(r.get('ok') is True, 'Ghi được một khuyết tật mang chữ tự do')
    d, tu_choi = SD.du_lieu_dang(goc, MA)
    kiem(d is not None and not tu_choi,
         f'Bản vẫn đăng được sau khi ghi khuyết tật — {tu_choi}')
    if d is None:
        return
    tho = json.dumps(d, ensure_ascii=False)
    kiem('khuyet_tat' not in tho,
         "Dữ liệu đăng KHÔNG chứa khoá 'khuyet_tat'")
    kiem('CHỮ TỰ DO KHÔNG ĐƯỢC RA CÔNG KHAI' not in tho,
         'và không chứa NỘI DUNG khuyết tật — chữ tự do phải dừng ở phiếu')


def _cac_chuoi(v):
    """Mọi chuỗi nằm ở BẤT KỲ độ sâu nào trong một giá trị JSON."""
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        ra = []
        for k, x in v.items():
            ra += _cac_chuoi(x)
        return ra
    if isinstance(v, (list, tuple)):
        ra = []
        for x in v:
            ra += _cac_chuoi(x)
        return ra
    return []


def _tuan_nhieu_gv(goc, ma, tm, ten_gv):
    """Một tuần có ĐÚNG MỘT bản "dung", các ô mang NHIỀU tên GV khác nhau.

       `o_mau()` của thu_kho_tuan chỉ dùng một tên (`T.Thử`) nên không dùng
       được ở đây: mốc so của CA 1c là TẬP TÊN NGƯỜI, mà một tập một phần
       tử thì phép kiểm "danh sách gom sẵn" mất hết khả năng phân biệt.
       Tên dựng ra CỐ Ý không trùng gì trong `cauhinh.json`.
    """
    import doc_tkb as D
    o = {'A3': 'THỜI KHÓA BIỂU THỬ', 'A4': 'TUẦN 9 (05/1/2026-10/1/2026)'}
    for i, g in enumerate(ten_gv):
        o[f'D{8 + i}'] = f'Môn Thử {i + 1} ({g})'
    for c in 'DEFGHI':
        o[f'{c}43'] = f'=COUNTA({c}8:{c}42)'
    t = dung_xlsx(os.path.join(tm, f'{ma}-nhieu-gv.xlsx'), o)
    K.them_ban(goc, ma, t, 'người thử', tach=D.doc(t))
    p, _ = K.doc_phieu_ky(goc, ma)
    K.danh_dau_ban(goc, ma, len((p or {}).get('ban') or []), 'dung',
                   'ca thử: bản này dùng được')


def ca_1c_khong_dang_danh_sach_nguoi_gom_san(tm):
    print('\nCA 1c — dữ liệu đăng KHÔNG chở DANH SÁCH NGƯỜI gom sẵn')
    print('-' * 74)
    goc, MA = os.path.join(tm, 'kho1c'), '2026-04-06'
    TEN_GV = ['T.Một', 'T.Hai', 'T.Ba', 'T.Bốn']
    _tuan_nhieu_gv(goc, MA, tm, TEN_GV)
    d, tu_choi = SD.du_lieu_dang(goc, MA)
    kiem(isinstance(d, dict) and not tu_choi,
         f'Sinh được dữ liệu đăng — {tu_choi}')
    if not isinstance(d, dict):
        return

    # MỐC SO dựng từ CHÍNH 144 ô, không từ hằng số nào (nếp hỏng 12): ô đổi
    # thì mốc đổi theo. Cột `gv` là cột thứ mấy thì HỎI `truong_o`, đừng đếm
    # tay — đếm tay là ghim lại đúng thứ tự mà `TRUONG_O` được phép đổi.
    to = list(d.get('truong_o') or [])
    kiem('gv' in to, f'Mỗi ô vẫn khai cột tên GV — truong_o = {to}')
    if 'gv' not in to:
        return
    i_gv = to.index('gv')
    ten_nguoi = {r[i_gv] for r in (d.get('o') or []) if r[i_gv]}

    # ĐIỀU KIỆN TIÊN QUYẾT. Mốc so là một TẬP; tập một phần tử (hoặc rỗng)
    # làm mọi phép kiểm dưới đây vẫn XANH mà không kiểm gì cả — bẫy
    # `n_uyen == 0`, mục 7 của danh sách kiểm.
    kiem(len(ten_nguoi) > 1,
         f'Điều kiện tiên quyết: bản thử có {len(ten_nguoi)} tên GV KHÁC '
         f'nhau trong các ô — mốc so đủ sức phân biệt')

    # (a) TÊN TRONG TỪNG Ô THÌ GIỮ — tờ TKB dán ở trường xưa nay vẫn vậy.
    kiem(ten_nguoi == set(TEN_GV),
         f'Tên GV trong TỪNG Ô còn nguyên — {sorted(ten_nguoi)}')

    # (b) Nhưng KHÔNG khoá cấp trên nào được chở tên người. Đi trên MỌI khoá
    #     chứ không hỏi đích danh 'gv': đổi tên khoá thành 'giao_vien' hay
    #     'danh_sach' là lách được một phép kiểm hỏi đích danh.
    ro = []
    for k, v in d.items():
        if k == 'o':
            continue
        co = sorted(set(_cac_chuoi(v)) & ten_nguoi)
        if co:
            ro.append((k, co))
    kiem(not ro,
         f'KHÔNG khoá cấp trên nào chở tên người — rò: {ro}')

    # (c) Và nói đích danh khoá đã bỏ. KHÔNG thừa so với (b): `gv: []` lọt
    #     qua (b) mà vẫn là khoá đã bị người dùng bỏ, quay lại dưới dạng rỗng.
    kiem('gv' not in d,
         f"Khoá 'gv' đã bỏ hẳn — còn {len(d)} khoá cấp trên")

    # (d) Trang xem MẤT gì? Không mất gì: dựng lại được từ chính các ô.
    dung_lai = sorted({r[i_gv] for r in d['o'] if r[i_gv]})
    kiem(dung_lai == sorted(ten_nguoi),
         f'Trang dựng lại được danh sách lúc chạy từ {len(d["o"])} ô — '
         f'{dung_lai}')

    # (e) LỚP LỖI RỘNG HƠN: không khoá cấp trên nào được là BẢN SAO của
    #     một CỘT trong `o`. Bắt cả `gv` lẫn `lop` lẫn bất cứ cột nào ai
    #     đó gom sẵn ngày mai — hỏi đích danh hai cái tên thì cột thứ ba
    #     vẫn lọt. `truong_o` KHÁC HẠNG và cố ý được tha: nó là danh sách
    #     TÊN CỘT, không dựng từ `o`, và bỏ nó thì trang phải ghim cứng
    #     thứ tự cột trong JS — đúng bẫy khop_loc()/_cum_cua().
    cot = {t: sorted({r[j] for r in d['o'] if r[j] is not None})
           for j, t in enumerate(to)}
    ban_sao = []
    for k, v in d.items():
        if k in ('o', 'truong_o') or not isinstance(v, list):
            continue
        for t, gt in cot.items():
            if gt and sorted(v) == gt:
                ban_sao.append((k, f'= cột {t!r}'))
    kiem(not ban_sao,
         f'KHÔNG khoá cấp trên nào là BẢN SAO của một cột trong `o` — '
         f'{ban_sao}')
    kiem('lop' not in d,
         f"Cụ thể: khoá 'lop' cũng đã bỏ — còn {len(d)} khoá cấp trên")


def _tiem_dau(v, giu, dau, duong=''):
    """Thay MỌI chuỗi trong phiếu bằng một dấu duy nhất, trừ `giu`.

       Đi đệ quy nên trường chữ tự do mới thêm vào phiếu ngày mai cũng bị
       tiêm mà không phải sửa ca thử — đó là cả điểm của cách làm này. Một
       danh sách tên trường viết tay thì đúng hôm nay và sai từ ngày mai.
    """
    if isinstance(v, dict):
        for k in list(v):
            if k in giu:
                continue
            x = v[k]
            if isinstance(x, str) and x:
                m = f'CHU-TU-DO-{len(dau):02d}-KHONG-DUOC-RA-CONG-KHAI'
                dau[m] = f'{duong}{k}'
                v[k] = m
            else:
                _tiem_dau(x, giu, dau, f'{duong}{k}.')
    elif isinstance(v, list):
        for i, x in enumerate(v):
            if isinstance(x, str) and x:
                m = f'CHU-TU-DO-{len(dau):02d}-KHONG-DUOC-RA-CONG-KHAI'
                dau[m] = f'{duong}[{i}]'
                v[i] = m
            else:
                _tiem_dau(x, giu, dau, f'{duong}[{i}].')


def ca_1d_khong_chu_tu_do_nao_qua_cua(tm):
    print('\nCA 1d — KHÔNG trường chữ tự do nào của phiếu qua được cửa đăng')
    print('-' * 74)
    goc, MA = os.path.join(tm, 'kho1d'), '2026-05-04'
    _dung_tuan(goc, MA, 'dung', 'ca thử: bản này dùng được', 4, tm)
    K.ghi_khuyet_tat(goc, MA, 1, 'khuyết tật của ca thử', 'người thử')
    # `them_ban` không đòi các khai báo cấp TUẦN, nên kho thử mặc định
    # không có chúng — mà đó lại chính là bốn trường chữ tự do cần thử.
    # `sua_tuan()` là đường DUY NHẤT ghi được chúng (đã kiểm: không mô-đun
    # nào khác gọi nó), nên dựng qua đúng đường đó.
    K.sua_tuan(goc, MA, nhan='TUẦN 3', nam_hoc='2026-2027', hoc_ky='1',
               ghi_chu='ghi chú riêng của khoa, không phải để ai đọc')

    dd = os.path.join(K.thu_muc_tuan(goc, MA), 'phieu.json')
    with io.open(dd, encoding='utf-8') as f:
        p = json.load(f)

    # GIỮ NGUYÊN: trường có KHUÔN (thử riêng ở phần B), hai đường dẫn tệp
    # (tiêm vào là hỏng chỗ tìm tệp, thử nhầm thứ), và ba giá trị MÁY SINH
    # vốn ĐƯỢC PHÉP ra ngoài.
    #
    # ⚠ GHIM LITERAL, KHÔNG viết `set(SD.KHUON_TUAN)`. Bản đầu viết vậy và
    # đó là nếp hỏng 12 nguyên bản: mốc so lấy từ CHÍNH hằng đang bị canh.
    # Đo 26/8/2026 trên bản vá "thêm 'ghi_chu' vào KHUON_TUAN": tập tiêm tụt
    # từ 7 dấu xuống 6 (`ghi_chu` tự rơi ra khỏi tập tiêm), mục hành vi vẫn
    # in `[ĐẠT] — rò: []`, trong khi `du_lieu_dang()` THẬT SỰ đăng
    # `ghi_chu = 'CHỮ TỰ DO CÓ TÊN CÔ X'`. Chỉ mục nêu ĐÍCH DANH `ghi_chu`
    # ở phần C là đỏ — tức lưới bắt được một CÁI TÊN, không bắt được LỚP.
    KHUON_DA_DUYET = ('ma_tuan', 'nhan', 'tu_ngay', 'den_ngay', 'nam_hoc',
                      'hoc_ky')
    kiem(tuple(sorted(SD.KHUON_TUAN)) == tuple(sorted(KHUON_DA_DUYET)),
         f'KHUON_TUAN ĐÚNG BẰNG bộ đã duyệt — thừa '
         f'{sorted(set(SD.KHUON_TUAN) - set(KHUON_DA_DUYET))}, thiếu '
         f'{sorted(set(KHUON_DA_DUYET) - set(SD.KHUON_TUAN))}')
    giu = set(KHUON_DA_DUYET) | {'tep', 'tach', 'sha256', 'gio_luu', 'bo_doc',
                                 'trang_thai'}
    dau = {}
    _tiem_dau(p, giu, dau)
    with io.open(dd, 'w', encoding='utf-8') as f:
        json.dump(p, f, ensure_ascii=False)

    kiem(len(dau) > 4,
         f'Điều kiện tiên quyết: tiêm được {len(dau)} dấu vào phiếu — '
         f'{sorted(dau.values())}')

    d, tu_choi = SD.du_lieu_dang(goc, MA)
    kiem(isinstance(d, dict) and not tu_choi,
         f'Bản vẫn đăng được sau khi phiếu đầy chữ tự do — {tu_choi}')
    if not isinstance(d, dict):
        return
    tho = json.dumps(d, ensure_ascii=False)
    ro = sorted(dau[m] for m in dau if m in tho)
    kiem(not ro, f'KHÔNG dấu nào trong {len(dau)} dấu ra tới bản đăng — '
                 f'rò: {ro}')

    # Đường dẫn tệp mang tên tệp gốc của trường — cũng không được ra.
    ten_tep = (p.get('ban') or [{}])[0].get('tep') or ''
    kiem(bool(ten_tep) and ten_tep not in tho,
         'và tên tệp gốc cũng không ra — đường dẫn là siêu dữ liệu của kho')

    # ---- B. Trường CÓ KHUÔN: sai khuôn thì TỪ CHỐI, không lặng lẽ bỏ ----
    with io.open(dd, encoding='utf-8') as f:
        p2 = json.load(f)
    p2['nhan'] = 'TUẦN 1 — nhắc cô X nộp sổ đầu bài trước Thứ Sáu'
    with io.open(dd, 'w', encoding='utf-8') as f:
        json.dump(p2, f, ensure_ascii=False)
    d2, tc2 = SD.du_lieu_dang(goc, MA)
    kiem(d2 is None and bool(tc2),
         'Trường CÓ KHUÔN mà bị gõ chữ tự do vào -> TỪ CHỐI ĐĂNG cả bản')
    kiem('nhan' in (tc2 or ''),
         f'và câu từ chối gọi ĐÍCH DANH trường sai khuôn — {(tc2 or "")[:60]}')

    # ---- C. `_cua_tuan` không lấy được khoá chưa khai khuôn -------------
    kiem('ghi_chu' in p, 'Phiếu THẬT SỰ có khoá ghi_chu cấp tuần')
    kiem(SD._cua_tuan(goc, MA, 'ghi_chu') is None,
         'nhưng _cua_tuan() KHÔNG lấy được nó — cửa khoá ở tầng dưới nữa')


def ca_1e_khai_nguon_noi_ngay_truong_sua(tm):
    print('\nCA 1e — dòng KHAI NGUỒN nói ngày TRƯỜNG SỬA, hoặc nói là không có')
    print('-' * 74)
    import doc_tkb as D
    NGAY = '2026-08-18T17:06:19Z'

    # ---- A. Tệp CÓ docProps -> câu phải mang đúng ngày đó -------------
    goc, MA = os.path.join(tm, 'kho1e'), '2026-06-01'
    t = dung_xlsx(os.path.join(tm, 'co-ngay.xlsx'), o_mau(so_tiet=4))
    _them_doc_props(t, **{'dcterms:modified': NGAY})
    K.them_ban(goc, MA, t, 'người thử', tach=D.doc(t))
    K.danh_dau_ban(goc, MA, 1, 'dung', 'ca thử: bản này dùng được')
    d, tu_choi = SD.du_lieu_dang(goc, MA)
    kiem(isinstance(d, dict) and not tu_choi, f'Sinh được — {tu_choi}')
    if not isinstance(d, dict):
        return
    cau = d.get('khai_nguon') or ''
    kiem(NGAY in cau, f'Câu khai nguồn mang ĐÚNG ngày trường sửa — {cau!r}')

    # MỐC SO là giá trị CHỤP TRƯỚC, không phải "khác rỗng" (nếp hỏng 13):
    # `gio_luu` thật của bản này, đọc ra rồi mới đòi nó VẮNG trong câu.
    gio_luu = (d.get('nguon') or {}).get('gio_luu')
    kiem(isinstance(gio_luu, str) and gio_luu,
         f'Điều kiện tiên quyết: bản có gio_luu để mà so — {gio_luu!r}')
    kiem(gio_luu not in cau,
         'và KHÔNG mang gio_luu — hai mốc khác nhau, đừng để lẫn')

    # ---- B. Tệp KHÔNG có docProps -> nói TRỐNG, KHÔNG thay bằng gio_luu ----
    goc2, MA2 = os.path.join(tm, 'kho1e2'), '2026-06-08'
    t2 = dung_xlsx(os.path.join(tm, 'khong-ngay.xlsx'), o_mau(so_tiet=4))
    K.them_ban(goc2, MA2, t2, 'người thử', tach=D.doc(t2))
    K.danh_dau_ban(goc2, MA2, 1, 'dung', 'ca thử: bản này dùng được')
    d2, _ = SD.du_lieu_dang(goc2, MA2)
    kiem(isinstance(d2, dict), 'Bản KHÔNG có ngày vẫn đăng được')
    if not isinstance(d2, dict):
        return
    cau2 = d2.get('khai_nguon') or ''
    gl2 = (d2.get('nguon') or {}).get('gio_luu')
    kiem(isinstance(gl2, str) and gl2 and gl2 not in cau2,
         f'THIẾU ngày thì KHÔNG thay bằng gio_luu — câu: {cau2!r}')
    kiem('KHÔNG RÕ' in cau2,
         'mà nói thẳng là KHÔNG RÕ — thà trống còn hơn nói sai ngày')
    kiem(NGAY not in cau2 and cau2 != cau,
         'và không mượn ngày của bản khác')


def ca_2_kien_truc_khong_co_loi_vong():
    print('\nCA 2 — KIẾN TRÚC: không có đường nào khác dẫn tới dữ liệu')
    print('-' * 74)
    dd = os.path.join(GOC, 'sinh_dang.py')
    nguon = io.open(dd, encoding='utf-8').read()
    try:
        cay = ast.parse(nguon)
    except SyntaxError as e:
        kiem(False, f'Phân tích được sinh_dang.py -> {e}')
        return
    kiem(True, 'Phân tích được cây cú pháp của sinh_dang.py')

    # --- (a) không gọi hàm đọc phiếu thô ---
    CAM_GOI = {'doc_phieu', 'doc_phieu_ky'}
    goi = set()
    for n in ast.walk(cay):
        if isinstance(n, ast.Call):
            f = n.func
            ten = (f.attr if isinstance(f, ast.Attribute)
                   else (f.id if isinstance(f, ast.Name) else None))
            if ten:
                goi.add(ten)
    vi_pham = sorted(CAM_GOI & goi)
    kiem(not vi_pham,
         f'KHÔNG gọi hàm đọc phiếu thô {sorted(CAM_GOI)} — thấy {vi_pham}')

    # --- (b) không bóc khoá 'ban' của phiếu ---
    boc = []
    for n in ast.walk(cay):
        if isinstance(n, ast.Subscript):
            sl = n.slice
            if isinstance(sl, ast.Constant) and sl.value == 'ban':
                boc.append(getattr(n, 'lineno', '?'))
        if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) \
                and n.func.attr == 'get' and n.args:
            a0 = n.args[0]
            if isinstance(a0, ast.Constant) and a0.value == 'ban':
                boc.append(getattr(n, 'lineno', '?'))
    kiem(not boc, f"KHÔNG bóc khoá 'ban' của phiếu — thấy ở dòng {boc}")

    # --- (c) CỬA phải thật sự được gọi (chống 'sạch vì rỗng') ---
    kiem('ban_de_dang' in goi,
         'Và CÓ gọi ban_de_dang() — nếu không thì hai mục trên sạch vô nghĩa')

    # --- (d) không hàm công khai nào NHẬN dữ liệu trực tiếp ---
    CAM_THAM_SO = {'ban', 'phieu', 'tach', 'du_lieu', 'o', 'ds'}
    xau = []
    for ten, ham in vars(SD).items():
        if ten.startswith('_') or not inspect.isfunction(ham):
            continue
        if getattr(ham, '__module__', None) != SD.__name__:
            continue
        ts = set(inspect.signature(ham).parameters)
        chung = ts & CAM_THAM_SO
        if chung:
            xau.append((ten, sorted(chung)))
    kiem(not xau,
         f'Không hàm công khai nào NHẬN thẳng dữ liệu {sorted(CAM_THAM_SO)} '
         f'— thấy {xau}')

    # --- (e) và phải CÓ hàm công khai để mục (d) không sạch vì rỗng ---
    cong_khai = [t for t, h in vars(SD).items()
                 if not t.startswith('_') and inspect.isfunction(h)
                 and getattr(h, '__module__', None) == SD.__name__]
    kiem(len(cong_khai) > 0,
         f'Có {len(cong_khai)} hàm công khai để mục trên có gì mà soi — '
         f'{sorted(cong_khai)}')

    # --- (f) mọi hàm công khai đều đòi (goc, ma_tuan), không nhận gì khác ---
    sai_chu_ky = []
    for ten in cong_khai:
        ts = list(inspect.signature(getattr(SD, ten)).parameters)
        if ts[:2] != ['goc', 'ma_tuan']:
            sai_chu_ky.append((ten, ts))
    kiem(not sai_chu_ky,
         f'Mọi hàm công khai bắt đầu bằng (goc, ma_tuan) — {sai_chu_ky}')

    # --- (g) BỘ TRƯỜNG RA NGOÀI bị GHIM CỨNG, cố ý ---
    #
    # Ghim literal ở đây là ĐÚNG, khác hẳn luật "đừng ghim hằng số lấy từ
    # cauhinh.json". `TRUONG_O` không phải dữ liệu nhà trường — nó là một
    # QUYẾT ĐỊNH VỀ PHẠM VI CÔNG KHAI, và cả điểm của mục này là: nới nó ra
    # thì ca thử phải ĐỎ, để người nới phải đi hỏi lại nhà trường.
    #
    # Bản đầu của mục này so `d['truong_o']` với `SD.TRUONG_O` — tức so đầu
    # ra với chính hằng số sinh ra nó, nên thêm trường mới thì HAI VẾ CÙNG
    # ĐỔI và mục vẫn xanh. Đã đo: thêm 'tho' và 'o_excel' -> 30/30, không
    # một mục nào đỏ. Đúng nếp hỏng "một mục canh sai chỗ trông y hệt một
    # mục canh đúng chỗ".
    DA_DUYET = {'lop', 'thu', 'tiet', 'mon', 'gv'}
    kiem(set(SD.TRUONG_O) == DA_DUYET,
         f'Bộ trường ra ngoài ĐÚNG BẰNG bộ đã duyệt — thừa '
         f'{sorted(set(SD.TRUONG_O) - DA_DUYET)}, thiếu '
         f'{sorted(DA_DUYET - set(SD.TRUONG_O))}')
    kiem('tho' not in SD.TRUONG_O and 'o_excel' not in SD.TRUONG_O,
         "và KHÔNG có 'tho' (chuỗi gốc trong ô) hay 'o_excel' (toạ độ) — "
         'hai thứ này không có trên trang xem hiện tại')

    # --- (h) không nhắc tới docs/ ---
    chuoi = [n.value for n in ast.walk(cay)
             if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    ma = [c for c in chuoi if 'docs' in c and len(c) < 60
          and not c.strip().startswith('#')]
    tho = [c for c in ma if c.strip() in ('docs', 'docs/', './docs')]
    kiem(not tho, f'Không có hằng chuỗi trỏ vào docs/ — {tho}')

    # --- (i) KHÔNG áp BẢNG TÊN lúc đăng ---
    #
    # Sức ép làm việc này là có thật: trang công khai lấy tên từ
    # `cauhinh.json` nên hiện `T.T.Hiền`, còn bản tách trong kho ghi
    # `T.Hiền` — người nối Đợt 4 sẽ thấy "cùng một cô hai tên" và sẽ chữa
    # bằng cách gọi `bang_ten.chuan()` ngay trong vòng lặp bóc ô. Đo
    # 26/8/2026: thêm một dòng như vậy thì bộ thử này vẫn 32/32, KHÔNG một
    # mục nào đỏ — tức trước mục này không có gì canh.
    #
    # Vì sao phải chặn: khoa có H.Hiền (Địa lí) VÀ T.T.Hiền (Sinh học). Gộp
    # sai một lần là gán tiết của cô này cho cô kia trước mặt phụ huynh, và
    # git thì nhớ vĩnh viễn. Trang công khai là bản điện tử của đúng tờ đang
    # treo ở trường: trường phát ra sao thì đăng vậy, không tự bịa nhãn.
    #
    # Mốc so là literal viết ở đây, CỐ Ý — lấy từ `bang_ten.py` là hai vế
    # cùng dịch (nếp hỏng 12), y như chuyện `TRUONG_O` ở mục (g).
    CAM_TEN = {'bang_ten', 'chuan', 'gop', 'da_duyet', 'ten_la', 'BT'}
    nhac = set(goi)
    for n in ast.walk(cay):
        if isinstance(n, ast.Name):
            nhac.add(n.id)
        elif isinstance(n, ast.Attribute):
            nhac.add(n.attr)
        elif isinstance(n, ast.Import):
            nhac |= {a.name.split('.')[0] for a in n.names}
            nhac |= {a.asname for a in n.names if a.asname}
        elif isinstance(n, ast.ImportFrom):
            if n.module:
                nhac.add(n.module.split('.')[0])
    dinh = sorted(CAM_TEN & nhac)
    kiem(not dinh,
         'KHÔNG áp bảng tên lúc đăng — trường phát ra sao thì đăng vậy. '
         f'Thấy {dinh}')
    # ⚠ GIỚI HẠN ĐÃ BIẾT, ĐỪNG ĐỌC QUÁ: mục này canh TÊN ĐỊNH DANH, không
    # canh HÀNH VI. Nó chặn đường THẲNG (`import bang_ten` rồi `.chuan()`),
    # KHÔNG chặn đường VÒNG — một bản cài tự `json.load('bang_ten_gv.json')`
    # rồi tra bằng `dict.get` đi lọt sạch: đo 26/8/2026 vẫn 37/37, không
    # mục nào đỏ, trong khi tên GV ra công khai đã bị gộp (T.Hiền ->
    # T.T.Hiền). Chặn kín thì phải khẳng định trên HÀNH VI — so chuỗi ra
    # công khai với chuỗi thô trong bản tách. Ghi ở "Việc treo".


def ca_3_goi_thang_vao_ruot_khong_lay_duoc_gi(tm):
    print('\nCA 3 — gọi thẳng vào ruột, KHÔNG qua cửa: phải không lấy được gì')
    print('-' * 74)
    goc = os.path.join(tm, 'kho3')
    _dung_tuan(goc, '2026-01-05', 'sai', 'ca thử: bản này SAI', 3, tm)
    p, _ = K.doc_phieu_ky(goc, '2026-01-05')
    ban_sai = ((p or {}).get('ban') or [{}])[0]
    kiem(K.trang_thai_cua(ban_sai) == 'sai', 'Đã dựng một tuần chỉ có bản SAI')

    # thử MỌI hàm công khai với bản sai làm đối số -> không hàm nào nhận
    nhan = []
    for ten, ham in vars(SD).items():
        if ten.startswith('_') or not inspect.isfunction(ham):
            continue
        if getattr(ham, '__module__', None) != SD.__name__:
            continue
        for doi_so in ((ban_sai,), (p,), (goc, ban_sai), (ban_sai, p)):
            try:
                r = ham(*doi_so)
            except Exception:                           # noqa: BLE001
                continue
            if isinstance(r, tuple) and r and isinstance(r[0], dict):
                nhan.append((ten, len(doi_so)))
            elif isinstance(r, dict) and r:
                nhan.append((ten, len(doi_so)))
    kiem(not nhan,
         f'Không hàm nào nhận thẳng bản/phiếu rồi trả dữ liệu — {nhan}')

    # và đường đúng vẫn từ chối
    d, tu_choi = SD.du_lieu_dang(goc, '2026-01-05')
    kiem(d is None and bool(tu_choi),
         'Đường đúng cũng từ chối, vì bản duy nhất là "sai"')


def ca_4_khong_ghi_vao_docs(tm):
    print('\nCA 4 — lệnh dang-thu TỪ CHỐI ghi vào docs/, qua tiến trình con')
    print('-' * 74)
    docs = os.path.join(GOC, 'docs')
    truoc = sorted(os.listdir(docs)) if os.path.isdir(docs) else None
    kiem(truoc is not None, f'Có thư mục docs/ để canh — {truoc}')

    goc = os.path.join(tm, 'kho4')
    _dung_tuan(goc, '2026-01-05', 'dung', 'ca thử: dùng được', 3, tm)

    r = subprocess.run(
        [sys.executable, os.path.join(GOC, 'luu_tuan.py'), '--kho', goc,
         'dang-thu', '--tuan', '2026-01-05', '--ra', 'docs'],
        cwd=GOC, capture_output=True, text=True, timeout=60)
    kiem(r.returncode != 0, f'Ghi vào docs/ -> thoát KHÁC 0 ({r.returncode})')
    kiem('docs' in (r.stdout + r.stderr),
         'và nói rõ vì sao từ chối')
    sau = sorted(os.listdir(docs)) if os.path.isdir(docs) else None
    kiem(sau == truoc, f'docs/ KHÔNG đổi một tệp nào — {truoc} -> {sau}')

    # đường hợp lệ thì ghi được, và ghi ra ngoài docs/
    ra = os.path.join(tm, 'ra4')
    r2 = subprocess.run(
        [sys.executable, os.path.join(GOC, 'luu_tuan.py'), '--kho', goc,
         'dang-thu', '--tuan', '2026-01-05', '--ra', ra],
        cwd=GOC, capture_output=True, text=True, timeout=60)
    kiem(r2.returncode == 0, f'Thư mục thường thì ghi được — {r2.returncode}')
    dd = os.path.join(ra, '2026-01-05.json')
    kiem(os.path.exists(dd), 'Có tệp JSON sinh ra')
    if os.path.exists(dd):
        try:
            d = json.load(io.open(dd, encoding='utf-8'))
        except Exception as e:                          # noqa: BLE001
            kiem(False, f'Đọc lại JSON -> {type(e).__name__}: {e}')
            return
        kiem(d.get('truong_o') == list(SD.TRUONG_O),
             f'Khai đúng bộ trường ra ngoài — {d.get("truong_o")}')
        o = d.get('o') or []
        kiem(o and all(len(x) == len(SD.TRUONG_O) for x in o),
             'Mỗi ô đúng số trường, không thừa trường nào')
        kiem(sau == (sorted(os.listdir(docs)) if os.path.isdir(docs) else None),
             'Và docs/ VẪN không đổi sau lượt ghi hợp lệ')


# ==========================================================================
def main():
    dat_dong_ho_canh(180)
    print('=' * 74)
    print(' THỬ: bộ sinh dữ liệu đăng — không có lối vòng qua cửa')
    print('=' * 74)
    tm = tempfile.mkdtemp(prefix='thu_sinh_dang_')
    try:
        ca_1_hanh_vi(tm)
        ca_1b_khuyet_tat_khong_ro_ra_cong_khai(tm)
        ca_1c_khong_dang_danh_sach_nguoi_gom_san(tm)
        ca_1d_khong_chu_tu_do_nao_qua_cua(tm)
        ca_1e_khai_nguon_noi_ngay_truong_sua(tm)
        ca_2_kien_truc_khong_co_loi_vong()
        ca_3_goi_thang_vao_ruot_khong_lay_duoc_gi(tm)
        ca_4_khong_ghi_vao_docs(tm)
    finally:
        shutil.rmtree(tm, ignore_errors=True)

    dat = sum(1 for ok, _ in KQ if ok)
    print('\n' + '=' * 74)
    print(f'Tổng: {dat}/{len(KQ)} mục ĐẠT.')
    return 0 if dat == len(KQ) else 1


if __name__ == '__main__':
    sys.exit(main())

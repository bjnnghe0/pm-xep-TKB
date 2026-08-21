#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ ĐỢT 3 VIỆC 1 — CÂU ĐỌC LẠI
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_doc_lai.py

 VÌ SAO CÓ PHẦN NÀY. 20/8 thầy cô khai ba quy tắc có ghi_chu nói "không trùng
 ngày với" mà loai lại là chi_xep_thu — NGHĨA NGƯỢC HẲN. Phần mềm nhận cả hai,
 không kêu một tiếng, phải bấm Lưu 5 lần rồi chạy xếp mới lộ ra cấu hình VÔ
 NGHIỆM.

 BA MỤC QUAN TRỌNG NHẤT, và cả ba đều canh chất lượng chứ không canh sự tồn tại:

   CA 2  17 câu KHÁC NHAU ĐÔI MỘT, **và** 17 CHUỖI MẪU cũng vậy.
         `MAU_CAU = 'x'` qua được @dang_ky, nên phải có mục này.
         Hai phép so chứ không một: bản đầu chỉ so CÂU ĐÃ DỰNG và không bắt
         được dạng sai hay gặp nhất — chép MAU_CAU của loại bên cạnh rồi quên
         sửa — vì mỗi loại dựng câu từ VI_DU riêng nên chuỗi ra vẫn khác nhau.
   CA 3  Câu phải NHẮC LẠI giá trị lấy từ VI_DU. Câu đúng ngữ pháp mà bỏ mất
         "Thứ 2" thì vô dụng đúng ở chỗ cần dùng.
   CA 5  Ghi chú KHÔNG chứa từ khoá nào -> câu đọc lại VẪN HIỆN.
         Đây là điều kiện người dùng đặt: từ khoá là GỢI Ý, không phải PHÁN
         QUYẾT. "Sử với Toán đừng dính nhau" không khớp từ khoá nào, và đúng
         lúc đó câu đọc lại lại càng cần.
==========================================================================
"""
import io
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import GOC_TM, MayChuTam, cau_hinh_tam    # noqa: E402
import quy_tac as QT         # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


# ==========================================================================
def ca_1_moi_loai_deu_khai_du():
    print('\nCA 1 — mọi loại đều khai MAU_CAU, và @dang_ky ÉP điều đó')
    print('-' * 74)
    thieu = [t for t, c in QT.DANH_MUC.items()
             if not str(getattr(c, 'MAU_CAU', '')).strip()]
    kiem(not thieu, f'{len(QT.DANH_MUC)}/{len(QT.DANH_MUC)} loại có MAU_CAU — '
                    f'thiếu: {thieu}')

    sai_o = {}
    for t, c in QT.DANH_MUC.items():
        hop_le = {x['ten'] for x in c.TRUONG} | {
            x['nhom'] for x in c.TRUONG if x.get('nhom')}
        la = [o for o in QT._o_trong_mau(c.MAU_CAU) if o not in hop_le]
        if la:
            sai_o[t] = la
    kiem(not sai_o, f'Mọi ô {{…}} đều khớp một trường (hoặc nhóm) trong TRUONG '
                    f'— sai: {sai_o}')

    # ÉP BẰNG CẤU TRÚC: thử đăng ký một lớp thiếu MAU_CAU, phải DỪNG.
    try:
        @QT.dang_ky('loai_thu_khong_co_mau_cau')
        class ThuThieu(QT.QuyTac):
            TRUONG = []
        chan = False
    except SystemExit as e:
        chan = 'MAU_CAU' in str(e)
    finally:
        QT.DANH_MUC.pop('loai_thu_khong_co_mau_cau', None)
    kiem(chan, 'Đăng ký một loại THIẾU MAU_CAU thì DỪNG ngay lúc nạp mô-đun — '
               'không phải "ca thử đỏ ở đâu đó"')

    try:
        @QT.dang_ky('loai_thu_o_sai')
        class ThuOSai(QT.QuyTac):
            TRUONG = [{'ten': 'thu', 'kieu': 'ds_thu', 'nhan': 'x',
                       'bat_buoc': True}]
            MAU_CAU = 'xếp vào {khong_co_truong_nay}'
        chan2 = False
    except SystemExit as e:
        chan2 = 'khong_co_truong_nay' in str(e)
    finally:
        QT.DANH_MUC.pop('loai_thu_o_sai', None)
    kiem(chan2, 'Ô {…} không khớp TRUONG cũng DỪNG, và câu lỗi chỉ đích danh ô')


# ==========================================================================
def ca_2_muoi_bay_cau_khac_nhau():
    print('\nCA 2 — 17 câu KHÁC NHAU ĐÔI MỘT (mục bắt câu vô nghĩa)')
    print('-' * 74)
    cau = {t: QT.cau_doc_lai(c.VI_DU) for t, c in QT.DANH_MUC.items()}
    rong = [t for t, x in cau.items() if not x.strip()]
    kiem(not rong, f'Không câu nào rỗng — rỗng: {rong}')
    con = [t for t, x in cau.items() if '{' in x or '}' in x or '[' in x]
    kiem(not con, f'Không câu nào còn sót ô {{…}} hay đoạn […] — sót: {con}')

    trung = {}
    for t, x in cau.items():
        trung.setdefault(x, []).append(t)
    doi = {x: ds for x, ds in trung.items() if len(ds) > 1}
    kiem(not doi,
         f'{len(cau)} CÂU khác nhau đôi một — trùng: '
         f'{[ds for ds in doi.values()]}')

    # So CHÍNH CHUỖI MẪU, không chỉ so câu đã dựng. Đây là mục bắt được dạng
    # sai hay gặp nhất: chép MAU_CAU của loại bên cạnh rồi quên sửa.
    # ĐÃ ĐO: bản đầu của ca thử này chỉ so câu đã dựng, và KHÔNG bắt được —
    # vì mỗi loại dựng câu từ VI_DU riêng nên chuỗi ra vẫn khác nhau. Một mục
    # canh sai chỗ trông y hệt một mục canh đúng chỗ.
    tmau = {}
    for t, c in QT.DANH_MUC.items():
        tmau.setdefault(' '.join(c.MAU_CAU.split()), []).append(t)
    doi_mau = {x: ds for x, ds in tmau.items() if len(ds) > 1}
    kiem(not doi_mau,
         f'Và {len(QT.DANH_MUC)} CHUỖI MẪU cũng khác nhau đôi một — trùng: '
         f'{[ds for ds in doi_mau.values()]}')

    ngan = {t: x for t, x in cau.items() if len(x) < 20}
    kiem(not ngan, f'Không câu nào ngắn cụt — {ngan}')


# ==========================================================================
def ca_3_cau_nhac_lai_gia_tri():
    print('\nCA 3 — câu phải NHẮC LẠI giá trị người dùng khai')
    print('-' * 74)
    thieu = []
    for t, c in QT.DANH_MUC.items():
        cau = QT.cau_doc_lai(c.VI_DU)
        for tr in c.TRUONG:
            gt = c.VI_DU.get(tr['ten'])
            if gt is None or tr['kieu'] == 'loc':
                continue
            mong = QT._dinh_dang(tr['kieu'], gt)
            if mong and mong not in cau:
                thieu.append(f'{t}.{tr["ten"]} ({mong!r})')
    kiem(not thieu,
         f'Mọi giá trị khai trong VI_DU đều xuất hiện trong câu — thiếu: '
         f'{thieu}')

    # Bộ lọc cũng phải hiện ra, kể cả khi RỖNG.
    kiem('mọi tiết' in QT.cau_bo_loc({}),
         f'Bộ lọc RỖNG nói thành chữ "mọi tiết", không im lặng — '
         f'{QT.cau_bo_loc({})!r}')
    # Dùng tên BỊA, không dùng tên thật của trường: cau_bo_loc() chỉ ghép
    # chuỗi, nó không tra dữ liệu — nên ghim tên thật vào đây vừa thừa vừa làm
    # ca thử vỡ khi nhà trường đổi tên môn. (tests/thu_ghim_du_lieu.py đã bắt
    # đúng ba chỗ này ở bản đầu.)
    mon, lop1, lop2, gv = 'Môn Bịa', 'Lớp Bịa 1', 'Lớp Bịa 2', 'GV Bịa'
    c = QT.cau_bo_loc({'mon': mon, 'lop': [lop1, lop2], 'tru': {'gv': gv}})
    kiem(mon in c and lop1 in c and lop2 in c and 'TRỪ' in c and gv in c,
         f'Bộ lọc có "tru" nói đủ cả hai vế — {c!r}')


# ==========================================================================
def ca_4_bat_dung_loi_qt16():
    print('\nCA 4 — bắt đúng lỗi QT 16: ghi_chu nói một đằng, loai làm một nẻo')
    print('-' * 74)
    # Nguyên văn tình huống 20/8: ý định "không trùng ngày với", khai chi_xep_thu
    xau = {'loai': 'chi_xep_thu',
           'ghi_chu': 'Lịch sử không trùng ngày với Toán 12B4',
           'loc': {'mon': 'Lịch sử'}, 'thu': [3, 4, 5]}
    kiem(QT.so_ghi_chu(xau) is not None,
         'Ghi chú "không trùng ngày" + loại chi_xep_thu -> CÓ cảnh báo')

    tot = {'loai': 'khac_ngay',
           'ghi_chu': 'Lịch sử không trùng ngày với Toán 12B4',
           'a': {'mon': 'Lịch sử'}, 'b': {'mon': 'Toán học'}}
    kiem(QT.so_ghi_chu(tot) is None,
         'Cùng ghi chú đó + loại khac_ngay -> KHÔNG cảnh báo (đã đúng loại)')

    # Không báo oan khi ghi_chu dùng từ khoá của CHÍNH ý niệm đang chọn.
    hop = {'loai': 'chi_xep_thu', 'ghi_chu': 'Vật lý chỉ xếp Thứ 2',
           'loc': {'mon': 'Vật lý'}, 'thu': [2]}
    kiem(QT.so_ghi_chu(hop) is None,
         'Ghi chú "chỉ xếp" + loại chi_xep_thu -> KHÔNG báo oan')

    # Câu vừa có "chỉ" vừa có "không xếp" là cách nói hợp lệ, đừng báo.
    ca_hai = {'loai': 'chi_xep_thu',
              'ghi_chu': 'Vật lý chỉ xếp Thứ 2, không xếp ngày khác',
              'loc': {'mon': 'Vật lý'}, 'thu': [2]}
    kiem(QT.so_ghi_chu(ca_hai) is None,
         'Ghi chú nói cả hai chiều nhưng khớp ý niệm đang chọn -> không báo')


# ==========================================================================
def ca_5_khong_tu_khoa_van_hien_cau(tm):
    print('\nCA 5 — ĐIỀU KIỆN NGƯỜI DÙNG: không từ khoá nào -> câu VẪN hiện')
    print('-' * 74)
    dd = cau_hinh_tam(os.path.join(tm, 'd5'))
    with MayChuTam(dd) as (k, _):
        # "Sử với Toán đừng dính nhau" — không từ khoá nào khớp.
        r = {'loai': 'chi_xep_thu', 'ghi_chu': 'Sử với Toán đừng dính nhau',
             'loc': {'mon': 'Lịch sử'}, 'thu': [3]}
        ma, d = k.js('/api/thu-quy-tac', {'doc_lai': True, 'quy_tac': r})
        kiem(ma == 200, f'/api/thu-quy-tac?doc_lai qua HTTP thật — {ma}')
        kiem(bool(d.get('cau')),
             f'Không từ khoá nào khớp, câu đọc lại VẪN hiện — {d.get("cau")!r}')
        kiem(d.get('canh_bao') is None,
             'Và KHÔNG báo bừa: từ khoá là gợi ý, không phải phán quyết')

        # Nhánh có cảnh báo cũng phải qua được HTTP
        r2 = dict(r, ghi_chu='Sử không trùng ngày với Toán')
        _, d2 = k.js('/api/thu-quy-tac', {'doc_lai': True, 'quy_tac': r2})
        kiem(bool(d2.get('cau')) and bool(d2.get('canh_bao')),
             'Nhánh có bằng chứng ngược thì có CẢ câu lẫn cảnh báo')

        # Chưa chọn loại / loại lạ: nói rõ, không vỡ
        _, d3 = k.js('/api/thu-quy-tac', {'doc_lai': True, 'quy_tac': {}})
        kiem(d3.get('loi') and not d3.get('cau'),
             f'Chưa chọn loại -> nói rõ, không câu rỗng im lặng — {d3}')
        _, d4 = k.js('/api/thu-quy-tac',
                     {'doc_lai': True, 'quy_tac': {'loai': 'khong-co-loai-nay'}})
        kiem(d4.get('loi') and 'khong-co-loai-nay' in d4['loi'],
             f'Loại lạ -> nói rõ tên loại lạ — {d4}')


# ==========================================================================
def ca_6_khong_giai_gi_ca(tm):
    print('\nCA 6 — đường đọc lại KHÔNG giải, KHÔNG ghi, KHÔNG kẹt sau khoá thử')
    print('-' * 74)
    import hashlib
    import time
    dd = cau_hinh_tam(os.path.join(tm, 'd6'))
    goc = hashlib.md5(io.open(dd, 'rb').read()).hexdigest()
    with MayChuTam(dd) as (k, _):
        r = {'loai': 'chi_xep_thu', 'ghi_chu': 'thử', 'loc': {}, 'thu': [2]}
        t0 = time.perf_counter()
        for _ in range(20):
            k.js('/api/thu-quy-tac', {'doc_lai': True, 'quy_tac': r})
        giay = time.perf_counter() - t0
        kiem(giay < 3,
             f'20 lượt đọc lại hết {giay:.2f}s — đủ rẻ để gọi sau mỗi phím gõ')
        kiem(hashlib.md5(io.open(dd, 'rb').read()).hexdigest() == goc,
             'cauhinh.json KHÔNG đổi một byte nào')
        _, dq = k.js('/api/quy-tac')
        kiem(dq.get('so_moi') == 0,
             f'Và KHÔNG tạo nháp nào trong phiên — so_moi={dq.get("so_moi")}')

    html = io.open(os.path.join(GOC_TM, 'web', 'index.html'),
                   encoding='utf-8').read()
    js = io.open(os.path.join(GOC_TM, 'web', 'app.js'), encoding='utf-8').read()
    thieu = [i for i in ('doc-lai', 'doc-lai-cau', 'doc-lai-canh-bao')
             if f'id="{i}"' not in html]
    kiem(not thieu, f'Giao diện có đủ ba mảnh — thiếu {thieu}')
    kiem('doc_lai: true' in js, 'app.js gọi đúng nhánh doc_lai')
    kiem('henDocLai' in js and 'setTimeout' in js,
         'và hoãn lại chứ không bắn theo từng phím gõ')


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ ĐỢT 3 VIỆC 1 — CÂU ĐỌC LẠI')
    print('=' * 74)
    ca_1_moi_loai_deu_khai_du()
    ca_2_muoi_bay_cau_khac_nhau()
    ca_3_cau_nhac_lai_gia_tri()
    ca_4_bat_dung_loi_qt16()
    with tempfile.TemporaryDirectory() as tm:
        os.makedirs(os.path.join(tm, 'd5'), exist_ok=True)
        os.makedirs(os.path.join(tm, 'd6'), exist_ok=True)
        ca_5_khong_tu_khoa_van_hien_cau(tm)
        ca_6_khong_giai_gi_ca(tm)
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

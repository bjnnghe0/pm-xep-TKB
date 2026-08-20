#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 CA THỬ CHẾ ĐỘ TÁI LẬP
--------------------------------------------------------------------------
 Chạy:  python3 tests/thu_tai_lap.py

 VÌ SAO CÓ TỆP NÀY. Bộ giải bị chặn bằng ĐỒNG HỒ TREO TƯỜNG (60 giây tổng,
 3 giây mỗi lượt), nên hai lần chạy cùng seed vẫn cho số phương án khác nhau
 — đã thấy 396 rồi 395 rồi 396. Hệ quả tệ hơn con số: từ nay MỌI hồi quy thật
 đều có thể bị đổ cho "dao động bình thường", và không ai cãi được.

 che_do_tai_lap bỏ HẲN hai phép kiểm đồng hồ (chứ không đặt số thật to — đặt
 số to chỉ ghim theo XÁC SUẤT, máy bận thì vẫn nổ). Chỉ còn chặn bằng BỘ ĐẾM.

 BỐN CÂU CA THỬ NÀY PHẢI TRẢ LỜI:
   1. Cờ có thật sự bỏ hai giới hạn không (điều kiện tiên quyết của mọi mục sau)
   2. Cùng seed có ra cùng kết quả không — trong CÙNG tiến trình
   3. ... và giữa HAI TIẾN TRÌNH khác nhau (PYTHONHASHSEED ngẫu nhiên mỗi lần,
      nên thứ tự lặp set có thể đổi — đây là nguồn bất định đáng ngờ nhất)
   4. KHÔNG CÓ ĐỒNG HỒ THÌ CÁI GÌ BẢO ĐẢM DỪNG? Chạy trên cấu hình VÔ NGHIỆM
      để chứng minh nó dừng bằng bộ đếm chứ không treo mãi.

 Ca thử phải biết ĐỎ, không phải biết VỠ: không dùng list.index() hay bất cứ
 thứ gì ném ngoại lệ giữa chừng làm chết cả bộ thử.
==========================================================================
"""
import hashlib
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tien_ich_web import GOC_TM, MayChuTam, cau_hinh_tam  # noqa: E402
import xep_tkb as X                                      # noqa: E402

KQ = []


def kiem(dieu_kien, mo_ta):
    KQ.append((bool(dieu_kien), mo_ta))
    print(f'  [{"ĐẠT" if dieu_kien else "LỖI"}] {mo_ta}')


def dau_van_tay(bt, pa):
    """Rút một phương án thành MỘT chuỗi so sánh được.

       Băm cả (lớp, ngày, vị trí, môn, GV) của từng cụm — tức toàn bộ nội dung
       sẽ đi vào vùng D8:I32 của tệp Excel. So dấu vân tay chặt hơn so điểm số:
       hai phương án khác nhau vẫn có thể trùng điểm.
    """
    if pa is None:
        return 'KHONG-CO-LOI-GIAI'
    X.nap(bt, pa)
    o = sorted((c.lop, c.ngay, c.vitri, c.mon, c.gv)
               for c in bt.cac_cum if not c.la_trong)
    return hashlib.sha256(
        json.dumps(o, ensure_ascii=False).encode()).hexdigest()[:16]


def cau_hinh(sua=None):
    cfg = X.doc_cau_hinh(os.path.join(GOC_TM, 'cauhinh.json'))
    if sua:
        sua(cfg)
    return cfg


# ==========================================================================
def ca_1_co_bo_that_hai_gioi_han():
    print('\nCA 1 — cờ có THẬT SỰ bỏ hai giới hạn thời gian không')
    print('-' * 74)
    # Đây là ĐIỀU KIỆN TIÊN QUYẾT của mọi mục sau. Không có mục này thì ai tắt
    # cờ đi, các mục "hai lần giống nhau" vẫn xanh — vì hai lượt chạy nhanh
    # trên máy rảnh vẫn có thể tình cờ trùng nhau. Đúng lối thu_du_phong.py:
    # tự khẳng định điều kiện tiên quyết trước khi kiểm cái cần kiểm.
    goc = {'so_lan_thu': 5, 'seed': 7,
           'gioi_han_giay_moi_lan': 3.0, 'gioi_han_tong_giay': 60}

    tat = X.gop_tim_kiem(goc)
    kiem(tat['gioi_han_giay_moi_lan'] == 3.0 and tat['gioi_han_tong_giay'] == 60,
         f'Cờ TẮT: giữ nguyên giới hạn thời gian — '
         f'{tat["gioi_han_giay_moi_lan"]}s / {tat["gioi_han_tong_giay"]}s')
    kiem(tat['che_do_tai_lap'] is False, 'Cờ tắt thì che_do_tai_lap = False')

    bat = X.gop_tim_kiem(goc, che_do_tai_lap=True)
    kiem(bat['gioi_han_giay_moi_lan'] is None,
         f'Cờ BẬT: gioi_han_giay_moi_lan = None (bỏ hẳn, không phải số to) — '
         f'{bat["gioi_han_giay_moi_lan"]!r}')
    kiem(bat['gioi_han_tong_giay'] is None,
         f'Cờ BẬT: gioi_han_tong_giay = None — {bat["gioi_han_tong_giay"]!r}')
    kiem(bat['so_lan_thu'] == 5 and bat['seed'] == 7 and
         bat['gioi_han_buoc'] == 30000,
         'Cờ BẬT vẫn giữ nguyên bộ đếm: so_lan_thu, seed, gioi_han_buoc')

    # bật từ chính cauhinh.json chứ không chỉ qua tham số
    tu_tep = X.gop_tim_kiem({'che_do_tai_lap': True, 'so_lan_thu': 5})
    kiem(tu_tep['gioi_han_tong_giay'] is None,
         'Bật được từ mục "tim_kiem" trong cauhinh.json, không chỉ qua tham số')

    # ghi_de bằng None phải bị BỎ QUA, không được ghi đè thành None
    gd = X.gop_tim_kiem(goc, so_lan_thu=None, seed=None)
    kiem(gd['so_lan_thu'] == 5 and gd['seed'] == 7,
         'Tuỳ chọn dòng lệnh chưa khai (None) thì KHÔNG đè lên cấu hình')

    # MỘT bản cài duy nhất. Trước đây ba chỗ chép tay cùng một dict, nên thêm
    # một luật mới là phải nhớ sửa cả ba — quên một chỗ thì hỏng trong im lặng.
    # Ghim bằng cách đếm: chỉ gop_tim_kiem() được dựng khoá 'gioi_han_tong_giay'.
    dem = sum(io.open(os.path.join(GOC_TM, t), encoding='utf-8').read()
              .count("'gioi_han_tong_giay':") for t in ('xep_tkb.py', 'web.py'))
    kiem(dem == 1,
         f'Cả dự án chỉ còn ĐÚNG MỘT chỗ dựng dict tim_kiem — đếm được {dem}')


# ==========================================================================
def ca_2_cung_tien_trinh():
    print('\nCA 2 — cùng seed, cùng kết quả (trong CÙNG một tiến trình)')
    print('-' * 74)
    cfg = cau_hinh()
    tk = X.gop_tim_kiem({'so_lan_thu': 10, 'seed': 2027}, che_do_tai_lap=True)

    dau = []
    for lan in range(2):
        bt = X.BaiToan(cfg)              # dựng lại từ đầu, như hai lần chạy thật
        kqt = X.tim_phuong_an(bt, tk)
        dau.append((dau_van_tay(bt, kqt.tot or kqt.du_phong),
                    kqt.diem, kqt.so_hop_le, kqt.da_thu))
    kiem(dau[0] == dau[1],
         f'Hai lượt giống HỆT nhau — {dau[0]} vs {dau[1]}')
    kiem(dau[0][3] == 10,
         f'Và chạy đủ 10 lượt thử, không bị đồng hồ cắt ngang — {dau[0][3]}')

    # đổi seed thì PHẢI khác — nếu không thì phép so trên là vô nghĩa
    tk2 = X.gop_tim_kiem({'so_lan_thu': 10, 'seed': 999}, che_do_tai_lap=True)
    bt = X.BaiToan(cfg)
    kqt2 = X.tim_phuong_an(bt, tk2)
    kiem(dau_van_tay(bt, kqt2.tot or kqt2.du_phong) != dau[0][0],
         'Đổi seed thì kết quả KHÁC — phép so ở trên có khả năng phân biệt')


# ==========================================================================
def ca_3_hai_tien_trinh():
    print('\nCA 3 — cùng seed, cùng kết quả giữa HAI TIẾN TRÌNH khác nhau')
    print('-' * 74)
    # Nguồn bất định đáng ngờ nhất mà mục 2 KHÔNG bắt được: PYTHONHASHSEED
    # ngẫu nhiên mỗi tiến trình, nên thứ tự lặp của set chuỗi có thể đổi.
    ma = ('import sys, json, hashlib; sys.path.insert(0, %r);'
          'sys.path.insert(0, %r);'
          'import xep_tkb as X;'
          'cfg = X.doc_cau_hinh(%r);'
          'bt = X.BaiToan(cfg);'
          'tk = X.gop_tim_kiem({"so_lan_thu": 8, "seed": 2027},'
          '                    che_do_tai_lap=True);'
          'k = X.tim_phuong_an(bt, tk);'
          'pa = k.tot or k.du_phong; X.nap(bt, pa);'
          'o = sorted((c.lop, c.ngay, c.vitri, c.mon, c.gv)'
          '           for c in bt.cac_cum if not c.la_trong);'
          'print(hashlib.sha256(json.dumps(o, ensure_ascii=False).encode())'
          '      .hexdigest()[:16], k.diem, k.da_thu)'
          % (GOC_TM, os.path.dirname(os.path.abspath(__file__)),
             os.path.join(GOC_TM, 'cauhinh.json')))

    ra = []
    for _ in range(3):
        kq = subprocess.run([sys.executable, '-c', ma], capture_output=True,
                            text=True, timeout=300)
        ra.append(kq.stdout.strip())
    kiem(all(x == ra[0] and x for x in ra),
         f'Ba tiến trình riêng cho cùng một kết quả — {ra}')


# ==========================================================================
def ca_4_vo_nghiem_van_dung():
    print('\nCA 4 — KHÔNG CÓ ĐỒNG HỒ THÌ CÁI GÌ BẢO ĐẢM DỪNG?')
    print('-' * 74)
    # Câu hỏi trọng tâm. Trả lời: gioi_han_buoc — _quay_lui() tăng self.buoc ở
    # đầu MỖI lần gọi rồi ném TimeoutError khi vượt, và mọi đường đệ quy đều đi
    # qua đúng hàm đó. Chứng minh bằng một cấu hình VÔ NGHIỆM: bộ giải sẽ vét
    # cạn và không bao giờ tìm được lời giải, nên nếu chỉ có đồng hồ giữ nó lại
    # thì bỏ đồng hồ đi là TREO MÃI.
    #
    # CẤU HÌNH VÔ NGHIỆM PHẢI THẬT SỰ BẮT NÓ VÉT. Lần đầu tôi dồn hết vào MỘT
    # thứ: đúng là vô nghiệm, nhưng bộ giải bí ngay ở nút đầu và trả về sau
    # 0,0 giây — chứng minh "trả về nhanh" chứ KHÔNG chứng minh "bộ đếm chặn
    # được một cuộc tìm kiếm tốn kém". Đã đo lại và chọn HAI thứ: vẫn vô nghiệm
    # (24 tiết không nhét vừa 10 ô) nhưng đủ rộng để quay lui bùng nổ —
    # đo được ĐỐT TRỌN 20.000 bước trong ~6 giây.
    def ep_hai_thu(cfg):
        cfg['quy_tac'] = [{'loai': 'chi_xep_thu',
                           'ghi_chu': 'CỐ Ý VÔ NGHIỆM: dồn hết vào Thứ 2 và 3',
                           'loc': {}, 'thu': [2, 3]}]
        cfg['tim_kiem'] = {}
    cfg = cau_hinh(ep_hai_thu)

    BUOC = 20000
    tk = X.gop_tim_kiem({'so_lan_thu': 2, 'seed': 1, 'gioi_han_buoc': BUOC},
                        che_do_tai_lap=True)
    kiem(tk['gioi_han_tong_giay'] is None and tk['gioi_han_giay_moi_lan'] is None,
         'Điều kiện tiên quyết: đang chạy KHÔNG có giới hạn thời gian nào')

    # Dụng cụ đo: bọc BoGiai để lấy số bước THẬT của từng lượt. Không có nó thì
    # không phân biệt được "dừng vì hết bước" với "dừng vì bí ngay từ đầu".
    that = X.BoGiai
    da_dung = []

    class BoGiaiDem(that):
        def giai(self):
            try:
                return super().giai()
            finally:
                da_dung.append(self.buoc)

    X.BoGiai = BoGiaiDem
    xong = threading.Event()
    hop = {}

    def chay():
        t0 = time.time()
        try:
            hop['kq'] = X.tim_phuong_an(X.BaiToan(cfg), tk)
        finally:
            hop['giay'] = time.time() - t0
            xong.set()

    try:
        threading.Thread(target=chay, daemon=True).start()
        # Trần này CHỈ để ca thử không treo cả bộ nếu mã hỏng. Nó không phải
        # thứ chứng minh bộ giải dừng — cái chứng minh là nó dừng sớm hơn nhiều
        # VÀ đã đốt trọn bộ đếm bước.
        xong.wait(timeout=300)
    finally:
        X.BoGiai = that

    kiem(xong.is_set(),
         'Cấu hình VÔ NGHIỆM + không giới hạn thời gian -> vẫn DỪNG, không treo')
    if not xong.is_set():
        return                       # đừng đọc hop[] khi luồng còn chạy

    kq = hop.get('kq')
    kiem(kq is not None and kq.tot is None and kq.du_phong is None,
         'Đúng là vô nghiệm: không tìm được lời giải nào')
    kiem(kq is not None and kq.da_thu == 2,
         f'Đã thử đủ 2 lượt rồi mới thôi (bộ đếm NGOÀI: so_lan_thu) — '
         f'{kq.da_thu if kq else "?"}')

    # ĐÂY LÀ MỤC QUAN TRỌNG NHẤT của cả tệp: chứng minh nó thật sự phải vét, và
    # thứ chặn nó lại là bộ đếm BƯỚC chứ không phải may mắn bí sớm.
    kiem(da_dung and min(da_dung) > BUOC * 0.9,
         f'Mỗi lượt ĐỐT TRỌN bộ đếm bước ({BUOC:,}) rồi mới chịu thua — '
         f'số bước từng lượt: {da_dung}')
    print(f'       (dừng sau {hop["giay"]:.1f} giây, trần ca thử là 300 giây)')

    # Và chứng minh chính bộ đếm là thứ điều khiển: nhân ba số bước thì thời
    # gian phải tăng rõ rệt. Nếu có thứ khác dừng nó thì con số gần như không
    # đổi, và mục này đỏ.
    tk2 = X.gop_tim_kiem({'so_lan_thu': 1, 'seed': 1, 'gioi_han_buoc': BUOC * 3},
                         che_do_tai_lap=True)
    t1 = time.time()
    X.tim_phuong_an(X.BaiToan(cfg), tk2)
    giay_3x = time.time() - t1
    giay_1x = hop['giay'] / 2                     # hop['giay'] là 2 lượt
    kiem(giay_1x > 0.5 and giay_3x > giay_1x * 1.8,
         f'Nhân ba bộ đếm bước thì lâu hơn rõ rệt ({giay_1x:.1f}s/lượt -> '
         f'{giay_3x:.1f}s/lượt) — đúng BỘ ĐẾM BƯỚC là thứ chặn')


# ==========================================================================
def ca_5_khong_hoi_quy():
    print('\nCA 5 — không làm hồi quy chế độ chạy thật')
    print('-' * 74)
    goc = {'so_lan_thu': 400, 'seed': 0, 'gioi_han_buoc': 30000,
           'gioi_han_giay_moi_lan': 3.0, 'gioi_han_tong_giay': 60}
    tk = X.gop_tim_kiem(goc)
    kiem(tk['gioi_han_tong_giay'] == 60 and tk['gioi_han_giay_moi_lan'] == 3.0,
         'Mặc định (không bật cờ) vẫn đúng 60 giây / 3 giây như trước')

    cfg_that = cau_hinh()
    kiem('che_do_tai_lap' not in cfg_that.get('tim_kiem', {}),
         'cauhinh.json THẬT không bật chế độ tái lập — chạy thật giữ nguyên')

    # /api/thu-quy-tac phải GIỮ chặn bằng đồng hồ kể cả khi cauhinh.json bật cờ,
    # vì nó giải NGAY trong luồng HTTP — bỏ chặn là một lượt thử quy tắc giữ
    # luồng rất lâu.
    #
    # Đo QUA HTTP THẬT, không grep mã nguồn: bản đầu tôi viết
    # kiem('che_do_tai_lap=False' in ma_web, ...) và nó XANH cả khi đã gỡ tham
    # số ra khỏi lời gọi — vì chuỗi đó còn nằm trong dòng chú thích ngay trên.
    # Ca thử kiểm lời chú thích chứ không kiểm mã. Đúng bài học đã trả giá.
    #
    # Cách phân biệt: dùng cấu hình VÔ NGHIỆM-KHÓ nên mỗi lượt đốt trọn bộ đếm
    # bước (~6 giây). Còn chặn 8 giây thì cả lượt thử xong trong ~10 giây; mất
    # chặn thì 30 lượt × 6 giây ≈ 3 phút.
    tmx = tempfile.mkdtemp(prefix='tailap_')
    try:
        def bat_co_va_vo_nghiem(cfg):
            cfg['tim_kiem'] = {'so_lan_thu': 30, 'seed': 1,
                               'gioi_han_buoc': 20000,
                               'che_do_tai_lap': True}
            cfg['quy_tac'] = [{'loai': 'chi_xep_thu',
                               'ghi_chu': 'CỐ Ý VÔ NGHIỆM',
                               'loc': {}, 'thu': [2, 3]}]
        dd = cau_hinh_tam(tmx, bat_co_va_vo_nghiem)
        with MayChuTam(dd) as (k, _):
            t0 = time.time()
            ma, _ = k.post('/api/thu-quy-tac', {'tat': []})
            giay = time.time() - t0
        kiem(ma == 200, f'/api/thu-quy-tac vẫn trả lời được — {ma}')
        kiem(giay < 30,
             f'Dù cauhinh.json BẬT che_do_tai_lap, /api/thu-quy-tac vẫn bị chặn '
             f'bằng đồng hồ: xong sau {giay:.1f}s (mất chặn thì ~180s)')
    finally:
        shutil.rmtree(tmx, ignore_errors=True)


# ==========================================================================
if __name__ == '__main__':
    print('=' * 74)
    print(' THỬ CHẾ ĐỘ TÁI LẬP')
    print('=' * 74)
    ca_1_co_bo_that_hai_gioi_han()
    ca_2_cung_tien_trinh()
    ca_3_hai_tien_trinh()
    ca_4_vo_nghiem_van_dung()
    ca_5_khong_hoi_quy()
    print('=' * 74)
    hong = [m for ok, m in KQ if not ok]
    print(f'Tổng: {len(KQ) - len(hong)}/{len(KQ)} mục ĐẠT.')
    if hong:
        for m in hong:
            print('  LỖI:', m)
        sys.exit(1)

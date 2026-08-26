#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 SINH DỮ LIỆU MỘT TUẦN ĐỂ ĐĂNG — và KHÔNG CÓ LỐI VÒNG
--------------------------------------------------------------------------
 ┌──────────────────────────────────────────────────────────────────────┐
 │ ĐƯỜNG DUY NHẤT LẤY ĐƯỢC DỮ LIỆU LÀ `kho_tuan.ban_de_dang()`.         │
 │                                                                      │
 │ Mô-đun này KHÔNG được:                                               │
 │   · gọi `doc_phieu` / `doc_phieu_ky`                                 │
 │   · đọc `phieu['ban']`                                               │
 │   · nhận một bản, một phiếu, hay một dict đã tách làm THAM SỐ         │
 │                                                                      │
 │ `tests/thu_sinh_dang.py` CA 2 đi trên CÂY CÚ PHÁP của chính tệp này  │
 │ và ĐỎ nếu thấy bất kỳ điều nào ở trên. Đó là ca canh KIẾN TRÚC,      │
 │ không canh kết quả — vì một lối vòng vẫn cho ra kết quả ĐÚNG trong   │
 │ mọi trường hợp bình thường, và chỉ sai đúng vào hôm có bản SAI.      │
 └──────────────────────────────────────────────────────────────────────┘

 VÌ SAO PHẢI GẮT NHƯ VẬY. Tuần 2026-08-24 có hai bản mâu thuẫn; bản 21/8
 bỏ mất 6 tiết chuyên đề Sử và đổi giáo viên, Khoa xác nhận 22/8/2026 là
 SAI. Hai bản nằm cạnh nhau trong cùng một thư mục, tên chỉ khác nhau ở
 giờ lưu. Ai viết một dòng `phieu['ban'][0]` hay `phieu['ban'][-1]` cho
 nhanh thì có 50% cơ hội đăng đúng bản sai đó ra cho cả trường đọc, và
 **git thì nhớ vĩnh viễn**.

 KHÔNG GHI VÀO `docs/`. Mô-đun này chỉ TRẢ VỀ dict. Việc ghi ra tệp là của
 người gọi, và `luu_tuan.py dang-thu` cố ý ghi vào thư mục TẠM, đồng thời
 TỪ CHỐI mọi đường dẫn nằm trong `docs/`.

 KHÔNG ĐĂNG TỆP .xlsx GỐC — chỉ đăng dữ liệu ĐÃ TÁCH. Lý do có số đo:
 `docProps/core.xml` của chính tệp tuần 1 chứa `lastModifiedBy` là tên một
 người, và bản 21/8 còn có sheet `THEO DÕI BÙ TBK` thường kèm lý do nghỉ.

 CÁC TRƯỜNG RA NGOÀI = ĐÚNG BẰNG những gì trang xem hiện tại đã hiện
 (`xuat_html.du_lieu()`): tên lớp · họ tên GVCN · tên viết tắt GV bộ môn ·
 môn · thứ và tiết · tuần. KHÔNG thêm trường mới — muốn thêm thì hỏi
 người dùng, đúng như lúc xin phép công khai TKB trên GitHub Pages.

 ┌──────────────────────────────────────────────────────────────────────┐
 │ KHÔNG ĐĂNG **DANH SÁCH NGƯỜI GOM SẴN**. Tên trong TỪNG Ô thì giữ.    │
 │                                                                      │
 │ Hai thứ đó khác hạng nhau, và đây là lý do — người dùng chốt         │
 │ 26/8/2026, nguyên văn: *"Danh sách 28 tên gom một chỗ là danh bạ.    │
 │ Tên trong từng ô thì giữ — tờ TKB dán ở trường xưa nay vẫn vậy.      │
 │ Nhưng danh sách gom sẵn thì trường CHƯA TỪNG PHÁT, và tôi không có   │
 │ phép của ai để phát nó."*                                            │
 │                                                                      │
 │ Tờ giấy dán ở trường có tên cô X ở ô Thứ Ba tiết 6 — ai muốn biết    │
 │ cô X dạy mấy tiết thì phải tự đọc hết bảng. Một khoá `gv` gom sẵn    │
 │ thì làm hộ việc đó cho bất kỳ ai trên Internet, bằng một dòng JSON.  │
 │ Cùng dữ liệu, khác hẳn mức dễ dùng — và mức dễ dùng mới là thứ nhà   │
 │ trường chưa bao giờ quyết.                                           │
 │                                                                      │
 │ Trang xem CẦN danh sách để lọc thì **dựng lúc chạy từ chính 144 ô**  │
 │ (`[...new Set(o.map(r => r[4]))]`), đừng đăng thành khoá riêng.      │
 │ `tests/thu_sinh_dang.py` CA 1c canh điều này trên HÀNH VI: không     │
 │ khoá cấp trên nào được là một danh sách TÊN NGƯỜI gom sẵn.           │
 │                                                                      │
 │ 26/8/2026 người dùng bỏ tiếp khoá `lop` **cùng một lẽ** — nó cũng    │
 │ chỉ là `sorted({r[0] for r in o})`, tức một bản sao của thứ đã nằm   │
 │ sẵn trong 144 ô. Nay KHÔNG khoá cấp trên nào là bản sao của một cột  │
 │ trong `o`; CA 1c canh cả lớp lỗi đó chứ không riêng hai cái tên.     │
 │                                                                      │
 │ HỆ QUẢ ĐÃ BIẾT VÀ ĐÃ CHẤP NHẬN: lớp nghỉ TRỌN TUẦN, không có ô nào,  │
 │ sẽ biến mất khỏi ô chọn của trang. **Đó KHÔNG phải lỗi.** Trang này  │
 │ nói *tuần này học gì*; lớp không có tiết nào thì không có gì để      │
 │ hiện. Người dùng chốt 26/8/2026. Đo trên tuần 2026-08-24: cả 6 lớp   │
 │ đều có 24 ô, số lớp không có ô nào là 0.                             │
 └──────────────────────────────────────────────────────────────────────┘
==========================================================================
"""
import io
import json
import os
import re

import kho_tuan as K

# Đúng bộ trường mà trang xem hiện tại đã hiện. Thêm vào đây là MỞ RỘNG
# phạm vi công khai — phải hỏi người dùng trước.
TRUONG_O = ('lop', 'thu', 'tiet', 'mon', 'gv')

# ==========================================================================
# CỬA KHUÔN — CHỮ TỰ DO KHÔNG QUA ĐƯỢC CỬA ĐĂNG
# ==========================================================================
# Người dùng chốt 26/8/2026, nguyên văn: *"Rà toàn phiếu, liệt kê MỌI trường
# chữ tự do, chặn hết. Không chừa trường nào vì 'câu hiện tại vô hại' — câu
# hiện tại là câu tôi viết, câu sau thì chưa ai viết."*
#
# Rà ra được **năm** trường chữ tự do đang đi thẳng ra công khai, không phải
# một: `ly_do` · `nhan` · `nam_hoc` · `hoc_ky` · `tieu_de`. Bốn cái đầu vào
# phiếu qua `--nhan` / `--nam-hoc` / `--hoc-ky` / `--ly-do`, không khoá nào
# kiểm lấy một ký tự.
#
# CÁCH BỊT KHÔNG PHẢI DANH SÁCH CẤM, MÀ LÀ **KHUÔN**. Danh sách cấm thì mỗi
# trường mới thêm vào phiếu lại lọt cho tới khi có người nhớ ra; khuôn thì
# trường nào chưa khai khuôn là **không ra được**, im lặng cũng không ra.
# Một trường đã ép khuôn thì thôi không còn là chữ tự do nữa — đó mới là
# điều đang cần, chứ không phải bỏ hẳn trường đi.
KHUON_TUAN = {
    'ma_tuan':  r'^\d{4}-\d{2}-\d{2}$',      # ngày Thứ Hai, khoá kho
    'nhan':     r'^TUẦN \d{1,2}$',             # "TUẦN 1"
    'tu_ngay':  r'^\d{4}-\d{2}-\d{2}$',
    'den_ngay': r'^\d{4}-\d{2}-\d{2}$',
    'nam_hoc':  r'^\d{4}-\d{4}$',             # "2026-2027"
    'hoc_ky':   r'^[12]$',
}

# Khoá của MỘT BẢN được phép ra ngoài. Cả ba đều MÁY SINH, không có đường
# nào cho người gõ chữ vào: mốc thời gian ISO, 64 hex, và dấu bộ đọc.
# `ly_do` CỐ Ý KHÔNG có ở đây — xem khối chữ dưới.
TRUONG_NGUON = ('gio_luu', 'sha256', 'bo_doc')


def _qua_khuon(khoa, gt):
    """Giá trị có đúng KHUÔN đã khai không. Trả (giá trị, None) hoặc
       (None, câu từ chối). Không khai khuôn thì KHÔNG QUA — fail-closed."""
    mau = KHUON_TUAN.get(khoa)
    if mau is None:
        return None, (f'Trường {khoa!r} chưa khai khuôn trong KHUON_TUAN nên '
                      'KHÔNG được đăng. Thêm khuôn là MỞ RỘNG phạm vi công '
                      'khai — phải hỏi nhà trường, đúng như TRUONG_O.')
    # THIẾU HẲN ≠ SAI KHUÔN, và phân biệt hai cái là bắt buộc.
    # Phiếu không khai `nhan` là chuyện THƯỜNG — `them_ban` không đòi
    # `--nhan`. Không khai thì đăng None: không một ký tự nào ra ngoài, mà
    # cũng không chặn oan cả tuần. Còn CÓ KHAI mà sai khuôn thì đúng là có
    # người vừa gõ chữ vào, và lúc đó phải DỪNG.
    # (Bản đầu gộp hai cái làm một: `nhan is None` cũng bị từ chối, và ca
    #  thử CA 1d đỏ ngay lượt chạy đầu — kho thử không khai `nhan` bao giờ.)
    if gt is None:
        return None, None
    if not isinstance(gt, str) or not re.match(mau, gt):
        return None, (
            f'Trường {khoa!r} của phiếu không đúng khuôn {mau} — đang là '
            f'{gt!r}. KHÔNG đăng, và cố ý KHÔNG lặng lẽ bỏ qua: một ô chữ '
            'tự do lọt ra trang công khai thì không rút lại được, còn git '
            'thì nhớ vĩnh viễn. Sửa phiếu cho đúng khuôn rồi đăng lại.')
    return gt, None


def _cau_khai_nguon(ngay_truong_sua, sha256):
    """Dòng KHAI NGUỒN của trang, sinh TỪ TRƯỜNG CÓ CẤU TRÚC.

       KHÔNG có ô nào cho người gõ chữ tự do vào dòng này — nó ghép từ đúng
       hai giá trị máy sinh: `dcterms:modified` của chính tệp trường phát,
       và 12 hex đầu của SHA-256.

       ┌──────────────────────────────────────────────────────────────────┐
       │ THIẾU NGÀY THÌ NÓI LÀ KHÔNG CÓ — TUYỆT ĐỐI KHÔNG THAY BẰNG       │
       │ `gio_luu`. Thà TRỐNG còn hơn NÓI SAI NGÀY.                       │
       │                                                                  │
       │ `gio_luu` là lúc BẤM LỆNH LƯU VÀO KHO, không phải ngày trường    │
       │ sửa tệp. Đo 26/8/2026 trên bản tuần 1: lưu 22/8 11:32, tệp sửa   │
       │ lần cuối 18/8 17:06 — LỆCH BỐN NGÀY. Thầy cô đọc trang này để    │
       │ biết *tờ này trường phát ngày nào*, không phải để biết ai đó bấm │
       │ lệnh lúc nào. Một con số sai bốn ngày mà trông như đúng thì tệ   │
       │ hơn hẳn một ô trống có ghi rõ là trống.                          │
       │                                                                  │
       │ Bản tách sinh bởi bộ đọc PHIÊN BẢN 1 không có khoá này — nên     │
       │ nhánh "không rõ" là đường ĐANG ĐI THẬT với mọi bản lưu trước     │
       │ 26/8/2026, không phải nhánh phòng xa.                            │
       └──────────────────────────────────────────────────────────────────┘

       Ngày giữ NGUYÊN VĂN chuỗi ISO của Excel (`...T17:06:19Z`), không đổi
       múi giờ — xem `doc_tkb._ngay_truong_sua()`.
    """
    if not isinstance(sha256, str):
        return None
    if isinstance(ngay_truong_sua, str) and ngay_truong_sua:
        ngay = f'sửa lần cuối {ngay_truong_sua}'
    else:
        ngay = ('KHÔNG RÕ ngày trường sửa — bản này lưu bằng bộ đọc đời cũ, '
                'chưa đọc được ngày từ tệp')
    return f'Bản nhà trường phát, {ngay} · SHA-256 {sha256[:12]}…'


def du_lieu_dang(goc, ma_tuan):
    """Trả (dict để đăng, None) hoặc (None, câu từ chối). KHÔNG BAO GIỜ NÉM.

       Tham số CHỈ có thư mục kho và mã tuần — cố ý. Không nhận bản, không
       nhận phiếu, không nhận dict đã tách: nhận được thì có lối vòng.
    """
    ds, tu_choi = K.ban_de_dang(goc, ma_tuan)
    if tu_choi:
        return None, tu_choi
    if not ds:
        return None, f'Tuần {ma_tuan} không có bản nào đăng được.'
    if len(ds) > 1:
        return None, (
            f'Tuần {ma_tuan} có {len(ds)} bản đánh dấu "dung" — không biết '
            'đăng bản nào. Đánh dấu lại để chỉ còn ĐÚNG MỘT bản "dung".')

    ban = ds[0]
    dt = ban.get('tach')
    if not dt:
        return None, (f'Bản {ban.get("tep")!r} không có dữ liệu đã tách — '
                      'chỉ có tệp gốc. KHÔNG đăng tệp gốc: nó mang tên người '
                      'sửa cuối trong siêu dữ liệu, và có thể có sheet phụ.')
    dd = os.path.join(K.thu_muc_tuan(goc, ma_tuan), dt)
    try:
        with io.open(dd, encoding='utf-8-sig') as f:
            tach = json.load(f)
    except Exception as e:                              # noqa: BLE001
        return None, f'Không đọc được bản tách {dt}: {type(e).__name__}: {e}'
    if not isinstance(tach, dict) or not isinstance(tach.get('o'), list):
        return None, f'Bản tách {dt} sai cấu trúc.'

    o = []
    for x in tach['o']:
        if not isinstance(x, dict):
            continue
        o.append([x.get(k) for k in TRUONG_O])
    o.sort(key=lambda r: (r[1] or 0, r[2] or 0, str(r[0])))

    # MỌI trường cấp tuần đi qua CỬA KHUÔN. Không khai khuôn thì không ra.
    ra = {'ma_tuan': ma_tuan}
    for khoa in KHUON_TUAN:
        gt = ma_tuan if khoa == 'ma_tuan' else _cua_tuan(goc, ma_tuan, khoa)
        gt, tu_choi = _qua_khuon(khoa, gt)
        if tu_choi:
            return None, tu_choi
        ra[khoa] = gt

    # `nguon` dựng từ DANH SÁCH TRẮNG, không phải bóc từng khoá bằng tay.
    # Bóc tay là cách `ly_do` lọt ra được suốt từ đầu: nó nằm ngay cạnh ba
    # khoá máy sinh, trông y như chúng, và không ai phải quyết gì để nó ra.
    ra['nguon'] = {k: ban.get(k) for k in TRUONG_NGUON}
    # Ngày lấy từ BẢN TÁCH (bộ đọc sinh ra), KHÔNG từ phiếu — phiếu là chỗ
    # người gõ. `.get()` chứ không bóc thẳng: bản tách của bộ đọc phiên bản
    # 1 không có khoá này, và đó là đường đang đi thật.
    ra['nguon']['ngay_truong_sua'] = tach.get('ngay_truong_sua')
    ra['khai_nguon'] = _cau_khai_nguon(tach.get('ngay_truong_sua'),
                                       ban.get('sha256'))

    # ⚠ `tieu_de` KHÔNG ĐI QUA CỬA KHUÔN, và đó là QUYẾT ĐỊNH, không phải
    # bỏ sót. Người dùng đã xét đúng chỗ này và BÁC việc ép khuôn nó —
    # 26/8/2026, nguyên văn: *"tieu_de là ô A3 nguyên văn của trường, cùng
    # hạng với tên môn và tên GV. Ép khuôn là SỬA CHỮ CỦA TRƯỜNG."*
    #
    # Ranh giới chia hai nhóm, và nó là ranh giới về NGUỒN chứ không phải
    # về hình dạng chuỗi:
    #   · CHỮ CỦA NGƯỜI VẬN HÀNH KHO (nhan, nam_hoc, hoc_ky, ly_do,
    #     ghi_chu) -> ÉP KHUÔN. Ta làm ra nó, ta chịu trách nhiệm về nó.
    #   · CHỮ CỦA TRƯỜNG (ô A3, tên môn, tên GV trong từng ô) -> NGUYÊN
    #     VĂN. Trang công khai là bản điện tử của đúng tờ đang treo ở
    #     trường; sửa chữ của trường là làm bản trên mạng khác bản in.
    # Xem CLAUDE.md mục "Hai trang công khai, hai NGUỒN CHỮ".
    ra['tieu_de'] = tach.get('tieu_de')

    ra['truong_o'] = list(TRUONG_O)
    ra['o'] = o
    return ra, None


def _cua_tuan(goc, ma_tuan, khoa):
    """Một khai báo cấp tuần. Đi qua `ban_de_dang` đã chặn xong rồi mới gọi.

       Hàm này CỐ Ý không đọc `phieu['ban']` — nó chỉ lấy đúng một khoá cấp
       tuần, và không có đường nào từ đây tới danh sách bản.

       Và nó CHỈ lấy được khoá đã khai khuôn. Phiếu còn khoá `ghi_chu` cấp
       tuần — chữ tự do thuần tuý — mà một dòng `_cua_tuan(g, m, 'ghi_chu')`
       viết cho nhanh là đủ đưa nó lên Internet. Chặn ngay ở đây thì dòng
       ấy không viết được, chứ không phải viết được rồi trông chờ người sau
       nhớ ra.
    """
    if khoa not in KHUON_TUAN:
        return None
    ds = K.liet_ke(goc)
    for x in ds:
        if x.get('ma_tuan') == ma_tuan:
            p = x.get('phieu') or {}
            return p.get(khoa)
    return None

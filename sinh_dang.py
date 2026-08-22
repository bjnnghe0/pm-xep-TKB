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
==========================================================================
"""
import io
import json
import os

import kho_tuan as K

# Đúng bộ trường mà trang xem hiện tại đã hiện. Thêm vào đây là MỞ RỘNG
# phạm vi công khai — phải hỏi người dùng trước.
TRUONG_O = ('lop', 'thu', 'tiet', 'mon', 'gv')


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

    lop = sorted({r[0] for r in o if r[0]})
    return {
        'ma_tuan': ma_tuan,
        'nhan': _cua_tuan(goc, ma_tuan, 'nhan'),
        'tu_ngay': _cua_tuan(goc, ma_tuan, 'tu_ngay'),
        'den_ngay': _cua_tuan(goc, ma_tuan, 'den_ngay'),
        'nam_hoc': _cua_tuan(goc, ma_tuan, 'nam_hoc'),
        'hoc_ky': _cua_tuan(goc, ma_tuan, 'hoc_ky'),
        'tieu_de': tach.get('tieu_de'),
        'lop': lop,
        'gv': sorted({r[4] for r in o if r[4]}),
        'truong_o': list(TRUONG_O),
        'o': o,
        'nguon': {'gio_luu': ban.get('gio_luu'),
                  'sha256': ban.get('sha256'),
                  'bo_doc': ban.get('bo_doc'),
                  'ly_do_dung': ban.get('ly_do')},
    }, None


def _cua_tuan(goc, ma_tuan, khoa):
    """Một khai báo cấp tuần. Đi qua `ban_de_dang` đã chặn xong rồi mới gọi.

       Hàm này CỐ Ý không đọc `phieu['ban']` — nó chỉ lấy đúng một khoá cấp
       tuần, và không có đường nào từ đây tới danh sách bản.
    """
    ds = K.liet_ke(goc)
    for x in ds:
        if x.get('ma_tuan') == ma_tuan:
            p = x.get('phieu') or {}
            return p.get(khoa)
    return None

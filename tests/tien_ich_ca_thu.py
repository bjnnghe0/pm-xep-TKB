#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 BỎ QUA và GHI CHÚ — MỘT BẢN CÀI DUY NHẤT
--------------------------------------------------------------------------
 `kiem(True, 'bỏ qua vì thiếu X')` là SAI, và sai theo kiểu tệ nhất: nó
 **cộng một mục vào "Tổng: N/N"**. Máy thiếu công cụ vẫn cho ra một bộ thử
 XANH TRỌN VẸN, và người đọc con số ấy không có cách nào biết một mục đã
 không chạy. "Chưa kiểm" và "đã đạt" là hai chuyện khác hẳn nhau.
 Xem nếp hỏng 21 trong CLAUDE.md.

 Ba mức, ba cách in, và chỉ MỘT mức được vào tổng:

   kiem(...)    -> [ĐẠT]/[LỖI]   VÀO tổng. Một phép khẳng định thật.
   bo_qua(...)  -> [BỎ QUA]      KHÔNG vào tổng. Không kiểm được vì
                                 thiếu công cụ ngoài / nền tảng khác /
                                 không dựng nổi cảnh cần thử.
   ghi_chu(...) -> [GHI CHÚ]     KHÔNG vào tổng. Một câu nói cho người
                                 đọc, không phải một phép khẳng định.

 Mỗi bộ thử chạy trong MỘT tiến trình riêng nên danh sách mức mô-đun ở đây
 là đủ — không cần truyền qua lại.

 Bộ thử nào dùng `bo_qua()` thì PHẢI gọi `in_bo_qua()` ngay sau dòng
 "Tổng:", nếu không thì mục bỏ qua biến mất khỏi màn hình và ta quay lại
 đúng chỗ cũ.
==========================================================================
"""

BO_QUA = []


def bo_qua(mo_ta):
    """Mục KHÔNG kiểm được. KHÔNG tính là ĐẠT, KHÔNG vào tổng."""
    BO_QUA.append(mo_ta)
    print(f'  [BỎ QUA] {mo_ta}')


def ghi_chu(mo_ta):
    """Một câu cho người đọc. Không phải phép khẳng định, không vào tổng."""
    print(f'  [GHI CHÚ] {mo_ta}')


def in_bo_qua():
    """In khối cảnh báo cuối bộ thử. Gọi NGAY SAU dòng "Tổng:"."""
    if not BO_QUA:
        return
    print(f'  ⚠ BỎ QUA {len(BO_QUA)} mục — bộ thử này CHƯA kiểm hết:')
    for m in BO_QUA:
        print(f'      · {m}')

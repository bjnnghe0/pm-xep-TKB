#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 GHI TỆP XUỐNG ĐĨA CHO BỀN — MỘT BẢN CÀI DUY NHẤT
--------------------------------------------------------------------------
 VÌ SAO CÓ TỆP NÀY. Trước 22/8/2026 dự án có HAI bản cài của cùng một thao
 tác: `tai_khoan._ghi_nguyen_tu()` và ba hàm rời trong `web.py`
 (`_dong_bo_tep`, `_dong_bo_thu_muc`, `_chep_ben`). Cả hai đều đúng, nhưng
 hai bản cài của một thao tác ghi đĩa là cách chắc nhất để sau này sửa một
 bản rồi quên bản kia — đúng bài học `khop_loc()` / `_cum_cua()` đã ghi
 trong CLAUDE.md, chỉ khác là lần này cái giá phải trả là DỮ LIỆU.

 Nay ba nơi cùng gọi vào đây: `tai_khoan.py`, `web.py`, `kho_tuan.py`.

 KHÔNG PHỤ THUỘC GÌ NGOÀI THƯ VIỆN CHUẨN, và không biết gì về HTTP, về
 cấu hình, về Excel. Thêm một người dùng mới thì không phải sửa tệp này.

 ⚠ GIỚI HẠN ĐÃ BIẾT, ĐỪNG ĐỌC QUÁ. `ben=True` ghim ĐÚNG THỨ TỰ
 fsync/replace/fsync-thư-mục. Nó KHÔNG chứng minh được độ bền vật lý khi
 mất điện thật — muốn chứng minh phải cắt điện thật hoặc dùng dm-flakey
 (đòi quyền root). Xem mục tương ứng trong "Việc treo" của CLAUDE.md.
==========================================================================
"""
import os

__all__ = ['dong_bo_tep', 'dong_bo_thu_muc', 'chep_ben', 'ghi_nguyen_tu']


def dong_bo_tep(f):
    """Ép nội dung tệp ĐANG MỞ xuống đĩa thật."""
    f.flush()
    os.fsync(f.fileno())


def dong_bo_thu_muc(tm):
    """Ép CÁI TÊN vừa đổi xuống đĩa. Trả True nếu đã làm được.

       Trả về bool chứ không nuốt im lặng, để ca thử khẳng định được.

       Trên Windows `os.open()` không mở được thư mục nên bước này bỏ qua —
       nói thẳng ra đây chứ không giấu: phần đổi tên trên NTFS đi qua nhật ký
       siêu dữ liệu nên tương đối bền, còn RỦI RO CÒN LẠI thì vẫn còn. Bước
       fsync tệp tạm mới là bước quan trọng nhất, và bước đó chạy trên cả hai
       hệ điều hành.
    """
    if os.name != 'posix':
        return False
    try:
        fd = os.open(tm, os.O_RDONLY)
    except OSError:
        return False
    try:
        os.fsync(fd)
        return True
    except OSError:
        return False                 # vài hệ tệp không cho fsync thư mục
    finally:
        os.close(fd)


def chep_ben(nguon, dich):
    """`shutil.copy()` nhưng ép xuống đĩa.

       Vì sao bản sao lưu cũng phải fsync: mất điện ngay sau khi bấm Lưu thì
       tệp mới đã bền, nhưng bản sao lưu có thể rỗng — tức mất đúng cái phao
       cứu sinh, trong khi người dùng đinh ninh là có. Đó là kiểu hỏng tệ
       nhất của dự án này: im lặng và mất dữ liệu.
    """
    with open(nguon, 'rb') as f:
        dl = f.read()
    with open(dich, 'wb') as f:
        f.write(dl)
        dong_bo_tep(f)


def ghi_nguyen_tu(duong_dan, chuoi, ben, quyen=None, duoi='.json'):
    """Ghi đè một tệp nhỏ: tệp tạm -> `os.replace`. Không bao giờ để tệp rách.

       `ben=True` thì fsync cả tệp lẫn thư mục cha — dành cho tệp mà mất là
       hỏng việc thật (`tai_khoan.json`, `phieu.json` của kho tuần).
       `ben=False` bỏ fsync, dành cho tệp mà nội dung VỨT ĐI ĐƯỢC — sổ khoá
       tạm chẳng hạn: mất thì mọi người được thử lại từ đầu, không ai bị khoá
       oan, mà nó lại bị ghi ở đường CHƯA XÁC THỰC nên không đáng để một người
       gõ sai mật khẩu ép được ta fsync.

       `quyen` khác None thì đặt quyền NGAY LÚC TẠO (`O_EXCL` + chmod), không
       để hở một khe nào ở 644. Dùng cho `tai_khoan.json` (0o600).

       Tên tệp tạm kèm PID: một lần sập giữa chừng không được phép chặn vĩnh
       viễn mọi lần ghi sau đó. Hai tiến trình cùng ghi cũng không đụng nhau
       vì mỗi bên một tên tạm.
    """
    tam = f'{duong_dan}.tam.{os.getpid()}{duoi}'
    co = os.O_CREAT | os.O_WRONLY | os.O_EXCL
    fd = os.open(tam, co, quyen) if quyen is not None else os.open(tam, co)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as f:
            f.write(chuoi)
            f.flush()
            if ben:
                os.fsync(f.fileno())
        os.replace(tam, duong_dan)
    except BaseException:
        try:
            os.remove(tam)
        except OSError:
            pass
        raise
    if ben:
        dong_bo_thu_muc(os.path.dirname(os.path.abspath(duong_dan)))

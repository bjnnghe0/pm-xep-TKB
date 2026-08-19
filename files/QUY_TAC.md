# DANH MỤC QUY TẮC XẾP THỜI KHÓA BIỂU

Xem nhanh trong máy: `python xep_tkb.py --quy-tac`

Mọi quy tắc đều nằm trong mục `"quy_tac"` của `cauhinh.json`, dạng một danh sách.
Thêm quy tắc = chép thêm một khối `{ ... }` vào danh sách đó. Không giới hạn số lượng.

```json
"quy_tac": [
  { "loai": "khong_xep_thu", "ghi_chu": "Văn cô Duy không xếp Thứ 2",
    "loc": { "gv": "Đ.Duy" }, "thu": [2] },

  { "loai": "...", "ghi_chu": "...", ... }
]
```

Ba khoá dùng chung cho mọi quy tắc:

| Khoá | Ý nghĩa |
|---|---|
| `loai` | **Bắt buộc.** Tên loại quy tắc, lấy từ bảng bên dưới. |
| `ghi_chu` | Câu mô tả bằng tiếng Việt. Câu này hiện nguyên văn ở sheet "Kiểm tra quy tắc". |
| `bat` | Đặt `false` để **tạm tắt** quy tắc mà không phải xoá. Mặc định là bật. |

## Bộ lọc `loc` — chọn quy tắc áp cho ai

| Khoá | Ví dụ |
|---|---|
| `mon` | `"Vật lý"` hoặc `["Toán học", "Ngữ văn"]` |
| `nhom_mon` | `"Sử"` — gộp cả tiết chính lẫn chuyên đề, xem cột `nhom` trong `dinh_muc_mon` |
| `gv` | `"N.Uyên"` hoặc `["N.Uyên", "N.Xuân"]` |
| `lop` | `"12B1"` hoặc `["12B1", "12B2"]` |
| `la_chuyen_de` | `true` = chỉ tiết chuyên đề, `false` = chỉ tiết chính |

Khoá nào **không ghi** thì coi như không lọc theo khoá đó. `"loc": {}` = áp cho tất cả.
Ghi nhiều khoá thì phải thoả **đồng thời** (VD `{"mon":"Hoá học","lop":["12B1","12B2"]}`
= chỉ tiết Hoá của hai lớp đó).

Riêng loại quy tắc so sánh hai nhóm thì thay `loc` bằng hai khoá `a` và `b`,
mỗi khoá là một bộ lọc y hệt trên.

## Cách ghi thứ và tiết

- `thu`: số hiệu thứ trong tuần — `[2, 3]` = Thứ 2 và Thứ 3.
- `tiet`: **số hiệu tiết thật** như in trên TKB — `[9, 10]`.
- `tiet_trong_buoi`: **thứ tự trong buổi**, `1` = tiết đầu buổi. Buổi chiều bắt đầu
  từ tiết 6 nên `tiet_trong_buoi: [4,5]` chính là tiết 9 và 10.
- `o`: danh sách ô cụ thể `[[thứ, tiết], ...]` — VD `[[4, 6], [4, 7]]`.

---

# A. GIỚI HẠN NGÀY / TIẾT

### `chi_xep_thu` — chỉ được xếp vào những thứ liệt kê
```json
{ "loai": "chi_xep_thu", "ghi_chu": "Vật lý 12B1, 12B2 chỉ Thứ 2 hoặc Thứ 3",
  "loc": { "mon": "Vật lý", "lop": ["12B1", "12B2"] }, "thu": [2, 3] }
```

### `khong_xep_thu` — cấm những thứ liệt kê
```json
{ "loai": "khong_xep_thu", "ghi_chu": "Hoá 12B1-12B4 không xếp Thứ 3 và Thứ 5",
  "loc": { "mon": "Hoá học", "lop": ["12B1","12B2","12B3","12B4"] }, "thu": [3, 5] }
```

### `chi_xep_tiet` — chỉ được xếp vào những tiết liệt kê
Cả cụm phải nằm gọn trong khoảng tiết đó.
```json
{ "loai": "chi_xep_tiet", "ghi_chu": "SHCN luôn ở tiết cuối buổi",
  "loc": { "nhom_mon": "SHCN" }, "tiet_trong_buoi": [5] }
```

### `khong_xep_tiet` — cấm những tiết liệt kê
```json
{ "loai": "khong_xep_tiet", "ghi_chu": "Sử cô Ngọc Uyên không xếp tiết 4, tiết 5",
  "loc": { "gv": "N.Uyên", "nhom_mon": "Sử" }, "tiet_trong_buoi": [4, 5] }
```

### `khong_xep_o` — cấm từng ô cụ thể (thứ + tiết)
Dùng khi thầy cô bận cố định một vài buổi trong tuần.
```json
{ "loai": "khong_xep_o", "ghi_chu": "Thầy Nam bận họp Thứ 4 tiết 6, 7",
  "loc": { "gv": "H.Nam" }, "o": [[4, 6], [4, 7]] }
```

### `co_dinh` — ghim cứng vào đúng một ô
Nếu bộ lọc khớp nhiều cụm thì chỉ cụm đầu tiên của mỗi lớp bị ghim.
```json
{ "loai": "co_dinh", "ghi_chu": "SHCN 12B1 cố định Thứ 6 tiết 10",
  "loc": { "mon": "SHCN", "lop": "12B1" }, "thu": 6, "tiet": 10 }
```

---

# B. QUAN HỆ GIỮA CÁC TIẾT

### `khac_ngay` — hai nhóm không được rơi vào cùng một ngày
`pham_vi`: `"toan_truong"` (mặc định) hoặc `"moi_lop"` (chỉ xét trong từng lớp).
```json
{ "loai": "khac_ngay", "ghi_chu": "Sử cô Lê Xuân không cùng ngày với lịch thầy Hùng",
  "a": { "gv": "N.Xuân" }, "b": { "gv": "M.Hùng" } }
```

### `cung_ngay` — nhóm a phải rơi vào ngày mà nhóm b cũng có tiết
```json
{ "loai": "cung_ngay", "ghi_chu": "Chuyên đề Toán học đúng ngày có tiết Toán chính",
  "a": { "mon": "Chuyên đề Toán" }, "b": { "mon": "Toán học" } }
```

### `toi_da_tiet_moi_ngay` — trần số tiết trong một ngày
`theo`: `"gv"` | `"lop"` | `"mon_lop"` (số tiết cùng một môn trong một lớp).
```json
{ "loai": "toi_da_tiet_moi_ngay", "ghi_chu": "Mỗi giáo viên dạy tối đa 4 tiết/buổi",
  "loc": {}, "theo": "gv", "so": 4 }
```

### `toi_da_ngay_moi_tuan` — trần số buổi phải lên lớp trong tuần
`theo`: `"gv"` (mặc định) | `"lop"`.
```json
{ "loai": "toi_da_ngay_moi_tuan", "ghi_chu": "Cô Ngọc Uyên tối đa 3 buổi/tuần",
  "loc": { "gv": "N.Uyên" }, "theo": "gv", "so": 3 }
```

### `khong_ke_nhau` — hai nhóm không được xếp sát nhau
Xét trong cùng một lớp, cùng một buổi.
```json
{ "loai": "khong_ke_nhau", "ghi_chu": "Không xếp Toán sát ngay Vật lý",
  "a": { "nhom_mon": "Toán" }, "b": { "nhom_mon": "Lý" } }
```

### `phai_ke_nhau` — nhóm a bắt buộc nằm sát nhóm b
Quy tắc **cứng**. Nếu bật lên mà báo không xếp được thì đổi sang
`uu_tien_ke_nhau` (mềm) ở phần D.
```json
{ "loai": "phai_ke_nhau", "ghi_chu": "Chuyên đề Toán phải nối tiếp tiết Toán chính",
  "a": { "mon": "Chuyên đề Toán" }, "b": { "mon": "Toán học" } }
```

---

# C. GOM TIẾT

### `gom_tiet` — đổi cách chia cụm cho riêng một môn/lớp
Ghi đè lên `dinh_muc_mon`. Đây là chỗ quyết định "gom hay không gom".

| Khai báo | Ý nghĩa |
|---|---|
| `[2]` | 2 tiết dính liền trong 1 buổi |
| `[3]` | 3 tiết dính liền (HĐTN) |
| `[2, 1]` | 3 tiết chia 2 buổi: một buổi 2 tiết, một buổi 1 tiết |
| `[1, 1]` | 2 tiết tách hẳn ra 2 buổi khác nhau |

```json
{ "loai": "gom_tiet", "ghi_chu": "Riêng 12B5, 12B6 tách Hoá ra 2 buổi",
  "loc": { "mon": "Hoá học", "lop": ["12B5", "12B6"] }, "cum": [1, 1] }
```

---

# D. TIÊU CHÍ MỀM (không bắt buộc, chỉ chấm điểm)

Chương trình chạy hàng trăm phương án rồi giữ lại phương án **tổng điểm cao nhất**.
`diem` càng lớn thì tiêu chí đó càng được coi trọng; ghi số âm để né tránh.

### `uu_tien_o` — cộng điểm khi xếp đúng thứ/tiết mong muốn
```json
{ "loai": "uu_tien_o", "ghi_chu": "Ưu tiên Toán, Văn vào 2 tiết đầu buổi",
  "loc": { "nhom_mon": ["Toán", "Văn"] }, "tiet_trong_buoi": [1, 2], "diem": 3 }
```

### `uu_tien_ke_nhau` — cộng điểm khi nhóm a nằm sát nhóm b
Đặt `cung_nhom_mon: true` để chỉ tính khi hai cụm thuộc cùng một môn.
```json
{ "loai": "uu_tien_ke_nhau", "ghi_chu": "Nên xếp chuyên đề nối tiếp tiết chính",
  "a": { "la_chuyen_de": true }, "b": { "la_chuyen_de": false },
  "cung_nhom_mon": true, "diem": 12 }
```

### `uu_tien_it_buoi` — dồn buổi cho giáo viên
Trừ điểm theo tổng số buổi thầy cô phải lên lớp.
```json
{ "loai": "uu_tien_it_buoi", "ghi_chu": "Giáo viên ít phải lên lớp", "loc": {}, "diem": 4 }
```

### `uu_tien_trai_deu` — trải môn đều trong tuần
Cộng điểm khi hai buổi của cùng một môn cách nhau từ `cach` ngày trở lên.
```json
{ "loai": "uu_tien_trai_deu", "ghi_chu": "Hai buổi cùng môn cách nhau ≥ 2 ngày",
  "loc": {}, "cach": 2, "diem": 3 }
```

---

# E. Hai luật nền

Nằm riêng ở mục `"luat_chung"`, áp cho toàn bộ TKB, chỉ bật/tắt:

```json
"luat_chung": {
  "khong_tiet_trong_giua_buoi": true,   // dồn tiết trống về cuối buổi
  "mot_cum_moi_mon_moi_ngay": true      // một môn không xếp 2 lần trong 1 ngày
}
```

> `mot_cum_moi_mon_moi_ngay` xét theo **tên môn**, nên "Toán học" và
> "Chuyên đề Toán" vẫn được phép chung một ngày.

---

# F. Khi báo "KHÔNG XẾP ĐƯỢC"

Nghĩa là các quy tắc đang mâu thuẫn, không tồn tại lời giải nào. Làm theo thứ tự:

1. Nếu chương trình chỉ đích danh cụm bị **"chặn hết mọi ô"** → sửa đúng quy tắc
   liên quan đến cụm đó.
2. Tăng `so_lan_thu` và `gioi_han_tong_giay` trong mục `tim_kiem` — đôi khi chỉ là
   chưa tìm đủ lâu.
3. Thêm `"bat": false` vào từng quy tắc mới thêm gần đây để tìm ra cái nào gây kẹt.
4. Quy tắc hay gây kẹt nhất là `chi_xep_thu` bó vào ít ngày, `phai_ke_nhau`,
   và `toi_da_ngay_moi_tuan` đặt số quá nhỏ.

Nếu tìm được lời giải nhưng vẫn còn quy tắc vi phạm, chương trình sẽ **cảnh báo**
và vẫn xuất phương án gần đúng nhất — mở sheet "Kiểm tra quy tắc" để xem dòng nào
màu đỏ.

---

# G. Tự viết thêm một LOẠI quy tắc mới

Chỉ khi 17 loại trên không diễn tả được yêu cầu. Mở `quy_tac.py`, chép một lớp có
sẵn rồi sửa. Mỗi quy tắc có tối đa 7 móc nối, cài cái nào cần thì cài:

| Móc nối | Chạy lúc nào | Dùng để |
|---|---|---|
| `thu_hep_mien()` | 1 lần trước khi giải | Cắt bớt ngày/tiết được phép. Nhanh nhất, ưu tiên dùng. |
| `cho_phep(gs, c, ngay, v)` | trong lúc giải | Trả `False` để chặn một nước đi. |
| `dat()` / `go()` | trong lúc giải | Cập nhật bộ đếm riêng khi đặt/gỡ một cụm. |
| `thich(gs, c, ngay, v)` | trong lúc giải | Trả `True` = "ô này đẹp", chương trình thử ô đó trước. |
| `hoan(gs, c)` | trong lúc giải | Trả `True` = "khoan xếp cụm này, chờ cụm khác đã". |
| `hau_kiem()` | sau khi giải | Trả danh sách chỗ vi phạm để in ra bảng đối chiếu. |
| `diem()` | sau khi giải | Điểm mềm, càng cao càng được ưu tiên chọn. |

Ví dụ đầy đủ một loại quy tắc mới — *"môn X không được xếp vào buổi cuối tuần"*:

```python
@dang_ky('khong_cuoi_tuan')
class KhongCuoiTuan(QuyTac):
    MO_TA = 'Không xếp vào ngày cuối cùng của tuần học.'
    VI_DU = {"loai": "khong_cuoi_tuan", "loc": {"mon": "Vật lý"}}

    def thu_hep_mien(self):
        cuoi = self.bt.SO_NGAY - 1
        for c in self.cac_cum():          # cac_cum() = các cụm khớp bộ lọc "loc"
            c.ngay_ok -= {cuoi}

    def hau_kiem(self):
        cuoi = self.bt.SO_NGAY - 1
        return [self.ten_o(c) for c in self.cac_cum() if c.ngay == cuoi]
```

Lưu file, chạy `python tu_kiem_tra.py` để chắc chắn không làm hỏng gì, rồi dùng ngay
trong `cauhinh.json`. Không phải đụng vào `xep_tkb.py`.

**Thông tin có sẵn trong mỗi cụm `c`:** `c.lop` `c.mon` `c.nhom` `c.gv` `c.size`
`c.la_cd` `c.ngay` `c.vitri`. `ngay` đếm từ 0 (0 = thứ đầu tiên trong `cac_thu`),
`vitri` đếm từ 0 (0 = tiết đầu buổi).

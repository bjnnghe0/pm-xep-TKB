# PHẦN MỀM XẾP THỜI KHÓA BIỂU — Khối 12

Tự xếp TKB thoả toàn bộ quy tắc đã khai báo, rồi xuất ra file Excel **đúng y mẫu
TKB Tuần 1** (giữ nguyên khung, font, viền, công thức tổng tiết).

Quy tắc để **rời** trong `cauhinh.json`, thêm bao nhiêu cũng được mà không phải
sửa code. Tra cứu đầy đủ 17 loại quy tắc: **`QUY_TAC.md`**.

---

## 1. Bộ file

| File | Vai trò | Có cần sửa? |
|---|---|---|
| `cauhinh.json` | Lớp, giáo viên, số tiết, **và toàn bộ quy tắc** | **Đây là nơi làm việc chính** |
| `QUY_TAC.md` | Tra cứu 17 loại quy tắc, có ví dụ chép được ngay | Đọc |
| `HUONG_DAN.md` | File này | Đọc |
| `xep_tkb.py` | Bộ giải + xuất Excel | Không |
| `quy_tac.py` | Định nghĩa các loại quy tắc | Chỉ khi tự viết thêm loại mới |
| `mau_tkb.xlsx` | File mẫu (TKB Tuần 1 đã xoá nội dung tiết) | Khi đổi phòng học, GVCN |
| `tu_kiem_tra.py` | Chạy thử mọi loại quy tắc | Chạy sau khi sửa `quy_tac.py` |
| `chay.bat` | Bấm đúp để chạy trên Windows | Không |
| `TKB_Khoi12.xlsx` | Kết quả | — |

## 2. Cài đặt (làm một lần)

1. Cài **Python** tại python.org — nhớ tick **"Add Python to PATH"** ở màn hình đầu.
2. Mở Command Prompt, gõ: `pip install openpyxl`

## 3. Chạy

Bấm đúp `chay.bat`, hoặc mở Command Prompt tại thư mục này:

```
python xep_tkb.py                      xếp và xuất Excel
python xep_tkb.py --quy-tac            xem danh mục quy tắc + mẫu chép sẵn
python xep_tkb.py --in-man-hinh        xem luôn TKB trên màn hình
python xep_tkb.py --seed 99            ra một phương án khác hẳn
python xep_tkb.py --xuat TKB_T3.xlsx   đổi tên file kết quả
python tu_kiem_tra.py                  chạy thử toàn bộ các loại quy tắc
```

> **Mẹo:** mỗi `--seed` cho một phương án khác nhau nhưng đều hợp lệ.
> Chạy vài seed rồi chọn cái nhìn thuận mắt nhất.

## 4. File kết quả có 3 sheet

- **Khối 12** — TKB chính, đúng mẫu Tuần 1, in ra ký ngay được.
- **TKB giáo viên** — lịch dạy của từng thầy cô, dò chéo cho nhanh.
- **Kiểm tra quy tắc** — đối chiếu ĐẠT/LỖI **từng quy tắc một**, kèm điểm các tiêu
  chí mềm và bảng số tiết / số buổi của mỗi giáo viên.

---

## 5. Thêm một quy tắc mới

Mở `cauhinh.json` bằng Notepad, tìm mục `"quy_tac"`, chép thêm một khối vào:

```json
"quy_tac": [
  ... các quy tắc cũ ...,

  { "loai": "khong_xep_o",
    "ghi_chu": "Thầy Nam bận họp Thứ 4 tiết 6, 7",
    "loc": { "gv": "H.Nam" },
    "o": [[4, 6], [4, 7]] }
]
```

Ba việc cần làm:
1. Chọn `loai` phù hợp — xem `QUY_TAC.md` hoặc chạy `python xep_tkb.py --quy-tac`.
2. Viết `ghi_chu` bằng tiếng Việt — câu này hiện nguyên văn ở sheet "Kiểm tra quy tắc".
3. Chạy lại chương trình, xem dòng tương ứng có báo ĐẠT không.

**Tạm tắt một quy tắc** mà không xoá: thêm `"bat": false` vào khối đó.

Trong `cauhinh.json` có sẵn mục `"_quy_tac_de_san_chua_bat"` chứa 7 quy tắc mẫu
đang tắt. Muốn dùng cái nào thì chép sang mục `"quy_tac"` rồi sửa `"bat"` thành
`true` (hoặc bỏ hẳn dòng `bat`).

## 6. Các mục khác trong `cauhinh.json`

### Đổi tuần / tiêu đề
```json
"tuan": "TUẦN 3 (07/9/2026-12/9/2026)"
```

### Đổi khung giờ học
```json
"khung_gio": { "cac_thu": [2,3,4,5,6], "buoi": "Chiều", "cac_tiet": [6,7,8,9,10] }
```
Đang để 5 ngày × 5 tiết = 25 ô/lớp, ghi vào vùng **D8:I32** của file mẫu.

Dưới vùng đó, `mau_tkb.xlsx` còn **hai khối Thứ 7** đang để trống:

| Dòng | Khối |
|---|---|
| 33–37 | Thứ 7 – **Sáng**, tiết 1–5 |
| 38–42 | Thứ 7 – **Chiều**, tiết 6–10 |

> **⚠ Cẩn thận khi thêm Thứ 7.** Chương trình ghi **tuần tự** theo đúng thứ tự
> các ngày trong `cac_thu`, mỗi ngày chiếm số dòng bằng số tiết trong buổi (hiện
> là 5), và **không hề đọc nhãn buổi ở cột B**. Nên nếu thêm `7` vào `cac_thu`
> của buổi **Chiều**, ngày Thứ 7 sẽ rơi xuống dòng 33–37 — tức là khối **Thứ 7
> Sáng**: sai buổi và sai cả số hiệu tiết (mẫu ghi tiết 1–5 trong khi đang xếp
> tiết 6–10).
>
> Muốn đúng thì chọn một trong hai cách: sửa nhãn buổi/tiết ở cột B, C của
> `mau_tkb.xlsx` cho khớp với thực tế, **hoặc** giữ nguyên mẫu và đổi
> `vi_tri_bang` trong `cauhinh.json` để bảng bắt đầu ở dòng khác.

Công thức tổng tiết ở dòng 43 là `=COUNTA(D8:D42)` nên đã tính sẵn cả hai khối
Thứ 7, không phải sửa gì thêm.

### Đổi giáo viên hoặc số tiết một môn
Trong `phan_cong`, mỗi dòng là `["Tên môn", "GV viết tắt", số tiết/tuần]`:
```json
"12B1": [
  ["Toán học", "M.Hạnh", 3],
  ["Vật lý", "T.V.Quỳnh", 2]
]
```

### Thêm một môn mới
Khai báo trong `dinh_muc_mon` trước, rồi mới dùng được ở `phan_cong`:
```json
"Tin học": { "nhom": "Tin", "cum": [2] }
```
`nhom` là tên ngắn để lọc trong quy tắc; `cum` là cách gom tiết (xem `QUY_TAC.md` mục C).

---

## 7. Khi báo "KHÔNG XẾP ĐƯỢC"

Xem mục F của `QUY_TAC.md`. Tóm tắt: tăng `so_lan_thu` / `gioi_han_tong_giay`
trong mục `tim_kiem`, hoặc thêm `"bat": false` vào từng quy tắc mới thêm gần đây
để tìm ra cái nào gây kẹt.

---

## 8. Dữ liệu đang khai báo sẵn

- 6 lớp 12B1–12B6, học **buổi chiều, tiết 6–10, Thứ 2 → Thứ 6** (Thứ 7 để trống,
  giống Tuần 1).
- Mỗi lớp **24 tiết/tuần** trên 25 ô → mỗi lớp được nghỉ 1 tiết cuối của một buổi.
- Toán 3+1, Văn 3+1, Sử 2+1, Địa 2+1, HĐTN 3, GDKT-PL 2, Hoá 2, SHCN 1;
  Vật lý 2 (12B1, 12B2), Sinh học 2 (12B3–12B6).
- Giáo viên từng lớp lấy theo TKB Tuần 1, vì hai file PCCM chỉ ghi số lớp chứ không
  ghi lớp nào; riêng file tổ KHTN còn ghi *"Chưa PCCM môn vật lý và sinh học"*.
  **Nếu phân công năm 2026–2027 khác đi, chỉ cần sửa lại mục `phan_cong`.**

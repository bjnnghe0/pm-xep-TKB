# Dự án: Phần mềm xếp thời khóa biểu

Khoa Khoa học Cơ bản — Trường Cao đẳng Đà Lạt. Xếp TKB 6 lớp khối 12
(12B1–12B6), buổi chiều tiết 6–10, Thứ 2 → Thứ 6. Mỗi lớp 24 tiết/tuần trên
lưới 25 ô (5 ngày × 5 tiết), dư đúng 1 ô trống.

Người dùng cuối là giáo viên, **không biết lập trình**: họ chỉ mở
`cauhinh.json` bằng Notepad và bấm đúp `chay.bat`.

---

## Lệnh hay dùng

```bash
python xep_tkb.py                      # xếp và xuất TKB_Khoi12.xlsx
python xep_tkb.py --quy-tac            # in danh mục 17 loại quy tắc + mẫu JSON
python xep_tkb.py --in-man-hinh        # in luôn TKB ra màn hình
python xep_tkb.py --seed 99 --lan 800  # đổi seed / số lần thử
python xep_tkb.py --cauhinh khac.json  # dùng file cấu hình khác
python xep_tkb.py --xuat TKB_T3.xlsx   # đổi tên file kết quả
python xep_tkb.py --tuan "TUẦN 3 ..."  # đổi dòng chữ tuần, không sửa cauhinh.json
python tu_kiem_tra.py                  # BẮT BUỘC chạy sau mỗi lần sửa quy_tac.py
python tests/thu_du_phong.py           # thử nhánh dự phòng của main()
python tests/thu_kiem_khai_bao.py      # thử việc bắt lỗi khai sai thứ / tiết
python tests/thu_loc_tru.py            # thử khoá "tru" trong bộ lọc
python tests/thu_gop_bo_loc.py         # thử hai chỗ lọc dùng chung khop_loc()
python tests/thu_web.py                # thử giao diện web

python web.py                          # giao diện web -> http://127.0.0.1:20266
python web.py --port 8080              # đổi cổng; Ctrl+C để tắt
```

### Môi trường Python trên máy này (Linux)
Máy này **không có `pip`** và không có `python` (chỉ có `python3`), lại bị PEP 668
chặn cài gói vào hệ thống. Đã dựng sẵn một venv dùng chung:

```bash
~/.venvs/xeptkb/bin/python xep_tkb.py       # thay cho "python xep_tkb.py"
~/.venvs/xeptkb/bin/python tu_kiem_tra.py
```

Dựng lại khi cần: `python3 -m venv ~/.venvs/xeptkb && ~/.venvs/xeptkb/bin/pip install openpyxl`
(hiện dùng Python 3.12.3 + openpyxl 3.1.5).

Trên máy Windows của nhà trường thì vẫn đúng như `HUONG_DAN.md`: cài Python,
chạy `pip install openpyxl`, rồi bấm đúp `chay.bat`.

---

## Phân vai file

| File | Chứa gì | Nguyên tắc |
|---|---|---|
| `cauhinh.json` | Dữ liệu (lớp, GV, số tiết) + toàn bộ danh sách quy tắc | Người dùng cuối sửa. Không phá cấu trúc. |
| `cauhinh.khoi12.goc.json` | **Bản gốc chỉ có khối 12**, đóng băng ở tag `v1.0-khoi12` | **KHÔNG được sửa.** Chỉ để đối chiếu |
| `quy_tac.py` | 17 loại quy tắc, registry `DANH_MUC` | **Mọi logic nghiệp vụ nằm ở đây** |
| `xep_tkb.py` | Mô hình dữ liệu, bộ giải, hậu kiểm, xuất Excel | **Không được hardcode quy tắc nghiệp vụ** |
| `mau_tkb.xlsx` | Mẫu Excel của trường (1 sheet "Khối 12") | Chương trình copy rồi ghi đè D8:I32 |
| `TKB_Khoi12.xlsx` | Kết quả (3 sheet) | File sinh ra, ghi đè mỗi lần chạy |
| `tu_kiem_tra.py` | Chạy thử từng loại quy tắc | Chạy sau mỗi thay đổi |
| `tests/thu_du_phong.py` | Ép nhánh dự phòng của `main()` xảy ra bằng một lớp quy tắc dùng-một-lần, chỉ đăng ký trong tiến trình thử | Chạy khi sửa `main()` |
| `tests/thu_kiem_khai_bao.py` | Bảng 4 tổ hợp `tiet` / `tiet_trong_buoi`, khoá `thu`, khoá `o` | Chạy khi sửa `tap_tiet()` / `tap_ngay()` |
| `tests/thu_loc_tru.py` | Khoá `tru` ở cả `khop()` lẫn `_cum_cua()` | Chạy khi sửa bộ lọc |
| `tests/thu_gop_bo_loc.py` | Hai chỗ lọc cho kết quả giống hệt nhau | Chạy khi sửa `khop_loc()` |
| `web.py` + `web/` | Giao diện web cục bộ (chỉ thư viện chuẩn) | Chỉ gọi vào `xep_tkb.py`, không sửa |
| `tests/thu_web.py` | Web: giống dòng lệnh, bắt `SystemExit`, khoá một-lượt | Chạy khi sửa `web.py` |
| `chay.bat` | Bấm đúp để chạy trên Windows | — |
| `HUONG_DAN.md`, `QUY_TAC.md` | Tài liệu cho người dùng cuối, tiếng Việt | Cập nhật khi thêm loại quy tắc mới |

> **`cauhinh.khoi12.goc.json` là bản đối chiếu, không phải bản chạy.** Nó là bản
> sao y nguyên của `cauhinh.json` tại thời điểm phần mềm mới chỉ xếp **một khối
> 12** trên một sheet, và phải giữ nguyên như vậy mãi mãi — chương trình không
> bao giờ đọc nó. Khi mở rộng sang khối 11 và khối 10, cấu trúc `cauhinh.json` sẽ
> đổi (nhiều khối, mỗi khối một khung giờ, bộ lọc `loc` thêm khoá `khoi`); lúc đó
> mở file này ra để đối chiếu xem khai báo cũ đã được chuyển sang dạng mới đúng
> chưa, và để dựng lại nhanh một ca thử "chỉ khối 12" khi cần khoanh vùng lỗi.
> Muốn quay lui hẳn về bản một khối thì `git checkout v1.0-khoi12`.

> **⚠ Repo từng có thư mục `files/` — đã xoá ở commit `461c40e`, ĐỪNG khôi phục.**
> Đó là bản tải về ban đầu, lẫn `files/xep_tkb.py` **cũ** (có từ trước khi tách
> `quy_tac.py`: không có `import quy_tac`, còn đọc mục `rang_buoc` kiểu cũ) với
> `files/quy_tac.py` **mới**, lại thiếu hẳn `mau_tkb.xlsx`, `tu_kiem_tra.py`,
> `chay.bat` — ghép lại không chạy được. Bản đúng chính là thư mục gốc này, giải
> ra từ `files/PhanMem_XepTKB.zip`.
>
> Nội dung cũ vẫn nằm nguyên trong commit `defbd59`, cần thì tra bằng
> `git show defbd59:files/xep_tkb.py`. Khôi phục nó về lại cây làm việc sẽ tạo
> hai bản `cauhinh.json` / `quy_tac.py` / `xep_tkb.py` trong cùng một repo —
> đúng cái bẫy sửa nhầm file mà lần dọn này giải quyết.
>
> Tag `v1.0-khoi12` lúc đầu trỏ vào `defbd59`, tức bản còn `files/`. Tag đã được
> **dời sang commit sau khi dọn**, nên `git checkout v1.0-khoi12` giờ cho cây làm
> việc sạch, không kéo `files/` về nữa.

---

## Mô hình dữ liệu

**`Cum`** = nhóm tiết liên tiếp của cùng 1 môn / 1 GV / 1 lớp.
Thuộc tính (`__slots__`): `ma lop mon nhom gv size la_cd la_trong ngay_ok
vitri_ok o_cam ngay vitri qt qt_gy`

- `ngay` đếm từ 0 (0 = thứ đầu trong `cac_thu`), `vitri` đếm từ 0 (0 = tiết đầu buổi).
- `ngay_ok` / `vitri_ok` = miền giá trị **còn lại**: khởi đầu **đầy** rồi bị các
  quy tắc cắt nhỏ dần (`&=`, `-=`); nằm trong tập = **được phép**.
- `o_cam` **ngược cực** với hai tập trên: là tập ô `(ngay, vitri)` **bị cấm**,
  khởi đầu **rỗng** rồi phình to dần (`|=`); nằm trong tập = **bị chặn**.
  Quen tay coi nó cũng là miền giá trị rồi viết `c.o_cam &= ...` là logic ngược
  hoàn toàn — quy tắc sẽ im lặng không chặn gì, hoặc chặn nhầm đúng những ô đáng
  lẽ được phép. Xem `KhongXepO` trong `quy_tac.py` làm mẫu.
- `qt` = quy tắc phải hỏi trong lúc giải; `qt_gy` = quy tắc có gợi ý thứ tự thử ô.
- **Ô trống** được mô hình hoá thành một `Cum` giả `la_trong=True`, size = số ô dư
  (`xep_tkb.py:209`). Khi luật `khong_tiet_trong_giua_buoi` bật (mặc định `True`),
  miền bị ghim `vitri_ok = {SO_TIET - size}` để dồn ô trống về cuối buổi
  (`xep_tkb.py:224`) → 24 tiết + 1 ô trống lấp kín đúng 25 ô, không có tiết trống
  chen giữa buổi. Đặt luật này `false` thì ô trống giữ nguyên miền đầy đủ và có
  thể rơi vào giữa buổi.
- `chia_cum(so_tiet, mau_cum)` cắt số tiết/tuần thành các cụm theo `dinh_muc_mon.cum`,
  có thể bị quy tắc `gom_tiet` ghi đè cho riêng một môn/lớp.

**`BaiToan`** dựng từ `cfg`: `_tao_cum()` → `_tao_quy_tac()` → `_kiem_tra_so_bo()`.
`_kiem_tra_so_bo()` dừng chương trình nếu có cụm bị chặn hết mọi ô.

`chuyen_doi_cau_hinh_cu(cfg)` nhận cả cấu hình **kiểu cũ** (`rang_buoc`, `uu_tien`)
lẫn **kiểu mới** (`quy_tac`), tự dịch sang kiểu mới và lọc bỏ `"bat": false`.

---

## Cơ chế quy tắc

Đăng ký bằng `@dang_ky('ten_loai')` vào `DANH_MUC`, kế thừa `QuyTac`. Các hook:

| Hook | Chạy lúc nào | Dùng để |
|---|---|---|
| `thu_hep_mien()` | 1 lần trước khi giải | Cắt bớt `ngay_ok` / `vitri_ok`, cộng dồn ô cấm vào `o_cam`. **Nhanh nhất, ưu tiên dùng.** |
| `lien_quan(c)` | 1 lần | Cụm nào cần gắn quy tắc này (mặc định = `khop(c)`) |
| `dat_lai()` | 1 lần trước MỖI lần thử (mỗi seed) | Xoá trạng thái riêng. Mặc định dựng lại quy tắc bằng `__init__`, hiếm khi cần ghi đè |
| `cho_phep(gs,c,ngay,v)` | mỗi nước đi | `False` = chặn |
| `dat(gs,c)` / `go(gs,c)` | mỗi nước đi | Cập nhật bộ đếm riêng |
| `thich(gs,c,ngay,v)` | mỗi nước đi | `True` = ô đẹp, thử trước |
| `hoan(gs,c)` | mỗi nước đi | `True` = hoãn cụm này lại |
| `hau_kiem()` | sau khi giải | Trả list chỗ vi phạm |
| `diem()` | sau khi giải | Điểm mềm |

Tiện ích có sẵn trong `QuyTac`: `loc()`, `khop(c, dk)`, `cac_cum(dk)`, `tap_ngay()`,
`tap_tiet()`, `ten_o(c)`, `_ben(c)` (trả `['a']`/`['b']` cho quy tắc so 2 nhóm),
`_ke(c, ngay, vitri, k)` (hai cụm có sát nhau không).

### Bốn quy ước SỐNG CÒN khi viết loại quy tắc mới

1. **Cờ lớp phải khai đúng.** `CAN_TRONG_KHI_GIAI = True` nếu có dùng
   `cho_phep`/`dat`/`go`; `CO_GOI_Y = True` nếu có dùng `thich`/`hoan`.
   Quên khai → hook không bao giờ được gọi (xem `BaiToan._tao_quy_tac`).
2. **Mọi bộ đếm riêng của quy tắc phải khởi tạo trong `__init__`.** Đối tượng
   quy tắc chỉ được tạo một lần rồi dùng lại cho mọi seed. Trước mỗi lần thử,
   `BoGiai._khoi_tao()` (`xep_tkb.py:283`) gọi `q.dat_lai()` cho **tất cả** quy
   tắc, không phân biệt cờ; `QuyTac.dat_lai()` mặc định dựng lại quy tắc bằng
   `self.__init__(self.r, self.bt)`. Bộ đếm đặt ở chỗ khác (biến của lớp, gán
   muộn trong `thu_hep_mien()`…) sẽ không được xoá → rác từ seed trước làm sai
   kết quả. Chỉ ghi đè `dat_lai()` khi việc dựng lại quá tốn kém, và khi đó phải
   tự xoá hết bộ đếm. `dat_lai()` chạy đúng 1 lần mỗi seed, không nằm trong vòng
   quay lui.
3. **Giá trị người dùng khai phải được kiểm miền, không được lặng lẽ bỏ qua.**
   `tap_tiet()` và `_kiem_o()` dừng chương trình bằng `SystemExit` kèm thông báo
   chỉ đích danh quy tắc, khoá, giá trị sai, miền hợp lệ và **đoán khoá người
   dùng định dùng**. `QuyTac.__init__` gọi sẵn hai hàm này khi quy tắc có khoá
   `thu`/`tiet`/`tiet_trong_buoi`/`o`, nên lỗi lộ ra ngay lúc dựng `BaiToan`,
   không đợi tới lúc chấm điểm. Loại quy tắc mới đọc thêm khoá số nào từ
   `cauhinh.json` thì cũng phải kiểm như vậy — bỏ qua âm thầm biến quy tắc sai
   thành quy tắc không cấm gì mà vẫn báo ĐẠT.

   Ba hàm kiểm dùng chung `_bao_loi()`: `_kiem_thu()` (khoá `thu`, cả dạng danh
   sách lẫn số lẻ của `co_dinh`), `_kiem_tiet()` (`tiet` / `tiet_trong_buoi`),
   `_kiem_o()` (khoá `o`, kiểm cả phần thứ lẫn phần tiết). `_ds()` cho phép ghi
   một giá trị lẻ thay cho danh sách.

4. **Tên loại quy tắc mềm phải bắt đầu bằng `uu_tien`.** `xep_tkb.py` phân biệt
   quy tắc cứng / tiêu chí mềm bằng đúng `q.TEN.startswith('uu_tien')`
   (ở `hau_kiem()` và ở `main()`). Đặt tên sai → quy tắc mềm bị đem đi hậu kiểm.

Ngoài ra: `gom_tiet` là **ngoại lệ**, không có hook nào — nó được đọc sớm ở
`BaiToan._map_gom_tiet()` trước khi cắt cụm, và bị `_tao_quy_tac()` bỏ qua.

### Bộ lọc: MỘT bản cài duy nhất

`quy_tac.khop_loc(dk, mon, nhom, gv, lop, la_cd)` là **nơi duy nhất** định nghĩa
"một tiết có thoả bộ lọc không". Hai chỗ gọi nó:

- `QuyTac.khop()` — mọi loại quy tắc, truyền thẳng từ đối tượng `Cum`.
- `BaiToan._cum_cua()` (`xep_tkb.py`) — `gom_tiet`, chạy trong `_tao_cum()` tức
  **trước khi có đối tượng `Cum` nào**. Đây chính là lý do `khop_loc()` nhận
  **tham số rời** chứ không nhận `Cum`.

Thêm khoá lọc mới thì chỉ sửa `khop_loc()`, hai chỗ tự động theo. Đây không phải
đưa quy tắc nghiệp vụ vào `xep_tkb.py` mà ngược lại — rút hẳn phần lọc ra khỏi đó.

> **Bài học vì sao phải gộp.** Trước đây `_cum_cua()` có bản cài riêng và
> **không hiểu `la_chuyen_de`**. Đo được: cùng bộ lọc `{"la_chuyen_de": true}`,
> `khop()` khớp đúng 24 cụm chuyên đề, còn `_cum_cua()` lại đụng **48 cặp
> (lớp, môn) thuộc 9 môn KHÔNG phải chuyên đề** — sai hoàn toàn, và im lặng.
> Cứ để hai bản cài song song thì kiểu lệch này còn tái diễn.

Kiểm khai báo cũng dùng chung, ở mức module trong `quy_tac.py`:
`bao_loi()` (khuôn thông báo), `kiem_bo_loc()` (khoá lạ, `tru` rỗng / sai kiểu).
`kiem_bo_loc()` chạy **1 lần lúc dựng** — `QuyTac.__init__` cho `loc`/`a`/`b`,
`_map_gom_tiet()` cho `gom_tiet` — nên vòng quay lui không phải trả giá kiểm tra.

Thêm loại mới thì nhớ đủ 5 việc: `MO_TA` + `VI_DU` (chép thẳng vào `cauhinh.json`
là chạy được) → thêm vào đúng nhóm trong `in_danh_muc()` → thêm ca thử vào
`tu_kiem_tra.py` → cập nhật `QUY_TAC.md`.

---

## Bộ giải

Quay lui + MRV. Khoá chọn biến: `(số lựa chọn, hoan(c), la_cd, -size)` — ít lựa
chọn nhất trước, cụm bị `hoan` để sau, chuyên đề để sau, cụm to trước.
Forward-checking (`lua_chon` trả rỗng → quay lui ngay), value-ordering theo số
quy tắc `thich()` ô đó.

Kiểm tra nền trong `dat_duoc()` (không phải quy tắc, luôn chạy): trùng ô của lớp,
trùng ô của giáo viên, `o_cam`, và luật `mot_cum_moi_mon_moi_ngay`.

`main()` chạy nhiều seed (`tim_kiem.so_lan_thu` — `cauhinh.json` đang đặt 400,
mặc định trong mã là 300, ghi đè bằng `--lan`), mỗi lần giới hạn theo
`gioi_han_buoc` (30000) và `gioi_han_giay_moi_lan` (3s), tổng
`gioi_han_tong_giay` (60s).

Ba nhánh kết thúc:
1. Có phương án **qua được hậu kiểm** → giữ cái điểm mềm cao nhất.
2. Có lời giải nhưng cái nào cũng trượt hậu kiểm → in `[CẢNH BÁO]` và lấy phương
   án **ít vi phạm nhất**, xếp hạng theo khoá `(số quy tắc lỗi tăng dần, điểm mềm
   giảm dần)` — điểm mềm chỉ là tiêu chí phụ khi số lỗi bằng nhau. In thẳng ra
   màn hình số quy tắc vi phạm, tên từng quy tắc kèm chi tiết `hau_kiem()` trả
   về, và dòng gợi ý nới quy tắc nào; vẫn xuất Excel.

Dòng tổng kết dùng **hai câu chữ khác nhau** cho hai nhánh, không được trộn:
nhánh 1 in `Điểm cao nhất: <d>.`, nhánh 2 in `Phương án ít vi phạm nhất: <n> quy
tắc lỗi, điểm mềm <d>.` — chữ "cao nhất" chỉ đúng khi việc chọn thật sự dựa trên
điểm mềm.
3. Không tìm được lời giải nào → in `[KHÔNG XẾP ĐƯỢC]` rồi `sys.exit(1)`,
   **không xuất Excel**.

---

## Xuất Excel

`xuat_excel()` copy `mau_tkb.xlsx` → file kết quả rồi **ghi đè nội dung**, nên giữ
nguyên 100% khung, font Times New Roman, viền, và công thức `=COUNTA(D8:D42)` ở
dòng 43. Vị trí bảng lấy từ `thong_tin.vi_tri_bang`
(`hang_bat_dau: 8`, `cot_bat_dau: 4`, `hang_tieu_de: 3`, `hang_tuan: 4`, `hang_gvcn: 7`).

- Ô của lớp thứ *j*, ngày *d*, tiết *p*: `cell(8 + d*5 + p, 4 + j)` → vùng **D8:I32**.
- Dòng 33–42 là hai khối Thứ 7 của mẫu (33–37 = Sáng, tiết 1–5; 38–42 = Chiều,
  tiết 6–10), hiện để trống vì `khung_gio` chỉ khai Thứ 2–6.
- Sheet kết quả: **Khối 12** (từ mẫu) + **TKB giáo viên** + **Kiểm tra quy tắc**
  (hai sheet sau do chương trình tạo mới, xoá và vẽ lại mỗi lần chạy).

### Bản in — đã kiểm 19/8/2026

Sheet "Khối 12" in **vừa đúng 1 trang A4 ngang**, đủ 6 cột lớp, dòng 43 (sáu ô
đều bằng 24) và khối ký tên. Page setup trong `mau_tkb.xlsx`: `landscape`, khổ
A4, `fitToPage=True`, `fitToWidth=1`, **`fitToHeight=1`**, lề
0.95/0.7/**0.35**/**0.35** inch. Kiểm bằng cách xuất PDF thật rồi đếm trang,
lặp lại được:

```bash
python -c "import openpyxl; wb=openpyxl.load_workbook('TKB_Khoi12.xlsx'); \
  [wb.__delitem__(t) for t in ('TKB giáo viên','Kiểm tra quy tắc')]; wb.save('/tmp/in.xlsx')"
soffice --headless --convert-to pdf --outdir /tmp /tmp/in.xlsx
pdfinfo /tmp/in.pdf | grep -E 'Pages|Page size'     # phải là: Pages 1, A4
pdftoppm -png -r 110 /tmp/in.pdf /tmp/trang         # xem tận mắt
```

Đo bằng `pdftotext -bbox`: chữ cuối cùng cách mép vùng in **0,07 inch** — trang
đã gần như kín.

> **⚠ Cạm bẫy mới, khó phát hiện hơn tràn trang.** Từ khi đặt `fitToHeight=1`,
> thêm dòng bên dưới khối ký tên **không còn tràn sang trang 2** nữa — Excel im
> lặng **thu nhỏ toàn bộ bảng** cho vừa một trang. Tràn trang thì mở file ra là
> thấy ngay và biết đường sửa; thu nhỏ dần thì không có dấu hiệu gì, đến lúc
> nhận ra thì chữ đã bé quá không đọc nổi. **Mỗi lần thêm dòng phải xuất PDF xem
> lại**, đừng đinh ninh là vẫn đọc được.

#### Bài học: ô bật `wrap_text` ở cột hẹp phải GỘP NGANG trước, tự giãn sau

Cột B chỉ rộng **7.29**, tức khoảng 7 ký tự. Ô nào ở cột B mà bật `wrap_text` thì
cho tự giãn chiều cao **không** cho ra "vừa đủ" mà cho ra một cột chữ dọc dài
ngoẵng: ô ghi chú `B45` từng giãn thành **11 dòng** và đẩy khối ký tên sang trang
2 — đã thử và đo, không phải suy đoán. Thứ tự đúng là **gộp ngang trước, bỏ ghim
`customHeight` sau**. Cùng nguyên tắc cho mọi cột hẹp khác (A rộng 6.29, C rộng
11.57).

| Dòng | Đã làm | Kết quả in ra |
|---|---|---|
| 6 — tên lớp + phòng học | bỏ ghim `customHeight` | đủ 3 dòng; cột D–I đã rộng 25.71 nên không cần gộp |
| 45 — ghi chú giờ vào lớp | **gộp `B45:I45`** rồi mới bỏ ghim | đủ 2 dòng, chạy ngang cả bảng |

> **Chỗ chưa kiểm được:** bản in ở đây kiểm bằng LibreOffice. Excel có một hạn
> chế đã biết — **không tự giãn chiều cao cho dòng mà nội dung nằm trong ô đã
> gộp**. Nếu mở trên Excel thấy dòng ghi chú cụt mất dòng thứ hai thì chữa bằng
> cách ghim lại dòng 45 ở khoảng `ht="26"` (đủ 2 dòng) — cách đó đúng trên cả
> Excel lẫn LibreOffice.

> **Sửa `mau_tkb.xlsx` thì đừng dùng openpyxl để ghi đè cả file** — nó ghi lại
> toàn bộ workbook. Cách đã dùng: mở như file zip, sửa đúng thuộc tính cần trong
> `xl/worksheets/sheet1.xml`, đóng lại, rồi đối chiếu mọi phần còn lại phải giống
> hệt từng byte.

---

## Ràng buộc nghiệp vụ đang khai trong `cauhinh.json`

**10 quy tắc cứng:** SHCN tiết cuối buổi **trừ lớp cô N.Uyên chủ nhiệm** ·
SHCN lớp cô N.Uyên xếp tiết 6 hoặc 7 · Vật lý 12B1,12B2 chỉ Thứ 2/3 ·
Sinh học 12B3,12B4 chỉ Thứ 2/3 · Sinh học 12B5,12B6 chỉ Thứ 2/3 ·
Hoá 12B1–12B4 không Thứ 3,5 · Văn cô Đ.Duy không Thứ 2 · Sử cô N.Uyên không
tiết 4,5 của buổi · Toán thầy M.Tuấn 12B2 khác ngày Toán thầy M.Hùng 12B4 ·
Sử cô N.Xuân khác ngày lịch thầy M.Hùng.

**3 tiêu chí mềm:** chuyên đề kề tiết chính (12đ) · dồn buổi cho GV (−4đ/buổi) ·
hai buổi cùng môn cách ≥ 2 ngày (3đ).

**2 luật nền** (`luat_chung`): `khong_tiet_trong_giua_buoi`, `mot_cum_moi_mon_moi_ngay`.

Cách gom tiết nằm ở `dinh_muc_mon.cum`: Toán/Văn `[2,1]`, HĐTN `[3]`,
Sử/Địa/Lý/Sinh/Hoá/GDKT-PL `[2]`, chuyên đề & SHCN `[1]`.

Mục `_quy_tac_de_san_chua_bat` chứa 7 quy tắc mẫu đang tắt — chép sang `quy_tac`
và bỏ `"bat": false` là dùng được.

---

## Giao diện web (`web.py` + `web/`)

`python web.py` → `http://127.0.0.1:20266`. Ctrl+C để tắt.
**Chỉ thư viện chuẩn** (`http.server`, `json`, `threading`), **chỉ bind 127.0.0.1**,
không tải gì từ mạng. `web.py` **chỉ gọi vào** `xep_tkb.py` / `quy_tac.py`, không
sửa gì trong đó.

| Đường | Việc |
|---|---|
| `GET /` · `GET /web/<tệp>` | Trang và tệp tĩnh — danh sách trắng `TINH`, đường dẫn lạ trả 404 |
| `POST /api/xep` | Bắt đầu một lượt; đang chạy thì trả **409** kèm "Đang xếp, vui lòng đợi." |
| `GET /api/trang-thai?tu=N` | Tiến độ + nhật ký **từ dòng N trở đi** (đừng gửi lại cả khung log mỗi lần hỏi) |
| `GET /api/quy-tac` · `POST /api/luu-quy-tac` | Đọc / ghi cờ bật-tắt |
| `GET /api/tai-ve` | Tải `TKB_Khoi12.xlsx` |

### Ba chỗ dễ sai, đã xử

1. **Không giải trong hàm xử lý HTTP.** Một lượt xếp mất ~50 giây; giải ngay trong
   handler thì trình duyệt treo, người dùng tưởng hỏng rồi bấm lại. Bộ giải chạy ở
   `threading.Thread`, trang hỏi `/api/trang-thai` mỗi 0,7 giây.
2. **`SystemExit` phải bắt trong luồng.** `kiem_bo_loc()`, `_bao_loi()`,
   `_kiem_tra_so_bo()`… đều `raise SystemExit` khi khai báo sai — đúng, vì với
   dòng lệnh thì dừng hẳn là phải. Nhưng trong web nó sẽ giết cả máy chủ. `_chay()`
   bắt `SystemExit` **và** `Exception`, in nguyên văn ra khung nhật ký, máy chủ
   sống tiếp. Đây là **đường đi chính** khi người dùng sửa quy tắc sai, không phải
   trường hợp hiếm.
3. **Việc tìm phương án dùng CHUNG một hàm.** `xep_tkb.tim_phuong_an(bt, tk,
   bao_tien_do=None)` là nơi duy nhất chứa vòng lặp thử-nhiều-seed. `main()` gọi
   với `bao_tien_do=None` (im lặng, đúng hành vi dòng lệnh cũ); `web._chay()`
   truyền một hàm gọi lại để cập nhật thanh tiến độ. **Đừng chép lại vòng lặp này
   ở bất kỳ đâu** — cả dự án chỉ còn một chỗ dựng `BoGiai`.

   `tk` truyền vào là **dict đã gộp sẵn** tuỳ chọn dòng lệnh với mục `tim_kiem`,
   đủ 5 khoá `so_lan_thu` / `seed` / `gioi_han_buoc` / `gioi_han_giay_moi_lan` /
   `gioi_han_tong_giay`. Trả về `KetQuaTim` (namedtuple):
   `tot diem so_ok so_hop_le da_thu du_phong diem_dp loi_dp giay`.

   `tests/thu_web.py` vẫn so **từng ô của vùng D8:I32** giữa hai đường chạy
   (150 ô, 0 lệch). Sau khi gộp, ca thử này canh đúng chỗ đáng canh: phần còn lại
   của `_chay()` — dựng cấu hình, tắt quy tắc tạm, xuất Excel — mới là chỗ có thể
   lệch khỏi dòng lệnh.

Công tắc bật/tắt ở màn hình "Quy tắc" mặc định **chỉ áp cho lượt chạy hiện tại**
(đặt `bat: false` trên bản `cfg` trong bộ nhớ). Nút "Lưu vào cauhinh.json" mới ghi
file, và luôn sao lưu `cauhinh.bak.json` trước.

> **Quyết định có chủ ý, đừng "sửa" lại:** nút Lưu ghi file bằng `json.dump` rồi
> gom các danh sách toàn số/chuỗi về một dòng (`_gon_json`). Cách này **giữ nguyên
> thứ tự khoá** nhưng **cách xuống dòng có thể xê dịch** so với bản viết tay.
> Đã cân nhắc phương án vá thẳng chuỗi văn bản để không đụng một ký tự nào, và
> **đã bác**: khoá `bat` có thể chưa tồn tại nên phải chèn mới, mỗi quy tắc lại
> viết một kiểu, vá chuỗi trên JSON viết tay là loại việc dễ làm hỏng file trong
> im lặng — đúng thứ mà cả dự án này đang tránh. Đổi lại, luôn có
> `cauhinh.bak.json` và ngay cạnh nút có ghi rõ cảnh báo. Người dùng đã duyệt.

Mục `_quy_tac_de_san_chua_bat` **không** hiện trên giao diện — muốn dùng quy tắc
mẫu nào thì vẫn phải chép tay sang mục `quy_tac` như cũ.

---

## Cách kiểm chứng một thay đổi

Ngoài hai lệnh bắt buộc, đây là hai kỹ thuật đã dùng khi sửa nhánh dự phòng của
`main()` — nhánh mà bộ quy tắc thật không bao giờ chạm tới. Lặp lại được cho mọi
thay đổi ở chỗ khó dựng tình huống.

### 1. Dựng cấu hình cho hai tiêu chí KÉO NGƯỢC NHAU

Một ca thử chỉ có giá trị khi tiêu chí cũ và tiêu chí mới **chỉ về hai phương án
khác nhau**. Nếu phương án tốt nhất theo cả hai cách xếp hạng trùng nhau thì ca
thử xanh cả trước lẫn sau khi sửa — vô nghĩa.

Cách làm trong `tests/thu_du_phong.py`: khai một tiêu chí mềm thưởng rất đậm
(`uu_tien_o`, 50đ) cho đúng cái mà các quy tắc thử coi là **lỗi** (Toán/Văn vào 2
tiết đầu buổi). Nhờ vậy phương án điểm mềm cao nhất chắc chắn cũng là phương án
nhiều lỗi nhất, và hai cách xếp hạng buộc phải cho kết quả khác nhau.

Ca thử **tự khẳng định điều kiện tiên quyết đó** trước khi kiểm cái cần kiểm
(`Phương án ít lỗi nhất có điểm mềm THẤP HƠN…`), nên nếu dữ liệu đổi khiến ca thử
mất khả năng phân biệt thì nó báo đỏ chứ không âm thầm xanh.

Hai mẹo phụ đi kèm:
- Ép nhánh cần thử **luôn** xảy ra bằng một quy tắc thử lúc nào cũng lỗi.
- Lớp quy tắc dùng-một-lần chỉ gán vào `QT.DANH_MUC` **trong tiến trình thử**,
  không đăng ký bằng `@dang_ky` trong `quy_tac.py`; ca thử có một mục tự kiểm tra
  rằng tên loại đó không hề tồn tại trong `quy_tac.py` thật.
- Khoá chặt `tim_kiem` (giới hạn giây đặt rất rộng) để chạy lại cho ra đúng dãy
  phương án cũ, rồi so kết quả của `main()` với dãy tự chạy lại được.

### 2. Lùi đúng dòng vừa sửa, xác nhận ca thử chuyển sang ĐỎ

Ca thử xanh chưa chứng minh được gì cả — phải chứng minh nó **biết đỏ**:

```bash
cp -r <dự án> /tmp/bancu            # chép sang thư mục tạm, đừng đụng bản thật
# sửa /tmp/bancu/xep_tkb.py, lùi ĐÚNG dòng vừa đổi về bản cũ
cd /tmp/bancu && python tests/thu_du_phong.py    # phải thoát mã 1
```

Kiểm cả **mục nào** đỏ, không chỉ nhìn mã thoát: đúng những mục nói về hành vi
vừa sửa phải đỏ, các mục không liên quan (nhất là mục không-hồi-quy) phải vẫn
xanh. Khi lùi lại logic cũ của nhánh dự phòng, kết quả đúng là 13/18 — 5 mục về
việc chọn phương án chuyển đỏ, CA 2 vẫn xanh nguyên.

---

## Trạng thái đã kiểm chứng (19/8/2026)

- `python xep_tkb.py`: 396 phương án hợp lệ / 400 lần thử trong ~50s, điểm cao nhất
  **−26**, **22/22 quy tắc ĐẠT**, xuất `TKB_Khoi12.xlsx`
  đủ 3 sheet, 144 ô chữ trong D8:I32, dòng 43 vẫn còn công thức COUNTA, font Times
  New Roman + viền `thin` nguyên vẹn.
- `python tu_kiem_tra.py`: 17 loại quy tắc đã đăng ký, ca CƠ SỞ + 11 ca thử đều
  **OK** (~105s), điểm từng ca −36 / −39 / −33 / −43 / −25 / −48 / −55 / −22 / 6 /
  −49 / −50 / 33. 11 loại được thử trực tiếp; 6 loại còn lại (`chi_xep_tiet`,
  `khong_xep_thu`, `khac_ngay`, và 3 loại `uu_tien_*`) được phủ qua ca CƠ SỞ vì
  đã có sẵn trong `cauhinh.json`.
- `python tests/thu_du_phong.py`: **20/20 mục ĐẠT** (~10s). Lùi riêng dòng xếp hạng
  dự phòng về bản cũ thì tụt còn 13/18 — ca thử có biết đỏ.
- `python tests/thu_kiem_khai_bao.py`: **42/42 mục ĐẠT** (~5s). Lùi phần kiểm miền
  khoá tiết về bản im lặng cũ thì tụt còn 10/21; lùi riêng phần khoá `thu` thì tụt
  còn 34/42 — ca thử có biết đỏ, và đỏ đúng chỗ.
- `python tests/thu_loc_tru.py`: **25/25 mục ĐẠT** (~3s). Lùi khoá `tru` khỏi cả hai
  chỗ lọc thì tụt còn 5/25.
- `python tests/thu_gop_bo_loc.py`: **23/23 mục ĐẠT** (~5s). Trả `_cum_cua()` về bản
  cài riêng thì tụt còn 16/23.
- `python tests/thu_web.py`: **47/47 mục ĐẠT** (~40s). Chạy trong thư mục tạm, không
  đụng `cauhinh.json` thật. Mục quan trọng nhất: 150 ô của vùng D8:I32 giống hệt
  nhau giữa dòng lệnh và web.
- 22 dòng hậu kiểm = 3 kiểm tra nền + 9 dòng gom tiết theo môn + 10 quy tắc cứng.
  **Đừng ghim con số này vào ca thử** — thêm một quy tắc vào `cauhinh.json` là vỡ.
  Khẳng định `Tổng: N/N quy tắc ĐẠT` (hai số bằng nhau) thay vì so với số cụ thể.

---

## Quy ước code

- Tên biến / hàm / lớp: **tiếng Việt không dấu** (`thu_hep_mien`, `cac_cum`, `dat_duoc`).
- Comment, docstring, thông báo ra màn hình, `ghi_chu`: **tiếng Việt có dấu**.
- Thông báo lỗi cho người dùng cuối theo mẫu `[LỖI] ...` kèm gợi ý sửa ở
  `cauhinh.json`, dừng bằng `raise SystemExit(...)`.
- Chỉ dùng thư viện chuẩn + `openpyxl`.

## Điều cấm

- Hardcode quy tắc nghiệp vụ vào `xep_tkb.py`.
- Đổi định dạng / bố cục Excel xuất ra (nhà trường in ra ký trực tiếp).
- Xoá hoặc đổi tên các hook của `QuyTac` (làm hỏng cả 17 loại quy tắc).
- Báo "xong" khi chưa chạy sạch cả `tu_kiem_tra.py` lẫn `xep_tkb.py`.
- Sửa `cauhinh.json` mà không sao lưu trước — đó là toàn bộ công sức khai báo dữ liệu.

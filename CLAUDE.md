# Dự án: Phần mềm xếp thời khóa biểu

Khoa Khoa học Cơ bản — Trường Cao đẳng Đà Lạt. Xếp TKB 6 lớp khối 12
(12B1–12B6), buổi chiều tiết 6–10, Thứ 2 → Thứ 6. Mỗi lớp 24 tiết/tuần trên
lưới 25 ô (5 ngày × 5 tiết), dư đúng 1 ô trống.

Người dùng cuối là giáo viên, **không biết lập trình**: họ chỉ mở
`cauhinh.json` bằng Notepad và bấm đúp `chay.bat`.

---

## Lệnh hay dùng

```bash
python3 xep_tkb.py                      # xếp và xuất TKB_Khoi12.xlsx
python3 xep_tkb.py --quy-tac            # in danh mục 17 loại quy tắc + mẫu JSON
python3 xep_tkb.py --in-man-hinh        # in luôn TKB ra màn hình
python3 xep_tkb.py --seed 99 --lan 800  # đổi seed / số lần thử
python3 xep_tkb.py --cauhinh khac.json  # dùng file cấu hình khác
python3 xep_tkb.py --xuat TKB_T3.xlsx   # đổi tên file kết quả
python3 xep_tkb.py --tuan "TUẦN 3 ..."  # đổi dòng chữ tuần, không sửa cauhinh.json
python3 xep_tkb.py --xuat-html          # xuất thêm trang web tĩnh tkb_web.html
python3 xep_tkb.py --tai-lap            # chế độ TÁI LẬP: cùng seed -> cùng kết quả
python3 tu_kiem_tra.py                  # BẮT BUỘC chạy sau mỗi lần sửa quy_tac.py
python3 tests/thu_du_phong.py           # thử nhánh dự phòng của main()
python3 tests/thu_kiem_khai_bao.py      # thử việc bắt lỗi khai sai thứ / tiết
python3 tests/thu_loc_tru.py            # thử khoá "tru" trong bộ lọc
python3 tests/thu_gop_bo_loc.py         # thử hai chỗ lọc dùng chung khop_loc()
python3 tests/thu_web.py                # thử giao diện web
python3 tests/thu_xuat_html.py          # thử trang web tĩnh
python3 tests/thu_truong.py             # thử khai báo TRUONG của các loại quy tắc
python3 tests/thu_them_quy_tac.py       # thử thêm/xoá/lưu quy tắc từ giao diện
python3 tests/thu_an_ninh.py            # BẮT BUỘC chạy sau mỗi lần sửa web.py
python3 tests/thu_lenh_chay.py          # ghim: mọi hướng dẫn gõ lệnh là python3
python3 tests/thu_chong_do.py           # BẮT BUỘC chạy sau mỗi lần sửa khoá tạm
python3 tests/thu_ghim_du_lieu.py       # ghim luật: ca thử không được ghim hằng số
python3 tests/thu_dau_ban.py            # 2C: dấu bản chống mất bản sửa
python3 tests/thu_doc_lai.py            # Đợt 3 việc 1+2: câu đọc lại, xem trước phạm vi
python3 tests/thu_o_tong.py             # BẮT BUỘC chạy sau mỗi lần sửa mau_tkb.xlsx
python3 tests/thu_kho_tuan.py           # kho TKB theo tuần + bộ đọc .xlsx

python3 luu_tuan.py xem <tệp.xlsx>       # đọc thử một tuần, KHÔNG ghi gì
python3 luu_tuan.py them <tệp.xlsx> --tuan 2026-08-24 --nguoi "..."
python3 luu_tuan.py liet-ke              # các tuần đang có trong kho
python3 luu_tuan.py danh-dau --tuan 2026-08-24 --ban 2 \
        --trang-thai sai --ly-do "..."   # bản này dùng được hay không
python3 luu_tuan.py de-dang  --tuan 2026-08-24   # bản nào ĐĂNG ĐƯỢC

python3 web.py                          # giao diện web -> http://127.0.0.1:20266
python3 web.py --port 8080              # đổi cổng; Ctrl+C để tắt
```

### Môi trường Python trên máy này (Linux)
Máy này **không có `pip`** và không có `python` (chỉ có `python3`), lại bị PEP 668
chặn cài gói vào hệ thống. Đã dựng sẵn một venv dùng chung:

```bash
~/.venvs/xeptkb/bin/python xep_tkb.py       # thay cho "python3 xep_tkb.py"
~/.venvs/xeptkb/bin/python tu_kiem_tra.py
```

> **Quy ước của cả tài liệu này:** mọi dòng lệnh đều viết `python3` — đó là dạng
> đúng cho một máy Linux có openpyxl, và là dạng ca thử `tests/thu_lenh_chay.py`
> ghim. **Trên máy này** thì thay `python3` bằng `~/.venvs/xeptkb/bin/python`,
> vì `python3` hệ thống thiếu openpyxl (đã đo: `python3 -c "import openpyxl"`
> báo `ModuleNotFoundError`). **Trên Windows** thì thay bằng `python`.

Dựng lại khi cần: `python3 -m venv ~/.venvs/xeptkb && ~/.venvs/xeptkb/bin/pip install openpyxl`
(đo 22/8/2026: Python 3.12.3 + openpyxl 3.1.5 — `~/.venvs/xeptkb/bin/python
-c "import sys,openpyxl;print(sys.version.split()[0],openpyxl.__version__)"`).

Trên máy Windows của nhà trường thì vẫn đúng như `HUONG_DAN.md`: cài Python,
chạy `pip install openpyxl`, rồi bấm đúp `chay.bat`.

---

## Phân vai file

| File | Chứa gì | Nguyên tắc |
|---|---|---|
| `cauhinh.json` | Dữ liệu (lớp, GV, số tiết) + toàn bộ danh sách quy tắc | Người dùng cuối sửa. Không phá cấu trúc. |
| `cauhinh_may_chu.json` | Danh sách `host_cho_phep` / `origin_cho_phep`. **Đã gitignore**, mỗi máy một khác | Thiếu thì mặc định chỉ 127.0.0.1. Sửa xong phải chạy lại `web.py` |
| `cauhinh.khoi12.goc.json` | **Bản gốc chỉ có khối 12**, đóng băng ở tag `v1.0-khoi12` | **KHÔNG được sửa.** Chỉ để đối chiếu |
| `quy_tac.py` | 17 loại quy tắc, registry `DANH_MUC` | **Mọi logic nghiệp vụ nằm ở đây** |
| `xep_tkb.py` | Mô hình dữ liệu, bộ giải, hậu kiểm, xuất Excel | **Không được hardcode quy tắc nghiệp vụ** |
| `mau_tkb.xlsx` | Mẫu Excel của trường (1 sheet "Khối 12") | Chương trình copy rồi ghi đè D8:I32 |
| `TKB_Khoi12.xlsx` | Kết quả (3 sheet) | File sinh ra, ghi đè mỗi lần chạy |
| `tu_kiem_tra.py` | Chạy thử từng loại quy tắc | Chạy sau mỗi thay đổi |
| `tests/thu_du_phong.py` | Ép nhánh dự phòng của `main()` xảy ra bằng một lớp quy tắc dùng-một-lần, chỉ đăng ký trong tiến trình thử | Chạy khi sửa `main()` |
| `tests/thu_kiem_khai_bao.py` | Bảng 4 tổ hợp `tiet` / `tiet_trong_buoi`, khoá `thu`, khoá `o` | Chạy khi sửa `tap_tiet()` / `tap_ngay()` |
| `tests/thu_loc_tru.py` | Khoá `tru` ở cả `khop()` lẫn `_cum_cua()` | Chạy khi sửa bộ lọc |
| `tests/thu_truong.py` | Mọi loại có `TRUONG`; khoá lạ cấp cao nhất thì DỪNG | Chạy khi thêm loại quy tắc |
| `tests/thu_them_quy_tac.py` | Thêm/xoá/lưu qua API; kích thước ô nhập trong CSS; CA 8 canh **nhân bản** + cửa chặn trùng câu `ghi_chu` | Chạy khi sửa form quy tắc |
| `tests/tien_ich_web.py` | `MayChuTam` (máy chủ thật) + `Khach` (socket trần, gửi được yêu cầu **dị dạng**: sai `Content-Type`, thiếu/nói dối `Content-Length`, `chunked`, và qua `tho_dong()` là **tiêu đề trùng tên**) | Hạ tầng dùng chung của mọi ca thử web |
| `tests/thu_an_ninh.py` | 10 bất biến an ninh: thân dị dạng · nguồn gốc · sao lưu · ghi nguyên tử · khoá một lượt · traceback · công thức Excel · trần thân · phễu tiêu đề · fsync | **Chạy khi sửa `web.py` hoặc chỗ ghi ô Excel** |
| `tests/thu_lenh_chay.py` | Ghim: không tệp nào (trừ `.bat`) còn dòng hướng dẫn gõ lệnh `python` trần. CA 0 khẳng định bộ dò biết bắt VÀ biết bỏ qua; CA 2 đọc câu lỗi thật qua tiến trình con và HTTP | Chạy khi thêm/sửa bất kỳ dòng hướng dẫn gõ lệnh nào |
| `tests/thu_doc_lai.py` | Đợt 3 việc 1+2: câu đọc lại **và** xem trước phạm vi. Canh CHẤT LƯỢNG — 17 câu **và** 17 chuỗi mẫu khác nhau đôi một, câu nhắc lại giá trị từ `VI_DU`, và không từ khoá nào thì câu **vẫn hiện**. CA 7 canh phần phạm vi: gõ sai tên phải chỉ **đích danh**, loại hai vế phải đếm **riêng từng vế**, và gõ dở thì **không được ném** | **Chạy khi thêm loại quy tắc, sửa `MAU_CAU`, hoặc sửa `pham_vi_quy_tac()`** |
| `ghi_ben.py` | **MỘT bản cài duy nhất** của việc ghi tệp cho bền: `ghi_nguyen_tu` · `chep_ben` · `dong_bo_tep` · `dong_bo_thu_muc`. Không biết gì về HTTP, cấu hình, hay Excel | Dùng chung cho `tai_khoan.py`, `web.py`, `kho_tuan.py` — **đừng chép bản thứ hai** |
| `doc_tkb.py` | Đọc một `.xlsx` của trường → một dict. `zipfile` + `xml.etree`, **chỉ đọc**. Không biết `luu_tru/` hay `cauhinh.json` tồn tại | Đợt 4 dùng lại y nguyên. Sửa cách đọc thì **bump `PHIEN_BAN`** |
| `kho_tuan.py` | Kho TKB theo tuần: `phieu.json`, thêm bản, đánh dấu, liệt kê. **KHÔNG biết Excel là gì** | Năm luật: không bao giờ đè · trùng SHA-256 thì từ chối · phiếu ghi nguyên tử · khoá tuần là NGÀY · **`ban_de_dang()` là cửa DUY NHẤT ra đường đăng** |
| `luu_tuan.py` | Dòng lệnh cho thầy cô: `xem` / `them` / `liet-ke` | `xem` không ghi một byte nào |
| `bang_ten_mon.json` | Chuỗi tên môn **thầy cô duyệt tay**. **CÓ COMMIT** | Là quyết định, không phải dữ liệu lưu trữ. Phần mềm **không bao giờ tự gộp** |
| `luu_tru/` | Kho tuần: tệp gốc + bản tách + phiếu. **Đã gitignore** | ⚠ git KHÔNG phải bản sao lưu — xem `CHAY_CUNG_MAY.md` mục 9 |
| `tests/thu_kho_tuan.py` | 6 ca: đọc đúng · tệp hỏng thật thì ĐỎ không VỠ · định nghĩa `loi` · không đè + từ chối trùng · dấu bộ đọc · phiếu hỏng thì dừng. **Tự dựng mọi tệp .xlsx của mình** | **Chạy khi sửa `doc_tkb.py` hoặc `kho_tuan.py`** |
| `tests/thu_o_tong.py` | Sáu ô "TỔNG SỐ TIẾT/TUẦN" (dòng 43) phải đếm **từ dòng đầu vùng dữ liệu**. Dòng đầu suy từ `vi_tri_bang`, dòng phải phủ suy từ `khung_gio` — **không ghim số trần**. CA 3 vá một cột về dòng sau trên **bản chép** rồi đòi bộ dò ĐỎ đúng một cột | **Chạy khi sửa `mau_tkb.xlsx` hoặc `xuat_excel()`** |
| `tests/thu_dau_ban.py` | 2C: dấu bản của `cauhinh.json` (QĐ 7) và của **kết quả xếp** (QĐ 4). Có mục bắn 12 người cùng lúc để canh phép kiểm dấu nằm TRONG khoá ghi | **Chạy khi sửa `luu_quy_tac` hoặc hai đường tải** |
| `tests/thu_ghim_du_lieu.py` | **Ghim LUẬT**: không ca thử nào được so bằng với hằng số lấy từ `cauhinh.json`. Đi trên **cây cú pháp**, từ vựng dựng từ chính tệp dữ liệu. **Tha SÀN KHÁC-RỖNG** (`> 0`, `> 1`, `>= 1` — chỉ toán tử thứ tự, chỉ số 0 và 1), vì CLAUDE.md bắt buộc phải khẳng định số đếm khác 0 trước khi dùng. Ngoại lệ khai bằng `ghim-co-y`, và số ngoại lệ bị chặn trên | **Chạy khi viết ca thử mới** |
| `tai_khoan.py` | Đọc/ghi `tai_khoan.json` + băm scrypt. **Không biết gì về HTTP** | Dùng chung cho `web.py` và `tao_mat_khau.py` — đừng chép bản thứ hai |
| `tao_mat_khau.py` · `tao_tai_khoan.bat` | Đặt/đổi/tắt/bật/xoá/liệt kê tài khoản, và **`mo-khoa`** gỡ khoá tạm. **Có commit** | Không có `--mat-khau`: mọi thứ gõ trên dòng lệnh đều vào lịch sử shell và `ps aux` |
| `tai_khoan.json` | Bản băm mật khẩu. **Đã gitignore** | Thiếu thì máy chủ TỪ CHỐI khởi động |
| `khoa_dang_nhap.json` | Sổ khoá tạm của 2B: bộ đếm lần gõ sai + mốc hết khoá. **Đã gitignore**, KHÔNG có bản `.mau` | Không ai tạo tay — `web.py` tự sinh. Thiếu hoặc hỏng thì coi như chưa ai bị khoá, và kêu to ra dòng lệnh |
| `*.json.mau` | Bản mẫu của hai tệp bị gitignore, **có commit** | Để cài lại máy còn biết cấu trúc |
| `tests/thu_dang_nhap.py` | Cổng đăng nhập: xoay mã phiên · câu chung · hai tài khoản · một lần scrypt mọi nhánh · bốn nhánh từ chối khởi động | Chạy khi sửa cổng đăng nhập |
| `tests/thu_chong_do.py` | 2B: khoá đúng ngưỡng · **nhánh khoá vẫn chạy đủ 1 lượt scrypt** · mọi loại tên đúng 1 lượt · vào đúng thì xoá bộ đếm · gõ thêm không kéo dài · hết giờ và cửa sổ quên · `mo-khoa` từ **tiến trình khác** · **loạt bắn dồn** · sổ bền và không chứa bí mật · sổ hỏng thì fail-open | **Chạy khi sửa khoá tạm** |
| `tests/thu_phien.py` | Hạ tầng phiên: nháp tách theo phiên · hai tên cookie · hết hạn · trần · **đồng hồ canh deadlock** | Chạy khi sửa `tao_phien`/`doc_phien`/cookie |
| `tests/thu_tai_lap.py` | Chế độ tái lập: cùng seed cho cùng kết quả (cả giữa hai tiến trình), và cấu hình VÔ NGHIỆM vẫn DỪNG | Chạy khi sửa `gop_tim_kiem()` hoặc `tim_phuong_an()` |
| `tests/thu_gop_bo_loc.py` | Hai chỗ lọc cho kết quả giống hệt nhau | Chạy khi sửa `khop_loc()` |
| `web.py` + `web/` | Giao diện web cục bộ (chỉ thư viện chuẩn) | Chỉ gọi vào `xep_tkb.py`, không sửa |
| `tests/thu_web.py` | Web: giống dòng lệnh, bắt `SystemExit`, khoá một-lượt | Chạy khi sửa `web.py` |
| `xuat_html.py` | Sinh `tkb_web.html` — một file tự chứa để chia sẻ | Không phụ thuộc openpyxl |
| `tests/thu_xuat_html.py` | Trang tĩnh: tự chứa, khớp 150 ô với Excel | Chạy khi sửa `xuat_html.py` |
| `DUA_LEN_MANG.md` | Hướng dẫn GitHub Pages cho người không rành kỹ thuật | Cập nhật khi đổi quy trình |
| `docs/` | `index.html` (bản sao `tkb_web.html`) + `.nojekyll` rỗng — thư mục GitHub Pages phục vụ | Do script ghi, đừng sửa tay |
| `xeptkb.service` · `CHAY_CUNG_MAY.md` | Dịch vụ systemd **phạm vi người dùng** (không cần sudo, đã có `Linger=yes`) + hướng dẫn cài/kiểm/gỡ. Mỗi dòng dễ sai đều kèm số đo | Cập nhật khi đổi cổng, đường dẫn, hay trình thông dịch |
| `dua_len.sh` · `dua_len.bat` | Xếp → xuất HTML → chép sang `docs/` → commit → push | Dừng và báo rõ nếu chưa nối kho từ xa |
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

### Năm quy ước SỐNG CÒN khi viết loại quy tắc mới

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

4. **Phải khai `TRUONG`** — danh sách các khoá cấp cao nhất loại đó nhận, mỗi
   khoá ghi `ten` / `kieu` (xem `QT.KIEU`) / `nhan` tiếng Việt / `bat_buoc`.
   Hai khoá thay thế nhau thì cho cùng `nhom` (vd `tiet` và `tiet_trong_buoi`).
   `TRUONG` phục vụ **cả** `--quy-tac` **lẫn** form nhập trên web, nên khai một
   chỗ là đủ; chép sang JS là chắc chắn lệch. Không khai thì mọi khoá riêng của
   loại đó đều bị coi là khoá lạ và chương trình DỪNG.

5. **Tên loại quy tắc mềm phải bắt đầu bằng `uu_tien`.** `xep_tkb.py` phân biệt
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

### Chế độ tái lập — `tim_kiem.che_do_tai_lap`

Bộ giải chặn bằng **đồng hồ treo tường**, nên hai lần chạy cùng seed vẫn cho số
phương án khác nhau (đã thấy 396 → 395 → 396). Con số lệch thì nhỏ, nhưng hệ quả
thì không: **mọi hồi quy thật đều có thể bị đổ cho "dao động bình thường"**.

Bật `che_do_tai_lap` (trong mục `tim_kiem` của `cauhinh.json`, hoặc cờ
`--tai-lap`) thì **bỏ HẲN** hai phép kiểm đồng hồ. Mặc định TẮT; chạy thật giữ
nguyên 60 giây.

> **Bỏ hẳn chứ không đặt số thật to.** `cau_hinh_tam()` của bộ thử vốn đã đặt
> `gioi_han_giay_moi_lan: 10, gioi_han_tong_giay: 3600` — tức đã cố ghim, nhưng
> ghim theo **xác suất**: máy bận thì nó vẫn nổ, ca thử chớp đỏ, và người sau lại
> đổ cho dao động. Bỏ hẳn phép kiểm làm điều đó **không thể** xảy ra.

**Cái gì bảo đảm bộ giải DỪNG khi không còn đồng hồ — hai BỘ ĐẾM:**

| Bộ đếm | Chỗ cài | Chặn cái gì |
|---|---|---|
| `gioi_han_buoc` (30000) | `_quay_lui()` tăng `self.buoc` ở đầu **mỗi** lần gọi rồi ném `TimeoutError` khi vượt | Một lượt. Mọi đường đệ quy đều đi qua đúng hàm đó |
| `so_lan_thu` | vòng `for` của `tim_phuong_an()` | Số lượt |

Chặn trên = `so_lan_thu × gioi_han_buoc` nút, hữu hạn, không phụ thuộc đồng hồ.

> **Ca thử phải bắt bộ giải VÉT THẬT, không chỉ "trả về nhanh".** Bản đầu tôi
> dồn hết mọi môn vào **một** thứ: đúng là vô nghiệm, nhưng bộ giải bí ngay ở nút
> đầu và trả về sau **0,0 giây** — chứng minh được đúng một điều vô nghĩa. Cấu
> hình dùng thật là dồn vào **hai** thứ: vẫn vô nghiệm (24 tiết không nhét vừa
> 10 ô) nhưng đủ rộng để quay lui bùng nổ — đo được (MÁY A) **đốt trọn 20.000 bước trong
> ~6 giây mỗi lượt**, và nhân ba bộ đếm thì thời gian nhân ba (5,9s → 17,6s).

`gop_tim_kiem()` là **nơi duy nhất** dựng dict `tim_kiem`. Trước đây ba chỗ chép
tay cùng một dict (`xep_tkb.main`, `web._chay`, `web.thu_quy_tac`) nên mỗi luật
mới phải nhớ sửa cả ba. Ngoại lệ có chủ ý: `web.thu_quy_tac()` ép
`che_do_tai_lap=False` kể cả khi cấu hình bật, vì nó giải **ngay trong luồng
HTTP** nên bắt buộc phải giữ chặn bằng đồng hồ.

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
dòng 43.

> **⚠ Vùng của sáu công thức dòng 43 phải bắt đầu từ dòng 8 — có ca thử canh.**
> Ngày 21/8/2026 nhà trường đưa ra một tệp TKB tuần 1 làm tay khai
> `D43=COUNTA(D10:D42)`, `E43=COUNTA(E11:E42)`, `F43=COUNTA(F10:F42)` trong khi
> dữ liệu bắt đầu ở dòng **8** — ba lớp đầu in ra thiếu 2–3 tiết (21/20/21 thay
> vì 23/23/23). Ô vẫn ra số, số vẫn trông hợp lý, **không một dấu hiệu nào báo**.
>
> **Đã đo: `mau_tkb.xlsx` của dự án KHÔNG dính lỗi đó** — cả sáu đều là
> `<cột>8:<cột>42`, và `TKB_Khoi12.xlsx` xuất ra đếm đúng 24 mỗi lớp. Tệp hỏng
> là tệp làm tay của trường, phần mềm không hề đụng tới. `tests/thu_o_tong.py`
> là hàng rào giữ nguyên trạng đang đúng, không phải bản vá cho một lỗi đã có.
>
> `thu_an_ninh.py` CA A8 **không** đủ: nó hỏi "bảy công thức còn hay mất", nên
> đổi `D8` thành `D10` thì nó vẫn xanh nguyên.

Vị trí bảng lấy từ `thong_tin.vi_tri_bang`
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
~/.venvs/xeptkb/bin/python -c "import openpyxl; wb=openpyxl.load_workbook('TKB_Khoi12.xlsx'); \
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

**Các quy tắc cứng** (đếm bằng lệnh ở mục "Số đếm"; **11** lúc 22/8/2026):
SHCN tiết cuối buổi **trừ lớp cô N.Uyên chủ nhiệm** ·
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

`python3 web.py` → `http://127.0.0.1:20266`. Ctrl+C để tắt.
**Chỉ thư viện chuẩn** (`http.server`, `json`, `threading`), **chỉ bind 127.0.0.1**,
không tải gì từ mạng. `web.py` **chỉ gọi vào** `xep_tkb.py` / `quy_tac.py`, không
sửa gì trong đó.

| Đường | Việc |
|---|---|
| `GET /` · `GET /web/<tệp>` | Trang và tệp tĩnh — danh sách trắng `TINH`, đường dẫn lạ trả 404 |
| `POST /api/xep` | Bắt đầu một lượt; đang chạy thì trả **409** kèm "Đang xếp, vui lòng đợi." |
| `GET /api/trang-thai?tu=N` | Tiến độ + nhật ký **từ dòng N trở đi** (đừng gửi lại cả khung log mỗi lần hỏi) |
| `GET /api/quy-tac` · `POST /api/luu-quy-tac` | Đọc danh sách / ghi xuống file. `/api/quy-tac` phát **dấu bản** và **phạm vi từng quy tắc**; `/api/luu-quy-tac` **ĐÒI** khoá `dau`, lệch thì **409** |
| `GET /api/loai-quy-tac` | Danh mục 17 loại: `MO_TA`, `TRUONG`, `VI_DU`, nhóm — sinh từ `QT.DANH_MUC` |
| `GET /api/gia-tri` | Lớp / GV / môn / nhóm môn / thứ / tiết — đọc từ `cauhinh.json` |
| `POST /api/them-quy-tac` · `POST /api/xoa-quy-tac` | Chỉ đổi cấu hình **của phiên**, không ghi file |
| `POST /api/thu-quy-tac` | Xếp thử rút gọn (30 lần thử / 8 giây) để xem còn xếp được không. Thêm `"nhanh": true` thì hạ xuống **1 lần thử / 1 giây** — dùng cho cảnh báo sớm sau khi Lưu |
| `GET /api/tai-ve` · `GET /api/tai-web` | Tải `TKB_Khoi12.xlsx` / `tkb_web.html`. Nhận `?dau=` — lệch với lượt xếp đang có trên đĩa thì **409** kèm tên người vừa xếp đè |

`PHIEN['them']` giữ các quy tắc người dùng thêm ở màn hình Quy tắc — **chỉ trong
bộ nhớ**. `cau_hinh_phien()` ghép `cauhinh.json` + `PHIEN['them']` và là **nguồn
duy nhất** cho `/api/quy-tac`, `/api/xep`, `/api/thu-quy-tac`, `/api/luu-quy-tac`.
Chỉ nút Lưu mới ghi file, ghi xong thì xoá `PHIEN['them']`. Chỉ số quy tắc là chỉ
số trong danh sách đã ghép; quy tắc từ file không xoá được (dùng công tắc để tắt).

`/api/thu-quy-tac` **giải ngay trong luồng HTTP** — ngoại lệ có chủ ý của quy tắc
"không giải trong handler", vì nó chặn cứng 30 lần thử / 8 giây (đo được ~2,3 giây trên MÁY A)
chứ không phải ~50 giây như lượt xếp thật. Nó cũng **không đụng vào `TT`** nên
không ghi đè kết quả đang hiện trên màn hình.

### Kích thước ô nhập — có ngưỡng, có ca thử

Mọi thứ bấm được (`input`, `select`, `textarea`, `button`, tab, ô vuông thứ/tiết,
nút Xoá, công tắc): **min-height ≥ 40px, font-size ≥ 15px**. Ô đánh dấu là ngoại lệ,
20×20px. Danh sách dài (28 giáo viên…) cao ≥ 200px, mỗi dòng ≥ 32px, có ô lọc và
dòng đếm. Danh sách ngắn cố định (thứ, tiết, lớp) dựng thành **dãy ô vuông bấm
bật/tắt** ≥ 56×40px chứ không phải `<select multiple>` — cái đó cao vài pixel mỗi
dòng, không bấm nổi.

> `tests/thu_them_quy_tac.py` CA 6 **đọc khai báo trong `style.css`**, không dựng
> trang thật để đo. Nó bắt được việc khai sai cỡ, **không** bắt được lỗi bố cục
> kiểu chữ tràn ra ngoài khung. Muốn chắc thì vẫn phải mở trình duyệt xem.

### Mười bất biến an ninh — ĐỪNG làm hồi quy

A1–A8 vá 19/8/2026 trước khi thêm đăng nhập; A9–A11 vá cùng ngày, ở **Đợt 1 của
Giai đoạn 2** — cũng trước khi thêm đăng nhập, và đó là điều kiện tiên quyết:
thêm cookie vào một máy chủ còn lỗ chèn đầu HTTP là làm an ninh **kém đi**, vì
cookie tự đính kèm nên mọi lỗ cũ đều mượn được quyền của người vừa đăng nhập.

Cả mười đều **hỏng ngay khi chạy cục bộ**, không phải rủi ro lý thuyết chờ tới
lúc mở Internet. Mỗi mục có ca thử riêng trong `tests/thu_an_ninh.py`; con số
trong ngoặc là kết quả khi lùi lại bản cũ.

| # | Bất biến | Chỗ cài |
|---|---|---|
| A2 | Thân yêu cầu **dị dạng ≠ thân rỗng**. `Transfer-Encoding`, thiếu/sai `Content-Length` → 400. Ba đường GHI dùng `_than_json(bat_buoc=True)` | `web.py` `_than_json()` (2/10) |
| A1 | Chỉ nhận yêu cầu từ **nguồn đã khai**: `Host` + `Origin` + `Content-Type: application/json`. `Host`/`Origin`/`Content-Length` mỗi thứ chỉ được **một dòng**, `Content-Length` phải khớp `[0-9]{1,15}`, và danh sách tên máy đọc từ `cauhinh_may_chu.json` — **fail-closed** | `web.py` `_kiem_nguon_goc()`, `_mot_dong_duy_nhat()`, `nap_cau_hinh_may_chu()` (17/33 · 166/172 · 197/202) |
| A7 | `cauhinh.bak.goc.json` giữ bản **đầu tiên**, không bao giờ đè; thêm 5 bản xoay vòng | `web.py` `_xoay_sao_luu()` (41/49) |
| — | Ghi `cauhinh.json` **nguyên tử**: dựng chuỗi → tệp tạm → đọc lại → sao lưu → `os.replace()`. Cả hàm trong `KHOA_GHI` | `web.py` `luu_quy_tac()` |
| A4 | Kiểm cờ + xoá trạng thái + đặt cờ trong **CÙNG một lần giữ khoá** | `web.py` `gianh_luot()` (11 lượt chồng nhau) |
| A3 | Dấu vết lỗi ra **cửa sổ dòng lệnh**, người dùng chỉ thấy mã 6 ký tự. `SystemExit` vẫn hiện **nguyên văn** | `web.py` `_bao_su_co()` (70/78) |
| A8 | Mọi chỗ ghi ô Excel đi qua `_dat_o()` — chuỗi đầu `=` bị ép `data_type='s'` | `xep_tkb.py` `_dat_o()` (9 thẻ `<f>` thay vì 7) |
| A9 | Thân yêu cầu có **trần cứng** `TRAN_THAN` = 256 KB. Chặn theo `Content-Length` **trước** khi đọc, chặn lại theo mẩu 64 KB **khi** đọc → 413 | `web.py` `_than_json()` + `_doc_than_co_tran()` (156/165) |
| A10 | **Mọi** tiêu đề đi qua `_tra_byte()` — kiểm xong hết rồi mới `send_response()` | `web.py` `_tra_byte()` (151/165) |
| A11 | Ghi tệp **bền**: `fsync` tệp tạm → sao lưu (cũng `fsync`) → `os.replace` → `fsync` thư mục cha | `web.py` `luu_quy_tac()`, `_chep_ben()`, `_dong_bo_thu_muc()` (159/165) |

### Danh sách tên máy: `cauhinh_may_chu.json`

Từ khi đặt sau Tailscale Serve, trình duyệt gửi `Host: admin.tail7dc28e.ts.net`
và `Origin: https://admin.tail7dc28e.ts.net`, nên phép kiểm ghim cứng
`127.0.0.1:20266` từ chối sạch. Danh sách nay đọc từ tệp — **tệp RIÊNG, không
phải `cauhinh.json`**: `cauhinh.json` là tệp thầy cô mở bằng Notepad để sửa dữ
liệu nhà trường và có thể đem đi chỗ khác, còn tên máy trong mạng riêng thì mỗi
máy một khác và không việc gì phải đi theo tệp dữ liệu. Tệp nằm **cạnh `web.py`,
KHÔNG đi theo `--cauhinh`** — nếu không thì `--cauhinh khac.json` sẽ âm thầm đổi
luôn cả danh sách máy được phép gọi vào. Đã `.gitignore`.

**Máy chủ vẫn chỉ `bind('127.0.0.1', 20266)`.** Không có `--host`, không
`0.0.0.0`. Đường vào từ ngoài là do proxy chuyển tiếp, không phải do đổi chỗ nghe.

| Tình huống | Xử lý |
|---|---|
| Không có tệp | Mặc định loopback, **im lặng** — đây là cài đặt thường |
| Tệp hỏng / sai kiểu / có ký tự điều khiển | Mặc định loopback, **kêu to** ra cửa sổ dòng lệnh |
| Cả hai danh sách rỗng | Mặc định loopback, kêu to |
| Hợp lệ | Danh sách đó **THAY THẾ** mặc định, và in ra màn hình |

#### Cổng gác NHỮNG đường nào — đã đo, không suy luận

`_kiem_nguon_goc()` được gọi ở **dòng đầu tiên** của cả `do_GET` lẫn `do_POST`,
**trước** mọi phép so đường dẫn. Nên nó gác **tất cả**, đọc lẫn ghi. Đo bằng cách
bắn `Host: evil.com` vào từng đường qua HTTP thật:

| Nhóm | Đường | `Host` lạ | `Origin` trang lạ |
|---|---|---|---|
| Tĩnh | `/` · `/index.html` · `/web/app.js` · `/web/style.css` | 400 | — |
| Đọc | `/api/trang-thai` · `/api/quy-tac` · `/api/loai-quy-tac` · `/api/gia-tri` · `/api/tai-ve` · `/api/tai-web` | 400 | — |
| **Ghi** | `/api/xep` · `/api/luu-quy-tac` · `/api/them-quy-tac` · `/api/xoa-quy-tac` · `/api/thu-quy-tac` | **400** | **400** |

**0 đường lọt**, và `cauhinh.json` không bị đụng tới. (Mẫu số là TỔNG SỐ ĐƯỜNG
lúc đo — hồi đó 15, nay 19; đếm bằng lệnh ở mục "Số đếm". Điều đáng nhớ là
số 0 ở vế sau, không phải mẫu số ở vế trước.)
Chiều ngược lại cũng đo: `Host` + `Origin` đúng thì cổng không chặn oan đường nào.
Ca thử `ca_a1c_moi_duong_deu_bi_gac` **bóc danh sách đường thẳng từ `web.py`** rồi
so với tập đã biết, nên thêm đường mới là nó ĐỎ trước — buộc người thêm phải ngó
lại xem đã gác chưa.

> **Vì sao KHÔNG bắt buộc phải có dòng `Origin` ở đường ghi — cố ý, không phải
> bỏ sót.** Kiểm `Origin` chỉ chặn được **trình duyệt bị một trang lạ sai
> khiến**, vì trình duyệt không cho trang web nói dối `Origin`. Một chương trình
> gọi thẳng (`curl`, script) tự đặt `Origin` nào cũng được, nên bắt buộc phải có
> `Origin` **không thêm được một chút an toàn nào** trước nó — chỉ thêm rủi ro từ
> chối oan một khách hợp lệ. Khi có dòng `Origin` thì nó vẫn bị kiểm chặt (đo
> được: cả năm đường GHI CẤU HÌNH — `/api/xep`, `/api/luu-quy-tac`,
> `/api/them-quy-tac`, `/api/xoa-quy-tac`, `/api/thu-quy-tac` — đều trả 400
> với `Origin` trang lạ. Gọi tên thay vì đếm: thêm một đường mới thì danh
> sách này thiếu hẳn một cái tên, nhìn là thấy, chứ không âm thầm lệch một số).
>
> Hàng rào đối với khách gọi thẳng là **đăng nhập**, không phải `Origin`. Điều
> này quan trọng hơn từ khi có Tailscale: trước kia "khách gọi thẳng" nghĩa là
> người đã ngồi trước máy; nay là **mọi thiết bị trong tailnet**. Trong lúc chưa
> có cổng đăng nhập (Đợt 2), ranh giới thật đang là chính tailnet — ai vào được
> tailnet thì ghi được `cauhinh.json`. Biết mà chấp nhận, không phải không biết.

> **Thay thế, không cộng thêm.** Có tệp rồi thì `localhost:20266`, `[::1]:20266`
> đều bị chặn. Đặt máy chủ sau proxy có TLS mà vẫn để chúng lọt là giữ lại đúng
> những cửa mình tưởng đã đóng. Ai cần thì viết vào tệp — một chỗ, nhìn là thấy.

> **Host và Origin là HAI bảng riêng, khai hai lần.** Đừng ghép
> `'https://' + host` cho đỡ phải khai: làm vậy là tự tay nhận cả `http://` lẫn
> `https://` cho cùng một tên, tức mở lại đúng cái mà việc đặt sau TLS định đóng.
> Ca thử có mục riêng: đúng tên máy mà sai giao thức vẫn phải 400.

> **Quyết định về `:443` — KHÔNG tự nhận, và đây là lý do.** Trình duyệt **bỏ**
> `:443` khi gửi `Host` cho HTTPS, nên chuỗi cần khai là
> `admin.tail7dc28e.ts.net` không kèm cổng. Máy chủ **không** tự chấp nhận thêm
> dạng `admin.tail7dc28e.ts.net:443`. Tự suy ra một biến thể mà người quản trị
> không hề viết chính là bước đầu của lối "chuẩn hoá cho dễ khớp" đã đẻ ra mọi
> dòng bẫy trong bảng ca thử. Ai thật sự cần dạng có cổng thì thêm đúng chuỗi đó
> vào danh sách — nó là một dãy, thêm bao nhiêu cũng được. Đổi lại, phép so khớp
> chỉ có đúng một luật: **so cả chuỗi, chỉ bỏ qua hoa/thường**.

> **Chuẩn hoá CHỈ hạ chữ thường — cố ý bỏ `.strip()`.** Đã đo: bộ phân tích tiêu
> đề của thư viện chuẩn tự bỏ khoảng trắng **đầu** nhưng **giữ nguyên** khoảng
> trắng cuối (`'Host: 127.0.0.1:20266   '` → `'127.0.0.1:20266   '`). Cắt hộ cho
> dễ khớp là nới lỏng phép so. Bảng ca thử A1 có một dòng đã **đổi từ 200 sang
> 400** vì việc này — đổi có chủ ý, không phải hồi quy.

> **Chỗ đề bài đòi chặn mà KHÔNG chặn được, đã kiểm:** gửi
> `Host: <tên hợp lệ>\r\nX-Gia: 1` thì `\r\n` **không** nằm lại trong giá trị
> `Host`. Đo bằng `email.parser`: nó tách thành **hai dòng tiêu đề**, và `Host`
> còn lại là chuỗi hợp lệ → máy chủ cho qua, và như vậy là **đúng**. Chặn ở đây
> cũng vô nghĩa: khách chèn thêm tiêu đề vào yêu cầu của chính nó thì chẳng được
> gì. Dạng thật sự mang `\r\n` vào giá trị là **obs-fold** (dòng nối tiếp bắt
> đầu bằng khoảng trắng) — dạng đó bị chặn, có ca thử riêng. Mối nguy còn lại là
> chiều ngược lại, ta phát `\r\n` ra **phản hồi**, và đó là A10.

> **Thêm chỗ phát tiêu đề HTTP mới thì PHẢI đi qua `_tra_byte(mã, [(tên, giá
> trị)…], thân)`, đừng gọi thẳng `send_header()`.** Lý do không phải chỉ là gọn:
> `send_header()` của thư viện chuẩn chỉ gọi được **sau** `send_response()`, nên
> một hàm bọc kiểm-tại-chỗ vẫn để lại dòng trạng thái trong bộ đệm rồi ném — và
> ta được đúng cái phản hồi **hai dòng trạng thái**. Đo được trên bản cũ: đặt
> `file_xuat = 'TKB_Khối12.xlsx'` (tên có dấu, chuyện rất dễ xảy ra) thì máy chủ
> trả **200** với `server`/`date`/`content-type` mỗi thứ **hai lần**, và trình
> duyệt tải về một tệp `.xlsx` thật ra chứa câu báo lỗi JSON. Không một chữ giải
> thích. Vì vậy `_tra_byte()` nhận **cả danh sách** tiêu đề và kiểm xong hết rồi
> mới phát dòng trạng thái đầu tiên.
>
> Tên tệp thì qua `_ten_tep_an_toan()`: ký tự điều khiển và `"` → **DỪNG** (400,
> chỉ đích danh `thong_tin.file_xuat`); chữ có dấu tiếng Việt → **giữ**, phát
> kèm `filename*=UTF-8''…` theo RFC 6266. Khác `_dat_o()` ở đúng chỗ này: Excel
> còn một cách lưu khác giữ nguyên được từng ký tự, HTTP thì không.
>
> **Thêm chỗ ghi ô Excel mới thì PHẢI dùng `_dat_o(ws, hàng, cột, giá_trị)`,
> đừng gọi thẳng `ws.cell(...)`.** Kiểm kê các chỗ ghi bằng
> `grep -c "_dat_o(" xep_tkb.py` (**22** lúc 22/8/2026 — trước đây tài liệu ghi
> tay là 25). Trong đó có những giá trị rơi vào
> **đầu ô**, trong đó 2 đường sửa được qua HTTP: `thong_tin.tuan` (→ `Khối 12!A4`)
> và `ghi_chu` của quy tắc **MỀM** (`cham_diem` dùng nó làm khoá dict → ghi thẳng
> vào ô, **không có tiền tố**; quy tắc CỨNG thì vô hại vì có `[tên_loại] ` đứng
> trước). Bảy công thức của `mau_tkb.xlsx` (D43:I43, H48) không đi qua `_dat_o`
> nên còn nguyên — ca thử khẳng định cả hai chiều.

> **Ca thử web KHÔNG được gọi tắt vào hàm Python.** `tests/thu_web.py` CA 6 tự
> canh điều đó. Gọi thẳng `web._chay()` / `web.luu_quy_tac()` là bỏ qua đúng tầng
> sắp đặt cổng đăng nhập — ca thử sẽ xanh giả dù cổng đó hỏng hoàn toàn.

> **Hai bài học khi viết ca thử đua tranh** (mất công mới rút ra được):
> 1. **Đếm số phản hồi 200 không đo được chồng lấn.** Bộ giải giữ GIL nên luồng
>    HTTP đói hẳn: đo được (MÁY A) người thứ 8 mãi 1,06 giây mới được phục vụ, sau khi
>    lượt trước đã xong ở 0,78 giây — nhận 200 là ĐÚNG. Phải đo **thẳng số luồng
>    `_chay` cùng sống**.
> 2. **Khe hở hẹp thì ca thử xanh cả trên mã hỏng.** Nới bằng cách thêm 50ms vào
>    `_than_json()` — điểm **nằm trong** vùng chưa khoá của bản cũ và **nằm ngoài**
>    ở bản mới. Nới khe hở có sẵn, không tạo lỗi mới.

### Ổ NTFS, Windows song song, và phép tự kiểm GHI ĐƯỢC

Máy này **có Windows cài song song** — đo bằng `efibootmgr`:
`Boot0000* Windows Boot Manager`, cộng đủ bộ phân vùng Windows trên **`nvme1n1`**
(EFI System · Microsoft reserved · Microsoft basic data · Windows recovery).
Thư mục dự án nằm trên một phân vùng **NTFS ở Ổ KHÁC**: **`nvme0n1p2`**, nhãn
`NAM MEO`, 657,3 GB — đo lại 22/8/2026.

> **⚠ Tài liệu này từng ghi NGƯỢC HAI Ổ** — nói Windows ở `nvme0n1` và dự án ở
> `nvme1n1p2`, trong khi thật ra ngược hẳn lại. Sửa 22/8/2026. Không ca thử nào
> đỏ vì chuyện này, và cũng không thể có: đó là số đo về phần cứng, không phải
> về mã. Cách duy nhất là đo lại:
> ```bash
> findmnt --target .    # -> /dev/nvme0n1p2  ntfs3
> lsblk -o NAME,SIZE,FSTYPE,LABEL,MOUNTPOINT | grep -iE 'nvme|NAM'
> ```
> Đừng chép hai tên này đi đâu nữa — chúng đổi khi cắm thêm ổ hoặc đổi máy.

> **Lỗi im lặng nhất của cả phần mềm.** Windows tắt kiểu **"khởi động nhanh"**
> (fast startup) là ngủ đông chứ không tắt hẳn, nên phân vùng còn ở trạng thái
> **BẨN**; Linux thấy vậy gắn **CHỈ ĐỌC** để khỏi làm hỏng dữ liệu. Hậu quả:
> phần mềm chạy bình thường, xếp bình thường 50 giây, tới lúc bấm Lưu mới hỏng
> — mà nguyên nhân thật là **một cái tắt máy sai cách hôm trước, trên hệ điều
> hành khác**, và không có gì trong phần mềm chỉ ra điều đó.

`web.main()` gọi `kiem_ghi_duoc()` **trước khi bind cổng** và trước cả dòng
"Mở trình duyệt vào": ghi thật một tệp tạm rồi xoá. Không ghi được thì **DỪNG**
kèm câu chỉ đúng cách chữa (vào Windows tắt "khởi động nhanh", rồi *Shut down*
hẳn — đừng *Restart*, đừng đóng nắp máy).

> **Không dùng `os.access(W_OK)`.** Nó chỉ hỏi bit quyền, mà tình huống đang lo
> là hệ tệp gắn CHỈ ĐỌC — lúc đó bit quyền vẫn nói "được ghi". Phải ghi thật.

`tests/thu_web.py` CA 7 dựng thư mục `chmod 500` rồi chạy `web.py` bằng **tiến
trình con**. Hai chỗ đã phải sửa vì kỷ luật:
- chạy bằng root thì `chmod` không chặn được → ca thử **tự khai mất khả năng
  phân biệt** thay vì âm thầm xanh;
- lùi bản vá ra thì máy chủ khởi động được và `serve_forever()` chạy mãi →
  `subprocess.run` ném `TimeoutExpired`. Bản đầu **VỠ** đúng kiểu hỏng số 2;
  nay bắt lấy và biến thành một mục **ĐỎ**.

### Đường vào từ ngoài — ĐO LẠI 21/8, đã tách hai cổng

| Cổng | Phạm vi | Phục vụ |
|---|---|---|
| `:443` | **Funnel — cả Internet** | chỉ `/nbv` (trang công khai Nguyên Bản Việt) |
| `:8443` | **chỉ tailnet** | `/` → `127.0.0.1:20266`, tức trang quản trị TKB |

> **Funnel bật theo cặp TÊN-MÁY:CỔNG, KHÔNG theo đường dẫn.** Trước 21/8 cả hai
> đường cùng nằm ở `:443`, nên bật Funnel cho trang công khai `/nbv` đã **kéo
> theo `/`** — trang quản trị TKB phơi ra Internet mà không ai cố ý làm vậy.
> Câu "ranh giới thật đang là chính tailnet" ở mục A1 khi đó **sai**; ranh giới
> thật là mật khẩu, đối diện Internet.
>
> Đo lại bằng `tailscale serve status --json`, xem khoá `AllowFunnel` — đừng
> đọc dòng chữ tóm tắt, nó không nói rõ đường nào thuộc cổng nào.
> Đo được 21/8: `AllowFunnel: {"admin.tail7dc28e.ts.net:443": true}` và cổng
> 443 chỉ còn `/nbv`. TKB **không còn** trên Internet.

Đổi cổng thì phải thêm tên máy mới vào **cả hai** danh sách của
`cauhinh_may_chu.json`; hiện có `admin.tail7dc28e.ts.net:8443` ở cả hai.

#### Cả hai đầu TỰ SỐNG LẠI sau khi bật máy — ĐÃ ĐO 21/8/2026

Khởi động lại máy thật. Sau khi máy bật, **không gõ lệnh nào trước khi thử**:

```
uptime -s        -> 2026-08-21 18:35:23
Active since     -> 2026-08-21 18:35:34   (sau 11 giây)
Main PID         -> 1271
Loaded           -> enabled; preset: enabled
```

Rồi từ điện thoại, **tắt Wi-Fi, chạy 4G**:
`https://admin.tail7dc28e.ts.net:8443/` → đăng nhập → **Xếp** → **Lưu**.
Chạy suốt, **không 502**.

| # | Kết luận | Số đo nào nói điều đó |
|---|---|---|
| **5d** | `xeptkb.service` khởi sinh **lúc máy đang dựng**, trước khi có ai đăng nhập màn hình | `Main PID 1271`, và `Active since` chỉ sau `uptime -s` **11 giây** |
| **5e** | `tailscale serve --https=8443` **TỰ SỐNG LẠI** sau khởi động | Điện thoại 4G vào được `:8443` mà **chưa ai gõ lệnh `tailscale serve` nào** sau khi máy lên |

**5e trước giờ chưa ai đo — giờ đã đo. Đợt 2 ĐÓNG.** Chi tiết và công thức lặp
lại được ở `CHAY_CUNG_MAY.md` mục 7.

> **Ghi SỐ ĐO, đừng ghi KẾT LUẬN SUÔNG.** Câu "dịch vụ tự chạy được" mà không
> kèm bốn dòng số trên thì sáu tháng nữa không ai nhớ nó dựa trên gì, và sẽ
> phải khởi động lại máy để đo lại từ đầu.

> **KHÔNG dựng thêm unit systemd cho `tailscale serve`.** Số đo nói nó tự sống
> lại; thêm mã khi số đo nói không cần là thêm một chỗ để hỏng.

### Ổ dữ liệu đã có sẵn trong `/etc/fstab` — đừng thêm lần nữa

Đo được, không suy: `systemctl show 'media-adminnam-NAM\x20MEO.mount'` cho
`SourcePath=/etc/fstab`, `Loaded: loaded (/etc/fstab; generated)`. Dòng có sẵn
từ **6/8/2026**, đã đủ `nofail`, `x-systemd.device-timeout=30`, `uid=1000`,
`gid=1000`, `acl`:

```
UUID=8018451718450D9A /media/adminnam/NAM\040MEO ntfs3 rw,nosuid,nodev,relatime,uid=1000,gid=1000,acl,iocharset=utf8,prealloc,nofail,x-systemd.device-timeout=30 0 0
```

> **BẪY DẤU CÁCH đã bắt đúng người viết ra nó.** `grep "NAM MEO" /etc/fstab`
> cho **0 dòng** (đo lại 22/8/2026: vẫn 0), vì fstab ghi dấu cách thành `\040`. Kết luận "ổ do udisks tự
> gắn" sinh ra từ đúng cú grep hụt đó.
>
> **BÀI HỌC RỘNG HƠN CẢ DẤU CÁCH: một lệnh không ra kết quả KHÔNG có nghĩa là
> thứ đó không tồn tại — có thể lệnh sai.** Từ một phép tìm âm tính, cả một
> tiền đề ("ổ do udisks gắn → dịch vụ hệ thống không thấy ổ lúc khởi động")
> được dựng lên và sống qua nhiều lượt trao đổi. Xác nhận bằng một phép đo
> KHÁC KIỂU (`systemctl show`, `findmnt`, `stat`), đừng suy từ một cú grep.

### Dấu cách trong "NAM MEO" — NĂM ngữ cảnh, năm cách viết

Đã **đo từng cái**, không suy từ tài liệu. Viết nhầm cách là hỏng, và bốn trong
năm kiểu hỏng đều **im lặng**:

| Nơi | Viết đúng | Viết sai thì sao |
|---|---|---|
| `/etc/fstab` | `NAM\040MEO` | — |
| Tên **unit** systemd | `media-adminnam-NAM\x20MEO.mount` | — |
| `RequiresMountsFor=` (danh sách) | `"/media/adminnam/NAM MEO"` **có ngoặc** | `\x20` → đọc ra `NAMx20MEO`, chờ đường dẫn không tồn tại = **không chờ gì**. Dấu cách trần → cắt còn `/media/adminnam/NAM` |
| `WorkingDirectory=` (một giá trị) | `/media/adminnam/NAM MEO/...` **dấu cách trần** | Bọc ngoặc → `Unit configuration has fatal error` |
| Dòng lệnh shell | `"NAM MEO"` | — |

> **Hai khoá systemd cạnh nhau, hai luật NGƯỢC nhau.** `RequiresMountsFor` là
> danh sách ngăn bằng dấu cách nên **phải** bọc ngoặc; `WorkingDirectory` là
> một giá trị nên bọc ngoặc là **hỏng hẳn**. Không có cách viết nào đúng cho cả
> hai — đừng đi tìm.
>
> Còn một chỗ thứ sáu: `Documentation=file:///...NAM%20MEO/...` cũng hỏng, vì
> systemd đọc `%` là ký hiệu thay thế của nó (`Failed to resolve unit
> specifiers`). Muốn giữ URL thì phải `%%20`.

### 2C — dấu bản chống mất bản sửa (QĐ 7 + QĐ 4)

**Hai tầng, hai lỗ khác nhau, đừng gộp.**

| | Lỗ | Ai canh |
|---|---|---|
| QĐ 7 | A mở màn hình Quy tắc · B sửa và Lưu · A Lưu theo danh sách CŨ → mất sạch bản của B | dấu bản của `cauhinh.json` |
| QĐ 4 | B bấm Xếp đè hai tệp kết quả · A bấm Tải về và nhận tệp của B mà không biết | dấu bản của **kết quả xếp** |

Dấu bản của QĐ 7 **không** bắt được lỗ QĐ 4 — lúc đó `cauhinh.json` không hề
đổi. **DÁN TÊN để BIẾT, DẤU BẢN để CHẶN — cần cả hai.**

> **Dấu bản của `cauhinh.json` là BĂM NỘI DUNG TỆP, không phải mã ngẫu nhiên.**
> Thầy cô được quyền mở tệp bằng Notepad và sửa tay — đó là đường dùng CHÍNH,
> ghi ngay ở đầu tài liệu này. Một mã ngẫu nhiên giữ trong bộ nhớ sẽ **không hề
> biết** lần sửa tay đó, nên hai người vẫn đè mất bài của nhau y như cũ, mà lần
> này còn kèm một cái dấu bản trông có vẻ an toàn. Băm nội dung thì bắt được
> mọi kiểu đổi: qua giao diện, sửa tay, khôi phục từ bản sao lưu, khởi động lại.
> Có mục ca thử sửa tệp bằng `json.dump` rồi đòi dấu phải đổi.

> **Kiểm dấu nằm TRONG `KHOA_GHI` — lỗi A4 lần thứ hai.** Kiểm ở ngoài rồi mới
> vào khoá thì hai người cùng bấm Lưu sẽ **cùng** thấy dấu khớp, rồi lần lượt
> ghi đè nhau. Đo được (MÁY A): đẩy phép kiểm ra ngoài khoá thì **8 trong 12** yêu cầu
> song song ghi được, thay vì đúng 1.

> **409 chứ không 400.** Hai mã nói hai chuyện: 400 = *"bạn gửi sai"*,
> 409 = *"bạn gửi đúng nhưng thế giới vừa đổi"*. Giao diện chỉ hiện nút
> **"Tải lại danh sách"** cho đúng mã 409. Thiếu hẳn khoá `dau` thì là 400 —
> đó là yêu cầu sai, không phải xung đột.

**Ngoại lệ có chủ ý của QĐ 4:** máy chủ vừa khởi động lại thì `TT['dau']` là
`None` mà tệp kết quả hôm qua vẫn nằm trên đĩa → **cho tải**. Từ chối lúc đó là
từ chối oan; người dùng không làm gì sai, chỉ là máy vừa bật lại.

**Ca thử tự tiêm `dau` ở tầng khách** (`Khach.yeu_cau`), không sửa hai chục chỗ
gọi — gần hết những chỗ đó viết ra để thử thứ KHÁC (nguồn gốc, thân dị dạng,
sao lưu, fsync), bắt chúng tự lo dấu bản là làm chúng thử nhầm thứ. Cùng lẽ với
`MayChuTam` tự đăng nhập. Muốn thử chính cái xung đột thì truyền `dau=` tay,
hoặc `dau=False` để **không gửi** khoá đó.

> **2C bắt được một lỗi của 2B.** Ca thử bắn 12 người đăng nhập **đúng** cùng
> lúc (chỉ để có 12 phiên) làm lộ ra: bộ đếm khoá tạm đếm **LẦN THỬ** chứ không
> đếm **LẦN SAI**, nên người thứ (ngưỡng+1) đăng nhập **đúng** cùng lúc ăn 429.
> Đã tách hai kiểu chặn: **khoá THẬT** (đã có lần sai xác nhận — chặn cả mật
> khẩu đúng) và **chốt chặn** loạt bắn dồn (**chỉ** chặn mật khẩu sai). Cho mật
> khẩu đúng đi qua chốt chặn không mất gì — kẻ đoán trúng thì đã thắng rồi.
> Ghim lại ở `thu_chong_do.py` CA 11b.

### Cảnh báo sớm sau khi Lưu — CẢNH BÁO, không CHẶN

Thầy cô bấm Lưu năm lần, thêm bốn quy tắc, và `cauhinh.json` thành **vô nghiệm**
mà giao diện không nói một tiếng. Vì sao lọt: `them_quy_tac()` **có** dựng
`X.BaiToan(cfg)`, nhưng phép kiểm đó (`_kiem_tra_so_bo`) chỉ bắt được *"có cụm
nào hết sạch ô hợp lệ không"* — kiểm **TĨNH**. Cấu hình hỏng thật lại vô nghiệm
kiểu **TỔ HỢP**: mỗi cụm đều còn ô, chỉ là không xếp chung được. Đo: `BaiToan()`
trên bản hỏng dựng xong trong **1 ms, không kêu một tiếng** (MÁY A). Còn `luu_quy_tac()`
thì không dựng `BaiToan` gì cả.

**Không có phép kiểm rẻ tiền nào bắt được lỗi này — muốn biết thì phải xếp thử.**

Đo trên **MÁY A**:

| | Cấu hình TỐT | Cấu hình VÔ NGHIỆM |
|---|---|---|
| 1 lần thử / 1 giây | **0,1 s** | 1,1 s |
| 3 lần thử / 1 giây | 0,2 s | 3,3 s |
| 3 lần thử / 3 giây | 0,2 s | 9,3 s |

Chọn **1 lần thử / 1 giây**: câu hỏi lúc đó là *"còn xếp được không"*, không
phải *"xếp tối ưu chưa"*. Chiều đánh đổi thuận — lúc mọi thứ ổn thì gần như
không tốn gì, chỉ chậm đúng lúc có chuyện.

> **CẢNH BÁO chứ không CHẶN — người dùng đã chốt, đừng tự đổi.** Nút Lưu là
> thao tác làm hằng ngày; bắt nó đợi 1–9 giây thì thầy cô tưởng máy treo rồi
> bấm lại, sinh ra đúng cái tranh chấp hai lượt vừa bịt. Và **chặn oan** (cấu
> hình khó nhưng vẫn có nghiệm — bộ giải quay lui có xác suất) còn tệ hơn: bị
> từ chối mà không hiểu vì sao, không có cách tự gỡ. Tệp hỏng nằm trên đĩa là
> chấp nhận được vì đã có `cauhinh.bak.json` **và** git.

> **KHÔNG BAO GIỜ nói "vô nghiệm" khi `vet_can = false`.** Một giây không đủ để
> chứng minh điều đó. Ba câu, ba mức chắc chắn khác nhau:
> `co_loi_giai` → *"vẫn xếp được"* · `vet_can` → *"CHẮC CHẮN không xếp được"* ·
> còn lại → *"ĐÁNG NGỜ … nhưng một giây thì chưa đủ để khẳng định là vô
> nghiệm"*. Nói quá dù chỉ một lần là thầy cô thôi tin mọi cảnh báo sau.
> `thu_them_quy_tac.py` CA 7 thử **cả ba** nhánh qua HTTP thật; lùi cờ
> `het_gio` ra là mục về nhánh thứ ba đỏ ngay.

Khung cảnh báo nói rõ **quy tắc nào vừa lưu** (nghi phạm đầu tiên) và có nút
**tắt đúng những quy tắc đó rồi thử lại**. Nút nằm SẴN trong `index.html`, không
dựng bằng `innerHTML`: mọi id JS gọi tới đều phải có trong HTML —
`tests/thu_web.py` canh đúng bất biến đó và đã bắt được bản đầu.

### Ba chỗ dễ sai, đã xử

1. **Không giải trong hàm xử lý HTTP.** Một lượt xếp mất ~50 giây (MÁY A); giải ngay trong
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
   `tot diem so_ok so_hop_le da_thu du_phong diem_dp loi_dp giay vet_can`.

   **`vet_can`** = đã có ít nhất một lượt **vét cạn** không gian mà không tìm
   được gì, tức **chắc chắn** vô nghiệm. `BoGiai.giai()` trả `None` cho **cả
   hai** lý do — `_quay_lui` trả `False` (vét cạn) và `TimeoutError` (đụng trần)
   — nên trước đây không ai phân biệt nổi, và bất cứ ai muốn báo "cấu hình này
   vô nghiệm" đều buộc phải **nói quá**. `self.het_gio` phân biệt hai đường đó.
   Với 90 cụm thì vét cạn gần như **không bao giờ** xảy ra trong ngân sách
   thật, nên `vet_can=False` **KHÔNG** có nghĩa là "có nghiệm".

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

## Trang web tĩnh (`xuat_html.py`)

`xuat_html(bt, pa, duong_dan)` — nhận đúng `bt` và `pa` như `xuat_excel()`, sinh
**một file `.html` duy nhất**, tự chứa: HTML + CSS + JS + dữ liệu nhúng dạng JSON.
Không CDN, không font ngoài, không `fetch`, không `localStorage`. Mở bằng `file://`
(bấm đúp từ USB) chạy đủ chức năng; đưa lên GitHub Pages cũng chạy y hệt.

- Dữ liệu nằm ở `<script id="du-lieu" type="application/json">`, JS nằm giữa hai
  mốc `/*JS-BAT-DAU*/` … `/*JS-KET-THUC*/` — **hai mốc này để ca thử bóc ra kiểm**,
  đừng xoá. Chuỗi `</` trong JSON được đổi thành `<\/` để không cắt ngang thẻ
  `<script>`.
- Ô ghi dạng mảng phẳng `[lop, ngay, vitri, mon, gv]` cho nhẹ file.
- Ba chế độ xem chọn bằng nút, lựa chọn ghi vào địa chỉ trang (`#lop=12B3`,
  `#gv=N.Uyên`, `#khoi`) nên **chia sẻ được đúng màn hình đang xem** và tải lại
  không mất. Không dùng `localStorage` — người xem có thể mở bằng `file://`.
- Ưu tiên điện thoại: font hệ thống, `viewport`, `@media (max-width: 560px)`, bảng
  "cả khối" cuộn ngang trong khung `overflow-x: auto` với cột đầu `position: sticky`.

`xep_tkb.py` **chỉ thêm lời gọi** (`--xuat-html`, nạp muộn `import xuat_html`),
không thêm logic nghiệp vụ. `web.py` sinh sẵn `tkb_web.html` sau mỗi lượt xếp
thành công; nút **Xuất trang web** chỉ tải file đó về qua `GET /api/tai-web`.

> **Riêng tư — đã chốt 19/8/2026, đừng tự đổi:** trang công khai **GIỮ NGUYÊN họ
> tên đầy đủ của GVCN** ở đầu mỗi cột lớp (khoá `gvcn`). Lý do: trang này là bản
> điện tử của đúng tờ TKB đang treo ở trường, mà tờ đó vốn đã ghi họ tên đầy đủ
> GVCN — đổi sang tên viết tắt sẽ làm bản trên mạng khác bản in, gây khó cho phụ
> huynh khi cần biết ai chủ nhiệm lớp con mình. Người dùng đã cân nhắc và quyết
> định như vậy.
>
> Kèm theo quyết định đó: `DUA_LEN_MANG.md` mở đầu bằng bảng liệt kê **chính xác**
> những gì công khai (tên lớp · **họ tên đầy đủ GVCN** · tên viết tắt GV bộ môn ·
> môn · thứ và tiết · tuần), nói rõ **không có** số điện thoại/email/địa chỉ/ngày
> sinh/ảnh/tên học sinh, và nhắc **hỏi ý nhà trường trước khi bật Pages**.
>
> Khoá `gvcn_vt` trong `cauhinh.json` vẫn chưa chỗ nào dùng — nếu sau này nhà
> trường đổi ý thì đó là chỗ để đổi sang, trong `xuat_html.du_lieu()`.

### Đưa lên GitHub Pages

> **✅ Nhà trường đã ĐỒNG Ý công khai trang TKB — 19/8/2026.** Điều kiện tiên
> quyết ghi ở đầu `DUA_LEN_MANG.md` ("Hãy hỏi ý nhà trường trước khi bật GitHub
> Pages") đã được đáp ứng, nên PHẦN A được phép làm. Phạm vi công khai vẫn đúng
> bảng đã chốt: tên lớp · **họ tên đầy đủ GVCN** · tên viết tắt GV bộ môn · môn ·
> thứ và tiết · tuần — và **không có** số điện thoại/email/địa chỉ/ngày sinh/ảnh/
> tên học sinh. Muốn công khai thêm gì ngoài bảng đó thì phải hỏi lại nhà trường.

`docs/index.html` là bản sao của `tkb_web.html`; `docs/.nojekyll` rỗng để Pages
đừng xử lý lại tệp. Đã kiểm `.gitignore` **không** loại nhầm hai tệp này
(`tkb_web.html` ở thư mục gốc thì bị loại, đúng ý — nó là tệp sinh ra), và có ghi
chú ngay trong `.gitignore` nhắc đừng thêm dòng loại `docs/`.

**Tên thư mục phải là `docs`, đừng đổi.** GitHub Pages chỉ nhận đúng hai chỗ:
gốc kho, hoặc thư mục tên `docs`. Đặt tên khác thì hoặc phải để trang ở gốc kho
(lẫn với mã nguồn), hoặc link phải mang đuôi thư mục.

> **⚠ Trên máy Linux này phải chỉ rõ Python cho `dua_len.sh`:**
> ```bash
> PYTHON=~/.venvs/xeptkb/bin/python ./dua_len.sh
> ```
> Script mặc định gọi `python3`, mà `python3` hệ thống **không có openpyxl** →
> chạy trần `./dua_len.sh` sẽ chết ở bước xếp. Trên máy Windows của trường thì
> bấm đúp `dua_len.bat` như thường, không cần gì thêm.

`dua_len.sh` / `dua_len.bat` kiểm đủ điều kiện **trước** khi xếp, để không mất 50
giây rồi mới báo thiếu: có `git` chưa → có phải kho git chưa → có remote `origin`
chưa. Thiếu cái nào cũng dừng kèm hướng dẫn trỏ về `DUA_LEN_MANG.md`.

> **✅ ĐÃ LÊN MẠNG THẬT — 19/8/2026.** Kho: `bjnnghe0/pm-xep-TKB` (Public).
> Trang đang sống tại **https://bjnnghe0.github.io/pm-xep-TKB/** — đã kiểm
> HTTP 200 và so từng byte với `docs/index.html` (md5 trùng khít).
>
> **⚠ Link PHÂN BIỆT CHỮ HOA/THƯỜNG — đã đo, không phải suy đoán.** Chỉ
> `pm-xep-TKB` cho 200; `pm-xep-tkb` và `PM-XEP-TKB` đều trả **404**. Vì vậy
> **đừng đọc link cho người khác gõ tay** — hãy gửi link bấm được (Zalo, email)
> hoặc mã QR. Thiếu dấu `/` cuối thì GitHub tự chuyển hướng 301, không sao;
> vào bằng `http://` cũng tự chuyển sang `https://`.
>
> Email tác giả trong **cả 28 commit** đã đổi sang `281376871+bjnnghe0@
> users.noreply.github.com` — Gmail thật không lộ. Kho đã đẩy rồi, nên **đừng
> đặt lại `user.email` về Gmail**; sửa sau phải viết lại lịch sử và ép ghi đè.

> Link Pages là `https://<tk>.github.io/<kho>/` — ngắn gọn, không đuôi thư mục,
> nhờ dùng đúng tên `docs`. Trong Settings → Pages phải chọn nhánh **main** +
> thư mục **/docs**. Script tự in đúng link này, và chỉ đoán link khi remote
> thật sự ở `github.com`.

Đã thử toàn bộ script bằng một kho bare cục bộ trong thư mục tạm — **không tạo kho
GitHub, không push ra ngoài**.

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
cd /tmp/bancu && python3 tests/thu_du_phong.py    # phải thoát mã 1
```

Kiểm cả **mục nào** đỏ, không chỉ nhìn mã thoát: đúng những mục nói về hành vi
vừa sửa phải đỏ, các mục không liên quan (nhất là mục không-hồi-quy) phải vẫn
xanh. Khi lùi lại logic cũ của nhánh dự phòng, kết quả đúng là 13/18 — 5 mục về
việc chọn phương án chuyển đỏ, CA 2 vẫn xanh nguyên.

---

## Số đếm — ĐỪNG CHÉP, HÃY ĐẾM

> **Luật, 22/8/2026:** *số nào một lệnh đếm được thì **XOÁ SỐ**, thay bằng chính
> lệnh đó; số nào không đếm được thì **giữ, kèm ngày đo**.*
>
> Vì sao thành luật: đợt kiểm kê 21/8 tìm được **82 con số không kèm ngày**,
> trong đó **11 con đã sai** mà không ca thử nào đỏ. Cập nhật 82 số chỉ mua
> được vài tháng — sáu tháng nữa lại sai 82 số khác. Cái sửa được gốc là đừng
> chép số vào văn xuôi nữa.
>
> Con số chép tay tệ nhất là con **lặp lại nhiều chỗ**: `17 loại` từng nằm ở
> **13 chỗ**, `28 giáo viên` ở 4 chỗ, `150 ô` ở 4 chỗ, `~50 giây` ở 4 chỗ.

| Muốn biết | Gõ |
|---|---|
| Số **loại quy tắc** đã đăng ký | `python3 -c "import quy_tac as Q; print(len(Q.DANH_MUC))"` |
| Số **kiểu trường** (`QT.KIEU`) | `python3 -c "import quy_tac as Q; print(len(Q.KIEU))"` |
| Số **quy tắc** trong tệp / đang bật | `python3 -c "import json; q=json.load(open('cauhinh.json'))['quy_tac']; print(len(q), len([r for r in q if r.get('bat',True)]))"` |
| Số quy tắc **cứng** đang bật | `python3 -c "import json; q=json.load(open('cauhinh.json'))['quy_tac']; print(len([r for r in q if r.get('bat',True) and not r['loai'].startswith('uu_tien')]))"` |
| Số **giáo viên** | `python3 -c "import json; p=json.load(open('cauhinh.json'))['phan_cong']; print(len({m[1] for k,d in p.items() if not k.startswith('_') for m in d}))"` |
| Số **ô** của cả khối (lớp × ngày × tiết) | `python3 -c "import json; c=json.load(open('cauhinh.json')); k=c['khung_gio']; print(len(c['lop'])*len(k['cac_thu'])*len(k['cac_tiet']))"` |
| Số **tiết/tuần** mỗi lớp | `python3 -c "import json; p=json.load(open('cauhinh.json'))['phan_cong']; print({k: sum(x for m in d for x in m if isinstance(x,int)) for k,d in p.items() if not k.startswith('_')})"` |
| Số **cụm** | `python3 -c "import xep_tkb as X; print(len(X.BaiToan(X.doc_cau_hinh('cauhinh.json')).cac_cum))"` |
| Số **đường dẫn** máy chủ | `python3 -c "import re,io; print(len(set(re.findall(r'/api/[a-z-]+', io.open('web.py',encoding='utf-8').read()))) + 5)"` — 14 API + 5 tĩnh |
| Số **ca** trong một bộ thử | `grep -cE '^def ca_' tests/<tên>.py` |
| Số **công thức** trong mẫu Excel | `unzip -p mau_tkb.xlsx xl/worksheets/sheet1.xml \| grep -o '<f>' \| wc -l` |
| Số **dòng hậu kiểm** | đọc dòng `Tổng: N/N quy tắc ĐẠT` của `python3 xep_tkb.py` |

> **Số KHÔNG đếm được bằng một lệnh** — thời gian chạy, kết quả lùi-bản-vá, số
> đo đua tranh, kết quả mô phỏng — thì **giữ, và phải kèm ngày đo VÀ TÊN MÁY**.
> Chúng là ảnh chụp một lần đo trên MỘT máy, không phải thuộc tính của mã.

### Trạng thái của một bản — và CỬA DUY NHẤT ra đường đăng

Một tuần có thể có **nhiều bản mâu thuẫn nhau**. Đã xảy ra thật: tuần
`2026-08-24` có hai bản, và Khoa xác nhận **22/8/2026** bản 21/8 là **SAI** —
nó bỏ 6 tiết chuyên đề Sử, đẩy N.Xuân từ 9 tiết xuống 0 và dựng K.Ly từ 0 lên
6. `cauhinh.json` khớp bản 18/8, nên **`cauhinh.json` đúng, không sửa gì**.

| `trang_thai` | Nghĩa | Ra được đường đăng? |
|---|---|---|
| `dung` | đã xác nhận dùng được | **CÓ** |
| `sai` | đã biết là sai | không |
| `chua_ro` | **mặc định** — chưa ai xét | **không** |

`ly_do` **bắt buộc** khi nói `dung` hoặc `sai`: một bản bị đánh dấu mà không
nói vì sao thì sáu tháng nữa không ai dám tin cái dấu đó, và sẽ có người gỡ nó.

> **`kho_tuan.ban_de_dang()` là cửa DUY NHẤT.** Mọi đường đăng phải đi qua nó.
> Đọc thẳng `phieu['ban']` rồi tự lọc là dựng **bản cài thứ hai**, và bản thứ
> hai sẽ lệch — đúng bài học `khop_loc()` / `_cum_cua()`.

> **`chua_ro` cũng bị chặn — fail-closed, và đây là chỗ dễ cãi nhất.** Mặc định
> của một bản mới chính là `chua_ro`, nên nếu cho nó qua thì cửa này **không
> chặn gì cả trong trường hợp thường gặp nhất**. Cái giá là phải đánh dấu tay
> một lần mỗi tuần — rẻ hơn nhiều so với đăng nhầm một bản sai, vì trang công
> khai thì cả trường đọc, và git thì **nhớ vĩnh viễn**.
>
> Bản ghi cũ **thiếu hẳn khoá** `trang_thai` cũng đọc ra `chua_ro`, không phải
> `dung`: phiếu ghi từ trước khi có trường này thì đúng là chưa ai xét.

> **KHÔNG XOÁ BẢN SAI.** Nó là bằng chứng, và là ca thử thật duy nhất đang có.

---

### MÁY A — mọi số hiệu năng trong tài liệu này đo trên đây

```
MÁY A   admin · Intel Core i5-12400F · 12 nhân · 62 GB RAM
        Python 3.12.3 + openpyxl 3.1.5 (~/.venvs/xeptkb)
        thư mục dự án: /dev/nvme0n1p2, ntfs3
        (kiểm kê 22/8/2026)
```

> **Số hiệu năng không kèm máy là số vô nghĩa — máy khác là số khác.** Mọi con
> số thời gian / bộ nhớ trong tài liệu này ngầm hiểu là **MÁY A**.

**Đo lại 22/8/2026 trên MÁY A — năm số cũ vẫn đúng trong sai số:**

| Số | Tài liệu ghi | Đo lại 22/8 |
|---|---|---|
| `TK.bam()` một lượt scrypt | 27 ms | **29,6 ms** |
| đọc tệp + dựng `BaiToan` + tính phạm vi mọi quy tắc | 2,67 ms | **2,45 ms** |
| `os.stat` trên ntfs3 | 0,78 µs | **0,84 µs** |
| dựng `BaiToan` | 1 ms | **1,2 ms** |
| `cau_doc_lai` cho mọi quy tắc | 20 lượt / 0,01 giây | **0,11 ms** |

**Số hiệu năng CHƯA đo lại** — vẫn của MÁY A, nhưng **ngày đo không còn ghi
lại** (chúng ra đời rải rác 19–21/8/2026): `~50 giây` một lượt xếp · bảng
`0,1 s … 9,3 s` của cảnh báo sớm · `537 MB` cho 32 lượt scrypt · `1,06 / 0,78
giây` của ca thử đua tranh · `8 trong 12` yêu cầu song song · `~2,3 giây` của
`/api/thu-quy-tac` · `5,9s → 17,6s` của chế độ tái lập · bảng mô phỏng ngưỡng
khoá. **Giữ vì mỗi số đang chống lưng cho một quyết định**, ghi ngay tại chỗ.

> **Hai số đã XOÁ 22/8/2026 vì không quyết định nào dựa vào chúng:**
> `240 giây` (thời gian `thu_phien.py` treo khi lùi bản vá — đồng hồ canh lấy
> số **180**, không phải 240) và `~14 KB` (cỡ `tkb_web.html` — không có số đối
> chứng nào để so, và lựa chọn "mảng phẳng" đã tự biện minh bằng chữ "cho nhẹ
> file"; đo lại 22/8 là **15 KB**, tức nó cũng đã trôi rồi).

---

## Trạng thái đã kiểm chứng (19/8/2026)

- `python3 xep_tkb.py`: 396 phương án hợp lệ / 400 lần thử trong ~50s, điểm cao nhất
  **−26**, **22/22 quy tắc ĐẠT**, xuất `TKB_Khoi12.xlsx`
  đủ 3 sheet, 144 ô chữ trong D8:I32, dòng 43 vẫn còn công thức COUNTA, font Times
  New Roman + viền `thin` nguyên vẹn.
- `python3 tu_kiem_tra.py`: 17 loại quy tắc đã đăng ký, ca CƠ SỞ + 11 ca thử đều
  **OK** (~105s), điểm từng ca −36 / −39 / −33 / −43 / −25 / −48 / −55 / −22 / 6 /
  −49 / −50 / 33. 11 loại được thử trực tiếp; 6 loại còn lại (`chi_xep_tiet`,
  `khong_xep_thu`, `khac_ngay`, và 3 loại `uu_tien_*`) được phủ qua ca CƠ SỞ vì
  đã có sẵn trong `cauhinh.json`.
- `python3 tests/thu_du_phong.py`: **20/20 mục ĐẠT** (~10s). Lùi riêng dòng xếp hạng
  dự phòng về bản cũ thì tụt còn 13/18 — ca thử có biết đỏ.
- `python3 tests/thu_kiem_khai_bao.py`: **42/42 mục ĐẠT** (~5s). Lùi phần kiểm miền
  khoá tiết về bản im lặng cũ thì tụt còn 10/21; lùi riêng phần khoá `thu` thì tụt
  còn 34/42 — ca thử có biết đỏ, và đỏ đúng chỗ.
- `python3 tests/thu_loc_tru.py`: **26/26 mục ĐẠT** (~3s). Lùi khoá `tru` khỏi cả hai
  chỗ lọc thì tụt còn 5/25.
- `python3 tests/thu_gop_bo_loc.py`: **23/23 mục ĐẠT** (~5s). Trả `_cum_cua()` về bản
  cài riêng thì tụt còn 16/23.
- `python3 tests/thu_web.py`: **66/66 mục ĐẠT** (~40s). Chạy trong thư mục tạm, không
  đụng `cauhinh.json` thật. Mục quan trọng nhất: 150 ô của vùng D8:I32 giống hệt
  nhau giữa dòng lệnh và web.
- `python3 tests/thu_an_ninh.py`: **213/213 mục ĐẠT** (~2 phút), 12 ca (đếm: `grep -cE "^def ca_"`). Lùi từng bản
  vá ra thì tụt đúng phần của nó và **chỉ** phần của nó — đo trên bộ 172 mục:
  A9 → 163 (9× CA A9) · A10 → 158 (14× CA A10) · A11 → 166 (6× CA A11) ·
  tiêu đề trùng → 166 (6× CA A1). Danh sách tên máy đo trên bộ 202 mục:
  ghim cứng → 198 · gộp Host/Origin → 200 · thêm lại `.strip()` → 200 ·
  **fail-open khi tệp hỏng → 197** · `endswith` → 200 · bỏ kiểm ký tự điều khiển → 201.
  Cổng gác mọi đường đo trên bộ 211 mục: thêm đường ghi mới mà quên gác → 210 ·
  bỏ cổng ở `do_POST` → 192 · bỏ cổng ở `do_GET` → 194 ·
  **chỉ gác đường tĩnh, thả nổi mọi `/api/` → 192**.
- `python3 tests/thu_truong.py`: **30/30 mục ĐẠT** (~2s). Bỏ `kiem_khoa_quy_tac()`
  thì tụt còn 15/23.
- `python3 tests/thu_them_quy_tac.py`: **61/61 mục ĐẠT** (~30s). Bỏ `X.BaiToan(cfg)`
  trong `them_quy_tac()` và thu nhỏ `.nut-o` thì tụt còn 38/50.
- `python3 tests/thu_dang_nhap.py`: **94/94 mục ĐẠT** (~8s), 12 ca. Bỏ
  `tuoi_tai_khoan()` khỏi `doc_phien()` thì tụt còn **87/94** — đỏ đúng 7 mục về
  QĐ 3, trong đó có cả hai mục cũ ở CA 2/CA 7 vốn được lời gọi tay ru ngủ.
- `python3 tests/thu_doc_lai.py`: **44/44 mục ĐẠT** (~5s), 7 ca (đếm: `grep -cE "^def ca_"`). Lùi ra thì đỏ
  đúng phần của nó: `so_ghi_chu` luôn trả None → 25/28 · bỏ nhánh `doc_lai` ở
  `web.py` → 24/28 · cho hai loại dùng CHUNG một `MAU_CAU` → 27/28.
  > **Mục cuối suýt là một mục canh sai chỗ.** Bản đầu chỉ so CÂU ĐÃ DỰNG, và
  > **không** bắt được template chép lại — vì mỗi loại dựng câu từ `VI_DU`
  > riêng nên chuỗi ra vẫn khác nhau. Phải so **chính `MAU_CAU`** mới bắt được.
  > Một mục canh sai chỗ trông y hệt một mục canh đúng chỗ.
- `python3 tests/thu_dau_ban.py`: **39/39 mục ĐẠT** (~90s), 6 ca. Lùi ra thì đỏ
  đúng phần của nó: bỏ hẳn phép kiểm dấu → 33/39 · đẩy phép kiểm RA NGOÀI
  `KHOA_GHI` → 38/39 (**8/12 yêu cầu song song ghi được** thay vì đúng 1) ·
  bỏ kiểm dấu ở hai đường tải → 34/39. Không lần nào Traceback.
- `python3 tests/thu_kho_tuan.py`: **100/100 mục ĐẠT** (~3s, đo 22/8/2026), 7 ca.
  CA 7 lùi ra thì đỏ đúng phần của nó: cho bản "sai" lọt cửa đăng →
  CA 7 lùi ra thì đỏ đúng phần của nó: cho bản "sai" lọt cửa đăng → 92/100 ·
  thiếu khoá thì coi là `dung` → 99/100.
  (Sáu ca đầu, đo trước khi thêm CA 7/8: **77/77**.)
  Lùi ra thì đỏ đúng phần của nó: bỏ luật từ chối trùng SHA-256 → 62/77 ·
  ghi đè lên phiếu hỏng → 66/77 · bỏ vòng chống va chạm tên → 74/77 ·
  nuốt lặng vùng Thứ 7 → 69/77 · bỏ phép so vùng COUNTA → 69/77 · gộp ngầm
  tên môn → 70/77 · bỏ dấu bộ đọc → 70/77 · bỏ hai lớp chắn tệp-không-zip
  → 75/76 (ĐỎ, không VỠ). **Không lần nào Traceback.**
  > **Hai mục lúc đầu KHÔNG biết đỏ, đã sửa.** "Không cái nào bị đè" xanh cả
  > khi bỏ vòng chống va chạm, vì hai tệp thử vốn đã khác tên gốc — nay có
  > mục ép **cùng tên gốc, cùng giây** (truyền `khi=`, không trông vào tốc độ
  > máy). Đúng bài học "một mục canh sai chỗ trông y hệt mục canh đúng chỗ".
- `python3 tests/thu_o_tong.py`: **36/36 mục ĐẠT** (~2s, đo 21/8/2026), 5 ca.
  Vá `D43` về `COUNTA(D10:D42)` trên **bản chép** thì bộ dò ĐỎ **đúng một cột**,
  năm cột kia vẫn sạch, và `mau_tkb.xlsx` thật không bị đụng. CA 4 chứng minh
  `thu_an_ninh.py` CA A8 **không** thay được tệp này: A8 hỏi "bảy công thức còn
  hay mất", mà bản hỏng thì vẫn còn đủ bảy.
- `python3 tests/thu_ghim_du_lieu.py`: **11/11 mục ĐẠT** (~1s). Lùi ra thì đỏ đúng
  phần của nó: ghim lại số cứng ở `thu_web.py` → 10/11 (D1) · ghim lại danh sách tên
  lớp ở `thu_loc_tru.py` → 10/11 (D2) · làm từ vựng bóc rỗng → 8/11 · cho bộ dò soi
  danh sách tệp rỗng → 8/11. **Không lần nào Traceback.**
- `python3 tests/thu_chong_do.py`: **58/58 mục ĐẠT** (~15s), 13 ca (đếm: `grep -cE "^def ca_"`). Lùi từng bản vá
  ra thì tụt đúng phần của nó: chặn TRƯỚC khi băm → 46/51 (5 mục về điều kiện 2) ·
  bỏ chốt chặn trong `ghi_nhan_thu()` → 49/51 (loạt bắn dồn lọt 8 thay vì đúng 5) ·
  đăng nhập đúng không xoá bộ đếm → 48/51 · gõ thêm lại dời mốc khoá → 50/51 ·
  đem sổ vào RAM → 39/52 · gỡ hẳn 2B → 25/52 · để `_ghi_so()` NÉM thay vì kêu to
  → 52/55 (và khi đó **mọi** lần đăng nhập, kể cả mật khẩu ĐÚNG, đều trả 500).
  **Không lần nào Traceback** — bản đầu có vỡ ở `doc_so()` khi thiếu tệp, đã sửa
  thành hàm toàn phần.
- `python3 tests/thu_lenh_chay.py`: **19/19 mục ĐẠT** (**~0,7s** — đo lại 21/8/2026,
  ba lượt cho 0,69 / 0,68 / 0,69 giây; con số `~10s` cũ đã sai. Chạy được bằng **cả**
  `python3` hệ thống lẫn venv, vì `openpyxl` chỉ nạp muộn trong `xuat_excel()`).
  Lùi `quy_tac.py:125` về
  `python` trần thì tụt còn 16/19; lùi thêm `web.py:1191` + `tai_khoan.py:123` thì 14/19.
  Làm hỏng bộ dò cũng đỏ: bắt hụt → 15/19, bỏ lookbehind (bắt quá rộng) → 17/19.
- `python3 tests/thu_xuat_html.py`: **32/32 mục ĐẠT** (~5s). Cũng so 150 ô, lần này
  giữa `tkb_web.html` và file Excel. Mục `node --check` tự bỏ qua nếu máy không có
  `node` — ca thử không đòi hỏi phải cài `node`.
- Dòng hậu kiểm = 3 kiểm tra nền + 1 dòng gom tiết mỗi môn + 1 dòng mỗi quy
  tắc cứng. **Đừng chép tổng vào đây** — nó đổi theo `cauhinh.json` (đo
  22/8/2026: `23/23`, trước đó tài liệu ghi `22` và đã sai).
  **Đừng ghim con số này vào ca thử** — thêm một quy tắc vào `cauhinh.json` là vỡ.
  Khẳng định `Tổng: N/N quy tắc ĐẠT` (hai số bằng nhau) thay vì so với số cụ thể.

---

## Kỷ luật ca thử — bất biến

> **Bản hỏng phải vá vào MÃ CHẠY THẬT và quan sát qua HTTP THẬT.**
> **Không gọi thẳng hàm rồi xem giá trị trả về.**
> **Ca thử phải biết ĐỎ, không phải biết VỠ.**
>
> **Ca thử KHÔNG khẳng định trên VĂN BẢN MÃ NGUỒN. Khẳng định trên HÀNH VI quan
> sát qua HTTP. Nếu buộc phải đọc mã nguồn thì LỘT CHÚ THÍCH TRƯỚC.**
>
> **Mọi ca thử dựng máy chủ, luồng, hoặc khoá phải có ĐỒNG HỒ CANH.**
> **Bộ thử không bao giờ được phép TREO — hết giờ thì ĐỎ, không chờ tiếp.**

MƯỜI lần đã dính, cùng một gốc — mỗi lần một kiểu khác:

| # | Kiểu | Nó đã che giấu gì |
|---|---|---|
| 1 | Gọi tắt vào hàm Python | Bỏ qua cả tầng HTTP, tức bỏ qua đúng chỗ sắp đặt cổng đăng nhập |
| 2 | `list.index()` ném `ValueError` | Ca thử **chết giữa chừng** thay vì báo đỏ; mọi ca sau nó không bao giờ chạy |
| 3 | Chỉ xem giá trị trả về của hàm nạp | Bản fail-open trả `(None, None)` y hệt bản đúng → xanh giả, trong khi máy chủ mở toang |
| 4 | Khớp chuỗi trong mã nguồn | Chuỗi đó cũng nằm trong **dòng chú thích** ngay trên — ca thử kiểm lời chú thích chứ không kiểm mã |
| 7 | **Ghim hằng số lấy từ `cauhinh.json`** | Ca thử đỏ vì **DỮ LIỆU đổi**, không vì mã sai — thầy cô thêm bốn quy tắc qua giao diện là ba bộ thử đỏ một lượt, mà không dòng mã nào sai. Tệ hơn ở chiều ngược lại: `c.gv == 'N.Uyên'` dùng để **tính kỳ vọng**, nên khi cô ấy không còn trong `phan_cong` thì số đếm thành 0, phép trừ hoá ra "giữ nguyên tất cả", và ca thử **XANH trong khi không kiểm gì cả**. Luật này CLAUDE.md đã ghi từ lâu mà vẫn có 12 chỗ vi phạm — vì **luật viết ra không tự thi hành**. Nay có `tests/thu_ghim_du_lieu.py` bắt cả lớp lỗi |
| 6 | **Gọi tay hàm nạp ngay trước khi khẳng định** | Biến thể của kiểu 1. `thu_dang_nhap.py` gọi `W.nap_tai_khoan_may_chu()` rồi mới khẳng định "tắt tài khoản có hiệu lực NGAY" — nên nó chứng minh HỆ QUẢ (phiên chết) mà bỏ qua CÁI CÒ (máy chủ có tự đọc lại tệp không). Ngoài đời `nap_tai_khoan_may_chu()` chỉ chạy một lần trong `main()`, tức QĐ 3 **sai suốt** mà ca thử vẫn xanh |
| 8 | **Bóc khoá của câu trả lời HỎNG ngay trong dòng khẳng định** — lại là kiểu 2 | Ca thử CA 7 (`thu_doc_lai.py`) viết `pv4['ve'][1]['so_cum']` và `d['pham_vi']['so_cum']`. Chạy trên mã đúng thì xanh; lùi bản vá ra thì **`IndexError` / `KeyError`** — vỡ, không đỏ. Bài học mở rộng: luật cũ chỉ nói về *dữ liệu vào* hỏng, nhưng bản hỏng còn có thể trả **THIẾU KHOÁ** ở câu trả lời. Nên câu đúng là: **mọi phép bóc trong dòng khẳng định phải chịu được hình dạng mà BẢN HỎNG trả về**, cả vào lẫn ra. Cách chữa: `isinstance` + `.get()` trước, rồi mới so — và in luôn hình dạng thật ra thông báo (`các khoá ['canh_bao', 'cau', 'loi']`) để biết ngay đã thiếu gì.<br><br>**Gặp lại ngay hôm sau, lần này ở ca thử CÓ SẴN:** lùi `noi_dung` khỏi `/api/quy-tac` thì `thu_them_quy_tac.py` **CA 1** ném `KeyError` ở dòng `r['noi_dung'].get('thu')` — vỡ ngay ca đầu, nên CA 8 (ca thật sự canh chuyện đó) **không bao giờ chạy**. Bài học thêm: viết ca thử mới đúng chuẩn là chưa đủ — **lùi bản vá ra rồi xem NÓ VỠ Ở ĐÂU**, vì chỗ vỡ thường nằm trong một ca cũ chẳng liên quan |
| 5 | **Bộ thử TREO thay vì đỏ** | Dạng KHÁC HẲN bốn cái trên: bốn cái đầu là *khẳng định sai chỗ*, cái này là *bộ thử không tự thoát được*. Lùi lỗi khoá-tái-nhập ra thì `thu_phien.py` treo cứng (`MayChuTam.__exit__` gọi `may.shutdown()`, hàm đó chờ mãi một luồng kẹt trong khoá) — ngồi đợi mãi vẫn chưa xong. **Treo còn tệ hơn vỡ**, vì nó chặn luôn mọi bộ thử chạy sau, và trên máy tự động thì nó ngốn hết thời gian rồi chết vì hết giờ, không ai biết mục nào hỏng |
| 9 | **Chốt canh TRẢ VỀ SỚM nên không bao giờ nhìn tới thứ nó canh** | `doc_tkb._duong_sheet()` `return` ngay khi khớp sheet đầu tiên, nên danh sách "các sheet khác" chỉ chứa những sheet đứng TRƯỚC nó — tức gần như luôn RỖNG. Sheet bị bỏ sót đúng là `THEO DÕI BÙ TBK`, sheet đứng sau `Khối 12` và là sheet **chứa lý do nghỉ**. Nếu Đợt 4 tin vào danh sách đó để lọc trước khi đăng thì nó đăng luôn thứ đáng lẽ phải chặn. Hàm vẫn trả đúng cái nó được hỏi (đường dẫn sheet), chỉ sai ở cái nó trả **kèm theo** — nên không ca thử nào về đường chính đỏ. Sửa ở `e312121` |
| 10 | **Hai tệp thử khác nhau ở đúng chỗ khiến nhánh cần canh không bao giờ chạy tới** | Mục *"không cái nào bị đè"* của `thu_kho_tuan.py` **xanh cả khi đã bỏ hẳn vòng chống va chạm tên** — vì hai tệp thử có tên gốc khác nhau (`d.xlsx`, `e.xlsx`) nên tên đích vốn đã khác, vòng đó chưa bao giờ quay lấy một lần. Phải **ÉP** điều kiện va chạm: cùng tên gốc, cùng giây, và **truyền giây vào** (`khi=`) chứ không trông vào việc máy chạy đủ nhanh — ca thử phụ thuộc tốc độ máy là ca thử sẽ chớp đỏ trên máy của trường. Sửa ở `e312121` |

> ### KIỂU HỎNG SỐ 2 ĐÃ DÍNH BỐN LẦN — đếm lại cho khỏi quên
>
> | # | Vỡ ở đâu | Vì sao |
> |---|---|---|
> | 1 | `list.index()` ném `ValueError` | Lùi bản vá ra thì thao tác biến mất |
> | 2 | `MayChuTam.__exit__` gọi `shutdown()` | Chờ mãi một luồng kẹt trong khoá — **treo**, còn tệ hơn vỡ |
> | 3 | `doc_so()` ném khi thiếu tệp | Bản hỏng đang thử làm sổ khoá biến mất |
> | 4 | `KeyError: 'nhom'` | Ca thử nhét một lớp giả **thiếu `NHAN`**, API trả 500, phép bóc `d2['nhom']` ném |
>
> Lần 4 đáng nhớ nhất vì dữ liệu hỏng **chính là đầu vào mong đợi** của ca thử
> đó — nó cố ý dựng một lớp thiếu khai báo để thử lưới đỡ.
>
> **LUẬT: ca thử cố ý dựng dữ liệu HỎNG phải bọc phép gọi trong `try`, hoặc
> kiểm HÌNH DẠNG câu trả lời TRƯỚC khi bóc. Dữ liệu hỏng là đầu vào mong đợi
> của ca thử đó, không phải sự cố.**

> ### MỘT MỤC CANH SAI CHỖ TRÔNG Y HỆT MỘT MỤC CANH ĐÚNG CHỖ.
> ### CHỈ CÓ LÙI BẢN VÁ RA MỚI PHÂN BIỆT ĐƯỢC.
>
> Không phải một kiểu hỏng nữa trong bảng trên — đây là lý do **cả bảng trên
> tồn tại**. Mục nào cũng in ra `[ĐẠT]` như nhau; mắt thường không phân biệt
> được mục thật sự canh cái gì đó với mục chỉ trông như đang canh.
>
> Đã đo, 21/8: `thu_doc_lai.py` CA 2 khẳng định *"17 câu khác nhau đôi một"* và
> tôi viết trong docstring rằng đó là mục **duy nhất** bắt được `MAU_CAU` đặt
> bừa. Lùi thử — cho hai loại dùng **chung một** `MAU_CAU` — thì nó **vẫn
> xanh**: mỗi loại dựng câu từ `VI_DU` riêng nên chuỗi ra vẫn khác nhau. Phải
> so **chính chuỗi mẫu** mới bắt được.
>
> Vì vậy: **viết xong một mục canh thì phải lùi ra thử ngay**, đừng đợi tới lúc
> có người sửa mã. Mục càng nghe có vẻ chắc chắn thì càng đáng thử.

**Danh sách kiểm cho ca thử mới:**

1. Có dựng máy chủ thật và đi qua HTTP không? Nếu không, vì sao?
2. Lùi bản vá ra thì mục này **đỏ** hay **vỡ**? Nếu vỡ thì sửa (đừng `.index()`,
   đừng chỉ số cứng, đừng đọc khoá chắc chắn có).
3. Có mục nào chỉ xem giá trị trả về mà không xem hành vi không?
4. Nếu có đọc mã nguồn: đã lột chú thích chưa? Đã có guard cho trường hợp phép
   bóc trả về rỗng chưa?
5. Ca thử có dựng máy chủ / luồng / khoá không? Nếu có thì **đã đặt đồng hồ
   canh chưa** (`dat_dong_ho_canh()` trong `thu_phien.py` là mẫu)?
6. Có mục tự khẳng định **điều kiện tiên quyết** chưa — để khi dữ liệu đổi khiến
   ca thử mất khả năng phân biệt thì nó báo đỏ chứ không âm thầm xanh?
7. Có chỗ nào so bằng với **hằng số lấy từ `cauhinh.json`** không (số quy tắc,
   tên lớp, tên môn, tên GVCN)? Dựng kỳ vọng TỪ tệp, đừng chép giá trị ra.
   `tests/thu_ghim_du_lieu.py` canh việc này, nhưng đừng đợi nó nhắc.
   **Và nếu số kỳ vọng được TÍNH TỪ dữ liệu thì phải khẳng định nó KHÁC 0
   trước khi dùng.** Bộ lọc rỗng làm phép so trở nên vô nghĩa mà **vẫn xanh** —
   đây là dạng lỗi số 3 (xanh giả) ở hình thức mới, và nó nguy hiểm hơn hẳn
   việc đỏ oan. Đã đo một lần:
   `n_uyen = len([c for c in NEN.cac_cum if c.gv == 'N.Uyên'])` — cô ấy rời
   `phan_cong` là số này thành 0, phép trừ `tat_ca - n_uyen` hoá ra "giữ
   nguyên tất cả", và ca thử xanh trong khi không kiểm gì cả.
8. Nếu ca thử phải **tự dựng trạng thái** (thêm quy tắc nháp, tắt bớt quy tắc)
   thì dữ liệu dựng ra có **mâu thuẫn được** với `cauhinh.json` thật không?
   Bộ lọc nên chọn thứ KHÔNG KHỚP GÌ CẢ, để nó không bao giờ có ý kiến về dữ
   liệu nhà trường — xem `NHAP_A` trong `tests/thu_phien.py`.
9. Mục này canh một **giá trị trả KÈM THEO** (danh sách phụ, cờ, số đếm) chứ
   không phải giá trị chính? Nếu có thì hỏi tiếp: hàm có thể trả **đúng cái
   chính mà sai cái kèm theo** không — và lúc đó có mục nào đỏ không?
   (Nếp hỏng 9.)
10. Hai dữ liệu thử của mục này có **khác nhau ở đúng chỗ** khiến nhánh cần
   canh không bao giờ chạy tới không? Nhánh chỉ chạy khi hai thứ TRÙNG nhau
   (trùng tên, trùng giây, trùng khoá) thì phải **ép cho trùng**, và ép bằng
   tham số truyền vào chứ không bằng tốc độ máy. (Nếp hỏng 10.)

---

## Việc treo

```
[!] CHẶN — THU HẸP ACL TRƯỚC KHI MỜI BẤT KỲ AI VÀO TAILNET.
    Số đo 21/8/2026:
      · ACL đã biên dịch (tailscale debug netmap, PacketFilter mục 0) cho
        phép MỌI nguồn trong 100.64.0.0/10 tới MỌI cổng 0-65535
      · tailnet hiện có thiết bị của BỐN tài khoản khác nhau
      · :20267 Directus — chạy bằng ROOT, bind 0.0.0.0 + [::] — trả lời
        trên IP tailnet 100.74.144.121
      · :11434 Ollama — bind wildcard — cũng trả lời trên IP đó
      · :20266 TKB — CHỈ loopback, bắn vào IP tailnet KHÔNG nối được
    Điều kiện cũ "chờ xong cổng đăng nhập" KHÔNG ĐỦ: cổng đăng nhập chỉ
    gác :20266. Mời một người vào tailnet là mở cho họ cả :20267 chạy
    bằng root, mà cửa đó không có mật khẩu nào của dự án này canh.
    => Mời người = mở Directus. Hai chuyện này đi liền, đừng tách.
    NGƯỜI DÙNG TỰ SỬA ACL. Đừng đụng vào — sửa sai là mất đường vào máy
    từ xa, và không có đường nào chữa từ xa.

[ ] Đổi mật khẩu thử trước khi đặt sau reverse proxy
[ ] Bật cờ Secure cho cookie khi có TLS
[ ] Thêm --host (giữ 127.0.0.1 cho tới khi có TLS)
[ ] Hai loại quy tắc CHƯA HỀ được dùng ở đâu: `cung_ngay` và
    `phai_ke_nhau` — không có trong 17 quy tắc đang chạy, cũng không có
    trong mục "_quy_tac_de_san_chua_bat". Người dùng chốt: GIỮ NGUYÊN trong
    "nâng cao", đừng bỏ — chưa dùng không có nghĩa là không cần.
    Xem lại khi mở rộng sang khối 11 và khối 10.
[ ] BẬT AI NGOÀI CHO CHATBOX = gửi TÊN GIÁO VIÊN, TÊN LỚP, TÊN MÔN của
    trường ra một máy chủ ở nước ngoài. Đây là QUYẾT ĐỊNH CỦA NHÀ TRƯỜNG,
    không phải quyết định kỹ thuật. Phải hỏi ý nhà trường TRƯỚC KHI bật,
    đúng như lúc xin phép công khai TKB trên GitHub Pages.
    Về kỹ thuật thì urllib trong thư viện chuẩn gọi được, không phá luật
    "chỉ dùng thư viện chuẩn + openpyxl". Nhưng kỹ thuật làm được không có
    nghĩa là được phép làm.
    Mặc định TẮT, và tắt theo kiểu fail-closed: khoá thiếu hoặc hỏng thì
    dùng luật viết tay, không bao giờ tự bật.
[ ] ĐỢT 3 — GIAO DIỆN TẠO QUY TẮC. Bốn việc, thiết kế ở mục riêng bên
    dưới, CHƯA DUYỆT:
      1. Câu ĐỌC LẠI sinh từ máy, hiện cạnh ghi_chu người dùng gõ
      2. Xem trước PHẠM VI (bao nhiêu lớp / cụm / tiết; 0 lớp thì cảnh báo)
      3. Tên loại bằng TIẾNG VIỆT thay cho chi_xep_thu / khac_ngay / ...
      4. Nút "Tạo giống quy tắc này" trên mỗi dòng
    Lý do: 20/8 thầy cô khai QT 14/15/16 với ghi_chu nói "không trùng ngày
    với" mà loai lại là chi_xep_thu — NGHĨA NGƯỢC HẲN. Phần mềm nhận cả hai,
    không kêu một tiếng, phải bấm Lưu 5 lần rồi chạy xếp mới lộ ra là cấu
    hình VÔ NGHIỆM. Người dùng cuối không có ai gỡ giúp.
[ ] CHƯA AI chứng minh chống được MẤT ĐIỆN THẬT. SIGKILL giữa lúc ghi chỉ
    chứng minh tệp đích không rách khi TIẾN TRÌNH chết — dữ liệu vẫn có thể
    còn nằm trong bộ nhớ đệm của hệ điều hành. Muốn chứng minh phải cắt điện
    thật hoặc dùng dm-flakey (đòi quyền root). CA A11 tự khai đúng giới hạn
    này ở tests/thu_an_ninh.py:962-968 — nó ghim THỨ TỰ fsync/replace, không
    ghim độ bền vật lý. Đừng đọc bảng "cắt điện giả lập" mà tưởng đã xong.
[ ] Quyền 600 của tai_khoan.json: mới đo được BIT ĐƯỢC LƯU VÀ ĐỌC LẠI ĐÚNG
    trên ntfs3 (nhờ tuỳ chọn gắn "acl"). CHƯA đo được người dùng KHÁC có bị
    chặn thật không — máy chỉ có một tài khoản (uid 1000; đo lại 22/8/2026:
    `awk -F: '$3>=1000 && $3<65534' /etc/passwd | wc -l` -> 1) và không có sudo.
    Suy luận là uid khác rơi vào lớp "other" nên 600 chặn, nhưng đó là suy
    luận chứ không phải số đo.
[ ] Tách 3 tài khoản RIÊNG cho 3 người, thay cho một tài khoản chung.
    Người dùng đã chốt: giữ một tài khoản chung cho GIAI ĐOẠN THỬ; khi mời
    đồng nghiệp vào tailnet thì tính lại. Việc này chữa GỐC của hai chuyện:
    khoá oan chỉ ảnh hưởng một người thay vì cả khoa, và QĐ 4 ("dán tên người
    xếp") mới có nghĩa — hiện mọi lượt xếp đều mang tên "khoahoccoban", nên
    câu "Kết quả đã bị thay bởi lượt xếp của <tên>" không nói được gì.
[ ] Sửa được thân quy tắc đã nằm trong cauhinh.json. Cần nghĩ lại dấu bản 2C
    trước: hiện băm CẢ TỆP nên hai người sửa HAI QUY TẮC KHÁC NHAU vẫn chặn
    oan cả hai. Hướng: dấu bản theo từng quy tắc, hoặc gộp thay vì chặn.
    Đợt riêng, không chen vào Đợt 3.
    (Người dùng đã chốt 21/8: CHẤP NHẬN giới hạn, ĐỪNG làm bây giờ. Nút Sửa
     chỉ hiện trên quy tắc nháp là đúng — nút hứa việc nó không làm được thì
     tệ hơn không có nút.)
[ ] BA CHỮ TRONG NHÃN chờ người dùng quyết sau khi xem màn hình thật —
    "ô", "nhóm", "cụm" có phải chữ của PHẦN MỀM chứ không phải chữ thầy cô
    quen dùng không:
      · "ô"    trong khong_xep_o, co_dinh — hay thầy cô nói "tiết 3 thứ Hai"?
      · "nhóm" trong bốn nhãn quan hệ — thầy cô nghĩ theo MÔN và LỚP
      · "cụm"  trong gom_tiet, uu_tien_ke_nhau — cùng câu hỏi
    Ghi ở đây để câu hỏi không trôi mất qua một lần tóm tắt hội thoại.
    CHƯA trả lời, chờ người dùng đi qua 11 mục xem-bằng-mắt rồi quyết.

> **Ba dòng này đi với nhau, đừng làm lẻ.** Chừng nào còn giữ ràng buộc "không
> thêm `--host`" thì máy chủ vĩnh viễn chạy `http://127.0.0.1`, mà trên `http://`
> trình duyệt **vứt** cookie có cờ `Secure` — bật lẻ cờ đó là không ai đăng nhập
> được, và thông báo lỗi sẽ không hề nhắc tới nó. Vì vậy Giai đoạn 2 **cố ý chưa
> thêm cờ vào mã**: thêm một công tắc chỉ có thể sai chứ không bao giờ đúng là
> tự đặt bẫy. Khi nào thật sự có proxy TLS thì làm cả ba dòng cùng lúc.

### Đã đóng — ĐỪNG mở lại

```
[x] "Làm cho tailscale serve tự sống lại sau khởi động"
    ĐÓNG 21/8/2026: KHÔNG PHẢI VIỆC. Đã đo — nó vốn đã tự sống lại.
    Khởi động lại máy thật, không gõ lệnh nào, rồi vào từ điện thoại 4G
    qua :8443: chạy suốt, không 502. Bốn dòng số ở mục "Đường vào từ
    ngoài"; công thức đo lại ở CHAY_CUNG_MAY.md mục 7.
    => KHÔNG dựng unit systemd cho tailscale serve. Thêm mã khi số đo nói
       không cần là thêm một chỗ để hỏng.
    Cái CÒN LẠI cần canh không phải "nó có tự lên không" mà là "cấu hình
    serve có bị xoá mất không" — hai chuyện khác nhau. Xem CHAY_CUNG_MAY.md
    mục 6, hai dòng "cách kiểm / cách dựng lại".
```

> **Ghi ở đây chứ không xoá trắng, và đây là lý do.** Một mục biến mất không dấu
> vết thì lần sau có người lại nghĩ ra đúng việc đó, lại mất một buổi để kết
> luận y hệt. Dòng `[x]` kèm ngày và lý do rẻ hơn nhiều so với việc đo lại.
>
> **Lưu ý về lịch sử:** mục này chưa từng có một dòng trong khối `[ ]` phía
> trên — nó sống dưới dạng một câu chưa-có-số-đo ở `CHAY_CUNG_MAY.md` mục 6
> (*"về nguyên tắc nó sống qua khởi động lại. Nhưng đó là nguyên tắc; bằng
> chứng là mục 7"*). Câu đó nay đã thay bằng số đo.

---

## Đợt 3 — giao diện tạo quy tắc (THIẾT KẾ, **CHƯA DUYỆT**)

Chưa viết một dòng mã nào. Ghi ở đây để bản thiết kế không trôi mất.

### Câu ĐỌC LẠI sinh từ đâu — và làm sao BẮT BUỘC mọi loại phải có

Không viết tay 17 hàm sinh câu. Nguyên liệu đã có sẵn hết trong `TRUONG`:
mỗi trường đã khai `nhan` tiếng Việt (`"Chỉ được xếp vào các thứ"`) và `kieu`
(`ds_thu`, `ds_tiet_buoi`, `loc`…). Ba mảnh:

| Mảnh | Ai viết | Viết mấy lần |
|---|---|---|
| Mô tả bộ lọc — *"Vật lý của 12B1, 12B2 (thầy T.V.Quỳnh)"* | dùng chung | **1 lần** cho cả 17 loại |
| Định dạng giá trị theo `kieu` — `[2,3]` → *"Thứ 2, Thứ 3"* | dùng chung | **1 lần mỗi `kieu`** (đếm: `len(QT.KIEU)`) |
| Vị ngữ — *"CHỈ được xếp vào {thu}"* | mỗi loại | một **CHUỖI MẪU**, không phải một hàm |

`MAU_CAU` là **chuỗi**, không phải hàm — ít chỗ sai hơn hẳn, và
`@dang_ky` kiểm được ngay lúc nạp mô-đun.

**Bắt buộc bằng CẤU TRÚC, không bằng lời nhắc.** `@dang_ky` từ chối đăng ký
lớp thiếu `MAU_CAU`, hoặc có ô `{ten}` không khớp trường nào trong `TRUONG`
→ `import quy_tac` DỪNG. Thêm loại mới mà quên thì **cả chương trình không
chạy**, không phải "ca thử đỏ ở đâu đó".

> **KHÔNG có đường lùi "thiếu MAU_CAU thì tự ghép từ TRUONG".** Nghe thì tiện,
> nhưng đường lùi biến việc quên thành việc **im lặng** — đúng hạng lỗi mà cả
> Đợt 2 dựng ra để chống. Bản ghép tự động chỉ dùng làm **chữ mồi** cho người
> viết loại mới chép ra rồi sửa.

Ca thử canh **chất lượng**, không chỉ sự tồn tại — vì `MAU_CAU = 'x'` cũng qua
được `@dang_ky`. Dựng câu từ chính `VI_DU` của mỗi loại (17/17 loại đã có sẵn
`VI_DU`, không phải thêm dữ liệu thử), rồi đòi: câu không rỗng · không còn `{`
sót · **17 câu KHÁC NHAU ĐÔI MỘT** · và có nhắc lại giá trị lấy từ `VI_DU`.
Mục "khác nhau đôi một" mới là mục bắt được câu vô nghĩa.

### So câu máy với ghi_chu người gõ — chỉ báo khi có BẰNG CHỨNG NGƯỢC

**Không đo độ giống nhau.** Hai câu bao giờ chẳng khác nhau; báo theo độ giống
là đẻ ra báo động giả, mà báo động giả thì thầy cô sẽ học cách bỏ qua — đúng
bài học "đừng nói quá" của khung cảnh báo 2C.

Thay vào đó: mỗi **NHÓM** loại có vài từ khoá tiếng Việt, và chỉ báo khi
`ghi_chu` chứa từ khoá của một nhóm **KHÁC** nhóm đang chọn:

| Nhóm | Từ khoá trong ghi_chu |
|---|---|
| chỉ-xếp-vào | "chỉ", "duy nhất" |
| không-xếp-vào | "không xếp", "tránh", "cấm" |
| khác-ngày | "khác ngày", "không cùng ngày", "không trùng ngày" |
| cố-định | "cố định", "đúng vào" |

Đúng cái đã xảy ra: ghi_chu *"không trùng ngày với"* + loại `chi_xep_thu`
(nhóm chỉ-xếp-vào) → báo. Từ khoá gắn theo **nhóm** (`NHOM_LOAI`, đã có sẵn và
đã tự lộ loại chưa xếp nhóm), nên loại mới thừa hưởng, không phải khai thêm.

### Bốn điều kiện người dùng đặt thêm (21/8) — đã duyệt

**1. Từ khoá là GỢI Ý, không phải PHÁN QUYẾT.** Bảng từ khoá bắt được QT 16 vì
ghi_chu tình cờ có chữ *"không trùng ngày"*. Thầy cô viết *"Sử với Toán đừng
dính nhau"* thì **không từ khoá nào khớp**. Nên câu đọc lại phải hiện **LUÔN
LUÔN**; từ khoá chỉ quyết định có **tô cảnh báo** hay không.
Ca thử: ghi_chu không chứa từ khoá nào → câu đọc lại **vẫn hiện**.

**2. "CHƯA XẾP NHÓM" phải ĐỎ, không được im.** Tôi từng nói loại mới "thừa
hưởng nhóm CHƯA XẾP NHÓM nên không phải khai thêm" — đó chính là **dạng lỗi im
lặng** mà cả tài liệu này viết ra để chống. Ca thử ghim: mọi loại trong
`DANH_MUC` phải có mặt trong `NHOM_LOAI`, và phải có `NHAN` lẫn `MO_TA`. Thiếu
bất kỳ cái nào → **ĐỎ**. Loại thứ 18 không được lọt.

**3. Nhãn tiếng Việt phải nói RÕ CHIỀU.** Cạm bẫy của `chi_xep_thu` là chữ
**"CHỈ"**. Nhãn phải bật chữ đó lên. Hai nhãn của cặp dễ lẫn nhất:

| Loại | Nhãn tiếng Việt |
|---|---|
| `chi_xep_thu` | **CHỈ được xếp vào những thứ đã chọn** — mọi thứ khác đều cấm |
| `khac_ngay` | Hai nhóm **KHÔNG được rơi vào cùng một ngày** — mỗi nhóm vẫn xếp thứ nào cũng được |

Vế sau dấu gạch của mỗi nhãn nói đúng cái mà **nhãn kia không làm**. Đó mới là
chỗ khiến hai loại không lẫn được nữa; chỉ đọc vế đầu thì vẫn lẫn.

**4. Giữ ngưỡng chạm**: chữ ≥ 15px, nút và ô chọn cao ≥ 40px. Thầy cô dùng điện
thoại. `tests/thu_them_quy_tac.py` CA 6 đã canh sẵn, nhãn dài hơn thì phải xem
lại bố cục bằng mắt vì CA 6 **không** bắt được chữ tràn khung.

### Việc 1 — ĐÃ LÀM (21/8)

`quy_tac.cau_doc_lai(r)` nhận **một dict quy tắc**, trả câu tiếng Việt. Ba mảnh,
và chỉ mảnh thứ ba là việc của người thêm loại mới:

| Mảnh | Viết mấy lần |
|---|---|
| `cau_bo_loc()` — mô tả bộ lọc | **1 lần** cho cả 17 loại |
| `_dinh_dang()` — theo `kieu` đã khai trong `TRUONG` | **1 lần mỗi kiểu** |
| `MAU_CAU` — vị ngữ | một **chuỗi mẫu** mỗi loại |

`@dang_ky` **TỪ CHỐI** đăng ký lớp thiếu `MAU_CAU`, hoặc có ô `{ten}` không
khớp `TRUONG` → `import quy_tac` DỪNG. Không có đường lùi "tự ghép từ TRUONG".

> **Viết câu đọc lại đã bắt được lỗi trong chính bản thảo của tôi.** Phải đọc
> `def diem()` của bốn tiêu chí mềm mới viết đúng được vị ngữ, và hoá ra
> `uu_tien_it_buoi` là điểm **TRỪ** (`return -dv * số buổi`) chứ không phải
> cộng, còn `uu_tien_o` tính theo **từng TIẾT** (`d += dv * c.size`) chứ không
> phải mỗi lần. Câu đầu tôi viết sai cả dấu lẫn đơn vị. Đó chính là thứ mà câu
> đọc lại sinh ra để chặn — chỉ khác là lần này nó chặn người viết ra nó.

`so_ghi_chu(r)` so ghi chú người gõ với **ý niệm** của loại (`Y_NIEM` +
`TU_KHOA_NHOM`), và **chỉ báo khi có bằng chứng ngược**. Câu đọc lại thì hiện
**LUÔN LUÔN** — từ khoá là gợi ý, không phải phán quyết.

Đường HTTP: `POST /api/thu-quy-tac` với `{"doc_lai": true}`. **Không thêm đường
mới** (vẫn 19). Nhánh rẽ đặt **trước** cả phép kiểm "đang xếp" lẫn `KHOA_THU`:
câu đọc lại chỉ ghép chuỗi (đo được **20 lượt / 0,01 giây** trên MÁY A;
đo lại 22/8/2026: mọi quy tắc hết **0,11 ms**), bắt nó xếp hàng
sau một lượt xếp thử 8 giây thì ô nhập đứng hình đúng lúc người dùng đang gõ.

### Việc 3 — ĐÃ LÀM (21/8): nhãn tiếng Việt cho 17 loại

> **Phân biệt `chi_xep_thu` ↔ `khac_ngay` KHÔNG nằm ở chữ "CHỈ" hay "KHÔNG".**
> Nó nằm ở chỗ **có nêu tên NGÀY hay không**:
>
> | Loại | Bạn nói gì |
> |---|---|
> | `chi_xep_thu` | Bạn nêu **RÕ ngày nào được phép** (`thu: [2,3]`) |
> | `khac_ngay` | Bạn **KHÔNG nêu ngày nào cả**, chỉ nói hai nhóm phải tách ra |
>
> QT 16 ngày 20/8 nêu `thu: [3,4,5]` — nếu nhãn nói thẳng *"bạn nêu rõ ngày nào
> được phép"* thì ngay lúc chọn đã thấy sai. Chẩn đoán đầu ("cạm bẫy là chữ
> CHỈ") đúng một nửa: chữ CHỈ làm câu dễ đọc nhầm, nhưng thứ phân biệt được hai
> loại là **có tham số ngày hay không**.

`NHAN` khai ở mỗi lớp, `@dang_ky` **ép** y như `MAU_CAU`. Ô chọn hiện **nhãn
tiếng Việt**, tên kỹ thuật xuống dòng ngay dưới (`#ten-ky-thuat`, 15px, phông
đơn cách) — thầy cô còn đối chiếu `cauhinh.json` bằng Notepad.

**Hai tầng chặn loại thứ 18, cần cả hai:**

| Tầng | Chặn cái gì |
|---|---|
| `@dang_ky` + phép kiểm ngay sau `NHOM_LOAI` | Người **thêm loại mới** theo đường bình thường — `import quy_tac` DỪNG |
| `nhom_danh_muc()` trả nhóm "CHƯA XẾP NHÓM" | Mọi **đường vòng** còn lại (nhét thẳng vào `DANH_MUC`) — lưới đỡ lúc chạy |

`tests/thu_truong.py` CA 7 canh cả hai, và canh thêm **chất lượng nhãn**: mỗi
nhãn phải bật một chữ chỉ hướng (CHỈ / KHÔNG / PHẢI / NÊN / GHIM / MỖI / Chia),
và 17 nhãn khác nhau đôi một.

> **`danh_muc_loai()` dùng `getattr` cho `NHAN`, không `.NHAN` trần.** Cửa ép là
> `@dang_ky`; đây là tầng **hiển thị**. Để nó ném `AttributeError` là đổi một
> lỗi khai báo thành một mã sự cố 500 vô nghĩa cho người dùng.

### Xem trước phạm vi (việc 2) — quy tắc này chạm vào những gì

`pham_vi_quy_tac(r, bt)` trong `quy_tac.py` nhận **một dict quy tắc trần** và
trả về số cụm / số tiết / danh sách lớp · môn · GV bị chạm, cộng `ten_la` =
những tên khai trong bộ lọc mà **không có trong dữ liệu nhà trường**.
`canh_bao_pham_vi(pv)` biến kết quả đó thành một câu tiếng Việt, hoặc `None`.

| Cảnh | Câu cảnh báo nói gì |
|---|---|
| Có tên lạ | Chỉ **đích danh** từng tên sai, theo từng khoá |
| Loại hai vế mà một vế rỗng | Nêu **tên vế** rỗng (A hay B) |
| Không tên nào lạ mà vẫn khớp 0 cụm | Nhắc ba nguyên nhân hay gặp |

`/api/quy-tac` **chở sẵn phạm vi của từng quy tắc** (`lop` · `mon` · `gv` ·
`so_cum` · `so_tiet`) để màn hình Quy tắc lọc được theo GV / môn / lớp. Đo trên
`cauhinh.json` thật (MÁY A; đo lại 22/8: 2,45 ms): cả lượt — đọc tệp + dựng `BaiToan` + 17 lần tính phạm vi —
hết **2,67 ms** (3,7 ms cả vòng HTTP). Tính ở máy chủ vì *"quy tắc này chạm vào
ai"* **là ngữ nghĩa của bộ lọc**; để JS tự bóc `noi_dung.loc` là dựng bản cài
thứ hai, đúng kiểu lệch đã trả giá ở `khop_loc()` / `_cum_cua()`.
`thu_them_quy_tac.py` CA 9 canh đúng điều đó — nó ĐỎ nếu JS nhắc tới
`noi_dung.loc`.

Cấu hình hỏng thì `pham_vi` là `None` và **thẻ vẫn hiện**: thầy cô vào màn hình
Quy tắc chính là để sửa chỗ hỏng đó.

> **Khớp 0 cụm là CẢNH BÁO, không CHẶN.** Có học kỳ lớp đó chưa học môn ấy —
> quy tắc khớp 0 cụm là đúng ý người khai. Chặn hẳn là chặn oan, đúng cái bẫy
> đã bác một lần ở `/api/tai-ve` khi máy chủ vừa khởi động lại.

> **Vì sao mục này đáng một hàm riêng: đây là bẫy `n_uyen == 0` ở phía NGƯỜI
> DÙNG.** Quy tắc gõ sai tên vẫn lưu được, vẫn hiện trong danh sách, và hậu
> kiểm vẫn báo **ĐẠT** — vì không có gì để kiểm. Người khai tưởng đã cấm; thực
> ra không cấm gì. `tests/thu_ghim_du_lieu.py` bắt đúng lớp lỗi này ở phía ca
> thử; `pham_vi_quy_tac()` bắt nó ở phía màn hình.

**Đi CHUNG một lượt gọi với câu đọc lại**, nhánh `{"doc_lai": true}` của
`POST /api/thu-quy-tac` — hai thứ luôn hiện cùng nhau, tách ra là hai lượt mạng
cho một lần gõ phím. Không thêm đường mới; vẫn **19 đường**.

**Không bao giờ ném.** Đây là thứ chạy trong lúc người dùng đang gõ **dở**:
loại chưa chọn, khoá bắt buộc chưa điền, bộ lọc sai kiểu — không cái nào là sự
cố. Sai thì trả khoá `loi` và phần xem trước tự ẩn, còn **câu đọc lại vẫn
hiện** (nó chỉ ghép chuỗi, không cần dữ liệu).

### Nhân bản (việc 4) — "Tạo giống quy tắc này"

Mỗi dòng trong bảng quy tắc có nút **Tạo giống**. Nó **CHỈ điền form**, không
thêm thẳng: chép `loai` + toàn bộ `noi_dung` xuống form, đặt `ghi_chu` thành
câu cũ **+ " — bản sao"**, rồi đưa con trỏ về **cuối câu** — đúng chỗ cần sửa.
(`select()` bôi đen cả câu thì gõ một phím là mất sạch phần vừa chép.)

`veTruong(nguon)` nhận nguồn giá trị điền sẵn; bỏ trống thì lấy `VI_DU` của
loại. **MỘT hàm vẽ, không phải hai** — hai bản vẽ là hai bản sẽ lệch, đúng bài
học `khop_loc()` / `_cum_cua()`.

> **`them_quy_tac()` CHẶN khi `ghi_chu` trùng (sau `.strip()`) — đã ĐO, không
> suy.** Nhân bản y nguyên một quy tắc **MỀM** rồi chấm điểm: `cham_diem()`
> ghi `ct[q.ghi_chu] = x`, hai quy tắc cùng khoá thì cái sau **ĐÈ** cái trước.
> Đo được **4 quy tắc mềm ra 3 dòng** trong bảng "Kiểm tra quy tắc" trên Excel,
> trong khi tổng điểm **vẫn cộng đủ cả hai**. Mất một dòng, không một chữ báo.
>
> Quy tắc **CỨNG** thì `hau_kiem()` gom vào **list** nên không mất dòng — nhưng
> hai dòng chữ y hệt nhau trong bảng đối chiếu cũng không ai đọc nổi. Chặn cả
> hai cho một luật, và câu từ chối nhắc lại **số thứ tự** quy tắc bị trùng,
> **hậu quả**, và **cách chữa**.
>
> Hậu tố `" — bản sao"` vì vậy là **điểm khởi đầu để sửa**, không phải câu dùng
> luôn: bấm Thêm ngay mà không sửa thì vẫn qua, nhưng bấm Thêm hai lần liên
> tiếp thì bị chặn.

### Màn hình Quy tắc — bốn phần giao diện (ĐÃ LÀM 21/8)

| Phần | Làm gì | Chỗ ca thử KHÔNG canh được |
|---|---|---|
| 1 | **Thẻ** thay bảng dài, gom theo `NHOM_LOAI` | Chữ có tràn khung không; lưới nhiều cột có so le khó nhìn không |
| 2 | **Tìm + lọc** theo GV / môn / lớp / nhóm | Thanh lọc trên điện thoại có chật không |
| 3 | **Huy hiệu** Bắt buộc/Ưu tiên, dòng phạm vi, **Sửa**/Tạo giống/Xoá | Ba nút cùng hàng trên điện thoại; ba màu huy hiệu có phân biệt được không |
| 4 | **Bốn trạng thái** tải · rỗng · lỗi · xong, và **bàn phím** | Viền lấy nét có thấy rõ trên nền thẻ không |

> **`CA 6` và `CA 11` đọc CSS và mã nguồn, KHÔNG dựng trình duyệt.** Chúng bắt
> được việc khai sai cỡ và việc **bỏ hẳn** một nhánh; chúng **không** bắt được
> lỗi bố cục. Bốn dòng cuối bảng trên là việc phải mở trình duyệt xem bằng mắt.

**Nút "Sửa" CHỈ có ở quy tắc NHÁP — ràng buộc thật, không phải chưa làm tới.**
`luu_quy_tac()` ghi cờ bật/tắt cộng danh sách nháp; nó **không** ghi được thân
một quy tắc đã có trong `cauhinh.json`. Cho nút Sửa hiện ở đó là hứa một việc
không làm được: thầy cô sửa, bấm Lưu, mở tệp ra thấy y như cũ. Quy tắc trong
file có **Tạo giống + công tắc**, đúng cơ chế máy chủ làm được.

**Sửa = XOÁ nháp rồi ĐIỀN form, đúng thứ tự đó.** Điền trước mà xoá hỏng thì
bấm Thêm sẽ đụng cửa chặn trùng câu `ghi_chu`, và câu từ chối ấy nói về một
chuyện khác hẳn.

> **Lỗ đã bịt ở phần 4:** `napQuyTac()` từng viết `if (!d) return;` — máy chủ
> 500 hoặc câu trả lời không phải JSON thì màn hình **đứng im với danh sách cũ,
> không một chữ nào**. Cùng hạng lỗi im lặng cả dự án này chống, chỉ khác là nó
> nằm ở giao diện. Nay có **hai** nhánh lỗi (mạng hỏng ≠ câu trả lời hỏng, hai
> câu khác nhau) và một nút **Thử lại** nằm SẴN trong HTML.

> **Bàn phím: chỉ Esc trong ô Tìm, KHÔNG chiếm phím tắt toàn trang.** `/` hay
> `Ctrl+K` là thói quen của lập trình viên; thầy cô không biết chúng tồn tại,
> mà chúng lại cướp phím của người đang gõ ở ô khác. Viền lấy nét dùng
> `:focus-visible` chứ không `:focus` trần — `:focus` trần để lại khung xanh
> sau **mỗi cú bấm chuột**, thứ ai cũng tưởng là lỗi hiển thị. CA 11 canh cả hai.

### VIẾT THÀNH HÀM RỜI — Đợt 4 cắm vào đây, đừng bắt nó viết lại

Đợt 4 (chatbox) chia làm **ba lớp độc lập**, và **hai trong ba lớp đó chính là
Đợt 3**:

| Lớp của Đợt 4 | Ai làm | Ở đâu |
|---|---|---|
| Bộ **phân tích**: câu tiếng Việt → bản nháp | Đợt 4 | mới |
| Bộ **kiểm tra**: bản nháp → hợp lệ hay không | **Đợt 3 việc 2** | dùng lại y nguyên |
| Bộ **hiển thị**: bản nháp → câu đọc lại | **Đợt 3 việc 1** | dùng lại y nguyên |

> **Vì vậy Đợt 3 PHẢI viết hai thứ đó thành HÀM RỜI nhận MỘT DICT QUY TẮC**,
> không gắn vào form, không đọc gì từ `request`:
> ```
> cau_doc_lai(r)         -> str        (việc 1)
> pham_vi_quy_tac(r, bt) -> dict       (việc 2)
> canh_bao_pham_vi(pv)   -> str|None   (việc 2)
> ```
> Gắn vào form thì Đợt 4 buộc phải chép bản thứ hai — đúng kiểu lệch đã trả giá
> ở `khop_loc()` / `_cum_cua()`. Đây là ràng buộc kiến trúc, không phải gợi ý.

### Ba ràng buộc phải giữ

1. **KHÔNG thay `ghi_chu` bằng câu sinh ra, kể cả khi người dùng bấm đồng ý.**
   `cham_diem()` dùng `ghi_chu` của quy tắc **MỀM** làm khoá dict, và khoá đó
   chảy thẳng vào ô Excel (gốc của A8). Câu sinh ra chỉ **hiện song song**.
   Nếu Đợt sau muốn có nút "dùng câu này" thì phải kèm phép chống trùng khoá
   và một ca thử riêng — Đợt 3 cố ý **không làm**.
2. **Câu đọc lại sinh ở MÁY CHỦ**, không chép ngữ nghĩa sang JS. Cùng lý do
   `TRUONG` phục vụ cả `--quy-tac` lẫn form web: chép sang JS là chắc chắn lệch.
3. **Phạm vi ra 0 lớp thì CẢNH BÁO, không CHẶN.** Quy tắc không khớp gì là
   "không cấm gì mà vẫn báo ĐẠT" — đúng bẫy `n_uyen == 0`, lần này ở phía người
   dùng. Nhưng chặn hẳn thì có lúc chặn oan (học kỳ này lớp đó chưa có môn ấy).

---

## Đợt 4 — chatbox tạo quy tắc (THIẾT KẾ, **CHƯA DUYỆT**)

Chạy **hoàn toàn bằng luật viết tay tại chỗ**. **KHÔNG gọi AI ở đợt này.**
Chỉ để sẵn chỗ cắm.

### Hợp đồng: BẢN NHÁP

Ba lớp chỉ trao đổi với nhau qua đúng một cấu trúc. Đây là hợp đồng, đổi nó là
đổi cả ba:

```python
BanNhap = {
    'quy_tac':  dict | None,   # ĐÚNG hình dạng một quy tắc trong cauhinh.json
    'do_tin':   'chac' | 'doan' | 'khong_hieu',
    'thieu':    [{'khoa': str, 'cau_hoi': str, 'chon': [...]}],
    'nguon':    'luat' | 'api',
    'vi_sao':   str,           # vì sao bộ phân tích hiểu như vậy
}
```

Ba bất biến của hợp đồng:
- `do_tin == 'khong_hieu'` ⇒ `quy_tac is None`. Không có chuyện "chưa hiểu
  nhưng đây là quy tắc tôi đoán".
- `thieu` khác rỗng ⇒ **không được thêm vào danh sách**, phải hỏi cho xong.
- `quy_tac` đi qua **đúng** `kiem_khoa_quy_tac()` như một quy tắc gõ tay. Khoá
  lạ thì DỪNG — không có cửa riêng cho chatbox.

> `quy_tac` **cố ý** dùng y nguyên hình dạng của `cauhinh.json`, không phải một
> hình dạng trung gian riêng. Nhờ vậy bộ kiểm tra và bộ hiển thị của Đợt 3 nhận
> nó mà không cần biết nó từ đâu tới — và khi nối API sau này, **chỉ lớp phân
> tích đổi**.

### ĐƯỜNG ĐI BẮT BUỘC — hai lần bấm người, hai cửa khác nhau

```
câu người gõ
  -> POST /api/hieu-cau       (chỉ ĐỌC; không ghi tệp, không đụng nháp phiên)
  -> bản nháp + độ tin cậy + câu đọc lại + phạm vi
  -> NGƯỜI BẤM "Thêm vào danh sách"
  -> POST /api/them-quy-tac   (nháp CỦA PHIÊN, chỉ trong bộ nhớ — 2A-2a)
  -> NGƯỜI BẤM "Lưu vào cauhinh.json"
  -> POST /api/luu-quy-tac    (đòi DẤU BẢN — 2C)
```

> **KHÔNG dựng cơ chế "chờ xác nhận" mới.** Nháp theo phiên của 2A-2a ĐÃ LÀ
> trạng thái chưa xác nhận, và nút Lưu của 2C đã là cửa thứ hai. Chatbox chỉ
> được đứng ở **đầu** dây chuyền đó, không được rẽ tắt.

**Ca thử ghim, hai tầng:**
1. **Cấu trúc** — soi cây cú pháp mô-đun bộ phân tích: không được nhắc tới
   `luu_quy_tac`, `_gon_json`, `os.replace`, hay `open(..., 'w')`. Bắt LỚP lỗi,
   không bắt một lần lỗi — cùng kiểu `thu_ghim_du_lieu.py`.
2. **Hành vi** — gửi một câu qua `/api/hieu-cau` rồi khẳng định `cauhinh.json`
   **không đổi một byte** (so md5) **và** `so_moi` của phiên **vẫn bằng 0**.
   Mục thứ hai mới là mục thật; mục thứ nhất chỉ chặn trước.

### Bộ KIỂM TRA chạy trên MỌI bản nháp, không phân biệt nguồn

Luật viết tay hay API đều qua đúng một cửa `kiem_ban_nhap()`. Bảy phép kiểm,
và **bảng dưới nói cái nào đã có sẵn** — đọc bảng, đừng đếm lại:

| # | Kiểm | Có sẵn? |
|---|---|---|
| 1 | `loai` có trong `DANH_MUC` không | có (`kiem_khoa_quy_tac`) |
| 2 | Khoá lạ / `tru` rỗng / sai kiểu | có (`kiem_bo_loc`) |
| 3 | Miền `thu` / `tiet` / `o` | có (`_kiem_thu`, `_kiem_tiet`, `_kiem_o`) |
| 4 | Có cụm nào bị chặn hết mọi ô | có (`_kiem_tra_so_bo`) |
| 5 | Còn xếp được không (1 lần thử / 1 giây) | có (cảnh báo sớm 2C) |
| 6 | **Tên GV / lớp / môn có THẬT không** | **đã có** (`pham_vi_quy_tac`, Đợt 3 việc 2) |
| 7 | **Trùng câu `ghi_chu` với quy tắc đã có không** | **đã có** (`them_quy_tac`, Đợt 3 việc 4) |

Phép 6 quan trọng hơn vẻ ngoài: nó bắt đúng cái bẫy `n_uyen == 0` ở phía người
dùng — bộ lọc gõ sai tên thì khớp 0 cụm, **không cấm gì cả mà vẫn báo ĐẠT**.

### Bộ phân tích KHÔNG ĐƯỢC ĐOÁN

- **Thực thể nhận bằng TRA BẢNG, không bằng suy đoán.** Tên lớp / môn / GV chỉ
  được nhận khi khớp nguyên văn với dữ liệu thật (sau khi hạ hoa-thường). Không
  có "gần giống", không có sửa lỗi chính tả.
- **Dải KHÔNG tự mở.** *"12B3 đến 12B6"* sinh một mục `thieu` kèm `chon` =
  `[12B3, 12B4, 12B5, 12B6]` để người bấm xác nhận — không tự điền.
- **Hai nhóm luật cùng khớp → `doan`, liệt kê CẢ HAI**, không chọn hộ.
- **Không nhóm nào khớp → `khong_hieu`**, chỉ sang form nhập tay.
  **TUYỆT ĐỐI không chọn một loại "gần đúng"** — đó chính là lỗi QT 14/15/16 ở
  dạng tự động, và ở dạng đó nó xảy ra hàng ngày chứ không phải một lần.

### Độ tin cậy phải HIỆN RA

| `do_tin` | Câu mở đầu | Màu |
|---|---|---|
| `chac` | **"Tôi hiểu là:"** | xanh |
| `doan` | **"Tôi đoán là … nhưng chưa chắc, kiểm lại giúp:"** + `vi_sao` | vàng |
| `khong_hieu` | **"Tôi chưa hiểu câu này."** + nút mở form | xám |

Nhánh `doan` **bắt buộc** hiện `vi_sao` (từ khoá nào đã khớp). Không nói được
vì sao thì không được phép nói "tôi đoán".

### Chỗ cắm cho API — để chỗ, KHÔNG viết mã gọi

```python
def hieu(cau, bt) -> BanNhap: ...      # interface, một hàm
```
Hai cài đặt: `hieu_theo_luat()` (Đợt 4) và `hieu_theo_api()` (**chưa viết**).
Chọn bằng `cauhinh_may_chu.json` — **không** phải `cauhinh.json`, cùng lẽ với
danh sách tên máy: đây là cấu hình của MỘT máy, không phải dữ liệu nhà trường,
và nó đã `.gitignore`.

```json
{ "hieu_cau_bang_ai": false }
```

> **Mặc định TẮT, và fail-closed theo hướng NGƯỢC với thói quen.** Khoá thiếu
> hoặc hỏng → dùng luật viết tay. Nhưng khoá **bật** mà chưa có cài đặt API →
> **DỪNG kèm câu rõ**, tuyệt đối không âm thầm rơi về luật viết tay: người quản
> trị sẽ tưởng AI đang chạy trong khi không. Im lặng rơi về là đúng hạng lỗi cả
> dự án này viết ra để chống.

### Giá phải trả: một đường dẫn mới

`POST /api/hieu-cau` đưa tổng số đường từ **19 lên 20**. Kèm theo bắt buộc:
cập nhật **bảng đường dẫn nguồn-duy-nhất**, thêm vào `ca_a1c_moi_duong_deu_bi_gac`,
và đường này **cần phiên + cần xác thực** — nó đọc tên 28 giáo viên và tên lớp
của trường.

---

## Đợt 2 — chín quyết định đã duyệt (20/8/2026), **ĐÓNG 21/8/2026**

> **Đóng vì có SỐ ĐO, không phải vì thấy đủ.** Hai mục cuối — `5d` dịch vụ tự
> lên cùng máy, `5e` `tailscale serve` tự sống lại — đã đo trên máy thật ngày
> 21/8/2026. Bốn dòng số ở mục "Đường vào từ ngoài" bên trên; công thức lặp lại
> được ở `CHAY_CUNG_MAY.md` mục 7.

| # | Quyết định |
|---|---|
| 1 | Hạn phiên: **nghỉ 8 giờ, tuyệt đối 12 giờ**. Ô đăng nhập là lớp phủ, việc đang dở tự chạy lại |
| 2 | Đóng trình duyệt → phải đăng nhập lại (cookie kiểu phiên, không `Max-Age`) |
| 3 | Tắt tài khoản có hiệu lực **ngay**, phiên đang mở của người đó chết theo |
| 4 | Kết quả xếp dùng chung, **dán tên** người xếp **và có DẤU BẢN riêng** — xem dưới |
| 5 | Mật khẩu tối thiểu **12 ký tự**, không đòi chữ hoa / ký tự lạ |
| 6 | Khoá tạm **10 lần sai → 15 phút** (duyệt nâng từ 5 — xem mục 2B), đếm theo tài khoản, cửa sổ quên 30 phút |
| 7 | Chống mất bản sửa: dấu bản + 409 + "Tải lại danh sách", **và** tách nháp theo phiên |
| 8 | Thứ tự: 2A-2a hạ tầng phiên → 2A-1 đăng nhập → 2A-3 di trú → 2A-4 giao diện → 2A-5 ca thử → 2B chống dò → 2C chống mất bản sửa |
| 9 | Cookie **`SameSite=Lax`**, không phải `Strict` — xem dưới |

### QĐ 4 — kết quả xếp cũng cần dấu bản, không chỉ dán tên

Dấu bản của QĐ 7 canh `cauhinh.json`, **không** canh kết quả xếp. Lỗ còn lại:
cô B bấm Xếp đè kết quả thầy A đang mở; A bấm Tải về và nhận tệp của B mà không
biết. Cùng một lỗi, khác tầng.

- Mỗi lượt xếp xong sinh một dấu mới (`secrets.token_hex(8)`), trả kèm
  `/api/trang-thai`.
- `/api/tai-ve` và `/api/tai-web` nhận `?dau=…`; lệch thì **chặn** kèm câu
  *"Kết quả đã bị thay bởi lượt xếp của <tên>, xem lại trước khi tải."*
- **Dán tên để BIẾT, dấu bản để CHẶN — cần cả hai.**
- Ngoại lệ có chủ ý: máy chủ vừa khởi động lại thì chưa có dấu nào, mà tệp hôm
  qua vẫn nằm trên đĩa. Lúc đó **cho tải**, kèm ghi chú tệp thuộc lượt chạy
  trước. Từ chối lúc này là từ chối oan — đúng cái bẫy đã bác một lần.

### QĐ 9 — vì sao `Lax` chứ không `Strict`

Đã thử tìm một kịch bản tấn công mà `Lax` + kiểm `Origin` + mọi đường ghi là
POST vẫn thủng. **Không tìm được**, và có một lý do khiến `Strict` còn kém hấp
dẫn hơn nữa:

> Mối đe doạ đáng lo nhất ở đây là **một máy khác trong tailnet**
> (`other.tail7dc28e.ts.net`). Máy đó **same-site** với máy quản trị vì cùng tên
> đăng ký `tail7dc28e.ts.net`. `SameSite` — dù `Lax` hay `Strict` — **không chặn
> nó**. Đối với đúng mối đe doạ đó, `Strict` mua được con số không. Cái chặn nó
> là kiểm `Origin` và tiền tố `__Host-`.

Bốn hướng đã rà: không đường GET nào đổi trạng thái · không nhận
`X-HTTP-Method-Override` · điều hướng cấp cao nhất không mang `Origin` nhưng lúc
đó cookie chỉ đi với GET · và:

> **Phải khai `SameSite=Lax` TƯỜNG MINH.** Chrome có ngoại lệ "Lax+POST 2 phút"
> cho phép POST cross-site cấp cao nhất mang cookie — nhưng ngoại lệ đó **chỉ áp
> cho cookie KHÔNG khai SameSite**. Bỏ trống không giống khai `Lax`.

Đổi lại: giáo viên gửi link cho nhau qua Zalo là cách làm việc thật, và `Strict`
làm **mọi** lần bấm link đều văng về ô mật khẩu — ghi vào tài liệu không chữa
được, chỉ giải thích cho một phiền toái hằng ngày.

---

## Phiên trình duyệt (2A-2a) — chưa có xác thực

Phiên ở bước này trả lời đúng **một** câu: *bản nháp quy tắc này là của trình
duyệt nào*. Chưa có mật khẩu, chưa có tên người. Đăng nhập (2A-1) lắp lên đúng
hạ tầng này, không dựng lại.

> **Lỗi đã bịt, đo được trước khi sửa.** Thầy A thêm một quy tắc nháp (chưa Lưu),
> cô B bấm Lưu → tệp đi từ **13 lên 14** quy tắc: quy tắc **chưa ai duyệt** của A
> vào thẳng `cauhinh.json`, còn A vẫn thấy nháp của mình là "chưa lưu". Im lặng
> cả hai chiều. Không cần tới hai người — mở phần mềm trên máy bàn và trên điện
> thoại đã là hai trình duyệt khác nhau.
>
> **Dấu bản của `cauhinh.json` KHÔNG bắt được lỗi này** — lúc B tải danh sách về
> thì tệp trên đĩa chưa hề đổi, dấu bản khớp hoàn hảo. Lỗ ở **bộ nhớ**, không
> phải ở **tệp**, nên phải chữa bằng cách tách theo phiên.

| Thứ | Cách làm |
|---|---|
| Mã phiên | `secrets.token_urlsafe(32)`, sinh **ở máy chủ**, không bao giờ nhận nuôi mã khách gửi lên (chống cố định phiên, đúng ngay từ bước chưa có mật khẩu) |
| Cất | `CAC_PHIEN` + `PHIEN_THEM`, khoá riêng `KHOA_PHIEN` |
| Hết hạn | Nghỉ 8 giờ / tuyệt đối 12 giờ, theo **hai đồng hồ** — `monotonic` không đếm lúc máy ngủ, `time()` nhảy khi NTP chỉnh. Hết theo cái nào tới trước |
| Trần | 32 phiên; đầy thì **đuổi cái ngồi không lâu nhất**, không bao giờ từ chối người mới |
| Dọn | Lười, ngay trong lúc tra sổ. Không luồng nền |

### Hai tên cookie — và vì sao chỉ được đọc MỘT

```
Host loopback  ->  phien_tkb          ; Path=/; HttpOnly; SameSite=Lax
Host khác      ->  __Host-phien_tkb   ; Path=/; HttpOnly; SameSite=Lax; Secure
```

Cờ `Secure` **suy từ `Host`**, không phải một khoá cấu hình. Mọi giá trị mặc định
của một khoá như vậy đều có trạng thái hỏng **trong im lặng**: đăng nhập trả 200,
trình duyệt vứt cookie, yêu cầu kế 401, quay lại ô mật khẩu, không một chữ giải
thích. Tin được vì `Host` đã qua danh sách trắng A1 **ngay trước đó**.

> **Chỉ đọc ĐÚNG MỘT tên, tên ứng với chế độ hiện tại.** Viết "thử `__Host-`
> trước, không có thì thử tên trơn" là tự mở lại đúng lỗ vừa bịt — kẻ kia chỉ cần
> đặt tên trơn là được đọc. Có ca thử riêng cho điều này.

> **`SameSite=Lax` phải khai TƯỜNG MINH.** Chrome có ngoại lệ "Lax+POST 2 phút"
> cho phép POST cross-site cấp cao nhất mang cookie, và ngoại lệ đó **chỉ áp cho
> cookie KHÔNG khai SameSite**. Bỏ trống không giống khai `Lax`.

### `_don_phien_da_khoa()` — vì sao tách khỏi bản tự khoá

`threading.Lock` **không tái nhập**. Một hàm đã giữ `KHOA_PHIEN` mà gọi sang hàm
tự khoá là **treo cứng máy chủ** ngay phiên hết hạn đầu tiên. Đừng chữa bằng
`RLock` — nó giấu mất chỗ nào đang giữ khoá bao lâu.

> **Đã lùi đúng lỗi này để thử, và phát hiện một lỗ trong chính bộ thử:** nó
> **TREO** chứ không đỏ (`MayChuTam.__exit__` gọi `may.shutdown()`, mà hàm đó chờ
> mãi một luồng đang kẹt trong khoá). Treo còn tệ hơn vỡ vì nó chặn luôn mọi bộ
> thử chạy sau. Đã thêm **đồng hồ canh 180 giây** vào `thu_phien.py` để mọi
> deadlock tương lai thành một dòng đỏ — đo lại: 4/6 mục, thoát 1.

---

## Cổng đăng nhập (2A-1)

**Từ đây, vào được tailnet KHÔNG còn đủ để ghi `cauhinh.json`.**

| Thứ | Cách làm |
|---|---|
| Tài khoản | `tai_khoan.json` — **một DÃY**, mỗi người một bản ghi. Thêm người là chạy lại script, không sửa mã |
| Băm | `scrypt` **đúng một bộ tham số** `{n=16384, r=8, p=1, dklen=32}`, `maxmem` tường minh. Muối 16 byte **riêng từng người**. So bằng `hmac.compare_digest` |
| Thiếu/hỏng/rỗng/sai kiểu | Máy chủ **TỪ CHỐI KHỞI ĐỘNG**, và chưa hề in dòng "Mở trình duyệt vào" |
| Sổ rỗng lúc chạy | **503** ("chưa cài xong"), không phải 401 ("chưa đăng nhập") |
| Tắt một tài khoản | Có hiệu lực **ngay**, phiên đang mở của người đó chết theo (QĐ 3) |

### QĐ 3 "có hiệu lực NGAY" — đọc lại theo TỆP

`nap_tai_khoan_may_chu()` từng **chỉ được gọi một lần trong `main()`**, nên
ngoài đời QĐ 3 **sai suốt**: `python3 tao_mat_khau.py tat <tên>` không có tác
dụng gì cho tới khi chạy lại `web.py`. Ca thử vẫn xanh vì nó **gọi tay hàm
nạp** ngay trước khi khẳng định — nó chứng minh HỆ QUẢ (phiên chết) mà bỏ qua
CÁI CÒ. Đó là kiểu hỏng số 6 trong bảng kỷ luật.

`tuoi_tai_khoan()` soi dấu tệp `(st_ino, st_mtime_ns, st_size)` ở **đầu
`doc_phien()`** — cùng chỗ với phép kiểm QĐ 3 đã có, để hai thứ đi liền một
mạch. Đo trên **chính ổ ntfs3 của dự án** (MÁY A; đo lại 22/8: 0,84 µs): `os.replace()` đổi `st_ino` mỗi lần
ghi, 5 lần ghi liên tiếp cho 5 mốc `mtime` phân biệt, `os.stat` tốn **0,78 µs**
— rẻ hơn bốn bậc so với một lượt scrypt.

> **Đọc lại KHÔNG được thì GIỮ SỔ CŨ, ngược với lúc khởi động — và có lý do.**
> Lúc khởi động chưa có sổ nào để giữ nên từ chối chạy là đúng. Đang chạy mà
> tệp hỏng thì đó là **sự cố mới** (đĩa lỗi, ai đó sửa tay), không phải một
> quyết định về quyền. Đổ sổ về rỗng lúc đó là cho cả khoa nghỉ việc giữa buổi
> vì một byte lỗi; giữ sổ cũ thì **không ai được thêm quyền nào**.
> Hệ quả phải biết: tệp hỏng thì lệnh `tat` chưa có hiệu lực — đúng, tệp hỏng
> không phải một lệnh tắt.

Kêu **một lần cho mỗi dấu tệp**, không kêu lại mỗi yêu cầu: trang hỏi trạng
thái mỗi 0,7 giây, kêu mỗi lần là 1,4 dòng/giây ngập cửa sổ dòng lệnh.

Ca thử `thu_dang_nhap.py` CA 7b chạy hẳn `tao_mat_khau.py` bằng **tiến trình
con** rồi chỉ quan sát qua HTTP — không một lời gọi hàm nạp nào. Hai lời gọi
tay cũ ở CA 2 và CA 7 đã bỏ; giờ chúng cũng đỏ nếu lùi bản vá.

### Xoay mã phiên — chống cố định phiên

Phiên vô danh **KHÔNG BAO GIỜ** được nâng cấp tại chỗ thành phiên đã đăng nhập.
Đăng nhập thành công thì **huỷ hẳn mã cũ** và **sinh mã mới**.

> Vì sao không dựa vào tiền tố `__Host-` để miễn việc này, dù nó đã chặn được
> đường gieo cookie: như vậy là đặt an ninh của mình vào một tính năng của trình
> duyệt thay vì vào mã của mình. Xoay mã tốn ba dòng.

**Nháp thì CHUYỂN sang mã mới, không bỏ.** Thứ kẻ tấn công cần là mã *sau* khi
đăng nhập; mã đã xoay thì hắn không có, và nháp chuyển hay không không đụng tới
tính chất đó. Phiên vô danh vốn **không thể** có nháp (mọi đường tạo nháp đều
đòi xác thực), nên lần đăng nhập đầu chuyển một danh sách rỗng.

> **Nháp sống và chết cùng phiên**, trừ đúng lúc xoay mã. Hết hạn hoặc đăng xuất
> là nháp mất. Giữ nháp sống lâu hơn phiên nghĩa là giữ một bản ghi tồn tại
> ngoài phiên — đúng loại trạng thái làm việc suy luận về cố định phiên trở nên
> khó. (Bản thiết kế ban đầu ghi "hết hạn thì nháp giữ nguyên"; mã làm ngược
> lại, và đây là quyết định giữ theo mã.)

### Một lần scrypt ở MỌI nhánh

Tên có thật · tên không tồn tại · tên sai cú pháp · tên rỗng — **tất cả** đều
chạy đúng một lần `scrypt`, dùng bản ghi giả khi cần. Thoát sớm ở bất kỳ nhánh
nào là mở một kênh đo thời gian để dò xem tài khoản nào có thật.

> **Ca thử đếm SỐ LỜI GỌI, không đo đồng hồ.** Đếm là bằng chứng xác định; đo
> thời gian phụ thuộc tải máy và sẽ chớp đỏ ngẫu nhiên trên máy của trường. Kèm
> một mục canh riêng: `bam()` phải thật sự đắt (≥ 8 ms) — mục đó bắt lỗi "thay
> scrypt bằng hàm băm rẻ tiền", thứ mà phép so bằng-nhau không bao giờ thấy.

`KHOA_BAM = Semaphore(2)`: `scrypt` cấp phát 16 MB và **nhả GIL**, nên nhiều lời
gọi chạy song song thật — đã đo 32 lần cùng lúc đẩy tiến trình lên 537 MB (MÁY A).
`/api/dang-nhap` là đường **chưa xác thực** duy nhất tốn kém như vậy.

---

## Chống dò mật khẩu (2B) — khoá tạm theo tài khoản

QĐ 6: sai **10 lần** → khoá **15 phút**, đếm theo **TÀI KHOẢN**, cửa sổ quên
**30 phút**. Đếm theo tài khoản chứ không theo IP là bắt buộc chứ không phải lựa
chọn: sau Tailscale Serve **mọi** yêu cầu đều mang `127.0.0.1`, nên đếm theo IP
là đếm tất cả mọi người vào chung một ô.

Ba hằng số ở `tai_khoan.py`: `SO_LAN_SAI_TOI_DA` / `GIAY_KHOA` / `GIAY_QUEN`.
Đổi ngưỡng là đổi **một dòng**, và `tests/thu_chong_do.py` đọc thẳng ba hằng đó
nên không phải sửa ca thử theo — đã thử: nâng 5 → 10 thì bộ thử tự chạy theo,
bộ thử tự chạy theo, không phải sửa ca thử.
(Trước đây chỗ này ghi `55/55` còn mục "Trạng thái" ghi `58/58` — hai con số
cho cùng một bộ thử, chép ở hai thời điểm. Nay không chép số nữa.)

### Sổ khoá tạm nằm trong TỆP, và đó là lý do chính

`khoa_dang_nhap.json` nằm cạnh `tai_khoan.json`, đường dẫn **suy ra** từ nó
(`TK.duong_dan_khoa()`) chứ không khai riêng — khai riêng thì `--tai-khoan` của
ca thử sẽ trỏ một nơi còn sổ trỏ nơi khác, và kết quả ca thử phụ thuộc **thứ tự
chạy**.

> **Vì sao không để trong RAM của `web.py`** — vì `mo-khoa` là **tiến trình
> khác**. Cả khoa dùng chung MỘT tài khoản, nên một người quên mật khẩu là khoá
> cả khoa; cửa thoát hiểm tại máy không phải thứ xa xỉ. Trạng thái nằm trong RAM
> thì `tao_mat_khau.py` không có đường nào chạm tới. Đã đo: đem sổ vào RAM thì
> `thu_chong_do.py` tụt còn **39/52**.

Kèm theo, miễn phí: **khởi động lại `web.py` không phải là đường lách khoá.**
`CAC_PHIEN` ở RAM nên mất, sổ khoá thì không — có ca thử riêng.

| Tình huống | Xử lý |
|---|---|
| Không có tệp | Chưa ai bị khoá, **im lặng** — đây là trạng thái thường |
| Tệp hỏng / sai kiểu | Chưa ai bị khoá, **kêu to**; lần gõ sai kế tiếp ghi lại sổ mới |
| Ghi không được | Kêu to, lượt đăng nhập vẫn chạy tiếp |

> **FAIL-OPEN, ngược hẳn `nap()` ngay bên trên — và đây là lý do.** Chiều kia
> ("sổ hỏng thì coi như khoá hết") biến một byte lỗi thành cảnh **cả khoa bị
> nhốt ở ngoài**, mà cách chữa duy nhất là ra tận máy. Khoá tạm là lớp phòng thủ
> **THÊM**; lớp chính là chính mật khẩu, và nó còn nguyên khi sổ hỏng. Kẻ tấn
> công cũng không gây được hỏng: chỉ `web.py` ghi tệp này, ghi nguyên tử.

Sổ **không chứa bí mật nào** — tên tài khoản (đã có trong `tai_khoan.json`), một
bộ đếm, hai mốc thời gian. Vẫn để quyền 600 và **đã gitignore**: nó là trạng
thái CHẠY của đúng một máy. **Không có bản `.mau`** — khác `tai_khoan.json`,
không ai tạo tệp này bằng tay.

Ghi **không `fsync`** (khác `tai_khoan.json`): nội dung vứt đi được, mà nó lại bị
ghi ở đường **chưa xác thực** — không đáng để một người gõ sai mật khẩu ép được
máy chủ `fsync`. `_ghi_nguyen_tu(..., ben=)` là một bản cài cho cả hai.

### Đồng hồ TREO TƯỜNG, không phải monotonic

Ngược hẳn phiên trình duyệt (dùng **cả hai** đồng hồ). Lý do: `monotonic` của
tiến trình này vô nghĩa với tiến trình kia, mà cả điểm của sổ là hai tiến trình
cùng đọc. Giá phải trả là đồng hồ nhảy, nên `_kep_khoa_den()` kẹp mốc hết khoá
không quá `GIAY_KHOA` — chặn đúng chiều nguy hiểm (nhảy **lùi** làm khoá dài vô
hạn). Chiều kia chỉ mất một phần của 15 phút, không đáng đổi lấy thêm cơ chế.

### Ba chỗ dễ sai, đã xử — và ca thử canh từng chỗ

1. **Nhánh bị khoá VẪN chạy đủ một lượt `scrypt`.** Phép kiểm nằm **SAU**
   `TK.bam()`, không phải trước. Chặn trước cho "đỡ tốn CPU" là đổi 27 ms (MÁY A) lấy
   một kênh đo: gõ bậy cho đủ ngưỡng rồi xem lần kế tiếp trả lời nhanh hay
   chậm là biết
   tài khoản có thật hay không. **Hệ quả phải chấp nhận: khoá tạm KHÔNG giảm
   được chút tải CPU nào** — nó chống dò mật khẩu, không chống làm nghẽn máy
   chủ. Đừng trông cậy nhầm. Lùi ra: **46/51**.
2. **KIỂM và TĂNG trong CÙNG một lần giữ khoá** (`TK.ghi_nhan_thu()`). Tách ra
   hai lần giữ khoá thì một loạt bắn dồn lọt hết, vì mọi yêu cầu đều đọc bộ đếm
   xong mới xếp hàng ở `KHOA_BAM` — đúng lỗi A4 mà `gianh_luot()` đã giải. Đo
   được: bỏ chốt chặn thì 40 yêu cầu bắn cùng lúc **lọt 8 thay vì đúng 5**.
3. **Đang khoá thì mật khẩu ĐÚNG cũng không vào.** Cho vào là bỏ hẳn tác dụng
   của khoá: kẻ dò cứ đoán tiếp trong lúc bị khoá, tới lúc trúng thì vào.

Thêm hai luật nhỏ nhưng phải giữ: **đăng nhập đúng xoá sạch bộ đếm** (bốn lần lỡ
tay rải rác trong ngày không được cộng dồn thành khoá oan), và **gõ thêm lúc
đang khoá KHÔNG dời mốc hết khoá** (dời mốc là trao cho kẻ dò cái nút nhốt cả
khoa ở ngoài vĩnh viễn).

### Chỉ đếm tài khoản CÓ THẬT — và cái giá của việc đó

Tên không tồn tại / sai cú pháp / rỗng **không bao giờ vào sổ**. Hai lý do:

- `/api/dang-nhap` là đường **chưa xác thực**, nên nếu đếm cả tên bịa thì kích
  thước sổ do khách điều khiển — mười triệu tên bịa là mười triệu mục.
- Bản nào "cũng đếm tên bịa cho công bằng" đều phải kèm **trần + phép đuổi**, mà
  phép đuổi ấy **CHÍNH LÀ đường lách khoá**: bắn đủ tên bịa cho tràn sổ là đẩy
  mục thật ra ngoài, bộ đếm về 0.

> **Đánh đổi có chủ ý, đã ghi thành một mục ca thử riêng:** ai chịu gõ sai đủ 5
> lần thì phân biệt được tên có thật (429) với tên bịa (401). Với **một** tài
> khoản dùng chung mang tên khoa thì đó không phải bí mật. Đổi lại là một câu
> báo dùng được cho thầy cô — và một cái khoá không lách được.
>
> Cái giá phụ: nhánh tên-có-thật ghi tệp (~1 ms) còn nhánh tên-bịa thì không.
> So với 27 ms của `scrypt` thì đó là 4%. Biết, và chấp nhận — bịt nó bằng cách
> đếm cả tên bịa là mở lại đúng đường lách ở trên.

### Câu thông báo — cố ý KHÁC câu chung

Nhánh khoá trả **429** kèm câu nói rõ **còn mấy phút** và **nguyên câu lệnh gỡ
tại máy**; các nhánh sai khác vẫn giữ **401** với đúng một câu chung, giống nhau
từng byte. Người bị khoá gần như luôn là thầy cô gõ nhầm, và câu chung sẽ đẩy họ
đi thử lại thêm chục lần rồi đi đổi mật khẩu — trong khi thứ họ cần biết là
"đợi 12 phút". Số phút **làm tròn LÊN**: "còn 0 phút" là câu vô nghĩa với người
đang đợi.

### Lệnh tại máy

```bash
python3 tao_mat_khau.py mo-khoa <tên>   # gỡ khoá ngay, máy chủ nhận ra liền
python3 tao_mat_khau.py liet-ke         # cột KHOÁ TẠM: ai đang khoá, còn mấy phút
```

`doi` (đổi mật khẩu) và `xoa` cũng xoá mục trong sổ: đặt mật khẩu mới rồi mà vẫn
phải ngồi đợi hết 15 phút là vô nghĩa, và bộ đếm cũ nói về một mật khẩu không
còn tồn tại.

### Ngưỡng 10 — đã duyệt, và điều QUAN TRỌNG HƠN con số

Ngưỡng 5 của QĐ 6 đúng cho **tài khoản riêng từng người**: ai gõ sai thì người
đó chịu. Cả khoa dùng CHUNG một tài khoản thì số lần gõ sai của ba người **cộng
dồn vào một ô**. Đo (mô phỏng 200.000 ngày, 3 người, 2%/người/ngày rơi vào cảnh
nhớ nhầm mật khẩu; tốc độ dò đo trên **MÁY A**: scrypt 27,0 ms, `KHOA_BAM=2` →
69,8 lần/giây = 251.284 lần/giờ nếu không khoá):

| Ngưỡng | Khoá oan | Tốc độ dò tối đa | So với không khoá |
|---|---|---|---|
| 5 (QĐ 6 gốc) | ~7 lần/năm học | 20 lần/giờ | chậm hơn 12.564× |
| **10 (đang dùng)** | ~0,15 lần/năm | 40 lần/giờ | chậm hơn **6.282×** |
| 20 | ~0 | 80 lần/giờ | chậm hơn 3.141× |

Điểm gãy nằm giữa 5 và 10: **khoá oan giảm 48 lần, an ninh chỉ giảm 2 lần.**
Trên 10 thì khoá oan không giảm thêm mà an ninh vẫn tiếp tục giảm tuyến tính.

> **⚠ HẠN CHẾ ĐÃ BIẾT — ngưỡng chỉ quyết định TAI NẠN, KHÔNG quyết định TẤN
> CÔNG.** Ai vào được tailnet vẫn **nhốt được cả khoa ở ngoài, vô hạn**, chỉ
> bằng cách gõ sai cho đủ ngưỡng mỗi 15 phút. Nâng 5 lên 10 chỉ bắt họ gõ 10
> lần thay vì 5 — không mua được gì trước một kẻ cố ý. Gỡ khoá đòi **ra tận
> máy**, tức đúng thứ người bị nhốt từ xa không có.
>
> Đây là cái giá cố hữu của MỌI cơ chế khoá theo tài khoản, không phải lỗi cài
> đặt, và **không chữa được bằng cách chỉnh ngưỡng**. Thứ chữa được nó là
> **tài khoản riêng từng người** (mỗi người tự nhốt mình, không nhốt người
> khác) — đã ghi vào "Việc treo".
>
> Cũng vì vậy: khoá tạm **không** thay được cho một mật khẩu tử tế. Với cụm 4
> từ kiểu `khoa-co-ban-da-lat`, ngay cả bản KHÔNG khoá cũng cần hàng nghìn năm;
> khoá tạm chỉ thật sự mua được thời gian khi mật khẩu đoán được từ ngữ cảnh.

> **Đua tranh giữa hai tiến trình — biết, và cố ý không chữa thêm.** `web.py`
> ghi sổ nhiều nhất 10 lần mỗi 15 phút mỗi tài khoản (chính cái khoá tự chặn tốc
> độ ghi của nó), còn `mo-khoa` thì chạy tay. Khe trùng nhau là vài chục micro
> giây, và hậu quả xấu nhất là lệnh gỡ khoá bị đè mất — chạy lại là xong. Thêm
> một lớp khoá liên-tiến-trình cho khe đó là trả giá phức tạp cho một thứ không
> ai gặp.

---

## Bảng đường dẫn — NGUỒN DUY NHẤT

**Mọi chỗ khác trỏ về bảng này, đừng đếm lại ở nơi khác.** Con số đã trôi ba lần
(14 → 15 → 18) vì mỗi chỗ đếm một kiểu; chỗ nào cũng "gần đúng" thì lỗi trốn được.

Đếm bằng cách bắn thật vào máy chủ và xem đường nào KHÔNG trả 404 kèm câu
"Không có trang này" — không suy từ mã nguồn:

| Nhóm | Đếm bằng |
|---|---|
| Tĩnh (GET) | `/` · `/index.html` · `/web/index.html` · `/web/style.css` · `/web/app.js` — **gọi tên, không đếm** |
| API | `python3 -c "import re,io; print(len(set(re.findall(r'/api/[a-z-]+', io.open('web.py',encoding='utf-8').read()))))"` |

**Đo 22/8/2026: 14 API + 5 tĩnh = 19 đường.** Ba đường đăng nhập
(`/api/toi-la-ai`, `/api/dang-nhap`, `/api/dang-xuat`) **đã làm xong** —
Đợt 2 đóng 21/8/2026, nên bảng cũ xếp chúng vào *"sẽ thêm"* là đã cũ.

> **Chỗ đã đếm sót:** `/web/index.html` phục vụ được (200) vì `_tinh()` nhận cả
> `/web/<tệp>` cho mọi tên trong `TINH`, mà `index.html` nằm trong đó. Nó không
> phải đường giao diện dùng — giao diện vào bằng `/` — nhưng vẫn là một URL có
> thật, và trước đây cả `ca_a1c` lẫn bảng thiết kế đều bỏ quên nó.
>
> `/api/tai-ve` từng bị đếm nhầm thành "không có" khi chạy trong thư mục tạm:
> nó trả 404 với câu *"Chưa có file kết quả"* — khác hẳn câu *"Không có trang
> này"*. Phân biệt hai câu 404 đó, đừng chỉ nhìn mã.

| # | Đường | Cách | Có sẵn? | Cần **phiên** | Cần **xác thực** | Lý do |
|---|---|---|---|---|---|---|
| 1 | `/` | GET | có | không | **không** | Vỏ trang; phải mở thì mới có chỗ hiện ô mật khẩu |
| 2 | `/index.html` | GET | có | không | **không** | Cùng tệp với `/` |
| 3 | `/web/index.html` | GET | có | không | **không** | Đường sót; cùng tệp, giao diện không dùng |
| 4 | `/web/style.css` | GET | có | không | **không** | Trang đăng nhập phải tải được CSS |
| 5 | `/web/app.js` | GET | có | không | **không** | Chính nó vẽ ô đăng nhập |
| 6 | `/api/toi-la-ai` | GET | **MỚI** | không | **không** | Trả đúng một khoá `{"dang_nhap": …}`, không kèm dữ liệu. Trang gọi lúc vừa tải để biết vẽ gì |
| 7 | `/api/dang-nhap` | POST | **MỚI** | không | **không** | Gác cổng bằng chính nó thì không ai vào được |
| 8 | `/api/dang-xuat` | POST | **MỚI** | không | **không** | Hết hạn rồi vẫn phải bấm được cho sạch cookie; luỹ đẳng |
| 9 | `/api/trang-thai` | GET | có | **CÓ** | **CÓ** | Chở toàn bộ nhật ký + lưới TKB + lịch 28 giáo viên |
| 10 | `/api/quy-tac` | GET | có | **CÓ** | **CÓ** | Bộ ràng buộc nội bộ; cũng là nơi phát **dấu bản** |
| 11 | `/api/loai-quy-tac` | GET | có | **CÓ** | **CÓ** | Không chứa dữ liệu trường — vẫn gác, vì mặc-định-cấm chỉ đáng tin khi không có ngoại lệ |
| 12 | `/api/gia-tri` | GET | có | **CÓ** | **CÓ** | Danh sách 28 tên giáo viên |
| 13 | `/api/tai-ve` | GET | có | **CÓ** | **CÓ** | Cả tệp Excel. Lỗi trả `text/plain` vì mở bằng `window.location` |
| 14 | `/api/tai-web` | GET | có | **CÓ** | **CÓ** | Bản chưa qua mắt ban giám hiệu. Như trên |
| 15 | `/api/xep` | POST | có | **CÓ** | **CÓ** | 60 giây CPU, ghi đè hai tệp kết quả |
| 16 | `/api/luu-quy-tac` | POST | có | **CÓ** | **CÓ** | **Ghi đè `cauhinh.json`** — đường đắt nhất |
| 17 | `/api/them-quy-tac` | POST | có | **CÓ** | **CÓ** | Đổi bản nháp **của phiên đó** |
| 18 | `/api/xoa-quy-tac` | POST | có | **CÓ** | **CÓ** | Như trên, chiều ngược lại |
| 19 | `/api/thu-quy-tac` | POST | có | **CÓ** | **CÓ** | Giải ngay trong luồng HTTP |
| — | *mọi đường khác* | — | — | — | **CÓ** | **401 trước 404**, để không tiết lộ đường nào tồn tại |

**Hai cột khác nhau, đừng gộp.** *Cần phiên* = cần một mã phiên để biết bản nháp
là của ai (dựng ở 2A-2a, **chưa có mật khẩu**). *Cần xác thực* = phải đăng nhập
(lắp ở 2A-1). Năm đường tĩnh không cần cả hai; ba đường mới cần phiên-để-cấp chứ
không cần xác thực-để-vào.

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

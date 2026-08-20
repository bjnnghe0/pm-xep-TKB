# ĐƯA THỜI KHÓA BIỂU LÊN MẠNG

> ## ⚠ ĐỌC TRƯỚC KHI LÀM
>
> Trang này **ai có link cũng xem được** — không có mật khẩu, không giới hạn
> người xem. Người ngoài trường xem được. Google và các công cụ tìm kiếm cũng
> có thể tìm ra và lưu lại.
>
> **Những thông tin sẽ công khai, đúng và đủ:**
>
> | Thông tin | Ví dụ |
> |---|---|
> | Tên lớp | `12B1` … `12B6` |
> | **Họ tên đầy đủ của giáo viên chủ nhiệm** | `Lê Thị Anh`, `Dương Thị Ngọc Uyên` |
> | Tên viết tắt giáo viên bộ môn | `N.Uyên`, `T.Thu.Hằng` |
> | Môn học | `Toán học`, `Chuyên đề Lịch sử` |
> | Thứ và tiết của từng buổi | `Thứ 3, tiết 6` |
> | Tuần và thời điểm xuất file | `TUẦN 2 (31/8/2026-05/9/2026)` |
>
> **KHÔNG có:** số điện thoại, email, địa chỉ, ngày sinh, ảnh, tên học sinh.
>
> Họ tên đầy đủ GVCN được giữ **có chủ ý**, để giống hệt bản in treo ở trường.
>
> **Hãy hỏi ý nhà trường trước khi bật GitHub Pages.** Đây là quyết định của
> nhà trường, không phải của người chạy phần mềm. Nếu nhà trường chỉ muốn cho
> người trong trường xem thì **đừng làm PHẦN A**, hãy dùng cách ở **PHẦN C**
> (USB / thư mục chung), không cần Internet mà cũng không công khai gì.

---

# PHẦN A — LÀM MỘT LẦN DUY NHẤT

> **Phần này bạn phải tự làm**, tôi không làm thay được: mọi bước đều cần
> **tài khoản GitHub của bạn** — mở hộp thư của bạn để xác nhận, đặt mật khẩu
> của bạn, sinh mã đăng nhập gắn với tài khoản của bạn.
>
> Làm một lần rồi thôi. Từ tuần sau chỉ còn PHẦN B, mất 2 phút.

## Bước 1. Tạo tài khoản GitHub

1. Mở trình duyệt, vào **github.com**
2. Bấm **Sign up** ở góc trên bên phải
3. Nhập email của trường (hoặc của bạn), bấm **Continue**
4. Đặt mật khẩu, bấm **Continue**
5. Đặt **tên tài khoản** — ngắn, không dấu, không khoảng trắng.
   Ví dụ `cdd-lat` hoặc `khoahoccoban`.
   ⚠ **Tên này nằm trong link cuối cùng**, chọn cho gọn và dễ đọc.
6. Làm theo các bước xác nhận trên màn hình, rồi mở hộp thư bấm vào thư GitHub
   gửi để kích hoạt.

## Bước 2. Tạo kho chứa

1. Đăng nhập xong, bấm dấu **`+`** ở góc trên bên phải màn hình
2. Chọn **New repository**
3. Ô **Repository name**: gõ `tkb-khoi12`
4. Chọn **Public**
   *(Bắt buộc — bản miễn phí chỉ đăng được trang web từ kho Public. Đây cũng
   đúng ý muốn: để giáo viên và học sinh vào xem.)*
5. **Đừng tick** ô "Add a README file"
   *(Kho phải rỗng thì bước 5 mới đẩy lên được suôn sẻ.)*
6. Bấm nút xanh **Create repository** ở dưới cùng
7. Màn hình hiện ra một trang hướng dẫn — **giữ nguyên trang này**, bước 4 cần
   địa chỉ ghi ở đó, dạng `https://github.com/<tên tài khoản>/tkb-khoi12.git`

## Bước 3. Cài git trên máy (nếu chưa có)

1. Vào **git-scm.com**, bấm **Download for Windows**
2. Chạy tệp vừa tải, bấm **Next** liên tục cho tới **Install**, rồi **Finish**
3. Kiểm tra: mở Command Prompt, gõ `git --version`.
   Hiện ra một dòng có số phiên bản là được.

## Bước 4. Nối thư mục phần mềm với kho vừa tạo

Mở Command Prompt **tại thư mục phần mềm** (bấm vào thanh địa chỉ của thư mục,
gõ `cmd` rồi Enter), lần lượt gõ từng dòng:

```
git init -b main
git config user.name "Ten cua ban"
git config user.email "email@cua.ban"
git remote add origin https://github.com/<tên tài khoản>/tkb-khoi12.git
```

Dòng cuối thay `<tên tài khoản>` bằng tên bạn đặt ở Bước 1.

> Nếu thư mục đã là kho git rồi thì dòng `git init` sẽ báo "Reinitialized" —
> không sao, bỏ qua và làm tiếp.

## Bước 5. Chuẩn bị mã đăng nhập (Personal Access Token)

GitHub **không nhận mật khẩu thường** khi đẩy dữ liệu lên. Phải có một chuỗi mã
riêng, gọi là token.

1. Trên GitHub, bấm ảnh đại diện góc trên bên phải → **Settings**
2. Kéo xuống cuối cột trái, bấm **Developer settings**
3. Bấm **Personal access tokens** → **Tokens (classic)**
4. Bấm **Generate new token** → **Generate new token (classic)**
5. Ô **Note**: gõ `may tinh xep tkb`
6. Ô **Expiration**: chọn **No expiration**
   *(Chọn thời hạn thì tới ngày đó phải làm lại bước này.)*
7. Trong danh sách quyền, tick ô **repo** (ô đầu tiên, tick là tick cả nhóm)
8. Kéo xuống cuối, bấm **Generate token**
9. ⚠ **Chép ngay chuỗi vừa hiện ra và cất vào chỗ an toàn.**
   Rời khỏi trang là không xem lại được nữa, phải sinh cái mới.

Lần đầu chạy `dua_len.bat`, git sẽ hỏi:
- **Username** → gõ tên tài khoản GitHub
- **Password** → **dán chuỗi token**, không phải mật khẩu đăng nhập

Windows sẽ nhớ giúp, các lần sau không hỏi lại.

## Bước 6. Đẩy lên lần đầu

Bấm đúp **`dua_len.bat`**. Nó sẽ tự: xếp TKB → xuất trang web → chép vào
`docs/` → đẩy lên GitHub. Lần đầu mất khoảng 1 phút rưỡi.

> Máy không cài được git? Vẫn làm được bằng tay: chạy
> `python3 xep_tkb.py --xuat-html` (trên Windows gõ `python`, không có chữ số 3
> — xem mục 3 của `HUONG_DAN.md`), đổi tên `tkb_web.html` thành `index.html`,
> rồi trên GitHub bấm **Add file** → **Upload files**, kéo tệp vào, bấm
> **Commit changes**. Tuần nào cũng làm lại bốn thao tác đó.

## Bước 7. Bật GitHub Pages

1. Vào trang kho `tkb-khoi12` trên GitHub
2. Bấm **Settings** (thanh ngang phía trên, có hình bánh răng)
3. Cột bên trái, kéo xuống, bấm **Pages**
4. Mục **Source**: chọn **Deploy from a branch**
5. Dòng dưới: ô nhánh chọn **main**, ô thư mục chọn **/docs**, bấm **Save**
   ⚠ Chọn đúng **/docs**, không phải **/ (root)** — trang nằm trong thư mục `docs`.
6. **Đợi 2–5 phút** cho lần bật đầu tiên *(các lần cập nhật sau chỉ 1–2 phút)*
7. Tải lại chính trang Settings → Pages. Khi xong sẽ hiện khung xanh:
   *"Your site is live at https://…"*

## Bước 8. Kiểm tra link đã sống chưa

Link của bạn là:

```
https://<tên tài khoản>.github.io/tkb-khoi12/
```

Ngắn gọn, không có đuôi thư mục. Có được vậy là nhờ trang đặt trong thư mục
`docs` — GitHub Pages nhận đúng hai chỗ là gốc kho và `docs`, chọn `docs` thì
link ra gọn mà thư mục phần mềm cũng không bị lẫn tệp. Script tự in đúng link
này ở dòng cuối, cứ chép từ đó cho chắc.

- Mở link. Nếu hiện **404** thì chưa xong — đợi thêm 2 phút rồi tải lại.
- Vẫn 404 sau 10 phút: kiểm lại Bước 7 mục 5 đã chọn đúng **main** và
  **/docs** chưa, và trong kho đã có thư mục `docs` chưa.
- Mở được rồi thì xem dòng **"Xuất lúc ..."** ở đầu trang — ngày giờ phải khớp
  lần bạn vừa chạy.

Gửi link này cho giáo viên và học sinh. **Link không bao giờ đổi**, tuần nào
cũng dùng đúng nó.

---

# PHẦN B — LÀM HẰNG TUẦN (2 phút)

1. Mở `cauhinh.json`, sửa dòng `"tuan"` thành tuần mới.
   *(Hoặc bỏ qua bước này rồi dùng `python3 xep_tkb.py --tuan "TUẦN 3 (...)"`.)*
2. Bấm đúp **`dua_len.bat`**
3. Đợi nó chạy xong (~1 phút rưỡi), đọc dòng cuối
4. Đợi thêm 1–2 phút, mở link kiểm tra dòng **"Xuất lúc ..."**

Hết. Không phải vào GitHub, không phải kéo thả gì.

Nếu script **dừng lại giữa chừng**, nó in rõ lý do và cách sửa. Ba lý do hay gặp:

| Script báo | Cách sửa |
|---|---|
| *chưa nối với kho trên GitHub* | Chưa làm Bước 4. Quay lại PHẦN A. |
| *đẩy lên không xong* | Chưa đăng nhập (Bước 5), hoặc máy mất mạng. |
| *xếp thời khóa biểu không xong* | Quy tắc trong `cauhinh.json` mâu thuẫn. Đọc thông báo lỗi ngay phía trên. |

Trên Linux/macOS thì chạy `./dua_len.sh` thay cho `dua_len.bat`.

---

# PHẦN C — KHI TRƯỜNG MẤT MẠNG

Tệp `tkb_web.html` **không cần Internet**, mọi thứ nằm gọn trong một tệp.

- Chép vào **USB**, cắm vào máy nào cũng bấm đúp mở được.
- Hoặc bỏ vào **thư mục chia sẻ** trong mạng nội bộ của trường.
- Hoặc gửi thẳng tệp qua Zalo/email, mở trên điện thoại vẫn xem được đủ ba
  chế độ: theo lớp, theo giáo viên, cả khối.

Cách này **không công khai gì ra Internet**. Nếu nhà trường không muốn đưa
thời khóa biểu lên mạng thì chỉ cần dùng PHẦN C, bỏ hẳn PHẦN A và B.

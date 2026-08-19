# ĐƯA THỜI KHÓA BIỂU LÊN MẠNG CHO GIÁO VIÊN VÀ HỌC SINH XEM

Sau khi xếp xong, phần mềm sinh ra file **`tkb_web.html`**. Đó là **một file duy
nhất**, mở bằng điện thoại hay máy tính đều được, có sẵn ba cách xem: theo lớp,
theo giáo viên, và cả khối.

Có hai cách dùng, làm cả hai càng tốt:

| Cách | Khi nào |
|---|---|
| **Đưa lên GitHub Pages** | Bình thường. Ai có link đều xem được, kể cả ở nhà. |
| **Chép vào USB / thư mục chung** | Khi trường mất mạng. Bấm đúp file là mở. |

---

## PHẦN 1 — Làm một lần: tạo chỗ đặt trang

Vì sao chọn GitHub Pages: **miễn phí**, và **link không bao giờ đổi**. Mỗi tuần chỉ
việc thay file, người xem vẫn dùng đúng cái link cũ.

### Bước 1. Tạo tài khoản

1. Vào **github.com**.
2. Bấm **Sign up** (góc trên bên phải).
3. Nhập email, đặt mật khẩu, đặt tên tài khoản — nên đặt ngắn, không dấu, ví dụ
   `cdd-lat` hoặc `khoahoccoban`. **Tên này sẽ nằm trong link**, nên chọn cho gọn.
4. Mở hộp thư, bấm vào thư GitHub gửi để xác nhận.

### Bước 2. Tạo kho chứa file

1. Đăng nhập xong, bấm dấu **`+`** ở góc trên bên phải → chọn **New repository**.
2. Ô **Repository name**: gõ `tkb-khoi12`.
3. Chọn **Public**. *(Bắt buộc — bản miễn phí chỉ đăng được trang từ kho Public.
   Đây cũng là điều mong muốn: để giáo viên và học sinh vào xem.)*
4. Tick ô **Add a README file**.
5. Bấm nút xanh **Create repository** ở dưới cùng.

### Bước 3. Tải trang lên lần đầu

1. Trên máy, tìm file `tkb_web.html` trong thư mục phần mềm.
2. **Đổi tên nó thành `index.html`.** *(Bấm chuột phải → Rename. Làm vậy để link
   ngắn gọn; không đổi tên vẫn chạy, chỉ là link dài hơn một đoạn.)*
3. Ở trang kho vừa tạo, bấm **Add file** → **Upload files**.
4. Kéo thả `index.html` vào khung giữa màn hình.
5. Kéo xuống dưới, bấm nút xanh **Commit changes**.

### Bước 4. Bật trang web

1. Trong kho, bấm **Settings** (thanh ngang phía trên, có hình bánh răng).
2. Cột bên trái, kéo xuống, bấm **Pages**.
3. Mục **Source**: chọn **Deploy from a branch**.
4. Ngay dưới: ô nhánh chọn **main**, ô thư mục chọn **/ (root)**.
5. Bấm **Save**.
6. **Đợi 1–2 phút** rồi tải lại chính trang Settings → Pages này. Sẽ hiện một
   khung xanh kèm địa chỉ trang.

### Bước 5. Link của bạn

```
https://<tên tài khoản>.github.io/tkb-khoi12/
```

Ví dụ tài khoản `cdd-lat` thì link là `https://cdd-lat.github.io/tkb-khoi12/`.

Gửi link này cho giáo viên và học sinh. **Link không đổi**, tuần nào cũng dùng nó.

> Giao diện GitHub thỉnh thoảng đổi chữ trên nút đôi chút, nhưng thứ tự các bước
> thì vẫn vậy: tạo kho → tải file lên → Settings → Pages → chọn nhánh → Save.

---

## PHẦN 2 — Việc hằng tuần (khoảng 2 phút)

1. **Xếp thời khoá biểu.**
   - Dùng giao diện web: chạy `python web.py`, mở `http://127.0.0.1:20266`,
     bấm **Xếp thời khoá biểu**, xong bấm **Xuất trang web** để tải file về.
   - Hoặc dòng lệnh: `python xep_tkb.py --xuat-html`
2. **Đổi tên** file vừa có thành `index.html`.
3. Vào kho trên GitHub, bấm **Add file** → **Upload files**, kéo `index.html` vào,
   bấm **Commit changes**.
   *File cùng tên sẽ tự đè lên file cũ — đúng như mong muốn.*
4. Đợi 1–2 phút, mở link kiểm tra lại. Trên đầu trang có dòng **"Xuất lúc ..."**,
   xem ngày giờ ở đó có đúng lần vừa xếp không.

Dòng "Xuất lúc" chính là để người xem tự biết mình đang đọc bản nào — dặn giáo
viên để ý dòng đó.

---

## PHẦN 3 — Khi trường mất mạng

File `tkb_web.html` **không cần Internet**. Mọi thứ nằm gọn trong một file.

- Chép vào **USB**, cắm vào máy nào cũng bấm đúp mở được.
- Hoặc bỏ vào **thư mục chia sẻ** trong mạng nội bộ của trường.
- Hoặc gửi thẳng file qua Zalo/email cho giáo viên, mở trên điện thoại vẫn xem
  được đủ ba chế độ.

Không cần cài gì thêm, không cần phần mềm xếp TKB, chỉ cần một trình duyệt.

---

## PHẦN 4 — ⚠ Cần nhớ về quyền riêng tư

**Trang này ai có link cũng xem được.** Không có mật khẩu, và các máy tìm kiếm
cũng có thể lập chỉ mục nó.

Vì vậy:

- **Chỉ để tên viết tắt giáo viên như hiện tại** (`N.Uyên`, `M.Hạnh`...).
- **Đừng thêm số điện thoại, địa chỉ nhà, email cá nhân, ngày sinh, hay bất cứ
  thông tin cá nhân nào khác** vào `cauhinh.json` — vì mọi thứ trong đó đều có
  thể hiện lên trang.
- Cần liên hệ thì để số điện thoại **văn phòng khoa**, đừng để số riêng của thầy cô.

> **Một chỗ nên cân nhắc:** trang hiện đang hiện **họ tên đầy đủ của giáo viên chủ
> nhiệm** ở đầu mỗi cột lớp (ví dụ *"12B1 — Lê Thị Anh"*), giống hệt bản in treo ở
> trường. Nếu nhà trường thấy không nên đưa họ tên đầy đủ lên Internet thì đổi
> được: trong `cauhinh.json` đã có sẵn khoá `gvcn_vt` (tên viết tắt) cho từng lớp,
> chỉ cần nhờ sửa một dòng trong `xuat_html.py` để dùng khoá đó thay cho `gvcn`.

Nếu chỉ muốn cho người trong trường xem thì **đừng dùng GitHub Pages**, hãy dùng
cách ở Phần 3 (thư mục chia sẻ nội bộ hoặc USB).

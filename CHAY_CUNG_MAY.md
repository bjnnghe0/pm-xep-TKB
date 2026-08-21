# Chạy cùng máy — dịch vụ systemd và Tailscale

Mục đích: bật máy lên là phần mềm tự chạy, không phải mở cửa sổ dòng lệnh gõ gì.

Mọi lệnh dưới đây **không cần `sudo`**. Đó là chủ ý, không phải may: dịch vụ chạy
ở **phạm vi người dùng** (`systemctl --user`) chứ không phải phạm vi hệ thống.

> **Vì sao user unit chứ không phải system unit.** Máy này đã có sẵn `nbv-web`
> chạy đúng kiểu đó, và `loginctl show-user adminnam -p Linger` cho `Linger=yes`
> — nghĩa là dịch vụ người dùng **vẫn chạy khi chưa ai đăng nhập**, tức vẫn tự
> lên sau khi bật máy. Được thế thì một system unit chỉ thêm một lần `sudo` mà
> không mua thêm gì. Nếu sau này thật sự cần phạm vi hệ thống thì chép
> `xeptkb.service` vào `/etc/systemd/system/`, **thêm** `User=adminnam` và
> `Group=adminnam`, đổi `WantedBy=default.target` thành `multi-user.target`, rồi
> dùng `systemctl` (không có `--user`).

---

## 1. Tệp dịch vụ

Nội dung nằm sẵn ở **`xeptkb.service`** trong thư mục dự án — đọc thẳng tệp đó,
mỗi dòng có ghi chú vì sao. Chỗ đặt khi cài:

```
~/.config/systemd/user/xeptkb.service
```

Ba dòng dễ sai nhất, **đã đo trên chính máy này**:

| Khoá | Viết đúng | Viết sai thì sao |
|---|---|---|
| `RequiresMountsFor=` | `"/media/adminnam/NAM MEO"` — **có ngoặc kép** | `\x20` → systemd đọc ra `/media/adminnam/NAMx20MEO`, chờ một đường dẫn không tồn tại, tức **không chờ gì cả**. Dấu cách trần → cắt còn `/media/adminnam/NAM` |
| `WorkingDirectory=` | `/media/adminnam/NAM MEO/...` — **dấu cách trần** | Bọc ngoặc kép → `Unit configuration has fatal error, unit will not be started` |
| `ExecStart=` | `/home/adminnam/.venvs/xeptkb/bin/python3` | `/usr/bin/python3` **không có openpyxl** → máy chủ chạy ngon, xếp xong 50 giây mới báo thiếu thư viện ở bước xuất Excel |

---

## 2. Cài — chép dán một lượt

```bash
cd "/media/adminnam/NAM MEO/projects/PM xep tkb"

# Đang chạy tay thì tắt đi, không thì hai bên tranh nhau cổng 20266
pkill -f "python3 -u web.py" ; pkill -f "web.py --port 20266" ; true

mkdir -p ~/.config/systemd/user
cp xeptkb.service ~/.config/systemd/user/xeptkb.service
systemctl --user daemon-reload
systemctl --user enable --now xeptkb.service

# Dịch vụ người dùng phải chạy cả khi chưa ai đăng nhập
loginctl enable-linger "$USER"
```

---

## 3. Kiểm sau khi cài

```bash
# a) dịch vụ đang chạy, và bật cùng máy
systemctl --user is-enabled xeptkb.service      # -> enabled
systemctl --user is-active  xeptkb.service      # -> active

# b) không còn cảnh báo cú pháp nào
systemd-analyze --user verify ~/.config/systemd/user/xeptkb.service
#    (không in gì = sạch)

# c) RequiresMountsFor trỏ ĐÚNG chỗ gắn ổ
systemctl --user show xeptkb.service -p RequiresMountsFor
#    phải thấy: "/media/adminnam/NAM MEO"
#    KHÔNG được thấy: /media/adminnam/NAM     hoặc   NAMx20MEO
systemctl --user show xeptkb.service -p After | tr ' ' '\n' | grep -i "NAM"
#    phải thấy: "media-adminnam-NAM\x20MEO.mount"

# d) trần khởi động lại đã đúng (nếu không thì bẫy quay vòng còn nguyên)
systemctl --user show xeptkb.service -p StartLimitBurst -p StartLimitIntervalUSec
#    phải thấy: StartLimitBurst=3   StartLimitIntervalUSec=5min

# e) có người nghe cổng 20266, và trả lời được
ss -ltnp | grep 20266
curl -s -o /dev/null -w '%{http_code}\n' -H 'Host: 127.0.0.1:20266' \
     http://127.0.0.1:20266/          # -> 200

# f) nhật ký
journalctl --user -u xeptkb.service -n 20 --no-pager
```

> **Vì sao `curl` phải kèm `-H 'Host: ...'`.** Máy chủ chỉ nhận yêu cầu từ tên
> máy đã khai trong `cauhinh_may_chu.json` (bất biến A1). Gọi `curl` trần sẽ
> nhận **400** — đó là **đúng**, không phải hỏng.

---

## 4. Thử BẪY FAIL-CLOSED — tự làm được, mất 20 giây

`web.py` **cố ý** từ chối khởi động khi thiếu/hỏng `tai_khoan.json`. Phải chắc
là lúc đó dịch vụ **bỏ cuộc và nằm ở `failed`**, chứ không quay vòng vô tận.

```bash
cd "/media/adminnam/NAM MEO/projects/PM xep tkb"
mv tai_khoan.json tai_khoan.json.giau            # giấu đi, KHÔNG xoá
systemctl --user restart xeptkb.service

sleep 20
systemctl --user is-active xeptkb.service        # -> failed   (KHÔNG phải activating)
systemctl --user show xeptkb.service -p NRestarts # -> 2
journalctl --user -u xeptkb.service -n 12 --no-pager | tail -8
#    phải thấy nguyên văn:  [LỖI] Chưa có tệp tai_khoan.json.
#    và:                    Start request repeated too quickly.

# trả lại như cũ
mv tai_khoan.json.giau tai_khoan.json
systemctl --user reset-failed xeptkb.service
systemctl --user start xeptkb.service
systemctl --user is-active xeptkb.service        # -> active
```

**Đã đo cả hai bên** trên một bản sao của dịch vụ này:

| Cấu hình | Kết quả |
|---|---|
| Mặc định `5 lần / 10 giây` + `RestartSec=5` | 7 lần thử trong 35 giây, vẫn `activating` — **quay vòng vô tận** |
| `3 lần / 300 giây` (bản đang dùng) | vào `failed` sau **15 giây** và nằm yên |

Lý do bản mặc định không bao giờ chạm trần: `RestartSec=5` nghĩa là mỗi cửa sổ
10 giây chỉ có 2–3 lần khởi động, mà trần là 5.

---

## 5. Gỡ — quay lại chạy tay

```bash
systemctl --user disable --now xeptkb.service
rm -f ~/.config/systemd/user/xeptkb.service
systemctl --user daemon-reload
systemctl --user reset-failed xeptkb.service 2>/dev/null; true

# chạy tay như cũ
cd "/media/adminnam/NAM MEO/projects/PM xep tkb"
~/.venvs/xeptkb/bin/python3 web.py
```

`loginctl enable-linger` thì **đừng tắt** nếu còn dịch vụ `nbv-web` — nó cũng
dựa vào đó.

---

## 6. Tailscale — có tự sống lại sau khi bật máy không

Đo được trên máy này:

```
tailscaled            enabled · active     -> tự chạy cùng máy
tailscale serve status:
  https://admin.tail7dc28e.ts.net (Funnel on)
  |-- /    proxy http://127.0.0.1:20266
  |-- /nbv proxy http://127.0.0.1:8080
```

Khai báo `serve`/`funnel` nằm trong trạng thái của `tailscaled` chứ không phải
trong một lệnh phải gõ lại, nên **về nguyên tắc nó sống qua khởi động lại**.
Nhưng đó là nguyên tắc; bằng chứng là mục 7.

```bash
# sau khi bật máy lại
systemctl is-active tailscaled          # -> active
tailscale status | head -3              # máy này phải có địa chỉ 100.x
tailscale serve status                  # phải còn nguyên hai dòng proxy
```

Nếu khai báo mất thì dựng lại:

```bash
tailscale serve --bg --set-path / 20266
```

---

## 7. Bằng chứng cuối — KHỞI ĐỘNG LẠI MÁY THẬT

Không gõ lệnh nào sau khi máy lên. Từ điện thoại **dùng 4G, tắt Wi-Fi** (để chắc
chắn không đi vòng qua mạng nhà):

1. Mở `https://admin.tail7dc28e.ts.net`
2. Đăng nhập
3. Sửa một quy tắc rồi bấm **Lưu vào cauhinh.json**
4. Về máy, kiểm tệp thật sự đổi trên đĩa:

```bash
cd "/media/adminnam/NAM MEO/projects/PM xep tkb"
ls -l --time-style=+%H:%M:%S cauhinh.json cauhinh.bak.json
git diff --stat cauhinh.json
```

Ba thứ phải cùng đúng thì mới gọi là xong: máy chủ tự lên · ổ đã gắn trước khi
nó lên · và ghi được xuống đĩa.

---

## 8. Khi hỏng thì nhìn đâu

| Triệu chứng | Nhìn |
|---|---|
| Trang không mở được | `systemctl --user status xeptkb.service` |
| Dịch vụ ở `failed` | `journalctl --user -u xeptkb.service -n 30` — câu lỗi tiếng Việt của `web.py` nằm nguyên ở đó |
| Vào được nhưng bấm **Lưu** hỏng | Ổ NTFS đang ở chế độ **chỉ đọc**. Máy chủ lẽ ra đã từ chối khởi động và nói rõ — xem journal. Chữa: vào Windows tắt "khởi động nhanh" rồi *Shut down* hẳn |
| Xếp xong báo thiếu `openpyxl` | `ExecStart` đang trỏ nhầm `/usr/bin/python3`. Phải là `~/.venvs/xeptkb/bin/python3` |
| Chỉ hỏng lúc vừa bật máy | `RequiresMountsFor` khai sai — xem lại mục 3c |

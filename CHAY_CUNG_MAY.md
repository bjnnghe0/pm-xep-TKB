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
  https://admin.tail7dc28e.ts.net        (Funnel on)   |-- /nbv -> 127.0.0.1:8080
  https://admin.tail7dc28e.ts.net:8443   (tailnet only)|-- /    -> 127.0.0.1:20266
```

> **⚠ HAI CỔNG, HAI PHẠM VI KHÁC HẲN NHAU — đừng trộn.**
> `:443` bật **Funnel**, tức mở ra **cả Internet**; `:8443` chỉ trong **tailnet**.
> Funnel bật theo cặp **tên-máy:cổng**, KHÔNG theo đường dẫn — nên trước đây bật
> Funnel cho trang công khai `/nbv` là **kéo theo cả `/`**, và trang quản trị TKB
> phơi ra Internet mà không ai cố ý làm vậy. Đã tách: TKB dời sang `:8443`,
> đường `/` gỡ khỏi `:443`. Đo lại bất cứ lúc nào bằng:
> `tailscale serve status --json` → xem khoá `AllowFunnel`.
>
> Đổi cổng thì phải thêm tên máy MỚI vào **cả hai** danh sách của
> `cauhinh_may_chu.json` (`host_cho_phep` và `origin_cho_phep`), nếu không mọi
> yêu cầu đều 400. Hiện có: `admin.tail7dc28e.ts.net:8443`.

Khai báo `serve`/`funnel` nằm trong trạng thái của `tailscaled` chứ không phải
trong một lệnh phải gõ lại, nên **về nguyên tắc nó sống qua khởi động lại**.

> **✅ ĐÃ ĐO, KHÔNG CÒN LÀ NGUYÊN TẮC — 21/8/2026.** Khởi động lại máy thật, rồi
> **không gõ một lệnh nào** trước khi thử. `tailscale serve --https=8443` **tự
> sống lại**: từ điện thoại tắt Wi-Fi, chạy 4G, vào
> `https://admin.tail7dc28e.ts.net:8443/` → đăng nhập → Xếp → Lưu, chạy suốt,
> **không 502**. Số đo đầy đủ ở mục 7. Vì vậy **không cần** dựng thêm unit
> systemd nào cho `tailscale serve` — thêm mã khi số đo nói không cần là thêm
> một chỗ để hỏng.

```bash
# sau khi bật máy lại
systemctl is-active tailscaled          # -> active
tailscale status | head -3              # máy này phải có địa chỉ 100.x
tailscale serve status                  # phải còn nguyên hai dòng proxy
```

Nếu khai báo mất thì dựng lại — **đúng hai lệnh này, đừng gõ tắt**:

```bash
# TKB: chỉ trong tailnet, cổng 8443
tailscale serve --bg --https=8443 --set-path / 20266

# trang công khai: Funnel, cổng 443
tailscale funnel --bg --set-path /nbv 8080
```

> **ĐỪNG gõ `tailscale serve --bg --set-path / 20266`.** Thiếu `--https=8443`
> thì nó gắn `/` vào cổng **443** — cổng đang bật Funnel — và trang quản trị
> TKB lại phơi ra Internet. Đó đúng là cấu hình vừa gỡ đi.

### 6b. Điều kiện nào làm MẤT cấu hình serve — hai dòng phải nhớ

**Chỉ ghi giấy. Không có script canh chừng, và cố ý không có.**

```bash
tailscale serve status                                  # CÁCH KIỂM — chỉ đọc, an toàn
tailscale serve --bg --https=8443 --set-path / 20266    # CÁCH DỰNG LẠI — lệnh ĐẶT
```

Dòng dựng lại chỉ dựng lại **cổng 8443 của TKB**. Nó **không** dựng lại trang
công khai `/nbv` ở cổng 443 — cái đó là lệnh `tailscale funnel` riêng, ngay bên
trên.

**Bốn điều kiện, và mức bằng chứng của từng cái. Ba trong bốn là CHƯA BIẾT:**

| Điều kiện | Mức | Đã biết gì |
|---|---|---|
| Khởi động lại máy | **ĐÃ ĐO — KHÔNG mất** | Xem mục 7 |
| `tailscale logout` | **CHƯA BIẾT — nghi nhất** | Khoá cất serve gắn **theo profile** (`_serve/<ID hồ sơ>`, đọc từ nhị phân). `logout` là thứ đụng vào hồ sơ. Chưa ai chạy thử trên máy này |
| `tailscale down` | **CHƯA BIẾT** | Trợ giúp của bản đang cài chỉ nói `Disconnect from Tailscale`, không một chữ serve/funnel. Nhưng dù cấu hình còn nguyên thì `down` vẫn đưa máy offline — **"cấu hình còn" khác "thầy cô vào được"** |
| Đổi tài khoản / hồ sơ | **CHƯA BIẾT** | Máy đang có đúng **1 hồ sơ**. Muốn đo phải tạo hồ sơ thứ hai, tức phải `tailscale login` |
| Nâng cấp gói | **Đo được phần TỆP, chưa đo được HỆ QUẢ** | `postinst` **khởi động lại daemon ở MỌI lần nâng cấp**. Không script nào xoá trạng thái (chỉ nhánh `purge` mới `rm -rf`). Nhưng chưa ai đo binary MỚI đọc trạng thái CŨ có giữ serve không |

> **⚠ Máy này TỰ NÂNG CẤP tailscale lúc nửa đêm — đã xảy ra ít nhất một lần.**
> `tailscale debug prefs` cho `"AutoUpdate": {"Check": true, "Apply": true}`.
> `/var/log/apt/history.log` có dòng `2026-08-08 01:30:33 apt-get install --yes
> --allow-downgrades tailscale=1.102.2`, **không có `Requested-By:`** (khác lần
> cài tay 9/7 thì có) — tức không ai bấm. Nghĩa là đường vào có thể tắt vài giây
> lúc 1h30 sáng mà không ai hay. Đó là lý do dòng **CÁCH KIỂM** đáng nhớ hơn
> dòng dựng lại.

> **⚠ Gõ sai tên lệnh con = chạy một lệnh ĐẶT.** `tailscale serve <đích>` là một
> dạng gọi hợp lệ **không có tên lệnh con**, nên `tailscale serve statuss` không
> báo "lệnh không tồn tại" mà có thể đi thẳng vào nhánh đặt cấu hình. Gõ tay thì
> nhìn kỹ.
>
> **`tailscale funnel reset` KHÔNG vô hại** — nó tắt trang công khai `/nbv`.

> **Cách rẻ nhất để khỏi phải đoán:** trước mỗi lần làm việc có thể chạm serve
> (nâng cấp, đổi tài khoản, thử nghiệm), chạy `tailscale serve status --json` và
> giữ lại kết quả. Mất thì có sẵn bản để dựng lại.

---

## 7. Bằng chứng cuối — ĐÃ KHỞI ĐỘNG LẠI MÁY THẬT, 21/8/2026

> **✅ ĐẠT. Bốn dòng số dưới đây là toàn bộ bằng chứng — đừng thay chúng bằng
> câu "dịch vụ tự chạy được".** Một câu kết luận không kèm số đo thì sáu tháng
> nữa không ai nhớ nó dựa trên gì, và sẽ phải đo lại từ đầu.

Khởi động lại máy thật. Sau khi máy bật, **không gõ lệnh nào trước khi thử**:

```
uptime -s        -> 2026-08-21 18:35:23
Active since     -> 2026-08-21 18:35:34   (sau 11 giây)
Main PID         -> 1271
Loaded           -> enabled; preset: enabled
```

Bốn dòng đó lấy ra bằng đúng bốn lệnh này, chạy lại lúc nào cũng được:

```bash
uptime -s                                                      # -> 2026-08-21 18:35:23
systemctl --user show xeptkb.service -p ActiveEnterTimestamp   # -> ... 18:35:34 +07
systemctl --user show xeptkb.service -p MainPID                # -> 1271
systemctl --user show xeptkb.service -p UnitFileState -p UnitFilePreset
#                                                              # -> enabled / enabled
```

Rồi từ điện thoại, **tắt Wi-Fi, dùng 4G**:
`https://admin.tail7dc28e.ts.net:8443/` → đăng nhập → **Xếp** → **Lưu**.
Chạy suốt. **Không 502.**

**Hai kết luận, cả hai đều có số đo đứng sau:**

| # | Kết luận | Số đo nào nói điều đó |
|---|---|---|
| **5d** | Dịch vụ systemd khởi sinh **lúc máy đang dựng**, trước khi có ai đăng nhập màn hình | `Active since` chỉ sau `uptime -s` **11 giây** — đó là số đo quyết định. `Main PID 1271` đi cùng chiều: một PID nhỏ như vậy hợp với tiến trình sinh ra trong đợt dựng máy (chỉ dấu, không phải bằng chứng riêng lẻ) |
| **5e** | `tailscale serve --https=8443` **tự sống lại** sau khởi động | Điện thoại 4G vào được `:8443` mà **chưa ai gõ lệnh `tailscale serve` nào** sau khi máy lên. Không 502 nghĩa là proxy còn trỏ đúng `127.0.0.1:20266` |

**Mục 5e trước giờ chưa ai đo.** Giờ đã đo. **Đợt 2 đóng.**

---

### Đo lại thế nào — công thức lặp lại được

Không gõ lệnh nào sau khi máy lên. Từ điện thoại **dùng 4G, tắt Wi-Fi** (để chắc
chắn không đi vòng qua mạng nhà):

1. Mở `https://admin.tail7dc28e.ts.net:8443/` — **nhớ `:8443`**; địa chỉ
   không có cổng là trang công khai, không phải trang quản trị
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
| **Sửa xong nguyên nhân mà dịch vụ vẫn `failed`** | Trạng thái `failed` **DÍNH**, không tự gỡ. Phải:<br>`systemctl --user reset-failed xeptkb.service`<br>`systemctl --user start xeptkb.service`<br>Đây **không phải lỗi** — bẫy fail-closed cố ý bắt systemd bỏ cuộc và **nằm yên** ở `failed` để người vận hành nhìn thấy. Cái giá là phải gỡ tay. |
| Vào được nhưng bấm **Lưu** hỏng | Ổ NTFS đang ở chế độ **chỉ đọc**. Máy chủ lẽ ra đã từ chối khởi động và nói rõ — xem journal. Chữa: vào Windows tắt "khởi động nhanh" rồi *Shut down* hẳn |
| Xếp xong báo thiếu `openpyxl` | `ExecStart` đang trỏ nhầm `/usr/bin/python3`. Phải là `~/.venvs/xeptkb/bin/python3` |
| Chỉ hỏng lúc vừa bật máy | `RequiresMountsFor` khai sai — xem lại mục 3c |

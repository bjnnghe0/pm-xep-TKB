#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 TRA BẢNG TÊN — MỘT BẢN CÀI DUY NHẤT, VÀ CHỈ SO CHUỖI ĐÚNG Y HỆT
--------------------------------------------------------------------------
 Chạy thử:  python3 bang_ten.py

 Tệp của trường viết một môn ra nhiều chuỗi (`GDKT-PL` và `GDKTPL`,
 `Chuyên đề Lịch sử` và `Chuyên đề sử`), và viết tắt tên giáo viên cũng
 vậy (`T.Hiền` và `T.T.Hiền`). Mô-đun này giữ **quyết định của thầy cô**
 về chuỗi nào là chuỗi nào, và trả lời đúng một câu:

     chuỗi lạ  ->  tên chuẩn

 ┌──────────────────────────────────────────────────────────────────────┐
 │ PHÉP TRA LÀ SO CHUỖI ĐÚNG Y HỆT — `self.gop.get(s, s)`.              │
 │                                                                      │
 │ KHÔNG `.strip()` · KHÔNG `.lower()` · KHÔNG bỏ dấu · KHÔNG chuẩn hoá  │
 │ Unicode · KHÔNG tiền tố · KHÔNG hậu tố · KHÔNG "gần giống".          │
 │                                                                      │
 │ VÌ SAO GẮT ĐẾN VẬY — có một cái bẫy THẬT trong dữ liệu nhà trường:   │
 │ khoa có **H.Hiền** (Địa lí, GVCN 12B2) VÀ **T.T.Hiền** (Sinh học).   │
 │ Hai người khác nhau, cùng phần sau dấu chấm cuối. Bất kỳ phép so     │
 │ "gần đúng" nào đụng tới phần đuôi — `split('.')[-1]`, `endswith`,    │
 │ bỏ dấu rồi so — đều gộp hai cô làm một, và khi ấy tờ TKB treo ở      │
 │ trường sẽ ghi tiết của cô này dưới tên cô kia.                       │
 │ `tests/thu_bang_ten.py` canh đúng chuyện đó.                         │
 └──────────────────────────────────────────────────────────────────────┘

 ┌──────────────────────────────────────────────────────────────────────┐
 │ BẢNG TÊN ÁP CHO **ĐỐI CHIẾU** VÀ **BÁO CÁO**.                        │
 │ KHÔNG BAO GIỜ ÁP CHO **ĐĂNG**.                                       │
 │                                                                      │
 │ Trang công khai là bản điện tử của đúng tờ TKB đang treo ở trường.   │
 │ Trường phát ra sao thì đăng vậy — không tự bịa nhãn. Muốn trang      │
 │ hiện tên chuẩn thì sửa tệp gốc ở trường, đừng sửa lúc đăng.          │
 │ `sinh_dang.py` là cửa duy nhất ra công khai và nó KHÔNG được nhắc    │
 │ tới mô-đun này; `tests/thu_sinh_dang.py` CA 2 canh bằng cây cú pháp. │
 └──────────────────────────────────────────────────────────────────────┘

 CŨNG KHÔNG ÁP CHO BỘ ĐỌC. `doc_tkb.doc(ten_mon_biet=)` chỉ nhận
 `bang.biet`, KHÔNG nhận `bang.gop`. Lý do: `luu_tuan.py them` lấy chính
 dict do bộ đọc trả về rồi ghi vĩnh viễn vào `luu_tru/<tuần>/tach/`, mà
 `dau_bo_doc()` chỉ băm MÃ NGUỒN `doc_tkb.py` chứ không băm đối số — nới
 đối số ấy là đổi nội dung bản tách trong khi dấu bộ đọc không đổi một
 ký tự. Việc trừ phần đã gộp làm ở tầng BÁO CÁO (`luu_tuan._in_bao_cao`).

 BẢNG NÀY CHỈ NHẬN CẶP ĐÚNG Ở **MỌI Ô**. Sai lệch của **một ô** thì
 không bao giờ chữa ở đây — nó là khuyết tật của một bản, ghi bằng
 `kho_tuan.ghi_khuyet_tat()`. Đo trên tệp tuần 1 (26/8/2026): thêm một
 mục `"Địa lí" -> "Chuyên đề Địa lí"` vào bảng sẽ đổi **13 ô** thay vì
 đúng 1 ô đáng đổi, cả sáu lớp sai một lượt, trong im lặng.

 CHỈ ÁP LÚC ĐỌC. Mô-đun này không ghi một byte nào, không sửa tệp trong
 `luu_tru/`, không sửa `cauhinh.json`, không biết `cauhinh.json` tồn tại.
==========================================================================
"""
import io
import json
import os

TEN_MON = 'bang_ten_mon.json'
TEN_GV = 'bang_ten_gv.json'

# Hai khoá BẮT BUỘC của mỗi mục gộp. Chúng là lý do DUY NHẤT khiến mục gộp
# là một object chứ không phải một cặp chuỗi: không phép đo nào chứng minh
# được `T.Hiền` với `T.T.Hiền` là một người — chỉ có chữ ký của người duyệt.
KHOA_DUYET = ('nguoi_duyet', 'ngay')


def goc_mac_dinh():
    return os.path.dirname(os.path.abspath(__file__))


class Bang:
    """Một bảng tên đã duyệt. TOÀN PHẦN: không hàm nào ở đây ném.

       `biet`  — tập chuỗi đã duyệt là ĐÚNG, không phải gộp đi đâu.
       `gop`   — dict chuỗi lạ -> tên chuẩn.
       `duyet` — dict chuỗi lạ -> {'nguoi': ..., 'ngay': ...}.
       `loi`   — danh sách câu tiếng Việt. Khác rỗng thì bảng RỖNG HẲN, và
                 người gọi phải KÊU TO chứ đừng đi tiếp trong im lặng: một
                 bảng rỗng làm mọi phép kiểm tên trở nên vô nghĩa mà vẫn
                 chạy trót lọt.
    """

    __slots__ = ('ten', 'nguon', 'biet', 'gop', 'duyet', 'loi')

    def __init__(self, ten, nguon=None, biet=(), gop=None, duyet=None, loi=()):
        self.ten = ten
        self.nguon = nguon
        self.biet = frozenset(biet)
        self.gop = dict(gop or {})
        self.duyet = dict(duyet or {})
        self.loi = list(loi)

    # ------------------------------------------------------------------
    def chuan(self, s):
        """Chuỗi lạ -> tên chuẩn. SO ĐÚNG Y HỆT, không có ngoại lệ nào.

           Không có trong bảng thì trả về **chính nó**, nguyên vẹn từng ký
           tự — kể cả khoảng trắng thừa và hoa/thường lệch. Sửa hộ ở đây là
           nới lỏng phép so, và cái nới ấy sẽ gộp mất hai người có thật
           (xem khối chữ đầu tệp).
        """
        return self.gop.get(s, s)

    def da_duyet(self):
        """Mọi chuỗi thầy cô đã ngó qua: tên chuẩn CỘNG các chuỗi lạ đã gộp.

           ⚠ KHÔNG truyền cái này vào `doc_tkb.doc(ten_mon_biet=)` — xem
           khối chữ đầu tệp. Nó dùng cho tầng BÁO CÁO: để phân biệt
           "chuỗi chưa ai xét" với "chuỗi đã có luật gộp".
        """
        return self.biet | frozenset(self.gop)

    def ai_duyet(self, s):
        """(người, ngày) của một cặp gộp, hoặc (None, None)."""
        d = self.duyet.get(s) or {}
        return d.get('nguoi'), d.get('ngay')

    def ten_la(self, tu_vung):
        """Vế CHUẨN nào không có trong vốn từ người gọi đưa vào.

           Bốn phép kiểm lúc nạp đều kiểm HÌNH DẠNG, không kiểm NỘI DUNG:
           `"GDKTPL" -> "GDKT_PL"` (gạch dưới thay gạch ngang) qua sạch cả
           bốn, và khi đó bảng trông như đang gộp nhưng thật ra đẻ thêm một
           chuỗi lạ mới. Chỗ duy nhất biết tên nào có thật là dữ liệu nhà
           trường, mà mô-đun này cố ý không đọc — nên người gọi bơm vào.

           Cùng hình dạng với `pham_vi_quy_tac().ten_la`: một bản cài của
           cùng một ý niệm, không phải hai.
        """
        co = set(tu_vung or ())
        return sorted({v for v in self.gop.values() if v not in co})

    def __len__(self):
        return len(self.gop)

    def __repr__(self):
        return (f'<Bang {self.ten}: {len(self.biet)} biết, '
                f'{len(self.gop)} gộp, {len(self.loi)} lỗi>')


# ==========================================================================
def _chuan_cua(v):
    """Vế chuẩn của một mục gộp, chấp cả dạng object lẫn dạng chuỗi trần."""
    return v.get('chuan') if isinstance(v, dict) else v


def _kiem(ten, biet, gop):
    """Trả danh sách câu lỗi. Bảng sai thì DÙNG RỖNG chứ không dùng một nửa."""
    loi = []
    if not isinstance(biet, list):
        loi.append(f'{ten}: khoá "biet" phải là một dãy.')
        biet = []
    for x in biet:
        if not isinstance(x, str) or not x:
            loi.append(f'{ten}: "biet" có mục không phải chuỗi khác rỗng: {x!r}')
    if not isinstance(gop, dict):
        return loi + [f'{ten}: khoá "gop" phải là một object.']

    for k, v in gop.items():
        if not isinstance(k, str) or not k:
            loi.append(f'{ten}: khoá gộp không phải chuỗi khác rỗng: {k!r}')
            continue
        chuan = _chuan_cua(v)
        if not isinstance(chuan, str) or not chuan:
            loi.append(f'{ten}: mục gộp {k!r} thiếu "chuan" (chuỗi khác rỗng).')
            continue
        if chuan == k:
            loi.append(f'{ten}: mục gộp {k!r} trỏ về chính nó — thừa, và làm '
                       'người đọc tưởng có gì đó đang xảy ra.')
        if not isinstance(v, dict):
            loi.append(f'{ten}: mục gộp {k!r} phải là một object có '
                       f'{list(KHOA_DUYET)}. Cặp chuỗi trần không nói được ai '
                       'duyệt và duyệt ngày nào.')
            continue
        for khoa in KHOA_DUYET:
            x = v.get(khoa)
            if not isinstance(x, str) or not x.strip():
                loi.append(
                    f'{ten}: mục gộp {k!r} thiếu "{khoa}". Không phép đo nào '
                    'chứng minh được hai chuỗi là một người hay một môn — chỉ '
                    'có chữ ký người duyệt. Thiếu nó thì sáu tháng nữa không '
                    'ai dám tin cặp gộp này, và sẽ có người gỡ nó.')

    # NỐI CHUỖI: a -> b và b -> c. Tra một lần cho ra b, tra hai lần cho ra c;
    # kết quả phụ thuộc SỐ LẦN TRA, tức phép tra không còn là một hàm nữa.
    thang = {k: _chuan_cua(v) for k, v in gop.items() if isinstance(k, str)}
    noi = sorted(k for k, v in thang.items() if isinstance(v, str) and v in thang)
    if noi:
        loi.append(f'{ten}: gộp NỐI CHUỖI ở {noi} — tên chuẩn của mục này lại '
                   'là chuỗi lạ của mục khác. Tra một lần và tra hai lần sẽ ra '
                   'hai kết quả khác nhau. Sửa cho mỗi mục trỏ THẲNG tới tên '
                   'chuẩn cuối cùng.')
    return loi


def nap_mot(duong_dan, ten):
    """Đọc MỘT tệp bảng tên. KHÔNG BAO GIỜ NÉM.

       Thiếu tệp  -> bảng rỗng, KHÔNG lỗi (đây là cài đặt thường).
       Tệp hỏng   -> bảng rỗng, CÓ lỗi — người gọi phải kêu to.
    """
    if not os.path.exists(duong_dan):
        return Bang(ten, duong_dan)
    try:
        with io.open(duong_dan, encoding='utf-8-sig') as f:
            b = json.load(f)
    except Exception as e:                              # noqa: BLE001
        return Bang(ten, duong_dan,
                    loi=[f'{ten} hỏng, không đọc được: {type(e).__name__}: {e}'])
    if not isinstance(b, dict):
        return Bang(ten, duong_dan, loi=[f'{ten}: gốc tệp phải là một object.'])

    biet = b.get('biet', [])
    gop = b.get('gop', {})
    loi = _kiem(ten, biet, gop)
    if loi:
        return Bang(ten, duong_dan, loi=loi)

    g, d = {}, {}
    for k, v in gop.items():
        g[k] = _chuan_cua(v)
        d[k] = {'nguoi': v.get('nguoi_duyet'), 'ngay': v.get('ngay')}
    return Bang(ten, duong_dan, biet=biet, gop=g, duyet=d)


def nap(goc=None):
    """Trả (bảng môn, bảng GV). Hai bảng RIÊNG, cố ý không nhập làm một.

       Một chuỗi có thể vừa là tên môn ở tệp này vừa là tên viết tắt giáo
       viên ở tệp khác; đổ chung vào một dict là tự tay dựng chỗ cho lỗi đó.

       Nạp ĐÚNG MỘT LẦN ở điểm vào rồi truyền đối tượng `Bang` xuống — đừng
       để mỗi nơi tự gọi `nap()`, đó là cách bản cài thứ hai ra đời.
    """
    goc = goc or goc_mac_dinh()
    return (nap_mot(os.path.join(goc, TEN_MON), TEN_MON),
            nap_mot(os.path.join(goc, TEN_GV), TEN_GV))


# ==========================================================================
if __name__ == '__main__':
    for b in nap():
        print(f'{b.ten}: {len(b.biet)} tên đã biết · {len(b.gop)} cặp gộp')
        for k in sorted(b.gop):
            ng, ngay = b.ai_duyet(k)
            print(f'   {k!r} -> {b.gop[k]!r}   ({ng} · {ngay})')
        for x in b.loi:
            print(f'   [LỖI] {x}')

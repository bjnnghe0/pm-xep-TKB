#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
==========================================================================
 XUẤT THỜI KHÓA BIỂU RA MỘT TRANG WEB TĨNH
--------------------------------------------------------------------------
 xuat_html(bt, pa, duong_dan)  — nhận đúng bt và pa như xuat_excel().

 Sinh ra MỘT file .html duy nhất, tự chứa hoàn toàn: HTML + CSS + JS +
 dữ liệu nhúng thẳng dạng JSON. Không CDN, không font ngoài, không gọi
 mạng. Mở bằng file:// (bấm đúp từ USB) chạy đủ chức năng, mà đưa lên
 GitHub Pages cũng chạy y hệt.

 Trang chỉ để XEM và LỌC. Không sửa, không xếp lại.
==========================================================================
"""
import json
from datetime import datetime

TRANG = '''<!DOCTYPE html>
<html lang="vi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>__TIEU_DE__</title>
<style>
:root { color-scheme: light; }
* { box-sizing: border-box; }
body { margin: 0; padding: 0 12px 36px; background: #f4f6f9; color: #1c2430;
       font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif;
       font-size: 15px; -webkit-text-size-adjust: 100%; }
header { padding: 14px 0 10px; }
h1 { margin: 0; font-size: 19px; line-height: 1.3; }
.tuan { margin: 5px 0 0; font-size: 15px; font-weight: 600; color: #0b3d75; }
.xuat-luc { margin: 3px 0 0; font-size: 12.5px; color: #5a6673; }
nav { display: flex; gap: 6px; flex-wrap: wrap; margin: 12px 0 10px; }
nav button { flex: 1 1 auto; min-width: 104px; padding: 10px 12px; font-size: 14px;
             font-family: inherit; border: 1px solid #c3ccd7; background: #fff;
             border-radius: 8px; cursor: pointer; color: #33404f; }
nav button.chon { background: #1a6fc4; border-color: #1a6fc4; color: #fff;
                  font-weight: 600; }
.chon-hop { margin-bottom: 12px; }
select { width: 100%; max-width: 420px; padding: 10px; font-size: 16px;
         font-family: inherit; border: 1px solid #c3ccd7; border-radius: 8px;
         background: #fff; }
.cuon { overflow-x: auto; -webkit-overflow-scrolling: touch;
        border: 1px solid #dde3ea; border-radius: 8px; background: #fff; }
table { border-collapse: collapse; width: 100%; background: #fff; }
th, td { border: 1px solid #dde3ea; padding: 6px 7px; font-size: 13px;
         text-align: center; vertical-align: middle; }
th { background: #eef2f7; font-weight: 600; }
.mon { font-weight: 600; display: block; }
.phu { color: #5a6673; font-size: 11.5px; display: block; }
.trong { background: #fafbfc; }
.nhan { background: #eef2f7; font-weight: 600; white-space: nowrap; }
.het-ngay td, .het-ngay th { border-bottom: 2px solid #9aa8b8; }
.goi-y { margin: 8px 0 0; font-size: 12.5px; color: #5a6673; }
.khoi table { min-width: 760px; }
.khoi th, .khoi td { min-width: 122px; }
.khoi .nhan { min-width: 46px; position: sticky; left: 0; z-index: 1; }
.gv-tom { margin: 0 0 10px; font-size: 13.5px; color: #33404f; }
footer { margin-top: 22px; font-size: 12px; color: #7a8593; text-align: center; }
@media (max-width: 560px) {
  body { font-size: 14px; padding: 0 8px 30px; }
  h1 { font-size: 17px; }
  th, td { padding: 5px 4px; font-size: 12.5px; }
}
</style>
</head>
<body>

<header>
  <h1>__TIEU_DE__</h1>
  <p class="tuan" id="tuan"></p>
  <p class="xuat-luc" id="xuat-luc"></p>
</header>

<nav>
  <button data-che="lop">Theo lớp</button>
  <button data-che="gv">Theo giáo viên</button>
  <button data-che="khoi">Cả khối</button>
</nav>

<div class="chon-hop"><select id="o-chon"></select></div>
<div id="noi-dung"></div>

<footer>Trang chỉ để xem. Muốn đổi thời khoá biểu thì dùng phần mềm xếp TKB.</footer>

<script id="du-lieu" type="application/json">__DU_LIEU__</script>
<script>
/*JS-BAT-DAU*/
'use strict';
var D = JSON.parse(document.getElementById('du-lieu').textContent);
var cheDo = 'lop';
var dangChon = D.lop[0];

function ma(s) {
  return String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

/* Ô của (lớp, ngày, vị trí). D.o là mảng phẳng cho nhẹ file. */
var bang = {};
D.o.forEach(function (x) { bang[x[0] + '|' + x[1] + '|' + x[2]] = x; });
function oCua(lop, ngay, vitri) { return bang[lop + '|' + ngay + '|' + vitri]; }

function docDiaChi() {
  var h = decodeURIComponent(location.hash.replace(/^#/, ''));
  var m = h.match(/^(lop|gv)=(.*)$/);
  if (m) {
    cheDo = m[1];
    dangChon = m[2];
  } else if (h === 'khoi') {
    cheDo = 'khoi';
  }
}

function ghiDiaChi() {
  var h = cheDo === 'khoi' ? 'khoi' : cheDo + '=' + dangChon;
  if (decodeURIComponent(location.hash.replace(/^#/, '')) !== h) {
    location.hash = h;
  }
}

function veChonHop() {
  var o = document.getElementById('o-chon');
  var hop = document.querySelector('.chon-hop');
  if (cheDo === 'khoi') { hop.style.display = 'none'; return; }
  hop.style.display = '';
  var ds = cheDo === 'lop' ? D.lop : D.gv;
  if (ds.indexOf(dangChon) < 0) dangChon = ds[0];
  o.innerHTML = ds.map(function (x) {
    return '<option value="' + ma(x) + '"' + (x === dangChon ? ' selected' : '')
      + '>' + ma(cheDo === 'lop' ? x + ' — ' + (D.gvcn[x] || '') : x) + '</option>';
  }).join('');
}

function dauHang(i) { return i % D.cac_tiet.length === 0; }

function veTheoLop(lop) {
  var h = '<div class="cuon"><table><tr><th class="nhan">Tiết</th>'
        + D.cac_thu.map(function (t) { return '<th>Thứ ' + t + '</th>'; }).join('')
        + '</tr>';
  D.cac_tiet.forEach(function (tiet, p) {
    h += '<tr><td class="nhan">' + tiet + '</td>';
    D.cac_thu.forEach(function (t, d) {
      var o = oCua(lop, d, p);
      h += o ? '<td><span class="mon">' + ma(o[3]) + '</span>'
             + '<span class="phu">' + ma(o[4]) + '</span></td>'
             : '<td class="trong"></td>';
    });
    h += '</tr>';
  });
  h += '</table></div>';
  var so = D.o.filter(function (x) { return x[0] === lop; }).length;
  return '<p class="gv-tom"><b>' + ma(lop) + '</b> · GVCN ' + ma(D.gvcn[lop] || '')
       + ' · ' + so + ' tiết/tuần · buổi ' + ma(D.buoi) + '</p>' + h;
}

function veTheoGV(gv) {
  var cua = D.o.filter(function (x) { return x[4] === gv; });
  var ngay = {};
  cua.forEach(function (x) { ngay[x[1]] = true; });
  var h = '<div class="cuon"><table><tr><th class="nhan">Tiết</th>'
        + D.cac_thu.map(function (t) { return '<th>Thứ ' + t + '</th>'; }).join('')
        + '</tr>';
  D.cac_tiet.forEach(function (tiet, p) {
    h += '<tr><td class="nhan">' + tiet + '</td>';
    D.cac_thu.forEach(function (t, d) {
      var o = cua.filter(function (x) { return x[1] === d && x[2] === p; })[0];
      h += o ? '<td><span class="mon">' + ma(o[0]) + '</span>'
             + '<span class="phu">' + ma(o[3]) + '</span></td>'
             : '<td class="trong"></td>';
    });
    h += '</tr>';
  });
  h += '</table></div>';
  return '<p class="gv-tom"><b>' + ma(gv) + '</b> · ' + cua.length + ' tiết/tuần · '
       + Object.keys(ngay).length + ' buổi lên lớp</p>' + h;
}

function veCaKhoi() {
  var h = '<div class="cuon khoi"><table><tr><th class="nhan">Thứ</th>'
        + '<th class="nhan">Tiết</th>'
        + D.lop.map(function (l) {
            return '<th>' + ma(l) + '<span class="phu">' + ma(D.gvcn[l] || '')
                 + '</span></th>'; }).join('')
        + '</tr>';
  D.cac_thu.forEach(function (thu, d) {
    D.cac_tiet.forEach(function (tiet, p) {
      var cuoi = p === D.cac_tiet.length - 1;
      h += '<tr' + (cuoi ? ' class="het-ngay"' : '') + '>';
      if (p === 0) {
        h += '<td class="nhan" rowspan="' + D.cac_tiet.length + '">Thứ ' + thu
           + '</td>';
      }
      h += '<td class="nhan">' + tiet + '</td>';
      D.lop.forEach(function (l) {
        var o = oCua(l, d, p);
        h += o ? '<td><span class="mon">' + ma(o[3]) + '</span>'
               + '<span class="phu">' + ma(o[4]) + '</span></td>'
               : '<td class="trong"></td>';
      });
      h += '</tr>';
    });
  });
  h += '</table></div><p class="goi-y">Bảng rộng — vuốt ngang để xem hết các lớp. '
     + 'Trên điện thoại nên dùng chế độ <b>Theo lớp</b> cho dễ đọc.</p>';
  return h;
}

function ve() {
  document.querySelectorAll('nav button').forEach(function (n) {
    n.classList.toggle('chon', n.dataset.che === cheDo);
  });
  veChonHop();
  var n = document.getElementById('noi-dung');
  if (cheDo === 'lop') n.innerHTML = veTheoLop(dangChon);
  else if (cheDo === 'gv') n.innerHTML = veTheoGV(dangChon);
  else n.innerHTML = veCaKhoi();
  document.title = D.tieu_de + ' — ' + (cheDo === 'khoi' ? 'Cả khối' : dangChon);
}

document.querySelectorAll('nav button').forEach(function (n) {
  n.onclick = function () { cheDo = n.dataset.che; ghiDiaChi(); ve(); };
});
document.getElementById('o-chon').onchange = function (e) {
  dangChon = e.target.value; ghiDiaChi(); ve();
};
window.onhashchange = function () { docDiaChi(); ve(); };

document.getElementById('tuan').textContent = D.tuan;
document.getElementById('xuat-luc').textContent = 'Xuất lúc ' + D.xuat_luc
  + ' — nếu thấy ngày này cũ hơn tuần đang học thì hỏi lại nhà trường.';
docDiaChi();
ghiDiaChi();
ve();
/*JS-KET-THUC*/
</script>
</body>
</html>
'''


def du_lieu(bt, pa):
    """Gom dữ liệu cần cho trang xem. Ô ghi dạng mảng phẳng cho nhẹ file:
       [lop, ngay, vitri, mon, gv]."""
    from xep_tkb import nap                       # nạp muộn, tránh vòng import
    nap(bt, pa)
    o = []
    for c in bt.cac_cum:
        if c.la_trong:
            continue
        for p in range(c.vitri, c.vitri + c.size):
            o.append([c.lop, c.ngay, p, c.mon, c.gv])
    o.sort(key=lambda x: (x[1], x[2], bt.lop.index(x[0])))
    return {
        'tieu_de': bt.cfg['thong_tin']['tieu_de'],
        'tuan': bt.cfg['thong_tin']['tuan'],
        'xuat_luc': datetime.now().strftime('%H:%M ngày %d/%m/%Y'),
        'buoi': bt.buoi,
        'cac_thu': list(bt.cac_thu),
        'cac_tiet': list(bt.cac_tiet),
        'lop': list(bt.lop),
        'gvcn': {l: bt.thong_tin_lop[l]['gvcn'] for l in bt.lop},
        'gv': sorted({c.gv for c in bt.cac_cum if not c.la_trong}),
        'o': o,
    }


def xuat_html(bt, pa, duong_dan):
    """Ghi ra một file .html tự chứa. Trả về đường dẫn đã ghi."""
    d = du_lieu(bt, pa)
    js = json.dumps(d, ensure_ascii=False, separators=(',', ':'))
    js = js.replace('</', '<\\/')                 # đừng để chuỗi cắt ngang <script>
    trang = (TRANG.replace('__TIEU_DE__', d['tieu_de'])
                  .replace('__DU_LIEU__', js))
    with open(duong_dan, 'w', encoding='utf-8') as f:
        f.write(trang)
    return duong_dan

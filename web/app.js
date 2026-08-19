'use strict';
// Giao diện chỉ nói chuyện với máy chủ cục bộ qua mấy đường /api/... bên dưới.
// Không tải gì từ mạng, chạy được cả khi máy không có Internet.

const $ = (id) => document.getElementById(id);
let daLog = 0;        // đã hiện bao nhiêu dòng nhật ký
let dongHo = null;    // bộ đếm hỏi trạng thái
let quyTac = [];      // danh sách quy tắc đang hiện ở màn hình 3

// ---------------------------------------------------------------- chuyển màn
function moMan(ten) {
  const nut = document.querySelector(`.tab[data-man="${ten}"]`);
  if (!nut) return;
  document.querySelectorAll('.tab').forEach((x) => x.classList.remove('dang-chon'));
  document.querySelectorAll('.man').forEach((x) => x.classList.add('an'));
  nut.classList.add('dang-chon');
  $(ten).classList.remove('an');
  if (ten === 'man-quytac') { napQuyTac(); napDanhMuc(); }
}

document.querySelectorAll('.tab').forEach((nut) => {
  nut.onclick = () => { location.hash = nut.dataset.man; moMan(nut.dataset.man); };
});
// Tải lại trang thì vẫn ở đúng màn hình cũ.
window.onhashchange = () => moMan(location.hash.slice(1));

// ---------------------------------------------------------------- 1. xếp TKB
$('nut-xep').onclick = async () => {
  const than = {
    tuan: $('o-tuan').value,
    seed: $('o-seed').value,
    so_lan: $('o-lan').value,
    tat: quyTac.filter((r) => !r.bat).map((r) => r.i),
  };
  const tl = await fetch('/api/xep', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(than),
  });
  const kq = await tl.json();
  if (!tl.ok) { alert(kq.loi || 'Không gọi được máy chủ.'); return; }
  daLog = 0;
  $('log').textContent = '';
  $('hop-loi').classList.add('an');
  $('hop-ket-qua').classList.add('an');
  $('tien-do').classList.remove('an');
  $('nut-xep').disabled = true;
  $('nut-xep').textContent = 'Đang xếp...';
  batDauHoi();
};

function batDauHoi() {
  if (dongHo) clearInterval(dongHo);
  hoi();
  dongHo = setInterval(hoi, 700);
}

async function hoi() {
  let t;
  try { t = await (await fetch('/api/trang-thai?tu=' + daLog)).json(); }
  catch (e) { return; }

  if (t.log_moi && t.log_moi.length) {
    $('log').textContent += t.log_moi.join('\n') + '\n';
    $('log').scrollTop = $('log').scrollHeight;
    daLog = t.log_het;
  }

  if (t.dang_chay) {
    const pc = t.so_lan ? Math.min(100, Math.round((t.da_thu / t.so_lan) * 100)) : 0;
    $('thanh-chay').style.width = pc + '%';
    $('chu-tien-do').textContent =
      `Đang thử lần ${t.da_thu}/${t.so_lan} · ${t.hop_le} phương án hợp lệ · `
      + `còn khoảng ${t.con_giay} giây`;
  }

  if (t.xong) {
    clearInterval(dongHo); dongHo = null;
    $('nut-xep').disabled = false;
    $('nut-xep').textContent = 'Xếp thời khoá biểu';
    $('thanh-chay').style.width = '100%';
    $('chu-tien-do').textContent = t.loi
      ? 'Dừng vì có lỗi — xem khung đỏ bên dưới.'
      : `Xong: ${t.hop_le} phương án hợp lệ / ${t.da_thu} lần thử.`;
    if (t.loi) {
      $('chu-loi').textContent = t.loi;
      $('hop-loi').classList.remove('an');
    }
    veKetQua(t);
  }
}

function veKetQua(t) {
  if (t.bang && t.bang.length) {
    const dat = t.bang.length - t.so_loi;
    $('tom-tat').textContent = `— ${dat}/${t.bang.length} ĐẠT`
      + (t.diem !== null ? ` · điểm mềm ${t.diem}` : '');
    $('bang-doi-chieu').innerHTML =
      '<tr><th style="width:70px">Kết quả</th><th>Nội dung quy tắc</th>'
      + '<th style="width:38%">Ghi chú</th></tr>'
      + t.bang.map((r) =>
        `<tr><td class="${r.kq === 'ĐẠT' ? 'dat' : 'loi-o'}">${r.kq}</td>`
        + `<td>${ma(r.ten)}</td><td>${ma(r.ghi_chu)}</td></tr>`).join('');
    $('bang-diem').innerHTML =
      '<tr><th>Tiêu chí</th><th style="width:90px">Điểm</th></tr>'
      + Object.entries(t.diem_mem).map(([k, v]) =>
        `<tr><td>${ma(k)}</td><td style="text-align:right">${v}</td></tr>`).join('')
      + `<tr><th>Tổng</th><th style="text-align:right">${t.diem}</th></tr>`;
    $('hop-ket-qua').classList.remove('an');
  }
  if (t.luoi) { veTKB(t.luoi); }
  if (t.gv) { veGV(t.gv); }
}

// ---------------------------------------------------------------- 2. xem TKB
function veTKB(l) {
  $('chua-xep-1').classList.add('an');
  $('chu-tuan').textContent = l.tieu_de + ' — ' + l.tuan;
  let h = '<tr><th>Thứ</th><th>Buổi</th><th>Tiết</th>'
        + l.lop.map((x, j) => `<th>${x}<br><span class="o-gv">${ma(l.gvcn[j])}</span></th>`).join('')
        + '</tr>';
  l.hang.forEach((r, i) => {
    const cuoi = (i % 5) === 4;
    h += `<tr class="${cuoi ? 'het-ngay' : ''}">`;
    if (r.dau_ngay) {
      h += `<td class="nhan-ngay" rowspan="5">Thứ ${r.thu}</td>`
         + `<td class="nhan-ngay" rowspan="5">${ma(r.buoi)}</td>`;
    }
    h += `<td>${r.tiet}</td>`;
    h += r.o.map((o) => o
      ? `<td><span class="o-mon">${ma(o.mon)}</span><br>`
        + `<span class="o-gv">${ma(o.gv)}</span></td>`
      : '<td></td>').join('');
    h += '</tr>';
  });
  h += '<tr class="tong"><td colspan="3">TỔNG SỐ TIẾT/TUẦN</td>'
     + l.tong.map((x) => `<td>${x}</td>`).join('') + '</tr>';
  $('bang-tkb').innerHTML = h;
}

$('nut-tai').onclick = () => { window.location = '/api/tai-ve'; };
$('nut-tai-web').onclick = () => { window.location = '/api/tai-web'; };

// ---------------------------------------------------------------- 3. quy tắc
async function napQuyTac() {
  const d = await (await fetch('/api/quy-tac')).json();
  // giữ lại các công tắc người dùng vừa gạt, đừng nạp đè lên
  const daGat = new Map(quyTac.map((r) => [r.i, r.bat]));
  quyTac = d.quy_tac.map((r) => ({ ...r, bat: daGat.has(r.i) ? daGat.get(r.i) : r.bat }));
  veQuyTac();
  if (!$('o-tuan').value) $('o-tuan').placeholder = d.tuan;
}

function veQuyTac() {
  $('bang-quy-tac').innerHTML =
    '<tr><th style="width:90px">Dùng</th><th>Nội dung</th>'
    + '<th style="width:180px">Loại</th></tr>'
    + quyTac.map((r, k) =>
      `<tr class="${r.bat ? '' : 'tat'}">`
      + `<td><label class="cong-tac"><input type="checkbox" data-k="${k}" `
      + `${r.bat ? 'checked' : ''}> ${r.bat ? 'Bật' : 'Tắt'}</label></td>`
      + `<td>${ma(r.ghi_chu)}${r.mem ? ' <span class="mem">tiêu chí mềm</span>' : ''}`
      + `${r.moi ? ' <span class="moi">chưa lưu</span>' : ''}</td>`
      + `<td class="loai">${ma(r.loai)}`
      + (r.moi ? ` <button class="nut-xoa" data-xoa="${r.i}">Xoá</button>` : '')
      + '</td></tr>').join('');
  $('bang-quy-tac').querySelectorAll('input[type=checkbox]').forEach((o) => {
    o.onchange = () => { quyTac[+o.dataset.k].bat = o.checked; veQuyTac(); };
  });
  $('bang-quy-tac').querySelectorAll('[data-xoa]').forEach((o) => {
    o.onclick = async () => {
      const tl = await fetch('/api/xoa-quy-tac', {
        method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ i: +o.dataset.xoa }),
      });
      const kq = await tl.json();
      if (!tl.ok) { baoLoi(kq.loi || 'Không xoá được.'); return; }
      quyTac = kq.quy_tac.map((r) => ({ ...r }));
      veQuyTac();
    };
  });
}

// ---- form thêm quy tắc: dựng ô nhập từ TRUONG, không chép tay danh sách khoá ----
let DM = null;      // danh mục loại quy tắc, lấy từ /api/loai-quy-tac
let GT = null;      // giá trị chọn được, lấy từ /api/gia-tri

async function napDanhMuc() {
  if (DM) return;
  DM = await (await fetch('/api/loai-quy-tac')).json();
  GT = await (await fetch('/api/gia-tri')).json();
  $('o-loai').innerHTML = DM.nhom.map((n) =>
    `<optgroup label="${ma(n.nhom)}">`
    + n.loai.map((l) => `<option value="${ma(l.ten)}">${ma(l.ten)}</option>`).join('')
    + '</optgroup>').join('');
  $('o-loai').onchange = veTruong;
  veTruong();
}

function loaiDangChon() {
  const t = $('o-loai').value;
  for (const n of DM.nhom) for (const l of n.loai) if (l.ten === t) return l;
  return null;
}

/* Hai cách chọn nhiều giá trị. Cả hai đều dựng bằng checkbox thật nên đọc
   giá trị chỉ có MỘT đường: docNhieu(). Không cho gõ tay, vì gõ sai tên giờ
   làm chương trình dừng hẳn. */

let demO = 0;

/* Danh sách NGẮN và cố định (thứ, tiết): dãy ô vuông bấm bật/tắt. */
function oNut(ds, daChon, khoa, nhan) {
  const c = [].concat(daChon === undefined ? [] : daChon).map(String);
  return `<div class="o-nut" data-o="${khoa}" data-nhieu="1">` + ds.map((x) => {
    const id = 'n' + (++demO);
    const co = c.includes(String(x));
    return `<label class="nut-o${co ? ' chon' : ''}" for="${id}">`
      + `<input type="checkbox" id="${id}" value="${ma(x)}"${co ? ' checked' : ''}>`
      + `${ma(nhan ? nhan(x) : x)}</label>`;
  }).join('') + '</div>';
}

/* Danh sách DÀI (28 giáo viên, 14 môn...): danh sách cuộn + ô tìm kiếm. */
function oDs(ds, daChon, khoa) {
  const c = [].concat(daChon === undefined ? [] : daChon).map(String);
  return `<div data-o="${khoa}" data-nhieu="1">`
    + `<input type="search" class="tim" placeholder="gõ để lọc nhanh...">`
    + '<div class="ds-chon">' + ds.map((x) => {
        const id = 'd' + (++demO);
        const co = c.includes(String(x));
        return `<label class="dong" for="${id}">`
          + `<input type="checkbox" id="${id}" value="${ma(x)}"${co ? ' checked' : ''}>`
          + `<span>${ma(x)}</span></label>`;
      }).join('') + '</div>'
    + `<p class="dem-chon">Đang chọn: <b>0</b> / ${ds.length}</p></div>`;
}

/* Đọc giá trị — dùng chung cho cả hai kiểu trên. */
function docNhieu(hop, khoa) {
  const c = hop.querySelector(`[data-o="${khoa}"][data-nhieu]`);
  if (!c) return [];
  return [...c.querySelectorAll('input[type=checkbox]:checked')].map((x) => x.value);
}

/* Bật/tắt màu ô vuông, lọc danh sách dài, đếm số đang chọn. */
function noiSuKien(goc) {
  goc.querySelectorAll('.nut-o input').forEach((o) => {
    o.onchange = () => o.closest('.nut-o').classList.toggle('chon', o.checked);
  });
  goc.querySelectorAll('[data-nhieu] .ds-chon').forEach((d) => {
    const hop = d.parentElement;
    const dem = () => {
      const n = d.querySelectorAll('input:checked').length;
      hop.querySelector('.dem-chon b').textContent = n;
    };
    d.querySelectorAll('input').forEach((o) => { o.onchange = dem; });
    dem();
    const tim = hop.querySelector('.tim');
    if (tim) {
      tim.oninput = () => {
        const t = tim.value.trim().toLowerCase();
        d.querySelectorAll('.dong').forEach((x) => {
          x.classList.toggle('an', t && !x.textContent.toLowerCase().includes(t));
        });
      };
    }
  });
}

function oMot(ds, daChon, khoa, trong) {
  return `<select data-o="${khoa}"><option value="">${ma(trong || '— bỏ trống —')}</option>`
    + ds.map((x) => `<option value="${ma(x)}"${String(x) === String(daChon)
        ? ' selected' : ''}>${ma(x)}</option>`).join('') + '</select>';
}

/* Bộ lọc dùng chung cho "loc", "a", "b" và cho cả "tru" lồng bên trong. */
function veLoc(khoa, gt, cho_tru) {
  gt = gt || {};
  const h = ['<div class="loc-o">'
    + '<label>Môn' + oDs(GT.mon, gt.mon, khoa + '.mon') + '</label>'
    + '<label>Nhóm môn' + oDs(GT.nhom_mon, gt.nhom_mon, khoa + '.nhom_mon') + '</label>'
    + '<label>Giáo viên' + oDs(GT.gv, gt.gv, khoa + '.gv') + '</label>'
    + '<label>Lớp' + oNut(GT.lop, gt.lop, khoa + '.lop') + '</label>'
    + '<label>Chuyên đề'
    + oMot(['true', 'false'], gt.la_chuyen_de === undefined ? '' : String(gt.la_chuyen_de),
           khoa + '.la_chuyen_de', '— cả hai —') + '</label>'
    + '</div>'];
  if (cho_tru) {
    const t = gt.tru || null;
    h.push('<div class="tru-hop"><label class="cong-tac">'
      + `<input type="checkbox" data-tru="${khoa}"${t ? ' checked' : ''}> `
      + 'Trừ ra một số trường hợp (khoá "tru")</label>'
      + `<div data-tru-hop="${khoa}"${t ? '' : ' class="an"'}>`
      + veLoc(khoa + '.tru', t, false) + '</div></div>');
  }
  return h.join('');
}

function veTruong() {
  const l = loaiDangChon();
  if (!l) return;
  $('mo-ta-loai').textContent = l.mo_ta;
  if (!$('o-ghi-chu').value.trim()) $('o-ghi-chu').value = l.vi_du.ghi_chu || '';
  const nhomDa = {};
  $('o-truong').className = 'o-truong';
  $('o-truong').innerHTML = l.truong.map((tr) => {
    const gt = l.vi_du[tr.ten];
    const co = gt !== undefined;
    let than = '';
    if (tr.kieu === 'loc') than = veLoc(tr.ten, gt, true);
    else if (tr.kieu === 'ds_thu')
      than = oNut(GT.thu, gt, tr.ten, (x) => 'Thứ ' + x);
    else if (tr.kieu === 'ds_tiet')
      than = oNut(GT.tiet, gt, tr.ten, (x) => 'Tiết ' + x);
    else if (tr.kieu === 'ds_tiet_buoi')
      than = oNut(GT.tiet_trong_buoi, gt, tr.ten, (x) => 'Tiết thứ ' + x);
    else if (tr.kieu === 'so_thu') than = oMot(GT.thu, gt, tr.ten);
    else if (tr.kieu === 'so_tiet') than = oMot(GT.tiet, gt, tr.ten);
    else if (tr.kieu === 'so_tiet_buoi') than = oMot(GT.tiet_trong_buoi, gt, tr.ten);
    else if (tr.kieu === 'chon') than = oMot(tr.chon || [], gt, tr.ten);
    else if (tr.kieu === 'dung_sai')
      than = `<label class="cong-tac"><input type="checkbox" data-o="${tr.ten}"`
           + `${gt ? ' checked' : ''}> có</label>`;
    else if (tr.kieu === 'so')
      than = `<input type="number" data-o="${tr.ten}" value="${co ? gt : ''}">`;
    else if (tr.kieu === 'ds_so')
      than = `<input type="text" data-o="${tr.ten}" data-ds-so="1" `
           + `value="${co ? gt.join(', ') : ''}" placeholder="vd 2, 1">`;
    else if (tr.kieu === 'ds_o')
      than = veDsO(tr.ten, gt);
    const nhac = tr.nhom
      ? '<span class="nhac">Chọn MỘT trong hai cách ghi tiết — bỏ trống cách kia.</span>'
      : '';
    if (tr.nhom) nhomDa[tr.nhom] = true;
    return `<div class="truong${tr.bat_buoc && !tr.nhom ? ' bat-buoc' : ''}`
      + `${tr.nhom ? ' thay-the' : ''}" data-truong="${tr.ten}" `
      + `data-kieu="${tr.kieu}">`
      + `<span class="ten">${ma(tr.nhan)}</span>${nhac}`
      + `<span class="kieu">"${ma(tr.ten)}" — ${ma(DM.kieu[tr.kieu] || tr.kieu)}</span>`
      + than + '</div>';
  }).join('');
  noiSuKien($('o-truong'));
  $('o-truong').querySelectorAll('input[data-tru]').forEach((o) => {
    o.onchange = () => {
      const h = $('o-truong').querySelector(`[data-tru-hop="${o.dataset.tru}"]`);
      h.classList.toggle('an', !o.checked);
    };
  });
}

document.addEventListener('click', (e) => {
  const n = e.target.closest && e.target.closest('[data-them-o]');
  if (!n) return;
  const hop = $('o-truong').querySelector(`[data-ds-o="${n.dataset.themO}"]`);
  const d = document.createElement('div');
  d.className = 'loc-o';
  d.style.marginBottom = '6px';
  d.innerHTML = '<label>Thứ' + oMot(GT.thu, GT.thu[0], '', '—') + '</label>'
              + '<label>Tiết' + oMot(GT.tiet, GT.tiet[0], '', '—') + '</label>';
  hop.appendChild(d);
  noiSuKien(hop);
});

function veDsO(khoa, gt) {
  const ds = gt && gt.length ? gt : [[GT.thu[0], GT.tiet[0]]];
  return `<div data-ds-o="${khoa}">` + ds.map((c) =>
    '<div class="loc-o" style="margin-bottom:6px">'
    + '<label>Thứ' + oMot(GT.thu, c[0], '', '—') + '</label>'
    + '<label>Tiết' + oMot(GT.tiet, c[1], '', '—') + '</label></div>').join('')
    + '</div><button type="button" class="nut-xoa" data-them-o="' + khoa
    + '">+ thêm một ô</button>';
}

/* Gom giá trị trên form thành đúng khối JSON của một quy tắc. */
function docForm() {
  const l = loaiDangChon();
  const r = { loai: l.ten, ghi_chu: $('o-ghi-chu').value.trim() };
  l.truong.forEach((tr) => {
    const hop = $('o-truong').querySelector(`[data-truong="${tr.ten}"]`);
    if (!hop) return;
    if (tr.kieu === 'loc') {
      const v = docLoc(hop, tr.ten);
      if (v) r[tr.ten] = v;
    } else if (tr.kieu === 'ds_o') {
      const ds = [];
      hop.querySelectorAll('[data-ds-o] .loc-o').forEach((d) => {
        const o = d.querySelectorAll('select');
        if (o[0].value && o[1].value) ds.push([+o[0].value, +o[1].value]);
      });
      if (ds.length) r[tr.ten] = ds;
    } else {
      const o = hop.querySelector(`[data-o="${tr.ten}"]`);
      if (!o) return;
      if (o.dataset.nhieu !== undefined) {
        const v = docNhieu(hop, tr.ten).map(so);
        if (v.length) r[tr.ten] = v;
        return;
      }
      if (o.type === 'checkbox') { if (o.checked) r[tr.ten] = true; return; }
      if (o.dataset.dsSo !== undefined) {
        const v = o.value.split(',').map((x) => +x.trim()).filter((x) => x > 0);
        if (v.length) r[tr.ten] = v;
        return;
      }
      if (o.value !== '') r[tr.ten] = so(o.value);
    }
  });
  return r;
}

function docLoc(hop, tien) {
  const d = {};
  ['mon', 'nhom_mon', 'gv', 'lop'].forEach((k) => {
    const v = docNhieu(hop, tien + '.' + k);
    if (v.length) d[k] = v.length === 1 ? v[0] : v;
  });
  const cd = hop.querySelector(`[data-o="${tien}.la_chuyen_de"]`);
  if (cd && cd.value) d.la_chuyen_de = cd.value === 'true';
  const t = hop.querySelector(`[data-tru="${tien}"]`);
  if (t && t.checked) {
    const con = docLoc(hop.querySelector(`[data-tru-hop="${tien}"]`), tien + '.tru');
    if (con) d.tru = con;
  }
  return Object.keys(d).length ? d : null;
}

function so(v) { return /^-?\d+$/.test(v) ? +v : v; }

function baoLoi(chu) {
  $('chu-them').textContent = chu;
  $('chu-them').classList.toggle('an', !chu);
}

$('nut-them').onclick = async () => {
  baoLoi('');
  $('ket-qua-thu').classList.add('an');
  if (!$('o-ghi-chu').value.trim()) {
    baoLoi('Chưa điền "Nội dung quy tắc". Câu này hiện trên bảng đối chiếu '
         + 'nên không được để trống.');
    return;
  }
  const tl = await fetch('/api/them-quy-tac', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ quy_tac: docForm() }),
  });
  const kq = await tl.json();
  if (!tl.ok) { baoLoi(kq.loi || 'Không thêm được.'); return; }
  quyTac = kq.quy_tac.map((r) => ({ ...r }));
  veQuyTac();
  $('o-ghi-chu').value = '';
  $('chu-luu').textContent = 'Đã thêm vào danh sách (chưa lưu xuống file).';
};

$('nut-thu').onclick = async () => {
  baoLoi('');
  const n = $('nut-thu');
  n.disabled = true; n.textContent = 'Đang thử...';
  try {
    const tl = await fetch('/api/thu-quy-tac', {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ quy_tac: docForm(),
                             tat: quyTac.filter((r) => !r.bat).map((r) => r.i) }),
    });
    const kq = await tl.json();
    if (!tl.ok) { baoLoi(kq.loi || 'Không thử được.'); return; }
    const h = $('ket-qua-thu');
    h.classList.remove('an');
    if (kq.xep_duoc) {
      h.className = 'thu-hop thu-ok';
      h.innerHTML = `<b>Vẫn xếp được.</b> ${kq.so_hop_le}/${kq.so_lan} lần thử ra `
        + `phương án hợp lệ trong ${kq.giay} giây, điểm mềm ${kq.diem}.`;
    } else if (kq.co_loi_giai) {
      h.className = 'thu-hop thu-canh-bao';
      h.innerHTML = '<b>Xếp ra được nhưng không phương án nào thoả hết quy tắc.</b>'
        + `<br>${kq.so_lan} lần thử, 0 phương án hợp lệ. Đang vi phạm:<ul>`
        + kq.vi_pham.map((v) => `<li>${ma(v.ten)}</li>`).join('') + '</ul>'
        + 'Nên nới bớt một trong những quy tắc trên. Vẫn thêm được nếu bạn muốn.';
    } else {
      h.className = 'thu-hop thu-canh-bao';
      h.innerHTML = '<b>KHÔNG xếp được lần nào.</b> '
        + `${kq.so_lan} lần thử đều không ra lời giải.<br>`
        + 'Quy tắc này nhiều khả năng mâu thuẫn với quy tắc đang có — nên nới bớt '
        + 'điều kiện (ít lớp hơn, nhiều thứ/tiết hơn), hoặc tắt tạm một quy tắc '
        + 'khác ở bảng trên. Vẫn thêm được nếu bạn muốn giữ lại.';
    }
  } finally {
    n.disabled = false; n.textContent = 'Thử quy tắc này';
  }
};

$('nut-luu').onclick = async () => {
  const tat = quyTac.filter((r) => !r.bat).map((r) => r.i);
  if (!confirm('Ghi cờ bật/tắt vào cauhinh.json?\n'
             + 'Bản cũ sẽ được sao lưu thành cauhinh.bak.json.')) return;
  const tl = await fetch('/api/luu-quy-tac', {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ tat }),
  });
  const kq = await tl.json();
  $('chu-luu').textContent = tl.ok
    ? `Đã ghi. ${kq.doi} quy tắc đổi trạng thái. Bản cũ: ${kq.sao_luu}`
    : 'Lỗi: ' + (kq.loi || '');
};

// ---------------------------------------------------------- 4. lịch giáo viên
let duLieuGV = null;

function veGV(g) {
  duLieuGV = g;
  $('chua-xep-2').classList.add('an');
  locGV();
}

function locGV() {
  if (!duLieuGV) return;
  const tu = ($('o-loc-gv').value || '').trim().toLowerCase();
  const ds = duLieuGV.gv.filter((r) => !tu || r.gv.toLowerCase().includes(tu));
  $('bang-gv').innerHTML =
    '<tr><th>Giáo viên</th><th>Số tiết</th><th>Số buổi</th>'
    + duLieuGV.cot.map((c) => `<th>${c.replace('/', '<br>')}</th>`).join('') + '</tr>'
    + ds.map((r) =>
      `<tr><td class="ten-gv">${ma(r.gv)}</td><td>${r.so_tiet}</td>`
      + `<td>${r.so_buoi}</td>`
      + r.o.map((o) => o
        ? `<td>${ma(o.lop)}<br><span class="o-gv">${ma(o.mon)}</span></td>`
        : '<td></td>').join('') + '</tr>').join('');
}

$('o-loc-gv').oninput = locGV;

// ---------------------------------------------------------------- tiện ích
function ma(s) {
  return String(s === null || s === undefined ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
}

// Lần đầu mở trang: nạp quy tắc và lấy kết quả của lượt chạy trước (nếu có).
if (location.hash.length > 1) moMan(location.hash.slice(1));
napQuyTac();
hoi();

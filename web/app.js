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
  if (ten === 'man-quytac') napQuyTac();
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
      + `<td>${ma(r.ghi_chu)}${r.mem ? ' <span class="mem">tiêu chí mềm</span>' : ''}</td>`
      + `<td class="loai">${ma(r.loai)}</td></tr>`).join('');
  $('bang-quy-tac').querySelectorAll('input[type=checkbox]').forEach((o) => {
    o.onchange = () => { quyTac[+o.dataset.k].bat = o.checked; veQuyTac(); };
  });
}

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

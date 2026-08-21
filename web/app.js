'use strict';
// Giao diện chỉ nói chuyện với máy chủ cục bộ qua mấy đường /api/... bên dưới.
// Không tải gì từ mạng, chạy được cả khi máy không có Internet.

// ---------------------------------------------------------------- phễu gọi API
// MỌI lời gọi API đi qua ĐÚNG hàm này. Trước đây có 9 chỗ fetch rải rác, trong
// đó 4 chỗ (hoi, napQuyTac, napDanhMuc x2) KHÔNG kiểm tl.ok — mà thân của 401
// lại LÀ JSON hợp lệ, nên .json() chạy lọt rồi mới ném TypeError ở dòng sau:
// màn hình trắng trơn, không một chữ giải thích. Ở hoi() thì cú ném đó còn rơi
// vào catch(e){return} và bị nuốt sạch — thanh tiến độ đứng im vĩnh viễn.
//
// Bất biến kiểm được rẻ tiền: cả tệp này chỉ được có ĐÚNG MỘT chữ "fetch(".
let viecCho = null;         // việc vừa trượt vì hết phiên, chạy lại sau khi vào

async function goi(duong, than, tuyChon) {
  const opt = than === undefined
    ? {}
    : { method: 'POST', headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(than) };
  const tl = await fetch(duong, opt);
  if (tuyChon && tuyChon.laDangNhap) {
    // Ba đường xác thực KHÔNG đi qua nhánh bắt 401 — 401 ở đó nghĩa là "sai
    // mật khẩu", không phải "hết phiên"; xử như hết phiên là đệ quy vô tận.
    let dd = null;
    try { dd = await tl.json(); } catch (e) { dd = null; }
    return { ma: tl.status, ok: tl.ok, d: dd };
  }
  if (tl.status === 401 || tl.status === 503) {
    if (tuyChon && tuyChon.lai) viecCho = tuyChon.lai;
    hienDangNhap(tl.status === 503
      ? 'Máy chủ chưa có tài khoản nào. Xem cửa sổ dòng lệnh.'
      : null);
    throw { hetPhien: true };
  }
  let d = null;
  try { d = await tl.json(); } catch (e) { d = null; }
  return { ma: tl.status, ok: tl.ok, d: d };
}

// Vỏ mỏng cho những chỗ đang dùng kiểu "tl.ok / await tl.json()" của fetch.
async function goiCu(duong, than) {
  let r;
  try { r = await goi(duong, than === undefined ? {} : than); }
  catch (e) { return { ok: false, json: async () => ({ loi: '' }) }; }
  return { ok: r.ok, json: async () => r.d || {} };
}

function hienDangNhap(loi) {
  const m = $('man-dang-nhap');
  if (m.classList.contains('an')) m.classList.remove('an');
  if (loi) { $('loi-dang-nhap').textContent = loi;
             $('loi-dang-nhap').classList.remove('an'); }
  const o = $('o-mat-khau'); if (o) { o.value = ''; o.focus(); }
}

function anDangNhap(ten) {
  $('man-dang-nhap').classList.add('an');
  $('loi-dang-nhap').classList.add('an');
  $('chu-nguoi').textContent = ten ? `Đang đăng nhập: ${ten}` : '';
  $('nut-dang-xuat').classList.toggle('an', !ten);
}

const $ = (id) => document.getElementById(id);
let daLog = 0;        // đã hiện bao nhiêu dòng nhật ký
let dongHo = null;    // bộ đếm hỏi trạng thái
let quyTac = [];      // danh sách quy tắc đang hiện ở màn hình 3
let dauCauHinh = null; // 2C — dấu bản của cauhinh.json lúc TẢI danh sách về
let dauKetQua = null;  // QĐ 4 — dấu bản của lượt xếp đang hiện trên màn hình

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
  let r;
  try { r = await goi('/api/xep', than, { lai: () => $('nut-xep').onclick() }); }
  catch (e) { return; }
  if (!r.ok) { alert((r.d && r.d.loi) || 'Không gọi được máy chủ.'); return; }
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
  try { t = (await goi('/api/trang-thai?tu=' + daLog)).d; }
  catch (e) {
    // Hết phiên giữa lượt xếp: DỪNG hỏi, nếu không nó nện 401 mỗi 0,7 giây.
    // Máy chủ vẫn xếp tiếp, kết quả không mất — đăng nhập lại là thấy.
    if (e && e.hetPhien) { clearInterval(dongHo); dongHo = null; daLog = 0; }
    return;
  }
  if (!t) return;
  dauKetQua = t.dau || null;
  const c = $('chu-nguoi-xep');
  if (t.nguoi) {
    c.textContent = 'Kết quả này do ' + t.nguoi + ' xếp.';
    c.classList.remove('an');
  } else {
    c.classList.add('an');
  }

  if (t.log_moi && t.log_moi.length) {
    $('log').textContent += t.log_moi.join('\n') + '\n';
    $('log').scrollTop = $('log').scrollHeight;
    daLog = t.log_het;
  }

  if (t.dang_chay) {
    const pc = t.so_lan ? Math.min(100, Math.round((t.da_thu / t.so_lan) * 100)) : 0;
    $('thanh-chay').style.width = pc + '%';
    // con_giay là null khi chạy chế độ tái lập (không có giới hạn thời gian
    // nên không đếm ngược được) — lúc đó bỏ hẳn vế đếm ngược, đừng hiện "null".
    const dem = (t.con_giay === null || t.con_giay === undefined)
      ? '' : ` · còn khoảng ${t.con_giay} giây`;
    $('chu-tien-do').textContent =
      `Đang thử lần ${t.da_thu}/${t.so_lan} · ${t.hop_le} phương án hợp lệ`
      + dem;
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

// Đính dấu bản của lượt xếp ĐANG HIỆN trên màn hình. Máy chủ so với dấu của
// tệp đang nằm trên đĩa; lệch nghĩa là có người vừa xếp đè, và nó chặn kèm tên
// người đó. Chưa xếp lần nào thì dauKetQua là null -> không đính gì, máy chủ
// cho tải (tệp của lượt chạy trước).
const kemDau = (d) => (dauKetQua ? d + '?dau=' + encodeURIComponent(dauKetQua) : d);
$('nut-tai').onclick = () => { window.location = kemDau('/api/tai-ve'); };
$('nut-tai-web').onclick = () => { window.location = kemDau('/api/tai-web'); };

// ---------------------------------------------------------------- 3. quy tắc
async function napQuyTac() {
  let d;
  try { d = (await goi('/api/quy-tac', undefined, { lai: napQuyTac })).d; }
  catch (e) { return; }
  if (!d) return;
  // giữ lại các công tắc người dùng vừa gạt, đừng nạp đè lên
  const daGat = new Map(quyTac.map((r) => [r.i, r.bat]));
  quyTac = d.quy_tac.map((r) => ({ ...r, bat: daGat.has(r.i) ? daGat.get(r.i) : r.bat }));
  dauCauHinh = d.dau;          // gửi lại y nguyên lúc bấm Lưu
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
      const tl = await goiCu('/api/xoa-quy-tac', { i: +o.dataset.xoa });
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
  // Gán CẢ HAI cùng lúc: nếu phiên hết hạn giữa hai lời gọi thì DM có mà GT
  // không, và màn hình Quy tắc kẹt vĩnh viễn ở trạng thái nửa vời.
  let dm, gt;
  try {
    dm = (await goi('/api/loai-quy-tac', undefined, { lai: napDanhMuc })).d;
    gt = (await goi('/api/gia-tri', undefined, { lai: napDanhMuc })).d;
  } catch (e) { return; }
  if (!dm || !gt) return;
  DM = dm; GT = gt;
  $('o-loai').innerHTML = DM.nhom.map((n) =>
    `<optgroup label="${ma(n.nhom)}">`
    // Ô chọn hiện NHÃN TIẾNG VIỆT, không hiện tên kỹ thuật. Tên kỹ thuật
    // xuống dòng #ten-ky-thuat ngay dưới — thầy cô còn đối chiếu cauhinh.json
    // bằng Notepad, nên không được giấu hẳn nó đi.
    + n.loai.map((l) =>
        `<option value="${ma(l.ten)}">${ma(l.nhan || l.ten)}</option>`).join('')
    + '</optgroup>').join('');
  $('o-loai').onchange = () => { veTruong(); henDocLai(); };
  $('o-ghi-chu').oninput = henDocLai;
  // Bắt Ở KHUNG CHA, không gắn vào từng ô: veTruong() vẽ lại toàn bộ ô nhập
  // mỗi lần đổi loại, nên gắn vào từng ô là gắn xong lại mất.
  $('o-truong').addEventListener('input', henDocLai);
  $('o-truong').addEventListener('change', henDocLai);
  veTruong();
  henDocLai();
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
  $('ten-ky-thuat').textContent = 'tên trong cauhinh.json:  "loai": "' + l.ten + '"';
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
// -------------------------------------------------- Đợt 3 việc 1: đọc lại
// Câu do MÁY CHỦ sinh, không sinh ở đây: ngữ nghĩa của 17 loại nằm trong
// quy_tac.py, chép sang JS là chắc chắn lệch — cùng lý do TRUONG phục vụ cả
// "--quy-tac" lẫn form web từ một chỗ.
let hoDocLai = null;

function henDocLai() {
  // Hoãn 300ms: gõ từng phím mà bắn từng lượt thì vừa phí vừa nhấp nháy.
  clearTimeout(hoDocLai);
  hoDocLai = setTimeout(docLai, 300);
}

async function docLai() {
  const khung = $('doc-lai');
  let r;
  try { r = docForm(); } catch (e) { khung.classList.add('an'); return; }
  if (!r || !r.loai) { khung.classList.add('an'); return; }
  let d;
  try {
    d = (await goi('/api/thu-quy-tac', { doc_lai: true, quy_tac: r })).d;
  } catch (e) { return; }
  if (!d) return;
  const cb = $('doc-lai-canh-bao');
  if (d.cau) {
    khung.className = 'thu-hop ' + (d.canh_bao ? 'thu-canh-bao' : 'thu-ok');
    $('doc-lai-cau').innerHTML =
      '<b>Máy hiểu câu này là:</b><br>' + ma(d.cau);
    cb.textContent = d.canh_bao || '';
    cb.classList.toggle('an', !d.canh_bao);
    khung.classList.remove('an');
  } else {
    khung.classList.add('an');
  }
}

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
  const tl = await goiCu('/api/them-quy-tac', { quy_tac: docForm() });
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
    const tl = await goiCu('/api/thu-quy-tac',
      { quy_tac: docForm(),
        tat: quyTac.filter((r) => !r.bat).map((r) => r.i) });
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

// -------------------------------------------------- cảnh báo sớm sau khi Lưu
// VÌ SAO CẢNH BÁO chứ không CHẶN: nút Lưu là thao tác thầy cô làm hằng ngày.
// Bắt nó đợi 1-9 giây thì họ tưởng máy treo rồi bấm lại — sinh ra đúng cái
// tranh chấp hai lượt vừa bịt. Và chặn oan (cấu hình khó nhưng vẫn có nghiệm)
// thì tệ hơn nữa: bị từ chối mà không hiểu vì sao, không có cách tự gỡ.
// Nên: LƯU LUÔN, rồi kiểm ở NỀN và nói ra.
//
// KHÔNG BAO GIỜ nói "vô nghiệm" khi máy chủ trả vet_can = false. Một giây
// không đủ để khẳng định điều đó; nói quá một lần là thầy cô thôi tin mọi
// cảnh báo sau.
let nghiPhamCuoi = [];          // quy tắc vừa được Lưu — nghi phạm đầu tiên

// Nút gỡ nhanh nằm SẴN trong index.html chứ không dựng bằng innerHTML: mọi id
// mà JS gọi tới đều phải có trong HTML — tests/thu_web.py canh đúng bất biến đó,
// và nó vừa bắt được bản đầu của hàm này.
function hienCanhBao(lop, html, nhanNut, hienTaiLai) {
  const h = $('canh-bao-luu');
  h.className = 'thu-hop ' + lop;
  $('canh-bao-chu').innerHTML = html;
  const g = $('nut-go-nhanh');
  g.textContent = nhanNut || '';
  g.disabled = false;
  g.classList.toggle('an', !nhanNut);
  $('nut-tai-lai-ds').classList.toggle('an', !hienTaiLai);
  h.classList.remove('an');
}

async function kiemNhanhSauLuu() {
  const ds = nghiPhamCuoi;
  hienCanhBao('thu-cho', 'Đang kiểm nhanh xem còn xếp được không...', '');
  let kq;
  try {
    const tl = await goiCu('/api/thu-quy-tac',
      { nhanh: true, tat: quyTac.filter((r) => !r.bat).map((r) => r.i) });
    kq = await tl.json();
    if (!tl.ok) throw new Error(kq.loi || '');
  } catch (e) {
    hienCanhBao('thu-canh-bao',
      '<b>Chưa kiểm được.</b> Đã lưu xong, nhưng lượt kiểm nhanh không chạy '
      + 'được. Bấm <b>Xếp thời khoá biểu</b> ở màn hình 1 để biết chắc.');
    return;
  }
  if (kq.co_loi_giai) {
    hienCanhBao('thu-ok',
      `<b>Đã lưu — vẫn xếp được.</b> Kiểm nhanh ${kq.giay} giây, tìm được `
      + 'phương án ngay.');
    return;
  }
  const ten = ds.length
    ? '<br>Nghi phạm đầu tiên là quy tắc vừa lưu:<ul>'
      + ds.map((r) => `<li>${ma(r.ghi_chu)} <span class="loai">${ma(r.loai)}</span></li>`)
        .join('') + '</ul>'
    : '<br>Lần Lưu này không thêm quy tắc mới nào — hãy xem lại các công tắc '
      + 'vừa gạt.';
  const nhanNut = ds.length
    ? `Tắt ${ds.length} quy tắc vừa lưu rồi thử lại` : '';
  if (kq.vet_can) {
    hienCanhBao('thu-loi',
      '<b>Đã lưu, nhưng cấu hình này CHẮC CHẮN KHÔNG xếp được.</b> Bộ giải đã '
      + `vét cạn mọi khả năng trong ${kq.giay} giây.` + ten, nhanNut);
  } else {
    hienCanhBao('thu-canh-bao',
      `<b>Đã lưu, nhưng ĐÁNG NGỜ.</b> Kiểm nhanh ${kq.giay} giây không tìm được `
      + 'phương án nào. Cấu hình bình thường tìm ra ngay trong khoảng 0,1 giây, '
      + 'nên đây là dấu hiệu xấu — <b>nhưng một giây thì chưa đủ để khẳng định '
      + 'là vô nghiệm.</b> Muốn biết chắc thì bấm <b>Xếp thời khoá biểu</b> ở '
      + 'màn hình 1.' + ten, nhanNut);
  }
}

$('nut-go-nhanh').onclick = async () => {
  const ds = nghiPhamCuoi;
  if (!ds.length) return;
  const g = $('nut-go-nhanh');
  g.disabled = true;
  const bo = new Set(ds.map((r) => r.i));
  quyTac.forEach((r) => { if (bo.has(r.i)) r.bat = false; });
  veQuyTac();
  const tl = await goiCu('/api/luu-quy-tac',
    { tat: quyTac.filter((r) => !r.bat).map((r) => r.i) });
  const k2 = await tl.json();
  $('chu-luu').textContent = tl.ok
    ? `Đã tắt ${bo.size} quy tắc và ghi lại. Bản cũ: ${k2.sao_luu}`
    : 'Lỗi: ' + (k2.loi || '');
  nghiPhamCuoi = [];
  napQuyTac();
  kiemNhanhSauLuu();
};

$('nut-luu').onclick = async () => {
  const tat = quyTac.filter((r) => !r.bat).map((r) => r.i);
  if (!confirm('Ghi cờ bật/tắt vào cauhinh.json?\n'
             + 'Bản cũ sẽ được sao lưu thành cauhinh.bak.json.')) return;
  // CHỤP nghi phạm TRƯỚC khi lưu: sau khi lưu thì cờ "moi" biến mất hết.
  nghiPhamCuoi = quyTac.filter((r) => r.moi).map((r) => ({ ...r }));
  let r;
  try {
    r = await goi('/api/luu-quy-tac', { tat, dau: dauCauHinh });
  } catch (e) { return; }
  const kq = r.d || {};
  if (r.ma === 409) {
    // 2C — có người vừa đổi tệp. KHÔNG ghi đè, và cho đúng một nút để đi tiếp.
    $('chu-luu').textContent = '';
    hienCanhBao('thu-loi', ma(kq.loi || 'Tệp đã đổi.'), '', true);
    return;
  }
  $('chu-luu').textContent = r.ok
    ? `Đã ghi. ${kq.doi} quy tắc đổi trạng thái. Bản cũ: ${kq.sao_luu}`
    : 'Lỗi: ' + (kq.loi || '');
  if (!r.ok) { $('canh-bao-luu').classList.add('an'); return; }
  dauCauHinh = kq.dau || dauCauHinh;   // lưu tiếp được, khỏi phải tải lại
  napQuyTac();
  kiemNhanhSauLuu();          // KHÔNG await: nút Lưu đã xong, khung tự hiện sau
};

$('nut-tai-lai-ds').onclick = async () => {
  $('nut-tai-lai-ds').disabled = true;
  await napQuyTac();                   // lấy danh sách và DẤU MỚI
  $('canh-bao-luu').classList.add('an');
  $('nut-tai-lai-ds').disabled = false;
  $('chu-luu').textContent = 'Đã tải lại danh sách mới nhất. Xem lại rồi Lưu.';
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

// ---------------------------------------------------------------- đăng nhập
$('form-dang-nhap').onsubmit = async (e) => {
  e.preventDefault();
  const nut = $('nut-dang-nhap');
  nut.disabled = true; nut.textContent = 'Đang kiểm...';
  let tl;
  try {
    tl = await goi('/api/dang-nhap',
                   { ten: $('o-ten').value, mat_khau: $('o-mat-khau').value },
                   { laDangNhap: true });
  } catch (err) { tl = null; }
  nut.disabled = false; nut.textContent = 'Đăng nhập';
  const d = (tl && tl.d) || {};
  if (!tl || !tl.ok) {
    $('loi-dang-nhap').textContent =
      d.loi || 'Không gọi được máy chủ. Máy chủ còn đang chạy không?';
    $('loi-dang-nhap').classList.remove('an');
    $('o-mat-khau').value = '';
    $('o-mat-khau').focus();
    return;
  }
  anDangNhap(d.ten);
  const lai = viecCho; viecCho = null;
  if (lai) lai();                       // chạy lại đúng MỘT việc vừa trượt
  else moMan(location.hash.slice(1) || 'man-xep');
};

$('nut-dang-xuat').onclick = async () => {
  try {
    await goi('/api/dang-xuat', {}, { laDangNhap: true });
  } catch (e) { /* mất mạng thì thôi, cứ hiện lại ô đăng nhập */ }
  if (dongHo) { clearInterval(dongHo); dongHo = null; }
  anDangNhap(null);
  hienDangNhap(null);
};

// Hỏi ngay lúc tải trang, để hiện ô mật khẩu TRƯỚC khi thầy cô bấm nút —
// nếu không thì cú bấm đầu tiên bị mất và không được chạy lại.
(async () => {
  try {
    const d = (await goi('/api/toi-la-ai', undefined,
                         { laDangNhap: true })).d;
    if (d && d.dang_nhap) anDangNhap(d.ten); else hienDangNhap(null);
  } catch (e) { hienDangNhap(null); }
})();

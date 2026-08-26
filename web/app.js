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
// ---------------------------------------------------------------------------
// Đợt 3 phần 4 — BỐN TRẠNG THÁI của danh sách quy tắc
//
// Bản trước viết `if (!d) return;` — máy chủ 500 hay câu trả lời không phải
// JSON thì màn hình đứng im với danh sách cũ, KHÔNG một chữ nào. Thầy cô sửa
// một quy tắc, bấm, không thấy gì đổi, và không có cách nào biết vì sao. Đó
// đúng là hạng lỗi im lặng cả dự án này viết ra để chống — chỉ khác là lần
// này nó nằm ở giao diện chứ không ở chỗ ghi tệp.
// ---------------------------------------------------------------------------
function trangThaiDs(trang, chu) {
  $('qt-dang-tai').classList.toggle('an', trang !== 'tai');
  $('qt-loi').classList.toggle('an', trang !== 'loi');
  $('ds-quy-tac').classList.toggle('an', trang !== 'xong');
  if (trang === 'loi') $('qt-loi-chu').textContent = chu || '';
}

async function napQuyTac() {
  // Chỉ hiện "đang tải" khi CHƯA có gì trên màn hình. Nạp lại sau mỗi lần
  // thêm/xoá mà chớp một khung "đang tải" thì danh sách nhảy giật, và thầy cô
  // mất chỗ đang đọc.
  if (!quyTac.length) trangThaiDs('tai');
  let d;
  try { d = (await goi('/api/quy-tac', undefined, { lai: napQuyTac })).d; }
  catch (e) {
    // Hết phiên thì lớp phủ đăng nhập đã hiện — báo lỗi thêm là báo sai
    // nguyên nhân. Việc đang dở tự chạy lại sau khi đăng nhập (QĐ 1).
    if (!(e && e.hetPhien)) {
      trangThaiDs('loi', 'Không nối được tới máy chủ. Kiểm tra xem cửa sổ '
                       + 'dòng lệnh còn chạy không, rồi bấm "Thử lại".');
    }
    return;
  }
  if (!d || !Array.isArray(d.quy_tac)) {
    trangThaiDs('loi', 'Máy chủ trả về câu trả lời không đọc được. Xem cửa sổ '
                     + 'dòng lệnh để biết chi tiết, rồi bấm "Thử lại".');
    return;
  }
  trangThaiDs('xong');
  // giữ lại các công tắc người dùng vừa gạt, đừng nạp đè lên
  const daGat = new Map(quyTac.map((r) => [r.i, r.bat]));
  quyTac = d.quy_tac.map((r) => ({ ...r, bat: daGat.has(r.i) ? daGat.get(r.i) : r.bat }));
  dauCauHinh = d.dau;          // gửi lại y nguyên lúc bấm Lưu
  veQuyTac();
  if (!$('o-tuan').value) $('o-tuan').placeholder = d.tuan;
}

// Nhóm của một loại quy tắc, tra từ DM (/api/loai-quy-tac). DM có thể chưa
// về — napQuyTac() và napDanhMuc() chạy song song — nên phải chịu được null:
// lúc đó dồn hết vào một nhóm, rồi napDanhMuc() vẽ lại.
function nhomCuaLoai(ten) {
  if (!DM) return null;
  for (const n of DM.nhom) {
    if (n.loai.some((l) => l.ten === ten)) return n.nhom;
  }
  return 'CHƯA XẾP NHÓM';
}

function nhanCuaLoai(ten) {
  if (!DM) return '';
  for (const n of DM.nhom) {
    const l = n.loai.find((x) => x.ten === ten);
    if (l) return l.nhan || '';
  }
  return '';
}

// ---------------------------------------------------------------------------
// Đợt 3 phần 2 — TÌM và LỌC
//
// "Quy tắc này chạm vào ai" tính ở MÁY CHỦ (khoá pham_vi của /api/quy-tac,
// dùng lại pham_vi_quy_tac của việc 2). Ở đây chỉ so danh sách tên — KHÔNG
// đọc lại noi_dung.loc để tự suy ra, vì đó là dựng bản cài thứ hai của bộ
// lọc, đúng kiểu lệch đã trả giá ở khop_loc() / _cum_cua().
// ---------------------------------------------------------------------------
function docBoLoc() {
  return { tim: ($('tim-qt').value || '').trim().toLowerCase(),
           nhom: $('loc-nhom').value, gv: $('loc-gv').value,
           mon: $('loc-mon').value, lop: $('loc-lop').value };
}

function coLoc(b) { return !!(b.tim || b.nhom || b.gv || b.mon || b.lop); }

function loLot(r, b) {
  const pv = r.pham_vi;
  // Quy tắc chưa tính được phạm vi (cấu hình đang hỏng) thì LUÔN hiện khi lọc
  // theo GV/môn/lớp. Giấu nó đi là giấu đúng cái thầy cô đang cần tìm để sửa.
  if (b.gv && pv && !pv.gv.includes(b.gv)) return false;
  if (b.mon && pv && !pv.mon.includes(b.mon)) return false;
  if (b.lop && pv && !pv.lop.includes(b.lop)) return false;
  if (b.nhom && (nhomCuaLoai(r.loai) || '') !== b.nhom) return false;
  if (b.tim) {
    const kho = [r.ghi_chu, r.loai, nhanCuaLoai(r.loai),
                 pv ? pv.lop.join(' ') : '', pv ? pv.mon.join(' ') : '',
                 pv ? pv.gv.join(' ') : ''].join(' ').toLowerCase();
    if (!kho.includes(b.tim)) return false;
  }
  return true;
}

function veLocQuyTac() {
  const chon = (o, ds, nhan) => {
    const cu = o.value;
    o.innerHTML = `<option value="">${nhan}</option>`
      + ds.map((x) => `<option value="${ma(x)}">${ma(x)}</option>`).join('');
    if (ds.includes(cu)) o.value = cu;      // giữ lựa chọn khi vẽ lại
  };
  chon($('loc-nhom'), DM ? DM.nhom.map((n) => n.nhom) : [], '— mọi nhóm —');
  // Danh sách rút TỪ CHÍNH các quy tắc đang có, không phải toàn bộ 28 giáo
  // viên: chọn một cái tên rồi ra 0 thẻ là câu trả lời vô ích.
  const gop = (khoa) => [...new Set(quyTac.flatMap(
    (r) => (r.pham_vi ? r.pham_vi[khoa] : [])))].sort();
  chon($('loc-gv'), gop('gv'), '— mọi giáo viên —');
  chon($('loc-mon'), gop('mon'), '— mọi môn —');
  chon($('loc-lop'), gop('lop'), '— mọi lớp —');
}

function veQuyTac() {
  const hop = $('ds-quy-tac');
  veLocQuyTac();
  const b = docBoLoc();
  $('nut-bo-loc').classList.toggle('an', !coLoc(b));
  if (!quyTac.length) {
    hop.innerHTML = '<p class="trong-rong">Chưa có quy tắc nào.</p>';
    $('dem-quy-tac').textContent = '';
    return;
  }
  // Gom theo nhóm, GIỮ THỨ TỰ của DM để hai màn hình cùng một trật tự. Loại
  // nào DM chưa biết thì rơi vào nhóm cuối chứ không biến mất — thẻ biến mất
  // là đúng kiểu lỗi im lặng cả dự án này viết ra để chống.
  const thuTu = DM ? DM.nhom.map((n) => n.nhom) : [];
  const gom = new Map(thuTu.map((t) => [t, []]));
  let hien = 0;
  quyTac.forEach((r, k) => {
    if (!loLot(r, b)) return;
    hien += 1;
    const n = nhomCuaLoai(r.loai) || 'Tất cả quy tắc';
    if (!gom.has(n)) gom.set(n, []);
    gom.get(n).push({ r, k });
  });
  $('dem-quy-tac').textContent = coLoc(b)
    ? `Hiện ${hien} / ${quyTac.length} quy tắc.`
    : `${quyTac.length} quy tắc.`;
  if (!hien) {
    hop.innerHTML = '<p class="trong-rong">Không quy tắc nào khớp bộ lọc. '
      + 'Bấm "Bỏ lọc" để xem lại tất cả.</p>';
    return;
  }
  hop.innerHTML = [...gom.entries()].filter(([, ds]) => ds.length)
    .map(([ten, ds]) =>
      `<section class="nhom-qt"><h3 class="nhom-ten">${ma(ten)}`
      + `<span class="nhom-dem">${ds.length}</span></h3>`
      + '<div class="the-ds">' + ds.map(({ r, k }) => theQuyTac(r, k)).join('')
      + '</div></section>').join('');
  noiSuKienThe(hop);
}

function theQuyTac(r, k) {
  const nhan = nhanCuaLoai(r.loai);
  return `<article class="the-qt${r.bat ? '' : ' tat'}" data-the="${k}">`
    + '<div class="the-dau">'
    + `<span class="the-so">#${r.i + 1}</span>`
    + `${r.mem ? '<span class="chip chip-mem">Ưu tiên</span>'
               : '<span class="chip chip-cung">Bắt buộc</span>'}`
    + `${r.moi ? '<span class="chip chip-moi">chưa lưu</span>' : ''}`
    + '</div>'
    + `<p class="the-chu">${ma(r.ghi_chu)}</p>`
    + `<p class="the-loai">${ma(nhan || r.loai)}`
    + `<code>${ma(r.loai)}</code></p>`
    + (r.pham_vi ? `<p class="the-pv">Chạm vào ${r.pham_vi.so_cum} cụm · `
        + `${r.pham_vi.so_tiet} tiết · ${r.pham_vi.lop.length} lớp</p>` : '')
    + '<div class="the-nut">'
    + `<label class="cong-tac"><input type="checkbox" data-k="${k}" `
    + `${r.bat ? 'checked' : ''}> ${r.bat ? 'Bật' : 'Tắt'}</label>`
    // "Sửa" CHỈ có ở quy tắc nháp. Quy tắc đã nằm trong cauhinh.json thì
    // luu_quy_tac() chỉ ghi được cờ bật/tắt, không ghi được thân — nên một nút
    // "Sửa" ở đó là nút hứa cái nó không làm được. Xem ghi chú ở suaQuyTac().
    + (r.moi ? `<button class="nut-sua" data-sua="${k}">Sửa</button>` : '')
    + `<button class="nut-nhan-ban" data-nhan-ban="${k}">Tạo giống</button>`
    + (r.moi ? `<button class="nut-xoa" data-xoa="${r.i}">Xoá</button>` : '')
    + '</div></article>';
}

function noiSuKienThe(hop) {
  hop.querySelectorAll('input[type=checkbox]').forEach((o) => {
    o.onchange = () => { quyTac[+o.dataset.k].bat = o.checked; veQuyTac(); };
  });
  hop.querySelectorAll('[data-nhan-ban]').forEach((o) => {
    o.onclick = () => nhanBan(quyTac[+o.dataset.nhanBan]);
  });
  hop.querySelectorAll('[data-sua]').forEach((o) => {
    o.onclick = () => suaQuyTac(quyTac[+o.dataset.sua]);
  });
  hop.querySelectorAll('[data-xoa]').forEach((o) => {
    o.onclick = async () => {
      const tl = await goiCu('/api/xoa-quy-tac', { i: +o.dataset.xoa });
      const kq = await tl.json();
      if (!tl.ok) { baoLoi(kq.loi || 'Không xoá được.'); return; }
      quyTac = kq.quy_tac.map((r) => ({ ...r }));
      veQuyTac();
    };
  });
}

$('nut-tai-lai-qt').onclick = () => { quyTac = []; napQuyTac(); };

// BÀN PHÍM. Hai phím, cả hai đều là thói quen sẵn có, không phải phím bí mật:
//   Esc trong ô Tìm  -> xoá bộ lọc (giống Esc đóng hộp thoại)
//   Enter trong ô Tìm -> không gửi gì cả; lọc đã chạy theo từng phím rồi.
// KHÔNG chiếm phím tắt toàn trang kiểu "/" hay "Ctrl+K": thầy cô không biết
// chúng tồn tại, mà chúng lại cướp phím của người đang gõ trong ô khác.
$('tim-qt').onkeydown = (e) => {
  if (e.key === 'Escape' && $('tim-qt').value) {
    e.preventDefault();
    $('tim-qt').value = '';
    veQuyTac();
  }
  if (e.key === 'Enter') e.preventDefault();
};

['tim-qt', 'loc-nhom', 'loc-gv', 'loc-mon', 'loc-lop'].forEach((id) => {
  const o = $(id);
  o[o.tagName === 'INPUT' ? 'oninput' : 'onchange'] = () => veQuyTac();
});
$('nut-bo-loc').onclick = () => {
  ['tim-qt', 'loc-nhom', 'loc-gv', 'loc-mon', 'loc-lop']
    .forEach((id) => { $(id).value = ''; });
  veQuyTac();
  $('tim-qt').focus();
};

// ---------------------------------------------------------------------------
// Đợt 3 phần 3 — SỬA một quy tắc NHÁP
//
// Chỉ quy tắc nháp mới sửa được, và đây là ràng buộc THẬT chứ không phải chưa
// làm tới: luu_quy_tac() ghi cờ bật/tắt cộng danh sách nháp, KHÔNG ghi được
// thân một quy tắc đã có trong cauhinh.json. Cho nút "Sửa" hiện ở đó là hứa
// một việc không làm được — thầy cô sửa, bấm Lưu, rồi mở tệp ra thấy y như cũ.
//
// Sửa = XOÁ nháp rồi ĐIỀN form. Xoá TRƯỚC, điền SAU: nếu điền trước mà xoá
// hỏng thì bấm Thêm sẽ đụng cửa chặn trùng câu ghi_chu, và câu từ chối đó nói
// về một chuyện khác hẳn — người dùng không cách nào hiểu.
// ---------------------------------------------------------------------------
async function suaQuyTac(r) {
  if (!r || !r.moi) return;
  const luu = { loai: r.loai, ghi_chu: r.ghi_chu,
                noi_dung: r.noi_dung, bat: r.bat };
  baoLoi('');
  const tl = await goiCu('/api/xoa-quy-tac', { i: r.i });
  const kq = await tl.json();
  if (!tl.ok) { baoLoi(kq.loi || 'Không sửa được: xoá bản nháp cũ thất bại.'); return; }
  quyTac = kq.quy_tac.map((x) => ({ ...x }));
  veQuyTac();
  if (!datLoai(luu.loai)) {
    baoLoi('Loại "' + luu.loai + '" không còn trong danh mục.');
    return;
  }
  $('o-ghi-chu').value = luu.ghi_chu || '';   // giữ NGUYÊN câu, không thêm hậu tố
  veTruong(luu.noi_dung || {});
  henDocLai();
  $('chu-luu').textContent = 'Đã đưa quy tắc xuống form để sửa. Sửa xong bấm '
    + '"Thêm vào danh sách" để đưa lại lên trên.';
  $('o-ghi-chu').scrollIntoView({ block: 'center' });
  $('o-ghi-chu').focus();
  $('o-ghi-chu').setSelectionRange($('o-ghi-chu').value.length,
                                   $('o-ghi-chu').value.length);
}

// ---------------------------------------------------------------------------
// Đợt 3 việc 4 — "Tạo giống quy tắc này"
//
// CHỈ ĐIỀN FORM, KHÔNG THÊM THẲNG. Thầy cô phải sửa ít nhất câu "Nội dung"
// trước khi bấm Thêm — và máy chủ CHẶN nếu câu đó trùng, vì đã đo được: hai
// quy tắc MỀM cùng ghi_chu thì cham_diem() lấy ghi_chu làm khoá dict, cái sau
// ĐÈ cái trước, bảng "Kiểm tra quy tắc" trên Excel MẤT một dòng mà tổng điểm
// vẫn cộng đủ. Sai trong im lặng.
//
// Vì vậy hậu tố " — bản sao" là điểm KHỞI ĐẦU để sửa, không phải câu dùng luôn.
// ---------------------------------------------------------------------------
function nhanBan(r) {
  if (!r) return;
  baoLoi('');
  $('ket-qua-thu').classList.add('an');
  if (!datLoai(r.loai)) {
    baoLoi('Không nhân bản được: loại "' + r.loai + '" không còn trong danh '
         + 'mục. Có thể cauhinh.json khai một loại mà bản phần mềm này chưa có.');
    return;
  }
  $('o-ghi-chu').value = (r.ghi_chu || '') + ' — bản sao';
  veTruong(r.noi_dung || {});
  henDocLai();
  $('chu-luu').textContent = 'Đã chép quy tắc xuống form bên dưới. Hãy SỬA câu '
    + '"Nội dung" cho khác đi rồi bấm "Thêm vào danh sách".';
  $('o-ghi-chu').scrollIntoView({ block: 'center' });
  $('o-ghi-chu').focus();
  // Con trỏ về CUỐI câu, ngay chỗ hậu tố — chỗ cần sửa. select() bôi đen cả
  // câu thì gõ một phím là mất sạch phần vừa chép.
  $('o-ghi-chu').setSelectionRange($('o-ghi-chu').value.length,
                                   $('o-ghi-chu').value.length);
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
  veDsLoai();
  if (quyTac.length) veQuyTac();   // giờ mới biết nhóm + nhãn
  $('o-ghi-chu').oninput = henDocLai;
  // Bắt Ở KHUNG CHA, không gắn vào từng ô: veTruong() vẽ lại toàn bộ ô nhập
  // mỗi lần đổi loại, nên gắn vào từng ô là gắn xong lại mất.
  $('o-truong').addEventListener('input', henDocLai);
  $('o-truong').addEventListener('change', henDocLai);
  veTruong();
  henDocLai();
}

// ---------------------------------------------------------------------------
// Đợt 3 việc 4 — DÃY THẺ CHỌN thay <select>
//
// Vì sao bỏ <select>: <option> không xuống dòng được, và bộ chọn của hệ điều
// hành trên điện thoại cắt chuỗi sớm. Nhãn ở đây CỐ Ý có hai vế, vế sau dấu
// gạch mới là vế phân biệt — "CHỈ được xếp vào những thứ đã chọn — mọi thứ
// khác đều cấm" so với "Hai nhóm KHÔNG được rơi vào cùng một ngày — mỗi nhóm
// vẫn xếp thứ nào cũng được". Cắt ở dấu gạch là mất đúng vế mang thông tin,
// và cạm bẫy QT 14/15/16 (thầy cô chọn chi_xep_thu khi định nói khac_ngay)
// quay lại nguyên vẹn.
//
// Bốn nhóm GẬP/MỞ, mặc định gập hết: 17 thẻ trải ra là ~4,6 màn hình điện
// thoại. Thẻ HAI DÒNG — nhãn (vế đầu) + tên kỹ thuật; vế sau dấu gạch dồn
// xuống #mo-ta-loai ngay dưới, KHÔNG mất chữ nào, chỉ dời chỗ.
//
// KHÔNG gắn phím tắt toàn trang: radio cùng `name` đã đi được bằng phím mũi
// tên sẵn trong trình duyệt. thu_them_quy_tac.py CA 11 cấm
// document.addEventListener('keydown').
// ---------------------------------------------------------------------------
let loaiChon = '';        // tên kỹ thuật của loại đang chọn, '' = chưa chọn
const nhomMo = new Set(); // tên nhóm đang MỞ

function veDsLoai() {
  if (!DM || !DM.nhom) return;
  $('ds-nhom-loai').innerHTML = DM.nhom.map((n) => {
    const mo = nhomMo.has(n.nhom);
    const the = n.loai.map((l) => {
      const nhan = (l.nhan || l.ten).split(' — ')[0];
      const chon = l.ten === loaiChon;
      return `<label class="the-loai-chon${chon ? ' dang-chon' : ''}">`
        + `<input type="radio" name="loai-qt" value="${ma(l.ten)}"`
        + `${chon ? ' checked' : ''}>`
        + '<span class="dau-cham"></span><span class="chu">'
        + `<span class="nhan-loai">${ma(nhan)}</span>`
        + `<code class="ma-loai">${ma(l.ten)}</code></span></label>`;
    }).join('');
    return `<div class="nhom-loai"><button type="button" class="nut-nhom"`
      + ` data-nhom="${ma(n.nhom)}" aria-expanded="${mo}">`
      + `<span class="mui">${mo ? '▾' : '▸'}</span>`
      + `<span class="ten-nhom">${ma(n.nhom)}</span>`
      + `<span class="nhom-dem">${n.loai.length}</span></button>`
      + (mo ? `<div class="the-loai-ds">${the}</div>` : '') + '</div>';
  }).join('');

  $('ds-nhom-loai').querySelectorAll('.nut-nhom').forEach((b) => {
    b.onclick = () => {
      const t = b.dataset.nhom;
      if (nhomMo.has(t)) nhomMo.delete(t); else nhomMo.add(t);
      veDsLoai();
    };
  });
  $('ds-nhom-loai').querySelectorAll('input[name="loai-qt"]').forEach((o) => {
    o.onchange = () => {
      if (!o.checked) return;
      loaiChon = o.value;
      veDsLoai();
      veTruong();
      henDocLai();
    };
  });
}

// Đặt loại từ mã (nút Sửa / Tạo giống). Trả false nếu loại không còn trong
// danh mục. MỞ SẴN nhóm chứa nó — "mặc định gập hết" mà không mở thì loại
// đang chọn VÔ HÌNH, đúng chỗ thua đã nêu lúc trình bố cục.
function datLoai(t) {
  if (!coLoai(t)) return false;
  loaiChon = t;
  for (const n of DM.nhom) {
    if (n.loai.some((l) => l.ten === t)) nhomMo.add(n.nhom);
  }
  veDsLoai();
  return true;
}

function coLoai(t) {
  if (!DM || !DM.nhom) return false;
  return DM.nhom.some((n) => n.loai.some((l) => l.ten === t));
}

function loaiDangChon() {
  for (const n of DM.nhom) for (const l of n.loai) {
    if (l.ten === loaiChon) return l;
  }
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

// nguon = nơi lấy giá trị điền sẵn. Bỏ trống thì lấy VI_DU của loại (đường
// bình thường); nút "Tạo giống quy tắc này" truyền vào noi_dung của quy tắc
// đang nhân bản. MỘT hàm vẽ, không phải hai — hai bản vẽ là hai bản sẽ lệch.
function veTruong(nguon) {
  const l = loaiDangChon();
  // CHƯA CHỌN LOẠI là trạng thái THẬT từ khi bỏ <select>: <select> luôn tự
  // chọn phần tử đầu, dãy thẻ thì không chọn gì cho tới khi người dùng bấm.
  // Phải DỌN SẠCH, đừng để mô tả của loại cũ nằm lại bên dưới một khung
  // không còn chọn gì — đó là kiểu sai im lặng cả dự án này chống.
  if (!l) {
    $('o-truong').innerHTML = '';
    $('mo-ta-loai').textContent = '';
    $('ten-ky-thuat').textContent = '';
    return;
  }
  const vi = nguon || l.vi_du;
  $('mo-ta-loai').textContent = l.mo_ta;
  $('ten-ky-thuat').textContent = 'tên trong cauhinh.json:  "loai": "' + l.ten + '"';
  if (!nguon && !$('o-ghi-chu').value.trim())
    $('o-ghi-chu').value = l.vi_du.ghi_chu || '';
  const nhomDa = {};
  $('o-truong').className = 'o-truong';
  $('o-truong').innerHTML = l.truong.map((tr) => {
    const gt = vi[tr.ten];
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
  const pv = $('doc-lai-pham-vi');
  if (d.cau) {
    const loi = d.canh_bao || d.canh_bao_pham_vi;
    khung.className = 'thu-hop ' + (loi ? 'thu-canh-bao' : 'thu-ok');
    $('doc-lai-cau').innerHTML =
      '<b>Máy hiểu câu này là:</b><br>' + ma(d.cau);
    // Xem trước phạm vi (việc 2). Nói SỐ trước, rồi mới liệt kê tên — người
    // đọc cần biết "có khớp gì không" trước khi cần biết "khớp những gì".
    const p = d.pham_vi;
    if (p && !p.loi) {
      const ve = (p.ve || []).length
        ? p.ve.map((v) => `nhóm ${ma(v.ten)}: ${v.so_cum} cụm`).join(' · ')
        : '';
      pv.innerHTML = '<b>Chạm vào:</b> ' + p.so_cum + ' cụm · ' + p.so_tiet
        + ' tiết · ' + (p.lop.length ? p.lop.length + ' lớp (' + ma(p.lop.join(', ')) + ')'
                                     : '<b>KHÔNG lớp nào</b>')
        + (ve ? '<br>' + ve : '');
      pv.classList.remove('an');
    } else {
      pv.classList.add('an');
    }
    cb.textContent = loi || '';
    cb.classList.toggle('an', !loi);
    khung.classList.remove('an');
  } else {
    khung.classList.add('an');
  }
}

function docForm() {
  const l = loaiDangChon();
  if (!l) return null;        // chưa chọn loại — người gọi tự báo
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
  const r = docForm();
  if (!r) {
    baoLoi('Chưa chọn "Loại quy tắc". Mở một nhóm rồi bấm vào loại cần dùng.');
    return;
  }
  const tl = await goiCu('/api/them-quy-tac', { quy_tac: r });
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
  const rt = docForm();
  if (!rt) {
    baoLoi('Chưa chọn "Loại quy tắc". Mở một nhóm rồi bấm vào loại cần dùng.');
    return;
  }
  n.disabled = true; n.textContent = 'Đang thử...';
  try {
    const tl = await goiCu('/api/thu-quy-tac',
      { quy_tac: rt,
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

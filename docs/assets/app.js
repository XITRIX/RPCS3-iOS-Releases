/* Aggregate snapshots only. No Analytics SDK, cookies or visitor tracking. */
'use strict';
const $ = id => document.getElementById(id);
const model = window.PerformanceModel;
const devices = window.DeviceNames;
const integer = new Intl.NumberFormat('en');
const decimal = new Intl.NumberFormat('en', {maximumFractionDigits: 1});
let snapshot, visible = [];
const states = ['nominal', 'fair', 'serious', 'critical'];
const duration = seconds => seconds >= 3600 ? `${decimal.format(seconds / 3600)} hr` : seconds >= 60 ? `${decimal.format(seconds / 60)} min` : `${decimal.format(seconds)} sec`;
function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}
function reset() {
  $('search').value = ''; $('device').value = ''; $('mode').value = 'jit'; $('sort').value = 'game'; render();
}
function render() {
  visible = model.select(snapshot.rows, {query: $('search').value, device: $('device').value, mode: $('mode').value, sort: $('sort').value});
  const fragment = document.createDocumentFragment();
  for (const row of visible) {
    const tr = element('tr');
    const game = element('td'); game.append(element('div', 'game', row.game), element('span', 'title-id', row.titleId));
    const hardware = element('td', 'device', devices.name(row.device)); hardware.title = row.device; hardware.append(element('span', 'mode', row.mode));
    tr.append(game, hardware);
    for (const state of states) {
      const cell = row.thermal[state], td = element('td');
      if (cell?.seconds > 0) {
        td.append(element('span', 'fps', decimal.format(cell.frameEquivalents / cell.seconds)), element('span', 'unit', 'FPS'), element('span', 'duration', duration(cell.seconds)));
      } else { td.append(element('span', 'missing', '—')); td.setAttribute('aria-label', `${state}: no measurements`); }
      tr.append(td);
    }
    const measured = element('td', 'measured', duration(model.total(row).seconds));
    if (row.thermal.unknown) measured.append(element('span', 'duration', `Includes ${duration(row.thermal.unknown.seconds)} in unknown thermal state`));
    tr.append(measured); fragment.append(tr);
  }
  $('rows').replaceChildren(fragment);
  $('count').textContent = `${integer.format(visible.length)} of ${integer.format(snapshot.rows.length)} device / game results · ${duration(visible.reduce((n, r) => n + model.total(r).seconds, 0))} measured`;
  $('empty').hidden = visible.length !== 0;
  $('export').disabled = visible.length === 0;
}
async function start() {
  try {
    const response = await fetch('data/performance.json', {cache: 'no-cache'});
    if (!response.ok) throw new Error('Snapshot unavailable');
    snapshot = await response.json();
    if (snapshot.schemaVersion !== 1 || !Array.isArray(snapshot.rows)) throw new Error('Unsupported snapshot');
    const generated = new Date(snapshot.generatedAt);
    $('period').textContent = snapshot.period.label || `${snapshot.period.start} — ${snapshot.period.end} · inclusive`;
    const age = Math.max(0, Date.now() - generated.getTime()) / 86400000;
    $('freshness').textContent = age > 2 ? `Snapshot is ${Math.floor(age)} days old · updates may be delayed` : 'Dated snapshot · refreshes daily';
    const rows = snapshot.rows;
    $('stat-games').textContent = integer.format(new Set(rows.map(r => r.titleId)).size);
    $('stat-devices').textContent = integer.format(new Set(rows.map(r => devices.name(r.device))).size);
    $('stat-combinations').textContent = integer.format(rows.length);
    $('stat-hours').textContent = decimal.format(rows.reduce((n, r) => n + model.total(r).seconds, 0) / 3600);
    for (const device of [...new Set(rows.map(r => devices.name(r.device)))].sort((a, b) => a.localeCompare(b, 'en', {numeric: true}))) {
      const option = element('option', '', device); option.value = device; $('device').append(option);
    }
    if (snapshot.warnings?.length) { $('notice').textContent = snapshot.warnings.join(' '); $('notice').hidden = false; }
    $('filters').addEventListener('submit', e => e.preventDefault());
    $('search').addEventListener('input', render);
    for (const id of ['device', 'mode', 'sort']) $(id).addEventListener('change', render);
    $('clear').addEventListener('click', reset); $('empty-reset').addEventListener('click', reset);
    $('export').addEventListener('click', () => {
      const url = URL.createObjectURL(new Blob(['\uFEFF', model.csv(visible)], {type: 'text/csv;charset=utf-8'}));
      const link = element('a'); link.href = url; link.download = 'rpcs3-apple-performance.csv'; document.body.append(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 1000);
    });
    render();
  } catch (_) { $('error').hidden = false; $('count').textContent = 'Snapshot unavailable'; }
}
// A separate visual header keeps page scrolling independent of horizontal table scrolling.
// The original table header remains the accessible source of column labels.
function pinTableHeader() {
  const shell = $('results'), table = shell.querySelector('table');
  const head = table.tHead;
  const pinned = element('div', 'pinned-table-header');
  pinned.setAttribute('aria-hidden', 'true'); pinned.hidden = true;
  const copy = element('table'); copy.append(head.cloneNode(true));
  pinned.append(copy); document.body.append(pinned);
  let pending = false;
  function update() {
    pending = false;
    const bounds = table.getBoundingClientRect();
    const height = head.getBoundingClientRect().height;
    pinned.hidden = !table.tBodies[0].rows.length || bounds.top >= 0 || bounds.bottom <= 0;
    if (pinned.hidden) return;
    const region = shell.getBoundingClientRect();
    pinned.style.left = `${region.left + shell.clientLeft}px`;
    pinned.style.width = `${shell.clientWidth}px`;
    pinned.style.height = `${height}px`;
    pinned.style.top = `${Math.min(0, bounds.bottom - height)}px`;
    copy.style.width = `${bounds.width}px`;
    copy.style.transform = `translateX(${-shell.scrollLeft}px)`;
    [...head.rows[0].cells].forEach((cell, index) => {
      const width = `${cell.getBoundingClientRect().width}px`;
      const target = copy.tHead.rows[0].cells[index];
      target.style.width = width; target.style.minWidth = width; target.style.maxWidth = width;
    });
  }
  function schedule() {
    if (!pending) { pending = true; requestAnimationFrame(update); }
  }
  window.addEventListener('scroll', schedule, {passive: true});
  window.addEventListener('resize', schedule);
  shell.addEventListener('scroll', schedule, {passive: true});
  new ResizeObserver(schedule).observe(table);
  update();
}
pinTableHeader();
start();

(function (root) {
  'use strict';
  const devices = typeof module !== 'undefined' && module.exports ? require('./devices.js') : root.DeviceNames;
  function total(row) {
    return Object.values(row.thermal).reduce((sum, cell) => ({seconds: sum.seconds + cell.seconds, frames: sum.frames + cell.frameEquivalents}), {seconds: 0, frames: 0});
  }
  function fps(row) { const t = total(row); return t.seconds ? t.frames / t.seconds : null; }
  function select(rows, {query = '', device = '', mode = 'jit', sort = 'game'} = {}) {
    const needle = query.trim().toLocaleLowerCase();
    return rows.filter(r => (!device || r.device === device || devices.name(r.device) === device) && (!mode || r.mode === mode) &&
      `${r.game} ${r.titleId} ${r.device} ${devices.name(r.device)}`.toLocaleLowerCase().includes(needle)).sort((a, b) => {
        if (sort === 'coverage') return total(b).seconds - total(a).seconds || a.game.localeCompare(b.game);
        if (sort === 'fps') return fps(b) - fps(a) || a.game.localeCompare(b.game);
        if (sort === 'device') return devices.name(a.device).localeCompare(devices.name(b.device), 'en', {numeric: true}) || a.game.localeCompare(b.game);
        return a.game.localeCompare(b.game) || a.device.localeCompare(b.device) || a.mode.localeCompare(b.mode);
      });
  }
  function csv(rows) {
    // Spreadsheet programs must not interpret telemetry titles as formulas.
    const quote = v => '"' + String(v).replace(/^[=+\-@\t\r]/, "'$&").replace(/"/g, '""') + '"';
    const records = [['Game', 'Title ID', 'Device name', 'Hardware model', 'Execution mode', 'Thermal state', 'Measured seconds', 'Average FPS']];
    for (const row of rows) for (const [state, cell] of Object.entries(row.thermal)) {
      records.push([row.game, row.titleId, devices.name(row.device), row.device, row.mode, state, cell.seconds, cell.frameEquivalents / cell.seconds]);
    }
    return records.map(r => r.map(quote).join(',')).join('\r\n');
  }
  const api = {total, fps, select, csv};
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  else root.PerformanceModel = api;
})(typeof window === 'undefined' ? globalThis : window);

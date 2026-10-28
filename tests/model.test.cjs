const assert = require('node:assert/strict');
const model = require('../docs/assets/model.js');
const data = require('../docs/data/performance.json');
const a = {game: '=Game', titleId: 'ID1', device: 'iPad16,3', mode: 'jit', thermal: {nominal: {seconds: 10, frameEquivalents: 600}, serious: {seconds: 90, frameEquivalents: 1800}}};
const b = {game: 'Other', titleId: 'ID2', device: 'iPhone16,2', mode: 'interpreter', thermal: {fair: {seconds: 10, frameEquivalents: 0}}};
assert.equal(model.fps(a), 24); // Must not average 60 and 20 into 40.
assert.equal(model.fps(b), 0);
assert.equal(model.select([a, b], {query: 'id1'}).length, 1);
assert.equal(model.select([a, b], {device: b.device, mode: ''}).length, 1);
assert.equal(model.select([a, b], {mode: ''}).length, 2);
assert.equal(model.select([a, b], {query: 'missing', mode: ''}).length, 0);
assert.equal(model.select([b, a], {sort: 'coverage', mode: ''})[0], a);
assert.ok(model.csv([a]).includes('"\'=Game"'));
assert.equal(data.rows.length, new Set(data.rows.map(r => [r.device, r.game, r.titleId, r.mode].join('|'))).size);
assert.ok(data.rows.every(r => Object.values(r.thermal).every(c => c.seconds > 0 && Number.isFinite(c.frameEquivalents) && c.frameEquivalents >= 0)));
assert.ok(data.rows.length > 0);
console.log('Filtering, sorting, weighted FPS, zero stalls, CSV safety and snapshot checks pass.');

const devices = require('../docs/assets/devices.js');
assert.equal(devices.name('iPhone15,4'), 'iPhone 15');
assert.equal(devices.name('iPhone16,2'), 'iPhone 15 Pro Max');
assert.equal(devices.name('iPhone19,3'), 'iPhone 18 Pro Max');
assert.equal(devices.name('iPad17,4'), 'iPad Pro 13-inch (M5)');
assert.equal(devices.name('iPhone99,99'), 'iPhone99,99');
assert.equal(devices.name('__proto__'), '__proto__');
// Live telemetry may contain generic or newly introduced hardware identifiers.
assert.ok(data.rows.every(row => typeof row.device === 'string' && row.device.trim().length > 0));
const unmappedDevices = [...new Set(data.rows.map(row => row.device))]
  .filter(device => !Object.hasOwn(devices.mapping, device)).sort();
for (const device of unmappedDevices) assert.equal(devices.name(device), device);
if (unmappedDevices.length) {
  console.warn('Unmapped device identifiers (using raw fallback): ' + JSON.stringify(
    unmappedDevices.map(device => ({device, rows: data.rows.filter(row => row.device === device).length}))));
}
for (const device of ['arm64', 'iPhone99,99']) {
  const unknown = {...a, device};
  assert.equal(devices.name(device), device);
  assert.equal(model.fps(unknown), 24);
  assert.deepEqual(model.select([unknown, a], {query: device}), [unknown]);
  assert.deepEqual(model.select([unknown, a], {device}), [unknown]);
  assert.ok(model.csv([unknown]).includes(`"${device}","${device}"`));
  assert.equal(unknown.device, device);
}
assert.equal(model.select([a], {query: 'iPad Pro 11-inch (M4)'}).length, 1);
assert.equal(model.select([a], {device: 'iPad Pro 11-inch (M4)'}).length, 1);
const wifi = {...a, device: 'iPad17,3'}, cellular = {...a, device: 'iPad17,4'};
assert.equal(model.select([wifi, cellular], {device: 'iPad Pro 13-inch (M5)'}).length, 2);
assert.ok(model.csv([a]).includes('iPad Pro 11-inch (M4)'));
console.log('Device names, unknown fallback, name search and shared model variants pass.');

// rp1_smartciti_place.mjs -- finish the SmartCiti fabric (73):
//   1. bind the fly.io fabric URL in the company Map Viewer (persists to the fabric record)
//   2. set the parcel at the SmartCiti.X Holodeck registered anchor (my-fabric/anchors.json)
//   3. verify: Latitude/Longitude + public Spatial Fabric URL on the fabric home
// Log: /tmp/rp1-place.log
import fs from 'node:fs';
const LOG = '/tmp/rp1-place.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `smartciti place, ${new Date().toISOString()}\n`);
const FABRIC_URL = 'https://worldforge-api.fly.dev/v2/rp1/fabric/smartciti-holodeck';
const LAT = 39.84645175015757, LON = -86.621608018757;

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { log('FATAL no tab'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Page.enable');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const goto = async (url, settle = 3000) => { await send('Page.navigate', { url }); await sleep(settle); };

// 1. bind the fabric URL in the Map Viewer
await goto('https://dev.rp1.com/company/137/fabric/viewer');
const bind = await ev(`(() => {
  const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
  if (!inp) return 'NO_INPUT';
  inp.focus(); inp.value = ${JSON.stringify(FABRIC_URL)};
  inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true }));
  const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Load Url');
  if (b) b.click();
  return 'LOADING';
})()`);
log(`viewer bind: ${bind}`);
await sleep(5000);

// 2. set the parcel on the fabric home
await goto('https://dev.rp1.com/company/fabric/73/home');
const place = await ev(`(() => {
  const fill = (sel, val) => {
    const i = [...document.querySelectorAll('input')].find(x => (x.name === sel));
    if (!i) return false;
    i.focus(); i.value = val;
    i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new Event('change', { bubbles: true }));
    return true;
  };
  const a = fill('lat', String(${LAT}));
  const b = fill('lon', String(${LON}));
  const btn = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Update Area');
  if (!btn) return 'NO_UPDATE_BUTTON lat=' + a + ' lon=' + b;
  btn.click();
  return 'UPDATE_CLICKED';
})()`);
log(`parcel: ${place}`);
await sleep(5000);

// 3. verify
const v = await ev(`(() => {
  const txt = document.body.innerText || '';
  const latM = /Latitude\\s*\\n\\s*([\\-0-9.]+)/.exec(txt);
  const lonM = /Longitude\\s*\\n\\s*([\\-0-9.]+)/.exec(txt);
  const enter = [...document.querySelectorAll('input')].map(i => i.value).find(x => x && x.includes('enter.rp1.com'));
  const fabricUrl = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
  return JSON.stringify({ lat: latM ? latM[1] : null, lon: lonM ? lonM[1] : null, enterUrl: (enter || '').slice(0, 110), fabricUrlKept: fabricUrl ? fabricUrl.value.slice(0, 90) : null }, null, 1);
})()`);
log(`verify: ${v}`);
log('--- place done');
ws.close();
process.exit(0);

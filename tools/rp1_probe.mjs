// rp1_probe.mjs -- attach to the logged-in dev.rp1.com page over CDP and survey the Dev Center.
// Read-only recon: URL, title, visible text, links/buttons, storage key NAMES (values never printed).
//   node tools/rp1_probe.mjs            # DOM + links + storage keys to stdout
//   node tools/rp1_probe.mjs --shot     # also save /tmp/rp1-devcenter.png
const PORT = 9362;

const targets = await fetch(`http://127.0.0.1:9222/json/list`).then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no rp1.com page target; open tabs:', targets.filter(t => t.type === 'page').map(t => t.url)); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise((res) => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Page.enable'); await send('Runtime.enable');

console.log('URL:   ' + (await ev('location.href')));
console.log('TITLE: ' + (await ev('document.title')));
await new Promise(r => setTimeout(r, 1500)); // let any late SPA render settle

const info = await ev(`(() => {
  const txt = (document.body?.innerText || '').replace(/\\n{3,}/g, '\\n\\n');
  const links = [...document.querySelectorAll('a')].map(a => (a.innerText || '').trim().slice(0, 60) + ' => ' + a.href).filter(s => s.length > 4);
  const btns = [...document.querySelectorAll('button, [role=button]')].map(b => (b.innerText || b.getAttribute('aria-label') || '').trim()).filter(Boolean);
  const forms = [...document.querySelectorAll('input, select, textarea')].map(i => (i.name || i.id || i.placeholder || i.type || '?'));
  const sk = Object.keys(localStorage).concat(Object.keys(sessionStorage));
  return JSON.stringify({ txt: txt.slice(0, 4000), links: links.slice(0, 60), btns: btns.slice(0, 40), forms: forms.slice(0, 30), storageKeys: sk }, null, 1);
})()`);
console.log(info || '(empty body — still rendering?)');

if (process.argv.includes('--shot')) {
  const shot = await send('Page.captureScreenshot', { format: 'png' });
  const { writeFileSync } = await import('node:fs');
  writeFileSync('/tmp/rp1-devcenter.png', Buffer.from(shot.result.data, 'base64'));
  console.log('shot: /tmp/rp1-devcenter.png');
}
ws.close();

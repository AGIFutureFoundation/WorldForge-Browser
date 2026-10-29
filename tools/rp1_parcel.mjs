// rp1_parcel.mjs -- click "Select Parcel" with Network capture; dump what happens (map picker? API call?).
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('rp1.com'));
if (!page) { console.error('no rp1.com page'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const requests = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent') {
    const u = m.params.request.url;
    if (!u.startsWith('data:')) requests.push(`${m.params.request.method} ${u.slice(0, 130)}`);
  }
  if (m.method === 'Network.loadingFailed') requests.push(`FAILED ${m.params.errorText}`);
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable');

const pre = await ev(`(() => {
  const lat = document.querySelector('input[name=lat]')?.value;
  const lon = document.querySelector('input[name=lon]')?.value;
  return JSON.stringify({ lat, lon });
})()`);
console.log('parcel form:', pre);

const clicked = await ev(`(() => {
  const btns = [...document.querySelectorAll('button, [role=button]')].filter(b => (b.innerText || '').trim() === 'Select Parcel');
  if (!btns.length) return 'NOT_FOUND';
  btns[btns.length - 1].scrollIntoView({ block: 'center' });
  btns[btns.length - 1].click();
  return 'CLICKED';
})()`);
console.log('click:', clicked);
await new Promise(r => setTimeout(r, 6000));
console.log('--- network ---');
console.log(requests.slice(-20).join('\n') || '(no requests)');
const state = await ev(`(() => {
  const modals = [...document.querySelectorAll('.modal.show, [role=dialog], .offcanvas.show')]
    .map(m => (m.innerText || '').replace(/\\s+/g, ' ').slice(0, 400)).filter(Boolean);
  const canvas = [...document.querySelectorAll('canvas')].map(c => ({ w: c.width, h: c.height }));
  const alerts = [...document.querySelectorAll('.alert, .toast')].map(a => (a.innerText || '').replace(/\\s+/g, ' ').slice(0, 160)).filter(s => s.trim());
  return JSON.stringify({ modals, canvasCount: canvas.length, alerts: alerts.slice(0, 6), url: location.href }, null, 1);
})()`);
console.log('--- page state ---');
console.log(state);
ws.close();

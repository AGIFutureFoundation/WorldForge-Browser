// rp1_reconnect.mjs -- click Reconnect with Network capture on: what does it call, what fails?
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
    if (!u.startsWith('data:')) requests.push(`${m.params.request.method} ${u.slice(0, 110)}`);
  }
  if (m.method === 'Network.loadingFailed') requests.push(`FAILED ${m.params.errorText} ${m.params.requestId}`);
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable');

const clicked = await ev(`(() => {
  const btns = [...document.querySelectorAll('button')].filter(b => (b.innerText || '').trim() === 'Reconnect');
  if (!btns.length) return 'NOT_FOUND';
  btns[0].click();
  return 'CLICKED ' + btns.length + ' reconnect buttons';
})()`);
console.log(click_label(clicked));
await new Promise(r => setTimeout(r, 6000));
console.log('--- network after Reconnect ---');
console.log(requests.slice(-25).join('\n') || '(no requests)');
const banner = await ev(`(() => {
  const t = (document.body.innerText || '');
  const lost = t.includes('connection to RP1 has been lost');
  const friends = t.includes('not connected to the friends service');
  return JSON.stringify({ connectionLost: lost, friendsDown: friends });
})()`);
console.log('--- banner state ---');
console.log(banner);
ws.close();

function click_label(s) { return s; }

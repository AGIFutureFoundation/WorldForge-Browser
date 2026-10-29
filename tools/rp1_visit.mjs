// rp1_visit.mjs -- open the enter.rp1.com visit URL in a new tab and watch what it loads.
//   node tools/rp1_visit.mjs "https://enter.rp1.com?start_cid=553&lat=..&lon=..&rad=6371000"
const url = process.argv[2];
const res = await fetch('http://127.0.0.1:9222/json/new?' + encodeURIComponent(url), { method: 'PUT' });
const target = await res.json();
console.log('opened tab:', target.url.slice(0, 100));
await new Promise(r => setTimeout(r, 2000));

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && (t.targetId === target.id || t.url.includes('enter.rp1.com')));
if (!page) { console.log('tab not found'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const reqs = [];
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent') {
    const u = m.params.request.url;
    if (u.includes('worldforge') || u.includes('.glb') || u.includes('.msf') || u.includes('fabric')) reqs.push(u.slice(0, 130));
  }
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable'); await send('Page.enable');
await new Promise(r => setTimeout(r, 12000)); // give the world time to stream
const state = await ev(`(() => {
  const canvases = [...document.querySelectorAll('canvas')].map(c => ({ w: c.width, h: c.height }));
  return JSON.stringify({ url: location.href, title: document.title, canvases, txt: (document.body.innerText || '').slice(0, 300) }, null, 1);
})()`);
console.log('--- enter tab ---');
console.log(state);
console.log('--- payload/fabric fetches ---');
console.log(reqs.slice(0, 15).join('\n') || '(none captured)');
const shot = await send('Page.captureScreenshot', { format: 'png' });
const { writeFileSync } = await import('node:fs');
writeFileSync('/tmp/rp1-visit.png', Buffer.from(shot.result.data, 'base64'));
console.log('shot: /tmp/rp1-visit.png');
ws.close();

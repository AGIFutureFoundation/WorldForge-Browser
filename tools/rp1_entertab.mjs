// rp1_entertab.mjs -- attach to the enter.rp1.com tab (the visited fabric) and verify it is
// fetching our payload from fly.io.   node tools/rp1_entertab.mjs
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
console.log('--- tabs ---');
for (const t of targets.filter(t => t.type === 'page')) console.log(' -', t.url.slice(0, 100));
const page = targets.find(t => t.type === 'page' && t.url.includes('enter.rp1.com'));
if (!page) { console.log('no enter.rp1.com tab (yet)'); process.exit(0); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const flyReqs = []; let loaded = 0, failed = 0;
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent' && m.params.request.url.includes('worldforge-api.fly.dev')) {
    flyReqs.push(m.params.request.url);
  }
  if (m.method === 'Network.loadingFinished' && m.params.requestId) loaded++;
  if (m.method === 'Network.loadingFailed') { failed++; }
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable');
await new Promise(r => setTimeout(r, 8000)); // give the world time to load
const state = await ev(`(() => {
  const canvases = [...document.querySelectorAll('canvas')].map(c => ({ w: c.width, h: c.height }));
  return JSON.stringify({ url: location.href, title: document.title, canvases, bodyStart: (document.body.innerText || '').slice(0, 200) }, null, 1);
})()`);
console.log('--- enter tab state ---');
console.log(state);
console.log('--- fetches from fly.io (' + flyReqs.length + ') ---');
console.log(flyReqs.slice(0, 10).join('\n') || '(none captured yet)');
const shot = await send('Page.captureScreenshot', { format: 'png' });
const { writeFileSync } = await import('node:fs');
writeFileSync('/tmp/rp1-visit.png', Buffer.from(shot.result.data, 'base64'));
console.log('shot: /tmp/rp1-visit.png');
ws.close();

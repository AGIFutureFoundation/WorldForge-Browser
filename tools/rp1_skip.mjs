// rp1_skip.mjs -- click Skip on the mic dialog, then watch the enter tab for world streaming.
const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('enter.rp1.com'));
if (!page) { console.log('no enter.rp1.com tab'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map(); const flyReqs = []; let others = 0; let wsCount = 0;
ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Network.requestWillBeSent') {
    const u = m.params.request.url;
    if (u.startsWith('ws')) wsCount++;
    else if (u.includes('worldforge-api.fly.dev')) flyReqs.push(u.slice(0, 140));
    else if (!u.startsWith('data:')) others++;
  }
  const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
});
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Network.enable');

const s = await ev(`(() => {
  const b = [...document.querySelectorAll('button, [role=button]')].find(x => (x.innerText || '').trim() === 'Skip');
  if (!b) return 'NO_SKIP (txt: ' + (document.body.innerText || '').slice(0, 120) + ')';
  b.click(); return 'SKIPPED';
})()`);
console.log('mic:', s);
await new Promise(r => setTimeout(r, 25000)); // world stream settle
console.log('--- fly.io fetches (' + flyReqs.length + ') ---');
console.log(flyReqs.join('\n') || '(none)');
console.log('other requests:', others, '| websockets:', wsCount);
const state = await ev(`(() => JSON.stringify({ txt: (document.body.innerText || '').slice(0, 300), canvas: [...document.querySelectorAll('canvas')].map(c => c.width + 'x' + c.height) }, null, 1))()`);
console.log('--- tab state ---');
console.log(state);
const shot = await send('Page.captureScreenshot', { format: 'png' });
const { writeFileSync } = await import('node:fs');
writeFileSync('/tmp/rp1-world.png', Buffer.from(shot.result.data, 'base64'));
console.log('shot: /tmp/rp1-world.png');
ws.close();

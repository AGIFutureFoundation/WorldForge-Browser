// Headless Chrome (software WebGL) over CDP: the same pattern as worldforge/viewer/record_extra.mjs.
import { spawn } from 'node:child_process';
import fs from 'node:fs'; import os from 'node:os'; import path from 'node:path';

const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
export const BASE = process.env.WF_BASE || 'http://127.0.0.1:8094';
const PORT = Number(process.env.CDP_PORT || 9361);
export const sleep = (ms) => new Promise(r => setTimeout(r, ms));
export const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wfe-'));

export async function session(W, H) {
  const chrome = spawn(CHROME, ['--headless=new', `--remote-debugging-port=${PORT}`, `--user-data-dir=${path.join(tmp, 'p')}`,
    '--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist', '--enable-webgl',
    '--mute-audio', '--hide-scrollbars', `--window-size=${W},${H}`, 'about:blank'], { stdio: 'ignore' });
  let tg;
  for (let i = 0; i < 150 && !(tg && tg.some(t => t.type === 'page')); i++) {
    await sleep(200); tg = await fetch(`http://127.0.0.1:${PORT}/json/list`).then(r => r.json()).catch(() => null);
  }
  const ws = new WebSocket(tg.find(t => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
  let id = 0; const pend = new Map(); const logs = [];
  ws.addEventListener('message', e => {
    const m = JSON.parse(e.data);
    if (m.method === 'Runtime.exceptionThrown') logs.push(m.params.exceptionDetails?.exception?.description?.split('\n')[0]);
    if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') logs.push(m.params.args.map(a => a.value ?? a.description).join(' '));
    const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); }
  });
  const send = (method, params = {}) => new Promise((res, rej) => {
    const n = ++id; const t = setTimeout(() => rej(new Error(method + ' timeout')), 240000);
    pend.set(n, m => { clearTimeout(t); res(m); }); ws.send(JSON.stringify({ id: n, method, params }));
  });
  const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
  await send('Emulation.setDeviceMetricsOverride', { width: W, height: H, deviceScaleFactor: 1, mobile: false });
  await send('Page.enable'); await send('Runtime.enable');
  return { send, ev, logs, close: () => { try { ws.close(); } catch {} chrome.kill(); } };
}

export async function open(S, slug, extra = '') {
  S.logs.length = 0;
  await S.send('Page.navigate', { url: `${BASE}/earth/world.html?world=${slug}${extra}` });
  const t0 = Date.now();
  while (Date.now() - t0 < 200000) {
    await sleep(500);
    const r = await S.ev('JSON.stringify(window.__wf||{})').catch(() => null);
    const w = r && JSON.parse(r);
    if (w?.ready) return w;
    if (w?.error) throw new Error(`${slug}: ${w.error}`);
  }
  throw new Error(`${slug}: not ready in 200 s; console: ${S.logs.slice(0, 3).join(' | ')}`);
}
export const shot = async (S, q = 88) => Buffer.from((await S.send('Page.captureScreenshot', { format: 'jpeg', quality: q })).result.data, 'base64');
export const hud = (S, show) => S.ev(`document.querySelectorAll('.panel').forEach(p=>p.style.visibility='${show ? 'visible' : 'hidden'}')`);
export const wf = (S, js) => S.ev(`(()=>{const w=window.__wf; ${js}})()`);

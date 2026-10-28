import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

const PORT = 9363;
const CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wfe-debug-'));

const chrome = spawn(CHROME, [
  '--headless=new',
  `--remote-debugging-port=${PORT}`,
  `--user-data-dir=${path.join(tmp, 'p')}`,
  '--use-gl=angle',
  '--use-angle=swiftshader-webgl',
  '--enable-unsafe-swiftshader',
  '--ignore-gpu-blocklist',
  '--enable-webgl',
  '--mute-audio',
  '--window-size=960,540',
  'about:blank'
], { stdio: ['ignore', 'pipe', 'pipe'] });

chrome.stderr.on('data', d => console.error('[chrome]', d.toString().trim()));

await new Promise(r => setTimeout(r, 4000));

const targets = await fetch(`http://127.0.0.1:${PORT}/json/list`).then(r => r.json());
const wsUrl = targets.find(t => t.type === 'page').webSocketDebuggerUrl;
const ws = new WebSocket(wsUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));

let id = 0;
const pend = new Map();

ws.addEventListener('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Runtime.exceptionThrown') {
    console.log('EXCEPTION:', m.params.exceptionDetails);
  }
  if (m.method === 'Runtime.consoleAPICalled') {
    console.log('CONSOLE:', m.params.type, m.params.args.map(a => a.value ?? a.description).join(' '));
  }
  const p = pend.get(m.id);
  if (p) { pend.delete(m.id); p(m); }
});

const send = (method, params = {}) => new Promise(res => {
  const n = ++id;
  const t = setTimeout(() => { console.log('TIMEOUT:', method); res(null); }, 30000);
  pend.set(n, m => { clearTimeout(t); res(m); });
  ws.send(JSON.stringify({ id: n, method, params }));
});

await send('Page.enable');
await send('Runtime.enable');

console.log('Navigating to world.html...');
await send('Page.navigate', { url: 'http://127.0.0.1:8094/earth/world.html?world=climate-dao' });

await new Promise(r => setTimeout(r, 12000));

const wf = await send('Runtime.evaluate', {
  expression: 'JSON.stringify(window.__wf || {})',
  returnByValue: true
});
console.log('__wf:', wf?.result?.result?.value);

chrome.kill();
ws.close();
console.log('Done');
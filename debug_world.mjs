import { spawn } from 'node:child_process';
import { sleep } from './earth/cdp.mjs';

const chrome = spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome', [
  '--headless=new', '--remote-debugging-port=9363',
  '--use-gl=angle', '--use-angle=swiftshader-webgl',
  '--mute-audio', 'about:blank'
], { stdio: 'ignore' });

await sleep(2000);
const targets = await fetch('http://127.0.0.1:9363/json/list').then(r => r.json());
const ws = new WebSocket(targets.find(t => t.type === 'page').webSocketDebuggerUrl);
await new Promise(r => ws.addEventListener('open', r, { once: true }));

let id = 0;
const pend = new Map();
const exceptions = [];

ws.on('message', e => {
  const m = JSON.parse(e.data);
  if (m.method === 'Runtime.exceptionThrown') {
    exceptions.push(m.params.exceptionDetails);
    console.log('EXCEPTION:', m.params.exceptionDetails.exception?.description?.split('\n').slice(0, 3).join(' | '));
  }
  if (m.method === 'Runtime.consoleAPICalled' && m.params.type === 'error') {
    console.log('ERROR:', m.params.args.map(a => a.value ?? a.description).join(' '));
  }
  const p = pend.get(m.id);
  if (p) { pend.delete(m.id); p(m); }
});

const send = (method, params) => new Promise(res => {
  const n = ++id;
  pend.set(n, res);
  ws.send(JSON.stringify({ id: n, method, params }));
});

const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;

await send('Page.enable');
await send('Runtime.enable');
await send('Page.navigate', { url: 'http://127.0.0.1:8094/earth/world.html?world=climate-dao' });

for (let i = 0; i < 16; i++) {
  await sleep(500);
  const wf = await ev('JSON.stringify(window.__wf||{})').catch(() => null);
  if (wf) {
    console.log('__wf at ' + (i * 0.5) + 's:', wf);
    break;
  }
}

console.log('Exceptions caught:', exceptions.length);
chrome.kill();
process.exit(0);

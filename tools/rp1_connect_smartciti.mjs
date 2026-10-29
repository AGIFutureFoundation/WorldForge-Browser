// rp1_connect_smartciti.mjs -- connect the SmartCiti and Cognition Dev Center companies to
// their full AGI Corp fabrics served from fly.io (worldforge/fabrics/):
//   SmartCiti -> /v2/rp1/fabric/smartciti-holodeck   (SmartCiti.X Holodeck)
//   Cognition -> /v2/rp1/fabric/cognition-x          (Cognition.X Campus)
// Verifies the loaded fabric's Resource references point at worldforge-api.fly.dev.
// Log: /tmp/rp1-smartciti.log
import fs from 'node:fs';

const PAIRS = [
  ['SmartCiti', 'smartciti-holodeck'],
  ['Cognition', 'cognition-x'],
];
const FABRIC = (slug) => `https://worldforge-api.fly.dev/v2/rp1/fabric/${slug}`;
const LOG = '/tmp/rp1-smartciti.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `smartciti/cognition connect, ${new Date().toISOString()}\n`);

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

for (const [company, slug] of PAIRS) {
  try {
    await goto('https://dev.rp1.com/home');
    const clicked = await ev(`(() => {
      const els = [...document.querySelectorAll('span, a, li, div, button')].filter(el => (el.innerText || '').trim() === ${JSON.stringify(company)} && el.children.length === 0);
      if (!els.length) return 'NAV_NOT_FOUND';
      els[els.length - 1].scrollIntoView({ block: 'center' });
      els[els.length - 1].click();
      return 'OK';
    })()`);
    await sleep(2500);
    const url = await ev('location.href');
    const m = /company\/(\d+)/.exec(url || '');
    if (clicked !== 'OK' || !m) { log(`FAIL ${company}: nav=${clicked} url=${url}`); continue; }
    const cid = m[1];
    log(`${company}: company id ${cid}`);

    await goto(`https://dev.rp1.com/company/${cid}/fabric/viewer`);
    const loaded = await ev(`(() => {
      const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
      if (!inp) return 'NO_INPUT';
      inp.focus(); inp.value = ${JSON.stringify(FABRIC(slug))};
      inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true }));
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Load Url');
      if (b) b.click();
      return 'LOADING';
    })()`);
    log(`${company} (${cid}): ${loaded}`);
    await sleep(6000); // the holodeck fabric is 48KB with many nodes + GLB fetches

    const verify = await ev(`(() => {
      const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
      const editor = (document.body.innerText || '').includes('Add RMPObject');
      // dump every visible input value that mentions worldforge-api (resource references)
      const wf = [...document.querySelectorAll('input')].map(i => i.value).filter(v => v && v.includes('worldforge-api.fly.dev')).slice(0, 6);
      const body = document.body.innerText || '';
      const refs = (body.match(/worldforge-api\\.fly\\.dev[^\\s]*/g) || []).slice(0, 6);
      return JSON.stringify({ urlKept: inp ? inp.value.slice(0, 90) : null, editorLoaded: editor, flyRefs: [...new Set([...wf, ...refs])].slice(0, 6) }, null, 1);
    })()`);
    const v = JSON.parse(verify || '{}');
    log(`${company} (${cid}) -> ${slug}: urlKept=${v.urlKept} editor=${v.editorLoaded}`);
    log(`  fly.io refs in viewer: ${JSON.stringify(v.flyRefs)}`);
    if (v.urlKept === FABRIC(slug)) log(`${company}: CONNECTED (fabric from fly.io)`);
    else log(`${company}: PROBLEM`);
  } catch (e) {
    log(`FAIL ${company}: ${String(e).slice(0, 160)}`);
  }
}
log('--- done');
ws.close();
process.exit(0);

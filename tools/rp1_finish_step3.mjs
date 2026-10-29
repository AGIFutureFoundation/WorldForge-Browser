// rp1_finish_step3.mjs -- fill step3 (Admin: the pattern from the completed companies) for the
// half-created companies and continue to completion, then load the fly.io fabric per company.
// Log: /tmp/rp1-step3-bulk.log
import fs from 'node:fs';

const COMPANIES = [
  [195, 's13-gonstead-x'], [196, 's14-askdoc-x'], [197, 's15-romanbridge-dao'], [198, 's16-echodawn-dao'],
  [199, 's17-curable-blockchain-dao'], [200, 'biota-blockchain'], [201, 's22-get-delivery-dao'],
  [202, 's24-donatello-dao'], [203, 's26-lyka-dao'], [204, 's27-genomic-dao'], [205, 's28-genomic-blockchain'],
  [206, 's34-als-dao'], [207, 's35-parkinsons-dao'],
];
const FABRIC = (slug) => `https://worldforge-api.fly.dev/v2/rp1/fabric/${slug}`;
const LOG = '/tmp/rp1-step3-bulk.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `step3 finisher: ${COMPANIES.length} companies, ${new Date().toISOString()}\n`);

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

for (const [cid, slug] of COMPANIES) {
  try {
    await goto(`https://dev.rp1.com/company/${cid}/step3`);
    const res = await ev(`(() => {
      const fill = (key, val) => {
        const i = [...document.querySelectorAll('input')].find(x => (x.placeholder || x.name || x.id || '') === key);
        if (!i) return false;
        i.focus(); i.value = val;
        i.dispatchEvent(new Event('input', { bubbles: true })); i.dispatchEvent(new Event('change', { bubbles: true }));
        return true;
      };
      const f = fill('First Name', 'Mike') && fill('Last Name', 'Rice') && fill('Title', 'Founder');
      if (!f) return 'FIELDS_MISSING url=' + location.href;
      const b = [...document.querySelectorAll('button')].filter(x => (x.offsetParent || x.getClientRects().length) && (x.innerText || '').trim() === 'Next');
      if (!b.length) return 'NO_NEXT';
      b[0].click();
      return 'NEXT_CLICKED';
    })()`);
    await sleep(4000);
    const url = await ev('location.href');
    log(`${cid} ${slug}: ${res} -> ${url}`);
    if (/step\d/.test(url) && !/step3/.test(url)) {
      const more = await ev(`(() => JSON.stringify([...document.querySelectorAll('input, select')].filter(i => i.offsetParent || i.getClientRects().length).map(i => ({ n: (i.name || i.id || i.placeholder || i.type || '?').slice(0, 50), v: (i.value || '').slice(0, 40) }))))()`);
      log(`${cid}: MORE STEPS ${url} fields: ${more}`);
      continue;
    }
    if (/step3/.test(url)) { log(`${cid}: still on step3 (fill failed?)`); continue; }
    // completed: load the fabric
    await goto(`https://dev.rp1.com/company/${cid}/fabric/viewer`);
    await ev(`(() => {
      const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
      if (!inp) return 'NO_INPUT';
      inp.focus(); inp.value = ${JSON.stringify(FABRIC(slug))};
      inp.dispatchEvent(new Event('input', { bubbles: true })); inp.dispatchEvent(new Event('change', { bubbles: true }));
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Load Url');
      if (b) b.click();
      return 'LOADING';
    })()`);
    await sleep(3500);
    const verify = await ev(`(() => {
      const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
      const editor = (document.body.innerText || '').includes('Add RMPObject');
      return JSON.stringify({ urlKept: inp ? inp.value.slice(0, 80) : null, editorLoaded: editor });
    })()`);
    const v = JSON.parse(verify || '{}');
    log(`${cid} ${slug}: ${v.urlKept === FABRIC(slug) && v.editorLoaded ? 'FABRIC-LOADED-OK' : 'FABRIC-PROBLEM ' + verify}`);
  } catch (e) {
    log(`FAIL ${cid} ${slug}: ${String(e).slice(0, 140)}`);
  }
}
log('--- step3 finisher done');
ws.close();
process.exit(0);

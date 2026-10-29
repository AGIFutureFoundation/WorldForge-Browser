// rp1_finish_step2.mjs -- complete the 13 half-created companies (stuck at /company/<id>/step2)
// using the established pattern (United States, LLC (S Corporation), "W3 LLC-<Name> Series <N> LLC"),
// then load each one's fly.io fabric in its Map Viewer. Log: /tmp/rp1-step2-bulk.log.
import fs from 'node:fs';

const COMPANIES = [
  [195, 'W3 LLC-Gonstead.X Series 13 LLC', 's13-gonstead-x'],
  [196, 'W3 LLC-AskDoc.X Series 14 LLC', 's14-askdoc-x'],
  [197, 'W3 LLC-RomanBridge.DAO Series 15 LLC', 's15-romanbridge-dao'],
  [198, 'W3 LLC-EchoDawn.DAO Series 16 LLC', 's16-echodawn-dao'],
  [199, 'W3 LLC-Curable Blockchain.DAO Series 17 LLC', 's17-curable-blockchain-dao'],
  [200, 'W3 LLC-BioDao.Blockchain Series 1 LLC', 'biota-blockchain'],
  [201, 'W3 LLC-Get Delivery.DAO Series 22 LLC', 's22-get-delivery-dao'],
  [202, 'W3 LLC-Donatello.DAO Series 24 LLC', 's24-donatello-dao'],
  [203, 'W3 LLC-Lyka.DAO Series 26 LLC', 's26-lyka-dao'],
  [204, 'W3 LLC-Genomic.DAO Series 27 LLC', 's27-genomic-dao'],
  [205, 'W3 LLC-Genomic Blockchain.DAO Series 28 LLC', 's28-genomic-blockchain'],
  [206, 'W3 LLC-ALS.DAO Series 34 LLC', 's34-als-dao'],
  [207, 'W3 LLC-Parkinsons.DAO Series 35 LLC', 's35-parkinsons-dao'],
];
const FABRIC = (slug) => `https://worldforge-api.fly.dev/v2/rp1/fabric/${slug}`;
const LOG = '/tmp/rp1-step2-bulk.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };
fs.writeFileSync(LOG, `step2 finisher: ${COMPANIES.length} companies, ${new Date().toISOString()}\n`);

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

for (const [cid, legal, slug] of COMPANIES) {
  try {
    await goto(`https://dev.rp1.com/company/${cid}/step2`);
    const res = await ev(`(() => {
      const setSel = (sel, val) => { sel.value = val; sel.dispatchEvent(new Event('input', { bubbles: true })); sel.dispatchEvent(new Event('change', { bubbles: true })); };
      const sels = [...document.querySelectorAll('select')];
      const country = sels.find(s => [...s.options].some(o => o.text === 'United States'));
      const etype = sels.find(s => [...s.options].some(o => o.text === 'LLC (S Corporation)'));
      if (!country || !etype) return 'SELECTS_MISSING ' + sels.length;
      setSel(country, 'US');
      setSel(etype, '7');
      const legal = [...document.querySelectorAll('input')].find(i => /legal name/i.test(i.placeholder || i.name || i.id || ''));
      if (!legal) return 'LEGAL_INPUT_MISSING';
      legal.focus(); legal.value = ${JSON.stringify(legal)};
      legal.dispatchEvent(new Event('input', { bubbles: true }));
      legal.dispatchEvent(new Event('change', { bubbles: true }));
      const vis = [...document.querySelectorAll('button')].filter(b => (b.offsetParent || b.getClientRects().length))
        .map(b => (b.innerText || '').trim().replace(/\\s+/g, ' ')).filter(Boolean);
      return JSON.stringify({ filled: true, visibleButtons: vis.slice(0, 15) });
    })()`);
    if (!res.startsWith('{')) { log(`FAIL ${cid} ${slug}: ${res}`); continue; }
    const vis = JSON.parse(res).visibleButtons;
    log(`${cid} ${slug}: filled; buttons: ${vis.join(' / ').slice(0, 180)}`);
    const want = ['Save', 'Save Changes', 'Continue', 'Next', 'Submit', 'Create', 'Finish', 'Complete', 'Update'];
    let clicked = null;
    for (const w of want) {
      const c = await ev(`(() => {
        const b = [...document.querySelectorAll('button')].filter(x => (x.offsetParent || x.getClientRects().length) && (x.innerText || '').trim() === ${JSON.stringify(w)});
        if (!b.length) return null;
        b[0].click(); return ${JSON.stringify(w)};
      })()`);
      if (c) { clicked = c; break; }
    }
    if (!clicked) { log(`WARN ${cid}: no submit button (buttons: ${vis.join('/')})`); continue; }
    await sleep(4000);
    const url = await ev('location.href');
    log(`${cid} ${slug}: clicked "${clicked}" -> ${url}`);
    if (/step\d/.test(url)) {
      const more = await ev(`(() => JSON.stringify([...document.querySelectorAll('input, select')].filter(i => i.offsetParent || i.getClientRects().length).map(i => ({ n: (i.name || i.id || i.placeholder || i.type || '?').slice(0, 50), v: (i.value || '').slice(0, 40) }))))()`);
      log(`${cid}: NEXT STEP ${url} fields: ${more}`);
      continue;
    }
    log(`${cid} ${slug}: reached ${url} -- fabric load pass next`);
  } catch (e) {
    log(`FAIL ${cid} ${slug}: ${String(e).slice(0, 140)}`);
  }
}
log('--- step2 finisher done');
ws.close();
process.exit(0);

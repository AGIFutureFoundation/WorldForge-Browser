// rp1_bulk_connect.mjs -- connect every mapped Dev Center company to its fly.io fabric:
// click company -> capture /company/<id> -> open its fabric viewer -> fill the fabric URL
// -> Load Url -> verify -> next. Progress written incrementally to /tmp/rp1-bulk.log.
// Companies map 1:1 to the mounted WorldForge worlds (slug); fabric = /v2/rp1/fabric/<slug>.
import fs from 'node:fs';

const MAP = [
  ['Empathic', 'empathic-x'],
  ['Curable', 's04-curable-x'],
  ['Bio Pharma', 's05-biopharma-go'],
  ['Blockchain', 's06-blockchain'],
  ['Locator', 'locator-x'],
  ['Aerospace', 's31-aerospace-dao'],
  ['InfoGurus', 's33-infogurus'],
  ['Incubator', 's21-incubator-dao'],
  ['Moscone Center', 's19-moscone-x'],
  ['Parking', 's12-parking-smart-x'],
  ['Solar', 's32-solar-dao'],
  ['CMMC', 's20-cmmc'],
  ['Meta', 's29-metaverse-dao'],
  ['Molecular', 's11-molecular'],
  ['Robotics', 'robotics-dao'],
  ['Chat', 's23-avatar-chat'],
  ['Divine', 's07-divine-dao'],
  ['My Pet', 's25-mypet-ai'],
  ['Astrological', 's09-astrological-x'],
  ['Gonstead', 's13-gonstead-x'],
  ['AskDoc', 's14-askdoc-x'],
  ['RomanBridge', 's15-romanbridge-dao'],
  ['EchoDawn', 's16-echodawn-dao'],
  ['Curable Blockchain', 's17-curable-blockchain-dao'],
  ['BioDao', 'biota-blockchain'],
  ['Get Delivery', 's22-get-delivery-dao'],
  ['Donatello', 's24-donatello-dao'],
  ['Lyka', 's26-lyka-dao'],
  ['Genomic', 's27-genomic-dao'],
  ['Genomic Blockchain', 's28-genomic-blockchain'],
  ['ALS', 's34-als-dao'],
  ['Parkinsons', 's35-parkinsons-dao'],
];
const FABRIC = (slug) => `https://worldforge-api.fly.dev/v2/rp1/fabric/${slug}`;
const LOG = '/tmp/rp1-bulk.log';
const log = (s) => { fs.appendFileSync(LOG, s + '\n'); };

fs.writeFileSync(LOG, `rp1 bulk connect: ${MAP.length} companies, start ${new Date().toISOString()}\n`);

const targets = await fetch('http://127.0.0.1:9222/json/list').then(r => r.json());
const page = targets.find(t => t.type === 'page' && t.url.includes('dev.rp1.com'));
if (!page) { log('FATAL: no dev.rp1.com tab open'); process.exit(1); }
const ws = new WebSocket(page.webSocketDebuggerUrl);
await new Promise((r, j) => { ws.addEventListener('open', r, { once: true }); ws.addEventListener('error', j, { once: true }); });
let id = 0; const pend = new Map();
ws.addEventListener('message', e => { const m = JSON.parse(e.data); const p = pend.get(m.id); if (p) { pend.delete(m.id); p(m); } });
const send = (method, params = {}) => new Promise(res => { const n = ++id; pend.set(n, res); ws.send(JSON.stringify({ id: n, method, params })); });
const ev = async (x) => (await send('Runtime.evaluate', { expression: x, awaitPromise: true, returnByValue: true })).result?.result?.value;
await send('Runtime.enable'); await send('Page.enable');
const sleep = (ms) => new Promise(r => setTimeout(r, ms));
const goto = async (url, settle = 2500) => { await send('Page.navigate', { url }); await sleep(settle); };

let okCount = 0, failCount = 0;
for (const [company, slug] of MAP) {
  try {
    // 1. go to the Dev Center home (the only page with the companies sidebar), then click
    await goto('https://dev.rp1.com/home', 2500);
    const clicked = await ev(`(() => {
      const els = [...document.querySelectorAll('span, a, li, div, button')].filter(el => (el.innerText || '').trim() === ${JSON.stringify(company)} && el.children.length === 0);
      if (!els.length) return 'NAV_NOT_FOUND';
      els[els.length - 1].scrollIntoView({ block: 'center' });
      els[els.length - 1].click();
      return 'OK';
    })()`);
    if (clicked !== 'OK') { log(`FAIL ${company} (${slug}): company not in sidebar`); failCount++; continue; }
    await sleep(2500);
    const url = await ev('location.href');
    const m = /company\/(\d+)\/home/.exec(url || '');
    if (!m) { log(`FAIL ${company} (${slug}): no company id (url=${url})`); failCount++; continue; }
    const cid = m[1];

    // 2. open its fabric viewer and load the fabric from fly.io
    await goto(`https://dev.rp1.com/company/${cid}/fabric/viewer`, 2500);
    const filled = await ev(`(() => {
      const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
      if (!inp) return 'INPUT_NOT_FOUND';
      inp.focus(); inp.value = ${JSON.stringify(FABRIC(slug))};
      inp.dispatchEvent(new Event('input', { bubbles: true }));
      inp.dispatchEvent(new Event('change', { bubbles: true }));
      return 'OK';
    })()`);
    if (filled !== 'OK') { log(`FAIL ${company} (company ${cid}, ${slug}): fabric url input missing`); failCount++; continue; }
    await ev(`(() => {
      const b = [...document.querySelectorAll('button')].find(x => (x.innerText || '').trim() === 'Load Url');
      if (b) b.click();
      return !!b;
    })()`);
    await sleep(3500);

    // 3. verify: the RMPObject editor present + url field persisted
    const verify = await ev(`(() => {
      const inp = [...document.querySelectorAll('input')].find(i => (i.placeholder || '').includes('MYURL.COM'));
      const editor = (document.body.innerText || '').includes('Add RMPObject');
      return JSON.stringify({ urlKept: inp ? inp.value.slice(0, 80) : null, editorLoaded: editor });
    })()`);
    const v = JSON.parse(verify || '{}');
    if (v.urlKept === FABRIC(slug) && v.editorLoaded) {
      log(`OK   ${company} (company ${cid}) -> ${slug} :: fabric loaded from fly.io`);
      okCount++;
    } else {
      log(`WARN ${company} (company ${cid}) -> ${slug} :: urlKept=${v.urlKept} editor=${v.editorLoaded}`);
      failCount++;
    }
  } catch (e) {
    log(`FAIL ${company} (${slug}): ${String(e).slice(0, 120)}`);
    failCount++;
  }
}
log(`--- done: ${okCount} connected, ${failCount} failed, of ${MAP.length}`);
ws.close();
process.exit(0);

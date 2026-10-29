// motion_check.mjs -- end-to-end check of the Movement LM pipeline:
//   1. motion-lm.html loads model.json in-browser, stats render, UI sampling produces a valid sequence
//   2. a world page records schema /3 robot episodes (joint traces) and human union-module motions,
//      and exposes the "Movement corpus" download
// Usage: node earth/motion_check.mjs   (needs earth/serve.mjs on :8094)
import { session, open, sleep, BASE } from './cdp.mjs';
import fs from 'node:fs';

fs.mkdirSync('/tmp/motion', { recursive: true });
let bad = 0;
const S = await session(1280, 800);
try {
  // ---- 1. motion-LM dashboard
  S.logs.length = 0;
  await S.send('Page.navigate', { url: `${BASE}/earth/motion-lm.html` });
  let ok = false;
  for (let i = 0; i < 60 && !ok; i++) {
    await sleep(500);
    ok = await S.ev('document.querySelectorAll("#stats div").length >= 6 && document.querySelectorAll("#gallery .card").length > 0');
  }
  if (!ok) { console.log('MOTION-LM: model/gallery did not load'); bad++; }
  else {
    const stats = await S.ev('document.getElementById("curve-note").textContent');
    console.log('MOTION-LM:', stats);
    await S.send('Page.navigate', { url: `${BASE}/earth/motion-lm.html` });
    await sleep(4000);
    const gen = await S.ev('(function(){ document.getElementById("gen").click(); return "clicked"; })()');
    await sleep(3000);
    const info = await S.ev('document.getElementById("geninfo").textContent');
    console.log('MOTION-LM sample:', info);
    if (!/structurally valid|ragged/.test(info)) bad++;
    const shot = await S.send('Page.captureScreenshot', { format: 'png', captureBeyondViewport: false });
    fs.writeFileSync('/tmp/motion/motion-lm.png', Buffer.from(shot.result?.data ?? shot.data, 'base64'));
  }
  if (S.logs.length) { console.log('  js errors:', S.logs.slice(0, 3).join(' | ')); bad++; }

  // ---- 2. world page: schema /3 records + human motions + corpus button
  S.logs.length = 0;
  const w = await open(S, 'climate-dao', '', { timeoutMs: 90000 });
  await sleep(6000);                                     // let robot episodes tick + record
  const probe = JSON.parse(await S.ev(`(function(){
    const btns = [...document.querySelectorAll('#game button')].map(b => b.textContent);
    const t = window.__wf.training;
    t.startScenario(window.__wf.trainingScenarios[0]);
    for (let i = 0; i < 4; i++) t.completeStep();
    return JSON.stringify({
      ready: !!window.__wf.ready, records: window.__wf.records(),
      humanMotions: t.getMotions().length,
      humanSteps: (t.getMotions()[0] || {steps: []}).steps.length,
      humanMoves: ((t.getMotions()[0] || {steps: [{moves: []}]}).steps[0].moves || []).length,
      corpusBtn: btns.includes('Movement corpus') });
  })()`));
  console.log('WORLD:', JSON.stringify(probe));
  const good = probe.ready && probe.records > 0 && probe.humanMotions >= 1 && probe.humanSteps === 4
    && probe.humanMoves >= 2 && probe.corpusBtn;
  if (!good) bad++;
  if (S.logs.length) { console.log('  js errors:', S.logs.slice(0, 3).join(' | ')); bad++; }
} catch (e) { console.log('FAIL ' + e.message); bad++; }
finally { S.close(); }
console.log(bad ? 'MOTION CHECK FAILED' : 'MOTION CHECK PASSED');
process.exit(bad ? 1 : 0);

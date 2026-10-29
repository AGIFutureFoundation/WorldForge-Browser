// motion-lm.js: in-browser inference for wf-motion-lm-1 (numpy-trained tiny GPT) + PS2-style
// movement replay. Loads data/motion/model.json + samples.json; static page, no server logic.
const $ = (id) => document.getElementById(id);

function gelu(x) { return 0.5 * x * (1 + Math.tanh(0.7978845608 * (x + 0.044715 * x ** 3))); }

function ln(x, t, d, g, b) {          // layernorm row t of a T x d array
  let mu = 0; for (let j = 0; j < d; j++) mu += x[t * d + j]; mu /= d;
  let v = 0; for (let j = 0; j < d; j++) { const u = x[t * d + j] - mu; v += u * u; }
  v = Math.sqrt(v / d + 1e-5);
  const o = new Float64Array(d);
  for (let j = 0; j < d; j++) o[j] = ((x[t * d + j] - mu) / v) * g[j] + b[j];
  return o;
}

function matvec(h, W, m, k, out, outOff, bias) {   // h (m) @ W (m x k) + bias (k)
  for (let j = 0; j < k; j++) out[outOff + j] = bias ? bias[j] : 0;
  for (let i = 0; i < m; i++) { const hi = h[i], wo = i * k;
    for (let j = 0; j < k; j++) out[outOff + j] += hi * W[wo + j]; }
}

class Runtime {
  constructor(model) {
    this.cfg = model.config; this.itos = model.itos; this.metrics = model.metrics;
    this.stoi = {}; model.itos.forEach((t, i) => this.stoi[t] = i);
    this.W = {};
    for (const [k, v] of Object.entries(model.weights))
      this.W[k] = Float64Array.from(v.data);
  }

  forward(ids) {                       // batch=1 causal forward -> logits [T x V]
    const { d, n_layer: L, n_head: H, vocab: V } = this.cfg, dh = d / H, T = ids.length, W = this.W;
    const x = new Float64Array(T * d);
    for (let t = 0; t < T; t++) for (let j = 0; j < d; j++)
      x[t * d + j] = W['emb'][ids[t] * d + j] + W['pos'][t * d + j];
    for (let i = 0; i < L; i++) {
      const h1 = new Array(T);
      for (let t = 0; t < T; t++) h1[t] = ln(x, t, d, W[`l${i}_ln1_g`], W[`l${i}_ln1_b`]);
      const qkv = new Float64Array(T * 3 * d);
      for (let t = 0; t < T; t++) matvec(h1[t], W[`l${i}_wqkv`], d, 3 * d, qkv, t * 3 * d, W[`l${i}_bqkv`]);
      const ao = new Float64Array(T * d), scale = 1 / Math.sqrt(dh);
      for (let t = 0; t < T; t++) for (let h = 0; h < H; h++) {
        const att = new Float64Array(t + 1), qs = t * 3 * d + h * dh;
        let mx = -Infinity;
        for (let s = 0; s <= t; s++) { let dot = 0; const ks = s * 3 * d + d + h * dh;
          for (let j = 0; j < dh; j++) dot += qkv[qs + j] * qkv[ks + j];
          att[s] = dot * scale; mx = Math.max(mx, att[s]); }
        let sm = 0; for (let s = 0; s <= t; s++) { att[s] = Math.exp(att[s] - mx); sm += att[s]; }
        for (let s = 0; s <= t; s++) { att[s] /= sm; const vs = s * 3 * d + 2 * d + h * dh;
          for (let j = 0; j < dh; j++) ao[t * d + h * dh + j] += att[s] * qkv[vs + j]; }
      }
      const x2 = new Float64Array(T * d), proj = new Float64Array(T * d);
      for (let t = 0; t < T; t++) matvec(ao.subarray(t * d, t * d + d), W[`l${i}_wo`], d, d, proj, t * d, null);
      for (let t = 0; t < T; t++) for (let j = 0; j < d; j++) x2[t * d + j] = x[t * d + j] + proj[t * d + j];
      const u1 = new Float64Array(4 * d), g1 = new Float64Array(4 * d), f2 = new Float64Array(T * d);
      for (let t = 0; t < T; t++) {
        const h2 = ln(x2, t, d, W[`l${i}_ln2_g`], W[`l${i}_ln2_b`]);
        matvec(h2, W[`l${i}_w1`], d, 4 * d, u1, 0, W[`l${i}_b1`]);
        for (let j = 0; j < 4 * d; j++) g1[j] = gelu(u1[j]);
        matvec(g1, W[`l${i}_w2`], 4 * d, d, f2, t * d, W[`l${i}_b2`]);
        for (let j = 0; j < d; j++) x[t * d + j] = x2[t * d + j] + f2[t * d + j];
      }
    }
    const logits = new Float64Array(T * V);
    for (let t = 0; t < T; t++)
      matvec(ln(x, t, d, W['lnf_g'], W['lnf_b']), W['head_w'], d, V, logits, t * V, W['head_b']);
    return logits;
  }

  sample(agent, task, temp = 0.9, topk = 20, n = 90) {   // -> token strings
    const ids = [this.stoi['<s>'], this.stoi[agent], this.stoi[task]], V = this.cfg.vocab;
    while (ids.length < n) {
      const logits = this.forward(ids), off = (ids.length - 1) * V;
      const order = Array.from({ length: V }, (_, i) => i).sort((a, b) => logits[off + b] - logits[off + a]).slice(0, topk);
      let mx = logits[off + order[0]];
      let s = 0; const w = order.map(i => { const e = Math.exp(logits[off + i] / temp - mx / temp); s += e; return e; });
      let r = Math.random() * s, nxt = order[order.length - 1];
      for (let k = 0; k < order.length; k++) { r -= w[k]; if (r <= 0) { nxt = order[k]; break; } }
      ids.push(nxt);
      if (nxt === this.stoi['</s>']) break;
    }
    return ids.map(i => this.itos[i]);
  }
}

// ---------- token stream -> movement script (mirrors earth/motion decode_script) ----------
const DEQ = { DIR: b => b * 22.5, DIST: b => Math.max(0.5, 2 ** b - 1), KG: b => Math.max(0.5, 2 ** b - 1),
  DEG: b => b * 15, SEC: b => Math.max(1, 2 ** b - 1), SLOPE: b => b * 10, AMP: b => b * 0.3 };

function decodeScript(tokens) {
  const steps = []; let cur = null, pend = [];
  const flush = () => { if (cur !== null) steps.push({ step: cur, dur_s: null, moves: pend }); cur = null; pend = []; };
  for (const t of tokens) {
    if (t === '</s>') break;
    const fam = t.includes('_') ? t.split('_')[0] : t;
    if (t.startsWith('STEP_')) { flush(); cur = +t.slice(5); }
    else if (t.startsWith('SEC_') && steps.length && steps[steps.length - 1].dur_s === null)
      steps[steps.length - 1].dur_s = DEQ.SEC(+t.slice(4));
    else if (['OUT', 'AG', 'TASK', '<s>', '<pad>'].includes(fam)) continue;
    else if (['WALK', 'MOVE', 'LIFT', 'CARRY', 'PLACE', 'INSPECT', 'TYPE', 'BEND', 'REACH', 'PRESS', 'CHECK', 'GAIT', 'RESUME'].includes(fam))
      pend.push({ v: fam });
    else if (DEQ[fam] && pend.length) {
      const key = { DIR: 'dir_deg', DIST: 'm', KG: 'kg', DEG: 'deg', AMP: 'amp' }[fam];
      if (key) pend[pend.length - 1][key] = DEQ[fam](+t.split('_')[1]);
    }
  }
  flush();
  return { steps, outcome: tokens.includes('OUT_TIMEOUT') ? 'timeout' : 'success' };
}

// ---------- PS2-style replay: path + action pulses on a pixelated canvas ----------
function playScript(canvas, chips, tokens, agent) {
  const script = decodeScript(tokens), ctx = canvas.getContext('2d');
  canvas.width = Math.max(320, canvas.clientWidth | 0);
  canvas.height = Math.max(200, canvas.clientHeight | 0);
  const scale = 3.2;                                   // metres -> px
  const isHuman = agent === 'AG_HUMAN';
  const acts = [];
  script.steps.forEach((s, i) => s.moves.forEach(m => acts.push({ ...m, step: i })));
  let px = canvas.width / 2, py = canvas.height / 2, heading = 0;
  const hist = [];
  chips.innerHTML = '';
  let t = 0, raf = 0;
  function draw() {
    ctx.imageSmoothingEnabled = false;
    ctx.fillStyle = '#0d1620'; ctx.fillRect(0, 0, canvas.width, canvas.height);
    ctx.strokeStyle = 'rgba(60,90,110,.15)'; ctx.lineWidth = 1;
    for (let g = 0; g < canvas.width; g += 40) { ctx.beginPath(); ctx.moveTo(g, 0); ctx.lineTo(g, canvas.height); ctx.stroke(); }
    for (let g = 0; g < canvas.height; g += 40) { ctx.beginPath(); ctx.moveTo(0, g); ctx.lineTo(canvas.width, g); ctx.stroke(); }
    ctx.lineWidth = 3;
    for (let i = 1; i < hist.length; i++) {
      ctx.strokeStyle = ['#34d399', '#60a5fa', '#c792ea', '#fbbf24'][hist[i].step % 4];
      ctx.beginPath(); ctx.moveTo(hist[i - 1].x, hist[i - 1].y); ctx.lineTo(hist[i].x, hist[i].y); ctx.stroke();
    }
    ctx.save(); ctx.translate(px, py); ctx.rotate(heading);
    if (isHuman) {
      ctx.fillStyle = '#f5f0e6'; ctx.fillRect(-3, -8, 6, 10);         // torso
      ctx.fillStyle = '#ffb26b'; ctx.fillRect(-2, -13, 4, 4);         // head
    } else {
      ctx.fillStyle = '#f2c200'; ctx.fillRect(-6, -6, 12, 12);        // chunky robot
      ctx.fillStyle = '#1c1c1c'; ctx.fillRect(-6, -6, 12, 3);
      ctx.fillStyle = '#88ccff'; ctx.fillRect(2, -2, 3, 3);
    }
    ctx.restore();
    if (t > 0 && acts[t - 1] && acts[t - 1].v !== 'WALK' && acts[t - 1].v !== 'MOVE') {
      const a = acts[t - 1];
      ctx.fillStyle = 'rgba(124,247,212,.9)'; ctx.font = '600 12px monospace';
      ctx.fillText(a.v + (a.kg ? ` ${a.kg}kg` : a.s ? ` ${a.s}s` : a.deg ? ` ${a.deg}°` : ''), px + 10, py - 10);
    }
  }
  function step() {
    if (t >= acts.length) { draw(); return; }
    const a = acts[t];
    if (a.v === 'WALK' || a.v === 'MOVE') {
      heading = ((a.dir_deg ?? 0) - 90) * Math.PI / 180;              // compass heading -> screen
      const dist = (a.m ?? 3) * scale, frames = 14;
      const x0 = px, y0 = py, x1 = px + Math.cos(heading) * dist, y1 = py + Math.sin(heading) * dist;
      let f = 0;
      const glide = () => {
        f++; px = x0 + (x1 - x0) * f / frames; py = y0 + (y1 - y0) * f / frames;
        hist.push({ x: px, y: py, step: a.step }); draw();
        if (f < frames) raf = requestAnimationFrame(glide);
        else { t++; step(); }
      };
      raf = requestAnimationFrame(glide);
    } else {
      const chip = document.createElement('span');
      chip.className = `chip s${a.step % 4}`;
      chip.textContent = a.v + (a.kg ? ` ${a.kg}kg` : a.s ? ` ${a.s}s` : a.deg ? ` ${a.deg}°` : a.amp !== undefined ? ` amp ${a.amp}` : '');
      chips.appendChild(chip);
      draw(); t++; setTimeout(step, 420);
    }
  }
  cancelAnimationFrame(raf);
  draw(); step();
  return script;
}

// ---------- page wiring ----------
const AGENT_LABELS = { AG_HUMAN: 'Human trainee', AG_ROBOT_QUAD: 'Quadruped (Spot/Go2)', AG_ROBOT_HUM: 'Humanoid (TALOS/NAO)',
  AG_ROBOT_ARM: 'Arm (UR10e/FR3/Gen3)', AG_ROBOT_WHEELED: 'Wheeled (Husky/Fetch)', AG_ROBOT_DRONE: 'Drone (Crazyflie)' };
const slug = (s) => s.toLowerCase().replace(/[^a-z0-9]+/g, '-');

async function main() {
  const [model, samples] = await Promise.all([
    fetch('data/motion/model.json').then(r => r.json()),
    fetch('data/motion/samples.json').then(r => r.json()).catch(() => null),
  ]);
  const rt = new Runtime(model), m = model.metrics;
  $('stats').innerHTML = [
    [m.episodes, 'movement episodes'], [m.robot_episodes, 'robot episodes'], [m.human_episodes, 'human episodes'],
    [(m.params / 1000).toFixed(0) + 'k', 'parameters'], [m.val_ppl, 'val perplexity'],
    [(m.validity * 100).toFixed(0) + '%', 'valid samples'], [(m.train_tokens / 1000).toFixed(0) + 'k', 'train tokens'],
    [model.config.d + 'd·' + model.config.n_layer + 'L', 'tiny GPT'],
  ].map(([b, s]) => `<div><b>${b}</b><span>${s}</span></div>`).join('');
  const c = $('loss'); c.width = c.clientWidth; c.height = c.clientHeight;
  const ctx = c.getContext('2d'), curve = m.curve;
  const mx = Math.max(...curve.map(p => p.train_nll)) * 1.1;
  const plot = (key, color) => { ctx.strokeStyle = color; ctx.lineWidth = 2; ctx.beginPath();
    curve.forEach((p, i) => { const x = 30 + i * (c.width - 50) / (curve.length - 1),
      y = c.height - 14 - (p[key] / mx) * (c.height - 28); i ? ctx.lineTo(x, y) : ctx.moveTo(x, y); });
    ctx.stroke(); };
  plot('train_nll', '#34d399'); plot('val_nll', '#60a5fa');
  ctx.font = '11px monospace'; ctx.fillStyle = '#34d399'; ctx.fillText('train', 34, 12);
  ctx.fillStyle = '#60a5fa'; ctx.fillText('val', 80, 12);
  $('curve-note').textContent = `final: train nll ${curve[curve.length - 1].train_nll} · val ppl ${m.val_ppl} · trained locally in ${m.seconds}s (numpy, no API keys)`;
  const humanTasks = model.tasks.human, robotTasks = model.tasks.robots;
  const fillTasks = (isHuman) => {
    $('task').innerHTML = (isHuman ? humanTasks : robotTasks)
      .map(n => `<option value="TASK_${isHuman ? slug(n) : 'ROBOT_' + n}">${n}</option>`).join('');
  };
  Object.entries(AGENT_LABELS).forEach(([k, v]) => {
    const o = document.createElement('option'); o.value = k; o.textContent = v; $('agent').appendChild(o);
  });
  fillTasks(true);
  $('agent').onchange = () => fillTasks($('agent').value === 'AG_HUMAN');
  $('temp').oninput = () => $('tempv').textContent = $('temp').value;
  $('gen').onclick = () => {
    $('geninfo').textContent = 'sampling…';
    setTimeout(() => {
      const toks = rt.sample($('agent').value, $('task').value, +$('temp').value);
      const valid = toks.includes('</s>') && toks.filter(t => t.startsWith('STEP_')).length >= 2;
      $('geninfo').textContent = `${toks.length} tokens · ${valid ? 'structurally valid' : 'ragged'} · outcome: ${decodeScript(toks).outcome}`;
      playScript($('replay'), $('chips'), toks, $('agent').value);
    }, 30);
  };
  if (samples) {
    $('gallery').innerHTML = samples.generated.map((g, i) =>
      `<div class="card" data-i="${i}"><b>${AGENT_LABELS[g.agent] || g.agent} · ${g.task.replace('TASK_', '')}</b>` +
      `<div class="tok">${g.tokens.slice(3, 26).join(' ')} …</div>` +
      `<div style="margin-top:6px;font-size:.7rem;color:${g.valid ? '#34d399' : '#fbbf24'}">${g.valid ? 'valid' : 'ragged'} · ${g.script.outcome}</div></div>`).join('');
    $('gallery').querySelectorAll('.card').forEach(el => el.onclick = () => {
      const g = samples.generated[+el.dataset.i];
      playScript($('replay'), $('chips'), g.tokens, g.agent);
    });
    const first = samples.generated.find(g => g.valid);
    if (first) setTimeout(() => playScript($('replay'), $('chips'), first.tokens, first.agent), 400);
  }
}
main().catch(e => { $('geninfo').textContent = 'model load failed: ' + e.message; });


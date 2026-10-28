// HUD: facts, credits, world/trades/programs panels, quiz, avatar talk, game buttons, JSONL export, module panels
import * as THREE from 'three';
import { onState, award } from './play.js';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

export function showModule(modId, mods) {
  const mod = mods[modId]; if (!mod) return;
  const panel = document.getElementById('module-panel'); if (!panel) return;
  panel.querySelector('.module-content').innerHTML = `<h3>${esc(mod.title)}</h3><p>${esc(mod.content || '')}</p><div class="module-actions"><button onclick="window.__wf.closeModule()">Close</button><button onclick="window.__wf.startModule('${modId}')">Start Training</button></div>`;
  panel.style.display = 'block';
}

export function wireHud({ slug, geo, img, world, trades, programs, course, counts, S, avatars, fleet, fly }) {
  $('facts').innerHTML = Object.entries(counts).map(([k, v]) => `<span><b>${v === true ? 'yes' : v === false ? 'no' : esc(v)}</b> ${esc(k)}</span>`).join('');
  $('credit').textContent = [img.credit, ...geo.attribution, 'HD foliage: Poly Haven (CC0)'].join(' · ');
  if (world) {
    const bldgs = (world.districts || []).flatMap(d => d.buildings || []);
    const bDetails = bldgs.length ? bldgs.map(b => `${esc(b.name)} (${esc(b.floors)} fl, ${esc(b.use)})`).join(', ') : 'Real OSM buildings';
    $('about').innerHTML = `<p>${esc(world.summary)}</p>
      <details><summary>🏢 Buildings & Streets</summary><p>${bDetails}</p><p>Streets: ${esc((world.districts||[]).map(d=>d.real_anchor).join(', '))}</p></details>`;
  }

  if (trades && trades.scenarios) {
    const mods = trades.modules || {};
    const mj = JSON.stringify(mods).replace(/"/g, '&quot;');
    $('trades').innerHTML = trades.scenarios.map(s => {
      const mod = mods[s.module_link] || {};
      const mb = mod.id ? `<button class="module-btn" onclick="window.__wf.showModule('${s.module_link}',${mj})">Module</button>` : '';
      return `<details><summary>${esc(s.trade||s.level||'')} · ${esc(s.certification_level||'')}${mb}</summary><p><b>${esc(s.task||'')}</b></p>${s.location?`<p>${esc(s.location)}</p>`:''}${(s.learning_objectives||[]).map(o=>`<p>${esc(o)}</p>`).join('')}${s.duration_minutes?`<p>${esc(s.duration_minutes)} min</p>`:''}</details>`;
    }).join('') + (trades.credential?`<p class="muted">Credential: <b>${esc(trades.credential.name)}</b></p>`:'');
  }
  if (trades && trades.k12_programs) {
    const mods = trades.modules || {};
    const mj = JSON.stringify(mods).replace(/"/g, '&quot;');
    $('trades').innerHTML += '<h3>K-12 Programs</h3>' + trades.k12_programs.map(p => {
      const mod = mods[p.module_link] || {};
      const mb = mod.id ? `<button class="module-btn" onclick="window.__wf.showModule('${p.module_link}',${mj})">Module</button>` : '';
      return `<details><summary>${esc(p.title)} (Grade ${esc(p.grade||'')})${mb}</summary>${(p.sessions||[]).map(s=>`<p><b>${esc(s.zone)}</b>: ${esc(s.activity)} (${esc(s.minutes)} min)</p>`).join('')}</details>`;
    }).join('');
  }
  if (trades && trades.ngo_programs) {
    const mods = trades.modules || {};
    const mj = JSON.stringify(mods).replace(/"/g, '&quot;');
    $('trades').innerHTML += '<h3>NGO Programs</h3>' + trades.ngo_programs.map(p => {
      const mod = mods[p.module_link] || {};
      const mb = mod.id ? `<button class="module-btn" onclick="window.__wf.showModule('${p.module_link}',${mj})">Module</button>` : '';
      return `<details><summary>${esc(p.title)}${mb}</summary>${(p.sessions||[]).map(s=>`<p><b>${esc(s.zone)}</b>: ${esc(s.activity)} (${esc(s.minutes)} min)</p>`).join('')}</details>`;
    }).join('');
  }
  if (trades && trades.un_programs) {
    const mods = trades.modules || {};
    const mj = JSON.stringify(mods).replace(/"/g, '&quot;');
    $('trades').innerHTML += '<h3>UN Programs</h3>' + trades.un_programs.map(p => {
      const mod = mods[p.module_link] || {};
      const mb = mod.id ? `<button class="module-btn" onclick="window.__wf.showModule('${p.module_link}',${mj})">Module</button>` : '';
      return `<details><summary>${esc(p.title)}${mb}</summary>${(p.sessions||[]).map(s=>`<p><b>${esc(s.zone)}</b>: ${esc(s.activity)} (${esc(s.minutes)} min)</p>`).join('')}</details>`;
    }).join('');
  }

  if (programs && programs.programs) $('programs').innerHTML = programs.programs.map(p => `<details><summary>${esc(p.audience).toUpperCase()} · ${esc(p.title)}</summary><p>${esc(p.grade_or_level)}</p><ul>${p.sessions.map(s => `<li>${esc(s.zone)}: ${esc(s.activity)} (${esc(s.minutes)} min)</li>`).join('')}</ul><p class="muted">Data shared: ${esc(p.data_shared)}<br>Consent: ${esc(p.consent)}</p></details>`).join('');
  if (course && course.checkpoints) {
    $('quiz').innerHTML = `<b>${esc(course.title)}</b>` + course.checkpoints.map((k, i) => `<div class="qz" data-i="${i}"><p>${esc(k.zone)}: ${esc(k.q)}</p>${k.choices.map((ch, j) => `<button data-j="${j}">${esc(ch)}</button>`).join('')}</div>`).join('');
    $('quiz').onclick = (e) => { const bt = e.target.closest('button'); if (!bt) return; const box = bt.closest('.qz'), k = course.checkpoints[+box.dataset.i];
      if (box.dataset.done) return; box.dataset.done = 1; const ok = +bt.dataset.j === k.answer; bt.classList.add(ok ? 'ok' : 'no');
      if (ok) award(k.xp, `quiz: ${k.zone}`); else box.querySelectorAll('button')[k.answer].classList.add('ok'); };
  }
  onState(s => { $('xp').textContent = `${s.xp} XP`; $('log').innerHTML = s.log.map(l => `<li>${esc(l)}</li>`).join(''); });
  $('goRobots').onclick = () => { const e = fleet.userData.episodes[0]; if (e) fly(e.o.position, 18); };
  $('jsonl').onclick = () => {
    const blob = new Blob([fleet.userData.jsonl()], { type: 'application/x-ndjson' });
    Object.assign(document.createElement('a'), { href: URL.createObjectURL(blob), download: `${slug}-robot-episodes.jsonl` }).click();
  };
  setInterval(() => { const n = fleet.userData.records.length;
    $('eps').textContent = `${n} robot episodes recorded`;
    window.__wfGame?.episodes?.(n); }, 1000);

  function robotSheet(e) {
    const s = e.t, task = e.task;
    return `<b style="color:#34d399">${s.brand} ${s.model}</b> <span class="muted">(${s.cls}, to manufacturer spec)</span>
      <p style="margin:2px 0">dims ${s.size[0]}×${s.size[1]}×${s.size[2]} m · ${s.mass_kg} kg · payload ${s.payload_kg} kg · ${s.dof} DOF</p>
      <p style="margin:2px 0">sensors: ${(s.sensors || []).join(', ')} · ${s.facts}</p>
      <p style="margin:2px 0">task: ${esc(task.id)} in ${esc(task.zone)} — ${esc(task.goal || '')}</p>
      <p class="muted" style="margin:2px 0">human-in-loop: ${esc(task.human_in_loop || 'n/a')}</p>`;
  }

  S.renderer.domElement.addEventListener('click', (ev) => {
    const r = new THREE.Raycaster(), rect = ev.target.getBoundingClientRect();
    r.setFromCamera(new THREE.Vector2((ev.clientX - rect.left) / rect.width * 2 - 1, -(ev.clientY - rect.top) / rect.height * 2 + 1), S.camera);
    // avatars (Omega Steward, Hermes, Coach, Hive) + game-layer NPCs, pavilions and easter eggs
    const talkables = [...(avatars.userData.talkers || []), ...(window.__wfTalkers || [])];
    let hit = r.intersectObjects(talkables, true)[0];
    if (hit) {
      let o = hit.object; while (o && !o.userData.who) o = o.parent;
      if (o) {
        if (o.userData.egg !== undefined) { window.__wfGame?.egg?.(o.userData.egg);
          $('talk').innerHTML = `<b style="color:#ffd34d">${esc(o.userData.who)}</b><p>${esc(o.userData.say?.found || 'Seal collected.')}</p>
            <p class="muted">Easter egg ${o.userData.egg + 1}/3 — the Steward Seals.</p>`;
          return; }
        $('talk').innerHTML = `<b>${esc(o.userData.who)}</b>${o.userData.role ? ` <span class="muted">(${esc(o.userData.role)})</span>` : ''}${Object.values(o.userData.say || {}).map(t => `<p>${esc(t)}</p>`).join('')}`;
        window.__wfGame?.talk?.(o.userData.who);
        award(5, `talked with ${o.userData.who}`);
        return;
      }
    }
    // robot twins: click one for its manufacturer spec sheet
    hit = r.intersectObjects(fleet.children, true)[0];
    if (hit) {
      let o = hit.object; while (o && !o.userData.spec) o = o.parent;
      if (!o) return;
      const e = fleet.userData.episodes.find(x => x.o === o);
      if (e) { $('talk').innerHTML = robotSheet(e); award(3, `inspected ${e.t.brand} ${e.t.model}`); }
    }
  });
  window.__wf = window.__wf || {};
  window.__wf.showModule = showModule;
  window.__wf.closeModule = () => { document.getElementById('module-panel').style.display = 'none'; };
  window.__wf.startModule = (id) => { award(25, `started module ${id}`); window.__wf.closeModule(); };
}

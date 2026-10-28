// WorldForge Earth game layer: NPC-style agents (one per district, from the world doc), district
// pavilions whose signs open the zone's interior spaces (rooms, props, buildings) on click,
// three hidden Steward Seals (easter eggs), and a gamified learning board: levels, badges and
// missions derived from THIS world's quests + trades data. Nothing invents facts: names, roles,
// rooms and props come from earth/team content; lines that reference quests use quest titles.
import * as THREE from 'three';
import { state, onState, award } from './play.js';

function label(text, color = '#fff', size = 30) {
  const c = document.createElement('canvas'), x = c.getContext('2d');
  x.font = `600 ${size}px system-ui`; const w = Math.min(x.measureText(text).width + 26, 720);
  c.width = w; c.height = size + 20; x.font = `600 ${size}px system-ui`;
  x.fillStyle = 'rgba(10,20,30,.72)'; x.beginPath(); x.roundRect(0, 0, w, size + 20, 12); x.fill();
  x.fillStyle = color; x.fillText(text, 13, size + 4);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthTest: false }));
  s.scale.set(w / 16, (size + 20) / 16, 1); s.renderOrder = 10; return s;
}
const figColors = { Coach: 0xff7a1a, 'Safety Steward': 0xffd34d, 'Fleet Lead': 0x6ad1ff, 'Data Clerk': 0x9be7c4,
  'Community Guide': 0xc792ea, 'Site Steward': 0xf5f0e6, 'Neighborhood Liaison': 0x7cf7d4 };

function npcFigure(name) {
  const g = new THREE.Group(), m = new THREE.MeshStandardMaterial({ color: figColors[name] || 0x8fb3c9, roughness: 0.5, metalness: 0.1 });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.34, 0.95, 4, 10), m); body.position.y = 0.9;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.25, 16, 12), m); head.position.y = 1.8;
  const badge = new THREE.Mesh(new THREE.CylinderGeometry(0.09, 0.09, 0.22, 12),
    new THREE.MeshBasicMaterial({ color: 0x34d399 })); badge.position.set(0.28, 1.25, 0); badge.rotation.z = 0.5;
  g.add(body, head, badge);
  g.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return g;
}

// one district pavilion: arch + sign; click walks up the interior (rooms / props / buildings)
function pavilion(district, ground, angle, radius) {
  const g = new THREE.Group();
  const p1 = new THREE.Mesh(new THREE.CylinderGeometry(0.35, 0.45, 5.4, 10), new THREE.MeshStandardMaterial({ color: 0x2c4050, roughness: 0.8 }));
  const p2 = p1.clone(); const span = 4.6;
  p1.position.set(-span / 2, 2.7, 0); p2.position.set(span / 2, 2.7, 0);
  const beam = new THREE.Mesh(new THREE.BoxGeometry(span + 1, 0.5, 1.2), new THREE.MeshStandardMaterial({ color: 0x34d399, roughness: 0.4 }));
  beam.position.y = 5.5;
  const mdl = new THREE.Mesh(new THREE.ConeGeometry(0.7, 1.5, 10), new THREE.MeshStandardMaterial({ color: 0x26796a }));
  mdl.position.y = 6.4; mdl.rotation.z = 0.15;
  const sign = label(`${district.zone} · enter`, '#9ef5d8', 26); sign.position.y = 7.6;
  g.add(p1, p2, beam, mdl, sign);
  g.rotation.y = -angle;
  const x = Math.cos(angle) * radius, z = Math.sin(angle) * radius;
  g.position.set(x, ground.height(x, z), z);
  g.userData = { who: `${district.zone} Pavilion`, role: 'interactive space', district,
    say: { enter: `Rooms: ${(district.interior_rooms || []).join(' · ')}. Props: ${(district.props || []).join(' · ')}.`,
      buildings: (district.buildings || []).map(b => `${b.name} (${b.floors} fl, ${b.use})`).join(' · '),
      anchor: `Real anchor: ${district.real_anchor}. Agents here: ${(district.npc_agents || []).join(', ')}.`,
      hint: 'Walk the rooms, then press the quest rings to finish the zone.' } };
  g.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return g;
}
const EGG_HINTS = ['near the tallest glass', 'by the water edge', 'under the oldest tree'];

export function makeGame({ S, ground, world, slug, quests = [] }) {
  const g = new THREE.Group(); g.name = 'game-layer';
  const talkers = [];
  const districts = world?.districts || [];

  // ---- district pavilions + their NPC-style agents, on a circle around the plaza
  districts.forEach((d, i) => {
    const a = (i / Math.max(districts.length, 1)) * Math.PI * 2 + 0.4, r = 92;
    const pav = pavilion(d, ground, a, r); g.add(pav); talkers.push(pav);
    (d.npc_agents || []).slice(0, 2).forEach((name, k) => {
      const f = npcFigure(name);
      const x = Math.cos(a) * (r - 8) + (k ? 4 : -4), z = Math.sin(a) * (r - 8) + (k ? 3 : -3);
      f.position.set(x, ground.height(x, z), z);
      const lab = label(name, '#dfffee', 24); lab.position.y = 2.45; f.add(lab);
      const q = quests[i % Math.max(quests.length, 1)] || {};
      f.userData = { who: name, role: `${d.zone} agent`, say: {
        hello: `Welcome to ${d.zone}. Real anchor: ${d.real_anchor}.`,
        about: `I watch over ${(d.interior_rooms || ['the rooms']).slice(0, 3).join(', ')}.`,
        quest: q.title ? `There is a task: ${q.title} (${q.xp || 25} XP).` : 'No open tasks in my zone right now.' },
        wander: { t: Math.random() * 9, x, z } };
      g.add(f); talkers.push(f);
    });
  });

  // ---- easter eggs: three hidden Steward Seals at deterministic spots per world
  let seed = [...slug].reduce((a, c) => (a * 33 + c.charCodeAt(0)) >>> 0, 7);
  const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
  const eggs = [];
  for (let i = 0; i < 3; i++) {
    const e = new THREE.Mesh(new THREE.TetrahedronGeometry(0.55, 0),
      new THREE.MeshStandardMaterial({ color: 0xffd34d, emissive: 0x8a6a12, roughness: 0.25, metalness: 0.7 }));
    const a = rand() * Math.PI * 2, r = 30 + rand() * 90;
    const x = Math.cos(a) * r, z = Math.sin(a) * r;
    e.position.set(x, ground.height(x, z) + 1.1, z);
    e.userData = { egg: i, hint: EGG_HINTS[i], who: 'Steward Seal', role: 'easter egg',
      say: { found: `Seal ${i + 1} of 3. Look for the next one ${EGG_HINTS[(i + 1) % 3]}.` } };
    g.add(e); eggs.push(e); talkers.push(e);
  }

  // ---- missions + badges + level curve, rendered into a small DOM board
  const badges = { conversationalist: false, eggHunter: false, robotWhisperer: false, questRings: false, hoopster: false };
  const missions = (world?.quests || []).map(q => ({ title: q.title, xp: q.xp || 25, done: false }));
  const talked = new Set(), eggsFound = new Set();
  let episodesSeen = 0;

  const host = document.getElementById('c')?.parentElement || document.body;
  const board = document.createElement('div'); board.id = 'wf-game';
  board.style.cssText = 'position:absolute;right:12px;bottom:12px;z-index:5;width:270px;background:rgba(8,14,20,.8);border:1px solid #1f3a44;border-radius:10px;padding:10px;font:12px system-ui;color:#cfe3e8';
  const level = (xp) => Math.floor(Math.sqrt(xp / 40)) + 1;
  function render() {
    const lv = level(state.xp), next = Math.round((lv * lv - 1) * 40 + 40);
    const pct = Math.min(100, Math.round(state.xp / next * 100));
    board.innerHTML = `<div style="display:flex;justify-content:space-between"><b>Level ${lv} · ${state.xp} XP</b><span>${pct}%</span></div>
      <div style="height:6px;background:#12202b;border-radius:4px;margin:4px 0"><div style="height:6px;width:${pct}%;background:linear-gradient(90deg,#0b6e4f,#34d399);border-radius:4px"></div></div>
      <div style="margin:6px 0 2px;color:#7dd8b5">Missions</div>
      ${missions.map(m => `<div style="color:${m.done ? '#7d8d95' : '#cfe3e8'}">${m.done ? '✓' : '○'} ${m.title} <span style="float:right;color:#6b7c85">${m.xp}xp</span></div>`).join('')}
      <div style="margin:6px 0 2px;color:#7dd8b5">Badges</div>
      <div style="display:flex;gap:3px;flex-wrap:wrap">${Object.entries(badges).map(([k, v]) =>
        `<span title="${k}" style="padding:2px 6px;border-radius:8px;background:${v ? '#12362b;color:#7cf7d4' : '#121a22;color:#40525c'}">${k.slice(0, 6)}</span>`).join('')}</div>
      <div style="margin-top:6px;color:#6b7c85">Seals: ${eggsFound.size}/3 · Robot episodes: ${episodesSeen}</div>`;
  }
  onState(s => { // missions complete when their quest XP lands
    (s.log || []).forEach(l => { const m = missions.find(m => l.includes(m.title)); if (m) m.done = true;
      if (/basket/.test(l)) badges.hoopster = true; if (/checkpoint/.test(l) && s.log.length >= 3) badges.questRings = true; });
    render();
  });
  window.__wfGame = { talk: (who) => { if (!badges.conversationalist && !talked.has(who)) { talked.add(who);
      if (talked.size >= 3) { badges.conversationalist = true; award(40, 'badge: conversationalist'); } else award(5, `met ${who}`); } else award(2, `talked with ${who}`); },
    egg: (i) => { if (!eggsFound.has(i)) { eggsFound.add(i); award(25, `Steward Seal ${i + 1}/3`);
      if (eggsFound.size === 3) { badges.eggHunter = true; award(100, 'badge: egg hunter'); } } },
    episodes: (n) => { episodesSeen = n; if (n >= 3 && !badges.robotWhisperer) { badges.robotWhisperer = true; award(40, 'badge: robot whisperer'); } },
    sealCount: () => eggsFound.size };
  render(); host.appendChild(board);

  g.userData.tick = (time) => {
    for (const c of g.children) if (c.userData?.wander) {
      const w = c.userData.wander; w.x += Math.sin(time * 0.35 + w.t) * 0.08; w.z += Math.cos(time * 0.28 + w.t) * 0.08;
      c.position.set(w.x, ground.height(w.x, w.z), w.z); c.rotation.y = Math.atan2(Math.sin(time * 0.35 + w.t), Math.cos(time * 0.28 + w.t));
    }
    eggs.forEach(e => { if (!eggsFound.has(e.userData.egg)) { e.rotation.y = time; e.position.y = ground.height(e.position.x, e.position.z) + 1.1 + Math.sin(time * 2 + e.userData.egg) * 0.25; } else e.scale.setScalar(0.001); });
  };
  return { group: g, talkers, board };
}


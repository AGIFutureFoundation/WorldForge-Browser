// WorldForge Earth gameplay: Master Card zones on real ground, basketball court + shooting game, avatars
// (Omega Steward, Hermes messenger, Hive swarm, Coach, zone agents), quest rings with XP, robot twins.
import * as THREE from 'three';

export const state = { xp: 0, made: 0, shots: 0, log: [] };
const listeners = new Set();
export const onState = (f) => listeners.add(f);
const emit = () => listeners.forEach(f => f(state));
export function award(xp, why) { state.xp += xp; state.log.unshift(`+${xp} XP - ${why}`); state.log.length = Math.min(state.log.length, 8); emit(); }

function label(text, color = '#fff', bg = 'rgba(10,20,30,.72)') {
  const c = document.createElement('canvas'), x = c.getContext('2d');
  x.font = '600 34px system-ui'; const w = Math.min(x.measureText(text).width + 36, 1000);
  c.width = w; c.height = 54; x.font = '600 34px system-ui';
  x.fillStyle = bg; x.beginPath(); x.roundRect(0, 0, w, 54, 14); x.fill(); x.fillStyle = color; x.fillText(text, 18, 38);
  const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: new THREE.CanvasTexture(c), depthTest: false }));
  s.scale.set(w / 18, 3, 1); s.renderOrder = 10; return s;
}

// Master Cards: zone/plaza/gate/council volums from cards.json, set on the real terrain
export function makeCards(cards, ground) {
  const g = new THREE.Group(); g.name = 'master-cards';
  const col = { zone: 0x43c59e, plaza: 0xf1c40f, gate: 0xe67e22, council: 0x9b59b6 };
  const zones = [];
  for (const c of cards) {
    if (!col[c.kind]) continue;
    const [cx, , cz] = c.volum.center, [hx, hy, hz] = c.volum.halfExtents;
    const y = ground.height(cx, cz);
    const box = new THREE.Mesh(new THREE.BoxGeometry(2 * hx, 2 * hy, 2 * hz),
      new THREE.MeshBasicMaterial({ color: col[c.kind], transparent: true, opacity: 0.07, depthWrite: false }));
    box.position.set(cx, y + hy, cz);
    const edges = new THREE.LineSegments(new THREE.EdgesGeometry(box.geometry), new THREE.LineBasicMaterial({ color: col[c.kind] }));
    edges.position.copy(box.position);
    const l = label(c.name || c.kind[0].toUpperCase() + c.kind.slice(1), '#fff'); l.position.set(cx, y + 2 * hy + 4, cz);
    box.userData.card = c; g.add(box, edges, l);
    if (c.kind === 'zone') zones.push({ name: c.name, x: cx, z: cz, card: c });
  }
  g.userData.zones = zones;
  return g;
}

// ---------------------------------------------------------------- avatars
function figure(color, scale = 1, halo = false) {
  const g = new THREE.Group(), m = new THREE.MeshStandardMaterial({ color, roughness: 0.5, metalness: 0.1 });
  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.35, 1.0, 4, 10), m); body.position.y = 0.9;
  const head = new THREE.Mesh(new THREE.SphereGeometry(0.26, 16, 12), m); head.position.y = 1.85;
  g.add(body, head);
  if (halo) { const h = new THREE.Mesh(new THREE.TorusGeometry(0.34, 0.035, 8, 32), new THREE.MeshBasicMaterial({ color: 0xffe38a }));
    h.rotation.x = Math.PI / 2; h.position.y = 2.25; g.add(h); }
  g.scale.setScalar(scale); g.traverse(o => { if (o.isMesh) o.castShadow = true; });
  return g;
}

export function makeAvatars(lines, zones, ground, court) {
  const g = new THREE.Group(); g.name = 'avatars';
  const at = (o, x, z) => { o.position.set(x, ground.height(x, z), z); return o; };
  const L = lines || {};
  const zs = zones || [];
  const cx = court ? court[0] : 40, cz = court ? court[1] : 40;
  const omega = at(figure(0xf5f0e6, 1.25, true), 10, -8); omega.userData = { who: 'Omega Steward', role: 'defined, not seated: advises, never votes', say: L.omega };
  const coach = at(figure(0xff7a1a, 1.05), cx - 18, cz); coach.userData = { who: 'Coach', say: L.coach };
  const hermes = at(figure(0x6ad1ff, 0.95), 0, 12); hermes.userData = { who: 'Hermes', role: 'messenger between zones and worlds', say: L.hermes, route: zs.map(z => [z.x, z.z]) };
  const wing = new THREE.Mesh(new THREE.ConeGeometry(0.12, 0.6, 4), new THREE.MeshBasicMaterial({ color: 0xffffff }));
  wing.rotation.z = Math.PI / 2; wing.position.set(0.3, 1.9, 0); hermes.add(wing, wing.clone().translateX(-0.6));
  g.add(omega, coach, hermes);
  // Hive: a swarm of small drones orbiting the zone it is working in
  const hz = zs[1] || zs[0] || { x: 40, z: 0, name: 'plaza' };
  const hive = new THREE.Group(); hive.userData = { who: 'Hive', zone: hz.name, say: L.hive, center: [hz.x, hz.z] };
  for (let i = 0; i < 24; i++) { const d = new THREE.Mesh(new THREE.OctahedronGeometry(0.35), new THREE.MeshStandardMaterial({ color: 0xffc233, emissive: 0x442200 }));
    d.userData.phase = i * 0.26; d.userData.r = 6 + (i % 4) * 2.5; hive.add(d); }
  g.add(hive);
  for (const [o, t] of [[omega, 'Omega Steward'], [coach, 'Coach'], [hermes, 'Hermes']]) { const l = label(t, '#ffe9a8'); l.position.y = 3.2; l.scale.multiplyScalar(0.6); o.add(l); }
  const hl = label(`Hive @ ${hz.name}`, '#ffd34d'); hl.position.set(hz.x, ground.height(hz.x, hz.z) + 16, hz.z); hl.scale.multiplyScalar(0.6); g.add(hl);
  let leg = 0, t = 0;
  g.userData.tick = (dt, time) => {
    const r = hermes.userData.route;
    if (r && r.length) { const [tx, tz] = leg % 2 ? [0, 0] : r[(leg / 2 | 0) % r.length]; const p = hermes.position;
      const dx = tx - p.x, dz = tz - p.z, d = Math.hypot(dx, dz);
      if (d < 2) leg++; else { p.x += dx / d * dt * 6; p.z += dz / d * dt * 6; p.y = ground.height(p.x, p.z); hermes.rotation.y = Math.atan2(dx, dz); } }
    hive.children.forEach(d => { const a = time * 0.9 + d.userData.phase, [cx, cz] = hive.userData.center;
      d.position.set(cx + Math.cos(a) * d.userData.r, ground.height(cx, cz) + 7 + Math.sin(a * 2.3) * 2, cz + Math.sin(a) * d.userData.r); d.rotation.y = a; });
    omega.rotation.y = Math.sin(time * 0.3) * 0.5;
  };
  g.userData.talkers = [omega, coach, hermes];
  return g;
}


// ---------------------------------------------------------------- basketball court + shooting game (real ballistics)
export function makeCourt(court, ground, name = 'Community Court') {
  const [cx, cz] = court, y = ground.height(cx, cz) + 0.12;
  const g = new THREE.Group(); g.name = 'basketball-court'; g.position.set(cx, y, cz);
  const c = document.createElement('canvas'); c.width = 1024; c.height = 576; const x = c.getContext('2d');
  x.fillStyle = '#2e6f9e'; x.fillRect(0, 0, 1024, 576); x.fillStyle = '#c8763b'; x.fillRect(40, 40, 944, 496);
  x.strokeStyle = '#fff'; x.lineWidth = 6; x.strokeRect(40, 40, 944, 496);
  x.beginPath(); x.moveTo(512, 40); x.lineTo(512, 536); x.stroke(); x.beginPath(); x.arc(512, 288, 60, 0, 7); x.stroke();
  x.strokeRect(40, 208, 190, 160); x.strokeRect(794, 208, 190, 160);
  x.beginPath(); x.arc(40, 288, 230, -1.3, 1.3); x.stroke(); x.beginPath(); x.arc(984, 288, 230, Math.PI - 1.3, Math.PI + 1.3); x.stroke();
  const floor = new THREE.Mesh(new THREE.BoxGeometry(32, 0.2, 18), new THREE.MeshStandardMaterial({ map: new THREE.CanvasTexture(c), roughness: 0.6 }));
  floor.receiveShadow = true; g.add(floor);
  const hoops = [];
  for (const s of [1, -1]) {
    const pole = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.1, 3.4), new THREE.MeshStandardMaterial({ color: 0x333333 }));
    pole.position.set(s * 15.4, 1.7, 0);
    const board = new THREE.Mesh(new THREE.BoxGeometry(0.06, 1.05, 1.8), new THREE.MeshStandardMaterial({ color: 0xffffff, transparent: true, opacity: 0.85 }));
    board.position.set(s * 14.6, 3.45, 0);
    const rim = new THREE.Mesh(new THREE.TorusGeometry(0.23, 0.02, 8, 24), new THREE.MeshStandardMaterial({ color: 0xff4500 }));
    rim.rotation.x = Math.PI / 2; rim.position.set(s * 14.35, 3.05, 0);
    g.add(pole, board, rim); hoops.push(rim);
  }
  const l = label(name, '#ffd8b0'); l.position.set(0, 7, 0); g.add(l);
  g.userData.hoops = hoops;
  return g;
}

export function makeShooter(scene, camera, court) {
  const ball = new THREE.Mesh(new THREE.SphereGeometry(0.12, 20, 14), new THREE.MeshStandardMaterial({ color: 0xd2691e, roughness: 0.7 }));
  ball.castShadow = true; ball.visible = false; scene.add(ball);
  const v = new THREE.Vector3(); let live = false, scored = false, t = 0;
  function shoot(power = 0.62) {
    const cam = camera.position;
    const target = court.userData.hoops.map(h => h.getWorldPosition(new THREE.Vector3())).sort((a, b) => a.distanceTo(cam) - b.distanceTo(cam))[0];
    const from = court.position.clone().add(new THREE.Vector3(Math.sign(target.x - court.position.x) * 8.5, 2.1, (Math.random() - 0.5) * 3));
    ball.position.copy(from); ball.visible = true; live = true; scored = false; t = 0;
    // ideal 52-degree arc; skill error grows with the power slider's distance from 0.62
    const d = new THREE.Vector3(target.x - from.x, 0, target.z - from.z), dist = d.length(), dy = target.y - from.y, ang = THREE.MathUtils.degToRad(52);
    const vIdeal = Math.sqrt(9.81 * dist * dist / (2 * Math.cos(ang) ** 2 * (dist * Math.tan(ang) - dy)));
    const err = 1 + (power - 0.62) * 0.55 + (Math.random() - 0.5) * 0.03;
    d.normalize().multiplyScalar(vIdeal * Math.cos(ang) * err); v.set(d.x, vIdeal * Math.sin(ang) * err, d.z);
    state.shots++; ball.userData.target = target; emit();
  }
  function tick(dt) {
    if (!live) return; t += dt;
    v.y -= 9.81 * dt; ball.position.addScaledVector(v, dt);
    const tg = ball.userData.target;
    if (!scored && v.y < 0 && Math.abs(ball.position.y - tg.y) < 0.15 && Math.hypot(ball.position.x - tg.x, ball.position.z - tg.z) < 0.22) {
      scored = true; state.made++; award(state.made % 5 === 0 ? 50 : 10, state.made % 5 === 0 ? 'five baskets!' : 'basket');
    }
    if (ball.position.y < court.position.y || t > 4) { live = false; ball.visible = false; }
  }
  return { shoot, tick };
}

// ---------------------------------------------------------------- quests: rings at each zone, fly through for XP
export function makeQuestRings(zones, ground, quests = []) {
  const g = new THREE.Group(); g.name = 'quest-rings';
  const zs = zones || [];
  const done = new Set();
  zs.forEach((z, i) => {
    const r = new THREE.Mesh(new THREE.TorusGeometry(3.2, 0.25, 10, 40), new THREE.MeshBasicMaterial({ color: 0x7cf7d4 }));
    r.position.set(z.x, ground.height(z.x, z.z) + 3.6, z.z); r.userData = { zone: z.name, xp: 20 + 10 * (i % 3) };
    g.add(r);
  });
  g.userData.tick = (time, player) => g.children.forEach(r => {
    r.rotation.y = time; r.scale.setScalar(1 + Math.sin(time * 3) * 0.05);
    if (!done.has(r.userData.zone) && player.distanceTo(r.position) < 14) {
      done.add(r.userData.zone); r.material.color.set(0xffd34d); award(r.userData.xp, `checkpoint: ${r.userData.zone}`);
      const q = quests.find(q => q.to_zone === r.userData.zone); if (q) award(Math.min(q.xp || 25, 100), `quest: ${q.title}`);
    }
  });
  return g;
}

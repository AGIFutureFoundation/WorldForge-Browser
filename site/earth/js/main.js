// WorldForge Earth: one world page. ?world=<slug>  [&t=<hour>] [&hd=1] [&tour=1]
import * as THREE from 'three';
import { makeStage, makeGround, drapeImagery, makeBuildings, clock, uniforms } from './core.js';
import { makeVegetation, loadHeroFoliage } from './nature.js';
import { makeWater } from './water.js';
import { makeCards, makeAvatars, makeQuestRings } from './play.js';
import { makeFleet } from './robots.js';
import { wireHud } from './hud.js';

const q = new URLSearchParams(location.search);
const slug = q.get('world') || 'climate-dao';
const $ = (id) => document.getElementById(id);
const status = (t) => { $('status').textContent = t; };
const get = (u) => fetch(u).then(r => { if (!r.ok) throw new Error(`${r.status} ${u}`); return r.json(); });
const opt = (u) => get(u).catch(() => null);
window.__wf = { ready: false, slug };
const DIRS = { N: [0, 1], NE: [-0.7, 0.7], E: [-1, 0], SE: [-0.7, -0.7], S: [0, -1], SW: [0.7, -0.7], W: [1, 0], NW: [0.7, 0.7] };

(async () => {
  status('Loading the real ground...');
  const [geo, cardsDoc, world, trades, robots, programs, lines, course, index] = await Promise.all([
    get(`data/${slug}.geo.json`), opt(`../worldforge/out/${slug}/cards.json`), opt(`team/world/${slug}.json`),
    opt(`team/trades/${slug}.json`), opt(`team/robots/${slug}.json`), opt(`team/programs/${slug}.json`),
    opt('team/dialogue.json'), opt('team/courses.json'), opt('worlds.json')]);
  const meta = (index?.worlds || []).find(w => w.slug === slug) || { name: slug };
  document.title = `${meta.name} - ${geo?.place || slug} | WorldForge Earth`;
  $('title').textContent = meta.name; $('place').textContent = `${geo?.place || 'Real Earth location'} · ${geo?.lat?.toFixed(4) || '0'}, ${geo?.lon?.toFixed(4) || '0'}`;

  const S = makeStage($('c'));
  const ground = makeGround(geo); S.scene.add(ground.mesh, ground.skirt);
  S.setSun(+(q.get('t') || 10.5));
  const wind = DIRS[world?.wind?.prevailing_from] || [0.8, 0.4], ws = Math.min(world?.wind?.mean_mps ?? 4, 12) / 4;
  uniforms.uWind.value.set(wind[0] * ws, wind[1] * ws);

  status('Streaming satellite imagery...');
  const img = await drapeImagery(geo, ground, p => status(`Streaming satellite imagery... ${(p * 100) | 0}%`));
  const b = makeBuildings(geo, ground); if (b) S.scene.add(b);
  const veg = makeVegetation(geo, ground, world?.biome || meta?.biome || 'urban-park'); S.scene.add(veg);
  const water = makeWater(geo, ground, S.sun.position.clone().normalize(), world?.water?.flow_mps ?? 0.4); S.scene.add(water);
  const cards = makeCards(cardsDoc?.cards || [], ground); S.scene.add(cards);
  const zones = cards.userData.zones || [];
  const avatars = makeAvatars(lines?.[slug], zones, ground); S.scene.add(avatars);
  const rings = makeQuestRings(zones, ground, world?.quests || []); S.scene.add(rings);
  const fleet = makeFleet(robots?.tasks || [], zones, ground, { slug, place: geo?.place || slug }); S.scene.add(fleet);
  if (q.get('hd') === '1') loadHeroFoliage(S.scene, ground);

  const counts = { ...veg.userData.counts, buildings: geo?.features?.building?.length || 0, ...water.userData.counts,
    robots: fleet.userData.episodes.length, zones: zones.length, imageryZoom: img?.zoom || 0 };
  let flyT = null;
  const fly = (p, dist = 40) => { flyT = { from: S.camera.position.clone(), to: p.clone().add(new THREE.Vector3(dist, dist * 0.6, dist)), look: p.clone(), t: 0 }; };
  wireHud({ slug, geo, img, world, trades, programs, course: course?.[slug], counts, S, avatars, fleet, fly });

  const tour = q.get('tour') === '1';
  const stops = zones.length ? [new THREE.Vector3(0, 0, 0), ...zones.map(z => new THREE.Vector3(z.x, ground.height(z.x, z.z), z.z))] : [new THREE.Vector3(0, 0, 0)];
  let tourI = 0, tourClock = 0;
  if (tour) fly(stops[0], 140);
  S.renderer.setAnimationLoop(() => {
    const raw = clock.getDelta(), dt = Math.min(raw, 0.05), time = clock.elapsedTime; uniforms.uTime.value = time;
    // robots run on real time (capped, sub-stepped) so slow GPUs still produce training episodes at the same rate
    for (let left = Math.min(raw, 0.5); left > 1e-4; left -= 0.05) fleet.userData.tick(Math.min(left, 0.05));
    avatars.userData.tick(dt, time); rings.userData.tick(time, S.camera.position);
    if (flyT) { flyT.t = Math.min(flyT.t + dt / 2.5, 1); const e = flyT.t * flyT.t * (3 - 2 * flyT.t);
      S.camera.position.lerpVectors(flyT.from, flyT.to, e); S.controls.target.lerp(flyT.look, e * 0.25 + 0.05); if (flyT.t >= 1) flyT = null; }
    if (tour && !flyT && (tourClock += dt) > 2.5) { tourClock = 0; tourI = (tourI + 1) % stops.length; fly(stops[tourI], tourI === 0 ? 140 : 34); }
    S.controls.update(); S.renderer.render(S.scene, S.camera);
  });
  $('status').hidden = true;
  window.__wf = { ready: true, slug, counts, records: () => fleet.userData.records.length, fly, stops,
    debug: () => fleet.userData.episodes.map(e => ({ id: e.task.id, cls: e.t.cls, state: e.state, t0: +e.t0.toFixed(1), dist: +e.dist.toFixed(1),
      at: [+e.o.position.x.toFixed(1), +e.o.position.z.toFixed(1)], goal: [+e.goal.x.toFixed(1), +e.goal.y.toFixed(1)] })) };
})().catch(e => { status('Could not load this world: ' + e.message); window.__wf = { ready: false, error: String(e) }; });

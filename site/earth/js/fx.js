// WorldForge Earth FX: living sky + weather. Weather systems (clear / cloudy / rain / snow /
// fog) with a drifting cloud layer, particle rain + snow, fog-bank control and wind gusts that
// modulate the SAME shared wind field the foliage sways to. All GPU-cheap: sprites + one Points.
import * as THREE from 'three';
import { uniforms } from './core.js';

export const WEATHERS = {
  clear:  { clouds: 0, rain: 0, snow: 0, fog: [1200, 4200], gust: 1.0 },
  cloudy: { clouds: 1, rain: 0, snow: 0, fog: [900, 3600], gust: 1.3 },
  rain:   { clouds: 0.6, rain: 1, snow: 0, fog: [420, 2600], gust: 1.6 },
  snow:   { clouds: 0.35, snow: 1, fog: [380, 2200], gust: 0.7 },
  fog:    { clouds: 0, rain: 0, snow: 0, fog: [90, 900], gust: 0.4 },
};

function cloudTex() {
  const c = document.createElement('canvas'); c.width = c.height = 128;
  const x = c.getContext('2d'), g = x.createRadialGradient(64, 64, 8, 64, 64, 62);
  g.addColorStop(0, 'rgba(255,255,255,.95)'); g.addColorStop(0.55, 'rgba(255,255,255,.55)');
  g.addColorStop(1, 'rgba(255,255,255,0)'); x.fillStyle = g; x.fillRect(0, 0, 128, 128);
  return new THREE.CanvasTexture(c);
}
function flakeTex(rain) {
  const c = document.createElement('canvas'); c.width = 16; c.height = 32;
  const x = c.getContext('2d');
  if (rain) { const g = x.createLinearGradient(0, 0, 0, 32);
    g.addColorStop(0, 'rgba(160,200,255,0)'); g.addColorStop(.5, 'rgba(160,200,255,.9)'); g.addColorStop(1, 'rgba(160,200,255,0)');
    x.fillStyle = g; x.fillRect(6, 0, 1.5, 32); }
  else { const g = x.createRadialGradient(8, 16, 1, 8, 16, 7);
    g.addColorStop(0, 'rgba(255,255,255,1)'); g.addColorStop(1, 'rgba(255,255,255,0)');
    x.fillStyle = g; x.fillRect(0, 0, 16, 32); }
  return new THREE.CanvasTexture(c);
}
const hm = (s, d) => { const [h, m] = String(s || '').split(':').map(Number); return (isNaN(h) ? d : h + (m || 0) / 60); };

export function makeSkyFX({ S, world, baseWind = [0.8, 0.3], initial = 'clear' }) {
  uniforms.uWeather = uniforms.uWeather || { value: 'clear' };
  const g = new THREE.Group(); g.name = 'sky-fx';

  // cloud layer: 14 sprites drifting on the wind, wrapping around the world
  const ct = cloudTex(), clouds = [];
  for (let i = 0; i < 14; i++) {
    const s = new THREE.Sprite(new THREE.SpriteMaterial({ map: ct, transparent: true, opacity: 0, depthWrite: false }));
    s.scale.set(320 + Math.random() * 420, 90 + Math.random() * 110, 1);
    s.position.set((Math.random() - 0.5) * 1100, 240 + Math.random() * 130, (Math.random() - 0.5) * 1100);
    s.renderOrder = -2; clouds.push(s); g.add(s);
  }

  // precipitation: one THREE.Points cloud, reused for rain and snow
  const N = 1600, pos = new Float32Array(N * 3), vel = new Float32Array(N);
  for (let i = 0; i < N; i++) { pos[i * 3] = (Math.random() - 0.5) * 500; pos[i * 3 + 1] = Math.random() * 160; pos[i * 3 + 2] = (Math.random() - 0.5) * 500; vel[i] = 0.6 + Math.random() * 0.8; }
  const pgeo = new THREE.BufferGeometry(); pgeo.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  const precip = new THREE.Points(pgeo, new THREE.PointsMaterial({
    map: flakeTex(true), size: 1.6, transparent: true, opacity: 0.5, depthWrite: false, sizeAttenuation: true }));
  precip.visible = false; g.add(precip);

  let mode = 'clear', snowMode = false, cover = WEATHERS.clear.clouds;

  function setWeather(name) {
    const w = WEATHERS[name] || WEATHERS.clear; mode = name; uniforms.uWeather.value = name;
    snowMode = !!w.snow; cover = w.clouds;
    precip.material.map = flakeTex(!snowMode); precip.material.needsUpdate = true;
    precip.visible = !!(w.rain || w.snow);
    precip.material.size = snowMode ? 0.9 : 1.6;
    S.scene.fog.near = w.fog[0]; S.scene.fog.far = w.fog[1];
    S.scene.fog.color.set(snowMode || name === 'fog' ? 0xd8e2ea : 0xb4d0ea);
    S.scene.background.copy(S.scene.fog.color);
    return mode;
  }
  const bw = new THREE.Vector2(baseWind[0], baseWind[1]);
  function tick(dt, time) {
    // wind gusts: slow noise around the world's prevailing wind, scaled by the weather
    const gustiness = WEATHERS[mode].gust;
    const gust = (Math.sin(time * 0.31) * 0.5 + Math.sin(time * 0.83 + 1.7) * 0.3 + 1) * 0.6 * gustiness;
    uniforms.uWind.value.set(bw.x * gust, bw.y * gust);
    // clouds: drift + wrap, fade to the weather's cloud cover
    for (const c of clouds) {
      c.position.x += uniforms.uWind.value.x * dt * 6; c.position.z += uniforms.uWind.value.y * dt * 6;
      if (c.position.x > 650) c.position.x = -650; if (c.position.z > 650) c.position.z = -650;
      c.material.opacity += (cover * 0.55 - c.material.opacity) * dt * 0.7;
    }
    // precipitation falls in a window around the origin; the wind pushes it sideways
    if (precip.visible) {
      const p = pgeo.attributes.position, fall = (snowMode ? 9 : 46) * dt, drift = snowMode ? 3 : 10;
      for (let i = 0; i < N; i++) {
        let y = p.getY(i) - fall * vel[i];
        p.setX(i, p.getX(i) + uniforms.uWind.value.x * dt * drift + (snowMode ? Math.sin(time * 2 + i) * dt * 2 : 0));
        p.setZ(i, p.getZ(i) + uniforms.uWind.value.y * dt * drift);
        if (y < 0) { y = 140 + Math.random() * 30;
          p.setX(i, (Math.random() - 0.5) * 500); p.setZ(i, (Math.random() - 0.5) * 500); }
        p.setY(i, y);
      }
      p.needsUpdate = true;
    }
  }
  setWeather(initial);
  return { group: g, tick, setWeather, get weather() { return mode; },
    hours: { sunrise: hm(world?.day_cycle?.sunrise_local, 6.4), sunset: hm(world?.day_cycle?.sunset_local, 19.5) } };
}

// small DOM panel for weather control, injected beside the canvas
export function weatherPanel(fx) {
  const host = document.getElementById('c')?.parentElement || document.body;
  const d = document.createElement('div');
  d.id = 'wf-weather';
  d.style.cssText = 'position:absolute;left:12px;bottom:12px;z-index:5;display:flex;gap:4px;flex-wrap:wrap;background:rgba(8,14,20,.72);padding:6px;border-radius:8px;font:12px system-ui';
  d.innerHTML = Object.keys(WEATHERS).map(n => `<button data-w="${n}" style="border:1px solid #2c3e50;background:#0f1a24;color:#94a3b8;border-radius:5px;padding:3px 8px;cursor:pointer">${n}</button>`).join('');
  d.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return;
    fx.setWeather(b.dataset.w);
    d.querySelectorAll('button').forEach(x => x.style.color = x.dataset.w === fx.weather ? '#34d399' : '#94a3b8'); });
  host.appendChild(d);
  return d;
}


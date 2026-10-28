// Robot digital twins on the real terrain, modeled to each manufacturer's published specs
// (dimensions, mass, payload, DOF, drive class, brand colors). Each runs a ROS 2-style task
// from earth/team (eval-checked): publishes simulated /odom, /cmd_vel and /joint_states,
// plans over the real elevation, honours safety stops, and writes one RICH JSONL training
// record per episode (schema worldforge-earth/robot-episode/2: manufacturer block, sampled
// route, battery/thermal model, event log, live wind context). Visuals are scaffold-accurate
// (simple geoms at true proportions); kinematics remain honest training-data scaffolds.
import * as THREE from 'three';
import { uniforms } from './core.js';

export const TWINS = {
  'boston-dynamics-spot': { brand: 'Boston Dynamics', model: 'Spot', cls: 'quadruped', speed: 1.6,
    color: 0xf2c200, accent: 0x1c1c1c, size: [1.1, 0.6, 0.5], mass_kg: 32, payload_kg: 14, battery_min: 90,
    dof: 12, sensors: ['5 stereo cameras', 'LiDAR option', 'IMU', 'joint encoders'], facts: '1.6 m/s, 90 min' },
  'unitree-go2': { brand: 'Unitree', model: 'Go2', cls: 'quadruped', speed: 2.5,
    color: 0x9aa4ad, accent: 0x22262b, size: [0.7, 0.4, 0.31], mass_kg: 15, payload_kg: 8, battery_min: 120,
    dof: 12, sensors: ['Intel RealSense D435 (EDU)', 'IMU', 'foot force sensors'], facts: '3-4 m/s sprint class' },
  'pal-robotics-talos': { brand: 'PAL Robotics', model: 'TALOS', cls: 'humanoid', speed: 0.5,
    color: 0x2f4f6f, accent: 0xe8e8e8, size: [0.5, 1.75, 0.35], mass_kg: 95, payload_kg: 4, battery_min: 120,
    dof: 32, sensors: ['head RGB-D', 'forearm cameras', 'FT sensors', '2 LiDAR'], facts: '1.75 m biped' },
  'softbank-nao': { brand: 'SoftBank Robotics', model: 'NAO V6', cls: 'humanoid', speed: 0.3,
    color: 0xeeeeee, accent: 0x1a4fd6, size: [0.3, 0.58, 0.2], mass_kg: 5.4, payload_kg: 0.5, battery_min: 90,
    dof: 25, sensors: ['2 HD cams', '4 mics', 'IR', 'sonars'], facts: '0.58 m biped' },
  'universal-robots-ur10e': { brand: 'Universal Robots', model: 'UR10e', cls: 'arm', speed: 0,
    color: 0x5b8fb9, accent: 0x2c2c2c, size: [0.3, 1.3, 0.3], mass_kg: 33.5, payload_kg: 5, battery_min: 0,
    dof: 6, sensors: ['joint encoders', 'tool force-torque', 'safety-rated stops'], facts: '1300 mm reach' },
  'franka-fr3': { brand: 'Franka Robotics', model: 'FR3', cls: 'arm', speed: 0,
    color: 0xf4f4f4, accent: 0x1867d6, size: [0.25, 0.85, 0.25], mass_kg: 18, payload_kg: 3, battery_min: 0,
    dof: 7, sensors: ['joint torque sensors x7', 'camera flange'], facts: '855 mm reach' },
  'kinova-gen3': { brand: 'Kinova', model: 'Gen3', cls: 'arm', speed: 0,
    color: 0x222222, accent: 0xdedede, size: [0.2, 0.9, 0.2], mass_kg: 12, payload_kg: 4, battery_min: 0,
    dof: 7, sensors: ['2D/3D vision', 'force-torque'], facts: '902 mm reach' },
  'fetch-robotics-fetch': { brand: 'Fetch Robotics (Zebra)', model: 'Fetch', cls: 'mobile-manipulator', speed: 1.0,
    color: 0xdddddd, accent: 0x333333, size: [0.56, 1.1, 0.56], mass_kg: 80, payload_kg: 25, battery_min: 480,
    dof: 18, sensors: ['SICK laser', 'tilting LiDAR', 'cameras'], facts: '9 h runtime' },
  'clearpath-husky-a200': { brand: 'Clearpath Robotics', model: 'Husky A200', cls: 'ugv', speed: 1.0,
    color: 0xffc000, accent: 0x1c1c1c, size: [0.99, 0.39, 0.67], mass_kg: 46, payload_kg: 75, battery_min: 180,
    dof: 4, sensors: ['GPS/IMU', 'front+rear cameras', 'LiDAR option'], facts: 'skid-steer, 1.0 m/s' },
  'bitcraze-crazyflie-2-1-plus': { brand: 'Bitcraze', model: 'Crazyflie 2.1+', cls: 'drone', speed: 1.5,
    color: 0x3a3a3a, accent: 0xd64541, size: [0.1, 0.03, 0.1], mass_kg: 0.027, payload_kg: 0.01, battery_min: 7,
    dof: 4, sensors: ['ToF deck', 'flow deck v2', 'IMU'], facts: '92 mm, 27 g' },
};

const mat = (c, m = {}) => new THREE.MeshStandardMaterial({ color: c, roughness: m.rough ?? 0.45, metalness: m.metal ?? 0.35 });
const eye = (c = 0x88ccff) => new THREE.MeshBasicMaterial({ color: c });


function quadruped(id) {
  const t = TWINS[id], [w, h, d] = t.size, g = new THREE.Group();
  const trunk = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.55, d), mat(t.color));
  trunk.position.y = h * 0.72; g.add(trunk);
  const stripe = new THREE.Mesh(new THREE.BoxGeometry(w * 1.01, h * 0.12, d * 1.01), mat(t.accent, { rough: 0.3 }));
  stripe.position.y = h * 0.78; g.add(stripe);
  const head = new THREE.Mesh(new THREE.BoxGeometry(w * 0.5, h * 0.42, d * 0.6), mat(t.accent));
  head.position.set(0, h * 0.72, d * 0.68); g.add(head);
  for (const s of [-1, 1]) { const c = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, 0.04, 10), eye());
    c.rotation.x = Math.PI / 2; c.position.set(s * w * 0.1, h * 0.72, d * 0.68 + 0.05); g.add(c); }
  if (id.startsWith('boston')) { const ant = new THREE.Mesh(new THREE.CylinderGeometry(0.008, 0.008, h * 0.7, 6), mat(0x111111));
    ant.position.set(0, h * 1.2, -d * 0.2); ant.rotation.x = -0.5; g.add(ant); }
  g.userData.legs = [];
  for (const [a, c] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const hip = new THREE.Mesh(new THREE.BoxGeometry(0.07, h * 0.32, 0.07), mat(t.accent, { rough: 0.3 }));
    hip.position.set(a * w * 0.52, h * 0.66, c * d * 0.42);
    const knee = new THREE.Group(); knee.position.y = -h * 0.32;
    const shank = new THREE.Mesh(new THREE.BoxGeometry(0.06, h * 0.42, 0.06), mat(t.accent, { rough: 0.3 }));
    shank.position.y = -h * 0.2; knee.add(shank);
    hip.add(knee); g.add(hip); g.userData.legs.push({ hip, knee });
  }
  return g;
}

function humanoid(id) {
  const t = TWINS[id], [w, h, d] = t.size, g = new THREE.Group();
  const torso = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.42, d * 0.55), mat(t.color));
  torso.position.y = h * 0.62; g.add(torso);
  const pelvis = new THREE.Mesh(new THREE.BoxGeometry(w * 0.85, h * 0.12, d * 0.5), mat(t.accent));
  pelvis.position.y = h * 0.38; g.add(pelvis);
  const hd = new THREE.Mesh(new THREE.SphereGeometry(w * 0.32, 14, 10), mat(t.accent, { rough: 0.25 }));
  hd.position.y = h * 0.9; g.add(hd);
  g.userData.eyes = [];
  for (const s of [-1, 1]) { const led = new THREE.Mesh(new THREE.SphereGeometry(w * 0.05, 8, 6),
      eye(id.startsWith('pal') ? 0xafe9ff : 0x2a6cff));
    led.position.set(s * w * 0.12, h * 0.92, w * 0.28); g.add(led); g.userData.eyes.push(led); }
  g.userData.legs = []; g.userData.arms = [];
  for (const s of [-1, 1]) {
    const shoulder = new THREE.Group(); shoulder.position.set(s * w * 0.62, h * 0.78, 0);
    const arm = new THREE.Mesh(new THREE.BoxGeometry(w * 0.18, h * 0.3, w * 0.18), mat(t.color));
    arm.position.y = -h * 0.15; shoulder.add(arm); g.add(shoulder); g.userData.arms.push(shoulder);
    const hip = new THREE.Mesh(new THREE.BoxGeometry(w * 0.22, h * 0.38, d * 0.2), mat(t.color));
    hip.position.set(s * w * 0.28, h * 0.19, 0);
    const foot = new THREE.Mesh(new THREE.BoxGeometry(w * 0.24, h * 0.04, d * 0.45), mat(t.accent));
    foot.position.set(0, -h * 0.2, d * 0.08); hip.add(foot); g.add(hip); g.userData.legs.push({ hip, knee: foot });
  }
  return g;
}

// --- industrial arm (UR10e / FR3 / Gen3): base, 2-link shoulder+elbow chain, wrist camera, gripper ---
function arm(id) {
  const t = TWINS[id], [w, h, _d] = t.size, g = new THREE.Group();
  const base = new THREE.Mesh(new THREE.CylinderGeometry(w * 0.75, w * 0.85, 0.22, 20), mat(t.accent, { metal: 0.5 }));
  base.position.y = 0.11; g.add(base);
  const shoulder = new THREE.Group(); shoulder.position.y = 0.2; g.add(shoulder);
  const l1 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.42, h * 0.5, w * 0.42), mat(t.color, { metal: 0.2 }));
  l1.position.y = h * 0.25; shoulder.add(l1);
  const elbow = new THREE.Group(); elbow.position.y = h * 0.5 + 0.1;
  const l2 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.36, h * 0.42, w * 0.36), mat(t.color, { metal: 0.2 }));
  l2.position.y = h * 0.2; elbow.add(l2);
  const wrist = new THREE.Group(); wrist.position.y = h * 0.45;
  const cam = new THREE.Mesh(new THREE.BoxGeometry(w * 0.2, w * 0.2, w * 0.2), mat(0x0e0e10));
  const gripL = new THREE.Mesh(new THREE.BoxGeometry(w * 0.1, h * 0.1, w * 0.08), mat(t.accent, { rough: 0.2 }));
  gripL.position.set(-w * 0.12, h * 0.08, 0);
  const gripR = gripL.clone(); gripR.position.x = w * 0.12;
  wrist.add(cam, gripL, gripR); elbow.add(wrist);
  shoulder.add(elbow); g.userData.joint = elbow; g.userData.wrist = wrist;
  return g;
}

// --- wheeled robots (Husky A200 UGV / Fetch mobile manipulator) with roll cage or lift column ---
function wheeled(id) {
  const t = TWINS[id], [w, h, d] = t.size, g = new THREE.Group();
  const chassis = new THREE.Mesh(new THREE.BoxGeometry(w, h * 0.78, d), mat(t.color, { metal: 0.2 }));
  chassis.position.y = 0.28; g.add(chassis);
  g.userData.wheels = [];
  for (const [a, c] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.17, 0.17, 0.12, 14), mat(0x151515, { rough: 0.7, metal: 0.1 }));
    wh.rotation.z = Math.PI / 2; wh.position.set(a * w * 0.55, 0.17, c * d * 0.85); g.add(wh); g.userData.wheels.push(wh);
  }
  if (t.cls === 'ugv') {                                  // Husky: sensor mast + roll bar
    const mast = new THREE.Mesh(new THREE.CylinderGeometry(0.025, 0.025, h * 1.5, 8), mat(0x333333));
    mast.position.set(0, h * 0.85, -d * 0.25); g.add(mast);
    const scan = new THREE.Mesh(new THREE.CylinderGeometry(0.035, 0.035, 0.09, 10), eye(0x55ff99));
    scan.position.set(0, h * 1.6, -d * 0.25); g.userData.scan = scan; g.add(scan);
    for (const s of [-1, 1]) { const bar = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, h * 1.15, 8), mat(t.accent));
      bar.position.set(s * w * 0.42, h * 0.95, -d * 0.1); bar.rotation.z = s * 0.28; g.add(bar); }
  } else {                                                // Fetch: lift column + pan-tilt head
    const col = new THREE.Mesh(new THREE.BoxGeometry(w * 0.45, h * 0.95, w * 0.35), mat(t.accent, { metal: 0.3 }));
    col.position.set(0, h * 0.55, -d * 0.05); g.add(col);
    const head = new THREE.Mesh(new THREE.BoxGeometry(w * 0.4, w * 0.32, w * 0.42), mat(0x0e0e10));
    head.position.set(0, h * 1.12, -d * 0.05); g.add(head);
    const lens = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.06, 12), eye(0x66ddff)) ;
    lens.rotation.x = Math.PI / 2; lens.position.set(0, h * 1.12, -d * 0.05 + w * 0.24); g.add(lens);
  }
  return g;
}

// --- drone (Crazyflie): frame, prop guards, 4 spinning props, LED ----------------------------------------
function drone(id) {
  const t = TWINS[id], [w, h, d] = t.size, g = new THREE.Group();
  const core = new THREE.Mesh(new THREE.BoxGeometry(w * 0.5, h * 2.2, d * 0.5), mat(t.color, { rough: 0.3, metal: 0.5 }));
  const deck = new THREE.Mesh(new THREE.BoxGeometry(w * 0.54, h * 0.5, d * 0.54), mat(t.accent, { metal: 0.2 }));
  deck.position.y = h * 1.35; g.add(core, deck);
  g.userData.props = [];
  for (const [a, b] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
    const armM = new THREE.Mesh(new THREE.BoxGeometry(w * 0.45, h * 0.5, w * 0.08), mat(t.accent));
    armM.position.set(a * w * 0.45, 0, b * d * 0.45); armM.rotation.y = Math.atan2(b, a); g.add(armM);
    const guard = new THREE.Mesh(new THREE.TorusGeometry(w * 0.28, 0.012, 6, 18), mat(0xd8d8d8, { metal: 0.6 }));
    guard.rotation.x = Math.PI / 2; guard.position.set(a * w * 0.62, h * 0.4, b * d * 0.62); g.add(guard);
    const rotor = new THREE.Group(); rotor.position.set(a * w * 0.62, h * 0.5, b * d * 0.62);
    for (let k = 0; k < 2; k++) { const bl = new THREE.Mesh(new THREE.BoxGeometry(w * 0.5, 0.006, w * 0.05), mat(0x222222, { rough: 0.9 }));
      bl.rotation.y = k * Math.PI / 2; rotor.add(bl); }
    g.add(rotor); g.userData.props.push(rotor);
  }
  const led = new THREE.Mesh(new THREE.SphereGeometry(0.02, 8, 6), eye(0xff4040));
  led.position.set(0, 0, d * 0.3); g.add(led);
  return g;
}

function body(id) {
  const t = TWINS[id];
  let g;
  if (t.cls === 'quadruped') g = quadruped(id);
  else if (t.cls === 'humanoid') g = humanoid(id);
  else if (t.cls === 'arm') g = arm(id);
  else if (t.cls === 'drone') g = drone(id);
  else g = wheeled(id);
  g.scale.setScalar(t.cls === 'drone' ? 8 : 1.6);        // drones drawn larger to stay visible
  g.traverse(o => { if (o.isMesh) o.castShadow = true; });
  g.userData.spec = t; g.userData.robotId = id;
  return g;
}
// One twin running one task: navigate (mobile) or a pick cycle (arm) toward the task's zone, on real slope.
export function makeFleet(tasks, zones, ground, world) {
  const g = new THREE.Group(); g.name = 'robot-twins';
  const episodes = [], records = [];
  const zoneAt = n => zones.find(z => z.name === n) || zones[0] || { x: 30, z: 30, name: 'plaza' };
  (tasks || []).forEach((task, i) => {
    if (!TWINS[task.robot]) return;
    const t = TWINS[task.robot], o = body(task.robot), goal = zoneAt(task.zone);
    const a = i * 1.1, start = new THREE.Vector2(Math.cos(a) * 26, Math.sin(a) * 26);
    const at = (t.cls === 'arm' || t.cls === 'drone') ? new THREE.Vector2(goal.x + Math.cos(a) * 8, goal.z + Math.sin(a) * 8) : start;
    o.position.set(at.x, ground.height(at.x, at.y) + 0.02, at.y); g.add(o);
    episodes.push({ task, t, o, goal: new THREE.Vector2(goal.x + Math.cos(a) * 6, goal.z + Math.sin(a) * 6),
      start: at.clone(), t0: 0, dist: 0, maxSlope: 0, stops: 0, state: 'running', route: [], events: [],
      sampleT: 0, ros: { cmd_vel: [0, 0], odom: [at.x, at.y, 0] } });
  });
  function record(e, outcome) {
    const t = e.t;
    const battery = t.battery_min ? Math.max(2, Math.round(100 - e.t0 / 60 / t.battery_min * 100)) : 100;
    const r = { schema: 'worldforge-earth/robot-episode/2', world: world.slug, place: world.place,
      robot: e.task.robot, manufacturer: { brand: t.brand, model: t.model, class: t.cls, dims_m: t.size,
        mass_kg: t.mass_kg, payload_kg: t.payload_kg, dof: t.dof, sensors: t.sensors, facts: t.facts },
      task_id: e.task.id, zone: e.task.zone, ros_action: e.task.ros?.action, topics: e.task.ros?.topics,
      outcome, duration_s: +e.t0.toFixed(2), path_m: +e.dist.toFixed(2), max_slope_deg: +e.maxSlope.toFixed(1),
      safety_stops: e.stops, events: e.events.slice(0, 24), route: e.route.slice(0, 90),
      success_checks: e.task.success, human_in_loop: e.task.human_in_loop,
      feedback_fields: e.task.feedback_schema?.fields,
      battery_pct: battery, core_temp_c: +(35 + Math.sin(e.t0 / 20) * 3 + (e.stops * 0.4)).toFixed(1),
      wind_mps: +Math.hypot(uniforms.uWind.value.x, uniforms.uWind.value.y).toFixed(2),
      weather: uniforms.uWeather?.value ?? 'clear',
      sim: 'kinematic scaffold (visuals spec-accurate, not vendor physics)', ts: new Date().toISOString() };
    records.push(r); return r;
  }
  const sample = (e) => { e.route.push([+e.t0.toFixed(1), +e.o.position.x.toFixed(1), +e.o.position.z.toFixed(1),
    +e.o.rotation.y.toFixed(2), +Math.max(0, ground.height(e.o.position.x, e.o.position.z)).toFixed(1)]); };
  g.userData.tick = (dt) => {
    for (const e of episodes) {
      if (e.state !== 'running') continue;
      e.t0 += dt; e.sampleT += dt;
      if (e.sampleT > 2) { sample(e); e.sampleT = 0; }
      const t = e.t;
      // ---- idle-time animation of every actuated part (also runs while moving)
      const P = e.o.userData.props || []; P.forEach((p, k) => p.rotation.y += dt * (40 + k));
      (e.o.userData.wheels || []).forEach(w => w.rotation.x += dt * t.speed * 8);
      if (e.o.userData.scan) e.o.userData.scan.rotation.y += dt * 6;
      if (t.cls === 'arm') {
        const j = e.o.userData.joint, w = e.o.userData.wrist;
        if (j) j.rotation.z = Math.sin(e.t0 * 1.4) * 0.9;
        if (w) w.rotation.x = Math.cos(e.t0 * 1.1) * 0.6;
        e.o.rotation.y += dt * 0.6;
        if (e.t0 > 6) { record(e, 'success'); e.t0 = 0; }
        continue;
      }
      const p = new THREE.Vector2(e.o.position.x, e.o.position.z), to = e.goal.clone().sub(p), d = to.length();
      if (d < 1.5) {                      // episode done: record it, then run the next episode back to the start
        record(e, 'success'); e.t0 = 0; e.dist = 0; e.maxSlope = 0; e.stops = 0; e.route = []; e.events = [];
        const back = e.home || (e.home = new THREE.Vector2(e.o.position.x, e.o.position.z));
        [e.goal, e.home] = [e.start || back, e.goal]; e.start = e.home; continue;
      }
      to.normalize();
      const ahead = p.clone().addScaledVector(to, 2), rise = ground.height(ahead.x, ahead.y) - ground.height(p.x, p.y);
      const slope = Math.atan2(Math.abs(rise), 2) * 57.3; e.maxSlope = Math.max(e.maxSlope, slope);
      const limit = t.cls === 'drone' ? 90 : t.cls === 'quadruped' ? 30 : t.cls === 'humanoid' ? 12 : 20;
      if (slope > limit) { e.stops++; e.events.push({ t: +e.t0.toFixed(1), type: 'slope_stop', slope_deg: +slope.toFixed(1) });
        to.rotateAround(new THREE.Vector2(), 0.9); }
      const step = Math.min(Math.max(t.speed, 0.6) * 12 * dt, d);   // 12x sim speed-up (training throughput)
      e.o.position.x += to.x * step; e.o.position.z += to.y * step; e.dist += step;
      e.o.position.y = ground.height(e.o.position.x, e.o.position.z) + (t.cls === 'drone' ? 8 + Math.sin(e.t0 * 2) : 0);
      e.o.rotation.y = Math.atan2(to.x, to.y);
      (e.o.userData.legs || []).forEach((l, k) => { const s = Math.sin(e.t0 * 10 + k * Math.PI);
        if (l.hip) { l.hip.rotation.x = s * 0.5; l.knee.rotation.z = Math.sin(e.t0 * 10 + k * Math.PI + 0.6) * 0.4; }
        else l.rotation.x = s * 0.5; });
      (e.o.userData.arms || []).forEach((s2, k) => s2.rotation.x = Math.sin(e.t0 * 6 + k * Math.PI) * 0.3);
      (e.o.userData.eyes || []).forEach(ed => ed.material.color.setHSL(0.58, 0.9, 0.55 + 0.2 * Math.sin(e.t0 * 3)));
      e.ros.cmd_vel = [t.speed, 0]; e.ros.odom = [+e.o.position.x.toFixed(1), +e.o.position.z.toFixed(1), +e.o.rotation.y.toFixed(2)];
      if (e.t0 > 120) { record(e, 'timeout'); e.state = 'done'; }
    }
  };
  g.userData.episodes = episodes; g.userData.records = records;
  g.userData.jsonl = () => records.map(r => JSON.stringify(r)).join('\n') + '\n';
  return g;
}


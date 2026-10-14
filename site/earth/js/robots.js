// Robot digital twins on the real terrain. Each runs a ROS 2-style task from earth/team (GLM-authored, eval-checked):
// it publishes simulated /odom, /cmd_vel and /joint_states, plans over the real elevation, honours safety stops,
// and writes one JSONL training record per episode (fields from the task's feedback_schema, plus standard ones).
// Kinematics are simple and honest: these are training-data scaffolds, not vendor-accurate physics.
import * as THREE from 'three';

export const TWINS = {
  'boston-dynamics-spot': { cls: 'quadruped', speed: 1.6, color: 0xf2c200, size: [1.1, 0.6, 0.5] },
  'unitree-go2': { cls: 'quadruped', speed: 2.5, color: 0x9aa4ad, size: [0.7, 0.4, 0.31] },
  'pal-robotics-talos': { cls: 'humanoid', speed: 0.5, color: 0x2f4f6f, size: [0.5, 1.75, 0.35] },
  'softbank-nao': { cls: 'humanoid', speed: 0.3, color: 0xeeeeee, size: [0.3, 0.58, 0.2] },
  'universal-robots-ur10e': { cls: 'arm', speed: 0, color: 0x5b8fb9, size: [0.3, 1.3, 0.3] },
  'franka-fr3': { cls: 'arm', speed: 0, color: 0xf4f4f4, size: [0.25, 0.85, 0.25] },
  'kinova-gen3': { cls: 'arm', speed: 0, color: 0x222222, size: [0.2, 0.9, 0.2] },
  'fetch-robotics-fetch': { cls: 'mobile-manipulator', speed: 1.0, color: 0xdddddd, size: [0.56, 1.1, 0.56] },
  'clearpath-husky-a200': { cls: 'ugv', speed: 1.0, color: 0xffc000, size: [0.99, 0.39, 0.67] },
  'bitcraze-crazyflie-2-1-plus': { cls: 'drone', speed: 1.5, color: 0x3a3a3a, size: [0.1, 0.03, 0.1] },
};

function body(id) {
  const t = TWINS[id], [w, h, d] = t.size, s = t.cls === 'drone' ? 8 : 1.6;   // drones drawn larger to be visible
  const g = new THREE.Group(), m = new THREE.MeshStandardMaterial({ color: t.color, roughness: 0.4, metalness: 0.3 });
  if (t.cls === 'arm') {
    const base = new THREE.Mesh(new THREE.CylinderGeometry(w * 0.7, w * 0.8, 0.2), m);
    const l1 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.4, h * 0.5, w * 0.4), m); l1.position.y = h * 0.25 + 0.1;
    const elbow = new THREE.Group(); elbow.position.y = h * 0.5 + 0.1;
    const l2 = new THREE.Mesh(new THREE.BoxGeometry(w * 0.35, h * 0.45, w * 0.35), m); l2.position.y = h * 0.22; elbow.add(l2);
    g.add(base, l1, elbow); g.userData.joint = elbow;
  } else if (t.cls === 'drone') {
    const c = new THREE.Mesh(new THREE.BoxGeometry(w, h * 2, d), m); g.add(c);
    for (const [a, b] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) { const p = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.004, 12), new THREE.MeshBasicMaterial({ color: 0x88ccff })); p.position.set(a * w * 0.6, h, b * d * 0.6); g.add(p); }
  } else {
    const b = new THREE.Mesh(new THREE.BoxGeometry(w, t.cls === 'humanoid' ? h * 0.45 : h * 0.6, d), m);
    b.position.y = t.cls === 'humanoid' ? h * 0.7 : h * 0.55; g.add(b);
    if (t.cls === 'humanoid') { const hd = new THREE.Mesh(new THREE.SphereGeometry(w * 0.28, 12, 10), m); hd.position.y = h * 1.02; g.add(hd); }
    const legs = t.cls === 'quadruped' ? [[1, 1], [1, -1], [-1, 1], [-1, -1]] : t.cls === 'humanoid' ? [[0, 0.5], [0, -0.5]] : [];
    for (const [a, c] of legs) { const l = new THREE.Mesh(new THREE.BoxGeometry(0.06, h * 0.5, 0.06), m); l.position.set(a * w * 0.4, h * 0.25, c * d * 0.4); g.add(l); g.userData.legs = (g.userData.legs || []).concat(l); }
    if (t.cls === 'ugv' || t.cls === 'mobile-manipulator') for (const [a, c] of [[1, 1], [1, -1], [-1, 1], [-1, -1]]) {
      const wh = new THREE.Mesh(new THREE.CylinderGeometry(0.16, 0.16, 0.1, 12), new THREE.MeshStandardMaterial({ color: 0x111111 }));
      wh.rotation.x = Math.PI / 2; wh.position.set(a * w * 0.38, 0.16, c * d * 0.55); g.add(wh); }
  }
  g.scale.setScalar(s); g.traverse(o => { if (o.isMesh) o.castShadow = true; });
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
    const at = t.cls === 'arm' ? new THREE.Vector2(goal.x + Math.cos(a) * 8, goal.z + Math.sin(a) * 8) : start;
    o.position.set(at.x, ground.height(at.x, at.y), at.y); g.add(o);
    episodes.push({ task, t, o, goal: new THREE.Vector2(goal.x + Math.cos(a) * 6, goal.z + Math.sin(a) * 6), start: at.clone(),
      t0: 0, dist: 0, maxSlope: 0, stops: 0, state: 'running', ros: { cmd_vel: [0, 0], odom: [at.x, at.y, 0] } });
  });
  function record(e, outcome) {
    const r = { schema: 'worldforge-earth/robot-episode/1', world: world.slug, place: world.place, robot: e.task.robot,
      task_id: e.task.id, zone: e.task.zone, ros_action: e.task.ros?.action, topics: e.task.ros?.topics,
      outcome, duration_s: +e.t0.toFixed(2), path_m: +e.dist.toFixed(2), max_slope_deg: +e.maxSlope.toFixed(1),
      safety_stops: e.stops, success_checks: e.task.success, human_in_loop: e.task.human_in_loop,
      feedback_fields: e.task.feedback_schema?.fields, sim: 'kinematic scaffold (not vendor physics)', ts: new Date().toISOString() };
    records.push(r); return r;
  }
  g.userData.tick = (dt) => {
    for (const e of episodes) {
      if (e.state !== 'running') continue;
      e.t0 += dt;
      if (e.t.cls === 'arm') {
        const j = e.o.userData.joint; if (j) j.rotation.z = Math.sin(e.t0 * 1.4) * 0.9;
        e.o.rotation.y += dt * 0.6;
        if (e.t0 > 6) { record(e, 'success'); e.t0 = 0; }
        continue;
      }
      const p = new THREE.Vector2(e.o.position.x, e.o.position.z), to = e.goal.clone().sub(p), d = to.length();
      if (d < 1.5) {                      // episode done: record it, then run the next episode back to the start
        record(e, 'success'); e.t0 = 0; e.dist = 0; e.maxSlope = 0; e.stops = 0;
        const back = e.home || (e.home = new THREE.Vector2(e.o.position.x, e.o.position.z));
        [e.goal, e.home] = [e.start || back, e.goal]; e.start = e.home; continue;
      }
      to.normalize();
      const ahead = p.clone().addScaledVector(to, 2), rise = ground.height(ahead.x, ahead.y) - ground.height(p.x, p.y);
      const slope = Math.atan2(Math.abs(rise), 2) * 57.3; e.maxSlope = Math.max(e.maxSlope, slope);
      const limit = e.t.cls === 'drone' ? 90 : e.t.cls === 'quadruped' ? 30 : e.t.cls === 'humanoid' ? 12 : 20;
      if (slope > limit) { e.stops++; to.rotateAround(new THREE.Vector2(), 0.9); }
      const step = Math.min(Math.max(e.t.speed, 0.6) * 12 * dt, d);   // 12x sim speed-up (training throughput)
      e.o.position.x += to.x * step; e.o.position.z += to.y * step; e.dist += step;
      e.o.position.y = ground.height(e.o.position.x, e.o.position.z) + (e.t.cls === 'drone' ? 8 + Math.sin(e.t0 * 2) : 0);
      e.o.rotation.y = Math.atan2(to.x, to.y);
      (e.o.userData.legs || []).forEach((l, k) => { l.rotation.x = Math.sin(e.t0 * 10 + k * Math.PI) * 0.5; });
      e.ros.cmd_vel = [e.t.speed, 0]; e.ros.odom = [+e.o.position.x.toFixed(1), +e.o.position.z.toFixed(1), +e.o.rotation.y.toFixed(2)];
      if (e.t0 > 120) { record(e, 'timeout'); e.state = 'done'; }
    }
  };
  g.userData.episodes = episodes; g.userData.records = records;
  g.userData.jsonl = () => records.map(r => JSON.stringify(r)).join('\n') + '\n';
  return g;
}

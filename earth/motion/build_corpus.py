#!/usr/bin/env python3
"""build_corpus.py -- Movement Task Corpus (MTC-1) for the WorldForge movement LM.

Merges two honest sources into one JSONL corpus, per world:
  1. ROBOT episodes (schema worldforge-earth/robot-episode/3, offline mirror of the live
     robots.js sim): manufacturer twins marching their earth/team tasks over the REAL
     elevation grid (bilinear height sampling, slope stops, 2 Hz route + actuated joint
     traces using the same gait formulas as the browser).
  2. HUMAN episodes (schema worldforge-earth/human-motion/1, offline mirror of
     training-sim.js): union-module scenarios with per-step movement primitives derived
     from each step's wording (same regexes as the JS stepMoves).

Everything is deterministic: mulberry32 seeded per (world, episode-id), so a rebuild is
byte-identical. Union scenarios are parsed OUT OF site/earth/js/training-sim.js so the
corpus can never drift from the shipped union training modules.

Output: earth/motion/corpus/motion-corpus.jsonl + corpus-stats.json
"""
import json, math, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SITE = os.path.join(ROOT, 'site', 'earth')
OUT_DIR = os.path.join(ROOT, 'earth', 'motion', 'corpus')


# deterministic RNG, same constants as the JS (fnv1a hash + mulberry32)
def fnv(s):
    h = 2166136261
    for c in s:
        h ^= ord(c)
        h = (h * 16777619) & 0xFFFFFFFF
    return h


def mulberry32(seed):
    a = [seed & 0xFFFFFFFF]
    def nxt():
        a[0] = (a[0] + 0x6D2B79F5) & 0xFFFFFFFF
        t = a[0]
        t = (t ^ (t >> 15)) * (t | 1) & 0xFFFFFFFF
        t = (t ^ (t + ((t ^ (t >> 7)) * (t | 61) & 0xFFFFFFFF))) & 0xFFFFFFFF
        return ((t ^ (t >> 14)) & 0xFFFFFFFF) / 4294967296
    return nxt


# union modules: parsed straight out of the shipped training-sim.js (single source of truth)
def union_scenarios():
    src = open(os.path.join(SITE, 'js', 'training-sim.js')).read()
    m = re.search(r'export const SCENARIOS = \{(.*?)\n\};', src, re.S)
    if not m:
        raise SystemExit('cannot find SCENARIOS in training-sim.js')
    out = {}
    for sec in re.finditer(r"'([^']+)': \[(.*?)\](?=,\n  '|$|\s*\n\})", m.group(1), re.S):
        sector, body = sec.group(1), sec.group(2)
        scen = []
        for s in re.finditer(r"\{ name: '([^']+)', steps: \[([^\]]*)\], duration: (\d+) \}", body):
            scen.append({'name': s.group(1),
                         'steps': [x.strip().strip("'") for x in s.group(2).split(',')],
                         'duration_min': int(s.group(3))})
        if scen:
            out[sector] = scen
    if 'General' not in out:
        raise SystemExit(f'parsed sectors {list(out)} -- General missing from training-sim.js')
    return out


# manufacturer twin classes, parsed from robots.js (class + speed drive the route sim)
def twins():
    src = open(os.path.join(SITE, 'js', 'robots.js')).read()
    m = re.search(r'export const TWINS = \{(.*?)\n\};', src, re.S)
    if not m:
        raise SystemExit('cannot find TWINS in robots.js')
    out = {}
    for t in re.finditer(r"'([a-z0-9-]+)': \{([^{}]*?)\}", m.group(1)):
        rid, body = t.group(1), t.group(2)
        cls = re.search(r"cls: '([\w-]+)'", body)
        spd = re.search(r"speed: ([\d.]+)", body)
        if cls and spd:
            out[rid] = {'cls': cls.group(1), 'speed': float(spd.group(1))}
    if len(out) < 10:
        raise SystemExit(f'parsed only {len(out)} twins from robots.js')
    return out


# terrain: the world's REAL elevation grid where fetched, else flat ground
class Ground:
    def __init__(self, slug):
        p = os.path.join(SITE, 'data', f'{slug}.geo.json')
        self.N = self.H = self.E = None
        if os.path.exists(p):
            g = json.load(open(p))
            self.N, self.H, self.E = g['n'], g['half'], g['elev']

    def height(self, x, z):
        if not self.E:
            return 0.0
        N, H, E = self.N, self.H, self.E
        step = (2 * H) / (N - 1)
        fx = min(max((x + H) / step, 0), N - 1.001)
        fz = min(max((z + H) / step, 0), N - 1.001)
        i, j = int(fx), int(fz)
        ax, az = fx - i, fz - j
        a, b = E[j * N + i], E[j * N + i + 1]
        c, d = E[(j + 1) * N + i], E[(j + 1) * N + i + 1]
        return (a * (1 - ax) + b * ax) * (1 - az) + (c * (1 - ax) + d * ax) * az


# robot episode: mirrors robots.js (12x sim speed, slope stops, 2 Hz route + gait joints)
SLOPE_LIMIT = {'drone': 90, 'quadruped': 30, 'humanoid': 12}


def robot_episode(slug, task, twin, ground, rng):
    cls, speed = twin['cls'], twin['speed']
    a = rng() * 6.28
    p = [math.cos(a) * 26, math.sin(a) * 26]
    goal = [math.cos(a + 2.1) * (40 + rng() * 50), math.sin(a + 2.1) * (40 + rng() * 50)]
    limit = SLOPE_LIMIT.get(cls, 20)
    dt, t0, dist, stops, max_slope = 0.5, 0.0, 0.0, 0, 0.0
    route, joints, events = [], [], []
    outcome = 'timeout'
    while t0 < 120:
        tx, tz = goal[0] - p[0], goal[1] - p[1]
        d = math.hypot(tx, tz)
        if d < 1.5:
            outcome = 'success'
            break
        if cls != 'arm':
            ux, uz = tx / d, tz / d
            slope = math.degrees(math.atan2(abs(ground.height(p[0] + ux * 2, p[1] + uz * 2) - ground.height(p[0], p[1])), 2))
            max_slope = max(max_slope, slope)
            if slope > limit:
                stops += 1
                events.append({'t': round(t0, 1), 'type': 'slope_stop', 'slope_deg': round(slope, 1)})
                ux, uz = ux * math.cos(0.9) - uz * math.sin(0.9), ux * math.sin(0.9) + uz * math.cos(0.9)
            step = min(max(speed, 0.6) * 12 * dt, d)
            p[0] += ux * step; p[1] += uz * step
            dist += step
        # 2 Hz sampling: route + actuated joints (same formulas as the browser)
        rot = math.atan2(goal[0] - p[0], goal[1] - p[1]) if cls != 'arm' else t0 * 0.6
        route.append([round(t0, 1), round(p[0], 1), round(p[1], 1), round(rot, 2),
                      round(max(0, ground.height(p[0], p[1])), 1)])
        if cls == 'arm':
            joints.append([round(math.sin(t0 * 1.4) * 0.9, 2), round(math.cos(t0 * 1.1) * 0.6, 2)])
        else:
            j = []
            for k in range(4):
                j.extend([round(math.sin(t0 * 10 + k * math.pi) * 0.5, 2),
                          round(math.sin(t0 * 10 + k * math.pi + 0.6) * 0.4, 2)])
            for k in range(2):
                j.append(round(math.sin(t0 * 6 + k * math.pi) * 0.3, 2))
            joints.append(j)
        t0 += dt
    return {'schema': 'worldforge-earth/robot-episode/3', 'world': slug, 'robot': task['robot'],
            'class': cls, 'task_id': task['id'], 'goal': task.get('goal'), 'terrain': task.get('terrain'),
            'outcome': outcome, 'duration_s': round(t0, 1), 'path_m': round(dist, 1),
            'max_slope_deg': round(max_slope, 1), 'safety_stops': stops,
            'events': events[:24], 'route': route[:240], 'joints': joints[:240], 'joints_hz': 2,
            'sim': 'kinematic scaffold (mirrors robots.js)'}


# human episode: mirrors training-sim.js stepMoves (same regexes, same verb set)
STEP_RX = [
    ('LIFT_SET', re.compile(r'rack|mount|panel|install|load|wire|cable|frame|rig|build')),
    ('INSPECT', re.compile(r'test|check|inspect|scan|verif|audit|ndt|quality|diagnos')),
    ('TYPE', re.compile(r'config|program|type|log|document|report|record|plan|cue|eq|mix|reconcil')),
    ('BEND', re.compile(r'gown|entry|exit|prep|clean|cycle|stock|receive|sort|count|collect')),
    ('REACH_SET', re.compile(r'power|energize|switch|launch|deploy|activate|live|commission|press')),
]


def step_moves(name, rng):
    mv = [{'v': 'WALK', 'm': 3 + int(rng() * 9), 'dir': int(rng() * 16)}]
    hit = set()
    for tag, rx in STEP_RX:
        if rx.search(name.lower()):
            hit.add(tag)
            if tag == 'LIFT_SET':
                mv += [{'v': 'LIFT', 'kg': round(1 + rng() * 11, 1)},
                       {'v': 'CARRY', 'm': round(1 + rng() * 4, 1)}, {'v': 'PLACE'}]
            elif tag == 'BEND':
                mv.append({'v': 'BEND', 'deg': 20 + int(rng() * 40)})
            elif tag == 'REACH_SET':
                mv += [{'v': 'REACH', 'm': round(0.4 + rng() * 0.35, 2)}, {'v': 'PRESS'}]
            else:
                mv.append({'v': tag, 's': (20 if tag == 'INSPECT' else 30) + int(rng() * (40 if tag == 'INSPECT' else 90))})
    mv.append({'v': 'CHECK'})
    return mv, hit


def human_episode(slug, scenario, sector, rng):
    steps = []
    per = scenario['duration_min'] * 60 / max(1, len(scenario['steps']))
    for name in scenario['steps']:
        moves, hit = step_moves(name, rng)
        elapsed = min(240, max(5, per * (0.5 + rng())))
        bend = next((m['deg'] for m in moves if m['v'] == 'BEND'), 0)
        steps.append({'step': name, 'elapsed_s': round(elapsed, 1), 'moves': moves,
                      'posture': {'bend_deg': bend, 'reach_m': round(0.3 + rng() * 0.4, 2),
                                  'load_kg': next((m['kg'] for m in moves if m['v'] == 'LIFT'), 0)}})
    return {'schema': 'worldforge-earth/human-motion/1', 'world': slug, 'agent': 'human-trainee',
            'scenario': scenario['name'], 'sector': sector, 'steps': steps,
            'outcome': 'success', 'total_s': round(sum(s['elapsed_s'] for s in steps), 1),
            'sim': 'union-module movement model (mirrors training-sim.js)'}


def main():
    scenarios = union_scenarios()
    twin_specs = twins()
    worlds = json.load(open(os.path.join(SITE, 'worlds.json')))
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, 'motion-corpus.jsonl')
    n_robot = n_human = 0
    with open(out_path, 'w') as f:
        for w in worlds:
            slug = w['slug']
            sector = (w.get('trades') or {}).get('sector') or 'General'
            scen = scenarios.get(sector) or scenarios['General']
            ground = Ground(slug)
            rp = os.path.join(SITE, 'team', 'robots', f'{slug}.json')
            if os.path.exists(rp):
                for task in json.load(open(rp)).get('tasks', []):
                    twin = twin_specs.get(task['robot'])
                    if not twin:
                        continue
                    ep = robot_episode(slug, task, twin, ground, mulberry32(fnv(slug + task['id'])))
                    f.write(json.dumps(ep, separators=(',', ':')) + '\n')
                    n_robot += 1
            for sc in scen:
                ep = human_episode(slug, sc, sector, mulberry32(fnv(slug + sc['name'])))
                f.write(json.dumps(ep, separators=(',', ':')) + '\n')
                n_human += 1
    stats = {'episodes': {'robot': n_robot, 'human': n_human, 'total': n_robot + n_human},
             'worlds': len(worlds),
             'sectors': sorted(set((w.get('trades') or {}).get('sector') or 'General' for w in worlds)),
             'scenarios': {k: [s['name'] for s in v] for k, v in scenarios.items()},
             'bytes': os.path.getsize(out_path)}
    with open(os.path.join(OUT_DIR, 'corpus-stats.json'), 'w') as f:
        json.dump(stats, f, indent=1)
    print(f'MTC-1 corpus: {n_robot} robot + {n_human} human episodes, {stats["bytes"]/1e6:.1f} MB -> {out_path}')


if __name__ == '__main__':
    main()

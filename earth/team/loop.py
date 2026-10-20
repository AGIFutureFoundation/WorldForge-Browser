#!/usr/bin/env python3
"""WorldForge Earth GLM team loop: metaprompt -> generate -> eval -> repair, with a heartbeat.

Claude (in Cline) orchestrates and reviews; the GLM team (Z.ai) does the bulk generation, so Claude credits stay small.
Each job is one world x one role. Output: earth/team/out/<role>/<slug>.json, only if it passes its evals.
A failed eval feeds its exact failure messages back into the prompt (metaprompt repair), up to 3 tries.

  python3 earth/team/loop.py --minutes 45 [--workers 6] [--roles a,b]
Heartbeat: earth/team/heartbeat.jsonl (one line per job + one summary line per minute)
"""
import concurrent.futures as cf, json, pathlib, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent
EARTH = HERE.parent
sys.path.insert(0, '/Users/romanbridge.x/Documents/tempgithelp/mail')
import glm  # noqa: E402  (Z.ai key from tempgithelp/.env, never printed)
from roles import ROLES  # noqa: E402

OUT = HERE / 'out'
HB = HERE / 'heartbeat.jsonl'
LOCK = threading.Lock()
STATS = {'ok': 0, 'fail': 0, 'repaired': 0, 'calls': 0, 'chars_out': 0}


def beat(**kw):
    kw['t'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    with LOCK, HB.open('a') as f:
        f.write(json.dumps(kw) + '\n')


def brief(slug):
    spec = json.loads((EARTH / 'specs' / f'{slug}.json').read_text())
    loc = next(l for l in json.loads((EARTH / 'locations.json').read_text()) if l['slug'] == slug)
    geo_p = EARTH.parent / 'site' / 'earth' / 'data' / f'{slug}.geo.json'
    geo = None
    if geo_p.exists():
        g = json.loads(geo_p.read_text())
        named = sorted({f['n'] for k in ('building', 'park', 'water', 'river', 'wood') for f in g['features'][k] if f.get('n')})
        e = g['elev']
        geo = {'counts': {k: len(v) for k, v in g['features'].items()}, 'relief_m': round(max(e) - min(e), 1),
               'named_places_in_1200m_square': named[:40], 'has_sea_level_water': g.get('sea') is not None}
    return {'world': spec, 'place': loc, 'map': geo}


def parse(text):
    i, j = text.find('{'), text.rfind('}')
    if i < 0 or j < 0:
        raise ValueError('no JSON object in reply')
    return json.loads(text[i:j + 1])


def run_job(role, slug, deadline):
    dst = OUT / role / f'{slug}.json'
    if dst.exists():
        return 'skip'
    r = ROLES[role]
    b = brief(slug)
    if r.get('needs_map') and not b['map']:
        return 'wait'
    user = r['prompt'](b)
    errors = []
    for attempt in range(3):
        if time.time() > deadline:
            return 'timeout'
        msg = user if not errors else (user + '\n\nYOUR PREVIOUS ANSWER FAILED THESE CHECKS - fix every one and '
                                       'return the full JSON again:\n- ' + '\n- '.join(errors[:12]))
        t0 = time.time()
        try:
            txt = glm.ask(r['system'], msg, model=r.get('model', 'glm-5.3'), max_tokens=r.get('max_tokens', 6000))
            with LOCK:
                STATS['calls'] += 1
                STATS['chars_out'] += len(txt)
            doc = parse(txt)
            errors = r['evals'](doc, b)
        except Exception as e:  # noqa: BLE001
            errors = [f'{type(e).__name__}: {str(e)[:200]}']
        beat(role=role, slug=slug, attempt=attempt + 1, secs=round(time.time() - t0, 1), errors=errors[:5])
        if not errors:
            doc['_meta'] = {'role': role, 'slug': slug, 'generator': 'glm (Z.ai) via earth/team/loop.py',
                            'attempts': attempt + 1, 'evals_passed': True, 'status': 'draft, unreviewed by a person'}
            dst.parent.mkdir(parents=True, exist_ok=True)
            dst.write_text(json.dumps(doc, indent=1, ensure_ascii=False))
            with LOCK:
                STATS['ok'] += 1
                STATS['repaired'] += attempt > 0
            return 'ok'
    with LOCK:
        STATS['fail'] += 1
    return 'fail'


def main():
    minutes = float(sys.argv[sys.argv.index('--minutes') + 1]) if '--minutes' in sys.argv else 45
    workers = int(sys.argv[sys.argv.index('--workers') + 1]) if '--workers' in sys.argv else 6
    roles = sys.argv[sys.argv.index('--roles') + 1].split(',') if '--roles' in sys.argv else list(ROLES)
    deadline = time.time() + minutes * 60
    slugs = [l['slug'] for l in json.loads((EARTH / 'locations.json').read_text())]
    beat(event='start', minutes=minutes, workers=workers, roles=roles, worlds=len(slugs))
    rounds = 0
    while time.time() < deadline:
        rounds += 1
        jobs = [(r, s) for r in roles for s in slugs if not (OUT / r / f'{s}.json').exists()]
        if not jobs:
            break
        with cf.ThreadPoolExecutor(workers) as ex:
            futs = {ex.submit(run_job, r, s, deadline): (r, s) for r, s in jobs}
            last = time.time()
            for f in cf.as_completed(futs):
                f.result()
                if time.time() - last > 60:
                    beat(event='heartbeat', round=rounds, **STATS, remaining_min=round((deadline - time.time()) / 60, 1))
                    last = time.time()
        time.sleep(5)  # 'wait' jobs (map not baked yet) get picked up next round
    done = {r: len(list((OUT / r).glob('*.json'))) if (OUT / r).exists() else 0 for r in roles}
    beat(event='end', rounds=rounds, done=done, **STATS)
    print(json.dumps({'done': done, **STATS}))


if __name__ == '__main__':
    main()

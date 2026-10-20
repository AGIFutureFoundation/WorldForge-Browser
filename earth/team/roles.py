"""GLM team roles for WorldForge Earth: each role = system metaprompt + user prompt builder + evals.

Evals are code, not vibes: they check structure, that names come from the brief (no invented zones/places),
that human-reserved actions never appear as agent/robot actions, and that numbers stay physically sane.
"""
import json

RESERVED = ['governance.final_vote', 'charter.amend', 'treasury.transfer', 'proposal.enact', 'windfall.distribute',
            'steward.appoint']
TRADES = ['ironworkers', 'electricians', 'pipefitters', 'carpenters', 'operating-eng', 'laborers', 'sheetmetal',
          'bricklayers', 'cement-masons', 'roofers', 'painters', 'glaziers', 'insulators', 'millwrights', 'welders',
          'hvacr', 'crane-ops', 'riggers', 'line-workers', 'solar', 'wind', 'surveyors', 'fire-sprinkler', 'hazmat',
          'machinists', 'water-distrib', 'wastewater', 'battery-storage', 'ev-charging', 'grounds', 'teamsters', 'divers']
ROBOTS = ['boston-dynamics-spot', 'unitree-go2', 'pal-robotics-talos', 'softbank-nao', 'universal-robots-ur10e',
          'franka-fr3', 'kinova-gen3', 'fetch-robotics-fetch', 'clearpath-husky-a200', 'bitcraze-crazyflie-2-1-plus']
AUDIENCES = ['union', 'k12', 'ngo', 'nonprofit']
BIOMES = ['temperate-forest', 'wetland', 'coast', 'desert', 'alpine', 'grassland', 'tropical', 'urban-park',
          'river-valley', 'mediterranean']

BASE = ('You are a member of the WorldForge Earth build team (AGI Future Foundation PBC, "Powered by AGI Corp"). '
        'Principle: "Agents operate; people govern." Agents and robots NEVER perform these human-reserved actions: '
        + ', '.join(RESERVED) + '. Ground everything in the BRIEF: the world spec, the real place and the real map '
        'facts. Do not invent statistics, prices, partners or claims of deployment. Output ONE JSON object only, no '
        'prose, no code fences.')


def _brief(b):
    return 'BRIEF:\n' + json.dumps(b, ensure_ascii=False)[:9000]


def _zones(b):
    return [z['name'] for z in b['world'].get('zones', [])]


def _txt(doc):
    return json.dumps(doc, ensure_ascii=False).lower()


def _reserved_hits(doc):
    t = _txt(doc)
    return [r for r in RESERVED if r in t and 'human' not in t[max(0, t.find(r) - 160):t.find(r) + 160]]



# ---------------------------------------------------------------- 1. world: detailed world from metaprompt + real map
def world_prompt(b):
    return (_brief(b) + '\n\nDesign the DETAILED walkable world for this brief, placed on the real place. Return:\n'
            '{"title","summary" (<=400 chars),"biome" (one of ' + '|'.join(BIOMES) + '),'
            '"districts":[{"zone" (EXACT zone name from world.zones),"real_anchor" (a real feature in/near the place, '
            'prefer names from map.named_places_in_1200m_square),"buildings":[{"name","use","floors" (1-40)}] (2-4),'
            '"interior_rooms":[..3-6 short names],"props":[..4-8],"npc_agents":[..names of world.agents in that zone]}],'
            '"flora":{"trees":[..3-6 species that really grow in this biome/region],"shrubs":[..2-4],"flowers":[..2-5],'
            '"ground":"grass|moss|sand|gravel|scrub"},'
            '"water":{"kind":"ocean|river|lake|bay|fountain|none","flow_mps" (0-3),"wave_m" (0-2)},'
            '"wind":{"prevailing_from":"N|NE|E|SE|S|SW|W|NW","mean_mps" (0-15)},'
            '"day_cycle":{"sunrise_local":"HH:MM","sunset_local":"HH:MM"},'
            '"court":{"name","style","why_here" (<=160)},'
            '"quests":[{"title","from_zone","to_zone","steps":[..3-5],"xp" (10-100)}] (3-5)}\n'
            'Every zone in world.zones must appear exactly once in districts.')


def world_evals(doc, b):
    e = []
    zones = _zones(b)
    got = [d.get('zone') for d in doc.get('districts', [])]
    for z in zones:
        if got.count(z) != 1:
            e.append(f'district for zone "{z}" must appear exactly once (got {got.count(z)})')
    for g in got:
        if g not in zones:
            e.append(f'district zone "{g}" is not a zone in world.zones; use exact names: {zones}')
    if doc.get('biome') not in BIOMES:
        e.append(f'biome must be one of {BIOMES}')
    fl = doc.get('flora', {})
    if not (3 <= len(fl.get('trees', [])) <= 6) or len(fl.get('flowers', [])) < 2:
        e.append('flora.trees needs 3-6 species and flora.flowers at least 2')
    w = doc.get('water', {})
    if not (0 <= float(w.get('flow_mps', -1)) <= 3) or not (0 <= float(w.get('wave_m', -1)) <= 2):
        e.append('water.flow_mps must be 0-3 and wave_m 0-2')
    if not (0 <= float(doc.get('wind', {}).get('mean_mps', -1)) <= 15):
        e.append('wind.mean_mps must be 0-15')
    for d in doc.get('districts', []):
        for bl in d.get('buildings', []):
            if not (1 <= int(bl.get('floors', 0)) <= 40):
                e.append(f'building {bl.get("name")} floors must be 1-40')
    qs = doc.get('quests', [])
    if not 3 <= len(qs) <= 5:
        e.append('quests must have 3-5 entries')
    for q in qs:
        for k in ('from_zone', 'to_zone'):
            if q.get(k) not in zones:
                e.append(f'quest "{q.get("title")}" {k} must be an exact zone name')
    e += [f'reserved action {r} assigned to an agent' for r in _reserved_hits(doc)]
    return e


# ---------------------------------------------------------------- 2. trades: human training simulator (unions)
def trades_prompt(b):
    return (_brief(b) + '\n\nWrite the HUMAN TRADES TRAINING SIMULATOR for this world: realistic job-site scenarios '
            'a union apprentice would meet when building or maintaining this real place. Return:\n'
            '{"scenarios":[{"id" (kebab),"trade" (one of ' + ','.join(TRADES) + '),"zone" (exact zone name),'
            '"task" (<=200),"hazards":[2-4],"ppe":[2-5],"steps":[4-8 short imperative steps],'
            '"rubric":[{"axis","pass_if"} 3-5],"minutes" (10-120),"level":"apprentice|journey|foreman",'
            '"robot_assist" (one of ' + ','.join(ROBOTS) + ' or null),"robot_role" (<=120 or null)}] (5-8),'
            '"credential":{"name","requires":[scenario ids]}}')


def trades_evals(doc, b):
    e = []
    zones = _zones(b)
    sc = doc.get('scenarios', [])
    if not 5 <= len(sc) <= 8:
        e.append('scenarios must have 5-8 entries')
    ids = set()
    for s in sc:
        sid = s.get('id', '?')
        ids.add(sid)
        if s.get('trade') not in TRADES:
            e.append(f'{sid}: trade must be one of the listed trades')
        if s.get('zone') not in zones:
            e.append(f'{sid}: zone must be an exact zone name from {zones}')
        if not 4 <= len(s.get('steps', [])) <= 8:
            e.append(f'{sid}: steps must be 4-8')
        if not 3 <= len(s.get('rubric', [])) <= 5:
            e.append(f'{sid}: rubric must have 3-5 axes')
        if not s.get('ppe') or not s.get('hazards'):
            e.append(f'{sid}: hazards and ppe are required')
        if s.get('robot_assist') not in ROBOTS + [None]:
            e.append(f'{sid}: robot_assist must be a listed robot id or null')
        if not 10 <= int(s.get('minutes', 0)) <= 120:
            e.append(f'{sid}: minutes must be 10-120')
    for r in doc.get('credential', {}).get('requires', []):
        if r not in ids:
            e.append(f'credential requires unknown scenario id {r}')
    e += [f'reserved action {r} assigned to an agent' for r in _reserved_hits(doc)]
    return e


# ---------------------------------------------------------------- 3. robots: ROS 2 style robot training episodes
def robots_prompt(b):
    return (_brief(b) + '\n\nWrite ROBOT SIMULATION TRAINING TASKS for digital twins in this world, in ROS 2 style. '
            'Robots: ' + ', '.join(ROBOTS) + '. Return:\n'
            '{"tasks":[{"id" (kebab),"robot" (robot id),"zone" (exact zone name),"goal" (<=160),'
            '"ros":{"action" (e.g. /navigate_to_pose, /follow_joint_trajectory, /pick, /inspect),"topics":[2-5 topic '
            'names starting with /],"frame":"map|odom|base_link"},'
            '"terrain" (what real ground/obstacles from the place matter),"success":[2-4 measurable checks],'
            '"safety_stops":[2-4],"human_in_loop" (what a person approves; <=120),'
            '"feedback_schema":{"fields":[4-8 field names for the JSONL training record]}}] (5-8)}')


def robots_evals(doc, b):
    e = []
    zones = _zones(b)
    ts = doc.get('tasks', [])
    if not 5 <= len(ts) <= 8:
        e.append('tasks must have 5-8 entries')
    for t in ts:
        tid = t.get('id', '?')
        if t.get('robot') not in ROBOTS:
            e.append(f'{tid}: robot must be one of {ROBOTS}')
        if t.get('zone') not in zones:
            e.append(f'{tid}: zone must be an exact zone name')
        ros = t.get('ros', {})
        if not str(ros.get('action', '')).startswith('/'):
            e.append(f'{tid}: ros.action must start with /')
        if not ros.get('topics') or any(not str(x).startswith('/') for x in ros.get('topics', [])):
            e.append(f'{tid}: ros.topics must be names starting with /')
        if not 2 <= len(t.get('success', [])) <= 4 or not t.get('safety_stops'):
            e.append(f'{tid}: needs 2-4 success checks and safety_stops')
        if not t.get('human_in_loop'):
            e.append(f'{tid}: human_in_loop is required')
        if not 4 <= len(t.get('feedback_schema', {}).get('fields', [])) <= 8:
            e.append(f'{tid}: feedback_schema.fields must have 4-8 names')
    e += [f'reserved action {r} assigned to a robot' for r in _reserved_hits(doc)]
    return e



# ---------------------------------------------------------------- 4. programs: K-12 / NGO / nonprofit / union
def programs_prompt(b):
    return (_brief(b) + '\n\nWrite LEARNING PROGRAMS that use this world for four audiences: union, k12, ngo, '
            'nonprofit. Return:\n{"programs":[{"audience" (union|k12|ngo|nonprofit),"title","grade_or_level",'
            '"outcomes":[2-4],"sessions":[{"zone" (exact zone name),"activity" (<=160),"minutes" (10-90)}] (3-5),'
            '"data_shared" (what anonymised data the learners contribute to shared models, <=160),'
            '"consent" (how consent / privacy is handled, <=160; for k12 must mention guardian/parent consent)}] '
            '(exactly 4, one per audience)}')


def programs_evals(doc, b):
    e = []
    zones = _zones(b)
    ps = doc.get('programs', [])
    if sorted(str(p.get('audience')) for p in ps) != sorted(AUDIENCES):
        e.append('programs must be exactly one per audience: union, k12, ngo, nonprofit')
    for p in ps:
        a = p.get('audience')
        for s in p.get('sessions', []):
            if s.get('zone') not in zones:
                e.append(f'{a}: session zone "{s.get("zone")}" must be an exact zone name')
            if not 10 <= int(s.get('minutes', 0)) <= 90:
                e.append(f'{a}: session minutes must be 10-90')
        if not 3 <= len(p.get('sessions', [])) <= 5:
            e.append(f'{a}: sessions must be 3-5')
        if a == 'k12' and not any(w in str(p.get('consent', '')).lower() for w in ('parent', 'guardian')):
            e.append('k12 consent must mention parent or guardian consent')
    e += [f'reserved action {r} assigned to an agent' for r in _reserved_hits(doc)]
    return e


ROLES = {
    'world': {'system': BASE + ' Role: world architect.', 'prompt': world_prompt, 'evals': world_evals,
              'needs_map': True},
    'trades': {'system': BASE + ' Role: union training director (OSHA-minded).', 'prompt': trades_prompt,
               'evals': trades_evals},
    'robots': {'system': BASE + ' Role: ROS 2 robotics simulation engineer.', 'prompt': robots_prompt,
               'evals': robots_evals},
    'programs': {'system': BASE + ' Role: education and nonprofit program designer.', 'prompt': programs_prompt,
                 'evals': programs_evals},
}


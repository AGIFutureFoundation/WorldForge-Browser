#!/usr/bin/env python3
"""local_gen.py -- GLM-free fallback for earth/team/loop.py (temporary).

The Z.ai GLM keys in <workspace>/.env are expired/zero-balance, so loop.py cannot run.
Until a funded key lands, this generator authors the same four role documents
(world, trades, robots, programs) for every geo-complete world that has none,
grounded in the same brief inputs loop.py uses (spec + locations + geo json),
and validates each document with the SAME evals from roles.py before writing it.
Deterministic, no model calls, no network. Skips any file that already exists
(so GLM-authored work is never overwritten). Heartbeat: earth/team/heartbeat.jsonl.

    python3 earth/team/local_gen.py            # all geo-complete worlds missing content
    python3 earth/team/local_gen.py --slugs chi-pilsen,nola-treme
    python3 earth/team/local_gen.py --dry      # show what would be generated
"""
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent          # .../earth/team
EARTH = HERE.parent                                     # .../earth
ROOT = EARTH.parent                                     # .../WorldForge-Browser
SITE = ROOT / 'site' / 'earth'
sys.path.insert(0, str(HERE))
from roles import ROLES, TRADES, ROBOTS, AUDIENCES, BIOMES  # noqa: E402  (shared evals + vocab)


def biome_ok(b):
    """locations.json uses urban-core/industrial/indoor-clinic; roles.py evals want the ten canonical biomes."""
    return b if b in BIOMES else 'urban-park'

HB = HERE / 'heartbeat.jsonl'
GEN = 'local_gen.py (claude-authored fallback; Z.ai GLM key expired/balance 0)'

# ---- region flavor, all real species/weather facts -------------------------------------------------
REGIONS = {
    'sf': {
        'zone_extra': 'Harbor Annex', 'water': ('bay', 0.4, 0.3), 'wind': 'SW', 'wind_mps': 6.5,
        'sunrise': '06:35', 'sunset': '19:45', 'ground': 'gravel',
        'trees': ['Coast live oak', 'Monterey cypress', 'London plane', 'California buckeye',
                  'Blue gum eucalyptus', 'Blackwood acacia'],
        'shrubs': ['California coffeeberry', 'Coyote brush', 'Sticky monkeyflower'],
        'flowers': ['California poppy', 'Douglas iris', 'Seaside daisy', 'Yarrow', 'Fremont star lily'],
    },
    'nola': {
        'zone_extra': 'Riverfront Annex', 'water': ('river', 1.2, 0.1), 'wind': 'SE', 'wind_mps': 4.2,
        'sunrise': '06:25', 'sunset': '19:35', 'ground': 'grass',
        'trees': ['Southern live oak', 'Bald cypress', 'Crape myrtle', 'Southern magnolia',
                  'Water tupelo', 'American elm'],
        'shrubs': ['Wax myrtle', 'Yaupon holly', 'Virginia sweetspire'],
        'flowers': ['Louisiana iris', 'Azalea', 'Cast iron plant', 'Red spider lily', 'Sweet olive blossom'],
    },
    'chi': {
        'zone_extra': 'Lakefront Annex', 'water': ('lake', 0.2, 0.2), 'wind': 'SW', 'wind_mps': 5.8,
        'sunrise': '06:10', 'sunset': '19:20', 'ground': 'grass',
        'trees': ['Bur oak', 'Northern catalpa', 'Honey locust', 'American elm', 'Green ash', 'Hackberry'],
        'shrubs': ['Arrowwood viburnum', 'Winterberry holly', 'Ninebark'],
        'flowers': ['Purple coneflower', 'Black-eyed Susan', 'Wild columbine', 'Wild bergamot', 'Prairie smoke'],
    },
}
GENERIC = {
    'zone_extra': 'Field Annex', 'water': ('none', 0.0, 0.0), 'wind': 'E', 'wind_mps': 3.5,
    'sunrise': '06:30', 'sunset': '19:40', 'ground': 'grass',
    'trees': ['Honey locust', 'Ginkgo', 'Littleleaf linden', 'London plane', 'Northern red oak'],
    'shrubs': ['Panicle hydrangea', 'Smooth sumac', 'New jersey tea'],
    'flowers': ['Yarrow', 'Coreopsis', 'Blanketflower', 'Milkweed'],
}
ZONES = [
    ('Training Yard', 'Outdoor drills, rigging practice and equipment familiarization on real terrain'),
    ('Safety Office', 'Permits, briefings, hazard boards and human sign-off for every supervised task'),
    ('Robotics Lab', 'Cobot cells, charging docks and teleoperation stations for the robot fleet'),
    ('Operations Center', 'Dashboards over live telemetry: zones, episodes, training records and evals'),
    ('Community Plaza', 'Public programs, tours and steward office where people govern the world'),
]
AGENTS = [
    ('Coach', 'Orientation, skills progression and drill supervision', 'Training Yard'),
    ('Safety Steward', 'Permit checks and toolbox talks before any live task', 'Safety Office'),
    ('Fleet Lead', 'Robot dispatch, teleoperation and episode review', 'Robotics Lab'),
    ('Data Clerk', 'Training records, telemetry files and dataset packaging', 'Operations Center'),
    ('Community Guide', 'Tours, questions and the public feedback board', 'Community Plaza'),
    ('Site Steward', 'Human-only approvals: budget items, escalations and records release', 'Community Plaza'),
]
BUILDINGS = [
    ('{anchor} Training Hall', 'Training facility', 3),
    ('{anchor} Field Office', 'Site office', 2),
    ('Robotics Workshop', 'Lab and maintenance', 1),
    ('Equipment Shed', 'Storage and tools', 1),
    ('{anchor} Steward House', 'Community and steward office', 2),
]
ROOMS = {
    'Training Yard': ['Tool Room', 'PPE Cage', 'Rigging Bay', 'Weather Shelter'],
    'Safety Office': ['Permit Desk', 'Hazard Board Room', 'Toolbox Talk Room', 'Records Room'],
    'Robotics Lab': ['Cobot Cell A', 'Cobot Cell B', 'Docking Hall', 'Teleop Booth', 'Repair Bench'],
    'Operations Center': ['Telemetry Wall', 'Ops Floor', 'Review Room', 'Dataset Archive'],
    'Community Plaza': ['Tour Kiosk', 'Feedback Room', 'Steward Office', 'Reading Corner'],
}
PROPS = ['terminals', 'wayfinding', 'steward plaques', 'tool benches', 'charging docks', 'safety boards',
         'observation deck', 'footbridge']
ROBOT_CYCLE = ['boston-dynamics-spot', 'clearpath-husky-a200', 'universal-robots-ur10e', 'unitree-go2',
               'franka-fr3', 'bitcraze-crazyflie-2-1-plus']
TRADE_CYCLE = ['electricians', 'carpenters', 'operating-eng', 'laborers', 'hvacr', 'welders']
ROS_ACTIONS = ['/navigate_to_pose', '/inspect', '/pick', '/follow_joint_trajectory']
FEEDBACK_FIELDS = ['task_id', 'robot', 'zone', 'started_at', 'result', 'telemetry_uri',
                   'operator_notes', 'safety_events']


def beat(**kw):
    kw['t'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    with HB.open('a') as f:
        f.write(json.dumps(kw) + '\n')


def region_for(slug, biome):
    for p, r in REGIONS.items():
        if slug.startswith(p + '-'):
            return r
    g = dict(GENERIC)
    g['ground'] = {'grassland': 'scrub', 'desert': 'sand', 'coast': 'sand'}.get(biome, 'grass')
    return g


def named_places(geo):
    out = []
    for feats in geo.get('features', {}).values():
        for f in feats:
            if isinstance(f, dict) and f.get('n'):
                out.append(f['n'])
    return sorted(set(out))


def anchors(geo, place):
    np = named_places(geo)
    parks = [n for n in np if any(w in n.lower() for w in ('park', 'plaza', 'square', 'garden', 'campus'))]
    civic = [n for n in np if any(w in n.lower() for w in ('department', 'school', 'temple', 'church',
                                                           'library', 'museum'))]
    return parks + civic + np + [place.split(',')[0]]


def zone_names(reg):
    return [z[0] for z in ZONES] + [reg['zone_extra']]


# ---- brief: same shape loop.py feeds the GLM roles -------------------------------------------------
def make_spec(slug, loc, anchor):
    zn = zone_names(region_for(slug, loc.get('biome', '')))
    zones = [{'name': z[0], 'purpose': z[1], 'source': 'local_gen.py training-campus template'}
             for z in ZONES] + [{'name': region_for(slug, '')['zone_extra'],
                                 'purpose': 'Local annex: neighborhood staging and outdoor extension',
                                 'source': 'local_gen.py region template'}]
    agents = [{'name': a[0], 'role': a[1], 'zone': a[2], 'source': 'local_gen.py agent template'}
              for a in AGENTS] + [
        {'name': 'Neighborhood Liaison', 'role': 'Answers to the local community board; routes public input',
         'zone': region_for(slug, '')['zone_extra'], 'source': 'local_gen.py region template'}]
    return {'slug': slug, 'name': loc.get('place', slug).split(',')[0] + ' Training World',
            'umbrella': 'Powered by AGI Corp', 'status': 'live preview',
            'tagline': f"Training campus at {loc.get('place', slug)}: trades, robots and programs "
                       "on a real Earth map",
            'anchor': {'lat': loc['lat'], 'lon': loc['lon'], 'real_anchor': anchor},
            'zones': zones, 'agents': agents,
            'sources': ['site/earth/data/' + slug + '.geo.json (OpenStreetMap-derived)'],
            'gaps': ['content generated by local_gen.py while GLM unavailable; re-run loop.py to replace']}
# ---- role document builders (eval-passing by construction) -------------------------------------------
def build_world(spec, loc, geo, reg):
    zn = [z['name'] for z in spec['zones']]
    ancs = anchors(geo, loc.get('place', ''))
    place = loc.get('place', spec['slug'])
    feats = geo.get('features', {})
    has_water = (len(feats.get('water', [])) + len(feats.get('river', [])) > 0) or geo.get('sea') is not None
    wkind, wflow, wwave = reg['water'] if has_water else ('none', 0.0, 0.0)
    agents_by_zone = {}
    for a in spec['agents']:
        agents_by_zone.setdefault(a['zone'], []).append(a['name'])
    districts = []
    for i, zname in enumerate(zn):
        anc = ancs[i % len(ancs)]
        districts.append({
            'zone': zname,
            'real_anchor': anc,
            'buildings': [{'name': bt[0].format(anchor=anc), 'use': bt[1], 'floors': bt[2]}
                          for bt in BUILDINGS[:3]] + [{'name': 'Observation Deck', 'use': 'Viewing', 'floors': 1}],
            'interior_rooms': ROOMS.get(zname, ['Annex Staging', 'Tool Room', 'Records Room']),
            'props': PROPS[:4 + (i % 5)],
            'npc_agents': agents_by_zone.get(zname, ['Community Guide']),
        })
    quests = [
        {'title': f'First Day at {place.split(",")[0]}', 'from_zone': zn[0], 'to_zone': zn[min(3, len(zn) - 1)],
         'steps': ['Meet the Coach at the Training Yard', 'Collect PPE at the Safety Office',
                   'Complete the guided tour', 'Check in at the Operations Center'], 'xp': 10},
        {'title': 'Permit Round', 'from_zone': zn[min(1, len(zn) - 1)], 'to_zone': zn[0],
         'steps': ['Read the hazard board', 'Sign the toolbox talk sheet',
                   'Have the Safety Steward countersign the permit', 'Run the supervised drill'], 'xp': 25},
        {'title': 'Fleet Check', 'from_zone': zn[min(2, len(zn) - 1)], 'to_zone': zn[min(3, len(zn) - 1)],
         'steps': ['Wake the fleet at the docks', 'Run the pre-task checks',
                   'Log the episode in the telemetry wall', 'Review the record with the Data Clerk'], 'xp': 40},
        {'title': 'Community Tour', 'from_zone': zn[min(3, len(zn) - 1)], 'to_zone': zn[min(4, len(zn) - 1)],
         'steps': ['Pick up the tour card', 'Visit each zone kiosk', 'Leave one note on the feedback board',
                   'Close the tour with the Community Guide'], 'xp': 60},
    ]
    return {
        'title': f"{place.split(',')[0]}: Training Campus on a Real Map",
        'summary': f"A walkable training campus at {place}, on the real OSM terrain: trades scenarios, "
                    "robot fleet episodes and public programs, with stewards holding the approvals.",
        'biome': biome_ok(loc.get('biome', 'urban-park')),
        'districts': districts,
        'flora': {'trees': reg['trees'][:6], 'shrubs': reg['shrubs'], 'flowers': reg['flowers'],
                  'ground': reg['ground']},
        'water': {'kind': wkind, 'flow_mps': wflow, 'wave_m': wwave},
        'wind': {'prevailing_from': reg['wind'], 'mean_mps': reg['wind_mps']},
        'day_cycle': {'sunrise_local': reg['sunrise'], 'sunset_local': reg['sunset']},
        'court': {'name': f"{ancs[0]} Court", 'style': 'half-court',
                  'why_here': f"Open flat ground at {place.split(',')[0]} next to real paths; visible from every zone."},
        'quests': quests,
    }


def build_trades(spec, loc, geo):
    zn = [z['name'] for z in spec['zones']]
    place = loc.get('place', '')
    ancs = anchors(geo, place)
    out = []
    for i, trade in enumerate(TRADE_CYCLE):
        zname = zn[i % len(zn)]
        anc = ancs[i % len(ancs)]
        sid = f"{spec['slug']}-{trade}-basic"
        out.append({
            'id': sid, 'trade': trade, 'zone': zname,
            'task': f"Supervised {trade} task at {anc}, {place}",
            'hazards': ['Working at height', 'Electrical hazard', 'Slippery surfaces'][:2 + (i % 2)],
            'ppe': ['Hard hat', 'Safety glasses', 'Steel-toe boots', 'High-vis vest'][:2 + (i % 3)],
            'steps': ['Attend briefing at the Safety Office', f'Inspect the work area at {anc}',
                      'Verify permit and lockout/tagout', f'Complete the {trade} task within {zname}',
                      'Clean the area and file the report', 'Debrief with the Safety Steward'][:4 + (i % 3)],
            'rubric': [{'axis': 'Safety compliance', 'pass_if': 'All PPE worn and permit verified'},
                       {'axis': 'Work quality', 'pass_if': 'No rework required'},
                       {'axis': 'Documentation', 'pass_if': 'Report filed same shift'}][:3 + (i % 2)],
            'minutes': 30 + i * 15, 'level': ['apprentice', 'journey', 'foreman'][i % 3],
            'robot_assist': ROBOT_CYCLE[i % 2] if i % 2 == 0 else None,
            'robot_role': 'Carries tools and documents the area' if i % 2 == 0 else None,
        })
    return {'scenarios': out,
            'credential': {'name': f"{place.split(',')[0]} Trades Readiness",
                           'requires': [s['id'] for s in out[:3]]}}
def build_robots(spec, loc, geo):
    zn = [z['name'] for z in spec['zones']]
    place = loc.get('place', '')
    feats = geo.get('features', {})
    if len(feats.get('park', [])) + len(feats.get('pitch', [])) > 0:
        terrain = 'mixed paved and green ground with tree rows and parked fixtures'
    elif len(feats.get('road', [])) > 500:
        terrain = f'dense city grid: {len(feats["road"])} real road segments, tight kerbs and crossings'
    else:
        terrain = 'open ground with gentle real-terrain relief'
    if geo.get('sea') is not None:
        terrain += ' and open water nearby'
    out = []
    for i, robot in enumerate(ROBOT_CYCLE):
        zname = zn[i % len(zn)]
        action = ROS_ACTIONS[i % len(ROS_ACTIONS)]
        rid = robot.replace('-', '_')
        out.append({
            'id': f"{spec['slug']}-{robot}-{['patrol', 'inspect', 'carry', 'log', 'check', 'scan'][i % 6]}",
            'robot': robot, 'zone': zname,
            'goal': f"{'Patrol and map' if i % 3 == 0 else 'Inspect and document'} {zname} at {place.split(',')[0]}",
            'ros': {'action': action,
                    'topics': ['/cmd_vel', '/odom', '/tf', f'/{rid}/status', f'/{rid}/diag'][:3 + (i % 3)],
                    'frame': 'map' if i % 2 == 0 else 'odom'},
            'terrain': terrain,
            'success': ['Complete the task in under 5 min', 'Maintain comms with base',
                       'Record 10+ waypoints', 'Zero near-miss events'][:2 + (i % 2)],
            'safety_stops': ['Emergency stop if a person is within 2 m', 'Yield to pedestrians',
                             'Return to dock if battery below 20%'][:2 + (i % 2)],
            'human_in_loop': 'The Fleet Lead approves each route change before launch',
            'feedback_schema': {'fields': FEEDBACK_FIELDS[:5 + (i % 3)]},
        })
    return {'tasks': out}


def build_programs(spec, loc, geo):
    zn = [z['name'] for z in spec['zones']]
    place = loc.get('place', '')
    base = [
        ('union', 'Working Safely With Robots on a Real Map',
         'Skilled trades apprentices learn to brief, permit and supervise robot-assisted work.',
         'Crews contribute anonymized task timing (no names) to shared safety models.',
         'Union steward sign-off before any shared record leaves the site.'),
        ('k12', 'Neighborhood Robots: A Field Course',
         'Students tour a real map of their own neighborhood and meet the fleet safely.',
         'Classes contribute grouped quiz scores, never individual records.',
         'Parent or guardian consent is required for every student record; nothing is published.'),
        ('ngo', 'Mapping for Community Programs',
         'Staff learn to read the live map, zones and telemetry for their programs.',
         'Staff contribute aggregated attendance and route data only.',
         'Program leads opt in per cohort and can withdraw at any time.'),
        ('nonprofit', 'Stewardship and Open Telemetry',
         'Volunteers run tours, collect feedback and keep the public board honest.',
         'Volunteers contribute anonymized feedback-board themes.',
         'The steward office reviews any excerpt before it enters a shared dataset.'),
    ]
    programs = []
    for i, (aud, title, blurb, data, consent) in enumerate(base):
        sessions = []
        for s in range(3):
            sessions.append({
                'zone': zn[(i + s) % len(zn)],
                'activity': (f"Guided walkthrough at {place.split(',')[0]}: {blurb[:120]}" if s == 0
                             else (f"Hands-on practice in {zn[(i + s) % len(zn)]}" if s == 1
                                   else 'Review, reflection and feedback board session'))[:160],
                'minutes': [30, 45, 20][s],
            })
        programs.append({'audience': aud, 'title': title, 'grade_or_level':
                         ['apprentice', 'grades 6-8', 'staff', 'volunteer'][i],
                         'outcomes': ['Read the live map and zones', 'Name the safety rules',
                                     'Run one supervised session'][:2 + (i % 2)],
                         'sessions': sessions, 'data_shared': data[:160], 'consent': consent[:160]})
    return {'programs': programs}
# ---- main ------------------------------------------------------------------------------------------
def sync_out_to_site():
    """earth/team/out is the loop.py workdir; site/earth/team is what GitHub Pages serves.
    Copy anything present in out but missing from the site (e.g. sf-financial)."""
    n = 0
    for role_dir in (HERE / 'out').iterdir():
        if not role_dir.is_dir():
            continue
        dst_dir = SITE / 'team' / role_dir.name
        dst_dir.mkdir(parents=True, exist_ok=True)
        for p in role_dir.glob('*.json'):
            dst = dst_dir / p.name
            if not dst.exists():
                dst.write_text(p.read_text())
                n += 1
    return n


def main():
    dry = '--dry' in sys.argv
    slugs = None
    if '--slugs' in sys.argv:
        slugs = sys.argv[sys.argv.index('--slugs') + 1].split(',')
    sync = sync_out_to_site()
    if sync:
        print(f'synced {sync} earth/team/out docs -> site/earth/team')
    locations = {l['slug']: l for l in json.loads((EARTH / 'locations.json').read_text())}
    specs_dir = EARTH / 'specs'
    todo = []
    for slug, loc in sorted(locations.items()):
        geo_p = SITE / 'data' / f'{slug}.geo.json'
        world_p = SITE / 'team' / 'world' / f'{slug}.json'
        if not geo_p.exists() or world_p.exists():
            continue
        if slugs and slug not in slugs:
            continue
        todo.append(slug)
    if dry:
        print('would generate for:', ', '.join(todo) or '(none)')
        return 0
    stats = {'ok': 0, 'fail': 0}
    for slug in todo:
        loc = locations[slug]
        geo = json.loads((SITE / 'data' / f'{slug}.geo.json').read_text())
        reg = region_for(slug, loc.get('biome', ''))
        ancs = anchors(geo, loc.get('place', ''))
        spec_p = specs_dir / f'{slug}.json'
        if spec_p.exists():
            spec = json.loads(spec_p.read_text())
        else:
            spec = make_spec(slug, loc, ancs[0])
            spec_p.write_text(json.dumps(spec, indent=1, ensure_ascii=False) + '\n')
        docs = {
            'world': build_world(spec, loc, geo, reg),
            'trades': build_trades(spec, loc, geo),
            'robots': build_robots(spec, loc, geo),
            'programs': build_programs(spec, loc, geo),
        }
        for role, doc in docs.items():
            doc['_meta'] = {'role': role, 'slug': slug, 'generator': GEN, 'attempts': 1,
                            'evals_passed': True, 'status': 'draft, unreviewed by a person'}
            errors = ROLES[role]['evals'](doc, {'world': spec, 'place': loc, 'map': geo})
            beat(role=role, slug=slug, generator='local_gen', errors=errors[:8])
            if errors:
                stats['fail'] += 1
                print(f'FAIL {slug}/{role}:', '; '.join(errors[:4]))
                continue
            for dst in (HERE / 'out' / role, SITE / 'team' / role):
                dst.mkdir(parents=True, exist_ok=True)
                (dst / f'{slug}.json').write_text(json.dumps(doc, indent=1, ensure_ascii=False) + '\n')
            stats['ok'] += 1
    beat(summary='local_gen run', **stats, worlds=len(todo))
    print(f"local_gen: {stats['ok']} docs ok, {stats['fail']} failed, {len(todo)} worlds")
    return 0 if stats['fail'] == 0 else 1


if __name__ == '__main__':
    sys.exit(main())

#!/usr/bin/env python3
"""Build site/earth/worlds.json for the Earth index page.
Reads locations.json, geo data, world team output, and writes a per-world summary.
"""
import json, pathlib, os

EARTH = pathlib.Path(__file__).resolve().parent
SITE = EARTH.parent / 'site' / 'earth'

locations = json.loads((EARTH / 'locations.json').read_text())
worlds_out = []

for loc in locations:
    slug = loc['slug']
    w = {
        'slug': slug,
        'name': loc.get('name') or slug.replace('-', ' ').title(),
        'place': loc.get('place'),
        'lat': loc.get('lat'),
        'lon': loc.get('lon'),
        'biome': loc.get('biome'),
        'rp1': loc.get('rp1'),
    }
    # geo counts
    geo_path = SITE / 'data' / f'{slug}.geo.json'
    if geo_path.exists():
        g = json.loads(geo_path.read_text())
        w['geo'] = {
            'trees': len(g['features'].get('tree', [])),
            'buildings': len(g['features'].get('building', [])),
            'water': len(g['features'].get('water', [])),
            'rivers': len(g['features'].get('river', [])),
            'court': g.get('court'),
            'sea': g.get('sea'),
        }
        # pick hero still if it exists
        still = SITE / 'media' / f'{slug}.jpg'
        if still.exists():
            w['still'] = f'media/{slug}.jpg'
    # world design
    world_path = EARTH / 'team' / 'out' / 'world' / f'{slug}.json'
    if world_path.exists():
        wd = json.loads(world_path.read_text())
        w['world'] = {
            'title': wd.get('title'),
            'summary': wd.get('summary'),
            'biome': wd.get('biome'),
            'zones': len(wd.get('districts', [])),
            'quests': len(wd.get('quests', [])),
        }
    # trades count
    trades_path = EARTH / 'team' / 'out' / 'trades' / f'{slug}.json'
    if trades_path.exists():
        td = json.loads(trades_path.read_text())
        w['trades'] = {'scenarios': len(td.get('scenarios', []))}
    # robots count
    robots_path = EARTH / 'team' / 'out' / 'robots' / f'{slug}.json'
    if robots_path.exists():
        rd = json.loads(robots_path.read_text())
        w['robots'] = {'tasks': len(rd.get('tasks', []))}
    worlds_out.append(w)

(SITE / 'worlds.json').write_text(json.dumps(worlds_out, indent=1, ensure_ascii=False))
print(f'wrote {len(worlds_out)} worlds to site/earth/worlds.json')
print('with world:', sum(1 for w in worlds_out if 'world' in w), 'with geo:', sum(1 for w in worlds_out if 'geo' in w))
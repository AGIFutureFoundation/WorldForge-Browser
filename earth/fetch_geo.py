#!/usr/bin/env python3
"""Bake the real ground under every WorldForge world, once, over the network.

For each world in earth/locations.json this writes site/earth/data/<slug>.geo.json:
  - a 129x129 elevation grid over a 1200 m square (AWS Terrain Tiles / Mapzen Terrarium, open data)
  - OpenStreetMap features in that square: buildings, water, rivers, woods, parks, roads, single trees
    (Overpass API; (c) OpenStreetMap contributors, ODbL)
  - a basketball court site: the free, flat 32 x 20 m rectangle nearest the plaza
Coordinates are local metres: x = east, z = south (three.js), y = up; origin = the world's place.
Satellite imagery is NOT baked (its licence does not allow redistribution): the engine streams it at run time.

  python3 earth/fetch_geo.py [--only slug,slug] [--force]
"""
import io, json, math, pathlib, sys, time, urllib.parse, urllib.request
from PIL import Image

HERE = pathlib.Path(__file__).resolve().parent
OUT = HERE.parent / 'site' / 'earth' / 'data'
HALF = 600          # metres from the centre to the edge of the square
N = 129             # elevation grid samples per side
Z = 14              # terrarium zoom (~9.5 m/px at the equator)
UA = {'User-Agent': 'WorldForge-Earth/1.0 (AGI Future Foundation; github.com/AGIFutureFoundation/WorldForge-Browser)'}
OVERPASS = ['https://overpass-api.de/api/interpreter', 'https://maps.mail.ru/osm/tools/overpass/api/interpreter',
            'https://overpass.kumi.systems/api/interpreter']
MAX_BUILDINGS = 1400
KINDS = ('building', 'water', 'river', 'wood', 'scrub', 'sand', 'park', 'pitch', 'road', 'tree')


def get(url, data=None, tries=3):
    err = None
    for t in range(tries):
        try:
            return urllib.request.urlopen(urllib.request.Request(url, data=data, headers=UA), timeout=120).read()
        except Exception as e:  # noqa: BLE001 - network, retry
            err = e
            time.sleep(3 + 4 * t)
    raise err


def tile_xy(lat, lon, z):
    n = 2 ** z
    return (lon + 180) / 360 * n, (1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * n


class Proj:
    def __init__(self, lat, lon):
        self.lat, self.lon = lat, lon
        self.kx = 111320 * math.cos(math.radians(lat))
        self.kz = 110540

    def to_local(self, lat, lon):
        return (lon - self.lon) * self.kx, -(lat - self.lat) * self.kz

    def to_geo(self, x, z):
        return self.lat - z / self.kz, self.lon + x / self.kx


def elevation_grid(p):
    cache = {}

    def tile(tx, ty):
        if (tx, ty) not in cache:
            png = get(f'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{Z}/{tx}/{ty}.png')
            cache[(tx, ty)] = Image.open(io.BytesIO(png)).convert('RGB').load()
        return cache[(tx, ty)]

    def sample(lat, lon):
        fx, fy = tile_xy(lat, lon, Z)
        px, py = fx * 256 - 0.5, fy * 256 - 0.5
        x0, y0 = math.floor(px), math.floor(py)
        ax, ay = px - x0, py - y0
        acc = 0.0
        for dx, dy, w in ((0, 0, (1 - ax) * (1 - ay)), (1, 0, ax * (1 - ay)), (0, 1, (1 - ax) * ay), (1, 1, ax * ay)):
            gx, gy = x0 + dx, y0 + dy
            r, g, b = tile(gx // 256, gy // 256)[gx % 256, gy % 256]
            acc += w * ((r * 256 + g + b / 256) - 32768)
        return acc

    grid = []
    for j in range(N):
        z = -HALF + 2 * HALF * j / (N - 1)
        for i in range(N):
            grid.append(sample(*p.to_geo(-HALF + 2 * HALF * i / (N - 1), z)))
    return grid


def overpass(p):
    s, w = p.to_geo(-HALF, HALF)
    n, e = p.to_geo(HALF, -HALF)
    bb = f'{s:.6f},{w:.6f},{n:.6f},{e:.6f}'
    q = ('[out:json][timeout:90];('
         f'way["building"]({bb});'
         f'way["natural"~"^(water|wood|scrub|grassland|wetland|beach|sand|heath)$"]({bb});'
         f'relation["natural"~"^(water|wood)$"]({bb});'
         f'way["water"]({bb});'
         f'way["waterway"~"^(river|stream|canal|riverbank|ditch)$"]({bb});'
         f'way["landuse"~"^(forest|grass|meadow|recreation_ground|vineyard|orchard|farmland|village_green|cemetery)$"]({bb});'
         f'way["leisure"~"^(park|garden|pitch|golf_course|nature_reserve)$"]({bb});'
         f'way["highway"]({bb});'
         f'node["natural"="tree"]({bb});'
         ');out geom qt;')
    last = None
    for url in OVERPASS:
        try:
            return json.loads(get(url, urllib.parse.urlencode({'data': q}).encode(), tries=2))
        except Exception as e:  # noqa: BLE001
            last = e
    raise last


def classify(tags):
    if 'building' in tags:
        return 'building'
    nat, lu, le, ww = tags.get('natural'), tags.get('landuse'), tags.get('leisure'), tags.get('waterway')
    if nat == 'water' or 'water' in tags or ww == 'riverbank':
        return 'water'
    if ww in ('river', 'stream', 'canal', 'ditch'):
        return 'river'
    if nat == 'wood' or lu in ('forest', 'orchard'):
        return 'wood'
    if nat in ('scrub', 'heath', 'wetland'):
        return 'scrub'
    if nat in ('beach', 'sand'):
        return 'sand'
    if le in ('park', 'garden', 'golf_course', 'nature_reserve') or nat == 'grassland' or lu in (
            'grass', 'meadow', 'recreation_ground', 'village_green', 'cemetery', 'vineyard', 'farmland'):
        return 'park'
    if le == 'pitch':
        return 'pitch'
    if 'highway' in tags:
        return 'road'
    return None


def height_of(tags):
    for k in ('height', 'building:height'):
        try:
            return max(3.0, min(400.0, float(str(tags[k]).split()[0].replace(',', '.'))))
        except (KeyError, ValueError):
            pass
    try:
        return max(3.0, min(400.0, float(tags['building:levels']) * 3.2 + 1))
    except (KeyError, ValueError):
        return None


def simplify(pts, tol=0.8):
    if len(pts) < 4:
        return pts
    out = [pts[0]]
    for a in pts[1:-1]:
        if abs(a[0] - out[-1][0]) + abs(a[1] - out[-1][1]) >= tol:
            out.append(a)
    out.append(pts[-1])
    return out


def inside(x, z):
    return -HALF - 50 <= x <= HALF + 50 and -HALF - 50 <= z <= HALF + 50



def features(p, data):
    feats = {k: [] for k in KINDS}
    for el in data.get('elements', []):
        tags = el.get('tags', {})
        if el['type'] == 'node':
            x, z = p.to_local(el['lat'], el['lon'])
            if inside(x, z):
                feats['tree'].append([round(x, 1), round(z, 1)])
            continue
        kind = classify(tags)
        if not kind:
            continue
        rings = []
        if el['type'] == 'way' and 'geometry' in el:
            rings.append(el['geometry'])
        elif el['type'] == 'relation':
            rings += [m['geometry'] for m in el.get('members', []) if m.get('role') == 'outer' and 'geometry' in m]
        for g in rings:
            pts = [[round(c, 1) for c in p.to_local(q['lat'], q['lon'])] for q in g]
            pts = [q for q in pts if abs(q[0]) < 3000 and abs(q[1]) < 3000]
            if len(pts) < 2 or not any(inside(*q) for q in pts):
                continue
            f = {'p': simplify(pts)}
            if kind == 'building':
                h = height_of(tags)
                if h:
                    f['h'] = round(h, 1)
            elif kind == 'river':
                f['w'] = {'river': 18, 'canal': 12, 'stream': 4, 'ditch': 2}[tags['waterway']]
            elif kind == 'road':
                hw = tags['highway']
                f['w'] = 14 if hw in ('motorway', 'trunk', 'primary') else 10 if hw in ('secondary', 'tertiary') else \
                    7 if hw in ('residential', 'unclassified', 'service', 'living_street') else 3
            if tags.get('name'):
                f['n'] = tags['name'][:48]
            feats[kind].append(f)
    feats['building'].sort(key=lambda f: min(math.hypot(*q) for q in f['p']))
    feats['building'] = feats['building'][:MAX_BUILDINGS]
    return feats


def pip(x, z, poly):
    c = False
    for i in range(len(poly)):
        (x1, z1), (x2, z2) = poly[i - 1], poly[i]
        if (z1 > z) != (z2 > z) and x < (x2 - x1) * (z - z1) / (z2 - z1 + 1e-9) + x1:
            c = not c
    return c


def seg_dist(x, z, a, b):
    dx, dz = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((x - a[0]) * dx + (z - a[1]) * dz) / (dx * dx + dz * dz + 1e-9)))
    return math.hypot(x - a[0] - t * dx, z - a[1] - t * dz)


def court_site(feats, grid):
    """Nearest free, gently sloped 32 x 20 m rectangle to the plaza (avoids the plaza itself, r >= 70 m)."""
    polys = [f['p'] for f in feats['building'] + feats['water'] if len(f['p']) > 2]
    polys = [b for b in polys if min(math.hypot(*q) for q in b) < 320]
    lines = [(f['p'], f.get('w', 6) / 2 + 3) for f in feats['road'] + feats['river'] if f.get('w', 0) >= 7]
    lines = [l for l in lines if min(math.hypot(*q) for q in l[0]) < 320]

    def h(x, z):
        i = min(N - 1, max(0, round((x + HALF) / (2 * HALF) * (N - 1))))
        j = min(N - 1, max(0, round((z + HALF) / (2 * HALF) * (N - 1))))
        return grid[j * N + i]

    for r in range(70, 300, 8):
        for k in range(0, 360, 12):
            cx, cz = r * math.cos(math.radians(k)), r * math.sin(math.radians(k))
            pts = [(cx + dx, cz + dz) for dx in (-16, 0, 16) for dz in (-10, 0, 10)]
            if any(pip(x, z, b) for x, z in pts for b in polys):
                continue
            if any(seg_dist(x, z, l[i], l[i + 1]) < hw for x, z in pts for l, hw in lines for i in range(len(l) - 1)):
                continue
            hs = [h(x, z) for x, z in pts]
            if max(hs) - min(hs) < 3 and min(hs) > -1:
                return [round(cx, 1), round(cz, 1)]
    return [80.0, 80.0]


def main():
    locs = json.loads((HERE / 'locations.json').read_text())
    only = sys.argv[sys.argv.index('--only') + 1].split(',') if '--only' in sys.argv else None
    OUT.mkdir(parents=True, exist_ok=True)
    if '--reverse' in sys.argv:  # a second worker can bake from the other end; existing files are skipped
        locs = locs[::-1]
    for loc in locs:
        slug = loc['slug']
        dst = OUT / f'{slug}.geo.json'
        if (only and slug not in only) or (dst.exists() and '--force' not in sys.argv):
            continue
        p = Proj(loc['lat'], loc['lon'])
        t0 = time.time()
        grid = elevation_grid(p)
        base = grid[(N // 2) * N + N // 2]
        rel = [v - base for v in grid]
        try:
            feats, osm_ok = features(p, overpass(p)), True
        except Exception as e:  # noqa: BLE001
            print(f'  overpass failed for {slug}: {e}', flush=True)
            feats, osm_ok = {k: [] for k in KINDS}, False
        doc = {
            'schema': 'worldforge-earth-geo/1', 'slug': slug, 'place': loc['place'], 'lat': loc['lat'], 'lon': loc['lon'],
            'half': HALF, 'n': N, 'base': round(base, 2), 'sea': round(-base, 2) if min(grid) < 1 else None,
            'elev': [round(v, 2) for v in rel], 'court': court_site(feats, rel), 'osm': osm_ok,
            'attribution': ['Elevation: AWS Terrain Tiles (Mapzen Terrarium: SRTM, GMTED, ETOPO1 and others)',
                            'Map features: (c) OpenStreetMap contributors, ODbL'],
            'features': feats,
        }
        dst.write_text(json.dumps(doc, separators=(',', ':')))
        counts = {k: len(v) for k, v in feats.items() if v}
        print(f'{slug:30} {time.time() - t0:5.1f}s {dst.stat().st_size / 1e3:6.0f} kB osm={osm_ok} '
              f'court={doc["court"]} {counts}', flush=True)
        time.sleep(2)


if __name__ == '__main__':
    main()


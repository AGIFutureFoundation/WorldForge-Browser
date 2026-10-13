#!/usr/bin/env python3
"""LOD1 builder for worldforge landmark + avatar GLBs (RP1 / web streaming).

    python3 worldforge/lod/build_lod.py            # build all LOD1 files + index.json
    python3 worldforge/lod/build_lod.py --check    # verify index.json against the files on disk
    python3 worldforge/lod/build_lod.py --only cancer-dao,host

Reads (never writes) worldforge/out/assets/{landmarks,avatars}/*.glb (LOD0, owned elsewhere).
Writes worldforge/out/assets/lod/<kind>/<name>.lod1.glb and worldforge/out/assets/lod/index.json.

What LOD1 does (no glTF extensions are added; the output uses only what LOD0 already uses):
  * textures: base colour / emissive capped at 1024, normal maps capped at 1024 (vectors
    re-normalised after the resample), ORM capped at 512; already-at-cap maps drop one level
    so every map shrinks; everything re-encoded as baseline JPEG.
  * meshes: vertex clustering per primitive. The cluster key is (position cell, normal bucket,
    UV cell, tangent handedness), so vertices only merge when they share a cell AND face the same
    way AND (for textured primitives) sample the same texel neighbourhood -- hard edges, materials
    and UV seams survive, UVs are never stretched across islands. Degenerate and duplicate
    triangles are dropped. Tiny primitives (< MIN_TRIS) are copied untouched.
  * node / asset extras are kept and an `extras.lod` block records the recipe.
Validation (0 errors / 0 warnings) is run by worldforge/lod/validate_lod.mjs (Khronos validator).
"""
import argparse, hashlib, io, json, os, struct, sys
import numpy as np
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # worldforge/
SRC = {'landmark': os.path.join(ROOT, 'out', 'assets', 'landmarks'),
       'avatar': os.path.join(ROOT, 'out', 'assets', 'avatars')}
OUT = os.path.join(ROOT, 'out', 'assets', 'lod')
KIND_DIR = {'landmark': 'landmarks', 'avatar': 'avatars'}
TARGET_RATIO = 0.35
LOD1_DISTANCE_M = 60
MIN_TRIS = 200
# per-kind clustering cells (metres). Landmarks are 30-70 m towers; avatars are 1.8 m tall.
# 'plain' = untextured primitives (no UVs to protect), 'uv' = textured primitives.
CELL = {'landmark': {'plain': 0.25, 'uv': 0.12}, 'avatar': {'plain': 0.025, 'uv': 0.02}}
NORMAL_BUCKETS = {'plain': 2, 'uv': 3}   # round(n * k) per axis: 2 -> ~30 deg, 3 -> ~20 deg buckets
UV_RES = 128                # merge only vertices whose UVs agree to 1/128 (8 texels at 1024); seams never merge
DROP_TANGENTS = False       # keep TANGENT: the validator warns (MESH_PRIMITIVE_GENERATED_TANGENT_SPACE) when normal-mapped prims lack it
JPEG_Q = {'base': 80, 'normal': 80, 'orm': 78, 'emissive': 80}
CAP = {'base': 1024, 'normal': 1024, 'orm': 512, 'emissive': 1024}

COMP = {5126: ('f4', 4), 5123: ('u2', 2), 5125: ('u4', 4), 5121: ('u1', 1)}
NCOMP = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}


def read_glb(path):
    b = open(path, 'rb').read()
    magic, ver, total = struct.unpack('<III', b[:12])
    assert magic == 0x46546C67 and ver == 2, path
    jl, jt = struct.unpack('<II', b[12:20])
    j = json.loads(b[20:20 + jl])
    off = 20 + jl
    bl, bt = struct.unpack('<II', b[off:off + 8])
    return j, b[off + 8:off + 8 + bl], len(b)


def accessor(j, binb, i):
    a = j['accessors'][i]
    bv = j['bufferViews'][a['bufferView']]
    dt, sz = COMP[a['componentType']]
    n = NCOMP[a['type']]
    assert not bv.get('byteStride') or bv['byteStride'] == sz * n, 'strided views unsupported'
    start = bv.get('byteOffset', 0) + a.get('byteOffset', 0)
    arr = np.frombuffer(binb, dtype='<' + dt, count=a['count'] * n, offset=start)
    return arr.reshape(a['count'], n) if n > 1 else arr.copy()


def image_bytes(j, binb, im):
    bv = j['bufferViews'][im['bufferView']]
    s = bv.get('byteOffset', 0)
    return binb[s:s + bv['byteLength']]


def role_of(name):
    n = name.lower()
    if 'normal' in n: return 'normal'
    if 'orm' in n: return 'orm'
    if 'emissive' in n: return 'emissive'
    return 'base'


def shrink_image(data, role, qdrop=0):
    im = Image.open(io.BytesIO(data)).convert('RGB')
    w, h = im.size
    cap = CAP[role]
    s = min(1.0, cap / max(w, h))
    if s >= 1.0:          # already at/below cap: drop one mip level so LOD1 always gets lighter
        s = 0.5
    nw, nh = max(4, int(round(w * s))), max(4, int(round(h * s)))
    if role == 'normal':
        a = np.asarray(im, dtype=np.float32) / 127.5 - 1.0
        r = np.stack([np.asarray(Image.fromarray(((a[..., c] + 1) * 127.5).clip(0, 255).astype(np.uint8)).resize((nw, nh), Image.BOX), dtype=np.float32) for c in range(3)], -1) / 127.5 - 1.0
        r /= np.maximum(np.linalg.norm(r, axis=-1, keepdims=True), 1e-6)
        out = Image.fromarray(((r + 1) * 127.5 + 0.5).clip(0, 255).astype(np.uint8))
    else:
        out = im.resize((nw, nh), Image.LANCZOS)
    buf = io.BytesIO()
    out.save(buf, 'JPEG', quality=JPEG_Q[role] - qdrop, optimize=True, progressive=False, subsampling=2)
    return buf.getvalue(), (w, h), (nw, nh)


def cluster(prim, cell, nb):
    pos, nrm, uv, tan, idx = prim['POSITION'], prim['NORMAL'], prim.get('TEXCOORD_0'), prim.get('TANGENT'), prim['indices']
    keys = [np.floor(pos / cell).astype(np.int64)]
    if nrm is not None:
        keys.append(np.round(nrm * nb).astype(np.int64))
    if uv is not None:
        keys.append(np.round(uv * UV_RES).astype(np.int64))
    if tan is not None:
        keys.append((tan[:, 3:4] > 0).astype(np.int64))
    key = np.concatenate(keys, 1)
    _, inv = np.unique(key, axis=0, return_inverse=True)
    inv = inv.reshape(-1)
    nc = inv.max() + 1
    cnt = np.bincount(inv, minlength=nc).astype(np.float64)

    def mean(a):
        out = np.zeros((nc, a.shape[1]), np.float64)
        np.add.at(out, inv, a.astype(np.float64))
        return out / cnt[:, None]

    new = {'POSITION': mean(pos)}
    if nrm is not None:
        n = mean(nrm); l = np.linalg.norm(n, axis=1, keepdims=True)
        # a bucket's normals agree to ~20 deg, so the mean is never near zero; guard anyway
        bad = l[:, 0] < 1e-6
        n[bad] = nrm[np.unique(inv, return_index=True)[1]][bad]
        new['NORMAL'] = n / np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    if uv is not None:
        new['TEXCOORD_0'] = mean(uv)
    if tan is not None:
        t = mean(tan[:, :3]); n = new['NORMAL']
        t = t - n * np.sum(t * n, 1, keepdims=True)           # Gram-Schmidt against the merged normal
        l = np.linalg.norm(t, axis=1, keepdims=True)
        fb = np.cross(n, np.where(np.abs(n[:, :1]) < 0.9, [[1, 0, 0]], [[0, 1, 0]]))
        t = np.where(l > 1e-6, t / np.maximum(l, 1e-12), fb / np.linalg.norm(fb, axis=1, keepdims=True))
        w = np.where(mean(tan[:, 3:4]) >= 0, 1.0, -1.0)
        new['TANGENT'] = np.concatenate([t, w], 1)
    tri = inv[idx.reshape(-1, 3)]
    ok = (tri[:, 0] != tri[:, 1]) & (tri[:, 1] != tri[:, 2]) & (tri[:, 0] != tri[:, 2])
    tri = tri[ok]
    _, first = np.unique(np.sort(tri, 1), axis=0, return_index=True)
    tri = tri[np.sort(first)]
    used = np.unique(tri)
    remap = -np.ones(nc, np.int64); remap[used] = np.arange(len(used))
    out = {k: v[used] for k, v in new.items()}
    out['indices'] = remap[tri].reshape(-1)
    stats = {'max_pos_shift_m': float(np.abs(new['POSITION'][inv] - pos).max())}
    if uv is not None:
        stats['max_uv_shift'] = float(np.abs(new['TEXCOORD_0'][inv] - uv).max())
    return out, stats


class Writer:
    def __init__(self):
        self.buf = bytearray(); self.views = []; self.accessors = []

    def view(self, data, target=None):
        while len(self.buf) % 4: self.buf.append(0)
        v = {'buffer': 0, 'byteOffset': len(self.buf), 'byteLength': len(data)}
        if target: v['target'] = target
        self.buf += data; self.views.append(v)
        return len(self.views) - 1

    def acc(self, arr, kind):
        if kind == 'indices':
            ct = 5123 if arr.max() < 65535 else 5125
            data = arr.astype('<u2' if ct == 5123 else '<u4').tobytes()
            v = self.view(data, 34963)
            self.accessors.append({'bufferView': v, 'componentType': ct, 'count': int(arr.size), 'type': 'SCALAR'})
        else:
            a = np.ascontiguousarray(arr, dtype='<f4')
            v = self.view(a.tobytes(), 34962)
            d = {'bufferView': v, 'componentType': 5126, 'count': int(a.shape[0]), 'type': {2: 'VEC2', 3: 'VEC3', 4: 'VEC4'}[a.shape[1]]}
            if kind == 'POSITION':
                d['min'] = [float(x) for x in a.min(0)]; d['max'] = [float(x) for x in a.max(0)]
            self.accessors.append(d)
        return len(self.accessors) - 1


def tri_count(j):
    t = 0
    for m in j['meshes']:
        for p in m['primitives']:
            if 'indices' in p: t += j['accessors'][p['indices']]['count'] // 3
            else: t += j['accessors'][p['attributes']['POSITION']]['count'] // 3
    return t


def build_one(kind, name, qdrop=0):
    src = os.path.join(SRC[kind], name + '.glb')
    j, binb, bytes0 = read_glb(src)
    tris0 = tri_count(j)
    w = Writer()
    out = json.loads(json.dumps(j))
    out.pop('buffers', None); out.pop('bufferViews', None); out.pop('accessors', None)
    texlog = []
    for im_i, im in enumerate(out['images']):
        role = role_of(im.get('name', ''))
        data, s0, s1 = shrink_image(image_bytes(j, binb, j['images'][im_i]), role, qdrop)
        im['bufferView'] = w.view(data); im['mimeType'] = 'image/jpeg'
        texlog.append({'image': im.get('name'), 'role': role, 'from': list(s0), 'to': list(s1), 'jpeg_quality': JPEG_Q[role] - qdrop})
    cells = CELL[kind]
    primlog = []
    for mi, m in enumerate(j['meshes']):
        for pi, p in enumerate(m['primitives']):
            attrs = {k: accessor(j, binb, a) for k, a in p['attributes'].items()}
            idx = accessor(j, binb, p['indices']).astype(np.int64)
            prim = dict(attrs); prim['indices'] = idx
            ntri = idx.size // 3
            known = set(attrs) <= {'POSITION', 'NORMAL', 'TEXCOORD_0', 'TANGENT'}
            kindp = 'uv' if 'TEXCOORD_0' in attrs else 'plain'
            if ntri >= MIN_TRIS and known and p.get('mode', 4) == 4:
                c, st = cluster(prim, cells[kindp], NORMAL_BUCKETS[kindp])
                # silhouette guard: keep the original if the bbox moved by more than one cell
                d = np.abs(c['POSITION'].min(0) - attrs['POSITION'].min(0)).max() + np.abs(c['POSITION'].max(0) - attrs['POSITION'].max(0)).max()
                if d <= 2 * cells[kindp] and c['indices'].size >= 3:
                    prim = c
                    st.update(material=j['materials'][p['material']]['name'] if 'material' in p else None, tris0=ntri, tris1=int(c['indices'].size // 3))
                    primlog.append(st)
            op = out['meshes'][mi]['primitives'][pi]
            keep = [k for k in p['attributes'] if not (DROP_TANGENTS and k == 'TANGENT')]
            op['attributes'] = {k: w.acc(prim[k], k) for k in keep}
            op['indices'] = w.acc(np.asarray(prim['indices']), 'indices')
    out['accessors'] = w.accessors
    out['bufferViews'] = w.views
    while len(w.buf) % 4: w.buf.append(0)
    out['buffers'] = [{'byteLength': len(w.buf)}]
    tris1 = tri_count(out)
    out['asset'].setdefault('extras', {})['lod'] = {
        'level': 1, 'of': os.path.relpath(src, ROOT), 'generator': 'worldforge/lod/build_lod.py',
        'use_beyond_m': LOD1_DISTANCE_M, 'textures': texlog, 'primitives': primlog, 'tangents_dropped': DROP_TANGENTS, 'tris0': tris0, 'tris1': tris1,
        'method': 'vertex clustering keyed by position cell + normal bucket + UV cell + tangent sign; textures capped (base/normal 1024, ORM 512) and JPEG re-encoded'}
    js = json.dumps(out, separators=(',', ':')).encode()
    while len(js) % 4: js += b' '
    glb = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(w.buf)) + struct.pack('<II', len(js), 0x4E4F534A) + js + struct.pack('<II', len(w.buf), 0x004E4942) + bytes(w.buf)
    dst_dir = os.path.join(OUT, KIND_DIR[kind]); os.makedirs(dst_dir, exist_ok=True)
    dst = os.path.join(dst_dir, name + '.lod1.glb')
    open(dst, 'wb').write(glb)
    return {'kind': kind, 'name': name,
            'lod0': os.path.relpath(src, os.path.join(ROOT, 'out')),
            'lod1': os.path.relpath(dst, os.path.join(ROOT, 'out')),
            'bytes0': bytes0, 'bytes1': len(glb), 'tris0': tris0, 'tris1': tris1,
            'ratio': round(len(glb) / bytes0, 4),
            'max_pos_shift_m': round(max([p['max_pos_shift_m'] for p in primlog] or [0]), 4),
            'max_uv_shift': round(max([p.get('max_uv_shift', 0) for p in primlog] or [0]), 5),
            'sha256_lod0': hashlib.sha256(open(src, 'rb').read()).hexdigest(),
            'sha256_lod1': hashlib.sha256(glb).hexdigest()}


def names(kind):
    return sorted(f[:-4] for f in os.listdir(SRC[kind]) if f.endswith('.glb'))


def write_index(items):
    tot0 = sum(i['bytes0'] for i in items); tot1 = sum(i['bytes1'] for i in items)
    idx = {'schemaVersion': 'worldforge-lod/0.1', 'generator': 'worldforge/lod/build_lod.py',
           'umbrella': 'Powered by AGI Corp', 'target_ratio_max': TARGET_RATIO,
           'totals': {'count': len(items), 'bytes0': tot0, 'bytes1': tot1, 'ratio': round(tot1 / tot0, 4),
                      'tris0': sum(i['tris0'] for i in items), 'tris1': sum(i['tris1'] for i in items),
                      'max_ratio': max(i['ratio'] for i in items)},
           'items': items,
           'rp1': {'suggestion': f'reference lod1 at distance > {LOD1_DISTANCE_M} m',
                   'distance_m': LOD1_DISTANCE_M,
                   'how': 'serve <kind>/<name>.lod1.glb as the far model and swap to the LOD0 path (lod0, relative to worldforge/out/) inside the radius; both share origin, units (metres), up (+Y) and facing, so the swap is in place.'}}
    p = os.path.join(OUT, 'index.json')
    json.dump(idx, open(p, 'w'), indent=1)
    return idx


def check():
    p = os.path.join(OUT, 'index.json')
    idx = json.load(open(p)); bad = []
    want = {(k, n) for k in SRC for n in names(k)}
    have = {(i['kind'], i['name']) for i in idx['items']}
    if want != have: bad.append(f'index items mismatch: missing {sorted(want - have)} extra {sorted(have - want)}')
    for i in idx['items']:
        f1 = os.path.join(ROOT, 'out', i['lod1']); f0 = os.path.join(ROOT, 'out', i['lod0'])
        if not os.path.exists(f1): bad.append(f'missing {i["lod1"]}'); continue
        b1 = os.path.getsize(f1)
        if b1 != i['bytes1']: bad.append(f'{i["name"]}: bytes1 {b1} != index {i["bytes1"]}')
        if hashlib.sha256(open(f1, 'rb').read()).hexdigest() != i['sha256_lod1']: bad.append(f'{i["name"]}: lod1 sha mismatch')
        if hashlib.sha256(open(f0, 'rb').read()).hexdigest() != i['sha256_lod0']: bad.append(f'{i["name"]}: LOD0 changed since build (rebuild)')
        if i['ratio'] > TARGET_RATIO: bad.append(f'{i["name"]}: ratio {i["ratio"]} > {TARGET_RATIO}')
        if i['tris1'] > i['tris0']: bad.append(f'{i["name"]}: tris grew')
        j, _, _ = read_glb(f1)
        for im in j['images']:
            if im.get('mimeType') != 'image/jpeg': bad.append(f'{i["name"]}: non-JPEG image {im.get("name")}')
    v = os.path.join(OUT, 'validation.json')
    if os.path.exists(v):
        vj = json.load(open(v))
        for f, r in vj.get('files', {}).items():
            if r['errors'] or r['warnings']: bad.append(f'validator: {f} {r["errors"]}E {r["warnings"]}W')
        if len(vj.get('files', {})) != len(idx['items']): bad.append('validation.json does not cover every LOD1')
    else:
        bad.append('validation.json missing (run node worldforge/lod/validate_lod.mjs)')
    print(f'{len(idx["items"])} LOD1 items, total ratio {idx["totals"]["ratio"]}, max {idx["totals"]["max_ratio"]}')
    for b in bad: print('FAIL', b)
    print('check OK' if not bad else f'check FAILED ({len(bad)})')
    return 0 if not bad else 1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    ap.add_argument('--only', default='')
    a = ap.parse_args()
    if a.check: sys.exit(check())
    only = set(filter(None, a.only.split(',')))
    items = []
    prev = {}
    pi = os.path.join(OUT, 'index.json')
    if only and os.path.exists(pi):
        prev = {(i['kind'], i['name']): i for i in json.load(open(pi))['items']}
    for kind in ('landmark', 'avatar'):
        for n in names(kind):
            if only and n not in only:
                if (kind, n) in prev: items.append(prev[(kind, n)])
                continue
            r = build_one(kind, n)
            for qdrop in (8, 14, 20):        # adaptive: only files over budget lose JPEG quality, in small steps
                if r['ratio'] <= TARGET_RATIO - 0.01: break
                r = build_one(kind, n, qdrop)
            items.append(r)
            print(f'{kind:8s} {n:32s} {r["bytes0"]/1e6:5.2f} MB -> {r["bytes1"]/1e6:5.2f} MB ({r["ratio"]*100:4.1f}%)  tris {r["tris0"]} -> {r["tris1"]}', flush=True)
    idx = write_index(items)
    print('total', idx['totals'])


if __name__ == '__main__':
    main()

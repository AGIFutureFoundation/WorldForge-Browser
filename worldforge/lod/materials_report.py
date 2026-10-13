#!/usr/bin/env python3
"""Physically-plausible material audit for the landmark + avatar GLBs (report only; LOD0 files are never written).

    python3 worldforge/lod/materials_report.py           # writes worldforge/out/assets/lod/materials.json
    python3 worldforge/lod/materials_report.py --check   # exit 1 if materials.json is stale vs the GLBs

For every material it measures the effective albedo (baseColorFactor x baseColor texture, in linear and sRGB),
the effective roughness / metallic (factor x ORM G / B channels) and compares them with recommended PBR ranges
(dielectric albedo sRGB ~50..240, i.e. linear ~0.03..0.87; metals linear reflectance >= 0.5; metallic 0 or 1,
blended values only on genuinely mixed texels). Out-of-range materials are flagged with exact names and files
so the asset owners can fix them at source (worldforge/landmarks/build_landmarks.py, worldforge/avatars/build_avatars.py).
"""
import hashlib, io, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_lod import read_glb, image_bytes, SRC, OUT, ROOT  # noqa: E402

RECOMMENDED = {
    'dielectric_albedo_srgb': [50, 240], 'dielectric_albedo_linear': [0.031, 0.871],
    'metal_albedo_linear_min': 0.5, 'albedo_linear_hard_min': 0.02, 'albedo_linear_hard_max': 0.95,
    'metallic': 'exactly 0 (dielectric) or 1 (metal); in-between only on mixed texels (rust, dirt, edges)',
    'roughness': [0.05, 1.0],
    'glass': 'metallic 0, roughness 0.0-0.1, base colour near white with alphaMode BLEND or KHR_materials_transmission; IOR 1.5',
    'emissive': 'emissive materials are exempt from albedo limits; emissive strength in nits/lux needs scene exposure context',
    'references': ['glTF 2.0 spec 3.9.2 (metallic-roughness)', 'Physically Based (physicallybased.info) albedo tables',
                   'Unreal/Substance PBR guide: dielectric sRGB 50-240, metals 180-255 sRGB'],
}
KNOWN_FIX = {
    'LM_Glass': 'glass modelled as a 0.6-metal; make it metallic 0, roughness ~0.05, alphaMode BLEND (or KHR_materials_transmission)',
    'LM_Metal': 'dark 0.85-metal; real metals reflect >= 50% (aluminium ~0.91, steel ~0.56 linear): raise baseColor to ~0.56-0.91 and set metallic 1, or keep the dark colour as a painted dielectric (metallic 0)',
    'LM_Fin_Tint': 'tinted 0.7-metal; anodised/painted fins are either metal 1 with a bright tint or painted dielectric 0',
    'AV_Trim': '0.85-metal trim: set metallic 1 (brass/gold reflectance ~0.9 linear is fine)',
    'AV_Boot': '0.15 metallic on a rubber/leather boot: set metallic 0',
    'AV_Emblem': '0.35 metallic emblem: choose 0 (printed) or 1 (metal badge)',
    'AV_Shell': 'baseColor 0.92 linear (sRGB ~246) is brighter than white paint/plastic (~0.8 linear): lower to <= 0.8',
    'LM_Facade': 'ORM blue channel is fractional across the whole map on these files: author metallic 0 for stone/render and 1 only on metal mullions',
    'LM_Plaque': '0.25 metallic plaque: choose 0 (enamel) or 1 (cast metal)',
}


def srgb_to_lin(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


def lum(rgb):
    return float(0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2])


def tex(j, binb, ti, cache):
    if ti is None: return None
    src = j['textures'][ti]['source']
    if src not in cache:
        im = Image.open(io.BytesIO(image_bytes(j, binb, j['images'][src]))).convert('RGB')
        im.thumbnail((256, 256))
        cache[src] = np.asarray(im, np.float64) / 255.0
    return cache[src]


def audit_material(j, binb, m, cache):
    pbr = m.get('pbrMetallicRoughness', {})
    bcf = np.array(pbr.get('baseColorFactor', [1, 1, 1, 1])[:3], np.float64)
    mf, rf = float(pbr.get('metallicFactor', 1.0)), float(pbr.get('roughnessFactor', 1.0))
    bt = tex(j, binb, pbr.get('baseColorTexture', {}).get('index'), cache)
    ot = tex(j, binb, pbr.get('metallicRoughnessTexture', {}).get('index'), cache)
    emissive = any(m.get('emissiveFactor', [0, 0, 0])) and (m.get('emissiveTexture') is not None or 'KHR_materials_emissive_strength' in m.get('extensions', {}) or max(m.get('emissiveFactor')) > 0.5)
    if bt is not None:
        lin = srgb_to_lin(bt).reshape(-1, 3) * bcf
    else:
        lin = bcf.reshape(1, 3)
    L = 0.2126 * lin[:, 0] + 0.7152 * lin[:, 1] + 0.0722 * lin[:, 2]
    mean_lin = lin.mean(0)
    rough = (ot[..., 1].reshape(-1) * rf) if ot is not None else np.array([rf])
    metal = (ot[..., 2].reshape(-1) * mf) if ot is not None else np.array([mf])
    mixed = float(np.mean((metal > 0.05) & (metal < 0.95)))
    r = {'name': m.get('name'), 'baseColorFactor': [round(float(x), 4) for x in bcf], 'baseColorTexture': bt is not None,
         'metallicFactor': mf, 'roughnessFactor': rf, 'ormTexture': ot is not None, 'emissive': bool(emissive),
         'albedo_linear_mean': [round(float(x), 4) for x in mean_lin], 'albedo_luminance_linear': {
             'p02': round(float(np.percentile(L, 2)), 4), 'mean': round(float(L.mean()), 4), 'p98': round(float(np.percentile(L, 98)), 4)},
         'albedo_srgb_mean_8bit': [int(round(float(x) * 255)) for x in lin_to_srgb(mean_lin)],
         'roughness_effective': {'min': round(float(rough.min()), 3), 'mean': round(float(rough.mean()), 3), 'max': round(float(rough.max()), 3)},
         'metallic_effective': {'min': round(float(metal.min()), 3), 'mean': round(float(metal.mean()), 3), 'max': round(float(metal.max()), 3), 'mixed_texel_fraction': round(mixed, 3)},
         'flags': []}
    f = r['flags']; Lm = float(L.mean()); metal_mean = float(metal.mean())
    is_metal = metal_mean >= 0.5
    if not emissive:
        if Lm < RECOMMENDED['albedo_linear_hard_min']: f.append(f'albedo too dark (mean linear luminance {Lm:.3f} < 0.02, near pure black)')
        if Lm > RECOMMENDED['albedo_linear_hard_max'] or float(np.percentile(L, 98)) > 0.95: f.append(f'albedo too bright (linear luminance p98 {np.percentile(L, 98):.3f} > 0.95)')
        if not is_metal and Lm < RECOMMENDED['dielectric_albedo_linear'][0]: f.append(f'dielectric albedo below sRGB 50 (linear {Lm:.3f})')
        if not is_metal and Lm > RECOMMENDED['dielectric_albedo_linear'][1]: f.append(f'dielectric albedo above sRGB 240 (linear {Lm:.3f})')
        if is_metal and Lm < RECOMMENDED['metal_albedo_linear_min']: f.append(f'metal reflectance too dark (linear {Lm:.3f} < 0.5; real metals 0.5-0.98)')
    if ot is None and 0.0 < mf < 1.0: f.append(f'metallicFactor {mf} is neither 0 nor 1 (uniform blend, no mixed texels)')
    if ot is not None and mixed > 0.25: f.append(f'{mixed * 100:.0f}% of ORM texels are partially metallic (0.05-0.95)')
    if ot is not None and 0.0 < mf < 1.0 and metal.max() > 0.05: f.append(f'metallicFactor {mf} scales a metallic texture to fractional values')
    if float(rough.min()) < 0.03 and not emissive: f.append(f'roughness reaches {rough.min():.3f} (< 0.03: mirror-like, aliasing risk)')
    if 'glass' in (m.get('name') or '').lower() and (mf > 0 or m.get('alphaMode', 'OPAQUE') == 'OPAQUE'):
        f.append(f'glass is opaque and metallic {mf}: use metallic 0 + alphaMode BLEND or KHR_materials_transmission')
    if f and m.get('name') in KNOWN_FIX: r['suggested_fix'] = KNOWN_FIX[m['name']]
    return r


def build():
    per_name, files, digest = {}, {}, hashlib.sha256()
    for kind in ('landmark', 'avatar'):
        for fn in sorted(f for f in os.listdir(SRC[kind]) if f.endswith('.glb')):
            p = os.path.join(SRC[kind], fn)
            raw = open(p, 'rb').read(); digest.update(raw)
            j, binb, _ = read_glb(p)
            cache = {}
            for m in j['materials']:
                r = audit_material(j, binb, m, cache)
                e = per_name.setdefault(m.get('name'), {'kind': kind, 'files': 0, 'flagged_files': [], 'flags': {}, 'samples': []})
                e['files'] += 1
                if r['flags']:
                    e['flagged_files'].append(f'{os.path.basename(SRC[kind])}/{fn}')
                    for fl in r['flags']: e['flags'][fl.split(' (')[0]] = e['flags'].get(fl.split(' (')[0], 0) + 1
                if len(e['samples']) < 3: e['samples'].append({'file': fn, **r})
                files.setdefault(f'{os.path.basename(SRC[kind])}/{fn}', []).append({'material': m.get('name'), 'flags': r['flags']})
    flagged = sorted([n for n, e in per_name.items() if e['flagged_files']])
    out = {'schemaVersion': 'worldforge-materials-audit/0.1', 'generator': 'worldforge/lod/materials_report.py',
           'umbrella': 'Powered by AGI Corp', 'report_only': True,
           'note': 'measured from the LOD0 GLBs as they are; nothing was changed. Fix at source and re-run.',
           'inputs_sha256': digest.hexdigest(), 'recommended': RECOMMENDED,
           'summary': {'materials': len(per_name), 'flagged_materials': len(flagged), 'flagged_names': flagged,
                       'clean_names': sorted(n for n in per_name if n not in flagged),
                       'glbs': len(files), 'glbs_with_flags': sum(1 for v in files.values() if any(x['flags'] for x in v))},
           'materials': {n: {**e, 'flagged_file_count': len(e['flagged_files']), 'suggested_fix': KNOWN_FIX.get(n) if e['flagged_files'] else None} for n, e in sorted(per_name.items())},
           'by_file': files}
    return out


def main():
    p = os.path.join(OUT, 'materials.json')
    rep = build()
    if '--check' in sys.argv:
        old = json.load(open(p)) if os.path.exists(p) else {}
        ok = old.get('inputs_sha256') == rep['inputs_sha256']
        print('materials.json', 'up to date' if ok else 'STALE (LOD0 GLBs changed; re-run)'); sys.exit(0 if ok else 1)
    os.makedirs(OUT, exist_ok=True)
    json.dump(rep, open(p, 'w'), indent=1)
    s = rep['summary']
    print(f"{s['materials']} material names across {s['glbs']} GLBs; flagged {s['flagged_materials']}: {', '.join(s['flagged_names'])}")
    for n in s['flagged_names']:
        e = rep['materials'][n]; print(f'  {n}: {e["flagged_file_count"]}/{e["files"]} files ->', '; '.join(f'{k} x{v}' for k, v in e['flags'].items()))


if __name__ == '__main__':
    main()

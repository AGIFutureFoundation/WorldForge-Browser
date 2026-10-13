#!/usr/bin/env python3
"""WorldForge signature landmarks: one procedural civic tower GLB per world, written from scratch with numpy + PIL.

  python3 worldforge/landmarks/build_landmarks.py               # writes worldforge/out/assets/landmarks/{<slug>.glb x41,
                                                                #   index.json}, runs the Khronos validator (node +
                                                                #   tools/gltf-validator) into validation.json, renders
                                                                #   preview.jpg (numpy software raster) + preview.json
  python3 worldforge/landmarks/build_landmarks.py --no-preview  # same, without re-rendering the contact sheet
  python3 worldforge/landmarks/build_landmarks.py --check       # rebuilds in memory, exit 1 if anything on disk differs,
                                                                #   validation.json / preview.json lag the GLBs, or an
                                                                #   eval fails; writes nothing; prints one final line

What these are and are not. Each landmark is a synthetic, procedurally generated tower: a stepped stone plinth (4 m) with
an entrance portal facing +Z, a shaft with vertical fins, mullions, spandrels and setbacks, and a crown carrying an
emissive ring in the team's brand hue. It is not a real building, is not modelled on one and imports nothing; the root
node says so (extras.synthetic: true). Inputs, all read-only: my-fabric/worlds/index.json (which worlds exist and the
fields the style family is derived from), worlds/generated/teams/<slug>.json .brand (hue + mark letters), and
worldforge/out/<slug>/{blockout.generated.json, cards.json} (only to compute a clear placement suggestion for the lead).
The only text on a landmark is the brand mark's letters on the emblem plaque. No logos, no names, no business content.
"""
import argparse
import colorsys
import hashlib
import io
import json
import math
import re
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT_REL = 'worldforge/out/assets/landmarks'
OUT = ROOT / OUT_REL
GENERATOR = 'worldforge/landmarks/build_landmarks.py'
WORLDS_INDEX = ROOT / 'my-fabric/worlds/index.json'
TEAMS_DIR = ROOT / 'worlds/generated/teams'
WF_OUT = ROOT / 'worldforge/out'
VALIDATOR_DIR = ROOT / 'tools/gltf-validator'

NAME_LIMIT = 48                       # Artemis 0.4.0 aborts on longer node names (see worldforge/build.mjs)
MAX_BYTES = 3_500_000                 # per GLB, self-contained
TRI_RANGE = (8000, 60000)
H_RANGE = (30.0, 70.0)
HALF_FOOT = 6.0                       # footprint 12 x 12 m, origin at base centre
PLINTH_TOP = 4.0
NOTE = 'synthetic procedural civic landmark; not a real building and not modelled on one'
TAU = 2.0 * math.pi
VREF = 100.0                          # v = (VREF - y) / tile height: floor seams land on y = 4 + 4k
TILE = {'facade': (6.0, 8.0), 'glass': (3.0, 4.0), 'stone': (3.0, 3.0)}
NORMAL_MAPPED = ('facade', 'glass', 'stone')
TEXTURED = ('facade', 'glass', 'stone', 'plaque')
MAT_ORDER = ['stone', 'facade', 'glass', 'fin', 'metal', 'glow', 'plaque']
MAT_NAME = {'stone': 'LM_Stone', 'facade': 'LM_Facade', 'glass': 'LM_Glass', 'fin': 'LM_Fin_Tint', 'metal': 'LM_Metal',
            'glow': 'LM_Crown_Glow', 'plaque': 'LM_Plaque'}
PLAQUE_CLEAR = 6.7                    # front fins in the plaque bay start above the plaque frame (top 6.4 m)
PLACE_MARGIN = 3.0                    # metres of clearance kept around the 12 x 12 footprint
SEED = 4177

STYLES = {
    'series-setback': {
        'basis': "my-fabric/worlds/index.json worlds[].name ends in '(Series N)'",
        'form': 'square shaft, three setbacks, corner piers, tinted blade fins between glass bays, louvred lantern, '
                'emissive ring and needle spire',
    },
    'track-twist': {
        'basis': 'worlds[].zones[].source cites worlds/sources/founder-tracks-2026-09-28.md',
        'form': 'stacked two-floor glass modules turning a few degrees per module around a mast, tinted corner '
                'piers and blades, floor plates, two tilted emissive rings',
    },
    'focus-rotunda': {
        'basis': "worlds[].name ends in ' DAO' and zones[].source cites the PBC mission statement ('How It Works')",
        'form': 'round drum shaft with one setback, radial tinted fins, limestone bands, a dome and a floating '
                'emissive ring',
    },
    'platform-prism': {
        'basis': 'none of the rules above (worlds whose zones cite their own source documents)',
        'form': 'chamfered octagonal prism with a batter and one setback, tinted edge fins, glass main faces, '
                'stepped crown with emissive bands and a mast',
    },
}


# ------------------------------------------------------------------------------------------- inputs ----
def u01(slug, salt):
    return int(hashlib.sha256(f'landmark:{salt}:{slug}'.encode()).hexdigest()[:12], 16) / float(16 ** 12)


def height_for(slug):
    return round(2.0 * (H_RANGE[0] + (H_RANGE[1] - H_RANGE[0]) * u01(slug, 'height'))) / 2.0


def style_for(w):
    if re.search(r'\(Series \d+\)$', w['name']):
        return 'series-setback'
    srcs = [z.get('source', '') for z in w.get('zones', [])]
    if any('founder-tracks' in s for s in srcs):
        return 'track-twist'
    if w['name'].endswith(' DAO') and any('mission statement' in s for s in srcs):
        return 'focus-rotunda'
    return 'platform-prism'


def plaque_text(mark):
    """The mark's letters and digits only (some registry marks carry a stray '(' from a '(Series N)' name)."""
    return ''.join(ch for ch in mark if ch.isalnum()).upper()


def node_name(s):
    return s if len(s) <= NAME_LIMIT else s[:NAME_LIMIT - 1] + '…'


def load_specs():
    idx = json.loads(WORLDS_INDEX.read_text())
    specs = []
    for w in idx['worlds']:
        team = json.loads((TEAMS_DIR / f"{w['slug']}.json").read_text())
        brand = team['brand']
        st = style_for(w)
        m = re.search(r'\(Series (\d+)\)$', w['name'])
        specs.append({
            'slug': w['slug'], 'name': w['name'], 'style': st, 'height_m': height_for(w['slug']),
            'hue': int(brand['hue']), 'mark': brand['mark'], 'plaque_text': plaque_text(brand['mark']),
            'series_n': int(m.group(1)) if m else None,
            'variant': int(u01(w['slug'], 'variant') * 3),
            'twist_sign': 1 if u01(w['slug'], 'twist') < 0.5 else -1,
            'twist_deg': round(6.0 + 4.0 * u01(w['slug'], 'twist-mag'), 1),
            'fin_depth': round(0.55 + 0.3 * u01(w['slug'], 'fin'), 2),
        })
    return specs


# ------------------------------------------------------------------------------------------- colour ----
def srgb_to_lin(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def lin_to_srgb(c):
    c = np.asarray(c, np.float64)
    return np.where(c <= 0.0031308, c * 12.92, 1.055 * np.power(np.maximum(c, 0), 1 / 2.4) - 0.055)


def hsl(h, s, l):
    return np.array(colorsys.hls_to_rgb((h % 360) / 360.0, l, s))


def hue_of_lin(c):
    r, g, b = [float(x) for x in lin_to_srgb(c)]
    return colorsys.rgb_to_hls(r, g, b)[0] * 360.0


def brand_colours(hue):
    fin = srgb_to_lin(hsl(hue, 0.5, 0.48))
    glow = srgb_to_lin(hsl(hue, 0.95, 0.58))
    glow = glow / glow.max()
    return [round(float(x), 5) for x in fin], [round(float(x), 5) for x in glow]


# ------------------------------------------------------------------------------------------ geometry ----
def nrmz(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n < 1e-12, 1.0, n)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def grid_tris(K, C, pole=None):
    pole = np.zeros(K, bool) if pole is None else pole
    j = np.arange(C - 1)
    out = []
    for k in range(K - 1):
        a = k * C + j
        b, d = a + 1, a + C
        c = d + 1
        if not pole[k]:
            out.append(np.stack([a, b, c], 1))
        if not pole[k + 1]:
            out.append(np.stack([a, c, d], 1))
    return np.concatenate(out)


def roty(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]], np.float64)


def rotx(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def rot_to(v, frm=(0.0, 1.0, 0.0)):
    a = nrmz(np.asarray(frm, np.float64))
    b = nrmz(np.asarray(v, np.float64))
    c = float(a @ b)
    ax = np.cross(a, b)
    s = float(np.linalg.norm(ax))
    if s < 1e-9:
        return np.eye(3) if c > 0 else np.diag([1.0, -1.0, -1.0])
    k = ax / s
    Kx = np.array([[0, -k[2], k[1]], [k[2], 0, -k[0]], [-k[1], k[0], 0]])
    return np.eye(3) + s * Kx + (1 - c) * (Kx @ Kx)


def rot2(poly, a):
    """Rotate (x, z) points about +Y by a (same sense as roty): local +Z turns toward +X for a = +90 deg."""
    p = np.asarray(poly, np.float64)
    c, s = math.cos(a), math.sin(a)
    return np.stack([p[:, 0] * c + p[:, 1] * s, -p[:, 0] * s + p[:, 1] * c], 1)


def rect(hx, hz, cx=0.0, cz=0.0):
    # order: +Z face (left to right seen from outside), +X face, -Z face, -X face
    return np.array([(cx - hx, cz + hz), (cx + hx, cz + hz), (cx + hx, cz - hz), (cx - hx, cz - hz)], np.float64)


def circle(r, n, phase=0.0):
    th = phase + TAU * np.arange(n) / n
    return np.stack([r * np.sin(th), r * np.cos(th)], 1)


def octagon(h, c):
    return np.array([(-h + c, h), (h - c, h), (h, h - c), (h, -h + c), (h - c, -h), (-h + c, -h), (-h, -h + c),
                     (-h, h - c)], np.float64)


def blade(w, d, nose=8):
    """Fin cross-section in local (x, z): root on z = 0, a rounded nose of radius w/2 ending at z = d (outward)."""
    r = w / 2
    a = np.linspace(math.pi, 0.0, nose + 1)                      # from -x side over the tip to +x side
    arc = np.stack([r * np.cos(a), d - r + r * np.sin(a)], 1)
    return np.vstack([arc, [(r, 0.0), (-r, 0.0)]])


def shoelace(p):
    p = np.asarray(p, np.float64)
    return float(np.sum(p[:, 0] * np.roll(p[:, 1], -1) - np.roll(p[:, 0], -1) * p[:, 1]))


def orient_poly(p):
    """Our rings run with a negative shoelace area (like rect()); flip a polygon that does not."""
    p = np.asarray(p, np.float64)
    return p[::-1].copy() if shoelace(p) > 0 else p


def strip_poly(a, b, depth):
    """Plan of a thin horizontal blade standing out `depth` from the face segment a->b (outward is (-ez, ex) for our
    ring orientation: the +Z face of rect() runs toward +X)."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    e = (b - a) / np.linalg.norm(b - a)
    n = np.array([-e[1], e[0]])
    return orient_poly(np.array([a, b, b + n * depth, a + n * depth]))


class Part:
    def __init__(self, pos, uv, idx, weld):
        self.pos = np.asarray(pos, np.float64).reshape(-1, 3)
        self.uv = np.asarray(uv, np.float64).reshape(-1, 2)
        self.idx = np.asarray(idx, np.int64).reshape(-1, 3)
        self.weld = weld


class Geo:
    def __init__(self):
        self.parts = {m: [] for m in MAT_ORDER}

    def add(self, mat, pos, uv, idx, weld=False, M=None, t=None):
        pos = np.asarray(pos, np.float64).reshape(-1, 3)
        idx = np.asarray(idx, np.int64).reshape(-1, 3)
        if M is not None:
            M = np.asarray(M, np.float64)
            if np.linalg.det(M) < 0:
                idx = idx[:, ::-1].copy()
            pos = pos @ M.T
        if t is not None:
            pos = pos + np.asarray(t, np.float64)
        if uv is None:
            uv = np.zeros((len(pos), 2))
        self.parts[mat].append(Part(pos, uv, idx, weld))

    # -- extrusions ------------------------------------------------------------------------------------------
    def walls(self, mat, polys, ys, yaw=0.0, t=(0, 0, 0), smooth=False, u_wrap=1.0, edge_mats=None):
        """Side surface through closed rings polys[k] at heights ys[k]. Flat: one quad per edge per segment with its own
        vertices, u measured from the face's left corner (seen from outside). Smooth: one welded band per segment with
        a duplicated seam column, u = u_wrap tiles around."""
        M = roty(yaw)
        for k in range(len(ys) - 1):
            P0, P1 = np.asarray(polys[k], np.float64), np.asarray(polys[k + 1], np.float64)
            y0, y1 = ys[k], ys[k + 1]
            n = len(P0)
            if smooth:
                th = TILE.get(mat, (1.0, 1.0))[1]
                A, B = np.vstack([P0, P0[:1]]), np.vstack([P1, P1[:1]])
                pos = np.concatenate([np.c_[A[:, 0], np.full(n + 1, y0), A[:, 1]],
                                      np.c_[B[:, 0], np.full(n + 1, y1), B[:, 1]]])
                u = np.arange(n + 1) / n * u_wrap
                uv = np.c_[np.r_[u, u], np.r_[np.full(n + 1, (VREF - y0) / th), np.full(n + 1, (VREF - y1) / th)]]
                self.add(mat, pos, uv, grid_tris(2, n + 1), True, M, t)
                continue
            a, b = P0, np.roll(P0, -1, 0)
            c, d = np.roll(P1, -1, 0), P1
            e = b - a
            L = np.linalg.norm(e, axis=1)
            for j in range(n):
                if L[j] < 1e-9 and np.linalg.norm(c[j] - d[j]) < 1e-9:
                    continue
                m = edge_mats[j] if edge_mats is not None else mat
                tw, th = TILE.get(m, (1.0, 1.0))
                eh = e[j] / L[j] if L[j] > 1e-9 else nrmz(c[j] - d[j])
                q2 = np.array([a[j], b[j], c[j], d[j]])
                qy = np.array([y0, y0, y1, y1])
                pos = np.c_[q2[:, 0], qy, q2[:, 1]]
                uv = np.c_[(q2 - a[j]) @ eh / tw, (VREF - qy) / th]
                self.add(m, pos, uv, [[0, 1, 2], [0, 2, 3]], False, M, t)

    def cap(self, mat, poly, y, up=True, yaw=0.0, t=(0, 0, 0)):
        poly = np.asarray(poly, np.float64)
        n = len(poly)
        tw, th = TILE.get(mat, (1.0, 1.0))
        pos = np.c_[poly[:, 0], np.full(n, y), poly[:, 1]]
        idx = np.stack([np.zeros(n - 2, np.int64), np.arange(1, n - 1), np.arange(2, n)], 1)
        idx = orient(pos, idx, 1.0 if up else -1.0)
        self.add(mat, pos, np.c_[poly[:, 0] / tw, poly[:, 1] / th], idx, False, roty(yaw), t)

    def annulus(self, mat, outer, inner, y, up=True, yaw=0.0, t=(0, 0, 0)):
        outer, inner = np.asarray(outer, np.float64), np.asarray(inner, np.float64)
        n = len(outer)
        tw, th = TILE.get(mat, (1.0, 1.0))
        P = np.vstack([outer, inner])
        pos = np.c_[P[:, 0], np.full(2 * n, y), P[:, 1]]
        j = np.arange(n)
        j1 = (j + 1) % n
        idx = np.vstack([np.stack([j, j1, n + j1], 1), np.stack([j, n + j1, n + j], 1)])
        idx = orient(pos, idx, 1.0 if up else -1.0)
        self.add(mat, pos, np.c_[P[:, 0] / tw, P[:, 1] / th], idx, False, roty(yaw), t)

    def prism(self, mat, poly, y0, y1, yaw=0.0, t=(0, 0, 0), top=True, bottom=False, smooth=False, u_wrap=1.0,
              edge_mats=None, top_mat=None):
        self.walls(mat, [poly, poly], [y0, y1], yaw, t, smooth, u_wrap, edge_mats)
        if top:
            self.cap(top_mat or mat, poly, y1, True, yaw, t)
        if bottom:
            self.cap(top_mat or mat, poly, y0, False, yaw, t)

    def box(self, mat, x0, y0, z0, x1, y1, z1, yaw=0.0, t=(0, 0, 0), top=True, bottom=True):
        self.prism(mat, rect((x1 - x0) / 2, (z1 - z0) / 2, (x0 + x1) / 2, (z0 + z1) / 2), y0, y1, yaw, t, top, bottom)

    def ring_band(self, mat, outer, inner, y0, y1, yaw=0.0, t=(0, 0, 0), smooth=False, u_wrap=1.0, inner_wall=False):
        """A closed band (walls of `outer` from y0 to y1 plus top and bottom annuli to `inner`)."""
        self.walls(mat, [outer, outer], [y0, y1], yaw, t, smooth, u_wrap)
        if inner_wall:
            self.walls(mat, [inner[::-1], inner[::-1]], [y0, y1], yaw, t, smooth, u_wrap)
        self.annulus(mat, outer, inner, y1, True, yaw, t)
        self.annulus(mat, outer, inner, y0, False, yaw, t)

    def lathe(self, mat, prof, segs, M=None, t=None, tile=1.0, u_tiles=1):
        prof = np.asarray(prof, np.float64)
        r, y = prof[:, 0], prof[:, 1]
        K, C = len(r), segs + 1
        th = math.pi + TAU * np.arange(C) / segs
        X = r[:, None] * np.sin(th)[None, :]
        Z = r[:, None] * np.cos(th)[None, :]
        Y = np.broadcast_to(y[:, None], (K, C))
        pos = np.stack([X, Y, Z], -1).reshape(-1, 3)
        arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(r), np.diff(y)))])
        v = (arc[-1] - arc) / tile
        u = np.arange(C) / segs * u_tiles
        uv = np.stack([np.broadcast_to(u[None, :], (K, C)), np.broadcast_to(v[:, None], (K, C))], -1).reshape(-1, 2)
        self.add(mat, pos, uv, grid_tris(K, C, r < 1e-9), True, M, t)

    def torus(self, mat, R, r, segs=128, rsegs=14, M=None, t=None):
        a = np.linspace(-math.pi, math.pi, rsegs + 1)
        self.lathe(mat, np.stack([R + r * np.cos(a), r * np.sin(a)], 1), segs, M, t)

    def strut(self, mat, a, b, r, segs=10):
        a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
        L = float(np.linalg.norm(b - a))
        self.lathe(mat, [(r, 0.0), (r, L)], segs, rot_to(b - a), a)

    def bead(self, mat, c, r, segs=24, rings=12):
        p = np.linspace(0, math.pi, rings + 1)
        f = np.sin(p)
        f[0] = f[-1] = 0.0
        self.lathe(mat, np.stack([r * f, -r * np.cos(p)], 1), segs, None, c)

    def quad(self, mat, p, uv):
        self.add(mat, p, uv, [[0, 1, 2], [0, 2, 3]], False)


def orient(pos, idx, sign):
    n = np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]])
    flip = n[:, 1] * sign < 0
    idx = idx.copy()
    idx[flip] = idx[flip][:, ::-1]
    return idx


def finalize(part, tangents):
    p, i = part.pos, part.idx
    fn = np.cross(p[i[:, 1]] - p[i[:, 0]], p[i[:, 2]] - p[i[:, 0]])
    vn = np.zeros_like(p)
    for k in range(3):
        np.add.at(vn, i[:, k], fn)
    if part.weld:
        key = np.round(p * 1e5).astype(np.int64)
        _, inv = np.unique(key, axis=0, return_inverse=True)
        inv = np.asarray(inv).reshape(-1)
        acc = np.zeros((int(inv.max()) + 1, 3))
        np.add.at(acc, inv, vn)
        vn = acc[inv]
    ok = np.linalg.norm(vn, axis=1) > 1e-14
    n = np.where(ok[:, None], nrmz(vn), [0.0, 1.0, 0.0])
    out = {'pos': p, 'nrm': n, 'uv': part.uv, 'idx': i}
    if tangents:
        w = part.uv
        e1, e2 = p[i[:, 1]] - p[i[:, 0]], p[i[:, 2]] - p[i[:, 0]]
        d1, d2 = w[i[:, 1]] - w[i[:, 0]], w[i[:, 2]] - w[i[:, 0]]
        det = d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1]
        inv_det = np.where(np.abs(det) > 1e-14, 1.0 / np.where(np.abs(det) > 1e-14, det, 1.0), 0.0)
        sdir = (e1 * d2[:, 1:2] - e2 * d1[:, 1:2]) * inv_det[:, None]
        tdir = (e2 * d1[:, 0:1] - e1 * d2[:, 0:1]) * inv_det[:, None]
        ts, tt = np.zeros_like(p), np.zeros_like(p)
        for k in range(3):
            np.add.at(ts, i[:, k], sdir)
            np.add.at(tt, i[:, k], tdir)
        t = ts - n * np.sum(n * ts, 1, keepdims=True)
        good = np.linalg.norm(t, axis=1) > 1e-12
        alt = np.cross(n, np.where(np.abs(n[:, 2:3]) < 0.9, [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]))
        t = nrmz(np.where(good[:, None], t, alt))
        # glTF: bitangent = cross(N, T) * w points toward decreasing v (the image's "up")
        hand = np.where(np.sum(np.cross(n, t) * tt, 1) < 0, 1.0, -1.0)
        out['tan'] = np.concatenate([t, hand[:, None]], 1)
    return out


# ------------------------------------------------------------------------------------------ the tower ----
def plinth(g):
    """Stepped stone plinth, 0-4 m: three steps all round (a crepidoma), the body with an entrance portal on +Z,
    a cornice, a tinted inlay band, a canopy over the portal and a glazed door."""
    g.prism('stone', rect(6.0, 6.0), 0.0, 0.32)
    g.prism('stone', rect(5.6, 5.6), 0.32, 0.64)
    g.prism('stone', rect(5.2, 5.2), 0.64, 0.96)
    b, pw, ph, pd = 4.95, 1.5, 3.2, 0.7               # body half, portal half-width, portal top, recess depth
    zb = b - pd
    g.box('stone', -b, 0.96, -b, b, 3.7, zb, top=False, bottom=False)          # back mass (recess back wall at zb)
    g.box('stone', -b, 0.96, zb, -pw, 3.7, b, top=False, bottom=False)         # left of the portal
    g.box('stone', pw, 0.96, zb, b, 3.7, b, top=False, bottom=False)           # right of the portal
    g.box('stone', -pw, ph, zb, pw, 3.7, b, top=False, bottom=True)            # lintel (its underside is the soffit)
    # cornice: a moulded profile around the body, then the plinth top
    prof = [(b, 3.7), (b + 0.08, 3.72), (b + 0.08, 3.8), (b + 0.2, 3.86), (b + 0.2, 4.0)]
    g.walls('stone', [rect(h, h) for h, _ in prof], [y for _, y in prof])
    g.cap('stone', rect(b + 0.2, b + 0.2), 4.0)
    # tinted inlay band on three faces and both sides of the portal
    y0, y1, s = 3.42, 3.56, 0.025
    g.box('fin', -b - s, y0, -b - s, b + s, y1, -b, bottom=True)
    g.box('fin', -b - s, y0, -b, -b, y1, b + s, bottom=True)
    g.box('fin', b, y0, -b, b + s, y1, b + s, bottom=True)
    g.box('fin', -b, y0, b, -pw, y1, b + s, bottom=True)
    g.box('fin', pw, y0, b, b, y1, b + s, bottom=True)
    # door: glass leaf in a metal frame at the back of the recess
    zd = zb + 0.035
    g.quad('glass', np.array([[-1.2, 0.96, zd], [1.2, 0.96, zd], [1.2, 3.0, zd], [-1.2, 3.0, zd]]),
           np.array([[(-1.2) / 3, (VREF - 0.96) / 4], [1.2 / 3, (VREF - 0.96) / 4], [1.2 / 3, (VREF - 3.0) / 4],
                     [-1.2 / 3, (VREF - 3.0) / 4]]))
    for x0, x1 in ((-1.32, -1.2), (1.2, 1.32), (-0.04, 0.04)):
        g.box('metal', x0, 0.96, zb, x1, 3.0, zb + 0.09, bottom=False)
    g.box('metal', -1.32, 3.0, zb, 1.32, 3.14, zb + 0.09, bottom=True)
    # canopy over the portal, carried on two thin hangers
    g.box('metal', -2.1, 3.22, b - 0.05, 2.1, 3.32, 5.85, bottom=True)
    for x in (-1.9, 1.9):
        g.strut('metal', (x, 3.32, 5.7), (x, 3.7, b + 0.02), 0.03, 8)
    # two lamp standards on the lowest step, flanking the stair
    for x in (-3.4, 3.4):
        g.lathe('metal', [(0.0, 0.32), (0.16, 0.32), (0.16, 0.5), (0.1, 0.56), (0.055, 0.7), (0.045, 3.0), (0.09, 3.06),
                          (0.0, 3.08)], 24, t=(x, 0.0, 5.75))
        g.bead('glow', (x, 3.3, 5.75), 0.22, 24, 12)
        g.lathe('metal', [(0.0, 3.5), (0.16, 3.5), (0.05, 3.62), (0.0, 3.66)], 16, t=(x, 0.0, 5.75))
    return {'door_center': [0.0, 1.98, round(zd, 3)], 'portal': {'half_width': pw, 'top': ph, 'faces': '+Z'}}


def sign_box(g, zf, back):
    """Projecting metal frame on the shaft base above the portal, carrying the emblem plaque (faces +Z)."""
    zfront = zf + 0.55
    g.box('metal', -1.8, 4.5, zf - back, 1.8, 6.4, zfront, bottom=True)
    z = zfront + 0.006
    g.quad('plaque', np.array([[-1.6, 4.65, z], [1.6, 4.65, z], [1.6, 6.25, z], [-1.6, 6.25, z]]),
           np.array([[0.0, 1.0], [1.0, 1.0], [1.0, 0.0], [0.0, 0.0]]))
    return {'plaque_center': [0.0, 5.45, round(z, 3)], 'plaque_size_m': [3.2, 1.6], 'normal': [0, 0, 1]}


def cornice_rect(g, h, yb, mat='facade', depth=0.22, tall=0.6, inlay=True):
    prof = [(h, yb - tall), (h + depth * 0.55, yb - tall + 0.1), (h + depth * 0.55, yb - 0.2), (h + depth, yb - 0.12),
            (h + depth, yb)]
    g.walls(mat, [rect(x, x) for x, _ in prof], [y for _, y in prof])
    g.cap(mat, rect(h + depth, h + depth), yb)
    if inlay:
        hi = h + depth * 0.55
        g.ring_band('fin', rect(hi + 0.012, hi + 0.012), rect(hi - 0.02, hi - 0.02), yb - tall + 0.2, yb - tall + 0.3)


def parapet_rect(g, h, y, tall=0.95, thick=0.22):
    g.ring_band('facade', rect(h, h), rect(h - thick, h - thick), y, y + tall, inner_wall=True)


def face_yaws():
    return [0.0, math.pi / 2, math.pi, 3 * math.pi / 2]


def series_setback(g, sp):
    H = sp['height_m']
    crown_min = 9.6
    nf = int((H - PLINTH_TOP - crown_min) // 4)
    Ts = PLINTH_TOP + 4 * nf
    f3 = 0.18 + 0.14 * u01(sp['slug'], 'tier3')          # tier proportions vary per world (slug hash)
    f2 = 0.22 + 0.16 * u01(sp['slug'], 'tier2')
    n3 = max(1, round(nf * f3))
    n2 = max(1, round(nf * f2))
    n1 = max(2, nf - n2 - n3)
    n2 = nf - n1 - n3
    widths = [9.0, 7.5, 6.0]
    bounds = [PLINTH_TOP, PLINTH_TOP + 4 * n1, PLINTH_TOP + 4 * (n1 + n2), Ts]
    fd = sp['fin_depth']
    for k, W in enumerate(widths):
        ya, yb = bounds[k], bounds[k + 1]
        h = W / 2
        gi = h - 0.35                                   # glass plane
        g.walls('glass', [rect(gi, gi)] * 2, [ya, yb])
        for sx in (-1, 1):
            for sz in (-1, 1):
                cx, cz = sx * (h - 0.75), sz * (h - 0.75)
                g.box('facade', cx - 0.75, ya, cz - 0.75, cx + 0.75, yb - 0.6, cz + 0.75, top=False, bottom=False)
        span = W - 3.0
        npanes = int(round(span / 1.5))
        for yaw in face_yaws():
            for j in range(1, npanes):
                s = -span / 2 + 1.5 * j
                poly = blade(0.16, fd + 0.35) + [s, gi]
                y0 = PLAQUE_CLEAR if (k == 0 and yaw == 0.0 and abs(s) < 1.9) else ya   # keep the plaque bay clear
                g.prism('fin', poly, y0, yb - 0.6, yaw, bottom=y0 > ya)
            for j in range(npanes):                      # slim metal mullion at each pane centre
                s = -span / 2 + 0.75 + 1.5 * j
                g.prism('metal', rect(0.035, 0.06, s, gi + 0.06), ya, yb - 0.6, yaw, top=False)
            for f in range(1, (int(round(yb - ya)) // 4)):  # spandrel band on every floor line
                yf = ya + 4 * f
                g.box('facade', -span / 2, yf - 0.3, gi, span / 2, yf + 0.3, gi + 0.22, yaw)
            for f in range(int(round(yb - ya)) // 4):        # metal transom 0.9 m above each floor line
                yt = ya + 4 * f + 0.9
                g.box('metal', -span / 2, yt, gi, span / 2, yt + 0.07, gi + 0.1, yaw)
        cornice_rect(g, h, yb)
        if k < 2:
            parapet_rect(g, h + 0.18, yb)
    # crown: drum, louvred lantern, emissive ring, stepped cap, needle spire with a glowing bead at exactly H
    g.prism('facade', rect(2.7, 2.7), Ts, Ts + 0.8)
    ly0, ly1 = Ts + 0.8, Ts + 3.8
    g.walls('glass', [rect(2.25, 2.25)] * 2, [ly0, ly1])
    for sx in (-1, 1):
        for sz in (-1, 1):
            g.box('metal', sx * 2.25 - 0.14, ly0, sz * 2.25 - 0.14, sx * 2.25 + 0.14, ly1, sz * 2.25 + 0.14,
                  top=False, bottom=False)
    for yaw in face_yaws():
        for i in range(9):
            y = ly0 + 0.3 + 0.3 * i
            g.box('metal', -2.05, y, 2.25, 2.05, y + 0.05, 2.45, yaw)
    rings = [(3.5, 0.16, Ts + 2.3)] if sp['variant'] != 1 else [(3.5, 0.15, Ts + 1.7), (3.5, 0.15, Ts + 3.0)]
    for R, r, y in rings:
        g.torus('glow', R, r, t=(0, y, 0))
        for a in (0.25, 0.75, 1.25, 1.75):
            d = np.array([math.sin(a * math.pi), 0.0, math.cos(a * math.pi)])
            g.strut('metal', d * 2.25 * math.sqrt(2) + [0, y, 0], d * (R - r * 0.5) + [0, y, 0], 0.05)
    y = ly1
    for hh, dy in ((2.6, 0.5), (2.0, 0.5), (1.3, 0.5)):
        g.prism('facade', rect(hh, hh), y, y + dy)
        y += dy
    tip = H - 0.5
    spire = [(0.55, y), (0.42, y + 0.3 * (tip - y)), (0.2, y + 0.75 * (tip - y)), (0.07, tip - 0.15), (0.0, tip)]
    g.lathe('metal', spire, 32)
    g.bead('glow', (0, H - 0.25, 0), 0.25)
    return {'zf': 4.5, 'back': 0.36, 'shaft_top': Ts, 'floors': nf, 'tiers': [n1, n2, n3]}


def focus_rotunda(g, sp):
    H = sp['height_m']
    crown_min = 9.0
    nf = int((H - PLINTH_TOP - crown_min) // 4)
    Ts = PLINTH_TOP + 4 * nf
    n1 = max(2, round(nf * 0.6))
    n2 = nf - n1
    tiers = [(4.5, PLINTH_TOP, PLINTH_TOP + 4 * n1, 24), (3.6, PLINTH_TOP + 4 * n1, Ts, 18)]
    segs = 96
    fd = sp['fin_depth']
    for k, (R, ya, yb, nfin) in enumerate(tiers):
        gr = R - 0.35
        g.walls('glass', [circle(gr, segs)] * 2, [ya, yb], smooth=True, u_wrap=nfin / 2)
        for i in range(nfin):
            th = (i + 0.5) / nfin * TAU
            g.prism('fin', blade(0.16, 0.7 * fd) + [0.0, gr], ya, yb - 0.7, th)
            g.prism('metal', rect(0.03, 0.05, 0.0, gr + 0.04), ya, yb - 0.7, th + 0.5 / nfin * TAU, top=False)
        for f in range(int(round(yb - ya)) // 4):         # metal transom ring 0.9 m above each floor line
            yt = ya + 4 * f + 0.9
            g.ring_band('metal', circle(gr + 0.06, segs), circle(gr - 0.01, segs), yt, yt + 0.07, smooth=True)
        for f in range(2, int(round(yb - ya)) // 4, 2):  # limestone band every two floors
            yf = ya + 4 * f
            g.ring_band('facade', circle(R + 0.03, segs), circle(gr, segs), yf - 0.35, yf + 0.35, smooth=True,
                        u_wrap=round(TAU * R / 6.0))
        prof = [(R, yb - 0.7), (R + 0.15, yb - 0.58), (R + 0.15, yb - 0.2), (R + 0.32, yb - 0.1), (R + 0.32, yb)]
        uw = round(TAU * R / 6.0)
        g.walls('facade', [circle(x, segs) for x, _ in prof], [y for _, y in prof], smooth=True, u_wrap=uw)
        g.cap('facade', circle(R + 0.32, segs), yb)
        g.ring_band('fin', circle(R + 0.162, segs), circle(R + 0.13, segs), yb - 0.48, yb - 0.36, smooth=True)
        if k == 0:
            g.ring_band('facade', circle(R + 0.3, segs), circle(R + 0.1, segs), yb, yb + 0.95, smooth=True,
                        u_wrap=uw, inner_wall=True)
    # crown: drum with its own cornice, a floating emissive ring on eight struts, dome, glazed oculus lantern, finial
    g.walls('facade', [circle(3.0, segs)] * 2, [Ts, Ts + 2.2], smooth=True, u_wrap=3)
    g.walls('facade', [circle(x, segs) for x in (3.0, 3.18, 3.18)], [Ts + 2.2, Ts + 2.32, Ts + 2.5], smooth=True,
            u_wrap=3)
    g.annulus('facade', circle(3.18, segs), circle(2.95, segs), Ts + 2.5)
    yr = Ts + 1.2
    g.torus('glow', 4.3, 0.2, 160, 16, t=(0, yr, 0))
    for i in range(8):
        a = (i + 0.5) / 8 * TAU
        d = np.array([math.sin(a), 0.0, math.cos(a)])
        g.strut('metal', d * 2.95 + [0, yr, 0], d * 4.2 + [0, yr, 0], 0.06)
    p = np.linspace(0.0, 1.0, 13)
    dome = np.stack([0.8 + 2.15 * np.cos(p * math.pi / 2), Ts + 2.5 + 2.4 * np.sin(p * math.pi / 2)], 1)
    g.lathe('facade', dome, segs, tile=4.0, u_tiles=3)
    yl = Ts + 4.9
    g.walls('glass', [circle(0.8, 32)] * 2, [yl - 0.1, yl + 1.1], smooth=True, u_wrap=2)
    g.prism('metal', circle(1.0, 32), yl + 1.1, yl + 1.3, smooth=True, bottom=True)
    tip = H - 0.4
    g.lathe('metal', [(0.3, yl + 1.3), (0.2, yl + 1.3 + 0.4 * (tip - yl - 1.3)), (0.05, tip - 0.1), (0.0, tip)], 24)
    g.bead('glow', (0, H - 0.2, 0), 0.2)
    return {'zf': 4.5, 'back': 0.75, 'shaft_top': Ts, 'floors': nf, 'tiers': [n1, n2]}


def track_twist(g, sp):
    H = sp['height_m']
    crown_min = 8.0
    nm = max(2, int((H - PLINTH_TOP - crown_min) // 8))
    Ts = PLINTH_TOP + 8 * nm
    dlt = math.radians(sp['twist_sign'] * sp['twist_deg'])
    fd = sp['fin_depth']
    for k in range(nm):
        W = 6.6 - 0.14 * k
        h = W / 2
        phi = k * dlt
        ya, yb = PLINTH_TOP + 8 * k, PLINTH_TOP + 8 * (k + 1)
        g.prism('facade', rect(h + 0.25, h + 0.25), ya, ya + 0.5, phi, bottom=True)
        g.ring_band('fin', rect(h + 0.262, h + 0.262), rect(h + 0.24, h + 0.24), ya + 0.18, ya + 0.32, phi)
        gi = h - 0.2
        g.walls('glass', [rect(gi, gi)] * 2, [ya + 0.5, yb], phi)
        for sx in (-1, 1):
            for sz in (-1, 1):
                c = (sx * (h - 0.12), sz * (h - 0.12))
                g.prism('facade', rect(0.3, 0.3, *c), ya + 0.5, yb, phi, top=False)
        for yaw in face_yaws():
            for s in (-W / 4, 0.0, W / 4):
                y0 = PLAQUE_CLEAR if (k == 0 and yaw == 0.0 and abs(s) < 1.9) else ya + 0.5  # keep the plaque bay clear
                g.prism('fin', blade(0.12, fd) + [s, gi], y0, yb, phi + yaw, top=False, bottom=y0 > ya + 0.5)
            g.box('facade', -(h - 0.45), ya + 4 - 0.25, gi, h - 0.45, ya + 4 + 0.25, gi + 0.2, phi + yaw)
            for yt in (ya + 1.4, ya + 4.9):              # metal transom on each floor
                g.box('metal', -(h - 0.4), yt, gi, h - 0.4, yt + 0.07, gi + 0.09, phi + yaw)
    hl = 6.6 / 2 - 0.14 * nm
    phi = nm * dlt
    g.prism('facade', rect(hl + 0.3, hl + 0.3), Ts, Ts + 0.6, phi, bottom=True)
    g.ring_band('fin', rect(hl + 0.312, hl + 0.312), rect(hl + 0.29, hl + 0.29), Ts + 0.2, Ts + 0.34, phi)
    g.walls('facade', [circle(2.2, 64)] * 2, [Ts + 0.6, Ts + 2.0], smooth=True, u_wrap=2)
    g.cap('facade', circle(2.2, 64), Ts + 2.0)
    tip = H - 0.4
    g.lathe('metal', [(0.45, Ts + 2.0), (0.32, Ts + 2.0 + 0.5 * (tip - Ts - 2.0)), (0.1, tip - 0.2), (0.0, tip)], 24)
    g.bead('glow', (0, H - 0.2, 0), 0.2)
    for R, r, tilt, y in ((3.3, 0.18, 0.26, Ts + 3.4), (2.4, 0.13, -0.21, Ts + 5.0)):
        M = roty(phi) @ rotx(tilt)
        g.torus('glow', R, r, M=M, t=(0, y, 0))
        for a in (0.0, 0.5, 1.0, 1.5):
            d = M @ np.array([math.sin(a * math.pi), 0.0, math.cos(a * math.pi)])
            g.strut('metal', np.array([0, y, 0]) + d * 0.3, np.array([0, y, 0]) + d * (R - r * 0.5), 0.045)
    return {'zf': 3.1, 'back': 0.1, 'shaft_top': Ts, 'floors': 2 * nm, 'modules': nm,
            'twist_deg_per_module': round(math.degrees(dlt), 2)}


def platform_prism(g, sp):
    H = sp['height_m']
    crown_min = 7.5
    nf = int((H - PLINTH_TOP - crown_min) // 4)
    Ts = PLINTH_TOP + 4 * nf
    n1 = max(2, round(nf * 0.62))
    segs_ = [(4.5, 4.5 * 0.88, PLINTH_TOP, PLINTH_TOP + 4 * n1), (3.6, 3.6 * 0.86, PLINTH_TOP + 4 * n1, Ts)]
    fd = sp['fin_depth']
    mats = ['glass', 'facade'] * 4
    for k, (h0, h1, ya, yb) in enumerate(segs_):
        hf = lambda y: h0 + (h1 - h0) * (y - ya) / (yb - ya)
        ys = [ya + 4 * i for i in range(int(round(yb - ya)) // 4 + 1)]
        g.walls('glass', [octagon(hf(y), hf(y) / 3) for y in ys], ys, edge_mats=mats)
        P0, P1 = octagon(h0, h0 / 3), octagon(h1, h1 / 3)
        for v in range(8):                                # tinted fins on the eight edges, following the batter
            a = math.atan2(P0[v, 0], P0[v, 1])
            bl = rot2(blade(0.2, fd), a)
            g.walls('fin', [bl + P0[v], bl + P1[v]], [ya, yb])
            g.cap('fin', bl + P1[v], yb)
        for f in range(4):                                # five slim mullions on each main face
            for q in (1 / 6, 2 / 6, 3 / 6, 4 / 6, 5 / 6):
                pa = P0[2 * f] + (P0[2 * f + 1] - P0[2 * f]) * q
                pb = P1[2 * f] + (P1[2 * f + 1] - P1[2 * f]) * q
                e = P0[2 * f + 1] - P0[2 * f]
                a = math.atan2(-e[1], e[0])               # outward normal of the face, as a yaw
                m = rot2(rect(0.04, 0.07, 0.0, 0.05), a)
                g.walls('metal', [m + pa, m + pb], [ya, yb])
        for y in ys[:-1]:                                 # two sunshade blades per floor on each main face
            for yb_ in (y + 1.55, y + 2.85):
                hy = hf(yb_)
                O = octagon(hy, hy / 3)
                for f in range(4):
                    g.prism('metal', strip_poly(O[2 * f], O[2 * f + 1], 0.42), yb_, yb_ + 0.06, bottom=True)
        for y in ys[1:-1]:                                # spandrel band on every floor line
            hy = hf(y)
            g.ring_band('facade', octagon(hy + 0.14, (hy + 0.14) / 3), octagon(hy - 0.05, (hy - 0.05) / 3),
                        y - 0.2, y + 0.2)
        prof = [(h1, yb - 0.6), (h1 + 0.12, yb - 0.5), (h1 + 0.12, yb - 0.2), (h1 + 0.24, yb - 0.1), (h1 + 0.24, yb)]
        g.walls('facade', [octagon(x, x / 3) for x, _ in prof], [y for _, y in prof])
        g.cap('facade', octagon(h1 + 0.24, (h1 + 0.24) / 3), yb)
        g.ring_band('fin', octagon(h1 + 0.132, (h1 + 0.132) / 3), octagon(h1 + 0.1, (h1 + 0.1) / 3), yb - 0.42, yb - 0.3)
    # crown: an octagonal cap with a floating emissive ring on eight struts, a ribbed upper stage wrapped by an
    # emissive band, then a mast with a glowing bead at exactly H
    y = Ts
    g.prism('facade', octagon(2.9, 2.9 / 3), y, y + 1.4)
    yr = y + 0.75
    g.torus('glow', 3.75, 0.18, 128, 14, t=(0, yr, 0))
    O = octagon(2.9, 2.9 / 3)
    for v in range(8):
        d = np.array([O[v, 0], 0.0, O[v, 1]])
        d = d / np.linalg.norm(d)
        g.strut('metal', np.array([O[v, 0], yr, O[v, 1]]) * [0.98, 1, 0.98], d * 3.66 + [0, yr, 0], 0.05)
    y += 1.4
    g.prism('facade', octagon(2.15, 2.15 / 3), y, y + 1.9)
    g.ring_band('glow', octagon(2.21, 2.21 / 3), octagon(2.13, 2.13 / 3), y + 0.5, y + 0.85)
    for i in range(16):
        a = (i + 0.5) / 16 * TAU
        rib = rot2(rect(0.05, 0.11, 0.0, 2.2), a)
        g.prism('metal', rib, y, y + 1.9, top=True)
    y += 1.9
    tip = H - 0.4
    g.lathe('metal', [(0.4, y), (0.28, y + 0.45 * (tip - y)), (0.08, tip - 0.2), (0.0, tip)], 24)
    g.bead('glow', (0, H - 0.2, 0), 0.2)
    return {'zf': 4.5, 'back': 0.2, 'shaft_top': Ts, 'floors': nf, 'tiers': [n1, nf - n1]}


SHAFTS = {'series-setback': series_setback, 'focus-rotunda': focus_rotunda, 'track-twist': track_twist,
          'platform-prism': platform_prism}


# ------------------------------------------------------------------------------------------ textures ----
def jpeg(arr, q=85):
    b = io.BytesIO()
    Image.fromarray(arr).save(b, 'JPEG', quality=q, optimize=True)
    return b.getvalue()


def png(img):
    b = io.BytesIO()
    img.save(b, 'PNG', optimize=True)
    return b.getvalue()


def to8(a):
    return (np.clip(a, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def fnoise(N, beta, seed, aniso=1.0):
    """Tileable 1/f^beta noise (FFT-filtered white noise), zero mean, unit std. aniso > 1 stretches it along y."""
    rng = np.random.default_rng(seed)
    w = rng.standard_normal((N, N))
    F = np.fft.rfft2(w)
    fy = np.fft.fftfreq(N)[:, None] * aniso
    fx = np.fft.rfftfreq(N)[None, :]
    f = np.sqrt(fx ** 2 + fy ** 2)
    f[0, 0] = 1.0
    F *= f ** (-beta / 2.0)
    F[0, 0] = 0.0
    n = np.fft.irfft2(F, s=(N, N))
    return ((n - n.mean()) / n.std()).astype(np.float32)


def normal_from_height(Hs, k):
    gx = (np.roll(Hs, -1, 1) - np.roll(Hs, 1, 1)) * 0.5
    gy = (np.roll(Hs, -1, 0) - np.roll(Hs, 1, 0)) * 0.5
    n = np.stack([-gx * k, gy * k, np.ones_like(gx)], -1)
    return n / np.linalg.norm(n, axis=-1, keepdims=True)


FACADE = {   # tile 6 m x 8 m; cols x rows of panels, stagger, sRGB base, grain, brushed, metallic, roughness, reveal
    'series-setback': dict(cols=4, rows=4, stagger=False, rgb=(0.80, 0.785, 0.75), grain=0.018, brushed=False,
                           metal=0.0, rough=0.55, reveal=False),
    'focus-rotunda': dict(cols=2, rows=8, stagger=True, rgb=(0.84, 0.815, 0.75), grain=0.03, brushed=False,
                          metal=0.0, rough=0.68, reveal=False),
    'track-twist': dict(cols=4, rows=2, stagger=False, rgb=(0.76, 0.78, 0.80), grain=0.022, brushed=True,
                        metal=0.35, rough=0.42, reveal=False),
    'platform-prism': dict(cols=2, rows=4, stagger=False, rgb=(0.79, 0.79, 0.78), grain=0.016, brushed=False,
                           metal=0.0, rough=0.5, reveal=True),
}


def facade_maps(style, N=2048):
    """Panels with recessed seams. Fine grain lives only in baseColor; the normal map carries seams, bevels and a soft
    low-frequency wave; ORM is smooth (so the 2048 maps stay small)."""
    P = FACADE[style]
    seed = SEED + sorted(FACADE).index(style) * 101
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    cw, rh = N / P['cols'], N / P['rows']
    row = (yy // rh).astype(np.int32)
    xs = (xx + ((row % 2) * cw / 2 if P['stagger'] else 0.0)) % N
    col = (xs // cw).astype(np.int32)
    fx, fy = xs % cw, yy % rh
    d = np.minimum(np.minimum(fx, cw - fx), np.minimum(fy, rh - fy))
    if P['reveal']:
        d = np.minimum(d, np.abs(fy - rh * 0.5) + 2.0)
    gw = 5.0
    groove = smoothstep(gw, gw * 0.35, d)
    bevel = smoothstep(gw, gw + 9.0, d)
    jit = rng.normal(0, 1, (P['rows'], P['cols'])).astype(np.float32)[row, col]
    grain = fnoise(N, 1.0 if not P['brushed'] else 0.8, seed + 1, aniso=10.0 if P['brushed'] else 1.0)
    soft = fnoise(N, 3.0, seed + 3)
    base = 1.0 + 0.022 * jit + P['grain'] * grain + 0.014 * soft
    base = base * (1.0 - 0.38 * groove) - 0.03 * (1 - bevel) * (1 - groove)
    rgb = np.stack([base * P['rgb'][0], base * P['rgb'][1], base * P['rgb'][2]], -1)
    Hs = bevel - 0.6 * groove + 0.6 * soft / max(1.0, float(np.abs(soft).max()))
    nrm = normal_from_height(Hs, 2.0)
    ao = np.clip(1.0 - 0.45 * groove - 0.06 * (1 - bevel), 0, 1)
    rough = np.clip(P['rough'] + 0.03 * soft + 0.25 * groove, 0, 1)
    metal = np.full_like(ao, P['metal']) * (1 - groove)
    orm = np.stack([ao, rough, metal], -1)
    return {
        'facade_base': (jpeg(to8(rgb), 82), 'image/jpeg', N, N, f'facade baseColor ({style}, neutral, panel seams)'),
        'facade_normal': (jpeg(to8(nrm * 0.5 + 0.5), 88), 'image/jpeg', N, N, f'facade normal ({style}, panel seams)'),
        'facade_orm': (jpeg(to8(orm), 84), 'image/jpeg', N, N, f'facade ORM ({style}; R occlusion, G roughness, B metallic)'),
    }


def glass_maps(N=1024):
    """Tile 3.0 m x 4.0 m: two panes, frames on the pane edges and a transom 0.9 m above each floor line."""
    rng = np.random.default_rng(SEED + 7)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    pw = N / 2
    pane = (xx // pw).astype(np.int32)
    dxe = np.minimum(xx % pw, pw - xx % pw)
    ty = N * (1 - 0.9 / 4.0)
    dye = np.minimum(np.minimum(yy, N - yy), np.abs(yy - ty))
    d = np.minimum(dxe, dye)
    frame = smoothstep(9.0, 6.0, d)
    lite = (yy > ty).astype(np.int32)
    jit = rng.normal(0, 1, (2, 2)).astype(np.float32)[lite, pane]
    v = yy / N
    sky = 0.75 + 0.5 * (1 - v) ** 2
    wav = fnoise(N, 3.0, SEED + 8)
    g = (1.0 + 0.06 * jit + 0.03 * wav) * sky
    glass = np.stack([0.060 * g, 0.075 * g, 0.092 * g], -1)
    metal = np.array([0.17, 0.17, 0.18], np.float32)
    rgb = glass * (1 - frame[..., None]) + metal * frame[..., None]
    Hs = smoothstep(9.0, 4.0, d) * 1.0 + 0.004 * wav
    nrm = normal_from_height(Hs, 1.6)
    ao = 1.0 - 0.18 * smoothstep(14.0, 9.0, d) * (1 - frame)
    rough = 0.06 + 0.32 * frame + 0.01 * wav
    orm = np.stack([ao, rough, np.ones_like(ao)], -1)
    return {
        'glass_base': (jpeg(to8(rgb), 86), 'image/jpeg', N, N, 'glass curtain wall baseColor (dark, framed panes)'),
        'glass_normal': (jpeg(to8(nrm * 0.5 + 0.5), 88), 'image/jpeg', N, N, 'glass curtain wall normal (frames)'),
        'glass_orm': (jpeg(to8(orm), 86), 'image/jpeg', N, N, 'glass curtain wall ORM (R occlusion, G roughness, B metallic)'),
    }


def stone_maps(N=1024):
    """Tile 3 m x 3 m: granite ashlar, courses 0.75 m, blocks 1.5 m, staggered, chamfered block edges."""
    rng = np.random.default_rng(SEED + 11)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    rh, cw = N / 4, N / 2
    row = (yy // rh).astype(np.int32)
    xs = (xx + (row % 2) * cw / 2) % N
    col = (xs // cw).astype(np.int32)
    fx, fy = xs % cw, yy % rh
    d = np.minimum(np.minimum(fx, cw - fx), np.minimum(fy, rh - fy))
    joint = smoothstep(3.5, 1.5, d)
    bevel = smoothstep(3.5, 13.0, d)
    jit = rng.normal(0, 1, (4, 2)).astype(np.float32)[row, col]
    fine = fnoise(N, 0.3, SEED + 12)
    mid = fnoise(N, 1.4, SEED + 13)
    dark = (fine > 1.55).astype(np.float32)
    light = (fine < -1.75).astype(np.float32)
    base = 1.0 + 0.04 * jit + 0.035 * mid + 0.02 * fine - 0.28 * dark + 0.22 * light
    base = base * (1 - 0.45 * joint) - 0.04 * (1 - bevel) * (1 - joint)
    rgb = np.stack([base * 0.56, base * 0.54, base * 0.505], -1)
    Hs = bevel - 0.5 * joint + 0.08 * mid
    nrm = normal_from_height(Hs, 1.8)
    ao = np.clip(1.0 - 0.5 * joint - 0.08 * (1 - bevel), 0, 1)
    rough = np.clip(0.72 + 0.04 * mid + 0.15 * joint, 0, 1)
    orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
    return {
        'stone_base': (jpeg(to8(rgb), 80), 'image/jpeg', N, N, 'stone plinth baseColor (granite ashlar)'),
        'stone_normal': (jpeg(to8(nrm * 0.5 + 0.5), 86), 'image/jpeg', N, N, 'stone plinth normal (joints, chamfers)'),
        'stone_orm': (jpeg(to8(orm), 84), 'image/jpeg', N, N, 'stone plinth ORM (R occlusion, G roughness, B metallic)'),
    }


def plaque_map(text, hue, W=1024, H=512):
    """The emblem plaque: the brand mark's letters, centred, in Pillow's bundled sans (Aileron). No other text."""
    field = tuple(int(round(c * 255)) for c in hsl(hue, 0.32, 0.15))
    rule = tuple(int(round(c * 255)) for c in hsl(hue, 0.6, 0.62))
    ink = (244, 239, 228)
    img = Image.new('RGB', (W, H), field)
    d = ImageDraw.Draw(img)
    d.rectangle([22, 22, W - 23, H - 23], outline=(205, 198, 182), width=6)
    d.rectangle([40, 40, W - 41, H - 41], outline=rule, width=3)
    size = 300
    while True:
        font = ImageFont.load_default(size=size)
        sw = max(2, size // 40)
        x0, y0, x1, y1 = d.textbbox((0, 0), text, font=font, stroke_width=sw)
        if (x1 - x0 <= W - 220 and y1 - y0 <= H - 200) or size <= 40:
            break
        size -= 8
    d.text((W / 2, H / 2), text, fill=ink, font=font, anchor='mm', stroke_width=sw, stroke_fill=ink)
    return {'plaque': (png(img), 'image/png', W, H, 'emblem plaque (brand mark letters only)')}, {'font': 'Pillow default (Aileron)', 'size_px': size}


# ------------------------------------------------------------------------------------------------ GLB ----
class Bin:
    def __init__(self):
        self.data = bytearray()
        self.views, self.accessors = [], []

    def view(self, blob, target=None):
        self.data += b'\0' * ((4 - len(self.data) % 4) % 4)
        v = {'buffer': 0, 'byteOffset': len(self.data), 'byteLength': len(blob)}
        if target:
            v['target'] = target
        self.data += blob
        self.views.append(v)
        return len(self.views) - 1

    def accessor(self, arr, kind, minmax=False):
        if kind == 'SCALAR':
            ct = 5125 if arr.dtype == np.uint32 else 5123
            v = self.view(arr.tobytes(), 34963)
            acc = {'bufferView': v, 'componentType': ct, 'count': int(arr.size), 'type': 'SCALAR'}
        else:
            a = np.ascontiguousarray(arr, np.float32)
            v = self.view(a.tobytes(), 34962)
            acc = {'bufferView': v, 'componentType': 5126, 'count': int(a.shape[0]), 'type': kind}
            if minmax:
                acc['min'] = [float(x) for x in a.min(0)]
                acc['max'] = [float(x) for x in a.max(0)]
        self.accessors.append(acc)
        return len(self.accessors) - 1


def glb_bytes(doc, data):
    j = json.dumps(doc, separators=(',', ':'), ensure_ascii=False).encode('utf-8')
    j += b' ' * ((4 - len(j) % 4) % 4)
    b = bytes(data) + b'\0' * ((4 - len(data) % 4) % 4)
    head = struct.pack('<4sII', b'glTF', 2, 12 + 8 + len(j) + 8 + len(b))
    return head + struct.pack('<I4s', len(j), b'JSON') + j + struct.pack('<I4s', len(b), b'BIN\0') + b


def material_defs(fin, glow):
    tex3 = lambda p: {'baseColorTexture': f'{p}_base', 'metallicRoughnessTexture': f'{p}_orm'}
    return {
        'stone': {'tex': ['stone_base', 'stone_normal', 'stone_orm'], 'mat': {
            'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], **tex3('stone'), 'metallicFactor': 1.0,
                                     'roughnessFactor': 1.0},
            'normalTexture': 'stone_normal', 'occlusionTexture': 'stone_orm'}},
        'facade': {'tex': ['facade_base', 'facade_normal', 'facade_orm'], 'mat': {
            'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], **tex3('facade'), 'metallicFactor': 1.0,
                                     'roughnessFactor': 1.0},
            'normalTexture': 'facade_normal', 'occlusionTexture': 'facade_orm'}},
        'glass': {'tex': ['glass_base', 'glass_normal', 'glass_orm'], 'mat': {
            'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], **tex3('glass'), 'metallicFactor': 0.6,
                                     'roughnessFactor': 1.0},
            'normalTexture': 'glass_normal', 'occlusionTexture': 'glass_orm'}},
        'fin': {'tex': [], 'mat': {'pbrMetallicRoughness': {'baseColorFactor': [*fin, 1.0], 'metallicFactor': 0.7,
                                                            'roughnessFactor': 0.34}}},
        'metal': {'tex': [], 'mat': {'pbrMetallicRoughness': {'baseColorFactor': [0.2, 0.19, 0.18, 1.0],
                                                              'metallicFactor': 0.85, 'roughnessFactor': 0.38}}},
        'glow': {'tex': [], 'mat': {'pbrMetallicRoughness': {'baseColorFactor': [*glow, 1.0], 'metallicFactor': 0.0,
                                                             'roughnessFactor': 0.4},
                                    'emissiveFactor': glow,
                                    'extensions': {'KHR_materials_emissive_strength': {'emissiveStrength': 5.0}}}},
        'plaque': {'tex': ['plaque'], 'mat': {
            'pbrMetallicRoughness': {'baseColorFactor': [1, 1, 1, 1], 'baseColorTexture': 'plaque',
                                     'metallicFactor': 0.25, 'roughnessFactor': 0.45},
            'emissiveTexture': 'plaque', 'emissiveFactor': [0.3, 0.3, 0.3]}},
    }


def build_world(sp, shared):
    g = Geo()
    probe = plinth(g)
    shaft = SHAFTS[sp['style']](g, sp)
    probe.update(sign_box(g, shaft['zf'], shaft['back']))
    fin, glow = brand_colours(sp['hue'])
    defs = material_defs(fin, glow)
    ptex, pinfo = plaque_map(sp['plaque_text'], sp['hue'])
    tex_all = dict(shared['common'], **shared[sp['style']], **ptex)
    mats = [m for m in MAT_ORDER if g.parts[m]]
    images = []
    for m in mats:
        for t in defs[m]['tex']:
            if t not in images:
                images.append(t)
    B = Bin()
    img_json = [{'name': t, 'bufferView': B.view(tex_all[t][0]), 'mimeType': tex_all[t][1]} for t in images]
    tex_index = {t: i for i, t in enumerate(images)}

    def mat_json(m):
        d = json.loads(json.dumps(defs[m]['mat']))
        pbr = d['pbrMetallicRoughness']
        for key in ('baseColorTexture', 'metallicRoughnessTexture'):
            if key in pbr:
                pbr[key] = {'index': tex_index[pbr[key]]}
        for key in ('normalTexture', 'occlusionTexture', 'emissiveTexture'):
            if key in d:
                d[key] = {'index': tex_index[d[key]]}
        return {'name': MAT_NAME[m], **d}

    prims, tri, nv_all = [], 0, 0
    lo, hi = np.full(3, np.inf), np.full(3, -np.inf)
    for m in mats:
        fin_ = [finalize(p, m in NORMAL_MAPPED) for p in g.parts[m]]
        pos = np.vstack([f['pos'] for f in fin_])
        nrm = np.vstack([f['nrm'] for f in fin_])
        offs = np.cumsum([0] + [len(f['pos']) for f in fin_])[:-1]
        idx = np.vstack([f['idx'] + o for f, o in zip(fin_, offs)])
        nv = len(pos)
        idx = idx.astype(np.uint16 if nv < 65535 else np.uint32).reshape(-1)
        attrs = {'POSITION': B.accessor(pos, 'VEC3', True), 'NORMAL': B.accessor(nrm, 'VEC3')}
        if m in TEXTURED:
            attrs['TEXCOORD_0'] = B.accessor(np.vstack([f['uv'] for f in fin_]), 'VEC2')
        if m in NORMAL_MAPPED:
            attrs['TANGENT'] = B.accessor(np.vstack([f['tan'] for f in fin_]), 'VEC4')
        prims.append({'attributes': attrs, 'indices': B.accessor(idx, 'SCALAR'), 'material': mats.index(m), 'mode': 4})
        tri += len(idx) // 3
        nv_all += nv
        lo, hi = np.minimum(lo, pos.min(0)), np.maximum(hi, pos.max(0))
    name = node_name(f"Landmark · {sp['name']}")
    extras = {
        'world': sp['slug'], 'height_m': sp['height_m'], 'style': sp['style'], 'generator': GENERATOR, 'synthetic': True,
        'note': NOTE, 'units': 'metres', 'up': '+Y', 'entrance_facing': '+Z', 'origin': 'base centre (plinth at y = 0)',
        'footprint_m': [12.0, 12.0], 'plinth_m': PLINTH_TOP, 'style_basis': STYLES[sp['style']]['basis'],
        'brand': {'hue': sp['hue'], 'mark': sp['mark'], 'plaque_text': sp['plaque_text'],
                  'source': f"worlds/generated/teams/{sp['slug']}.json#brand"},
        'tint_targets': [MAT_NAME['fin'], MAT_NAME['glow']],
        'shaft_top_m': shaft['shaft_top'],
        'door_center': probe['door_center'], 'plaque_center': probe['plaque_center'],
    }
    used_ext = sorted({e for m in mats for e in defs[m]['mat'].get('extensions', {})})
    doc = {
        'asset': {'version': '2.0', 'generator': GENERATOR, 'extras': {
            'authorship': 'independently-generated-procedural-geometry', 'externalGeometryImported': False,
            'synthetic': True, 'note': NOTE}},
        **({'extensionsUsed': used_ext} if used_ext else {}),
        'scene': 0, 'scenes': [{'name': name, 'nodes': [0]}],
        'nodes': [{'name': name, 'mesh': 0, 'extras': extras}],
        'meshes': [{'name': name, 'primitives': prims}],
        'materials': [mat_json(m) for m in mats],
        'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}],
        'textures': [{'sampler': 0, 'source': i} for i in range(len(images))],
        'images': img_json,
        'accessors': B.accessors, 'bufferViews': B.views, 'buffers': [{'byteLength': 0}],
    }
    B.data += b'\0' * ((4 - len(B.data) % 4) % 4)
    doc['buffers'][0]['byteLength'] = len(B.data)
    glb = glb_bytes(doc, B.data)
    info = {
        'slug': sp['slug'], 'file': f"{sp['slug']}.glb", 'bytes': len(glb), 'triangles': tri, 'vertices': nv_all,
        'height_m': sp['height_m'], 'style': sp['style'], 'hue': sp['hue'], 'mark': sp['mark'],
        'plaque_text': sp['plaque_text'], 'node': name, 'shaft': {k: v for k, v in shaft.items() if k not in ('zf', 'back')},
        'bounds': {'min': [round(float(v), 4) for v in lo], 'max': [round(float(v), 4) for v in hi]},
        'materials': [MAT_NAME[m] for m in mats],
        'fin_rgb_linear': fin, 'glow_rgb_linear': glow,
        'textures': [{'use': tex_all[t][4], 'width': tex_all[t][2], 'height': tex_all[t][3], 'mimeType': tex_all[t][1],
                      'bytes': len(tex_all[t][0])} for t in images],
        'sha256': hashlib.sha256(glb).hexdigest(),
    }
    return glb, info, {'probe': probe, 'extras': extras, 'names': [name], 'plaque': pinfo}


# ------------------------------------------------------------------------------------------ placement ----
def placement_obstacles(slug):
    b = json.loads((WF_OUT / slug / 'blockout.generated.json').read_text())
    c = json.loads((WF_OUT / slug / 'cards.json').read_text())
    rects, segs, plaza = [], [], None
    for p in b['primitives']:
        if 'landmark' in (p.get('massingType') or '') or 'landmark' in p['primitiveId']:
            continue                                   # a landmark the lead places later must not move itself
        if p['massingType'] == 'plaza':
            plaza = (p['position'][0], p['position'][2], p['dimensions'][0] / 2, p['dimensions'][2] / 2)
            continue
        rects.append((p['position'][0], p['position'][2], p['dimensions'][0] / 2, p['dimensions'][2] / 2))
    for card in c['cards']:
        if card['kind'] in ('world', 'plaza') or 'landmark' in card['kind'] or 'landmark' in card['cardId']:
            continue
        v = card['volum']
        rects.append((v['center'][0], v['center'][2], v['halfExtents'][0], v['halfExtents'][2]))
    for r in b['roads']:
        if 'landmark' in r['primitiveId']:
            continue
        segs.append((*r['startXZ'], *r['endXZ'], r['widthMeters'] / 2))
    return np.array(rects, np.float64), np.array(segs, np.float64), plaza


FOOT_PTS = np.stack(np.meshgrid(np.linspace(-HALF_FOOT, HALF_FOOT, 13), np.linspace(-HALF_FOOT, HALF_FOOT, 13)),
                    -1).reshape(-1, 2)


def clearance(x, z, yaw, rects, segs):
    P = rot2(FOOT_PTS, yaw) + [x, z]
    px, pz = P[:, 0:1], P[:, 1:2]
    dmin = np.inf
    if len(rects):
        dx = np.maximum(np.abs(px - rects[:, 0]) - rects[:, 2], 0.0)
        dz = np.maximum(np.abs(pz - rects[:, 1]) - rects[:, 3], 0.0)
        dmin = min(dmin, float(np.hypot(dx, dz).min()))
    if len(segs):
        ax, az, bx, bz, hw = (segs[:, i] for i in range(5))
        ex, ez = bx - ax, bz - az
        L2 = np.maximum(ex * ex + ez * ez, 1e-12)
        t = np.clip(((px - ax) * ex + (pz - az) * ez) / L2, 0, 1)
        d = np.hypot(px - (ax + t * ex), pz - (az + t * ez)) - hw
        dmin = min(dmin, float(d.min()))
    return dmin


def candidates():
    """Centres in front of the plaza's north edge (|x| <= 18), nearest first; yaw turns the entrance (+Z) to the
    plaza centre. Ties prefer the east side of the council road."""
    out = []
    for z in np.arange(-31.0, -90.01, -0.5):
        for x in np.arange(-18.0, 18.01, 0.5):
            if abs(x) < 7.0:
                continue                                 # keep the council road axis (and its sight line) open
            yaw = round(math.degrees(math.atan2(-x, -z)) * 2) / 2
            out.append(((-24.0 - z) + 0.5 * abs(x), 0 if x > 0 else 1, round(float(x), 1), round(float(z), 1), yaw))
    out.sort()
    return out


def foot_off_plaza(x, z, yaw, plaza):
    if plaza is None:
        return True
    P = rot2(rect(HALF_FOOT, HALF_FOOT), math.radians(yaw)) + [x, z]
    return float(P[:, 1].max()) <= plaza[1] - plaza[3] - 1.0


def placements(slugs):
    obst = {s: placement_obstacles(s) for s in slugs}
    cands = candidates()
    per, universal = {}, None
    for s in slugs:
        rects, segs, plaza = obst[s]
        for _, _, x, z, yaw in cands:
            if not foot_off_plaza(x, z, yaw, plaza):
                continue
            c = clearance(x, z, math.radians(yaw), rects, segs)
            if c >= PLACE_MARGIN:
                per[s] = {'translation': [x, 0.0, z], 'yaw_deg': yaw, 'clearance_m': round(c, 2)}
                break
        else:
            per[s] = None
    for _, _, x, z, yaw in cands:
        ok = True
        cmin = np.inf
        for s in slugs:
            rects, segs, plaza = obst[s]
            if not foot_off_plaza(x, z, yaw, plaza):
                ok = False
                break
            c = clearance(x, z, math.radians(yaw), rects, segs)
            cmin = min(cmin, c)
            if c < PLACE_MARGIN:
                ok = False
                break
        if ok:
            universal = {'translation': [x, 0.0, z], 'yaw_deg': yaw, 'clearance_m': round(cmin, 2)}
            break
    return per, universal


# ------------------------------------------------------------------------------------------------ build ----
def build_all():
    specs = load_specs()
    shared = {'common': dict(glass_maps(), **stone_maps())}
    for st in sorted({s['style'] for s in specs}):
        shared[st] = facade_maps(st)
    outputs, infos, evals, probes = {}, [], {}, {}
    for sp in specs:
        glb, info, probe = build_world(sp, shared)
        outputs[info['file']] = glb
        infos.append(info)
        probes[sp['slug']] = probe
    per, universal = placements([s['slug'] for s in specs])
    for info in infos:
        info['placement'] = per[info['slug']]
    for sp, info in zip(specs, infos):
        evals[sp['slug']] = world_evals(sp, info, probes[sp['slug']])
    style_counts = {st: sum(1 for s in specs if s['style'] == st) for st in STYLES}
    index = {
        'schemaVersion': 'worldforge-landmarks/0.1', 'generator': GENERATOR, 'synthetic': True, 'note': NOTE,
        'umbrella': 'Powered by AGI Corp',
        'units': 'metres', 'up': '+Y', 'entrance_facing': '+Z', 'origin': 'base centre (plinth at y = 0)',
        'footprint_m': [12.0, 12.0], 'height_rule': "30 + 40 * u, u = first 48 bits of sha256('landmark:height:<slug>'), "
                                                    'rounded to 0.5 m',
        'inputs': ['my-fabric/worlds/index.json', 'worlds/generated/teams/<slug>.json#brand',
                   'worldforge/out/<slug>/blockout.generated.json + cards.json (placement only)'],
        'styles': {st: dict(STYLES[st], count=style_counts[st]) for st in STYLES},
        'tinting': 'facade/glass/stone textures are neutral and shared per style; the brand hue lives only in the '
                   'LM_Fin_Tint (fins, inlays) and LM_Crown_Glow (emissive ring, bead) material factors and the plaque',
        'plaque': 'the only text is the brand mark letters (alphanumerics of brand.mark), Pillow default sans (Aileron)',
        'placement_rule': ('suggested, not applied: worldforge/build.mjs is not edited by this generator. Centre within '
                           '|x| 7-18 m of the council road axis, north of the plaza (footprint >= 1 m off the plaza '
                           'pad), >= 3 m clear of every blockout primitive, road and card volume in that world; '
                           'nearest to the plaza first, east side on ties; yaw turns the +Z entrance to face the plaza '
                           'centre. Apply as node translation + rotation about +Y.'),
        'universal_placement': universal,
        'validation': f'{OUT_REL}/validation.json', 'preview': f'{OUT_REL}/preview.jpg',
        'totals': {'worlds': len(infos), 'triangles': sum(i['triangles'] for i in infos),
                   'bytes': sum(i['bytes'] for i in infos), 'max_bytes': max(i['bytes'] for i in infos),
                   'min_height_m': min(i['height_m'] for i in infos), 'max_height_m': max(i['height_m'] for i in infos),
                   'styles': style_counts, 'placed': sum(1 for i in infos if i['placement'])},
        'worlds': infos,
    }
    outputs['index.json'] = (json.dumps(index, indent=1, ensure_ascii=False) + '\n').encode('utf-8')
    return outputs, index, evals


# ------------------------------------------------------------------------------------------------ evals ----
def world_evals(sp, info, probe):
    tex = {t['use'].split(' (')[0]: (t['width'], t['height']) for t in info['textures']}
    lo, hi = info['bounds']['min'], info['bounds']['max']
    ex = probe['extras']
    fin_h, glow_h = hue_of_lin(info['fin_rgb_linear']), hue_of_lin(info['glow_rgb_linear'])
    hd = lambda a: min(abs(a - sp['hue']) % 360, 360 - abs(a - sp['hue']) % 360)
    return {
        'height_in_range': H_RANGE[0] <= sp['height_m'] <= H_RANGE[1],
        'height_from_hash': sp['height_m'] == height_for(sp['slug']),
        'top_at_height': abs(hi[1] - sp['height_m']) < 0.01,
        'origin_base_centre': abs(lo[1]) < 1e-4 and abs(lo[0] + hi[0]) < 1e-3 and abs(lo[2] + hi[2]) < 1e-3,
        'footprint_12m': max(abs(lo[0]), abs(hi[0]), abs(lo[2]), abs(hi[2])) <= HALF_FOOT + 1e-4,
        'entrance_plus_z': probe['probe']['door_center'][2] > 0.5 * HALF_FOOT and abs(probe['probe']['door_center'][0]) < 1e-6
                           and probe['probe']['plaque_center'][2] > 0.0 and probe['probe']['normal'] == [0, 0, 1],
        'triangles_in_range': TRI_RANGE[0] <= info['triangles'] <= TRI_RANGE[1],
        'under_3_5mb': info['bytes'] <= MAX_BYTES,
        'names_fit': all(len(n) <= NAME_LIMIT for n in probe['names']),
        'extras': ex.get('world') == sp['slug'] and ex.get('height_m') == sp['height_m'] and ex.get('style') == sp['style']
                  and ex.get('generator') == GENERATOR and ex.get('synthetic') is True,
        'textures': tex.get('facade baseColor') == (2048, 2048) and tex.get('facade normal') == (2048, 2048)
                    and tex.get('facade ORM') == (2048, 2048) and tex.get('glass curtain wall baseColor') == (1024, 1024)
                    and tex.get('stone plinth baseColor') == (1024, 1024) and tex.get('emblem plaque') == (1024, 512),
        'brand_hue': hd(fin_h) < 1.5 and hd(glow_h) < 1.5,
        'plaque_text': bool(sp['plaque_text']) and sp['plaque_text'] == plaque_text(sp['mark']),
        'style_derived': sp['style'] in STYLES,
        'placement_clear': info['placement'] is not None and info['placement']['clearance_m'] >= PLACE_MARGIN,
    }


def validate(paths):
    script = r"""
const v = require('gltf-validator'); const fs = require('fs'); const path = require('path');
(async () => {
  const out = { validator: 'gltf-validator ' + v.version(), files: {} };
  for (const f of process.argv.slice(1)) {
    const r = await v.validateBytes(new Uint8Array(fs.readFileSync(f)), { maxIssues: 200 });
    const i = r.issues;
    out.files[path.basename(f)] = { errors: i.numErrors, warnings: i.numWarnings, infos: i.numInfos, hints: i.numHints,
      messages: i.messages.map((m) => ({ code: m.code, severity: m.severity, message: m.message, pointer: m.pointer ?? null })) };
  }
  process.stdout.write(JSON.stringify(out));
})().catch((e) => { console.error(e); process.exit(2); });
"""
    r = subprocess.run(['node', '-e', script, *[str(p) for p in paths]], cwd=VALIDATOR_DIR, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError(f'validator failed: {r.stderr.strip()[:400]}')
    return json.loads(r.stdout)


def validation_doc(report, outputs):
    files = {}
    for f in sorted(report['files']):
        files[f] = {'sha256': hashlib.sha256(outputs[f]).hexdigest(), **report['files'][f]}
    return {'schemaVersion': 'worldforge-landmarks-validation/0.1', 'validator': report['validator'], 'files': files}


def validation_failures(vdoc, outputs, files):
    bad, stale = [], []
    for f in files:
        rec = (vdoc or {}).get('files', {}).get(f)
        if not rec or rec.get('sha256') != hashlib.sha256(outputs[f]).hexdigest():
            stale.append(f)
        elif rec.get('errors') or rec.get('warnings'):
            bad.append(f)
    return bad, stale


def glbs_digest(outputs, files):
    h = hashlib.sha256()
    for f in files:
        h.update(f.encode() + b'\0' + hashlib.sha256(outputs[f]).hexdigest().encode() + b'\n')
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------- preview ----
def read_glb(blob):
    jl = struct.unpack_from('<I', blob, 12)[0]
    doc = json.loads(blob[20:20 + jl])
    bo = 20 + jl + 8

    def acc(i):
        a = doc['accessors'][i]
        v = doc['bufferViews'][a['bufferView']]
        dt = {5126: np.float32, 5123: np.uint16, 5125: np.uint32}[a['componentType']]
        n = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        arr = np.frombuffer(blob, dt, a['count'] * n, bo + v['byteOffset'] + a.get('byteOffset', 0))
        return arr.reshape(a['count'], n).astype(np.float64) if n > 1 else arr.astype(np.int64)

    def img(i):
        v = doc['bufferViews'][doc['images'][i]['bufferView']]
        return Image.open(io.BytesIO(blob[bo + v['byteOffset']: bo + v['byteOffset'] + v['byteLength']])).convert('RGB')

    prims = []
    for p in doc['meshes'][doc['nodes'][0]['mesh']]['primitives']:
        prims.append({'pos': acc(p['attributes']['POSITION']), 'nrm': acc(p['attributes']['NORMAL']),
                      'uv': acc(p['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in p['attributes'] else None,
                      'idx': acc(p['indices']).reshape(-1, 3), 'mat': doc['materials'][p['material']]})
    return doc, prims, img


def rasterize(P, D, tri, W, H):
    x, y = P[tri, 0], P[tri, 1]
    ix0 = np.clip(np.ceil(x.min(1) - 0.5), 0, W - 1).astype(np.int64)
    ix1 = np.clip(np.floor(x.max(1) - 0.5), 0, W - 1).astype(np.int64)
    iy0 = np.clip(np.ceil(y.min(1) - 0.5), 0, H - 1).astype(np.int64)
    iy1 = np.clip(np.floor(y.max(1) - 0.5), 0, H - 1).astype(np.int64)
    bw, bh = ix1 - ix0 + 1, iy1 - iy0 + 1
    keep = (bw > 0) & (bh > 0) & (x.max(1) > 0) & (x.min(1) < W) & (y.max(1) > 0) & (y.min(1) < H)
    p2 = lambda v: (1 << np.ceil(np.log2(np.maximum(v, 1))).astype(np.int64))
    kb = p2(bw) * 8192 + p2(bh)
    frags = []
    for key in np.unique(kb[keep]):
        sel = np.nonzero(keep & (kb == key))[0]
        gw, gh = int(key // 8192), int(key % 8192)
        oy, ox = np.divmod(np.arange(gw * gh), gw)
        for chunk in np.array_split(sel, max(1, len(sel) * gw * gh // 2_000_000 + 1)):
            px = ix0[chunk, None] + ox[None, :]
            py = iy0[chunk, None] + oy[None, :]
            ok = (px <= ix1[chunk, None]) & (py <= iy1[chunk, None])
            cx, cy = px + 0.5, py + 0.5
            X, Y = x[chunk], y[chunk]
            area = (X[:, 1] - X[:, 0]) * (Y[:, 2] - Y[:, 0]) - (X[:, 2] - X[:, 0]) * (Y[:, 1] - Y[:, 0])
            area = np.where(np.abs(area) < 1e-12, 1e-12, area)[:, None]
            w0 = ((X[:, 1:2] - cx) * (Y[:, 2:3] - cy) - (X[:, 2:3] - cx) * (Y[:, 1:2] - cy)) / area
            w1 = ((X[:, 2:3] - cx) * (Y[:, 0:1] - cy) - (X[:, 0:1] - cx) * (Y[:, 2:3] - cy)) / area
            w2 = 1.0 - w0 - w1
            ok &= (w0 >= -1e-6) & (w1 >= -1e-6) & (w2 >= -1e-6)
            r, c = np.nonzero(ok)
            t = chunk[r]
            dd = D[tri[t, 0]] * w0[r, c] + D[tri[t, 1]] * w1[r, c] + D[tri[t, 2]] * w2[r, c]
            frags.append((py[r, c] * W + px[r, c], dd, t, w0[r, c], w1[r, c], w2[r, c]))
    if not frags:
        return np.zeros(0, np.int64), np.zeros(0, np.int64), np.zeros((0, 3))
    pix, dep, tid, b0, b1, b2 = (np.concatenate(z) for z in zip(*frags))
    order = np.lexsort((-dep, pix))
    first = np.r_[True, pix[order][1:] != pix[order][:-1]]
    win = order[first]
    return pix[win], tid[win], np.stack([b0[win], b1[win], b2[win]], 1)


def sample(tex, uv):
    h, w = tex.shape[:2]
    x = uv[:, 0] * w - 0.5
    y = uv[:, 1] * h - 0.5
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    g = lambda yy, xx: tex[yy % h, xx % w]
    return (g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy) + g(y0 + 1, x0) * (1 - fx) * fy
            + g(y0 + 1, x0 + 1) * fx * fy)


def shade(prims_all, sel_tri, bary, tri_prim, tri_local, V):
    """Daylight: Lambert + Blinn-Phong sun, sky/ground hemisphere, a reflection of a sky gradient, emissive added."""
    out = np.zeros((len(sel_tri), 3))
    lights = [(nrmz(np.array([0.5, 0.7, 0.62])), 2.6, np.array([1.0, 0.96, 0.9])),
              (nrmz(np.array([-0.7, 0.35, 0.4])), 0.5, np.array([0.8, 0.88, 1.0]))]
    sky, ground = np.array([0.55, 0.62, 0.72]), np.array([0.16, 0.15, 0.13])
    for pi_, pr in enumerate(prims_all):
        m = tri_prim[sel_tri] == pi_
        if not m.any():
            continue
        t = pr['idx'][tri_local[sel_tri[m]]]
        b = bary[m]
        N = nrmz(np.einsum('ki,kij->kj', b, pr['nrm'][t]))
        mat, pbr = pr['mat'], pr['mat']['pbrMetallicRoughness']
        alb = np.broadcast_to(np.asarray(pbr['baseColorFactor'][:3], np.float64), N.shape).copy()
        uv = np.einsum('ki,kij->kj', b, pr['uv'][t]) if pr['uv'] is not None else None
        if 'baseColorTexture' in pbr and uv is not None:
            alb = alb * sample(pr['tex'][pbr['baseColorTexture']['index']], uv)
        em = np.zeros_like(N)
        if 'emissiveFactor' in mat:
            k = mat.get('extensions', {}).get('KHR_materials_emissive_strength', {}).get('emissiveStrength', 1.0)
            em = np.broadcast_to(np.array(mat['emissiveFactor']) * k * 0.35, N.shape).copy()
            if 'emissiveTexture' in mat and uv is not None:
                em = em * sample(pr['tex'][mat['emissiveTexture']['index']], uv)
        metal, rough = pbr.get('metallicFactor', 1.0), pbr.get('roughnessFactor', 1.0)
        name = mat.get('name', '')
        if name == 'LM_Glass':
            metal, rough = 0.6, 0.08
        elif 'metallicRoughnessTexture' in pbr:
            metal, rough = (0.3, 0.45) if name == 'LM_Facade' and False else (0.0, 0.6)
        f0 = 0.04 * (1 - metal) + alb * metal
        hemi = ground + (sky - ground) * (0.5 + 0.5 * N[:, 1:2])
        col = alb * (1 - metal) * hemi * 0.95
        s = float(np.clip(2.0 / max(rough, 0.05) ** 4 - 2.0, 2.0, 2048.0))
        for L, I, lc in lights:
            ndl = np.clip(N @ L, 0, None)[:, None]
            Hh = nrmz(L + V)
            spec = f0 * ((s + 8) / (8 * math.pi)) * np.clip(N @ Hh, 0, None)[:, None] ** s * ndl
            col += I * lc * (alb * (1 - metal) * ndl / math.pi * 2.0 + spec * 0.5)
        R = 2 * np.sum(N * V, 1, keepdims=True) * N - V
        env = ground + (np.array([0.62, 0.72, 0.86]) * 1.5 - ground) * smoothstep(-0.25, 0.5, R[:, 1:2])
        fres = f0 + (1 - f0) * (1 - np.clip(np.sum(N * V, 1, keepdims=True), 0, 1)) ** 5 * (1 - rough) ** 2
        col += env * fres * (1 - rough * 0.85)
        out[m] = col + em
    return out


def preview_raster(out_path, outputs, index, cols=11, cw=200, rowH=560, head=84, ss=2):
    """Contact sheet of all GLBs as written, to one scale: numpy software raster (no normal maps, no shadows)."""
    order = sorted(index['worlds'], key=lambda i: (list(STYLES).index(i['style']), i['slug']))
    rows_n = math.ceil(len(order) / cols)
    W = cols * cw
    scale = (rowH - 74) / 72.0 * ss                      # px per metre, same for every cell
    pitch, yaw = math.radians(4.0), 0.55
    Ry = roty(yaw)
    V = np.array([0.0, math.sin(pitch), math.cos(pitch)])
    sheet = Image.new('RGB', (W, head + rows_n * rowH), (236, 239, 243))
    tcache = {}
    for r in range(rows_n):
        cells = order[r * cols:(r + 1) * cols]
        Wss, Hss = W * ss, rowH * ss
        gy = Hss - 58 * ss
        P, D, tri, tri_prim, tri_local, prims_all = [], [], [], [], [], []
        base = 0
        for c, info in enumerate(cells):
            doc, prims, img = read_glb(outputs[info['file']])
            cx = (c + 0.5) * cw * ss
            for pr in prims:
                pr['tex'] = {}
                for key in ('baseColorTexture', 'emissiveTexture'):
                    ref = pr['mat']['pbrMetallicRoughness'].get(key) if key == 'baseColorTexture' else pr['mat'].get(key)
                    if ref is None:
                        continue
                    i = doc['textures'][ref['index']]['source']
                    im = img(i)
                    nm = doc['images'][i]['name']
                    k = (info['slug'] if nm == 'plaque' else '', nm)
                    if k not in tcache:
                        size = (256, 128) if nm == 'plaque' else (128, 128)
                        tcache[k] = srgb_to_lin(np.asarray(im.resize(size, Image.BOX), np.float64) / 255.0)
                    pr['tex'][ref['index']] = tcache[k]
                pos = pr['pos'] @ Ry.T
                q = dict(pr, nrm=pr['nrm'] @ Ry.T)
                sx = pos[:, 0]
                sy = pos[:, 1] * math.cos(pitch) - pos[:, 2] * math.sin(pitch)
                dz = pos[:, 1] * math.sin(pitch) + pos[:, 2] * math.cos(pitch)
                px = np.stack([cx + sx * scale, gy - sy * scale], 1)
                a = pr['idx']
                e = ((px[a[:, 1], 0] - px[a[:, 0], 0]) * (px[a[:, 0], 1] - px[a[:, 2], 1])
                     - (px[a[:, 2], 0] - px[a[:, 0], 0]) * (px[a[:, 0], 1] - px[a[:, 1], 1]))
                front = np.nonzero(e > 0)[0]
                P.append(px)
                D.append(dz)
                tri.append(a[front] + base)
                tri_local.append(front)
                tri_prim.append(np.full(len(front), len(prims_all)))
                prims_all.append(q)
                base += len(pos)
        P, D = np.vstack(P), np.concatenate(D)
        tri, tri_local, tri_prim = np.vstack(tri), np.concatenate(tri_local), np.concatenate(tri_prim)
        pix, tid, bary = rasterize(P, D, tri, Wss, Hss)
        col = shade(prims_all, tid, bary, tri_prim, tri_local, V)
        col = 1.0 - np.exp(-col * 1.1)
        yy = np.linspace(0, 1, Hss)[:, None, None]
        bg = np.array([0.62, 0.72, 0.84]) * (1 - yy) + np.array([0.90, 0.92, 0.94]) * yy
        bg = np.broadcast_to(bg, (Hss, Wss, 3)).copy()
        bg[gy:] = np.array([0.55, 0.56, 0.55])
        X = np.arange(Wss)[None, :]
        Yg = np.arange(Hss)[:, None]
        for c in range(len(cells)):
            cx = (c + 0.5) * cw * ss
            d = ((X - cx - 5 * ss) / (8.5 * scale)) ** 2 + ((Yg - gy - 2 * ss) / (1.2 * scale)) ** 2
            bg *= (1 - 0.35 * np.exp(-d * 3.0))[..., None] ** 1.0
        imgarr = bg.reshape(-1, 3).copy()
        imgarr[pix] = np.clip(col, 0, 1) ** (1 / 2.2)
        im = Image.fromarray(to8(imgarr.reshape(Hss, Wss, 3))).resize((W, rowH), Image.LANCZOS)
        sheet.paste(im, (0, head + r * rowH))
        d = ImageDraw.Draw(sheet)
        f = lambda s: ImageFont.load_default(size=s)
        for c, info in enumerate(cells):
            cx = (c + 0.5) * cw
            y0 = head + (r + 1) * rowH - 50
            slug = info['slug'] if len(info['slug']) <= 24 else info['slug'][:23] + '…'
            d.text((cx, y0), slug, fill=(24, 28, 36), font=f(13), anchor='mt')
            d.text((cx, y0 + 19), f"{info['height_m']:g} m · {info['style']}", fill=(70, 78, 92), font=f(11), anchor='mt')
    d = ImageDraw.Draw(sheet)
    f = lambda s: ImageFont.load_default(size=s)
    d.text((24, 14), 'WorldForge signature landmarks - 41 worlds, one scale', fill=(20, 24, 32), font=f(26))
    d.text((24, 48), 'Synthetic procedural towers (not real buildings). Brand hue on fins, inlays and the crown ring; '
           'plaque shows the brand mark letters only. numpy software raster of the GLBs as written '
           '(no normal maps, no shadows).', fill=(70, 78, 92), font=f(14))
    b = io.BytesIO()
    sheet.save(b, 'JPEG', quality=88, optimize=True)
    out_path.write_bytes(b.getvalue())
    return b.getvalue(), f'{out_path.relative_to(ROOT)}: {sheet.width}x{sheet.height}, {len(b.getvalue()) / 1e3:.0f} KB'


# ----------------------------------------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='rebuild in memory; exit 1 if outputs on disk differ')
    ap.add_argument('--no-preview', action='store_true', help='skip rendering preview.jpg (write mode)')
    ap.add_argument('--no-validate', action='store_true', help='skip the Khronos validator run (write mode)')
    args = ap.parse_args()

    outputs, index, evals = build_all()
    glbs = [i['file'] for i in index['worlds']]
    tri = index['totals']['triangles']
    n = len(glbs)
    vpath, ppath = OUT / 'validation.json', OUT / 'preview.json'

    if args.check:
        stale = [f for f, b in outputs.items() if not (OUT / f).exists() or (OUT / f).read_bytes() != b]
        try:
            vdoc = json.loads(vpath.read_text())
        except (OSError, ValueError):
            vdoc = None
        bad_v, stale_v = validation_failures(vdoc, outputs, glbs)
        try:
            pdoc = json.loads(ppath.read_text())
            prev_ok = (pdoc.get('glbs_sha256') == glbs_digest(outputs, glbs) and (OUT / 'preview.jpg').exists()
                       and hashlib.sha256((OUT / 'preview.jpg').read_bytes()).hexdigest() == pdoc.get('sha256'))
        except (OSError, ValueError):
            prev_ok = False
        failing = sorted({s for s, e in evals.items() if not all(e.values())} | {f[:-4] for f in bad_v})
        if stale:
            print(f'landmarks STALE: {len(stale)} of {len(outputs)} files differ from their generator (first: {stale[0]})')
            sys.exit(1)
        if stale_v:
            print(f'landmarks STALE: validation.json is behind {len(stale_v)} GLBs (first: {stale_v[0]}); run {GENERATOR}')
            sys.exit(1)
        if not prev_ok:
            print(f'landmarks STALE: preview.jpg / preview.json do not match the current GLBs; run {GENERATOR}')
            sys.exit(1)
        print(f'landmarks current: {n} worlds, {tri} triangles, {len(failing)} failing')
        sys.exit(1 if failing else 0)

    OUT.mkdir(parents=True, exist_ok=True)
    for f, b in outputs.items():
        (OUT / f).write_bytes(b)
    bad_v, stale_v = [], []
    if not args.no_validate:
        report = validate([OUT / f for f in glbs])
        vdoc = validation_doc(report, outputs)
        vpath.write_text(json.dumps(vdoc, indent=1, ensure_ascii=False) + '\n')
        bad_v, stale_v = validation_failures(vdoc, outputs, glbs)
        tot = {k: sum(r[k] for r in vdoc['files'].values()) for k in ('errors', 'warnings', 'infos', 'hints')}
        codes = sorted({m['code'] for r in vdoc['files'].values() for m in r['messages']})
        print(f"  validator ({vdoc['validator']}): {tot['errors']} errors, {tot['warnings']} warnings, "
              f"{tot['infos']} infos, {tot['hints']} hints over {n} GLBs" + (f' [{", ".join(codes)}]' if codes else ''))
    for i in index['worlds']:
        e = evals[i['slug']]
        pl = i['placement']
        print(f"  {i['file']}: {i['style']}, {i['height_m']:g} m, {i['triangles']} tris, {i['bytes'] / 1e6:.2f} MB, "
              f"hue {i['hue']}, '{i['plaque_text']}'"
              + (f", place {pl['translation'][0]:g},{pl['translation'][2]:g} yaw {pl['yaw_deg']:g}" if pl else ', NO PLACE')
              + ('' if all(e.values()) else f'  FAIL {[k for k, v in e.items() if not v]}'))
    if not args.no_preview:
        blob, msg = preview_raster(OUT / 'preview.jpg', outputs, index)
        ppath.write_text(json.dumps({'file': 'preview.jpg', 'method': 'numpy software raster (no normal maps, no shadows)',
                                     'glbs_sha256': glbs_digest(outputs, glbs),
                                     'sha256': hashlib.sha256(blob).hexdigest()}, indent=1) + '\n')
        print(f'  preview: {msg}')
    failing = sorted({s for s, e in evals.items() if not all(e.values())} | {f[:-4] for f in bad_v + stale_v})
    print(f'landmarks {"RED" if failing else "GREEN"}: {n} worlds, {tri} triangles, '
          f'{index["totals"]["bytes"] / 1e6:.1f} MB (max {index["totals"]["max_bytes"] / 1e6:.2f} MB), '
          f'{len(failing)} failing' + (f' ({", ".join(failing)})' if failing else ''))
    sys.exit(1 if failing else 0)


if __name__ == '__main__':
    main()

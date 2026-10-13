#!/usr/bin/env python3
"""WorldForge agent avatars: six stylised, rig-free humanoid GLBs written from scratch with numpy + PIL.

  python3 worldforge/avatars/build_avatars.py              # writes worldforge/out/assets/avatars/{<role>.glb,
                                                           #   index.json}, then runs the Khronos validator
                                                           #   (node + tools/gltf-validator) into validation.json
  python3 worldforge/avatars/build_avatars.py --preview    # also renders preview.jpg via headless Chrome + preview.html
                                                           #   (needs the static server on :8080 and the jsDelivr CDN)
  python3 worldforge/avatars/build_avatars.py --check      # rebuilds in memory, exit 1 if anything on disk differs or
                                                           #   validation.json is behind the GLBs; writes nothing

Roles (one GLB each): specialist, coordinator, omega, host, liaison, alignment. WorldForge cards point at these files
(worldforge/build.mjs AVATAR_DIR / AVATAR_ROLES): agent cards at specialist.glb, Omega Steward cards at omega.glb.

What these are and are not. Each avatar is a procedurally generated, stylised figure: smooth lathe/ellipsoid/capsule
parts, a visor band where a face would be, mitt hands, no rig, no animation, no likeness of anyone. They are agents,
not people, and the root node says so in its extras (synthetic: true). Geometry and every texture are generated here
from fixed seeds; nothing is imported. Body fabric is neutral light grey so a viewer can tint it per world by
multiplying the baseColorFactor of the AV_Fabric_* materials (worlds/generated/teams/<slug>.json .brand.hue).
"""
import argparse
import hashlib
import io
import json
import math
import struct
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OUT_REL = 'worldforge/out/assets/avatars'
OUT = ROOT / OUT_REL
GENERATOR = 'worldforge/avatars/build_avatars.py'
ROLES = ['specialist', 'coordinator', 'omega', 'host', 'liaison', 'alignment']
NAME_LIMIT = 48                       # Artemis 0.4.0 aborts on longer node names (see worldforge/build.mjs)
TRI_RANGE = (6000, 20000)
MAX_BYTES = 4 * 1024 * 1024
HEIGHT = {'omega': 2.1}               # metres, top of head; everyone else 1.8
NOTE = 'stylised agent avatar; an agent, not a person'
SEED = 1729
TILE = 0.5                            # metres of fabric per texture repeat
TAU = 2.0 * math.pi
VALIDATOR_DIR = ROOT / 'tools/gltf-validator'
CHROME = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
PREVIEW_URL = 'http://127.0.0.1:8080/worldforge/avatars/preview.html?sheet=1'


# ------------------------------------------------------------------------------------------- geometry ----
def nrmz(v):
    n = np.linalg.norm(v, axis=-1, keepdims=True)
    return v / np.where(n < 1e-12, 1.0, n)


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


class Part:
    """A piece of surface: positions, UVs, triangles. Normals/tangents are derived at the end from final positions."""

    def __init__(self, pos, uv, idx, weld=True):
        self.pos = np.asarray(pos, np.float64).reshape(-1, 3)
        self.uv = np.asarray(uv, np.float64).reshape(-1, 2)
        self.idx = np.asarray(idx, np.int64).reshape(-1, 3)
        self.weld = weld                      # average normals across coincident vertices (UV seams, poles)

    def xform(self, M=None, t=None):
        if M is not None:
            M = np.asarray(M, np.float64)
            if np.linalg.det(M) < 0:
                self.idx = self.idx[:, ::-1].copy()
            self.pos = self.pos @ M.T
        if t is not None:
            self.pos = self.pos + np.asarray(t, np.float64)
        return self


def grid_tris(K, C, pole=None):
    """Quads between K rows of C vertices; a row flagged as a pole collapses to a fan (no degenerate triangles)."""
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


def lathe(prof, segs, sx=1.0, sz=1.0, tile=TILE, u_tiles=None):
    """Revolve a (r, y) profile (bottom to top) about +Y. Seam at the back (-Z); outward normals for profiles that go
    up the outside. UVs: u wraps an integer number of fabric tiles, v runs top-down in metres / tile."""
    prof = np.asarray(prof, np.float64)
    r, y = prof[:, 0], prof[:, 1]
    K, C = len(r), segs + 1
    th = math.pi + TAU * np.arange(C) / segs
    X = r[:, None] * np.sin(th)[None, :] * sx
    Z = r[:, None] * np.cos(th)[None, :] * sz
    Y = np.broadcast_to(y[:, None], (K, C))
    pos = np.stack([X, Y, Z], -1).reshape(-1, 3)
    s = 0.5 * (sx + sz)
    arc = np.concatenate([[0.0], np.cumsum(np.hypot(np.diff(r) * s, np.diff(y)))])
    v = (arc[-1] - arc) / tile
    if u_tiles is None:
        a, b = r.max() * sx, r.max() * sz
        per = math.pi * (3 * (a + b) - math.sqrt((3 * a + b) * (a + 3 * b)))
        u_tiles = max(1, int(round(per / tile)))
    u = np.arange(C) / segs * u_tiles
    uv = np.stack([np.broadcast_to(u[None, :], (K, C)), np.broadcast_to(v[:, None], (K, C))], -1).reshape(-1, 2)
    return Part(pos, uv, grid_tris(K, C, r < 1e-9))


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


def rot_x(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]], np.float64)


def frame(d, pn):
    """Rotation whose local Y is d and local Z is pn (orthogonalised); local X = d x pn."""
    d = nrmz(np.asarray(d, np.float64))
    pn = np.asarray(pn, np.float64)
    pn = nrmz(pn - d * float(pn @ d))
    w = np.cross(d, pn)
    return np.stack([w, d, pn], 1)


def limb(a, b, ra, rb, segs=20, cap=5, mid=6):
    """Tapered capsule from joint a to joint b."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    L = float(np.linalg.norm(b - a))
    prof = [(ra * math.sin(p), -ra * math.cos(p)) for p in np.linspace(0, math.pi / 2, cap + 1)]
    prof += [(ra + (rb - ra) * t, L * t) for t in np.linspace(0, 1, mid + 1)[1:-1]]
    prof += [(rb * math.sin(p), L + rb * math.cos(p)) for p in np.linspace(math.pi / 2, 0, cap + 1)]
    return lathe(prof, segs).xform(rot_to(b - a), a)


def tube(a, b, prof_loop, segs=24):
    """A closed (r, t) loop revolved along the segment a->b (t in metres from a): sleeves, collars, cuffs."""
    a, b = np.asarray(a, np.float64), np.asarray(b, np.float64)
    return lathe(prof_loop, segs).xform(rot_to(b - a), a)


def ellipsoid(c, rx, ry, rz, segs=24, rings=14, M=None):
    p = np.linspace(0, math.pi, rings + 1)
    f = np.sin(p)
    f[0] = f[-1] = 0.0
    return lathe(np.stack([f, -ry * np.cos(p)], 1), segs, sx=rx, sz=rz).xform(M, c)


def torus(R, r, segs=48, rsegs=10, sz=1.0):
    a = np.linspace(-math.pi, math.pi, rsegs + 1)
    return lathe(np.stack([R + r * np.cos(a), r * np.sin(a)], 1), segs, sz=sz)


def surface_band(r_of_y, sx, sz, th0, th1, nth, ns, yc, half, lift, uv_fn):
    """A band hugging a lathe body: theta from +Z toward +X, rows bottom to top; lift(theta, s) is the outward offset in
    metres (negative sinks the edge into the body so no seam shows)."""
    th = np.linspace(th0, th1, nth + 1)
    s = np.linspace(-1.0, 1.0, ns + 1)
    S, TH = np.meshgrid(s, th, indexing='ij')
    Y = yc(TH) + S * half
    R = r_of_y(Y)
    H = lift(TH, S)
    pos = np.stack([(R * sx + H) * np.sin(TH), Y, (R * sz + H) * np.cos(TH)], -1).reshape(-1, 3)
    U, V = uv_fn(TH, S)
    return Part(pos, np.stack([U, V], -1).reshape(-1, 2), grid_tris(ns + 1, nth + 1))


def place(part, point, normal):
    """Seat a decal-like part (built facing local +Y, image-down along local +Z) on a surface point."""
    n = nrmz(np.asarray(normal, np.float64))
    right = nrmz(np.cross(-n, [0.0, 1.0, 0.0]))
    up = np.cross(n, right)
    return part.xform(np.stack([right, n, -up], 1), point)


def puck(R, t, segs=40):
    """Round badge: flat face up (+Y), bevelled rim; planar UVs so the emblem image sits on the face."""
    prof = [(0.0, 0.0), (R * 0.96, 0.0), (R, t * 0.18), (R, t * 0.72), (R * 0.95, t), (R * 0.88, t), (0.0, t)]
    p = lathe(prof, segs)
    p.uv = np.stack([0.5 + p.pos[:, 0] / (2 * R), 0.5 + p.pos[:, 2] / (2 * R)], 1)
    return p


def shield_outline(n=10):
    """Unit heater-shield outline in (x right, z down): x in [-0.5, 0.5], z in [-0.47, 0.53]. Convex."""
    right = [(0.5, -0.47), (0.5, 0.0)]
    for t in np.linspace(0, 1, n + 1)[1:]:
        right.append(((1 - t) ** 2 * 0.5 + 2 * (1 - t) * t * 0.5, 2 * (1 - t) * t * 0.32 + t * t * 0.53))
    left = [(-x, z) for x, z in reversed(right[:-1])]
    return np.array(right + left, np.float64)


def shield_plate(w, h, t, bend):
    """Extruded shield (front at local y=t) with chest-following bend(x); planar UVs over the shield's bounding box."""
    P = shield_outline() * [w, h]
    n = len(P)
    cen = np.array([0.0, 0.0])
    def ring(y):
        return np.stack([P[:, 0], y + bend(P[:, 0]), P[:, 1]], 1)
    front = np.vstack([[0.0, t + bend(np.array([0.0]))[0], 0.0], ring(t)])
    back = np.vstack([[0.0, bend(np.array([0.0]))[0], 0.0], ring(0.0)])
    side_f, side_b = ring(t), ring(0.0)
    pos = np.vstack([front, back, side_f, side_b])
    o_b, o_sf, o_sb = n + 1, 2 * (n + 1), 2 * (n + 1) + n
    i = np.arange(n)
    j = (i + 1) % n
    tri_f = np.stack([np.zeros(n, int), 1 + i, 1 + j], 1)
    tri_b = np.stack([np.full(n, o_b), o_b + 1 + j, o_b + 1 + i], 1)
    tri_s = np.vstack([np.stack([o_sf + i, o_sb + i, o_sb + j], 1), np.stack([o_sf + i, o_sb + j, o_sf + j], 1)])
    idx = np.vstack([tri_f, tri_b, tri_s])
    # orient every triangle against its intended outward direction
    mid = pos[idx].mean(1)
    fn = np.cross(pos[idx[:, 1]] - pos[idx[:, 0]], pos[idx[:, 2]] - pos[idx[:, 0]])
    want = np.zeros_like(fn)
    want[:n] = [0, 1, 0]
    want[n:2 * n] = [0, -1, 0]
    want[2 * n:] = np.stack([mid[2 * n:, 0] - cen[0], np.zeros(2 * n), mid[2 * n:, 2] - cen[1]], 1)
    flip = np.sum(fn * want, 1) < 0
    idx[flip] = idx[flip][:, ::-1]
    uv = np.stack([pos[:, 0] / w + 0.5, pos[:, 2] / h + 0.47], 1)
    return Part(pos, uv, idx, weld=False)


def offset_profile(prof, d):
    """Offset a (r, y) profile along its outward 2-D normal (for profiles that go up the outside)."""
    p = np.asarray(prof, np.float64)
    tng = np.gradient(p, axis=0)
    nrm = nrmz(np.stack([tng[:, 1], -tng[:, 0]], 1))
    return p + nrm * d


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


# --------------------------------------------------------------------------------------------- figure ----
HEAD_CY, HEAD_RY, HEAD_RX, HEAD_RZ = 1.682, 0.118, 0.1, 0.112
BODY_SZ = 0.64
TORSO = np.array([(0, 0.93), (0.13, 0.935), (0.145, 0.97), (0.148, 1.03), (0.152, 1.1), (0.162, 1.18), (0.172, 1.26),
                  (0.178, 1.33), (0.178, 1.39), (0.168, 1.43), (0.145, 1.46), (0.11, 1.48), (0.07, 1.492), (0, 1.5)])
PELVIS = np.array([(0, 0.83), (0.09, 0.835), (0.14, 0.86), (0.163, 0.9), (0.168, 0.95), (0.16, 1.0), (0.145, 1.04),
                   (0, 1.06)])
NECK = np.array([(0, 1.47), (0.05, 1.47), (0.052, 1.5), (0.051, 1.55), (0.048, 1.6), (0, 1.6)])


def interp_r(prof, y):
    y = np.asarray(y, np.float64)
    r = np.interp(y, prof[:, 1], prof[:, 0])
    return np.where((y < prof[0, 1]) | (y > prof[-1, 1]), 0.0, r)


def body_r(y):
    return np.maximum(interp_r(TORSO, y), interp_r(PELVIS, y))


def head_profile(rings=30):
    p = np.linspace(0, math.pi, rings + 1)
    f = np.sin(p) * (0.86 + 0.14 * (1 - np.cos(p)) / 2)          # narrower at the chin, fuller at the crown
    f[0] = f[-1] = 0.0
    return np.stack([f, HEAD_CY - HEAD_RY * np.cos(p)], 1)


def chest_point(r_of_y, theta, y, off=0.0):
    r = float(r_of_y(np.array([y]))[0])
    a, b = r + off, r * BODY_SZ + off
    point = np.array([a * math.sin(theta), y, b * math.cos(theta)])
    normal = nrmz(np.array([math.sin(theta) / a, 0.0, math.cos(theta) / b]))
    return point, normal


def arm_pose(role, side):
    """Shoulder, elbow, wrist, hand direction and palm normal for side +1 (figure's left, +X) or -1."""
    sh = (side * 0.183, 1.42, -0.005)
    if role == 'host':          # open hands: forearms forward, palms up
        return sh, (side * 0.25, 1.14, 0.05), (side * 0.39, 1.02, 0.23), (side * 0.6, -0.04, 0.8), (side * 0.15, 1.0, 0.0)
    if role == 'omega':         # hands held together in front, palms facing
        return sh, (side * 0.235, 1.12, 0.03), (side * 0.15, 0.975, 0.2), (-side * 0.7, -0.15, 0.6), (-side, 0.35, 0.0)
    el, wr = (side * 0.232, 1.135, -0.02), (side * 0.252, 0.88, 0.025)
    d = np.subtract(wr, el) + [0, 0, 0.05]
    return sh, el, wr, tuple(d), (-side, 0.0, 0.12)


def hand(wrist, d, pn, side):
    M = frame(d, pn)
    w, dd, pp = M[:, 0], M[:, 1], M[:, 2]
    wrist = np.asarray(wrist, np.float64)
    parts = [ellipsoid(wrist + dd * 0.08, 0.043, 0.085, 0.024, segs=20, rings=12, M=M)]
    thumb_side = -side * w
    td = nrmz(dd * 0.75 + thumb_side * 0.55 + pp * 0.25)
    parts.append(ellipsoid(wrist + dd * 0.045 + thumb_side * 0.036 + pp * 0.012, 0.015, 0.036, 0.014, segs=14,
                           rings=8, M=frame(td, pp)))
    return parts


def jacket_profile():
    ys = np.linspace(0.95, 1.478, 30)
    outer = offset_profile(np.stack([body_r(ys), ys], 1), 0.014)
    r0 = outer[0, 0]
    hem = [(0.0, 0.815), (0.15, 0.815), (r0 + 0.004, 0.82), (r0 + 0.002, 0.88)]
    collar = [(0.085, 1.497), (0.072, 1.502), (0.07, 1.545), (0.063, 1.553), (0.05, 1.549)]
    return np.vstack([hem, outer, collar])


ROBE = np.array([(0.0, 0.075), (0.3, 0.075), (0.335, 0.08), (0.34, 0.1), (0.31, 0.35), (0.27, 0.6), (0.225, 0.85),
                 (0.188, 1.0), (0.182, 1.1), (0.186, 1.22), (0.19, 1.32), (0.19, 1.4), (0.176, 1.45), (0.13, 1.482),
                 (0.085, 1.5), (0.07, 1.53), (0.066, 1.57), (0.05, 1.575), (0.04, 1.565)])
ROBE_SZ = 0.7
TALL_COLLAR = np.array([(0.05, 1.465), (0.072, 1.465), (0.074, 1.5), (0.078, 1.58), (0.08, 1.615), (0.076, 1.622),
                        (0.068, 1.618), (0.064, 1.58), (0.06, 1.5), (0.056, 1.47), (0.05, 1.465)])


def assemble(role):
    """Meshes for one role, in a 1.8 m frame (omega is scaled to 2.1 m afterwards). Returns ({material: [Part]}, halo
    parts or None, sockets)."""
    M = {k: [] for k in ('body', 'garment', 'shell', 'visor', 'trim', 'boot', 'emblem')}
    hp = head_profile()
    M['shell'].append(lathe(hp, 48, sx=HEAD_RX, sz=HEAD_RZ))
    head_r = lambda y: np.interp(y, hp[:, 1], hp[:, 0])
    A = 1.75
    M['visor'].append(surface_band(
        head_r, HEAD_RX, HEAD_RZ, -A, A, 48, 10, lambda th: HEAD_CY + 0.005 + 0.004 * np.cos(th), 0.028,
        lambda th, s: 0.009 * (1 - s * s) ** 0.35 * smoothstep(0.0, 0.35, A - np.abs(th)) - 0.003,
        lambda th, s: ((th + A) / (2 * A), (1 - s) / 2)))
    M['body'].append(lathe(NECK, 24))

    robe = role == 'omega'
    if role == 'specialist':
        M['garment'].append(lathe(jacket_profile(), 48, sz=BODY_SZ))
        M['trim'].append(torus(0.192, 0.007, 48, 8, sz=BODY_SZ * 1.02).xform(None, (0, 0.822, 0)))
    elif robe:
        M['garment'].append(lathe(ROBE, 56, sz=ROBE_SZ))
        M['trim'].append(torus(0.338, 0.011, 56, 8, sz=ROBE_SZ).xform(None, (0, 0.088, 0)))
    else:
        M['body'].append(lathe(TORSO, 48, sz=BODY_SZ))
        M['body'].append(lathe(PELVIS, 48, sz=BODY_SZ))
        rb = float(body_r(np.array([1.02]))[0])
        M['trim'].append(torus(rb + 0.004, 0.011, 48, 8, sz=BODY_SZ).xform(None, (0, 1.02, 0)))

    # neckline
    if role == 'coordinator':
        M['garment'].append(lathe(TALL_COLLAR, 40))
        M['trim'].append(torus(0.165, 0.016, 56, 10, sz=0.72).xform(rot_x(0.12), (0, 1.49, 0.0)))
        p, n = np.array([0.0, 1.49 - 0.165 * 0.72 * math.sin(0.12), 0.165 * 0.72 * math.cos(0.12) + 0.012]), [0, -0.12, 1]
        M['emblem'].append(place(puck(0.03, 0.007), p, n))
    elif role in ('host', 'liaison', 'alignment'):
        M['trim'].append(torus(0.058, 0.011, 40, 8, sz=0.92).xform(None, (0, 1.497, 0)))

    # arms and hands
    for side in (1, -1):
        sh, el, wr, d, pn = arm_pose(role, side)
        upper = 'garment' if role in ('specialist', 'omega') else 'body'
        fore = 'garment' if role == 'specialist' else 'body'
        gu = 0.006 if upper == 'garment' else 0.0
        gf = 0.006 if fore == 'garment' else 0.0
        M[upper].append(ellipsoid(sh, 0.058 + gu, 0.058 + gu, 0.058 + gu, segs=20, rings=12))
        M[upper].append(limb(sh, el, 0.05 + gu, 0.042 + gu))
        M[fore].append(limb(el, wr, 0.041 + gf, 0.034 + gf))
        M['shell'].extend(hand(wr, d, pn, side))
        fd = nrmz(np.subtract(wr, el))
        if role == 'specialist':
            M['trim'].append(torus(0.04, 0.008, 28, 8).xform(rot_to(fd), np.asarray(wr) - fd * 0.012))
        if robe:   # bell sleeve over the forearm, open at the wrist
            L = float(np.linalg.norm(np.subtract(wr, el)))
            bell = [(0.048, -0.02), (0.056, 0.0), (0.066, L * 0.5), (0.08, L + 0.02), (0.083, L + 0.03),
                    (0.077, L + 0.032), (0.068, L + 0.015), (0.056, L * 0.5), (0.044, 0.0), (0.048, -0.02)]
            M['garment'].append(tube(el, wr, np.array(bell), segs=28))

    # legs and feet
    for side in (1, -1):
        hip, knee, ankle = (side * 0.092, 0.9, 0.0), (side * 0.1, 0.5, 0.012), (side * 0.105, 0.095, -0.005)
        if not robe:
            M['body'].append(limb(hip, knee, 0.078, 0.056, segs=22, cap=5, mid=7))
            M['body'].append(limb(knee, ankle, 0.054, 0.037, segs=22, cap=5, mid=7))
        foot = ellipsoid((side * 0.105, 0.032, 0.045), 0.046, 0.058, 0.122, segs=24, rings=14)
        foot.pos[:, 1] = np.maximum(foot.pos[:, 1], 0.0)
        M['boot'].append(foot)

    # role marks
    if role == 'specialist':
        jp = jacket_profile()
        jr = lambda y: np.interp(y, jp[2:-1, 1], jp[2:-1, 0])
        p, n = chest_point(jr, 0.5, 1.33)
        M['emblem'].append(place(puck(0.026, 0.006), p - n * 0.002, n))
    elif role == 'host':
        p, n = chest_point(body_r, 0.45, 1.335)
        M['emblem'].append(place(puck(0.02, 0.005), p - n * 0.0015, n))
    elif role == 'liaison':
        yc = lambda th: 1.2 + 0.19 * np.sin(th)
        per = max(1, int(round(0.85 / TILE)))
        M['garment'].append(surface_band(
            body_r, 1.0, BODY_SZ, -math.pi, math.pi, 96, 6, yc, 0.042,
            lambda th, s: 0.013 * (1 - s * s) ** 0.3 - 0.003,
            lambda th, s: ((th + math.pi) / TAU * per, (1 - s) / 2 * (0.084 / TILE))))
        th = 0.6
        p, n = chest_point(body_r, th, float(yc(th)), off=0.008)
        M['emblem'].append(place(puck(0.03, 0.007), p, n))
    elif role == 'alignment':
        y = 1.285
        r = float(body_r(np.array([y]))[0])
        a, b = r, r * BODY_SZ
        bend = lambda x: b * (np.sqrt(np.clip(1 - (x / a) ** 2, 0, 1)) - 1)
        M['emblem'].append(place(shield_plate(0.11, 0.13, 0.008, bend), (0, y, b - 0.002), (0, 0, 1)))
    elif robe:
        M['emblem'].append(place(puck(0.032, 0.007), (0, 1.40, 0.19 * ROBE_SZ - 0.002), (0, 0, 1)))

    halo = [torus(0.135, 0.0105, 64, 10)] if robe else None
    sockets = {'voice': [0.0, HEAD_CY - 0.02, HEAD_RZ + 0.02], 'nameplate': [0.0, 1.8 + (0.32 if robe else 0.18), 0.0]}
    if robe:
        sockets['halo'] = [0.0, 1.905, -0.015]
    return {k: v for k, v in M.items() if v}, halo, sockets


# ------------------------------------------------------------------------------------------- textures ----
def jpeg(arr, q=88):
    b = io.BytesIO()
    Image.fromarray(arr).save(b, 'JPEG', quality=q, optimize=True)
    return b.getvalue()


def png(img):
    b = io.BytesIO()
    img.save(b, 'PNG', optimize=True)
    return b.getvalue()


def to8(a):
    return (np.clip(a, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def fabric_maps(N=2048, T=16):
    """Plain-weave fabric, tileable: baseColor (2048, neutral light grey), tangent-space normal (2048, weave + seam
    grooves + stitches along the tile edges, where lathe UV seams fall) and ORM (1024: occlusion, roughness, metallic)."""
    rng = np.random.default_rng(SEED)
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    col, row = (xx // T).astype(np.int32), (yy // T).astype(np.int32)
    fx, fy = (xx % T) / T, (yy % T) / T
    prof = lambda f: np.sin(np.pi * f) ** 0.6
    warp_up = 0.5 + 0.5 * np.cos(np.pi * (yy / T - 0.5) + np.pi * col)
    weft_up = 0.5 + 0.5 * np.cos(np.pi * (xx / T - 0.5) + np.pi * row + np.pi)
    hw = prof(fx) * (0.35 + 0.65 * warp_up)
    hf = prof(fy) * (0.35 + 0.65 * weft_up)
    H = np.maximum(hw, hf)
    on_warp = hw >= hf
    tv_w = rng.normal(0, 1, N // T).astype(np.float32)[col]
    tv_f = rng.normal(0, 1, N // T).astype(np.float32)[row]
    slub = rng.normal(0, 1, (N // T, N // T)).astype(np.float32)[row, col]
    mottle = np.zeros((N, N), np.float32)
    for _ in range(6):
        kx, ky = rng.integers(1, 5, 2)
        ph = rng.uniform(0, TAU)
        mottle += np.cos(TAU * (kx * xx + ky * yy) / N + ph).astype(np.float32) / 6
    thread = np.where(on_warp, tv_w, tv_f)
    # seams on the tile edges (u = 0 and v = 0), with a running stitch either side
    dx = np.minimum(xx, N - 1 - xx)
    dy = np.minimum(yy, N - 1 - yy)
    groove = np.maximum(smoothstep(4.0, 0.0, dx), smoothstep(4.0, 0.0, dy))
    stitch_x = (np.abs(dx - 11) < 1.6) & (((yy // 10) % 2) == 0)
    stitch_y = (np.abs(dy - 11) < 1.6) & (((xx // 10) % 2) == 0)
    stitch = (stitch_x | stitch_y).astype(np.float32)
    Hs = H * (1 - 0.8 * groove) - 0.6 * groove + 0.55 * stitch + 0.04 * slub * H
    base = 0.785 + 0.075 * (H - 0.6) + 0.012 * thread + 0.008 * slub + 0.012 * mottle
    base = np.where(on_warp, base, base * 0.975) - 0.10 * groove + 0.05 * stitch
    rgb = np.stack([base * 0.995, base, base * 1.01], -1)
    k = 2.2
    gx = (np.roll(Hs, -1, 1) - np.roll(Hs, 1, 1)) * 0.5
    gy = (np.roll(Hs, -1, 0) - np.roll(Hs, 1, 0)) * 0.5
    n = np.stack([-gx * k, gy * k, np.ones_like(gx)], -1)
    n /= np.linalg.norm(n, axis=-1, keepdims=True)
    H2 = Hs.reshape(N // 2, 2, N // 2, 2).mean((1, 3))
    s2 = slub.reshape(N // 2, 2, N // 2, 2).mean((1, 3))
    g2 = groove.reshape(N // 2, 2, N // 2, 2).mean((1, 3))
    ao = 1.0 - 0.42 * np.clip(1 - H2, 0, 1) ** 2 - 0.25 * g2
    rough = 0.8 + 0.1 * np.clip(1 - H2, 0, 1) + 0.02 * s2
    orm = np.stack([ao, rough, np.zeros_like(ao)], -1)
    return {
        'fabric_base': (jpeg(to8(rgb)), 'image/jpeg', N, N, 'body fabric baseColor (neutral light grey, woven)'),
        'fabric_normal': (jpeg(to8(n * 0.5 + 0.5), 90), 'image/jpeg', N, N, 'body fabric normal (weave + seams)'),
        'fabric_orm': (jpeg(to8(orm)), 'image/jpeg', N // 2, N // 2, 'body fabric ORM (R occlusion, G roughness, B metallic)'),
    }


def visor_maps(N=1024):
    yy, xx = np.mgrid[0:N, 0:N].astype(np.float32)
    u, v = (xx + 0.5) / N, (yy + 0.5) / N
    glint = np.exp(-((v - 0.28) / 0.07) ** 2) * smoothstep(0.0, 0.3, u) * smoothstep(0.0, 0.3, 1 - u)
    scan = 1.0 - 0.06 * (((yy // 4) % 2) == 0)
    edge = 0.6 + 0.4 * smoothstep(0.0, 0.12, u) * smoothstep(0.0, 0.12, 1 - u)
    base = np.stack([0.022 + 0.0 * u, 0.032 + 0.0 * u, 0.05 + 0.0 * u], -1) * (scan * edge)[..., None]
    base = base + (glint * 0.16)[..., None] * np.array([0.8, 0.9, 1.0], np.float32)
    window = smoothstep(0.06, 0.24, u) * smoothstep(0.06, 0.24, 1 - u)
    bar = np.exp(-((v - 0.5) / 0.055) ** 2) * window
    em = np.clip(0.07 * window + bar * (0.95 + 0.05 * np.cos(TAU * 24 * u)) * scan, 0, 1)
    return {
        'visor_base': (jpeg(to8(base)), 'image/jpeg', N, N, 'visor baseColor (glossy dark glass)'),
        'visor_emissive': (jpeg(to8(np.stack([em, em, em], -1))), 'image/jpeg', N, N, 'visor emissive (light bar)'),
    }


FIELD, RIM, MARK, ACCENT = (24, 34, 58), (198, 202, 212), (234, 208, 148), (118, 186, 206)


def emblem_map(role, N=1024):
    """Abstract role mark on a navy field with a silver rim: geometric shapes only, no text, no real logos."""
    S = 2 * N
    img = Image.new('RGB', (S, S), RIM)
    d = ImageDraw.Draw(img)
    P = lambda x, y: (x * S, y * S)
    W = lambda f: max(1, int(round(f * S)))
    def circ(cx, cy, r, **kw):
        d.ellipse([P(cx - r, cy - r), P(cx + r, cy + r)], **kw)
    if role == 'alignment':
        o = shield_outline()
        poly = [P(x + 0.5, z + 0.47) for x, z in o]
        d.polygon(poly, fill=RIM)
        c = np.array([0.5, 0.47 + 0.02])
        inner = [P(*(c + (np.array([x + 0.5, z + 0.47]) - c) * 0.88)) for x, z in o]
        d.polygon(inner, fill=FIELD)
        # a level beam resting on a fulcrum, a pan hanging from each end: balance, drawn as plain geometry
        d.line([P(0.22, 0.34), P(0.78, 0.34)], fill=MARK, width=W(0.04))
        d.line([P(0.5, 0.34), P(0.5, 0.60)], fill=MARK, width=W(0.035))
        d.polygon([P(0.5, 0.58), P(0.39, 0.74), P(0.61, 0.74)], fill=MARK)
        for x in (0.25, 0.75):
            d.line([P(x, 0.34), P(x - 0.07, 0.50)], fill=MARK, width=W(0.014))
            d.line([P(x, 0.34), P(x + 0.07, 0.50)], fill=MARK, width=W(0.014))
            d.chord([P(x - 0.1, 0.42), P(x + 0.1, 0.58)], 0, 180, fill=ACCENT)
    else:
        circ(0.5, 0.5, 0.47, fill=FIELD)
        circ(0.5, 0.5, 0.43, outline=RIM, width=W(0.012))
        if role == 'specialist':
            hexa = lambda r: [P(0.5 + r * math.cos(math.pi / 6 + k * math.pi / 3), 0.5 + r * math.sin(math.pi / 6 + k * math.pi / 3)) for k in range(6)]
            d.polygon(hexa(0.30), outline=MARK, width=W(0.045))
            d.polygon(hexa(0.10), fill=ACCENT)
            for a in (-90, 30, 150):
                ar = math.radians(a)
                d.line([P(0.5 + 0.1 * math.cos(ar), 0.5 + 0.1 * math.sin(ar)), P(0.5 + 0.27 * math.cos(ar), 0.5 + 0.27 * math.sin(ar))], fill=MARK, width=W(0.03))
        elif role == 'coordinator':
            pts = [(0.5 + 0.24 * math.cos(math.radians(a)), 0.5 + 0.24 * math.sin(math.radians(a))) for a in (-90, 30, 150)]
            for i in range(3):
                d.line([P(*pts[i]), P(*pts[(i + 1) % 3])], fill=MARK, width=W(0.03))
            for x, y in pts:
                circ(x, y, 0.07, fill=MARK)
            circ(0.5, 0.5, 0.06, outline=ACCENT, width=W(0.025))
        elif role == 'omega':
            for r, w in ((0.30, 0.04), (0.19, 0.03)):
                d.arc([P(0.5 - r, 0.5 - r), P(0.5 + r, 0.5 + r)], 125, 415, fill=MARK, width=W(w))
            circ(0.5, 0.2, 0.045, fill=ACCENT)
            circ(0.5, 0.5, 0.05, fill=MARK)
        elif role == 'host':
            r = 0.26
            d.arc([P(0.5 - r, 0.46 - r), P(0.5 + r, 0.46 + r)], 15, 165, fill=MARK, width=W(0.05))
            circ(0.5, 0.40, 0.075, fill=ACCENT)
        elif role == 'liaison':
            yy, xx = np.mgrid[0:S, 0:S].astype(np.float32) / S
            m = (np.hypot(xx - 0.41, yy - 0.5) < 0.2) & (np.hypot(xx - 0.59, yy - 0.5) < 0.2)
            a = np.array(img)
            a[m] = ACCENT
            img = Image.fromarray(a)
            d = ImageDraw.Draw(img)
            for cx in (0.41, 0.59):
                d.ellipse([P(cx - 0.2, 0.3), P(cx + 0.2, 0.7)], outline=MARK, width=W(0.035))
    return {'emblem': (png(img.resize((N, N), Image.LANCZOS)), 'image/png', N, N, f'{role} emblem baseColor (abstract mark)')}


# ------------------------------------------------------------------------------------------ materials ----
def material_defs(role):
    garment = {'specialist': [0.42, 0.47, 0.55], 'coordinator': [0.30, 0.36, 0.52], 'omega': [0.93, 0.92, 0.89],
               'liaison': [0.64, 0.50, 0.32]}.get(role, [0.6, 0.6, 0.62])
    omega = role == 'omega'
    fabric = lambda name, rgb: {'name': name, 'tex': ['fabric_base', 'fabric_normal', 'fabric_orm'], 'mat': {
        'pbrMetallicRoughness': {'baseColorFactor': [*rgb, 1.0], 'baseColorTexture': 'fabric_base',
                                 'metallicRoughnessTexture': 'fabric_orm', 'metallicFactor': 1.0, 'roughnessFactor': 1.0},
        'normalTexture': 'fabric_normal', 'occlusionTexture': 'fabric_orm'}}
    plain = lambda name, rgb, metal, rough, **kw: {'name': name, 'tex': [], 'mat': {
        'pbrMetallicRoughness': {'baseColorFactor': [*rgb, 1.0], 'metallicFactor': metal, 'roughnessFactor': rough}, **kw}}
    visor_em = [1.0, 0.86, 0.58] if omega else [0.36, 0.64, 0.74]
    defs = {
        'body': fabric('AV_Fabric_Body', [0.9, 0.91, 0.93]),
        'garment': fabric('AV_Fabric_Garment', garment),
        'shell': plain('AV_Shell', [0.92, 0.92, 0.94], 0.0, 0.32),
        'trim': plain('AV_Trim', [0.8, 0.76, 0.66], 0.85, 0.3),
        'boot': plain('AV_Boot', [0.16, 0.17, 0.19], 0.15, 0.55),
        'visor': {'name': 'AV_Visor', 'tex': ['visor_base', 'visor_emissive'], 'mat': {
            'pbrMetallicRoughness': {'baseColorFactor': [1.0, 1.0, 1.0, 1.0], 'baseColorTexture': 'visor_base',
                                     'metallicFactor': 0.0, 'roughnessFactor': 0.07},
            'emissiveTexture': 'visor_emissive', 'emissiveFactor': visor_em,
            **({'extensions': {'KHR_materials_emissive_strength': {'emissiveStrength': 2.5}}} if omega else {})}},
        'emblem': {'name': 'AV_Emblem', 'tex': ['emblem'], 'mat': {
            'pbrMetallicRoughness': {'baseColorFactor': [1.0, 1.0, 1.0, 1.0], 'baseColorTexture': 'emblem',
                                     'metallicFactor': 0.35, 'roughnessFactor': 0.38}}},
        'halo': plain('AV_Halo', [1.0, 0.95, 0.82], 0.0, 0.4, emissiveFactor=[1.0, 0.86, 0.55],
                      extensions={'KHR_materials_emissive_strength': {'emissiveStrength': 3.0}}),
    }
    return defs


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


def build_role(role, shared_tex):
    groups, halo, sockets = assemble(role)
    scale = HEIGHT.get(role, 1.8) / 1.8
    defs = material_defs(role)
    tex_all = dict(shared_tex, **emblem_map(role))
    order = [k for k in ('body', 'garment', 'shell', 'visor', 'trim', 'boot', 'emblem') if k in groups]
    mats = order + (['halo'] if halo else [])
    images = []
    for m in mats:
        for t in defs[m]['tex']:
            if t not in images:
                images.append(t)
    B = Bin()
    img_json = []
    for t in images:
        blob, mime = tex_all[t][0], tex_all[t][1]
        img_json.append({'name': t, 'bufferView': B.view(blob), 'mimeType': mime})
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
        return {'name': defs[m]['name'], **d}

    stats = {'triangles': 0, 'vertices': 0, 'min': np.full(3, np.inf), 'max': np.full(3, -np.inf)}

    def mesh_from(group_items, xf_scale, offset=None):
        prims = []
        for m, parts in group_items:
            tex = bool(defs[m]['tex'])
            tan = 'normalTexture' in defs[m]['mat']
            fin = [finalize(p, tan) for p in parts]
            pos = np.vstack([f['pos'] for f in fin]) * xf_scale
            nrm = np.vstack([f['nrm'] for f in fin])
            uv = np.vstack([f['uv'] for f in fin])
            offs = np.cumsum([0] + [len(f['pos']) for f in fin])[:-1]
            idx = np.vstack([f['idx'] + o for f, o in zip(fin, offs)])
            nv = len(pos)
            idx = idx.astype(np.uint16 if nv < 65535 else np.uint32).reshape(-1)
            attrs = {'POSITION': B.accessor(pos, 'VEC3', True), 'NORMAL': B.accessor(nrm, 'VEC3')}
            if tex:
                attrs['TEXCOORD_0'] = B.accessor(uv, 'VEC2')
            if tan:
                attrs['TANGENT'] = B.accessor(np.vstack([f['tan'] for f in fin]), 'VEC4')
            prims.append({'attributes': attrs, 'indices': B.accessor(idx, 'SCALAR'), 'material': mats.index(m), 'mode': 4})
            world = pos + (offset if offset is not None else 0.0)
            stats['triangles'] += len(idx) // 3
            stats['vertices'] += nv
            stats['min'] = np.minimum(stats['min'], world.min(0))
            stats['max'] = np.maximum(stats['max'], world.max(0))
            if m == 'visor':
                stats['visor_z'] = float(world[:, 2].mean())
            if offset is None:
                stats['body_top'] = max(stats.get('body_top', 0.0), float(world[:, 1].max()))
        return prims

    label = role.capitalize()
    name = f'Avatar · {label}'
    meshes = [{'name': name, 'primitives': mesh_from([(m, groups[m]) for m in order], scale)}]
    root = {'name': name, 'mesh': 0, 'extras': {
        'role': role, 'generator': GENERATOR, 'synthetic': True, 'note': NOTE,
        'height_m': HEIGHT.get(role, 1.8), 'units': 'metres', 'up': '+Y', 'facing': '+Z', 'rig': None,
        'tint_targets': ['AV_Fabric_Body', 'AV_Fabric_Garment'],
        'sockets': {k: [round(v * scale, 4) for v in p] for k, p in sockets.items()},
    }}
    nodes = [root]
    if halo:
        t = [round(v * scale, 4) for v in sockets['halo']]
        tilt = -0.26
        hname = f'Avatar · {label} · Halo'
        meshes.append({'name': hname, 'primitives': mesh_from([('halo', halo)], scale, offset=np.array(t))})
        root['children'] = [1]
        nodes.append({'name': hname, 'mesh': 1, 'translation': t,
                      'rotation': [math.sin(tilt / 2), 0.0, 0.0, math.cos(tilt / 2)],
                      'extras': {'part': 'halo', 'note': 'floating ring; a viewer may spin it about its local +Y'}})
    used_ext = sorted({e for m in mats for e in defs[m]['mat'].get('extensions', {})})
    doc = {
        'asset': {'version': '2.0', 'generator': GENERATOR, 'extras': {
            'authorship': 'independently-generated-procedural-geometry', 'externalGeometryImported': False,
            'synthetic': True, 'note': NOTE}},
        **({'extensionsUsed': used_ext} if used_ext else {}),
        'scene': 0, 'scenes': [{'name': name, 'nodes': [0]}],
        'nodes': nodes, 'meshes': meshes, 'materials': [mat_json(m) for m in mats],
        'samplers': [{'magFilter': 9729, 'minFilter': 9987, 'wrapS': 10497, 'wrapT': 10497}],
        'textures': [{'sampler': 0, 'source': i} for i in range(len(images))],
        'images': img_json,
        'accessors': B.accessors, 'bufferViews': B.views, 'buffers': [{'byteLength': 0}],
    }
    B.data += b'\0' * ((4 - len(B.data) % 4) % 4)
    doc['buffers'][0]['byteLength'] = len(B.data)
    glb = glb_bytes(doc, B.data)
    info = {
        'role': role, 'file': f'{role}.glb', 'node': name, 'bytes': len(glb), 'triangles': stats['triangles'],
        'vertices': stats['vertices'], 'height_m': HEIGHT.get(role, 1.8),
        'bounds': {'min': [round(float(v), 4) for v in stats['min']], 'max': [round(float(v), 4) for v in stats['max']]},
        'materials': [defs[m]['name'] for m in mats],
        'textures': [{'use': tex_all[t][4], 'width': tex_all[t][2], 'height': tex_all[t][3], 'mimeType': tex_all[t][1]} for t in images],
        'extensionsUsed': used_ext,
        'sha256': hashlib.sha256(glb).hexdigest(),
    }
    info['figure_top_m'] = round(stats['body_top'], 4)
    return glb, info, {'visor_z': stats.get('visor_z', 0.0), 'names': [n['name'] for n in nodes], 'extras': root['extras']}


def build_all():
    shared = dict(fabric_maps())
    shared.update(visor_maps())
    outputs, infos, evals = {}, [], {}
    for role in ROLES:
        glb, info, probe = build_role(role, shared)
        outputs[f'{role}.glb'] = glb
        infos.append(info)
        evals[role] = role_evals(info, probe)
    index = {
        'schemaVersion': 'worldforge-avatar-glbs/0.1', 'generator': GENERATOR, 'synthetic': True, 'note': NOTE,
        'units': 'metres', 'up': '+Y', 'facing': '+Z', 'feet_at_y': 0.0, 'rig': 'none (static, rig-free)',
        'tinting': 'textures are neutral light grey; tint per world by multiplying the baseColorFactor of the '
                   'AV_Fabric_Body / AV_Fabric_Garment materials (brand hue: worlds/generated/teams/<slug>.json .brand.hue)',
        'card_refs': 'worldforge/build.mjs AVATAR_DIR/AVATAR_ROLES; agent cards -> specialist.glb, omega cards -> omega.glb',
        'validation': f'{OUT_REL}/validation.json',
        'totals': {'roles': len(infos), 'triangles': sum(i['triangles'] for i in infos), 'bytes': sum(i['bytes'] for i in infos)},
        'roles': infos,
        'sha256': {i['file']: i['sha256'] for i in infos},
    }
    outputs['index.json'] = (json.dumps(index, indent=1, ensure_ascii=False) + '\n').encode('utf-8')
    return outputs, index, evals


# ---------------------------------------------------------------------------------------------- evals ----
def role_evals(info, probe):
    tex = {t['use'].split(' (')[0]: (t['width'], t['height']) for t in info['textures']}
    want_h = info['height_m']
    return {
        'triangles_in_range': TRI_RANGE[0] <= info['triangles'] <= TRI_RANGE[1],
        'feet_at_y0': abs(info['bounds']['min'][1]) < 1e-4,
        'height': abs(info['figure_top_m'] - want_h) < 0.03,
        'faces_plus_z': probe['visor_z'] > 0.05,
        'names_fit': all(len(n) <= NAME_LIMIT and n.startswith('Avatar · ') for n in probe['names']),
        'extras': probe['extras'].get('synthetic') is True and probe['extras'].get('generator') == GENERATOR
                  and probe['extras'].get('note') == NOTE and probe['extras'].get('role') == info['role'],
        'under_4mb': info['bytes'] < MAX_BYTES,
        'textures': tex.get('body fabric baseColor') == (2048, 2048) and tex.get('body fabric normal') == (2048, 2048)
                    and tex.get('body fabric ORM') == (1024, 1024) and tex.get('visor baseColor') == (1024, 1024)
                    and all(v == (1024, 1024) for k, v in tex.items() if 'emblem' in k) and any('emblem' in k for k in tex),
    }


def validate(paths):
    """Khronos glTF-Validator over the written GLBs (node, tools/gltf-validator). Returns the parsed report."""
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
        rep = report['files'][f]
        files[f] = {'sha256': hashlib.sha256(outputs[f]).hexdigest(), **rep}
    return {'schemaVersion': 'worldforge-avatar-glbs-validation/0.1', 'validator': report['validator'], 'files': files}


def validation_failures(vdoc, outputs):
    """Roles whose validation record is missing, stale (hash mismatch) or not clean (errors/warnings)."""
    bad, stale = [], []
    for role in ROLES:
        f = f'{role}.glb'
        rec = (vdoc or {}).get('files', {}).get(f)
        if not rec or rec.get('sha256') != hashlib.sha256(outputs[f]).hexdigest():
            stale.append(f)
        elif rec.get('errors') or rec.get('warnings'):
            bad.append(f)
    return bad, stale


# -------------------------------------------------------------------------------------------- preview ----
def render_preview(out_path, w=1800, h=1320):
    script = r"""
const { spawn } = require('child_process'); const fs = require('fs'); const os = require('os'); const path = require('path');
const [chromePath, url, out, w, h] = process.argv.slice(1);
const port = 9347;
const tmp = fs.mkdtempSync(path.join(os.tmpdir(), 'wf-avatars-'));
const chrome = spawn(chromePath, ['--headless=new', `--remote-debugging-port=${port}`, `--user-data-dir=${path.join(tmp, 'p')}`,
  '--use-gl=angle', '--use-angle=swiftshader-webgl', '--enable-unsafe-swiftshader', '--hide-scrollbars', `--window-size=${w},${h}`, 'about:blank'], { stdio: 'ignore' });
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const watchdog = setTimeout(() => { console.error('preview failed: watchdog (page not ready in 280 s; is the jsDelivr CDN reachable?)');
  chrome.kill(); try { fs.rmSync(tmp, { recursive: true, force: true }); } catch {} process.exit(1); }, 280000);
(async () => {
  let targets;
  for (let i = 0; i < 100 && !targets; i++) { await sleep(200); targets = await fetch(`http://127.0.0.1:${port}/json/list`).then((r) => r.json()).catch(() => null); }
  const ws = new WebSocket(targets.find((t) => t.type === 'page').webSocketDebuggerUrl);
  await new Promise((r) => ws.addEventListener('open', r, { once: true }));
  let id = 0; const pending = new Map();
  ws.addEventListener('message', (e) => { const m = JSON.parse(e.data); pending.get(m.id)?.(m); pending.delete(m.id); });
  const send = (method, params = {}) => new Promise((r) => { pending.set(++id, r); ws.send(JSON.stringify({ id, method, params })); });
  await send('Emulation.setDeviceMetricsOverride', { width: Number(w), height: Number(h), deviceScaleFactor: 1, mobile: false });
  await send('Page.enable'); await send('Page.navigate', { url });
  let state = null;
  for (let i = 0; i < 480; i++) {
    await sleep(500);
    const r = await send('Runtime.evaluate', { expression: 'JSON.stringify({ready: window.__avatarsReady === true, error: window.__avatarsError || null})', returnByValue: true });
    state = JSON.parse(r.result?.result?.value ?? '{}');
    if (state.ready || state.error) break;
  }
  if (!state?.ready) throw new Error('page not ready: ' + JSON.stringify(state));
  await sleep(400);
  const shot = await send('Page.captureScreenshot', { format: 'jpeg', quality: 88 });
  fs.writeFileSync(out, Buffer.from(shot.result.data, 'base64'));
  console.log(`${out}: ${(fs.statSync(out).size / 1e3).toFixed(0)} KB`);
  ws.close();
})().catch((e) => { console.error('preview failed:', e.message); process.exitCode = 1; })
  .finally(async () => { clearTimeout(watchdog); chrome.kill(); await sleep(800); try { fs.rmSync(tmp, { recursive: true, force: true }); } catch {} });
"""
    try:
        r = subprocess.run(['node', '-e', script, CHROME, PREVIEW_URL, str(out_path), str(w), str(h)], capture_output=True,
                           text=True, timeout=330)
    except subprocess.TimeoutExpired:
        return False, 'preview failed: timed out'
    return r.returncode == 0, (r.stdout + r.stderr).strip()


def read_glb(blob):
    """Minimal GLB reader for the files this script writes: nodes (TRS), meshes, accessors, materials, images."""
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
    def quat(q):
        x, y, z, w = q
        return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                         [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                         [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])
    prims = []
    def walk(ni, R, T):
        n = doc['nodes'][ni]
        Rl = quat(n['rotation']) if 'rotation' in n else np.eye(3)
        Tl = np.array(n.get('translation', [0.0, 0.0, 0.0]))
        R2, T2 = R @ Rl, R @ Tl + T
        if 'mesh' in n:
            for p in doc['meshes'][n['mesh']]['primitives']:
                m = doc['materials'][p['material']]
                prims.append({'pos': acc(p['attributes']['POSITION']) @ R2.T + T2, 'nrm': acc(p['attributes']['NORMAL']) @ R2.T,
                              'uv': acc(p['attributes']['TEXCOORD_0']) if 'TEXCOORD_0' in p['attributes'] else None,
                              'idx': acc(p['indices']).reshape(-1, 3), 'mat': m})
        for c in n.get('children', []):
            walk(c, R2, T2)
    for ni in doc['scenes'][doc['scene']]['nodes']:
        walk(ni, np.eye(3), np.zeros(3))
    return doc, prims, img


def srgb_lin(c):
    return np.asarray(c, np.float64) ** 2.2


def rasterize(P, D, tri, W, H):
    """Fragments of triangles (pixel coords, y down; D larger = nearer) resolved by a z-buffer.
    Returns (pixel index, triangle index, barycentrics) for the nearest fragment of each covered pixel."""
    x, y = P[tri, 0], P[tri, 1]
    ix0 = np.clip(np.ceil(x.min(1) - 0.5), 0, W - 1).astype(np.int64)
    ix1 = np.clip(np.floor(x.max(1) - 0.5), 0, W - 1).astype(np.int64)
    iy0 = np.clip(np.ceil(y.min(1) - 0.5), 0, H - 1).astype(np.int64)
    iy1 = np.clip(np.floor(y.max(1) - 0.5), 0, H - 1).astype(np.int64)
    bw, bh = ix1 - ix0 + 1, iy1 - iy0 + 1
    keep = (bw > 0) & (bh > 0) & (x.max(1) > 0) & (x.min(1) < W) & (y.max(1) > 0) & (y.min(1) < H)
    p2 = lambda v: (1 << np.ceil(np.log2(np.maximum(v, 1))).astype(np.int64))
    kb = p2(bw) * 4096 + p2(bh)
    frags = []
    for key in np.unique(kb[keep]):
        sel = np.nonzero(keep & (kb == key))[0]
        gw, gh = int(key // 4096), int(key % 4096)
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
    pix, dep, tid, b0, b1, b2 = (np.concatenate(z) for z in zip(*frags))
    order = np.lexsort((-dep, pix))
    first = np.r_[True, pix[order][1:] != pix[order][:-1]]
    win = order[first]
    return pix[win], tid[win], np.stack([b0[win], b1[win], b2[win]], 1)


def shade(prims_all, sel_tri, bary, tri_prim, tri_local, V):
    """Lambert + Blinn-Phong + a sky/ground environment term; emissive added; linear light out."""
    out = np.zeros((len(sel_tri), 3))
    lights = [(nrmz(np.array([0.55, 0.75, 0.6])), 2.3, np.array([1.0, 0.97, 0.92])),
              (nrmz(np.array([-0.75, 0.3, 0.45])), 0.55, np.array([0.8, 0.88, 1.0])),
              (nrmz(np.array([-0.35, 0.45, -0.85])), 1.5, np.array([0.75, 0.85, 1.0]))]
    sky, ground = np.array([0.42, 0.46, 0.55]), np.array([0.10, 0.09, 0.085])
    for pi_, pr in enumerate(prims_all):
        m = tri_prim[sel_tri] == pi_
        if not m.any():
            continue
        t = pr['idx'][tri_local[sel_tri[m]]]
        b = bary[m]
        N = nrmz(np.einsum('ki,kij->kj', b, pr['nrm'][t]))
        mat, pbr = pr['mat'], pr['mat']['pbrMetallicRoughness']
        alb = np.broadcast_to(srgb_lin(pbr['baseColorFactor'][:3]), N.shape).copy()
        if 'baseColorTexture' in pbr and pr['uv'] is not None:
            uv = np.einsum('ki,kij->kj', b, pr['uv'][t])
            tex = pr['tex'][pbr['baseColorTexture']['index']]
            alb = alb * sample(tex, uv)
        em = np.zeros_like(N)
        if 'emissiveFactor' in mat:
            k = mat.get('extensions', {}).get('KHR_materials_emissive_strength', {}).get('emissiveStrength', 1.0)
            em = np.broadcast_to(np.array(mat['emissiveFactor']) * k, N.shape).copy()
            if 'emissiveTexture' in mat and pr['uv'] is not None:
                em = em * sample(pr['tex'][mat['emissiveTexture']['index']], np.einsum('ki,kij->kj', b, pr['uv'][t]))
        metal, rough = pbr.get('metallicFactor', 1.0), pbr.get('roughnessFactor', 1.0)
        if 'metallicRoughnessTexture' in pbr:
            metal, rough = 0.0, 0.85
        f0 = 0.04 * (1 - metal) + alb * metal
        hemi = ground + (sky - ground) * (0.5 + 0.5 * N[:, 1:2])
        col = alb * (1 - metal) * hemi * 0.9
        s = float(np.clip(2.0 / max(rough, 0.05) ** 4 - 2.0, 2.0, 2048.0))
        for L, I, lc in lights:
            ndl = np.clip(N @ L, 0, None)[:, None]
            Hh = nrmz(L + V)
            spec = f0 * ((s + 8) / (8 * math.pi)) * np.clip(N @ Hh, 0, None)[:, None] ** s * ndl
            col += I * lc * (alb * (1 - metal) * ndl / math.pi * 2.2 + spec * 0.6)
        R = 2 * np.sum(N * V, 1, keepdims=True) * N - V
        env = ground + (sky * 1.6 - ground) * smoothstep(-0.2, 0.6, R[:, 1:2])
        fres = f0 + (1 - f0) * (1 - np.clip(np.sum(N * V, 1, keepdims=True), 0, 1)) ** 5 * (1 - rough) ** 2
        col += env * fres * (1 - rough * 0.85)
        out[m] = col + em
    return out


def sample(tex, uv):
    """Bilinear, wrapping; tex is a float linear-light array (h, w, 3)."""
    h, w = tex.shape[:2]
    x = uv[:, 0] * w - 0.5
    y = uv[:, 1] * h - 0.5
    x0, y0 = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = (x - x0)[:, None], (y - y0)[:, None]
    g = lambda yy, xx: tex[yy % h, xx % w]
    return (g(y0, x0) * (1 - fx) * (1 - fy) + g(y0, x0 + 1) * fx * (1 - fy) + g(y0 + 1, x0) * (1 - fx) * fy
            + g(y0 + 1, x0 + 1) * fx * fy)


def preview_raster(out_path, W=1800, rowH=620, head=70, ss=2):
    """Contact sheet of the GLBs as written: a numpy software raster (no normal maps, no shadows; a look, not a
    render target). Top row front three-quarter, bottom row back three-quarter."""
    from PIL import ImageFont
    files = [(r, (OUT / f'{r}.glb').read_bytes()) for r in ROLES]
    figs = []
    for r, blob in files:
        doc, prims, img = read_glb(blob)
        cache = {}
        for pr in prims:
            pr['tex'] = {}
            for key in ('baseColorTexture', 'emissiveTexture'):
                ref = pr['mat']['pbrMetallicRoughness'].get(key) if key == 'baseColorTexture' else pr['mat'].get(key)
                if ref is None:
                    continue
                i = doc['textures'][ref['index']]['source']
                if i not in cache:
                    im = img(i)
                    name = doc['images'][i]['name']
                    size = 64 if name.startswith('fabric') else 128      # mip level: fabric threads are sub-pixel here
                    cache[i] = srgb_lin(np.asarray(im.resize((size, size), Image.BOX), np.float64) / 255.0)
                pr['tex'][ref['index']] = cache[i]
        figs.append((r, len(blob), sum(len(p['idx']) for p in prims), prims))
    pitch = math.radians(8.0)
    spacing = 1.25
    scale = W / (spacing * len(ROLES)) * ss
    Wss, Hss = W * ss, rowH * ss
    V = np.array([0.0, math.sin(pitch), math.cos(pitch)])
    rows = []
    for yaw in (0.42, math.pi + 0.42):
        Rz = np.array([[math.cos(yaw), 0, math.sin(yaw)], [0, 1, 0], [-math.sin(yaw), 0, math.cos(yaw)]])
        allp, alln, D, P, tri, tri_prim, tri_local, prims_all = [], [], [], [], [], [], [], []
        base = 0
        for i, (r, _, _, prims) in enumerate(figs):
            cx = (i - (len(figs) - 1) / 2) * spacing
            for pr in prims:
                pos = pr['pos'] @ Rz.T + [cx, 0, 0]
                q = dict(pr, nrm=pr['nrm'] @ Rz.T)
                sx = pos[:, 0]
                sy = pos[:, 1] * math.cos(pitch) - pos[:, 2] * math.sin(pitch)
                dz = pos[:, 1] * math.sin(pitch) + pos[:, 2] * math.cos(pitch)
                px = np.stack([sx * scale + Wss / 2, Hss - 70 * ss - sy * scale], 1)
                # back-face cull in screen space (front faces are counter-clockwise with y up)
                a = pr['idx']
                e = ((px[a[:, 1], 0] - px[a[:, 0], 0]) * (px[a[:, 0], 1] - px[a[:, 2], 1])
                     - (px[a[:, 2], 0] - px[a[:, 0], 0]) * (px[a[:, 0], 1] - px[a[:, 1], 1]))
                front = np.nonzero(e > 0)[0]
                P.append(px); D.append(dz)
                tri.append(a[front] + base); tri_local.append(front); tri_prim.append(np.full(len(front), len(prims_all)))
                prims_all.append(q)
                base += len(pos)
        P, D = np.vstack(P), np.concatenate(D)
        tri, tri_local, tri_prim = np.vstack(tri), np.concatenate(tri_local), np.concatenate(tri_prim)
        pix, tid, bary = rasterize(P, D, tri, Wss, Hss)
        col = shade(prims_all, tid, bary, tri_prim, tri_local, V)
        col = 1.0 - np.exp(-col * 1.15)                                  # filmic-ish shoulder
        img = np.zeros((Hss * Wss, 3))
        yy = np.linspace(0, 1, Hss)[:, None, None]
        bg = (np.array([0.115, 0.135, 0.17]) * (1 - yy) + np.array([0.06, 0.07, 0.09]) * yy) ** 1.0
        bg = np.broadcast_to(bg, (Hss, Wss, 3)).copy()
        gy = Hss - 70 * ss
        X, Yg = np.meshgrid(np.arange(Wss), np.arange(Hss))
        for i in range(len(figs)):
            cx = (i - (len(figs) - 1) / 2) * spacing * scale + Wss / 2
            d = ((X - cx) / (0.42 * scale)) ** 2 + ((Yg - gy) / (0.42 * scale * math.sin(pitch) * 1.6)) ** 2
            bg *= (1 - 0.55 * np.exp(-d * 2.2))[..., None]
        img[:] = bg.reshape(-1, 3)
        img[pix] = col ** (1 / 2.2)
        rows.append(Image.fromarray(to8(img.reshape(Hss, Wss, 3))).resize((W, rowH), Image.LANCZOS))
    sheet = Image.new('RGB', (W, head + 2 * rowH), (16, 19, 25))
    for k, im in enumerate(rows):
        sheet.paste(im, (0, head + k * rowH))
    d = ImageDraw.Draw(sheet)
    font = lambda s: ImageFont.load_default(size=s)
    d.text((24, 16), 'WorldForge agent avatars', fill=(236, 239, 244), font=font(26))
    d.text((24, 46), 'Synthetic, stylised figures for agents: agents, not people. Static and rig-free. '
           'numpy software raster of the GLBs as written (no normal maps, no shadows).', fill=(150, 160, 175), font=font(15))
    for k, name in enumerate(('front three-quarter', 'back three-quarter')):
        d.text((24, head + k * rowH + 14), name.upper(), fill=(140, 150, 166), font=font(14))
    for i, (r, nbytes, ntri, _) in enumerate(figs):
        cx = W / 2 + (i - (len(figs) - 1) / 2) * spacing * scale / ss
        for k in range(2):
            y0 = head + (k + 1) * rowH - 54
            d.text((cx, y0), r, fill=(236, 239, 244), font=font(19), anchor='mt')
            if k == 0:
                d.text((cx, y0 + 26), f'{ntri:,} tris · {nbytes / 1e6:.2f} MB · {HEIGHT.get(r, 1.8)} m', fill=(150, 160, 175), font=font(13), anchor='mt')
    b = io.BytesIO()
    sheet.save(b, 'JPEG', quality=90, optimize=True)
    out_path.write_bytes(b.getvalue())
    return f'{out_path.relative_to(ROOT)}: {W}x{head + 2 * rowH}, {len(b.getvalue()) / 1e3:.0f} KB (software raster)'


# ----------------------------------------------------------------------------------------------- main ----
def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--check', action='store_true', help='rebuild in memory; exit 1 if outputs on disk differ')
    ap.add_argument('--preview', action='store_true', help='also render preview.jpg (numpy software raster of the GLBs)')
    ap.add_argument('--preview-chrome', action='store_true', help='render preview.jpg from preview.html in headless Chrome '
                    '(needs the :8080 server and the jsDelivr CDN)')
    ap.add_argument('--no-validate', action='store_true', help='skip the Khronos validator run (write mode)')
    args = ap.parse_args()

    outputs, index, evals = build_all()
    tri = index['totals']['triangles']
    vpath = OUT / 'validation.json'

    if args.check:
        stale = [f for f, b in outputs.items() if not (OUT / f).exists() or (OUT / f).read_bytes() != b]
        try:
            vdoc = json.loads(vpath.read_text())
        except (OSError, ValueError):
            vdoc = None
        bad_v, stale_v = validation_failures(vdoc, outputs)
        failing = sorted({r for r, e in evals.items() if not all(e.values())} | {f[:-4] for f in bad_v})
        if stale:
            print(f'avatars STALE: {len(stale)} of {len(outputs)} files differ from their generator (first: {stale[0]})')
            sys.exit(1)
        if stale_v:
            print(f'avatars STALE: validation.json is behind {len(stale_v)} GLBs (first: {stale_v[0]}); run {GENERATOR}')
            sys.exit(1)
        print(f'avatars current: {len(ROLES)} roles, {tri} triangles, {len(failing)} failing')
        sys.exit(1 if failing else 0)

    OUT.mkdir(parents=True, exist_ok=True)
    for f, b in outputs.items():
        (OUT / f).write_bytes(b)
    bad_v, stale_v = [], []
    if not args.no_validate:
        report = validate([OUT / f'{r}.glb' for r in ROLES])
        vdoc = validation_doc(report, outputs)
        vpath.write_text(json.dumps(vdoc, indent=1, ensure_ascii=False) + '\n')
        bad_v, stale_v = validation_failures(vdoc, outputs)
        for f, rec in vdoc['files'].items():
            codes = sorted({m['code'] for m in rec['messages']})
            print(f'  {f}: {rec["errors"]} errors, {rec["warnings"]} warnings, {rec["infos"]} infos, {rec["hints"]} hints'
                  + (f' [{", ".join(codes)}]' if codes else ''))
    for i in index['roles']:
        e = evals[i['role']]
        print(f'  {i["file"]}: {i["triangles"]} tris, {i["vertices"]} verts, {i["bytes"] / 1e6:.2f} MB, '
              f'top {i["bounds"]["max"][1]:.3f} m' + ('' if all(e.values()) else f'  FAIL {[k for k, v in e.items() if not v]}'))
    if args.preview_chrome:
        ok, msg = render_preview(OUT / 'preview.jpg')
        print(f'  preview: {msg}')
    elif args.preview:
        print(f'  preview: {preview_raster(OUT / "preview.jpg")}')
    failing = sorted({r for r, e in evals.items() if not all(e.values())} | {f[:-4] for f in bad_v + stale_v})
    print(f'avatars {"RED" if failing else "GREEN"}: {len(ROLES)} roles, {tri} triangles, '
          f'{index["totals"]["bytes"] / 1e6:.1f} MB, {len(failing)} failing' + (f' ({", ".join(failing)})' if failing else ''))
    sys.exit(1 if failing else 0)


if __name__ == '__main__':
    main()

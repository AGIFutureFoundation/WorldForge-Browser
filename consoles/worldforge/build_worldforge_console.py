#!/usr/bin/env python3
"""WorldForge team console: one static page over the 41 WorldForge worlds, each in its own team skin.

    python3 consoles/worldforge/build_worldforge_console.py           # -> consoles/worldforge/index.html, runs the console evals
    python3 consoles/worldforge/build_worldforge_console.py --check   # exit 1 if index.html is behind what it reads

What it reads (and nothing else):
  worldforge/out/index.json                 network totals, the broken-case discrimination results, the world order
  worldforge/out/<slug>/cards.json          the Master Cards: world -> plaza, gate, council (+3 empty human seats),
                                            Omega Steward, zones -> agents, each with its permission matrix
  worldforge/out/<slug>/manifest.json       counts, the world's WorldForge evals and its gate table (1.1 ... 1.4)
  worlds/generated/teams/<slug>.json        .brand only: the team skin (hue, mark, lockup)
  worldforge/out/avatars/index.json         the avatar registry, IF it exists (another builder writes it); its
                                            presence and content are part of the stamp, so the page goes STALE the
                                            moment it appears and must be rebuilt
  worldforge/out/assets/avatars/*.glb       names only: whether each avatar model is on disk yet
  projects/index.json                       the private repository names, so they can be kept off the page

The source stamp is the sha256 of this builder plus the canonical JSON of exactly the slice above that the page is
built from (volatile *_at / time keys in the avatar registry dropped, ISO times masked). worldforge's own sourceHash
is not part of it, so a WorldForge rebuild that changes no card does not stale the console.

Every name, role, zone and persona on the page is copied from those files with its citation. Agents operate, people
govern: rights held by the steward quorum render as "held". Omega Stewards are "defined, not seated". Voices are
synthetic and play only once the hive has voiced the line; nothing plays until a person presses play. No model runs.
"""
import glob
import hashlib
import html
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "index.html")
BUILDER = "consoles/worldforge/build_worldforge_console.py"
WF = "worldforge/out"
INDEX = "worldforge/out/index.json"
AVATARS = "worldforge/out/avatars/index.json"
AVATAR_GLBS = "worldforge/out/assets/avatars"
TEAMS = "worlds/generated/teams"
PROJECTS = "projects/index.json"
STAMP_TAG = "worldforge-console-source-stamp"
MAX_BYTES = 2 * 1024 * 1024
# The house rule: these six are held for a 2-of-3 Steward Council and no agent card may ever hold them.
HOUSE_RESERVED = ["governance.final_vote", "charter.amend", "treasury.transfer", "proposal.enact", "windfall.distribute", "steward.appoint"]
HUMAN_ONLY_RIGHTS = ["delegate", "transfer", "govern"]
COMMON = {"cardId", "kind", "parentCardId", "owner", "umbrella", "permissions", "reserved_for_humans", "displayName", "volum"}
VOLATILE_KEY = re.compile(r"^(run_at|generated|generated_at|built_at|updated_at|timestamp|time|mtime)$|_at$", re.I)
ISO_TIME = re.compile(r"\d{4}-\d\d-\d\dT\d\d:\d\d(?::\d\d(?:\.\d+)?)?(?:Z|[+-]\d\d:?\d\d)?")
EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
WALLET = re.compile(r"\b0x[a-fA-F0-9]{40}\b")
KEYLIKE = re.compile(r"\b(?:sk-[A-Za-z0-9_-]{16,}|sk_live_[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|xox[bap]-[A-Za-z0-9-]{10,})")
AUDIO_PATH = "agents/hive/voices/{world}/{line}.mp4"


# ------------------------------------------------------------------------------------------- helpers ----
def J(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return json.load(f)


def E(s):
    return html.escape("" if s is None else str(s), quote=True)


def scrub(x):
    if isinstance(x, dict):
        return {k: scrub(v) for k, v in x.items() if not VOLATILE_KEY.search(str(k))}
    if isinstance(x, list):
        return [scrub(v) for v in x]
    if isinstance(x, str):
        return ISO_TIME.sub("<time>", x)
    return x


def label_of(c):
    if c.get("name"):
        return c["name"]
    dn = c.get("displayName") or c.get("cardId")
    return re.sub(r" \u00b7 Powered by AGI Corp$", "", dn)


def script_json(obj):
    s = json.dumps(obj, ensure_ascii=False, separators=(",", ":"), sort_keys=True)
    return s.replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")


# -------------------------------------------------------------------------------- avatar registry ----
def first(d, keys):
    for k in keys:
        if isinstance(d, dict) and d.get(k) not in (None, "", [], {}):
            return d[k]
    return None


def norm_gates(g):
    """name -> ok pairs from a dict ({name: bool | {ok: bool}}) or a list ([{name|id|check, ok|pass|passed}])."""
    out = []
    if isinstance(g, dict):
        for k, v in g.items():
            ok = v if isinstance(v, bool) else first(v, ["ok", "pass", "passed", "result"]) if isinstance(v, dict) else None
            out.append([str(k), bool(ok) if ok is not None else None])
    elif isinstance(g, list):
        for v in g:
            if isinstance(v, dict):
                ok = first(v, ["ok", "pass", "passed", "result"])
                if ok is None and "ok" in v:
                    ok = v["ok"]
                out.append([str(first(v, ["name", "id", "check", "gate"]) or "?"), bool(ok) if ok is not None else None])
            elif isinstance(v, str):
                out.append([v, None])
    return out


def avatar_rows(doc):
    """Flatten whatever list of avatar rows the registry carries; the schema is not fixed yet, so this is tolerant."""
    rows = []
    if isinstance(doc, list):
        return [r for r in doc if isinstance(r, dict)]
    if not isinstance(doc, dict):
        return rows
    for k in ("avatars", "agents", "rows", "entries", "cards"):
        if isinstance(doc.get(k), list):
            rows += [r for r in doc[k] if isinstance(r, dict)]
    ws = doc.get("worlds")
    items = ws.items() if isinstance(ws, dict) else ((None, w) for w in ws) if isinstance(ws, list) else []
    for slug, w in items:
        inner = w if isinstance(w, list) else first(w, ["avatars", "agents", "rows", "cards"]) if isinstance(w, dict) else None
        if not isinstance(inner, list):
            continue  # a per-world summary (counts, checks), not a list of rows
        wslug = slug or (first(w, ["slug", "world"]) if isinstance(w, dict) else None)
        for r in inner or []:
            if isinstance(r, dict):
                rows.append(dict(r, _world=wslug))
    return rows


def read_avatars(path, card_index, worlds):
    """The avatar registry (worldforge/avatars.mjs, schema worldforge-avatars/0.1) plus its persona-prompt gate results
    (prompts/<slug>.json next to it, gates only; the prompt text stays in those files). card_index: {cardId: (world,
    name, swarm)}. Rows of another shape are still read through the tolerant field lookups above."""
    if not os.path.exists(path):
        return {"present": False, "path": AVATARS}, []
    files = [AVATARS]
    try:
        with open(path, encoding="utf-8") as f:
            doc = json.load(f)
    except (OSError, ValueError) as e:
        with open(path, "rb") as f:
            raw = hashlib.sha256(f.read()).hexdigest()[:16]
        return {"present": True, "path": AVATARS, "error": f"could not parse ({type(e).__name__}); it may still be being written", "raw": raw}, files
    doc = scrub(doc)
    pdir = os.path.join(os.path.dirname(path), "prompts")
    gates_by_id, prompt_files = {}, 0
    for slug in worlds:
        pf = os.path.join(pdir, f"{slug}.json")
        if not os.path.exists(pf):
            continue
        try:
            with open(pf, encoding="utf-8") as f:
                pd = json.load(f)
        except (OSError, ValueError):
            continue
        prompt_files += 1
        files.append(f"{os.path.dirname(AVATARS)}/prompts/{slug}.json")
        for pr in pd.get("prompts") or []:
            g = pr.get("gates")
            if isinstance(g, dict) and "passed" in g:
                gates_by_id[pr.get("id")] = {"passed": g.get("passed"), "of": g.get("of"), "failed": list(g.get("failed") or []), "chars": pr.get("chars")}
            elif g is not None:
                ng = norm_gates(g)
                gates_by_id[pr.get("id")] = {"passed": sum(1 for x in ng if x[1]), "of": len(ng), "failed": [x[0] for x in ng if x[1] is False], "chars": pr.get("chars")}
    by_swarm = {v[2]: k for k, v in card_index.items() if v[2]}
    by_world, unmatched = {}, 0
    for r in avatar_rows(doc):
        cid = first(r, ["cardId", "card_id", "card"])
        b = r.get("binding") if isinstance(r.get("binding"), dict) else {}
        sw = first(r, ["swarm", "swarm_id"]) or b.get("swarm")
        if isinstance(cid, str) and cid not in card_index:
            unmatched += 1
            continue
        if not cid and r.get("role") != "coordinator" and isinstance(sw, str):
            cid = by_swarm.get(sw)
        world = first(r, ["world", "slug", "_world"]) or (card_index[cid][0] if cid else None)
        if world not in worlds:
            unmatched += 1
            continue
        intro = first(r, ["intro", "intro_line", "introLine", "greeting", "line", "lines"])
        if isinstance(intro, list):
            intro = intro[0] if intro else None
        intro_from = intro.get("from") if isinstance(intro, dict) else None
        if isinstance(intro, dict):
            intro = first(intro, ["text", "line"])
        mp = b.get("metaprompt")
        mp = (f'{mp.get("file")}#{mp.get("id")}' if mp.get("id") else mp.get("file")) if isinstance(mp, dict) else mp
        voice = r.get("voice") if isinstance(r.get("voice"), dict) else {}
        pid_ = r.get("persona_prompt_id")
        g = gates_by_id.get(pid_)
        if g is None and first(r, ["gates", "persona_gates", "prompt_gates", "persona_prompt_gates", "evals", "checks"]) is not None:
            ng = norm_gates(first(r, ["gates", "persona_gates", "prompt_gates", "persona_prompt_gates", "evals", "checks"]))
            g = {"passed": sum(1 for x in ng if x[1]), "of": len(ng), "failed": [x[0] for x in ng if x[1] is False], "chars": None}
        model = first(r, ["model_ref", "model", "glb"]) or ((r.get("avatar") or {}).get("model_ref") if isinstance(r.get("avatar"), dict) else None)
        by_world.setdefault(world, []).append({
            "aid": r.get("avatarId"), "cid": cid if cid else None, "name": r.get("name"), "role": r.get("role"),
            "role_text": r.get("role_text") if not cid else None, "zone": r.get("zone"), "source": r.get("source") if not cid else None,
            "model": model if isinstance(model, str) else None, "tint": r.get("tint_hue"), "swarm": sw if isinstance(sw, str) else None,
            "hive": b.get("hive"), "metaprompt": mp if isinstance(mp, str) else None,
            "intro": intro if isinstance(intro, str) else None, "intro_from": intro_from if isinstance(intro_from, str) else None,
            "voice": voice.get("id") if isinstance(voice.get("id"), str) else (r.get("voice") if isinstance(r.get("voice"), str) else None),
            "vstatus": voice.get("status") if isinstance(voice.get("status"), str) else (voice.get("status_rule") and "checked at view time"),
            "seat": r.get("seat_status"), "pid": pid_, "gates": g,
            "reserved_ok": not any(str(h).startswith("agents") for k in HUMAN_ONLY_RIGHTS for h in ((r.get("permissions") or {}).get(k) or [])),
        })
    wchecks = {}
    for w in doc.get("worlds") or [] if isinstance(doc, dict) else []:
        if isinstance(w, dict) and w.get("slug") in worlds and isinstance(w.get("checks"), dict):
            wchecks[w["slug"]] = {"checks": w["checks"], "failed": list(w.get("failed") or [])}
    top = doc if isinstance(doc, dict) else {}
    tot = top.get("totals") if isinstance(top.get("totals"), dict) else {}
    digest = hashlib.sha256(json.dumps(doc, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    rows_n = sum(len(v) for v in by_world.values())
    return {"present": True, "path": AVATARS, "schema": str(top.get("schemaVersion") or ""), "generator": str(top.get("generator") or ""),
            "digest": digest, "totals": {k: v for k, v in tot.items() if isinstance(v, (int, float)) and not isinstance(v, bool)},
            "honesty": [h for h in (top.get("honesty") or []) if isinstance(h, str)], "checks": [c for c in (top.get("checks") or []) if isinstance(c, str)],
            "broken": [sum(1 for x in top.get("broken") or [] if isinstance(x, dict) and x.get("ok")), len(top.get("broken") or [])],
            "byWorld": by_world, "worldChecks": wchecks, "matched": rows_n, "unmatched": unmatched, "promptFiles": prompt_files,
            "gated": sum(1 for v in by_world.values() for x in v if x["gates"])}, files


# ---------------------------------------------------------------------------------------------- data ----
def load(avatars_path=None):
    avatars_path = avatars_path or os.path.join(ROOT, AVATARS)
    files = [BUILDER, INDEX, PROJECTS]
    idx = J(INDEX)
    proj = J(PROJECTS)
    private = sorted({n for r in proj["rows"] if r.get("private") for n in (r["repo"], r["name"])}, key=lambda s: (-len(s), s))
    red = {"repo": 0, "email": 0, "wallet": 0, "key": 0}

    def redact(s):
        for n in private:
            s, k = re.subn(re.escape(n), "a private repository", s, flags=re.I)
            red["repo"] += k
        s, k = EMAIL.subn("[email withheld]", s); red["email"] += k
        s, k = WALLET.subn("[address withheld]", s); red["wallet"] += k
        s, k = KEYLIKE.subn("[key withheld]", s); red["key"] += k
        return s

    def deep(x):
        if isinstance(x, dict):
            return {k: deep(v) for k, v in x.items()}
        if isinstance(x, list):
            return [deep(v) for v in x]
        return redact(x) if isinstance(x, str) else x

    perms, perm_ix, rsvs, rsv_ix = [], {}, [], {}

    def pid(p):
        k = json.dumps(p, sort_keys=True)
        if k not in perm_ix:
            perm_ix[k] = len(perms); perms.append(p)
        return perm_ix[k]

    def rid(r):
        k = json.dumps(r, sort_keys=True)
        if k not in rsv_ix:
            rsv_ix[k] = len(rsvs); rsvs.append(r)
        return rsv_ix[k]

    worlds, card_index, issues = [], {}, []
    rights = None
    for row in idx["worlds"]:
        slug = row["slug"]
        cpath, mpath, tpath = f"{WF}/{slug}/cards.json", f"{WF}/{slug}/manifest.json", f"{TEAMS}/{slug}.json"
        files += [cpath, mpath, tpath]
        cd, man = J(cpath), J(mpath)
        team = J(tpath) if os.path.exists(os.path.join(ROOT, tpath)) else {}
        brand = team.get("brand") or {}
        if rights is None:
            rights = cd["rights"]
        elif cd["rights"] != rights:
            issues.append(f"{slug}: rights list differs from the first world's")
        cards = []
        for c in cd["cards"]:
            cc = {"id": c["cardId"], "k": c["kind"], "pa": c["parentCardId"], "n": label_of(c), "dn": c.get("displayName"),
                  "p": pid(c["permissions"]), "r": rid(c.get("reserved_for_humans") or []),
                  "v": [(c.get("volum") or {}).get("center"), (c.get("volum") or {}).get("halfExtents")]}
            if c.get("owner") != cd.get("owner") or c.get("umbrella") != cd.get("umbrella"):
                cc["owner"], cc["umbrella"] = c.get("owner"), c.get("umbrella")
            for k, v in c.items():
                if k not in COMMON:
                    cc[k] = v
            if cc["k"] == "omega" and isinstance(cc.get("voice"), dict):
                for ln in cc["voice"].get("lines") or []:
                    want = AUDIO_PATH.format(world=slug, line=ln.get("id"))
                    if ln.get("audio") != want or not re.fullmatch(r"[a-z]+", str(ln.get("id"))):
                        issues.append(f"{slug}: voice line {ln.get('id')} audio path {ln.get('audio')!r} is not {want}")
                        ln["audio"] = None
            cards.append(cc)
            card_index[c["cardId"]] = (slug, cc["n"], (c.get("binding") or {}).get("swarm") if isinstance(c.get("binding"), dict) else None)
        wc = next((c for c in cd["cards"] if c["kind"] == "world"), cd["cards"][0])
        worlds.append({
            "slug": slug, "name": wc.get("name") or row.get("name"), "tagline": wc.get("tagline"), "status": wc.get("status"),
            "mgmt": wc.get("management_style"), "anchor": wc.get("anchor"), "owner": cd.get("owner"), "umbrella": cd.get("umbrella"),
            "principle": cd.get("principle"), "omega_steward": wc.get("omega_steward"),
            "brand": {"hue": brand.get("hue"), "mark": brand.get("mark"), "lockup": brand.get("lockup"), "source": f"{tpath}#brand" if brand else None},
            "counts": man.get("counts") or {}, "glbBytes": row.get("glbBytes"), "evals": man.get("evals") or {},
            "gates": [[k, v] for k, v in (man.get("gates") or {}).items()], "gaps": list(cd.get("gaps") or []), "cards": cards,
        })
    glbs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, AVATAR_GLBS, "*.glb")))
    av, av_files = read_avatars(avatars_path, card_index, [w["slug"] for w in worlds])
    files += av_files
    data = {"umbrella": idx.get("umbrella"), "owner": idx.get("owner"), "rights": rights or [], "perms": perms, "reserved": rsvs,
            "totals": idx.get("totals") or {}, "broken": idx.get("broken") or [], "worlds": worlds, "avatars": av, "avatarGlbs": glbs,
            "houseReserved": HOUSE_RESERVED}
    data = deep(data)
    return {"data": data, "private": private, "files": files, "redactions": red, "issues": issues, "avatars_path": avatars_path}


def stamp(S):
    h = hashlib.sha256()
    with open(os.path.join(ROOT, BUILDER), "rb") as f:
        h.update(f.read())
    h.update(b"\0")
    h.update(json.dumps({"data": S["data"], "private": S["private"]}, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()[:16]


def stats(D):
    W = D["worlds"]
    cards = [c for w in W for c in w["cards"]]
    bcards = [c for c in cards if c["k"] in ("zone", "council")]
    omegas = [c for c in cards if c["k"] == "omega"]
    avs = [c for c in cards if c["k"] in ("agent", "omega") and (c.get("avatar") or {}).get("model_ref")]
    evals = sum(len(w["evals"]) for w in W)
    failing = sum(1 for w in W for v in w["evals"].values() if not v)
    return {
        "worlds": len(W), "cards": len(cards), "primitives": sum(int(w["counts"].get("primitives", 0)) for w in W),
        "evals": evals, "failing": failing, "broken_ok": sum(1 for b in D["broken"] if b.get("ok")), "broken": len(D["broken"]),
        "bldg_linked": sum(1 for c in bcards if c.get("building")), "bldg_slots": len(bcards),
        "bldg_interior": sum(1 for c in bcards if (c.get("building") or {}).get("interior")),
        "avatars": len(avs), "agents": sum(1 for c in cards if c["k"] == "agent"),
        "omegas": len(omegas), "omega_dns": sum(1 for c in omegas if c.get("status") == "defined, not seated" and c.get("seated_agent") is None),
        "anchored": sum(1 for w in W if (w.get("anchor") or {}).get("lat") is not None),
        "seats": sum(1 for c in cards if c["k"] == "seat"), "seats_empty": sum(1 for c in cards if c["k"] == "seat" and c.get("seated") is None),
        "lines": sum(len((c.get("voice") or {}).get("lines") or []) for c in omegas),
    }


# ---------------------------------------------------------------------------------------------- views ----
ICON_SUN = '<svg id="icoSun" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="4" fill="none" stroke="currentColor" stroke-width="2"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/></svg>'
ICON_MOON = '<svg id="icoMoon" viewBox="0 0 24 24" aria-hidden="true"><path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z" fill="none" stroke="currentColor" stroke-width="2" stroke-linejoin="round"/></svg>'
HONESTY = [
    ("Agents operate; people govern",
     "No agent card holds delegate, transfer or govern. The six reserved actions are held for a 2-of-3 Steward Council, and every council seat is an empty human seat."),
    ("Defined, not seated",
     "Each Omega Steward is a role definition until a person seats an agent. No model runs on this page."),
    ("Synthetic voices",
     "Every voice is synthetic (Kokoro text-to-speech). A line plays only once the hive has voiced it, and nothing plays until you press play."),
    ("Placeholder massing, open gates",
     "Geometry is synthetic. The GLB card tree is verified in JavaScript; the native Sneeze load (1.2n) and a rendered frame (1.4) are still open."),
]


def kpi(label, value, sub, tone=""):
    return f'<div class="kpi {tone}"><div class="kl">{E(label)}</div><div class="kv">{value}</div><div class="ks">{sub}</div></div>'


def nav_button(w):
    fail = sum(1 for v in w["evals"].values() if not v)
    anchored = (w.get("anchor") or {}).get("lat") is not None
    q = " ".join([w["name"] or "", w["slug"], w.get("tagline") or ""]).lower()
    return (f'<button type="button" class="wb" data-world="{E(w["slug"])}" data-q="{E(q)}" style="--h:{E(w["brand"]["hue"])}" aria-current="false">'
            f'<span class="mark" aria-hidden="true">{E(w["brand"]["mark"])}</span><span class="wbt"><b>{E(w["name"])}</b>'
            f'<small>{len(w["cards"])} cards &middot; {"evals ok" if not fail else f"{fail} failing"} &middot; {"anchored" if anchored else "no anchor yet"}</small></span></button>')


CSS = r"""
:root{--h:200;--bg:#070b16;--bg2:#0a1020;--panel:#0e1528;--panel2:#131c34;--line:#233052;--ink:#eaf0ff;--ink2:#9ba8c8;
--ok:#34d399;--warn:#fbbf24;--bad:#fb7185;--info:#7dd3fc;--vio:#c4b5fd;--mag:#f0abfc;
--brand:hsl(var(--h) 72% 60%);--brand-ink:hsl(var(--h) 85% 78%);--brand-dim:hsl(var(--h) 45% 15%);--brand-line:hsl(var(--h) 50% 36%);
--shadow:0 16px 44px rgba(0,0,0,.42);--sans:system-ui,-apple-system,'Segoe UI',Roboto,'Helvetica Neue',Arial,sans-serif;
--mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;color-scheme:dark}
:root[data-theme="light"]{--bg:#f4f6fb;--bg2:#eceff7;--panel:#ffffff;--panel2:#f5f7fc;--line:#d6ddec;--ink:#0d1430;--ink2:#4b5675;
--ok:#047857;--warn:#a85b06;--bad:#be123c;--info:#0369a1;--vio:#6d28d9;--mag:#a21caf;
--brand:hsl(var(--h) 62% 40%);--brand-ink:hsl(var(--h) 70% 28%);--brand-dim:hsl(var(--h) 60% 93%);--brand-line:hsl(var(--h) 45% 72%);
--shadow:0 12px 32px rgba(16,24,64,.09);color-scheme:light}
*{box-sizing:border-box}html,body{margin:0}html{-webkit-text-size-adjust:100%}
body{background:radial-gradient(900px 380px at 6% -6%,hsl(var(--h) 70% 50% / .16),transparent 70%),radial-gradient(760px 360px at 98% 0%,hsl(calc(var(--h) + 60) 70% 50% / .10),transparent 70%),var(--bg);
background-attachment:fixed;color:var(--ink);font:14px/1.55 var(--sans);-webkit-font-smoothing:antialiased;min-height:100vh}
a{color:var(--brand-ink)}code,.mono{font-family:var(--mono);font-size:12px}h1,h2,h3,h4{margin:0}button,select,input{font:inherit;color:inherit}
:focus-visible{outline:2px solid var(--brand);outline-offset:2px}
.sr{position:absolute!important;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
.skip{position:absolute;left:-999px;top:8px;z-index:50;background:var(--panel);padding:8px 12px;border-radius:8px}.skip:focus{left:12px}
.wrap{max-width:1560px;margin:0 auto;padding:0 24px}
.top{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--bg) 84%,transparent);backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);border-bottom:1px solid var(--line)}
.bar{display:flex;align-items:center;gap:12px;min-height:60px;flex-wrap:wrap;padding-top:8px;padding-bottom:8px}
.brand{display:flex;align-items:center;gap:10px;min-width:0;flex:1 1 260px}.brand b{font:800 16px/1.15 var(--sans);white-space:nowrap}
.brand small{display:block;color:var(--ink2);font-size:11.5px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.brand>div{min-width:0}
.mark{flex:none;display:grid;place-items:center;width:34px;height:34px;border-radius:9px;font:800 12px/1 var(--sans);letter-spacing:.02em;color:#fff;
background:linear-gradient(135deg,hsl(var(--h) 72% 48%),hsl(calc(var(--h) + 40) 75% 36%));box-shadow:inset 0 0 0 1px hsl(var(--h) 90% 75% / .35)}
.mark.lg{width:64px;height:64px;border-radius:16px;font-size:20px}
.pick{display:flex;align-items:center;gap:6px;flex:0 1 420px;min-width:0}
.pick select{flex:1;min-width:0;background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:8px 10px}
.ibtn{flex:none;width:36px;height:36px;border-radius:10px;border:1px solid var(--line);background:var(--panel);display:grid;place-items:center;cursor:pointer;font-size:18px;line-height:1}
.ibtn:hover{border-color:var(--brand)}.ibtn svg{width:17px;height:17px}
#icoMoon{display:none}:root[data-theme="light"] #icoSun{display:none}:root[data-theme="light"] #icoMoon{display:block}
.hero{padding:28px 0 8px}
.eyebrow{font:700 11px/1.4 var(--mono);letter-spacing:.12em;text-transform:uppercase;color:var(--brand-ink)}
.hero h1{font:800 clamp(24px,3.8vw,36px)/1.12 var(--sans);letter-spacing:-.015em;margin:8px 0 8px}
.lede{color:var(--ink2);max-width:860px;margin:0;font-size:14.5px}
.honesty{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:10px;margin:16px 0 4px}
.hn{padding:11px 13px;border-radius:12px;background:var(--panel);border:1px solid var(--line);border-left:3px solid var(--brand)}
.hn:nth-child(2){border-left-color:var(--warn)}.hn:nth-child(3){border-left-color:var(--mag)}.hn:nth-child(4){border-left-color:var(--info)}
.hn b{display:block;font-size:13px}.hn p{margin:3px 0 0;color:var(--ink2);font-size:12.5px;line-height:1.45}
.kpis{display:grid;grid-template-columns:repeat(8,minmax(0,1fr));gap:10px;margin:14px 0 18px}
.kpi{padding:12px 13px;border-radius:12px;background:var(--panel);border:1px solid var(--line);position:relative;overflow:hidden;min-width:0}
.kpi:before{content:"";position:absolute;inset:0 0 auto 0;height:2px;background:linear-gradient(90deg,var(--brand),transparent)}
.kl{font:600 10.5px/1.3 var(--sans);color:var(--ink2);text-transform:uppercase;letter-spacing:.06em}
.kv{font:800 24px/1.15 var(--sans);margin:5px 0 3px;font-variant-numeric:tabular-nums}.kv small{font-size:13px;color:var(--ink2);font-weight:600}
.ks{font-size:11.5px;color:var(--ink2);line-height:1.35}.kpi.ok .kv{color:var(--ok)}.kpi.warn .kv{color:var(--warn)}.kpi.bad .kv{color:var(--bad)}
.layout{display:grid;grid-template-columns:270px minmax(0,1fr);gap:16px;align-items:start}
.wl{position:sticky;top:76px;max-height:calc(100vh - 92px);overflow:auto;background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:8px}
.wl input{width:100%;background:var(--panel2);border:1px solid var(--line);border-radius:9px;padding:8px 10px;margin-bottom:6px}
.wb{display:flex;gap:10px;align-items:center;width:100%;text-align:left;padding:7px 8px;border:1px solid transparent;border-radius:10px;background:none;cursor:pointer}
.wb:hover{background:var(--panel2)}.wb[aria-current="true"]{background:hsl(var(--h) 50% 50% / .14);border-color:hsl(var(--h) 60% 55% / .55)}
.wb[hidden]{display:none}.wbt{min-width:0}.wbt b{display:block;font-size:13px;line-height:1.25}.wbt small{display:block;color:var(--ink2);font-size:11px}
#view{min-width:0}#view:focus{outline:none}
.panel{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px;margin:0 0 14px;min-width:0}
.panel>h3{font:700 15px/1.3 var(--sans);margin-bottom:10px;display:flex;align-items:center;gap:8px;flex-wrap:wrap}
.panel>h3 .src{font:500 11px var(--mono);color:var(--ink2);margin-left:auto;overflow-wrap:anywhere}
.wh{display:flex;gap:16px;align-items:center;padding:18px;border-radius:14px;margin-bottom:14px;border:1px solid var(--brand-line);
background:linear-gradient(110deg,var(--brand-dim),var(--panel) 70%)}
.wh-t{min-width:0;flex:1}.wh h2{font:800 clamp(20px,3vw,28px)/1.2 var(--sans);margin:3px 0 4px;display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.wh p{margin:0;color:var(--ink2)}.meta{display:flex;gap:6px 12px;flex-wrap:wrap;margin-top:8px;font-size:12.5px;color:var(--ink2);align-items:center}
.links{display:flex;gap:8px;flex-wrap:wrap;margin-top:12px}
.btn{display:inline-flex;align-items:center;gap:6px;font:600 12.5px var(--sans);padding:7px 13px;border-radius:9px;border:1px solid transparent;cursor:pointer;text-decoration:none;
background:linear-gradient(135deg,hsl(var(--h) 72% 46%),hsl(calc(var(--h) + 40) 72% 40%));color:#fff}
.btn:hover{filter:brightness(1.08)}.btn.ghost{background:transparent;border-color:var(--line);color:var(--ink)}.btn.ghost:hover{border-color:var(--brand)}.btn.sm{padding:4px 10px;font-size:12px}
.wstats{display:grid;grid-template-columns:repeat(auto-fit,minmax(112px,1fr));gap:8px;margin:0 0 14px}
.ws{padding:8px 10px;border-radius:10px;background:var(--panel);border:1px solid var(--line)}.ws span{display:block;font-size:10.5px;color:var(--ink2);text-transform:uppercase;letter-spacing:.05em}
.ws b{font:800 18px/1.3 var(--sans);font-variant-numeric:tabular-nums}
.two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:14px}
.tag{display:inline-block;font:700 10.5px/1.6 var(--mono);padding:0 7px;border-radius:5px;letter-spacing:.03em;white-space:nowrap;vertical-align:middle}
.tag.ok{color:var(--ok);background:color-mix(in srgb,var(--ok) 14%,transparent)}.tag.bad{color:var(--bad);background:color-mix(in srgb,var(--bad) 14%,transparent)}
.tag.open,.tag.miss,.tag.dn,.tag.pend{color:var(--warn);background:color-mix(in srgb,var(--warn) 13%,transparent)}.tag.part{color:var(--info);background:color-mix(in srgb,var(--info) 13%,transparent)}
.tag.st{color:var(--brand-ink);background:hsl(var(--h) 60% 50% / .16)}.tag.gov{color:var(--vio);background:color-mix(in srgb,var(--vio) 14%,transparent)}
.tag.seat{color:var(--vio);border:1px dashed color-mix(in srgb,var(--vio) 55%,transparent)}.tag.bk{color:var(--info);background:color-mix(in srgb,var(--info) 12%,transparent)}
.tw{overflow-x:auto;border:1px solid var(--line);border-radius:10px;max-width:100%}
table{border-collapse:collapse;width:100%;font-size:12.5px}th,td{text-align:left;padding:7px 10px;border-bottom:1px solid var(--line);vertical-align:top}
th{font:600 10.5px var(--sans);color:var(--ink2);text-transform:uppercase;letter-spacing:.05em;background:var(--panel2);white-space:nowrap}tr:last-child td{border-bottom:0}
td.num{font-variant-numeric:tabular-nums;white-space:nowrap}td code{overflow-wrap:anywhere}
.tbar{display:flex;gap:8px;flex-wrap:wrap;align-items:center;margin-bottom:10px}
.legend{display:flex;gap:6px 14px;flex-wrap:wrap;font-size:11.5px;color:var(--ink2);align-items:center}.lg{display:inline-flex;align-items:center;gap:5px}.legend .pc{flex-direction:row;min-width:0;padding:0 5px;line-height:1.6}
.tree,.tree ul{list-style:none;margin:0;padding:0}.tree ul{margin-left:13px;padding-left:12px;border-left:1px dashed var(--line)}.tree ul[hidden]{display:none}
.row{display:flex;flex-wrap:wrap;align-items:center;gap:4px 10px;padding:6px 6px;border-radius:9px}.row:hover{background:var(--panel2)}
.tg{flex:none;width:24px;height:24px;border-radius:7px;border:1px solid var(--line);background:var(--panel2);display:grid;place-items:center;cursor:pointer;padding:0}
.tg svg{width:12px;height:12px;transition:transform .15s}.tg[aria-expanded="true"] svg{transform:rotate(90deg)}.tg.sp{border:0;background:none;cursor:default}
.kt{flex:none;min-width:58px;text-align:center;font:700 10px/1.7 var(--mono);text-transform:uppercase;letter-spacing:.06em;padding:0 6px;border-radius:5px;color:var(--ink2);background:var(--panel2);border:1px solid var(--line)}
.k-world .kt{color:var(--brand-ink);border-color:var(--brand-line)}.k-plaza .kt{color:var(--ink)}.k-gate .kt{color:var(--warn)}
.k-council .kt,.k-seat .kt{color:var(--vio)}.k-omega .kt{color:var(--mag)}.k-zone .kt{color:var(--info)}.k-agent .kt{color:var(--ok)}
.nm{flex:1 1 260px;min-width:0}.nm b{font-size:13px;margin-right:6px}.nm small{display:block;color:var(--ink2);font:11px/1.4 var(--mono);overflow-wrap:anywhere}
.nm .ds{display:block;color:var(--ink2);font-size:12px;line-height:1.4;overflow-wrap:anywhere}
.perm{display:inline-flex;gap:2px;flex:none}
.pc{display:inline-flex;flex-direction:column;align-items:center;min-width:38px;padding:1px 3px;border-radius:5px;font:600 9.5px/1.3 var(--mono);border:1px solid var(--line);color:var(--ink2)}
.pc b{font-size:10.5px;color:var(--ink)}.pc.p{color:var(--ok)}.pc.s{color:var(--info)}.pc.a{color:var(--brand-ink);border-color:var(--brand-line)}
.pc.q{color:var(--warn);background:color-mix(in srgb,var(--warn) 12%,transparent);border-color:color-mix(in srgb,var(--warn) 45%,transparent)}
.cv{flex:none;font-size:12px;white-space:nowrap}
.chips{display:flex;flex-wrap:wrap;gap:6px}
.chip{display:inline-flex;align-items:center;gap:5px;font:600 11.5px/1.5 var(--sans);padding:2px 9px;border-radius:999px;border:1px solid var(--line);background:var(--panel2);max-width:100%;overflow-wrap:anywhere}
.chip.val{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 35%,transparent)}
.chip.lock{font-family:var(--mono);font-weight:600;color:var(--warn);border-radius:7px;background:color-mix(in srgb,var(--warn) 9%,transparent);border-color:color-mix(in srgb,var(--warn) 40%,transparent)}
.kvs{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px}
.kvs div{padding:8px 10px;border-radius:9px;background:var(--panel2);border:1px solid var(--line);min-width:0}.kvs span{display:block;font-size:11px;color:var(--ink2)}.kvs b{overflow-wrap:anywhere;font-weight:600}
h4{font:700 11.5px/1.3 var(--mono);text-transform:uppercase;letter-spacing:.1em;color:var(--brand-ink);margin:14px 0 8px}
.lines{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:8px}
.ln{padding:10px 12px;border-radius:10px;background:var(--panel2);border:1px solid var(--line);min-width:0}
.ln-h{display:flex;align-items:center;gap:8px;flex-wrap:wrap}.ln p{margin:6px 0 8px}.ln audio{width:100%;height:34px}
.synth{font:600 10.5px var(--mono);color:var(--mag)}.vs{font:600 10.5px var(--mono);color:var(--ink2);padding:0 6px;border-radius:5px;border:1px solid var(--line)}.vs.vok{color:var(--ok);border-color:color-mix(in srgb,var(--ok) 45%,transparent)}.vs.vpend{color:var(--warn);border-color:color-mix(in srgb,var(--warn) 45%,transparent)}
.note{color:var(--ink2);border:1px dashed var(--line);border-radius:9px;padding:8px 10px;margin:10px 0 0;font-size:12.5px}
.pend{color:var(--ink2);border:1px dashed var(--warn);border-radius:9px;padding:8px 10px;margin:0 0 10px;font-size:12.5px}
.evs{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:4px 10px}
.evs li{font-size:12px;display:flex;gap:6px;align-items:baseline;min-width:0}.evs li code{overflow-wrap:anywhere}
.evs .ok span{color:var(--ok);font-weight:800}.evs .bad span{color:var(--bad);font-weight:800}.evs .bad code{color:var(--bad)}
.avt th,.bt th{white-space:normal}.nw{white-space:nowrap}
.avt td.who{min-width:170px}.avt td.bind{min-width:180px}.avt td.intro{min-width:220px}.avt td.gt{min-width:90px}.avt td.mdl{min-width:110px}.avt td.mdl .tag{margin-top:3px}
.avt .ds,.bt .ds{display:block;margin-top:3px;color:var(--ink2);font-size:12px;overflow-wrap:anywhere}.avt .ds.mono{font:11px/1.4 var(--mono)}
.bt td.zn{min-width:130px}.bt td code,.avt td code{overflow-wrap:break-word;word-break:normal}
.pl{display:flex;gap:6px;align-items:baseline;min-width:0;line-height:1.5}.pl+.pl{margin-top:2px}.pk{flex:none;width:30px;font:600 10px/1.5 var(--mono);color:var(--ink2);text-transform:uppercase;letter-spacing:.04em}
.bt td.num .pl{justify-content:flex-start}.cvl{display:block;margin-top:4px}
.gaps{margin:0;padding-left:18px}.gaps li{margin:4px 0}.gaps .d{color:var(--ink2)}
.muted{color:var(--ink2)}.s{font-size:12px}
.foot{margin:30px 0 0;border-top:1px solid var(--line);background:var(--bg2)}.foot .wrap{padding-top:20px;padding-bottom:26px}
.foot p{margin:5px 0;color:var(--ink2);font-size:12.5px}
@media (max-width:1180px){.kpis{grid-template-columns:repeat(4,minmax(0,1fr))}.honesty{grid-template-columns:repeat(2,minmax(0,1fr))}.two{grid-template-columns:1fr}}
@media (max-width:900px){.layout{grid-template-columns:1fr}.wl{display:none}}
@media (max-width:640px){.wrap{padding:0 16px}.kpis{grid-template-columns:repeat(2,minmax(0,1fr))}.honesty{grid-template-columns:1fr}
.brand small{display:none}.pick{flex:1 1 100%;order:3}.wh{flex-direction:column;align-items:flex-start;padding:14px}.kv{font-size:20px}
.tree ul{margin-left:6px;padding-left:8px}.nm{flex-basis:100%}.lines{grid-template-columns:1fr}.panel{padding:12px}}
@media (prefers-reduced-motion: reduce){*{transition:none!important}}
"""

JS = r"""
(() => {
  'use strict';
  const D = JSON.parse(document.getElementById('wf-data').textContent);
  const $ = (s, r) => (r || document).querySelector(s);
  const $$ = (s, r) => Array.from((r || document).querySelectorAll(s));
  const esc = (s) => String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const root = document.documentElement;
  const BY = new Map(D.worlds.map((w) => [w.slug, w]));
  const RA = { view: 'V', enter: 'E', build: 'B', operate: 'O', delegate: 'D', transfer: 'T', govern: 'G' };
  const LINE = { greet: 'Greeting', role: 'Role', boundary: 'Boundary', services: 'Services' };
  const UP = '../../';
  const CHEV = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7" fill="none" stroke="currentColor" stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  const viewerUrl = (slug, card) => UP + 'worldforge/viewer.html?world=' + encodeURIComponent(slug) + (card ? '&card=' + encodeURIComponent(card) : '');
  const base = (p) => String(p || '').split('/').pop();
  const tag = (cls, text) => '<span class="tag ' + cls + '">' + esc(text) + '</span>';
  const num = (v) => (v == null ? 'none' : Number(v).toLocaleString('en-US'));
  const px = (v) => (v == null ? 'none' : num(v) + ' px');

  // ---- permissions: one cell per right; a right held by the steward quorum always reads "held"
  function holder(h) {
    if (h.includes('steward-quorum')) return ['held', 'q', 'held for the Steward Council, 2-of-3 quorum'];
    if (h.some((x) => String(x).startsWith('agents'))) return ['stw+agt', 'a', h.join(', ') + ' (agents only in their own zone)'];
    if (h.includes('public')) return ['pub', 'p', h.join(', ')];
    if (h.includes('stewards')) return ['stw', 's', h.join(', ')];
    return [h.length ? h.join('+') : 'none', 'n', h.length ? h.join(', ') : 'nobody'];
  }
  function perms(i) {
    const P = D.perms[i] || {};
    return '<span class="perm">' + D.rights.map((r) => {
      const [code, cls, full] = holder(P[r] || []);
      const t = r + ': ' + full;
      return '<span class="pc ' + cls + '" title="' + esc(t) + '" aria-label="' + esc(t) + '"><b aria-hidden="true">' + esc(RA[r] || r.charAt(0).toUpperCase()) + '</b><span aria-hidden="true">' + esc(code) + '</span></span>';
    }).join('') + '</span>';
  }

  // ---- master card tree
  function chips(c) {
    if (c.k === 'world') return tag('st', c.status || '');
    if (c.k === 'council') return tag('gov', 'people govern') + (c.building ? ' ' + tag('bk', c.building.kind) : '');
    if (c.k === 'seat') return tag('seat', (c.seat_type || 'human') + ' seat \u00b7 ' + (c.seated == null ? 'empty' : 'seated'));
    if (c.k === 'omega') return tag('dn', c.status || 'defined, not seated');
    if (c.k === 'zone') return c.building ? tag('bk', c.building.kind) : tag('miss', 'no building linked');
    return '';
  }
  function desc(c) {
    if (c.k === 'agent') return c.role;
    if (c.k === 'world') return c.tagline;
    if (c.k === 'omega') return (c.omega_id || '') + ' \u00b7 seated agent: ' + (c.seated_agent == null ? 'none' : c.seated_agent);
    return c.purpose || '';
  }
  let uid = 0;
  function row(w, c, kids, open) {
    const id = 'ch' + (++uid);
    const tg = kids ? '<button type="button" class="tg" aria-expanded="' + open + '" aria-controls="' + id + '" aria-label="' + (open ? 'Collapse ' : 'Expand ') + esc(c.n) + '">' + CHEV + '</button>'
      : '<span class="tg sp" aria-hidden="true"></span>';
    const d = desc(c);
    return [id, '<div class="row k-' + esc(c.k) + '">' + tg + '<span class="kt">' + esc(c.k) + '</span><span class="nm"><b>' + esc(c.n) + '</b>' + chips(c)
      + '<small title="' + esc(c.dn || '') + '">' + esc(c.id) + (kids ? ' \u00b7 ' + kids + ' child card' + (kids === 1 ? '' : 's') : '') + '</small>'
      + (d ? '<span class="ds">' + esc(d) + '</span>' : '') + '</span>' + perms(c.p)
      + '<a class="cv" href="' + esc(viewerUrl(w.slug, c.id)) + '" aria-label="' + esc('Card in viewer: ' + c.n) + '">Card in viewer</a></div>'];
  }
  const ORDER = { plaza: 0, gate: 1, council: 2, seat: 3, omega: 4, zone: 5, agent: 6 };
  function tree(w) {
    const kids = new Map();
    w.cards.forEach((c) => { if (c.pa) { if (!kids.has(c.pa)) kids.set(c.pa, []); kids.get(c.pa).push(c); } });
    const node = (c, depth) => {
      const ch = (kids.get(c.id) || []).slice().sort((a, b) => (ORDER[a.k] == null ? 9 : ORDER[a.k]) - (ORDER[b.k] == null ? 9 : ORDER[b.k]));
      const open = depth < 2;
      const [id, r] = row(w, c, ch.length, open);
      if (!ch.length) return '<li>' + r + '</li>';
      return '<li>' + r + '<ul id="' + id + '"' + (open ? '' : ' hidden') + '>' + ch.map((x) => node(x, depth + 1)).join('') + '</ul></li>';
    };
    const known = new Set(w.cards.map((c) => c.id));
    const tops = w.cards.filter((c) => !c.pa || !known.has(c.pa));
    return '<ul class="tree">' + tops.map((c) => node(c, 0)).join('') + '</ul>';
  }
  function legend() {
    return '<div class="legend"><span><b>V</b> view \u00b7 <b>E</b> enter \u00b7 <b>B</b> build \u00b7 <b>O</b> operate \u00b7 <b>D</b> delegate \u00b7 <b>T</b> transfer \u00b7 <b>G</b> govern</span>'
      + '<span class="lg"><span class="pc p">pub</span>public</span><span class="lg"><span class="pc s">stw</span>stewards</span><span class="lg"><span class="pc a">stw+agt</span>stewards, plus agents in their own zone</span>'
      + '<span class="lg"><span class="pc q">held</span>held for the 2-of-3 Steward Council</span></div>';
  }

  // ---- buildings
  function glb(p) { return p ? '<a href="' + esc(UP + p) + '" title="' + esc(p) + '"><code>' + esc(base(p)) + '</code></a>' : '<span class="muted">none</span>'; }
  // one labelled line per part, so the exterior / interior / room GLBs, textures and triangles line up across columns
  const part = (k, v) => '<span class="pl"><span class="pk">' + k + '</span>' + v + '</span>';
  function door(d) {
    if (!d) return '<span class="muted">none</span>';
    return '<span class="pl nw">centre (' + esc((d.centre || []).join(', ')) + ') m</span><span class="pl nw">\u00b1' + esc(d.half_width) + ' m wide \u00b7 ' + esc(d.head) + ' m head</span>';
  }
  function buildings(w) {
    const cs = w.cards.filter((c) => c.k === 'council' || c.k === 'zone');
    const linked = cs.filter((c) => c.building).length;
    const rows = cs.map((c) => {
      const b = c.building;
      const who = '<b>' + esc(c.n) + '</b>' + (c.k === 'council' ? ' ' + tag('gov', 'council') : '');
      if (!b) return '<tr><td class="zn">' + who + '</td><td colspan="5" class="muted">no building linked in my-fabric/worlds/spaces_index.json</td></tr>';
      const res = b.resolution || {}, tri = b.triangles || {};
      return '<tr><td class="zn">' + who + (b.sign ? '<span class="ds">sign \u201c' + esc(b.sign) + '\u201d</span>' : '<span class="ds muted">no sign</span>') + '</td><td>' + esc(b.kind) + '</td><td class="md">'
        + part('ext', glb(b.exterior)) + part('int', glb(b.interior)) + part('room', glb(b.room)) + '</td><td class="num">' + part('ext', px(res.exterior)) + part('int', px(res.interior))
        + '</td><td class="num">' + part('ext', num(tri.exterior)) + part('int', num(tri.interior)) + '</td><td>' + door(b.door) + '</td></tr>';
    }).join('');
    const src = (cs.find((c) => c.building) || {}).building;
    return '<section class="panel" aria-labelledby="hB"><h3 id="hB">Buildings <span class="tag ' + (linked === cs.length ? 'ok' : 'miss') + '">' + linked + ' / ' + cs.length + ' linked</span><span class="src">' + esc(src ? src.source : 'my-fabric/worlds/spaces_index.json') + '</span></h3>'
      + '<div class="tw"><table class="bt"><thead><tr><th>Zone and sign</th><th>Kind</th><th>Models: exterior, interior, room GLB</th><th>Texture</th><th>Triangles</th><th>Door</th></tr></thead><tbody>' + rows + '</tbody></table></div>'
      + '<p class="note">Buildings are generated shells, fit-outs and rooms (my-fabric/worlds/spaces_index.json); the council building is the Steward Council\'s forum, which agents never operate.</p></section>';
  }

  // ---- avatars: the avatar registry when it exists (it adds coordinator rows that have no card yet), else the cards
  function gateTag(g) {
    if (!g) return '<span class="muted">no persona-prompt gates found</span>';
    const bad = (g.failed || []).length;
    return tag(bad || g.passed !== g.of ? 'bad' : 'ok', g.passed + ' / ' + g.of + ' pass') + (bad ? ' <span class="s">failing: ' + g.failed.map(esc).join(', ') + '</span>' : '')
      + (g.chars ? '<br><span class="muted s">' + num(g.chars) + ' chars</span>' : '');
  }
  function modelCell(ref) {
    if (!ref) return '<span class="muted">none</span>';
    const on = D.avatarGlbs.includes(base(ref));
    return on ? '<a href="' + esc(UP + ref) + '"><code>' + esc(base(ref)) + '</code></a> ' + tag('ok', 'on disk') : '<code title="' + esc(ref) + '">' + esc(base(ref)) + '</code> ' + tag('miss', 'not on disk yet');
  }
  function avatars(w) {
    const A = D.avatars || { present: false };
    const reg = !!A.present && !A.error;
    const zn = new Map(w.cards.filter((c) => c.k === 'zone').map((c) => [c.id, c.n]));
    const byId = new Map(w.cards.map((c) => [c.id, c]));
    const cardList = w.cards.filter((c) => c.k === 'omega').concat(w.cards.filter((c) => c.k === 'agent'));
    const cv = (cid, n) => cid ? '<a class="s cvl" href="' + esc(viewerUrl(w.slug, cid)) + '" aria-label="' + esc('Card in viewer: ' + n) + '">Card in viewer</a>' : '';
    let rows = '', head = '';
    if (reg) {
      const R = ((A.byWorld || {})[w.slug] || []).slice();
      const rank = { omega: 0, coordinator: 1, specialist: 2 };
      R.sort((a, b) => (rank[a.role] == null ? 9 : rank[a.role]) - (rank[b.role] == null ? 9 : rank[b.role]));
      const covered = new Set(R.map((r) => r.cid).filter(Boolean));
      rows = R.map((r) => {
        const c = r.cid ? byId.get(r.cid) : null;
        const roleText = c ? (c.k === 'omega' ? 'Omega Steward' : c.role) : (r.role_text || '');
        const who = r.role === 'omega' ? tag('dn', r.seat || 'defined, not seated') : !r.cid ? tag('miss', 'no card yet') : '';
        const bind = (r.swarm ? '<code>' + esc(r.swarm) + '</code>' : r.hive ? '<code>' + esc(r.hive) + '</code>' : '<span class="muted">unbound</span>') + (r.metaprompt ? '<span class="ds mono">' + esc(r.metaprompt) + '</span>' : '')
          + '<span class="ds">voice ' + (r.voice ? '<code>' + esc(r.voice) + '</code> \u00b7 ' + esc(r.role === 'omega' ? 'lines checked at view time in the Omega panel' : (r.vstatus || '')) : 'none') + '</span>';
        return '<tr><td class="who"><b>' + esc(r.name) + '</b> ' + who + '<span class="ds">' + tag('st', r.role || '') + ' ' + esc(r.zone || '') + '</span><span class="ds">' + esc(roleText) + '</span>' + cv(r.cid, r.name) + '</td><td class="bind">' + bind + '</td><td class="mdl">'
          + modelCell(r.model) + '</td><td class="intro">' + (r.intro ? esc(r.intro) : '<span class="muted">no intro line</span>') + '</td><td class="gt">' + gateTag(r.gates) + '</td></tr>';
      }).join('') + cardList.filter((c) => !covered.has(c.id)).map((c) => '<tr><td class="who"><b>' + esc(c.n) + '</b> ' + tag('bad', 'no registry row') + cv(c.id, c.n) + '</td><td colspan="4" class="muted">this card has no row in ' + esc(A.path) + '</td></tr>').join('');
      const wc = (A.worldChecks || {})[w.slug];
      const ck = wc ? Object.values(wc.checks) : [];
      head = '<p class="note" style="margin:0 0 10px">Read from <code>' + esc(A.path) + '</code>' + (A.schema ? ' (' + esc(A.schema) + (A.generator ? ', ' + esc(A.generator) : '') + ')' : '') + ' · digest <code>' + esc(A.digest) + '</code> · '
        + R.length + ' avatars for this world' + (wc ? ' · registry checks ' + tag(wc.failed.length ? 'bad' : 'ok', ck.filter(Boolean).length + ' / ' + ck.length + ' pass') + (wc.failed.length ? ' failing: ' + wc.failed.map(esc).join(', ') : '') : '')
        + '. Persona-prompt gates come from <code>' + esc(A.path.replace(/index\.json$/, 'prompts/' + w.slug + '.json')) + '</code>; no model runs these prompts.</p>'
        + (A.honesty && A.honesty.length ? '<details class="note" style="margin:0 0 10px"><summary>Registry honesty notes</summary><ul class="gaps">' + A.honesty.map((h) => '<li>' + esc(h) + '</li>').join('') + '</ul></details>' : '');
    } else {
      rows = cardList.map((c) => {
        const av = c.avatar || {};
        const bind = c.k === 'omega' ? '<code>' + esc(c.hive_ref || 'no hive row') + '</code>' : '<code>' + esc((c.binding || {}).swarm || 'unbound') + '</code><span class="ds mono">' + esc((c.binding || {}).metaprompt || '') + '</span>';
        return '<tr><td class="who"><b>' + esc(c.n) + '</b>' + (c.k === 'omega' ? ' ' + tag('dn', 'defined, not seated') : '') + '<span class="ds">' + tag('st', c.k === 'omega' ? 'omega' : (av.role || 'specialist')) + ' '
          + esc(c.k === 'omega' ? 'beside the council' : (zn.get(c.pa) || 'plaza (zone not in spec)')) + '</span><span class="ds">' + esc(c.k === 'omega' ? 'Omega Steward' : c.role) + '</span>' + cv(c.id, c.n) + '</td><td class="bind">' + bind + '</td><td class="mdl">' + modelCell(av.model_ref)
          + '</td><td class="intro"><span class="muted">avatar registry not built yet</span></td><td class="gt"><span class="muted">not built yet</span></td></tr>';
      }).join('');
      head = A.error ? '<p class="pend">Avatar registry present but unreadable: ' + esc(A.error) + '.</p>'
        : '<p class="pend">Avatar registry not built yet: <code>' + esc(A.path) + '</code> does not exist. Intro lines and persona-prompt gate results appear here once it does; this console goes STALE at that moment and is rebuilt.</p>';
    }
    return '<section class="panel" aria-labelledby="hA"><h3 id="hA">Avatars <span class="tag st">' + (reg ? ((A.byWorld || {})[w.slug] || []).length : cardList.length) + ' avatars</span><span class="src">' + esc(reg ? A.path : 'cards.json avatar + binding') + '</span></h3>' + head
      + '<div class="tw"><table class="avt"><thead><tr><th>Avatar, role and zone</th><th>Binding and voice</th><th>Model</th><th>Intro line</th><th>Persona-prompt gates</th></tr></thead><tbody>' + rows + '</tbody></table></div></section>';
  }

  // ---- Omega Steward
  function omega(w) {
    const o = w.cards.find((c) => c.k === 'omega');
    if (!o) return '<section class="panel" aria-labelledby="hO"><h3 id="hO">Omega Steward</h3><p class="pend">No Omega Steward is defined for this world in agents/advisory/omega_agents.json.</p></section>';
    const p = o.persona, v = o.voice;
    const persona = p ? '<div class="kvs"><div><span>Temperament</span><b>' + esc(p.temperament || 'not set') + '</b></div><div><span>Style</span><b>' + esc(p.style || 'not set') + '</b></div></div>'
      + '<h4>Values</h4><div class="chips">' + ((p.values || []).map((x) => '<span class="chip val">' + esc(x) + '</span>').join('') || '<span class="muted">none listed</span>') + '</div>'
      + '<h4>Refuses</h4><div class="chips">' + ((p.refuses || []).map((x) => '<span class="chip lock">' + esc(x) + '</span>').join('') || '<span class="muted">none listed</span>') + '</div>'
      : '<p class="pend">Persona pending: this world has no row in the hive registry yet.</p>';
    let voice = '<p class="pend">Voice pending: no hive voice for this world yet.</p>';
    if (v) {
      const fb = v.browser_fallback || {};
      const lines = (v.lines || []).map((l) => {
        const lab = LINE[l.id] || l.id;
        return '<li class="ln"><div class="ln-h"><b>' + esc(lab) + '</b><span class="synth">synthetic voice' + (v.kokoro ? ' \u00b7 Kokoro ' + esc(v.kokoro) : '') + '</span><span class="vs" data-vs>not checked</span></div><p>' + esc(l.text) + '</p>'
          + (l.audio ? '<audio controls preload="none" src="' + esc(UP + l.audio) + '" aria-label="' + esc(lab + ' line, synthetic voice') + '"></audio>' : '<span class="muted s">no audio path</span>') + '</li>';
      }).join('');
      voice = '<div class="kvs"><div><span>Kokoro voice</span><b class="mono">' + esc(v.kokoro || 'none') + '</b></div><div><span>Browser fallback</span><b class="mono">pitch ' + esc(fb.pitch) + ' \u00b7 rate ' + esc(fb.rate) + ' \u00b7 ' + esc(fb.lang) + '</b></div></div>'
        + '<h4>Lines</h4><ol class="lines">' + lines + '</ol>'
        + '<p class="note">A line plays only once voiced: the hive renders it to <code>agents/hive/voices/' + esc(w.slug) + '/&lt;line&gt;.mp4</code>, and until then the player has nothing to play. Every voice is synthetic, and nothing plays until you press play.</p>';
    }
    return '<section class="panel" aria-labelledby="hO"><h3 id="hO">Omega Steward ' + tag('dn', o.status || 'defined, not seated') + '<span class="src">' + esc(o.hive_ref || o.source || '') + '</span></h3>'
      + '<div class="kvs"><div><span>Name</span><b>' + esc(o.n) + '</b></div><div><span>Omega id</span><b class="mono">' + esc(o.omega_id) + '</b></div><div><span>Seated agent</span><b>' + esc(o.seated_agent == null ? 'none (defined, not seated)' : o.seated_agent) + '</b></div><div><span>Avatar model</span><b class="mono">' + esc((o.avatar || {}).model_ref || 'none') + '</b></div></div>'
      + '<h4>Persona</h4>' + persona + '<h4>Voice</h4>' + voice
      + '<h4>May never</h4><div class="chips">' + (o.may_never || []).map((x) => '<span class="chip lock">' + esc(x) + '</span>').join('') + '</div></section>';
  }

  // ---- evals, gates, gaps, reserved actions
  function gates(w) {
    const rows = w.gates.map(([k, v]) => {
      const s = String(v);
      const cls = s === 'done' ? 'ok' : s === 'failed' ? 'bad' : s.indexOf('open') === 0 ? 'open' : 'part';
      return '<tr><td>' + esc(k) + '</td><td>' + tag(cls, s) + '</td></tr>';
    }).join('');
    return '<section class="panel" aria-labelledby="hG"><h3 id="hG">Gates<span class="src">manifest.json gates</span></h3><div class="tw"><table><thead><tr><th>Gate</th><th>Status</th></tr></thead><tbody>' + rows + '</tbody></table></div></section>';
  }
  function evals(w) {
    const e = Object.entries(w.evals);
    const bad = e.filter((x) => !x[1]).length;
    const items = e.slice().sort((a, b) => (a[1] === b[1] ? 0 : a[1] ? 1 : -1)).map(([k, v]) => '<li class="' + (v ? 'ok' : 'bad') + '"><span aria-hidden="true">' + (v ? '\u2713' : '\u2717') + '</span><code>' + esc(k) + '</code><span class="sr">' + (v ? 'passes' : 'fails') + '</span></li>').join('');
    return '<section class="panel" aria-labelledby="hE"><h3 id="hE">WorldForge evals ' + tag(bad ? 'bad' : 'ok', (e.length - bad) + ' / ' + e.length + ' pass') + '<span class="src">manifest.json evals</span></h3><ul class="evs">' + items + '</ul></section>';
  }
  function reserved(w) {
    const rs = new Set(w.cards.map((c) => c.r));
    const r = D.reserved[w.cards[0].r] || [];
    const q = (r[0] || {}).held_for || {};
    return '<section class="panel" aria-labelledby="hR"><h3 id="hR">Held for people <span class="src">reserved_for_humans</span></h3><div class="chips">' + r.map((x) => '<span class="chip lock">' + esc(x.action) + '</span>').join('') + '</div>'
      + '<p class="note">Held for the ' + esc(q.holder || 'Steward Council') + ', ' + esc(q.quorum || '2-of-3') + ' of ' + esc(q.seats) + ' human seats' + (rs.size === 1 ? ', carried verbatim on all ' + w.cards.length + ' cards of this world' : ', but the cards of this world carry ' + rs.size + ' different lists') + '. No agent or Omega card holds any of them.</p></section>';
  }
  function gaps(w) {
    const g = w.gaps.map((x) => '<li>' + esc(x) + ' <span class="d">(cards.json gaps)</span></li>');
    w.gates.forEach(([k, v]) => { if (String(v) !== 'done') g.push('<li>gate ' + esc(k) + ': ' + esc(v) + ' <span class="d">(manifest.json)</span></li>'); });
    const A = D.avatars || {};
    if (!A.present) g.push('<li>avatar registry not built yet <span class="d">(' + esc(A.path) + ')</span></li>');
    else if (!A.error) {
      const R = (A.byWorld || {})[w.slug] || [];
      const nocard = R.filter((r) => !r.cid).length, scripted = R.filter((r) => r.role !== 'omega' && r.vstatus && r.vstatus.indexOf('not voiced') >= 0).length;
      if (nocard) g.push('<li>' + nocard + ' avatar(s) without a Master Card yet (coordinator stand spec only) <span class="d">(' + esc(A.path) + ')</span></li>');
      if (scripted) g.push('<li>' + scripted + ' specialist/coordinator voice(s) scripted, not voiced: a Kokoro id is assigned and no audio exists</li>');
    }
    const miss = [...new Set(w.cards.map((c) => (c.avatar || {}).model_ref).filter((p) => p && !D.avatarGlbs.includes(base(p))))];
    if (miss.length) g.push('<li>avatar models not on disk yet: ' + miss.map((p) => '<code>' + esc(base(p)) + '</code>').join(', ') + '</li>');
    const nob = w.cards.filter((c) => (c.k === 'zone' || c.k === 'council') && !c.building);
    if (nob.length) g.push('<li>' + nob.length + ' zone(s) without a linked building</li>');
    return '<section class="panel" aria-labelledby="hX"><h3 id="hX">Gaps: what is not done</h3><ul class="gaps">' + (g.join('') || '<li>none recorded</li>') + '</ul></section>';
  }
  function header(w) {
    const a = w.anchor || {};
    const fmt = (x) => Number(x).toFixed(4);
    const anch = a.lat != null && a.lon != null ? (a.rp1 ? '<a href="' + esc(a.rp1) + '" target="_blank" rel="noopener noreferrer">RP1 anchor ' + fmt(a.lat) + ', ' + fmt(a.lon) + '</a>' : 'RP1 anchor ' + fmt(a.lat) + ', ' + fmt(a.lon)) : tag('miss', 'no anchor yet');
    const os = w.omega_steward;
    return '<div class="wh"><span class="mark lg" aria-hidden="true">' + esc(w.brand.mark) + '</span><div class="wh-t"><div class="eyebrow">' + esc(w.brand.lockup || '') + '</div>'
      + '<h2 id="wTitle">' + esc(w.name) + ' ' + tag('st', w.status || '') + '</h2><p>' + esc(w.tagline || '') + '</p>'
      + '<div class="meta">' + anch + '<span>' + esc(w.mgmt || '') + '</span><span>Omega: ' + (os ? esc(os.status) : 'none defined') + '</span><span class="mono">' + esc(w.slug) + '</span><span>skin: hue ' + esc(w.brand.hue) + ', mark ' + esc(w.brand.mark) + '</span></div>'
      + '<div class="links"><a class="btn" href="' + esc(viewerUrl(w.slug)) + '">Open in viewer</a><a class="btn ghost" href="../hive/#' + esc(w.slug) + '">Hive console</a><a class="btn ghost" href="../../agents/teams.html">Team console</a></div></div></div>';
  }
  function wstats(w) {
    const c = w.counts, e = Object.values(w.evals);
    const cell = (k, v) => '<div class="ws"><span>' + esc(k) + '</span><b>' + v + '</b></div>';
    return '<div class="wstats">' + cell('cards', w.cards.length) + cell('zones', esc(c.zones)) + cell('agents', esc(c.agents)) + cell('primitives', esc(c.primitives)) + cell('roads', esc(c.roads))
      + cell('plan nodes', esc(c.planNodes)) + cell('GLB', w.glbBytes ? (w.glbBytes / 1024).toFixed(1) + ' KB' : 'none') + cell('evals', e.filter(Boolean).length + '/' + e.length) + '</div>';
  }

  // ---- world switching
  const view = $('#view'), sel = $('#worldSel'), status = $('#status');
  let cur = null, probeGen = 0;
  function probeVoices() {
    const gen = ++probeGen;
    $$('#view audio').forEach((a) => {
      const st = a.closest('.ln').querySelector('[data-vs]');
      const set = (t, cls) => { if (gen === probeGen) { st.textContent = t; st.className = 'vs ' + cls; } };
      a.addEventListener('error', () => set('not voiced yet', 'vpend'));
      if (location.protocol === 'file:' || typeof fetch !== 'function') { set('voice status unknown (open over http)', ''); return; }
      fetch(a.getAttribute('src'), { method: 'HEAD', cache: 'no-store' }).then((r) => set(r.ok ? 'voiced' : 'not voiced yet', r.ok ? 'vok' : 'vpend')).catch(() => set('voice status unknown', ''));
    });
  }
  function show(slug, push) {
    const w = BY.get(slug) || BY.get(D.defaultWorld) || D.worlds[0];
    cur = w.slug;
    root.style.setProperty('--h', String(w.brand.hue == null ? 200 : w.brand.hue));
    $('#topMark').textContent = w.brand.mark || '';
    $('#topLockup').textContent = w.brand.lockup || '';
    sel.value = w.slug;
    $$('#wlist .wb').forEach((b) => b.setAttribute('aria-current', b.dataset.world === w.slug ? 'true' : 'false'));
    uid = 0;
    view.innerHTML = header(w) + wstats(w)
      + '<section class="panel" aria-labelledby="hT"><h3 id="hT">Master Card tree <span class="tag st">' + w.cards.length + ' cards</span><span class="src">worldforge/out/' + esc(w.slug) + '/cards.json</span></h3>'
      + '<div class="tbar"><button type="button" class="btn ghost sm" data-all="1">Expand all</button><button type="button" class="btn ghost sm" data-all="0">Collapse all</button></div>' + legend()
      + '<div style="margin-top:10px">' + tree(w) + '</div></section>'
      + '<div class="two">' + gates(w) + reserved(w) + '</div>' + evals(w) + buildings(w) + avatars(w) + omega(w) + gaps(w);
    status.textContent = 'Showing ' + w.name;
    if (push) { try { history.replaceState(null, '', '?world=' + encodeURIComponent(w.slug)); } catch (e) { /* ignore */ } }
    probeVoices();
  }
  view.addEventListener('click', (e) => {
    const t = e.target instanceof Element ? e.target : null;
    if (!t) return;
    const tg = t.closest('.tg[aria-controls]');
    if (tg) {
      const open = tg.getAttribute('aria-expanded') !== 'true';
      tg.setAttribute('aria-expanded', String(open));
      tg.setAttribute('aria-label', tg.getAttribute('aria-label').replace(/^(Expand|Collapse) /, open ? 'Collapse ' : 'Expand '));
      const ul = document.getElementById(tg.getAttribute('aria-controls'));
      if (ul) ul.hidden = !open;
      return;
    }
    const all = t.closest('[data-all]');
    if (all) {
      const open = all.dataset.all === '1';
      $$('.tg[aria-controls]', view).forEach((b) => {
        if (!open && b.closest('.tree > li > .row')) return; // keep the world card open so the tree never vanishes
        b.setAttribute('aria-expanded', String(open));
        b.setAttribute('aria-label', b.getAttribute('aria-label').replace(/^(Expand|Collapse) /, open ? 'Collapse ' : 'Expand '));
        const ul = document.getElementById(b.getAttribute('aria-controls'));
        if (ul) ul.hidden = !open;
      });
    }
  });
  $('#wlist').addEventListener('click', (e) => { const b = e.target instanceof Element ? e.target.closest('.wb') : null; if (b) { show(b.dataset.world, true); view.focus({ preventScroll: true }); } });
  $('#wlist').addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowDown' && e.key !== 'ArrowUp') return;
    const bs = $$('#wlist .wb').filter((b) => !b.hidden);
    const i = bs.indexOf(document.activeElement);
    if (i < 0) return;
    e.preventDefault();
    const n = bs[Math.max(0, Math.min(bs.length - 1, i + (e.key === 'ArrowDown' ? 1 : -1)))];
    if (n) n.focus();
  });
  sel.addEventListener('change', () => show(sel.value, true));
  const step = (d) => { const i = D.worlds.findIndex((w) => w.slug === cur); show(D.worlds[(i + d + D.worlds.length) % D.worlds.length].slug, true); };
  $('#prevW').addEventListener('click', () => step(-1));
  $('#nextW').addEventListener('click', () => step(1));
  $('#wq').addEventListener('input', (e) => {
    const q = e.target.value.trim().toLowerCase();
    $$('#wlist .wb').forEach((b) => { b.hidden = !!q && !q.split(/\s+/).every((t) => b.dataset.q.includes(t)); });
  });
  $('#themeBtn').addEventListener('click', () => {
    const next = root.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
    root.setAttribute('data-theme', next);
    try { localStorage.setItem('wf-theme', next); } catch (e) { /* storage unavailable */ }
  });
  let start = null;
  try { start = new URLSearchParams(location.search).get('world'); } catch (e) { /* ignore */ }
  if (!start && location.hash) start = decodeURIComponent(location.hash.slice(1));
  window.WF = { show, slugs: D.worlds.map((w) => w.slug), current: () => cur };
  show(start && BY.has(start) ? start : D.defaultWorld, false);
})();
"""


def page(S, st):
    D = dict(S["data"])
    T = stats(D)
    D["defaultWorld"] = "locator-x" if any(w["slug"] == "locator-x" for w in D["worlds"]) else D["worlds"][0]["slug"]
    w0 = next(w for w in D["worlds"] if w["slug"] == D["defaultWorld"])
    A = D["avatars"]
    refs = sorted({os.path.basename(c["avatar"]["model_ref"]) for w in D["worlds"] for c in w["cards"] if (c.get("avatar") or {}).get("model_ref")}
                  | {os.path.basename(r["model"]) for v in (A.get("byWorld") or {}).values() for r in v if r.get("model")})
    on_disk = [r for r in refs if r in D["avatarGlbs"]]
    if A["present"] and not A.get("error"):
        at = A.get("totals") or {}
        gp = sum(int((r.get("gates") or {}).get("passed") or 0) for v in A["byWorld"].values() for r in v)
        go = sum(int((r.get("gates") or {}).get("of") or 0) for v in A["byWorld"].values() for r in v)
        av_val = A["matched"]
        av_sub = (f'{E(at.get("specialists", "?"))} specialists, {E(at.get("coordinators", "?"))} coordinators, {E(at.get("omegas", "?"))} Omegas &middot; '
                  f'prompt gates {gp:,}/{go:,} &middot; models on disk {len(on_disk)}/{len(refs)}')
        av_tone = "ok" if on_disk and len(on_disk) == len(refs) and gp == go else "warn"
    else:
        av_val = T["avatars"]
        av_sub = (f'{T["agents"]} agents + {T["omegas"]} Omegas bound on cards &middot; '
                  + ("avatar registry not built yet" if not A["present"] else f'registry unreadable: {E(A.get("error"))}') + f' &middot; {len(on_disk)} of {len(refs)} role models on disk')
        av_tone = "warn"
    k = "".join([
        kpi("Worlds", T["worlds"], "41 team skins &middot; worldforge/out/index.json"),
        kpi("Master cards", f'{T["cards"]:,}', f'{T["seats_empty"]} of {T["seats"]} human seats empty'),
        kpi("Primitives", f'{T["primitives"]:,}', "synthetic placeholder massing"),
        kpi("Evals / failing", f'{T["evals"]:,}<small> / {T["failing"]}</small>', f'broken cases {T["broken_ok"]}/{T["broken"]} discriminated', "ok" if not T["failing"] else "bad"),
        kpi("Buildings linked", f'{T["bldg_linked"]}<small> / {T["bldg_slots"]}</small>', f'zones + councils &middot; {T["bldg_interior"]} with an interior'),
        kpi("Avatars", av_val, av_sub, av_tone),
        kpi("Omegas", f'{T["omega_dns"]}<small> / {T["omegas"]}</small>', "defined, not seated", "warn"),
        kpi("Anchored in RP1", f'{T["anchored"]}<small> / {T["worlds"]}</small>', "the rest: no anchor yet", "warn" if T["anchored"] < T["worlds"] else "ok"),
    ])
    honesty = "".join(f'<div class="hn"><b>{E(t)}</b><p>{E(x)}</p></div>' for t, x in HONESTY)
    navs = "".join(nav_button(w) for w in D["worlds"])
    opts = "".join(f'<option value="{E(w["slug"])}"{" selected" if w["slug"] == D["defaultWorld"] else ""}>{E(w["name"])}</option>' for w in D["worlds"])
    return f"""<!doctype html>
<html lang="en" style="--h:{E(w0["brand"]["hue"])}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>WorldForge Console</title>
<meta name="description" content="WorldForge team console: Master Cards, buildings, avatars, Omega Stewards, evals and gates for the {T["worlds"]} worlds of the AGI Future Foundation PBC, {E(D["umbrella"])}.">
<meta name="color-scheme" content="dark light">
<script>try{{var t=localStorage.getItem('wf-theme');if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}}catch(e){{}}</script>
<style>{CSS}</style>
</head>
<body>
<!-- {STAMP_TAG}: {st} -->
<a class="skip" href="#view">Skip to the world</a>
<header class="top"><div class="wrap bar">
  <div class="brand"><span class="mark" id="topMark" aria-hidden="true">{E(w0["brand"]["mark"])}</span><div><b>WorldForge console</b><small id="topLockup">{E(w0["brand"]["lockup"])}</small></div></div>
  <div class="pick"><button type="button" class="ibtn" id="prevW" aria-label="Previous world">&#8249;</button>
    <label class="sr" for="worldSel">World</label><select id="worldSel">{opts}</select>
    <button type="button" class="ibtn" id="nextW" aria-label="Next world">&#8250;</button></div>
  <button class="ibtn" id="themeBtn" type="button" aria-label="Switch between dark and light theme">{ICON_SUN}{ICON_MOON}</button>
</div></header>
<main class="wrap" id="main">
  <section class="hero" aria-labelledby="h1">
    <div class="eyebrow">{E(D["owner"])} &middot; WorldForge &middot; {E(D["umbrella"])}</div>
    <h1 id="h1">WorldForge team console</h1>
    <p class="lede">{T["worlds"]} coming-soon worlds carried through WorldForge: Master Cards, card-tagged GLBs and Sneeze mount plans. Every world, zone, agent and persona here is copied from a registry file and keeps its citation. Pick a world to see its card tree, buildings, avatars, Omega Steward, evals, gates and gaps.</p>
    <div class="honesty" role="note" aria-label="Honesty strip">{honesty}</div>
  </section>
  <section aria-label="Network totals"><div class="kpis">{k}</div></section>
  <div class="layout">
    <nav class="wl" aria-label="Worlds"><label class="sr" for="wq">Filter worlds</label><input id="wq" type="search" placeholder="Filter {T["worlds"]} worlds" autocomplete="off"><div id="wlist">{navs}</div></nav>
    <article id="view" tabindex="-1" aria-labelledby="wTitle"><noscript><p class="pend">This console renders each world with inline JavaScript; the network totals above are static.</p></noscript></article>
  </div>
  <p class="sr" id="status" aria-live="polite"></p>
</main>
<footer class="foot"><div class="wrap">
  <p>{E(HONESTY[0][1])} {E(HONESTY[1][1])}</p>
  <p>{E(HONESTY[2][1])} {E(HONESTY[3][1])}</p>
  <p>This page describes an organization being built. It is not an offer to sell securities or a solicitation of an offer to buy them, and it is not legal, tax or financial advice.</p>
  <p class="mono">stamp {st} &middot; built from {len(S["files"])} files by {E(BUILDER)} &middot; {E(D["owner"])} &middot; {E(D["umbrella"])}</p>
</div></footer>
<script type="application/json" id="wf-data">{script_json(D)}</script>
<script>{JS}</script>
</body>
</html>
"""


# --------------------------------------------------------------------------------------------- evals ----
def inline_scripts(doc):
    return [m.group(2) for m in re.finditer(r"<script(\s[^>]*)?>(.*?)</script>", doc, re.S) if 'type="application/json"' not in (m.group(1) or "")]


def node_run(code, check=False):
    try:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
            f.write(code); path = f.name
        r = subprocess.run(["node", "--check", path] if check else ["node", path], capture_output=True, text=True, timeout=60)
        os.unlink(path)
        return r.returncode == 0, ((r.stderr or "") + (r.stdout or "")).strip().splitlines()[:1]
    except (OSError, subprocess.SubprocessError) as e:
        return False, [str(e)]


def evals(S, doc, st):
    res = []

    def ok(name, cond, detail=""):
        res.append((name, bool(cond), detail))

    D = S["data"]
    T = stats(D)
    idx = J(INDEX)
    slugs = [r["slug"] for r in idx["worlds"]]
    ok("every world in worldforge/out/index.json appears once: data, picker and world list",
       [w["slug"] for w in D["worlds"]] == slugs and all(doc.count(f'<option value="{E(s)}"') == 1 and doc.count(f'class="wb" data-world="{E(s)}"') == 1 for s in slugs),
       f'{len(D["worlds"])} worlds')
    allc = [(w["slug"], c) for w in D["worlds"] for c in w["cards"]]
    orphan = [c["id"] for s, c in allc if c["pa"] and c["pa"] not in {x["id"] for x in next(w for w in D["worlds"] if w["slug"] == s)["cards"]}]
    ids = [c["id"] for _, c in allc]
    ok("every card of every cards.json is embedded once and every parent resolves", len(ids) == len(set(ids)) == idx["totals"]["cards"] and not orphan,
       f"{len(ids)} cards, {len(orphan)} orphans")
    t = idx["totals"]
    ok("network totals agree with worldforge/out/index.json (cards, primitives, evals, failing, anchored)",
       (T["cards"], T["primitives"], T["evals"], T["failing"], T["anchored"]) == (t["cards"], t["primitives"], t["evals"], t["failed"], t["anchored"]),
       f'{(T["cards"], T["primitives"], T["evals"], T["failing"], T["anchored"])} vs {(t["cards"], t["primitives"], t["evals"], t["failed"], t["anchored"])}')
    bad_seats = [w["slug"] for w in D["worlds"] if (lambda co, ss: len(co) != 1 or len(ss) != 3 or any(x["pa"] != co[0]["id"] or x.get("seat_type") != "human" or x.get("seated") is not None for x in ss))(
        [c for c in w["cards"] if c["k"] == "council"], [c for c in w["cards"] if c["k"] == "seat"])]
    ok("each world: one council with exactly 3 empty human seats under it", not bad_seats, ", ".join(bad_seats[:4]))
    held_bad = [c["id"] for _, c in allc if c["k"] in ("agent", "omega") and any(str(h).startswith("agents") or str(h).startswith("omega") for r in HUMAN_ONLY_RIGHTS for h in D["perms"][c["p"]].get(r, []))]
    q_rights = sorted({r for p in D["perms"] for r, h in p.items() if "steward-quorum" in h})
    ok("agents operate, people govern: no agent or Omega card holds delegate, transfer or govern", not held_bad and "transfer" in q_rights and "govern" in q_rights, ", ".join(held_bad[:4]))
    ok("steward-quorum rights render as 'held' (permission row legend and cell code)",
       "if (h.includes('steward-quorum')) return ['held', 'q', 'held for the Steward Council, 2-of-3 quorum'];" in JS and "held for the 2-of-3 Steward Council" in JS)
    rbad = [c["id"] for _, c in allc if [x.get("action") for x in D["reserved"][c["r"]]] != HOUSE_RESERVED
            or any((x.get("held_for") or {}).get("quorum") != "2-of-3" or (x.get("held_for") or {}).get("holder") != "Steward Council" for x in D["reserved"][c["r"]])]
    ok("every card reserves the six house actions for the 2-of-3 Steward Council", not rbad, ", ".join(rbad[:4]))
    om = [c for _, c in allc if c["k"] == "omega"]
    ok("every Omega card is 'defined, not seated' with no seated agent and an avatar model_ref",
       om and all(c.get("status") == "defined, not seated" and c.get("seated_agent") is None and (c.get("avatar") or {}).get("model_ref") for c in om), f"{len(om)} Omegas")
    lines = [(w["slug"], ln) for w in D["worlds"] for c in w["cards"] if c["k"] == "omega" for ln in ((c.get("voice") or {}).get("lines") or [])]
    ok("every voice line points at agents/hive/voices/<world>/<id>.mp4, rendered via ../../ with preload none",
       lines and not S["issues"] and all(ln["audio"] == AUDIO_PATH.format(world=s, line=ln["id"]) for s, ln in lines)
       and "'<audio controls preload=\"none\" src=\"' + esc(UP + l.audio)" in JS and "const UP = '../../';" in JS, f'{len(lines)} lines; ' + "; ".join(S["issues"][:2]))
    ok("no autoplay anywhere, and no .play() call in the script", "autoplay" not in doc.lower() and ".play(" not in JS)
    ok("every audio player is labelled 'synthetic voice' and the panel says a line plays only once voiced",
       '<span class="synth">synthetic voice' in JS and "A line plays only once voiced" in JS and "Synthetic voices" in doc)
    tb = [w["slug"] for w in D["worlds"] if not (isinstance(w["brand"].get("hue"), (int, float)) and w["brand"].get("mark") and w["brand"].get("lockup"))]
    ok("41 team skins: hue, mark and lockup from worlds/generated/teams/<slug>.json .brand", not tb and len(D["worlds"]) == len(slugs), ", ".join(tb[:4]))
    absent = not D["avatars"]["present"]
    ok("avatar registry: when absent the page says 'avatar registry not built yet'; when present it is read",
       (absent and "avatar registry not built yet" in doc and "Avatar registry not built yet" in JS) or (not absent and D["avatars"].get("path") == AVATARS))
    agent0 = next(c for _, c in allc if c["k"] == "agent")
    w0 = next(s_ for s_, c in allc if c is agent0)
    fx_dir = tempfile.mkdtemp()
    os.makedirs(os.path.join(fx_dir, "prompts"))
    fx = os.path.join(fx_dir, "index.json")
    with open(fx, "w") as f:
        json.dump({"schemaVersion": "worldforge-avatars/0.1", "generated_at": "2099-01-01T00:00:00Z", "totals": {"avatars": 3},
                   "rows": [{"avatarId": "a1", "cardId": agent0["id"], "world": w0, "name": agent0["n"], "role": "specialist", "intro": {"text": "Hello <b>x</b>", "from": "fixture"},
                             "persona_prompt_id": "persona:fx", "permissions": {"govern": ["steward-quorum"]}},
                            {"avatarId": "a2", "cardId": None, "world": w0, "name": "Fixture Coordinator", "role": "coordinator", "role_text": "fixture"},
                            {"avatarId": "a3", "cardId": "agent:nowhere/x", "world": "nowhere"}],
                   "worlds": [{"slug": w0, "avatars": 2, "checks": {"one": True, "two": False}, "failed": ["two"]}]}, f)
    with open(os.path.join(fx_dir, "prompts", f"{w0}.json"), "w") as f:
        json.dump({"prompts": [{"id": "persona:fx", "chars": 10, "gates": {"passed": 15, "of": 16, "failed": ["g"]}, "text": "not embedded"}]}, f)
    S2 = load(fx)
    os.unlink(os.path.join(fx_dir, "prompts", f"{w0}.json")); os.rmdir(os.path.join(fx_dir, "prompts")); os.unlink(fx); os.rmdir(fx_dir)
    a2 = S2["data"]["avatars"]
    r2 = (a2.get("byWorld") or {}).get(w0) or []
    ok("broken fixture: an avatar registry appearing changes the stamp (STALE), rows group by world, coordinators without a card are kept, prompt gates are read, prompt text and *_at keys stay out",
       stamp(S2) != st and a2["present"] and a2["matched"] == 2 and a2["unmatched"] == 1 and any(r["cid"] is None and r["role"] == "coordinator" for r in r2)
       and any(r["gates"] == {"passed": 15, "of": 16, "failed": ["g"], "chars": 10} for r in r2) and a2["worldChecks"][w0]["failed"] == ["two"]
       and "generated_at" not in json.dumps(a2) and "not embedded" not in json.dumps(a2), f'matched {a2.get("matched")}, unmatched {a2.get("unmatched")}')
    A = D["avatars"]
    if A["present"] and not A.get("error"):
        at = A.get("totals") or {}
        go = sum(int((r.get("gates") or {}).get("of") or 0) for v in A["byWorld"].values() for r in v)
        cards_av = {c["id"] for _, c in allc if c["k"] in ("agent", "omega", "coordinator", "advisor")}
        reg_cids = {r["cid"] for v in A["byWorld"].values() for r in v if r["cid"]}
        ok("avatar registry agrees with the cards and its own totals (every agent and Omega card has a row; rows, prompt gates)",
           cards_av == reg_cids and A["matched"] == at.get("avatars", A["matched"]) and A["unmatched"] == 0 and go == at.get("prompt_gates", go),
           f'{len(cards_av - reg_cids)} cards without a row, {len(reg_cids - cards_av)} rows without a card, {A["matched"]} rows vs {at.get("avatars")}, gates {go} vs {at.get("prompt_gates")}')
        ok("no avatar row holds delegate, transfer or govern", all(r["reserved_ok"] for v in A["byWorld"].values() for r in v))
    ok("links: viewer ?world= and &card=, the hive console ../hive/, the team console ../../agents/teams.html",
       "'worldforge/viewer.html?world=' + encodeURIComponent(slug) + (card ? '&card=' + encodeURIComponent(card) : '')" in JS and 'href="../hive/#' in JS and "../../agents/teams.html" in JS and ">Open in viewer</a>" in JS and ">Card in viewer</a>" in JS)
    low = doc.lower()
    priv = sorted({n for n in S["private"] if n.lower() in low})
    ok("no private repository name (projects/index.json rows with private=true)", S["private"] and not priv, ", ".join(priv))
    emails = sorted(set(EMAIL.findall(doc)))
    ok("no email address, wallet address or key-like token on the page", not emails and not WALLET.search(doc) and not KEYLIKE.search(doc), ", ".join(emails[:3]))
    ok("visitor text uses no sprint-internal words ('the peer', 'peer's', 'the lead')", not re.search(r"\bthe peer\b|\bpeer's\b|peer\\'s|\bthe lead\b", doc, re.I))
    ok("no local absolute path or account name on the page","/users/" not in low and "/home/" not in low and "romanbridge.x/" not in low and "/private/" not in low)
    nm_bad = [c["id"] for _, c in allc if len(c.get("dn") or "") > 48]
    ok("every card display name is within the 48-character fabric node limit", not nm_bad, ", ".join(nm_bad[:3]))
    scripts = inline_scripts(doc)
    good, err = node_run("\n;\n".join(scripts), check=True)
    ok("inline scripts pass node --check", good and len(scripts) == 2, " ".join(err))
    m = re.search(r"^  const esc = .*?;$", JS, re.M)
    good2, err2 = node_run((m.group(0) if m else "const esc = null;") + "\nconst o = esc('<img src=x onerror=alert(1)> \"q\" \\'s\\' &');\nif (/[<>\"']/.test(o) || !o.includes('&lt;img')) { console.error(o); process.exit(1); }\n")
    ok("broken fixture: esc() escapes markup from a registry string before it reaches innerHTML", m and good2, " ".join(err2))
    data = re.search(r'<script type="application/json" id="wf-data">(.*?)</script>', doc, re.S).group(1)
    ok("embedded JSON carries no raw < or > and parses", "<" not in data and ">" not in data and isinstance(json.loads(data), dict))
    ok("external resources: none (no remote script, stylesheet or font)", not re.search(r'<(?:script|link|img|iframe)[^>]+(?:src|href)="https?://', doc) and "@import" not in doc and "<link" not in low)
    size = len(doc.encode())
    ok("page under 2 MB", size < MAX_BYTES, f"{size // 1024} KB")
    ok("deterministic: two builds are byte-identical", page(load(), st) == doc)
    ok("theme tokens on :root, dark by default, light on toggle, stored in try/catch",
       CSS.lstrip().startswith(":root{--h:200;--bg:#070b16") and ':root[data-theme="light"]' in CSS and "try { localStorage.setItem('wf-theme'" in JS and "try{var t=localStorage.getItem('wf-theme')" in doc)
    ok("responsive to phone width (640px breakpoint with a 16px gutter; tables scroll inside their panel)",
       "@media (max-width:640px){.wrap{padding:0 16px}" in CSS and ".tw{overflow-x:auto" in CSS)
    ok("keyboard: worlds, toggles and expand/collapse are <button>s; no clickable div", doc.count('<button type="button" class="wb"') == len(slugs)
       and "'<button type=\"button\" class=\"tg\" aria-expanded=\"'" in JS and "onclick" not in low and 'role="button"' not in low)
    return res


def main():
    args = sys.argv[1:]
    if "--check" in args:
        S = load()
        st = stamp(S)
        disk = open(OUT, encoding="utf-8").read() if os.path.exists(OUT) else ""
        m = re.search(STAMP_TAG + r": ([0-9a-f]{16})", disk)
        if not m or m.group(1) != st:
            print(f"worldforge console STALE: built from {m.group(1) if m else 'nothing'}, sources are now {st}"); sys.exit(1)
        if page(S, st) != disk:  # the stamp matches but the bytes do not: a hand edit or a truncated write
            print(f"worldforge console STALE: built from {st}, sources are now {st}, but index.html differs from a fresh build"); sys.exit(1)
        print(f"worldforge console current ({st})"); return
    st, S, doc, results = None, None, None, []
    for _ in range(4):  # another builder may be writing worldforge/out or the avatar registry: rebuild until one build sees one state
        S = load()
        st = stamp(S)
        doc = page(S, st)
        results = evals(S, doc, st)
        if stamp(load()) == st:
            break
    else:
        results.append(("sources held still for one build (they kept changing while it ran)", False, ""))
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(doc)
    bad = [r for r in results if not r[1]]
    for name, good, detail in results:
        print(f"{'ok  ' if good else 'FAIL'}  {name}{('  (' + detail + ')') if detail and not good else ''}")
    T = stats(S["data"])
    A = S["data"]["avatars"]
    print(f"worldforge console: {T['worlds']} worlds, {T['cards']} cards, {T['bldg_linked']}/{T['bldg_slots']} buildings linked, {T['avatars']} avatars bound, "
          f"avatar registry {'read (' + str(A.get('matched')) + ' rows)' if A['present'] and not A.get('error') else 'unreadable' if A['present'] else 'not built yet'}, "
          f"{T['omega_dns']}/{T['omegas']} Omegas defined-not-seated, {T['anchored']} anchored, redactions {S['redactions']}, {len(S['files'])} files read")
    print(f"---- worldforge console: {T['worlds']} worlds, {len(doc.encode()) // 1024} KB, stamp {st}, {len(bad)} failing worldforge console evals")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()

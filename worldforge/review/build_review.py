#!/usr/bin/env python3
"""WorldForge review: a 120-second review film and a pitch-deck-style whitepaper, rebuilt every 45-minute round.

    node worldforge/review/record.mjs                    # 1. record the 3D clips through worldforge/viewer.html
    python3 worldforge/review/build_review.py            # 2. film + captions + whitepaper + media + build.json
    python3 worldforge/review/build_review.py --no-film  #    whitepaper, captions and media only (fast)
    python3 worldforge/review/build_review.py --silent   #    film without narration even if macOS `say` works
    python3 worldforge/review/build_review.py --check    # whitepaper current? film present and 118-122 s?

The lead writes worldforge/review/round.json each round ({n, date, window, headline, landed[], doing[], next[],
gates[], worlds?[], modes?[]}). Every number on screen and on the page is read at build time from a registry file
(worldforge/out/**, worldforge/out/avatars/index.json, my-fabric/worlds/spaces_index.json, agents/hive/index.json,
evidence/heartbeat.log, atlas/roadmap.json, worlds/generated/teams/*.json) and the page names its source.

Two values move between rounds without the review changing: the heartbeat log gains a line every beat, and the hive
voices lines while a round runs. The build pins the beat line and the voiced-line count it printed in out/build.json;
--check rebuilds with those pinned values, confirms the pinned beat line is still in the log and the voiced count has
not fallen, and so stays current between rounds instead of flickering STALE every five minutes.

Outputs (worldforge/review/out/): review-film.mp4 (gitignored), review.vtt, whitepaper.html, media/*, build.json.
Writes nothing outside worldforge/review/ and $TMPDIR.
"""
import colorsys, glob, hashlib, html, json, math, os, re, shutil, subprocess, sys, tempfile

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
MEDIA = os.path.join(OUT, "media")
CLIPS = os.path.join(OUT, "clips")
FILM = os.path.join(OUT, "review-film.mp4")
VTT = os.path.join(OUT, "review.vtt")
PAGE = os.path.join(OUT, "whitepaper.html")
BUILD = os.path.join(OUT, "build.json")
FFMPEG = os.environ.get("FFMPEG") or os.path.join(ROOT, ".cache", "bin", "ffmpeg")

W, H, FPS = 960, 540, 24
SECTIONS = [("title", 8), ("landed", 18), ("worlds", 60), ("numbers", 14), ("next", 14), ("end", 6)]
TOTAL_S = sum(s for _, s in SECTIONS)
DEFAULT_WORLDS = ["locator-x", "cancer-dao", "s29-metaverse-dao"]
DEFAULT_MODES = ["flyin", "building", "omega", "orbit"]
EMAIL = "x@agifuturefoundation.org"
FORBIDDEN = ["agi-corp-worlds"]          # the private repository name never appears on the page or in the film
VOICE = "Samantha"                      # macOS system voice; labelled synthetic on the end card and on the page
X264 = ["-c:v", "libx264", "-preset", "veryfast", "-crf", "22", "-pix_fmt", "yuv420p", "-video_track_timescale", "12288",
        "-color_range", "tv", "-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709"]
# every segment ends in the same limited-range BT.709 4:2:0 so the concatenated stream never changes parameters mid-film
TAIL = "scale=out_range=tv:out_color_matrix=bt709,format=yuv420p,setsar=1,setparams=range=tv:colorspace=bt709:color_primaries=bt709:color_trc=bt709"
DISCLAIMER = ("Describes an organization being built. Nothing here is an offer to sell or a solicitation to buy any "
              "security or membership interest, and nothing here is legal, tax or financial advice.")

AVENIR = "/System/Library/Fonts/Avenir Next.ttc"   # the same faces atlas/build_film.py F() uses
FACES = {"bold": 0, "demi": 2, "medium": 5, "regular": 7, "heavy": 8, "light": 10}
BG0, BG1 = (6, 9, 24), (16, 14, 44)
CYAN, PURPLE, GOLD, GREEN, PINK, WHITE, MUTED = (0, 230, 230), (140, 80, 255), (255, 190, 40), (40, 230, 150), (255, 70, 140), (255, 255, 255), (150, 165, 195)
MASS = {"plaza": (199, 204, 214), "gate": (242, 191, 64), "council": (140, 107, 191), "seat": (178, 140, 230),
        "zone-pad": (102, 153, 178), "zone-hall": (158, 171, 184), "agent-avatar": (51, 204, 153)}  # build.mjs COLORS
MODE_LABEL = {"orbit": "Orbit", "flyin": "Fly-in", "building": "Building", "omega": "Omega Steward", "council": "Steward Council"}


def rel(p):
    return os.path.relpath(p, ROOT)


def R(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)


def opt(p):
    return R(p) if os.path.exists(os.path.join(ROOT, p)) else None


def die(msg):
    print(f"worldforge review FAILED: {msg}")
    sys.exit(1)


# ------------------------------------------------------------------------------------------------ registry reads
def load_round():
    path = os.path.join(HERE, "round.json")
    if not os.path.exists(path):
        die("no worldforge/review/round.json (copy round.template.json)")
    rd = json.load(open(path))
    for k in ("n", "date", "window", "headline"):
        if k not in rd:
            die(f"round.json has no '{k}'")
    for k in ("landed", "doing", "next", "gates"):
        if not isinstance(rd.get(k), list):
            die(f"round.json '{k}' must be a list")
    rd["worlds"] = rd.get("worlds") or DEFAULT_WORLDS
    rd["modes"] = rd.get("modes") or DEFAULT_MODES
    rd["placeholder"] = bool(rd.get("placeholder")) or "TODO by lead" in json.dumps({k: rd[k] for k in ("date", "window", "headline", "landed", "next")})
    return rd


def gate_text(g):
    if isinstance(g, dict):
        name = g.get("name") or g.get("gate") or g.get("id") or ""
        st = g.get("status") or g.get("state") or ""
        return f"{name}: {st}" if st else str(name)
    return str(g)


BEAT = re.compile(r"^(\d\d:\d\d:\d\d) (GREEN|RED|AMBER|YELLOW)\b")


def heartbeat_lines():
    p = os.path.join(ROOT, "evidence", "heartbeat.log")
    if not os.path.exists(p):
        return []
    return [l.rstrip("\n") for l in open(p, errors="replace") if BEAT.match(l)]


def parse_beat(line):
    if not line:
        return None
    m = BEAT.match(line)
    segs = {}
    for part in line.split(" | ")[1:]:
        if ":" in part:
            k, v = part.split(":", 1)
            segs[k.strip()] = v.strip()
    return {"time": m.group(1), "status": m.group(2), "segments": segs, "line": line}


KIND_ORDER = ["world", "plaza", "gate", "council", "seat", "omega", "coordinator", "advisor", "zone", "agent"]


def kind_rank(k):
    """Stable order for card kinds: the known kinds first, then any kind build.mjs adds later, alphabetically."""
    return (KIND_ORDER.index(k), "") if k in KIND_ORDER else (len(KIND_ORDER), k)


def plural(n, word):
    return f"{n} {word}" + ("" if n == 1 else "s")


def asset_validation(glbs):
    """Khronos validator results for the avatar GLBs (worldforge/out/assets/avatars/validation.json), counted only for
    files whose sha256 on disk still matches the one the validator saw."""
    val = opt("worldforge/out/assets/avatars/validation.json") or {}
    files = val.get("files") or {}
    out = {"validator": val.get("validator", ""), "glbs": len(glbs), "validated": 0, "errors": 0, "warnings": 0}
    for g in glbs:
        v = files.get(g)
        if not v:
            continue
        sha = hashlib.sha256(open(os.path.join(ROOT, "worldforge/out/assets/avatars", g), "rb").read()).hexdigest()
        if v.get("sha256") == sha:
            out["validated"] += 1
            out["errors"] += int(v.get("errors") or 0)
            out["warnings"] += int(v.get("warnings") or 0)
    return out


def load(pinned=None):
    """Everything the film and the page show, read from the registries. `pinned` replaces the two moving values."""
    rd = load_round()
    idx = R("worldforge/out/index.json")
    worlds = idx["worlds"]
    cards = {w["slug"]: R(f"worldforge/out/{w['slug']}/cards.json") for w in worlds}
    kinds, linked, slots, on_disk, bkinds = {}, 0, 0, 0, {}
    agents = 0
    omega_dns = seats = seats_empty = 0
    # avatars and bindings are counted on every card that carries one, whatever its kind (agent, coordinator,
    # advisor, omega, and any kind build.mjs adds later), and reported per kind and per avatar role
    av_kind, bound_kind, kind_note, avatar_roles, av_kind_role, model_refs = {}, {}, {}, {}, {}, set()
    reserved = None
    for slug, doc in cards.items():
        for c in doc["cards"]:
            k = c["kind"]
            kinds[k] = kinds.get(k, 0) + 1
            if reserved is None and c.get("reserved_for_humans"):
                reserved = [x["action"] for x in c["reserved_for_humans"]]
            if k in ("zone", "council"):
                slots += 1
                b = c.get("building") or {}
                if b.get("kind"):
                    bkinds[b["kind"]] = bkinds.get(b["kind"], 0) + 1
                if b.get("exterior") and b.get("interior"):
                    linked += 1
                    if all(os.path.exists(os.path.join(ROOT, b[x])) for x in ("exterior", "interior") if b.get(x)):
                        on_disk += 1
            if k == "agent":
                agents += 1
            bd = c.get("binding") or {}
            if bd.get("swarm") and bd.get("metaprompt") and bd.get("fabricNode"):
                bound_kind[k] = bound_kind.get(k, 0) + 1
            av = c.get("avatar") or {}
            if av.get("model_ref"):
                av_kind[k] = av_kind.get(k, 0) + 1
                model_refs.add(av["model_ref"])
                role = av.get("role") or "?"
                avatar_roles[role] = avatar_roles.get(role, 0) + 1
                kr = av_kind_role.setdefault(k, {})
                kr[role] = kr.get(role, 0) + 1
                if k not in kind_note and c.get("note"):
                    kind_note[k] = c["note"]
            if k == "omega":
                if c.get("status") == "defined, not seated" and c.get("seated_agent") is None:
                    omega_dns += 1
            if k == "seat":
                seats += 1
                if c.get("seated") is None:
                    seats_empty += 1
    if sum(kinds.values()) != idx["totals"]["cards"]:
        die(f"the cards.json files hold {sum(kinds.values())} cards but worldforge/out/index.json totals.cards is "
            f"{idx['totals']['cards']} (worldforge/out mid-rebuild? run node worldforge/build.mjs, then rebuild)")
    models_present = sorted(m for m in model_refs if os.path.exists(os.path.join(ROOT, m)))

    av_idx = opt("worldforge/out/avatars/index.json")
    av_tot = (av_idx or {}).get("totals") or {}
    av_assets = opt("worldforge/out/assets/avatars/index.json")
    asset_glbs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "worldforge/out/assets/avatars/*.glb")))
    glb_val = asset_validation(asset_glbs) if av_assets else None

    spaces = opt("my-fabric/worlds/spaces_index.json") or {}
    hive = opt("agents/hive/index.json") or {}
    htot = dict(hive.get("totals") or {})
    beats = heartbeat_lines()
    beat_line = (pinned or {}).get("heartbeat_line") if pinned else (beats[-1] if beats else None)
    if pinned and "hive_spoken" in pinned:
        htot["spoken_now"] = htot.get("spoken")
        htot["spoken"] = pinned["hive_spoken"]

    first = rd["worlds"][0] if rd["worlds"][0] in cards else worlds[0]["slug"]
    manifest = R(f"worldforge/out/{first}/manifest.json")
    roadmap = opt("atlas/roadmap.json") or {}
    founder = [{"name": p["name"], "status": p["status"], "gate": p.get("gate", "")} for p in roadmap.get("phases", []) if p.get("status") != "done"]

    names = {w["slug"]: w["name"] for w in worlds}
    featured = []
    for slug in rd["worlds"]:
        if slug not in cards:
            die(f"round.json names world '{slug}', which worldforge/out/index.json does not list")
        cs = cards[slug]["cards"]
        wc = next(c for c in cs if c["kind"] == "world")
        zones = [c for c in cs if c["kind"] == "zone"]
        bz = next((c for c in zones if (c.get("building") or {}).get("exterior")), None)
        om = next((c for c in cs if c["kind"] == "omega"), None)
        team = opt(f"worlds/generated/teams/{slug}.json") or {}
        fav = {}
        for c in cs:
            if (c.get("avatar") or {}).get("model_ref"):
                fav[c["kind"]] = fav.get(c["kind"], 0) + 1
        fseats = [c for c in cs if c["kind"] == "seat"]
        featured.append({
            "slug": slug, "name": names[slug], "tagline": wc.get("tagline", ""), "brand": team.get("brand") or {},
            "zones": [z["name"] for z in zones], "agents": sum(1 for c in cs if c["kind"] == "agent"),
            "avatars": dict(sorted(fav.items(), key=lambda kv: kind_rank(kv[0]))),
            "seats": len(fseats), "seats_empty": sum(1 for c in fseats if c.get("seated") is None),
            "building": ({"zone": bz["name"], "kind": bz["building"]["kind"], "res": (bz["building"].get("resolution") or {})} if bz else None),
            "omega": ({"name": om["name"], "status": om["status"], "persona": om.get("persona") or {},
                       "greet": next((l["text"] for l in (om.get("voice") or {}).get("lines", []) if l["id"] == "greet"), ""),
                       "kokoro": (om.get("voice") or {}).get("kokoro")} if om else None),
        })
    brands = {}
    for w in worlds:
        t = opt(f"worlds/generated/teams/{w['slug']}.json") or {}
        brands[w["slug"]] = t.get("brand") or {}

    # the 3D section: this round's clips, else WorldForge stills, else plan views drawn from the blockout
    clips = []
    ci = opt(rel(os.path.join(CLIPS, "index.json")))
    if ci and ci.get("round") == rd["n"]:
        for c in ci.get("clips", []):
            if os.path.exists(os.path.join(ROOT, c["file"])):
                clips.append({"slug": c["slug"], "mode": c["mode"], "file": c["file"], "seconds": c.get("seconds", 5)})
    stills = sorted(rel(p) for p in glob.glob(os.path.join(ROOT, "worldforge/out/stills/*.jpg")))
    three_d = "clips" if clips else ("stills" if stills else "plans")

    rep = {k: next((c for c in cards[first]["cards"] if c["kind"] == k), None) for k in ("world", "plaza", "zone", "agent", "council", "omega")}
    by_rank = lambda d: dict(sorted(d.items(), key=lambda kv: kind_rank(kv[0])))
    return {
        "round": rd, "index": idx, "totals": idx["totals"], "broken": idx.get("broken", []), "kinds": by_rank(kinds),
        "buildings": {"linked": linked, "slots": slots, "on_disk": on_disk, "kinds": dict(sorted(bkinds.items(), key=lambda kv: (-kv[1], kv[0])))},
        "agents": agents, "bound": sum(bound_kind.values()), "bound_kind": by_rank(bound_kind),
        "with_avatar": sum(av_kind.values()), "avatar_kind": by_rank(av_kind), "kind_note": kind_note,
        "avatar_kind_roles": {k: dict(sorted(v.items())) for k, v in av_kind_role.items()},
        "avatar_roles": dict(sorted(avatar_roles.items())), "model_refs": sorted(model_refs), "models_present": models_present,
        "avatars_index": av_tot, "avatar_assets": av_assets, "asset_glbs": asset_glbs, "glb_validation": glb_val,
        "omega_dns": omega_dns, "seats": seats, "seats_empty": seats_empty, "reserved": reserved or [],
        "spaces": spaces, "hive": {"totals": htot, "engine": hive.get("voice_engine") or {}, "note": hive.get("note", "")},
        "beat": parse_beat(beat_line), "gates": manifest.get("gates", {}), "gates_src": f"worldforge/out/{first}/manifest.json",
        "founder": founder, "featured": featured, "names": names, "brands": brands, "worlds": worlds,
        "clips": clips, "stills": stills, "three_d": three_d, "rep": rep, "first": first,
        "narration": (pinned or {}).get("narration"),
    }


def hue_rgb(h, l=0.6, s=0.75):
    r, g, b = colorsys.hls_to_rgb(((h or 0) % 360) / 360, l, s)
    return int(r * 255), int(g * 255), int(b * 255)


def open_gates(D):
    return [k for k, v in D["gates"].items() if not str(v).startswith("done")]


# ------------------------------------------------------------------------------------------------ film plan
def and_list(xs):
    xs = list(xs)
    return ", ".join(xs[:-1]) + (" and " if len(xs) > 1 else "") + (xs[-1] if xs else "")


MODE_PHRASE = {"flyin": "a fly-in", "building": "a building and its interior", "omega": "the Omega Steward",
               "orbit": "an orbit", "council": "the Steward Council and its empty seats"}


def still_slug(D, path):
    """The world a still shows, only when its file name starts with that world's slug; otherwise None."""
    stem = os.path.splitext(os.path.basename(path))[0]
    return next((w for w in sorted(D["names"], key=len, reverse=True) if stem == w or stem.startswith(w + "-")), None)


def worlds_line(D):
    f = D["featured"]
    names = and_list(x["name"] for x in f)
    if D["three_d"] == "clips":
        # read from the clips actually cut in, in the order round.json lists worlds and modes
        modes = [m for m in D["round"]["modes"] if any(c["mode"] == m for c in D["clips"])]
        shown = [x for x in f if any(c["slug"] == x["slug"] for c in D["clips"])]
        every = all(any(c["slug"] == x["slug"] and c["mode"] == m for c in D["clips"]) for x in shown for m in modes)
        return (f"{and_list(x['name'] for x in shown)}, recorded in the WorldForge viewer: "
                f"{and_list(MODE_PHRASE.get(m, m) for m in modes)}" + (" of each world." if every and len(shown) > 1 else "."))
    if D["three_d"] == "stills":
        used = D["stills"][:12]
        named = []
        for s in used:
            sl = still_slug(D, s)
            if sl and D["names"][sl] not in named:
                named.append(D["names"][sl])
        line = "No 3D clips were recorded this round, so these are stills from the WorldForge stills folder"
        line += f", showing {and_list(named)}" if named else ""
        line += f", and plan views of {names}." if len(used) < 3 else "."
        return line
    return f"No 3D clips were recorded this round, so these are plan views of {names}, drawn from each world's generated blockout."


def narration_lines(D):
    rd, t = D["round"], D["totals"]
    landed = rd["landed"][:3]
    lines = {
        "title": (f"WorldForge review {rd['n']}. You are hearing a synthetic voice." if (D["narration"] or "").startswith("say:")
                  else f"WorldForge review {rd['n']}. This cut is silent: captions only, no narration."),
        "landed": "Landed this round: " + "; ".join(landed) + "." if landed else "Nothing is listed as landed this round.",
        "worlds": worlds_line(D),
        "numbers": (f"{t['worlds']} worlds, {t['cards']} master cards, {t['evals']} evals with {t['failed']} failing. "
                    f"{D['buildings']['linked']} buildings linked. {D['omega_dns']} Omega Stewards, defined, not seated."),
        "next": ("Next: " + "; ".join(rd["next"][:2]) + ". " if rd["next"] else "") + f"{len(open_gates(D))} WorldForge gates are still open.",
        "end": "Not mounted in Sneeze yet. Omegas are defined, not seated. " + ("The voice was synthetic." if (D["narration"] or "").startswith("say:") else "Omega voices are synthetic."),
    }
    return lines


def lower_third_text(D, slug, mode):
    f = next(x for x in D["featured"] if x["slug"] == slug)
    if mode == "flyin":
        return "Fly-in", f"From high above the Alignment Evaluation Gate down to the {f['name']} plaza"
    if mode == "building":
        b = f["building"]
        if not b:
            return "Building", "First zone building (none linked in the cards)"
        res = b["res"].get("exterior")
        return f"Building · {b['zone']}", f"Up to the {b['kind']} door, then inside the interior" + (f" ({res} px exterior textures)" if res else "")
    if mode == "omega":
        return "Omega Steward", "Defined, not seated · beside the Steward Council · synthetic voice"
    if mode == "council":
        return "Steward Council", f"{f['seats']} human seats, {f['seats_empty']} empty · 2 of 3 signed votes decide"
    av = f["avatars"]
    return "Orbit", (f"{plural(len(f['zones']), 'zone')} · avatars on {sum(av.values())} cards ("
                     + ", ".join(f"{n} {k}" for k, n in av.items()) + f") · {f['seats_empty']} of {f['seats']} human seats empty")


def still_label(D, path):
    """(slug, title, desc) for a still, from its file name alone: a world only when the name starts with its slug, the
    viewer only for viewer-<mode>.jpg; anything else is labelled by its path and nothing more."""
    base = os.path.basename(path)
    stem = os.path.splitext(base)[0]
    slug = still_slug(D, path)
    if slug:
        rest = stem[len(slug):].lstrip("-")
        return slug, D["names"][slug], (f"Still: {MODE_LABEL.get(rest, rest.replace('-', ' '))} · " if rest else "Still · ") + f"worldforge/out/stills/{base}"
    if stem.startswith("viewer-") and stem[7:] in MODE_LABEL:
        return None, f"WorldForge viewer · {MODE_LABEL[stem[7:]]}", f"Still from the viewer (no world named in the file) · worldforge/out/stills/{base}"
    return None, stem.replace("-", " ").capitalize(), f"Still · worldforge/out/stills/{base}"


def three_d_items(D):
    """(kind, source, slug, title, desc) for the 3D section, in order."""
    if D["three_d"] == "clips":
        return [("clip", c["file"], c["slug"]) + lower_third_text(D, c["slug"], c["mode"]) for c in D["clips"]]
    if D["three_d"] == "stills":
        items = []
        for s in D["stills"][:12]:
            items.append(("still", s) + still_label(D, s))
        if len(items) < 3:   # one or two stills cannot carry a minute: add the plan views of the featured worlds
            items += [("plan", f"media/plan-{f['slug']}.png", f["slug"], f["name"], f"Plan view: {len(f['zones'])} zones, {f['agents']} agents, gate south, Steward Council north")
                      for f in D["featured"]]
        return items
    return [("plan", f"media/plan-{f['slug']}.png", f["slug"], f["name"], f"Plan view: {len(f['zones'])} zones, {f['agents']} agents, gate south, Steward Council north")
            for f in D["featured"]]


def item_head(D, slug, title):
    """The world name first (when the item belongs to a world), then what is shown: same text on screen and in the VTT."""
    name = D["names"].get(slug, title) if slug else title
    return f"{name}  ·  {title}" if title != name else name


def split_frames(total, n):
    base, extra = divmod(total, n)
    return [base + (1 if i < extra else 0) for i in range(n)]


def film_plan(D):
    """Segments with exact frame counts (sum = 120 s at 24 fps) and the caption cues."""
    lines = narration_lines(D)
    segs, cues, t0 = [], [], 0
    for name, dur in SECTIONS:
        n = dur * FPS
        if name == "worlds":
            items = three_d_items(D)
            for (kind, src, slug, title, desc), fr in zip(items, split_frames(n, len(items))):
                segs.append({"section": name, "kind": kind, "src": src, "slug": slug, "title": title, "desc": desc, "frames": fr})
        else:
            segs.append({"section": name, "kind": "card", "frames": n})
        cues.append((t0, t0 + dur, lines[name]))
        t0 += dur
    # per-item captions inside the 3D section
    t = SECTIONS[0][1] + SECTIONS[1][1]
    item_cues = []
    for s in segs:
        if s["section"] == "worlds":
            item_cues.append((t, t + s["frames"] / FPS, f"{item_head(D, s['slug'], s['title'])} · {s['desc']}".replace("  ·  ", " · ")))
            t += s["frames"] / FPS
    assert sum(s["frames"] for s in segs) == TOTAL_S * FPS
    return segs, cues, item_cues, lines


def vtt_cues(D):
    """[[start_s, end_s, text], ...] for the film's caption track (rounded to the millisecond, JSON-safe)."""
    segs, cues, item_cues, _ = film_plan(D)
    out = []
    w0 = SECTIONS[0][1] + SECTIONS[1][1]
    for a, b, text in cues:
        if a == w0:
            out.append([a + 0.2, a + 6, text])
            for ia, ib, it in item_cues:
                st = max(ia, a + 6)
                if st < ib - 0.3:      # an item fully covered by the section line gets no cue of its own
                    out.append([st, ib - 0.05, it])
            continue
        out.append([a + 0.2, b - 0.2, text])
    return [[round(a, 3), round(b, 3), t] for a, b, t in out]


def vtt_render(n, cues):
    ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}"
    out = ["WEBVTT", "", f"NOTE WorldForge Review {n} captions, built by worldforge/review/build_review.py", ""]
    for i, (a, b, text) in enumerate(cues, 1):
        out += [str(i), f"{ts(a)} --> {ts(b)}", text, ""]
    return "\n".join(out)


def vtt_text(D, film=None):
    """The captions belong to the film: once a film has been cut, they are rendered from the cues it stored in
    build.json, so a --no-film rebuild (or registry drift) never makes the caption track disagree with the picture."""
    if film and film.get("captions"):
        return vtt_render(film.get("round"), film["captions"])
    return vtt_render(D["round"]["n"], vtt_cues(D))


def plan_sha(D):
    segs, cues, item_cues, lines = film_plan(D)
    shown = {"round": D["round"], "segs": segs, "lines": lines, "numbers": numbers_tiles(D), "gates": D["gates"],
             "narration": D["narration"], "three_d": D["three_d"]}
    return hashlib.sha256(json.dumps(shown, sort_keys=True, default=str).encode()).hexdigest()[:16]


def numbers_tiles(D):
    t, b, ht = D["totals"], D["buildings"], D["hive"]["totals"]
    av = D["avatars_index"]
    broken_ok = sum(1 for x in D["broken"] if x.get("ok"))
    tiles = [
        (str(t["worlds"]), "worlds", f"{t['anchored']} with an RP1 anchor", CYAN),
        (str(t["cards"]), "GLEWME Master Cards", f"{t['primitives']} primitives in the GLBs", PURPLE),
        (str(t["evals"]), f"evals · {t['failed']} failing", f"{broken_ok}/{len(D['broken'])} broken worlds fail only their own check", GREEN),
        (f"{b['linked']}/{b['slots']}", "buildings linked", f"{(D['spaces'].get('totals') or {}).get('exteriors', '?')} exteriors, {(D['spaces'].get('totals') or {}).get('interiors', '?')} interiors in spaces_index", GOLD),
    ]
    gv = D["glb_validation"]
    sub = []
    if av.get("avatars") is not None:
        sub.append(f"registry: {av['avatars']}, {av.get('evals', '?')} evals, {av.get('failing', '?')} failing")
    if gv:
        sub.append(f"{gv['validated']}/{gv['glbs']} GLBs validated, {gv['errors']} errors")
    if not sub:
        sub.append(f"{D['bound']} bound to swarm + metaprompt")
    tiles.append((str(D["with_avatar"]), "cards carry an avatar", " · ".join(sub), PINK))
    tiles.append((str(D["omega_dns"]), "Omegas defined, not seated", f"hive: {ht.get('spoken', '?')} of {ht.get('lines', '?')} lines voiced", CYAN))
    return tiles


# ------------------------------------------------------------------------------------------------ drawing
_fonts = {}


def F(face, size):
    k = (face, size)
    if k not in _fonts:
        try:
            _fonts[k] = ImageFont.truetype(AVENIR, size, index=FACES[face])
        except OSError:
            _fonts[k] = ImageFont.truetype("/System/Library/Fonts/Supplemental/Arial.ttf", size)
    return _fonts[k]


def wrap(s, font, width):
    words, lines, cur = str(s).split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if font.getlength(t) <= width or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    if cur:
        lines.append(cur)
    return lines


def clamp_lines(lines, font, width, n):
    if len(lines) <= n:
        return lines
    out = lines[:n]
    last = out[-1]
    while last and font.getlength(last + "…") > width:
        last = last[:-1]
    out[-1] = last.rstrip() + "…"
    return out


def ease(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3 - 2 * x)


def col(c, a):
    return tuple(c[:3]) + (int(255 * max(0.0, min(1.0, a))),)


def tracked(d, xy, s, font, fill, track=3, anchor="la"):
    x, y = xy
    if anchor[0] == "r":
        x -= sum(font.getlength(ch) + track for ch in s) - track
    for ch in s:
        d.text((x, y), ch, font=font, fill=fill, anchor="l" + anchor[1])
        x += font.getlength(ch) + track


def fit_font(s, face, size, width, minsize=18):
    while size > minsize and F(face, size).getlength(s) > width:
        size -= 2
    return F(face, size)


_bg = None


def background():
    global _bg
    if _bg is None:
        img = Image.new("RGB", (W, H))
        d = ImageDraw.Draw(img)
        for y in range(H):
            t = y / H
            d.line([(0, y), (W, y)], fill=tuple(int(BG0[i] * (1 - t) + BG1[i] * t) for i in range(3)))
        glow = Image.radial_gradient("L").resize((1000, 1000)).point(lambda v: int(max(0.0, 1 - v / 160) ** 1.6 * 55))
        for cx, cy, c in ((170, 110, PURPLE), (830, 440, CYAN)):
            mask = Image.new("L", (W, H), 0)
            mask.paste(glow, (cx - 500, cy - 500))
            img = Image.composite(Image.new("RGB", (W, H), c), img, mask)
        _bg = img
    return _bg.copy()


def chrome(d, D, eyebrow, source=None, footer=True):
    tracked(d, (56, 40), eyebrow.upper(), F("demi", 13), col(CYAN, 1))
    tracked(d, (W - 56, 40), f"WORLDFORGE REVIEW {D['round']['n']}", F("demi", 12), col(MUTED, 1), anchor="ra")
    s = "PLACEHOLDER ROUND FILE · TODO BY LEAD"
    f = F("demi", 12); w = f.getlength(s) + 24
    if footer:
        d.text((56, H - 34), "Powered by AGI Corp", font=F("demi", 13), fill=col(MUTED, 1))
        if source:
            x = 56 + F("demi", 13).getlength("Powered by AGI Corp") + 14
            room = (W - 56 - w - 14 if D["round"]["placeholder"] else W - 56) - x   # never runs under the badge
            d.text((x, H - 33), clamp_lines([f"·  source: {source}"], F("regular", 12), room, 1)[0], font=F("regular", 12), fill=col(MUTED, 1))
    if D["round"]["placeholder"]:
        d.rounded_rectangle([W - 56 - w, H - 44, W - 56, H - 18], 13, fill=col(GOLD, 0.16), outline=col(GOLD, 0.9))
        d.text((W - 56 - w / 2, H - 31), s, font=f, fill=col(GOLD, 1), anchor="mm")


def caption_strip(img, text):
    d = ImageDraw.Draw(img, "RGBA")
    f = F("medium", 17)
    lines = clamp_lines(wrap(text, f, W - 160), f, W - 160, 2)
    h = 16 + 24 * len(lines)
    d.rectangle([0, H - 62 - h, W, H - 62], fill=(0, 0, 0, 150))
    for i, l in enumerate(lines):
        d.text((W / 2, H - 62 - h + 10 + i * 24), l, font=f, fill=(255, 255, 255, 240), anchor="ma")


def card_title(D, t, dur, silent=False):
    """silent=True lifts the whole block 50 px so the burned-in caption strip (bottom edge H-62) clears 'Powered by'."""
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    rd = D["round"]
    a = ease(t / 0.8) * ease((dur - t) / 0.5)
    chrome(d, D, "AGI Future Foundation PBC · SmartCiti.X virtual worlds", footer=False)
    s = f"WorldForge Review {rd['n']} · {rd['window']}"
    f = fit_font(s, "bold", 54, W - 112)
    lift = 50 if silent else 0
    y = 150 - lift + int(14 * (1 - ease(t / 1.0)))
    d.text((56, y), s, font=f, fill=col(WHITE, a))
    yy = y + f.size + 26
    for l in clamp_lines(wrap(rd["headline"], F("medium", 24), W - 140), F("medium", 24), W - 140, 3):
        d.text((56, yy), l, font=F("medium", 24), fill=col((220, 228, 245), a * ease((t - 0.6) / 0.8))); yy += 34
    d.text((56, yy + 14), str(rd["date"]), font=F("regular", 16), fill=col(MUTED, a * ease((t - 0.9) / 0.8)))
    d.line([(56, 400 - lift), (56 + 300 * ease((t - 0.4) / 1.4), 400 - lift)], fill=col(CYAN, a), width=3)
    d.text((56, 418 - lift), "Powered by AGI Corp", font=F("demi", 30), fill=col(CYAN, a * ease((t - 1.0) / 0.8)))
    return img


def card_landed(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    rd = D["round"]
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, D, f"Landed this round · review {rd['n']}", "worldforge/review/round.json")
    d.text((56, 70), "What landed", font=F("bold", 40), fill=col(WHITE, a))
    items = rd["landed"][:6]
    f = F("medium", 19)
    width = W - 112 - 40
    per = [clamp_lines(wrap(x, f, width), f, width, 2) for x in items]
    total = sum(len(p) * 25 + 12 for p in per)
    if total > 330:
        per = [clamp_lines(wrap(x, f, width), f, width, 1) for x in items]
    y = 140
    for i, lines in enumerate(per):
        ai = a * ease((t - 0.8 - i * 1.3) / 0.5)
        dx = int(18 * (1 - ease((t - 0.8 - i * 1.3) / 0.5)))
        d.ellipse([56 + dx, y + 3, 76 + dx, y + 23], outline=col(GREEN, ai), width=2)
        d.line([(61 + dx, y + 13), (65 + dx, y + 18), (72 + dx, y + 8)], fill=col(GREEN, ai), width=2)
        for j, l in enumerate(lines):
            d.text((96 + dx, y + j * 25), l, font=f, fill=col(WHITE, ai * (1 if j == 0 else 0.85)))
        y += len(lines) * 25 + 14
    if not items:
        d.text((56, 150), "round.json lists nothing as landed", font=F("medium", 22), fill=col(MUTED, a))
    if len(rd["landed"]) > 6:
        d.text((96, y + 4), f"+{len(rd['landed']) - 6} more on the whitepaper's Review slide", font=F("regular", 15), fill=col(MUTED, a))
    return img


def card_numbers(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, D, "By the numbers · read from the registries at build time", "worldforge/out/{index, avatars, assets/avatars}, spaces_index, hive")
    d.text((56, 70), "By the numbers", font=F("bold", 40), fill=col(WHITE, a))
    tiles = numbers_tiles(D)
    gw, gh, gx, gy = (W - 112 - 2 * 20) / 3, 150, 20, 20
    for i, (num, label, sub, c) in enumerate(tiles):
        x = 56 + (i % 3) * (gw + gx); y = 140 + (i // 3) * (gh + gy)
        ai = a * ease((t - 0.3 - i * 0.25) / 0.5)
        d.rounded_rectangle([x, y, x + gw, y + gh], 14, fill=col(c, 0.08 * ai), outline=col(c, 0.55 * ai), width=1)
        # count up: digits roll from 0 to the registry value over a second
        k = ease((t - 0.3 - i * 0.25) / 1.1)
        shown = re.sub(r"\d+", lambda m: str(int(round(int(m.group()) * k))), num)
        d.text((x + 18, y + 14), shown, font=fit_font(num, "bold", 46, gw - 36), fill=col(c, ai))
        d.text((x + 18, y + 76), label, font=fit_font(label, "demi", 17, gw - 36, 12), fill=col(WHITE, ai))
        for j, l in enumerate(clamp_lines(wrap(sub, F("regular", 13), gw - 36), F("regular", 13), gw - 36, 2)):
            d.text((x + 18, y + 102 + j * 17), l, font=F("regular", 13), fill=col(MUTED, ai))
    return img


def status_color(s):
    s = str(s)
    return GREEN if s.startswith("done") else (CYAN if s.startswith("prepared") else (PINK if s.startswith("fail") else GOLD))


def card_next(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    rd = D["round"]
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, D, "Next + gates", f"round.json, {D['gates_src']}")
    d.text((56, 70), "Next", font=F("bold", 36), fill=col(WHITE, a))
    f = F("medium", 18); width = 380
    y = 128
    for i, x in enumerate(rd["next"][:4]):
        ai = a * ease((t - 0.5 - i * 0.6) / 0.5)
        d.polygon([(58, y + 7), (58, y + 19), (68, y + 13)], fill=col(CYAN, ai))
        lines = clamp_lines(wrap(x, f, width), f, width, 3)
        for j, l in enumerate(lines):
            d.text((84, y + j * 24), l, font=f, fill=col(WHITE, ai))
        y += len(lines) * 24 + 14
    if not rd["next"]:
        d.text((56, y), "round.json lists nothing next", font=f, fill=col(MUTED, a))
    x0 = 500
    d.text((x0, 70), "Gates", font=F("bold", 36), fill=col(WHITE, a))
    y = 128
    for i, (g, st) in enumerate(D["gates"].items()):
        ai = a * ease((t - 1.0 - i * 0.35) / 0.5)
        c = status_color(st)
        label = str(st).split(":")[0]
        pf = F("demi", 12); pw = pf.getlength(label) + 18
        d.rounded_rectangle([x0, y, x0 + pw, y + 22], 11, fill=col(c, 0.18 * ai), outline=col(c, 0.9 * ai))
        d.text((x0 + pw / 2, y + 11), label, font=pf, fill=col(c, ai), anchor="mm")
        for j, l in enumerate(clamp_lines(wrap(g, F("medium", 15), W - 56 - x0 - pw - 12), F("medium", 15), W - 56 - x0 - pw - 12, 2)):
            d.text((x0 + pw + 12, y + 2 + j * 19), l, font=F("medium", 15), fill=col(WHITE, ai))
        y += 40
    rg = [gate_text(g) for g in rd["gates"][:3]]
    if rg:
        d.text((x0, y + 6), "This round", font=F("demi", 14), fill=col(CYAN, a)); y += 30
        for i, g in enumerate(rg):
            ai = a * ease((t - 3.0 - i * 0.4) / 0.5)
            for j, l in enumerate(clamp_lines(wrap(g, F("regular", 14), W - 56 - x0), F("regular", 14), W - 56 - x0, 2)):
                d.text((x0, y + j * 18), l, font=F("regular", 14), fill=col((220, 228, 245), ai))
            y += 40
    return img


def end_claims(D):
    og = open_gates(D)
    narr = D["narration"] or "silent"
    three = {"clips": "3D clips rendered in headless Chrome (software WebGL) from the viewer; generated geometry, no imported coordinates",
             "stills": "3D clips not recorded this round: stills from worldforge/out/stills, labelled by file name",
             "plans": "3D clips not recorded this round: plan views drawn from each generated blockout"}[D["three_d"]]
    return [
        "Not mounted in Sneeze yet: gates " + (", ".join(g.split(" ")[0] for g in og) + " not done" if og else "all done"),
        f"Omegas defined, not seated · {D['seats_empty']} of {D['seats']} human seats empty",
        (f"Synthetic voices: narration is the macOS system voice ({narr.split(':', 1)[1]}); Omega lines are Kokoro" if narr.startswith("say:")
         else "Silent film: no narration this round, captions burned in; Omega voices are synthetic (Kokoro)"),
        three,
    ]


def card_end(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.4) * ease((dur - t) / 0.6)
    chrome(d, D, "What this film does not claim")
    d.text((56, 70), "Plainly", font=F("bold", 40), fill=col(WHITE, a))
    y = 140
    f = F("medium", 19)
    for i, s in enumerate(end_claims(D)):
        ai = a * ease((t - 0.2 - i * 0.35) / 0.4)
        d.rectangle([56, y + 4, 60, y + 22], fill=col(GOLD, ai))
        for j, l in enumerate(clamp_lines(wrap(s, f, W - 150), f, W - 150, 2)):
            d.text((76, y + j * 25), l, font=f, fill=col(WHITE, ai))
        y += 25 * len(clamp_lines(wrap(s, f, W - 150), f, W - 150, 2)) + 18
    d.text((56, y + 18), f"Powered by AGI Corp · {EMAIL}", font=F("demi", 20), fill=col(CYAN, a))
    return img


CARDS = {"title": card_title, "landed": card_landed, "numbers": card_numbers, "next": card_next, "end": card_end}


def lower_third(D, slug, title, desc, k, n, banner=None):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(400, H):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(200 * (y - 400) / (H - 400))))
    for y in range(0, 80):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(130 * (1 - y / 80))))
    tracked(d, (40, 22), f"WORLDFORGE REVIEW {D['round']['n']} · 3D", F("demi", 12), (255, 255, 255, 220))
    d.text((W - 40, 22), f"{k}/{n}", font=F("demi", 13), fill=(255, 255, 255, 200), anchor="ra")
    f = next((x for x in D["featured"] if x["slug"] == slug), None)
    hue = (f or {}).get("brand", {}).get("hue") if f else D["brands"].get(slug, {}).get("hue")
    accent = hue_rgb(hue) if hue is not None else CYAN
    mark = ((f or {}).get("brand", {}).get("mark") if f else D["brands"].get(slug, {}).get("mark")) or ""
    x = 40
    if mark:
        d.rounded_rectangle([x, 452, x + 54, 506], 10, fill=accent + (235,))
        d.text((x + 27, 479), mark, font=fit_font(mark, "bold", 22, 46, 10), fill=(10, 12, 24, 255), anchor="mm")
        x += 70
    head = item_head(D, slug, title)
    d.text((x, 450), head, font=fit_font(head, "bold", 26, W - x - 40, 16), fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 160))
    d.text((x, 486), desc, font=fit_font(desc, "medium", 17, W - x - 40, 12), fill=accent + (255,), stroke_width=1, stroke_fill=(0, 0, 0, 200))
    if banner:
        bf = F("demi", 15); bw = bf.getlength(banner) + 28
        d.rounded_rectangle([W / 2 - bw / 2, 42, W / 2 + bw / 2, 70], 14, fill=col(GOLD, 0.22), outline=col(GOLD, 0.95))
        d.text((W / 2, 56), banner, font=bf, fill=col(GOLD, 1), anchor="mm")
    return img


def plan_image(slug, D):
    """A plan view drawn from worldforge/out/<slug>/blockout.generated.json (deterministic PNG)."""
    bo = R(f"worldforge/out/{slug}/blockout.generated.json")
    f = next((x for x in D["featured"] if x["slug"] == slug), None) or {"name": D["names"][slug], "tagline": "", "zones": [], "brand": D["brands"].get(slug, {})}
    hue = (f.get("brand") or {}).get("hue")
    accent = hue_rgb(hue) if hue is not None else CYAN
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    ext = bo["coordinateFrame"]["extentXZ"][1]
    S, ox, oy = 340, 70, 92
    sc = S / (2 * ext)
    P = lambda x, z: (ox + (x + ext) * sc, oy + (z + ext) * sc)
    d.rounded_rectangle([ox, oy, ox + S, oy + S], 12, fill=(26, 34, 30, 255), outline=(60, 72, 70, 255))
    for r in bo["roads"]:
        d.line([P(*r["startXZ"]), P(*r["endXZ"])], fill=(78, 80, 88, 255), width=max(2, int(r["widthMeters"] * sc)))
    order = ["plaza", "zone-pad", "zone-hall", "council", "seat", "gate", "agent-avatar"]
    for p in sorted(bo["primitives"], key=lambda p: order.index(p["massingType"]) if p["massingType"] in order else 99):
        x, _, z = p["position"]; w, _, dd = p["dimensions"]
        c = MASS.get(p["massingType"], (180, 180, 180))
        if p["massingType"] == "zone-pad":
            c = tuple(int(c[i] * 0.5 + accent[i] * 0.5) for i in range(3))
        if p["massingType"] == "agent-avatar":
            cx, cy = P(x, z); r = 3.2
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c + (255,), outline=(10, 12, 24, 255))
            continue
        (x0, y0), (x1, y1) = P(x - w / 2, z - dd / 2), P(x + w / 2, z + dd / 2)
        if p["shape"] == "pad" and p["massingType"] == "plaza":
            d.ellipse([x0, y0, x1, y1], fill=c + (230,))
        else:
            d.rectangle([x0, y0, x1, y1], fill=c + (235,), outline=(10, 12, 24, 200))
    for z in bo["zones"]:
        cx, cy = P(*z["centerXZ"])
        lab = z["displayName"]
        fz = F("demi", 10)
        lab = clamp_lines([lab], fz, 100, 1)[0]
        d.text((cx, cy + 19), lab, font=fz, fill=(240, 244, 255, 255), anchor="ma", stroke_width=2, stroke_fill=(10, 12, 24, 255))
    d.text(P(0, ext - 8), "gate", font=F("demi", 11), fill=col(GOLD, 1), anchor="mb")
    d.text(P(0, -ext + 4), "Steward Council", font=F("demi", 11), fill=col((200, 170, 255), 1), anchor="mt")
    x, xr = 450, W - 70
    tracked(d, (x, 94), "PLAN VIEW · GENERATED BLOCKOUT", F("demi", 11), col(CYAN, 1))
    y = 112
    for l in clamp_lines(wrap(f["name"], F("bold", 28), xr - x), F("bold", 28), xr - x, 1):
        d.text((x, y), l, font=F("bold", 28), fill=col(WHITE, 1)); y += 36
    for l in clamp_lines(wrap(f.get("tagline", ""), F("regular", 13), xr - x), F("regular", 13), xr - x, 2):
        d.text((x, y), l, font=F("regular", 13), fill=col(MUTED, 1)); y += 17
    y += 10
    for i, z in enumerate(bo["zones"][:7]):
        d.rectangle([x, y + 4, x + 9, y + 13], fill=accent + (255,))
        d.text((x + 16, y), clamp_lines([z["displayName"]], F("medium", 14), xr - x - 16, 1)[0], font=F("medium", 14), fill=col(WHITE, 1)); y += 21
    y += 6
    leg = [("gate", "Alignment Evaluation Gate (south)"), ("council", "Steward Council, 3 empty seats (north)"), ("agent-avatar", "agent and Omega avatars")]
    for k, s in leg:
        d.rectangle([x, y + 4, x + 9, y + 13], fill=MASS[k] + (255,)); d.text((x + 16, y), s, font=F("regular", 12), fill=col(MUTED, 1)); y += 18
    d.text((x, 420), f"source: worldforge/out/{slug}/blockout.generated.json", font=F("regular", 10), fill=col(MUTED, 1))
    return img.convert("RGB")


def png_bytes(img):
    import io
    b = io.BytesIO(); img.save(b, "PNG", optimize=False); return b.getvalue()


def jpg_bytes(img, q=86):
    import io
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=q); return b.getvalue()


# ------------------------------------------------------------------------------------------------ media plan
def media_plan(D):
    """name -> ('gen', bytes-producer) | ('copy', src) | ('frame', clip, seconds). Determined by D alone."""
    m = {"review-poster.jpg": ("gen", lambda: jpg_bytes(card_title(D, 4.0, 8)))}
    for f in D["featured"]:
        m[f"plan-{f['slug']}.png"] = ("gen", (lambda s: (lambda: png_bytes(plan_image(s, D))))(f["slug"]))
    used = {src for src, _ in pick_images(D)["worlds"]}
    for s in D["stills"][:6]:   # only stills the page shows (the film reads stills from worldforge/out/stills directly)
        if "media/still-" + os.path.basename(s) in used:
            m["still-" + os.path.basename(s)] = ("copy", s)
    for c in D["clips"]:
        m[f"frame-{c['slug']}-{c['mode']}.jpg"] = ("frame", c["file"], c["seconds"] * 0.6)
    return m


def pick_images(D):
    """Which media each slide shows: real renders first, plan views when nothing was rendered."""
    clips = {(c["slug"], c["mode"]): f"media/frame-{c['slug']}-{c['mode']}.jpg" for c in D["clips"]}
    worlds = []
    for f in D["featured"]:
        src = clips.get((f["slug"], "orbit")) or clips.get((f["slug"], "flyin"))
        st = next((s for s in D["stills"][:6] if still_slug(D, s) == f["slug"]), None)
        if src:
            worlds.append((src, f"{f['name']} · orbit, recorded in the WorldForge viewer"))
        elif st:
            worlds.append(("media/still-" + os.path.basename(st), f"{f['name']} · still, worldforge/out/stills/{os.path.basename(st)}"))
        else:
            worlds.append((f"media/plan-{f['slug']}.png", f"{f['name']} · plan view drawn from the generated blockout"))
    b = next(((clips[(f["slug"], "building")], f) for f in D["featured"] if (f["slug"], "building") in clips), None)
    o = next(((clips[(f["slug"], "omega")], f) for f in D["featured"] if (f["slug"], "omega") in clips), None)
    return {
        "worlds": worlds,
        "building": (b[0], f"{b[1]['name']} · {b[1]['building']['zone'] if b[1]['building'] else 'building'}, door to interior") if b else None,
        "omega": (o[0], f"{o[1]['name']} · Omega Steward avatar beside the council (defined, not seated)") if o else None,
    }


# ------------------------------------------------------------------------------------------------ whitepaper
def e(s):
    return html.escape(str(s), quote=True)


def svg_plan(slug):
    bo = R(f"worldforge/out/{slug}/blockout.generated.json")
    ext = bo["coordinateFrame"]["extentXZ"][1]
    parts = [f'<svg viewBox="{-ext} {-ext} {2 * ext} {2 * ext}" role="img" aria-label="plan view">',
             f'<rect class="g" x="{-ext}" y="{-ext}" width="{2 * ext}" height="{2 * ext}" rx="10"/>']
    for r in bo["roads"]:
        (x0, z0), (x1, z1) = r["startXZ"], r["endXZ"]
        parts.append(f'<line class="r" x1="{x0:g}" y1="{z0:g}" x2="{x1:g}" y2="{z1:g}" stroke-width="{r["widthMeters"]:g}"/>')
    for p in bo["primitives"]:
        x, _, z = p["position"]; w, _, dd = p["dimensions"]; k = p["massingType"]
        if k == "agent-avatar":
            parts.append(f'<circle class="a" cx="{x:g}" cy="{z:g}" r="3.4"/>')
        elif k == "plaza":
            parts.append(f'<circle class="p" cx="{x:g}" cy="{z:g}" r="{w / 2:g}"/>')
        elif k in ("zone-pad", "zone-hall", "council", "gate", "seat"):
            parts.append(f'<rect class="{ {"zone-pad": "zp", "zone-hall": "zh", "council": "c", "gate": "gt", "seat": "s"}[k] }" x="{x - w / 2:g}" y="{z - dd / 2:g}" width="{w:g}" height="{dd:g}"/>')
    parts.append("</svg>")
    return "".join(parts)


def perm_table(D):
    rep = D["rep"]
    kinds = [k for k in ("world", "zone", "agent", "council") if rep.get(k)]
    rights = list(rep["world"]["permissions"].keys())
    head = "".join(f"<th>{e(k)}</th>" for k in kinds)
    rows = []
    for r in rights:
        cells = []
        for k in kinds:
            v = rep[k]["permissions"].get(r, [])
            cls = "held" if "steward-quorum" in v else ("agent" if any(x.startswith("agents") for x in v) else "")
            cells.append(f'<td class="{cls}">{e(", ".join(v))}</td>')
        rows.append(f"<tr><th>{e(r)}</th>{''.join(cells)}</tr>")
    return f'<table class="perm"><thead><tr><th>right</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'


def stat(num, label, sub="", tone=""):
    return f'<div class="stat {tone}"><div class="n">{e(num)}</div><div class="l">{e(label)}</div>' + (f'<div class="s">{e(sub)}</div>' if sub else "") + "</div>"


def fig(src, cap):
    return f'<figure><img src="{e(src)}" alt="{e(cap)}" loading="lazy" width="960" height="540"><figcaption>{e(cap)}</figcaption></figure>'


def ul(items, cls=""):
    if not items:
        return '<p class="muted">none listed</p>'
    return f'<ul class="{cls}">' + "".join(f"<li>{e(x)}</li>" for x in items) + "</ul>"


def slide(sid, eyebrow, title, body, src=""):
    s = f'<p class="src">source: {src}</p>' if src else ""
    return f'<section class="slide" id="{sid}"><div class="frame"><p class="eyebrow">{e(eyebrow)}</p><h2>{title}</h2>{body}{s}</div></section>'


CSS = """
:root{--bg:#070a18;--bg2:#0f0e2a;--panel:#12142c;--line:#272b52;--text:#eef1fb;--muted:#9aa6c4;--cyan:#00e6e6;--purple:#8c50ff;--gold:#ffbe28;--green:#28e696;--pink:#ff468c;--held:#ffbe28;--agent:#28e696;--plan-g:#1a221e;--plan-r:#4e5058;--plan-p:#c7ccd6;--plan-zp:#5d8fa8;--plan-zh:#9eabb8;--plan-c:#8c6bbf;--plan-gt:#f2bf40;--plan-a:#33cc99;color-scheme:dark}
:root[data-theme="light"]{--bg:#f6f7fb;--bg2:#eceefa;--panel:#ffffff;--line:#d7dbea;--text:#111428;--muted:#56607a;--cyan:#007f86;--purple:#5b2fd0;--gold:#9a6500;--green:#0b7d4f;--pink:#b8235d;--held:#9a6500;--agent:#0b7d4f;--plan-g:#e3e9e4;--plan-r:#a5a7ad;--plan-p:#ffffff;--plan-zp:#7fb0c8;--plan-zh:#7d8a98;--plan-c:#8c6bbf;--plan-gt:#d49a10;--plan-a:#14946b;color-scheme:light}
@media (prefers-color-scheme: dark){:root:not([data-theme="light"]){color-scheme:dark}}
:root[data-theme="dark"]{color-scheme:dark}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;background:var(--bg);color:var(--text);font:clamp(16px,1.25vw,19px)/1.5 "Avenir Next",Avenir,system-ui,-apple-system,"Segoe UI",sans-serif;overflow-x:hidden}
a{color:var(--cyan)}
header.top{position:sticky;top:0;z-index:5;display:flex;gap:8px;align-items:center;padding:8px 16px;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
header.top nav{flex:1 1 auto;min-width:0;display:flex;gap:4px;align-items:center;overflow-x:auto;white-space:nowrap;scrollbar-width:none}
header.top nav::-webkit-scrollbar{display:none}
nav a{color:var(--muted);text-decoration:none;font-size:13px;padding:4px 8px;border-radius:6px}
nav a:hover{color:var(--text);background:var(--panel)}
nav .brand{color:var(--text);font-weight:700;margin-right:8px}
header.top button{flex:0 0 auto;font:inherit;font-size:13px;color:var(--text);background:var(--panel);border:1px solid var(--line);border-radius:6px;padding:4px 10px;cursor:pointer}
.slide{padding:clamp(28px,5vw,72px) 16px;border-bottom:1px solid var(--line);background:linear-gradient(180deg,var(--bg),var(--bg2))}
.frame{width:min(1200px,100%);margin:0 auto}
@media (min-width:900px){.frame{aspect-ratio:16/9;display:flex;flex-direction:column;justify-content:center}}
.eyebrow{margin:0 0 10px;color:var(--cyan);font-size:13px;font-weight:600;letter-spacing:.2em;text-transform:uppercase}
h1{font-size:clamp(44px,8vw,112px);line-height:1;margin:0 0 18px;letter-spacing:-.02em}
h2{font-size:clamp(30px,4.2vw,58px);line-height:1.08;margin:0 0 22px;letter-spacing:-.01em}
h3{font-size:clamp(18px,1.6vw,22px);margin:0 0 8px}
.lede{font-size:clamp(19px,2vw,28px);color:var(--text);max-width:52ch;margin:0 0 20px}
.muted{color:var(--muted)}
.src{margin:18px 0 0;color:var(--muted);font-size:12px;word-break:break-word}
.grid{display:grid;gap:16px}
.grid>*{min-width:0}
.bar{display:grid;grid-template-columns:72px 1fr 36px;align-items:center;gap:8px;font-size:14px;margin:6px 0}
.bar i{display:block;height:10px;border-radius:5px;background:var(--gold)}
.bar b{text-align:right;font-variant-numeric:tabular-nums}
.g2{grid-template-columns:repeat(auto-fit,minmax(min(100%,420px),1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr))}
.stats{display:grid;gap:12px;grid-template-columns:repeat(auto-fit,minmax(min(100%,170px),1fr));margin:0 0 18px}
.stat{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:14px 16px}
.stat .n{font-size:clamp(28px,3.4vw,46px);font-weight:700;line-height:1.05;color:var(--cyan);font-variant-numeric:tabular-nums}
.stat.gold .n{color:var(--gold)}.stat.green .n{color:var(--green)}.stat.purple .n{color:var(--purple)}.stat.pink .n{color:var(--pink)}
.stat .l{font-weight:600;margin-top:4px}
.stat .s{color:var(--muted);font-size:13px;margin-top:2px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px}
.card p{margin:0 0 8px}
ul{margin:0;padding-left:1.2em}
li{margin:0 0 6px}
figure{margin:0}
figure img,video{display:block;width:100%;height:auto;border-radius:12px;border:1px solid var(--line);background:#000}
figcaption{color:var(--muted);font-size:13px;margin-top:6px}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{text-align:left;border-top:1px solid var(--line);padding:6px 8px;vertical-align:top}
thead th{color:var(--muted);font-weight:600;border-top:0}
td.held{color:var(--held)}td.agent{color:var(--agent)}
.tablewrap{overflow-x:auto}
code,pre{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:13px}
pre{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:12px 14px;overflow-x:auto;margin:0;white-space:pre-wrap;word-break:break-word}
.pill{display:inline-block;border:1px solid currentColor;border-radius:999px;padding:1px 10px;font-size:12px;font-weight:600}
.done{color:var(--green)}.open{color:var(--gold)}.prepared{color:var(--cyan)}.failed{color:var(--pink)}
.worlds{display:grid;gap:10px;grid-template-columns:repeat(auto-fill,minmax(112px,1fr))}
.world{background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:8px;font-size:12px;line-height:1.25}
.world svg{display:block;width:100%;height:auto;margin-bottom:6px}
.world .mk{display:inline-block;min-width:22px;padding:0 4px;border-radius:5px;color:#0a0c18;font-weight:700;font-size:11px;text-align:center;margin-right:4px}
svg .g{fill:var(--plan-g)}svg .r{stroke:var(--plan-r);stroke-linecap:round}svg .p{fill:var(--plan-p)}svg .zp{fill:var(--plan-zp);opacity:.75}svg .zh{fill:var(--plan-zh)}svg .c{fill:var(--plan-c)}svg .gt{fill:var(--plan-gt)}svg .s{fill:var(--plan-c)}svg .a{fill:var(--plan-a)}
.banner{border:1px solid var(--gold);color:var(--gold);border-radius:10px;padding:8px 12px;margin:0 0 16px;font-weight:600}
.cta{display:flex;flex-wrap:wrap;gap:10px;margin-top:8px}
.cta a{display:inline-block;padding:10px 16px;border-radius:10px;border:1px solid var(--cyan);text-decoration:none;font-weight:600}
.cta a.primary{background:var(--cyan);color:var(--bg)}
blockquote{margin:0;padding:10px 14px;border-left:3px solid var(--purple);background:var(--panel);border-radius:0 10px 10px 0}
footer{padding:24px 16px 40px;color:var(--muted);font-size:13px;text-align:center}
"""

JS = """
(function(){var r=document.documentElement,b=document.getElementById('theme');
function set(t){r.setAttribute('data-theme',t);b.textContent=t==='dark'?'Light':'Dark';try{localStorage.setItem('wf-theme',t)}catch(e){}}
var s=null;try{s=localStorage.getItem('wf-theme')}catch(e){}
set(s==='light'?'light':'dark');b.addEventListener('click',function(){set(r.getAttribute('data-theme')==='dark'?'light':'dark')});})();
"""


def build_html(D, film_seconds=None, film=None):
    """film: build.json's film record; when its plan_sha differs from this page's plan the Review slide says so."""
    rd, t, b, ht = D["round"], D["totals"], D["buildings"], D["hive"]["totals"]
    sp = D["spaces"].get("totals") or {}
    imgs = pick_images(D)
    av = D["avatars_index"]
    broken_ok = sum(1 for x in D["broken"] if x.get("ok"))
    beat = D["beat"]
    og = open_gates(D)
    narr = D["narration"] or "silent"
    S = []

    banner = '<p class="banner">Placeholder round file: the lead has not filled worldforge/review/round.json yet (fields read "TODO by lead").</p>' if rd["placeholder"] else ""
    S.append(f'''<section class="slide" id="cover"><div class="frame">{banner}<div class="grid g2" style="align-items:center"><div><p class="eyebrow">AGI Future Foundation PBC · SmartCiti.X virtual worlds</p>
<h1>WorldForge</h1><p class="lede">GLEWME Master Cards for {t["worlds"]} coming-soon worlds: every object knows who owns it, the region it covers and who may change it. Agents operate; people govern.</p>
<p class="muted">Review {e(rd["n"])} · {e(rd["window"])} · {e(rd["date"])} · Powered by AGI Corp</p>
<div class="cta"><a class="primary" href="#review">Watch the 2-minute review</a><a href="mailto:{EMAIL}">Contact</a></div></div>
<div>{fig(*imgs["worlds"][0])}<div class="stats" style="margin-top:12px">{stat(t["worlds"], "worlds")}{stat(t["cards"], "cards", "", "purple")}{stat(t["evals"], "evals", f"{t['failed']} failing", "green")}</div></div></div></div></section>''')

    S.append(slide("problem", "The problem", "A spec is not a scene", f'''<div class="grid g3">
<div class="card"><h3>Worlds exist on paper</h3><p>{t["worlds"]} worlds are specified, with zones, agents and citations in <code>my-fabric/worlds/index.json</code>. A host engine cannot load a specification.</p></div>
<div class="card"><h3>Objects need owners</h3><p>In a shared world every object needs an owner, a bounded region and a permission matrix that a native loader can read without trusting display names.</p></div>
<div class="card"><h3>Agents must not hold power</h3><p>Agents will run these worlds. Final votes, the charter, the treasury, enactment, windfall and appointments must be rights no agent can ever hold.</p></div></div>''',
        "my-fabric/worlds/index.json, worldforge/README.md"))

    kinds = D["kinds"]   # every kind in the cards, in kind_rank order; load() fails the build unless they sum to totals.cards
    kind_list = ", ".join(f"{n} {k}" for k, n in kinds.items())
    z = D["rep"]["zone"]
    sample = {k: z[k] for k in ("cardId", "kind", "parentCardId", "owner", "volum")} if z else {}
    S.append(slide("built", "What we built", "GLEWME Master Cards, Volum and permissions", f'''<div class="grid g2"><div>
<p class="lede" style="font-size:clamp(17px,1.6vw,22px)">{t["cards"]} cards across {t["worlds"]} worlds: {e(kind_list)}.</p>
<p>Each card carries an <strong>owner</strong> ({e(D["rep"]["world"]["owner"])}), a <strong>Volum</strong> (a box: centre and half-extents in metres, Y up) and a permission matrix over <code>{e(", ".join(D["rep"]["world"]["permissions"].keys()))}</code>. Every node in each world's GLB carries its <code>cardId</code> in extras, so a loader indexes cards without display names.</p>
<pre>{e(json.dumps(sample, indent=1, ensure_ascii=False))}</pre></div>
<div class="tablewrap"><h3>Permission matrix ({e(D["names"][D["first"]])})</h3>{perm_table(D)}<p class="muted" style="font-size:13px">Gold: held for the steward quorum. Green: agents may operate their own zone.</p></div></div>''',
        f"worldforge/out/index.json, worldforge/out/{D['first']}/cards.json"))

    figs = "".join(fig(s, c) for s, c in imgs["worlds"])
    tiles = "".join(f'<div class="world">{svg_plan(w["slug"])}<span class="mk" style="background:hsl({D["brands"].get(w["slug"], {}).get("hue", 180)} 70% 60%)">{e(D["brands"].get(w["slug"], {}).get("mark", ""))}</span>{e(w["name"])}</div>' for w in D["worlds"])
    S.append(slide("worlds", "The worlds", f"{t['worlds']} worlds, one card tree each", f'''<div class="grid g3" style="margin-bottom:16px">{figs}</div>
<p class="muted">Plan views below are drawn from each world's generated blockout: plaza at the centre, the Alignment Evaluation Gate south, the Steward Council north, zones on a ring. Geometry is generated; no coordinates or models were imported.</p>
<div class="worlds">{tiles}</div>''', "worldforge/out/&lt;slug&gt;/blockout.generated.json, worlds/generated/teams/&lt;slug&gt;.json (brand)"))

    shared = (D["spaces"].get("shared") or [])
    rows = "".join(f'<tr><td><code>{e(s["model"])}</code></td><td>{e(s["kind"])}</td><td>{e(s["role"])}</td><td>{s["triangles"]:,}</td><td>{e(", ".join(sorted({str(x["w"]) for x in s.get("textures", [])})))} px · {len(s.get("textures", []))} maps</td></tr>' for s in shared)
    bk = b["kinds"]; top = max(bk.values()) if bk else 1
    bars = "".join(f'<div class="bar"><span>{e(k)}</span><i style="width:{100 * v / top:.1f}%"></i><b>{v}</b></div>' for k, v in bk.items())
    bfig = fig(*imgs["building"]) if imgs["building"] else f'<div class="card"><h3>Building kinds across {b["slots"]} zone and council cards</h3>{bars}<p class="muted" style="font-size:13px;margin-top:8px">No building clip was recorded this round.</p></div>'
    S.append(slide("buildings", "Buildings and interiors", "Enterable buildings with hi-res PBR", f'''<div class="stats">{stat(sp.get("exteriors", "?"), "exteriors")}{stat(sp.get("interiors", "?"), "interiors")}{stat(sp.get("textures", "?"), "textures", f"{sp.get('at_2048', '?')} at 2048 px", "gold")}{stat(f"{b['linked']}/{b['slots']}", "zone and council cards linked", f"{b['on_disk']} with both models on disk", "green")}{stat(f"{sp.get('mb', '?')} MB", "shared + room bytes", "", "purple")}</div>
<div class="grid g2"><div>{bfig}</div><div><p class="muted">{e(D["spaces"].get("about", ""))}</p><div class="tablewrap"><table><thead><tr><th>hero model</th><th>kind</th><th>role</th><th>triangles</th><th>textures</th></tr></thead><tbody>{rows}</tbody></table></div></div></div>''',
        "my-fabric/worlds/spaces_index.json, worldforge/out/*/cards.json (building)"))

    ak, bk_, kc = D["avatar_kind"], D["bound_kind"], D["kinds"]
    ex = D["rep"]["agent"]
    exb = ex.get("binding", {}) if ex else {}
    gv = D["glb_validation"]
    models_line = (f"{len(D['models_present'])} of {len(D['model_refs'])} referenced avatar models are on disk ({', '.join(os.path.basename(m) for m in D['models_present'])})." if D["models_present"]
                   else f"None of the {len(D['model_refs'])} referenced avatar models ({', '.join(os.path.basename(m) for m in D['model_refs'])}) is on disk yet; the cards reference them by role.")
    if gv:
        tri = ((D["avatar_assets"] or {}).get("totals") or {}).get("triangles")
        models_line += (f" The Khronos validator ({gv['validator']}) reports {gv['errors']} errors and {gv['warnings']} warnings on the "
                        f"{gv['validated']} of {gv['glbs']} GLBs whose sha256 still matches the validated file" + (f"; {tri:,} triangles in all." if tri else "."))
    # the title claims only what the counts show: every card of each bound kind carries both an avatar and a binding
    full = bool(bk_) and all(bk_[k] == kc.get(k) and ak.get(k) == kc.get(k) for k in bk_)
    title = (f"Every {and_list(bk_)} card has an avatar and a binding" if full
             else f"Avatars on {D['with_avatar']} cards, {D['bound']} bound to a swarm")
    unbound = [k for k in ak if k not in bk_]
    why = {k: D["kind_note"].get(k) or ("defined, not seated" if k == "omega" else "") for k in unbound}
    lede = ""
    if unbound:
        lede = f"{and_list(unbound).capitalize()} cards carry an avatar but no swarm binding"
        if any(why.values()):
            lede += " (" + "; ".join(f"{k}: {why[k]}" for k in unbound if why[k]) + ")"
        lede += "."
    krows = "".join(f'<tr><td>{e(k)}</td><td>{kc.get(k, 0)}</td><td>{n}</td><td>{bk_.get(k, 0)}</td><td>{e(", ".join(f"{v} {r}" for r, v in D["avatar_kind_roles"].get(k, {}).items()))}</td></tr>' for k, n in ak.items())
    parts = [(av[k], k) for k in ("specialists", "coordinators", "advisors", "omegas") if isinstance(av.get(k), int)]
    other = (av.get("avatars") or 0) - sum(n for n, _ in parts)
    reg_sub = ", ".join(f"{n} {k}" for n, k in parts) + (f", {other} other" if other else "")
    avs = (stat(av["avatars"], "avatars in the avatar registry", reg_sub, "pink") +
           stat(av.get("evals", "?"), "avatar evals", f"{av.get('failing', '?')} failing", "green")) if av.get("avatars") is not None else ""
    gstat = stat(f"{len(D['models_present'])}/{len(D['model_refs'])}", "avatar models on disk", f"{gv['validated']} validated, {gv['errors']} errors, {gv['warnings']} warnings" if gv else "", "gold")
    ofig = fig(*imgs["omega"]) if imgs["omega"] else ""
    S.append(slide("avatars", "Avatars connected to agents", e(title), f'''<div class="stats">{stat(D["with_avatar"], "cards carry an avatar", f"across {plural(len(ak), 'card kind')}", "purple")}{stat(D["bound"], "bound to swarm, metaprompt and fabric node", and_list(f"{n} {k}" for k, n in bk_.items()), "green")}{gstat}{avs}</div>
{f'<p class="muted">{e(lede)}</p>' if lede else ""}
<div class="grid {"g2" if ofig else ""}"><div><div class="tablewrap"><table><thead><tr><th>card kind</th><th>cards</th><th>with avatar</th><th>bound</th><th>avatar roles</th></tr></thead><tbody>{krows}</tbody></table></div>
<div class="card" style="margin-top:12px"><h3>Example binding: {e(ex["name"]) if ex else ""}</h3><p class="muted">{e(ex.get("role", "")) if ex else ""}</p>
<pre>{e(json.dumps(exb, indent=1, ensure_ascii=False))}</pre><p class="muted" style="margin-top:8px">{e(models_line)}</p></div></div><div>{ofig}</div></div>''',
        "worldforge/out/*/cards.json (avatar, binding on every card kind)" + (", worldforge/out/avatars/index.json" if av else "")
        + (", worldforge/out/assets/avatars/index.json and validation.json" if gv else "")))

    om = D["featured"][0]["omega"]
    eng = D["hive"]["engine"]
    persona = ""
    if om:
        p = om["persona"]
        persona = f'''<div class="card"><h3>{e(om["name"])} <span class="pill open">{e(om["status"])}</span></h3>
<p><strong>Temperament:</strong> {e(p.get("temperament", ""))}</p><p><strong>Style:</strong> {e(p.get("style", ""))}</p>
<p><strong>Values:</strong> {e("; ".join(p.get("values", [])))}</p><p><strong>Refuses:</strong> <code>{e(", ".join(p.get("refuses", [])))}</code></p>
<blockquote>{e(om["greet"])}</blockquote><p class="muted" style="margin-top:6px">Voice: Kokoro <code>{e(om.get("kokoro") or "")}</code>; the line says it is synthetic.</p></div>'''
    spoken_note = " when this page was built"   # pinned in build.json; the live count is never printed, so voicing does not stale the page
    S.append(slide("hive", "Omega Hive", "One persona and one synthetic voice per Omega Steward", f'''<div class="stats">{stat(ht.get("omegas", "?"), "Omega Stewards", "defined, not seated")}{stat(ht.get("voices", "?"), "synthetic voices", eng.get("name", ""), "purple")}{stat(ht.get("lines", "?"), "scripted lines", "4 per Omega", "gold")}{stat(f"{ht.get('spoken', '?')} of {ht.get('lines', '?')}", "lines voiced", spoken_note.strip(), "green")}</div>
<div class="grid g2">{persona}<div class="card"><p>{e(D["hive"]["note"])}</p><p class="muted">Engine: {e(eng.get("name", ""))}, licence {e(eng.get("license", ""))}, synthetic: {e(str(eng.get("synthetic", "")).lower())}.</p></div></div>''',
        "agents/hive/index.json (totals, voice_engine), worldforge/out/*/cards.json (omega)"))

    S.append(slide("governance", "Governance", "Agents operate; people govern", f'''<div class="grid g2"><div>
<p class="lede" style="font-size:clamp(17px,1.6vw,22px)">Six actions are held for a 2-of-3 Steward Council, on every card in every world. No agent card holds any of them, and an eval fails the build if one does.</p>
<ul>{"".join(f"<li><code>{e(a)}</code></li>" for a in D["reserved"])}</ul></div>
<div><div class="stats">{stat(D["seats"], "human steward seats", f"{D['seats_empty']} empty", "gold")}{stat(D["omega_dns"], "Omega Stewards", "defined, not seated")}{stat("2 of 3", "signed votes decide", "", "green")}</div>
<p class="muted">Agents may view, enter and operate their own zone, and nothing else. <code>delegate</code> belongs to stewards; <code>transfer</code> and <code>govern</code> belong to the steward quorum.</p></div></div>''',
        "worldforge/out/*/cards.json (reserved_for_humans, permissions, seat), worlds/PBC.json via worldforge/build.mjs"))

    segs = beat["segments"] if beat else {}
    picks = [k for k in ("GLB", "REFS", "SWARMS", "PROMPTS", "DEEP", "ADVISORY", "PUBLISH") if k in segs]
    beat_html = (f'<p><span class="pill {"done" if beat["status"] == "GREEN" else "failed"}">{e(beat["status"])}</span> last beat at {e(beat["time"])}</p><ul>' +
                 "".join(f"<li><strong>{e(k)}</strong>: {e(segs[k])}</li>" for k in picks) + "</ul>") if beat else '<p class="muted">No heartbeat beat line in evidence/heartbeat.log.</p>'
    film_line = f"{film_seconds:.1f} s" if film_seconds else "not built"
    # the film and its captions are cut once per round; the page can be rebuilt after it (--no-film, registry moves)
    trail = ""
    if film and film.get("plan_sha") and film["plan_sha"] != plan_sha(D):
        trail = (f'<p class="banner" style="font-size:13px;margin-top:8px">This film was cut for round {e(film.get("round"))} before the '
                 f'registries last moved; its on-screen numbers and narration can trail this page, which was rebuilt after it.</p>')
    notdone = [
        "Not mounted in Sneeze: " + ", ".join(og) + "." if og else "All WorldForge gates are done.",
        f"Omega Stewards are defined, not seated; {D['seats_empty']} of {D['seats']} human seats are empty.",
        f"{ht.get('spoken', '?')} of {ht.get('lines', '?')} Omega lines voiced; every voice is synthetic.",
        ("Avatar models referenced by the cards are not on disk yet." if not D["models_present"] else f"{len(D['models_present'])} of {len(D['model_refs'])} avatar models on disk."),
        {"clips": "3D clips are software-WebGL renders of generated geometry.", "stills": "No 3D clips were recorded this round (stills only).", "plans": "No 3D clips or stills were recorded this round (plan views only)."}[D["three_d"]],
    ]
    S.append(slide("evidence", "Evidence", "Checked, not asserted", f'''<div class="stats">{stat(t["evals"], "WorldForge evals", f"{t['failed']} failing", "green")}{stat(f"{broken_ok}/{len(D['broken'])}", "broken worlds caught", "each fails only its own check", "gold")}{stat(av.get("evals", "?") if av else "?", "avatar evals", f"{av.get('failing', '?')} failing" if av else "registry not built", "purple")}{stat(film_line, "review film", "narrated: " + (narr.split(":", 1)[1] + " (synthetic)" if narr.startswith("say:") else "no, captions only"), "pink")}</div>
<div class="grid g2"><div class="card"><h3>Heartbeat</h3>{beat_html}</div><div class="card"><h3>What is not done</h3>{ul(notdone)}</div></div>''',
        "worldforge/out/index.json (totals, broken), evidence/heartbeat.log (beat pinned at build), worldforge/review/out/build.json"))

    grows = "".join(f'<tr><td>{e(k)}</td><td><span class="pill {("done" if str(v).startswith("done") else "prepared" if str(v).startswith("prepared") else "failed" if str(v).startswith("fail") else "open")}">{e(str(v).split(":")[0])}</span> <span class="muted">{e(str(v).split(":", 1)[1].strip()) if ":" in str(v) else ""}</span></td></tr>' for k, v in D["gates"].items())
    frows = "".join(f'<tr><td>{e(p["name"])}</td><td><span class="pill {"open" if p["status"] != "now" else "prepared"}">{e(p["status"])}</span></td><td class="muted">{e(p["gate"])}</td></tr>' for p in D["founder"])
    S.append(slide("roadmap", "Roadmap gates", "Each gate is a named decision", f'''<div class="grid g2"><div class="tablewrap"><h3>WorldForge</h3><table><tbody>{grows}</tbody></table></div>
<div class="tablewrap"><h3>Founder and board gates</h3><table><tbody>{frows}</tbody></table></div></div>''', f"{D['gates_src']} (gates), atlas/roadmap.json (phases not done)"))

    S.append(slide("review", f"Review {rd['n']} · {rd['window']}", e(rd["headline"]), f'''<div class="grid g2"><div><video src="review-film.mp4" controls preload="metadata" poster="media/review-poster.jpg" width="960" height="540"><track kind="captions" src="review.vtt" srclang="en" label="English" default></video>
<p class="muted" style="font-size:13px;margin-top:6px">2-minute review film, {e(film_line)} · {"narrated by a synthetic macOS system voice" if narr.startswith("say:") else "silent with captions"} · 3D: {e(D["three_d"])}</p>{trail}</div>
<div class="grid" style="gap:12px"><div class="card"><h3>Landed</h3>{ul(rd["landed"])}</div><div class="card"><h3>Doing</h3>{ul(rd["doing"])}</div></div></div>
<div class="grid g2" style="margin-top:12px"><div class="card"><h3>Next</h3>{ul(rd["next"])}</div><div class="card"><h3>Gates this round</h3>{ul([gate_text(g) for g in rd["gates"]])}</div></div>''',
        f"worldforge/review/round.json (round {e(rd['n'])}, {e(rd['date'])})"))

    asks = [f"WorldForge {g}" for g in og] + [f"{p['name']}: {p['gate']}" for p in D["founder"][:3]]
    S.append(slide("ask", "The ask", "Decisions, not features", f'''<div class="grid g2"><div><p class="lede" style="font-size:clamp(17px,1.6vw,22px)">The build runs and checks itself. What moves it forward now are decisions only people can make:</p>{ul(asks)}</div>
<div class="card"><h3>Contact</h3><p><a href="mailto:{EMAIL}">{EMAIL}</a></p><p class="muted">AGI Future Foundation PBC · Powered by AGI Corp</p><p class="muted" style="font-size:13px">{e(DISCLAIMER)}</p></div></div>''',
        f"{D['gates_src']}, atlas/roadmap.json"))

    nav = "".join(f'<a href="#{i}">{e(n)}</a>' for i, n in (("problem", "Problem"), ("built", "Cards"), ("worlds", "Worlds"), ("buildings", "Buildings"), ("avatars", "Avatars"), ("hive", "Hive"), ("governance", "Governance"), ("evidence", "Evidence"), ("roadmap", "Gates"), ("review", f"Review {rd['n']}"), ("ask", "Ask")))
    page = f'''<!doctype html>
<html lang="en" data-theme="dark">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>WorldForge Whitepaper</title>
<meta name="description" content="WorldForge review {e(rd["n"])}: GLEWME Master Cards, buildings, avatars and the Omega Hive for {t["worlds"]} SmartCiti.X worlds. Powered by AGI Corp.">
<style>{CSS}</style>
</head>
<body>
<header class="top"><nav aria-label="Slides"><a class="brand" href="#cover">WorldForge</a>{nav}</nav><button id="theme" type="button">Light</button></header>
<main>
{chr(10).join(S)}
</main>
<footer>Powered by AGI Corp · AGI Future Foundation PBC · built by worldforge/review/build_review.py from the registry files named on each slide; every number is read at build time.</footer>
<script>{JS}</script>
</body>
</html>
'''
    honesty_scan(page, "whitepaper.html")
    return page


def honesty_scan(text, where):
    low = text.lower()
    for f in FORBIDDEN:
        if f in low:
            die(f"{where} would contain the private repository name; fix the source that carries it")
    for m in re.findall(r"[\w.+-]+@[\w-]+\.[\w.]+", text):
        if m != EMAIL:
            die(f"{where} would contain an email address other than {EMAIL}: {m}")
    if re.search(r"\b0x[0-9a-fA-F]{40}\b", text):
        die(f"{where} would contain a wallet-like address")
    if re.search(r"\b(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16})\b", text):
        die(f"{where} would contain a key-like string")


# ------------------------------------------------------------------------------------------------ ffmpeg helpers
def ff(args, **kw):
    return subprocess.run([FFMPEG, "-hide_banner", "-loglevel", "error", "-y"] + args, check=True, **kw)


def duration(path):
    err = subprocess.run([FFMPEG, "-hide_banner", "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):([\d.]+)", err)
    return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else None


def pipe_frames(path, nframes, frame_at, dup=1):
    """Render frames with frame_at(i) -> PIL image and encode them. dup=2 renders every other frame (12 fps states)."""
    p = subprocess.Popen([FFMPEG, "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                          "-r", str(FPS), "-i", "-", "-vf", TAIL, "-frames:v", str(nframes)] + X264 + [path], stdin=subprocess.PIPE)
    last = None
    for i in range(nframes):
        if i % dup == 0 or last is None:
            last = frame_at(i).convert("RGB").tobytes()
        p.stdin.write(last)
    p.stdin.close()
    if p.wait() != 0:
        die(f"ffmpeg failed encoding {os.path.basename(path)}")


def clip_warnings(D):
    """Clips not in the limited-range BT.709 yuv420p that record.mjs now writes (the film re-encodes them either way)."""
    old = []
    for c in D["clips"]:
        err = subprocess.run([FFMPEG, "-hide_banner", "-i", os.path.join(ROOT, c["file"])], capture_output=True, text=True).stderr
        m = re.search(r"Video: [^\n]*?\b(yuvj?\d+p\w*)(?:\((\w+))?", err)
        if m and (m.group(1), m.group(2)) != ("yuv420p", "tv"):
            old.append(f"{os.path.basename(c['file'])} {m.group(1)}({m.group(2) or '?'})")
    return [f"{len(old)} of {len(D['clips'])} clips are not yuv420p(tv, bt709) (e.g. {old[0]}): re-run node worldforge/review/record.mjs"] if old else []


def say_available():
    if sys.platform != "darwin" or not shutil.which("say"):
        return None
    tmp = tempfile.mkdtemp(prefix="wf-say-")
    try:
        out = os.path.join(tmp, "probe.aiff")
        voices = subprocess.run(["say", "-v", "?"], capture_output=True, text=True).stdout
        voice = VOICE if re.search(rf"^{VOICE}\s", voices, re.M) else None
        subprocess.run(["say"] + (["-v", voice] if voice else []) + ["-o", out, "probe"], capture_output=True, timeout=60)
        d = duration(out) if os.path.exists(out) else None
        return (voice or "default") if d and d > 0.1 else None
    except Exception:
        return None
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def synth(text, path, voice):
    subprocess.run(["say"] + (["-v", voice] if voice != "default" else []) + ["-r", "180", "-o", path, text], check=True, capture_output=True, timeout=120)
    return duration(path) or 0.0


# ------------------------------------------------------------------------------------------------ film
def render_film(D, tmp):
    segs, cues, item_cues, lines = film_plan(D)
    silent = not (D["narration"] or "").startswith("say:")
    files, frame0 = [], 0
    starts = {}
    t_acc = 0
    for name, dur in SECTIONS:
        starts[name] = t_acc; t_acc += dur
    items_n = sum(1 for s in segs if s["section"] == "worlds")
    k = 0
    banners = {"clip": None, "still": "stills — 3D clips not recorded this round",
               "plan": "plan views from the generated blockout — 3D clips not recorded this round"}
    for i, s in enumerate(segs):
        out = os.path.join(tmp, f"seg{i:02d}.mp4")
        if s["kind"] == "card":
            dur = dict(SECTIONS)[s["section"]]
            fn = CARDS[s["section"]]
            def frame_at(j, fn=fn, dur=dur, name=s["section"]):
                img = card_title(D, (j - j % 2) / FPS, dur, silent=silent) if name == "title" else fn(D, (j - j % 2) / FPS, dur)
                if silent:
                    caption_strip(img, lines[name])
                return img
            pipe_frames(out, s["frames"], frame_at, dup=2)
        else:
            k += 1
            lt = lower_third(D, s["slug"], s["title"], s["desc"], k, items_n, banners[s["kind"]])
            lt_path = os.path.join(tmp, f"lt{i:02d}.png"); lt.save(lt_path)
            d = s["frames"] / FPS
            if s["kind"] == "clip":
                src = os.path.join(ROOT, s["src"])
                L = duration(src) or d
                stretch = max(0.5, min(3.0, d / L))
                fc = (f"[0:v]setpts={stretch:.5f}*PTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
                      f"tpad=stop_mode=clone:stop_duration={d:.3f}[c];[c][1:v]overlay=0:0,fade=t=in:st=0:d=0.3,fade=t=out:st={d - 0.3:.3f}:d=0.3,{TAIL}[v]")
                ff(["-i", src, "-loop", "1", "-framerate", str(FPS), "-i", lt_path, "-filter_complex", fc, "-map", "[v]", "-frames:v", str(s["frames"]), "-an"] + X264 + [out])
            else:
                src_img = Image.open(os.path.join(ROOT, s["src"]) if s["kind"] == "still" else os.path.join(OUT, s["src"])).convert("RGB")
                # cover-fit at 1.25x, then a slow deterministic pan + zoom (Ken Burns); every window is downscaled
                scale = max(W / src_img.width, H / src_img.height) * 1.25
                big = src_img.resize((int(src_img.width * scale), int(src_img.height * scale)), Image.LANCZOS)
                n = s["frames"]; dirn = 1 if k % 2 else -1
                m = min(big.width / W, big.height / H)
                def frame_at(j, big=big, n=n, dirn=dirn, lt=lt, m=m):
                    u = j / max(1, n - 1)
                    z = 1.0 + 0.06 * (u if dirn > 0 else 1 - u)
                    cw, ch = W * m / (1.04 * z), H * m / (1.04 * z)   # 96% of the image at z=1, 91% at z=1.06
                    x = (big.width - cw) * (0.5 + 0.3 * dirn * (u - 0.5)); y = (big.height - ch) * (0.5 - 0.2 * (u - 0.5))
                    fr = big.crop((round(x), round(y), round(x + cw), round(y + ch))).resize((W, H), Image.BILINEAR).convert("RGBA")
                    fr.alpha_composite(lt)
                    a = min(1.0, j / 7, (n - 1 - j) / 7)
                    if a < 1:
                        fr = Image.blend(Image.new("RGBA", (W, H), (0, 0, 0, 255)), fr, max(0.0, a))
                    return fr
                pipe_frames(out, n, frame_at, dup=1)
        files.append(out)
    lst = os.path.join(tmp, "list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in files)
    video = os.path.join(tmp, "video.mp4")
    ff(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", video])

    os.makedirs(OUT, exist_ok=True)
    if silent:
        shutil.copyfile(video, FILM)
        return {"narration": "silent", "lines": {}}
    voice = D["narration"].split(":", 1)[1]
    inputs, filters, labels, info = [], [], [], {}
    for j, (name, dur) in enumerate(SECTIONS):
        text = lines[name]
        budget = dur - 1.0
        path = os.path.join(tmp, f"n{j}.aiff")
        d = synth(text, path, voice)
        tries = 0
        while d / 1.25 > budget and tries < 4 and len(text.split()) > 6:
            # too long even sped up: drop the trailing clause and re-synthesise (the captions keep the full line)
            text = re.sub(r"[;,.]?\s*[^;,.]*[;,.]?\s*$", ".", text.rstrip(".")).strip() or text
            d = synth(text, path, voice); tries += 1
        tempo = max(1.0, d / budget) if d > budget else 1.0
        tempo = min(tempo, 1.6)
        inputs += ["-i", path]
        delay = int((starts[name] + 0.5) * 1000)
        filters.append(f"[{j + 1}:a]aresample=48000,aformat=channel_layouts=mono" + (f",atempo={tempo:.3f}" if tempo > 1.0 else "") + f",adelay={delay}:all=1[a{j}]")
        labels.append(f"[a{j}]")
        info[name] = {"text": text, "seconds": round(d / tempo, 2), "tempo": round(tempo, 3)}
    fc = ";".join(filters) + f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0,apad=whole_dur={TOTAL_S},atrim=0:{TOTAL_S}[a]"
    ff(["-i", video] + inputs + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-t", str(TOTAL_S), "-movflags", "+faststart", FILM])
    return {"narration": D["narration"], "lines": info}


# ------------------------------------------------------------------------------------------------ build / check
def write_media(D, check=False):
    """Write (or, in check mode, compare) media. Returns a list of problems in check mode."""
    os.makedirs(MEDIA, exist_ok=True)
    problems = []
    for name, spec in media_plan(D).items():
        dst = os.path.join(MEDIA, name)
        if spec[0] == "gen":
            data = spec[1]()
            if check:
                if not os.path.exists(dst) or open(dst, "rb").read() != data:
                    problems.append(f"media/{name} differs")
            else:
                if not os.path.exists(dst) or open(dst, "rb").read() != data:
                    open(dst, "wb").write(data)
        elif spec[0] == "copy":
            data = open(os.path.join(ROOT, spec[1]), "rb").read()
            if check:
                if not os.path.exists(dst) or open(dst, "rb").read() != data:
                    problems.append(f"media/{name} differs from {spec[1]}")
            else:
                open(dst, "wb").write(data)
        else:  # a frame of a recorded clip: a build artifact like the film, so check only that it exists
            if check:
                if not os.path.exists(dst):
                    problems.append(f"media/{name} missing")
            else:
                ff(["-ss", f"{spec[2]:.2f}", "-i", os.path.join(ROOT, spec[1]), "-frames:v", "1", "-q:v", "3", dst])
    if not check:
        keep = set(media_plan(D))
        for f in os.listdir(MEDIA):
            if f not in keep:
                os.remove(os.path.join(MEDIA, f))
    return problems


def check():
    if not os.path.exists(BUILD):
        print("worldforge review STALE: no worldforge/review/out/build.json; run python3 worldforge/review/build_review.py"); sys.exit(1)
    bj = json.load(open(BUILD))
    pinned = bj.get("pinned", {})
    problems = []
    beats = heartbeat_lines()
    if pinned.get("heartbeat_line") and pinned["heartbeat_line"] not in beats:
        problems.append("the heartbeat beat the page cites is no longer in evidence/heartbeat.log")
    D = load({"heartbeat_line": pinned.get("heartbeat_line"), "hive_spoken": pinned.get("hive_spoken"), "narration": (bj.get("film") or {}).get("narration")})
    now = D["hive"]["totals"].get("spoken_now")
    if isinstance(now, int) and isinstance(pinned.get("hive_spoken"), int) and now < pinned["hive_spoken"]:
        problems.append(f"hive voiced lines fell from {pinned['hive_spoken']} to {now}")
    film = bj.get("film") or {}
    secs = duration(FILM) if os.path.exists(FILM) else None
    page = build_html(D, secs, film)
    if not os.path.exists(PAGE) or open(PAGE).read() != page:
        problems.append("whitepaper.html differs from a rebuild")
    # the captions belong to the film: compared with the cues the film stored, not with today's registries
    if not os.path.exists(VTT) or open(VTT).read() != vtt_text(D, film):
        problems.append("review.vtt differs from the film's captions")
    problems += write_media(D, check=True)
    if secs is None:
        problems.append("review-film.mp4 missing (it is gitignored; rebuild)")
    elif not 118 <= secs <= 122:
        problems.append(f"review-film.mp4 is {secs:.1f} s, not 118-122 s")
    # The film is a build artifact: only its presence, length and round are checked, so registry counts moving between
    # rounds do not stale it (build.json keeps plan_sha for anyone who wants to compare the full plan).
    if film.get("round") != D["round"]["n"]:
        problems.append(f"the film is from round {film.get('round')}, round.json is round {D['round']['n']}")
    if problems:
        print(f"worldforge review STALE (round {D['round']['n']}): " + "; ".join(problems)); sys.exit(1)
    print(f"worldforge review current (round {D['round']['n']}, film {secs:.1f}s)")


def build(no_film=False, silent=False):
    beats = heartbeat_lines()
    hive = opt("agents/hive/index.json") or {}
    prev = json.load(open(BUILD)) if os.path.exists(BUILD) else {}
    narration = None
    if no_film:
        narration = (prev.get("film") or {}).get("narration")
    elif not silent:
        v = say_available()
        narration = f"say:{v}" if v else "silent"
    else:
        narration = "silent"
    pinned = {"heartbeat_line": beats[-1] if beats else None, "hive_spoken": (hive.get("totals") or {}).get("spoken"), "narration": narration}
    D = load(pinned)
    os.makedirs(OUT, exist_ok=True)
    write_media(D)
    film = prev.get("film") if no_film else None
    warn = []
    if not no_film:
        cues = vtt_cues(D)
        honesty_scan(vtt_render(D["round"]["n"], cues), "review.vtt")
        warn = clip_warnings(D)
        tmp = tempfile.mkdtemp(prefix="wf-review-")
        try:
            info = render_film(D, tmp)
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        secs = duration(FILM)
        if secs is None or not 118 <= secs <= 122:
            die(f"review-film.mp4 probed at {secs} s, outside 118-122 s")
        film = {"file": rel(FILM), "round": D["round"]["n"], "seconds": round(secs, 2), "frames": TOTAL_S * FPS, "narration": info["narration"],
                "narration_lines": info["lines"], "three_d": D["three_d"],
                "clips": [c["file"] for c in D["clips"]], "plan_sha": plan_sha(D), "captions": cues}
    secs = duration(FILM) if os.path.exists(FILM) else None
    page = build_html(D, secs, film)
    vtt = vtt_text(D, film)     # --no-film keeps the film's own captions, so they never disagree with its picture
    honesty_scan(vtt, "review.vtt")
    open(PAGE, "w").write(page)
    open(VTT, "w").write(vtt)
    bj = {"schemaVersion": "worldforge-review-build/0.1", "round": D["round"]["n"], "placeholder": D["round"]["placeholder"],
          "film": film, "pinned": {"heartbeat_line": pinned["heartbeat_line"], "hive_spoken": pinned["hive_spoken"]},
          "whitepaper_sha256": hashlib.sha256(page.encode()).hexdigest(), "media": sorted(media_plan(D))}
    json.dump(bj, open(BUILD, "w"), indent=1)
    open(BUILD, "a").write("\n")
    f = film or {}
    print(f"worldforge review built (round {D['round']['n']}): film {f.get('seconds', '?')}s ({f.get('narration', '?')}, 3D: {D['three_d']}), "
          f"whitepaper {len(page) // 1024} KB, {len(media_plan(D))} media, captions {vtt.count(' --> ')} cues"
          + (f" | warning: {'; '.join(warn)}" if warn else ""))


if __name__ == "__main__":
    a = sys.argv[1:]
    if "--check" in a:
        check()
    else:
        build(no_film="--no-film" in a, silent="--silent" in a)

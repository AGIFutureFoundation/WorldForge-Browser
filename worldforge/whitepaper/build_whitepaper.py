#!/usr/bin/env python3
"""SmartCiti.X Agentic Worlds: a whitepaper page and two 120-second films, built from the registries.

    python3 worldforge/whitepaper/build_whitepaper.py            # page + both films + captions + posters + build.json
    python3 worldforge/whitepaper/build_whitepaper.py --no-film  # page, media and build.json only (keeps the films)
    python3 worldforge/whitepaper/build_whitepaper.py --silent   # films without narration even if macOS `say` works
    python3 worldforge/whitepaper/build_whitepaper.py --check    # page current? films present and 118-122 s?

Inputs (read only):
  worldforge/whitepaper/content/market.json        fact-checked external claims (confirmed / corrected only) + narrative
  worldforge/whitepaper/content/explainers-*.json   deep explainers written by the explainer agents
  the registries: worldforge/out/**, agents/**, my-fabric/worlds/*.json, worlds/PBC.json, atlas/roadmap.json,
  evidence/heartbeat.log, rp1/publish/manifest.json, worldforge/native/conformance-report.json
  helpers from worldforge/review/build_review.py (imported, never edited)

Every project number on the page and in the films is read from a registry file when this runs, and the page names that
file. Explainer facts whose source names a JSON pointer are re-read here: a value that has moved since the explainer was
written is shown with the registry's current value beside it, never silently.

Outputs (worldforge/whitepaper/out/): index.html, film-features.mp4, film-roadmap-stack.mp4 (both gitignored),
film-features.vtt, film-roadmap-stack.vtt, media/*, build.json. Writes nothing outside worldforge/whitepaper/ and $TMPDIR.
"""
import datetime, glob, hashlib, html, importlib.util, io, json, os, re, shutil, subprocess, sys, tempfile

from PIL import Image, ImageDraw

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(HERE, "out")
MEDIA = os.path.join(OUT, "media")
CONTENT = os.path.join(HERE, "content")
PAGE = os.path.join(OUT, "index.html")
BUILD = os.path.join(OUT, "build.json")

# the review pipeline's drawing, ffmpeg and narration helpers, loaded read-only from its file
_spec = importlib.util.spec_from_file_location("wf_review_helpers", os.path.join(ROOT, "worldforge", "review", "build_review.py"))
RV = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(RV)
F, wrap, clamp_lines, ease, col, tracked, fit_font = RV.F, RV.wrap, RV.clamp_lines, RV.ease, RV.col, RV.tracked, RV.fit_font
background, ff, duration, say_available, synth, caption_strip, hue_rgb = (RV.background, RV.ff, RV.duration, RV.say_available,
                                                                           RV.synth, RV.caption_strip, RV.hue_rgb)
W, H, FPS, X264, TAIL, FFMPEG = RV.W, RV.H, RV.FPS, RV.X264, RV.TAIL, RV.FFMPEG
CYAN, PURPLE, GOLD, GREEN, PINK, WHITE, MUTED = RV.CYAN, RV.PURPLE, RV.GOLD, RV.GREEN, RV.PINK, RV.WHITE, RV.MUTED

# No contact address is published unless the founder confirms one: pass --contact-email ADDRESS (or set
# WHITEPAPER_CONTACT_EMAIL). It is pinned in build.json so --check rebuilds the same page.
FORBIDDEN = ["-".join(("agi", "corp", "worlds"))]   # the private repository's name (assembled, never written) must not appear in any output
TITLE = "SmartCiti.X Agentic Worlds — Whitepaper"
ORG = "AGI Future Foundation PBC"
UMBRELLA = "Powered by AGI Corp"
SLUG = "smartcitix-agentic-worlds-whitepaper"

FILMS = {
    "features": {"file": "film-features.mp4", "vtt": "film-features.vtt", "poster": "media/poster-features.jpg",
                 "name": "SmartCiti.X Agentic Worlds: Features",
                 "sections": [("title", 6), ("network", 14), ("walk", 54), ("avatars", 12), ("hive", 12), ("gov", 12), ("end", 10)]},
    "roadmap-stack": {"file": "film-roadmap-stack.mp4", "vtt": "film-roadmap-stack.vtt", "poster": "media/poster-roadmap-stack.jpg",
                      "name": "SmartCiti.X Agentic Worlds: Roadmap and Stack",
                      "sections": [("title", 6), ("stack", 40), ("evidence", 14), ("roadmap", 40), ("ask", 10), ("end", 10)]},
}
for _f in FILMS.values():
    assert sum(s for _, s in _f["sections"]) == 120
TOTAL_S = 120

WALK = [("cancer-dao", "flyin"), ("cancer-dao", "building"), ("cancer-dao", "omega"), ("cancer-dao", "council"),
        ("cancer-dao", "landmark"), ("cancer-dao", "orbit"), ("locator-x", "building"), ("s29-metaverse-dao", "landmark"),
        ("s29-metaverse-dao", "orbit")]
FAMILY = {"focus-rotunda": "PBC focus DAOs", "series-setback": "W3 LLC series worlds, named only",
          "track-twist": "Program-track worlds", "platform-prism": "Earlier worlds with their own sources"}
DISCLAIMER = ("Describes an organization being built. Nothing here is an offer to sell or a solicitation to buy any security, "
              "token or membership interest, and nothing here is legal, tax or financial advice.")


def die(msg):
    print(f"whitepaper FAILED: {msg}")
    sys.exit(1)


def R(p):
    with open(os.path.join(ROOT, p)) as f:
        return json.load(f)


def opt(p):
    return R(p) if os.path.exists(os.path.join(ROOT, p)) else None


def and_list(xs):
    xs = list(xs)
    return ", ".join(xs[:-1]) + (" and " if len(xs) > 1 else "") + (xs[-1] if xs else "")


def fmt(n):
    return f"{n:,}" if isinstance(n, int) else str(n)


# ------------------------------------------------------------------------------------------------ heartbeat
BEAT = re.compile(r"^(\d\d:\d\d:\d\d) (GREEN|RED|AMBER|YELLOW)\b")


def heartbeat_lines():
    p = os.path.join(ROOT, "evidence", "heartbeat.log")
    return [l.rstrip("\n") for l in open(p, errors="replace") if BEAT.match(l)] if os.path.exists(p) else []


def beat_fields(line):
    out = {}
    for part in (line or "").split(" | ")[1:]:
        if ":" in part:
            k, v = part.split(":", 1)
            out[k.strip()] = v.strip()
    return out


# ------------------------------------------------------------------------------------------------ explainer fact check
PTR = re.compile(r"(?<![\w./<>*-])([A-Za-z][\w./-]*\.json)\s*(?:#\s*|\s+)([A-Za-z_][\w-]*(?:\[\*?\])?(?:\.[A-Za-z_][\w-]*(?:\[\*?\])?)*)(?=$|[\s,;)])")
NUM = re.compile(r"-?\d[\d,]*(?:\.\d+)?")
_json_cache = {}


def _resolve(obj, ptr):
    cur, spread, last_arr = [obj], False, False
    for seg in ptr.split("."):
        m = re.match(r"([A-Za-z_][\w-]*)(\[\*?\])?$", seg)
        name, arr = m.group(1), m.group(2)
        nxt = []
        for c in cur:
            if not isinstance(c, dict) or name not in c:
                return None
            v = c[name]
            if arr:
                if not isinstance(v, list):
                    return None
                nxt.extend(v); spread = True
            else:
                nxt.append(v)
        cur, last_arr = nxt, bool(arr)
    if spread:
        if cur and all(isinstance(x, (int, float)) and not isinstance(x, bool) for x in cur):
            return sum(cur)
        return len(cur) if last_arr else None
    return cur[0]


def voice_phrases(VX):
    """Voicing counts as words, built from the registries (voices manifest, avatar registry, hive, dialogues)."""
    voiced = [(VX["coord_v"], "coordinators"), (VX["spec_v"], "specialists"), (VX["adv_v"], "advisors")] + [(n, k) for k, n in VX["other_v"].items()]
    parts = [(VX["coordinators"] - VX["coord_v"], VX["coordinators"], "coordinators"), (VX["advisors"] - VX["adv_v"], VX["advisors"], "advisors"),
             (VX["specialists"] - VX["spec_v"], VX["specialists"], "specialists")]
    nv = sum(max(0, a) for a, _, _ in parts)
    dl = (VX["answers"] or 0) + (VX["turns"] or 0)
    return {"L": fmt(VX["L"]), "S": f"{VX['S']:,.1f}", "voiced": and_list(f"{fmt(n)} {lab}" for n, lab in voiced if n) or "none",
            "notv": and_list(f"{fmt(a)} of {fmt(b)} {lab}" for a, b, lab in parts if a > 0) or "none", "nv": fmt(nv),
            "nonomega": fmt(VX["avatars"] - VX["omegas"]), "avatars": fmt(VX["avatars"]), "hs": fmt(VX["hs"]), "hl": fmt(VX["hl"]),
            "ds": fmt(VX["ds"]), "dl": fmt(dl), "dnv": fmt(dl - (VX["ds"] or 0)), "answers": fmt(VX["answers"]), "turns": fmt(VX["turns"])}


_D = r"\d[\d,]*(?:\.\d+)?"
VOICE_SRC = "worldforge/out/voices/manifest.json#totals; worldforge/out/avatars/index.json#totals; agents/hive/index.json#totals; agents/hive/dialogues.json#totals"
# Sentences in the explainers whose counts move as voicing proceeds: rebuilt from the registries at build time (the
# explainer's wording is kept in build.json under "rebuilt"). A pattern that no longer matches is simply not applied.
TEXT_FIXES = [
    (rf"{_D} of the {_D} non-Omega intros are not voiced yet: [^()]*?\(worldforge/out/voices/manifest\.json\)\.",
     "{nv} of the {nonomega} non-Omega intros are not voiced yet: {notv} (worldforge/out/voices/manifest.json)."),
    (rf"{_D} of {_D} non-Omega avatar intros are not voiced: [^.]*\.", "{nv} of {nonomega} non-Omega avatar intros are not voiced: {notv}."),
    (rf"{_D} of {_D} dialogue lines are voiced \([^)]*\)\.", "{ds} of {dl} dialogue lines are voiced (agents/hive/dialogues.json)."),
    (rf"{_D} of {_D} dialogue lines are not voiced\.", "{dnv} of {dl} dialogue lines are not voiced."),
    (rf"Omega dialogues \(agents/hive/dialogues\.json\): {_D} lines \({_D} answers and {_D} handoff turns\), {_D} spoken\.",
     "Omega dialogues (agents/hive/dialogues.json): {dl} lines ({answers} answers and {turns} handoff turns), {ds} spoken."),
    (rf"Avatar intros \(worldforge/out/voices/manifest\.json\): {_D} lines voiced, [^.]*?, {_D} seconds in total\.",
     "Avatar intros (worldforge/out/voices/manifest.json): {L} lines voiced ({voiced}), {S} seconds in total."),
    (rf"{_D} of {_D} Omega lines, {_D} of {_D} dialogue lines and {_D} avatar intros \([^)]*\)\. The advisors and most specialists are not voiced yet\.",
     "{hs} of {hl} Omega lines, {ds} of {dl} dialogue lines and {L} avatar intros ({voiced}). {nv} of the {nonomega} non-Omega intros are not voiced yet: {notv}."),
    (rf"WorldForge has rendered {_D} intro lines \([^)]*\), {_D} s in all", "WorldForge has rendered {L} intro lines ({voiced}), {S} s in all"),
    (rf"Not every line is voiced: {_D} WorldForge intros of {_D} avatars, and {_D} of {_D} hive lines\.",
     "Not every line is voiced: {L} WorldForge intros of {avatars} avatars, and {hs} of {hl} hive lines."),
    (r"The log currently holds (\d+) beats: (\d+) GREEN and (\d+) RED", "When this explainer was written the log held \\1 beats: \\2 GREEN and \\3 RED"),
    (r"The agent fields of that latest beat are quoted below\.", "The agent fields of that beat are quoted below; the beat this page cites is excerpted beside them."),
]


def apply_text_fixes(doc, VX):
    P = voice_phrases(VX)
    log = []

    def fix(text, where):
        out = text
        for pat, tpl in TEXT_FIXES:
            def rep(m, tpl=tpl):
                return m.expand(tpl.format(**P)) if "\\" in tpl else tpl.format(**P)
            new = re.sub(pat, rep, out)
            if new != out:
                out = new
        if out != text:
            log.append({"where": where, "explainer": text, "page": out, "pointer": VOICE_SRC})
        return out

    for s in doc["sections"]:
        n0 = len(log)
        for key in ("dek",):
            if s.get(key):
                s[key] = fix(s[key], f"{s['id']} / {key}")
        for key in ("paragraphs", "bullets", "not_done"):
            s[key] = [fix(x, f"{s['id']} / {key}") for x in s.get(key, [])]
        if len(log) > n0:
            s["_rebuilt_text"] = True
    for q in doc.get("faq", []):
        q["a"] = fix(q["a"], f"faq / {q['q']}")
        if log and log[-1]["where"] == f"faq / {q['q']}":
            q["_rebuilt"] = True
    return log


def _fact_beats(ctx):
    return ctx["pinned"]["beats_total"], "evidence/heartbeat.log (beats logged when this page was built)", True


def _fact_glb_sweep(ctx):
    v = (ctx["N"].get("glb_sweep") or {}).get("value")
    return v, "evidence/heartbeat.log (GLB field of the beat this page cites)", True


def _fact_world_glb_bytes(ctx):
    return sum(int(w.get("glbBytes") or 0) for w in ctx["index"]["worlds"]), "worldforge/out/index.json#worlds[].glbBytes (sum)", False


def _fact_plan_flags(slug):
    def f(ctx):
        row = next((p for p in ctx["conformance"].get("perPlan") or [] if p.get("slug") == slug), None)
        return (row or {}).get("nativeViolations"), f"worldforge/native/conformance-report.json#perPlan[slug={slug}].nativeViolations", True
    return f


# Facts whose source this build cannot parse as written: the pointer is supplied here so drift shows as "now N".
# (current, pointer, compare the first number only)
FACT_CHECK = {
    ("heartbeat-and-evals", "Beats logged"): _fact_beats,
    ("pipeline-and-validation", "Heartbeat GLB sweep"): _fact_glb_sweep,
    ("pipeline-and-validation", "World GLBs"): _fact_world_glb_bytes,
    ("walkthrough-cancer-dao", "Native name-limit flags in this mount plan"): _fact_plan_flags("cancer-dao"),
}
# Facts whose value is rebuilt from the registry at build time (the explainer's value is kept in build.json).
FACT_REBUILD = {
    ("synthetic-voices", "Dialogue lines spoken"): lambda P, VX: ("{ds} of {dl}".format(**P), "agents/hive/dialogues.json#totals.spoken"),
    ("synthetic-voices", "Avatar intros voiced"): lambda P, VX: ("{L} ({voiced}), {S} s".format(**P), "worldforge/out/voices/manifest.json#totals"),
    ("landmarks-and-avatars", "WorldForge voiced intros"): lambda P, VX: ("{L} lines, {S} s (Kokoro v1.0, local)".format(**P), "worldforge/out/voices/manifest.json#totals"),
    ("landmarks-and-avatars", "Avatars placed in the deep fabrics"): lambda P, VX: (
        f"{fmt(VX['m_av'])} across {VX['m_worlds']} worlds, from {VX['m_models']} models", "my-fabric/worlds/avatars_mount.json#totals"),
}
# A note shown with a fact that quotes an earlier heartbeat beat
FACT_NOTE = {("pipeline-and-validation", "Heartbeat GLB sweep"): "from an earlier beat (07:29:33); the beat this page cites is in the stack section"}


def check_fact(fact, sec_id=None, ctx=None):
    """('verified'|'drift'|'unchecked'|'rebuilt', current value or None, pointer or None) for one explainer fact.

    FACT_REBUILD rewrites the value from the registry ('rebuilt'). FACT_CHECK supplies a pointer for a source this
    build cannot parse. Otherwise only the first JSON file a source names is read, and only when it is followed by a
    plain pointer. A pointer that spreads over a list ([] / [*]) is summed only when the source says "(sum)". A list or
    object is compared by its length only when the value is that bare number (an object), or (a list) starts with it
    followed by ':', ',', '(' or 'items'. Anything else is left 'unchecked' and shown as the explainer agent's reading of
    its source."""
    key = (sec_id, fact.get("label"))
    if ctx and key in FACT_REBUILD:
        val, ref = FACT_REBUILD[key](voice_phrases(ctx["VX"]), ctx["VX"])
        fact["_was"], fact["value"] = fact.get("value"), val
        return "rebuilt", val, ref
    if ctx and key in FACT_CHECK:
        cur, ref, first_only = FACT_CHECK[key](ctx)
        nums = [float(x.replace(",", "")) for x in NUM.findall(str(fact.get("value", "")))]
        cands = nums[:1] if first_only else nums
        if cur is None or not cands:
            return "unchecked", None, None
        return ("verified" if any(abs(n - cur) < 1e-9 for n in cands) else "drift"), cur, ref
    src = fact.get("source", "")
    first = re.search(r"[A-Za-z][\w./<>*-]*\.json", src)
    m = PTR.search(src)
    if not first or not m or m.start() != first.start():
        return "unchecked", None, None
    path, ptr = m.group(1), m.group(2)
    rest = src[m.end():].strip()
    spread = "[" in ptr
    if spread and not rest.startswith("(sum)"):
        return "unchecked", None, None
    if rest and not (rest[0] in ",;" or rest.startswith("(sum)") or rest.startswith("(count)") or re.match(r"\(\d+ entries\)", rest)):
        return "unchecked", None, None
    full = os.path.join(ROOT, path)
    if not os.path.isfile(full):
        return "unchecked", None, None
    if path not in _json_cache:
        try:
            _json_cache[path] = json.load(open(full))
        except Exception:
            return "unchecked", None, None
    v = _resolve(_json_cache[path], ptr)
    value = str(fact.get("value", "")).strip()
    nums = [float(x.replace(",", "")) for x in NUM.findall(value)]
    if isinstance(v, bool) or v is None:
        return "unchecked", None, None
    if isinstance(v, dict):   # an object whose headline count is one of these keys is compared on that key
        key = next((k for k in ("total", "violations", "tokens", "count") if isinstance(v.get(k), (int, float)) and not isinstance(v.get(k), bool)), None)
        if key and re.match(r"\d", value):
            v, ptr = v[key], f"{ptr}.{key}"
    if isinstance(v, (int, float)):
        cur, cands = v, nums[:1] if ptr.endswith((".total", ".violations", ".tokens", ".count")) else nums
    elif isinstance(v, (list, dict)):
        mm = re.match(r"(\d[\d,]*)\s*(?:$|:|,|\(|items\b)", value) if isinstance(v, list) else re.fullmatch(r"(\d[\d,]*)", value)
        if not mm:
            return "unchecked", None, None
        cur, cands = len(v), [float(mm.group(1).replace(",", ""))]
    else:
        return "unchecked", None, None
    ref = f"{path}#{ptr}"
    if any(abs(n - cur) < 1e-9 for n in cands):
        return "verified", cur, ref
    if not cands:
        return "unchecked", None, None
    return "drift", cur, ref


# ------------------------------------------------------------------------------------------------ roadmap qualifiers
# atlas/roadmap.json belongs to another team. Where its wording overstates what is done, this page shows a qualified
# line instead and lists the roadmap's own wording under the table (build.json "page_qualifiers"). A pattern that no
# longer matches (the source was fixed) is simply not applied.
ROADMAP_ITEM_QUALIFIERS = [
    (r"management teams seated by each company's own agents",
     "Agent swarms, metaprompts and management teams generated by each company's own swarm (no agent is seated)"),
    (r"2-of-3 signed steward votes",
     "Hash-chained agent ledger with 2-of-3 steward approvals signed with throwaway test keys (no steward is seated)"),
]


def qualify_roadmap(roadmap, n_artemis_logs, n_worlds):
    out = []
    for p in roadmap.get("phases", []):
        items = []
        for it in p.get("items", []):
            new = next((q for pat, q in ROADMAP_ITEM_QUALIFIERS if re.search(pat, it)), None)
            if new:
                out.append({"where": f"atlas/roadmap.json#phases[{p['name']}].items", "source": it, "page": new})
            items.append(new or it)
        p["items"] = items
    for s in roadmap.get("stack", []):
        if s.get("name", "").startswith("RP1 Artemis") and re.search(r"every world", s.get("role", "")):
            new = (f"loads spatial fabrics; {n_artemis_logs} fabrics have local load logs (evidence/artemis-*.log), not one per world; "
                   f"the deep fabrics of the {n_worlds} WorldForge worlds have not been loaded in Artemis yet")
            out.append({"where": f"atlas/roadmap.json#stack[{s['name']}].role", "source": s["role"], "page": new})
            s["role"] = new
    return out


# ------------------------------------------------------------------------------------------------ registry reads
def load(pinned):
    """Everything the page and films show, read from the registries now. `pinned` fixes the values that move between
    builds without the whitepaper changing (the heartbeat beat it cites and the build date)."""
    N, used = {}, set()

    def num(key, value, source):
        N[key] = {"value": value, "source": source}
        used.add(source.split("#")[0].split(" ")[0])
        return value

    def rd(p):
        used.add(p)
        return R(p)

    def ro(p):
        if os.path.exists(os.path.join(ROOT, p)):
            used.add(p)
            return R(p)
        return None

    idx = rd("worldforge/out/index.json")
    t = idx["totals"]
    for k in ("worlds", "cards", "evals", "failed", "anchored", "primitives"):
        num(k, t[k], f"worldforge/out/index.json#totals.{k}")
    worlds = idx["worlds"]
    names = {w["slug"]: w["name"] for w in worlds}
    num("zones", sum(w["zones"] for w in worlds), "worldforge/out/index.json#worlds[].zones (sum)")
    num("broken", len(idx.get("broken", [])), "worldforge/out/index.json#broken")

    kinds, bound, omega_dns, seats, seats_empty, reserved_entries = {}, 0, 0, 0, 0, 0
    cards = {}
    rights = None
    for w in worlds:
        doc = R(f"worldforge/out/{w['slug']}/cards.json")
        cards[w["slug"]] = doc
        rights = rights or doc.get("rights")
        for c in doc["cards"]:
            kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
            bd = c.get("binding") or {}
            if bd.get("swarm") and bd.get("metaprompt") and bd.get("fabricNode"):
                bound += 1
            if c["kind"] == "omega" and c.get("status") == "defined, not seated" and c.get("seated_agent") is None:
                omega_dns += 1
            if c["kind"] == "seat":
                seats += 1
                seats_empty += c.get("seated") is None
            reserved_entries += len(c.get("reserved_for_humans") or [])
    used.add("worldforge/out/<slug>/cards.json")
    if sum(kinds.values()) != t["cards"]:
        die(f"cards.json files hold {sum(kinds.values())} cards but worldforge/out/index.json totals.cards is {t['cards']} (mid-rebuild?)")
    src_cards = "worldforge/out/<slug>/cards.json"
    num("card_kinds", len(kinds), f"{src_cards} (distinct kind)")
    num("bound", bound, f"{src_cards} (binding.swarm + metaprompt + fabricNode)")
    num("omega_cards_dns", omega_dns, f"{src_cards} (kind omega, status 'defined, not seated', seated_agent null)")
    num("seats", seats, f"{src_cards} (kind seat)")
    num("seats_empty", seats_empty, f"{src_cards} (kind seat, seated null)")
    num("reserved_entries", reserved_entries, f"{src_cards} (reserved_for_humans entries, summed)")
    num("rights", len(rights or []), "worldforge/out/<slug>/cards.json#rights")

    pbc = rd("worlds/PBC.json")
    num("steward_seats", pbc["steward_seats"], "worlds/PBC.json#steward_seats")
    num("reserved_actions", len(pbc["reserved_for_humans"]), "worlds/PBC.json#reserved_for_humans")

    av = (ro("worldforge/out/avatars/index.json") or {}).get("totals") or {}
    for k in ("avatars", "specialists", "coordinators", "advisors", "omegas", "persona_prompts", "prompt_gates", "prompt_gates_failing", "evals", "failing"):
        if k in av:
            num(f"avatars.{k}", av[k], f"worldforge/out/avatars/index.json#totals.{k}")
    ava = ro("worldforge/out/assets/avatars/index.json") or {}
    num("avatar_glbs", (ava.get("totals") or {}).get("roles"), "worldforge/out/assets/avatars/index.json#totals.roles")
    num("avatar_triangles", (ava.get("totals") or {}).get("triangles"), "worldforge/out/assets/avatars/index.json#totals.triangles")

    def validation(p):
        v = ro(p) or {}
        files = v.get("files") or {}
        return {"validator": v.get("validator", ""), "files": len(files), "errors": sum(int(x.get("errors") or 0) for x in files.values()),
                "warnings": sum(int(x.get("warnings") or 0) for x in files.values())}
    av_val = validation("worldforge/out/assets/avatars/validation.json")
    lm_val = validation("worldforge/out/assets/landmarks/validation.json")
    num("avatar_validated", av_val["files"], "worldforge/out/assets/avatars/validation.json#files")
    num("avatar_val_errors", av_val["errors"], "worldforge/out/assets/avatars/validation.json#files[].errors (sum)")
    lm = ro("worldforge/out/assets/landmarks/index.json") or {}
    num("landmarks", (lm.get("totals") or {}).get("worlds"), "worldforge/out/assets/landmarks/index.json#totals.worlds")
    num("landmark_validated", lm_val["files"], "worldforge/out/assets/landmarks/validation.json#files")
    num("landmark_val_errors", lm_val["errors"], "worldforge/out/assets/landmarks/validation.json#files[].errors (sum)")
    families = []
    for style, info in (lm.get("styles") or {}).items():
        families.append({"style": style, "label": FAMILY.get(style, style), "count": info.get("count", 0), "basis": info.get("basis", "")})
    families.sort(key=lambda f: -f["count"])

    oc = ro("worldforge/out/onchain/index.json") or {}
    num("tokens", (oc.get("totals") or {}).get("tokens"), "worldforge/out/onchain/index.json#totals.tokens")
    dep = oc.get("deployment") or {}
    num("minted", dep.get("minted"), "worldforge/out/onchain/index.json#deployment.minted")
    num("onchain_evals", (oc.get("evals") or {}).get("total"), "worldforge/out/onchain/index.json#evals.total")
    num("onchain_failed", (oc.get("evals") or {}).get("failed"), "worldforge/out/onchain/index.json#evals.failed")
    num("merkle_world_roots", (oc.get("network") or {}).get("worlds"), "worldforge/out/onchain/index.json#network.worlds")

    hive = ro("agents/hive/index.json") or {}
    ht = hive.get("totals") or {}
    for k in ("omegas", "voices", "lines", "spoken"):
        num(f"hive.{k}", ht.get(k), f"agents/hive/index.json#totals.{k}")
    num("hive.seated", sum(1 for o in hive.get("omegas", []) if o.get("seated")), "agents/hive/index.json#omegas[].seated")
    dlg = (ro("agents/hive/dialogues.json") or {}).get("totals") or {}
    for k in ("answers", "handoffs", "turns", "spoken", "citations"):
        if k in dlg:
            num(f"dialogues.{k}", dlg[k], f"agents/hive/dialogues.json#totals.{k}")
    engine = (hive.get("voice_engine") or {}).get("name", "")

    swarm_files = sorted(p for p in glob.glob(os.path.join(ROOT, "agents/swarms/*.json")) if not p.endswith("agi-corp.json"))
    used.add("agents/swarms/*.json")
    num("swarms", len(swarm_files), "agents/swarms/*.json (every file except agi-corp.json)")
    num("specialists", sum(len(json.load(open(p)).get("agents", [])) for p in swarm_files), "agents/swarms/<slug>.json#agents (sum)")
    pt = (ro("agents/prompts/index.json") or {}).get("totals") or {}
    num("prompts", pt.get("prompts"), "agents/prompts/index.json#totals.prompts")
    num("prompts_failing", pt.get("failing"), "agents/prompts/index.json#totals.failing")
    num("prompts_awaiting_focus", pt.get("spec_metaprompts_awaiting_focus"), "agents/prompts/index.json#totals.spec_metaprompts_awaiting_focus")
    led = os.path.join(ROOT, "agents/ledger/ledger.jsonl")
    if os.path.exists(led):
        used.add("agents/ledger/ledger.jsonl")
        num("ledger_entries", sum(1 for l in open(led) if l.strip()), "agents/ledger/ledger.jsonl (line count)")

    sp = (ro("my-fabric/worlds/spaces_index.json") or {}).get("totals") or {}
    num("exteriors", sp.get("exteriors"), "my-fabric/worlds/spaces_index.json#totals.exteriors")
    num("interiors", sp.get("interiors"), "my-fabric/worlds/spaces_index.json#totals.interiors")
    num("at_2048", sp.get("at_2048"), "my-fabric/worlds/spaces_index.json#totals.at_2048")
    sc = (ro("my-fabric/worlds/scenes_index.json") or {}).get("totals") or {}
    if sc:
        num("forecourts", sc.get("forecourts"), "my-fabric/worlds/scenes_index.json#totals.forecourts")
    vo = (ro("worldforge/out/voices/manifest.json") or {}).get("totals") or {}
    num("voiced_intros", vo.get("lines"), "worldforge/out/voices/manifest.json#totals.lines")
    num("voiced_seconds", vo.get("seconds"), "worldforge/out/voices/manifest.json#totals.seconds")
    br = dict(vo.get("by_role") or {})
    num("voiced_by_role", dict(br),"worldforge/out/voices/manifest.json#totals.by_role")
    mount = (ro("my-fabric/worlds/avatars_mount.json") or {}).get("totals") or {}
    VX = {"L": vo.get("lines") or 0, "S": float(vo.get("seconds") or 0), "coord_v": br.pop("coordinator", 0), "spec_v": br.pop("specialist", 0),
          "adv_v": sum(br.pop(k, 0) for k in ("host", "liaison", "alignment", "advisor")), "other_v": br,
          "avatars": av.get("avatars") or 0, "advisors": av.get("advisors") or 0, "specialists": av.get("specialists") or 0,
          "coordinators": av.get("coordinators") or 0, "omegas": av.get("omegas") or 0,
          "hs": ht.get("spoken"), "hl": ht.get("lines"), "ds": dlg.get("spoken"), "answers": dlg.get("answers"), "turns": dlg.get("turns"),
          "m_av": mount.get("avatars"), "m_worlds": mount.get("worlds"), "m_models": mount.get("models")}

    rp1 = (ro("rp1/publish/manifest.json") or {}).get("summary") or {}
    for k in ("installers", "dry_runs_ok", "ready", "blocked", "worlds"):
        if k in rp1:
            num(f"rp1.{k}", rp1[k], f"rp1/publish/manifest.json#summary.{k}")
    nat = (ro("worldforge/native/conformance-report.json") or {}).get("totals") or {}
    num("mount_nodes", nat.get("nodes"), "worldforge/native/conformance-report.json#totals.nodes")
    num("mount_plans", nat.get("plans"), "worldforge/native/conformance-report.json#totals.plans")

    gates = rd("worldforge/out/cancer-dao/manifest.json").get("gates", {})
    roadmap = rd("atlas/roadmap.json")

    beats = heartbeat_lines()
    used.add("evidence/heartbeat.log")
    beat = pinned["heartbeat_line"]
    bf = beat_fields(beat)
    gm = re.match(r"(\d[\d,]*) GLBs validated, (\d+) with errors", bf.get("GLB", ""))
    num("beats_total", pinned["beats_total"], "evidence/heartbeat.log (lines beginning with a time and a status, when built)")
    num("beats_green", pinned["beats_green"], "evidence/heartbeat.log (GREEN lines, when built)")
    if gm:
        num("glb_sweep", int(gm.group(1).replace(",", "")), "evidence/heartbeat.log (GLB field of the cited beat)")
        num("glb_sweep_bad", int(gm.group(2)), "evidence/heartbeat.log (GLB field of the cited beat)")

    # featured world (Cancer DAO) facts for the walkthrough lower thirds
    feat = {}
    for slug in sorted({s for s, _ in WALK}):
        cs = cards[slug]["cards"]
        bz = next((c for c in cs if c["kind"] == "zone" and (c.get("building") or {}).get("exterior")), None)
        om = next((c for c in cs if c["kind"] == "omega"), None)
        gate = next((c for c in cs if c["kind"] == "gate"), None)
        lmw = next((x for x in lm.get("worlds", []) if x.get("slug") == slug), {})
        team = opt(f"worlds/generated/teams/{slug}.json") or {}
        hv = next((o for o in hive.get("omegas", []) if (o.get("world") or "").lower() in (slug, names[slug].lower()) or o.get("id") == f"omega.{slug}"), {})
        fs = [c for c in cs if c["kind"] == "seat"]
        feat[slug] = {
            "name": names[slug], "brand": team.get("brand") or {},
            "zones": sum(1 for c in cs if c["kind"] == "zone"), "agents": sum(1 for c in cs if c["kind"] == "agent"),
            "advisors": sum(1 for c in cs if c["kind"] == "advisor"),
            "building": ({"zone": bz["name"], "kind": bz["building"]["kind"]} if bz else None),
            "omega_status": (om or {}).get("status", ""), "omega_voice": ((om or {}).get("voice") or {}).get("kokoro") or (hv.get("voice") or {}).get("kokoro"),
            "gate_dist": abs(((gate or {}).get("volum") or {}).get("center", [0, 0, 0])[2]) if gate else None,
            "seats": len(fs), "seats_empty": sum(1 for c in fs if c.get("seated") is None),
            "landmark": {"height": lmw.get("height_m"), "style": lmw.get("style"), "applied": not str(lm.get("placement_rule", "")).startswith("suggested, not applied")},
        }
    used.add("worlds/generated/teams/<slug>.json")
    used.add("worldforge/out/assets/landmarks/index.json")

    artemis_logs = sorted(os.path.basename(p) for p in glob.glob(os.path.join(ROOT, "evidence", "artemis-*.log")))
    used.add("evidence/artemis-*.log")
    num("artemis_logs", len(artemis_logs), "evidence/artemis-*.log (file count)")
    roadmap = json.loads(json.dumps(roadmap))
    qualified = qualify_roadmap(roadmap, len(artemis_logs), t["worlds"])

    # explainer facts: re-read (pointer in the source, or a pointer this build adds), or rebuilt from the registry
    ctx = {"VX": VX, "N": N, "conformance": ro("worldforge/native/conformance-report.json") or {}, "index": idx, "pinned": pinned}
    order_names = ["world-and-governance", "agents-and-hive", "environments-and-stack"]
    paths = [os.path.join(CONTENT, f"explainers-{n}.json") for n in order_names]
    paths += [p for p in sorted(glob.glob(os.path.join(CONTENT, "explainers-*.json"))) if p not in paths]
    explainers, rebuilt = [], []
    for p in paths:
        if not os.path.exists(p):
            continue
        doc = json.load(open(p))
        for s in doc["sections"]:
            for fct in s.get("facts", []):
                st, cur, ref = check_fact(fct, s["id"], ctx)
                fct["_check"] = {"status": st, "current": cur, "pointer": ref}
                if st == "rebuilt":
                    rebuilt.append({"where": f"{s['id']} / fact '{fct['label']}'", "explainer": fct["_was"], "page": fct["value"], "pointer": ref})
        rebuilt += apply_text_fixes(doc, VX)
        explainers.append(doc)

    market = json.load(open(os.path.join(CONTENT, "market.json")))
    keep = [c for c in market["claims"] if c.get("verdict") in ("confirmed", "corrected")]
    ids = {c["id"] for c in keep}
    order = []
    for part in ("why", "what", "how"):
        for para in market["narrative"][part]:
            for cid in re.findall(r"\[([a-z0-9-]+)\]", para):
                if cid not in ids:
                    die(f"the narrative cites [{cid}], which content/market.json does not keep as confirmed or corrected")
                if cid not in order:
                    order.append(cid)
    for c in keep:
        if c["id"] not in order:
            order.append(c["id"])
    claims = {c["id"]: c for c in keep}
    fn = {cid: i + 1 for i, cid in enumerate(order)}

    return {"N": N, "used": used, "names": names, "worlds": worlds, "kinds": dict(sorted(kinds.items(), key=lambda kv: -kv[1])),
            "rights": rights or [], "pbc": pbc, "families": families, "av_val": av_val, "lm_val": lm_val, "deployment": dep,
            "engine": engine, "gates": gates, "roadmap": roadmap, "beat": beat, "beat_fields": bf, "feat": feat,
            "explainers": explainers, "rebuilt": rebuilt, "qualified": qualified, "market": market, "claims": claims, "order": order, "fn": fn,
            "date": pinned["date"], "narration": pinned.get("narration") or "silent", "lm": lm, "VX": VX, "artemis_logs": artemis_logs,
            "base_url": pinned.get("base_url"), "contact": pinned.get("contact"), "built_at": pinned.get("built_at") or pinned["date"]}


def V(D, key):
    return D["N"][key]["value"]


def S(D, key):
    return D["N"][key]["source"]


def open_gates(D):
    return [(k, v) for k, v in D["gates"].items() if not str(v).startswith("done")]


def gate_id(k):
    return k.split(" ")[0]


# ------------------------------------------------------------------------------------------------ stack + roadmap model
def stack_layers(D):
    """Six layers, bottom to top, each with facts read from the registries (shared by the film, the SVG and the page)."""
    g = D["gates"]
    gs = "; ".join(f"{gate_id(k)} {str(v).split(':')[0]}" for k, v in g.items())
    stack = {s["name"]: s for s in D["roadmap"].get("stack", [])}
    artemis = next((n for n in stack if n.startswith("RP1 Artemis")), "RP1 Artemis")
    return [
        {"id": "assets", "name": "Assets", "sub": "glTF 2.0 + PBR, Khronos-validated",
         "facts": [f"{fmt(V(D, 'glb_sweep'))} GLBs in the heartbeat sweep, {V(D, 'glb_sweep_bad')} with errors or warnings" if "glb_sweep" in D["N"] else "GLB sweep not in the cited beat",
                   f"{V(D, 'exteriors')} building exteriors + {V(D, 'interiors')} interiors; {V(D, 'at_2048')} facade maps at 2048 px",
                   f"{V(D, 'landmarks')} civic landmarks and {V(D, 'avatar_glbs')} avatar role models, {V(D, 'landmark_val_errors') + V(D, 'avatar_val_errors')} validator errors"],
         "source": "evidence/heartbeat.log; my-fabric/worlds/spaces_index.json; worldforge/out/assets/*/validation.json", "status": "in use"},
        {"id": "cards", "name": "SmartCiti.X Master Cards", "sub": "one card per object: Volum, 7 rights, 6 reserved actions",
         "facts": [f"{fmt(V(D, 'cards'))} cards in {V(D, 'card_kinds')} kinds across {V(D, 'worlds')} worlds",
                   f"rights: {', '.join(D['rights'])}",
                   f"{fmt(V(D, 'reserved_entries'))} reservation entries, each held for the Steward Council"],
         "source": "worldforge/out/index.json; worldforge/out/<slug>/cards.json", "status": "in use"},
        {"id": "agents", "name": "Agents", "sub": "swarms, metaprompts, avatars, the Omega Hive",
         "facts": [f"{V(D, 'swarms')} swarms, {V(D, 'specialists')} specialist agents; {V(D, 'prompts')} prompts, {V(D, 'prompts_failing')} failing",
                   f"{V(D, 'avatars.avatars')} avatars bound to agent records, {V(D, 'avatars.persona_prompts')} persona prompts",
                   f"{V(D, 'hive.omegas')} Omega Stewards, {V(D, 'hive.seated')} seated; voices synthetic ({D['engine']})"],
         "source": "agents/swarms/*.json; agents/prompts/index.json; worldforge/out/avatars/index.json; agents/hive/index.json", "status": "in use, stub replies"},
        {"id": "evidence", "name": "Heartbeat, evals, ledger", "sub": "every beat re-runs the checks",
         "facts": [f"{V(D, 'beats_total')} beats logged ({V(D, 'beats_green')} GREEN); cited beat {D['beat'][:8]} {BEAT.match(D['beat']).group(2) if D['beat'] else '?'}",
                   f"{fmt(V(D, 'evals'))} WorldForge evals, {V(D, 'failed')} failing; {fmt(V(D, 'avatars.evals'))} avatar and {V(D, 'onchain_evals')} onchain evals",
                   f"{V(D, 'ledger_entries')} hash-chained ledger entries, signed with test keys" if "ledger_entries" in D["N"] else "ledger not present"],
         "source": "evidence/heartbeat.log; worldforge/out/index.json; agents/ledger/ledger.jsonl", "status": "in use"},
        {"id": "engines", "name": "Engines: RP1 + Sneeze", "sub": f"{artemis} fabrics, MSF installers, Sneeze native path",
         "facts": [f"{V(D, 'rp1.installers')} RP1 installers, {V(D, 'rp1.dry_runs_ok')} dry runs OK; {V(D, 'rp1.ready')} worlds ready, {V(D, 'rp1.blocked')} blocked (no anchor)",
                   f"Sneeze gates: {gs}",
                   f"{fmt(V(D, 'mount_nodes'))} mount-plan nodes in {V(D, 'mount_plans')} plans, not mounted"],
         "source": "rp1/publish/manifest.json; worldforge/out/<slug>/manifest.json; worldforge/native/conformance-report.json", "status": "dry-run; not mounted"},
        {"id": "onchain", "name": "Onchain-ready export", "sub": "ERC-721-style metadata + Merkle roots, not deployed",
         "facts": [f"{V(D, 'tokens')} draft token records, one per Master Card",
                   f"{V(D, 'merkle_world_roots')} world Merkle roots + 1 network root; {V(D, 'onchain_evals')} checks, {V(D, 'onchain_failed')} failing",
                   f"chain: {D['deployment'].get('chain') or 'none'}; contract: {D['deployment'].get('contract') or 'none'}; minted: {V(D, 'minted')}"],
         "source": "worldforge/out/onchain/index.json", "status": "not deployed, not minted"},
    ]


def phase_steps(D):
    return [p for p in D["roadmap"].get("phases", [])]


# ------------------------------------------------------------------------------------------------ narration + captions
def synthetic(D):
    return (D["narration"] or "").startswith("say:")


def narration(D, film):
    """The section-level narration line ({section: text}). Sections with items (walkthrough clips, stack layers,
    roadmap steps) add one short line per item: see film_plan()."""
    syn = synthetic(D)
    voice_bit = "You are hearing a synthetic voice." if syn else "This cut is silent: captions only."
    if film == "features":
        fam = D["families"]
        return {
            "title": f"SmartCiti.X agentic worlds: the features. {voice_bit}",
            "network": (f"{V(D, 'worlds')} coming-soon worlds in {len(fam)} families share one charter and one rulebook: "
                        f"{fmt(V(D, 'cards'))} Master Cards and {fmt(V(D, 'evals'))} evals, {V(D, 'failed')} failing."),
            "walk": None,
            "avatars": (f"{V(D, 'avatars.avatars')} avatars are bound to agent records with persona prompts. "
                        f"{V(D, 'avatar_glbs')} role models pass the Khronos validator with {V(D, 'avatar_val_errors')} errors."),
            "hive": (f"The Omega Hive: {V(D, 'hive.omegas')} Omega Stewards, defined, not seated. "
                     f"{V(D, 'hive.spoken')} of {V(D, 'hive.lines')} lines are voiced with synthetic voices."),
            "gov": (f"Agents operate; people govern. {V(D, 'reserved_actions')} actions, from the final vote to treasury transfers, "
                    f"are held for a two-of-three human Steward Council."),
            "end": "Not mounted in Sneeze. Nothing deployed or minted. Most worlds have no anchor. " + ("The narration was a synthetic voice." if syn else "Omega voices are synthetic."),
        }
    phases = phase_steps(D)
    cnt = {s: sum(1 for p in phases if p.get("status") == s) for s in ("done", "now", "next", "later")}
    status = BEAT.match(D["beat"]).group(2) if D["beat"] else "unknown"
    return {
        "title": f"SmartCiti.X: the roadmap and the stack. {voice_bit}",
        "stack": "The stack, layer by layer.",
        "evidence": (f"Evidence: {fmt(V(D, 'glb_sweep'))} GLBs validated, {fmt(V(D, 'evals'))} WorldForge evals with {V(D, 'failed')} failing, "
                     f"{V(D, 'beats_total')} heartbeat beats logged. The beat cited here was {status}."),
        "roadmap": (f"The roadmap: {cnt['done']} phase done and {len(phases) - cnt['done']} open. "
                    f"Every open phase waits on a named human gate."),
        "ask": "Next steps are human decisions: anchors, the shared database, real stewards, and whether to publish on RP1.",
        "end": "Nothing deployed, minted or mounted. Omegas are defined, not seated. " + ("The voice was synthetic." if syn else "Omega voices are synthetic."),
    }


def spoken(text):
    """What the synthetic voice reads: the captions keep the written form."""
    for a, b in (("SmartCiti.X", "SmartCiti dot X"), ("Locator.X", "Locator dot X"), ("2 of 3", "two of three")):
        text = text.replace(a, b)
    return text


def split_frames(total, n):
    base, extra = divmod(total, n)
    return [base + (1 if i < extra else 0) for i in range(n)]


MODE_LABEL = {"flyin": "Fly-in", "building": "Building", "omega": "Omega Steward", "council": "Steward Council", "landmark": "Civic landmark", "orbit": "Orbit"}


def walk_item(D, slug, mode):
    f = D["feat"][slug]
    if mode == "flyin":
        return "Fly-in", "From above the Alignment Evaluation Gate" + (f" ({f['gate_dist']:g} m south)" if f["gate_dist"] else "") + " down to the plaza"
    if mode == "building":
        b = f["building"]
        return (f"Building · {b['zone']}", f"Up to the {b['kind']} door, then inside the interior") if b else ("Building", "No building linked in the cards")
    if mode == "omega":
        return "Omega Steward", f"{f['omega_status'] or 'defined, not seated'} · voice defined" + (f": Kokoro {f['omega_voice']}" if f["omega_voice"] else "") + " (synthetic), not played here"
    if mode == "council":
        return "Steward Council", f"{f['seats']} human seats, {f['seats_empty']} empty · 2 of 3 signatures decide"
    if mode == "landmark":
        lmk = f["landmark"]
        return "Civic landmark", f"{lmk['height']:g} m {lmk['style']} tower · placement " + ("applied" if lmk["applied"] else "suggested, not applied")
    return "Orbit", f"{f['zones']} zones, {f['agents']} specialist agents, {f['advisors']} scripted advisors"


def walk_line(D, slug, mode, first, first_of_world):
    """One short narrated line per walkthrough clip (the lower third's facts, spoken)."""
    f = D["feat"][slug]
    if mode == "flyin":
        s = "the fly-in, from above the gate down to the plaza."
    elif mode == "building":
        s = f"a building in the {f['building']['zone']} zone, up to the door and inside." if f["building"] else "a building."
    elif mode == "omega":
        s = f"the Omega Steward: {f['omega_status'] or 'defined, not seated'}. Its synthetic voice is defined, not played here."
    elif mode == "council":
        s = f"the Steward Council: {f['seats']} human seats, {f['seats_empty']} empty. 2 of 3 signatures decide."
    elif mode == "landmark":
        lmk = f["landmark"]
        s = f"the civic landmark, a {lmk['height']:g} metre tower" + ("." if lmk["applied"] else ", its placement suggested, not applied.")
    else:
        s = f"an orbit: {f['zones']} zones and {f['agents']} specialist agents."
    if first:
        return f"A walk through {f['name']}, recorded in the WorldForge viewer. First, {s}"
    if first_of_world:
        return f"{f['name']}: {s}"
    return f"Then {s}"


LAYER_SAY = {"assets": "assets", "cards": "SmartCiti.X Master Cards", "agents": "agents", "evidence": "heartbeat, evals and ledger",
             "engines": "engines, RP1 and Sneeze", "onchain": "the onchain-ready export"}
ORDINAL = ["one", "two", "three", "four", "five", "six", "seven", "eight"]


def layer_line(D, i, L):
    sweep = f"{fmt(V(D, 'glb_sweep'))} GLBs in the heartbeat sweep, {V(D, 'glb_sweep_bad')} with errors." if "glb_sweep" in D["N"] else "glTF models validated by Khronos."
    txt = {"assets": sweep,
           "cards": f"{fmt(V(D, 'cards'))} cards, each with a Volum and {V(D, 'rights')} rights.",
           "agents": f"{V(D, 'swarms')} swarms, {V(D, 'avatars.avatars')} avatars and {V(D, 'hive.omegas')} Omega Stewards, {V(D, 'hive.seated')} seated.",
           "evidence": f"{fmt(V(D, 'evals'))} evals, {V(D, 'failed')} failing, and a ledger signed with test keys.",
           "engines": f"{V(D, 'rp1.installers')} RP1 installers, dry runs only; nothing is mounted in Sneeze.",
           "onchain": f"{V(D, 'tokens')} draft token records; nothing deployed, {V(D, 'minted')} minted."}[L["id"]]
    return f"Layer {ORDINAL[i]}, {LAYER_SAY[L['id']]}: {txt}"


def gate_short(g):
    g = re.sub(r"\s*\([^)]*\)", "", g or "")
    return re.split(r"[;:]", g)[0].strip()


def film_plan(D, film):
    """Segments with exact frame counts (120 s at 24 fps) and the narration script: one event per line, with the
    earliest time it may start ('t'), the time it should be done by ('until', the start of the next item or the end of
    its section) and the hard end of its section ('sec_end')."""
    secs = FILMS[film]["sections"]
    base = narration(D, film)
    segs, script, t0 = [], [], 0.0
    for name, dur in secs:
        n = dur * FPS
        items = []
        if film == "features" and name == "walk":
            clips = [(s, m) for s, m in WALK if os.path.exists(os.path.join(ROOT, f"worldforge/review/out/clips/{s}-{m}.mp4"))]
            if not clips:
                die("no walkthrough clips in worldforge/review/out/clips (run node worldforge/review/record.mjs)")
            prev = None
            for i, ((slug, mode), fr) in enumerate(zip(clips, split_frames(n, len(clips)))):
                title, desc = walk_item(D, slug, mode)
                segs.append({"section": name, "kind": "clip", "slug": slug, "mode": mode, "title": title, "desc": desc, "frames": fr,
                             "src": f"worldforge/review/out/clips/{slug}-{mode}.mp4"})
                items.append((fr / FPS, walk_line(D, slug, mode, i == 0, slug != prev)))
                prev = slug
        else:
            segs.append({"section": name, "kind": "card", "frames": n})
            if film == "roadmap-stack" and name == "stack":
                for i, (L, fr) in enumerate(zip(stack_layers(D), split_frames(n, 6))):
                    items.append((fr / FPS, layer_line(D, i, L)))
            if film == "roadmap-stack" and name == "roadmap":
                for st, fr in zip(roadmap_steps(D), roadmap_frames(D, n)):
                    items.append((fr / FPS, st["line"]))
        sec_end = t0 + dur - 0.35
        evs = []
        if base.get(name):
            evs.append({"section": name, "t": round(t0 + 0.5, 3), "text": base[name]})
        ta = t0
        for d, line in items:
            evs.append({"section": name, "t": round(ta + 0.15, 3), "text": line})
            ta += d
        for i, ev in enumerate(evs):
            ev["until"] = evs[i + 1]["t"] if i + 1 < len(evs) else round(sec_end, 3)
            ev["sec_end"] = round(sec_end, 3)
        script += evs
        t0 += dur
    assert sum(s["frames"] for s in segs) == TOTAL_S * FPS
    return segs, script


def roadmap_steps(D):
    out = []
    for p in phase_steps(D):
        line = f"{p['name']}: done." if p.get("status") == "done" else f"{p['name']}. Gate: {gate_short(p.get('gate'))}."
        out.append({"kind": "phase", "phase": p, "line": line})
    g = [str(v) for v in D["gates"].values()]
    nd = sum(1 for v in g if v.startswith("done"))
    out.append({"kind": "gates", "line": f"WorldForge gates on the Sneeze native path: {nd} done, {len(g) - nd} not done. Nothing is mounted."})
    return out


def roadmap_frames(D, n):
    k = len(phase_steps(D))
    gates_fr = 7 * FPS
    return split_frames(n - gates_fr, k) + [gates_fr]


def estimate_seconds(text):
    """Speaking time at the narration rate (say -r 180, about 3 words a second), for silent cuts."""
    return max(1.2, len(spoken(text).split()) / 2.9)


def schedule(script, raw):
    """Place each line: it starts at its earliest time or 0.25 s after the line before it in the same section, whichever
    is later. A section that would overrun is read faster (tempo up to 1.35); beyond that the build fails so the line
    gets shortened rather than cut off. Returns the events with start, end, seconds and tempo set."""
    out, i = [], 0
    while i < len(script):
        j = i
        while j < len(script) and script[j]["section"] == script[i]["section"]:
            j += 1
        group, durs = script[i:j], raw[i:j]
        for k in range(15):
            tempo = 1.0 + 0.025 * k
            prev_end, placed = None, []
            for ev, d in zip(group, durs):
                start = ev["t"] if prev_end is None else max(ev["t"], prev_end + 0.25)
                sec = d / tempo
                placed.append(dict(ev, start=round(start, 3), end=round(start + sec, 3), seconds=round(sec, 2), tempo=round(tempo, 3)))
                prev_end = start + sec
            if prev_end <= group[0]["sec_end"]:
                break
        else:
            die(f"narration for section '{group[0]['section']}' runs {prev_end - group[0]['sec_end']:.1f} s past its end even at tempo 1.35; shorten its lines")
        out += placed
        i = j
    return out


def cues_from(events):
    """One caption cue per narrated line: it covers the speech, stays at least 1.6 s, and gives way to the next line."""
    cues = []
    for i, ev in enumerate(events):
        nxt = events[i + 1]["start"] if i + 1 < len(events) and events[i + 1]["section"] == ev["section"] else ev["sec_end"] + 0.3
        end = min(nxt - 0.05, max(ev["end"] + 0.6, ev["start"] + 1.6))
        cues.append([round(ev["start"], 3), round(max(end, ev["end"]), 3), ev["text"]])
    return cues


def voice_script(D, film, tmp):
    """(segments, scheduled narration events, caption cues). With a voice, every line is synthesised first so its
    caption is timed to the measured speech; a silent cut uses the estimated speaking time."""
    segs, script = film_plan(D, film)
    raw = []
    if synthetic(D):
        voice = D["narration"].split(":", 1)[1]
        for i, ev in enumerate(script):
            path = os.path.join(tmp, f"{film}-n{i:02d}.aiff")
            raw.append(synth(spoken(ev["text"]), path, voice))
            ev["path"] = path
    else:
        raw = [estimate_seconds(ev["text"]) for ev in script]
    events = schedule(script, raw)
    return segs, events, cues_from(events)


def vtt_note(narration):
    return "narration is a synthetic voice" if str(narration or "").startswith("say:") else "silent cut: captions only"


def vtt_render(name, cues, note="narration is a synthetic voice"):
    ts = lambda x: f"{int(x // 3600):02d}:{int(x % 3600 // 60):02d}:{x % 60:06.3f}"
    out = ["WEBVTT", "", f"NOTE {name} captions, built by worldforge/whitepaper/build_whitepaper.py ({note})", ""]
    for i, (a, b, text) in enumerate(cues, 1):
        out += [str(i), f"{ts(a)} --> {ts(b)}", text, ""]
    return "\n".join(out)


# ------------------------------------------------------------------------------------------------ drawing
_img_cache = {}


def fitted(path, box_w, box_h):
    k = (path, box_w, box_h)
    if k not in _img_cache:
        im = Image.open(os.path.join(ROOT, path)).convert("RGB")
        s = min(box_w / im.width, box_h / im.height)
        _img_cache[k] = im.resize((max(1, int(im.width * s)), max(1, int(im.height * s))), Image.LANCZOS)
    return _img_cache[k]


def one_line(text, font, width):
    return clamp_lines(wrap(text, font, width), font, width, 1)[0] if text else ""


def chrome(d, eyebrow, film_label, source=None):
    tracked(d, (56, 40), eyebrow.upper(), F("demi", 13), col(CYAN, 1))
    tracked(d, (W - 56, 40), film_label.upper(), F("demi", 12), col(MUTED, 1), anchor="ra")
    d.text((56, H - 34), UMBRELLA, font=F("demi", 13), fill=col(MUTED, 1))
    if source:
        x = 56 + F("demi", 13).getlength(UMBRELLA) + 14
        d.text((x, H - 33), one_line(f"·  source: {source}", F("regular", 12), W - 56 - x), font=F("regular", 12), fill=col(MUTED, 1))


def bullet_lines(d, x, y, items, width, a, t, color=CYAN, size=18, gap=12, maxl=2, start=0.4, step=0.45):
    f = F("medium", size)
    for i, s in enumerate(items):
        ai = a * ease((t - start - i * step) / 0.5)
        d.ellipse([x, y + 7, x + 8, y + 15], fill=col(color, ai))
        ls = clamp_lines(wrap(s, f, width - 22), f, width - 22, maxl)
        for j, l in enumerate(ls):
            d.text((x + 22, y + j * (size + 6)), l, font=f, fill=col(WHITE, ai * (1 if j == 0 else 0.9)))
        y += len(ls) * (size + 6) + gap
    return y


def paste_kb(img, path, box, t, dur, a):
    """Paste a still into box (x, y, w, h) with a slow zoom (Ken Burns) and alpha a."""
    x, y, w, h = box
    base = fitted(path, int(w * 1.12), int(h * 1.12))
    z = 1.0 + 0.08 * ease(t / max(dur, 0.1))
    cw, ch = int(base.width / z / 1.04), int(base.height / z / 1.04)
    cx, cy = (base.width - cw) // 2, (base.height - ch) // 2
    crop = base.crop((cx, cy, cx + cw, cy + ch))
    s = min(w / crop.width, h / crop.height)
    crop = crop.resize((int(crop.width * s), int(crop.height * s)), Image.BILINEAR)
    ox, oy = x + (w - crop.width) // 2, y + (h - crop.height) // 2
    if a < 1:
        bg = img.crop((ox, oy, ox + crop.width, oy + crop.height)).convert("RGB")
        crop = Image.blend(bg, crop, max(0.0, a))
    img.paste(crop, (ox, oy))
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([ox - 1, oy - 1, ox + crop.width, oy + crop.height], 6, outline=col(CYAN, 0.35 * a), width=1)
    return ox, oy, crop.width, crop.height


def card_title(D, t, dur, film, silent=False):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.8) * ease((dur - t) / 0.5)
    tracked(d, (56, 40), "AGI FUTURE FOUNDATION PBC · SMARTCITI.X", F("demi", 13), col(CYAN, 1))
    lift = 50 if silent else 0
    y = 130 - lift + int(14 * (1 - ease(t / 1.0)))
    d.text((56, y), "SmartCiti.X Agentic Worlds", font=F("bold", 56), fill=col(WHITE, a))
    sub = "Film 1 · Features" if film == "features" else "Film 2 · Roadmap and Stack"
    d.text((56, y + 78), sub, font=F("medium", 30), fill=col((220, 228, 245), a * ease((t - 0.5) / 0.8)))
    d.text((56, y + 128), "Agents operate; people govern.", font=F("medium", 22), fill=col(GOLD, a * ease((t - 0.8) / 0.8)))
    d.line([(56, 380 - lift), (56 + 300 * ease((t - 0.4) / 1.4), 380 - lift)], fill=col(CYAN, a), width=3)
    d.text((56, 398 - lift), UMBRELLA, font=F("demi", 30), fill=col(CYAN, a * ease((t - 1.0) / 0.8)))
    note = (f"Narration: synthetic voice (macOS {D['narration'].split(':', 1)[1]}) · numbers read from registry files on {D['date']}"
            if synthetic(D) else f"Silent cut: captions only · numbers read from registry files on {D['date']}")
    d.text((56, 444 - lift), note, font=F("regular", 15), fill=col(MUTED, a * ease((t - 1.2) / 0.8)))
    return img


def card_network(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, "The world network", "SmartCiti.X · features", "worldforge/out/index.json; worldforge/out/assets/landmarks/index.json")
    d.text((56, 66), "One network, four families", font=F("bold", 34), fill=col(WHITE, a))
    y = 124
    for i, fam in enumerate(D["families"][:4]):
        ai = a * ease((t - 0.5 - i * 0.5) / 0.5)
        d.rounded_rectangle([56, y, 500, y + 58], 10, fill=col(PURPLE, 0.10 * ai), outline=col(PURPLE, 0.45 * ai))
        d.text((74, y + 8), str(fam["count"]), font=F("bold", 34), fill=col(CYAN, ai))
        d.text((140, y + 9), fam["label"], font=fit_font(fam["label"], "demi", 18, 345, 12), fill=col(WHITE, ai))
        d.text((140, y + 33), f"landmark style: {fam['style']}", font=F("regular", 13), fill=col(MUTED, ai))
        y += 68
    tiles = [(str(V(D, "worlds")), "worlds"), (fmt(V(D, "cards")), "Master Cards"), (fmt(V(D, "evals")), f"evals · {V(D, 'failed')} failing"),
             (f"{V(D, 'anchored')}/{V(D, 'worlds')}", "with an RP1 anchor")]
    x = 56
    for i, (n, lab) in enumerate(tiles):
        ai = a * ease((t - 2.8 - i * 0.3) / 0.5)
        d.text((x, 410), n, font=F("bold", 26), fill=col(GOLD, ai))
        d.text((x, 444), lab, font=F("regular", 13), fill=col(MUTED, ai))
        x += 112
    paste_kb(img, "worldforge/out/assets/landmarks/preview.jpg", (540, 80, 364, 384), t, dur, a * ease((t - 0.3) / 0.8))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((722, 474), f"{V(D, 'landmarks')} civic landmarks, one style per family", font=F("regular", 13), fill=col(MUTED, a), anchor="ma")
    return img


def card_avatars(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, "Avatars connected to agents", "SmartCiti.X · features", "worldforge/out/avatars/index.json; worldforge/out/assets/avatars/{index,validation}.json")
    d.text((56, 66), "Avatars bound to agents", font=F("bold", 34), fill=col(WHITE, a))
    paste_kb(img, "worldforge/out/assets/avatars/preview.jpg", (56, 120, 430, 320), t, dur, a * ease((t - 0.2) / 0.7))
    d = ImageDraw.Draw(img, "RGBA")
    items = [f"{V(D, 'avatars.avatars')} avatars: {V(D, 'avatars.specialists')} specialists, {V(D, 'avatars.coordinators')} coordinators, {V(D, 'avatars.advisors')} advisors, {V(D, 'avatars.omegas')} Omegas",
             f"{fmt(V(D, 'bound'))} cards bound to a swarm, a metaprompt and a fabric node",
             f"{V(D, 'avatars.persona_prompts')} persona prompts; {fmt(V(D, 'avatars.prompt_gates'))} prompt gates, {V(D, 'avatars.prompt_gates_failing')} failing",
             f"{V(D, 'avatar_glbs')} role models: {V(D, 'avatar_validated')} validated, {V(D, 'avatar_val_errors')} errors ({D['av_val']['validator']})",
             f"{V(D, 'voiced_intros')} voiced intro lines; every voice is synthetic"]
    bullet_lines(d, 512, 128, items, 392, a, t, color=PINK, size=17, gap=10)
    return img


def card_hive(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, "The Omega Hive", "SmartCiti.X · features", "agents/hive/index.json; agents/hive/dialogues.json")
    d.text((56, 66), "Omega Stewards: defined, not seated", font=F("bold", 32), fill=col(WHITE, a))
    n = V(D, "hive.omegas") or 0
    seated = V(D, "hive.seated")
    cols = 11
    for i in range(n):
        cx, cy = 76 + (i % cols) * 38, 150 + (i // cols) * 44
        ai = a * ease((t - 0.3 - i * 0.03) / 0.4)
        fill = col(CYAN, 0.9 * ai) if i < seated else None
        d.ellipse([cx - 13, cy - 13, cx + 13, cy + 13], outline=col(CYAN, 0.85 * ai), width=2, fill=fill)
    rows = (n + cols - 1) // cols
    d.text((56, 150 + rows * 44), f"{n} rings, {seated} filled: no Omega is seated", font=F("regular", 14), fill=col(MUTED, a))
    sp, ln = V(D, "hive.spoken") or 0, V(D, "hive.lines") or 1
    bx, by = 56, 400
    d.text((bx, by - 26), f"Lines voiced: {sp} of {ln}", font=F("demi", 16), fill=col(WHITE, a))
    d.rounded_rectangle([bx, by, bx + 400, by + 14], 7, outline=col(MUTED, 0.6 * a))
    d.rounded_rectangle([bx, by, bx + int(400 * sp / ln * ease((t - 1) / 1.5)), by + 14], 7, fill=col(GREEN, 0.85 * a))
    items = [f"{V(D, 'hive.voices')} distinct synthetic voices ({D['engine']})",
             f"{fmt(V(D, 'dialogues.answers'))} scripted answers with {fmt(V(D, 'dialogues.citations'))} citations" if "dialogues.answers" in D["N"] else "dialogues not built",
             f"{V(D, 'dialogues.handoffs')} handoffs to another world's Omega" if "dialogues.handoffs" in D["N"] else "",
             "Each Omega says it is synthetic and that people decide"]
    bullet_lines(d, 520, 136, [x for x in items if x], 384, a, t, color=CYAN, size=17, start=1.0)
    return img


def card_gov(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, "Governance", "SmartCiti.X · features", "worlds/PBC.json; worldforge/out/<slug>/cards.json")
    d.text((56, 66), "Agents operate; people govern", font=F("bold", 34), fill=col(WHITE, a))
    d.text((56, 118), f"Held for the Steward Council: {V(D, 'steward_seats')} human seats, 2 signatures decide", font=F("demi", 17), fill=col(GOLD, a))
    y = 154
    for i, act in enumerate(D["pbc"]["reserved_for_humans"]):
        ai = a * ease((t - 0.6 - i * 0.35) / 0.4)
        x = 56 + (i % 2) * 240
        yy = y + (i // 2) * 50
        d.rounded_rectangle([x, yy, x + 226, yy + 38], 19, fill=col(GOLD, 0.12 * ai), outline=col(GOLD, 0.85 * ai))
        d.text((x + 113, yy + 19), act, font=fit_font(act, "demi", 16, 200, 11), fill=col(GOLD, ai), anchor="mm")
    x0 = 560
    for i in range(V(D, "steward_seats")):
        ai = a * ease((t - 2.4 - i * 0.3) / 0.4)
        sx = x0 + i * 112
        d.rounded_rectangle([sx, 160, sx + 90, 240], 10, outline=col((200, 170, 255), 0.9 * ai), width=2)
        d.text((sx + 45, 200), "empty", font=F("demi", 15), fill=col((200, 170, 255), ai), anchor="mm")
    d.text((x0, 252), f"{V(D, 'seats_empty')} of {V(D, 'seats')} human seats empty network-wide", font=F("regular", 14), fill=col(MUTED, a))
    items = [f"{V(D, 'rights')} rights per card: {', '.join(D['rights'])}",
             "agents hold one extra right: operate their own zone",
             "every world's evals check that no agent card holds a reserved right"]
    bullet_lines(d, x0, 290, items, W - 56 - x0, a, t, color=GOLD, size=16, start=3.0)
    return img


def end_claims(D):
    og = open_gates(D)
    return [
        "Not mounted in Sneeze: " + ("; ".join(f"gate {gate_id(k)} {str(v).split(':')[0]}" for k, v in og) if og else "all gates done"),
        f"Nothing deployed or minted on any chain: chain {D['deployment'].get('chain') or 'none'}, {V(D, 'minted')} minted",
        f"{V(D, 'anchored')} of {V(D, 'worlds')} worlds have an RP1 anchor; publishing on RP1 is the founder's call",
        f"Omega Stewards defined, not seated ({V(D, 'hive.seated')} of {V(D, 'hive.omegas')}); human seats empty",
        ("Synthetic voices: narration is macOS " + D["narration"].split(":", 1)[1] + f"; Omega lines are {D['engine'].split(' (')[0]}") if synthetic(D)
        else "Silent cut, captions burned in; Omega voices are synthetic",
        "No revenue, users, customers or partnerships are claimed",
    ]


def card_end(D, t, dur, film):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.4) * ease((dur - t) / 0.6)
    chrome(d, "What this film does not claim", "SmartCiti.X · " + ("features" if film == "features" else "roadmap and stack"),
           "worldforge/out/<slug>/manifest.json; worldforge/out/onchain/index.json; agents/hive/index.json")
    d.text((56, 66), "Plainly", font=F("bold", 38), fill=col(WHITE, a))
    y = 126
    f = F("medium", 18)
    for i, s in enumerate(end_claims(D)):
        ai = a * ease((t - 0.2 - i * 0.3) / 0.4)
        d.rectangle([56, y + 4, 60, y + 22], fill=col(GOLD, ai))
        ls = clamp_lines(wrap(s, f, W - 150), f, W - 150, 2)
        for j, l in enumerate(ls):
            d.text((76, y + j * 24), l, font=f, fill=col(WHITE, ai))
        y += 24 * len(ls) + 13
    d.text((56, y + 12), f"{UMBRELLA} · {ORG}" + (f" · {D['contact']}" if D.get("contact") else ""), font=F("demi", 18), fill=col(CYAN, a))
    return img


def card_stack(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.4) * ease((dur - t) / 0.5)
    layers = stack_layers(D)
    step_d = dur / len(layers)
    k = min(len(layers) - 1, int(t / step_d))
    tt = t - k * step_d
    L = layers[k]
    chrome(d, f"The stack · layer {k + 1} of {len(layers)}", "SmartCiti.X · roadmap and stack", L["source"])
    d.text((56, 66), "The stack", font=F("bold", 34), fill=col(WHITE, a))
    hues = [CYAN, PURPLE, PINK, GREEN, GOLD, (120, 170, 255)]
    bh, gap, x0, x1 = 50, 10, 56, 430
    for i, lay in enumerate(layers):
        if i > k:
            continue
        y = 456 - (i + 1) * bh - i * gap
        ai = a * (ease(tt / 0.6) if i == k else 1.0)
        c = hues[i]
        active = i == k
        d.rounded_rectangle([x0, y, x1, y + bh], 10, fill=col(c, (0.30 if active else 0.10) * ai), outline=col(c, (1.0 if active else 0.45) * ai), width=2 if active else 1)
        d.text((x0 + 16, y + 9), f"{i + 1}", font=F("bold", 22), fill=col(c, ai))
        d.text((x0 + 48, y + 7), lay["name"], font=fit_font(lay["name"], "demi", 18, x1 - x0 - 64, 12), fill=col(WHITE, ai))
        d.text((x0 + 48, y + 29), one_line(lay["sub"], F("regular", 12), x1 - x0 - 64), font=F("regular", 12), fill=col(MUTED, ai))
    px = 470
    ap = a * ease(tt / 0.6)
    tracked(d, (px, 120), f"LAYER {k + 1} · {L['status'].upper()}", F("demi", 12), col(hues[k], ap))
    yy = 142
    for l in clamp_lines(wrap(L["name"], F("bold", 30), W - 56 - px), F("bold", 30), W - 56 - px, 2):
        d.text((px, yy), l, font=F("bold", 30), fill=col(WHITE, ap)); yy += 38
    for l in clamp_lines(wrap(L["sub"], F("medium", 16), W - 56 - px), F("medium", 16), W - 56 - px, 2):
        d.text((px, yy), l, font=F("medium", 16), fill=col(MUTED, ap)); yy += 22
    bullet_lines(d, px, yy + 14, L["facts"], W - 56 - px, a, tt, color=hues[k], size=16, gap=10, maxl=3, start=0.5, step=0.6)
    return img


def card_evidence(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, "Evidence · read from the registries at build time", "SmartCiti.X · roadmap and stack",
           "evidence/heartbeat.log; worldforge/out/index.json; worldforge/out/assets/*/validation.json; worldforge/out/avatars/index.json")
    d.text((56, 66), "Evidence", font=F("bold", 34), fill=col(WHITE, a))
    status = BEAT.match(D["beat"]).group(2) if D["beat"] else "?"
    tiles = [
        (fmt(V(D, "glb_sweep")), "GLBs in the heartbeat sweep", f"{V(D, 'glb_sweep_bad')} with errors or warnings", CYAN),
        (f"{V(D, 'landmark_validated') + V(D, 'avatar_validated')}", "landmark + avatar GLBs", f"{V(D, 'landmark_val_errors') + V(D, 'avatar_val_errors')} errors · {D['lm_val']['validator']}", PURPLE),
        (fmt(V(D, "evals")), "WorldForge evals", f"{V(D, 'failed')} failing · {V(D, 'broken')} broken fixtures each fail their own check", GREEN),
        (fmt(V(D, "avatars.evals")), "avatar registry evals", f"{V(D, 'avatars.failing')} failing", PINK),
        (str(V(D, "onchain_evals")), "onchain-draft checks", f"{V(D, 'onchain_failed')} failing · nothing deployed", GOLD),
        (str(V(D, "beats_total")), "heartbeat beats logged", f"{V(D, 'beats_green')} GREEN · cited beat {D['beat'][:8]} {status}", CYAN),
    ]
    gw, gh = (W - 112 - 40) / 3, 150
    for i, (n, lab, sub, c) in enumerate(tiles):
        x = 56 + (i % 3) * (gw + 20); y = 124 + (i // 3) * (gh + 20)
        ai = a * ease((t - 0.3 - i * 0.25) / 0.5)
        d.rounded_rectangle([x, y, x + gw, y + gh], 14, fill=col(c, 0.08 * ai), outline=col(c, 0.55 * ai))
        kk = ease((t - 0.3 - i * 0.25) / 1.1)
        shown = re.sub(r"\d[\d,]*", lambda m: fmt(int(round(int(m.group().replace(",", "")) * kk))), n)
        d.text((x + 18, y + 14), shown, font=fit_font(n, "bold", 44, gw - 36), fill=col(c, ai))
        d.text((x + 18, y + 74), lab, font=fit_font(lab, "demi", 17, gw - 36, 12), fill=col(WHITE, ai))
        for j, l in enumerate(clamp_lines(wrap(sub, F("regular", 13), gw - 36), F("regular", 13), gw - 36, 2)):
            d.text((x + 18, y + 100 + j * 17), l, font=F("regular", 13), fill=col(MUTED, ai))
    return img


STATUS_C = {"done": GREEN, "now": CYAN, "next": GOLD, "later": (150, 165, 195)}


def card_roadmap(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.4) * ease((dur - t) / 0.5)
    steps = roadmap_steps(D)
    frs = roadmap_frames(D, int(dur * FPS))
    acc, k = 0.0, 0
    for i, fr in enumerate(frs):
        if t < acc + fr / FPS or i == len(frs) - 1:
            k = i; break
        acc += fr / FPS
    tt = t - acc
    phases = phase_steps(D)
    st = steps[k]
    chrome(d, "Roadmap · every open phase has a human gate", "SmartCiti.X · roadmap and stack",
           "atlas/roadmap.json" if st["kind"] == "phase" else "worldforge/out/<slug>/manifest.json#gates")
    d.text((56, 62), "Roadmap", font=F("bold", 32), fill=col(WHITE, a))
    n = len(phases)
    xs = [86 + i * (W - 172) / max(1, n - 1) for i in range(n)]
    ty = 128
    d.line([(xs[0], ty), (xs[-1], ty)], fill=col(MUTED, 0.5 * a), width=2)
    for i, p in enumerate(phases):
        c = STATUS_C.get(p.get("status"), MUTED)
        r = 13 if i == k else 9
        d.ellipse([xs[i] - r, ty - r, xs[i] + r, ty + r], fill=col(c, (1.0 if p.get("status") == "done" else 0.25) * a), outline=col(c, a), width=2)
        d.text((xs[i], ty + 20), p.get("status", ""), font=F("demi", 12), fill=col(c, a), anchor="ma")
    pa = a * ease(tt / 0.5)
    if st["kind"] == "phase":
        p = st["phase"]
        c = STATUS_C.get(p.get("status"), MUTED)
        y = 178
        d.text((56, y), p["name"], font=fit_font(p["name"], "bold", 30, 640), fill=col(WHITE, pa))
        pf = F("demi", 13); pw = pf.getlength(p["status"].upper()) + 22
        d.rounded_rectangle([W - 56 - pw, y + 6, W - 56, y + 30], 12, fill=col(c, 0.18 * pa), outline=col(c, 0.9 * pa))
        d.text((W - 56 - pw / 2, y + 18), p["status"].upper(), font=pf, fill=col(c, pa), anchor="mm")
        yy = bullet_lines(d, 56, y + 48, p.get("items", [])[:4], W - 112, a, tt, color=c, size=16, gap=6, maxl=1, start=0.4, step=0.35)
        gate = p.get("gate", "none named")
        gf = F("medium", 15)
        gl = clamp_lines(wrap("Human gate: " + gate, gf, W - 112 - 28), gf, W - 112 - 28, 3)
        gy = max(yy + 6, 372)
        gy = min(gy, 470 - 24 * len(gl) - 18)
        ga = a * ease((tt - 1.2) / 0.5)
        d.rounded_rectangle([56, gy, W - 56, gy + 18 + 22 * len(gl)], 10, fill=col(GOLD, 0.10 * ga), outline=col(GOLD, 0.8 * ga))
        for j, l in enumerate(gl):
            d.text((70, gy + 9 + j * 22), l, font=gf, fill=col(GOLD, ga))
    else:
        d.text((56, 178), "WorldForge gates: the Sneeze native path", font=F("bold", 26), fill=col(WHITE, pa))
        y = 226
        for i, (g, sv) in enumerate(D["gates"].items()):
            ai = a * ease((tt - 0.3 - i * 0.35) / 0.4)
            sv = str(sv)
            c = GREEN if sv.startswith("done") else (CYAN if sv.startswith("prepared") else GOLD)
            label = sv.split(":")[0]
            pf = F("demi", 12); pw = pf.getlength(label) + 18
            d.rounded_rectangle([56, y, 56 + pw, y + 24], 12, fill=col(c, 0.18 * ai), outline=col(c, 0.9 * ai))
            d.text((56 + pw / 2, y + 12), label, font=pf, fill=col(c, ai), anchor="mm")
            txt = g + (f" — {sv.split(':', 1)[1].strip()}" if ":" in sv else "")
            d.text((56 + pw + 14, y + 3), one_line(txt, F("medium", 16), W - 112 - pw - 14), font=F("medium", 16), fill=col(WHITE, ai))
            y += 40
        d.text((56, y + 8), "Publishing any world on RP1's Earth is the founder's call.", font=F("demi", 16), fill=col(GOLD, a * ease((tt - 2.4) / 0.5)))
    return img


def card_ask(D, t, dur):
    img = background(); d = ImageDraw.Draw(img, "RGBA")
    a = ease(t / 0.5) * ease((dur - t) / 0.5)
    chrome(d, "Next steps", "SmartCiti.X · roadmap and stack", "atlas/roadmap.json (gates of the phases not done)")
    d.text((56, 66), "Next steps are human decisions", font=F("bold", 32), fill=col(WHITE, a))
    items = [f"{p['name']}: {p.get('gate', '')}" for p in phase_steps(D) if p.get("status") != "done"]
    y = bullet_lines(d, 56, 124, items, W - 112, a, t, color=GOLD, size=15, gap=6, maxl=2, start=0.3, step=0.4)
    d.text((56, max(y + 8, 440)), f"Questions and review: {D['contact']}" if D.get("contact") else f"Questions and review: {ORG}", font=F("demi", 18), fill=col(CYAN, a))
    return img


CARDS = {"features": {"title": None, "network": card_network, "avatars": card_avatars, "hive": card_hive, "gov": card_gov, "end": None},
         "roadmap-stack": {"title": None, "stack": card_stack, "evidence": card_evidence, "roadmap": card_roadmap, "ask": card_ask, "end": None}}


def draw_card(D, film, name, t, dur, silent=False):
    if name == "title":
        return card_title(D, t, dur, film, silent=silent)
    if name == "end":
        return card_end(D, t, dur, film)
    return CARDS[film][name](D, t, dur)


def lower_third(D, slug, title, desc, k, n):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img, "RGBA")
    for y in range(370, H):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(min(1.0, (y - 370) / 70) * 225)))
    for y in range(0, 80):
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(130 * (1 - y / 80))))
    tracked(d, (40, 22), "SMARTCITI.X · WORLD WALKTHROUGH · RECORDED IN THE WORLDFORGE VIEWER", F("demi", 12), (255, 255, 255, 220))
    d.text((W - 40, 22), f"{k}/{n}", font=F("demi", 13), fill=(255, 255, 255, 200), anchor="ra")
    f = D["feat"][slug]
    hue = (f["brand"] or {}).get("hue")
    accent = hue_rgb(hue) if hue is not None else CYAN
    mark = (f["brand"] or {}).get("mark") or ""
    x = 40
    if mark:
        d.rounded_rectangle([x, 452, x + 54, 506], 10, fill=accent + (235,))
        mk = re.sub(r"[^A-Za-z0-9]", "", mark)[:3] or mark   # the brand mark, minus stray punctuation (e.g. "MD(")
        d.text((x + 27, 479), mk, font=fit_font(mk, "bold", 22, 46, 10), fill=(10, 12, 24, 255), anchor="mm")
        x += 70
    head = f"{f['name']}  ·  {title}"
    d.text((x, 450), head, font=fit_font(head, "bold", 26, W - x - 40, 16), fill=(255, 255, 255, 255), stroke_width=1, stroke_fill=(0, 0, 0, 160))
    light = tuple(int(c + (255 - c) * 0.45) for c in accent)
    d.text((x, 486), desc, font=fit_font(desc, "medium", 17, W - x - 40, 12), fill=light + (255,), stroke_width=2, stroke_fill=(0, 0, 0, 230))
    return img


# ------------------------------------------------------------------------------------------------ film render
def pipe_frames(path, nframes, frame_at, dup=2):
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


def render_film(D, film, tmp, segs, events):
    secs = FILMS[film]["sections"]
    silent = not synthetic(D)
    starts, acc = {}, 0
    for name, dur in secs:
        starts[name] = acc; acc += dur
    cues = cues_from(events)

    def caption_at(name, t_abs):
        """The burned-in caption of a silent cut: the latest line of this section that has started."""
        cur = None
        for (a, b, text), ev in zip(cues, events):
            if ev["section"] == name and a <= t_abs + 1e-6:
                cur = text
        return cur

    files = []
    items_n = sum(1 for s in segs if s["kind"] == "clip")
    k = 0
    for i, s in enumerate(segs):
        out = os.path.join(tmp, f"{film}-seg{i:02d}.mp4")
        if s["kind"] == "card":
            dur = dict(secs)[s["section"]]
            def frame_at(j, dur=dur, name=s["section"]):
                t = (j - j % 2) / FPS
                img = draw_card(D, film, name, t, dur, silent=silent)
                if silent:
                    text = caption_at(name, starts[name] + t)
                    if text:
                        caption_strip(img, text)
                return img
            pipe_frames(out, s["frames"], frame_at, dup=2)
        else:
            k += 1
            lt = lower_third(D, s["slug"], s["title"], s["desc"], k, items_n)
            lt_path = os.path.join(tmp, f"{film}-lt{i:02d}.png"); lt.save(lt_path)
            d = s["frames"] / FPS
            src = os.path.join(ROOT, s["src"])
            L = duration(src) or d
            stretch = max(0.5, min(3.0, d / L))
            fc = (f"[0:v]setpts={stretch:.5f}*PTS,fps={FPS},scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2,"
                  f"tpad=stop_mode=clone:stop_duration={d:.3f}[c];[c][1:v]overlay=0:0,fade=t=in:st=0:d=0.3,fade=t=out:st={d - 0.3:.3f}:d=0.3,{TAIL}[v]")
            ff(["-i", src, "-loop", "1", "-framerate", str(FPS), "-i", lt_path, "-filter_complex", fc, "-map", "[v]", "-frames:v", str(s["frames"]), "-an"] + X264 + [out])
        files.append(out)
    lst = os.path.join(tmp, f"{film}-list.txt")
    with open(lst, "w") as f:
        f.writelines(f"file '{p}'\n" for p in files)
    video = os.path.join(tmp, f"{film}-video.mp4")
    ff(["-f", "concat", "-safe", "0", "-i", lst, "-c", "copy", "-movflags", "+faststart", video])
    dst = os.path.join(OUT, FILMS[film]["file"])
    lines = [{"section": ev["section"], "text": ev["text"], "start": ev["start"], "end": ev["end"], "seconds": ev["seconds"], "tempo": ev["tempo"]} for ev in events]
    if silent:
        shutil.copyfile(video, dst)
        return {"narration": "silent", "lines": lines}
    inputs, filters, labels = [], [], []
    for j, ev in enumerate(events):
        inputs += ["-i", ev["path"]]
        filters.append(f"[{j + 1}:a]aresample=48000,aformat=channel_layouts=mono" + (f",atempo={ev['tempo']:.3f}" if ev["tempo"] > 1.0 else "")
                       + f",adelay={int(round(ev['start'] * 1000))}:all=1[a{j}]")
        labels.append(f"[a{j}]")
    fc = ";".join(filters) + f";{''.join(labels)}amix=inputs={len(labels)}:normalize=0:dropout_transition=0,apad=whole_dur={TOTAL_S},atrim=0:{TOTAL_S}[a]"
    ff(["-i", video] + inputs + ["-filter_complex", fc, "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "128k", "-t", str(TOTAL_S), "-movflags", "+faststart", dst])
    return {"narration": D["narration"], "lines": lines}


# ------------------------------------------------------------------------------------------------ media
ALT = {
    "worldforge/out/stills/console.jpg": "The WorldForge team console: a dark dashboard with network totals across the top, a list of worlds on the left and the Locator.X card with its counts and Master Card tree",
    "worldforge/out/stills/viewer-building.jpg": "A generated building in the WorldForge viewer: a dark shell signed Master Dashboard, its glass front showing the fitted interior, with planters on a paved forecourt at dusk",
    "worldforge/out/stills/viewer-council.jpg": "Inside the Steward Council hall: three purple chairs labelled as empty human seats, with a long table and timber screens",
    "worldforge/out/stills/viewer-flyin.jpg": "Fly-in view of a world: a round plaza with a green ring and a world sign in front of a tall dark landmark tower, roads and buildings beyond, dusk sky",
    "worldforge/out/stills/viewer-landmark.jpg": "A civic landmark tower seen from the air: a tall dark shaft with glowing rings and a needle spire above a wooded plain",
    "worldforge/out/stills/viewer-omega.jpg": "An Omega Steward figure in dark green with a halo, labelled defined, not seated, synthetic voice, standing beside a building",
    "worldforge/out/stills/viewer-orbit.jpg": "Orbit view of a whole world: a central plaza and landmark tower with roads radiating to zone buildings on a green plain",
    "worldforge/out/assets/avatars/preview.jpg": "Six white avatar role models in front and back views: specialist, coordinator, Omega with halo, host, liaison and alignment",
    "worldforge/out/assets/landmarks/preview.jpg": "Contact sheet of the 41 civic landmark towers in four rows, each tinted in its world's brand colour",
    "worldforge/review/out/media/plan-cancer-dao.png": "Plan view of Cancer DAO drawn from its generated blockout: plaza at the centre, five zones in a ring, the gate to the south and the Steward Council to the north",
    "worldforge/review/out/media/plan-locator-x.png": "Plan view of Locator.X drawn from its generated blockout: plaza, zones in a ring, gate south, Steward Council north",
    "pitch/media/teams-console.jpg": "The teams console: a grid of team cards with their worlds and seats",
}


def media_name(path):
    base = os.path.splitext(os.path.basename(path))[0]
    if path.endswith(".mp4"):
        return f"frame-{base}.jpg"
    if "/stills/" in path:
        return f"still-{base}.jpg"
    if "/assets/avatars/" in path:
        return "avatars-preview.jpg"
    if "/assets/landmarks/" in path:
        return "landmarks-preview.jpg"
    return f"{base}.jpg"


def jpg_resized(path, maxw=1280, q=82):
    im = Image.open(os.path.join(ROOT, path)).convert("RGB")
    if im.width > maxw:
        im = im.resize((maxw, int(im.height * maxw / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, "JPEG", quality=q, optimize=True)
    return b.getvalue(), im.size


VIS = re.compile(r"((?:worldforge|pitch|my-fabric|agents)/[\w./-]+\.(?:jpg|png|mp4))")


def section_visual(sec):
    """(media name, source path, alt, kind) for an explainer section's visual_hint, or None (then a drawn diagram)."""
    for p in VIS.findall(sec.get("visual_hint", "")):
        if not os.path.exists(os.path.join(ROOT, p)):
            continue
        if p.endswith(".mp4") and "/clips/" not in p:
            continue
        if p.endswith(".mp4"):
            stem = os.path.splitext(os.path.basename(p))[0]
            slug = next((s for s in sorted(WORLD_NAMES, key=len, reverse=True) if stem.startswith(s + "-")), None)
            mode = stem[len(slug) + 1:] if slug else stem
            alt = f"Frame from the recorded {MODE_LABEL.get(mode, mode).lower()} clip of {WORLD_NAMES.get(slug, stem)} in the WorldForge viewer"
            return media_name(p), p, alt, "frame"
        return media_name(p), p, ALT.get(p, f"Still from {p}"), "copy"
    return None


WORLD_NAMES = {}


def media_plan(D):
    """name -> ('gen', fn) | ('copy', src) | ('frame', clip, seconds)."""
    m = {}
    for film in FILMS:
        m[os.path.basename(FILMS[film]["poster"])] = ("gen", (lambda f: (lambda: jpg_poster(D, f)))(film))
    for p in ["worldforge/out/stills/viewer-orbit.jpg", "worldforge/out/stills/viewer-council.jpg", "worldforge/out/stills/console.jpg",
              "worldforge/out/assets/avatars/preview.jpg", "worldforge/out/assets/landmarks/preview.jpg", "worldforge/out/stills/viewer-omega.jpg",
              "worldforge/out/stills/viewer-flyin.jpg", "worldforge/out/stills/viewer-building.jpg", "worldforge/out/stills/viewer-landmark.jpg"]:
        if os.path.exists(os.path.join(ROOT, p)):
            m[media_name(p)] = ("copy", p)
    for doc in D["explainers"]:
        for sec in doc["sections"]:
            v = section_visual(sec)
            if v:
                name, p, _, kind = v
                m[name] = ("frame", p, 2.5) if kind == "frame" else ("copy", p)
    return m


def jpg_poster(D, film):
    img = card_title(D, 4.0, 6, film)
    d = ImageDraw.Draw(img, "RGBA")
    d.rounded_rectangle([W - 56 - 64, H - 56 - 64, W - 56, H - 56], 32, fill=(255, 255, 255, 40), outline=(255, 255, 255, 200), width=2)
    cx, cy = W - 56 - 32, H - 56 - 32
    d.polygon([(cx - 9, cy - 14), (cx - 9, cy + 14), (cx + 15, cy)], fill=(255, 255, 255, 230))
    d.text((W - 56 - 80, H - 56 - 32), "2:00", font=F("demi", 18), fill=col(WHITE, 0.9), anchor="rm")
    b = io.BytesIO(); img.convert("RGB").save(b, "JPEG", quality=86); return b.getvalue()


def write_media(D, check=False):
    os.makedirs(MEDIA, exist_ok=True)
    problems = []
    for name, spec in media_plan(D).items():
        dst = os.path.join(MEDIA, name)
        if spec[0] == "gen":
            data = spec[1]()
        elif spec[0] == "copy":
            data = jpg_resized(spec[1])[0]
        else:
            if check:
                if not os.path.exists(dst):
                    problems.append(f"media/{name} missing")
            else:
                ff(["-ss", f"{spec[2]:.2f}", "-i", os.path.join(ROOT, spec[1]), "-frames:v", "1", "-q:v", "3", dst])
            continue
        if check:
            if not os.path.exists(dst) or open(dst, "rb").read() != data:
                problems.append(f"media/{name} differs")
        elif not os.path.exists(dst) or open(dst, "rb").read() != data:
            open(dst, "wb").write(data)
    if not check:
        keep = set(media_plan(D))
        for f in os.listdir(MEDIA):
            if f not in keep:
                os.remove(os.path.join(MEDIA, f))
    return problems


# ------------------------------------------------------------------------------------------------ page
def e(s):
    return html.escape(str(s), quote=True)


def cite(D, text):
    """Escape text, then turn [claim-id] into a footnote link [n] and {pbc.*} tokens into PBC.json values."""
    pbc = D["pbc"]
    mission = pbc["mission"]
    toks = {
        "pbc.mission_lc": e(mission[0].lower() + mission[1:]),
        "pbc.agents_handle": e(and_list(pbc["management_style"]["agents_handle"])),
        "pbc.humans_hold": e(and_list(pbc["management_style"]["humans_hold"])),
        "pbc.reserved": and_list(f"<code>{e(a)}</code>" for a in pbc["reserved_for_humans"]),
        "pbc.seats": e(pbc["steward_seats"]),
    }
    out = e(text)
    out = re.sub(r"\{(pbc\.[a-z_]+)\}", lambda m: toks[m.group(1)], out)
    return re.sub(r"\[([a-z0-9-]+)\]", lambda m: f'<sup class="fn"><a href="#src-{D["fn"][m.group(1)]}" aria-label="Source {D["fn"][m.group(1)]}">[{D["fn"][m.group(1)]}]</a></sup>', out)


def src_tag(s):
    return f'<span class="src">source: {e(s)}</span>'


def stat(num, label, source, tone=""):
    return (f'<div class="stat {tone}"><span class="num">{e(num)}</span><span class="lab">{e(label)}</span>'
            f'<span class="src">{e(source)}</span></div>')


def img_size(src):
    """width and height attributes read from the written media file (no layout shift while lazy images load)."""
    p = os.path.join(OUT, src)
    if not os.path.exists(p):
        return ""
    with Image.open(p) as im:
        return f' width="{im.width}" height="{im.height}"'


def fig(src, alt, cap, cls=""):
    return (f'<figure class="{cls}"><img src="{e(src)}" alt="{e(alt)}"{img_size(src)} loading="lazy" decoding="async">'
            f'<figcaption>{cap}</figcaption></figure>')


def ul(items, cls=""):
    return f'<ul class="{cls}">' + "".join(f"<li>{x}</li>" for x in items) + "</ul>"


def diagram_tiers(D):
    tiers = D["pbc"]["structure"]
    h = 70 * len(tiers) + 20
    rows = []
    for i, tr in enumerate(tiers):
        y = 10 + i * 70
        w = 600 - i * 60
        x = (640 - w) / 2
        rows.append(f'<rect x="{x}" y="{y}" width="{w}" height="58" rx="10" class="d-box d-{i}"/>'
                    f'<text x="320" y="{y + 24}" class="d-t" text-anchor="middle">{e(tr["tier"])}</text>'
                    f'<text x="320" y="{y + 44}" class="d-s" text-anchor="middle">{e(tr["what"][:78])}</text>')
    return (f'<figure class="diagram"><svg viewBox="0 0 640 {h}" role="img" aria-labelledby="dt-t"><title id="dt-t">Three tiers from worlds/PBC.json: '
            + e("; ".join(f"{t['tier']}: {t['what']}" for t in tiers)) + "</title>" + "".join(rows) +
            '</svg><figcaption>Structure as described in <code>worlds/PBC.json#structure</code>. Entity status is set by the filings, not by this page.</figcaption></figure>')


def diagram_chain(D):
    n = V(D, "ledger_entries") if "ledger_entries" in D["N"] else 0
    boxes = []
    labels = ["genesis", "register", "register", "…", f"entry {n}"]
    for i, lab in enumerate(labels):
        x = 12 + i * 126
        boxes.append(f'<rect x="{x}" y="20" width="104" height="54" rx="8" class="d-box d-1"/><text x="{x + 52}" y="44" class="d-t" text-anchor="middle">{e(lab)}</text>'
                     f'<text x="{x + 52}" y="62" class="d-s" text-anchor="middle">{"prev → hash" if i else "first hash"}</text>')
        if i < len(labels) - 1:
            boxes.append(f'<path d="M{x + 106} 47 L{x + 124} 47" class="d-line" marker-end="url(#arr)"/>')
    boxes.append('<text x="320" y="104" class="d-s" text-anchor="middle">each registration carries two steward approvals (2 of 3), signed with test keys today</text>')
    return ('<figure class="diagram"><svg viewBox="0 0 640 120" role="img" aria-labelledby="dc-t"><title id="dc-t">The agent ledger as a hash chain: '
            f'genesis, then {n} entries in all, each linked to the previous hash and carrying two steward approvals</title>'
            '<defs><marker id="arr" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10z" class="d-arrow"/></marker></defs>'
            + "".join(boxes) + '</svg><figcaption>Drawn from the shape of <code>agents/ledger/ledger.jsonl</code>; '
            f'{n} lines when this page was built.</figcaption></figure>')


def diagram_x402(D):
    steps = ["request", "402: price, payTo null", "signed payload", "budget check"]
    ends = ["held", "would settle", "refused"]
    parts = []
    for i, s in enumerate(steps):
        x = 10 + i * 156
        parts.append(f'<rect x="{x}" y="14" width="140" height="46" rx="8" class="d-box d-1"/><text x="{x + 70}" y="42" class="d-t" text-anchor="middle">{e(s)}</text>')
        if i < len(steps) - 1:
            parts.append(f'<path d="M{x + 142} 37 L{x + 154} 37" class="d-line" marker-end="url(#arr2)"/>')
    for i, s in enumerate(ends):
        x = 120 + i * 140
        parts.append(f'<rect x="{x}" y="96" width="120" height="40" rx="20" class="d-box d-2"/><text x="{x + 60}" y="121" class="d-t" text-anchor="middle">{e(s)}</text>')
        parts.append(f'<path d="M550 60 L{x + 60} 94" class="d-line" marker-end="url(#arr2)"/>')
    return ('<figure class="diagram"><svg viewBox="0 0 640 146" role="img" aria-labelledby="dx-t"><title id="dx-t">x402 rehearsal flow: request, a payment-required reply with no payee, '
            'a signed payload and a budget check, ending held, would settle or refused. Nothing settles.</title>'
            '<defs><marker id="arr2" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="6" markerHeight="6" orient="auto"><path d="M0 0 L10 5 L0 10z" class="d-arrow"/></marker></defs>'
            + "".join(parts) + '</svg><figcaption>The rehearsal flow described in <code>agents/x402/*.json</code>. No payment rail is connected; nothing settles.</figcaption></figure>')


def diagram_beat(D):
    f = D["beat_fields"]
    keep = ["GLB", "SWARMS", "PROMPTS", "LEDGER", "HIVE", "WORLDFORGE", "DIALOGUES"]
    rows = "".join(f"<div><b>{e(k)}</b> {e(f[k])}</div>" for k in keep if k in f)
    st = BEAT.match(D["beat"]).group(2) if D["beat"] else "?"
    return (f'<figure class="beat"><div class="beatbox" role="img" aria-label="Excerpt of the heartbeat beat at {e(D["beat"][:8])}, status {st}">'
            f'<div class="beathead">{e(D["beat"][:8])} <span class="pill {"ok" if st == "GREEN" else "warn"}">{st}</span></div>{rows}</div>'
            f'<figcaption>Excerpt of the beat this page cites, from <code>evidence/heartbeat.log</code> (pinned when the page was built).</figcaption></figure>')


DIAGRAMS = {"pbc-structure": diagram_tiers, "ledger-and-keyring": diagram_chain, "x402-rehearsal": diagram_x402, "heartbeat-and-evals": diagram_beat}


def facts_table(sec):
    rows = []
    for fct in sec.get("facts", []):
        c = fct.get("_check") or {}
        stc = c.get("status", "unchecked")
        src = fct["source"]
        if stc == "verified":
            badge = '<span class="pill ok" title="re-read from the registry when this page was built">re-read</span>'
        elif stc == "drift":
            badge = f'<span class="pill warn" title="the registry now reads {e(fmt(c["current"]))}">now {e(fmt(c["current"]))}</span>'
        elif stc == "rebuilt":
            badge = '<span class="pill ok" title="written from the registry when this page was built">from registry</span>'
            src = f"{c['pointer']} (written from the registry when this page was built)"
        else:
            badge = '<span class="pill muted" title="read by the explainer agent from the named source; not machine-checked by this build">as read</span>'
        if stc in ("verified", "drift") and c.get("pointer") and c["pointer"].split("#")[0].split(" ")[0] not in src:
            src = f"{src} (checked against {c['pointer']})"
        note = FACT_NOTE.get((sec.get("id"), fct["label"]))
        val = e(fct["value"]) + (f' <span class="muted">({e(note)})</span>' if note else "")
        rows.append(f"<tr><th scope=\"row\">{e(fct['label'])}</th><td data-label=\"Value\">{val} {badge}</td><td data-label=\"Source\" class=\"srccell\">{e(src)}</td></tr>")
    return ('<div class="tablewrap"><table class="facts rs"><caption class="sr">Facts for this section, each with its source</caption>'
            '<thead><tr><th scope="col">Fact</th><th scope="col">Value</th><th scope="col">Source</th></tr></thead><tbody>' + "".join(rows) + "</tbody></table></div>")


def explainer_section(D, sec):
    vis = section_visual(sec)
    wide = sec["id"] in DIAGRAMS
    if wide:
        visual = hscroll(DIAGRAMS[sec["id"]](D))
    elif vis:
        name, p, alt, kind = vis
        visual = fig(f"media/{name}", alt, f"Visual: <code>{e(p)}</code>" + (" (a frame of the recorded clip)" if kind == "frame" else ""))
    else:
        visual = ""
    drift = [f for f in sec.get("facts", []) if (f.get("_check") or {}).get("status") == "drift"]
    dnote = ""
    if drift:
        dnote = ('<p class="drift"><b>Moved since this explainer was written:</b> ' + "; ".join(
            f"{e(f['label'])}: the text says {e(f['value'])}, <code>{e(f['_check']['pointer'])}</code> now reads <b>{e(fmt(f['_check']['current']))}</b>" for f in drift)
            + ". The prose below keeps the explainer's wording; the registry value is the current one.</p>")
    if sec.get("_rebuilt_text") or any((f.get("_check") or {}).get("status") == "rebuilt" for f in sec.get("facts", [])):
        dnote += ('<p class="drift"><b>Counts written from the registries when this page was built:</b> the voicing and beat counts in this section '
                  f'are read from <code>{e(VOICE_SRC)}</code> and <code>evidence/heartbeat.log</code>, not from the explainer text; the explainer\'s '
                  'earlier wording is kept in <code>worldforge/whitepaper/out/build.json</code> under <code>rebuilt</code>.</p>')
    paras = "".join(f"<p>{e(p)}</p>" for p in sec.get("paragraphs", []))
    bullets = ul([e(b) for b in sec["bullets"]]) if sec.get("bullets") else ""
    nd = ul([e(x) for x in sec.get("not_done", [])], "notdone")
    return (f'<article class="explainer" id="x-{e(sec["id"])}"><h3>{e(sec["title"])}</h3><p class="dek">{e(sec.get("dek", ""))}</p>'
            f'<div class="xgrid{" wide" if wide else ""}"><div class="xtext">{dnote}{paras}{bullets}</div><div class="xside">{visual}</div></div>'
            f'<h4>Facts</h4>{facts_table(sec)}<h4>Not done yet</h4>{nd}</article>')


def hscroll(markup):
    """On a phone, a 640-unit diagram scaled to the screen would draw 7 px labels: below 640 px it keeps its full width
    inside a box that scrolls sideways (focusable, so a keyboard can scroll it too)."""
    if "<svg" not in markup:
        return markup
    m = re.search(r'<title id="[^"]+">([^<]{0,90})', markup)
    label = e(html.unescape(m.group(1)).split(":")[0] if m else "Diagram") + " (scrolls sideways on narrow screens)"
    return (markup.replace("<svg", f'<div class="hscroll" tabindex="0" role="region" aria-label="{label}"><svg', 1)
            .replace("</svg>", '</svg></div><p class="swipe">Scroll sideways to read the whole diagram.</p>', 1))


def qual_note(D, part):
    qs = [q for q in D.get("qualified", []) if part in q["where"]]
    if not qs:
        return ""
    return ('<p class="muted qual">Qualified on this page: ' + "; ".join(f"<code>{e(q['where'])}</code> reads “{e(q['source'])}”" for q in qs)
            + ". The page words these lines to match the records (no agent or steward is seated; steward approvals are signed with test keys; "
            "not every fabric has been loaded in Artemis). The roadmap file belongs to its owner; the source wording is flagged for them.</p>")


def stack_svg(D):
    layers = stack_layers(D)
    n = len(layers)
    bh, gap = 74, 12
    h = n * (bh + gap) + 10
    parts = []
    for i, L in enumerate(layers):
        y = 10 + (n - 1 - i) * (bh + gap)
        parts.append(f'<g class="lay lay-{i}"><rect x="8" y="{y}" width="624" height="{bh}" rx="12"/>'
                     f'<text x="30" y="{y + 32}" class="ln">{i + 1}</text>'
                     f'<text x="64" y="{y + 31}" class="lt">{e(L["name"])}</text>'
                     f'<text x="64" y="{y + 55}" class="ls">{e(L["sub"][:64])}</text>'
                     f'<text x="616" y="{y + 31}" class="lst" text-anchor="end">{e(L["status"])}</text></g>')
    title = "The SmartCiti.X stack, bottom to top: " + "; ".join(f"{L['name']} ({L['status']})" for L in layers)
    return (f'<svg class="stacksvg" viewBox="0 0 640 {h}" role="img" aria-labelledby="stk-t"><title id="stk-t">{e(title)}</title>' + "".join(parts) + "</svg>")


def _words(t):
    return {w for w in re.findall(r"[a-z0-9]+", t.lower()) if w not in {"the", "a", "an", "of", "or", "and", "any", "these", "is", "are", "do", "does", "has", "have", "this", "in", "on"}}


def drift_map(D):
    """{'1,025': (1066, pointer), ...}: the first number of every explainer fact whose registry value has moved."""
    out = {}
    for doc in D["explainers"]:
        for s in doc["sections"]:
            for f in s.get("facts", []):
                c = f.get("_check") or {}
                if c.get("status") == "drift":
                    m = NUM.search(str(f["value"]))
                    old = m.group().rstrip(",") if m else ""
                    if len(old) >= 3:
                        out[old] = (c["current"], c["pointer"])
    return out


def faq_items(D):
    """The explainers' FAQ, near-duplicate questions merged (first kept). An answer quoting a number that has moved
    since the explainer was written gets the registry's current value appended."""
    out, seen = [], []
    for doc in D["explainers"]:
        for q in doc.get("faq", []):
            w = _words(q["q"])
            if any(len(w & x) / max(1, len(w | x)) >= 0.6 for x in seen):
                continue
            seen.append(w)
            q = dict(q)
            if q.pop("_rebuilt", False):
                q["a"] = q["a"].rstrip() + " (Counts read from the voice manifest, the avatar registry and the hive registries when this page was built.)"
            out.append(q)
    out.append({"q": "Do the market figures on this page show demand for SmartCiti.X?",
                "a": "No. They are forecasts and survey results about adjacent markets, cited with their publishers and dates. "
                     "AGI Future Foundation PBC and SmartCiti.X have no revenue, users, customers or partnerships to report."})
    dm = drift_map(D)
    for q in out:
        notes = [f"{old} is now {fmt(cur)} ({ptr})" for old, (cur, ptr) in dm.items() if re.search(rf"(?<![\d,]){re.escape(old)}(?![\d,])", q["q"] + " " + q["a"])]
        if notes:
            q["a"] = q["a"].rstrip() + " [Registry update since this answer was written: " + "; ".join(notes) + ".]"
    return out


def glossary_items(D):
    seen, out = set(), []
    for doc in D["explainers"]:
        for g in doc.get("glossary", []):
            k = re.sub(r"\s*\(.*?\)", "", g["term"]).strip().lower()
            k = re.sub(r"s$", "", k)
            if k not in seen:
                seen.add(k); out.append(g)
    return sorted(out, key=lambda g: g["term"].lower().lstrip("-"))


def seo(D):
    t = D["N"]
    desc = (f"Agent-managed, human-governed virtual worlds by {ORG}: {V(D, 'worlds')} worlds, {fmt(V(D, 'cards'))} Master Cards, "
            f"numbers read from registries. Nothing deployed.")
    if len(desc) > 155:
        desc = f"Agent-managed, human-governed virtual worlds by {ORG}. Every number read from a registry. Nothing deployed or minted."
    keywords = ["agentic AI", "AI agents", "virtual worlds", "AI governance", "human-in-the-loop", "agent-managed DAO", "digital twins",
                "smart cities", "spatial computing", "glTF 2.0", "RP1 spatial fabrics", "Omega Stewards", "SmartCiti.X", ORG]
    longtail = ["how to govern AI agents in virtual worlds", "agent-managed human-governed DAO", "AI agents with actions reserved for humans",
                "2-of-3 steward council for AI governance", "Khronos-validated glTF virtual world pipeline", "synthetic voice disclosure for AI avatars",
                "onchain-ready ERC-721 metadata not deployed", "virtual world whitepaper with sourced numbers"]
    og_title = "SmartCiti.X Agentic Worlds: agents operate, people govern"
    og_desc = (f"{V(D, 'worlds')} coming-soon virtual worlds where agents do operational work and a 2-of-3 human Steward Council holds "
               f"{V(D, 'reserved_actions')} decisions. Every number read from a registry file.")
    posts = [
        (f"We wrote up how SmartCiti.X works: {V(D, 'worlds')} coming-soon virtual worlds where agents do operational work and people keep "
         f"{V(D, 'reserved_actions')} decisions (final vote, charter, treasury, enactment, windfall, steward appointment) for a 2-of-3 human council. "
         "Every number in the whitepaper is read from a registry file. Nothing is deployed, minted or live yet."),
        (f"SmartCiti.X whitepaper: {V(D, 'worlds')} agent-managed, human-governed virtual worlds. {fmt(V(D, 'cards'))} Master Cards, "
         f"{fmt(V(D, 'evals'))} evals, {V(D, 'failed')} failing. Agents operate; people govern. Not deployed, not minted, not live, and we say so."),
        ("Two 2-minute films: the features, and the roadmap and stack. The narration is a synthetic voice and is labelled as one. "
         f"The {V(D, 'hive.omegas')} Omega Stewards are defined, not seated."),
    ]
    assert len(TITLE) <= 60 and len(desc) <= 155 and len(posts[1]) <= 280, (len(TITLE), len(desc), len(posts[1]))
    return {"title": TITLE, "description": desc, "keywords": keywords, "longtail": longtail, "slug": SLUG,
            "og_title": og_title, "og_description": og_desc, "posts": posts}


SECTIONS_NAV = [("film-features", "Features film"), ("why", "Why"), ("what", "What"), ("how", "How"), ("explainers", "Explainers"),
                ("film-roadmap", "Roadmap film"), ("stack", "Stack"), ("roadmap", "Roadmap"), ("market", "Market"),
                ("not-claimed", "Not claimed"), ("faq", "FAQ"), ("glossary", "Glossary"), ("sources", "Sources"), ("share-kit", "Share kit")]

CSS = r"""
:root{--bg:#060918;--bg2:#100e2c;--panel:#111733;--panel2:#161d3f;--ink:#eef2ff;--muted:#9aa6c4;--line:#273058;
--accent:#00e6e6;--accent2:#8c50ff;--gold:#ffbe28;--green:#28e696;--pink:#ff468c;--code:#1a2148;--shadow:0 10px 30px rgba(0,0,0,.35);color-scheme:dark}
@media (prefers-color-scheme: light){:root:not([data-theme="dark"]){--bg:#f6f7fb;--bg2:#eceefa;--panel:#ffffff;--panel2:#f2f4fb;--ink:#121633;--muted:#525c7a;--line:#d6dbea;
--accent:#006a70;--accent2:#5b2fd6;--gold:#805200;--green:#0b6a44;--pink:#b4235e;--code:#eef0f8;--shadow:0 6px 20px rgba(20,30,80,.08);color-scheme:light}}
:root[data-theme="light"]{--bg:#f6f7fb;--bg2:#eceefa;--panel:#ffffff;--panel2:#f2f4fb;--ink:#121633;--muted:#525c7a;--line:#d6dbea;
--accent:#006a70;--accent2:#5b2fd6;--gold:#805200;--green:#0b6a44;--pink:#b4235e;--code:#eef0f8;--shadow:0 6px 20px rgba(20,30,80,.08);color-scheme:light}
*{box-sizing:border-box}html{scroll-behavior:smooth;scroll-padding-top:64px}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.62 -apple-system,BlinkMacSystemFont,"Avenir Next","Segoe UI",Inter,Roboto,Helvetica,Arial,sans-serif;overflow-x:hidden}
a{color:var(--accent)}a:focus-visible,button:focus-visible,summary:focus-visible,video:focus-visible{outline:3px solid var(--gold);outline-offset:2px;border-radius:4px}
code{font:0.86em ui-monospace,SFMono-Regular,Menlo,monospace;background:var(--code);padding:1px 5px;border-radius:5px;overflow-wrap:anywhere}
.skip{position:absolute;left:-999px;top:8px;background:var(--gold);color:#000;padding:8px 12px;border-radius:6px;z-index:20}.skip:focus{left:8px}
.sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}
header.top{position:sticky;top:0;z-index:10;background:color-mix(in srgb,var(--bg) 88%,transparent);backdrop-filter:blur(8px);border-bottom:1px solid var(--line)}
.topin{max-width:1180px;margin:0 auto;padding:8px 16px;display:flex;gap:12px;align-items:center}
.brand{font-weight:700;white-space:nowrap;color:var(--ink);text-decoration:none}.brand span{color:var(--accent)}
nav.toc{flex:1;min-width:0;overflow-x:auto;scrollbar-width:none}nav.toc::-webkit-scrollbar{display:none}
nav.toc.more{-webkit-mask-image:linear-gradient(to right,#000 calc(100% - 56px),transparent);mask-image:linear-gradient(to right,#000 calc(100% - 56px),transparent)}
nav.toc ul{display:flex;gap:4px;list-style:none;margin:0;padding:0}nav.toc a{display:block;padding:6px 9px;border-radius:8px;color:var(--muted);text-decoration:none;font-size:14px;white-space:nowrap}
nav.toc a:hover{color:var(--ink);background:var(--panel)}
.theme{flex:none;background:var(--panel);color:var(--ink);border:1px solid var(--line);border-radius:999px;padding:6px 12px;font:inherit;font-size:14px;cursor:pointer}
main{max-width:1180px;margin:0 auto;padding:0 16px}
section{padding:56px 0;border-bottom:1px solid var(--line)}
h1,h2,h3,h4{line-height:1.18;margin:0 0 .5em}h1{font-size:clamp(34px,5.2vw,56px);letter-spacing:-.02em}
h2{font-size:clamp(26px,3.6vw,40px);letter-spacing:-.01em}h3{font-size:clamp(20px,2.4vw,26px)}h4{font-size:15px;text-transform:uppercase;letter-spacing:.08em;color:var(--muted);margin-top:1.6em}
.eyebrow{font-size:13px;letter-spacing:.14em;text-transform:uppercase;color:var(--accent);font-weight:700;margin:0 0 10px}
.lead{font-size:clamp(18px,2.1vw,22px);color:var(--ink);max-width:62ch}
p{max-width:72ch}.muted{color:var(--muted)}
.slide{position:relative;border:1px solid var(--line);border-radius:22px;padding:clamp(20px,4vw,48px);margin:28px 0;
background:radial-gradient(ellipse at 15% 10%,color-mix(in srgb,var(--accent2) 22%,transparent),transparent 55%),radial-gradient(ellipse at 90% 90%,color-mix(in srgb,var(--accent) 16%,transparent),transparent 50%),linear-gradient(180deg,var(--panel),var(--bg2));box-shadow:var(--shadow)}
@media (min-width:960px){.slide.wide{aspect-ratio:16/9;display:flex;flex-direction:column;justify-content:center}}
.hero{display:grid;grid-template-columns:1.25fr 1fr;gap:28px;align-items:center}
.hero img{width:100%;border-radius:14px;border:1px solid var(--line);display:block;height:auto}
.byline{color:var(--muted);font-size:15px}.byline b{color:var(--accent)}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(118px,1fr));gap:12px;margin:22px 0 0}
.hero-stats{grid-template-columns:repeat(4,minmax(0,1fr))}@media (max-width:860px){.hero-stats{grid-template-columns:repeat(2,minmax(0,1fr))}}
.stat{background:var(--panel2);border:1px solid var(--line);border-radius:14px;padding:12px 14px;display:flex;flex-direction:column;min-width:0}
.stat .num{font-size:clamp(24px,3vw,34px);font-weight:800;color:var(--accent);line-height:1.1}.stat.gold .num{color:var(--gold)}.stat.green .num{color:var(--green)}.stat.pink .num{color:var(--pink)}.stat.purple .num{color:var(--accent2)}
.stat .lab{font-weight:600;font-size:14px;margin-top:4px}.stat .src,.src{font-size:12px;color:var(--muted);overflow-wrap:anywhere}
.video{margin:18px 0 0}.video video{width:100%;height:auto;aspect-ratio:16/9;border-radius:14px;border:1px solid var(--line);background:#000;display:block}
.video figcaption,figcaption{font-size:14px;color:var(--muted);margin-top:8px}
figure{margin:0}figure img{max-width:100%;height:auto;border-radius:12px;border:1px solid var(--line);display:block}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:16px;margin-top:18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:18px 20px;min-width:0}
.card h3{font-size:20px}.card p{font-size:16px}.card .big{font-size:30px;font-weight:800;color:var(--accent);line-height:1}
.two{display:grid;grid-template-columns:1fr 1fr;gap:28px;align-items:start}
.chips{display:flex;flex-wrap:wrap;gap:8px;margin:10px 0;padding:0;list-style:none}.chips li{border:1px solid var(--gold);color:var(--gold);border-radius:999px;padding:3px 12px;font:14px ui-monospace,Menlo,monospace}
.pill{display:inline-block;font-size:12px;font-weight:700;border-radius:999px;padding:1px 9px;border:1px solid;vertical-align:1px;white-space:nowrap}
.pill.ok{color:var(--green);border-color:var(--green)}.pill.warn{color:var(--gold);border-color:var(--gold)}.pill.muted{color:var(--muted);border-color:var(--line)}
.pill.now{color:var(--accent);border-color:var(--accent)}.pill.next{color:var(--gold);border-color:var(--gold)}.pill.later{color:var(--muted);border-color:var(--muted)}.pill.done{color:var(--green);border-color:var(--green)}
sup.fn a{text-decoration:none;font-weight:700;font-size:.78em}
.explainer{padding:30px 0;border-top:1px dashed var(--line)}.explainer:first-of-type{border-top:0}
.dek{color:var(--muted);font-size:18px;max-width:70ch}
.xgrid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(0,1fr);gap:28px;align-items:start}
.xside{position:sticky;top:76px}.xgrid.wide{grid-template-columns:1fr}.xgrid.wide .xside{position:static;max-width:760px}
.drift{border-left:3px solid var(--gold);padding:8px 12px;background:color-mix(in srgb,var(--gold) 9%,transparent);border-radius:0 10px 10px 0;font-size:15px}
.tablewrap{overflow-x:auto;border:1px solid var(--line);border-radius:12px;max-width:100%}
table{border-collapse:collapse;width:100%;font-size:15px}th,td{text-align:left;vertical-align:top;padding:9px 12px;border-bottom:1px solid var(--line)}
thead th{background:var(--panel2);font-size:13px;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}
tbody th{font-weight:600}.srccell{font-size:13px;color:var(--muted);overflow-wrap:anywhere;min-width:180px}
td{overflow-wrap:anywhere}table.market td:first-child{white-space:nowrap}ul.cols{columns:2 300px;column-gap:28px}ul.cols li{break-inside:avoid}
ul.notdone li::marker{content:"○  ";color:var(--gold)}
.diagram svg,.stacksvg{width:100%;height:auto;display:block}.swipe{display:none}
@media (max-width:640px){.hscroll{overflow-x:auto;border:1px solid var(--line);border-radius:12px;padding:6px}.hscroll svg{min-width:640px}
.swipe{display:block;font-size:13px;color:var(--muted);margin:4px 0 0}}.hscroll:focus-visible{outline:3px solid var(--gold);outline-offset:2px}
.d-box{fill:var(--panel2);stroke:var(--accent2);stroke-width:1.5}.d-0{stroke:var(--accent)}.d-2{stroke:var(--gold)}
.d-t{fill:var(--ink);font:600 15px -apple-system,"Avenir Next",sans-serif}.d-s{fill:var(--muted);font:12px -apple-system,"Avenir Next",sans-serif}
.d-line{stroke:var(--muted);stroke-width:1.6;fill:none}.d-arrow{fill:var(--muted)}
.beatbox{background:var(--code);border:1px solid var(--line);border-radius:12px;padding:12px 14px;font:13px/1.5 ui-monospace,Menlo,monospace;overflow-wrap:anywhere}
.beathead{font-weight:700;margin-bottom:6px}.beatbox b{color:var(--accent)}
.lay rect{fill:var(--panel2);stroke-width:2}.lay-0 rect{stroke:var(--accent)}.lay-1 rect{stroke:var(--accent2)}.lay-2 rect{stroke:var(--pink)}.lay-3 rect{stroke:var(--green)}.lay-4 rect{stroke:var(--gold)}.lay-5 rect{stroke:#78aaff}
.ln{fill:var(--accent);font:800 24px -apple-system,"Avenir Next",sans-serif}.lt{fill:var(--ink);font:700 20px -apple-system,"Avenir Next",sans-serif}
.ls{fill:var(--muted);font:14px -apple-system,"Avenir Next",sans-serif}.lst{fill:var(--gold);font:600 13px -apple-system,"Avenir Next",sans-serif}
.layers{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,320px),1fr));gap:14px;margin-top:18px}
ol.timeline{list-style:none;margin:20px 0;padding:0;border-left:2px solid var(--line)}
ol.timeline>li{position:relative;padding:0 0 26px 26px}ol.timeline>li::before{content:"";position:absolute;left:-9px;top:6px;width:16px;height:16px;border-radius:50%;background:var(--bg);border:3px solid var(--muted)}
ol.timeline>li.done::before{background:var(--green);border-color:var(--green)}ol.timeline>li.now::before{border-color:var(--accent)}ol.timeline>li.next::before{border-color:var(--gold)}
.gate{border:1px solid var(--gold);border-radius:12px;padding:8px 12px;color:var(--ink);background:color-mix(in srgb,var(--gold) 8%,transparent);font-size:15px;max-width:72ch}
.gate b{color:var(--gold)}
details{border:1px solid var(--line);border-radius:12px;padding:0 16px;margin:10px 0;background:var(--panel)}
summary{cursor:pointer;font-weight:650;padding:14px 0;list-style-position:outside}details[open] summary{border-bottom:1px solid var(--line);margin-bottom:8px}
dl.gloss{columns:2 340px;column-gap:32px}dl.gloss div{break-inside:avoid;margin:0 0 14px}dl.gloss dt{font-weight:700}dl.gloss dd{margin:2px 0 0;color:var(--muted);font-size:15px}
ol.sources li{margin:0 0 10px;overflow-wrap:anywhere;font-size:15px}ol.sources li:target{background:color-mix(in srgb,var(--gold) 14%,transparent);border-radius:6px}
.kit{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;margin:12px 0}
.kit pre{white-space:pre-wrap;overflow-wrap:anywhere;font:14px/1.5 ui-monospace,Menlo,monospace;margin:6px 0 0;background:var(--code);padding:10px 12px;border-radius:8px}
.notclaimed li{margin:6px 0}.notclaimed li::marker{color:var(--gold)}
footer{max-width:1180px;margin:0 auto;padding:36px 16px 60px;color:var(--muted);font-size:14px}
@media (max-width:860px){.hero,.two,.xgrid{grid-template-columns:1fr}.xside{position:static}body{font-size:16px}section{padding:40px 0}.slide{border-radius:16px}}
@media (max-width:640px){table.rs thead{display:none}table.rs,table.rs tbody,table.rs tr,table.rs th,table.rs td{display:block;width:100%}
table.rs tr{border-bottom:1px solid var(--line);padding:8px 0}table.rs th,table.rs td{border:0;padding:2px 12px}.srccell{min-width:0}
table.rs td[data-label]::before{content:attr(data-label) ": ";font-weight:700;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.05em}}
@media (prefers-reduced-motion:reduce){html{scroll-behavior:auto}}
"""

JS = """(function(){var r=document.documentElement,b=document.getElementById('theme');function lab(){var d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');b.textContent=d==='dark'?'Light theme':'Dark theme';}
try{var s=localStorage.getItem('wp-theme');if(s)r.setAttribute('data-theme',s);}catch(e){}
b.addEventListener('click',function(){var d=r.getAttribute('data-theme')||(matchMedia('(prefers-color-scheme: light)').matches?'light':'dark');var n=d==='dark'?'light':'dark';r.setAttribute('data-theme',n);try{localStorage.setItem('wp-theme',n);}catch(e){}lab();});lab();
var t=document.querySelector('nav.toc');function more(){t.classList.toggle('more',t.scrollLeft+t.clientWidth<t.scrollWidth-2);}if(t){t.addEventListener('scroll',more,{passive:true});addEventListener('resize',more);more();}})();"""


def build_html(D, films):
    """films: {name: {"seconds": s, ...}} from build.json (or None when a film has not been cut)."""
    sx = seo(D)
    pbc = D["pbc"]
    fnum = D["fn"]
    claims = D["claims"]
    films = films or {}
    base = D.get("base_url")

    def absu(rel):
        return base + rel if base else rel

    def film_block(key, sid, h2, blurb):
        f = FILMS[key]
        info = films.get(key) or {}
        secs = info.get("seconds")
        narr = info.get("narration") or "not cut yet"
        nlab = (f"synthetic narration (macOS {narr.split(':', 1)[1]}), labelled on the end card" if narr.startswith("say:")
                else ("silent cut with burned-in captions" if narr == "silent" else "film not cut yet"))
        return (f'<section id="{sid}" aria-labelledby="{sid}-h"><div class="slide wide"><p class="eyebrow">Video · 2 minutes</p><h2 id="{sid}-h">{e(h2)}</h2>'
                f'<p class="lead">{blurb}</p><figure class="video"><video controls preload="none" playsinline width="960" height="540" poster="{e(f["poster"])}" '
                f'aria-describedby="{sid}-cap"><source src="{e(f["file"])}" type="video/mp4"><track kind="captions" src="{e(f["vtt"])}" srclang="en" label="English" default>'
                f'Your browser cannot play this video. <a href="{e(f["file"])}">Download the MP4</a>.</video>'
                f'<figcaption id="{sid}-cap">{e(f["name"])} · {e(f"{secs:.1f} s" if secs else "length unknown")} · 960×540 · {e(nlab)} · '
                f'captions <a href="{e(f["vtt"])}">{e(f["vtt"])}</a>'
                + (f' · its numbers were read when it was cut, at heartbeat beat {e(info["cited_beat"])}, so they can trail this page' if info.get("cited_beat") else "")
                + '</figcaption></figure></div></section>')

    # ---------------- hero
    hero_stats = "".join(x.replace('<div class="stat', '<div role="listitem" class="stat', 1) for x in [
        stat(V(D, "worlds"), "worlds, all coming soon", S(D, "worlds")),
        stat(fmt(V(D, "cards")), "SmartCiti.X Master Cards", S(D, "cards"), "purple"),
        stat(f"{fmt(V(D, 'evals'))} / {V(D, 'failed')}", "evals / failing", S(D, "evals"), "green"),
        stat(V(D, "avatars.avatars"), "avatars bound to agents", S(D, "avatars.avatars"), "pink"),
        stat(f"{V(D, 'hive.omegas')} / {V(D, 'hive.seated')}", "Omega Stewards / seated", S(D, "hive.omegas")),
        stat(f"{V(D, 'exteriors')}", "buildings, each with an interior", S(D, "exteriors"), "gold"),
        stat(f"{V(D, 'anchored')} of {V(D, 'worlds')}", "worlds with an RP1 anchor", S(D, "anchored"), "gold"),
    ])
    hero = (f'<section id="top" aria-labelledby="h1" class="herosec"><div class="slide wide"><div class="hero"><div>'
            f'<p class="eyebrow">{e(ORG)} · {e(UMBRELLA)}</p><h1 id="h1">{e(TITLE)}</h1>'
            f'<p class="lead">A network of agent-managed, human-governed virtual worlds. Agents do the operational work under explicit permissions; '
            f'a 2-of-3 human Steward Council holds the {V(D, "reserved_actions")} decisions that matter.</p>'
            f'<p class="byline">Published {e(D["date"])} by <b>{e(ORG)}</b>. Every project number below is read from a registry file when the page is built, '
            f'and names that file. Nothing here is deployed, minted or live.</p></div>'
            f'<figure><img src="media/still-viewer-orbit.jpg" alt="{e(ALT["worldforge/out/stills/viewer-orbit.jpg"])}"{img_size("media/still-viewer-orbit.jpg")} fetchpriority="high">'
            f'<figcaption>Orbit of a generated world in the WorldForge viewer (<code>worldforge/out/stills/viewer-orbit.jpg</code>).</figcaption></figure></div>'
            f'<div class="stats hero-stats" role="list" aria-label="Key numbers read from the registries">{hero_stats}</div></div></section>')

    # ---------------- why
    why_paras = "".join(f"<p>{cite(D, p)}</p>" for p in D["market"]["narrative"]["why"])
    hi = [("gartner-apps-2026", "40%", "of enterprise apps with task-specific agents by 2026 (Gartner forecast)"),
          ("kpmg-agents-q3-2026", "62%", "of surveyed US $1B+ organizations building or deploying agents (KPMG, Q3 2026)"),
          ("gartner-sprawl-2028", "150,000+", "agents expected per average Global Fortune 500 enterprise by 2028 (The Register, covering Gartner's agent-sprawl guidance)"),
          ("kpmg-highrisk-q3-2026", "49%", "of surveyed leaders closed some high-risk uses to autonomous agents (KPMG)")]
    why_tiles = "".join(f'<div class="stat {tone}"><span class="num">{e(n)}<sup class="fn"><a href="#src-{fnum[c]}" aria-label="Source {fnum[c]}">[{fnum[c]}]</a></sup></span>'
                        f'<span class="lab">{e(lab)}</span><span class="src">{e(claims[c].get("display_publisher") or claims[c]["publisher"])}, {e(claims[c]["year"])}</span></div>'
                        for (c, n, lab), tone in zip(hi, ["", "green", "gold", "pink"]))
    why = (f'<section id="why" aria-labelledby="why-h"><p class="eyebrow">Why · the problem and the moment</p><h2 id="why-h">Agents are arriving faster than their governance</h2>'
           f'<div class="stats">{why_tiles}</div>{why_paras}'
           f'<p class="muted">Figures are third-party forecasts and survey results, cited with their publisher and date; see the <a href="#market">market overview</a> and the caveats under it.</p></section>')

    # ---------------- what
    what_paras = "".join(f"<p>{cite(D, p)}</p>" for p in D["market"]["narrative"]["what"])
    fam_cards = "".join(f'<div class="card"><div class="big">{f["count"]}</div><h3>{e(f["label"])}</h3><p class="muted">Landmark style <code>{e(f["style"])}</code>. Basis: {e(f["basis"])}</p></div>'
                        for f in D["families"])
    mgmt = pbc["management_style"]
    what = (f'<section id="what" aria-labelledby="what-h"><p class="eyebrow">What · the agentic world network</p><h2 id="what-h">Agent-managed, human-governed worlds</h2>'
            f'{what_paras}<div class="two"><div><h3>Agents handle</h3>{ul([e(x) for x in mgmt["agents_handle"]])}<h3>Humans hold</h3>{ul([e(x) for x in mgmt["humans_hold"]])}'
            f'{src_tag("worlds/PBC.json#management_style")}<h3>Held for the Steward Council (2 of {e(pbc["steward_seats"])})</h3>'
            f'<ul class="chips">' + "".join(f"<li>{e(a)}</li>" for a in pbc["reserved_for_humans"]) + f'</ul>{src_tag("worlds/PBC.json#reserved_for_humans")}</div>'
            f'<div>{fig("media/landmarks-preview.jpg", ALT["worldforge/out/assets/landmarks/preview.jpg"], "The " + str(V(D, "landmarks")) + " civic landmarks, one style per family (<code>worldforge/out/assets/landmarks/preview.jpg</code>).")}</div></div>'
            f'<h3>{V(D, "worlds")} worlds in {len(D["families"])} families</h3><div class="cards">{fam_cards}</div>{src_tag("worldforge/out/assets/landmarks/index.json#styles")}'
            f'<h3>Mission and programs</h3><p><b>Mission:</b> {e(pbc["mission"])} {src_tag("worlds/PBC.json#mission")}</p>'
            f'<div class="cards">' + "".join(f'<div class="card"><h3>{e(p["name"])}</h3><p>{e(p["what"])}</p></div>' for p in pbc["programs"]) +
            f'</div>{src_tag("worlds/PBC.json#programs")}</section>')

    # ---------------- how
    kinds_txt = ", ".join(f"{k} {v}" for k, v in D["kinds"].items())
    how_cards = [
        ("Master Cards and Volum", fmt(V(D, "cards")), f"One SmartCiti.X Master Card for every object in a world, in {V(D, 'card_kinds')} kinds ({kinds_txt}). Each card carries its owner, its Volum (a box in world space), a permission matrix and the reserved actions.", "worldforge/out/<slug>/cards.json; worldforge/out/index.json"),
        ("Permissions: seven rights", str(V(D, "rights")), f"Every card names who may {', '.join(D['rights'])}. Agents get one extra right, operating their own zone; {fmt(V(D, 'reserved_entries'))} reservation entries hold the {V(D, 'reserved_actions')} reserved actions for the Steward Council.", "worldforge/out/<slug>/cards.json#rights; worlds/PBC.json"),
        ("Swarms", str(V(D, "swarms")), f"Each world runs a hub-hybrid swarm: one coordinator and its specialists ({V(D, 'specialists')} specialist agents in all). Agents answer with deterministic stubs today and hand off between zones.", "agents/swarms/*.json"),
        ("Metaprompts", str(V(D, "prompts")), f"{V(D, 'prompts')} prompts, {V(D, 'prompts_failing')} failing their checks. {V(D, 'prompts_awaiting_focus')} spec metaprompts wait on a founder-written focus, and say so.", "agents/prompts/index.json"),
        ("Avatars", str(V(D, "avatars.avatars")), f"{V(D, 'avatars.avatars')} avatars bound to agent records, {V(D, 'avatars.persona_prompts')} persona prompts, {V(D, 'avatar_glbs')} role models validated with {V(D, 'avatar_val_errors')} errors.", "worldforge/out/avatars/index.json; worldforge/out/assets/avatars/validation.json"),
        ("The Omega Hive", f"{V(D, 'hive.omegas')}", f"{V(D, 'hive.omegas')} Omega Stewards with personas and synthetic voices ({D['engine']}); {V(D, 'hive.seated')} seated. {V(D, 'hive.spoken')} of {V(D, 'hive.lines')} lines voiced.", "agents/hive/index.json"),
        ("Heartbeat and evals", fmt(V(D, "evals")), f"{fmt(V(D, 'evals'))} WorldForge evals with {V(D, 'failed')} failing; {V(D, 'broken')} deliberately broken worlds each fail their own check. {V(D, 'beats_total')} heartbeat beats were logged when this page was built ({V(D, 'beats_green')} GREEN).", "worldforge/out/index.json; evidence/heartbeat.log"),
    ]
    how = (f'<section id="how" aria-labelledby="how-h"><p class="eyebrow">How · it works</p><h2 id="how-h">Cards, permissions, swarms, metaprompts, avatars, hive, heartbeat</h2>'
           + "".join(f"<p>{cite(D, p)}</p>" for p in D["market"]["narrative"]["how"]) +
           '<div class="cards">' + "".join(f'<div class="card"><div class="big">{e(n)}</div><h3>{e(t)}</h3><p>{e(txt)}</p>{src_tag(s)}</div>' for t, n, txt, s in how_cards) + "</div>"
           f'<div class="two" style="margin-top:22px">{fig("media/still-viewer-council.jpg", ALT["worldforge/out/stills/viewer-council.jpg"], "The Steward Council: three human seats, all empty (<code>worldforge/out/stills/viewer-council.jpg</code>).")}'
           f'{fig("media/avatars-preview.jpg", ALT["worldforge/out/assets/avatars/preview.jpg"], "The six avatar role models (<code>worldforge/out/assets/avatars/preview.jpg</code>).")}</div></section>')

    # ---------------- explainers
    ex_html = []
    total_sections = 0
    for doc in D["explainers"]:
        gid = doc.get("group", "group")
        gtitle = doc.get("title") or {"environments-and-stack": "Environments, assets and the stack", "world-and-governance": "The world and its governance"}.get(gid, gid)
        secs = "".join(explainer_section(D, s) for s in doc["sections"])
        total_sections += len(doc["sections"])
        ex_html.append(f'<section id="g-{e(gid)}" aria-labelledby="g-{e(gid)}-h"><p class="eyebrow">Deep explainer</p><h2 id="g-{e(gid)}-h">{e(gtitle)}</h2>'
                       f'<p class="muted">Written by the explainer agents from the registries on 2026-10-12. Facts marked <span class="pill ok">re-read</span> were re-read from their '
                       f'registry when this page was built; <span class="pill warn">now N</span> marks a value that has since moved; <span class="pill muted">as read</span> '
                       f'is the agent\'s reading of a source this build does not parse.</p>{secs}</section>')
    toc = "".join(f'<li><a href="#x-{e(s["id"])}">{e(s["title"])}</a></li>' for doc in D["explainers"] for s in doc["sections"])
    explainers = (f'<section id="explainers" aria-labelledby="ex-h"><p class="eyebrow">Deep explainers</p><h2 id="ex-h">{total_sections} explainers, each with facts, a visual and what is not done</h2>'
                  f'<ol class="xtoc">{toc}</ol></section>' + "".join(ex_html))

    # ---------------- stack + roadmap
    layers = stack_layers(D)
    stack = (f'<section id="stack" aria-labelledby="stack-h"><p class="eyebrow">The stack</p><h2 id="stack-h">Six layers, from validated assets to onchain-ready records</h2>'
             f'<div class="two"><div>{hscroll(stack_svg(D))}</div><div class="layers" style="margin-top:0">' +
             "".join(f'<div class="card"><h3>{i + 1}. {e(L["name"])}<span class="sr"> — status:</span> <span class="pill muted">{e(L["status"])}</span></h3>{ul([e(x) for x in L["facts"]])}{src_tag(L["source"])}</div>'
                     for i, L in enumerate(layers)) + "</div></div>"
             '<h3>Tools in use</h3><div class="tablewrap"><table class="rs"><thead><tr><th scope="col">Tool</th><th scope="col">Role</th><th scope="col">Status</th></tr></thead><tbody>' +
             "".join(f'<tr><th scope="row">{e(s["name"])}</th><td data-label="Role">{e(s["role"])}</td><td data-label="Status">{e(s["status"])}</td></tr>' for s in D["roadmap"].get("stack", [])) +
             f'</tbody></table></div>{src_tag("atlas/roadmap.json#stack")}{qual_note(D, "#stack")}</section>')
    phases = phase_steps(D)
    road = (f'<section id="roadmap" aria-labelledby="road-h"><p class="eyebrow">Roadmap</p><h2 id="road-h">Every open phase waits on a named human gate</h2><ol class="timeline">' +
            "".join(f'<li class="{e(p.get("status", ""))}"><h3>{e(p["name"])}<span class="sr"> — status:</span> <span class="pill {e(p.get("status", ""))}">{e(p.get("status", ""))}</span></h3>'
                    f'{ul([e(x) for x in p.get("items", [])])}<p class="gate"><b>Human gate:</b> {e(p.get("gate", "none named"))}</p></li>' for p in phases) +
            f'</ol>{src_tag("atlas/roadmap.json#phases")}{qual_note(D, "#phases")}<h3>WorldForge gates: the Sneeze native path</h3><div class="tablewrap"><table><thead><tr><th scope="col">Gate</th><th scope="col">Status</th></tr></thead><tbody>' +
            "".join(f'<tr><th scope="row">{e(k)}</th><td>{e(v)}</td></tr>' for k, v in D["gates"].items()) +
            f'</tbody></table></div>{src_tag("worldforge/out/cancer-dao/manifest.json#gates (the same in every world)")}'
            f'<p class="gate"><b>Human gates:</b> mounting in Sneeze needs the Sneeze source checked out and a rendered frame; publishing any world on RP1\'s Earth, '
            f'and choosing the anchors most worlds still lack ({V(D, "worlds") - V(D, "anchored")} of {V(D, "worlds")}), is the founder\'s call.</p></section>')

    # ---------------- market
    rows = []
    for cid in D["order"]:
        c = claims[cid]
        rows.append(f'<tr><td><a href="#src-{fnum[cid]}">[{fnum[cid]}]</a></td><td data-label="Topic">{e(c["topic"])}</td><td data-label="Figure">{e(c["figure"])}</td><td data-label="Year">{e(c["year"])}</td>'
                    f'<td data-label="Publisher"><a href="{e(c["url"])}" rel="noopener external">{e(c.get("display_publisher") or c["publisher"])}</a></td><td data-label="Verdict"><span class="pill {"ok" if c["verdict"] == "confirmed" else "warn"}">{e(c["verdict"])}</span></td></tr>')
    market = (f'<section id="market" aria-labelledby="mkt-h"><p class="eyebrow">Market overview</p><h2 id="mkt-h">{len(claims)} fact-checked figures from adjacent markets</h2>'
              '<p>Only claims the fact-check confirmed (or corrected, then used in corrected form) are shown. They describe adjacent markets; they are not evidence of demand for this project.</p>'
              '<div class="tablewrap"><table class="market rs"><caption class="sr">Market claims with figure, year, publisher and verdict</caption><thead><tr><th scope="col">#</th><th scope="col">Topic</th>'
              '<th scope="col">Figure</th><th scope="col">Year</th><th scope="col">Publisher</th><th scope="col">Verdict</th></tr></thead><tbody>' + "".join(rows) +
              f'</tbody></table></div>{src_tag("worldforge/whitepaper/content/market.json")}<h3>Reading these figures</h3>{ul([e(x) for x in D["market"]["caveats"]])}</section>')

    # ---------------- not claimed
    nc = end_claims(D) + [
        f"Agents answer with deterministic stubs; no AI model answers visitors in these worlds today",
        f"Ledger signatures use test keys; no human steward has registered a key",
        f"{V(D, 'prompts_awaiting_focus')} worlds' spec metaprompts still wait on a founder-written focus",
        "Market forecasts are third-party estimates about adjacent markets, not facts about this project",
    ]
    notc = (f'<section id="not-claimed" aria-labelledby="nc-h"><p class="eyebrow">Plainly</p><h2 id="nc-h">What we do not claim</h2>'
            f'<ul class="notclaimed">' + "".join(f"<li>{e(x)}</li>" for x in nc) + f'</ul><p class="muted">{e(DISCLAIMER)}</p></section>')

    # ---------------- faq + glossary
    faqs = faq_items(D)
    faq = (f'<section id="faq" aria-labelledby="faq-h"><p class="eyebrow">FAQ</p><h2 id="faq-h">Questions people ask</h2>' +
           "".join(f"<details><summary>{e(q['q'])}</summary><p>{e(q['a'])}</p></details>" for q in faqs) + "</section>")
    gl = glossary_items(D)
    gloss = (f'<section id="glossary" aria-labelledby="gl-h"><p class="eyebrow">Glossary</p><h2 id="gl-h">{len(gl)} terms</h2><dl class="gloss">' +
             "".join(f'<div><dt>{e(g["term"])}</dt><dd>{e(g["definition"])}</dd></div>' for g in gl) + "</dl></section>")

    # ---------------- sources
    srcs = []
    for cid in D["order"]:
        c = claims[cid]
        prim = f' Primary release: <a href="{e(c["primary_url"])}" rel="noopener external">{e(c["primary_url"])}</a>.' if c.get("primary_url") else ""
        note = f" {e(c['note'])}" if c.get("note") else ""
        srcs.append(f'<li id="src-{fnum[cid]}">{e(c.get("display_publisher") or c["publisher"])}, “{e(c["title"])}” ({e(c["year"])}). <a href="{e(c["url"])}" rel="noopener external">{e(c["url"])}</a>. '
                    f'Accessed {e(c["accessed"])}. Claim id <code>{e(cid)}</code>, verdict {e(c["verdict"])}.{note}{prim}</li>')
    reg = sorted(D["used"])
    ex_read = sorted({p for doc in D["explainers"] for p in (doc.get("read_from") or doc.get("sources_read") or [])})
    sources = (f'<section id="sources" aria-labelledby="src-h"><p class="eyebrow">Sources</p><h2 id="src-h">Sources</h2><h3>Market sources (numbered as cited)</h3>'
               f'<ol class="sources">{"".join(srcs)}</ol><h3>Registry files this page read when it was built</h3>{ul([f"<code>{e(p)}</code>" for p in reg], "cols")}'
               f'<h3>Files the explainer agents read</h3>{ul([f"<code>{e(p)}</code>" for p in ex_read], "cols")}'
               f'<p class="muted">The heartbeat beat cited on this page is pinned in <code>worldforge/whitepaper/out/build.json</code>: <code>{e(D["beat"][:8])}</code>.</p></section>')

    # ---------------- share kit
    kit = (f'<section id="share-kit" aria-labelledby="kit-h"><p class="eyebrow">Appendix</p><h2 id="kit-h">Search and share kit</h2>'
           + (f'<p class="muted">Drafts for whoever publishes this page. Canonical URL: <code>{e(base)}</code>. The posts claim no traction because there is none to claim.</p>' if base else
              '<p class="muted">Drafts for whoever publishes this page. No canonical URL is set because no public address has been given for it yet. The posts claim no traction because there is none to claim.</p>') +
           f'<div class="kit"><h3>Title tag ({len(sx["title"])} characters)</h3><pre>{e(sx["title"])}</pre></div>'
           f'<div class="kit"><h3>Meta description ({len(sx["description"])} characters)</h3><pre>{e(sx["description"])}</pre></div>'
           f'<div class="kit"><h3>Target keywords</h3><pre>{e(", ".join(sx["keywords"]))}</pre><h3>Long-tail phrases</h3>{ul([e(x) for x in sx["longtail"]])}</div>'
           f'<div class="kit"><h3>Suggested URL slug</h3><pre>/{e(sx["slug"])}/</pre></div>'
           f'<div class="kit"><h3>Open Graph and Twitter</h3><pre>og:title / twitter:title: {e(sx["og_title"])}\nog:description / twitter:description: {e(sx["og_description"])}\nog:image / twitter:image: {e(absu(FILMS["features"]["poster"]))} (1200×630 crop recommended before launch)</pre>'
           + ('' if base else '<p class="gate"><b>Not ready to share yet:</b> the image and video URLs in these tags are relative, and Facebook, LinkedIn, X and Slack '
              'need absolute ones, so a shared link would show no image card. There is no og:url or canonical URL either. Before publishing, rebuild with '
              '<code>--base-url https://&lt;host&gt;/&lt;folder&gt;/</code> (the folder that will serve this page); the build then writes absolute URLs, og:url and the canonical link. '
              'No domain is assumed here.</p>') + '</div>'
           f'<div class="kit"><h3>Social post drafts</h3>' + "".join(f"<pre>{e(p)}</pre>" for p in sx["posts"]) + "</div></section>")

    contact = (f'<section id="contact" aria-labelledby="ct-h"><div class="slide"><p class="eyebrow">Contact</p><h2 id="ct-h">Review it, question it, check it</h2>'
               + (f'<p class="lead">Write to <a href="mailto:{e(D["contact"])}">{e(D["contact"])}</a>. {e(ORG)} · {e(UMBRELLA)}.</p>' if D.get("contact") else
                  f'<p class="lead">Questions and review go to {e(ORG)} · {e(UMBRELLA)}. No public contact address is printed here until the founder confirms one.</p>')
               + f'<p class="muted">{e(DISCLAIMER)}</p></div></section>')

    body = (hero +
            film_block("features", "film-features", "Film 1: the features",
                       "Two minutes on the world network, a recorded walk through Cancer DAO, avatars bound to agents, the Omega Hive and governance. "
                       "The narration is a synthetic voice, with one short line per section and per walkthrough clip; the Omega Steward's own synthetic voice is not played in it.") +
            why + what + how + explainers +
            film_block("roadmap-stack", "film-roadmap", "Film 2: the roadmap and the stack",
                       "Two minutes on the six layers of the stack, the evidence behind them, the roadmap's phases and their human gates, and the next steps. "
                       "Each layer and each phase has its own narrated line.") +
            stack + road + market + notc + faq + gloss + sources + kit + contact)

    # ---------------- head: SEO + JSON-LD
    sections_list = [n for _, n in SECTIONS_NAV]
    org = {"@type": "Organization", "@id": absu("#org"), "name": ORG, "slogan": UMBRELLA}
    if D.get("contact"):
        org["email"] = D["contact"]
    article = {"@type": "TechArticle", "@id": absu("#article"), "headline": TITLE, "description": sx["description"], "author": {"@id": absu("#org")},
               "publisher": {"@id": absu("#org")}, "datePublished": D["date"], "dateModified": D["date"], "inLanguage": "en", "keywords": ", ".join(sx["keywords"]),
               "articleSection": sections_list, "image": absu(FILMS["features"]["poster"]),
               "about": ["agentic AI", "AI governance", "virtual worlds"], "isAccessibleForFree": True}
    vids = []
    for key, desc in (("features", "The features of SmartCiti.X: the world network, a recorded walkthrough, avatars bound to agents, the Omega Hive and governance. Synthetic narration."),
                      ("roadmap-stack", "The SmartCiti.X roadmap and stack: six layers, the evidence, roadmap phases with their human gates, and next steps. Synthetic narration.")):
        f = FILMS[key]
        vids.append({"@type": "VideoObject", "@id": absu(f"#film-{key}"), "name": f["name"], "description": desc, "duration": "PT2M", "uploadDate": D["built_at"],
                     "thumbnailUrl": absu(f["poster"]), "contentUrl": absu(f["file"]), "inLanguage": "en", "publisher": {"@id": absu("#org")}})
    faqld = {"@type": "FAQPage", "@id": absu("#faq"), "mainEntity": [{"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faqs]}
    if base:
        article["url"] = base
        article["mainEntityOfPage"] = base
    ld = json.dumps({"@context": "https://schema.org", "@graph": [org, article] + vids + [faqld]}, ensure_ascii=False, indent=1).replace("</", "<\\/")
    nav = "".join(f'<li><a href="#{a}">{e(b)}</a></li>' for a, b in SECTIONS_NAV)
    head = (
        '<!doctype html>\n<html lang="en">\n<head>\n<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f'<title>{e(sx["title"])}</title>\n<meta name="description" content="{e(sx["description"])}">\n'
        f'<meta name="keywords" content="{e(", ".join(sx["keywords"]))}">\n<meta name="robots" content="index,follow">\n'
        f'<meta name="author" content="{e(ORG)}">\n<meta name="theme-color" content="#060918">\n'
        + (f'<link rel="canonical" href="{e(base)}">\n<meta property="og:url" content="{e(base)}">\n' if base else
           '<!-- No canonical URL: no public address has been given for this page. Rebuild with --base-url to write the canonical link, og:url and absolute og:image / JSON-LD URLs. -->\n')
        + '<link rel="icon" href="data:,">\n'
        f'<meta property="og:type" content="article">\n<meta property="og:title" content="{e(sx["og_title"])}">\n<meta property="og:description" content="{e(sx["og_description"])}">\n'
        f'<meta property="og:image" content="{e(absu(FILMS["features"]["poster"]))}">\n<meta property="og:image:alt" content="Title card of the SmartCiti.X features film">\n'
        f'<meta property="og:site_name" content="SmartCiti.X">\n<meta property="article:published_time" content="{e(D["date"])}">\n'
        f'<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:title" content="{e(sx["og_title"])}">\n'
        f'<meta name="twitter:description" content="{e(sx["og_description"])}">\n<meta name="twitter:image" content="{e(absu(FILMS["features"]["poster"]))}">\n'
        f'<script type="application/ld+json">\n{ld}\n</script>\n<style>{CSS}</style>\n</head>\n<body>\n'
        '<a class="skip" href="#main">Skip to content</a>\n'
        f'<header class="top"><div class="topin"><a class="brand" href="#top">SmartCiti<span>.X</span></a><nav class="toc" aria-label="Sections"><ul>{nav}</ul></nav>'
        '<button id="theme" class="theme" type="button">Light theme</button></div></header>\n'
        f'<main id="main">\n{body}\n</main>\n<footer><p>{e(TITLE)} · {e(ORG)} · {e(UMBRELLA)} · built {e(D["date"])} by <code>worldforge/whitepaper/build_whitepaper.py</code> '
        f'from the registries named on the page.' + (f' Contact <a href="mailto:{e(D["contact"])}">{e(D["contact"])}</a>.' if D.get("contact") else "")
        + f'</p></footer>\n<script>{JS}</script>\n</body>\n</html>\n')
    return head


def honesty_scan(text, where, contact=None):
    low = text.lower()
    for f in FORBIDDEN:
        if f in low:
            die(f"{where} would contain the private repository name")
    for m in re.findall(r"[\w.+-]+@[A-Za-z][\w-]*\.[A-Za-z][\w.]*", text):
        if m != contact:
            die(f"{where} would contain an email address ({m}); a contact address is published only when passed with --contact-email")
    if re.search(r"\b0x[0-9a-fA-F]{40}\b", text):
        die(f"{where} would contain a wallet-like address")
    if re.search(r"\b(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{16})\b", text):
        die(f"{where} would contain a key-like string")
    if re.search(r"~/Downloads|/Users/", text):
        die(f"{where} would contain a local file path")


def count_sections(page):
    return len(re.findall(r"<section id=", page))


# ------------------------------------------------------------------------------------------------ build / check
def build_json(D, page, films, pinned):
    ex = {"verified": 0, "rebuilt_facts": 0, "drift": [], "unchecked": 0}
    for doc in D["explainers"]:
        for s in doc["sections"]:
            for f in s.get("facts", []):
                c = f["_check"]
                if c["status"] == "verified":
                    ex["verified"] += 1
                elif c["status"] == "rebuilt":
                    ex["rebuilt_facts"] += 1
                elif c["status"] == "drift":
                    ex["drift"].append({"section": s["id"], "label": f["label"], "text": f["value"], "registry_now": c["current"], "pointer": c["pointer"]})
                else:
                    ex["unchecked"] += 1
    return {"schemaVersion": "smartcitix-whitepaper-build/0.1", "title": TITLE, "pinned": pinned,
            "numbers": D["N"], "sources": {"registries": sorted(D["used"]), "market": "worldforge/whitepaper/content/market.json",
                                           "explainers": sorted(os.path.relpath(p, ROOT) for p in glob.glob(os.path.join(CONTENT, "explainers-*.json")))},
            "claims": [{"n": D["fn"][c], "id": c, "verdict": D["claims"][c]["verdict"]} for c in D["order"]],
            "films": films, "explainer_facts": ex, "rebuilt": D["rebuilt"], "page_qualifiers": D.get("qualified", []), "sections": count_sections(page),
            "page_sha256": hashlib.sha256(page.encode()).hexdigest(), "media": sorted(media_plan(D))}


def check():
    if not os.path.exists(BUILD):
        print("whitepaper STALE: no worldforge/whitepaper/out/build.json; run python3 worldforge/whitepaper/build_whitepaper.py"); sys.exit(1)
    bj = json.load(open(BUILD))
    pinned = bj["pinned"]
    problems = []
    if pinned.get("heartbeat_line") and pinned["heartbeat_line"] not in heartbeat_lines():
        problems.append("the heartbeat beat the page cites is no longer in evidence/heartbeat.log")
    D = load(pinned)
    WORLD_NAMES.update(D["names"])
    films = bj.get("films") or {}
    page = build_html(D, films)
    if not os.path.exists(PAGE) or open(PAGE).read() != page:
        problems.append("index.html differs from a rebuild")
    problems += write_media(D, check=True)
    secs = {}
    for key, f in FILMS.items():
        p = os.path.join(OUT, f["file"])
        s = duration(p) if os.path.exists(p) else None
        secs[key] = s
        if s is None:
            problems.append(f"{f['file']} missing (gitignored; rebuild)")
        elif not 118 <= s <= 122:
            problems.append(f"{f['file']} is {s:.1f} s, not 118-122 s")
        cues = (films.get(key) or {}).get("captions")
        vp = os.path.join(OUT, f["vtt"])
        if cues and (not os.path.exists(vp) or open(vp).read() != vtt_render(f["name"], cues, vtt_note((films.get(key) or {}).get("narration")))):
            problems.append(f"{f['vtt']} differs from the film's captions")
        nl = (films.get(key) or {}).get("narration_lines")
        if not isinstance(nl, list) or len(nl) != len(cues or []):
            problems.append(f"{f['file']} has no per-line narration timing (cut before captions were timed to speech; rebuild the films)")
        else:
            late = [x["text"][:40] for x, c in zip(nl, cues) if c[2] != x["text"] or c[0] > x["start"] + 0.01 or c[1] < x["end"] - 0.01]
            if late:
                problems.append(f"{f['vtt']}: {len(late)} caption cue(s) do not cover their spoken line (first: '{late[0]}')")
    if problems:
        print("whitepaper STALE: " + "; ".join(problems)); sys.exit(1)
    print(f"whitepaper current: {count_sections(page)} sections, {len(D['order'])} cited market claims, "
          f"films {secs['features']:.1f}s + {secs['roadmap-stack']:.1f}s")


LOCK = os.path.join(OUT, ".build.lock")


def build(no_film=False, silent=False, base_url=None, contact=None):
    """One build at a time: a second build started while one runs would overwrite its films and page halfway."""
    os.makedirs(OUT, exist_ok=True)
    if os.path.exists(LOCK):
        try:
            pid = int(open(LOCK).read().strip() or 0)
            os.kill(pid, 0)
            die(f"another whitepaper build (pid {pid}) is running; wait for it to finish")
        except (ValueError, ProcessLookupError):
            pass
        except PermissionError:
            die("another whitepaper build is running; wait for it to finish")
    open(LOCK, "w").write(str(os.getpid()))
    try:
        _build(no_film, silent, base_url, contact)
    finally:
        try:
            os.remove(LOCK)
        except OSError:
            pass


def _build(no_film=False, silent=False, base_url=None, contact=None):
    prev = json.load(open(BUILD)) if os.path.exists(BUILD) else {}
    beats = heartbeat_lines()
    if no_film:
        narration = (prev.get("pinned") or {}).get("narration") or "silent"
    elif silent:
        narration = "silent"
    else:
        v = say_available()
        narration = f"say:{v}" if v else "silent"
    if base_url and not re.fullmatch(r"https?://[^\s\"'<>]+/", base_url):
        die("--base-url must be an absolute http(s) URL of the folder that will serve index.html, ending in '/'")
    if contact and not re.fullmatch(r"[\w.+-]+@[A-Za-z][\w-]*\.[A-Za-z][\w.]*", contact):
        die("--contact-email is not an email address")
    pinned = {"heartbeat_line": beats[-1] if beats else None, "beats_total": len(beats), "beats_green": sum(1 for b in beats if BEAT.match(b).group(2) == "GREEN"),
              "date": datetime.date.today().isoformat(), "built_at": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
              "narration": narration, "base_url": base_url, "contact": contact}
    D = load(pinned)
    WORLD_NAMES.update(D["names"])
    os.makedirs(OUT, exist_ok=True)
    write_media(D)
    films = dict(prev.get("films") or {}) if no_film else {}
    if not no_film:
        tmp = tempfile.mkdtemp(prefix="wf-whitepaper-")
        try:
            for key in FILMS:
                segs, events, cues = voice_script(D, key, tmp)
                honesty_scan(vtt_render(FILMS[key]["name"], cues), FILMS[key]["vtt"], D.get("contact"))
                info = render_film(D, key, tmp, segs, events)
                s = duration(os.path.join(OUT, FILMS[key]["file"]))
                if s is None or not 118 <= s <= 122:
                    die(f"{FILMS[key]['file']} probed at {s} s, outside 118-122 s")
                films[key] = {"file": f"worldforge/whitepaper/out/{FILMS[key]['file']}", "seconds": round(s, 2), "frames": TOTAL_S * FPS,
                              "narration": info["narration"], "narration_lines": info["lines"], "captions": cues,
                              "clips": [x["src"] for x in segs if x["kind"] == "clip"],
                              "cited_beat": (D["beat"][:8] + " " + BEAT.match(D["beat"]).group(2)) if D["beat"] else None}
                open(os.path.join(OUT, FILMS[key]["vtt"]), "w").write(vtt_render(FILMS[key]["name"], cues, vtt_note(info["narration"])))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
    page = build_html(D, films)
    honesty_scan(page, "index.html", D.get("contact"))
    open(PAGE, "w").write(page)
    bj = build_json(D, page, films, pinned)
    json.dump(bj, open(BUILD, "w"), indent=1, ensure_ascii=False)
    open(BUILD, "a").write("\n")
    f1, f2 = films.get("features") or {}, films.get("roadmap-stack") or {}
    ex = bj["explainer_facts"]
    print(f"whitepaper built: {bj['sections']} sections, {len(D['order'])} cited market claims, page {len(page) // 1024} KB, "
          f"films {f1.get('seconds', '?')}s + {f2.get('seconds', '?')}s ({narration}), {len(bj['media'])} media, "
          f"explainer facts {ex['verified']} re-read / {len(ex['drift'])} moved / {ex['unchecked']} as read")


if __name__ == "__main__":
    a = sys.argv[1:]
    if "-h" in a or "--help" in a:
        print(__doc__.split("Inputs (read only):")[0].strip())
        print("\n    --base-url https://<host>/<folder>/   absolute social/JSON-LD URLs, og:url and canonical (or WHITEPAPER_BASE_URL)"
              "\n    --contact-email ADDRESS               print a contact address (or WHITEPAPER_CONTACT_EMAIL)")
        sys.exit(0)
    known, skip = {"--check", "--no-film", "--silent", "--base-url", "--contact-email"}, False
    for i, x in enumerate(a):
        if skip:
            skip = False
            continue
        if x not in known:
            die(f"unknown argument {x!r} (try --help)")
        skip = x in ("--base-url", "--contact-email")

    def arg(flag, env):
        if flag in a and a.index(flag) + 1 < len(a):
            return a[a.index(flag) + 1]
        return os.environ.get(env) or None
    if "--check" in a:
        check()
    else:
        build(no_film="--no-film" in a, silent="--silent" in a, base_url=arg("--base-url", "WHITEPAPER_BASE_URL"),
              contact=arg("--contact-email", "WHITEPAPER_CONTACT_EMAIL"))

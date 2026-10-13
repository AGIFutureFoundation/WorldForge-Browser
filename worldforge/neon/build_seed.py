#!/usr/bin/env python3
"""The WorldForge build (worldforge/out/) as Neon-ready Postgres seed SQL, built offline. Schema `worldforge`.

    python3 worldforge/neon/build_seed.py            # -> worldforge/neon/seed.sql + worldforge/neon/manifest.json
    python3 worldforge/neon/build_seed.py --check    # exit 1 if seed.sql is behind its sources or differs from them

Nothing here touches a database, and no credential is read or written: the founder applies the files by hand
(worldforge/neon/LOAD.md). worldforge/neon/schema.sql declares the tables; this builder reads worldforge/out and
writes seed.sql, deterministic and stamped with a sha256 of every source file, plus manifest.json.

It follows the house rules of neon/build_seed.py (read, never imported or written), checked by the evals on every
run (the last line counts the failures):
  - every INSERT names a worldforge table and only columns that schema.sql declares, and the SQL parses
  - no credential, key, token, connection string, tax identifier or private repository is written anywhere
  - nothing invented: every card, avatar and prompt rebuilds exactly from its rows (nulls stay NULL)
  - row counts equal the builders' own totals, primary keys are distinct and every foreign key resolves
  - agents operate, people govern: transfer/govern and the six reserved actions stay with the 2-of-3 council
  - the on-chain rows describe a collection that is not deployed and not minted, and every Merkle proof verifies
  - recorded hashes match the files on disk; deliberately broken fixtures each fail their own eval
Outputs are written only when every eval passes.

SQL validation: PostgreSQL and sqlparse are not installed here, so the builder runs its own conservative check -
a quote-, E-string- and comment-aware statement splitter, balanced parentheses outside strings, a token-level parse
of every seed statement against the only grammar it writes (SET client_encoding / BEGIN / INSERT ... VALUES ...
ON CONFLICT (pk) DO UPDATE SET c = EXCLUDED.c / COMMIT), and a structural read of schema.sql.
"""
import glob
import hashlib
import json
import math
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT = os.path.join(ROOT, "worldforge", "out")
SCHEMA = os.path.join(HERE, "schema.sql")
SEED = os.path.join(HERE, "seed.sql")
MANIFEST = os.path.join(HERE, "manifest.json")
STAMP_RE = re.compile(r"^-- worldforge-neon-source-stamp: ([0-9a-f]{16})$", re.M)
SCHEMA_NAME = "worldforge"
CARD_LIFTED = ("cardId", "kind", "parentCardId", "displayName", "owner", "umbrella", "volum", "permissions", "source")
AVATAR_LIFTED = ("avatarId", "cardId", "world", "kind", "role", "name", "binding", "audio", "model_ref", "persona_prompt_id", "source")
PROMPT_KEYS = {"id", "avatarId", "kind", "role", "name", "chars", "text", "gates"}
AGENT_KINDS = ("agent", "coordinator", "advisor", "omega")
RESERVED = ["governance.final_vote", "charter.amend", "treasury.transfer", "proposal.enact", "windfall.distribute", "steward.appoint"]


def rel(p):
    return os.path.relpath(p, ROOT)


_J = {}


def J(p):
    """Parsed JSON, cached per path for one run (callers never mutate it)."""
    if p not in _J:
        with open(os.path.join(ROOT, p), encoding="utf-8") as f:
            _J[p] = json.load(f)
    return _J[p]


def B(p):
    with open(os.path.join(ROOT, p), "rb") as f:
        return f.read()


def sha(b):
    return hashlib.sha256(b).hexdigest()


def exists(p):
    return os.path.exists(os.path.join(ROOT, p))


# ----------------------------------------------------------------------------------------------- the sources ----
def slugs():
    return sorted(w["slug"] for w in J("worldforge/out/index.json")["worlds"])


def training_path():
    p = "worldforge/out/training/index.json"
    return p if exists(p) else None


def token_files(slug):
    return sorted(rel(p) for p in glob.glob(os.path.join(OUT, "onchain", slug, "tokens", "*.json")))


def sources():
    """Every file the seed depends on, in a fixed order. Token files are listed per world in the manifest."""
    out = ["worldforge/neon/build_seed.py", "worldforge/neon/schema.sql", "agents/corporations/index.json", "projects/index.json",
           "worldforge/out/index.json", "worldforge/out/avatars/index.json", "worldforge/out/onchain/index.json",
           "worldforge/out/assets/landmarks/index.json"]
    lm = J("worldforge/out/assets/landmarks/index.json")
    for s in slugs():
        out += [f"worldforge/out/{s}/cards.json", f"worldforge/out/{s}/manifest.json", f"worldforge/out/{s}/sneeze-mount-plan.json",
                f"worldforge/out/{s}/{s}.glb", f"worldforge/out/avatars/prompts/{s}.json",
                f"worldforge/out/onchain/{s}/collection.json", f"worldforge/out/onchain/{s}/proofs.json"]
        out += token_files(s)
    out += sorted(f"worldforge/out/assets/landmarks/{w['file']}" for w in lm["worlds"])
    if training_path():
        out += [training_path()] + training_files()
    return out


def stamp():
    h = hashlib.sha256()
    for p in sources():
        h.update(p.encode()); h.update(b"\0"); h.update(B(p)); h.update(b"\0")
    return h.hexdigest()[:16]


def private_variants():
    """The spellings a private repository could leak under (owner/name, name, slug), as neon/build_seed.py derives them."""
    pj = J("projects/index.json")
    out = set()
    for r in pj["rows"] + pj.get("unassigned", []):
        if r.get("private"):
            out |= {r["repo"].lower(), r["name"].lower(), re.sub(r"[^a-z0-9]+", "-", r["name"].lower()).strip("-")}
    return sorted(v for v in out if len(v) >= 4)


# ------------------------------------------------------------------------------------------------- the rows ----
def build_rows():
    idx = J("worldforge/out/index.json")
    family = {c["world"] for c in J("agents/corporations/index.json")["cells"]}
    av = J("worldforge/out/avatars/index.json")
    oc = J("worldforge/out/onchain/index.json")
    lm = J("worldforge/out/assets/landmarks/index.json")
    oc_world = {w["slug"]: w for w in oc["worlds"]}
    rows = {t: [] for t in TABLES}
    src_cards, src_avatars, src_prompts = {}, {}, {}
    for w in sorted(idx["worlds"], key=lambda w: w["slug"]):
        s = w["slug"]
        doc = J(f"worldforge/out/{s}/cards.json")
        man = J(f"worldforge/out/{s}/manifest.json")
        plan = J(f"worldforge/out/{s}/sneeze-mount-plan.json")
        world_card = next(c for c in doc["cards"] if c["kind"] == "world")
        anchor = world_card.get("anchor") or {}
        rows["worlds_ref"].append({
            "slug": s, "name": w["name"], "status": w["status"], "family_slug": s if s in family else None,
            "anchored": bool(w["anchored"]), "rp1_lat": anchor.get("lat"), "rp1_lon": anchor.get("lon"), "omega": bool(w["omega"]),
            "cards": w["cards"], "zones": w["zones"], "agents": w["agents"], "primitives": w["primitives"], "roads": w["roads"],
            "plan_nodes": w["planNodes"], "resource_nodes": w["resourceNodes"], "glb_path": f"worldforge/out/{s}/{s}.glb",
            "glb_bytes": w["glbBytes"], "glb_sha256": man["files"][f"{s}.glb"], "cards_sha256": man["files"]["cards.json"],
            "gaps": list(doc.get("gaps") or []), "gates": Jsonb(man["gates"])})
        for c in doc["cards"]:
            src_cards[c["cardId"]] = (s, c)
            rows["cards"].append({
                "card_id": c["cardId"], "world": s, "kind": c["kind"], "parent_card_id": c["parentCardId"], "name": c.get("name"),
                "display_name": c["displayName"], "owner": c["owner"], "umbrella": c["umbrella"], "volum": Jsonb(c["volum"]),
                "permissions": Jsonb(c["permissions"]), "source": c["source"],
                "attrs": Jsonb({k: v for k, v in c.items() if k not in CARD_LIFTED and k != "reserved_for_humans"})})
            for i, r in enumerate(c.get("reserved_for_humans") or []):
                h = r["held_for"]
                rows["card_reserved_actions"].append({"card_id": c["cardId"], "action": r["action"], "ord": i, "holder": h["holder"],
                                                      "quorum": h["quorum"], "seats": h["seats"]})
            if c.get("building"):
                b = c["building"]
                rows["buildings"].append({"card_id": c["cardId"], "world": s, "kind": b["kind"], "sign": b.get("sign"), "exterior": b["exterior"],
                                          "interior": b.get("interior"), "room": b.get("room"), "door": jb(b.get("door")),
                                          "resolution": jb(b.get("resolution")), "triangles": jb(b.get("triangles")), "source": b["source"]})
        nodes = plan["nodes"]
        rows["mount_plans"].append({
            "world": s, "schema_version": plan["schemaVersion"], "engine": plan["engine"], "binding_status": plan["bindingStatus"],
            "root_card_id": plan["rootCardId"], "mount_parent": plan["mountParent"], "nodes": len(nodes),
            "resource_nodes": sum(1 for n in nodes if n.get("resource")), "preview_glb_path": plan["previewGlb"]["path"],
            "preview_glb_sha256": plan["previewGlb"]["sha256"], "assets": Jsonb(plan["assets"]),
            "acceptance_requirements": list(plan["acceptanceRequirements"])})
        for name, ok in sorted(man["evals"].items()):
            rows["evals"].append({"source": f"worldforge/out/{s}/manifest.json", "scope": f"world:{s}", "name": name, "ok": bool(ok)})
        pr = J(f"worldforge/out/avatars/prompts/{s}.json")
        for p in pr["prompts"]:
            src_prompts[p["id"]] = (s, p)
            g = p["gates"]
            rows["persona_prompts"].append({"id": p["id"], "avatar_id": p["avatarId"], "world": s, "kind": p["kind"], "role": p["role"],
                                            "name": p["name"], "chars": p["chars"], "text": p["text"], "gates_passed": g["passed"],
                                            "gates_of": g["of"], "gates_failed": list(g["failed"])})
        col = J(f"worldforge/out/onchain/{s}/collection.json")
        proofs = J(f"worldforge/out/onchain/{s}/proofs.json")
        dep = col["deployment"]
        rows["onchain_collections"].append({
            "world": s, "name": col["name"], "standard": col["standard"], "status": dep["status"], "token_count": col["token_count"],
            "card_count": col["card_count"], "merkle_root": col["merkle_root"], "network_root": oc["network_root"],
            "network_proof": list(oc_world[s]["network_proof"]), "cards_sha256": col["source"]["cards_sha256"],
            "token_id_rule": col["token_id_rule"], "chain": dep["chain"], "contract": dep["contract"], "minted": dep["minted"],
            "transactions": dep["transactions"]})
        for tf in token_files(s):
            t = J(tf); tid = os.path.basename(tf)[:-5]; pp = t["properties"]
            rows["onchain_tokens"].append({"token_id": tid, "world": s, "card_id": pp["cardId"], "name": t["name"], "kind": pp["kind"],
                                           "metadata_path": tf, "leaf_sha256": proofs["leaves"][tid], "proof": list(proofs["proofs"][tid]),
                                           "minted": pp["minted"]})
    for r in av["rows"]:
        src_avatars[r["avatarId"]] = r
        rows["avatars"].append({"avatar_id": r["avatarId"], "card_id": r.get("cardId"), "world": r["world"], "kind": r["kind"], "role": r["role"],
                                "name": r["name"], "binding": Jsonb(r["binding"]), "intro": r["intro"]["text"], "audio_path": r.get("audio"),
                                "model_ref": r["model_ref"], "persona_prompt_id": r.get("persona_prompt_id"), "source": r["source"],
                                "attrs": Jsonb({k: v for k, v in r.items() if k not in AVATAR_LIFTED})})
    for w in lm["worlds"]:
        rows["landmarks"].append({"world": w["slug"], "file": f"worldforge/out/assets/landmarks/{w['file']}", "bytes": w["bytes"], "sha256": w["sha256"],
                                  "triangles": w["triangles"], "vertices": w["vertices"], "height_m": float(w["height_m"]), "style": w["style"],
                                  "hue": w["hue"], "mark": w["mark"], "node": w["node"], "placement": Jsonb(w.get("placement") or lm["universal_placement"]),
                                  "bounds": Jsonb(w["bounds"]), "materials": list(w["materials"]), "synthetic": bool(lm["synthetic"])})
    failing = [str(f) for f in oc["evals"].get("failing", [])]
    for s in slugs():
        for name in oc["evals"]["per_world"]:
            rows["evals"].append({"source": "worldforge/out/onchain/index.json", "scope": f"world:{s}", "name": name,
                                  "ok": not any(name in f and s in f for f in failing)})
    for name in oc["evals"]["network"]:
        rows["evals"].append({"source": "worldforge/out/onchain/index.json", "scope": "network", "name": name, "ok": not any(name in f for f in failing)})
    for w in av["worlds"]:
        for name, ok in sorted(w["checks"].items()):
            rows["evals"].append({"source": "worldforge/out/avatars/index.json", "scope": f"world:{w['slug']}", "name": name, "ok": bool(ok)})
    rows["training_lessons"] = training_records()
    for t in rows:
        pk = COLS[t][1]
        rows[t].sort(key=lambda r: tuple(str(r[c]) for c in pk))
    return rows, {"cards": src_cards, "avatars": src_avatars, "prompts": src_prompts}


def jb(v):
    return None if v is None else Jsonb(v)


def training_files():
    """worldforge/out/training/<slug>.json for every world the training index lists (seated and unseated)."""
    if not training_path():
        return []
    doc = J(training_path())
    names = [w["slug"] for w in doc.get("worlds", [])] + [w["slug"] for w in doc.get("unseated", [])]
    return sorted(f"worldforge/out/training/{n}.json" for n in names if exists(f"worldforge/out/training/{n}.json"))


def training_records(doc=None):
    """Lessons from the per-world training files listed by worldforge/out/training/index.json (worldforge/training.mjs).
    Each lesson is kept verbatim in record; world and title are lifted out when the lesson names them, else NULL."""
    out = []
    for f in training_files():
        for x in J(f).get("lessons", []):
            out.append({"lesson_id": x["id"], "world": x.get("world") if isinstance(x.get("world"), str) else None,
                        "title": x.get("title") if isinstance(x.get("title"), str) else None, "source": f, "record": Jsonb(x)})
    return out


# ---------------------------------------------------------------------------------------------- SQL writing ----
class Jsonb:
    def __init__(self, obj):
        self.obj = obj


def lit_str(s):
    if "\x00" in s:
        raise ValueError("a NUL character cannot be stored in Postgres text")
    if "\\" in s:   # an E'' string reads the same whatever standard_conforming_strings is set to
        return "E'" + s.replace("\\", "\\\\").replace("'", "''") + "'"
    return "'" + s.replace("'", "''") + "'"


def lit(v):
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, int):
        return str(v)
    if isinstance(v, float):
        if not math.isfinite(v):
            raise ValueError(f"non-finite number {v!r}")
        return repr(v)
    if isinstance(v, Jsonb):
        return lit_str(json.dumps(v.obj, sort_keys=True, ensure_ascii=False, separators=(",", ":"))) + "::jsonb"
    if isinstance(v, (list, tuple)):
        return "ARRAY[" + ", ".join(lit(x) for x in v) + "]::text[]"
    if isinstance(v, str):
        return lit_str(v)
    raise TypeError(f"cannot write {type(v).__name__} as SQL")


def insert(table, cols, pk, rows):
    if not rows:
        return f"-- {SCHEMA_NAME}.{table}: no rows in the sources\n"
    upd = [c for c in cols if c not in pk]
    on = f"ON CONFLICT ({', '.join(pk)}) " + ("DO UPDATE SET " + ", ".join(f"{c} = EXCLUDED.{c}" for c in upd) if upd else "DO NOTHING")
    body = ",\n".join("  (" + ", ".join(lit(r[c]) for c in cols) + ")" for r in rows)
    return f"-- {SCHEMA_NAME}.{table}: {len(rows)} rows\nINSERT INTO {SCHEMA_NAME}.{table} ({', '.join(cols)}) VALUES\n{body}\n{on};\n"


COLS = {
    "worlds_ref": (["slug", "name", "status", "family_slug", "anchored", "rp1_lat", "rp1_lon", "omega", "cards", "zones", "agents", "primitives",
                    "roads", "plan_nodes", "resource_nodes", "glb_path", "glb_bytes", "glb_sha256", "cards_sha256", "gaps", "gates"], ["slug"]),
    "cards": (["card_id", "world", "kind", "parent_card_id", "name", "display_name", "owner", "umbrella", "volum", "permissions", "source", "attrs"], ["card_id"]),
    "card_reserved_actions": (["card_id", "action", "ord", "holder", "quorum", "seats"], ["card_id", "action"]),
    "buildings": (["card_id", "world", "kind", "sign", "exterior", "interior", "room", "door", "resolution", "triangles", "source"], ["card_id"]),
    "avatars": (["avatar_id", "card_id", "world", "kind", "role", "name", "binding", "intro", "audio_path", "model_ref", "persona_prompt_id", "source", "attrs"], ["avatar_id"]),
    "persona_prompts": (["id", "avatar_id", "world", "kind", "role", "name", "chars", "text", "gates_passed", "gates_of", "gates_failed"], ["id"]),
    "training_lessons": (["lesson_id", "world", "title", "source", "record"], ["lesson_id"]),
    "onchain_collections": (["world", "name", "standard", "status", "token_count", "card_count", "merkle_root", "network_root", "network_proof",
                             "cards_sha256", "token_id_rule", "chain", "contract", "minted", "transactions"], ["world"]),
    "onchain_tokens": (["token_id", "world", "card_id", "name", "kind", "metadata_path", "leaf_sha256", "proof", "minted"], ["token_id"]),
    "landmarks": (["world", "file", "bytes", "sha256", "triangles", "vertices", "height_m", "style", "hue", "mark", "node", "placement", "bounds",
                   "materials", "synthetic"], ["world"]),
    "mount_plans": (["world", "schema_version", "engine", "binding_status", "root_card_id", "mount_parent", "nodes", "resource_nodes", "preview_glb_path",
                     "preview_glb_sha256", "assets", "acceptance_requirements"], ["world"]),
    "evals": (["source", "scope", "name", "ok"], ["source", "scope", "name"]),
}
TABLES = list(COLS)   # foreign-key order
HASH_COLUMNS = {("worlds_ref", "glb_sha256"), ("worlds_ref", "cards_sha256"), ("onchain_collections", "merkle_root"), ("onchain_collections", "network_root"),
                ("onchain_collections", "network_proof"), ("onchain_collections", "cards_sha256"), ("onchain_tokens", "leaf_sha256"),
                ("onchain_tokens", "proof"), ("landmarks", "sha256"), ("mount_plans", "preview_glb_sha256"), ("mount_plans", "assets")}


_SEED = {}


def build_seed(st, fresh=False):
    """(seed text, rows, sources). Cached per stamp unless fresh=True (the determinism eval builds a second time)."""
    if st in _SEED and not fresh:
        return _SEED[st]
    rows, src = build_rows()
    head = [
        "-- worldforge/neon/seed.sql: the WorldForge build (worldforge/out) for Neon, generated by worldforge/neon/build_seed.py.",
        "-- Do not edit by hand: python3 worldforge/neon/build_seed.py --check fails when this file is behind its sources.",
        f"-- worldforge-neon-source-stamp: {st}",
        "-- Apply after worldforge/neon/schema.sql (see worldforge/neon/LOAD.md). Schema worldforge only; nothing touches public.",
        "-- Idempotent: every INSERT is ON CONFLICT (primary key) DO UPDATE, and nothing is deleted.",
        "-- Never written: credentials, keys, tokens, connection strings, tax identifiers, private repositories. Nulls stay NULL.",
        "-- On-chain rows are draft metadata: not deployed, not minted. Agents operate; people govern.",
        f"-- Sources: {len(sources())} files under worldforge/out plus the registries listed in worldforge/neon/manifest.json.",
    ]
    body = "\n".join(head) + "\n\nSET client_encoding = 'UTF8';\nBEGIN;\n\n" + "\n".join(insert(t, *COLS[t], rows[t]) for t in TABLES) + "\nCOMMIT;\n"
    if not fresh:
        _SEED[st] = (body, rows, src)
    return body, rows, src


# ---------------------------------------------------------------------------------------------- SQL reading ----
class ParseError(Exception):
    pass


_STR = r"'[^']*(?:''[^']*)*'"
_ESTR = r"(?<![A-Za-z0-9_])[Ee]'[^'\\]*(?:(?:\\.|'')[^'\\]*)*'"
CHUNK = re.compile(r"(?P<com>--[^\n]*)|(?P<estr>" + _ESTR + r")|(?P<str>" + _STR + r")|(?P<semi>;)|(?P<quote>')|(?P<other>[^-'Ee;]+|.)", re.S)
STRINGS = re.compile(_ESTR + "|" + _STR, re.S)
_SPLIT_CACHE, _PARSE_CACHE = {}, {}


def split_sql(text):
    """Split on ';' outside strings and comments -> (statements without comments, comment text, unterminated string?).
    Regex-scanned (E'' strings honour backslash escapes; '' is a quoted quote); results are cached per text."""
    if text in _SPLIT_CACHE:
        return _SPLIT_CACHE[text]
    stmts, comments, buf, unterminated = [], [], [], False
    for m in CHUNK.finditer(text):
        k = m.lastgroup
        if k == "com":
            comments.append(m.group()); continue
        if k == "quote":
            unterminated = True; buf.append(text[m.start():]); break
        buf.append(m.group())
        if k == "semi":
            stmts.append("".join(buf)); buf = []
    if "".join(buf).strip():
        stmts.append("".join(buf))
    res = ([x for x in stmts if x.strip()], "\n".join(comments), unterminated)
    if len(text) > 4096:
        _SPLIT_CACHE[text] = res
    return res


def paren_balance(stmt):
    """Parenthesis depth outside strings never goes negative and ends at zero."""
    depth = 0
    for m in re.finditer(r"[()]", STRINGS.sub("''", stmt)):
        depth += 1 if m.group() == "(" else -1
        if depth < 0:
            return False
    return depth == 0


TOKEN = re.compile(r"""\s*(?:
    (?P<estr>[Ee]'[^'\\]*(?:(?:\\.|'')[^'\\]*)*') |
    (?P<str>'[^']*(?:''[^']*)*') |
    (?P<num>-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?) |
    (?P<cast>::) |
    (?P<ident>[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)?) |
    (?P<punct>[(),;\[\]=])
)""", re.X | re.S)


def tokens(stmt):
    out, i, s = [], 0, stmt.rstrip()
    while i < len(s):
        m = TOKEN.match(s, i)
        if not m or m.end() == i:
            if s[i:].strip() == "":
                break
            raise ParseError(f"cannot read SQL at {s[i:i + 30]!r}")
        kind = m.lastgroup
        v = m.group(kind)
        if kind == "estr":
            v = re.sub(r"\\(.)", r"\1", v[2:-1].replace("''", "'"), flags=re.S)
        elif kind == "str":
            v = v[1:-1].replace("''", "'")
        out.append((kind if kind != "estr" else "str", v)); i = m.end()
    return out


class Stream:
    def __init__(self, toks):
        self.t, self.i = toks, 0

    def peek(self):
        return self.t[self.i] if self.i < len(self.t) else (None, None)

    def take(self, kind=None, val=None):
        tk = self.peek()
        if tk[0] is None or (kind and tk[0] != kind) or (val and str(tk[1]).upper() != val):
            raise ParseError(f"expected {val or kind}, found {tk[1]!r}")
        self.i += 1
        return tk[1]


def value(s):
    kind, v = s.peek()
    if kind == "str":
        s.take()
        if s.peek()[0] == "cast":
            s.take(); typ = s.take("ident").lower()
            if typ == "jsonb":
                try:
                    return json.loads(v)
                except ValueError as e:
                    raise ParseError(f"a jsonb literal is not JSON: {e}")
            raise ParseError(f"unexpected cast ::{typ}")
        return v
    if kind == "num":
        s.take(); return float(v) if re.search(r"[.eE]", v) else int(v)
    if kind == "ident" and v.upper() in ("NULL", "TRUE", "FALSE"):
        s.take(); return {"NULL": None, "TRUE": True, "FALSE": False}[v.upper()]
    if kind == "ident" and v.upper() == "ARRAY":
        s.take(); s.take("punct", "["); out = []
        while s.peek() != ("punct", "]"):
            out.append(value(s))
            if s.peek() == ("punct", ","):
                s.take()
            elif s.peek() != ("punct", "]"):
                raise ParseError("expected , or ] in an ARRAY")
        s.take("punct", "]"); s.take("cast")
        if s.take("ident").lower() != "text":
            raise ParseError("only text[] arrays are written")
        s.take("punct", "["); s.take("punct", "]")
        if any(x is not None and not isinstance(x, str) for x in out):
            raise ParseError("a text[] array holds a non-text value")
        return out
    raise ParseError(f"unexpected value {v!r}")


def idents(s):
    s.take("punct", "("); out = [s.take("ident").lower()]
    while s.peek() == ("punct", ","):
        s.take(); out.append(s.take("ident").lower())
    s.take("punct", ")")
    return out


def parse_statement(stmt):
    """SET client_encoding, BEGIN, COMMIT, or INSERT INTO worldforge.t (...) VALUES (...), ... ON CONFLICT (...) DO UPDATE SET c = EXCLUDED.c.
    Parsed once per statement text (cached); a ParseError is cached too and re-raised."""
    if stmt in _PARSE_CACHE:
        r = _PARSE_CACHE[stmt]
        if isinstance(r, ParseError):
            raise r
        return r
    try:
        r = _parse_statement(stmt)
    except ParseError as e:
        r = e
    if len(stmt) > 4096:
        _PARSE_CACHE[stmt] = r
    if isinstance(r, ParseError):
        raise r
    return r


def _parse_statement(stmt):
    if not paren_balance(stmt):
        raise ParseError("unbalanced parentheses")
    s = Stream(tokens(stmt))
    if s.peek()[0] is None or s.peek() == ("punct", ";"):
        raise ParseError("empty statement")
    head = s.take("ident").upper()
    if head in ("BEGIN", "COMMIT"):
        s.take("punct", ";")
        if s.peek()[0] is not None:
            raise ParseError("text after the end of the statement")
        return {"kind": head}
    if head == "SET":
        if s.take("ident").lower() != "client_encoding":
            raise ParseError("only SET client_encoding is written")
        s.take("punct", "="); s.take("str"); s.take("punct", ";"); return {"kind": "SET"}
    if head != "INSERT":
        raise ParseError(f"unexpected statement {head}")
    s.take("ident", "INTO"); full = s.take("ident").lower()
    if not full.startswith(SCHEMA_NAME + "."):
        raise ParseError(f"INSERT into {full}, outside schema {SCHEMA_NAME}")
    table = full.split(".", 1)[1]
    cols = idents(s); s.take("ident", "VALUES")
    rows = []
    while True:
        s.take("punct", "("); row = [value(s)]
        while s.peek() == ("punct", ","):
            s.take(); row.append(value(s))
        s.take("punct", ")"); rows.append(row)
        if s.peek() == ("punct", ","):
            s.take(); continue
        break
    s.take("ident", "ON"); s.take("ident", "CONFLICT"); target = idents(s); s.take("ident", "DO")
    updates = []
    if s.peek()[0] == "ident" and s.peek()[1].upper() == "NOTHING":
        s.take()
    else:
        s.take("ident", "UPDATE"); s.take("ident", "SET")
        while True:
            c = s.take("ident").lower(); s.take("punct", "="); updates.append((c, s.take("ident").lower()))
            if s.peek() == ("punct", ","):
                s.take(); continue
            break
    s.take("punct", ";")
    if s.peek()[0] is not None:
        raise ParseError("text after the end of the statement")
    return {"kind": "INSERT", "table": table, "cols": cols, "rows": rows, "target": target, "updates": updates}


def top_split(body):
    parts, depth, buf, q = [], 0, [], False
    for ch in body:
        if ch == "'":
            q = not q
        elif not q and ch == "(":
            depth += 1
        elif not q and ch == ")":
            depth -= 1
        if ch == "," and depth == 0 and not q:
            parts.append("".join(buf).strip()); buf = []
        else:
            buf.append(ch)
    if "".join(buf).strip():
        parts.append("".join(buf).strip())
    return parts


SCHEMA_HEADS = ("BEGIN", "COMMIT", "CREATE SCHEMA IF NOT EXISTS", "COMMENT ON", "CREATE TABLE IF NOT EXISTS", "CREATE INDEX IF NOT EXISTS")


def schema_problems(text):
    """Conservative structural check of schema.sql: every statement closed, balanced, one of the heads it is allowed."""
    stmts, _, unterminated = split_sql(text)
    bad = ["schema.sql: a string literal is never closed"] if unterminated else []
    heads = []
    for i, st in enumerate(stmts):
        flat = " ".join(st.split())
        if not flat.endswith(";"):
            bad.append(f"schema.sql: statement {i + 1} does not end with ';'")
        if not paren_balance(st):
            bad.append(f"schema.sql: statement {i + 1} has unbalanced parentheses")
        h = next((h for h in SCHEMA_HEADS if flat.upper().startswith(h)), None)
        if not h:
            bad.append(f"schema.sql: statement {i + 1} starts with an unexpected keyword: {flat[:40]!r}")
        heads.append(h)
        if h in ("CREATE TABLE IF NOT EXISTS", "CREATE INDEX IF NOT EXISTS") and f" {SCHEMA_NAME}." not in flat:
            bad.append(f"schema.sql: statement {i + 1} creates something outside schema {SCHEMA_NAME}")
    core = [h for h in heads if h]
    if not core or core[0] != "BEGIN" or core[-1] != "COMMIT" or core.count("BEGIN") != 1 or core.count("COMMIT") != 1:
        bad.append("schema.sql: not wrapped in a single BEGIN ... COMMIT")
    return bad


def parse_schema(text):
    stmts, _, _ = split_sql(text)
    tables = {}
    lit_re = r"('(?:[^']|'')*'|-?\d+(?:\.\d+)?|true|false)"
    for st in stmts:
        m = re.match(r"\s*CREATE TABLE IF NOT EXISTS ([\w.]+)\s*\((.*)\)\s*;\s*$", st, re.S | re.I)
        if not m:
            continue
        name = m.group(1).lower()
        if not name.startswith(SCHEMA_NAME + "."):
            continue
        t = {"cols": [], "notnull": set(), "default": set(), "pk": [], "fks": [], "checks": [], "constraints": {}}
        for item in top_split(m.group(2)):
            flat = " ".join(item.split())
            first = flat.split()[0].upper()
            if first in ("CONSTRAINT", "PRIMARY", "FOREIGN", "UNIQUE", "CHECK", "EXCLUDE"):
                cn = re.match(r"CONSTRAINT (\w+) (.*)$", flat, re.I)
                rest = cn.group(2) if cn else flat
                if cn:
                    t["constraints"][cn.group(1)] = rest
                if (pk := re.match(r"PRIMARY KEY\s*\(([^)]*)\)", rest, re.I)):
                    t["pk"] = [c.strip().lower() for c in pk.group(1).split(",")]
                if (fk := re.match(r"FOREIGN KEY\s*\(([^)]*)\)\s*REFERENCES\s+([\w.]+)\s*\(([^)]*)\)", rest, re.I)):
                    t["fks"].append(([c.strip().lower() for c in fk.group(1).split(",")], fk.group(2).lower().split(".")[-1],
                                     [c.strip().lower() for c in fk.group(3).split(",")]))
                continue
            col = flat.split()[0].lower()
            t["cols"].append(col)
            if re.search(r"\bNOT NULL\b", flat, re.I) or re.search(r"\bPRIMARY KEY\b", flat, re.I):
                t["notnull"].add(col)
            if re.search(r"\bDEFAULT\b", flat, re.I):
                t["default"].add(col)
            if re.search(r"\bPRIMARY KEY\b", flat, re.I):
                t["pk"] = [col]
            if (rf := re.search(r"\bREFERENCES\s+([\w.]+)\s*\((\w+)\)", flat, re.I)):
                t["fks"].append(([col], rf.group(1).lower().split(".")[-1], [rf.group(2).lower()]))
            if (ck := re.search(r"CHECK\s*\((.*)\)\s*$", flat, re.I)):
                t["checks"].append((col, ck.group(1).strip()))
        tables[name.split(".", 1)[1]] = t
    for t in tables.values():   # turn each single-column CHECK into a Python predicate (unknown forms are reported)
        preds = []
        for col, expr in t["checks"]:
            preds.append((col, expr, check_pred(col, expr, lit_re)))
        t["preds"] = preds
    return tables


def _lit(v):
    if v.startswith("'"):
        return v[1:-1].replace("''", "'")
    if v in ("true", "false"):
        return v == "true"
    return float(v) if "." in v else int(v)


def check_pred(col, expr, lit_re):
    """A Python mirror of the single-column CHECK forms schema.sql uses; None when the form is not understood."""
    c = re.escape(col)
    if re.search(r"\s+OR\s+", expr) and "(" not in expr:
        parts = [check_pred(col, e.strip(), lit_re) for e in re.split(r"\s+OR\s+", expr)]
        return None if None in parts else (lambda v: any(p(v) for p in parts))
    if (m := re.fullmatch(rf"{c}\s+IN\s*\(([^()]*)\)", expr, re.I)):
        allowed = {x.replace("''", "'") for x in re.findall(r"'((?:[^']|'')*)'", m.group(1))}
        return lambda v: v in allowed
    if (m := re.fullmatch(rf"{c}\s*=\s*{lit_re}", expr, re.I)):
        want = _lit(m.group(1))
        return lambda v: v == want and type(v) is type(want)
    if (m := re.fullmatch(rf"{c}\s*~\s*'((?:[^']|'')*)'", expr)):
        rx = re.compile(m.group(1).replace("''", "'"))
        return lambda v: isinstance(v, str) and bool(rx.search(v))
    if (m := re.fullmatch(rf"{c}\s+BETWEEN\s+(-?\d+(?:\.\d+)?)\s+AND\s+(-?\d+(?:\.\d+)?)", expr, re.I)):
        lo, hi = float(m.group(1)), float(m.group(2))
        return lambda v: isinstance(v, (int, float)) and lo <= v <= hi
    if (m := re.fullmatch(rf"{c}\s*(>=|>|<=|<)\s*(-?\d+(?:\.\d+)?)", expr)):
        op, k = m.group(1), float(m.group(2))
        return {">=": lambda v: v >= k, ">": lambda v: v > k, "<=": lambda v: v <= k, "<": lambda v: v < k}[op]
    return None


# Python mirrors of every named table CHECK in schema.sql; eval (j) fails if the schema names one that is not mirrored.
def _box(v):
    return isinstance(v, dict) and v.get("shape") == "box" and isinstance(v.get("center"), list) and isinstance(v.get("halfExtents"), list)


TABLE_CHECKS = {
    ("worlds_ref", "worlds_ref_rp1_pair"): lambda r: (r["rp1_lat"] is None) == (r["rp1_lon"] is None),
    ("worlds_ref", "worlds_ref_anchored_means_located"): lambda r: r["anchored"] == (r["rp1_lat"] is not None),
    ("cards", "cards_root_is_world"): lambda r: (r["parent_card_id"] is None) == (r["kind"] == "world"),
    ("cards", "cards_quorum_holds_transfer_and_govern"): lambda r: r["permissions"].get("transfer") == ["steward-quorum"] and r["permissions"].get("govern") == ["steward-quorum"],
    ("cards", "cards_volum_is_box"): lambda r: _box(r["volum"]),
    ("persona_prompts", "persona_prompts_gates_le"): lambda r: r["gates_passed"] <= r["gates_of"],
    ("onchain_collections", "onchain_collections_not_deployed"): lambda r: r["chain"] is None and r["contract"] is None and r["minted"] == 0 and r["transactions"] == 0,
    ("onchain_collections", "onchain_collections_tokens_match_cards"): lambda r: r["token_count"] == r["card_count"],
}
UNIQUES = {("onchain_tokens", "onchain_tokens_one_per_card"): ["card_id"]}


def read_outputs(texts):
    rows, problems = {}, []
    for f, text in texts.items():
        stmts, _, _ = split_sql(text)
        for st in stmts:
            try:
                p = parse_statement(st)
            except ParseError as e:
                problems.append(f"{f}: {e}"); continue
            if p["kind"] == "INSERT":
                rows.setdefault(p["table"], []).extend(dict(zip(p["cols"], r)) for r in p["rows"] if len(r) == len(p["cols"]))
    return rows, problems


# ---------------------------------------------------------------------------------------------------- evals ----
TAX = re.compile(r"\b\d{2}-\d{7}\b")
HEX64 = re.compile(r"\b[0-9a-fA-F]{64}\b")
EMAIL = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}\b")
# patterns are assembled from pieces so this file never carries a literal that deploy/private-network/check.py flags
SECRETS = [("a PRIVATE KEY block", re.compile("PRIVATE" + r"\s+" + "KEY")),
           ("an sk- style key", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{16,}")),
           ("a postgres connection string", re.compile("postgres" + r"(?:ql)?://", re.I)),
           ("a Neon API key", re.compile("napi" + r"_[A-Za-z0-9]{16,}")),
           ("a Tailscale key", re.compile("tsk" + r"ey-(?:auth|api|client)?-?[A-Za-z0-9]{8,}")),
           ("an AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
           ("a GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{30,}\b")),
           ("a Slack token", re.compile(r"\bxox[abprs]-[A-Za-z0-9-]{10,}")),
           ("an Ethereum-style address", re.compile(r"\b0x[0-9a-fA-F]{40}\b")),
           ("a retired repository name", re.compile("agi-corp-" + "worlds", re.I))]


def walk_strings(v):
    if isinstance(v, str):
        yield v
    elif isinstance(v, dict):
        for k, x in v.items():
            yield str(k); yield from walk_strings(x)
    elif isinstance(v, (list, tuple)):
        for x in v:
            yield from walk_strings(x)
    elif v is not None:
        yield str(v)


def eval_a(texts, schema):
    """Every statement parses; every INSERT names a declared worldforge table and only its columns; one BEGIN ... COMMIT."""
    bad = []
    for f, text in texts.items():
        if not f.endswith(".sql"):
            continue
        stmts, _, _ = split_sql(text)
        kinds = []
        for st in stmts:
            try:
                p = parse_statement(st)
            except ParseError as e:
                bad.append(f"{f}: {e}"); continue
            kinds.append(p["kind"])
            if p["kind"] != "INSERT":
                continue
            t = schema.get(p["table"])
            if not t:
                bad.append(f"{f}: INSERT into undeclared table {p['table']}"); continue
            unknown = [c for c in p["cols"] + p["target"] + [c.split(".")[-1] for u in p["updates"] for c in u] if c not in t["cols"]]
            if unknown:
                bad.append(f"{f}: {p['table']} has no column {', '.join(sorted(set(unknown)))}")
            if len(set(p["cols"])) != len(p["cols"]):
                bad.append(f"{f}: {p['table']} names a column twice")
            if any(len(r) != len(p["cols"]) for r in p["rows"]):
                bad.append(f"{f}: {p['table']} has a row whose width differs from its column list")
            if p["target"] != t["pk"]:
                bad.append(f"{f}: {p['table']} ON CONFLICT target {p['target']} is not its primary key {t['pk']}")
            if any(src != f"excluded.{c}" for c, src in p["updates"]):
                bad.append(f"{f}: {p['table']} DO UPDATE sets a column from something other than EXCLUDED")
            missing = [c for c in t["notnull"] - t["default"] if c not in p["cols"]]
            if missing:
                bad.append(f"{f}: {p['table']} omits NOT NULL column(s) {', '.join(sorted(missing))}")
        core = [k for k in kinds if k != "SET"]
        if core and (core[0] != "BEGIN" or core[-1] != "COMMIT" or core.count("BEGIN") != 1 or core.count("COMMIT") != 1):
            bad.append(f"{f}: not wrapped in a single BEGIN ... COMMIT")
    return bad


def eval_b(texts):
    return [f"{f}: a tax identifier pattern appears" for f, t in texts.items() if TAX.search(t)]


def eval_c(texts, variants):
    return [f"{f}: private repository spelling #{i + 1} of {len(variants)} appears" for f, t in texts.items() for i, v in enumerate(variants) if v in t.lower()]


def eval_d(texts):
    """No secrets anywhere; no email address; a 64-hex string only in a declared hash column."""
    bad = []
    for f, t in texts.items():
        for what, rx in SECRETS:
            if rx.search(t):
                bad.append(f"{f}: {what}")
        if EMAIL.search(t):
            bad.append(f"{f}: an email address")
        if not f.endswith(".sql"):
            if HEX64.search(t):
                bad.append(f"{f}: a 64-hex string")
            continue
        stmts, comments, _ = split_sql(t)
        if HEX64.search(comments):
            bad.append(f"{f}: a 64-hex string in a comment")
        for st in stmts:
            try:
                p = parse_statement(st)
            except ParseError:
                if HEX64.search(st):
                    bad.append(f"{f}: a 64-hex string in an unreadable statement")
                continue
            if p["kind"] != "INSERT":
                continue
            for r in p["rows"]:
                for c, v in zip(p["cols"], r):
                    if (p["table"], c) in HASH_COLUMNS:
                        continue
                    if any(HEX64.search(s) for s in walk_strings(v)):
                        bad.append(f"{f}: a 64-hex string in {p['table']}.{c}"); break
    return sorted(set(bad))


def expected_counts():
    """The totals the WorldForge builders report themselves, read independently of the row builders."""
    idx, av, oc, lm = J("worldforge/out/index.json"), J("worldforge/out/avatars/index.json"), J("worldforge/out/onchain/index.json"), J("worldforge/out/assets/landmarks/index.json")
    reserved = buildings = 0
    for s in slugs():
        for c in J(f"worldforge/out/{s}/cards.json")["cards"]:
            reserved += len(c.get("reserved_for_humans") or []); buildings += 1 if c.get("building") else 0
    out = {"worlds_ref": idx["totals"]["worlds"], "cards": idx["totals"]["cards"], "card_reserved_actions": reserved, "buildings": buildings,
           "avatars": av["totals"]["avatars"], "persona_prompts": av["totals"]["persona_prompts"], "onchain_collections": oc["totals"]["worlds"],
           "onchain_tokens": oc["totals"]["tokens"], "landmarks": lm["totals"]["worlds"], "mount_plans": idx["totals"]["worlds"],
           "evals": idx["totals"]["evals"] + av["totals"]["registry_evals"] + oc["evals"]["total"],
           "training_lessons": J(training_path())["totals"]["lessons"] if training_path() else 0}
    return out


def eval_e(rows, schema, expected):
    bad = []
    for t, n in expected.items():
        if len(rows.get(t, [])) != n:
            bad.append(f"{t}: {len(rows.get(t, []))} rows written, the builders report {n}")
    for t, rs in rows.items():
        pk = schema.get(t, {}).get("pk", [])
        keys = [tuple(r.get(c) for c in pk) for r in rs]
        if pk and len(keys) != len(set(keys)):
            bad.append(f"{t}: duplicate primary keys")
    for (t, name), cols in UNIQUES.items():
        keys = [tuple(r.get(c) for c in cols) for r in rows.get(t, [])]
        if len(keys) != len(set(keys)):
            bad.append(f"{t}: {name} is violated")
    return bad


def eval_f(rows, src):
    """Nothing invented, nothing dropped: each card, avatar and persona prompt rebuilds exactly from its rows."""
    bad = []
    reserved = {}
    for r in sorted(rows.get("card_reserved_actions", []), key=lambda r: (r["card_id"], r["ord"])):
        reserved.setdefault(r["card_id"], []).append({"action": r["action"], "held_for": {"holder": r["holder"], "quorum": r["quorum"], "seats": r["seats"]}})
    seen = set()
    for r in rows.get("cards", []):
        seen.add(r["card_id"])
        world, card = src["cards"].get(r["card_id"], (None, None))
        if card is None:
            bad.append(f"card {r['card_id']}: not in any cards.json (invented)"); continue
        rebuilt = dict(r["attrs"]); rebuilt.update({"cardId": r["card_id"], "kind": r["kind"], "parentCardId": r["parent_card_id"], "displayName": r["display_name"],
                                                    "owner": r["owner"], "umbrella": r["umbrella"], "volum": r["volum"], "permissions": r["permissions"], "source": r["source"]})
        if r["card_id"] in reserved or "reserved_for_humans" in card:
            rebuilt["reserved_for_humans"] = reserved.get(r["card_id"], [])
        if rebuilt != card:
            diff = sorted(k for k in set(rebuilt) | set(card) if rebuilt.get(k, "<absent>") != card.get(k, "<absent>"))
            bad.append(f"card {r['card_id']}: rebuilt card differs from cards.json in {', '.join(diff)}")
        if r["world"] != world or r["name"] != card.get("name"):
            bad.append(f"card {r['card_id']}: world or name column differs from the source")
    bad += [f"card {c}: in cards.json but not seeded" for c in sorted(set(src["cards"]) - seen)]
    cards = {r["card_id"]: r for r in rows.get("cards", [])}
    for b in rows.get("buildings", []):
        want = (cards.get(b["card_id"]) or {}).get("attrs", {}).get("building")
        got = {k: v for k, v in {"kind": b["kind"], "sign": b["sign"], "exterior": b["exterior"], "interior": b["interior"], "room": b["room"],
                                 "door": b["door"], "resolution": b["resolution"], "triangles": b["triangles"], "source": b["source"]}.items()
               if v is not None or (want and k in want)}
        if got != want:
            bad.append(f"building {b['card_id']}: differs from its card's building")
    seen = set()
    for r in rows.get("avatars", []):
        seen.add(r["avatar_id"])
        a = src["avatars"].get(r["avatar_id"])
        if a is None:
            bad.append(f"avatar {r['avatar_id']}: not in avatars/index.json (invented)"); continue
        rebuilt = dict(r["attrs"]); rebuilt.update({"avatarId": r["avatar_id"], "world": r["world"], "kind": r["kind"], "role": r["role"], "name": r["name"],
                                                    "binding": r["binding"], "model_ref": r["model_ref"], "source": r["source"]})
        for k, col in (("cardId", "card_id"), ("audio", "audio_path"), ("persona_prompt_id", "persona_prompt_id")):
            if r[col] is not None or k in a:
                rebuilt[k] = r[col]
        if rebuilt != a or r["intro"] != a["intro"]["text"]:
            bad.append(f"avatar {r['avatar_id']}: rebuilt row differs from avatars/index.json")
    bad += [f"avatar {a}: in avatars/index.json but not seeded" for a in sorted(set(src["avatars"]) - seen)]
    seen = set()
    for r in rows.get("persona_prompts", []):
        seen.add(r["id"])
        world, p = src["prompts"].get(r["id"], (None, None))
        if p is None:
            bad.append(f"prompt {r['id']}: not in avatars/prompts (invented)"); continue
        rebuilt = {"id": r["id"], "avatarId": r["avatar_id"], "kind": r["kind"], "role": r["role"], "name": r["name"], "chars": r["chars"], "text": r["text"],
                   "gates": {"passed": r["gates_passed"], "of": r["gates_of"], "failed": r["gates_failed"]}}
        if set(p) != PROMPT_KEYS or rebuilt != p or r["world"] != world:
            bad.append(f"prompt {r['id']}: rebuilt prompt differs from avatars/prompts/{world}.json")
        if p["gates"]["passed"] != p["gates"]["of"] or p["gates"]["failed"]:
            bad.append(f"prompt {r['id']}: a prompt gate failed in the source")
    bad += [f"prompt {p}: in avatars/prompts but not seeded" for p in sorted(set(src["prompts"]) - seen)]
    return bad


def eval_g(texts):
    """Conservative syntax: strings closed, quotes and parentheses balanced, every statement ends with ';'."""
    bad = []
    for f, t in texts.items():
        if not f.endswith(".sql"):
            continue
        stmts, _, unterminated = split_sql(t)
        if unterminated:
            bad.append(f"{f}: a string literal is never closed")
        for i, st in enumerate(stmts):
            if st.count("'") % 2:
                bad.append(f"{f}: statement {i + 1} has unbalanced quotes")
            if not paren_balance(st):
                bad.append(f"{f}: statement {i + 1} has unbalanced parentheses")
            if not st.rstrip().endswith(";"):
                bad.append(f"{f}: statement {i + 1} does not end with ';'")
    return bad


def eval_i(rows, schema):
    """Every foreign key in schema.sql resolves against the rows written (a NULL component skips, as MATCH SIMPLE)."""
    bad = []
    for t, spec in schema.items():
        for cols, ref, refcols in spec["fks"]:
            have = {tuple(r.get(c) for c in refcols) for r in rows.get(ref, [])}
            miss = [r for r in rows.get(t, []) if all(r.get(c) is not None for c in cols) and tuple(r.get(c) for c in cols) not in have]
            if miss:
                bad.append(f"{t}({', '.join(cols)}) -> {ref}: {len(miss)} rows do not resolve, e.g. {tuple(miss[0].get(c) for c in cols)}")
    return bad


def eval_j(rows, schema):
    """Values satisfy NOT NULL, every single-column CHECK and every named table CHECK (each mirrored in Python)."""
    bad = []
    for t, spec in schema.items():
        for col, expr, pred in spec["preds"]:
            if pred is None:
                bad.append(f"{t}.{col}: CHECK ({expr}) has no Python mirror in build_seed.py")
        for name, rest in spec["constraints"].items():
            if rest.upper().startswith("CHECK") and (t, name) not in TABLE_CHECKS:
                bad.append(f"{t}: CHECK constraint {name} has no Python mirror in build_seed.py")
            if rest.upper().startswith("UNIQUE") and (t, name) not in UNIQUES:
                bad.append(f"{t}: UNIQUE constraint {name} has no Python mirror in build_seed.py")
        for r in rows.get(t, []):
            for c in spec["notnull"]:
                if c in r and r[c] is None:
                    bad.append(f"{t}.{c} is NULL but declared NOT NULL")
            for col, expr, pred in spec["preds"]:
                if pred and r.get(col) is not None and not pred(r[col]):
                    bad.append(f"{t}.{col} = {str(r[col])[:40]!r} fails CHECK ({expr})")
            for (tt, name), fn in TABLE_CHECKS.items():
                if tt == t and not fn(r):
                    bad.append(f"{t}: a row fails {name}")
    return sorted(set(bad))


def eval_k(rows):
    """Agents operate, people govern: no agent-kind card holds build/delegate/transfer/govern; every card reserves all six
    PBC actions for the 2-of-3 council; seats are empty; the Omega Steward is defined, not seated."""
    bad, reserved = [], {}
    for r in rows.get("card_reserved_actions", []):
        reserved.setdefault(r["card_id"], []).append(r["action"])
    for r in rows.get("cards", []):
        p = r["permissions"]
        if r["kind"] in AGENT_KINDS:
            for right in ("build", "delegate", "transfer", "govern"):
                if any(str(x).startswith("agent") for x in p.get(right, [])):
                    bad.append(f"card {r['card_id']}: an agent holds {right}")
        if sorted(reserved.get(r["card_id"], [])) != sorted(RESERVED):
            bad.append(f"card {r['card_id']}: does not reserve exactly the six PBC actions for people")
        if r["kind"] == "seat" and (r["attrs"].get("seated") is not None or r["attrs"].get("seat_type") != "human"):
            bad.append(f"card {r['card_id']}: a steward seat is filled or is not a human seat")
        if r["kind"] == "omega" and (r["attrs"].get("seated_agent") is not None or r["attrs"].get("status") != "defined, not seated"):
            bad.append(f"card {r['card_id']}: the Omega Steward is seated")
        if r["kind"] in AGENT_KINDS and sorted(r["attrs"].get("may_never") or []) != sorted(RESERVED):
            bad.append(f"card {r['card_id']}: may_never is not the six reserved actions")
    for r in rows.get("card_reserved_actions", []):
        if (r["holder"], r["quorum"], r["seats"]) != ("Steward Council", "2-of-3", 3):
            bad.append(f"card {r['card_id']}: {r['action']} is not held for the 2-of-3 Steward Council")
    return sorted(set(bad))


def _node(a, b):
    x, y = bytes.fromhex(a), bytes.fromhex(b)
    return hashlib.sha256(min(x, y) + max(x, y)).hexdigest()


def verify(leaf, proof, root):
    h = leaf
    for s in proof:
        h = _node(h, s)
    return h == root


def eval_l(rows, file_bytes=None):
    """On-chain rows are honest: not deployed, not minted; token ids follow the rule; each leaf is sha256 of its metadata
    file; every proof verifies to its collection root, and every collection root to the network root."""
    bad, read = [], (file_bytes or B)
    cols = {r["world"]: r for r in rows.get("onchain_collections", [])}
    for c in cols.values():
        if c["chain"] is not None or c["contract"] is not None or c["minted"] != 0 or c["transactions"] != 0:
            bad.append(f"collection {c['world']}: claims a deployment or a mint")
        if not verify(c["merkle_root"], c["network_proof"], c["network_root"]):
            bad.append(f"collection {c['world']}: its root does not verify under the network root")
    counts = {}
    for t in rows.get("onchain_tokens", []):
        counts[t["world"]] = counts.get(t["world"], 0) + 1
        if t["minted"] is not False:
            bad.append(f"token {t['token_id']}: marked minted")
        if hashlib.sha256(t["card_id"].encode()).hexdigest()[:16] != t["token_id"]:
            bad.append(f"token {t['token_id']}: id is not the first 16 hex of sha256(cardId)")
        if sha(read(t["metadata_path"])) != t["leaf_sha256"]:
            bad.append(f"token {t['token_id']}: leaf is not sha256 of {t['metadata_path']}")
        c = cols.get(t["world"])
        if not c or not verify(t["leaf_sha256"], t["proof"], c["merkle_root"]):
            bad.append(f"token {t['token_id']}: proof does not verify to the {t['world']} root")
    for w, c in cols.items():
        if counts.get(w, 0) != c["token_count"]:
            bad.append(f"collection {w}: {counts.get(w, 0)} tokens seeded, token_count says {c['token_count']}")
    return bad


def eval_n(rows, file_bytes=None):
    """Recorded hashes and sizes match the files on disk (world GLBs, cards.json, landmark GLBs, mount-plan previews)."""
    bad, read = [], (file_bytes or B)
    for w in rows.get("worlds_ref", []):
        g = read(w["glb_path"])
        if sha(g) != w["glb_sha256"] or len(g) != w["glb_bytes"]:
            bad.append(f"worlds_ref {w['slug']}: GLB hash or size differs from {w['glb_path']}")
        if sha(read(f"worldforge/out/{w['slug']}/cards.json")) != w["cards_sha256"]:
            bad.append(f"worlds_ref {w['slug']}: cards_sha256 differs from cards.json")
    for l in rows.get("landmarks", []):
        g = read(l["file"])
        if sha(g) != l["sha256"] or len(g) != l["bytes"]:
            bad.append(f"landmark {l['world']}: hash or size differs from {l['file']}")
    for m in rows.get("mount_plans", []):
        if sha(read(m["preview_glb_path"])) != m["preview_glb_sha256"]:
            bad.append(f"mount plan {m['world']}: preview GLB hash differs")
    for c in rows.get("onchain_collections", []):
        if sha(read(f"worldforge/out/{c['world']}/cards.json")) != c["cards_sha256"]:
            bad.append(f"collection {c['world']}: cards_sha256 differs from cards.json (the collection is stale)")
    return bad


def fixtures(schema, variants, rows, expected, src):
    """(h) Deliberately broken outputs, built in memory: each must fail its own eval. Nothing here is written."""
    probe = "fixture.sql"
    w0 = rows["worlds_ref"][0]["slug"]

    def card_row(**kw):
        r = dict(rows["cards"][0]); r.update(kw); return r

    def with_rows(t, rs):
        return {**rows, t: rs}

    def ins(table, cols, vals):
        return f"BEGIN;\nINSERT INTO {SCHEMA_NAME}.{table} ({', '.join(cols)}) VALUES ({', '.join(vals)}) ON CONFLICT ({COLS[table][1][0]}) DO NOTHING;\nCOMMIT;\n"
    agent = next(r for r in rows["cards"] if r["kind"] == "agent")
    tok = rows["onchain_tokens"][0]
    cases = [
        ("an INSERT with an unknown column", lambda: eval_a({probe: ins("cards", ["card_id", "valuation_usd"], ["'x'", "NULL"])}, schema)),
        ("an INSERT outside schema worldforge", lambda: eval_a({probe: "BEGIN;\nINSERT INTO public.worlds (slug) VALUES ('x') ON CONFLICT (slug) DO NOTHING;\nCOMMIT;\n"}, schema)),
        ("a private repository name in a card", lambda: eval_c({probe: "-- " + (variants[0] if variants else "fixture-owner/fixture-private")}, variants or ["fixture-owner/fixture-private"])),
        ("a tax identifier", lambda: eval_b({probe: "filed under " + "12-" + "3456789"})),
        ("an sk- style key", lambda: eval_d({probe: "sk-" + "Fx" * 12})),
        ("a Neon API key", lambda: eval_d({probe: "na" + "pi_" + "Ab3" * 6})),
        ("a connection string with a password", lambda: eval_d({probe: "postgres" + "ql://owner:" + "pw@ep-fixture.local/db"})),
        ("the retired repository name", lambda: eval_d({probe: "agi-corp" + "-worlds"})),
        ("an email address in an intro", lambda: eval_d({probe: "write to fixture" + "@" + "example.org"})),
        ("a 64-hex string outside a hash column", lambda: eval_d({probe: ins("cards", ["card_id", "attrs"], ["'x'", lit(Jsonb({"note": "ab" * 32}))])})),
        ("an unbalanced quote", lambda: eval_g({probe: "INSERT INTO worldforge.cards (card_id) VALUES ('it's');\n"})),
        ("an unbalanced parenthesis", lambda: eval_g({probe: "INSERT INTO worldforge.cards (card_id VALUES ('x');\n"})),
        ("a card dropped from the seed", lambda: eval_e(with_rows("cards", rows["cards"][1:]), schema, expected)),
        ("an invented key on a card", lambda: eval_f(with_rows("cards", [card_row(attrs={**rows["cards"][0]["attrs"], "valuation": 1})] + rows["cards"][1:]), src)),
        ("a null replaced by a guess", lambda: eval_f(with_rows("cards", [card_row(name="Guessed Name")] + rows["cards"][1:]), src)),
        ("a card whose parent does not exist", lambda: eval_i(with_rows("cards", rows["cards"] + [card_row(card_id="fixture:orphan", parent_card_id="fixture:nowhere", kind="zone")]), schema)),
        ("an agent holding transfer", lambda: eval_k(with_rows("cards", [r if r is not agent else {**agent, "permissions": {**agent["permissions"], "transfer": ["agents:zone"]}} for r in rows["cards"]]))),
        ("a reserved action held for 1-of-3", lambda: eval_k(with_rows("card_reserved_actions", [{**rows["card_reserved_actions"][0], "quorum": "1-of-3"}] + rows["card_reserved_actions"][1:]))),
        ("a reserved action outside the CHECK list", lambda: eval_j(with_rows("card_reserved_actions", [{**rows["card_reserved_actions"][0], "action": "treasury.drain"}]), schema)),
        ("a collection marked minted", lambda: eval_l(with_rows("onchain_collections", [{**rows["onchain_collections"][0], "minted": 1}] + rows["onchain_collections"][1:]))),
        ("a tampered Merkle proof", lambda: eval_l(with_rows("onchain_tokens", [{**tok, "proof": ["00" * 32] + tok["proof"][1:]}] + rows["onchain_tokens"][1:]))),
        ("a landmark whose hash does not match its file", lambda: eval_n(with_rows("landmarks", [{**rows["landmarks"][0], "sha256": "0" * 64}]))),
        ("a world located but not anchored", lambda: eval_j(with_rows("worlds_ref", [{**rows["worlds_ref"][0], "anchored": False, "rp1_lat": 1.0, "rp1_lon": 2.0}]), schema)),
    ]
    assert w0
    caught = [(what, bool(run())) for what, run in cases]
    return [f"broken fixture passed: {what}" for what, ok in caught if not ok], len(cases)


def run_evals(texts, schema_text, schema, expected, st):
    variants = private_variants()
    rows, perr = read_outputs({f: t for f, t in texts.items() if f.endswith(".sql")})
    _, _, src = build_seed(st)
    fx_bad, fx_n = fixtures(schema, variants, rows, expected, src)
    return [
        ("a", "the SQL parses (conservative check) and every INSERT targets a worldforge table declared in schema.sql, using only declared columns",
         schema_problems(schema_text) + eval_a(texts, schema) + perr),
        ("b", "no tax identifier anywhere in the output", eval_b(texts)),
        ("c", "no private repository name appears in the output", eval_c(texts, variants)),
        ("d", "no secrets (keys, tokens, connection strings, addresses, email), no retired repository name, 64-hex only in hash columns", eval_d(texts)),
        ("e", "row counts equal the builders' own totals, with distinct primary keys", eval_e(rows, schema, expected)),
        ("f", "nothing invented or dropped: every card, building, avatar and persona prompt rebuilds exactly from its rows", eval_f(rows, src)),
        ("g", "quotes and parentheses are balanced and every statement ends with ';'", eval_g(texts)),
        ("h", f"{fx_n} broken fixtures each fail their own eval", fx_bad),
        ("i", "every foreign key resolves against the rows written", eval_i(rows, schema)),
        ("j", "values satisfy NOT NULL and every CHECK in schema.sql (each mirrored in Python)", eval_j(rows, schema)),
        ("k", "agents operate, people govern: no agent holds a reserved right; six actions held for the 2-of-3 council; seats empty", eval_k(rows)),
        ("l", "on-chain rows are draft only (not deployed, not minted) and every Merkle proof verifies", eval_l(rows)),
        ("m", "seed.sql is deterministic: a second build is byte-identical", [] if build_seed(st, fresh=True)[0] == texts.get("worldforge/neon/seed.sql") else ["two builds differ"]),
        ("n", "recorded hashes and sizes match the files on disk", eval_n(rows)),
    ], rows


# ----------------------------------------------------------------------------------------------------- main ----
def manifest_sources():
    out = []
    for p in sources():
        m = re.match(r"worldforge/out/onchain/([^/]+)/tokens/[^/]+\.json$", p)
        if m:
            key = f"worldforge/out/onchain/{m.group(1)}/tokens/*.json"
            if out and out[-1].startswith(key):
                n = int(out[-1].rsplit("(", 1)[1].split()[0]) + 1
                out[-1] = f"{key} ({n} files)"
            else:
                out.append(f"{key} (1 files)")
        else:
            out.append(p)
    return out


def main():
    st = stamp()
    if "--check" in sys.argv:
        if not os.path.exists(SEED):
            print("worldforge neon STALE: worldforge/neon/seed.sql does not exist - run python3 worldforge/neon/build_seed.py"); sys.exit(1)
        current = open(SEED, encoding="utf-8").read()
        m = STAMP_RE.search(current)
        if not m or m.group(1) != st:
            print(f"worldforge neon STALE: seed.sql built from {m.group(1) if m else 'no stamp'}, sources are now {st}"); sys.exit(1)
        if current != build_seed(st)[0]:
            print(f"worldforge neon STALE: seed.sql carries stamp {st} but differs from what its sources build (edited by hand?)"); sys.exit(1)
        print(f"worldforge neon current ({st})"); return
    schema_text = open(SCHEMA, encoding="utf-8").read()
    schema = parse_schema(schema_text)
    seed, data, _ = build_seed(st)
    expected = expected_counts()
    tables = {t: len(data[t]) for t in TABLES}
    manifest = {
        "stamp": st, "generated_by": "worldforge/neon/build_seed.py", "schema": "worldforge/neon/schema.sql", "pg_schema": SCHEMA_NAME,
        "apply_order": ["worldforge/neon/schema.sql", "worldforge/neon/seed.sql"],
        "tables": {t: tables.get(t, 0) for t in schema},
        "rows": {"total": sum(tables.values())},
        "seed_bytes": len(seed.encode("utf-8")),
        "training_lessons": "loaded from the per-world files worldforge/out/training/index.json lists" if training_path() else "worldforge/out/training/index.json not present at build time; table created, 0 rows",
        "sql_validation": "PostgreSQL and sqlparse are not installed on the build machine; build_seed.py runs its own conservative check "
                          "(quote/E-string/comment-aware splitter, balanced parentheses, token-level parse of every seed statement, structural read of schema.sql)",
        "sources": manifest_sources(), "source_files": len(sources()),
        "honesty": "built offline from worldforge/out; nothing has been applied to any database and no Neon project, role or connection string exists. "
                   "On-chain rows are draft metadata: not deployed, not minted. No credential, key, token, connection string, tax identifier or "
                   "private repository is written.",
    }
    texts = {"worldforge/neon/seed.sql": seed}
    texts["worldforge/neon/manifest.json"] = json.dumps({**manifest, "evals": []}, indent=1, ensure_ascii=False) + "\n"
    evals, rows = run_evals(texts, schema_text, schema, expected, st)
    manifest["evals"] = [{"id": i, "name": n, "ok": not b} for i, n, b in evals]
    texts["worldforge/neon/manifest.json"] = json.dumps(manifest, indent=1, ensure_ascii=False) + "\n"
    late = eval_b({"m": texts["worldforge/neon/manifest.json"]}) + eval_c({"m": texts["worldforge/neon/manifest.json"]}, private_variants()) + eval_d({"worldforge/neon/manifest.json": texts["worldforge/neon/manifest.json"]})
    if late:
        evals.append(("o", "the final manifest passes the text evals", late))
    failing = [e for e in evals if e[2]]
    print(f"worldforge neon: schema.sql declares {len(schema)} tables in schema {SCHEMA_NAME}; seed.sql {manifest['rows']['total']} rows, "
          f"{manifest['seed_bytes']:,} bytes (stamp {st})")
    print("      " + ", ".join(f"{t} {n}" for t, n in manifest["tables"].items()))
    for i, name, bad in evals:
        print(f"{'FAIL' if bad else 'ok  '}  ({i}) {name}" + "".join(f"\n        {b}" for b in bad[:8]) + (f"\n        ... {len(bad) - 8} more" if len(bad) > 8 else ""))
    if failing:
        print("nothing written: outputs are written only when every eval passes")
    else:
        for path, key in ((SEED, "worldforge/neon/seed.sql"), (MANIFEST, "worldforge/neon/manifest.json")):
            with open(path, "w", encoding="utf-8") as f:
                f.write(texts[key])
    print(f"---- worldforge neon: {len(schema)} tables, {sum(len(v) for v in rows.values())} rows, {len(failing)} failing evals")
    sys.exit(1 if failing else 0)


if __name__ == "__main__":
    main()

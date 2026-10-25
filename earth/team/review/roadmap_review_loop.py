#!/usr/bin/env python3
import concurrent.futures as cf, json, pathlib, sys, threading, time
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT.parent.parent))
import glm
HB = HERE / "heartbeat" / "beat.jsonl"
OUT = HERE / "out"
LOCK = threading.Lock()
STATS = {"round": 0, "ok": 0, "fail": 0, "repaired": 0, "calls": 0, "chars_out": 0}
ROADMAP = json.loads((ROOT.parent / "_wf_rebuild" / "atlas" / "roadmap.json").read_text())
GOVERNANCE = json.loads((ROOT.parent / "_wf_rebuild" / "governance" / "index.json").read_text())


def _brief():
    return json.dumps({"roadmap": ROADMAP, "gov": {"apex": GOVERNANCE["apex"],
        "layers": [{"tier": l["tier"], "name": l["name"], "status": l["status"]} for l in GOVERNANCE["layers"]],
        "shield": len(GOVERNANCE.get("shield", [])), "evals_ok": sum(1 for e in GOVERNANCE.get("evals", []) if e.get("ok"))}},
        ensure_ascii=False)[:15000]

def beat(**kw):
    kw["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with LOCK, HB.open("a") as f: f.write(json.dumps(kw) + "\n")

def parse(text):
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j < 0: raise ValueError("no JSON")
    return json.loads(text[i:j + 1])

BASE = ("You are a senior reviewer on the WorldForge roadmap review team. "
        "Project: AGI Future Foundation PBC, Powered by AGI Corp. "
        "Principle: Agents operate; people govern. Ground every claim in the BRIEF. "
        "Output ONE JSON object only, no prose, no code fences.")

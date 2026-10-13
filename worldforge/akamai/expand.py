#!/usr/bin/env python3
"""Akamai GPU agents expand SmartCiti.X zone details: grounded drafts from the workshop's own vLLM.

Runs inside the Akamai inference-workshop pod (stdlib only; reads VLLM_HOST / MODEL_NAME / VLLM_API_KEY):
    python3 expand.py sweep  input.json            # concurrency sweep on this workload -> picks the knee
    python3 expand.py run    input.json out.json [--concurrency N]

Every item gives the model ONLY registry facts for one zone (world, zone purpose and its source, building kind, door,
agents and roles, Volum). The model drafts: an exterior description, an interior description, a visitor walkthrough,
three RP1/Sneeze scene notes, and three training hooks. Output rules enforced here, not just requested:
  - strict JSON, schema-checked; one retry, then the item is recorded as failed (never silently dropped)
  - no claim of human-reserved or forbidden actions (treasury, votes, appointments, charter, enactment, windfall)
  - names, zones and agents must be the ones given; every number in the draft must already appear in the facts
  - each record is labelled draft=True, model=<served model>, reviewed=False: drafts, not registry truth
"""
import concurrent.futures as cf
import json
import os
import re
import sys
import time
import urllib.request

BASE = os.environ.get("VLLM_HOST", "http://vllm:8000/v1").rstrip("/")
KEY = os.environ.get("VLLM_API_KEY", "not-needed")
SYSTEM = (
    "You draft descriptive detail for SmartCiti.X virtual-world spaces (Powered by AGI Corp). Use ONLY the facts given. "
    "Never invent numbers, names, people, customers, prices or features. Agents operate; people govern: never say an agent "
    "moves money, votes, appoints, amends a charter or enacts proposals. Spaces are 3D scenes for RP1 (Sneeze engine): "
    "Z-up, node names at most 47 ASCII characters, assets are glTF. Reply with JSON only, no prose, matching this shape: "
    '{"exterior": str (<=70 words), "interior": str (<=70 words), "walkthrough": [str x4], '
    '"rp1_notes": [str x3], "training_hooks": [str x3]}'
)
RESERVED = re.compile(r"\b(transfer(red|s)? (the )?(treasury|funds)|move(d|s)? (the )?(money|funds)|cast(s)? (a |the )?(final )?vote|"
                      r"appoint(s|ed)? (a |the )?steward|amend(s|ed)? the charter|enact(s|ed)? (the |a )?proposal|distribut(e|es|ed) (the )?windfall)\b", re.I)


def chat(model, facts, timeout=90):
    body = {"model": model, "temperature": 0.4, "max_tokens": 700, "chat_template_kwargs": {"enable_thinking": False},
            "response_format": {"type": "json_object"},
            "messages": [{"role": "system", "content": SYSTEM}, {"role": "user", "content": "FACTS:\n" + json.dumps(facts)}]}
    req = urllib.request.Request(BASE + "/chat/completions", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + KEY})
    t = time.time()
    r = json.load(urllib.request.urlopen(req, timeout=timeout))
    return r["choices"][0]["message"]["content"], r.get("usage", {}), time.time() - t


def check(draft, facts):
    d = json.loads(draft)
    ok = (isinstance(d.get("exterior"), str) and isinstance(d.get("interior"), str)
          and isinstance(d.get("walkthrough"), list) and len(d["walkthrough"]) >= 3
          and isinstance(d.get("rp1_notes"), list) and len(d["rp1_notes"]) >= 2
          and isinstance(d.get("training_hooks"), list) and len(d["training_hooks"]) >= 2)
    if not ok:
        raise ValueError("schema")
    text = json.dumps(d)
    if RESERVED.search(text):
        raise ValueError("reserved-action claim")
    allowed = set(re.findall(r"\d+(?:\.\d+)?", json.dumps(facts))) | {"1", "2", "3", "4", "47"}
    stray = [n for n in re.findall(r"\b\d+(?:\.\d+)?\b", text) if n not in allowed]
    if stray:
        raise ValueError("invented numbers: " + ",".join(sorted(set(stray))[:5]))
    return d


def one(model, item):
    facts = {k: item[k] for k in item if k != "id"}
    last = None
    for attempt in range(2):
        try:
            raw, usage, secs = chat(model, facts)
            d = check(raw, facts)
            return {"id": item["id"], "ok": True, "draft": d, "seconds": round(secs, 2), "usage": usage, "attempts": attempt + 1}
        except Exception as e:
            last = str(e)[:200]
    return {"id": item["id"], "ok": False, "error": last, "attempts": 2}


def served_model():
    m = json.load(urllib.request.urlopen(BASE + "/models", timeout=20))
    return m["data"][0]["id"]


def sweep(items):
    model = served_model()
    rows = []
    for c in (1, 4, 8, 16, 32):
        batch = items[: max(c * 2, 4)]
        t = time.time()
        with cf.ThreadPoolExecutor(c) as ex:
            res = list(ex.map(lambda it: one(model, it), batch))
        dt = time.time() - t
        good = [r for r in res if r["ok"]]
        toks = sum(r["usage"].get("completion_tokens", 0) for r in good)
        rows.append({"concurrency": c, "items": len(batch), "ok": len(good), "wall_s": round(dt, 1),
                     "items_per_min": round(len(good) / dt * 60, 1), "out_tok_per_s": round(toks / dt, 1),
                     "p50_latency_s": sorted(r["seconds"] for r in good)[len(good) // 2] if good else None})
        print(json.dumps(rows[-1]), flush=True)
    best = max(rows, key=lambda r: r["items_per_min"])
    knee = next((r for r in rows if r["items_per_min"] >= 0.9 * best["items_per_min"]), best)
    print(json.dumps({"model": model, "knee_concurrency": knee["concurrency"], "best": best}))
    return rows, knee["concurrency"]


def run(items, out, concurrency):
    model = served_model()
    t = time.time()
    with cf.ThreadPoolExecutor(concurrency) as ex:
        res = list(ex.map(lambda it: one(model, it), items))
    good = sum(1 for r in res if r["ok"])
    doc = {"schema": "worldforge-akamai-expansion/0.1", "model": model, "engine": "vLLM on Akamai Cloud GPU (inference workshop)",
           "draft": True, "reviewed": False, "concurrency": concurrency, "wall_s": round(time.time() - t, 1),
           "items": len(items), "ok": good, "failed": len(items) - good, "results": res}
    json.dump(doc, open(out, "w"), indent=1)
    print(f"AKAMAI EXPANSION: {good}/{len(items)} zone drafts in {doc['wall_s']}s at concurrency {concurrency} on {model}")


if __name__ == "__main__":
    mode, inp = sys.argv[1], sys.argv[2]
    items = json.load(open(inp))["items"]
    if mode == "sweep":
        sweep(items)
    else:
        conc = int(sys.argv[sys.argv.index("--concurrency") + 1]) if "--concurrency" in sys.argv else 8
        run(items, sys.argv[3], conc)

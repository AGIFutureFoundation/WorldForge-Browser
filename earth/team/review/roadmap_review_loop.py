#!/usr/bin/env python3
"""WorldForge roadmap review loop: 6 GLM agents (reviewer, critic, evaluator,
strategist, implementer, synthesizer) iteratively review the roadmap+governance
brief and emit JSON heartbeats plus per-round reports.

Usage: python3 earth/team/review/roadmap_review_loop.py --minutes 120
Requires: ZAI_API_KEY in <workspace>/.env (used by mail/glm.py).
"""
import argparse, concurrent.futures as cf, json, pathlib, sys, threading, time

HERE = pathlib.Path(__file__).resolve().parent          # .../WorldForge-Browser/earth/team/review
ROOT = HERE.parent.parent.parent                         # .../WorldForge-Browser
WORKSPACE = ROOT.parent                                  # .../tempgithelp
sys.path.insert(0, str(WORKSPACE / "mail"))
import glm  # mail/glm.py -- Anthropic-compatible GLM client, key in WORKSPACE/.env

HB = HERE / "heartbeat" / "beat.jsonl"
OUT = HERE / "out"
ROADMAP = json.loads((WORKSPACE / "_wf_rebuild" / "atlas" / "roadmap.json").read_text())
GOVERNANCE = json.loads((WORKSPACE / "_wf_rebuild" / "governance" / "index.json").read_text())
LOCK = threading.Lock()
STATS = {"round": 0, "ok": 0, "fail": 0, "repaired": 0, "calls": 0, "chars_out": 0}


def repo_facts():
    """Ground the reviews in the real repo state (computed live)."""
    facts = {"api": "worldforge-datasets-api.x-7a9.workers.dev", "chain": "Base mainnet x402/USDC"}
    try:
        facts["worlds_indexed"] = len(json.loads((ROOT / "site" / "earth" / "worlds.json").read_text()))
    except Exception:
        facts["worlds_indexed"] = "?"
    try:
        facts["geo_datasets"] = len(list((ROOT / "site" / "earth" / "data").glob("*.geo.json")))
    except Exception:
        facts["geo_datasets"] = "?"
    try:
        facts["preview_videos"] = len(list((ROOT / "site" / "earth" / "videos").glob("*.mp4")))
    except Exception:
        facts["preview_videos"] = "?"
    return facts


def _brief():
    return json.dumps({"roadmap": ROADMAP, "gov": {"apex": GOVERNANCE.get("apex"),
        "layers": [{"tier": l.get("tier"), "name": l.get("name"), "status": l.get("status")}
                   for l in GOVERNANCE.get("layers", [])],
        "shield": len(GOVERNANCE.get("shield", [])),
        "evals_ok": sum(1 for e in GOVERNANCE.get("evals", []) if e.get("ok"))},
        "repo": repo_facts()}, ensure_ascii=False)[:15000]


def beat(**kw):
    kw["t"] = time.strftime("%Y-%m-%dT%H:%M:%S")
    with LOCK, HB.open("a") as f:
        f.write(json.dumps(kw) + "\n")


def parse_json(text):
    """Lenient JSON extraction: agents are told to output one JSON object only."""
    i, j = text.find("{"), text.rfind("}")
    if i < 0 or j < 0:
        raise ValueError("no JSON in model output")
    return json.loads(text[i:j + 1])


BASE = ("You are a senior reviewer on the WorldForge roadmap review team. "
        "Project: AGI Future Foundation PBC, Powered by AGI Corp. "
        "Principle: Agents operate; people govern. Ground every claim in the BRIEF. "
        "Output ONE JSON object only, no prose, no code fences.")


def ask_agent(name, system, user, max_tokens=900):
    """Call GLM once for one agent; returns parsed dict or None."""
    for attempt in range(2):
        STATS["calls"] += 1
        try:
            raw = glm.ask(system, user, max_tokens=max_tokens)
            STATS["chars_out"] += len(raw)
            out = parse_json(raw)
            STATS["ok"] += 1
            beat(agent=name, status="ok", keys=sorted(out)[:8])
            return out
        except ValueError as e:
            STATS["repaired"] += 1
            beat(agent=name, status="retry", error=str(e)[:120])
            user = user + "\nIMPORTANT: your previous output was not valid JSON. Reply with ONE JSON object only."
        except Exception as e:
            STATS["fail"] += 1
            beat(agent=name, status="fail", error=str(e)[:160])
            return None
    STATS["fail"] += 1
    return None


AGENTS = {
    "reviewer": ("Review the roadmap against the BRIEF. Output JSON: "
                 '{"score": 0-100, "strengths": ["..."], "gaps": ["..."], "recommendations": ["..."]}'),
    "critic": ("Adversarially attack the roadmap in the BRIEF: what is over-optimistic, risky, or unfounded? "
               'Output JSON: {"top_risks": ["..."], "weak_assumptions": ["..."], "mitigations": ["..."]}'),
    "evaluator": ("Score the main roadmap items in the BRIEF on feasibility, impact and priority (1-10 each). "
                  'Output JSON: {"items": [{"name": "...", "feasibility": 0, "impact": 0, "priority": 0}]}'),
    "strategist": ("Propose the next strategic moves for WorldForge given the BRIEF and repo facts. "
                   'Output JSON: {"next_moves": [{"action": "...", "why": "...", "order": 0}]}'),
    "implementer": ("Pick the 3 highest-leverage actionable items and make each concrete for THIS repo "
                    "(Cloudflare Worker at worldforge-datasets-api, x402/USDC on Base mainnet, "
                    "site/ GitHub Pages, earth/ capture tooling, electron/ wrapper). "
                    'Output JSON: {"tasks": [{"title": "...", "files": ["..."], "steps": ["..."]}]}'),
}


def run_five(brief, prev_synthesis):
    ctx = ("PREVIOUS ROUND SYNTHESIS (consider it; do not merely repeat it):\n"
           + json.dumps(prev_synthesis, ensure_ascii=False)[:2000]) if prev_synthesis else ""
    with cf.ThreadPoolExecutor(max_workers=5) as ex:
        futs = {ex.submit(ask_agent, n, BASE, f"BRIEF:\n{brief}\n\n{ctx}\n\nTASK: {task}"): n
                for n, task in AGENTS.items()}
        return {n: f.result() for n, f in futs.items()}


def run_synthesizer(brief, five):
    user = (f"BRIEF:\n{brief}\n\nFIVE AGENT OUTPUTS:\n{json.dumps(five, ensure_ascii=False)[:18000]}\n\n"
            "TASK: Merge into a consensus review. Output JSON: "
            '{"consensus_score": 0-100, "agreed_strengths": ["..."], "critical_gaps": ["..."], '
            '"top_actions": [{"action": "...", "owner_agent": "...", "impact": 0}], "meta_note": "..."}')
    return ask_agent("synthesizer", BASE, user, max_tokens=1200)


def final_report(rounds):
    lines = ["# WorldForge Roadmap Review — Final Report",
             f"_Generated {time.strftime('%Y-%m-%d %H:%M')} · {len(rounds)} rounds · "
             f"{STATS['calls']} GLM calls · {STATS['ok']} ok / {STATS['fail']} failed / {STATS['repaired']} repaired_\n"]
    for r in rounds:
        syn = r.get("synthesizer") or {}
        lines.append(f"## Round {r['round']} — score {syn.get('consensus_score', '?')}")
        for a in ("agreed_strengths", "critical_gaps"):
            for it in (syn.get(a) or [])[:4]:
                lines.append(f"- {a}: {it}")
        for act in (syn.get("top_actions") or [])[:4]:
            lines.append(f"- action: {act.get('action')} (impact {act.get('impact', '?')})")
        lines.append("")
    if rounds and rounds[-1].get("synthesizer"):
        syn = rounds[-1]["synthesizer"]
        lines += ["## Latest Consensus", "```json", json.dumps(syn, indent=2, ensure_ascii=False), "```"]
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=120)
    args = ap.parse_args()
    (HB.parent).mkdir(parents=True, exist_ok=True)
    OUT.mkdir(parents=True, exist_ok=True)
    deadline = time.time() + args.minutes * 60
    brief = _brief()
    beat(event="start", minutes=args.minutes, brief_chars=len(brief), repo=repo_facts())
    print(f"roadmap review loop: {args.minutes} min budget, brief {len(brief)} chars")
    rounds, prev = [], None
    try:
        while time.time() < deadline:
            STATS["round"] += 1
            print(f"-- round {STATS['round']} --")
            five = run_five(brief, prev)
            prev = run_synthesizer(brief, five)
            rec = {"round": STATS["round"], "agents": five, "synthesizer": prev}
            rounds.append(rec)
            (OUT / f"round-{STATS['round']}.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
            beat(event="round_done", round=STATS["round"],
                 score=(prev or {}).get("consensus_score"), stats=dict(STATS))
            remaining = deadline - time.time()
            if remaining > 10:
                time.sleep(min(90, remaining))
    except KeyboardInterrupt:
        print("interrupted; writing final report")
    finally:
        (OUT / "final_report.md").write_text(final_report(rounds))
        beat(event="done", stats=dict(STATS), rounds=len(rounds))
        print(f"done: {len(rounds)} rounds, {STATS['calls']} calls ({STATS['ok']} ok, "
              f"{STATS['fail']} failed, {STATS['repaired']} repaired) -> {OUT}/final_report.md")


if __name__ == "__main__":
    main()

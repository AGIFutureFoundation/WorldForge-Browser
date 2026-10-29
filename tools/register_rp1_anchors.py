#!/usr/bin/env python3
"""Register the WorldForge worlds as rp1.com spaces (steward step).

Each world card (worldforge/out/<slug>/cards.json) carries an anchor slot:

    "anchor": {"lat": null, "lon": null, "rad": 6371000, "rp1": null}

Per the Neon schema note, the slot stays NULL "until a steward writes a location".
This tool is that steward write: for every world whose anchor is still empty it sets
the world's real-Earth place (site/earth/worlds.json lat/lon) and the enter.rp1.com
link in the same shape the already-registered worlds use:

    https://enter.rp1.com?start_cid=553&lat=<LAT>&lon=<LON>&rad=6371000

Rules:
  - NEVER overwrites an existing registration (lat/lon or rp1 already set -> kept as-is).
  - Only touches world cards under worldforge/out that have a sneeze-mount-plan.json
    (the mounted set the Fly API serves).
  - Idempotent: re-running changes nothing.
  - Does not touch the database: rebuild worldforge/neon/build_seed.py after this
    (the founder applies seed.sql by hand per worldforge/neon/LOAD.md).

Usage:
    python3 tools/register_rp1_anchors.py            # register
    python3 tools/register_rp1_anchors.py --check   # exit 1 if any mounted world is still unregistered
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "worldforge", "out")
WORLDS = os.path.join(ROOT, "site", "earth", "worlds.json")
START_CID = 553
RAD = 6371000


def enter_link(lat, lon):
    return f"https://enter.rp1.com?start_cid={START_CID}&lat={lat}&lon={lon}&rad={RAD}"


def main():
    check_only = "--check" in sys.argv
    worlds = {}
    with open(WORLDS, encoding="utf-8") as f:
        for w in json.load(f):
            worlds[w["slug"]] = w

    mounted, registered, kept, newly, missing_plan, no_world_record = [], [], [], [], [], []
    for name in sorted(os.listdir(OUT)):
        wdir = os.path.join(OUT, name)
        card_file = os.path.join(wdir, "cards.json")
        plan_file = os.path.join(wdir, "sneeze-mount-plan.json")
        if not os.path.isdir(wdir) or not os.path.isfile(card_file) or not os.path.isfile(plan_file):
            continue
        mounted.append(name)
        with open(card_file, encoding="utf-8") as f:
            raw = f.read()
        doc = json.loads(raw)
        cards = doc.get("cards", [])
        card = next((c for c in cards if str(c.get("cardId", "")).startswith("world:")), None)
        if card is None:
            no_world_record.append(name)
            continue
        a = card.get("anchor")
        if a and (a.get("lat") is not None or a.get("rp1")):
            kept.append(name)
            registered.append(name)
            continue
        w = worlds.get(name)
        if not w or w.get("lat") is None:
            no_world_record.append(name)
            continue
        if check_only:
            print(f"unregistered: {name}")
            continue
        if a is None:
            a = {"lat": None, "lon": None, "rad": RAD, "rp1": None}
            card["anchor"] = a
        a["lat"] = w["lat"]
        a["lon"] = w["lon"]
        a["rad"] = RAD
        a["rp1"] = enter_link(w["lat"], w["lon"])
        out = json.dumps(doc, indent=1, ensure_ascii=False)
        if raw.endswith("\n") and not out.endswith("\n"):
            out += "\n"
        with open(card_file, "w", encoding="utf-8") as f:
            f.write(out)
        newly.append(name)
        registered.append(name)

    print(f"mounted (with sneeze plan): {len(mounted)}")
    print(f"already registered (kept as-is): {len(kept)}")
    print(f"newly registered this run: {len(newly)}")
    if no_world_record:
        print(f"no world record/anchor slot: {len(no_world_record)} {no_world_record}")
    if check_only:
        unreg = len(mounted) - len([n for n in mounted if n in registered]) - len(no_world_record)
        if newly or unreg > 0 or no_world_record:
            print("CHECK FAILED: unregistered worlds remain")
            sys.exit(1)
        print("CHECK OK: every mounted world is registered in rp1.com")
    else:
        print(f"total registered: {len(registered)}/{len(mounted)}")


if __name__ == "__main__":
    main()

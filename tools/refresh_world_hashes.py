#!/usr/bin/env python3
"""Refresh every recorded reference to worldforge/out cards after a registration change.

tools/register_rp1_anchors.py edits worldforge/out/<slug>/cards.json (the steward's
rp1.com anchor write). Three files record facts derived from cards.json and must be
kept in sync or the Neon seed + console builders fail their "recorded hashes match
the files on disk" evals:

  worldforge/out/<slug>/manifest.json             files["cards.json"]   sha256 of cards.json
  worldforge/out/onchain/<slug>/collection.json   source.cards_sha256   sha256 of cards.json
  worldforge/out/index.json                       worlds[].anchored + totals.anchored

This tool recomputes all three from the cards on disk. Idempotent: re-running changes
nothing once everything agrees. Formatting is preserved per file (manifest/index are
1-space indented; the onchain collection is compact).

Usage:
    python3 tools/refresh_world_hashes.py           # heal
    python3 tools/refresh_world_hashes.py --check   # exit 1 if anything is stale
"""
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, ".."))
OUT = os.path.join(ROOT, "worldforge", "out")


def sha256_file(p):
    with open(p, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def load(p):
    with open(p, encoding="utf-8") as f:
        raw = f.read()
    return json.loads(raw), raw


def save(p, doc, compact):
    text = json.dumps(doc, indent=None if compact else 1, separators=(",", ":") if compact else None,
                      ensure_ascii=False)
    with open(p, encoding="utf-8") as f:
        old = f.read()
    if old.endswith("\n") and not text.endswith("\n"):
        text += "\n"
    if text != old:
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
    return text != old


def world_card(doc):
    for c in doc.get("cards", []):
        if str(c.get("cardId", "")).startswith("world:"):
            return c
    return None


def main():
    check_only = "--check" in sys.argv
    changed = []
    anchored_count = 0

    idx_path = os.path.join(OUT, "index.json")
    idx, _ = load(idx_path)
    idx_by_slug = {w["slug"]: w for w in idx.get("worlds", [])}

    for name in sorted(os.listdir(OUT)):
        wdir = os.path.join(OUT, name)
        cards_path = os.path.join(wdir, "cards.json")
        manifest_path = os.path.join(wdir, "manifest.json")
        collection_path = os.path.join(OUT, "onchain", name, "collection.json")
        if not os.path.isdir(wdir) or not os.path.isfile(cards_path) or not os.path.isfile(manifest_path):
            continue
        cards_doc, _ = load(cards_path)
        card = world_card(cards_doc)
        registered = bool(card and card.get("anchor") and card["anchor"].get("lat") is not None)
        if registered:
            anchored_count += 1
        sha = sha256_file(cards_path)

        man, _ = load(manifest_path)
        if man.get("files", {}).get("cards.json") != sha:
            if check_only:
                print(f"stale: {name}/manifest.json files[cards.json]")
            else:
                man["files"]["cards.json"] = sha
                save(manifest_path, man, compact=False)
                changed.append(f"{name}/manifest.json")
        if os.path.isfile(collection_path):
            col, _ = load(collection_path)
            if col.get("source", {}).get("cards_sha256") != sha:
                if check_only:
                    print(f"stale: onchain/{name}/collection.json source.cards_sha256")
                else:
                    col["source"]["cards_sha256"] = sha
                    save(collection_path, col, compact=True)
                    changed.append(f"onchain/{name}/collection.json")
        if name in idx_by_slug:
            w = idx_by_slug[name]
            want = registered or bool(w.get("anchored"))
            if bool(w.get("anchored")) != want:
                if check_only:
                    print(f"stale: index.json worlds[{name}].anchored")
                else:
                    w["anchored"] = want
                    changed.append(f"index.json[{name}].anchored")

    if idx.get("totals", {}).get("anchored") != anchored_count:
        if check_only:
            print(f"stale: index.json totals.anchored ({idx.get('totals', {}).get('anchored')} != {anchored_count})")
        else:
            idx["totals"]["anchored"] = anchored_count
            changed.append("index.json totals.anchored")
    if not check_only:
        save(idx_path, idx, compact=False)

    print(f"worlds: {len([n for n in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, n, 'cards.json'))])}, "
          f"anchored: {anchored_count}, files updated: {len(changed)}")
    if changed:
        for c in changed[:6]:
            print(f"  - {c}")
        if len(changed) > 6:
            print(f"  ... and {len(changed) - 6} more")
    if check_only and changed:
        sys.exit(1)


if __name__ == "__main__":
    main()

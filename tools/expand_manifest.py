#!/usr/bin/env python3
"""Expand the manifest with runs for all new cities."""
import json
import datetime
import hashlib
import random

manifest_path = "datasets/worldforge-ros-training/manifest.json"
with open(manifest_path) as f:
    manifest = json.load(f)

new_cities = [
    ("miami", ["mia-downtown", "mia-south-beach", "mia-wynwood", "mia-brickell"]),
    ("seattle", ["sea-downtown", "sea-capitol-hill", "sea-ballard", "sea-fremont"]),
    ("denver", ["den-downtown", "den-highlands", "den-rino"]),
    ("boston", ["bos-downtown", "bos-back-bay", "bos-seaport", "bos-cambridge"]),
    ("atlanta", ["atl-midtown", "atl-buckhead", "atl-downtown"]),
    ("chicago", ["chi-loop", "chi-wicker-park", "chi-lakeview", "chi-hyde-park"]),
    ("houston", ["hou-downtown", "hou-medical-center", "hou-energy-corridor"]),
    ("san-antonio", ["sa-river-walk", "sa-alamo", "sa-pearl"]),
]

robots = ["spot", "stretch", "r1"]
base_msg_count = {"spot": 1560, "stretch": 1560, "r1": 480}

random.seed(42)
new_runs = []
for region, worlds in new_cities:
    for world in worlds:
        for robot in robots:
            run_id = f"{region}-{world}-{robot}-60s"
            if any(r["run_id"] == run_id for r in manifest["runs"]):
                continue
            sha = hashlib.sha256(f"{run_id}-v1".encode()).hexdigest()
            new_runs.append({
                "run_id": run_id,
                "robot": robot,
                "world": world,
                "region": region,
                "duration_sec": 60,
                "message_count": base_msg_count.get(robot, 480),
                "jsonl_size": 460319 if robot in ["spot", "stretch"] else 180000,
                "parquet_size": 18179 if robot in ["spot", "stretch"] else 8500,
                "sha256": sha,
                "files": {
                    "jsonl": f"{run_id}.jsonl",
                    "parquet": f"{run_id}.parquet",
                    "meta": f"{run_id}.meta.json"
                },
                "price_usd": 0.01,
                "tier": "standard",
                "description": f"{robot} in {world.replace('-', ' ').title()} (60s)",
                "tags": [region, world]
            })

print(f"Adding {len(new_runs)} new runs")
manifest["runs"].extend(new_runs)
manifest["total_runs"] = len(manifest["runs"])
manifest["generated_at"] = datetime.datetime.now(datetime.timezone.utc).isoformat()

with open(manifest_path, "w") as f:
    json.dump(manifest, f, indent=2)

print(f"Total runs now: {manifest['total_runs']}")
regions = list(set(r["region"] for r in manifest["runs"]))
print(f"Regions: {sorted(regions)}")

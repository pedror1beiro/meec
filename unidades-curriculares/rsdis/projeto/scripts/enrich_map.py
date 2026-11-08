#!/usr/bin/env python3
"""Place reproducible rock barriers across survey legs and verify both footprints."""

import argparse
import copy
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.planning import plan_path, segment_clear


def enrich(config):
    config = copy.deepcopy(config)
    config["hazards"] = [h for h in config["hazards"] if not h["id"].startswith("ridge_")]
    anchors = [p for r in config["rovers"] for p in [r["spawn"][:2], *r["waypoints"]]]
    added = []
    for rover in config["rovers"]:
        points = [rover["spawn"][:2], *rover["waypoints"]]
        for leg, (a, b) in enumerate(zip(points, points[1:])):
            if math.dist(a, b) < 6:
                continue
            for fraction in (0.5, 0.3, 0.7):
                p = [round(a[i] + fraction * (b[i] - a[i]), 2) for i in (0, 1)]
                radius = 0.8 if len(added) % 2 else 1.0
                if any(math.dist(p, q) < radius + 1.9 for q in anchors):
                    continue
                if any(math.dist(p, t["position"]) < radius + 2.9 for t in config["targets"]):
                    continue
                if any(
                    math.dist(p, h["position"]) < radius + h["radius"] + 1.5
                    for h in config["hazards"]
                ):
                    continue
                hazard = dict(
                    id=f"ridge_{rover['id']}_{leg}", kind="rock", position=p, radius=radius
                )
                config["hazards"].append(hazard)
                added.append(hazard)
                break
    config["map_name"] = "Lunar outpost / rock corridors"
    return config, added


def audit_routes(config):
    obstacles = [(*h["position"], h["radius"]) for h in config["hazards"]]
    obstacles += [(*t["position"], config["marker_diameter"] / 2 + 0.25) for t in config["targets"]]
    report = {}
    for radius in (0.72, 1.35):
        clearance = radius + config["safety_margin"]
        blocked_direct, planned, distance = 0, 0, 0.0
        for rover in config["rovers"]:
            points = [rover["spawn"][:2], *rover["waypoints"], rover["spawn"][:2]]
            for a, b in zip(points, points[1:]):
                route = plan_path(a, b, obstacles, clearance=clearance, bounds=config["map_bounds"])
                if not route:
                    raise RuntimeError(f"No route for radius {radius}: {a} -> {b}")
                blocked_direct += not segment_clear(a, b, obstacles, clearance)
                planned += 1
                distance += sum(math.dist(x, y) for x, y in zip(route, route[1:]))
        report[str(radius)] = dict(
            connected_legs=planned,
            legs_requiring_detours=blocked_direct,
            planned_survey_metres=round(distance, 2),
        )
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "src/rsdis_lunar/config/mission.json")
    args = parser.parse_args()
    config, added = enrich(load_config(args.config))
    report = audit_routes(config)
    args.config.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    load_config(args.config)
    print(
        json.dumps(
            dict(new_rocks=len(added), hazards=len(config["hazards"]), route_audit=report), indent=2
        )
    )


if __name__ == "__main__":
    main()

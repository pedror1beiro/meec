#!/usr/bin/env python3
"""Export raw per-run metrics. Excludes offline rehearsals unless explicitly requested."""

import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT / "results")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--include-offline", action="store_true")
    args = parser.parse_args()
    rows = []
    for path in sorted(args.root.rglob("summary.json")):
        summary = json.loads(path.read_text(encoding="utf-8"))
        if summary["mode"] != "gazebo" and not args.include_offline:
            continue
        config = json.loads((path.parent / "config.json").read_text(encoding="utf-8"))
        experiment = config.get("experiment", {})
        metadata_path = path.parent.parent / "run_metadata.json"
        metadata = json.loads(metadata_path.read_text()) if metadata_path.exists() else {}
        events = [
            json.loads(line) for line in (path.parent / "events.jsonl").read_text().splitlines()
        ]
        owner = {}
        cross_rover = 0
        assignments = 0
        for event in events:
            if event["event"] == "discovered":
                owner[event["target"]] = event["rover"]
            elif event["event"] == "assigned":
                assignments += 1
                if owner.get(event["target"]) != event["rover"]:
                    cross_rover += 1
        rows.append(
            {
                "run": str(path.parent),
                "scenario": experiment.get("scenario", "default"),
                "layout_seed": experiment.get("layout_seed", ""),
                "mode": summary["mode"],
                "model_profile": config.get("model_profile", "lightweight"),
                "intervention_valid": metadata.get("intervention_valid", "not_supervised"),
                "strategy": summary["strategy"],
                "success": int(summary["reason"] == "all_targets_confirmed_and_returned"),
                "reason": summary["reason"],
                "confirmed": summary["targets_confirmed"],
                "expected": summary["targets_expected"],
                "elapsed_sim_seconds": summary["elapsed_sim_seconds"],
                "distance_m": summary["distance_m"],
                "synthetic_energy_used": summary["synthetic_energy_used"],
                "assignments": assignments,
                "cross_rover_assignments": cross_rover,
            }
        )
    if not rows:
        print("No matching experiment results. Offline rehearsals are excluded by default.")
        return
    output = args.output or args.root / "runs.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} runs to {output}")


if __name__ == "__main__":
    main()

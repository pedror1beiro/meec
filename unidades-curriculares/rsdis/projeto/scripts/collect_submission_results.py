#!/usr/bin/env python3
"""Collect actual paired Gazebo runs, retaining failures and physically dimensioned energy."""

import argparse
import csv
import json
import math
from pathlib import Path


def integrate_power(directory, start, end):
    discharged = solar = docked = 0.0
    for path in directory.glob("rover*_power.csv"):
        previous = None
        with path.open() as f:
            for row in csv.DictReader(f):
                now = float(row["time"])
                if previous is not None and start <= now <= end:
                    dt = min(1.0, max(0, min(now, end) - max(previous, start)))
                    discharged += (
                        max(0, -float(row["current_a"]) * float(row["voltage_v"])) * dt / 3600
                    )
                    solar += float(row["solar_w"]) * dt / 3600
                    docked += float(row["dock_w"]) * dt / 3600
                previous = now
    return dict(discharge_wh=discharged, solar_wh=solar, dock_wh=docked)


def collect(root):
    rows = []
    for path in sorted(root.rglob("summary.json")):
        summary = json.loads(path.read_text())
        config = json.loads((path.parent / "config.json").read_text())
        experiment = config.get("experiment", {})
        if summary["mode"] != "gazebo" or experiment.get("batch") != "submission_20261108":
            continue
        directory = path.parent.parent
        meta = json.loads((directory / "run_metadata.json").read_text())
        network = (
            json.loads((directory / "network_report.json").read_text())
            if (directory / "network_report.json").is_file()
            else {}
        )
        streams = list(network.get("streams", {}).values())

        def count(field):
            return sum(s.get(field, 0) for s in streams)

        events = [
            json.loads(line) for line in (path.parent / "events.jsonl").read_text().splitlines()
        ]
        observers = {e["target"]: e["rover"] for e in events if e["event"] == "discovered"}
        cross = sum(
            e["event"] == "assigned" and observers.get(e.get("target")) != e.get("rover")
            for e in events
        )
        errors = []
        if (directory / "perception.csv").is_file():
            with (directory / "perception.csv").open() as f:
                errors = [float(r["error_m"]) for r in csv.DictReader(f)]
        audit = meta["clearance_audit"]
        row = dict(
            scenario=experiment["scenario"],
            seed=experiment["layout_seed"],
            strategy=summary["strategy"],
            success=int(summary["reason"] == "all_targets_confirmed_and_returned"),
            reason=summary["reason"],
            confirmed=summary["targets_confirmed"],
            sim_seconds=summary["elapsed_sim_seconds"],
            distance_m=summary["distance_m"],
            min_obstacle_gap_m=audit["minimum_obstacle_gap_m"],
            overlap_samples=audit["footprint_overlap_samples"],
            cross_rover_assignments=cross,
            intervention_valid=meta["intervention_valid"],
            delivery_attempts=count("attempts"),
            lost_attempts=count("lost_attempts"),
            retries=count("retries"),
            expired=count("expired"),
            mean_delivery_s=sum(
                s.get("delivered", 0) * (s.get("mean_delay_s") or 0) for s in streams
            )
            / max(1, count("delivered")),
            detection_samples=len(errors),
            detection_rmse_m=math.sqrt(sum(e * e for e in errors) / len(errors))
            if errors
            else None,
            source_sha256=meta["source_sha256"],
            run=str(directory),
        )
        row.update(
            integrate_power(
                directory,
                summary.get("world_start_seconds", 0),
                summary.get("world_finish_seconds", 1e9),
            )
        )
        rows.append(row)
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    rows = collect(args.root)
    if not rows:
        raise SystemExit("No matching actual submission experiments")
    if len({r["source_sha256"] for r in rows}) != 1:
        raise ValueError("Mixed runtime revisions: separate result folders before pairing policies")
    output = args.output or args.root / "comparison.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    pairs = {}
    for row in rows:
        key = (row["scenario"], row["seed"])
        if row["strategy"] in pairs.setdefault(key, {}):
            raise ValueError(f"Duplicate run for pair {key}; separate revisions before collecting")
        pairs[key][row["strategy"]] = row
    paired = sum(set(p) == {"nearest", "energy"} for p in pairs.values())
    print(
        json.dumps(
            dict(
                runs=len(rows),
                paired_layouts=paired,
                successes=sum(r["success"] for r in rows),
                source_revisions=len({r["source_sha256"] for r in rows}),
            ),
            indent=2,
        )
    )
    print(output)


if __name__ == "__main__":
    main()

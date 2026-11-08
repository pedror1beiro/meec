"""Build the paper's descriptive comparison from the complete frozen CSV."""

import argparse
import csv
import json
from pathlib import Path
from statistics import mean


def summarize(path):
    with path.open() as f:
        rows = list(csv.DictReader(f))
    scenarios = ("nominal", "asymmetric", "failure", "outage")
    expected = {
        (s, str(seed), p) for s in scenarios for seed in range(2) for p in ("nearest", "energy")
    }
    actual = {(r["scenario"], r["seed"], r["strategy"]) for r in rows}
    if len(rows) != 16 or actual != expected:
        raise ValueError("Require all 16 predefined cases, including any failures")
    if len({r["source_sha256"] for r in rows}) != 1:
        raise ValueError("The frozen batch must have one runtime fingerprint")
    groups = []
    for scenario in scenarios:
        for policy in ("nearest", "energy"):
            group = [r for r in rows if r["scenario"] == scenario and r["strategy"] == policy]
            groups.append(
                dict(
                    scenario=scenario,
                    policy=policy,
                    successes=sum(int(r["success"]) for r in group),
                    time=mean(float(r["sim_seconds"]) for r in group),
                    distance=mean(float(r["distance_m"]) for r in group),
                    discharge=mean(float(r["discharge_wh"]) for r in group),
                )
            )
    pairs = []
    for scenario in scenarios:
        for seed in ("0", "1"):
            pair = {
                r["strategy"]: r for r in rows if r["scenario"] == scenario and r["seed"] == seed
            }
            pairs.append(
                {
                    key: float(pair["energy"][key]) - float(pair["nearest"][key])
                    for key in ("sim_seconds", "distance_m", "discharge_wh")
                }
            )
    result = dict(
        runs=16,
        groups=groups,
        successes=sum(int(r["success"]) for r in rows),
        pairs=8,
        paired_mean_differences={k: mean(p[k] for p in pairs) for k in pairs[0]},
        min_gap=min(float(r["min_obstacle_gap_m"]) for r in rows),
        overlaps=sum(int(r["overlap_samples"]) for r in rows),
        interventions_valid=all(r["intervention_valid"] == "True" for r in rows),
        cross_assignments=sum(int(r["cross_rover_assignments"]) for r in rows),
        rmse_range=[
            min(float(r["detection_rmse_m"]) for r in rows),
            max(float(r["detection_rmse_m"]) for r in rows),
        ],
        source_sha256=rows[0]["source_sha256"],
    )
    for p in ("nearest", "energy"):
        group = [r for r in rows if r["strategy"] == p and r["scenario"] == "outage"]
        result["outage_" + p] = dict(
            lost=sum(int(r["lost_attempts"]) for r in group),
            retries=sum(int(r["retries"]) for r in group),
            expired=sum(int(r["expired"]) for r in group),
            delay=mean(float(r["mean_delivery_s"]) for r in group),
        )
    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("csv", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    results = summarize(args.csv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(results, indent=2) + "\n")
    print(json.dumps(results, indent=2))

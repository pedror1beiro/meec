#!/usr/bin/env python3
"""Run matched offline rehearsals; these are NOT publication-ready experiments."""

import argparse
import csv
from datetime import datetime
from pathlib import Path

from offline_demo import ROOT, load_config, rehearse


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "src/rsdis_lunar/config/mission.json")
    parser.add_argument("--seeds", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--scenarios",
        type=Path,
        help="Run both policies on every fixed JSON scenario in a directory",
    )
    args = parser.parse_args()
    parent = args.output or ROOT / "results" / (
        "comparison_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    )
    parent.mkdir(parents=True, exist_ok=False)
    rows = []
    cases = []
    if args.scenarios:
        for path in sorted(args.scenarios.glob("*.json")):
            config = load_config(path)
            cases.append(
                (path.stem, config.get("experiment", {}).get("layout_seed", 0), config, None, 0)
            )
    else:
        for seed in range(args.seeds):
            for scenario, failure in [("nominal", None), ("rover1_failure", 20.0)]:
                cases.append((scenario, seed, load_config(args.config), failure, seed))
    if not cases:
        parser.error("No scenarios to compare")
    for scenario, seed, config, failure, route_seed in cases:
        for strategy in ("nearest", "energy"):
            summary, _ = rehearse(
                config,
                strategy,
                failure,
                30.0,
                parent / f"{scenario}_{strategy}_{seed}",
                route_seed,
            )
            rows.append(
                {
                    "scenario": scenario,
                    "strategy": strategy,
                    "seed": seed,
                    "mode": summary["mode"],
                    **{
                        k: summary[k]
                        for k in (
                            "reason",
                            "elapsed_sim_seconds",
                            "targets_confirmed",
                            "distance_m",
                            "synthetic_energy_used",
                        )
                    },
                }
            )
    with (parent / "comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    for row in rows:
        print(
            f"{row['scenario']:16} {row['strategy']:7} route {row['seed']}: "
            f"{row['targets_confirmed']} targets, {row['elapsed_sim_seconds']:.1f}s"
        )
    print(parent / "comparison.csv")


if __name__ == "__main__":
    main()

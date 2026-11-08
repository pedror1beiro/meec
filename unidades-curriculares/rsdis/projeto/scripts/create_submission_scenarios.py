#!/usr/bin/env python3
"""Freeze a paired native-energy/network experiment design before collecting outcomes."""

import argparse
import copy
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.communications import link_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/submission_20261108")
    parser.add_argument("--seeds", type=int, default=2)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    base = load_config(ROOT / "src/rsdis_lunar/config/mission_small.json")
    for seed in range(args.seeds):
        layout = copy.deepcopy(base)
        rng = random.Random(seed)
        for target in layout["targets"]:
            target["position"] = [round(v + rng.uniform(-0.2, 0.2), 3) for v in target["position"]]
        for scenario in ("nominal", "asymmetric", "failure", "outage"):
            config = copy.deepcopy(layout)
            config["mission_seconds"] = 900
            config["experiment"] = dict(
                batch="submission_20261108",
                scenario=scenario,
                layout_seed=seed,
                randomisation="target xy +/-0.2 m; frozen before paired runs",
            )
            config["network"] = link_config(config, "outage" if scenario == "outage" else "ideal")
            config["network"]["seed"] = seed
            if scenario == "asymmetric":
                config["rovers"][0]["battery"] = 0.3
                config["rovers"][1]["battery"] = 0.95
            if scenario == "failure":
                # Paired policy comparisons use identical absolute failure times.
                # Task-triggered faults remain a separate functional-recovery gate.
                config["failure"] = dict(rover_id="rover1", at=30, duration=30)
            path = args.output / f"{scenario}_{seed:02}.json"
            if path.exists() and json.loads(path.read_text()) != config:
                raise FileExistsError(f"Refusing to change frozen design: {path}")
            path.write_text(json.dumps(config, indent=2) + "\n")
    print(f"Frozen {args.seeds * 4} configurations; execute both policies for each.")


if __name__ == "__main__":
    main()

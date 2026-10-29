#!/usr/bin/env python3
"""Generate paired, reproducible layouts before examining policy outcomes."""

import argparse
import copy
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--count", type=int, default=5)
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/generated")
    args = parser.parse_args()
    if args.count < 1:
        parser.error("--count must be positive")
    args.output.mkdir(parents=True, exist_ok=True)
    base = load_config(ROOT / "src/rsdis_lunar/config/mission.json")
    for seed in range(args.count):
        rng = random.Random(seed)
        layout = copy.deepcopy(base)
        for target in layout["targets"]:
            target["position"] = [round(v + rng.uniform(-0.6, 0.6), 3) for v in target["position"]]
        for scenario in ("nominal", "energy_stress", "failure", "energy_and_failure"):
            config = copy.deepcopy(layout)
            config["experiment"] = {
                "scenario": scenario,
                "layout_seed": seed,
                "layout_randomisation": "target xy +/-0.6 m; fixed before comparison",
            }
            if "energy" in scenario:
                config["rovers"][0]["battery"] = 0.42
                config["rovers"][1]["battery"] = 0.95
                config["energy"]["travel_per_metre"] = 0.012
            if "failure" in scenario:
                config["failure"] = {"rover_id": "rover1", "at": 20.0, "duration": 30.0}
            path = args.output / f"{scenario}_{seed:02}.json"
            if path.exists():
                if json.loads(path.read_text(encoding="utf-8")) == config:
                    continue
                raise FileExistsError(
                    f"Refusing to replace a modified experiment configuration: {path}"
                )
            path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Created {args.count * 4} fixed configurations under {args.output}")


if __name__ == "__main__":
    main()

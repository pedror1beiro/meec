"""Portable JSONL event and CSV telemetry output, one directory per run."""

import csv
from dataclasses import asdict
import json
from pathlib import Path


class Metrics:
    def __init__(self, directory, config, strategy, mode):
        self.path = Path(directory)
        self.path.mkdir(parents=True, exist_ok=False)
        self.mode, self.strategy = mode, strategy
        self.events = (self.path / "events.jsonl").open("w", encoding="utf-8")
        self.telemetry = (self.path / "telemetry.csv").open("w", newline="", encoding="utf-8")
        self.csv = csv.writer(self.telemetry)
        self.csv.writerow(
            ["time", "rover", "x", "y", "yaw", "battery", "mode", "distance_m", "energy_used"]
        )
        self.config = config
        (self.path / "config.json").write_text(
            json.dumps(config, indent=2) + "\n", encoding="utf-8"
        )
        self.closed = False
        self.last_sample = None
        self.origin = 0.0

    def record(self, coordinator, now):
        while coordinator.events:
            event = coordinator.events.pop(0)
            event["time"] = round(event["time"] - self.origin, 3)
            self.events.write(json.dumps(event) + "\n")
        self.events.flush()
        if self.last_sample == now:
            return
        self.last_sample = now
        for r in sorted(coordinator.rovers.values(), key=lambda r: r.rover_id):
            self.csv.writerow(
                [
                    round(now, 3),
                    r.rover_id,
                    *r.pose,
                    round(r.battery, 6),
                    r.mode,
                    round(r.travelled, 3),
                    round(r.energy_used, 6),
                ]
            )
        self.telemetry.flush()

    def finish(self, coordinator, now, reason):
        if self.closed:
            return
        self.record(coordinator, now)
        summary = {
            "mode": self.mode,
            "strategy": self.strategy,
            "reason": reason,
            "elapsed_sim_seconds": round(now, 3),
            "targets_expected": len(self.config["targets"]),
            "targets_discovered": len(coordinator.targets),
            "targets_confirmed": sum(t.confirmed for t in coordinator.targets.values()),
            "distance_m": sum(r.travelled for r in coordinator.rovers.values()),
            "synthetic_energy_used": sum(r.energy_used for r in coordinator.rovers.values()),
            "rovers": {r.rover_id: asdict(r) for r in coordinator.rovers.values()},
        }
        (self.path / "summary.json").write_text(
            json.dumps(summary, indent=2) + "\n", encoding="utf-8"
        )
        coordinator.closed = True
        self.events.close()
        self.telemetry.close()
        self.closed = True
        return summary

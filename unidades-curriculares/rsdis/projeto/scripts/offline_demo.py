#!/usr/bin/env python3
"""Cross-platform rehearsal of mission logic, NOT a Gazebo/perception experiment."""

import argparse
from datetime import datetime
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src" / "rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.core import Coordinator, Rover, distance, wrap
from rsdis_lunar.metrics import Metrics


def rehearse(
    config,
    strategy="energy",
    failure_at=None,
    failure_duration=30.0,
    output=None,
    seed=0,
    failure_rover=None,
):
    # Seed rotates the routes, retaining the same world/initial batteries across policies.
    # This varies visit order, not physical terrain or sensor noise.
    import copy

    config = copy.deepcopy(config)
    if failure_at is None and config.get("failure"):
        failure_at = config["failure"]["at"]
        failure_duration = config["failure"]["duration"]
        failure_rover = config["failure"]["rover_id"]
    for spec in config["rovers"]:
        shift = seed % len(spec["waypoints"])
        spec["waypoints"] = spec["waypoints"][shift:] + spec["waypoints"][:shift]
    coordinator = Coordinator(config, strategy)
    rovers = {r["id"]: Rover(r, config) for r in config["rovers"]}
    poses = {r["id"]: tuple(r["spawn"]) for r in config["rovers"]}
    dt, now = 0.1, 0.0
    if output is None:
        output = ROOT / "results" / ("offline_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    metrics = Metrics(output, config, strategy, "offline_kinematic_oracle_detection")
    # Keep a trace suitable for the portable HTML playback.
    trace = []
    failure_started = failure_ended = False
    return_requested = False
    reason = "time_limit"
    while now <= config["mission_seconds"]:
        if failure_at is not None:
            failed_id = failure_rover or config["rovers"][0]["id"]
            rovers[failed_id].enabled = not failure_at <= now < failure_at + failure_duration
            if now >= failure_at and not failure_started:
                coordinator.event(now, "failure_injected", rover=failed_id)
                failure_started = True
            if now >= failure_at + failure_duration and not failure_ended:
                coordinator.event(now, "failure_recovered", rover=failed_id)
                failure_ended = True
        # This detector reads known target positions to exercise coordination only.
        # ROS uses camera images and the independent vision.py implementation instead.
        for rover in rovers.values():
            if not rover.enabled:
                continue
            pose = poses[rover.id]
            for target in config["targets"]:
                tx, ty = target["position"]
                angle = wrap(math.atan2(ty - pose[1], tx - pose[0]) - pose[2])
                if (
                    distance(pose, target["position"]) < 8
                    and abs(angle) < config["camera_hfov"] / 2
                ):
                    rover.seen(target["id"], now)
                    coordinator.observe(target["id"], target["position"], rover.id, now)
                    for teammate in rovers.values():
                        teammate.remember(target["id"], target["position"])
        for rover in rovers.values():
            v, w = rover.step(poses[rover.id], dt, now, list(coordinator.rovers.values()))
            x, y, yaw = poses[rover.id]
            poses[rover.id] = (
                x + v * math.cos(yaw) * dt,
                y + v * math.sin(yaw) * dt,
                wrap(yaw + w * dt),
            )
            coordinator.update(rover.snapshot(now))
            while rover.results:
                rover_id, task_id, success, detail = rover.results.pop(0)
                coordinator.result(rover_id, task_id, success, now, detail)
        if round(now / dt) % 5 == 0:
            for goal in [] if return_requested else coordinator.tick(now):
                rovers[goal.rover_id].assign(goal, now)
            metrics.record(coordinator, now)
            trace.append(
                {
                    "time": round(now, 2),
                    "rovers": [
                        {"id": r.id, "pose": list(r.pose), "battery": r.battery, "mode": r.mode}
                        for r in rovers.values()
                    ],
                    "targets": {
                        t.target_id: ("confirmed" if t.confirmed else (t.owner or "discovered"))
                        for t in coordinator.targets.values()
                    },
                }
            )
        if len(coordinator.targets) == len(config["targets"]) and all(
            t.confirmed for t in coordinator.targets.values()
        ):
            if not return_requested:
                return_requested = True
                coordinator.event(now, "return_home_requested")
                for rover in rovers.values():
                    rover.return_home()
            if all(r.mode == "parked" for r in rovers.values()):
                reason = "all_targets_confirmed_and_returned"
                break
        now = round(now + dt, 6)
    if not trace or trace[-1]["time"] != round(now, 2):
        trace.append(
            {
                "time": round(now, 2),
                "rovers": [
                    {"id": r.id, "pose": list(r.pose), "battery": r.battery, "mode": r.mode}
                    for r in rovers.values()
                ],
                "targets": {
                    t.target_id: ("confirmed" if t.confirmed else (t.owner or "discovered"))
                    for t in coordinator.targets.values()
                },
            }
        )
    summary = metrics.finish(coordinator, now, reason)
    import json

    (Path(output) / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
    from playback import write_playback

    write_playback(Path(output), config, trace, summary)
    return summary, Path(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "src/rsdis_lunar/config/mission.json")
    parser.add_argument("--strategy", choices=["nearest", "energy"], default="energy")
    parser.add_argument("--failure-at", type=float)
    parser.add_argument("--failure-duration", type=float, default=30.0)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    summary, path = rehearse(
        load_config(args.config),
        args.strategy,
        args.failure_at,
        args.failure_duration,
        args.output,
        args.seed,
    )
    print(
        f"OFFLINE REHEARSAL ONLY: {summary['targets_confirmed']}/{summary['targets_expected']} targets, "
        f"{summary['elapsed_sim_seconds']:.1f}s; {summary['reason']}"
    )
    print(f"Metrics and playback: {path}")


if __name__ == "__main__":
    main()

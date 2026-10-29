import json
import math
from pathlib import Path


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))

    def numeric(value, label):
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
        ):
            raise ValueError(f"{label} must be a finite number")
        return float(value)

    for key in (
        "mission_seconds",
        "status_timeout",
        "lease_seconds",
        "task_timeout",
        "inspection_seconds",
        "inspection_standoff",
        "marker_diameter",
        "camera_offset",
        "camera_hfov",
    ):
        config[key] = numeric(config[key], key)
    for key, value in config["energy"].items():
        config["energy"][key] = numeric(value, "energy." + key)
    ids = [r["id"] for r in config["rovers"]]
    if len(ids) != len(set(ids)) or len(ids) < 2:
        raise ValueError("Provide at least two rovers with unique IDs")
    for spec in config["rovers"]:
        if not spec["id"].isidentifier() or not spec["waypoints"]:
            raise ValueError("Rover IDs must be identifiers and routes must be non-empty")
        if not 0 < spec["battery"] <= 1:
            raise ValueError("Initial battery must be in (0, 1]")
        if len(spec["spawn"]) != 3 or any(len(p) != 2 for p in spec["waypoints"]):
            raise ValueError("Use spawn=[x,y,yaw] and waypoints=[[x,y], ...]")
        spec["battery"] = numeric(spec["battery"], "initial battery")
        spec["spawn"] = [numeric(v, "spawn") for v in spec["spawn"]]
        spec["waypoints"] = [[numeric(v, "waypoint") for v in p] for p in spec["waypoints"]]
    target_ids = [t["id"] for t in config["targets"]]
    if len(set(target_ids)) != len(target_ids):
        raise ValueError("Each coloured marker must have a unique ID")
    for target in config["targets"]:
        if target["id"] not in ("red", "green", "blue", "magenta", "orange"):
            raise ValueError("Target IDs must match the five implemented marker colours")
        if len(target["position"]) != 2 or len(target["colour"]) != 4:
            raise ValueError("Use target position=[x,y] and colour=[r,g,b,a]")
        target["position"] = [numeric(v, "target position") for v in target["position"]]
        target["colour"] = [numeric(v, "target colour") for v in target["colour"]]
    if not 0 < config["energy"]["reserve"] < config["energy"]["resume_level"] <= 1:
        raise ValueError("Require 0 < reserve < resume_level <= 1")
    for key in (
        "mission_seconds",
        "status_timeout",
        "lease_seconds",
        "task_timeout",
        "inspection_seconds",
        "inspection_standoff",
        "marker_diameter",
    ):
        if config[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if config["lease_seconds"] <= 0.5 or config["status_timeout"] <= config["lease_seconds"]:
        raise ValueError("Require lease_seconds > 0.5 and status_timeout > lease_seconds")
    if not 0 < config["camera_hfov"] < math.pi:
        raise ValueError("camera_hfov must be in (0, pi)")
    if any(config["energy"][k] < 0 for k in ("idle_per_second", "travel_per_metre", "risk_weight")):
        raise ValueError("Energy consumption and risk weight must be non-negative")
    if config["energy"]["charge_per_second"] <= 0:
        raise ValueError("Charge rate must be positive")
    if config.get("failure"):
        failure = config["failure"]
        if failure["rover_id"] not in ids or failure["at"] < 0 or failure["duration"] <= 0:
            raise ValueError("Failure requires a known rover, at>=0 and duration>0")
        failure["at"] = numeric(failure["at"], "failure time")
        failure["duration"] = numeric(failure["duration"], "failure duration")
    return config


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def pose_tuple(pose):
    return pose.position.x, pose.position.y, yaw(pose.orientation)


def stamp_seconds(stamp):
    return stamp.sec + stamp.nanosec / 1e9

import json
import math
from pathlib import Path


def load_config(path):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    defaults = dict(
        map_bounds=[-18, 18, -13, 13], ground_size=[40, 30], rover_radius=0.72,
        safety_margin=0.28, marker_uncertainty=0.25, lidar_offset=0.62,
        lidar_height=0.65, lidar_range=12.0, scan_timeout=0.6,
        planner_resolution=0.5, max_speed=0.45, hazards=[], sectors=[],
    )
    for key, value in defaults.items():
        config.setdefault(key, value)

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
    for key in (
        "rover_radius", "safety_margin", "marker_uncertainty", "lidar_offset",
        "lidar_height", "lidar_range", "scan_timeout", "planner_resolution", "max_speed",
    ):
        config[key] = numeric(config[key], key)
        if config[key] <= 0:
            raise ValueError(f"{key} must be positive")
    if config["max_speed"] > 0.45:
        raise ValueError("max_speed must not exceed the model limit of 0.45 m/s")
    if len(config["map_bounds"]) != 4 or len(config["ground_size"]) != 2:
        raise ValueError("Use map_bounds=[xmin,xmax,ymin,ymax] and ground_size=[width,height]")
    bounds = config["map_bounds"] = [numeric(v, "map_bounds") for v in config["map_bounds"]]
    ground = config["ground_size"] = [numeric(v, "ground_size") for v in config["ground_size"]]
    if not (-ground[0] / 2 <= bounds[0] < bounds[1] <= ground[0] / 2 and
            -ground[1] / 2 <= bounds[2] < bounds[3] <= ground[1] / 2):
        raise ValueError("Map bounds must fit inside the ground surface")
    hazard_ids = set()
    for hazard in config["hazards"]:
        if hazard["id"] in hazard_ids or hazard["kind"] not in ("rock", "crater", "habitat", "solar"):
            raise ValueError("Hazards need unique IDs and kind=rock/crater/habitat/solar")
        hazard_ids.add(hazard["id"])
        if not hazard["id"].isidentifier() or len(hazard["position"]) != 2:
            raise ValueError("Hazards need identifier IDs and position=[x,y]")
        hazard["position"] = [numeric(v, "hazard position") for v in hazard["position"]]
        hazard["radius"] = numeric(hazard["radius"], "hazard radius")
        if hazard["radius"] <= 0:
            raise ValueError("Hazard radii must be positive")
    minimum_standoff = config["rover_radius"] + config["safety_margin"] + config["marker_diameter"] / 2 + config["marker_uncertainty"]
    if config["inspection_standoff"] < minimum_standoff + 0.2:
        # Older saved experiment files used 1.25 m. Keep them runnable safely.
        config["inspection_standoff"] = minimum_standoff + 0.35
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
    from .planning import in_bounds, segment_clear

    obstacles = [(*h["position"], h["radius"]) for h in config["hazards"]]
    clearance = config["rover_radius"] + config["safety_margin"]
    for spec in config["rovers"]:
        for position in [spec["spawn"][:2], *spec["waypoints"]]:
            if not in_bounds(position, bounds, clearance) or not segment_clear(position, position, obstacles, clearance):
                raise ValueError(f"{spec['id']} spawn/waypoint intersects a hazard or map boundary")
    return config


def yaw(q):
    return math.atan2(2 * (q.w * q.z + q.x * q.y), 1 - 2 * (q.y * q.y + q.z * q.z))


def pose_tuple(pose):
    return pose.position.x, pose.position.y, yaw(pose.orientation)


def stamp_seconds(stamp):
    return stamp.sec + stamp.nanosec / 1e9

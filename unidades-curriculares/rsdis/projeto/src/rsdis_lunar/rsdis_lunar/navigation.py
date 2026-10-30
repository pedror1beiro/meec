"""Shared route follower and range-sensor safety gate, independent of ROS."""

import math

from .planning import DEFAULT_BOUNDS, in_bounds, plan_path, segment_clear


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


def scan_points(ranges, angle_min, angle_increment, minimum, maximum, pose, offset):
    """Project laser returns from the front sensor into the world frame.

    +inf is a valid no-return ray. NaN, -inf and below-minimum returns invalidate
    the scan, so a broken/obstructed sensor cannot silently become free space.
    """
    points = {}
    valid = bool(len(ranges)) and angle_increment > 0 and maximum > minimum >= 0
    for i, value in enumerate(ranges):
        if math.isinf(value) and value > 0:
            continue
        if not math.isfinite(value) or value < minimum:
            valid = False
            continue
        if value >= maximum:
            continue
        angle = angle_min + i * angle_increment
        x, y = offset + value * math.cos(angle), value * math.sin(angle)
        wx = pose[0] + x * math.cos(pose[2]) - y * math.sin(pose[2])
        wy = pose[1] + x * math.sin(pose[2]) + y * math.cos(pose[2])
        points[(round(wx / 0.15), round(wy / 0.15))] = (wx, wy, 0.08)
    return list(points.values()), valid


def advance(pose, linear, angular, seconds):
    x, y, yaw = pose
    if abs(angular) < 1e-8:
        return x + linear * math.cos(yaw) * seconds, y + linear * math.sin(yaw) * seconds, yaw
    angle = yaw + angular * seconds
    return (
        x + linear / angular * (math.sin(angle) - math.sin(yaw)),
        y - linear / angular * (math.cos(angle) - math.cos(yaw)),
        wrap(angle),
    )


def safe_velocity(pose, linear, angular, obstacles, clearance, bounds, deceleration=0.6):
    """Check the swept circular footprint over reaction time AND braking distance."""
    if not all(math.isfinite(v) for v in (*pose, linear, angular)):
        return 0.0, 0.0
    if abs(linear) < 1e-8:
        return 0.0, angular if segment_clear(pose, pose, obstacles, clearance) else 0.0
    for scale in (1.0, 0.5, 0.25):
        v = linear * scale
        horizon = 0.5 + abs(v) / deceleration
        previous, safe = pose, True
        for step in range(1, 13):
            candidate = advance(pose, v, angular * scale, horizon * step / 12)
            if not in_bounds(candidate, bounds, clearance) or not segment_clear(
                previous, candidate, obstacles, clearance
            ):
                safe = False
                break
            previous = candidate
        if safe:
            return v, angular * scale
    return 0.0, 0.0


def static_obstacles(config):
    return [(*h["position"], h["radius"]) for h in config.get("hazards", [])]


class Navigator:
    def __init__(self, config):
        self.config = config
        self.radius = config.get("rover_radius", 0.72)
        self.clearance = self.radius + config.get("safety_margin", 0.28)
        self.bounds = tuple(config.get("map_bounds", DEFAULT_BOUNDS))
        self.static = static_obstacles(config)
        self.path, self.destination = [], None
        self.last_plan = -math.inf
        self.state = "idle"
        self.require_scan = False
        self.scan_at, self.scan_valid = -math.inf, False
        self.points, self.memory = [], {}

    def update_scan(self, points, now, valid=True, peers=()):
        self.scan_at, self.scan_valid, self.points = now, valid, list(points)
        for point in points:
            if any(math.dist(point[:2], p.pose[:2]) < self.radius + 0.5 for p in peers):
                continue
            if any(math.dist(point[:2], h[:2]) < h[2] + 0.35 for h in self.static):
                continue
            self.memory[(round(point[0] / 0.4), round(point[1] / 0.4))] = (*point, now)
        self.memory = {k: p for k, p in self.memory.items() if now - p[3] < 8.0}

    def obstacles(self, markers, peers, now):
        marker_radius = self.config["marker_diameter"] / 2 + self.config.get(
            "marker_uncertainty", 0.25
        )
        obstacles = self.static + [(*p, marker_radius) for p in markers]
        obstacles += [(*p.pose[:2], self.radius + 0.12) for p in peers]
        obstacles += [p[:3] for p in self.memory.values() if now - p[3] < 8.0]
        return obstacles

    def guard(self, pose, command, obstacles, now):
        if self.require_scan and (
            not self.scan_valid or not 0 <= now - self.scan_at < self.config.get("scan_timeout", 0.6)
        ):
            self.state = "waiting_for_scan"
            return 0.0, 0.0
        checked = safe_velocity(
            pose, *command, [*obstacles, *self.points], self.clearance, self.bounds
        )
        if command[0] and not checked[0]:
            self.state = "obstacle_stop"
        return checked

    def command(self, pose, destination, markers, peers, now):
        obstacles = self.obstacles(markers, peers, now)
        if self.require_scan and (not self.scan_valid or now - self.scan_at >= 0.6):
            self.state = "waiting_for_scan"
            return 0.0, 0.0
        if self.path and math.dist(pose[:2], self.path[0]) < 0.2:
            self.path.pop(0)
        changed = self.destination is None or math.dist(destination, self.destination) > 0.15
        blocked = bool(self.path) and not segment_clear(pose, self.path[0], obstacles, self.clearance)
        if changed or not self.path or blocked:
            if now - self.last_plan < 0.4 and not changed:
                self.state = "replanning"
                return 0.0, 0.0
            route = plan_path(
                pose, destination, obstacles,
                resolution=self.config.get("planner_resolution", 0.5),
                clearance=self.clearance, bounds=self.bounds,
            )
            self.path = route[1:] if route else []
            self.destination, self.last_plan = tuple(destination), now
        if not self.path:
            self.state = "path_blocked"
            return 0.0, 0.0
        waypoint = self.path[0]
        error = wrap(math.atan2(waypoint[1] - pose[1], waypoint[0] - pose[0]) - pose[2])
        turn = max(-0.55, min(0.55, 1.6 * error))
        speed = min(self.config.get("max_speed", 0.45), 0.8 * math.dist(pose[:2], waypoint))
        speed *= max(0.0, 1.0 - abs(error) / 0.18)
        if abs(error) >= 0.18:
            speed = 0.0
        self.state = "turning" if not speed else "driving"
        return self.guard(pose, (speed, turn), obstacles, now)

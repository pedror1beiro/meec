"""Independent geometry audit and synthetic ranging for portable regressions.

These know scenario truth. Neither is used as an input to the ROS controller.
The audit checks conservative footprint separation, not Gazebo contact forces.
"""

import math


class ClearanceAudit:
    def __init__(self, config):
        self.radius = config.get("rover_radius", 0.72)
        self.obstacles = [(*h["position"], h["radius"]) for h in config.get("hazards", [])]
        self.obstacles += [
            (*t["position"], config["marker_diameter"] / 2) for t in config["targets"]
        ]
        self.minimum, self.peer_minimum = math.inf, math.inf
        self.violations = 0

    def sample(self, poses):
        positions = list(poses.values())
        for pose in positions:
            for ox, oy, radius in self.obstacles:
                gap = math.hypot(pose[0] - ox, pose[1] - oy) - self.radius - radius
                self.minimum = min(self.minimum, gap)
                self.violations += int(gap < -0.01)
        for i, a in enumerate(positions):
            for b in positions[i + 1 :]:
                gap = math.dist(a[:2], b[:2]) - 2 * self.radius
                self.peer_minimum = min(self.peer_minimum, gap)
                self.violations += int(gap < -0.01)

    def report(self):
        return dict(
            minimum_obstacle_gap_m=round(self.minimum, 4) if math.isfinite(self.minimum) else None,
            minimum_peer_gap_m=round(self.peer_minimum, 4)
            if math.isfinite(self.peer_minimum)
            else None,
            footprint_overlap_samples=self.violations,
            method="conservative planar geometry, not a physics contact measurement",
        )


def simulated_scan(pose, config, poses, rover_id):
    """Oracle range endpoints for the offline harness only, without colour IDs."""
    offset = config.get("lidar_offset", 0.62)
    origin = pose[0] + offset * math.cos(pose[2]), pose[1] + offset * math.sin(pose[2])
    obstacles = [(*t["position"], config["marker_diameter"] / 2) for t in config["targets"]]
    obstacles += [
        (*h["position"], h["radius"]) for h in config.get("hazards", []) if h["kind"] != "crater"
    ]
    obstacles += [
        (*p[:2], config.get("rover_radius", 0.72)) for name, p in poses.items() if name != rover_id
    ]
    nearby = [
        h for h in obstacles if math.dist(origin, h[:2]) < config.get("lidar_range", 12) + h[2]
    ]
    points = {}
    for i in range(181):
        angle = pose[2] - math.pi / 2 + math.pi * i / 180
        dx, dy = math.cos(angle), math.sin(angle)
        nearest = config.get("lidar_range", 12.0)
        for x, y, radius in nearby:
            ox, oy = origin[0] - x, origin[1] - y
            b, c = ox * dx + oy * dy, ox * ox + oy * oy - radius * radius
            discriminant = b * b - c
            if discriminant < 0:
                continue
            hit = -b - math.sqrt(discriminant)
            if 0.06 < hit < nearest:
                nearest = hit
        if nearest < config.get("lidar_range", 12.0):
            x, y = origin[0] + nearest * dx, origin[1] + nearest * dy
            points[(round(x / 0.3), round(y / 0.3))] = (x, y, 0.08)
    return list(points.values())

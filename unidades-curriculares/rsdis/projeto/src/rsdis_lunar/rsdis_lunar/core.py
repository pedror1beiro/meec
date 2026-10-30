"""Mission logic shared by ROS nodes and the portable, non-physics rehearsal.

Energy units are fractions of a deliberately accelerated, synthetic battery.
Coordinates are metres in a shared world frame. This is not SLAM or Nav2.
"""

from dataclasses import dataclass
import math
from .navigation import Navigator


def distance(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def wrap(angle):
    return math.atan2(math.sin(angle), math.cos(angle))


@dataclass
class Energy:
    reserve: float = 0.15
    idle_per_second: float = 0.0001
    travel_per_metre: float = 0.006
    charge_per_second: float = 0.025
    resume_level: float = 0.85
    risk_weight: float = 8.0

    def cost(self, metres, seconds=0.0):
        return metres * self.travel_per_metre + seconds * self.idle_per_second


@dataclass
class Snapshot:
    rover_id: str
    pose: tuple
    battery: float
    mode: str
    seen_at: float
    travelled: float = 0.0
    energy_used: float = 0.0


@dataclass
class Goal:
    task_id: str
    target_id: str
    position: tuple
    rover_id: str


@dataclass
class Target:
    target_id: str
    position: tuple
    owner: str = ""
    task_id: str = ""
    assigned_at: float = 0.0
    confirmed: bool = False
    attempts: int = 0
    retry_at: float = 0.0
    observations: int = 1


class Coordinator:
    def __init__(self, config, strategy="energy"):
        if strategy not in ("nearest", "energy"):
            raise ValueError("strategy must be nearest or energy")
        self.config, self.strategy = config, strategy
        self.energy = Energy(**config["energy"])
        self.homes = {r["id"]: tuple(r["spawn"][:2]) for r in config["rovers"]}
        self.rovers = {}
        self.targets = {}
        self.events = []
        self.serial = 0
        self.closed = False

    def event(self, now, kind, **fields):
        self.events.append(dict(time=round(now, 3), event=kind, **fields))

    def observe(self, target_id, position, observer, now):
        if self.closed or observer not in self.homes:
            return
        if not all(math.isfinite(v) for v in position):
            return
        if target_id not in self.targets:
            self.targets[target_id] = Target(target_id, tuple(position))
            self.event(now, "discovered", target=target_id, rover=observer)
        else:
            t = self.targets[target_id]
            # Colour IDs identify unique markers. Reject grossly inconsistent observations.
            if not t.confirmed and not t.owner and distance(t.position, position) < 1.5:
                n = min(t.observations, 20)
                t.position = tuple((n * a + b) / (n + 1) for a, b in zip(t.position, position))
                t.observations += 1

    def update(self, snapshot):
        if snapshot.rover_id in self.homes:
            self.rovers[snapshot.rover_id] = snapshot

    def result(self, rover_id, task_id, success, now, detail=""):
        for t in self.targets.values():
            if t.task_id == task_id and t.owner == rover_id:
                t.confirmed = bool(success)
                self.event(
                    now,
                    "confirmed" if success else "released",
                    target=t.target_id,
                    rover=rover_id,
                    task=task_id,
                    detail=detail,
                )
                t.owner = t.task_id = ""
                t.retry_at = now + (0.0 if success else 5.0)
                return True
        return False  # Ignore duplicate or delayed results from an expired assignment.

    def estimate(self, rover, target):
        standoff = self.config["inspection_standoff"]
        outward = max(0.0, distance(rover.pose, target.position) - standoff)
        return_leg = distance(target.position, self.homes[rover.rover_id]) + standoff
        # Travel time is conservatively estimated at 0.3 m/s, plus turning/dwell.
        total = outward + return_leg
        required = self.energy.cost(total, total / 0.3 + 10.0) + self.energy.reserve
        return outward, required

    def tick(self, now):
        if self.closed:
            return []
        for t in self.targets.values():
            if t.owner:
                r = self.rovers.get(t.owner)
                if (
                    r is None
                    or now - r.seen_at > self.config["status_timeout"]
                    or r.mode in ("unavailable", "depleted", "returning", "charging")
                    or now - t.assigned_at > self.config["task_timeout"]
                ):
                    self.result(t.owner, t.task_id, False, now, "timeout_or_unavailable")
        busy = {t.owner for t in self.targets.values() if t.owner}
        for t in sorted(self.targets.values(), key=lambda t: t.target_id):
            if t.confirmed or t.owner or now < t.retry_at or t.attempts >= 3:
                continue
            candidates = []
            for r in self.rovers.values():
                if (
                    r.rover_id in busy
                    or r.mode not in ("exploring", "idle")
                    or now - r.seen_at > self.config["status_timeout"]
                ):
                    continue
                outward, required = self.estimate(r, t)
                if r.battery < required:
                    continue
                score = outward
                if self.strategy == "energy":
                    score += self.energy.risk_weight * required / max(r.battery, 0.01)
                candidates.append((score, r.rover_id))
            if candidates:
                _, t.owner = min(candidates)
                self.serial += 1
                t.task_id = f"{t.target_id}-{self.serial}"
                t.assigned_at = now
                t.attempts += 1
                busy.add(t.owner)
                self.event(now, "assigned", target=t.target_id, rover=t.owner, task=t.task_id)
        return [
            Goal(t.task_id, t.target_id, t.position, t.owner)
            for t in self.targets.values()
            if t.owner
        ]


class Rover:
    def __init__(self, spec, config):
        self.id, self.config = spec["id"], config
        self.home = tuple(spec["spawn"][:2])
        self.waypoints = [tuple(p) for p in spec["waypoints"]]
        self.energy = Energy(**config["energy"])
        self.battery = spec["battery"]
        self.pose = tuple(spec["spawn"])
        self.mode = "idle"
        self.enabled = True
        self.goal = None
        self.lease_until = 0.0
        self.retired = set()
        self.results = []
        self.observations = {}
        self.waypoint_index = 0
        self.dwell = 0.0
        self.travelled = 0.0
        self.energy_used = 0.0
        self.returning = False
        self.park = False
        self.known_targets = {}
        self.navigator = Navigator(config)
        self.paused = False
        self.approach = None
        self.approach_centre = None
        self.blocked_since = None
        self.survey_started = None
        self.survey_yaw = None
        self.survey_angle = 0.0

    def assign(self, goal, now):
        if goal.task_id in self.retired or goal.rover_id != self.id:
            return
        if not self.enabled or self.returning or self.battery <= 0:
            return
        if self.goal is None or self.goal.task_id != goal.task_id:
            if self.goal is not None:
                self.finish(False, "superseded")
            self.goal, self.dwell = goal, 0.0
            separation = max(0.01, distance(self.pose, goal.position))
            stand = self.config["inspection_standoff"] - 0.12
            self.approach = tuple(
                goal.position[i] - (goal.position[i] - self.pose[i]) * stand / separation
                for i in range(2)
            )
            self.approach_centre = tuple(goal.position)
            self.navigator.path = []
            self.navigator.pass_point = None
            self.survey_started = None
        self.lease_until = now + self.config["lease_seconds"]

    def finish(self, success, detail):
        if self.goal:
            self.results.append((self.id, self.goal.task_id, success, detail))
            self.retired.add(self.goal.task_id)
            self.goal, self.dwell = None, 0.0

    def seen(self, target_id, now, position=None):
        self.observations[target_id] = now
        if position is not None:
            self.remember(target_id, position)

    def remember(self, target_id, position):
        if all(math.isfinite(v) for v in position):
            old = self.known_targets.get(target_id)
            # Do not let one partially occluded, biased contour drag a stable
            # keep-out estimate towards the rover during an inspection.
            if old is None:
                self.known_targets[target_id] = tuple(position)
            elif distance(old, position) < 2.0:
                self.known_targets[target_id] = tuple(
                    0.8 * a + 0.2 * b for a, b in zip(old, position)
                )

    def return_home(self):
        self.returning = self.park = True
        self.finish(False, "mission_return")

    def snapshot(self, now):
        return Snapshot(
            self.id, self.pose, self.battery, self.mode, now, self.travelled, self.energy_used
        )

    def step(self, pose, dt, now, peers=()):
        peers = [p for p in peers if p.rover_id != self.id]
        travelled = distance(self.pose, pose)
        self.travelled += travelled
        self.pose = tuple(pose)
        if self.paused:
            self.lease_until += dt
            self.navigator.state = "paused"
            return 0.0, 0.0
        # Distance comes from odometry, rather than requested velocity.
        used = min(self.battery, self.energy.cost(travelled, dt))
        self.energy_used += used
        self.battery = max(0.0, self.battery - used)
        if not self.enabled:
            self.finish(False, "disabled")
            self.mode = "unavailable"
            return 0.0, 0.0
        if self.battery <= 0:
            self.finish(False, "depleted")
            self.mode = "depleted"
            return 0.0, 0.0
        if self.goal and now > self.lease_until:
            self.finish(False, "lease_expired")
        home_distance = distance(pose, self.home)
        home_budget = self.energy.cost(home_distance, home_distance / 0.3 + 5.0)
        if self.battery < self.energy.reserve + home_budget:
            self.returning = True
            self.finish(False, "energy_return")
        if self.returning:
            if home_distance < 0.3:
                self.mode = "parked" if self.park else "charging"
                self.battery = min(1.0, self.battery + self.energy.charge_per_second * dt)
                if self.battery >= self.energy.resume_level and not self.park:
                    self.returning = False
                return 0.0, 0.0
            self.mode, destination, tolerance = "returning", self.home, 0.25
        elif self.goal:
            self.mode = "inspecting"
            destination = self.known_targets.get(self.goal.target_id, self.goal.position)
            tolerance = self.config["inspection_standoff"]
            if distance(destination, self.approach_centre) > 0.12:
                correction = tuple(a - b for a, b in zip(destination, self.approach_centre))
                self.approach = tuple(a + b for a, b in zip(self.approach, correction))
                self.approach_centre = tuple(destination)
                self.navigator.path = []
        else:
            self.mode = "exploring"
            destination = self.waypoints[self.waypoint_index % len(self.waypoints)]
            tolerance = 0.35
            route = distance(pose, destination) + distance(destination, self.home)
            if self.battery < self.energy.reserve + self.energy.cost(route, route / 0.3 + 10):
                self.returning = True
                self.mode, destination, tolerance = "returning", self.home, 0.25
        error = wrap(math.atan2(destination[1] - pose[1], destination[0] - pose[0]) - pose[2])
        reached = distance(pose, destination) <= tolerance
        if reached:
            if self.mode == "inspecting":
                # Confirmation requires a recent detection by this rover, facing the marker.
                fresh = now - self.observations.get(self.goal.target_id, -math.inf) < 1.0
                self.dwell = self.dwell + dt if fresh and abs(error) < 0.2 else 0.0
                if self.dwell >= self.config["inspection_seconds"]:
                    self.finish(True, "camera_confirmed")
                self.navigator.state = "confirming" if fresh else "acquiring_marker"
                return self.navigator.guard(
                    pose,
                    (0.0, max(-0.55, min(0.55, 1.5 * error)) if abs(error) > 0.1 else 0.0),
                    self.navigator.obstacles(self.known_targets.values(), peers, now),
                    now,
                )
            if self.mode == "exploring":
                # A full camera sweep at route stops discovers sites in either direction.
                if self.survey_started is None:
                    self.survey_started, self.survey_yaw, self.survey_angle = now, pose[2], 0.0
                self.survey_angle += abs(wrap(pose[2] - self.survey_yaw))
                self.survey_yaw = pose[2]
                if self.survey_angle < 2 * math.pi and now - self.survey_started < 25:
                    self.navigator.state = "surveying"
                    return self.navigator.guard(
                        pose,
                        (0.0, 0.5),
                        self.navigator.obstacles(self.known_targets.values(), peers, now),
                        now,
                    )
                self.waypoint_index += 1
                self.survey_started = None
            return 0.0, 0.0
        navigation_goal = self.approach if self.mode == "inspecting" else destination
        command = self.navigator.command(
            pose, navigation_goal, self.known_targets.values(), peers, now
        )
        if self.navigator.state in ("path_blocked", "obstacle_stop", "clearance_stop"):
            self.blocked_since = now if self.blocked_since is None else self.blocked_since
            if now - self.blocked_since > 12:
                if self.goal:
                    self.finish(False, "path_blocked")
                elif self.mode == "exploring":
                    self.waypoint_index += 1
                self.blocked_since = None
        else:
            self.blocked_since = None
        return command

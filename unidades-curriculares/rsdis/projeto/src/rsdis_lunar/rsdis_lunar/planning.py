"""Bounded planar A* with circular obstacles and continuous edge checks.

An obstacle is (x, y) or (x, y, radius). Clearance is the rover's inflated
footprint, added to each obstacle's own radius. No image or world truth is read.
"""

import heapq
import math

DEFAULT_BOUNDS = (-36.0, 36.0, -26.0, 26.0)


def in_bounds(point, bounds, clearance=0.0):
    return (
        bounds[0] + clearance <= point[0] <= bounds[1] - clearance
        and bounds[2] + clearance <= point[1] <= bounds[3] - clearance
    )


def segment_clear(start, end, obstacles, clearance=0.95):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length2 = dx * dx + dy * dy
    for obstacle in obstacles:
        ox, oy = obstacle[:2]
        radius = clearance + (obstacle[2] if len(obstacle) > 2 else 0.0)
        t = (
            0.0
            if length2 == 0
            else max(0.0, min(1.0, ((ox - start[0]) * dx + (oy - start[1]) * dy) / length2))
        )
        separation = math.hypot(start[0] + t * dx - ox, start[1] + t * dy - oy)
        initial = math.hypot(start[0] - ox, start[1] - oy)
        # Only a monotonically outward escape from an inflated disk is permitted.
        escaping = (
            initial < radius
            and length2 > 0
            and (start[0] - ox) * dx + (start[1] - oy) * dy >= 0
            and math.hypot(end[0] - ox, end[1] - oy) > initial
        )
        if separation < radius - 1e-8 and not escaping:
            return False
    return True


def plan_path(start, goal, obstacles, resolution=0.5, clearance=0.95, bounds=DEFAULT_BOUNDS):
    """Return a collision-checked polyline, or None when no route exists."""
    obstacles = tuple(obstacles)
    start, goal = tuple(start[:2]), tuple(goal[:2])
    if not in_bounds(start, bounds, clearance) or not in_bounds(goal, bounds, clearance):
        return None
    if not segment_clear(goal, goal, obstacles, clearance):
        return None
    if segment_clear(start, goal, obstacles, clearance):
        return [start, goal]
    origin = bounds[0], bounds[2]

    def cell(position):
        return tuple(round((position[i] - origin[i]) / resolution) for i in range(2))

    def point(c):
        return tuple(c[i] * resolution + origin[i] for i in range(2))

    first = cell(start)
    queue = [(math.dist(start, goal), 0.0, first)]
    costs, previous = {first: 0.0}, {}
    last = None
    while queue:
        _, cost, current = heapq.heappop(queue)
        if cost != costs[current]:
            continue
        position = start if current == first else point(current)
        if math.dist(position, goal) <= resolution * 1.5 and segment_clear(
            position, goal, obstacles, clearance
        ):
            last = current
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            neighbour = current[0] + dx, current[1] + dy
            candidate = point(neighbour)
            if not in_bounds(candidate, bounds, clearance):
                continue
            if not segment_clear(position, candidate, obstacles, clearance):
                continue
            new_cost = cost + math.dist(position, candidate)
            if new_cost < costs.get(neighbour, math.inf):
                costs[neighbour], previous[neighbour] = new_cost, current
                heapq.heappush(queue, (new_cost + math.dist(candidate, goal), new_cost, neighbour))
    if last is None:
        return None
    reverse = [goal]
    while last != first:
        reverse.append(point(last))
        last = previous[last]
    route = [start, *reversed(reverse)]
    result, index = [start], 0
    while index < len(route) - 1:
        following = next(
            j
            for j in range(len(route) - 1, index, -1)
            if segment_clear(route[index], route[j], obstacles, clearance)
        )
        result.append(route[following])
        index = following
    return result


def next_waypoint(start, goal, obstacles, resolution=0.5, clearance=0.95, bounds=DEFAULT_BOUNDS):
    path = plan_path(start, goal, obstacles, resolution, clearance, bounds)
    return path[1] if path and len(path) > 1 else None

"""Small planar A* detours around shared marker locations.

This avoids driving through a marker after inspecting it. It does not infer rocks,
terrain traversability, or a map from images; replacing it with Nav2 is future work.
"""

import heapq
import math


def segment_clear(start, end, obstacles, clearance=0.95):
    dx, dy = end[0] - start[0], end[1] - start[1]
    length2 = dx * dx + dy * dy
    for ox, oy in obstacles:
        t = (
            0
            if length2 == 0
            else max(0, min(1, ((ox - start[0]) * dx + (oy - start[1]) * dy) / length2))
        )
        closest = math.hypot(start[0] + t * dx - ox, start[1] + t * dy - oy)
        # Allow escape if an imperfect detection placed the rover inside a keep-out disk.
        if math.hypot(start[0] - ox, start[1] - oy) < clearance:
            if math.hypot(end[0] - ox, end[1] - oy) > math.hypot(start[0] - ox, start[1] - oy):
                continue
        if closest < clearance:
            return False
    return True


def next_waypoint(start, goal, obstacles, resolution=0.5, clearance=0.95):
    obstacles = list(obstacles)
    if segment_clear(start, goal, obstacles, clearance):
        return tuple(goal)
    origin = (-18.0, -13.0)

    def cell(point):
        return (
            round((point[0] - origin[0]) / resolution),
            round((point[1] - origin[1]) / resolution),
        )

    def point(c):
        return (c[0] * resolution + origin[0], c[1] * resolution + origin[1])

    first = cell(start)
    queue = [(math.dist(start[:2], goal), 0.0, first)]
    costs, previous = {first: 0.0}, {}
    last = None
    while queue:
        _, cost, current = heapq.heappop(queue)
        if cost != costs[current]:
            continue
        # A rounded start cell may lie inside a disk even when the actual rover
        # is outside. Expand the first edges from the actual continuous pose.
        position = tuple(start[:2]) if current == first else point(current)
        if math.dist(position, goal) <= 0.75 and segment_clear(
            position, goal, obstacles, clearance
        ):
            last = current
            break
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            neighbour = current[0] + dx, current[1] + dy
            if not (0 <= neighbour[0] <= 72 and 0 <= neighbour[1] <= 52):
                continue
            candidate = point(neighbour)
            if not segment_clear(position, candidate, obstacles, clearance):
                continue
            new_cost = cost + resolution * math.hypot(dx, dy)
            if new_cost < costs.get(neighbour, math.inf):
                costs[neighbour], previous[neighbour] = new_cost, current
                heapq.heappush(queue, (new_cost + math.dist(candidate, goal), new_cost, neighbour))
    if last is None:
        return None
    path = [tuple(goal)]
    while last != first:
        path.append(point(last))
        last = previous[last]
    # Use the farthest visible path point to avoid steering at each grid cell.
    for waypoint in path:
        if segment_clear(start, waypoint, obstacles, clearance):
            return waypoint
    return None

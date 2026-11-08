"""Geometry of the optional, genuine Gazebo overhead recording camera."""

import math


def observer_height(config):
    width, height = config.get("ground_size", [40, 30])
    return max(width, height * 4 / 3) * 0.55 / math.tan(0.7)


def project_overhead(position, config, width=960, height=720):
    focal = width / (2 * math.tan(0.7))
    z = observer_height(config) - 0.5
    return int(width / 2 + position[0] * focal / z), int(height / 2 - position[1] * focal / z)

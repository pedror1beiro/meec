#!/usr/bin/env python3
"""Physical drive regression: turn beyond 360 degrees, then translate.

No mission agents run during this calibration. Opposite rotations check both
turn directions, and raw attitudes expose tipping or joint-axis mistakes.
"""

import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time


def main():
    import rclpy
    from rclpy.node import Node
    from rclpy.parameter import Parameter
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import Twist
    from nav_msgs.msg import Odometry
    from rsdis_lunar.common import pose_tuple
    from rsdis_lunar.core import wrap

    root = Path(__file__).resolve().parents[1]
    output = root / "results" / ("drive_" + str(time.time_ns()))
    output.mkdir(parents=True)
    log = (output / "launch.log").open("w", encoding="utf-8")
    process = subprocess.Popen(
        [
            "ros2",
            "launch",
            "rsdis_lunar",
            "prototype.launch.py",
            "headless:=true",
            "autonomy:=false",
            "dashboard:=false",
            "config:=" + str(root / "src/rsdis_lunar/config/mission_small.json"),
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    rclpy.init()
    node = Node("drive_regression", parameter_overrides=[Parameter("use_sim_time", value=True)])
    poses, rotation, attitude = {}, {}, {}
    trace, subscriptions = [], []
    names = ["rover1", "rover2"]
    publishers = {name: node.create_publisher(Twist, f"/{name}/cmd_vel", 10) for name in names}

    def receive(msg, name):
        pose = pose_tuple(msg.pose.pose)
        if name in poses:
            rotation[name] = rotation.get(name, 0.0) + wrap(pose[2] - poses[name][2])
        poses[name] = pose
        q = msg.pose.pose.orientation
        roll = math.atan2(2 * (q.w * q.x + q.y * q.z), 1 - 2 * (q.x * q.x + q.y * q.y))
        pitch = math.asin(max(-1, min(1, 2 * (q.w * q.y - q.z * q.x))))
        attitude[name] = dict(quaternion=[q.x, q.y, q.z, q.w], roll=roll, pitch=pitch)

    for name in names:
        subscriptions.append(
            node.create_subscription(
                Odometry, f"/{name}/odom", lambda m, n=name: receive(m, n), qos_profile_sensor_data
            )
        )
    started, sim_start, drive_starts, last_trace = time.monotonic(), None, {}, -1
    try:
        while time.monotonic() - started < 150 and process.poll() is None:
            rclpy.spin_once(node, timeout_sec=0.02)
            now = node.get_clock().now().nanoseconds / 1e9
            if len(poses) != 2 or now <= 1:
                continue
            sim_start = now if sim_start is None else sim_start
            elapsed = now - sim_start
            for i, name in enumerate(names):
                command = Twist()
                if 1 < elapsed < 26:
                    command.angular.z = 0.35 if i == 0 else -0.35
                elif 28 < elapsed < 33:
                    drive_starts.setdefault(name, poses[name][:2])
                    command.linear.x = 0.25
                publishers[name].publish(command)
            if int(elapsed) != last_trace:
                last_trace = int(elapsed)
                trace.append(
                    dict(
                        time=elapsed,
                        poses=dict(poses),
                        rotation=dict(rotation),
                        attitude=dict(attitude),
                    )
                )
            if elapsed >= 34:
                break
    finally:
        for pub in publishers.values():
            pub.publish(Twist())
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        node.destroy_node()
        rclpy.shutdown()
        log.close()
    distance = {name: math.dist(start, poses[name][:2]) for name, start in drive_starts.items()}
    checks = dict(
        positive_turn=rotation.get("rover1", 0) > 6,
        negative_turn=rotation.get("rover2", 0) < -6,
        translation=len(distance) == 2 and all(d > 0.6 for d in distance.values()),
        level=bool(attitude)
        and all(abs(a["roll"]) < 0.15 and abs(a["pitch"]) < 0.15 for a in attitude.values()),
    )
    report = dict(
        passed=all(checks.values()),
        checks=checks,
        rotation=rotation,
        distance=distance,
        attitude=attitude,
    )
    (output / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output / "trace.json").write_text(json.dumps(trace), encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

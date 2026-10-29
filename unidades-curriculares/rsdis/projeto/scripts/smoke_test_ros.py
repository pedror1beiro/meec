#!/usr/bin/env python3
"""Linux integration gate: launch Gazebo, then require both robots' real sensor streams.

Run after sourcing ROS and this workspace. This never substitutes oracle detections.
"""

import argparse
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--complete-mission", action="store_true")
    parser.add_argument("--model", choices=["lightweight", "viper"], default="lightweight")
    parser.add_argument("--simulation", type=Path)
    args = parser.parse_args()
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from nav_msgs.msg import Odometry
    from sensor_msgs.msg import CameraInfo, Image, JointState
    from rsdis_interfaces.msg import Detection, TaskGoal
    from rsdis_lunar.common import load_config

    root = Path(__file__).resolve().parents[1]
    config = load_config(root / "src/rsdis_lunar/config/mission.json")
    run_id = str(time.time_ns())
    output = root / "results" / ("smoke_" + run_id)
    output.mkdir(parents=True)
    log = (output / "launch.log").open("w", encoding="utf-8")
    command = [
        "ros2",
        "launch",
        "rsdis_lunar",
        "prototype.launch.py",
        "headless:=true",
        "output:=" + str(output),
        "config:=" + str(root / "src/rsdis_lunar/config/mission.json"),
        "model:=" + args.model,
        "upstream_simulation:="
        + str((args.simulation or root / "third_party/simulation").resolve()),
    ]
    # Separate process group allows graceful shutdown of launch and its descendants.
    process = subprocess.Popen(
        command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
    )
    rclpy.init()
    node = Node("rsdis_smoke_test")
    checks = {}
    subscriptions = []
    starts = {}
    for spec in config["rovers"]:
        name = spec["id"]
        checks[name + "/motion"] = False
        topics = [
            ("odom", Odometry),
            ("camera/image", Image),
            ("camera/info", CameraInfo),
        ]
        if args.model == "viper":
            topics.append(("joint_states", JointState))
        for topic, kind in topics:
            key = name + "/" + topic
            checks[key] = False

            def receive(msg, key=key, topic=topic, rover=name):
                if topic == "camera/image":
                    checks[key] = msg.width > 0 and msg.height > 0 and len(msg.data) > 0
                elif topic == "camera/info":
                    checks[key] = msg.k[0] > 0
                elif topic == "joint_states":
                    names = {n.split("::")[-1] for n in msg.name}
                    checks[key] = (
                        all(
                            w + "_wheel_axle_joint" in names
                            for w in ("front_left", "rear_left", "front_right", "rear_right")
                        )
                        and len(msg.position) >= 4
                    )
                else:
                    checks[key] = msg.header.frame_id == "world"
                    position = (msg.pose.pose.position.x, msg.pose.pose.position.y)
                    starts.setdefault(rover, position)
                    if math.dist(starts[rover], position) > 0.15:
                        checks[rover + "/motion"] = True

            subscriptions.append(
                node.create_subscription(kind, "/" + key, receive, qos_profile_sensor_data)
            )
    checks["camera_detection"] = False
    checks["task_assignment"] = False
    subscriptions.append(
        node.create_subscription(
            Detection,
            "/mission/detections",
            lambda msg: checks.__setitem__(
                "camera_detection", msg.target_id in {t["id"] for t in config["targets"]}
            ),
            10,
        )
    )
    subscriptions.append(
        node.create_subscription(
            TaskGoal,
            "/mission/goals",
            lambda msg: checks.__setitem__("task_assignment", bool(msg.task_id)),
            10,
        )
    )
    started = time.monotonic()
    success = False
    try:
        while time.monotonic() - started < args.timeout and process.poll() is None:
            rclpy.spin_once(node, timeout_sec=0.2)
            if all(checks.values()):
                if not args.complete_mission:
                    success = True
                    break
                summaries = list(output.glob("*/summary.json"))
                if summaries:
                    summary = json.loads(summaries[0].read_text())
                    success = summary["reason"] == "all_targets_confirmed_and_returned"
                    break
    finally:
        if process.poll() is None:
            os.killpg(process.pid, signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                process.wait(timeout=10)
        node.destroy_node()
        rclpy.shutdown()
        log.close()
    report = {
        "passed": success,
        "model": args.model,
        "checks": checks,
        "complete_mission_requested": args.complete_mission,
        "wall_seconds": round(time.monotonic() - started, 2),
    }
    (output / "smoke_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Logs: {output}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

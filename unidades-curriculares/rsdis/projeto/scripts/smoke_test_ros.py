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
from urllib.error import URLError
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--timeout", type=float, default=180)
    parser.add_argument("--complete-mission", action="store_true")
    parser.add_argument("--model", choices=["lightweight", "viper"], default="lightweight")
    parser.add_argument("--simulation", type=Path)
    parser.add_argument("--config", type=Path)
    parser.add_argument("--dashboard", action="store_true", help="Check console images and pause/resume services")
    args = parser.parse_args()
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from nav_msgs.msg import Odometry
    from geometry_msgs.msg import Twist
    from std_msgs.msg import String
    from sensor_msgs.msg import CameraInfo, Image, JointState, LaserScan
    from rsdis_interfaces.msg import Detection, TaskGoal
    from rsdis_lunar.common import load_config
    from rsdis_lunar.safety_audit import ClearanceAudit
    from rsdis_lunar.viper import profile

    root = Path(__file__).resolve().parents[1]
    config_path = (args.config or root / "src/rsdis_lunar/config/mission.json").resolve()
    config = load_config(config_path)
    if args.model == "viper":
        config = profile(config)
    audit = ClearanceAudit(config)
    poses = {}
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
        "config:=" + str(config_path),
        "model:=" + args.model,
        "dashboard:=" + ("true" if args.dashboard else "false"),
        "dashboard_port:=8876",
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
    last_commands = {}
    debug = {}
    debug_log = (output / "navigation.jsonl").open("w", encoding="utf-8")
    for spec in config["rovers"]:
        name = spec["id"]
        checks[name + "/motion"] = False
        def receive_debug(msg, name=name):
            record = json.loads(msg.data)
            debug[name] = record
            debug_log.write(json.dumps({"rover": name, **record}) + "\n")
            debug_log.flush()
        subscriptions.append(node.create_subscription(String, f"/{name}/navigation_debug", receive_debug, 10))
        subscriptions.append(node.create_subscription(
            Twist, f"/{name}/cmd_vel",
            lambda msg, n=name: last_commands.__setitem__(n, (msg.linear.x, msg.angular.z)), 10,
        ))
        topics = [
            ("odom", Odometry),
            ("camera/image", Image),
            ("camera/info", CameraInfo),
            ("scan", LaserScan),
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
                    checks[key] = bool(msg.k[0] > 0)
                elif topic == "scan":
                    checks[key] = bool(len(msg.ranges) >= 180 and msg.angle_increment > 0)
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
                    poses[rover] = position
                    if len(poses) == len(config["rovers"]):
                        audit.sample(poses)
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
    next_http = 0.0
    pause_sent = resume_sent = pause_stopped = False
    paused_time = None
    console_error = None
    progress = {}
    stall = None
    if args.dashboard:
        checks.update(console_state=False, console_cameras=False, pause_resume=False)

    def http(path, body=None):
        request = Request(
            "http://127.0.0.1:8876" + path,
            data=json.dumps(body).encode() if body else None,
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=1) as response:
            return response.read()

    try:
        while time.monotonic() - started < args.timeout and process.poll() is None:
            rclpy.spin_once(node, timeout_sec=0.2)
            if args.complete_mission:
                for name, sample in debug.items():
                    anchor, last_progress = progress.setdefault(name, (sample["pose"][:2], sample["time"]))
                    if sample.get("mode") != "inspecting" or math.dist(anchor, sample["pose"][:2]) > 0.15:
                        progress[name] = sample["pose"][:2], sample["time"]
                    elif sample["time"] - last_progress > 45:
                        stall = name + ": inspection made no positional progress for 45 simulation seconds"
                if stall:
                    break
            if args.dashboard and time.monotonic() >= next_http:
                next_http = time.monotonic() + 0.5
                try:
                    state = json.loads(http("/api/state"))
                    checks["console_state"] = bool(state.get("bounds") and len(state.get("rovers", [])) == len(config["rovers"]))
                    if checks["console_state"] and not checks["console_cameras"]:
                        checks["console_cameras"] = all(len(http(f"/camera/{r['id']}.jpg")) > 500 for r in config["rovers"])
                    ready = all(v for k, v in checks.items() if k != "pause_resume")
                    if ready and not pause_sent:
                        http("/api/command", {"action": "pause"})
                        pause_sent = True
                    if pause_sent and state.get("paused"):
                        paused_time = state["time"] if paused_time is None else paused_time
                        if state["time"] - paused_time >= 0.5 and not resume_sent:
                            pause_stopped = len(last_commands) == len(config["rovers"]) and all(abs(v) < 1e-6 and abs(w) < 1e-6 for v, w in last_commands.values())
                            http("/api/command", {"action": "resume"})
                            resume_sent = True
                    if resume_sent and not state.get("paused"):
                        checks["pause_resume"] = pause_stopped
                    console_error = None
                except (URLError, ValueError, TimeoutError, OSError) as error:
                    console_error = str(error)
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
        debug_log.close()
    report = {
        "passed": success,
        "model": args.model,
        "checks": {key: bool(value) for key, value in checks.items()},
        "clearance_audit": audit.report(),
        "complete_mission_requested": args.complete_mission,
        "console_error": console_error,
        "last_navigation": debug,
        "stall": stall,
        "wall_seconds": round(time.monotonic() - started, 2),
    }
    if audit.violations:
        report["passed"] = success = False
    (output / "smoke_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"Logs: {output}")
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Run one real Gazebo experiment and inject any configured temporary failure."""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import platform
import signal
import subprocess
import sys
import time
from xml.etree import ElementTree as ET


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--strategy", choices=["nearest", "energy"], required=True)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--wall-timeout", type=float, default=1800)
    parser.add_argument("--gui", action="store_true")
    parser.add_argument("--model", choices=["lightweight", "viper"], default="lightweight")
    parser.add_argument("--simulation", type=Path)
    args = parser.parse_args()
    if os.name == "nt":
        parser.error(
            "Run this supervisor in the Linux ROS environment; use offline_demo.py on Windows"
        )
    import rclpy
    from rclpy.node import Node
    from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, qos_profile_sensor_data
    from rosgraph_msgs.msg import Clock
    from std_msgs.msg import Bool
    from std_srvs.srv import SetBool
    from nav_msgs.msg import Odometry
    from rsdis_lunar.common import load_config, stamp_seconds
    from rsdis_lunar.provenance import source_fingerprint
    from rsdis_lunar.safety_audit import ClearanceAudit
    from rsdis_lunar.viper import profile
    from ament_index_python.packages import get_package_share_directory
    import cv2

    root = Path(__file__).resolve().parents[1]
    config_path = args.config.resolve()
    config = load_config(config_path)
    audit = ClearanceAudit(profile(config) if args.model == "viper" else config)
    poses = {}
    output = (
        args.output
        or root
        / "results"
        / ("gazebo_" + args.strategy + "_" + datetime.now().strftime("%Y%m%d_%H%M%S_%f"))
    ).resolve()
    output.mkdir(parents=True, exist_ok=False)
    log = (output / "launch.log").open("w", encoding="utf-8")
    command = [
        "ros2",
        "launch",
        "rsdis_lunar",
        "prototype.launch.py",
        "headless:=" + ("false" if args.gui else "true"),
        "config:=" + str(config_path),
        "strategy:=" + args.strategy,
        "output:=" + str(output),
        "model:=" + args.model,
        "upstream_simulation:="
        + str((args.simulation or root / "third_party/simulation").resolve()),
    ]
    metadata = {
        "config_file": str(config_path),
        "strategy": args.strategy,
        "model": args.model,
        "command": command,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "ros_distro": os.environ.get("ROS_DISTRO"),
        "ros_domain_id": os.environ.get("ROS_DOMAIN_ID", "0"),
        "failure_interventions": [],
        "started_utc": datetime.now(timezone.utc).isoformat(),
        "source_sha256": source_fingerprint(root),
        "opencv_version": cv2.__version__,
        "ros_package_versions": {},
    }
    for package in ("rclpy", "ros_gz_sim", "ros_gz_bridge", "xacro"):
        try:
            manifest = Path(get_package_share_directory(package)) / "package.xml"
            metadata["ros_package_versions"][package] = (
                ET.parse(manifest).getroot().findtext("version")
            )
        except (OSError, KeyError, LookupError):
            metadata["ros_package_versions"][package] = None
    if (root / "upstream.lock.json").exists():
        metadata["upstream_revisions"] = json.loads((root / "upstream.lock.json").read_text())
    process = subprocess.Popen(
        command, stdout=log, stderr=subprocess.STDOUT, start_new_session=True
    )
    rclpy.init()
    node = Node("experiment_supervisor")
    subscriptions = []

    def on_odom(msg, name):
        poses[name] = msg.pose.pose.position.x, msg.pose.pose.position.y
        if len(poses) == len(config["rovers"]):
            audit.sample(poses)

    for spec in config["rovers"]:
        name = spec["id"]
        subscriptions.append(
            node.create_subscription(
                Odometry, f"/{name}/odom", lambda m, n=name: on_odom(m, n), qos_profile_sensor_data
            )
        )
    state = {"sim": 0.0, "finished": False}
    _clock_subscription = node.create_subscription(
        Clock,
        "/clock",
        lambda msg: state.__setitem__("sim", stamp_seconds(msg.clock)),
        qos_profile_sensor_data,
    )
    latched = QoSProfile(
        depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL
    )
    _finished_subscription = node.create_subscription(
        Bool, "/mission/finished", lambda msg: state.__setitem__("finished", msg.data), latched
    )
    failure = config.get("failure")
    client = (
        node.create_client(SetBool, "/" + failure["rover_id"] + "/set_enabled") if failure else None
    )
    disabled = restored = False
    pending = []
    start = time.monotonic()
    outcome = "wall_timeout"
    try:
        while time.monotonic() - start < args.wall_timeout:
            if process.poll() is not None:
                outcome = "launch_exited"
                break
            rclpy.spin_once(node, timeout_sec=0.1)
            if failure and client.service_is_ready():
                if not disabled and state["sim"] >= failure["at"]:
                    future = client.call_async(SetBool.Request(data=False))
                    pending.append(future)
                    metadata["failure_interventions"].append(
                        {"sim_seconds": state["sim"], "enabled": False}
                    )
                    disabled = True
                if (
                    disabled
                    and not restored
                    and state["sim"] >= failure["at"] + failure["duration"]
                ):
                    future = client.call_async(SetBool.Request(data=True))
                    pending.append(future)
                    metadata["failure_interventions"].append(
                        {"sim_seconds": state["sim"], "enabled": True}
                    )
                    restored = True
            if state["finished"]:
                outcome = "mission_finished"
                break
    except KeyboardInterrupt:
        outcome = "interrupted"
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.wait()
        metadata["supervisor_outcome"] = outcome
        metadata["clearance_audit"] = audit.report()
        metadata["wall_seconds"] = round(time.monotonic() - start, 3)
        metadata["failure_service_results"] = [
            bool(f.done() and f.exception() is None and f.result().success) for f in pending
        ]
        metadata["intervention_valid"] = not failure or (
            disabled and restored and len(pending) == 2 and all(metadata["failure_service_results"])
        )
        (output / "run_metadata.json").write_text(
            json.dumps(metadata, indent=2) + "\n", encoding="utf-8"
        )
        node.destroy_node()
        rclpy.shutdown()
        log.close()
    print(output)
    summaries = list(output.glob("*/summary.json"))
    if summaries:
        summary = json.loads(summaries[0].read_text())
        print(json.dumps(summary, indent=2))
        if not metadata["intervention_valid"]:
            print(
                "The planned failure intervention was not completed; inspect metadata.",
                file=sys.stderr,
            )
            return 2
        return (
            0
            if summary["reason"] == "all_targets_confirmed_and_returned" and not audit.violations
            else 1
        )
    print(f"No mission summary; supervisor outcome: {outcome}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())

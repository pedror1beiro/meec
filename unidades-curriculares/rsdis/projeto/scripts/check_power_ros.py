#!/usr/bin/env python3
"""Gazebo energy bench: sunlight versus shade, discharge, then physical dock recharge."""

import json
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
    from sensor_msgs.msg import BatteryState
    from std_msgs.msg import Float32
    from std_srvs.srv import SetBool

    root = Path(__file__).resolve().parents[1]
    output = root / "results" / ("power_bench_" + str(time.time_ns()))
    output.mkdir(parents=True)
    config = json.loads((root / "src/rsdis_lunar/config/mission_small.json").read_text())
    # An actual rendered canopy shades rover2; rover1 remains exposed.
    config["shade_canopies"] = [dict(position=[-10, 3, 2.5], size=[6, 4, 0.1])]
    config["rovers"][0]["battery"] = 0.4
    config["rovers"][1]["battery"] = 0.4
    config_file = output / "config.json"
    config_file.write_text(json.dumps(config, indent=2))
    log = (output / "launch.log").open("w")
    process = subprocess.Popen(
        [
            "ros2",
            "launch",
            "rsdis_lunar",
            "prototype.launch.py",
            "headless:=true",
            "autonomy:=false",
            "dashboard:=false",
            "energy_source:=gazebo",
            "config:=" + str(config_file),
            "output:=" + str(output),
        ],
        stdout=log,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )
    rclpy.init()
    node = Node("energy_bench", parameter_overrides=[Parameter("use_sim_time", value=True)])
    states, solar, trace, responses, futures = {}, {}, [], [], []
    clients, subscriptions = {}, []
    for name in ("rover1", "rover2"):
        subscriptions.append(
            node.create_subscription(
                BatteryState,
                f"/{name}/battery",
                lambda m, n=name: states.__setitem__(n, m),
                qos_profile_sensor_data,
            )
        )
        subscriptions.append(
            node.create_subscription(
                Float32,
                f"/{name}/energy/solar_w",
                lambda m, n=name: solar.__setitem__(n, m.data),
                qos_profile_sensor_data,
            )
        )
        clients[name] = node.create_client(SetBool, f"/{name}/set_dock_enabled")
    started, origin, phase, last_record = time.monotonic(), None, 0, -1
    try:
        while time.monotonic() - started < 240 and process.poll() is None:
            rclpy.spin_once(node, timeout_sec=0.03)
            now = node.get_clock().now().nanoseconds / 1e9
            if len(states) < 2 or len(solar) < 2 or now < 2:
                continue
            if origin is None:
                origin = now
            elapsed = now - origin
            if phase == 0 and all(c.service_is_ready() for c in clients.values()):
                futures += [c.call_async(SetBool.Request(data=False)) for c in clients.values()]
                phase = 1
            if phase == 1 and elapsed > 12:
                futures += [c.call_async(SetBool.Request(data=True)) for c in clients.values()]
                phase = 2
            for future in list(futures):
                if future.done():
                    responses.append(bool(future.result().success))
                    futures.remove(future)
            if int(elapsed * 2) != last_record:
                last_record = int(elapsed * 2)
                trace.append(
                    dict(
                        time=elapsed,
                        phase=phase,
                        solar=dict(solar),
                        battery={
                            n: dict(
                                soc=m.percentage,
                                voltage=m.voltage,
                                current=m.current,
                                charge=m.charge,
                                capacity=m.capacity,
                            )
                            for n, m in states.items()
                        },
                    )
                )
            if elapsed > 25:
                break
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
        node.destroy_node()
        rclpy.shutdown()
        log.close()
    discharge = [f for f in trace if 5 < f["time"] < 11]
    charge = [f for f in trace if f["time"] > 20]
    enough = len(discharge) >= 5 and len(charge) >= 5
    checks = dict(
        services=len(responses) == 4 and all(responses),
        actual_sunlight=bool(discharge)
        and sum(f["solar"]["rover1"] for f in discharge) / len(discharge) > 1,
        rendered_shade=bool(discharge) and max(f["solar"]["rover2"] for f in discharge) < 0.1,
        ros_units=bool(trace)
        and all(
            0 <= b["soc"] <= 1 and 0 <= b["charge"] <= b["capacity"] and b["voltage"] > 0
            for f in trace
            for b in f["battery"].values()
        ),
        discharge=enough
        and all(
            discharge[-1]["battery"][n]["soc"] < discharge[0]["battery"][n]["soc"]
            and discharge[-1]["battery"][n]["current"] < 0
            for n in states
        ),
        recharge=enough
        and all(
            charge[-1]["battery"][n]["soc"] > discharge[-1]["battery"][n]["soc"] + 0.05
            and charge[-1]["battery"][n]["current"] > 0
            for n in states
        ),
    )
    report = dict(
        passed=all(checks.values()),
        checks=checks,
        samples=len(trace),
        wall_seconds=round(time.monotonic() - started, 2),
    )
    (output / "report.json").write_text(json.dumps(report, indent=2))
    (output / "trace.json").write_text(json.dumps(trace))
    print(json.dumps(report, indent=2), flush=True)
    print("Logs: " + str(output), flush=True)
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

"""Per-rover mission gateways with local sensing, delivery faults and bounded retries."""

import json
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from std_msgs.msg import String
from std_srvs.srv import SetBool
from rsdis_interfaces.msg import Detection, RoverStatus, TaskGoal, TaskResult

from .common import load_config
from .communications import LinkEmulator
from .qos import mission_qos


class MissionNetwork(Node):
    def __init__(self):
        super().__init__("mission_network")
        self.declare_parameter("config", "")
        self.declare_parameter("output", "")
        config = load_config(self.get_parameter("config").value)
        self.link = LinkEmulator(config["network"])
        self.publishers_by_channel = {
            "status": self.create_publisher(RoverStatus, "/mission/status", mission_qos()),
            "detections": self.create_publisher(Detection, "/mission/detections", mission_qos()),
            "results": self.create_publisher(TaskResult, "/mission/results", mission_qos()),
        }
        self.goals, self.ids = {}, {r["id"] for r in config["rovers"]}
        for name in sorted(self.ids):
            self.link.enabled[name] = True
            self.goals[name] = self.create_publisher(
                TaskGoal, f"/{name}/inbox/goals", mission_qos()
            )
            self.create_subscription(
                RoverStatus, f"/{name}/local/status", self.on_status, qos_profile_sensor_data
            )
            self.create_subscription(
                Detection,
                f"/{name}/local/detections",
                lambda m, n=name: self.link.submit("detections", n, m, self.now(), ttl=0.8),
                mission_qos(),
            )
            self.create_subscription(
                TaskResult,
                f"/{name}/local/results",
                lambda m, n=name: self.link.submit(
                    "results", n, m, self.now(), reliable=True, ttl=8, key=m.task_id
                ),
                mission_qos(),
            )
            self.create_service(
                SetBool,
                f"/{name}/set_link_enabled",
                lambda req, res, n=name: self.set_enabled(n, req, res),
            )
        self.create_subscription(TaskGoal, "/mission/goals", self.on_goal, mission_qos())
        self.stats = self.create_publisher(String, "/mission/network", mission_qos())
        self.output = (
            Path(self.get_parameter("output").value) if self.get_parameter("output").value else None
        )
        if self.output:
            self.output.mkdir(parents=True, exist_ok=True)
            self.trace = (self.output / "network.jsonl").open("w", encoding="utf-8")
        self.last_report = -1e9
        self.create_timer(0.02, self.tick)

    def now(self):
        return self.get_clock().now().nanoseconds / 1e9

    def set_enabled(self, name, request, response):
        self.link.enabled[name] = request.data
        response.success, response.message = (
            True,
            name + (": link connected" if request.data else ": link disconnected"),
        )
        return response

    def on_status(self, msg):
        if msg.rover_id not in self.ids:
            return
        self.link.positions[msg.rover_id] = (msg.pose.position.x, msg.pose.position.y)
        self.link.submit("status", msg.rover_id, msg, self.now(), ttl=0.8)

    def on_goal(self, msg):
        if msg.rover_id in self.ids:
            self.link.submit(
                "goals",
                msg.rover_id,
                msg,
                self.now(),
                reliable=True,
                ttl=max(0.1, msg.lease_seconds),
                key=msg.task_id,
            )

    def tick(self):
        now = self.now()
        for packet in self.link.poll(now):
            publisher = (
                self.goals[packet.rover]
                if packet.channel == "goals"
                else self.publishers_by_channel[packet.channel]
            )
            publisher.publish(packet.payload)
        if now - self.last_report >= 1:
            self.last_report = now
            report = self.link.report(now)
            self.stats.publish(String(data=json.dumps(report)))
            if self.output:
                self.trace.write(json.dumps(report) + "\n")
                self.trace.flush()

    def close(self):
        if self.output:
            (self.output / "network_report.json").write_text(
                json.dumps(self.link.report(self.now()), indent=2)
            )
            self.trace.close()


def main(args=None):
    rclpy.init(args=args)
    node = MissionNetwork()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

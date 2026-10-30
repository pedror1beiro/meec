from datetime import datetime
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from std_msgs.msg import Bool
from std_srvs.srv import SetBool, Trigger
from rsdis_interfaces.msg import Detection, RoverStatus, TaskGoal, TaskResult

from .common import load_config, pose_tuple, stamp_seconds
from .core import Coordinator, Snapshot
from .metrics import Metrics


class MissionManager(Node):
    def __init__(self):
        super().__init__("mission_manager")
        self.declare_parameter("config", "")
        self.declare_parameter("strategy", "energy")
        self.declare_parameter("output", str(Path.cwd() / "results"))
        config = load_config(self.get_parameter("config").value)
        strategy = self.get_parameter("strategy").value
        self.coordinator = Coordinator(config, strategy)
        self.expected = {t["id"] for t in config["targets"]}
        directory = Path(self.get_parameter("output").value) / datetime.now().strftime(
            "%Y%m%d_%H%M%S_%f"
        )
        self.metrics = Metrics(directory, config, strategy, "gazebo")
        self.start = None
        self.last_elapsed = 0.0
        self.finished = False
        self.return_requested = False
        self.paused = False
        self.paused_at = None
        self.paused_seconds = 0.0
        self.operator_return = False
        self.goal_pub = self.create_publisher(TaskGoal, "/mission/goals", 10)
        latched = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.finish_pub = self.create_publisher(Bool, "/mission/finished", latched)
        self.return_pub = self.create_publisher(Bool, "/mission/return_home", latched)
        self.pause_pub = self.create_publisher(Bool, "/mission/paused", latched)
        self.create_service(SetBool, "/mission/set_paused", self.on_pause)
        self.create_service(Trigger, "/mission/recall", self.on_recall)
        self.create_subscription(RoverStatus, "/mission/status", self.on_status, 10)
        self.create_subscription(Detection, "/mission/detections", self.on_detection, 10)
        self.create_subscription(TaskResult, "/mission/results", self.on_result, 10)
        self.create_timer(0.5, self.tick)
        self.get_logger().info(f"Writing mission metrics to {directory}")

    def on_pause(self, request, response):
        if self.finished:
            response.success, response.message = False, "Mission already finished"
            return response
        now = self.now_seconds()
        if request.data and not self.paused:
            self.paused_at = now
        elif self.paused and not request.data:
            duration = now - self.paused_at
            self.paused_seconds += duration
            for target in self.coordinator.targets.values():
                if target.owner:
                    target.assigned_at += duration
        self.paused = request.data
        self.pause_pub.publish(Bool(data=self.paused))
        self.coordinator.event(now, "paused" if self.paused else "resumed")
        response.success, response.message = True, "Paused" if self.paused else "Resumed"
        return response

    def on_recall(self, request, response):
        if self.finished:
            response.success, response.message = False, "Mission already finished"
            return response
        if self.paused:
            self.on_pause(SetBool.Request(data=False), SetBool.Response())
        self.return_requested = self.operator_return = True
        self.return_pub.publish(Bool(data=True))
        self.coordinator.event(self.now_seconds(), "operator_return_requested")
        response.success, response.message = True, "Rovers returning to their own charging pads"
        return response

    def now_seconds(self):
        return self.get_clock().now().nanoseconds / 1e9

    def on_status(self, msg):
        self.coordinator.update(
            Snapshot(
                msg.rover_id,
                pose_tuple(msg.pose),
                msg.battery,
                msg.mode,
                stamp_seconds(msg.header.stamp),
                msg.distance_travelled,
                msg.energy_used,
            )
        )

    def on_detection(self, msg):
        if (
            self.start is None
            or msg.header.frame_id != "world"
            or msg.confidence < 0.65
            or msg.target_id not in self.expected
            or self.now_seconds() - stamp_seconds(msg.header.stamp) > 1.0
        ):
            return
        self.coordinator.observe(
            msg.target_id, (msg.position.x, msg.position.y), msg.observer, self.now_seconds()
        )

    def on_result(self, msg):
        if not self.finished:
            self.coordinator.result(
                msg.rover_id, msg.task_id, msg.success, self.now_seconds(), msg.detail
            )

    def finish(self, reason):
        if self.finished:
            return
        self.finished = True
        self.metrics.finish(self.coordinator, self.last_elapsed, reason)
        if rclpy.ok():
            self.finish_pub.publish(Bool(data=True))
        count = sum(t.confirmed for t in self.coordinator.targets.values())
        self.get_logger().info(
            f"Mission finished ({reason}): {count}/{len(self.expected)} confirmed"
        )

    def tick(self):
        if self.finished:
            return
        now = self.now_seconds()
        if self.start is None:
            if len(self.coordinator.rovers) != len(self.coordinator.homes):
                return
            if any(now - r.seen_at > 1 for r in self.coordinator.rovers.values()):
                return
            self.start = now
            self.metrics.origin = now
        self.last_elapsed = now - self.start
        if self.paused:
            self.metrics.record(self.coordinator, self.last_elapsed)
            return
        if self.last_elapsed - self.paused_seconds >= self.coordinator.config["mission_seconds"]:
            self.finish("time_limit")
            return
        goals = [] if self.return_requested else self.coordinator.tick(now)
        for goal in goals:
            msg = TaskGoal()
            msg.header.stamp = self.get_clock().now().to_msg()
            msg.header.frame_id = "world"
            msg.rover_id, msg.task_id, msg.target_id = goal.rover_id, goal.task_id, goal.target_id
            msg.position.x, msg.position.y = goal.position
            msg.lease_seconds = self.coordinator.config["lease_seconds"]
            self.goal_pub.publish(msg)
        self.metrics.record(self.coordinator, self.last_elapsed)
        if self.operator_return and all(
            r.mode == "parked" for r in self.coordinator.rovers.values()
        ):
            self.finish("operator_returned")
            return
        if self.expected and all(
            self.coordinator.targets.get(t) and self.coordinator.targets[t].confirmed
            for t in self.expected
        ):
            if not self.return_requested:
                self.return_requested = True
                self.return_pub.publish(Bool(data=True))
                self.coordinator.event(now, "return_home_requested")
            if all(r.mode == "parked" for r in self.coordinator.rovers.values()):
                self.finish("all_targets_confirmed_and_returned")


def main(args=None):
    rclpy.init(args=args)
    node = MissionManager()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if not node.finished:
            node.finish("interrupted")
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

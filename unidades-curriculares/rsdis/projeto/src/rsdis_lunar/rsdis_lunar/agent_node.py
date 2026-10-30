import math
import json

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, qos_profile_sensor_data
from geometry_msgs.msg import PoseStamped, Twist
from nav_msgs.msg import Odometry, Path
from sensor_msgs.msg import LaserScan
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool
from rsdis_interfaces.msg import Detection, RoverStatus, TaskGoal, TaskResult

from .common import load_config, pose_tuple, stamp_seconds
from .core import Goal, Rover, Snapshot
from .navigation import scan_points


class RoverAgent(Node):
    def __init__(self):
        super().__init__("rover_agent")
        self.declare_parameter("config", "")
        self.declare_parameter("rover_id", "")
        config = load_config(self.get_parameter("config").value)
        self.rover_id = self.get_parameter("rover_id").value
        spec = next(r for r in config["rovers"] if r["id"] == self.rover_id)
        self.rover = Rover(spec, config)
        self.rover.navigator.require_scan = True
        self.pose = None
        self.odom_received = -math.inf
        self.last_time = None
        self.mission_finished = False
        self.peers = {}
        prefix = "/" + self.rover_id
        self.velocity_pub = self.create_publisher(Twist, prefix + "/cmd_vel", 10)
        self.status_pub = self.create_publisher(RoverStatus, "/mission/status", 10)
        self.result_pub = self.create_publisher(TaskResult, "/mission/results", 10)
        self.nav_pub = self.create_publisher(String, prefix + "/navigation_state", 10)
        self.debug_pub = self.create_publisher(String, prefix + "/navigation_debug", 10)
        self.plan_pub = self.create_publisher(Path, prefix + "/plan", 10)
        self.create_subscription(Odometry, prefix + "/odom", self.on_odom, qos_profile_sensor_data)
        self.create_subscription(LaserScan, prefix + "/scan", self.on_scan, qos_profile_sensor_data)
        self.create_subscription(TaskGoal, "/mission/goals", self.on_goal, 10)
        self.create_subscription(Detection, "/mission/detections", self.on_detection, 10)
        self.create_subscription(RoverStatus, "/mission/status", self.on_status, 10)
        latched = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL,
        )
        self.create_subscription(Bool, "/mission/finished", self.on_finished, latched)
        self.create_subscription(Bool, "/mission/return_home", self.on_return, latched)
        self.create_subscription(Bool, "/mission/paused", self.on_pause, latched)
        self.create_service(SetBool, prefix + "/set_enabled", self.on_enable)
        self.create_timer(0.1, self.tick)

    def now_seconds(self):
        return self.get_clock().now().nanoseconds / 1e9

    def on_odom(self, msg):
        self.pose = pose_tuple(msg.pose.pose)
        self.odom_received = self.now_seconds()

    def on_scan(self, msg):
        now = self.now_seconds()
        age = now - stamp_seconds(msg.header.stamp)
        if self.pose is None or not 0 <= age < 0.5 or now - self.odom_received >= 0.25:
            self.rover.navigator.scan_valid = False
            return
        points, valid = scan_points(
            msg.ranges,
            msg.angle_min,
            msg.angle_increment,
            msg.range_min,
            msg.range_max,
            self.pose,
            self.rover.config["lidar_offset"],
        )
        self.rover.navigator.update_scan(
            points, stamp_seconds(msg.header.stamp), valid, self.peers.values()
        )

    def on_pause(self, msg):
        self.rover.paused = msg.data
        if msg.data:
            self.velocity_pub.publish(Twist())

    def on_goal(self, msg):
        now = self.now_seconds()
        if self.mission_finished or now - stamp_seconds(msg.header.stamp) > msg.lease_seconds:
            return
        self.rover.assign(
            Goal(msg.task_id, msg.target_id, (msg.position.x, msg.position.y), msg.rover_id), now
        )

    def on_detection(self, msg):
        if (
            msg.header.frame_id != "world"
            or msg.confidence < 0.65
            or not 0 <= self.now_seconds() - stamp_seconds(msg.header.stamp) < 1.0
        ):
            return
        self.rover.remember(msg.target_id, (msg.position.x, msg.position.y))
        if msg.observer == self.rover_id:
            self.rover.seen(msg.target_id, stamp_seconds(msg.header.stamp))

    def on_return(self, msg):
        if msg.data:
            self.rover.return_home()

    def on_status(self, msg):
        if msg.rover_id != self.rover_id:
            self.peers[msg.rover_id] = Snapshot(
                msg.rover_id,
                pose_tuple(msg.pose),
                msg.battery,
                msg.mode,
                stamp_seconds(msg.header.stamp),
            )

    def on_enable(self, request, response):
        self.rover.enabled = request.data
        if not request.data:
            self.velocity_pub.publish(Twist())
        response.success = True
        response.message = "enabled" if request.data else "disabled; tasks will be released"
        return response

    def on_finished(self, msg):
        if msg.data:
            self.mission_finished = True
            self.velocity_pub.publish(Twist())

    def tick(self):
        now = self.now_seconds()
        dt = 0.0 if self.last_time is None else max(0.0, now - self.last_time)
        self.last_time = now
        command = Twist()
        if self.mission_finished:
            self.rover.navigator.state = "finished"
        elif self.pose is None or now - self.odom_received >= 0.5:
            self.rover.navigator.state = "waiting_for_odometry"
        if self.pose is not None and now - self.odom_received < 0.5 and not self.mission_finished:
            command.linear.x, command.angular.z = self.rover.step(
                self.pose, dt, now, self.peers.values()
            )
        self.velocity_pub.publish(command)
        if self.pose is None:
            return
        status = RoverStatus()
        status.header.stamp = self.get_clock().now().to_msg()
        status.header.frame_id = "world"
        status.rover_id = self.rover_id
        status.pose.position.x, status.pose.position.y = self.pose[:2]
        status.pose.orientation.z = math.sin(self.pose[2] / 2)
        status.pose.orientation.w = math.cos(self.pose[2] / 2)
        status.battery = self.rover.battery
        status.mode = (
            "finished"
            if self.mission_finished
            else ("unavailable" if now - self.odom_received >= 0.5 else self.rover.mode)
        )
        status.distance_travelled = self.rover.travelled
        status.energy_used = self.rover.energy_used
        self.status_pub.publish(status)
        self.nav_pub.publish(String(data=self.rover.navigator.state))
        if int(now * 10) % 5 == 0:
            nav = self.rover.navigator
            self.debug_pub.publish(
                String(
                    data=json.dumps(
                        dict(
                            time=now,
                            pose=self.pose,
                            state=nav.state,
                            mode=self.rover.mode,
                            task=self.rover.goal.task_id if self.rover.goal else None,
                            dwell=self.rover.dwell,
                            local_seen_age=(
                                now
                                - self.rover.observations.get(self.rover.goal.target_id, now - 999)
                            )
                            if self.rover.goal
                            else None,
                            requested=nav.requested,
                            command=[command.linear.x, command.angular.z],
                            blocker=nav.blocker,
                            path=nav.path,
                            markers=self.rover.known_targets,
                            scan_age=now - nav.scan_at if math.isfinite(nav.scan_at) else None,
                            scan_valid=nav.scan_valid,
                            memory_size=len(nav.memory),
                        )
                    )
                )
            )
        path = Path()
        path.header = status.header
        for x, y in [self.pose[:2], *self.rover.navigator.path]:
            point = PoseStamped()
            point.header = path.header
            point.pose.position.x, point.pose.position.y = float(x), float(y)
            point.pose.orientation.w = 1.0
            path.poses.append(point)
        self.plan_pub.publish(path)
        while self.rover.results:
            rover_id, task_id, success, detail = self.rover.results.pop(0)
            result = TaskResult()
            result.header = status.header
            result.rover_id, result.task_id = rover_id, task_id
            result.success, result.detail = success, detail
            self.result_pub.publish(result)


def main(args=None):
    rclpy.init(args=args)
    node = RoverAgent()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.velocity_pub.publish(Twist())
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

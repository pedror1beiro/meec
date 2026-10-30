from collections import deque
from copy import deepcopy

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Point, PoseStamped
from nav_msgs.msg import Path
from std_msgs.msg import String
from visualization_msgs.msg import Marker, MarkerArray
from rsdis_interfaces.msg import Detection, RoverStatus, TaskGoal, TaskResult

from .common import load_config


class MissionMonitor(Node):
    def __init__(self):
        super().__init__("mission_monitor")
        self.declare_parameter("config", "")
        config = load_config(self.get_parameter("config").value)
        self.marker_height = config.get("marker_height", 0.88)
        self.detailed = config.get("model_profile") == "space_ros_viper"
        self.ids = [r["id"] for r in config["rovers"]]
        self.config = config
        self.navigation = {}
        self.colours = {t["id"]: t["colour"] for t in config["targets"]}
        self.statuses = {}
        self.detections = {}
        self.tasks = {}
        self.confirmed = set()
        self.paths = {name: deque(maxlen=2000) for name in self.ids}
        self.path_pubs = {
            name: self.create_publisher(Path, "/" + name + "/path", 10) for name in self.ids
        }
        self.pub = self.create_publisher(MarkerArray, "/mission/markers", 10)
        self.create_subscription(RoverStatus, "/mission/status", self.on_status, 10)
        self.create_subscription(Detection, "/mission/detections", self.on_detection, 10)
        self.create_subscription(TaskGoal, "/mission/goals", self.on_goal, 10)
        self.create_subscription(TaskResult, "/mission/results", self.on_result, 10)
        for name in self.ids:
            self.create_subscription(String, f"/{name}/navigation_state", lambda msg, n=name: self.navigation.__setitem__(n, msg.data), 10)
        self.create_timer(0.5, self.tick)

    def on_status(self, msg):
        if msg.rover_id not in self.paths:
            return
        self.statuses[msg.rover_id] = msg
        path = self.paths[msg.rover_id]
        if (
            not path
            or abs(path[-1].pose.position.x - msg.pose.position.x)
            + abs(path[-1].pose.position.y - msg.pose.position.y)
            > 0.1
        ):
            p = PoseStamped()
            p.header, p.pose = msg.header, msg.pose
            path.append(p)

    def on_detection(self, msg):
        if msg.header.frame_id == "world" and msg.target_id in self.colours:
            self.detections[msg.target_id] = msg

    def on_goal(self, msg):
        self.tasks[msg.task_id] = msg.target_id

    def on_result(self, msg):
        if msg.success and msg.task_id in self.tasks:
            self.confirmed.add(self.tasks[msg.task_id])

    def marker(self, namespace, ident, kind):
        m = Marker()
        m.header.frame_id = "world"
        m.header.stamp = self.get_clock().now().to_msg()
        m.ns, m.id, m.type, m.action = namespace, ident, kind, Marker.ADD
        m.pose.orientation.w = 1.0
        m.color.a = 1.0
        return m

    def tick(self):
        markers = []
        palette = [(0.55, 0.72, 1.0), (1.0, 0.7, 0.35)]
        for i, name in enumerate(self.ids):
            if name not in self.statuses:
                continue
            status = self.statuses[name]
            body = self.marker("rover", i, Marker.CUBE)
            body.pose = deepcopy(status.pose)
            body.pose.position.z = 0.7 if self.detailed else 0.45
            body.scale.x, body.scale.y, body.scale.z = (
                (1.5, 1.5, 0.9) if self.detailed else (0.9, 0.58, 0.3)
            )
            body.color.r, body.color.g, body.color.b = palette[i % len(palette)]
            label = self.marker("rover_label", i, Marker.TEXT_VIEW_FACING)
            label.pose.position.x, label.pose.position.y = (
                status.pose.position.x,
                status.pose.position.y,
            )
            label.pose.position.z = self.marker_height + 0.52
            label.scale.z = 0.28
            label.color.r = label.color.g = label.color.b = 1.0
            label.text = f"{name}: {status.mode} | {self.navigation.get(name, '')} | {status.battery:.0%}"
            markers.extend((body, label))
            path = Path()
            path.header = label.header
            path.poses = list(self.paths[name])
            self.path_pubs[name].publish(path)
        for i, name in enumerate(sorted(self.detections)):
            detection = self.detections[name]
            marker = self.marker("target", i, Marker.SPHERE)
            marker.pose.position = deepcopy(detection.position)
            marker.pose.position.z = self.marker_height
            marker.scale.x = marker.scale.y = marker.scale.z = 0.5
            marker.color.r, marker.color.g, marker.color.b = self.colours[name][:3]
            label = self.marker("target_label", i, Marker.TEXT_VIEW_FACING)
            label.pose.position.x, label.pose.position.y = (
                detection.position.x,
                detection.position.y,
            )
            label.pose.position.z = self.marker_height + 0.52
            label.scale.z = 0.22
            label.color.r = label.color.g = label.color.b = 1.0
            label.text = name + (" [confirmed]" if name in self.confirmed else " [detected]")
            markers.extend((marker, label))
        for i, hazard in enumerate(self.config.get("hazards", [])):
            area = self.marker("mapped_hazards", i, Marker.CYLINDER)
            area.pose.position.x, area.pose.position.y = map(float, hazard["position"])
            area.pose.position.z = 0.03
            area.scale.x = area.scale.y = 2 * hazard["radius"]
            area.scale.z = 0.06
            area.color.r, area.color.g, area.color.b, area.color.a = 0.6, 0.56, 0.48, 0.45
            markers.append(area)
        xmin, xmax, ymin, ymax = self.config["map_bounds"]
        boundary = self.marker("map_bounds", 0, Marker.LINE_STRIP)
        boundary.scale.x = 0.08
        boundary.color.r = boundary.color.g = boundary.color.b = 0.6
        boundary.points = [Point(x=float(x), y=float(y), z=0.05) for x, y in [(xmin, ymin), (xmax, ymin), (xmax, ymax), (xmin, ymax), (xmin, ymin)]]
        markers.append(boundary)
        self.pub.publish(MarkerArray(markers=markers))


def main(args=None):
    rclpy.init(args=args)
    node = MissionMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

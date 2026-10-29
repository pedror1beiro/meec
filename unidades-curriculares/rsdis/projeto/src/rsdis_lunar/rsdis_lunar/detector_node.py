from collections import deque

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from cv_bridge import CvBridge
from nav_msgs.msg import Odometry
from sensor_msgs.msg import CameraInfo, Image
from rsdis_interfaces.msg import Detection

from .common import pose_tuple, stamp_seconds
from .vision import detect, to_world


class TargetDetector(Node):
    def __init__(self):
        super().__init__("target_detector")
        self.declare_parameter("rover_id", "")
        self.declare_parameter("marker_diameter", 0.5)
        self.declare_parameter("camera_offset", 0.46)
        self.rover_id = self.get_parameter("rover_id").value
        self.bridge = CvBridge()
        self.poses = deque(maxlen=100)
        self.intrinsics = None
        prefix = "/" + self.rover_id
        self.pub = self.create_publisher(Detection, "/mission/detections", 10)
        self.create_subscription(Odometry, prefix + "/odom", self.on_odom, qos_profile_sensor_data)
        self.create_subscription(
            CameraInfo, prefix + "/camera/info", self.on_info, qos_profile_sensor_data
        )
        self.create_subscription(
            Image, prefix + "/camera/image", self.on_image, qos_profile_sensor_data
        )

    def on_odom(self, msg):
        self.poses.append((stamp_seconds(msg.header.stamp), pose_tuple(msg.pose.pose)))

    def on_info(self, msg):
        self.intrinsics = tuple(msg.k)

    def on_image(self, msg):
        if not self.poses or self.intrinsics is None:
            return
        image_time = stamp_seconds(msg.header.stamp)
        pose_time, pose = min(self.poses, key=lambda p: abs(p[0] - image_time))
        if abs(pose_time - image_time) > 0.2:
            return
        image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        detections = detect(image, self.intrinsics, self.get_parameter("marker_diameter").value)
        for target_id, forward, left, score in detections:
            x, y = to_world(forward, left, pose, self.get_parameter("camera_offset").value)
            result = Detection()
            result.header.stamp = msg.header.stamp
            result.header.frame_id = "world"
            result.target_id, result.observer = target_id, self.rover_id
            result.position.x, result.position.y = x, y
            result.confidence = float(score)
            self.pub.publish(result)


def main(args=None):
    rclpy.init(args=args)
    node = TargetDetector()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

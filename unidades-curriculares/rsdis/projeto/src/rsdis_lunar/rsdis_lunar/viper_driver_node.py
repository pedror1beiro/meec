"""Namespaced steering adapter with command/joint-state freshness interlocks."""

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from geometry_msgs.msg import Twist
from sensor_msgs.msg import JointState
from std_msgs.msg import Float64

from .viper import WHEELS, gated_commands
from .common import stamp_seconds


class ViperDriver(Node):
    def __init__(self):
        super().__init__("viper_driver")
        self.declare_parameter("rover_id", "")
        name = self.get_parameter("rover_id").value
        self.last_command = -math.inf
        self.last_feedback = -math.inf
        self.command = (0.0, 0.0)
        self.steering = {}
        self.velocity_pubs = [
            self.create_publisher(Float64, f"/{name}/joints/{w}/velocity", 10) for w in WHEELS
        ]
        self.steering_pubs = [
            self.create_publisher(Float64, f"/{name}/joints/{w}/steering", 10) for w in WHEELS
        ]
        self.create_subscription(Twist, f"/{name}/cmd_vel", self.on_command, 10)
        self.create_subscription(
            JointState, f"/{name}/joint_states", self.on_feedback, qos_profile_sensor_data
        )
        self.create_timer(0.05, self.tick)

    def now_seconds(self):
        return self.get_clock().now().nanoseconds / 1e9

    def on_command(self, msg):
        self.command = (msg.linear.x, msg.angular.z)
        self.last_command = self.now_seconds()

    def on_feedback(self, msg):
        self.steering = {
            name.split("::")[-1]: position for name, position in zip(msg.name, msg.position)
        }
        self.last_feedback = stamp_seconds(msg.header.stamp)

    def tick(self):
        now = self.now_seconds()
        commands = gated_commands(
            *self.command, self.steering, now - self.last_command, now - self.last_feedback
        )
        for i, (angle, speed) in enumerate(commands):
            self.steering_pubs[i].publish(Float64(data=float(angle)))
            self.velocity_pubs[i].publish(Float64(data=float(speed)))


def main(args=None):
    rclpy.init(args=args)
    node = ViperDriver()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            for publisher in node.velocity_pubs:
                publisher.publish(Float64(data=0.0))
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

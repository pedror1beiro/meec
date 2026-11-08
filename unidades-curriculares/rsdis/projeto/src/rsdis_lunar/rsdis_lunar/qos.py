"""Explicit ROS 2 DDS contracts; see the official Jazzy QoS documentation."""

from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy


def mission_qos():
    return QoSProfile(
        depth=100, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.VOLATILE
    )


def state_qos():
    return QoSProfile(
        depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL
    )

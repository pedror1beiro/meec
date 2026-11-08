"""Drive Space ROS energy plugins using measured motion and charging-pad contact."""

import csv
import math
from pathlib import Path

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from nav_msgs.msg import Odometry
from sensor_msgs.msg import BatteryState
from std_msgs.msg import Float32
from std_srvs.srv import SetBool
from rsdis_interfaces.msg import RoverStatus

from .common import load_config, pose_tuple, stamp_seconds
from .power import dock_power, motion_load, power_config


class PowerGovernor(Node):
    def __init__(self):
        super().__init__("power_governor")
        for key, default in (("config", ""), ("rover_id", ""), ("output", "")):
            self.declare_parameter(key, default)
        config = load_config(self.get_parameter("config").value)
        self.name = self.get_parameter("rover_id").value
        spec = next(r for r in config["rovers"] if r["id"] == self.name)
        self.power = power_config(config)
        self.home = spec["spawn"][:2]
        self.pose, self.pose_at = tuple(spec["spawn"]), -math.inf
        self.speed = self.yaw_rate = 0.0
        self.mode, self.dock_enabled, self.manual_dock = "idle", True, False
        self.battery, self.solar, self.supply = None, 0.0, 0.0
        prefix = "/" + self.name
        self.load_pub = self.create_publisher(Float32, prefix + "/energy/load_w", 10)
        self.dock_pub = self.create_publisher(Float32, prefix + "/energy/dock_w", 10)
        self.create_subscription(Odometry, prefix + "/odom", self.on_odom, qos_profile_sensor_data)
        self.create_subscription(
            BatteryState, prefix + "/battery", self.on_battery, qos_profile_sensor_data
        )
        self.create_subscription(
            Float32,
            prefix + "/energy/solar_w",
            lambda m: setattr(self, "solar", m.data),
            qos_profile_sensor_data,
        )
        self.create_subscription(
            Float32,
            prefix + "/energy/supply_w",
            lambda m: setattr(self, "supply", m.data),
            qos_profile_sensor_data,
        )
        self.create_subscription(
            RoverStatus, prefix + "/local/status", self.on_status, qos_profile_sensor_data
        )
        self.create_service(SetBool, prefix + "/set_dock_enabled", self.on_dock)
        self.file = None
        output = self.get_parameter("output").value
        if output:
            Path(output).mkdir(parents=True, exist_ok=True)
            self.file = (Path(output) / (self.name + "_power.csv")).open(
                "w", newline="", encoding="utf-8"
            )
            self.writer = csv.writer(self.file)
            self.writer.writerow(
                [
                    "time",
                    "soc",
                    "voltage_v",
                    "current_a",
                    "charge_ah",
                    "load_w",
                    "solar_w",
                    "dock_w",
                    "supply_w",
                    "mode",
                ]
            )
        self.last_record = -math.inf
        self.create_timer(0.1, self.tick)

    def on_odom(self, msg):
        now = stamp_seconds(msg.header.stamp)
        pose = pose_tuple(msg.pose.pose)
        dt = now - self.pose_at
        if 0 < dt < 0.5:
            self.speed = math.dist(pose[:2], self.pose[:2]) / dt
            self.yaw_rate = (
                math.atan2(math.sin(pose[2] - self.pose[2]), math.cos(pose[2] - self.pose[2])) / dt
            )
        self.pose, self.pose_at = pose, now

    def on_battery(self, msg):
        self.battery = msg

    def on_status(self, msg):
        if msg.rover_id == self.name:
            self.mode = msg.mode

    def on_dock(self, request, response):
        self.dock_enabled = request.data
        self.manual_dock = request.data
        response.success, response.message = (
            True,
            "Dock enabled" if request.data else "Dock disabled",
        )
        return response

    def tick(self):
        now = self.get_clock().now().nanoseconds / 1e9
        fresh = 0 <= now - self.pose_at < 0.5
        load = motion_load(self.power, self.speed if fresh else 0, self.yaw_rate if fresh else 0)
        dock = dock_power(
            self.power,
            self.pose,
            self.home,
            self.speed,
            self.yaw_rate,
            "charging" if self.manual_dock else self.mode,
            self.dock_enabled and fresh,
        )
        self.load_pub.publish(Float32(data=float(load)))
        self.dock_pub.publish(Float32(data=float(dock)))
        if self.file and self.battery and now - self.last_record >= 0.5:
            self.last_record = now
            b = self.battery
            self.writer.writerow(
                [
                    round(now, 3),
                    b.percentage,
                    b.voltage,
                    b.current,
                    b.charge,
                    load,
                    self.solar,
                    dock,
                    self.supply,
                    self.mode,
                ]
            )
            self.file.flush()

    def close(self):
        self.dock_pub.publish(Float32(data=0.0))
        if self.file:
            self.file.close()


def main(args=None):
    rclpy.init(args=args)
    node = PowerGovernor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        if rclpy.ok():
            node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

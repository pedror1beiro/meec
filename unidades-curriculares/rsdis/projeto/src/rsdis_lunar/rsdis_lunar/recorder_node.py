"""Record genuine Gazebo camera images with ROS telemetry overlays."""

import json
from pathlib import Path

import cv2
from cv_bridge import CvBridge
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import String
from rsdis_interfaces.msg import MissionState, RoverStatus

from .common import load_config, stamp_seconds
from .qos import state_qos
from .recording import project_overhead


class MissionRecorder(Node):
    def __init__(self):
        super().__init__("mission_recorder")
        self.declare_parameter("config", "")
        self.declare_parameter("output", "")
        self.config = load_config(self.get_parameter("config").value)
        self.output = Path(self.get_parameter("output").value)
        self.output.mkdir(parents=True, exist_ok=True)
        self.bridge = CvBridge()
        self.rovers, self.cameras, self.confirmed = {}, {}, set()
        self.link, self.frames, self.start, self.end = {}, 0, None, None
        self.writer = cv2.VideoWriter(
            str(self.output / "mission_raw.avi"), cv2.VideoWriter_fourcc(*"MJPG"), 10, (1280, 800)
        )
        if not self.writer.isOpened():
            raise RuntimeError("Unable to create mission recording")
        self.create_subscription(
            Image, "/mission/overview/image", self.on_frame, qos_profile_sensor_data
        )
        self.create_subscription(
            MissionState,
            "/mission/state",
            lambda m: setattr(self, "confirmed", {t.target_id for t in m.targets if t.confirmed}),
            state_qos(),
        )
        self.create_subscription(
            String,
            "/mission/network",
            lambda m: setattr(self, "link", json.loads(m.data).get("online", {})),
            10,
        )
        for spec in self.config["rovers"]:
            name = spec["id"]
            self.create_subscription(
                RoverStatus,
                f"/{name}/local/status",
                lambda m: self.rovers.__setitem__(m.rover_id, m),
                qos_profile_sensor_data,
            )
            self.create_subscription(
                Image,
                f"/{name}/camera/image",
                lambda m, n=name: self.cameras.__setitem__(n, self.bridge.imgmsg_to_cv2(m, "bgr8")),
                qos_profile_sensor_data,
            )

    def on_frame(self, msg):
        now = stamp_seconds(msg.header.stamp)
        if self.start is None:
            self.start = now
        self.end = now
        image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        canvas = np.full((800, 1280, 3), (25, 22, 18), dtype=np.uint8)
        canvas[64:784, :960] = cv2.resize(image, (960, 720))

        def text(label, xy, size=0.55, colour=(235, 235, 235)):
            cv2.putText(canvas, label, xy, cv2.FONT_HERSHEY_SIMPLEX, size, colour, 1, cv2.LINE_AA)

        text("RSDIS | Cooperative lunar exploration", (20, 26), 0.68)
        text(
            f"Gazebo rendered cameras | t={now:.1f} s | {len(self.confirmed)}/{len(self.config['targets'])} confirmed | 5x simulation speed",
            (20, 50),
            0.48,
        )
        for i, spec in enumerate(self.config["rovers"]):
            name = spec["id"]
            colour = (255, 200, 155) if i == 0 else (110, 190, 245)
            y = 82 + i * 340
            text(name, (980, y), 0.7, colour)
            if name in self.cameras:
                canvas[y + 16 : y + 226, 976:1256] = cv2.resize(self.cameras[name], (280, 210))
            status = self.rovers.get(name)
            if status:
                text(f"Battery {status.battery:.0%}", (980, y + 251), 0.55)
                text(status.mode, (980, y + 278), 0.5)
                x, v = project_overhead(
                    (status.pose.position.x, status.pose.position.y), self.config
                )
                if 0 < x < 930 and 0 < v < 700:
                    text(name, (x + 6, v + 60), 0.48, colour)
            text(
                "Mission link: " + ("connected" if self.link.get(name, True) else "disconnected"),
                (980, y + 305),
                0.45,
            )
        text(
            "Recorded physical simulation; telemetry uses Gazebo world localisation.",
            (20, 797),
            0.4,
        )
        self.writer.write(canvas)
        self.frames += 1
        if self.frames in (1, 40, 100, 200):
            cv2.imwrite(str(self.output / f"overview_{self.frames:04}.jpg"), canvas)

    def close(self):
        self.writer.release()
        metadata = dict(
            source="actual Gazebo overview and rover RGB cameras with ROS telemetry overlays",
            frames=self.frames,
            capture_hz=2,
            playback_fps=10,
            speedup=5,
            first_sim_time=self.start,
            last_sim_time=self.end,
        )
        (self.output / "video_metadata.json").write_text(json.dumps(metadata, indent=2))


def main(args=None):
    rclpy.init(args=args)
    node = MissionRecorder()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

"""Loopback mission console. HTTP requests are queued onto the ROS executor."""

from collections import deque
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from queue import Empty, Queue
import threading
import time

from ament_index_python.packages import get_package_share_directory
from cv_bridge import CvBridge
import cv2
import rclpy
from rclpy.node import Node
from rclpy.qos import DurabilityPolicy, QoSProfile, ReliabilityPolicy, qos_profile_sensor_data
from nav_msgs.msg import Path as NavPath
from sensor_msgs.msg import Image
from std_msgs.msg import Bool, String
from std_srvs.srv import SetBool, Trigger
from rsdis_interfaces.msg import Detection, RoverStatus, TaskGoal, TaskResult

from .common import load_config, pose_tuple, stamp_seconds


class MissionDashboard(Node):
    def __init__(self):
        super().__init__("mission_dashboard")
        self.declare_parameter("config", "")
        self.declare_parameter("port", 8765)
        config = load_config(self.get_parameter("config").value)
        port = self.get_parameter("port").value
        self.config = config
        self.commands = Queue(maxsize=32)
        self.lock = threading.Lock()
        self.payload, self.images = b"{}", {}
        self.rovers, self.targets, self.plans = {}, {}, {}
        self.tasks, self.owners = {}, {}
        self.navigation = {}
        self.events = deque(maxlen=30)
        self.paused = self.finished = False
        self.last_command = "Ready"
        self.cv = CvBridge()
        self.camera_at = {}
        self.pending = []
        self.clients = {
            "pause": self.create_client(SetBool, "/mission/set_paused"),
            "recall": self.create_client(Trigger, "/mission/recall"),
        }
        self.create_subscription(RoverStatus, "/mission/status", self.on_status, 10)
        self.create_subscription(Detection, "/mission/detections", self.on_detection, 10)
        self.create_subscription(TaskGoal, "/mission/goals", self.on_goal, 10)
        self.create_subscription(TaskResult, "/mission/results", self.on_result, 10)
        latched = QoSProfile(depth=1, reliability=ReliabilityPolicy.RELIABLE, durability=DurabilityPolicy.TRANSIENT_LOCAL)
        self.create_subscription(Bool, "/mission/paused", lambda m: setattr(self, "paused", m.data), latched)
        self.create_subscription(Bool, "/mission/finished", lambda m: setattr(self, "finished", m.data), latched)
        self.trails = {r["id"]: deque(maxlen=2500) for r in config["rovers"]}
        for spec in config["rovers"]:
            name = spec["id"]
            self.clients[name] = self.create_client(SetBool, f"/{name}/set_enabled")
            self.create_subscription(String, f"/{name}/navigation_state", lambda m, n=name: self.navigation.__setitem__(n, m.data), 10)
            self.create_subscription(NavPath, f"/{name}/plan", lambda m, n=name: self.plans.__setitem__(n, [[p.pose.position.x, p.pose.position.y] for p in m.poses]), 10)
            self.create_subscription(Image, f"/{name}/camera/image", lambda m, n=name: self.on_image(n, m), qos_profile_sensor_data)
        page = (Path(get_package_share_directory("rsdis_lunar")) / "web/mission.html").read_bytes()
        dashboard = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def respond(self, code, content, mime="application/json"):
                self.send_response(code)
                self.send_header("Content-Type", mime)
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)

            def do_GET(self):
                path = self.path.split("?")[0]
                if path == "/":
                    self.respond(200, page, "text/html; charset=utf-8")
                elif path == "/api/state":
                    with dashboard.lock:
                        payload = dashboard.payload
                    self.respond(200, payload)
                elif path.startswith("/camera/"):
                    name = path.removeprefix("/camera/").removesuffix(".jpg")
                    with dashboard.lock:
                        image = dashboard.images.get(name)
                    self.respond(200 if image else 404, image or b"", "image/jpeg")
                else:
                    self.respond(404, b'{}')

            def do_POST(self):
                # A local webpage from another site must not control a running mission.
                origin = self.headers.get("Origin")
                if origin and origin not in (f"http://localhost:{port}", f"http://127.0.0.1:{port}"):
                    self.respond(403, b'{"error":"Origin rejected"}')
                    return
                try:
                    size = int(self.headers.get("Content-Length", "0"))
                    if self.path != "/api/command" or not 0 < size < 1024:
                        raise ValueError("Invalid request")
                    body = json.loads(self.rfile.read(size))
                    action = body["action"]
                    if action not in ("pause", "resume", "recall", "disable", "enable"):
                        raise ValueError("Unknown action")
                    if action in ("disable", "enable") and body.get("rover") not in dashboard.trails:
                        raise ValueError("Unknown rover")
                    dashboard.commands.put_nowait(body)
                    self.respond(202, b'{"queued":true}')
                except (ValueError, KeyError, TypeError):
                    self.respond(400, b'{"error":"Invalid command"}')
                except Exception:
                    self.respond(503, b'{"error":"Console busy"}')

        self.server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        self.server.daemon_threads = True
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.create_timer(0.25, self.tick)
        self.get_logger().info(f"Mission console: http://localhost:{port}")

    def event(self, text):
        self.events.appendleft(dict(time=round(self.get_clock().now().nanoseconds / 1e9, 1), text=text))

    def on_status(self, msg):
        if msg.rover_id not in self.trails:
            return
        pose = pose_tuple(msg.pose)
        self.rovers[msg.rover_id] = dict(id=msg.rover_id, pose=pose, battery=msg.battery, mode=msg.mode, stamp=stamp_seconds(msg.header.stamp))
        trail = self.trails[msg.rover_id]
        if not trail or abs(trail[-1][0] - pose[0]) + abs(trail[-1][1] - pose[1]) > 0.25:
            trail.append(pose[:2])

    def on_detection(self, msg):
        if msg.header.frame_id != "world" or msg.target_id not in {t["id"] for t in self.config["targets"]}:
            return
        if msg.target_id not in self.targets:
            self.event(f"{msg.observer} discovered {msg.target_id}")
        target = self.targets.setdefault(msg.target_id, dict(confirmed=False))
        target.update(position=[msg.position.x, msg.position.y], observer=msg.observer)

    def on_goal(self, msg):
        if msg.task_id not in self.tasks:
            self.event(f"{msg.rover_id} assigned to {msg.target_id}")
        self.tasks[msg.task_id] = msg.target_id
        self.owners[msg.target_id] = msg.rover_id

    def on_result(self, msg):
        target = self.tasks.get(msg.task_id)
        if target:
            self.owners.pop(target, None)
            if msg.success and target in self.targets:
                self.targets[target]["confirmed"] = True
            self.event(f"{msg.rover_id}: {target} / {msg.detail}")

    def on_image(self, name, msg):
        if time.monotonic() - self.camera_at.get(name, 0) < 0.8:
            return
        self.camera_at[name] = time.monotonic()
        try:
            ok, image = cv2.imencode(".jpg", self.cv.imgmsg_to_cv2(msg, desired_encoding="bgr8"), [cv2.IMWRITE_JPEG_QUALITY, 70])
            if ok:
                with self.lock:
                    self.images[name] = image.tobytes()
        except (ValueError, cv2.error) as error:
            self.get_logger().warning(str(error))

    def tick(self):
        try:
            body = self.commands.get_nowait()
        except Empty:
            body = None
        if body:
            action = body["action"]
            key = "pause" if action in ("pause", "resume") else ("recall" if action == "recall" else body.get("rover"))
            client = self.clients.get(key)
            if client and client.service_is_ready() and not self.finished:
                request = Trigger.Request() if action == "recall" else SetBool.Request(data=action in ("pause", "enable"))
                self.pending.append((action, client.call_async(request), time.monotonic()))
                self.last_command = action + ": waiting for rover response"
            else:
                self.last_command = "Mission finished or service unavailable"
        remaining = []
        for action, future, started in self.pending:
            if future.done():
                try:
                    result = future.result()
                    self.last_command = result.message
                    self.event(action + ": " + result.message)
                except Exception as error:
                    self.last_command = str(error)
            elif time.monotonic() - started < 5:
                remaining.append((action, future, started))
            else:
                self.last_command = action + ": response timed out"
        self.pending = remaining
        payload = dict(
            map_name=self.config.get("map_name", "Lunar survey"), bounds=self.config["map_bounds"],
            hazards=self.config["hazards"], sectors=self.config.get("sectors", []),
            bases=[dict(id=r["id"], position=r["spawn"][:2]) for r in self.config["rovers"]],
            colours={t["id"]: t["colour"] for t in self.config["targets"]}, expected=len(self.config["targets"]),
            time=round(self.get_clock().now().nanoseconds / 1e9, 1),
            rovers=list(self.rovers.values()), targets=self.targets, owners=self.owners,
            plans=self.plans, trails={k: list(v) for k, v in self.trails.items()}, navigation=self.navigation,
            paused=self.paused, finished=self.finished, events=list(self.events), last_command=self.last_command,
        )
        with self.lock:
            self.payload = json.dumps(payload).encode()

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)


def main(args=None):
    rclpy.init(args=args)
    node = MissionDashboard()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.close()
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

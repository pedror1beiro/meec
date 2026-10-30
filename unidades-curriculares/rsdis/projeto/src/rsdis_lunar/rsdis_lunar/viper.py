"""Optional Space ROS rover adapter for the flat integration field.

Reuse the upstream chassis, meshes, inertias and steering geometry. Replace its
single-rover ROS control/sensor plugins with namespaced Gazebo joint controllers.
Power remains the mission's synthetic model; no solar fidelity is implied.
"""

from copy import deepcopy
import math
from pathlib import Path
import tempfile
from xml.etree import ElementTree as ET

from .world import element, lidar, plugin

WHEELS = ("front_left", "rear_left", "front_right", "rear_right")
HALF_LENGTH, HALF_TRACK, WHEEL_RADIUS = 0.435, 0.525, 0.225
STEER_LIMIT = 0.9


def profile(config):
    result = deepcopy(config)
    result.update(
        model_profile="space_ros_viper",
        camera_offset=0.85,
        marker_height=1.7305,
        inspection_standoff=2.7,
        rover_radius=1.35,
        lidar_offset=1.0,
        lidar_height=1.4605,
    )
    return result


def wheel_commands(linear, angular):
    """Four-wheel steering for forward/reverse motion and rotation in place.

    Reduce mixed-motion yaw rate to respect the physical steering limits, rather
    than clamping individual steering angles into an inconsistent wheel geometry.
    Returns ordered (steering radians, wheel radians/second) pairs.
    """
    if not math.isfinite(linear) or not math.isfinite(angular):
        return [(0.0, 0.0)] * 4
    linear, angular = max(-0.45, min(0.45, linear)), max(-0.7, min(0.7, angular))
    if abs(linear) > 1e-4:
        bound = abs(linear) / (HALF_TRACK + HALF_LENGTH / math.tan(STEER_LIMIT))
        angular = max(-bound, min(bound, angular))
    else:
        linear = 0.0
    result = []
    for x, y in (
        (HALF_LENGTH, HALF_TRACK),
        (-HALF_LENGTH, HALF_TRACK),
        (HALF_LENGTH, -HALF_TRACK),
        (-HALF_LENGTH, -HALF_TRACK),
    ):
        vx, vy = linear - angular * y, angular * x
        angle, speed = math.atan2(vy, vx), math.hypot(vx, vy)
        if angle > math.pi / 2:
            angle, speed = angle - math.pi, -speed
        elif angle < -math.pi / 2:
            angle, speed = angle + math.pi, -speed
        result.append((angle, speed / WHEEL_RADIUS))
    return result


def gated_commands(linear, angular, steering, command_age, feedback_age):
    commands = wheel_commands(linear, angular) if command_age < 0.5 else [(0.0, 0.0)] * 4
    aligned = feedback_age < 0.5 and all(
        abs(steering.get(w + "_wheel_axle_joint", math.inf) - commands[i][0]) < 0.08
        for i, w in enumerate(WHEELS)
    )
    return [(angle, speed if aligned else 0.0) for angle, speed in commands]


def expand_upstream(simulation_path):
    """Expand the original Xacro without requiring an installed simulation package.

    Only temporary text copies are changed; the pinned upstream checkout stays intact.
    This also permits a structural check on Windows with the PyPI xacro package.
    """
    import xacro

    simulation_path = Path(simulation_path).resolve()
    source = simulation_path / "models/lunar_pole_exploration_rover/urdf"
    if not source.is_dir():
        raise FileNotFoundError("Fetch Space ROS sources first: python3 scripts/fetch_upstream.py")
    with tempfile.TemporaryDirectory(prefix="rsdis_xacro_") as temporary:
        directory = Path(temporary)
        for file in source.iterdir():
            if file.suffix not in (".xacro", ".gazebo"):
                continue
            text = file.read_text(encoding="utf-8")
            text = text.replace(
                "$(find simulation)/models/lunar_pole_exploration_rover/urdf/",
                directory.as_posix() + "/",
            )
            text = text.replace("$(find simulation)", simulation_path.as_posix())
            (directory / file.name).write_text(text, encoding="utf-8")
        return xacro.process_file(str(directory / "lunar_pole_exploration_rover.xacro")).toxml()


def adapt_urdf(expanded, simulation_path, rover_id, config, require_assets=True):
    if not rover_id.isidentifier():
        raise ValueError("Rover ID must be an identifier")
    simulation_path = Path(simulation_path).resolve()
    robot = ET.fromstring(expanded)
    robot.set("name", rover_id)
    expected = {w + "_wheel_joint" for w in WHEELS} | {w + "_wheel_axle_joint" for w in WHEELS}
    actual = {j.attrib["name"] for j in robot.findall("joint")}
    if not expected <= actual:
        raise ValueError("Upstream model is missing the expected wheel and steering joints")
    for child in list(robot):
        if child.tag in ("gazebo", "ros2_control", "transmission"):
            robot.remove(child)
    # Hold the camera mast and solar panels at their original zero-angle pose.
    for joint in robot.findall("joint"):
        name = joint.attrib["name"]
        if name.startswith("mast_") or name in (
            "left_solar_panel_joint",
            "right_solar_panel_joint",
            "rear_solar_panel_joint",
        ):
            joint.set("type", "fixed")
            for child in list(joint):
                if child.tag in ("axis", "limit", "dynamics"):
                    joint.remove(child)
    for mesh in robot.findall(".//mesh"):
        original = mesh.attrib["filename"]
        if original.startswith("package://simulation/"):
            file = simulation_path / original.removeprefix("package://simulation/")
            if require_assets:
                if not file.is_file():
                    raise FileNotFoundError(f"Missing upstream mesh: {file}")
                with file.open("rb") as handle:
                    if handle.read(80).startswith(b"version https://git-lfs.github.com/spec"):
                        raise RuntimeError(
                            "Unresolved Git LFS mesh. Run: python3 scripts/fetch_upstream.py --assets"
                        )
            mesh.set("filename", file.as_uri())
    systems = element(robot, "gazebo")
    for wheel in WHEELS:
        velocity = plugin(systems, "joint-controller", "JointController")
        element(velocity, "joint_name", wheel + "_wheel_joint")
        element(velocity, "topic", f"/{rover_id}/joints/{wheel}/velocity")
        steering = plugin(systems, "joint-position-controller", "JointPositionController")
        element(steering, "joint_name", wheel + "_wheel_axle_joint")
        element(steering, "topic", f"/{rover_id}/joints/{wheel}/steering")
        element(steering, "use_velocity_commands", "true")
        element(steering, "cmd_max", 1.5)
        element(steering, "cmd_min", -1.5)
    state = plugin(systems, "joint-state-publisher", "JointStatePublisher")
    element(state, "topic", f"/{rover_id}/joint_states")
    for joint_name in sorted(expected):
        element(state, "joint_name", joint_name)
    odom = plugin(systems, "odometry-publisher", "OdometryPublisher")
    for name, value in {
        "odom_topic": f"/{rover_id}/odom",
        "odom_frame": "world",
        "robot_base_frame": f"{rover_id}/base_link",
        "dimensions": 2,
        "odom_publish_frequency": 20,
    }.items():
        element(odom, name, value)
    sensing = element(robot, "gazebo", reference="chassis")
    lidar(sensing, rover_id, config)
    camera = element(sensing, "sensor", name="mission_camera", type="camera")
    element(camera, "pose", f"{config['camera_offset']} 0 1.4605 0 0 0")
    element(camera, "topic", f"/{rover_id}/camera/image")
    element(camera, "always_on", "true")
    element(camera, "update_rate", 5)
    camera_spec = element(camera, "camera")
    element(camera_spec, "camera_info_topic", f"/{rover_id}/camera/info")
    element(camera_spec, "horizontal_fov", config["camera_hfov"])
    image = element(camera_spec, "image")
    element(image, "width", 640)
    element(image, "height", 480)
    element(image, "format", "R8G8B8")
    clip = element(camera_spec, "clip")
    element(clip, "near", 0.05)
    element(clip, "far", 30)
    ET.indent(robot)
    return ET.tostring(robot, encoding="unicode")


def command_bridges(rover_id):
    return [
        f"/{rover_id}/joints/{wheel}/{command}@std_msgs/msg/Float64]gz.msgs.Double"
        for wheel in WHEELS
        for command in ("velocity", "steering")
    ] + [f"/{rover_id}/joint_states@sensor_msgs/msg/JointState[gz.msgs.Model"]

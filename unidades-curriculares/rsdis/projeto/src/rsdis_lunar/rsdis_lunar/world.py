"""Generate an asset-free lunar outpost with the same hazards used by planning."""

import math
from xml.etree import ElementTree as ET


def element(parent, tag, text=None, **attrs):
    node = ET.SubElement(parent, tag, attrs)
    if text is not None:
        node.text = str(text)
    return node


def material(parent, colour, emissive=False):
    node = element(parent, "material")
    for name in ("ambient", "diffuse"):
        element(node, name, colour)
    if emissive:
        element(node, "emissive", colour)


def geometry(parent, shape, size):
    geom = element(parent, "geometry")
    obj = element(geom, shape)
    if shape == "box":
        element(obj, "size", size)
    elif shape == "sphere":
        element(obj, "radius", size)
    elif shape == "cylinder":
        element(obj, "radius", size[0])
        element(obj, "length", size[1])
    return obj


def solid(link, name, pose, shape, size, colour, collision=True, emissive=False):
    visual = element(link, "visual", name=name)
    element(visual, "pose", pose)
    geometry(visual, shape, size)
    material(visual, colour, emissive)
    if collision:
        col = element(link, "collision", name=name)
        element(col, "pose", pose)
        geometry(col, shape, size)
    return visual


def plugin(parent, file, name):
    return element(
        parent, "plugin", filename=f"gz-sim-{file}-system", name=f"gz::sim::systems::{name}"
    )


def lidar(link, name, config):
    sensor = element(link, "sensor", name="safety_lidar", type="gpu_lidar")
    element(sensor, "pose", f"{config.get('lidar_offset', 0.62)} 0 {config.get('lidar_height', 0.65)} 0 0 0")
    element(sensor, "topic", f"/{name}/scan")
    element(sensor, "gz_frame_id", f"{name}/safety_lidar")
    element(sensor, "update_rate", 10)
    element(sensor, "always_on", "true")
    element(sensor, "visualize", "false")
    rays = element(sensor, "lidar")
    horizontal = element(element(rays, "scan"), "horizontal")
    for key, value in {"samples": 721, "resolution": 1, "min_angle": -math.pi / 2, "max_angle": math.pi / 2}.items():
        element(horizontal, key, value)
    distance = element(rays, "range")
    for key, value in {"min": 0.06, "max": config.get("lidar_range", 12.0), "resolution": 0.01}.items():
        element(distance, key, value)


def rover(world, spec, config):
    name = spec["id"]
    x, y, yaw = spec["spawn"]
    model = element(world, "model", name=name)
    element(model, "pose", f"{x} {y} 0.23 0 0 {yaw}")
    base = element(model, "link", name="base_link")
    inertial = element(base, "inertial")
    element(inertial, "mass", 20.0)
    inertia = element(inertial, "inertia")
    for axis, value in (("ixx", 0.7), ("iyy", 1.0), ("izz", 1.4)):
        element(inertia, axis, value)
    solid(base, "body", "0 0 0.22 0 0 0", "box", "0.9 0.58 0.3", "0.6 0.6 0.57 1")
    solid(
        base,
        "solar_panel",
        "-0.15 0 0.42 0 0 0",
        "box",
        "0.65 0.82 0.025",
        "0.035 0.04 0.07 1",
        False,
    )
    solid(base, "mast", "0.3 0 0.48 0 0 0", "cylinder", (0.025, 0.5), "0.7 0.7 0.7 1", False)
    solid(
        base,
        "camera_housing",
        "0.4 0 0.65 0 0 0",
        "box",
        "0.1 0.14 0.08",
        "0.15 0.15 0.15 1",
        False,
    )
    # Camera looks along +X in Gazebo's camera sensor convention.
    camera = element(base, "sensor", name="nav_camera", type="camera")
    element(camera, "pose", f"{config['camera_offset']} 0 0.65 0 0 0")
    element(camera, "topic", f"/{name}/camera/image")
    element(camera, "update_rate", 5)
    element(camera, "always_on", "true")
    camera_spec = element(camera, "camera")
    element(camera_spec, "camera_info_topic", f"/{name}/camera/info")
    element(camera_spec, "horizontal_fov", config["camera_hfov"])
    image = element(camera_spec, "image")
    element(image, "width", 640)
    element(image, "height", 480)
    element(image, "format", "R8G8B8")
    clip = element(camera_spec, "clip")
    element(clip, "near", 0.05)
    element(clip, "far", 30)
    lidar(base, name, config)
    drive = plugin(model, "diff-drive", "DiffDrive")
    for side, sign in (("left", 1), ("right", -1)):
        for end, wx in (("front", 0.3), ("rear", -0.3)):
            wheel_name = f"{side}_{end}_wheel"
            wheel = element(model, "link", name=wheel_name)
            element(wheel, "pose", f"{wx} {sign * 0.38} 0 -1.57079632679 0 0")
            wi = element(wheel, "inertial")
            element(wi, "mass", 1.0)
            ii = element(wi, "inertia")
            for axis, value in (("ixx", 0.012), ("iyy", 0.012), ("izz", 0.02)):
                element(ii, axis, value)
            solid(wheel, "wheel", "0 0 0 0 0 0", "cylinder", (0.22, 0.12), "0.12 0.12 0.12 1")
            # Low lateral friction supports skid steering in this integration model.
            col = wheel.find("collision")
            friction = element(element(col, "surface"), "friction")
            ode = element(friction, "ode")
            element(ode, "mu", 0.8)
            element(ode, "mu2", 0.1)
            joint = element(model, "joint", name=wheel_name + "_joint", type="revolute")
            element(joint, "parent", "base_link")
            element(joint, "child", wheel_name)
            axis = element(joint, "axis")
            element(axis, "xyz", "0 0 1")
            element(drive, side + "_joint", wheel_name + "_joint")
    for key, value in {
        "wheel_separation": 0.76,
        "wheel_radius": 0.22,
        "topic": f"/{name}/cmd_vel",
        "odom_topic": f"/{name}/wheel_odom",
        "tf_topic": f"/{name}/wheel_tf",
        "max_linear_acceleration": 0.6,
        "max_angular_acceleration": 1.2,
    }.items():
        element(drive, key, value)
    odom = plugin(model, "odometry-publisher", "OdometryPublisher")
    for key, value in {
        "odom_topic": f"/{name}/odom",
        "odom_frame": "world",
        "robot_base_frame": f"{name}/base_link",
        "dimensions": 2,
        "odom_publish_frequency": 20,
    }.items():
        element(odom, key, value)


def build_world(config, include_rovers=True):
    root = ET.Element("sdf", version="1.9")
    world = element(root, "world", name="lunar_test_field")
    physics = element(world, "physics", name="physics", type="ignored")
    element(physics, "max_step_size", 0.002)
    element(physics, "real_time_factor", 1.0)
    element(world, "gravity", "0 0 -1.62")
    scene = element(world, "scene")
    element(scene, "ambient", "0.3 0.3 0.3 1")
    element(scene, "background", "0.015 0.015 0.025 1")
    element(scene, "grid", "false")
    for file, name in (
        ("physics", "Physics"),
        ("user-commands", "UserCommands"),
        ("scene-broadcaster", "SceneBroadcaster"),
    ):
        plugin(world, file, name)
    sensors = plugin(world, "sensors", "Sensors")
    element(sensors, "render_engine", "ogre2")
    light = element(world, "light", name="sun", type="directional")
    element(light, "pose", "0 0 20 0 0 0")
    element(light, "diffuse", "0.8 0.8 0.8 1")
    element(light, "direction", "0.6 0.3 -0.5")
    element(light, "cast_shadows", "true")
    ground = element(world, "model", name="regolith")
    element(ground, "static", "true")
    ground_link = element(ground, "link", name="ground")
    width, height = config.get("ground_size", [40, 30])
    solid(ground_link, "ground", "0 0 -0.1 0 0 0", "box", f"{width} {height} 0.2", "0.35 0.34 0.32 1")
    for hazard in config.get("hazards", []):
        obj = element(world, "model", name=hazard["id"])
        element(obj, "static", "true")
        link = element(obj, "link", name="obstacle")
        x, y = hazard["position"]
        radius, kind = hazard["radius"], hazard["kind"]
        if kind == "crater":
            # A shallow visual depression and rim, with a circular planning exclusion.
            # No fictitious drivable heightmap or invisible collision wall is used.
            solid(link, "basin", f"{x} {y} 0.006 0 0 0", "cylinder", (radius, 0.012), "0.18 0.18 0.18 1", False)
            for i in range(24):
                angle = 2 * math.pi * i / 24
                px, py = x + radius * math.cos(angle), y + radius * math.sin(angle)
                solid(link, f"rim_{i}", f"{px} {py} -0.12 0 0 0", "sphere", 0.23, "0.42 0.41 0.39 1", False)
        elif kind == "habitat":
            solid(link, "module", f"{x} {y} 1.0 0 0 0", "cylinder", (radius * 0.8, 2.0), "0.72 0.73 0.72 1")
            solid(link, "roof", f"{x} {y} 2.05 0 0 0", "cylinder", (radius * 0.85, 0.1), "0.45 0.46 0.47 1")
        elif kind == "solar":
            solid(link, "panel", f"{x} {y} 0.6 0 0 0", "box", f"{radius * 1.5} {radius} 0.15", "0.07 0.09 0.16 1")
        else:
            # Faceted primitive rock, fully enclosed by the configured circular radius.
            solid(link, "boulder", f"{x} {y} {radius * 0.28} 0 0 0.3", "sphere", radius, "0.24 0.235 0.22 1")
    # Surface patches give scale without introducing unmodelled collision objects.
    for i in range(65):
        x = -width / 2 + 2 + ((i * 17) % int(width - 4))
        y = -height / 2 + 2 + ((i * 13) % int(height - 4))
        solid(ground_link, f"regolith_patch_{i}", f"{x} {y} 0.002 0 0 0", "cylinder", (0.15 + (i % 4) * 0.12, 0.003), "0.30 0.295 0.28 1", False)
    for spec in config["rovers"]:
        if include_rovers:
            rover(world, spec, config)
        home = element(world, "model", name=spec["id"] + "_charging_pad")
        element(home, "static", "true")
        link = element(home, "link", name="pad")
        x, y = spec["spawn"][:2]
        pad_size = max(2.4, 2 * config.get("rover_radius", 0.72) + 0.6)
        solid(link, "pad", f"{x} {y} 0.005 0 0 0", "box", f"{pad_size} {pad_size} 0.01", "0.13 0.15 0.18 1", False)
        solid(link, "pad_centre", f"{x} {y} 0.012 0 0 0", "box", f"{pad_size * 0.7} 0.08 0.01", "0.65 0.68 0.7 1", False)
    for target in config["targets"]:
        model = element(world, "model", name="target_" + target["id"])
        element(model, "static", "true")
        x, y = target["position"]
        link = element(model, "link", name="marker")
        marker_height = config.get("marker_height", 0.88)
        pole_height = marker_height - config["marker_diameter"] / 2
        solid(
            link,
            "pole",
            f"{x} {y} {pole_height / 2} 0 0 0",
            "cylinder",
            (0.04, pole_height),
            "0.4 0.4 0.4 1",
        )
        solid(
            link,
            "marker",
            f"{x} {y} {marker_height} 0 0 0",
            "sphere",
            config["marker_diameter"] / 2,
            " ".join(map(str, target["colour"])),
            emissive=True,
        )
    ET.indent(root)
    return ET.tostring(root, encoding="unicode")

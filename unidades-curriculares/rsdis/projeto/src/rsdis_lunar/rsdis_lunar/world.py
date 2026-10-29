"""Generate a small, self-contained SDF integration field (no network assets)."""

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
    solid(ground_link, "ground", "0 0 -0.1 0 0 0", "box", "40 30 0.2", "0.35 0.34 0.32 1")
    # Decoration stays outside the open test routes; obstacle avoidance is future work.
    for index, (x, y, radius) in enumerate(
        [(-5, -8, 0.8), (2, 8, 0.7), (10, 5, 1.0), (10, -6, 0.6), (-12, 2, 0.9)]
    ):
        rock = element(world, "model", name=f"rock_{index}")
        element(rock, "static", "true")
        link = element(rock, "link", name="rock")
        solid(link, "rock", f"{x} {y} 0 0 0 0", "sphere", radius, "0.22 0.21 0.2 1")
    for spec in config["rovers"]:
        if include_rovers:
            rover(world, spec, config)
        home = element(world, "model", name=spec["id"] + "_charging_pad")
        element(home, "static", "true")
        link = element(home, "link", name="pad")
        x, y = spec["spawn"][:2]
        solid(link, "pad", f"{x} {y} 0.005 0 0 0", "box", "1.6 1.6 0.01", "0.15 0.15 0.17 1", False)
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

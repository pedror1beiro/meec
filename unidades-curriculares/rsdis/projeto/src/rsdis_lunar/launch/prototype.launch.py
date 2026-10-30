"""Two-rover integration field with lightweight or locally downloaded Space ROS models."""

from pathlib import Path
import json
import tempfile

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument,
    EmitEvent,
    ExecuteProcess,
    OpaqueFunction,
    RegisterEventHandler,
)
from launch.event_handlers import OnProcessExit, OnShutdown
from launch.events import Shutdown
from launch.substitutions import LaunchConfiguration
from launch.conditions import IfCondition
from launch_ros.actions import Node

from rsdis_lunar.common import load_config
from rsdis_lunar.world import build_world
from rsdis_lunar.viper import adapt_urdf, command_bridges, expand_upstream, profile


def configure(context):
    config_path = LaunchConfiguration("config").perform(context)
    strategy = LaunchConfiguration("strategy").perform(context)
    headless = LaunchConfiguration("headless").perform(context).lower() == "true"
    output = LaunchConfiguration("output").perform(context)
    config = load_config(config_path)
    model = LaunchConfiguration("model").perform(context)
    if strategy not in ("nearest", "energy"):
        raise ValueError("strategy must be nearest or energy")
    temporary = tempfile.TemporaryDirectory(prefix="rsdis_lunar_")
    expanded = None
    if model == "viper":
        config = profile(config)
        simulation_path = LaunchConfiguration("upstream_simulation").perform(context)
        expanded = expand_upstream(simulation_path)
    # Save the actual profile used; agents, metrics and detectors share these values.
    config_file = Path(temporary.name) / "active_mission.json"
    config_file.write_text(json.dumps(config, indent=2), encoding="utf-8")
    config_path = str(config_file)
    world_file = Path(temporary.name) / "lunar_test_field.sdf"
    world_file.write_text(
        build_world(config, include_rovers=model == "lightweight"), encoding="utf-8"
    )
    spawn_nodes = []
    if model == "viper":
        for spec in config["rovers"]:
            urdf_file = Path(temporary.name) / (spec["id"] + ".urdf")
            urdf_file.write_text(
                adapt_urdf(expanded, simulation_path, spec["id"], config), encoding="utf-8"
            )
            x, y, yaw = spec["spawn"]
            spawn_nodes.append(
                Node(
                    package="ros_gz_sim",
                    executable="create",
                    arguments=[
                        "-world",
                        "lunar_test_field",
                        "-name",
                        spec["id"],
                        "-file",
                        str(urdf_file),
                        "-x",
                        str(x),
                        "-y",
                        str(y),
                        "-z",
                        "0.27",
                        "-Y",
                        str(yaw),
                    ],
                    output="screen",
                )
            )
    gazebo = ExecuteProcess(
        cmd=["gz", "sim", "-r", "-v", "3"]
        + (["-s", "--headless-rendering"] if headless else [])
        + [str(world_file)],
        output="screen",
    )
    # Explicit one-way bridges prevent odometry/image feedback and command loops.
    bridges = ["/clock@rosgraph_msgs/msg/Clock[gz.msgs.Clock"]
    for rover in config["rovers"]:
        prefix = "/" + rover["id"]
        bridges += [
            prefix + "/odom@nav_msgs/msg/Odometry[gz.msgs.Odometry",
            prefix + "/camera/image@sensor_msgs/msg/Image[gz.msgs.Image",
            prefix + "/camera/info@sensor_msgs/msg/CameraInfo[gz.msgs.CameraInfo",
            prefix + "/scan@sensor_msgs/msg/LaserScan[gz.msgs.LaserScan",
        ]
        bridges += (
            [prefix + "/cmd_vel@geometry_msgs/msg/Twist]gz.msgs.Twist"]
            if model == "lightweight"
            else command_bridges(rover["id"])
        )
    bridge = Node(
        package="ros_gz_bridge", executable="parameter_bridge", arguments=bridges, output="screen"
    )
    nodes = [
        bridge,
        Node(
            package="rsdis_lunar",
            executable="mission_manager",
            parameters=[
                {
                    "use_sim_time": True,
                    "config": config_path,
                    "strategy": strategy,
                    "output": output,
                }
            ],
            output="screen",
        ),
    ]
    nodes.append(
        Node(
            package="rsdis_lunar",
            executable="mission_monitor",
            parameters=[{"use_sim_time": True, "config": config_path}],
            output="screen",
        )
    )
    for rover in config["rovers"]:
        shared = {"use_sim_time": True, "rover_id": rover["id"]}
        nodes += [
            Node(
                package="rsdis_lunar",
                executable="rover_agent",
                namespace=rover["id"],
                parameters=[{**shared, "config": config_path}],
                output="screen",
            ),
            Node(
                package="rsdis_lunar",
                executable="target_detector",
                namespace=rover["id"],
                parameters=[
                    {
                        **shared,
                        "marker_diameter": config["marker_diameter"],
                        "camera_offset": config["camera_offset"],
                    }
                ],
                output="screen",
            ),
        ]
        if model == "viper":
            nodes.append(
                Node(
                    package="rsdis_lunar",
                    executable="viper_driver",
                    namespace=rover["id"],
                    parameters=[shared],
                    output="screen",
                )
            )
    actions = [gazebo, *nodes, *spawn_nodes]
    actions.append(
        Node(
            package="rsdis_lunar", executable="mission_dashboard",
            parameters=[{"use_sim_time": True, "config": config_path,
                         "port": int(LaunchConfiguration("dashboard_port").perform(context))}],
            condition=IfCondition(LaunchConfiguration("dashboard")), output="screen",
        )
    )

    def spawn_finished(event, context):
        if event.returncode != 0:
            return [EmitEvent(event=Shutdown(reason="Detailed rover spawn failed"))]
        return []

    for spawn in spawn_nodes:
        actions.append(
            RegisterEventHandler(OnProcessExit(target_action=spawn, on_exit=spawn_finished))
        )
    actions.append(
        Node(
            package="rviz2",
            executable="rviz2",
            arguments=[
                "-d",
                str(Path(get_package_share_directory("rsdis_lunar")) / "rviz/mission.rviz"),
            ],
            parameters=[{"use_sim_time": True}],
            condition=IfCondition(LaunchConfiguration("rviz")),
        )
    )
    for process in [gazebo, *nodes]:
        actions.append(
            RegisterEventHandler(
                OnProcessExit(
                    target_action=process,
                    on_exit=[
                        EmitEvent(event=Shutdown(reason="A required simulation process exited"))
                    ],
                )
            )
        )

    # Retain the directory for the full launch lifetime, then clean it at shutdown.
    def cleanup(context, *args, **kwargs):
        temporary.cleanup()
        return []

    actions.append(RegisterEventHandler(OnShutdown(on_shutdown=[OpaqueFunction(function=cleanup)])))
    return actions


def generate_launch_description():
    share = Path(get_package_share_directory("rsdis_lunar"))
    return LaunchDescription(
        [
            DeclareLaunchArgument("config", default_value=str(share / "config" / "mission.json")),
            DeclareLaunchArgument(
                "strategy", default_value="energy", choices=["nearest", "energy"]
            ),
            DeclareLaunchArgument("headless", default_value="false", choices=["true", "false"]),
            DeclareLaunchArgument("rviz", default_value="false", choices=["true", "false"]),
            DeclareLaunchArgument("dashboard", default_value="true", choices=["true", "false"]),
            DeclareLaunchArgument("dashboard_port", default_value="8765"),
            DeclareLaunchArgument(
                "model", default_value="lightweight", choices=["lightweight", "viper"]
            ),
            DeclareLaunchArgument(
                "upstream_simulation", default_value=str(Path.cwd() / "third_party/simulation")
            ),
            DeclareLaunchArgument("output", default_value=str(Path.cwd() / "results")),
            OpaqueFunction(function=configure),
        ]
    )

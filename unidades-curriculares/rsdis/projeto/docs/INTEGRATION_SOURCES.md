# Integration sources and authorship

Only components with a role in the cooperative lunar mission are included.
The paper cites these sources alongside the subsystem that uses them. This table
distinguishes dependency use, adapted source and original group work.

| Component and primary source | Use in this project | Authorship / integration boundary |
| --- | --- | --- |
| [Space ROS simulation, pinned revision](https://github.com/space-ros/simulation/tree/13226b067d921ca88f40cd643a7b3ce4ae8de903) | Optional VIPER geometry and steerable joints; rechargeable battery and solar plugins | Rover assets are fetched separately. Five plugin source/header files are retained under Apache-2.0, with original notices. Namespacing, power interfaces, sample watchdogs, ROS unit conventions and rendering-thread adaptations are ours. |
| [Space ROS lunar exploration demo, pinned revision](https://github.com/space-ros/demos/tree/4b4eb844742307178c80237597b43f7364ddeb5d/lunar_pole_exploration_rover) | Reference mission and upstream integration example | Its original launch is not presented as our implementation. Our two-rover mission, allocation and recovery nodes are developed here. |
| [Gazebo Harmonic systems](https://gazebosim.org/api/sim/8/namespacegz_1_1sim_1_1systems.html) | Physics, lunar gravity, differential drive, joint controllers, cameras, lidar and ground-truth odometry | Stock systems are dependencies. The generated outpost and additional rock layout are our world design. |
| [Gazebo battery interfaces](https://gazebosim.org/api/sim/8/battery.html) | BatterySoC, consumer power and simulator enforcement of exhaustion | The selected rechargeable plugin originates from Space ROS, itself adapted from Gazebo LinearBatteryPlugin. The parameters remain a scaled demonstration model. |
| [ros_gz bridge implementation](https://github.com/gazebosim/ros_gz/tree/jazzy/ros_gz_bridge) | One-way typed Gazebo/ROS bridges, including BatteryState and power topics | Used as an installed ROS package. Its BatteryState converter copies percentage directly, motivating our correction from 0..100 to 0..1. |
| [ROS 2 Jazzy QoS specification](https://github.com/ros2/ros2_documentation/blob/jazzy/source/Concepts/Intermediate/About-Quality-of-Service-Settings.rst) | Best-effort local telemetry/sensors, reliable mission messages, transient-local mission state | These DDS policies are existing middleware facilities. Our gateway, bounded retries, expiry checks and seeded link-fault emulator are original application code. The emulator is not a measured radio or DDS-loss model. |
| [OpenCV colour conversions and contours](https://docs.opencv.org/4.x/d9/d61/tutorial_py_morphological_ops.html) | HSV segmentation, contour processing and image conversion | OpenCV is an installed dependency. Marker identity, silhouette-angle ranging, filtering and timestamped world projection are our implementation. |
| [Matplotlib](https://matplotlib.org/stable/) | Map design illustrations and measured-result plots | Plotting dependency only. Planned layouts are labelled separately from recorded Gazebo observations. |

## Exact source tracking

`upstream.lock.json` pins the fetched Space ROS repositories. The energy package's
`UPSTREAM.json` records the upstream path, immutable source URL, original SHA256
and adapted SHA256 of every retained file. `scripts/check_attributions.py`
checks this manifest, copyright notices and the included Apache-2.0 licence.

The copied plugin headers credit Robin Baran, Stevedan Ogochukwu Omodolor Omodia
and, where present in the pinned source, Alexey Simonov. These notices must be
preserved in distributions. Dependency packages retain their own licences in the
Ubuntu/ROS installation; this project does not relicense their source.

## Group contribution

The group integrates the sources through new per-rover interfaces and develops
mission allocation, local confirmation, route safety, charging-pad control,
communication fault/recovery logic, experiment supervision and analysis. Neither
the upstream models/plugins nor standard A* and DDS concepts are claimed as new
research. The report's evidence comes from retained runs, with revisions and
configurations, and does not claim unmeasured policy improvements.

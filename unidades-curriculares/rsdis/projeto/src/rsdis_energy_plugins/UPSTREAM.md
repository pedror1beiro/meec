# Upstream provenance and adaptations

The five files in `src/` originate from Space ROS `simulation`, revision
`13226b067d921ca88f40cd643a7b3ce4ae8de903`:
https://github.com/space-ros/simulation/tree/13226b067d921ca88f40cd643a7b3ce4ae8de903/plugins

Original copyright notices and the Apache-2.0 licence are preserved. The RSDIS
team adapts these existing plugins rather than claiming their original design.
Our CMake package builds only the two required plugins against ROS Jazzy's
Gazebo Harmonic vendor libraries, without building the entire upstream demo.

Adaptations made for this integration:

- BatteryState percentage and current follow ROS units/sign conventions.
  The contract is defined by [sensor_msgs/BatteryState](https://github.com/ros2/common_interfaces/blob/jazzy/sensor_msgs/msg/BatteryState.msg);
  [ros_gz's converter](https://github.com/gazebosim/ros_gz/blob/jazzy/ros_gz_bridge/src/convert/sensor_msgs.cpp)
  copies these fields directly.
- Power samples are held between transport callbacks, with an expiry watchdog.
- A namespaced dynamic load input accounts for avionics and measured motion.
- Charging accepts solar and a dock power source. Charge stays within capacity;
  an empty battery can recover when external power becomes available.
- Battery and power telemetry are throttled to 10 Hz simulation time.
- Solar line-of-sight casts from just above the panel towards the directional
  light, consistently with its cosine incidence calculation, at 10 Hz. It uses
  SceneUpdate to avoid forcing render updates at every physics tick. Render
  objects are released in the RenderTeardown callback on the correct thread.

These remain demonstration parameters, not calibrated flight hardware or a
thermal/electrochemical model. The solar plugin checks rendered line of sight;
it requires the rendering engine even in a headless mission.

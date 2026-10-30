# Navigation and map update

The original demo could drive into poles before their colour was detected, cut
corners around a valid A* line, and oscillate when two rovers met. These changes
address those mechanisms in the shared controller and both model profiles.

## Maps

`mission.json` now describes an 80 x 60 m outpost with 76 x 56 m navigation bounds,
five camera-discovered scientific sites, two charging pads, ten boulders, four
crater exclusions, a habitat and a solar array. The rovers explore separate north
and south sectors, sweep their cameras at survey stops, and share discoveries.
`mission_small.json` retains a compact 40 x 30 m field for quicker checks.

Terrain hazards are a known prior map. Their configured geometry is used by both
world generation and planning, so scenery is not silently omitted from the
planner. Craters use dark flat basins and shallow visual rims. They are navigation
exclusions; this update does not add a physically excavated heightmap or validate
driving on slopes. All assets are generated locally without external downloads.

## Pole and rover avoidance

- A front range sensor sees geometry independently of the colour detector. Both
  lightweight and VIPER models publish `/roverN/scan` through a one-way ROS bridge.
- A* includes physical obstacle radii, a circular rover footprint and a margin.
  The lightweight radius is 0.72 m; VIPER uses 1.35 m and a 2.7 m stand-off.
  Marker keep-outs also include 0.25 m of estimation allowance.
- Routes and edges stay inside configured bounds. Inspection uses a fixed point
  outside the pole keep-out, rather than chasing the marker centre. Improved
  camera estimates shift this point without changing its approach direction.
  Arrival hysteresis prevents range jitter from alternating approach and camera
  aiming at the stand-off boundary.
- Sphere range uses silhouette tangent angles. A width-only estimate could
  underestimate range for a target near the image edge and misplace its keep-out.
- The lightweight wheel contacts use equal friction coefficients. The physical
  regression exposed a heading-dependent steering lock with the original pair;
  calibration now requires more than a full turn in both directions and measured
  translation while the chassis stays level.
- The follower turns before translation, slows near route corners, and checks
  the commanded curved sweep over reaction time plus stopping time. A scan older
  than 0.6 simulation seconds or invalid range data stops motion.
- Unlabelled scan returns enter an eight-second local obstacle memory. Peer
  poses are separate obstacles; a right-side passing manoeuvre prevents symmetric
  head-on oscillation. Stopped/unavailable peers remain occupied at their last pose.
- Sustained inability to find a path releases inspection work for retry. A rover
  cannot report a blocked return as a successful arrival at base.

The safeguards assume the supplied level world, limited speeds and functioning
ground-truth localisation. A forward planar scan cannot sense every low object,
drop-off or rear obstacle. Crater avoidance depends on the prior map. This is
not a replacement for a full navigation/localisation stack in arbitrary terrain.

## Interaction

The launch starts a local console at `http://localhost:8765`. It displays rover
modes, navigation reasons, camera images, paths, battery, discovered sites and
activity. Pause/resume preserves assignments; Return both to base ends exploration.
Enable/disable buttons exercise recovery of an unavailable rover.

Equivalent ROS controls:

```bash
ros2 service call /mission/set_paused std_srvs/srv/SetBool '{data: true}'
ros2 service call /mission/set_paused std_srvs/srv/SetBool '{data: false}'
ros2 service call /mission/recall std_srvs/srv/Trigger '{}'
ros2 topic echo /rover1/navigation_state
```

Use `dashboard:=false` or a different `dashboard_port` when needed. The server
binds only to the simulation PC. When using Docker, publish the loopback port
and adjust container networking deliberately; native Linux is the default path.

Each console run saves a latest checkpoint and camera images in its output
directory. `python scripts/view_recorded_console.py --run RUN_DIRECTORY` opens
that checkpoint on Windows or Linux without ROS. It is visibly labelled as a
recording, and all mission controls are disabled.

## Regression checks

The portable tests include an unseen pole detour with no colour report, stale
and invalid scan stops, curved-command braking, large-obstacle detours, bounds,
monotone escape from an inflated disk, two opposing rovers passing and exchanging
their start positions, and pause/recall assignment handling. The large-map
nominal and failure rehearsals must confirm five sites, return both rovers, and
record zero conservative footprint overlaps.

The Linux CI builds Jazzy packages, requires real camera/laser/odometry streams,
checks full-circle steering, runs the compact mission with console pause/resume,
and exercises the expanded map with a temporary rover failure. Its independent geometry audit uses
actual Gazebo odometry and known test geometry; it does not feed truth to the
controller or count as a force/contact measurement. Logs and audit values are
saved under `results/smoke_.../`.

Sensor configuration follows the [Gazebo Harmonic sensor documentation](https://gazebosim.org/docs/harmonic/sensors/).

# Space ROS reference assets

The idea builds on these public repositories:

- [Lunar pole exploration demo](https://github.com/space-ros/demos/tree/4b4eb844742307178c80237597b43f7364ddeb5d/lunar_pole_exploration_rover)
- [Simulation models and plugins](https://github.com/space-ros/simulation/tree/13226b067d921ca88f40cd643a7b3ce4ae8de903)

The demo documents ROS 2 Jazzy and Gazebo Harmonic, a VIPER-inspired rover,
Mons Mouton terrain, cameras, wheel commands, solar generation and rechargeable
battery plugins. Its authors credit Robin Baran and Stevedan Ogochukwu Omodolor
Omodia. Preserve upstream authorship and licence notices when adapting assets.

## Retrieve the sources and large meshes

Pinned revisions are recorded in `upstream.lock.json`. The adapted rover assets
are runtime-tested in our flat field; the original upstream demo and its physical
energy plugins have separate validation requirements.

```bash
# On either OS: small Git checkout; large LFS resources remain pointers.
python3 scripts/fetch_upstream.py

# On the Linux PC, install git-lfs if necessary and materialize the lunar assets.
sudo apt-get install git-lfs
python3 scripts/fetch_upstream.py --assets
```

`third_party/` is ignored by this project's Git and colcon discovery. A second
invocation checks the existing origin and exact revision and refuses to replace
a different checkout. Downloads do not execute the upstream build or launch code.

## Running the original demo separately

Follow the pinned [upstream README](https://github.com/space-ros/demos/blob/4b4eb844742307178c80237597b43f7364ddeb5d/lunar_pole_exploration_rover/README.md)
on Linux. Its Docker build is substantial and its launcher assumes Linux display
and graphics access. The demo Dockerfile imports `simulation` using a manifest
that originally tracks `main`; for reproducible experiments replace that reference
in a working copy with the revision in our lock file before building.

Do not confuse a source checkout with downloaded mesh assets. If a `.dae` file
starts with `version https://git-lfs.github.com/spec/v1`, the actual mesh has not
been retrieved. Our `--assets` mode verifies the main rover and terrain meshes.

## Cooperative rover adapter

The optional `model:=viper` launch path now prepares two copies of the actual
upstream rover. It preserves 29 links, 28 joints, mesh geometry and inertias per
rover. Our adapter replaces the upstream single-rover control/sensing plugins
with per-rover Gazebo joint controllers, world odometry, joint feedback and a
single reduced-resolution mission camera. No upstream C++ plugin build is needed
for this option.

```bash
python3 scripts/fetch_upstream.py --assets
python3 scripts/prepare_viper.py --validate-sdf
bash scripts/run_demo.sh model:=viper
```

The larger profile adjusts camera extrinsics, marker height, inspection stand-off,
marker clearance and peer spacing. It saves the active configuration with each
run. The driver computes four-wheel steering, stops on stale commands or missing
joint feedback, and waits for steering alignment before rotating the wheels.
The camera mast and solar panels remain fixed at their original zero-angle poses.
The Gazebo joint controller interfaces were checked against the official
[joint position controller source](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/joint_position_controller/JointPositionController.cc)
and [joint velocity controller source](https://github.com/gazebosim/gz-sim/blob/gz-sim8/src/systems/joint_controller/JointController.cc).

The actual upstream Xacro expands on the Windows authoring machine, all referenced
rover meshes have been materialized, and both adapted URDFs pass structural tests.
Gazebo conversion, controller loading, wheel contact, joint feedback and rendered
cameras also pass the optional Linux CI gate. At commit `8bcfb9a`, both rovers pass
full-circle steering and translation, then complete all five compact-map targets
and return in 171.5 simulation seconds with zero conservative footprint overlaps.
[Validation run](https://github.com/pedror1beiro/meec/actions/runs/41070906055).
Repeat the explicit gate on the target machine:

```bash
python3 scripts/smoke_test_ros.py --model viper --timeout 240
```

This gate requires motion, cameras and odometry from **both** rovers, plus steering
feedback and mission detections/assignments. A process that merely spawns models
does not pass. The GitHub workflow runs full physical drive and compact mission
checks using its manual `viper` input. The conversion preflight's
`physical_runtime_checked: false` describes that preparation step only; runtime
evidence is in the separate drive and smoke reports.

The flat test field and synthetic energy model are retained. This adapter does
not yet use Mons Mouton as traversable terrain or the physical solar/battery plugins.

## Remaining integration milestones

1. Validate the upstream single rover on the Linux GPU, including steering,
   camera topics, battery and panel output. Save the successful revision and logs.
2. Repeat the validated two-rover compact gate on the Linux GPU and validate the
   enlarged map before using the detailed profile in comparative experiments.
3. Validate contact, steering and clearance on additional surfaces. The current
   physical evidence covers a level field and fixed camera mast.
4. Replace the synthetic energy input with the battery plugin's charge state,
   and account for panel charging. Calibrate experiment duration and battery units
   before comparing outcomes; the upstream battery is intended for long missions.
5. Move to a verified terrain patch, ground the starting poses and targets, and
   introduce terrain-aware navigation. The existing 2D image-to-world projection
   is not adequate for arbitrary rover roll/pitch or terrain elevations.

This sequence retains a working integration baseline while detailed models are
introduced. The original demo's high-resolution multi-camera configuration can
be expensive; start with a single reduced-resolution navigation camera per rover.

# Cooperative Lunar Exploration

RSDIS academic project: two rovers explore a lunar test field, detect scientific
markers, share discoveries, distribute inspections, recover from rover failures,
and return to their bases. The research question is whether allocation that
considers battery state improves mission outcomes compared with nearest-rover
allocation under the same safety rules.

| Student number | Team member |
| --- | --- |
| 1221309 | Henrique Correia |
| 1231177 | Pedro Ribeiro |
| 1231216 | Francisco Liquito |

**Status: initial prototype.** Mission logic, marker-image tests and world
generation can be checked on Windows. ROS package compilation, Gazebo physics,
rendered-camera detection and the Docker image still require validation on a
Linux machine. No Gazebo results or performance improvements are claimed.

## Start here on the other PC

The target environment is **Ubuntu 24.04, ROS 2 Jazzy and Gazebo Harmonic**.
Copy this whole folder or extract the provided project archive. Linux commands
below run from the project root. Do not copy `.venv`, `build`, `install` or `log`
between operating systems.

1. Install ROS 2 Jazzy using the [official Ubuntu instructions](https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html).
2. Install this project's dependencies and build:

   ```bash
   bash scripts/setup_ubuntu.sh
   ```

3. Start the two-rover mission:

   ```bash
   bash scripts/run_demo.sh
   ```

4. Check that both cameras, odometry streams, detections and assignments work:
   stop the previous launch first, then run:

   ```bash
   source /opt/ros/jazzy/setup.bash
   source install/setup.bash
   python3 scripts/smoke_test_ros.py --timeout 180
   ```

The launch stops all its processes if a required node exits. Do not run two
missions in the same ROS domain at once; the topic names are intentionally shared.
For a separate team experiment, set a different `ROS_DOMAIN_ID` in every terminal
belonging to that experiment.

## What is implemented

| Feature | Initial implementation |
| --- | --- |
| Simulation | Generated SDF world, lunar gravity, two separate four-wheel rovers, two 640x480 RGB cameras |
| Exploration | Separate waypoint routes over an open field |
| Perception | OpenCV colour-sphere detection and known-diameter range approximation |
| Sharing | Typed ROS detections in a shared world frame; unique marker IDs suppress duplicates |
| Coordination | One owner per target, renewable leases, retries, stale-rover detection |
| Allocation | Nearest-rover baseline and battery-aware scoring with identical feasibility checks |
| Navigation | Heading control and planar A* detours around shared marker locations |
| Energy | Accelerated synthetic depletion and recharging at each rover's base |
| Recovery | A service disables a rover; its task is released and can be reassigned |
| Completion | All five markers confirmed by camera, then both rovers parked at base |
| Results | CSV telemetry, JSONL mission events, JSON run configuration and summary |

The default world uses our lightweight rover models. An **experimental
`model:=viper` option** adapts the actual Space ROS rover meshes, inertias and
steerable wheels to the same mission, with namespaced Gazebo joint controllers
and joint-feedback interlocks. Its structure and steering mathematics have been
checked locally; physical execution remains unverified. The detailed terrain and
physical solar/battery plugins are later milestones. See [the upstream guide](docs/UPSTREAM.md).

To prepare the detailed rover on Linux after the default smoke test passes:

```bash
python3 scripts/fetch_upstream.py --assets
python3 scripts/prepare_viper.py --validate-sdf
bash scripts/run_demo.sh model:=viper
# Stop the launch before this separate integration check:
python3 scripts/smoke_test_ros.py --model viper --timeout 240
```

The world uses ground-truth odometry. The controller does not implement SLAM,
general obstacle mapping, rough-terrain navigation, or scientific sample analysis.
Coloured spheres stand in for points of scientific interest. The battery values
are dimensionless, accelerated demonstration parameters, not calibrated VIPER data.

## Useful runs

```bash
# Same world and safety constraints, nearest-rover allocation
bash scripts/run_demo.sh strategy:=nearest

# Gazebo server with EGL sensor rendering, without the desktop GUI
bash scripts/run_demo.sh headless:=true

# Optional RViz view (install ros-jazzy-rviz2 first)
bash scripts/run_demo.sh rviz:=true

# Custom mission configuration (absolute path)
bash scripts/run_demo.sh config:=/absolute/path/to/mission.json

# Failure injection in a second sourced terminal
ros2 service call /rover1/set_enabled std_srvs/srv/SetBool '{data: false}'
# Restore the rover
ros2 service call /rover1/set_enabled std_srvs/srv/SetBool '{data: true}'

# Observe the mission
ros2 topic echo /mission/status
ros2 topic echo /mission/detections
ros2 topic echo /mission/results
```

The GUI opens Gazebo. Select a rover in the entity tree and press **F** to focus it.
Use `rqt_image_view` if installed to inspect `/rover1/camera/image` or
`/rover2/camera/image`. In RViz2, use fixed frame `world`; the optional monitor
publishes mission markers and paths (see launch options).

Each run writes to a unique directory under `results/`. A normal success summary
has `reason: all_targets_confirmed_and_returned`. A time-limited or interrupted
run is retained and must not be discarded from experimental results.

## Portable rehearsal on Windows

This does not need ROS, Gazebo or extra Python packages:

```powershell
python scripts/offline_demo.py
python scripts/offline_demo.py --failure-at 20 --failure-duration 30
python scripts/compare_offline.py --seeds 3
```

Open the generated `results/.../playback.html` in a browser to play the mission.
The rehearsal shares the actual coordinator and rover control logic, but uses
kinematic motion and **oracle detections from target coordinates**. It is a
debugging tool, not evidence of camera accuracy or physical feasibility.

## Tests

Core and world tests use Python's standard library:

```bash
python3 -m unittest discover -s tests -v
```

On Ubuntu, the setup script installs OpenCV so image tests run too. On Windows:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The GitHub Actions workflow builds the ROS packages in a Jazzy container and runs
the real sensor smoke test on Linux when this project is pushed to a repository.
The workflow has not been run in this Windows session.

## Optional Docker build on Linux

```bash
docker build -f docker/Dockerfile -t rsdis-lunar .
# Use software rendering for a first headless check; camera rendering may be slow.
docker run --rm -e LIBGL_ALWAYS_SOFTWARE=1 -v "$PWD/results:/workspace/results" rsdis-lunar
```

Hardware rendering depends on the Linux host's graphics setup. A native Ubuntu
run is the first validation path. The upstream `run_gpu.sh` is not a Windows
launcher and is not executed by our setup scripts.

## Project documents

- [Proposal criteria and acceptance checks](docs/PROPOSAL_COMPLIANCE.md)
- [System architecture and assumptions](docs/ARCHITECTURE.md)
- [Experiment protocol](docs/EXPERIMENTS.md)
- [Upstream sources and integration plan](docs/UPSTREAM.md)
- [Linux handoff and troubleshooting](docs/HANDOFF.md)
- [Continue from the meec GitHub repository](docs/CONTINUATION.md)
- [Demo recording and presentation plan](docs/DEMO.md)
- [Local validation record](docs/VALIDATION.md)

The IEEE paper source is under `report/`. It is a draft with explicitly pending
Gazebo results, not a completed experimental paper. Complete the experimental
results and conclusions before submission.

The transfer bundle is `output/rsdis_lunar_project.zip`, with a SHA-256 checksum
beside it. It contains source, fixed scenarios, the paper draft and labelled
offline examples. It excludes machine-specific environments, large upstream
assets and intermediate build folders. Regenerate it with:

```bash
python3 scripts/build_archive.py
```

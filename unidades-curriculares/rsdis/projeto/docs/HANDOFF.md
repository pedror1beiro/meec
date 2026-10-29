# Handoff to the Linux PC

## Recommended order

1. Copy/extract the project to a Linux filesystem, e.g. `~/RSDIS`.
2. Use Ubuntu 24.04 with ROS 2 Jazzy. Follow the official ROS installation guide
   linked from README if ROS is not installed.
3. Run `bash scripts/setup_ubuntu.sh` and review the build output.
4. Run `bash scripts/run_demo.sh`; inspect the two robot entities in Gazebo.
5. Verify both camera views, then run the smoke test after stopping the first launch.
6. Execute one supervised experiment and inspect its logs and summary.
7. Fetch the detailed upstream assets if the lightweight integration is stable.
8. Use `model:=viper` for the experimental detailed-rover option and run its own
   smoke test before using that profile in experiments.
9. Run the matched comparison and complete the paper/video from actual results.

No Windows system settings, WSL installation or Docker installation were required
to create this project. Python environment and generated build folders are local
to each machine and should not be copied across operating systems.

## Problems to check first

| Symptom | Check |
| --- | --- |
| Package not found | Source `/opt/ros/jazzy/setup.bash`, then this workspace's `install/setup.bash` |
| `gz sim` not found | Install `ros-jazzy-ros-gz`; use Gazebo Harmonic, not Gazebo Classic |
| Rovers visible but no movement | Confirm `/clock`, `/roverN/odom`, agent logs and `/roverN/cmd_vel` |
| Camera image exists but no detections | Check CameraInfo, marker visibility, BGR conversion, HSV masks and detector timestamps |
| Headless rendering fails | Check EGL/OpenGL/GPU drivers; try the GUI run; read Gazebo's Ogre2 logs |
| Very slow simulation | Use headless mode, verify hardware rendering and keep reduced-resolution cameras |
| Smoke test times out | Inspect `results/smoke_.../launch.log` and `smoke_report.json`; identify which exact stream is missing |
| RViz unavailable | Install `ros-jazzy-rviz2` or keep `rviz:=false` |
| External model is invisible | Confirm Git LFS materialized the `.dae` files and resource paths are correct |
| All targets confirmed but mission not successful | Check that both agents return and reach `parked`; success includes the return leg |
| Comparison has no rows | The exporter intentionally ignores offline rehearsals unless `--include-offline` is set |

The rendering setup varies by host. A GUI-free server still needs a functioning
render engine for camera images. Do not replace missing rendered images with
known target coordinates to make the smoke test pass.

## Specific unverified boundaries

The Linux build, Gazebo plugin loading, physical wheel behaviour, camera topic
names, rendered marker visibility, RViz and Docker execution were not run on the
Windows authoring machine. The Linux smoke test is the explicit gate for these
interfaces. Upstream source pins and LFS assets have been downloaded on the
authoring machine. The detailed rover adapter is prepared but physically untested;
the uneven terrain and physical solar/battery plugins remain future steps.

The built-in LaTeX preview compiler could not start in this Windows session, but
the local MiKTeX installation compiled the draft successfully. The reviewed PDF
is `output/pdf/rsdis_paper_draft.pdf`; the editable source is `report/main.tex`.
Replace the authors and pending results before submission.

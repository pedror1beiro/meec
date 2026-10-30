# Proposal criteria and acceptance checks

Source: the user-provided `RSDIS_Proposal_MultiRobot.pdf`, especially pages 4,
12, 13 and 14. The attached proposal defines academic requirements; its examples
do not require a UAV team, a maritime setting, SLAM, or a specific task allocator.

## Requirements

| Proposal requirement | Project response | Evidence required before submission |
| --- | --- | --- |
| Develop or reuse a 3D Gazebo scenario | Lunar test field, lunar gravity, two rover models, RGB sensors and targets | Gazebo launch, screenshots, reproducible world and model files |
| Develop ROS modules for multi-robot control and perception | Custom agent, coordinator and camera detector; typed interfaces | Compiling ROS packages, launch files, code and tests |
| Information sharing and complementary tasks | Detections shared between rovers; different search sectors; one detects and another can inspect; work transferred after failures | A recorded cross-rover assignment and a recorded task reassignment |
| IEEE scientific paper describing work, results and conclusions | IEEE-format draft and a matched experiment protocol | Completed measurements, figures, references and conclusions based on actual runs |
| Originality of chosen challenge | Lunar mission with an explicit energy/assignment trade-off | Demonstration and discussion of what the team developed versus reused |
| Integration of existing ROS packages | Gazebo, ros_gz, ROS 2 message tools, OpenCV/cv_bridge; Space ROS assets planned | Versions, upstream citations, integration explanation and licence notices |
| Overall solution meets its objectives | Discover, inspect, recover and return to base | End-to-end Linux run and failure scenario |

## Deliverables from page 13

| Deliverable | Present state |
| --- | --- |
| World and robot models in SDF/URDF | Procedural SDF source and exported test world; optional adapter for detailed upstream rover URDFs |
| ROS packages, launch files, README | Built on Jazzy; lightweight compact and expanded missions validated in Linux CI |
| Multi-robot mission video | Recording script/checklist prepared; capture after successful Gazebo integration |
| Final report and presentation | Paper draft and presentation outline prepared; results and final slides pending |

## Minimum acceptance gate

1. Both robots spawn and can move independently; odometry frames do not collide.
2. Both real rendered cameras publish non-empty images and CameraInfo.
3. Targets are discovered from images; target truth is not injected into the coordinator.
4. Each target has one active owner and is confirmed only by a recent local observation.
5. The demonstration includes a target discovered by one rover and inspected by the other.
6. Disabling one rover releases its task and another rover can complete it.
7. Battery reserve affects assignment or triggers a return/recharge.
8. Mission success requires all target confirmations and both rovers parked at base.
9. Every experimental run saves its configuration, telemetry, events and outcome.
10. The paper distinguishes actual Gazebo experiments from offline debugging runs.

The lightweight functional gates now have retained Linux evidence in
`examples/gazebo_validation_20261030/`: real images, full missions, failure task
transfer, return/recharge, telemetry and metadata. Final academic deliverables
still need the allocation-policy comparison, completed results/conclusions,
demonstration recording and presentation.

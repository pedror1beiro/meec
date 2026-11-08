# Demo video and presentation

Record only after an actual Gazebo run passes the sensor smoke test. The offline
playback is a separate debugging artifact and must be labelled if shown.

## Suggested three-minute video

1. **0:00-0:20:** Title, mission objective, two rovers and the lunar test field.
2. **0:20-0:50:** Both rovers explore separate sectors. Show an actual camera image
   and the corresponding shared target marker.
3. **0:50-1:20:** Show one target's `discovered` and `assigned` records, ideally with
   different rover IDs; explain why the allocator chose the inspecting rover.
4. **1:20-1:55:** Disable rover1 during an active inspection. Show the task release,
   changed ownership and the remaining rover completing it.
5. **1:55-2:25:** Show an actual battery decision: infeasible assignment, return or
   recharge. Identify native electrical units and accelerated model parameters.
6. **2:25-2:45:** Show all target confirmations and both rovers parked at base.
7. **2:45-3:00:** Show the measured comparison and state the main limitation.

If a particular trace lacks one of these events, record an appropriate predefined
scenario and state the scenario change. Do not splice footage to imply a single
continuous run when the clips came from different experiments.

## Record the ROS data

The supervisor now records genuine Gazebo overhead and rover camera frames,
adds ROS telemetry and encodes `mission.mp4` after shutdown. It can also
capture a metrics-only SQLite ROS bag:

```bash
python3 scripts/create_scenarios.py --count 1 --output results/demo_scenarios
python3 scripts/run_experiment_ros.py --config results/demo_scenarios/failure_00.json \
  --strategy energy --record-video --record-bag --wall-timeout 2400
```

Video metadata records capture/playback rates, frame count and simulation window.
Playback is nominally 5x simulation time. A recorded overhead camera is distinct
from the console's schematic map. Keep the entire run and its metadata together.

### Optional separate camera bag

In a sourced terminal on Linux, choose a unique output path:

```bash
ros2 bag record -o results/demo_bag_01 \
  /clock /mission/status /mission/detections /mission/goals /mission/results \
  /mission/return_home /mission/finished \
  /rover1/odom /rover2/odom \
  /rover1/camera/image /rover2/camera/image
```

Install the appropriate ROS bag tooling if it is not already available. Recording
images uses substantial disk bandwidth; retain a separate metrics-only capture
for large experimental batches. Use the host's screen recorder for Gazebo/RViz.

## Eight-slide presentation outline

1. Mission, motivation and research question.
2. Proposal requirements and our original contribution.
3. World, rover models and explicit simulation assumptions.
4. ROS architecture and camera-to-world detection pipeline.
5. Allocation policies and common battery feasibility constraints.
6. Failure recovery, with one real event timeline.
7. Matched experiment results, including unsuccessful runs.
8. Conclusions, limitations, upstream credits and next steps.

The Space ROS model and adapted energy plugins are credited in
`INTEGRATION_SOURCES.md` and the paper. See `ESTUDO_APRESENTACAO_PT.md` for
the suggested division between the three presenters and defence questions.

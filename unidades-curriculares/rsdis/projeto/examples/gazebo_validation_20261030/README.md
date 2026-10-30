# Gazebo validation, 30 October 2026

These are actual ROS 2 Jazzy / Gazebo Harmonic runs in the Linux CI container.
The validated source commit is `1317fb3737fe33d6a6e8379c961f349c6693f61c`.
[Workflow run and complete logs](https://github.com/pedror1beiro/meec/actions/runs/41065141765).

| Gate | Result |
| --- | --- |
| Physical drive | Full turns in both directions, translation and level attitude passed |
| Compact mission | Five targets confirmed, both rovers returned in 116.0 simulation seconds |
| Console | Real camera previews, telemetry and pause/resume passed |
| Expanded failure mission | Five targets confirmed, both rovers returned in 656.5 simulation seconds |
| Expanded clearance | Minimum conservative obstacle gap 0.2827 m; zero footprint overlaps |
| Failure intervention | rover1 disabled at world time 20 s and restored at 50 s; both service calls succeeded |
| Cooperation | Red task released by rover1, reassigned to rover2, and confirmed from rover2's camera |

The compact gap was 0.5421 m with zero overlaps. Clearance comes from a conservative
planar footprint audit using actual Gazebo odometry; it does not measure contact
forces. Event times are relative to mission start; intervention times in run
metadata use the world clock.

This is functional validation of one allocation policy and one expanded failure
layout. Statistical allocation comparisons remain pending. The historical failed
integration runs remain visible in GitHub Actions and led to the added steering,
range-estimation and stand-off regressions.

The files retain active configurations, telemetry, events, summaries and platform/
package versions. Camera images in `compact/` were rendered by Gazebo. The newer
console checkpoint format is exported by subsequent runs.

To repeat the expanded failure run in a sourced Linux workspace:

```bash
python3 scripts/run_experiment_ros.py --config examples/gazebo_validation_20261030/expanded_failure/config.json --strategy energy --wall-timeout 1400
```

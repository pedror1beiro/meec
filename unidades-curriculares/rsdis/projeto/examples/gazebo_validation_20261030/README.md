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
package versions. Camera images in `compact/` were rendered by Gazebo.

## Later checkpoint and detailed-rover validation

The `compact_checkpoint/` and `viper_compact/` folders come from source commit
`8bcfb9ae690abac5399997c4ab5660c116b8c6d8`. They are separate from the earlier
lightweight evidence above. The former is the saved end-of-mission console from
[this lightweight run](https://github.com/pedror1beiro/meec/actions/runs/41070832128),
artifact `compact-console-checkpoint`, folder `smoke_1793370150415106301`.
It completes in 116.0 simulation seconds with minimum obstacle gap 0.5453 m and
zero overlaps. The same workflow's `expanded_failure_repeat/` completes the large
failure scenario in 631.5 simulation seconds, with minimum obstacle gap 0.2804 m,
peer gap 5.0920 m and zero overlaps. Both intervention services succeed, and the
red task again transfers from the disabled rover1 to rover2 for camera confirmation.
The recorded runtime source fingerprint is
`b93fb802e3d3562f21a023df96539c6d2a7717c0496cd19ea60f920dcc46faaa`.

The latter retains the detailed rover's complete compact mission, physical drive
report and checkpoint from [this VIPER run](https://github.com/pedror1beiro/meec/actions/runs/41070906055).
Both models pass full-circle steering and translation. VIPER confirms all five
targets and returns both rovers in 171.5 simulation seconds. Its minimum
conservative obstacle gap is 0.5218 m, peer gap 0.4489 m, with zero overlaps.
Real camera, CameraInfo, laser, joint feedback, console pause/resume and checkpoint
export checks pass. The detailed model's enlarged map and rough terrain remain
unverified; these runs do not compare allocation policies.

To inspect either recorded console on Windows or Linux with standard Python:

```bash
python scripts/view_recorded_console.py --run examples/gazebo_validation_20261030/compact_checkpoint
# Or replace compact_checkpoint with viper_compact.
```

Open `http://localhost:8770`. This is a saved checkpoint, with mission controls
disabled. It is not a live simulation or a video of the entire mission.

To repeat the expanded failure run in a sourced Linux workspace:

```bash
python3 scripts/run_experiment_ros.py --config examples/gazebo_validation_20261030/expanded_failure/config.json --strategy energy --wall-timeout 1400
```

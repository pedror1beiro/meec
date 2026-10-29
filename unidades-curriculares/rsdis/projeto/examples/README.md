# Offline examples

These examples are portable kinematic rehearsals with oracle detections, not
Gazebo runs. Open each `playback.html` in a browser; no server is required.

- `offline_nominal`: discover five markers, inspect them, and return both rovers.
- `offline_failure`: disable rover1 for 30 simulated seconds; rover2 takes over.
- `choice_nearest` and `choice_energy`: the same diagnostic layout under both
  policies. Both rovers can inspect the central blue marker, but different
  initial batteries lead to different ownership under the two ranking rules.

The diagnostic is intentionally constructed to exercise the ranking difference.
It is not evidence that the energy rule performs better. The initial rehearsal
shows a small time penalty for that rule in this particular diagnostic.

The default comparison cases produced identical policy outcomes in the current
offline model. Preserve that observation; do not present it as a demonstrated
energy advantage or as an actual Gazebo result.

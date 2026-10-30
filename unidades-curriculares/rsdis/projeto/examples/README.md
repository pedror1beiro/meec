# Offline examples

These examples are portable kinematic rehearsals with oracle detections, not
Gazebo runs. Open each `playback.html` in a browser; no server is required.

- `offline_nominal`: discover five markers, inspect them, and return both rovers.
- `offline_failure`: disable rover1 for 30 simulated seconds; rover2 takes over.
- `expanded_nominal` and `expanded_failure`: the 30 October 80 x 60 m map, laser
  rehearsal and updated controller, with a conservative clearance audit in each
  summary. These replace the compact examples for checking the latest map.
- `navigation_matrix.csv`: twelve portable rehearsals with three route orders,
  nominal/failure conditions and both allocation policies.
- `gazebo_validation_20261030`: actual Linux ROS/Gazebo functional validation,
  including complete compact and expanded missions, real camera images, a
  failure reassignment and clearance audits. Its README identifies the source
  commit and workflow. These files are distinct from the portable rehearsals.
- `choice_nearest` and `choice_energy`: the same diagnostic layout under both
  policies. Both rovers can inspect the central blue marker, but different
  initial batteries lead to different ownership under the two ranking rules.

The diagnostic is intentionally constructed to exercise the ranking difference.
It is not evidence that the energy rule performs better. The initial rehearsal
shows a small time penalty for that rule in this particular diagnostic.

The default comparison cases produced identical policy outcomes in the current
offline model. Preserve that observation; do not present it as a demonstrated
energy advantage or as an actual Gazebo result.

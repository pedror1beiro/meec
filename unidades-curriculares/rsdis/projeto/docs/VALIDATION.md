# Validation record

This record separates portable checks from actual ROS/Gazebo execution.

## Navigation update, 30 October 2026

- 52 portable tests with OpenCV and Xacro, including sensor-only pole avoidance,
  scan loss/invalid data, swept-motion braking, bounded/radius-aware A*, opposing
  rover passing, pause/recall, generated-world geometry and the existing mission,
  perception, ownership, recovery and energy checks.
- The 80 x 60 m nominal rehearsal confirms all five sites and returns both rovers
  in 404.1 simulation seconds. Minimum conservative obstacle gap: 0.2917 m;
  footprint overlap samples: zero.
- Disabling rover1 at second 20 for 30 seconds completes the expanded mission in
  462.0 simulation seconds. Minimum conservative obstacle gap: 0.3003 m;
  footprint overlap samples: zero. The minimum peer footprint gap is 1.7728 m.
- The larger VIPER footprint profile also completes the kinematic rehearsal in
  402.2 simulation seconds, with zero overlaps and minimum obstacle gap 0.2810 m.
  This does not test VIPER wheel physics.
- The compact rehearsal completes in 104.2 simulation seconds.
- Ruff and byte compilation pass. Both real upstream URDFs still expand with
  29 links, 28 joints and 10 namespaced system plugins, plus the new range sensor.
- The console layout and follow-rover selector were inspected in a browser using
  explicitly labelled offline telemetry. Actual ROS service and image checks are
  included in the Linux integration gate.
- The updated IEEE draft remains two pages, with the team author block and no
  en/em dashes. Both pages were rendered and checked.

These rehearsal times and gaps use synthetic range endpoints, perfect target
detections and planar kinematics. They are regression evidence, not experimental
Gazebo comparisons. Existing examples from 29 October preserve the earlier map
and controller; expanded-map examples are identified separately.

The first Linux run of this update built both ROS packages and passed the actual
camera, laser, odometry, detection and task-assignment gate. The complete compact
mission and console controls remain under validation until their CI result is
recorded here. Comparative experiments, detailed-rover physics and Docker remain
pending.

## Historical baseline, 29 October 2026

## Executed

- Python byte compilation of project modules, scripts and tests.
- Ruff static checks and formatting checks on the project Python source/test files.
- 42 local unit/integration tests with OpenCV and Xacro installed, all passing.
- Five-colour synthetic image detection, cropped/tiny-blob rejection, range
  calculation and camera-to-world projection checks. A coloured square-panel
  regression prevents a simple rectangle from passing as a spherical marker.
- Ownership, duplicate handling, stale status, leases, battery feasibility,
  ranking differences, task reassignment and return/recharge checks.
- A* detour regression near a marker, including a rounded-grid start-cell case.
- Default nominal rehearsal: five markers confirmed; both rovers returned.
- Failure rehearsal: rover1 disabled at simulation second 20 for 30 seconds;
  its green-target task released, reassigned to rover2 and completed.
- Forty offline rehearsals over five fixed layouts, four conditions and both
  policies. All reached five confirmations and returned both rovers. These
  cases produced identical policy outcomes in this offline model.
- An additional constructed allocation-choice diagnostic under both policies.
  Both succeeded, with different initial ownership of the central blue target.
  The energy policy took 88.5 s versus 85.5 s for nearest in this diagnostic;
  this is an offline illustration, not evidence of improved performance.
- Shell syntax checks for Ubuntu setup, launch helper and experiment batch script.
- Both upstream repositories fetched and exact Git revisions verified against
  `upstream.lock.json`; lunar rover and Mons Mouton LFS assets downloaded.
- Real upstream Xacro expanded; two detailed rover URDFs prepared with 29 links,
  28 joints and 10 namespaced stock Gazebo plugins each. Mesh references resolve.
- Four-wheel steering checked for straight, reverse, in-place and mixed motion;
  stale/missing feedback interlocks stop wheel rotation.
- The detailed model's larger stand-off/clearance profile completes the portable
  mission rehearsal. This is still kinematic logic validation, not wheel physics.
- Code fingerprints change with source edits and remain stable across Windows
  versus Linux line endings; generated results are excluded from the fingerprint.
- IEEE draft compiled with local MiKTeX into two pages. Both pages rendered and
  reviewed; no unresolved references, font substitutions or overfull boxes in
  the final compilation. The editor's built-in compiler was unavailable.
- Portable HTML playback opened in a browser; timeline and status display checked.
- Transfer archive checksums verified. Extracted the archive into a separate
  directory and reran its offline mission and portable tests successfully. The
  actual-upstream expansion test requires a fetched checkout and is skipped in
  a source-only transfer until the upstream download step is run.

Local image tests used Python 3.13.13, NumPy 2.5.4 and OpenCV 4.14.0. The target ROS
environment uses its compatible Ubuntu/ROS packages instead of this Windows venv.

## Still pending

- ROS 2 interface generation and package compilation on Ubuntu/Jazzy.
- Actual Gazebo plugin loading, wheel contact, steering and rendered camera streams.
- CameraInfo topic delivery, detection from rendered images and timestamp pairing.
- Full mission and failure recovery using actual Gazebo physics and ROS messages.
- RViz monitoring, Docker build/run and the supplied Linux CI workflow.
- Runtime validation of the prepared detailed rover adapter; detailed terrain and
  physical solar/battery plugin integration.
- Measured Gazebo comparisons, final paper results, demonstration video and final slides.

The Linux smoke test deliberately requires real image and odometry messages and
cannot pass by using the offline oracle. The prepared protocol and deliverable
drafts do not imply that all final academic deliverables are complete.

## Reproduce local checks

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
python scripts/compare_offline.py --scenarios experiments/generated
```

The small matrix export is `examples/offline_matrix.csv`. The labelled nominal,
failure and policy-choice playbacks are under `examples/`. Raw authoring-session
debug runs remain under `results/` and are excluded from the transfer archive.

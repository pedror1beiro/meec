# Validation record

Checked on 29 October 2026 on the Windows authoring PC. This record separates
what was executed locally from what still needs the target Linux environment.

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

# Experiment protocol

Question: does including remaining battery in target allocation improve mission
completion and safe return compared with distance-only allocation?

## Hypotheses and fair comparisons

The energy heuristic may help under asymmetric energy and failures, but may also
send a rover farther or delay inspections. Equal results in a short easy mission
are plausible. Do not change layouts, budgets or scoring weights after inspecting
outcomes to obtain a preferred result. Record any exploratory tuning separately.

Both strategies use the same target perception, safety reserve, return check,
navigation, retry rules and failure intervention. Only the ranking score changes.
Nearest allocation must not be deliberately deprived of return safeguards.

## Predefined scenarios

Generate the configurations once, before the comparison:

```bash
python3 scripts/create_scenarios.py --count 5
```

This writes five deterministic target layouts, each with four conditions:
nominal, asymmetric energy with increased travel cost, temporary rover1 failure,
and combined energy/failure. The same configuration file is used for both policies.
Layout seeds vary target positions by at most 0.6 m; they do not imply stochastic
sensor noise or independent noise samples. Targets still need to be placed safely
when moving to an uneven detailed terrain model.

## First actual run

After the smoke test passes, source the workspace and launch one supervised run:

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
python3 scripts/run_experiment_ros.py \
  --config experiments/generated/failure_00.json --strategy energy --gui
```

The supervisor injects a configured failure using **simulation time**, not the
speed at which the host computer happens to render. It captures launch logs,
intervention times, source SHA-256 fingerprint, ROS/OpenCV package versions and
the manager's results. The fingerprint excludes generated results and normalizes
Windows/Linux line endings. Runs have a wall-time timeout to catch hangs; the
`--wall-timeout` default is 1800 seconds.

Once a single run has been reviewed, the full matrix is:

```bash
bash scripts/run_experiments.sh
```

After the separate detailed-rover smoke test passes, the same matrix can be run
with `bash scripts/run_experiments.sh experiments/generated viper`. Treat model
profiles as separate experimental conditions. The exporter records the active
`model_profile`; do not pool detailed-rover and lightweight results as one trial.

Five layouts x four conditions x two policies gives 40 runs. A single deterministic
run is useful for debugging but is not enough to justify a broad statistical claim.
Consider counterbalancing the policy order for thermal/load effects on the host;
the supplied batch script runs nearest then energy in each pair.

## Outputs and metrics

Each run stores the exact configuration, telemetry CSV, mission events JSONL and
summary JSON. Supervised runs additionally include launch logs and metadata.

- Primary: confirmed targets by the deadline and mission success, including return.
- Secondary: simulated completion time, path length and synthetic energy consumed.
- Recovery: failure time to reassignment, and failure time to completion of the
  released target; identify the affected target and task IDs in the event trace.
- Cooperation: detections whose observing rover differs from the assigned rover;
  `summarize_results.py` counts cross-rover assignments.
- Perception: compare estimated marker locations against the scenario truth in a
  separate detector evaluation; do not feed that truth into the controller.

```bash
python3 scripts/summarize_results.py
```

The exporter excludes offline rehearsals by default. Retain all failed/time-limited
runs, including how many targets were completed before the deadline. Report time
alongside success rate; averaging only successful runs can make a poor strategy
look fast. Use paired differences by layout, show individual runs, and avoid
statistical significance claims from an inadequately sized dataset.

## Required demonstration evidence

The trace should contain a target discovered by one rover and assigned to another,
a released/reassigned task after failure, an energy-driven decision and successful
return. The default nominal configuration does not guarantee all these events;
use the failure/energy conditions and confirm the actual event records before
recording the video. Do not label a planned event as observed.

Offline rehearsals are labelled `offline_kinematic_oracle_detection`. They are
valuable for verifying task logic but must remain separate from Gazebo results
and from measurements of rendered-camera detection performance.

## Allocation-choice diagnostic

`experiments/diagnostic/energy_choice.json` places two idle rovers at similar
distances from the central blue marker with different battery levels. This
constructed case exercises a different ownership decision under the two scores.
It is exploratory demonstration material, separate from the fixed matrix above.
Its offline example does not show a performance improvement for the energy rule.
Retain that distinction when presenting the example or selecting future experiments.

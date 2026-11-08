# Frozen paired Gazebo batch, 8 November 2026

Actual ROS 2 Jazzy / Gazebo Harmonic runs with native energy and rendered
cameras. Runtime: 6223585b59fb46ba7cdc5a7f3a7fbd59053e06ba.
Workflow: https://github.com/pedror1beiro/meec/actions/runs/42505786863

The eight configurations in `experiments/submission_20261108/` were frozen
before outcomes. Both policies use each configuration, producing 16 runs.
All outcomes are included. No layout, scoring weight or failure time was changed
after inspecting the batch. The two seeds jitter target xy by +/-0.2 m and do
not represent repeated independent sensor-noise trials.

`comparison.csv` contains each individual outcome, native discharge/solar/dock
Wh, distance, simulation time, conservative clearance, channel counters and
detector RMSE. `analysis_summary.json` contains arithmetic descriptive summaries.
Run paths in the CSV are relative to this folder. Original run metadata keeps
the Linux execution paths and source fingerprint for provenance.

Regenerate the analysis from retained raw files with:

```bash
python3 scripts/collect_submission_results.py --root examples/paired_gazebo_20261108
python3 report/summarize_evaluation.py examples/paired_gazebo_20261108/comparison.csv --output results/recomputed_summary.json
```

Create the `results` directory if needed. The collector rejects mixed runtime
fingerprints and duplicate pairs. Large launch debug logs remain available in
the linked workflow artifacts. The retained events, telemetry, electrical CSV,
network report, configurations and observer errors permit independent checks.

Power integrals use a clipped right-rectangle rule on telemetry, capping an
unobserved gap at one second. Charging input is recorded separately from discharge.
RMSE uses delivered high-confidence observations with correlated repeated frames;
it is not an independent-noise confidence interval. Gateway loss/delay is imposed
above ROS, not a measurement of DDS or lunar radio. Contact audits are planar
geometry, not contact forces. The expanded failure recording is a separate case.

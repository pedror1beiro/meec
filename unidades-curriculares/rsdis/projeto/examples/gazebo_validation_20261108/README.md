# Actual Gazebo validation, 8 November 2026

These are actual ROS 2 Jazzy / Gazebo Harmonic observations, not offline oracle
rehearsals. Read the run metadata and configuration before comparing numbers.

| Folder | Runtime | Workflow | Scope |
| --- | --- | --- | --- |
| native_6351d85 | 6351d85 | https://github.com/pedror1beiro/meec/actions/runs/42502766396 | Native energy bench, compact mission, expanded map with rover failure |
| viper_6223585 | 6223585 | https://github.com/pedror1beiro/meec/actions/runs/42506366909 | Detailed rover physical motion and native-energy compact mission |

Native 6351 summaries retain the historical field name `synthetic_energy_used`.
This field is cumulative discharged capacity fractions, not Wh. Metadata and
per-rover electrical CSV identify the actual Gazebo energy source. Runtime
6223585 corrects the label. Neither this functional dataset nor the historical
October checks is a matched allocation-policy comparison.

Logs are retained in the linked workflow artifacts. This folder keeps configuration,
metrics, events, power traces, reports and camera images without duplicating large
debug logs. Ground-truth observer clearance is conservative planar geometry,
not a contact-force measurement.

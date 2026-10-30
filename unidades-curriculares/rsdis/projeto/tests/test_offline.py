import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from offline_demo import load_config, rehearse


class MissionRehearsalTests(unittest.TestCase):
    def test_nominal_mission_confirms_targets_and_returns_both_rovers(self):
        config = load_config(ROOT / "src/rsdis_lunar/config/mission.json")
        with tempfile.TemporaryDirectory() as temp:
            summary, path = rehearse(config, output=Path(temp) / "nominal")
            self.assertEqual(summary["reason"], "all_targets_confirmed_and_returned")
            self.assertEqual(summary["targets_confirmed"], 5)
            self.assertEqual(summary["clearance_audit"]["footprint_overlap_samples"], 0)
            self.assertGreater(summary["clearance_audit"]["minimum_obstacle_gap_m"], 0.2)
            self.assertTrue(all(r["mode"] == "parked" for r in summary["rovers"].values()))
            trace = json.loads((path / "trace.json").read_text())
            self.assertTrue(all(r["mode"] == "parked" for r in trace[-1]["rovers"]))
            self.assertIn(
                "Offline kinematic rehearsal", (path / "playback.html").read_text(encoding="utf-8")
            )

    def test_failed_rover_task_is_reassigned_to_teammate(self):
        config = load_config(ROOT / "src/rsdis_lunar/config/mission.json")
        with tempfile.TemporaryDirectory() as temp:
            summary, path = rehearse(
                config, failure_at=20, failure_duration=30, output=Path(temp) / "failure"
            )
            events = [json.loads(line) for line in (path / "events.jsonl").read_text().splitlines()]
            released = [e for e in events if e["event"] == "released" and e["rover"] == "rover1"]
            self.assertTrue(released)
            target = released[0]["target"]
            self.assertTrue(
                any(
                    e["event"] == "assigned" and e["target"] == target and e["rover"] == "rover2"
                    for e in events
                )
            )
            self.assertEqual(summary["reason"], "all_targets_confirmed_and_returned")


if __name__ == "__main__":
    unittest.main()

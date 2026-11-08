from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.communications import LinkEmulator, link_config
from rsdis_lunar.common import load_config
from rsdis_lunar.core import Coordinator, Snapshot


class CommunicationTests(unittest.TestCase):
    def model(self, **kwargs):
        config = load_config(ROOT / "src/rsdis_lunar/config/mission_small.json")
        config["network"] = kwargs
        return LinkEmulator(link_config(config))

    def test_outage_loses_heartbeats_and_retries_result_on_reconnection(self):
        link = self.model(blackouts=[dict(rover="rover1", start=2, end=5)])
        link.submit("status", "rover1", "heartbeat", 3)
        link.submit("results", "rover1", "completion", 3, reliable=True, ttl=8, key="task-1")
        self.assertEqual(link.poll(3), [])
        self.assertEqual(link.poll(4), [])
        delivered = link.poll(5)
        self.assertEqual([p.payload for p in delivered], ["completion"])
        self.assertEqual(link.poll(6), [])
        self.assertGreater(link.report(6)["streams"]["rover1/results"]["retries"], 0)

    def test_delayed_goal_expires_before_rover_can_act_on_it(self):
        link = self.model(delay=3)
        link.submit("goals", "rover1", "obsolete", 0, reliable=True, ttl=2)
        self.assertEqual(link.poll(3), [])
        self.assertEqual(link.report(3)["streams"]["rover1/goals"]["expired"], 1)

    def test_reordered_status_cannot_replace_newer_pose_or_heartbeat(self):
        config = load_config(ROOT / "src/rsdis_lunar/config/mission_small.json")
        coordinator = Coordinator(config)
        coordinator.update(Snapshot("rover1", (1, 2, 0), 0.8, "idle", 10))
        coordinator.update(Snapshot("rover1", (99, 99, 0), 0.1, "idle", 5))
        self.assertEqual(coordinator.rovers["rover1"].pose, (1, 2, 0))

    def test_seeded_loss_is_repeatable_and_streams_are_independent(self):
        def run(extra):
            model = self.model(seed=7, loss=0.3, delay=0.1, jitter=0.05)
            for i in range(100):
                model.submit("status", "rover1", i, i * 0.2)
                if extra:
                    model.submit("status", "rover2", i, i * 0.2)
            result = [p.payload for p in model.poll(20) if p.rover == "rover1"]
            return result

        self.assertEqual(run(False), run(True))

    def test_queue_is_bounded_and_latest_renewal_replaces_older_one(self):
        link = self.model(delay=0.1)
        link.submit("goals", "rover1", "old", 0, reliable=True, key="same")
        link.submit("goals", "rover1", "renewed", 0.05, reliable=True, key="same")
        self.assertEqual([p.payload for p in link.poll(0.2)], ["renewed"])
        for i in range(1000):
            link.submit("status", "rover1", i, 1)
        self.assertLessEqual(len(link.pending), 512)


if __name__ == "__main__":
    unittest.main()

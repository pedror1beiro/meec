import copy
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.core import Coordinator, Goal, Rover, Snapshot, wrap


def configuration():
    return load_config(ROOT / "src/rsdis_lunar/config/mission_small.json")


class CoordinationTests(unittest.TestCase):
    def setUp(self):
        self.config = configuration()
        self.c = Coordinator(self.config, "nearest")
        self.c.update(Snapshot("rover1", (0, 0, 0), 0.95, "exploring", 0))
        self.c.update(Snapshot("rover2", (5, 0, 0), 0.95, "exploring", 0))
        self.c.observe("red", (2, 0), "rover1", 0)

    def test_one_owner_and_renewal_is_not_new_task(self):
        first = self.c.tick(0)
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0].rover_id, "rover1")
        self.assertEqual(self.c.tick(0.5)[0].task_id, first[0].task_id)
        self.assertEqual(self.c.targets["red"].attempts, 1)

    def test_duplicate_detection_and_duplicate_result(self):
        self.c.observe("red", (2.1, 0), "rover2", 0)
        self.assertEqual(len(self.c.targets), 1)
        goal = self.c.tick(0)[0]
        self.assertTrue(self.c.result(goal.rover_id, goal.task_id, True, 1))
        self.assertFalse(self.c.result(goal.rover_id, goal.task_id, True, 1))
        self.assertEqual(self.c.tick(1), [])

    def test_wrong_rover_cannot_confirm(self):
        goal = self.c.tick(0)[0]
        self.assertFalse(self.c.result("rover2", goal.task_id, True, 1))
        self.assertFalse(self.c.targets["red"].confirmed)

    def test_infeasible_low_battery_rover_is_rejected(self):
        self.c.rovers["rover1"].battery = 0.16
        self.assertEqual(self.c.tick(0)[0].rover_id, "rover2")

    def test_energy_policy_can_choose_further_rover(self):
        self.c.rovers["rover1"].battery = 0.35
        self.c.rovers["rover2"].pose = (4.3, 0, 0)
        self.assertEqual(self.c.tick(0)[0].rover_id, "rover1")
        c = Coordinator(self.config, "energy")
        c.rovers = self.c.rovers
        c.observe("red", (2, 0), "rover1", 0)
        self.assertEqual(c.tick(0)[0].rover_id, "rover2")

    def test_stale_status_releases_and_late_result_is_ignored(self):
        goal = self.c.tick(0)[0]
        self.assertEqual(self.c.tick(4), [])
        self.assertEqual(self.c.targets["red"].owner, "")
        self.assertFalse(self.c.result(goal.rover_id, goal.task_id, True, 4))
        self.c.update(Snapshot("rover2", (5, 0, 0), 0.95, "exploring", 10))
        new = self.c.tick(10)[0]
        self.assertEqual(new.rover_id, "rover2")
        self.assertNotEqual(new.task_id, goal.task_id)

    def test_failure_reattributes_task(self):
        self.c.tick(0)
        self.c.rovers["rover1"].mode = "unavailable"
        self.c.tick(1)
        self.c.rovers["rover2"].seen_at = 6
        self.assertEqual(self.c.tick(6)[0].rover_id, "rover2")

    def test_no_repeated_assignment_after_three_failed_attempts(self):
        for now in (0, 10, 20):
            for r in self.c.rovers.values():
                r.seen_at = now
            g = self.c.tick(now)[0]
            self.c.result(g.rover_id, g.task_id, False, now)
        for r in self.c.rovers.values():
            r.seen_at = 30
        self.assertEqual(self.c.tick(30), [])


class RoverTests(unittest.TestCase):
    def setUp(self):
        self.config = configuration()
        self.spec = copy.deepcopy(self.config["rovers"][0])
        self.spec["spawn"] = [0, 0, 0]
        self.r = Rover(self.spec, self.config)
        self.g = Goal("red-1", "red", (2, 0), "rover1")

    def test_inspection_requires_recent_visual_confirmation(self):
        self.r.assign(self.g, 0)
        for i in range(25):
            now = i / 10
            self.r.assign(self.g, now)
            self.r.step((0.8, 0, 0), 0.1, now)
        self.assertEqual(self.r.results, [])
        for i in range(25, 50):
            now = i / 10
            self.r.assign(self.g, now)
            self.r.seen("red", now)
            self.r.step((0.8, 0, 0), 0.1, now)
        self.assertEqual(len(self.r.results), 1)
        self.assertTrue(self.r.results[0][2])
        self.r.assign(self.g, 6)
        self.assertIsNone(self.r.goal)

    def test_lease_expiry_returns_failure(self):
        self.r.assign(self.g, 0)
        self.r.step((0, 0, 0), 0.1, 3)
        self.assertIsNone(self.r.goal)
        self.assertEqual(self.r.results[0][3], "lease_expired")

    def test_unavailable_stops_and_releases(self):
        self.r.assign(self.g, 0)
        self.r.enabled = False
        self.assertEqual(self.r.step((0, 0, 0), 0.1, 0.1), (0, 0))
        self.assertEqual(self.r.mode, "unavailable")
        self.assertFalse(self.r.results[0][2])

    def test_low_energy_returns_home_and_recharges(self):
        self.r.assign(self.g, 0)
        self.r.battery = 0.17
        self.r.pose = (5, 0, math.pi)
        self.r.step((5, 0, math.pi), 0.1, 0.1)
        self.assertEqual(self.r.mode, "returning")
        self.assertEqual(self.r.results[0][3], "energy_return")
        self.r.pose = (0, 0, 0)
        self.r.step((0, 0, 0), 1, 1)
        self.assertEqual(self.r.mode, "charging")
        self.assertGreater(self.r.battery, 0.17)

    def test_measured_distance_consumes_energy(self):
        battery = self.r.battery
        self.r.step((1, 0, 0), 1, 1)
        self.assertAlmostEqual(self.r.travelled, 1)
        self.assertAlmostEqual(battery - self.r.battery, 0.0061)
        self.assertAlmostEqual(self.r.energy_used, 0.0061)

    def test_heading_wrap(self):
        self.assertAlmostEqual(wrap(3 * math.pi), math.pi)


if __name__ == "__main__":
    unittest.main()

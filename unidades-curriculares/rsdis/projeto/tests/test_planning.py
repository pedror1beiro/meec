from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.planning import next_waypoint, segment_clear


class PlanningTests(unittest.TestCase):
    def test_clear_route_returns_goal(self):
        self.assertEqual(next_waypoint((0, 0), (5, 0), []), (5, 0))

    def test_marker_blocks_straight_route_and_detour_is_clear(self):
        obstacles = [(2, 0)]
        self.assertFalse(segment_clear((0, 0), (5, 0), obstacles))
        waypoint = next_waypoint((0, 0), (5, 0), obstacles)
        self.assertIsNotNone(waypoint)
        self.assertNotEqual(waypoint, (5, 0))
        self.assertTrue(segment_clear((0, 0), waypoint, obstacles))

    def test_start_near_marker_does_not_round_into_dead_end(self):
        start = (-2.71, -3.16)
        obstacles = [(-2, -2.5), (3, -2.5), (-1, 2.5), (4, 2.5)]
        waypoint = next_waypoint(start, (1.76, -2.64), obstacles)
        self.assertIsNotNone(waypoint)
        self.assertTrue(segment_clear(start, waypoint, obstacles))


if __name__ == "__main__":
    unittest.main()

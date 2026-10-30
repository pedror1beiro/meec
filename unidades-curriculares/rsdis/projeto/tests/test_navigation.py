import copy
import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.core import Goal, Rover, Snapshot
from rsdis_lunar.navigation import Navigator, advance, safe_velocity, scan_points
from rsdis_lunar.planning import in_bounds, plan_path, segment_clear
from rsdis_lunar.safety_audit import simulated_scan


class NavigationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / "src/rsdis_lunar/config/mission_small.json")

    def test_laser_projection_uses_extrinsic_and_rover_heading(self):
        points, valid = scan_points(
            [2, math.inf, math.nan], 0, math.pi / 2, 0.06, 12, (3, 4, math.pi / 2), 0.62
        )
        self.assertFalse(valid)
        self.assertAlmostEqual(points[0][0], 3)
        self.assertAlmostEqual(points[0][1], 6.62)
        self.assertTrue(scan_points([math.inf] * 3, -1, 1, 0.06, 12, (0, 0, 0), 0.62)[1])
        self.assertFalse(scan_points([0], 0, 1, 0.06, 12, (0, 0, 0), 0.62)[1])

    def test_lost_or_invalid_laser_stops_translation_and_rotation(self):
        nav = Navigator(self.config)
        nav.require_scan = True
        nav.update_scan([], 0)
        self.assertNotEqual(nav.command((0, 0, 0), (5, 0), [], [], 0.1), (0, 0))
        self.assertEqual(nav.command((0, 0, 0), (5, 0), [], [], 0.7), (0, 0))
        self.assertEqual(nav.state, "waiting_for_scan")
        nav.update_scan([], 1, valid=False)
        self.assertEqual(nav.guard((0, 0, 0), (0, 0.5), [], 1), (0, 0))

    def test_command_brakes_before_an_unlabelled_pole(self):
        nav = Navigator(self.config)
        nav.require_scan = True
        # No marker detection or semantic obstacle has been supplied.
        nav.update_scan([(1.1, 0, 0.08)], 0)
        self.assertEqual(nav.guard((0, 0, 0), (0.45, 0), [], 0.1), (0, 0))

    def test_curved_motion_and_map_edge_are_checked(self):
        bounds = (-10, 10, -10, 10)
        self.assertEqual(safe_velocity((0, 0, 0), 0.45, 0.55, [(1.1, 0.3, 0.1)], 1, bounds), (0, 0))
        v, _ = safe_velocity((8.95, 0, 0), 0.45, 0, [], 1, bounds)
        self.assertLess(v, 0.45)

    def test_escape_cannot_cross_the_centre_of_a_disk(self):
        self.assertFalse(segment_clear((0.3, 0), (-2, 0), [(0, 0)], 1))
        self.assertTrue(segment_clear((0.3, 0), (2, 0), [(0, 0)], 1))

    def test_astar_uses_actual_radius_bounds_and_continuous_edges(self):
        hazards = [(0, 0, 3), (6, 3, 1)]
        bounds = (-15, 15, -10, 10)
        path = plan_path((-12, 0), (12, 0), hazards, clearance=1, bounds=bounds)
        self.assertIsNotNone(path)
        self.assertTrue(all(in_bounds(p, bounds, 1) for p in path))
        self.assertTrue(all(segment_clear(a, b, hazards, 1) for a, b in zip(path, path[1:])))
        self.assertIsNone(plan_path((-12, 0), (0, 0), hazards, bounds=bounds))
        self.assertIsNone(plan_path((-12, 0), (16, 0), hazards, bounds=bounds))

    def test_sensor_only_detour_passes_a_pole_without_a_colour_detection(self):
        config = copy.deepcopy(self.config)
        config["hazards"] = []
        config["targets"] = [dict(id="red", position=[2, 0])]
        nav = Navigator(config)
        nav.require_scan = True
        pose = (-3, 0, 0)
        minimum = math.inf
        for i in range(900):
            now = i * 0.1
            points = simulated_scan(pose, config, {"rover1": pose}, "rover1")
            nav.update_scan(points, now)
            v, w = nav.command(pose, (6, 0), [], [], now)
            pose = advance(pose, v, w, 0.1)
            minimum = min(minimum, math.dist(pose[:2], (2, 0)) - 0.25 - 0.72)
            if math.dist(pose[:2], (6, 0)) < 0.3:
                break
        self.assertLess(math.dist(pose[:2], (6, 0)), 0.3)
        self.assertGreater(minimum, 0.2)

    def test_pause_preserves_assignment_and_recall_cancels_it(self):
        rover = Rover(self.config["rovers"][0], self.config)
        goal = Goal("test-1", "red", (-2, -2.5), rover.id)
        rover.assign(goal, 0)
        rover.paused = True
        self.assertEqual(rover.step(rover.pose, 5, 5), (0, 0))
        self.assertIsNotNone(rover.goal)
        self.assertGreaterEqual(rover.lease_until, 7)
        rover.return_home()
        self.assertIsNone(rover.goal)
        self.assertTrue(rover.park)

    def test_opposing_rovers_pass_and_can_exchange_start_positions(self):
        config = copy.deepcopy(self.config)
        config["hazards"] = []
        for goals in ([(6, 0), (-6, 0)], [(4, 0), (-4, 0)]):
            poses = [(-4, 0, 0), (4, 0, math.pi)]
            nav = [Navigator(config), Navigator(config)]
            minimum = math.inf
            for i in range(1000):
                commands = []
                for j in range(2):
                    peer = Snapshot("rover" + str(2 - j), poses[1 - j], 1, "exploring", i * 0.1)
                    commands.append(
                        nav[j].command(poses[j], goals[j], [], [peer], i * 0.1)
                        if math.dist(poses[j][:2], goals[j]) > 0.25
                        else (0, 0)
                    )
                poses = [advance(p, *commands[j], 0.1) for j, p in enumerate(poses)]
                minimum = min(minimum, math.dist(poses[0][:2], poses[1][:2]) - 1.44)
                if all(math.dist(poses[j][:2], goals[j]) < 0.25 for j in range(2)):
                    break
            self.assertTrue(all(math.dist(poses[j][:2], goals[j]) < 0.25 for j in range(2)))
            self.assertGreater(minimum, 0.2)


if __name__ == "__main__":
    unittest.main()

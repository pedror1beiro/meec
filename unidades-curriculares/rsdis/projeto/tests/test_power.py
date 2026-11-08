import copy
import math
from pathlib import Path
import sys
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.core import Rover
from rsdis_lunar.power import dock_power, motion_load, power_bridges, power_config
from rsdis_lunar.world import build_world


class PowerIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / "src/rsdis_lunar/config/mission_small.json")
        self.power = power_config(self.config)

    def test_charge_is_only_delivered_while_stopped_at_own_pad(self):
        home = (-8, -3)
        self.assertGreater(dock_power(self.power, (*home, 0), home, 0, 0, "charging"), 0)
        for pose, speed, yaw, mode, enabled in [
            ((-7, -3, 0), 0, 0, "charging", True),
            ((*home, 0), 0.1, 0, "charging", True),
            ((*home, 0), 0, 0.1, "charging", True),
            ((*home, 0), 0, 0, "exploring", True),
            ((*home, 0), 0, 0, "charging", False),
        ]:
            self.assertEqual(dock_power(self.power, pose, home, speed, yaw, mode, enabled), 0)

    def test_external_soc_is_not_double_depleted_or_invented_at_home(self):
        rover = Rover(self.config["rovers"][0], self.config)
        rover.external_energy = True
        rover.returning = True
        initial = rover.battery
        rover.step(rover.pose, 2, 2)
        self.assertEqual(rover.battery, initial)
        self.assertEqual(rover.energy_used, 0)

    def test_native_plugins_and_ros_bridges_are_namespaced(self):
        self.config["energy_source"] = "gazebo"
        root = ET.fromstring(build_world(self.config))
        for spec in self.config["rovers"]:
            model = root.find("world/model[@name='" + spec["id"] + "']")
            battery = model.find("plugin[@name='simulation::RechargeableBatteryPlugin']")
            self.assertAlmostEqual(
                float(battery.findtext("initial_charge")),
                spec["battery"] * self.power["capacity_ah"],
            )
            self.assertIsNotNone(model.find("link[@name='solar_panel_link']"))
            bridges, remaps = power_bridges(spec["id"], "solar_panel_link")
            self.assertTrue(all(spec["id"] in item for item in bridges))
            self.assertIn(
                (
                    f"/model/{spec['id']}/battery/{spec['id']}_battery/state",
                    f"/{spec['id']}/battery",
                ),
                remaps,
            )

    def test_power_parameters_and_motion_consumption(self):
        self.assertGreater(motion_load(self.power, 0.4, 0.3), motion_load(self.power, 0, 0))
        for value in (-1, math.inf, math.nan):
            config = copy.deepcopy(self.config)
            config["power"] = {"capacity_ah": value}
            with self.assertRaises(ValueError):
                power_config(config)


if __name__ == "__main__":
    unittest.main()

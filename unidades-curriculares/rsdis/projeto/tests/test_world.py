import json
from pathlib import Path
import sys
import tempfile
import unittest
from xml.etree import ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.common import load_config
from rsdis_lunar.world import build_world


class WorldTests(unittest.TestCase):
    def setUp(self):
        self.config = load_config(ROOT / "src/rsdis_lunar/config/mission.json")
        self.world = ET.fromstring(build_world(self.config)).find("world")

    def test_rovers_have_independent_command_odometry_and_camera_topics(self):
        for rover in self.config["rovers"]:
            name = rover["id"]
            model = self.world.find(f"model[@name='{name}']")
            plugins = {p.attrib["name"].split("::")[-1]: p for p in model.findall("plugin")}
            self.assertEqual(plugins["DiffDrive"].findtext("topic"), f"/{name}/cmd_vel")
            self.assertEqual(plugins["OdometryPublisher"].findtext("odom_topic"), f"/{name}/odom")
            self.assertEqual(plugins["OdometryPublisher"].findtext("odom_frame"), "world")
            camera = model.find("link/sensor")
            self.assertEqual(camera.findtext("topic"), f"/{name}/camera/image")
            self.assertEqual(camera.findtext("camera/camera_info_topic"), f"/{name}/camera/info")
            self.assertEqual(len(model.findall("joint")), 4)
            lidar = model.find("link/sensor[@type='gpu_lidar']")
            self.assertEqual(lidar.findtext("topic"), f"/{name}/scan")
            self.assertEqual(lidar.findtext("lidar/scan/horizontal/samples"), "721")

    def test_no_downloads_required_and_lunar_gravity(self):
        self.assertFalse(self.world.findall(".//uri"))
        self.assertEqual(self.world.findtext("gravity"), "0 0 -1.62")
        self.assertEqual(
            len([m for m in self.world.findall("model") if m.attrib["name"].startswith("target_")]),
            5,
        )

    def test_duplicate_rover_id_is_rejected(self):
        self.config["rovers"][1]["id"] = self.config["rovers"][0]["id"]
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.json"
            path.write_text(json.dumps(self.config), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_large_world_and_hazards_match_the_config(self):
        self.assertEqual(
            self.world.findtext("model[@name='regolith']/link/collision/geometry/box/size"),
            "80.0 60.0 0.2",
        )
        for hazard in self.config["hazards"]:
            self.assertIsNotNone(self.world.find(f"model[@name='{hazard['id']}']"))

    def test_non_finite_coordinates_are_rejected(self):
        self.config["rovers"][0]["spawn"][0] = float("nan")
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.json"
            path.write_text(json.dumps(self.config), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)

    def test_heartbeat_timeout_must_outlast_task_lease(self):
        self.config["status_timeout"] = 0.5
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "invalid.json"
            path.write_text(json.dumps(self.config), encoding="utf-8")
            with self.assertRaises(ValueError):
                load_config(path)


if __name__ == "__main__":
    unittest.main()

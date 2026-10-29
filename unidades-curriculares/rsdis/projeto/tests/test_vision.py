import math
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
try:
    import cv2
    import numpy as np
    from rsdis_lunar.vision import detect, to_world

    HAS_CV = True
except ImportError:
    HAS_CV = False


@unittest.skipUnless(HAS_CV, "Install requirements-dev.txt for image tests")
class VisionTests(unittest.TestCase):
    def setUp(self):
        self.image = np.zeros((480, 640, 3), dtype=np.uint8)
        self.k = (400, 0, 320, 0, 400, 240, 0, 0, 1)

    def test_all_five_marker_colours_and_range(self):
        colours = {
            "red": (0, 0, 255),
            "green": (0, 255, 0),
            "blue": (255, 0, 0),
            "magenta": (255, 0, 255),
            "orange": (0, 90, 255),
        }
        for i, (name, colour) in enumerate(colours.items()):
            cv2.circle(self.image, (100 + i * 100, 240), 20, colour, -1)
        result = {item[0]: item for item in detect(self.image, self.k)}
        self.assertEqual(set(result), set(colours))
        self.assertAlmostEqual(result["red"][1], 400 * 0.5 / 41)
        self.assertGreater(result["red"][2], 0)  # Left side of image is +left.
        self.assertLess(result["orange"][2], 0)

    def test_cropped_blob_and_empty_image_rejected(self):
        self.assertEqual(detect(self.image, self.k), [])
        cv2.circle(self.image, (0, 240), 30, (0, 0, 255), -1)
        self.assertEqual(detect(self.image, self.k), [])

    def test_tiny_blob_and_non_circular_region_rejected(self):
        cv2.circle(self.image, (200, 240), 2, (0, 0, 255), -1)
        cv2.rectangle(self.image, (300, 200), (310, 300), (0, 255, 0), -1)
        self.assertEqual(detect(self.image, self.k), [])

    def test_rotated_world_projection_and_camera_offset(self):
        x, y = to_world(2, 1, (10, 20, math.pi / 2), 0.5)
        self.assertAlmostEqual(x, 9)
        self.assertAlmostEqual(y, 22.5)

    def test_square_panel_is_not_a_spherical_science_marker(self):
        cv2.rectangle(self.image, (250, 200), (310, 260), (255, 0, 0), -1)
        self.assertEqual(detect(self.image, self.k), [])


if __name__ == "__main__":
    unittest.main()

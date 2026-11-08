import csv
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from collect_submission_results import integrate_power


class ElectricalMeasurementTests(unittest.TestCase):
    def test_constant_current_has_correct_watt_hours_and_clipped_window(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / "rover1_power.csv").open("w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["time", "current_a", "voltage_v", "solar_w", "dock_w"]
                )
                writer.writeheader()
                for t in range(61):
                    writer.writerow(dict(time=t, current_a=-1, voltage_v=24, solar_w=6, dock_w=0))
            whole = integrate_power(root, 0, 60)
            self.assertAlmostEqual(whole["discharge_wh"], 0.4)
            self.assertAlmostEqual(whole["solar_wh"], 0.1)
            self.assertAlmostEqual(integrate_power(root, 20, 40)["discharge_wh"], 24 * 20 / 3600)

    def test_recharging_does_not_cancel_previously_discharged_energy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with (root / "rover1_power.csv").open("w", newline="") as f:
                writer = csv.DictWriter(
                    f, fieldnames=["time", "current_a", "voltage_v", "solar_w", "dock_w"]
                )
                writer.writeheader()
                for t in range(21):
                    writer.writerow(
                        dict(
                            time=t,
                            current_a=-1 if t <= 10 else 1,
                            voltage_v=24,
                            solar_w=0,
                            dock_w=0 if t <= 10 else 30,
                        )
                    )
            measurement = integrate_power(root, 0, 20)
            self.assertAlmostEqual(measurement["discharge_wh"], 24 * 10 / 3600)
            self.assertAlmostEqual(measurement["dock_wh"], 30 * 10 / 3600)


if __name__ == "__main__":
    unittest.main()

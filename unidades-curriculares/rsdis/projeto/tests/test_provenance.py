from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src/rsdis_lunar"))
from rsdis_lunar.provenance import source_fingerprint


class ProvenanceTests(unittest.TestCase):
    def test_code_change_changes_fingerprint_but_generated_results_do_not(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            file = root / "src/controller.py"
            file.write_bytes(b"value = 1\n")
            before = source_fingerprint(root)
            (root / "results").mkdir()
            (root / "results/log.csv").write_text("time,value\n1,2\n")
            self.assertEqual(before, source_fingerprint(root))
            file.write_bytes(b"value = 2\n")
            self.assertNotEqual(before, source_fingerprint(root))

    def test_windows_and_linux_line_endings_have_same_fingerprint(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "src").mkdir()
            file = root / "src/controller.py"
            file.write_bytes(b"x = 1\r\ny = 2\r\n")
            windows = source_fingerprint(root)
            file.write_bytes(b"x = 1\ny = 2\n")
            self.assertEqual(windows, source_fingerprint(root))


if __name__ == "__main__":
    unittest.main()

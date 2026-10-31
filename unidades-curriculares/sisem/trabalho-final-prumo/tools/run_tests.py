"""Host-only logic/renderer tests. Does not claim hardware validation."""

import os
import shutil
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FW = ROOT / "firmware/PRUMO"
CC = os.environ.get("CC", "gcc")
if not shutil.which(CC):
    raise SystemExit("Install a host C compiler (gcc), or set CC.")
out = ROOT / "tmp/tests"
out.mkdir(parents=True, exist_ok=True)
tests = {
    "level": (
        ["tests/test_level.c", "firmware/PRUMO/App/level.c", "firmware/PRUMO/App/format.c"],
        ["firmware/PRUMO/App"],
    ),
    "ui": (
        ["tests/test_ui.c", "firmware/PRUMO/UI/ui.c", "firmware/PRUMO/App/format.c"],
        [
            "tests/stubs",
            "firmware/PRUMO/UI",
            "firmware/PRUMO/Components",
            "firmware/PRUMO/Core/Inc",
            "firmware/PRUMO/App",
        ],
    ),
}
for name, (sources, includes) in tests.items():
    exe = out / (name + (".exe" if os.name == "nt" else ""))
    subprocess.run(
        [
            CC,
            "-std=c11",
            "-Wall",
            "-Wextra",
            "-Werror",
            *["-I" + p for p in includes],
            *sources,
            "-lm",
            "-o",
            str(exe),
        ],
        cwd=ROOT,
        check=True,
    )
    subprocess.run([str(exe)], cwd=ROOT, check=True)

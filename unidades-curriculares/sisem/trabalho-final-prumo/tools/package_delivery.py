"""Create a transfer archive without caches, toolchain or intermediate objects."""

import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "entrega"
OUT.mkdir(exist_ok=True)
archive = OUT / "PRUMO-linux.zip"
skip = {"tmp", "entrega", ".git", "__pycache__", ".venv", ".metadata"}
build_files = {"PRUMO.elf", "PRUMO.hex", "PRUMO.bin", "PRUMO.map", "build-report.json"}
with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
    for p in sorted(ROOT.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(ROOT)
        if any(part in skip for part in rel.parts):
            continue
        if ("Debug" in rel.parts or "Release" in rel.parts) and p.name not in build_files:
            continue
        if p.suffix in {".o", ".d", ".su", ".pyc", ".exe"}:
            continue
        z.write(p, "SISEM/" + rel.as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    assert "SISEM/firmware/PRUMO/.project" in z.namelist()
    assert "SISEM/firmware/PRUMO/.cproject" in z.namelist()
digest = hashlib.sha256(archive.read_bytes()).hexdigest()
(OUT / "PRUMO-linux.sha256").write_text(digest + "  PRUMO-linux.zip\n", encoding="ascii")
print(archive, archive.stat().st_size, "bytes", digest)

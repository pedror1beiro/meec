#!/usr/bin/env python3
"""Package source, fixed scenarios, draft paper and labelled examples for transfer."""

import argparse
import hashlib
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DIRECTORIES = (
    "src",
    "scripts",
    "tests",
    "docs",
    "experiments",
    "worlds",
    "report",
    "examples",
    ".github",
    "docker",
)
FILES = (
    "README.md",
    "LICENSE",
    "NOTICE",
    ".gitignore",
    ".gitattributes",
    ".dockerignore",
    "requirements-dev.txt",
    "pyproject.toml",
    "upstream.lock.json",
    "output/pdf/rsdis_paper_draft.pdf",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "output/rsdis_lunar_project.zip")
    args = parser.parse_args()
    files = {ROOT / p for p in FILES if (ROOT / p).is_file()}
    for directory in DIRECTORIES:
        folder = ROOT / directory
        if folder.exists():
            files.update(
                p
                for p in folder.rglob("*")
                if p.is_file()
                and not set(p.relative_to(ROOT).parts) & {"__pycache__", "build", ".git"}
                and p.suffix not in (".pyc", ".aux", ".log", ".out")
            )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".zip.tmp")
    manifest = []
    with zipfile.ZipFile(
        temporary, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9
    ) as archive:
        for path in sorted(files):
            relative = path.relative_to(ROOT).as_posix()
            data = path.read_bytes()
            if path.suffix == ".sh":
                data = data.replace(b"\r\n", b"\n")
            manifest.append(hashlib.sha256(data).hexdigest() + "  " + relative)
            info = zipfile.ZipInfo("RSDIS/" + relative)
            info.create_system = 3
            info.external_attr = (0o100755 if path.suffix == ".sh" else 0o100644) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
        archive.writestr("RSDIS/MANIFEST.sha256", "\n".join(manifest) + "\n")
    temporary.replace(args.output)
    digest = hashlib.sha256(args.output.read_bytes()).hexdigest()
    args.output.with_suffix(".zip.sha256").write_text(
        digest + "  " + args.output.name + "\n", encoding="ascii"
    )
    with zipfile.ZipFile(args.output) as archive:
        assert archive.testzip() is None
        for line in archive.read("RSDIS/MANIFEST.sha256").decode().splitlines():
            expected, name = line.split("  ", 1)
            assert hashlib.sha256(archive.read("RSDIS/" + name)).hexdigest() == expected
    print(f"Verified {len(files)} files in {args.output} ({args.output.stat().st_size:,} bytes)")
    print("SHA256: " + digest)


if __name__ == "__main__":
    main()

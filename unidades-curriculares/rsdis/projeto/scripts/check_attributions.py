#!/usr/bin/env python3
"""Verify retained upstream authorship and the exact adapted source manifest."""

import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "src/rsdis_energy_plugins"


def digest(path):
    return hashlib.sha256(path.read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--refresh-adapted",
        action="store_true",
        help="Explicitly update adapted checksums after reviewed source changes",
    )
    args = parser.parse_args()
    manifest_path = PACKAGE / "UPSTREAM.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    licence = (PACKAGE / "LICENSE").read_text()
    assert "Apache License" in licence and "Version 2.0" in licence
    for item in manifest["files"]:
        path = PACKAGE / "src" / item["filename"]
        text = path.read_text(encoding="utf-8")
        assert "Copyright (C)" in text and "Licensed under the Apache License" in text, path
        assert manifest["revision"] in item["source_url"]
        assert len(item["upstream_sha256"]) == 64
        if args.refresh_adapted:
            item["adapted_sha256"] = digest(path)
        else:
            assert digest(path) == item["adapted_sha256"], (
                f"Source changed; review and refresh adapted checksum: {path}"
            )
    if args.refresh_adapted:
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(
        f"Verified {len(manifest['files'])} upstream source files, immutable URLs, adapted hashes and Apache-2.0 notices"
    )


if __name__ == "__main__":
    main()

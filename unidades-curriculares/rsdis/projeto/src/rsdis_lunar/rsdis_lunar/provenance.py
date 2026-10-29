"""Record the code used by an experiment even before the first Git commit."""

import hashlib
from pathlib import Path


def source_fingerprint(root):
    root = Path(root)
    files = []
    for directory in ("src", "scripts"):
        files.extend(
            p
            for p in (root / directory).rglob("*")
            if p.is_file() and "__pycache__" not in p.parts and p.suffix != ".pyc"
        )
    for name in ("upstream.lock.json", "pyproject.toml"):
        if (root / name).is_file():
            files.append(root / name)
    digest = hashlib.sha256()
    for file in sorted(files):
        digest.update(file.relative_to(root).as_posix().encode("utf-8") + b"\0")
        digest.update(file.read_bytes().replace(b"\r\n", b"\n") + b"\0")
    return digest.hexdigest()

#!/usr/bin/env python3
"""Fetch pinned Space ROS sources; --assets also downloads selected Git LFS files."""

import argparse
import json
import os
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def run(*command, cwd=None, capture=False):
    env = {**os.environ, "GIT_LFS_SKIP_SMUDGE": "1", "GIT_TERMINAL_PROMPT": "0"}
    result = subprocess.run(
        command,
        cwd=cwd,
        env=env,
        check=True,
        text=True,
        stdout=subprocess.PIPE if capture else None,
    )
    return result.stdout.strip() if capture else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--assets", action="store_true", help="Download the lunar rover and Mons Mouton LFS assets"
    )
    parser.add_argument(
        "--list", action="store_true", help="Print pinned repositories without downloading"
    )
    args = parser.parse_args()
    manifest = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
    if args.list:
        for repo in manifest["repositories"]:
            print(repo["name"], repo["commit"], repo["url"])
        return
    run("git", "--version")
    if args.assets:
        run("git", "lfs", "version")
    parent = ROOT / "third_party"
    parent.mkdir(exist_ok=True)
    (parent / "COLCON_IGNORE").touch()
    for repo in manifest["repositories"]:
        target = parent / repo["name"]
        if target.resolve().parent != parent.resolve():
            raise ValueError("Repository path must stay inside third_party")
        if target.exists():
            if not (target / ".git").is_dir():
                raise RuntimeError(f"Refusing to overwrite existing directory: {target}")
            origin = run("git", "remote", "get-url", "origin", cwd=target, capture=True)
            head = run("git", "rev-parse", "HEAD", cwd=target, capture=True)
            if origin != repo["url"] or head != repo["commit"]:
                raise RuntimeError(
                    f"Existing checkout has a different origin or revision: {target}"
                )
        else:
            run("git", "init", str(target))
            run("git", "remote", "add", "origin", repo["url"], cwd=target)
            run(
                "git",
                "fetch",
                "--depth",
                "1",
                "--filter=blob:none",
                "origin",
                repo["commit"],
                cwd=target,
            )
            run("git", "checkout", "--detach", "FETCH_HEAD", cwd=target)
        if args.assets:
            run("git", "lfs", "pull", "--include=" + repo["lfs_include"], "--exclude=", cwd=target)
            # A successful git command must also have materialized the mesh data.
            if repo["name"] == "simulation":
                for relative in (
                    "models/lunar_pole_exploration_rover/meshes/body.dae",
                    "models/moon_mons_mouton/meshes/mons_mouton_textured_low.dae",
                ):
                    with (target / relative).open("rb") as f:
                        if f.read(80).startswith(b"version https://git-lfs.github.com/spec"):
                            raise RuntimeError(f"LFS pointer is still unresolved: {relative}")
        print(f"Ready: {repo['name']} at {repo['commit']}")
    print(
        "The lightweight prototype is self-contained; these assets support the optional detailed rover and original demo."
    )
    if not args.assets:
        print("To retrieve the large lunar models later, rerun with --assets.")


if __name__ == "__main__":
    main()

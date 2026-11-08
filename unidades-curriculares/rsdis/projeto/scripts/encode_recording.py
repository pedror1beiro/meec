#!/usr/bin/env python3
"""Encode after ROS shutdown so launch signal timeouts cannot truncate the video."""

import argparse
import json
from pathlib import Path
import shutil
import subprocess


def encode(directory):
    directory = Path(directory)
    path = directory / "video_metadata.json"
    if not path.is_file() or not shutil.which("ffmpeg"):
        return False
    metadata = json.loads(path.read_text())
    if metadata.get("frames", 0) < 20:
        return False
    raw = directory / "mission_raw.avi"
    final = directory / "mission.mp4"
    result = subprocess.run(
        [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(raw),
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(final),
        ],
        capture_output=True,
        text=True,
        timeout=180,
    )
    valid = result.returncode == 0 and final.is_file() and final.stat().st_size > 1000
    metadata["h264_exported"] = valid
    if valid:
        raw.unlink()
        duration = metadata["last_sim_time"] - metadata["first_sim_time"]
        metadata["observed_capture_hz"] = (metadata["frames"] - 1) / duration if duration > 0 else 0
    else:
        metadata["export_error"] = result.stderr[-2000:]
    path.write_text(json.dumps(metadata, indent=2))
    return valid


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(0 if encode(args.run) else 1)


if __name__ == "__main__":
    main()

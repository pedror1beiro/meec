#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$ROOT_DIR/install/setup.bash" ]]; then
  echo 'Build first with: bash scripts/setup_ubuntu.sh' >&2
  exit 1
fi
# The ROS setup scripts read unset variables, which `set -u` rejects.
set +u
source /opt/ros/jazzy/setup.bash
source "$ROOT_DIR/install/setup.bash"
set -u
cd "$ROOT_DIR"
exec ros2 launch rsdis_lunar prototype.launch.py "$@"

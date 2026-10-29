#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f /opt/ros/jazzy/setup.bash ]]; then
  echo 'Install ROS 2 Jazzy on Ubuntu 24.04 first:' >&2
  echo 'https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html' >&2
  exit 1
fi
sudo apt-get update
sudo apt-get install -y ros-jazzy-ros-gz ros-jazzy-cv-bridge python3-opencv python3-numpy \
  python3-colcon-common-extensions python3-rosdep python3-pytest
source /opt/ros/jazzy/setup.bash
if [[ ! -f /etc/ros/rosdep/sources.list.d/20-default.list ]]; then
  sudo rosdep init
fi
rosdep update
cd "$ROOT_DIR"
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy
colcon build --symlink-install
echo "Build complete. Run: source '$ROOT_DIR/install/setup.bash'"
echo 'Then: ros2 launch rsdis_lunar prototype.launch.py'

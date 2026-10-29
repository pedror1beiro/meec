#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "$ROOT_DIR/install/setup.bash"
cd "$ROOT_DIR"
CONFIG_DIR="${1:-experiments/generated}"
MODEL="${2:-lightweight}"
shopt -s nullglob
configs=("$CONFIG_DIR"/*.json)
if (( ${#configs[@]} == 0 )); then
  echo 'No configurations. First run: python3 scripts/create_scenarios.py' >&2
  exit 1
fi
for config in "${configs[@]}"; do
  for strategy in nearest energy; do
    # Keep unsuccessful trials in the dataset and continue to the matched run.
    python3 scripts/run_experiment_ros.py --config "$config" --strategy "$strategy" --model "$MODEL" || \
      echo "Run did not finish successfully: $config / $strategy; inspect its logs."
  done
done
python3 scripts/summarize_results.py

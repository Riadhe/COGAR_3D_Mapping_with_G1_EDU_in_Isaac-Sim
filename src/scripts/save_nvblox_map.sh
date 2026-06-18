#!/usr/bin/env bash
# Save the in-memory NVBlox map to a .ply deliverable.
# Run this in a SECOND terminal AFTER the bag has finished playing,
# while run_nvblox_simple_room.sh is still running (map lives in node memory).
#
# Usage:
#   ./src/scripts/save_nvblox_map.sh
#   OUT=maps/simple_room/nvblox_mesh_v2.ply ./src/scripts/save_nvblox_map.sh
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

OUT="${OUT:-$REPO_ROOT/maps/simple_room/nvblox_mesh.ply}"
mkdir -p "$(dirname "$OUT")"

source /opt/ros/humble/setup.bash

echo "[save] Writing NVBlox map -> $OUT"
ros2 service call /nvblox_node/save_ply nvblox_msgs/srv/FilePath \
  "{file_path: $OUT}"

if [ -s "$OUT" ]; then
  SZ=$(du -h "$OUT" | cut -f1)
  echo "[save] OK: $OUT ($SZ)"
else
  echo "[save] WARNING: file is empty or missing. Is nvblox_node still running?"
  echo "[save] An empty map usually means the TSDF never integrated (check disk/frames)."
fi

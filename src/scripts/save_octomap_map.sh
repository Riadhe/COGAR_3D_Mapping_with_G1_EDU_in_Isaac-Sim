#!/usr/bin/env bash
#
# save_octomap_map.sh
# Save the OctoMap occupancy octree (.bt) into maps/<scene>/octomap/.
# Run while run_octomap_*.sh is STILL RUNNING (saver reads the live map topic).
#
# NOTE: octomap_saver_node needs an ABSOLUTE path passed as a ROS param
# (it does not expand ~).
#
# Usage:
#   ./src/scripts/save_octomap_map.sh
#   SCENE=warehouse ./src/scripts/save_octomap_map.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SCENE="${SCENE:-simple_room}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/maps/$SCENE/octomap}"
OUT_FILE="$OUT_DIR/octomap_occupancy.bt"

set +u
source /opt/ros/humble/setup.bash
set -u

mkdir -p "$OUT_DIR"

# Resolve to an absolute path (octomap_saver won't expand ~ or relative paths).
OUT_FILE="$(realpath -m "$OUT_FILE")"

echo "[save-octomap] Scene: $SCENE"
echo "[save-octomap] Saving octree -> $OUT_FILE"

if ! ros2 topic list 2>/dev/null | grep -q "/octomap_binary"; then
  echo "[save-octomap] ERROR: /octomap_binary not found — is octomap_server running?" >&2
  exit 1
fi

ros2 run octomap_server octomap_saver_node --ros-args -p octomap_path:="$OUT_FILE"

if [[ -s "$OUT_FILE" ]]; then
  echo "[save-octomap] OK: $(ls -lh "$OUT_FILE" | awk '{print $5, $9}')"
else
  echo "[save-octomap] WARNING: file missing/empty. Map may not have been received."
fi

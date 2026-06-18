#!/usr/bin/env bash
# Replay a scene bag through OctoMap (MID-360 LiDAR occupancy octree).
# Usage:
#   ./src/scripts/run_octomap.sh
#   SCENE=warehouse ./src/scripts/run_octomap.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SCENE="${SCENE:-simple_room}"
BAG="${BAG:-$REPO_ROOT/bags/$SCENE}"
FRAME_ID="World"
RESOLUTION="${RESOLUTION:-0.03}"
MAX_RANGE="${MAX_RANGE:-8.0}"
CLOUD_TOPIC="/point_cloud"

set +u
if [[ -z "${ROS_DISTRO:-}" ]]; then source /opt/ros/humble/setup.bash; fi
set -u

if [[ ! -e "$BAG/metadata.yaml" ]]; then
  echo "ERROR: bag not found at $BAG" >&2; exit 1
fi

echo "[octomap] Scene: $SCENE   Bag: $BAG"
ros2 daemon stop  >/dev/null 2>&1 || true
ros2 daemon start >/dev/null 2>&1 || true

PIDS=()
cleanup() {
  echo ""; echo "[octomap] Shutting down..."
  for pid in "${PIDS[@]}"; do kill "$pid" >/dev/null 2>&1 || true; done
  wait >/dev/null 2>&1 || true
  echo "[octomap] Done."
}
trap cleanup EXIT INT TERM

echo "[octomap] Starting octomap_server (res=$RESOLUTION, max_range=$MAX_RANGE)..."
ros2 run octomap_server octomap_server_node --ros-args \
  -p frame_id:="$FRAME_ID" -p resolution:="$RESOLUTION" \
  -p sensor_model.max_range:="$MAX_RANGE" \
  -p sensor_model.hit:=0.7 -p sensor_model.miss:=0.4 \
  -p sensor_model.min:=0.12 -p sensor_model.max:=0.97 \
  -p filter_ground:=false \
  -p pointcloud_min_z:=-0.1 -p pointcloud_max_z:=3.0 \
  -p occupancy_min_z:=-0.1 -p occupancy_max_z:=3.0 \
  -p filter_speckles:=true \
  -r cloud_in:="$CLOUD_TOPIC" &
PIDS+=($!)

echo "[octomap] Launching RViz2 (Fixed Frame=$FRAME_ID, add /occupied_cells_vis_array)..."
ros2 run rviz2 rviz2 &
PIDS+=($!)
sleep 3

echo "[octomap] Playing bag: $BAG"
ros2 bag play "$BAG"

echo ""
echo "[octomap] Bag finished; server + RViz still running."
echo "[octomap] Save: SCENE=$SCENE ./src/scripts/save_octomap_map.sh   then Ctrl-C."
wait "${PIDS[0]}"

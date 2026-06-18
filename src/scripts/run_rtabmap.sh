#!/usr/bin/env bash
# Replay a scene bag through RTAB-Map RGB-D SLAM.
# Usage:
#   ./src/scripts/run_rtabmap.sh
#   SCENE=warehouse ./src/scripts/run_rtabmap.sh
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SCENE="${SCENE:-simple_room}"
BAG="${BAG:-$REPO_ROOT/bags/$SCENE}"
FRAME_ID="d435_link"
RGB_TOPIC="/camera/color/image_raw"
DEPTH_TOPIC="/camera/depth/image_raw"
INFO_TOPIC="/camera/color/camera_info"
BAG_TOPICS=(
  /camera/color/image_raw /camera/depth/image_raw
  /camera/color/camera_info /camera/depth/camera_info
  /tf /tf_static
)
READINESS_TIMEOUT=30

set +u
source /opt/ros/humble/setup.bash
set -u

echo "[rtabmap] Scene: $SCENE   Bag: $BAG"
pkill -f rtabmap_node 2>/dev/null; pkill -f rtabmapviz 2>/dev/null
pkill -f "ros2 bag play" 2>/dev/null
sleep 1
ros2 daemon stop >/dev/null 2>&1; sleep 1
ros2 daemon start >/dev/null 2>&1; sleep 1

PIDS=()
cleanup() {
  echo ""; echo "[rtabmap] Shutting down..."
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null; done
  pkill -f rtabmap_node 2>/dev/null; pkill -f rtabmapviz 2>/dev/null
  pkill -f "ros2 bag play" 2>/dev/null
  echo "[rtabmap] Done. DB at ~/.ros/rtabmap.db"
  exit 0
}
trap cleanup INT TERM

if [ ! -e "$BAG/metadata.yaml" ]; then
  echo "[rtabmap] ERROR: bag not found at $BAG"; exit 1
fi

echo "[rtabmap] Launching RTAB-Map (fresh database)..."
ros2 launch rtabmap_launch rtabmap.launch.py \
  rgb_topic:="$RGB_TOPIC" depth_topic:="$DEPTH_TOPIC" \
  camera_info_topic:="$INFO_TOPIC" frame_id:="$FRAME_ID" \
  use_sim_time:=true approx_sync:=true approx_sync_max_interval:=0.04 \
  topic_queue_size:=30 sync_queue_size:=30 delete_db_on_start:=true \
  rtabmap_args:="--Grid/3D true --Grid/FromDepth true" rviz:=true &
PIDS+=($!)

echo "[rtabmap] Waiting for subscriber on $RGB_TOPIC (max ${READINESS_TIMEOUT}s)..."
elapsed=0
until ros2 topic info "$RGB_TOPIC" 2>/dev/null | grep -q "Subscription count: [1-9]"; do
  sleep 1; elapsed=$((elapsed+1))
  [ "$elapsed" -ge "$READINESS_TIMEOUT" ] && { echo "[rtabmap] WARN: no subscriber; playing anyway."; break; }
done
echo "[rtabmap] Ready (${elapsed}s). Playing bag."

ros2 bag play "$BAG" --clock --topics "${BAG_TOPICS[@]}" &
PIDS+=($!)

echo "[rtabmap] When bag finishes: SCENE=$SCENE ./src/scripts/save_rtabmap_map.sh (keep this running)."
wait "${PIDS[-1]}"
echo "[rtabmap] Bag finished; RTAB-Map still running. Save, then Ctrl-C."
while true; do sleep 3600; done

#!/usr/bin/env bash
# Replay a scene bag through NVBlox and build a 3D map.
# Usage:
#   ./src/scripts/run_nvblox.sh
#   SCENE=warehouse ./src/scripts/run_nvblox.sh
#   SCENE=warehouse BAG=/path/to/bag VOXEL=0.05 ./src/scripts/run_nvblox.sh
set +e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SCENE="${SCENE:-simple_room}"
BAG="${BAG:-$REPO_ROOT/bags/$SCENE}"
VOXEL="${VOXEL:-0.08}"
MAX_DIST="${MAX_DIST:-5.0}"

AVAIL_KB=$(df --output=avail "$REPO_ROOT" | tail -1 | tr -d ' ')
if [ "$AVAIL_KB" -lt 2097152 ]; then
  echo "[nvblox] WARNING: < 2 GB free; NVBlox can silently produce an empty map. Aborting."
  exit 1
fi

if [ ! -e "$BAG/metadata.yaml" ]; then
  echo "[nvblox] ERROR: bag not found at: $BAG"
  echo "[nvblox] Set BAG=<path> or check bags/$SCENE/."
  exit 1
fi

source /opt/ros/humble/setup.bash
export LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64:/opt/nvidia-driver-libs:$LD_LIBRARY_PATH

echo "[nvblox] Scene: $SCENE   Bag: $BAG"
echo "[nvblox] Clearing stale processes and ROS daemon..."
pkill -9 -f nvblox_node 2>/dev/null
pkill -9 -f rviz2 2>/dev/null
pkill -9 -f "bag play" 2>/dev/null
ros2 daemon stop >/dev/null 2>&1; sleep 1
ros2 daemon start >/dev/null 2>&1; sleep 1

PIDS=()
cleanup() {
  echo ""; echo "[nvblox] Shutting down..."
  for pid in "${PIDS[@]}"; do kill "$pid" 2>/dev/null; done
  pkill -9 -f nvblox_node 2>/dev/null
  pkill -9 -f rviz2 2>/dev/null
  pkill -9 -f "bag play" 2>/dev/null
}
trap cleanup EXIT INT TERM

echo "[nvblox] Starting nvblox (voxel=$VOXEL, max_dist=$MAX_DIST)..."
ros2 run nvblox_ros nvblox_node --ros-args \
  -p use_sim_time:=true -p input_qos:=DEFAULT -p use_tf_transforms:=true \
  -p global_frame:=World -p pose_frame:=pelvis -p map_clearing_frame_id:=pelvis \
  -p esdf_slice_bounds_visualization_attachment_frame_id:=pelvis \
  -p workspace_height_bounds_visualization_attachment_frame_id:=pelvis \
  -p voxel_size:=$VOXEL -p use_lidar:=false \
  -p static_mapper.projective_integrator_max_integration_distance_m:=$MAX_DIST \
  -r /camera_0/depth/image:=/camera/depth/image_raw \
  -r /camera_0/depth/camera_info:=/camera/depth/camera_info \
  -r /camera_0/color/image:=/camera/color/image_raw \
  -r /camera_0/color/camera_info:=/camera/color/camera_info &
PIDS+=($!)
sleep 4

echo "[nvblox] Opening RViz..."
ros2 run rviz2 rviz2 --ros-args -p use_sim_time:=true &
PIDS+=($!)
sleep 4

echo "[nvblox] Playing bag: $BAG"
ros2 bag play "$BAG"

echo ""
echo "[nvblox] Bag finished. Map held in memory."
echo "[nvblox] In another terminal: SCENE=$SCENE ./src/scripts/save_nvblox_map.sh"
echo "[nvblox] Then Ctrl-C here."
wait

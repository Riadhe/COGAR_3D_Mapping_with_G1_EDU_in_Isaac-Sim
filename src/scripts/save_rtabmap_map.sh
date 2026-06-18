#!/usr/bin/env bash
#
# save_rtabmap_map.sh
# Export RTAB-Map results (cloud + mesh) from the database, and the 2D
# occupancy grid from the live /rtabmap/map topic, into maps/<scene>/rtabmap/.
#
# Run AFTER run_rtabmap_*.sh has played the bag. The cloud/mesh export reads
# ~/.ros/rtabmap.db (works even after the node stops). The 2D grid needs
# RTAB-Map STILL RUNNING (it reads the live topic).
#
# Usage:
#   ./src/scripts/save_rtabmap_map.sh
#   SCENE=warehouse ./src/scripts/save_rtabmap_map.sh

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SCENE="${SCENE:-simple_room}"
DB="${DB:-$HOME/.ros/rtabmap.db}"
OUT_DIR="${OUT_DIR:-$REPO_ROOT/maps/$SCENE/rtabmap}"

set +u
source /opt/ros/humble/setup.bash
set -u

mkdir -p "$OUT_DIR"

if [[ ! -e "$DB" ]]; then
  echo "[save-rtabmap] ERROR: database not found at $DB" >&2
  echo "               Did run_rtabmap complete a run?" >&2
  exit 1
fi

echo "[save-rtabmap] Scene: $SCENE   ->  $OUT_DIR"

# --- Cloud (rtabmap-export appends _cloud to the basename) ------------------
echo "[save-rtabmap] Exporting point cloud..."
rtabmap-export --cloud --output rtabmap --output_dir "$OUT_DIR" "$DB"
[[ -e "$OUT_DIR/rtabmap_cloud.ply" ]] && mv -f "$OUT_DIR/rtabmap_cloud.ply" "$OUT_DIR/rtabmap_cloud.ply"

# --- Mesh (appends _mesh) ---------------------------------------------------
echo "[save-rtabmap] Exporting mesh..."
rtabmap-export --mesh --output rtabmap --output_dir "$OUT_DIR" "$DB"

# Normalise the doubled names rtabmap-export produces.
[[ -e "$OUT_DIR/rtabmap_cloud.ply" ]] || mv -f "$OUT_DIR"/rtabmap*_cloud.ply "$OUT_DIR/rtabmap_cloud.ply" 2>/dev/null || true
[[ -e "$OUT_DIR/rtabmap_mesh.ply"  ]] || mv -f "$OUT_DIR"/rtabmap*_mesh.ply  "$OUT_DIR/rtabmap_mesh.ply"  2>/dev/null || true

# --- 2D occupancy grid (needs the live /rtabmap/map topic) ------------------
echo "[save-rtabmap] Saving 2D occupancy grid (requires RTAB-Map still running)..."
if ros2 topic list 2>/dev/null | grep -q "/rtabmap/map"; then
  ros2 run nav2_map_server map_saver_cli -t /rtabmap/map -f "$OUT_DIR/rtabmap_grid" \
    && echo "[save-rtabmap] grid saved." \
    || echo "[save-rtabmap] grid save failed (is /rtabmap/map publishing?)."
else
  echo "[save-rtabmap] /rtabmap/map not found — RTAB-Map not running; skipped grid."
  echo "[save-rtabmap] (cloud + mesh were still exported from the database.)"
fi

echo "[save-rtabmap] Done. Contents:"
ls -lh "$OUT_DIR"

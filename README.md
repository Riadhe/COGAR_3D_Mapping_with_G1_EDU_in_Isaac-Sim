# Subgroup K1: 3D Mapping with G1 EDU in Isaac Sim

Assignment 1: Benchmarking 3D Mapping Pipelines for Humanoid Robot Perception (SIMULATION) + (NVIDIA)

What to do: Develop and evaluate a standalone 3D mapping pipeline for the G1 EDU robot in Isaac Sim using ROS2 Humble, focusing on how different mapping frameworks reconstruct indoor environments for humanoid operation
1) Set up the G1 EDU robot model in Isaac Sim with simulated RGB‑D camera and LiDAR sensor
2) Integrate and test one or more 3D mapping frameworks (e.g. RTAB‑Map, OctoMap, Voxblox, NVBlox)
3) Generate 3D maps of benchmark indoor environments with different levels of complexity
4) Evaluate mapping quality using geometric metrics such as reconstruction completeness, consistency, density, and update latency
5) Compare different map representations (point clouds, occupancy maps, voxel maps, ESDF) for navigation readiness
6) Document strengths and weaknesses of each mapping pipeline for humanoid robot deployment

Software needed: Isaac Sim, RTAB‑Map / OctoMap / Voxblox / NVBlox, Open3D, RViz2

Research needed: 3D mapping methods for mobile robots, RGB‑D / LiDAR reconstruction, voxel mapping, simulation‑based map evaluation

Deliverables: Standalone 3D mapping pipeline, benchmark maps of multiple environments, comparative report on map quality and representation suitability

# Stating point:
For the robot you should open Isaac Sim, import the robot from the repo unitree/G1 29 degrees of freedom (DOF) and use the G1 model physics.

- 3D LIDAR (LIVOX-MID360) + Depth Camera Intel RealSense (D435i)
---

## 1. Overview

This repo benchmarks multiple 3D mapping frameworks on the same recorded sensor data from the G1 EDU in Isaac Sim. Each framework replays an identical rosbag offline and exports its maps in comparable representations (cloud / mesh / occupancy / ESDF), which are then evaluated against shared geometric and navigation-readiness metrics.

**Status at a glance:**

| | Done | Pending |
|---|---|---|
| Scenes | `simple_room` | `warehouse` |
| Frameworks | NVBlox, RTAB-Map, OctoMap | — |
| Phase | map generation | metrics / comparative report |

---

## 2. Setup

### Stack
- **Host OS:** Ubuntu 24.04
- **Simulator:** NVIDIA Isaac Sim 5.1 (native install)
- **Container:** Distrobox + Ubuntu 22.04 with ROS2 Humble
- **Robot:** Unitree G1 29-DOF (`g1_29dof_with_hand_rev_1_0`)
- **Sensors:** Livox MID-360 LiDAR + Intel RealSense D435 RGB-D

### Topics published

| Topic | Source |
|---|---|
| `/point_cloud` | MID-360 LiDAR |
| `/camera/color/image_raw` (+ `camera_info`) | D435 color |
| `/camera/depth/image_raw` (+ `camera_info`) | D435 depth |
| `/joint_states` | G1 articulation (29 DOF) |
| `/clock` | Isaac Sim sim time |
| `/tf` + `/tf_static` | robot_state_publisher |

### TF / frames
TF is anchored to `World` via static transform, then `pelvis → ... → torso_link → {d435_link, mid360_link}`.

**Optical-frame convention (critical):** Isaac Sim publishes camera data on body frames (x-forward / z-up), but mapping frameworks expect optical frames (z-forward / x-right / y-down). The optical-frame static transforms are carried in the recorded `/tf_static`, so frameworks consume them directly off the bag. This was the root cause of an early rotated-map problem.

---

## 3. Benchmark scenes

| Scene | Source | Bag | Status |
|---|---|---|---|
| `simple_room` | Isaac Assets *Simple Room* | 160 s, 9014 msgs, 8 topics | ✅ recorded & mapped |
| `warehouse` | Isaac Assets | — | ⬜ pending |

**Recording:** load the scene into the G1 stage, drive a trajectory (`isaac_sim/scripts/motion_circle.py`), and `ros2 bag record` all sensor topics. `/clock` is recorded, so replay drives sim time (no `--clock` needed for NVBlox; RTAB-Map run uses `--clock` with `/clock` excluded from the topic list).

Bags are large and **not committed** to git — recorded separately and stored outside the repo.

---

## 4. Mapping frameworks

| Framework | Install | Native output | Status |
|---|---|---|---|
| **NVBlox** | Isaac ROS apt repo | TSDF mesh + ESDF | ✅ done |
| **RTAB-Map** | `ros-humble-rtabmap-ros` | RGB-D SLAM: cloud + 2D occupancy | ✅ done |
| **OctoMap** | `ros-humble-octomap-server` | occupancy octree (LiDAR) | ✅ done |

All runs are offline on the recorded bag, with Isaac Sim closed (bag is the only data source). See **How to run** below for commands.

### NVBlox
Builds a TSDF mesh + ESDF from the **D435 RGB-D** camera. Run script applies `input_qos:=DEFAULT` (Isaac Sim publishes Best-Effort), remaps `/camera_0/...` ← `/camera/...`, and includes disk-space + stale-daemon guards.

Saved artifacts (via `save_ply` / `save_map` services while the node is alive):
- `nvblox_mesh.ply` — TSDF mesh
- `nvblox_map.nvblx` — full native map (TSDF + ESDF)

NVBlox's navigation representation is the ESDF, contained in the `.nvblx`. The 2D occupancy grid is published only live during playback (not latched), so it is not captured post-run.

### RTAB-Map
RGB-D SLAM from the **D435** (`frame_id:=d435_link`, `approx_sync:=true`, `use_sim_time:=true`). The run script launches RTAB-Map, **waits until it has subscribed to the RGB topic**, then plays the bag — guaranteeing no opening frames are missed (replaces a manual `--start-paused` + SPACE step).

Saved artifacts (exports read the database `~/.ros/rtabmap.db`; the 2D grid is read from the live `/rtabmap/map` topic):
- `rtabmap_cloud.ply` — point cloud
- `rtabmap_mesh.ply` — mesh
- `rtabmap_grid.pgm` + `.yaml` — 2D occupancy grid

**Known limitations:** the D435 is chest-mounted, so the G1's own torso self-occludes part of the FOV (visible as a robot fragment in the cloud). The constant-radius circular trajectory produces feature-similar revisits that RTAB-Map's loop-closure verification tends to reject.

### OctoMap
Unlike the RGB-D frameworks, OctoMap builds from the **MID-360 LiDAR** point cloud (`cloud_in:=/point_cloud`, `frame_id:=World`, resolution 0.03 m, max range 8 m). A single bag pass produces a probabilistic 3D occupancy octree.

Saved artifact (`octomap_saver_node`, **absolute path** required — ROS params don't expand `~`):
- `octomap_occupancy.bt` — binary occupancy octree

**Note:** the resulting octree (~1.3M nodes @ 0.03 m) compresses to ~293 KB on disk, far smaller than the RGB-D point clouds for the same room — OctoMap collapses large uniform free/occupied regions into single nodes.

---

## How to run

All scripts are **scene-generic** via a `SCENE` variable (default `simple_room`). To benchmark a new scene: record its bag to `bags/<scene>/` (same topics as above), then run with `SCENE=<scene>`. Maps save to `maps/<scene>/<framework>/`.

**Pattern:** run script in terminal 1 (keep it alive after the bag finishes), save script in terminal 2.

### NVBlox
```
# terminal 1 — build the map
./src/scripts/run_nvblox.sh                  # simple_room (default)
SCENE=warehouse ./src/scripts/run_nvblox.sh  # another scene

# terminal 2 — save while the run is still alive
SCENE=warehouse ./src/scripts/save_nvblox_map.sh
```

### RTAB-Map
```
# terminal 1
SCENE=warehouse ./src/scripts/run_rtabmap.sh
# terminal 2 — exports cloud + mesh from DB, 2D grid from live topic
SCENE=warehouse ./src/scripts/save_rtabmap_map.sh
```

### OctoMap
```
# terminal 1
SCENE=warehouse ./src/scripts/run_octomap.sh
# terminal 2 — saves occupancy octree (.bt)
SCENE=warehouse ./src/scripts/save_octomap_map.sh
```

**Notes:**
- Keep the run terminal alive until the save completes — NVBlox/OctoMap hold the map in node memory; RTAB-Map's 2D grid is read from the live topic.
- Override the bag path with `BAG=/path/to/bag` if it isn't under `bags/<scene>/`.
- Tunables: NVBlox `VOXEL=`, `MAX_DIST=`; OctoMap `RESOLUTION=`, `MAX_RANGE=`.
- A new scene needs the **same topic names** as `simple_room`; record identically and the scripts work unchanged.

---

## 5. Map outputs

Maps live under `maps/<scene>/<framework>/`. Large map files are stored outside git; the structure and naming are tracked.

```
maps/
  simple_room/
    nvblox/    nvblox_mesh.ply, nvblox_map.nvblx
    rtabmap/   rtabmap_cloud.ply, rtabmap_mesh.ply, rtabmap_grid.pgm, rtabmap_grid.yaml
    octomap/   octomap_occupancy.bt
```

| Scene | Framework | Cloud | Mesh | Occupancy / ESDF |
|---|---|---|---|---|
| simple_room | NVBlox | (from mesh) | ✅ 32k v / 50k f | ESDF in `.nvblx` |
| simple_room | RTAB-Map | ✅ 436k pts | ✅ ~976k polys | ✅ 2D grid 212×229 @ 0.05 m |
| simple_room | OctoMap | (octree centers) | — | ✅ `.bt` octree, ~1.3M nodes @ 0.03 m |

---


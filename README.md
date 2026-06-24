# Subgroup K1: 3D Mapping with G1 EDU in Isaac Sim

**Assignment 1: Benchmarking 3D Mapping Pipelines for Humanoid Robot Perception (SIMULATION + NVIDIA)**

Develop and evaluate a standalone 3D mapping pipeline for the G1 EDU robot in Isaac Sim using ROS 2 Humble, focusing on how different mapping frameworks reconstruct indoor environments for humanoid operation.

1. Set up the G1 EDU robot model in Isaac Sim with simulated RGB-D camera and LiDAR sensor
2. Integrate and test one or more 3D mapping frameworks (e.g. RTAB-Map, OctoMap, Voxblox, NVBlox)
3. Generate 3D maps of benchmark indoor environments with different levels of complexity
4. Evaluate mapping quality using geometric metrics such as reconstruction completeness, consistency, density, and update latency
5. Compare different map representations (point clouds, occupancy maps, voxel maps, ESDF) for navigation readiness
6. Document strengths and weaknesses of each mapping pipeline for humanoid robot deployment

**Software:** Isaac Sim, RTAB-Map / OctoMap / Voxblox / NVBlox, Open3D, RViz2
**Deliverables:** standalone 3D mapping pipeline, benchmark maps of multiple environments, comparative report on map quality and representation suitability.

**Starting point:** open Isaac Sim, import the Unitree G1 29-DOF robot and use the G1 physics model. Sensors: 3D LiDAR (Livox MID-360) + Intel RealSense D435 depth camera.

---

## 1. Overview

This repo benchmarks multiple 3D mapping frameworks on the same recorded sensor data from the G1 EDU in Isaac Sim. Each framework replays an identical rosbag offline and exports its maps in comparable representations (cloud / mesh / occupancy / ESDF), which are then evaluated against shared geometric and navigation-readiness metrics.

---

## 2. Setup

### Stack
- **Host OS:** Ubuntu 24.04
- **Simulator:** NVIDIA Isaac Sim 5.1 (native install)
- **Container:** Distrobox + Ubuntu 22.04 with ROS 2 Humble
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

### Hardware constraints and reproducibility
All simulations, bag recordings, and map generation were executed on a local machine with constrained hardware (4 GB VRAM GPU, 14 GB RAM).
- **Impact:** the 4 GB VRAM limit bottlenecked GPU-heavy frameworks such as NVBlox, causing elevated update intervals and occasional frame drops during recording.
- **Justification:** these constraints are documented as genuine findings. The pipeline logic is sound, and running the identical setup on higher-end hardware (e.g. 16 GB+ VRAM) would naturally yield faster updates and denser maps.

---

## 3. Benchmark scenes

| Scene | Source | Bag | Status |
|---|---|---|---|
| `simple_room` | Isaac Assets *Simple Room* | 160 s, 9014 msgs, 8 topics | ✅ recorded & mapped |
| `warehouse` | Isaac Assets *Simple Warehouse* | 128 s, 8611 msgs, 9 topics | ✅ recorded & mapped |

**Recording:** load the scene into the G1 stage, drive a trajectory (`isaac_sim/scripts/360_rotation.py`), and `ros2 bag record` all sensor topics. `/clock` is recorded, so replay drives sim time (no `--clock` needed for NVBlox; the RTAB-Map run uses `--clock` with `/clock` excluded from the topic list).

> **Warehouse bag note:** recorded on memory-constrained hardware; ~2635 messages were dropped at record time due to cache-buffer overload (even loss across topics, ~25 %). The bag remains usable (~1250 frames/sensor) and produces valid maps; this is documented as a hardware-constraint artifact.

Bags are large and **not committed** to git — recorded separately and stored outside the repo.

---

## 4. Mapping frameworks

| Framework | Install | Native output | Sensor | Status |
|---|---|---|---|---|
| **NVBlox** | Isaac ROS apt repo | TSDF mesh + ESDF | D435 RGB-D | ✅ done |
| **RTAB-Map** | `ros-humble-rtabmap-ros` | RGB-D SLAM: cloud + 2D occupancy | D435 RGB-D | ✅ done |
| **OctoMap** | `ros-humble-octomap-server` | occupancy octree | MID-360 LiDAR | ✅ done |

Each framework is paired with its optimal native sensor (rather than fusing sensors, which would obscure individual algorithm strengths). All runs are offline on the recorded bag, with Isaac Sim closed (the bag is the only data source).

### NVBlox
Builds a TSDF mesh + ESDF from the **D435 RGB-D** camera. The run script applies `input_qos:=DEFAULT` (Isaac Sim publishes Best-Effort), remaps `/camera_0/...` ← `/camera/...`, and includes disk-space and stale-daemon guards.

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

**Known limitations:** the D435 is chest-mounted, so the G1's own torso self-occludes part of the FOV (visible as a robot fragment in the cloud). The trajectory produces feature-similar revisits that RTAB-Map's loop-closure verification tends to reject.

### OctoMap
Unlike the RGB-D frameworks, OctoMap builds from the **MID-360 LiDAR** point cloud (`cloud_in:=/point_cloud`, `frame_id:=World`, resolution 0.03 m, max range 8 m). A single bag pass produces a probabilistic 3D occupancy octree.

Saved artifact (`octomap_saver_node`, **absolute path** required — ROS params don't expand `~`):
- `octomap_occupancy.bt` — binary occupancy octree

**Note:** the resulting octree (~1.3M nodes @ 0.03 m) compresses to ~293 KB on disk, far smaller than the RGB-D point clouds for the same room — OctoMap collapses large uniform free/occupied regions into single nodes.

---

## 5. How to run

All scripts are **scene-generic** via a `SCENE` variable (default `simple_room`). To benchmark a new scene: record its bag to `bags/<scene>/` (same topics as above), then run with `SCENE=<scene>`. Maps save to `maps/<scene>/<framework>/`.

**Pattern:** run script in terminal 1 (keep it alive after the bag finishes), save script in terminal 2.

### NVBlox
```bash
# terminal 1 — build the map
./src/scripts/run_nvblox.sh                  # simple_room (default)
SCENE=warehouse ./src/scripts/run_nvblox.sh  # another scene

# terminal 2 — save while the run is still alive
SCENE=warehouse ./src/scripts/save_nvblox_map.sh
```

### RTAB-Map
```bash
# terminal 1
SCENE=warehouse ./src/scripts/run_rtabmap.sh
# terminal 2 — exports cloud + mesh from DB, 2D grid from live topic
SCENE=warehouse ./src/scripts/save_rtabmap_map.sh
```

### OctoMap
```bash
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

## 6. Map outputs

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
| simple_room | NVBlox | (from mesh) |  32k v / 50k f | ESDF in `.nvblx` |
| simple_room | RTAB-Map |  436k pts |  ~976k polys |  2D grid 212×229 @ 0.05 m |
| simple_room | OctoMap | (octree centers) | — | `.bt` octree, ~1.3M nodes @ 0.03 m |
| warehouse | NVBlox | (from mesh) |  mesh `.ply` | ESDF in `.nvblx` |
| warehouse | RTAB-Map |  516k pts |  mesh `.ply` |  2D grid 283×220 @ 0.05 m |
| warehouse | OctoMap | (octree centers) | — |  `.bt` octree |

---
## 7. Evaluation

Evaluation is **scene-independent**: metrics compare the three frameworks *within* each scene (identical bag = identical input). Scripts live in `evaluation/scripts/`, outputs in `evaluation/results/`.

**Dependencies:**
```bash
pip install open3d matplotlib numpy
```

### Metrics computed
- **Density** — points per m³ per framework
- **Coverage / completeness proxy** — occupied-voxel count and occupied volume at 5 cm (ground-truth-free; see note)
- **Consistency** — pairwise framework agreement via point-to-plane ICP registration + multi-resolution voxel IoU
- **Update latency** — per-framework map-update interval (median / mean / max), measured live during bag replay

> **On completeness:** absolute accuracy-vs-ground-truth was attempted (Isaac USD export → `make_gt_cloud.py`) but the exported mesh was volumetric and frame-misaligned, making surface comparison unreliable. The evaluation therefore uses ground-truth-free metrics (density, coverage, inter-framework consistency), which are robust and reproducible.

### Scripts

| Script | Purpose |
|---|---|
| `metrics_open3d.py` | Per-framework density / extent / volume + pairwise ICP & voxel IoU → `<scene>_per_framework.csv` |
| `make_figures.py` | Completeness/coverage CSV + density/coverage/latency charts (PNG) |
| `measure_latency.py` | Times a framework's map-update topic during replay → `<scene>_latency.csv` |
| `render_maps.py` | Offscreen Open3D renders of each saved map (PNG) |
| `save_octomap_cloud.py` | Captures OctoMap occupied-cell centers from `/octomap_point_cloud_centers` → `.ply` (for voxel metrics) |
| `make_gt_cloud.py` | Samples a ground-truth cloud from the Isaac USD export (early approach, retained for reference) |
| `_archive/` | Superseded diagnostic / early-version scripts, kept locally (gitignored) |

### Running the evaluation
All scripts honor the `SCENE` variable (default `simple_room`). Run after the maps for a scene exist:

```bash
python3 evaluation/scripts/metrics_open3d.py                  # simple_room
SCENE=warehouse python3 evaluation/scripts/metrics_open3d.py  # warehouse
SCENE=warehouse python3 evaluation/scripts/make_figures.py
SCENE=warehouse python3 evaluation/scripts/render_maps.py
```

Latency must run **while a framework replays the bag** (start the timer, then launch the run script in another terminal):

```bash
python3 evaluation/scripts/measure_latency.py /nvblox_node/mesh NVBlox
python3 evaluation/scripts/measure_latency.py /rtabmap/mapData RTAB-Map
python3 evaluation/scripts/measure_latency.py /octomap_point_cloud_centers OctoMap
```

### Outputs (`evaluation/results/`)
- `<scene>_per_framework.csv` — density, extent, volume
- `<scene>_completeness.csv` — coverage (voxels + volume)
- `<scene>_latency.csv` — update-interval stats
- `figures/<scene>_{density,coverage,latency}.png` — charts
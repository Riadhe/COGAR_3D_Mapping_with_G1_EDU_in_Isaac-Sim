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

## Week 1 — Setup and sensor pipeline 

**Goal:** Get the G1 EDU publishing all needed ROS2 topics for 3D mapping.

### Stack
- **Host OS:** Ubuntu 24.04
- **Simulator:** NVIDIA Isaac Sim 5.x (native install)
- **Container:** Distrobox + Ubuntu 22.04 with ROS2 Humble
- **Robot:** Unitree G1 29-DOF (`g1_29dof_with_hand_rev_1_0`)
- **Sensors:** Hesai Pandar XT-32 LiDAR + RealSense RSD455 RGB-D

### Topics published

| Topic | Rate | Source |
|---|---|---|
| `/point_cloud` | ~18 Hz | RTX LiDAR sensor |
| `/camera/color/image_raw` | ~12 Hz | RealSense color camera |
| `/camera/depth/image_raw` | ~11 Hz | RealSense pseudo-depth |
| `/joint_states` | ~18 Hz | G1 articulation (29 DOFs) |
| `/clock` | sim time | Isaac Sim clock |
| `/tf` + `/tf_static` | ~20 Hz | robot_state_publisher (container) |

### TF tree
Anchored to `world` via static transform, then `pelvis → ... → torso_link → {d435_link, mid360_link}`. Sensor frames are correctly placed via Unitree's official URDF.

### Notes
The Articulation Root API is applied to the `pelvis` prim (not the top-level Xform), which is what the OmniGraph Joint States dialog needs to target.

---

## Week 2 — First RTAB-Map test

**Goal:** Produce a first 3D map of an indoor scene using RTAB-Map on a recorded rosbag.

### Approach (rosbag workflow)

1. Load a benchmark indoor scene (`Simple Room` from Isaac Assets) into the Week 1 G1 scene
2. Move the G1 along a known trajectory through the scene (Python script from Isaac Sim Script Editor)
3. Record a rosbag of all sensor topics during motion
4. Run RTAB-Map **offline** on the rosbag, visualize the reconstructed 3D map in RViz2 and `rtabmap_viz`

### What's been done

- ✅ `simple_room.usd` loaded as a reference into `g1_scene.usd`; G1 positioned on the coffee table
- ✅ `ROS_TF` Action Graph extended: `targetPrims` now includes `torso_link`, `mid360_link`, `d435_link`, `head_link` and the G1 root, all parented under `World`
- ✅ LiDAR point cloud verified in RViz2 (Fixed Frame = `World`, PointCloud2 subscribed to `/point_cloud`)
- ✅ `motion_circle.py`: moves the G1 in a 0.5 m horizontal circle for 30 s, then resets to home pose
- ✅ `cleanup_xform.py`: utility to remove stray xform ops (`xformOp:rotateXYZ`) that broke physics on Play
- ✅ Rosbag recorded (`week2_first_map`, ~80 s duration, 7 topics, ~9 Hz each)
- ✅ RTAB-Map installed (`ros-humble-rtabmap-ros`) and launched on the rosbag with `frame_id:=d435_link`, `approx_sync:=true`, `use_sim_time:=true`
- ✅ 3D reconstruction of the room produced (depth-only, untextured): walls, floor, ceiling, coffee table, and the G1's own body visible as a self-occlusion artifact

### How to reproduce

1. Open `isaac_sim/stages/g1_scene.usd` in Isaac Sim 5.1, press Play.
2. Confirm topics `/camera/color/image_raw`, `/camera/depth/image_raw`, `/point_cloud`, `/tf` are published.
3. In the Script Editor, paste and run `isaac_sim/scripts/motion_circle.py`.
4. While motion is running, in a distrobox terminal:
```bash
   ros2 bag record /tf /tf_static /clock /camera/color/image_raw \
     /camera/depth/image_raw /camera_info /point_cloud /joint_states \
     -o week2_first_map
```
5. Stop the bag after the motion completes (~30 s + buffer).
6. Close Isaac Sim. Launch RTAB-Map and play the bag:
```bash
   ros2 launch rtabmap_launch rtabmap.launch.py \
     rgb_topic:=/camera/color/image_raw \
     depth_topic:=/camera/depth/image_raw \
     camera_info_topic:=/camera_info \
     frame_id:=d435_link \
     approx_sync:=true approx_sync_max_interval:=0.1 \
     use_sim_time:=true rviz:=true qos:=2 \
     args:="--delete_db_on_start --Vis/MinInliers 10"

   ros2 bag play week2_first_map --clock
```

### Utility scripts

- `isaac_sim/scripts/motion_circle.py` — programmatic G1 motion for repeatable rosbag recording
- `isaac_sim/scripts/cleanup_xform.py` — resets xform ops on the G1 root if physics misbehaves on Play

### Known limitations

- **Self-occlusion:** the D435 is chest-mounted on the G1, so the robot's own torso/arms occupy part of the field of view. Visible as a "robot fragment" in the reconstructed cloud — characteristic of humanoid platforms with chest-mounted RGB-D.
- **No RGB texture on the map (red surfaces):** RTAB-Map produces depth-only point cloud. Root cause appears to be visual-odometry instability ("Not enough inliers 0/N" warnings) driven by sim-time vs wall-time conflicts in the TF buffer. Color is correctly published (`rgb8`, 1280×720, `frame_id: d435_link`) but doesn't reach the global map.
- **Loop closure rarely accepted:** the constant-radius circular path produces feature-similar revisits that RTAB-Map's geometric verification rejects.

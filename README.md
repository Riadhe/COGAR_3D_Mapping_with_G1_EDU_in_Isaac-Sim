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
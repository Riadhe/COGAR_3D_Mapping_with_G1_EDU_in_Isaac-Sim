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
For the robot you should open Isaac Sim, import the robot from the repo unitree/G1 and use the G1 model physics, then you should add the three-fingered force control and dexterous hands. 
-> 3D LIDAR (LIVOX-MID360) + Depth Camera Intel RealSense (D435i)

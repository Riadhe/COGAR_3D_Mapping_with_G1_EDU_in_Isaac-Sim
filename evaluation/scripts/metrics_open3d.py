#!/usr/bin/env python3
"""Benchmark metrics using Open3D: per-framework stats + ICP registration + IoU.

Scene-parametrized via SCENE env var (default: simple_room).
Usage:
    python3 metrics_open3d.py                      # simple_room
    SCENE=warehouse python3 metrics_open3d.py      # warehouse
"""
import os
import csv
import numpy as np
import open3d as o3d

REPO = "/home/ba7rouch/Documents/GitHub/COGAR_3D_Mapping_with_G1_EDU_in_Isaac-Sim"
SCENE = os.environ.get("SCENE", "simple_room")
MAPS = {
    "NVBlox":   f"{REPO}/maps/{SCENE}/nvblox/nvblox_mesh.ply",
    "RTAB-Map": f"{REPO}/maps/{SCENE}/rtabmap/rtabmap_cloud.ply",
    "OctoMap":  f"{REPO}/maps/{SCENE}/octomap/octomap_cloud.ply",
}
RESULTS_DIR = f"{REPO}/evaluation/results"
os.makedirs(RESULTS_DIR, exist_ok=True)

print(f"=== SCENE: {SCENE} ===\n")


def load_pcd(path):
    # read_point_cloud reads PLY vertices (works for mesh PLY too via points)
    pcd = o3d.io.read_point_cloud(path)
    if len(pcd.points) == 0:               # fallback: mesh -> vertices
        m = o3d.io.read_triangle_mesh(path)
        pcd = o3d.geometry.PointCloud(m.vertices)
    return pcd


pcds = {n: load_pcd(p) for n, p in MAPS.items()}

print("== Per-framework ==")
print(f"{'Framework':<10}{'Points':>9}{'Extent(m)':>24}{'Vol(m3)':>9}{'Dens/m3':>9}")
for n, pc in pcds.items():
    pts = np.asarray(pc.points)
    ext = pts.max(0) - pts.min(0)
    vol = float(ext[0]*ext[1]*ext[2])
    print(f"{n:<10}{len(pts):>9}   {ext.round(2)}{vol:>9.1f}{len(pts)/vol:>9.0f}")


# --- Pairwise registration + multi-res voxel IoU (all pairs) ---
def prep(pcd):
    p = o3d.geometry.PointCloud(pcd)
    p.translate(-p.get_center())
    return p


def register(src, dst):
    s = prep(src).voxel_down_sample(0.05)
    d = prep(dst).voxel_down_sample(0.05)
    s.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.2, max_nn=30))
    d.estimate_normals(o3d.geometry.KDTreeSearchParamHybrid(radius=0.2, max_nn=30))
    reg = o3d.pipelines.registration.registration_icp(
        s, d, 0.30, np.eye(4),
        o3d.pipelines.registration.TransformationEstimationPointToPlane(),
        o3d.pipelines.registration.ICPConvergenceCriteria(max_iteration=200))
    # apply to full-res centered src
    s_full = prep(src)
    s_full.transform(reg.transformation)
    return reg, np.asarray(s_full.points), np.asarray(prep(dst).points)


def vset(p, vs):
    return set(map(tuple, np.floor(p/vs).astype(np.int64)))


names = list(pcds)
print("\n== Pairwise consistency (point-to-plane ICP) ==")
for i in range(len(names)):
    for j in range(i+1, len(names)):
        a_name, b_name = names[i], names[j]
        reg, a, b = register(pcds[a_name], pcds[b_name])
        print(f"\n  {a_name} <-> {b_name}:  fitness={reg.fitness:.3f}  RMSE={reg.inlier_rmse:.3f}m")
        row = "    IoU% by voxel: "
        for vs in (0.05, 0.10, 0.20, 0.50):
            va, vb = vset(a, vs), vset(b, vs)
            inter, union = len(va & vb), len(va | vb)
            iou = 100*inter/union if union else 0
            row += f"{vs}m={iou:.1f}  "
        print(row)


# --- Save per-framework results to CSV ---
csv_path = f"{RESULTS_DIR}/{SCENE}_per_framework.csv"
with open(csv_path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["framework", "points", "ext_x", "ext_y", "ext_z",
                "volume_m3", "density_per_m3"])
    for n, pc in pcds.items():
        pts = np.asarray(pc.points)
        ext = pts.max(0) - pts.min(0)
        vol = float(ext[0]*ext[1]*ext[2])
        w.writerow([n, len(pts), *ext.round(3), round(vol, 1),
                    round(len(pts)/vol, 1)])
print(f"\nsaved {csv_path}")
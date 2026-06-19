#!/usr/bin/env python3
"""Generate report figures + completeness(coverage) metric from saved maps.
Usage: SCENE=warehouse python3 make_figures.py
Reads maps/<scene>/*/*.ply and results/<scene>_latency.csv.
Writes PNGs + <scene>_completeness.csv into evaluation/results/figures/.
"""
import os, csv
import numpy as np
import open3d as o3d
import matplotlib
matplotlib.use("Agg")          # no display needed
import matplotlib.pyplot as plt

REPO = "/home/ba7rouch/Documents/GitHub/COGAR_3D_Mapping_with_G1_EDU_in_Isaac-Sim"
SCENE = os.environ.get("SCENE", "simple_room")
MAPS = {
    "NVBlox":   f"{REPO}/maps/{SCENE}/nvblox/nvblox_mesh.ply",
    "RTAB-Map": f"{REPO}/maps/{SCENE}/rtabmap/rtabmap_cloud.ply",
    "OctoMap":  f"{REPO}/maps/{SCENE}/octomap/octomap_cloud.ply",
}
OUT = f"{REPO}/evaluation/results/figures"
os.makedirs(OUT, exist_ok=True)
VOXEL = 0.05
COLORS = {"NVBlox": "#4C72B0", "RTAB-Map": "#DD8452", "OctoMap": "#55A868"}

def load(path):
    p = o3d.io.read_point_cloud(path)
    if len(p.points) == 0:
        m = o3d.io.read_triangle_mesh(path); p = o3d.geometry.PointCloud(m.vertices)
    return np.asarray(p.points)

clouds = {n: load(p) for n, p in MAPS.items()}

# ---- per-framework: density + completeness(coverage = occupied voxels) ----
rows = []
for n, pts in clouds.items():
    ext = pts.max(0) - pts.min(0)
    vol = float(ext[0]*ext[1]*ext[2])
    vox = set(map(tuple, np.floor(pts/VOXEL).astype(np.int64)))
    coverage_voxels = len(vox)
    coverage_vol = coverage_voxels * VOXEL**3       # m^3 of occupied space
    rows.append({"framework": n, "points": len(pts),
                 "density_per_m3": round(len(pts)/vol, 1),
                 "coverage_voxels": coverage_voxels,
                 "coverage_vol_m3": round(coverage_vol, 2),
                 "bbox_vol_m3": round(vol, 1)})

# write completeness CSV
comp_csv = f"{REPO}/evaluation/results/{SCENE}_completeness.csv"
with open(comp_csv, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader()
    for r in rows: w.writerow(r)
print(f"saved {comp_csv}")

names = [r["framework"] for r in rows]
cols  = [COLORS[n] for n in names]

# ---- chart 1: density ----
plt.figure(figsize=(6,4))
plt.bar(names, [r["density_per_m3"] for r in rows], color=cols)
plt.ylabel("Point density (pts/m³)"); plt.title(f"Map density — {SCENE}")
plt.tight_layout(); plt.savefig(f"{OUT}/{SCENE}_density.png", dpi=140); plt.close()

# ---- chart 2: coverage (completeness proxy) ----
plt.figure(figsize=(6,4))
plt.bar(names, [r["coverage_vol_m3"] for r in rows], color=cols)
plt.ylabel("Occupied volume (m³)"); plt.title(f"Map coverage / completeness proxy — {SCENE}")
plt.tight_layout(); plt.savefig(f"{OUT}/{SCENE}_coverage.png", dpi=140); plt.close()

# ---- chart 3: latency (from CSV; uses median_ms) ----
lat_csv = f"{REPO}/evaluation/results/{SCENE}_latency.csv"
if os.path.exists(lat_csv):
    lat = {}
    with open(lat_csv) as f:
        for r in csv.DictReader(f):
            lat[r["framework"]] = float(r["median_ms"])
    fw = [n for n in names if n in lat]
    plt.figure(figsize=(6,4))
    plt.bar(fw, [lat[n] for n in fw], color=[COLORS[n] for n in fw])
    plt.ylabel("Median map-update interval (ms)")
    plt.title(f"Update latency (lower=faster) — {SCENE}")
    plt.tight_layout(); plt.savefig(f"{OUT}/{SCENE}_latency.png", dpi=140); plt.close()
    print(f"saved latency chart")
else:
    print(f"(no latency CSV for {SCENE}, skipping latency chart)")

print(f"figures -> {OUT}/{SCENE}_*.png")
for r in rows:
    print(f"  {r['framework']:<10} density={r['density_per_m3']:>7} "
          f"coverage={r['coverage_vol_m3']:>7} m³  ({r['coverage_voxels']} voxels)")
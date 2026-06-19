#!/usr/bin/env python3
"""Sample the ground-truth room mesh into a cropped point cloud."""
import sys, numpy as np, trimesh
from plyfile import PlyData, PlyElement

GT_OBJ = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/ba7rouch/Desktop/g1_mapping/ground_truth_simple_room/ground_truth_simple_room.obj"
OUT_PLY = sys.argv[2] if len(sys.argv) > 2 else \
    "maps/simple_room/ground_truth/ground_truth_cloud.ply"

# Robot-reachable room interior (from RTAB-Map mapped bounds)
XMIN, XMAX = -4.2, 5.3
YMIN, YMAX = -5.3, 5.0
ZMIN, ZMAX = -2.3, 2.1
N_SAMPLE = 500000

print(f"Loading {GT_OBJ}")
m = trimesh.load(GT_OBJ, force='mesh')
print("GT mesh:", len(m.vertices), "verts")

pts, _ = trimesh.sample.sample_surface(m, N_SAMPLE)
pts = np.asarray(pts)

keep = ((pts[:,0]>=XMIN)&(pts[:,0]<=XMAX)&
        (pts[:,1]>=YMIN)&(pts[:,1]<=YMAX)&
        (pts[:,2]>=ZMIN)&(pts[:,2]<=ZMAX))
gt = pts[keep]
print(f"after crop: {len(gt)} ({100*keep.mean():.1f}%)")
print("cropped bounds  min", gt.min(0).round(2), " max", gt.max(0).round(2))

verts = np.array([tuple(p) for p in gt],
                 dtype=[('x','f4'),('y','f4'),('z','f4')])
PlyData([PlyElement.describe(verts,'vertex')]).write(OUT_PLY)
print("saved", OUT_PLY)

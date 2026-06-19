#!/usr/bin/env python3
"""Offscreen-render each saved map to a PNG for the report.
Usage: SCENE=warehouse python3 render_maps.py
Writes evaluation/results/figures/<scene>_<framework>_map.png
"""
import os
import numpy as np
import open3d as o3d

REPO = "/home/ba7rouch/Documents/GitHub/COGAR_3D_Mapping_with_G1_EDU_in_Isaac-Sim"
SCENE = os.environ.get("SCENE", "simple_room")
MAPS = {
    "nvblox":   f"{REPO}/maps/{SCENE}/nvblox/nvblox_mesh.ply",
    "rtabmap":  f"{REPO}/maps/{SCENE}/rtabmap/rtabmap_cloud.ply",
    "octomap":  f"{REPO}/maps/{SCENE}/octomap/octomap_cloud.ply",
}
OUT = f"{REPO}/evaluation/results/figures"
os.makedirs(OUT, exist_ok=True)

def render(path, out_png):
    # try mesh first (nvblox), else point cloud
    geo = o3d.io.read_triangle_mesh(path)
    if len(geo.vertices) > 0 and len(geo.triangles) > 0:
        geo.compute_vertex_normals()
    else:
        geo = o3d.io.read_point_cloud(path)
        if len(geo.points) == 0:
            print(f"  EMPTY: {path}"); return False
        # color points by height (z) for readability
        pts = np.asarray(geo.points)
        z = pts[:,2]; z = (z - z.min())/(np.ptp(z)+1e-9)
        import matplotlib.cm as cm
        geo.colors = o3d.utility.Vector3dVector(cm.viridis(z)[:, :3])

    vis = o3d.visualization.Visualizer()
    vis.create_window(visible=False, width=1280, height=960)
    vis.add_geometry(geo)
    opt = vis.get_render_option()
    opt.background_color = np.array([1, 1, 1])
    opt.point_size = 2.0
    # a reasonable viewpoint
    vc = vis.get_view_control()
    vc.set_zoom(0.7)
    vc.set_front([0.4, -0.6, -0.7])
    vc.set_up([0, 0, 1])
    vis.poll_events(); vis.update_renderer()
    vis.capture_screen_image(out_png, do_render=True)
    vis.destroy_window()
    return True

for fw, path in MAPS.items():
    if not os.path.exists(path):
        print(f"  missing {path}"); continue
    out = f"{OUT}/{SCENE}_{fw}_map.png"
    if render(path, out):
        print(f"saved {out}")

print("done")
#!/usr/bin/env python3
"""Subscribe to OctoMap's occupied-cell-centers and save to PLY.
Run while run_octomap.sh is live (after the bag finishes)."""
import sys
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
from sensor_msgs.msg import PointCloud2
from sensor_msgs_py import point_cloud2
from plyfile import PlyData, PlyElement

OUT = sys.argv[1] if len(sys.argv) > 1 else \
    "/home/ba7rouch/Documents/GitHub/COGAR_3D_Mapping_with_G1_EDU_in_Isaac-Sim/maps/simple_room/octomap/octomap_cloud.ply"

class Grab(Node):
    def __init__(self):
        super().__init__('octomap_grab')
        qos = QoSProfile(depth=1)
        qos.reliability = ReliabilityPolicy.RELIABLE
        qos.durability = DurabilityPolicy.VOLATILE
        self.sub = self.create_subscription(
            PointCloud2, '/octomap_point_cloud_centers', self.cb, qos)
        self.done = False
        self.get_logger().info('waiting for /octomap_point_cloud_centers ...')

    def cb(self, msg):
        pts = np.array([[p[0], p[1], p[2]]
                        for p in point_cloud2.read_points(
                            msg, field_names=('x','y','z'), skip_nans=True)],
                       dtype=np.float64)
        self.get_logger().info(f'got {len(pts)} points')
        verts = np.array([tuple(p) for p in pts],
                         dtype=[('x','f4'),('y','f4'),('z','f4')])
        PlyData([PlyElement.describe(verts,'vertex')]).write(OUT)
        self.get_logger().info(f'saved {OUT}')
        self.done = True

def main():
    rclpy.init()
    n = Grab()
    while rclpy.ok() and not n.done:
        rclpy.spin_once(n, timeout_sec=1.0)
    n.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
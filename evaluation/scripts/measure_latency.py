#!/usr/bin/env python3
"""Measure map-update latency on a topic. Waits for the topic to appear,
then logs inter-message intervals until Ctrl-C.
Usage:
  SCENE=warehouse python3 measure_latency.py /nvblox_node/mesh NVBlox
Start this, THEN start the framework+bag. It will wait, then time.
"""
import os, sys, csv, time
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy, HistoryPolicy
from rosidl_runtime_py.utilities import get_message as get_msg_type

REPO = "/home/ba7rouch/Documents/GitHub/COGAR_3D_Mapping_with_G1_EDU_in_Isaac-Sim"
SCENE = os.environ.get("SCENE", "simple_room")
TOPIC = sys.argv[1] if len(sys.argv) > 1 else "/nvblox_node/mesh"
NAME  = sys.argv[2] if len(sys.argv) > 2 else "framework"
RESULTS = f"{REPO}/evaluation/results"
os.makedirs(RESULTS, exist_ok=True)

class Timer(Node):
    def __init__(self):
        super().__init__('latency_timer')
        self.times = []
        self.sub = None
        self.qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE,
                              durability=DurabilityPolicy.VOLATILE,
                              history=HistoryPolicy.KEEP_LAST)
        # poll for the topic every 0.5s until it appears, then subscribe
        self.timer = self.create_timer(0.5, self._try_subscribe)
        self.get_logger().info(f"waiting for {TOPIC} to appear ...")

    def _try_subscribe(self):
        if self.sub is not None:
            return
        types = dict(self.get_topic_names_and_types())
        if TOPIC in types:
            msg_type = get_msg_type(types[TOPIC][0])
            self.sub = self.create_subscription(msg_type, TOPIC, self.cb, self.qos)
            self.get_logger().info(f"subscribed to {TOPIC} — timing now. Ctrl-C when bag done.")

    def cb(self, msg):
        self.times.append(time.monotonic())

def main():
    rclpy.init()
    n = Timer()
    try:
        rclpy.spin(n)
    except KeyboardInterrupt:
        pass
    t = np.array(n.times)
    try:
        n.destroy_node()
        rclpy.shutdown()
    except Exception:
        pass
    if len(t) < 2:
        print(f"\n[{NAME}] only {len(t)} messages — not enough to time.")
        print("  (Make sure the framework is publishing this topic while timing.)")
        return
    dt = np.diff(t)
    rate = 1.0/dt
    print(f"\n=== {NAME} @ {TOPIC} (SCENE={SCENE}) ===")
    print(f"  messages:        {len(t)}")
    print(f"  mean interval:   {dt.mean()*1000:.1f} ms  ({rate.mean():.2f} Hz)")
    print(f"  median interval: {np.median(dt)*1000:.1f} ms  ({1/np.median(dt):.2f} Hz)")
    print(f"  max interval:    {dt.max()*1000:.1f} ms  (worst stall)")
    print(f"  min interval:    {dt.min()*1000:.1f} ms")
    csv_path = f"{RESULTS}/{SCENE}_latency.csv"
    new = not os.path.exists(csv_path)
    with open(csv_path, "a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["framework","topic","n_msgs","mean_ms","median_ms","max_ms","mean_hz"])
        w.writerow([NAME, TOPIC, len(t), round(dt.mean()*1000,1),
                    round(np.median(dt)*1000,1), round(dt.max()*1000,1),
                    round(rate.mean(),2)])
    print(f"  saved -> {csv_path}")

if __name__ == "__main__":
    main()
"""
Motion script for G1 EDU mapping.
Moves the robot in a 0.5m horizontal circle for 30 seconds.
Run from Isaac Sim's Script Editor while simulation is playing.
"""
import asyncio
import math
import omni.usd
from pxr import Gf, UsdGeom

ROBOT_PATH = "/World/g1_29dof_with_hand_rev_1_0_physics"
RADIUS = 0.5
DURATION = 30.0
HZ = 30

async def move_g1_in_circle():
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(ROBOT_PATH)
    if not prim.IsValid():
        print(f"[ERROR] Prim not found: {ROBOT_PATH}")
        return

    xform = UsdGeom.Xformable(prim)
    translate_op = None
    for op in xform.GetOrderedXformOps():
        if op.GetOpName() == "xformOp:translate":
            translate_op = op
            break
    if translate_op is None:
        print("[ERROR] G1 has no translate op")
        return

    home_pos = translate_op.Get()
    cx, cy, cz = home_pos
    print(f"[INFO] Home position: ({cx:.2f}, {cy:.2f}, {cz:.2f})")

    t0 = asyncio.get_event_loop().time()
    dt = 1.0 / HZ

    try:
        while True:
            t = asyncio.get_event_loop().time() - t0
            if t > DURATION:
                break
            angle = 2.0 * math.pi * (t / DURATION)
            x = cx + RADIUS * math.cos(angle)
            y = cy + RADIUS * math.sin(angle)
            translate_op.Set(Gf.Vec3d(x, y, cz))
            await asyncio.sleep(dt)
    finally:
        translate_op.Set(home_pos)
        print("[INFO] Reset to home position.")

asyncio.ensure_future(move_g1_in_circle())
print("[INFO] G1 motion started (translate only).")

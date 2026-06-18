"""
Ultra-Slow 360° rotation for G1 EDU mapping (Focus on Walls).
- G1 stays at home position (0, 0, 0)
- Rotates 360° around Z axis over 150 seconds (2.5 mins)
- No pitch, skips floor/ceiling overhead to save GPU memory.
"""
import asyncio
import omni.usd
from pxr import Gf, UsdGeom

ROBOT_PATH = "/World/g1_29dof_with_hand_rev_1_0_physics"

HOME_Z = 0.0
DURATION = 150.0   # 2.5 minutes for a full 360° rotation (Ultra-slow)
HZ = 30

async def rotate_g1_slow_walls():
    stage = omni.usd.get_context().get_stage()
    prim = stage.GetPrimAtPath(ROBOT_PATH)
    if not prim.IsValid():
        print("[ERROR] G1 prim not found")
        return

    xform = UsdGeom.Xformable(prim)
    translate_op = None
    rotate_op = None
    for op in xform.GetOrderedXformOps():
        if op.GetOpName() == "xformOp:translate":
            translate_op = op
        elif op.GetOpName() == "xformOp:rotateXYZ":
            rotate_op = op

    if not translate_op or not rotate_op:
        print("[ERROR] Missing translate or rotateXYZ op")
        return

    # Lock position at home
    translate_op.Set(Gf.Vec3d(0, 0, HOME_Z))
    rotate_op.Set(Gf.Vec3f(0, 0, 0))
    await asyncio.sleep(1.0)
    print("[INFO] Starting ultra-slow 360° rotation (2.5 mins) for wall mapping...")

    dt = 1.0 / HZ
    t0 = asyncio.get_event_loop().time()

    while True:
        t = asyncio.get_event_loop().time() - t0
        if t >= DURATION:
            break
        f = t / DURATION
        yaw = 360.0 * f  # 0 → 360 degrees very slowly
        translate_op.Set(Gf.Vec3d(0, 0, HOME_Z))  # keep position locked
        rotate_op.Set(Gf.Vec3f(0, 0, yaw))
        await asyncio.sleep(dt)

    # Reset to initial yaw
    translate_op.Set(Gf.Vec3d(0, 0, HOME_Z))
    rotate_op.Set(Gf.Vec3f(0, 0, 0))
    print("[INFO] Done. Wall mapping complete.")

asyncio.ensure_future(rotate_g1_slow_walls())
print("[INFO] G1 ultra-slow rotation started.")
"""
Cleanup utility for G1 EDU.
Removes the rogue xformOp:rotateXYZ that causes physics to fall.
Resets translate to (0, 0, 1).
"""
import omni.usd
from pxr import Usd, UsdGeom, Gf

ROBOT_PATH = "/World/g1_29dof_with_hand_rev_1_0_physics"

stage = omni.usd.get_context().get_stage()
prim = stage.GetPrimAtPath(ROBOT_PATH)

if not prim.IsValid():
    print("[ERROR] Prim not found")
else:
    xform = UsdGeom.Xformable(prim)

    print("[BEFORE] xform ops:")
    for op in xform.GetOrderedXformOps():
        print(f"  {op.GetOpName()} = {op.Get()}")

    rotate_xyz_attr = prim.GetAttribute("xformOp:rotateXYZ")
    if rotate_xyz_attr.IsValid():
        prim.RemoveProperty("xformOp:rotateXYZ")
        print("[INFO] Removed xformOp:rotateXYZ")

    current_order = xform.GetXformOpOrderAttr().Get()
    if current_order:
        new_order = [op for op in current_order if op != "xformOp:rotateXYZ"]
        xform.GetXformOpOrderAttr().Set(new_order)

    translate_op = None
    for op in xform.GetOrderedXformOps():
        if op.GetOpName() == "xformOp:translate":
            translate_op = op
            break
    if translate_op:
        translate_op.Set(Gf.Vec3d(0.0, 0.0, 1.0))
        print("[INFO] Reset translate to (0, 0, 1)")

    print("[AFTER] xform ops:")
    for op in xform.GetOrderedXformOps():
        print(f"  {op.GetOpName()} = {op.Get()}")
    print("[DONE] G1 xform cleaned up.")

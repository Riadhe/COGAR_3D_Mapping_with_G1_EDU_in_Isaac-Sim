"""
Find which prim in the G1 USD has the ArticulationRootAPI applied.

Run inside Isaac Sim via: Window -> Script Editor, paste, click Run.

Why this exists:
When auto-generating the Joint States OmniGraph, the dialog asks for the
"Articulation Root" prim. If you point it at the top-level Xform but the
ArticulationRootAPI is actually applied to a deeper prim (e.g. `pelvis`),
the graph generates without a joint-reader node and no `/joint_states`
topic is published.

This script walks the G1 subtree and prints every prim that has the
ArticulationRootAPI, so you know exactly which prim path to use.

For our G1 USD: the API is on `/World/g1_29dof_with_hand_rev_1_0_physics/pelvis`.
"""
from pxr import UsdPhysics, Usd
import omni.usd

stage = omni.usd.get_context().get_stage()
root = stage.GetPrimAtPath("/World/g1_29dof_with_hand_rev_1_0_physics")

print("Searching for ArticulationRoot APIs under G1...")
print("---")
found = []
for prim in Usd.PrimRange(root):
    if prim.HasAPI(UsdPhysics.ArticulationRootAPI):
        found.append(str(prim.GetPath()))
        print(f"FOUND: {prim.GetPath()}")
print("---")
print(f"Total articulation roots found: {len(found)}")

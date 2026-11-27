"""Puts the left hand on the pistol's handle in the seven pistol animations.

Run in Blender with the work file open ("Desert FPS Weapons (work).blend"), for example through the Blender
MCP. It uses the helpers kept in the file's text block claude_fx.py.

At every key where the left hand was on the pistol it solves the left arm again: the hand's end goes to TARGET
in the pistol's own space (x along the barrel, y up, z to the right), turned as the right hand is, mirrored in
the pistol's middle plane. Keys where the hand is away (taking the magazine in the reload) are left alone.
The versions before are kept as "<name> (one hand under)".

Afterwards: export each with export_action (the priorities are below), import them into
ReplicatedStorage.DesertFpsAnimations (build/11_import_animations.luau), export each KeyframeSequence as .rbxm
and upload it, and put the new ids in AnimationConfig.
"""
import bpy
from mathutils import Matrix, Vector

ns = {}
exec(bpy.data.texts["claude_fx.py"].as_string(), ns)
A, rig = ns["A"], ns["rig"]
set_act, sample, apply_pose = ns["set_act"], ns["sample"], ns["apply_pose"]
ik_arm, set_hand, delta = ns["ik_arm"], ns["set_hand"], ns["delta"]
continuity, finalize = ns["continuity"], ns["finalize"]

gun = bpy.data.objects["W_pistol"]
GL = bpy.data.objects["GripLeft"]
scene = bpy.context.scene

TARGET = (0.06, -0.20, -0.10)             # where the left hand's end goes, in the pistol's own space
OLD = Vector((0.02, -0.22, -0.20))        # where it used to be: how a key with the hand on the pistol is told
LEFT = ("LeftSFK", "LeftLAFK", "LeftHFK")
MIRROR = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, 1)))
# name, priority, file, and whether the head is left out (the first-person arms have none)
ACTIONS = [
    ("FPS Pistol Hold", "Action", "fps_pistol_hold", False),
    ("FPS Pistol Fire", "Action2", "fps_pistol_fire", False),
    ("FPS Pistol Reload", "Action2", "fps_pistol_reload", False),
    ("FPV Pistol Idle", "Idle", "fpv_pistol_idle", True),
    ("FPV Pistol Equip", "Action", "fpv_pistol_equip", True),
    ("FPV Pistol Fire", "Action2", "fpv_pistol_fire", True),
    ("FPV Pistol Reload", "Action", "fpv_pistol_reload", True),
]
# Keys of the left arm to take out: in the first-person reload the hand held on through the first key and
# then swept across the view. Without the key it leaves for the magazine at once.
DROP = {"FPV Pistol Reload": [9]}


def on_gun(W):
    return ((W.inverted() @ GL.matrix_world.translation) - OLD).length < 0.05


def regrip(p):
    """Pose p with the left hand on the handle. Returns how far its end is from TARGET."""
    apply_pose(p)
    W = gun.matrix_world.copy()
    n = (W.to_3x3() @ Vector((0, 0, 1))).normalized()
    across = Matrix.Identity(3) - 2 * Matrix((n * n.x, n * n.y, n * n.z))
    turned = across @ delta(rig, "RightHand") @ MIRROR
    elbow = rig.pose.bones["RightLowerArm"].head.copy()
    goal = elbow - 2 * ((elbow - W.translation).dot(n)) * n
    target = W @ Vector(TARGET)
    set_hand(p, "Left", turned)
    for _ in range(4):
        apply_pose(p)
        wrist, grip = rig.pose.bones["LeftHand"].head.copy(), GL.matrix_world.translation.copy()
        ik_arm(p, "Left", target - (grip - wrist), goal, wrist=True)
        set_hand(p, "Left", turned)
    apply_pose(p)
    return (target - GL.matrix_world.translation).length


def regrip_action(name):
    a = bpy.data.actions[name]
    if not bpy.data.actions.get(name + " (one hand under)"):
        before = a.copy()
        before.name = name + " (one hand under)"
        before.use_fake_user = True
    frames = sorted({int(round(k.co.x)) for fc in a.fcurves if any(b in fc.data_path for b in LEFT)
                     for k in fc.keyframe_points})
    solved = {}
    set_act(A, None)                      # an action on the armature would undo each pose as it is solved
    for f in frames:
        p = sample(name, f)
        apply_pose(p)
        if on_gun(gun.matrix_world):
            solved[f] = (p, regrip(p))
    set_act(A, a)
    for f, (p, _) in solved.items():
        for b in LEFT:
            q, l = p[b]
            bone = A.pose.bones[b]
            bone.rotation_quaternion, bone.location = q, l
            bone.keyframe_insert("rotation_quaternion", frame=f)
            bone.keyframe_insert("location", frame=f)
    for f in DROP.get(name, []):
        for fc in a.fcurves:
            if any(b in fc.data_path for b in LEFT):
                for k in list(fc.keyframe_points):
                    if abs(k.co.x - f) < 0.5:
                        fc.keyframe_points.remove(k)
                fc.update()
    continuity(a)
    finalize(a, a["frame_range"][0], a["frame_range"][1], a["loop"])
    return sorted(solved), max(err for _, err in solved.values())


for name, _, _, _ in ACTIONS:
    print(name, *regrip_action(name))

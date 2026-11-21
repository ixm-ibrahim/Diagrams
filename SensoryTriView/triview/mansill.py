"""The generated man on the mannequin's joints (rung 3).

The mannequin's motion is 19 joint points and a head frame, baked on Empties named Man_<joint> in the scene of record
(triview/body.py). The man's skeleton is tied to those Empties by constraints, so he takes the mannequin's pose at
every frame and nothing is keyframed: his pelvis at the pelvis point, his trunk aimed from it at the neck point, his
head exactly where the mannequin's head is and turned as it is (so his eyes are where the First-Person camera is),
every limb segment from its joint point to the next. A segment is stretched or shortened along its length to reach,
because the mannequin's limbs are not his: its upper arm is 16 percent longer than his, its shin 10 percent shorter.

Stand-in or staying: the tie to the 19 points is this rung's way of standing him at the sill ("for this rung it is
fine, we can do better later", his word of 2026-11-19). Rung 4 brings his own performance and with it his own limbs.

His own file has him facing -Y with his left at +X; the mannequin's frames face +X with left at +Y: C turns one into
the other.
"""
import math

import bpy
from mathutils import Matrix, Vector

from . import man

C = Matrix.Rotation(math.radians(90.0), 4, "Z")

# a limb segment: (the bone that carries it, the bone whose tail is its far end, the joint point that end goes to)
SEGMENTS = (
    ("pelvis.{s}", "pelvis.{s}", "hip_{t}"),
    ("upperleg01.{s}", "upperleg02.{s}", "knee_{t}"),
    ("lowerleg01.{s}", "lowerleg02.{s}", "ankle_{t}"),
    ("shoulder01.{s}", "shoulder01.{s}", "shoulder_{t}"),
    ("upperarm01.{s}", "upperarm02.{s}", "elbow_{t}"),
    ("lowerarm01.{s}", "lowerarm02.{s}", "wrist_{t}"),
)
AIMS = (("foot.{s}", "toe_{t}"), ("wrist.{s}", "hand_{t}"))
SIDES = (("L", "l"), ("R", "r"))


def append_man(blend, scene):
    """Bring him from his own file into this scene. Returns his skeleton and his objects."""
    with bpy.data.libraries.load(str(blend), link=False) as (src, dst):
        dst.objects = [n for n in src.objects if n.startswith("Man3_")]
    obs = [o for o in dst.objects if o is not None]
    for o in obs:
        scene.collection.objects.link(o)
    rig = next(o for o in obs if o.type == "ARMATURE")
    return rig, obs


def straighten(rig):
    """Each limb is two bones in a row in the generator's skeleton, with a small kink between them. Put the joint
    between them on the straight line, so that aiming the first bone aims the whole segment."""
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="EDIT")
    eb = rig.data.edit_bones
    for side, _ in SIDES:
        for a, b in (("upperarm01", "upperarm02"), ("lowerarm01", "lowerarm02"), ("upperleg01", "upperleg02"), ("lowerleg01", "lowerleg02")):
            A, B = eb[f"{a}.{side}"], eb[f"{b}.{side}"]
            start, end = A.head.copy(), B.tail.copy()
            share = (A.tail - start).length / max((A.tail - start).length + (end - B.head).length, 1e-9)
            mid = start.lerp(end, share)
            A.tail = mid
            B.head = mid
    bpy.ops.object.mode_set(mode="OBJECT")


def _empty(name, scene, parent=None, basis=None):
    e = bpy.data.objects.new(name, None)
    e.empty_display_size = 0.03
    scene.collection.objects.link(e)
    if parent is not None:
        e.parent = parent
    if basis is not None:
        e.matrix_basis = basis
    return e


def _palm_axis(rig, side):
    """Which of the hand bone's own axes points out of the palm, in the rest pose: 'TRACK_X', 'TRACK_NEGATIVE_Z' ..."""
    b = rig.data.bones
    w = b[f"wrist.{side}"]
    along = (w.tail_local - w.head_local).normalized()
    spread = (b[f"finger5-1.{side}"].head_local - b[f"finger2-1.{side}"].head_local).normalized()
    n = along.cross(spread).normalized()
    # in the rest pose the palms face in toward the thighs: the left hand's toward -X, the right hand's toward +X
    inward = Vector((-1.0, 0.0, 0.0)) if side == "L" else Vector((1.0, 0.0, 0.0))
    if n.dot(inward) < 0.0:
        n = -n
    local = w.matrix_local.to_3x3().inverted() @ n
    best = max((("TRACK_X", local.x), ("TRACK_NEGATIVE_X", -local.x), ("TRACK_Z", local.z), ("TRACK_NEGATIVE_Z", -local.z)), key=lambda kv: kv[1])
    return best[0]


def place(scene, rig, prefix="Man_"):
    """Tie his skeleton to the mannequin's joint Empties. Returns the helpers made."""
    E = lambda n: bpy.data.objects[prefix + n]
    bones, pose = rig.data.bones, rig.pose.bones
    pelvis_rest = bones["root"].tail_local.copy()
    neck_rest = (bones["clavicle.L"].head_local + bones["clavicle.R"].head_local) * 0.5      # the base of his neck, between the collar bones
    head_rest = man.head_centre(rig)
    helpers = {}

    # the pelvis frame: at the pelvis point, turned as the torso, then leaned so that its up runs to the neck point
    P = _empty("M3_pelvis", scene)
    c = P.constraints.new("COPY_LOCATION"); c.target = E("pelvis")
    c = P.constraints.new("COPY_ROTATION"); c.target = E("torso")
    c = P.constraints.new("DAMPED_TRACK"); c.target = E("neck"); c.track_axis = "TRACK_Z"
    v = (C.to_3x3() @ (neck_rest - pelvis_rest)).normalized()
    align = v.rotation_difference(Vector((0.0, 0.0, 1.0))).to_matrix().to_4x4()
    helpers["root"] = _empty("M3_root", scene, P, align @ C @ Matrix.Translation(-pelvis_rest) @ bones["root"].matrix_local)
    # the head: exactly the mannequin's
    H = E("head")
    place_head = C @ Matrix.Translation(-head_rest)
    helpers["head"] = _empty("M3_head", scene, H, place_head @ bones["head"].matrix_local)
    helpers["headbase"] = _empty("M3_headbase", scene, H, place_head @ Matrix.Translation(bones["head"].head_local))
    for bone, key in (("root", "root"), ("head", "head")):
        c = pose[bone].constraints.new("COPY_TRANSFORMS")
        c.target = helpers[key]
        c.owner_space, c.target_space = "WORLD", "WORLD"
    bones["head"].inherit_scale = "NONE"
    # the neck from the trunk to the head's base
    bones["neck01"].inherit_scale = "NONE"
    c = pose["neck01"].constraints.new("STRETCH_TO")
    c.target = helpers["headbase"]
    c.rest_length = (bones["head"].head_local - bones["neck01"].head_local).length
    c.volume = "NO_VOLUME"
    # the limbs, joint point to joint point
    for side, t in SIDES:
        for first, last, joint in SEGMENTS:
            fb, lb = bones[first.format(s=side)], bones[last.format(s=side)]
            fb.inherit_scale = "NONE"
            c = pose[fb.name].constraints.new("STRETCH_TO")
            c.target = E(joint.format(t=t))
            c.rest_length = (lb.tail_local - fb.head_local).length
            c.volume = "NO_VOLUME"
        for bone, joint in AIMS:
            b = bones[bone.format(s=side)]
            b.inherit_scale = "NONE"
            c = pose[b.name].constraints.new("DAMPED_TRACK")
            c.target = E(joint.format(t=t))
            c.track_axis = "TRACK_Y"
        # the palm turned to face down, as a hand laid on a sill or a table is
        down = _empty(f"M3_palm_{t}", scene, E(f"hand_{t}"), Matrix.Translation((0.0, 0.0, -1.0)))
        down.matrix_parent_inverse = Matrix.Identity(4)
        c = pose[f"wrist.{side}"].constraints.new("LOCKED_TRACK")
        c.target = down
        c.lock_axis = "LOCK_Y"
        c.track_axis = _palm_axis(rig, side)
        helpers[f"palm_{t}"] = down
    # the eyes look where the First-Person camera looks (the eyes' own turning in the head, triview/body.py)
    cam = bpy.data.objects.get("Cam_First")
    if cam is not None:
        gaze = _empty("M3_gaze", scene, cam, Matrix.Translation((0.0, 0.0, -3.0)))
        for side, _ in SIDES:
            c = pose[f"eye.{side}"].constraints.new("DAMPED_TRACK")
            c.target = gaze
            c.track_axis = "TRACK_Y"
        helpers["gaze"] = gaze
    return helpers


def hide_mannequin(scene):
    """The mannequin stays in the file (the engine and the eyes' scans read it) and out of this rung's pictures."""
    hidden = []
    for ob in scene.objects:
        if ob.type == "MESH" and ob.name.startswith(("ManJ_", "ManL_", "ManO_", "Man_Head")):
            ob.hide_render = True
            hidden.append(ob.name)
    return hidden


def report(scene, rig, prefix="Man_"):
    """How far his joints stand from the mannequin's points at the scene's frame, in millimetres."""
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    r = rig.evaluated_get(dg)
    out = {}
    pairs = [("pelvis", "root", 1.0), ("head (eyes)", None, 0.0)]
    for side, t in SIDES:
        pairs += [(f"hip_{t}", f"upperleg01.{side}", 0.0), (f"knee_{t}", f"lowerleg01.{side}", 0.0), (f"ankle_{t}", f"foot.{side}", 0.0),
                  (f"shoulder_{t}", f"upperarm01.{side}", 0.0), (f"elbow_{t}", f"lowerarm01.{side}", 0.0), (f"wrist_{t}", f"wrist.{side}", 0.0)]
    for joint, bone, at in pairs:
        if bone is None:
            eyes = (r.matrix_world @ ((r.pose.bones["eye.L"].head + r.pose.bones["eye.R"].head) * 0.5))
            cam = bpy.data.objects.get("Cam_First")
            if cam is not None:
                out["eyes to the First-Person camera"] = round((eyes - cam.evaluated_get(dg).matrix_world.translation).length * 1000.0, 1)
            continue
        pb = r.pose.bones[bone]
        p = r.matrix_world @ (pb.tail if at else pb.head)
        target = bpy.data.objects[prefix + joint].evaluated_get(dg).matrix_world.translation
        out[joint] = round((p - target).length * 1000.0, 1)
    return out

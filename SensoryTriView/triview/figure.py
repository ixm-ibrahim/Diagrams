"""The stand-in mannequin: spheres at the joints and cylinders between them.

Poses are dictionaries of joint positions in the figure's own frame: x forward (the way
it faces), y to its left, z up, metres, the floor at z = 0. A pose is placed in a scene
by a location and a yaw, and the same builder makes the man in the room, the ghost in
the dark and the small simulated body inside the skull.
"""
import math

from mathutils import Matrix, Vector

from . import geo

# bone: (start joint, end joint, radius at start, radius at end, material group)
BONES = [
    ("pelvis", "chest", 0.13, 0.15, "cloth"),
    ("chest", "neck", 0.10, 0.06, "cloth"),
    ("neck", "head_base", 0.05, 0.05, "skin"),
    ("shoulder_l", "shoulder_r", 0.07, 0.07, "cloth"),
    ("shoulder_l", "elbow_l", 0.05, 0.042, "cloth"),
    ("shoulder_r", "elbow_r", 0.05, 0.042, "cloth"),
    ("elbow_l", "wrist_l", 0.04, 0.03, "skin"),
    ("elbow_r", "wrist_r", 0.04, 0.03, "skin"),
    ("wrist_l", "hand_l", 0.032, 0.022, "skin"),
    ("wrist_r", "hand_r", 0.032, 0.022, "skin"),
    ("hip_l", "knee_l", 0.078, 0.062, "cloth"),
    ("hip_r", "knee_r", 0.078, 0.062, "cloth"),
    ("knee_l", "ankle_l", 0.058, 0.04, "skin"),
    ("knee_r", "ankle_r", 0.058, 0.04, "skin"),
    ("ankle_l", "toe_l", 0.04, 0.025, "skin"),
    ("ankle_r", "toe_r", 0.04, 0.025, "skin"),
]

# joint: (radius, material group); the head is built apart with its own scale
JOINTS = {
    "pelvis": (0.12, "cloth"),
    "chest": (0.12, "cloth"),
    "neck": (0.055, "skin"),
    "shoulder_l": (0.065, "cloth"), "shoulder_r": (0.065, "cloth"),
    "elbow_l": (0.045, "skin"), "elbow_r": (0.045, "skin"),
    "wrist_l": (0.034, "skin"), "wrist_r": (0.034, "skin"),
    "hand_l": (0.045, "skin"), "hand_r": (0.045, "skin"),
    "hip_l": (0.085, "cloth"), "hip_r": (0.085, "cloth"),
    "knee_l": (0.065, "skin"), "knee_r": (0.065, "skin"),
    "ankle_l": (0.045, "skin"), "ankle_r": (0.045, "skin"),
    "toe_l": (0.03, "skin"), "toe_r": (0.03, "skin"),
}

HEAD_RADIUS = 0.105
HEAD_SCALE = (1.0, 0.95, 1.2)

# Stand-in organs for the senses (rung 2p, his specification of 2026-11-12): the ears and the eyes on the head, the
# heart and the lungs in the chest, each a sphere riding the head's frame (x forward, y left, z up, from the head's
# centre) or the torso's (the same axes from the chest joint). part: (what it rides, its centre, its radius, its
# scale along its own axes, its material group). The ears stand out of the head's sides; the eyes sit at the head's
# surface where the First-Person camera is, and are hidden from every camera at the eyes as the head is; the heart
# and the lungs lie inside the chest, where no ray reaches them. Rung 3 gives the figure a real body
ORGANS = {
    "ear_l": ("head", (0.0, 0.098, 0.0), 0.03, (0.75, 0.3, 1.0), "skin"),
    "ear_r": ("head", (0.0, -0.098, 0.0), 0.03, (0.75, 0.3, 1.0), "skin"),
    "eye_l": ("head", (0.092, 0.032, 0.018), 0.013, (1.0, 1.0, 1.0), "skin"),
    "eye_r": ("head", (0.092, -0.032, 0.018), 0.013, (1.0, 1.0, 1.0), "skin"),
    "heart": ("torso", (0.025, 0.0, -0.035), 0.04, (0.9, 1.0, 1.2), "heart"),
    "lung_l": ("torso", (0.0, 0.065, 0.0), 0.038, (1.0, 0.9, 2.0), "lung"),
    "lung_r": ("torso", (0.0, -0.065, 0.0), 0.038, (1.0, 0.9, 2.0), "lung"),
}


def standing():
    """Upright, arms a little out from the sides: the ghost's pose."""
    return {
        "head": (0.0, 0.0, 1.63), "eye": (0.09, 0.0, 1.65),
        "neck": (0.0, 0.0, 1.50), "chest": (0.0, 0.0, 1.40), "pelvis": (0.0, 0.0, 0.96),
        "shoulder_l": (0.0, 0.20, 1.46), "shoulder_r": (0.0, -0.20, 1.46),
        "elbow_l": (0.02, 0.29, 1.15), "elbow_r": (0.02, -0.29, 1.15),
        "wrist_l": (0.05, 0.35, 0.88), "wrist_r": (0.05, -0.35, 0.88),
        "hand_l": (0.06, 0.38, 0.75), "hand_r": (0.06, -0.38, 0.75),
        "hip_l": (0.0, 0.11, 0.93), "hip_r": (0.0, -0.11, 0.93),
        "knee_l": (0.0, 0.12, 0.50), "knee_r": (0.0, -0.12, 0.50),
        "ankle_l": (0.0, 0.12, 0.08), "ankle_r": (0.0, -0.12, 0.08),
        "toe_l": (0.20, 0.12, 0.02), "toe_r": (0.20, -0.12, 0.02),
    }


def sitting(seat_height):
    """On the edge of a seat of the given height, feet on the floor, head bowed to the
    right hand, which rests on the right thigh holding the phone."""
    h = seat_height
    return {
        "pelvis": (0.0, 0.0, h + 0.09),
        "hip_l": (0.02, 0.11, h + 0.07), "hip_r": (0.02, -0.11, h + 0.07),
        "knee_l": (0.46, 0.13, h + 0.04), "knee_r": (0.46, -0.13, h + 0.04),
        "ankle_l": (0.50, 0.13, 0.08), "ankle_r": (0.50, -0.13, 0.08),
        "toe_l": (0.68, 0.13, 0.02), "toe_r": (0.68, -0.13, 0.02),
        "chest": (0.06, 0.0, h + 0.52), "neck": (0.09, 0.0, h + 0.62),
        "head": (0.16, 0.0, h + 0.72), "eye": (0.24, 0.0, h + 0.70),
        "shoulder_l": (0.07, 0.20, h + 0.57), "shoulder_r": (0.07, -0.20, h + 0.57),
        "elbow_l": (0.12, 0.26, h + 0.32), "elbow_r": (0.12, -0.26, h + 0.32),
        "wrist_l": (0.30, 0.20, h + 0.16), "wrist_r": (0.30, -0.19, h + 0.17),
        "hand_l": (0.38, 0.17, h + 0.13), "hand_r": (0.37, -0.15, h + 0.15),
    }


def placement(location, yaw_deg=0.0):
    return Matrix.Translation(Vector(location)) @ Matrix.Rotation(math.radians(yaw_deg), 4, "Z")


def phone_matrix(pose, place, tilt_deg=-22.0, lift=0.045, forward=0.03):
    """Where the phone sits in the right hand: on the palm, long axis forward, tilted so the
    far end rises and the screen faces back up toward the eyes. Returns a world matrix whose
    origin is the phone's centre and whose +z is the screen's normal."""
    hand = Vector(pose["hand_r"])
    local = Matrix.Translation(hand + Vector((forward, 0.0, lift))) @ Matrix.Rotation(math.radians(tilt_deg), 4, "Y")
    return place @ local


def build(name, pose, materials, place, collection=None, parent=None, overrides=None,
          scale=1.0, segments=16):
    """Build the mannequin.

    materials: {"skin": mat, "cloth": mat, ...}; overrides maps a part name (a joint, or a bone
    by its end joint) to a material group, e.g. {"hand_r": "sight"}. scale multiplies radii
    only (positions come scaled through the parent or the pose). Returns (body, head, points)
    where points are the joints in the parent's frame after placement.
    """
    overrides = overrides or {}
    pose = dict(pose)
    if "head_base" not in pose:
        # the neck meets the head at its surface, not its centre, so nothing pokes into the skull
        head, neck = Vector(pose["head"]), Vector(pose["neck"])
        pose["head_base"] = tuple(head + (neck - head).normalized() * (HEAD_RADIUS * scale * 0.85))
    groups = list(materials.keys())
    mats = [materials[g] for g in groups]
    idx = {g: i for i, g in enumerate(groups)}

    def group_of(part, default):
        return overrides.get(part, default)

    bm = geo.new_bmesh()
    for a, b, ra, rb, g in BONES:
        gi = idx[group_of(b, g)]
        geo.add_segment(bm, pose[a], pose[b], ra * scale, rb * scale, gi, segments=segments)
    for j, (r, g) in JOINTS.items():
        gi = idx[group_of(j, g)]
        geo.add_sphere(bm, pose[j], r * scale, gi, segments=segments, rings=max(8, segments // 2))
    body = geo.finish(bm, name, mats, collection, parent, matrix=place)

    # The head is always its own object: the First-Person camera sits inside it and hides it,
    # and the True-Person camera will one day pass through it.
    bm = geo.new_bmesh()
    geo.add_sphere(bm, pose["head"], HEAD_RADIUS * scale, idx[group_of("head", "skin")],
                   scale=HEAD_SCALE, segments=segments * 2, rings=segments)
    head = geo.finish(bm, f"{name}_Head", mats, collection, parent, matrix=place)

    points = {k: place @ Vector(v) for k, v in pose.items()}
    return body, head, points


def crown(pose, place):
    """The top of the head in the placed frame."""
    return place @ (Vector(pose["head"]) + Vector((0.0, 0.0, HEAD_RADIUS * HEAD_SCALE[2])))

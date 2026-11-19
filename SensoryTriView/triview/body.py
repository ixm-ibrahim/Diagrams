"""The stand-in figure animated over the whole chain.

The road chosen: keyframed Empties at the joints, with each limb an object held between
two joints by constraints (Copy Location at one joint, Stretch To the other), and the
head a mesh parented to a head Empty that carries the head's own frame as a rotation.
The whole motion is then plain keyframes on the Empties, which render headless without
Python, and the engine reads the joints and the head frame straight off those Empties,
which is also what it will read off an armature's bones when his performance arrives
in rung 4. An armature would have needed bone rotations solved from joint positions
and an edit-mode pass headless, for no gain in a stand-in.

Motion is built from key poses (joint positions relative to the pelvis in the figure's
own frame, x forward, y left, z up) placed by a location and a rotation, blended in two
ways: 'place' slerps the rotation and lerps the local pose (turns), 'world' lerps the
joints in world space (sitting up, sitting down). Walks are procedural from footfalls
and are blended into the key poses on either side of them over half a second, so the
walk's lean never arrives in one frame.

The head is its own channel of yaw and pitch (HEAD_KEYS). Its frame is levelled to
gravity whenever he is upright, so a key's pitch is a true angle whatever the chest
does, and it follows the torso only as he lies down, where "level" means nothing.

The hand against the sun is solved every frame onto the line from the eyes to the sun
(SHADE), a forearm's length out, with the elbow below and outward, so it covers the sun
in First-Person and sits between the face and the window in Third-Person.

The timeline is rung 2b's (2026-11-07): the alarm's smack sends the phone to the table's
edge, a stretch lying down, a shorter doze, the groggy reach that knocks the phone off,
the rap, the retract and rub, the pick-up from the floor, then the crest at 40 s and
everything after it four seconds later than the concept's first draft. Every second
is a guess; rung 4 replaces them from his performance.
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Quaternion, Vector

from . import anim, geo, tags
from .figure import BONES, JOINTS, HEAD_RADIUS, HEAD_SCALE, ORGANS

JOINT_NAMES = ["pelvis", "chest", "neck", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r",
               "wrist_l", "wrist_r", "hand_l", "hand_r", "hip_l", "hip_r", "knee_l", "knee_r",
               "ankle_l", "ankle_r", "toe_l", "toe_r"]
ALL_JOINTS = JOINT_NAMES + ["head"]
HEAD_FROM_NECK = 0.125     # the head's centre sits this far up the head's own axis from the neck joint
EYE_OFFSET = (0.09, 0.0, 0.015)
EYE_REACH = 35.0           # degrees the eyes turn in the head toward what he looks at; beyond it the head has to turn (a stand-in
                           # bound: the motion's head keys were drawn with the eyes fixed in the head)
GAZE_EASE = 0.15           # seconds a look takes to land on its thing, and to come back to the head's own axis
EAR_OFFSET = 0.095
UPPER_ARM, FOREARM, HAND_LEN = 0.31, 0.27, 0.13   # the mannequin's arm as the poses draw it
THIGH, SHIN, FOOT_LEN = 0.43, 0.42, 0.21
# each limb: root, middle, end, tip, and the three lengths; the middle joint is solved every frame
# so the limbs keep these lengths whatever a pose or a walk asked for (his review of 2026-11-07:
# the arm stretched when it reached for the alarm), the authored middle only giving the bend's side
LIMBS = (
    ("shoulder_l", "elbow_l", "wrist_l", "hand_l", UPPER_ARM, FOREARM, HAND_LEN),
    ("shoulder_r", "elbow_r", "wrist_r", "hand_r", UPPER_ARM, FOREARM, HAND_LEN),
    ("hip_l", "knee_l", "ankle_l", "toe_l", THIGH, SHIN, FOOT_LEN),
    ("hip_r", "knee_r", "ankle_r", "toe_r", THIGH, SHIN, FOOT_LEN),
)
END_T = 116.5              # the last second the schedule holds
WALK_BLEND = 0.5           # seconds a walk is blended into the poses on either side of it

# ---- key poses, local to the pelvis -----------------------------------------------

def _sym(d):
    """Expand entries written once for the right side ('_r') into left and right."""
    out = {}
    for k, v in d.items():
        if k.endswith("_r"):
            out[k] = v
            out[k[:-2] + "_l"] = (v[0], -v[1], v[2])
        else:
            out[k] = v
    return out


STAND_L = _sym({
    "chest": (0.0, 0.0, 0.44), "neck": (0.0, 0.0, 0.54),
    "shoulder_r": (0.0, -0.20, 0.50), "elbow_r": (0.02, -0.25, 0.19),
    "wrist_r": (0.04, -0.27, -0.08), "hand_r": (0.05, -0.28, -0.21),
    "hip_r": (0.0, -0.11, -0.03), "knee_r": (0.01, -0.12, -0.46),
    "ankle_r": (0.0, -0.12, -0.88), "toe_r": (0.20, -0.12, -0.94),
})
STAND_Z = 0.96

SIT_L = _sym({
    "chest": (0.06, 0.0, 0.43), "neck": (0.09, 0.0, 0.53),
    "shoulder_r": (0.07, -0.20, 0.48), "elbow_r": (0.12, -0.26, 0.23),
    "wrist_r": (0.30, -0.19, 0.08), "hand_r": (0.37, -0.15, 0.06),
    "hip_r": (0.02, -0.11, -0.02), "knee_r": (0.46, -0.13, -0.05),
    "ankle_r": (0.50, -0.13, -0.56), "toe_r": (0.68, -0.13, -0.62),
})
SIT_L["wrist_l"] = (0.30, 0.20, 0.07)
SIT_L["hand_l"] = (0.38, 0.17, 0.04)
SIT_Z = 0.64

SIT_UP_L = dict(SIT_L)
SIT_UP_L.update(_sym({
    "chest": (0.0, 0.0, 0.44), "neck": (0.0, 0.0, 0.54),
    "shoulder_r": (0.0, -0.20, 0.50), "elbow_r": (0.05, -0.25, 0.20),
    "wrist_r": (0.28, -0.17, 0.05), "hand_r": (0.36, -0.15, 0.03),
}))

LIE_L = _sym({
    "chest": (0.03, 0.0, 0.44), "neck": (0.06, 0.0, 0.54),
    "shoulder_r": (0.04, -0.20, 0.50), "elbow_r": (0.0, -0.26, 0.20),
    "wrist_r": (-0.02, -0.28, -0.06), "hand_r": (-0.02, -0.29, -0.18),
    "hip_r": (0.0, -0.11, -0.03), "knee_r": (0.08, -0.12, -0.46),
    "ankle_r": (0.03, -0.12, -0.88), "toe_r": (0.20, -0.12, -0.92),
})
LIE_REACH_L = dict(LIE_L)
LIE_REACH_L.update({"elbow_r": (-0.02, -0.51, 0.64), "wrist_r": (-0.07, -0.76, 0.76), "hand_r": (-0.08, -0.84, 0.78)})
# the flick that stops the alarm and sends the phone skidding: the hand a little further and down on the table
LIE_SMACK_L = dict(LIE_REACH_L)
LIE_SMACK_L.update({"wrist_r": (-0.09, -0.80, 0.74), "hand_r": (-0.10, -0.86, 0.74)})
# the stretch lying down: both arms over the head along the pillow, the back arched a little
LIE_OUT_L = dict(LIE_L)
LIE_OUT_L.update(_sym({
    "chest": (0.04, 0.0, 0.44), "neck": (0.07, 0.0, 0.54), "shoulder_r": (0.05, -0.20, 0.51),
    "elbow_r": (0.0, -0.50, 0.58), "wrist_r": (-0.02, -0.76, 0.64), "hand_r": (-0.02, -0.88, 0.68),
}))
LIE_STRETCH_L = dict(LIE_L)
LIE_STRETCH_L.update(_sym({
    "chest": (0.06, 0.0, 0.44), "neck": (0.09, 0.0, 0.54), "shoulder_r": (0.07, -0.20, 0.52),
    "elbow_r": (0.03, -0.26, 0.82), "wrist_r": (0.02, -0.24, 1.08), "hand_r": (0.02, -0.23, 1.21),
}))

# lying on the back, crown to the south: local x (face) is world up, local z (crown) is world south
R_LIE = Matrix(((0.0, -1.0, 0.0), (0.0, 0.0, -1.0), (1.0, 0.0, 0.0)))
LIE_LOC = Vector((0.80, 1.20, 0.65))
SIT_LOC = Vector((1.38, 0.75, SIT_Z))
STAND_BED_LOC = Vector((1.88, 0.75, STAND_Z))
BEDSIDE_LOC = Vector((1.95, 0.75, STAND_Z))
WINDOW_LOC = Vector((3.45, 1.20, STAND_Z))

# halfway up: propped on the right hand on the mattress by his hip, the legs still on the bed
PROP_WORLD = {
    "pelvis": (0.82, 1.18, 0.65), "chest": (0.86, 1.00, 1.02), "neck": (0.88, 0.95, 1.12),
    "shoulder_l": (0.66, 0.98, 1.06), "shoulder_r": (1.06, 0.98, 1.06),
    "elbow_l": (0.60, 1.08, 0.80), "wrist_l": (0.56, 1.16, 0.60), "hand_l": (0.54, 1.22, 0.57),
    "elbow_r": (1.22, 0.76, 0.84), "wrist_r": (1.36, 0.66, 0.66), "hand_r": (1.42, 0.64, 0.60),
    "hip_l": (0.71, 1.18, 0.63), "hip_r": (0.93, 1.18, 0.63),
    "knee_l": (0.70, 1.64, 0.72), "knee_r": (0.94, 1.64, 0.72),
    "ankle_l": (0.70, 2.04, 0.62), "ankle_r": (0.94, 2.04, 0.62),
    "toe_l": (0.70, 2.10, 0.80), "toe_r": (0.94, 2.10, 0.80),
}

# the phone's places: on the table by his pillow, skidded to the table's north edge, on the floor
# in the gap between the table and his leg, face down on the table after the crest
PHONE_TABLE_1 = Matrix.Translation((1.66, 0.42, 0.559)) @ Matrix.Rotation(math.radians(15), 4, "Z")
PHONE_EDGE = Matrix.Translation((1.90, 0.455, 0.559)) @ Matrix.Rotation(math.radians(-8), 4, "Z")
PHONE_FLOOR = Matrix.Translation((1.89, 0.545, 0.004)) @ Matrix.Rotation(math.radians(70), 4, "Z")
PHONE_TABLE_2 = (Matrix.Translation((1.74, 0.38, 0.559)) @ Matrix.Rotation(math.radians(-10), 4, "Z")
                 @ Matrix.Rotation(math.pi, 4, "X"))

# the crest: first light, and his reaction to it. His word of 2026-11-16: the hand against the sun is a reaction to
# the light hitting his eyes, with a realistic reaction time, not an actor who knows the sun is coming. FIRST_LIGHT is
# the second the sun's upper limb clears the range as his eyes have it (the dawn's keys, triview/room.py; the build
# prints the scene's own figure beside it). By reflex his lids begin to shut a tenth of a second on (data/eyes.json:
# shut at 40.43, the closing itself a tenth of a second); his head flinches REACT_HEAD after the light; his hand
# starts REACT_HAND after it, about a simple reaction time, and takes HAND_RISE to reach the line to the sun. Until
# that day the hand and the head started at the very second of first light and the lids began to close before it
FIRST_LIGHT = 40.2
REACT_HEAD = 0.15
REACT_HAND = 0.25
HAND_RISE = 0.63
SHADE_T0 = FIRST_LIGHT + REACT_HAND
SHADE_T1 = SHADE_T0 + HAND_RISE
# the hand against the sun: (fade in from, to, fade out from, to, side)
SHADE = [(SHADE_T0, SHADE_T1, 51.8, 52.5, "l"), (51.8, 52.5, 64.0, 65.0, "r")]
SHADE_REACH = 0.26        # metres from the eyes along the line to the sun
HICCUP = (60.3, 61.6)     # the toe catches the rug: the arms lift and the shade lets go for a moment


def yaw_q(deg):
    return Quaternion((0.0, 0.0, 1.0), math.radians(deg))


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


class KeyPose:
    """Joint positions local to the pelvis, placed by a location and a rotation."""

    def __init__(self, local, loc, rot, face=None):
        self.local = {k: Vector(v) for k, v in local.items()}
        self.loc = Vector(loc)
        self.rot = rot.copy() if isinstance(rot, Quaternion) else rot.to_quaternion()
        # the way the torso faces, in world: by default the placed local x
        self.face = Vector(face) if face is not None else (self.rot.to_matrix() @ Vector((1.0, 0.0, 0.0)))

    def world(self):
        R = self.rot.to_matrix()
        out = {"pelvis": self.loc.copy()}
        for k, v in self.local.items():
            out[k] = self.loc + R @ v
        return out

    def with_local(self, **changes):
        kp = KeyPose(self.local, self.loc, self.rot, self.face)
        for k, v in changes.items():
            kp.local[k] = Vector(v)
        return kp

    def with_world(self, **changes):
        """Replace joints given in world coordinates."""
        R_inv = self.rot.to_matrix().transposed()
        kp = KeyPose(self.local, self.loc, self.rot, self.face)
        for k, v in changes.items():
            kp.local[k] = R_inv @ (Vector(v) - self.loc)
        return kp

    @staticmethod
    def from_world(world, rot, face=None):
        loc = Vector(world["pelvis"])
        R_inv = rot.to_matrix().transposed() if isinstance(rot, Quaternion) else rot.transposed()
        local = {k: R_inv @ (Vector(v) - loc) for k, v in world.items() if k != "pelvis"}
        return KeyPose(local, loc, rot, face)


def _key_poses():
    lie_q = R_LIE.to_quaternion()
    P = {}
    P["LIE"] = KeyPose(LIE_L, LIE_LOC, lie_q, face=(0, 0, 1))
    P["LIE_REACH"] = KeyPose(LIE_REACH_L, LIE_LOC, lie_q, face=(0, 0, 1))
    P["LIE_SMACK"] = KeyPose(LIE_SMACK_L, LIE_LOC, lie_q, face=(0, 0, 1))
    P["LIE_STRETCH"] = KeyPose(LIE_STRETCH_L, LIE_LOC, lie_q, face=(0, 0, 1))
    P["LIE_OUT"] = KeyPose(LIE_OUT_L, LIE_LOC, lie_q, face=(0, 0, 1))
    P["PROP"] = KeyPose.from_world(PROP_WORLD, lie_q, face=(0, 1, 0.45))
    P["SIT"] = KeyPose(SIT_L, SIT_LOC, yaw_q(0))
    # the groggy reach to the phone on the table's edge, the knock, the snap after it, the rap, the retract
    P["SIT_REACH_EDGE"] = P["SIT"].with_world(hand_r=(1.84, 0.50, 0.62), wrist_r=(1.76, 0.54, 0.64), elbow_r=(1.56, 0.56, 0.72))
    P["SIT_RAP"] = P["SIT"].with_world(hand_r=(1.87, 0.51, 0.53), wrist_r=(1.80, 0.55, 0.57), elbow_r=(1.58, 0.58, 0.70))
    P["SIT_SNAP"] = P["SIT"].with_world(hand_r=(1.86, 0.52, 0.42), wrist_r=(1.80, 0.55, 0.49), elbow_r=(1.58, 0.57, 0.68))
    # the hand pulled back in front of the chest, where the eyes can find it
    P["SIT_RETRACT"] = P["SIT"].with_world(hand_r=(1.72, 0.66, 0.85), wrist_r=(1.68, 0.62, 0.80), elbow_r=(1.52, 0.50, 0.68))
    # the left hand comes to the sore right hand and rubs it
    P["SIT_RUB"] = P["SIT_RETRACT"].with_world(hand_l=(1.73, 0.70, 0.88), wrist_l=(1.68, 0.76, 0.84), elbow_l=(1.48, 0.96, 0.72))
    # leaning down to his right for the phone on the floor, the left hand on the left knee
    P["SIT_LEAN_FLOOR"] = P["SIT"].with_world(
        chest=(1.50, 0.66, 1.02), neck=(1.55, 0.62, 1.10), shoulder_r=(1.56, 0.44, 1.02), shoulder_l=(1.46, 0.82, 1.08),
        hand_r=(1.86, 0.56, 0.10), wrist_r=(1.82, 0.56, 0.17), elbow_r=(1.70, 0.52, 0.50),
        hand_l=(1.80, 0.90, 0.62), wrist_l=(1.74, 0.92, 0.66), elbow_l=(1.50, 1.00, 0.84))
    # the phone held in front of the chest, looked at
    P["SIT_PHONE_LOOK"] = P["SIT"].with_world(hand_r=(1.78, 0.65, 0.95), wrist_r=(1.74, 0.63, 0.88), elbow_r=(1.56, 0.50, 0.74))
    P["SIT_UP"] = KeyPose(SIT_UP_L, SIT_LOC, yaw_q(0))
    P["SIT_PHONE_DOWN"] = P["SIT_UP"].with_world(hand_r=(1.74, 0.38, 0.60), wrist_r=(1.66, 0.42, 0.66), elbow_r=(1.48, 0.47, 0.76))
    P["SIT_HANDBED"] = P["SIT_UP"].with_world(hand_l=(1.25, 0.95, 0.57), wrist_l=(1.30, 0.93, 0.62), elbow_l=(1.38, 0.95, 0.80))
    P["STAND_BED"] = KeyPose(STAND_L, STAND_BED_LOC, yaw_q(0))
    # the hand against the sun as a pose, roughly at the brow: the solver in Motion.sample puts it
    # on the line from the eyes to the sun every frame; these keep the blends sensible around it
    shade = {"hand_r": (0.30, -0.08, 0.70), "wrist_r": (0.26, -0.12, 0.64), "elbow_r": (0.14, -0.28, 0.42)}
    shade_l = {"hand_l": (0.30, 0.08, 0.70), "wrist_l": (0.26, 0.12, 0.64), "elbow_l": (0.14, 0.28, 0.42)}
    # His note of 2026-11-07: the hand against the sun is the first reaction to the light, when it
    # first hits his eyes at the crest, not a thing he does later on the walk. The free left hand
    # comes up while the right still holds the phone; the right takes over on the rise, when the
    # left goes down to the bed to push off, and stays up through the walk to the sill.
    P["SIT_PHONE_LOOK_SHADE"] = P["SIT_PHONE_LOOK"].with_local(**shade_l)
    P["SIT_UP_SHADE"] = P["SIT_UP"].with_local(**shade_l)
    P["SIT_PHONE_DOWN_SHADE"] = P["SIT_PHONE_DOWN"].with_local(**shade_l)
    P["SIT_HANDBED_SHADE"] = P["SIT_HANDBED"].with_local(**shade)
    P["SIT_HANDSWITCH"] = P["SIT_PHONE_DOWN_SHADE"].with_local(hand_l=(0.36, 0.24, 0.34), wrist_l=(0.33, 0.24, 0.46), elbow_l=(0.14, 0.30, 0.42))
    P["STAND_SHADE"] = P["STAND_BED"].with_local(**shade)
    P["WINDOW_SHADE"] = KeyPose(P["STAND_SHADE"].local, WINDOW_LOC, yaw_q(0))
    sill = dict(STAND_L)
    sill.update(_sym({
        "chest": (0.08, 0.0, 0.43), "neck": (0.12, 0.0, 0.52), "shoulder_r": (0.10, -0.20, 0.48),
        "elbow_r": (0.28, -0.24, 0.10), "wrist_r": (0.46, -0.16, -0.06), "hand_r": (0.50, -0.15, -0.10),
    }))
    P["SILL"] = KeyPose(sill, WINDOW_LOC, yaw_q(0))
    stretch = dict(STAND_L)
    stretch.update(_sym({
        "chest": (0.0, 0.0, 0.46), "neck": (0.0, 0.0, 0.56), "shoulder_r": (0.0, -0.20, 0.52),
        "elbow_r": (0.0, -0.38, 0.76), "wrist_r": (0.0, -0.44, 1.02), "hand_r": (0.0, -0.46, 1.15),
    }))
    P["STRETCH"] = KeyPose(stretch, WINDOW_LOC, yaw_q(0))
    P["STAND_W"] = KeyPose(STAND_L, WINDOW_LOC, yaw_q(0))
    P["STAND_W_S"] = KeyPose(STAND_L, WINDOW_LOC, yaw_q(-90))
    P["STAND_W_TURNED"] = KeyPose(STAND_L, WINDOW_LOC, yaw_q(-180))
    P["STAND_BEDSIDE_W"] = KeyPose(STAND_L, BEDSIDE_LOC, yaw_q(-180))
    P["STAND_BEDSIDE_N"] = KeyPose(STAND_L, BEDSIDE_LOC, yaw_q(-270))
    P["STAND_BEDSIDE_E"] = KeyPose(STAND_L, BEDSIDE_LOC, yaw_q(-360))
    P["SIT_REACH_TABLE"] = P["SIT_UP"].with_world(hand_r=(1.76, 0.38, 0.60), wrist_r=(1.68, 0.42, 0.66), elbow_r=(1.50, 0.47, 0.76))
    P["SIT_TEXT"] = P["SIT"].with_world(hand_l=(1.74, 0.64, 0.68), wrist_l=(1.66, 0.70, 0.70), elbow_l=(1.48, 0.95, 0.85))
    return P


# ---- walks ------------------------------------------------------------------------

class Walk:
    """A procedural walk from footfalls. footfalls: per foot a list of (t_land, (x, y), lift, options)."""

    def __init__(self, t0, t1, start, end, yaw_deg, feet, right_arm=None, hiccup=None):
        self.t0, self.t1 = t0, t1
        self.start, self.end = Vector((start[0], start[1], STAND_Z)), Vector((end[0], end[1], STAND_Z))
        self.yaw = yaw_deg
        self.feet = feet              # {"l": [...], "r": [...]} each starting with the planted position at t0
        self.right_arm = right_arm    # None or a dict of local positions that hold the right arm
        self.hiccup = hiccup          # None or dict(t_catch, t_free, t_end, overshoot)
        self.swing = 0.55

    def pelvis(self, t):
        u = anim.smoothstep((t - self.t0) / (self.t1 - self.t0))
        p = self.start.lerp(self.end, u)
        p.z = STAND_Z
        return p

    def foot(self, t, side):
        falls = self.feet[side]
        prev = falls[0]
        nxt = None
        for f in falls[1:]:
            if f["t"] <= t:
                prev = f
            else:
                nxt = f
                break
        px, py = prev["pos"]
        if nxt is None:
            return Vector((px, py, 0.08)), 0.0
        swing = nxt.get("swing", self.swing)
        ts = nxt["t"] - swing
        if t < ts:
            return Vector((px, py, 0.08)), 0.0
        catch = nxt.get("catch")
        if catch is not None and t >= catch["t"]:
            # the toe stopped at the rug's edge: held, then lifted high and carried on
            cx, cy = catch["pos"]
            if t < catch["t_free"]:
                return Vector((cx, cy, 0.08 + 0.04)), 0.35
            u = (t - catch["t_free"]) / (nxt["t"] - catch["t_free"])
            u = anim.smoothstep(u)
            lift = nxt.get("lift", 0.07) * math.sin(math.pi * u)
            return Vector((anim.lerp(cx, nxt["pos"][0], u), anim.lerp(cy, nxt["pos"][1], u), 0.08 + lift)), math.sin(math.pi * u)
        if catch is not None:
            # before the catch: a normal swing toward where the model expects the foot to go
            u = (t - ts) / (catch["t"] - ts)
            u = anim.smoothstep(u) * 1.0
            cx, cy = catch["pos"]
            lift = 0.05 * math.sin(math.pi * 0.5 * u)
            return Vector((anim.lerp(px, cx, u), anim.lerp(py, cy, u), 0.08 + lift)), math.sin(math.pi * 0.5 * u)
        u = anim.smoothstep((t - ts) / swing)
        lift = nxt.get("lift", 0.07) * math.sin(math.pi * u)
        return Vector((anim.lerp(px, nxt["pos"][0], u), anim.lerp(py, nxt["pos"][1], u), 0.08 + lift)), math.sin(math.pi * u)

    def pose(self, t):
        yaw = math.radians(self.yaw)
        R = Matrix.Rotation(yaw, 3, "Z")
        fwd = R @ Vector((1.0, 0.0, 0.0))
        left = R @ Vector((0.0, 1.0, 0.0))
        pelvis = self.pelvis(t)
        lean = 0.02
        extra_fwd = 0.0
        arms_lift = 0.0
        if self.hiccup:
            h = self.hiccup
            if h["t_catch"] <= t < h["t_end"]:
                u = (t - h["t_catch"]) / (h["t_end"] - h["t_catch"])
                bump = math.sin(math.pi * min(1.0, u * 1.6)) if u < 0.625 else 0.0
                lean = 0.02 + 0.10 * bump
                extra_fwd = h["overshoot"] * bump
                arms_lift = math.sin(math.pi * u)
                pelvis = pelvis + fwd * extra_fwd - Vector((0, 0, 0.03 * bump))
        J = {"pelvis": pelvis}
        J["chest"] = pelvis + R @ Vector((0.02 + lean, 0.0, 0.44))
        J["neck"] = pelvis + R @ Vector((0.03 + lean * 1.3, 0.0, 0.54))
        for side, s in (("l", 1.0), ("r", -1.0)):
            J[f"shoulder_{side}"] = pelvis + R @ Vector((0.02 + lean, s * 0.20, 0.50))
            J[f"hip_{side}"] = pelvis + R @ Vector((0.0, s * 0.11, -0.03))
            ankle, lift_u = self.foot(t, side)
            J[f"ankle_{side}"] = ankle
            J[f"toe_{side}"] = ankle + fwd * 0.20 + Vector((0, 0, -0.06 + 0.04 * lift_u))
            hip = J[f"hip_{side}"]
            mid = (hip + ankle) * 0.5
            J[f"knee_{side}"] = mid + fwd * (0.06 + 0.22 * lift_u) + Vector((0, 0, 0.02))
        # arms swing against the legs
        d_r = (J["ankle_r"] - pelvis).dot(fwd)
        d_l = (J["ankle_l"] - pelvis).dot(fwd)
        for side, s, d in (("l", 1.0, d_r), ("r", -1.0, d_l)):
            sw = 0.45 * d
            lift = arms_lift
            swing_pose = {
                f"elbow_{side}": Vector((0.02 + sw * 0.3 + 0.12 * lift, s * (0.25 + 0.10 * lift), 0.19 + 0.08 * lift)),
                f"wrist_{side}": Vector((0.04 + sw * 0.7 + 0.25 * lift, s * (0.27 + 0.16 * lift), -0.08 + 0.26 * lift)),
                f"hand_{side}": Vector((0.05 + sw + 0.30 * lift, s * (0.28 + 0.18 * lift), -0.21 + 0.36 * lift)),
            }
            if side == "r" and self.right_arm is not None:
                # the hand held at the brow leaves it only as the arms lift at the hiccup
                for k, v in swing_pose.items():
                    held = Vector(self.right_arm[k])
                    J[k] = pelvis + R @ held.lerp(v, lift)
                continue
            for k, v in swing_pose.items():
                J[k] = pelvis + R @ v
        return J, fwd


def _walks():
    f1 = {
        "r": [{"t": 57.4, "pos": (1.88, 0.63)},
              {"t": 58.6, "pos": (2.08, 0.68)},
              {"t": 61.4, "pos": (2.95, 1.00), "swing": 1.4, "lift": 0.15,
               "catch": {"t": 60.3, "t_free": 60.62, "pos": (2.27, 0.70)}},
              {"t": 63.5, "pos": (3.45, 1.08)}],
        "l": [{"t": 57.4, "pos": (1.88, 0.87)},
              {"t": 59.8, "pos": (2.75, 0.98), "lift": 0.12},
              {"t": 62.6, "pos": (3.45, 1.32)}],
    }
    shade = {"hand_r": (0.30, -0.08, 0.70), "wrist_r": (0.26, -0.12, 0.64), "elbow_r": (0.14, -0.28, 0.42)}
    w1 = Walk(57.4, 63.8, (1.88, 0.75), (3.45, 1.20), 0.0, f1, right_arm=shade,
              hiccup={"t_catch": HICCUP[0], "t_end": HICCUP[1], "overshoot": 0.07})
    f2 = {
        "l": [{"t": 94.5, "pos": (3.45, 1.08)},
              {"t": 95.3, "pos": (3.00, 1.00)},
              {"t": 97.2, "pos": (2.15, 0.72), "lift": 0.16},
              {"t": 98.8, "pos": (1.95, 0.63)}],
        "r": [{"t": 94.5, "pos": (3.45, 1.32)},
              {"t": 96.2, "pos": (2.60, 1.07), "lift": 0.10},
              {"t": 98.1, "pos": (1.95, 0.87)}],
    }
    w2 = Walk(94.5, 98.8, (3.45, 1.20), (1.95, 0.75), -180.0, f2)
    return [w1, w2]


# ---- the schedule -----------------------------------------------------------------

def _schedule(P):
    """(t_start, t_end, pose_a, pose_b, mode): a hold when a is b. Rung 2b's timeline."""
    S = []
    def hold(t0, t1, a):
        S.append((t0, t1, a, a, "place"))
    def move(t0, t1, a, b, mode="world"):
        S.append((t0, t1, a, b, mode))
    hold(0.0, 8.5, "LIE")
    move(8.5, 9.6, "LIE", "LIE_REACH", "place")                 # the arm goes out blind to the table
    hold(9.6, 10.0, "LIE_REACH")
    move(10.0, 10.25, "LIE_REACH", "LIE_SMACK", "place")        # the flick that stops the alarm and sends the phone skidding
    hold(10.25, 10.6, "LIE_SMACK")
    move(10.6, 12.0, "LIE_SMACK", "LIE", "place")
    move(12.0, 12.8, "LIE", "LIE_OUT", "place")                 # the stretch: arms out to the sides, then over the head, a yawn
    move(12.8, 13.6, "LIE_OUT", "LIE_STRETCH", "place")
    hold(13.6, 15.4, "LIE_STRETCH")
    move(15.4, 16.2, "LIE_STRETCH", "LIE_OUT", "place")
    move(16.2, 17.0, "LIE_OUT", "LIE", "place")
    move(17.0, 19.4, "LIE", "PROP")                             # sits up, legs out, no phone
    move(19.4, 22.0, "PROP", "SIT")
    hold(22.0, 27.0, "SIT")                                     # the doze: the head alone moves
    move(27.0, 28.25, "SIT", "SIT_REACH_EDGE")                  # the groggy reach to the phone on the edge
    move(28.25, 28.55, "SIT_REACH_EDGE", "SIT_RAP")             # the fingers knock it off; the hand snaps after it and the knuckles rap the edge
    move(28.55, 28.75, "SIT_RAP", "SIT_SNAP")
    move(28.75, 29.3, "SIT_SNAP", "SIT_RETRACT")                # the hand comes back
    hold(29.3, 30.4, "SIT_RETRACT")
    move(30.4, 30.9, "SIT_RETRACT", "SIT_RUB")                  # the other hand rubs it
    hold(30.9, 34.0, "SIT_RUB")
    move(34.0, 35.0, "SIT_RUB", "SIT_RETRACT")
    move(35.0, 36.6, "SIT_RETRACT", "SIT_LEAN_FLOOR")           # down to the phone on the floor
    hold(36.6, 37.0, "SIT_LEAN_FLOOR")
    move(37.0, 38.3, "SIT_LEAN_FLOOR", "SIT_PHONE_LOOK")        # up with it; the screen wakes
    hold(38.3, SHADE_T0, "SIT_PHONE_LOOK")
    move(SHADE_T0, SHADE_T1, "SIT_PHONE_LOOK", "SIT_PHONE_LOOK_SHADE", "place")   # first light at FIRST_LIGHT: the free hand comes up a reaction time later
    hold(SHADE_T1, 44.0, "SIT_PHONE_LOOK_SHADE")                    # two breaths
    move(44.0, 46.5, "SIT_PHONE_LOOK_SHADE", "SIT_UP_SHADE")    # the head lifts to the window under the hand
    hold(46.5, 50.2, "SIT_UP_SHADE")
    move(50.2, 51.3, "SIT_UP_SHADE", "SIT_PHONE_DOWN_SHADE")    # the phone face down on the table
    hold(51.3, 51.8, "SIT_PHONE_DOWN_SHADE")
    move(51.8, 52.15, "SIT_PHONE_DOWN_SHADE", "SIT_HANDSWITCH")      # the left comes forward and down to the bed, the right takes over
    move(52.15, 52.5, "SIT_HANDSWITCH", "SIT_HANDBED_SHADE")
    move(52.5, 54.2, "SIT_HANDBED_SHADE", "STAND_SHADE")
    hold(54.2, 57.4, "STAND_SHADE")
    # 57.4 to 63.8: walk 1
    hold(63.8, 64.0, "WINDOW_SHADE")
    move(64.0, 65.0, "WINDOW_SHADE", "SILL", "place")
    hold(65.0, 72.6, "SILL")
    move(72.6, 75.0, "SILL", "STRETCH", "place")
    hold(75.0, 78.0, "STRETCH")
    move(78.0, 80.0, "STRETCH", "STAND_W", "place")
    hold(80.0, 92.5, "STAND_W")                                 # eyes closed in the sun, the chime
    move(92.5, 93.25, "STAND_W", "STAND_W_S", "place")
    move(93.25, 94.0, "STAND_W_S", "STAND_W_TURNED", "place")
    hold(94.0, 94.5, "STAND_W_TURNED")
    # 94.5 to 98.8: walk 2
    hold(98.8, 100.0, "STAND_BEDSIDE_W")
    move(100.0, 100.5, "STAND_BEDSIDE_W", "STAND_BEDSIDE_N", "place")
    move(100.5, 101.0, "STAND_BEDSIDE_N", "STAND_BEDSIDE_E", "place")
    move(101.0, 102.5, "STAND_BEDSIDE_E", "SIT_UP")
    hold(102.5, 104.0, "SIT_UP")
    move(104.0, 105.0, "SIT_UP", "SIT_REACH_TABLE")
    hold(105.0, 106.0, "SIT_REACH_TABLE")
    move(106.0, 107.0, "SIT_REACH_TABLE", "SIT")
    hold(107.0, 107.6, "SIT")
    move(107.6, 108.3, "SIT", "SIT_TEXT")
    hold(108.3, END_T, "SIT_TEXT")
    return S


# head yaw and pitch in degrees: (t, yaw, pitch), yaw positive to his left, pitch positive up.
# True angles while he is upright (the frame is levelled to gravity); relative to the torso
# while he lies, where 0 looks at the ceiling.
HEAD_KEYS = [
    (0.0, 0, 0), (12.0, 0, 0), (13.6, 0, 8), (15.4, 0, 8), (17.0, 0, 0),
    (19.4, 0, -12), (22.0, 0, -10),
    (24.5, 0, -45), (25.0, 0, -15), (25.6, 0, -25), (27.0, 0, -48),
    (27.6, -20, -40), (28.25, -30, -45), (28.5, -38, -58), (28.75, -40, -62),
    (29.3, -12, -35), (30.4, -10, -50), (34.0, -8, -50), (35.0, -20, -52),
    (36.0, -40, -58), (36.9, -42, -60), (38.3, -8, -50), (FIRST_LIGHT + REACT_HEAD, -8, -50),
    (FIRST_LIGHT + REACT_HEAD + 0.25, 4, -56), (41.4, 0, -50), (44.0, 0, -50), (46.5, 0, 5), (50.2, 0, 5),
    (51.0, -28, -32), (51.8, -10, -18), (52.5, 0, -5), (54.2, 0, 0), (57.4, 0, 0),
    (60.1, 0, -3), (60.45, 0, -24), (61.3, 0, -4), (63.8, 0, 0), (65.0, 0, 3),
    (66.5, -15, 5), (68.0, 12, 6), (70.0, 0, 5), (72.6, 0, 5),
    (75.0, 0, 16), (80.0, 0, 14), (88.3, 0, 14), (89.3, -20, 10), (90.5, -55, 5), (92.0, -60, 2), (92.5, -60, 0),
    (93.3, -30, -8), (94.0, 0, -14), (94.5, 0, -12), (96.6, 0, -32), (97.6, 0, -12), (98.8, 0, -10),
    (100.0, 0, -12), (101.0, 0, -6), (102.5, -8, -12), (104.0, -10, -14), (104.8, -45, -48), (106.0, -45, -48),
    (107.0, -5, -42), (END_T, 0, -42),
]


def _interp_keys(keys, t):
    if t <= keys[0][0]:
        return keys[0][1:]
    for (t0, *a), (t1, *b) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            u = anim.smoothstep((t - t0) / (t1 - t0))
            return tuple(anim.lerp(x, y, u) for x, y in zip(a, b))
    return keys[-1][1:]


def _two_bone(S, W, l1, l2, pole):
    """The elbow of an arm from shoulder S to wrist W with bone lengths l1 and l2, bent toward pole."""
    d = Vector(W) - Vector(S)
    L = d.length
    if L < 1e-6:
        return Vector(S) + Vector(pole).normalized() * l1
    dn = d / L
    L = min(L, l1 + l2 - 1e-3)
    cos_a = clamp((l1 * l1 + L * L - l2 * l2) / (2.0 * l1 * L), -1.0, 1.0)
    a = math.acos(cos_a)
    p = Vector(pole) - dn * Vector(pole).dot(dn)
    if p.length < 1e-6:
        p = Vector((0.0, 0.0, -1.0)) - dn * (-dn.z)
    p.normalize()
    return Vector(S) + dn * (l1 * math.cos(a)) + p * (l1 * math.sin(a))


# where each limb bends when a pose gives no clear side, in the body's frame: elbows out and down, knees forward
BEND_BIAS = {"elbow_l": (-0.5, 0.6, -0.6), "elbow_r": (-0.5, -0.6, -0.6), "knee_l": (1.0, 0.0, 0.0), "knee_r": (1.0, 0.0, 0.0)}


def fix_lengths(J, body_R=None):
    """Hold every limb at its bone lengths: the end joint stays where the pose put it unless it is
    out of reach, the middle joint is solved on the authored side of the bend, the tip follows.
    A firm bias toward each limb's natural side, elbows back, out and down, knees forward, is
    added to the authored side, so the bend turns through it rather than through nothing when
    a pose puts the middle joint on the line; the hand and the foot continue the forearm and the
    shin, leaning toward the authored direction, so they never swing through zero either."""
    R = body_R if body_R is not None else Matrix.Identity(3)
    for root, mid, end, tip, l1, l2, l3 in LIMBS:
        S, E, W, T = J[root], J[mid], J[end], J[tip]
        d = W - S
        L = d.length
        if L > l1 + l2 - 1e-3:
            W = S + d * ((l1 + l2 - 1e-3) / L)
        dn = d / L if L > 1e-6 else Vector((0.0, 0.0, 1.0))
        pole = E - (S + W) * 0.5
        pole = pole - dn * pole.dot(dn)
        bias = R @ Vector(BEND_BIAS[mid])
        pole = pole + (bias - dn * bias.dot(dn)) * 0.25
        if pole.length < 1e-4:
            pole = Vector((1.0, 0.0, 0.0)) if root.startswith("hip") else Vector((0.0, 0.0, -1.0))
        E2 = _two_bone(S, W, l1, l2, pole)
        fore = (W - E2).normalized()
        tip_dir = T - J[end]
        tip_dir = tip_dir.normalized() if tip_dir.length > 1e-6 else fore
        if not root.startswith("hip"):
            tip_dir = fore + tip_dir * 0.6      # a hand continues its forearm, leaning toward the authored direction
        J[mid], J[end], J[tip] = E2, W, W + tip_dir.normalized() * l3
    return J


class Motion:
    """The whole chain. sample(t) returns joints in world, the head frame, the body frame, the phone matrix.

    sun_dir(t) gives the unit vector toward the sun at second t, for the hand against it; by
    default a sun seven degrees up due east.
    """

    def __init__(self, sun_dir=None, gaze=None, gaze_points=None):
        # what the eyes look at apart from where the head faces (his fourteenth round of 2026-11-14: "eyes have eyeballs
        # and don't have to match the head movement exactly"): rows (t0, t1, name), the timeline's sight events that
        # name a thing; a row that follows another on the same thing within a fifth of a second is one look
        rows = []
        for t0, t1, name in sorted(gaze or [], key=lambda g: g[0]):
            if rows and rows[-1][2] == name and t0 - rows[-1][1] <= 0.2:
                rows[-1] = (rows[-1][0], max(rows[-1][1], t1), name)
            else:
                rows.append((float(t0), float(t1), name))
        self.gaze = rows
        self.gaze_points = {k: Vector(v) for k, v in (gaze_points or {}).items()}   # named places a look can rest on
        self.P = _key_poses()
        self.S = _schedule(self.P)
        self.walks = _walks()
        self.sun_dir = sun_dir or (lambda t: Vector((math.cos(math.radians(7.0)), 0.0, math.sin(math.radians(7.0)))))

    def _schedule_pose(self, t):
        for t0, t1, a, b, mode in self.S:
            if t0 <= t < t1 or (t1 >= END_T and t >= t0):
                A, B = self.P[a], self.P[b]
                if a == b:
                    return A.world(), A.face
                u = anim.smoothstep((t - t0) / (t1 - t0))
                if mode == "place":
                    rot = A.rot.slerp(B.rot, u)
                    loc = A.loc.lerp(B.loc, u)
                    local = {k: A.local[k].lerp(B.local[k], u) for k in A.local}
                    kp = KeyPose(local, loc, rot, face=A.face.lerp(B.face, u))
                    return kp.world(), kp.face
                WA, WB = A.world(), B.world()
                J = {k: WA[k].lerp(WB[k], u) for k in WA}
                return J, A.face.lerp(B.face, u)
        last = self.S[-1]
        return self.P[last[3]].world(), self.P[last[3]].face

    def _base(self, t):
        for w in self.walks:
            if w.t0 <= t < w.t1:
                J, fwd = w.pose(t)
                # the walk is blended into the poses on either side of it, so its lean and its
                # arms arrive and leave over half a second instead of in one frame
                if t < w.t0 + WALK_BLEND:
                    Jp, fp = self._schedule_pose(w.t0 - 1e-3)
                    u = anim.smoothstep((t - w.t0) / WALK_BLEND)
                    return {k: Jp[k].lerp(J[k], u) for k in J}, fp.lerp(fwd, u)
                if t > w.t1 - WALK_BLEND:
                    Jn, fn = self._schedule_pose(w.t1 + 1e-3)
                    u = anim.smoothstep((w.t1 - t) / WALK_BLEND)
                    return {k: Jn[k].lerp(J[k], u) for k in J}, fn.lerp(fwd, u)
                return J, fwd
        return self._schedule_pose(t)

    def _head_base(self, J, face):
        """The frame the head's yaw and pitch are keyed in: the torso's, levelled to gravity
        as far as he is upright."""
        torso_up = (J["neck"] - J["chest"]).normalized()
        f = Vector(face)
        f = (f - torso_up * f.dot(torso_up))
        if f.length < 1e-6:
            f = Vector((1.0, 0.0, 0.0))
        f.normalize()
        torso_left = torso_up.cross(f).normalized()
        Rt = Matrix((f, torso_left, torso_up)).transposed()      # columns: forward, left, up
        lean = math.degrees(math.acos(clamp(torso_up.z, -1.0, 1.0)))
        level = 1.0 - anim.smoothstep((lean - 30.0) / 30.0)       # 1 upright, 0 lying
        if level <= 1e-6:
            return Rt, Rt
        fh = Vector((f.x, f.y, 0.0))
        if fh.length < 1e-6:
            fh = Vector((face[0], face[1], 0.0))
        if fh.length < 1e-6:
            fh = Vector((1.0, 0.0, 0.0))
        fh.normalize()
        up = Vector((0.0, 0.0, 1.0))
        Rl = Matrix((fh, up.cross(fh).normalized(), up)).transposed()
        q = Rt.to_quaternion().slerp(Rl.to_quaternion(), level)
        return q.to_matrix(), Rt

    def _shade(self, t, J, hf, body_R):
        """The hand against the sun on the line from the eyes to the sun, with its wrist and elbow."""
        for t_in0, t_in1, t_out0, t_out1, side in SHADE:
            if not (t_in0 <= t < t_out1):
                continue
            w = anim.smoothstep((t - t_in0) / (t_in1 - t_in0)) * (1.0 - anim.smoothstep((t - t_out0) / (t_out1 - t_out0)))
            if HICCUP[0] <= t < HICCUP[1]:
                w *= 1.0 - 0.8 * math.sin(math.pi * (t - HICCUP[0]) / (HICCUP[1] - HICCUP[0]))
            if w <= 1e-4:
                continue
            d = Vector(self.sun_dir(t)).normalized()
            up = Vector((0.0, 0.0, 1.0))
            left = body_R @ Vector((0.0, 1.0, 0.0))
            s = 1.0 if side == "l" else -1.0
            hand = Vector(hf["eye"]) + d * SHADE_REACH
            wrist0 = hand - d * 0.08 - up * 0.06
            shoulder = J[f"shoulder_{side}"]
            pole = -up * 0.6 + left * (0.8 * s)
            elbow = _two_bone(shoulder, wrist0, UPPER_ARM, FOREARM, pole)
            wrist = hand + (elbow - hand).normalized() * HAND_LEN
            for k, v in ((f"hand_{side}", hand), (f"wrist_{side}", wrist), (f"elbow_{side}", elbow)):
                J[k] = J[k].lerp(v, w)

    def sample(self, t):
        J, face = self._base(t)
        # overlays: breathing while lying, the rub, the sway after standing, the shoulders dropping in the sun
        if t < 17.0:
            dz = 0.012 * math.sin(2 * math.pi * 0.22 * t)
            for k in ("chest", "neck", "shoulder_l", "shoulder_r"):
                J[k] = J[k] + Vector((0, 0, dz))
        if 30.9 <= t < 34.0:
            ph = 2 * math.pi * 2.2 * (t - 30.9)
            J["hand_l"] = J["hand_l"] + Vector((0.015 * math.sin(ph), 0.0, 0.008 * math.cos(ph)))
            J["wrist_l"] = J["wrist_l"] + Vector((0.010 * math.sin(ph), 0.0, 0.005 * math.cos(ph)))
        if 54.2 <= t < 57.4:
            tau = t - 54.2
            dy = 0.035 * math.sin(2 * math.pi * 0.9 * tau) * math.exp(-tau / 1.1)
            for k in ("pelvis", "chest", "neck", "shoulder_l", "shoulder_r", "elbow_l", "elbow_r",
                      "wrist_l", "wrist_r", "hand_l", "hand_r", "hip_l", "hip_r"):
                J[k] = J[k] + Vector((0, dy, 0))
        if 83.5 <= t < 93.25:
            # down over a second from 83.5 s, and back up over the turn from the window (92.5 to 93.25 s). Until
            # 2026-11-14 the drop ended at a stroke at 92.5 s: the arms rose 2.5 cm in one frame, a hop in the
            # Third-Person view and a one-frame glow of the arms' outlines in the mind's model
            u = anim.smoothstep((t - 83.5) / 1.0) * (1.0 - anim.smoothstep((t - 92.5) / 0.75))
            for k in ("shoulder_l", "shoulder_r", "elbow_l", "elbow_r", "wrist_l", "wrist_r", "hand_l", "hand_r"):
                J[k] = J[k] + Vector((0, 0, -0.025 * u))
        if t >= 108.3:
            # the thumbs on the screen: a small working motion of the hands
            J["hand_l"] = J["hand_l"] + Vector((0, 0, 0.006 * math.sin(2 * math.pi * 2.3 * t)))
            J["hand_r"] = J["hand_r"] + Vector((0, 0, 0.006 * math.sin(2 * math.pi * 2.3 * t + 1.5)))
        Rb, Rt = self._head_base(J, face)
        yaw, pitch = _interp_keys(HEAD_KEYS, t)
        Rh = Rb @ Matrix.Rotation(math.radians(yaw), 3, "Z") @ Matrix.Rotation(math.radians(-pitch), 3, "Y")
        fwd = Rh @ Vector((1.0, 0.0, 0.0))
        left = Rh @ Vector((0.0, 1.0, 0.0))
        up = Rh @ Vector((0.0, 0.0, 1.0))
        head = J["neck"] + up * HEAD_FROM_NECK
        J["head"] = head
        eye = head + Rh @ Vector(EYE_OFFSET)
        head_frame = {"loc": head, "rot": Rh, "fwd": fwd, "left": left, "up": up, "eye": eye,
                      "ear_l": head + left * EAR_OFFSET, "ear_r": head - left * EAR_OFFSET}
        body_R = Rt
        self._shade(t, J, head_frame, body_R)
        fix_lengths(J, body_R)
        phone = self.phone(t, J, body_R)
        head_frame.update(self._eyes(t, J, head_frame, phone))
        return J, head_frame, body_R, phone

    def _eyes(self, t, J, hf, phone):
        """The eyes' own frame: the head's, turned toward what the timeline has him look at (self.gaze) by EYE_REACH at
        the most, each look landing and leaving over GAZE_EASE; a later look takes over from an earlier one. The eyes
        stay where they are in the head: they turn, they do not move."""
        f = Vector(hf["fwd"])
        d = f.copy()
        reach = math.radians(EYE_REACH)
        for t0, t1, name in self.gaze:
            w = anim.smoothstep((t - t0) / GAZE_EASE) * (1.0 - anim.smoothstep((t - t1) / GAZE_EASE))
            if w <= 0.0:
                continue
            if name == "phone":
                p = phone.translation
            elif name in J:
                p = J[name]
            elif name in self.gaze_points:
                p = self.gaze_points[name]
            else:
                continue
            g = Vector(p) - Vector(hf["eye"])
            if g.length < 1e-6:
                continue
            g.normalize()
            ang = f.angle(g)
            if ang > reach:
                g = f.slerp(g, reach / ang)        # as far as the eyes turn, toward it
            d = d.slerp(g, w).normalized()
        Re = hf["rot"].copy() if d.angle(f) < 1e-9 else f.rotation_difference(d).to_matrix() @ hf["rot"]
        return {"eye_rot": Re, "eye_fwd": Re @ Vector((1.0, 0.0, 0.0)), "eye_left": Re @ Vector((0.0, 1.0, 0.0)),
                "eye_up": Re @ Vector((0.0, 0.0, 1.0))}

    # ---- the phone ----
    def _in_hand(self, J, R, lift=1.0):
        hand = J["hand_r"]
        off = R @ Vector((0.03, 0.0, 0.045 * lift))
        return Matrix.Translation(hand + off) @ R.to_4x4() @ Matrix.Rotation(math.radians(-22), 4, "Y")

    @staticmethod
    def _blend(A, B, u):
        loc = A.translation.lerp(B.translation, u)
        q = A.to_quaternion().slerp(B.to_quaternion(), u)
        return Matrix.Translation(loc) @ q.to_matrix().to_4x4()

    def phone(self, t, J, R):
        if t < 10.1:
            return PHONE_TABLE_1
        if t < 10.5:
            # the skid: fast off the hand, slowing to a stop at the edge
            x = (t - 10.1) / 0.4
            return self._blend(PHONE_TABLE_1, PHONE_EDGE, 1.0 - (1.0 - x) * (1.0 - x))
        if t < 28.3:
            return PHONE_EDGE
        if t < 28.72:
            # knocked over the north edge: a tumble into the gap, falling under gravity
            tau = t - 28.3
            u = clamp(tau / 0.42)
            a, b = PHONE_EDGE.translation, PHONE_FLOOR.translation
            xy = a.lerp(b, anim.smoothstep(min(1.0, u * 1.6)))
            z = max(b.z, a.z - 4.9 * tau * tau)
            qa, qb = PHONE_EDGE.to_quaternion(), PHONE_FLOOR.to_quaternion()
            q = qa.slerp(qb, u)
            tumble = Matrix.Rotation(math.radians(360.0) * u, 4, "X")
            return Matrix.Translation((xy.x, xy.y, z)) @ q.to_matrix().to_4x4() @ tumble
        if t < 36.7:
            return PHONE_FLOOR
        if t < 37.1:
            u = anim.smoothstep((t - 36.7) / 0.4)
            return self._blend(PHONE_FLOOR, self._in_hand(J, R), u)
        if t < 50.2:
            return self._in_hand(J, R)
        if t < 51.1:
            u = anim.smoothstep((t - 50.2) / 0.9)
            return self._blend(self._in_hand(J, R), PHONE_TABLE_2, u)
        if t < 105.0:
            return PHONE_TABLE_2
        if t < 106.0:
            u = anim.smoothstep((t - 105.0) / 1.0)
            return self._blend(PHONE_TABLE_2, self._in_hand(J, R), u)
        return self._in_hand(J, R)

    def blanket_offset(self, t):
        """The blanket is pushed aside as the legs swing out."""
        u = anim.smoothstep((t - 17.5) / 3.0)
        return Vector((0.12 * u, 0.28 * u, 0.0))


# ---- building the figure in Blender ---------------------------------------------

def _joint_part(joint):
    for part, spec in tags.PARTS.items():
        if joint in spec["joints"]:
            return part
    return "chest"


def _bone_part(end_joint):
    for part, spec in tags.PARTS.items():
        if end_joint in spec["bones"]:
            return part
    return "chest"


def build_figure(prefix, collection, materials, parent=None, radius_scale=1.0, segments=12,
                 empty_size=0.03, name_part=True):
    """Joint Empties, joint spheres parented to them, limbs held between them by constraints,
    and the head parented to the head Empty. Returns {"empties": {...}, "prims": [(obj, part)]}.

    materials: {"skin": mat, "cloth": mat}. Each primitive gets tags.PART_PROP.
    """
    empties = {}
    for name in ALL_JOINTS:
        e = geo.add_empty(f"{prefix}_{name}", (0, 0, 0), 1.0, collection, parent)
        e.empty_display_size = empty_size
        e.rotation_mode = "QUATERNION"
        empties[name] = e
    prims = []
    groups = list(materials.keys())
    mats = [materials[g] for g in groups]
    idx = {g: i for i, g in enumerate(groups)}

    for name, (r, g) in JOINTS.items():
        bm = geo.new_bmesh()
        geo.add_sphere(bm, (0, 0, 0), r * radius_scale, idx[g], segments=segments, rings=max(6, segments // 2))
        obj = geo.finish(bm, f"{prefix}J_{name}", mats, collection, empties[name])
        part = _joint_part(name)
        obj[tags.PART_PROP] = part
        prims.append((obj, part))

    for a, b, ra, rb, g in BONES:
        if b == "head_base":
            b = "head"
            rb = ra
        bm = geo.new_bmesh()
        m = Matrix.Translation((0, 0.5, 0)) @ Matrix.Rotation(math.radians(-90), 4, "X")
        n0 = len(bm.faces)
        bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=segments,
                              radius1=ra * radius_scale, radius2=rb * radius_scale, depth=1.0, matrix=m)
        bm.faces.ensure_lookup_table()
        for f in bm.faces[n0:]:
            f.material_index = idx[g]
            f.smooth = True
        obj = geo.finish(bm, f"{prefix}L_{b}", mats, collection, parent)
        c1 = obj.constraints.new("COPY_LOCATION")
        c1.target = empties[a]
        c2 = obj.constraints.new("STRETCH_TO")
        c2.target = empties[b]
        c2.rest_length = 1.0
        c2.volume = "NO_VOLUME"
        part = _bone_part(b if b != "head" else "head_base")
        obj[tags.PART_PROP] = part
        prims.append((obj, part))

    bm = geo.new_bmesh()
    geo.add_sphere(bm, (0, 0, 0), HEAD_RADIUS * radius_scale, idx["skin"], scale=HEAD_SCALE,
                   segments=segments * 2, rings=segments)
    head = geo.finish(bm, f"{prefix}_Head", mats, collection, empties["head"])
    head[tags.PART_PROP] = "head"
    prims.append((head, "head"))
    # the senses' stand-in parts (rung 2p): the ears and the eyes on the head, the heart and the lungs in the chest,
    # each its own thing with its part's name (triview/figure.py ORGANS), riding the head's Empty or a torso Empty
    # keyed at the chest joint in the torso's own frame (bake_figure), so they lie down with him
    torso = geo.add_empty(f"{prefix}_torso", (0, 0, 0), 1.0, collection, parent)
    torso.empty_display_size = empty_size
    torso.rotation_mode = "QUATERNION"
    empties["torso"] = torso
    organs = {}
    for part, (ride, centre, r, sc, g) in ORGANS.items():
        bm = geo.new_bmesh()
        geo.add_sphere(bm, (0.0, 0.0, 0.0), r * radius_scale, idx.get(g, idx["skin"]), scale=sc, segments=segments, rings=max(6, segments // 2))
        obj = geo.finish(bm, f"{prefix}O_{part}", mats, collection, empties["head"] if ride == "head" else torso)
        # the mesh about its own origin and the object at the organ's place, so the object's location is the organ's
        # centre (the model scales a breathing organ about it)
        obj.location = tuple(c * radius_scale for c in centre)
        obj[tags.PART_PROP] = part
        prims.append((obj, part))
        organs[part] = obj
    return {"empties": empties, "prims": prims, "head": head, "organs": organs, "eyes": [organs["eye_l"], organs["eye_r"]]}


def bake_figure(baker, empties, frames, fps, motion=None, samples=None):
    """Write the motion to the joint Empties. samples: {frame: (J, head_frame)} or a Motion."""
    for f in frames:
        t = anim.time_of(f, fps)
        if samples is not None:
            J, hf, body_R = samples[f][0], samples[f][1], samples[f][2]
        else:
            J, hf, body_R, _ = motion.sample(t)
        for name in JOINT_NAMES:
            baker.set_vec(empties[name], "location", f, J[name])
        baker.set_vec(empties["head"], "location", f, hf["loc"])
        baker.set_vec(empties["head"], "rotation_quaternion", f, hf["rot"].to_quaternion())
        if "torso" in empties:
            # the torso's frame at the chest joint, for the organs (rung 2p)
            baker.set_vec(empties["torso"], "location", f, J["chest"])
            baker.set_vec(empties["torso"], "rotation_quaternion", f, body_R.to_quaternion())

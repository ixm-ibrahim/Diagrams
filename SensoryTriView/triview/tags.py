"""The vocabulary shared by the art and the engine: region tags on surfaces and body
parts, the joint chains signals run along, and the sense families with their colours.

Nothing here touches Blender. The engine reads tags off the scene (as custom properties
named by TAG_PROP on the objects the rays can strike) and off the body parts, and the
True-Person art builds one region object per tag it can draw.
"""
from . import materials as mats

TAG_PROP = "tv_tag"          # custom property on room objects: the region a hit belongs to
PART_PROP = "tv_part"        # custom property on body primitives: the body part
OF_PROP = "tv_of"            # custom property on a room object set into another, lying on it or resting on it: that
                             # object's name. As a memory it ripples with it (triview/lidarscene.py, the table's wave_id)
PASS_PROP = "tv_pass"        # custom property on glass the eyes' rays pass through (the window's pane): the mind's picture
                             # takes it as absent, so a ray reaches what lies beyond it, as the engine's rays do

# Surfaces of the room the mind can hold, and what the real objects are tagged with.
SURFACES = ["floor", "ceiling", "wall_n", "wall_s", "wall_e", "wall_w", "window", "sill",
            "bed", "table", "table_far", "table_edge", "rug", "rug_edge", "phone", "ridge", "sun", "ground"]

# Body parts: each is a set of primitives of the mannequin, joints and bones by their end joint.
PARTS = {
    "head": {"joints": ["head"], "bones": []},
    "neck": {"joints": ["neck"], "bones": ["head_base"]},
    "chest": {"joints": ["chest"], "bones": ["chest", "neck", "shoulder_r"]},
    "pelvis": {"joints": ["pelvis"], "bones": []},
    "upper_arm_r": {"joints": ["shoulder_r"], "bones": ["elbow_r"]},
    "upper_arm_l": {"joints": ["shoulder_l"], "bones": ["elbow_l"]},
    "forearm_r": {"joints": ["elbow_r"], "bones": ["wrist_r"]},
    "forearm_l": {"joints": ["elbow_l"], "bones": ["wrist_l"]},
    "hand_r": {"joints": ["wrist_r", "hand_r"], "bones": ["hand_r"]},
    "hand_l": {"joints": ["wrist_l", "hand_l"], "bones": ["hand_l"]},
    "thigh_r": {"joints": ["hip_r"], "bones": ["knee_r"]},
    "thigh_l": {"joints": ["hip_l"], "bones": ["knee_l"]},
    "shin_r": {"joints": ["knee_r"], "bones": ["ankle_r"]},
    "shin_l": {"joints": ["knee_l"], "bones": ["ankle_l"]},
    "foot_r": {"joints": ["ankle_r", "toe_r"], "bones": ["toe_r"]},
    "foot_l": {"joints": ["ankle_l", "toe_l"], "bones": ["toe_l"]},
}

# The parts the senses light beyond the joints and the bones (rung 2p, his specification of 2026-11-12): the ears
# and the eyes on the head, the heart and the lungs in the chest, stand-in organs on the figure (triview/figure.py
# ORGANS), each its own thing. SENSE_PARTS is every part a sense can light, in the order the model's sense table
# holds them (triview/lidarscene.py sense_table).
ORGAN_PARTS = ["ear_l", "ear_r", "eye_l", "eye_r", "heart", "lung_l", "lung_r"]
SENSE_PARTS = list(PARTS) + ORGAN_PARTS
PART_INDEX = {p: i for i, p in enumerate(SENSE_PARTS)}

# The parts joined to each other at a joint (rung 2p). The stand-in shapes of joined parts overlap by construction (a
# joint's sphere sits in its neighbour's limb), so the model's contact test takes no touch between a part and the
# parts joined to it at one joint (own_parts); every other pair of parts touches where their surfaces meet (a hand on
# a thigh, a hand on the face, a forearm on the chest).
JOINED = [("head", "neck"), ("neck", "chest"), ("chest", "pelvis"), ("chest", "upper_arm_r"), ("chest", "upper_arm_l"),
          ("upper_arm_r", "forearm_r"), ("upper_arm_l", "forearm_l"), ("forearm_r", "hand_r"), ("forearm_l", "hand_l"),
          ("pelvis", "thigh_r"), ("pelvis", "thigh_l"), ("thigh_r", "shin_r"), ("thigh_l", "shin_l"),
          ("shin_r", "foot_r"), ("shin_l", "foot_l")]
NEAR_HOPS = 1
# His rule for a touch between two parts of the body (2026-11-13, thirteenth round): every pair but those joined at
# one joint. (Until then every part within two joints was left out, so a forearm on the chest, one thigh on the other
# and an upper arm against the neck were no touch.) The pairs two joints apart whose STAND-IN shapes run into each
# other by construction are named here and left out with them: LidarScene.read_pairs read every pair through the
# whole piece, and these three touch in every one of its 3,480 frames (the trunk's tube runs up into the head's ball
# and down into the tops of the thighs). They go with the stand-in mannequin, at rung 3.
FUSED_PAIRS = {("chest", "head"), ("chest", "thigh_l"), ("chest", "thigh_r")}


def near_parts(part, hops=NEAR_HOPS):
    """The part itself and every part within hops joints of it."""
    seen, edge = {part}, {part}
    for _ in range(hops):
        edge = {b if a in edge else a for a, b in JOINED if (a in edge) != (b in edge) or (a in edge and b in edge)} - seen
        seen |= edge
    return seen


def own_parts(part):
    """The parts whose surface meeting this part's is no touch: the part itself, the parts joined to it at one joint,
    and the parts its stand-in shape is fused with (FUSED_PAIRS). One rule for the spark's reading
    (LidarScene.read_pairs) and for the touch's glow (lidarscene.contact_nodes)."""
    out = near_parts(part, hops=1)
    for a, b in FUSED_PAIRS:
        if a == part:
            out.add(b)
        elif b == part:
            out.add(a)
    return out


# The point on a part where a sensation arises, as the joint that stands for it.
PART_POINT = {
    "head": "head", "neck": "neck", "chest": "chest", "pelvis": "pelvis",
    "upper_arm_r": "shoulder_r", "upper_arm_l": "shoulder_l",
    "forearm_r": "elbow_r", "forearm_l": "elbow_l",
    "hand_r": "hand_r", "hand_l": "hand_l",
    "thigh_r": "knee_r", "thigh_l": "knee_l",
    "shin_r": "ankle_r", "shin_l": "ankle_l",
    "foot_r": "toe_r", "foot_l": "toe_l",
    "ear_l": "head", "ear_r": "head", "eye_l": "head", "eye_r": "head",
    "heart": "chest", "lung_l": "chest", "lung_r": "chest",
}

# Joint chains from an extremity to the head: the roads comets and rivers run along.
CHAINS = {
    "arm_r": ["hand_r", "wrist_r", "elbow_r", "shoulder_r", "neck", "head"],
    "arm_l": ["hand_l", "wrist_l", "elbow_l", "shoulder_l", "neck", "head"],
    "leg_r": ["toe_r", "ankle_r", "knee_r", "hip_r", "pelvis", "chest", "neck", "head"],
    "leg_l": ["toe_l", "ankle_l", "knee_l", "hip_l", "pelvis", "chest", "neck", "head"],
    "torso": ["pelvis", "chest", "neck", "head"],
}

# Which chain carries a sensation that arises on a part.
PART_CHAIN = {
    "hand_r": "arm_r", "forearm_r": "arm_r", "upper_arm_r": "arm_r",
    "hand_l": "arm_l", "forearm_l": "arm_l", "upper_arm_l": "arm_l",
    "foot_r": "leg_r", "shin_r": "leg_r", "thigh_r": "leg_r",
    "foot_l": "leg_l", "shin_l": "leg_l", "thigh_l": "leg_l",
    "pelvis": "torso", "chest": "torso", "neck": "torso", "head": "torso",
}

def part_axis(part):
    """A part's own axis, as two joints of its chain: the end farther from the head and the end nearer it (one joint
    twice where the part has one). Read off the part's joints and bones and the order of its chain, so it holds for any
    figure whose parts and chains are named here: a forearm runs from its wrist to its elbow, a shin from its ankle to
    its knee. A touch's spark enters the limb at the touched place, joins this axis and runs along it to the nearer
    end and on up the chain (triview/engine.py). (Until the audit of 2026-11-15 a spark started at PART_POINT: the
    elbow for a forearm, the nearer end, but the ankle for a shin, the farther one, wherever the touch was.)"""
    chain = CHAINS[PART_CHAIN[part]]
    spec = PARTS[part]
    ends = [j for j in spec["joints"] + spec["bones"] if j in chain]
    if not ends:
        ends = [PART_POINT[part]] if PART_POINT[part] in chain else [chain[0]]
    return min(ends, key=chain.index), max(ends, key=chain.index)


# Sense families and their colours (concept section 8).
# (rung 2p: hearing a radar green, pain red, pleasure a sunlight gold, his specification of 2026-11-12)
SENSE_COLOUR = {
    "sight": mats.GOLD,
    "hearing": mats.RADAR,
    "airflow": mats.COOL,
    "touch": mats.MAGENTA,
    "temperature": mats.SUN_GOLD,
    "pain": mats.RED,
    "pleasure": mats.WARM_GOLD,
    "proprioception": mats.MINT,
    "effort": mats.LIME,
    "balance": mats.VIOLET,
    "breath": mats.WHITE,
    "heartbeat": mats.WHITE,
    "will": mats.WHITE,
    "memory": mats.GREY,
}

# A sound's rings take a shade of the radar's green by their source (his word of 2026-11-13: slightly different
# colours, so sounds that ring together can be told apart): the first source of the timeline the green itself, the
# later ones turned toward blue or toward yellow by these shares of the colour wheel, paler or fuller.
SOUND_SHADES = [(0.0, 0.75), (0.085, 0.80), (-0.085, 0.80), (0.045, 0.50), (-0.045, 0.55), (0.12, 0.70)]


def sound_shade(k):
    """The k-th sound source's green: the radar's hue turned and its fullness set by SOUND_SHADES, as bright."""
    import colorsys
    h, s_, v = colorsys.rgb_to_hsv(*mats.RADAR)
    dh, sat = SOUND_SHADES[k % len(SOUND_SHADES)]
    return tuple(colorsys.hsv_to_rgb((h + dh) % 1.0, sat, v))


# What each surface and part looks like in the mind once a sense has reached it (his review of
# 2026-11-07: the model coloured as the room is, not in the sense's colour; the sense colours stay
# on the signals). The room's own materials, lifted a little where they are dark.
_WALL = (0.74, 0.71, 0.65)
_WOOD = (0.40, 0.27, 0.16)
_SKIN = (0.62, 0.42, 0.32)
_CLOTH = (0.34, 0.35, 0.38)
SURFACE_COLOUR = {
    "floor": (0.46, 0.30, 0.17), "ceiling": (0.86, 0.86, 0.84),
    "wall_n": _WALL, "wall_s": _WALL, "wall_e": _WALL, "wall_w": _WALL,
    "window": (0.62, 0.76, 0.92), "sill": (0.90, 0.90, 0.88), "bed": (0.86, 0.85, 0.80),
    "table": _WOOD, "table_far": _WOOD, "table_edge": _WOOD,
    "rug": (0.64, 0.27, 0.20), "rug_edge": (0.64, 0.27, 0.20),
    "phone": (0.75, 0.85, 1.0), "ridge": (0.55, 0.46, 0.34), "sun": mats.GOLD, "ground": (0.50, 0.44, 0.30),
}
PART_COLOUR = {
    "head": _SKIN, "neck": _SKIN, "chest": _CLOTH, "pelvis": _CLOTH,
    "upper_arm_r": _CLOTH, "upper_arm_l": _CLOTH, "forearm_r": _SKIN, "forearm_l": _SKIN,
    "hand_r": _SKIN, "hand_l": _SKIN, "thigh_r": _CLOTH, "thigh_l": _CLOTH,
    "shin_r": _SKIN, "shin_l": _SKIN, "foot_r": _SKIN, "foot_l": _SKIN,
    "ear_l": _SKIN, "ear_r": _SKIN, "eye_l": _SKIN, "eye_r": _SKIN,
    "heart": mats.HEART_RED, "lung_l": mats.LUNG_PINK, "lung_r": mats.LUNG_PINK,
}

# The four states of knowing.
DARK, FILLED, REMEMBERED, SENSED = "dark", "filled", "remembered", "sensed"

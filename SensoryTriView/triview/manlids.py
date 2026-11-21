"""His lids (rung 3): the eye table's cover moves his lid bones.

The eye table (renders/rung2p/eye_frames.json, built by triview/eye.py) holds for every frame how far his lids cover
his eyes: 0 open, 1 shut. It is the same number the First-Person view draws its own lids from, so the lids seen from
outside and the lids seen from inside move together.

The generator's skeleton has an upper and a lower lid bone for each eye, both hinged at the eyeball's middle and
pointing forward: orbicularis03 the upper, orbicularis04 the lower. Turning one about its own X axis swings its lid
over the eyeball: the upper lid comes down with a negative turn, the lower lid comes up with a positive one. The upper
lid does about three quarters of the travel, as a real lid does and as the First-Person view's lids do
(tools/assemble_rung2.py, upper_share 0.75). His lashes ride the same bones.

Stand-in or staying: staying. The two angles of a shut eye are set by eye on this generator's face (SHUT).
"""
import math

UPPER, LOWER = "orbicularis03.{s}", "orbicularis04.{s}"
SHUT = {"upper_deg": -27.0, "lower_deg": 9.0,      # each lid's turn when the eye is shut
        "upper_out": 0.002, "lower_out": 0.0006}    # metres each lid moves out along its bone as it shuts: a lid rides
                                                    # over the cornea's bulge (on the third man the iris came through
                                                    # the shut lid as a dark dot, 2026-11-19)


def turn(cover):
    """The share of the shut angles for a cover of 0 to 1. The lids meet at about 0.6 of the shut angles and the rest
    presses them together, so the share rises as 0.62 of the cover while the eye is open (half covered at a cover of
    0.5, seen 2026-11-19: at half the shut angles only a slit was left) and reaches the whole by a cover of 1."""
    c = min(max(float(cover), 0.0), 1.0)
    return 0.62 * c + 0.38 * c ** 6


def pose(rig, cover, shut=None):
    """Set his four lid bones for a cover of 0 to 1, now."""
    shut = shut or SHUT
    for s in "LR":
        for name, deg, out in ((UPPER, shut["upper_deg"], shut.get("upper_out", 0.0)), (LOWER, shut["lower_deg"], shut.get("lower_out", 0.0))):
            pb = rig.pose.bones[name.format(s=s)]
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (math.radians(deg * turn(cover)), 0.0, 0.0)
            pb.location = (0.0, out * turn(cover), 0.0)


def steady_brows(body, card_weight):
    """The skin under his eyebrows no longer moves with the upper lid. His brows sit low, right over the lid, and the
    generator weights that skin to the upper lid's bone: on a blink it slid under the brow's strands, which ride the
    head, and the brow thinned for the length of the blink (seen 2026-11-19). Where the brow grows, and a little
    under its lower edge, the lid bone's share of each skin point is handed to the head bone. `card_weight` is the
    brow card's measure (triview/manhair._card_weight). Returns the number of skin points changed."""
    import numpy as np
    from . import manhair
    vp = manhair._base_points(body)
    up = np.array((0.0, 0.0, 1.0))
    k = np.clip(card_weight(vp) / 0.12, 0.0, 1.0)
    k = np.maximum(k, 0.6 * np.clip(card_weight(vp + up * 0.003) / 0.12, 0.0, 1.0))
    head = body.vertex_groups.get("head") or body.vertex_groups.new(name="head")
    changed = 0
    for s in "LR":
        group = body.vertex_groups.get(UPPER.format(s=s))
        if group is None:
            continue
        gi = group.index
        for v in body.data.vertices:
            kv = float(k[v.index])
            if kv <= 0.0:
                continue
            w = next((e.weight for e in v.groups if e.group == gi), 0.0)
            if w > 0.0:
                group.add([v.index], w * (1.0 - kv), "REPLACE")
                head.add([v.index], w * kv, "ADD")
                changed += 1
    return changed


def bake(rig, rows, shut=None):
    """Key his lid bones for every frame of the eye table. A key is written where the cover changes and on the frames
    either side of a change, so the curve holds still between. Returns the number of frames keyed."""
    shut = shut or SHUT
    rows = sorted(rows, key=lambda r: r["f"])
    covers = [float(r.get("cover", 0.0)) for r in rows]
    keyed = 0
    for s in "LR":
        for name, deg, out in ((UPPER, shut["upper_deg"], shut.get("upper_out", 0.0)), (LOWER, shut["lower_deg"], shut.get("lower_out", 0.0))):
            pb = rig.pose.bones[name.format(s=s)]
            pb.rotation_mode = "XYZ"
            for i, r in enumerate(rows):
                c = covers[i]
                moving = (i == 0 or i == len(rows) - 1 or abs(covers[i - 1] - c) > 1e-4 or abs(covers[i + 1] - c) > 1e-4)
                if not moving:
                    continue
                pb.rotation_euler = (math.radians(deg * turn(c)), 0.0, 0.0)
                pb.keyframe_insert("rotation_euler", index=0, frame=r["f"])
                pb.location = (0.0, out * turn(c), 0.0)
                pb.keyframe_insert("location", index=1, frame=r["f"])
                keyed += 1
    # straight lines between keys: the table already carries the lids' easing frame by frame
    action = rig.animation_data.action if rig.animation_data else None
    if action is not None:
        curves = []
        try:
            curves = list(action.fcurves)
        except AttributeError:
            for layer in action.layers:
                for strip in layer.strips:
                    for bag in strip.channelbags:
                        curves += list(bag.fcurves)
        for fc in curves:
            if "orbicularis" in fc.data_path:
                for k in fc.keyframe_points:
                    k.interpolation = "LINEAR"
    return keyed // 4

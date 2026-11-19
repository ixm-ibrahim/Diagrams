"""The True-Person scene: a still white glass figure in the dark, the soul above its
head, and inside the skull the mind's own model of the room and the body.

This rung draws a first sketch of the model by hand from the room's state. Rung 1
replaces the sketch with the engine that computes it from the scene every frame; the
pieces here (plates with edge lines, the simulated body, rays, the plumb line, words)
are the same pieces the engine will place.
"""
import math
from dataclasses import dataclass

import bpy
from mathutils import Matrix, Vector

from . import figure, geo, materials as mats, render


@dataclass
class MindSpec:
    model_scale: float = 1.0 / 24.0        # the room inside the skull: a few times smaller than the ghost's head
    held_depth: float = 3.0                # how far north of the south wall the mind holds the room
    ghost_location: tuple = (0.0, 0.0, 0.0)
    ghost_yaw_deg: float = 0.0
    ghost_edge_strength: float = 1.0
    ghost_fill: float = 0.02
    soul_radius: float = 0.045             # a closed hand
    soul_gap: float = 0.10                 # a hand's width above the crown
    soul_strength: float = 6.0
    # close, in front of the face and a little above: the skull fills the frame under the soul's light
    camera: tuple = ((1.9, 0.0, 1.84), (0.0, 0.0, 1.73), 50.0)
    plate_strength: float = 0.28           # remembered grey plates, faint
    far_plate_strength: float = 0.14       # the wall at his back, held but out of mind
    plate_edge_gain: float = 1.5
    edge_thickness: float = 0.03           # room metres, before the model scale
    ahead_face_alpha: float = 0.12         # a plate between the camera and the simulated body thins to its edges
    window_strength: float = 0.9           # a faint gold rectangle ahead
    window_face_alpha: float = 0.4
    body_strength: float = 0.4             # the simulated body, grey from memory
    sight_strength: float = 2.5            # the gold hand and phone
    ray_strength: float = 3.0
    ray_rows: int = 3
    ray_cols: int = 5
    ray_radius: float = 0.011
    plumb_strength: float = 2.5
    words: tuple = ("alarm", "phone", "bed", "table", "window", "sun", "rug", "cup", "door", "cat")
    lit_word: str = "phone"
    word_size: float = 0.26
    words_offset: float = 1.25             # room metres to the head's left, past the window's edge
    words_top: float = 1.55
    unlit_strength: float = 0.09           # a step darker than any surface he still holds
    lit_strength: float = 3.0
    bloom: bool = True
    bloom_threshold: float = 1.0
    bloom_strength: float = 0.35
    bloom_size: float = 0.6


def _plate_object(name, bm_fill, face_mat, edge_mat, parent, col, edge_thickness):
    """Finish a bmesh as a plate with a brighter edge line through a wireframe modifier."""
    obj = geo.finish(bm_fill, name, [face_mat, edge_mat], col, parent)
    wf = obj.modifiers.new("Edge", "WIREFRAME")
    wf.thickness = edge_thickness
    wf.use_replace = False
    wf.use_boundary = True
    wf.use_even_offset = True
    wf.material_offset = 1
    return obj


def build_true_scene(name, spec: MindSpec, room_info):
    """Create the True-Person scene from the room's state and return its key objects.

    room_info is the dict build_room returns: the man's pose, placement, head position,
    phone matrix and the room spec, from which the model inside the skull is drawn.
    """
    scene = bpy.data.scenes.new(name)
    col = scene.collection
    scene.world = mats.black_world("Dark")
    render.setup_eevee(scene)

    cam_loc, cam_target, cam_lens = spec.camera
    camera = geo.add_camera("Cam_True", cam_loc, cam_target, lens=cam_lens, clip_start=0.02, collection=col)
    scene.camera = camera

    # The ghost: the same mannequin, standing, in white glass
    glass = mats.ghost_glass("GhostGlass", edge_strength=spec.ghost_edge_strength, fill=spec.ghost_fill)
    pose_stand = figure.standing()
    place_ghost = figure.placement(spec.ghost_location, spec.ghost_yaw_deg)
    ghost, ghost_head, gpoints = figure.build("Ghost", pose_stand, {"skin": glass, "cloth": glass}, place_ghost, col,
                                              segments=24)

    # The soul: a soft white disc a hand's width above the crown, facing the camera
    crown = figure.crown(pose_stand, place_ghost)
    bm = geo.new_bmesh()
    geo.add_disc(bm, (0, 0, 0), spec.soul_radius, 0, segments=96)
    soul = geo.finish(bm, "Soul", [mats.soul_disc("Soul", spec.soul_radius, spec.soul_strength)], col)
    soul.location = crown + Vector((0.0, 0.0, spec.soul_gap + spec.soul_radius))
    geo.track_to(soul, camera, "TRACK_Z", "UP_Y")

    # The model frame: the head's own frame, scaled into the skull.
    # Room points map into it by to_head: translate by minus the real head, undo the head's yaw.
    head_world = Vector(room_info["head_world"])
    yaw = math.radians(room_info["spec"].man_yaw_deg)
    to_head = Matrix.Rotation(-yaw, 4, "Z") @ Matrix.Translation(-head_world)
    frame = geo.add_empty("ModelFrame", gpoints["head"], scale=spec.model_scale, collection=col)
    frame.rotation_euler = (0.0, 0.0, math.radians(spec.ghost_yaw_deg))

    rspec = room_info["spec"]
    W, D, H = rspec.size
    wy0, wy1, wz0, wz1 = rspec.window
    # what the mind holds of the room: the part he sits in, out to the window wall
    hold_y0, hold_y1 = 0.0, min(D, spec.held_depth)

    def hp(x, y, z):
        return to_head @ Vector((x, y, z))

    grey_face, grey_edge = mats.plate("Remembered", mats.GREY, spec.plate_strength, spec.plate_edge_gain)
    far_face, far_edge = mats.plate("RememberedFar", mats.GREY, spec.far_plate_strength, spec.plate_edge_gain)
    # the wall ahead and the window in it lie between this camera and the simulated body: edges, faint faces
    ahead_face, ahead_edge = mats.plate("RememberedAhead", mats.GREY, spec.plate_strength, spec.plate_edge_gain,
                                        face_alpha=spec.ahead_face_alpha)
    gold_face, gold_edge = mats.plate("Seen", mats.GOLD, spec.window_strength, spec.plate_edge_gain,
                                      face_alpha=spec.window_face_alpha)
    et = spec.edge_thickness

    bm = geo.new_bmesh()
    geo.add_quad(bm, hp(0, hold_y0, 0), hp(W, hold_y0, 0), hp(W, hold_y1, 0), hp(0, hold_y1, 0))
    floor = _plate_object("Model_Floor", bm, grey_face, grey_edge, frame, col, et)

    bm = geo.new_bmesh()
    # the window wall, four quads around the opening, in head coordinates
    def wall_pt(y, z):
        return hp(W, y, z)
    for a0, a1, b0, b1 in ((hold_y0, hold_y1, 0, wz0), (hold_y0, hold_y1, wz1, H), (hold_y0, wy0, wz0, wz1), (wy1, hold_y1, wz0, wz1)):
        geo.add_quad(bm, wall_pt(a0, b0), wall_pt(a1, b0), wall_pt(a1, b1), wall_pt(a0, b1))
    wall_e = _plate_object("Model_WallEast", bm, ahead_face, ahead_edge, frame, col, et)

    bm = geo.new_bmesh()
    geo.add_quad(bm, hp(0, hold_y0, 0), hp(0, hold_y0, H), hp(0, hold_y1, H), hp(0, hold_y1, 0))
    wall_w = _plate_object("Model_WallWest", bm, far_face, far_edge, frame, col, et)

    bm = geo.new_bmesh()
    geo.add_quad(bm, wall_pt(wy0, wz0), wall_pt(wy1, wz0), wall_pt(wy1, wz1), wall_pt(wy0, wz1))
    window = _plate_object("Model_Window", bm, gold_face, gold_edge, frame, col, et)

    bm = geo.new_bmesh()
    (bx0, by0, bz0), (bx1, by1, bz1) = rspec.bed
    geo.add_box(bm, (bx0, by0, bz0), (bx1, by1, bz1), 0, matrix=to_head)
    bed = _plate_object("Model_Bed", bm, grey_face, grey_edge, frame, col, et)

    bm = geo.new_bmesh()
    (tx0, ty0, tz0), (tx1, ty1, tz1) = rspec.table
    geo.add_box(bm, (tx0, ty0, tz0), (tx1, ty1, tz1), 0, matrix=to_head)
    table = _plate_object("Model_Table", bm, grey_face, grey_edge, frame, col, et)

    # The simulated body: the sitting pose, grey from memory, the right hand gold under the rays
    body_grey = mats.emission("SimBody", mats.GREY, spec.body_strength)
    sight = mats.emission("SimSight", mats.GOLD, spec.sight_strength)
    place_body = to_head @ room_info["place"]
    sim_body, sim_head, spoints = figure.build("SimBody", room_info["pose"],
                                               {"skin": body_grey, "cloth": body_grey, "sight": sight},
                                               place_body, col, parent=frame, overrides={"hand_r": "sight"},
                                               segments=12)

    # The phone, gold, known by sight
    pm = to_head @ room_info["phone_matrix"]
    L_, W_, T_ = rspec.phone_size
    bm = geo.new_bmesh()
    screen = mats.emission("SimScreen", mats.GOLD, spec.sight_strength * 1.6)
    geo.add_box(bm, (-L_ / 2, -W_ / 2, -T_ / 2), (L_ / 2, W_ / 2, T_ / 2), 0, matrix=pm, top_mat_index=1)
    sim_phone = geo.finish(bm, "SimPhone", [sight, screen], col, frame)

    # The fan of gold rays from the simulated eyes to the screen, brightest at the centre
    eye = spoints["eye"]
    ray_c = mats.emission("RayCentre", mats.GOLD, spec.ray_strength)
    ray_o = mats.emission("RayOuter", mats.GOLD, spec.ray_strength * 0.5)
    bm = geo.new_bmesh()
    rows, cols = spec.ray_rows, spec.ray_cols
    for i in range(rows):
        for j in range(cols):
            u = -0.5 + (i + 0.5) / rows
            v = -0.5 + (j + 0.5) / cols
            target = pm @ Vector((v * L_ * 1.15, u * W_ * 1.3, T_ / 2))
            central = abs(u) < 0.34 and abs(v) < 0.3
            geo.add_segment(bm, eye, target, spec.ray_radius * (1.0 if central else 0.75), None,
                            0 if central else 1, segments=6)
    rays = geo.finish(bm, "Rays", [ray_c, ray_o], col, frame)

    # The plumb line of balance: from the inner ear straight down to the floor
    violet = mats.emission("Plumb", mats.VIOLET, spec.plumb_strength)
    ear = spoints["head"] + Vector((0.0, -0.07, 0.0))
    floor_z = hp(0, 0, 0).z
    bm = geo.new_bmesh()
    geo.add_segment(bm, ear, (ear.x, ear.y, floor_z + 0.02), 0.012, None, 0, segments=8)
    geo.add_sphere(bm, (ear.x, ear.y, floor_z + 0.035), 0.035, 0, segments=12, rings=8)
    plumb = geo.finish(bm, "PlumbLine", [violet], col, frame)

    # Words of recognition to the left of the simulated head, upright, facing the camera
    unlit = mats.emission("WordUnlit", mats.GREY, spec.unlit_strength)
    lit = mats.emission("WordLit", mats.WHITE, spec.lit_strength)
    # one loose column to the head's left, clear of the window's edge, each word left-aligned so
    # none overlaps another; a small drift in x and y keeps it a jumble rather than a list
    words = []
    head_c = spoints["head"]
    clear_y = head_c.y + spec.words_offset
    for k, w in enumerate(spec.words):
        y = clear_y + (0.10 if k % 3 == 1 else 0.0) + (0.05 if k % 3 == 2 else 0.0)
        z = head_c.z + spec.words_top - k * spec.word_size * 1.3
        x = head_c.x + 0.3 + (0.15 if k % 2 else -0.1)
        mat = lit if w == spec.lit_word else unlit
        t = geo.add_text(f"Word_{w}", w, spec.word_size, (x, y, z), mat, col, frame, align="LEFT")
        geo.track_to(t, camera, "TRACK_Z", "UP_Y")
        words.append(t)

    bloom = None
    if spec.bloom:
        bloom = render.bloom_compositor(scene, spec.bloom_threshold, spec.bloom_strength, spec.bloom_size)

    return {
        "scene": scene, "camera": camera, "ghost": ghost, "ghost_head": ghost_head, "soul": soul,
        "frame": frame, "plates": [floor, wall_e, wall_w, window, bed, table],
        "sim_body": sim_body, "sim_head": sim_head, "sim_phone": sim_phone, "rays": rays, "plumb": plumb,
        "words": words, "bloom": bloom, "ghost_points": gpoints,
    }

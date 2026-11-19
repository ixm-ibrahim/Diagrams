"""The photoreal room: floor, walls, open window, bed, table, rug, the dawn outside,
the man, the phone, and the Third-Person and First-Person cameras. Everything is
parameters on RoomSpec so later rungs move things without touching the code.

Layout (concept section 7): the bed along the west wall running north to south with
the pillow at the south end, the table east of the bed beside the pillow with its top
level with the mattress and a hand's gap north of it beside his thigh, the window on
the east wall in front of the man, the rug between the bed and the window with its
near edge curled.

build_room builds rung 0's still (the man sitting from the pose tables).
build_room_animated builds rung 1's scene: the man as joint Empties with constrained
limbs over the whole chain, the phone and the blanket baked, the sun climbing, a lamp
for EEVEE proxies, and every surface tagged for the engine.
"""
import math
from dataclasses import dataclass

import bpy
from mathutils import Matrix, Vector

from . import anim, body, cameras, figure, geo, materials as mats, tags


@dataclass
class RoomSpec:
    size: tuple = (4.0, 4.5, 2.6)
    bed: tuple = ((0.10, 0.10, 0.00), (1.50, 2.10, 0.55))
    bed_base_top: float = 0.35
    pillow: tuple = ((0.30, 0.15, 0.55), (1.30, 0.62, 0.66))
    blanket: tuple = ((0.15, 0.95, 0.55), (1.25, 2.05, 0.63))
    table: tuple = ((1.60, 0.02, 0.00), (2.05, 0.47, 0.55))
    window: tuple = (0.5, 1.9, 0.9, 2.1)          # y0, y1, z0, z1 on the east wall
    wall_thickness: float = 0.12
    rug: tuple = (2.45, 3.6, 0.3, 1.7)            # x0, x1, y0, y1
    rug_curl_length: float = 0.28
    rug_curl_height: float = 0.07
    ridge_distance: float = 300.0                  # the stand-in range's crest (80 m until his review of 2026-11-08, second)
    sun_elevation_deg: float = -4.0
    sun_azimuth_deg: float = 0.0                   # east
    sun_rotation_deg: float | None = None          # None: derived from the azimuth
    sky_aerosol: float = 1.4
    sun_intensity: float = 1.0                     # the sky's sun strength; rung 2 raises it so sunlit skin outshines the screen
    sun_disc_standin: bool = False                 # a disc only the camera sees, far along the sun's line: the glare the sky's own disc never shows
    sun_disc_strength: float = 2000.0
    man_location: tuple = (1.38, 0.75, 0.0)
    man_yaw_deg: float = 0.0
    seat_height: float = 0.55
    phone_size: tuple = (0.15, 0.072, 0.0075)      # length (forward), width, thickness
    screen_strength: float = 6.0
    third_camera: tuple = ((3.3, 4.2, 1.6), (2.3, 0.85, 1.0), 28.0)
    proxy_camera: tuple = ((3.7, 4.1, 2.3), (1.7, 0.9, 0.7), 22.0)
    first_lens: float = 20.0
    portal: bool = True
    # the dawn over the scene: (seconds, sun elevation in degrees). The range's skyline on the sun's line stands
    # 6.77 degrees up from his eyes bent over the phone (its near shoulder overtops its crest, which stands 6.6:
    # measured in the built scene, 2026-11-16) and 6.74 from his eyes at the window, so first light is the disc's
    # upper limb over it at 40.2 s, and the disc is clear of it 40 s later as he closes his eyes in it: three
    # times nature's pace, where it took half a second before his review of 2026-11-07. The night brightens far
    # faster before that, which no eye can clock. (6.33, 6.87, 7.36 until 2026-11-16, worked out for the crest's
    # 6.6: in the scene as built the limb then cleared the range at 53 s, and his hand rose 13 s before any light
    # could reach him. The build prints the scene's own first light: rungs/rung2.py, FIRST LIGHT.)
    # (the turn in the sun's path a tenth of a second after first light, so the limb crosses the skyline at the
    # night's pace and stands a thirtieth of a degree over it three frames on, whatever his head does. Until 38 s
    # the path is the one every picture of the first 38 s was rendered under, 5.764677 being its height there;
    # from there it climbs a third faster to first light, the disc's centre at 6.5062 at 40.2 s and 6.4950 a frame
    # before, either side of the 6.5005 at which the limb of the sky's own disc, 0.2725 in radius, meets the skyline)
    sun_keys: tuple = ((0.0, -4.0), (38.0, 5.764677), (40.3, 6.5399), (80.0, 7.02), (116.0, 7.51))
    pane: bool = True                              # a glass leaf hinged on the north jamb, swung open outward
    pane_open_deg: float = 80.0
    standins: bool = False                         # stand-in furniture and trees (his review of 2026-11-08), until rung 5 dresses the room


def _room_materials():
    return {
        "wall": mats.principled("Wall", (0.74, 0.71, 0.65), roughness=0.85),
        "ceiling": mats.principled("Ceiling", (0.86, 0.86, 0.84), roughness=0.9),
        "floor": mats.principled("Floor", (0.33, 0.21, 0.12), roughness=0.4),
        "bed_base": mats.principled("BedBase", (0.20, 0.17, 0.14), roughness=0.7),
        "mattress": mats.principled("Mattress", (0.86, 0.85, 0.80), roughness=0.9),
        "pillow": mats.principled("Pillow", (0.92, 0.92, 0.90), roughness=0.95),
        "blanket": mats.principled("Blanket", (0.17, 0.21, 0.34), roughness=0.95),
        "table": mats.principled("Table", (0.26, 0.17, 0.10), roughness=0.45),
        "rug": mats.principled("Rug", (0.46, 0.19, 0.14), roughness=0.95),
        "frame": mats.principled("WindowFrame", (0.90, 0.90, 0.88), roughness=0.5),
        "ground": mats.principled("Ground", (0.42, 0.34, 0.20), roughness=1.0),   # an earth apart from the bushes' green (his eleventh review of 2026-11-11)
        "ridge": mats.principled("Ridge", (0.30, 0.26, 0.23), roughness=1.0),
        "skin": mats.principled("Skin", (0.62, 0.42, 0.32), roughness=0.5, subsurface=0.12),
        "cloth": mats.principled("Cloth", (0.34, 0.35, 0.38), roughness=0.9),
        "phone": mats.principled("Phone", (0.02, 0.02, 0.022), roughness=0.3),
        # the stand-in heart and lungs inside the chest (rung 2p): never seen in the room, their colours are what the
        # mind draws them in when it thinks of them
        "heart": mats.principled("Heart", (0.55, 0.06, 0.06), roughness=0.5),
        "lung": mats.principled("Lung", (0.75, 0.45, 0.45), roughness=0.6),
    }


def _build_shell(spec, m, col):
    """Floor, ceiling and four walls (east with the window), each its own object tagged with its region,
    so the engine's rays and the mind's model read a thing off the object it strikes (his sixth review
    of 2026-11-09: each thing in the scene has the same properties)."""
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    shell = []

    def part(name, tag, mat, add):
        bm = geo.new_bmesh()
        add(bm)
        ob = geo.finish(bm, name, [mat], col)
        ob[tags.TAG_PROP] = tag
        shell.append(ob)
        return ob

    part("Floor", "floor", m["floor"], lambda bm: geo.add_quad(bm, (0, 0, 0), (W, 0, 0), (W, D, 0), (0, D, 0), 0))
    part("Ceiling", "ceiling", m["ceiling"], lambda bm: geo.add_quad(bm, (0, 0, H), (0, D, H), (W, D, H), (W, 0, H), 0))
    part("Wall_W", "wall_w", m["wall"], lambda bm: geo.add_quad(bm, (0, 0, 0), (0, D, 0), (0, D, H), (0, 0, H), 0))
    part("Wall_S", "wall_s", m["wall"], lambda bm: geo.add_quad(bm, (0, 0, 0), (0, 0, H), (W, 0, H), (W, 0, 0), 0))
    part("Wall_N", "wall_n", m["wall"], lambda bm: geo.add_quad(bm, (0, D, 0), (W, D, 0), (W, D, H), (0, D, H), 0))
    part("Wall_E", "wall_e", m["wall"], lambda bm: geo.add_rect_with_hole(bm, "x", W, 0, D, 0, H, wy0, wy1, wz0, wz1, 0))
    return shell


def _build_frame(spec, m, col):
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    bm = geo.new_bmesh()
    t = spec.wall_thickness
    f = 0.05
    x0, x1 = W - 0.02, W + t
    geo.add_box(bm, (x0, wy0 - f, wz0 - f), (x1, wy1 + f, wz0), 0)
    geo.add_box(bm, (x0, wy0 - f, wz1), (x1, wy1 + f, wz1 + f), 0)
    geo.add_box(bm, (x0, wy0 - f, wz0), (x1, wy0, wz1), 0)
    geo.add_box(bm, (x0, wy1, wz0), (x1, wy1 + f, wz1), 0)
    geo.add_box(bm, (W - 0.07, wy0 - 0.07, wz0 - f - 0.03), (x1, wy1 + 0.07, wz0 - f), 0)  # sill
    frame = geo.finish(bm, "WindowFrame", [m["frame"]], col)
    frame[tags.TAG_PROP] = "wall_e"
    frame[tags.OF_PROP] = "Wall_E"
    frame["tv_poly_tags"] = ["wall_e"] * 24 + ["sill"] * 6
    return frame


def _build_pane(spec, col):
    """The open window's glass: one leaf hinged on the north jamb and swung outward (the concept has
    the window open; the stand-in room had a bare opening until his review of 2026-11-07), as two
    things: its wooden frame, which the eyes' rays strike like any surface, and its glass alone, which
    they pass through (tags.PASS_PROP) and which casts no shadow, so the sun comes in as before. With
    the leaf one thing the rays passed its frame too, and the mind's picture painted the frame onto the
    ground and the range beyond it (his seventh review of 2026-11-10: the window stretched to the
    mountains). Returns (frame, glass)."""
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    t = spec.wall_thickness
    width = (wy1 - wy0) - 0.02
    z0, z1 = wz0 + 0.01, wz1 - 0.01
    f, th = 0.045, 0.035
    # the leaf lies along local -y from the hinge at the origin, its thickness along local x
    bm = geo.new_bmesh()
    geo.add_box(bm, (-th / 2, -width, z0), (th / 2, 0.0, z0 + f), 0)
    geo.add_box(bm, (-th / 2, -width, z1 - f), (th / 2, 0.0, z1), 0)
    geo.add_box(bm, (-th / 2, -f, z0), (th / 2, 0.0, z1), 0)
    geo.add_box(bm, (-th / 2, -width, z0), (th / 2, -width + f, z1), 0)
    frame = geo.finish(bm, "PaneFrame", [mats.principled("PaneFrame", (0.90, 0.90, 0.88), roughness=0.5)], col)
    bm = geo.new_bmesh()
    geo.add_quad(bm, (0.0, -width + f, z0 + f), (0.0, -f, z0 + f), (0.0, -f, z1 - f), (0.0, -width + f, z1 - f), 0)
    glass = geo.finish(bm, "PaneGlass", [mats.glass_pane("PaneGlass")], col)
    glass[tags.PASS_PROP] = 1.0
    glass.visible_shadow = False
    for ob in (frame, glass):
        ob.location = (W + t - 0.02, wy1 - 0.01, 0.0)
        ob.rotation_euler = (0.0, 0.0, math.radians(spec.pane_open_deg))
        ob[tags.TAG_PROP] = "window"
        ob[tags.OF_PROP] = "WindowFrame"
    return frame, glass


def _build_bed(spec, m, col, with_blanket=True):
    bm = geo.new_bmesh()
    (bx0, by0, bz0), (bx1, by1, bz1) = spec.bed
    geo.add_box(bm, (bx0, by0, bz0), (bx1, by1, spec.bed_base_top), 0)
    geo.add_box(bm, (bx0 + 0.02, by0 + 0.02, spec.bed_base_top), (bx1 - 0.02, by1 - 0.02, bz1), 1)
    geo.add_box(bm, spec.pillow[0], spec.pillow[1], 2)
    bmats = [m["bed_base"], m["mattress"], m["pillow"]]
    if with_blanket:
        geo.add_box(bm, spec.blanket[0], spec.blanket[1], 3)
        bmats.append(m["blanket"])
    bed = geo.finish(bm, "Bed", bmats, col)
    bed[tags.TAG_PROP] = "bed"
    return bed


def _build_blanket(spec, m, col):
    bm = geo.new_bmesh()
    geo.add_box(bm, spec.blanket[0], spec.blanket[1], 0)
    blanket = geo.finish(bm, "Blanket", [m["blanket"]], col)
    blanket[tags.TAG_PROP] = "bed"
    blanket[tags.OF_PROP] = "Bed"
    return blanket


def _build_table(spec, m, col):
    bm = geo.new_bmesh()
    (tx0, ty0, tz0), (tx1, ty1, tz1) = spec.table
    geo.add_box(bm, (tx0, ty0, tz1 - 0.03), (tx1, ty1, tz1), 0)
    leg = 0.04
    for lx in (tx0 + 0.02, tx1 - 0.02 - leg):
        for ly in (ty0 + 0.02, ty1 - 0.02 - leg):
            geo.add_box(bm, (lx, ly, tz0), (lx + leg, ly + leg, tz1 - 0.03), 0)
    geo.add_box(bm, (tx0 + 0.03, ty0 + 0.03, 0.12), (tx1 - 0.03, ty1 - 0.03, 0.14), 0)  # a low shelf
    table = geo.finish(bm, "Table", [m["table"]], col)
    table[tags.TAG_PROP] = "table"
    return table


def _build_rug(spec, m, col):
    rx0, rx1, ry0, ry1 = spec.rug
    L, Hc = spec.rug_curl_length, spec.rug_curl_height

    def rug_point(u, v):
        x = rx0 + (rx1 - rx0) * u
        y = ry0 + (ry1 - ry0) * v
        d = x - rx0
        z = 0.0
        if d < L:
            tt = 1.0 - d / L
            z = Hc * tt * tt
            x += 0.5 * Hc * tt * tt
        return (x, y, z)

    bm = geo.new_bmesh()
    geo.add_grid(bm, 48, 12, rug_point, 0, smooth=True)
    rug = geo.finish(bm, "Rug", [m["rug"]], col)
    sol = rug.modifiers.new("Thickness", "SOLIDIFY")
    sol.thickness = 0.012
    sol.offset = 1.0
    rug[tags.TAG_PROP] = "rug"
    rug[tags.OF_PROP] = "Floor"
    rug["tv_curl_x"] = rx0 + L
    return rug


RANGE_DEPTH_SHARE = 0.45     # the range's slopes run this share of its distance in front of and behind the crest
RANGE_EYE = (1.5, 0.75, 1.2)  # the eyes the crest's elevations are measured from: on the bed
RIDGE_ELEVATION = 6.6        # degrees up from those eyes on the sun's line, at the crest's own line 300 m off. The skyline his
                             # eyes have is higher, 6.77: the range's near shoulder, 17 m nearer, overtops the crest


def range_elevation(theta_deg):
    """The crest's elevation in degrees from his eyes by azimuth (degrees, north positive): a saddle
    on the sun's line that keeps first light's time, the tallest peak 13 degrees left of it, another
    right, lesser ones beyond (his review of 2026-11-08, second: a range with a tall peak, not a line)."""
    def bump(c, w):
        return math.exp(-((theta_deg - c) / w) ** 2)
    peaks = (4.6 * bump(13.0, 6.0) + 3.3 * bump(-16.0, 7.5) + 2.2 * bump(31.0, 9.0) + 1.6 * bump(-34.0, 10.0)
             + 0.9 * bump(50.0, 12.0) + 0.7 * bump(-55.0, 12.0) + 0.5 * math.sin(theta_deg / 2.3) * bump(0.0, 60.0))
    base = RIDGE_ELEVATION - (4.6 * math.exp(-(13.0 / 6.0) ** 2) + 3.3 * math.exp(-(16.0 / 7.5) ** 2)
                              + 2.2 * math.exp(-(31.0 / 9.0) ** 2) + 1.6 * math.exp(-(34.0 / 10.0) ** 2))
    return base + peaks


def ridge_profile(spec):
    """(y, top) pairs of the range's crest at x = ridge_distance, as built."""
    ex, ey, ez = RANGE_EYE
    R = spec.ridge_distance
    ys = [-1200.0 + 8.0 * i for i in range(301)]
    out = []
    for y in ys:
        theta = math.degrees(math.atan2(y - ey, R - ex))
        top = ez + (R - ex) * math.tan(math.radians(range_elevation(theta)))
        out.append((y, max(0.5, top)))
    return out


def _build_outside(spec, m, col):
    """The ground to the horizon and a stand-in mountain range, each its own thing: the crest at
    ridge_distance with sloped faces on both sides, its heights from range_elevation. Rung 5 sets the
    real landscape."""
    W = spec.size[0]
    R = spec.ridge_distance
    far = R * 8.0
    bm = geo.new_bmesh()
    geo.add_quad(bm, (W, -far, -0.3), (far, -far, -0.3), (far, far, -0.3), (W, far, -0.3), 0)
    ground = geo.finish(bm, "Ground", [m["ground"]], col)
    ground[tags.TAG_PROP] = "ground"
    prof = ridge_profile(spec)
    depth = R * RANGE_DEPTH_SHARE

    def point(u, v):
        y, top = prof[min(len(prof) - 1, int(round(u * (len(prof) - 1))))]
        s = 2.0 * v - 1.0
        hat = (1.0 - s * s) ** 2
        return (R + s * depth, y, -0.3 + (top + 0.3) * hat)

    bm = geo.new_bmesh()
    geo.add_grid(bm, len(prof) - 1, 16, point, 0, smooth=True)
    rng = geo.finish(bm, "Range", [m["ridge"]], col)
    rng[tags.TAG_PROP] = "ridge"
    return [ground, rng]


def _build_standins(spec, m, col):
    """Stand-in furniture and trees (his review of 2026-11-08): a standing lamp by the window, a lamp on
    the table, an upright piano on the west wall and trees outside, so the mind's picture has depth to
    read beyond two surfaces. Rung 5 dresses the room and the outside for real. Each is tagged with
    the region it stands in, so the engine's rays count it toward that region."""
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    metal = mats.principled("StandinMetal", (0.07, 0.07, 0.08), roughness=0.35, metallic=0.8)
    shade = mats.principled("StandinShade", (0.92, 0.86, 0.70), roughness=0.9)
    wood = mats.principled("StandinWood", (0.09, 0.055, 0.035), roughness=0.3)
    bark = mats.principled("StandinBark", (0.13, 0.09, 0.06), roughness=0.95)
    leaf = mats.principled("StandinLeaf", (0.09, 0.20, 0.07), roughness=0.9)
    props = []
    # a standing lamp on the east wall, south of the window and clear of his arms at the sill
    bm = geo.new_bmesh()
    lx, ly = W - 0.28, wy0 - 0.28
    geo.add_segment(bm, (lx, ly, 0.0), (lx, ly, 0.025), 0.15, 0.15, 0, segments=32, caps=True)
    geo.add_segment(bm, (lx, ly, 0.02), (lx, ly, 1.55), 0.015, 0.015, 0, segments=12, caps=True)
    geo.add_segment(bm, (lx, ly, 1.45), (lx, ly, 1.78), 0.11, 0.19, 1, segments=32, caps=False)
    lamp = geo.finish(bm, "LampStand", [metal, shade], col)
    lamp[tags.TAG_PROP] = "wall_e"
    props.append(lamp)
    # a small lamp on the table, at its corner away from the bed
    (tx0, ty0, tz0), (tx1, ty1, tz1) = spec.table
    bm = geo.new_bmesh()
    px, py = tx1 - 0.09, ty0 + 0.10
    geo.add_segment(bm, (px, py, tz1), (px, py, tz1 + 0.02), 0.06, 0.06, 0, segments=24, caps=True)
    geo.add_segment(bm, (px, py, tz1 + 0.02), (px, py, tz1 + 0.30), 0.009, 0.009, 0, segments=12, caps=True)
    geo.add_segment(bm, (px, py, tz1 + 0.25), (px, py, tz1 + 0.42), 0.065, 0.105, 1, segments=24, caps=False)
    small = geo.finish(bm, "LampTable", [metal, shade], col)
    small[tags.TAG_PROP] = "table"
    small[tags.OF_PROP] = "Table"
    props.append(small)
    # an upright piano against the west wall, north of the bed
    (bx0, by0, bz0), (bx1, by1, bz1) = spec.bed
    bm = geo.new_bmesh()
    py0 = by1 + 0.30
    geo.add_box(bm, (0.02, py0, 0.0), (0.62, py0 + 1.45, 1.25), 0)
    geo.add_box(bm, (0.62, py0 + 0.08, 0.68), (0.92, py0 + 1.37, 0.76), 0)
    geo.add_box(bm, (0.62, py0 + 0.10, 0.76), (0.90, py0 + 1.35, 0.80), 1)
    for py_ in (py0 + 0.12, py0 + 1.25):
        geo.add_box(bm, (0.70, py_, 0.0), (0.76, py_ + 0.08, 0.68), 0)
    piano = geo.finish(bm, "Piano", [wood, shade], col)
    piano[tags.TAG_PROP] = "wall_w"
    props.append(piano)
    # outside (his review of 2026-11-08, second: eight trees hid the view): one big tree well to the
    # south of the window's view, a smaller one far to the north, both hidden from the bed by the
    # jambs, and low bushes on the ground under the eyes' horizon, so the open window, the sun and
    # the ridge stay clear in front of him; everything clear of the sun's line (y near 0.75)
    # each tree and each bush its own object: a thing the mind holds whole, with its shape (his sixth
    # review of 2026-11-09: the crowns drawn as saddles)
    ground = -0.3
    for k, (dx, y, trunk, crown) in enumerate(((9.0, -6.5, 3.4, 2.6), (14.0, 12.0, 3.0, 2.0)), 1):
        x = W + dx
        bm = geo.new_bmesh()
        geo.add_segment(bm, (x, y, ground), (x, y, ground + trunk + 0.3), 0.16, 0.11, 0, segments=12, caps=True)
        geo.add_sphere(bm, (x, y, ground + trunk + crown * 0.75), crown, 1, scale=(1.0, 1.0, 1.15), segments=16, rings=10)
        tree = geo.finish(bm, f"Tree_{k}", [bark, leaf], col)
        tree[tags.TAG_PROP] = "outside"
        props.append(tree)
    for k, (dx, y, r) in enumerate(((4.5, 3.2, 0.55), (7.5, -2.2, 0.7), (11.0, 5.0, 0.6), (16.0, -3.5, 0.8), (22.0, 1.5, 0.75),
                                    (30.0, 6.5, 0.9), (38.0, -5.0, 0.85)), 1):
        x = W + dx
        bm = geo.new_bmesh()
        geo.add_sphere(bm, (x, y, ground + r * 0.8), r, 0, scale=(1.0, 1.0, 0.8), segments=12, rings=8)
        bush = geo.finish(bm, f"Bush_{k}", [leaf], col)
        bush[tags.TAG_PROP] = "outside"
        props.append(bush)
    return props


def _build_portal(spec, col):
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    ld = bpy.data.lights.new("WindowPortal", "AREA")
    ld.shape = "RECTANGLE"
    ld.size = wy1 - wy0
    ld.size_y = wz1 - wz0
    ld.energy = 0.0
    try:
        ld.cycles.is_portal = True
    except Exception as e:
        print("room: portal not available:", e, flush=True)
    portal = bpy.data.objects.new("WindowPortal", ld)
    col.objects.link(portal)
    portal.location = (W + 0.05, (wy0 + wy1) / 2, (wz0 + wz1) / 2)
    portal.rotation_euler = (0.0, math.radians(90.0), 0.0)
    return portal


def _build_phone(spec, m, matrix, col, name="Phone"):
    L_, W_, T_ = spec.phone_size
    bm = geo.new_bmesh()
    screen = mats.screen("Screen", strength=spec.screen_strength)
    geo.add_box(bm, (-L_ / 2, -W_ / 2, -T_ / 2), (L_ / 2, W_ / 2, T_ / 2), 0, top_mat_index=1)
    phone = geo.finish(bm, name, [m["phone"], screen], col)
    phone.matrix_world = matrix
    phone[tags.TAG_PROP] = "phone"
    phone[tags.OF_PROP] = "Table"
    return phone, screen


def sun_direction(spec, elevation_deg):
    """Unit vector from the room toward the sun."""
    el = math.radians(elevation_deg)
    az = math.radians(spec.sun_azimuth_deg)
    return Vector((math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)))


def sun_elevation_at(spec, t):
    keys = spec.sun_keys
    if t <= keys[0][0]:
        return keys[0][1]
    for (t0, e0), (t1, e1) in zip(keys, keys[1:]):
        if t0 <= t < t1:
            return anim.lerp(e0, e1, (t - t0) / (t1 - t0))
    return keys[-1][1]


def build_room(scene, spec: RoomSpec, collection=None):
    """Rung 0's still: the room and the man sitting on the bed's east edge with the phone."""
    col = collection or scene.collection
    m = _room_materials()
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    shell = _build_shell(spec, m, col)
    _build_frame(spec, m, col)
    bed = _build_bed(spec, m, col)
    table = _build_table(spec, m, col)
    rug = _build_rug(spec, m, col)
    outside = _build_outside(spec, m, col)
    world = mats.sky_world("Dawn", spec.sun_elevation_deg, spec.sun_azimuth_deg, spec.sun_rotation_deg,
                           aerosol=spec.sky_aerosol, intensity=spec.sun_intensity)
    scene.world = world
    portal = _build_portal(spec, col) if spec.portal else None

    pose = figure.sitting(spec.seat_height)
    place = figure.placement(spec.man_location, spec.man_yaw_deg)
    man, head, points = figure.build("Man", pose, {"skin": m["skin"], "cloth": m["cloth"]}, place, col)
    pm = figure.phone_matrix(pose, place)
    phone, screen = _build_phone(spec, m, pm, col)

    (tloc, ttarget, tlens) = spec.third_camera
    cam_third = geo.add_camera("Cam_Third", tloc, ttarget, lens=tlens, clip_start=0.05, collection=col)
    eye = points["eye"]
    cam_first = geo.add_camera("Cam_First", eye, pm.translation, lens=spec.first_lens, clip_start=0.03,
                               collection=col)
    return {
        "scene": scene, "spec": spec,
        "shell": shell, "bed": bed, "table": table, "rug": rug, "outside": outside,
        "portal": portal, "world": world,
        "man": man, "head": head, "points": points, "pose": pose, "place": place,
        "phone": phone, "phone_matrix": pm,
        "cam_third": cam_third, "cam_first": cam_first,
        "head_world": points["head"],
        "window_centre": Vector((W, (wy0 + wy1) / 2, (wz0 + wz1) / 2)),
    }


def screen_strength_at(t, spec):
    """The phone's screen over the scene: lit by the alarm, by his use, by the chime, and at the end."""
    s = spec.screen_strength
    if 4.0 <= t < 10.5:
        return s
    if 38.3 <= t < 51.3:
        return s
    if 88.3 <= t < 91.5:
        return s
    if t >= 105.5:
        return s
    return 0.0


def build_room_animated(scene, spec: RoomSpec, motion, frames, fps, baker, collection=None, samples=None):
    """Rung 1's room: the animated man, the phone and the blanket baked, the dawn climbing.

    samples, when given, is {frame: (J, head_frame, body_R, phone_matrix)} from motion.sample,
    so the same numbers feed the room and the engine's checks.
    """
    col = collection or scene.collection
    m = _room_materials()
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    shell = _build_shell(spec, m, col)
    frame = _build_frame(spec, m, col)
    pane_frame, pane = _build_pane(spec, col) if spec.pane else (None, None)
    bed = _build_bed(spec, m, col, with_blanket=False)
    blanket = _build_blanket(spec, m, col)
    table = _build_table(spec, m, col)
    rug = _build_rug(spec, m, col)
    outside = _build_outside(spec, m, col)
    props = _build_standins(spec, m, col) if spec.standins else []
    world = mats.sky_world("Dawn", spec.sun_elevation_deg, spec.sun_azimuth_deg, spec.sun_rotation_deg,
                           aerosol=spec.sky_aerosol, intensity=spec.sun_intensity)
    scene.world = world
    sky = world.node_tree.nodes[world["sky_node"]]
    portal = _build_portal(spec, col) if spec.portal else None

    # A sun lamp for EEVEE proxies: Cycles takes its sun from the sky, EEVEE needs a lamp for shadows.
    ld = bpy.data.lights.new("ProxySun", "SUN")
    ld.energy = 4.0
    ld.angle = math.radians(1.0)
    ld.use_shadow = True
    sun = bpy.data.objects.new("ProxySun", ld)
    col.objects.link(sun)
    sun.location = (W + 2.0, (wy0 + wy1) / 2, 3.0)
    sun.rotation_mode = "QUATERNION"

    # The sky's own sun disc does not reach the camera in 5.2.3 Cycles (verified by looking straight
    # at it), so a stand-in disc a kilometre along the sun's line gives the First-Person view its glare
    # and the eye something to adapt to. It is visible to camera rays only and casts no light.
    sun_disc = None
    if spec.sun_disc_standin:
        bm = geo.new_bmesh()
        geo.add_disc(bm, (0, 0, 0), 1000.0 * math.tan(math.radians(0.533 / 2)), 0, segments=48)
        sun_disc = geo.finish(bm, "SunDiscStandin", [mats.emission("SunDiscStandin", (1.0, 0.96, 0.9), spec.sun_disc_strength)], col)
        for flag in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
            try:
                setattr(sun_disc, flag, False)
            except AttributeError:
                pass
        sun_disc.rotation_mode = "QUATERNION"
    fig = body.build_figure("Man", col, {"skin": m["skin"], "cloth": m["cloth"], "heart": m["heart"], "lung": m["lung"]}, segments=14)
    phone, screen = _build_phone(spec, m, Matrix.Identity(4), col)
    phone.rotation_mode = "QUATERNION"

    (ploc, ptarget, plens) = spec.proxy_camera
    cam_third = geo.add_camera("Cam_Third", ploc, ptarget, lens=plens, clip_start=0.05, collection=col)
    cam_first = geo.add_camera("Cam_First", (0, 0, 1.6), (1, 0, 1.6), lens=spec.first_lens, clip_start=0.03,
                               collection=col)
    cam_first.rotation_mode = "QUATERNION"

    body.bake_figure(baker, fig["empties"], frames, fps, motion=motion, samples=samples)
    em = next(n for n in screen.node_tree.nodes if n.bl_idname == "ShaderNodeEmission")
    strength_path = f'nodes["{em.name}"].inputs[{em.inputs.find("Strength")}].default_value'
    last_screen = None
    last_sun_sec = None
    for f in frames:
        t = anim.time_of(f, fps)
        if samples is not None:
            J, hf, body_R, pm = samples[f]
        else:
            J, hf, body_R, pm = motion.sample(t)
        baker.set_vec(phone, "location", f, pm.translation)
        baker.set_vec(phone, "rotation_quaternion", f, pm.to_quaternion())
        baker.set_vec(blanket, "location", f, motion.blanket_offset(t))
        # the First-Person camera on the eyes, looking where the head looks; its blinks, exposure
        # and edge tint are rung 2's (triview/eye.py). The axes come from cameras.CAM_FROM_HEAD:
        # rung 1's bake turned the camera to the head's left, which no render of it had shown.
        loc, q = cameras.first_camera(hf)
        baker.set_vec(cam_first, "location", f, loc)
        baker.set_vec(cam_first, "rotation_quaternion", f, q)
        s = screen_strength_at(t, spec)
        if s != last_screen:
            if last_screen is not None:
                baker.set(screen.node_tree, strength_path, 0, f - 1, last_screen, anim.CONSTANT)
            baker.set(screen.node_tree, strength_path, 0, f, s, anim.CONSTANT)
            last_screen = s
        sec = int(t)
        # (every frame: keyed once a second until 2026-11-16, the sun's height ran straight from second to second and
        # the turn in its path at first light was spread over the whole of that second: the limb the keys put over the
        # range at 40.2 s cleared it at 40.7 in the scene as rendered, after his lids had shut)
        if True:
            el = sun_elevation_at(spec, t)
            baker.set(world.node_tree, f'nodes["{sky.name}"].sun_elevation', 0, f, math.radians(el))
            d = sun_direction(spec, el)
            sq = (-d).to_track_quat("-Z", "Y")
            baker.set_vec(sun, "rotation_quaternion", f, sq)
            if sun_disc is not None:
                centre = Vector((W / 2, D / 2, 1.5))
                baker.set_vec(sun_disc, "location", f, centre + d * 1000.0)
                baker.set_vec(sun_disc, "rotation_quaternion", f, (-d).to_track_quat("Z", "Y"))
            last_sun_sec = sec

    return {
        "scene": scene, "spec": spec,
        "shell": shell, "frame": frame, "pane_frame": pane_frame, "pane": pane, "bed": bed, "blanket": blanket, "table": table, "rug": rug,
        "outside": outside, "props": props, "portal": portal, "world": world, "sky": sky, "sun": sun, "sun_disc": sun_disc,
        "figure": fig, "phone": phone, "screen": screen,
        "cam_third": cam_third, "cam_first": cam_first,
        "window_centre": Vector((W, (wy0 + wy1) / 2, (wz0 + wz1) / 2)),
    }

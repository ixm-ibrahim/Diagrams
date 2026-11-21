"""The man's hair (rung 3): scalp hair, a beard or stubble, and brows, grown strand by strand on his own skin.

Every hair is its own curve standing on the smoothed surface of his head, and Cycles lights it with the hair shader.
Nothing here is a picture of hair. Where hair grows is told by rule in the head's own frame (the head's middle as
triview/man.py places it; forward, left, up), so the rules hold for any face the generator makes:

  the scalp   above a hairline given as an angle of elevation for every bearing round the head, with sideburns
  the beard   the lower face under a cheek line, the upper lip, and the neck down to a neckline; lips left out
  brows       two arcs over the eyes

Two cuts of the scalp:
  crop    a short crop, the same few millimetres all over (the first man, 2026-11-19)
  quiff   long on top, swept up at the front and back over the head, with the sides and the back faded short
Three growths of the lower face:
  stubble a day or two
  short   a short full beard with a moustache, trimmed to a neckline (the second man, 2026-11-19)
  boxed   a barbered beard: a straight cheek line from the sideburn to the corner of the mouth, a neckline that follows
          the jaw, short at the sides and longer on the chin, a moustache trimmed along the lip and narrowing to the
          corners of the mouth, and sideburns that join the hair to it (the third man, 2026-11-19)

Long hair cannot stand straight off the skin as a crop does: it has to lie over the skull. An ellipsoid is fitted to
his scalp, and every long hair is carried along it in the direction it is combed, at a height above it that rises
behind the root and settles toward the tip. Hairs gather into locks: each is drawn toward the nearest of a few hundred
lead hairs, more toward its tip.

Lengths are metres. The curves ride the head bone, so they follow the head and nothing else (rung 4 decides whether
his hair moves on its own). Stand-in or staying: the method stays; each cut and its numbers are a pick he may change.
"""
import math

import bpy
import numpy as np
from mathutils import Vector

# the hairline: (bearing from straight ahead in degrees, elevation in degrees above the head's middle)
HAIRLINE = ((0, 43), (25, 43), (45, 41), (58, 36), (66, 26), (74, 14), (84, 9), (96, 8), (108, 2), (120, -14), (140, -30), (160, -37), (180, -40))
HAIR = {
    "style": "crop",
    "beard": "stubble",
    "scalp": {"count": 130000, "top": 0.011, "side": 0.006, "radius": 0.000042, "seed": 11},
    "stubble": {"count": 9000, "length": 0.0013, "radius": 0.000045, "seed": 23},
    "brows": {"count": 900, "length": 0.008, "radius": 0.00004, "seed": 31, "width": 1.0},
    "melanin": 1.0, "redness": 0.15,
    # the quiff: the top long, the sides and back faded
    "top": {"count": 60000, "front": 0.066, "crown": 0.044, "points": 11, "radius": 0.00004, "seed": 11,
            "lift_front": 0.034, "lift_crown": 0.004, "sweep_deg": 20.0,      # how high it stands, and its turn toward his left
            "per_lock": 55, "lock": 0.72, "lock_turn": 0.16,                  # hairs to a lock, how tight, how much each lock goes its own way
            "wave": 0.0014, "frizz": 0.0009, "fly": 0.025},
    "sides": {"count": 125000, "low": 0.0022, "high": 0.022, "radius": 0.00004, "seed": 12,
              # the back's lengths from the nape up to the top's edge, metres
              # (the heights these lengths are set at, metres from the head's middle, the last being the ridge)
              "back": (0.010, 0.012, 0.014, 0.022, 0.028), "back_at": (-0.085, -0.050, 0.0, 0.035),
              # how flat the back's hair lies on his head (0 standing straight off it, 1 lying along it). At 0.45 to 0.68,
              # as the sides have it, the back's hair stood 25 to 50 degrees off his head from its first row under the top:
              # a second, rounded layer starting where the top's hair ends and pointing another way (his second ring of
              # 2026-11-20). Lying down, it carries on the top's own fall.
              "back_lie": 0.88,
              # how far under the ear lobe's bottom the hairline crosses the middle of the back of his neck. His skull
              # ends and his neck begins 50 mm under the head's middle; the first tables ended his hair right there (46 to
              # 50 mm), so none grew on his neck. A man's hair runs on down the neck a few centimetres (his first ring).
              "nape_drop": 0.048,
              # the taper at the nape and behind the ears, where the hair ends on bare skin (from 100 degrees round from
              # straight ahead, so behind the ear and not above it; full by 110). A low taper as barbers cut it under a
              # quiff: the hair keeps its length down the back of the head and only its last three centimetres go
              # down to the skin. No hair is longer than cut[0] + cut[1] * h + cut[2] * h * h, h being its root's
              # height above the hairline along the head in metres (0.5 mm at the line, 2.7 at 10 mm, 5.3 at 20, 8.3 at
              # 30, where it meets the lengths the back has anyway); the growth thins out over the last `thin` metres;
              # near the line the hair lies close to the skin.
              # History, 2026-11-20. Round one: 4 mm hair at full thickness to the line, standing 50 degrees off the
              # head, on a hairline that ran in a straight slant from above the ear to the nape: he read its edge as
              # belonging to the hair above, not to the skin. Round two: a skin fade that halved the lower hair's
              # length on the same slanted line: a cap over shaved skin with a wisp on the neck ("just looks weird").
              # The slanted line was the fault both times: a man's hair comes down close behind his ear to the lobe's
              # level and then runs back to the nape (the table grow() builds from his own ear, `behind_ear`).
              "nape": {"from": 100.0, "over": 10.0, "thin": 0.010, "cut": (0.0008, 0.30, 2.5), "lie": 0.88, "lie_over": 0.035}},
    "ridge": (0.062, 0.082),              # metres above the head's middle: where the sides turn into the top
    # the short full beard
    "short": {"count": 70000, "chin": 0.011, "jaw": 0.009, "cheek": 0.006, "lip": 0.008, "lip_thick": 1.2, "neck": 0.004, "radius": 0.00006,
              "points": 5, "seed": 23, "wave": 0.0006, "frizz": 0.00045, "melanin": None, "redness": None},
    # the barbered beard
    "boxed": {"count": 80000, "chin": 0.010, "jaw": 0.0075, "side": 0.0045, "lip": 0.009, "lip_thick": 1.2, "neck": 0.003,
              "radius": 0.000055, "points": 5, "seed": 23, "wave": 0.0004, "frizz": 0.0003, "melanin": None, "redness": None,
              "edge": 0.0025,          # metres over which a trimmed line goes from full growth to none
              "sag": 0.0035,           # how far the cheek line dips under a straight one
              "burn_low": 0.016,       # the sideburn hands over to the beard this far above the ear lobe's bottom
              # the front edge of the hair before the ear, from the sideburn's foot up over the temple, as shares of the
              # distance from the ear's front to the eyeball's middle (about 64 mm on him): at the foot, at the ear's
              # middle, at the eyes' level, at the temple's peak (15 mm above the eyes), 30 mm and 42 mm above the eyes.
              # On real men the temple's hair comes forward to a peak 2 to 3 cm behind the brow's outer end and the
              # sideburn hangs from it; the first shape was a strip beside the ear, some 55 mm behind the brow.
              # Under the peak the edge comes back to a shallow hollow at the eyes' level and from there leans FORWARD
              # as it goes down, as the ear's own front does, widening into the beard's cheek line. The second shape
              # (0.22, 0.28, 0.40, ...) leaned back toward the ear all the way down, 25 degrees off upright, and
              # ended as a strip 14 mm wide against the ear with the beard's cheek line starting from there.
              "temple": (0.53, 0.47, 0.43, 0.56, 0.53, 0.47),
              "burn_short": 0.006,     # the sideburn's shortest hair
              "burn_long": 0.008,      # the sideburn's longest hair
              "corner": 0.014},        # the radius of the beard's rear lower corner
}


def _frame(rig):
    from . import man
    c = np.array(man.head_centre(rig))
    return c, np.array((0.0, -1.0, 0.0)), np.array((1.0, 0.0, 0.0)), np.array((0.0, 0.0, 1.0))


def _surface(body, levels=2):
    """His body's surface as rendered (helpers masked off, smoothed): triangles' corners, normals, areas, and each
    triangle's material slot name. In the world, in the rest pose."""
    sub = next((m for m in body.modifiers if m.type == "SUBSURF"), None)
    keep = sub.levels if sub else None
    if sub:
        sub.levels = levels
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    nv, nt = len(me.vertices), len(me.loop_triangles)
    co = np.empty(nv * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    co = co.reshape(nv, 3).astype(np.float64)
    M = np.array(body.matrix_world)
    co = co @ M[:3, :3].T + M[:3, 3]
    tri = np.empty(nt * 3, dtype=np.int32)
    me.loop_triangles.foreach_get("vertices", tri)
    tri = tri.reshape(nt, 3)
    mi = np.empty(nt, dtype=np.int32)
    me.loop_triangles.foreach_get("material_index", mi)
    names = [s.material.name if s.material else "" for s in body.material_slots]
    a, b, c = co[tri[:, 0]], co[tri[:, 1]], co[tri[:, 2]]
    n = np.cross(b - a, c - a)
    area = 0.5 * np.linalg.norm(n, axis=1)
    n = n / np.maximum(2.0 * area[:, None], 1e-12)
    ev.to_mesh_clear()
    if sub:
        sub.levels = keep
    return a, b, c, n, area, mi, names


def _hairline(az_deg, table=None):
    table = table or HAIRLINE
    xs = np.array([p[0] for p in table], dtype=np.float64)
    ys = np.array([p[1] for p in table], dtype=np.float64)
    return np.interp(az_deg, xs, ys)


def _above_hairline(points, centre, fwd, left, up, table=None):
    """For points on his head: how far above the hairline each stands, in metres along the head (negative under it),
    and its bearing round from straight ahead in degrees. The line is the one _fields grows the scalp above."""
    rel = points - centre
    x, y, z = rel @ fwd, rel @ left, rel @ up
    az = np.degrees(np.arctan2(np.abs(y), x))
    el = np.degrees(np.arctan2(z, np.hypot(x, y)))
    line = _hairline(az, table) + 1.5 * np.sin(az * 0.37) * np.sin(az * 0.11 + 1.0)
    return np.radians(el - line) * np.linalg.norm(rel, axis=1), az


def _behind_ear(table, face, nape=None):
    """The hairline's table with its stretch behind the ear set from his own ear. A man's hair comes down close behind
    the ear, about a centimetre from the ear's rear edge, to the level of the lobe, and from there runs back and a
    little down to the nape. The table as first written ran in one straight slant from above the ear to the nape and
    left a wedge of bare skin behind the ear, up to 5 cm wide at the lobe's level (measured on the third man)."""
    b0 = math.degrees(math.atan2(face["ear_side"], face["ear_rear"]))        # the bearing of the ear's rear edge
    lobe = math.degrees(math.atan2(face["ear_bottom"], face["ear_side"] * 0.95))   # the elevation of the lobe's bottom on the skin behind it
    nape = float(_hairline(180.0, table)) if nape is None else nape           # the elevation at which the line crosses the neck's middle
    kept = [p for p in table if p[0] <= b0 + 1.0]
    new = [(b0 + 6.0, float(_hairline(b0 + 1.0, table)) - 2.0), (b0 + 10.0, 0.35 * lobe), (b0 + 14.0, 0.80 * lobe), (b0 + 20.0, lobe),
           # from the lobe's level the line drops steeply to the nape's level, so that from behind the hair's lower edge runs
           # nearly the neck's whole width (dropping slowly over 35 degrees it made a narrow tongue down the neck's middle)
           (b0 + 27.0, lobe + 0.60 * (nape - lobe)), (b0 + 36.0, lobe + 0.92 * (nape - lobe)), (b0 + 46.0, nape), (180.0, nape)]
    out = tuple(kept) + tuple((round(a, 1), round(e, 1)) for a, e in new if a < 180.0 or a == 180.0)
    print(f"HAIR hairline behind the ear: the ear's rear edge at {b0:.0f} degrees round, the lobe's bottom at {lobe:.0f} degrees of elevation; "
          f"the table from there: {out[len(kept):]}", flush=True)
    return out


def _sample(a, b, c, n, weight, count, rng):
    """count points on the triangles, each triangle taken in proportion to its weight (area times how much grows there)."""
    w = weight / weight.sum()
    idx = rng.choice(len(w), size=count, p=w)
    u, v = rng.random(count), rng.random(count)
    flip = u + v > 1.0
    u[flip], v[flip] = 1.0 - u[flip], 1.0 - v[flip]
    p = a[idx] + (b[idx] - a[idx]) * u[:, None] + (c[idx] - a[idx]) * v[:, None]
    return p, n[idx], idx


def _unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-12)


def _strands(roots, dirs, bend, lengths, points=4, rng=None, wave=0.0, frizz=0.0):
    """Every hair's points, from its root along its direction, bending toward `bend` along its length; with `wave` a
    slow sideways swing of that many metres and with `frizz` a point-to-point unevenness, both growing toward the tip."""
    count = len(roots)
    pos = np.empty((count, points, 3), dtype=np.float64)
    d = _unit(dirs)
    p = roots - d * 0.0004                     # the root a little under the skin, so no hair floats
    pos[:, 0] = p
    step = (lengths + 0.0004)[:, None] / (points - 1)
    for k in range(1, points):
        dk = _unit(d + bend * (0.45 * k / (points - 1)))
        p = p + dk * step
        pos[:, k] = p
    if rng is not None and (wave or frizz):
        s = np.linspace(0.0, 1.0, points)[None, :, None]
        side = _unit(np.cross(d, rng.normal(0.0, 1.0, (count, 3))))
        if wave:
            phase, freq = rng.uniform(0.0, 2.0 * math.pi, (count, 1, 1)), rng.uniform(0.8, 1.7, (count, 1, 1))
            pos += side[:, None, :] * (wave * np.sin(2.0 * math.pi * freq * s + phase) * s)
        if frizz:
            pos += rng.normal(0.0, frizz, pos.shape) * s
    return pos


def _object(name, pos, radius, rig, material, tip=0.35):
    """A hair object from every hair's points (count, points, 3), riding the head bone."""
    count, points = pos.shape[0], pos.shape[1]
    data = bpy.data.hair_curves.new(name)
    data.add_curves([points] * count)
    data.points.foreach_set("position", np.ascontiguousarray(pos, dtype=np.float32).reshape(-1))
    rad = np.empty((count, points), dtype=np.float32)
    rad[:] = radius * np.linspace(1.0, tip, points, dtype=np.float32)[None, :]
    if "radius" not in data.attributes:
        data.attributes.new("radius", "FLOAT", "POINT")
    data.attributes["radius"].data.foreach_set("value", rad.reshape(-1))
    data.materials.append(material)
    ob = bpy.data.objects.new(name, data)
    bpy.context.scene.collection.objects.link(ob)
    # ride the head bone: keep the world place while the bone's own frame takes the object
    ob.parent, ob.parent_type, ob.parent_bone = rig, "BONE", "head"
    bone = rig.data.bones["head"]
    ob.matrix_parent_inverse = (rig.matrix_world @ bone.matrix_local @ _tail_shift(bone)).inverted()
    ob["tv_man"] = rig.get("tv_man", "Man3")
    return ob


def _carry_with_head(body, rig, centre, fwd, left, up, table, zone):
    """Where hair grows on the back of his neck, let the head's bone carry his skin whole, easing back to the skin's own
    weights over 35 mm under the hairline. His hair rides the head's bone as one stiff piece; the skin of his upper neck
    was shared between the head's bone and the neck's (a quarter to a half the head's), so when his head turned or
    tipped, the hair there left the skin and hung behind his neck as a tail (seen at the window, 2026-11-20). Hairs
    gathered into groups by the skin's shares and held as the skin is were tried first: each group moved by its own
    amount and the hair broke into steps. The neck's bend now sits a little lower under the hair. A stand-in until
    rung 4 gives him hair that moves with his skin."""
    vp = _base_points(body)
    above, az = _above_hairline(vp, centre, fwd, left, up, table)
    rel = vp - centre
    near_head = (np.linalg.norm(rel, axis=1) < 0.19) & (rel @ up > -0.16)
    f = np.clip((az - (zone["from"] - 8.0)) / 12.0, 0.0, 1.0) * np.clip(1.0 + above / 0.035, 0.0, 1.0) * near_head
    bones = {g.index: g.name for g in body.vertex_groups if g.name in rig.data.bones}
    head_group = body.vertex_groups["head"]
    changed = 0
    for i in np.nonzero(f > 0.01)[0]:
        v = body.data.vertices[int(i)]
        w = {g.group: g.weight for g in v.groups if g.group in bones}
        total = sum(w.values())
        if total <= 0.0:
            continue
        k = float(f[i])
        others = 0.0
        for gi, weight in w.items():
            if bones[gi] != "head":
                new = weight / total * (1.0 - k)
                body.vertex_groups[gi].add([int(i)], new, "REPLACE")
                others += new
        head_group.add([int(i)], 1.0 - others, "REPLACE")
        changed += 1
    return changed


def _curves(name, roots, dirs, bend, lengths, radius, rig, material, points=4):
    """A hair object: every hair from its root along its direction, bending toward `bend` along its length."""
    return _object(name, _strands(roots, dirs, bend, lengths, points), radius, rig, material)


def _tail_shift(bone):
    from mathutils import Matrix
    return Matrix.Translation((0.0, bone.length, 0.0))      # a bone's children hang from its tail


def hair_material(name="ManHair", melanin=0.95, redness=0.22, roughness=0.32):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    h = nt.nodes.new("ShaderNodeBsdfHairPrincipled")
    h.model = "CHIANG"
    h.parametrization = "MELANIN"
    h.inputs["Melanin"].default_value = melanin
    h.inputs["Melanin Redness"].default_value = redness
    h.inputs["Roughness"].default_value = roughness
    h.inputs["Radial Roughness"].default_value = 0.4
    h.inputs["Random Color"].default_value = 0.15
    h.inputs["Random Roughness"].default_value = 0.2
    nt.links.new(h.outputs["BSDF"], out.inputs["Surface"])
    return mat


def _base_points(body):
    """Every vertex of his base mesh where the generator's shape keys put it, modifiers left out, in the world."""
    shown = [(m, m.show_viewport) for m in body.modifiers]
    for m, _ in shown:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    co = np.empty(len(me.vertices) * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    ev.to_mesh_clear()
    for m, was in shown:
        m.show_viewport = was
    dg.update()
    M = np.array(body.matrix_world)
    return co.reshape(-1, 3).astype(np.float64) @ M[:3, :3].T + M[:3, 3]


def _styled(x, y, z, face, B):
    """The barbered beard's lines, for points given in the head's frame (forward, left, up). Seen from his side the
    cheek line runs straight, with a slight dip, from the sideburn's foot before the ear to the corner of the mouth;
    the neckline runs from under the jaw's angle to a finger under the chin; nothing grows behind the ear's front.
    The moustache fills the upper lip under the nose and narrows to nothing just past the corners of the mouth. The
    sideburn is a strip before the ear from the beard's top up into the hair. Returns arrays by name."""
    m, ay, e = face["mouth_z"], np.abs(y), B["edge"]
    ef = face["ear_front"]
    depth = face["eye_x"] - ef                                  # from the ear's front to the eyeball's middle
    xb, xm = ef + B["temple"][0] * depth, face["mouth_x"] - 0.018      # the cheek line begins at the sideburn's front edge
    t = np.clip((x - xb) / (xm - xb), 0.0, 1.0)               # 0 before the ear, 1 at the corner of the mouth
    zb = face["ear_bottom"] + B["burn_low"]
    cheek_z = zb + (m + 0.003 - zb) * t - B["sag"] * np.sin(np.pi * t)
    under = np.clip((cheek_z - z) / e, 0.0, 1.0)
    xg, xf = ef + 0.012, face["chin_x"] - 0.030
    s = np.clip((x - xg) / (xf - xg), 0.0, 1.0)               # 0 under the jaw's angle, 1 under the chin
    zg, zc = face["chin_z"] + 0.018, face["chin_z"] - 0.010
    floor_z = zg + (zc - zg) * s
    over = np.clip((z - floor_z) / e, 0.0, 1.0)
    # nothing behind the ear's front beside the ear; under the lobe the beard runs back to the jaw's rear edge
    back = ef - 0.001 - 0.014 * np.clip((face["ear_bottom"] + 0.004 - z) / 0.008, 0.0, 1.0)
    fore = np.clip((x - back) / e, 0.0, 1.0)
    # the corner where the rear edge meets the neckline, at the jaw's angle, is rounded and not square
    r = B["corner"]
    dx, dz = x - back, z - floor_z
    in_corner = (dx < r) & (dz < r)
    over = np.where(in_corner, np.minimum(over, np.clip((r - np.hypot(r - dx, r - dz)) / e, 0.0, 1.0)), over)
    half = face["mouth_half"] + 0.012
    top = face["lip_top"] + 0.0125 + (m + 0.002 - face["lip_top"] - 0.0125) * np.clip((ay - 0.010) / (half - 0.010), 0.0, 1.0)
    lip = (np.clip((top - z) / (0.8 * e), 0.0, 1.0) * (z > m - 0.001) * np.clip((half - ay) / e, 0.0, 1.0)
           * (x > face["mouth_x"] - 0.035))
    # the sideburn: from where the ear joins the face to a finger's width before the ear's front, its front edge the
    # hairline's own line carried down, its top lost in the hair above the ear
    ez = face["eye_z"]
    knots = (zb, 0.5 * (face["ear_top"] + face["ear_bottom"]), ez, ez + 0.015, ez + 0.030, ez + 0.042)
    front = ef + depth * np.interp(z, knots, B["temple"])
    burn = (np.clip((x - (ef - 0.010)) / e, 0.0, 1.0) * np.clip((front - x) / (1.6 * e), 0.0, 1.0)
            * np.clip((z - (zb - 0.005)) / e, 0.0, 1.0) * np.clip((knots[-1] + 0.006 - z) / 0.012, 0.0, 1.0))
    # the beard's own hair runs up the sideburn, full at the beard and thinning to a third at the ear's top, no higher
    up_strip = (burn * np.clip((face["ear_top"] - z) / max(face["ear_top"] - zb, 1e-6), 0.33, 1.0)
                * np.clip((face["ear_top"] + 0.004 - z) / 0.008, 0.0, 1.0))
    # the scalp's own darker, denser hair thins out gradually down the sideburn, from full at about the ear's middle to
    # none just under the beard's top, while the beard's hair runs up through it: no line where one hands over
    burn_scalp = burn * np.clip((z - (zb - 0.005)) / 0.022, 0.0, 1.0)
    return {"beard": np.maximum(np.maximum(under * over * fore, lip), up_strip), "lip": lip, "t": t, "cheek_z": cheek_z,
            "floor_z": floor_z, "burn": burn, "burn_scalp": burn_scalp, "zb": zb}


def _fields(points, centre, fwd, left, up, face=None, boxed=None, hairline=None):
    """For points on his head: how much scalp hair grows there (0 to 1), how much beard (0 to 1), and the points'
    coordinates in the head's frame (forward, left, up). Without `face` the beard is the stubble's region as first
    drawn; with `face` (the measures of his mouth and chin, _face) it is the full beard's: under a cheek line, on the
    upper lip, and down to a neckline; with `boxed` (the barbered beard's numbers) it is that beard's, and the
    sideburn's strip is added to the scalp."""
    rel = points - centre
    x, y, z = rel @ fwd, rel @ left, rel @ up
    az = np.degrees(np.arctan2(np.abs(y), x))                 # 0 straight ahead, 180 straight behind
    el = np.degrees(np.arctan2(z, np.hypot(x, y)))
    dist = np.linalg.norm(rel, axis=1)
    head = (dist < 0.19) & (z > -0.16)
    line = _hairline(az, hairline) + 1.5 * np.sin(az * 0.37) * np.sin(az * 0.11 + 1.0)       # the line wanders a little
    scalp = np.clip((el - line) / 4.0, 0.0, 1.0)             # thin over the first degrees above the line
    burn = (az > 74) & (az < 90) & (z > -0.035) & (z < 0.03) & (x > 0.0)             # sideburns before each ear
    if boxed is not None:
        st = _styled(x, y, z, face, boxed)
        scalp = np.maximum(scalp, st["burn_scalp"]) * head
        return scalp, st["beard"] * (dist < 0.2), x, y, z
    scalp = np.where(burn, np.maximum(scalp, 0.8), scalp) * head
    if face is None:
        top = np.interp(az, [0, 18, 30, 55, 74, 86], [-0.047, -0.050, -0.036, -0.030, -0.012, 0.012])    # the beard's upper edge
        beard = np.clip((top - z) / 0.008, 0.0, 1.0) * np.clip((z + 0.150) / 0.02, 0.0, 1.0) * (az < 86) * (dist < 0.2)
        return scalp, beard, x, y, z
    m = face["mouth_z"]
    # the cheek line: level with the mouth beside it, rising to the sideburn before the ear
    top = np.interp(az, [0, 24, 38, 55, 74, 86], [m, m + 0.007, m + 0.020, m + 0.029, m + 0.045, m + 0.066])
    under = np.clip((top - z) / 0.007, 0.0, 1.0)
    # the upper lip: from the mouth's line up to under the nose, a little wider than the mouth
    lip = (np.clip((face["lip_top"] + 0.0135 - z) / 0.004, 0.0, 1.0) * (z > m - 0.001) * (np.abs(y) < face["mouth_half"] + 0.011)
           * (x > face["mouth_x"] - 0.03))
    # the neckline: a finger under the chin in front, rising under the jaw toward the ear
    c = face["chin_z"]
    floor = np.interp(az, [0, 40, 62, 76, 86], [c - 0.020, c - 0.014, c + 0.010, c + 0.028, c + 0.045])
    over = np.clip((z - floor) / 0.009, 0.0, 1.0)
    beard = np.maximum(under * over, lip) * (az < 86) * (dist < 0.2)
    return scalp, beard, x, y, z


def _face(mid, mi, names, centre, fwd, left, up):
    """The measures of his mouth and chin in the head's frame, read off his own surface: the lips are their own
    material, the chin is the lowest skin at the front of his face."""
    rel = mid - centre
    x, y, z = rel @ fwd, rel @ left, rel @ up
    lips = np.isin(mi, [i for i, s in enumerate(names) if s == "ManLips"])
    if lips.sum() < 4:
        raise RuntimeError("his lips' material was not found: the beard cannot be placed")
    lips &= x > x[lips].max() - 0.012                           # the lips as seen from in front, not the mouth's inside
    face = {"lip_top": float(z[lips].max()), "lip_bottom": float(z[lips].min()), "mouth_half": float(np.abs(y[lips]).max()),
            "mouth_x": float(x[lips].max())}
    face["mouth_z"] = 0.5 * (face["lip_top"] + face["lip_bottom"])
    # the chin: its foremost point lies under the lower lip; its underside is about 18 mm below that point
    below = ~lips & (np.abs(y) < 0.015) & (z < face["lip_bottom"] - 0.012) & (z > face["lip_bottom"] - 0.06) & (x > face["mouth_x"] - 0.05)
    face["chin_z"] = float(z[below][np.argmax(x[below])]) - 0.018
    face["chin_x"] = float(x[below].max())
    ears = np.isin(mi, [i for i, s in enumerate(names) if s == "ManEars"])
    if ears.sum() >= 4:
        face.update(ear_front=float(x[ears].max()), ear_top=float(z[ears].max()), ear_bottom=float(z[ears].min()),
                    ear_rear=float(x[ears].min()), ear_side=float(np.abs(y[ears]).min()))
    return face


# ---- long hair over the skull ----

def _fit_ellipsoid(q):
    """An ellipsoid with its axes along the head's own (forward, left, up) through points on his scalp: its middle and
    its three half-widths. Least squares on A x2 + B y2 + C z2 + D x + E y + F z = 1."""
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    M = np.stack([x * x, y * y, z * z, x, y, z], axis=1)
    sol = np.linalg.lstsq(M, np.ones(len(q)), rcond=None)[0]
    A, B, C, D, E, F = sol
    if min(A, B, C) <= 0.0:
        c = q.mean(axis=0)
        r = np.full(3, np.linalg.norm(q - c, axis=1).mean())
        return c, r
    c = np.array([-D / (2 * A), -E / (2 * B), -F / (2 * C)])
    K = 1.0 + A * c[0] ** 2 + B * c[1] ** 2 + C * c[2] ** 2
    return c, np.sqrt(K / np.array([A, B, C]))


def _scalp_map(ell, tris_local):
    """His own scalp's distance from the ellipsoid's middle, by direction: rays cast from the middle through his head's
    surface on a grid of bearings and elevations. Where a ray meets nothing, the ellipsoid's own distance."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    c, r = ell[0], ell[1]
    a, b, d = tris_local
    n = len(a)
    tree = BVHTree.FromPolygons([Vector(v) for v in np.concatenate([a, b, d])], [(i, n + i, 2 * n + i) for i in range(n)])
    az = np.linspace(-math.pi, math.pi, 181)
    el = np.linspace(-0.7, 0.5 * math.pi, 73)
    R = np.empty((len(el), len(az)))
    origin = Vector(c)
    for i, e in enumerate(el):
        for j, t in enumerate(az):
            v = np.array((math.cos(e) * math.cos(t), math.cos(e) * math.sin(t), math.sin(e)))
            hit = tree.ray_cast(origin, Vector(v), 0.4)
            R[i, j] = hit[3] if hit[0] is not None else 1.0 / math.sqrt(float(np.sum((v / r) ** 2)))
    return az, el, R


def _surface_distance(rel, ell):
    """The distance from the ellipsoid's middle to the surface hair lies on, in each point's direction: his own scalp
    where it has been read (_scalp_map), the ellipsoid otherwise."""
    c, r = ell[0], ell[1]
    dist = np.linalg.norm(rel, axis=-1)
    if len(ell) < 3 or ell[2] is None:
        rho = np.sqrt(np.sum((rel / r) ** 2, axis=-1))
        return dist / np.maximum(rho, 1e-9), dist
    az, el, R = ell[2]
    t = np.arctan2(rel[..., 1], rel[..., 0])
    e = np.arcsin(np.clip(rel[..., 2] / np.maximum(dist, 1e-9), -1.0, 1.0))
    fj = np.clip((t - az[0]) / (az[1] - az[0]), 0.0, len(az) - 1.001)
    fi = np.clip((e - el[0]) / (el[1] - el[0]), 0.0, len(el) - 1.001)
    j0, i0 = fj.astype(int), fi.astype(int)
    wj, wi = fj - j0, fi - i0
    surf = (R[i0, j0] * (1 - wi) * (1 - wj) + R[i0, j0 + 1] * (1 - wi) * wj + R[i0 + 1, j0] * wi * (1 - wj) + R[i0 + 1, j0 + 1] * wi * wj)
    return surf, dist


def _height(q, ell):
    """How far a point stands above the surface hair lies on, along the line from the ellipsoid's middle."""
    surf, dist = _surface_distance(q - ell[0], ell)
    return dist - surf


def _at_height(q, ell, h):
    """The point moved along that line to stand h above the surface hair lies on."""
    rel = q - ell[0]
    surf, dist = _surface_distance(rel, ell)
    return ell[0] + rel * ((surf + h) / np.maximum(dist, 1e-9))[..., None]


def _nearest(q, leads, chunk=4000):
    """For every point, the index of the nearest lead."""
    out = np.empty(len(q), dtype=np.int64)
    for i in range(0, len(q), chunk):
        d = np.linalg.norm(q[i:i + chunk, None, :] - leads[None, :, :], axis=2)
        out[i:i + chunk] = np.argmin(d, axis=1)
    return out


def _swept(q, T, ell, rng):
    """The top's long hairs in the head's frame (forward, left, up): from roots q, combed back over the head with a
    turn toward his left, standing up behind the front hairline, gathered into locks. Returns (count, points, 3)."""
    N, n = len(q), T["points"]
    x, y = q[:, 0], q[:, 1]
    fr = np.clip((x + 0.03) / 0.11, 0.0, 1.0)                 # 1 at the front hairline, 0 behind the crown
    edge = np.clip(np.abs(y) / 0.07, 0.0, 1.0)                # 1 at the top's left and right edges
    # the locks: every hair belongs to the nearest lead hair and shares its lock's turn, height and length
    G = max(N // T["per_lock"], 1)
    lead = rng.choice(N, G, replace=False)
    own = _nearest(q, q[lead])
    turn = rng.normal(0.0, T["lock_turn"], (G, 3))[own]
    tall = rng.uniform(0.75, 1.28, G)[own]
    long = rng.uniform(0.84, 1.08, G)[own]
    # the comb: back, turned toward his left; hair behind the crown falls down the back, hair at the edges falls outward
    W = np.zeros((N, 3))
    W[:, 0] = -1.0
    W[:, 1] = math.tan(math.radians(T["sweep_deg"])) + np.sign(y) * 0.30 * edge * (1.0 - fr)
    W[:, 2] = -0.65 * (1.0 - fr) ** 2 - 0.18 * edge * (1.0 - fr)
    W = _unit(W + turn + rng.normal(0.0, 0.04, (N, 3)))
    # toward the top's left and right edges the hair is cut shorter and kept lower, so the top meets the faded sides
    # behind the crown the lengths are more uneven, so the top ends in a soft edge over the faded back and not in a shelf
    uneven = rng.uniform(0.9, 1.05, N) - rng.uniform(0.0, 0.38, N) * (1.0 - np.clip(fr / 0.45, 0.0, 1.0))
    L = (T["crown"] + (T["front"] - T["crown"]) * fr) * long * uneven * (1.0 - 0.28 * edge)
    peak = (T["lift_crown"] + (T["lift_front"] - T["lift_crown"]) * fr ** 1.2) * tall * (1.0 - 0.5 * edge)
    tip = peak * (0.5 + 0.12 * fr)
    h0 = _height(q, ell)
    c, r = ell[0], ell[1]
    pos = np.empty((N, n, 3))
    p = q.copy()
    pos[:, 0] = p
    step = (L * 0.86 / (n - 1))[:, None]
    for k in range(1, n):
        s = k / (n - 1)
        nrm = _unit((p - c) / (r * r))                        # the ellipsoid's own outward direction here
        w = _unit(W - nrm * np.sum(W * nrm, axis=1)[:, None])
        p = p + w * step
        rise = math.sin(0.5 * math.pi * min(s / 0.34, 1.0))
        fall = 0.0 if s <= 0.34 else ((s - 0.34) / 0.66) ** 1.3
        p = _at_height(p, ell, h0 + peak * rise + (tip - peak) * fall)
        pos[:, k] = p
    # into locks: toward the lead hair, more toward the tip; a few hairs stay free
    s = np.linspace(0.0, 1.0, n)[None, :, None]
    free = rng.random(N) < T["fly"]
    pull = np.where(free, 0.0, T["lock"] * rng.uniform(0.7, 1.0, N))[:, None, None]
    pos = pos + (pos[lead][own] - pos) * pull * s ** 0.8
    side = _unit(np.cross(W, rng.normal(0.0, 1.0, (N, 3))))
    phase, freq = rng.uniform(0.0, 2.0 * math.pi, (N, 1, 1)), rng.uniform(0.7, 1.5, (N, 1, 1))
    pos += side[:, None, :] * (T["wave"] * np.sin(2.0 * math.pi * freq * s + phase) * s)
    pos += rng.normal(0.0, 1.0, pos.shape) * (T["frizz"] * np.where(free, 3.0, 1.0)[:, None, None]) * s
    # no hair under the skin: every point at least a hair's breadth above where its own root stood
    h = _height(pos.reshape(-1, 3), ell).reshape(N, n)
    floor = h0[:, None] + 0.0006 * np.minimum(np.linspace(0.0, 1.0, n)[None, :] * 6.0, 1.0)
    low = h < floor
    low[:, 0] = False
    if low.any():
        fixed = _at_height(pos.reshape(-1, 3), ell, floor.reshape(-1)).reshape(N, n, 3)
        pos = np.where(low[:, :, None], fixed, pos)
    return pos


def _card_weight(card):
    """The generator's own brow card as a measure of where brow hair grows. The card is a small sheet fitted to his
    face, drawn with a picture of a brow that is see-through where no hair is painted. Returns a function that gives,
    for points in the world, how opaque that picture is on the card's nearest place (0 to 1, smoothed over about a
    millimetre), and 0 for points more than 6 mm from the card."""
    from mathutils import Vector
    from mathutils.bvhtree import BVHTree
    from mathutils.interpolate import poly_3d_calc
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = card.evaluated_get(dg)
    me = ev.to_mesh()
    me.calc_loop_triangles()
    M = card.matrix_world
    verts = [M @ v.co for v in me.vertices]
    tris = [tuple(t.vertices) for t in me.loop_triangles]
    uvs = me.uv_layers.active.data
    tri_uv = [[(uvs[l].uv[0], uvs[l].uv[1]) for l in t.loops] for t in me.loop_triangles]
    ev.to_mesh_clear()
    image = None
    for slot in card.material_slots:
        if slot.material and slot.material.node_tree:
            for node in slot.material.node_tree.nodes:
                if node.type == "TEX_IMAGE" and node.image is not None and node.image.channels == 4:
                    image = node.image
    if image is None:
        raise RuntimeError("the generator's brow card carries no picture with a see-through channel")
    w, h = image.size
    alpha = np.array(image.pixels[:], dtype=np.float32).reshape(h, w, 4)[..., 3]
    # the picture is painted in strokes with gaps between them: a mean over 9 by 9 pixels gives the growth's density
    pad = np.pad(alpha, 4, mode="edge")
    alpha = sum(pad[i:i + h, j:j + w] for i in range(9) for j in range(9)) / 81.0
    tree = BVHTree.FromPolygons(verts, tris)
    lo = np.min(np.array(verts), axis=0) - 0.006
    hi = np.max(np.array(verts), axis=0) + 0.006

    def weight(points):
        out = np.zeros(len(points))
        near = np.nonzero(np.all((points >= lo) & (points <= hi), axis=1))[0]
        for i in near:
            loc, nrm, idx, _ = tree.find_nearest(Vector(points[i]), 0.006)
            if loc is None:
                continue
            # only skin that lies under the card: a point beside it would take the opacity of the card's edge
            off = Vector(points[i]) - loc
            if (off - nrm * off.dot(nrm)).length > 0.0015:
                continue
            ws = poly_3d_calc([verts[j] for j in tris[idx]], loc)
            u = sum(wt * uv[0] for wt, uv in zip(ws, tri_uv[idx]))
            v = sum(wt * uv[1] for wt, uv in zip(ws, tri_uv[idx]))
            out[i] = alpha[min(max(int(v * (h - 1) + 0.5), 0), h - 1), min(max(int(u * (w - 1) + 0.5), 0), w - 1)]
        return out

    return weight, image.name


LASH = {
    # (a first try, 130 and 70 hairs of 0.09 mm, straight and evenly spread, showed as a pale comb of fine lines)
    "upper": 130, "lower": 75,               # hairs to a lid: a man's upper lid carries 90 to 160, his lower 75 to 80
    # metres: the longest hair of a lid. A real upper lash is 8 to 12 mm long, a lower one 6 to 8. (The generator's strip
    # is only 4 to 6 mm wide; an earlier build measured it wrongly and grew upper hairs of 16 mm that read as false lashes.)
    "upper_long": 0.0075, "lower_long": 0.006,
    # which way a lash leaves the lid: straight out from the eyeball's middle through its root, tipped by this share
    # upward (negative: downward). A real upper lash leaves the lid pointing forward and a little down and then curls
    # upward; a lower one points forward and down. (The generator's strips point 50 degrees upward from the start, for
    # long curled lashes: hairs along them lay up the lid toward the brow like a brush.)
    "upper_tilt": -0.15, "lower_tilt": -0.50,
    "stray": 0.10,                           # each hair's own direction off that, as a share (0.10: about 6 degrees)
    "bow_upper": 0.50, "bow_lower": -0.12,   # how far a hair curves upward along its length, as a share of that length
    "radius": 0.00007, "tip": 0.12, "points": 6, "seed": 41,    # 0.14 mm thick at the root, as lashes are (thicker than scalp hair)
    "melanin": 1.0, "redness": 0.05, "parts": 3,
    "tuft": 0.0004,                          # metres: lashes stand in little groups; a hair's tip is drawn toward its group's
    "rows": 0.06,                            # the roots stand in a band this share of a hair's length deep, not on one line
}


def lash_strips(card, rig):
    """The generator's four lash strips (an upper and a lower for each eye), each read as the grid of points it is: some
    columns along the lid by a few rows from the lid's rim to the lashes' ends.

    A strip's boundary is one closed loop. Its four corners (the boundary points that belong to a single face) part the
    loop into two long edges and two short ends; the long edge nearer the eyeball's middle is the lid's rim, where a
    lash starts, the other is where the picture's lashes end, and the two carry the same number of points: point for
    point they are the two ends of one column. (Two earlier readings failed: parting the boundary's points by their
    distance from the eyeball, which put 21 points on one edge and 11 on the other, and putting them in order along
    the strip's long direction, which doubles back where the rim curves at the eye's inner corner. Either way the
    hairs leaned along the lid.)

    Returns a list of dicts: side "L" or "R", upper, rim and ends (points in the world, rest pose, in the same order
    along the lid), rim_idx, lid_bone, weights (bone shares of the card's points), axis (the strip's long direction)."""
    me, M = card.data, card.matrix_world
    co = np.array([M @ v.co for v in me.vertices], dtype=np.float64)
    faces = [tuple(f.vertices) for f in me.polygons]
    names = {g.index: g.name for g in card.vertex_groups}
    weights = [{names[g.group]: g.weight for g in v.groups if g.weight > 0.0} for v in me.vertices]
    root_of = list(range(len(co)))

    def find(i):
        while root_of[i] != i:
            root_of[i] = root_of[root_of[i]]
            i = root_of[i]
        return i

    for f in faces:
        for a in f[1:]:
            root_of[find(a)] = find(f[0])
    groups = {}
    for k, f in enumerate(faces):
        groups.setdefault(find(f[0]), []).append(k)
    eye = {s: np.array(rig.matrix_world @ rig.data.bones["eye." + s].head_local) for s in "LR"}
    out = []
    for strip in groups.values():
        verts = sorted({v for k in strip for v in faces[k]})
        s_ = "L" if co[verts, 0].mean() > 0 else "R"
        edges, count = {}, {}
        for k in strip:
            f = faces[k]
            for v in f:
                count[v] = count.get(v, 0) + 1
            for a, b in zip(f, f[1:] + f[:1]):
                edges[(min(a, b), max(a, b))] = edges.get((min(a, b), max(a, b)), 0) + 1
        nb = {}
        for (a, b), n_ in edges.items():
            if n_ == 1:
                nb.setdefault(a, []).append(b)
                nb.setdefault(b, []).append(a)
        corners = [v for v in nb if count[v] == 1]
        if len(corners) != 4 or any(len(m) != 2 for m in nb.values()):
            print(f"HAIR lashes: a strip of {len(verts)} points is not a grid ({len(corners)} corners)", flush=True)
            return None
        loop, before, at_ = [], None, corners[0]
        while True:
            loop.append(at_)
            onward = [v for v in nb[at_] if v != before]
            before, at_ = at_, onward[0]
            if at_ == loop[0] or len(loop) > len(nb):
                break
        cuts = [i for i, v in enumerate(loop) if v in corners]
        chains = [loop[i:j + 1] for i, j in zip(cuts, cuts[1:])] + [loop[cuts[-1]:] + loop[:1]]
        chains.sort(key=len, reverse=True)
        c = co[verts] - co[verts].mean(axis=0)
        axis = np.linalg.svd(c, full_matrices=False)[2][0]
        axis = axis if axis[0] > 0 else -axis
        long_a, long_b = ((ch if co[ch[-1]] @ axis > co[ch[0]] @ axis else ch[::-1]) for ch in chains[:2])
        if len(long_a) != len(long_b):
            print(f"HAIR lashes: a strip's two long edges carry {len(long_a)} and {len(long_b)} points", flush=True)
            return None
        da, db = (float(np.linalg.norm(co[ch] - eye[s_], axis=1).mean()) for ch in (long_a, long_b))
        rim, ends = (long_a, long_b) if da < db else (long_b, long_a)
        w_all = [weights[v] for v in verts]
        upper = sum(w.get("orbicularis03." + s_, 0.0) for w in w_all) > sum(w.get("orbicularis04." + s_, 0.0) for w in w_all)
        out.append({"side": s_, "upper": upper, "rim": co[rim], "ends": co[ends], "rim_idx": list(rim), "weights": weights,
                    "lid_bone": ("orbicularis03." if upper else "orbicularis04.") + s_, "axis": axis, "eye": eye[s_],
                    "rows": len(chains[2]) if len(chains) > 2 else 0})
    return out


def lashes(card, rig, params=None):
    """Lash hairs, strand by strand, grown where the generator's own lash strips lie.

    The generator's lashes are four strips (an upper and a lower for each eye) carrying a picture of lashes 512 pixels
    wide for all four: enlarged in a close picture its strokes go soft and its see-through edges show as ghosts. Each
    strip says where a lash starts (its edge on the lid's rim) and which way it points (along the strip's columns);
    the hairs take both from it and their lengths from real lashes, longest in the lid's middle, curving upward on the
    upper lid and downward on the lower, each a little shorter or longer than its neighbour.

    The strips move with the lids because their points are shared between the head's bone and a lid's bone. Hair cannot
    be shared out point by point here, so each lid's hairs are gathered into three parts along the lid, each held by
    the two bones in the mean shares of the strip's rim there. Returns the hair objects; the strips are left in the
    file and kept out of the pictures. If the strips cannot be read, nothing is grown and the strips stay in the pictures."""
    P = dict(LASH, **(params or {}))
    rng = np.random.default_rng(P["seed"])
    strips = lash_strips(card, rig)
    if not strips:
        print("HAIR lashes: NO HAIRS GROWN, the generator's painted strips stay", flush=True)
        return []
    up = np.array((0.0, 0.0, 1.0))
    mat = hair_material("ManLashes", P["melanin"], P["redness"], 0.25)
    made, report = [], []
    for st in strips:
        s_, upper, r_pts, t_pts, axis, weights = st["side"], st["upper"], st["rim"], st["ends"], st["axis"], st["weights"]
        run = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(r_pts, axis=0), axis=1))))
        r_run = run / run[-1]

        def at(pts, s):
            return np.stack([np.interp(s, r_run, pts[:, k]) for k in range(3)], axis=-1)

        n = P["upper"] if upper else P["lower"]
        s = rng.uniform(0.04, 0.96, n)                             # none at the very corners of the eye
        R, T = at(r_pts, s), at(t_pts, np.clip(s + rng.normal(0.0, 0.012, n), 0.0, 1.0))
        span = T - R
        width = np.linalg.norm(span, axis=1)
        out_ = R - st["eye"]
        out_ /= np.linalg.norm(out_, axis=1)[:, None]
        unit = out_ + up[None, :] * (P["upper_tilt"] if upper else P["lower_tilt"]) + rng.normal(0.0, P["stray"], (n, 3))
        unit /= np.linalg.norm(unit, axis=1)[:, None]
        tangent = at(r_pts, np.clip(s + 0.02, 0.0, 1.0)) - at(r_pts, np.clip(s - 0.02, 0.0, 1.0))
        lean_deg = np.degrees(np.arcsin(np.clip(np.abs(np.einsum("nk,nk->n", unit, tangent)) / np.maximum(np.linalg.norm(tangent, axis=1), 1e-9), 0.0, 1.0)))
        length = (0.40 + 0.60 * np.sin(np.pi * s) ** 0.7) * rng.uniform(0.70, 1.0, n) * (P["upper_long"] if upper else P["lower_long"])
        u = np.linspace(0.0, 1.0, P["points"])
        R = R + unit * (rng.random(n) * P["rows"] * length)[:, None]
        pos = R[:, None, :] + unit[:, None, :] * (length[:, None] * u[None, :])[..., None]
        pos += up[None, None, :] * ((P["bow_upper"] if upper else P["bow_lower"]) * length[:, None] * u[None, :] ** 2)[..., None]
        # little groups: each hair's tip is drawn toward the tip of one of a few dozen lead hairs near it
        leads = max(n // 5, 1)
        lead_s = rng.random(leads)
        own = np.argmin(np.abs(s[:, None] - lead_s[None, :]), axis=1)
        drift = (lead_s[own] - s) * np.linalg.norm(r_pts[-1] - r_pts[0]) * 0.6
        pos += axis[None, None, :] * ((np.clip(drift, -P["tuft"], P["tuft"]) + rng.normal(0.0, 0.0003, n))[:, None] * u[None, :] ** 1.5)[..., None]
        pos += up[None, None, :] * (rng.normal(0.0, 0.05, n) * length)[:, None, None] * (u[None, :, None] ** 2)
        # three parts along the lid, each held as the strip's rim is held there
        r_idx, lid_bone = np.array(st["rim_idx"]), st["lid_bone"]
        for part in range(P["parts"]):
            lo, hi = part / P["parts"], (part + 1) / P["parts"]
            which = (s >= lo) & (s < hi if part < P["parts"] - 1 else s <= hi)
            if not which.any():
                continue
            here = [v for v, t in zip(r_idx, r_run) if lo - 0.05 <= t <= hi + 0.05] or list(r_idx)
            share = {b: float(np.mean([weights[v].get(b, 0.0) for v in here])) for b in ("head", lid_bone)}
            total = sum(share.values()) or 1.0
            ob = _object(f"Man3_Lash_{'U' if upper else 'D'}{s_}{part}", pos[which], P["radius"], rig, mat, tip=P["tip"])
            ob.parent = None
            ob.matrix_world.identity()
            con = ob.constraints.new("ARMATURE")
            for b, w in share.items():
                if w > 0.0:
                    t = con.targets.new()
                    t.target, t.subtarget, t.weight = rig, b, w / total
            made.append(ob)
        report.append(f"{'upper' if upper else 'lower'} {'left' if s_ == 'L' else 'right'}: {n} hairs of {float(length.min()) * 1000:.1f} to {float(length.max()) * 1000:.1f} mm, "
                      f"the strip {len(r_pts)} columns by {st['rows']} rows and {float(width.mean()) * 1000:.1f} mm wide, its rim {float(np.linalg.norm(R - st['eye'], axis=1).mean()) * 1000:.1f} mm "
                      f"from the eyeball's middle, the hairs' ends {float(np.linalg.norm(pos[:, -1] - st['eye'], axis=1).mean()) * 1000:.1f} mm, ends {float((pos[:, -1, 2] - R[:, 2]).mean()) * 1000:.1f} mm above their roots, "
                      f"leaning {float(np.median(lean_deg)):.0f} degrees off square to the rim at the median ({float(np.percentile(lean_deg, 95)):.0f} at the 95th hundredth)")
    card.hide_render = True
    print("HAIR lashes: " + "; ".join(sorted(report)) + f"; in {len(made)} parts held by the head's bone and the lids' bones", flush=True)
    return made


def grow(body, rig, params=None, brow_card=None):
    """Grow his scalp hair, his beard or stubble and his brows, and mark on his skin where hair grows (the attribute
    tv_hair, which the skin reads to show hair under its surface as real skin does). Returns the hair objects by name."""
    P = dict(HAIR)
    for k, v in (params or {}).items():
        P[k] = dict(P[k], **v) if isinstance(v, dict) and isinstance(P.get(k), dict) else v
    centre, fwd, left, up = _frame(rig)
    a, b, c, n, area, mi, names = _surface(body)
    mid = (a + b + c) / 3.0
    full = P["beard"] in ("short", "boxed")
    boxed = P["boxed"] if P["beard"] == "boxed" else None
    face = _face(mid, mi, names, centre, fwd, left, up) if full else None
    if boxed is not None and "ear_front" not in face:
        raise RuntimeError("his ears' material was not found: the sideburns cannot be placed")
    if face is not None:
        from . import man as _man
        eye_mid = np.array(_man.eyes_point(rig)) - centre
        face.update(eye_x=float(eye_mid @ fwd), eye_z=float(eye_mid @ up))
    if face is not None and "ear_rear" in face and P.get("behind_ear", True):
        # where the hairline crosses the middle of the back of his neck: a set distance under the lobe's bottom, read off his
        # own neck there as an elevation
        nape_z = face["ear_bottom"] - P["sides"]["nape_drop"]
        rel_mid = mid - centre
        mx, my, mz = rel_mid @ fwd, rel_mid @ left, rel_mid @ up
        strip_back = (np.abs(my) < 0.012) & (mx < 0.0) & (np.abs(mz - nape_z) < 0.006)
        nape_elev = math.degrees(math.atan2(nape_z, float(-mx[strip_back].min()))) if strip_back.any() else None
        print(f"HAIR nape line: {-nape_z * 1000:.0f} mm under the head's middle ({P['sides']['nape_drop'] * 1000:.0f} mm under the lobe's bottom), "
              f"where the back of his neck stands {(-mx[strip_back].min() * 1000) if strip_back.any() else float('nan'):.0f} mm behind the head's middle: "
              f"an elevation of {nape_elev if nape_elev is not None else float('nan'):.1f} degrees", flush=True)
        P["hairline"] = _behind_ear(P.get("hairline") or HAIRLINE, face, nape_elev)
    scalp_w, beard_w, x, y, z = _fields(mid, centre, fwd, left, up, face, boxed, P.get("hairline"))
    # the skin proper: not the ears, lips or nails, which carry their own materials (triview/manlook.py)
    is_skin = np.isin(mi, [i for i, s in enumerate(names) if s == "ManSkin" or s.endswith(".body")])
    mat = hair_material(melanin=P["melanin"], redness=P["redness"])
    made = {}
    local = lambda p: np.stack(((p - centre) @ fwd, (p - centre) @ left, (p - centre) @ up), axis=-1)
    world = lambda q: centre + q[..., 0:1] * fwd + q[..., 1:2] * left + q[..., 2:3] * up
    crown = centre + up * 0.118 - fwd * 0.035

    def lying(pts, nrm):
        away = pts - crown
        away -= nrm * np.sum(away * nrm, axis=1)[:, None]         # along the surface, away from the crown
        return _unit(away)

    if P["style"] == "quiff":
        lo, hi = P["ridge"]
        t = np.clip((z - lo) / (hi - lo), 0.0, 1.0)
        topness = t * t * (3.0 - 2.0 * t)
        # ---- the top: long, swept up and back ----
        T = P["top"]
        rng = np.random.default_rng(T["seed"])
        every = area * scalp_w * is_skin
        ell = _fit_ellipsoid(local(mid[(every > 0) & (z > 0.0)]))
        # heights above his own scalp, not above the ellipsoid: his skull leaves it by several millimetres at the back
        head_tris = (np.linalg.norm(mid - centre, axis=1) < 0.2) & is_skin
        ell = (ell[0], ell[1], _scalp_map(ell, (local(a[head_tris]), local(b[head_tris]), local(c[head_tris]))))
        pts, nrm, idx = _sample(a, b, c, n, every * topness, T["count"], rng)
        pos = world(_swept(local(pts), T, ell, rng))
        pos[:, 0] = pts - nrm * 0.0004
        made["scalp"] = _object("Man3_Hair", pos, T["radius"], rig, mat, tip=0.45)
        print(f"HAIR top: {T['count']} hairs of {T['crown'] * 1000:.0f} to {T['front'] * 1000:.0f} mm on "
              f"{float((every * (topness > 0.5) > 0).astype(float) @ area) * 1e4:.0f} cm2; the skull's ellipsoid: middle "
              f"{tuple(round(float(v), 3) for v in ell[0])}, half-widths {tuple(round(float(v), 3) for v in ell[1])}; his scalp stands "
              f"{float(np.percentile(_height(local(mid[(every > 0) & (z > 0.0)]), (ell[0], ell[1])), 2)) * 1000:.0f} to "
              f"{float(np.percentile(_height(local(mid[(every > 0) & (z > 0.0)]), (ell[0], ell[1])), 98)) * 1000:.0f} mm off that ellipsoid", flush=True)
        # ---- the sides and the back: faded, a couple of millimetres at the bottom, longer toward the top ----
        S = P["sides"]
        rng = np.random.default_rng(S["seed"])
        NP = S["nape"]
        above_mid, az_mid = _above_hairline(mid, centre, fwd, left, up, P.get("hairline"))
        back_mid = np.clip((az_mid - NP["from"]) / NP["over"], 0.0, 1.0)
        thinning = 1.0 - back_mid + back_mid * np.clip(above_mid / NP["thin"], 0.0, 1.0)
        pts, nrm, idx = _sample(a, b, c, n, every * (1.0 - topness) * thinning, S["count"], rng)
        zz = (pts - centre) @ up
        ramp = np.clip((zz + 0.012) / (lo + 0.012), 0.0, 1.0) ** 1.6
        length = S["low"] + (S["high"] - S["low"]) * ramp
        # at the back of the head the cut tapers low: longer hair right up to the top's edge, short only near the nape,
        # so the top does not end over nearly bare skin (the sides before the ears keep their fade)
        qs = local(pts)
        behind = np.clip((np.degrees(np.arctan2(np.abs(qs[:, 1]), qs[:, 0])) - 105.0) / 30.0, 0.0, 1.0)
        taper = np.interp(zz, list(S["back_at"]) + [lo], S["back"])
        length = (length * (1.0 - behind) + taper * behind) * rng.uniform(0.8, 1.12, len(pts)) * (0.5 + 0.5 * scalp_w[idx])
        above, az_p = _above_hairline(pts, centre, fwd, left, up, P.get("hairline"))
        at_back = np.clip((az_p - NP["from"]) / NP["over"], 0.0, 1.0)
        h = np.maximum(above, 0.0)
        cut = (NP["cut"][0] + NP["cut"][1] * h + NP["cut"][2] * h * h) * rng.uniform(0.85, 1.1, len(pts))
        length = length * (1.0 - at_back) + np.minimum(length, cut) * at_back
        away = lying(pts, nrm)
        flow = _unit(away - fwd[None, :] * 0.45)                    # down and a little back
        lean = 0.45 + 0.3 * ramp
        lean = lean + (S["back_lie"] - lean) * behind
        lean = lean + (np.maximum(NP["lie"], lean) - lean) * at_back * np.clip(1.0 - h / NP["lie_over"], 0.0, 1.0)
        low = at_back > 0.5
        print(f"HAIR nape: {int(low.sum())} of the sides' hairs stand at the back and behind the ears; by height above the hairline "
              + ", ".join(f"{int(lo_mm)} to {int(hi_mm)} mm: {int(((h[low] >= lo_mm / 1000) & (h[low] < hi_mm / 1000)).sum())} hairs of "
                          f"{float(np.median(length[low][(h[low] >= lo_mm / 1000) & (h[low] < hi_mm / 1000)]) * 1000) if ((h[low] >= lo_mm / 1000) & (h[low] < hi_mm / 1000)).any() else 0.0:.1f} mm"
                          for lo_mm, hi_mm in ((0, 5), (5, 10), (10, 20), (20, 30), (30, 45), (45, 70))), flush=True)
        if boxed is not None:
            # the sideburn: never shorter than the beard's sides it runs into, and lying straight down
            q = local(pts)
            strip = _styled(q[:, 0], q[:, 1], q[:, 2], face, boxed)["burn"] > 0.3
            length = np.where(strip, np.clip(length, boxed["burn_short"] * rng.uniform(0.9, 1.1, len(pts)), boxed["burn_long"]), length)
            # before the ear the hair lies straight down; on the temple above it keeps the sides' own lie, down and back
            beside = strip & (q[:, 2] < face["ear_top"])
            down_s = -up[None, :] - nrm * np.sum(-up[None, :] * nrm, axis=1)[:, None]
            flow = np.where(beside[:, None], _unit(down_s), flow)
            lean = np.where(strip, 0.78, lean)
            print(f"HAIR temples and sideburns: {int(strip.sum())} of the sides' hairs, of {boxed['burn_short'] * 1000:.0f} to {boxed['burn_long'] * 1000:.0f} mm; "
                  f"the temple's peak {(face['ear_front'] + boxed['temple'][3] * (face['eye_x'] - face['ear_front'])) * 1000:.0f} mm forward, {(face['eye_x'] - face['ear_front'] - boxed['temple'][3] * (face['eye_x'] - face['ear_front'])) * 1000:.0f} mm behind the eyeball's middle; ear front "
                  f"{face['ear_front'] * 1000:.0f} mm, top {face['ear_top'] * 1000:.0f}, lobe {face['ear_bottom'] * 1000:.0f} (from the head's middle); "
                  f"the front edge stands {boxed['temple'][2] * (face['eye_x'] - face['ear_front']) * 1000:.0f} mm before the ear's front at the eyes' level, "
                  f"{boxed['temple'][1] * (face['eye_x'] - face['ear_front']) * 1000:.0f} at the ear's middle, "
                  f"{boxed['temple'][0] * (face['eye_x'] - face['ear_front']) * 1000:.0f} at the beard's top; from the eyes' level down it leans "
                  f"{math.degrees(math.atan2((boxed['temple'][0] - boxed['temple'][2]) * (face['eye_x'] - face['ear_front']), face['eye_z'] - face['ear_bottom'] - boxed['burn_low'])):.0f} degrees forward", flush=True)
        dirs = nrm * (1.0 - lean)[:, None] + flow * lean[:, None] + rng.normal(0.0, 0.1, (len(pts), 3))
        made["sides"] = _object("Man3_HairSides", _strands(pts, dirs, flow * 0.7 - nrm * 0.15, length, 4, rng, frizz=0.00025),
                                S["radius"], rig, mat)
        print(f"HAIR on his neck: the head's bone now carries his skin whole on {_carry_with_head(body, rig, centre, fwd, left, up, P.get('hairline'), NP)} "
              f"points under the hair at the back of his neck and behind his ears", flush=True)
        print(f"HAIR sides: {S['count']} hairs of {S['low'] * 1000:.1f} to {S['high'] * 1000:.0f} mm", flush=True)
    else:
        # ---- the crop ----
        S = P["scalp"]
        rng = np.random.default_rng(S["seed"])
        pts, nrm, idx = _sample(a, b, c, n, area * scalp_w * is_skin, S["count"], rng)
        away = lying(pts, nrm)
        topness = np.clip((((pts - centre) @ up) - 0.02) / 0.07, 0.0, 1.0)      # 1 on the top of the head, 0 on the sides
        length = (S["side"] + (S["top"] - S["side"]) * topness) * rng.uniform(0.75, 1.15, len(pts)) * (0.45 + 0.55 * scalp_w[idx])
        lean = 0.55 - 0.25 * topness                               # hair on the sides lies flatter
        dirs = nrm * (1.0 - lean)[:, None] + away * lean[:, None] + rng.normal(0.0, 0.12, (len(pts), 3))
        made["scalp"] = _curves("Man3_Hair", pts, dirs, away * 0.6 - up[None, :] * 0.25, length, S["radius"], rig, mat)
        print(f"HAIR scalp: {S['count']} hairs on {float((area * (scalp_w > 0) * is_skin).sum()) * 1e4:.0f} cm2", flush=True)

    if boxed is not None:
        # ---- the barbered beard: short at the sides, longer on the chin, trimmed lines, a moustache cut along the lip ----
        B = boxed
        rng = np.random.default_rng(B["seed"])
        bmat = mat if B["melanin"] is None else hair_material("ManBeard", B["melanin"], B["redness"] if B["redness"] is not None else P["redness"], 0.38)
        lip_mid = _styled(x, y, z, face, B)["lip"]
        # the chin's front faces the camera and the sun squarely and shows skin through a thin growth: more hairs there
        chin_mid = np.clip(1.0 - np.abs(y) / 0.032, 0.0, 1.0) * np.clip((face["mouth_z"] - 0.008 - z) / 0.018, 0.0, 1.0)
        pts, nrm, idx = _sample(a, b, c, n, area * beard_w * is_skin * (1.0 + B["lip_thick"] * (lip_mid > 0.5) + 0.8 * chin_mid), B["count"], rng)
        q = local(pts)
        st = _styled(q[:, 0], q[:, 1], q[:, 2], face, B)
        m, ay = face["mouth_z"], np.abs(q[:, 1])
        on_lip = (st["lip"] > 0.5) & (q[:, 2] > m + 0.001)
        chinness = np.clip(1.0 - ay / 0.032, 0.0, 1.0) * np.clip((m - 0.008 - q[:, 2]) / 0.018, 0.0, 1.0)
        length = B["side"] + (B["jaw"] - B["side"]) * st["t"] ** 1.3
        length = length + (B["chin"] - length) * chinness
        length = length * np.clip((st["cheek_z"] - q[:, 2]) / 0.008, 0.45, 1.0)           # shorter up to the cheek line: a clean edge
        in_strip = (st["burn"] > 0.3) & (q[:, 2] > st["cheek_z"] - 0.004)                 # the sideburn: the beard's side length, not trimmed
        length = np.where(in_strip, B["side"], length)
        length = np.minimum(length, B["neck"] + (length - B["neck"]) * np.clip((q[:, 2] - st["floor_z"]) / 0.012, 0.0, 1.0))
        # the moustache: every hair cut where it reaches the lip's upper edge, which curves down to the corners
        lip_edge = face["lip_top"] - (face["lip_top"] - m) * np.clip(ay / face["mouth_half"], 0.0, 1.0) ** 2
        cut = np.clip((q[:, 2] - lip_edge) * 1.2 + 0.002, 0.003, B["lip"])
        length = np.where(on_lip, cut, length) * rng.uniform(0.85, 1.05, len(pts))
        down = -up[None, :]
        out_side = left[None, :] * np.sign(q[:, 1])[:, None]
        u = np.clip(ay / (face["mouth_half"] + 0.012), 0.0, 1.0)[:, None]
        flow = np.where(on_lip[:, None], down * (1.0 - 0.55 * u) + out_side * (0.2 + 0.8 * u),
                        down + fwd[None, :] * (0.30 - 0.18 * chinness[:, None]))
        flow = _unit(flow - nrm * np.sum(flow * nrm, axis=1)[:, None])
        stand = np.where(on_lip, 0.24, 0.22 + 0.16 * chinness)
        dirs = nrm * stand[:, None] + flow * (1.0 - stand)[:, None] + rng.normal(0.0, 0.09, (len(pts), 3))
        pos = _strands(pts, dirs, flow * 0.7 - nrm * 0.3, length, B["points"], rng, wave=B["wave"], frizz=B["frizz"])
        made["stubble"] = _object("Man3_Stubble", pos, B["radius"], rig, bmat, tip=0.55)
        print(f"HAIR beard, barbered: {B['count']} hairs ({int(on_lip.sum())} on the lip) on {float((area * (beard_w > 0) * is_skin).sum()) * 1e4:.0f} cm2; "
              f"mouth at {m * 1000:.0f} mm, lip top {face['lip_top'] * 1000:.0f}, chin's underside {face['chin_z'] * 1000:.0f}, "
              f"chin's tip {face['chin_x'] * 1000:.0f} forward, mouth half-width {face['mouth_half'] * 1000:.0f}", flush=True)
    elif full:
        # ---- a short full beard: longest on the chin, shorter up the cheeks and down the neck, a moustache ----
        B = P["short"]
        rng = np.random.default_rng(B["seed"])
        bmat = mat if B["melanin"] is None else hair_material("ManBeard", B["melanin"], B["redness"] if B["redness"] is not None else P["redness"], 0.38)
        # the upper lip grows as thickly as the chin and has far less skin to grow on: its hairs are drawn closer together
        az_mid = np.degrees(np.arctan2(np.abs(y), x))
        lip_zone = (z > face["mouth_z"] - 0.001) & (np.abs(y) < face["mouth_half"] + 0.011) & (az_mid < 40)
        pts, nrm, idx = _sample(a, b, c, n, area * beard_w * is_skin * (1.0 + B["lip_thick"] * lip_zone), B["count"], rng)
        q = local(pts)
        az = np.degrees(np.arctan2(np.abs(q[:, 1]), q[:, 0]))
        m, chin = face["mouth_z"], face["chin_z"]
        on_lip = (q[:, 2] > m - 0.001) & (np.abs(q[:, 1]) < face["mouth_half"] + 0.011) & (az < 40)
        chinness = np.clip(1.0 - az / 38.0, 0.0, 1.0) * np.clip((m - 0.006 - q[:, 2]) / 0.02, 0.0, 1.0)
        cheek = np.clip((q[:, 2] - (m - 0.012)) / 0.03, 0.0, 1.0) * (~on_lip)
        neck = np.clip((chin - 0.004 - q[:, 2]) / 0.012, 0.0, 1.0)
        length = B["jaw"] + (B["chin"] - B["jaw"]) * chinness
        length = length + (B["cheek"] - length) * cheek
        length = length + (B["neck"] - length) * neck
        length = np.where(on_lip, B["lip"], length) * rng.uniform(0.75, 1.1, len(pts)) * (0.4 + 0.6 * beard_w[idx])
        down = -up[None, :]
        out_side = left[None, :] * np.sign(q[:, 1])[:, None]
        flow = np.where(on_lip[:, None], down * 0.75 + out_side * 0.65, down + out_side * 0.12 * np.clip(az / 60.0, 0.0, 1.0)[:, None])
        flow = _unit(flow - nrm * np.sum(flow * nrm, axis=1)[:, None])
        stand = np.where(on_lip, 0.30, 0.42 + 0.14 * chinness)
        dirs = nrm * stand[:, None] + flow * (1.0 - stand)[:, None] + rng.normal(0.0, 0.14, (len(pts), 3))
        pos = _strands(pts, dirs, flow * 0.7 - nrm * 0.25, length, B["points"], rng, wave=B["wave"], frizz=B["frizz"])
        made["stubble"] = _object("Man3_Stubble", pos, B["radius"], rig, bmat, tip=0.5)
        print(f"HAIR beard: {B['count']} hairs on {float((area * (beard_w > 0) * is_skin).sum()) * 1e4:.0f} cm2; mouth at "
              f"{m * 1000:.0f} mm, lip top {face['lip_top'] * 1000:.0f}, chin {chin * 1000:.0f}, mouth half-width "
              f"{face['mouth_half'] * 1000:.0f} (from the head's middle)", flush=True)
    else:
        # ---- stubble: the lower face and the top of the neck ----
        B = P["stubble"]
        rng = np.random.default_rng(B["seed"])
        pts, nrm, idx = _sample(a, b, c, n, area * beard_w * is_skin, B["count"], rng)
        dirs = nrm * 0.8 - up[None, :] * 0.45 + rng.normal(0.0, 0.2, (len(pts), 3))
        length = B["length"] * rng.uniform(0.6, 1.2, len(pts))
        print(f"HAIR stubble: {B['count']} hairs on {float((area * (beard_w > 0) * is_skin).sum()) * 1e4:.0f} cm2", flush=True)
        made["stubble"] = _curves("Man3_Stubble", pts, dirs, -up[None, :] * np.ones((len(pts), 3)) * 0.3, length, B["radius"], rig, mat, points=3)

    # ---- brows: an arc over each eye, hairs lying outward ----
    R = P["brows"]
    rng = np.random.default_rng(R["seed"])
    from . import man
    eyes = np.array(man.eyes_point(rig))
    wide = float(R.get("width", 1.0))

    def brow_field(points, fwd_x):
        ex, ez = (points - eyes) @ left, (points - eyes) @ up
        sx = np.abs(ex)
        arc = 0.0215 + 0.0075 * np.sin(np.clip((sx - 0.010) / 0.048, 0.0, 1.0) * math.pi * 0.8)    # the brow's middle line above the eyes
        width = 0.0045 * wide * (1.0 - 0.55 * np.clip((sx - 0.030) / 0.028, 0.0, 1.0))            # thinner toward the tail
        inb = (sx > 0.009) & (sx < 0.058) & (np.abs(ez - arc) < width) & (fwd_x > 0.05)
        return inb * np.clip(1.0 - np.abs(ez - arc) / np.maximum(width, 1e-6), 0.0, 1.0) ** 0.6

    card_w = None
    if R.get("card") and brow_card is not None:
        # the brows grow where the generator's own brow card lies on his face, as thickly as its picture is opaque:
        # the place and the shape then follow his face (a rule of heights above the eyes put them 14 mm too high on
        # the third man, 2026-11-19)
        card_w, card_name = _card_weight(brow_card)
        opaque = card_w(mid)
        brow_w = np.where(opaque > 0.05, np.sqrt(opaque), 0.0)            # the root spreads the growth toward the picture's thin edges
    else:
        brow_w = brow_field(mid, x)
    grown = (area * (brow_w > 0) * is_skin)
    ez_all = (mid - eyes) @ up
    print(f"HAIR brows: {R['count']} hairs on {float(grown.sum()) * 1e4:.1f} cm2"
          + (f", from the generator's card ({card_name}), {float(ez_all[grown > 0].min()) * 1000:.0f} to {float(ez_all[grown > 0].max()) * 1000:.0f} mm above his eyeball middles" if card_w is not None and grown.sum() > 0 else "")
          + f"; eyes at {tuple(round(float(v), 3) for v in eyes)}, head's middle {tuple(round(float(v), 3) for v in centre)}", flush=True)
    if (area * brow_w * is_skin).sum() > 0:
        pts, nrm, idx = _sample(a, b, c, n, area * brow_w * is_skin, R["count"], rng)
        side = np.sign((pts - eyes) @ left)[:, None]
        sxp = np.abs((pts - eyes) @ left)
        inner = np.clip(1.0 - (sxp - 0.009) / 0.016, 0.0, 1.0)[:, None]                         # the inner end stands up more
        if card_w is not None:
            # hairs lie along the brow, outward: up and out at its inner end, level along its body, down and out at its tail
            tail = np.clip((sxp - 0.040) / 0.014, 0.0, 1.0)[:, None]
            flow = left[None, :] * side * (1.0 - 0.35 * inner) + up[None, :] * (0.75 * inner - 0.30 * tail)
            flow -= nrm * np.sum(flow * nrm, axis=1)[:, None]
            flow /= np.maximum(np.linalg.norm(flow, axis=1)[:, None], 1e-9)
            dirs = nrm * 0.10 + flow * 0.95 + rng.normal(0.0, 0.07, (len(pts), 3))
            # shorter toward the tail and where the growth thins: every hair points outward, and at full length the
            # tail came out as a blunt, heavy end (2026-11-19)
            length = (R["length"] * rng.uniform(0.6, 1.05, len(pts)) * (0.7 + 0.3 * np.clip(brow_w[idx] / 0.6, 0.0, 1.0))
                      * (1.0 - 0.35 * tail[:, 0]))
            # brow hair is the darkest on a head and lies on lit skin: its own darker material
            brow_mat = hair_material("ManBrows", R.get("melanin", P["melanin"]), R.get("redness", P["redness"]), 0.36)
            made["brows"] = _curves("Man3_Brows", pts, dirs, flow * 0.4 - nrm * 0.5, length, R["radius"], rig, brow_mat)
        else:
            flow = left[None, :] * side * (1.0 - 0.5 * inner) + up[None, :] * (0.25 + 0.75 * inner) * 0.6
            flow -= nrm * np.sum(flow * nrm, axis=1)[:, None]
            flow /= np.maximum(np.linalg.norm(flow, axis=1)[:, None], 1e-9)
            dirs = nrm * 0.28 + flow * 0.9 + rng.normal(0.0, 0.08, (len(pts), 3))
            length = R["length"] * rng.uniform(0.6, 1.1, len(pts)) * (0.6 + 0.4 * (1.0 - inner[:, 0] * 0.3))
            made["brows"] = _curves("Man3_Brows", pts, dirs, flow * 0.5 - nrm * 0.25, length, R["radius"], rig, mat)

    # ---- where hair grows, marked on the skin itself ----
    vp = _base_points(body)
    v_scalp, v_beard, vx, _, vz = _fields(vp, centre, fwd, left, up, face, boxed, P.get("hairline"))
    if P["style"] == "quiff":
        # faded sides show more scalp through the hair: the mark is lighter where the hair is shortest
        v_scalp = v_scalp * (0.55 + 0.45 * np.clip((vz + 0.012) / (P["ridge"][0] + 0.012), 0.0, 1.0))
        # at the nape and behind the ears the shadow of shaved hair under the skin comes in over the taper's first 2 cm
        NP = P["sides"]["nape"]
        v_above, v_az = _above_hairline(vp, centre, fwd, left, up, P.get("hairline"))
        v_back = np.clip((v_az - NP["from"]) / NP["over"], 0.0, 1.0)
        v_scalp = v_scalp * (1.0 - v_back + v_back * np.clip(v_above / 0.02, 0.0, 1.0) ** 0.8)
    v_brow = np.clip(card_w(vp) / 0.5, 0.0, 1.0) if card_w is not None else brow_field(vp, vx)
    mark = np.maximum(np.maximum(v_scalp, (1.0 if full else 0.55) * v_beard), (1.0 if card_w is not None else 0.8) * v_brow).astype(np.float32)
    attr = body.data.attributes.get("tv_hair") or body.data.attributes.new("tv_hair", "FLOAT", "POINT")
    attr.data.foreach_set("value", mark)
    return made

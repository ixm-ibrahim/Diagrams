"""The man's surfaces for Cycles (rung 3): skin, eyes, cloth.

The generator gives him a hand-painted colour map for the skin (2048 pixels, no pores). This module puts that map under a
skin that scatters light beneath its surface the way skin does (Blender's random walk for skin), adds the relief the map
lacks by formula (pores about 0.4 mm apart, a finer and a coarser unevenness) and breaks the map's even colour with a
faint blotchiness. Lengths are metres, as the room is.

Round two (2026-11-20): the skin's fine relief and its fine colour variation are a real man's. They come from an open
scan of a head (LPS head: "Infinite, 3D Head Scan" by Lee Perry-Smith, Infinite-Realities, CC BY 3.0: credit is owed
wherever the piece is shown), carried onto his face place for place, and on the rest of him a patch of that scan's
forehead repeated at its true size (the maps in assets/open/lpshead/derived; how they are made: the working note).
Only the fine part is taken: no shape, no tone, no feature of the scanned man. The pores by formula stay as the
fall-back when the maps are not on disk.

Every formula of the skin reads his REST pose (the attributes tv_rest and tv_restn, written by skin()), not the place
his skin is at in the frame: with the frame's own coordinates the blotches, moles and relief slid over him as he moved.

Stand-in or staying: the method stays; the painted map is the open route's limit and is what a scanned head replaces.
"""
import json
import pathlib

import bpy

# Round three (2026-11-20): the maps come from a better scan where it is on disk: Digital Reality Lab's free "Marcus" head
# sample (8K colour, relief and shine of a real man; free for personal and commercial use WITH CREDIT; neither its files
# nor anything made from them may be passed on, so they live under assets/licensed, outside git, and a scene that packs
# them must not be published). From it his face takes the scan's own COLOUR as well (brought to his painted map's
# overall tone, so he keeps his complexion and his own face's shape), not only the fine relief. The first folder below
# that holds the maps is the one used.
DETAILS = (pathlib.Path(__file__).resolve().parents[1] / "assets" / "licensed" / "digitalrealitylab" / "derived",
           pathlib.Path(__file__).resolve().parents[1] / "assets" / "open" / "lpshead" / "derived")
DETAIL = next((d for d in DETAILS if (d / "skin_detail.json").exists()), DETAILS[-1])

SKIN = {
    "scatter_scale": 0.005,                  # metres: how far light travels under the skin (the red channel's reach)
    "scatter_radius": (1.0, 0.36, 0.17),     # red goes farthest, blue least: the warm glow at a shadow's edge
    "roughness": 0.50,
    "roughness_var": 0.09,
    "coat": 0.0,                             # the thin film of oil on skin
    "sheen": 0.12,                           # the down on skin at a grazing angle
    "pore_scale": 2600.0,                    # cells a metre: pores about 0.4 mm apart
    "pore_depth": 0.00006,                   # metres
    "fine_scale": 900.0,                     # the fine unevenness, about a millimetre
    "coarse_scale": 140.0,                   # the coarse unevenness, about 7 mm
    "relief": 0.9, 
    "mottle_scale": 60.0,                    # blotches about 1.5 cm
    "mottle": 0.05,                          # the share by which a blotch shifts the colour
    "saturation": 1.12,
    "value": 0.58,
    "hair_shadow": 0.6,                      # how far the skin goes toward a dark cool tone where hair grows
    "flush": 0.55,                           # how far the nose, cheeks and ears go toward red
    "oil": 0.10,                             # how much smoother the forehead and the nose are
    "mole_scale": 220.0,                     # cells a metre: a pattern of 4.5 mm
    "mole_share": 0.02,                      # the share of its cells that carry a mole
    "mole": 0.7,                             # how dark a mole is
    "detail": True,                          # the scan's fine relief and tint, where the maps are on disk
    "detail_relief": 1.6,                    # 1 = the heights as calibrated (a cheek's mean roughness of 20 micrometres)
    "detail_tint": 1.0,                      # 1 = the scan's fine colour variation as it is, 0 = none
    "scatter_weight": 1.0,                   # the share of his skin's colour that comes from under the surface (the rest from its very top, sharp)
    "ear_flush": 0.45,                       # how much redder than the rest his ears are, by formula
    # the rims of his lids where they meet the eyeball (the attribute tv_wet, mark_face): pinker, smooth and wet, as a
    # living lid's rim is; on the painted map and the scan they were pale dry skin
    "lid_tint": 0.7, "lid_gloss": 0.22, "lid_coat": 0.5,
    # metres of depth for a fine part that is darker by the whole of its brightness: a pore 10 percent darker than the
    # skin round it lies 80 micrometres deep, as a real pore does (0 leaves the finest relief out; at 0.00025 it could not be seen)
    "fine_depth": 0.0008,
    "lip_sat": 0.8, "lip_val": 0.93, "lip_rough": 0.42, "lip_relief": 0.35, "lip_coat": 0.04,
}

EYE_BROWN = {"IrisMajorColor": (0.21, 0.095, 0.035, 1.0), "IrisMinorColor": (0.075, 0.03, 0.012, 1.0),
             "IrisSection4Color": (0.02, 0.01, 0.005, 1.0), "EyeWhiteColor": (0.90, 0.87, 0.83, 1.0)}


def _painted_map(body):
    """The generator's colour map of the skin: the first sRGB picture inside its skin group."""
    for slot in body.material_slots:
        mat = slot.material
        if mat is None or not mat.use_nodes:
            continue
        stack = [mat.node_tree]
        while stack:
            nt = stack.pop()
            for n in nt.nodes:
                if n.type == "TEX_IMAGE" and n.image is not None and n.image.colorspace_settings.name == "sRGB":
                    return n.image
                if n.type == "GROUP" and n.node_tree is not None:
                    stack.append(n.node_tree)
    raise RuntimeError("the generator's skin carries no colour map")


def _enabled(sockets, name):
    """A Mix node carries a socket of each name for every kind of data: the one in use."""
    return next(s for s in sockets if s.name == name and s.enabled)


def _detail(nt, p, rest):
    """The scan's fine relief (a height in metres) and fine tint (a colour to multiply by) for his skin, as two
    sockets; None when the maps are not on disk or the skin is told to do without."""
    info_path = DETAIL / "skin_detail.json"
    if not p.get("detail") or not info_path.exists():
        return None
    info = json.loads(info_path.read_text(encoding="utf-8"))
    N, L = nt.nodes.new, nt.links.new

    def image(name, colour=False):
        img = bpy.data.images.load(str(DETAIL / name), check_existing=True)
        img.colorspace_settings.name = "sRGB" if colour else "Non-Color"
        return img

    def tex(img, vector, extension, smooth=False):
        t = N("ShaderNodeTexImage")
        t.image, t.extension = img, extension
        t.interpolation = "Cubic" if smooth else "Linear"
        L(vector, t.inputs["Vector"])
        return t.outputs["Color"]

    def math(op, a, b=None):
        m = N("ShaderNodeMath")
        m.operation = op
        for k, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                m.inputs[k].default_value = v
            else:
                L(v, m.inputs[k])
        return m.outputs["Value"]

    # ---- his face: the maps laid out as his own skin is, a box of his UV layout ----
    u0, u1, v0, v1 = info["uv_box"]
    coord = N("ShaderNodeTexCoord")
    place = N("ShaderNodeMapping")
    place.vector_type = "POINT"
    place.inputs["Scale"].default_value = (1.0 / (u1 - u0), 1.0 / (v1 - v0), 1.0)
    place.inputs["Location"].default_value = (-u0 / (u1 - u0), -v0 / (v1 - v0), 0.0)
    L(coord.outputs["UV"], place.inputs["Vector"])
    face_h = tex(image("head_relief.png"), place.outputs["Vector"], "EXTEND", smooth=True)
    face_t = None if info.get("colour") else tex(image("head_tint.png"), place.outputs["Vector"], "EXTEND")
    trust = tex(image("head_trust.png"), place.outputs["Vector"], "CLIP")
    # his skin's layout cuts him just under the jaw: a second set of maps carries the scan's skin on down his neck
    trust_head, more_colour = trust, None
    for part in [q for q in info.get("parts", []) if q["name"] != "head"]:
        a0, a1, b0, b1 = part["uv_box"]
        place_n = N("ShaderNodeMapping")
        place_n.vector_type = "POINT"
        place_n.inputs["Scale"].default_value = (1.0 / (a1 - a0), 1.0 / (b1 - b0), 1.0)
        place_n.inputs["Location"].default_value = (-a0 / (a1 - a0), -b0 / (b1 - b0), 0.0)
        L(coord.outputs["UV"], place_n.inputs["Vector"])
        part_h = tex(image(part["name"] + "_relief.png"), place_n.outputs["Vector"], "EXTEND", smooth=True)
        part_k = tex(image(part["name"] + "_trust.png"), place_n.outputs["Vector"], "CLIP")
        join_h = N("ShaderNodeMix")
        join_h.data_type = "FLOAT"
        L(trust_head, _enabled(join_h.inputs, "Factor"))
        L(part_h, _enabled(join_h.inputs, "A"))
        L(face_h, _enabled(join_h.inputs, "B"))
        face_h = _enabled(join_h.outputs, "Result")
        trust = math("MAXIMUM", trust, part_k)
        if info.get("colour"):
            more_colour = tex(image(part["name"] + "_colour.png", colour=True), place_n.outputs["Vector"], "EXTEND")
    # ---- everywhere else: a patch of the scan's forehead at its true size, laid on from three sides of his rest pose ----
    restn = N("ShaderNodeAttribute")
    restn.attribute_name = "tv_restn"
    scaled = N("ShaderNodeVectorMath")
    scaled.operation = "SCALE"
    scaled.inputs["Scale"].default_value = 1.0 / info["tile_m"]
    L(rest, scaled.inputs[0])
    xyz = N("ShaderNodeSeparateXYZ")
    L(scaled.outputs["Vector"], xyz.inputs["Vector"])
    absn = N("ShaderNodeVectorMath")
    absn.operation = "ABSOLUTE"
    L(restn.outputs["Vector"], absn.inputs[0])
    nxyz = N("ShaderNodeSeparateXYZ")
    L(absn.outputs["Vector"], nxyz.inputs["Vector"])
    tile_r, tile_t = image("tile_relief.png"), image("tile_tint.png")
    total, sum_h, sum_t = None, None, None
    for side, (a, b) in (("X", ("Y", "Z")), ("Y", ("X", "Z")), ("Z", ("X", "Y"))):
        flat = N("ShaderNodeCombineXYZ")
        L(xyz.outputs[a], flat.inputs["X"])
        L(xyz.outputs[b], flat.inputs["Y"])
        w = math("POWER", nxyz.outputs[side], 4.0)
        h = math("MULTIPLY", tex(tile_r, flat.outputs["Vector"], "REPEAT", smooth=True), w)
        t = N("ShaderNodeVectorMath")
        t.operation = "SCALE"
        L(tex(tile_t, flat.outputs["Vector"], "REPEAT"), t.inputs[0])
        L(w, t.inputs["Scale"])
        if total is None:
            total, sum_h, sum_t = w, h, t.outputs["Vector"]
        else:
            total, sum_h = math("ADD", total, w), math("ADD", sum_h, h)
            add = N("ShaderNodeVectorMath")
            add.operation = "ADD"
            L(sum_t, add.inputs[0])
            L(t.outputs["Vector"], add.inputs[1])
            sum_t = add.outputs["Vector"]
    one_over = math("DIVIDE", 1.0, total)
    tile_h = math("MULTIPLY", sum_h, one_over)
    tile_tint = N("ShaderNodeVectorMath")
    tile_tint.operation = "SCALE"
    L(sum_t, tile_tint.inputs[0])
    L(one_over, tile_tint.inputs["Scale"])
    # ---- the two together: his face's own where the match is trusted ----
    mix_h = N("ShaderNodeMix")
    mix_h.data_type = "FLOAT"
    L(trust, _enabled(mix_h.inputs, "Factor"))
    L(tile_h, _enabled(mix_h.inputs, "A"))
    L(face_h, _enabled(mix_h.inputs, "B"))
    height = math("MULTIPLY", math("SUBTRACT", _enabled(mix_h.outputs, "Result"), 0.5), 2.0 * info["relief_clip_m"] * p["detail_relief"])
    if info.get("fine") and p.get("fine_depth") and (DETAIL / info["fine"]).exists():
        # the finest relief, on his face only, twice as fine as the scan's measured relief: ESTIMATED from the fine part
        # of the scan's own photographs (darker there: deeper, a pore or a line), not measured. The map holds 0.5 plus
        # the share by which the fine part stands off 1, times 1 / fine_span.
        fine_h = tex(image(info["fine"]), place.outputs["Vector"], "EXTEND", smooth=True)
        height = math("ADD", height, math("MULTIPLY", math("MULTIPLY", math("SUBTRACT", fine_h, 0.5), trust_head), info.get("fine_span", 0.5) * p["fine_depth"]))
    mix_t = N("ShaderNodeMix")
    mix_t.data_type = "RGBA"
    L(trust, _enabled(mix_t.inputs, "Factor"))
    L(tile_tint.outputs["Vector"], _enabled(mix_t.inputs, "A"))
    if face_t is not None:
        L(face_t, _enabled(mix_t.inputs, "B"))
    twice = N("ShaderNodeVectorMath")                         # the maps hold the tint halved, so that they can brighten too
    twice.operation = "SCALE"
    twice.inputs["Scale"].default_value = 2.0
    L(_enabled(mix_t.outputs, "Result"), twice.inputs[0])
    some = N("ShaderNodeMix")
    some.data_type = "RGBA"
    _enabled(some.inputs, "Factor").default_value = p["detail_tint"]
    _enabled(some.inputs, "A").default_value = (1.0, 1.0, 1.0, 1.0)
    L(twice.outputs["Vector"], _enabled(some.inputs, "B"))
    out = {"height": height, "tint": _enabled(some.outputs, "Result"), "trust": trust, "colour": None, "rough": None, "rough_trust": trust_head}
    if info.get("colour"):
        # the scan's own colour for his face; the tint then serves only where the face's map is not trusted (the tile)
        out["colour"] = tex(image("head_colour.png", colour=True), place.outputs["Vector"], "EXTEND")
        if more_colour is not None:
            join_c = N("ShaderNodeMix")
            join_c.data_type = "RGBA"
            L(trust_head, _enabled(join_c.inputs, "Factor"))
            L(more_colour, _enabled(join_c.inputs, "A"))
            L(out["colour"], _enabled(join_c.inputs, "B"))
            out["colour"] = _enabled(join_c.outputs, "Result")
        only_tile = N("ShaderNodeMix")
        only_tile.data_type = "RGBA"
        L(trust, _enabled(only_tile.inputs, "Factor"))
        L(tile_tint.outputs["Vector"], _enabled(only_tile.inputs, "A"))
        _enabled(only_tile.inputs, "B").default_value = (0.5, 0.5, 0.5, 1.0)
        for link in list(twice.inputs[0].links):
            nt.links.remove(link)
        L(_enabled(only_tile.outputs, "Result"), twice.inputs[0])
    if info.get("rough"):
        out["rough"] = math("MULTIPLY", tex(image("head_rough.png"), place.outputs["Vector"], "EXTEND"), 2.0)
    return out


def _skin_material(name, image, p, roughness=None, relief=1.0, coat=None, flush_add=0.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    N, L = nt.nodes.new, nt.links.new
    out = N("ShaderNodeOutputMaterial")
    bsdf = N("ShaderNodeBsdfPrincipled")
    L(bsdf.outputs["BSDF"], out.inputs["Surface"])
    coord = N("ShaderNodeTexCoord")
    # where a point of his skin stands in his rest pose, metres: what every formula below reads, so nothing slides
    rest_attr = N("ShaderNodeAttribute")
    rest_attr.attribute_name = "tv_rest"
    REST = rest_attr.outputs["Vector"]
    detail = _detail(nt, p, REST)
    tex = N("ShaderNodeTexImage")
    tex.image = image
    L(coord.outputs["UV"], tex.inputs["Vector"])
    hsv = N("ShaderNodeHueSaturation")
    hsv.inputs["Saturation"].default_value = p["saturation"]
    hsv.inputs["Value"].default_value = p["value"]
    if detail is not None and detail["colour"] is not None:
        tinted = N("ShaderNodeMix")
        tinted.data_type, tinted.blend_type = "RGBA", "MULTIPLY"
        _enabled(tinted.inputs, "Factor").default_value = 1.0
        L(tex.outputs["Color"], _enabled(tinted.inputs, "A"))
        L(detail["tint"], _enabled(tinted.inputs, "B"))
        scanned = N("ShaderNodeMix")
        scanned.data_type = "RGBA"
        L(detail["trust"], _enabled(scanned.inputs, "Factor"))
        L(_enabled(tinted.outputs, "Result"), _enabled(scanned.inputs, "A"))
        L(detail["colour"], _enabled(scanned.inputs, "B"))
        L(_enabled(scanned.outputs, "Result"), hsv.inputs["Color"])
    else:
        L(tex.outputs["Color"], hsv.inputs["Color"])
    # blotchiness: a slow noise in the body's own space brightens and reddens by a few percent
    mottle = N("ShaderNodeTexNoise")
    mottle.inputs["Scale"].default_value = p["mottle_scale"]
    mottle.inputs["Detail"].default_value = 3.0
    L(REST, mottle.inputs["Vector"])
    m_map = N("ShaderNodeMapRange")
    m_map.inputs["From Min"].default_value, m_map.inputs["From Max"].default_value = 0.3, 0.7
    m_map.inputs["To Min"].default_value, m_map.inputs["To Max"].default_value = 1.0 - p["mottle"], 1.0 + p["mottle"]
    L(mottle.outputs["Fac"], m_map.inputs["Value"])
    red = N("ShaderNodeCombineColor")
    L(m_map.outputs["Result"], red.inputs["Red"])
    red.inputs["Green"].default_value = 1.0
    red.inputs["Blue"].default_value = 1.0
    mix = N("ShaderNodeMix")
    mix.data_type, mix.blend_type = "RGBA", "MULTIPLY"
    mix.inputs["Factor"].default_value = 1.0
    if detail is not None and detail["colour"] is None:
        fine_tint = N("ShaderNodeMix")
        fine_tint.data_type, fine_tint.blend_type = "RGBA", "MULTIPLY"
        _enabled(fine_tint.inputs, "Factor").default_value = 1.0
        L(hsv.outputs["Color"], _enabled(fine_tint.inputs, "A"))
        L(detail["tint"], _enabled(fine_tint.inputs, "B"))
        L(_enabled(fine_tint.outputs, "Result"), mix.inputs["A"])
    else:
        L(hsv.outputs["Color"], mix.inputs["A"])
    L(red.outputs["Color"], mix.inputs["B"])
    # hair under the skin: where hair grows (the attribute tv_hair, written by triview/manhair.py) the skin is
    # darker and cooler, as a shaved scalp and a shaved chin are
    grown = N("ShaderNodeAttribute")
    grown.attribute_name = "tv_hair"
    g_mul = N("ShaderNodeMath")
    g_mul.operation = "MULTIPLY"
    g_mul.inputs[1].default_value = p["hair_shadow"]
    L(grown.outputs["Fac"], g_mul.inputs[0])
    shade = N("ShaderNodeMix")
    shade.data_type, shade.blend_type = "RGBA", "MULTIPLY"
    shade.inputs["B"].default_value = (0.42, 0.44, 0.50, 1.0)
    L(g_mul.outputs["Value"], shade.inputs["Factor"])
    L(mix.outputs["Result"], shade.inputs["A"])
    # the face's own colour: blood shows on the nose, the cheeks and the ears (the attribute tv_flush, mark_face)
    flush = N("ShaderNodeAttribute")
    flush.attribute_name = "tv_flush"
    f_mul = N("ShaderNodeMath")
    f_mul.operation = "MULTIPLY_ADD"
    f_mul.inputs[1].default_value = p["flush"]
    f_mul.inputs[2].default_value = flush_add
    L(flush.outputs["Fac"], f_mul.inputs[0])
    warm = N("ShaderNodeMix")
    warm.data_type, warm.blend_type = "RGBA", "MULTIPLY"
    warm.inputs["B"].default_value = (1.0, 0.80, 0.78, 1.0)
    L(f_mul.outputs["Value"], warm.inputs["Factor"])
    L(shade.outputs["Result"], warm.inputs["A"])
    # a few moles: one cell in fifty of a 4.5 mm pattern carries a dark spot about a millimetre across
    moles = N("ShaderNodeTexVoronoi")
    moles.feature, moles.distance = "F1", "EUCLIDEAN"
    moles.inputs["Scale"].default_value = p["mole_scale"]
    L(REST, moles.inputs["Vector"])
    near = N("ShaderNodeMapRange")
    near.inputs["From Min"].default_value, near.inputs["From Max"].default_value = 0.10, 0.24
    near.inputs["To Min"].default_value, near.inputs["To Max"].default_value = 1.0, 0.0
    L(moles.outputs["Distance"], near.inputs["Value"])
    sep = N("ShaderNodeSeparateColor")
    L(moles.outputs["Color"], sep.inputs["Color"])
    few = N("ShaderNodeMath")
    few.operation = "LESS_THAN"
    few.inputs[1].default_value = p["mole_share"]
    L(sep.outputs["Red"], few.inputs[0])
    spot = N("ShaderNodeMath")
    spot.operation = "MULTIPLY"
    L(near.outputs["Result"], spot.inputs[0])
    L(few.outputs["Value"], spot.inputs[1])
    s_mul = N("ShaderNodeMath")
    s_mul.operation = "MULTIPLY"
    s_mul.inputs[1].default_value = p["mole"]
    L(spot.outputs["Value"], s_mul.inputs[0])
    dark = N("ShaderNodeMix")
    dark.data_type, dark.blend_type = "RGBA", "MULTIPLY"
    dark.inputs["B"].default_value = (0.42, 0.30, 0.25, 1.0)
    L(s_mul.outputs["Value"], dark.inputs["Factor"])
    L(warm.outputs["Result"], dark.inputs["A"])
    wet = N("ShaderNodeAttribute")
    wet.attribute_name = "tv_wet"
    w_mul = N("ShaderNodeMath")
    w_mul.operation = "MULTIPLY"
    w_mul.inputs[1].default_value = p["lid_tint"]
    L(wet.outputs["Fac"], w_mul.inputs[0])
    rim = N("ShaderNodeMix")
    rim.data_type, rim.blend_type = "RGBA", "MULTIPLY"
    _enabled(rim.inputs, "B").default_value = (1.0, 0.72, 0.70, 1.0)
    L(w_mul.outputs["Value"], _enabled(rim.inputs, "Factor"))
    L(dark.outputs["Result"], _enabled(rim.inputs, "A"))
    L(_enabled(rim.outputs, "Result"), bsdf.inputs["Base Color"])
    # under the surface
    bsdf.subsurface_method = "RANDOM_WALK_SKIN"
    bsdf.inputs["Subsurface Weight"].default_value = p["scatter_weight"]
    bsdf.inputs["Subsurface Radius"].default_value = p["scatter_radius"]
    bsdf.inputs["Subsurface Scale"].default_value = p["scatter_scale"]
    bsdf.inputs["Subsurface IOR"].default_value = 1.4
    bsdf.inputs["Subsurface Anisotropy"].default_value = 0.8
    bsdf.inputs["IOR"].default_value = 1.45
    # the surface's shine, uneven
    rv = N("ShaderNodeTexNoise")
    rv.inputs["Scale"].default_value = 220.0
    rv.inputs["Detail"].default_value = 2.0
    L(REST, rv.inputs["Vector"])
    r_map = N("ShaderNodeMapRange")
    base_r = p["roughness"] if roughness is None else roughness
    r_map.inputs["To Min"].default_value, r_map.inputs["To Max"].default_value = base_r - p["roughness_var"], base_r + p["roughness_var"]
    L(rv.outputs["Fac"], r_map.inputs["Value"])
    # the forehead and the nose carry more oil and shine more (the attribute tv_oil, mark_face)
    oil = N("ShaderNodeAttribute")
    oil.attribute_name = "tv_oil"
    o_mul = N("ShaderNodeMath")
    o_mul.operation = "MULTIPLY"
    o_mul.inputs[1].default_value = p["oil"]
    L(oil.outputs["Fac"], o_mul.inputs[0])
    r_sub = N("ShaderNodeMath")
    r_sub.operation = "SUBTRACT"
    L(r_map.outputs["Result"], r_sub.inputs[0])
    L(o_mul.outputs["Value"], r_sub.inputs[1])
    r_oil = r_sub
    r_sub = N("ShaderNodeMath")                       # and the lids' rims are wet
    r_sub.operation = "MULTIPLY_ADD"
    r_sub.use_clamp = True
    L(wet.outputs["Fac"], r_sub.inputs[0])
    r_sub.inputs[1].default_value = -p["lid_gloss"]
    L(r_oil.outputs["Value"], r_sub.inputs[2])
    if detail is not None and detail["rough"] is not None:
        uneven = N("ShaderNodeMix")
        uneven.data_type = "FLOAT"
        L(detail["rough_trust"], _enabled(uneven.inputs, "Factor"))
        _enabled(uneven.inputs, "A").default_value = 1.0
        L(detail["rough"], _enabled(uneven.inputs, "B"))
        r_mul = N("ShaderNodeMath")
        r_mul.operation = "MULTIPLY"
        L(r_sub.outputs["Value"], r_mul.inputs[0])
        L(_enabled(uneven.outputs, "Result"), r_mul.inputs[1])
        L(r_mul.outputs["Value"], bsdf.inputs["Roughness"])
    else:
        L(r_sub.outputs["Value"], bsdf.inputs["Roughness"])
    c_wet = N("ShaderNodeMath")
    c_wet.operation = "MULTIPLY_ADD"
    c_wet.use_clamp = True
    L(wet.outputs["Fac"], c_wet.inputs[0])
    c_wet.inputs[1].default_value = p["lid_coat"]
    c_wet.inputs[2].default_value = p["coat"] if coat is None else coat
    L(c_wet.outputs["Value"], bsdf.inputs["Coat Weight"])
    c_rough = N("ShaderNodeMath")
    c_rough.operation = "MULTIPLY_ADD"
    L(wet.outputs["Fac"], c_rough.inputs[0])
    c_rough.inputs[1].default_value = -0.22
    c_rough.inputs[2].default_value = 0.3
    L(c_rough.outputs["Value"], bsdf.inputs["Coat Roughness"])
    bsdf.inputs["Sheen Weight"].default_value = p["sheen"]
    bsdf.inputs["Sheen Roughness"].default_value = 0.5
    # the relief the painted map lacks: pores, a fine and a coarse unevenness, as one height
    pores = N("ShaderNodeTexVoronoi")
    pores.feature, pores.distance = "F1", "EUCLIDEAN"
    pores.inputs["Scale"].default_value = p["pore_scale"]
    L(REST, pores.inputs["Vector"])
    fine = N("ShaderNodeTexNoise")
    fine.inputs["Scale"].default_value = p["fine_scale"]
    fine.inputs["Detail"].default_value = 4.0
    L(REST, fine.inputs["Vector"])
    coarse = N("ShaderNodeTexNoise")
    coarse.inputs["Scale"].default_value = p["coarse_scale"]
    coarse.inputs["Detail"].default_value = 2.0
    L(REST, coarse.inputs["Vector"])
    h1 = N("ShaderNodeMath")
    h1.operation = "MULTIPLY_ADD"                    # pores' distance (0 at a pore's middle) + fine
    L(pores.outputs["Distance"], h1.inputs[0])
    h1.inputs[1].default_value = 1.0
    L(fine.outputs["Fac"], h1.inputs[2])
    h2 = N("ShaderNodeMath")
    h2.operation = "MULTIPLY_ADD"
    L(coarse.outputs["Fac"], h2.inputs[0])
    h2.inputs[1].default_value = 2.5
    L(h1.outputs["Value"], h2.inputs[2])
    bump = N("ShaderNodeBump")
    if detail is not None:
        # heights in metres: the coarse unevenness by formula as before, and the scan's fine relief in place of the pores
        slow = N("ShaderNodeMath")
        slow.operation = "MULTIPLY"
        L(coarse.outputs["Fac"], slow.inputs[0])
        slow.inputs[1].default_value = 2.5 * p["pore_depth"] * p["relief"] * relief
        both = N("ShaderNodeMath")
        both.operation = "MULTIPLY_ADD"
        L(detail["height"], both.inputs[0])
        both.inputs[1].default_value = relief ** 0.5
        L(slow.outputs["Value"], both.inputs[2])
        bump.inputs["Strength"].default_value = 1.0
        bump.inputs["Distance"].default_value = 1.0
        dry = N("ShaderNodeMath")                     # no skin relief on the wet rims
        dry.operation = "MULTIPLY_ADD"
        L(wet.outputs["Fac"], dry.inputs[0])
        dry.inputs[1].default_value = -0.9
        dry.inputs[2].default_value = 1.0
        level = N("ShaderNodeMath")
        level.operation = "MULTIPLY"
        L(both.outputs["Value"], level.inputs[0])
        L(dry.outputs["Value"], level.inputs[1])
        L(level.outputs["Value"], bump.inputs["Height"])
    else:
        bump.inputs["Strength"].default_value = p["relief"] * relief
        bump.inputs["Distance"].default_value = p["pore_depth"]
        L(h2.outputs["Value"], bump.inputs["Height"])
    L(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat


def _rest_frame(body):
    """Every point of his base mesh in the rest pose, where the generator's shape puts it, and the skin's outward
    direction there: in the world, modifiers left out."""
    import numpy as np
    shown = [(m, m.show_viewport) for m in body.modifiers]
    for m, _ in shown:
        m.show_viewport = False
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = body.evaluated_get(dg)
    me = ev.to_mesh()
    n = len(me.vertices)
    co, no = np.empty(n * 3, dtype=np.float32), np.empty(n * 3, dtype=np.float32)
    me.vertices.foreach_get("co", co)
    me.vertex_normals.foreach_get("vector", no)
    ev.to_mesh_clear()
    for m, was in shown:
        m.show_viewport = was
    dg.update()
    M = np.array(body.matrix_world)
    pts = co.reshape(-1, 3).astype(np.float64) @ M[:3, :3].T + M[:3, 3]
    nrm = no.reshape(-1, 3).astype(np.float64) @ M[:3, :3].T
    return pts, nrm / np.maximum(np.linalg.norm(nrm, axis=1)[:, None], 1e-12)


def mark_face(body, rig, lash_card=None):
    """Mark on his skin where blood shows (tv_flush: the nose's tip, the two cheeks) and where the skin is oilier
    (tv_oil: the nose and the forehead), by rule from the tip of his own nose, in the head's frame."""
    import numpy as np
    from . import manhair
    centre, fwd, left, up = manhair._frame(rig)
    rel = manhair._base_points(body) - centre
    x, y, z = rel @ fwd, rel @ left, rel @ up
    head = np.linalg.norm(rel, axis=1) < 0.2
    middle = head & (np.abs(y) < 0.012) & (z > -0.05) & (z < 0.02)
    i = int(np.argmax(np.where(middle, x, -1.0)))
    nx, nz = float(x[i]), float(z[i])                         # the nose's tip

    def blob(cx, cy, cz, r):
        return np.exp(-((x - cx) ** 2 + (y - cy) ** 2 + (z - cz) ** 2) / (r * r))

    flush = np.maximum.reduce([0.9 * blob(nx - 0.006, 0.0, nz + 0.004, 0.017),
                               0.75 * blob(nx - 0.042, 0.047, nz + 0.004, 0.027),
                               0.75 * blob(nx - 0.042, -0.047, nz + 0.004, 0.027)]) * head
    oil = np.maximum(0.8 * blob(nx - 0.01, 0.0, nz + 0.012, 0.02), 0.9 * blob(nx - 0.03, 0.0, nz + 0.075, 0.04)) * head
    # the rims of his lids: the band of skin between the line his lashes grow from and the lid's own edge at the
    # eyeball, a few millimetres wide. Found from the generator's lash strips: his skin's points that lie within a few
    # millimetres of a strip's edge on the lid, on the side of the eye's opening (under the upper lid's lash line, over
    # the lower lid's). (A first rule, every point of skin within 2.8 mm of the eyeball's surface, took the whole of
    # both lids, which lie on the eyeball: his upper lid shone as if wet.)
    wet = np.zeros(len(rel))
    strips = manhair.lash_strips(lash_card, rig) if lash_card is not None else None
    world = rel + centre
    for st in strips or []:
        run = np.concatenate(([0.0], np.cumsum(np.linalg.norm(np.diff(st["rim"], axis=0), axis=1))))
        fine = np.linspace(0.0, run[-1], 400)
        line = np.stack([np.interp(fine, run, st["rim"][:, k_]) for k_ in range(3)], axis=-1)
        near = np.flatnonzero(np.linalg.norm(world - st["eye"], axis=1) < 0.03)
        gap = np.linalg.norm(world[near][:, None, :] - line[None, :, :], axis=-1)
        j = gap.argmin(axis=1)
        dist = gap[np.arange(len(near)), j]
        inward = (line[j, 2] - world[near, 2]) * (1.0 if st["upper"] else -1.0)          # metres toward the eye's opening
        here = (1.0 - np.clip((dist - EYE["rim"][0]) / (EYE["rim"][1] - EYE["rim"][0]), 0.0, 1.0)) * np.clip((inward - 0.0001) / 0.0005, 0.0, 1.0)
        wet[near] = np.maximum(wet[near], here)
        print(f"SKIN lids' rims: {'upper' if st['upper'] else 'lower'} {'left' if st['side'] == 'L' else 'right'}: {int((here > 0.5).sum())} points of skin marked; "
              f"of the skin within 4 mm of the lash line, {int(((dist < 0.004) & (inward > 0.0001)).sum())} points lie toward the eye's opening and {int(((dist < 0.004) & (inward <= 0.0001)).sum())} away from it", flush=True)
    wet *= head
    print(f"SKIN lids' rims: {int((wet > 0.5).sum())} of his skin's points marked as a lid's wet rim, {int((wet > 0.0).sum())} touched"
          + ("" if strips else " (NO LASH STRIPS READ: no rim marked)"), flush=True)
    for name, values in (("tv_flush", flush), ("tv_oil", oil), ("tv_wet", wet)):
        attr = body.data.attributes.get(name) or body.data.attributes.new(name, "FLOAT", "POINT")
        attr.data.foreach_set("value", values.astype(np.float32))
    return {"nose_tip_forward": nx, "nose_tip_up": nz}


def skin(body, params=None):
    """Replace the generator's skin on every slot of his body with this module's, the lips and nails by their own
    variants of it (smoother, shinier). Returns the materials by slot name."""
    p = dict(SKIN, **(params or {}))
    image = _painted_map(body)
    rest, restn = _rest_frame(body)
    for attr_name, values in (("tv_rest", rest), ("tv_restn", restn)):
        attr = body.data.attributes.get(attr_name) or body.data.attributes.new(attr_name, "FLOAT_VECTOR", "POINT")
        attr.data.foreach_set("vector", values.astype("float32").ravel())
    print("SKIN: his rest pose written onto his", len(rest), "points; the scan's fine relief and tint "
          + ("in use" if p.get("detail") and (DETAIL / "skin_detail.json").exists() else "NOT in use (the pores by formula)")
          + f", from {DETAIL.parent.name}", flush=True)
    made = {"skin": _skin_material("ManSkin", image, p),
            "ears": _skin_material("ManEars", image, p, flush_add=p["ear_flush"]),      # the same skin under its own name: no hair grows on it; ears are redder
            # a man's lips: a little paler and duller than the painted map has them, and not wet
            "lips": _skin_material("ManLips", image, dict(p, saturation=p["saturation"] * p["lip_sat"], value=p["value"] * p["lip_val"]),
                                   roughness=p["lip_rough"], relief=p["lip_relief"], coat=p["lip_coat"]),
            "nails": _skin_material("ManNails", image, p, roughness=0.22, relief=0.1, coat=0.5)}
    for slot in body.material_slots:
        nm = slot.material.name if slot.material else ""
        kind = ("lips" if nm.endswith(".lips") else "nails" if nm.endswith(("fingernails", "toenails"))
                else "ears" if nm.endswith(".ears") else "skin")
        slot.material = made[kind]
    return made, image


EYE = {
    # (the first numbers, a white of 0.80 and veins at 0.55 that came in only far from the iris, gave a clean bright white
    # with no vein to be seen in the part of the eye the lids leave open)
    # (in the low sun the white stands at the picture's bright end, where colour washes out: at a white of 0.66 and vessels
    # mixed in at a quarter of their own colour, no vessel and no tone could be seen at all)
    "white": (0.56, 0.54, 0.51, 1.0),        # the white of the eye where it is clearest, beside the iris
    "corner": (0.60, 0.42, 0.36, 1.0),       # its tone toward the corners: pinker and a little darker
    "vein": (0.42, 0.03, 0.03, 1.0),
    "veins": 0.8,                            # how strongly the vessels show at most (at 1.0 the eye read as bloodshot)
    "vein_thin": (0.016, 0.022),             # the winding lines' half width, in the cloud pattern's own units: about 0.1 mm on the eye
    "corner_at": 0.62,                       # how far round from the eye's own axis the corner's tone is full (0.62: 52 degrees)
    "cornea_ior": 1.376,
    "ball": 0.0149,                          # metres: the eyeball's radius (the ball fitted through the eye mesh in eyes())
    "rim": (0.0022, 0.0040),                 # metres from the lash line toward the eye's opening: a lid's wet rim inside the first, dry skin beyond the second
    "lash": (0.035, 0.022, 0.016, 1.0),      # a dark brown: near black with wide strokes read as painted lashes
    "lash_edge": (0.22, 0.55),               # the share of the picture's opacity at which a stroke begins and is full
}


def eyes(eyes_obj, colours=None, rig=None, lashes=None, params=None):
    """The generator's own eye (a clear outer layer over an iris drawn by formula): its colours set, brown by default.

    Round three (2026-11-20, his word: the eyes "look too smooth"), three things on top of the generator's eye:
      light   the clear front of the eye let no sunlight through to the eyeball (a renderer follows light through curved
              glass only with help), so the white and the iris were lit by the room's glow alone and lay flat and grey.
              For the rays that ask "is this point in shadow" the eye's clear front now counts as not there.
      white   the white of the eye was one even colour. It now has fine veins in patches, more toward the corners, and
              a tone that goes pinker and darker away from the iris. They are drawn in the eyeball's own rest
              coordinates (the attribute tv_eye), so they turn with the eye.
      lashes  the generator's lashes are a picture on a strip, 512 pixels for all four rows: enlarged, its strokes
              went soft and pale. The strokes' edges are drawn crisp again and the lashes are near black.
    Stand-in or staying: the light and the white stay. The lashes are still the generator's picture on a strip; real
    lash hairs that follow the lids come with the hair that moves with his skin (rung 4)."""
    colours = colours or EYE_BROWN
    e = dict(EYE, **(params or {}))
    mat = eyes_obj.material_slots[0].material
    nt = mat.node_tree
    group = next(n for n in nt.nodes if n.type == "GROUP")
    for key, value in colours.items():
        if key in group.inputs:
            group.inputs[key].default_value = value
    if "OuterLayerIOR" in group.inputs:
        group.inputs["OuterLayerIOR"].default_value = e["cornea_ior"]
    N, L = nt.nodes.new, nt.links.new
    out = next(n for n in nt.nodes if n.type == "OUTPUT_MATERIAL")
    # ---- light through the clear front ----
    if not any(n.type == "LIGHT_PATH" for n in nt.nodes):
        path, clear, both = N("ShaderNodeLightPath"), N("ShaderNodeBsdfTransparent"), N("ShaderNodeMixShader")
        L(path.outputs["Is Shadow Ray"], both.inputs[0])
        L(group.outputs["BSDF"], both.inputs[1])
        L(clear.outputs["BSDF"], both.inputs[2])
        L(both.outputs["Shader"], out.inputs["Surface"])
    # ---- the white: tone and veins, in each eyeball's own rest coordinates ----
    if rig is not None and "EyeWhiteColor" in group.inputs and all(b in rig.data.bones for b in ("eye.L", "eye.R")):
        import numpy as np
        me = eyes_obj.data
        co = np.array([eyes_obj.matrix_world @ v.co for v in me.vertices])
        # each eyeball's own middle: the middle of the ball that fits its outer points best (the eye bones' heads do not lie
        # there: measured from them every point of the white counted as straight ahead, and no vessel showed)
        bone = {s: np.array(rig.matrix_world @ rig.data.bones["eye." + s].head_local) for s in "LR"}
        left = np.linalg.norm(co - bone["L"], axis=1) < np.linalg.norm(co - bone["R"], axis=1)
        centre = {}
        for s, sel in (("L", left), ("R", ~left)):
            pts = co[sel]
            far = pts[np.linalg.norm(pts - pts.mean(axis=0), axis=1) > np.median(np.linalg.norm(pts - pts.mean(axis=0), axis=1))]
            A = np.c_[2.0 * far, np.ones(len(far))]
            sol = np.linalg.lstsq(A, (far ** 2).sum(axis=1), rcond=None)[0]
            centre[s] = sol[:3]
            print(f"EYES: the {'left' if s == 'L' else 'right'} eyeball's middle {np.round(centre[s], 4)}, radius {float(np.sqrt(sol[3] + (sol[:3] ** 2).sum())) * 1000:.1f} mm; "
                  f"the eye bone's head {np.round(bone[s], 4)}", flush=True)
        own = np.where(left[:, None], co - centre["L"], co - centre["R"])
        attr = me.attributes.get("tv_eye") or me.attributes.new("tv_eye", "FLOAT_VECTOR", "POINT")
        attr.data.foreach_set("vector", own.astype(np.float32).ravel())
        at = N("ShaderNodeAttribute")
        at.attribute_name = "tv_eye"

        def vmath(op, a, b=None, scale=None):
            m = N("ShaderNodeVectorMath")
            m.operation = op
            L(a, m.inputs[0])
            if b is not None:
                if isinstance(b, tuple):
                    m.inputs[1].default_value = b
                else:
                    L(b, m.inputs[1])
            if scale is not None:
                m.inputs["Scale"].default_value = scale
            return m

        def ranged(value, a, b, lo=0.0, hi=1.0):
            m = N("ShaderNodeMapRange")
            m.inputs["From Min"].default_value, m.inputs["From Max"].default_value = a, b
            m.inputs["To Min"].default_value, m.inputs["To Max"].default_value = lo, hi
            L(value, m.inputs["Value"])
            return m.outputs["Result"]

        def times(a, b):
            m = N("ShaderNodeMath")
            m.operation = "MULTIPLY"
            L(a, m.inputs[0])
            if isinstance(b, (int, float)):
                m.inputs[1].default_value = b
            else:
                L(b, m.inputs[1])
            return m.outputs["Value"]

        unit = vmath("NORMALIZE", at.outputs["Vector"])
        ahead = vmath("DOT_PRODUCT", unit.outputs["Vector"], (0.0, -1.0, 0.0)).outputs["Value"]   # 1 on the eye's own axis, 0 at its sides
        side = ranged(ahead, 0.86, e["corner_at"])                           # 0 at the iris's rim, 1 toward the corners
        # the red vessels of the white run in from the eye's two corners toward the iris, thin and winding, and fade before
        # they reach it. Here: the borders of long cells stretched along the eye's left-to-right direction, a coarse net
        # and a finer one, strongest to the left and right of the iris.
        parts = N("ShaderNodeSeparateXYZ")
        L(unit.outputs["Vector"], parts.inputs["Vector"])
        sideways = N("ShaderNodeMath")
        sideways.operation = "ABSOLUTE"
        L(parts.outputs["X"], sideways.inputs[0])
        beside = ranged(sideways.outputs["Value"], 0.15, 0.45, 0.35, 1.0)

        def vessels(stretch, warp_scale, warp, thin):
            w = N("ShaderNodeTexNoise")
            w.inputs["Scale"].default_value = warp_scale
            L(at.outputs["Vector"], w.inputs["Vector"])
            moved = vmath("ADD", at.outputs["Vector"], vmath("SCALE", w.outputs["Color"], scale=warp).outputs["Vector"])
            long_cells = vmath("MULTIPLY", moved.outputs["Vector"], stretch)
            net = N("ShaderNodeTexVoronoi")
            net.feature = "DISTANCE_TO_EDGE"
            net.inputs["Scale"].default_value = 1.0
            L(long_cells.outputs["Vector"], net.inputs["Vector"])
            return ranged(net.outputs["Distance"], 0.0, thin, 1.0, 0.0)

        def winding(stretch, warp_scale, warp, thin, shift):
            """Long winding lines with open ends: the places where a smooth cloud pattern, stretched along the eye's
            left-to-right direction, passes through its middle value. (Cell borders alone, the first build of
            2026-11-20, close into a net of rings like a honeycomb; a real eye's vessels are separate winding lines
            that fork.)"""
            w = N("ShaderNodeTexNoise")
            w.inputs["Scale"].default_value = warp_scale
            L(at.outputs["Vector"], w.inputs["Vector"])
            moved = vmath("ADD", at.outputs["Vector"], vmath("SCALE", w.outputs["Color"], scale=warp).outputs["Vector"])
            long_ = vmath("ADD", vmath("MULTIPLY", moved.outputs["Vector"], stretch).outputs["Vector"], shift)
            field = N("ShaderNodeTexNoise")
            field.inputs["Scale"].default_value = 1.0
            field.inputs["Detail"].default_value = 1.0
            L(long_.outputs["Vector"], field.inputs["Vector"])
            off = N("ShaderNodeMath")
            off.operation = "SUBTRACT"
            L(field.outputs["Fac"], off.inputs[0])
            off.inputs[1].default_value = 0.5
            away = N("ShaderNodeMath")
            away.operation = "ABSOLUTE"
            L(off.outputs["Value"], away.inputs[0])
            return ranged(away.outputs["Value"], 0.0, thin, 1.0, 0.0)

        def most(a, b):
            m = N("ShaderNodeMath")
            m.operation = "MAXIMUM"
            L(a, m.inputs[0])
            L(b, m.inputs[1])
            return m.outputs["Value"]

        patch = N("ShaderNodeTexNoise")
        patch.inputs["Scale"].default_value = 140.0
        L(at.outputs["Vector"], patch.inputs["Vector"])
        main_lines = winding((60.0, 150.0, 400.0), 160.0, 0.0040, e["vein_thin"][0], (0.0, 0.0, 0.0))        # about 17 mm long, 2.5 mm apart
        side_lines = winding((120.0, 280.0, 720.0), 380.0, 0.0020, e["vein_thin"][1], (13.1, 7.7, 3.3))
        # the forks between them: pieces of a fine net of cell borders, kept in patches only, so no ring closes
        forks = times(vessels((170.0, 420.0, 760.0), 520.0, 0.0014, 0.05), ranged(patch.outputs["Fac"], 0.47, 0.60))
        either = most(most(main_lines, times(side_lines, 0.7)), times(forks, 0.45))
        vein = times(times(times(either, side), beside), e["veins"])
        tone = N("ShaderNodeMix")
        tone.data_type = "RGBA"
        L(times(side, 0.8), _enabled(tone.inputs, "Factor"))
        _enabled(tone.inputs, "A").default_value = e["white"]
        _enabled(tone.inputs, "B").default_value = e["corner"]
        veined = N("ShaderNodeMix")
        veined.data_type = "RGBA"
        L(vein, _enabled(veined.inputs, "Factor"))
        L(_enabled(tone.outputs, "Result"), _enabled(veined.inputs, "A"))
        _enabled(veined.inputs, "B").default_value = e["vein"]
        L(_enabled(veined.outputs, "Result"), group.inputs["EyeWhiteColor"])
        # the generator also reads the white's colour as a height: with vessels in it they stood up as shiny ridges and
        # showed as pale arcs, not as red lines (seen in the first pictures of 2026-11-20). The white's height is level now.
        height = group.node_tree.nodes.get("EyewhiteHeight")
        if height is not None:
            for link in list(height.inputs[0].links):
                group.node_tree.links.remove(link)
            height.inputs[0].default_value = (0.8, 0.8, 0.8, 1.0)
    # ---- the lashes: the picture's strokes crisp and near black ----
    if lashes is not None and lashes.material_slots and lashes.material_slots[0].material:
        lt = lashes.material_slots[0].material.node_tree
        bsdf = next((n for n in lt.nodes if n.type == "BSDF_PRINCIPLED"), None)
        pic = next((n for n in lt.nodes if n.type == "TEX_IMAGE" and n.image is not None), None)
        if bsdf is not None and pic is not None and not any(n.type == "MAP_RANGE" for n in lt.nodes):
            pic.interpolation = "Cubic"
            crisp = lt.nodes.new("ShaderNodeMapRange")
            crisp.inputs["From Min"].default_value, crisp.inputs["From Max"].default_value = e["lash_edge"]
            lt.links.new(pic.outputs["Alpha"], crisp.inputs["Value"])
            for link in list(bsdf.inputs["Alpha"].links):
                lt.links.remove(link)
            lt.links.new(crisp.outputs["Result"], bsdf.inputs["Alpha"])
            for link in list(bsdf.inputs["Base Color"].links):
                lt.links.remove(link)
            bsdf.inputs["Base Color"].default_value = e["lash"]
            bsdf.inputs["Roughness"].default_value = 0.42
    return mat


def cloth(ob, colour=None, roughness=0.85):
    """A garment of the generator's: its own picture kept (or one plain colour), a cloth's dull surface with the soft
    glow cotton has at a grazing angle, and a weave by formula. A stand-in: rung 4 makes his real clothes."""
    mat = ob.material_slots[0].material
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    if colour is not None:
        for link in list(bsdf.inputs["Base Color"].links):
            nt.links.remove(link)
        bsdf.inputs["Base Color"].default_value = (*colour, 1.0)
    bsdf.inputs["Roughness"].default_value = roughness
    bsdf.inputs["Sheen Weight"].default_value = 0.12
    bsdf.inputs["Sheen Roughness"].default_value = 0.45
    bsdf.inputs["Specular IOR Level"].default_value = 0.2
    coord = nt.nodes.new("ShaderNodeTexCoord")
    weave = nt.nodes.new("ShaderNodeTexWave")
    weave.wave_type, weave.bands_direction = "BANDS", "X"
    weave.inputs["Scale"].default_value = 2200.0          # threads under half a millimetre
    weave2 = nt.nodes.new("ShaderNodeTexWave")
    weave2.wave_type, weave2.bands_direction = "BANDS", "Z"
    weave2.inputs["Scale"].default_value = 2200.0
    nt.links.new(coord.outputs["Object"], weave.inputs["Vector"])
    nt.links.new(coord.outputs["Object"], weave2.inputs["Vector"])
    add = nt.nodes.new("ShaderNodeMath")
    add.operation = "ADD"
    nt.links.new(weave.outputs["Fac"], add.inputs[0])
    nt.links.new(weave2.outputs["Fac"], add.inputs[1])
    bump = nt.nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = 0.35
    bump.inputs["Distance"].default_value = 0.0001
    nt.links.new(add.outputs["Value"], bump.inputs["Height"])
    nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
    return mat

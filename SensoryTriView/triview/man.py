"""The man (rung 3): a young man generated with the open-source generator MPFB (the MakeHuman community's add-on for
Blender, GPL; its assets public domain or free with credit), with a skeleton, a skin, eyes, lashes, brows, teeth and
clothes, built without a window.

What is a stand-in and what stays: the generator, the skeleton and the way he is put together stay. His face's skin is
the generator's hand-painted one, the open route's limit: a scanned head replaces it if he is judged to need one
(rung 3). His clothes are the generator's fitted ones: rung 4 makes his real clothes. His hair is grown by
triview/manhair.py.

The generator needs to be enabled in the session's preferences before its services can be imported (its own
get_preference looks itself up there), so every entry point goes through generator().
"""
import math
import pathlib

import bpy
from mathutils import Vector

ADDON = "bl_ext.blender_org.mpfb"

# The man as picked on 2026-11-19 at his word ("download whatever you want and just run with it, if I don't like it
# then we can swap it for another"). Every entry is a swap: another skin, another shirt, other numbers.
#   macro: the generator's own sliders, 0 to 1. gender 1 is a man; age 0.5 is 25 years; the three race shares sum to 1.
SPEC = {
    "macro": {"gender": 1.0, "age": 0.5, "muscle": 0.62, "weight": 0.45, "proportions": 0.62, "height": 0.5,
              "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.2, "caucasian": 0.6, "african": 0.2}},
    "crown": 1.756,                      # metres, the height the mannequin's motion was written for (figure.standing)
    "skin": "toigo_light_skin_male_bronze",
    "eyes": "high-poly",
    "lashes": "eyelashes01",
    "brows": "eyebrow006",
    "teeth": "teeth_base",
    "tongue": "tongue01",
    "clothes": ["toigo_basic_tucked_t-shirt", "elvs_male_trouser_short_1"],
    "rig": "default",
    "eye_colour": None,                  # None: brown (manlook.EYE_BROWN)
    "shirt_colour": (0.10, 0.105, 0.12),  # a plain charcoal T-shirt: in the low sun a mid grey reads as cream and a white one burns out
}

# The second man, picked on 2026-11-19 at his word ("can you pick a different face (and body that matches the face?)
# like maybe a more bearded with more stylish hair"): a few years older, a squarer jaw, a stronger chin and brow,
# leaner cheeks, a nose with a slight hump, a slightly thicker neck, an ordinary build of a man near thirty; a short full
# beard; the hair long on top, swept up and back, the sides and back faded (triview/manhair.py).
#   targets: the generator's detail sliders by their file names, 0 to 1, laid over the macro sliders.
SPEC_B = dict(SPEC, **{
    "macro": {"gender": 1.0, "age": 0.53, "muscle": 0.56, "weight": 0.44, "proportions": 0.50, "height": 0.5,
              "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.0, "caucasian": 0.9, "african": 0.1}},
    "targets": {
        "head-square": 0.15, "head-fat-decr": 0.30,
        "chin-bones-incr": 0.20, "chin-width-incr": 0.15, "chin-prominent-incr": 0.30, "chin-jaw-drop-incr": 0.15,
        "l-cheek-bones-incr": 0.30, "r-cheek-bones-incr": 0.30, "l-cheek-volume-decr": 0.45, "r-cheek-volume-decr": 0.45,
        "nose-hump-incr": 0.22, "nose-scale-vert-incr": 0.15, "nose-point-down": 0.12, "nose-width2-decr": 0.15,
        "eyebrows-trans-down": 0.30,
        "mouth-scale-horiz-incr": 0.15, "mouth-lowerlip-volume-incr": 0.15,
        "neck-scale-horiz-incr": 0.10, "neck-scale-depth-incr": 0.05,
    },
    "skin": "young_caucasian_male2",
    # a T-shirt that hangs over the waistband: the tucked one left a strip of bare back above the shorts (2026-11-19)
    "clothes": ["elvs_crude_t-shirt_male", "elvs_male_trouser_short_1"],
    "hem_under_waistband": True,
    "skin_params": {"value": 0.62, "saturation": 1.10, "pore_depth": 0.00012, "roughness_var": 0.14, "mottle": 0.08, "hair_shadow": 0.78},
    # very dark brown: in the low sun anything lighter reads as ginger
    "hair_params": {"style": "quiff", "beard": "short", "melanin": 0.995, "redness": 0.15,
                    "brows": {"count": 1800, "length": 0.009, "width": 1.25, "radius": 0.00005},
                    "short": {"melanin": 1.0, "redness": 0.15}},
})

# The third man, at his word on the second (2026-11-19 about 21:05): "hair is great, but missing side burns that
# connect the head of hair to the beard, and the beard is not shaped sytlishly at all and the moustash is also shaped
# weird too. and the face doesn't really match the hair ... perhaps a more european face. and his body doesn't look
# toned at all, just kind of round, like he should look manly". The hair is the second man's, untouched.
SPEC_C = dict(SPEC_B, **{
    # muscle near the slider's top at an average weight: at a weight of 0.40 the same muscle gave thin arms and legs
    "macro": {"gender": 1.0, "age": 0.53, "muscle": 0.95, "weight": 0.52, "proportions": 0.70, "height": 0.5,
              "cupsize": 0.5, "firmness": 0.5, "race": {"asian": 0.0, "caucasian": 1.0, "african": 0.0}},
    "targets": {
        # a longer, narrower face; eyes set deep under a stronger brow, with a hollow above the lid; a high, narrow,
        # longer nose; lean cheeks; a firm chin and jaw; thinner lips
        "head-oval": 0.25, "head-scale-horiz-decr": 0.25, "head-fat-decr": 0.25,
        # a lower, narrower, flatter forehead (his word of 2026-11-19: "his forehead is massive")
        "forehead-scale-vert-decr": 0.35, "forehead-temple-decr": 0.35, "forehead-nubian-decr": 0.25,
        "eyebrows-trans-forward": 0.45, "eyebrows-trans-down": 0.10,
        "l-eye-eyefold-concave": 0.50, "r-eye-eyefold-concave": 0.50,
        "l-eye-push1-in": 0.30, "r-eye-push1-in": 0.30, "l-eye-push2-in": 0.30, "r-eye-push2-in": 0.30,
        "l-eye-height2-incr": 0.25, "r-eye-height2-incr": 0.25, "l-eye-scale-incr": 0.12, "r-eye-scale-incr": 0.12,
        "nose-greek-incr": 0.25, "nose-scale-depth-incr": 0.30, "nose-scale-vert-incr": 0.20,
        "nose-width1-decr": 0.20, "nose-width2-decr": 0.30, "nose-width3-decr": 0.20, "nose-flaring-decr": 0.20,
        "nose-hump-incr": 0.15, "nose-point-down": 0.10,
        "l-cheek-volume-decr": 0.40, "r-cheek-volume-decr": 0.40,
        "chin-prominent-incr": 0.35, "chin-height-incr": 0.15, "chin-bones-incr": 0.25, "chin-jaw-drop-incr": 0.20,
        "mouth-upperlip-volume-decr": 0.30, "mouth-lowerlip-volume-decr": 0.10, "mouth-scale-horiz-incr": 0.10,
        "neck-scale-horiz-incr": 0.15, "neck-scale-depth-incr": 0.10,
        # a trained body: a chest and a back with muscle on them, shoulders and arms to match, a waist narrower than the chest
        "torso-vshape-incr": 0.30, "torso-muscle-pectoral-incr": 0.50, "torso-muscle-dorsi-incr": 0.40,
        "l-upperarm-muscle-incr": 0.70, "r-upperarm-muscle-incr": 0.70,
        "l-upperarm-shoulder-muscle-incr": 0.60, "r-upperarm-shoulder-muscle-incr": 0.60,
        "l-lowerarm-muscle-incr": 0.50, "r-lowerarm-muscle-incr": 0.50,
    },
    # the round-necked T-shirt (the other one's neck is cut wide and low), its hem carried down inside the shorts
    "clothes": ["toigo_basic_tucked_t-shirt", "elvs_male_trouser_short_1"],
    "hem_under_waistband": False,
    "extend_hem": 0.060,                # metres under the waistband's top the shirt's hem is carried to
    "hide_under_clothes": True,
    # grey-blue eyes
    "eye_colour": {"IrisMajorColor": (0.16, 0.27, 0.36, 1.0), "IrisMinorColor": (0.07, 0.12, 0.18, 1.0),
                   "IrisSection4Color": (0.03, 0.05, 0.08, 1.0)},
    # roughness 0.54 and detail_relief 1.5 since round two (2026-11-20): with the scan's fine relief in place of the pores by
    # formula his skin shone more at roughness 0.50 (the formula's pores, 0.4 mm apart and too deep, had been scattering
    # the highlight); at 0.58 with the heights at 1.1 times the calibrated ones the relief no longer showed in the low sun
    # round three (2026-11-20), with the scanned head's own colour on his face: the formula's blotches, moles and flush are
    # turned down or off (the scan brings real ones), and light travels less far under his skin (0.0035 m for red, close to
    # the measured 3.7 mm; at 0.005 his nose glowed like wax)
    "skin_params": {"value": 0.66, "saturation": 1.02, "pore_depth": 0.00012, "roughness_var": 0.06, "mottle": 0.02, "hair_shadow": 0.78,
                    "roughness": 0.54, "detail_relief": 1.25, "flush": 0.15, "mole_share": 0.0, "scatter_scale": 0.003, "oil": 0.08,
                    # a fifth of his skin's colour from its very top, so the scan's pores and spots stay sharp; the scan's ears and
                    # lips carry their own colour, so the formula's reddening of the ears and the lips' own settings are turned down
                    "scatter_weight": 0.8, "ear_flush": 0.12, "lip_sat": 0.92, "lip_val": 0.97, "lip_rough": 0.38, "lip_relief": 1.0, "lip_coat": 0.0},
    # a thick, nearly straight brow (the generator's twelfth), grown as strands where that card lies on his face
    "brows": "eyebrow012",
    # his hairline 15 mm lower than the first table had it: measured on him it stood 82 mm above his eyes, where a
    # man's stands about 67 (bearing from straight ahead, elevation above the head's middle, degrees)
    "hair_params": {"style": "quiff", "beard": "boxed", "melanin": 0.995, "redness": 0.15,
                    "hairline": ((0, 35), (25, 35.5), (45, 34.5), (58, 31), (66, 24), (74, 14), (84, 9), (96, 8), (108, 2),
                                 (120, -14), (140, -30), (160, -37), (180, -40)),
                    "brows": {"count": 5200, "length": 0.0065, "radius": 0.00005, "card": True, "melanin": 1.0, "redness": 0.12},
                    "boxed": {"melanin": 1.0, "redness": 0.15}},
})

SPECS = {"a": SPEC, "b": SPEC_B, "c": SPEC_C}


def generator():
    """The generator's services, with the add-on enabled for this session (nothing is saved to the preferences)."""
    import addon_utils
    if ADDON not in bpy.context.preferences.addons:
        addon_utils.enable(ADDON, default_set=True)
    from bl_ext.blender_org.mpfb.services import LocationService
    from bl_ext.blender_org.mpfb.services.humanservice import HumanService
    from bl_ext.blender_org.mpfb.services.objectservice import ObjectService
    return HumanService, ObjectService, LocationService


def find_asset(location, name, ext):
    """An asset's file by its name, in the user's packs first, then in the add-on's own data."""
    for root in (location.get_user_data(), location.get_mpfb_data()):
        hits = sorted(pathlib.Path(root).rglob(f"{name}.{ext}"))
        if hits:
            return str(hits[0])
    raise FileNotFoundError(f"the generator has no {name}.{ext}; packs in {location.get_user_data()}")


def crown_height(basemesh):
    """The highest point of his body as it is drawn. The generator shapes him with shape keys over one base mesh and
    hides its helper shapes with a mask, so the mesh has to be read as evaluated: its stored vertices are the unshaped
    base, 7 cm shorter than this man (found 2026-11-19: he stood 1.83 m while the stored mesh said 1.756)."""
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    ev = basemesh.evaluated_get(dg)
    me = ev.to_mesh()
    top = max((ev.matrix_world @ v.co).z for v in me.vertices)
    ev.to_mesh_clear()
    return top


def generate(spec=None, name="Man3"):
    """Build him in the open file at the world's origin, facing -Y, feet on the ground, in the generator's rest pose.
    Returns a dict of his objects: body, rig, eyes, lashes, brows, teeth, tongue, clothes (a list)."""
    spec = dict(SPEC if spec is None else spec)
    HumanService, ObjectService, location = generator()
    # twice: once to read the height the sliders give, once at the scale that puts his crown where the motion has it
    def shaped(scale):
        b = HumanService.create_human(scale=scale, macro_detail_dict=spec["macro"])
        if spec.get("targets"):
            # the detail sliders, before the skeleton and every fitted part: they take their places from his shape
            from bl_ext.blender_org.mpfb.services.targetservice import TargetService
            stack = [{"target": k, "value": float(v)} for k, v in spec["targets"].items()]
            missing = [t["target"] for t in stack if not TargetService.target_full_path(t["target"])]
            if missing:
                raise FileNotFoundError(f"the generator has no detail slider named {missing}")
            TargetService.bulk_load_targets(b, stack)
        return b

    probe = shaped(0.1)
    h0 = crown_height(probe)
    bpy.data.objects.remove(probe, do_unlink=True)
    scale = 0.1 * spec["crown"] / h0
    body = shaped(scale)
    body.name = name + "_Body"
    out = {"body": body, "scale": scale, "slider_height": round(h0, 4)}
    rig = HumanService.add_builtin_rig(body, spec["rig"])
    rig.name = name + "_Rig"
    out["rig"] = rig
    parts = (("eyes", "Eyes", "PROCEDURAL_EYES"), ("lashes", "Eyelashes", "MAKESKIN"), ("brows", "Eyebrows", "MAKESKIN"),
             ("teeth", "Teeth", "MAKESKIN"), ("tongue", "Tongue", "MAKESKIN"))
    for key, kind, material in parts:
        if not spec.get(key):
            continue
        ob = HumanService.add_mhclo_asset(find_asset(location, spec[key], "mhclo"), body, asset_type=kind, subdiv_levels=1,
                                          material_type=material)
        ob.name = f"{name}_{kind}"
        out[key] = ob
    out["clothes"] = []
    for c in spec.get("clothes", []):
        ob = HumanService.add_mhclo_asset(find_asset(location, c, "mhclo"), body, asset_type="Clothes", subdiv_levels=1,
                                          material_type="MAKESKIN")
        ob.name = f"{name}_Cloth_{len(out['clothes'])}"
        ob["tv_garment"] = c
        for mod in ob.modifiers:
            if mod.type == "SUBSURF":
                mod.render_levels = 2
        out["clothes"].append(ob)
    if spec.get("extend_hem") and len(out["clothes"]) >= 2:
        # the round-necked shirt ends at his waist, above shorts that sit on his hips, and a strip of bare skin shows
        # between them when he leans: its lowest ring of points is carried down under the waistband's top and drawn
        # in a little, so that it lies inside the shorts
        import bmesh
        shirt, shorts = out["clothes"][0], out["clothes"][1]
        top = max((shorts.matrix_world @ v.co).z for v in shorts.data.vertices)
        M = shirt.matrix_world
        bm = bmesh.new()
        bm.from_mesh(shirt.data)
        edge = [v for v in bm.verts if v.is_boundary]
        low = min((M @ v.co).z for v in edge)
        hem = [v for v in edge if (M @ v.co).z < low + 0.06]
        cx = sum((M @ v.co).x for v in hem) / len(hem)
        cy = sum((M @ v.co).y for v in hem) / len(hem)
        moved, drop = 0, float(spec["extend_hem"]) if spec["extend_hem"] is not True else 0.035
        for v in hem:
            w = M @ v.co
            if w.z > top - drop:
                v.co = M.inverted() @ Vector((cx + (w.x - cx) * 0.95, cy + (w.y - cy) * 0.95, top - drop))
                moved += 1
        bm.to_mesh(shirt.data)
        bm.free()
        shirt.data.update()
        out["hem"] = {"points": moved, "from": round(low, 3), "to": round(top - drop, 3), "waistband": round(top, 3)}
    if spec.get("hem_under_waistband") and len(out["clothes"]) >= 2:
        # the shirt's tail runs down inside the shorts and comes through their seat about 65 mm under the waistband's
        # top: the shirt is not drawn below a line 40 mm under that top, where the shorts cover it in every pose
        # (at 15 mm the cut's edge showed above the waistband when he leaned, 2026-11-19)
        shirt, shorts = out["clothes"][0], out["clothes"][1]
        top = max((shorts.matrix_world @ v.co).z for v in shorts.data.vertices)
        keep = shirt.vertex_groups.new(name="tv_drawn")
        keep.add([v.index for v in shirt.data.vertices if (shirt.matrix_world @ v.co).z >= top - 0.040], 1.0, "REPLACE")
        mask = shirt.modifiers.new("HemUnderWaistband", "MASK")
        mask.vertex_group = keep.name
        while shirt.modifiers.find(mask.name) > 0:
            shirt.modifiers.move(shirt.modifiers.find(mask.name), shirt.modifiers.find(mask.name) - 1)
        out["hem"] = round(top - 0.040, 3)
    if spec.get("hide_under_clothes") and out["clothes"]:
        # his body is not drawn where a garment covers it, more than 25 mm in from that garment's openings: muscle
        # under a fitted shirt otherwise comes through the cloth as spots of skin (seen on his back, 2026-11-19)
        import bmesh
        from mathutils import kdtree
        from . import manhair
        pts = manhair._base_points(body)
        under = set()
        for ob in out["clothes"]:
            Mw = ob.matrix_world
            gv = [Mw @ v.co for v in ob.data.vertices]
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            rim = [Mw @ v.co for v in bm.verts if v.is_boundary]
            bm.free()
            tree, edge = kdtree.KDTree(len(gv)), kdtree.KDTree(max(len(rim), 1))
            for i, w in enumerate(gv):
                tree.insert(w, i)
            for i, w in enumerate(rim):
                edge.insert(w, i)
            tree.balance()
            edge.balance()
            lo = Vector((min(w.x for w in gv), min(w.y for w in gv), min(w.z for w in gv))) - Vector((0.03, 0.03, 0.03))
            hi = Vector((max(w.x for w in gv), max(w.y for w in gv), max(w.z for w in gv))) + Vector((0.03, 0.03, 0.03))
            for i, q in enumerate(pts):
                if not (lo.x <= q[0] <= hi.x and lo.y <= q[1] <= hi.y and lo.z <= q[2] <= hi.z):
                    continue
                w, j, d = tree.find(Vector(q))
                if d < 0.03 and (not rim or edge.find(w)[2] > 0.025):
                    under.add(i)
        group = body.vertex_groups.new(name="tv_under_cloth")
        group.add(sorted(under), 1.0, "REPLACE")
        mask = body.modifiers.new("UnderClothes", "MASK")
        mask.vertex_group = group.name
        mask.invert_vertex_group = True
        while body.modifiers.find(mask.name) > 1:
            body.modifiers.move(body.modifiers.find(mask.name), body.modifiers.find(mask.name) - 1)
        out["under_clothes"] = len(under)
    HumanService.set_character_skin(find_asset(location, spec["skin"], "mhmat"), body, skin_type="ENHANCED_SSS")
    # his surfaces for Cycles: the generator's painted map under this project's own skin, brown eyes, cloth
    from . import manlook
    manlook.skin(body, spec.get("skin_params"))
    out["face_marks"] = manlook.mark_face(body, rig, lash_card=out.get("lashes"))
    if "eyes" in out:
        manlook.eyes(out["eyes"], spec.get("eye_colour"), rig=rig, lashes=out.get("lashes"), params=spec.get("eye_params"))
    for i, ob in enumerate(out["clothes"]):
        manlook.cloth(ob, colour=spec.get("shirt_colour") if i == 0 else None)
    # his surface smooth at render: the base mesh is coarse (about 13,000 faces of body)
    sub = body.modifiers.new("Smooth", "SUBSURF")
    sub.levels, sub.render_levels = 1, 2
    # his hair, stubble and brows as strands; the generator's painted brow cards then stay out of the pictures
    if spec.get("hair", True):
        from . import manhair
        out["hair"] = manhair.grow(body, rig, spec.get("hair_params"), brow_card=out.get("brows"))
        if "brows" in out["hair"] and "brows" in out:
            if ((spec.get("hair_params") or {}).get("brows") or {}).get("card"):
                # brows grown low over the lid: the skin under them stays with the head when he blinks
                from . import manlids
                out["steady_brows"] = manlids.steady_brows(body, manhair._card_weight(out["brows"])[0])
            out["brows"].hide_render = True
        if "lashes" in out and spec.get("lash_hairs", True):
            # lash hairs strand by strand where the generator's painted lash strips lie; the strips stay out of the pictures
            out["lash_hairs"] = manhair.lashes(out["lashes"], rig, spec.get("lash_params"))
    for ob in [body, rig] + [out[k] for k in ("eyes", "lashes", "brows", "teeth", "tongue") if k in out] + out["clothes"]:
        ob["tv_man"] = name
    return out


EYE_OFFSET = (0.09, 0.0, 0.015)      # the mannequin's eye point from its head's middle: forward, left, up (triview/body.py)


def eyes_point(rig):
    """The point between the middles of his two eyeballs, in the world, in the rest pose."""
    b = rig.data.bones
    return rig.matrix_world @ ((b["eye.L"].head_local + b["eye.R"].head_local) * 0.5)


def head_centre(rig):
    """The middle of his head in the rest pose, placed from his eyes as the mannequin's eye point is placed from its
    head's middle, so the two heads' eyes and middles agree. He faces -Y in his own file."""
    return eyes_point(rig) + Vector((0.0, EYE_OFFSET[0], -EYE_OFFSET[2]))


def preview_setup(scene, rig, sun_elevation_deg=6.857, round_deg=61.0, distance=0.808, lens=38.0, drop=0.055):
    """A plain look at him in the rest pose under the sill's light: the sky's own sun low and straight in front of his
    face, a camera where the Third-Person camera stands at the sill relative to his head (so many degrees round to his
    right, so far away, a little under the head's middle). For a first look only: the sill's own scene replaces it."""
    world = bpy.data.worlds.new("PreviewSky")
    world.use_nodes = True
    nt = world.node_tree
    bg = nt.nodes["Background"]
    sky = nt.nodes.new("ShaderNodeTexSky")
    for kind in ("MULTIPLE_SCATTERING", "NISHITA"):
        try:
            sky.sky_type = kind
            break
        except TypeError:
            continue
    sky.sun_elevation = math.radians(sun_elevation_deg)
    # he faces -Y; the sky's sun stands at this turn from +Y, so half a turn puts it before his face
    sky.sun_rotation = math.radians(180.0)
    nt.links.new(sky.outputs[0], bg.inputs[0])
    bg.inputs[1].default_value = 1.0
    scene.world = world
    c = head_centre(rig)
    fwd, right = Vector((0.0, -1.0, 0.0)), Vector((-1.0, 0.0, 0.0))
    a = math.radians(round_deg)
    pos = c + (fwd * math.cos(a) + right * math.sin(a)) * distance + Vector((0.0, 0.0, -drop))
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.lens = lens
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = pos
    cam.rotation_euler = (c - pos).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    # a floor and a wall behind him, so the light has something to come back from
    for nm, loc, rot in (("PreviewFloor", (0, 0, 0), (0, 0, 0)), ("PreviewWall", (0, 2.2, 1.5), (math.radians(90), 0, 0))):
        me = bpy.data.meshes.new(nm)
        s = 4.0
        me.from_pydata([(-s, -s, 0), (s, -s, 0), (s, s, 0), (-s, s, 0)], [], [(0, 1, 2, 3)])
        ob = bpy.data.objects.new(nm, me)
        ob.location, ob.rotation_euler = loc, rot
        scene.collection.objects.link(ob)
        m = bpy.data.materials.new(nm)
        m.use_nodes = True
        m.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.55, 0.5, 0.45, 1.0)
        me.materials.append(m)
    return cam

"""Materials for both engines, built from nodes.

Blender 5.2 gives every new material and world a node tree already (Principled BSDF
and Background), so nothing here touches the deprecated use_nodes flag.
"""
import bpy

# Sense colours from the concept, section 4.
GOLD = (1.0, 0.76, 0.22)      # sight
CYAN = (0.25, 0.85, 1.0)      # hearing, air
MAGENTA = (1.0, 0.25, 0.75)   # touch
ORANGE = (1.0, 0.5, 0.15)     # warmth
SALMON = (1.0, 0.45, 0.4)     # pain
MINT = (0.5, 1.0, 0.75)       # proprioception
LIME = (0.7, 1.0, 0.25)       # effort
VIOLET = (0.6, 0.35, 1.0)     # balance
GREY = (0.55, 0.55, 0.58)     # remembered
WHITE = (1.0, 1.0, 1.0)       # the self
# rung 2p (his specification of 2026-11-12): the senses on the simulated body
RADAR = (0.25, 1.0, 0.35)     # hearing: the rings and the ear a ring crosses, a radar's green
RED = (1.0, 0.12, 0.06)       # pain: the blend on a touched part, the ear at a loud sound, the eyes in the sun's glare
WARM_GOLD = (1.0, 0.8, 0.3)   # pleasure: the blend on a touched part, a sunlight warmth
COOL = (0.35, 0.55, 1.0)      # cold: the air at the window on the face
SUN_GOLD = (1.0, 0.72, 0.2)   # warmth on the skin the sun reaches (his word of 2026-11-13, eleventh round: warmth is a golden
                              # colour; ORANGE until then, which over skin read as red, pain's colour)
HEART_RED = (0.95, 0.12, 0.1) # the heart while thought of
LUNG_PINK = (1.0, 0.62, 0.6)  # the lungs while thought of


def _set(node, name, value):
    """Set a node input by name, or by index where names repeat (Math nodes call every input 'Value')."""
    if isinstance(name, int):
        sock = node.inputs[name] if name < len(node.inputs) else None
    else:
        sock = node.inputs.get(name)
    if sock is None:
        print(f"materials: {node.bl_idname} has no input '{name}', skipped", flush=True)
        return
    sock.default_value = value


def _rgba(c):
    return (c[0], c[1], c[2], 1.0)


def _clear(mat):
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    return nt, out


def principled(name, color, roughness=0.6, metallic=0.0, subsurface=0.0, specular=0.5):
    mat = bpy.data.materials.new(name)
    nt = mat.node_tree
    bsdf = next((n for n in nt.nodes if n.bl_idname == "ShaderNodeBsdfPrincipled"), None)
    if bsdf is None:
        nt, out = _clear(mat)
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    _set(bsdf, "Base Color", _rgba(color))
    _set(bsdf, "Roughness", roughness)
    _set(bsdf, "Metallic", metallic)
    _set(bsdf, "Specular IOR Level", specular)
    if subsurface > 0:
        _set(bsdf, "Subsurface Weight", subsurface)
        _set(bsdf, "Subsurface Radius", (1.0, 0.3, 0.15))
        _set(bsdf, "Subsurface Scale", 0.03)
    mat.diffuse_color = _rgba(color)
    return mat


def emission(name, color, strength=1.0, blended=False):
    """A surface lit evenly from within. blended=True makes EEVEE sort it as transparent."""
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    em = nt.nodes.new("ShaderNodeEmission")
    _set(em, "Color", _rgba(color))
    _set(em, "Strength", strength)
    nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    mat.diffuse_color = _rgba(color)
    if blended:
        mat.surface_render_method = "BLENDED"
    return mat


def emission_veil(name, color, strength, alpha):
    """An emissive face that lets most of what is behind it through: Mix(Transparent, Emission)."""
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    _set(em, "Color", _rgba(color))
    _set(em, "Strength", strength)
    mix = nt.nodes.new("ShaderNodeMixShader")
    _set(mix, "Fac", alpha)
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_backface_culling = False
    mat.diffuse_color = (color[0], color[1], color[2], alpha)
    return mat


def plate(name, color, strength, edge_gain=1.5, face_alpha=1.0):
    """Two materials for one plate of the model: its face and its edge line, the edge a shade brighter.

    face_alpha below 1 thins the face toward its edges, for a plate the model holds between the
    camera and the simulated body, which must never hide it (concept, section 4).
    """
    if face_alpha < 1.0:
        face = emission_veil(f"{name}.face", color, strength, face_alpha)
    else:
        face = emission(f"{name}.face", color, strength)
    edge = emission(f"{name}.edge", color, strength * edge_gain)
    return face, edge


def screen(name, color=(0.75, 0.85, 1.0), strength=8.0):
    return emission(name, color, strength)


def ghost_glass(name, edge_strength=1.6, fill=0.025, power=2.2, fade=None):
    """White glass that is nearly clear where it faces the camera and bright at its edges.

    Mix(Transparent, Emission) by fill + (1 - fill) * facing^power, where facing comes from
    a Layer Weight node: 0 head-on, 1 at the silhouette. Rendered with EEVEE's blended
    method so the model inside the skull shows through without dither noise. fade, a fade
    group, multiplies the mix factor by its Ghost output so a move can bring the ghost up
    from nothing or sink it (rung 2).
    """
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    _set(lw, "Blend", 0.5)
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    _set(pw, 1, power)
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    _set(mr, "From Min", 0.0)
    _set(mr, "From Max", 1.0)
    _set(mr, "To Min", fill)
    _set(mr, "To Max", 1.0)
    nt.links.new(pw.outputs["Value"], mr.inputs["Value"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    _set(em, "Color", _rgba(WHITE))
    _set(em, "Strength", edge_strength)
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(_fade_gain(nt, mr.outputs["Result"], fade, "Ghost"), mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat.use_backface_culling = False
    mat.diffuse_color = (1.0, 1.0, 1.0, 0.2)
    return mat


def soul_disc(name, radius, strength=6.0, rim=0.22, fade=None):
    """A soft white light: full across the disc, falling to clear over a narrow rim.

    The falloff reads the disc's own coordinates, so the disc object must have the
    circle centred on its origin with the given radius. fade, a fade group, multiplies
    the mix factor by its Soul output so a move can bring the light up or take it away.
    """
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    ln = nt.nodes.new("ShaderNodeVectorMath")
    ln.operation = "LENGTH"
    nt.links.new(tc.outputs["Object"], ln.inputs[0])
    # t = (radius - r) / (radius * rim), clamped and smoothed: 1 inside, 0 at the rim
    mr = nt.nodes.new("ShaderNodeMapRange")
    mr.interpolation_type = "SMOOTHSTEP"
    _set(mr, "From Min", radius)
    _set(mr, "From Max", radius * (1.0 - rim))
    _set(mr, "To Min", 0.0)
    _set(mr, "To Max", 1.0)
    nt.links.new(ln.outputs["Value"], mr.inputs["Value"])
    # brightness: a gentle rise toward the centre so it reads as a light, not a flat surface; times the
    # will (Will, a value keyed per frame: how willful he is this moment, his tenth review of 2026-11-10)
    cen = nt.nodes.new("ShaderNodeMapRange")
    _set(cen, "From Min", 0.0)
    _set(cen, "From Max", radius)
    _set(cen, "To Min", strength * 1.35)
    _set(cen, "To Max", strength * 0.85)
    nt.links.new(ln.outputs["Value"], cen.inputs["Value"])
    will = nt.nodes.new("ShaderNodeValue")
    will.name = "Will"
    will.label = "Will"
    will.outputs[0].default_value = 1.0
    willed = nt.nodes.new("ShaderNodeMath")
    willed.operation = "MULTIPLY"
    nt.links.new(cen.outputs["Result"], willed.inputs[0])
    nt.links.new(will.outputs[0], willed.inputs[1])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    _set(em, "Color", _rgba(WHITE))
    nt.links.new(willed.outputs["Value"], em.inputs["Strength"])
    # Near (a value keyed per frame, 1 by default) takes the disc itself away, clear and not black, for a
    # rendering camera within reach of it
    near = nt.nodes.new("ShaderNodeValue")
    near.name = "Near"
    near.label = "Near"
    near.outputs[0].default_value = 1.0
    present = nt.nodes.new("ShaderNodeMath")
    present.operation = "MULTIPLY"
    nt.links.new(_fade_gain(nt, mr.outputs["Result"], fade, "Soul"), present.inputs[0])
    nt.links.new(near.outputs[0], present.inputs[1])
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(present.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_backface_culling = False
    mat.diffuse_color = (1.0, 1.0, 1.0, 1.0)
    return mat


def glass_pane(name, ior=1.5, tint=(0.92, 0.96, 0.98)):
    """Window glass: a pane thin enough that its two faces bend nothing, so the view through it is
    the view, and it reflects by Fresnel alone, four percent straight on and more at a grazing
    angle, the same from either face (Mix(Transparent, Glossy) by Schlick's Fresnel from the angle
    alone). Cycles' own Fresnel and its Glass BSDF take the back face of a single quad for the far
    side of a block of glass, so beyond 42 degrees the pane reflected everything: the open leaf was
    a mirror (his eighth review of 2026-11-10). Shadow rays pass, so the sun comes in as if the
    pane were not there."""
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    _set(tr, "Color", (*tint, 1.0))
    gl = nt.nodes.new("ShaderNodeBsdfGlossy")
    _set(gl, "Color", (1.0, 1.0, 1.0, 1.0))
    _set(gl, "Roughness", 0.02)
    # Schlick: R = F0 + (1 - F0)(1 - cos)^5, with cos the angle between the ray and the face, either face
    f0 = ((ior - 1.0) / (ior + 1.0)) ** 2
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    cos = nt.nodes.new("ShaderNodeVectorMath")
    cos.operation = "DOT_PRODUCT"
    nt.links.new(geom.outputs["Normal"], cos.inputs[0])
    nt.links.new(geom.outputs["Incoming"], cos.inputs[1])
    cos_abs = nt.nodes.new("ShaderNodeMath")
    cos_abs.operation = "ABSOLUTE"
    nt.links.new(cos.outputs["Value"], cos_abs.inputs[0])
    one_minus = nt.nodes.new("ShaderNodeMath")
    one_minus.operation = "SUBTRACT"
    one_minus.inputs[0].default_value = 1.0
    nt.links.new(cos_abs.outputs["Value"], one_minus.inputs[1])
    fifth = nt.nodes.new("ShaderNodeMath")
    fifth.operation = "POWER"
    nt.links.new(one_minus.outputs["Value"], fifth.inputs[0])
    fifth.inputs[1].default_value = 5.0
    fr = nt.nodes.new("ShaderNodeMath")
    fr.operation = "MULTIPLY_ADD"
    nt.links.new(fifth.outputs["Value"], fr.inputs[0])
    fr.inputs[1].default_value = 1.0 - f0
    fr.inputs[2].default_value = f0
    pane = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(fr.outputs["Value"], pane.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], pane.inputs[1])
    nt.links.new(gl.outputs["BSDF"], pane.inputs[2])
    clear = nt.nodes.new("ShaderNodeBsdfTransparent")
    lp = nt.nodes.new("ShaderNodeLightPath")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(lp.outputs["Is Shadow Ray"], mix.inputs["Fac"])
    nt.links.new(pane.outputs["Shader"], mix.inputs[1])
    nt.links.new(clear.outputs["BSDF"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.diffuse_color = (0.8, 0.9, 1.0, 0.3)
    return mat


def clear(name):
    """A surface that is not there: a Transparent BSDF alone, for an object another pass needs."""
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    nt.links.new(tr.outputs["BSDF"], out.inputs["Surface"])
    return mat


def black_world(name="Dark"):
    world = bpy.data.worlds.new(name)
    bg = next(n for n in world.node_tree.nodes if n.bl_idname == "ShaderNodeBackground")
    _set(bg, "Color", (0.0, 0.0, 0.0, 1.0))
    _set(bg, "Strength", 0.0)
    return world


def sky_world(name, sun_elevation_deg, sun_azimuth_deg=0.0, sun_rotation_deg=None, intensity=1.0,
              aerosol=1.0, air=1.0, ozone=1.0, strength=1.0, model="MULTIPLE_SCATTERING"):
    """A physical sky. Azimuth is compass style from +x (east) toward +y (north).

    sun_rotation_deg is what the node's own rotation property is set to; when None it is
    derived as 90 - azimuth: the node's rotation runs from +y (north) toward +x (east), so
    east is +90. (It was -90 until 2026-11-08, which put the sun in the west: a panoramic
    render of the sky alone showed it at azimuth 179.) sun_direction is set to the same
    vector so the sun lands in one place whichever property the model reads.
    """
    import math
    world = bpy.data.worlds.new(name)
    nt = world.node_tree
    bg = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeBackground")
    sky = nt.nodes.new("ShaderNodeTexSky")
    try:
        sky.sky_type = model
    except TypeError:
        sky.sky_type = "SINGLE_SCATTERING"
    el = math.radians(sun_elevation_deg)
    az = math.radians(sun_azimuth_deg)
    sky.sun_elevation = el
    sky.sun_rotation = math.radians(sun_rotation_deg) if sun_rotation_deg is not None else (math.pi / 2 - az)
    try:
        sky.sun_direction = (math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el))
    except Exception as e:
        print("materials: sun_direction not set:", e, flush=True)
    sky.sun_intensity = intensity
    sky.sun_disc = True
    sky.aerosol_density = aerosol
    sky.air_density = air
    sky.ozone_density = ozone
    nt.links.new(sky.outputs["Color"], bg.inputs["Color"])
    _set(bg, "Strength", strength)
    world["sky_node"] = sky.name
    return world


# ---- the model's shading for rung 1: one node group, four materials, state on the objects ----

def model_group(name="TVModel", head_centre=(0.0, 0.0, 1.63), radii=(0.105, 0.0998, 0.126), glass=0.985,
                near_m=1.3, far_m=4.5, gone_m=9.0, model_scale=1.0 / 24.0, eye_lens=20.0, eye_sensor=36.0, eye_aspect=16.0 / 9.0):
    """A node group every model material shares. It reads the pixel's world position and gives:

    Clip:     1 inside the skull, 0 beyond the glass, so nothing of the model draws outside the head.
    FaceThin: 1 near the simulated body, 0 far from it, in room metres: a plate's face goes with distance.
    EdgeThin: the same for edges, which last farther before they go too.

    The simulated body's position arrives through three Value nodes (BodyX, BodyY, BodyZ) that the
    bake keyframes, so the thinning follows him without any Python at render time.
    """
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(name, "ShaderNodeTree")
    for out_name in ("Clip", "FaceThin", "EdgeThin", "Sight", "InFront"):
        ng.interface.new_socket(out_name, in_out="OUTPUT", socket_type="NodeSocketFloat")
    ng.interface.new_socket("ProjUV", in_out="OUTPUT", socket_type="NodeSocketVector")
    out = ng.nodes.new("NodeGroupOutput")
    geo = ng.nodes.new("ShaderNodeNewGeometry")
    # sight's attention this frame, keyframed by the bake: 0 with the eyes shut, so the seen picture goes
    sv = ng.nodes.new("ShaderNodeValue"); sv.name = "Sight"; sv.label = sv.name
    sv.outputs[0].default_value = 0.0
    ng.links.new(sv.outputs[0], out.inputs["Sight"])
    # the simulated eyes' camera, keyframed by the bake: its place (EyeX, EyeY, EyeZ) and the rows of
    # its world-to-camera rotation (Eye00 .. Eye22). Every pixel is projected into that camera's frame
    # here, so the First-Person picture lands exactly where those eyes would see it, whatever the
    # size of the face it lands on; a vertex-wise projection went wrong on any plate the eyes sat beside.
    def val(name, v=0.0):
        n = ng.nodes.new("ShaderNodeValue"); n.name = name; n.label = name
        n.outputs[0].default_value = v
        return n
    eye = ng.nodes.new("ShaderNodeCombineXYZ")
    for i, ax in enumerate("XYZ"):
        ng.links.new(val(f"Eye{ax}", head_centre[i]).outputs[0], eye.inputs[i])
    rel = ng.nodes.new("ShaderNodeVectorMath"); rel.operation = "SUBTRACT"
    ng.links.new(geo.outputs["Position"], rel.inputs[0])
    ng.links.new(eye.outputs["Vector"], rel.inputs[1])
    comps = []
    for r, default in enumerate(((0.0, -1.0, 0.0), (0.0, 0.0, 1.0), (-1.0, 0.0, 0.0))):
        row = ng.nodes.new("ShaderNodeCombineXYZ")
        for c in range(3):
            ng.links.new(val(f"Eye{r}{c}", default[c]).outputs[0], row.inputs[c])
        dot = ng.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
        ng.links.new(rel.outputs["Vector"], dot.inputs[0])
        ng.links.new(row.outputs["Vector"], dot.inputs[1])
        comps.append(dot)
    # camera space: x right, y up, the view down -z; depth = -z
    depth = ng.nodes.new("ShaderNodeMath"); depth.operation = "MULTIPLY"; _set(depth, 1, -1.0)
    ng.links.new(comps[2].outputs["Value"], depth.inputs[0])
    infront = ng.nodes.new("ShaderNodeMath"); infront.operation = "GREATER_THAN"; _set(infront, 1, 0.0004)
    ng.links.new(depth.outputs["Value"], infront.inputs[0])
    ng.links.new(infront.outputs["Value"], out.inputs["InFront"])
    safe = ng.nodes.new("ShaderNodeMath"); safe.operation = "MAXIMUM"; _set(safe, 1, 0.0004)
    ng.links.new(depth.outputs["Value"], safe.inputs[0])
    k_h = eye_lens / eye_sensor
    uv = []
    for i, k in enumerate((k_h, k_h * eye_aspect)):
        d = ng.nodes.new("ShaderNodeMath"); d.operation = "DIVIDE"
        ng.links.new(comps[i].outputs["Value"], d.inputs[0])
        ng.links.new(safe.outputs["Value"], d.inputs[1])
        m = ng.nodes.new("ShaderNodeMath"); m.operation = "MULTIPLY_ADD"; _set(m, 1, k); _set(m, 2, 0.5)
        ng.links.new(d.outputs["Value"], m.inputs[0])
        uv.append(m)
    puv = ng.nodes.new("ShaderNodeCombineXYZ")
    ng.links.new(uv[0].outputs["Value"], puv.inputs[0])
    ng.links.new(uv[1].outputs["Value"], puv.inputs[1])
    ng.links.new(puv.outputs["Vector"], out.inputs["ProjUV"])
    # skull test
    sub = ng.nodes.new("ShaderNodeVectorMath"); sub.operation = "SUBTRACT"
    _set(sub, 1, (head_centre[0], head_centre[1], head_centre[2]))
    ng.links.new(geo.outputs["Position"], sub.inputs[0])
    div = ng.nodes.new("ShaderNodeVectorMath"); div.operation = "DIVIDE"
    _set(div, 1, (radii[0] * glass, radii[1] * glass, radii[2] * glass))
    ng.links.new(sub.outputs["Vector"], div.inputs[0])
    ln = ng.nodes.new("ShaderNodeVectorMath"); ln.operation = "LENGTH"
    ng.links.new(div.outputs["Vector"], ln.inputs[0])
    clip = ng.nodes.new("ShaderNodeMapRange"); clip.interpolation_type = "SMOOTHSTEP"
    _set(clip, "From Min", 0.985); _set(clip, "From Max", 1.0); _set(clip, "To Min", 1.0); _set(clip, "To Max", 0.0)
    ng.links.new(ln.outputs["Value"], clip.inputs["Value"])
    ng.links.new(clip.outputs["Result"], out.inputs["Clip"])
    # distance from the simulated body
    vals = []
    for axis in ("X", "Y", "Z"):
        v = ng.nodes.new("ShaderNodeValue"); v.name = f"Body{axis}"; v.label = v.name
        v.outputs[0].default_value = head_centre["XYZ".index(axis)]
        vals.append(v)
    comb = ng.nodes.new("ShaderNodeCombineXYZ")
    for i, v in enumerate(vals):
        ng.links.new(v.outputs[0], comb.inputs[i])
    sub2 = ng.nodes.new("ShaderNodeVectorMath"); sub2.operation = "SUBTRACT"
    ng.links.new(geo.outputs["Position"], sub2.inputs[0])
    ng.links.new(comb.outputs["Vector"], sub2.inputs[1])
    ln2 = ng.nodes.new("ShaderNodeVectorMath"); ln2.operation = "LENGTH"
    ng.links.new(sub2.outputs["Vector"], ln2.inputs[0])
    # the model's scale in the skull is keyframed on this Value node (the mind's zoom, rung 2b), so
    # the thinning is measured in room metres at whatever scale the model holds
    ms = ng.nodes.new("ShaderNodeValue"); ms.name = "ModelScale"; ms.label = ms.name
    ms.outputs[0].default_value = model_scale
    room = ng.nodes.new("ShaderNodeMath"); room.operation = "DIVIDE"
    ng.links.new(ln2.outputs["Value"], room.inputs[0])
    ng.links.new(ms.outputs[0], room.inputs[1])
    face = ng.nodes.new("ShaderNodeMapRange"); face.interpolation_type = "SMOOTHSTEP"
    _set(face, "From Min", near_m); _set(face, "From Max", far_m); _set(face, "To Min", 1.0); _set(face, "To Max", 0.0)
    ng.links.new(room.outputs["Value"], face.inputs["Value"])
    ng.links.new(face.outputs["Result"], out.inputs["FaceThin"])
    edge = ng.nodes.new("ShaderNodeMapRange"); edge.interpolation_type = "SMOOTHSTEP"
    _set(edge, "From Min", far_m); _set(edge, "From Max", gone_m); _set(edge, "To Min", 1.0); _set(edge, "To Max", 0.0)
    ng.links.new(room.outputs["Value"], edge.inputs["Value"])
    ng.links.new(edge.outputs["Result"], out.inputs["EdgeThin"])
    return ng


def model_material(name, gain, thin="none", clip=True, group=None, extra_prop=None, fade=None,
                   project=None, memory_gain=1.0, seen_gain=1.0):
    """The memory look: an additive light whose colour and attention come from the object's own
    properties "col" and "att" (the Attribute node in Object mode), times gain, times the group's
    factors. thin: "none", "face" or "edge". extra_prop: another float property multiplied in
    ("face" for a plate's veil, "edge" for its edge gain). fade: a fade group whose Model output
    multiplies the strength, so a move can bring the whole model up or sink it.

    project: (image, uv_map_name, frame_count) adds the seen look (his review of 2026-11-07): the
    First-Person picture, an image sequence, projected through the UV map a UV Project modifier
    writes from the simulated eyes, shown wherever the surface is both inside that picture's frame
    (the image clips outside it) and lit by the spot light at the eyes, whose shadows are the
    occlusion, times the group's Sight; everywhere else the memory look stands. From the
    simulated eyes the seen part is the First-Person view itself."""
    group = group or model_group()
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_type = "OBJECT"; att.attribute_name = "att"
    col = nt.nodes.new("ShaderNodeAttribute"); col.attribute_type = "OBJECT"; col.attribute_name = "col"
    grp = nt.nodes.new("ShaderNodeGroup"); grp.node_tree = group
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    nt.links.new(att.outputs["Fac"], m1.inputs[0])
    nt.links.new(grp.outputs["Clip"] if clip else att.outputs["Fac"], m1.inputs[1])
    if not clip:
        _set(m1, 1, 1.0)
        nt.links.new(att.outputs["Fac"], m1.inputs[0])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; _set(m2, 1, gain * memory_gain)
    nt.links.new(m1.outputs["Value"], m2.inputs[0])
    last = m2
    if thin in ("face", "edge"):
        m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"
        nt.links.new(last.outputs["Value"], m3.inputs[0])
        nt.links.new(grp.outputs["FaceThin" if thin == "face" else "EdgeThin"], m3.inputs[1])
        last = m3
    if extra_prop:
        ex = nt.nodes.new("ShaderNodeAttribute"); ex.attribute_type = "OBJECT"; ex.attribute_name = extra_prop
        m4 = nt.nodes.new("ShaderNodeMath"); m4.operation = "MULTIPLY"
        nt.links.new(last.outputs["Value"], m4.inputs[0])
        nt.links.new(ex.outputs["Fac"], m4.inputs[1])
        last = m4
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(col.outputs["Color"], em.inputs["Color"])
    nt.links.new(_fade_gain(nt, last.outputs["Value"], fade, "Model"), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs["BSDF"], add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    if project is None:
        nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    else:
        image, uv_name, frame_count = project
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = image
        tex.interpolation = "Linear"
        tex.extension = "CLIP"
        tex.image_user.frame_duration = int(frame_count)
        tex.image_user.frame_start = 1
        tex.image_user.frame_offset = 0
        tex.image_user.use_auto_refresh = True
        nt.links.new(grp.outputs["ProjUV"], tex.inputs["Vector"])
        # lit by the spot at the eyes: the only lamp in the dark, so a white diffuse reads it alone
        dif = nt.nodes.new("ShaderNodeBsdfDiffuse"); _set(dif, "Color", (1.0, 1.0, 1.0, 1.0))
        s2c = nt.nodes.new("ShaderNodeShaderToRGB")
        nt.links.new(dif.outputs["BSDF"], s2c.inputs["Shader"])
        bw = nt.nodes.new("ShaderNodeRGBToBW")
        nt.links.new(s2c.outputs["Color"], bw.inputs["Color"])
        lit = nt.nodes.new("ShaderNodeMapRange"); lit.interpolation_type = "SMOOTHSTEP"
        _set(lit, "From Min", 0.004); _set(lit, "From Max", 0.03); _set(lit, "To Min", 0.0); _set(lit, "To Max", 1.0)
        nt.links.new(bw.outputs["Val"], lit.inputs["Value"])
        s0 = nt.nodes.new("ShaderNodeMath"); s0.operation = "MULTIPLY"
        nt.links.new(tex.outputs["Alpha"], s0.inputs[0])
        nt.links.new(grp.outputs["InFront"], s0.inputs[1])
        s1 = nt.nodes.new("ShaderNodeMath"); s1.operation = "MULTIPLY"
        nt.links.new(lit.outputs["Result"], s1.inputs[0])
        nt.links.new(s0.outputs["Value"], s1.inputs[1])
        # sight on at all: the seen picture stands where the eyes reach; its brightness carries the attention
        on = nt.nodes.new("ShaderNodeMapRange"); on.interpolation_type = "SMOOTHSTEP"
        _set(on, "From Min", 0.0); _set(on, "From Max", 0.08); _set(on, "To Min", 0.0); _set(on, "To Max", 1.0)
        nt.links.new(grp.outputs["Sight"], on.inputs["Value"])
        s2 = nt.nodes.new("ShaderNodeMath"); s2.operation = "MULTIPLY"
        nt.links.new(s1.outputs["Value"], s2.inputs[0])
        nt.links.new(on.outputs["Result"], s2.inputs[1])
        s3 = nt.nodes.new("ShaderNodeMath"); s3.operation = "MULTIPLY"
        nt.links.new(s2.outputs["Value"], s3.inputs[0])
        nt.links.new(grp.outputs["Clip"], s3.inputs[1])
        seen = _fade_gain(nt, s3.outputs["Value"], fade, "Model")
        # the seen picture: the eye's own frame, from a third of its brightness at the least attention to all of it
        se = nt.nodes.new("ShaderNodeEmission")
        nt.links.new(tex.outputs["Color"], se.inputs["Color"])
        br = nt.nodes.new("ShaderNodeMapRange")
        _set(br, "From Min", 0.0); _set(br, "From Max", 1.0); _set(br, "To Min", 0.35 * seen_gain); _set(br, "To Max", 1.0 * seen_gain)
        nt.links.new(grp.outputs["Sight"], br.inputs["Value"])
        nt.links.new(br.outputs["Result"], se.inputs["Strength"])
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(seen, mix.inputs["Fac"])
        nt.links.new(add.outputs["Shader"], mix.inputs[1])
        nt.links.new(se.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat.use_backface_culling = False
    mat.diffuse_color = (0.6, 0.6, 0.6, 0.5)
    return mat


SIGHT_PATH = 'nodes["Sight"].outputs[0].default_value'
EYE_PATHS = {n: f'nodes["{n}"].outputs[0].default_value' for n in ["EyeX", "EyeY", "EyeZ"] + [f"Eye{r}{c}" for r in range(3) for c in range(3)]}


def wave_material(name, colour, gain, fade=None, waves=5.0, speed=2.5):
    """The gravity arrow's shaft: an additive light in one colour whose strength runs as a wave
    along the object's length (its generated Y, 0 at the tail, 1 at the tip) toward the tip, the
    time read from a Value node named T that the bake keyframes with the scene's seconds. The
    object's "att" property is the sense's attention, as on every model material."""
    mat = bpy.data.materials.new(name)
    nt, out = _clear(mat)
    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_type = "OBJECT"; att.attribute_name = "att"
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Generated"], sep.inputs[0])
    tv = nt.nodes.new("ShaderNodeValue"); tv.name = "T"; tv.label = "T"
    tv.outputs[0].default_value = 0.0
    m_v = nt.nodes.new("ShaderNodeMath"); m_v.operation = "MULTIPLY"; _set(m_v, 1, waves * 6.2831853)
    nt.links.new(sep.outputs["Y"], m_v.inputs[0])
    m_t = nt.nodes.new("ShaderNodeMath"); m_t.operation = "MULTIPLY"; _set(m_t, 1, speed * 6.2831853)
    nt.links.new(tv.outputs[0], m_t.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"
    nt.links.new(m_v.outputs["Value"], sub.inputs[0])
    nt.links.new(m_t.outputs["Value"], sub.inputs[1])
    sn = nt.nodes.new("ShaderNodeMath"); sn.operation = "SINE"
    nt.links.new(sub.outputs["Value"], sn.inputs[0])
    # 0.45 + 0.55 * (0.5 + 0.5 sin): the wave never goes dark, only dims
    mr = nt.nodes.new("ShaderNodeMapRange")
    _set(mr, "From Min", -1.0); _set(mr, "From Max", 1.0); _set(mr, "To Min", 0.45); _set(mr, "To Max", 1.0)
    nt.links.new(sn.outputs["Value"], mr.inputs["Value"])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    nt.links.new(att.outputs["Fac"], m1.inputs[0])
    nt.links.new(mr.outputs["Result"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"; _set(m2, 1, gain)
    nt.links.new(m1.outputs["Value"], m2.inputs[0])
    em = nt.nodes.new("ShaderNodeEmission")
    _set(em, "Color", _rgba(colour))
    nt.links.new(_fade_gain(nt, m2.outputs["Value"], fade, "Model"), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs["BSDF"], add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat.use_backface_culling = False
    mat.diffuse_color = (colour[0], colour[1], colour[2], 0.6)
    return mat


WAVE_T_PATH = 'nodes["T"].outputs[0].default_value'
MODEL_SCALE_PATH = 'nodes["ModelScale"].outputs[0].default_value'


# ---- rung 2: fades for the moves between the room and the dark ----------------------

def fade_group(name="TVFade"):
    """One node group with three Value nodes, Model, Ghost and Soul, each an output. Every
    material of the True scene multiplies by the one it needs, so keyframing the three
    values (on the group's own node tree) brings the model, the ghost and the soul up from
    nothing or sinks them during a move. They stay at 1 in the piece."""
    ng = bpy.data.node_groups.get(name)
    if ng is not None:
        return ng
    ng = bpy.data.node_groups.new(name, "ShaderNodeTree")
    out = ng.nodes.new("NodeGroupOutput")
    for i, n in enumerate(("Model", "Ghost", "Soul")):
        ng.interface.new_socket(n, in_out="OUTPUT", socket_type="NodeSocketFloat")
        v = ng.nodes.new("ShaderNodeValue")
        v.name = n
        v.label = n
        v.outputs[0].default_value = 1.0
        v.location = (-200, -120 * i)
        ng.links.new(v.outputs[0], out.inputs[n])
    return ng


def _fade_gain(nt, socket, fade, output_name):
    """socket times the fade group's output, or socket itself when there is no fade group."""
    if fade is None:
        return socket
    grp = nt.nodes.new("ShaderNodeGroup")
    grp.node_tree = fade
    m = nt.nodes.new("ShaderNodeMath")
    m.operation = "MULTIPLY"
    nt.links.new(socket, m.inputs[0])
    nt.links.new(grp.outputs[output_name], m.inputs[1])
    return m.outputs["Value"]


DRAIN_PATH = 'nodes["Drain"].outputs[0].default_value'


def _surface_link(nt):
    out = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeOutputMaterial")
    link = out.inputs["Surface"].links[0]
    src = link.from_socket
    nt.links.remove(link)
    return out, src


def add_drain(mat):
    """Mix the material's surface toward black by a Value node named Drain (0 the material as
    it was, 1 black), for the room going dark from the walls inward. Returns the Value node;
    its keyframes go on the material's node tree at DRAIN_PATH."""
    nt = mat.node_tree
    out, src = _surface_link(nt)
    black = nt.nodes.new("ShaderNodeEmission")
    _set(black, "Color", (0.0, 0.0, 0.0, 1.0))
    _set(black, "Strength", 0.0)
    v = nt.nodes.new("ShaderNodeValue")
    v.name = "Drain"
    v.label = "Drain"
    v.outputs[0].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(v.outputs[0], mix.inputs["Fac"])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(black.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return v


def add_glass_drain(mat, edge_strength=0.9, fill=0.02, power=3.0):
    """Mix the material's surface toward white glass, the ghost's look, by a Value node named
    Drain (0 the material as it was, 1 glass): the body draining to the ghost in a move."""
    nt = mat.node_tree
    out, src = _surface_link(nt)
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    _set(lw, "Blend", 0.5)
    pw = nt.nodes.new("ShaderNodeMath")
    pw.operation = "POWER"
    _set(pw, 1, power)
    nt.links.new(lw.outputs["Facing"], pw.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange")
    _set(mr, "From Min", 0.0)
    _set(mr, "From Max", 1.0)
    _set(mr, "To Min", fill)
    _set(mr, "To Max", 1.0)
    nt.links.new(pw.outputs["Value"], mr.inputs["Value"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    em = nt.nodes.new("ShaderNodeEmission")
    _set(em, "Color", _rgba(WHITE))
    _set(em, "Strength", edge_strength)
    glass = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mr.outputs["Result"], glass.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], glass.inputs[1])
    nt.links.new(em.outputs["Emission"], glass.inputs[2])
    v = nt.nodes.new("ShaderNodeValue")
    v.name = "Drain"
    v.label = "Drain"
    v.outputs[0].default_value = 0.0
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(v.outputs[0], mix.inputs["Fac"])
    nt.links.new(src, mix.inputs[1])
    nt.links.new(glass.outputs["Shader"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    return v

"""The True-Person scene for rung 1: the art that draws what the engine says.

A still white glass figure in the dark, the soul above its head, and inside the skull
the model: plates for every region the mind can hold, the simulated body, and pools of
primitives for the signals (waves, discs, comets, rivers, fields, the gravity arrow,
breath, heart, pain, warmth, the ridge and the sun, words). Every object's state comes
from custom properties "att" and "col" the shared materials read, and from baked
transforms, so the render runs from plain keyframes.

Static plates are built once in room metres under the ModelFrame empty, whose baked
matrix is the head-frame transform, scale included (the mind's zoom, rung 2b); everything
that moves is baked in ghost space, and the glyphs on the body are scaled with the zoom
so they keep their proportion to it. The fan of rays is no longer drawn (his review of
2026-11-07): sight shows as the surfaces it reaches coming up in their own colours.
"""
import math

import bpy
from mathutils import Matrix, Vector

from . import anim, body, cameras, engine, figure, geo, materials as mats, render, tags
import struct
import zlib
import pathlib

N_RIDGE = 36
N_GROUND = 4


def ridge_profile_of(spec):
    """(y, top) of the ridge as room.ridge_profile builds it; kept here so mindscene need not import room."""
    ys = [-600 + 10 * i for i in range(121)]
    tops = [max(1.5, 7.0 + 4.0 * math.sin(y / 41.0) + 2.5 * math.sin(y / 13.0 + 1.3) + 1.2 * math.sin(y / 5.1 + 2.1)) for y in ys]
    return list(zip(ys, tops))


def _props(obj, att=0.0, col=(0.55, 0.55, 0.58), **more):
    obj["att"] = float(att)
    obj["col"] = [float(c) for c in col]
    for k, v in more.items():
        obj[k] = float(v)


def _segment_mesh(name, radius, segments=8):
    bm = geo.new_bmesh()
    import bmesh
    m = Matrix.Translation((0, 0.5, 0)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    bmesh.ops.create_cone(bm, cap_ends=False, cap_tris=False, segments=segments, radius1=radius, radius2=radius,
                          depth=1.0, matrix=m)
    for f in bm.faces:
        f.smooth = True
    return bm


def _cone(name, radius, length, mat, col, segments=10):
    """A cone along local +y from its base at the origin to its tip at y = length."""
    bm = geo.new_bmesh()
    import bmesh
    m = Matrix.Translation((0, length * 0.5, 0)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=True, segments=segments, radius1=radius, radius2=0.0,
                          depth=length, matrix=m)
    for f in bm.faces:
        f.smooth = True
    return geo.finish(bm, name, [mat], col)


def _placeholder_png(path):
    """An 8 by 8 black PNG, for the First-Person sequence before its frames exist."""
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + bytes(24) for _ in range(8))
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", 8, 8, 8, 2, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(png)
    return path


def first_sequence(first_dir, frame_count, placeholder_dir):
    """The First-Person frames as an image sequence named FirstView. When the frames are not there
    yet the sequence points at a placeholder; the render repoints it (rungs/rung2.py)."""
    first = pathlib.Path(first_dir) / "frame_0001.png"
    if not first.exists():
        first = _placeholder_png(pathlib.Path(placeholder_dir) / "frame_0001.png")
    img = bpy.data.images.load(str(first), check_existing=False)
    img.name = "FirstView"
    img.source = "SEQUENCE"
    return img


def _project_from_eyes(obj, projector, uv_name="SimEye"):
    """A UV map the simulated eyes' camera writes every frame, after the object's other modifiers."""
    if obj.type != "MESH":
        return
    if uv_name not in obj.data.uv_layers:
        obj.data.uv_layers.new(name=uv_name)
    mod = obj.modifiers.new("SimEye", "UV_PROJECT")
    mod.uv_layer = uv_name
    mod.projector_count = 1
    mod.projectors[0].object = projector
    mod.aspect_x = 16.0
    mod.aspect_y = 9.0


def _sphere(name, radius, mat, col, scale=(1, 1, 1), segments=12):
    bm = geo.new_bmesh()
    geo.add_sphere(bm, (0, 0, 0), radius, 0, scale=scale, segments=segments, rings=max(6, segments // 2))
    return geo.finish(bm, name, [mat], col)


def _disc(name, radius, mat, col, segments=48):
    bm = geo.new_bmesh()
    geo.add_disc(bm, (0, 0, 0), radius, 0, segments=segments)
    return geo.finish(bm, name, [mat], col)


def _annulus(name, mat, col, inner=0.85, segments=64, thin=0.96):
    """A flat ring of unit outer radius with a shape key that thins it (inner radius thin)."""
    bm = geo.new_bmesh()
    outer = [bm.verts.new((math.cos(2 * math.pi * i / segments), math.sin(2 * math.pi * i / segments), 0.0)) for i in range(segments)]
    inner_v = [bm.verts.new((inner * math.cos(2 * math.pi * i / segments), inner * math.sin(2 * math.pi * i / segments), 0.0)) for i in range(segments)]
    for i in range(segments):
        j = (i + 1) % segments
        f = bm.faces.new((outer[i], outer[j], inner_v[j], inner_v[i]))
        f.material_index = 0
    obj = geo.finish(bm, name, [mat], col)
    # rim: 1 at the ring's outer edge, 0 at its inner, for a material that glows from the edge inward (rung 2p)
    rim = obj.data.attributes.new("rim", "FLOAT", "POINT")
    for i in range(segments):
        rim.data[i].value = 1.0
        rim.data[segments + i].value = 0.0
    obj.shape_key_add(name="Basis")
    key = obj.shape_key_add(name="thin")
    for i in range(segments):
        v = key.data[segments + i]
        v.co = Vector((thin * math.cos(2 * math.pi * i / segments), thin * math.sin(2 * math.pi * i / segments), 0.0))
    return obj


class TrueScene:
    def __init__(self, name, room_spec, fps=24, eevee_samples=32, bloom=True, draw_rays=False,
                 first_dir=None, frame_count=1, placeholder_dir=None, render_fps=None):
        self.spec = room_spec
        self.fps = fps
        self.draw_rays = draw_rays
        # the seen look: the First-Person frames projected from the simulated eyes (his review of 2026-11-07)
        self.project = None
        if first_dir is not None:
            img = first_sequence(first_dir, frame_count, placeholder_dir or (pathlib.Path(first_dir).parent / "placeholder"))
            self.project = (img, "SimEye", frame_count)
        scene = bpy.data.scenes.new(name)
        self.scene = scene
        scene.render.fps = int(round(render_fps or fps))
        col = scene.collection
        self.col = col
        scene.world = mats.black_world("Dark")
        render.setup_eevee(scene, samples=eevee_samples)
        self.group = mats.model_group(head_centre=tuple(engine.HEAD_CENTRE), radii=tuple(engine.SKULL_RADII),
                                      model_scale=engine.MODEL_SCALE)
        # the fades a move keyframes (model, ghost, soul); 1 throughout the piece
        self.fade = mats.fade_group()
        fd = self.fade
        self.m_face = mats.model_material("PlateFace", 0.9, thin="face", clip=True, group=self.group, extra_prop="face", fade=fd, project=self.project)
        self.m_edge = mats.model_material("PlateEdge", 1.5, thin="edge", clip=True, group=self.group, extra_prop="edge", fade=fd, project=self.project)
        self.m_body = mats.model_material("SimBody", 1.3, thin="none", clip=True, group=self.group, fade=fd, project=self.project)
        self.m_far = mats.model_material("FarSeen", 1.0, thin="none", clip=True, group=self.group, fade=fd, project=self.project, memory_gain=0.0)
        # the window's opening is never painted: what is seen through it lies on the far geometry
        self.m_face_plain = mats.model_material("PlateFacePlain", 0.9, thin="face", clip=True, group=self.group, extra_prop="face", fade=fd)
        self.m_edge_plain = mats.model_material("PlateEdgePlain", 1.5, thin="edge", clip=True, group=self.group, extra_prop="edge", fade=fd)
        self.m_light = mats.model_material("Light", 2.6, thin="none", clip=False, group=self.group, fade=fd)
        self.m_soft = mats.model_material("SoftLight", 1.6, thin="none", clip=False, group=self.group, fade=fd)

        # the simulated eyes: a camera that projects the First-Person picture onto the model, and a spot
        # light at the same place whose light with its shadows says what those eyes can see
        self.sim_eye_cam = geo.add_camera("Cam_SimEye", (0.0, 0.0, 1.63), (1.0, 0.0, 1.63), lens=cameras.FIRST_LENS, clip_start=0.001, collection=col)
        self.sim_eye_cam.rotation_mode = "QUATERNION"
        ld = bpy.data.lights.new("SimEyeLight", "SPOT")
        ld.energy = 300.0
        ld.spot_size = math.radians(100.0)
        ld.spot_blend = 0.0
        ld.use_shadow = True
        ld.shadow_soft_size = 0.0
        for attr, val in (("shadow_buffer_clip_start", 0.0005), ("shadow_maximum_resolution", 0.0002), ("use_shadow_jitter", False)):
            try:
                setattr(ld, attr, val)
            except Exception as e:
                print("mindscene: light setting skipped:", attr, e, flush=True)
        self.sim_eye_light = bpy.data.objects.new("SimEyeLight", ld)
        col.objects.link(self.sim_eye_light)
        self.sim_eye_light.rotation_mode = "QUATERNION"
        # camera on its road, tracking an aim empty
        self.cam = geo.add_camera("Cam_True", (4.0, 0.0, 1.15), (0.0, 0.0, 1.05), lens=24.0, clip_start=0.02, collection=col)
        self.aim = geo.add_empty("Cam_True_Aim", (0.0, 0.0, 1.05), 1.0, col)
        geo.track_to(self.cam, self.aim, "TRACK_NEGATIVE_Z", "UP_Y")
        scene.camera = self.cam

        # the ghost and the soul
        self.glass = mats.ghost_glass("GhostGlass", edge_strength=0.45, fill=0.01, power=3.5, fade=self.fade)
        pose = figure.standing()
        place = figure.placement((0.0, 0.0, 0.0), 0.0)
        self.ghost, self.ghost_head, gp = figure.build("Ghost", pose, {"skin": self.glass, "cloth": self.glass}, place, col, segments=24)
        crown = figure.crown(pose, place)
        bm = geo.new_bmesh()
        geo.add_disc(bm, (0, 0, 0), 0.045, 0, segments=96)
        self.soul = geo.finish(bm, "Soul", [mats.soul_disc("Soul", 0.045, 6.0, fade=self.fade)], col)
        self.soul.location = tuple(engine.SOUL_POS)
        geo.track_to(self.soul, self.cam, "TRACK_Z", "UP_Y")

        # the model frame and the plates
        self.frame = geo.add_empty("ModelFrame", tuple(engine.HEAD_CENTRE), engine.MODEL_SCALE, col)
        self.frame.rotation_mode = "QUATERNION"
        self.plates = {}
        self.plate_centroids = {}
        self._build_plates()

        # the simulated body
        self.sim = body.build_figure("Sim", col, {"skin": self.m_body, "cloth": self.m_body}, radius_scale=engine.MODEL_SCALE,
                                     segments=10, empty_size=0.005)
        for obj, part in self.sim["prims"]:
            _props(obj, 0.0, mats.GREY)
        self.sim_head = self.sim["head"]
        # the far geometry the eyes can reach when the model zooms out: the ground and the ridge as built
        self.far = []
        if self.project is not None:
            W = self.spec.size[0]
            R = self.spec.ridge_distance
            prof = ridge_profile_of(self.spec)
            bm = geo.new_bmesh()
            geo.add_quad(bm, (W, -600, -0.3), (R * 6, -600, -0.3), (R * 6, 600, -0.3), (W, 600, -0.3), 0)
            g = geo.finish(bm, "Far_ground", [self.m_far], col, self.frame)
            bm = geo.new_bmesh()
            geo.add_ridge(bm, R, [p[0] for p in prof], [p[1] for p in prof], -80.0, 0)
            r = geo.finish(bm, "Far_ridge", [self.m_far], col, self.frame)
            for o in (g, r):
                _props(o, 1.0, mats.GREY)
                self.far.append(o)
            # the dome: the skull's inner surface, just inside the glass, where the eyes' picture lands for
            # everything the eyes see beyond the skull's reach (the concept: what the mind holds beyond
            # the skull's reach is drawn at the glass), so that from the simulated eyes the picture is whole
            self.m_dome = mats.model_material("DomeSeen", 1.0, thin="none", clip=False, group=self.group, fade=fd, project=self.project, memory_gain=0.0)
            rad = engine.SKULL_RADII * 0.95
            self.dome = _sphere("Dome", 1.0, self.m_dome, col, scale=(rad.x, rad.y, rad.z), segments=48)
            self.dome.location = engine.HEAD_CENTRE
            _props(self.dome, 1.0, mats.GREY)

        # pools
        self.rays = []
        if draw_rays:
            for k in range(engine.RAY_COUNT):
                i, j = divmod(k, engine.RAY_COLS)
                central = abs(i - (engine.RAY_ROWS - 1) / 2) < 1 and abs(j - (engine.RAY_COLS - 1) / 2) < 2.5
                bm = _segment_mesh(f"Ray{k}", 0.0016 if central else 0.0012)
                o = geo.finish(bm, f"Ray_{k:02d}", [self.m_light], col)
                o.rotation_mode = "QUATERNION"
                _props(o, 0.0, mats.GOLD)
                self.rays.append(o)
        self.waves = []
        for k in range(engine.WAVE_SLOTS):
            o = _annulus(f"Wave_{k:02d}", self.m_soft, col)
            geo.track_to(o, self.cam, "TRACK_Z", "UP_Y")
            _props(o, 0.0, mats.CYAN)
            self.waves.append(o)
        self.discs = []
        for k in range(engine.DISC_SLOTS):
            o = _disc(f"SoundDisc_{k}", 1.0, self.m_soft, col)
            geo.track_to(o, self.cam, "TRACK_Z", "UP_Y")
            _props(o, 0.0, mats.CYAN)
            self.discs.append(o)
        self.pulses = {}
        self.flashes = {}
        for chain in tags.CHAINS:
            self.pulses[chain] = []
            for k in range(engine.PULSES_PER_CHAIN):
                o = _sphere(f"Pulse_{chain}_{k}", 0.0035, self.m_light, col)
                _props(o, 0.0, mats.MAGENTA)
                self.pulses[chain].append(o)
            o = _sphere(f"Flash_{chain}", 0.005, self.m_light, col)
            _props(o, 0.0, mats.MAGENTA)
            self.flashes[chain] = o
        self.rivers = {}
        for chain, joints in tags.CHAINS.items():
            segs = []
            for a, b in zip(joints, joints[1:]):
                bm = _segment_mesh(f"River_{chain}_{a}", 0.0011)
                o = geo.finish(bm, f"River_{chain}_{a}_{b}", [self.m_light], col)
                c1 = o.constraints.new("COPY_LOCATION"); c1.target = self.sim["empties"][a]
                c2 = o.constraints.new("STRETCH_TO"); c2.target = self.sim["empties"][b]; c2.rest_length = 1.0; c2.volume = "NO_VOLUME"
                _props(o, 0.0, mats.MINT)
                segs.append(o)
            self.rivers[chain] = segs
        self.fields = {}
        for part, spec in tags.PARTS.items():
            r = max((figure.JOINTS[j][0] for j in spec["joints"] if j in figure.JOINTS), default=0.08)
            if part == "head":
                r = figure.HEAD_RADIUS * 0.75
            o = _sphere(f"Field_{part}", r * 1.45 * engine.MODEL_SCALE, self.m_soft, col)
            _props(o, 0.0, mats.ORANGE)
            self.fields[part] = o
        o = _sphere("Field_head_edge", figure.HEAD_RADIUS * 0.5 * engine.MODEL_SCALE, self.m_soft, col)
        _props(o, 0.0, tags.SENSE_COLOUR["airflow"])
        self.fields["head_edge"] = o
        self.throb = _sphere("PainThrob", 0.0045, self.m_light, col)
        _props(self.throb, 0.0, mats.SALMON)
        self.breath = _sphere("Breath", 0.0075, self.m_soft, col, scale=(1.0, 1.3, 1.1))
        _props(self.breath, 0.0, mats.WHITE)
        self.heart = _sphere("Heart", 0.0025, self.m_light, col)
        _props(self.heart, 0.0, mats.WHITE)
        self.glow = _disc("SoulGlow", 0.0035, self.m_light, col)
        geo.track_to(self.glow, self.cam, "TRACK_Z", "UP_Y")
        _props(self.glow, 0.0, mats.WHITE)
        # the gravity arrow: a shaft whose light runs as a wave toward the tip, and the tip
        self.m_wave = mats.wave_material("GravityWave", mats.VIOLET, 2.4, fade=fd)
        bm = _segment_mesh("GravityShaft", 0.0013)
        self.plumb = geo.finish(bm, "GravityArrow", [self.m_wave], col)
        self.plumb.rotation_mode = "QUATERNION"
        _props(self.plumb, 0.0, mats.VIOLET)
        self.plumb_tip = _cone("GravityTip", 0.0042, 0.009, self.m_light, col)
        self.plumb_tip.rotation_mode = "QUATERNION"
        _props(self.plumb_tip, 0.0, mats.VIOLET)
        self.warmth = []
        for k in range(engine.WARMTH_SLOTS):
            bm = _segment_mesh(f"Warmth{k}", 0.001)
            o = geo.finish(bm, f"WarmthRay_{k}", [self.m_light], col)
            o.rotation_mode = "QUATERNION"
            _props(o, 0.0, mats.ORANGE)
            self.warmth.append(o)
        self.sun = _disc("SunDisc", 0.006, self.m_light, col)
        geo.track_to(self.sun, self.cam, "TRACK_Z", "UP_Y")
        _props(self.sun, 0.0, mats.GOLD)
        self.ridge = []
        for k in range(N_RIDGE):
            bm = _segment_mesh(f"Ridge{k}", 0.0009)
            o = geo.finish(bm, f"Ridge_{k:02d}", [self.m_light], col)
            o.rotation_mode = "QUATERNION"
            _props(o, 0.0, mats.GREY)
            self.ridge.append(o)
        self.ground = []
        for k in range(N_GROUND):
            bm = _segment_mesh(f"Ground{k}", 0.0008)
            o = geo.finish(bm, f"Ground_{k}", [self.m_light], col)
            o.rotation_mode = "QUATERNION"
            _props(o, 0.0, mats.GREY)
            self.ground.append(o)

        # words of recognition: one loose column to the left of the simulated head, inside the skull
        self.words = {}
        hc = engine.HEAD_CENTRE
        self.word_anchor = geo.add_empty("WordAnchor", tuple(hc), 1.0, col)

        # the will's words: one text object per word on the timeline, lit white, dropping in
        self.will_words = []
        self.bloom = render.bloom_compositor(scene, 1.0, 0.35, 0.6) if bloom else None
        # only the model's surfaces and the simulated limbs stand in the eyes' light: the simulated head
        # wraps the eye point and would shadow everything, and the glyphs are lights, not things
        for o in col.objects:
            casts = o.name.startswith(("Model_", "Far_", "SimJ_", "SimL_"))
            try:
                o.visible_shadow = casts
            except AttributeError:
                pass

    def add_words(self, words, will):
        col = self.col
        hc = engine.HEAD_CENTRE
        size = 0.0105
        for k, w in enumerate(words):
            x = hc.x + (0.012 if k % 2 else -0.008) + (0.006 if k % 3 == 2 else 0.0)
            y = hc.y + 0.062
            z = hc.z + 0.058 - k * size * 1.18
            t = geo.add_text(f"Word_{k}_{w}", w, size, (x, y, z), self.m_light, col, align="LEFT")
            geo.track_to(t, self.cam, "TRACK_Z", "UP_Y")
            _props(t, 0.07, mats.GREY)
            self.words.setdefault(w, []).append(t)
        for i, w in enumerate(will):
            t = geo.add_text(f"Will_{i}_{w['word']}", w["word"], 0.014, (hc.x, hc.y, hc.z + 0.3), self.m_light, col, align="CENTER")
            geo.track_to(t, self.cam, "TRACK_Z", "UP_Y")
            _props(t, 0.0, mats.WHITE)
            t.hide_render = True
            self.will_words.append(t)

    # ---- plates ----
    def _plate(self, tag, bm, centroid=None, parent=True):
        plain = tag == "window"
        obj = geo.finish(bm, f"Model_{tag}", [self.m_face_plain if plain else self.m_face, self.m_edge_plain if plain else self.m_edge], self.col, self.frame if parent else None)
        wf = obj.modifiers.new("Edge", "WIREFRAME")
        wf.thickness = 0.028
        wf.use_replace = False
        wf.use_boundary = True
        wf.use_even_offset = True
        wf.material_offset = 1
        _props(obj, 0.0, mats.GREY, face=(0.12 if plain else 1.0), edge=1.0)
        self.plates[tag] = obj
        if centroid is not None:
            self.plate_centroids[tag] = Vector(centroid)
        return obj

    def _build_plates(self):
        sp = self.spec
        W, D, H = sp.size
        wy0, wy1, wz0, wz1 = sp.window
        q = geo.add_quad
        bm = geo.new_bmesh(); q(bm, (0, 0, 0), (W, 0, 0), (W, D, 0), (0, D, 0)); self._plate("floor", bm, (W / 2, D / 2, 0))
        bm = geo.new_bmesh(); q(bm, (0, 0, H), (0, D, H), (W, D, H), (W, 0, H)); self._plate("ceiling", bm, (W / 2, D / 2, H))
        bm = geo.new_bmesh(); q(bm, (0, 0, 0), (0, D, 0), (0, D, H), (0, 0, H)); self._plate("wall_w", bm, (0, D / 2, H / 2))
        bm = geo.new_bmesh(); q(bm, (0, 0, 0), (0, 0, H), (W, 0, H), (W, 0, 0)); self._plate("wall_s", bm, (W / 2, 0, H / 2))
        bm = geo.new_bmesh(); q(bm, (0, D, 0), (W, D, 0), (W, D, H), (0, D, H)); self._plate("wall_n", bm, (W / 2, D, H / 2))
        bm = geo.new_bmesh(); geo.add_rect_with_hole(bm, "x", W, 0, D, 0, H, wy0, wy1, wz0, wz1, 0); self._plate("wall_e", bm, (W, D / 2, H / 2))
        bm = geo.new_bmesh(); q(bm, (W, wy0, wz0), (W, wy1, wz0), (W, wy1, wz1), (W, wy0, wz1)); self._plate("window", bm, (W, (wy0 + wy1) / 2, (wz0 + wz1) / 2))
        bm = geo.new_bmesh(); geo.add_box(bm, (W - 0.07, wy0 - 0.07, wz0 - 0.08), (W + 0.1, wy1 + 0.07, wz0 - 0.05)); self._plate("sill", bm, (W, (wy0 + wy1) / 2, wz0 - 0.06))
        (bx0, by0, bz0), (bx1, by1, bz1) = sp.bed
        bm = geo.new_bmesh(); geo.add_box(bm, (bx0, by0, bz0), (bx1, by1, bz1)); self._plate("bed", bm, ((bx0 + bx1) / 2, (by0 + by1) / 2, bz1))
        (tx0, ty0, tz0), (tx1, ty1, tz1) = sp.table
        bm = geo.new_bmesh()
        geo.add_box(bm, (tx0, ty0, tz1 - 0.03), (tx1 - 0.01, ty1, tz1))
        leg = 0.04
        for lx in (tx0 + 0.02, tx1 - 0.02 - leg):
            for ly in (ty0 + 0.02, ty1 - 0.02 - leg):
                geo.add_box(bm, (lx, ly, tz0), (lx + leg, ly + leg, tz1 - 0.03))
        self._plate("table", bm, ((tx0 + tx1) / 2, (ty0 + ty1) / 2, tz1))
        bm = geo.new_bmesh(); q(bm, (tx1, ty0, tz0), (tx1, ty1, tz0), (tx1, ty1, tz1), (tx1, ty0, tz1)); self._plate("table_far", bm, (tx1, (ty0 + ty1) / 2, tz1 / 2))
        bm = geo.new_bmesh(); q(bm, (tx0, ty1 + 0.004, tz1 - 0.03), (tx1, ty1 + 0.004, tz1 - 0.03), (tx1, ty1 + 0.004, tz1 + 0.004), (tx0, ty1 + 0.004, tz1 + 0.004)); self._plate("table_edge", bm, ((tx0 + tx1) / 2, ty1, tz1))
        rx0, rx1, ry0, ry1 = sp.rug
        L, Hc = sp.rug_curl_length, sp.rug_curl_height
        bm = geo.new_bmesh(); q(bm, (rx0 + L, ry0, 0.002), (rx1, ry0, 0.002), (rx1, ry1, 0.002), (rx0 + L, ry1, 0.002)); self._plate("rug", bm, ((rx0 + rx1) / 2, (ry0 + ry1) / 2, 0))
        bm = geo.new_bmesh(); q(bm, (rx0, ry0, 0.002), (rx0 + L, ry0, 0.002), (rx0 + L, ry1, 0.002), (rx0, ry1, 0.002)); self._plate("rug_edge", bm, (rx0 + L / 2, (ry0 + ry1) / 2, 0))

        def curl(u, v):
            x = rx0 + L * u
            d = x - rx0
            tt = 1.0 - d / L
            return (x + 0.5 * Hc * tt * tt, ry0 + (ry1 - ry0) * v, Hc * tt * tt)
        bm = geo.new_bmesh(); geo.add_grid(bm, 6, 1, curl, 0, smooth=False); self._plate("rug_edge_curled", bm, (rx0 + L / 2, (ry0 + ry1) / 2, Hc / 2))
        L_, W_, T_ = sp.phone_size
        bm = geo.new_bmesh(); geo.add_box(bm, (-L_ / 2, -W_ / 2, -T_ / 2), (L_ / 2, W_ / 2, T_ / 2)); self._plate("phone", bm, None, parent=False)
        self.plates["phone"].rotation_mode = "QUATERNION"

    # ---- baking ----
    def bake(self, states, baker):
        sw = anim.Sparse(baker)
        veil = {tag: 1.0 for tag in self.plate_centroids}
        glass_em = next(n for n in self.glass.node_tree.nodes if n.bl_idname == "ShaderNodeEmission")
        glass_path = f'nodes["{glass_em.name}"].inputs[{glass_em.inputs.find("Strength")}].default_value'
        body_paths = {ax: f'nodes["Body{ax}"].outputs[0].default_value' for ax in "XYZ"}
        fade_paths = {n: f'nodes["{n}"].outputs[0].default_value' for n in ("Model", "Ghost", "Soul")}
        hc = engine.HEAD_CENTRE
        W, D, H = self.spec.size
        limbs = [o for o, part in self.sim["prims"] if o.name.startswith("SimL_")]
        rounds = [o for o, part in self.sim["prims"] if not o.name.startswith("SimL_")]
        for fs in states:
            f = fs.frame
            # the mind's zoom: the model frame carries the scale; the glyphs on the body are scaled
            # with it so they keep their proportion to the simulated body
            k = fs.scale / engine.MODEL_SCALE
            sw.set(self.group, mats.MODEL_SCALE_PATH, 0, f, fs.scale)
            sw.set(self.m_wave.node_tree, mats.WAVE_T_PATH, 0, f, fs.t)
            # the simulated eyes: where the First-Person camera is, in the model
            sw.set(self.group, mats.SIGHT_PATH, 0, f, fs.sight_att)
            eye_pos = fs.M @ Vector(fs.eye_room)
            eye_q = (fs.M.to_3x3().normalized() @ fs.head_rot @ cameras.CAM_FROM_HEAD).to_quaternion()
            for o in (self.sim_eye_cam, self.sim_eye_light):
                baker.set_vec(o, "location", f, eye_pos)
                baker.set_vec(o, "rotation_quaternion", f, eye_q)
            # the same camera inside the model's node group, for the projection per pixel
            R_wc = eye_q.to_matrix().transposed()
            for i, ax in enumerate("XYZ"):
                sw.set(self.group, mats.EYE_PATHS[f"Eye{ax}"], 0, f, eye_pos[i])
            for r in range(3):
                for c in range(3):
                    sw.set(self.group, mats.EYE_PATHS[f"Eye{r}{c}"], 0, f, R_wc[r][c])
            for o in rounds:
                sw.set_vec(o, "scale", f, (k, k, k))
            for o in limbs:
                sw.set(o, "scale", 0, f, k)
                sw.set(o, "scale", 2, f, k)
            # the fades of a move (rung 2); a FrameState without them is the piece, at 1
            sw.set(self.fade, fade_paths["Model"], 0, f, getattr(fs, "fade_model", 1.0))
            sw.set(self.fade, fade_paths["Ghost"], 0, f, getattr(fs, "fade_ghost", 1.0))
            sw.set(self.fade, fade_paths["Soul"], 0, f, getattr(fs, "fade_soul", 1.0))
            loc, rot, sc = fs.M.decompose()
            baker.set_vec(self.frame, "location", f, loc)
            baker.set_vec(self.frame, "rotation_quaternion", f, rot)
            baker.set_vec(self.frame, "scale", f, sc)   # exactly every frame, as the location: a sparse scale slid the model off the eyes between keys
            pos, aim, lens = fs.camera
            baker.set_vec(self.cam, "location", f, pos)
            baker.set_vec(self.aim, "location", f, aim)
            sw.set(self.cam.data, "lens", 0, f, lens)
            # close to the head the glass layers pile up, so the ghost is eased down with the camera's distance
            dist = (pos - hc).length
            sw.set(self.glass.node_tree, glass_path, 0, f, fs.ghost * (0.4 + 0.6 * anim.smoothstep((dist - 1.5) / 2.5)))
            centre = fs.sim_joints["pelvis"].lerp(fs.sim_joints["chest"], 0.5)
            for ax, v in zip("XYZ", centre):
                sw.set(self.group, body_paths[ax], 0, f, v)
            # the soft glyphs on the body are large close up: they dim as the camera comes within the
            # skull's reach (the reveal), and are whole from where the True road keeps the camera
            near = anim.smoothstep((dist - 0.08) / 0.4)
            # the camera's place in the model's own room metres: inside the room during the reveal
            c_room = fs.M.inverted() @ Vector(pos)
            inside_room = (-0.2 < c_room.x < W + 0.2) and (-0.2 < c_room.y < D + 0.2) and (-0.2 < c_room.z < H + 0.2)
            planes = {"floor": c_room.z, "ceiling": H - c_room.z, "wall_w": c_room.x, "wall_e": W - c_room.x,
                      "wall_s": c_room.y, "wall_n": D - c_room.y}
            # plates
            for tag, obj in self.plates.items():
                key = "rug_edge" if tag == "rug_edge_curled" else tag
                r = fs.regions.get(key)
                if r is None:
                    continue
                att = r["att"]
                if tag == "rug_edge" and fs.rug_curled:
                    att = 0.0
                if tag == "rug_edge_curled" and not fs.rug_curled:
                    att = 0.0
                if tag == "phone":
                    if fs.phone is None:
                        att = 0.0
                    else:
                        pl, pr, ps = fs.phone.decompose()
                        baker.set_vec(obj, "location", f, pl)
                        baker.set_vec(obj, "rotation_quaternion", f, pr)
                        sw.set_vec(obj, "scale", f, ps)
                sw.set_prop(obj, "att", f, att)
                sw.set_prop(obj, "col", f, r["col"])
                # a plate the camera is about to pass through fades out as it comes (the reveal)
                cross = 1.0
                if tag in planes:
                    cross = anim.smoothstep(abs(planes[tag]) / 0.35)
                sw.set_prop(obj, "edge", f, (1.0 - 0.75 * r["soft"]) * cross * (0.35 if tag == "window" else 1.0))
                if tag in self.plate_centroids:
                    P = fs.M @ self.plate_centroids[tag]
                    cb = pos - hc
                    pb = P - hc
                    along = pb.dot(cb) / max(cb.length, 1e-6)
                    perp = (pb - cb.normalized() * along).length
                    # the veil thins a plate held between the camera and the body, from outside the skull only
                    target = 0.15 if (along > 0.005 and perp < 0.09 and not inside_room) else 1.0
                    veil[tag] += (target - veil[tag]) * 0.18
                    sw.set_prop(obj, "face", f, (0.12 if tag == "window" else veil[tag] * (1.0 - 0.15 * r["soft"])) * cross)
            # the simulated body
            for name, e in self.sim["empties"].items():
                baker.set_vec(e, "location", f, fs.sim_joints[name])
            for obj, part in self.sim["prims"]:
                p = fs.parts[part]
                sw.set_prop(obj, "att", f, p["att"])
                sw.set_prop(obj, "col", f, p["col"])
            # rays
            for o, (a, b, att) in zip(self.rays, fs.rays):
                if att > 1e-4:
                    loc, q, L = anim.segment_transform(a, b)
                    baker.set_vec(o, "location", f, loc)
                    baker.set_vec(o, "rotation_quaternion", f, q)
                    baker.set(o, "scale", 1, f, L)
                sw.set_prop(o, "att", f, att)
            # waves and discs
            for o, (c, r, s, att) in zip(self.waves, fs.waves):
                if att > 1e-4:
                    baker.set_vec(o, "location", f, c)
                    baker.set_vec(o, "scale", f, (r, r, r))
                    baker.set(o.data.shape_keys, 'key_blocks["thin"].value', 0, f, 1.0 - min(1.0, s))
                sw.set_prop(o, "att", f, att * (0.5 + 0.5 * s))
            for o, (c, r, att) in zip(self.discs, fs.discs):
                if att > 1e-4:
                    baker.set_vec(o, "location", f, c)
                    sw.set_vec(o, "scale", f, (r, r, r))
                sw.set_prop(o, "att", f, att)
            # comets: pulses and flashes
            for chain, objs in self.pulses.items():
                lst = fs.pulses.get(chain, [])
                flash_att, flash_col = 0.0, mats.MAGENTA
                for kk, o in enumerate(objs):
                    if kk < len(lst):
                        p, att, colr, fl = lst[kk]
                        if att > 1e-4:
                            baker.set_vec(o, "location", f, p)
                            sw.set_vec(o, "scale", f, (k, k, k))
                        sw.set_prop(o, "att", f, att * near)
                        sw.set_prop(o, "col", f, colr)
                        if fl > flash_att:
                            flash_att, flash_col = fl, colr
                    else:
                        sw.set_prop(o, "att", f, 0.0)
                fo = self.flashes[chain]
                if flash_att > 1e-4:
                    baker.set_vec(fo, "location", f, hc - Vector((0.004, 0.0, -0.001)))
                sw.set_prop(fo, "att", f, flash_att * near)
                sw.set_prop(fo, "col", f, flash_col)
            # rivers
            for chain, segs in self.rivers.items():
                rv = fs.rivers.get(chain)
                for o in segs:
                    if rv is None:
                        sw.set_prop(o, "att", f, 0.0)
                    else:
                        colr, width, att = rv
                        sw.set_prop(o, "att", f, att)
                        sw.set_prop(o, "col", f, colr)
                        w = (0.6 + 1.6 * width) * k
                        sw.set(o, "scale", 0, f, w)
                        sw.set(o, "scale", 2, f, w)
            # fields
            for slot, o in self.fields.items():
                fd = fs.fields.get(slot)
                if fd is None:
                    sw.set_prop(o, "att", f, 0.0)
                    continue
                p, colr, spread, att = fd
                baker.set_vec(o, "location", f, p)
                s = (0.55 + 0.9 * spread) * k
                sw.set_vec(o, "scale", f, (s, s, s))
                sw.set_prop(o, "att", f, att * near)
                sw.set_prop(o, "col", f, colr)
            # pain, breath, heart, glow
            p, s, att = fs.throb
            if att > 1e-4:
                baker.set_vec(self.throb, "location", f, p)
                baker.set_vec(self.throb, "scale", f, (s * k, s * k, s * k))
            sw.set_prop(self.throb, "att", f, att * near)
            chest = fs.sim_joints["chest"]
            s, att = fs.breath
            if att > 1e-4:
                baker.set_vec(self.breath, "location", f, chest + Vector((0.002, 0.0, 0.001)) * k)
                baker.set_vec(self.breath, "scale", f, (s * k, s * k, s * k))
            sw.set_prop(self.breath, "att", f, att * near)
            s, att = fs.heart
            if att > 1e-4:
                baker.set_vec(self.heart, "location", f, chest + Vector((0.0025, 0.0015, 0.002)) * k)
                baker.set_vec(self.heart, "scale", f, (s * k, s * k, s * k))
            sw.set_prop(self.heart, "att", f, att * near)
            gpos = fs.sim_joints["pelvis"].lerp(chest, 0.55)
            baker.set_vec(self.glow, "location", f, gpos)
            sw.set_vec(self.glow, "scale", f, (k, k, k))
            sw.set_prop(self.glow, "att", f, fs.glow * near)
            # the gravity arrow: the shaft from the inner ear toward down, the tip at its end
            a, b, att = fs.plumb
            if att > 1e-4:
                tip_len = 0.009
                d = (b - a)
                L = d.length
                if L > tip_len + 1e-4:
                    loc, q, Ls = anim.segment_transform(a, b - d * (tip_len / L))
                    baker.set_vec(self.plumb, "location", f, loc)
                    baker.set_vec(self.plumb, "rotation_quaternion", f, q)
                    baker.set(self.plumb, "scale", 1, f, Ls)
                    baker.set_vec(self.plumb_tip, "location", f, b - d * (tip_len / L))
                    baker.set_vec(self.plumb_tip, "rotation_quaternion", f, q)
            sw.set_prop(self.plumb, "att", f, att)
            sw.set_prop(self.plumb_tip, "att", f, att)
            # warmth and the sun
            for o, (a, b, att) in zip(self.warmth, fs.warmth):
                if att > 1e-4:
                    loc, q, L = anim.segment_transform(a, b)
                    baker.set_vec(o, "location", f, loc)
                    baker.set_vec(o, "rotation_quaternion", f, q)
                    baker.set(o, "scale", 1, f, L)
                sw.set_prop(o, "att", f, att)
            p, att, colr = fs.sun
            if att > 1e-4:
                baker.set_vec(self.sun, "location", f, p)
            sw.set_prop(self.sun, "att", f, att)
            sw.set_prop(self.sun, "col", f, colr)
            # the ridge and the ground at the glass
            att, colr = fs.ridge_att
            pts = fs.ridge
            for k, o in enumerate(self.ridge):
                if att > 1e-4 and k + 1 < len(pts):
                    loc, q, L = anim.segment_transform(pts[k], pts[k + 1])
                    baker.set_vec(o, "location", f, loc)
                    baker.set_vec(o, "rotation_quaternion", f, q)
                    baker.set(o, "scale", 1, f, L)
                    sw.set_prop(o, "att", f, att)
                    sw.set_prop(o, "col", f, colr)
                else:
                    sw.set_prop(o, "att", f, 0.0)
            att, colr = fs.ground_att
            g = fs.ground
            for k, o in enumerate(self.ground):
                if att > 1e-4 and len(g) == 4:
                    loc, q, L = anim.segment_transform(g[k], g[(k + 1) % 4])
                    baker.set_vec(o, "location", f, loc)
                    baker.set_vec(o, "rotation_quaternion", f, q)
                    baker.set(o, "scale", 1, f, L)
                    sw.set_prop(o, "att", f, att)
                    sw.set_prop(o, "col", f, colr)
                else:
                    sw.set_prop(o, "att", f, 0.0)
            # words
            for w, objs in self.words.items():
                lit = fs.words.get(w, 0.0)
                for o in objs:
                    sw.set_prop(o, "att", f, 0.07 * fs.awareness * fs.budget_scale + 1.0 * lit)
                    c = [anim.lerp(g, 1.0, lit) for g in mats.GREY]
                    sw.set_prop(o, "col", f, c)
            live = {i: (p, att) for i, p, att in fs.will}
            for i, o in enumerate(self.will_words):
                if i in live:
                    p, att = live[i]
                    baker.set_vec(o, "location", f, p)
                    sw.set_prop(o, "att", f, att)
                    sw.set(o, "hide_render", 0, f, 0.0, anim.CONSTANT)
                else:
                    sw.set_prop(o, "att", f, 0.0)
                    sw.set(o, "hide_render", 0, f, 1.0, anim.CONSTANT)
        sw.finish()

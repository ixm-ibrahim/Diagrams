"""Keyframe baking in bulk, and small motion helpers.

Blender 5.2 actions are slotted: an action holds slots, layers and strips, and the
F-curves of an ID live in the channelbag of its slot (there is no Action.fcurves any
more). The Baker collects samples per ID and data path while the engine runs, then
writes every F-curve at once with foreach_set, which is thousands of times faster than
keyframe_insert per frame and leaves the file with plain keyframes that render without
any Python.
"""
import math

import bpy
import numpy as np
from mathutils import Matrix, Quaternion, Vector

LINEAR, CONSTANT, BEZIER = 1, 0, 2   # keyframe interpolation enum values, verified by running

_ID_TYPE = {
    bpy.types.Object: "OBJECT", bpy.types.Material: "MATERIAL", bpy.types.World: "WORLD",
    bpy.types.Camera: "CAMERA", bpy.types.Light: "LIGHT", bpy.types.Scene: "SCENE",
    bpy.types.Mesh: "MESH", bpy.types.Curve: "CURVE", bpy.types.TextCurve: "CURVE",
    bpy.types.Key: "KEY",
}


def id_type_of(idblock):
    for cls, name in _ID_TYPE.items():
        if isinstance(idblock, cls):
            return name
    if isinstance(idblock, bpy.types.NodeTree):
        return "NODETREE"
    return "OBJECT"


def ensure_channelbag(idblock, name=None):
    """Return the channelbag that holds idblock's F-curves, creating action, slot, layer and strip."""
    adt = idblock.animation_data or idblock.animation_data_create()
    act = adt.action
    if act is None:
        act = bpy.data.actions.new(name or f"{idblock.name}Action")
        adt.action = act
    if not act.slots:
        slot = act.slots.new(id_type_of(idblock), idblock.name)
    else:
        slot = act.slots[0]
    if adt.action_slot is None:
        adt.action_slot = slot
    if not act.layers:
        layer = act.layers.new("Layer")
    else:
        layer = act.layers[0]
    if not layer.strips:
        strip = layer.strips.new(type="KEYFRAME")
    else:
        strip = layer.strips[0]
    return strip.channelbag(adt.action_slot, ensure=True)


class Baker:
    """Collects (frame, value) samples and writes them as F-curves in one pass.

    set(idblock, data_path, index, frame, value) records one sample. Samples for one
    curve must arrive in increasing frame order. write() creates the F-curves.
    """

    def __init__(self):
        self.tracks = {}      # id(idblock) -> (idblock, {(path, index): ([frames], [values], interp)})

    def set(self, idblock, data_path, index, frame, value, interp=LINEAR):
        key = idblock.as_pointer()
        entry = self.tracks.get(key)
        if entry is None:
            entry = (idblock, {})
            self.tracks[key] = entry
        curve = entry[1].get((data_path, index))
        if curve is None:
            curve = ([], [], interp)
            entry[1][(data_path, index)] = curve
        curve[0].append(float(frame))
        curve[1].append(float(value))

    def set_vec(self, idblock, data_path, frame, values, interp=LINEAR):
        for i, v in enumerate(values):
            self.set(idblock, data_path, i, frame, v, interp)

    def set_prop(self, obj, name, frame, value, interp=LINEAR):
        """A custom property: a float, or a sequence for an array property."""
        if isinstance(value, (int, float)):
            self.set(obj, f'["{name}"]', 0, frame, value, interp)
        else:
            for i, v in enumerate(value):
                self.set(obj, f'["{name}"]', i, frame, v, interp)

    def count(self):
        return sum(len(c[0]) for _, curves in self.tracks.values() for c in curves.values())

    def write(self):
        written = 0
        for idblock, curves in self.tracks.values():
            cb = ensure_channelbag(idblock)
            for (path, index), (frames, values, interp) in curves.items():
                fc = cb.fcurves.find(path, index=index)
                if fc is None:
                    fc = cb.fcurves.new(path, index=index)
                n = len(frames)
                existing = len(fc.keyframe_points)
                fc.keyframe_points.add(n)
                if existing:
                    # keep any earlier points by rewriting the whole curve in order
                    old = np.empty(existing * 2, dtype=np.float32)
                    fc.keyframe_points.foreach_get("co", old)
                co = np.empty((existing + n) * 2, dtype=np.float32)
                if existing:
                    co[: existing * 2] = old
                co[existing * 2::2] = frames
                co[existing * 2 + 1::2] = values
                fc.keyframe_points.foreach_set("co", co)
                ipo = np.full(existing + n, interp, dtype=np.int32)
                fc.keyframe_points.foreach_set("interpolation", ipo)
                fc.update()
                written += n
        return written


# ---- motion helpers -------------------------------------------------------------

def smoothstep(u):
    u = 0.0 if u < 0.0 else 1.0 if u > 1.0 else u
    return u * u * (3.0 - 2.0 * u)


def lerp(a, b, u):
    return a + (b - a) * u


def frame_of(t, fps=24, first=1):
    return int(round(t * fps)) + first


def time_of(frame, fps=24, first=1):
    return (frame - first) / fps


def segment_transform(a, b):
    """Location, rotation and length that put a unit +Y segment from a to b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    length = d.length
    if length < 1e-9:
        return a, Quaternion((1.0, 0.0, 0.0, 0.0)), 0.0
    q = Vector((0.0, 1.0, 0.0)).rotation_difference(d / length)
    return a, q, length


def frame_from_axes(forward, up):
    """A rotation whose local x is forward and local z is up (y = up x forward), orthonormalised."""
    f = Vector(forward).normalized()
    u = Vector(up)
    u = (u - f * u.dot(f)).normalized()
    l = u.cross(f).normalized()
    m = Matrix((f, l, u)).transposed()  # columns f, l, u
    return m.to_4x4()


class Sparse:
    """Writes a value only when it changes, holding the previous value up to the frame before,
    so a curve stays exact at every frame with keys only where something happens."""

    def __init__(self, baker, eps=1e-3):
        self.b = baker
        self.eps = eps
        self.last = {}     # key -> [idblock, last seen frame, last value, last written frame, interp]

    def set(self, idblock, path, index, frame, value, interp=LINEAR):
        key = (idblock.as_pointer(), path, index)
        value = float(value)
        last = self.last.get(key)
        if last is None:
            self.b.set(idblock, path, index, frame, value, interp)
            self.last[key] = [idblock, frame, value, frame, interp]
            return
        _, lf, lv, lw, _ = last
        if abs(value - lv) <= self.eps:
            last[1] = frame
            return
        if lw < frame - 1:
            self.b.set(idblock, path, index, frame - 1, lv, interp)
        self.b.set(idblock, path, index, frame, value, interp)
        last[1], last[2], last[3] = frame, value, frame

    def set_vec(self, idblock, path, frame, values, interp=LINEAR):
        for i, v in enumerate(values):
            self.set(idblock, path, i, frame, v, interp)

    def set_prop(self, obj, name, frame, value, interp=LINEAR):
        if isinstance(value, (int, float)):
            self.set(obj, f'["{name}"]', 0, frame, value, interp)
        else:
            for i, v in enumerate(value):
                self.set(obj, f'["{name}"]', i, frame, v, interp)

    def finish(self):
        for key, (idblock, lf, lv, lw, interp) in self.last.items():
            if lw < lf:
                self.b.set(idblock, key[1], key[2], lf, lv, interp)

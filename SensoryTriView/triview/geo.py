"""Mesh construction helpers built on bmesh.

Headless Blender refuses edit-mode operators unless the view layer has an active
object, so every shape here is made in a bmesh and written to a mesh datablock.
All functions take and return plain tuples or mathutils Vectors in metres.
"""
import math

import bpy
import bmesh
from mathutils import Matrix, Vector

UP = Vector((0.0, 0.0, 1.0))


def _new_faces(bm, n0=None):
    """The faces made since the last call: every face is tagged once it has been handed out, so the new
    ones are the untagged. The slice bm.faces[n0:] is not them: a create op fills the slots its own
    temporaries freed, so the sphere added after a cone took fourteen of the cone's places in the table
    and the cone's faces moved past them (the stand-in trees had fourteen bark facets on their crowns
    and green trunks from rung 2e to his eleventh review, 2026-11-11)."""
    bm.faces.ensure_lookup_table()
    new = [f for f in bm.faces if not f.tag]
    for f in new:
        f.tag = True
    return new


def add_sphere(bm, center, radius, mat_index=0, scale=(1.0, 1.0, 1.0), segments=24, rings=16):
    """A UV sphere at center. scale stretches it along its own axes (heads are taller than wide)."""
    n0 = len(bm.faces)
    m = Matrix.Translation(Vector(center)) @ Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
    bmesh.ops.create_uvsphere(bm, u_segments=segments, v_segments=rings, radius=radius, matrix=m)
    for f in _new_faces(bm, n0):
        f.material_index = mat_index
        f.smooth = True


def add_segment(bm, a, b, r1, r2=None, mat_index=0, segments=16, caps=False):
    """A cylinder (or cone) from point a to point b, radius r1 at a and r2 at b."""
    a, b = Vector(a), Vector(b)
    d = b - a
    length = d.length
    if length < 1e-6:
        return
    if r2 is None:
        r2 = r1
    rot = UP.rotation_difference(d.normalized()).to_matrix().to_4x4()
    m = Matrix.Translation((a + b) * 0.5) @ rot
    n0 = len(bm.faces)
    bmesh.ops.create_cone(bm, cap_ends=caps, cap_tris=False, segments=segments,
                          radius1=r1, radius2=r2, depth=length, matrix=m)
    axis = d.normalized()
    for f in _new_faces(bm, n0):
        f.material_index = mat_index
        f.normal_update()
        # caps are the faces whose normal runs along the segment; sides are smooth
        f.smooth = abs(f.normal.dot(axis)) < 0.9


def add_box(bm, lo, hi, mat_index=0, matrix=None, top_mat_index=None):
    """An axis-aligned box from corner lo to corner hi, optionally transformed by matrix.

    top_mat_index, when given, is used for the face whose normal points up in the box's
    own frame before the transform (a phone's screen, a table's top).
    """
    lo, hi = Vector(lo), Vector(hi)
    size = hi - lo
    m = Matrix.Translation((lo + hi) * 0.5) @ Matrix.Diagonal((size.x, size.y, size.z, 1.0))
    n0 = len(bm.faces)
    bmesh.ops.create_cube(bm, size=1.0, matrix=m)
    faces = _new_faces(bm, n0)
    bm.normal_update()
    for f in faces:
        f.smooth = False
        f.material_index = mat_index
        if top_mat_index is not None and f.normal.z > 0.5:
            f.material_index = top_mat_index
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=list({v for f in faces for v in f.verts}))


def add_quad(bm, p0, p1, p2, p3, mat_index=0):
    """One flat quad through four points in order."""
    vs = [bm.verts.new(Vector(p)) for p in (p0, p1, p2, p3)]
    f = bm.faces.new(vs)
    f.material_index = mat_index
    f.tag = True
    f.smooth = False
    return f


def add_rect_with_hole(bm, axis, at, u0, u1, v0, v1, hu0, hu1, hv0, hv1, mat_index=0):
    """A rectangle in the plane perpendicular to axis ('x', 'y' or 'z') at coordinate at,
    spanning u0..u1 and v0..v1 in the other two axes (in alphabetical order), with a
    rectangular hole hu0..hu1, hv0..hv1 cut out of it, built as four quads."""
    def pt(u, v):
        if axis == "x":
            return (at, u, v)
        if axis == "y":
            return (u, at, v)
        return (u, v, at)
    # below the hole, above the hole, left strip, right strip (strips span only the hole's height)
    rects = [
        (u0, u1, v0, hv0),
        (u0, u1, hv1, v1),
        (u0, hu0, hv0, hv1),
        (hu1, u1, hv0, hv1),
    ]
    for a0, a1, b0, b1 in rects:
        if a1 - a0 > 1e-6 and b1 - b0 > 1e-6:
            add_quad(bm, pt(a0, b0), pt(a1, b0), pt(a1, b1), pt(a0, b1), mat_index)


def add_grid(bm, nu, nv, point, mat_index=0, smooth=True):
    """A grid of nu by nv quads; point(u, v) with u, v in 0..1 returns the vertex position."""
    verts = [[bm.verts.new(Vector(point(i / nu, j / nv))) for j in range(nv + 1)] for i in range(nu + 1)]
    for i in range(nu):
        for j in range(nv):
            f = bm.faces.new((verts[i][j], verts[i + 1][j], verts[i + 1][j + 1], verts[i][j + 1]))
            f.material_index = mat_index
            f.tag = True
            f.smooth = smooth


def add_ridge(bm, x, ys, tops, bottom, mat_index=0):
    """A vertical wall at x running along y with a jagged top: a mountain silhouette."""
    top = [bm.verts.new((x, y, h)) for y, h in zip(ys, tops)]
    bot = [bm.verts.new((x, y, bottom)) for y in ys]
    for i in range(len(ys) - 1):
        f = bm.faces.new((bot[i], bot[i + 1], top[i + 1], top[i]))
        f.material_index = mat_index
        f.tag = True
        f.smooth = False


def add_disc(bm, center, radius, mat_index=0, segments=64):
    """A flat filled circle in the XY plane at center."""
    n0 = len(bm.faces)
    m = Matrix.Translation(Vector(center))
    bmesh.ops.create_circle(bm, cap_ends=True, cap_tris=False, segments=segments, radius=radius, matrix=m)
    for f in _new_faces(bm, n0):
        f.material_index = mat_index
        f.smooth = False


def finish(bm, name, materials=(), collection=None, parent=None, sharp_angle=50.0, matrix=None):
    """Write the bmesh to a new mesh object. Edges between smooth faces that meet at more
    than sharp_angle degrees are marked sharp, which 4.1+ honours without auto smooth."""
    if matrix is not None:
        bmesh.ops.transform(bm, matrix=matrix, verts=list(bm.verts))
    bm.normal_update()
    cos_t = math.cos(math.radians(sharp_angle))
    for e in bm.edges:
        lf = e.link_faces
        if len(lf) == 2 and lf[0].smooth and lf[1].smooth and lf[0].normal.dot(lf[1].normal) < cos_t:
            e.smooth = False
    mesh = bpy.data.meshes.new(name)
    bm.to_mesh(mesh)
    bm.free()
    mesh.update()
    for m in materials:
        mesh.materials.append(m)
    obj = bpy.data.objects.new(name, mesh)
    (collection or bpy.context.scene.collection).objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def new_bmesh():
    return bmesh.new()


def add_empty(name, location=(0, 0, 0), scale=1.0, collection=None, parent=None, display="PLAIN_AXES"):
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_type = display
    obj.empty_display_size = 0.1
    obj.location = location
    obj.scale = (scale, scale, scale)
    (collection or bpy.context.scene.collection).objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj


def look_at(obj, target):
    """Point an object's -Z axis (a camera's view) at target with +Y up."""
    d = Vector(target) - Vector(obj.location)
    obj.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()


def add_camera(name, location, target, lens=28.0, sensor_width=36.0, clip_start=0.05, clip_end=1000.0,
               collection=None):
    cam = bpy.data.cameras.new(name)
    cam.lens = lens
    cam.sensor_width = sensor_width
    cam.sensor_fit = "HORIZONTAL"
    cam.clip_start = clip_start
    cam.clip_end = clip_end
    obj = bpy.data.objects.new(name, cam)
    (collection or bpy.context.scene.collection).objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def track_to(obj, target, track="TRACK_Z", up="UP_Y"):
    """Keep obj facing target through a constraint; constraints evaluate headless, drivers do not."""
    c = obj.constraints.new("TRACK_TO")
    c.target = target
    c.track_axis = track
    c.up_axis = up
    return c


def add_text(name, body, size, location, material, collection=None, parent=None, align="CENTER"):
    cu = bpy.data.curves.new(name, "FONT")
    cu.body = body
    cu.size = size
    cu.align_x = align
    cu.align_y = "CENTER"
    cu.materials.append(material)
    obj = bpy.data.objects.new(name, cu)
    obj.location = location
    (collection or bpy.context.scene.collection).objects.link(obj)
    if parent is not None:
        obj.parent = parent
    return obj

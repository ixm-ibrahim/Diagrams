"""Rung 2: the animatic. The Third-Person and First-Person camera roads over the whole scene,
the eye's blinks, exposure and edge tint, the camera roads of the four moves, and renders
that compose at final layout as a fast rough of the piece and of the showcase.

Run inside Blender from the project folder, absolute paths for every output:

  build:   blender.exe -b --python rungs/rung2.py -- build [--no-probes] [--frames a-b]
           builds Room and True, bakes the Third-Person road and the First-Person camera on
           the eyes, runs the engine, bakes the True-Person view, probes the eye's field
           for the exposure model, writes renders/rung2/eye_frames.json and saves
           scenes/rung2.blend.
  build --moves: the same scene with the four moves baked (Cam_Move on the head moves and on
           the reveal's room camera, the True camera on the reveal's model camera, the fades),
           saved as scenes/rung2_moves.blend. Needs the piece's eye_frames.json for the exposures.
  render:  blender.exe -b --python rungs/rung2.py -- render --view third|first|true --frames a-b
           --view scan (rung 2d): the eyes' fisheye scan per frame, frame_%04d.png with the eye's exposure
           --view backdrop (rung 2h): the same scan with everything but the sky, the ground and the range hidden
           --view sky (rung 2i): the same scan with everything but the sky's shell hidden, for the sky remembered behind the range
           --view peel (rung 2l): the same rays carried on through the first thing they strike to its far side, position
           and index alone, for the far side of every thing the mind holds whole
           --view pane (rung 2o): the window's glass alone, reflecting the scene and nothing else, for the model's glass layer
           and pos_%04d.exr with every pixel's hit in room metres; --mind lidar builds the True scene
           as the scan surface alone (triview/lidarscene.py), --true-road close a still test camera.
           --view check (rung 2o): the model through the simulated eyes themselves, the First-Person camera's
           own place, lens and frame, the mind's own things hidden, to set beside the First-Person picture
           (tools/check_eyes.py renders and compares)
           --profile: for every frame rendered, the seconds to set it, to render it, and the modifiers that took longest
           --no-frame-set: a True-Person frame worked out once, by the render alone (the pictures are the same to the pixel)
           tools/dev_showcase.py: the whole scene at every frame, chunk by chunk, only what is missing: the five scans, the
           First-Person view, the True-Person view at 1920 by 1080, the Third-Person view; then four videos with the
           stand-in sound and a clock in the scene's seconds
           blender.exe -b --python rungs/rung2.py -- render --view move --move third_true --pass room|mind --frames a-b
           Cycles for the room (24 samples at 960 by 540 by default), EEVEE for the dark.
           Frames already on disk are skipped, so a chunk can be rerun after a crash.

tools/run_rung2.py drives the builds, the chunks and the assembly from outside Blender.
"""
import argparse
import json
import math
import os
import pathlib
import shutil
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from triview import anim, body, cameras, engine, eye, geo, lidarscene, mindscene, render, room, tags, materials as mats  # noqa: E402

RENDER_FPS = 24             # the render's frames a second
FPS = 24.0                  # frames per chain second: RENDER_FPS over the chain's pace (data/beats.json), set in main()
PANEL = (960, 540)
PROBE_SIZE = (160, 90)
MOVE_NAMES = ("third_first", "first_third", "third_true", "true_third", "true_first")
SCAN_VIEWS = ("scan", "scan_move", "backdrop", "backdrop_move", "sky", "sky_move", "peel", "pane")
DATA_VIEWS = ("scan", "backdrop", "sky", "peel", "pane")   # the views that write a position and an index picture per frame
ORBIT_SPAN = (58.0, 90.0)   # the test's orbit (his review of 2026-11-08): one full turn round the head between these seconds
CLOSE_LENS = 72.0           # the test station's lens (60 until his seventh review of 2026-11-10: a little closer)
# a True camera for a test of the model alone (rung 2d): still, behind the left shoulder and above,
# looking into the skull from where the eyes' picture is seen the right way round
_hc = engine.HEAD_CENTRE
# 0.44 m from the head's centre (0.61 and 0.48 m read too small: his reviews of 2026-11-08)
CAMERA_KEYS_CLOSE = [
    (0.0, (_hc.x - 0.334, _hc.y + 0.247, _hc.z + 0.145), (_hc.x + 0.02, _hc.y, _hc.z - 0.01), CLOSE_LENS),
    (200.0, (_hc.x - 0.334, _hc.y + 0.247, _hc.z + 0.145), (_hc.x + 0.02, _hc.y, _hc.z - 0.01), CLOSE_LENS),
]



def orbit_keys():
    """The close station, and between ORBIT_SPAN one full turn round the head, rising over the crown
    and dipping below the eyes on the way: every angle of the model in one pass (his review of
    2026-11-08). Outside the span the camera rests at the close station, where the moves twin it."""
    t0, t1 = ORBIT_SPAN
    p0 = Vector(CAMERA_KEYS_CLOSE[0][1]) - _hc
    aim = CAMERA_KEYS_CLOSE[0][2]
    r = p0.length
    az0 = math.atan2(p0.y, p0.x)
    el0 = math.asin(p0.z / r)
    keys = [(0.0, tuple(_hc + p0), aim, CLOSE_LENS), (t0 - 1.0, tuple(_hc + p0), aim, CLOSE_LENS)]
    n = int(round((t1 - t0) / 0.25))
    for i in range(n + 1):
        u = i / n
        s = u * u * (3.0 - 2.0 * u)
        az = az0 + 2.0 * math.pi * s
        el = el0 + math.radians(22.0) * math.sin(2.0 * math.pi * u)
        pos = _hc + Vector((r * math.cos(el) * math.cos(az), r * math.cos(el) * math.sin(az), r * math.sin(el)))
        keys.append((t0 + (t1 - t0) * u, tuple(pos), aim, CLOSE_LENS))
    keys.append((t1 + 1.0, tuple(_hc + p0), aim, CLOSE_LENS))
    keys.append((200.0, tuple(_hc + p0), aim, CLOSE_LENS))
    return keys


# the showcase's opening (his fourteenth round of 2026-11-14): where the True camera stands with the whole glass body in
# view, behind its left shoulder on the side its held place is, and its aim at the body's middle
OPEN_WIDE = ((-3.22, 2.38, 1.45), (0.0, 0.0, 0.95), 24.0)


def open_keys(keys, t0, t1):
    """A held True camera given an opening: it stands back at OPEN_WIDE, the whole glass body in view, until t0
    seconds (the alarm), and is at its held place by t1, so the head it looks into from then on is seen to be the
    glass body's (his word of 2026-11-14: the camera was too close for the viewer to know what it looked at). The
    way in is even to the eye: the camera's distance from its aim and its lens both change by equal ratios in equal
    times, eased at both ends; and the aim leads, its distance from where it ends shrinking as the frame's height
    does, so the head keeps its place in the frame all the way in (with the aim going at the camera's own pace the
    head left the top of the frame half way)."""
    _, pos, aim, lens = keys[0]
    wp, wa, wl = OPEN_WIDE
    ow, oc = Vector(wp) - Vector(wa), Vector(pos) - Vector(aim)
    out = [(0.0, wp, wa, wl), (max(t0 - 0.25, 0.0), wp, wa, wl)]
    n = max(int(round((t1 - t0) / 0.25)), 1)
    h0, h1 = ow.length / wl, oc.length / lens          # the frame's height at the aim, up to a constant
    for i in range(n + 1):
        u = i / n
        s = u * u * (3.0 - 2.0 * u)
        dist = ow.length * (oc.length / ow.length) ** s
        ln = wl * (lens / wl) ** s
        lead = (dist / ln - h1) / (h0 - h1)
        a = Vector(aim).lerp(Vector(wa), max(0.0, min(1.0, lead)))
        d = ow.normalized().lerp(oc.normalized(), s).normalized() * dist
        out.append((t0 + (t1 - t0) * u, tuple(a + d), tuple(a), ln))
    out.append((t1 + 0.25, pos, aim, lens))
    out.append((200.0, pos, aim, lens))
    return out


def hold_keys(keys, t_hold):
    """The camera held still at its place on its road at t_hold seconds: a test of the model's own motion
    (2026-11-12: the drift of a remembered far side, which the orbit's own motion swamped)."""
    before = [k for k in keys if k[0] <= t_hold] or keys[:1]
    after = [k for k in keys if k[0] > t_hold] or keys[-1:]
    a, b = before[-1], after[0]
    w = 0.0 if b[0] <= a[0] else (t_hold - a[0]) / (b[0] - a[0])
    pos = tuple(Vector(a[1]).lerp(Vector(b[1]), w))
    return [(0.0, pos, a[2], a[3]), (200.0, pos, a[2], a[3])]


README = """Sensory Tri-View: the animatic's scene file (rung 2b), built by rungs/rung2.py; nothing in it needs Python to render.

Scenes
  Room  Cycles. The stand-in room, the mannequin, the phone, the dawn. Cameras: Cam_Third on the Third-Person road
        (triview/cameras.py THIRD_KEYS), Cam_First on the man's eyes, Cam_Move for the moves.
  True  EEVEE. The dark with the ghost, the soul and the mind's model inside the skull. Camera: Cam_True on the True road
        (triview/engine.py CAMERA_KEYS), tracking Cam_True_Aim.

Objects by name
  Man_<joint>, ManJ_<joint>, ManL_<joint>, Man_Head   the mannequin: joint Empties with keyframes, spheres and stretched limbs
                                                      (triview/body.py builds and animates it; triview/figure.py has the sizes)
  Floor, Ceiling, Wall_W, Wall_S, Wall_N, Wall_E, WindowFrame, PaneFrame, PaneGlass, Bed, Blanket, Table, Rug, Ground, Range,
  Phone, WindowPortal                                 the room, every thing its own object (triview/room.py)
  LampStand, LampTable, Piano, Tree_1, Tree_2, Bush_1 to Bush_7   stand-in furniture and trees, depth for the mind's picture to
                                                      read (rung 2e); rung 5 dresses the room and the outside for real
  Cam_Scan, SkyShell                                  the eyes' scan camera (a fisheye on Cam_First) and the far shell its
                                                      position pass reads for the sky (clear to the colour pass)
  Scan, MemoryLast, SunBall, Wave_, MiniSoul          with --mind lidar (triview/lidarscene.py): the scan as the mind's model,
                                                      the last picture the eyes held (none before their first opening, so while
                                                      he wakes with his eyes shut nothing of a picture stands in the head), the
                                                      sun as a ball of light, the sounds' rings
                                                      (rung 2p: one per tenth of a second of a sound, as bright as the sound is
                                                      loud, in its source's own shade of the radar's green, a bright line at the
                                                      outer edge trailing inward over 0.08 of the radius), the mind's own
                                                      simulation of the soul behind the simulated head
  Outline, Lightning_, GravityArrow, SenseTable       the senses on the simulated body (rung 2p, his specification of 2026-11-12
                                                      and his review of 2026-11-13, triview/lidarscene.py). Outline: one layer of
                                                      light 1.8 cm outside the skin for every sense on the skin, a band along the
                                                      outline of a moving part, a glow over the touched patch with its pain or
                                                      pleasure, a glow of warmth in gold on every part and of the window's cold
                                                      air on the named ones, on the skin the sun's rays or the air reach
                                                      (ContactBody's sun and air: the skin faces the source and the way to it is
                                                      clear of the room and of the body's own parts) and only where that skin
                                                      faces the camera, and the flash of the part a spark comes from; fading to
                                                      nothing at the layer's own outline (so no glow ends where the body does)
                                                      and wavering in brightness and hue. Two senses on one patch: the stronger
                                                      shows in its own colour. The head carries no moving-part band.
                                                      Lightning_: the touch's spark, a white zigzag in a blue glow through the
                                                      middle of the limb from the touched part joint by joint to the skull, drawn
                                                      toward the rendering camera so the limb does not hide it. It strikes where a
                                                      touch begins (his word of 2026-11-13: every case, and none while a touch
                                                      only lasts; his thirteenth round: run through the whole timeline, a collision
                                                      test between the limbs not joined at one joint). Before the engine runs, the
                                                      gap between every body part and every thing of the room, and every other
                                                      body part but those joined to it at one joint (tags.own_parts), is measured
                                                      at every frame (LidarScene.read_pairs, kept in <out>/contact_pairs.npz under
                                                      a key of the body pieces' places); triview/touches.py says which touches
                                                      begin, each at the frame its approach ends and with how fast its gap closed
                                                      (<out>/contact_pairs.json; tools/touch_audit.py lists them and prints any
                                                      pair's gap frame by frame); the pain's impact strikes by the timeline. It
                                                      is one spark from the contact to the skull in two poses, half way and at the
                                                      skull, its front the bright thing, each pose standing two frames while the
                                                      scene moves on every frame (on twos), gone at the fifth frame (his words of
                                                      2026-11-13: as a bolt of lightning is). Its light is the
                                                      touch's intensity, full for the pain's and by the square below it: the
                                                      timeline's strength times attention where it names the touch, and never less
                                                      than the touch's own, 0.2 where its gap closed at a standstill to 0.6 at a
                                                      metre a second, times his awareness (<out>/sparks.json: every spark drawn
                                                      with its light). GravityArrow: a
                                                      solid extruded arrow inside the simulated skull along where down is felt,
                                                      opaque and shaded, a ripple of its own shape running from its tail to its
                                                      point (a crest 17 percent wider, 28 until his thirteenth round), its broad face turned about its own length toward the rendering
                                                      camera and 28 degrees on, so one side shows. SenseTable: the picture
                                                      every surface samples for the sense on a part this frame (the organs' sense
                                                      light on their own tiles: the ear a ring crosses in green or in red, the
                                                      eyes red in the sun's glare, the heart and the lungs while thought of, the
                                                      torso breathing; the outline senses; and touch's colour and level on each
                                                      part), written by the bake to <out>/senses.exr
  ContactBody                                         where the body is touched (rung 2p, his word of 2026-11-12: one rule for
                                                      everything that touches him, and only the touched patch): the body's own
                                                      shapes in room metres, cut fine, every vertex carrying its contact with
                                                      every other thing (within a skin's distance of its surface, or inside its
                                                      closed shape) and with the body parts not joined to its own. Nothing of it
                                                      renders; every surface a sense lights reads the touched patch from it. It also
                                                      says where the body's skin is: a vertex inside another piece of the stand-in
                                                      body (inner) is no skin, and a sense is drawn on the skin alone, so the known
                                                      shapes' tiles and the outline glow leave those places out (his word of
                                                      2026-11-12: the outside of the mesh, what the sense's rays strike)
  ManO_<part>, Man_torso                              the mannequin's stand-in ears, eyes, heart and lungs (triview/figure.py ORGANS),
                                                      riding the head or a torso Empty keyed at the chest in the torso's frame
  Backdrop, SkyFill                                   the sky, the ground and the range behind the near things outside, from the
                                                      backdrop view (the scan with the near things hidden), and the sky behind
                                                      the range from the sky view: memories, gone where the eyes' rays reach
  MemoryShapes                                        every thing of the room by its known shape (rung 2o): a thing thought of,
                                                      drawn whole as memory in its known colour under the known light, fully opaque,
                                                      its shape first and its colour after; the far side of every thing held whole.
                                                      A tile of it is gone where the eyes see its place this frame (the scan's
                                                      own hit there, at its distance), so a seen surface shows as seen from every
                                                      camera; lit under a tenth, a tile thins out as it dims.
                                                      The known light's brightness is read off the picture that stands in the head
                                                      (the render sets Exposure and ExposureOut per frame from the eyes' own scan,
                                                      kept in <out>/known_light.json; the mind's own light before any picture). The peel
                                                      view still gives the rim's chords their far ends
  ThingTable                                          one vertex per thing of the room (its pass index): centre, radius and
                                                      region, which the surfaces' geometry reads for every hit by the index the
                                                      scan's index pass wrote beside its position
  ProxySun, SunDiscStandin                            stand-in light for the animatic; rung 5 sets the real light
  Ghost*, Soul                                        the True view's still glass figure and the light above it (triview/mindscene.py)
  ModelFrame, Model_<region>                          the mind's model: plates in room metres under one empty whose keyframed
                                                      matrix turns the room into the head's frame and scales it into the skull
  Sim_<joint>, SimJ_, SimL_, Sim_Head                 the simulated body inside the skull (the plates model, --mind plates)
  Wave_, SoundDisc_, Pulse_, Flash_, River_, Field_, PainThrob, Breath, Heart, SoulGlow, GravityArrow, GravityTip,
  WarmthRay_, SunDisc, Ridge_, Ground_, Word_, Will_  rung 1's signals in the plates model (triview/mindscene.py), baked from the
                                                      engine's per-frame state; the lidar model draws the senses in rung 2p's forms

Custom properties   att (attention 0..1) and col (colour) on every model object, read by the materials; face and edge on the
                    plates; tv_tag and tv_part on what the engine's rays can strike; tv_pass on glass the rays pass through
                    (clear to the scan's camera rays too); pass_index, every mesh's own number, the thing the scan's index
                    pass writes with each hit.
Node groups         TVModel (skull clip, thinning with distance, ModelScale = the mind's zoom), TVFade (Model, Ghost, Soul
                    fades the moves keyframe).
Data                data/beats.json (timeline), data/senses.json (sense events, will, recognition, memory, thoughts),
                    data/eyes.json (closures, blinks, exposure), data/cut.json (the showcase's order, the moves).
Driving it          tools/run_rung2.py builds, renders in chunks and assembles; tools/assemble_rung2.py lays the frames out
                    with FFmpeg and draws the lids and the edge tint from renders/rung2/eye_frames.json.
Stand-ins           the mannequin, its stand-in organs and its motion (rungs 3 and 4), the light and the pane (rung 5), every
                    second of timing (rung 4), a sound's loudness taken from the timeline's envelope (rung 6). The roads, the eye
                    model, the moves, the engine's rules and the data files are the lasting part.
"""


def write_readme(extra=""):
    txt = bpy.data.texts.get("README") or bpy.data.texts.new("README")
    txt.clear()
    txt.write(README + extra)
    return txt


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description="Sensory Tri-View rung 2")
    ap.add_argument("mode", choices=("build", "render"))
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung2.blend"))
    ap.add_argument("--moves-blend", default=str(ROOT / "scenes" / "rung2_moves.blend"))
    ap.add_argument("--senses", default=str(ROOT / "data" / "senses.json"))
    ap.add_argument("--beats", default=str(ROOT / "data" / "beats.json"))
    ap.add_argument("--eyes", default=str(ROOT / "data" / "eyes.json"))
    ap.add_argument("--cut", default=str(ROOT / "data" / "cut.json"))
    ap.add_argument("--frames", default=None, help="a-b or a,b,c; default the whole scene")
    ap.add_argument("--view", default="first", choices=("third", "first", "true", "move", "scan", "scan_move", "backdrop", "backdrop_move",
                                                        "sky", "sky_move", "peel", "pane", "check"))
    ap.add_argument("--move", default="third_first", choices=MOVE_NAMES)
    ap.add_argument("--pass", dest="pass_", default="room", choices=("room", "mind"))
    ap.add_argument("--moves", action="store_true", help="build the moves file")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--eevee-samples", type=int, default=24)
    ap.add_argument("--size", default=None, help="WxH; default 960x540")
    ap.add_argument("--border", default=None, help="x0,y0,x1,y1 in the frame's pixels from its top left: render that region alone, cropped to it "
                                                   "(a review clip of one part of the frame at more samples for the same time)")
    ap.add_argument("--hide", default=None, help="objects of the True scene left out of the render, by name and comma separated: one layer of the "
                    "model alone (Scan, MemoryLast, Backdrop, SkyFill, MemoryShapes, Outline), to find which layer a fault lies in")
    ap.add_argument("--to", default=None, help="the folder under --out the True frames go to, in place of true or true16: a test's own folder")
    ap.add_argument("--mind", default="plates", choices=("plates", "lidar"), help="the True scene: rung 2c plates, or the eyes scan alone (rung 2d)")
    ap.add_argument("--scan-size", type=int, default=640, help="the scan picture, pixels across its square")
    ap.add_argument("--scan-fov", type=float, default=200.0, help="the scan field across, degrees")
    ap.add_argument("--true-road", default="piece", choices=("piece", "close", "orbit"),
                    help="the True camera: the concept road, a close station over the shoulder for a test, or that station with one full turn round the head")
    ap.add_argument("--true-hold", type=float, default=None, help="hold the True camera still at its place on its road at this second: a test of the model's own motion")
    ap.add_argument("--true-open", default=None, help="a,b: the True camera stands back with the whole glass body in view until a seconds and is at "
                    "its held place by b (with --true-hold); the glass body is then built with its head")
    ap.add_argument("--no-probes", action="store_true")
    ap.add_argument("--probes-from", default=None, help="an earlier build's probes.json to reuse, so the eye table and the scan rendered at it stay as they were")
    ap.add_argument("--overwrite", action="store_true")
    ap.add_argument("--profile", action="store_true", help="print, for every frame rendered, the seconds to set the frame, the seconds to render "
                    "it, and the modifiers that took the longest to work out (a tool: where a frame's time goes)")
    ap.add_argument("--no-frame-set", action="store_true", help="a True-Person frame: give the scene its frame's number and leave the working "
                    "out to the render itself, which works the whole scene out anyway (with frame_set every frame was worked out twice)")
    ap.add_argument("--no-denoise", action="store_true", help="the Cycles views without the denoiser (it bleeds a silhouette's colours into its neighbours)")
    ap.add_argument("--step", type=int, default=1, help="render every Nth frame of the range, counted from frame 1: a fast test (his sixth review of 2026-11-09)")
    return ap.parse_args(argv)


def read_json(path):
    return json.loads(pathlib.Path(path).read_text(encoding="utf-8"))


def write_json(path, data):
    pathlib.Path(path).write_text(json.dumps(data, indent=1), encoding="utf-8")


def frame_range(args, total):
    if args.frames:
        if "," in args.frames or "-" not in args.frames:
            return [int(v) for v in args.frames.split(",") if v.strip()]
        a, b = (int(v) for v in args.frames.split("-"))
        return list(range(max(1, a), min(total, b) + 1))
    return list(range(1, total + 1))


# ---- build ---------------------------------------------------------------------------

def bake_third_road(cam, frames, baker):
    sw = anim.Sparse(baker)
    cam.rotation_mode = "QUATERNION"
    for f in frames:
        t = anim.time_of(f, FPS)
        pos, aim, lens = cameras.third_road(t)
        baker.set_vec(cam, "location", f, pos)
        baker.set_vec(cam, "rotation_quaternion", f, cameras.look_quat(pos, aim))
        sw.set(cam.data, "lens", 0, f, lens)
    sw.finish()


def probe_stats(path):
    """Linear statistics of a small EXR frame: the brightest tenth's mean, the key, the mean."""
    img = bpy.data.images.load(str(path), check_existing=False)
    try:
        w, h = img.size
        arr = np.empty(w * h * img.channels, dtype=np.float32)
        img.pixels.foreach_get(arr)
        rgb = arr.reshape(h, w, img.channels)[:, :, :3]
        lum = 0.2126 * rgb[:, :, 0] + 0.7152 * rgb[:, :, 1] + 0.0722 * rgb[:, :, 2]
        flat = np.sort(lum.ravel())
        top = flat[int(len(flat) * 0.9):]
        return {"bright": float(top.mean()), "key": float(math.exp(float(np.log(lum + 1e-4).mean()))),
                "mean": float(lum.mean()), "max": float(lum.max())}
    finally:
        bpy.data.images.remove(img)


def run_probes(scene, cam, frames_at, head, hide_head, tmp_dir, samples=8):
    """Tiny linear renders through cam at the given frames; returns {frame: stats}. head: the head, or the head with
    the stand-in eyes at the camera (rung 2p), hidden together."""
    own = list(head) if isinstance(head, (list, tuple)) else [head]
    head = own[0]
    render.setup_cycles(scene, samples=samples, adaptive=False, denoise=False)
    scene.render.use_persistent_data = True
    scene.camera = cam
    scene.render.resolution_x, scene.render.resolution_y = PROBE_SIZE
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "OPEN_EXR"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "16"
    scene.render.image_settings.exr_codec = "ZIP"
    scene.view_settings.exposure = 0.0
    for ob in own:
        ob.visible_camera = not hide_head
    out = {}
    path = pathlib.Path(tmp_dir) / f"probe_{cam.name}.exr"
    for f in frames_at:
        scene.frame_set(f)
        scene.render.filepath = str(path)
        bpy.ops.render.render(write_still=True, scene=scene.name)
        out[f] = probe_stats(path)
    try:
        os.remove(path)
    except OSError:
        pass
    for ob in own:
        ob.visible_camera = True
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_depth = "8"
    return out


def thing_points(spec, targets):
    """A room point for every region a thought can name (data/senses.json thoughts), for the mind's zoom:
    a thought's things are attended at their distance (triview/engine.py)."""
    W, D, H = spec.size
    wy0, wy1, wz0, wz1 = spec.window
    window = (W, (wy0 + wy1) / 2.0, (wz0 + wz1) / 2.0)
    sun_dir = room.sun_direction(spec, room.sun_elevation_at(spec, 60.0))
    sun = (W + sun_dir[0] * engine.SKY_DISTANCE, D / 2.0 + sun_dir[1] * engine.SKY_DISTANCE, 1.6 + sun_dir[2] * engine.SKY_DISTANCE)
    return {"bed": targets["bed"], "table": targets["table"], "table_far": targets["table"], "table_edge": targets["table"],
            "phone": targets["table"], "window": window, "sill": window, "wall_e": (W, D / 2.0, H / 2.0),
            "wall_w": (0.0, D / 2.0, H / 2.0), "wall_n": (W / 2.0, D, H / 2.0), "wall_s": (W / 2.0, 0.0, H / 2.0),
            "floor": (W / 2.0, D / 2.0, 0.0), "rug": (W / 2.0, D / 2.0, 0.0), "rug_edge": (W / 2.0, D / 2.0, 0.0),
            "ceiling": (W / 2.0, D / 2.0, H), "outside": (W + 20.0, D / 2.0, -0.3), "ground": (W + 20.0, D / 2.0, -0.3),
            "ridge": (W + spec.ridge_distance, D / 2.0, 0.0), "sun": sun, "sky": (W + engine.SKY_DISTANCE, D / 2.0, 0.0)}


def twin_spans(cut):
    """The reveals' twin phases from the cut's mind moves: while the model's camera rides the twin of the
    room's camera the model is the room at one scale (triview/engine.py). to_true: from the hold to
    twin_end; to_third: eased in from the hold, exact from twin_start to the end."""
    spans = []
    for m in cut.get("moves", {}).values():
        if m.get("kind") != "mind":
            continue
        hold, t1 = float(m["hold"]), float(m["t1"])
        if m["direction"] == "to_true":
            spans.append({"ease_from": hold, "from": hold, "to": float(m.get("twin_end", m["dissolve"][1]))})
        elif m["direction"] == "to_third":
            spans.append({"ease_from": hold, "from": float(m.get("twin_start", m["dissolve"][0])), "to": t1})
    return spans


def slot_colour(m):
    """A material's known colour: its base colour (an emitter's own), grey without one."""
    if m is not None and m.use_nodes:
        for n in m.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBsdfPrincipled":
                c = n.inputs["Base Color"].default_value
                return (float(c[0]), float(c[1]), float(c[2]))
            if n.bl_idname == "ShaderNodeEmission":
                c = n.inputs["Color"].default_value
                return (float(c[0]), float(c[1]), float(c[2]))
    return (0.6, 0.6, 0.6)


def thing_colours(ob):
    """A thing's known colours, one per material slot (grey for an empty slot)."""
    cols = [slot_colour(slot.material) for slot in ob.material_slots]
    return cols or [(0.6, 0.6, 0.6)]


def thing_colour(ob):
    return thing_colours(ob)[0]


def thing_rows(scene):
    """Give every mesh in the scene a pass index of its own (1 upward, by name) and return the model's
    table of things: per index its name, its centre, radius and half-extents in room metres (its bounds
    at the scene's frame; a thing that moves does so within the reach, where it is held at its distance
    whatever its row says), its region among the ten the mind can think of, read off the object's own
    properties (tv_tag, tv_part), its known colour, and whether the mind draws its shape whole (not the
    glass the rays pass through)."""
    rows = [{"id": 0, "name": "none", "centre": (0.0, 0.0, 0.0), "radius": 1.0e9, "region": lidarscene.REGION_OTHER, "part": -1}]
    # by name, the senses' stand-in organs (rung 2p) after everything else: the index pictures on disk keep their ids
    meshes = sorted((ob for ob in scene.objects if ob.type == "MESH"), key=lambda ob: (ob.get(tags.PART_PROP) in tags.ORGAN_PARTS, ob.name))
    dg = bpy.context.evaluated_depsgraph_get()
    for i, ob in enumerate(meshes, 1):
        ob.pass_index = i
        ev = ob.evaluated_get(dg)
        corners = [ev.matrix_world @ Vector(c) for c in ev.bound_box]
        lo = Vector((min(c.x for c in corners), min(c.y for c in corners), min(c.z for c in corners)))
        hi = Vector((max(c.x for c in corners), max(c.y for c in corners), max(c.z for c in corners)))
        # closed: every edge of the mesh has two faces, so a point can be told inside it (the model's contact test: a body
        # part sunk into the mattress is touched by it)
        edge_faces = {}
        for poly in ob.data.polygons:
            for key in poly.edge_keys:
                edge_faces[key] = edge_faces.get(key, 0) + 1
        closed = bool(edge_faces) and all(n == 2 for n in edge_faces.values())
        # round: no one direction holds much of its surface (a crown, a bush, a limb of the body), against a flat-faced
        # thing (a frame, a bed, a table). Its faces are taken together by the way they face, to a tenth of the normal:
        # a box's side counts whole however it is cut, and a limb's end cap, one many-sided face, does not make the limb
        # flat. The mind's picture closes a round thing's limb with chords; on a flat face seen edge-on those stood as a
        # comb (triview/lidarscene.py ROUND_SHARE)
        facing = {}
        for poly in ob.data.polygons:
            key = tuple(round(c, 1) for c in poly.normal)
            facing[key] = facing.get(key, 0.0) + poly.area
        face_share = (max(facing.values()) / max(sum(facing.values()), 1e-12)) if facing else 1.0
        rows.append({"id": i, "name": ob.name, "centre": tuple((lo + hi) / 2.0), "radius": max((hi - lo).length / 2.0, 0.01),
                     "half": tuple((hi - lo) / 2.0), "region": lidarscene.region_of(ob.get(tags.TAG_PROP), ob.get(tags.PART_PROP)),
                     "colour": thing_colour(ob), "colours": thing_colours(ob), "shape": not bool(ob.get(tags.PASS_PROP)),
                     "part": tags.PART_INDEX.get(ob.get(tags.PART_PROP), -1), "closed": closed, "of": ob.get(tags.OF_PROP),
                     "round": 1.0 if face_share < lidarscene.ROUND_SHARE else 0.0, "face_share": round(face_share, 4)})
    return rows


class Build:
    def __init__(self, args):
        self.args = args
        if args.true_road == "close":
            engine.CAMERA_KEYS = CAMERA_KEYS_CLOSE
        elif args.true_road == "orbit":
            engine.CAMERA_KEYS = orbit_keys()
        if getattr(args, "true_hold", None) is not None:
            engine.CAMERA_KEYS = hold_keys(engine.CAMERA_KEYS, float(args.true_hold))
        if getattr(args, "true_open", None):
            t_a, t_b = (float(v) for v in args.true_open.split(","))
            engine.CAMERA_KEYS = open_keys(engine.CAMERA_KEYS, t_a, t_b)
            # the glass body under the head, giving way over the last part of the way in
            lidarscene.GHOST_BODY = (t_a + 0.6 * (t_b - t_a), t_b)
        self.out = pathlib.Path(args.out).resolve()
        self.out.mkdir(parents=True, exist_ok=True)
        self.senses = engine.load_senses(args.senses)
        self.beats = read_json(args.beats)
        self.eyes_spec = eye.load(args.eyes)
        self.cut = read_json(args.cut)
        self.total = int(round(self.beats["duration_seconds"] * FPS))
        self.eyes = eye.Eyes(self.eyes_spec, self.beats["duration_seconds"], fps=FPS)
        self.frames = frame_range(args, self.total)
        self.timings = {"blender": bpy.app.version_string, "frames": [self.frames[0], self.frames[-1]], "moves": bool(args.moves)}

    def scenes(self):
        t0 = time.perf_counter()
        bpy.ops.wm.read_factory_settings(use_empty=True)
        room_scene = bpy.context.scene
        room_scene.name = "Room"
        room_scene.render.fps = RENDER_FPS
        room_scene.frame_start, room_scene.frame_end = self.frames[0], self.frames[-1]
        # the sky's own sun lights the room, at its physical strength, with the screen at a quarter of
        # its default: the light audit of 2026-11-08 found the sky's sun had stood in the west behind
        # the west wall, which is why its disc never reached the camera and its light never reached
        # the room, and why a proxy lamp and a stand-in disc had been added; both are gone
        self.spec = room.RoomSpec(sun_intensity=1.0, screen_strength=1.5, sun_disc_standin=False, standins=True)
        spec = self.spec
        # the hand against the sun is solved onto the line from the eyes to the sun, so the motion needs the sun
        # and what the eyes look at: the timeline's sight events that name a thing (the eyes turn to it in the head)
        (gbx0, gby0, _), (gbx1, gby1, gbz1) = spec.bed
        (gtx0, gty0, _), (gtx1, gty1, gtz1) = spec.table
        looks = [(ev["t0"], ev["t1"], ev["target"]) for ev in self.senses["events"] if ev.get("sense") == "sight" and ev.get("target")]
        self.motion = body.Motion(sun_dir=lambda t: room.sun_direction(spec, room.sun_elevation_at(spec, t)), gaze=looks,
                                  gaze_points={"bed": ((gbx0 + gbx1) / 2, (gby0 + gby1) / 2, gbz1), "table": ((gtx0 + gtx1) / 2, (gty0 + gty1) / 2, gtz1)})
        self.samples = {f: self.motion.sample(anim.time_of(f, FPS)) for f in self.frames}
        baker = anim.Baker()
        self.info = room.build_room_animated(room_scene, self.spec, self.motion, self.frames, FPS, baker, samples=self.samples)
        self.room_scene = room_scene
        # rung 1's proxy lamp stays for EEVEE previews but renders nothing: the sky's sun is the light
        sun = self.info["sun"]
        sun.data.energy = 40.0
        sun.data.color = (1.0, 0.86, 0.68)
        sun.data.angle = math.radians(0.53)
        sun.hide_render = True
        bake_third_road(self.info["cam_third"], self.frames, baker)
        self.cam_move = geo.add_camera("Cam_Move", (3.5, 3.0, 1.6), (2.0, 0.8, 1.2), lens=28.0, clip_start=0.03,
                                       collection=room_scene.collection)
        self.cam_move.rotation_mode = "QUATERNION"
        # the eyes' scan (rung 2d): a fisheye camera riding the First-Person camera over the field of both
        # eyes, and a shell far outside the room that the scan's position pass shows for the sky's hits
        cam_first = self.info["cam_first"]
        self.cam_scan = geo.add_camera("Cam_Scan", (0.0, 0.0, 1.6), (1.0, 0.0, 1.6), lens=cameras.FIRST_LENS, clip_start=0.03,
                                       collection=room_scene.collection)
        self.cam_scan.parent = cam_first
        self.cam_scan.matrix_parent_inverse = Matrix.Identity(4)
        self.cam_scan.location = (0.0, 0.0, 0.0)
        self.cam_scan.rotation_euler = (0.0, 0.0, 0.0)
        cd = self.cam_scan.data
        cd.type = "PANO"
        cd.panorama_type = "FISHEYE_EQUIDISTANT"
        cd.fisheye_fov = math.radians(self.args.scan_fov)
        cd.sensor_width = 36.0
        cd.clip_end = 20000.0
        W, D, H = spec.size
        bm = geo.new_bmesh()
        geo.add_sphere(bm, (W / 2, D / 2, 0.0), 9000.0, 0, segments=32, rings=16)
        # the shell stays in the scene for both passes: camera rays alone see it, its own material is
        # clear, and only the position pass's material makes anything of it. Hidden and shown per
        # frame, it stayed in the colour pass on runs of frames under persistent data, where the rays
        # refracted through the window's glass were the only ones to reach it, so the open leaf went
        # black (his review of 2026-11-08: black flicker on the window)
        self.sky_shell = geo.finish(bm, "SkyShell", [mats.clear("SkyShellClear")], room_scene.collection)
        for flag in ("visible_diffuse", "visible_glossy", "visible_transmission", "visible_volume_scatter", "visible_shadow"):
            setattr(self.sky_shell, flag, False)
        self.sky_shell[tags.TAG_PROP] = "sky"
        # the sun's stand-in disc, when there is one, is clear to the scan like the window's glass
        if self.info["sun_disc"] is not None:
            self.info["sun_disc"][tags.PASS_PROP] = 1.0
        # every thing the rays can strike gets a pass index of its own, which the scan's index pass
        # writes with every hit, and a row in the model's table of things (triview/lidarscene.py)
        self.things = thing_rows(room_scene)
        print(f"THINGS: {len(self.things) - 1} things indexed: " + ", ".join(f"{r['name']} r{r['region']}" for r in self.things[1:]), flush=True)
        n_room = baker.write()
        self.timings["room_build_s"] = round(time.perf_counter() - t0, 2)
        self.timings["room_keyframes"] = n_room
        print(f"BUILD room: {self.timings['room_build_s']} s, {n_room} keyframes", flush=True)

        t1 = time.perf_counter()
        if self.args.mind == "lidar":
            self.true_scene = lidarscene.LidarScene("True", self.spec, FPS, eevee_samples=self.args.eevee_samples, bloom=True, render_fps=RENDER_FPS,
                                                    scan_dir=self.out / "scan", frame_count=self.total, placeholder_dir=self.out / "placeholder",
                                                    scan_size=self.args.scan_size, fov_deg=self.args.scan_fov, things=self.things)
        else:
            self.true_scene = mindscene.TrueScene("True", self.spec, FPS, eevee_samples=self.args.eevee_samples, bloom=True, render_fps=RENDER_FPS,
                                                  first_dir=self.out / "first", frame_count=self.total, placeholder_dir=self.out / "placeholder")
        self.true_scene.scene.frame_start, self.true_scene.scene.frame_end = self.frames[0], self.frames[-1]
        self.true_scene.add_words(self.senses["words"], self.senses["will"])
        self.timings["true_build_s"] = round(time.perf_counter() - t1, 2)

        t2 = time.perf_counter()
        bpy.context.window.scene = room_scene
        reader = engine.SceneReader(room_scene, self.info["figure"]["empties"], self.info["phone"], self.info["sky"], self.spec,
                                    room.sun_direction, (body.EYE_OFFSET, body.EAR_OFFSET))
        (bx0, by0, bz0), (bx1, by1, bz1) = self.spec.bed
        (tx0, ty0, tz0), (tx1, ty1, tz1) = self.spec.table
        targets = {"bed": ((bx0 + bx1) / 2, (by0 + by1) / 2, bz1), "table": ((tx0 + tx1) / 2, (ty0 + ty1) / 2, tz1)}
        # when the touch begins or lands anew through the piece, read off the contact itself: the lightning's strikes
        # (his word of 2026-11-13, thirteenth round: every pair of a body part and a thing, or another part not joined to
        # it at one joint), each with how fast its gap closed
        strikes, begins = (self.true_scene.read_pairs(room_scene, self.frames, FPS, self.out / "contact_pairs.json")
                           if self.args.mind == "lidar" else ([], []))
        print(f"STRIKES: {len(strikes)} sparks from {len(begins)} touches that begin: "
              + ", ".join(f"{h[0]:.2f} {h[1]} {h[2]:.2f}" for h in strikes), flush=True)
        eng = engine.Engine(self.senses, reader, FPS, ridge_profile=room.ridge_profile(self.spec), window=self.spec.window,
                            room_size=self.spec.size, targets=targets, thing_points=thing_points(self.spec, targets),
                            twin_spans=twin_spans(self.cut), cover_of=lambda t: self.eyes.cover(t), strikes=strikes,
                            ridge_elevation=room.RIDGE_ELEVATION)
        self.states = [eng.frame_state(f) for f in self.frames]
        self.by_frame = {s.frame: s for s in self.states}
        # the crest's reaction against the light itself (his word of 2026-11-16: a reaction to the light hitting his eyes,
        # with a realistic reaction time, not an actor who knows it is coming). The scene's own first light is the first
        # frame the eyes' rays reach the sun's disc with the lids open; the script's reactions are printed beside it
        lit = [s for s in self.states if s.sun_sight > 0.0 and self.eyes.cover(s.t) < 0.5]
        if lit:
            t_light = lit[0].t
            t_hand = body.SHADE[0][0]
            t_lids = next((s.t for s in self.states if s.t >= t_light and self.eyes.cover(s.t) > 0.05), None)
            late = [t_hand - t_light] + ([t_lids - t_light] if t_lids is not None else [])
            verdict = "a reaction" if min(late) >= 0.08 else "WARNING: NOT A REACTION, he moves with the light or before it"
            print(f"FIRST LIGHT: the sun's disc first reaches his open eyes at {t_light:.2f} s (the script has {body.FIRST_LIGHT:.2f}); "
                  f"his lids begin to shut {'%.2f s' % (t_lids - t_light) if t_lids is not None else 'never'} after it, his hand starts {t_hand - t_light:+.2f} s "
                  f"from it: {verdict}", flush=True)
        else:
            print("FIRST LIGHT: WARNING, the sun's disc never reaches his open eyes", flush=True)
        # every spark drawn through the piece, with the intensity it reached and its light: the audit's table
        # (tools/touch_audit.py reads it beside the touches that begin)
        drawn = sorted((t0, part, a) for (part, t0), a in eng._strike_peak.items() if a > 1e-4)
        write_json(self.out / "sparks.json", {"sparks": [
            {"t": round(t0, 3), "part": part, "intensity": round(a, 4),
             "light": round(engine.clamp(a / engine.LIGHTNING_FULL) ** engine.LIGHTNING_CURVE, 4)} for t0, part, a in drawn]})
        print(f"SPARKS: {len(drawn)} drawn, written to sparks.json", flush=True)
        self.timings["engine_s"] = round(time.perf_counter() - t2, 2)
        print(f"ENGINE: {len(self.states)} frames in {self.timings['engine_s']} s", flush=True)

    # the context the moves read
    def head_at(self, t):
        f = min(max(anim.frame_of(t, FPS), self.frames[0]), self.frames[-1])
        return self.samples[f][1]

    @staticmethod
    def true_at(t):
        return engine.catmull(engine.CAMERA_KEYS, t)

    def bake_true(self):
        t3 = time.perf_counter()
        baker = anim.Baker()
        if self.args.mind == "lidar":
            # the simulated eyes exactly where the scan camera was: the same samples Cam_First was baked from
            gap = max((Vector(self.samples[fs.frame][1]["eye"]) - Vector(fs.eye_room)).length for fs in self.states)
            print(f"BAKE: the engine's eye and the scan camera's differ by at most {gap * 1000:.2f} mm", flush=True)
            self.true_scene.bake(self.states, baker, cover_of=lambda f: self.eyes.cover(anim.time_of(f, FPS)),
                                 eye_of=lambda f: (self.samples[f][1]["eye"], self.samples[f][1]["rot"],
                                                   self.samples[f][1].get("eye_rot", self.samples[f][1]["rot"])), eyes=self.eyes,
                                 phone_of=lambda f: self.samples[f][3].translation)
            # the picture frames each frame's memories read: a stepped render keeps them too
            # and the picture that stands in the head each frame, with how far it stands: the known light is read off it
            write_json(self.out / "held_frames.json", {"by_frame": {str(f): refs for f, refs in self.true_scene.held.items()},
                                                       "picture": {str(f): [p, round(w, 4)] for f, (p, w) in self.true_scene.picture.items()}})
        else:
            self.true_scene.bake(self.states, baker)
        n_true = baker.write()
        self.timings["bake_s"] = round(time.perf_counter() - t3, 2)
        self.timings["true_keyframes"] = n_true
        print(f"BAKE: {n_true} keyframes in {self.timings['bake_s']} s", flush=True)

    def eye_table(self):
        """Probes for the exposure model, then the per-frame eye table."""
        t4 = time.perf_counter()
        spec, frames = self.spec, self.frames
        times = {f: anim.time_of(f, FPS) for f in frames}
        face_sun = {}
        sun_uv = {}
        sun_dir, pain_dir = {}, {}     # the same two places as directions in the eyes' own frame (forward, left, up)

        def eye_axes(hf):
            return hf.get("eye_fwd", hf["fwd"]), hf.get("eye_left", hf["left"]), hf.get("eye_up", hf["up"])

        for f in frames:
            hf = self.samples[f][1]
            el = room.sun_elevation_at(spec, times[f])
            d = room.sun_direction(spec, el)
            # (by the share of the disc up over the land as his eyes have it, the engine's sun_up: by the sun's height over
            # the level until 2026-11-16, and the closed lids glowed with a sun still behind the range, through the doze)
            face_sun[f] = max(0.0, hf["fwd"].dot(d)) * float(getattr(self.by_frame.get(f), "sun_up", 0.0))
            # where the sun stands in the First-Person picture (0 to 1 across and down), for the light through
            # the closed lids (his tenth review of 2026-11-10): the camera on the eyes, its lens over a 36 mm sensor;
            # in the eyes' own frame, which their look turns in the head (2026-11-14)
            ex, ey, ez = eye_axes(hf)
            x, y, z = ex.dot(d), ey.dot(d), ez.dot(d)
            sun_dir[f] = [round(float(x), 4), round(float(y), 4), round(float(z), 4)]
            if x > 0.05:
                k = cameras.FIRST_LENS / 36.0
                sun_uv[f] = (round(0.5 - (y / x) * k, 4), round(0.5 - (z / x) * k * (PANEL[0] / PANEL[1]), 4))
        # the First-Person flash toward a pain (rung 2p): its level and where the pain lies in the picture (0 to 1 across
        # and down, past the frame's edge when it lies behind), from the engine's flash
        pain_rows = {}
        for f in frames:
            fs = self.by_frame.get(f)
            level, fdir = getattr(fs, "flash", (0.0, None)) if fs is not None else (0.0, None)
            if level <= 1e-3 or fdir is None:
                continue
            d = Vector(fdir)
            if d.length < 1e-6:
                continue
            d.normalize()
            hf = self.samples[f][1]
            ex, ey, ez = eye_axes(hf)
            x, y, z = ex.dot(d), ey.dot(d), ez.dot(d)
            pain_dir[f] = [round(float(x), 4), round(float(y), 4), round(float(z), 4)]
            k = cameras.FIRST_LENS / 36.0
            if x > 0.2:
                u, v = 0.5 - (y / x) * k, 0.5 - (z / x) * k * (PANEL[0] / PANEL[1])
            else:
                m = max(abs(y), abs(z), 1e-6)
                u, v = 0.5 - 0.75 * y / m, 0.5 - 0.75 * z / m
            pain_rows[f] = [round(float(level), 3), round(max(-0.5, min(1.5, u)), 3), round(max(-0.5, min(1.5, v)), 3)]
        eyes = self.eyes
        head = [self.info["figure"]["head"]] + list(self.info["figure"].get("eyes", []))
        ef, et = self.eyes_spec["exposure_first"], self.eyes_spec["exposure_third"]
        if self.args.no_probes:
            probes_first = [(times[frames[0]], 0.1, 0.01, 0.05), (times[frames[-1]], 0.1, 0.01, 0.05)]
            probes_third = [(times[frames[0]], 0.05), (times[frames[-1]], 0.05)]
        elif self.args.probes_from:
            saved = read_json(self.args.probes_from)
            probes_first = [(p["t"], p["bright"], p["key"], p["mean"]) for p in saved["first"]]
            probes_third = [(p["t"], p["mean"]) for p in saved["third"]]
            write_json(self.out / "probes.json", saved)
            print(f"EYE: probes reused from {self.args.probes_from}", flush=True)
        else:
            step_f = int(round(float(ef.get("probe_step", 0.25)) * FPS))
            step_t = int(round(float(et.get("probe_step", 1.0)) * FPS))
            at_first = [f for f in frames if (f - 1) % step_f == 0]
            at_third = [f for f in frames if (f - 1) % step_t == 0]
            if frames[-1] not in at_first:
                at_first.append(frames[-1])
            if frames[-1] not in at_third:
                at_third.append(frames[-1])
            bpy.context.window.scene = self.room_scene
            # the probes see the field, not the sun's disc: one pixel of the disc would swamp the
            # brightest tenth and shut the eye down (the eye adapts to the field, the disc is glare)
            self.info["sky"].sun_disc = False
            pf = run_probes(self.room_scene, self.info["cam_first"], at_first, head, True, self.out)
            pt = run_probes(self.room_scene, self.info["cam_third"], at_third, head, False, self.out)
            self.info["sky"].sun_disc = True
            probes_first = [(times[f], pf[f]["bright"], pf[f]["key"], pf[f]["mean"]) for f in at_first]
            probes_third = [(times[f], pt[f]["mean"]) for f in at_third]
            write_json(self.out / "probes.json", {"first": [{"t": p[0], "bright": p[1], "key": p[2], "mean": p[3]} for p in probes_first],
                                                  "third": [{"t": p[0], "mean": p[1]} for p in probes_third]})
        rows = eye.build_table(frames, FPS, times, eyes, probes_first, probes_third, self.by_frame, face_sun, self.eyes_spec, sun_uv=sun_uv,
                               pain=pain_rows, sun_dir=sun_dir, pain_dir=pain_dir)
        table = {"fps": FPS, "render_fps": RENDER_FPS, "frames": [frames[0], frames[-1]], "closures": eyes.closures, "blinks": eyes.blinks, "rows": rows}
        write_json(self.out / "eye_frames.json", table)
        self.timings["probes_s"] = round(time.perf_counter() - t4, 2)
        self.timings["probes"] = {"first": len(probes_first), "third": len(probes_third)}
        print(f"EYE: table of {len(rows)} frames, {len(eyes.blinks)} blinks, probes in {self.timings['probes_s']} s", flush=True)
        return table

    # ---- the moves ----
    def M_at(self, t):
        f = min(max(anim.frame_of(t, FPS), self.frames[0]), self.frames[-1])
        return self.by_frame[f].M

    def first_at(self, t):
        """The First-Person camera at t: on the eyes, looking where the head looks."""
        hf = self.head_at(t)
        return Vector(hf["eye"]), Vector(hf["eye"]) + Vector(hf["fwd"]), cameras.FIRST_LENS

    def believed_point(self, t, p_model):
        """A point of the room, already in the model's frame as the twin camera is, to where the mind
        holds it: on its line from the eyes at its believed distance (triview/engine.py believed, the
        far field taken as resolved) and pressed onto the glass beyond the knee, as every hit is. The
        camera is a thing in the room like any other, so a camera that stands between the room's walls
        stands between the model's (his sixth review of 2026-11-09: a wall in the way of the reveal)."""
        f = min(max(anim.frame_of(t, FPS), self.frames[0]), self.frames[-1])
        fs = self.by_frame[f]
        eye_model = fs.M @ Vector(self.samples[f][1]["eye"])
        v = Vector(p_model) - eye_model
        d = v.length
        if d < 1e-9:
            return Vector(p_model)
        d_b = engine.believed(d / fs.scale, 1.0) * fs.scale
        knee = lidarscene.KNEE * engine.GLASS_RADIUS
        span = engine.GLASS_RADIUS - knee
        d_p = d_b if d_b <= knee else knee + span * (1.0 - math.exp(-(d_b - knee) / span))
        return eye_model + v * (d_p / d)

    def bake_moves(self, eye_rows):
        """Cam_Move on the head moves and on the reveal's room camera; the True camera and the
        fades on the reveal's model camera. Returns the per-frame tables of the moves."""
        t5 = time.perf_counter()
        rows_by_frame = {r["f"]: r for r in eye_rows}
        baker = anim.Baker()
        sw = anim.Sparse(baker)
        head = self.info["figure"]["head"]
        own = [head] + list(self.info["figure"].get("eyes", []))
        cam = self.cam_move

        def pain_at(row, w):
            pn = row.get("pain")
            return None if (not pn or w <= 0.0) else [round(pn[0] * w, 3), pn[1], pn[2]]
        tables = {}
        # in time order: keyed out of it, the sparse keys of one move ran on into the next's (the room camera's
        # lens drifted from 38.6 to 35.9 mm through the reveal while the model's stayed: his ninth review)
        for name in sorted(MOVE_NAMES, key=lambda n: float(self.cut["moves"][n]["t0"])):
            mspec = self.cut["moves"][name]
            t0, t1 = float(mspec["t0"]), float(mspec["t1"])
            mframes = [f for f in range(anim.frame_of(t0, FPS), anim.frame_of(t1, FPS) + 1) if f in self.by_frame]
            rows = []
            if not mframes:
                tables[name] = {"kind": mspec["kind"], "t0": t0, "t1": t1, "frames": [], "rows": []}
                continue
            if mspec["kind"] == "head":
                fn = cameras.third_to_first if name == "third_first" else cameras.first_to_third
                for f in mframes:
                    t = anim.time_of(f, FPS)
                    ms = fn(t, t0, t1, self.head_at, cameras.third_road)
                    baker.set_vec(cam, "location", f, ms.pos)
                    baker.set_vec(cam, "rotation_quaternion", f, ms.rot)
                    sw.set(cam.data, "lens", 0, f, ms.lens)
                    for ob in own:
                        sw.set(ob, "visible_camera", 0, f, 0.0 if ms.head_hidden else 1.0, anim.CONSTANT)
                    er = rows_by_frame.get(f, {})
                    w = ms.eye_weight
                    exp = anim.lerp(er.get("exp_third", 0.0), er.get("exp_first", 0.0), w)
                    # the eye's own lids count once the camera is more the eye than the road
                    own = float(er.get("cover", 0.0)) if w > 0.5 else 0.0
                    cover = max(ms.cover, own)
                    closed = bool(er.get("closed", 0)) and w > 0.5
                    rows.append({"f": f, "t": round(t, 4), "cover": round(cover, 3), "blink": int(cover >= 0.999),
                                 "closed": int(closed), "eye_weight": round(w, 3), "exp": round(exp, 3),
                                 "lid": er.get("lid", [0, 0, 0]) if (closed or own > 0) else [0, 0, 0],
                                 "tint": er.get("tint", [0, 0, 0]), "tint_a": round(er.get("tint_a", 0.0) * w, 3),
                                 "sun_uv": er.get("sun_uv"), "face_sun": er.get("face_sun", 0.0), "pain": pain_at(er, w),
                                 "pos": [round(v, 3) for v in ms.pos], "lens": round(ms.lens, 2)})
            else:
                direction = mspec["direction"]
                # the twin camera is a thing in the room like any other, placed in the model by the rule
                # every hit follows (believed_point), so a camera between the room's walls stays between them
                rv = cameras.Reveal(name, mspec, cameras.third_road, self.true_at, self.M_at, direction,
                                    bounds=((0.0, 0.0, 0.0), tuple(self.spec.size)), first_at=self.first_at,
                                    press=self.believed_point if self.args.mind == "lidar" else None)
                hold, d0, d1 = float(mspec["hold"]), float(mspec["dissolve"][0]), float(mspec["dissolve"][1])
                twin_end, twin_start = float(mspec.get("twin_end", d1)), float(mspec.get("twin_start", d0))
                last_room = None
                for f in mframes:
                    t = anim.time_of(f, FPS)
                    smp = rv.sample(t)
                    room_cam = smp["room"] if smp["room"] is not None else last_room
                    if room_cam is None:
                        p, a, l = cameras.third_road(t1) if direction != "to_first" else self.first_at(t)
                        room_cam = (Vector(p), Vector(a), l)
                    last_room = room_cam
                    rp, ra, rl = room_cam
                    mp, ma, ml = smp["mind"]
                    baker.set_vec(cam, "location", f, rp)
                    # the dive's room camera is the First-Person camera itself, its roll the head's
                    rot = cameras.first_camera(self.head_at(t))[1] if direction == "to_first" else cameras.look_quat(rp, ra)
                    baker.set_vec(cam, "rotation_quaternion", f, rot)
                    sw.set(cam.data, "lens", 0, f, rl)
                    for ob in own:
                        sw.set(ob, "visible_camera", 0, f, 0.0 if direction == "to_first" else 1.0, anim.CONSTANT)
                    fs = self.by_frame[f]
                    fs.camera = (Vector(mp), Vector(ma), ml)
                    # the model's camera turns as the twin of the room's camera, roll included (his ninth review
                    # of 2026-11-10: with the model's up the torso's and the camera's the room's, the picture
                    # rolled by the torso's tilt, 7 to 11 degrees), eased to the road's own bearing where the
                    # camera leaves the twin
                    twin_q = (fs.M.to_3x3().normalized() @ rot.to_matrix()).to_quaternion()
                    if direction == "to_true":
                        w_twin = 1.0 if t <= twin_end else 1.0 - cameras.ramp(t, twin_end, float(mspec.get("ease1", t1)))
                    else:
                        w_twin = cameras.ramp(t, hold, twin_start)
                    # the camera always looks at its own aim; only its up eases between the twin's and the model's
                    up_twin = twin_q @ Vector((0.0, 1.0, 0.0))
                    up = up_twin.slerp(Vector((0.0, 0.0, 1.0)), 1.0 - w_twin) if w_twin < 0.999 else up_twin
                    fs.camera_rot = cameras.look_quat_up(Vector(mp), Vector(ma), up)
                    fs.fade_model, fs.fade_ghost, fs.fade_soul = smp["fade_model"], smp["ghost_w"], smp["soul_w"]
                    er = rows_by_frame.get(f, {})
                    # the room pass stays at the road's exposure, and the model's picture through the
                    # move is a second scan of the eyes at that exposure (scan_move), easing to the
                    # eye's own as the camera leaves the skull, so nothing brightens as the model
                    # takes over (his review of 2026-11-08, second: the rays spawning into existence)
                    e3, e1 = er.get("exp_third", 0.0), er.get("exp_first", 0.0)
                    if direction == "to_true":
                        exp, scan_exp = e3, anim.lerp(e3, e1, cameras.ramp(t, twin_end, t1))
                    elif direction == "to_third":
                        exp, scan_exp = e3, anim.lerp(e1, e3, cameras.ramp(t, hold, twin_start))
                    else:
                        exp, scan_exp = e1, None
                    # the dive lands on the eyes: their lids and tint come in with the room's share
                    w = smp["room_w"] if direction == "to_first" else 0.0
                    cover = float(er.get("cover", 0.0)) * w
                    rows.append({"f": f, "t": round(t, 4), "cover": round(cover, 3), "blink": int(cover >= 0.999),
                                 "closed": int(bool(er.get("closed", 0)) and w > 0.5), "eye_weight": round(w, 3),
                                 "exp": round(exp, 3), "lid": er.get("lid", [0, 0, 0]) if cover > 0 else [0, 0, 0],
                                 "tint": er.get("tint", [0, 0, 0]) if w > 0 else [0, 0, 0], "tint_a": round(er.get("tint_a", 0.0) * w, 3),
                                 "sun_uv": er.get("sun_uv"), "face_sun": er.get("face_sun", 0.0), "pain": pain_at(er, w),
                                 "pos": [round(v, 3) for v in rp], "mind_pos": [round(v, 3) for v in mp], "lens": round(rl, 2),
                                 "mind_lens": round(ml, 2), "direction": direction,
                                 "scan_exp": None if scan_exp is None else round(scan_exp, 3),
                                 "weights": {k: round(smp[k], 3) for k in ("room_w", "model_w", "ghost_w", "soul_w")}})
            tables[name] = {"kind": mspec["kind"], "t0": t0, "t1": t1, "frames": [mframes[0], mframes[-1]] if mframes else [], "rows": rows}
        sw.finish()
        n = baker.write()
        self.timings["moves_bake_s"] = round(time.perf_counter() - t5, 2)
        self.timings["moves_keyframes"] = n
        print(f"MOVES: {n} keyframes in {self.timings['moves_bake_s']} s", flush=True)
        return tables

    def summary(self, table):
        rows = {r["f"]: r for r in table["rows"]}
        out = {"beats": []}
        for b in self.beats["beats"]:
            mid = anim.frame_of((b["start"] + b["end"]) / 2.0, FPS)
            fs = self.by_frame.get(mid)
            r = rows.get(mid)
            if fs is None or r is None:
                continue
            pos, aim, lens = cameras.third_road(anim.time_of(mid, FPS))
            out["beats"].append({"beat": b["id"], "frame": mid, "third_camera": [round(v, 2) for v in pos], "third_lens": round(lens, 1),
                                 "exp_third": r["exp_third"], "exp_first": r["exp_first"], "closed": r["closed"],
                                 "sense": r["sense"], "tint_a": r["tint_a"], "bright": r["bright"], "face_sun": r["face_sun"]})
        out["blinks"] = len(table["blinks"])
        return out


def build(args):
    b = Build(args)
    t0 = time.perf_counter()
    b.scenes()
    if args.moves:
        table_path = b.out / "eye_frames.json"
        if not table_path.exists():
            sys.exit("build --moves needs renders/rung2/eye_frames.json from the piece's build first")
        eye_rows = read_json(table_path)["rows"]
        tables = b.bake_moves(eye_rows)
        b.bake_true()
        write_json(b.out / "moves_frames.json", {"fps": FPS, "render_fps": RENDER_FPS, "moves": tables})
        blend = pathlib.Path(args.moves_blend).resolve()
    else:
        b.bake_true()
        table = b.eye_table()
        write_json(b.out / "animatic_summary.json", b.summary(table))
        blend = pathlib.Path(args.blend).resolve()
    blend.parent.mkdir(parents=True, exist_ok=True)
    write_readme(f"\nThis file: {'the moves' if args.moves else 'the piece'}, frames {b.frames[0]} to {b.frames[-1]}, built {time.strftime('%Y-%m-%d %H:%M')} with Blender {bpy.app.version_string}.\n")
    b.timings["objects"] = len(bpy.data.objects)
    b.timings["total_s"] = round(time.perf_counter() - t0, 2)
    write_json(b.out / ("build_timings_moves.json" if args.moves else "build_timings.json"), b.timings)
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    print("SAVED:", blend, flush=True)
    print("TIMINGS:", json.dumps(b.timings), flush=True)


# ---- render --------------------------------------------------------------------------

def _through(nt, surface, layer):
    """The surface for the ray's layer-th strike: the first `layer` surfaces a ray meets are passed (a
    Transparent BSDF until the light path's Transparent Depth reaches the layer), so layer 1 is the far
    side of the thing the ray struck first, or whatever stands behind an open surface."""
    if layer <= 0:
        return surface
    lp = nt.nodes.new("ShaderNodeLightPath")
    deep = nt.nodes.new("ShaderNodeMath")
    deep.operation = "GREATER_THAN"
    nt.links.new(lp.outputs["Transparent Depth"], deep.inputs[0])
    deep.inputs[1].default_value = layer - 0.5
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(deep.outputs["Value"], mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(surface, mix.inputs[2])
    return mix.outputs["Shader"]


def reflection_material():
    """The pane's glass reflecting alone (the pane view, rung 2o): the window glass material with its clear side
    black, so the picture is the Fresnel reflection of the scene and nothing else."""
    mat = bpy.data.materials.get("PaneReflect")
    if mat is None:
        mat = mats.glass_pane("PaneReflect")
        for n in mat.node_tree.nodes:
            if n.bl_idname == "ShaderNodeBsdfTransparent":
                n.inputs["Color"].default_value = (0.0, 0.0, 0.0, 1.0)
    return mat


def position_material(layer=0):
    """A material that emits every surface's world position, for the scan's position pass (the glass the
    rays pass through is hidden from the camera for every pass of the scan: render_frames); layer 1 the
    position of the ray's second strike, for the peel view (rung 2l)."""
    name = "PositionEmit" if layer == 0 else f"PositionEmit{layer}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        g = nt.nodes.new("ShaderNodeNewGeometry")
        nt.links.new(g.outputs["Position"], em.inputs["Color"])
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(_through(nt, em.outputs["Emission"], layer), out.inputs["Surface"])
    return mat


def index_material(layer=0):
    """A material that emits every surface's pass index, its thing's own number, for the scan's index
    pass: the same rays as the position pass, so the two pictures hold the same hits; layer 1 the thing
    of the ray's second strike."""
    name = "IndexEmit" if layer == 0 else f"IndexEmit{layer}"
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        for n in list(nt.nodes):
            nt.nodes.remove(n)
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        em = nt.nodes.new("ShaderNodeEmission")
        info = nt.nodes.new("ShaderNodeObjectInfo")
        comb = nt.nodes.new("ShaderNodeCombineXYZ")
        nt.links.new(info.outputs["Object Index"], comb.inputs["X"])
        nt.links.new(comb.outputs["Vector"], em.inputs["Color"])
        em.inputs["Strength"].default_value = 1.0
        nt.links.new(_through(nt, em.outputs["Emission"], layer), out.inputs["Surface"])
    return mat


class PositionPass:
    """The scan's second render of a frame (rung 2d): every pixel's hit in room metres as a half-float
    EXR, one sample with the position material over everything. The far shell for the sky is always
    in the scene and clear to the colour pass; the window's glass is hidden from the camera for the
    whole chunk, colour and data passes alike. Nothing is hidden or shown between the passes: done
    per frame, that left the shell in the colour pass on runs of frames (persistent data), where the
    rays refracted through the glass leaf reached it and the leaf went black."""

    def __init__(self, scene, folder, layer=0):
        self.scene, self.folder = scene, folder
        self.mat_pos = position_material(layer)
        self.mat_idx = index_material(layer)
        self.vl = scene.view_layers[0]
        if layer > 0:
            scene.cycles.transparent_max_bounces = max(scene.cycles.transparent_max_bounces, layer + 2)

    def render(self, f, pos=True, idx=True):
        """The position picture and the index picture of a frame (rung 2j: the thing of every hit, as
        pass indices), each one sample with its material over everything: the same pattern of rays."""
        sc = self.scene
        c = sc.cycles
        saved = (c.samples, c.use_adaptive_sampling, c.use_denoising)
        c.samples, c.use_adaptive_sampling, c.use_denoising = 1, False, False
        s = sc.render.image_settings
        s.file_format, s.color_mode, s.color_depth, s.exr_codec = "OPEN_EXR", "RGB", "16", "ZIP"
        try:
            for want, mat, stem in ((pos, self.mat_pos, "pos"), (idx, self.mat_idx, "idx")):
                if not want:
                    continue
                self.vl.material_override = mat
                sc.render.filepath = str(self.folder / f"{stem}_{f:04d}.exr")
                bpy.ops.render.render(write_still=True, scene=sc.name)
        finally:
            self.vl.material_override = None
            c.samples, c.use_adaptive_sampling, c.use_denoising = saved


class KnownLight:
    """The known shapes' exposure by frame (2026-11-12): read off the picture that stands in the head that frame
    (held_frames.json's picture: its frame, and how far it stands), by lidarscene.known_exposure on the scan's pictures
    of that frame, times KNOWN_OVER_SEEN; the mind's own light (KNOWN_OWN) where no picture stands, and between the two
    as the first picture comes in. A frame whose scan is not on disk takes the nearest scans' values, either side
    within REACH frames; with none, the mind's own light. The measures are kept in <out>/known_light.json by the
    pictures' paths and times, so a second render reads them back."""
    REACH = 15

    def __init__(self, out, col_dir, colours, room_size, pictures):
        self.out, self.col_dir, self.colours, self.room_size, self.pictures = pathlib.Path(out), pathlib.Path(col_dir), colours, room_size, pictures
        self.cache_path = self.out / "known_light.json"
        self.cache = read_json(self.cache_path) if self.cache_path.exists() else {}
        self.dirty = False
        self.told = set()

    def measure(self, f):
        col = self.col_dir / f"frame_{f:04d}.png"
        idx, pos = self.out / "scan" / f"idx_{f:04d}.exr", self.out / "scan" / f"pos_{f:04d}.exr"
        if not (col.exists() and idx.exists() and pos.exists()) or self.room_size is None:
            return None
        key = str(col)
        stamp = [col.stat().st_mtime, idx.stat().st_mtime]
        hit = self.cache.get(key)
        if hit is None or hit[0] != stamp:
            hit = [stamp, lidarscene.known_exposure(col, idx, pos, self.colours, self.room_size)]
            self.cache[key] = hit
            self.dirty = True
        return hit[1]

    def seen(self, f):
        """The picture's two levels at a frame, indoors and outdoors, from its own scan or the nearest ones."""
        m = self.measure(f)
        if m is None:
            near = []
            for sign in (-1, 1):
                for d in range(1, self.REACH + 1):
                    m2 = self.measure(f + sign * d)
                    if m2 is not None:
                        near.append((d, m2))
                        break
            if not near:
                return None
            if len(near) == 1:
                m = near[0][1]
            else:
                (d0, a), (d1, b) = near
                w = d0 / (d0 + d1)
                m = [None if (a[i] is None or b[i] is None) else a[i] + (b[i] - a[i]) * w for i in range(2)]
        e_in, e_out = m
        if e_in is None and e_out is None:
            return None
        e_in = e_out / lidarscene.KNOWN_OUT_OVER_IN if e_in is None else e_in
        e_out = e_in * lidarscene.KNOWN_OUT_OVER_IN if e_out is None else e_out
        return e_in * lidarscene.KNOWN_OVER_SEEN, e_out * lidarscene.KNOWN_OVER_SEEN

    def at(self, f):
        own = lidarscene.KNOWN_OWN
        picture, stands = self.pictures.get(str(f), [f, 1.0])
        got = self.seen(int(picture)) if picture is not None else None
        if got is None:
            if picture is not None and "none" not in self.told:
                self.told.add("none")
                print(f"RENDER: no scan on disk near frame {picture}; the known shapes there stand in the mind's own light", flush=True)
            return own, own
        return own + (got[0] - own) * stands, own + (got[1] - own) * stands

    def save(self):
        if self.dirty:
            write_json(self.cache_path, self.cache)
            self.dirty = False


def render_frames(args):
    out = pathlib.Path(args.out).resolve()
    beats = read_json(args.beats)
    total = int(round(beats["duration_seconds"] * FPS))
    frames = frame_range(args, total)
    if args.step > 1:
        # a fast test: every Nth frame, counted from the scene's first frame whatever the chunk, and for
        # the scans the picture frames those frames' memories read (held_frames.json, from the bake)
        frames = [f for f in frames if (f - 1) % args.step == 0]
        held = out / "held_frames.json"
        if args.view in SCAN_VIEWS and held.exists():
            by_frame = read_json(held)["by_frame"]
            frames = sorted(set(frames) | {r for f in frames for r in by_frame.get(str(f), [])})
    size = PANEL if not args.size else tuple(int(v) for v in args.size.lower().split("x"))
    if args.view in ("scan", "scan_move", "peel", "pane") and not args.size:
        size = (args.scan_size, args.scan_size)
    elif args.view in ("backdrop", "backdrop_move", "sky", "sky_move") and not args.size:
        side = int(round(args.scan_size * lidarscene.BACKDROP_SHARE))
        size = (side, side)
    is_move = args.view == "move"
    blend = pathlib.Path(args.moves_blend if is_move else args.blend).resolve()
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    exposure = {}
    if args.view in ("third", "first", "scan", "backdrop", "sky", "pane"):
        table = read_json(out / "eye_frames.json")
        key = "exp_third" if args.view == "third" else "exp_first"
        exposure = {r["f"]: r[key] for r in table["rows"]}
    elif args.view in ("scan_move", "backdrop_move", "sky_move"):
        table = read_json(out / "moves_frames.json")
        exposure = {r["f"]: r["scan_exp"] for r in table["moves"][args.move]["rows"] if r.get("scan_exp") is not None}
        frames = [f for f in frames if f in exposure]
    elif is_move and args.pass_ == "room":
        table = read_json(out / "moves_frames.json")
        exposure = {r["f"]: r["exp"] for r in table["moves"][args.move]["rows"]}
        frames = [f for f in frames if f in exposure]
    elif is_move:
        table = read_json(out / "moves_frames.json")
        allowed = {r["f"] for r in table["moves"][args.move]["rows"]}
        frames = [f for f in frames if f in allowed]
    if not frames:
        print("RENDER: nothing to do", flush=True)
        return
    mind = args.view in ("true", "check") or (is_move and args.pass_ == "mind")
    if mind:
        scene = bpy.data.scenes["True"]
        cam = bpy.data.objects["Cam_True"]
        render.setup_eevee(scene, samples=args.eevee_samples)
        if args.view == "check":
            # the check from the eyes (his eleventh review of 2026-11-11): the model through the simulated eyes
            # themselves, which ride the First-Person camera's place and bearing with its lens, so that beside the
            # First-Person picture every splat should sit on its own pixel in its own colour; the mind's own things
            # (the glass, the soul, the sun's ball, the sounds' rings) are hidden, and the frames to compare are
            # ones with the eyes open (the First-Person frames carry no lids)
            cam = bpy.data.objects["Cam_SimEye"]
            own = [ob.name for ob in scene.objects if ob.name in ("Ghost_Head", "Soul", "SunBall", "MiniSoul") or ob.name.startswith("Wave_")]
            for name in own:
                bpy.data.objects[name].hide_render = True
            # and the senses on the simulated body (rung 2p): their switches off, their own objects hidden
            own += lidarscene.senses_off(scene)
            print(f"RENDER check: hidden {own}, the senses off", flush=True)
        # the seen part of the model is the First-Person frames: point the sequence at them
        img = bpy.data.images.get("FirstView")
        first_dir = out / "first"
        if img is not None:
            if (first_dir / "frame_0001.png").exists():
                img.filepath = str(first_dir / "frame_0001.png")
                img.source = "SEQUENCE"
                img.reload()
            missing = [f for f in frames if not (first_dir / f"frame_{f:04d}.png").exists()]
            if missing:
                print(f"RENDER: {len(missing)} First-Person frames are not rendered yet (first {missing[0]}); the model will show them black", flush=True)
        # the eyes' scan (rung 2d): the two sequences point at the scan's frames
        pos_img, col_img = bpy.data.images.get("ScanPos"), bpy.data.images.get("ScanColour")
        for idx_name, idx_folder in (("ScanIdx", "scan"), ("BackIdx", "backdrop"), ("SkyIdx", "sky"), ("PeelIdx", "peel"), ("PaneIdx", "pane")):
            idx_img = bpy.data.images.get(idx_name)
            if idx_img is not None:
                found_idx = lidarscene.repoint(idx_img, out / idx_folder, "idx_*.exr")
                have_idx = {int(q.stem.split("_")[1]) for q in found_idx}
                missing_idx = [f for f in frames if f not in have_idx]
                if missing_idx:
                    print(f"RENDER: {len(missing_idx)} {idx_folder} index frames are not rendered yet (first {missing_idx[0]}); every hit there is held piece by piece", flush=True)
        pane_pos, pane_col = bpy.data.images.get("PanePos"), bpy.data.images.get("PaneColour")
        if pane_pos is not None and pane_col is not None:
            found = lidarscene.repoint(pane_pos, out / "pane", "pos_*.exr")
            lidarscene.repoint(pane_col, out / "pane", "frame_*.png")
            have = {int(q.stem.split("_")[1]) for q in found}
            missing = [f for f in frames if f not in have]
            if missing:
                print(f"RENDER: {len(missing)} pane frames are not rendered yet (first {missing[0]}); no reflections there", flush=True)
        peel_pos = bpy.data.images.get("PeelPos")
        if peel_pos is not None:
            found = lidarscene.repoint(peel_pos, out / "peel", "pos_*.exr")
            have = {int(q.stem.split("_")[1]) for q in found}
            missing = [f for f in frames if f not in have]
            if missing:
                print(f"RENDER: {len(missing)} peel frames are not rendered yet (first {missing[0]}); no far sides there", flush=True)
        if pos_img is not None and col_img is not None:
            found = lidarscene.repoint(pos_img, out / "scan", "pos_*.exr")
            lidarscene.repoint(col_img, out / "scan", "frame_*.png")
            have = {int(q.stem.split("_")[1]) for q in found}
            missing = [f for f in frames if f not in have]
            if missing:
                print(f"RENDER: {len(missing)} scan frames are not rendered yet (first {missing[0]}); the model will show nothing there", flush=True)
            if is_move:
                # the move's own scan at the road's exposure, where it exists for every frame
                mv = out / "scan_move"
                if all((mv / f"frame_{f:04d}.png").exists() for f in frames):
                    lidarscene.repoint(col_img, mv, "frame_*.png")
                    print("RENDER: the model's picture through the move is the move scan (the road's exposure)", flush=True)
        # the backdrop scan's two sequences, and the move's own backdrop at the road's exposure
        back_pos, back_col = bpy.data.images.get("BackPos"), bpy.data.images.get("BackColour")
        if back_pos is not None and back_col is not None:
            found = lidarscene.repoint(back_pos, out / "backdrop", "pos_*.exr")
            lidarscene.repoint(back_col, out / "backdrop", "frame_*.png")
            have = {int(q.stem.split("_")[1]) for q in found}
            missing = [f for f in frames if f not in have]
            if missing:
                print(f"RENDER: {len(missing)} backdrop frames are not rendered yet (first {missing[0]}); the backdrop will be missing there", flush=True)
            if is_move:
                mv = out / "backdrop_move"
                if all((mv / f"frame_{f:04d}.png").exists() for f in frames):
                    lidarscene.repoint(back_col, mv, "frame_*.png")
                    print("RENDER: the backdrop through the move is the move's backdrop (the road's exposure)", flush=True)
        # the sky scan's two sequences (rung 2i), and the move's own at the road's exposure
        sky_pos, sky_col = bpy.data.images.get("SkyPos"), bpy.data.images.get("SkyColour")
        if sky_pos is not None and sky_col is not None:
            found = lidarscene.repoint(sky_pos, out / "sky", "pos_*.exr")
            lidarscene.repoint(sky_col, out / "sky", "frame_*.png")
            have = {int(q.stem.split("_")[1]) for q in found}
            missing = [f for f in frames if f not in have]
            if missing:
                print(f"RENDER: {len(missing)} sky frames are not rendered yet (first {missing[0]}); the remembered sky will be missing there", flush=True)
            if is_move:
                mv = out / "sky_move"
                if all((mv / f"frame_{f:04d}.png").exists() for f in frames):
                    lidarscene.repoint(sky_col, mv, "frame_*.png")
                    print("RENDER: the sky through the move is the move's sky (the road's exposure)", flush=True)
        if args.view == "true":
            # the piece's own True-Person frames at 1920 by 648, or the 16:9 frames of the showcase
            folder = out / (args.to or ("true" if size == (1920, 648) else "true16"))
            for name in (args.hide.split(",") if args.hide else []):
                bpy.data.objects[name].hide_render = True
            if args.hide:
                print(f"RENDER true: left out {args.hide}", flush=True)
        elif args.view == "check":
            folder = out / "check"
        else:
            folder = out / "moves" / args.move / "mind"
    else:
        scene = bpy.data.scenes["Room"]
        cam = bpy.data.objects[{"third": "Cam_Third", "first": "Cam_First", "move": "Cam_Move", "scan": "Cam_Scan", "scan_move": "Cam_Scan",
                                "backdrop": "Cam_Scan", "backdrop_move": "Cam_Scan", "sky": "Cam_Scan", "sky_move": "Cam_Scan",
                                "peel": "Cam_Scan", "pane": "Cam_Scan"}[args.view]]
        render.setup_cycles(scene, samples=args.samples, adaptive=True, denoise=not args.no_denoise)
        scene.cycles.adaptive_threshold = 0.05
        scene.cycles.max_bounces = 6
        scene.render.use_persistent_data = True
        head = bpy.data.objects["Man_Head"]
        if not is_move:
            for name in ("Man_Head", "ManO_eye_l", "ManO_eye_r"):
                if name in bpy.data.objects:
                    bpy.data.objects[name].visible_camera = args.view == "third"
        if args.view in SCAN_VIEWS:
            # every scan picture is point sampled: the pixel filter at its narrowest, so a pixel's colour
            # is the colour of the one surface at its centre, the surface its position and index name,
            # and not a blend over the filter's width with what stands beside it (his eighth review of
            # 2026-11-10: the frame's white and the ground's grey bled a dotted rim onto the far surface
            # behind every silhouette, seen from any camera off the eyes)
            scene.render.filter_size = 0.01
            # the glass the eyes' rays pass through (tv_pass) is not there to the scan's camera rays, in
            # the colour pass and the data passes alike, as it is not to the engine's rays: the mind's
            # picture holds what lies beyond it, not the pane's reflections (his seventh review of
            # 2026-11-10: the glass's picture of the sun was painted onto the ground). The First-Person
            # view keeps the real glass.
            passed = [ob.name for ob in scene.objects if ob.get(tags.PASS_PROP)]
            if args.view == "pane":
                # the pane view (rung 2o): the glass alone before the camera, reflecting the scene, which its glossy rays
                # see and the camera's do not; the model's glass layer places these reflections at the pane's own depth
                refl = reflection_material()
                for ob in scene.objects:
                    if ob.type == "MESH" and ob.name not in passed:
                        ob.visible_camera = False
                for name in passed:
                    ob = bpy.data.objects[name]
                    ob.visible_camera = True
                    for i in range(len(ob.data.materials)):
                        ob.data.materials[i] = refl
                # the world is black to the camera (a transparent film), so off the glass the colour, the position and
                # the index pictures hold nothing, while the glass still reflects the sky its glossy rays see
                scene.render.film_transparent = True
                print(f"RENDER pane: the glass alone, reflecting: {passed}", flush=True)
            else:
                for name in passed:
                    bpy.data.objects[name].visible_camera = False
                print(f"RENDER {args.view}: clear to the rays: {passed}", flush=True)
        if args.view in ("backdrop", "backdrop_move", "sky", "sky_move"):
            # the backdrop (rung 2h): the sky, the ground and the range alone, everything nearer hidden
            # for the whole chunk, never shown and hidden per frame (under persistent data that left
            # the far shell in the colour pass, found 2026-11-08); the sky view (rung 2i): the shell alone
            keep = {"SkyShell", "Ground", "Range"} if args.view.startswith("backdrop") else {"SkyShell"}
            hidden = [ob.name for ob in scene.objects if ob.type == "MESH" and ob.name not in keep and not ob.hide_render]
            for name in hidden:
                bpy.data.objects[name].hide_render = True
            print(f"RENDER {args.view}: {len(hidden)} objects hidden, {sorted(keep)} kept", flush=True)
        folder = out / args.view if not is_move else out / "moves" / args.move / "room"
    bpy.context.window.scene = scene
    folder.mkdir(parents=True, exist_ok=True)
    scene.camera = cam
    shapes_ng = bpy.data.node_groups.get("MemoryShapesNodes") if mind else None
    # the known light is read off the picture that stands in the head (2026-11-12, lidarscene.known_exposure): the
    # brightness of the eyes' own scan of that picture's frame, indoors and outdoors, in the colour pictures the model
    # itself shows (the move's own scan through a move); the mind's own light where no picture stands
    known_light = None
    if shapes_ng is not None:
        held_path = out / "held_frames.json"
        pictures = read_json(held_path).get("picture", {}) if held_path.exists() else {}
        col_dir = pathlib.Path(bpy.path.abspath(bpy.data.images["ScanColour"].filepath)).parent if "ScanColour" in bpy.data.images else out / "scan"
        table_obj = bpy.data.objects.get("ThingTable")
        colours = [c.color[:3] for c in table_obj.data.attributes["colour"].data] if table_obj is not None else []
        room_size = tuple(table_obj["room_size"]) if (table_obj is not None and "room_size" in table_obj.keys()) else None
        known_light = KnownLight(out, col_dir, colours, room_size, pictures)
    render.set_output(scene, size, str(folder / "frame_0000.png"))
    if getattr(args, "border", None):
        x0, y0, x1, y1 = (float(v) for v in args.border.split(","))
        scene.render.use_border, scene.render.use_crop_to_border = True, True
        scene.render.border_min_x, scene.render.border_max_x = x0 / size[0], x1 / size[0]
        scene.render.border_min_y, scene.render.border_max_y = 1.0 - y1 / size[1], 1.0 - y0 / size[1]
    done, skipped = 0, 0
    t0 = time.perf_counter()
    times = []
    mon = render.GpuMonitor().start()
    # the peel view (rung 2l) writes the position and the index of the ray's second strike, no colour
    pos_pass = PositionPass(scene, folder, layer=1 if args.view == "peel" else 0) if args.view in DATA_VIEWS else None
    has_colour = args.view != "peel"
    # with the lids fully shut the eyes take nothing in: the scan of such a frame is the scan of the last frame before
    # it on which they were open (cover under 0.1, the frame the last picture is of), its files copied (the model keys
    # the place the picture was taken from the same way: triview/lidarscene.py, pic_frame). Before the eyes' first
    # opening there is no such frame: rendered as it is
    taken_at, copied = {}, 0
    scan_files = (["frame_{:04d}.png"] if has_colour else []) + ["pos_{:04d}.exr", "idx_{:04d}.exr"]
    if args.view in DATA_VIEWS:
        cover = {r["f"]: float(r["cover"]) for r in read_json(out / "eye_frames.json")["rows"]}
        last = None
        for f in sorted(cover):
            if cover[f] < 0.1:
                last = f
            elif cover[f] >= 0.999 and last is not None:
                taken_at[f] = last
        # a frame whose scan is another's needs that one's files: rendered here too where they are missing
        frames = sorted(set(frames) | {taken_at[f] for f in frames if f in taken_at
                                        and not all((folder / n.format(taken_at[f])).exists() for n in scan_files)})
    for f in frames:
        if f in taken_at:
            for n in scan_files:
                src = folder / n.format(taken_at[f])
                if src.exists():
                    shutil.copyfile(src, folder / n.format(f))
            copied += 1
            continue
        path = folder / f"frame_{f:04d}.png"
        # each picture of a frame is rendered only if it is missing: the colour, the position, the index
        # (an index pass added to a scan rendered before it costs the index alone)
        need_col = has_colour and (args.overwrite or not path.exists())
        need_pos = pos_pass is not None and (args.overwrite or not (folder / f"pos_{f:04d}.exr").exists())
        need_idx = pos_pass is not None and (args.overwrite or not (folder / f"idx_{f:04d}.exr").exists())
        if not (need_col or need_pos or need_idx):
            skipped += 1
            continue
        ts = time.perf_counter()
        if mind and args.no_frame_set:
            scene.frame_current = f
        else:
            scene.frame_set(f)
        set_s = time.perf_counter() - ts
        if f in exposure:
            scene.view_settings.exposure = exposure[f]
        if shapes_ng is not None:
            e_in, e_out = known_light.at(f)
            shapes_ng.nodes["Exposure"].outputs[0].default_value = e_in
            shapes_ng.nodes["ExposureOut"].outputs[0].default_value = e_out
        tf = time.perf_counter()
        if need_col:
            scene.render.filepath = str(path)
            bpy.ops.render.render(write_still=True, scene=scene.name)
        if need_pos or need_idx:
            pos_pass.render(f, pos=need_pos, idx=need_idx)
            render.set_output(scene, size, str(folder / "frame_0000.png"))
        times.append(time.perf_counter() - tf)
        done += 1
        if args.profile:
            dg = bpy.context.evaluated_depsgraph_get()
            rows = sorted(((m.execution_time, ob.name, m.name) for ob in scene.objects for m in ob.evaluated_get(dg).modifiers), reverse=True)
            print(f"PROFILE {args.view} {f}: set {set_s:.2f} s, render {times[-1]:.2f} s; modifiers worked out in {sum(r[0] for r in rows):.2f} s: "
                  + "; ".join(f"{n}/{m} {t:.2f}" for t, n, m in rows[:14]), flush=True)
        if done % 25 == 0:
            print(f"RENDER {args.view}: frame {f}, {done} done, {times[-1]:.2f} s/frame", flush=True)
    if known_light is not None:
        known_light.save()
    gpu = mon.stop()
    total_s = time.perf_counter() - t0
    label = args.view if not is_move else f"{args.move}:{args.pass_}"
    if args.view in ("scan_move", "backdrop_move", "sky_move"):
        label = f"{args.view}:{args.move}"
    rec = {"view": label, "frames": [frames[0], frames[-1]], "rendered": done, "skipped": skipped, "copied": copied,
           "seconds": round(total_s, 1), "per_frame_mean": round(sum(times) / len(times), 3) if times else None,
           "per_frame_first": round(times[0], 2) if times else None, "gpu": gpu, "size": list(size),
           "engine": scene.render.engine, "samples": args.samples if not mind else args.eevee_samples}
    with open(out / "render_log.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    print("CHUNK:", json.dumps(rec), flush=True)


def chain_fps(beats):
    """Frames per chain second: the render's rate over the chain's pace (data/beats.json pace, 1 by default)."""
    return RENDER_FPS / float(beats.get("pace", 1.0))


def main():
    global FPS
    args = parse_args()
    FPS = chain_fps(read_json(args.beats))
    try:
        if args.mode == "build":
            build(args)
        else:
            render_frames(args)
    except Exception:
        # Blender exits 0 after a script's traceback; the driver needs a real failure code
        import traceback
        traceback.print_exc()
        sys.stdout.flush()
        sys.exit(1)


if __name__ == "__main__":
    main()

"""Sensory Tri-View, rung 3: the man.

    blender -b --python rungs/rung3.py -- man   [--blend scenes/rung3_man.blend] [--skin NAME] [--race a,c,f] [--look PNG]
    blender -b --python rungs/rung3.py -- look  [--blend scenes/rung3_man.blend] --look PNG [--samples 128]
    blender -b --python rungs/rung3.py -- sill  [--record scenes/rung2p_r14m51.blend] [--man scenes/rung3_man.blend] [--blend scenes/rung3_sill.blend]
    blender -b --python rungs/rung3.py -- still --view third|first --frame 1996 --look PNG [--blend scenes/rung3_sill.blend] [--samples 256]

man:   generate him with the open-source generator (triview/man.py) in the generator's rest pose and save the file.
       With --look, also render a first look at his head under the sill's light.
look:  open a saved file and render that look again.
sill:  open the scene of record (never saved over), bring the man in, tie his skeleton to the mannequin's joint points
       (triview/mansill.py), leave the mannequin out of the pictures, and save the result as its own file.
still: one frame of that file through the Third-Person camera or the camera on his eyes, at the exposure the eye table
       holds for the frame.
turn:  the frames --frame to --frame-end of that file through the Third-Person camera into --out as frame_<n>.png, each
       at the eye table's exposure for its frame. A picture on disk is not rendered again, so a run that was stopped
       carries on where it was (tools/rung3_turn.py runs it in parts under the heat guard and joins the video).

Every render's time and graphics memory go to renders/rung3/frame_costs.json (rungs 5 and 6 need the numbers).
A Python error ends Blender with a failing code (Blender itself exits with 0 after one).
"""
import argparse
import json
import pathlib
import sys
import time
import traceback

import bpy

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

COSTS = ROOT / "renders" / "rung3" / "frame_costs.json"


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description="Sensory Tri-View rung 3")
    ap.add_argument("mode", choices=("man", "look", "sill", "still", "turn"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung3_man.blend"))
    ap.add_argument("--spec", default="a", choices=("a", "b", "c"), help="man: which man of triview/man.py (a: the first; b: the bearded one with the swept-back hair; c: b with a European face, a trained body and a barbered beard)")
    ap.add_argument("--aim-down", type=float, default=0.0, help="look: metres under his head's middle the look's camera aims at and stands level with (0.55 with --distance 2.6 shows his body)")
    ap.add_argument("--round", type=float, default=61.0, help="look: degrees round to his right the look's camera stands (61: the Third-Person camera's place at the sill)")
    ap.add_argument("--distance", type=float, default=0.808, help="look: metres from his head's middle")
    ap.add_argument("--skin", default=None, help="the generator's skin by name, in place of the picked one")
    ap.add_argument("--race", default=None, help="asian,caucasian,african shares of his build and face, summing to 1")
    ap.add_argument("--look", default=None, help="a PNG to render a first look at his head to")
    ap.add_argument("--samples", type=int, default=128)
    ap.add_argument("--record", default=str(ROOT / "scenes" / "rung2p_r14m51.blend"), help="sill: the scene of record he is brought into")
    ap.add_argument("--man", default=str(ROOT / "scenes" / "rung3_man.blend"), help="sill: his own file")
    ap.add_argument("--view", default="third", choices=("third", "first", "field", "qa", "face", "eye"))
    ap.add_argument("--cover", type=float, default=None, help="look, still: set his lids to this cover (0 open, 1 shut) in place of the eye table's")
    ap.add_argument("--frame", type=int, default=1996)
    ap.add_argument("--frame-end", type=int, default=None, help="turn: the last frame of the run")
    ap.add_argument("--step", type=int, default=1, help="turn: every how many frames (a rough takes a larger step)")
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung3" / "turn" / "frames"), help="turn: the folder of the run's pictures")
    ap.add_argument("--exposure-offset", type=float, default=0.0,
                    help="still: stops added to the eye table's exposure for the frame (the table was set on the dark mannequin in a room mostly in shade; a sunlit face needs less)")
    ap.add_argument("--eye-table", default=str(ROOT / "renders" / "rung2p" / "eye_frames.json"))
    ap.add_argument("--size", default="1920x864")
    ap.add_argument("--exposure", type=float, default=-1.6, help="the look's exposure in stops")
    ap.add_argument("--note", default="", help="a word on what this render is, for the cost record")
    ap.add_argument("--denoiser", default="optix", choices=("optix", "oidn"),
                    help="what cleans the picture's grain: optix as the engine's pictures use, or oidn (Open Image Denoise, guided by "
                         "the surface's own colour and direction), which keeps more of fine skin relief")
    args = ap.parse_args(argv)
    # every path absolute: Blender resolves a relative one against the drive's root while no file is open
    # (the first look of 2026-11-19 went to C:\renders that way)
    if args.mode in ("sill", "still", "turn") and pathlib.Path(args.blend).name == "rung3_man.blend":
        args.blend = str(ROOT / "scenes" / "rung3_sill.blend")
    args.blend = str(pathlib.Path(args.blend).resolve())
    args.record, args.man = str(pathlib.Path(args.record).resolve()), str(pathlib.Path(args.man).resolve())
    if args.look:
        args.look = str(pathlib.Path(args.look).resolve())
    return args


def denoiser(scene, args):
    """The man's pictures may be cleaned by Open Image Denoise in place of OptiX (--denoiser oidn)."""
    if getattr(args, "denoiser", "optix") == "oidn":
        c = scene.cycles
        c.denoiser = "OPENIMAGEDENOISE"
        c.denoising_input_passes = "RGB_ALBEDO_NORMAL"
        c.denoising_prefilter = "ACCURATE"
        c.denoising_use_gpu = True


def record_cost(row):
    data = json.loads(COSTS.read_text(encoding="utf-8")) if COSTS.exists() else {"note": "", "rows": []}
    data["rows"].append(row)
    COSTS.write_text(json.dumps(data, indent=1), encoding="utf-8")


def look(args, scene, rig, what):
    from triview import man, render
    cam = bpy.data.objects.get("PreviewCam") or man.preview_setup(scene, rig)
    if args.cover is not None:
        from triview import manlids
        manlids.pose(rig, args.cover)
    if (args.round, args.distance, args.aim_down) != (61.0, 0.808, 0.0):
        # the same look from another side: the camera moved round his head, still aimed at its middle
        import math
        from mathutils import Vector
        c = man.head_centre(rig) - Vector((0.0, 0.0, args.aim_down))
        a = math.radians(args.round)
        cam.location = c + (Vector((0.0, -1.0, 0.0)) * math.cos(a) + Vector((-1.0, 0.0, 0.0)) * math.sin(a)) * args.distance + Vector((0.0, 0.0, -0.055))
        cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    size = tuple(int(v) for v in args.size.split("x"))
    render.setup_cycles(scene, samples=args.samples, adaptive=True, denoise=True)
    denoiser(scene, args)
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    info = render.render_view(scene, cam, size, args.look, exposure=args.exposure, label="look")
    row = {"date": time.strftime("%Y-%m-%d"), "what": what + (": " + args.note if args.note else ""), "scene": pathlib.Path(args.blend).name,
           "view": "a first look, the Third-Person camera's place at the sill relative to his head, rest pose, preview sky",
           "size": list(size), "samples": args.samples, "adaptive_threshold": 0.01, "max_bounces": 8, "denoised": True,
           "seconds": info["seconds"], "gpu_peak_mb": info["gpu"]["peak_mb"], "gpu_baseline_mb": info["gpu"]["baseline_mb"],
           "exposure": args.exposure, "picture": str(pathlib.Path(args.look).resolve().relative_to(ROOT)).replace("\\", "/")}
    record_cost(row)
    print("LOOK:", json.dumps(row), flush=True)


def sill(args):
    from triview import mansill
    bpy.ops.wm.open_mainfile(filepath=args.record)
    scene = bpy.data.scenes["Room"]
    bpy.context.window.scene = scene
    rig, obs = mansill.append_man(args.man, scene)
    mansill.straighten(rig)
    helpers = mansill.place(scene, rig)
    hidden = mansill.hide_mannequin(scene)
    # his lids follow the eye table's cover, the number the First-Person view draws its own lids from
    from triview import manlids
    rows = json.loads(pathlib.Path(args.eye_table).read_text(encoding="utf-8"))["rows"]
    print(f"SILL: his lids keyed on {manlids.bake(rig, rows)} frames of {len(rows)} from the eye table", flush=True)
    print(f"SILL: {len(obs)} of his objects brought in, {len(helpers)} helpers, {len(hidden)} mannequin shapes left out of the pictures", flush=True)
    for f in (args.frame, 1, 1500, 3200):
        scene.frame_set(f)
        print(f"SILL frame {f}: his joints from the mannequin's points, mm: {json.dumps(mansill.report(scene, rig))}", flush=True)
    scene.frame_set(args.frame)
    own = (rig.matrix_world @ rig.data.bones["upperarm01.L"].head_local - rig.matrix_world @ rig.data.bones["upperarm01.R"].head_local).length
    theirs = (bpy.data.objects["Man_shoulder_l"].matrix_world.translation - bpy.data.objects["Man_shoulder_r"].matrix_world.translation).length
    print(f"SILL: the mannequin's shoulder points stand {theirs * 1000:.0f} mm apart at frame {args.frame}; his own shoulder joints {own * 1000:.0f} mm in his rest pose", flush=True)
    bpy.ops.wm.save_as_mainfile(filepath=args.blend)
    print("SAVED:", args.blend, flush=True)


def still(args):
    from triview import render
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.data.scenes["Room"]
    bpy.context.window.scene = scene
    row = next(r for r in json.loads(pathlib.Path(args.eye_table).read_text(encoding="utf-8"))["rows"] if r["f"] == args.frame)
    size = tuple(int(v) for v in args.size.split("x"))
    if args.view == "qa":
        # a checking view of his whole figure, from behind his right shoulder
        from mathutils import Vector
        scene.frame_set(args.frame)
        chest = bpy.data.objects["Man_chest"].matrix_world.translation.copy()
        data = bpy.data.cameras.new("Cam_QA")
        data.lens = 30.0
        cam = bpy.data.objects.new("Cam_QA", data)
        scene.collection.objects.link(cam)
        cam.location = chest + Vector((-1.75, -0.95, 0.2))      # inside the room: its south wall is 1.2 m to his right
        cam.rotation_euler = (chest + Vector((0.0, 0.0, -0.25)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        exposure = float(row["exp_third"]) + args.exposure_offset
    else:
        cam = bpy.data.objects[{"third": "Cam_Third", "first": "Cam_First", "field": "Cam_Scan", "face": "Cam_Third", "eye": "Cam_Third"}[args.view]]
        exposure = float(row["exp_third" if args.view in ("third", "face", "eye") else "exp_first"]) + args.exposure_offset
    if args.view == "face":
        # a close look at his face: the Third-Person camera's direction, a third of its distance from his head
        from mathutils import Vector
        scene.frame_set(args.frame)
        third = bpy.data.objects["Cam_Third"]
        head = bpy.data.objects["Man_head"].matrix_world.translation.copy()
        data = bpy.data.cameras.new("Cam_Face")
        data.lens = 60.0
        cam = bpy.data.objects.new("Cam_Face", data)
        scene.collection.objects.link(cam)
        away = third.matrix_world.translation - head
        cam.location = head + away.normalized() * 0.55
        cam.rotation_euler = (head + Vector((0.0, 0.0, 0.01)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        exposure = float(row["exp_third"]) + args.exposure_offset
    if args.view == "eye":
        # a very close look at his right eye (the one toward the Third-Person camera), from that camera's direction:
        # 11 cm of his face across the picture
        from mathutils import Vector
        scene.frame_set(args.frame)
        rig = next(ob for ob in scene.objects if ob.type == "ARMATURE" and ob.get("tv_man"))
        bpy.context.view_layer.update()
        eye = rig.matrix_world @ rig.pose.bones["eye.R"].head
        third = bpy.data.objects["Cam_Third"]
        data = bpy.data.cameras.new("Cam_Eye")
        data.lens = 150.0
        cam = bpy.data.objects.new("Cam_Eye", data)
        scene.collection.objects.link(cam)
        away = third.matrix_world.translation - eye
        cam.location = eye + away.normalized() * 0.45
        cam.rotation_euler = (eye + Vector((0.0, 0.0, -0.006)) - cam.location).to_track_quat("-Z", "Y").to_euler()
        exposure = float(row["exp_third"]) + args.exposure_offset
    if args.view in ("first", "field"):
        # the camera sits inside his head: what lies within 11 cm of it is not drawn (it still casts its shadow)
        cam.data.clip_start = 0.11
    if args.view == "field":
        # his eyes' whole field: the 200 degree fisheye the passed First-Person view is cut from, a square picture
        size = (1024, 1024)
    render.setup_cycles(scene, samples=args.samples, adaptive=True, denoise=True)
    denoiser(scene, args)
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    scene.render.use_persistent_data = False
    scene.frame_set(args.frame)
    if args.cover is not None:
        # try a lid position on this frame: the keys are muted for the render, the bones set by hand
        from triview import manlids
        rig = next(ob for ob in scene.objects if ob.type == "ARMATURE" and ob.get("tv_man"))
        if rig.animation_data is not None:
            rig.animation_data.action = None
        manlids.pose(rig, args.cover)
    info = render.render_view(scene, cam, size, args.look, exposure=exposure, label=args.view)
    out = {"date": time.strftime("%Y-%m-%d"), "what": "the man at the sill" + (": " + args.note if args.note else ""),
           "scene": pathlib.Path(args.blend).name + ", scene Room", "view": args.view, "frame": args.frame,
           "scene_second": round((args.frame - 1) / 30.0, 2), "player_second": round((args.frame - 1) / 24.0, 1),
           "size": list(size), "samples": args.samples, "adaptive_threshold": 0.01, "max_bounces": 8, "denoised": True,
           "seconds": info["seconds"], "gpu_peak_mb": info["gpu"]["peak_mb"], "gpu_baseline_mb": info["gpu"]["baseline_mb"],
           "exposure": exposure, "picture": str(pathlib.Path(args.look).resolve().relative_to(ROOT)).replace("\\", "/")}
    record_cost(out)
    print("STILL:", json.dumps(out), flush=True)


def turn(args):
    """A run of frames through the Third-Person camera: what is missing of --frame to --frame-end, one picture a frame.
    Each frame's seconds and graphics memory go to <out>/../frames.json, and the run's mean to the rung's cost record."""
    from triview import render
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    last = args.frame if args.frame_end is None else args.frame_end
    todo = [f for f in range(args.frame, last + 1, args.step) if not (out / f"frame_{f:04d}.png").exists()]
    print(f"TURN: frames {args.frame} to {last}, step {args.step}: {len(todo)} to render into {out}", flush=True)
    if not todo:
        return
    bpy.ops.wm.open_mainfile(filepath=args.blend)
    scene = bpy.data.scenes["Room"]
    bpy.context.window.scene = scene
    rows = {r["f"]: r for r in json.loads(pathlib.Path(args.eye_table).read_text(encoding="utf-8"))["rows"]}
    cam = bpy.data.objects["Cam_Third"]
    size = tuple(int(v) for v in args.size.split("x"))
    render.setup_cycles(scene, samples=args.samples, adaptive=True, denoise=True)
    denoiser(scene, args)
    scene.cycles.adaptive_threshold = 0.01
    scene.cycles.max_bounces = 8
    scene.render.use_persistent_data = False
    log = out.parent / (out.name + ".json")
    made = json.loads(log.read_text(encoding="utf-8")) if log.exists() else []
    mine = []
    for f in todo:
        if (out.parent / "STOP").exists():
            print("TURN: a file named STOP was found; ending before frame", f, flush=True)
            break
        scene.frame_set(f)
        exposure = float(rows[f]["exp_third"]) + args.exposure_offset
        tmp = out / f"making_{f:04d}.png"                      # a picture cut off while being written never counts as made
        info = render.render_view(scene, cam, size, str(tmp), exposure=exposure, label="turn", quiet=True)
        tmp.replace(out / f"frame_{f:04d}.png")
        row = {"f": f, "scene_second": round((f - 1) / 30.0, 2), "player_second": round((f - 1) / 24.0, 2), "samples": args.samples,
               "seconds": info["seconds"], "gpu_peak_mb": info["gpu"]["peak_mb"], "exposure": round(exposure, 3), "cover": rows[f].get("cover", 0.0)}
        made.append(row)
        mine.append(row)
        log.write_text(json.dumps(made, indent=1), encoding="utf-8")
        print("TURN:", json.dumps(row), flush=True)
    if mine:
        record_cost({"date": time.strftime("%Y-%m-%d"), "what": "the man's turn at the sill" + (": " + args.note if args.note else ""),
                     "scene": pathlib.Path(args.blend).name + ", scene Room", "view": "third", "frames": [mine[0]["f"], mine[-1]["f"]],
                     "count": len(mine), "size": list(size), "samples": args.samples, "adaptive_threshold": 0.01, "max_bounces": 8,
                     "denoised": True, "seconds": round(sum(r["seconds"] for r in mine) / len(mine), 2),
                     "gpu_peak_mb": max(r["gpu_peak_mb"] for r in mine), "picture": str(out.relative_to(ROOT)).replace("\\", "/")})


def main():
    args = parse_args()
    if args.mode == "sill":
        return sill(args)
    if args.mode == "turn":
        return turn(args)
    if args.mode == "still":
        return still(args)
    from triview import man
    if args.mode == "man":
        bpy.ops.wm.read_factory_settings(use_empty=True)
        scene = bpy.context.scene
        spec = dict(man.SPECS[args.spec])
        if args.skin:
            spec["skin"] = args.skin
        if args.race:
            a, c, f = (float(v) for v in args.race.split(","))
            spec["macro"] = dict(spec["macro"], race={"asian": a, "caucasian": c, "african": f})
        t0 = time.perf_counter()
        parts = man.generate(spec)
        body, rig = parts["body"], parts["rig"]
        print(f"MAN: generated in {time.perf_counter() - t0:.1f} s; the sliders alone gave {parts['slider_height']} m, scaled by "
              f"{parts['scale'] / 0.1:.4f} to a crown at {man.crown_height(body):.3f} m", flush=True)
        print(f"MAN: body {len(body.data.vertices)} vertices, {len(body.data.polygons)} faces; skeleton {len(rig.data.bones)} bones; "
              f"head's middle {tuple(round(v, 3) for v in man.head_centre(rig))}", flush=True)
        b = rig.data.bones
        wide = (rig.matrix_world @ b["upperarm01.L"].head_local - rig.matrix_world @ b["upperarm01.R"].head_local).length
        print(f"MAN: his shoulder joints stand {wide * 1000:.0f} mm apart; his eyes {man.eyes_point(rig).z:.3f} m up", flush=True)
        for key in ("eyes", "lashes", "brows", "teeth", "tongue"):
            if key in parts:
                print(f"MAN: {key}: {parts[key].name}, {len(parts[key].data.vertices)} vertices", flush=True)
        for ob in parts["clothes"]:
            print(f"MAN: wears {ob['tv_garment']}: {ob.name}, {len(ob.data.vertices)} vertices", flush=True)
        if "hem" in parts:
            print(f"MAN: the shirt's hem: {parts['hem']}", flush=True)
        if "steady_brows" in parts:
            print(f"MAN: {parts['steady_brows']} skin points under his brows handed from the upper lid's bone to the head's", flush=True)
        if "under_clothes" in parts:
            print(f"MAN: {parts['under_clothes']} points of his body lie under his clothes and are not drawn; body modifiers {[m.name for m in body.modifiers]}", flush=True)
        print("MAN: materials: " + ", ".join(sorted({s.material.name for ob in scene.objects if ob.type == "MESH" for s in ob.material_slots if s.material})), flush=True)
        if args.look:
            look(args, scene, rig, f"the generated man, skin {spec['skin']}")
        blend = pathlib.Path(args.blend).resolve()
        blend.parent.mkdir(parents=True, exist_ok=True)
        bpy.ops.file.pack_all()
        bpy.ops.wm.save_as_mainfile(filepath=str(blend))
        print("SAVED:", blend, flush=True)
    elif args.mode == "look":
        bpy.ops.wm.open_mainfile(filepath=str(pathlib.Path(args.blend).resolve()))
        rig = next(ob for ob in bpy.data.objects if ob.type == "ARMATURE" and ob.get("tv_man"))
        look(args, bpy.context.scene, rig, "the saved man")


try:
    main()
except Exception:
    traceback.print_exc()
    sys.exit(1)

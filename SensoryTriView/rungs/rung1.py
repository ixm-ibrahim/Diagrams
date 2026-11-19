"""Rung 1: the engine. The scene blocked over the whole chain, the sense timeline as data,
the True-Person view computed by the rules and baked, rendered at low resolution.

Run inside Blender from the project folder, absolute paths for every output:

  build:   blender.exe -b --python rungs/rung1.py -- build [--blend <abs .blend>] [--out <abs folder>]
  render:  blender.exe -b --python rungs/rung1.py -- render --view true --frames 1-300 [--blend ...] [--out ...]
           --view third renders the EEVEE Third-Person proxy from the Room scene.
           Frames already on disk are skipped, so a chunk can be rerun after a crash.

tools/run_rung1.py drives build, the chunks and the assembly from outside Blender.
"""
import argparse
import json
import pathlib
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import bpy  # noqa: E402

from triview import anim, body, engine, mindscene, render, room, tags  # noqa: E402

FPS = 24
TRUE_SIZE = (1920, 648)
THIRD_SIZE = (960, 432)


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description="Sensory Tri-View rung 1")
    ap.add_argument("mode", choices=("build", "render"))
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung1"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung1.blend"))
    ap.add_argument("--senses", default=str(ROOT / "data" / "senses.json"))
    ap.add_argument("--beats", default=str(ROOT / "data" / "beats.json"))
    ap.add_argument("--frames", default=None, help="a-b or a,b,c; default the whole scene")
    ap.add_argument("--view", default="true", choices=("true", "third"))
    ap.add_argument("--eevee-samples", type=int, default=24)
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--no-bloom", action="store_true")
    ap.add_argument("--overwrite", action="store_true")
    return ap.parse_args(argv)


def frame_range(args, beats):
    total = int(round(beats["duration_seconds"] * FPS))
    if args.frames:
        if "," in args.frames:
            return [int(v) for v in args.frames.split(",") if v.strip()]
        a, b = (int(v) for v in args.frames.split("-"))
        return list(range(max(1, a), min(total, b) + 1))
    return list(range(1, total + 1))


def build(args):
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    blend = pathlib.Path(args.blend).resolve()
    blend.parent.mkdir(parents=True, exist_ok=True)
    senses = engine.load_senses(args.senses)
    beats = json.loads(pathlib.Path(args.beats).read_text(encoding="utf-8"))
    frames = frame_range(args, beats)
    timings = {"blender": bpy.app.version_string, "frames": [frames[0], frames[-1]]}
    t0 = time.perf_counter()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    room_scene = bpy.context.scene
    room_scene.name = "Room"
    room_scene.render.fps = FPS
    room_scene.frame_start, room_scene.frame_end = frames[0], frames[-1]
    spec = room.RoomSpec()
    motion = body.Motion()
    samples = {f: motion.sample(anim.time_of(f, FPS)) for f in frames}
    baker = anim.Baker()
    info = room.build_room_animated(room_scene, spec, motion, frames, FPS, baker, samples=samples)
    n_room = baker.write()
    timings["room_build_s"] = round(time.perf_counter() - t0, 2)
    timings["room_keyframes"] = n_room
    print(f"BUILD room: {timings['room_build_s']} s, {n_room} keyframes", flush=True)

    t1 = time.perf_counter()
    true_scene = mindscene.TrueScene("True", spec, FPS, eevee_samples=args.eevee_samples, bloom=not args.no_bloom)
    true_scene.scene.frame_start, true_scene.scene.frame_end = frames[0], frames[-1]
    true_scene.add_words(senses["words"], senses["will"])
    timings["true_build_s"] = round(time.perf_counter() - t1, 2)

    t2 = time.perf_counter()
    bpy.context.window.scene = room_scene
    reader = engine.SceneReader(room_scene, info["figure"]["empties"], info["phone"], info["sky"], spec,
                                room.sun_direction, (body.EYE_OFFSET, body.EAR_OFFSET))
    eng = engine.Engine(senses, reader, FPS, ridge_profile=room.ridge_profile(spec), window=spec.window,
                        room_size=spec.size)
    states = []
    for f in frames:
        states.append(eng.frame_state(f))
    timings["engine_s"] = round(time.perf_counter() - t2, 2)
    print(f"ENGINE: {len(states)} frames in {timings['engine_s']} s", flush=True)

    t3 = time.perf_counter()
    baker = anim.Baker()
    true_scene.bake(states, baker)
    n_true = baker.write()
    timings["bake_s"] = round(time.perf_counter() - t3, 2)
    timings["true_keyframes"] = n_true
    print(f"BAKE: {n_true} keyframes in {timings['bake_s']} s", flush=True)

    # the proxy's exposure over the dawn, found by search at a few moments and keyframed
    t4 = time.perf_counter()
    render.setup_eevee(room_scene, samples=8, view_transform="AgX")
    room_scene.eevee.use_shadows = True
    exposures = []
    exp = 1.5
    baker = anim.Baker()
    for sec in (0.0, 8.0, 20.0, 36.0, 48.0, 64.0, 84.0, 104.0, 112.0):
        f = anim.frame_of(min(sec, (frames[-1] - 1) / FPS), FPS)
        if f < frames[0] or f > frames[-1]:
            continue
        room_scene.frame_set(f)
        exp = render.find_exposure(room_scene, info["cam_third"], 0.22, size=(320, 144), samples=8, start=exp,
                                   iterations=6, tmp_dir=out, lo=-9.0, hi=8.0)
        exposures.append((sec, round(exp, 2)))
        baker.set(room_scene, "view_settings.exposure", 0, f, exp)
    baker.write()
    timings["exposure_s"] = round(time.perf_counter() - t4, 2)
    timings["exposures"] = exposures
    print(f"EXPOSURE: {exposures}", flush=True)

    summary = summarise(states, beats, senses)
    (out / "engine_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    timings["objects"] = len(bpy.data.objects)
    timings["total_s"] = round(time.perf_counter() - t0, 2)
    (out / "build_timings.json").write_text(json.dumps(timings, indent=2), encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(blend))
    print("SAVED:", blend, flush=True)
    print("TIMINGS:", json.dumps(timings), flush=True)


def summarise(states, beats, senses):
    """What the engine held and lit at each beat, for the report and the hand-over."""
    out = {"beats": []}
    by_frame = {s.frame: s for s in states}
    for b in beats["beats"]:
        mid = anim.frame_of((b["start"] + b["end"]) / 2.0, FPS)
        fs = by_frame.get(mid)
        if fs is None:
            continue
        regions = {k: (v["state"], round(v["att"], 3)) for k, v in fs.regions.items() if v["att"] > 1e-3}
        parts = {k: (v["state"], round(v["att"], 3)) for k, v in fs.parts.items() if v["att"] > 1e-3}
        rays_on = sum(1 for r in fs.rays if r[2] > 1e-3)
        waves_on = sum(1 for w in fs.waves if w[3] > 1e-3)
        out["beats"].append({
            "beat": b["id"], "frame": mid, "t": round(anim.time_of(mid, FPS), 2),
            "awareness": round(fs.awareness, 2), "budget_scale": round(fs.budget_scale, 3),
            "regions": regions, "parts": parts, "rays": rays_on, "waves": waves_on,
            "plumb": round(fs.plumb[2], 3), "throb": round(fs.throb[2], 3), "breath": round(fs.breath[1], 3),
            "heart": round(fs.heart[1], 3), "glow": round(fs.glow, 3), "sun": round(fs.sun[1], 3),
            "ridge_points": len(fs.ridge), "words_lit": {w: round(a, 2) for w, a in fs.words.items() if a > 0.01},
            "will_live": [i for i, _, _ in fs.will], "camera": [round(v, 2) for v in fs.camera[0]],
            "phone_in_model": fs.phone is not None, "rug_curled": fs.rug_curled,
        })
    # per second: the busiest claims
    per_second = []
    for s in states:
        if (s.frame - 1) % FPS == 0:
            per_second.append({"t": int(anim.time_of(s.frame, FPS)), "aw": round(s.awareness, 2), "scale": round(s.budget_scale, 2),
                               "rays": sum(1 for r in s.rays if r[2] > 1e-3),
                               "lit": sorted([k for k, v in s.regions.items() if v["state"] == tags.SENSED]),
                               "held": sorted([k for k, v in s.regions.items() if v["state"] in (tags.REMEMBERED, tags.FILLED)]),
                               "body": sorted([k for k, v in s.parts.items() if v["state"] == tags.SENSED])})
    out["per_second"] = per_second
    return out


def render_frames(args):
    out = pathlib.Path(args.out).resolve()
    blend = pathlib.Path(args.blend).resolve()
    beats = json.loads(pathlib.Path(args.beats).read_text(encoding="utf-8"))
    frames = frame_range(args, beats)
    bpy.ops.wm.open_mainfile(filepath=str(blend))
    if args.view == "true":
        scene = bpy.data.scenes["True"]
        cam = scene.camera
        size = TRUE_SIZE
        render.setup_eevee(scene, samples=args.eevee_samples)
    else:
        scene = bpy.data.scenes["Room"]
        cam = bpy.data.objects["Cam_Third"]
        size = THIRD_SIZE
        render.setup_eevee(scene, samples=max(4, args.eevee_samples // 2), view_transform="AgX")
        scene.eevee.use_shadows = True
    # the scene must be the window's scene for frame_set to drive the render headless (verified by running)
    bpy.context.window.scene = scene
    folder = out / args.view
    folder.mkdir(parents=True, exist_ok=True)
    size = (int(size[0] * args.scale), int(size[1] * args.scale))
    scene.camera = cam
    render.set_output(scene, size, str(folder / "frame_0000.png"))
    done, skipped = 0, 0
    t0 = time.perf_counter()
    times = []
    mon = render.GpuMonitor().start()
    for f in frames:
        path = folder / f"frame_{f:04d}.png"
        if path.exists() and not args.overwrite:
            skipped += 1
            continue
        scene.frame_set(f)
        scene.render.filepath = str(path)
        tf = time.perf_counter()
        bpy.ops.render.render(write_still=True, scene=scene.name)
        times.append(time.perf_counter() - tf)
        done += 1
        if done % 25 == 0:
            print(f"RENDER {args.view}: frame {f}, {done} done, {times[-1]:.2f} s/frame", flush=True)
    gpu = mon.stop()
    total = time.perf_counter() - t0
    rec = {"view": args.view, "frames": [frames[0], frames[-1]], "rendered": done, "skipped": skipped,
           "seconds": round(total, 1), "per_frame_mean": round(sum(times) / len(times), 3) if times else None,
           "per_frame_first": round(times[0], 2) if times else None, "gpu": gpu, "size": size}
    log = out / f"render_log_{args.view}.jsonl"
    with open(log, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(rec) + "\n")
    print("CHUNK:", json.dumps(rec), flush=True)


def main():
    args = parse_args()
    if args.mode == "build":
        build(args)
    else:
        render_frames(args)


if __name__ == "__main__":
    main()

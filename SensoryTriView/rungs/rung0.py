"""Rung 0: prove the pipeline end to end on this laptop.

Builds the stand-in room and the True-Person scene, saves the .blend, renders one frame
of each of the three views at panel size and writes timings.json. Compose the panels
afterwards with tools/compose.py.

Run inside Blender, from the project folder:
  blender.exe -b --python rungs/rung0.py -- [--views third,first,true] [--scale 0.5] [--samples 128]

Options after the double dash reach this script; the ones before it are Blender's.
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

from triview import mind, render, room  # noqa: E402

PANEL_TOP = (1920, 864)       # Third-Person and First-Person, side by side across the top
PANEL_BOTTOM = (3840, 1296)   # True-Person across the bottom


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser(description="Sensory Tri-View rung 0")
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung0"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung0.blend"))
    ap.add_argument("--views", default="third,first,true")
    ap.add_argument("--scale", type=float, default=1.0, help="resolution scale for quick looks")
    ap.add_argument("--samples", type=int, default=128, help="Cycles samples for the photoreal views")
    ap.add_argument("--eevee-samples", type=int, default=64)
    ap.add_argument("--exposure-third", type=float, default=None, help="fixed exposure; default: searched")
    ap.add_argument("--exposure-first", type=float, default=None)
    ap.add_argument("--target-third", type=float, default=0.10, help="mean display value the search aims at")
    ap.add_argument("--target-first", type=float, default=0.10)
    ap.add_argument("--metric-first", default="mean", choices=("mean", "p99"),
                    help="p99 exposes for the screen itself and leaves the room black")
    ap.add_argument("--no-bloom", action="store_true")
    ap.add_argument("--no-save", action="store_true")
    return ap.parse_args(argv)


def main():
    args = parse_args()
    # Blender resolves a bare relative path against the drive root, not the working folder
    out = pathlib.Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    args.blend = str(pathlib.Path(args.blend).resolve())
    pathlib.Path(args.blend).parent.mkdir(parents=True, exist_ok=True)
    t_start = time.perf_counter()

    bpy.ops.wm.read_factory_settings(use_empty=True)
    room_scene = bpy.context.scene
    room_scene.name = "Room"
    room_spec = room.RoomSpec()
    info = room.build_room(room_scene, room_spec)
    render.setup_cycles(room_scene, samples=args.samples)

    mind_spec = mind.MindSpec(bloom=not args.no_bloom)
    true_info = mind.build_true_scene("True", mind_spec, info)
    true_scene = true_info["scene"]
    render.setup_eevee(true_scene, samples=args.eevee_samples)

    t_build = time.perf_counter() - t_start
    print(f"BUILD: {t_build:.1f} s, {len(bpy.data.objects)} objects, head at "
          f"{tuple(round(v, 3) for v in info['head_world'])}", flush=True)
    if not args.no_save:
        bpy.ops.wm.save_as_mainfile(filepath=args.blend)
        print("SAVED:", args.blend, flush=True)

    views = [v.strip() for v in args.views.split(",") if v.strip()]
    results = {"blender": bpy.app.version_string, "build_seconds": round(t_build, 2), "views": {}}

    def size(base):
        return (int(round(base[0] * args.scale)), int(round(base[1] * args.scale)))

    if "third" in views:
        exp = args.exposure_third
        if exp is None:
            exp = render.find_exposure(room_scene, info["cam_third"], args.target_third, tmp_dir=out)
        results["views"]["third"] = render.render_view(room_scene, info["cam_third"], size(PANEL_TOP),
                                                       out / "third.png", exposure=exp, label="third")

    if "first" in views:
        hide = [info["head"]]
        exp = args.exposure_first
        if exp is None:
            exp = render.find_exposure(room_scene, info["cam_first"], args.target_first, hide_from_camera=hide,
                                       tmp_dir=out, metric=args.metric_first)
        results["views"]["first"] = render.render_view(room_scene, info["cam_first"], size(PANEL_TOP),
                                                       out / "first.png", exposure=exp, hide_from_camera=hide,
                                                       label="first")

    if "true" in views:
        r = render.render_view(true_scene, true_info["camera"], size(PANEL_BOTTOM), out / "true.png", label="true")
        r["bloom"] = bool(true_scene.render.use_compositing and true_scene.compositing_node_group)
        if (r.get("mean") or 0.0) < 0.002 and r["bloom"]:
            print("TRUE: black frame with the compositor on; rendering again without bloom", flush=True)
            render.disable_compositor(true_scene)
            r = render.render_view(true_scene, true_info["camera"], size(PANEL_BOTTOM), out / "true.png",
                                   label="true")
            r["bloom"] = False
        results["views"]["true"] = r

    results["total_seconds"] = round(time.perf_counter() - t_start, 2)
    (out / "timings.json").write_text(json.dumps(results, indent=2))
    print("TIMINGS:", json.dumps(results), flush=True)
    if not args.no_save:
        bpy.ops.wm.save_as_mainfile(filepath=args.blend)


if __name__ == "__main__":
    main()

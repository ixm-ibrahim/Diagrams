"""A quick look at the body motion: build the animated room, render a few EEVEE proxy
frames at beat moments, print contacts. Scratch script for rung 1; not part of the rung.

  blender.exe -b --python rungs/probe_body.py -- --out <abs folder> --times 2,10,17,25,29,35,45,51,56.4,63,72,80,86,93,99,106
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
from mathutils import Vector  # noqa: E402

from triview import anim, body, render, room  # noqa: E402


def main():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--times", default="2,10,17,25,29,35,45,51,56.4,63,72,80,86,93,99,106")
    ap.add_argument("--size", default="960x432")
    ap.add_argument("--samples", type=int, default=16)
    ap.add_argument("--save", default=None)
    a = ap.parse_args(argv)
    out = pathlib.Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    w, h = (int(v) for v in a.size.split("x"))
    fps = 24
    frames = list(range(1, 2689))

    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "Room"
    scene.render.fps = fps
    scene.frame_start, scene.frame_end = frames[0], frames[-1]
    t0 = time.perf_counter()
    motion = body.Motion()
    samples = {f: motion.sample(anim.time_of(f, fps)) for f in frames}
    t1 = time.perf_counter()
    baker = anim.Baker()
    info = room.build_room_animated(scene, room.RoomSpec(), motion, frames, fps, baker, samples=samples)
    n = baker.write()
    t2 = time.perf_counter()
    print(f"PROBE: motion {t1-t0:.1f}s, build+bake {t2-t1:.1f}s, {n} keyframes, {len(bpy.data.objects)} objects", flush=True)

    render.setup_eevee(scene, samples=a.samples, view_transform="AgX")
    scene.view_settings.exposure = 1.5
    scene.eevee.use_shadows = True
    contacts = {}
    for ts in a.times.split(","):
        t = float(ts)
        f = anim.frame_of(t, fps)
        scene.frame_set(f)
        J, hf, _, pm = samples[f]
        contacts[ts] = {
            "toe_r": [round(v, 2) for v in J["toe_r"]], "hand_r": [round(v, 2) for v in J["hand_r"]],
            "head": [round(v, 2) for v in hf["loc"]], "fwd": [round(v, 2) for v in hf["fwd"]],
            "phone": [round(v, 2) for v in pm.translation],
        }
        e = info["figure"]["empties"]["hand_r"]
        contacts[ts]["hand_r_blender"] = [round(v, 2) for v in e.matrix_world.translation]
        path = out / f"body_{ts.replace('.', 'p')}.png"
        r = render.render_view(scene, info["cam_third"], (w, h), path, label=f"t{ts}", quiet=True)
        print(f"PROBE: t={ts} frame {f} {r['seconds']}s mean {r['mean']}", flush=True)
    (out / "contacts.json").write_text(json.dumps(contacts, indent=1))
    if a.save:
        bpy.ops.wm.save_as_mainfile(filepath=str(pathlib.Path(a.save).resolve()))
    print("PROBE DONE", flush=True)


if __name__ == "__main__":
    main()

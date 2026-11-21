"""The man's short turn at the sill (rung 3): his head turning at the window, through the Third-Person camera.

    python tools/rung3_turn.py whole    [--first 1966 --last 2101] [--samples 256] [--chunk 12]
    python tools/rung3_turn.py render
    python tools/rung3_turn.py assemble
    python tools/rung3_turn.py status

The frames are scene 65.5 to 70.0 s (player 81.9 to 87.5 s): he blinks at player 82.2 s, his head is turned 15 degrees
to his right at player 83.1 s, 12 degrees to his left at player 85.0 s and straight again at player 87.5 s
(triview/body.py, HEAD_KEYS). Each frame is rendered by `rungs/rung3.py turn` from scenes/rung3_sill_c.blend at the eye
table's exposure for the frame plus --exposure-offset.

render:   what is missing of the frames, a part of --chunk frames to a Blender process, under tools/dev_showcase.py's
          heat guard and battery rule. A picture on disk is never rendered again, so the run can be stopped (a file
          named STOP in the output folder, looked for between frames) and started again where it was.
assemble: the frames joined by FFmpeg at 24 frames a second, the piece's own pace, as <out>/<name>.mp4, with a second
          video that plays the turn three times over for looking at it longer.
whole:    render, then assemble, in one command that can be run again after any interruption. What it prints also goes
          to <out>/whole.log; its last line is TURN DONE (TURN INCOMPLETE and no video if frames are left).
status:   what is on disk of what is wanted, and the seconds and graphics memory of the frames made so far.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import dev_showcase as ds  # noqa: E402

BLENDER, RENDER_FPS = ds.BLENDER, ds.RENDER_FPS


def stamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def frame_path(a, f):
    return a.out / "frames" / f"frame_{f:04d}.png"


def missing(a):
    return [f for f in range(a.first, a.last + 1) if not frame_path(a, f).exists()]


def render(a):
    """Render what is missing of the turn; the number of frames still missing at the end."""
    out = a.out
    (out / "frames").mkdir(parents=True, exist_ok=True)
    (out / "logs").mkdir(parents=True, exist_ok=True)
    stop = out / "STOP"
    guard = not a.no_heat_guard
    floor = 100 if a.on_battery is None else a.on_battery
    ds.awake(True)
    fails = 0
    while True:
        todo = missing(a)
        if not todo:
            return 0
        if stop.exists():
            print(f"STOP found with {len(todo)} frames left; ending", flush=True)
            sys.exit(0)
        if ds.battery_low(floor)[0]:
            ds.wait_for_charger("the turn", stop)
            continue
        if guard:
            temp, speed, busy = ds.machine()
            if temp is not None and temp >= ds.START_C:
                ds.cool_down("the turn", "too hot to start, " + ds.heat_text(temp, speed, busy), stop)
                continue
        # one part: the first run of missing frames, at most --chunk of them
        part = [todo[0]]
        while len(part) < a.chunk and part[-1] + 1 in todo:
            part.append(part[-1] + 1)
        cmd = [BLENDER, "-b", "--python", str(ROOT / "rungs" / "rung3.py"), "--", "turn", "--blend", str(a.blend),
               "--frame", str(part[0]), "--frame-end", str(part[-1]), "--samples", str(a.samples), "--size", a.size,
               "--exposure-offset", str(a.exposure_offset), "--denoiser", a.denoiser, "--out", str(out / "frames"), "--note", a.note]
        t0 = time.perf_counter()
        with open(out / "logs" / "turn_render.log", "a", encoding="utf-8", errors="replace") as fh:
            fh.write(f"\n==== {stamp()} frames {part[0]} to {part[-1]}\n")
            fh.flush()
            code, why = ds.run_guarded(cmd, fh, out, ["frames"], guard, floor)
        secs = time.perf_counter() - t0
        left = [f for f in part if not frame_path(a, f).exists()]
        made = len(part) - len(left)
        temp = ds.machine()[0]
        print(f"{stamp()} frames {part[0]} to {part[-1]}: {made} of {len(part)} in {secs / 60.0:.1f} min "
              f"({secs / max(made, 1):.0f} s a frame with the scene's loading), {len(missing(a))} left, the card at "
              f"{'?' if temp is None else int(temp)} C" + (f"; ended: {why}" if why else "" if code == 0 else f"; code {code}"), flush=True)
        for p in (out / "frames").glob("making_*.png"):          # a picture cut off while being written
            p.unlink()
        if why:
            if why.startswith(ds.ON_BATTERY):
                ds.wait_for_charger("the turn", stop)
            else:
                ds.cool_down("the turn", why, stop)
            continue
        if made == 0:
            fails += 1
            if fails >= 3:
                print(f"three parts in a row made no frame (code {code}): see {out / 'logs' / 'turn_render.log'}", flush=True)
                return len(missing(a))
        else:
            fails = 0


def assemble(a):
    """The frames joined at the piece's pace, and the same turn three times over."""
    left = missing(a)
    if left:
        sys.exit(f"{len(left)} frames are missing ({left[0]} to {left[-1]}): render first")
    src = str(a.out / "frames" / "frame_%04d.png")
    one = a.out / f"{a.name}.mp4"
    base = ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(RENDER_FPS), "-start_number", str(a.first), "-i", src]
    enc = ["-c:v", "libx264", "-crf", str(a.crf), "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]
    subprocess.run(base + ["-frames:v", str(a.last - a.first + 1)] + enc + [str(one)], check=True)
    thrice = a.out / f"{a.name}_three_times.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-stream_loop", "2", "-i", str(one), "-c", "copy", str(thrice)], check=True)
    n = a.last - a.first + 1
    print(f"ASSEMBLED {stamp()}: {one} ({n} frames, {n / RENDER_FPS:.1f} s, {one.stat().st_size / 1e6:.1f} MB) and {thrice.name}", flush=True)


def status(a):
    left = missing(a)
    n = a.last - a.first + 1
    print(f"the turn, frames {a.first} to {a.last}: {n - len(left)} of {n} on disk" + (f", missing from {left[0]}" if left else ""), flush=True)
    log = a.out / "frames.json"
    if log.exists():
        rows = [r for r in json.loads(log.read_text(encoding="utf-8")) if a.first <= r["f"] <= a.last]
        if rows:
            secs = sorted(r["seconds"] for r in rows)
            print(f"  {len(rows)} frames timed: {sum(secs) / len(secs):.1f} s a frame on average, {secs[0]:.1f} to {secs[-1]:.1f}; "
                  f"graphics memory at most {max(r['gpu_peak_mb'] for r in rows)} MB", flush=True)


def whole(a):
    a.out.mkdir(parents=True, exist_ok=True)
    sys.stdout = ds.Tee(sys.__stdout__, open(a.out / "whole.log", "a", encoding="utf-8"))
    print(f"TURN START {stamp()}: frames {a.first} to {a.last} of {a.blend.name} at {a.samples} samples into {a.out}", flush=True)
    t0 = time.time()
    left = render(a)
    status(a)
    if left:
        print(f"TURN INCOMPLETE {stamp()}: {left} frames are missing, so no video is made; run the same command again", flush=True)
        sys.exit(1)
    print(f"ALL FRAMES DONE {stamp()} after {(time.time() - t0) / 60.0:.0f} min of this run", flush=True)
    assemble(a)
    print(f"TURN DONE {stamp()}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="The man's short turn at the sill (rung 3)")
    ap.add_argument("what", choices=("render", "assemble", "status", "whole"))
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung3" / "turn"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung3_sill_c.blend"))
    ap.add_argument("--first", type=int, default=1966, help="scene 65.5 s, player 81.9 s")
    ap.add_argument("--last", type=int, default=2101, help="scene 70.0 s, player 87.5 s")
    ap.add_argument("--samples", type=int, default=256)
    ap.add_argument("--size", default="1920x864")
    ap.add_argument("--exposure-offset", type=float, default=-1.5,
                    help="stops added to the eye table's Third-Person exposure (the table was set on the dark mannequin; rung 5 sets the eye's exposure for a real face)")
    ap.add_argument("--denoiser", default="optix", choices=("optix", "oidn"),
                    help="what cleans the frames' noise: OptiX (round one) or Open Image Denoise (round three's pictures, kinder to fine skin)")
    ap.add_argument("--chunk", type=int, default=12, help="frames a Blender process renders before the next is started")
    ap.add_argument("--name", default="turn")
    ap.add_argument("--note", default="round one")
    ap.add_argument("--crf", type=int, default=14)
    ap.add_argument("--no-heat-guard", action="store_true", help="do not pause the render when the machine is too hot (tools/dev_showcase.py)")
    ap.add_argument("--on-battery", nargs="?", type=int, const=ds.BATTERY_FLOOR, default=None, metavar="PERCENT",
                    help="render on the laptop's battery too, until its charge has fallen to this percent (20 if no number is given)")
    a = ap.parse_args()
    a.out, a.blend = pathlib.Path(a.out).resolve(), pathlib.Path(a.blend).resolve()
    {"render": render, "assemble": assemble, "status": status, "whole": whole}[a.what](a)


if __name__ == "__main__":
    main()

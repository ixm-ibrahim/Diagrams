"""Drive rung 2 from outside Blender: the builds, the renders in chunks, the assembly.

    python tools/run_rung2.py --build            the piece's scene, probes and eye table
    python tools/run_rung2.py --build-moves      the moves' scene (after --build)
    python tools/run_rung2.py --views first,third [--chunk 336] [--frames a-b]
    python tools/run_rung2.py --moves third_first,first_third,third_true,true_third
    python tools/run_rung2.py --true16           the True-Person view at 16:9 for the showcase's segment
    python tools/run_rung2.py --check --frames a-b   the model through the simulated eyes (rung 2o), to set beside the
                                                 First-Person frames; tools/check_eyes.py picks open-eye frames and compares
    python tools/run_rung2.py --scan --frames a-b   the eyes' scan (rung 2d), colour and position per frame
    python tools/run_rung2.py --scan-move --moves third_true   the move's scan at the road's exposure (after --build-moves)
    python tools/run_rung2.py --backdrop --frames a-b   the backdrop scan (rung 2h): the sky, the ground and the range alone
    python tools/run_rung2.py --backdrop-move --moves third_true   the move's backdrop at the road's exposure
    python tools/run_rung2.py --sky --frames a-b   the sky scan (rung 2i): the sky's shell alone, remembered behind the range
    python tools/run_rung2.py --sky-move --moves third_true   the move's sky at the road's exposure
    python tools/run_rung2.py --peel --frames a-b   the peel scan (rung 2l): the far side of the first thing every ray strikes,
                                                 position and index alone (no exposure, so no move pass is needed)
    (with --scan-move, --backdrop-move or --sky-move, --moves names the scans' moves alone; the passes need a call of their own)
    python tools/run_rung2.py --assemble         the videos and the sheets
    --step 5 --speed 2                           a fast test (his sixth review of 2026-11-09): every fifth frame rendered and
                                                 assembled with each frame held, plus showcase_fast.mp4 played at twice the pace;
                                                 the scans keep the picture frames the memories read as well (held_frames.json)
    python tools/run_rung2.py --views third,first --step 5   the other two views over the same frames, for the showcase of each view

A run of its own (the lidar test of rung 2d) keeps its files apart:
    --out renders/rung2d --blend scenes/rung2d.blend --moves-blend scenes/rung2d_moves.blend
    --cut data/cut_test.json --mind lidar

Each chunk is its own Blender process (short and resumable: frames already on disk are
skipped) with its console in <out>/logs/. Anything over two minutes should run in the
background. run_summary.json records every chunk's exit code and seconds.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
RENDER_FPS = 24
FPS = 24.0   # frames per chain second, set from data/beats.json's pace in main()


def run(args, log_path):
    with open(log_path, "w", encoding="utf-8") as log:
        t0 = time.perf_counter()
        r = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, cwd=str(ROOT))
        return r.returncode, time.perf_counter() - t0


def frames_of(spec):
    a, b = (int(v) for v in spec.split("-"))
    return a, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--build-moves", action="store_true")
    ap.add_argument("--views", default="")
    ap.add_argument("--moves", default="")
    ap.add_argument("--true16", action="store_true")
    ap.add_argument("--check", action="store_true", help="the model through the simulated eyes over --frames (rung 2o)")
    ap.add_argument("--true-size", default=None, help="WxH for the 16:9 True view; default 960x540")
    ap.add_argument("--scan", action="store_true", help="the eyes' scan over --frames (rung 2d)")
    ap.add_argument("--scan-move", action="store_true", help="the listed moves' scan at the road's exposure, colour only")
    ap.add_argument("--backdrop", action="store_true", help="the backdrop scan over --frames: the sky, the ground and the range with the near things hidden")
    ap.add_argument("--backdrop-move", action="store_true", help="the listed moves' backdrop at the road's exposure, colour only")
    ap.add_argument("--sky", action="store_true", help="the sky scan over --frames: the sky's shell alone, for the sky remembered behind the range")
    ap.add_argument("--sky-move", action="store_true", help="the listed moves' sky at the road's exposure, colour only")
    ap.add_argument("--peel", action="store_true", help="the peel scan over --frames: the far side of the first thing every ray strikes, position and index")
    ap.add_argument("--pane", action="store_true", help="the pane scan over --frames: the window's glass reflecting alone, for the model's glass layer (rung 2o)")
    ap.add_argument("--probes-from", default=None, help="reuse an earlier build's probes.json for the eye table")
    ap.add_argument("--chunk", type=int, default=336)
    ap.add_argument("--frames", default=None, help="a-b to limit the range of the views and the scan")
    ap.add_argument("--samples", type=int, default=24)
    ap.add_argument("--assemble", action="store_true")
    ap.add_argument("--assemble-only", default="all", choices=("all", "piece", "showcase", "moves", "sheets"))
    ap.add_argument("--no-probes", action="store_true")
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung2.blend"))
    ap.add_argument("--moves-blend", default=str(ROOT / "scenes" / "rung2_moves.blend"))
    ap.add_argument("--cut", default=str(ROOT / "data" / "cut.json"))
    ap.add_argument("--mind", default="plates", choices=("plates", "lidar"))
    ap.add_argument("--scan-size", type=int, default=640)
    ap.add_argument("--scan-fov", type=float, default=200.0)
    ap.add_argument("--true-road", default="piece", choices=("piece", "close", "orbit"), help="the True camera: the concept's road, a close station over the shoulder for a test, or that station with one full turn round the head")
    ap.add_argument("--eevee-samples", type=int, default=24, help="EEVEE samples for the True views")
    ap.add_argument("--step", type=int, default=1, help="render and assemble every Nth frame, counted from frame 1: a fast test")
    ap.add_argument("--speed", type=float, default=2.0, help="with --step, the pace of showcase_fast.mp4 over real time")
    ap.add_argument("--tag", default="", help="a name for a second cut's assembled outputs (showcase_<tag>.mp4 and the rest)")
    ap.add_argument("--audio", default=None, help="a soundtrack (tools/fake_audio.py) for the assembly to lay under the showcase")
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    blend = pathlib.Path(a.blend).resolve()
    moves_blend = pathlib.Path(a.moves_blend).resolve()
    cut_path = pathlib.Path(a.cut).resolve()
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    cut = json.loads(cut_path.read_text(encoding="utf-8"))
    global FPS
    FPS = RENDER_FPS / float(beats.get("pace", 1.0))
    total = int(round(beats["duration_seconds"] * FPS))
    summary_path = out / "run_summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8")) if summary_path.exists() else {"chunks": []}
    base = [BLENDER, "-b", "--python", str(ROOT / "rungs" / "rung2.py"), "--"]
    common = ["--out", str(out), "--blend", str(blend), "--moves-blend", str(moves_blend), "--cut", str(cut_path),
              "--mind", a.mind, "--scan-size", str(a.scan_size), "--scan-fov", str(a.scan_fov), "--true-road", a.true_road,
              "--eevee-samples", str(a.eevee_samples), "--step", str(a.step)]

    def stepped(f):
        return (f - 1) % a.step == 0

    def held_refs(frames):
        """The picture frames the model's memories read at these frames (held_frames.json, from the
        bake): a stepped render of the scans keeps them too."""
        held = out / "held_frames.json"
        if a.step <= 1 or not held.exists():
            return set()
        by_frame = json.loads(held.read_text(encoding="utf-8"))["by_frame"]
        return {r for f in frames for r in by_frame.get(str(f), [])}

    def record(label, start, end, code, secs, retry=False):
        rec = {"label": label, "start": start, "end": end, "code": code, "seconds": round(secs, 1)}
        if retry:
            rec["retry"] = True
        summary["chunks"].append(rec)
        summary_path.write_text(json.dumps(summary, indent=1), encoding="utf-8")

    if a.build:
        extra = ["--no-probes"] if a.no_probes else []
        if a.probes_from:
            extra += ["--probes-from", str(pathlib.Path(a.probes_from).resolve())]
        code, secs = run(base + ["build"] + common + extra, logs / "build.txt")
        print(f"build: code {code} in {secs:.0f} s", flush=True)
        record("build", 1, total, code, secs)
        if code != 0:
            sys.exit(code)
    if a.build_moves:
        code, secs = run(base + ["build", "--moves"] + common, logs / "build_moves.txt")
        print(f"build moves: code {code} in {secs:.0f} s", flush=True)
        record("build_moves", 1, total, code, secs)
        if code != 0:
            sys.exit(code)

    def chunks(label, folder, first, last, args_view, also=(), colour=True):
        """also: further per-frame file patterns that must exist too (the scan's positions and indices);
        colour: the view writes a colour frame as well (the peel does not). With --step only every Nth
        frame counts."""
        def done(f):
            return (not colour or (folder / f"frame_{f:04d}.png").exists()) and all((folder / pat.format(f)).exists() for pat in also)
        start = first
        while start <= last:
            end = min(last, start + a.chunk - 1)
            wanted = [f for f in range(start, end + 1) if stepped(f)]
            if also:
                wanted = sorted(set(wanted) | held_refs(wanted))
            missing = [f for f in wanted if not done(f)]
            if not missing:
                print(f"{label} {start}-{end}: done already", flush=True)
                start = end + 1
                continue
            cmd = base + ["render"] + args_view + ["--frames", f"{start}-{end}", "--samples", str(a.samples)] + common
            code, secs = run(cmd, logs / f"render_{label}_{start:04d}_{end:04d}.txt")
            n_after = sum(1 for f in wanted if done(f))
            print(f"{label} {start}-{end}: code {code}, {len(missing)} to do, {n_after - (len(wanted) - len(missing))} rendered in {secs:.0f} s", flush=True)
            record(label, start, end, code, secs)
            if code != 0:
                print("chunk failed, retrying once", flush=True)
                code, secs = run(cmd, logs / f"render_{label}_{start:04d}_{end:04d}_retry.txt")
                record(label, start, end, code, secs, retry=True)
            start = end + 1

    first, last = 1, total
    if a.frames:
        first, last = frames_of(a.frames)
    scan_also = ("pos_{:04d}.exr", "idx_{:04d}.exr")
    if a.scan:
        chunks("scan", out / "scan", first, last, ["--view", "scan"], also=scan_also)
    if a.backdrop:
        chunks("backdrop", out / "backdrop", first, last, ["--view", "backdrop"], also=scan_also)
    if a.sky:
        chunks("sky", out / "sky", first, last, ["--view", "sky"], also=scan_also)
    if a.peel:
        chunks("peel", out / "peel", first, last, ["--view", "peel"], also=scan_also, colour=False)
    if a.pane:
        chunks("pane", out / "pane", first, last, ["--view", "pane"], also=scan_also)
    for view in [v for v in a.views.split(",") if v]:
        extra = ["--size", "1920x648"] if view == "true" else []
        chunks(view, out / view, first, last, ["--view", view] + extra)
    if a.check:
        chunks("check", out / "check", first, last, ["--view", "check"])
    for flag, view in ((a.scan_move, "scan_move"), (a.backdrop_move, "backdrop_move"), (a.sky_move, "sky_move")):
        if not flag:
            continue
        table = json.loads((out / "moves_frames.json").read_text(encoding="utf-8"))["moves"]
        for move in [m for m in a.moves.split(",") if m]:
            rows = [r for r in table.get(move, {"rows": []})["rows"] if r.get("scan_exp") is not None]
            if rows:
                chunks(f"{view}_{move}", out / view, rows[0]["f"], rows[-1]["f"], ["--view", view, "--move", move])
    # with --scan-move, --backdrop-move or --sky-move, --moves names the scans' moves alone: their passes are not
    # rendered (they were, with the scene as it stood at that moment, and stood as done later: found 2026-11-09)
    render_moves = not (a.scan_move or a.backdrop_move or a.sky_move)
    for move in ([m for m in a.moves.split(",") if m] if render_moves else []):
        spec = cut["moves"][move]
        f0 = int(round(spec["t0"] * FPS)) + 1
        f1 = int(round(spec["t1"] * FPS)) + 1
        passes = ["room", "mind"] if spec["kind"] == "mind" else ["room"]
        for p in passes:
            chunks(f"{move}_{p}", out / "moves" / move / p, f0, f1, ["--view", "move", "--move", move, "--pass", p])
    if a.true16:
        seg = next(s for s in cut["showcase"] if s["view"] == "true")
        f0 = int(round(seg["t0"] * FPS)) + 1
        f1 = int(round(seg["t1"] * FPS))
        chunks("true16", out / "true16", f0, f1, ["--view", "true"] + (["--size", a.true_size] if a.true_size else []))
    if a.assemble:
        code, secs = run([sys.executable, str(ROOT / "tools" / "assemble_rung2.py"), "--out", str(out), "--cut", str(cut_path),
                          "--only", a.assemble_only, "--step", str(a.step), "--speed", str(a.speed)] + (["--tag", a.tag] if a.tag else [])
                         + (["--audio", str(pathlib.Path(a.audio).resolve())] if a.audio else []),
                         logs / f"assemble{'_' + a.tag if a.tag else ''}.txt")
        print(f"assemble: code {code} in {secs:.0f} s", flush=True)
        record("assemble", 1, total, code, secs)
    print("RUN DONE", flush=True)


if __name__ == "__main__":
    main()

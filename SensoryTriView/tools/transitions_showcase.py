"""The showcase with the moves between views (rung 3, at his word of 2026-11-19: "the previous rung didn't have a
showcase showing the transitions between views").

    python tools/transitions_showcase.py render   [--dry-run] [--chunk 60]
    python tools/transitions_showcase.py assemble [--frames a-b] [--moves-from samples_step30 --hold-missing]
    python tools/transitions_showcase.py status
    python tools/transitions_showcase.py whole

The showcase is the whole scene in the cut's order (data/cut.json): Third-Person, the move into First-Person,
First-Person, the move back into Third-Person, Third-Person, the move into True-Person, True-Person, the dive into
First-Person, First-Person, then the three views together. The single views are the frames he passed in rung 2p
(renders/rung2p: third, first, scan, show_r14); only the moves are rendered here, from the two scenes built with that
cut on the engine as passed (scenes/rung3_transitions.blend and rung3_transitions_moves.blend, into
renders/rung3/transitions, whose five folders of the eyes' pictures are junctions to rung 2p's and are only read).

render: the moves the cut's showcase names, in time order, and for each only what is missing:
  the three scans of the eyes at the road's exposure (scan_move, backdrop_move, sky_move), for a move whose rows carry one;
  the room pass, 960 by 540 (Cycles): the camera of the move in the room;
  the mind pass, 1920 by 1080 (EEVEE), for a move through the mind: the model through the move's twin camera.
A frame on disk is never rendered again, so the run can be stopped (a file named STOP in the output folder, looked for
between steps) and started again where it was. The heat guard and the battery's rule are tools/dev_showcase.py's own.
Every step's seconds go to <out>/status.json. A mind pass is refused while any of its move's scans is missing:
rungs/rung2.py would then draw the model from the piece's own scans, at the eyes' exposure, and say nothing.

assemble: every frame composed here and piped to FFmpeg, 1920 by 1080 at 24 frames a second with the stand-in sound,
as <out>/<videos>/<name>.mp4, and one short clip of each move with a second and a half on either side.
  Third-Person, True-Person   the passed frames.
  First-Person                the eyes' whole field, as the passed showcase shows it (tools/first_still.py, field eyes).
  a move round his head       the room pass with the lids, the tint and the pain's flash from the move's own row. The
                              First-Person view is the eyes' whole field, a wider picture than the camera on the eyes
                              that the move arrives with, so the picture changes from one to the other while his lids
                              are shut in the move's blink, cross-faded evenly over the shut frames.
  a move through the mind     the room pass and the mind pass cross-dissolved in display values by the row's own weight.
  the dive                    lands on the camera on the eyes with no blink to change behind, so the First-Person
                              seconds that follow it keep the camera's picture (field camera).
  the three together          the passed layout, 1280 by 1080, centred on black.
--moves-from and --hold-missing make a rough from a stepped sample: a missing move frame is the nearest earlier one.

whole: render, status, assemble, in one command that can be run again after any interruption. What it prints also goes
to <out>/whole.log; its last line is WHOLE DONE.

status: what is on disk of what is wanted, and the seconds a frame of each kind of step so far.
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

BLENDER, RENDER_FPS, FONT = ds.BLENDER, ds.RENDER_FPS, ds.FONT
SCAN_FOLDERS = ("scan_move", "backdrop_move", "sky_move")
ROOM_SIZE = (960, 540)
FRAME = (1920, 1080)
CLIP_PAD = 36           # frames of the neighbouring views before and after a move in its own clip
LABELS = {"third": "Third-Person view", "first": "First-Person view", "true": "True-Person view",
          "third_first": "Third-Person into First-Person", "first_third": "First-Person back to Third-Person",
          "third_true": "Third-Person into True-Person", "true_first": "True-Person into First-Person",
          "true_third": "True-Person back to Third-Person"}


def stamp():
    return time.strftime("%Y-%m-%d %H:%M:%S")


def load(a):
    """The scene's frames a second, its frame count, the cut and the moves' per-frame tables."""
    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    cfps = RENDER_FPS / float(beats.get("pace", 1.0))
    total = int(round(beats["duration_seconds"] * cfps))
    cut = json.loads(a.cut.read_text(encoding="utf-8"))
    path = a.out / "moves_frames.json"
    table = json.loads(path.read_text(encoding="utf-8"))["moves"] if path.exists() else {}
    return cfps, total, cut, table


def showcase_moves(cut):
    """The moves the showcase shows, in time order."""
    names = [seg["move"] for seg in cut["showcase"] if seg["view"] == "move"]
    return sorted(dict.fromkeys(names), key=lambda n: float(cut["moves"][n]["t0"]))


def move_frames(spec, cfps):
    """A move's frames as rungs/rung2.py and tools/run_rung2.py count them: both ends kept."""
    return list(range(int(round(float(spec["t0"]) * cfps)) + 1, int(round(float(spec["t1"]) * cfps)) + 2))


def segment_frames(seg, cfps):
    """A showcase segment's frames as tools/assemble_rung2.py counts them: the segments tile the scene."""
    return list(range(int(round(float(seg["t0"]) * cfps)) + 1, int(round(float(seg["t1"]) * cfps)) + 1))


def common(a):
    return ["--out", str(a.out), "--mind", "lidar", "--scan-size", "1024", "--scan-fov", "200", "--true-road", "orbit", "--step", "1",
            "--cut", str(a.cut), "--blend", str(a.blend), "--moves-blend", str(a.moves_blend)]


def frame_path(folder, f):
    return folder / f"frame_{f:04d}.png"


def chunks(frames, n):
    """The frames in runs of n for one Blender process each; a short last run (under a third of n) joins the one
    before it, so no process is started for a frame or two."""
    out = [frames[i:i + n] for i in range(0, len(frames), n)]
    if len(out) > 1 and len(out[-1]) < max(n // 3, 1):
        last = out.pop()
        out[-1] = out[-1] + last
    return out


# ---- render ---------------------------------------------------------------------------------------------------------

def render(a):
    """Render what is missing of the moves; the number of pictures still missing at the end (with --dry-run, the
    number that would be rendered)."""
    cfps, total, cut, table = load(a)
    out = a.out
    if not table:
        sys.exit(f"no moves_frames.json in {out}: build the moves' scene first (rungs/rung2.py build --moves)")
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    status_path = out / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {"steps": []}
    stop = out / "STOP"
    guard = not a.no_heat_guard
    # the charge at or under which the render waits for the charger: on the battery at all, unless --on-battery
    floor = 100 if a.on_battery is None else a.on_battery
    if not a.dry_run:
        ds.awake(True)
    rung2 = [BLENDER, "-b", "--python", str(ROOT / "rungs" / "rung2.py"), "--", "render"]
    planned = [0]

    def missing(folder, fs):
        return [f for f in fs if not frame_path(out / folder, f).exists()]

    def step(label, cmd, need, count, folders):
        """Run one step for the pictures it still has to make; True if it left none missing."""
        while True:
            todo = need()
            if not todo:
                return True
            if a.dry_run:
                planned[0] += len(todo)
                print(f"DRY RUN {label}: {len(todo)} frames, {todo[0]} to {todo[-1]}\n    {subprocess.list2cmdline(cmd(todo))}", flush=True)
                return True
            if stop.exists():
                print(f"STOP found before {label}; ending", flush=True)
                sys.exit(0)
            if ds.battery_low(floor)[0]:
                ds.wait_for_charger(label, stop)
                continue
            if guard:
                temp, speed, busy = ds.machine()
                if temp is not None and temp >= ds.START_C:
                    ds.cool_down(label, "too hot to start, " + ds.heat_text(temp, speed, busy), stop)
                    continue
            for folder in folders:
                (out / folder).mkdir(parents=True, exist_ok=True)
            t0 = time.perf_counter()
            log = logs / f"transitions_{label.split()[0]}.log"
            with open(log, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n==== {stamp()} {label}: {len(todo)} frames\n")
                fh.flush()
                code, why = ds.run_guarded(cmd(todo), fh, out, folders, guard, floor)
            secs = time.perf_counter() - t0
            left = need()
            made = len(todo) - len(left)
            rec = {"at": stamp(), "step": label, "frames": [todo[0], todo[-1]], "wanted": len(todo), "made": made,
                   "seconds": round(secs, 1), "per_frame": round(secs / max(made, 1), 2), "code": code}
            if why:
                rec["paused"] = why
            status["steps"].append(rec)
            status_path.write_text(json.dumps(status, indent=1), encoding="utf-8")
            on_battery = bool(why) and why.startswith(ds.ON_BATTERY)
            print(f"{rec['at']} {label}: {made} of {len(todo)} frames in {secs / 60.0:.1f} min ({rec['per_frame']} s a frame), "
                  + ("ended on the battery" if on_battery else "ended for heat" if why else f"code {code}")
                  + (("; " + ds.heat_text(*ds.machine())) if guard and not why else ""), flush=True)
            count[0] += made
            if why:
                if on_battery:
                    ds.wait_for_charger(label, stop)
                else:
                    ds.cool_down(label, why, stop)
                continue
            return not left

    left_all = 0
    for name in showcase_moves(cut):
        spec = cut["moves"][name]
        rows = {r["f"]: r for r in table.get(name, {}).get("rows", [])}
        frames = [f for f in move_frames(spec, cfps) if f in rows]
        if not frames:
            print(f"MOVE {name}: no rows in moves_frames.json; skipped", flush=True)
            continue
        is_mind = spec["kind"] == "mind"
        scan_frames = [f for f in frames if rows[f].get("scan_exp") is not None]
        room, mind = f"moves/{name}/room", f"moves/{name}/mind"

        def scans_left():
            return [f for f in scan_frames if any(not frame_path(out / folder, f).exists() for folder in SCAN_FOLDERS)]

        for attempt in range(3):
            made = [0]
            ok = True
            if scan_frames:
                # one call of the runner: each of its three scans skips the frames it has
                ok &= step(f"scans {name}", lambda todo: [
                    sys.executable, str(ROOT / "tools" / "run_rung2.py"), "--scan-move", "--backdrop-move", "--sky-move", "--moves", name,
                    "--samples", str(a.samples), "--out", str(out), "--blend", str(a.blend), "--moves-blend", str(a.moves_blend),
                    "--cut", str(a.cut), "--mind", "lidar", "--scan-size", "1024", "--scan-fov", "200", "--true-road", "orbit"],
                    scans_left, made, SCAN_FOLDERS)
            for fs in chunks(frames, a.chunk):
                ok &= step(f"room {name} {fs[0]}-{fs[-1]}", lambda todo: rung2 + ["--view", "move", "--move", name, "--pass", "room",
                           "--frames", f"{todo[0]}-{todo[-1]}", "--samples", str(a.samples)] + common(a),
                           lambda fs=fs: missing(room, fs), made, (room,))
            if is_mind:
                short = scans_left() if (scan_frames and not a.dry_run) else []
                if short:
                    print(f"MIND {name} NOT RENDERED: {len(short)} of its frames lack a scan picture of the move ({short[0]} to {short[-1]}); "
                          "without them the model would be drawn from the piece's own scans at the eyes' exposure", flush=True)
                    ok = False
                else:
                    for fs in chunks(frames, a.chunk):
                        ok &= step(f"mind {name} {fs[0]}-{fs[-1]}", lambda todo: rung2 + ["--view", "move", "--move", name, "--pass", "mind",
                                   "--frames", f"{todo[0]}-{todo[-1]}", "--eevee-samples", str(a.eevee_samples), "--size", a.size,
                                   "--no-frame-set"] + common(a),
                                   lambda fs=fs: missing(mind, fs), made, (mind,))
            if ok or a.dry_run:
                break
            if not made[0]:
                print(f"move {name}: a pass made nothing new; going on to the next move", flush=True)
                break
        left = len(scans_left()) + len(missing(room, frames)) + (len(missing(mind, frames)) if is_mind else 0)
        left_all += left
        if not a.dry_run:
            print(f"MOVE {name} {'complete' if not left else f'INCOMPLETE, {left} pictures missing'} at {time.strftime('%H:%M:%S')}", flush=True)
    if a.dry_run:
        print(f"DRY RUN: {planned[0]} frames would be rendered (a frame of the scans counted once for its three pictures)", flush=True)
        return planned[0]
    print(f"RENDERDONE: {left_all} pictures of the moves still missing", flush=True)
    return left_all


# ---- status ---------------------------------------------------------------------------------------------------------

def status(a):
    from PIL import Image
    cfps, total, cut, table = load(a)
    out = a.out
    size = tuple(int(v) for v in a.size.lower().split("x"))

    def have(folder, fs):
        return [f for f in fs if frame_path(folder, f).exists()]

    def line(label, got, fs):
        print(f"  {label:26s} {len(got):5d} of {len(fs):5d}   " + (", ".join(f"{lo}-{hi}" for lo, hi in ds.runs(got)[:6]) or "none"))

    print(f"THE MOVES in {out}")
    for name in showcase_moves(cut):
        spec = cut["moves"][name]
        rows = {r["f"]: r for r in table.get(name, {}).get("rows", [])}
        frames = [f for f in move_frames(spec, cfps) if f in rows]
        print(f" {name}: {LABELS.get(name, name)}, frames {frames[0]} to {frames[-1]}" if frames else f" {name}: no rows")
        scan_frames = [f for f in frames if rows[f].get("scan_exp") is not None]
        for folder in SCAN_FOLDERS if scan_frames else ():
            line(folder, have(out / folder, scan_frames), scan_frames)
        line("room pass", have(out / "moves" / name / "room", frames), frames)
        if spec["kind"] == "mind":
            got = have(out / "moves" / name / "mind", frames)
            line("mind pass", got, frames)
            wrong = []
            for f in got:
                with Image.open(frame_path(out / "moves" / name / "mind", f)) as im:
                    if im.size != size:
                        wrong.append(f)
            if wrong:
                print(f"  WARNING: {len(wrong)} mind frames are not {size[0]} by {size[1]} ({wrong[0]} to {wrong[-1]}): "
                      "move them away, a frame on disk is never rendered again")
    print(f"THE PASSED FRAMES in {a.piece}")
    needs = {"third": [], "first, the eyes' scan": [], "first, the camera": [], "true": []}
    prev = None
    for seg in cut["showcase"]:
        fs = segment_frames(seg, cfps)
        if seg["view"] in ("third", "all"):
            needs["third"] += fs
        if seg["view"] in ("true", "all"):
            needs["true"] += fs
        if seg["view"] == "all":
            needs["first, the eyes' scan"] += fs
        if seg["view"] == "first":
            after_dive = prev is not None and prev["view"] == "move" and cut["moves"][prev["move"]].get("direction") == "to_first"
            needs["first, the camera" if after_dive else "first, the eyes' scan"] += fs
        if seg["view"] == "move" and cut["moves"][seg["move"]]["kind"] == "head":
            needs["first, the eyes' scan"] += fs      # the eyes' side of the blink
        prev = seg
    folders = {"third": a.piece / "third", "first, the eyes' scan": a.piece / "scan", "first, the camera": a.piece / "first",
               "true": a.piece / a.true_frames}
    for key, fs in needs.items():
        line(key, have(folders[key], fs), fs)
    print(f"  {'the eye table':26s} {'there' if (a.piece / 'eye_frames.json').exists() else 'MISSING'}"
          f"   the sound {'there' if (a.piece / 'fake_audio.wav').exists() else 'missing: the videos will be silent'}")
    sp = out / "status.json"
    if sp.exists():
        steps = json.loads(sp.read_text(encoding="utf-8"))["steps"]
        print("THE STEPS SO FAR")
        for kind in ("scans", "room", "mind"):
            rs = [r for r in steps if r["step"].split()[0] == kind and r["made"]]
            if rs:
                print(f"  {kind:6s} {sum(r['made'] for r in rs):5d} frames in {sum(r['seconds'] for r in rs) / 3600.0:.2f} h, "
                      f"{sum(r['seconds'] for r in rs) / sum(r['made'] for r in rs):.2f} s a frame; the last step {rs[-1]['per_frame']} s a frame at {rs[-1]['at']}")


# ---- assemble -------------------------------------------------------------------------------------------------------

def assemble(a):
    import bisect

    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from compose import find_ffmpeg
    import first_still
    import assemble_rung2 as asm

    cfps, total, cut, table = load(a)
    piece = a.piece
    src_moves = (a.out / a.moves_from) if a.moves_from else a.out
    dst = a.out / a.videos
    dst.mkdir(parents=True, exist_ok=True)
    scratch = dst / "scratch"
    scratch.mkdir(exist_ok=True)
    spec_eyes = first_still.load_spec(piece, field="eyes")
    spec_cam = first_still.load_spec(piece, field="camera")
    piece_rows = spec_eyes["rows"]
    font, small = ImageFont.truetype(FONT, 22), ImageFont.truetype(FONT, 17)
    W, H = FRAME
    mrows = {name: {r["f"]: r for r in m.get("rows", [])} for name, m in table.items()}

    # ---- the plan: every frame's segment ----
    plan = []
    prev = None
    for seg in cut["showcase"]:
        kind = dict(seg)
        kind["frames"] = segment_frames(seg, cfps)
        if seg["view"] == "first":
            after_dive = prev is not None and prev["view"] == "move" and cut["moves"][prev["move"]].get("direction") == "to_first"
            kind["field"] = "camera" if after_dive else "eyes"
        if seg["view"] == "move":
            spec = cut["moves"][seg["move"]]
            kind["kind"], kind["direction"] = spec["kind"], spec.get("direction")
            rows = mrows.get(seg["move"], {})
            if spec["kind"] == "head":
                fs = [f for f in kind["frames"] if f in rows]
                # the run of frames with the lids shut, and which end of the move is on the eyes
                shut = [f for f in fs if float(rows[f].get("cover", 0.0)) >= 0.999]
                run = max(ds.runs(shut), key=lambda r: r[1] - r[0]) if shut else None
                if run is None and fs:
                    peak = max(fs, key=lambda f: float(rows[f].get("cover", 0.0)))
                    run = (peak, peak - 1)       # no shut frame: the picture changes at the lids' fullest cover
                kind["shut"] = run
                kind["eyes_first"] = bool(fs) and float(rows[fs[0]].get("eye_weight", 0.0)) > float(rows[fs[-1]].get("eye_weight", 0.0))
        plan += [(f, kind) for f in kind["frames"]]
        prev = seg
    span_all = (plan[0][0], plan[-1][0])
    if a.frames:
        lo, hi = (int(v) for v in a.frames.split("-"))
        plan = [(f, k) for f, k in plan if lo <= f <= hi]
    if not plan:
        sys.exit("no frame of the showcase in that span")
    first_f, last_f = plan[0][0], plan[-1][0]
    gaps = [(p[0], q[0]) for p, q in zip(plan, plan[1:]) if q[0] != p[0] + 1]
    if gaps:
        print(f"NOTE: the cut's segments do not tile the scene; the frames jump at {gaps[:4]}", flush=True)
    tag = f"_{first_f}_{last_f}" if (first_f, last_f) != span_all else ""

    # ---- pictures ----
    def mark(img, text, xy, fnt=small, fill=(235, 235, 235)):
        d = ImageDraw.Draw(img)
        x, y = xy
        d.text((x + 1, y + 1), text, font=fnt, fill=(0, 0, 0))
        d.text((x, y), text, font=fnt, fill=fill)

    def blank(size, text="not rendered"):
        img = Image.new("RGB", size, (0, 0, 0))
        mark(img, text, (12, size[1] // 2 - 10))
        return img

    def panel(path, size):
        if path is None or not path.exists():
            return blank(size)
        img = Image.open(path).convert("RGB")
        return img if img.size == size else img.resize(size, Image.LANCZOS)

    held_cache = {}
    missed = {}

    def move_file(name, which, f):
        """The move's picture of frame f: its own; with --hold-missing the nearest earlier one on disk (the first one
        where none is earlier); None where there is none."""
        folder = src_moves / "moves" / name / which
        path = frame_path(folder, f)
        if path.exists():
            return path
        missed[(name, which)] = missed.get((name, which), 0) + 1
        if not a.hold_missing:
            return None
        if folder not in held_cache:
            held_cache[folder] = sorted(int(p.stem.split("_")[1]) for p in folder.glob("frame_*.png")) if folder.exists() else []
        got = held_cache[folder]
        if not got:
            return None
        i = bisect.bisect_right(got, f) - 1
        return frame_path(folder, got[max(i, 0)])

    def to_image(arr):
        return Image.fromarray((np.clip(arr, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), "RGB")

    def first_field(f, field, row=None):
        """The First-Person picture of frame f as tools/first_still.py composes it, 960 by 540, 0 to 1; with `row`, under
        that row's lids and tint in place of the eye table's own. None where its picture is missing."""
        spec = spec_eyes if field == "eyes" else spec_cam
        if row is not None:
            spec = dict(spec, rows={f: row})
        shown, _ = first_still.compose_frame(piece, f, spec, scratch)
        return shown

    def camera_mask(w, h):
        key = (w, h, False)
        if key not in spec_cam["masks"]:
            path = scratch / f"mask_{w}x{h}.png"
            if not path.exists():
                asm.vignette_mask(path, w, h, spec_cam["feather"])
            spec_cam["masks"][key] = np.asarray(Image.open(path).convert("L"), dtype=np.float32)[..., None] / 255.0
        return spec_cam["masks"][key]

    def lay_camera(src, r, f):
        """A picture of the camera on the eyes (a move's room pass) with the senses of row r laid on as
        tools/first_still.py compose_frame lays them for field camera: the lid over the picture, then the tint and the
        pain's flash through the vignette mask, screened on. 0 to 1."""
        base = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32) / 255.0
        h, w = base.shape[:2]
        sun_uv, pain = r.get("sun_uv"), r.get("pain")
        cover = asm.row_cover(r)
        if cover > 0.0:
            lid_path = scratch / f"mlid_{f:04d}.png"
            asm.lid_image(lid_path, cover, r.get("lid", [0, 0, 0]), spec_cam["upper_share"], src, sun_uv, float(r.get("face_sun", 0.0)), size=(w, h))
            lid = np.asarray(Image.open(lid_path).convert("RGBA").resize((w, h), Image.BILINEAR), dtype=np.float32) / 255.0
            base = base * (1.0 - lid[..., 3:4]) + lid[..., :3] * lid[..., 3:4]
            lid_path.unlink()
        alpha = float(r.get("tint_a", 0.0)) * spec_cam["tint_gain"]
        tint = [float(c) * alpha for c in r.get("tint", [0, 0, 0])]
        if pain and float(pain[0]) > 1e-3:
            tint_path = scratch / f"mtint_{f:04d}.png"
            asm.tint_image(tint_path, tint, pain, size=(w, h))
            layer = np.asarray(Image.open(tint_path).convert("RGB"), dtype=np.float32) / 255.0
            tint_path.unlink()
        else:
            layer = np.zeros_like(base) + np.clip(np.array(tint, dtype=np.float32), 0.0, 1.0)[None, None, :]
        return np.clip(1.0 - (1.0 - base) * (1.0 - layer * camera_mask(w, h)), 0.0, 1.0)

    def eyes_share(kind, f):
        """How much of a head move's frame is the eyes' whole field, 0 to 1: nought on the camera's side of the blink,
        one on the eyes' side, and across the shut frames an even cross-fade."""
        s0, s1 = kind["shut"]
        n = s1 - s0 + 1
        if f < s0:
            w = 0.0
        elif f > s1:
            w = 1.0
        else:
            w = (f - s0 + 1) / (n + 1.0)
        return 1.0 - w if kind["eyes_first"] else w

    def head_move(kind, f):
        name = kind["move"]
        r = mrows.get(name, {}).get(f)
        if r is None or kind.get("shut") is None:
            return blank(ROOM_SIZE)
        e = eyes_share(kind, f)
        cam = eyes = None
        if e < 1.0:
            src = move_file(name, "room", f)
            if src is None:
                return blank(ROOM_SIZE)
            cam = lay_camera(src, r, f)
        if e > 0.0:
            pr = piece_rows.get(f)
            if pr is not None:
                merged = dict(pr)
                merged.update({k: r[k] for k in ("cover", "blink", "closed", "lid", "tint", "tint_a", "face_sun") if k in r})
                eyes = first_field(f, "eyes", merged)
            if eyes is None:
                return blank(ROOM_SIZE)
            if eyes.shape[:2] != (ROOM_SIZE[1], ROOM_SIZE[0]):
                eyes = np.asarray(to_image(eyes).resize(ROOM_SIZE, Image.LANCZOS), dtype=np.float32) / 255.0
        if cam is not None and cam.shape[:2] != (ROOM_SIZE[1], ROOM_SIZE[0]):
            cam = np.asarray(to_image(cam).resize(ROOM_SIZE, Image.LANCZOS), dtype=np.float32) / 255.0
        if cam is None:
            return to_image(eyes)
        if eyes is None:
            return to_image(cam)
        return to_image(cam * (1.0 - e) + eyes * e)

    def mind_move(kind, f):
        name = kind["move"]
        r = mrows.get(name, {}).get(f)
        if r is None:
            return blank(FRAME)
        w = float(r.get("weights", {}).get("model_w", 0.0))
        room = mind = None
        if w < 1.0:
            src = move_file(name, "room", f)
            if src is None:
                room = blank(FRAME)
            elif kind["direction"] == "to_first":
                room = to_image(lay_camera(src, r, f)).resize(FRAME, Image.LANCZOS)
            else:
                room = panel(src, FRAME)
        if w > 0.0:
            mind = panel(move_file(name, "mind", f), FRAME)
        if room is None:
            return mind
        if mind is None:
            return room
        return Image.blend(room, mind, w)      # C = A (1 - w) + B w, in display values

    def frame_picture(f, kind):
        view = kind["view"]
        if view == "third":
            img = panel(frame_path(piece / "third", f), ROOM_SIZE).resize(FRAME, Image.LANCZOS)
        elif view == "first":
            shown = first_field(f, kind["field"])
            img = blank(FRAME) if shown is None else to_image(shown).resize(FRAME, Image.LANCZOS)
        elif view == "true":
            img = panel(frame_path(piece / a.true_frames, f), FRAME)
        elif view == "move" and kind["kind"] == "head":
            img = head_move(kind, f).resize(FRAME, Image.LANCZOS)
        elif view == "move":
            img = mind_move(kind, f)
        elif view == "all":
            third = panel(frame_path(piece / "third", f), ROOM_SIZE)
            shown = first_field(f, "eyes")
            first = blank(ROOM_SIZE) if shown is None else to_image(shown)
            true = panel(frame_path(piece / a.true_frames, f), FRAME)
            three = Image.new("RGB", (1280, 1080), (0, 0, 0))
            three.paste(third.resize((640, 360), Image.LANCZOS), (0, 0))
            three.paste(first.resize((640, 360), Image.LANCZOS), (640, 0))
            three.paste(true.resize((1280, 720), Image.LANCZOS), (0, 360))
            mark(three, "Third-Person view", (10, 8))
            mark(three, "First-Person view", (650, 8))
            mark(three, "True-Person view, held camera over the glass body's left shoulder", (10, 368))
            img = Image.new("RGB", FRAME, (0, 0, 0))
            img.paste(three, ((W - 1280) // 2, 0))
            return img
        else:
            return blank(FRAME, f"no such view: {view}")
        if img.size != FRAME:
            img = img.resize(FRAME, Image.LANCZOS)
        mark(img, LABELS.get(kind.get("move") if view == "move" else view, view), (16, H - 36), font)
        return img

    # ---- the videos ----
    ffmpeg = find_ffmpeg()
    audio = piece / "fake_audio.wav"

    def writer(path, start):
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
               "-r", str(RENDER_FPS), "-i", "-"]
        if audio.exists():
            cmd += ["-ss", f"{(start - 1) / RENDER_FPS:.4f}", "-i", str(audio)]
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p"]
        if audio.exists():
            cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
        cmd += ["-movflags", "+faststart", str(path)]
        return subprocess.Popen(cmd, stdin=subprocess.PIPE)

    main_path = dst / f"{a.name}{tag}.mp4"
    outs = [(main_path, first_f, last_f, writer(main_path, first_f))]
    for seg in cut["showcase"]:
        if seg["view"] != "move":
            continue
        fs = segment_frames(seg, cfps)
        c0, c1 = fs[0] - CLIP_PAD, fs[-1] + CLIP_PAD
        if c0 < first_f or c1 > last_f:
            continue        # a clip only where the whole of it lies in the span
        path = dst / f"{a.name}_move_{seg['move']}.mp4"
        outs.append((path, c0, c1, writer(path, c0)))
    t0 = time.perf_counter()
    for n, (f, kind) in enumerate(plan):
        data = frame_picture(f, kind).tobytes()
        for path, lo, hi, proc in outs:
            if lo <= f <= hi:
                proc.stdin.write(data)
        if (n + 1) % 240 == 0:
            print(f"assembled {n + 1} of {len(plan)} frames, {time.perf_counter() - t0:.0f} s", flush=True)
    for path, lo, hi, proc in outs:
        proc.stdin.close()
        code = proc.wait()
        print(f"{'wrote' if code == 0 else 'FAILED'} {path}  {path.stat().st_size / 1e6:.1f} MB" if path.exists() else f"FAILED {path}", flush=True)
    for (name, which), n in sorted(missed.items()):
        print(f"NOTE: {n} frames of the {which} pass of {name} were not on disk: " + ("held from the nearest earlier one" if a.hold_missing else "shown as not rendered"), flush=True)
    print(f"ASSEMBLED frames {first_f} to {last_f}: {len(plan) / RENDER_FPS:.1f} s of film in {time.perf_counter() - t0:.0f} s", flush=True)


# ---- whole ----------------------------------------------------------------------------------------------------------

def whole(a):
    """The showcase with the moves in one command: what is missing of the moves, then the videos. Run it again after
    any interruption and it carries on."""
    a.out.mkdir(parents=True, exist_ok=True)
    sys.stdout = ds.Tee(sys.__stdout__, open(a.out / "whole.log", "a", encoding="utf-8"))
    print(f"WHOLE START {stamp()}: the moves of {a.cut.name} from {a.moves_blend.name} into {a.out}", flush=True)
    left = render(a)
    if left and not a.dry_run:
        left = render(a)
    if a.dry_run:
        return
    status(a)
    if left:
        print(f"WHOLE INCOMPLETE {stamp()}: {left} pictures of the moves are missing, so no video is made; run the same command again", flush=True)
        sys.exit(1)
    print(f"ALL FRAMES DONE {stamp()}", flush=True)
    assemble(a)
    print(f"WHOLE DONE {stamp()}", flush=True)


def main():
    ap = argparse.ArgumentParser(description="The showcase with the moves between views (rung 3)")
    ap.add_argument("what", choices=("render", "assemble", "status", "whole"))
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung3" / "transitions"), help="where the moves are rendered and the videos go")
    ap.add_argument("--piece", default=str(ROOT / "renders" / "rung2p"), help="the passed frames: third, first, scan, the True-Person frames, eye_frames.json, fake_audio.wav")
    ap.add_argument("--true-frames", default="show_r14", help="the folder under --piece of the passed True-Person frames")
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung3_transitions.blend"))
    ap.add_argument("--moves-blend", default=str(ROOT / "scenes" / "rung3_transitions_moves.blend"))
    ap.add_argument("--cut", default=str(ROOT / "data" / "cut.json"))
    ap.add_argument("--chunk", type=int, default=60, help="frames a step renders in one Blender process")
    ap.add_argument("--size", default="1920x1080", help="the mind passes")
    ap.add_argument("--eevee-samples", type=int, default=48)
    ap.add_argument("--samples", type=int, default=24, help="Cycles samples of the scans and the room passes")
    ap.add_argument("--videos", default="showcase", help="the folder under --out the videos go to")
    ap.add_argument("--name", default="transitions_showcase")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--no-heat-guard", action="store_true", help="render, whole: do not pause the render when the machine is too hot (tools/dev_showcase.py)")
    ap.add_argument("--on-battery", nargs="?", type=int, const=ds.BATTERY_FLOOR, default=None, metavar="PERCENT",
                    help="render, whole: render on the laptop's battery too, until its charge has fallen to this percent (20 if no number is given)")
    ap.add_argument("--dry-run", action="store_true", help="render, whole: print each step's command and frames, run nothing")
    ap.add_argument("--frames", default=None, help="assemble: a-b, that span only")
    ap.add_argument("--moves-from", default=None, help="assemble: the folder under --out the moves' frames are read from (default --out itself)")
    ap.add_argument("--hold-missing", action="store_true", help="assemble: a missing move frame is the nearest earlier one on disk: a rough from a stepped sample")
    a = ap.parse_args()
    a.out, a.piece = pathlib.Path(a.out).resolve(), pathlib.Path(a.piece).resolve()
    a.blend, a.moves_blend, a.cut = (pathlib.Path(p).resolve() for p in (a.blend, a.moves_blend, a.cut))
    {"render": render, "assemble": assemble, "status": status, "whole": whole}[a.what](a)


if __name__ == "__main__":
    main()

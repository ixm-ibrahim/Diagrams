"""The dev showcase (rung 2p, his thirteenth round of 2026-11-13: the whole thing at 1080p and at every frame, so it
runs smooth).

    python tools/dev_showcase.py render   [--frames 1-3480] [--chunk 240] [--to show_r13]
    python tools/dev_showcase.py assemble [--frames 1-3480] [--to show_r13] [--name dev_showcase]
    python tools/dev_showcase.py status   [--to show_r13]
    python tools/dev_showcase.py whole    [--first 1177-1273,300-420] [--to show_r14] [--videos showcase_r14]

whole: the showcase in one command that can be run again after any interruption and carries on: the spans named in
--first before anything else (the spans already passed off on, so a fault in one shows within the first hours), then
every frame, then the four videos. What it prints also goes to <to>/whole.log.

render: the scene chunk by chunk in order, and for each chunk only what is missing: the eyes' five scans (the scan, the
backdrop, the sky, the peel, the pane), the First-Person view (the model's seen part reads it), the True-Person view at
1920 by 1080 from the scene's own camera (the held camera over the glass body's left shoulder in
scenes/rung2p_hold50.blend), and the Third-Person view. A frame on disk is never rendered again, so the run can be
stopped (a file named STOP in the True frames' folder, looked for between steps) and started again where it was.
Every step's seconds go to <to>/status.json.

The heat guard (2026-11-16, its rule changed 2026-11-17): a render that the machine cannot cool pauses itself and
carries on by itself. While a step runs, the graphics card's thermometer (in effect the case's: the card does little
in these renders) and the processor's speed are read every half minute. Two minutes at 88 C or more, or at 80 C or more
with the processor held under its nominal speed while busy (the firmware does that when heat is not leaving the case,
as with the laptop's lid shut), end the step's Blender. A processor held back while the case is under 80 C does not
pause the render: it goes on at the pace the firmware allows, and a line HELD BACK says so. After a pause the render
waits until the thermometer reads 75 C or less and a wait is over (5 minutes after the first pause, then 15, 30, and an
hour for every later one), or 60 C or less at any time, and goes on with the frames still missing. Half an hour of
rendering without a pause, over however many steps, counts as cooled. --no-heat-guard turns it off.

The battery (2026-11-17): a render does not run the laptop's battery down. Two minutes on the battery end the step's
Blender and a line ON BATTERY says so; no step starts on the battery. The render goes on with the frames still missing
once the charger has been back for a minute (a line ON CHARGER). While it waits it does not ask the machine to stay
awake, so the laptop may sleep as it would without the render. --on-battery renders on the battery too, until its
charge has fallen to 20 percent (or to the percent given after it), and waits for the charger from there.

assemble: four videos at 24 frames a second with the stand-in sound, from the frames on disk, each with a small clock
in the scene's seconds:
  <name>_true_1080p.mp4     the True-Person view alone, 1920 by 1080
  <name>_three_views.mp4    1280 by 1080: Third-Person and First-Person on top (640 by 360 each), the True-Person view
                            across the bottom (1280 by 720)
  <name>_first.mp4          the First-Person view alone with its lids and edge tint, 960 by 540
  <name>_third.mp4          the Third-Person view alone, 960 by 540
With --frames a-b only that span; a frame whose True-Person picture is missing ends the span there.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
RENDER_FPS = 24
# every picture a scan writes for a frame: its colour (the peel has none), its positions and its index
SCANS = tuple((folder, pat) for folder in ("scan", "backdrop", "sky", "peel", "pane")
              for pat in ("frame_{:04d}.png", "pos_{:04d}.exr", "idx_{:04d}.exr") if not (folder == "peel" and pat.startswith("frame")))
FONT = r"C:\Windows\Fonts\arial.ttf"

# The heat guard. On the night of 2026-11-16 the laptop's lid was shut an hour into the last showcase of rung 2p: the
# frames went from 25 seconds each to minutes and then to an hour, and the graphics card stood at 96 C for hours,
# 9 C over its own greatest working temperature, with nothing to stop the render.
# On the morning of 2026-11-17, with the lid open and the laptop in use, the processor was held back for a few minutes
# with the thermometer at 72 C. The first rule paused the render for an hour for that, and would have gone on doing so:
# the count of pauses in a row was only set back by one step of half an hour, and no step that morning ran that long.
# So: a held-back processor pauses the render only when the case is warm as well, and the clean time adds up over steps.
# Measured: a healthy render reads 149 to 193 percent of the nominal speed and 58 to 66 C; held back, 60 to 77 percent.
HOT_C = 88              # the graphics card's thermometer at or over this is too hot (the card's own limit is 87 C)
WARM_C = 80             # a processor held back pauses the render only with the thermometer at or over this
START_C = 85            # no step starts while it reads this or more
SLOW_SPEED = 85.0       # the processor under this percent of its nominal speed ...
BUSY = 30.0             # ... while it is at least this percent busy: the firmware is holding it back
HOT_READS = 4           # readings in a row that pause the render
HELD_NOTE_MIN = 10      # minutes between the lines that say the processor is held back while the case is not warm
HEAT_EVERY = 30         # seconds between readings while a step runs
COOL_C = 75             # after a pause: this or less, and the wait over, starts it again
COOL_NOW_C = 60         # after a pause: this or less starts it again at once (the case is losing its heat again);
COOL_NOW_LEAST = 45     #   each such start in a row asks 5 C less of the next, down to this
WAITS_MIN = (5, 15, 30, 60)   # minutes of waiting after the first pause, the second in a row, ... (the last for all later ones)
CLEAN_MIN = 30          # minutes of rendering without a pause, over all steps, that count as cooled: the next pause is a first one
COOL_EVERY = 120        # seconds between readings while paused (a reading wakes a sleeping graphics card)
# pauses in a row; the thermometer reading that starts the render at once; the seconds rendered since the last pause
HEAT = {"pauses": 0, "quick": COOL_NOW_C, "clean": 0.0}

# The battery. On 2026-11-17 at 11:23 the charger was unplugged with the last showcase of rung 2p running. On its
# battery the laptop held the processor at 82 to 85 percent of its nominal speed, a frame took 135 seconds where it had
# taken 55, and the battery went from full to 52 percent in 70 minutes (20 to 23 W drawn, most of it by the render). A
# render that takes half a day is not worth the battery of someone working away from his desk: it waits for the charger.
ON_BATTERY = "the laptop on its battery"     # how the reason of a step ended for the battery begins
BATTERY_READS = 4       # readings in a row on the battery that end a step (two minutes: a plug moved to another socket does not)
CHARGER_READS = 2       # readings in a row on the charger that start the render again
BATTERY_EVERY = 30      # seconds between readings while the render waits for the charger
BATTERY_NOTE_MIN = 20   # minutes between the lines that say the render is still waiting
BATTERY_FLOOR = 20      # --on-battery without a number: the charge (percent) at which a render on the battery waits after all


def power():
    """(True if the laptop is running from its battery, the battery's charge in percent or None). Not on the battery
    when Windows cannot say: the render waits only when it is told plainly that the charger is away."""
    try:
        import ctypes

        class Status(ctypes.Structure):
            _fields_ = [("line", ctypes.c_ubyte), ("flag", ctypes.c_ubyte), ("percent", ctypes.c_ubyte), ("saver", ctypes.c_ubyte),
                        ("life", ctypes.c_ulong), ("full_life", ctypes.c_ulong)]

        s = Status()
        if not ctypes.windll.kernel32.GetSystemPowerStatus(ctypes.byref(s)):
            return False, None
        # line: 0 the charger away, 1 the charger connected, 255 not known
        return s.line == 0, (int(s.percent) if s.percent <= 100 else None)
    except Exception:
        return False, None


def power_text(charge):
    return "the battery at " + (f"{charge} percent" if charge is not None else "a charge that cannot be read")


def battery_low(floor):
    """(True if the render has to wait for the charger, the battery's charge): the laptop on its battery with its
    charge at or under `floor` percent. A floor of 100 or more: on the battery at all. Under a lower floor a charge
    that cannot be read does not stop the render."""
    if floor is None:
        return False, None
    away, charge = power()
    return away and (floor >= 100 or (charge is not None and charge <= floor)), charge


def awake(on):
    """Ask the machine not to fall asleep while this runs, or stop asking: a request that lasts as long as this process
    and changes no setting (a closed lid, or choosing Sleep, still sleeps)."""
    try:
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | (0x00000001 if on else 0))
    except Exception:
        pass


def wait_for_charger(label, stop):
    """The render paused because the laptop runs from its battery: wait until the charger is back (the battery, in this
    file's first lines). `stop` is the file whose presence ends the whole run."""
    away, charge = power()
    print(f"ON BATTERY {time.strftime('%Y-%m-%d %H:%M:%S')} at {label}: {power_text(charge)}. The render waits for the charger", flush=True)
    awake(False)
    t0 = noted = time.time()
    back = 0
    while True:
        if stop.exists():
            print(f"STOP found while waiting for the charger at {label}; ending", flush=True)
            sys.exit(0)
        time.sleep(BATTERY_EVERY)
        away, charge = power()
        back = 0 if away else back + 1
        if back >= CHARGER_READS:
            break
        if away and time.time() - noted >= BATTERY_NOTE_MIN * 60.0:
            noted = time.time()
            print(f"still on battery {time.strftime('%H:%M:%S')}: {power_text(charge)}, {(noted - t0) / 60.0:.0f} min waited", flush=True)
    awake(True)
    print(f"ON CHARGER {time.strftime('%Y-%m-%d %H:%M:%S')} after {(time.time() - t0) / 60.0:.0f} min: {power_text(charge)}. The render goes on", flush=True)


def machine():
    """What can be read of the machine's heat without administrator rights: the graphics card's thermometer (C), the
    processor's speed as a percent of its nominal speed, and the percent of its time it is busy. None for whatever
    cannot be read (no such card; counters named in another language)."""
    temp = speed = busy = None
    try:
        out = subprocess.run(["nvidia-smi", "--query-gpu=temperature.gpu", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True, timeout=30).stdout
        temp = float(out.strip().splitlines()[0])
    except Exception:
        pass
    try:
        out = subprocess.run(["typeperf", r"\Processor Information(_Total)\% Processor Performance",
                              r"\Processor Information(_Total)\% Processor Time", "-sc", "1"],
                             capture_output=True, text=True, timeout=60).stdout
        row = [ln for ln in out.splitlines() if ln.startswith('"') and "PDH-CSV" not in ln][-1]
        speed, busy = (float(v.strip().strip('"')) for v in row.split(",")[1:3])
    except Exception:
        pass
    return temp, speed, busy


def heat_text(temp, speed, busy):
    parts = []
    if temp is not None:
        parts.append(f"the graphics card {temp:.0f} C")
    if speed is not None and busy is not None:
        parts.append(f"the processor at {speed:.0f} percent of its nominal speed, {busy:.0f} percent busy")
    return ", ".join(parts) or "the machine's heat cannot be read"


def cool_down(label, why, stop):
    """The render paused for heat: wait until the machine has cooled (the heat guard, in this file's first lines).
    `stop` is the file whose presence ends the whole run."""
    HEAT["pauses"] += 1
    wait_min = WAITS_MIN[min(HEAT["pauses"], len(WAITS_MIN)) - 1]
    print(f"PAUSED {time.strftime('%Y-%m-%d %H:%M:%S')} at {label}: {why}. Waiting for the graphics card to read {COOL_C} C or less "
          f"and {wait_min} min to pass, or {HEAT['quick']} C or less at any time (pause {HEAT['pauses']} in a row)", flush=True)
    t0 = time.time()
    reads = 0
    while True:
        if stop.exists():
            print(f"STOP found while paused at {label}; ending", flush=True)
            sys.exit(0)
        time.sleep(COOL_EVERY)
        reads += 1
        temp, speed, busy = machine()
        waited = (time.time() - t0) / 60.0
        quick = temp is not None and temp <= HEAT["quick"]
        if quick or (waited >= wait_min and (temp is None or temp <= COOL_C)):
            break
        if reads % 10 == 0:
            print(f"still paused {time.strftime('%H:%M:%S')}: {heat_text(temp, speed, busy)}, {waited:.0f} min waited", flush=True)
    if quick:
        # the next start at once has to be earned by a cooler reading than this one, until a clean run
        HEAT["quick"] = max(HEAT["quick"] - 5, COOL_NOW_LEAST)
    print(f"RESUMED {time.strftime('%Y-%m-%d %H:%M:%S')} after {waited:.0f} min: {heat_text(temp, speed, busy)}", flush=True)


def run_guarded(cmd, fh, out, folders, guard=True, floor=100):
    """One step's command under the heat guard and the battery's: (its return code, None), or (None, why) if it was
    ended for heat or because the laptop runs from its battery (why then begins with ON_BATTERY). `floor` is the charge
    in percent at or under which a step on the battery is ended (100: on the battery at all; None: never). A step ended
    so may have been cut off while writing a picture, so the pictures it wrote in its last seconds (in `folders`, under
    `out`) are removed and made again."""
    proc = subprocess.Popen(cmd, stdout=fh, stderr=subprocess.STDOUT, cwd=str(ROOT))
    t0 = time.time()
    hot, drained, why, code = 0, 0, None, None
    held_run, noted = 0, 0.0      # held-back readings in a row; when the last HELD BACK line was printed
    while True:
        try:
            code = proc.wait(timeout=HEAT_EVERY if (guard or floor is not None) else None)
            break
        except subprocess.TimeoutExpired:
            pass
        if floor is not None:
            low, charge = battery_low(floor)
            drained = drained + 1 if low else 0
            if drained >= BATTERY_READS:
                why = ON_BATTERY + ", " + power_text(charge)
        if guard and not why:
            temp, speed, busy = machine()
            too_hot = temp is not None and temp >= HOT_C
            held = speed is not None and busy is not None and busy >= BUSY and speed < SLOW_SPEED
            # held back with the case not warm: the firmware's doing, and no danger; the render goes on at that pace.
            # With no thermometer to read, a held-back processor alone decides.
            warm = temp is None or temp >= WARM_C
            hot = hot + 1 if (too_hot or (held and warm)) else 0
            held_run = held_run + 1 if held else 0
            # on its battery the laptop holds the processor back as well; that is said by the battery's own lines
            if held_run >= 2 and not warm and not drained and time.time() - noted >= HELD_NOTE_MIN * 60.0:
                noted = time.time()
                print(f"HELD BACK {time.strftime('%Y-%m-%d %H:%M:%S')}: {heat_text(temp, speed, busy)}; "
                      f"the case is under {WARM_C} C, so the render goes on at that pace", flush=True)
            if hot >= HOT_READS:
                why = ("the graphics card too hot" if too_hot else "the processor held back and the case warm") + ", " + heat_text(temp, speed, busy)
        if why:
            cut = time.time()
            # the whole tree: the scans' step is a runner that starts Blender itself
            subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"], capture_output=True)
            proc.wait()
            for folder in folders:
                for p in (out / folder).iterdir():
                    if p.name.startswith(("frame_", "pos_", "idx_")) and p.stat().st_mtime >= cut - 3.0:
                        p.unlink()
            break
    # the time rendered since the last pause adds up over the steps (the spans of a showcase are short steps: counted
    # step by step, a morning of healthy rendering never set the pauses back)
    HEAT["clean"] += time.time() - t0
    if HEAT["clean"] / 60.0 >= CLEAN_MIN:
        HEAT["pauses"], HEAT["quick"] = 0, COOL_NOW_C
    if why and not why.startswith(ON_BATTERY):
        HEAT["clean"] = 0.0
    return code, why


def span(text, total):
    a, b = (int(v) for v in text.split("-")) if text else (1, total)
    return list(range(max(a, 1), min(b, total) + 1))


def runs(frames):
    """A list of frames as its runs: [(first, last)]."""
    out = []
    for f in frames:
        if out and f == out[-1][1] + 1:
            out[-1] = (out[-1][0], f)
        else:
            out.append((f, f))
    return out


def common(a):
    return ["--out", str(a.out), "--mind", "lidar", "--scan-size", "1024", "--scan-fov", "200", "--true-road", "orbit", "--step", "1",
            "--cut", str(a.cut), "--blend", str(a.blend), "--moves-blend", str(a.moves_blend)]


def render(a):
    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    total = int(round(beats["duration_seconds"] * RENDER_FPS / float(beats.get("pace", 1.0))))
    frames = span(a.frames, total)
    dst = a.out / a.to
    dst.mkdir(parents=True, exist_ok=True)
    logs = a.out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    status_path = dst / "status.json"
    status = json.loads(status_path.read_text(encoding="utf-8")) if status_path.exists() else {"steps": []}
    stop = dst / "STOP"
    awake(True)
    rung2 = [BLENDER, "-b", "--python", str(ROOT / "rungs" / "rung2.py"), "--", "render"]

    def missing(folder, pattern, fs):
        return [f for f in fs if not (a.out / folder / pattern.format(f)).exists()]

    guard = not a.no_heat_guard
    # the charge at or under which the render waits for the charger: on the battery at all, unless --on-battery
    floor = 100 if a.on_battery is None else a.on_battery

    def step(label, cmd, need, count, folders):
        """Run one step for the frames it still has to make; True if it left none missing."""
        while True:
            todo = need()
            if not todo:
                return True
            if stop.exists():
                print(f"STOP found before {label}; ending", flush=True)
                sys.exit(0)
            if battery_low(floor)[0]:
                wait_for_charger(label, stop)
                continue
            if guard:
                temp, speed, busy = machine()
                if temp is not None and temp >= START_C:
                    cool_down(label, "too hot to start, " + heat_text(temp, speed, busy), stop)
                    continue
            t0 = time.perf_counter()
            log = logs / f"dev_showcase_{label.split()[0]}.log"
            with open(log, "a", encoding="utf-8", errors="replace") as fh:
                fh.write(f"\n==== {time.strftime('%Y-%m-%d %H:%M:%S')} {label}: {len(todo)} frames\n")
                fh.flush()
                code, why = run_guarded(cmd(todo), fh, a.out, folders, guard, floor)
            secs = time.perf_counter() - t0
            left = need()
            made = len(todo) - len(left)
            rec = {"at": time.strftime("%Y-%m-%d %H:%M:%S"), "step": label, "frames": [todo[0], todo[-1]], "wanted": len(todo), "made": made,
                   "seconds": round(secs, 1), "per_frame": round(secs / max(made, 1), 2), "code": code}
            if why:
                rec["paused"] = why
            status["steps"].append(rec)
            status_path.write_text(json.dumps(status, indent=1), encoding="utf-8")
            on_battery = bool(why) and why.startswith(ON_BATTERY)
            print(f"{rec['at']} {label}: {made} of {len(todo)} frames in {secs / 60.0:.1f} min ({rec['per_frame']} s a frame), "
                  + ("ended on the battery" if on_battery else "ended for heat" if why else f"code {code}")
                  + (("; " + heat_text(*machine())) if guard and not why else ""), flush=True)
            count[0] += made
            if why:
                if on_battery:
                    wait_for_charger(label, stop)
                else:
                    cool_down(label, why, stop)
                continue
            return not left

    for i in range(0, len(frames), a.chunk):
        fs = frames[i:i + a.chunk]
        name = f"{fs[0]}-{fs[-1]}"
        for attempt in range(3):
            made = [0]
            ok = True
            # the eyes' scans: one call of the runner over the chunk's span of missing frames, each scan skipping the
            # frames it has (a call a gap, four frames between two kept ones, started five Blenders every four frames
            # and doubled the scans' cost)
            def scans_missing():
                return sorted({f for folder, pat in SCANS for f in missing(folder, pat, fs)})

            ok &= step(f"scans {name}", lambda todo: [
                sys.executable, str(ROOT / "tools" / "run_rung2.py"), "--scan", "--backdrop", "--sky", "--peel", "--pane", "--samples", "24",
                "--out", str(a.out), "--blend", str(a.blend), "--moves-blend", str(a.moves_blend), "--cut", str(a.cut), "--mind", "lidar",
                "--scan-size", "1024", "--scan-fov", "200", "--true-road", "orbit", "--frames", f"{todo[0]}-{todo[-1]}"], scans_missing, made,
                ("scan", "backdrop", "sky", "peel", "pane"))
            ok &= step(f"first {name}", lambda todo: rung2 + ["--view", "first"] + common(a) + ["--frames", f"{todo[0]}-{todo[-1]}"],
                       lambda: missing("first", "frame_{:04d}.png", fs), made, ("first",))
            ok &= step(f"true {name}", lambda todo: rung2 + ["--view", "true"] + common(a) + [
                "--eevee-samples", str(a.eevee_samples), "--size", a.size, "--frames", f"{todo[0]}-{todo[-1]}", "--to", a.to, "--no-frame-set"],
                lambda: missing(a.to, "frame_{:04d}.png", fs), made, (a.to,))
            ok &= step(f"third {name}", lambda todo: rung2 + ["--view", "third"] + common(a) + ["--frames", f"{todo[0]}-{todo[-1]}"],
                       lambda: missing("third", "frame_{:04d}.png", fs), made, ("third",))
            if ok:
                break
            if not made[0]:
                print(f"chunk {name}: a pass made nothing new; going on to the next chunk", flush=True)
                break
        print(f"CHUNK {name} {'complete' if ok else 'INCOMPLETE'} at {time.strftime('%H:%M:%S')}", flush=True)
    left = len(missing(a.to, "frame_{:04d}.png", frames))
    print(f"RENDERDONE: {len(frames) - left} of {len(frames)} True-Person frames on disk", flush=True)
    return left


class Tee:
    """What is printed goes to every stream given, at once (the console and a log)."""

    def __init__(self, *streams):
        self.streams = [s for s in streams if s is not None]

    def write(self, text):
        for s in self.streams:
            s.write(text)
            s.flush()

    def flush(self):
        for s in self.streams:
            s.flush()


def whole(a):
    """The showcase in one command (rung 2p's last showcase, 2026-11-16): the spans of --first, then every frame, then
    the videos. Each part makes only what is missing, so the command can be run again after any interruption. A full
    pass that leaves frames missing is tried once more before the videos are made."""
    dst = a.out / a.to
    dst.mkdir(parents=True, exist_ok=True)
    sys.stdout = Tee(sys.__stdout__, open(dst / "whole.log", "a", encoding="utf-8"))

    def stamp():
        return time.strftime("%Y-%m-%d %H:%M:%S")

    print(f"WHOLE START {stamp()}: {a.blend.name} to {a.to}, the videos to {a.videos}", flush=True)
    for s in [v.strip() for v in (a.first or "").split(",") if v.strip()]:
        a.frames = s
        render(a)
        print(f"FIRST SPAN {s} done {stamp()}", flush=True)
    print(f"FIRST SPANS DONE {stamp()}", flush=True)
    a.frames = None
    for attempt in range(2):
        if render(a) == 0:
            break
    print(f"ALL FRAMES DONE {stamp()}", flush=True)
    status(a)
    assemble(a)
    print(f"WHOLE DONE {stamp()}", flush=True)


def status(a):
    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    total = int(round(beats["duration_seconds"] * RENDER_FPS / float(beats.get("pace", 1.0))))
    frames = span(a.frames, total)
    scans_have = [f for f in frames if all((a.out / folder / pat.format(f)).exists() for folder, pat in SCANS)]
    print(f"{'scans':10s} {len(scans_have):5d} of {len(frames)}   (all five scans of a frame)")
    for folder, pat in (("first", "frame_{:04d}.png"), (a.to, "frame_{:04d}.png"), ("third", "frame_{:04d}.png")):
        have = [f for f in frames if (a.out / folder / pat.format(f)).exists()]
        print(f"{folder:10s} {len(have):5d} of {len(frames)}   " + (", ".join(f"{lo}-{hi}" for lo, hi in runs(have)[:8]) or "none"))
    sp = a.out / a.to / "status.json"
    if sp.exists():
        steps = json.loads(sp.read_text(encoding="utf-8"))["steps"]
        for kind in ("scans", "first", "true", "third"):
            rs = [r for r in steps if r["step"].startswith(kind) and r["made"]]
            if rs:
                print(f"{kind:6s} {sum(r['made'] for r in rs):5d} frames in {sum(r['seconds'] for r in rs) / 3600.0:.2f} h, "
                      f"{sum(r['seconds'] for r in rs) / sum(r['made'] for r in rs):.2f} s a frame; the last step {rs[-1]['per_frame']} s a frame at {rs[-1]['at']}")


def assemble(a):
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from compose import find_ffmpeg
    import first_still

    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    cfps = RENDER_FPS / float(beats.get("pace", 1.0))
    total = int(round(beats["duration_seconds"] * cfps))
    frames = span(a.frames, total)
    src = a.out / a.to
    have = []
    for f in frames:
        if not (src / f"frame_{f:04d}.png").exists():
            break
        have.append(f)
    if not have:
        sys.exit(f"no True-Person frame at {frames[0]} in {src}")
    if len(have) < len(frames):
        print(f"the True-Person frames run from {have[0]} to {have[-1]}; the span ends there", flush=True)
    dst = a.out / a.videos
    dst.mkdir(parents=True, exist_ok=True)
    scratch = dst / "scratch"
    scratch.mkdir(exist_ok=True)
    spec = first_still.load_spec(a.out, field=a.first_field)
    ffmpeg = find_ffmpeg()
    audio = a.out / "fake_audio.wav"
    font, small = ImageFont.truetype(FONT, 22), ImageFont.truetype(FONT, 17)
    tag = f"_{have[0]}_{have[-1]}" if len(have) < total else ""

    def writer(name, w, h):
        path = dst / f"{a.name}_{name}{tag}.mp4"
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{w}x{h}",
               "-r", str(RENDER_FPS), "-i", "-"]
        if audio.exists():
            cmd += ["-ss", f"{(have[0] - 1) / RENDER_FPS:.4f}", "-i", str(audio)]
        cmd += ["-c:v", "libx264", "-preset", "slow", "-crf", str(a.crf), "-pix_fmt", "yuv420p"]
        if audio.exists():
            cmd += ["-c:a", "aac", "-b:a", "128k", "-shortest"]
        cmd += ["-movflags", "+faststart", str(path)]
        return path, subprocess.Popen(cmd, stdin=subprocess.PIPE)

    kinds = {"true": ("true_1080p", 1920, 1080), "three": ("three_views", 1280, 1080), "first": ("first", 960, 540), "third": ("third", 960, 540)}
    wanted = [k.strip() for k in a.only.split(",")] if a.only else list(kinds)
    outs = {k: writer(*kinds[k]) for k in kinds if k in wanted}

    def mark(img, text, xy, fnt=small, fill=(235, 235, 235)):
        d = ImageDraw.Draw(img)
        x, y = xy
        d.text((x + 1, y + 1), text, font=fnt, fill=(0, 0, 0))
        d.text((x, y), text, font=fnt, fill=fill)

    def panel(path, size):
        if not path.exists():
            img = Image.new("RGB", size, (0, 0, 0))
            mark(img, "not rendered", (12, size[1] // 2 - 10))
            return img
        img = Image.open(path).convert("RGB")
        return img if img.size == size else img.resize(size, Image.LANCZOS)

    t0 = time.perf_counter()
    for n, f in enumerate(have):
        # the scene's own second; with --clock both, the second the whole showcase's player shows at this frame first (a
        # snippet's own player starts at nought, and he reads the showcase's player: his word of 2026-11-14)
        clock = f"{(f - 1) / cfps:6.1f} s" if a.clock == "scene" else f"   showcase player {(f - 1) / RENDER_FPS:.1f} s, scene {(f - 1) / cfps:.1f} s"
        true = Image.open(src / f"frame_{f:04d}.png").convert("RGB")
        if true.size != (1920, 1080):
            true = true.resize((1920, 1080), Image.LANCZOS)
        third = panel(a.out / "third" / f"frame_{f:04d}.png", (960, 540))
        shown, _ = first_still.compose_frame(a.out, f, spec, scratch)
        if shown is None:
            first = panel(a.out / "first" / "missing.png", (960, 540))
        else:
            first = Image.fromarray((shown * 255.0 + 0.5).astype(np.uint8), "RGB")
            first = first if first.size == (960, 540) else first.resize((960, 540), Image.LANCZOS)
        three = Image.new("RGB", (1280, 1080), (0, 0, 0))
        three.paste(third.resize((640, 360), Image.LANCZOS), (0, 0))
        three.paste(first.resize((640, 360), Image.LANCZOS), (640, 0))
        three.paste(true.resize((1280, 720), Image.LANCZOS), (0, 360))
        mark(three, "Third-Person view", (10, 8))
        mark(three, "First-Person view", (650, 8))
        mark(three, "True-Person view, held camera over the glass body's left shoulder", (10, 368))
        mark(three, clock.strip(), (1280 - 16 - int(ImageDraw.Draw(three).textlength(clock.strip(), font=font)), 1080 - 30), font)
        true_out, first_out, third_out = true.copy(), first.copy(), third.copy()
        mark(true_out, "True-Person view" + clock, (16, 1080 - 36), font)
        mark(first_out, "First-Person view" + clock, (10, 540 - 28))
        mark(third_out, "Third-Person view" + clock, (10, 540 - 28))
        for key, img in (("true", true_out), ("three", three), ("first", first_out), ("third", third_out)):
            if key in outs:
                outs[key][1].stdin.write(img.tobytes())
        if (n + 1) % 240 == 0:
            print(f"assembled {n + 1} of {len(have)} frames, {time.perf_counter() - t0:.0f} s", flush=True)
    for key, (path, proc) in outs.items():
        proc.stdin.close()
        code = proc.wait()
        print(f"{'wrote' if code == 0 else 'FAILED'} {path}  {path.stat().st_size / 1e6:.1f} MB" if path.exists() else f"FAILED {path}", flush=True)
    print(f"ASSEMBLED frames {have[0]} to {have[-1]}: {len(have) / RENDER_FPS:.1f} s of film", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("what", choices=("render", "assemble", "status", "whole"))
    ap.add_argument("--first", default=None, help="whole: the spans a-b,c-d rendered before the rest")
    ap.add_argument("--no-heat-guard", action="store_true",
                    help="render, whole: do not pause the render when the machine is too hot (see the heat guard in this file's first lines)")
    ap.add_argument("--on-battery", nargs="?", type=int, const=BATTERY_FLOOR, default=None, metavar="PERCENT",
                    help="render, whole: render on the laptop's battery too, until its charge has fallen to this percent (20 if no number is given); "
                         "by default the render waits for the charger (see the battery in this file's first lines)")
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2p"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung2p_hold50.blend"))
    ap.add_argument("--moves-blend", default=str(ROOT / "scenes" / "rung2p_moves.blend"))
    ap.add_argument("--cut", default=str(ROOT / "data" / "cut_test.json"))
    ap.add_argument("--frames", default=None, help="a-b; default the whole scene")
    ap.add_argument("--chunk", type=int, default=240, help="frames a step renders in one Blender process")
    ap.add_argument("--to", default="show_r13", help="the folder under --out of the True-Person frames")
    ap.add_argument("--size", default="1920x1080")
    ap.add_argument("--eevee-samples", type=int, default=48)
    ap.add_argument("--videos", default="showcase_r13", help="the folder under --out the videos go to")
    ap.add_argument("--name", default="dev_showcase")
    ap.add_argument("--crf", type=int, default=16)
    ap.add_argument("--clock", default="scene", choices=("scene", "both"),
                    help="the clock burnt into the videos: the scene's second alone, or the whole showcase's player second with it (for a snippet)")
    ap.add_argument("--only", default=None, help="assemble: write these videos alone, of true,three,first,third (default all four)")
    ap.add_argument("--first-field", default="eyes", choices=("eyes", "camera"),
                    help="the First-Person view: the eyes' whole field (their scan's ellipse) or the camera on the eyes (tools/first_still.py)")
    a = ap.parse_args()
    a.out = pathlib.Path(a.out).resolve()
    a.blend, a.moves_blend, a.cut = (pathlib.Path(p).resolve() for p in (a.blend, a.moves_blend, a.cut))
    {"render": render, "assemble": assemble, "status": status, "whole": whole}[a.what](a)


if __name__ == "__main__":
    main()

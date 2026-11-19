"""Drive rung 1 from outside Blender: build, render both views in chunks, assemble.

    python tools/run_rung1.py [--build] [--views true,third] [--chunk 336] [--assemble]

Each chunk is its own Blender process (short, resumable: frames already on disk are
skipped), with the console written to renders/rung1/logs/. Anything over two minutes
should run in the background.
"""
import argparse
import json
import pathlib
import subprocess
import sys
import time

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
OUT = ROOT / "renders" / "rung1"
BLEND = ROOT / "scenes" / "rung1.blend"


def run(args, log_path):
    with open(log_path, "w", encoding="utf-8") as log:
        t0 = time.perf_counter()
        r = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, cwd=str(ROOT))
        return r.returncode, time.perf_counter() - t0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build", action="store_true")
    ap.add_argument("--views", default="true,third")
    ap.add_argument("--chunk", type=int, default=336)
    ap.add_argument("--frames", default=None, help="a-b to limit the range")
    ap.add_argument("--assemble", action="store_true")
    a = ap.parse_args()
    logs = OUT / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    total = int(round(beats["duration_seconds"] * beats["fps"]))
    first, last = 1, total
    if a.frames:
        first, last = (int(v) for v in a.frames.split("-"))
    summary = {"chunks": []}
    base = [BLENDER, "-b", "--python", str(ROOT / "rungs" / "rung1.py"), "--"]
    if a.build:
        code, secs = run(base + ["build", "--out", str(OUT), "--blend", str(BLEND)], logs / "build.txt")
        print(f"build: code {code} in {secs:.0f} s", flush=True)
        if code != 0:
            sys.exit(code)
    for view in a.views.split(","):
        start = first
        while start <= last:
            end = min(last, start + a.chunk - 1)
            folder = OUT / view
            missing = [f for f in range(start, end + 1) if not (folder / f"frame_{f:04d}.png").exists()]
            if not missing:
                print(f"{view} {start}-{end}: done already", flush=True)
                start = end + 1
                continue
            code, secs = run(base + ["render", "--view", view, "--frames", f"{start}-{end}", "--out", str(OUT), "--blend", str(BLEND)],
                             logs / f"render_{view}_{start:04d}_{end:04d}.txt")
            n_after = sum(1 for f in range(start, end + 1) if (folder / f"frame_{f:04d}.png").exists())
            print(f"{view} {start}-{end}: code {code}, {len(missing)} to do, {n_after - (end - start + 1 - len(missing))} rendered in {secs:.0f} s", flush=True)
            summary["chunks"].append({"view": view, "start": start, "end": end, "code": code, "seconds": round(secs, 1)})
            if code != 0:
                print("chunk failed, retrying once", flush=True)
                code, secs = run(base + ["render", "--view", view, "--frames", f"{start}-{end}", "--out", str(OUT), "--blend", str(BLEND)],
                                 logs / f"render_{view}_{start:04d}_{end:04d}_retry.txt")
                summary["chunks"].append({"view": view, "start": start, "end": end, "code": code, "seconds": round(secs, 1), "retry": True})
            start = end + 1
    (OUT / "run_summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    if a.assemble:
        code, secs = run([sys.executable, str(ROOT / "tools" / "assemble.py")], logs / "assemble.txt")
        print(f"assemble: code {code} in {secs:.0f} s", flush=True)
    print("RUN DONE", flush=True)


if __name__ == "__main__":
    main()

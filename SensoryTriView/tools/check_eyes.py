"""The eye-point check (his eleventh review of 2026-11-11): the model rendered through the simulated eyes
themselves, the First-Person camera's own place, bearing, lens and frame, set beside the First-Person picture
of the same frame. From the eyes every splat sits on its own pixel in its own colour, so the two pictures
should agree up to the scan's resolution; what differs names a fault in the model.

    python tools/check_eyes.py --out renders/rung2o --blend scenes/rung2o.blend --cut data/cut_test.json --frames auto:8
    python tools/check_eyes.py --out renders/rung2o --blend scenes/rung2o.blend --frames 1651,2101,2731

--frames auto:N picks N frames with the eyes open, spread over the cut's True-Person segments and moves, among the
frames the First-Person view has; a list names them. The check frames are rendered through rungs/rung2.py
(--view check, frames already on disk skipped) at the First-Person frame's own size, then compared:

    mad        the mean difference over the frame, 0 to 255
    over24     the share of pixels differing by more than 24 in some channel
    mad_scan   the same mean difference with both pictures blurred to the scan's own footprint (what is left
               once the scan's resolution is allowed for)
    holes      the share of pixels dark in the model (under 16) where the picture is lit (over 48): surface missing

Writes <out>/check/compare_<frame>.png (picture, model, their difference), <out>/check/check_sheet.png and
<out>/check/summary.json."""
import argparse
import json
import math
import pathlib
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parents[1]
BLENDER = r"C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
FIRST_LENS = 20.0
SENSOR = 36.0


def label(img, text):
    d = ImageDraw.Draw(img)
    d.rectangle((0, 0, 8 + 7 * len(text), 18), fill=(0, 0, 0))
    d.text((4, 3), text, fill=(255, 255, 255))
    return img


def pick_frames(out, cut, n, chain_fps, step):
    """N frames with the eyes open, spread over the cut's True-Person segments and mind moves, among the
    First-Person frames rendered."""
    rows = {r["f"]: r for r in json.loads((out / "eye_frames.json").read_text(encoding="utf-8"))["rows"]}
    spans = []
    for seg in cut.get("showcase", []):
        if seg["view"] == "true" or (seg["view"] == "move" and cut["moves"][seg["move"]]["kind"] == "mind"):
            spans.append((int(round(float(seg["t0"]) * chain_fps)) + 1, int(round(float(seg["t1"]) * chain_fps))))
    if not spans:
        spans = [(min(rows), max(rows))]
    wanted = []
    for a, b in spans:
        for f in range(a, b + 1):
            if (f - 1) % step == 0 and (out / "first" / f"frame_{f:04d}.png").exists() and rows.get(f, {}).get("cover", 1.0) < 0.001:
                wanted.append(f)
    if not wanted:
        return []
    if n >= len(wanted):
        return wanted
    picks = sorted({wanted[int(round(i * (len(wanted) - 1) / (n - 1)))] for i in range(n)}) if n > 1 else [wanted[len(wanted) // 2]]
    return picks


def render(frames, args, out, blend):
    missing = [f for f in frames if not (out / "check" / f"frame_{f:04d}.png").exists()]
    if not missing:
        print("check: every frame rendered already", flush=True)
        return
    logs = out / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    cmd = [BLENDER, "-b", "--python", str(ROOT / "rungs" / "rung2.py"), "--", "render", "--view", "check",
           "--frames", ",".join(str(f) for f in missing) + ("," if len(missing) == 1 else ""), "--out", str(out), "--blend", str(blend), "--mind", "lidar",
           "--scan-size", str(args.scan_size), "--scan-fov", str(args.scan_fov), "--true-road", args.true_road,
           "--eevee-samples", str(args.eevee_samples)]
    with open(logs / "check.txt", "w", encoding="utf-8") as log:
        r = subprocess.run(cmd, stdout=log, stderr=subprocess.STDOUT, cwd=str(ROOT))
    print(f"check: rendered {len(missing)} frames, code {r.returncode}", flush=True)


def compare(f, out, scan_size, scan_fov):
    a = Image.open(out / "first" / f"frame_{f:04d}.png").convert("RGB")
    b = Image.open(out / "check" / f"frame_{f:04d}.png").convert("RGB")
    if b.size != a.size:
        b = b.resize(a.size, Image.LANCZOS)
    x = np.asarray(a).astype(np.float32)
    y = np.asarray(b).astype(np.float32)
    diff = np.abs(x - y)
    # the scan's footprint in the picture's pixels: its degrees per pixel over the picture's at its centre
    deg_scan = scan_fov / scan_size
    deg_pic = math.degrees(2.0 * math.atan(SENSOR / 2.0 / FIRST_LENS)) / a.width
    foot = deg_scan / deg_pic
    sigma = max(0.5, foot / 2.0)
    xa = np.asarray(a.filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32)
    yb = np.asarray(b.filter(ImageFilter.GaussianBlur(sigma))).astype(np.float32)
    lit = x.max(axis=2) > 48
    holes = (y.max(axis=2) < 16) & lit
    rec = {"frame": f, "mad": round(float(diff.mean()), 2), "over24": round(float((diff.max(axis=2) > 24).mean()), 4),
           "mad_scan": round(float(np.abs(xa - yb).mean()), 2), "holes": round(float(holes.mean()), 4),
           "scan_footprint_px": round(foot, 2)}
    d_img = Image.fromarray(np.clip(diff * 3.0, 0, 255).astype(np.uint8))
    sheet = Image.new("RGB", (a.width * 3 + 8, a.height))
    sheet.paste(label(a.copy(), f"the First-Person picture  frame {f}"), (0, 0))
    sheet.paste(label(b.copy(), f"the model from the eyes  frame {f}"), (a.width + 4, 0))
    sheet.paste(label(d_img, f"difference x3  mad {rec['mad']}  holes {100 * rec['holes']:.1f}%"), (2 * a.width + 8, 0))
    sheet.save(out / "check" / f"compare_{f:04d}.png")
    return rec, a, b


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2"))
    ap.add_argument("--blend", default=str(ROOT / "scenes" / "rung2.blend"))
    ap.add_argument("--cut", default=str(ROOT / "data" / "cut.json"))
    ap.add_argument("--frames", default="auto:8")
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--scan-size", type=int, default=1024)
    ap.add_argument("--scan-fov", type=float, default=200.0)
    ap.add_argument("--true-road", default="orbit")
    ap.add_argument("--eevee-samples", type=int, default=48)
    ap.add_argument("--no-render", action="store_true", help="compare the frames on disk alone")
    args = ap.parse_args()
    out = pathlib.Path(args.out).resolve()
    blend = pathlib.Path(args.blend).resolve()
    cut = json.loads(pathlib.Path(args.cut).read_text(encoding="utf-8"))
    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    chain_fps = 24.0 / float(beats.get("pace", 1.0))
    if args.frames.startswith("auto:"):
        frames = pick_frames(out, cut, int(args.frames.split(":")[1]), chain_fps, args.step)
    else:
        frames = [int(v) for v in args.frames.split(",") if v.strip()]
    if not frames:
        sys.exit("check: no frames to compare")
    print("check frames:", frames, flush=True)
    (out / "check").mkdir(parents=True, exist_ok=True)
    if not args.no_render:
        render(frames, args, out, blend)
    recs, tiles = [], []
    for f in frames:
        if not (out / "check" / f"frame_{f:04d}.png").exists():
            print(f"check: frame {f} not rendered", flush=True)
            continue
        rec, a, b = compare(f, out, args.scan_size, args.scan_fov)
        recs.append(rec)
        tiles.append((a, b, f))
        print(f"frame {f}: mad {rec['mad']}, over24 {100 * rec['over24']:.1f}%, mad at the scan's footprint {rec['mad_scan']}, holes {100 * rec['holes']:.2f}%", flush=True)
    if tiles:
        w, h = 480, 270
        sheet = Image.new("RGB", (w * len(tiles) + 4 * (len(tiles) - 1), h * 2 + 4))
        for i, (a, b, f) in enumerate(tiles):
            sheet.paste(label(a.resize((w, h), Image.LANCZOS), f"picture  f{f} ({(f - 1) / chain_fps:.1f} s)"), (i * (w + 4), 0))
            sheet.paste(label(b.resize((w, h), Image.LANCZOS), f"model from the eyes  f{f}"), (i * (w + 4), h + 4))
        sheet.save(out / "check" / "check_sheet.png")
    summary = {"frames": recs, "mean_mad": round(sum(r["mad"] for r in recs) / len(recs), 2) if recs else None,
               "mean_mad_scan": round(sum(r["mad_scan"] for r in recs) / len(recs), 2) if recs else None,
               "mean_holes": round(sum(r["holes"] for r in recs) / len(recs), 4) if recs else None}
    (out / "check" / "summary.json").write_text(json.dumps(summary, indent=1), encoding="utf-8")
    print("CHECK DONE", json.dumps({k: v for k, v in summary.items() if k != "frames"}), flush=True)


if __name__ == "__main__":
    main()

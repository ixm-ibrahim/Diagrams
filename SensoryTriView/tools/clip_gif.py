"""A short looping clip from a run of frames (rung 2p): the held camera's frames played in order with a caption strip,
as an animated GIF, for judging the model's own motion (the memory's drift, the rings, the lightning) where a still
cannot show it.

    python tools/clip_gif.py --folder renders/rung2p/clip_chime --frames 2656-2701 --step 5 --out renders/rung2p/review/clip_chime.gif \\
        --ms 200 --text "True-Person view, 88.5 to 90 s ..." [--crop WxH] [--box x0,y0,x1,y1] [--scale 0.5] \
        [--dither none] [--mp4 clip.mp4]

--dither none keeps a GIF's flat surfaces flat (the default dither speckles them, which reads as grain); --mp4 writes the
same frames as a video beside the GIF, in full colour.
"""
import argparse
import pathlib
import shutil
import subprocess
import sys
import tempfile

from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from label_stills import label  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True)
    ap.add_argument("--frames", required=True, help="a-b, every --step from a")
    ap.add_argument("--step", type=int, default=5)
    ap.add_argument("--out", required=True)
    ap.add_argument("--ms", type=int, default=200, help="milliseconds a frame is shown")
    ap.add_argument("--text", default="")
    ap.add_argument("--crop", default=None, help="WxH about the frame's centre")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--box", default=None, help="x0,y0,x1,y1: the region kept, in the frame's own pixels")
    ap.add_argument("--dither", default="fs", choices=("fs", "none"))
    ap.add_argument("--mp4", default=None, help="also write the frames as a video here")
    a = ap.parse_args()
    f0, f1 = (int(v) for v in a.frames.split("-"))
    folder = pathlib.Path(a.folder)
    frames = []
    for f in range(f0, f1 + 1, a.step):
        p = folder / f"frame_{f:04d}.png"
        if not p.exists():
            print("missing", p)
            continue
        im = Image.open(p).convert("RGB")
        if a.box:
            im = im.crop(tuple(int(v) for v in a.box.split(",")))
        if a.crop:
            w, h = (int(v) for v in a.crop.lower().split("x"))
            cx, cy = im.width // 2, im.height // 2
            im = im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
        if a.scale != 1.0:
            im = im.resize((int(im.width * a.scale), int(im.height * a.scale)), Image.LANCZOS)
        frames.append(label(im, a.text, size=20) if a.text else im)
    if not frames:
        sys.exit("no frames")
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    dither = Image.Dither.FLOYDSTEINBERG if a.dither == "fs" else Image.Dither.NONE
    pal = [fr.quantize(colors=255, method=Image.Quantize.MEDIANCUT, dither=dither) for fr in frames]
    pal[0].save(out, save_all=True, append_images=pal[1:], duration=a.ms, loop=0, optimize=False)
    print("wrote", out, len(frames), "frames at", a.ms, "ms")
    if a.mp4:
        ff = shutil.which("ffmpeg")
        if ff is None:
            sys.exit("no ffmpeg for --mp4")
        with tempfile.TemporaryDirectory() as tmp:
            for i, fr in enumerate(frames):
                w, h = fr.width - fr.width % 2, fr.height - fr.height % 2
                fr.crop((0, 0, w, h)).save(pathlib.Path(tmp) / f"f_{i:04d}.png")
            # played three times over, so a player that does not loop still shows the motion for a few seconds
            subprocess.run([ff, "-y", "-loglevel", "error", "-stream_loop", "2", "-framerate", f"{1000.0 / a.ms:.3f}", "-i", str(pathlib.Path(tmp) / "f_%04d.png"),
                            "-c:v", "libx264", "-crf", "14", "-pix_fmt", "yuv420p", str(a.mp4)], check=True)
        print("wrote", a.mp4)


if __name__ == "__main__":
    main()

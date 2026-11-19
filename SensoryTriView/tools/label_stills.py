"""Label review stills (rung 2p): a caption strip under each frame naming the view, the second, what to look at
and the camera, and an optional crop about the frame's centre, where the simulated head sits from the held
camera. Writes the labelled stills into a folder.

    python tools/label_stills.py --out renders/rung2p --folder true16 --dest renders/rung2p/review \\
        --still 211 "True-Person, 7.0 s: the alarm's rings and the red ears" --crop 1400x900
"""
import argparse
import pathlib

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
FONT = r"C:\Windows\Fonts\arial.ttf"


def label(img, text, size=26):
    import textwrap
    width = max(40, int(img.width / (size * 0.52)))
    lines = []
    for para in text.replace("\r", "").split("\n"):
        lines.extend(textwrap.wrap(para.strip(), width) or [""])
    strip = len(lines) * (size + 4) + 12
    out = Image.new("RGB", (img.width, img.height + strip), (12, 12, 12))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)
    try:
        font = ImageFont.truetype(FONT, size)
    except OSError:
        font = ImageFont.load_default()
    y = img.height + 6
    for line in lines:
        d.text((16, y), line, fill=(235, 235, 235), font=font)
        y += size + 4
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2p"))
    ap.add_argument("--folder", default="true16")
    ap.add_argument("--dest", default=None)
    ap.add_argument("--crop", default=None, help="WxH about the frame's centre; the whole frame by default")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--still", nargs=2, action="append", metavar=("FRAME", "TEXT"), default=[])
    ap.add_argument("--chain-fps", type=float, default=30.0)
    a = ap.parse_args()
    out = pathlib.Path(a.out)
    dest = pathlib.Path(a.dest) if a.dest else out / "review"
    dest.mkdir(parents=True, exist_ok=True)
    for frame, text in a.still:
        f = int(frame)
        src = out / a.folder / f"frame_{f:04d}.png"
        im = Image.open(src).convert("RGB")
        if a.crop:
            w, h = (int(v) for v in a.crop.lower().split("x"))
            cx, cy = im.width // 2, im.height // 2
            im = im.crop((cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2))
        if a.scale != 1.0:
            im = im.resize((int(im.width * a.scale), int(im.height * a.scale)), Image.LANCZOS)
        t = (f - 1) / a.chain_fps
        lab = label(im, text.replace("{t}", f"{t:.2f}"))
        path = dest / f"still_{f:04d}.png"
        lab.save(path)
        print("wrote", path)


if __name__ == "__main__":
    main()

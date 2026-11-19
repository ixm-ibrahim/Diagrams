"""A review sheet (rung 2p): the same region of several frames side by side, each panel marked with its second, over
one caption strip that says what is seen, from which camera, and what to look at.

    python tools/sheet_stills.py --folder renders/rung2p/side4k --frames 151,181,211,241 --box 520,300,2320,2160 \
        --scale 0.5 --out renders/rung2p/review/sheet_waking.png --text "True-Person view at ..." [--marks "5 s,6 s,7 s,8 s"]

A panel's mark is its frame's chain second unless --marks names them.
"""
import argparse
import pathlib
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from label_stills import FONT, label  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", required=True)
    ap.add_argument("--frames", required=True, help="a,b,c")
    ap.add_argument("--box", default=None, help="x0,y0,x1,y1: the region kept, in the frame's own pixels")
    ap.add_argument("--scale", type=float, default=1.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--text", default="")
    ap.add_argument("--marks", default=None, help="a mark per panel, comma separated, in place of the seconds")
    ap.add_argument("--chain-fps", type=float, default=30.0)
    ap.add_argument("--gap", type=int, default=6)
    ap.add_argument("--text-size", type=int, default=24)
    a = ap.parse_args()
    frames = [int(v) for v in a.frames.split(",")]
    marks = a.marks.split(",") if a.marks else [f"{(f - 1) / a.chain_fps:g} s" for f in frames]
    panels = []
    for f in frames:
        im = Image.open(pathlib.Path(a.folder) / f"frame_{f:04d}.png").convert("RGB")
        if a.box:
            im = im.crop(tuple(int(v) for v in a.box.split(",")))
        if a.scale != 1.0:
            im = im.resize((int(im.width * a.scale), int(im.height * a.scale)), Image.LANCZOS)
        panels.append(im)
    w, h = panels[0].size
    sheet = Image.new("RGB", (len(panels) * w + (len(panels) - 1) * a.gap, h), (12, 12, 12))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype(FONT, 30)
    except OSError:
        font = ImageFont.load_default()
    for i, (im, mark) in enumerate(zip(panels, marks)):
        x = i * (w + a.gap)
        sheet.paste(im, (x, 0))
        box = d.textbbox((0, 0), mark, font=font)
        d.rectangle((x, 0, x + box[2] + 24, box[3] + 20), fill=(0, 0, 0))
        d.text((x + 12, 8), mark, fill=(240, 240, 240), font=font)
    out = pathlib.Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    (label(sheet, a.text, size=a.text_size) if a.text else sheet).save(out)
    print("wrote", out, sheet.size)


if __name__ == "__main__":
    main()

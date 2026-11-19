"""Assemble rung 2's roughs from the rendered sequences with FFmpeg.

    python tools/assemble_rung2.py [--out renders/rung2] [--crf 18] [--only piece|showcase|moves|sheets]

Writes into the output folder:
  piece.mp4               1920 by 1080: the final layout at half scale. Third-Person 960 by 432 top
                          left, First-Person 960 by 432 top right (its blinks, lids and edge tint
                          laid over), the True-Person view 1920 by 648 across the bottom (rung 1's
                          frames).
  showcase.mp4            1920 by 1080: Third-Person alone, the move into First-Person, First-Person
                          alone, the move back into Third-Person by his other side, Third-Person,
                          the move into True-Person, True-Person alone, then all three together.
  showcase_<view>.mp4     the showcase's whole span from each camera alone, third, first and true (the
                          last the showcase itself), a regression test of the three views of one scene
                          (his seventh review of 2026-11-10); with --step, each one's _fast cut too, and
                          triview_fast.mp4 with the three together, Third and First over True.
  moves.mp4               the moves one after the other, each labelled.
  move_<name>.mp4         each move alone.
  contact_sheet.png       one piece frame per beat, a second into each beat, two columns.
  moves_sheet.png         eight frames across each move, one row per move.

The eye's lids and tint come from renders/rung2/eye_frames.json (the piece) and
moves_frames.json (the moves) as tiny per-frame images this tool writes and FFmpeg scales up:
a lid frame (8 by 64, colour and alpha, the upper lid down from the top and the lower lid up
from the bottom by the frame's cover, scaled with bilinear filtering so the edge is soft) laid
over the picture, and a tint frame screened on through a vignette mask. Tuning them means
rerunning this tool, not a render. FFmpeg is called by absolute path; paths inside filter
graphs are relative to the project folder.
"""
import argparse
import json
import math
import os
import pathlib
import shutil
import struct
import subprocess
import sys
import textwrap
import zlib

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from compose import find_ffmpeg  # noqa: E402

FPS = 24          # the render's frames a second, for FFmpeg
CFPS = 24.0       # frames per chain second (data/beats.json pace), for the cut's and the beats' seconds; set in main()
FONTS = {"regular": r"C:\Windows\Fonts\arial.ttf", "bold": r"C:\Windows\Fonts\arialbd.ttf"}
ENC = ["-c:v", "libx264", "-preset", "medium", "-pix_fmt", "yuv420p", "-movflags", "+faststart"]


def cfile(path):
    """A path for an FFmpeg concat list: absolute, since the demuxer resolves relative ones against the list file."""
    return pathlib.Path(path).resolve().as_posix()


def rel(path):
    return os.path.relpath(str(path), str(ROOT)).replace("\\", "/")


def esc(text):
    return (text.replace("\\", "\\\\").replace(":", "\\:").replace(",", "\\,")
            .replace("'", "\u2019").replace("%", "%%"))


# ---- tiny PNGs ------------------------------------------------------------------------

def write_png(path, w, h, rows, color_type):
    """rows: list of bytes per row; color_type 0 grey, 2 RGB, 6 RGBA."""
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = b"".join(b"\x00" + r for r in rows)
    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
    with open(path, "wb") as fh:
        fh.write(png)


def flat_png(path, rgb, alpha=None, size=8):
    r, g, b = (max(0, min(255, int(round(v * 255)))) for v in rgb)
    if alpha is None:
        row = bytes((r, g, b)) * size
        write_png(path, size, size, [row] * size, 2)
    else:
        a = max(0, min(255, int(round(alpha * 255))))
        row = bytes((r, g, b, a)) * size
        write_png(path, size, size, [row] * size, 6)


def vignette_mask(path, w, h, feather):
    """Grey mask: 0 inside, rising smoothly to 1 at the frame edge over the outer feather fraction."""
    rows = []
    for y in range(h):
        ny = abs(2.0 * (y + 0.5) / h - 1.0)
        row = bytearray(w)
        for x in range(w):
            nx = abs(2.0 * (x + 0.5) / w - 1.0)
            r = (nx ** 4 + ny ** 4) ** 0.25
            u = (r - (1.0 - feather)) / feather
            u = 0.0 if u < 0 else 1.0 if u > 1 else u
            row[x] = int(round(255 * u * u * (3 - 2 * u)))
        rows.append(bytes(row))
    write_png(path, w, h, rows, 0)


LID_ROWS = 64
# the light through a closed lid (his tenth review of 2026-11-10): the lids' colour from the eye table,
# shaped by the picture behind them blurred as the lids diffuse it (LID_FLAT of it flat, the rest by the
# picture's light over its mean), and the sun's own spot where the sun stands, by how far the face is
# toward it
LID_FLAT = 0.45
LID_BLUR = 6            # the blur's radius on the picture at an eighth of its size: about fifty pixels of the frame
LID_SUN_SIGMA = 0.1     # the sun's spot, as a share of the frame's width
LID_SUN_GAIN = 0.6
LID_SUN_COLOUR = (1.0, 0.55, 0.3)
# the First-Person flash toward a pain (rung 2p, his specification of 2026-11-12): a broad red glow centred where
# the pain lies in the picture, or past the frame's edge toward it when it lies behind, screened on through the
# vignette mask with the tint, so it reads at the edge nearest the pain; its level from the eye table's pain
PAIN_SIGMA = 0.35       # the glow's spread, as a share of the frame's width
PAIN_GAIN = 0.9
PAIN_COLOUR = (1.0, 0.1, 0.05)


class Pictures:
    """The rendered frames of a folder, for the nearest at or before a frame (a stepped render holds each)."""

    def __init__(self):
        self.cache = {}

    def nearest(self, folder, f):
        folder = pathlib.Path(folder)
        if folder not in self.cache:
            have = sorted(int(p.stem.split("_")[1]) for p in folder.glob("frame_*.png")) if folder.exists() else []
            self.cache[folder] = have
        have = self.cache[folder]
        if not have:
            return None
        import bisect
        i = bisect.bisect_right(have, f) - 1
        if i < 0:
            # nothing rendered at or before: the first frame after, if it is the same held run; else no picture
            if have[0] - f >= 10:
                return None
            i = 0
        return folder / f"frame_{have[i]:04d}.png"


def lid_image(path, cover, rgb, upper_share, picture, sun_uv, face_sun, size=(960, 540)):
    """A full-size RGBA lid: the lids' colour shaped by the picture's blurred light, with the sun's spot;
    the alpha the wipe, the upper lid down from the top and the lower up from the bottom by the cover."""
    import numpy as np
    from PIL import Image, ImageFilter
    W, H = size
    base = np.array(rgb, dtype=np.float32)
    im = Image.open(picture).convert("RGB")
    small = im.resize((W // 8, H // 8), Image.BILINEAR).filter(ImageFilter.GaussianBlur(LID_BLUR))
    lum = np.asarray(small, dtype=np.float32) / 255.0
    lum = 0.2126 * lum[..., 0] + 0.7152 * lum[..., 1] + 0.0722 * lum[..., 2]
    mean = max(float(lum.mean()), 1e-3)
    m = np.asarray(Image.fromarray(lum / mean, mode="F").resize((W, H), Image.BILINEAR), dtype=np.float32)
    gain = LID_FLAT + (1.0 - LID_FLAT) * m
    out = base[None, None, :] * gain[..., None]
    if sun_uv is not None and face_sun > 0.0:
        yy, xx = np.mgrid[0:H, 0:W]
        dx = (xx + 0.5) / W - float(sun_uv[0])
        dy = ((yy + 0.5) / H - float(sun_uv[1])) * (H / W)
        g = np.exp(-(dx * dx + dy * dy) / (2.0 * LID_SUN_SIGMA ** 2)).astype(np.float32)
        out = out + np.array(LID_SUN_COLOUR, dtype=np.float32)[None, None, :] * (LID_SUN_GAIN * float(face_sun)) * g[..., None]
    out = np.clip(out, 0.0, 1.0)
    cover = max(0.0, min(1.0, float(cover)))
    y = np.arange(H, dtype=np.float32)
    a_top = np.clip(cover * upper_share * H - y, 0.0, 1.0)
    a_bot = np.clip(cover * (1.0 - upper_share) * H - (H - 1 - y), 0.0, 1.0)
    alpha = np.maximum(a_top, a_bot)[:, None]
    rgba = np.concatenate([out, np.broadcast_to(alpha[..., None], (H, W, 1))], axis=2)
    Image.fromarray((rgba * 255.0 + 0.5).astype(np.uint8), "RGBA").save(path)


def tint_image(path, rgb, pain, size=(960, 540)):
    """A full-size tint frame: the flat tint plus the pain's red flash (pain: level, u, v)."""
    import numpy as np
    from PIL import Image
    W, H = size
    a, u, v = pain
    out = np.zeros((H, W, 3), dtype=np.float32) + np.array(rgb, dtype=np.float32)[None, None, :]
    yy, xx = np.mgrid[0:H, 0:W]
    dx = (xx + 0.5) / W - float(u)
    dy = ((yy + 0.5) / H - float(v)) * (H / W)
    g = np.exp(-(dx * dx + dy * dy) / (2.0 * PAIN_SIGMA ** 2)).astype(np.float32)
    out = out + np.array(PAIN_COLOUR, dtype=np.float32)[None, None, :] * (PAIN_GAIN * float(a)) * g[..., None]
    Image.fromarray((np.clip(out, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8), "RGB").save(path)


def lid_png(path, cover, rgb, upper_share=0.75):
    """An 8 by 64 RGBA lid: the upper lid down from the top over cover * upper_share of the
    height, the lower lid up from the bottom over the rest, the boundary rows part covered."""
    cover = max(0.0, min(1.0, float(cover)))
    r, g, b = (max(0, min(255, int(round(v * 255)))) for v in rgb)
    top = cover * upper_share * LID_ROWS
    bot = cover * (1.0 - upper_share) * LID_ROWS
    rows = []
    for y in range(LID_ROWS):
        a_top = max(0.0, min(1.0, top - y))
        a_bot = max(0.0, min(1.0, bot - (LID_ROWS - 1 - y)))
        a = max(0, min(255, int(round(255 * max(a_top, a_bot)))))
        rows.append(bytes((r, g, b, a)) * 8)
    write_png(path, 8, LID_ROWS, rows, 6)


def row_cover(r):
    """The lid cover of a table row: the per-frame cover, or the old flags of a table without one."""
    if r is None:
        return 0.0
    if "cover" in r:
        return float(r["cover"])
    return 1.0 if (r.get("blink") or r.get("closed")) else 0.0


def write_overlays(folder, rows_by_frame, frames, tint_gain, upper_share=0.75, pictures=None, source=None):
    """lid_%04d.png (RGBA) and tint_%04d.png (RGB) for every frame of the range. A closed lid is drawn from
    the picture behind it (source, a folder of frames, or the row's own _src) when that picture exists:
    its light through the lids, with the sun's spot; else the flat lid of the table."""
    folder.mkdir(parents=True, exist_ok=True)
    pictures = pictures or Pictures()
    made = {}
    for f in frames:
        r = rows_by_frame.get(f)
        lid_path = folder / f"lid_{f:04d}.png"
        tint_path = folder / f"tint_{f:04d}.png"
        if lid_path.exists():
            lid_path.unlink()
        if r is None:
            lid_png(lid_path, 0.0, (0, 0, 0), upper_share)
            flat_png(tint_path, (0, 0, 0))
            continue
        c = row_cover(r)
        rgb = r.get("lid", [0, 0, 0]) if c > 0 else (0, 0, 0)
        src = r.get("_src", source)
        picture = pictures.nearest(src, f) if (c > 0 and src is not None) else None
        if picture is None:
            lid_png(lid_path, c, rgb, upper_share)
        else:
            sun_uv = r.get("sun_uv")
            face_sun = float(r.get("face_sun", 0.0))
            key = (str(picture), round(c, 3), tuple(round(v, 3) for v in rgb), None if sun_uv is None else tuple(round(v, 2) for v in sun_uv), round(face_sun, 2))
            if key in made:
                try:
                    os.link(made[key], lid_path)
                except OSError:
                    shutil.copy(made[key], lid_path)
            else:
                lid_image(lid_path, c, rgb, upper_share, picture, sun_uv, face_sun)
                made[key] = lid_path
        a = r.get("tint_a", 0.0) * tint_gain
        tint = [c * a for c in r.get("tint", [0, 0, 0])]
        pain = r.get("pain")
        if pain and float(pain[0]) > 1e-3:
            key = ("pain", round(float(pain[0]), 2), round(float(pain[1]), 2), round(float(pain[2]), 2), tuple(round(c, 3) for c in tint))
            if tint_path.exists():
                tint_path.unlink()
            if key in made:
                try:
                    os.link(made[key], tint_path)
                except OSError:
                    shutil.copy(made[key], tint_path)
            else:
                tint_image(tint_path, tint, pain)
                made[key] = tint_path
        else:
            flat_png(tint_path, tint)


# ---- FFmpeg ----------------------------------------------------------------------------

class FF:
    def __init__(self, ffmpeg, crf):
        self.ff = ffmpeg
        self.crf = crf

    def run(self, args, quiet=False):
        cmd = [self.ff, "-y", "-hide_banner", "-loglevel", "error"] + ([] if quiet else ["-stats"]) + args
        print("ffmpeg", " ".join(str(c) for c in args[:8]), "...", flush=True)
        subprocess.run(cmd, check=True, cwd=str(ROOT))

    def enc(self):
        return ENC + ["-crf", str(self.crf), "-r", str(FPS)]


def seq(folder, start, count, pattern="frame_%04d.png"):
    return ["-framerate", str(FPS), "-start_number", str(start), "-i", str(folder / pattern)] + ([] if count is None else [])


def stepped_frames(f0, f1, step):
    return [f for f in range(f0, f1 + 1) if (f - 1) % step == 0]


def fill_dir(out, folder, f0, f1, step):
    """For a stepped render (every step-th frame counted from frame 1), a folder under out/logs/fill
    where every frame of f0 to f1 is the nearest rendered frame at or before it, as a hard link (a
    copy where a link cannot be made), so the assembly runs unchanged and each rendered frame holds.
    The render folders themselves are never filled: a later full render would take the fills as done."""
    if step <= 1:
        return folder
    dst = out / "logs" / "fill" / folder.relative_to(out)
    dst.mkdir(parents=True, exist_ok=True)
    have = sorted(int(p.stem.split("_")[1]) for p in folder.glob("frame_*.png"))
    have_set = set(have)
    last = None
    for f in range(f0, f1 + 1):
        if f in have_set:
            last = f
        src_f = last if last is not None else next((h for h in have if h >= f), None)
        if src_f is None:
            continue
        target = dst / f"frame_{f:04d}.png"
        if target.exists():
            target.unlink()
        try:
            os.link(folder / f"frame_{src_f:04d}.png", target)
        except OSError:
            shutil.copy(folder / f"frame_{src_f:04d}.png", target)
    return dst


def fast_cut(ff, src, dst, step, speed):
    """One of each held run of frames of a stepped video, played at the pace asked for."""
    rate = FPS / step * speed
    ff.run(["-i", str(src), "-vf", f"select='not(mod(n\\,{step}))',setpts=N/({rate:.4f}*TB)",
            "-an"] + ff.enc() + ["-r", f"{rate:.4f}", str(dst)], quiet=True)
    return rate


def dissolve_expr(spec):
    """A mind move's composite: the room pass and the model pass cross-dissolved in display values
    by the move's weights, as an FFmpeg blend expression of T, the seconds since the move's first
    frame. The model then appears as the rest of the light dims and no light is added (his review
    of 2026-11-08, second); the two passes added, each faded on its own, brightened the overlap."""
    t0 = float(spec["t0"])
    d0, d1 = (float(v) - t0 for v in spec["dissolve"])
    s = f"st(0,clip((T-{d0:.4f})/{max(d1 - d0, 1e-3):.4f},0,1));st(0,ld(0)*ld(0)*(3-2*ld(0)))"
    w = "ld(0)" if spec["direction"] == "to_true" else "(1-ld(0))"
    return f"{s};A*(1-{w})+B*{w}"


def mind_move_graph(spec, room_label, mind_label, out_label, eye=None):
    """[room] and [mind] cross-dissolved; eye=(tint, lid, mask) puts the First-Person overlays on the
    room pass first, for the dive onto the eyes."""
    graph = ""
    if eye is not None:
        graph = eye_chain(room_label, eye[0], eye[1], eye[2], (960, 540), out_label + "_e") + ";"
        room_label = out_label + "_e"
    return (graph + f"[{room_label}]format=rgb24[{out_label}_r];[{mind_label}]format=rgb24[{out_label}_m];"
            f"[{out_label}_r][{out_label}_m]blend=all_expr='{dissolve_expr(spec)}':shortest=1[{out_label}]")


def eye_chain(label_in, label_tint, label_lid, label_mask, size, out_label):
    """The First-Person overlays: the lid over the render, then the tint screened on through the
    vignette mask, so the sense holding attention still colours the edge while the eyes are closed."""
    w, h = size
    return (f"[{label_lid}]scale={w}:{h}:flags=bilinear,format=rgba[{out_label}_ld];"
            f"[{label_in}]format=rgb24[{out_label}_b];"
            f"[{out_label}_b][{out_label}_ld]overlay=shortest=1:format=auto,format=rgb24[{out_label}_bl];"
            f"[{label_tint}]scale={w}:{h}:flags=neighbor,format=rgb24[{out_label}_tc];"
            f"[{label_mask}]format=rgb24[{out_label}_mk];"
            f"[{out_label}_tc][{out_label}_mk]blend=all_mode=multiply:shortest=1[{out_label}_tm];"
            f"[{out_label}_bl][{out_label}_tm]blend=all_mode=screen:shortest=1[{out_label}]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2"))
    ap.add_argument("--true", default=None, help="True-Person frames; default renders/rung2/true, else rung 1's")
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--only", default="all", choices=("all", "piece", "showcase", "moves", "sheets"))
    ap.add_argument("--tint-gain", type=float, default=None, help="override data/eyes.json's tint strength")
    ap.add_argument("--cut", default=str(ROOT / "data" / "cut.json"), help="the showcase order and the moves")
    ap.add_argument("--step", type=int, default=1, help="the render's step: every Nth frame rendered, each held in the videos")
    ap.add_argument("--speed", type=float, default=2.0, help="with --step, the pace of showcase_fast.mp4 over real time")
    ap.add_argument("--tag", default="", help="a name for a second cut's outputs: showcase_<tag>.mp4 and the rest")
    ap.add_argument("--audio", default=None, help="a soundtrack in the render's seconds (tools/fake_audio.py): laid under the showcase from the cut's first second, as showcase<tag>_sound.mp4")
    a = ap.parse_args()
    step = max(1, a.step)
    T = f"_{a.tag}" if a.tag else ""
    out = pathlib.Path(a.out).resolve()
    true_dir = pathlib.Path(a.true).resolve() if a.true else (out / "true" if (out / "true").exists() else ROOT / "renders" / "rung1" / "true")
    beats = json.loads((ROOT / "data" / "beats.json").read_text(encoding="utf-8"))
    cut = json.loads(pathlib.Path(a.cut).read_text(encoding="utf-8"))
    eyes_spec = json.loads((ROOT / "data" / "eyes.json").read_text(encoding="utf-8"))
    eye_table = json.loads((out / "eye_frames.json").read_text(encoding="utf-8"))
    moves_path = out / "moves_frames.json"
    moves_table = json.loads(moves_path.read_text(encoding="utf-8"))["moves"] if moves_path.exists() else {}
    tint_gain = a.tint_gain if a.tint_gain is not None else float(eyes_spec["tint"]["strength"])
    feather = float(eyes_spec["tint"].get("feather", 0.32))
    upper_share = float(eyes_spec.get("lids", {}).get("upper_share", 0.75))
    ff = FF(find_ffmpeg(), a.crf)
    textdir = out / "logs"
    textdir.mkdir(parents=True, exist_ok=True)
    for key, src in FONTS.items():
        dst = textdir / f"font_{key}.ttf"
        if not dst.exists():
            shutil.copy(src, dst)
    font = rel(textdir / "font_regular.ttf")
    bold = rel(textdir / "font_bold.ttf")
    global CFPS
    CFPS = FPS / float(beats.get("pace", 1.0))
    total = int(round(beats["duration_seconds"] * CFPS))
    frames = list(range(1, total + 1))

    # ---- overlays: the piece's timeline and the showcase's ----
    ov = out / "overlay"
    ov.mkdir(parents=True, exist_ok=True)
    masks = {}
    for size in ((960, 432), (960, 540)):
        p = ov / f"mask_{size[0]}x{size[1]}.png"
        if not p.exists():
            vignette_mask(p, size[0], size[1], feather)
        masks[size] = p
    third_dir, first_dir, true16_dir = out / "third", out / "first", out / "true16"
    pictures = Pictures()
    piece_rows = {r["f"]: r for r in eye_table["rows"]}
    write_overlays(ov / "piece", piece_rows, frames, tint_gain, upper_share, pictures=pictures, source=first_dir)
    show_rows = {}
    for seg in cut["showcase"]:
        f0, f1 = int(round(seg["t0"] * CFPS)) + 1, int(round(seg["t1"] * CFPS))
        if seg["view"] == "first":
            for f in range(f0, f1 + 1):
                show_rows[f] = piece_rows.get(f)
        elif seg["view"] == "move" and seg["move"] in moves_table and (
                moves_table[seg["move"]]["kind"] == "head" or cut["moves"][seg["move"]].get("direction") == "to_first"):
            # the move's lids are drawn from its own room pass, the eyes' picture at the road's exposure
            for r in moves_table[seg["move"]]["rows"]:
                show_rows[r["f"]] = dict(r, _src=out / "moves" / seg["move"] / "room")
    write_overlays(ov / f"show{T}", show_rows, frames, tint_gain, upper_share, pictures=pictures, source=first_dir)
    show = ov / f"show{T}"
    print("overlays written", flush=True)
    n_third = len(list(third_dir.glob("frame_*.png"))) if third_dir.exists() else 0
    n_first = len(list(first_dir.glob("frame_*.png"))) if first_dir.exists() else 0
    n_true = len(list(true_dir.glob("frame_*.png"))) if true_dir.exists() else 0
    print(f"frames: third {n_third}, first {n_first}, true {n_true}", flush=True)

    def piece_inputs(start):
        return (["-framerate", str(FPS), "-start_number", str(start), "-i", str(third_dir / "frame_%04d.png"),
                 "-framerate", str(FPS), "-start_number", str(start), "-i", str(first_dir / "frame_%04d.png"),
                 "-framerate", str(FPS), "-start_number", str(start), "-i", str(true_dir / "frame_%04d.png"),
                 "-framerate", str(FPS), "-start_number", str(start), "-i", str(ov / "piece" / "tint_%04d.png"),
                 "-framerate", str(FPS), "-start_number", str(start), "-i", str(ov / "piece" / "lid_%04d.png"),
                 "-loop", "1", "-framerate", str(FPS), "-i", str(masks[(960, 432)])])

    piece_graph = ("[0:v]crop=960:432:0:54,format=rgb24[t3];[1:v]crop=960:432:0:54[f0];"
                   + eye_chain("f0", "3:v", "4:v", "5:v", (960, 432), "fp") + ";"
                   "[t3][fp]hstack=inputs=2:shortest=1[top];[2:v]format=rgb24[tr];"
                   "[top][tr]vstack=inputs=2:shortest=1,format=yuv420p[frame]")

    if a.only in ("all", "piece") and n_third and n_first and n_true:
        ff.run(piece_inputs(1) + ["-filter_complex", piece_graph, "-map", "[frame]", "-shortest",
                                  "-frames:v", str(min(n_third, n_first, n_true))] + ff.enc() + [str(out / "piece.mp4")])

    # ---- the moves alone ----
    move_clips = {}
    if a.only in ("all", "moves", "showcase", "sheets"):
        for name, spec in cut["moves"].items():
            f0, f1 = int(round(spec["t0"] * CFPS)) + 1, int(round(spec["t1"] * CFPS)) + 1
            n = f1 - f0 + 1
            room = out / "moves" / name / "room"
            expect = n if step == 1 else len(stepped_frames(f0, f1, step))
            if not room.exists() or len(list(room.glob("frame_*.png"))) < expect:
                print(f"move {name}: frames missing, skipped", flush=True)
                continue
            room = fill_dir(out, room, f0, f1, step)
            clip = out / f"move_{name}.mp4"
            label = {"third_first": "Third-Person to First-Person", "first_third": "First-Person to Third-Person",
                     "third_true": "Third-Person to True-Person", "true_third": "True-Person to Third-Person",
                     "true_first": "True-Person to First-Person"}[name]
            text = f"drawtext=fontfile={bold}:fontsize=36:fontcolor=white@0.85:x=32:y=28:text='{esc(label + '   ' + str(spec['t0']) + ' to ' + str(spec['t1']) + ' s')}'"
            if spec["kind"] == "head":
                inputs = ["-framerate", str(FPS), "-start_number", str(f0), "-i", str(room / "frame_%04d.png"),
                          "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "tint_%04d.png"),
                          "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "lid_%04d.png"),
                          "-loop", "1", "-framerate", str(FPS), "-i", str(masks[(960, 540)])]
                graph = eye_chain("0:v", "1:v", "2:v", "3:v", (960, 540), "mv") + f";[mv]scale=1920:1080:flags=lanczos,{text},format=yuv420p[frame]"
            else:
                mind = fill_dir(out, out / "moves" / name / "mind", f0, f1, step)
                inputs = ["-framerate", str(FPS), "-start_number", str(f0), "-i", str(room / "frame_%04d.png"),
                          "-framerate", str(FPS), "-start_number", str(f0), "-i", str(mind / "frame_%04d.png")]
                eye = None
                if spec.get("direction") == "to_first":
                    inputs += ["-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "tint_%04d.png"),
                               "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "lid_%04d.png"),
                               "-loop", "1", "-framerate", str(FPS), "-i", str(masks[(960, 540)])]
                    eye = ("2:v", "3:v", "4:v")
                graph = mind_move_graph(spec, "0:v", "1:v", "mv", eye) + f";[mv]scale=1920:1080:flags=lanczos,{text},format=yuv420p[frame]"
            ff.run(inputs + ["-filter_complex", graph, "-map", "[frame]", "-frames:v", str(n)] + ff.enc() + [str(clip)])
            move_clips[name] = (clip, n)
        if move_clips and a.only in ("all", "moves"):
            gap = out / "logs" / "gap.mp4"
            ff.run(["-f", "lavfi", "-i", f"color=c=black:s=1920x1080:r={FPS}:d=0.5", "-frames:v", "12"] + ff.enc() + [str(gap)], quiet=True)
            lst = out / "logs" / "moves_list.txt"
            lines = []
            for name in cut["moves"]:
                if name in move_clips:
                    lines.append(f"file '{cfile(move_clips[name][0])}'")
                    lines.append(f"file '{cfile(gap)}'")
            lst.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
            ff.run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / "moves.mp4")], quiet=True)

    # ---- the showcase ----
    if a.only in ("all", "showcase"):
        segs = []
        ok = True
        for i, seg in enumerate(cut["showcase"]):
            f0, f1 = int(round(seg["t0"] * CFPS)) + 1, int(round(seg["t1"] * CFPS))
            n = f1 - f0 + 1
            path = out / "logs" / f"show{T}_{i:02d}_{seg['view']}.mp4"
            view = seg["view"]
            if view == "third":
                if n_third < f1:
                    ok = False
                    break
                ff.run(["-framerate", str(FPS), "-start_number", str(f0), "-i", str(third_dir / "frame_%04d.png"),
                        "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-frames:v", str(n)] + ff.enc() + [str(path)])
            elif view == "first":
                if n_first < f1:
                    ok = False
                    break
                inputs = ["-framerate", str(FPS), "-start_number", str(f0), "-i", str(first_dir / "frame_%04d.png"),
                          "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "tint_%04d.png"),
                          "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "lid_%04d.png"),
                          "-loop", "1", "-framerate", str(FPS), "-i", str(masks[(960, 540)])]
                graph = eye_chain("0:v", "1:v", "2:v", "3:v", (960, 540), "sf") + ";[sf]scale=1920:1080:flags=lanczos,format=yuv420p[frame]"
                ff.run(inputs + ["-filter_complex", graph, "-map", "[frame]", "-frames:v", str(n)] + ff.enc() + [str(path)])
            elif view == "move":
                name = seg["move"]
                if name not in move_clips:
                    ok = False
                    break
                # the move clip without its label
                spec = cut["moves"][name]
                m0 = int(round(spec["t0"] * CFPS)) + 1
                room = fill_dir(out, out / "moves" / name / "room", f0, f1, step)
                if spec["kind"] == "head":
                    inputs = ["-framerate", str(FPS), "-start_number", str(f0), "-i", str(room / "frame_%04d.png"),
                              "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "tint_%04d.png"),
                              "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "lid_%04d.png"),
                              "-loop", "1", "-framerate", str(FPS), "-i", str(masks[(960, 540)])]
                    graph = eye_chain("0:v", "1:v", "2:v", "3:v", (960, 540), "sm") + ";[sm]scale=1920:1080:flags=lanczos,format=yuv420p[frame]"
                else:
                    mind = fill_dir(out, out / "moves" / name / "mind", f0, f1, step)
                    inputs = ["-framerate", str(FPS), "-start_number", str(f0), "-i", str(room / "frame_%04d.png"),
                              "-framerate", str(FPS), "-start_number", str(f0), "-i", str(mind / "frame_%04d.png")]
                    eye = None
                    if spec.get("direction") == "to_first":
                        inputs += ["-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "tint_%04d.png"),
                                   "-framerate", str(FPS), "-start_number", str(f0), "-i", str(show / "lid_%04d.png"),
                                   "-loop", "1", "-framerate", str(FPS), "-i", str(masks[(960, 540)])]
                        eye = ("2:v", "3:v", "4:v")
                    graph = mind_move_graph(spec, "0:v", "1:v", "sm", eye) + ";[sm]scale=1920:1080:flags=lanczos,format=yuv420p[frame]"
                ff.run(inputs + ["-filter_complex", graph, "-map", "[frame]", "-frames:v", str(n)] + ff.enc() + [str(path)])
            elif view == "true":
                last_wanted = f1 if step == 1 else stepped_frames(f0, f1, step)[-1]
                if not true16_dir.exists() or not (true16_dir / f"frame_{last_wanted:04d}.png").exists():
                    ok = False
                    break
                src16 = fill_dir(out, true16_dir, f0, f1, step)
                ff.run(["-framerate", str(FPS), "-start_number", str(f0), "-i", str(src16 / "frame_%04d.png"),
                        "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-frames:v", str(n)] + ff.enc() + [str(path)])
            elif view == "all":
                if min(n_third, n_first, n_true) < f1:
                    ok = False
                    break
                ff.run(piece_inputs(f0) + ["-filter_complex", piece_graph, "-map", "[frame]", "-frames:v", str(n)] + ff.enc() + [str(path)])
            segs.append(path)
        if ok:
            lst = out / "logs" / f"showcase_list{T}.txt"
            lst.write_text("\n".join(f"file '{cfile(p)}'" for p in segs) + "\n", encoding="utf-8", newline="\n")
            ff.run(["-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(out / f"showcase{T}.mp4")], quiet=True)
            shutil.copy(out / f"showcase{T}.mp4", out / f"showcase_true{T}.mp4")
            if a.audio and pathlib.Path(a.audio).exists():
                # the stand-in soundtrack under the showcase (rung 2p): from the cut's first second, in the render's seconds
                offset = float(cut["showcase"][0]["t0"]) / float(beats.get("pace", 1.0))
                ff.run(["-i", str(out / f"showcase{T}.mp4"), "-ss", f"{offset:.3f}", "-i", str(a.audio), "-map", "0:v", "-map", "1:a",
                        "-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", str(out / f"showcase{T}_sound.mp4")], quiet=True)
                print(f"showcase{T}_sound.mp4: the stand-in soundtrack from {offset:.2f} s", flush=True)
            if step > 1:
                # the fast cut: one of each held run of frames, played at the pace asked for
                rate = fast_cut(ff, out / f"showcase{T}.mp4", out / f"showcase{T}_fast.mp4", step, a.speed)
                shutil.copy(out / f"showcase{T}_fast.mp4", out / f"showcase_true{T}_fast.mp4")
                print(f"showcase{T}_fast.mp4: every {step}th frame at {rate:.2f} a second, {a.speed:g} times real time", flush=True)
        else:
            print("showcase: a segment's frames are missing, skipped", flush=True)
        # the showcase's whole span from the other two cameras, each alone: the three views of one scene
        # as a regression test (his seventh review of 2026-11-10), and the three together
        span0, span1 = int(round(cut["showcase"][0]["t0"] * CFPS)) + 1, int(round(cut["showcase"][-1]["t1"] * CFPS))
        n_span = span1 - span0 + 1
        view_fast = {}
        for view, folder in (("third", third_dir), ("first", first_dir)):
            last_wanted = span1 if step == 1 else stepped_frames(span0, span1, step)[-1]
            if not folder.exists() or not (folder / f"frame_{last_wanted:04d}.png").exists():
                print(f"showcase_{view}: frames missing, skipped", flush=True)
                continue
            src = fill_dir(out, folder, span0, span1, step)
            clip = out / f"showcase_{view}{T}.mp4"
            if view == "third":
                ff.run(["-framerate", str(FPS), "-start_number", str(span0), "-i", str(src / "frame_%04d.png"),
                        "-vf", "scale=1920:1080:flags=lanczos,format=yuv420p", "-frames:v", str(n_span)] + ff.enc() + [str(clip)])
            else:
                inputs = ["-framerate", str(FPS), "-start_number", str(span0), "-i", str(src / "frame_%04d.png"),
                          "-framerate", str(FPS), "-start_number", str(span0), "-i", str(ov / "piece" / "tint_%04d.png"),
                          "-framerate", str(FPS), "-start_number", str(span0), "-i", str(ov / "piece" / "lid_%04d.png"),
                          "-loop", "1", "-framerate", str(FPS), "-i", str(masks[(960, 540)])]
                graph = eye_chain("0:v", "1:v", "2:v", "3:v", (960, 540), "sv") + ";[sv]scale=1920:1080:flags=lanczos,format=yuv420p[frame]"
                ff.run(inputs + ["-filter_complex", graph, "-map", "[frame]", "-frames:v", str(n_span)] + ff.enc() + [str(clip)])
            if step > 1:
                view_fast[view] = out / f"showcase_{view}{T}_fast.mp4"
                fast_cut(ff, clip, view_fast[view], step, a.speed)
        if ok and len(view_fast) == 2 and (out / f"showcase{T}_fast.mp4").exists():
            rate = FPS / step * a.speed
            ff.run(["-i", str(view_fast["third"]), "-i", str(view_fast["first"]), "-i", str(out / f"showcase{T}_fast.mp4"),
                    "-filter_complex", "[0:v]scale=960:540[a];[1:v]scale=960:540[b];[a][b]hstack=inputs=2:shortest=1[top];"
                    "[2:v]scale=1920:1080[c];[top][c]vstack=inputs=2:shortest=1,format=yuv420p[v]",
                    "-map", "[v]"] + ff.enc() + ["-r", f"{rate:.4f}", str(out / f"triview{T}_fast.mp4")], quiet=True)
            print(f"triview{T}_fast.mp4: Third and First over True, the fast cut", flush=True)

    # ---- sheets ----
    if a.only in ("all", "sheets") and n_third and n_first and n_true:
        sel_frames = [int(round((b["start"] + 1.0) * CFPS)) + 1 for b in beats["beats"]]
        sel = "+".join(f"eq(n\\,{f - 1})" for f in sel_frames)
        labels = []
        for b, f in zip(beats["beats"], sel_frames):
            title = f"{b['name']}   {b['start']} to {b['end']} s"
            labels.append(f"drawtext=fontfile={bold}:fontsize=40:fontcolor=white@0.9:x=24:y=16:text='{esc(title)}':enable='eq(n\\,{f - 1})'")
        rows = (len(sel_frames) + 1) // 2
        sheet_graph = piece_graph.replace("[frame]", "[full];[full]" + ",".join(labels) + f",select='{sel}',scale=960:540,tile=2x{rows}[frame]")
        ff.run(piece_inputs(1) + ["-filter_complex", sheet_graph, "-map", "[frame]", "-frames:v", "1", str(out / "contact_sheet.png")], quiet=True)
        strips = []
        for name in cut["moves"]:
            if name not in move_clips:
                continue
            clip, n = move_clips[name]
            picks = [int(round(i * (n - 1) / 7.0)) for i in range(8)]
            s = "+".join(f"eq(n\\,{p})" for p in picks)
            strip = out / "logs" / f"strip_{name}.png"
            ff.run(["-i", str(clip), "-vf", f"select='{s}',scale=480:270,tile=8x1", "-frames:v", "1", str(strip)], quiet=True)
            strips.append(strip)
        if strips:
            inputs = []
            for s in strips:
                inputs += ["-i", str(s)]
            graph = "".join(f"[{i}:v]" for i in range(len(strips))) + f"vstack=inputs={len(strips)}[v]" if len(strips) > 1 else "[0:v]copy[v]"
            ff.run(inputs + ["-filter_complex", graph, "-map", "[v]", "-frames:v", "1", str(out / "moves_sheet.png")], quiet=True)
    print("ASSEMBLED", out, flush=True)


if __name__ == "__main__":
    main()

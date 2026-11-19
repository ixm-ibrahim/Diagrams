"""Assemble rung 1's review from the rendered sequences with FFmpeg.

    python tools/assemble.py [--out renders/rung1] [--fps 24]

Writes into the output folder:
  review.mp4              1920 by 1080: the Third-Person proxy top left, the beat and what the
                          view should show top right, the True-Person view across the bottom
  true_person.mp4         the True-Person view alone, 1920 by 648
  contact_sheet.png       one review frame per beat, two columns
  contact_sheet_true.png  the True-Person frame alone per beat, two columns
The beat texts come from data/beats.json. FFmpeg by absolute path (not on PATH everywhere).
Paths inside filter graphs are given relative to the project folder, because FFmpeg's
filter parser reads a drive letter's colon as an option separator whatever the escaping.
"""
import argparse
import json
import os
import pathlib
import shutil
import subprocess
import sys
import textwrap

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from compose import find_ffmpeg  # noqa: E402

FONTS = {"regular": r"C:\Windows\Fonts\arial.ttf", "bold": r"C:\Windows\Fonts\arialbd.ttf"}


def rel(path):
    return os.path.relpath(str(path), str(ROOT)).replace("\\", "/")


def esc(text):
    """Escape a drawtext string: backslashes, colons, commas, quotes, percent signs."""
    return (text.replace("\\", "\\\\").replace(":", "\\:").replace(",", "\\,")
            .replace("'", "\u2019").replace("%", "%%"))


def beat_filters(beats, textdir):
    """drawtext filters for the info panel: beat name, seconds, and what the view should show."""
    for key, src in FONTS.items():
        dst = textdir / f"font_{key}.ttf"
        if not dst.exists():
            shutil.copy(src, dst)
    font = rel(textdir / "font_regular.ttf")
    bold = rel(textdir / "font_bold.ttf")
    parts = []
    for b in beats["beats"]:
        t0, t1 = b["start"], b["end"]
        enable = f"between(t\\,{t0}\\,{t1 - 0.0001})"
        title = f"{b['name']}   {t0} to {t1} s"
        parts.append(f"drawtext=fontfile={bold}:fontsize=30:fontcolor=white:x=24:y=20:text='{esc(title)}':enable='{enable}'")
        lines = textwrap.wrap(b["shows"], 58)[:9]
        tf = textdir / f"beat_{b['id']}.txt"
        tf.write_text("\n".join(lines), encoding="utf-8", newline="\n")  # drawtext draws a CR as a blank line
        parts.append(f"drawtext=fontfile={font}:fontsize=22:fontcolor=0xd8d8d8:x=24:y=64:line_spacing=6:"
                     f"textfile={rel(tf)}:enable='{enable}'")
    parts.append(f"drawtext=fontfile={font}:fontsize=22:fontcolor=0x9a9a9a:x=24:y=392:"
                 f"text='frame %{{frame_num}}   %{{pts\\:hms}}':start_number=1")
    parts.append(f"drawtext=fontfile={font}:fontsize=20:fontcolor=0x9a9a9a:x=700:y=392:text='timing\\: guess'")
    return ",".join(parts)


def run(cmd):
    print(" ".join(str(c) for c in cmd[:6]), "...", flush=True)
    subprocess.run(cmd, check=True, cwd=str(ROOT))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung1"))
    ap.add_argument("--true", default=None, help="folder of True-Person frames, default <out>/true")
    ap.add_argument("--third", default=None, help="folder of Third-Person frames, default <out>/third")
    ap.add_argument("--fps", type=int, default=24)
    ap.add_argument("--beats", default=str(ROOT / "data" / "beats.json"))
    ap.add_argument("--crf", type=int, default=18)
    ap.add_argument("--no-video", action="store_true")
    ap.add_argument("--no-sheets", action="store_true")
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    true_dir = pathlib.Path(a.true).resolve() if a.true else out / "true"
    third_dir = pathlib.Path(a.third).resolve() if a.third else out / "third"
    beats = json.loads(pathlib.Path(a.beats).read_text(encoding="utf-8"))
    ff = find_ffmpeg()
    textdir = out / "logs"
    textdir.mkdir(parents=True, exist_ok=True)
    n_true = len(list(true_dir.glob("frame_*.png")))
    n_third = len(list(third_dir.glob("frame_*.png")))
    print(f"frames: true {n_true}, third {n_third}", flush=True)
    info = beat_filters(beats, textdir)
    # the text panel is a colour source, which never ends on its own: it is given the sequence's length
    duration = max(1, min(n_true, n_third)) / a.fps
    graph = (f"[1:v]scale=960:432:flags=lanczos,format=rgb24[p];"
             f"color=c=0x101010:s=960x432:r={a.fps}:d={duration:.3f}[bg];[bg]{info}[info];"
             f"[p][info]hstack=inputs=2[top];[0:v]format=rgb24[t];[top][t]vstack=inputs=2,format=yuv420p[frame]")
    inputs = ["-framerate", str(a.fps), "-start_number", "1", "-i", str(true_dir / "frame_%04d.png"),
              "-framerate", str(a.fps), "-start_number", "1", "-i", str(third_dir / "frame_%04d.png")]
    if not a.no_video:
        run([ff, "-y", "-hide_banner", "-loglevel", "error", "-stats"] + inputs +
            ["-filter_complex", graph, "-map", "[frame]", "-shortest",
             "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-r", str(a.fps), "-movflags", "+faststart",
             str(out / "review.mp4")])
        run([ff, "-y", "-hide_banner", "-loglevel", "error", "-stats"] + inputs[:6] +
            ["-vf", "format=yuv420p", "-c:v", "libx264", "-preset", "medium", "-crf", str(a.crf), "-r", str(a.fps),
             "-movflags", "+faststart", str(out / "true_person.mp4")])
    if not a.no_sheets:
        # one frame per beat, a second into each beat, where its first things have arrived
        frames = [int(round((b["start"] + 1.0) * a.fps)) + 1 for b in beats["beats"]]
        sel = "+".join(f"eq(n\\,{f - 1})" for f in frames)
        rows = (len(frames) + 1) // 2
        sheet_graph = graph.replace("[frame]", f"[full];[full]select='{sel}',scale=960:540,tile=2x{rows}[frame]")
        run([ff, "-y", "-hide_banner", "-loglevel", "error"] + inputs +
            ["-filter_complex", sheet_graph, "-map", "[frame]", "-frames:v", "1", str(out / "contact_sheet.png")])
        run([ff, "-y", "-hide_banner", "-loglevel", "error"] + inputs[:6] +
            ["-vf", f"select='{sel}',scale=960:324,tile=2x{rows}", "-frames:v", "1", str(out / "contact_sheet_true.png")])
    print("ASSEMBLED", out, flush=True)


if __name__ == "__main__":
    main()

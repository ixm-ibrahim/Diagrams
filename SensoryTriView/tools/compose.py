"""Lay the three rendered panels into the tri-view frame with FFmpeg.

    python tools/compose.py renders/rung0

reads third.png, first.png and true.png from the folder and writes frame.png
(3840 by 2160: the two top panels side by side, the True-Person panel below) and a
half-size frame_preview.png. FFmpeg is called by absolute path because it is not on
PATH in every terminal on this laptop; override with --ffmpeg or TRIVIEW_FFMPEG.
"""
import argparse
import os
import pathlib
import subprocess
import sys

DEFAULT_FFMPEG = (r"C:\Users\IbrahimMahmoud\AppData\Local\Microsoft\WinGet\Packages"
                  r"\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.2-full_build\bin\ffmpeg.exe")

FILTER = ("[0:v]format=rgb24[a];[1:v]format=rgb24[b];[2:v]format=rgb24[c];"
          "[a][b]hstack=inputs=2[top];[top][c]vstack=inputs=2[frame]")


def find_ffmpeg(explicit=None):
    for c in (explicit, os.environ.get("TRIVIEW_FFMPEG"), DEFAULT_FFMPEG):
        if c and os.path.isfile(c):
            return c
    return "ffmpeg"


def compose(third, first, true, out, ffmpeg=None, preview=None, preview_scale=0.5):
    ffmpeg = ffmpeg or find_ffmpeg()
    cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error",
           "-i", str(third), "-i", str(first), "-i", str(true),
           "-filter_complex", FILTER, "-map", "[frame]", "-frames:v", "1", str(out)]
    subprocess.run(cmd, check=True)
    if preview:
        cmd = [ffmpeg, "-y", "-hide_banner", "-loglevel", "error", "-i", str(out),
               "-vf", f"scale=iw*{preview_scale}:ih*{preview_scale}:flags=lanczos", "-frames:v", "1", str(preview)]
        subprocess.run(cmd, check=True)
    return out


def main():
    ap = argparse.ArgumentParser(description="compose the tri-view frame")
    ap.add_argument("folder", help="folder holding third.png, first.png and true.png")
    ap.add_argument("--out", default=None, help="output frame, default <folder>/frame.png")
    ap.add_argument("--preview", default=None, help="half-size preview, default <folder>/frame_preview.png")
    ap.add_argument("--no-preview", action="store_true")
    ap.add_argument("--ffmpeg", default=None)
    a = ap.parse_args()
    folder = pathlib.Path(a.folder)
    out = pathlib.Path(a.out) if a.out else folder / "frame.png"
    preview = None if a.no_preview else (pathlib.Path(a.preview) if a.preview else folder / "frame_preview.png")
    for name in ("third.png", "first.png", "true.png"):
        if not (folder / name).is_file():
            sys.exit(f"missing {folder / name}")
    compose(folder / "third.png", folder / "first.png", folder / "true.png", out, find_ffmpeg(a.ffmpeg), preview)
    print("composed", out, "preview", preview or "none")


if __name__ == "__main__":
    main()

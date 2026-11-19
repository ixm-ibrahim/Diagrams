"""First-Person stills as the assembly shows the view (rung 2p).

The eyes' render of a frame carries no sense of its own. What the First-Person view shows of the senses is laid on by
the assembly from the eye table's row for the frame (renders/<out>/eye_frames.json): the lids, the tint of the sense
that holds attention at the frame's edge, and the red flash toward a pain. tools/assemble_rung2.py does that for the
videos; this does the same for single frames, with that tool's own lid and tint pictures and the same order (the lid
over the render, then the tint times the vignette mask, screened on), so a still can be reviewed without a video.

Two pictures can stand under them (field, his fourteenth round of 2026-11-14):
  eyes    the eyes' whole field, the default: the eyes' own scan (renders/<out>/scan, a fisheye of 200 degrees on the eyes,
          the very picture the mind's model is built from), kept to the ellipse the model keeps of it (engine.FIELD_H across,
          FIELD_V high), the ellipse's height the panel's. What the simulated mannequin sees in the True-Person view and
          what the First-Person view shows are then one picture. The lids close over the ellipse's height, as the
          model's do; the tint lies along the ellipse's edge; the sun's glow through the lids and the pain's flash are
          placed by their directions in the eyes' own frame (the table's sun_dir, pain_dir).
  camera  the camera on the eyes (renders/<out>/first: a 20 mm lens, 84 degrees across and 54 high), as it was until then:
          the middle of that field only, so the model's seen picture held things this frame did not.

python tools/first_still.py --out renders/rung2p --frames 946,976 --to first_r8 [--field camera]
"""
import argparse
import json
import math
import pathlib
import sys

import numpy as np
from PIL import Image

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import assemble_rung2 as asm  # noqa: E402

PANEL = (960, 540)
SCAN_FOV = 200.0               # the scan's field across its square picture (triview/lidarscene.py FOV_DEG)
FIELD_H, FIELD_V = 200.0, 130.0   # the field of both eyes kept from it (triview/engine.py FIELD_H, FIELD_V)
FIELD_EDGE = 0.03              # the share of the ellipse's radius over which the picture falls to black at the field's edge


def load_spec(out, tint_gain=None, field="eyes"):
    """What a frame's lids and tint are worked out from: the eye table's rows and data/eyes.json's settings."""
    eyes_spec = json.loads((ROOT / "data" / "eyes.json").read_text(encoding="utf-8"))
    rows = {r["f"]: r for r in json.loads((pathlib.Path(out) / "eye_frames.json").read_text(encoding="utf-8"))["rows"]}
    return {"rows": rows, "tint_gain": tint_gain if tint_gain is not None else float(eyes_spec["tint"]["strength"]),
            "feather": float(eyes_spec["tint"].get("feather", 0.32)),
            "upper_share": float(eyes_spec.get("lids", {}).get("upper_share", 0.75)), "masks": {}, "field": field}


def _ellipse(W, H):
    """The field's ellipse in a W by H panel: its half width and half height in pixels (its height the panel's), and
    each pixel's radius in it (0 at the centre, 1 at the edge)."""
    b = H / 2.0
    a = b * FIELD_H / FIELD_V
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float32)
    r = np.sqrt(((xx + 0.5 - W / 2.0) / a) ** 2 + ((yy + 0.5 - H / 2.0) / b) ** 2)
    return a, b, r


def field_uv(direction, W, H):
    """Where a direction in the eyes' own frame (forward, left, up) falls in the panel, 0 to 1 across and down: the
    scan's own mapping (the angle from straight ahead over the scan's field, along the azimuth) laid in the panel as
    the ellipse lies. None where there is no direction."""
    if direction is None:
        return None
    x, y, z = (float(v) for v in direction)
    n = math.sqrt(x * x + y * y + z * z)
    if n < 1e-9:
        return None
    theta = math.acos(max(-1.0, min(1.0, x / n)))
    phi = math.atan2(z, -y)                          # up over right
    rr = math.degrees(theta) / SCAN_FOV              # 0.5 at the scan's rim
    span =(H / 2.0) * FIELD_H / FIELD_V * 2.0 * (SCAN_FOV / FIELD_H)   # the scan's full width in panel pixels
    return 0.5 + rr * math.cos(phi) * span / W, 0.5 - rr * math.sin(phi) * span / H


def eyes_picture(out, f, size=PANEL):
    """The eyes' whole field for frame f: the scan's ellipse, its height the panel's, black beyond the field's edge.
    None where the scan is missing."""
    src = pathlib.Path(out) / "scan" / f"frame_{f:04d}.png"
    if not src.exists():
        return None
    W, H = size
    scan = Image.open(src).convert("RGB")
    S = scan.size[0]
    span = int(round((H / 2.0) * FIELD_H / FIELD_V * 2.0 * (SCAN_FOV / FIELD_H)))     # the scan's width in panel pixels
    small = scan.resize((span, span), Image.LANCZOS)
    canvas = Image.new("RGB", (W, H), (0, 0, 0))
    canvas.paste(small, ((W - span) // 2, (H - span) // 2))
    pic = np.asarray(canvas, dtype=np.float32) / 255.0
    _, _, r = _ellipse(W, H)
    u = np.clip((1.0 - r) / FIELD_EDGE, 0.0, 1.0)
    return pic * (u * u * (3.0 - 2.0 * u))[..., None]


def _field_mask(W, H, feather):
    """The tint's mask for the eyes' field: 0 inside, rising smoothly to 1 at the ellipse's edge over the outer feather
    share of its radius, and 1 beyond it."""
    _, _, r = _ellipse(W, H)
    u = np.clip((r - (1.0 - feather)) / feather, 0.0, 1.0)
    return (u * u * (3.0 - 2.0 * u))[..., None]


def compose_frame(out, f, spec, scratch):
    """The First-Person frame f as the assembly shows it: the picture under the lids, then the tint and the pain's
    flash through the vignette mask, screened on. Returns the picture (H, W, 3, 0 to 1) and its row, or (None, None)
    where the picture or the row is missing. scratch: a folder for the lid and tint pictures on their way."""
    out, scratch = pathlib.Path(out), pathlib.Path(scratch)
    r = spec["rows"].get(f)
    if r is None:
        return None, None
    whole = spec.get("field", "eyes") == "eyes"
    if whole:
        base = eyes_picture(out, f)
        if base is None:
            return None, None
        H, W = base.shape[:2]
        src = scratch / f"eyes_{f:04d}.png"
        Image.fromarray((base * 255.0 + 0.5).astype(np.uint8), "RGB").save(src)
        sun_uv = field_uv(r.get("sun_dir"), W, H)
        pain = r.get("pain")
        if pain and r.get("pain_dir") is not None:
            pu, pv = field_uv(r["pain_dir"], W, H)
            pain = [pain[0], pu, pv]
    else:
        src = out / "first" / f"frame_{f:04d}.png"
        if not src.exists():
            return None, None
        base = np.asarray(Image.open(src).convert("RGB"), dtype=np.float32) / 255.0
        H, W = base.shape[:2]
        sun_uv, pain = r.get("sun_uv"), r.get("pain")
    # the lids over the picture
    cover = asm.row_cover(r)
    if cover > 0.0:
        lid_path = scratch / f"lid_{f:04d}.png"
        asm.lid_image(lid_path, cover, r.get("lid", [0, 0, 0]), spec["upper_share"], src, sun_uv, float(r.get("face_sun", 0.0)), size=(W, H))
        lid = np.asarray(Image.open(lid_path).convert("RGBA").resize((W, H), Image.BILINEAR), dtype=np.float32) / 255.0
        base = base * (1.0 - lid[..., 3:4]) + lid[..., :3] * lid[..., 3:4]
        lid_path.unlink()
    # the tint and the pain's flash, through the vignette mask, screened on
    alpha = float(r.get("tint_a", 0.0)) * spec["tint_gain"]
    tint = [float(c) * alpha for c in r.get("tint", [0, 0, 0])]
    if pain and float(pain[0]) > 1e-3:
        tint_path = scratch / f"tint_{f:04d}.png"
        asm.tint_image(tint_path, tint, pain, size=(W, H))
        layer = np.asarray(Image.open(tint_path).convert("RGB"), dtype=np.float32) / 255.0
        tint_path.unlink()
    else:
        layer = np.zeros_like(base) + np.clip(np.array(tint, dtype=np.float32), 0.0, 1.0)[None, None, :]
    masks = spec["masks"]
    key = (W, H, whole)
    if key not in masks:
        if whole:
            masks[key] = _field_mask(W, H, spec["feather"])
        else:
            mask_path = scratch / f"mask_{W}x{H}.png"
            if not mask_path.exists():
                asm.vignette_mask(mask_path, W, H, spec["feather"])
            masks[key] = np.asarray(Image.open(mask_path).convert("L"), dtype=np.float32)[..., None] / 255.0
    shown = 1.0 - (1.0 - base) * (1.0 - layer * masks[key])
    if whole:
        # nothing shows beyond the field's edge: the lids and the tint lie on the eyes' picture, not on the panel
        _, _, rad = _ellipse(W, H)
        u = np.clip((1.0 - rad) / FIELD_EDGE, 0.0, 1.0)
        shown = shown * (u * u * (3.0 - 2.0 * u))[..., None]
        src.unlink()
    return np.clip(shown, 0.0, 1.0), r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2p"))
    ap.add_argument("--frames", required=True, help="a,b,c")
    ap.add_argument("--to", default="first_still", help="the folder under --out the stills go to")
    ap.add_argument("--tint-gain", type=float, default=None, help="override data/eyes.json's tint strength")
    ap.add_argument("--field", default="eyes", choices=("eyes", "camera"), help="the eyes' whole field (their scan's ellipse), or the camera on the eyes")
    a = ap.parse_args()
    out = pathlib.Path(a.out).resolve()
    dst = out / a.to
    dst.mkdir(parents=True, exist_ok=True)
    spec = load_spec(out, a.tint_gain, a.field)
    for f in [int(v) for v in a.frames.split(",") if v.strip()]:
        shown, r = compose_frame(out, f, spec, dst)
        if shown is None:
            print(f"frame {f}: no First-Person picture, or no row in the eye table")
            continue
        Image.fromarray((shown * 255.0 + 0.5).astype(np.uint8), "RGB").save(dst / f"frame_{f:04d}.png")
        pain = r.get("pain")
        print(f"frame {f}: sense {r.get('sense')}, flash {None if not pain else [round(float(v), 2) for v in pain]}, lids {asm.row_cover(r):.2f}")


if __name__ == "__main__":
    main()

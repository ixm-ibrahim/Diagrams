"""The audit of every touch through the piece (rung 2p, his thirteenth round of 2026-11-13: run through the whole
timeline and verify the sparks occur at the right times).

    python tools/touch_audit.py [--out renders/rung2p] [--senses data/senses.json]
    python tools/touch_audit.py --pair hand_r Table --from 27.8 --to 28.8

Reads the gaps LidarScene.read_pairs measured and kept (contact_pairs.npz: every body part against every thing of the
room and every other body part not joined to it at one joint, at every frame) and works out the touches that begin
by the same rule the build uses (triview/touches.py). No Blender needed.

Without --pair: every touch that begins, for every touch or pain the timeline names the beginning nearest it, and
every spark the last build drew with its light (sparks.json). With --pair: that pair's gap frame by frame over the span, in
millimetres, which is how a rule's choice of a moment is checked against the picture."""
import argparse
import importlib.util
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[1]


def load_touches():
    spec = importlib.util.spec_from_file_location("touches", ROOT / "triview" / "touches.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2p"))
    ap.add_argument("--senses", default=str(ROOT / "data" / "senses.json"))
    ap.add_argument("--pair", nargs=2, default=None, metavar=("PART", "OTHER"), help="a body part and a thing, or part:<name>")
    ap.add_argument("--from", dest="t0", type=float, default=0.0)
    ap.add_argument("--to", dest="t1", type=float, default=1e9)
    a = ap.parse_args()
    touches = load_touches()
    z = np.load(pathlib.Path(a.out) / "contact_pairs.npz", allow_pickle=False)
    series = touches.unpack(z)
    times = [float(t) for t in z["times"]]
    if a.pair:
        ser = series.get(tuple(a.pair))
        if ser is None:
            near = sorted(o for p, o in series if p == a.pair[0])
            raise SystemExit(f"{a.pair[0]} never came within {touches.PAIR_REACH} m of {a.pair[1]}; it did of: {', '.join(near)}")
        print(f"{a.pair[0]} and {a.pair[1]}: the gap in millimetres, frame by frame ('.' beyond {touches.PAIR_REACH * 1000:.0f} mm)")
        for k, t in enumerate(times):
            if a.t0 - 1e-6 <= t <= a.t1 + 1e-6:
                d = ser.get(k)
                print(f"  {t:7.2f} s  frame {k + 1:4d}  " + ("." if d is None else f"{d * 1000:5.1f}  " + "#" * int(round(d * 1000))))
        return
    begins, shares = touches.begins_of_pairs(series, times)
    print(f"{len(series)} pairs came within {touches.PAIR_REACH} m; {len(begins)} touches begin (a touch between two body parts is listed from each)")
    for t, part, other, v in begins:
        if a.t0 <= t <= a.t1:
            print(f"  {t:7.2f} s  {part:12s} {other:20s} closing at {v:5.2f} m/s")
    events = json.loads(pathlib.Path(a.senses).read_text(encoding="utf-8"))["events"]
    named = [e for e in events if e.get("kind") == "comet" and e.get("sense") in ("touch", "pain")]
    print(f"\nthe timeline names {len(named)} touches and pains:")
    for e in sorted(named, key=lambda e: e["t"]):
        same = [(abs(t - e["t"]), t, other, v) for t, part, other, v in begins if part == e["part"]]
        best = min(same) if same else None
        where = f"nearest beginning of {e['part']}: {best[1]:.2f} s on {best[2]} ({best[0]:.2f} s away)" if best else "no beginning of that part"
        print(f"  {e['t']:7.2f} s  {e['sense']:5s} {e['part']:8s} strength {e.get('strength', 0.5):.2f} attention {e.get('attention', 0):.2f}   {where}")
    sparks_path = pathlib.Path(a.out) / "sparks.json"
    if sparks_path.exists():
        sparks = json.loads(sparks_path.read_text(encoding="utf-8"))["sparks"]
        print()
        print(f"the build drew {len(sparks)} sparks (sparks.json): second, part, light (1 is the pain's; the least a touch has is 0.06)")
        for sp in sparks:
            if a.t0 <= sp["t"] <= a.t1:
                print(f"  {sp['t']:7.2f} s  {sp['part']:12s} light {sp['light']:.2f}  " + "#" * int(round(sp["light"] * 40)))


if __name__ == "__main__":
    main()

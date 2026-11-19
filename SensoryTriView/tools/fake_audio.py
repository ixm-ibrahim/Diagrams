"""The stand-in soundtrack (rung 2p): every hearing event of data/senses.json synthesized (triview/sound.py) and
laid on one mono track in the render's seconds, written as a WAV beside the renders; a debug stand-in until the
piece has its sound files (rung 6). The same waveforms give the sounds' rings their loudness.

    python tools/fake_audio.py [--out renders/rung2p] [--senses data/senses.json]
"""
import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from triview import sound  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "renders" / "rung2p"))
    ap.add_argument("--senses", default=str(ROOT / "data" / "senses.json"))
    ap.add_argument("--beats", default=str(ROOT / "data" / "beats.json"))
    a = ap.parse_args()
    senses = json.loads(pathlib.Path(a.senses).read_text(encoding="utf-8"))
    beats = json.loads(pathlib.Path(a.beats).read_text(encoding="utf-8"))
    pace = float(beats.get("pace", 1.0))
    duration = float(beats["duration_seconds"])
    out = pathlib.Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    samples = sound.track(senses["events"], duration, pace)
    path = sound.write_wav(out / "fake_audio.wav", samples)
    print("wrote", path, f"{len(samples) / sound.RATE:.1f} s at {sound.RATE} Hz, pace {pace}")
    for ev in senses["events"]:
        if ev.get("kind") == "wave":
            env = sound.envelope(ev)
            print(f"  {ev['id']:12s} {ev['t0']:6.2f} to {ev['t1']:6.2f} s  rings {len(env):3d}  peaks " + " ".join(f"{v:.2f}" for v in env[:12]))


if __name__ == "__main__":
    main()

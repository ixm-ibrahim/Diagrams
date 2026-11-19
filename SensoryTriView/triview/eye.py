"""The First-Person eye's behaviours (concept section 5): the long closures and the blinks,
the eye's own exposure over the dawn, the lit eyelids, and the faint edge tint in the colour
of the sense that holds his attention.

The eye's exposure is a model, not a search: at probe moments the First-Person camera
renders a tiny linear frame at exposure 0, and the brightest tenth of it is the field the
eye adapts to (a bright window pulls the eye down and the room goes dark around it, as it
does when you look out of a window). The exposure the eye wants brings that field to a set
level; the exposure it has follows with a lag, fast when the field brightens (the picture
washes out white before the eye adjusts) and slow when it darkens (dark adaptation). With
the eyes closed the field is what the lids let through, a small fraction of the open field,
so the eye adapts up behind closed lids and the opening eyes are dazzled.

The lids are a wipe, never a cut (his review of 2026-11-07): a blink closes over two frames,
is shut for two and opens over three; a closure closes over three frames and opens over six,
the first waking over ten. Every frame carries a cover, 0 open to 1 shut, and the assembly
tool draws the lids from it, the upper lid taking most of the frame and the lower the rest,
in a warm colour while the eyes are closed in light. The per-frame table (renders/rung2/
eye_frames.json) is what the assembly draws from, so the lids can be tuned without a render.
Nothing here touches Blender.
"""
import json
import math
import random

from . import anim, tags

DEFAULT_LIDS = {"close_frames": 3, "open_frames": 6, "first_open_frames": 10,
                "blink_profile": [0.5, 1.0, 1.0, 0.65, 0.35, 0.12], "upper_share": 0.75}


def load(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def tonemap(x):
    """A filmic-ish curve for a flat colour field: scene linear to display 0..1."""
    x = max(0.0, x)
    v = x / (1.0 + x)
    return v ** (1.0 / 2.2)


class Eyes:
    """Closures from the chain and blinks from a seeded rhythm, each as a lid cover over time."""

    def __init__(self, spec, duration, forced_blinks=(), fps=24):
        self.fps = fps
        self.closures = [(float(a), float(b)) for a, b in spec["closures"]]
        lids = dict(DEFAULT_LIDS)
        lids.update(spec.get("lids", {}))
        self.lids = lids
        self.profile = [float(v) for v in lids["blink_profile"]]
        bl = spec["blink"]
        self.blink_frames = len(self.profile)
        self.blinks = self._schedule(bl, duration, forced_blinks)

    def closed(self, t):
        """Inside a long closure (the lids fully shut, the eye adapting to what they let through)."""
        return any(a <= t < b for a, b in self.closures)

    def _schedule(self, bl, duration, forced):
        rng = random.Random(int(bl.get("seed", 1)))
        gap_lo, gap_hi = float(bl["min_gap"]), float(bl["max_gap"])
        clear = float(bl.get("clear_of_closure", 0.7))
        length = self.blink_frames / self.fps
        out = [(float(a), float(b)) for a, b in forced]
        t = rng.uniform(gap_lo, gap_hi)
        while t < duration:
            ok = not self.closed(t) and not self.closed(t + length)
            for a, b in self.closures:
                if abs(t - a) < clear or abs(t - b) < clear:
                    ok = False
            for a, b in out:
                if abs(t - a) < 1.0:
                    ok = False
            if ok:
                out.append((t, t + length))
            t += rng.uniform(gap_lo, gap_hi)
        return sorted(out)

    def blinking(self, t):
        return any(a <= t < b for a, b in self.blinks)

    def cover(self, t):
        """How far the lids are shut at t, 0 open to 1 closed: the closures with their ramps, and the blinks."""
        c = 0.0
        fps = self.fps
        for i, (a, b) in enumerate(self.closures):
            close_s = self.lids["close_frames"] / fps
            open_s = (self.lids["first_open_frames"] if i == 0 else self.lids["open_frames"]) / fps
            if a - close_s <= t < a:
                c = max(c, anim.smoothstep((t - (a - close_s)) / close_s))
            elif a <= t < b:
                c = 1.0
            elif b <= t < b + open_s:
                c = max(c, 1.0 - anim.smoothstep((t - b) / open_s))
        for a, b in self.blinks:
            if a <= t < b:
                k = int((t - a) * fps)
                if 0 <= k < len(self.profile):
                    c = max(c, self.profile[k])
        return min(1.0, c)

    def dark(self, t):
        return self.cover(t) >= 0.999


def interp_probes(probes, t):
    """Linear interpolation in log space between (t, value) probes."""
    if not probes:
        return 1e-3
    if t <= probes[0][0]:
        return probes[0][1]
    for (t0, v0), (t1, v1) in zip(probes, probes[1:]):
        if t0 <= t < t1:
            u = (t - t0) / (t1 - t0)
            return math.exp(anim.lerp(math.log(max(v0, 1e-6)), math.log(max(v1, 1e-6)), u))
    return probes[-1][1]


def adapt(fields, fps, target, lo, hi, tau_brighter, tau_darker):
    """The exposure the eye has, per frame, following the exposure it wants.

    fields: per frame the linear field value at exposure 0. Returns a list of exposures.
    """
    dt = 1.0 / fps
    out = []
    e = None
    for field in fields:
        want = max(lo, min(hi, math.log2(target / max(field, 1e-6))))
        if e is None:
            e = want
        else:
            tau = tau_brighter if want < e else tau_darker
            e += (want - e) * (1.0 - math.exp(-dt / tau))
        out.append(e)
    return out


def leader_tint(fs):
    """The colour and strength of the sense that holds his attention in a FrameState."""
    sense, att = getattr(fs, "attention_leader", ("none", 0.0))
    col = tags.SENSE_COLOUR.get(sense)
    if col is None or att <= 1e-3:
        return (0.0, 0.0, 0.0), 0.0, sense
    return tuple(col), min(1.0, att), sense


def build_table(frames, fps, times, eyes, probes_first, probes_third, states_by_frame, face_sun, spec, sun_uv=None, pain=None,
                sun_dir=None, pain_dir=None):
    """The per-frame eye table.

    times: {frame: t}; face_sun: {frame: 0..1 how much the face is toward the sun above the
    ridge}; probes_first: [(t, bright, key, mean)]; probes_third: [(t, mean)]; sun_uv: {frame: (u, v)}
    where the sun stands in the First-Person picture, for the light through the closed lids; pain:
    {frame: [level, u, v]}, the First-Person flash toward a pain (rung 2p) and where the pain lies.
    """
    sun_uv = sun_uv or {}
    pain = pain or {}
    # the sun and a pain as directions in the eyes' own frame (forward, left, up), for a First-Person picture that is
    # the eyes' whole field and not a camera's frame (tools/first_still.py, 2026-11-14)
    sun_dir = sun_dir or {}
    pain_dir = pain_dir or {}
    ef, et = spec["exposure_first"], spec["exposure_third"]
    lid_k = float(ef.get("lid_transmission", 0.08))
    lid_col = spec.get("lid_colour", [0.55, 0.10, 0.03])
    bright_open = {f: interp_probes([(p[0], p[1]) for p in probes_first], times[f]) for f in frames}
    fields = []
    for f in frames:
        t = times[f]
        b = bright_open[f]
        fields.append(lid_k * b if eyes.closed(t) else b)
    e_first = adapt(fields, fps, float(ef["target"]), float(ef["lo"]), float(ef["hi"]),
                    float(ef["tau_brighter"]), float(ef["tau_darker"]))
    means = [interp_probes([(p[0], p[1]) for p in probes_third], times[f]) for f in frames]
    e_third = adapt(means, fps, float(et["target_mean"]), float(et["lo"]), float(et["hi"]), float(et["tau"]), float(et["tau"]))
    rows = []
    for i, f in enumerate(frames):
        t = times[f]
        closed = eyes.closed(t)
        blink = eyes.blinking(t)
        cover = eyes.cover(t)
        fs = states_by_frame.get(f)
        tint_col, tint_a, sense = leader_tint(fs) if fs is not None else ((0, 0, 0), 0.0, "none")
        lid = [0.0, 0.0, 0.0]
        if cover > 1e-3:
            # what the lids let through, seen by the eye at its current exposure
            field = lid_k * bright_open[f] * (2.0 ** e_first[i])
            peak = max(lid_col)
            lid = [tonemap(field * c / peak) for c in lid_col]
        rows.append({
            "f": f, "t": round(t, 4), "closed": int(closed), "blink": int(blink), "cover": round(cover, 3),
            "exp_first": round(e_first[i], 3), "exp_third": round(e_third[i], 3),
            "lid": [round(v, 4) for v in lid], "tint": [round(c, 3) for c in tint_col], "tint_a": round(tint_a, 3),
            "sense": sense, "bright": round(bright_open[f], 5), "mean_third": round(means[i], 5),
            "face_sun": round(face_sun.get(f, 0.0), 3), "sun_uv": sun_uv.get(f), "pain": pain.get(f),
            "sun_dir": sun_dir.get(f), "pain_dir": pain_dir.get(f),
        })
    return rows

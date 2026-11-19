"""The touches that begin, from the gaps between the body's parts and everything else (rung 2p, his thirteenth round of
2026-11-13: run through the whole timeline, a collision test between the limbs that are not joined at one joint, and
render what touches).

No Blender here: LidarScene.read_pairs measures the gaps inside Blender and keeps them, and this module says what
they mean, so tools/touch_audit.py can read the same rule outside it.

A pair is a body part and a thing of the room, or a body part and another body part ("part:<name>"). Its gap at a
frame is the least distance from the part's skin to the other's surface, known where it is under PAIR_REACH."""
import numpy as np

PAIR_REACH = 0.05          # how far a point of the skin looks for the other's surface, room metres
PAIR_SAMPLE = 0.03         # the body's shapes are cut to edges under this for the test, room metres
PAIR_ON = 0.013            # a pair touches when its gap is this or under (the contact's 0.9 of the touch's glow),
PAIR_OFF = 0.031           # and has parted once its gap has opened to this (the contact's 0.3)


def pack(series, key, times):
    """The gaps as arrays, for numpy's savez."""
    names = sorted(series)
    idx, dist, start = [], [], [0]
    for name in names:
        ks = sorted(series[name])
        idx.extend(ks)
        dist.extend(series[name][k] for k in ks)
        start.append(len(idx))
    return {"key": np.array(key), "pairs": np.array(["|".join(n) for n in names]), "start": np.array(start, np.int64),
            "idx": np.array(idx, np.int32), "dist": np.array(dist, np.float32), "times": np.array(times, np.float64)}


def unpack(z):
    """The gaps back from pack's arrays: {(part, other): {frame index: gap}}."""
    series = {}
    for name, a, b in zip(z["pairs"], z["start"][:-1], z["start"][1:]):
        part, other = str(name).split("|")
        series[(part, other)] = {int(k): float(d) for k, d in zip(z["idx"][a:b], z["dist"][a:b])}
    return series


PAIR_STILL = 0.0005        # the approach has ended at the first frame the gap closes by less than this, room metres,
PAIR_SETTLE = 8            # looked for over this many frames from the frame the gap came under PAIR_ON


def begins_of_pairs(series, times):
    """Every touch that begins: (second, part, other, how fast the gap closed in metres a second), in order, and every
    pair's share of the frames it touches with its least gap. A pair touches from PAIR_ON and has parted at PAIR_OFF; a
    touch begins each time it comes to touch after it was apart (touching at the first frame, it has not begun).

    Its second is where the approach ends, not where the gap comes under PAIR_ON: a hand that creeps the last
    centimetre onto a table is under PAIR_ON four frames before it lands (the reach, 28.17 s against 28.3 s), and the
    spark belongs to the landing the picture shows. The closing is the fastest of the frames of the approach, and of
    the two frames before the gap came under PAIR_ON taken together, a gap beyond PAIR_REACH counted as PAIR_REACH (so
    1.5 at the most at 30 frames a second)."""
    begins, shares = [], {}
    n = len(times)
    for (part, other), ser in sorted(series.items()):
        gap = [min(ser.get(k, PAIR_REACH), PAIR_REACH) for k in range(n)]
        touching = ser.get(0, 1e9) <= PAIR_ON
        count = 0
        for k in range(n):
            d = ser.get(k, 1e9)
            if not touching and d <= PAIR_ON:
                touching = True
                if k > 0:
                    j = k
                    while j + 1 < n and j - k < PAIR_SETTLE and gap[j + 1] < gap[j] - PAIR_STILL:
                        j += 1
                    dt = max(times[k] - times[k - 1], 1e-6)
                    speed = max([(gap[m - 1] - gap[m]) / dt for m in range(k, j + 1)] + [(gap[max(k - 2, 0)] - gap[k]) / (2.0 * dt), 0.0])
                    begins.append((float(times[j]), part, other, round(float(speed), 4)))
            elif touching and d >= PAIR_OFF:
                touching = False
            count += 1 if touching else 0
        shares[f"{part}|{other}"] = [round(count / n, 4), round(float(min(ser.values())), 4)]
    begins.sort()
    return begins, shares

"""Stand-in sounds (rung 2p, his word of 2026-11-12): until the piece has its sound files (rung 6), every hearing
event of the timeline (data/senses.json) gets a synthesized waveform with peaks and troughs of its own kind: the
alarm's beeps, the slap that silences it, the knuckles' rap and the phone's thud, the rooster's crow of three
seconds, the birds' chirps, the phone's chime of one second. The rings of a sound read this waveform: one ring per
interval of a tenth of a second, as bright as the waveform's peak in that interval (loudness). tools/fake_audio.py
writes the same waveforms as a stand-in soundtrack, so what is heard and what the rings show are one thing.

Nothing here touches Blender. Times are the chain's seconds; a waveform's samples run at RATE a second.
"""
import math

import numpy as np

RATE = 24000


def _env(n, attack, release, hold=None):
    """An amplitude envelope over n samples: a rise over attack seconds, a fall over release at the end, 1 between
    (or an exponential decay with the given hold time constant after the attack)."""
    t = np.arange(n) / RATE
    dur = n / RATE
    e = np.minimum(1.0, t / max(attack, 1e-4))
    if hold is not None:
        e = e * np.exp(-np.maximum(t - attack, 0.0) / hold)
    e = e * np.minimum(1.0, np.maximum(dur - t, 0.0) / max(release, 1e-4))
    return e


def _tone(freq, n, harmonics=(1.0,), glide=None):
    """A tone of n samples at freq hertz (gliding to glide hertz over the samples when given), with the given
    harmonic weights."""
    t = np.arange(n) / RATE
    if glide is None:
        phase = 2.0 * math.pi * freq * t
    else:
        f = freq + (glide - freq) * t / max(t[-1], 1e-6)
        phase = 2.0 * math.pi * np.cumsum(f) / RATE
    out = np.zeros(n)
    for k, w in enumerate(harmonics, 1):
        out += w * np.sin(k * phase)
    return out / max(sum(abs(w) for w in harmonics), 1e-6)


def _noise(n, seed=1):
    rng = np.random.default_rng(seed)
    return rng.uniform(-1.0, 1.0, n)


def _place(track, start, piece):
    """piece added into track from start seconds, clipped to the track."""
    i0 = int(round(start * RATE))
    if i0 >= len(track) or i0 + len(piece) <= 0:
        return
    a = max(i0, 0)
    b = min(i0 + len(piece), len(track))
    track[a:b] += piece[a - i0:b - i0]


def waveform(ev):
    """The stand-in waveform of a hearing event, from its t0 to its t1, peak amplitude its strength."""
    t0, t1 = float(ev["t0"]), float(ev["t1"])
    dur = max(t1 - t0, 0.05)
    n = int(round(dur * RATE))
    s = float(ev.get("strength", 0.6))
    kind = ev["id"]
    rhythm = ev.get("rhythm", "single")
    w = np.zeros(n)
    if rhythm == "pulses":
        # a phone's alarm: a beep per period, on for under half of it, with a flutter in its loudness
        period = 1.0 / float(ev.get("rate_hz", 2.0))
        m = int(round(0.22 * RATE))
        beep = _tone(2093.0, m, harmonics=(1.0, 0.3)) * _env(m, 0.005, 0.02)
        beep *= 1.0 - 0.15 * (0.5 + 0.5 * np.sin(2.0 * math.pi * 25.0 * np.arange(m) / RATE))
        k = 0
        while k * period < dur:
            _place(w, k * period, beep)
            k += 1
    elif rhythm == "swell" or kind == "crow":
        # a rooster's crow over the event: four syllables, the third long with a warble, the last falling
        syll = ((0.0, 0.12, 620.0, 700.0, 0.6), (0.15, 0.28, 700.0, 760.0, 0.75), (0.32, 0.64, 780.0, 820.0, 1.0), (0.67, 1.0, 760.0, 520.0, 0.8))
        for a, b, f0, f1, amp in syll:
            ta, tb = a * dur, b * dur
            m = int(round((tb - ta) * RATE))
            if m <= 0:
                continue
            piece = _tone(f0, m, harmonics=(1.0, 0.6, 0.4, 0.3, 0.2, 0.15), glide=f1) * _env(m, 0.04, 0.1)
            if b - a > 0.25:
                piece *= 1.0 - 0.35 * (0.5 + 0.5 * np.sin(2.0 * math.pi * 6.0 * np.arange(m) / RATE))
            _place(w, ta, piece * amp)
    elif kind.startswith("bird"):
        # a bird: three short chirps rising in pitch
        for k, start in enumerate((0.0, 0.25, 0.5)):
            m = int(round(0.12 * RATE))
            chirp = _tone(3000.0 + 300.0 * k, m, glide=4500.0 + 300.0 * k) * _env(m, 0.01, 0.03)
            _place(w, start * dur / 0.7, chirp * (0.8 + 0.2 * (k % 2)))
    elif kind == "chime":
        # a phone's chime: two notes, each ringing out with a tremolo
        for start, freq in ((0.0, 1046.5), (0.45, 1318.5)):
            m = int(round(min(0.6, dur - start) * RATE))
            if m <= 0:
                continue
            note = _tone(freq, m, harmonics=(1.0, 0.35)) * _env(m, 0.005, 0.03, hold=0.3)
            note *= 1.0 - 0.3 * (0.5 + 0.5 * np.sin(2.0 * math.pi * 6.0 * np.arange(m) / RATE))
            _place(w, start, note)
    elif kind == "smack_sound":
        # the slap on the phone: a burst of noise, gone at once
        m = int(round(min(0.25, dur) * RATE))
        _place(w, 0.0, _noise(m, 2) * _env(m, 0.002, 0.02, hold=0.05))
    elif kind == "rap_sound":
        # the knuckles on the table's edge: two knocks
        for start in (0.0, 0.09):
            m = int(round(0.12 * RATE))
            knock = (0.6 * _noise(m, 3) + 0.4 * _tone(420.0, m)) * _env(m, 0.002, 0.02, hold=0.03)
            _place(w, start, knock)
    elif kind == "phone_thud":
        # the phone on the floor: a low thud
        m = int(round(min(0.35, dur) * RATE))
        _place(w, 0.0, (0.7 * _tone(120.0, m, harmonics=(1.0, 0.5)) + 0.3 * _noise(m, 4)) * _env(m, 0.003, 0.05, hold=0.1))
    else:
        # any other sound: a tone loud at once and dying away
        _place(w, 0.0, _tone(440.0, n) * _env(n, 0.01, 0.05, hold=dur / 3.0))
    peak = float(np.max(np.abs(w))) if n else 0.0
    if peak > 1e-9:
        w = w / peak * s
    return w


_ENVELOPES = {}


def envelope(ev, step=0.1):
    """The loudness per interval of step seconds from the event's start: the waveform's peak amplitude in each."""
    key = (ev["id"], float(ev["t0"]), float(ev["t1"]), step)
    env = _ENVELOPES.get(key)
    if env is None:
        w = np.abs(waveform(ev))
        m = int(round(step * RATE))
        n = int(math.ceil(len(w) / m))
        env = [float(w[i * m:(i + 1) * m].max()) if i * m < len(w) else 0.0 for i in range(n)]
        _ENVELOPES[key] = env
    return env


def loudness(ev, t, step=0.1):
    """A sound's loudness at t, 0 to 1: the peak of its stand-in waveform in the interval of step seconds that holds t."""
    env = envelope(ev, step)
    i = int((t - float(ev["t0"])) / step)
    if i < 0 or i >= len(env):
        return 0.0
    return env[i]


def track(events, duration, pace=1.0):
    """A mono track of the stand-in sounds in the render's seconds: each sound at its t0 over the pace (a chain second
    plays over 1/pace seconds), stretched by the same, so it keeps time with the rings; returns float samples at RATE."""
    n = int(round(duration / pace * RATE)) + RATE
    out = np.zeros(n)
    for ev in events:
        if ev.get("kind") != "wave":
            continue
        w = waveform(ev)
        if pace != 1.0:
            idx = np.linspace(0.0, len(w) - 1, int(round(len(w) / pace)))
            w = np.interp(idx, np.arange(len(w)), w)
        _place(out, float(ev["t0"]) / pace, w)
    peak = float(np.max(np.abs(out))) if n else 0.0
    if peak > 1.0:
        out = out / peak
    return out


def write_wav(path, samples, rate=RATE):
    import struct
    import wave
    data = np.clip(samples, -1.0, 1.0)
    pcm = (data * 32767.0).astype("<i2").tobytes()
    with wave.open(str(path), "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(rate)
        f.writeframes(pcm)
    return path

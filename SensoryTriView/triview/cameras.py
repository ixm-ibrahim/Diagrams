"""The camera roads of the two photoreal views and of the four moves (concept sections 3 and 5).

- The Third-Person road: THIRD_KEYS in room metres, a cubic Hermite spline in time whose
  tangents are zeroed at every hold, so the camera truly rests where it rests and eases
  in and out of every move. It starts wide in the north-east corner (the foot of the bed,
  the window side) looking back along the bed, drifts in for the knock, the pain and the
  crest, slides south along the window wall as he walks, is close at his right side at the
  sill with his face in the light, goes behind his shoulder for the eyes closed in the sun
  (the reveal is made from there), lets him walk away at the chime, waits close by the bed
  for the return move, and ends where it began.
- The First-Person camera: on the eyes, looking where the head looks. CAM_FROM_HEAD turns
  the head's frame (x forward, y left, z up) into a camera's (looks down -Z, +Y up).
- The moves. Third to First and First to Third are roads in the head's own space, so the
  approach from behind lands on the eyes whatever the head does; the pass through the
  skull is covered by the lids closing and opening (a wipe, not a cut). Third to True is
  the reveal (his review of 2026-11-07): the camera pulls straight back along its own axis
  while the room dissolves into the mind's model of it, drawn by the model's camera on the
  exact twin of the room camera inside the skull, and goes on out through the back of the
  skull to the True road, so what was the Third-Person view turns out to have been the
  simulation in the head all along. True to Third is the mirror: the push back in. True to
  First (his review of 2026-11-08, second) is the dive: the camera goes in through the back
  of the skull to the simulated eyes, where the model's picture is the eyes' own, and the
  model dissolves into the room seen from the eyes. The dissolves are cross-dissolves of
  the two passes' display pictures, weighted so the model appears as the rest of the light
  dims rather than as light added.

Nothing here touches Blender objects; rungs bake what these functions return.
"""
import math

from mathutils import Matrix, Quaternion, Vector

from . import anim, engine
from .body import EYE_OFFSET

CAM_FROM_HEAD = Matrix(((0.0, 0.0, -1.0), (-1.0, 0.0, 0.0), (0.0, 1.0, 0.0)))
FIRST_LENS = 20.0

# (seconds, position, aim, lens) in room metres: x east, y north, z up. Rung 2b's timeline.
THIRD_KEYS = [
    (0.0, (3.55, 4.10, 1.80), (1.10, 0.90, 0.75), 24),
    (12.0, (3.55, 4.10, 1.80), (1.10, 0.90, 0.75), 24),
    (21.0, (3.30, 3.60, 1.65), (1.50, 0.80, 1.00), 28),
    (27.0, (3.10, 3.20, 1.50), (1.60, 0.75, 1.00), 32),
    (28.3, (2.95, 2.75, 1.40), (1.70, 0.55, 0.75), 40),
    (30.0, (2.95, 2.75, 1.40), (1.70, 0.55, 0.75), 40),
    (33.0, (2.90, 2.60, 1.40), (1.60, 0.68, 0.95), 42),
    (36.5, (3.05, 2.70, 1.40), (1.75, 0.60, 0.60), 36),
    (38.5, (3.05, 2.70, 1.45), (1.60, 0.72, 1.00), 38),
    (40.0, (2.95, 2.75, 1.40), (1.65, 0.65, 1.05), 38),
    (48.0, (3.05, 2.70, 1.45), (1.60, 0.75, 1.15), 40),
    (54.0, (3.25, 2.95, 1.55), (1.90, 0.75, 1.15), 30),
    (57.0, (3.50, 3.00, 1.60), (2.00, 0.80, 1.20), 28),
    (59.0, (3.60, 2.30, 1.60), (2.30, 0.85, 1.25), 28),
    (61.0, (3.70, 1.30, 1.60), (2.90, 1.00, 1.35), 30),
    (63.0, (3.76, 0.60, 1.58), (3.35, 1.15, 1.50), 34),
    (65.0, (3.75, 0.42, 1.55), (3.56, 1.20, 1.60), 38),
    (72.0, (3.75, 0.42, 1.55), (3.56, 1.20, 1.60), 38),
    (74.5, (3.65, 0.15, 1.45), (3.50, 1.20, 1.60), 24),
    (77.0, (3.65, 0.15, 1.45), (3.50, 1.20, 1.60), 24),
    (80.0, (2.25, 1.20, 1.72), (3.45, 1.20, 1.58), 45),     # behind his shoulder: the sun over the ridge past his head; the reveal's station
    (88.5, (2.25, 1.20, 1.72), (3.45, 1.20, 1.58), 45),
    (92.5, (3.20, 0.30, 1.60), (3.45, 1.20, 1.60), 34),
    (97.0, (3.70, 1.70, 1.62), (2.60, 1.00, 1.40), 28),
    (100.0, (3.55, 3.00, 1.70), (1.95, 0.75, 1.10), 26),
    (101.0, (2.90, 1.90, 1.50), (1.50, 0.75, 1.00), 30),    # close by the bed: the return move's station, inside the skull's reach
    (105.5, (2.90, 1.90, 1.50), (1.50, 0.75, 1.00), 30),
    (110.0, (3.55, 4.10, 1.80), (1.40, 0.80, 0.95), 24),
    (116.5, (3.55, 4.10, 1.80), (1.40, 0.80, 0.95), 24),
]


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def _tangents(keys, index):
    """Catmull-Rom tangents in time for the position and the aim, zero at a hold."""
    n = len(keys)
    if index == 0 or index == n - 1:
        return Vector((0, 0, 0)), Vector((0, 0, 0))
    t0, p0, a0, _ = keys[index - 1]
    t1, p1, a1, _ = keys[index]
    t2, p2, a2, _ = keys[index + 1]
    p0, p1, p2, a0, a1, a2 = Vector(p0), Vector(p1), Vector(p2), Vector(a0), Vector(a1), Vector(a2)
    hold_pos = (p1 - p0).length < 1e-6 or (p2 - p1).length < 1e-6
    hold_aim = (a1 - a0).length < 1e-6 or (a2 - a1).length < 1e-6
    mp = Vector((0, 0, 0)) if hold_pos else (p2 - p0) / (t2 - t0)
    ma = Vector((0, 0, 0)) if hold_aim else (a2 - a0) / (t2 - t0)
    return mp, ma


def hermite_road(keys, t):
    """A road through (t, position, aim, lens) keys: cubic Hermite in time with Catmull-Rom
    tangents zeroed at holds. Returns (position, aim, lens)."""
    if t <= keys[0][0]:
        return Vector(keys[0][1]), Vector(keys[0][2]), float(keys[0][3])
    if t >= keys[-1][0]:
        return Vector(keys[-1][1]), Vector(keys[-1][2]), float(keys[-1][3])
    for i in range(len(keys) - 1):
        t1, t2 = keys[i][0], keys[i + 1][0]
        if t1 <= t < t2:
            dt = t2 - t1
            u = (t - t1) / dt
            h00 = 2 * u ** 3 - 3 * u ** 2 + 1
            h10 = u ** 3 - 2 * u ** 2 + u
            h01 = -2 * u ** 3 + 3 * u ** 2
            h11 = u ** 3 - u ** 2
            mp1, ma1 = _tangents(keys, i)
            mp2, ma2 = _tangents(keys, i + 1)
            p1, p2 = Vector(keys[i][1]), Vector(keys[i + 1][1])
            a1, a2 = Vector(keys[i][2]), Vector(keys[i + 1][2])
            pos = h00 * p1 + h10 * dt * mp1 + h01 * p2 + h11 * dt * mp2
            aim = h00 * a1 + h10 * dt * ma1 + h01 * a2 + h11 * dt * ma2
            lens = anim.lerp(float(keys[i][3]), float(keys[i + 1][3]), anim.smoothstep(u))
            return pos, aim, lens
    return Vector(keys[-1][1]), Vector(keys[-1][2]), float(keys[-1][3])


def third_road(t):
    return hermite_road(THIRD_KEYS, t)


def look_quat_up(pos, aim, up):
    """A camera at pos looking at aim with its own up as near to `up` as the look allows, as a quaternion
    (a reveal's twin camera carries the room's up into the model, which is not the model's up)."""
    f = (Vector(aim) - Vector(pos))
    if f.length < 1e-9:
        f = Vector((1.0, 0.0, 0.0))
    f.normalize()
    r = f.cross(Vector(up))
    if r.length < 1e-6:
        r = f.cross(Vector((0.0, 0.0, 1.0)))
    r.normalize()
    u = r.cross(f).normalized()
    m = Matrix((r, u, -f)).transposed()   # columns: the camera's X, Y and Z axes
    return m.to_quaternion()


def look_quat(pos, aim):
    """A camera at pos looking at aim with +Y up, as a quaternion."""
    d = Vector(aim) - Vector(pos)
    if d.length < 1e-9:
        d = Vector((1.0, 0.0, 0.0))
    return d.to_track_quat("-Z", "Y")


def first_camera(head_frame):
    """Location and rotation of the First-Person camera: on the eyes, looking where the eyes look (the head's frame turned
    by the eyes' own look, body.Motion._eyes; the head's own frame where a frame carries none)."""
    rot = head_frame.get("eye_rot", head_frame["rot"]) @ CAM_FROM_HEAD
    return Vector(head_frame["eye"]), rot.to_quaternion()


def head_matrix(head_frame):
    return Matrix.Translation(Vector(head_frame["loc"])) @ head_frame["rot"].to_4x4()


# ---- the two head moves -----------------------------------------------------------

def _local_spline(keys, u):
    """A Hermite road in a local frame over u in 0..1; keys are (u, position)."""
    road = [(k[0], k[1], (0.0, 0.0, 0.0), 1.0) for k in keys]
    pos, _, _ = hermite_road(road, u)
    return pos


def ramp(t, a, b):
    """0 before a, 1 after b, smooth between."""
    if b <= a:
        return 1.0 if t >= b else 0.0
    return anim.smoothstep((t - a) / (b - a))


class MoveSample:
    def __init__(self, pos, rot, lens, cover=0.0, head_hidden=False, eye_weight=0.0):
        self.pos, self.rot, self.lens = pos, rot, lens
        self.cover = cover                  # how far the lids are closed, 0 open to 1 shut: the pass through the skull
        self.head_hidden = head_hidden      # the man's own head is hidden from the camera
        self.eye_weight = eye_weight        # 0 the Third camera's exposure and look, 1 the eye's

    @property
    def blink(self):
        return self.cover >= 0.999


# where the lids close and open on the way in and on the way out, as fractions of the move;
# the head is hidden only once the lids are nearly shut, and shown again before they open
IN_CLOSE, IN_SHUT, IN_OPEN = (0.86, 0.90), (0.90, 0.955), (0.955, 1.0)
OUT_CLOSE, OUT_SHUT, OUT_OPEN = (0.0, 0.03), (0.03, 0.085), (0.085, 0.14)


def third_to_first(t, t0, t1, head_at, third_at, lens_first=FIRST_LENS):
    """From the Third-Person road at t0, round his left side to behind his head and in to the eyes.

    head_at(t) gives the head frame, third_at(t) the Third road's (pos, aim, lens).
    """
    u = clamp((t - t0) / (t1 - t0))
    hf = head_at(t)
    H = head_matrix(hf)
    p_start, aim_start, lens_start = third_at(t0)
    start_local = head_matrix(head_at(t0)).inverted() @ Vector(p_start)
    keys = [(0.0, tuple(start_local)), (0.36, (0.45, 1.30, 0.15)), (0.70, (-0.85, 0.45, 0.12)),
            (0.88, (-0.30, 0.0, 0.04)), (1.0, tuple(EYE_OFFSET))]
    local = _local_spline(keys, u)
    pos = H @ local
    # the aim eases from the road's own aim point to his head over the first third, so the
    # first frame is the Third-Person frame it leaves (the mirror move does the same at its end)
    head_aim = Vector(hf["loc"]) + hf["fwd"] * 0.04
    aim = Vector(aim_start).lerp(head_aim, anim.smoothstep(u / 0.3))
    q_look = look_quat(pos, aim)
    _, q_eye = first_camera(hf)
    w = anim.smoothstep((u - 0.62) / 0.38)
    rot = q_look.slerp(q_eye, w)
    lens = anim.lerp(lens_start, lens_first, anim.smoothstep(u))
    cover = ramp(u, *IN_CLOSE) * (1.0 - ramp(u, *IN_OPEN))
    return MoveSample(pos, rot, lens, cover=cover, head_hidden=u >= IN_SHUT[0] - 0.005,
                      eye_weight=anim.smoothstep((u - 0.5) / 0.5))


def first_to_third(t, t0, t1, head_at, third_at, lens_first=FIRST_LENS):
    """The mirror: out through the back of his head as the lids close, round his right side to
    the place on the Third-Person road the other move left, so the two make one circle."""
    u = clamp((t - t0) / (t1 - t0))
    hf = head_at(t)
    H = head_matrix(hf)
    p_end, aim_end, lens_end = third_at(t1)
    end_local = head_matrix(head_at(t1)).inverted() @ Vector(p_end)
    keys = [(0.0, tuple(EYE_OFFSET)), (0.12, (-0.30, 0.0, 0.04)), (0.40, (-0.80, -0.55, 0.10)),
            (0.70, (-0.35, -1.05, 0.0)), (1.0, tuple(end_local))]
    local = _local_spline(keys, u)
    pos = H @ local
    _, q_eye = first_camera(hf)
    head_aim = Vector(hf["loc"]) + hf["fwd"] * 0.04
    aim = head_aim.lerp(Vector(aim_end), anim.smoothstep((u - 0.7) / 0.3))
    q_look = look_quat(pos, aim)
    w = anim.smoothstep(u / 0.38)
    rot = q_eye.slerp(q_look, w)
    lens = anim.lerp(lens_first, lens_end, anim.smoothstep(u))
    cover = ramp(u, *OUT_CLOSE) * (1.0 - ramp(u, *OUT_OPEN))
    return MoveSample(pos, rot, lens, cover=cover, head_hidden=u <= OUT_SHUT[1],
                      eye_weight=1.0 - anim.smoothstep(u / 0.5))


# ---- the reveal: between the room and the dark --------------------------------------

def _slerp_dir(a, b, s):
    a, b = Vector(a).normalized(), Vector(b).normalized()
    q = a.rotation_difference(b)
    q_s = Quaternion((1.0, 0.0, 0.0, 0.0)).slerp(q, s)
    return q_s @ a


class Reveal:
    """One of the two changes between the room and the dark, as one camera pulling out of the
    skull or pushing back in.

    to_true: the Third road until the hold; then the room camera pulls straight back along its
    own axis by `pull` metres until twin_end while the room dissolves into the model, the model's
    camera riding the exact twin of the room camera inside the skull (M(t) applied to it); then
    the model's camera goes on from the twin out to the True road's station at ease1, its distance
    from the head growing evenly in proportion, and from ease1 it rides the True road. The ghost
    and the soul come up as the camera leaves the skull.

    to_third: the mirror. The True road until the hold; the model's camera pushes in toward the
    twin of the Third road's station, its distance shrinking in proportion, until twin_start; from
    there to t1 the twins converge, the room camera coming in along the station's own axis from
    `pull` metres behind it, while the model dissolves into the room.

    to_first: the dive. The True road until the hold; the model's camera goes in to the twin of
    the First-Person camera, the simulated eyes, until twin_start; from there to t1 the room
    camera is the First-Person camera on the eyes and the model dissolves into the room seen
    from them.

    The sample's room_w is the room pass's share of the composite and model_w the model's, the
    two summing to one; fade_model is the model's own alpha, 1 through every mind move.

    spec: dict from data/cut.json. M_at(t) is the model's frame at t (room to ghost space, scale
    included), third_at and true_at the two roads, first_at(t) the First-Person camera (pos, aim, lens).
    """

    def __init__(self, name, spec, third_at, true_at, M_at, direction, head_centre=None, press=None, bounds=None, first_at=None):
        """press(t, point) -> point: the model's own pressing of what lies beyond the skull's reach toward
        the eyes (rung 2d), applied to the twin camera and its aim too, so the camera rides inside the
        model as the hits do."""
        self.name = name
        self.press = press
        # the room's box: the room camera's pull-back stops short of a wall (a station near the east
        # wall put the camera behind it, and the frame was the wall's back until it came through)
        self.bounds = bounds
        self.t0, self.t1 = float(spec["t0"]), float(spec["t1"])
        self.hold = float(spec["hold"])
        self.pull = float(spec.get("pull", 1.2))
        self.d0, self.d1 = (float(v) for v in spec["dissolve"])
        self.twin_end = float(spec.get("twin_end", self.d1))
        self.twin_start = float(spec.get("twin_start", self.d0))
        self.ease1 = float(spec.get("ease1", self.t1))
        self.third_at = third_at
        self.true_at = true_at
        self.first_at = first_at
        self.M_at = M_at
        self.direction = direction
        self.hc = Vector(head_centre) if head_centre is not None else Vector(engine.HEAD_CENTRE)

    def twin(self, room_cam, t):
        M = self.M_at(t)
        p, a, l = room_cam
        p, a = M @ Vector(p), M @ Vector(a)
        if self.press is not None:
            p, a = self.press(t, p), self.press(t, a)
        return p, a, l

    @staticmethod
    def _back(station, delta):
        p, a, l = station
        p, a = Vector(p), Vector(a)
        axis = (a - p).normalized()
        return p - axis * delta, a - axis * delta, l

    def _pull(self, station):
        """The pull-back for a station: the move's own, or less where a wall is nearer than that."""
        if self.bounds is None:
            return self.pull
        p, a, _ = station
        p, a = Vector(p), Vector(a)
        d = -(a - p).normalized()
        lo, hi = (Vector(self.bounds[0]), Vector(self.bounds[1]))
        t_exit = float("inf")
        for i in range(3):
            if d[i] > 1e-9:
                t_exit = min(t_exit, (hi[i] - p[i]) / d[i])
            elif d[i] < -1e-9:
                t_exit = min(t_exit, (lo[i] - p[i]) / d[i])
        return max(0.1, min(self.pull, t_exit - 0.08))

    def _between(self, cam0, cam1, s):
        """A camera on the way from cam0 to cam1: the distance from the head grows or shrinks in
        proportion, the direction turns evenly, the aim and the lens blend."""
        p0, a0, l0 = Vector(cam0[0]), Vector(cam0[1]), cam0[2]
        p1, a1, l1 = Vector(cam1[0]), Vector(cam1[1]), cam1[2]
        r0, r1 = p0 - self.hc, p1 - self.hc
        d0, d1 = max(r0.length, 1e-4), max(r1.length, 1e-4)
        d = d0 * (d1 / d0) ** s
        direction = _slerp_dir(r0, r1, s)
        return self.hc + direction * d, a0.lerp(a1, s), anim.lerp(l0, l1, s)

    def _ghost(self, mind_pos):
        d = (Vector(mind_pos) - self.hc).length
        return anim.smoothstep((d - 0.13) / 0.25)

    def sample(self, t):
        """dict(room=(pos, aim, lens), mind=(pos, aim, lens), room_w, model_w, fade_model, ghost_w, soul_w)."""
        if self.direction == "to_first":
            return self._sample_to_first(t)
        if self.direction == "to_true":
            if t <= self.hold:
                room = self.third_at(t)
                room = (Vector(room[0]), Vector(room[1]), room[2])
                mind = self.twin(room, t)
                return {"room": room, "mind": mind, "room_w": 1.0, "model_w": 0.0, "fade_model": 1.0, "ghost_w": 0.0, "soul_w": 0.0}
            station = self.third_at(self.hold)
            pull = self._pull(station)
            room_w = 1.0 - ramp(t, self.d0, self.d1)
            model_w = 1.0 - room_w
            if t <= self.twin_end:
                delta = pull * anim.smoothstep((t - self.hold) / (self.twin_end - self.hold))
                room = self._back(station, delta)
                mind = self.twin(room, t)
            else:
                room = self._back(station, pull)
                if t >= self.ease1:
                    p, a, l = self.true_at(t)
                    mind = (Vector(p), Vector(a), l)
                else:
                    start = self.twin(room, self.twin_end)
                    end = self.true_at(self.ease1)
                    s = anim.smoothstep((t - self.twin_end) / (self.ease1 - self.twin_end))
                    mind = self._between(start, end, s)
            g = self._ghost(mind[0])
            return {"room": room, "mind": mind, "room_w": room_w, "model_w": model_w, "fade_model": 1.0, "ghost_w": g, "soul_w": g}
        # to_third
        if t <= self.hold:
            p, a, l = self.true_at(t)
            mind = (Vector(p), Vector(a), l)
            return {"room": None, "mind": mind, "room_w": 0.0, "model_w": 1.0, "fade_model": 1.0, "ghost_w": self._ghost(mind[0]), "soul_w": self._ghost(mind[0])}
        if t >= self.t1:
            room = self.third_at(t)
            room = (Vector(room[0]), Vector(room[1]), room[2])
            mind = self.twin(room, t)
            return {"room": room, "mind": mind, "room_w": 1.0, "model_w": 0.0, "fade_model": 1.0, "ghost_w": 0.0, "soul_w": 0.0}
        station = self.third_at(self.t1)
        pull = self._pull(station)
        room_w = ramp(t, self.d0, self.d1)
        model_w = 1.0 - room_w
        if t >= self.twin_start:
            delta = pull * (1.0 - anim.smoothstep((t - self.twin_start) / (self.t1 - self.twin_start)))
            room = self._back(station, delta)
            mind = self.twin(room, t)
        else:
            room = self._back(station, pull)
            p, a, l = self.true_at(self.hold)
            start = (Vector(p), Vector(a), l)
            end = self.twin(room, self.twin_start)
            s = anim.smoothstep((t - self.hold) / (self.twin_start - self.hold))
            mind = self._between(start, end, s)
        g = self._ghost(mind[0])
        return {"room": room, "mind": mind, "room_w": room_w, "model_w": model_w, "fade_model": 1.0, "ghost_w": g, "soul_w": g}

    def _eye_twin(self, t):
        """The First-Person camera at t and its twin in the model: the simulated eyes."""
        p, a, l = self.first_at(t)
        room = (Vector(p), Vector(a), l)
        return room, self.twin(room, t)

    def _sample_to_first(self, t):
        if t <= self.hold:
            p, a, l = self.true_at(t)
            mind = (Vector(p), Vector(a), l)
            g = self._ghost(mind[0])
            return {"room": None, "mind": mind, "room_w": 0.0, "model_w": 1.0, "fade_model": 1.0, "ghost_w": g, "soul_w": g}
        room, twin = self._eye_twin(t)
        room_w = ramp(t, self.d0, self.d1)
        if t >= self.twin_start:
            mind = twin
        else:
            p, a, l = self.true_at(self.hold)
            start = (Vector(p), Vector(a), l)
            _, end = self._eye_twin(self.twin_start)
            s = anim.smoothstep((t - self.hold) / (self.twin_start - self.hold))
            mind = self._between(start, end, s)
        g = self._ghost(mind[0])
        return {"room": room, "mind": mind, "room_w": room_w, "model_w": 1.0 - room_w, "fade_model": 1.0, "ghost_w": g, "soul_w": g}

    def frames(self, fps=24):
        return list(range(anim.frame_of(self.t0, fps), anim.frame_of(self.t1, fps) + 1))

"""The engine: the True-Person view computed from the scene state by the concept's rules.

For every frame it reads the scene (the head's frame, the joints, the tagged surfaces
through raycasts, the phone, the sun) and the sense timeline (data/senses.json), and
writes a FrameState: the head-frame transform that turns the room into the model and the
mind's zoom, every region's and part's state of knowing and attention under the budget,
the fan of rays and the share of the sun's disc they reach, the thoughts, the senses on
the simulated body (rung 2p, his specification of 2026-11-12 and his review of 2026-11-13:
the rings of a sound, one per tenth of a second at the sound's loudness, each in its
source's own shade of the radar's green; touch's level on every part, which the
model draws as a glow over the patch of the part that meets another thing, magenta blended
toward red by pain and toward gold by pleasure; the sense light on a whole part, a pain or a pleasure
with no touch, the ear a ring crosses in green or in red when the sound hurts, the eyes red
in the sun's glare, every pain's red throbbing from its onset (pain_beat), the heart and the lungs while thought of; the band along a moving part's outline by how willed its
motion is (none on the head); warmth's level on every part, at rest by the sun's disc above the ridge, and the cold
air's on the named parts; the touch's spark, laid through the joints from the touched part up its
limb to the nearest point of the skull, struck where a touch begins (every pair of a body part and a
thing, or another part not joined to it at one joint, read by lidarscene.py with how fast its gap closed,
and handed in) and acting as lightning does (one spark from the
contact to the skull in two poses, each held two frames, then gone), its light the touch's intensity (the
timeline's strength times attention where it names the touch, never less than the touch's own by how fast
its gap closed), with the flash of the part it comes from; the organs' and the torso's breathing scales; the
gravity arrow; the First-Person flash toward a pain), the
will's words on their way down, and the camera's place on its road. It makes no Blender
objects; lidarscene.py draws what it says. (mindscene.py, rung 1's plates model, drew
comets, rivers, fields, a plumb line, breath and heart from the same state; the lidar
model of rung 2 replaced those forms.)

Coordinates: the room in metres; the model in ghost space, where the ghost's head is
at HEAD_CENTRE facing +x. room_to_model(frame) maps one to the other.
"""
import json
import math

from mathutils import Matrix, Vector

from . import anim, sound, tags
from .figure import HEAD_RADIUS, HEAD_SCALE

HEAD_CENTRE = Vector((0.0, 0.0, 1.63))
SKULL_RADII = Vector((HEAD_RADIUS * HEAD_SCALE[0], HEAD_RADIUS * HEAD_SCALE[1], HEAD_RADIUS * HEAD_SCALE[2]))
GLASS = 0.955                 # where "at the glass" is, as a fraction of the skull's radii
# the soul: a disc a closed hand across, three hands' width clear of the skull, behind and above the head on a
# line falling to the head's centre at forty-five degrees (his tenth review of 2026-11-10: straight above the
# crown until then; a hand's width clear until his eleventh, 2026-11-11: too close to the head)
SOUL_RADIUS = 0.045
SOUL_GAP = 0.30
SOUL_DIR = Vector((-1.0, 0.0, 1.0)).normalized()
SOUL_POS = HEAD_CENTRE + SOUL_DIR * (1.0 / math.sqrt(sum((SOUL_DIR[i] / SKULL_RADII[i]) ** 2 for i in range(3))) + SOUL_GAP + SOUL_RADIUS)
MODEL_SCALE = 1.0 / 24.0      # the model's scale in the skull while attention is in the room
# the mind's zoom (his review of 2026-11-07): when what he attends to is far, the sun and the range,
# the model shrinks so that it fits inside the skull, and comes back as attention returns to the room
FAR_TAGS = ("ridge", "ground", "sun")
ZOOM_IN_TAU, ZOOM_OUT_TAU = 1.0, 1.0   # his review of 2026-11-08: the model pumped; it breathes now
ZOOM_HOLD = 0.7              # seconds a nearer target must hold before the model comes back in: a glance at something near does not pull it
# the zoom fits what sight reaches: the scale at which the surfaces holding most of sight's attention
# sit inside the glass (his review of 2026-11-07: from the simulated eyes the model is the First-Person
# view, so what those eyes see must fit in the skull); SEEN_SHARE of the rays' attention, nearest first
SEEN_SHARE = 0.9
GLASS_RADIUS = 0.95 * min(SKULL_RADII) - 0.006   # the glass's reach from the eyes, as the lidar scene draws it
FIT_RADIUS = 0.93 * GLASS_RADIUS
# distance as the mind holds it (his review of 2026-11-08): within reach a thing sits at its distance;
# beyond, distance is compressed logarithmically, so the trees, the ridge, the sky and the sun keep
# their order but not their scale, the way nobody holds the sun at its true distance. The sky's
# believed distance is where the model's zoom stops: at FAR_SCALE it sits just inside the glass.
BELIEVE_NEAR = 6.0           # the mind's reach, a room's span: within it a distance is held as it is (2.2 until his sixth
                             # review of 2026-11-09: the room's own walls were compressed, so a camera standing between them
                             # in the room stood beyond them in the model, and the reveal looked at the walls' backs)
BELIEVE_K = 0.5              # 0.1 crushed the trees, the range and the sky into one shell at the glass (his review of 2026-11-09);
                             # at 0.5 the outside beyond the reach takes 4.9 believed metres whatever the reach is
# a thing's radius over its distance from the eyes: below the first a thing is compact, held whole at one
# believed distance with its shape kept (a crown stays a crown); above the second it spans its own
# distance (the ground, the range, the sky) and is held piece by piece, every hit compressed on its own
COMPACT = (0.5, 1.0)
BELIEVE_FLAT_FROM = 6.0      # before the far field has resolved, everything beyond this (outside the room) lies flat at the sky's distance
# a thought (his seventh review of 2026-11-10: conscious memory is what he thinks of at the moment, coming up
# fast and fading slowly) rises over this many seconds; it fades over its own time in the timeline
THINK_RISE = 0.4
COLOUR_DELAY = 1.5           # a thought's things come up as their shapes first, colourless, and their colour arrives this many
COLOUR_RISE = 1.0            # seconds after the thought begins, over this many (his word of 2026-11-12: the geometry of a thing
                             # and its colour come to mind at different times)
THINK_FAINT = 0.02           # the faintest light of a thought that shows (the memory material thins a tile out under five times
                             # this): a thought that names its own rise, a slow one, comes up from it by equal ratios in equal
                             # times, so its shape thickens in over the first two fifths of the rise and brightens over the rest
                             # (his word of 2026-11-14 on the bed's coming: "it needs to be slower, matching the gradual increase
                             # in awareness when waking up"; a smoothstep of the same rise stood whole within its first fifth)
AWARE_FLOOR = 0.02           # a thought's clock runs at one over his awareness, no faster than this allows (his word of
                             # 2026-11-12: the drop faster when awareness is low): at full awareness a thought fades over its
                             # own time from the timeline; at none it is gone fifty times sooner
BELIEVE_FLAT_K = 1.0
KNEE = 0.9                   # the share of the glass radius where the model presses what still lies outside onto the glass
FIELD_H, FIELD_V = 200.0, 130.0   # the field of both eyes together: an ellipse 200 degrees across, 130 high
SUN_LIMB_DEG = 0.27          # the sun's disc, its radius from the eyes, where the scene's sky gives none (the reader takes the sky's own
                             # sun size): five rays, the centre and four limbs, tell whether the eyes' rays reach any of it
SUN_UP_RAYS = 96             # rays spread evenly over the disc by area, each at a height of its own (a sunflower): the share of them
                             # clear of the land is the share of the disc that is up, in steps of a hundredth as the sun rises over a
                             # ridge (the five rays alone went from a fifth to four fifths in one frame, 2026-11-16)
SUN_FLOWER = tuple((math.sqrt((i + 0.5) / SUN_UP_RAYS) * math.cos(i * math.pi * (3.0 - math.sqrt(5.0))),
                    math.sqrt((i + 0.5) / SUN_UP_RAYS) * math.sin(i * math.pi * (3.0 - math.sqrt(5.0)))) for i in range(SUN_UP_RAYS))
SUN_CAST = 3000.0            # metres a ray toward the sun is followed: past everything that can stand before the sun (the stand-in
                             # range at 300 m), short of the sky's shell (SKY_DISTANCE). The reader's own reach is 200 m
SUN_NEAR = 60.0              # metres from his eyes beyond which what stands before the sun is the land (the range), not his hand
                             # or the room: the share of the disc clear of the land is the share that is up (sun_up)
THINK_REACH = 1.0            # a thought's weight in the mind's zoom, as a share of a full fan of sight at attention 1 (his eighth
                             # review of 2026-11-10: the chime's place behind him is what he attends to, so the model comes in to it)
SKY_DISTANCE = 9000.0        # the scan's shell for the sky, room metres


def _ordered(d):
    near = min(d, BELIEVE_NEAR)
    over = max(d - BELIEVE_NEAR, 0.0)
    return near + BELIEVE_K * math.log(1.0 + over / BELIEVE_K)


BELIEVE_SKY = _ordered(SKY_DISTANCE)
BELIEVE_FLAT_BASE = _ordered(BELIEVE_FLAT_FROM)
BELIEVE_SUN = BELIEVE_SKY + 0.3   # the sun, a ball of light a little beyond the sky
FAR_SCALE = FIT_RADIUS / BELIEVE_SKY   # his review of 2026-11-07: at 1/800 the body was a speck; about 1/86 with the sky at 7.1 believed metres


def believed(d, resolve=1.0):
    """A room distance as the mind holds it: resolve 0 lays everything beyond the room flat at the sky's
    distance, as the sun is the moment it hits; 1 keeps the far things in order, compressed."""
    ordered = _ordered(d)
    far = max(d - BELIEVE_FLAT_FROM, 0.0)
    flat = min(ordered, BELIEVE_FLAT_BASE) + (BELIEVE_SKY - BELIEVE_FLAT_BASE) * (1.0 - math.exp(-far / BELIEVE_FLAT_K))
    return flat + (ordered - flat) * resolve


def compact_weight(radius, centre_distance):
    """How much a thing is held whole: 1 for a thing small against its distance, 0 for one that spans it."""
    ratio = radius / max(centre_distance, 1e-3)
    return 1.0 - anim.smoothstep((ratio - COMPACT[0]) / (COMPACT[1] - COMPACT[0]))


def believed_hit(d, centre_distance, radius, resolve=1.0):
    """A hit's distance as the mind holds it, the same rule as the model's geometry (triview/lidarscene.py
    place): a compact thing is scaled whole about the eyes by its centre's believed distance over its
    true one, so its shape and its angular size are kept; a thing that spans its distance is compressed
    hit by hit; before the far field resolves everything beyond the reach lies flat at the sky."""
    w = compact_weight(radius, centre_distance)
    shape = _ordered(centre_distance) * d / max(centre_distance, 1e-3)
    resolved = _ordered(d) + (shape - _ordered(d)) * w
    far = max(d - BELIEVE_FLAT_FROM, 0.0)
    flat = min(_ordered(d), BELIEVE_FLAT_BASE) + (BELIEVE_SKY - BELIEVE_FLAT_BASE) * (1.0 - math.exp(-far / BELIEVE_FLAT_K))
    return flat + (resolved - flat) * resolve
PLUMB_LEN = 0.045            # the gravity arrow's length in the skull, a fixed glyph whatever the model's scale (rung 1's; the
                             # lidar model draws the arrow inside the simulated skull, sized with the model: triview/lidarscene.py)
# ---- the senses on the simulated body (rung 2p, his specification of 2026-11-12) ----
RING_EVERY = 0.1             # seconds between the rings of a sound: one ring per interval while it lasts, as bright as the sound is
                             # loud in that interval (loudness: the event's envelope, a stand-in for the sound file of rung 6)
RING_FADE = 0.12             # seconds a ring takes to go once it has passed the farther ear
LOUD = 0.7                   # a sound louder than this (the timeline's strength) hurts: the ear it crosses goes red and fades
PAIN_FADE = 1.0              # seconds a pain's glow on the ear or the eyes fades over: pain persists a short while
PAIN_THROB_HZ = 1.6          # whatever is in pain throbs, the ears, the eyes or a part of the body (his word of 2026-11-13,
PAIN_THROB_LOW = 0.4         # twelfth round: so that its persistence shows): beats a second; the share of the pain's light left
PAIN_THROB_RISE = 0.12       # between two beats; the share of a beat it rises over; and how fast it falls after (e to the
PAIN_THROB_FALL = 3.0        # minus this by the next beat). A pain stands at a beat's top at its onset (pain_beat)
EAR_CROSS = 0.08             # seconds an ear stays lit after a ring has crossed it, so a crossing reads at the render's rate
GLARE = 1.2                  # how hard the sun hurts the eyes as it first hits them, per share of its disc the rays come to reach
GLARE_HOLD = 0.0             # no steady smart while the disc stays in them (0.1 per share of the disc until his eleventh round of
                             # 2026-11-13: the eyes stood red all through the window and read as pain or as warmth; his
                             # specification is a red that fades)
GLARE_ANGLE = (20.0, 35.0)   # degrees from the line of sight within which the sun dazzles in full, and beyond which not at all:
                             # a sun low in the field's corner is light on the face, not glare (in this stand-in scene the sun clears
                             # the ridge from 26 s and stands in the 200-degree field for most of the piece)
PROP_SPEED = 0.5             # room metres a second at which a moving part's outline glows at its full
PROP_FLOOR = 0.3             # the share of that glow a movement keeps when nothing wills it (a sway, a settling)
PROP_MAX = 0.35              # the outline's brightness for a willed movement at full speed: faint, never bright (his word)
LIGHTNING_REACH = (0.5, 1.0)   # one spark from the point of contact to the head, gone at once (his word of 2026-11-13, tenth
                             # round: as a bolt of lightning is, with a gap to see between two touches). How far along its
                             # path its front has come at each frame of its life: half way at the frame the contact begins,
                             # at the skull at the next, nothing at the third: two frames, a twelfth of a second of the
                             # film. (Until then it reached the skull in 0.07 s and struck along the whole path for eight
                             # frames more, each frame a new zigzag: three touches in a row read as one beam that lasted
                             # and ran both ways. Before that 1.8 room metres a second, or the timeline's own speed for
                             # the impact, which still sets how long the impact's glow lasts)
LIGHTNING_HOLD = 2           # frames each of the spark's poses stands: the spark is animated at half the scene's frame rate, on
                             # twos, while the scene moves every frame (his word of 2026-11-13, twelfth round: he liked the
                             # spark better in the half-speed clip, 'the framerate of the lightning movement is not the same as
                             # the scene itself'). Its path is laid at a pose's first frame and stands still for the pose
LIGHTNING_FULL = 0.8         # a spark's light is the touch's intensity, the impact's strength times the attention the timeline gives
LIGHTNING_CURVE = 2.0        # it at its second: in full from this intensity, the pain's (0.9 times 0.9), and below it by this power, so
                             # a contact barely felt (an unnamed one, 0.075) is barely to be seen: a hundredth of the pain's light (his
                             # word of 2026-11-13, eleventh round. Until then the attention alone, under the budget of the moment)
LIGHTNING_SLOTS = 6
STRIKE_MATCH = 0.5           # seconds within which a strike read off the contact and a touch impact the timeline names on the
                             # same limb are one event: the strike takes the impact's strength (0.4 until the thirteenth round: the
                             # hand lands on the phone 0.4 s before the timeline's 105 s, and the phone had a second spark there)
STRIKE_SOFT = 0.2            # a touch's own intensity for its spark, read off the contact (his word of 2026-11-13, thirteenth round:
STRIKE_HARD = 0.6            # some sparks seemed missing): from the first where the gap closed at a standstill to the second where it
STRIKE_SPEED = 1.0           # closed at this many metres a second or faster, times his awareness. A touch the timeline names is never
                             # dimmer than this. (Until then a touch the timeline did not name had 0.075 of the full intensity, under a
                             # hundredth of the full light: 78 of the piece's 90 sparks could not be seen.)
LIGHTNING_KNOTS = 10         # the points a signal's path is laid through: the touched place on the skin, the nearest point of
                             # the part's own axis, the joints from there up its limb to the neck, then the nearest point of the
                             # skull (his word of 2026-11-13: through the centre of the limbs, the shortest way from the touch
                             # to the closest part of the skull, not through the air; his word of 2026-11-16: it begins from
                             # the point of contact, not a joint. 8 until then, the path begun at a joint)
STRIKE_SOURCE = 3.0          # seconds: a pain's spark, which no contact shows, starts where the part was last touched if that
                             # was within this long before it (the hurt comes from the knock), else at the middle of the part
LIGHTNING_COLOUR = (0.72, 0.86, 1.0)   # a spark's bluish white, whatever the sense that sends it (the same word)
HEAD_CLEAR = 0.03            # room metres outside the simulated head's surface where the signal stops, clear of the eyes' picture
TORSO_BREATH = 0.035         # the simulated torso scales by this share at a full breath: gently (his word)
HEART_SWELL = 0.25           # the heart's scale swings by this share with each beat
LUNG_SWELL = 0.3             # the lungs' scale swings by this share over a full breath
FLASH_FROM = 0.25            # a pain's attention over which the First-Person frame flashes red toward it
SENSE_MIX = 0.6              # a sense's colour on a part takes this share and the part's own colour the rest (his word of 2026-11-12:
                             # 30 to 50 percent of the actual colour kept, for touch, proprioception and temperature); the red of a
                             # hurting ear and of the eyes in the glare stands alone, as he specified it; the heart and the lungs keep
                             # most of their own colours (ORGAN_MIX)
ORGAN_MIX = 0.36
WARM_REST = 0.2              # the sun's warmth on any part its rays reach, as far as he is aware, by the share of the sun's disc
                             # above the ridge: the body feels it too, not the parts the timeline names alone (his word of
                             # 2026-11-13, eleventh round). The timeline's warmth on a part stands where it is higher
TOUCH_REST = 0.25            # the level of a resting contact, as far as he is aware: the pillow under the head, the mattress under
                             # the back, the floor under the feet. Touch is contact (his word of 2026-11-12: one rule for everything
                             # that touches him, and only the patch that is touched): the model lights the part of a body part's
                             # surface that meets another thing's, at this level or at the timeline's touch on the part where higher
ORGAN_CLEAR_AT = 0.3         # the attention on the breath or the heartbeat at which the chest's tiles have cleared in full (to
                             # CHEST_CLEAR of their opacity gone): thought of at all, the organs show

RAY_ROWS, RAY_COLS = 3, 9
RAY_COUNT = RAY_ROWS * RAY_COLS


def _fan_weight():
    """The attention a full fan of sight carries at attention 1: the sum of its rays' weights."""
    s = 0.0
    for i in range(RAY_ROWS):
        for j in range(RAY_COLS):
            u = -1.0 + 2.0 * (j + 0.5) / RAY_COLS
            v = -1.0 + 2.0 * (i + 0.5) / RAY_ROWS
            s += 1.0 - 0.55 * math.sqrt(u * u + v * v) / math.sqrt(2.0)
    return s


FAN_WEIGHT = _fan_weight()
WAVE_SLOTS = 12
DISC_SLOTS = 3
WARMTH_SLOTS = 3
PULSES_PER_CHAIN = 2
WAVE_TRAVEL = 0.3            # seconds for a ring to reach the nearer ear (0.45 until rung 2p: with a ring every tenth of a second
                             # the eye follows the stream, so a ring may travel faster, his word of 2026-11-12)
SWELL_TRAVEL = 0.9
COMET_SPEED = 1.8            # room metres per second along the body
TAIL = 0.14

# sound sources outside the window, in room coordinates (judged, so roughly)
FAR_SOURCES = {
    "range_a": Vector((80.0, 12.0, 9.5)), "range_b": Vector((80.0, -14.0, 8.5)),
    "ground_a": Vector((30.0, 6.0, 0.3)), "ground_b": Vector((48.0, -9.0, 0.3)),
}

# the True-Person camera's road (concept section 4) on rung 2b's timeline: seconds, position, aim, lens
CAMERA_KEYS = [
    (0.0, (4.0, 0.0, 1.15), (0.0, 0.0, 1.05), 24),
    (4.0, (4.0, 0.0, 1.15), (0.0, 0.0, 1.05), 24),
    (12.0, (1.9, 0.0, 1.82), (0.0, 0.0, 1.69), 50),
    (24.0, (1.8, -0.2, 1.82), (0.0, 0.0, 1.69), 50),
    (27.0, (0.12, -1.25, 1.72), (0.0, 0.0, 1.655), 60),
    (35.0, (0.08, -1.25, 1.72), (0.0, 0.0, 1.655), 60),
    (38.5, (1.2, -0.9, 1.9), (0.1, 0.0, 1.64), 50),
    (44.5, (-1.6, -0.1, 2.0), (0.25, 0.0, 1.62), 45),
    (56.0, (-1.55, 0.05, 2.0), (0.25, 0.0, 1.62), 45),
    (64.0, (-1.5, 0.1, 1.98), (0.3, 0.0, 1.6), 45),
    (72.0, (-1.5, 0.1, 1.98), (0.3, 0.0, 1.6), 45),
    (76.0, (-2.6, 0.2, 2.1), (0.0, 0.0, 1.45), 40),
    (80.0, (-3.2, 0.25, 2.0), (0.0, 0.0, 1.3), 32),
    (84.0, (-4.6, 0.3, 1.5), (0.0, 0.0, 1.05), 24),
    (88.3, (-4.6, 0.3, 1.5), (0.0, 0.0, 1.05), 24),
    (91.5, (-0.3, 2.2, 1.78), (0.0, 0.0, 1.62), 45),
    (94.0, (-0.5, 2.0, 1.85), (0.0, 0.0, 1.62), 45),
    (97.5, (0.6, 1.7, 1.9), (0.0, 0.0, 1.62), 45),
    (99.5, (1.35, 0.85, 1.85), (0.0, 0.0, 1.62), 45),     # front and left: the return move pushes in from here, the Third station being in front of him
    (106.0, (1.35, 0.85, 1.85), (0.0, 0.0, 1.62), 45),
    (110.0, (3.0, 2.2, 1.4), (0.0, 0.0, 1.2), 28),
    (114.0, (4.0, 0.0, 1.15), (0.0, 0.0, 1.05), 24),
    (116.5, (4.0, 0.0, 1.15), (0.0, 0.0, 1.05), 24),
]

GREY = tags.SENSE_COLOUR["memory"]


def clamp(v, lo=0.0, hi=1.0):
    return lo if v < lo else hi if v > hi else v


def to_glass(p, fraction=GLASS):
    """Project a ghost-space point beyond the skull's reach onto the glass; inside it stays."""
    d = p - HEAD_CENTRE
    e = Vector((d.x / (SKULL_RADII.x * fraction), d.y / (SKULL_RADII.y * fraction), d.z / (SKULL_RADII.z * fraction)))
    L = e.length
    if L <= 1.0:
        return p, False
    e /= L
    return HEAD_CENTRE + Vector((e.x * SKULL_RADII.x * fraction, e.y * SKULL_RADII.y * fraction, e.z * SKULL_RADII.z * fraction)), True


def piecewise(points, t, tkey="t", vkey="a"):
    if t <= points[0][tkey]:
        return points[0][vkey]
    for a, b in zip(points, points[1:]):
        if a[tkey] <= t < b[tkey]:
            return anim.lerp(a[vkey], b[vkey], (t - a[tkey]) / (b[tkey] - a[tkey]))
    return points[-1][vkey]


def catmull(keys, t):
    """Catmull-Rom over (t, position, aim, lens) keys: a continuous road with no stops."""
    n = len(keys)
    if t <= keys[0][0]:
        return Vector(keys[0][1]), Vector(keys[0][2]), keys[0][3]
    if t >= keys[-1][0]:
        return Vector(keys[-1][1]), Vector(keys[-1][2]), keys[-1][3]
    for i in range(n - 1):
        if keys[i][0] <= t < keys[i + 1][0]:
            k0 = keys[max(i - 1, 0)]
            k1, k2 = keys[i], keys[i + 1]
            k3 = keys[min(i + 2, n - 1)]
            u = (t - k1[0]) / (k2[0] - k1[0])

            def cr(a, b, c, d):
                a, b, c, d = Vector(a), Vector(b), Vector(c), Vector(d)
                return 0.5 * ((2 * b) + (-a + c) * u + (2 * a - 5 * b + 4 * c - d) * u * u + (-a + 3 * b - 3 * c + d) * u ** 3)

            pos = cr(k0[1], k1[1], k2[1], k3[1])
            aim = cr(k0[2], k1[2], k2[2], k3[2])
            lens = anim.lerp(k1[3], k2[3], anim.smoothstep(u))
            return pos, aim, lens
    return Vector(keys[-1][1]), Vector(keys[-1][2]), keys[-1][3]


def pain_beat(since):
    """A pain's throb, `since` seconds after its onset: 1 at the onset and at every beat's top, a quick rise and a slow
    fall to about PAIN_THROB_LOW before the next beat."""
    phi = (max(since, 0.0) * PAIN_THROB_HZ + PAIN_THROB_RISE) % 1.0
    if phi < PAIN_THROB_RISE:
        x = phi / PAIN_THROB_RISE
        beat = x * x * (3.0 - 2.0 * x)
    else:
        beat = math.exp(-PAIN_THROB_FALL * (phi - PAIN_THROB_RISE) / (1.0 - PAIN_THROB_RISE))
    return PAIN_THROB_LOW + (1.0 - PAIN_THROB_LOW) * beat


class Region:
    """One held region of the model: a surface or a body part."""

    def __init__(self, tag):
        self.tag = tag
        self.in_mind = 0.0        # 0 dark, 1 held, fading in between
        self.finish = 0.7         # 0 sharp, 1 soft (filled in)
        self.filled = False
        self.last_sensed = None
        self.att = 0.0
        self.colour = GREY
        self.state = tags.DARK
        self.seen_ever = False
        self.finish_from = None


class FrameState:
    def __init__(self, frame, t):
        self.frame, self.t = frame, t
        self.M = Matrix.Identity(4)
        self.regions = {}      # tag -> dict(att, col, face, edge, soft, state)
        self.parts = {}        # part -> dict(att, col, state)
        self.sim_joints = {}   # joint -> ghost-space position
        self.rays = []         # (a, b, att) in ghost space, RAY_COUNT entries, att 0 hides
        self.waves = []        # (centre, radius, strength, att), WAVE_SLOTS entries
        self.wave_colours = [] # each ring's colour, its source's shade of the radar's green, beside waves
        self.discs = []        # (centre, radius, att), DISC_SLOTS entries
        self.pulses = {}       # chain -> [(pos, att, colour, flash_att)] PULSES_PER_CHAIN entries
        self.rivers = {}       # chain -> (colour, width, att)
        self.fields = {}       # slot -> (pos, colour, spread, att)
        self.throb = (Vector((0, 0, 0)), 1.0, 0.0)
        self.breath = (1.0, 0.0)
        self.heart = (1.0, 0.0)
        self.glow = 0.0
        self.plumb = (Vector((0, 0, 0)), Vector((0, 0, 0)), 0.0)
        self.warmth = []       # (a, b, att) WARMTH_SLOTS entries
        self.sun = (Vector((0, 0, 0)), 0.0, GREY)
        self.ridge = []        # list of ghost-space points, a polyline
        self.ridge_att = (0.0, GREY)
        self.ground = []       # 4 ghost-space points
        self.ground_att = (0.0, GREY)
        self.words = {}        # word -> att
        self.will = []         # (index, pos, att)
        self.camera = (Vector((4, 0, 1.15)), Vector((0, 0, 1.05)), 24.0)
        self.ghost = 1.0
        self.phone = None      # ghost-space matrix of the phone, or None
        self.rug_curled = False
        self.budget_scale = 1.0
        self.awareness = 1.0
        self.attention_leader = ("none", 0.0)   # (sense, scaled attention) of the strongest sense event
        self.scale = MODEL_SCALE               # the model's scale in the skull this frame (the mind's zoom)
        self.far = 0.0                         # 1 while attention is on the far things, the range and the sun
        self.sight_att = 0.0                   # sight's attention this frame, 0 with the eyes shut: gates the seen picture
        self.thought = {}                      # tag -> the conscious attention on the region from memory, 0..1 (the timeline's thoughts)
        self.thought_colour = {}               # tag -> how far the thought's thing has its colour back, 0..1 (COLOUR_DELAY after the thought begins)
        self.sun_sight = 0.0                   # 1 while the eyes' rays reach any of the sun's disc this frame (it lies in the field of both eyes and some of it is clear of his hand, the room and the land), else 0
        self.sun_up = 0.0                      # the share of the sun's disc clear of the land on its own line from his eyes, whatever his hand or the room hides
        self.sun_felt = 0.0                    # the attention a sense other than sight holds on the sun this frame (the warmth on his face), 0..1
        self.eye_room = Vector((0, 0, 0))      # the eyes in room metres, and the head's rotation there, for the projector
        self.head_rot = Matrix.Identity(3)
        # the senses on the simulated body (rung 2p)
        self.sense_light = {}                  # part -> (colour, strength 0..1, tint 0..1): the sense's light on the part, drawn on its tiles
                                               # and its known shape; tint is how far the colour replaces the part's own
        self.outline = {}                      # part -> (colour, strength 0..1): a glow along the part's outline (proprioception)
        self.temperature = {}                  # part -> (warmth's level, the cold air's level): drawn by the model on the skin the
                                               # sun's rays and the window's air reach
        self.lightning = []                    # (the path's points, progress 0..1, att, colour, the frame it began at) in ghost space, LIGHTNING_SLOTS entries
        self.spark_part = {}                   # part -> the light of the spark that comes from it this frame: the part flashes with it
        self.organs = {"heart": 1.0, "lung": 1.0, "torso": 1.0}   # the scales of the heart, the lungs and the torso this frame
        self.throb_pulse = 1.0                 # the pain's throb this frame, 0.55 to 1
        self.flash = (0.0, None)               # the First-Person flash: its level, and the pain's direction from the eyes in the room
        self.touch = {}                        # part -> (colour, level 0..1): touch's level on the part, drawn by the model where the part's
                                               # surface meets another thing's


class Engine:
    def __init__(self, data, reader, fps=24, ridge_profile=None, window=None, room_size=None, targets=None,
                 thing_points=None, twin_spans=None, cover_of=None, strikes=None, ridge_elevation=None):
        self.data = data
        # the ridge's height on the sun's line, degrees (room.RIDGE_ELEVATION): the sun's warmth on the skin is by the share
        # of its disc above it
        self.ridge_elevation = ridge_elevation
        # the moments a touch begins or lands anew, read off the contact itself: (second, part, how fast the gap closed,
        # metres a second, the touched place on the part's skin in the room at that second, or None)
        # (lidarscene.strikes_of_pairs)
        self.strikes = sorted((tuple(h) + (None,) * (4 - len(h)) for h in (strikes or [])), key=lambda h: h[:3])
        self._strike_peak = {}                 # a spark's strength: the most its event has had since it began, held through its life
        self._strike_pose = {}                 # (part, second, pose) -> the path's points in the model, laid at the pose's first frame
        self._strike_anchor = {}               # (part, second) -> where the touch lies on the part: how far along its axis, and off it
        self.cover_of = cover_of               # the lids' cover at a second (triview/eye.py), for the sun's glare on the eyes
        self.targets = {k: Vector(v) for k, v in (targets or {}).items()}   # named places a sight event can aim at
        # a room point for every region a thought can name, for the zoom's reach; and the reveals' twin
        # phases (dicts ease_from, from, to in seconds), when the model is the room at one scale
        self.thing_points = {k: Vector(v) for k, v in (thing_points or {}).items()}
        self.twin_spans = [dict(s) for s in (twin_spans or [])]
        self.reader = reader
        self.fps = fps
        self.ridge_profile = ridge_profile or []
        self.window = window or (0.5, 1.9, 0.9, 2.1)
        self.room_size = room_size or (4.0, 4.5, 2.6)
        self.budget = data.get("budget", {"ceiling": 1.0, "held_floor": 0.05, "held_base": 0.12})
        self.regions = {tag: Region(tag) for tag in tags.SURFACES}
        self.regions["table_far"].filled = True
        self.regions["table_far"].finish = 0.9
        self.parts = {p: Region(p) for p in tags.PARTS}
        self.memory = sorted(data.get("memory", []), key=lambda m: m["t"])
        self.thoughts = sorted(data.get("thoughts", []), key=lambda m: m["t0"])
        self._aw_cum_t, self._aw_cum, self._aw_cost1 = 0.0, 0.0, {}
        self.body_memory = sorted(data.get("body_memory", []), key=lambda m: m["t"])
        self.events = data["events"]
        self.will = data["will"]
        self.recognition = data["recognition"]
        self.plumb_dir = Vector((0.0, 0.0, -1.0))
        self.plumb_vel = Vector((0.0, 0.0, 0.0))
        self.plumb_a_s = 0.0                   # balance's attention from the motion itself, decaying
        self.prev_pd_head = None
        self.zoom = True
        self.scale = MODEL_SCALE
        self.zoom_log = math.log(MODEL_SCALE)
        self.zoom_hist = []
        self.far_level = 0.0                   # a smoothed vote for the far things, with hysteresis below
        self.far_state = False
        self.near_frames = 0
        self.prev_head = None
        self.prev_head_v = None
        self.veil = {}
        self.sun_seen_ever = False
        self.rug_curled = False
        self.last_region_lookup = {}
        # the senses' states between frames (rung 2p)
        self.prev_J = None                     # last frame's joints, for a part's speed
        self.ear_lit = {"ear_l": 0.0, "ear_r": 0.0}    # an ear's green after a ring has crossed it, fading
        self.ear_pain = {"ear_l": 0.0, "ear_r": 0.0}   # its red after a loud ring, fading
        self.ear_hurt_t = {"ear_l": 0.0, "ear_r": 0.0}  # when that hurt began: its throb counts from there
        self.hurt_from = None                  # where the loud sound came from, for the First-Person flash
        # a shade of the radar's green per sound source, in the order the sources first sound in the timeline
        order = []
        for ev in sorted((e for e in self.events if e.get("kind") == "wave"), key=lambda e: float(e.get("t0", 0.0))):
            if ev["source"] not in order:
                order.append(ev["source"])
        self.sound_shade = {src: tags.sound_shade(k) for k, src in enumerate(order)}
        self.eye_pain = 0.0                    # the eyes' smart from the sun's glare, fading
        self.eye_hurt_t = 0.0                  # when that smart began: its throb counts from there
        self.prev_sun_hit = 0.0

    # ---- envelopes ----
    @staticmethod
    def _attention(ev, t):
        a = ev.get("attention", 0.5)
        if "decay" in ev:
            return piecewise(ev["decay"], t)
        t0 = ev.get("t0", ev.get("t", 0.0))
        t1 = ev.get("t1", t0)
        if isinstance(a, (list, tuple)):
            u = 0.0 if t1 <= t0 else clamp((t - t0) / (t1 - t0))
            base = anim.lerp(a[0], a[1], u)
        else:
            base = a
        if "dip" in ev and t >= ev["dip"][0]["t"]:
            base = min(base, piecewise(ev["dip"], t))
        return base

    def envelope(self, ev, t, attack=0.12, release=0.5):
        t0 = ev.get("t0", ev.get("t"))
        t1 = ev.get("t1", t0 + ev.get("life", 0.0))
        if t < t0 or t > t1 + release:
            return 0.0
        ramp = anim.smoothstep((t - t0) / attack) if attack > 0 else 1.0
        if t > t1:
            ramp *= 1.0 - anim.smoothstep((t - t1) / release)
        return self._attention(ev, min(t, t1)) * ramp

    # ---- memory schedules ----
    def _apply_memory(self, t):
        """The latest schedule entry for each region decides whether it is in mind."""
        latest = {}
        for m in self.memory:
            if m["t"] <= t:
                latest[m["region"]] = m
        for tag, m in latest.items():
            r = self.regions.get(tag)
            if r is None:
                continue
            if m["in_mind"]:
                r.in_mind = anim.smoothstep((t - m["t"]) / 0.8)
                if r.finish_from is not m:
                    r.finish_from = m
                    fin = m.get("finish", "keep")
                    if fin == "sharp":
                        r.finish = 0.0
                    elif fin == "soft":
                        r.finish = 0.7
                    elif fin == "filled":
                        r.finish = 0.9
            else:
                r.in_mind = 1.0 - clamp((t - m["t"]) / m.get("fade", 1.0))
        latest_p = {}
        for m in self.body_memory:
            if m["t"] <= t:
                for p in m["parts"]:
                    latest_p[p] = m
        for p, m in latest_p.items():
            r = self.parts[p]
            if m["in_mind"]:
                r.in_mind = anim.smoothstep((t - m["t"]) / 0.8)
            else:
                r.in_mind = 1.0 - clamp((t - m["t"]) / m.get("fade", 1.0))

    # ---- thoughts ----
    def _aw_cost(self, t):
        """A thought's clock from the start to t: the integral of one over his awareness, floored at AWARE_FLOOR,
        so the clock runs at the timeline's pace while he is fully aware and faster as awareness falls. Kept
        running frame by frame, since the frames come in order; a step back restarts it."""
        step = 1.0 / self.fps
        if t < self._aw_cum_t:
            self._aw_cum_t, self._aw_cum = 0.0, 0.0
        while self._aw_cum_t + step <= t:
            mid = self._aw_cum_t + 0.5 * step
            self._aw_cum += step / max(piecewise(self.data["awareness"], mid, "t", "level"), AWARE_FLOOR)
            self._aw_cum_t += step
        return self._aw_cum + (t - self._aw_cum_t) / max(piecewise(self.data["awareness"], t, "t", "level"), AWARE_FLOOR)

    def _aw_cost_at(self, t1):
        """The clock's reading at a thought's end, worked out once per thought."""
        if t1 not in self._aw_cost1:
            step = 1.0 / self.fps
            n = int(t1 / step)
            cost = sum(step / max(piecewise(self.data["awareness"], (k + 0.5) * step, "t", "level"), AWARE_FLOOR) for k in range(n))
            cost += (t1 - n * step) / max(piecewise(self.data["awareness"], t1, "t", "level"), AWARE_FLOOR)
            self._aw_cost1[t1] = cost
        return self._aw_cost1[t1]

    def _thoughts(self, t):
        """The conscious attention on each region from memory this frame: the timeline's thoughts, each
        naming the regions it holds, rising from t0 over its own rise (THINK_RISE where it names none), standing to t1 and
        fading from there
        over its own fade on the awareness clock (_aw_cost); the strongest wins a region. Apart from in_mind,
        which is what the mind knows whether or not it thinks of it (the plates model's held state, the
        unconscious fill to come)."""
        out = {tag: 0.0 for tag in self.regions}
        # and the tags a thought names beyond the room's surfaces ("body": his own body, region 9 of the model), which
        # fell through this table until rung 2p (the alarm's thought never lit the body's known shapes)
        for th in self.thoughts:
            for tag in th["regions"]:
                out.setdefault(tag, 0.0)
        self._colour_now = {}
        cost_now = None
        for th in self.thoughts:
            t0 = float(th["t0"])
            t1 = float(th.get("t1", t0))
            if t < t0:
                continue
            if th.get("rise") is None:
                level = anim.smoothstep((t - t0) / THINK_RISE) if THINK_RISE > 0 else 1.0
            else:
                level = THINK_FAINT ** (1.0 - min(1.0, (t - t0) / max(float(th["rise"]), 1e-6)))
            if t > t1:
                if cost_now is None:
                    cost_now = self._aw_cost(t)
                level *= math.exp(-(cost_now - self._aw_cost_at(t1)) / max(float(th.get("fade", 1.0)), 1e-3))
            level *= float(th.get("level", 1.0))
            # the colour arrives COLOUR_DELAY after the thought begins, while the thought lasts: an earlier thought of the
            # same thing, long faded, lends it no colour
            colour = anim.smoothstep((t - t0 - COLOUR_DELAY) / COLOUR_RISE) if level > 1e-4 else 0.0
            for tag in th["regions"]:
                if tag in out and level > out[tag]:
                    out[tag] = level
                if colour > self._colour_now.get(tag, 0.0):
                    self._colour_now[tag] = colour
        return out

    # ---- the frame ----
    def frame_state(self, frame):
        t = anim.time_of(frame, self.fps)
        fs = FrameState(frame, t)
        st = self.reader.state(frame)
        J, head = st["joints"], st["head"]
        fs.awareness = piecewise(self.data["awareness"], t, "t", "level")
        aw = fs.awareness

        # The model's frame: centred on the head, forward where the head faces, up along the torso.
        # The room turns with the gaze and stays level when he nods or bends, and the simulated
        # body stands upright in the skull with its head tilted as his is (his note of
        # 2026-11-07; rung 1 used the head's full frame, which laid the body back whenever he
        # looked down). The head's own frame still casts the rays and carries the ears.
        torso_up = (J["neck"] - J["pelvis"]).normalized()
        fwd = head["fwd"] - torso_up * head["fwd"].dot(torso_up)
        if fwd.length < 0.05:
            fwd = head["up"] - torso_up * head["up"].dot(torso_up)
        R = anim.frame_from_axes(fwd, torso_up).to_3x3()   # columns forward, left, up
        Rt = R.transposed().to_4x4()
        # the scale is last frame's zoom, decided below from what he attends to this frame
        mscale = self.scale
        M = Matrix.Translation(HEAD_CENTRE) @ Matrix.Scale(mscale, 4) @ Rt @ Matrix.Translation(-head["loc"])
        fs.M = M
        fs.scale = mscale

        def gm(p):
            return M @ Vector(p)

        # ---- memory: what is in mind, and what he thinks of ----
        self._apply_memory(t)
        fs.thought = self._thoughts(t)
        fs.thought_colour = dict(self._colour_now)

        # ---- sense events now ----
        active = []
        for ev in self.events:
            kind = ev["kind"]
            if kind == "comet":
                chain = tags.CHAINS[tags.PART_CHAIN[ev["part"]]]
                length = sum((J[a] - J[b]).length for a, b in zip(chain, chain[1:]))
                ev["life"] = length / ev.get("speed", COMET_SPEED) + 0.35
                ev["_length"] = length
            a = self.envelope(ev, t)
            if a > 1e-4:
                active.append((ev, a))

        # ---- claims under the budget ----
        claims = {ev["id"]: a for ev, a in active}
        will_glow_raw = self._glow(t)
        claims["_glow"] = will_glow_raw * 0.5
        for rec in self.recognition:
            dt = t - rec["t"]
            if 0.0 <= dt < 1.4:
                claims[f"_rec_{rec['t']}"] = 0.6 * (anim.smoothstep(dt / 0.1) * (1.0 - anim.smoothstep((dt - 0.3) / 1.1)))
        total = sum(claims.values())
        ceiling = self.budget["ceiling"]
        scale = {k: 1.0 for k in claims}
        if total > ceiling and claims:
            top = max(claims, key=claims.get)
            top_a = min(claims[top], ceiling)
            rest = total - claims[top]
            s = (ceiling - top_a) / rest if rest > 1e-6 else 0.0
            for k in claims:
                scale[k] = s if k != top else top_a / claims[top]
            fs.budget_scale = s
        scaled = {k: claims[k] * scale[k] for k in claims}
        # which sense holds his attention: the strongest claim among the sense events (the edge
        # tint of the First-Person view reads it; the will and recognition are not senses)
        leader = None
        leader_ev = None
        for ev, a in active:
            s_a = scaled.get(ev["id"], 0.0)
            if leader is None or s_a > leader[1]:
                leader = (ev["sense"], s_a)
                leader_ev = ev
        fs.attention_leader = leader if leader is not None else ("none", 0.0)

        # ---- the held floor and base ----
        floor_a = self.budget["held_floor"]
        base_a = self.budget["held_base"]
        held_level = floor_a + (base_a - floor_a) * fs.budget_scale
        held_level *= aw

        sensed_region = {}     # tag -> (att, colour, sense)
        sensed_part = {}       # part -> (att, colour, sense)

        def sense_region(tag, att, sense):
            if att <= 1e-4:
                return
            cur = sensed_region.get(tag)
            if cur is None or att > cur[0]:
                sensed_region[tag] = (att, tags.SENSE_COLOUR[sense], sense)

        def sense_part(part, att, sense):
            if att <= 1e-4:
                return
            cur = sensed_part.get(part)
            if cur is None or att > cur[0]:
                sensed_part[part] = (att, tags.SENSE_COLOUR[sense], sense)

        # ---- sight: the fan of rays ----
        rays = [(Vector((0, 0, 0)), Vector((0, 0, 0)), 0.0)] * RAY_COUNT
        sight_ev = None
        for ev, a in active:
            if ev["kind"] == "rays":
                sight_ev = (ev, scaled[ev["id"]])
        sun_dir = st["sun_dir"]
        # the sun's disc as his eyes have it, its radius the scene's own (the sky's sun size). Five rays, its centre and
        # four limbs out across its OWN line, each followed SUN_CAST metres: sun_clear, the rays nothing stands on at
        # all (the eyes' rays reach the disc). SUN_UP_RAYS rays spread over the disc, each started SUN_NEAR out: sun_far,
        # the rays clear of everything beyond SUN_NEAR (the share of the disc up over the land). Until 2026-11-16 the
        # rays stopped at the reader's 200 m, short of the stand-in range at 300 m, and their limbs were laid along the
        # eyes' axes: the range never hid the sun, the engine took it as seen from the second it stood over the level,
        # 18 s of the scene before first light, and the glare's red fired on his eyes in the doze (his word of that
        # day: the sun does not come into his mind before it hits him in the eyes)
        sun_clear, sun_far = [False] * 5, [False] * 5
        if sun_dir.z > 0.0:
            up_s = Vector((0.0, 0.0, 1.0)) - sun_dir * sun_dir.z
            up_s = up_s.normalized() if up_s.length > 1e-6 else Vector((1.0, 0.0, 0.0))
            left_s = up_s.cross(sun_dir).normalized()
            r_s = math.tan(math.radians(st.get("sun_radius", SUN_LIMB_DEG)))
            disc = [(sun_dir + off).normalized() for off in (Vector((0.0, 0.0, 0.0)), up_s * r_s, -up_s * r_s, left_s * r_s, -left_s * r_s)]
            sun_clear = [not self.reader.cast(head["eye"], ray, distance=SUN_CAST)["hit"] for ray in disc]
            flower = [(sun_dir + (left_s * a + up_s * b) * r_s).normalized() for a, b in SUN_FLOWER]
            sun_far = [not self.reader.cast(head["eye"] + ray * SUN_NEAR, ray, distance=SUN_CAST)["hit"] for ray in flower]
        fs.sun_up = sum(sun_far) / float(len(sun_far))
        sun_seen_now = False
        far_sum, all_sum, body_sum = 0.0, 0.0, 0.0     # how much of sight's attention lands beyond the window; his own body is an occluder, not a thing attended
        reach = []                                      # (distance from the head's centre, attention) of every ray's landing, his body left out
        if sight_ev is not None:
            ev, a = sight_ev
            spread = math.radians(ev.get("spread_deg", 14))
            eye = head["eye"]
            # along the eyes' own look (the head's frame turned by the eyes, body.Motion._eyes)
            fwd, left, up = head.get("eye_fwd", head["fwd"]), head.get("eye_left", head["left"]), head.get("eye_up", head["up"])
            if ev.get("target"):
                # a narrow gaze on a thing: the fan's axis runs from the eye to it, not along the head
                tgt = self._source(ev["target"], st)
                fwd = (tgt - eye).normalized()
                left = (head["up"].cross(fwd)).normalized()
                up = fwd.cross(left).normalized()
            rays = []
            k = 0
            for i in range(RAY_ROWS):
                for j in range(RAY_COLS):
                    u = -1.0 + 2.0 * (j + 0.5) / RAY_COLS
                    v = -1.0 + 2.0 * (i + 0.5) / RAY_ROWS
                    d = (fwd + left * (-u * math.tan(spread)) + up * (v * math.tan(spread) * 0.55)).normalized()
                    w = 1.0 - 0.55 * math.sqrt(u * u + v * v) / math.sqrt(2.0)
                    hit = self.reader.cast(eye, d)
                    ray_att = a * w
                    all_sum += ray_att
                    if hit["hit"]:
                        end_room = hit["location"]
                        tag = hit["tag"]
                        if hit["through_window"]:
                            sense_region("window", ray_att * 0.9, "sight")
                        if hit["kind"] == "surface":
                            sense_region(tag, ray_att, "sight")
                            reach.append(((Vector(end_room) - head["loc"]).length, ray_att))
                            if tag in FAR_TAGS:
                                far_sum += ray_att
                        elif hit["kind"] == "body":
                            sense_part(tag, ray_att, "sight")
                            body_sum += ray_att
                    else:
                        end_room = eye + d * 60.0
                        far_sum += ray_att
                        reach.append((SKY_DISTANCE, ray_att))   # a ray that meets nothing reaches the sky, for the zoom
                        sense_region("window", ray_att * 0.9, "sight")
                        if d.dot(sun_dir) > math.cos(math.radians(3.0)) and any(sun_clear):
                            sense_region("sun", ray_att, "sight")
                            sun_seen_now = True
                    a_g = gm(eye)
                    b_g, _ = to_glass(gm(end_room))
                    rays.append((a_g, b_g, ray_att))
                    k += 1
            # the sun is seen when it lies within the fan and nothing stands before it, by a ray cast
            # straight at it: the fan's 27 rays alone, each needing to pass within three degrees of it,
            # never found it at the window (2026-11-08)
            if not sun_seen_now and sun_dir.z > 0.0 and fwd.dot(sun_dir) > math.cos(spread):
                # the disc's upper limb counts: at the crest only the limb is clear of the ridge
                if sun_clear[1] or sun_clear[0]:
                    sense_region("sun", a * 0.7, "sight")
                    sun_seen_now = True
        fs.rays = rays
        fs.sight_att = sight_ev[1] if sight_ev is not None else 0.0
        # whether the eyes' rays reach the sun's disc, whatever the senses make of the sun: five rays, the centre
        # and four limbs, the glass passed, from within the field of both eyes. The model draws the sun's seen
        # half by this and nothing else (his eighth review of 2026-11-10: the ball had stood lit by the warmth on
        # his face while his hand hid the disc, and blinked off with every blink). Any of the disc reached is the
        # sun seen, at its own strength: a sliver of it over a ridge dazzles as the whole does (by the share of the
        # five rays until 2026-11-16: with the range counted, the sun newly over it stood in his head as a ghost at
        # a fifth of its light until its centre cleared, twenty seconds on)
        fs.sun_sight = 0.0
        if sun_dir.z > 0.0:
            up_h, left_h, fwd_h = head.get("eye_up", head["up"]), head.get("eye_left", head["left"]), head.get("eye_fwd", head["fwd"])
            elev = math.degrees(math.asin(clamp(sun_dir.dot(up_h), -1.0, 1.0)))
            flat = sun_dir - up_h * sun_dir.dot(up_h)
            azim = math.degrees(math.acos(clamp(flat.normalized().dot(fwd_h), -1.0, 1.0))) if flat.length > 1e-6 else 0.0
            if azim <= FIELD_H / 2.0 and abs(elev) <= FIELD_V / 2.0:
                fs.sun_sight = 1.0 if any(sun_clear) else 0.0
        fs.eye_room = Vector(head["eye"])
        fs.head_rot = head["rot"].copy()
        if sun_seen_now:
            self.sun_seen_ever = True
            self.regions["sun"].seen_ever = True

        # ---- hearing: the rings of a sound (rung 2p, his specification of 2026-11-12) ----
        # One ring every RING_EVERY seconds while a sound lasts, each as bright as the sound is loud in that interval
        # (loudness: the peak of the sound's stand-in waveform, triview/sound.py, until rung 6 brings the sound files;
        # the same waveforms are the stand-in soundtrack), travelling from the sound's judged
        # place to the nearer ear in WAVE_TRAVEL seconds and on past the farther, then gone over RING_FADE. An ear a ring
        # crosses lights green for the moment of the crossing (fs.sense_light, below), and red, fading, when the sound is
        # louder than LOUD: a pain persists a short while
        waves = []
        wave_cols = []
        wave_room = []
        discs = []
        ears = {"ear_l": head["ear_l"], "ear_r": head["ear_r"]}
        ear_hit = {"ear_l": 0.0, "ear_r": 0.0}
        ear_hurt = {"ear_l": 0.0, "ear_r": 0.0}
        dt = 1.0 / self.fps
        for ev, a in active:
            if ev["kind"] != "wave":
                continue
            a = scaled[ev["id"]]
            src = self._source(ev["source"], st)
            # the sound's judged place: where the mind believes its source to be, by the rule for every point (believed:
            # as it is within the reach, compressed in order beyond it). The model places it as it places a hit of the
            # eyes' picture (triview/lidarscene.py bake: flat until the far field resolves, pressed beyond the knee), so
            # a far sound's rings start at the thing it comes from. (Until the audit of 2026-11-15 a source beyond a
            # literal 6 m was drawn 6 m from the head: a bird on the ridge rang from the air over the bushes.)
            to_src = src - head["eye"]
            d_src = to_src.length
            d_judged = believed(d_src)
            centre_room = head["eye"] + to_src * (d_judged / d_src) if d_src > 1e-6 else Vector(src)
            d_ear = {k: (centre_room - p).length for k, p in ears.items()}
            d_near, d_far = min(d_ear.values()), max(d_ear.values())
            speed = max(d_near, 0.05) / WAVE_TRAVEL
            t0, t1 = ev["t0"], ev["t1"]
            n = int((min(t, t1) - t0) / RING_EVERY) + 1
            for i in range(n):
                tl = t0 + i * RING_EVERY
                if tl > t1 or tl > t:
                    continue
                loud = sound.loudness(ev, tl, RING_EVERY)
                if loud <= 1e-3:
                    continue
                tau = t - tl
                r_room = speed * tau + 0.02
                r_prev = speed * (tau - dt) + 0.02
                over = (r_room - d_far - 0.02) / speed
                if over > RING_FADE:
                    continue
                fade = 1.0 if over <= 0.0 else 1.0 - over / RING_FADE
                c_g, _ = to_glass(gm(centre_room))
                # the ring's brightness: its loudness, dimmed as the sound is less attended, and as far as he is aware (his
                # word of 2026-11-12: the rings' brightness is awareness); the fourth entry is that gate
                waves.append((c_g, r_room * mscale, loud, (0.5 + 0.5 * a) * fade * aw))
                # for the model's own placing: the source in the room, the ring's radius in judged room metres, and the
                # judged distance from the eyes that radius is measured against
                wave_room.append((tuple(src), r_room, d_judged))
                wave_cols.append(self.sound_shade.get(ev["source"], tags.SENSE_COLOUR["hearing"]))
                for k, d in d_ear.items():
                    if r_prev < d <= r_room:
                        ear_hit[k] = max(ear_hit[k], loud * a)
                        if loud > LOUD:
                            hurt = a * clamp(0.5 + (loud - LOUD) / (1.0 - LOUD))
                            if hurt > ear_hurt[k]:
                                ear_hurt[k] = hurt
                                self.hurt_from = centre_room
            # the disc at the judged source: on the model's surface there, or at the glass when none
            d_room = 0.10 + 0.55 * ev.get("doubt", 0.1)
            c_g, clamped = to_glass(gm(src))
            discs.append((c_g, d_room * mscale, a))
        waves = waves[:WAVE_SLOTS]
        wave_cols = wave_cols[:WAVE_SLOTS]
        wave_room = wave_room[:WAVE_SLOTS]
        while len(waves) < WAVE_SLOTS:
            waves.append((HEAD_CENTRE, 0.0, 0.0, 0.0))
            wave_cols.append(tags.SENSE_COLOUR["hearing"])
            wave_room.append(None)
        fs.wave_colours = wave_cols
        fs.wave_room = wave_room
        discs = discs[:DISC_SLOTS]
        while len(discs) < DISC_SLOTS:
            discs.append((HEAD_CENTRE, 0.0, 0.0))
        fs.waves, fs.discs = waves, discs
        for k in ears:
            self.ear_lit[k] = max(ear_hit[k], self.ear_lit[k] * math.exp(-dt / EAR_CROSS))
            faded = self.ear_pain[k] * math.exp(-dt / PAIN_FADE)
            if ear_hurt[k] > faded and faded < 0.05:
                self.ear_hurt_t[k] = t          # a new hurt (a ring after quiet): its throb begins at a beat's top
            self.ear_pain[k] = max(ear_hurt[k], faded)

        # ---- comets, rivers, fields, throb on the simulated body ----
        pulses = {c: [] for c in tags.CHAINS}
        rivers = {}
        fields = {}
        for ev, a in active:
            kind = ev["kind"]
            a = scaled[ev["id"]]
            sense = ev["sense"]
            if kind == "comet":
                chain_name = tags.PART_CHAIN[ev["part"]]
                chain = tags.CHAINS[chain_name]
                tau = t - ev["t"]
                speed = ev.get("speed", COMET_SPEED)
                dist = speed * tau
                length = ev["_length"]
                pos_room, on_path = self._along(J, chain, dist)
                flash = 0.0
                if dist >= length:
                    flash = max(0.0, 1.0 - (dist - length) / (speed * 0.2))
                if len(pulses[chain_name]) < PULSES_PER_CHAIN:
                    pulses[chain_name].append((gm(pos_room), a if on_path else 0.0, tags.SENSE_COLOUR[sense], a * flash))
                # the thread under the pulse, and the part and the place it came from
                if on_path:
                    cur = rivers.get(chain_name)
                    if cur is None or a * 0.5 > cur[2]:
                        rivers[chain_name] = (tags.SENSE_COLOUR[sense], 0.35, a * 0.5)
                if sense == "pain":
                    pass
                else:
                    sense_part(ev["part"], a, sense)
                if "place" in ev:
                    sense_region(ev["place"], a, sense)
                    if ev["place"] == "rug_edge":
                        self.rug_curled = True
                        self.regions["rug_edge"].finish = 0.0
            elif kind == "river":
                chains = list(tags.CHAINS) if ev.get("chain") == "all" else [ev["chain"]]
                for cn in chains:
                    cur = rivers.get(cn)
                    if cur is None or a > cur[2]:
                        rivers[cn] = (tags.SENSE_COLOUR[sense], ev.get("strength", 0.5), a)
                    if sense == "proprioception":
                        for j in tags.CHAINS[cn]:
                            for p, spec in tags.PARTS.items():
                                if j in spec["joints"]:
                                    sense_part(p, a * 0.8, sense)
                if "part" in ev:
                    sense_part(ev["part"], a, sense)
                if "place" in ev:
                    sense_region(ev["place"], a, sense)
            elif kind == "field":
                parts = ev.get("parts", [])
                if "sweep" in ev:
                    u = clamp((t - ev["t0"]) / (ev["t1"] - ev["t0"]))
                    idx = min(len(parts) - 1, int(u * len(parts)))
                    parts_now = parts[max(0, idx - 1): idx + 1]
                else:
                    parts_now = parts
                for p in parts_now:
                    slot = p + ("_edge" if ev.get("offset") == "edge" else "")
                    cur = fields.get(slot)
                    if cur is None or a > cur[3]:
                        fields[slot] = (p, tags.SENSE_COLOUR[sense], ev.get("strength", 0.5), a)
                    sense_part(p, a, sense)
                if "place" in ev:
                    sense_region(ev["place"], a, sense)
            elif kind == "throb":
                phase = 0.5 + 0.5 * math.sin(2 * math.pi * ev.get("rate_hz", 1.5) * (t - ev["t0"]))
                pos = J[tags.PART_POINT[ev["part"]]]
                fs.throb = (gm(pos), 1.0 + 0.5 * phase, a * (0.55 + 0.45 * phase))
                fs.throb_pulse = 0.55 + 0.45 * phase
                sense_part(ev["part"], a * 0.6, sense)
            elif kind == "breath":
                rate = ev.get("rate_hz", 0.2)
                if rate <= 0.0:
                    held = ev.get("held_until", ev["t1"])
                    if t < held:
                        ph = anim.smoothstep((t - ev["t0"]) / 0.6)
                    else:
                        ph = 1.0 - anim.smoothstep((t - held) / 1.0)
                else:
                    ph = 0.5 - 0.5 * math.cos(2 * math.pi * rate * (t - ev["t0"]))
                fs.breath = (1.0 + 0.9 * ev.get("depth", 0.7) * ph, a)
                sense_part("chest", a * 0.5, "breath")
            elif kind == "heart":
                rate = ev.get("rate_hz", 1.2)
                ph = ((t - ev["t0"]) * rate) % 1.0
                beat = math.exp(-(ph / 0.16) ** 2) + 0.35 * math.exp(-((ph - 0.3) / 0.12) ** 2)
                fs.heart = (0.7 + 0.8 * beat, a * (0.4 + 0.6 * beat))
            elif kind == "plumb":
                pass
        # the pain comet's origin stays sensed, dim, by the throb
        fs.pulses = pulses
        fs.rivers = rivers
        for slot, (p, col, spread, a) in fields.items():
            pos = self._part_centre(J, p, head)
            if slot.endswith("_edge"):
                pos = pos + head["left"] * 0.09 - head["fwd"] * 0.02
            elif p == "head":
                pos = pos + head["fwd"] * 0.075
            fs.fields[slot] = (gm(pos), col, spread, a)

        # ---- balance: the gravity arrow ----
        # His review of 2026-11-07: an arrow from the inner ear to where the ear says down is, dim
        # while down holds still in his head and bright when it moves: sitting up, standing, the
        # trip, the turns. Its attention comes from the motion itself, with the timeline's own
        # balance events on top of it.
        plumb_a = 0.0
        swing = 1.0
        for ev, a in active:
            if ev["kind"] == "plumb":
                plumb_a = max(plumb_a, scaled[ev["id"]])
                swing = max(swing, ev.get("swing", 1.0) * 1.0)
        hp = head["loc"]
        dt = 1.0 / self.fps
        if self.prev_head is not None:
            v = (hp - self.prev_head) / dt
            acc = (v - self.prev_head_v) / dt if self.prev_head_v is not None else Vector((0, 0, 0))
            self.prev_head_v = v
        else:
            acc = Vector((0, 0, 0))
        self.prev_head = hp
        # a damped pendulum driven by the head's acceleration, settling to gravity
        target = (Vector((0, 0, -9.81)) - acc * (0.6 * swing)).normalized()
        self.plumb_vel += (target - self.plumb_dir) * 55.0 * dt - self.plumb_vel * 9.0 * dt
        self.plumb_dir = (self.plumb_dir + self.plumb_vel * dt).normalized()
        # how fast "down" moves in the head's own frame: the inner ear's signal
        pd_head = head["rot"].transposed() @ self.plumb_dir
        if self.prev_pd_head is not None:
            rate = math.degrees(pd_head.angle(self.prev_pd_head, 0.0)) / dt
            a_motion = clamp(rate / 150.0)
        else:
            a_motion = 0.0
        self.prev_pd_head = pd_head
        self.plumb_a_s = max(a_motion, self.plumb_a_s * math.exp(-dt / 0.6))
        plumb_a = max(plumb_a, self.plumb_a_s * aw, 0.10 * aw)
        ear_room = head["loc"] - head["left"] * 0.085
        a_g = gm(ear_room)
        dir_g = (M.to_3x3() @ self.plumb_dir).normalized()
        fs.plumb = (a_g, a_g + dir_g * PLUMB_LEN, plumb_a)

        # ---- warmth rays and the sun ----
        warmth = []
        for ev, a in active:
            if ev["kind"] == "field" and ev.get("ray_to") == "sun":
                a = scaled[ev["id"]]
                for p in ev.get("parts", [])[:WARMTH_SLOTS]:
                    origin = self._part_centre(J, p, head)
                    if p == "head":
                        origin = origin + head["fwd"] * 0.09
                    end_room = origin + sun_dir * 60.0
                    warmth.append((gm(origin), to_glass(gm(end_room))[0], a))
        warmth = warmth[:WARMTH_SLOTS]
        while len(warmth) < WARMTH_SLOTS:
            warmth.append((HEAD_CENTRE, HEAD_CENTRE, 0.0))
        fs.warmth = warmth
        # the sun's warmth on his face senses the sun as surely as sight does: at the crest his raised
        # hand hides the disc from the eyes while the light plainly reaches him (found 2026-11-08)
        if sun_dir.z > 0.0:
            for ev, a in active:
                if ev["kind"] == "field" and ev.get("ray_to") == "sun" and "head" in ev.get("parts", []):
                    sense_region("sun", scaled[ev["id"]] * 0.7, "temperature")
                    self.sun_seen_ever = True
                    self.regions["sun"].seen_ever = True
        # a sense on a thing other than sight holds the thing in mind, as a thought does (his eighth review of
        # 2026-11-10: the warmth on his face keeps the sun behind his hand): the model lights the sun's memory by it
        felt = sensed_region.get("sun")
        fs.sun_felt = min(1.0, float(felt[0])) if (felt is not None and felt[2] != "sight") else 0.0
        sun_region = self.regions["sun"]
        sun_pos = to_glass(gm(head["eye"] + sun_dir * 60.0))[0]
        if sun_region.seen_ever and sun_region.in_mind > 0:
            if "sun" in sensed_region:
                fs.sun = (sun_pos, sensed_region["sun"][0], tags.SENSE_COLOUR["sight"])
            else:
                fs.sun = (sun_pos, held_level * sun_region.in_mind * 1.2, GREY)
        else:
            fs.sun = (sun_pos, 0.0, GREY)

        # ---- the senses on the simulated body (rung 2p, his specification of 2026-11-12) ----
        # Every sense lights the part it arises on, on the mind's own body, whether or not the eyes see it; the senses
        # may overlap. A sense light on a part (fs.sense_light: its colour, its strength, how far the colour replaces
        # the part's own): touch in magenta at the touch's intensity, blended toward red by the share of pain and
        # toward gold by the share of pleasure; the ear a ring crosses, green, or red when the sound hurts; the eyes red
        # as the sun's glare hits them; the heart and the lungs in their own colours while thought of
        light = {}
        touch_i, touch_p, touch_q = {}, {}, {}

        def more(d, p, v):
            if v > d.get(p, 0.0):
                d[p] = v

        for ev, a in active:
            a = scaled[ev["id"]]
            s_ev = float(ev.get("strength", 0.5))
            sense, kind = ev["sense"], ev["kind"]
            if kind in ("comet", "throb"):
                parts_now = [ev["part"]]
            elif kind == "river":
                parts_now = [ev["part"]] if "part" in ev else []
            elif kind == "field":
                parts_now = list(ev.get("parts", []))
                if "sweep" in ev:
                    u = clamp((t - ev["t0"]) / (ev["t1"] - ev["t0"]))
                    idx = min(len(parts_now) - 1, int(u * len(parts_now)))
                    parts_now = parts_now[max(0, idx - 1): idx + 1]
            else:
                continue
            for p in parts_now:
                if sense == "touch":
                    more(touch_i, p, a * s_ev)
                elif sense == "pain":
                    # a pain throbs from its own onset (pain_beat); its level is the attention times the event's strength,
                    # as a touch's and a pleasure's are (until the audit of 2026-11-15 the strength was left out)
                    more(touch_p, p, a * s_ev * pain_beat(t - float(ev.get("t0", ev.get("t", t)))))
                elif sense == "pleasure":
                    more(touch_q, p, a * s_ev)
        # touch is contact: the model lights the patch of a part's surface that meets another thing's (triview/lidarscene.py
        # contact_nodes), at the part's touch level: the timeline's touch on the part where it names one, else TOUCH_REST,
        # the level of a resting contact, as far as he is aware.
        # A pain or a pleasure lights the whole of its part for as long as it lasts, whatever the part touches meanwhile;
        # a touch on that part shows on its own patch, in touch's colour, beside it (his word of 2026-11-16: an unhurt
        # part cannot look like a hurt one). (Until then a pain on a part the timeline also touched was folded into that
        # touch: the touched patch alone, magenta blended toward red by the pain's share, and the rest of the part left
        # alone. A hand that hurt for the whole piece looked like the unhurt hand each time it rested on a thing, and
        # went red again each time it let go.)
        for p in tags.PARTS:
            i_, p_, q_ = touch_i.get(p, 0.0), touch_p.get(p, 0.0), touch_q.get(p, 0.0)
            rest = TOUCH_REST * aw
            if max(i_, rest) > 1e-3:
                fs.touch[p] = (tags.SENSE_COLOUR["touch"], max(i_, rest))
            if p_ + q_ > 1e-3:
                col = Vector(tags.SENSE_COLOUR["pain"]).lerp(Vector(tags.SENSE_COLOUR["pleasure"]), q_ / (p_ + q_))
                light[p] = (tuple(col), max(p_, q_), SENSE_MIX)
        for k in ears:
            g, r = self.ear_lit[k], self.ear_pain[k] * pain_beat(t - self.ear_hurt_t[k])
            if max(g, r) > 1e-3:
                # green for a ring's crossing; red alone while a loud sound's hurt lasts (his word of 2026-11-12: a mix read yellow)
                col = tags.SENSE_COLOUR["pain"] if r > 1e-3 else tags.SENSE_COLOUR["hearing"]
                light[k] = (col, max(g, r), 1.0)
        # the sun's glare: as the disc comes to the eyes near the line of sight (within GLARE_ANGLE of it, any of it
        # uncovered by the hand or the ridge) the smart rises by GLARE, and fades over PAIN_FADE; a steady smart of
        # GLARE_HOLD while it stays there. The lids dim what shows, and a blink restarts nothing
        cover_now = float(self.cover_of(t)) if self.cover_of is not None else 0.0
        gaze_deg = math.degrees(math.acos(clamp(head.get("eye_fwd", head["fwd"]).dot(sun_dir), -1.0, 1.0)))
        central = 1.0 - anim.smoothstep((gaze_deg - GLARE_ANGLE[0]) / (GLARE_ANGLE[1] - GLARE_ANGLE[0]))
        hit = fs.sun_sight * central
        onset = max(0.0, hit - self.prev_sun_hit)
        self.prev_sun_hit = hit
        faded_eye = self.eye_pain * math.exp(-dt / PAIN_FADE)
        if onset * GLARE > 0.05 and faded_eye < 0.05:
            self.eye_hurt_t = t
        self.eye_pain = min(1.0, faded_eye + onset * GLARE)
        eye_level = max(self.eye_pain * pain_beat(t - self.eye_hurt_t), GLARE_HOLD * hit) * (1.0 - cover_now) * aw
        if eye_level > 1e-3:
            for k in ("eye_l", "eye_r"):
                light[k] = (tags.SENSE_COLOUR["pain"], eye_level, 1.0)
        # the heart and the lungs while thought of (the timeline's breath and heartbeat events), in their own colours,
        # the heart's light pulsing with its beat; their scales, and the torso's gentle scale with the lungs
        b_scale, b_att = fs.breath
        h_scale, h_att = fs.heart
        breath_ph = clamp((b_scale - 1.0) / 0.9) if b_att > 1e-4 else 0.0
        beat = clamp((h_scale - 0.7) / 0.8) if h_att > 1e-4 else 0.0
        fs.organs = {"heart": 1.0 + HEART_SWELL * beat, "lung": 1.0 + LUNG_SWELL * breath_ph, "torso": 1.0 + TORSO_BREATH * breath_ph,
                     "clear": clamp(max(b_att, h_att) / ORGAN_CLEAR_AT) * aw}   # the chest clears so the organs inside show while thought of
        if b_att > 1e-3:
            for k in ("lung_l", "lung_r"):
                light[k] = (tags.PART_COLOUR[k], b_att * aw, ORGAN_MIX)
        if h_att > 1e-3:
            light["heart"] = (tags.PART_COLOUR["heart"], h_att * aw, ORGAN_MIX)
        fs.sense_light = light
        # the outline glow at a part's rim: proprioception, a part's own motion (its joints' speed) times how willed
        # the motion is (the timeline's proprioception and effort events on it, or a word of will just said), faint
        # at most; warmth in orange and the window's cold air in blue where they reach a part. One glow per part,
        # its colour the senses' mixed by their strengths
        speeds = {}
        if self.prev_J is not None:
            for part, spec in tags.PARTS.items():
                js = [j for j in spec["joints"] + spec["bones"] if j in J and j in self.prev_J]
                if js:
                    speeds[part] = sum((J[j] - self.prev_J[j]).length for j in js) / len(js) / dt
        self.prev_J = {k: Vector(v) for k, v in J.items()}
        willful = {}
        for ev, a in active:
            a = scaled[ev["id"]]
            if ev["sense"] == "proprioception" and ev["kind"] == "river":
                chains = list(tags.CHAINS) if ev.get("chain") == "all" else [ev["chain"]]
                for cn in chains:
                    for j in tags.CHAINS[cn]:
                        for p, spec in tags.PARTS.items():
                            if j in spec["joints"]:
                                more(willful, p, a)
            elif ev["sense"] == "effort" and ev["kind"] == "field":
                for p in ev.get("parts", []):
                    more(willful, p, a * float(ev.get("strength", 0.5)))
        w_word = max((1.0 - anim.smoothstep((t - w["t"] - 0.3) / 1.2) for w in self.will if 0.0 <= t - w["t"] < 1.5), default=0.0)
        glow, warm, cool = {}, {}, {}
        for p, v in speeds.items():
            if p == "head":
                # no band on the head (his word of 2026-11-13, eleventh round): the mind's model is centred on the head, so
                # its own motion shows as the room's motion and as the gravity arrow. A band round it, in a mint close to the
                # ears' green, stood where a sound's rings reach the ears and read as the whole head lit by the sound
                continue
            w = max(willful.get(p, 0.0), w_word)
            g = clamp(v / PROP_SPEED) * (PROP_FLOOR + (1.0 - PROP_FLOOR) * w) * PROP_MAX * aw
            if g > 1e-3:
                glow[p] = g
        for ev, a in active:
            if ev["kind"] != "field":
                continue
            a = scaled[ev["id"]] * float(ev.get("strength", 0.5))
            if ev["sense"] == "temperature":
                for p in ev.get("parts", []):
                    more(warm, p, a)
            elif ev["sense"] == "airflow":
                for p in ev.get("parts", []):
                    more(cool, p, a)
        # the sun's warmth at rest, on every part: the model draws it on the skin the rays reach (ContactBody's sun)
        sun_el = math.degrees(math.asin(clamp(sun_dir.z, -1.0, 1.0)))
        # (the share of the disc clear of the land as his eyes have it, read off the scene above: by the range's nominal
        # height until 2026-11-16, which the range's near shoulder overtops by a sixth of a degree)
        sun_up = fs.sun_up
        rest_w = WARM_REST * aw * sun_up
        if rest_w > 1e-3:
            for p in tags.PARTS:
                more(warm, p, rest_w)
        # the outline is proprioception's alone (his word of 2026-11-13: warmth works as touch does, on the outside, where
        # it affects). Warmth and the window's cold air are levels per part; the model draws each as a glow on the skin
        # the sun's rays and the air reach (triview/lidarscene.py: ContactBody's sun and air)
        fs.outline = {p: (tuple(tags.SENSE_COLOUR["proprioception"]), g) for p, g in glow.items()}
        fs.temperature = {p: (warm.get(p, 0.0), cool.get(p, 0.0)) for p in set(warm) | set(cool)}
        # the touch's signal: a spark from the touched part up the middle of its limb, joint by joint to the neck, and
        # on to the nearest point of the skull (his word of 2026-11-13; straight through the air to just outside the head
        # until then). It acts as lightning does (the same day's words: as fast as lightning, for a new movement alone,
        # no lasting spark; then, his tenth round: one spark from the point of contact to the head, gone at once, with a
        # gap to see between two touches): it runs its path once by LIGHTNING_REACH, a frame a step, and is gone. One
        # per new contact read off the body (self.strikes) and per touch or pain impact of the timeline (its comet
        # events). fs.lightning: the path's points in the model (LIGHTNING_KNOTS of them, the last repeated), how far
        # along it the spark's front has come, its strength, its colour, and the frame it began at (its zigzag's seed:
        # one shape for its whole life)
        bolts = []
        spark_part = {}
        head_c = head["loc"]
        skull_r = HEAD_RADIUS * HEAD_SCALE[2]
        life = len(LIGHTNING_REACH) * LIGHTNING_HOLD / self.fps

        def strike(part, t0, a, place=None, along=None):
            """One spark from a part, begun at t0 at the strength a: on its way, or over. Its strength is the most its
            event has had since it began: the attention's budget moves from frame to frame.
            It starts at the touched place (place: the point of the part's skin, in the room at t0), goes in to the
            nearest point of the part's own axis and runs along it to the end nearer the head, then joint by joint up
            the chain. Where the place is not known it starts on the axis: at `along` of its length where a touch
            shortly before left that (a pain's spark), else at its middle. No joint is named here: the axis and the
            chain are read off the figure's parts (tags.part_axis)."""
            tau = t - t0
            step = int(max(tau, 0.0) * self.fps + 1e-6) // LIGHTNING_HOLD
            if tau < -1e-6 or step >= len(LIGHTNING_REACH) or part not in tags.PART_CHAIN:
                return
            a = max(self._strike_peak.get((part, t0), 0.0), a)
            self._strike_peak[(part, t0)] = a
            if a <= 1e-4:
                return
            knots = self._strike_pose.get((part, t0, step))
            if knots is None:
                chain = tags.CHAINS[tags.PART_CHAIN[part]]
                far_j, near_j = tags.part_axis(part)
                a_pt, b_pt = Vector(J[far_j]), Vector(J[near_j])
                axis = b_pt - a_pt
                # where the touch lies on the part, read at the spark's first frame and carried with the part from there
                # (the body moves under a spark that stands for two poses): how far along the axis, and off it
                anchor = self._strike_anchor.get((part, t0))
                if anchor is None:
                    if place is not None:
                        c0 = Vector(place)
                        u = clamp((c0 - a_pt).dot(axis) / axis.length_squared) if axis.length_squared > 1e-12 else 0.0
                        anchor = (u, c0 - (a_pt + axis * u))
                    else:
                        anchor = (0.5 if along is None else float(along), None)
                    self._strike_anchor[(part, t0)] = anchor
                u, off = anchor
                on_axis = a_pt + axis * u
                pts = ([on_axis + off] if off is not None and off.length > 1e-4 else []) + [on_axis]
                pts += [Vector(J[n]) for n in chain[chain.index(near_j):-1]]
                pts = pts[:LIGHTNING_KNOTS - 1]
                to_last = pts[-1] - head_c
                pts.append(head_c + to_last.normalized() * min(skull_r, to_last.length) if to_last.length > 1e-6 else Vector(head_c))
                if sum((q - p).length for p, q in zip(pts, pts[1:])) < 0.02:
                    return
                knots = [gm(p) for p in pts]
                knots += [knots[-1]] * (LIGHTNING_KNOTS - len(knots))
                self._strike_pose[(part, t0, step)] = knots
            # its light by the touch's intensity, and the part it comes from flashes with it for as long (his words of
            # 2026-11-13, eleventh round: to show where the spark comes from)
            light = clamp(a / LIGHTNING_FULL) ** LIGHTNING_CURVE
            bolts.append((knots, LIGHTNING_REACH[step], light, LIGHTNING_COLOUR, float(int(round(t0 * self.fps)))))
            spark_part[part] = max(spark_part.get(part, 0.0), light)

        def impact(ev):
            """A named impact's intensity for its spark: its strength times the timeline's attention on it at its second.
            (The impact's own level rises over 0.12 s, longer than the spark lives, so the rise is left out; and the
            budget of the moment is left out, which squeezes a new impact as one claim among many in its first frames
            and halved the rap's spark.)"""
            return self._attention(ev, max(t, ev["t"])) * float(ev.get("strength", 0.5))

        # the timeline's impacts: a pain's strikes at its own second (no contact shows it); a touch's gives the strike
        # read off the contact nearest it on the same limb, within STRIKE_MATCH before or after, its strength, and
        # strikes at its own second where the reading has none near. (Until the tenth round only an impact already
        # begun gave its strength: the hands meet the sill a few frames before the timeline's second, and a spark two
        # frames long was over before its impact began.)
        named = {}
        for ev in self.events:
            if ev["kind"] != "comet" or ev["sense"] not in ("touch", "pain") or abs(t - ev["t"]) > STRIKE_MATCH + life + 1e-6:
                continue
            limb = tags.PART_CHAIN.get(ev["part"])
            near = [hit for hit in self.strikes if abs(hit[0] - ev["t"]) <= STRIKE_MATCH and tags.PART_CHAIN.get(hit[1]) == limb]
            if ev["sense"] == "pain" or not near:
                # no contact shows where: a touch on the same part within STRIKE_SOURCE before it gives the place along
                # the part (a pain comes from the knock that did the hurt), else the spark starts at the part's middle
                before = [k for k in self._strike_anchor if k[0] == ev["part"] and 0.0 <= ev["t"] - k[1] <= STRIKE_SOURCE]
                along = self._strike_anchor[max(before, key=lambda k: k[1])][0] if before else None
                strike(ev["part"], ev["t"], impact(ev), along=along)
            else:
                first = min(near, key=lambda hit: abs(hit[0] - ev["t"]))
                named[first] = max(named.get(first, 0.0), impact(ev))
        for hit in self.strikes:
            t0, part, speed, place = hit[:4]
            if t0 > t + 1e-6:
                break
            if t - t0 < life + 1e-6:
                x = clamp(speed / STRIKE_SPEED)
                own = aw * (STRIKE_SOFT + (STRIKE_HARD - STRIKE_SOFT) * x * x * (3.0 - 2.0 * x))
                strike(part, t0, max(named.get(hit, 0.0), own), place=place)
        bolts = bolts[:LIGHTNING_SLOTS]
        while len(bolts) < LIGHTNING_SLOTS:
            bolts.append(([HEAD_CENTRE] * LIGHTNING_KNOTS, 0.0, 0.0, GREY, 0.0))
        fs.spark_part = spark_part
        fs.lightning = bolts
        # the First-Person flash toward a pain: the strongest of a part's pain over FLASH_FROM (pulsing with the throb),
        # the sun's glare and a loud sound, with where it comes from
        flash, flash_dir = 0.0, None
        for p, v in touch_p.items():
            lvl = clamp((v - FLASH_FROM) / (1.0 - FLASH_FROM))     # v throbs already (pain_beat)
            if lvl > flash:
                flash, flash_dir = lvl, self._part_centre(J, p, head) - head["eye"]
        if eye_level > flash:
            flash, flash_dir = eye_level, Vector(sun_dir)
        ear_red = max(self.ear_pain[k] * pain_beat(t - self.ear_hurt_t[k]) for k in self.ear_pain)
        if ear_red > flash and self.hurt_from is not None:
            flash, flash_dir = ear_red, self.hurt_from - head["eye"]
        fs.flash = (flash, flash_dir)

        # ---- the ridge and the ground at the glass ----
        ridge_region = self.regions["ridge"]
        if ridge_region.in_mind > 0 and self.ridge_profile:
            pts = []
            eye = head["eye"]
            for y, top in self.ridge_profile:
                p = Vector((self.room_size[0] + 76.0, y, top))
                if self._through_window(eye, p):
                    pts.append(to_glass(gm(p))[0])
            fs.ridge = pts
            if "ridge" in sensed_region:
                fs.ridge_att = (0.0, tags.SURFACE_COLOUR["ridge"])
            else:
                fs.ridge_att = (held_level * ridge_region.in_mind * 1.3, GREY)
        ground_region = self.regions["ground"]
        if ground_region.in_mind > 0:
            eye = head["eye"]
            corners = [Vector((7.0, -3.0, 0.0)), Vector((7.0, 7.0, 0.0)), Vector((70.0, 30.0, 0.0)), Vector((70.0, -28.0, 0.0))]
            fs.ground = [to_glass(gm(c))[0] for c in corners]
            if "ground" in sensed_region:
                fs.ground_att = (0.0, tags.SURFACE_COLOUR["ground"])
            else:
                fs.ground_att = (held_level * ground_region.in_mind, GREY)

        # ---- regions of the room: state, colour, attention ----
        # A surface a sense is reaching shows its own colour, as the room has it (his review of
        # 2026-11-07); it drains to grey over a second once the sense leaves it, and stays grey
        # from memory. The sense's own colour is on the signal, not on the surface.
        def own_colour(own, last_sensed, sensed_now):
            if sensed_now:
                return own
            if last_sensed is None:
                return GREY
            fresh = 1.0 - anim.smoothstep((t - last_sensed) / 1.2)
            return tuple(anim.lerp(g, o, fresh) for g, o in zip(GREY, own))

        for tag, r in self.regions.items():
            sensed = sensed_region.get(tag)
            if sensed is not None:
                r.last_sensed = t
                if r.in_mind < 1.0:
                    r.in_mind = 1.0
            if r.last_sensed is not None and not r.filled:
                r.finish = 0.7 * clamp((t - r.last_sensed) / 45.0)
            col = own_colour(tags.SURFACE_COLOUR.get(tag, GREY), r.last_sensed, sensed is not None)
            if r.in_mind <= 1e-4 and sensed is None:
                r.state, r.att, r.colour = tags.DARK, 0.0, GREY
            elif sensed is not None:
                r.state, r.att, r.colour = tags.SENSED, sensed[0], col
            elif r.filled:
                r.state, r.att, r.colour = tags.FILLED, held_level * 0.8 * r.in_mind, GREY
            else:
                r.state, r.att, r.colour = tags.REMEMBERED, held_level * r.in_mind, col
            # a lit thing he still holds keeps some light just after the sense leaves it
            if r.state == tags.REMEMBERED and r.last_sensed is not None:
                r.att += 0.25 * max(0.0, 1.0 - (t - r.last_sensed) / 1.5) * aw
            fs.regions[tag] = {"att": r.att, "col": r.colour, "soft": r.finish, "state": r.state}
        # at the end the room sinks to faint grey behind the screen: the awareness curve does it
        fs.rug_curled = self.rug_curled

        # ---- the simulated body: parts and joints ----
        for part, r in self.parts.items():
            sensed = sensed_part.get(part)
            if sensed is not None:
                r.last_sensed = t
                r.in_mind = max(r.in_mind, 1.0)
            pcol = own_colour(tags.PART_COLOUR.get(part, GREY), r.last_sensed, sensed is not None)
            if sensed is not None:
                state, att, col = tags.SENSED, sensed[0], pcol
            elif r.in_mind > 1e-4:
                state, att, col = tags.REMEMBERED, held_level * r.in_mind, pcol
                if r.last_sensed is not None:
                    att += 0.2 * max(0.0, 1.0 - (t - r.last_sensed) / 1.2) * aw
            else:
                state, att, col = tags.DARK, 0.0, GREY
            fs.parts[part] = {"att": att, "col": col, "state": state}
        # the glow raises the body's centre with it
        glow = scaled.get("_glow", 0.0)
        fs.glow = max(glow, floor_a * 1.2 * aw if t > 9.0 else 0.0)
        for part in ("chest", "pelvis"):
            if fs.parts[part]["state"] != tags.SENSED:
                fs.parts[part]["att"] = max(fs.parts[part]["att"], glow * 0.35)
                if glow * 0.35 > 0 and fs.parts[part]["state"] == tags.DARK:
                    fs.parts[part]["state"] = tags.REMEMBERED
        # the simulated head holds the model's centre whether or not it is lit: a faint presence
        fs.parts["head"]["att"] = max(fs.parts["head"]["att"], floor_a * aw)
        # belief: where the mind puts the body; wrong for a moment at the rug
        belief = dict(J)
        belief["head"] = head["loc"]
        if 60.3 <= t < 60.75:
            u = clamp((t - 60.3) / 0.25)
            over = Vector((0.16, 0.0, 0.0)) * (1.0 - anim.smoothstep((t - 60.5) / 0.25)) * anim.smoothstep(u * 2)
            belief["toe_r"] = J["toe_r"] + over
            belief["ankle_r"] = J["ankle_r"] + over * 0.8
        fs.sim_joints = {k: gm(v) for k, v in belief.items()}

        # ---- the phone in the model ----
        pr = self.regions["phone"]
        if pr.in_mind > 1e-4 or "phone" in sensed_region:
            fs.phone = M @ st["phone"]
        else:
            fs.phone = None

        # ---- words of recognition ----
        for w in self.data.get("words", []):
            fs.words[w] = 0.0
        for rec in self.recognition:
            k = f"_rec_{rec['t']}"
            if k in scaled:
                fs.words[rec["word"]] = max(fs.words[rec["word"]], scaled[k] / 0.6)

        # ---- the will: words on their way down ----
        # His review of 2026-11-07: a word comes in fast and drops quickly, then slows and fades
        # out slowly, so it can be read: most of the drop in the first half second, the rest a
        # drift over the next 1.7 s while it fades.
        soul = SOUL_POS
        for i, w in enumerate(self.will):
            dt_w = t - w["t"]
            if 0.0 <= dt_w < 2.2:
                u1 = min(1.0, dt_w / 0.5)
                s_pos = 0.85 * (1.0 - (1.0 - u1) * (1.0 - u1)) + 0.15 * clamp((dt_w - 0.5) / 1.7)
                pos = soul.lerp(HEAD_CENTRE, s_pos)
                att = anim.smoothstep(dt_w / 0.15) * (1.0 - anim.smoothstep((dt_w - 0.9) / 1.3))
                fs.will.append((i, pos, att))

        # ---- the mind's zoom for the next frame: the scale that fits what sight reaches ----
        # the zoom follows what the eyes have, whichever sense attention is on (his review of
        # 2026-11-08: the model came back in during the stretch, and the wall seemed to fade in); the
        # distances are taken as the mind holds them; with the eyes shut, or nothing in reach, the
        # last target holds
        # a thought's things count as attended too (his eighth review of 2026-11-10): each at its place's
        # distance, the thought's level spread over them as a full fan of sight would be, so a thought of
        # the room while the eyes have nothing brings the model in to the room, and a thought while the
        # eyes hold the far field leaves the far field in
        thought_tags = [tag for tag, level in fs.thought.items() if level > 1e-3 and tag in self.thing_points]
        for tag in thought_tags:
            reach.append(((self.thing_points[tag] - head["loc"]).length, fs.thought[tag] * THINK_REACH * FAN_WEIGHT / len(thought_tags)))
        total = sum(a for _, a in reach)
        if reach and total > 1e-6:
            reach.sort()
            acc = 0.0
            d_seen = reach[-1][0]
            for dist, a in reach:
                acc += a
                if acc >= SEEN_SHARE * total:
                    d_seen = dist
                    break
            fit = FIT_RADIUS / max(believed(d_seen), 0.3)
            target = math.log(clamp(fit, FAR_SCALE, MODEL_SCALE))
        else:
            target = self.zoom_hist[-1] if self.zoom_hist else math.log(MODEL_SCALE)
        fs.far = 1.0 if target < math.log(MODEL_SCALE) - 1.5 else 0.0
        fs.far_vote = (round(far_sum, 3), round(all_sum, 3), round(body_sum, 3), round(math.exp(target), 5), leader_ev["id"] if leader_ev else None)
        if self.zoom:
            # the farthest target asked for within the hold wins: zooming out is prompt, coming back
            # in waits until nothing far has been looked at for ZOOM_HOLD seconds
            self.zoom_hist.append(target)
            keep = max(1, int(round(ZOOM_HOLD * self.fps)))
            if len(self.zoom_hist) > keep:
                self.zoom_hist.pop(0)
            held = min(self.zoom_hist)
            tau = ZOOM_OUT_TAU if held < self.zoom_log else ZOOM_IN_TAU
            self.zoom_log += (held - self.zoom_log) * (1.0 - math.exp(-dt / tau))
            # a reveal's twin phase (the cut's mind moves): the model is the room at one scale, the whole
            # room within the knee, so the camera riding the twin of the room's camera sees every thing
            # where the room has it and the two pictures dissolve into one (his eighth review of
            # 2026-11-10: at the room's own scale the twin stood pressed at the glass, and the model's lamp
            # beside the room's); the mind's zoom returns once the camera has left the twin
            t_next = t + dt
            for span in self.twin_spans:
                if span["ease_from"] <= t_next <= span["to"]:
                    W, D, H = self.room_size
                    d_far = max((Vector((x, y, z)) - head["eye"]).length for x in (0.0, W) for y in (0.0, D) for z in (0.0, H))
                    twin = math.log(KNEE * GLASS_RADIUS / max(believed(d_far), 0.3))
                    if "start_log" not in span:
                        span["start_log"] = self.zoom_log
                    w = 1.0 if t_next >= span["from"] else anim.smoothstep((t_next - span["ease_from"]) / max(span["from"] - span["ease_from"], 1e-6))
                    self.zoom_log = anim.lerp(span["start_log"], twin, w)
            self.scale = math.exp(self.zoom_log)

        # ---- the camera and the ghost ----
        fs.camera = catmull(CAMERA_KEYS, t)
        fs.ghost = 0.3 + 0.7 * anim.smoothstep((t - 3.5) / 5.0)
        return fs

    # ---- helpers ----
    def _glow(self, t):
        """The mind's picture of its soul: up as a word lands, sinking between words."""
        g = 0.0
        for w in self.will:
            land = w["t"] + 0.5
            dt = t - land
            if dt >= 0:
                g = max(g, 0.85 * math.exp(-dt / 2.2) + 0.1 * math.exp(-dt / 8.0))
        return g

    def _source(self, name, st):
        if name == "phone":
            return st["phone"].translation
        if name == "window":
            W = self.room_size[0]
            wy0, wy1, wz0, wz1 = self.window
            return Vector((W + 0.3, (wy0 + wy1) / 2, (wz0 + wz1) / 2))
        if name in FAR_SOURCES:
            return FAR_SOURCES[name]
        if name in self.targets:
            return self.targets[name]
        if name in st["joints"]:
            return st["joints"][name]
        return st["head"]["loc"]

    @staticmethod
    def _along(J, chain, dist):
        """The point dist metres along the chain's joints from its start; (point, on_path)."""
        remaining = dist
        for a, b in zip(chain, chain[1:]):
            seg = J[b] - J[a]
            L = seg.length
            if remaining <= L:
                return J[a] + seg * (remaining / L if L > 0 else 0.0), True
            remaining -= L
        return J[chain[-1]], False

    @staticmethod
    def _part_centre(J, part, head):
        if part == "head":
            return head["loc"]
        spec = tags.PARTS[part]
        pts = [J[j] for j in spec["joints"]]
        for b in spec["bones"]:
            if b in J:
                pts.append(J[b])
        if not pts:
            return head["loc"]
        c = Vector((0, 0, 0))
        for p in pts:
            c += p
        return c / len(pts)

    def _through_window(self, eye, p):
        W = self.room_size[0]
        wy0, wy1, wz0, wz1 = self.window
        d = p - eye
        if d.x <= 1e-6:
            return False
        u = (W - eye.x) / d.x
        q = eye + d * u
        return wy0 - 0.3 <= q.y <= wy1 + 0.3 and wz0 - 0.2 <= q.z <= wz1 + 0.2


class SceneReader:
    """Reads the scene state the engine needs at a frame from the Blender room scene."""

    def __init__(self, scene, figure_empties, phone, sky_node, spec, sun_direction_fn, head_offsets):
        self.scene = scene
        self.empties = figure_empties
        self.phone = phone
        self.sky = sky_node
        self.spec = spec
        self.sun_direction = sun_direction_fn
        self.eye_offset, self.ear_offset = head_offsets
        self.dg = None
        self.W = spec.size[0]
        self.window = spec.window

    def state(self, frame):
        sc = self.scene
        sc.frame_set(frame)
        self.dg = sc.view_layers[0].depsgraph
        joints = {name: e.matrix_world.translation.copy() for name, e in self.empties.items()}
        hm = self.empties["head"].matrix_world
        R = hm.to_3x3()
        loc = hm.translation.copy()
        fwd, left, up = R.col[0].normalized(), R.col[1].normalized(), R.col[2].normalized()
        head = {"loc": loc, "rot": R, "fwd": fwd, "left": left, "up": up,
                "eye": loc + R @ Vector(self.eye_offset),
                "ear_l": loc + left * self.ear_offset, "ear_r": loc - left * self.ear_offset}
        import math as _m
        el = _m.degrees(self.sky.sun_elevation)
        # the sun's size as the scene's sky has it (a sky texture's sun_size is the disc's whole angle, in radians)
        size = getattr(self.sky, "sun_size", None)
        return {"joints": joints, "head": head, "phone": self.phone.matrix_world.copy(),
                "sun_dir": self.sun_direction(self.spec, el), "sun_elevation": el,
                "sun_radius": _m.degrees(size) / 2.0 if size else SUN_LIMB_DEG}

    def cast(self, origin, direction, distance=200.0):
        ok, loc, normal, index, obj, _ = self.scene.ray_cast(self.dg, origin, direction, distance=distance)
        own = 0
        while ok and obj.get(tags.PART_PROP) in ("head", "eye_l", "eye_r") and (loc - origin).length < 0.2 and own < 3:
            # the eyes sit at the head's surface: a ray that meets his own skull, or the stand-in eyes there (rung 2p),
            # is cast on from there
            ok, loc, normal, index, obj, _ = self.scene.ray_cast(self.dg, loc + direction * 0.01, direction, distance=distance)
            own += 1
        passes = 0
        while ok and obj.get(tags.PASS_PROP) and passes < 3:
            # glass the eye sees through: the window's pane
            ok, loc, normal, index, obj, _ = self.scene.ray_cast(self.dg, loc + direction * 0.005, direction, distance=distance)
            passes += 1
        out = {"hit": bool(ok), "location": loc, "normal": normal, "obj": obj, "index": index,
               "tag": None, "kind": None, "through_window": False}
        if not ok:
            out["through_window"] = True
            return out
        if loc.x > self.W + 0.01:
            out["through_window"] = True
        tag = obj.get(tags.TAG_PROP)
        part = obj.get(tags.PART_PROP)
        if part is not None:
            out["kind"], out["tag"] = "body", part
            return out
        out["kind"] = "surface"
        if tag in ("shell", "wall_e") and "tv_poly_tags" in obj:
            pt = list(obj["tv_poly_tags"])
            out["tag"] = pt[index] if index < len(pt) else tag
        elif tag == "table":
            (tx0, ty0, tz0), (tx1, ty1, tz1) = self.spec.table
            if normal.x > 0.9:
                out["tag"] = "table_far"
            elif normal.y > 0.9 and loc.z > tz1 - 0.06:
                out["tag"] = "table_edge"
            else:
                out["tag"] = "table"
        elif tag == "rug":
            out["tag"] = "rug_edge" if loc.x < obj.get("tv_curl_x", 0.0) else "rug"
        elif tag == "outside":
            out["tag"] = "ground" if index == 0 else "ridge"
        else:
            out["tag"] = tag
        return out


def load_senses(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

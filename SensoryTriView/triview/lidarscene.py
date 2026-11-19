"""The True-Person scene as the eyes' own scan (his review of 2026-11-07, third pass; memory and the
senses back on 2026-11-08, fourth; distance as the mind holds it, 2026-11-08, fifth).

Inside the glass skull there is what the eyes capture this frame: a surface of ray hits, one small
splat per pixel of a fisheye scan taken from the eyes over the field of both eyes together, each
splat at the point its ray struck, turned to the surface there, coloured by the same ray's light.
Every hit sits at the distance the mind holds it (triview/engine.py believed): within reach as it is,
beyond reach compressed, so the trees, the ridge, the sky and the sun keep their order and not their
scale; until the far field has resolved, everything beyond reach lies flat at the sky's distance.
One rule for everything in the skull (his word of 2026-11-09, fifth review): a place the eyes' rays
reach this frame is seen, and drawn as the rays brought it back; everything else the mind holds is
memory, drawn in memory's style (most of its colour drained by its age, dimmer, shimmering), lit by
the attention on the thing it lies on or by the eyes being shut, and gone the moment a ray reaches it.
From the side the eyes never see a splat is dimmer, and drawn only while the rendering camera is far
(BACK_CLEAR): a camera near the skull or inside it looks into the model through the backs of the near
surfaces, and a wide station sees the closed shell a scan from inside is. One rule for every thing
(his seventh review of 2026-11-10), where the room's shell, a thing and the far field had each had
their own. What is not in the eyes' field is not drawn; what the lids cover is dimmed; what still lies
beyond the skull's reach is pressed onto the glass.

The memories, each lit one way (his seventh review: conscious memory alone for now, what he thinks of
at the moment, coming up fast and fading slowly; the unconscious fill of everything known is a later
rung's): the last picture the eyes held, standing whole while they stay shut, once they have held one (until
their first opening there is no picture: the last picture, the backdrop and the remembered sky have no
geometry, and the eyes being shut light nothing; his word of 2026-11-12, the waking); a thought's picture, the
frame in which the things he thinks of were last in sight together, lit on those things by the thought
(the chime: the phone's place, the table and the bed as last seen); the backdrop, the sky, the ground
and the range as a second scan with the trees, the bushes, the walls and the body hidden, what lies
behind a crown or a hand where no ray reaches this frame (his review of 2026-11-09: the trees cast
shadows on the sky), lit by the thought of the outside or by the eyes being shut; and the sky alone as
a third scan, remembered behind the range the same way: the sky down to the horizon the mind imagines
without the range, and below that horizon the ground as the eyes saw it, carried out to the sky's
dome, so no camera looks past the ridge into a hole. The thoughts are the timeline's (data/senses.json,
triview/engine.py), each naming the things it holds. The sun is held as what it is known to be, a ball
of light a little beyond the sky: the half the rays reach is seen while the sun is in sight, the rest
is memory, lit as the backdrop is, by the eyes being shut only where the last picture held the sun. The
senses on the picture are the rings of a sound alone. No plates,
no body glyphs, no words.

The scan comes from rungs/rung2.py's scan view: for every frame a colour picture through Cam_Scan
(frame_%04d.png, the eye's exposure in it) and the world position of every pixel's hit
(pos_%04d.exr, a one-sample render with a material that emits the position, a shell far outside for
the sky). Geometry nodes read both as image sequences, carry the hits into the model's frame (the
ModelFrame empty, the mind's zoom in its scale), press the far ones onto the glass, and instance the
splats with the picture's colour stored on them; the materials paint them from that colour. The
backdrop view renders the same two pictures with the near things hidden (backdrop/), and the sky view
with everything but the sky's shell hidden (sky/), both at the scan's own size: at half of it their
culling behind the live picture left a staircase round every crown (his seventh review). The peel view
(peel/) carries the same rays on through the first thing they strike to where they leave it, position
and index alone: the far side of every thing the mind holds whole (his eighth review of 2026-11-10: a
bush seen from the side was a crescent), drawn in the ray's own colour as a memory of this frame's
picture, its front away from the eyes where the surface faces, lit as the backdrop is.

A splat's sheet (its slope and its size) is laid only between hits on one thing, the thing's index
beside every hit: toward the neighbour on the same thing, and at the thing's edge facing the eyes at
the plain footprint (his eighth review: a lamp's rim had been stretched to the wall behind it, the
open leaf's frame to the jamb, and the far field's edge at the leaf's frame shrunk to a dotted seam).
The sun's seen half is lit by the share of its disc the eyes' rays reach, dimmed by the lids and gone
with the live picture as every seen splat is, and by nothing else: the warmth on his face had kept it
lit behind his hand, and every blink switched it off.
"""
import math
import pathlib

import bpy
import numpy as np
from mathutils import Matrix, Vector

from . import anim, cameras, engine, figure, geo, materials as mats, render, room, tags, touches
from .body import EYE_OFFSET
from .mindscene import _annulus, _placeholder_png

FOV_DEG = 200.0            # the scan's field across its square picture
FIELD_H, FIELD_V = engine.FIELD_H, engine.FIELD_V   # the field of both eyes kept from it (triview/engine.py): an ellipse 200 across, 130 high
KNEE = engine.KNEE         # the fraction of the glass radius where the pressing onto the glass begins, for what the believed distance still leaves outside
OVERLAP = 1.7              # a splat's width over its cell of the sheet (its pixel's footprint at the least), so the splats close
TILT_COS = 0.25            # a pixel whose sheet runs within this cosine of the ray, at a limb, is drawn as a coin, a splat facing
                           # the eyes at the plain footprint: it covers its pixel from the eyes (his eleventh review of 2026-11-11:
                           # with every splat in its sheet the limb's splats were edge-on from the eyes, a dark line at every
                           # silhouette) and is edge-on from the side, where its chord splat closes the band instead: every
                           # grazing pixel of a thing held whole, and a rim pixel of a thing that spans its distance. Every
                           # other splat lies in its sheet (the blend toward facing of rungs 2d to 2m stuck half-turned splats
                           # out of the sheet as fur)
GRAZE_COS = 0.15           # within this cosine of the ray the sign of the sheet's normal along the ray means nothing, and the
                           # front is set by the way out of the thing in the picture instead
CHORD_IN = 0.5             # a chord splat stands this many footprints inside its thing
UPPER_SHARE = 0.75         # the upper lid's share of a blink, as the First-Person lids
EDGE_JUMP = 0.12           # a neighbouring hit this share of the distance away marks an edge of depth, if the jump is
EDGE_RATIO = 2.5           # this many times the jump to the opposite neighbour: a grazing surface steps far on both sides,
                           # evenly (the far ground's rows read as edges until his review of 2026-11-09: rings from the side)
SPLAT_MIN = 0.0025         # the smallest splat, as a share of the glass radius: a render pixel from the close camera
STRETCH_MAX = 4.0          # a splat is at most this many times its plain footprint long along the sheet's slope: a surface
                           # within the reach closes down to fifteen degrees of grazing, and a thing's rim, where the sheet
                           # runs along the ray, streaks no farther (his eighth review of 2026-11-10: fur on every far side).
                           # 12 for a day, 2026-11-14, to close the window's reveal and the far ground seen at less: the
                           # pieces' ends stood as longer teeth at every edge of such a surface, a remembered ridge as steps
STRETCH_COMPACT = 12.0     # and for a thing held whole, whose far side closes it, as far as its cell along the sheet reaches
                           # (a thing's rim spans at most a few footprints along the ray, by its size); 1.5 through his ninth
                           # review of 2026-11-10, which left the rim a band of bare surface between the two sides
SHEET = True               # the seen picture drawn as connected sheets (scan_nodes, sheet), its splats left to the pixels
                           # no sheet takes
SHEET_STEP = 0.12          # two neighbouring pixels on one thing are joined in its sheet while the step between their hits is
                           # under this share of their distance from the eyes: a surface down to about two degrees of grazing
SHEET_WIN = 2              # a sheet's rim vertex is set where the pixels this many each way round it say its thing's edge lies,
SHEET_PAST = 0.5           # this share of a pixel farther, so two things that touch overlap, and at most
SHEET_OUT_MAX = 12.0       # this many footprints from its hit
SHEET_COIN = 1.0           # a coin of a thing held whole lies in its sheet no deeper than its nearest neighbour on the thing
                           # and this many footprints
SHEET_EVEN_COS = 0.94      # two pixels that step farther apart than SHEET_STEP are joined all the same where the step beyond
                           # or behind, on the same thing, is within EDGE_RATIO of theirs and runs within this cosine of it: a
                           # flat surface seen nearly edge-on (the window sill from the bed), whose rows stood apart as strips
ROUND_SHARE = 0.12         # a thing no one direction of whose faces holds this share of its surface is round to the picture (the
                           # table's round, worked out in rungs/rung2.py thing_rows): on a picture drawn as sheets the limb's
                           # chords are drawn for round things alone
SHEET_CHORDS = False       # the SEEN picture drawn as sheets carries the limb's chords as well: on a slab seen nearly edge-on
                           # every pixel grazes and carries one, a comb of strips as long as the slab is deep (the window sill
                           # from the bed); the known shape's tiles draw such a face instead (EDGE_SEEN). A picture held from
                           # another moment keeps its chords whatever this says: they close a round thing's limb
EDGE_SEEN = True           # a face the eyes see within TILT_COS of their ray is drawn by its thing's known shape, in the seen
                           # look and the picture's own colour for that thing there (shape_nodes): the picture has one row of
                           # pixels for such a face, a slanting line of hits across it, and no drawing of those makes the face
EDGE_SEEN_KEEP = 1.3       # the shape's faces within this many times TILT_COS at their middle are kept for that test
EDGE_SEEN_WIN = 2          # such a tile's colour: of the pixels this many each way round its place, the inner ones of its
                           # thing (no neighbour on another thing: a rim pixel is a mix of the thing and what stands behind
                           # it), the nearer their hit to the tile the more; with none, its thing's pixels among the nine
SHEET_OUT_GRAZE = 1.0      # a sheet's rim vertex on such a face (the pixel within TILT_COS of the ray, its thing one the mind
                           # has a shape of) is set out this many footprints at most: the shape's tiles draw the face to its
                           # true edge, where the rim's own reach along a grazing surface overshot it in teeth
SHEET_OUT_COIN = 2.0       # and any rim vertex of a thing held whole this many: at a round thing's limb the sheet's own step
                           # runs along the eyes' ray, and a vertex set out along it stood as hair once the chords were gone
LIMB_CHORD = 0.0           # a far side's hit this share of its thing's radius or less beyond the front is left out (0.25 until
                           # his tenth review: the far side stopped short of the rim and the band between the sides was bare)
LID_FLOOR = 0.2            # what the lids leave of the picture's brightness where they cover it
EDGE_ON = (0.01, 0.03)     # the cosine between a splat's normal and the view at which it fades out, and is whole: a last resort
                           # only, since the geometry turns every splat the camera would see edge-on toward it (CAM_TILT); 0.04 to
                           # 0.12 until his eleventh review of 2026-11-11, which left every thing open at the camera's own
                           # silhouette, where every tile is tangent to it, so the sky showed through a crown in streaks
CAM_TILT_COS = 0.2         # below this cosine between a splat's front and the rendering camera's view the splat turns toward the
                           # camera, by CAM_TILT of the view at full turn: a tile tangent to a ball at the camera's silhouette
                           # keeps a third of its width instead of vanishing. From the eyes nothing turns: every splat there
                           # faces the ray by at least TILT_COS, and the coins face it outright
CAM_TILT = 0.35
COIN_ON = (0.85, 0.97)     # the cosine between the rendering camera's view and the eyes' ray over which a coin comes in: it is
                           # drawn for the camera on the eyes' own ray (the reveal's twin, the dive, the check), where it
                           # covers its pixel; from any other direction the chords and the sheet's splats cover the surface,
                           # and its own colour, a silhouette pixel's mix with what stands behind, showed as pale dashes
NEAR_FOOT = (20.0, 60.0)   # a splat's distance from the rendering camera over its own footprint, below which it fades out: a
                           # fade by its size in the picture, the same at every scale of the model, so a camera passing through
                           # the sheet meets no streaks and the eyes, where every splat is a pixel (one over OVERLAP times the
                           # pixel's angle, some 170 footprints), see every one. Model metres (0.002 to 0.006) until 2026-11-12:
                           # at the eyes, with the model still small after the reveal's twin, his raised arm lay within those
                           # metres and faded out, so the check's frame at 48.8 s had it black where the picture has it
BACK_DIM = 0.6             # how bright a splat is from the side the eyes never see, where it is drawn
BACK_CLEAR = (2.0, 3.5)    # model metres from the rendering camera: nearer than the first a splat's back is clear, so a camera
                           # near the skull or inside it sees into the model; beyond the second the back is solid, so a wide
                           # station sees the model as the closed shell a scan from inside is. One rule for every thing (his
                           # seventh review of 2026-11-10); until then the room's shell was clear from behind, a thing solid
                           # and the far field clear, each by its kind
LIVE_HOLD = 0.35           # seconds the eyes must stay shut before the live picture goes and memory stands
LIVE_TAU = 0.3             # the live picture's fading once they have (0.6 until 2026-11-15: the lids' own picture then stood
                           # beside the remembered one, which now comes up at once, MEM_RISE, and ripples: a second of doubled
                           # crowns and ridge as his eyes shut in the sun)
SETTLE_TOP = 0.2           # a remembered hit at a place the eyes see holds still, on the seen picture's own depth, while that
                           # picture stands at this share of its light or more; it takes up its ripple and its own depth as the
                           # picture goes from here to SEEN_FADE's first mark (0.4 until 2026-11-15)
MEM_RISE = 0.3             # seconds over which the remembered picture comes up once the eyes count as shut (it waited for the
                           # lids' own picture to go and took 0.6 until 2026-11-15: in a doze of 1.6 s it barely stood)
MEM_DESAT = 0.5            # the share of a memory's colour that drains toward its own grey, its brightness kept (toward white
                           # from his ninth review of 2026-11-10 to his eleventh of 2026-11-11, where the remembered side of a
                           # crown in full colour read as seen: greyer, he said, and white too bright)
MEM_AGE_TAU = 6.0          # seconds over which a memory fades toward its floor: what is remembered fades with time
MEM_AGE_BRIGHT = 0.82      # the brightness an old memory keeps, as a share of the seen picture's: a memory of this very frame is
                           # as bright as sight and dims with its age alone (0.375 until his eighth review of 2026-11-10: the
                           # bed and the table he thought of at the chime, forty seconds old, were too faint to find; 0.7
                           # until his eleventh)
MEM_AGE_ALPHA = 1.0        # and the opacity an old memory keeps: whole (0.6, then 0.85 from his eleventh review, until 2026-11-12:
                           # the tiles are drawn by a dither, which at 85 percent drops a tile in some of a pixel's samples, and
                           # what lay behind showed through as specks, a pale wall through the piano, the bed through the
                           # blanket; three times the samples barely lessened it, and fully opaque it is gone. A memory's age is
                           # in its brightness, its drained colour and its waves)
LIT_THIN = (0.02, 0.10)    # a remembered tile's light under which it thins out, clear at the first and whole from the second: lit
                           # by a thought or a sense that is fading, a tile dimmed to black and stayed solid until 2026-11-12,
                           # fifth round, so the ears' red, fading for four seconds after the alarm, stood as two black marks on
                           # the pillow, and a forgotten bed as a dark block before what lay behind it
MEM_BRIGHT = MEM_AGE_BRIGHT   # what the sun's never-seen half shows by default; keyed per frame (MemBright) to the age of the
                              # picture that lights it, as every remembered splat's brightness is (his eighth review of 2026-11-10:
                              # with the eyes shut the sun stood as a dark disc against the remembered sky)
SEEN_TOL = 0.08            # a remembered hit within this share of its distance of the live hit in its direction is seen now, not remembered
SEEN_FADE = (0.1, 0.9)     # the live picture's standing (LiveNow, 0 to 1) between which a memory at a place the eyes see gives way to
                           # it: whole under the first, gone from the second, a smoothstep share between. One switch at one half until
                           # 2026-11-14: with his eyes shut in the sun the whole remembered view came in one frame, and went in one
                           # as they opened (the dev showcase, 80.77 and 89.23 s)
SEAM_N = 256               # the seam map's side (_seam_map): a coarse picture of where the eyes' picture has an edge
SEAM_BLUR = 8              # passes of the map's cells an edge is spread over, and
SEAM_GAIN = 6.0            # the band's gain: whole within about two degrees of an edge, gone by about five
SEAM_JUMP = 0.10           # a hit a cell on standing this share of its distance nearer or farther marks a step of depth, or a
                           # surface grazed at under about eight degrees, whose splats stand apart from the camera's side
SEAM_DEEP = 0.05           # under this much of the band a seen place lies deep inside what the eyes see, and its memory tile goes
SEAM_CELL = 0.2            # metres: the patch of a known shape's face the resolving test (SEAM_PIX) is put to
SEAM_BACK = 0.005          # a tile kept at a seam though the eyes see its place sits this share of its distance behind the seen
                           # surface, along its own face's normal
SEAM_STAND = (0.7, 0.95)   # a tile at a seam holds still between these shares of the live picture (LiveNow): it is anchored to
                           # a picture that stands, not to one still coming through its dither
SEAM_PIX = 1.5             # a tile can be kept at a seam where a patch of its face SEAM_CELL across, at its slant to the eyes'
                           # ray, spans this many pixels of the picture or more: under that the picture does not resolve the face
SEEN_BACK = 0.002          # between those marks a memory completing this very frame's picture, at a place the eyes see, sits this
                           # share of its distance behind the live picture: the two lie on the same splats, and of two surfaces at
                           # one depth the renderer draws the later over the other whatever its opacity
MEM_REGION_COUNT = 10      # the things a remembered hit can lie on, each with a keyed thought: bed, table, outside, east wall, floor, ceiling, west, north, south, other
# a memory's unrest is in its shape: its hits waver across the eyes' rays like a mirage, in waves wider than tall that
# change shape where they stand, in the thing's own coordinates (per thing, not a mask over the picture: his tenth
# review of 2026-11-10; flecks of light over the memory, then a fine noise, read as a texture: his eleventh of
# 2026-11-11). Until 2026-11-12, fifth round, the waves rose through the thing and moved its hits along the room's up
# alone: "the shimmer looks weird going up, I would have expected its visual movement to be more random or
# horizontally". A memory completing this frame's picture while the eyes are open holds still, so no strip of it
# drifts out of the hole it fills
HEAT_AMP_DEG = 3.9         # the ripple's amplitude across the eyes' ray, in degrees from the eyes, and
HEAT_WAVE_DEG = 5.9        # the waves' height, in degrees from the eyes: ONE ripple for every remembered thing (his fourteenth
                           # round of 2026-11-14: "multiple different kinds of memory effects ... they all should be the same
                           # effect"; "the ground and mountain clearly shimmer but the bushes don't"). Until then both were shares
                           # of each thing's own radius between bounds in the scan's footprints (the five numbers below), which
                           # as angles from the eyes came to 3.9 degrees for the ground, the range and the sky, about 2 for a
                           # wall or the bed and 0.4 for a bush, and would have halved with a scan twice as fine. These two are
                           # the far field's, the look he named as the proper one. The wave is a field over the direction from
                           # the eyes in the room's own axes: a turn of the head does not move it over the things. His own
                           # body's known shape keeps the old, small measure: it is felt at every moment, not held from sight
HEAT_AMP_RAD = HEAT_AMP_DEG * 3.141592653589793 / 180.0
HEAT_WAVE_RAD = HEAT_WAVE_DEG * 3.141592653589793 / 180.0
HEAT_STAGGER = (17.31, 5.77, 11.13, 3.7)   # a thing held whole reads the ripple this far on in the pattern (three axes) and in
                           # time, times its index: its own shimmer, of the one strength and the one wave size
HEAT_HELD = "centre"       # how a thing held whole takes that reading. "own": outright, so the whole thing also moves by it,
                           # apart from its neighbours. "centre": against the same reading at its own centre, so the centre stays
                           # where the thing is and the thing wavers about it. "field": as "centre", and the centre goes with the
                           # shared field there (r14s: its neighbours then rose and fell with it, as under the one field read off
                           # the direction alone)
HEAT_SHARE = 0.04          # the ripple's amplitude as a share of the thing's radius (0.015 until 2026-11-12: he saw no shimmer),
HEAT_FOOT_MIN = 2.0        # never under this many of the scan's footprints at the hit,
HEAT_FOOT_MAX = 20.0       # nor over this many (a mountain range would heave; 8 until 2026-11-12)
HEAT_LIGHT = 0.4           # the waves' light: a remembered tile brighter or dimmer by up to this share with the wave passing
                           # through it, smoothly, as heat's rising air gathers and spreads the light it bends (2026-11-12: a
                           # flat-coloured stand-in surface bent by the waves alone showed nothing inside its outline). No
                           # grain: the same slow field that moves the tile. At 0.25 a wall's light swung by a twentieth at a
                           # point, too little to see; 0.4 since the same day
HEAT_GRAIN = 0.12          # the waves' height as a share of the thing's radius,
HEAT_GRAIN_FOOT = (15.0, 30.0)   # held between these many footprints at the hit
HEAT_ASPECT = 4.0          # the waves this many times wider than tall
HEAT_SPEED = 1.5           # cells a second the pattern changes shape by, where it stands: as fast at a point as the 0.5 of
                           # change and the 1.4 of rise it had together until the fifth round of 2026-11-12, when the rise went
HEAT_ACROSS = 0.7071       # the wave moves a hit along each of the room's three axes by this share of the amplitude, so what is
                           # left across the ray, two directions of it, comes to the amplitude HEAT_SHARE names
HEAT_BEND = 0.15           # a thing held whole keeps its shape: the ripple moves no point of it, against its own centre, by
                           # more than this share of the thing's radius (a smooth limit: under half of it nothing changes).
                           # The waves are HEAT_ASPECT times wider than tall, so a thing as tall as it is wide and smaller
                           # than a wave is sheared: the remembered sun ball, 3 degrees in radius, was moved by a quarter of
                           # its radius in the mean and by two thirds at the worst, a wedge where a ball was (the audit's O5,
                           # 2026-11-16; a bush as wide is low, and was moved half as far). What spans its distance, the
                           # walls and the ground, is not held whole and has no such limit. 0: no limit
SUN_STAGGER = 97.0         # the sun's own place in the ripple's pattern and its own time (a thing held whole has its
                           # index for that; the sun ball has no row in the table of things)
SEAM_WIDE = (32, 12.0)     # how far a remembered tile is HELD at a seam: the seams spread over this many passes of the map and
                           # scaled by this gain, whole within about two degrees of the seam (the fringe of remembered tiles that
                           # closes a seam must not stir: at a gain of 9, whole at the seam alone, the white line along the
                           # window's frame broke into dashes) and gone by about eight, a bell's slope. (The seam band
                           # itself times three until 2026-11-15: from whole to nothing within a degree and a half, where the ripple
                           # pulled the tiles apart)
SEAM_WIDE_OUT = 0.014      # beyond the scan's circle that band falls away as a bell of this share of the scan's field (2.8 degrees)
SEAM_RING_HOLD = 0.05      # and beyond the field's own edge the hold falls away as a bell of this share of the ellipse's half axes,
                           # on both sides of the scan's circle alike (no hold at all beyond the circle, for a morning: a crack along it)
SHAPE_GROW = 1.3           # a remembered tile of a known shape is this many times its footprint wide (a tile drawn as seen keeps
                           # the footprint): stretched by the ripple, the tiles thin out, and wider ones keep the surface closed
SEAM_RING = 0.03           # the field's own edge is a seam: a ring this share of the ellipse's half axes wide at its edge
SEAM_UNDER = 2             # a sheet of a picture completing this frame's runs on this many pixels under the seen picture's rim,
                           # and the remembered sky as many under the sky's own rim: two layers' sheets ending on one line leave
                           # pixel-wide gaps between them (2026-11-15, dotted lines in the sky)
FIELD_RIM = 1.5            # a sheet's rim vertex within this many pixels of the field's edge is set on the edge itself
EDGE_SEEN_ROUND = 0.75     # a ROUND thing's face within this cosine of the eyes' ray is drawn by its known shape's tiles (TILT_COS
                           # for a flat-faced one): at a round limb the picture's last pixel lies well short of the faces seen
                           # edge-on, and the strip between was drawn by nothing (2026-11-15, the dashes in his forearm)
EDGE_SEEN_THIN = 0.15      # a tile drawn as seen sits this share of SEAM_BACK behind its face's own plane, on every thing alike (on
                           # a thing no more than three pixels thick in the picture alone, and the whole of SEAM_BACK on a thick closed
                           # one, until 2026-11-15: that and the shape's own set-in drew a piano's top three centimetres low, a black
                           # band between it and the wall behind it from the camera's side)
EDGE_SEEN_FACE = 0.35      # such a tile takes its colour from the picture's pixels whose hits lie within this many footprints of
                           # its own face's plane
TILE_UNREAD = ("as_seen", "contact", "d_pressed", "d_room", "edge_keep", "expo", "facing", "id", "inner", "inset_v", "kept",
               "known_col", "nrm_face", "nrm_room", "nrm_smooth", "open", "own_wave", "pc", "q_room", "round", "sense_col", "sense_w",
               "sky_lvl", "thing", "uv_now", "wave_id", "wave_radius", "other_lit", "touch_lvl", "rim_late")
                           # what a known shape's tiles carry for the making of them and no material reads: dropped from the
                           # drawn mesh (at the bed, 24.5 million vertices: 5 GB of these against 1.8 GB that is read)
THIN_PX = 6.0              # a round thing under this many of the picture's pixels thick, the way its face turns from the eyes,
                           # has no limb apart from its body: its tiles are not drawn as seen, and its sheet keeps its rim
                           # (the sheet a pixel more, so that no rim is left to tiles that are not drawn). On a ribbon a few
                           # pixels wide the limb's tests pass by chance, and the tiles that passed stood beside the ribbon
                           # as a broken row of dots from the camera's side: a tree's trunk five pixels wide at 82 s of the
                           # player (the audit's O2). Three pixels, for the sheet alone, until 2026-11-16
LIMB_STEP = 3.0            # a rim pixel of a round thing held whole whose neighbouring ray, on another thing, strikes this many
                           # footprints deeper stands on the thing's own silhouette: left out of its sheet, the tiles draw the limb,
LIMB_COS = 0.5             # where its own sheet runs within this cosine of the ray (the surface turning away: not a sharp edge,
                           # where the surface faces the eyes right up to it and no tile draws it; well inside EDGE_SEEN_ROUND)
SHEET_INSET = 3.0          # a sheet's pixel within two pixels of its thing's edge in the picture, on a thing that spans its
                           # distance, takes the picture's colour this many pixels in on its own thing: the render mixes a pixel
                           # beside an edge with what stands next to it, and on a surface seen at a slant that pixel is a long strip
SHEET_TOUCH = 1.0          # a sheet's rim vertex steps outward no farther than this share of the way, along its step, to the
                           # nearest neighbouring hit on another thing: where two things touch (two walls at a corner) a longer
                           # step stood through the other thing as a tooth from behind it; at 1 the two rims meet on the corner
SHEET_NEAR = 4.0           # that cap holds only where the two things touch: the neighbouring hit within this many of the pixel's
                           # own steps to its neighbours on its thing (at a silhouette the hit lies far along the ray and one pixel
                           # off across the step: capped there, every edge against what stands behind it kept the pixels' staircase)
SHEET_CLEAR = 2.0          # the inset colour (SHEET_INSET) is taken only where the pixel this many farther in is on the thing
                           # too: on a strip a few pixels wide the pixel three in is the one beside the strip's other edge
LIMB_VOTE = 12             # a rim pixel of a round thing is left to the tiles (LIMB_COS) by the rim pixels round it: this many
                           # passes of the blur along the grid, about four pixels each way along the rim, and where more than
LIMB_SHARE = 0.5           # this share of them pass the test. A lone one that passes, or a pair, stays in the sheet, and a lone
                           # one that fails goes with the rest
LIMB_IN = 1.0              # a round thing's tile drawn as seen goes where the picture half a tile along the limb either way, this
                           # many pixels in from the limb, shows another thing: at a limb's end (a shade's open top) the tile
                           # overhangs its face's edge across the eyes' ray, and stood over the rim as a lip
LIMB_NEAR = 3.0            # a round thing's wide band of tiles (EDGE_SEEN_ROUND) holds only on the limb's side: where the picture
                           # this many pixels from the tile's place, the way its face turns from the eyes (or half as many), no longer
                           # shows the tile's thing. A faceted shade's face seen at a slant lies whole inside the band, and its tiles
                           # stood over the shade's top rim
SHEET_SMOOTH = 2           # passes of smoothing along a sheet's rim: each rim vertex to the mean of itself and its neighbours on
                           # the rim (set where the pixels round it say the edge lies, it stood a fifth of a pixel off at random, and
                           # on a surface the camera sees at a slant those were teeth)
SUN_MEM_LEVEL = 0.4        # the sun's remembered half at this share of a picture's white (his tenth review: the two halves
                           # read alike at a picture's white beside the seen half's strength)
SHAPE_TILES = 4.0          # a known shape is drawn as tiles, this many per footprint squared scattered over its faces (the scan
                           # lays one per footprint on its grid), each OVERLAP footprints wide, so some twelve tiles lie over any
                           # point and a gap is one pixel in a hundred thousand (three per tile's own area left one in twenty: the
                           # sun's ball and the sky in specks through a crown's far side); each tile drifts on its own, so a
                           # remembered thing shimmers as the picture's memories do (2026-11-12)
SHAPE_GRAIN = 0.0          # no grain on a known shape's tiles (his word of 2026-11-12, rung 2p: a mirage bends an image smoothly and
                           # adds no noise; the 0.3 of grain given each tile that morning, so that flat-coloured tiles slid by the waves
                           # would show a change, was a workaround and read as grain). The memory's unrest is the drift alone: with
                           # the stand-in's flat colours it shows at edges and in shading, with rung 5's textures across the surfaces
SHAPE_EDGE = 0.12          # room metres, and
SHAPE_EDGE_DEG = 2.0       # degrees as seen from the middle of the room: a known shape is cut until no edge of it is longer than
                           # the greater of the two. A shape is carried into the model vertex by vertex, each placed as a ray's hit
                           # there would be; between its vertices a face stays flat, and the placing is no straight line (pressed
                           # toward the glass beyond the knee, flat against the sky until the far field resolves). A wall of one
                           # face 4.5 m long, a piano's top of one face, lay centimetres to decimetres off the picture's own hits on
                           # the same surface wherever part of it stood beyond the knee (2026-11-15: a black band between the
                           # piano's top and the wall behind it)
SHAPE_IN_FOOT = 2.0        # a thing drawn whole by its known shape sits this many of the scan's footprints inside its own surface,
                           # along its own normals, so the picture's splats and the far side draw over it wherever the rays reach it
# the known light on a known shape, a stand-in for the light the mind simulates (rung 6 lights the piece for real): the
# sky's light everywhere, the sun's where a face turns toward it, each in the dawn's colour, at an outdoor level and an
# indoor one (the room is lit by what comes through the window), times an exposure for each (Exposure indoors,
# ExposureOut outdoors, set at render time), so a remembered thing sits as dark or as bright as the picture beside it.
# That exposure is read off the picture itself (known_exposure, 2026-11-12): the brightness of the hits of the eyes' own
# scan that stands in the head that frame, over what their things' known colours give at exposure 1, times
# KNOWN_OVER_SEEN. Until then it was the eye's exposure times a level from the Third-Person probe, which ran five to
# thirteen times brighter than the picture wherever the eye was wide open in a dim room: the room's walls, thought of
# as he sits up at 17 s with the eye at +3 stops, came up blown to white beside a ceiling seen in dusk
SHAPE_SKY_OUT = (2.4, 2.65, 2.5)
SHAPE_SKY_IN = (1.05, 0.8, 0.62)
SHAPE_SUN = (1.47, 1.27, 0.96)   # (1.1, 0.95, 0.72) over the three quarters of the disc clear of the ridge at 70 s, where it was
                                 # calibrated: the sun's share now follows the disc (SunShare, keyed), nought before first light
KNOWN_OVER_SEEN = 1.62     # a known shape is drawn this many times brighter than the middle of the picture beside it: the
                           # level his reviews settled on (his eleventh, 2026-11-11: memory's colours slightly too dim). It is
                           # the outdoor shapes at the window beat (70 s) and the chime's nightstand as he turns (92.8 s) as they
                           # stood before, both within a twentieth
KNOWN_OUT_OVER_IN = 3.4    # where the picture holds no outdoor hits, or no indoor ones, the missing exposure is the other's by
                           # this ratio, the one measured at the window beat
KNOWN_OWN = 0.3            # the mind's own light: the exposure of a known shape while no picture stands in the head, before the
                           # eyes first open. The alarm's nightstand and bed stood between 0.24 and 0.41 by the old rule
CHEST_CLEAR = 0.85         # the chest's tiles, seen or known, clear by this share while the heart or the lungs are thought of, so
                           # the organs inside show (his specification: drawn while thought of)
CHORD_WIDE = 3.0           # a chord splat's width in footprints: wider than its pixel, so neighbouring chords whose hits lie at
                           # different depths along the ray still overlap from the side (a faceted crown steps in depth at its rim)
SHAPE_REACH = 50.0         # room metres: a thing larger than this (the ground, the range, the sky's shell) has no shape the mind
                           # draws whole
SOUL_FLOOR = 0.1           # the soul's light while nothing is willed (asleep): dim, never out
# the mind's simulation of its own soul in the model (his eleventh review of 2026-11-11): a disc behind and above the
# simulated head as the soul is behind the ghost's, white, never seen and so never tested; its presence is the
# character's own willfulness, rising at each act of will (the timeline's will words) and fading as he goes
# through the motions, on a floor, and gone as far as he is not aware
MINI_SOUL_FLOOR = 0.12
MINI_SOUL_RISE = 0.3       # seconds for the presence to rise at a word of will
MINI_SOUL_HOLD = 1.0       # seconds it stands
MINI_SOUL_FALL = 5.0       # seconds over which it fades to the floor
MINI_SOUL_STRENGTH = 4.0
MINI_SOUL_DIR = Vector((-1.0, 0.0, 1.0)).normalized()   # in the head's frame: behind and above
SOUL_NEAR = (0.22, 0.40)   # model metres from the rendering camera within which the soul's light fades out: the orbit test
                           # camera passes 18 cm behind it with the soul on its axis (a white frame); the piece's road never comes near
# the ten things the mind can think of (Think0 to Think9, keyed from the engine's thoughts), and which of them
# a room object's tag falls under: 0 bed, 1 table (and what stands on it), 2 outside, 3 the east wall and
# the window, 4 floor, 5 ceiling, 6 west wall, 7 north, 8 south, 9 other (his own body among it)
REGION_OTHER = 9
REGION_GROUP = {"bed": 0, "table": 1, "table_far": 1, "table_edge": 1, "phone": 1,
                "outside": 2, "ground": 2, "ridge": 2, "sun": 2, "sky": 2,
                "window": 3, "sill": 3, "wall_e": 3, "floor": 4, "rug": 4, "rug_edge": 4, "ceiling": 5,
                "wall_w": 6, "wall_n": 7, "wall_s": 8, "body": 9}
GROUP_TAGS = {}
for _tag, _group in REGION_GROUP.items():
    GROUP_TAGS.setdefault(_group, []).append(_tag)
GHOST_BODY = False         # the glass body under the glass head: left out while the camera only ever looks into the head (rung
                           # 2d: to expose the vision part), built when the True camera opens on the whole figure (rungs/rung2.py
                           # --true-open, his fourteenth round of 2026-11-14): then the two seconds between which it gives way
                           # as the camera arrives at the head, whole before the first and gone from the second, so that from
                           # the camera's held place nothing but the head's glass lies over the mind's model
BODY_SHOW_PATH = 'nodes["BodyShow"].outputs[0].default_value'
BACK_PUSH = 1.0            # the backdrop drawn this much farther than the live picture (1.012 until his eighth review of 2026-11-10:
                           # it is culled wherever the live picture has its hit, so it needs no depth of its own, and a strip of
                           # it filling a hole in the picture must sit in that hole's own depth, or a camera off the eyes sees a seam)
BACKDROP_SHARE = 1.0       # the backdrop scan's size as a share of the scan's (0.5 until his seventh review: culled behind the
                           # live picture at half its size, it left a staircase of memory round every crown)
WINDOW_MARGIN = 0.04       # metres of soft edge at the window's jambs and sill on the backdrop
RESOLVE_RISE = 5.0         # seconds of looking at the far field for its depth to resolve from flat against the sky
RESOLVE_FALL = 60.0        # and how slowly that knowledge goes once he looks away
SUN_FLAT_IN = -0.05        # unresolved, the sun's disc lies this many believed metres inside the sky's dome
SUN_FLAT_DEPTH = 0.08      # and is this share of its radius deep; resolved, it is a ball beyond the sky
SUN_BALL_DEG = 6.0         # the sun as the mind holds it, a ball this wide from the eyes: larger than the sky's disc
SUN_BALL_STRENGTH = 6.0
MEM_SHRINK = 0.985         # a picture from another time is drawn this much nearer the eyes than the live one, so the two never
                           # coincide while one fades into the other; a memory completing this frame's picture (the backdrop,
                           # the sky, the far sides) sits at its own depth, and at the last picture's while the eyes stay shut
MEM_GREY_TAU = 2.5         # seconds of a memory's age over which its colour drains toward grey (every memory alike)
COMPLETES_OLD = True       # True: what completes this frame's picture (the ground, the range and the sky behind near things) is
                           # drawn in memory's oldest look, as a thing's unseen side is. False: at age nought, close to the seen
                           # look, as it was until 2026-11-16. The audit's O7: he saw the two ways side by side and gave his
                           # word that day, "whichever is more consistent": every other thing his eyes do not see has memory's
                           # look, and this was the one drawn as seen
HELD_TILES = True          # the last picture the eyes held has tiles of its own (MemoryShapesLast) for the faces of its
                           # FLAT-faced things that the eyes saw nearly edge-on, as the live picture has: without them the
                           # remembered window sill's top stood in white wedges, the outside showing through the gaps between
                           # its rows (the audit's O1). Its round things are drawn as before: their rim in the sheet, their
                           # limb closed by chords. False: no such tiles
BACK_BEHIND = 0.005        # the backdrop this share of the glass radius farther from the RENDERING camera than the picture it completes,
                           # and
SKY_BEHIND = 0.01          # the remembered sky this share of the glass radius farther from the RENDERING camera, along the camera's
                           # own line of sight (so nothing moves in the picture): at the picture's own depth it shares every pixel
                           # with a range that still lies flat against the sky, and the two were drawn in patches
SKY_PUSH = 1.0             # the remembered sky at the picture's own depth (1.01 until his ninth review of 2026-11-10: the dome is
                           # beyond the range by its believed distance already, and the push read as a second shell)
SKY_FAR = 1000.0           # room metres: a backdrop hit nearer than this is the range or the ground, not the sky
SAME_PICTURE = 6           # frames: a thought's picture this close to the last picture the eyes held is that picture
HORIZON_SOFT = 0.004       # the sine of elevation over which the remembered dome passes from the ground's colour to the sky's
# ---- the senses on the simulated body (rung 2p, his specification of 2026-11-12) ----
# A sense lights the part it arises on, on the mind's own body, seen or not: the part's seen tiles, its remembered
# tiles and its known shape alike take the sense's colour at the sense's strength (the sense light, from the sense
# table); touch lights the patch of a part that meets another thing, and no more of it (ContactBody, below); a
# moving or a warm or a cold part glows at its rim (the outline); a touch sends a lightning to the head;
# the sounds' rings; the gravity arrow in the simulated skull. The sense table is one picture, a row per frame and a
# column per part and field, which the geometry samples at the frame and the hit's part (sense_table)
WAVE_GLYPHS = 12           # rings for the sounds: one per tenth of a second of a sound (engine.WAVE_SLOTS)
RING_INNER = 0.92          # a ring's inner radius as a share of its outer: the band its glow fades over, from a bright line at
                           # the outer edge inward, as a radar's sweep trails (his word of 2026-11-12: the rings glow gently).
                           # Every ring he saw until 2026-11-13 had a band of 0.04 of its radius: the shape key that thins
                           # a ring (rung 1's, mindscene._annulus) stands at 1 when made and nothing here keyed it, so the
                           # 0.28 written here never showed. His word of that day on the rings he saw: slightly too thin,
                           # double their size. So 0.08, and the key set to nought.
RING_EDGE = 0.5            # the share of the ring's band, from the inner edge, where the bright line begins: its outer half
RING_GAIN = 0.32           # the ring's light at full loudness and awareness; the band's soft part at RING_SOFT of it. (The
                           # same word: too strong, cut its brightness in half. At 2.2 the bright line was thinner than a
                           # render pixel, which shows a line's light summed and not its peak; this line is wider than a
                           # pixel, so half of what he saw is set by the brightest pixel across a ring.)
RING_SOFT = 0.45
SENSE_MIX = engine.SENSE_MIX   # a sense's colour on a part takes this share and the part's own colour the rest, wherever the sense
                           # is on at all (his word of 2026-11-12: 30 to 50 percent of the actual colour kept); the sense's strength
                           # sets the brightness, not the blend. The share comes per part from the engine through the sense table's
                           # tint (touch at this share, a hurting ear and the eyes in the glare at 1, the organs at ORGAN_MIX)
SENSE_ON = 0.1             # the strength at which the blend is fully in
SENSE_LIFT = 1.5           # a sense-lit tile is brighter by this share of its light at full strength
MEM_COLOUR_PATHS = [f'nodes["Col{i}"].outputs[0].default_value' for i in range(10)]
MINI_SOUL_AWAY = 3.0       # the mind's own soul stands this many times its distance farther from the simulated head, at the
                           # glass, while he is not aware, and comes back as awareness rises (his word of 2026-11-12: the soul
                           # returning to the body from far away as he gets his bearings)
OUTLINE_GAIN = 1.2         # the outline glow's strength at full, at the middle of its band
GLOW_ALPHA = 1.2           # a touch's glow covers what is behind it by this times its strength, in full from 0.83: a resting
                           # touch (a quarter) lets the bed show through it, a sharp one stands solid
GLOW_GAIN = 1.5            # the glow's own light: over 1, so it blooms
GLOW_EDGE = 0.9            # a touch's glow is whole where its layer faces the camera this squarely or more (the cosine of
                           # the angle between the layer and the line of sight) and fades to nothing at the layer's outline,
GLOW_SOFT = 2.0            # by this power: across a limb seen from the side, nearly the whole width is the fade
SENSE_SHIMMER = 0.22       # a body sense's glow wavers in brightness by this share either way (his word of 2026-11-13: a
                           # shimmer, not as strong as memory's, without moving anything, in the colour),
SENSE_SHIMMER_HUE = 0.025  # and its colour turns by this share of the colour wheel either way,
SENSE_SHIMMER_CELLS = 14.0 # in a slow noise of this many cells a room metre over the body,
SENSE_SHIMMER_SPEED = 1.2  # changing by this many cells a second
OUTLINE_PEAK = 0.6         # the outline glow is a band of light along the part's outline: strongest where the layer faces
                           # the camera this squarely (the same cosine), nothing at the layer's own outline and nothing where
OUTLINE_SOFT = 1.5         # it faces the camera full on; the power that shapes the fall either way
OUTLINE_OUT = 0.5          # the outline surface stands this many footprints outside the part's surface, over its tiles,
OUTLINE_HALO = 0.018       # and this many room metres farther out (his word of 2026-11-13: soft edges, glows): the layer's
                           # light fades to nothing at the layer's outline, which lies outside the body's own, so a glow
                           # has no edge where the body ends
LIGHTNING_WIDTH = 0.0019   # the spark's radius, room metres (scaled with the model). 0.0031 until his twelfth round of 2026-11-13
                           # (thinner, a quarter to a half); the blue sheath is LIGHTNING_HALO times it and thins with it.
                           # Before that 0.0025, until the sparks' numbers were
                           # written through a fine key writer (2026-11-13): the coarse one dropped every change under a
                           # thousandth, so the width and the throw stood at what the model's scale made them at each
                           # spark's first use (1/24), a quarter to a third over what was written here at the reach's scale
                           # (1/33). This and LIGHTNING_JAG are set to what he saw and passed there.
LIGHTNING_GAIN = 10.0      # bright enough to bloom: a white core in a blue glow
LIGHTNING_JAG = 0.0175     # room metres a point of the spark is thrown off its path, nought at its two ends: inside the limb
LIGHTNING_POINTS = 44      # few enough that the throws make corners, a zigzag and no wiggle
LIGHTNING_HALO = 7.0       # the blue sheath round the spark's white core, this many times its radius,
LIGHTNING_HALO_SHARE = 0.22   # at this share of the core's light, fading to nothing at its own edge
LIGHTNING_HALO_SOFT = 2.2     # (the power of how squarely the sheath faces the camera: its light gathers round the core)
LIGHTNING_CORE_COLOUR = (0.85, 0.93, 1.0)
LIGHTNING_HALO_COLOUR = (0.28, 0.52, 1.0)   # (his word of 2026-11-13: lightning has a bluish white glow, whatever the sense)
LIGHTNING_PULL = 0.20      # room metres every point of the spark is drawn toward the rendering camera along its own line of
                           # sight: its place in the picture is unchanged, and the limb it runs inside does not hide it
LIGHTNING_TAIL = 0.75      # behind its front the spark's light falls away over this share of the path's length, down to
LIGHTNING_TAIL_FLOOR = 0.12   # this share of it: the front is the bright thing, so a single frame shows which way it runs
                           # (his word of 2026-11-13, tenth round: one spark from the point of contact to the head)
# When a spark strikes (his word of 2026-11-13: at every new contact, each tap, every case): read off the contact itself.
# Since his thirteenth round pair by pair (LidarScene.read_pairs, triview/touches.py, strikes_of_pairs); the reading part
# by part before it (LidarScene.read_contact, strikes_of, with the two thresholds below) is kept and no longer called.
STRIKE_ON = 0.9            # a strike: a body part's contact (the most of its vertices') rises to this, a full touch,
STRIKE_OFF = 0.3           # after it has fallen to this, clear of everything by some three centimetres. (The first trigger,
                           # how fast new skin comes into contact, struck at every slide of an arm along the pillow and at
                           # each stroke of the rub, 134 times through the piece, and hardly at the knock.)
STRIKE_SAME = 0.15         # seconds within which the parts of one limb landing together are one strike, the farthest part's
STRIKE_TIE = 0.2           # of those, touches whose gaps closed within this of each other, metres a second, are as hard as each other
ARROW_LEN = 1.125          # the gravity arrow's length as a share of the head's radius (1.5 until his twelfth round of
                           # 2026-11-13: a quarter smaller)
ARROW_WIDTH = 0.0105       # half its shaft's width, room metres (0.014 until then); its head three times as wide
ARROW_DEPTH = 0.8          # half its depth as a share of half its shaft's width: an extruded arrow, a solid thing, like a
                           # rectangular prism with an arrow's point (the same word: not a revolved arrow, not a flat one)
ARROW_CUTS = 24            # the cuts along its shaft, so the ripple bends it smoothly
ARROW_TURN = math.radians(28.0)   # its broad face is turned about its length to the rendering camera and this much on, so one
                           # of its sides shows and it reads as solid
ARROW_PULSE = 1.5          # the ripple's crests that pass a point of it in a second, from its tail toward its point (the same
ARROW_RIPPLE = 0.17        # word: a ripple in the direction it points, and no change of colour); a crest widens it by this
                           # share (0.28 until his thirteenth round: the pulse 30 to 50 percent less),
ARROW_RIPPLE_WAVES = 1.25  # and this many crests stand along it at once. Its size and its light no longer pulse (the
                           # eleventh round's pulse of the whole arrow, which he found too much; before it bands of light)
ARROW_LOW = 0.6            # its light: its own colour as a light of this strength where balance is not attended, and of
ARROW_HIGH = 1.7           # this where it is attended in full; each face shaded from ARROW_SHADE of that to all of it by
ARROW_SHADE = 0.5          # how it stands to a light held above and beside the camera. Opaque: not see-through (the same word)
ARROW_SHOW = 0.03          # it is there from this much of balance's attention times his awareness: under it the arrow shrinks
                           # to nothing (asleep), since an opaque thing cannot fade
SPARK_FLASH_GAIN = 1.6     # the part a spark comes from flashes in the spark's white for as long as the spark lives: this
                           # many times a white surface's light at the spark's full light, over the part's skin on the
                           # glow's layer, soft at the layer's outline (his word of 2026-11-13, eleventh round). At 4 the
                           # knock's flash and the pain's were one blown white ball twice the hand's size
PAIR_BAND = 0.1            # two senses on one patch of skin: the stronger shows in its own colour, and they mix only
                           # where their strengths lie within this share of each other. (Mixed by their strengths, a
                           # touch's magenta and warmth's orange made red, pain's colour, on both hands at the sill)
SENSE_FIELDS = 5           # the sense table's fields per part: 0 the sense light (colour, strength), 1 the tint and the scale,
                           # 2 the outline (colour, strength), 3 touch (its colour, its level on the part), 4 the temperature
                           # (warmth's level in red, the cold air's in green)
# Warmth works as touch does (his word of 2026-11-13: on the outside, where it affects): a glow on the skin the source
# reaches. ContactBody carries, per vertex, sun (the sun's rays reach it) and air (the window's air does).
REACH_FACE = 0.35          # a source reaches the skin in full where the skin faces it this squarely or more (the cosine of the
                           # angle between the skin's outward normal and the way to the source), not at all where it turns away
REACH_LIFT = 0.004         # room metres off the skin a ray toward the source starts, clear of the skin's own surface
SUN_RAY = 6000.0           # room metres a ray toward the sun runs: past the range, short of the sky's shell
REACH_BLUR = 1             # times what a source reaches is spread over neighbouring vertices: a shade's edge on the skin is
                           # softened by one step of the body's cut (at 3 the shade of the raised hand on the face was gone)
# Touch is contact (his word of 2026-11-12: one rule for everything that touches him, and only the patch that is touched).
# A point of a body part's surface is touched where it lies within CONTACT_SKIN of another thing's surface, or inside
# another thing's closed shape (a soft thing's stand-in does not give way, so a body sunk into the mattress's box is
# pressed by the mattress there), or where the middle of the body part at that point lies inside the thing's closed
# shape: the thing has given way and wraps the part there, so its whole girth is touched (legs lying in a blanket's
# slab are covered by the blanket, though their tops stand out of the slab). Another thing is every mesh of the room,
# and every body part but those joined to this one at one joint and those its stand-in shape is fused with
# (tags.own_parts; until his thirteenth round every part within two joints was left out). Worked out once a frame on ContactBody, the body's own shapes cut finer than CONTACT_EDGE, which
# every surface of the model reads at its own points
CONTACT_SKIN = (0.01, 0.04)    # room metres: touched in full nearer than the first, not at all beyond the second
CONTACT_EDGE = 0.03            # room metres: the longest edge the body's shapes keep for the test
CONTACT_HOLD = 0.05            # room metres: a remembered hit farther than this from the body as it is now has no touch
CONTACT_FULL = (0.35, 0.65)    # the contact over which a patch's rim comes in: nothing under the first, in full from the second
INNER_SKIN = 0.004             # room metres: a point of one body piece deeper than this inside another piece is not skin
CONTACT_RIM = 0.6              # a known shape's tile lit by touch alone is drawn from this share of the part's touch level: under
                               # it the tile is left out, where it was drawn opaque and dark, a black fringe round every patch
SENSES_PATH = 'nodes["Senses"].outputs[0].default_value'
COVER_PATH = 'nodes["Cover"].outputs[0].default_value'
UNWIPE_PATH = 'nodes["Unwipe"].outputs[0].default_value'
LIVE_PATH = 'nodes["Live"].outputs[0].default_value'
LIVE_A_PATH = 'nodes["LiveA"].outputs[0].default_value'
STAND_PATH = 'nodes["Stand"].outputs[0].default_value'
GREY_PATH = 'nodes["Grey"].outputs[0].default_value'
STRENGTH_PATH = 'nodes["Strength"].outputs[0].default_value'
MEM_PATH = 'nodes["Mem"].outputs[0].default_value'
MEM_BRIGHT_PATH = 'nodes["MemBright"].outputs[0].default_value'
SEEN_PATH = 'nodes["Seen"].outputs[0].default_value'
FRAME_PATH = 'nodes["MemFrame"].outputs[0].default_value'
VISIBLE_PATH = 'nodes["Visible"].outputs[0].default_value'
RESOLVE_PATH = 'nodes["Resolve"].outputs[0].default_value'
WILL_PATH = 'nodes["Will"].outputs[0].default_value'
NEAR_PATH = 'nodes["Near"].outputs[0].default_value'


def _placeholder_exr(path):
    """An 8 by 8 float EXR of zeros, for the position sequence before its frames exist."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    img = bpy.data.images.new("ScanPlaceholder", 8, 8, alpha=True, float_buffer=True)
    img.filepath_raw = str(path)
    img.file_format = "OPEN_EXR"
    img.save()
    bpy.data.images.remove(img)
    return path


def _write_exr(path, arr):
    """A float RGBA picture (rows by columns by 4, row 0 at the bottom) written as an EXR."""
    path = pathlib.Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    h, w = arr.shape[0], arr.shape[1]
    # is_data: a float picture made without it is saved to EXR through the display curve in 5.2 (the sense table's red
    # (1, 0.12, 0.06) came back (1, 0.38, 0.27), its blend share 0.6 as 0.8, found 2026-11-12); as data it is written raw
    img = bpy.data.images.new("ExrWrite", w, h, alpha=True, float_buffer=True, is_data=True)
    img.pixels.foreach_set(np.ascontiguousarray(arr, dtype=np.float32).ravel())
    img.filepath_raw = str(path)
    img.file_format = "OPEN_EXR"
    img.save()
    bpy.data.images.remove(img)
    return path


def _blank_exr(path, w, h):
    """A blank float picture of the given size, for the sense table before the bake writes it."""
    return _write_exr(path, np.zeros((h, w, 4), dtype=np.float32))


def _picture(path, data):
    """A picture's pixels as rows from the bottom, four channels, as stored: a colour picture's values are still in
    its display curve."""
    img = bpy.data.images.load(str(path), check_existing=False)
    if data:
        img.colorspace_settings.name = "Non-Color"
    w, h = img.size
    px = np.empty(w * h * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(h, w, 4)


def known_exposure(col_path, idx_path, pos_path, colours, room_size, every=3):
    """The known light's level for one frame, read off the eyes' own scan of it (2026-11-12): the exposure at which a
    known shape sits as dark or as bright as the picture beside it. Over the scan's hits, every third pixel each way,
    whose thing has a known colour: the hit's brightness in the picture (its display curve undone) over the brightness
    its thing has by its known colour under the sky's level at exposure 1, the indoor level for a hit inside the
    room's box and the outdoor one beyond it, as shape_nodes lights a face. Returns the median of that ratio over the
    indoor hits and over the outdoor ones, each None where under a thousand such hits are in the picture, or None
    altogether where a picture is missing. colours: the table of things' known colours by index."""
    paths = [pathlib.Path(q) for q in (col_path, idx_path, pos_path)]
    if not all(q.exists() for q in paths):
        return None
    pic = _picture(paths[0], False)[::every, ::every, :3].astype(np.float64)
    idx = np.rint(_picture(paths[1], True)[::every, ::every, 0]).astype(np.int64)
    pos = _picture(paths[2], True)[::every, ::every, :3].astype(np.float64)
    if pic.shape[:2] != idx.shape or idx.shape != pos.shape[:2]:
        return None
    lum = np.array((0.2126, 0.7152, 0.0722))
    seen = np.where(pic <= 0.04045, pic / 12.92, ((pic + 0.055) / 1.055) ** 2.4) @ lum
    colours = np.asarray(colours, dtype=np.float64)
    known = colours[np.clip(idx, 0, len(colours) - 1)]
    W_, D_, H_ = room_size
    inside = ((np.abs(pos[..., 0] - W_ / 2.0) < W_ / 2.0 + 0.05) & (np.abs(pos[..., 1] - D_ / 2.0) < D_ / 2.0 + 0.05)
              & (np.abs(pos[..., 2] - H_ / 2.0) < H_ / 2.0 + 0.05))
    has = (idx > 0) & (idx < len(colours))
    out = []
    for mask, level in ((inside & has, SHAPE_SKY_IN), (~inside & has, SHAPE_SKY_OUT)):
        model = (known * np.array(level)) @ lum
        mask = mask & (model > 0.02)
        out.append(float(np.median(seen[mask] / model[mask])) if int(mask.sum()) >= 1000 else None)
    return tuple(out)


def sequence(name, folder, pattern, make_placeholder, placeholder_dir, colorspace):
    """An image sequence datablock: the folder's first numbered frame, or a placeholder; the render
    repoints it (rungs/rung2.py) once the frames exist."""
    folder = pathlib.Path(folder)
    first = None
    if folder.exists():
        found = sorted(folder.glob(pattern))
        first = found[0] if found else None
    if first is None:
        first = make_placeholder(pathlib.Path(placeholder_dir) / pattern.replace("*", "0001"))
    img = bpy.data.images.load(str(first), check_existing=False)
    img.name = name
    img.source = "SEQUENCE"
    img.colorspace_settings.name = colorspace
    return img


def repoint(img, folder, pattern):
    """Point a sequence at the folder's first numbered frame, if any; returns the frames found."""
    folder = pathlib.Path(folder)
    found = sorted(folder.glob(pattern)) if folder.exists() else []
    if found:
        img.filepath = str(found[0])
        img.source = "SEQUENCE"
        img.reload()
    return found


def region_of(tag, part=None):
    """The thing group a room object's tag falls under; a body part is other."""
    if part is not None:
        return REGION_OTHER
    return REGION_GROUP.get(tag, REGION_OTHER)


def scan_material(name, fade, field_v_share, upper_share=UPPER_SHARE, lids=True, memory=False, side=0, additive=False, senses=False,
                  colour_share=False):
    """The splats' look: the colour their ray brought back, stored on them by the geometry; the lids'
    wipe dimming the live picture (lids); a Live value that takes the live picture away while the eyes
    stay shut, or brings a memory up; Grey draining the colour; Strength for a sense's attention on a
    memory; from the side the eyes never see, dimmer, and clear while the rendering camera is near
    (BACK_CLEAR); fades where the rendering camera sees a splat edge-on or has it within reach; gate
    from the geometry for the backdrop's soft edge."""
    mat = bpy.data.materials.new(name)
    nt, out = mats._clear(mat)
    col = nt.nodes.new("ShaderNodeAttribute")
    col.attribute_type = "GEOMETRY"
    col.attribute_name = "scan_col"
    uv = nt.nodes.new("ShaderNodeAttribute")
    uv.attribute_type = "GEOMETRY"
    uv.attribute_name = "scan_uv"

    def value(nm, v):
        n = nt.nodes.new("ShaderNodeValue")
        n.name = nm
        n.label = nm
        n.outputs[0].default_value = v
        return n.outputs[0]

    live = value("Live", 0.0 if memory else 1.0)
    grey = value("Grey", 1.0 if memory else 0.0)
    strength = value("Strength", 1.0)
    # the colour, drained by Grey toward its own grey (the grey of the same brightness), MEM_DESAT of the way at
    # full Grey: a memory keeps its light and loses its colour (his eleventh review of 2026-11-11)
    desat = nt.nodes.new("ShaderNodeMath"); desat.operation = "MULTIPLY"
    nt.links.new(grey, desat.inputs[0])
    desat.inputs[1].default_value = MEM_DESAT
    desat_out = desat.outputs["Value"]
    sense_s = None
    if senses:
        # a tile a sense lights (sense_s from the geometry, rung 2p) keeps the sense's colour undrained and is brighter
        # by SENSE_LIFT of the sense's strength
        ss = nt.nodes.new("ShaderNodeAttribute"); ss.attribute_type = "GEOMETRY"; ss.attribute_name = "sense_s"
        sense_s = ss.outputs["Fac"]
        # how far the sense is on: in full from SENSE_ON of strength
        s_div = nt.nodes.new("ShaderNodeMath"); s_div.operation = "DIVIDE"
        nt.links.new(sense_s, s_div.inputs[0])
        s_div.inputs[1].default_value = SENSE_ON
        s_on = nt.nodes.new("ShaderNodeMath"); s_on.operation = "MINIMUM"
        nt.links.new(s_div.outputs["Value"], s_on.inputs[0])
        s_on.inputs[1].default_value = 1.0
        sense_on = s_on.outputs["Value"]
        keep = nt.nodes.new("ShaderNodeMath"); keep.operation = "SUBTRACT"
        keep.inputs[0].default_value = 1.0
        nt.links.new(sense_on, keep.inputs[1])
        kept = nt.nodes.new("ShaderNodeMath"); kept.operation = "MULTIPLY"
        nt.links.new(desat_out, kept.inputs[0])
        nt.links.new(keep.outputs["Value"], kept.inputs[1])
        desat_out = kept.outputs["Value"]
    if colour_share:
        # a known shape whose colour has not come back yet (mem_colour from the geometry, 0 to 1) is drained to its grey in full:
        # the memory's shimmer with none of its colour (his word of 2026-11-12)
        mc = nt.nodes.new("ShaderNodeAttribute"); mc.attribute_type = "GEOMETRY"; mc.attribute_name = "mem_colour"
        rest = nt.nodes.new("ShaderNodeMath"); rest.operation = "SUBTRACT"
        rest.inputs[0].default_value = 1.0
        nt.links.new(desat_out, rest.inputs[1])
        back = nt.nodes.new("ShaderNodeMath"); back.operation = "MULTIPLY"
        nt.links.new(rest.outputs["Value"], back.inputs[0])
        nt.links.new(mc.outputs["Fac"], back.inputs[1])
        d_full = nt.nodes.new("ShaderNodeMath"); d_full.operation = "SUBTRACT"
        d_full.inputs[0].default_value = 1.0
        nt.links.new(back.outputs["Value"], d_full.inputs[1])
        desat_out = d_full.outputs["Value"]
    lum = nt.nodes.new("ShaderNodeVectorMath"); lum.operation = "DOT_PRODUCT"
    nt.links.new(col.outputs["Color"], lum.inputs[0])
    lum.inputs[1].default_value = (0.2126, 0.7152, 0.0722)
    own_grey = nt.nodes.new("ShaderNodeCombineColor")
    for ch in ("Red", "Green", "Blue"):
        nt.links.new(lum.outputs["Value"], own_grey.inputs[ch])
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    nt.links.new(desat_out, mixc.inputs["Factor"])
    nt.links.new(col.outputs["Color"], mixc.inputs[6])
    nt.links.new(own_grey.outputs["Color"], mixc.inputs[7])
    # the lids: the upper lid down over upper_share of the field, the lower up over the rest
    bright = strength
    if lids:
        cover = value("Cover", 0.0)
        sep = nt.nodes.new("ShaderNodeSeparateXYZ")
        nt.links.new(uv.outputs["Vector"], sep.inputs["Vector"])
        h = field_v_share
        top = nt.nodes.new("ShaderNodeMath"); top.operation = "MULTIPLY_ADD"
        nt.links.new(cover, top.inputs[0])
        top.inputs[1].default_value = -upper_share * 2.0 * h
        top.inputs[2].default_value = 0.5 + h
        bot = nt.nodes.new("ShaderNodeMath"); bot.operation = "MULTIPLY_ADD"
        nt.links.new(cover, bot.inputs[0])
        bot.inputs[1].default_value = (1.0 - upper_share) * 2.0 * h
        bot.inputs[2].default_value = 0.5 - h
        under_top = nt.nodes.new("ShaderNodeMath"); under_top.operation = "LESS_THAN"
        nt.links.new(sep.outputs["Y"], under_top.inputs[0])
        nt.links.new(top.outputs["Value"], under_top.inputs[1])
        over_bot = nt.nodes.new("ShaderNodeMath"); over_bot.operation = "GREATER_THAN"
        nt.links.new(sep.outputs["Y"], over_bot.inputs[0])
        nt.links.new(bot.outputs["Value"], over_bot.inputs[1])
        open_ = nt.nodes.new("ShaderNodeMath"); open_.operation = "MULTIPLY"
        nt.links.new(under_top.outputs["Value"], open_.inputs[0])
        nt.links.new(over_bot.outputs["Value"], open_.inputs[1])
        # the lids dim the picture to a floor rather than cutting it away: eight blinks in half a
        # minute that cut it to nothing read as a strobe (his review of 2026-11-08)
        lid = nt.nodes.new("ShaderNodeMath"); lid.operation = "MULTIPLY_ADD"
        nt.links.new(open_.outputs["Value"], lid.inputs[0])
        lid.inputs[1].default_value = 1.0 - LID_FLOOR
        lid.inputs[2].default_value = LID_FLOOR
        lid_out = lid.outputs["Value"]
        if memory:
            # a memory that completes the picture comes out from under the lids as the live picture goes (Unwipe, keyed:
            # nought while the live picture stands, one once it has gone): its lid factor passes from the one under the
            # wipe to the one with the lids open, lid + (lid_open - lid) * Unwipe, so with Unwipe at one it is drawn
            # exactly as with no wipe (a place outside the eyes' own band stays at the lids' floor either way). Until
            # 2026-11-14 the wipe was dropped in the one frame the eyes became long shut, and the completion stood
            # bright at a stroke
            unwipe = value("Unwipe", 0.0)
            in_top = nt.nodes.new("ShaderNodeMath"); in_top.operation = "LESS_THAN"
            nt.links.new(sep.outputs["Y"], in_top.inputs[0])
            in_top.inputs[1].default_value = 0.5 + h
            in_bot = nt.nodes.new("ShaderNodeMath"); in_bot.operation = "GREATER_THAN"
            nt.links.new(sep.outputs["Y"], in_bot.inputs[0])
            in_bot.inputs[1].default_value = 0.5 - h
            open_0 = nt.nodes.new("ShaderNodeMath"); open_0.operation = "MULTIPLY"
            nt.links.new(in_top.outputs["Value"], open_0.inputs[0])
            nt.links.new(in_bot.outputs["Value"], open_0.inputs[1])
            lid_0 = nt.nodes.new("ShaderNodeMath"); lid_0.operation = "MULTIPLY_ADD"
            nt.links.new(open_0.outputs["Value"], lid_0.inputs[0])
            lid_0.inputs[1].default_value = 1.0 - LID_FLOOR
            lid_0.inputs[2].default_value = LID_FLOOR
            rest_l = nt.nodes.new("ShaderNodeMath"); rest_l.operation = "SUBTRACT"
            nt.links.new(lid_0.outputs["Value"], rest_l.inputs[0])
            nt.links.new(lid_out, rest_l.inputs[1])
            lifted = nt.nodes.new("ShaderNodeMath"); lifted.operation = "MULTIPLY_ADD"
            nt.links.new(rest_l.outputs["Value"], lifted.inputs[0])
            nt.links.new(unwipe, lifted.inputs[1])
            nt.links.new(lid_out, lifted.inputs[2])
            lid_out = lifted.outputs["Value"]
        if lids == "field":
            # a remembered tile is under the lids only where it lies inside the eyes' field (in_field from the geometry:
            # the back of a thing he is looking at); what he remembers outside his field, behind him, has no lid over
            # it and keeps its light through a blink (the audit of 2026-11-15: the lids darkened the remembered ground
            # and sky behind near things, by his ninth review, and not the remembered back of a thing beside them)
            inf = nt.nodes.new("ShaderNodeAttribute"); inf.attribute_type = "GEOMETRY"; inf.attribute_name = "in_field"
            # (and never his own body's tiles, nor a tile a sense lights: he feels those, and the lids cover sight alone)
            body_a = nt.nodes.new("ShaderNodeAttribute"); body_a.attribute_type = "GEOMETRY"; body_a.attribute_name = "own_body"
            not_body = nt.nodes.new("ShaderNodeMath"); not_body.operation = "SUBTRACT"
            not_body.inputs[0].default_value = 1.0
            nt.links.new(body_a.outputs["Fac"], not_body.inputs[1])
            amount = nt.nodes.new("ShaderNodeMath"); amount.operation = "MULTIPLY"
            nt.links.new(inf.outputs["Fac"], amount.inputs[0])
            nt.links.new(not_body.outputs["Value"], amount.inputs[1])
            amount_out = amount.outputs["Value"]
            if sense_s is not None:
                not_sense = nt.nodes.new("ShaderNodeMath"); not_sense.operation = "SUBTRACT"
                not_sense.inputs[0].default_value = 1.0
                nt.links.new(sense_on, not_sense.inputs[1])
                amount2 = nt.nodes.new("ShaderNodeMath"); amount2.operation = "MULTIPLY"
                nt.links.new(amount_out, amount2.inputs[0])
                nt.links.new(not_sense.outputs["Value"], amount2.inputs[1])
                amount_out = amount2.outputs["Value"]
            less = nt.nodes.new("ShaderNodeMath"); less.operation = "SUBTRACT"
            nt.links.new(lid_out, less.inputs[0])
            less.inputs[1].default_value = 1.0
            in_f = nt.nodes.new("ShaderNodeMath"); in_f.operation = "MULTIPLY_ADD"
            nt.links.new(less.outputs["Value"], in_f.inputs[0])
            nt.links.new(amount_out, in_f.inputs[1])
            in_f.inputs[2].default_value = 1.0
            lid_out = in_f.outputs["Value"]
        m = nt.nodes.new("ShaderNodeMath"); m.operation = "MULTIPLY"
        nt.links.new(lid_out, m.inputs[0])
        nt.links.new(strength, m.inputs[1])
        bright = m.outputs["Value"]
    # from the side the eyes never see a splat is dimmer, and drawn only while the rendering camera is
    # far (below, with the alpha): the same for every thing. A chord splat (chord 1 from the geometry) has no
    # such side: it stands for the thing's surface along the ray and is never seen from inside the thing
    geom = nt.nodes.new("ShaderNodeNewGeometry")
    chd0 = nt.nodes.new("ShaderNodeAttribute"); chd0.attribute_type = "GEOMETRY"; chd0.attribute_name = "chord"
    not_chord = nt.nodes.new("ShaderNodeMath"); not_chord.operation = "SUBTRACT"
    not_chord.inputs[0].default_value = 1.0
    nt.links.new(chd0.outputs["Fac"], not_chord.inputs[1])
    backfacing = nt.nodes.new("ShaderNodeMath"); backfacing.operation = "MULTIPLY"
    nt.links.new(geom.outputs["Backfacing"], backfacing.inputs[0])
    nt.links.new(not_chord.outputs["Value"], backfacing.inputs[1])
    back_dim = nt.nodes.new("ShaderNodeMath"); back_dim.operation = "MULTIPLY_ADD"
    nt.links.new(backfacing.outputs["Value"], back_dim.inputs[0])
    back_dim.inputs[1].default_value = BACK_DIM - 1.0
    back_dim.inputs[2].default_value = 1.0
    b2 = nt.nodes.new("ShaderNodeMath"); b2.operation = "MULTIPLY"
    nt.links.new(bright, b2.inputs[0])
    nt.links.new(back_dim.outputs["Value"], b2.inputs[1])
    b3 = nt.nodes.new("ShaderNodeMath"); b3.operation = "MULTIPLY"
    nt.links.new(b2.outputs["Value"], b3.inputs[0])
    nt.links.new(live, b3.inputs[1])
    bright_out = b3.outputs["Value"]
    if sense_s is not None:
        lift = nt.nodes.new("ShaderNodeMath"); lift.operation = "MULTIPLY_ADD"
        nt.links.new(sense_s, lift.inputs[0])
        lift.inputs[1].default_value = SENSE_LIFT
        lift.inputs[2].default_value = 1.0
        b4 = nt.nodes.new("ShaderNodeMath"); b4.operation = "MULTIPLY"
        nt.links.new(bright_out, b4.inputs[0])
        nt.links.new(lift.outputs["Value"], b4.inputs[1])
        bright_out = b4.outputs["Value"]
    if memory:
        # a remembered hit is lit by the thought on its thing, or by the eyes being shut (mem_lit, from
        # the geometry), and fades with the memory's age (AgeB, keyed, 1 for a memory of this very frame);
        # its unrest is in its shape, the heat-wave drift of the geometry, not in its light (his eleventh
        # review of 2026-11-11: flecks of light over it read as a noise texture)
        lit = nt.nodes.new("ShaderNodeAttribute"); lit.attribute_type = "GEOMETRY"; lit.attribute_name = "mem_lit"
        b6 = nt.nodes.new("ShaderNodeMath"); b6.operation = "MULTIPLY"
        nt.links.new(bright_out, b6.inputs[0])
        nt.links.new(lit.outputs["Fac"], b6.inputs[1])
        b7 = nt.nodes.new("ShaderNodeMath"); b7.operation = "MULTIPLY"
        nt.links.new(b6.outputs["Value"], b7.inputs[0])
        nt.links.new(value("AgeB", 1.0), b7.inputs[1])
        # and the light its waves carry (heat from the geometry, -0.5 to 0.5: the tile brighter or dimmer by HEAT_LIGHT
        # as the wave passes, smooth as the wave is)
        ht = nt.nodes.new("ShaderNodeAttribute"); ht.attribute_type = "GEOMETRY"; ht.attribute_name = "heat"
        rip = nt.nodes.new("ShaderNodeMath"); rip.operation = "MULTIPLY_ADD"
        nt.links.new(ht.outputs["Fac"], rip.inputs[0])
        rip.inputs[1].default_value = 4.0 * HEAT_LIGHT
        rip.inputs[2].default_value = 1.0
        b8 = nt.nodes.new("ShaderNodeMath"); b8.operation = "MULTIPLY"
        nt.links.new(b7.outputs["Value"], b8.inputs[0])
        nt.links.new(rip.outputs["Value"], b8.inputs[1])
        bright_out = b8.outputs["Value"]
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(mixc.outputs[2], em.inputs["Color"])
    nt.links.new(bright_out, em.inputs["Strength"])
    # a splat the rendering camera sees edge-on fades out, and one within NEAR_FOOT of its own footprints of
    # the camera, so a camera passing through the surface (the reveal, the mirror) meets no streaks and no
    # pops; from the simulated eyes every splat faces the ray and spans a pixel, so nothing fades there
    facing = nt.nodes.new("ShaderNodeVectorMath"); facing.operation = "DOT_PRODUCT"
    nt.links.new(geom.outputs["Normal"], facing.inputs[0])
    nt.links.new(geom.outputs["Incoming"], facing.inputs[1])
    face_abs = nt.nodes.new("ShaderNodeMath"); face_abs.operation = "ABSOLUTE"
    nt.links.new(facing.outputs["Value"], face_abs.inputs[0])
    edge_on = nt.nodes.new("ShaderNodeMapRange"); edge_on.interpolation_type = "SMOOTHSTEP"
    mats._set(edge_on, "From Min", EDGE_ON[0]); mats._set(edge_on, "From Max", EDGE_ON[1]); mats._set(edge_on, "To Min", 0.0); mats._set(edge_on, "To Max", 1.0)
    nt.links.new(face_abs.outputs["Value"], edge_on.inputs["Value"])
    camd = nt.nodes.new("ShaderNodeCameraData")
    foot = nt.nodes.new("ShaderNodeAttribute"); foot.attribute_type = "GEOMETRY"; foot.attribute_name = "foot"
    foot_floor = nt.nodes.new("ShaderNodeMath"); foot_floor.operation = "MAXIMUM"
    nt.links.new(foot.outputs["Fac"], foot_floor.inputs[0])
    foot_floor.inputs[1].default_value = 1e-7
    feet = nt.nodes.new("ShaderNodeMath"); feet.operation = "DIVIDE"
    nt.links.new(camd.outputs["View Distance"], feet.inputs[0])
    nt.links.new(foot_floor.outputs["Value"], feet.inputs[1])
    near = nt.nodes.new("ShaderNodeMapRange"); near.interpolation_type = "SMOOTHSTEP"
    mats._set(near, "From Min", NEAR_FOOT[0]); mats._set(near, "From Max", NEAR_FOOT[1]); mats._set(near, "To Min", 0.0); mats._set(near, "To Max", 1.0)
    nt.links.new(feet.outputs["Value"], near.inputs["Value"])
    vis = nt.nodes.new("ShaderNodeMath"); vis.operation = "MULTIPLY"
    nt.links.new(edge_on.outputs["Result"], vis.inputs[0])
    nt.links.new(near.outputs["Result"], vis.inputs[1])
    # the back's alpha: clear while the rendering camera is near, solid once it is far
    far = nt.nodes.new("ShaderNodeMapRange"); far.interpolation_type = "SMOOTHSTEP"
    mats._set(far, "From Min", BACK_CLEAR[0]); mats._set(far, "From Max", BACK_CLEAR[1]); mats._set(far, "To Min", 0.0); mats._set(far, "To Max", 1.0)
    nt.links.new(camd.outputs["View Distance"], far.inputs["Value"])
    far_m1 = nt.nodes.new("ShaderNodeMath"); far_m1.operation = "SUBTRACT"
    nt.links.new(far.outputs["Result"], far_m1.inputs[0])
    far_m1.inputs[1].default_value = 1.0
    back_a = nt.nodes.new("ShaderNodeMath"); back_a.operation = "MULTIPLY_ADD"
    nt.links.new(backfacing.outputs["Value"], back_a.inputs[0])
    nt.links.new(far_m1.outputs["Value"], back_a.inputs[1])
    back_a.inputs[2].default_value = 1.0
    a2 = nt.nodes.new("ShaderNodeMath"); a2.operation = "MULTIPLY"
    nt.links.new(vis.outputs["Value"], a2.inputs[0])
    nt.links.new(back_a.outputs["Value"], a2.inputs[1])
    a3 = nt.nodes.new("ShaderNodeMath"); a3.operation = "MULTIPLY"
    nt.links.new(a2.outputs["Value"], a3.inputs[0])
    # (the seen picture's own cover, LiveA: Live, but whole while the last picture still stands before it as the eyes
    # open after a long shutting, LidarScene.bake. Its light goes by Live alone)
    nt.links.new(live if (memory or additive) else value("LiveA", 1.0), a3.inputs[1])
    # the backdrop's soft edge at the window's frame (gate from the geometry; 1 on everything else)
    gate = nt.nodes.new("ShaderNodeAttribute"); gate.attribute_type = "GEOMETRY"; gate.attribute_name = "gate"
    a3g = nt.nodes.new("ShaderNodeMath"); a3g.operation = "MULTIPLY"
    nt.links.new(a3.outputs["Value"], a3g.inputs[0])
    nt.links.new(gate.outputs["Fac"], a3g.inputs[1])
    alpha = a3g.outputs["Value"]
    # a coin (coin from the geometry, not on a chord) off the eyes' own ray is clear
    coin = nt.nodes.new("ShaderNodeAttribute"); coin.attribute_type = "GEOMETRY"; coin.attribute_name = "coin"
    ray = nt.nodes.new("ShaderNodeAttribute"); ray.attribute_type = "GEOMETRY"; ray.attribute_name = "ray"
    along = nt.nodes.new("ShaderNodeVectorMath"); along.operation = "DOT_PRODUCT"
    nt.links.new(geom.outputs["Incoming"], along.inputs[0])
    nt.links.new(ray.outputs["Vector"], along.inputs[1])
    along_neg = nt.nodes.new("ShaderNodeMath"); along_neg.operation = "MULTIPLY"
    nt.links.new(along.outputs["Value"], along_neg.inputs[0])
    along_neg.inputs[1].default_value = -1.0
    on_ray = nt.nodes.new("ShaderNodeMapRange"); on_ray.interpolation_type = "SMOOTHSTEP"
    mats._set(on_ray, "From Min", COIN_ON[0]); mats._set(on_ray, "From Max", COIN_ON[1]); mats._set(on_ray, "To Min", 0.0); mats._set(on_ray, "To Max", 1.0)
    nt.links.new(along_neg.outputs["Value"], on_ray.inputs["Value"])
    coin_only = nt.nodes.new("ShaderNodeMath"); coin_only.operation = "MULTIPLY"
    nt.links.new(coin.outputs["Fac"], coin_only.inputs[0])
    nt.links.new(not_chord.outputs["Value"], coin_only.inputs[1])
    off_ray = nt.nodes.new("ShaderNodeMath"); off_ray.operation = "SUBTRACT"
    off_ray.inputs[0].default_value = 1.0
    nt.links.new(on_ray.outputs["Result"], off_ray.inputs[1])
    coin_clear = nt.nodes.new("ShaderNodeMath"); coin_clear.operation = "MULTIPLY"
    nt.links.new(coin_only.outputs["Value"], coin_clear.inputs[0])
    nt.links.new(off_ray.outputs["Value"], coin_clear.inputs[1])
    coin_keep = nt.nodes.new("ShaderNodeMath"); coin_keep.operation = "SUBTRACT"
    coin_keep.inputs[0].default_value = 1.0
    nt.links.new(coin_clear.outputs["Value"], coin_keep.inputs[1])
    a_coin = nt.nodes.new("ShaderNodeMath"); a_coin.operation = "MULTIPLY"
    nt.links.new(alpha, a_coin.inputs[0])
    nt.links.new(coin_keep.outputs["Value"], a_coin.inputs[1])
    alpha = a_coin.outputs["Value"]
    if memory:
        a5 = nt.nodes.new("ShaderNodeMath"); a5.operation = "MULTIPLY"
        nt.links.new(alpha, a5.inputs[0])
        age_a = value("AgeA", 1.0)
        if sense_s is not None:
            # a tile a sense lights is not an old memory: fully opaque (what lay behind showed through it at an old
            # memory's opacity and washed its colour)
            age_mix = nt.nodes.new("ShaderNodeMix")
            age_mix.data_type = "FLOAT"
            nt.links.new(sense_on, age_mix.inputs["Factor"])
            nt.links.new(age_a, age_mix.inputs[2])
            age_mix.inputs[3].default_value = 1.0
            age_a = age_mix.outputs[0]
        nt.links.new(age_a, a5.inputs[1])
        # a tile lit under LIT_THIN's second thins out as it dims, and is gone at its first: a thing fading from mind goes,
        # where it had stood as a dark shape before what lay behind it
        a6 = nt.nodes.new("ShaderNodeMapRange"); a6.interpolation_type = "SMOOTHSTEP"
        mats._set(a6, "From Min", LIT_THIN[0]); mats._set(a6, "From Max", LIT_THIN[1]); mats._set(a6, "To Min", 0.0); mats._set(a6, "To Max", 1.0)
        nt.links.new(lit.outputs["Fac"], a6.inputs["Value"])
        a7 = nt.nodes.new("ShaderNodeMath"); a7.operation = "MULTIPLY"
        nt.links.new(a5.outputs["Value"], a7.inputs[0])
        nt.links.new(a6.outputs["Result"], a7.inputs[1])
        alpha = a7.outputs["Value"]
    if side:
        # the rim's chord splats (chord 1 from the geometry) are split at their own middle across the eyes' ray
        # (eq_c, eq_n): the seen surfaces keep the near half (side -1), the far side the far half (+1), so the
        # seam between a thing's two sides is the locus of its chords' middles, the limb of a ball. Every other
        # splat is whole (his eleventh review of 2026-11-11: cut at a plane through the thing's centre, a bed
        # lost the far half of its top, a wall stood half faded and the chime's furniture came out in slivers)
        g2 = nt.nodes.new("ShaderNodeNewGeometry")
        eq_c = nt.nodes.new("ShaderNodeAttribute"); eq_c.attribute_type = "GEOMETRY"; eq_c.attribute_name = "eq_c"
        eq_n = nt.nodes.new("ShaderNodeAttribute"); eq_n.attribute_type = "GEOMETRY"; eq_n.attribute_name = "eq_n"
        chd = nt.nodes.new("ShaderNodeAttribute"); chd.attribute_type = "GEOMETRY"; chd.attribute_name = "chord"
        rel = nt.nodes.new("ShaderNodeVectorMath"); rel.operation = "SUBTRACT"
        nt.links.new(g2.outputs["Position"], rel.inputs[0])
        nt.links.new(eq_c.outputs["Vector"], rel.inputs[1])
        dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
        nt.links.new(rel.outputs["Vector"], dot.inputs[0])
        nt.links.new(eq_n.outputs["Vector"], dot.inputs[1])
        # what is cut: past the middle for the seen surfaces (side -1), short of it for the far side (+1)
        beyond = nt.nodes.new("ShaderNodeMath"); beyond.operation = "GREATER_THAN" if side < 0 else "LESS_THAN"
        nt.links.new(dot.outputs["Value"], beyond.inputs[0])
        beyond.inputs[1].default_value = 0.0
        cut2 = nt.nodes.new("ShaderNodeMath"); cut2.operation = "MULTIPLY"
        nt.links.new(beyond.outputs["Value"], cut2.inputs[0])
        nt.links.new(chd.outputs["Fac"], cut2.inputs[1])
        keep = nt.nodes.new("ShaderNodeMath"); keep.operation = "SUBTRACT"
        keep.inputs[0].default_value = 1.0
        nt.links.new(cut2.outputs["Value"], keep.inputs[1])
        a_cut = nt.nodes.new("ShaderNodeMath"); a_cut.operation = "MULTIPLY"
        nt.links.new(alpha, a_cut.inputs[0])
        nt.links.new(keep.outputs["Value"], a_cut.inputs[1])
        alpha = a_cut.outputs["Value"]
    if senses:
        # the chest's tiles clear while the heart or the lungs are thought of (sense_clear from the geometry, CHEST_CLEAR at full)
        scl = nt.nodes.new("ShaderNodeAttribute"); scl.attribute_type = "GEOMETRY"; scl.attribute_name = "sense_clear"
        keep_c = nt.nodes.new("ShaderNodeMath"); keep_c.operation = "MULTIPLY_ADD"
        nt.links.new(scl.outputs["Fac"], keep_c.inputs[0])
        keep_c.inputs[1].default_value = -CHEST_CLEAR
        keep_c.inputs[2].default_value = 1.0
        a_clear = nt.nodes.new("ShaderNodeMath"); a_clear.operation = "MULTIPLY"
        nt.links.new(alpha, a_clear.inputs[0])
        nt.links.new(keep_c.outputs["Value"], a_clear.inputs[1])
        alpha = a_clear.outputs["Value"]
    alpha = mats._fade_gain(nt, alpha, fade, "Model")
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    if additive:
        # the glass layer's reflections (rung 2o): light added over what lies beyond the pane, its alpha gating the
        # light rather than covering the view
        gated = nt.nodes.new("ShaderNodeMath"); gated.operation = "MULTIPLY"
        nt.links.new(bright_out, gated.inputs[0])
        nt.links.new(alpha, gated.inputs[1])
        cover = nt.nodes.new("ShaderNodeAttribute"); cover.attribute_type = "GEOMETRY"; cover.attribute_name = "cover"
        conserved = nt.nodes.new("ShaderNodeMath"); conserved.operation = "MULTIPLY"
        nt.links.new(gated.outputs["Value"], conserved.inputs[0])
        nt.links.new(cover.outputs["Fac"], conserved.inputs[1])
        for link in list(em.inputs["Strength"].links):
            nt.links.remove(link)
        nt.links.new(conserved.outputs["Value"], em.inputs["Strength"])
        add = nt.nodes.new("ShaderNodeAddShader")
        nt.links.new(tr.outputs["BSDF"], add.inputs[0])
        nt.links.new(em.outputs["Emission"], add.inputs[1])
        nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
        mat.surface_render_method = "BLENDED"
        mat.use_transparency_overlap = True
        mat.use_backface_culling = False
        mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
        return mat
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alpha, mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False
    mat.diffuse_color = (0.8, 0.8, 0.8, 1.0)
    return mat


def sun_material(name, colour, field_v_share, upper_share=UPPER_SHARE):
    """The sun as a ball of light. The same rule as every splat (his word of 2026-11-09): the half of the
    ball the eyes' rays reach is seen while Seen is set (the sun in sight), in its own colour at the
    sun's Strength; the rest is memory at the level Mem gives it (the thought of the outside, or the
    eyes shut: his seventh review of 2026-11-10), and it looks as every memory looks (the audit of 2026-11-15,
    his word of 2026-11-16): its colour drained toward its own grey by Grey, at memory's brightness for its age
    (MemBright) times SUN_MEM_LEVEL of a picture's white, brighter and dimmer as the ripple's wave passes (heat,
    from the ball's own geometry), opaque, thinning out as it fades (LIT_THIN), and under the lids' wipe where it
    lies in the eyes' field (scan_uv and in_field from the geometry; Unwipe, as a memory that completes the
    picture has). Until then it alone among memories was see-through by its level, drained toward white, with no
    wave of light and no lid over it: rippled as the rule has it, the ball's folds showed through each other as
    creases, and it stood as a flat grey shape. The seen half is under the same wipe (a dimming by the lids'
    cover as a whole until then). Clear where neither lights it, so the unlit ball hides nothing. The ball's own Z
    axis points from the eyes to the sun, so the half the rays reach is where its local z is below nought."""
    mat = bpy.data.materials.new(name)
    nt, out = mats._clear(mat)

    def value(nm, v):
        n = nt.nodes.new("ShaderNodeValue")
        n.name = nm
        n.label = nm
        n.outputs[0].default_value = v
        return n.outputs[0]

    def m(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs["Value"]

    def attr(nm, socket):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_type = "GEOMETRY"
        n.attribute_name = nm
        return n.outputs[socket]

    strength = value("Strength", 0.0)
    mem = value("Mem", 0.0)
    seen = value("Seen", 0.0)
    cover = value("Cover", 0.0)
    live = value("Live", 1.0)
    grey = value("Grey", 1.0)
    unwipe = value("Unwipe", 0.0)
    mem_bright = value("MemBright", MEM_BRIGHT)
    # the lids, as on every splat: the upper lid down over upper_share of the field, the lower up over the rest,
    # dimming what they cover to their floor
    sep_uv = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(attr("scan_uv", "Vector"), sep_uv.inputs["Vector"])
    h = field_v_share
    top = m("MULTIPLY_ADD", cover, -upper_share * 2.0 * h, 0.5 + h)
    bot = m("MULTIPLY_ADD", cover, (1.0 - upper_share) * 2.0 * h, 0.5 - h)
    open_ = m("MULTIPLY", m("LESS_THAN", sep_uv.outputs["Y"], top), m("GREATER_THAN", sep_uv.outputs["Y"], bot))
    lid = m("MULTIPLY_ADD", open_, 1.0 - LID_FLOOR, LID_FLOOR)
    # the seen half's light: the sun's strength, gone with the live picture; Seen is 1 while the eyes' rays reach
    # any of the disc (triview/engine.py sun_sight)
    s_live = m("MULTIPLY", strength, live)
    s_lid = m("MULTIPLY", s_live, lid)
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    nt.links.new(tc.outputs["Object"], sep.inputs["Vector"])
    front = nt.nodes.new("ShaderNodeMapRange"); front.interpolation_type = "SMOOTHSTEP"
    mats._set(front, "From Min", 0.08); mats._set(front, "From Max", -0.08); mats._set(front, "To Min", 0.0); mats._set(front, "To Max", 1.0)
    nt.links.new(sep.outputs["Z"], front.inputs["Value"])
    # the seen half: the half the rays reach, by the share they reach, while the live picture stands (gone
    # with it, the whole ball is memory: with the eyes shut the seen half stood as a dark disc)
    live_part = m("MULTIPLY", front.outputs["Result"], m("MULTIPLY", seen, live))
    mem_part = m("SUBTRACT", 1.0, live_part)
    # the memory's colour: drained toward its own grey (the grey of the same brightness) by Grey, MEM_DESAT of the
    # way at full Grey, as every memory's is
    lum = 0.2126 * colour[0] + 0.7152 * colour[1] + 0.0722 * colour[2]
    mixc = nt.nodes.new("ShaderNodeMix")
    mixc.data_type = "RGBA"
    nt.links.new(m("MULTIPLY", m("MULTIPLY", mem_part, grey), MEM_DESAT), mixc.inputs["Factor"])
    mixc.inputs[6].default_value = (*colour, 1.0)
    mixc.inputs[7].default_value = (lum, lum, lum, 1.0)
    # the memory's light: its level (the thought's, or the eyes being shut) at SUN_MEM_LEVEL of a picture's white (the
    # seen half is the sun's own strength, the remembered half memory's light, and the two must read apart: his tenth
    # review of 2026-11-10), by the age of the picture that lights it (MemBright), with the light its waves carry
    # (HEAT_LIGHT), under the lids where it lies in the eyes' field and out from under them as the live picture goes
    lid_mem = m("ADD", lid, m("MULTIPLY", m("SUBTRACT", 1.0, lid), unwipe))
    lid_mem = m("MULTIPLY_ADD", m("SUBTRACT", lid_mem, 1.0), attr("in_field", "Fac"), 1.0)
    wave = m("MULTIPLY_ADD", attr("heat", "Fac"), 4.0 * HEAT_LIGHT, 1.0)
    held = m("MINIMUM", mem, 1.0)
    mem_lit = m("MULTIPLY", m("MULTIPLY", m("MULTIPLY", held, mem_bright), SUN_MEM_LEVEL), m("MULTIPLY", wave, lid_mem))
    seen_lit = m("MULTIPLY", s_lid, live_part)
    bright = m("MULTIPLY_ADD", mem_part, mem_lit, seen_lit)
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(mixc.outputs[2], em.inputs["Color"])
    nt.links.new(bright, em.inputs["Strength"])
    # opaque where the seen half stands and where the memory is lit; a memory lit under LIT_THIN's second thins out
    # as it dims and is gone at its first, as every memory's tile is; clear where neither lights the ball
    thin = nt.nodes.new("ShaderNodeMapRange"); thin.interpolation_type = "SMOOTHSTEP"
    mats._set(thin, "From Min", LIT_THIN[0]); mats._set(thin, "From Max", LIT_THIN[1]); mats._set(thin, "To Min", 0.0); mats._set(thin, "To Max", 1.0)
    nt.links.new(mem, thin.inputs["Value"])
    alpha = m("MINIMUM", m("ADD", m("MULTIPLY", live_part, m("MINIMUM", s_live, 1.0)), m("MULTIPLY", mem_part, thin.outputs["Result"])), 1.0)
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    mix = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(alpha, mix.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
    nt.links.new(em.outputs["Emission"], mix.inputs[2])
    nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = True
    return mat


def _heat(nodes, links, q_room, radius_socket, d_room, d_pressed, pixel_angle, axes_model, facing, tm, hold=None, eye_room=None, own_body=None,
          thing=None, own=None, table=None, bend_radius=None):
    """A memory's ripple at a room point, in model metres across the eyes' ray: waves in the thing's own
    coordinates, HEAT_ASPECT times wider than tall, changing shape where they stand at HEAT_SPEED cells a second and
    travelling nowhere, the shape displaced by them in every direction across the ray, by HEAT_SHARE of the thing's
    radius in all (between HEAT_FOOT_MIN and HEAT_FOOT_MAX footprints at the hit), scaled as the hit's placement
    scales the thing. axes_model: the room's two level axes and its up as unit vectors in the model's frame, one
    reading of the wave for each. hold (0 or 1) stills it. bend_radius: the radius, in the room's metres, of the thing
    the point ripples with; as far as that thing is held whole (own) the offset is limited to HEAT_BEND of it.
    Returns the offset and the wave's level at the point."""

    def math(op, a=None, b=None, c=None):
        n = nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                links.new(v, n.inputs[i])
        return n.outputs["Value"]

    def vmath(op, a=None, b=None, scale=None):
        n = nodes.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (tuple, list, Vector)):
                n.inputs[i].default_value = tuple(v)
            else:
                links.new(v, n.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)):
                n.inputs["Scale"].default_value = float(scale)
            else:
                links.new(scale, n.inputs["Scale"])
        return n.outputs["Vector"] if op not in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Value"]

    foot = math("MULTIPLY", d_room, pixel_angle)
    grain_v = math("MINIMUM", math("MAXIMUM", math("MULTIPLY", radius_socket, HEAT_GRAIN), math("MULTIPLY", foot, HEAT_GRAIN_FOOT[0])),
                   math("MULTIPLY", foot, HEAT_GRAIN_FOOT[1]))
    amp_room = math("MINIMUM", math("MAXIMUM", math("MULTIPLY", radius_socket, HEAT_SHARE), math("MULTIPLY", foot, HEAT_FOOT_MIN)),
                    math("MULTIPLY", foot, HEAT_FOOT_MAX))
    amp = math("MULTIPLY", amp_room, math("DIVIDE", d_pressed, math("MAXIMUM", d_room, 1e-6)))
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(q_room, sep.inputs["Vector"])
    coord = nodes.new("ShaderNodeCombineXYZ")
    links.new(math("DIVIDE", sep.outputs["X"], math("MULTIPLY", grain_v, HEAT_ASPECT)), coord.inputs["X"])
    links.new(math("DIVIDE", sep.outputs["Y"], math("MULTIPLY", grain_v, HEAT_ASPECT)), coord.inputs["Y"])
    links.new(math("DIVIDE", sep.outputs["Z"], grain_v), coord.inputs["Z"])
    coord_out = coord.outputs["Vector"]
    if eye_room is not None:
        # one ripple for every remembered thing (HEAT_AMP_DEG, HEAT_WAVE_DEG): the amplitude an angle from the eyes, so
        # the hit's pressed distance times it in the model; the wave read at the hit's direction from the eyes in the
        # room's axes. own_body (0 or 1) keeps the measure above for his own body's known shape
        amp_new = math("MULTIPLY", d_pressed, HEAT_AMP_RAD)
        u_dir = nodes.new("ShaderNodeSeparateXYZ")
        links.new(vmath("NORMALIZE", vmath("SUBTRACT", q_room, eye_room)), u_dir.inputs["Vector"])
        coord_u = nodes.new("ShaderNodeCombineXYZ")
        links.new(math("DIVIDE", u_dir.outputs["X"], HEAT_WAVE_RAD * HEAT_ASPECT), coord_u.inputs["X"])
        links.new(math("DIVIDE", u_dir.outputs["Y"], HEAT_WAVE_RAD * HEAT_ASPECT), coord_u.inputs["Y"])
        links.new(math("DIVIDE", u_dir.outputs["Z"], HEAT_WAVE_RAD), coord_u.inputs["Z"])
        if own_body is None:
            amp, coord_out = amp_new, coord_u.outputs["Vector"]
        else:
            amp = math("ADD", amp_new, math("MULTIPLY", math("SUBTRACT", amp, amp_new), own_body))
            pick = nodes.new("ShaderNodeMix")
            pick.data_type = "VECTOR"
            links.new(own_body, pick.inputs[0])
            links.new(coord_u.outputs["Vector"], pick.inputs[4])
            links.new(coord.outputs["Vector"], pick.inputs[5])
            coord_out = pick.outputs[1]
    if hold is not None:
        amp = math("MULTIPLY", amp, hold)
    clock = math("MULTIPLY", tm.outputs["Seconds"], HEAT_SPEED)

    def wave(vec, w_clock):
        noise = nodes.new("ShaderNodeTexNoise")
        noise.noise_dimensions = "4D"
        links.new(vec, noise.inputs["Vector"])
        links.new(w_clock, noise.inputs["W"])
        noise.inputs["Scale"].default_value = 1.0
        noise.inputs["Detail"].default_value = 1.5
        noise.inputs["Roughness"].default_value = 0.5
        return noise.outputs["Fac"], noise.outputs["Color"]

    wave_lvl, wave_col = wave(coord_out, clock)
    own_w = None
    if thing is not None and own is not None and table is not None and eye_room is not None:
        # a thing held whole wavers in its own pattern and at its own time (HEAT_STAGGER, by its index): per thing, not
        # a mask over the picture (his tenth review of 2026-11-10, and of 2026-11-14 on the one ripple read off the
        # direction from the eyes alone: "it looks like it's screen based rather than object based ... it should be
        # per object, such there's a stagger/randomization in the shimmer"). own (0 to 1) is how far the thing is held
        # whole (COMPACT): what spans its distance, the walls with the floor, the ground with the range and the sky,
        # shares the one field whole, so things that meet along long edges do not part; his own body's known shape,
        # with its own small measure, likewise
        own_w = own if own_body is None else math("MULTIPLY", own, math("SUBTRACT", 1.0, own_body))

        def stagger(index_socket):
            shift = nodes.new("ShaderNodeCombineXYZ")
            for i_s in range(3):
                links.new(math("MULTIPLY", index_socket, HEAT_STAGGER[i_s]), shift.inputs[i_s])
            return shift.outputs["Vector"], math("MULTIPLY_ADD", index_socket, HEAT_STAGGER[3], clock)

        shift_q, clock_q = stagger(thing)
        held_lvl, held_col = wave(vmath("ADD", coord_out, shift_q), clock_q)
        if HEAT_HELD != "own":
            # the thing's own reading is taken against the same reading at its own centre, so the centre does not
            # move by it (HEAT_HELD): the reading at the centre is worked out on the table of things (a point a
            # thing, its index the thing's) and looked up by the hit's thing
            own_lvl, own_col = held_lvl, held_col
            t_info = nodes.new("GeometryNodeObjectInfo")
            t_info.transform_space = "ORIGINAL"
            t_info.inputs["Object"].default_value = table
            t_cen = nodes.new("GeometryNodeInputNamedAttribute")
            t_cen.data_type = "FLOAT_VECTOR"
            t_cen.inputs["Name"].default_value = "centre"
            t_idx = nodes.new("GeometryNodeInputIndex")
            c_dir = nodes.new("ShaderNodeSeparateXYZ")
            links.new(vmath("NORMALIZE", vmath("SUBTRACT", t_cen.outputs["Attribute"], eye_room)), c_dir.inputs["Vector"])
            c_coord = nodes.new("ShaderNodeCombineXYZ")
            links.new(math("DIVIDE", c_dir.outputs["X"], HEAT_WAVE_RAD * HEAT_ASPECT), c_coord.inputs["X"])
            links.new(math("DIVIDE", c_dir.outputs["Y"], HEAT_WAVE_RAD * HEAT_ASPECT), c_coord.inputs["Y"])
            links.new(math("DIVIDE", c_dir.outputs["Z"], HEAT_WAVE_RAD), c_coord.inputs["Z"])
            shift_c, clock_c = stagger(t_idx.outputs["Index"])
            mid_own_lvl, mid_own_col = wave(vmath("ADD", c_coord.outputs["Vector"], shift_c), clock_c)

            def of_thing(field_socket, dtype):
                s_t = nodes.new("GeometryNodeSampleIndex")
                s_t.data_type = dtype
                s_t.domain = "POINT"
                links.new(t_info.outputs["Geometry"], s_t.inputs["Geometry"])
                links.new(field_socket, _sock(s_t.inputs, "Value"))
                links.new(thing, s_t.inputs["Index"])
                return _sock(s_t.outputs, "Value")

            base_col, base_lvl = (0.5, 0.5, 0.5), 0.5
            if HEAT_HELD == "field":
                mid_lvl, mid_col = wave(c_coord.outputs["Vector"], clock)
                base_col, base_lvl = of_thing(mid_col, "FLOAT_COLOR"), of_thing(mid_lvl, "FLOAT")
            held_col = vmath("ADD", base_col, vmath("SUBTRACT", own_col, of_thing(mid_own_col, "FLOAT_COLOR")))
            held_lvl = math("ADD", base_lvl, math("SUBTRACT", own_lvl, of_thing(mid_own_lvl, "FLOAT")))
        pick_w = nodes.new("ShaderNodeMix")
        pick_w.data_type = "VECTOR"
        links.new(own_w, pick_w.inputs["Factor"])
        links.new(wave_col, pick_w.inputs[4])
        links.new(held_col, pick_w.inputs[5])
        wave_col = pick_w.outputs[1]
        wave_lvl = math("ADD", wave_lvl, math("MULTIPLY", math("SUBTRACT", held_lvl, wave_lvl), own_w))
    level = math("SUBTRACT", wave_lvl, 0.5)
    # three readings of the wave, one along each of the room's axes (the noise's three channels, each about a half)
    reads = nodes.new("ShaderNodeSeparateXYZ")
    links.new(vmath("SUBTRACT", wave_col, (0.5, 0.5, 0.5)), reads.inputs["Vector"])
    reach = math("MULTIPLY", amp, 2.0 * HEAT_ACROSS)
    off = None
    for axis, read in zip(axes_model, (reads.outputs["X"], reads.outputs["Y"], reads.outputs["Z"])):
        part = vmath("SCALE", axis, scale=math("MULTIPLY", read, reach))
        off = part if off is None else vmath("ADD", off, part)
    if hold is not None:
        level = math("MULTIPLY", level, hold)
    # the offset across the ray, and the wave's own level there (-0.5 to 0.5), for the light it carries (HEAT_LIGHT)
    across = vmath("SUBTRACT", off, vmath("SCALE", facing, scale=vmath("DOT_PRODUCT", off, facing)))
    if own_w is not None and bend_radius is not None and HEAT_BEND:
        # a thing held whole keeps its shape (HEAT_BEND): its radius in the model at the point, as the placing scales it
        cap = math("MULTIPLY", math("MULTIPLY", bend_radius, HEAT_BEND), math("DIVIDE", d_pressed, math("MAXIMUM", d_room, 1e-6)))
        q_b = math("DIVIDE", vmath("LENGTH", across), math("MAXIMUM", cap, 1e-9))
        soft_b = math("POWER", math("ADD", 1.0, math("POWER", q_b, 4.0)), -0.25)
        across = vmath("SCALE", across, scale=math("ADD", 1.0, math("MULTIPLY", math("SUBTRACT", soft_b, 1.0), own_w)))
    return across, level


def _ops(nodes, links):
    """The two node makers every tree here uses: a Math node and a Vector Math node, their inputs values or sockets."""

    def math(op, a=None, b=None, c=None):
        n = nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                links.new(v, n.inputs[i])
        return n.outputs["Value"]

    def vmath(op, a=None, b=None, scale=None):
        n = nodes.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (tuple, list, Vector)):
                n.inputs[i].default_value = tuple(v)
            else:
                links.new(v, n.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)):
                n.inputs["Scale"].default_value = float(scale)
            else:
                links.new(scale, n.inputs["Scale"])
        return n.outputs["Vector"] if op not in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Value"]

    return math, vmath


def contact_nodes(name, body, targets, window_c=None, shade=None):
    """Where the body is touched (rung 2p, his word of 2026-11-12: touch by one rule for everything, and only the
    patch that is touched). The body's own shapes in room metres, joined, each cut finer than CONTACT_EDGE, every
    vertex carrying contact (0 to 1): 1 within CONTACT_SKIN[0] of another thing's surface or inside another thing's
    closed shape, falling to 0 at CONTACT_SKIN[1]; and 1 where the middle of the part at the vertex (core: halfway
    to the part's own far wall along the vertex's inward normal) lies inside another thing's closed shape, which has
    then given way and wraps the part. Another thing: each mesh of the room, the closed ones each alone
    (so a point is told inside each), the open ones together by distance alone; and each body part, for the parts not
    joined to it at one joint or fused with it (tags.own_parts). Nothing here knows the bed from the floor or the hand
    from the head.

    A point is told inside a closed shape alone: an open one (a limb's tube has no ends) has no inside, and the
    nearest-face test took every point beyond a tube's open end, within its width, as inside it (the shins under the
    trunk's tube while he stood, found 2026-11-12).

    The body's skin (his word of 2026-11-12, sixth round: a sense is drawn on the outside of the body, what its rays
    strike, not on the stand-in's pieces whole with what lies inside one another): every vertex also carries inner, 1
    where it lies inside another piece of the body, deeper than INNER_SKIN. A piece's solid is its own mesh where
    that is closed, and its convex hull where it is open (a limb's tube without ends), so every piece has an inside.

    body: [(object, part index, subdivision level, closed)]; targets: [(object, closed)]."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links
    math, vmath = _ops(nodes, links)
    go = nodes.new("NodeGroupOutput")

    def geo_of(ob):
        info = nodes.new("GeometryNodeObjectInfo")
        info.transform_space = "RELATIVE"
        info.inputs["Object"].default_value = ob
        return info.outputs["Geometry"]

    def joined(geos):
        j = nodes.new("GeometryNodeJoinGeometry")
        for g in geos:
            links.new(g, j.inputs["Geometry"])
        return j.outputs["Geometry"]

    pos = nodes.new("GeometryNodeInputPosition").outputs["Position"]
    nrm = nodes.new("GeometryNodeInputNormal").outputs["Normal"]
    core_n = nodes.new("GeometryNodeInputNamedAttribute")
    core_n.data_type = "FLOAT_VECTOR"
    core_n.inputs["Name"].default_value = "core"
    core = core_n.outputs["Attribute"]

    def touch_of(target, solid):
        """A point's contact with a target: by its distance to the target's surface, or, for a solid, by lying inside
        it (on the inner side of the nearest face)."""
        prox = nodes.new("GeometryNodeProximity")
        prox.target_element = "FACES"
        links.new(target, prox.inputs["Geometry"])
        links.new(pos, prox.inputs["Sample Position"])
        near = nodes.new("ShaderNodeMapRange")
        near.interpolation_type = "SMOOTHSTEP"
        near.inputs["From Min"].default_value = CONTACT_SKIN[0]
        near.inputs["From Max"].default_value = CONTACT_SKIN[1]
        near.inputs["To Min"].default_value = 1.0
        near.inputs["To Max"].default_value = 0.0
        links.new(prox.outputs["Distance"], near.inputs["Value"])
        c = near.outputs["Result"]
        if solid:
            # wrapped: the middle of the part at this point lies inside the solid
            prox_c = nodes.new("GeometryNodeProximity")
            prox_c.target_element = "FACES"
            links.new(target, prox_c.inputs["Geometry"])
            links.new(core, prox_c.inputs["Sample Position"])
            smp_c = nodes.new("GeometryNodeSampleNearestSurface")
            smp_c.data_type = "FLOAT_VECTOR"
            links.new(target, smp_c.inputs["Mesh"])
            links.new(nrm, smp_c.inputs["Value"])
            links.new(core, smp_c.inputs["Sample Position"])
            behind_c = vmath("DOT_PRODUCT", vmath("SUBTRACT", core, prox_c.outputs["Position"]), smp_c.outputs["Value"])
            c = math("MAXIMUM", c, math("LESS_THAN", behind_c, math("MULTIPLY", prox_c.outputs["Distance"], -0.5)))
            smp = nodes.new("GeometryNodeSampleNearestSurface")
            smp.data_type = "FLOAT_VECTOR"
            links.new(target, smp.inputs["Mesh"])
            links.new(nrm, smp.inputs["Value"])
            links.new(pos, smp.inputs["Sample Position"])
            # inside: the point lies behind the nearest face, squarely (within sixty degrees of its inward normal). Behind
            # by any margin took a point level with a box's face and far beyond its corner as inside, by rounding (a
            # vertex of the head 0.7 m from the pillow's corner and level with its north face, found 2026-11-12)
            behind = vmath("DOT_PRODUCT", vmath("SUBTRACT", pos, prox.outputs["Position"]), smp.outputs["Value"])
            inside = math("LESS_THAN", behind, math("MULTIPLY", prox.outputs["Distance"], -0.5))
            c = math("MAXIMUM", c, inside)
        return c

    part_geos = {}
    whole = nodes.new("GeometryNodeJoinGeometry")
    for piece, (ob, part, level, closed) in enumerate(body):
        g = geo_of(ob)
        part_geos.setdefault((part, bool(closed)), []).append(g)
        if level > 0:
            sub = nodes.new("GeometryNodeSubdivideMesh")
            sub.inputs["Level"].default_value = int(level)
            links.new(g, sub.inputs["Mesh"])
            g = sub.outputs["Mesh"]
        # the middle of the part at each vertex: halfway to the part's own far wall along the vertex's inward normal (a
        # sphere's centre, a limb's axis), whatever the part's shape
        ray = nodes.new("GeometryNodeRaycast")
        links.new(geo_of(ob), ray.inputs["Target Geometry"])
        links.new(vmath("SUBTRACT", pos, vmath("SCALE", nrm, scale=0.001)), ray.inputs["Source Position"])
        links.new(vmath("SCALE", nrm, scale=-1.0), ray.inputs["Ray Direction"])
        ray.inputs["Ray Length"].default_value = 1.0
        mid = nodes.new("ShaderNodeMix")
        mid.data_type = "VECTOR"
        links.new(ray.outputs["Is Hit"], mid.inputs["Factor"])
        links.new(pos, mid.inputs[4])
        links.new(vmath("SCALE", vmath("ADD", pos, ray.outputs["Hit Position"]), scale=0.5), mid.inputs[5])
        sc = nodes.new("GeometryNodeStoreNamedAttribute")
        sc.data_type = "FLOAT_VECTOR"
        sc.domain = "POINT"
        sc.inputs["Name"].default_value = "core"
        links.new(g, sc.inputs["Geometry"])
        links.new(mid.outputs[1], sc.inputs["Value"])
        st = nodes.new("GeometryNodeStoreNamedAttribute")
        st.data_type = "FLOAT"
        st.domain = "POINT"
        st.inputs["Name"].default_value = "part"
        st.inputs["Value"].default_value = float(part)
        links.new(sc.outputs["Geometry"], st.inputs["Geometry"])
        sp = nodes.new("GeometryNodeStoreNamedAttribute")
        sp.data_type = "FLOAT"
        sp.domain = "POINT"
        sp.inputs["Name"].default_value = "piece"
        sp.inputs["Value"].default_value = float(piece)
        links.new(st.outputs["Geometry"], sp.inputs["Geometry"])
        links.new(sp.outputs["Geometry"], whole.inputs["Geometry"])
    part_n = nodes.new("GeometryNodeInputNamedAttribute")
    part_n.data_type = "FLOAT"
    part_n.inputs["Name"].default_value = "part"
    part_v = part_n.outputs["Attribute"]
    contact = None

    def more(c):
        nonlocal contact
        contact = c if contact is None else math("MAXIMUM", contact, c)

    for ob, closed in targets:
        if closed:
            more(touch_of(geo_of(ob), True))
    opens = [geo_of(ob) for ob, closed in targets if not closed]
    if opens:
        more(touch_of(joined(opens), False))
    names = list(tags.PARTS)
    for (part, closed), geos in sorted(part_geos.items()):
        # a part touches every part but itself, the parts joined to it at one joint and those it is fused with
        own = None
        for k in sorted(tags.PART_INDEX[q] for q in tags.own_parts(names[part])):
            e = math("COMPARE", part_v, float(k), 0.5)
            own = e if own is None else math("MAXIMUM", own, e)
        more(math("MULTIPLY", touch_of(joined(geos), closed), math("SUBTRACT", 1.0, own)))
    out = nodes.new("GeometryNodeStoreNamedAttribute")
    out.data_type = "FLOAT"
    out.domain = "POINT"
    out.inputs["Name"].default_value = "contact"
    links.new(whole.outputs["Geometry"], out.inputs["Geometry"])
    if contact is not None:
        links.new(contact, out.inputs["Value"])
    # the skin: a vertex inside another piece's solid (on the inner side of its nearest face, deeper than INNER_SKIN)
    piece_n = nodes.new("GeometryNodeInputNamedAttribute")
    piece_n.data_type = "FLOAT"
    piece_n.inputs["Name"].default_value = "piece"
    inner = None
    for piece, (ob, part, level, closed) in enumerate(body):
        solid = geo_of(ob)
        if not closed:
            hull = nodes.new("GeometryNodeConvexHull")
            links.new(solid, hull.inputs["Geometry"])
            solid = hull.outputs["Convex Hull"]
        prox = nodes.new("GeometryNodeProximity")
        prox.target_element = "FACES"
        links.new(solid, prox.inputs["Geometry"])
        links.new(pos, prox.inputs["Sample Position"])
        smp = nodes.new("GeometryNodeSampleNearestSurface")
        smp.data_type = "FLOAT_VECTOR"
        links.new(solid, smp.inputs["Mesh"])
        links.new(nrm, smp.inputs["Value"])
        links.new(pos, smp.inputs["Sample Position"])
        behind = vmath("DOT_PRODUCT", vmath("SUBTRACT", pos, prox.outputs["Position"]), smp.outputs["Value"])
        ins = math("MULTIPLY", math("LESS_THAN", behind, math("MULTIPLY", prox.outputs["Distance"], -0.5)),
                   math("GREATER_THAN", prox.outputs["Distance"], INNER_SKIN))
        ins = math("MULTIPLY", ins, math("SUBTRACT", 1.0, math("COMPARE", piece_n.outputs["Attribute"], float(piece), 0.5)))
        inner = ins if inner is None else math("MAXIMUM", inner, ins)
    skin = nodes.new("GeometryNodeStoreNamedAttribute")
    skin.data_type = "FLOAT"
    skin.domain = "POINT"
    skin.inputs["Name"].default_value = "inner"
    links.new(out.outputs["Geometry"], skin.inputs["Geometry"])
    if inner is not None:
        links.new(inner, skin.inputs["Value"])
    # what the sun's rays and the window's air reach on the skin (his word of 2026-11-13: warmth works as touch does,
    # on the outside, where it affects): a vertex whose skin faces the source and whose way to it meets nothing, the
    # room's things and the body's own pieces alike, so a hand held up shades the face. Glass the eyes see through lets
    # both pass. The sun's direction is three Value nodes the bake keys (SunX, SunY, SunZ, along the room's axes); the
    # air's source is the middle of the window's opening (window_c, room metres). What can stand in the way is the room's
    # own things (shade) and the body: the range outside is left out. The sun's disc is partly above the ridge from 26 s
    # while its middle stays a fraction of a degree under the stand-in range's top until about 80 s, so a ray toward
    # the middle met the range from every point of the body and no warmth showed through the sunrise (2026-11-13);
    # whether the sun is up is the timeline's to say, where it reaches in the room is told here.
    if shade is None:
        shade = [ob for ob, _ in targets if not ob.get(tags.PASS_PROP)]
    blockers = joined([geo_of(ob) for ob in shade] + [geo_of(ob) for ob, _, _, _ in body])
    sun_c = nodes.new("ShaderNodeCombineXYZ")
    for ax, v0 in zip("XYZ", (0.0, 0.0, 1.0)):
        val = nodes.new("ShaderNodeValue")
        val.name = val.label = f"Sun{ax}"
        val.outputs[0].default_value = v0
        links.new(val.outputs[0], sun_c.inputs[ax])

    def reached(way, length):
        """1 where the skin faces along way (a unit vector toward the source) and a ray of that length meets nothing."""
        face = nodes.new("ShaderNodeMapRange")
        face.interpolation_type = "SMOOTHSTEP"
        face.inputs["From Min"].default_value = 0.0
        face.inputs["From Max"].default_value = REACH_FACE
        links.new(vmath("DOT_PRODUCT", nrm, way), face.inputs["Value"])
        ray = nodes.new("GeometryNodeRaycast")
        links.new(blockers, ray.inputs["Target Geometry"])
        links.new(vmath("ADD", pos, vmath("SCALE", nrm, scale=REACH_LIFT)), ray.inputs["Source Position"])
        links.new(way, ray.inputs["Ray Direction"])
        if isinstance(length, (int, float)):
            ray.inputs["Ray Length"].default_value = float(length)
        else:
            links.new(length, ray.inputs["Ray Length"])
        return math("MULTIPLY", face.outputs["Result"], math("SUBTRACT", 1.0, ray.outputs["Is Hit"]))

    last = skin.outputs["Geometry"]
    reaches = [("sun", reached(vmath("NORMALIZE", sun_c.outputs["Vector"]), SUN_RAY))]
    if window_c is not None:
        to_w = vmath("SUBTRACT", tuple(window_c), pos)
        reaches.append(("air", reached(vmath("NORMALIZE", to_w), math("MAXIMUM", math("SUBTRACT", vmath("LENGTH", to_w), 0.05), 0.0))))
    for nm, value in reaches:
        # a shadow's edge is told vertex by vertex, in steps the size of the body's cut (3 cm): spread over the
        # neighbouring vertices REACH_BLUR times, so the edge of a shade on the skin is soft and not a row of teeth
        blur = nodes.new("GeometryNodeBlurAttribute")
        blur.data_type = "FLOAT"
        blur.inputs["Iterations"].default_value = REACH_BLUR
        links.new(value, blur.inputs["Value"])
        st_r = nodes.new("GeometryNodeStoreNamedAttribute")
        st_r.data_type = "FLOAT"
        st_r.domain = "POINT"
        st_r.inputs["Name"].default_value = nm
        links.new(last, st_r.inputs["Geometry"])
        links.new(blur.outputs["Value"], st_r.inputs["Value"])
        last = st_r.outputs["Geometry"]
    links.new(last, go.inputs["Geometry"])
    return ng


def _body_at(nodes, links, contact_obj, pos_socket, name):
    """A named number ContactBody carries on the body's surface (sun, air), 0 to 1 between its vertices, read at the
    nearest point of the body's shapes to a room point."""
    info = nodes.new("GeometryNodeObjectInfo")
    info.transform_space = "ORIGINAL"
    info.inputs["Object"].default_value = contact_obj
    att = nodes.new("GeometryNodeInputNamedAttribute")
    att.data_type = "FLOAT"
    att.inputs["Name"].default_value = name
    smp = nodes.new("GeometryNodeSampleNearestSurface")
    smp.data_type = "FLOAT"
    links.new(info.outputs["Geometry"], smp.inputs["Mesh"])
    links.new(att.outputs["Attribute"], smp.inputs["Value"])
    links.new(pos_socket, smp.inputs["Sample Position"])
    return smp.outputs["Value"]


def _inner_at(nodes, links, contact_obj, pos_socket):
    """Whether a room point on the body's surface lies inside another piece of the body (0 to 1 between ContactBody's
    vertices), read off ContactBody at the nearest point of the body's shapes."""
    info = nodes.new("GeometryNodeObjectInfo")
    info.transform_space = "ORIGINAL"
    info.inputs["Object"].default_value = contact_obj
    att = nodes.new("GeometryNodeInputNamedAttribute")
    att.data_type = "FLOAT"
    att.inputs["Name"].default_value = "inner"
    smp = nodes.new("GeometryNodeSampleNearestSurface")
    smp.data_type = "FLOAT"
    links.new(info.outputs["Geometry"], smp.inputs["Mesh"])
    links.new(att.outputs["Attribute"], smp.inputs["Value"])
    links.new(pos_socket, smp.inputs["Sample Position"])
    return smp.outputs["Value"]


def _contact_at(nodes, links, contact_obj, pos_socket, hold=False):
    """The body's contact (0 to 1) at a room point on its surface, read off ContactBody at the nearest point of the
    body's shapes. hold: nought where the point lies farther than CONTACT_HOLD from the body as it is this frame (a
    remembered hit of a part that has since moved)."""
    math, vmath = _ops(nodes, links)
    info = nodes.new("GeometryNodeObjectInfo")
    info.transform_space = "ORIGINAL"
    info.inputs["Object"].default_value = contact_obj
    att = nodes.new("GeometryNodeInputNamedAttribute")
    att.data_type = "FLOAT"
    att.inputs["Name"].default_value = "contact"
    smp = nodes.new("GeometryNodeSampleNearestSurface")
    smp.data_type = "FLOAT"
    links.new(info.outputs["Geometry"], smp.inputs["Mesh"])
    links.new(att.outputs["Attribute"], smp.inputs["Value"])
    links.new(pos_socket, smp.inputs["Sample Position"])
    c = smp.outputs["Value"]
    if hold:
        prox = nodes.new("GeometryNodeProximity")
        prox.target_element = "FACES"
        links.new(info.outputs["Geometry"], prox.inputs["Geometry"])
        links.new(pos_socket, prox.inputs["Sample Position"])
        c = math("MULTIPLY", c, math("LESS_THAN", prox.outputs["Distance"], CONTACT_HOLD))
    return c


def _thing_lookup(nodes, links, table_obj, id_socket):
    """The table of things' row for a hit's index: its centre and radius in room metres and its region
    among the ten the mind can think of, sampled off the ThingTable mesh (one vertex per thing, the
    rows as its attributes). Without a table every hit is held piece by piece as other."""
    out = {}
    if table_obj is None:
        c = nodes.new("ShaderNodeCombineXYZ")
        out["centre"] = c.outputs["Vector"]
        for name, v in (("radius", 1.0e9), ("region", float(REGION_OTHER)), ("part", -1.0)):
            n = nodes.new("ShaderNodeValue")
            n.outputs[0].default_value = v
            out[name] = n.outputs[0]
        grey = nodes.new("FunctionNodeInputColor")
        out["colour"] = grey.outputs["Color"]
        return out
    info = nodes.new("GeometryNodeObjectInfo")
    info.transform_space = "ORIGINAL"
    info.inputs["Object"].default_value = table_obj
    for name, dtype in (("centre", "FLOAT_VECTOR"), ("radius", "FLOAT"), ("region", "FLOAT"), ("colour", "FLOAT_COLOR"), ("part", "FLOAT"),
                        ("wave_id", "FLOAT"), ("wave_centre", "FLOAT_VECTOR"), ("wave_radius", "FLOAT"), ("round", "FLOAT")):
        named = nodes.new("GeometryNodeInputNamedAttribute")
        named.data_type = dtype
        named.inputs["Name"].default_value = name
        smp = nodes.new("GeometryNodeSampleIndex")
        smp.data_type = dtype
        smp.domain = "POINT"
        links.new(info.outputs["Geometry"], smp.inputs["Geometry"])
        links.new(named.outputs["Attribute"], smp.inputs["Value"])
        links.new(id_socket, smp.inputs["Index"])
        out[name] = smp.outputs["Value"]
    return out


def _sense_sample(nodes, links, img, part_socket, field, n_frames):
    """The sense table's row for this frame at a part (rung 2p): the picture's column is the field's block plus the part's
    index, its row the scene's frame; returns the sample's colour and alpha. Field 0 is the sense light (its colour, its
    strength in the alpha), 1 the tint (red: how far the colour replaces the part's own) and the part's scale (green),
    2 the outline (its colour, its strength in the alpha), 3 touch (its colour, its level on the part in the alpha)."""
    W = SENSE_FIELDS * len(tags.SENSE_PARTS)
    time = nodes.new("GeometryNodeInputSceneTime")
    col_i = nodes.new("ShaderNodeMath"); col_i.operation = "ADD"
    links.new(part_socket, col_i.inputs[0])
    col_i.inputs[1].default_value = float(field * len(tags.SENSE_PARTS)) + 0.5
    u = nodes.new("ShaderNodeMath"); u.operation = "DIVIDE"
    links.new(col_i.outputs["Value"], u.inputs[0])
    u.inputs[1].default_value = float(W)
    row = nodes.new("ShaderNodeMath"); row.operation = "SUBTRACT"
    links.new(time.outputs["Frame"], row.inputs[0])
    row.inputs[1].default_value = 0.5
    v = nodes.new("ShaderNodeMath"); v.operation = "DIVIDE"
    links.new(row.outputs["Value"], v.inputs[0])
    v.inputs[1].default_value = float(max(n_frames, 1))
    uv = nodes.new("ShaderNodeCombineXYZ")
    links.new(u.outputs["Value"], uv.inputs["X"])
    links.new(v.outputs["Value"], uv.inputs["Y"])
    tex = nodes.new("GeometryNodeImageTexture")
    tex.interpolation = "Closest"
    tex.extension = "EXTEND"
    tex.inputs["Image"].default_value = img
    links.new(uv.outputs["Vector"], tex.inputs["Vector"])
    return tex.outputs["Color"], tex.outputs["Alpha"]


def _sense_of(nodes, links, img, part_socket, n_frames, on_socket, math, vmath, contact=None, organs_only=False, soft=False):
    """The sense on a hit's part this frame, gated by the Senses switch and by the hit lying on a part at all: the sense
    light's colour and strength, the tint, the part's scale (1 at rest), the outline's colour and strength.

    contact (0 to 1, the hit's own, from ContactBody): touch lights the hit by the part's touch level (the table's
    fourth field) times its contact, in touch's colour at SENSE_MIX; where the part's own sense light is on as well
    (a pain, a pleasure), the two blend by their strengths and the stronger sets the strength.

    organs_only: the sense light counts on the organs alone (the ears, the eyes, the heart, the lungs): the tiles'
    call, since 2026-11-13, when the senses on the skin became a glow of their own (outline_material). soft: the touch
    comes in over the whole of the contact's fall, a soft edge, for that glow."""
    valid = math("MULTIPLY", math("GREATER_THAN", part_socket, -0.5), on_socket)
    organ = math("GREATER_THAN", part_socket, len(tags.PARTS) - 0.5)
    skin = math("MULTIPLY", valid, math("SUBTRACT", 1.0, organ))
    l_col, l_a = _sense_sample(nodes, links, img, part_socket, 0, n_frames)
    t_col, _ = _sense_sample(nodes, links, img, part_socket, 1, n_frames)
    o_col, o_a = _sense_sample(nodes, links, img, part_socket, 2, n_frames)
    w_col, _ = _sense_sample(nodes, links, img, part_socket, 4, n_frames)
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(t_col, sep.inputs["Vector"])
    sep_w = nodes.new("ShaderNodeSeparateXYZ")
    links.new(w_col, sep_w.inputs["Vector"])
    strength = math("MULTIPLY", l_a, math("MULTIPLY", valid, organ) if organs_only else valid)
    light_s = strength
    touch_lvl = None
    tint = sep.outputs["X"]
    col = l_col
    scale = math("MULTIPLY_ADD", math("SUBTRACT", sep.outputs["Y"], 1.0), valid, 1.0)
    if contact is not None:
        k_col, k_a = _sense_sample(nodes, links, img, part_socket, 3, n_frames)
        # the patch's edge: in full from CONTACT_FULL of contact, so the patch is one brightness to its rim (with the
        # touch falling off over the whole skin, the rim was a wide fringe of dark tiles, 2026-11-12)
        edge = nodes.new("ShaderNodeMapRange")
        edge.interpolation_type = "SMOOTHSTEP"
        edge.inputs["From Min"].default_value = 0.0 if soft else CONTACT_FULL[0]
        edge.inputs["From Max"].default_value = 1.0 if soft else CONTACT_FULL[1]
        links.new(contact, edge.inputs["Value"])
        touch_lvl = math("MULTIPLY", k_a, valid)
        touch = math("MULTIPLY", touch_lvl, edge.outputs["Result"])
        share = math("DIVIDE", touch, math("MAXIMUM", math("ADD", strength, touch), 1e-6))
        mixc = nodes.new("ShaderNodeMix")
        mixc.data_type = "RGBA"
        links.new(share, mixc.inputs["Factor"])
        links.new(l_col, mixc.inputs[6])
        links.new(k_col, mixc.inputs[7])
        col = mixc.outputs[2]
        tint = math("ADD", math("MULTIPLY", tint, math("SUBTRACT", 1.0, share)), math("MULTIPLY", share, SENSE_MIX))
        strength = math("MAXIMUM", strength, touch)
    # the blend of the sense's colour over the part's own: the share the engine gives the part (the table's tint), fully
    # in from SENSE_ON of strength
    on = math("MINIMUM", math("DIVIDE", strength, SENSE_ON), 1.0)
    mix = math("MULTIPLY", on, tint)
    return {"col": col, "s": strength, "tint": tint, "mix": mix, "scale": scale, "light_s": light_s, "touch_lvl": touch_lvl, "skin": skin,
            "warm": math("MULTIPLY", sep_w.outputs["X"], skin), "cool": math("MULTIPLY", sep_w.outputs["Y"], skin),
            "flash": math("MULTIPLY", sep_w.outputs["Z"], skin),
            "clear": math("MULTIPLY", sep.outputs["Z"], valid), "out_col": o_col, "out_s": math("MULTIPLY", o_a, valid)}


def scan_nodes(name, pos_img, col_img, frame_obj, eye_obj, size, fov_deg, field_h, field_v, radius, centre, material,
               peel_pos_img=None, peel_idx_img=None,
               held_frame=False, box=None, spec=None, backdrop=False, sky_fill=False, live_pos_img=None,
               back_pos_img=None, back_col_img=None, idx_img=None, table_obj=None, peel=False, live_idx_img=None, live_idx_pos=None,
               tight=False, senses=False, sense_img=None, n_frames=1, torso_obj=None, contact_obj=None, sheet=False):
    """The geometry: a grid of the scan's pixels, every point moved to its ray's hit in the model's
    frame and pressed onto the glass beyond the knee, the field outside the two eyes' ellipse deleted,
    a splat instanced on each point turned to the sheet the held hits make (its neighbours held the
    same way), as long as its cell along the sheet's slope and as wide as its cell across, the
    picture's colour and coordinate stored for the material.

    held_frame: the pictures are read at the frame on a Value node named MemFrame, keyed by the bake,
    instead of the scene's frame: a memory. box: ((x0, y0, z0), (x1, y1, z1)) in room metres keeps
    only the hits inside it: a patch of memory. A memory's hits are lit by the thought on the thing
    they lie on (Think0 to Think9, keyed, one per region, whole things) or by the eyes being shut
    (Shut), and those the eyes have now, in their field and at the live hit's distance there (the live
    scan's position picture, live_pos_img), are not drawn while the live picture stands (LiveNow): the
    same thing can be seen and remembered at once (his review of 2026-11-08, second), and a memory goes
    the moment a ray reaches its place. While the live picture is going or coming back (the eyes long
    shut, or just opened: LiveNow between SEEN_FADE's marks) such a memory is thinned by the share the
    live picture stands, so the two hand over without a step. backdrop: the pictures are the backdrop scan's (the
    sky, the ground and the range with the near things hidden), kept where the ray from the eyes
    passes through the window's opening (a soft edge at its frame, stored as gate for the material),
    drawn a little beyond the live picture; sky_fill: the pictures are the sky scan's (the sky's
    shell alone), kept where the backdrop's ray (back_pos_img) struck the range or the ground above
    the horizon, so the sky the range hides is remembered down to the horizon.

    idx_img: the scan's index picture, every hit's thing (its object's pass index), and table_obj
    the table of things (LidarScene._thing_table): from them each hit takes its thing's centre and
    radius, which place it (a compact thing is held whole, its shape kept: his sixth review of
    2026-11-09, the crowns drawn as saddles), and its region, which lights it when remembered.

    peel: the pictures are the peel scan's, the far side of the first thing each ray struck: kept where
    that thing is the one the scan's own index picture (live_idx_img) has at the pixel and is held
    whole (compact), coloured by the scan's own picture (the same ray's colour), the splat's front
    away from the eyes where the surface faces; a memory, lit as the backdrop is.

    sheet: the picture's pixels are joined into connected sheets wherever neighbours lie on one thing and step
    evenly in depth (the seen picture: a surface whole at any slant, its edge a line), and only the pixels no
    sheet takes are drawn as splats."""
    W, H = size
    live_pos_img = pos_img if live_pos_img is None else live_pos_img
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links

    def math(op, a=None, b=None, c=None):
        n = nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                links.new(v, n.inputs[i])
        return n.outputs["Value"]

    def vmath(op, a=None, b=None, scale=None):
        n = nodes.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (tuple, list, Vector)):
                n.inputs[i].default_value = tuple(v)
            else:
                links.new(v, n.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)):
                n.inputs["Scale"].default_value = float(scale)
            else:
                links.new(scale, n.inputs["Scale"])
        return n.outputs["Vector"] if op not in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Value"]

    # a surface that is not visible has no geometry at all: a transparent splat still occluded the
    # live ones where the two coincided (found 2026-11-08), and the render is spared the work
    visible = nodes.new("ShaderNodeValue")
    visible.name = "Visible"
    visible.label = "Visible"
    visible.outputs[0].default_value = 1.0
    if held_frame:
        fv = nodes.new("ShaderNodeValue")
        fv.name = "MemFrame"
        fv.label = "MemFrame"
        fv.outputs[0].default_value = 1.0
        frame_socket = fv.outputs[0]
        # the memory's depth against the live picture's (Shrink, keyed: MEM_SHRINK for a picture from
        # another time, 1 for one completing this frame's)
        shrink = nodes.new("ShaderNodeValue")
        shrink.name = "Shrink"
        shrink.label = "Shrink"
        shrink.outputs[0].default_value = MEM_SHRINK
    else:
        time = nodes.new("GeometryNodeInputSceneTime")
        frame_socket = time.outputs["Frame"]

    def sample(img, uv_socket, frame=None):
        tex = nodes.new("GeometryNodeImageTexture")
        tex.interpolation = "Closest"
        tex.extension = "EXTEND"
        tex.inputs["Image"].default_value = img
        links.new(uv_socket, tex.inputs["Vector"])
        links.new(frame_socket if frame is None else frame, tex.inputs["Frame"])
        return tex.outputs["Color"]

    go = nodes.new("NodeGroupOutput")
    grid = nodes.new("GeometryNodeMeshGrid")
    grid.inputs["Size X"].default_value = 1.0
    grid.inputs["Size Y"].default_value = 1.0
    grid.inputs["Vertices X"].default_value = W
    grid.inputs["Vertices Y"].default_value = H
    # the picture coordinate of every grid point, stored by name first: a Position node reads the
    # geometry where it is consumed, so after Set Position it would read the hit, not the grid
    pin = nodes.new("GeometryNodeInputPosition")
    uv0 = vmath("ADD", pin.outputs["Position"], (0.5, 0.5, 0.0))
    st = nodes.new("GeometryNodeStoreNamedAttribute")
    st.data_type = "FLOAT2"
    st.domain = "POINT"
    st.inputs["Name"].default_value = "scan_uv"
    links.new(grid.outputs["Mesh"], st.inputs["Geometry"])
    links.new(uv0, st.inputs["Value"])
    named = nodes.new("GeometryNodeInputNamedAttribute")
    named.data_type = "FLOAT_VECTOR"   # read back as a vector: the input node has no two-component type
    named.inputs["Name"].default_value = "scan_uv"
    uv = named.outputs["Attribute"]
    # the picture's colour, stored for the material
    stc = nodes.new("GeometryNodeStoreNamedAttribute")
    stc.data_type = "FLOAT_COLOR"
    stc.domain = "POINT"
    stc.inputs["Name"].default_value = "scan_col"
    links.new(st.outputs["Geometry"], stc.inputs["Geometry"])
    links.new(sample(col_img, uv), stc.inputs["Value"])
    # the hit and its four neighbours, in room metres
    uv_r, uv_u = vmath("ADD", uv, (1.0 / W, 0.0, 0.0)), vmath("ADD", uv, (0.0, 1.0 / H, 0.0))
    uv_l, uv_d = vmath("ADD", uv, (-1.0 / W, 0.0, 0.0)), vmath("ADD", uv, (0.0, -1.0 / H, 0.0))
    p_room = sample(pos_img, uv)
    p_right, p_up, p_left, p_down = (sample(pos_img, q) for q in (uv_r, uv_u, uv_l, uv_d))
    # the thing each hit lies on, by the index the scan's index pass wrote beside its position, and the
    # thing's row in the table: for the hit and for its four neighbours, since a splat's sheet is laid
    # only between hits on one thing (his eighth review of 2026-11-10)

    def id_of(uv_socket, img=None):
        img = idx_img if img is None else img
        if img is None:
            return math("ADD", 0.0, 0.0)
        sep_i = nodes.new("ShaderNodeSeparateXYZ")
        links.new(sample(img, uv_socket), sep_i.inputs["Vector"])
        return math("ROUND", sep_i.outputs["X"])

    id_hit = id_of(uv)
    ids = {"right": id_of(uv_r), "up": id_of(uv_u), "left": id_of(uv_l), "down": id_of(uv_d)}
    same = {k: math("COMPARE", v, id_hit, 0.5) for k, v in ids.items()}
    thing_hit = _thing_lookup(nodes, links, table_obj, id_hit)
    things = {k: _thing_lookup(nodes, links, table_obj, v) for k, v in ids.items()}
    sense = None
    if senses and sense_img is not None:
        # the sense on the hit's part this frame (rung 2p): its colour replaces the picture's by its strength and tint
        # (below, scan_col), and a breathing part's hits are scaled about the torso (the chest with the lungs, gently)
        on = nodes.new("ShaderNodeValue")
        on.name = "Senses"
        on.label = "Senses"
        on.outputs[0].default_value = 1.0
        # touch by contact: the hit's own contact, read off ContactBody at the hit's room point (a remembered hit's only
        # where the body still is)
        # (the senses on the skin are a glow of their own since 2026-11-13: the tiles carry the organs' alone, and no touch)
        sense = _sense_of(nodes, links, sense_img, thing_hit["part"], n_frames, on.outputs[0], math, vmath, organs_only=True)
        if torso_obj is not None:
            torso = nodes.new("GeometryNodeObjectInfo")
            torso.transform_space = "ORIGINAL"
            torso.inputs["Object"].default_value = torso_obj
            pc = torso.outputs["Location"]

            def breathe(q):
                return vmath("ADD", pc, vmath("SCALE", vmath("SUBTRACT", q, pc), scale=sense["scale"]))

            p_room, p_right, p_up, p_left, p_down = (breathe(q) for q in (p_room, p_right, p_up, p_left, p_down))
    if peel:
        # the far side counts only where it is the far side of the thing the scan's own ray struck first
        same_thing = math("COMPARE", id_hit, id_of(uv, live_idx_img), 0.5)
    # a hit on the sky's shell lies on one of its flat facets (a 32 by 16 sphere), so the sheet's
    # normal would kink by eleven degrees at every facet edge: every far hit, and the neighbours that
    # give its sheet, is snapped onto the shell's exact sphere, and the sheet is the sphere
    shell_centre = (spec.size[0] / 2.0, spec.size[1] / 2.0, 0.0) if spec is not None else (0.0, 0.0, 0.0)

    def on_shell(p):
        r = vmath("SUBTRACT", p, shell_centre)
        far = math("GREATER_THAN", vmath("LENGTH", r), SKY_FAR)
        snapped = vmath("ADD", vmath("SCALE", vmath("NORMALIZE", r), scale=engine.SKY_DISTANCE), shell_centre)
        pick_p = nodes.new("ShaderNodeMix")
        pick_p.data_type = "VECTOR"
        links.new(far, pick_p.inputs["Factor"])
        links.new(p, pick_p.inputs[4])
        links.new(snapped, pick_p.inputs[5])
        return pick_p.outputs[1]

    p_room, p_right, p_up, p_left, p_down = (on_shell(q) for q in (p_room, p_right, p_up, p_left, p_down))
    t_right = vmath("SUBTRACT", p_right, p_room)
    t_up = vmath("SUBTRACT", p_up, p_room)
    t_left = vmath("SUBTRACT", p_left, p_room)
    t_down = vmath("SUBTRACT", p_down, p_room)
    # into the model's frame: the ModelFrame empty carries the head frame and the mind's zoom
    info = nodes.new("GeometryNodeObjectInfo")
    info.transform_space = "ORIGINAL"
    info.inputs["Object"].default_value = frame_obj
    tp = nodes.new("FunctionNodeTransformPoint")
    links.new(p_room, tp.inputs["Vector"])
    links.new(info.outputs["Transform"], tp.inputs["Transform"])

    def direction(src):
        n = nodes.new("FunctionNodeTransformDirection")
        links.new(src, n.inputs["Direction"])
        links.new(info.outputs["Transform"], n.inputs["Transform"])
        return n.outputs["Direction"]

    # every distance is taken from the eyes themselves, not the skull's centre: the pressing onto the
    # glass then runs along the eyes' own rays, so from the eyes nothing shifts and no seam opens
    # between a near hit and the pressed far one beside it
    eye = nodes.new("GeometryNodeObjectInfo")
    eye.transform_space = "ORIGINAL"
    eye.inputs["Object"].default_value = eye_obj
    v = vmath("SUBTRACT", tp.outputs["Vector"], eye.outputs["Location"])
    d = vmath("LENGTH", v)
    # the eyes in room metres, and the hit's place in the room, for the tests below
    inv_frame = nodes.new("FunctionNodeInvertMatrix")
    links.new(info.outputs["Transform"], inv_frame.inputs["Matrix"])
    eye_room = nodes.new("FunctionNodeTransformPoint")
    links.new(eye.outputs["Location"], eye_room.inputs["Vector"])
    links.new(inv_frame.outputs["Matrix"], eye_room.inputs["Transform"])
    sep_room = nodes.new("ShaderNodeSeparateXYZ")
    links.new(p_room, sep_room.inputs["Vector"])
    # the distance as the mind holds it (his review of 2026-11-08: the window, the ridge and the sky
    # all sat at the glass): in room metres, within reach as it is, beyond reach compressed so the
    # far things keep their order and not their scale (triview/engine.py believed); before the far
    # field has resolved (Resolve 0) everything beyond reach lies flat at the sky's distance, as the
    # sun does the moment it hits; and onto the glass beyond the knee, for what the believed distance
    # still leaves outside: straight to knee * radius, then eased toward the radius without reaching it
    sep_t = nodes.new("FunctionNodeSeparateTransform")
    links.new(info.outputs["Transform"], sep_t.inputs["Transform"])
    sep_s = nodes.new("ShaderNodeSeparateXYZ")
    links.new(sep_t.outputs["Scale"], sep_s.inputs["Vector"])
    mscale = sep_s.outputs["X"]
    resolve = nodes.new("ShaderNodeValue")
    resolve.name = "Resolve"
    resolve.label = "Resolve"
    resolve.outputs[0].default_value = 1.0
    knee = KNEE * radius
    span = radius - knee

    def ordered_of(d_room_):
        """A room distance compressed beyond the mind's reach (triview/engine.py _ordered)."""
        b_near = math("MINIMUM", d_room_, engine.BELIEVE_NEAR)
        b_over = math("MAXIMUM", math("SUBTRACT", d_room_, engine.BELIEVE_NEAR), 0.0)
        ln = nodes.new("ShaderNodeMath")
        ln.operation = "LOGARITHM"
        links.new(math("ADD", math("DIVIDE", b_over, engine.BELIEVE_K), 1.0), ln.inputs[0])
        ln.inputs[1].default_value = 2.718281828459045
        return math("ADD", b_near, math("MULTIPLY", ln.outputs["Value"], engine.BELIEVE_K))

    def place(v_, d_, thing):
        """A hit at v_ from the eyes (model metres, d_ its length) on a thing (its table row) to where
        the mind holds it; returns the point, its pressed distance and its room distance. The rule
        (triview/engine.py believed_hit): a compact thing, small against its distance, is scaled whole
        about the eyes by its centre's believed distance over its true one, so it keeps its shape and
        its angular size; a thing that spans its distance (the ground, the range, the sky) is
        compressed hit by hit, in order; between the two by its radius over its distance (COMPACT).
        Before the far field resolves, everything beyond the reach lies flat at the sky."""
        d_room_ = math("DIVIDE", d_, mscale)
        ordered = ordered_of(d_room_)
        dc = math("MAXIMUM", vmath("LENGTH", vmath("SUBTRACT", thing["centre"], eye_room.outputs["Vector"])), 1e-3)
        shape = math("MULTIPLY", ordered_of(dc), math("DIVIDE", d_room_, dc))
        compact = nodes.new("ShaderNodeMapRange")
        compact.interpolation_type = "SMOOTHSTEP"
        compact.inputs["From Min"].default_value = engine.COMPACT[0]
        compact.inputs["From Max"].default_value = engine.COMPACT[1]
        compact.inputs["To Min"].default_value = 1.0
        compact.inputs["To Max"].default_value = 0.0
        links.new(math("DIVIDE", thing["radius"], dc), compact.inputs["Value"])
        resolved = math("ADD", ordered, math("MULTIPLY", math("SUBTRACT", shape, ordered), compact.outputs["Result"]))
        b_far = math("MAXIMUM", math("SUBTRACT", d_room_, engine.BELIEVE_FLAT_FROM), 0.0)
        flat_rise = math("SUBTRACT", 1.0, math("EXPONENT", math("DIVIDE", b_far, -engine.BELIEVE_FLAT_K)))
        flat = math("ADD", math("MINIMUM", ordered, engine.BELIEVE_FLAT_BASE),
                    math("MULTIPLY", flat_rise, engine.BELIEVE_SKY - engine.BELIEVE_FLAT_BASE))
        believed = math("ADD", flat, math("MULTIPLY", math("SUBTRACT", resolved, flat), resolve.outputs[0]))
        d_b = math("MULTIPLY", believed, mscale)
        near = math("MINIMUM", d_b, knee)
        over = math("MAXIMUM", math("SUBTRACT", d_b, knee), 0.0)
        eased = math("MULTIPLY", math("SUBTRACT", 1.0, math("EXPONENT", math("MULTIPLY", math("DIVIDE", over, span), -1.0))), span)
        d_pressed_ = math("ADD", near, eased)
        ratio = math("DIVIDE", d_pressed_, math("MAXIMUM", d_, 1e-6))
        if held_frame:
            ratio = math("MULTIPLY", ratio, shrink.outputs[0])
        if backdrop:
            ratio = math("MULTIPLY", ratio, BACK_PUSH)
        if sky_fill:
            ratio = math("MULTIPLY", ratio, SKY_PUSH)
        return vmath("ADD", vmath("SCALE", v_, scale=ratio), eye.outputs["Location"]), d_pressed_, d_room_, compact.outputs["Result"]

    p_model, d_pressed, d_room, compact_w = place(v, d, thing_hit)
    facing = vmath("NORMALIZE", v)
    # a rim pixel: a hit with a neighbour on another thing
    rim_any = math("SUBTRACT", 1.0, math("MINIMUM", math("MINIMUM", same["right"], same["up"]), math("MINIMUM", same["left"], same["down"])))
    # the neighbours to the right and above, held the same way: the splat lies along the sheet the
    # held hits make (the far ground curves toward the eyes) and covers its cell of it, so from the
    # side the rows of a grazing surface close instead of parting into rings (his review of
    # 2026-11-09: moire lines)

    def neighbour(p_room_n, thing_n):
        tp_n = nodes.new("FunctionNodeTransformPoint")
        links.new(p_room_n, tp_n.inputs["Vector"])
        links.new(info.outputs["Transform"], tp_n.inputs["Transform"])
        v_n = vmath("SUBTRACT", tp_n.outputs["Vector"], eye.outputs["Location"])
        return place(v_n, vmath("LENGTH", v_n), thing_n)[0]

    # the sheet's two tangents, each toward the neighbour on the same thing: the one to the right or
    # above, else the one to the left or below turned about, so a splat is never stretched to another
    # thing (a lamp's rim to the wall behind it); on an axis with no neighbour of its own the hit is
    # at the edge of its thing

    nb = {k: neighbour(p_k, things[k]) for k, p_k in (("right", p_right), ("up", p_up), ("left", p_left), ("down", p_down))}

    def tangent(k_a, k_b):
        t_a = vmath("SUBTRACT", nb[k_a], p_model)
        t_b = vmath("SUBTRACT", p_model, nb[k_b])
        pick_t = nodes.new("ShaderNodeMix")
        pick_t.data_type = "VECTOR"
        links.new(same[k_a], pick_t.inputs["Factor"])
        links.new(t_b, pick_t.inputs[4])
        links.new(t_a, pick_t.inputs[5])
        return pick_t.outputs[1], math("MAXIMUM", same[k_a], same[k_b])

    t_right_m, has_u = tangent("right", "left")
    t_up_m, has_v = tangent("up", "down")
    # the way out of the thing in the picture, across the ray: toward the neighbouring rays whose first strike (the
    # live picture's, so the seen surface and the far side agree on it and their halves of a chord coincide) lies
    # farthest from this one in depth. At a rim that is the ray that strikes the thing behind; inside a thing it is
    # the way its surface falls away toward its limb. Radial at a ball's limb, the side face's normal at a box's
    # edge, whatever the thing's shape and wherever its centre: the front of the chord splats, and of every
    # grazing splat, whose sheet's normal means nothing along the ray
    if peel:
        p_live = sample(live_idx_pos, uv)
        p_live_k = {k: sample(live_idx_pos, uv_k) for k, uv_k in (("right", uv_r), ("up", uv_u), ("left", uv_l), ("down", uv_d))}
    else:
        p_live = p_room
        p_live_k = {"right": p_right, "up": p_up, "left": p_left, "down": p_down}
    # the signed gradient of the first strike's depth over two rings of neighbours (the jumps over one ring alone,
    # unsigned, were noisy on a grazing surface, so the chord walls tilted at random): toward the rays whose first
    # strike lies deeper, which at a limb is the way out of the thing, and at a rim the ray that strikes what
    # stands behind
    live_src = live_idx_pos if peel else pos_img
    p_live_k2 = {k: sample(live_src, vmath("ADD", uv, off)) for k, off in (("right", (2.0 / W, 0.0, 0.0)), ("up", (0.0, 2.0 / H, 0.0)),
                                                                             ("left", (-2.0 / W, 0.0, 0.0)), ("down", (0.0, -2.0 / H, 0.0)))}
    d_live = vmath("LENGTH", vmath("SUBTRACT", p_live, eye_room.outputs["Vector"]))
    out_sum = None
    for samples, weight in ((p_live_k, 1.0), (p_live_k2, 0.5)):
        for k, p_k in samples.items():
            to_k = vmath("SUBTRACT", p_k, eye_room.outputs["Vector"])
            dir_k = vmath("NORMALIZE", direction(to_k))
            jump = math("MULTIPLY", math("SUBTRACT", vmath("LENGTH", to_k), d_live), weight)
            step = vmath("SCALE", vmath("SUBTRACT", dir_k, facing), scale=jump)
            out_sum = step if out_sum is None else vmath("ADD", out_sum, step)
    outward = vmath("NORMALIZE", vmath("SUBTRACT", out_sum, vmath("SCALE", facing, scale=vmath("DOT_PRODUCT", out_sum, facing))))
    n_sheet = vmath("NORMALIZE", vmath("CROSS_PRODUCT", t_right_m, t_up_m))
    # at an edge of depth within one thing, where a neighbouring ray struck far nearer or farther on
    # one side alone (a grazing surface steps far on both sides, evenly), and at the edge of the thing,
    # the sheet's normal means nothing: the splat faces the eyes there instead, at its plain footprint.
    # A neighbour on another thing is taken as the mirror of the one on this thing: no jump of its own

    def one_sided(t_a, t_b, same_a, same_b):
        la, lb = vmath("LENGTH", direction(t_a)), vmath("LENGTH", direction(t_b))
        la2 = math("ADD", math("MULTIPLY", la, same_a), math("MULTIPLY", lb, math("SUBTRACT", 1.0, same_a)))
        lb2 = math("ADD", math("MULTIPLY", lb, same_b), math("MULTIPLY", la, math("SUBTRACT", 1.0, same_b)))
        big, small = math("MAXIMUM", la2, lb2), math("MAXIMUM", math("MINIMUM", la2, lb2), 1e-7)
        return math("MULTIPLY", math("GREATER_THAN", big, math("MULTIPLY", d, EDGE_JUMP)),
                    math("GREATER_THAN", math("DIVIDE", big, small), EDGE_RATIO))

    edge = math("MAXIMUM", one_sided(t_right, t_left, same["right"], same["left"]), one_sided(t_up, t_down, same["up"], same["down"]))
    edge = math("MAXIMUM", edge, math("MAXIMUM", math("SUBTRACT", 1.0, has_u), math("SUBTRACT", 1.0, has_v)))
    dot_s = vmath("DOT_PRODUCT", n_sheet, facing)
    cos_s = math("ABSOLUTE", dot_s)
    # the sheet's normal turned inward, so the splat's front faces the eyes: by the normal's sign along the ray,
    # the ray's own for the seen surfaces and its opposite for a far side, where the ray leaves the thing; and
    # where the sheet runs within GRAZE_COS of the ray, as at a limb, where that sign means nothing, away from
    # the way out of the thing (outward, above), so the splat still faces outward (his tenth review of
    # 2026-11-10: from the side half the limb showed its clear back; the centre of the thing until his eleventh,
    # which turns a crown's underside over, the tree's centre being in its trunk)
    sgn_ray = math("MULTIPLY", math("SIGN", dot_s), -1.0 if peel else 1.0)
    sgn_out = math("MULTIPLY", math("SIGN", vmath("DOT_PRODUCT", n_sheet, outward)), -1.0)
    grazing = math("LESS_THAN", cos_s, GRAZE_COS)
    sgn = math("ADD", sgn_ray, math("MULTIPLY", math("SUBTRACT", sgn_out, sgn_ray), grazing))
    n_toward = vmath("SCALE", n_sheet, scale=sgn)
    # a pixel whose sheet runs within TILT_COS of the ray, a limb, is a coin: a splat facing the eyes at the plain
    # footprint, which covers its pixel from the eyes (in its sheet it would be edge-on there, and faded) and is
    # edge-on from the side, where its chord splat closes the band (his eleventh review of 2026-11-11): every
    # grazing pixel of a thing held whole, whose grazing pixels lie at its limbs, and a rim pixel of a thing that
    # spans its distance, whose grazing rows (the far ground) must still close from the side in their sheet
    whole = math("GREATER_THAN", compact_w, 0.5)
    # every rim pixel of a thing held whole is a coin, grazing or not: its own colour is a silhouette's mix with what
    # stands behind, right from the eyes and a pale dash from anywhere else (the chord at the pixel, in the thing's
    # interior colour, stands for the surface from the side)
    coin = math("MAXIMUM", math("MULTIPLY", rim_any, whole), math("MULTIPLY", math("MAXIMUM", rim_any, whole), math("LESS_THAN", cos_s, TILT_COS)))
    edge = math("MAXIMUM", edge, coin)
    # for the shader: a coin is drawn for the camera on the eyes' own ray alone
    for nm, dtype, val in (("coin", "FLOAT", coin), ("ray", "FLOAT_VECTOR", facing)):
        st_c = nodes.new("GeometryNodeStoreNamedAttribute")
        st_c.data_type = dtype
        st_c.domain = "POINT"
        st_c.inputs["Name"].default_value = nm
        links.new(stc.outputs["Geometry"], st_c.inputs["Geometry"])
        links.new(val, st_c.inputs["Value"])
        stc = st_c
    if peel:
        # the chord's condition, shared with the seen surface: the front's own sheet in the live picture, its
        # tangents toward the neighbours on the front's thing as the seen surface lays them (a thing held whole
        # is scaled whole about the eyes, so the angle to the ray is the same in the room as in the model); the
        # far hit's own sheet decided until his eleventh review of 2026-11-11, so the two halves of a chord stood
        # on different pixels and the sky showed through where one was missing
        id_front = id_of(uv, live_idx_img)
        same_live = {k: math("COMPARE", id_of(uv_k, live_idx_img), id_front, 0.5) for k, uv_k in (("right", uv_r), ("up", uv_u), ("left", uv_l), ("down", uv_d))}
        rim_live = math("SUBTRACT", 1.0, math("MINIMUM", math("MINIMUM", same_live["right"], same_live["up"]), math("MINIMUM", same_live["left"], same_live["down"])))

        def tangent_live(k_a, k_b):
            t_a = vmath("SUBTRACT", p_live_k[k_a], p_live)
            t_b = vmath("SUBTRACT", p_live, p_live_k[k_b])
            pick_l = nodes.new("ShaderNodeMix")
            pick_l.data_type = "VECTOR"
            links.new(same_live[k_a], pick_l.inputs["Factor"])
            links.new(t_b, pick_l.inputs[4])
            links.new(t_a, pick_l.inputs[5])
            return pick_l.outputs[1]

        n_front = vmath("NORMALIZE", vmath("CROSS_PRODUCT", tangent_live("right", "left"), tangent_live("up", "down")))
        ray_room = vmath("NORMALIZE", vmath("SUBTRACT", p_live, eye_room.outputs["Vector"]))
        graze_chord = math("LESS_THAN", math("ABSOLUTE", vmath("DOT_PRODUCT", n_front, ray_room)), TILT_COS)
        same_c = same_live
    else:
        graze_chord = math("LESS_THAN", cos_s, TILT_COS)
        same_c = same
    # a silhouette rim: a neighbouring ray on another thing that strikes deeper (the thing behind). Beyond such a
    # pixel the surface still runs along the ray to the limb, grazing or not as the pixel's own sheet may be (a
    # faceted crown's rim pixels graze the ray only half the time), so every one carries a chord; a rim against a
    # thing in front, whose neighbouring ray strikes nearer, carries none: the surface goes on behind that thing,
    # and a chord would be a wall through this one's inside (the pane's bar over a crown)
    rim_far = None
    for k in ("right", "up", "left", "down"):
        deeper = math("GREATER_THAN", vmath("LENGTH", vmath("SUBTRACT", p_live_k[k], eye_room.outputs["Vector"])), math("ADD", d_live, 1e-4))
        edge_k = math("MULTIPLY", math("SUBTRACT", 1.0, same_c[k]), deeper)
        rim_far = edge_k if rim_far is None else math("MAXIMUM", rim_far, edge_k)
    coin_chord = math("MULTIPLY", whole, math("MAXIMUM", rim_far, graze_chord))
    pick = nodes.new("ShaderNodeMix")
    pick.data_type = "VECTOR"
    links.new(edge, pick.inputs["Factor"])
    links.new(n_toward, pick.inputs[4])
    links.new(facing, pick.inputs[5])
    n_model = pick.outputs[1]
    # the splat's size: as long as its cell along the sheet's slope (the ray's direction laid in the
    # splat's plane) and as wide as its cell across, so a grazing surface closes from the side and
    # from the eyes the splat covers its pixel and no more; at an edge of depth the plain footprint
    pixel_angle = fov_deg * 3.141592653589793 / 180.0 / W
    base = math("MULTIPLY", d_pressed, pixel_angle * OVERLAP)
    slope = vmath("NORMALIZE", vmath("SUBTRACT", facing, vmath("SCALE", n_model, scale=vmath("DOT_PRODUCT", facing, n_model))))
    across_dir = vmath("CROSS_PRODUCT", n_model, slope)

    # the glass layer alone (tight): on an axis of the scan with no neighbour on the glass, at a spike of the pane's
    # outline one pixel thin, a tile has no cell of its own. Its tangent there runs to the neighbouring ray's place,
    # and a ray that struck no glass has none in the pane's pictures (index 0, position nought), so that place is the
    # room's origin: the tile, laid to that length in a direction the rounding chose (it faces the eyes there, and its
    # slope is the rounding's leftover), stood across the picture as a strip of the reflection's light for one frame
    # (found in the last showcase's frames, 2026-11-18: 612 and 3016, thinner ones through his turn at 3011 to 3030).
    # There a tile is no longer than its pixel's plain footprint. Every other tile keeps its cell to the last digit
    # (the two factors are exactly 0 and 1), so a frame with no such tile is drawn as it was
    lone = math("SUBTRACT", 1.0, math("MINIMUM", has_u, has_v)) if tight else None
    plain = math("MULTIPLY", d_pressed, pixel_angle) if tight else None

    def cell_of(axis):
        # the cell's whole support along the axis: the sum of its two edges' projections (the larger
        # alone left pinholes on a crown, where the slope runs diagonally across the scan's grid)
        cell = math("ADD", math("ABSOLUTE", vmath("DOT_PRODUCT", t_right_m, axis)), math("ABSOLUTE", vmath("DOT_PRODUCT", t_up_m, axis)))
        if tight:
            return math("ADD", math("MULTIPLY", cell, math("SUBTRACT", 1.0, lone)), math("MULTIPLY", math("MINIMUM", cell, plain), lone))
        return cell

    def extent(axis):
        cell = cell_of(axis)
        if tight:
            # the glass layer's tiles (rung 2o) are cut to their cells, no stretch and no overlap beyond the smallest tile
            return math("MAXIMUM", cell, radius * SPLAT_MIN)
        sized = math("MINIMUM", math("MAXIMUM", math("MULTIPLY", cell, OVERLAP), radius * SPLAT_MIN), radius * 0.06)
        cap = math("MULTIPLY_ADD", compact_w, STRETCH_COMPACT - STRETCH_MAX, STRETCH_MAX)
        sized = math("MINIMUM", sized, math("MULTIPLY", base, cap))
        return math("MULTIPLY_ADD", math("SUBTRACT", sized, base), math("SUBTRACT", 1.0, edge), base)

    size_ = nodes.new("ShaderNodeCombineXYZ")
    links.new(extent(slope), size_.inputs["X"])
    links.new(extent(across_dir), size_.inputs["Y"])
    size_.inputs["Z"].default_value = 1.0
    if tight:
        # an added layer conserves its light: a tile larger than its cell (the smallest tile is a render pixel of the close
        # camera, many times a cell of a near thing with the model zoomed out) carries its cell's share of the picture,
        # so however many tiles stack on a point they sum to the picture once (cover, for the material)
        cover = math("MINIMUM", math("DIVIDE", math("MULTIPLY", cell_of(slope), cell_of(across_dir)),
                                     math("MAXIMUM", math("MULTIPLY", extent(slope), extent(across_dir)), 1e-14)), 1.0)
        st_cv = nodes.new("GeometryNodeStoreNamedAttribute")
        st_cv.data_type = "FLOAT"
        st_cv.domain = "POINT"
        st_cv.inputs["Name"].default_value = "cover"
        links.new(stc.outputs["Geometry"], st_cv.inputs["Geometry"])
        links.new(cover, st_cv.inputs["Value"])
        stc = st_cv
    # the rendering camera, for the turn of a splat it would see edge-on (toward_camera, below)
    active_cam = nodes.new("GeometryNodeInputActiveCamera")
    cam_info = nodes.new("GeometryNodeObjectInfo")
    cam_info.transform_space = "ORIGINAL"
    links.new(active_cam.outputs["Active Camera"], cam_info.inputs["Object"])

    def toward_camera(front, at):
        """A splat's front turned toward the rendering camera where the camera would see it edge-on: a flat tile
        tangent to a curved thing at the camera's own silhouette has no width from there and let the backdrop
        through; turned by CAM_TILT of the view at full turn it keeps a third of its width (his eleventh review of
        2026-11-11). Nothing turns where the front already faces the camera by CAM_TILT_COS."""
        view = vmath("NORMALIZE", vmath("SUBTRACT", at, cam_info.outputs["Location"]))
        c = math("ABSOLUTE", vmath("DOT_PRODUCT", front, view))
        w = nodes.new("ShaderNodeMapRange")
        w.interpolation_type = "SMOOTHSTEP"
        w.inputs["From Min"].default_value = CAM_TILT_COS
        w.inputs["From Max"].default_value = 0.0
        w.inputs["To Min"].default_value = 0.0
        w.inputs["To Max"].default_value = 1.0
        links.new(c, w.inputs["Value"])
        return vmath("NORMALIZE", vmath("SUBTRACT", front, vmath("SCALE", view, scale=math("MULTIPLY", w.outputs["Result"], CAM_TILT))))
    # a memory's drift (his eleventh review of 2026-11-11): its hits ripple across the eyes' rays with a slow
    # noise in the thing's own grain, like heat over a road, so what is remembered never sits as still as what
    # is seen, and keeps its colour. The noise is a field over the room, so neighbours drift together and the
    # memories' seams stay closed; a picture completing this frame's (Shrink 1) holds still against the live
    # picture it completes. Nothing for the seen surface and the live fills
    p_draw = p_model
    heat_off = None
    if held_frame:
        tm = nodes.new("GeometryNodeInputSceneTime")
        wave_w = math("LESS_THAN", shrink.outputs[0], 0.9999)
        if backdrop and live_idx_img is not None and live_pos_img is not None:
            # a picture completing this frame's (the backdrop, the remembered sky) holds still at the seams of the eyes'
            # picture alone, by the band the known shapes hold by (_seam_map), and ripples away from them as every
            # memory does (2026-11-15: held still whole, the outside remembered behind what he sees did not shimmer
            # as the rest). A picture from another time ripples whole, as ever; the map is not worked out for it
            now_b = nodes.new("GeometryNodeInputSceneTime")
            seam_b = _seam_map(nodes, links, math, vmath, live_idx_img, live_pos_img, now_b.outputs["Frame"], eye_room.outputs["Vector"], fov_deg)
            # (how far it is held is the wide band, as for the known shapes' tiles: SEAM_WIDE. By the seam band times
            # three until 2026-11-15, whole to three degrees and gone a degree and a half on: the sky the ridge hides
            # from his eyes rippled right above the ridge's line from the camera's side, as streaks)
            free_b = math("SUBTRACT", 1.0, _seam_at(nodes, links, vmath, seam_b, uv, "band_wide"))
            pick_b = nodes.new("GeometryNodeSwitch")
            pick_b.input_type = "FLOAT"
            links.new(wave_w, pick_b.inputs["Switch"])
            links.new(free_b, pick_b.inputs["False"])
            pick_b.inputs["True"].default_value = 1.0
            wave_w = pick_b.outputs["Output"]
        axes_model = []
        for k in range(3):
            ax_c = nodes.new("ShaderNodeCombineXYZ")
            ax_c.inputs[k].default_value = 1.0
            axes_model.append(vmath("NORMALIZE", direction(ax_c.outputs["Vector"])))

        # the thing the hit's thing ripples with (the table's wave_id: itself, or the thing it is set into, lies on or
        # rests on), and how far THAT thing is held whole
        dc_wave = math("MAXIMUM", vmath("LENGTH", vmath("SUBTRACT", thing_hit["wave_centre"], eye_room.outputs["Vector"])), 1e-3)
        own_wave = nodes.new("ShaderNodeMapRange")
        own_wave.interpolation_type = "SMOOTHSTEP"
        own_wave.inputs["From Min"].default_value = engine.COMPACT[0]
        own_wave.inputs["From Max"].default_value = engine.COMPACT[1]
        own_wave.inputs["To Min"].default_value = 1.0
        own_wave.inputs["To Max"].default_value = 0.0
        links.new(math("DIVIDE", thing_hit["wave_radius"], dc_wave), own_wave.inputs["Value"])

        def heat(q_room):
            """The memory's ripple at a room point, in model metres across the ray, and the wave's level there (_heat)."""
            # (own_body: a hit on a piece of his own body keeps the body's small ripple, as his body's known shape does: he
            # feels his body at every moment, whether or not he last saw that piece. Until the audit of 2026-11-15 the
            # pieces of his body in a remembered picture took the full ripple, three times the rest of his body's)
            return _heat(nodes, links, q_room, thing_hit["radius"], d_room, d_pressed, pixel_angle, axes_model, facing, tm, hold=wave_w,
                         eye_room=eye_room.outputs["Vector"], own_body=math("GREATER_THAN", thing_hit["part"], -0.5),
                         thing=thing_hit["wave_id"], own=own_wave.outputs["Result"], table=table_obj,
                         bend_radius=thing_hit["wave_radius"])

        heat_off, heat_lvl = heat(p_room)
        p_draw = vmath("ADD", p_model, heat_off)
        if backdrop:
            # what completes a picture stands a hair farther from the RENDERING camera than the picture, along the
            # camera's own line of sight, so nothing moves in the picture: the backdrop by BACK_BEHIND of the glass
            # radius, the remembered sky behind it by SKY_BEHIND. They lie at the picture's own depth (BACK_PUSH,
            # SKY_PUSH), and while the far field still lies flat against the sky the bushes, the ground behind them,
            # the range and the sky behind it share every pixel: rippling each on its own they took the pixels in
            # patches of two colours (2026-11-15, the window in the doze)
            from_cam = vmath("NORMALIZE", vmath("SUBTRACT", p_draw, cam_info.outputs["Location"]))
            p_draw = vmath("ADD", p_draw, vmath("SCALE", from_cam, scale=radius * (SKY_BEHIND if sky_fill else BACK_BEHIND)))
    # the points: moved to their hits, the field outside the ellipse removed, and outside the box
    setp = nodes.new("GeometryNodeSetPosition")
    links.new(stc.outputs["Geometry"], setp.inputs["Geometry"])
    links.new(p_draw, setp.inputs["Position"])
    cen = vmath("SUBTRACT", uv, (0.5, 0.5, 0.0))
    ell = vmath("LENGTH", vmath("MULTIPLY", cen, (2.0 * fov_deg / field_h, 2.0 * fov_deg / field_v, 0.0)))
    outside = nodes.new("FunctionNodeCompare")
    outside.data_type = "FLOAT"
    outside.operation = "GREATER_THAN"
    links.new(ell, outside.inputs[0])
    outside.inputs[1].default_value = 1.0
    drop = outside.outputs["Result"]
    if box is not None:
        lo, hi = box
        d_lo = vmath("SUBTRACT", p_room, tuple(lo))
        d_hi = vmath("SUBTRACT", tuple(hi), p_room)
        inner = vmath("MINIMUM", d_lo, d_hi)
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(inner, sep.inputs["Vector"])
        least = math("MINIMUM", math("MINIMUM", sep.outputs["X"], sep.outputs["Y"]), sep.outputs["Z"])
        out_box = math("LESS_THAN", least, 0.0)
        drop = math("MAXIMUM", drop, out_box)
    drop = math("MAXIMUM", drop, math("LESS_THAN", visible.outputs[0], 0.01))
    # a frame with no picture (the placeholder, a missing file) puts every hit at the room's origin
    drop = math("MAXIMUM", drop, math("LESS_THAN", vmath("LENGTH", p_room), 0.01))
    geom_in = setp.outputs["Geometry"]
    room_w = spec.size[0] if spec is not None else 4.0
    # which of the ten things the mind can think of the hit belongs to: its thing's region, from the
    # table, so a memory is lit thing by thing, whole (the bed lights, the floor beside it does not)
    weights = [math("COMPARE", thing_hit["region"], float(i), 0.5) for i in range(MEM_REGION_COUNT)]
    gate = 1.0
    if backdrop:
        # kept where the ray from the eyes passes through the window's opening at the jambs' inner
        # plane, with a soft edge at the frame
        xp, wy0, wy1, wz0, wz1 = room_w - 0.02, *spec.window
        sep_e = nodes.new("ShaderNodeSeparateXYZ")
        links.new(eye_room.outputs["Vector"], sep_e.inputs["Vector"])
        dir_room = vmath("NORMALIZE", vmath("SUBTRACT", p_room, eye_room.outputs["Vector"]))
        sep_d = nodes.new("ShaderNodeSeparateXYZ")
        links.new(dir_room, sep_d.inputs["Vector"])
        t_cross = math("DIVIDE", math("SUBTRACT", xp, sep_e.outputs["X"]), math("MAXIMUM", sep_d.outputs["X"], 1e-3))
        y_cross = math("MULTIPLY_ADD", sep_d.outputs["Y"], t_cross, sep_e.outputs["Y"])
        z_cross = math("MULTIPLY_ADD", sep_d.outputs["Z"], t_cross, sep_e.outputs["Z"])

        def soft_in(value, lo, hi):
            a = nodes.new("ShaderNodeMapRange"); a.interpolation_type = "SMOOTHSTEP"
            a.inputs["From Min"].default_value = lo; a.inputs["From Max"].default_value = lo + WINDOW_MARGIN
            a.inputs["To Min"].default_value = 0.0; a.inputs["To Max"].default_value = 1.0
            links.new(value, a.inputs["Value"])
            b = nodes.new("ShaderNodeMapRange"); b.interpolation_type = "SMOOTHSTEP"
            b.inputs["From Min"].default_value = hi - WINDOW_MARGIN; b.inputs["From Max"].default_value = hi
            b.inputs["To Min"].default_value = 1.0; b.inputs["To Max"].default_value = 0.0
            links.new(value, b.inputs["Value"])
            return math("MULTIPLY", a.outputs["Result"], b.outputs["Result"])

        gate = math("MULTIPLY", math("MULTIPLY", soft_in(y_cross, wy0, wy1), soft_in(z_cross, wz0, wz1)),
                    math("GREATER_THAN", sep_d.outputs["X"], 0.05))
        if sky_fill:
            # the dome remembered wherever the backdrop's ray did not reach the sky above the horizon:
            # the sky's own picture above the horizon the mind imagines without the range, and below
            # it the ground as the eyes saw it in that direction, carried out to the dome, so a camera
            # looking down past the ridge sees the imagined plain beyond the range and its horizon,
            # never a hole (the sky texture itself goes dark a few degrees below the horizon)
            p_back = sample(back_pos_img, uv)
            d_back = vmath("LENGTH", vmath("SUBTRACT", p_back, eye_room.outputs["Vector"]))
            elev = sep_d.outputs["Z"]
            sky_here = math("MULTIPLY", math("GREATER_THAN", d_back, SKY_FAR), math("GREATER_THAN", elev, 0.0))
            if sheet:
                # as a sheet it runs on SEAM_UNDER pixels under the sky's own rim (the sky's sheet ends a pixel short of
                # where this one began, and the black behind showed between them as a dotted line): gone only where
                # every pixel that near is the sky's too
                blur_k = nodes.new("GeometryNodeBlurAttribute")
                blur_k.data_type = "FLOAT"
                links.new(sky_here, _sock(blur_k.inputs, "Value"))
                blur_k.inputs["Iterations"].default_value = SEAM_UNDER
                sky_here = math("GREATER_THAN", _sock(blur_k.outputs, "Value"), 0.9999)
            drop = math("MAXIMUM", drop, sky_here)
            hz = nodes.new("ShaderNodeMapRange"); hz.interpolation_type = "SMOOTHSTEP"
            hz.inputs["From Min"].default_value = -HORIZON_SOFT; hz.inputs["From Max"].default_value = HORIZON_SOFT
            hz.inputs["To Min"].default_value = 0.0; hz.inputs["To Max"].default_value = 1.0
            links.new(elev, hz.inputs["Value"])
            dome_col = nodes.new("ShaderNodeMix")
            dome_col.data_type = "RGBA"
            links.new(hz.outputs["Result"], dome_col.inputs["Factor"])
            links.new(sample(back_col_img, uv), dome_col.inputs[6])
            links.new(sample(col_img, uv), dome_col.inputs[7])
        drop = math("MAXIMUM", drop, math("LESS_THAN", gate, 0.02))
    wall = None
    if peel:
        # the far side is held where the thing is held whole (compact): a thing that spans its distance,
        # the ground, the range, the sky, has no far side the mind completes; and only as the far side of
        # the thing the ray struck first: the front of a whole thing standing behind another (a crown
        # behind the open pane's bar) is a hole in the far side for now, since the ray's own colour there
        # is the thing in front's (his eleventh review of 2026-11-11). A hit within LIMB_CHORD of the
        # thing's radius beyond the front is left to the front's own splats
        p_front_room = sample(live_idx_pos, uv)
        d_front = vmath("LENGTH", vmath("SUBTRACT", p_front_room, eye_room.outputs["Vector"]))
        is_far = math("GREATER_THAN", math("SUBTRACT", d_room, d_front), math("MULTIPLY", thing_hit["radius"], LIMB_CHORD))
        gate = math("MULTIPLY", math("MULTIPLY", same_thing, compact_w), is_far)
        drop = math("MAXIMUM", drop, math("LESS_THAN", gate, 0.02))
    # (no chords on the seen picture's sheets, SHEET_CHORDS: the known shape's tiles draw its grazing faces. A picture
    # held from another moment has no such tiles and keeps its chords: without them a remembered crown's limb was a
    # comb of long thin faces, 2026-11-15)
    if (peel or peel_pos_img is not None) and (SHEET_CHORDS or not sheet or held_frame):
        # the limb's chords: at every coin (above) of a thing held whole, a splat from the front hit to the far hit
        # along the ray, as wide as the pixel's footprint, its front the way out of the thing. Between the two the
        # surface runs along the ray, a span no ray samples, and from the side the coins are edge-on, so the
        # chords close the band instead, nested from the last in-sheet ring to the rim like the shells of an
        # onion (his tenth review of 2026-11-10: a bare band between the two sides; his eleventh: a fence at
        # the rim alone left the band open at its depth, and the backdrop showed through it in streaks). Every
        # surface builds them, and the shader splits each at its middle: the seen surfaces hold the near half
        # in the seen look, the far side the far half as memory, so the seam is the locus of the middles
        if peel:
            front_room, far_room, has_far = p_front_room, p_room, same_thing
        else:
            front_room, far_room = p_room, sample(peel_pos_img, uv)
            has_far = math("COMPARE", id_of(uv, peel_idx_img), id_hit, 0.5)

        def placed(room_socket):
            tp_x = nodes.new("FunctionNodeTransformPoint")
            links.new(room_socket, tp_x.inputs["Vector"])
            links.new(info.outputs["Transform"], tp_x.inputs["Transform"])
            v_x = vmath("SUBTRACT", tp_x.outputs["Vector"], eye.outputs["Location"])
            return place(v_x, vmath("LENGTH", v_x), thing_hit)[0]

        p_front_model = p_model if not peel else placed(front_room)
        p_far_model = p_model if peel else placed(far_room)
        chord = vmath("SUBTRACT", p_far_model, p_front_model)
        chord_len = vmath("LENGTH", chord)
        mid = vmath("ADD", p_front_model, vmath("SCALE", chord, scale=0.5))
        # as wide as the front's footprint, and pushed inside by half of it, in both surfaces alike, so the two
        # halves of a chord lie in one plane
        base_w = base if not peel else math("MULTIPLY", vmath("LENGTH", vmath("SUBTRACT", p_front_model, eye.outputs["Location"])), pixel_angle * OVERLAP)
        wide = math("MULTIPLY", base_w, CHORD_WIDE / OVERLAP)
        # its front the way out of the thing in the picture (outward, above), whatever the thing's shape; a little
        # inside the thing (a chord lies inside its arc anyway); drifting with the memory it belongs to
        n_wall = outward
        mid = vmath("SUBTRACT", mid, vmath("SCALE", n_wall, scale=math("MULTIPLY", base_w, CHORD_IN)))
        if held_frame:
            mid = vmath("ADD", mid, heat(vmath("SCALE", vmath("ADD", front_room, far_room), scale=0.5))[0])
        rim_w = math("MULTIPLY", math("MULTIPLY", coin_chord, has_far), compact_w)
        if sheet:
            # (on a picture drawn as sheets, the chords of round things alone: ROUND_SHARE)
            rim_w = math("MULTIPLY", rim_w, thing_hit["round"])
        wall = {"rim": rim_w, "mid": mid, "len": chord_len, "normal": n_wall, "width": wide}
        # the chord's middle and the ray, for the shader's split of it into the seen half and the remembered half
        for nm, val in (("eq_c", mid), ("eq_n", facing)):
            st_eq = nodes.new("GeometryNodeStoreNamedAttribute")
            st_eq.data_type = "FLOAT_VECTOR"
            st_eq.domain = "POINT"
            st_eq.inputs["Name"].default_value = nm
            links.new(geom_in, st_eq.inputs["Geometry"])
            links.new(val, st_eq.inputs["Value"])
            geom_in = st_eq.outputs["Geometry"]
    sta = nodes.new("GeometryNodeStoreNamedAttribute")
    sta.data_type = "FLOAT"
    sta.domain = "POINT"
    sta.inputs["Name"].default_value = "gate"
    links.new(geom_in, sta.inputs["Geometry"])
    if isinstance(gate, float):
        sta.inputs["Value"].default_value = gate
    else:
        links.new(gate, sta.inputs["Value"])
    geom_in = sta.outputs["Geometry"]
    # a rim pixel's own colour is a mix of its thing and what stands behind the silhouette (a bush's rim ring came
    # out a third sky, whatever the pixel filter and the denoiser); its splat keeps that colour, which from the eyes
    # is the pixel's own (the eye-point check of 2026-11-11: painted in the interior colour, every silhouette came
    # out a scan pixel too wide), while its chord splat, which stands for the thing's surface along the ray, takes
    # the colour of a neighbour on its own thing (chord_col, below; his tenth review of 2026-11-10: pale streaks
    # along every rim when the rim's own mix ran along the ray)
    offsets = ((1.0 / W, 0.0, 0.0), (0.0, 1.0 / H, 0.0), (-1.0 / W, 0.0, 0.0), (0.0, -1.0 / H, 0.0))

    def rim_of(uv_k):
        """1 where any of a pixel's four neighbours lies on another thing."""
        id_k = id_of(uv_k)
        inner = None
        for off in offsets:
            same_kk = math("COMPARE", id_of(vmath("ADD", uv_k, off)), id_k, 0.5)
            inner = same_kk if inner is None else math("MINIMUM", inner, same_kk)
        return math("SUBTRACT", 1.0, inner)

    def pick_colour(flags):
        """The colour of the last neighbour whose flag is set, else the pixel's own."""
        c = sample(col_img, uv)
        for (k, uv_k), flag in zip((("down", uv_d), ("up", uv_u), ("left", uv_l), ("right", uv_r)), flags):
            pick_c = nodes.new("ShaderNodeMix")
            pick_c.data_type = "RGBA"
            links.new(flag, pick_c.inputs["Factor"])
            links.new(c, pick_c.inputs[6])
            links.new(sample(col_img, uv_k), pick_c.inputs[7])
            c = pick_c.outputs[2]
        return c

    order = (("down", uv_d), ("up", uv_u), ("left", uv_l), ("right", uv_r))
    # a neighbour on the thing that is interior itself (along a ring the next pixel is a rim pixel too, as mixed)
    interior = [math("MULTIPLY", same[k], math("SUBTRACT", 1.0, rim_of(uv_k))) for k, uv_k in order]
    has_interior = math("MAXIMUM", math("MAXIMUM", interior[0], interior[1]), math("MAXIMUM", interior[2], interior[3]))
    from_interior = pick_colour(interior)
    from_any = pick_colour([same[k] for k, _ in order])
    # failing one, the mean of the picture two pixels in over the neighbours there on the thing (along a diagonal
    # edge the rim is two pixels thick)
    acc, cnt = None, None
    for off2 in ((2.0 / W, 0.0, 0.0), (0.0, 2.0 / H, 0.0), (-2.0 / W, 0.0, 0.0), (0.0, -2.0 / H, 0.0)):
        uv2 = vmath("ADD", uv, off2)
        same2 = math("COMPARE", id_of(uv2), id_hit, 0.5)
        c2 = vmath("SCALE", sample(col_img, uv2), scale=same2)
        acc = c2 if acc is None else vmath("ADD", acc, c2)
        cnt = same2 if cnt is None else math("ADD", cnt, same2)
    mean2 = vmath("SCALE", acc, scale=math("DIVIDE", 1.0, math("MAXIMUM", cnt, 1.0)))
    fallback = nodes.new("ShaderNodeMix")
    fallback.data_type = "RGBA"
    links.new(math("GREATER_THAN", cnt, 0.5), fallback.inputs["Factor"])
    links.new(from_any, fallback.inputs[6])
    links.new(mean2, fallback.inputs[7])
    best = nodes.new("ShaderNodeMix")
    best.data_type = "RGBA"
    links.new(has_interior, best.inputs["Factor"])
    links.new(fallback.outputs[2], best.inputs[6])
    links.new(from_interior, best.inputs[7])
    rim_c = nodes.new("ShaderNodeMix")
    rim_c.data_type = "RGBA"
    links.new(rim_any, rim_c.inputs["Factor"])
    links.new(sample(col_img, uv), rim_c.inputs[6])
    links.new(best.outputs[2], rim_c.inputs[7])
    stp = nodes.new("GeometryNodeStoreNamedAttribute")
    stp.data_type = "FLOAT_COLOR"
    stp.domain = "POINT"
    stp.inputs["Name"].default_value = "chord_col"
    links.new(geom_in, stp.inputs["Geometry"])
    links.new(rim_c.outputs[2], stp.inputs["Value"])
    geom_in = stp.outputs["Geometry"]
    # a rim pixel that is no coin lies in its sheet and is drawn from every side: it takes its own thing's colour too
    # (2026-11-14: its own, a mix with what stands behind the silhouette, stood along the ridge as pale specks from the
    # camera's side). A coin, drawn for the eyes' own ray alone, keeps the pixel's colour
    own_now = nodes.new("GeometryNodeInputNamedAttribute")
    own_now.data_type = "FLOAT_COLOR"
    own_now.inputs["Name"].default_value = "scan_col"
    rim_own = nodes.new("ShaderNodeMix")
    rim_own.data_type = "RGBA"
    links.new(math("MULTIPLY", rim_any, math("SUBTRACT", 1.0, coin)), rim_own.inputs["Factor"])
    links.new(own_now.outputs["Attribute"], rim_own.inputs[6])
    links.new(best.outputs[2], rim_own.inputs[7])
    st_ro = nodes.new("GeometryNodeStoreNamedAttribute")
    st_ro.data_type = "FLOAT_COLOR"
    st_ro.domain = "POINT"
    st_ro.inputs["Name"].default_value = "scan_col"
    links.new(geom_in, st_ro.inputs["Geometry"])
    links.new(rim_own.outputs[2], st_ro.inputs["Value"])
    geom_in = st_ro.outputs["Geometry"]
    # the splat's footprint at its hit, for the material's fade near the rendering camera (NEAR_FOOT): on the
    # points, so the sheet's splats and the chords carry it alike
    stf = nodes.new("GeometryNodeStoreNamedAttribute")
    stf.data_type = "FLOAT"
    stf.domain = "POINT"
    stf.inputs["Name"].default_value = "foot"
    links.new(geom_in, stf.inputs["Geometry"])
    links.new(base, stf.inputs["Value"])
    geom_in = stf.outputs["Geometry"]
    if held_frame:
        # the wave's level at the hit, for the light a memory's waves carry (HEAT_LIGHT, the material)
        sth = nodes.new("GeometryNodeStoreNamedAttribute")
        sth.data_type = "FLOAT"
        sth.domain = "POINT"
        sth.inputs["Name"].default_value = "heat"
        links.new(geom_in, sth.inputs["Geometry"])
        links.new(heat_lvl, sth.inputs["Value"])
        geom_in = sth.outputs["Geometry"]
    if sky_fill:
        stc2 = nodes.new("GeometryNodeStoreNamedAttribute")
        stc2.data_type = "FLOAT_COLOR"
        stc2.domain = "POINT"
        stc2.inputs["Name"].default_value = "scan_col"
        links.new(geom_in, stc2.inputs["Geometry"])
        links.new(dome_col.outputs[2], stc2.inputs["Value"])
        geom_in = stc2.outputs["Geometry"]
    if sense is not None:
        # the sense's colour over the picture's on the part's tiles, SENSE_MIX of it with the tint once the sense is on
        # (the part keeps the rest of its own colour); the strength kept for the material (sense_s: the tile brighter,
        # its colour not drained)
        own_c = nodes.new("GeometryNodeInputNamedAttribute")
        own_c.data_type = "FLOAT_COLOR"
        own_c.inputs["Name"].default_value = "scan_col"
        mixs = nodes.new("ShaderNodeMix")
        mixs.data_type = "RGBA"
        links.new(sense["mix"], mixs.inputs["Factor"])
        links.new(own_c.outputs["Attribute"], mixs.inputs[6])
        links.new(sense["col"], mixs.inputs[7])
        for nm, dtype, val in (("scan_col", "FLOAT_COLOR", mixs.outputs[2]), ("sense_s", "FLOAT", sense["s"]), ("sense_clear", "FLOAT", sense["clear"])):
            st_s = nodes.new("GeometryNodeStoreNamedAttribute")
            st_s.data_type = dtype
            st_s.domain = "POINT"
            st_s.inputs["Name"].default_value = nm
            links.new(geom_in, st_s.inputs["Geometry"])
            links.new(val, st_s.inputs["Value"])
            geom_in = st_s.outputs["Geometry"]
    if held_frame:
        shut = nodes.new("ShaderNodeValue")
        shut.name = "Shut"
        shut.label = "Shut"
        shut.outputs[0].default_value = 0.0
        # the thought on the thing the hit lies on this frame, from ten keyed values (0 to 1), or the
        # eyes shut: the lighting is per hit, by its thing, with no cut
        think = None
        for i in range(MEM_REGION_COUNT):
            tv = nodes.new("ShaderNodeValue")
            tv.name = f"Think{i}"
            tv.label = tv.name
            tv.outputs[0].default_value = 0.0
            lit_i = math("MULTIPLY", tv.outputs[0], weights[i])
            think = lit_i if think is None else math("MAXIMUM", think, lit_i)
        lit = math("MAXIMUM", math("MINIMUM", think, 1.0), shut.outputs[0])
        if sense is not None:
            # a remembered tile of a part a sense lights is lit by the sense (rung 2p)
            lit = math("MAXIMUM", lit, sense["s"])
        # seen now: the hit's direction from the eyes as they are this frame falls inside their field,
        # and the live hit there lies at the same distance (verified mapping: uv = 0.5 + theta / fov
        # along the azimuth, theta from the camera's -Z)
        live_now = nodes.new("ShaderNodeValue")
        live_now.name = "LiveNow"
        live_now.label = "LiveNow"
        live_now.outputs[0].default_value = 1.0
        inv = nodes.new("FunctionNodeInvertMatrix")
        links.new(eye.outputs["Transform"], inv.inputs["Matrix"])
        td = nodes.new("FunctionNodeTransformDirection")
        links.new(v, td.inputs["Direction"])
        links.new(inv.outputs["Matrix"], td.inputs["Transform"])
        dc = vmath("NORMALIZE", td.outputs["Direction"])
        sep_c = nodes.new("ShaderNodeSeparateXYZ")
        links.new(dc, sep_c.inputs["Vector"])
        theta = math("ARCCOSINE", math("MINIMUM", math("MAXIMUM", math("MULTIPLY", sep_c.outputs["Z"], -1.0), -1.0), 1.0))
        phi = math("ARCTAN2", sep_c.outputs["Y"], sep_c.outputs["X"])
        fov_rad = fov_deg * 3.141592653589793 / 180.0
        rr = math("DIVIDE", theta, fov_rad)
        uv_now = nodes.new("ShaderNodeCombineXYZ")
        links.new(math("MULTIPLY_ADD", rr, math("COSINE", phi), 0.5), uv_now.inputs["X"])
        links.new(math("MULTIPLY_ADD", rr, math("SINE", phi), 0.5), uv_now.inputs["Y"])
        now = nodes.new("GeometryNodeInputSceneTime")
        p_live_room = sample(live_pos_img, uv_now.outputs["Vector"], frame=now.outputs["Frame"])
        d_live = vmath("LENGTH", vmath("SUBTRACT", p_live_room, eye_room.outputs["Vector"]))
        d_now = vmath("LENGTH", vmath("SUBTRACT", p_room, eye_room.outputs["Vector"]))
        # (the backdrop kept a rim of itself behind every live edge until his eighth review of 2026-11-10,
        # a dotted seam from the side; a splat covers its whole cell, so the live edge and the backdrop
        # behind it meet with no gap)
        # whether the live picture's surface passes through the hit's distance there: the hit's distance within the span
        # of the live hits on its line and on the four pixels beside it, SEEN_TOL either way. (On the line alone, within
        # SEEN_TOL, until 2026-11-15: on far ground the eyes see at a slant each row of the picture lies half as far
        # again as the one before, a remembered hit falls between two live rows and is near neither, and wedges of the
        # remembered ground stood dark before the seen ground for a second as his eyes reopened)
        d_lo, d_hi = d_live, d_live
        for off_l in ((1.0 / W, 0.0, 0.0), (-1.0 / W, 0.0, 0.0), (0.0, 1.0 / H, 0.0), (0.0, -1.0 / H, 0.0)):
            p_l = sample(live_pos_img, vmath("ADD", uv_now.outputs["Vector"], off_l), frame=now.outputs["Frame"])
            d_l = vmath("LENGTH", vmath("SUBTRACT", p_l, eye_room.outputs["Vector"]))
            d_lo, d_hi = math("MINIMUM", d_lo, d_l), math("MAXIMUM", d_hi, d_l)
        close = math("MULTIPLY", math("GREATER_THAN", d_now, math("MULTIPLY", d_lo, 1.0 - SEEN_TOL)),
                     math("LESS_THAN", d_now, math("MULTIPLY", d_hi, 1.0 + SEEN_TOL)))
        # within the eyes' field: the ellipse the live picture keeps, not the scan's whole circle
        cen_now = vmath("SUBTRACT", uv_now.outputs["Vector"], (0.5, 0.5, 0.0))
        ell_now = vmath("LENGTH", vmath("MULTIPLY", cen_now, (2.0 * fov_deg / field_h, 2.0 * fov_deg / field_v, 0.0)))
        within = math("MULTIPLY", math("LESS_THAN", theta, fov_rad * 0.49), math("LESS_THAN", ell_now, 0.995))
        seen_place = math("MULTIPLY", close, within)
        if peel:
            # a far side lies behind its own ray's first strike: no ray reaches it this frame (the test
            # above, at its tolerance, took the far side of a distant bush for its front)
            seen_place = math("ADD", 0.0, 0.0)
        # a memory at a place the eyes see gives way as the live picture comes to stand (LiveNow against SEEN_FADE): gone
        # outright once it stands whole, as ever; thinned by a smoothstep share between the marks; whole once it has gone.
        # The share rides on the gate the material multiplies its alpha by
        stand = nodes.new("ShaderNodeMapRange"); stand.interpolation_type = "SMOOTHSTEP"
        stand.inputs["From Min"].default_value = SEEN_FADE[0]; stand.inputs["From Max"].default_value = SEEN_FADE[1]
        stand.inputs["To Min"].default_value = 0.0; stand.inputs["To Max"].default_value = 1.0
        links.new(live_now.outputs[0], stand.inputs["Value"])
        if heat_off is not None:
            # a remembered hit at a place the eyes see settles onto that place as the live picture comes to stand there:
            # its ripple is taken back by the share the live picture stands (2026-11-14: with one ripple of 3.9 degrees
            # for everything, the remembered window frame stood beside the seen one as wavy lines while his eyes opened)
            settle = nodes.new("GeometryNodeSetPosition")
            links.new(geom_in, settle.inputs["Geometry"])
            settled = nodes.new("ShaderNodeMapRange")
            settled.interpolation_type = "SMOOTHSTEP"
            settled.inputs["From Min"].default_value = SEEN_FADE[0]
            settled.inputs["From Max"].default_value = SETTLE_TOP
            settled.inputs["To Min"].default_value = 0.0
            settled.inputs["To Max"].default_value = 1.0
            links.new(live_now.outputs[0], settled.inputs["Value"])
            links.new(vmath("SCALE", heat_off, scale=math("MULTIPLY", math("MULTIPLY", seen_place, settled.outputs["Result"]), -1.0)), settle.inputs["Offset"])
            geom_in = settle.outputs["Geometry"]
        # (a memory completing this very frame's picture, the backdrop and the remembered sky, is lit by a thought alone, as
        # every memory is, and goes where the eyes see its place. Lit by sight itself and kept behind the live picture for a
        # day, 2026-11-14, it turned every place the eyes do not see through the window into memory nobody had, his word of
        # that day, and stood through the seen picture as a speckle where the two lay at one depth)
        seen_gone = seen_place
        if sheet and backdrop:
            # as a sheet, a picture completing this frame's runs on SEAM_UNDER pixels under the seen picture's rim: cut
            # exactly where the eyes see its place, its sheet ended a pixel short of the seen picture's own, and the
            # black behind showed between the two as a dotted line (as splats each covered its whole cell). A hit at a
            # seen place goes only where every hit that near is at a seen place too; the ones kept sit a hair behind
            # the seen picture (SEEN_BACK, below), whole
            blur_s = nodes.new("GeometryNodeBlurAttribute")
            blur_s.data_type = "FLOAT"
            links.new(seen_place, _sock(blur_s.inputs, "Value"))
            blur_s.inputs["Iterations"].default_value = SEAM_UNDER
            st_deep = nodes.new("GeometryNodeStoreNamedAttribute")
            st_deep.data_type = "FLOAT"
            st_deep.domain = "POINT"
            st_deep.inputs["Name"].default_value = "seen_deep"
            links.new(geom_in, st_deep.inputs["Geometry"])
            links.new(math("MULTIPLY", seen_place, math("GREATER_THAN", _sock(blur_s.outputs, "Value"), 0.9999)), st_deep.inputs["Value"])
            geom_in = st_deep.outputs["Geometry"]
            deep_a = nodes.new("GeometryNodeInputNamedAttribute")
            deep_a.data_type = "FLOAT"
            deep_a.inputs["Name"].default_value = "seen_deep"
            seen_gone = deep_a.outputs["Attribute"]
        seen = math("MULTIPLY", seen_gone, math("GREATER_THAN", live_now.outputs[0], SEEN_FADE[1]))
        drop = math("MAXIMUM", drop, seen)
        drop = math("MAXIMUM", drop, math("LESS_THAN", lit, 0.02))
        st_keep = nodes.new("GeometryNodeStoreNamedAttribute")
        st_keep.data_type = "FLOAT"
        st_keep.domain = "POINT"
        st_keep.inputs["Name"].default_value = "gate"
        links.new(geom_in, st_keep.inputs["Geometry"])
        links.new(math("MULTIPLY", math("SUBTRACT", 1.0, math("MULTIPLY", seen_gone, stand.outputs["Result"])), gate),
                  st_keep.inputs["Value"])
        geom_in = st_keep.outputs["Geometry"]
        # a memory completing this very frame's picture (Shrink 1) lies on the live picture's own splats, and of two
        # surfaces at one depth the renderer draws the later one over the other whatever its opacity (2026-11-14: as his
        # eyes opened the thinned backdrop still hid the seen picture until it was deleted, and the picture came at a
        # stroke). While the live picture is coming to stand, such a tile at a seen place sits SEEN_BACK of its distance
        # farther from the eyes, behind the picture that replaces it; the tiles that fill the picture's holes keep the
        # holes' own depth
        # (and a picture from another time, which stands Shrink nearer the eyes: at a seen place it goes to the live
        # picture's own depth and SEEN_BACK beyond, by the share its ripple is taken back, so the two pictures coincide
        # while one gives way to the other. Left nearer, 2026-11-15, its dark range lay over the seen ground's bright
        # edge from the camera's side as his eyes reopened, a row of ticks for half a second)
        is_now = math("GREATER_THAN", shrink.outputs[0], 0.9999)
        stand_b = nodes.new("ShaderNodeMapRange")
        stand_b.interpolation_type = "SMOOTHSTEP"
        stand_b.inputs["From Min"].default_value = SEEN_FADE[0]
        stand_b.inputs["From Max"].default_value = SETTLE_TOP
        stand_b.inputs["To Min"].default_value = 0.0
        stand_b.inputs["To Max"].default_value = 1.0
        links.new(live_now.outputs[0], stand_b.inputs["Value"])
        share_b = math("ADD", math("MULTIPLY", is_now, math("GREATER_THAN", live_now.outputs[0], SEEN_FADE[0])),
                       math("MULTIPLY", math("SUBTRACT", 1.0, is_now), stand_b.outputs["Result"]))
        # (what completes the last picture goes back with it, whole: its tiles where the eyes' own ray stops at a nearer
        # thing, the ground behind a bush and the sky behind the range, are at no seen place and stayed forward, before
        # the live picture as a dim veil at the frame the eyes became long shut and before the last picture's bushes and
        # range until those came forward through them at a stroke, half a second later: the window in his head lost 29
        # levels of 255 in one frame and then 23, found in the last showcase's frames at 774 and 790, 2026-11-18. While
        # the eyes are long shut, is_now 0, such a picture goes back by the same share at every tile; with is_now 1
        # nothing changes)
        place_b = math("MAXIMUM", seen_place, math("SUBTRACT", 1.0, is_now)) if (backdrop or sky_fill) else seen_place
        back = math("MULTIPLY", place_b, share_b)
        far_b = math("SUBTRACT", math("DIVIDE", 1.0 + SEEN_BACK, math("MAXIMUM", shrink.outputs[0], 0.5)), 1.0)
        pos_now = nodes.new("GeometryNodeInputPosition")
        st_back = nodes.new("GeometryNodeSetPosition")
        links.new(geom_in, st_back.inputs["Geometry"])
        links.new(vmath("SCALE", vmath("SUBTRACT", pos_now.outputs["Position"], eye.outputs["Location"]), scale=math("MULTIPLY", back, far_b)),
                  st_back.inputs["Offset"])
        geom_in = st_back.outputs["Geometry"]
        stl = nodes.new("GeometryNodeStoreNamedAttribute")
        stl.data_type = "FLOAT"
        stl.domain = "POINT"
        stl.inputs["Name"].default_value = "mem_lit"
        links.new(geom_in, stl.inputs["Geometry"])
        links.new(lit, stl.inputs["Value"])
        geom_in = stl.outputs["Geometry"]
    sheet_geo = None
    if sheet:
        # the seen picture as connected sheets (his word of 2026-11-14: "why are the edges of some objects in the
        # true-person view not smooth"). A splat is its pixel's own patch of the surface, as long as the pixel's step
        # along the slope: where a surface seen nearly edge-on ends, the patches' square ends stand as a row of teeth
        # from the camera's side, and between two rows as slivers. The grid's own faces join the pixels instead: a
        # face stays where its four pixels lie on one thing and each steps to the next by less than SHEET_STEP of its
        # distance, so a surface is whole at any slant and its edge is a line through its rim pixels. That line runs
        # through the rim pixels' middles, half a pixel inside the thing's edge and stepped as the pixels are: each rim
        # vertex is set where the pixels round it say the edge lies (below), so a slanting edge comes out as a line
        # and two things that touch still meet. Nothing outward at the field's own edge
        def keep(geo, nm, value, dtype="FLOAT", domain="POINT"):
            s_k = nodes.new("GeometryNodeStoreNamedAttribute")
            s_k.data_type = dtype
            s_k.domain = domain
            s_k.inputs["Name"].default_value = nm
            links.new(geo, s_k.inputs["Geometry"])
            if isinstance(value, (int, float)):
                _sock(s_k.inputs, "Value").default_value = float(value)
            else:
                links.new(value, _sock(s_k.inputs, "Value"))
            return s_k.outputs["Geometry"]

        def held(nm, dtype="FLOAT"):
            a_k = nodes.new("GeometryNodeInputNamedAttribute")
            a_k.data_type = dtype
            a_k.inputs["Name"].default_value = nm
            return a_k.outputs["Attribute"]

        eye_d = vmath("DISTANCE", p_model, eye.outputs["Location"])
        # where the thing's edge lies beyond a pixel's middle, read off the pixels round it (SHEET_WIN each way): the share
        # of them on its own thing says how far (a straight edge through the middle leaves half of them, one half a
        # pixel on three fifths of five rows), and their balance which way is out
        side = {(1, 0): "right", (0, 1): "up", (-1, 0): "left", (0, -1): "down"}
        in_win, g_x, g_y, cover = {}, None, None, None
        for d_y in range(-SHEET_WIN, SHEET_WIN + 1):
            for d_x in range(-SHEET_WIN, SHEET_WIN + 1):
                if d_x == 0 and d_y == 0:
                    continue
                if (d_x, d_y) in side:
                    m_w = same[side[(d_x, d_y)]]
                else:
                    m_w = math("COMPARE", id_of(vmath("ADD", uv, (d_x / W, d_y / H, 0.0))), id_hit, 0.5)
                in_win[(d_x, d_y)] = m_w
                cover = m_w if cover is None else math("ADD", cover, m_w)
                if d_x:
                    g_x = math("MULTIPLY", m_w, float(d_x)) if g_x is None else math("MULTIPLY_ADD", m_w, float(d_x), g_x)
                if d_y:
                    g_y = math("MULTIPLY", m_w, float(d_y)) if g_y is None else math("MULTIPLY_ADD", m_w, float(d_y), g_y)
        rows_w = 2.0 * SHEET_WIN + 1.0
        beyond = math("MINIMUM", math("MAXIMUM", math("MULTIPLY", math("SUBTRACT", math("DIVIDE", math("ADD", cover, 1.0), rows_w * rows_w), 0.5), rows_w), 0.0), 1.5)
        g_len = math("SQRT", math("ADD", math("MULTIPLY", g_x, g_x), math("MULTIPLY", g_y, g_y)))
        # a vertex on its sheet's rim (which those are is read off the sheet itself, below) goes that far out and
        # SHEET_PAST of a pixel on, so two things that touch overlap
        reach_px = math("MULTIPLY", math("ADD", beyond, SHEET_PAST), math("GREATER_THAN", g_len, 0.5))
        out_g = math("DIVIDE", -1.0, math("MAXIMUM", g_len, 1e-6))
        foot_s = math("MULTIPLY", eye_d, pixel_angle)

        # a pixel on its thing's edge in the picture, or beside one on its own thing (the inner corner where the edge
        # crosses from one pixel column or row to the next: its vertex stands on the sheet's rim too)
        near_rim = rim_any
        for (k_n, _), in_k in zip(order, interior):
            near_rim = math("MAXIMUM", near_rim, math("SUBTRACT", same[k_n], in_k))

        def step_px(k_a, k_b, far_a, far_b, t_m):
            """The model step a pixel on along one axis of the picture: the sheet's own tangent where the sheet steps evenly
            (the step to the neighbour and the one beyond it within EDGE_RATIO of each other: a floor running to a wall),
            and where it does not (toward a round thing's outline, where the steps run along the eyes' ray and one whole
            step out stood as a spike), one footprint across the ray."""
            def pick_p(a_s, b_s):
                pk = nodes.new("ShaderNodeMix")
                pk.data_type = "VECTOR"
                links.new(same[k_a], pk.inputs["Factor"])
                links.new(b_s, pk.inputs[4])
                links.new(a_s, pk.inputs[5])
                return pk.outputs[1]

            p_1, p_2 = pick_p(p_live_k[k_a], p_live_k[k_b]), pick_p(p_live_k2[k_a], p_live_k2[k_b])
            on_2 = math("ADD", in_win[far_b], math("MULTIPLY", math("SUBTRACT", in_win[far_a], in_win[far_b]), same[k_a]))
            s_1, s_2 = vmath("DISTANCE", p_1, p_room), vmath("DISTANCE", p_2, p_1)
            even = math("MULTIPLY", on_2, math("MULTIPLY", math("LESS_THAN", s_1, math("MULTIPLY", s_2, EDGE_RATIO)),
                                               math("LESS_THAN", s_2, math("MULTIPLY", s_1, EDGE_RATIO))))
            # (never on the rim of a thing held whole: at its limb the sheet's own step runs along the eyes' ray, and
            # vertices set out along it by different amounts stood as a comb from the camera's side, 2026-11-15)
            # (nor on the pixel beside it, near_rim: stepping along the tangent while its neighbours on the rim step
            # across the ray, the inner corner stood a pixel inside the outline from the camera's side, a dent at
            # every crossing, 2026-11-15)
            even = math("MULTIPLY", even, math("SUBTRACT", 1.0, math("MULTIPLY", near_rim, whole)))
            across = vmath("SUBTRACT", t_m, vmath("SCALE", facing, scale=vmath("DOT_PRODUCT", t_m, facing)))
            pk_t = nodes.new("ShaderNodeMix")
            pk_t.data_type = "VECTOR"
            links.new(even, pk_t.inputs["Factor"])
            links.new(vmath("SCALE", vmath("NORMALIZE", across), scale=foot_s), pk_t.inputs[4])
            links.new(t_m, pk_t.inputs[5])
            return pk_t.outputs[1]

        s_right = step_px("right", "left", (2, 0), (-2, 0), t_right_m)
        s_up = step_px("up", "down", (0, 2), (0, -2), t_up_m)
        out_step = vmath("ADD", vmath("SCALE", s_right, scale=math("MULTIPLY", math("MULTIPLY", g_x, out_g), reach_px)),
                         vmath("SCALE", s_up, scale=math("MULTIPLY", math("MULTIPLY", g_y, out_g), reach_px)))
        cap_len = math("MULTIPLY", foot_s, SHEET_OUT_MAX)
        if EDGE_SEEN:
            shaped = math("LESS_THAN", thing_hit["radius"], SHAPE_REACH)
            graze_cap = math("MULTIPLY", math("LESS_THAN", cos_s, TILT_COS), shaped)
            coin_cap = math("MULTIPLY", math("MULTIPLY", rim_any, whole), shaped)
            cap_len = math("MULTIPLY", foot_s, math("MINIMUM", math("ADD", SHEET_OUT_MAX, math("MULTIPLY", graze_cap, SHEET_OUT_GRAZE - SHEET_OUT_MAX)),
                                                          math("ADD", SHEET_OUT_MAX, math("MULTIPLY", coin_cap, SHEET_OUT_COIN - SHEET_OUT_MAX))))
        # and no farther than SHEET_TOUCH of the way, along the step, to the nearest neighbouring hit on another thing (as
        # the mind places it): at a corner of two walls the other wall's hit lies in that wall's plane, so the step ends
        # on the corner; two things in one plane still overlap by a pixel; at a silhouette, where the neighbouring ray
        # strikes far behind, nothing changes. (By the plain distance to that hit, until 2026-11-15: on a wall the eyes
        # see at a slant the hit lies a hand's breadth off, and the step still stood through the other wall)
        # (only where the two things touch, SHEET_NEAR: the neighbouring hit within that many of the pixel's own steps
        # to its neighbours on its thing, a footprint at the least. At a silhouette the hit lies far along the ray
        # and a pixel off across the step: capped there, the lamp shade's edge at 55 s of the player stood in the
        # pixels' steps, 2026-11-15)
        own_step = foot_s
        for k in ("right", "up", "left", "down"):
            own_step = math("MAXIMUM", own_step, math("MULTIPLY", same[k], vmath("DISTANCE", nb[k], p_model)))
        dir_o = vmath("NORMALIZE", out_step)
        touch_d = None
        for k in ("right", "up", "left", "down"):
            a_k = vmath("DOT_PRODUCT", vmath("SUBTRACT", nb[k], p_model), dir_o)
            ok_k = math("MULTIPLY", math("MULTIPLY", math("SUBTRACT", 1.0, same[k]), math("GREATER_THAN", a_k, 0.0)),
                        math("LESS_THAN", vmath("DISTANCE", nb[k], p_model), math("MULTIPLY", own_step, SHEET_NEAR)))
            t_k = math("ADD", math("MULTIPLY", a_k, ok_k), math("MULTIPLY", math("SUBTRACT", 1.0, ok_k), 1.0e9))
            touch_d = t_k if touch_d is None else math("MINIMUM", touch_d, t_k)
        cap_len = math("MINIMUM", cap_len, math("MULTIPLY", touch_d, SHEET_TOUCH))
        out_step = vmath("SCALE", out_step, scale=math("MINIMUM", 1.0, math("DIVIDE", cap_len, math("MAXIMUM", vmath("LENGTH", out_step), 1e-9))))
        limb_px = None
        # (the hit's own distance from the eyes: for a held picture d_live is the live picture's at the hit's place now)
        d_own = vmath("LENGTH", vmath("SUBTRACT", p_room, eye_room.outputs["Vector"]))
        # (the live picture alone: a picture held from another moment keeps its round things' rims in its sheet, HELD_TILES)
        if EDGE_SEEN and not peel and not backdrop and not held_frame:
            # a round thing held whole, in the seen picture: its sheet runs to the last pixel clear of its silhouette, and
            # its known shape's tiles draw the limb from there (EDGE_SEEN_ROUND). Left out of the sheet: a rim pixel on
            # the thing's own silhouette (a neighbouring ray on another thing strikes LIMB_STEP footprints deeper; not a
            # rim against a thing in front, nor the seam between two pieces of his body), where the thing is more than a
            # rim wide; and any pixel of it whose sheet runs within TILT_COS of the ray. In the sheet, pulled to their
            # neighbours' depth, those stood as hair along a crown's lit rim from the camera's side (2026-11-15)
            rim_deep = None
            for k in ("right", "up", "left", "down"):
                far_k = math("GREATER_THAN", math("SUBTRACT", vmath("LENGTH", vmath("SUBTRACT", p_live_k[k], eye_room.outputs["Vector"])), d_own),
                             math("MULTIPLY", d_own, pixel_angle * LIMB_STEP))
                deep_k = math("MULTIPLY", math("SUBTRACT", 1.0, same[k]), far_k)
                rim_deep = deep_k if rim_deep is None else math("MAXIMUM", rim_deep, deep_k)
            # (only where a tile is no larger than the picture's own pixel at the thing: nearer the eyes a tile has its
            # floor, SPLAT_MIN of the glass radius, and a limb drawn by tiles coarser than the picture was ragged where
            # the sheet's own rim is a clean line. There the sheet keeps its rim and the tiles lie behind it)
            fine = math("GREATER_THAN", math("MULTIPLY", d_pressed, pixel_angle), radius * SPLAT_MIN)
            # (and only where the thing is more than THIN_PX and one pixels thick the way it lies in the picture: a lamp's
            # pole three pixels wide lost its two rim columns to tiles that sit half its width behind it, 2026-11-15)
            inw3 = nodes.new("ShaderNodeCombineXYZ")
            links.new(math("DIVIDE", math("MULTIPLY", g_x, (THIN_PX + 1.0) / W), math("MAXIMUM", g_len, 1e-6)), inw3.inputs["X"])
            links.new(math("DIVIDE", math("MULTIPLY", g_y, (THIN_PX + 1.0) / H), math("MAXIMUM", g_len, 1e-6)), inw3.inputs["Y"])
            thick = math("MULTIPLY", math("GREATER_THAN", g_len, 0.5), math("COMPARE", id_of(vmath("ADD", uv, inw3.outputs["Vector"])), id_hit, 0.5))
            round_whole = math("MULTIPLY", math("MULTIPLY", whole, thing_hit["round"]), math("MULTIPLY", math("MULTIPLY", shaped, fine), thick))
            # (a rim pixel only where its own sheet runs within LIMB_COS of the ray: at a sharp edge, a lamp shade's open
            # top, the surface faces the eyes right up to the silhouette and no tile draws it; a pixel inside the thing
            # only within two pixels of its edge in the picture: his own chest, which his eyes see nearly edge-on over a
            # hand's breadth, stays in its sheet)
            limb_rim = math("MULTIPLY", math("MULTIPLY", rim_any, math("LESS_THAN", cos_s, LIMB_COS)), math("MULTIPLY", has_interior, rim_deep))
            limb_in = math("MULTIPLY", math("MULTIPLY", math("SUBTRACT", 1.0, rim_any), math("LESS_THAN", cos_s, TILT_COS)), math("LESS_THAN", cover, 23.5))
            # (by a vote along the rim: the share of the round thing's rim pixels within LIMB_VOTE steps that pass the
            # test, the blur of the test over the blur of the rim's flag. A faceted shade's last face is a sliver
            # the eyes see edge-on, a tenth of a pixel wide: one rim pixel in eight fell on it and was left out
            # alone, a notch in the shade's edge every eight rows, 2026-11-15. A limb is a stretch of the rim; a
            # pixel inside the thing goes only beside such a stretch)
            limb_flag = math("MULTIPLY", rim_any, round_whole)

            def blur_v(value_s):
                b_v = nodes.new("GeometryNodeBlurAttribute")
                b_v.data_type = "FLOAT"
                links.new(value_s, _sock(b_v.inputs, "Value"))
                b_v.inputs["Iterations"].default_value = LIMB_VOTE
                return _sock(b_v.outputs, "Value")

            limb_share = math("DIVIDE", blur_v(math("MULTIPLY", limb_rim, limb_flag)), math("MAXIMUM", blur_v(limb_flag), 1e-6))
            voted = math("GREATER_THAN", limb_share, LIMB_SHARE)
            limb_rim = math("MULTIPLY", math("MULTIPLY", rim_any, voted), math("MULTIPLY", has_interior, rim_deep))
            limb_px = math("MULTIPLY", round_whole, math("MAXIMUM", limb_rim, math("MULTIPLY", limb_in, voted)))
            # (and no step outward for the pixels beside them, the sheet's new rim: the tiles lie just behind it)
            # (only where the vote has left the rim to the tiles: elsewhere the rim stays, and the pixel at an inner
            # corner of its staircase must step out with it, 2026-11-15)
            out_step = vmath("SCALE", out_step, scale=math("SUBTRACT", 1.0, math("MULTIPLY", math("MULTIPLY", round_whole, voted), math("SUBTRACT", 1.0, rim_any))))
        # the field's own edge: the picture ends there by whole pixels, a staircase that stood as saw teeth on a surface
        # the camera sees at a slant (2026-11-15, the remembered wall at 105 s of the player). A rim vertex within
        # FIELD_RIM pixels of the ellipse is set on it: the step to the ellipse along its gradient, (1 - e) e g / |g|^2
        # with g = e grad e, in pixels along the picture's two axes, by the sheet's own step a pixel on along each
        g_f = vmath("MULTIPLY", cen, ((2.0 * fov_deg / field_h) ** 2, (2.0 * fov_deg / field_v) ** 2, 0.0))
        lam_f = math("DIVIDE", math("MULTIPLY", math("SUBTRACT", 1.0, ell), ell), math("MAXIMUM", vmath("DOT_PRODUCT", g_f, g_f), 1e-12))
        d_f = nodes.new("ShaderNodeSeparateXYZ")
        links.new(vmath("SCALE", g_f, scale=lam_f), d_f.inputs["Vector"])
        px_x, px_y = math("MULTIPLY", d_f.outputs["X"], float(W)), math("MULTIPLY", d_f.outputs["Y"], float(H))
        near_f = math("LESS_THAN", math("ADD", math("MULTIPLY", px_x, px_x), math("MULTIPLY", px_y, px_y)), FIELD_RIM * FIELD_RIM)
        out_step = vmath("ADD", out_step, vmath("ADD", vmath("SCALE", s_right, scale=math("MULTIPLY", px_x, near_f)),
                                                vmath("SCALE", s_up, scale=math("MULTIPLY", px_y, near_f))))
        # the step from the pixel to its neighbour (to the right, and above) runs evenly along a line with the step
        # beyond that neighbour or with the one behind the pixel, both on the pixel's own thing: the rows of a flat
        # surface seen nearly edge-on, which the plain test (SHEET_STEP) parts into strips (2026-11-15: the window
        # sill's staircase and the comb up the window's side, from the bed). In the room's own metres
        def even_to(k_a, k_b, far_a):
            s_1 = vmath("SUBTRACT", p_live_k[k_a], p_room)
            l_1 = vmath("LENGTH", s_1)

            def with_step(s_v, on):
                l_v = vmath("LENGTH", s_v)
                ratio = math("MULTIPLY", math("LESS_THAN", l_1, math("MULTIPLY", l_v, EDGE_RATIO)), math("LESS_THAN", l_v, math("MULTIPLY", l_1, EDGE_RATIO)))
                along = math("GREATER_THAN", vmath("DOT_PRODUCT", s_1, s_v), math("MULTIPLY", math("MULTIPLY", l_1, l_v), SHEET_EVEN_COS))
                return math("MULTIPLY", on, math("MULTIPLY", ratio, along))

            beyond_ok = with_step(vmath("SUBTRACT", p_live_k2[k_a], p_live_k[k_a]), in_win[far_a])
            behind_ok = with_step(vmath("SUBTRACT", p_room, p_live_k[k_b]), same[k_b])
            return math("MULTIPLY", same[k_a], math("MAXIMUM", beyond_ok, behind_ok))

        geom_in = keep(geom_in, "even_r", even_to("right", "left", (2, 0)))
        geom_in = keep(geom_in, "even_u", even_to("up", "down", (0, 2)))
        geom_in = keep(geom_in, "sheet_id", id_hit)
        geom_in = keep(geom_in, "sheet_d", eye_d)
        # (the hit as the mind places it, before a memory's ripple: the step between two pixels is measured on these)
        geom_in = keep(geom_in, "sheet_pm", p_model, "FLOAT_VECTOR")
        geom_in = keep(geom_in, "sheet_out", out_step, "FLOAT_VECTOR")
        geom_in = keep(geom_in, "rim_px", rim_any)
        # a coin of a thing held whole (its rim, and any pixel whose sheet runs along the eyes' ray) struck the thing
        # where its surface runs along the ray, and its depth jumps from one such pixel to the next: joined into the
        # sheet as it stood, a row of them was hair on every bush. It is held no deeper than its nearest neighbour on
        # the thing and SHEET_COIN footprints (left out of the sheet instead, each left a hole in a crown, and the
        # grazing rim of every wide surface went back to splats)
        d_in = None
        for k in ("right", "up", "left", "down"):
            d_k = math("ADD", vmath("DISTANCE", nb[k], eye.outputs["Location"]), math("MULTIPLY", math("SUBTRACT", 1.0, same[k]), 1.0e9))
            d_in = d_k if d_in is None else math("MINIMUM", d_in, d_k)
        held_d = math("MINIMUM", eye_d, math("ADD", d_in, math("MULTIPLY", foot_s, SHEET_COIN)))
        pull = vmath("SCALE", facing, scale=math("MULTIPLY", math("SUBTRACT", held_d, eye_d), math("MULTIPLY", coin, whole)))
        geom_in = keep(geom_in, "sheet_pull", pull, "FLOAT_VECTOR")
        if limb_px is not None:
            drop = math("MAXIMUM", drop, limb_px)
    dele = nodes.new("GeometryNodeDeleteGeometry")
    dele.domain = "POINT"
    dele.mode = "ALL"
    links.new(geom_in, dele.inputs["Geometry"])
    links.new(drop, dele.inputs["Selection"])
    base_geo = dele.outputs["Geometry"]
    if sheet:
        # the same test on the grid's edges, by the facts at each edge's two ends: an edge that is not joined goes, and
        # the faces on it; its pixels stay
        ev = nodes.new("GeometryNodeInputMeshEdgeVertices")

        def at_end(k, nm):
            f_k = nodes.new("GeometryNodeFieldAtIndex")
            f_k.domain = "POINT"
            f_k.data_type = "FLOAT"
            links.new(ev.outputs[f"Vertex Index {k}"], f_k.inputs["Index"])
            links.new(held(nm), _sock(f_k.inputs, "Value"))
            return _sock(f_k.outputs, "Value")

        # or the edge's own step runs evenly (even_r, even_u above, held at the end that comes first in the picture
        # along the edge's own axis: an edge of the grid runs along a row or up a column, told by its ends' picture
        # coordinates)
        def at_end_v(k, nm):
            f_k = nodes.new("GeometryNodeFieldAtIndex")
            f_k.domain = "POINT"
            f_k.data_type = "FLOAT_VECTOR"
            links.new(ev.outputs[f"Vertex Index {k}"], f_k.inputs["Index"])
            links.new(held(nm, "FLOAT_VECTOR"), _sock(f_k.inputs, "Value"))
            return _sock(f_k.outputs, "Value")

        # the step between the edge's two pixels, between the hits as placed (sheet_pm) and not as drawn: a remembered
        # picture is drawn rippled, and measured there the sheet parted wherever the ripple stretched it (2026-11-15,
        # dark tears in the remembered wall beside his head)
        step_e = vmath("DISTANCE", at_end_v(1, "sheet_pm"), at_end_v(2, "sheet_pm"))
        uv_1, uv_2 = nodes.new("ShaderNodeSeparateXYZ"), nodes.new("ShaderNodeSeparateXYZ")
        links.new(at_end_v(1, "scan_uv"), uv_1.inputs["Vector"])
        links.new(at_end_v(2, "scan_uv"), uv_2.inputs["Vector"])
        level = math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", uv_1.outputs["Y"], uv_2.outputs["Y"])), 0.5 / H)
        first = math("ADD", math("MULTIPLY", level, math("LESS_THAN", uv_1.outputs["X"], uv_2.outputs["X"])),
                     math("MULTIPLY", math("SUBTRACT", 1.0, level), math("LESS_THAN", uv_1.outputs["Y"], uv_2.outputs["Y"])))

        def pick_f(a_s, b_s, fac):
            return math("ADD", b_s, math("MULTIPLY", math("SUBTRACT", a_s, b_s), fac))

        even_e = pick_f(pick_f(at_end(1, "even_r"), at_end(2, "even_r"), first), pick_f(at_end(1, "even_u"), at_end(2, "even_u"), first), level)
        join_e = math("MULTIPLY", math("COMPARE", at_end(1, "sheet_id"), at_end(2, "sheet_id"), 0.5),
                      math("MAXIMUM", math("GREATER_THAN", even_e, 0.5),
                           math("LESS_THAN", step_e, math("MULTIPLY", math("MINIMUM", at_end(1, "sheet_d"), at_end(2, "sheet_d")), SHEET_STEP))))
        cut_f = nodes.new("GeometryNodeDeleteGeometry")
        cut_f.domain = "EDGE"
        cut_f.mode = "EDGE_FACE"
        links.new(base_geo, cut_f.inputs["Geometry"])
        links.new(math("LESS_THAN", join_e, 0.5), cut_f.inputs["Selection"])
        # a pixel with a face left is drawn by its sheet; one with none (a thing a pixel thin) by its splat, as
        # ever. A vertex with fewer than its four faces stands on its sheet's rim
        v_nb = nodes.new("GeometryNodeInputMeshVertexNeighbors")
        base_geo = keep(cut_f.outputs["Geometry"], "in_sheet", math("GREATER_THAN", v_nb.outputs["Face Count"], 0.5))
        base_geo = keep(base_geo, "sheet_rim", math("LESS_THAN", v_nb.outputs["Face Count"], 3.5))
        only_s = nodes.new("GeometryNodeDeleteGeometry")
        only_s.domain = "POINT"
        only_s.mode = "ALL"
        links.new(base_geo, only_s.inputs["Geometry"])
        links.new(math("LESS_THAN", held("in_sheet"), 0.5), only_s.inputs["Selection"])
        # every rim pixel of a sheet in its own thing's colour (chord_col: the pixel's own is a mix with what stands
        # behind the silhouette), and no coin: the sheet covers the pixel from the eyes and from the side alike
        rim_col = nodes.new("ShaderNodeMix")
        rim_col.data_type = "RGBA"
        links.new(held("rim_px"), rim_col.inputs["Factor"])
        links.new(held("scan_col", "FLOAT_COLOR"), rim_col.inputs[6])
        links.new(held("chord_col", "FLOAT_COLOR"), rim_col.inputs[7])
        col_sheet = rim_col.outputs[2]
        if SHEET_INSET and not sky_fill:
            # within two pixels of its thing's edge in the picture (another thing in the five-by-five round it), on a
            # thing that spans its distance: the picture's colour SHEET_INSET pixels in, the way its own thing lies
            # (g, the balance of the pixels round it on its thing), where that pixel is on the thing too. The render
            # mixes a pixel beside an edge with what stands next to it, a pixel further by its denoiser, and on a
            # surface the eyes see at a slant one pixel is a long strip: a comb along the ground beside the room's
            # wall, wedges along its far edge under the range, pale ticks on the ridge under the sun (2026-11-15)
            inw = nodes.new("ShaderNodeCombineXYZ")
            links.new(math("DIVIDE", math("MULTIPLY", g_x, SHEET_INSET / W), math("MAXIMUM", g_len, 1e-6)), inw.inputs["X"])
            links.new(math("DIVIDE", math("MULTIPLY", g_y, SHEET_INSET / H), math("MAXIMUM", g_len, 1e-6)), inw.inputs["Y"])
            uv_in = vmath("ADD", uv, inw.outputs["Vector"])
            near_edge = math("MULTIPLY", math("LESS_THAN", cover, 23.5), math("GREATER_THAN", g_len, 0.5))
            # (and only where the pixel SHEET_CLEAR farther in is on the thing too: on a strip of wall five pixels wide
            # between two things the pixel three in is the one beside the other edge, and its mix was painted along
            # the strip, 2026-11-15, a pale smudge on the wall beside the lamp shade at 55 s of the player)
            uv_in2 = vmath("ADD", uv, vmath("SCALE", inw.outputs["Vector"], scale=(SHEET_INSET + SHEET_CLEAR) / SHEET_INSET))
            # (and not where the two things touch, as two walls at a corner: there the picture runs on from one to the
            # other, and a colour from three pixels on stood as a band beside the corner, 2026-11-15, a pale line on
            # the wall by the lamp's pole at 55 s of the player. Touching: a rim pixel whose neighbouring hit on the
            # other thing lies within SHEET_NEAR of the larger of the two things' own steps there, in the room's
            # metres; and the pixels of its sheet within two steps of such a one. Read two pixels out along the
            # way the thing lies instead, the test missed at every step of the corner's line and left a row of dots)
            own_r = math("MULTIPLY", vmath("DISTANCE", p_room, eye_room.outputs["Vector"]), pixel_angle)
            for k in ("right", "up", "left", "down"):
                own_r = math("MAXIMUM", own_r, math("MULTIPLY", same[k], vmath("DISTANCE", p_live_k[k], p_room)))
            touch_rim = None
            for k in ("right", "up", "left", "down"):
                near_k = math("MULTIPLY", math("SUBTRACT", 1.0, same[k]),
                              math("LESS_THAN", vmath("DISTANCE", p_live_k[k], p_room),
                                   math("MULTIPLY", math("MAXIMUM", own_r, vmath("DISTANCE", p_live_k2[k], p_live_k[k])), SHEET_NEAR)))
                touch_rim = near_k if touch_rim is None else math("MAXIMUM", touch_rim, near_k)
            blur_t = nodes.new("GeometryNodeBlurAttribute")
            blur_t.data_type = "FLOAT"
            links.new(touch_rim, _sock(blur_t.inputs, "Value"))
            blur_t.inputs["Iterations"].default_value = 2
            touching = math("GREATER_THAN", _sock(blur_t.outputs, "Value"), 1e-6)
            inset_w = math("MULTIPLY", math("MULTIPLY", math("MULTIPLY", near_edge, math("SUBTRACT", 1.0, whole)), math("SUBTRACT", 1.0, touching)),
                           math("MULTIPLY", math("COMPARE", id_of(uv_in), id_hit, 0.5), math("COMPARE", id_of(uv_in2), id_hit, 0.5)))
            inset = nodes.new("ShaderNodeMix")
            inset.data_type = "RGBA"
            links.new(inset_w, inset.inputs["Factor"])
            links.new(col_sheet, inset.inputs[6])
            links.new(sample(col_img, uv_in), inset.inputs[7])
            col_sheet = inset.outputs[2]
        sheet_geo = keep(only_s.outputs["Geometry"], "scan_col", col_sheet, "FLOAT_COLOR")
        sheet_geo = keep(sheet_geo, "coin", 0.0)
        set_out = nodes.new("GeometryNodeSetPosition")
        links.new(sheet_geo, set_out.inputs["Geometry"])
        links.new(vmath("ADD", vmath("SCALE", held("sheet_out", "FLOAT_VECTOR"), scale=held("sheet_rim")), held("sheet_pull", "FLOAT_VECTOR")),
                  set_out.inputs["Offset"])
        # its faces' fronts toward the eyes, as a splat's is
        nrm_f = nodes.new("GeometryNodeInputNormal")
        pos_f = nodes.new("GeometryNodeInputPosition")
        flip_f = nodes.new("GeometryNodeFlipFaces")
        placed = set_out.outputs["Geometry"]
        if SHEET_SMOOTH:
            # the rim smoothed along itself (SHEET_SMOOTH passes): a rim vertex to the mean of itself and its neighbours ON
            # THE RIM. The blur node's weight is the vertex's own share, not its neighbours' (a plain blur drew every rim
            # vertex toward the ones inside the sheet, and each straight edge came out scalloped): the mean over the rim
            # alone is the blur of the position times the rim's flag over the blur of the flag. Only where the vertex has
            # a neighbour inside the sheet: on a strip one face wide both sides are rim and are each other's neighbours,
            # and the mean would draw it thin
            def blur_once(value_s, dtype):
                b_n = nodes.new("GeometryNodeBlurAttribute")
                b_n.data_type = dtype
                links.new(value_s, _sock(b_n.inputs, "Value"))
                b_n.inputs["Iterations"].default_value = 1
                return _sock(b_n.outputs, "Value")

            # (for a day, 2026-11-15, as one weighted blur in which an inner corner of the rim's staircase handed its
            # neighbours' positions on and was set between them: that also bridged the shoulders of a small bite in
            # an outline, drew its bottom out and folded the sheet, tan specks from behind the wall at 119 s of the
            # player. The dents it was for are cured where the inner corner takes its step: near_rim, above)
            smooth_w = math("MULTIPLY", held("sheet_rim"), math("GREATER_THAN", blur_once(math("SUBTRACT", 1.0, held("sheet_rim")), "FLOAT"), 1e-6))
            share_w = math("MAXIMUM", blur_once(smooth_w, "FLOAT"), 1e-6)
            pos_b = nodes.new("GeometryNodeInputPosition")
            smooth_p = pos_b.outputs["Position"]
            for _ in range(SHEET_SMOOTH):
                smooth_p = vmath("SCALE", blur_once(vmath("SCALE", smooth_p, scale=smooth_w), "FLOAT_VECTOR"), scale=math("DIVIDE", 1.0, share_w))
            set_sm = nodes.new("GeometryNodeSetPosition")
            links.new(placed, set_sm.inputs["Geometry"])
            links.new(math("GREATER_THAN", smooth_w, 0.5), set_sm.inputs["Selection"])
            links.new(smooth_p, set_sm.inputs["Position"])
            placed = set_sm.outputs["Geometry"]
        links.new(placed, flip_f.inputs["Mesh"])
        links.new(math("GREATER_THAN", vmath("DOT_PRODUCT", nrm_f.outputs["Normal"], vmath("SUBTRACT", pos_f.outputs["Position"], eye.outputs["Location"])), 0.0),
                  flip_f.inputs["Selection"])
        sheet_geo = flip_f.outputs["Mesh"]
    pts = nodes.new("GeometryNodeMeshToPoints")
    pts.mode = "VERTICES"
    links.new(base_geo, pts.inputs["Mesh"])
    # the splat: a unit square turned to the normal, its front toward the eyes, scaled to the size
    quad = nodes.new("GeometryNodeMeshGrid")
    quad.inputs["Size X"].default_value = 1.0
    quad.inputs["Size Y"].default_value = 1.0
    quad.inputs["Vertices X"].default_value = 2
    quad.inputs["Vertices Y"].default_value = 2
    def flag_chord(mesh_socket, value):
        st_ch = nodes.new("GeometryNodeStoreNamedAttribute")
        st_ch.data_type = "FLOAT"
        st_ch.domain = "FACE"
        st_ch.inputs["Name"].default_value = "chord"
        st_ch.inputs["Value"].default_value = value
        links.new(mesh_socket, st_ch.inputs["Geometry"])
        return st_ch.outputs["Geometry"]

    setm = nodes.new("GeometryNodeSetMaterial")
    setm.inputs["Material"].default_value = material
    links.new(flag_chord(quad.outputs["Mesh"], 0.0), setm.inputs["Geometry"])
    rot = nodes.new("FunctionNodeAlignRotationToVector")
    rot.axis = "Z"
    # its front against the inward normal (toward the eyes, or the way out of a thing at its limb), turned toward
    # the rendering camera where that would see it edge-on
    links.new(toward_camera(vmath("SCALE", n_model, scale=-1.0), p_draw), rot.inputs["Vector"])
    # and its long side along the sheet's slope
    rot2 = nodes.new("FunctionNodeAlignRotationToVector")
    rot2.axis = "X"
    rot2.pivot_axis = "Z"
    links.new(rot.outputs["Rotation"], rot2.inputs["Rotation"])
    links.new(slope, rot2.inputs["Vector"])
    iop = nodes.new("GeometryNodeInstanceOnPoints")
    links.new(pts.outputs["Points"], iop.inputs["Points"])
    links.new(setm.outputs["Geometry"], iop.inputs["Instance"])
    links.new(rot2.outputs["Rotation"], iop.inputs["Rotation"])
    links.new(size_.outputs["Vector"], iop.inputs["Scale"])
    if sheet:
        links.new(math("LESS_THAN", held("in_sheet"), 0.5), iop.inputs["Selection"])
    instances = iop.outputs["Instances"]
    if wall is not None:
        # the rim's chord splats (above): one per rim pixel, from the front hit to the far hit along the ray
        wq = nodes.new("GeometryNodeMeshGrid")
        wq.inputs["Size X"].default_value = 1.0
        wq.inputs["Size Y"].default_value = 1.0
        wq.inputs["Vertices X"].default_value = 2
        wq.inputs["Vertices Y"].default_value = 2
        setw = nodes.new("GeometryNodeSetMaterial")
        setw.inputs["Material"].default_value = material
        links.new(flag_chord(wq.outputs["Mesh"], 1.0), setw.inputs["Geometry"])
        rw = nodes.new("FunctionNodeAlignRotationToVector")
        rw.axis = "Z"
        links.new(toward_camera(wall["normal"], wall["mid"]), rw.inputs["Vector"])
        rw2 = nodes.new("FunctionNodeAlignRotationToVector")
        rw2.axis = "X"
        rw2.pivot_axis = "Z"
        links.new(rw.outputs["Rotation"], rw2.inputs["Rotation"])
        links.new(facing, rw2.inputs["Vector"])
        wsize = nodes.new("ShaderNodeCombineXYZ")
        links.new(wall["len"], wsize.inputs["X"])
        links.new(wall["width"], wsize.inputs["Y"])
        wsize.inputs["Z"].default_value = 1.0
        # the chord in the thing's own colour (chord_col, above), where the rim pixel's own is a mix with what
        # stands behind the silhouette
        ccol = nodes.new("GeometryNodeInputNamedAttribute")
        ccol.data_type = "FLOAT_COLOR"
        ccol.inputs["Name"].default_value = "chord_col"
        stw2 = nodes.new("GeometryNodeStoreNamedAttribute")
        stw2.data_type = "FLOAT_COLOR"
        stw2.domain = "POINT"
        stw2.inputs["Name"].default_value = "scan_col"
        links.new(pts.outputs["Points"], stw2.inputs["Geometry"])
        links.new(ccol.outputs["Attribute"], stw2.inputs["Value"])
        iow = nodes.new("GeometryNodeInstanceOnPoints")
        links.new(stw2.outputs["Geometry"], iow.inputs["Points"])
        links.new(math("GREATER_THAN", wall["rim"], 0.5), iow.inputs["Selection"])
        links.new(setw.outputs["Geometry"], iow.inputs["Instance"])
        links.new(rw2.outputs["Rotation"], iow.inputs["Rotation"])
        links.new(wsize.outputs["Vector"], iow.inputs["Scale"])
        # placed at the chord's middle: the points stand at the hits
        tr = nodes.new("GeometryNodeTranslateInstances")
        tr.inputs["Local Space"].default_value = False
        links.new(iow.outputs["Instances"], tr.inputs["Instances"])
        links.new(vmath("SUBTRACT", wall["mid"], p_draw), tr.inputs["Translation"])
        # (the shader splits the chord at its middle: chord 1; every other splat is whole)
        join = nodes.new("GeometryNodeJoinGeometry")
        links.new(tr.outputs["Instances"], join.inputs["Geometry"])
        links.new(instances, join.inputs["Geometry"])
        instances = join.outputs["Geometry"]
    real = nodes.new("GeometryNodeRealizeInstances")
    links.new(instances, real.inputs["Geometry"])
    drawn = real.outputs["Geometry"]
    if sheet_geo is not None:
        set_s = nodes.new("GeometryNodeSetMaterial")
        set_s.inputs["Material"].default_value = material
        links.new(flag_chord(sheet_geo, 0.0), set_s.inputs["Geometry"])
        both = nodes.new("GeometryNodeJoinGeometry")
        links.new(set_s.outputs["Geometry"], both.inputs["Geometry"])
        links.new(drawn, both.inputs["Geometry"])
        drawn = both.outputs["Geometry"]
    # a surface that is not visible is not worked out at all (2026-11-15: until then every attribute was worked out
    # for its whole grid and every point then deleted, above)
    shown = nodes.new("GeometryNodeSwitch")
    shown.input_type = "GEOMETRY"
    links.new(math("GREATER_THAN", visible.outputs[0], 0.01), _sock(shown.inputs, "Switch"))
    links.new(drawn, _sock(shown.inputs, "True"))
    links.new(_sock(shown.outputs, "Output"), go.inputs["Geometry"])
    return ng


def _sock(sockets, name):
    """The enabled socket of that name (a node that works on several types has one of each, one of them enabled)."""
    return next(s for s in sockets if s.name == name and s.enabled)


def _seam_map(nodes, links, math, vmath, idx_img, pos_img, frame_socket, eye_room, fov_deg):
    """The seams of the eyes' picture this frame, as a grid of SEAM_N by SEAM_N points over the scan's square (rung 2p,
    his fourteenth round of 2026-11-14): 1 on a cell where the picture has an edge, spread over SEAM_BLUR passes of the
    grid and scaled by SEAM_GAIN into a band that is whole within about two degrees of an edge and gone by about five. An
    edge: two things meeting within the cell (nine readings of the scan's index picture across it), a step of depth or
    a grazing surface (the hit a cell on standing more than SEAM_JUMP of its distance nearer or farther), or the field's
    own edge. Returns the grid, the band stored on its points by name."""
    grid = nodes.new("GeometryNodeMeshGrid")
    grid.inputs["Size X"].default_value = 1.0
    grid.inputs["Size Y"].default_value = 1.0
    grid.inputs["Vertices X"].default_value = SEAM_N
    grid.inputs["Vertices Y"].default_value = SEAM_N
    pin = nodes.new("GeometryNodeInputPosition")
    uv = vmath("ADD", pin.outputs["Position"], (0.5, 0.5, 0.0))

    def tap(img, off):
        tex = nodes.new("GeometryNodeImageTexture")
        tex.interpolation = "Closest"
        tex.extension = "EXTEND"
        tex.inputs["Image"].default_value = img
        links.new(uv if off is None else vmath("ADD", uv, off), tex.inputs["Vector"])
        links.new(frame_socket, tex.inputs["Frame"])
        return tex.outputs["Color"]

    def id_at(off):
        sep = nodes.new("ShaderNodeSeparateXYZ")
        links.new(tap(idx_img, off), sep.inputs["Vector"])
        return math("ROUND", sep.outputs["X"])

    c = 1.0 / SEAM_N
    id0 = id_at(None)
    same = None
    for du in (-0.4, 0.0, 0.4):
        for dv in (-0.4, 0.0, 0.4):
            if du == 0.0 and dv == 0.0:
                continue
            s = math("COMPARE", id_at((du * c, dv * c, 0.0)), id0, 0.5)
            same = s if same is None else math("MINIMUM", same, s)
    edge = math("SUBTRACT", 1.0, same)
    d0 = vmath("LENGTH", vmath("SUBTRACT", tap(pos_img, None), eye_room))
    for off in ((c, 0.0, 0.0), (0.0, c, 0.0)):
        dk = vmath("LENGTH", vmath("SUBTRACT", tap(pos_img, off), eye_room))
        edge = math("MAXIMUM", edge, math("GREATER_THAN", math("ABSOLUTE", math("SUBTRACT", dk, d0)), math("MULTIPLY", d0, SEAM_JUMP)))
    cen = vmath("SUBTRACT", uv, (0.5, 0.5, 0.0))
    ell = vmath("LENGTH", vmath("MULTIPLY", cen, (2.0 * fov_deg / FIELD_H, 2.0 * fov_deg / FIELD_V, 0.0)))
    # two bands: "band_in", the seams inside the picture alone (what a nearer thing or a grazing surface hides), and
    # "band", those with the field's own edge (where the picture ends and a memory beyond it must hold still)
    edge_in = math("MULTIPLY", edge, math("LESS_THAN", ell, 0.97))
    # (the field's own edge is a ring at the ellipse, SEAM_RING wide, and an edge counts inside the field alone. Until
    # 2026-11-15 every cell outside the ellipse counted as an edge, and every remembered tile outside his field held
    # still while his eyes were open: the whole unseen room, frozen)
    edge = math("MAXIMUM", edge_in, math("MULTIPLY", math("GREATER_THAN", ell, 0.97), math("LESS_THAN", ell, 1.0 + SEAM_RING)))
    geo_out = grid.outputs["Mesh"]
    # (and "band_wide": every seam with the field's edge, spread wide, for how far a remembered tile is held: SEAM_WIDE)
    for nm, e, n_b, g_b in (("band", edge, SEAM_BLUR, SEAM_GAIN), ("band_in", edge_in, SEAM_BLUR, SEAM_GAIN), ("band_wide", edge, SEAM_WIDE[0], SEAM_WIDE[1])):
        blur = nodes.new("GeometryNodeBlurAttribute")
        blur.data_type = "FLOAT"
        links.new(e, _sock(blur.inputs, "Value"))
        blur.inputs["Iterations"].default_value = n_b
        blur.inputs["Weight"].default_value = 1.0
        st = nodes.new("GeometryNodeStoreNamedAttribute")
        st.data_type = "FLOAT"
        st.domain = "POINT"
        st.inputs["Name"].default_value = nm
        links.new(geo_out, st.inputs["Geometry"])
        links.new(math("MINIMUM", math("MULTIPLY", _sock(blur.outputs, "Value"), g_b), 1.0), st.inputs["Value"])
        geo_out = st.outputs["Geometry"]
    return geo_out


def _seam_at(nodes, links, vmath, seam, uv_socket, name="band"):
    """The seam map's band at a place of the eyes' picture (uv, 0 to 1 across and up): its nearest point's. name: "band"
    (every seam and the field's own edge) or "band_in" (the seams inside the picture alone)."""
    # (the nearest place on the map's surface, the band interpolated across its face: read at the nearest point the
    # kept and the dropped tiles met along the map's cells, in steps)
    band = nodes.new("GeometryNodeInputNamedAttribute")
    band.data_type = "FLOAT"
    band.inputs["Name"].default_value = name
    sn = nodes.new("GeometryNodeSampleNearestSurface")
    sn.data_type = "FLOAT"
    links.new(seam, sn.inputs["Mesh"])
    links.new(band.outputs["Attribute"], _sock(sn.inputs, "Value"))
    links.new(vmath("SUBTRACT", uv_socket, (0.5, 0.5, 0.0)), sn.inputs["Sample Position"])
    return _sock(sn.outputs, "Value")


def shape_nodes(name, things, frame_obj, eye_obj, table_obj, material, radius, pixel_angle, room_size,
                sense_img=None, n_frames=1, torso_obj=None, outline=False, contact_obj=None, levels=None,
                live_pos_img=None, fov_deg=FOV_DEG, live_idx_img=None, live_col_img=None, seen_material=None, scan_size=None,
                held=False, test_eye_obj=None):
    """A thought-of thing drawn whole by its known shape, a memory (his eleventh review of 2026-11-11: the chime's
    bed and table should simply be there, as the boxes they are). Every mesh thing of the room is joined into one
    surface, each vertex marked with its thing; carried into the model's frame and placed as the thing's hits are
    (scaled whole about the eyes by its centre's believed distance over its true one, pressed onto the glass
    beyond the knee); shrunk a little about its centre so the live picture and the far side draw over it wherever
    the rays reach it; drawn as tiles at the footprint, each drifting as every remembered tile does; coloured by the
    thing's known colour; lit by the thought on it (Think0 to Think9, keyed).

    The senses (rung 2p): a part's shape is lit by the sense on it as well (the sense table, sense_img: the sense
    light's colour replacing the known colour by its strength and tint), and a breathing part is scaled about its
    centre (the chest about the torso's, the heart and the lungs about their own). things: (object, index, colours,
    part). outline: the same shapes kept as surfaces, OUTLINE_HALO outside the parts instead of inside, lit along
    their outlines by the outline sense on each part (the table's third field) in its colour, the glow of a moving, a
    warm or a cold part, and over the touched patch by touch: a sense's own light and no memory (outline_material).

    Touch (contact_obj, ContactBody): a body part's shape is cut as finely as ContactBody's (levels: the cuts per
    object) and every vertex takes its contact from it, so the touched patch alone is lit by touch and drawn.

    The skin (2026-11-12, sixth round): a sense is drawn on the outside of the body alone. A body piece's tile, and
    the outline's light, are left out where the piece lies inside another piece of the body (inner, from ContactBody).

    Seen now (live_pos_img, the scan's position pictures; 2026-11-12, fifth round): a tile whose place the eyes see
    this frame is not drawn, as every other memory is gone the moment a ray reaches it. Its place is seen where its
    direction from the eyes lies in their field and the scan's hit there stands at its own distance (SEEN_TOL), on
    the side of its thing that faces the eyes (a closed thing's far side is never seen; an open sheet, a wall, has
    one side); while the live picture stands (LiveNow, keyed). things then carry a fifth entry, whether the thing's
    mesh is closed.

    held (the audit of 2026-11-15, his word of 2026-11-16): the same shapes for the picture the eyes last held. Nothing is
    lit as a memory; the faces seen nearly edge-on in THAT picture are found as they are in the live one (its pictures read
    at the frame on MemFrame, keyed, from the eyes as they were at that frame: test_eye_obj, keyed to them) and drawn in
    the last picture's own look (seen_material: its material), lit by the eyes being shut (Shut), a little nearer the eyes
    as that picture's hits are (MEM_SHRINK) and rippling with them."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links

    def math(op, a=None, b=None, c=None):
        n = nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                links.new(v, n.inputs[i])
        return n.outputs["Value"]

    def vmath(op, a=None, b=None, scale=None):
        n = nodes.new("ShaderNodeVectorMath")
        n.operation = op
        for i, v in enumerate((a, b)):
            if v is None:
                continue
            if isinstance(v, (tuple, list, Vector)):
                n.inputs[i].default_value = tuple(v)
            else:
                links.new(v, n.inputs[i])
        if scale is not None:
            if isinstance(scale, (int, float)):
                n.inputs["Scale"].default_value = float(scale)
            else:
                links.new(scale, n.inputs["Scale"])
        return n.outputs["Vector"] if op not in ("LENGTH", "DOT_PRODUCT", "DISTANCE") else n.outputs["Value"]

    def value(nm, v):
        n = nodes.new("ShaderNodeValue")
        n.name = nm
        n.label = nm
        n.outputs[0].default_value = v
        return n.outputs[0]

    def store(geom, nm, dtype, val, domain="POINT"):
        st = nodes.new("GeometryNodeStoreNamedAttribute")
        st.data_type = dtype
        st.domain = domain
        st.inputs["Name"].default_value = nm
        links.new(geom, st.inputs["Geometry"])
        if isinstance(val, (int, float)):
            st.inputs["Value"].default_value = float(val)
        elif isinstance(val, (tuple, list)):
            st.inputs["Value"].default_value = tuple(val)
        else:
            links.new(val, st.inputs["Value"])
        return st.outputs["Geometry"]

    def named(nm, dtype):
        n = nodes.new("GeometryNodeInputNamedAttribute")
        n.data_type = dtype
        n.inputs["Name"].default_value = nm
        return n.outputs["Attribute"]

    go = nodes.new("NodeGroupOutput")
    visible = value("Visible", 1.0)
    resolve = value("Resolve", 1.0)
    senses_on = value("Senses", 1.0)
    torso = None
    if torso_obj is not None:
        torso = nodes.new("GeometryNodeObjectInfo")
        torso.transform_space = "ORIGINAL"
        torso.inputs["Object"].default_value = torso_obj
    organ_parts = {tags.PART_INDEX[p] for p in tags.ORGAN_PARTS}
    chest_part = tags.PART_INDEX["chest"]
    # every thing's shape in room metres, each vertex marked with its thing, each face with its known colour (its
    # material slot's base colour); and the centre a breathing part scales about (pc): the torso's for the chest, its
    # own for an organ, nought (with a scale of 1) for the rest
    join = nodes.new("GeometryNodeJoinGeometry")
    for ob, idx, cols, part, *more in things:
        info = nodes.new("GeometryNodeObjectInfo")
        info.transform_space = "RELATIVE"
        info.inputs["Object"].default_value = ob
        g = store(info.outputs["Geometry"], "open", "FLOAT", 0.0 if (more and more[0]) else 1.0)
        # the shape's own vertex normals before it is cut (SHAPE_EDGE), carried through the cut: the set-in and the light
        # use these, so a cut shape is set in and lit exactly as the uncut one (a vertex the cut makes inside a flat
        # face has that face's normal, one on its border the mean of the faces meeting there: set in by those, the
        # border's small faces were warped by up to thirty degrees, 2026-11-15)
        g = store(g, "nrm_smooth", "FLOAT_VECTOR", nodes.new("GeometryNodeInputNormal").outputs["Normal"])
        # (levels: a body part cut as finely as ContactBody's, every other shape by SHAPE_EDGE)
        cuts = int((levels or {}).get(ob.name, 0))
        if cuts > 0:
            sub = nodes.new("GeometryNodeSubdivideMesh")
            sub.inputs["Level"].default_value = cuts
            links.new(g, sub.inputs["Mesh"])
            g = sub.outputs["Mesh"]
        g = store(g, "thing", "FLOAT", float(idx))
        g = store(g, "own_body", "FLOAT", 1.0 if part >= 0 else 0.0)     # a piece of his own body: its ripple (_heat)
        if part == chest_part and torso is not None:
            pc = torso.outputs["Location"]
        elif part in organ_parts:
            pc = info.outputs["Location"]
        else:
            pc = (0.0, 0.0, 0.0)
        g = store(g, "pc", "FLOAT_VECTOR", pc)
        slot = nodes.new("GeometryNodeInputNamedAttribute")
        slot.data_type = "INT"
        slot.inputs["Name"].default_value = "material_index"
        col = nodes.new("FunctionNodeInputColor")
        col.value = (*cols[0], 1.0)
        col_out = col.outputs["Color"]
        for k, c in enumerate(cols[1:], 1):
            is_k = math("COMPARE", slot.outputs["Attribute"], float(k), 0.5)
            mixk = nodes.new("ShaderNodeMix")
            mixk.data_type = "RGBA"
            links.new(is_k, mixk.inputs["Factor"])
            links.new(col_out, mixk.inputs[6])
            mixk.inputs[7].default_value = (*c, 1.0)
            col_out = mixk.outputs[2]
        links.new(store(g, "known_col", "FLOAT_COLOR", col_out, domain="FACE"), join.inputs["Geometry"])
    geom = join.outputs["Geometry"]
    pos = nodes.new("GeometryNodeInputPosition")
    p_room0 = pos.outputs["Position"]
    thing_attr = nodes.new("GeometryNodeInputNamedAttribute")
    thing_attr.data_type = "FLOAT"
    thing_attr.inputs["Name"].default_value = "thing"
    row = _thing_lookup(nodes, links, table_obj, math("ROUND", thing_attr.outputs["Attribute"]))
    # the sense on the vertex's part this frame (rung 2p), and the breathing scale about the part's centre
    sense = None
    p_room = p_room0
    if sense_img is not None:
        contact = None
        if contact_obj is not None:
            # each vertex's contact, kept on it while the shape still stands in the room
            geom = store(geom, "contact", "FLOAT", _contact_at(nodes, links, contact_obj, p_room0))
            contact = named("contact", "FLOAT")
            # and whether it is skin: a vertex of a body part inside another piece of the body is left out below
            is_body = math("MULTIPLY", math("GREATER_THAN", row["part"], -0.5), math("LESS_THAN", row["part"], len(tags.PARTS) - 0.5))
            geom = store(geom, "inner", "FLOAT", math("MULTIPLY", _inner_at(nodes, links, contact_obj, p_room0), is_body))
        sense = _sense_of(nodes, links, sense_img, row["part"], n_frames, senses_on, math, vmath,
                          contact=contact if outline else None, organs_only=not outline, soft=outline)
        pc_v = named("pc", "FLOAT_VECTOR")
        p_room = vmath("ADD", pc_v, vmath("SCALE", vmath("SUBTRACT", p_room0, pc_v), scale=sense["scale"]))
    # the known light on each face, worked out in the room before the shape is moved into the model (a Position or
    # Normal node reads the geometry where it is consumed): the sky's level indoors or outdoors by the face's centre
    # against the room's box, the sun's share by the face's normal against the sun's direction in the room
    sun = nodes.new("ShaderNodeCombineXYZ")
    links.new(value("SunX", 1.0), sun.inputs["X"])
    links.new(value("SunY", 0.0), sun.inputs["Y"])
    links.new(value("SunZ", 0.0), sun.inputs["Z"])
    W_, D_, H_ = room_size
    sep_r = nodes.new("ShaderNodeSeparateXYZ")
    links.new(p_room0, sep_r.inputs["Vector"])
    inside = math("MULTIPLY", math("MULTIPLY", math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", sep_r.outputs["X"], W_ / 2.0)), W_ / 2.0 + 0.05),
                                              math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", sep_r.outputs["Y"], D_ / 2.0)), D_ / 2.0 + 0.05)),
                  math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", sep_r.outputs["Z"], H_ / 2.0)), H_ / 2.0 + 0.05))
    sky_mix = nodes.new("ShaderNodeMix")
    sky_mix.data_type = "VECTOR"
    links.new(inside, sky_mix.inputs["Factor"])
    sky_mix.inputs[4].default_value = tuple(SHAPE_SKY_OUT)
    sky_mix.inputs[5].default_value = tuple(SHAPE_SKY_IN)
    # the sky's level by the face, the sun's share by each tile's own smooth normal below (a Normal node read on the
    # points is the vertex normal, the surface's as the picture has it): lit once per face, every tile of a face
    # carried one flat colour and the tiles' drift showed nothing inside it (2026-11-12)
    geom = store(geom, "sky_lvl", "FLOAT_VECTOR", sky_mix.outputs[1], domain="FACE")
    # and the exposure by the face the same way: the picture's own brightness indoors, or outdoors (set at render time)
    expo_mix = nodes.new("ShaderNodeMix")
    expo_mix.data_type = "FLOAT"
    links.new(inside, expo_mix.inputs["Factor"])
    links.new(value("ExposureOut", 1.0), expo_mix.inputs[2])
    links.new(value("Exposure", 1.0), expo_mix.inputs[3])
    geom = store(geom, "expo", "FLOAT", expo_mix.outputs[0], domain="FACE")
    nrm_pt = nodes.new("GeometryNodeInputNormal")
    geom = store(geom, "nrm_room", "FLOAT_VECTOR", vmath("NORMALIZE", named("nrm_smooth", "FLOAT_VECTOR")))
    # and the face's own normal, for the test of whether the eyes see a tile's place (below)
    geom = store(geom, "nrm_face", "FLOAT_VECTOR", nrm_pt.outputs["Normal"], domain="FACE")
    # into the model's frame, and placed about the eyes as the thing's hits are: by its centre's believed distance
    # over its true one, pressed onto the glass beyond the knee
    info_f = nodes.new("GeometryNodeObjectInfo")
    info_f.transform_space = "ORIGINAL"
    info_f.inputs["Object"].default_value = frame_obj
    tp = nodes.new("FunctionNodeTransformPoint")
    links.new(p_room, tp.inputs["Vector"])
    links.new(info_f.outputs["Transform"], tp.inputs["Transform"])
    tc = nodes.new("FunctionNodeTransformPoint")
    links.new(row["centre"], tc.inputs["Vector"])
    links.new(info_f.outputs["Transform"], tc.inputs["Transform"])
    eye = nodes.new("GeometryNodeObjectInfo")
    eye.transform_space = "ORIGINAL"
    eye.inputs["Object"].default_value = eye_obj
    # the eyes the picture is tested from, and the frame its pictures are read at: the present ones, or (held) the eyes
    # as they were when they took the picture they last held, and that picture's frame
    eye_t, frame_pic = eye, None
    if held:
        eye_t = nodes.new("GeometryNodeObjectInfo")
        eye_t.transform_space = "ORIGINAL"
        eye_t.inputs["Object"].default_value = test_eye_obj
        frame_pic = value("MemFrame", 1.0)
    v = vmath("SUBTRACT", tp.outputs["Vector"], eye.outputs["Location"])
    v_c = vmath("SUBTRACT", tc.outputs["Vector"], eye.outputs["Location"])
    d = math("MAXIMUM", vmath("LENGTH", v), 1e-6)
    dc = math("MAXIMUM", vmath("LENGTH", v_c), 1e-6)
    sep_t = nodes.new("FunctionNodeSeparateTransform")
    links.new(info_f.outputs["Transform"], sep_t.inputs["Transform"])
    sep_s = nodes.new("ShaderNodeSeparateXYZ")
    links.new(sep_t.outputs["Scale"], sep_s.inputs["Vector"])
    mscale = sep_s.outputs["X"]
    d_room = math("DIVIDE", d, mscale)
    dc_room = math("DIVIDE", dc, mscale)

    def ordered_of(d_room_):
        b_near = math("MINIMUM", d_room_, engine.BELIEVE_NEAR)
        b_over = math("MAXIMUM", math("SUBTRACT", d_room_, engine.BELIEVE_NEAR), 0.0)
        ln = nodes.new("ShaderNodeMath")
        ln.operation = "LOGARITHM"
        links.new(math("ADD", math("DIVIDE", b_over, engine.BELIEVE_K), 1.0), ln.inputs[0])
        ln.inputs[1].default_value = 2.718281828459045
        return math("ADD", b_near, math("MULTIPLY", ln.outputs["Value"], engine.BELIEVE_K))

    # every vertex placed exactly as a hit there would be (scan_nodes place): a compact thing scaled whole about
    # the eyes by its centre's believed distance, a spanning one compressed point by point, between the two by
    # its radius over its distance; flat at the sky until the far field resolves; pressed onto the glass beyond
    # the knee. One scale from the centre (until the fix of 2026-11-11) put a far crown's near side in front of
    # its own hits while the far field was still flattening
    ordered = ordered_of(d_room)
    shape = math("MULTIPLY", ordered_of(dc_room), math("DIVIDE", d_room, dc_room))
    compact = nodes.new("ShaderNodeMapRange")
    compact.interpolation_type = "SMOOTHSTEP"
    compact.inputs["From Min"].default_value = engine.COMPACT[0]
    compact.inputs["From Max"].default_value = engine.COMPACT[1]
    compact.inputs["To Min"].default_value = 1.0
    compact.inputs["To Max"].default_value = 0.0
    links.new(math("DIVIDE", row["radius"], dc_room), compact.inputs["Value"])
    resolved = math("ADD", ordered, math("MULTIPLY", math("SUBTRACT", shape, ordered), compact.outputs["Result"]))
    b_far = math("MAXIMUM", math("SUBTRACT", d_room, engine.BELIEVE_FLAT_FROM), 0.0)
    flat_rise = math("SUBTRACT", 1.0, math("EXPONENT", math("DIVIDE", b_far, -engine.BELIEVE_FLAT_K)))
    flat = math("ADD", math("MINIMUM", ordered, engine.BELIEVE_FLAT_BASE), math("MULTIPLY", flat_rise, engine.BELIEVE_SKY - engine.BELIEVE_FLAT_BASE))
    believed = math("ADD", flat, math("MULTIPLY", math("SUBTRACT", resolved, flat), resolve))
    d_b = math("MULTIPLY", believed, mscale)
    knee = KNEE * radius
    span = radius - knee
    near = math("MINIMUM", d_b, knee)
    over = math("MAXIMUM", math("SUBTRACT", d_b, knee), 0.0)
    eased = math("MULTIPLY", math("SUBTRACT", 1.0, math("EXPONENT", math("MULTIPLY", math("DIVIDE", over, span), -1.0))), span)
    d_pressed = math("ADD", near, eased)
    ratio = math("DIVIDE", d_pressed, d)
    whole = math("GREATER_THAN", compact.outputs["Result"], 0.5)
    p1 = vmath("ADD", eye.outputs["Location"], vmath("SCALE", v, scale=ratio))
    # inside its own surface by SHAPE_IN_FOOT footprints along its own normal, whatever its shape (the outline a little
    # outside it instead, over the part's tiles)
    nrm = nodes.new("GeometryNodeInputNormal")
    n_dir = nodes.new("FunctionNodeTransformDirection")
    links.new(vmath("NORMALIZE", named("nrm_smooth", "FLOAT_VECTOR")), n_dir.inputs["Direction"])
    links.new(info_f.outputs["Transform"], n_dir.inputs["Transform"])
    n_model = vmath("NORMALIZE", n_dir.outputs["Direction"])
    push = -SHAPE_IN_FOOT if not outline else OUTLINE_OUT
    p2 = vmath("ADD", p1, vmath("SCALE", n_model, scale=math("MULTIPLY", d_pressed, pixel_angle * push)))
    if outline:
        # the glow's layer stands OUTLINE_HALO outside the skin, in the model's scale (the note at OUTLINE_HALO)
        p2 = vmath("ADD", p2, vmath("SCALE", n_model, scale=math("MULTIPLY", mscale, OUTLINE_HALO)))
    # the hit's facts, kept on the vertices for the tiles below (a Position node reads the geometry where it is
    # consumed, so these are stored while the shape still stands in the room): its room point, its distances, its
    # ray, its thing's radius and its footprint
    facing = vmath("NORMALIZE", vmath("SUBTRACT", p2, eye.outputs["Location"]))
    tm = nodes.new("GeometryNodeInputSceneTime")
    pic_frame = frame_pic if held else tm.outputs["Frame"]
    axes_model = []
    for k in range(3):
        ax_c = nodes.new("ShaderNodeCombineXYZ")
        ax_c.inputs[k].default_value = 1.0
        ax_d = nodes.new("FunctionNodeTransformDirection")
        links.new(ax_c.outputs["Vector"], ax_d.inputs["Direction"])
        links.new(info_f.outputs["Transform"], ax_d.inputs["Transform"])
        axes_model.append(vmath("NORMALIZE", ax_d.outputs["Direction"]))
    geom = store(geom, "q_room", "FLOAT_VECTOR", p_room)
    geom = store(geom, "d_room", "FLOAT", d_room)
    geom = store(geom, "d_pressed", "FLOAT", d_pressed)
    geom = store(geom, "facing", "FLOAT_VECTOR", facing)
    geom = store(geom, "radius", "FLOAT", row["radius"])
    # how far the thing it ripples with is held whole (the table's wave_id: itself, or the thing it is set into, lies on
    # or rests on): its own ripple (_heat)
    tcw = nodes.new("FunctionNodeTransformPoint")
    links.new(row["wave_centre"], tcw.inputs["Vector"])
    links.new(info_f.outputs["Transform"], tcw.inputs["Transform"])
    dcw_room = math("DIVIDE", math("MAXIMUM", vmath("LENGTH", vmath("SUBTRACT", tcw.outputs["Vector"], eye.outputs["Location"])), 1e-6), mscale)
    own_wave = nodes.new("ShaderNodeMapRange")
    own_wave.interpolation_type = "SMOOTHSTEP"
    own_wave.inputs["From Min"].default_value = engine.COMPACT[0]
    own_wave.inputs["From Max"].default_value = engine.COMPACT[1]
    own_wave.inputs["To Min"].default_value = 1.0
    own_wave.inputs["To Max"].default_value = 0.0
    links.new(math("DIVIDE", row["wave_radius"], dcw_room), own_wave.inputs["Value"])
    geom = store(geom, "own_wave", "FLOAT", own_wave.outputs["Result"])
    geom = store(geom, "wave_id", "FLOAT", row["wave_id"])
    geom = store(geom, "wave_radius", "FLOAT", row["wave_radius"])
    geom = store(geom, "round", "FLOAT", row["round"])
    geom = store(geom, "foot", "FLOAT", math("MULTIPLY", d_pressed, pixel_angle * OVERLAP))
    if not outline:
        # the way back from where the shape is set in (SHAPE_IN_FOOT, above) to its own surface, for the tiles drawn as seen
        geom = store(geom, "inset_v", "FLOAT_VECTOR", vmath("SCALE", n_model, scale=math("MULTIPLY", d_pressed, pixel_angle * SHAPE_IN_FOOT)))
    if outline:
        # the outline glow (rung 2p): the surface kept, lit at its rim by the outline sense on its part, in that colour
        own_o = nodes.new("ShaderNodeMix")
        own_o.data_type = "RGBA"
        own_o.inputs["Factor"].default_value = SENSE_MIX
        links.new(named("known_col", "FLOAT_COLOR"), own_o.inputs[6])
        links.new(sense["out_col"], own_o.inputs[7])
        geom = store(geom, "out_col", "FLOAT_COLOR", own_o.outputs[2])
        # on the skin alone: nought where the piece runs inside another (inner, from ContactBody)
        skin_w = 1.0 if contact_obj is None else math("SUBTRACT", 1.0, named("inner", "FLOAT"))
        geom = store(geom, "out_s", "FLOAT", math("MULTIPLY", sense["out_s"], skin_w))
        # the glow of a touch, a pain or a pleasure over the skin (2026-11-13): the sense's colour over the part's own by
        # its share, its strength falling with the contact itself (a soft edge), on the skin's parts alone; and the room
        # point, which the glow's waver is laid over
        own_g = nodes.new("ShaderNodeMix")
        own_g.data_type = "RGBA"
        links.new(sense["tint"], own_g.inputs["Factor"])
        links.new(named("known_col", "FLOAT_COLOR"), own_g.inputs[6])
        links.new(sense["col"], own_g.inputs[7])
        touch_s = math("MULTIPLY", math("MULTIPLY", sense["s"], sense["skin"]), skin_w)
        geom = store(geom, "glow_col", "FLOAT_COLOR", own_g.outputs[2])
        geom = store(geom, "glow_s", "FLOAT", touch_s)
        most = math("MAXIMUM", math("MULTIPLY", sense["out_s"], skin_w), touch_s)
        if contact_obj is not None:
            # warmth and the window's cold air, as touch (his word of 2026-11-13): the part's level times what
            # ContactBody says the sun's rays and the air reach at this point of the skin, kept apart from the touch
            # (temp_col, temp_s) so the material can hide them where that skin faces away from the camera. Of the two
            # the stronger shows in its own colour, over the part's own at SENSE_MIX
            warm_s = math("MULTIPLY", math("MULTIPLY", sense["warm"], _body_at(nodes, links, contact_obj, p_room0, "sun")), skin_w)
            cool_s = math("MULTIPLY", math("MULTIPLY", sense["cool"], _body_at(nodes, links, contact_obj, p_room0, "air")), skin_w)
            temp_s = math("MAXIMUM", warm_s, cool_s)
            pick = nodes.new("ShaderNodeMapRange")
            pick.interpolation_type = "SMOOTHSTEP"
            pick.inputs["From Min"].default_value = -PAIR_BAND
            pick.inputs["From Max"].default_value = PAIR_BAND
            links.new(math("DIVIDE", math("SUBTRACT", cool_s, warm_s), math("MAXIMUM", math("ADD", warm_s, cool_s), 1e-6)), pick.inputs["Value"])
            which = nodes.new("ShaderNodeMix")
            which.data_type = "RGBA"
            links.new(pick.outputs["Result"], which.inputs["Factor"])
            which.inputs[6].default_value = (*tags.SENSE_COLOUR["temperature"], 1.0)
            which.inputs[7].default_value = (*tags.SENSE_COLOUR["airflow"], 1.0)
            own_t = nodes.new("ShaderNodeMix")
            own_t.data_type = "RGBA"
            own_t.inputs["Factor"].default_value = SENSE_MIX
            links.new(named("known_col", "FLOAT_COLOR"), own_t.inputs[6])
            links.new(which.outputs[2], own_t.inputs[7])
            geom = store(geom, "temp_col", "FLOAT_COLOR", own_t.outputs[2])
            geom = store(geom, "temp_s", "FLOAT", temp_s)
            most = math("MAXIMUM", most, temp_s)
        # the flash of the part a spark comes from, over the part's skin
        flash_s = math("MULTIPLY", sense["flash"], skin_w)
        geom = store(geom, "flash_s", "FLOAT", flash_s)
        most = math("MAXIMUM", most, flash_s)
        geom = store(geom, "most_s", "FLOAT", most)
        geom = store(geom, "glow_p", "FLOAT_VECTOR", p_room0)
        setp = nodes.new("GeometryNodeSetPosition")
        links.new(geom, setp.inputs["Geometry"])
        links.new(p2, setp.inputs["Position"])
        drop = math("MAXIMUM", math("LESS_THAN", named("most_s", "FLOAT"), 0.02), math("LESS_THAN", visible, 0.01))
        dele = nodes.new("GeometryNodeDeleteGeometry")
        dele.domain = "FACE"
        dele.mode = "ALL"
        links.new(setp.outputs["Geometry"], dele.inputs["Geometry"])
        links.new(drop, dele.inputs["Selection"])
        setm = nodes.new("GeometryNodeSetMaterial")
        setm.inputs["Material"].default_value = material
        links.new(dele.outputs["Geometry"], setm.inputs["Geometry"])
        links.new(setm.outputs["Geometry"], go.inputs["Geometry"])
        return ng
    setp = nodes.new("GeometryNodeSetPosition")
    links.new(geom, setp.inputs["Geometry"])
    links.new(p2, setp.inputs["Position"])
    geom = setp.outputs["Geometry"]
    # its known colour under the known light (shade, above) at the eye's exposure that frame (Exposure, set at render
    # time); lit by the thought on its thing, or by the eyes being shut as far as he is aware (Shut, keyed: the room
    # and his own body come up from memory at the alarm, as the beats say)
    think = None
    for i in range(MEM_REGION_COUNT):
        lit_i = math("MULTIPLY", value(f"Think{i}", 0.0), math("COMPARE", row["region"], float(i), 0.5))
        think = lit_i if think is None else math("MAXIMUM", think, lit_i)
    # lit by a thought alone (his eleventh review of 2026-11-11: the eyes shut do not bring the whole room up; at the
    # alarm the thought of the phone, the table, the bed and his own body does, data/senses.json)
    shut_v = value("Shut", 0.0)
    lit = math("MINIMUM", think, 1.0)
    if held:
        lit = math("MULTIPLY", lit, 0.0)      # nothing as a memory: the faces seen edge-on in the last picture alone
    # how far the thing has its colour back (Col0 to Col9, keyed: a thought's things come up as shapes first, colourless,
    # their colour COLOUR_DELAY later, his word of 2026-11-12); a part a sense lights has its colour at once
    colour = None
    for i in range(MEM_REGION_COUNT):
        c_i = math("MULTIPLY", value(f"Col{i}", 1.0), math("COMPARE", row["region"], float(i), 0.5))
        colour = c_i if colour is None else math("MAXIMUM", colour, c_i)
    if sense is not None:
        colour = math("MAXIMUM", colour, math("MINIMUM", math("DIVIDE", sense["s"], SENSE_ON), 1.0))
    # at a seam of the eyes' picture the memory and the seen picture meet with no gap (his fourteenth round of
    # 2026-11-14: "the gap between all seams should be filled in with the memory effect so the seam has no gaps - with
    # all objects"): where the picture has a seam (_seam_map), a tile that a thought or a sense lights is kept though
    # the eyes see its place, set just behind the seen surface and held still (below). Sight itself lights no tile,
    # at a place it sees or at one it does not (his word of 2026-11-14 on that day's stills: "it wasn't that the
    # unseen part should have been as memory (unless the timeline changed)"): what the eyes see is the seen
    # picture's to draw, whole (scan_nodes, sheet)
    seam, still, hold_live = None, None, None
    edge_seen = EDGE_SEEN and seen_material is not None and scan_size is not None and None not in (live_pos_img, live_idx_img, live_col_img)
    seen_pts = None
    live_now = value("LiveNow", 1.0) if live_pos_img is not None else None
    if live_pos_img is not None and live_idx_img is not None and not held:
        inv_s = nodes.new("FunctionNodeInvertMatrix")
        links.new(info_f.outputs["Transform"], inv_s.inputs["Matrix"])
        eye_s = nodes.new("FunctionNodeTransformPoint")
        links.new(eye.outputs["Location"], eye_s.inputs["Vector"])
        links.new(inv_s.outputs["Matrix"], eye_s.inputs["Transform"])
        tm_s = nodes.new("GeometryNodeInputSceneTime")
        seam = _seam_map(nodes, links, math, vmath, live_idx_img, live_pos_img, tm_s.outputs["Frame"], eye_s.outputs["Vector"], fov_deg)
    geom = store(geom, "mem_colour", "FLOAT", colour)
    if sense is not None:
        if sense["touch_lvl"] is not None:
            # what lights the vertex besides touch, and the part's touch level, for the rim's tiles below
            geom = store(geom, "other_lit", "FLOAT", math("MAXIMUM", lit, sense["light_s"]))
            geom = store(geom, "touch_lvl", "FLOAT", sense["touch_lvl"])
        # or by the sense on its part (rung 2p): a touched hand's shape in the touch's colour, the heart while thought of
        lit = math("MAXIMUM", lit, sense["s"])
        geom = store(geom, "sense_s", "FLOAT", sense["s"])
        geom = store(geom, "sense_col", "FLOAT_COLOR", sense["col"])
        geom = store(geom, "sense_w", "FLOAT", sense["mix"])
        geom = store(geom, "sense_clear", "FLOAT", sense["clear"])
    geom = store(geom, "mem_lit", "FLOAT", lit)
    geom = store(geom, "gate", "FLOAT", 1.0)
    # drawn wherever it is remembered, whole or not (the walls, the floor and the ceiling with the rest: his
    # eleventh review of 2026-11-11, everything in the mind's eye by the one rule)
    unlit = math("LESS_THAN", lit, 0.02)
    if edge_seen:
        # a face the eyes may see nearly edge-on is kept though nothing lights it as a memory: its tiles are put to
        # the test below (EDGE_SEEN). By the face's own normal and its middle, while the live picture stands
        inv_k = nodes.new("FunctionNodeInvertMatrix")
        links.new(info_f.outputs["Transform"], inv_k.inputs["Matrix"])
        eye_k = nodes.new("FunctionNodeTransformPoint")
        links.new(eye_t.outputs["Location"], eye_k.inputs["Vector"])
        links.new(inv_k.outputs["Matrix"], eye_k.inputs["Transform"])
        c_k = math("ABSOLUTE", vmath("DOT_PRODUCT", vmath("NORMALIZE", named("nrm_face", "FLOAT_VECTOR")),
                                    vmath("NORMALIZE", vmath("SUBTRACT", named("q_room", "FLOAT_VECTOR"), eye_k.outputs["Vector"]))))
        # (a round thing's within EDGE_SEEN_ROUND: its limb is the tiles' to draw)
        thr_k = math("ADD", TILT_COS, math("MULTIPLY", named("round", "FLOAT"), EDGE_SEEN_ROUND - TILT_COS))
        edge_face = math("MULTIPLY", math("LESS_THAN", c_k, math("MULTIPLY", thr_k, EDGE_SEEN_KEEP)), math("GREATER_THAN", live_now, SEEN_FADE[0]))
        unlit = math("MULTIPLY", unlit, math("SUBTRACT", 1.0, edge_face))
        # (kept on the faces, and so on their tiles: the touched patch's rim cut waits for the edge-on test on those)
        geom = store(geom, "edge_keep", "FLOAT", edge_face, domain="FACE")
    drop = math("MAXIMUM", unlit, math("LESS_THAN", visible, 0.01))
    dele = nodes.new("GeometryNodeDeleteGeometry")
    dele.domain = "FACE"
    dele.mode = "ALL"
    links.new(geom, dele.inputs["Geometry"])
    links.new(drop, dele.inputs["Selection"])
    # drawn as tiles, as every memory is (2026-11-12: a remembered thing drawn as one smooth surface, its vertices a
    # hand apart on a crown, bent with the memory's waves and showed nothing of them, while the same waves slide the
    # picture's tiles against each other and shimmer): SHAPE_TILES tiles per footprint squared over its faces, each
    # at the footprint in the surface, carrying its hit's facts, each drifting on its own
    foot_v = named("foot", "FLOAT")
    # a tile no smaller than a render pixel of the close camera (SPLAT_MIN of the glass radius, the floor the eyes' picture
    # has): a thing a hand's breadth from the eyes, his own body, had tiles a tenth of that pixel wide, 3.5 million of them
    # for the blanket's touch alone (2026-11-12). The footprint stored on the tiles for the near fade stays the plain one
    size_v = math("MAXIMUM", foot_v, radius * SPLAT_MIN)
    dist = nodes.new("GeometryNodeDistributePointsOnFaces")
    dist.distribute_method = "RANDOM"
    links.new(dele.outputs["Geometry"], dist.inputs["Mesh"])
    links.new(math("DIVIDE", SHAPE_TILES * OVERLAP * OVERLAP, math("MAXIMUM", math("MULTIPLY", size_v, size_v), 1e-12)), dist.inputs["Density"])
    eye_heat = nodes.new("FunctionNodeTransformPoint")     # the eyes in the room's own metres, for the ripple's field
    inv_heat = nodes.new("FunctionNodeInvertMatrix")
    links.new(info_f.outputs["Transform"], inv_heat.inputs["Matrix"])
    links.new(eye.outputs["Location"], eye_heat.inputs["Vector"])
    links.new(inv_heat.outputs["Matrix"], eye_heat.inputs["Transform"])
    off, heat_lvl = _heat(nodes, links, named("q_room", "FLOAT_VECTOR"), named("radius", "FLOAT"), named("d_room", "FLOAT"), named("d_pressed", "FLOAT"),
                          pixel_angle, axes_model, named("facing", "FLOAT_VECTOR"), tm, eye_room=eye_heat.outputs["Vector"],
                          own_body=named("own_body", "FLOAT"), thing=named("wave_id", "FLOAT"), own=named("own_wave", "FLOAT"),
                          table=table_obj, bend_radius=named("wave_radius", "FLOAT"))
    tiles_in = dist.outputs["Points"]
    if sense is not None and sense["touch_lvl"] is not None:
        # a touched patch at one brightness to its rim: a tile lit by touch alone is left out under CONTACT_RIM of the
        # part's touch level
        rim = math("MULTIPLY", math("LESS_THAN", named("other_lit", "FLOAT"), 0.02),
                   math("LESS_THAN", named("sense_s", "FLOAT"), math("MULTIPLY", named("touch_lvl", "FLOAT"), CONTACT_RIM)))
        if edge_seen:
            # a tile of a face kept for the edge-on test (EDGE_SEEN) is put to this cut after that test, below: taken
            # here, the tiles of his hand's edge-on faces went with the rim of its touch (2026-11-15, the phone at 133 s)
            late = math("MULTIPLY", rim, math("GREATER_THAN", named("edge_keep", "FLOAT"), 0.5))
            tiles_in = store(tiles_in, "rim_late", "FLOAT", late)
            rim = math("MULTIPLY", rim, math("LESS_THAN", named("edge_keep", "FLOAT"), 0.5))
        cut = nodes.new("GeometryNodeDeleteGeometry")
        cut.domain = "POINT"
        links.new(tiles_in, cut.inputs["Geometry"])
        links.new(rim, cut.inputs["Selection"])
        tiles_in = cut.outputs["Geometry"]
    if contact_obj is not None:
        # the body's skin alone: a tile of a body piece that lies inside another piece is not drawn
        cut_in = nodes.new("GeometryNodeDeleteGeometry")
        cut_in.domain = "POINT"
        links.new(tiles_in, cut_in.inputs["Geometry"])
        links.new(math("GREATER_THAN", named("inner", "FLOAT"), 0.5), cut_in.inputs["Selection"])
        tiles_in = cut_in.outputs["Geometry"]
    if live_pos_img is not None:
        # a tile whose place the eyes see this frame is not drawn (the notes above). The place's direction from the eyes
        # is its room point's (the placing and the pressing run along the eyes' own rays), carried into the eyes' frame
        # and laid on the scan's picture as the scan lays it (uv = 0.5 + theta / fov along the azimuth)
        # (LiveNow: the one value made above, where sight lights the seams)
        inv_f = nodes.new("FunctionNodeInvertMatrix")
        links.new(info_f.outputs["Transform"], inv_f.inputs["Matrix"])
        eye_rm = nodes.new("FunctionNodeTransformPoint")
        links.new(eye_t.outputs["Location"], eye_rm.inputs["Vector"])
        links.new(inv_f.outputs["Matrix"], eye_rm.inputs["Transform"])
        v_rm = vmath("SUBTRACT", named("q_room", "FLOAT_VECTOR"), eye_rm.outputs["Vector"])
        d_now = vmath("LENGTH", v_rm)
        to_m = nodes.new("FunctionNodeTransformDirection")
        links.new(v_rm, to_m.inputs["Direction"])
        links.new(info_f.outputs["Transform"], to_m.inputs["Transform"])
        ray_m = vmath("NORMALIZE", to_m.outputs["Direction"])
        inv_e = nodes.new("FunctionNodeInvertMatrix")
        links.new(eye_t.outputs["Transform"], inv_e.inputs["Matrix"])
        to_e = nodes.new("FunctionNodeTransformDirection")
        links.new(ray_m, to_e.inputs["Direction"])
        links.new(inv_e.outputs["Matrix"], to_e.inputs["Transform"])
        sep_e = nodes.new("ShaderNodeSeparateXYZ")
        links.new(vmath("NORMALIZE", to_e.outputs["Direction"]), sep_e.inputs["Vector"])
        theta = math("ARCCOSINE", math("MINIMUM", math("MAXIMUM", math("MULTIPLY", sep_e.outputs["Z"], -1.0), -1.0), 1.0))
        phi = math("ARCTAN2", sep_e.outputs["Y"], sep_e.outputs["X"])
        fov_rad = fov_deg * 3.141592653589793 / 180.0
        rr = math("DIVIDE", theta, fov_rad)
        uv_now = nodes.new("ShaderNodeCombineXYZ")
        links.new(math("MULTIPLY_ADD", rr, math("COSINE", phi), 0.5), uv_now.inputs["X"])
        links.new(math("MULTIPLY_ADD", rr, math("SINE", phi), 0.5), uv_now.inputs["Y"])
        tex = nodes.new("GeometryNodeImageTexture")
        tex.interpolation = "Closest"
        tex.extension = "EXTEND"
        tex.inputs["Image"].default_value = live_pos_img
        links.new(uv_now.outputs["Vector"], tex.inputs["Vector"])
        links.new(pic_frame, tex.inputs["Frame"])
        d_live = vmath("LENGTH", vmath("SUBTRACT", tex.outputs["Color"], eye_rm.outputs["Vector"]))
        # (a frame with no scan on disk reads nought everywhere: no hit, nothing seen)
        hit = math("GREATER_THAN", vmath("LENGTH", tex.outputs["Color"]), 1e-4)
        close = math("LESS_THAN", math("ABSOLUTE", math("SUBTRACT", d_live, d_now)), math("MULTIPLY", d_now, SEEN_TOL))
        # whether the picture resolves the tile's face at all (2026-11-14): a patch of it SEAM_CELL across, at its slant
        # to the eyes' ray (nrm_face, the face's own normal in the room), spans SEAM_PIX of the picture's pixels or more.
        # Where it does not (a crown's faces near its limb, each under a pixel wide), which pixel a tile falls on is
        # chance, and sight has no say on the tile: the scattered tiles it marked there stood as lines down the crown
        c_inc = math("ABSOLUTE", vmath("DOT_PRODUCT", vmath("NORMALIZE", named("nrm_face", "FLOAT_VECTOR")), vmath("NORMALIZE", v_rm)))
        resolved = math("GREATER_THAN", math("MULTIPLY", c_inc, SEAM_CELL), math("MULTIPLY", math("MULTIPLY", d_now, pixel_angle), SEAM_PIX))
        cen_now = vmath("SUBTRACT", uv_now.outputs["Vector"], (0.5, 0.5, 0.0))
        ell_now = vmath("LENGTH", vmath("MULTIPLY", cen_now, (2.0 * fov_deg / FIELD_H, 2.0 * fov_deg / FIELD_V, 0.0)))
        within = math("MULTIPLY", math("LESS_THAN", theta, fov_rad * 0.49), math("LESS_THAN", ell_now, 0.995))
        # (in the room, against the eyes' ray there: a flat-faced thing by its face's own normal; a ROUND thing by its
        # smooth normal at the tile, the one its light and its set-in use. A round thing's faces stand for a curved
        # surface, and that surface's own rim runs across its facets: the part of a facet on the eyes' side of that rim
        # is seen, the rest is the far side. Read off the face as placed and set in until 2026-11-15: a facet turned
        # toward the eyes by a degree came out turned away, and facets turned away by up to nine degrees were drawn as
        # seen behind a crown. By the face's own normal for every thing, one test scene (r14m30): two facets of a
        # stand-in crown, a metre wide and turned toward the eyes by one and two degrees, drawn whole, lumps over the
        # crown; without them (r14m33) a scoop out of its top)
        n_face_or_smooth = nodes.new("ShaderNodeMix")
        n_face_or_smooth.data_type = "VECTOR"
        links.new(named("round", "FLOAT"), n_face_or_smooth.inputs["Factor"])
        links.new(named("nrm_face", "FLOAT_VECTOR"), n_face_or_smooth.inputs[4])
        links.new(named("nrm_room", "FLOAT_VECTOR"), n_face_or_smooth.inputs[5])
        toward = math("LESS_THAN", vmath("DOT_PRODUCT", n_face_or_smooth.outputs[1], v_rm), 0.0)
        can_see = math("MAXIMUM", named("open", "FLOAT"), toward)
        seen = math("MULTIPLY", math("MULTIPLY", close, within), math("MULTIPLY", can_see, hit))
        # for the lids' wipe on a remembered tile (the material's lids="field"): its place in the eyes' picture, and
        # whether it lies inside their field
        tiles_in = store(tiles_in, "scan_uv", "FLOAT_VECTOR", uv_now.outputs["Vector"])
        tiles_in = store(tiles_in, "in_field", "FLOAT", within)
        if edge_seen:
            # a face the eyes see nearly edge-on (EDGE_SEEN): in their field, the scan's hit on its line no nearer than
            # the tile (the face itself, or whatever lies beyond it), the face turned their way, within TILT_COS of the
            # ray; while the live picture stands. Such a tile is the shape's to draw, as seen, and is no memory
            clear = math("GREATER_THAN", d_live, math("MULTIPLY", d_now, 1.0 - SEEN_TOL))
            # the limb's side (LIMB_NEAR): the way the tile's face turns from the eyes is its normal's part across
            # their ray, on the side facing them; that many pixels on in the picture (and half as many), another
            # thing or none
            ray_r = vmath("NORMALIZE", v_rm)
            n_r = vmath("NORMALIZE", named("nrm_face", "FLOAT_VECTOR"))
            n_eye = vmath("SCALE", n_r, scale=math("MULTIPLY", math("SIGN", vmath("DOT_PRODUCT", n_r, ray_r)), -1.0))
            tilt_n = vmath("NORMALIZE", vmath("SUBTRACT", n_eye, vmath("SCALE", ray_r, scale=vmath("DOT_PRODUCT", n_eye, ray_r))))

            def off_thing(v_l, behind=False):
                """Whether the picture, along the room direction given from the eyes, shows another thing than the tile's
                (with behind: and that thing's hit there lies beyond the tile, by SEEN_TOL of its distance)."""
                to_ml = nodes.new("FunctionNodeTransformDirection")
                links.new(v_l, to_ml.inputs["Direction"])
                links.new(info_f.outputs["Transform"], to_ml.inputs["Transform"])
                to_el = nodes.new("FunctionNodeTransformDirection")
                links.new(vmath("NORMALIZE", to_ml.outputs["Direction"]), to_el.inputs["Direction"])
                links.new(inv_e.outputs["Matrix"], to_el.inputs["Transform"])
                sep_l = nodes.new("ShaderNodeSeparateXYZ")
                links.new(vmath("NORMALIZE", to_el.outputs["Direction"]), sep_l.inputs["Vector"])
                th_l = math("ARCCOSINE", math("MINIMUM", math("MAXIMUM", math("MULTIPLY", sep_l.outputs["Z"], -1.0), -1.0), 1.0))
                ph_l = math("ARCTAN2", sep_l.outputs["Y"], sep_l.outputs["X"])
                rr_l = math("DIVIDE", th_l, fov_rad)
                uv_l = nodes.new("ShaderNodeCombineXYZ")
                links.new(math("MULTIPLY_ADD", rr_l, math("COSINE", ph_l), 0.5), uv_l.inputs["X"])
                links.new(math("MULTIPLY_ADD", rr_l, math("SINE", ph_l), 0.5), uv_l.inputs["Y"])
                t_l = nodes.new("GeometryNodeImageTexture")
                t_l.interpolation = "Closest"
                t_l.extension = "EXTEND"
                t_l.inputs["Image"].default_value = live_idx_img
                links.new(uv_l.outputs["Vector"], t_l.inputs["Vector"])
                links.new(pic_frame, t_l.inputs["Frame"])
                s_l = nodes.new("ShaderNodeSeparateXYZ")
                links.new(t_l.outputs["Color"], s_l.inputs["Vector"])
                off_s = math("SUBTRACT", 1.0, math("COMPARE", math("ROUND", s_l.outputs["X"]), named("thing", "FLOAT"), 0.5))
                if behind:
                    t_b = nodes.new("GeometryNodeImageTexture")
                    t_b.interpolation = "Closest"
                    t_b.extension = "EXTEND"
                    t_b.inputs["Image"].default_value = live_pos_img
                    links.new(uv_l.outputs["Vector"], t_b.inputs["Vector"])
                    links.new(pic_frame, t_b.inputs["Frame"])
                    d_b = vmath("LENGTH", vmath("SUBTRACT", t_b.outputs["Color"], eye_rm.outputs["Vector"]))
                    off_s = math("MULTIPLY", off_s, math("MULTIPLY", math("GREATER_THAN", vmath("LENGTH", t_b.outputs["Color"]), 1e-4),
                                                         math("GREATER_THAN", d_b, math("MULTIPLY", d_now, 1.0 + SEEN_TOL))))
                return off_s

            px_r = math("MULTIPLY", d_now, pixel_angle)       # a pixel of the picture at the tile, in the room's metres
            limb_side = None
            for k_px in (LIMB_NEAR, LIMB_NEAR * 0.5):
                off_l = off_thing(vmath("ADD", v_rm, vmath("SCALE", tilt_n, scale=math("MULTIPLY", px_r, k_px))))
                limb_side = off_l if limb_side is None else math("MAXIMUM", limb_side, off_l)
            wide = math("MULTIPLY", named("round", "FLOAT"), limb_side)
            # a round thing under THIN_PX pixels thick the way the face turns (that many pixels inward, the picture shows
            # another thing, one that lies behind the tile) has no limb apart from its body: the picture's own sheet
            # draws it whole (scan_nodes, thick) and its tiles are not drawn as seen. (Behind the tile: a thing in
            # front, the wall over the window before a crown, hides part of a thick thing and does not make it thin)
            # (inward: against the part across the ray of the shape's own OUTWARD normal. Not tilt_n, the normal as
            # turned toward the eyes: on a facet just past the outline, turned a little away from the eyes, that one is
            # the flipped normal and its part across the ray points into the thing; the step then went outward, met
            # the sky, and whole facets' tiles went from a crown's outline, bites out of it, 2026-11-16)
            out_n = vmath("NORMALIZE", vmath("SUBTRACT", n_r, vmath("SCALE", ray_r, scale=vmath("DOT_PRODUCT", n_r, ray_r))))
            thin_t = math("MULTIPLY", named("round", "FLOAT"),
                          off_thing(vmath("SUBTRACT", v_rm, vmath("SCALE", out_n, scale=math("MULTIPLY", px_r, THIN_PX))), behind=True))
            # a limb's end (LIMB_IN): half a tile along the limb either way (across the face's turn, across the ray),
            # and that many pixels in from the limb
            along_n = vmath("NORMALIZE", vmath("CROSS_PRODUCT", n_r, tilt_n))
            v_in = vmath("SUBTRACT", v_rm, vmath("SCALE", tilt_n, scale=math("MULTIPLY", px_r, LIMB_IN)))
            limb_end = None
            for sgn_a in (1.0, -1.0):
                off_a = off_thing(vmath("ADD", v_in, vmath("SCALE", along_n, scale=math("MULTIPLY", px_r, OVERLAP * 0.5 * sgn_a))), behind=True)
                limb_end = off_a if limb_end is None else math("MAXIMUM", limb_end, off_a)
            # (the wide band's tiles alone, a face seen at a slant: on a face seen edge-on, running along the ray,
            # "along the limb" has no direction, and the test took a comb of tiles from under his own leg; and only
            # where the other thing there lies behind the tile: beside a thing in front of it, the wall over the
            # window before a tree's crown, the picture ends and the tile with it, 2026-11-15)
            limb_end = math("MULTIPLY", math("MULTIPLY", named("round", "FLOAT"), math("GREATER_THAN", c_inc, TILT_COS)), limb_end)
            as_seen = math("MULTIPLY", math("MULTIPLY", math("MULTIPLY", within, hit), math("MULTIPLY", clear, can_see)),
                           math("MULTIPLY", math("LESS_THAN", c_inc, math("ADD", TILT_COS, math("MULTIPLY", wide, EDGE_SEEN_ROUND - TILT_COS))),
                                math("MULTIPLY", math("MULTIPLY", math("GREATER_THAN", live_now, SEEN_FADE[0]), math("SUBTRACT", 1.0, limb_end)),
                                     math("SUBTRACT", 1.0, thin_t))))
            if held:
                # the last picture's tiles are its flat-faced things' alone (HELD_TILES): its round things keep their rim
                # in their sheet and their limb's chords, as before 2026-11-16. A round thing's band of tiles ripples
                # tile by tile against a sheet that ripples vertex by vertex, and stood through it in blocks (a lamp
                # shade's side) and round it as specks (every remembered bush)
                as_seen = math("MULTIPLY", as_seen, math("SUBTRACT", 1.0, named("round", "FLOAT")))
            tiles_in = store(tiles_in, "as_seen", "FLOAT", as_seen)
            tiles_in = store(tiles_in, "uv_now", "FLOAT_VECTOR", uv_now.outputs["Vector"])
            seen = math("MULTIPLY", seen, math("SUBTRACT", 1.0, as_seen))
        # a tile at a place the eyes see gives way as the live picture comes to stand, as every memory does (SEEN_FADE, the
        # notes at scan_nodes): thinned by a smoothstep share of LiveNow between the marks, the share on the gate the
        # material multiplies its alpha by; with the eyes long shut the test is not even worked out
        if seam is not None:
            # at a seam of the eyes' picture a seen tile is kept: it lies inside its thing, behind the seen picture, and
            # shows where that picture ends or leaves a gap (deleted exactly up to the seen region's edge, the memory
            # stood off the seam by its own ripple: his second picture of 2026-11-14, the right wall). Deep inside
            # what the eyes see it goes, as ever
            # (none beyond the scan's circle, more than half its field from the eyes' line: read at the map's nearest
            # point, such a tile took the band of the map's border)
            still = math("MULTIPLY", _seam_at(nodes, links, vmath, seam, uv_now.outputs["Vector"]), math("LESS_THAN", rr, 0.5))
            # as far as the live picture stands (SEAM_STAND, for its stillness), and only where the picture resolves the
            # tile's face
            stand_t = nodes.new("ShaderNodeMapRange")
            stand_t.interpolation_type = "SMOOTHSTEP"
            stand_t.inputs["From Min"].default_value = SEAM_STAND[0]
            stand_t.inputs["From Max"].default_value = SEAM_STAND[1]
            stand_t.inputs["To Min"].default_value = 0.0
            stand_t.inputs["To Max"].default_value = 1.0
            links.new(live_now, stand_t.inputs["Value"])
            hold_live = stand_t.outputs["Result"]
            # (sight lights no tile: a kept one has its thought's or its sense's light and the memory's own look. Lit by
            # sight and coloured as seen for a day, 2026-11-14, the kept tiles lay in the seen surface's own plane wherever
            # that surface runs along the eyes' ray, and stood through it as a grey band)
            kept_t = math("MULTIPLY", math("MULTIPLY", seen, resolved), math("GREATER_THAN", still, SEAM_DEEP))
            tiles_in = store(tiles_in, "kept", "FLOAT", math("MULTIPLY", kept_t, math("GREATER_THAN", live_now, SEEN_FADE[0])))
            # (kept where the picture resolves its face; elsewhere it goes as ever)
            seen = math("MULTIPLY", seen, math("MAXIMUM", math("LESS_THAN", still, SEAM_DEEP), math("SUBTRACT", 1.0, resolved)))
        stand = nodes.new("ShaderNodeMapRange"); stand.interpolation_type = "SMOOTHSTEP"
        stand.inputs["From Min"].default_value = SEEN_FADE[0]; stand.inputs["From Max"].default_value = SEEN_FADE[1]
        stand.inputs["To Min"].default_value = 0.0; stand.inputs["To Max"].default_value = 1.0
        links.new(live_now, stand.inputs["Value"])
        fading = nodes.new("GeometryNodeSwitch")
        fading.input_type = "FLOAT"
        links.new(math("GREATER_THAN", live_now, SEEN_FADE[0]), fading.inputs["Switch"])
        fading.inputs["False"].default_value = 0.0
        # a tile seen edge-on (EDGE_SEEN) is, among the memory's tiles, a tile at a place the eyes see: it gives way to
        # the live picture by the same share and is gone outright once that picture stands whole, while the seen
        # picture's material draws it apart (below). Kept out of the memory's tiles until 2026-11-18, it was drawn by
        # neither once the seen picture's cover had run out through a long shutting of his eyes with LiveNow still over
        # SEEN_FADE's first mark: the limb of every round thing stood open, the sky through a remembered tree's crown,
        # until the memory's tiles came at a stroke at the mark, twenty frames after the shutting counted as long.
        # (The last picture's tiles, its flat-faced things' alone, are left as they were)
        seen_g = math("MAXIMUM", seen, named("as_seen", "FLOAT")) if (edge_seen and not held) else seen
        links.new(math("MULTIPLY", seen_g, stand.outputs["Result"]), fading.inputs["True"])
        gate_v = math("SUBTRACT", 1.0, fading.outputs["Output"])
        tiles_in = store(tiles_in, "gate", "FLOAT", gate_v)
        # and gone outright once the live picture stands whole
        gate = nodes.new("GeometryNodeSwitch")
        gate.input_type = "BOOLEAN"
        links.new(math("GREATER_THAN", live_now, SEEN_FADE[1]), gate.inputs["Switch"])
        gate.inputs["False"].default_value = False
        links.new(seen_g, gate.inputs["True"])
        if edge_seen and not held:
            # (the tiles drawn as seen are taken here, before the memory's cuts, from the same tiles)
            sep_edge = nodes.new("GeometryNodeSeparateGeometry")
            sep_edge.domain = "POINT"
            links.new(tiles_in, sep_edge.inputs["Geometry"])
            links.new(math("GREATER_THAN", named("as_seen", "FLOAT"), 0.5), sep_edge.inputs["Selection"])
            seen_pts = sep_edge.outputs["Selection"]
        cut_seen = nodes.new("GeometryNodeDeleteGeometry")
        cut_seen.domain = "POINT"
        links.new(tiles_in, cut_seen.inputs["Geometry"])
        links.new(gate.outputs["Output"], cut_seen.inputs["Selection"])
        tiles_in = cut_seen.outputs["Geometry"]
        if edge_seen:
            # the tiles of the faces kept for the test that are neither a memory nor seen edge-on go; the ones seen
            # edge-on are drawn apart (below)
            cut_dim = nodes.new("GeometryNodeDeleteGeometry")
            cut_dim.domain = "POINT"
            links.new(tiles_in, cut_dim.inputs["Geometry"])
            # (unlit, or left out by the touched patch's rim cut, which waited for this test: rim_late)
            gone = math("LESS_THAN", named("mem_lit", "FLOAT"), 0.02)
            if sense is not None and sense["touch_lvl"] is not None:
                gone = math("MAXIMUM", gone, math("GREATER_THAN", named("rim_late", "FLOAT"), 0.5))
            if held:
                links.new(math("MULTIPLY", gone, math("LESS_THAN", named("as_seen", "FLOAT"), 0.5)),
                          cut_dim.inputs["Selection"])
                sep_s = nodes.new("GeometryNodeSeparateGeometry")
                sep_s.domain = "POINT"
                links.new(cut_dim.outputs["Geometry"], sep_s.inputs["Geometry"])
                links.new(math("GREATER_THAN", named("as_seen", "FLOAT"), 0.5), sep_s.inputs["Selection"])
                seen_pts = sep_s.outputs["Selection"]
                tiles_in = sep_s.outputs["Inverted"]
            else:
                # (an unlit tile goes from the memory's tiles whether or not it is seen edge-on, and what is left are
                # the memory's tiles, the ones seen edge-on among them)
                links.new(gone, cut_dim.inputs["Selection"])
                tiles_in = cut_dim.outputs["Geometry"]
    drift = nodes.new("GeometryNodeSetPosition")
    links.new(tiles_in, drift.inputs["Geometry"])
    if still is not None:
        # a tile at a seam of the eyes' picture holds still: the memory is anchored where it meets what he sees, and
        # ripples freely away from it (the waves' light it keeps)
        # and sits just behind the seen surface: SEAM_BACK of its distance along its own face's normal, away from the
        # eyes (along the eyes' ray until 2026-11-14: a tile of a surface that runs along the ray stayed in the surface's
        # own plane, and stood through the seen picture from the camera's side)
        pos_t = nodes.new("GeometryNodeInputPosition")
        to_t = vmath("SUBTRACT", pos_t.outputs["Position"], eye.outputs["Location"])
        n_t = vmath("NORMALIZE", dist.outputs["Normal"])
        n_away = vmath("SCALE", n_t, scale=math("SIGN", vmath("DOT_PRODUCT", n_t, to_t)))
        away_t = vmath("SCALE", n_away, scale=math("MULTIPLY", math("MULTIPLY", named("kept", "FLOAT"), vmath("LENGTH", to_t)), SEAM_BACK))
        # (as far as the live picture stands: with his eyes shut a memory ripples at a seam as it does anywhere)
        # (how far: the wide band inside the scan's circle, SEAM_WIDE; and by the field's own ellipse, whole from just
        # inside its edge and falling as a bell beyond it, SEAM_RING_HOLD, on both sides of the scan's circle. The
        # seam band times three, cut at one, and nothing beyond the circle, until 2026-11-15: the hold ended within a
        # degree and a half, and at the circle on a line, and the ripple tore the remembered wall along both)
        ring_h = math("MULTIPLY", math("GREATER_THAN", ell_now, 0.97),
                      math("EXPONENT", math("MULTIPLY", math("POWER", math("DIVIDE", math("MAXIMUM", math("SUBTRACT", ell_now, 1.0), 0.0), SEAM_RING_HOLD), 2.0), -0.5)))
        # (beyond the scan's circle the band of the map's nearest place, falling as a bell of the band's own width,
        # SEAM_WIDE_OUT of the scan's field, so the hold has no step at the circle: cut off there, a tick of the crack
        # stayed wherever the band stood higher than the ellipse's own bell)
        wide_h = math("MULTIPLY", _seam_at(nodes, links, vmath, seam, uv_now.outputs["Vector"], "band_wide"),
                      math("EXPONENT", math("MULTIPLY", math("POWER", math("DIVIDE", math("MAXIMUM", math("SUBTRACT", rr, 0.5), 0.0), SEAM_WIDE_OUT), 2.0), -0.5)))
        held_t = math("MULTIPLY", math("MAXIMUM", wide_h, ring_h), hold_live)
        links.new(vmath("ADD", vmath("SCALE", off, scale=math("SUBTRACT", 1.0, held_t)), away_t), drift.inputs["Offset"])
    else:
        links.new(off, drift.inputs["Offset"])
    # each tile's colour: the known colour under the sky's level and the sun's share by its own normal, at the eye's
    # exposure that frame
    # (SunShare, keyed: the share of the sun's disc that stands above the ridge; nought until first light)
    lit_t = math("MULTIPLY", value("SunShare", 1.0),
                 math("MAXIMUM", vmath("DOT_PRODUCT", vmath("NORMALIZE", named("nrm_room", "FLOAT_VECTOR")), vmath("NORMALIZE", sun.outputs["Vector"])), 0.0))
    shade_t = vmath("ADD", named("sky_lvl", "FLOAT_VECTOR"), vmath("SCALE", tuple(SHAPE_SUN), scale=lit_t))
    # and its own grain, by its stable id (SHAPE_GRAIN)
    rnd = nodes.new("FunctionNodeRandomValue")
    rnd.data_type = "FLOAT"
    rnd.inputs[0].default_value = -SHAPE_GRAIN * 1.732
    rnd.inputs[1].default_value = SHAPE_GRAIN * 1.732
    grain = math("ADD", 1.0, rnd.outputs[0])
    known_lit = vmath("SCALE", vmath("MULTIPLY", named("known_col", "FLOAT_COLOR"), shade_t), scale=math("MULTIPLY", named("expo", "FLOAT"), grain))
    if sense is not None:
        # the sense's colour over the known colour by the sense's strength and tint, with the tile's own grain
        mixs = nodes.new("ShaderNodeMix")
        mixs.data_type = "RGBA"
        links.new(named("sense_w", "FLOAT"), mixs.inputs["Factor"])
        links.new(known_lit, mixs.inputs[6])
        links.new(vmath("SCALE", named("sense_col", "FLOAT_COLOR"), scale=grain), mixs.inputs[7])
        known_lit = mixs.outputs[2]
    tiles_g = store(drift.outputs["Geometry"], "scan_col", "FLOAT_COLOR", known_lit)
    tiles_g = store(tiles_g, "heat", "FLOAT", heat_lvl)
    tile = nodes.new("GeometryNodeMeshGrid")
    tile.inputs["Size X"].default_value = 1.0
    tile.inputs["Size Y"].default_value = 1.0
    tile.inputs["Vertices X"].default_value = 2
    tile.inputs["Vertices Y"].default_value = 2
    tile_m = nodes.new("GeometryNodeSetMaterial")
    tile_m.inputs["Material"].default_value = material
    links.new(store(tile.outputs["Mesh"], "chord", "FLOAT", 0.0), tile_m.inputs["Geometry"])
    size_t = nodes.new("ShaderNodeCombineXYZ")
    links.new(size_v, size_t.inputs["X"])
    links.new(size_v, size_t.inputs["Y"])
    size_t.inputs["Z"].default_value = 1.0
    iop = nodes.new("GeometryNodeInstanceOnPoints")
    links.new(tiles_g, iop.inputs["Points"])
    links.new(tile_m.outputs["Geometry"], iop.inputs["Instance"])
    links.new(dist.outputs["Rotation"], iop.inputs["Rotation"])
    # (a remembered tile SHAPE_GROW times as wide: the ripple stretches a remembered surface and its tiles thin out)
    size_m = nodes.new("ShaderNodeCombineXYZ")
    # (not a tile kept at a seam, which sits just behind the seen picture and holds still: wider, those covered the
    # thin line of a window frame's edge beside them, which broke into dashes)
    grow_m = math("MULTIPLY", size_v, math("ADD", 1.0, math("MULTIPLY", math("SUBTRACT", 1.0, named("kept", "FLOAT")), SHAPE_GROW - 1.0)))
    links.new(grow_m, size_m.inputs["X"])
    links.new(grow_m, size_m.inputs["Y"])
    size_m.inputs["Z"].default_value = 1.0
    links.new(size_m.outputs["Vector"], iop.inputs["Scale"])
    real = nodes.new("GeometryNodeRealizeInstances")
    links.new(iop.outputs["Instances"], real.inputs["Geometry"])

    def lean(geo_s):
        """The tiles without what no material reads of them (TILE_UNREAD)."""
        for nm_x in TILE_UNREAD:
            rm_x = nodes.new("GeometryNodeRemoveAttribute")
            links.new(geo_s, rm_x.inputs["Geometry"])
            rm_x.inputs["Name"].default_value = nm_x
            geo_s = rm_x.outputs["Geometry"]
        return geo_s

    drawn_t = lean(real.outputs["Geometry"])
    if seen_pts is not None:
        # the tiles of the faces the eyes see nearly edge-on (EDGE_SEEN): just behind the seen surface along the face's
        # own normal, still (no ripple: they are seen), in the picture's colour for their thing at their place
        pos_s = nodes.new("GeometryNodeInputPosition")
        to_s = vmath("SUBTRACT", pos_s.outputs["Position"], eye.outputs["Location"])
        n_s = vmath("NORMALIZE", dist.outputs["Normal"])
        n_aw = vmath("SCALE", n_s, scale=math("SIGN", vmath("DOT_PRODUCT", n_s, to_s)))
        back_s = nodes.new("GeometryNodeSetPosition")
        links.new(seen_pts, back_s.inputs["Geometry"])
        # (on its face's own plane: the shape is set SHAPE_IN_FOOT inside its surface so that a memory's tiles lie under
        # the picture; a tile drawn as seen IS the picture there, and set in with the rest it drew the face low and short
        # of its far edge: a black band between a piano's top and the wall behind it from the camera's side,
        # 2026-11-15. The set-in is taken back along the face's normal alone: within the face the tiles stay short of
        # its edges, where a tile half over an edge would stand past it. And EDGE_SEEN_THIN of SEAM_BACK behind that
        # plane for every thing alike: the whole of SEAM_BACK, kept for a thick closed thing until then, was another
        # centimetre and a half at the piano's distance)
        out_s = vmath("SCALE", n_s, scale=vmath("DOT_PRODUCT", named("inset_v", "FLOAT_VECTOR"), n_s))
        links.new(vmath("ADD", out_s, vmath("SCALE", n_aw, scale=math("MULTIPLY", vmath("LENGTH", to_s), SEAM_BACK * EDGE_SEEN_THIN))), back_s.inputs["Offset"])
        tm_c = nodes.new("GeometryNodeInputSceneTime")

        def pic(img, uv_socket):
            t_p = nodes.new("GeometryNodeImageTexture")
            t_p.interpolation = "Closest"
            t_p.extension = "EXTEND"
            t_p.inputs["Image"].default_value = img
            links.new(uv_socket, t_p.inputs["Vector"])
            links.new(pic_frame, t_p.inputs["Frame"])
            return t_p.outputs["Color"]

        uv_t, q_t, thing_t = named("uv_now", "FLOAT_VECTOR"), named("q_room", "FLOAT_VECTOR"), named("thing", "FLOAT")
        soft = math("MULTIPLY", named("d_room", "FLOAT"), pixel_angle)
        # the thing each pixel round the tile's place lies on (EDGE_SEEN_WIN each way, and one more for the test of an
        # inner pixel: its four neighbours on its own thing)
        n_w = EDGE_SEEN_WIN
        id_at = {}
        for d_x in range(-n_w - 1, n_w + 2):
            for d_y in range(-n_w - 1, n_w + 2):
                if abs(d_x) == n_w + 1 and abs(d_y) == n_w + 1:
                    continue
                id_k = nodes.new("ShaderNodeSeparateXYZ")
                links.new(pic(live_idx_img, vmath("ADD", uv_t, (d_x / scan_size[0], d_y / scan_size[1], 0.0))), id_k.inputs["Vector"])
                id_at[(d_x, d_y)] = math("ROUND", id_k.outputs["X"])
        # the tile's own face in the picture: the pixels whose hits lie within EDGE_SEEN_FACE footprints of its plane
        n_face = vmath("NORMALIZE", named("nrm_face", "FLOAT_VECTOR"))
        face_tol = math("MULTIPLY", soft, EDGE_SEEN_FACE)
        in_col, in_w, own_col, own_w, any_col, any_w, own9 = None, None, None, None, None, None, None
        near_col, near_w = None, None
        for d_x in range(-n_w, n_w + 1):
            for d_y in range(-n_w, n_w + 1):
                uv_k = vmath("ADD", uv_t, (d_x / scan_size[0], d_y / scan_size[1], 0.0))
                inner = None
                for o_x, o_y in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    same_o = math("COMPARE", id_at[(d_x + o_x, d_y + o_y)], id_at[(d_x, d_y)], 0.5)
                    inner = same_o if inner is None else math("MULTIPLY", inner, same_o)
                on_thing = math("COMPARE", id_at[(d_x, d_y)], thing_t, 0.5)
                if abs(d_x) <= 1 and abs(d_y) <= 1:
                    own9 = on_thing if own9 is None else math("ADD", own9, on_thing)
                p_k = pic(live_pos_img, uv_k)
                near_k = math("DIVIDE", on_thing, math("ADD", vmath("DISTANCE", p_k, q_t), soft))
                on_face = math("MULTIPLY", on_thing, math("LESS_THAN", math("ABSOLUTE", vmath("DOT_PRODUCT", vmath("SUBTRACT", p_k, q_t), n_face)), face_tol))
                col_k = pic(live_col_img, uv_k)
                for key, w_k in (("in", math("MULTIPLY", near_k, inner)), ("own", math("MULTIPLY", on_face, inner)), ("any", on_face)):
                    c_k2 = vmath("SCALE", col_k, scale=w_k)
                    if key == "in":
                        in_col, in_w = (c_k2, w_k) if in_col is None else (vmath("ADD", in_col, c_k2), math("ADD", in_w, w_k))
                    elif key == "own":
                        own_col, own_w = (c_k2, w_k) if own_col is None else (vmath("ADD", own_col, c_k2), math("ADD", own_w, w_k))
                    else:
                        any_col, any_w = (c_k2, w_k) if any_col is None else (vmath("ADD", any_col, c_k2), math("ADD", any_w, w_k))
                # (every pixel of its thing by nearness, rim ones with the rest: the last picture colour before the known one)
                c_n2 = vmath("SCALE", col_k, scale=near_k)
                near_col, near_w = (c_n2, near_k) if near_col is None else (vmath("ADD", near_col, c_n2), math("ADD", near_w, near_k))

        def pick_v(fac, a_s, b_s):
            p_v = nodes.new("ShaderNodeMix")
            p_v.data_type = "VECTOR"
            links.new(fac, p_v.inputs["Factor"])
            links.new(a_s, p_v.inputs[4])
            links.new(b_s, p_v.inputs[5])
            return p_v.outputs[1]

        def mean_of(col_s, w_s):
            return vmath("SCALE", col_s, scale=math("DIVIDE", 1.0, math("MAXIMUM", w_s, 1e-9)))

        # the mean of the picture over the tile's own face, its inner pixels first (a mean, each pixel alike: by the
        # nearest pixel a face a pixel or two wide came out hatched, the window's jamb at 34 s of the player). Failing
        # those, a flat-faced thing's tile takes the face's rim pixels (a round thing's are a mix with what stands
        # behind its silhouette, pale flecks on a crown); then the inner pixels of its thing nearby, by nearness; and
        # with none of those the known colour under the known light, as a memory's tile has it
        # (and before the known colour, the thing's own pixels nearby whatever they are, rim pixels too: a thing two or three
        # pixels wide in the picture, a lamp's pole, a tree's trunk, has no inner pixel, and with its tiles level with the
        # picture since 2026-11-15 the known colour stood on it as pale specks. The picture's own sheet ends on the same
        # choice: any neighbour on its thing)
        low_known = pick_v(math("GREATER_THAN", near_w, 0.0), known_lit, mean_of(near_col, near_w))
        low_round = pick_v(math("GREATER_THAN", in_w, 0.0), low_known, mean_of(in_col, in_w))
        low_flat = pick_v(math("GREATER_THAN", any_w, 0.0), low_round, mean_of(any_col, any_w))
        low = pick_v(math("GREATER_THAN", named("round", "FLOAT"), 0.5), low_flat, low_round)
        col_seen = pick_v(math("GREATER_THAN", own_w, 0.0), low, mean_of(own_col, own_w))
        # drawn as seen only where the picture shows the tile's own thing at its place or beside it: a tile of a piece
        # of his body buried in another (a joint's ball inside a limb) passes the as-seen test by its tolerance, and
        # stood white, in the known colour, wherever the sheet in front of it was open (2026-11-15)
        cut_far = nodes.new("GeometryNodeDeleteGeometry")
        cut_far.domain = "POINT"
        seen_geo = back_s.outputs["Geometry"]
        if held:
            # a tile of the last picture: a little nearer the eyes, as that picture's hits are (MEM_SHRINK), and rippling
            # with them (the one ripple at the same room point)
            pos_h = nodes.new("GeometryNodeInputPosition")
            near_h = nodes.new("GeometryNodeSetPosition")
            links.new(seen_geo, near_h.inputs["Geometry"])
            links.new(vmath("ADD", eye.outputs["Location"],
                            vmath("SCALE", vmath("SUBTRACT", pos_h.outputs["Position"], eye.outputs["Location"]), scale=MEM_SHRINK)),
                      near_h.inputs["Position"])
            links.new(off, near_h.inputs["Offset"])
            seen_geo = near_h.outputs["Geometry"]
        links.new(seen_geo, cut_far.inputs["Geometry"])
        links.new(math("LESS_THAN", own9, 0.5), cut_far.inputs["Selection"])
        g_s = store(cut_far.outputs["Geometry"], "scan_col", "FLOAT_COLOR", col_seen)
        g_s = store(g_s, "scan_uv", "FLOAT_VECTOR", uv_t)
        for nm_s in ("sense_s", "sense_clear", "coin", "heat"):
            g_s = store(g_s, nm_s, "FLOAT", 0.0)
        if held:
            # lit as the last picture is, by the eyes being shut, with the light its waves carry
            g_s = store(g_s, "heat", "FLOAT", heat_lvl)
            g_s = store(g_s, "mem_lit", "FLOAT", shut_v)
        if held:
            # a tile of the last picture gives way as the live picture comes to stand, as that picture's sheet does at
            # a place the eyes see (scan_nodes, SEEN_FADE; Stand, keyed: the live picture's standing). At its whole
            # cover until the last picture was gone, it stood on before the live picture, nearly unlit: black bands
            # on every crown's limb for a third of a second as his eyes opened (2026-11-16)
            stand_h = nodes.new("ShaderNodeMapRange")
            stand_h.interpolation_type = "SMOOTHSTEP"
            stand_h.inputs["From Min"].default_value = SEEN_FADE[0]
            stand_h.inputs["From Max"].default_value = SEEN_FADE[1]
            stand_h.inputs["To Min"].default_value = 0.0
            stand_h.inputs["To Max"].default_value = 1.0
            links.new(value("Stand", 0.0), stand_h.inputs["Value"])
            g_s = store(g_s, "gate", "FLOAT", math("SUBTRACT", 1.0, stand_h.outputs["Result"]))
        else:
            g_s = store(g_s, "gate", "FLOAT", 1.0)
        tile_s = nodes.new("GeometryNodeMeshGrid")
        tile_s.inputs["Size X"].default_value = 1.0
        tile_s.inputs["Size Y"].default_value = 1.0
        tile_s.inputs["Vertices X"].default_value = 2
        tile_s.inputs["Vertices Y"].default_value = 2
        tile_sm = nodes.new("GeometryNodeSetMaterial")
        tile_sm.inputs["Material"].default_value = seen_material
        links.new(store(tile_s.outputs["Mesh"], "chord", "FLOAT", 0.0), tile_sm.inputs["Geometry"])
        iop_s = nodes.new("GeometryNodeInstanceOnPoints")
        links.new(g_s, iop_s.inputs["Points"])
        links.new(tile_sm.outputs["Geometry"], iop_s.inputs["Instance"])
        links.new(dist.outputs["Rotation"], iop_s.inputs["Rotation"])
        links.new(size_t.outputs["Vector"], iop_s.inputs["Scale"])
        real_s = nodes.new("GeometryNodeRealizeInstances")
        links.new(iop_s.outputs["Instances"], real_s.inputs["Geometry"])
        # its front toward the eyes, as the sheet's faces are turned (scan_nodes): a tile lies as its face of the known
        # shape does, and a thing that is an open sheet the eyes see from its back (a wall of the room, the ceiling)
        # had its tiles' backs to the eyes. From the eyes' side the camera then saw the back of every such tile, which
        # is clear while the camera is near (BACK_CLEAR): those tiles never showed, and the end of the east wall from
        # the window stood as the ends of the picture's own rows, a row of notches (the audit's O2, 2026-11-16)
        nrm_s = nodes.new("GeometryNodeInputNormal")
        pos_f_s = nodes.new("GeometryNodeInputPosition")
        flip_s = nodes.new("GeometryNodeFlipFaces")
        links.new(real_s.outputs["Geometry"], flip_s.inputs["Mesh"])
        # (a flat-faced thing's alone: a round thing's tiles just past its outline, turned a little from the eyes,
        # keep the shape's own outward front, which is the side the camera sees them from. Turned as well, they
        # showed their clear backs and the open lamp shade's edge stood speckled, 2026-11-16)
        links.new(math("MULTIPLY", math("GREATER_THAN", vmath("DOT_PRODUCT", nrm_s.outputs["Normal"], vmath("SUBTRACT", pos_f_s.outputs["Position"], eye.outputs["Location"])), 0.0),
                       math("LESS_THAN", named("round", "FLOAT"), 0.5)),
                  flip_s.inputs["Selection"])
        both_t = nodes.new("GeometryNodeJoinGeometry")
        # (the live picture's tiles alone. A tile of the last picture ripples, and so does that picture's sheet, whose
        # vertices on a face seen nearly edge-on lie a hand's breadth apart: turned to the eyes and so seen from the
        # camera's side, the remembered wall's tiles stood through its sheet in streaks, a fan across the wall with
        # his eyes shut in the sun, 2026-11-16. Left as they lie, they do not show there, as before that day)
        links.new(lean(real_s.outputs["Geometry"] if held else flip_s.outputs["Mesh"]), both_t.inputs["Geometry"])
        links.new(drawn_t, both_t.inputs["Geometry"])
        drawn_t = both_t.outputs["Geometry"]
    # a layer that is not shown is not worked out at all (Visible, keyed: the last picture's twin while his eyes are open)
    shown_t = nodes.new("GeometryNodeSwitch")
    shown_t.input_type = "GEOMETRY"
    links.new(math("GREATER_THAN", visible, 0.01), _sock(shown_t.inputs, "Switch"))
    links.new(drawn_t, _sock(shown_t.inputs, "True"))
    links.new(_sock(shown_t.outputs, "Output"), go.inputs["Geometry"])
    return ng


def outline_material(name, fade):
    """The body senses' light (rung 2p), one layer OUTLINE_HALO outside the skin. Its light fades to nothing at the
    layer's own outline, which lies outside the body's, so no glow has an edge where the body ends (his word of
    2026-11-13: soft edges, glows). Two parts, both wavering:

    the outline sense (proprioception): a light added over the part in the sense's colour
    (out_col from the geometry) at its strength (out_s), a band along the part's outline: OUTLINE_GAIN where the layer
    faces the camera at the cosine OUTLINE_PEAK, falling to nothing at the layer's outline and where it faces the
    camera full on, so the part's middle stays clear;

    touch with its pain and pleasure (the same word: a glow, no matte colour): the glow's colour (glow_col) at
    GLOW_GAIN of light, covering what is behind it by its strength (glow_s, which falls with the contact, so the
    patch has a soft edge along the skin) times GLOW_ALPHA, whole from the cosine GLOW_EDGE and nothing at the layer's
    outline. Blended, so the edge is smooth and has no grain. Warmth and the cold air the same way (temp_col, temp_s),
    but only where their skin faces the camera; where a touch and they share a patch the stronger shows in its own
    colour (PAIR_BAND). And the flash of the part a spark comes from (flash_s), the spark's white added over the part.

    The waver (the same word: a shimmer, weaker than memory's, moving nothing, in the colour): a slow noise over the
    body in room metres (glow_p) and time (T, keyed with the scene's seconds) that brightens and dims the light by
    SENSE_SHIMMER and turns its colour by SENSE_SHIMMER_HUE. Senses (keyed 1, nought for the eye-point check) switches
    all of it off."""
    mat = bpy.data.materials.new(name)
    nt, out = mats._clear(mat)

    def attr(nm):
        n = nt.nodes.new("ShaderNodeAttribute")
        n.attribute_type = "GEOMETRY"
        n.attribute_name = nm
        return n

    def m(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs["Value"]

    col, s_, gcol, gs, gp = attr("out_col"), attr("out_s"), attr("glow_col"), attr("glow_s"), attr("glow_p")
    tcol, ts, fl = attr("temp_col"), attr("temp_s"), attr("flash_s")
    on = nt.nodes.new("ShaderNodeValue"); on.name = "Senses"; on.label = "Senses"
    on.outputs[0].default_value = 1.0
    tv = nt.nodes.new("ShaderNodeValue"); tv.name = "T"; tv.label = "T"
    tv.outputs[0].default_value = 0.0
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    facing = lw.outputs["Facing"]
    # the waver
    cells = nt.nodes.new("ShaderNodeVectorMath"); cells.operation = "SCALE"
    nt.links.new(gp.outputs["Vector"], cells.inputs[0])
    cells.inputs["Scale"].default_value = SENSE_SHIMMER_CELLS
    noise = nt.nodes.new("ShaderNodeTexNoise")
    noise.noise_dimensions = "4D"
    nt.links.new(cells.outputs["Vector"], noise.inputs["Vector"])
    nt.links.new(m("MULTIPLY", tv.outputs[0], SENSE_SHIMMER_SPEED), noise.inputs["W"])
    noise.inputs["Scale"].default_value = 1.0
    noise.inputs["Detail"].default_value = 1.0
    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(noise.outputs["Color"], sep.inputs["Color"])
    waver = m("MULTIPLY_ADD", noise.outputs["Fac"], 2.0 * SENSE_SHIMMER, 1.0 - SENSE_SHIMMER)
    turn = m("MULTIPLY_ADD", sep.outputs["Green"], 2.0 * SENSE_SHIMMER_HUE, 0.5 - SENSE_SHIMMER_HUE)

    def turned(colour_socket):
        hsv = nt.nodes.new("ShaderNodeHueSaturation")
        nt.links.new(turn, hsv.inputs["Hue"])
        nt.links.new(colour_socket, hsv.inputs["Color"])
        return hsv.outputs["Color"]

    # how squarely the layer faces the camera: nought at the layer's own outline, 1 where it faces the camera full on
    square = m("SUBTRACT", 1.0, facing)
    # the outline senses: a band of light along the part's outline, fading to nothing both ways
    band = m("MINIMUM", m("DIVIDE", square, OUTLINE_PEAK), m("DIVIDE", facing, 1.0 - OUTLINE_PEAK))
    rim = m("POWER", m("MAXIMUM", band, 0.0), OUTLINE_SOFT)
    e_rim = m("MULTIPLY", m("MULTIPLY", m("MULTIPLY", s_.outputs["Fac"], rim), on.outputs[0]), m("MULTIPLY", waver, OUTLINE_GAIN))
    em_rim = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(turned(col.outputs["Color"]), em_rim.inputs["Color"])
    nt.links.new(mats._fade_gain(nt, e_rim, fade, "Model"), em_rim.inputs["Strength"])
    # the glows that have a place on the skin. A touch lies between the body and the thing touched, so it is drawn
    # through the limb, as he passed it. Warmth and the cold air lie on open skin, and the body hides them where that
    # skin faces away from the camera (his word of 2026-11-13, eleventh round: the side that faces the sun, and not the
    # whole head: the simulated head is not drawn unless he thinks of it, so its far side showed through it)
    surf = m("POWER", m("MINIMUM", m("DIVIDE", square, GLOW_EDGE), 1.0), GLOW_SOFT)
    shown = m("MULTIPLY", surf, on.outputs[0])
    geo_n = nt.nodes.new("ShaderNodeNewGeometry")
    front = m("SUBTRACT", 1.0, geo_n.outputs["Backfacing"])
    c_touch = m("MULTIPLY", m("MULTIPLY", gs.outputs["Fac"], GLOW_ALPHA), shown)
    c_temp = m("MULTIPLY", m("MULTIPLY", m("MULTIPLY", ts.outputs["Fac"], GLOW_ALPHA), shown), front)
    # two senses on one patch: the stronger shows in its own colour (PAIR_BAND)
    lead = nt.nodes.new("ShaderNodeMapRange")
    lead.interpolation_type = "SMOOTHSTEP"
    lead.inputs["From Min"].default_value = -PAIR_BAND
    lead.inputs["From Max"].default_value = PAIR_BAND
    nt.links.new(m("DIVIDE", m("SUBTRACT", c_temp, c_touch), m("MAXIMUM", m("ADD", c_temp, c_touch), 1e-6)), lead.inputs["Value"])
    both = nt.nodes.new("ShaderNodeMix")
    both.data_type = "RGBA"
    nt.links.new(lead.outputs["Result"], both.inputs["Factor"])
    nt.links.new(gcol.outputs["Color"], both.inputs[6])
    nt.links.new(tcol.outputs["Color"], both.inputs[7])
    cover = m("MINIMUM", m("MAXIMUM", c_touch, c_temp), 1.0)
    em_glow = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(turned(both.outputs[2]), em_glow.inputs["Color"])
    nt.links.new(m("MULTIPLY", waver, GLOW_GAIN), em_glow.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    over = nt.nodes.new("ShaderNodeMixShader")
    nt.links.new(mats._fade_gain(nt, cover, fade, "Model"), over.inputs["Fac"])
    nt.links.new(tr.outputs["BSDF"], over.inputs[1])
    nt.links.new(em_glow.outputs["Emission"], over.inputs[2])
    # the flash of the part a spark comes from: the spark's white over the part's skin, for as long as the spark lives
    em_flash = nt.nodes.new("ShaderNodeEmission")
    em_flash.inputs["Color"].default_value = (*LIGHTNING_CORE_COLOUR, 1.0)
    nt.links.new(mats._fade_gain(nt, m("MULTIPLY", m("MULTIPLY", fl.outputs["Fac"], SPARK_FLASH_GAIN), shown), fade, "Model"), em_flash.inputs["Strength"])
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(over.outputs["Shader"], add.inputs[0])
    nt.links.new(em_rim.outputs["Emission"], add.inputs[1])
    add2 = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(add.outputs["Shader"], add2.inputs[0])
    nt.links.new(em_flash.outputs["Emission"], add2.inputs[1])
    nt.links.new(add2.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat.use_backface_culling = False
    mat.diffuse_color = (0.5, 1.0, 0.75, 0.5)
    return mat


def _set_mode(node, prop_value, socket_value):
    """A node's mode: its property where the node has one, else its menu socket (5.2's resample curve)."""
    try:
        node.mode = prop_value
    except AttributeError:
        node.inputs["Mode"].default_value = socket_value


from .touches import PAIR_REACH, PAIR_SAMPLE      # the reading's reach and its cut; the rule itself is touches.py


def strikes_of_pairs(begins, points=None):
    """The sparks, from the beginnings of every touch (LidarScene.read_pairs: second, part, the thing or part touched,
    how fast the gap closed). The touches of one limb that begin within STRIKE_SAME of the first of them send one spark:
    the hardest of them, from its own part at its own second (of touches as hard as each other, by STRIKE_TIE, the
    first, and the farthest part of one frame).
    (Until the thirteenth round's audit the first's part and second with the hardest's closing: the falling phone
    grazes his shin and lands on his foot two frames later, and the shin flashed at the foot's strength.) The head
    sends none: its skin is the skull the spark runs to. Returns (second, part, metres a second, the touched place),
    in order: the place is the point of the part's skin nearest what it touches, in the room at that second (points,
    from read_pairs; None where it is not known), where the spark starts (his word of 2026-11-16: from the point of
    contact, not a joint, and by a rule that holds for any figure)."""

    def rank(part):
        chain = tags.CHAINS[tags.PART_CHAIN[part]]
        return chain.index(tags.part_axis(part)[1])

    points = points or {}
    raw = sorted(((float(t), p, float(v), points.get((round(float(t), 4), p, o))) for t, p, o, v in begins
                  if p != "head" and p in tags.PART_CHAIN), key=lambda x: (x[0], rank(x[1])))
    groups, last = [], {}
    for hit in raw:
        limb = tags.PART_CHAIN[hit[1]]
        k = last.get(limb)
        if k is not None and hit[0] - groups[k][0][0] < STRIKE_SAME:
            groups[k].append(hit)
            continue
        last[limb] = len(groups)
        groups.append([hit])
    return sorted((max(g, key=lambda x: (int(x[2] / STRIKE_TIE), -x[0], -rank(x[1]))) for g in groups), key=lambda x: x[:3])


def strikes_of(level, gain, times, parts):
    """The moments a touch begins, from read_contact's reading: each time a body part's contact rises to STRIKE_ON after
    it has fallen to STRIKE_OFF (touched at the first frame, a part has not begun). Where several parts of one limb land
    within STRIKE_SAME, the farthest part's alone. The head sends none: its skin is the skull the spark runs to.
    Returns (second, part), in order. (gain, how fast new skin comes into contact, is kept in the reading and not used.)"""

    def rank(part):
        chain = tags.CHAINS[tags.PART_CHAIN[part]]
        point = tags.PART_POINT[part]
        return chain.index(point) if point in chain else len(chain)

    raw = []
    for i, part in enumerate(parts):
        if part == "head" or part not in tags.PART_CHAIN:
            continue
        touched = bool(level[0, i] >= STRIKE_ON)
        for k in range(1, len(times)):
            v = float(level[k, i])
            if not touched and v >= STRIKE_ON:
                raw.append((float(times[k]), part))
                touched = True
            elif touched and v <= STRIKE_OFF:
                touched = False
    raw.sort(key=lambda x: (x[0], rank(x[1])))
    out, last = [], {}
    for t, part in raw:
        limb = tags.PART_CHAIN[part]
        if t - last.get(limb, -1e9) < STRIKE_SAME:
            continue
        out.append((t, part))
        last[limb] = t
    return out


def lightning_nodes(name, material, cam_obj):
    """The touch's signal (rung 2p): a spark along a path of LIGHTNING_KNOTS points (keyed Value nodes K0X to K7Z, in
    the model: the joints up the limb and the skull, triview/engine.py), drawn from its first point up to Progress of
    its length. LIGHTNING_POINTS points along it, each thrown off the path across it by a random throw that changes with
    Seed (keyed to the frame the spark began at: one zigzag for its whole life; a new one every frame until the tenth
    round, and the spark read as a beam that writhed), a fine throw and a coarser one every fifth point, Jag in all (keyed:
    LIGHTNING_JAG at the model's scale) and nought at the two ends; every point carries lit, the spark's light there: 1
    at its front (Progress), falling behind it over LIGHTNING_TAIL of the path to LIGHTNING_TAIL_FLOOR, for
    bolt_material; two tubes round it, the white core of radius Width
    and the blue sheath LIGHTNING_HALO times as wide (halo 0 and 1, for bolt_material); every point then drawn Pull
    toward the rendering camera along its own line of sight, so the limb the spark runs inside does not hide it."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links
    math, vmath = _ops(nodes, links)

    def value(nm, v):
        n = nodes.new("ShaderNodeValue")
        n.name = nm
        n.label = nm
        n.outputs[0].default_value = v
        return n.outputs[0]

    go = nodes.new("NodeGroupOutput")
    progress = value("Progress", 0.0)
    width = value("Width", 0.001)
    seed = value("Seed", 0.0)
    jag_v = value("Jag", 0.0005)
    pull = value("Pull", 0.0)
    # the path: a line of LIGHTNING_KNOTS vertices, each set to its keyed point by its index; points keyed alike (a
    # short path repeats its last) are merged, and the edges become one curve
    knots = nodes.new("GeometryNodeMeshLine")
    knots.inputs["Count"].default_value = engine.LIGHTNING_KNOTS
    idx = nodes.new("GeometryNodeInputIndex")
    at = None
    for k in range(engine.LIGHTNING_KNOTS):
        pt = nodes.new("ShaderNodeCombineXYZ")
        for ax in "XYZ":
            links.new(value(f"K{k}{ax}", 0.0), pt.inputs[ax])
        part = vmath("SCALE", pt.outputs["Vector"], scale=math("COMPARE", idx.outputs["Index"], float(k), 0.5))
        at = part if at is None else vmath("ADD", at, part)
    place = nodes.new("GeometryNodeSetPosition")
    links.new(knots.outputs["Mesh"], place.inputs["Geometry"])
    links.new(at, place.inputs["Position"])
    merge = nodes.new("GeometryNodeMergeByDistance")
    links.new(place.outputs["Geometry"], merge.inputs["Geometry"])
    merge.inputs["Distance"].default_value = 1e-6
    curve = nodes.new("GeometryNodeMeshToCurve")
    links.new(merge.outputs["Geometry"], curve.inputs["Mesh"])
    res = nodes.new("GeometryNodeResampleCurve")
    _set_mode(res, "COUNT", "Count")
    links.new(curve.outputs["Curve"], res.inputs["Curve"])
    res.inputs["Count"].default_value = LIGHTNING_POINTS
    tan = nodes.new("GeometryNodeInputTangent")
    idx2 = nodes.new("GeometryNodeInputIndex")

    def throw(id_socket, seed_socket):
        rnd = nodes.new("FunctionNodeRandomValue")
        rnd.data_type = "FLOAT_VECTOR"
        rnd.inputs[0].default_value = (-1.0, -1.0, -1.0)
        rnd.inputs[1].default_value = (1.0, 1.0, 1.0)
        links.new(id_socket, rnd.inputs["ID"])
        links.new(seed_socket, rnd.inputs["Seed"])
        return rnd.outputs[0]

    fine = throw(idx2.outputs["Index"], seed)
    coarse = throw(math("FLOOR", math("DIVIDE", idx2.outputs["Index"], 5.0)), math("ADD", seed, 17.0))
    both = vmath("ADD", vmath("SCALE", fine, scale=0.9), coarse)
    axis = vmath("NORMALIZE", tan.outputs["Tangent"])
    across = vmath("SUBTRACT", both, vmath("SCALE", axis, scale=vmath("DOT_PRODUCT", both, axis)))
    par = nodes.new("GeometryNodeSplineParameter")
    taper = math("POWER", math("SINE", math("MULTIPLY", par.outputs["Factor"], 3.141592653589793)), 0.5)
    off = vmath("SCALE", across, scale=math("MULTIPLY", jag_v, taper))
    jag = nodes.new("GeometryNodeSetPosition")
    links.new(res.outputs["Curve"], jag.inputs["Geometry"])
    links.new(off, jag.inputs["Offset"])
    # the spark's light along it: full at its front, falling away behind it
    behind = math("SUBTRACT", math("MAXIMUM", progress, 0.001), par.outputs["Factor"])
    lit_v = math("MINIMUM", math("MAXIMUM", math("SUBTRACT", 1.0, math("DIVIDE", behind, LIGHTNING_TAIL)), LIGHTNING_TAIL_FLOOR), 1.0)
    lit = nodes.new("GeometryNodeStoreNamedAttribute")
    lit.data_type = "FLOAT"
    lit.domain = "POINT"
    lit.inputs["Name"].default_value = "lit"
    links.new(jag.outputs["Geometry"], lit.inputs["Geometry"])
    links.new(lit_v, lit.inputs["Value"])
    trim = nodes.new("GeometryNodeTrimCurve")
    trim.mode = "FACTOR"
    links.new(lit.outputs["Geometry"], trim.inputs["Curve"])
    trim.inputs[2].default_value = 0.0
    links.new(math("MAXIMUM", progress, 0.001), trim.inputs[3])
    rad = nodes.new("GeometryNodeSetCurveRadius")
    links.new(trim.outputs["Curve"], rad.inputs["Curve"])
    links.new(width, rad.inputs["Radius"])
    circle = nodes.new("GeometryNodeCurvePrimitiveCircle")
    circle.mode = "RADIUS"
    circle.inputs["Resolution"].default_value = 10
    circle.inputs["Radius"].default_value = 1.0
    # the profile scaled by the width through the node's own Scale (5.2 no longer reads the curve's radius for it: the
    # tube came out a metre wide, 2026-11-12); the white core, and round it the blue sheath (halo 1, for the material)
    tube = nodes.new("GeometryNodeJoinGeometry")
    for halo_v, scale_socket in ((0.0, width), (1.0, math("MULTIPLY", width, LIGHTNING_HALO))):
        tube_k = nodes.new("GeometryNodeCurveToMesh")
        links.new(rad.outputs["Curve"], tube_k.inputs["Curve"])
        links.new(circle.outputs["Curve"], tube_k.inputs["Profile Curve"])
        links.new(scale_socket, tube_k.inputs["Scale"])
        tube_k.inputs["Fill Caps"].default_value = True
        mark = nodes.new("GeometryNodeStoreNamedAttribute")
        mark.data_type = "FLOAT"
        mark.domain = "POINT"
        mark.inputs["Name"].default_value = "halo"
        mark.inputs["Value"].default_value = halo_v
        links.new(tube_k.outputs["Mesh"], mark.inputs["Geometry"])
        links.new(mark.outputs["Geometry"], tube.inputs["Geometry"])
    # toward the rendering camera along each point's own line of sight
    cam = nodes.new("GeometryNodeObjectInfo")
    cam.transform_space = "ORIGINAL"
    cam.inputs["Object"].default_value = cam_obj
    pos = nodes.new("GeometryNodeInputPosition")
    to_cam = vmath("NORMALIZE", vmath("SUBTRACT", cam.outputs["Location"], pos.outputs["Position"]))
    near = nodes.new("GeometryNodeSetPosition")
    links.new(tube.outputs["Geometry"], near.inputs["Geometry"])
    links.new(vmath("SCALE", to_cam, scale=pull), near.inputs["Offset"])
    setm = nodes.new("GeometryNodeSetMaterial")
    setm.inputs["Material"].default_value = material
    links.new(near.outputs["Geometry"], setm.inputs["Geometry"])
    links.new(setm.outputs["Geometry"], go.inputs["Geometry"])
    return ng


def bolt_material(name, group, fade):
    """The spark's light (2026-11-13): a white core (halo 0 from the geometry) at LIGHTNING_GAIN and round it a blue
    sheath (halo 1) at LIGHTNING_HALO_SHARE of that, brightest along its middle and fading to nothing at its own edge;
    added light, as bright as the signal is strong (att, the object's property) and as the spark is lit at the point
    (lit, from the geometry: full at its front, less behind it), clipped to the glass skull."""
    mat = bpy.data.materials.new(name)
    nt, out = mats._clear(mat)
    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_type = "OBJECT"; att.attribute_name = "att"
    halo = nt.nodes.new("ShaderNodeAttribute"); halo.attribute_type = "GEOMETRY"; halo.attribute_name = "halo"
    grp = nt.nodes.new("ShaderNodeGroup"); grp.node_tree = group
    lw = nt.nodes.new("ShaderNodeLayerWeight")
    lw.inputs["Blend"].default_value = 0.5
    inner = nt.nodes.new("ShaderNodeMath"); inner.operation = "SUBTRACT"
    inner.inputs[0].default_value = 1.0
    nt.links.new(lw.outputs["Facing"], inner.inputs[1])
    soft = nt.nodes.new("ShaderNodeMath"); soft.operation = "POWER"
    nt.links.new(inner.outputs["Value"], soft.inputs[0])
    soft.inputs[1].default_value = LIGHTNING_HALO_SOFT
    sheath = nt.nodes.new("ShaderNodeMath"); sheath.operation = "MULTIPLY"
    nt.links.new(soft.outputs["Value"], sheath.inputs[0])
    sheath.inputs[1].default_value = LIGHTNING_HALO_SHARE
    level = nt.nodes.new("ShaderNodeMix"); level.data_type = "FLOAT"
    nt.links.new(halo.outputs["Fac"], level.inputs["Factor"])
    level.inputs[2].default_value = 1.0
    nt.links.new(sheath.outputs["Value"], level.inputs[3])
    colour = nt.nodes.new("ShaderNodeMix"); colour.data_type = "RGBA"
    nt.links.new(halo.outputs["Fac"], colour.inputs["Factor"])
    colour.inputs[6].default_value = (*LIGHTNING_CORE_COLOUR, 1.0)
    colour.inputs[7].default_value = (*LIGHTNING_HALO_COLOUR, 1.0)
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    nt.links.new(att.outputs["Fac"], m1.inputs[0])
    nt.links.new(level.outputs[0], m1.inputs[1])
    lit = nt.nodes.new("ShaderNodeAttribute"); lit.attribute_type = "GEOMETRY"; lit.attribute_name = "lit"
    m1b = nt.nodes.new("ShaderNodeMath"); m1b.operation = "MULTIPLY"
    nt.links.new(m1.outputs["Value"], m1b.inputs[0])
    nt.links.new(lit.outputs["Fac"], m1b.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
    nt.links.new(m1b.outputs["Value"], m2.inputs[0])
    nt.links.new(grp.outputs["Clip"], m2.inputs[1])
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"
    nt.links.new(m2.outputs["Value"], m3.inputs[0])
    m3.inputs[1].default_value = LIGHTNING_GAIN
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(colour.outputs[2], em.inputs["Color"])
    nt.links.new(mats._fade_gain(nt, m3.outputs["Value"], fade, "Model"), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs["BSDF"], add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat.use_backface_culling = False
    mat.diffuse_color = (0.6, 0.8, 1.0, 0.8)
    return mat


def ring_material(name, group, fade):
    """The sounds' rings (rung 2p): a light in the ring's colour (col, the object's property) at its brightness (att: the
    sound's loudness, as far as it is attended and he is aware), glowing from a bright line at the ring's outer edge
    softly inward over the ring's band (rim from the geometry, 1 at the outer edge and 0 at the inner), as a radar's
    sweep trails; clipped to the glass skull by the model group's Clip."""
    mat = bpy.data.materials.new(name)
    nt, out = mats._clear(mat)
    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_type = "OBJECT"; att.attribute_name = "att"
    col = nt.nodes.new("ShaderNodeAttribute"); col.attribute_type = "OBJECT"; col.attribute_name = "col"
    rim = nt.nodes.new("ShaderNodeAttribute"); rim.attribute_type = "GEOMETRY"; rim.attribute_name = "rim"
    grp = nt.nodes.new("ShaderNodeGroup"); grp.node_tree = group
    soft = nt.nodes.new("ShaderNodeMath"); soft.operation = "POWER"
    nt.links.new(rim.outputs["Fac"], soft.inputs[0])
    soft.inputs[1].default_value = 3.0
    edge = nt.nodes.new("ShaderNodeMapRange"); edge.interpolation_type = "SMOOTHSTEP"
    edge.inputs["From Min"].default_value = RING_EDGE; edge.inputs["From Max"].default_value = 1.0
    edge.inputs["To Min"].default_value = 0.0; edge.inputs["To Max"].default_value = 1.0
    nt.links.new(rim.outputs["Fac"], edge.inputs["Value"])
    glow = nt.nodes.new("ShaderNodeMath"); glow.operation = "MULTIPLY_ADD"
    nt.links.new(soft.outputs["Value"], glow.inputs[0])
    glow.inputs[1].default_value = RING_SOFT
    nt.links.new(edge.outputs["Result"], glow.inputs[2])
    m1 = nt.nodes.new("ShaderNodeMath"); m1.operation = "MULTIPLY"
    nt.links.new(att.outputs["Fac"], m1.inputs[0])
    nt.links.new(glow.outputs["Value"], m1.inputs[1])
    m2 = nt.nodes.new("ShaderNodeMath"); m2.operation = "MULTIPLY"
    nt.links.new(m1.outputs["Value"], m2.inputs[0])
    nt.links.new(grp.outputs["Clip"], m2.inputs[1])
    m3 = nt.nodes.new("ShaderNodeMath"); m3.operation = "MULTIPLY"
    nt.links.new(m2.outputs["Value"], m3.inputs[0])
    m3.inputs[1].default_value = RING_GAIN
    em = nt.nodes.new("ShaderNodeEmission")
    nt.links.new(col.outputs["Color"], em.inputs["Color"])
    nt.links.new(mats._fade_gain(nt, m3.outputs["Value"], fade, "Model"), em.inputs["Strength"])
    tr = nt.nodes.new("ShaderNodeBsdfTransparent")
    add = nt.nodes.new("ShaderNodeAddShader")
    nt.links.new(tr.outputs["BSDF"], add.inputs[0])
    nt.links.new(em.outputs["Emission"], add.inputs[1])
    nt.links.new(add.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "BLENDED"
    mat.use_transparency_overlap = True
    mat.use_backface_culling = False
    mat.diffuse_color = (0.25, 1.0, 0.35, 0.6)
    return mat


def _arrow(name, mat, col):
    """A unit arrow along +Y, its tail at the origin: a flat arrow given depth (his word of 2026-11-13, twelfth round:
    like a rectangular prism with an arrow's point, an extruded 2D arrow, not a revolved one). A shaft of half-width 1
    from 0 to 0.62 and a head of half-width 3 from 0.62 to the point at 1, ARROW_DEPTH either side of its own XY
    plane, cut along its length so the ripple (arrow_ripple_nodes) bends it smoothly. Scaled by (half-width, length,
    half-width) and turned about its own length each frame (LidarScene.bake)."""
    import bmesh
    bm = geo.new_bmesh()
    d = ARROW_DEPTH

    def ring(y, hw):
        return [bm.verts.new(c) for c in ((-hw, y, -d), (hw, y, -d), (hw, y, d), (-hw, y, d))]

    head_cuts = max(ARROW_CUTS // 2, 2)
    rings = [ring(0.62 * i / ARROW_CUTS, 1.0) for i in range(ARROW_CUTS + 1)]
    rings += [ring(0.62 + 0.38 * j / head_cuts, 3.0 * (1.0 - j / head_cuts)) for j in range(head_cuts + 1)]
    bm.faces.new(rings[0][::-1])
    for a, b in zip(rings, rings[1:]):
        for k in range(4):
            quad = (a[k], a[(k + 1) % 4], b[(k + 1) % 4], b[k])
            p = [v.co for v in quad]
            area = ((p[1] - p[0]).cross(p[2] - p[0])).length + ((p[2] - p[0]).cross(p[3] - p[0])).length
            if area > 1e-9:       # none where the four corners lie on one line (the head's back, above and below the shaft)
                bm.faces.new(quad)
    bmesh.ops.remove_doubles(bm, verts=list(bm.verts), dist=1e-7)
    bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces))
    return geo.finish(bm, name, [mat], col)


ARROW_PHASE_PATH = 'nodes["Phase"].outputs[0].default_value'


def arrow_ripple_nodes(name):
    """The gravity arrow's ripple: crests that run along it from its tail to its point (Phase, keyed: ARROW_PULSE times
    the scene's seconds). At a crest the arrow is ARROW_RIPPLE wider and deeper; ARROW_RIPPLE_WAVES crests stand
    along it. Its shape changes, its colour does not."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links
    math, vmath = _ops(nodes, links)
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")
    phase = nodes.new("ShaderNodeValue")
    phase.name = "Phase"
    phase.label = "Phase"
    phase.outputs[0].default_value = 0.0
    pos = nodes.new("GeometryNodeInputPosition")
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos.outputs["Position"], sep.inputs[0])
    arg = math("MULTIPLY", math("SUBTRACT", math("MULTIPLY", sep.outputs["Y"], ARROW_RIPPLE_WAVES), phase.outputs[0]), 6.283185307179586)
    crest = math("POWER", math("MULTIPLY_ADD", math("COSINE", arg), 0.5, 0.5), 2.0)
    wide = math("MULTIPLY_ADD", crest, ARROW_RIPPLE, 1.0)
    out = nodes.new("ShaderNodeCombineXYZ")
    links.new(math("MULTIPLY", sep.outputs["X"], wide), out.inputs["X"])
    links.new(sep.outputs["Y"], out.inputs["Y"])
    links.new(math("MULTIPLY", sep.outputs["Z"], wide), out.inputs["Z"])
    setp = nodes.new("GeometryNodeSetPosition")
    links.new(gi.outputs[0], setp.inputs["Geometry"])
    links.new(out.outputs["Vector"], setp.inputs["Position"])
    links.new(setp.outputs["Geometry"], go.inputs[0])
    return ng


def arrow_material(name, fade):
    """The gravity arrow's surface (his word of 2026-11-13, twelfth round: it seemed see-through, which is wrong). A
    solid thing: opaque, in its own colour as a light, so the mind's dark does not hide it, and shaded as a solid is,
    each face from ARROW_SHADE of its light to all of it by how it stands to a light held above and beside the camera.
    Its light by the attention on balance (att, the object's property): ARROW_LOW to ARROW_HIGH. Under a reveal's fade
    it thins out with the rest of the model."""
    mat = bpy.data.materials.new(name)
    nt, out = mats._clear(mat)

    def m(op, a, b=None, c=None):
        n = nt.nodes.new("ShaderNodeMath")
        n.operation = op
        for i, v in enumerate((a, b, c)):
            if v is None:
                continue
            if isinstance(v, (int, float)):
                n.inputs[i].default_value = float(v)
            else:
                nt.links.new(v, n.inputs[i])
        return n.outputs["Value"]

    att = nt.nodes.new("ShaderNodeAttribute"); att.attribute_type = "OBJECT"; att.attribute_name = "att"
    geo_n = nt.nodes.new("ShaderNodeNewGeometry")
    # the light's way: toward the camera from the face, lifted and a little to one side, in the room's own frame
    lift = nt.nodes.new("ShaderNodeVectorMath"); lift.operation = "ADD"
    nt.links.new(geo_n.outputs["Incoming"], lift.inputs[0])
    lift.inputs[1].default_value = (0.25, -0.2, 0.6)
    way = nt.nodes.new("ShaderNodeVectorMath"); way.operation = "NORMALIZE"
    nt.links.new(lift.outputs["Vector"], way.inputs[0])
    dot = nt.nodes.new("ShaderNodeVectorMath"); dot.operation = "DOT_PRODUCT"
    nt.links.new(geo_n.outputs["Normal"], dot.inputs[0])
    nt.links.new(way.outputs["Vector"], dot.inputs[1])
    shade = m("MULTIPLY_ADD", m("MAXIMUM", dot.outputs["Value"], 0.0), 1.0 - ARROW_SHADE, ARROW_SHADE)
    level = m("MULTIPLY_ADD", m("MINIMUM", m("MAXIMUM", att.outputs["Fac"], 0.0), 1.0), ARROW_HIGH - ARROW_LOW, ARROW_LOW)
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (*mats.VIOLET, 1.0)
    nt.links.new(m("MULTIPLY", shade, level), em.inputs["Strength"])
    if fade is None:
        nt.links.new(em.outputs["Emission"], out.inputs["Surface"])
    else:
        one = nt.nodes.new("ShaderNodeValue")
        one.outputs[0].default_value = 1.0
        tr = nt.nodes.new("ShaderNodeBsdfTransparent")
        mix = nt.nodes.new("ShaderNodeMixShader")
        nt.links.new(mats._fade_gain(nt, one.outputs[0], fade, "Model"), mix.inputs["Fac"])
        nt.links.new(tr.outputs["BSDF"], mix.inputs[1])
        nt.links.new(em.outputs["Emission"], mix.inputs[2])
        nt.links.new(mix.outputs["Shader"], out.inputs["Surface"])
    mat.surface_render_method = "DITHERED"
    mat.use_backface_culling = False
    mat.diffuse_color = (*mats.VIOLET, 1.0)
    return mat


def _end_mark(name, mat, col, toward, segments=48):
    """The balance arrow seen from its end (ARROW_END), a flat mark of unit radius in its own XY plane, kept facing the
    camera by a constraint: a ring, and inside it a point (toward: the arrow comes at the camera, its tip) or a cross
    (it goes away, its feathers)."""
    bm = geo.new_bmesh()
    turns = [2.0 * math.pi * i / segments for i in range(segments)]
    outer = [bm.verts.new((math.cos(a), math.sin(a), 0.0)) for a in turns]
    inner = [bm.verts.new((0.8 * math.cos(a), 0.8 * math.sin(a), 0.0)) for a in turns]
    for i in range(segments):
        j = (i + 1) % segments
        bm.faces.new((outer[i], outer[j], inner[j], inner[i]))
    if toward:
        bm.faces.new([bm.verts.new((0.3 * math.cos(a), 0.3 * math.sin(a), 0.0)) for a in turns[::2]])
    else:
        # one outline for the two bars, so their crossing is drawn once
        ln, w = 0.62, 0.1
        plus = ((w, w), (ln, w), (ln, -w), (w, -w), (w, -ln), (-w, -ln), (-w, -w), (-ln, -w), (-ln, w), (-w, w), (-w, ln), (w, ln))
        c = s_ = math.sqrt(0.5)
        bm.faces.new([bm.verts.new((x * c - y * s_, x * s_ + y * c, 0.0)) for x, y in plus])
    return geo.finish(bm, name, [mat], col)


def senses_off(scene):
    """The senses hidden for the eye-point check (rung 2p): every Senses switch off and the senses' own objects hidden,
    so the model from the eyes is the picture alone; returns what was hidden."""
    hidden = []
    for ng in bpy.data.node_groups:
        n = ng.nodes.get("Senses")
        if n is not None:
            n.outputs[0].default_value = 0.0
    for mat in bpy.data.materials:
        if mat.node_tree is not None:
            n = mat.node_tree.nodes.get("Senses")
            if n is not None:
                n.outputs[0].default_value = 0.0
    for ob in scene.objects:
        if ob.name == "Outline" or ob.name.startswith(("GravityArrow", "Lightning_")):
            ob.hide_render = True
            hidden.append(ob.name)
    return hidden


def sun_heat_nodes(name, eye_obj=None, fov_deg=200.0):
    """The sun's remembered part ripples as every memory does (his word of 2026-11-15: "I still don't see the sun or room
    shimmering in the same way"; until then it wavered by a twentieth of its radius, 0.15 degrees from the eyes, where
    every other memory has HEAT_AMP_DEG). The one ripple, as a thing held whole takes it (HEAT_HELD): the ball is
    SUN_BALL_DEG wide from the eyes, so in its own coordinates (a ball of radius 1, its z along the eyes' line, its y
    the way up) the amplitude is HEAT_AMP_DEG over its half width, and the wave's cells are HEAT_WAVE_DEG tall and
    HEAT_ASPECT times as wide over the same. The ripple runs across the eyes' line, as every memory's does. The half
    toward the eyes holds still as far as the sun is seen (Seen, keyed: its share in sight while the live picture
    stands); with his eyes shut, or the sun out of sight, the whole ball is a memory and the whole ball ripples.
    (Measured 2026-11-16, scratchpad v16_round.py: from the eyes its outline is as round as a remembered bush's.)
    For the material, as every memory's tile carries them (the audit of 2026-11-15): heat, the wave's own level at the
    point against its level at the ball's centre (-0.5 to 0.5: the light the wave carries); scan_uv, the point's place
    in the eyes' picture, and in_field, whether that lies in their field (the lids' wipe), from eye_obj."""
    ng = bpy.data.node_groups.new(name, "GeometryNodeTree")
    ng.interface.new_socket("Geometry", in_out="INPUT", socket_type="NodeSocketGeometry")
    ng.interface.new_socket("Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry")
    nodes, links = ng.nodes, ng.links
    math, vmath = _ops(nodes, links)
    gi = nodes.new("NodeGroupInput")
    go = nodes.new("NodeGroupOutput")
    pos = nodes.new("GeometryNodeInputPosition")
    tm = nodes.new("GeometryNodeInputSceneTime")
    seen = nodes.new("ShaderNodeValue")
    seen.name = "Seen"
    seen.label = "Seen"
    seen.outputs[0].default_value = 0.0
    half = SUN_BALL_DEG / 2.0
    k_y = half / HEAT_WAVE_DEG
    # its own place in the pattern and its own time, as a thing held whole has by its index (the sun has no row in the
    # table of things: a number of its own)
    shift = (SUN_STAGGER * HEAT_STAGGER[0], SUN_STAGGER * HEAT_STAGGER[1], SUN_STAGGER * HEAT_STAGGER[2])
    clock = math("MULTIPLY_ADD", tm.outputs["Seconds"], HEAT_SPEED, SUN_STAGGER * HEAT_STAGGER[3])

    def wave(vec):
        noise = nodes.new("ShaderNodeTexNoise")
        noise.noise_dimensions = "4D"
        if isinstance(vec, tuple):
            noise.inputs["Vector"].default_value = vec
        else:
            links.new(vec, noise.inputs["Vector"])
        links.new(clock, noise.inputs["W"])
        noise.inputs["Scale"].default_value = 1.0
        noise.inputs["Detail"].default_value = 1.5
        noise.inputs["Roughness"].default_value = 0.5
        return noise.outputs["Fac"], noise.outputs["Color"]

    def store(geom, nm, dtype, val):
        st = nodes.new("GeometryNodeStoreNamedAttribute")
        st.data_type = dtype
        st.domain = "POINT"
        st.inputs["Name"].default_value = nm
        links.new(geom, st.inputs["Geometry"])
        if isinstance(val, (int, float)):
            _sock(st.inputs, "Value").default_value = float(val)
        else:
            links.new(val, _sock(st.inputs, "Value"))
        return st.outputs["Geometry"]

    here_lvl, here_col = wave(vmath("ADD", vmath("MULTIPLY", pos.outputs["Position"], (k_y / HEAT_ASPECT, k_y, 0.0)), shift))
    mid_lvl, mid_col = wave(shift) if HEAT_HELD != "own" else (0.5, (0.5, 0.5, 0.5))
    read = vmath("SUBTRACT", here_col, mid_col)
    # across the eyes' line alone (the ball's own z), by the amplitude in the ball's own radii
    off = vmath("MULTIPLY", vmath("SCALE", read, scale=2.0 * HEAT_ACROSS * HEAT_AMP_DEG / half), (1.0, 1.0, 0.0))
    if HEAT_BEND:
        # a thing held whole keeps its shape (HEAT_BEND; the ball's radius is 1 in its own coordinates)
        q_b = math("DIVIDE", vmath("LENGTH", off), HEAT_BEND)
        off = vmath("SCALE", off, scale=math("POWER", math("ADD", 1.0, math("POWER", q_b, 4.0)), -0.25))
    sep = nodes.new("ShaderNodeSeparateXYZ")
    links.new(pos.outputs["Position"], sep.inputs["Vector"])
    far = nodes.new("ShaderNodeMapRange")
    far.interpolation_type = "SMOOTHSTEP"
    far.inputs["From Min"].default_value = 0.0
    far.inputs["From Max"].default_value = 0.3
    far.inputs["To Min"].default_value = 0.0
    far.inputs["To Max"].default_value = 1.0
    links.new(sep.outputs["Z"], far.inputs["Value"])
    weight = math("MAXIMUM", far.outputs["Result"], math("SUBTRACT", 1.0, seen.outputs[0]))
    # what the material reads, stored before the ripple moves the points
    geom = store(gi.outputs["Geometry"], "heat", "FLOAT", math("MULTIPLY", math("SUBTRACT", here_lvl, mid_lvl), weight))
    if eye_obj is not None:
        # the point's place in the eyes' picture, as the scan lays it (uv = 0.5 + theta / fov along the azimuth), and
        # whether it lies inside their field: the same reading a known shape's tile has (shape_nodes)
        own = nodes.new("GeometryNodeSelfObject")
        own_info = nodes.new("GeometryNodeObjectInfo")
        own_info.transform_space = "ORIGINAL"
        links.new(own.outputs["Self Object"], own_info.inputs["Object"])
        world = nodes.new("FunctionNodeTransformPoint")
        links.new(pos.outputs["Position"], world.inputs["Vector"])
        links.new(own_info.outputs["Transform"], world.inputs["Transform"])
        eye = nodes.new("GeometryNodeObjectInfo")
        eye.transform_space = "ORIGINAL"
        eye.inputs["Object"].default_value = eye_obj
        ray = vmath("NORMALIZE", vmath("SUBTRACT", world.outputs["Vector"], eye.outputs["Location"]))
        inv_e = nodes.new("FunctionNodeInvertMatrix")
        links.new(eye.outputs["Transform"], inv_e.inputs["Matrix"])
        to_e = nodes.new("FunctionNodeTransformDirection")
        links.new(ray, to_e.inputs["Direction"])
        links.new(inv_e.outputs["Matrix"], to_e.inputs["Transform"])
        sep_e = nodes.new("ShaderNodeSeparateXYZ")
        links.new(vmath("NORMALIZE", to_e.outputs["Direction"]), sep_e.inputs["Vector"])
        theta = math("ARCCOSINE", math("MINIMUM", math("MAXIMUM", math("MULTIPLY", sep_e.outputs["Z"], -1.0), -1.0), 1.0))
        phi = math("ARCTAN2", sep_e.outputs["Y"], sep_e.outputs["X"])
        fov_rad = fov_deg * 3.141592653589793 / 180.0
        rr = math("DIVIDE", theta, fov_rad)
        uv_now = nodes.new("ShaderNodeCombineXYZ")
        links.new(math("MULTIPLY_ADD", rr, math("COSINE", phi), 0.5), uv_now.inputs["X"])
        links.new(math("MULTIPLY_ADD", rr, math("SINE", phi), 0.5), uv_now.inputs["Y"])
        cen_now = vmath("SUBTRACT", uv_now.outputs["Vector"], (0.5, 0.5, 0.0))
        ell_now = vmath("LENGTH", vmath("MULTIPLY", cen_now, (2.0 * fov_deg / FIELD_H, 2.0 * fov_deg / FIELD_V, 0.0)))
        within = math("MULTIPLY", math("LESS_THAN", theta, fov_rad * 0.49), math("LESS_THAN", ell_now, 0.995))
        geom = store(geom, "scan_uv", "FLOAT_VECTOR", uv_now.outputs["Vector"])
        geom = store(geom, "in_field", "FLOAT", within)
    setp = nodes.new("GeometryNodeSetPosition")
    links.new(geom, setp.inputs["Geometry"])
    links.new(vmath("SCALE", off, scale=weight), setp.inputs["Offset"])
    links.new(setp.outputs["Geometry"], go.inputs["Geometry"])
    return ng


class LidarScene:
    def __init__(self, name, room_spec, fps=24, eevee_samples=32, bloom=True, scan_dir=None, frame_count=1,
                 placeholder_dir=None, scan_size=640, fov_deg=FOV_DEG, things=None, render_fps=None, **_ignored):
        self.spec = room_spec
        self.fps = fps                      # frames per chain second: the ages and the keys count in the chain's seconds
        self.scan_size = (int(scan_size), int(scan_size))
        self.fov_deg = float(fov_deg)
        scan_dir = pathlib.Path(scan_dir) if scan_dir is not None else None
        placeholder_dir = pathlib.Path(placeholder_dir) if placeholder_dir is not None else (scan_dir.parent / "placeholder")
        scene = bpy.data.scenes.new(name)
        self.scene = scene
        scene.render.fps = int(round(render_fps or fps))
        col = scene.collection
        self.col = col
        scene.world = mats.black_world("Dark")
        render.setup_eevee(scene, samples=eevee_samples)
        self.fade = mats.fade_group()
        fd = self.fade
        # the scan's two sequences, and the backdrop scan's (the sky, the ground and the range with
        # the near things hidden, at half the scan's size)
        self.pos_img = sequence("ScanPos", scan_dir, "pos_*.exr", _placeholder_exr, placeholder_dir, "Non-Color")
        self.col_img = sequence("ScanColour", scan_dir, "frame_*.png", _placeholder_png, placeholder_dir, "sRGB")
        # the index pictures: every hit's thing, written by the scan's index pass beside its position
        self.idx_img = sequence("ScanIdx", scan_dir, "idx_*.exr", _placeholder_exr, placeholder_dir, "Non-Color")
        back_dir = scan_dir.parent / "backdrop" if scan_dir is not None else None
        self.back_pos = sequence("BackPos", back_dir, "pos_*.exr", _placeholder_exr, placeholder_dir / "backdrop", "Non-Color")
        self.back_col = sequence("BackColour", back_dir, "frame_*.png", _placeholder_png, placeholder_dir / "backdrop", "sRGB")
        self.back_idx = sequence("BackIdx", back_dir, "idx_*.exr", _placeholder_exr, placeholder_dir / "backdrop", "Non-Color")
        self.back_size = (int(round(self.scan_size[0] * BACKDROP_SHARE)), int(round(self.scan_size[1] * BACKDROP_SHARE)))
        # and the sky scan's (the sky's shell alone, the same size as the backdrop's)
        sky_dir = scan_dir.parent / "sky" if scan_dir is not None else None
        self.sky_pos = sequence("SkyPos", sky_dir, "pos_*.exr", _placeholder_exr, placeholder_dir / "sky", "Non-Color")
        self.sky_col = sequence("SkyColour", sky_dir, "frame_*.png", _placeholder_png, placeholder_dir / "sky", "sRGB")
        self.sky_idx = sequence("SkyIdx", sky_dir, "idx_*.exr", _placeholder_exr, placeholder_dir / "sky", "Non-Color")
        # the peel scan's two pictures (rung 2l): the same rays carried on through the first thing they
        # strike to where they leave it, position and index alone; a far hit's colour is its ray's own
        peel_dir = scan_dir.parent / "peel" if scan_dir is not None else None
        self.peel_pos = sequence("PeelPos", peel_dir, "pos_*.exr", _placeholder_exr, placeholder_dir / "peel", "Non-Color")
        self.peel_idx = sequence("PeelIdx", peel_dir, "idx_*.exr", _placeholder_exr, placeholder_dir / "peel", "Non-Color")
        # the pane scan's three pictures (rung 2o): the window's glass alone, reflecting the scene, for the glass layer
        pane_dir = scan_dir.parent / "pane" if scan_dir is not None else None
        self.pane_pos = sequence("PanePos", pane_dir, "pos_*.exr", _placeholder_exr, placeholder_dir / "pane", "Non-Color")
        self.pane_col = sequence("PaneColour", pane_dir, "frame_*.png", _placeholder_png, placeholder_dir / "pane", "sRGB")
        self.pane_idx = sequence("PaneIdx", pane_dir, "idx_*.exr", _placeholder_exr, placeholder_dir / "pane", "Non-Color")
        # the table of things: one vertex per thing of the room, its row as attributes (centre, radius,
        # region, part), which every surface's geometry reads for each hit by the index the scan gives it; and
        # the rows themselves, for the bake (when each thing was in sight)
        self.things = list(things) if things else []
        self.table = self._thing_table(self.things)
        self.table["room_size"] = [float(v) for v in self.spec.size]   # for the known light's measure at render time
        # the sense table (rung 2p): a picture with a row per frame and a column per part and field, which the
        # surfaces sample for the sense on a hit's part this frame; blank until the bake writes it
        self.n_frames = int(frame_count)
        self.sense_path = (scan_dir.parent if scan_dir is not None else pathlib.Path(placeholder_dir)) / "senses.exr"
        self.sense_img = bpy.data.images.load(str(_blank_exr(self.sense_path, SENSE_FIELDS * len(tags.SENSE_PARTS), self.n_frames)), check_existing=False)
        self.sense_img.name = "SenseTable"
        self.sense_img.colorspace_settings.name = "Non-Color"
        self.torso = bpy.data.objects.get("Man_torso")
        # where the body is touched (rung 2p): ContactBody, read by every surface a sense lights
        self.contact, self.contact_levels = self._contact_body()
        # camera on its road, tracking an aim empty; the near clip is half a millimetre: at two
        # centimetres the splats a move's camera backed away from popped into view, and the material's
        # near fade handles what is closer than that
        self.cam = geo.add_camera("Cam_True", (4.0, 0.0, 1.15), (0.0, 0.0, 1.05), lens=24.0, clip_start=0.0005, collection=col)
        self.aim = geo.add_empty("Cam_True_Aim", (0.0, 0.0, 1.05), 1.0, col)
        self.track = geo.track_to(self.cam, self.aim, "TRACK_NEGATIVE_Z", "UP_Y")
        self.cam.rotation_mode = "QUATERNION"
        scene.camera = self.cam
        # the simulated eyes, for the check from inside the skull
        self.sim_eye_cam = geo.add_camera("Cam_SimEye", (0.0, 0.0, 1.63), (1.0, 0.0, 1.63), lens=cameras.FIRST_LENS, clip_start=0.001, collection=col)
        self.sim_eye_cam.rotation_mode = "QUATERNION"
        # the glass skull alone: the body and its glyphs are left out, to expose the vision part
        self.glass = mats.ghost_glass("GhostGlass", edge_strength=0.45, fill=0.01, power=3.5, fade=self.fade)
        pose = figure.standing()
        place = figure.placement((0.0, 0.0, 0.0), 0.0)
        body, self.ghost_head, _ = figure.build("Ghost", pose, {"skin": self.glass, "cloth": self.glass}, place, col, segments=24)
        self.m_body = None
        if GHOST_BODY:
            # the body in a glass of its own, the head's with a BodyShow value over how much of it shows (keyed)
            self.ghost_body = body
            self.m_body = mats.ghost_glass("GhostBodyGlass", edge_strength=0.45, fill=0.01, power=3.5, fade=self.fade)
            nt = self.m_body.node_tree
            mix = next(n for n in nt.nodes if n.bl_idname == "ShaderNodeMixShader")
            src = mix.inputs["Fac"].links[0].from_socket
            nt.links.remove(mix.inputs["Fac"].links[0])
            show = nt.nodes.new("ShaderNodeValue")
            show.name = "BodyShow"
            show.label = "BodyShow"
            show.outputs[0].default_value = 1.0
            shown = nt.nodes.new("ShaderNodeMath")
            shown.operation = "MULTIPLY"
            nt.links.new(src, shown.inputs[0])
            nt.links.new(show.outputs[0], shown.inputs[1])
            nt.links.new(shown.outputs["Value"], mix.inputs["Fac"])
            for i in range(len(body.data.materials)):
                body.data.materials[i] = self.m_body
        else:
            bpy.data.objects.remove(body)
        # the soul (his tenth review of 2026-11-10: back, and behind the head, its line down to the head at
        # forty-five degrees): a soft white disc facing the camera, lit by the will (Will, keyed: dim while
        # nothing is willed, as in sleep, never out), a thing of its own and no memory
        bm = geo.new_bmesh()
        geo.add_disc(bm, (0, 0, 0), engine.SOUL_RADIUS, 0, segments=96)
        self.m_soul = mats.soul_disc("Soul", engine.SOUL_RADIUS, 6.0, fade=self.fade)
        self.soul = geo.finish(bm, "Soul", [self.m_soul], col)
        self.soul.location = tuple(engine.SOUL_POS)
        geo.track_to(self.soul, self.cam, "TRACK_Z", "UP_Y")
        # the mind's simulation of its own soul, in the model behind the simulated head (placed and sized per frame)
        bm = geo.new_bmesh()
        geo.add_disc(bm, (0, 0, 0), 1.0, 0, segments=48)
        self.m_mini_soul = mats.soul_disc("MiniSoul", 1.0, MINI_SOUL_STRENGTH, fade=self.fade)
        self.mini_soul = geo.finish(bm, "MiniSoul", [self.m_mini_soul], col)
        geo.track_to(self.mini_soul, self.cam, "TRACK_Z", "UP_Y")
        self.will_times = []
        # the model frame: room metres into the skull, the mind's zoom in its scale
        self.frame = geo.add_empty("ModelFrame", tuple(engine.HEAD_CENTRE), engine.MODEL_SCALE, col)
        self.frame.rotation_mode = "QUATERNION"
        # the glass's reach from the eyes, which sit a few millimetres forward of the skull's centre
        radius = engine.GLASS_RADIUS
        self.radius = radius
        v_share = (FIELD_V / 2.0) / self.fov_deg
        common = (self.scan_size, self.fov_deg, FIELD_H, FIELD_V, radius, engine.HEAD_CENTRE)
        # the live surface: what the eyes capture this frame
        self.m_scan = scan_material("ScanSeen", fd, v_share, lids=True, side=-1, senses=True)
        self.scan = self._surface("Scan", "ScanNodes", self.m_scan, common, senses=True, sheet=SHEET)
        # the glass layer (rung 2o, his eleventh review): the eyes' picture of the pane's reflections, from the pane scan,
        # added at the pane's own depth over what lies beyond the glass; part of the seen picture, so the lids wipe it
        # and it goes with the live picture (the pane had been hidden from the scan since rung 2k, its reflections
        # painted onto the ground until then)
        self.m_refl = scan_material("Reflections", fd, v_share, lids=True, additive=True)
        self.refl = self._surface("Reflections", "ReflectionsNodes", self.m_refl, common, pane=True)
        # memory: the last picture the eyes held, standing whole while they stay shut
        self.m_last = scan_material("MemoryLast", fd, v_share, lids=False, memory=True, side=-1, senses=True)
        # (drawn as connected sheets like the seen picture, 2026-11-14: as splats its edges stood as rows of teeth)
        self.mem_last = self._surface("MemoryLast", "MemoryLastNodes", self.m_last, common, held_frame=True, senses=True, sheet=SHEET)
        # and the last picture's own glass layer: the pane's reflections as the eyes last held them, in memory's look,
        # lit by the eyes being shut as the rest of that picture is (the audit of 2026-11-15, his word of 2026-11-16:
        # the glass was the one thing with no place in the last picture, and its reflection went out as his eyes shut)
        self.m_refl_last = scan_material("ReflectionsLast", fd, v_share, lids=False, memory=True, additive=True)
        self.refl_last = self._surface("ReflectionsLast", "ReflectionsLastNodes", self.m_refl_last, common, held_frame=True, pane=True)
        # memory: a thought's picture, the frame in which the things he thinks of were last in sight
        # together, lit on those things by the thought (the chime: the phone's place, the table and the
        # bed as last seen, his review of 2026-11-08, second; the phone's own memory until his seventh
        # review of 2026-11-10, lit by its sound and its name; now any thought's, from the timeline)
        # (a thought's picture, the frame in which the things he thinks of were last in sight, stood here from his
        # seventh review of 2026-11-10 to his eleventh of 2026-11-11: a thing thought of is drawn whole by its known
        # shape now, MemoryShapes below, and the old picture's pixels over it only made the chime's nightstand a mess)
        # the backdrop: what the mind holds whole behind the near things outside, the sky, the ground
        # and the range as a second scan with the trees, the bushes, the walls and the body hidden,
        # kept where the eyes' rays pass through the window (his review of 2026-11-09: the trees and
        # the range cast shadows on the sky). A memory, as everything the rays do not reach: its
        # picture is this frame's while the eyes are open and the last one's while they stay shut
        # (MemFrame, keyed), lit by the thought of the outside or by the eyes being shut, and gone
        # wherever the live picture has the same hit (his word of 2026-11-09, fifth review)
        common_back = (self.back_size, self.fov_deg, FIELD_H, FIELD_V, radius, engine.HEAD_CENTRE)
        # the backdrop, the sky and the far sides complete this frame's picture, so the lids wipe them with it
        # (his ninth review of 2026-11-10: as the eyes closed, the live sky dimmed beside a fill at full light)
        self.m_back = scan_material("Backdrop", fd, v_share, lids=True, memory=True)
        # (both drawn as connected sheets like every other picture, 2026-11-15: as splats the remembered ridge kept steps)
        self.back = self._surface("Backdrop", "BackdropNodes", self.m_back, common_back, held_frame=True, backdrop=True, sheet=SHEET)
        # the dome remembered behind the range (his review of 2026-11-09, fifth: the black between the
        # mountains and the sky read as a shadow): the sky scan's picture above the horizon the mind
        # imagines without the range, the ground's colour below it, kept wherever the backdrop's ray did
        # not reach the sky above the horizon, a memory like the backdrop
        self.m_sky = scan_material("SkyFill", fd, v_share, lids=True, memory=True)
        self.sky = self._surface("SkyFill", "SkyFillNodes", self.m_sky, common_back, held_frame=True, backdrop=True, sky_fill=True, sheet=SHEET)
        # a thought-of thing drawn whole by its known shape (his eleventh review of 2026-11-11): the room's mesh
        # things as the mind knows them, lit by the known sun, a memory lit by the thought on each or by the eyes
        # being shut, under the picture's own splats wherever the rays reach it. The far side of every thing held
        # whole is this (his eighth review of 2026-11-10: a bush seen from the side was a crescent): until his
        # eleventh it was the rays' exit points painted in the front's own colour, the shadow side's
        self.m_shape = scan_material("MemoryShape", fd, v_share, lids="field", memory=True, senses=True, colour_share=True)
        shape_things = [(bpy.data.objects[r["name"]], int(r["id"]), list(r.get("colours") or [r.get("colour", (0.6, 0.6, 0.6))]), int(r.get("part", -1)),
                         bool(r.get("closed", False)))
                        for r in self.things
                        if r["id"] != 0 and r.get("shape", True) and r["name"] in bpy.data.objects and float(r["radius"]) < SHAPE_REACH]
        pixel_angle = self.fov_deg * math.pi / 180.0 / self.scan_size[0]
        # every known shape cut until no edge of it is longer than SHAPE_EDGE_DEG degrees as seen from the middle of the
        # room, SHAPE_EDGE metres at the least (the note at SHAPE_EDGE); a body part keeps the contact test's finer cut
        room_mid = Vector(tuple(float(v) for v in self.spec.size)) / 2.0
        shape_levels = dict(self.contact_levels)
        for ob_s, _, _, _, _ in shape_things:
            if ob_s.name in shape_levels:
                continue
            mw_s = ob_s.matrix_world
            vs_s = [mw_s @ v.co for v in ob_s.data.vertices]
            longest_s = max(((vs_s[e.vertices[0]] - vs_s[e.vertices[1]]).length for e in ob_s.data.edges), default=0.0)
            centre_s = sum((mw_s @ Vector(b) for b in ob_s.bound_box), Vector()) / 8.0
            limit_s = max(SHAPE_EDGE, (centre_s - room_mid).length * math.radians(SHAPE_EDGE_DEG))
            shape_levels[ob_s.name] = int(min(6, max(0, math.ceil(math.log2(max(longest_s, 1e-6) / limit_s)))))
        print("SHAPES cut: " + ", ".join(f"{o.name} {shape_levels[o.name]}" for o, _, _, p_s, _ in shape_things if p_s < 0), flush=True)
        self.shapes = self._object("MemoryShapes", "MemoryShapesNodes",
                                   shape_nodes("MemoryShapesNodes", shape_things, self.frame, self.sim_eye_cam, self.table, self.m_shape, radius,
                                               pixel_angle, tuple(self.spec.size), sense_img=self.sense_img, n_frames=self.n_frames, torso_obj=self.torso,
                                               contact_obj=self.contact, levels=shape_levels,
                                               live_pos_img=self.pos_img, fov_deg=self.fov_deg, live_idx_img=self.idx_img,
                                               live_col_img=self.col_img, seen_material=self.m_scan, scan_size=self.scan_size))
        # the last picture's own tiles (the audit of 2026-11-15, his word of 2026-11-16): the faces seen nearly edge-on in
        # the picture the eyes last held, drawn from the known shapes as the live picture's are, tested from the eyes as
        # they were at that picture's frame (EyeHeld, keyed), in the last picture's look
        self.eye_held = bpy.data.objects.new("EyeHeld", None)
        self.eye_held.rotation_mode = "QUATERNION"
        self.col.objects.link(self.eye_held)
        self.shapes_last = self._object("MemoryShapesLast", "MemoryShapesLastNodes",
                                        shape_nodes("MemoryShapesLastNodes", shape_things, self.frame, self.sim_eye_cam, self.table, self.m_last,
                                                    radius, pixel_angle, tuple(self.spec.size), levels=shape_levels,
                                                    live_pos_img=self.pos_img, fov_deg=self.fov_deg, live_idx_img=self.idx_img,
                                                    live_col_img=self.col_img, seen_material=self.m_last, scan_size=self.scan_size,
                                                    held=True, test_eye_obj=self.eye_held))
        # the senses on the simulated body (rung 2p): the outline glow of a moving, a warm or a cold part, the body's
        # parts as surfaces a little outside their tiles, lit at their rims; the touch's lightning to the head; the
        # gravity arrow in the simulated skull
        self.m_outline = outline_material("Outline", fd)
        body_things = [th for th in shape_things if th[3] >= 0]   # (no seen test on the glow: it is a sense's own light)
        self.outline = self._object("Outline", "OutlineNodes",
                                    shape_nodes("OutlineNodes", body_things, self.frame, self.sim_eye_cam, self.table, self.m_outline, radius,
                                                pixel_angle, tuple(self.spec.size), sense_img=self.sense_img, n_frames=self.n_frames, torso_obj=self.torso,
                                                outline=True, contact_obj=self.contact, levels=self.contact_levels))
        # the sun as the mind holds it (his review of 2026-11-08): a ball of light a little beyond the
        # sky, on the sun's line from the eyes, lit while the sun is in mind and the far field has
        # resolved; the half the rays reach seen while the sun is in sight, the rest memory
        self.m_sun = sun_material("SunBall", (1.0, 0.9, 0.72), v_share)
        bm = geo.new_bmesh()
        # (96 by 48 faces: at 24 by 16 the ball's rippled outline stood as corners, 2026-11-15)
        geo.add_sphere(bm, (0.0, 0.0, 0.0), 1.0, 0, segments=96, rings=48)
        self.sun_ball = geo.finish(bm, "SunBall", [self.m_sun], col)
        self.sun_ball.scale = (0.001, 0.001, 0.001)
        heat = self.sun_ball.modifiers.new("Heat", "NODES")
        heat.node_group = sun_heat_nodes("SunHeatNodes", self.sim_eye_cam, self.fov_deg)
        # the senses on the picture: the rings of a sound alone
        self.group = mats.model_group(head_centre=tuple(engine.HEAD_CENTRE), radii=tuple(engine.SKULL_RADII), model_scale=engine.MODEL_SCALE)
        # clipped to the skull: a far sound's ring, drawn at the glass, circled outside it (seen 2026-11-08)
        self.m_soft = mats.model_material("SoftLight", 1.6, thin="none", clip=True, group=self.group, fade=fd)
        self.m_ring = ring_material("Ring", self.group, fd)
        self.waves = []
        for k in range(WAVE_GLYPHS):
            o = _annulus(f"Wave_{k:02d}", self.m_ring, col, inner=RING_INNER)
            # the band is RING_INNER wide: the key that thins it stands at 1 when made (the note at RING_INNER)
            o.data.shape_keys.key_blocks["thin"].value = 0.0
            geo.track_to(o, self.cam, "TRACK_Z", "UP_Y")
            o["att"] = 0.0
            o["col"] = list(mats.RADAR)
            self.waves.append(o)
        self.m_bolt = bolt_material("Lightning", self.group, fd)
        self.bolts = []
        for k in range(engine.LIGHTNING_SLOTS):
            o = self._object(f"Lightning_{k:02d}", f"LightningNodes_{k:02d}", lightning_nodes(f"LightningNodes_{k:02d}", self.m_bolt, self.cam))
            o.data.materials.append(self.m_bolt)
            o["att"] = 0.0
            o["col"] = list(mats.MAGENTA)
            self.bolts.append(o)
        # the gravity arrow: a solid extruded arrow, opaque, a ripple running along it (his word of 2026-11-13, twelfth round)
        self.m_arrow = arrow_material("GravityArrow", fd)
        self.arrow = _arrow("GravityArrow", self.m_arrow, col)
        self.arrow.rotation_mode = "QUATERNION"
        self.arrow["att"] = 0.0
        self.ng_arrow = arrow_ripple_nodes("GravityArrowRipple")
        ripple = self.arrow.modifiers.new("Ripple", "NODES")
        ripple.node_group = self.ng_arrow
        # no end-on marks any more: a solid arrow seen along its length shows its own end
        self.arrow_marks = []
        self.bloom = render.bloom_compositor(scene, 1.0, 0.35, 0.6) if bloom else None

    def _organ_held(self, frame):
        """Whether the eyes' picture of that frame holds a hit on an organ (the ears, the eyes, the heart, the lungs), read
        off its index picture once; taken as so where the picture cannot be read."""
        if frame is None:
            return False
        cache = self.__dict__.setdefault("_organ_cache", {})
        if frame not in cache:
            found = True
            try:
                import re
                organ_ids = [int(r["id"]) for r in self.things if int(r.get("part", -1)) >= len(tags.PARTS)]
                path = pathlib.Path(bpy.path.abspath(self.idx_img.filepath))
                path = path.with_name(re.sub(r"\d+(?=\.\w+$)", f"{int(frame):04d}", path.name))
                im = bpy.data.images.load(str(path), check_existing=False)
                px = np.empty(im.size[0] * im.size[1] * 4, dtype=np.float32)
                im.pixels.foreach_get(px)
                found = bool(np.isin(np.unique(np.round(px[0::4]).astype(np.int32)), organ_ids).any()) if organ_ids else False
                bpy.data.images.remove(im)
            except Exception as exc:
                print(f"ORGAN HELD: the index picture of frame {frame} could not be read ({exc}): taken as holding one", flush=True)
            cache[frame] = found
            print(f"ORGAN HELD: the picture of frame {frame} holds a hit on an organ: {found}", flush=True)
        return cache[frame]

    def _thing_table(self, rows):
        """The table of things as a mesh of loose vertices (nothing renders), one per thing by its index,
        with the rows as point attributes; a table of the one row 'none' when no things are given."""
        if not rows or rows[0]["id"] != 0:
            rows.insert(0, {"id": 0, "name": "none", "centre": (0.0, 0.0, 0.0), "radius": 1.0e9, "region": REGION_OTHER})
        n = max(r["id"] for r in rows) + 1
        by_id = {r["id"]: r for r in rows}
        me = bpy.data.meshes.new("ThingTableMesh")
        me.from_pydata([(0.0, 0.0, 0.0)] * n, [], [])
        # the thing each thing ripples with as a memory (2026-11-15: a ripple per thing parted the window's frame from
        # its wall): itself, or the thing it names as the one it is set into, lies on or rests on (tags.OF_PROP, the
        # row's "of"), followed to its end; that thing's index, centre and radius stand in the row as wave_*
        by_name = {r["name"]: r for r in rows}

        def root_of(r, depth=0):
            of = r.get("of")
            return r if (not of or of not in by_name or depth > 8) else root_of(by_name[of], depth + 1)

        for name, dtype in (("centre", "FLOAT_VECTOR"), ("radius", "FLOAT"), ("region", "FLOAT"), ("colour", "FLOAT_COLOR"), ("part", "FLOAT"),
                            ("wave_id", "FLOAT"), ("wave_centre", "FLOAT_VECTOR"), ("wave_radius", "FLOAT"), ("round", "FLOAT")):
            attr = me.attributes.new(name, dtype, "POINT")
            for i in range(n):
                r = by_id.get(i, rows[0])
                if name == "centre":
                    attr.data[i].vector = tuple(r["centre"])
                elif name == "colour":
                    attr.data[i].color = (*r.get("colour", (0.6, 0.6, 0.6)), 1.0)
                elif name == "part":
                    attr.data[i].value = float(r.get("part", -1))
                elif name == "round":
                    attr.data[i].value = float(r.get("round", 0.0))
                elif name == "wave_id":
                    attr.data[i].value = float(root_of(r)["id"])
                elif name == "wave_centre":
                    attr.data[i].vector = tuple(root_of(r)["centre"])
                elif name == "wave_radius":
                    # (his own body is one thing to the ripple: a part of it is never held whole on its own, so the
                    # pieces of an arm in the last picture do not part at the joint)
                    attr.data[i].value = 1.0e9 if int(r.get("part", -1)) >= 0 else float(root_of(r)["radius"])
                else:
                    attr.data[i].value = float(r[name])
        ob = bpy.data.objects.new("ThingTable", me)
        self.col.objects.link(ob)
        ob["rows"] = [f'{r["id"]} {r["name"]} region {r["region"]}' for r in rows]
        return ob

    def _surface(self, obj_name, group_name, material, common, held_frame=False, box=None, backdrop=False, sky_fill=False, peel=False, pane=False,
                 senses=False, sheet=False):
        size, fov, fh, fv, radius, centre = common
        if pane:
            pos_img, col_img, idx_img = self.pane_pos, self.pane_col, self.pane_idx
        elif peel:
            pos_img, col_img, idx_img = self.peel_pos, self.col_img, self.peel_idx
        elif sky_fill:
            pos_img, col_img, idx_img = self.sky_pos, self.sky_col, self.sky_idx
        elif backdrop:
            pos_img, col_img, idx_img = self.back_pos, self.back_col, self.back_idx
        else:
            pos_img, col_img, idx_img = self.pos_img, self.col_img, self.idx_img
        ng = scan_nodes(group_name, pos_img, col_img, self.frame, self.sim_eye_cam, size, fov, fh, fv, radius, centre,
                        material, peel_pos_img=None if (peel or backdrop or pane) else self.peel_pos, peel_idx_img=None if (peel or backdrop or pane) else self.peel_idx, tight=pane,
                        held_frame=held_frame, box=box, spec=self.spec,
                        backdrop=backdrop, sky_fill=sky_fill, live_pos_img=self.pos_img, back_pos_img=self.back_pos,
                        back_col_img=self.back_col, idx_img=idx_img, table_obj=self.table, peel=peel, live_idx_img=self.idx_img,
                        live_idx_pos=self.pos_img, senses=senses, sense_img=self.sense_img, n_frames=self.n_frames, torso_obj=self.torso,
                        contact_obj=self.contact if senses else None, sheet=sheet)
        return self._object(obj_name, group_name, ng)

    def _contact_body(self):
        """ContactBody (rung 2p): the body's own shapes in room metres with every vertex's contact (contact_nodes),
        nothing that renders; and the cuts each of its objects takes so its longest edge is under CONTACT_EDGE (the
        mesh's own longest edge, at the size the table of things has the object). Its targets: every mesh thing that
        is no body part, the closed ones the mind holds a shape of told inside as well as near."""
        n_body = len(tags.PARTS)
        body, targets, levels = [], [], {}
        for r in self.things:
            ob = bpy.data.objects.get(r.get("name", ""))
            if r["id"] == 0 or ob is None or ob.type != "MESH":
                continue
            part = int(r.get("part", -1))
            if 0 <= part < n_body:
                vs = [v.co for v in ob.data.vertices]
                longest = max(((vs[e.vertices[0]] - vs[e.vertices[1]]).length for e in ob.data.edges), default=0.0)
                span = max((Vector(ob.bound_box[6]) - Vector(ob.bound_box[0])).length, 1e-6)
                longest *= 2.0 * float(r["radius"]) / span
                cuts = int(min(5, max(0, math.ceil(math.log2(max(longest, 1e-6) / CONTACT_EDGE)))))
                levels[ob.name] = cuts
                body.append((ob, part, cuts, bool(r.get("closed"))))
            elif part < 0:
                targets.append((ob, bool(r.get("closed")) and float(r["radius"]) < SHAPE_REACH))
        self.contact_parts = (body, targets) if body else None
        if not body:
            return None, {}
        wy0, wy1, wz0, wz1 = self.spec.window
        room_w, room_d, room_h = (float(v) for v in self.spec.size)
        window_c = (room_w, (wy0 + wy1) / 2.0, (wz0 + wz1) / 2.0)

        def in_room(o):
            c = sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8.0
            return -1.0 <= c.x <= room_w + 1.0 and -1.0 <= c.y <= room_d + 1.0 and -1.0 <= c.z <= room_h + 1.0

        # what can shade the skin from the sun or the window's air: the room's own things (the note in contact_nodes)
        shade = [o for o, _ in targets if in_room(o) and not o.get(tags.PASS_PROP)]
        ob = self._object("ContactBody", "ContactBodyNodes",
                          contact_nodes("ContactBodyNodes", body, targets, window_c=window_c, shade=shade))
        print("CONTACT: the room's things that can shade the skin: " + ", ".join(o.name for o in shade), flush=True)
        ob.hide_render = True
        return ob, levels

    def read_pairs(self, room_scene, frames, fps, cache_path=None):
        """Every touch through the piece, pair by pair (his word of 2026-11-13, thirteenth round: run through the whole
        timeline, a collision test between the limbs that are not joined at one joint, and render what touches). At
        every frame the skin of every body part, cut to PAIR_SAMPLE, is measured against the surface of every thing of
        the room and of every other body part but those joined to it at one joint or fused with it (tags.own_parts).
        The gaps (every pair's least distance at every frame it comes within PAIR_REACH) are kept beside cache_path
        as .npz under a key of the body pieces' places, and what counts as a touch that begins is worked out from
        them each time by touches.begins_of_pairs, whatever else the part touches meanwhile: the part-by-part reading
        before this (read_contact) saw no beginning where a hand that rested on one thing met a second, or met the
        other hand. cache_path itself takes the beginnings and every pair's share of the frames, to read. Returns the
        sparks (strikes_of_pairs) and the beginnings (second, part, other, metres a second)."""
        import hashlib
        import json
        import time
        import bmesh
        from mathutils.bvhtree import BVHTree
        if getattr(self, "contact_parts", None) is None:
            return [], []
        body, targets = self.contact_parts
        parts = list(tags.PARTS)
        times = [float(anim.time_of(f, fps)) for f in frames]
        h = hashlib.sha1()
        for f in frames[::10]:
            room_scene.frame_set(f)
            for ob, _, _, _ in body:
                h.update(np.round(np.array(ob.matrix_world, dtype=np.float64), 4).tobytes())
        h.update(repr(("gaps", len(frames), PAIR_REACH, PAIR_SAMPLE, sorted(tags.FUSED_PAIRS),
                       [(o.name, p) for o, p, _, _ in body], [o.name for o, _ in targets])).encode())
        key = h.hexdigest()
        store = pathlib.Path(cache_path).with_suffix(".npz") if cache_path is not None else None

        def cut_pieces():
            """Every piece of the body with its part and its skin's points, cut to PAIR_SAMPLE, in its own frame."""
            out = []
            for ob, part, _, _ in body:
                bm = bmesh.new()
                bm.from_mesh(ob.data)
                size = max(abs(v) for v in ob.matrix_world.to_scale())
                for _ in range(6):
                    long_edges = [e for e in bm.edges if (e.verts[0].co - e.verts[1].co).length * size > PAIR_SAMPLE]
                    if not long_edges:
                        break
                    bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1)
                pts = np.array([tuple(v.co) for v in bm.verts], dtype=np.float64).reshape(-1, 3)
                bm.free()
                out.append((ob, parts[part], pts))
            return out

        def touched_places(begins):
            """Where each touch that begins lies on the part: the point of the part's skin nearest the surface of what it
            touches, in the room at the touch's second (his word of 2026-11-16: a spark begins from the point of
            contact, and the rule must hold for whatever figure and room replace the stand-ins: so it is read off the
            two surfaces, as the touch itself is, and names no joint). Keyed (second, part, other)."""
            if not begins:
                return {}
            pcs = cut_pieces()
            by_name = {o.name: o for o, _ in targets}
            dg_ = room_scene.view_layers[0].depsgraph
            at = {}
            for t_b, part, other, _ in begins:
                at.setdefault(int(np.argmin(np.abs(np.array(times) - float(t_b)))), []).append((float(t_b), part, other))
            out = {}
            for k in sorted(at):
                room_scene.frame_set(frames[k])
                trees = {}

                def tree_of(ob):
                    if ob.name not in trees:
                        plain = len(ob.modifiers) == 0 and ob.data.shape_keys is None
                        ev = None if plain else ob.evaluated_get(dg_)
                        me = ob.data if plain else ev.to_mesh()
                        co = np.empty(len(me.vertices) * 3, np.float32)
                        me.vertices.foreach_get("co", co)
                        m = np.array(ob.matrix_world, dtype=np.float64)
                        w = co.reshape(-1, 3).astype(np.float64) @ m[:3, :3].T + m[:3, 3]
                        trees[ob.name] = BVHTree.FromPolygons([tuple(v) for v in w], [tuple(p.vertices) for p in me.polygons])
                        if ev is not None:
                            ev.to_mesh_clear()
                    return trees[ob.name]

                for t_b, part, other in at[k]:
                    others = ([ob for ob, p, _ in pcs if p == other[5:]] if other.startswith("part:")
                              else [by_name[other]] if other in by_name else [])
                    best = None
                    for ob, p, pts in pcs:
                        if p != part:
                            continue
                        m = np.array(ob.matrix_world, dtype=np.float64)
                        w = pts @ m[:3, :3].T + m[:3, 3]
                        for ob_b in others:
                            tree = tree_of(ob_b)
                            for q in w:
                                hit = tree.find_nearest(Vector(q), 2.0 * PAIR_REACH)
                                if hit[0] is not None and (best is None or hit[3] < best[0]):
                                    best = (hit[3], q)
                    if best is not None:
                        out[(round(t_b, 4), part, other)] = tuple(round(float(v), 4) for v in best[1])
            return out

        def finish(series, how):
            begins, shares = touches.begins_of_pairs(series, times)
            places = touched_places(begins)
            if cache_path is not None:
                pathlib.Path(cache_path).write_text(json.dumps({
                    "key": key, "begins": begins, "pairs": shares,
                    "places": {f"{t_:.4f}|{p_}|{o_}": list(v_) for (t_, p_, o_), v_ in sorted(places.items())}}, indent=0), encoding="utf-8")
            print(f"PAIRS: every pair's gap through the piece {how}: {len(series)} pairs came within {PAIR_REACH} m, "
                  f"{len(begins)} touches began, the touched place read for {len(places)} of them", flush=True)
            return strikes_of_pairs(begins, places), begins

        if store is not None and store.exists():
            z = np.load(store, allow_pickle=False)
            if str(z["key"]) == key:
                return finish(touches.unpack(z), f"read back from {store.name}")
        t_start = time.perf_counter()
        dg = room_scene.view_layers[0].depsgraph
        pieces = []
        for ob, part, _, _ in body:
            bm = bmesh.new()
            bm.from_mesh(ob.data)
            size = max(abs(v) for v in ob.matrix_world.to_scale())
            for _ in range(6):
                long_edges = [e for e in bm.edges if (e.verts[0].co - e.verts[1].co).length * size > PAIR_SAMPLE]
                if not long_edges:
                    break
                bmesh.ops.subdivide_edges(bm, edges=long_edges, cuts=1)
            pts = np.array([tuple(v.co) for v in bm.verts], dtype=np.float64).reshape(-1, 3)
            bm.free()
            pieces.append((ob, parts[part], pts))
        own = {p: tags.own_parts(p) for p in parts}

        def may_touch(a, b):
            return b not in own[a]

        room_w, room_d, room_h = (float(v) for v in self.spec.size)

        def in_room(o):
            c = sum((o.matrix_world @ Vector(b) for b in o.bound_box), Vector()) / 8.0
            return -1.0 <= c.x <= room_w + 1.0 and -1.0 <= c.y <= room_d + 1.0 and -1.0 <= c.z <= room_h + 1.0

        room_scene.frame_set(frames[0])
        things = [o for o, _ in targets if in_room(o)]
        still, series = {}, {}

        def note(pair, k, d):
            cur = series.setdefault(pair, {})
            if d < cur.get(k, 1e9):
                cur[k] = d

        for k, f in enumerate(frames):
            room_scene.frame_set(f)
            surf = {}

            def surface(ob):
                """The thing's surface in the room this frame, and its box grown by PAIR_REACH."""
                if ob.name in surf:
                    return surf[ob.name]
                mw = ob.matrix_world.copy()
                plain = len(ob.modifiers) == 0 and ob.data.shape_keys is None
                sig = tuple(round(v, 5) for row in mw for v in row)
                if plain and ob.name in still and still[ob.name][0] == sig:
                    surf[ob.name] = still[ob.name][1]
                    return surf[ob.name]
                ev = None if plain else ob.evaluated_get(dg)
                me = ob.data if plain else ev.to_mesh()
                co = np.empty(len(me.vertices) * 3, np.float32)
                me.vertices.foreach_get("co", co)
                m = np.array(mw, dtype=np.float64)
                w = co.reshape(-1, 3).astype(np.float64) @ m[:3, :3].T + m[:3, 3]
                polys = [tuple(p.vertices) for p in me.polygons]
                bvh = BVHTree.FromPolygons([tuple(v) for v in w], polys)
                if ev is not None:
                    ev.to_mesh_clear()
                surf[ob.name] = (bvh, w.min(0) - PAIR_REACH, w.max(0) + PAIR_REACH)
                if plain:
                    still[ob.name] = (sig, surf[ob.name])
                return surf[ob.name]

            def nearest(w, lo_a, hi_a, other):
                bvh, lo, hi = surface(other)
                if (hi_a < lo).any() or (lo_a > hi).any():
                    return None
                best = None
                for p in w[((w >= lo) & (w <= hi)).all(axis=1)]:
                    hit = bvh.find_nearest(Vector(p), PAIR_REACH)
                    if hit[0] is not None and (best is None or hit[3] < best):
                        best = hit[3]
                return best

            world = []
            for ob, part, pts in pieces:
                m = np.array(ob.matrix_world, dtype=np.float64)
                w = pts @ m[:3, :3].T + m[:3, 3]
                world.append((ob, part, w, w.min(0), w.max(0)))
            for ob, part, w, lo_a, hi_a in world:
                for other in things:
                    d = nearest(w, lo_a, hi_a, other)
                    if d is not None:
                        note((part, other.name), k, d)
                for ob_b, part_b, _, _, _ in world:
                    if part_b == part or not may_touch(part, part_b):
                        continue
                    d = nearest(w, lo_a, hi_a, ob_b)
                    if d is not None:
                        note((part, "part:" + part_b), k, d)
                        note((part_b, "part:" + part), k, d)
        if store is not None:
            np.savez_compressed(store, **touches.pack(series, key, times))
        return finish(series, f"measured at {len(frames)} frames in {time.perf_counter() - t_start:.1f} s")

    def read_contact(self, room_scene, frames, fps, cache_path=None):
        """When the body's touch changes through the piece, for the touch's lightning (rung 2p, his word of 2026-11-13:
        a lightning at every new contact, by one rule for every case, and none while a touch only lasts). For every
        frame and body part: level (the most of its vertices' contact, 0 to 1) and gain (how fast new skin comes into
        contact: the mean, over the part's vertices, of the rise of their contact, per second; a release is no gain;
        kept, and not used by the strikes).

        Read off a lighter ContactBody (cut one step coarser, the skin test left out of what is worked out) in a scene
        of its own at every frame, about a quarter of a second a read. Kept in cache_path beside the renders under a
        key made of the body pieces' places every tenth frame, so a build of the same animation reads it back, and the
        strikes are worked out afresh from it (strikes_of), so their thresholds can change without a new read.
        Returns the strikes: (second, part), in order."""
        import hashlib
        import time
        if getattr(self, "contact_parts", None) is None:
            return []
        parts = list(tags.PARTS)
        body, targets = self.contact_parts
        times = np.array([anim.time_of(f, fps) for f in frames], dtype=np.float64)
        h = hashlib.sha1()
        for f in frames[::10]:
            room_scene.frame_set(f)
            for ob, _, _, _ in body:
                h.update(np.round(np.array(ob.matrix_world, dtype=np.float64), 4).tobytes())
        h.update(repr((len(frames), CONTACT_SKIN, CONTACT_EDGE, [(o.name, p, c) for o, p, c, _ in body], [o.name for o, _ in targets])).encode())
        key = h.hexdigest()
        if cache_path is not None and pathlib.Path(cache_path).exists():
            z = np.load(cache_path)
            if str(z["key"]) == key:
                print(f"CONTACT: the touch through the piece read back from {cache_path}", flush=True)
                return strikes_of(z["level"], z["gain"], times, parts)
        t0 = time.perf_counter()
        ng = contact_nodes("ContactReadNodes", [(o, p, max(0, c - 1), cl) for o, p, c, cl in body], targets)
        stores = [n for n in ng.nodes if n.bl_idname == "GeometryNodeStoreNamedAttribute" and n.inputs["Name"].default_value == "contact"]
        assert len(stores) == 1, len(stores)
        go = next(n for n in ng.nodes if n.bl_idname == "NodeGroupOutput")
        ng.links.new(stores[0].outputs["Geometry"], go.inputs["Geometry"])
        me0 = bpy.data.meshes.new("ContactReadMesh")
        ob = bpy.data.objects.new("ContactRead", me0)
        mod = ob.modifiers.new("Contact", "NODES")
        mod.node_group = ng
        sc = bpy.data.scenes.new("ContactReadScene")
        sc.collection.objects.link(ob)
        n_p, n_f = len(parts), len(frames)
        level = np.zeros((n_f, n_p), np.float32)
        gain = np.zeros((n_f, n_p), np.float32)
        prev, masks = None, None
        for k, f in enumerate(frames):
            sc.frame_set(f)
            me = ob.evaluated_get(sc.view_layers[0].depsgraph).data
            n = len(me.vertices)
            c = np.empty(n, np.float32)
            me.attributes["contact"].data.foreach_get("value", c)
            if masks is None or len(masks[0]) != n:
                part = np.empty(n, np.float32)
                me.attributes["part"].data.foreach_get("value", part)
                masks = [np.abs(part - i) < 0.5 for i in range(n_p)]
                prev = None
            for i in range(n_p):
                m = masks[i]
                if not m.any():
                    continue
                w = c[m]
                level[k, i] = float(w.max())
                if prev is not None:
                    gain[k, i] = float(np.maximum(w - prev[m], 0.0).mean()) / max(times[k] - times[k - 1], 1e-6)
            prev = c
        bpy.data.scenes.remove(sc)
        bpy.data.objects.remove(ob)
        bpy.data.meshes.remove(me0)
        bpy.data.node_groups.remove(ng)
        if cache_path is not None:
            np.savez_compressed(cache_path, key=np.array(key), level=level, gain=gain)
        print(f"CONTACT: the touch through the piece read at {n_f} frames in {time.perf_counter() - t0:.1f} s", flush=True)
        return strikes_of(level, gain, times, parts)

    def _object(self, obj_name, group_name, ng):
        me = bpy.data.meshes.new(obj_name + "Mesh")
        ob = bpy.data.objects.new(obj_name, me)
        self.col.objects.link(ob)
        mod = ob.modifiers.new("Scan", "NODES")
        mod.node_group = ng
        ob["nodes"] = group_name
        return ob

    def add_words(self, words, will):
        """No words in this scene: the vision part, memory and the sounds alone; the will's words give the mind's
        simulated soul its presence (bake)."""
        self.will_times = sorted(float(w["t"]) for w in will)
        return None

    def willfulness(self, t):
        """The character's own willfulness at t: 1 at an act of will (a word of the timeline, risen over
        MINI_SOUL_RISE and held MINI_SOUL_HOLD), fading over MINI_SOUL_FALL to the floor between."""
        best = 0.0
        for tw in self.will_times:
            dt_w = t - tw
            if dt_w < 0.0:
                continue
            if dt_w < MINI_SOUL_RISE:
                v = anim.smoothstep(dt_w / MINI_SOUL_RISE)
            elif dt_w < MINI_SOUL_RISE + MINI_SOUL_HOLD:
                v = 1.0
            else:
                v = math.exp(-(dt_w - MINI_SOUL_RISE - MINI_SOUL_HOLD) / MINI_SOUL_FALL)
            best = max(best, v)
        return MINI_SOUL_FLOOR + (1.0 - MINI_SOUL_FLOOR) * best

    @staticmethod
    def _angles(v, head_rot):
        """A direction's azimuth from forward and its elevation from level, degrees, in the head's frame."""
        fwd = head_rot @ Vector((1.0, 0.0, 0.0))
        up = head_rot @ Vector((0.0, 0.0, 1.0))
        elev = math.degrees(math.asin(max(-1.0, min(1.0, v.dot(up)))))
        flat = v - up * v.dot(up)
        azim = math.degrees(math.acos(max(-1.0, min(1.0, flat.normalized().dot(fwd))))) if flat.length > 1e-6 else 0.0
        return azim, elev

    @classmethod
    def _view_of(cls, point_room, eye_room, head_rot, radius=0.0, half=None):
        """How well a thing about a room point sits in the field of both eyes, 100 degrees from forward and 65
        from level: the mean, over its centre, the six face centres and the eight corners of its box (half, its
        half-extents along the room's axes; six points seven tenths of its radius out when it has no box), of
        each point's place in the field, 1 straight ahead falling to 0 at the field's rim. A thing beside him
        or under him counts for little however near it is (his eleventh review of 2026-11-11: the chime's
        picture had been the last glimpse of the bed at the field's rim, with the phone in his hand)."""
        v = Vector(point_room) - Vector(eye_room)
        if v.length < 1e-6:
            return 1.0
        total = 0.0
        points = [Vector(point_room)]
        if half is not None:
            hx, hy, hz = (float(h) for h in half)
            for axis, h in enumerate((hx, hy, hz)):
                for sign in (-1.0, 1.0):
                    q = Vector(point_room)
                    q[axis] += sign * h
                    points.append(q)
            for sx in (-1.0, 1.0):
                for sy in (-1.0, 1.0):
                    for sz in (-1.0, 1.0):
                        points.append(Vector(point_room) + Vector((sx * hx, sy * hy, sz * hz)))
        else:
            for axis in range(3):
                for sign in (-0.7, 0.7):
                    q = Vector(point_room)
                    q[axis] += sign * radius
                    points.append(q)
        for q in points:
            w = q - Vector(eye_room)
            if w.length < 1e-6:
                total += 1.0
                continue
            az_q, el_q = cls._angles(w / w.length, head_rot)
            total += max(0.0, 1.0 - az_q / (FIELD_H / 2.0)) * max(0.0, 1.0 - abs(el_q) / (FIELD_V / 2.0))
        return total / len(points)

    @classmethod
    def _in_field(cls, point_room, eye_room, head_rot, radius=0.0):
        return cls._view_of(point_room, eye_room, head_rot, radius) > 0.0

    def bake(self, states, baker, cover_of=None, eye_of=None, eyes=None, phone_of=None):
        """cover_of(frame) -> the lids' cover; eye_of(frame) -> (eye in room metres, head rotation): the
        scan camera's own place; eyes: the eye model; phone_of(frame) -> the phone in room metres, the
        one thing of the table that moves out of reach. Leaves self.held: for every frame, the picture
        frames its memories read, which a stepped render keeps (rungs/rung2.py)."""
        sw = anim.Sparse(baker)
        # the sparks' points, width and throw are small numbers in the model: a writer that keeps changes down to a
        # millionth (the coarse one drops a change under a thousandth, 3 to 4 cm of the room at the reach's scale)
        swf = anim.Sparse(baker, eps=1e-6)
        glass_em = next(n for n in self.glass.node_tree.nodes if n.bl_idname == "ShaderNodeEmission")
        glass_path = f'nodes["{glass_em.name}"].inputs[{glass_em.inputs.find("Strength")}].default_value'
        fade_paths = {n: f'nodes["{n}"].outputs[0].default_value' for n in ("Model", "Ghost", "Soul")}
        ng_scan = bpy.data.node_groups[self.scan["nodes"]]
        ng_refl = bpy.data.node_groups[self.refl["nodes"]]
        ng_refl_last = bpy.data.node_groups[self.refl_last["nodes"]]
        ng_shapes_last = bpy.data.node_groups[self.shapes_last["nodes"]]
        ng_last = bpy.data.node_groups[self.mem_last["nodes"]]
        ng_back = bpy.data.node_groups[self.back["nodes"]]
        ng_sky = bpy.data.node_groups[self.sky["nodes"]]
        ng_shapes = bpy.data.node_groups[self.shapes["nodes"]]
        think_paths = [f'nodes["Think{i}"].outputs[0].default_value' for i in range(MEM_REGION_COUNT)]
        shut_path = 'nodes["Shut"].outputs[0].default_value'
        live_now_path = 'nodes["LiveNow"].outputs[0].default_value'
        age_b_path = 'nodes["AgeB"].outputs[0].default_value'
        age_a_path = 'nodes["AgeA"].outputs[0].default_value'
        shrink_path = 'nodes["Shrink"].outputs[0].default_value'

        def age_fade(age):
            k = math.exp(-max(age, 0.0) / MEM_AGE_TAU)
            return MEM_AGE_BRIGHT + (1.0 - MEM_AGE_BRIGHT) * k, MEM_AGE_ALPHA + (1.0 - MEM_AGE_ALPHA) * k

        def grey_of(age):
            """A memory's colour drains toward grey with its age, every memory alike."""
            return 0.3 + 0.7 * (1.0 - math.exp(-max(age, 0.0) / MEM_GREY_TAU))

        def stand_of(live_v):
            """How far the live picture stands against a memory at a place the eyes see: nought under SEEN_FADE's first
            mark, whole from its second, as the geometry works it out from LiveNow."""
            return anim.smoothstep((live_v - SEEN_FADE[0]) / (SEEN_FADE[1] - SEEN_FADE[0]))

        def key_memory(ng, mat, f, picture, t, shut_v, live_v, completes=False, cover_v=0.0, front=True):
            """One memory's frame keys: its picture's frame, its standing, the seen test, its age; completes:
            the memory completes the live picture (the backdrop, the sky, the far sides), so it sits at the
            picture's own depth and under the lids' wipe (cover_v) while it holds this frame, and at the last
            picture's depth, unwiped, while the eyes stay shut (front; with front False it holds the last picture at
            its own depth, behind the live one)."""
            sw.set(mat.node_tree, LIVE_PATH, 0, f, 1.0)
            sw.set(ng, shrink_path, 0, f, MEM_SHRINK if (not completes or (picture != f and front)) else 1.0)
            if completes:
                # under the lids' wipe as the live picture is (cover_v); while it holds the last picture, out from under
                # it as the live picture goes (Unwipe: 1 less the share SEEN_FADE gives the live picture's standing).
                # Until 2026-11-14 the wipe was dropped in the one frame the eyes became long shut
                sw.set(mat.node_tree, COVER_PATH, 0, f, cover_v)
                # (in steps of a five-hundredth: the key writer holds a value within a thousandth of the last one
                # written, and a smooth approach would stop short of one)
                sw.set(mat.node_tree, UNWIPE_PATH, 0, f, (round((1.0 - stand_of(live_v)) * 500.0) / 500.0) if picture != f else 0.0)
            sw.set(ng, shut_path, 0, f, shut_v)
            sw.set(ng, live_now_path, 0, f, live_v)
            sw.set(ng, FRAME_PATH, 0, f, float(picture), anim.CONSTANT)
            age = t - anim.time_of(picture, self.fps)
            if completes and picture == f and COMPLETES_OLD:
                # what completes this frame's picture is a place the eyes do not see: it takes memory's oldest look, as
                # the unseen side of a thing does (the known shapes, below), so what he thinks is there reads apart from
                # what he sees (his word of 2026-11-16: the point is to show the difference between the two). At age
                # nought until then: the ground behind a bush came in looking as the ground he sees
                grey_v, (age_b, age_a) = 1.0, (MEM_AGE_BRIGHT, MEM_AGE_ALPHA)
            else:
                grey_v, (age_b, age_a) = grey_of(age), age_fade(age)
            sw.set(mat.node_tree, GREY_PATH, 0, f, grey_v)
            sw.set(mat.node_tree, age_b_path, 0, f, age_b)
            sw.set(mat.node_tree, age_a_path, 0, f, age_a)
        hc = engine.HEAD_CENTRE
        dt = 1.0 / self.fps
        resolve = 0.0
        knee = KNEE * self.radius
        span = self.radius - knee
        self.held = {}
        self.picture = {}
        sun_sight_of = {fs.frame: float(getattr(fs, "sun_sight", 0.0)) for fs in states}
        # the sense table (rung 2p): a row per frame, per part the sense light (its colour, its strength), the tint and
        # the part's scale, and the outline (its colour, its strength); written as one picture the surfaces sample
        n_parts = len(tags.SENSE_PARTS)
        table = np.zeros((self.n_frames, SENSE_FIELDS * n_parts, 4), dtype=np.float32)
        table[:, n_parts:2 * n_parts, 1] = 1.0      # every part at rest: scale 1
        table[:, n_parts:2 * n_parts, 3] = 1.0
        bolt_paths = {nm: f'nodes["{nm}"].outputs[0].default_value'
                      for nm in [f"K{k}{ax}" for k in range(engine.LIGHTNING_KNOTS) for ax in "XYZ"] + ["Progress", "Width", "Seed", "Jag", "Pull"]}
        arrow_face = None
        # a picture is what the eyes have held: until their first opening there is none (last_open, mem_frame None), so the
        # last picture, the backdrop and the remembered sky have nothing to show and the eyes being shut light nothing
        # (his word of 2026-11-12: while he wakes, only what he is aware of; until then the scan of the first frame, made
        # through shut lids in the dark room, stood whole in the head from the moment he was aware, a black sheet before
        # the room's known shapes). Shut at the first frame, the eyes are taken as long shut already
        live, mem = 1.0, 0.0
        closed_since, was_long = None, False
        last_open, mem_frame = None, None
        sun_in_picture = False
        pic_frame = None      # the frame the eyes' picture was taken at: this one, or the last one before the lids shut
        if cover_of is not None and float(cover_of(states[0].frame)) >= 0.999:
            live, closed_since, was_long = 0.0, states[0].t - LIVE_HOLD, True
        for k, fs in enumerate(states):
            f, t = fs.frame, fs.t
            loc, rot, sc = fs.M.decompose()
            baker.set_vec(self.frame, "location", f, loc)
            baker.set_vec(self.frame, "rotation_quaternion", f, rot)
            # keyed exactly every frame, like the location: keyed sparsely, the scale between keys ran a
            # little off the location computed for it, degrees of parallax at a hand's distance from the eyes
            baker.set_vec(self.frame, "scale", f, sc)
            pos, aim, lens = fs.camera
            baker.set_vec(self.cam, "location", f, pos)
            baker.set_vec(self.aim, "location", f, aim)
            sw.set(self.cam.data, "lens", 0, f, lens)
            # through a reveal the camera turns as the twin of the room's camera, roll and all (rungs/rung2.py
            # bake_moves, fs.camera_rot); otherwise it tracks its aim with the model's up as its up
            rot_q = getattr(fs, "camera_rot", None)
            track_path = f'constraints["{self.track.name}"].influence'
            if rot_q is not None:
                baker.set_vec(self.cam, "rotation_quaternion", f, rot_q)
                sw.set(self.cam, track_path, 0, f, 0.0, anim.CONSTANT)
            else:
                sw.set(self.cam, track_path, 0, f, 1.0, anim.CONSTANT)
            dist = (pos - hc).length
            # the glass dims when the camera is close, and further as the mind zooms out, so the rim
            # does not fight the small model inside (his review of 2026-11-08, second)
            zoom_in = cameras.clamp((math.log(fs.scale) - math.log(engine.FAR_SCALE)) / (math.log(engine.MODEL_SCALE) - math.log(engine.FAR_SCALE)))
            sw.set(self.glass.node_tree, glass_path, 0, f,
                   fs.ghost * (0.3 + 0.7 * anim.smoothstep((dist - 1.5) / 2.5)) * (0.5 + 0.5 * zoom_in))
            fade_model = getattr(fs, "fade_model", 1.0)
            sw.set(self.fade, fade_paths["Model"], 0, f, fade_model)
            sw.set(self.fade, fade_paths["Ghost"], 0, f, getattr(fs, "fade_ghost", 1.0))
            if self.m_body is not None:
                g0, g1 = GHOST_BODY
                sw.set(self.m_body.node_tree, BODY_SHOW_PATH, 0, f, 1.0 - anim.smoothstep((t - g0) / max(g1 - g0, 1e-6)))
            sw.set(self.fade, fade_paths["Soul"], 0, f, getattr(fs, "fade_soul", 1.0))
            # the soul's light is the will: the awareness of the moment, lifted a little as a word lands
            # (fs.glow), on a floor so that asleep it is dim and never out
            aw = float(getattr(fs, "awareness", 1.0))
            will = SOUL_FLOOR + (1.0 - SOUL_FLOOR) * aw * (0.7 + 0.3 * min(1.0, float(getattr(fs, "glow", 0.0))))
            near = cameras.clamp(((Vector(pos) - engine.SOUL_POS).length - SOUL_NEAR[0]) / (SOUL_NEAR[1] - SOUL_NEAR[0]))
            sw.set(self.m_soul.node_tree, WILL_PATH, 0, f, will)
            sw.set(self.m_soul.node_tree, NEAR_PATH, 0, f, near)
            # the eyes' place, the head's frame, and the eyes' own frame (the head's turned by their look)
            eye_ref = eye_of(f) if eye_of is not None else (fs.eye_room, fs.head_rot)
            eye_room, head_rot = eye_ref[0], eye_ref[1]
            eye_rot = eye_ref[2] if len(eye_ref) > 2 else head_rot
            eye_pos = fs.M @ Vector(eye_room)
            # the mind's simulated soul: behind and above the simulated head on the soul's own line, at the soul's own
            # distance from the head's centre, in the model; its presence the willfulness as far as he is aware
            head_c_room = Vector(eye_room) - head_rot @ Vector(EYE_OFFSET)
            # farther from the head the less he is aware, back at its place as awareness returns (the waking)
            away = 1.0 + MINI_SOUL_AWAY * (1.0 - aw)
            soul_room = head_c_room + head_rot @ (MINI_SOUL_DIR * (engine.SOUL_POS - engine.HEAD_CENTRE).length * away)
            baker.set_vec(self.mini_soul, "location", f, fs.M @ soul_room)
            r_mini = engine.SOUL_RADIUS * fs.scale
            baker.set_vec(self.mini_soul, "scale", f, (r_mini, r_mini, r_mini))
            sw.set(self.m_mini_soul.node_tree, WILL_PATH, 0, f, self.willfulness(t) * aw)
            sw.set(self.m_mini_soul.node_tree, NEAR_PATH, 0, f, 1.0)
            eye_q = (fs.M.to_3x3().normalized() @ eye_rot @ cameras.CAM_FROM_HEAD).to_quaternion()
            # the place the eyes' picture was taken from. With the lids fully shut the eyes take nothing in: the picture
            # stays that of the last frame on which they were open (pic_frame, the frame the last picture is of: the
            # scans of the frames between are that frame's own, rungs/rung2.py), and so does the place it was taken
            # from, wherever the head goes behind the
            # lids. Every surface reads the picture's field and the lids' wipe from this camera. (Until 2026-11-16 the
            # scan and its place went on through shut lids for the LIVE_HOLD the live picture stands: at the crest his
            # hand, rising behind his lids, stood in the head as a dark shape for a third of a second, and the lids'
            # field, turning with his head, cut a dashed line across the window he remembered)
            # (the cover rounded as the eye table writes it, which the renderer reads for the same test)
            cover_pic = round(float(cover_of(f)), 3) if cover_of is not None else 0.0
            pic_frame = f if (cover_pic < 0.999 or last_open is None) else last_open
            pic_ref = eye_of(pic_frame) if (eye_of is not None and pic_frame is not None and pic_frame != f) else eye_ref
            pic_rot = pic_ref[2] if len(pic_ref) > 2 else pic_ref[1]
            baker.set_vec(self.sim_eye_cam, "location", f, fs.M @ Vector(pic_ref[0]))
            baker.set_vec(self.sim_eye_cam, "rotation_quaternion", f,
                          (fs.M.to_3x3().normalized() @ pic_rot @ cameras.CAM_FROM_HEAD).to_quaternion())
            # the lids: a blink dims the live picture through its wipe; the eyes kept shut take it away
            # after a moment and the last picture they held stands, draining and fading
            cover = float(cover_of(f)) if cover_of is not None else 0.0
            sw.set(self.m_scan.node_tree, COVER_PATH, 0, f, cover)
            sw.set(self.m_refl.node_tree, COVER_PATH, 0, f, cover)
            if round(cover, 3) < 0.1:
                last_open = f
            shut = round(cover, 3) >= 0.999
            if shut and closed_since is None:
                closed_since = t
            if not shut:
                closed_since = None
            long_shut = shut and (t - closed_since) >= LIVE_HOLD
            if long_shut and not was_long:
                mem_frame = last_open
                # the sun is part of that picture where the eyes' rays reached its disc in it
                sun_in_picture = mem_frame is not None and sun_sight_of.get(mem_frame, 0.0) > 0.01
            was_long = long_shut
            has_picture = mem_frame is not None
            target = 0.0 if long_shut else 1.0
            live += (target - live) * (1.0 - math.exp(-dt / (LIVE_TAU if target < live else 0.3)))
            # the memory comes up from the moment the eyes count as shut (over MEM_RISE), and goes before the live picture
            # is back. (Until 2026-11-15 it waited for the lids' own picture to have mostly gone, about a second, and took
            # 0.6 s: through a doze of 1.6 s the remembered room stood for half a second at a third of its light, and
            # its ripple with it: his "way more mild")
            want_mem = 1.0 if long_shut else 0.0
            mem += (want_mem - mem) * (1.0 - math.exp(-dt / (MEM_RISE if want_mem > mem else 0.25)))
            # the eyes shut light the last picture as far as he is aware: asleep, nothing stands in the head
            # (his tenth review of 2026-11-10, the waking snippet)
            shut_lit = mem * aw if has_picture else 0.0
            sw.set(self.m_scan.node_tree, LIVE_PATH, 0, f, live)
            # the seen picture's cover. As his eyes open after a long shutting the last picture goes out before the
            # live one, which comes in behind it: with both thinned at once (the live by Live, the last by its going)
            # neither covered, and from the camera's side the outside that lies behind the wall showed through both, a
            # grainy sheet beside the window for a third of a second (2026-11-16). While the last picture stands the
            # live one is whole behind it and comes up by its light alone; as the last one goes (its light from 0.05
            # down to the 0.018 at which it is gone) the cover returns to Live, by then nearly 1
            held_w = min(1.0, max(0.0, (shut_lit - 0.018) / 0.032)) if (has_picture and not shut) else 0.0
            # (as far as the lids have uncovered it: on the first frames of the opening they still cover nearly all of
            # the field and the live picture is at their floor, nearly black. Whole from the first frame, it stood
            # before every part of the remembered picture the ripple had carried behind it, and the room went black
            # with pale streaks for a frame, 2026-11-16)
            # (through a long shutting the cover runs out at the mark where the remembered picture comes forward of the
            # seen one, SETTLE_TOP. Falling with the light itself it was still a fifth there: a fifth of a dark veil was
            # hidden in one frame, and the picture in his head brightened by a step, 17 levels of 255 in the window,
            # half a second after his eyes had shut, 2026-11-18)
            live_cover = max(0.0, (live - SETTLE_TOP) / (1.0 - SETTLE_TOP)) if long_shut else live
            sw.set(self.m_scan.node_tree, LIVE_A_PATH, 0, f, live_cover + (1.0 - live_cover) * held_w * (1.0 - cover))
            sw.set(ng_scan, VISIBLE_PATH, 0, f, live)
            sw.set(self.m_refl.node_tree, LIVE_PATH, 0, f, live)
            sw.set(ng_refl, VISIBLE_PATH, 0, f, live)
            # the thought on each of the ten things this frame (triview/engine.py thoughts), which lights
            # every memory alike wherever its hits lie on that thing
            # as far as he is aware: a thought in his sleep lights nothing (his eleventh review of 2026-11-11)
            thinks = [aw * max((float(fs.thought.get(tg, 0.0)) for tg in GROUP_TAGS.get(g, ())), default=0.0) for g in range(MEM_REGION_COUNT)]
            colours = [max((float(getattr(fs, "thought_colour", {}).get(tg, 0.0)) for tg in GROUP_TAGS.get(g, ())), default=0.0) for g in range(MEM_REGION_COUNT)]
            for path, c in zip(MEM_COLOUR_PATHS, colours):
                sw.set(ng_shapes, path, 0, f, c)
            # the last picture stands whole while the eyes are long shut (Shut), and not otherwise
            key_memory(ng_last, self.m_last, f, mem_frame if has_picture else f, t, shut_lit, live)
            # the backdrop and the remembered sky: this frame's picture while the eyes are open, the
            # last picture's while they stay shut; lit by the thought of the outside, or by Shut
            # (the last picture's for as long as the last picture itself stands: after the eyes open it fades over a
            # quarter second and more, and what completes it fades with it. Until the audit of 2026-11-15 these two
            # changed over to this frame's picture, fresh and at full brightness, at the first frame of the opening,
            # while the last picture round them was still fading: pale patches behind every bush and tree for half a
            # second as his eyes opened after the sun)
            back_picture = mem_frame if (has_picture and (long_shut or shut_lit >= 0.018)) else f
            # (at the last picture's depth, nearer the eyes, only while the eyes stay shut. Once they open, what
            # completes the picture lies behind the live one, as it does at every other moment: left at the last
            # picture's depth it stood before the live picture, dim, and the window stayed dim for half a second
            # after his eyes had opened, 2026-11-16)
            key_memory(ng_back, self.m_back, f, back_picture, t, shut_lit, live, completes=True, cover_v=cover, front=long_shut)
            key_memory(ng_sky, self.m_sky, f, back_picture, t, shut_lit, live, completes=True, cover_v=cover, front=long_shut)
            # with no picture held, the surfaces that draw one have no geometry at all: a thought lights nothing of a
            # picture the eyes never had (the things thought of are drawn by their known shapes)
            # (and none on a frame where nothing lights it: its light is the eyes being shut or a sense on an organ, and
            # a hit under 0.02 of light is deleted in the geometry; the mark a tenth lower here, for the keys' tolerance)
            organ_lit = max((min(1.0, float(v_[1])) for p_, v_ in getattr(fs, "sense_light", {}).items() if p_ in tags.ORGAN_PARTS), default=0.0)
            # (a sense on an organ lights the last picture only where that picture holds a hit on an organ: read off its
            # index picture once, _organ_held)
            last_lit = shut_lit >= 0.018 or (organ_lit >= 0.018 and self._organ_held(mem_frame))
            sw.set(ng_last, VISIBLE_PATH, 0, f, 1.0 if (has_picture and last_lit) else 0.0, anim.CONSTANT)
            # the last picture's glass layer: the same frame's pictures of the pane, lit by the eyes being shut alone
            key_memory(ng_refl_last, self.m_refl_last, f, mem_frame if has_picture else f, t, shut_lit, live)
            sw.set(ng_refl_last, VISIBLE_PATH, 0, f, 1.0 if (has_picture and shut_lit >= 0.018) else 0.0, anim.CONSTANT)
            # the last picture's own tiles: shown with it, its frame's pictures, lit by the eyes being shut; and the eyes as
            # they were at that frame, carried into the model as it stands now
            sw.set(ng_shapes_last, VISIBLE_PATH, 0, f, 1.0 if (has_picture and last_lit) else 0.0, anim.CONSTANT)
            sw.set(ng_shapes_last, FRAME_PATH, 0, f, float(mem_frame if has_picture else f), anim.CONSTANT)
            sw.set(ng_shapes_last, shut_path, 0, f, shut_lit)
            sw.set(ng_shapes_last, STAND_PATH, 0, f, live)
            if has_picture and eye_of is not None:
                held_ref = eye_of(mem_frame)
                held_rot = held_ref[2] if len(held_ref) > 2 else held_ref[1]
                baker.set_vec(self.eye_held, "location", f, fs.M @ Vector(held_ref[0]))
                baker.set_vec(self.eye_held, "rotation_quaternion", f, (fs.M.to_3x3().normalized() @ held_rot @ cameras.CAM_FROM_HEAD).to_quaternion())
            else:
                baker.set_vec(self.eye_held, "location", f, eye_pos)
                baker.set_vec(self.eye_held, "rotation_quaternion", f, eye_q)
            # and none on a frame where nothing lights them: their light is a thought's or the eyes being shut (a hit
            # under 0.02 of light is deleted in the geometry; the mark a tenth lower here, for the keys' tolerance)
            back_lit = max(max(thinks), shut_lit) >= 0.018
            for ng in (ng_back, ng_sky):
                sw.set(ng, VISIBLE_PATH, 0, f, 1.0 if ((has_picture or not long_shut) and back_lit) else 0.0, anim.CONSTANT)
            # a thing thought of is drawn whole by its known shape (MemoryShapes), lit by the thought on it
            sw.set(ng_shapes, VISIBLE_PATH, 0, f, 1.0)
            sw.set(ng_shapes, shut_path, 0, f, shut_lit)
            # the shapes' tiles are gone where the eyes see their place, while the live picture stands
            sw.set(ng_shapes, live_now_path, 0, f, live)
            # and those inside the eyes' field are under the lids as the picture is, coming out from under them as the
            # live picture goes (the material's lids="field"; Unwipe as the backdrop's)
            sw.set(self.m_shape.node_tree, COVER_PATH, 0, f, cover)
            sw.set(self.m_shape.node_tree, UNWIPE_PATH, 0, f, round((1.0 - stand_of(live)) * 500.0) / 500.0)
            sun_el = room.sun_elevation_at(self.spec, t)
            sun_known = room.sun_direction(self.spec, sun_el)
            for axis, nm in enumerate(("SunX", "SunY", "SunZ")):
                sw.set(ng_shapes, f'nodes["{nm}"].outputs[0].default_value', 0, f, float(sun_known[axis]))
            # the known sun lights a face by the share of its disc above the ridge on its own line: nought before first
            # light (until 2026-11-12 every face turned east was sunlit from the first frame, the sun under the horizon)
            # (the engine's measure, read off the scene from his eyes: fs.sun_up)
            sw.set(ng_shapes, 'nodes["SunShare"].outputs[0].default_value', 0, f, float(getattr(fs, "sun_up", 0.0)))
            # the picture that stands in the head this frame, for the known light (rungs/rung2.py reads the shapes'
            # exposure off it): this frame's while the eyes are not long shut, the last one held while they are, none
            # before they have held one; and how far a picture stands at all (the first opening brings it in)
            self.picture[f] = ((mem_frame if long_shut else f) if (has_picture or not long_shut) else None,
                               1.0 if has_picture else (0.0 if long_shut else live))
            for path, a in zip(think_paths, thinks):
                for ng in (ng_back, ng_sky, ng_shapes):
                    sw.set(ng, path, 0, f, a)
            # the known shapes: the memory of what was never seen, the oldest there is, so fully drained, at an old
            # memory's brightness and opacity (his word of 2026-11-12: the unseen side of a thing and the memory of
            # a thing are one thing; until then the shapes stood at full brightness and opacity)
            for path, val in ((LIVE_PATH, 1.0), (GREY_PATH, 1.0), (age_b_path, MEM_AGE_BRIGHT), (age_a_path, MEM_AGE_ALPHA)):
                sw.set(self.m_shape.node_tree, path, 0, f, val)
            self.held[f] = sorted({f, back_picture} | ({mem_frame} if has_picture else set()))
            if f in (2101, 2401, 2671, 2731, 2761):
                print(f"MEMORY f={f}: thinks {[round(v, 2) for v in thinks]}, last picture {mem_frame}, shut {mem:.2f}", flush=True)
            # the far field resolves from flat against the sky to its order while the eyes have it,
            # and that knowledge goes only slowly once they have not
            far_sum, all_sum = float(fs.far_vote[0]), float(fs.far_vote[1])
            seeing_far = cover < 0.5 and all_sum > 1e-6 and far_sum / all_sum > 0.1
            if seeing_far:
                resolve += (1.0 - resolve) * (1.0 - math.exp(-dt / RESOLVE_RISE))
            else:
                resolve *= math.exp(-dt / RESOLVE_FALL)
            for ng in (ng_scan, ng_refl, ng_refl_last, ng_last, ng_back, ng_sky, ng_shapes, ng_shapes_last):
                sw.set(ng, RESOLVE_PATH, 0, f, resolve)
            # the sun as held: on its line from the eyes at its believed distance, pressed to the glass
            # if need be, sized to the angle the mind gives it; a disc flat against the sky at first, a
            # ball a little beyond it once the far field has resolved
            sun_dir = room.sun_direction(self.spec, room.sun_elevation_at(self.spec, t))
            dir_model = (fs.M.to_3x3() @ Vector(sun_dir)).normalized()
            d_sun = (engine.BELIEVE_SKY + SUN_FLAT_IN + (engine.BELIEVE_SUN - engine.BELIEVE_SKY - SUN_FLAT_IN) * resolve) * fs.scale
            d_sun = d_sun if d_sun <= knee else knee + span * (1.0 - math.exp(-(d_sun - knee) / span))
            # (as far as the last picture has taken the live one's place the ball is that picture's memory and stands as
            # its hits do, MEM_SHRINK nearer the eyes: left at the live picture's depth, the remembered sky, drawn nearer,
            # cut through the ball and all but a sliver of it lay behind the sky from the camera's side. The audit's O5:
            # the remembered sun a wedge, 2026-11-16)
            d_sun *= 1.0 + (MEM_SHRINK - 1.0) * ((1.0 - live) if has_picture else 0.0)
            baker.set_vec(self.sun_ball, "location", f, eye_pos + dir_model * d_sun)
            r_ball = d_sun * math.tan(math.radians(SUN_BALL_DEG / 2.0))
            depth = SUN_FLAT_DEPTH + (1.0 - SUN_FLAT_DEPTH) * resolve
            baker.set_vec(self.sun_ball, "scale", f, (r_ball, r_ball, r_ball * depth))
            baker.set_vec(self.sun_ball, "rotation_euler", f, tuple(dir_model.to_track_quat("Z", "Y").to_euler()))
            # the seen half while the eyes' rays reach any of the disc (triview/engine.py sun_sight), at
            # the sun's own strength, dimmed by the lids and gone with the live picture as every seen splat is
            sw.set(self.m_sun.node_tree, STRENGTH_PATH, 0, f, SUN_BALL_STRENGTH * fade_model)
            # (as it was in the picture that stands: behind shut lids the sun is seen as it was on the last frame before
            # they shut, whatever passes before them)
            seen_sun = sun_sight_of.get(pic_frame if pic_frame is not None else f, 0.0)
            sw.set(self.m_sun.node_tree, SEEN_PATH, 0, f, seen_sun)
            # (and to the ball's ripple: the half toward the eyes holds still as far as the sun is seen)
            sw.set(self.sun_ball.modifiers["Heat"].node_group, SEEN_PATH, 0, f, seen_sun * live)
            sw.set(self.m_sun.node_tree, COVER_PATH, 0, f, cover)
            sw.set(self.m_sun.node_tree, LIVE_PATH, 0, f, live)
            # the memory half lit by the thought of the outside, by the eyes shut, or by the warmth on his face: a
            # sense on the sun holds it in mind as a thought does (his eighth review of 2026-11-10)
            # (by the eyes shut only where the last picture held the sun: until 2026-11-12 the ball stood as a grey disc
            # in the head whenever the eyes were shut and he was aware, at the alarm and through the doze, before sunrise)
            sw.set(self.m_sun.node_tree, MEM_PATH, 0, f,
                   max(thinks[2], shut_lit if sun_in_picture else 0.0, float(getattr(fs, "sun_felt", 0.0))) * fade_model)
            # its look by the rule for every memory (the audit of 2026-11-15): while the last picture stands (the eyes long
            # shut, or just opened) the whole ball is that picture's memory and has its age; otherwise its remembered
            # half is the side the eyes never see, the oldest memory there is, as a thing's unseen side is (the known
            # shapes). Under the lids where it lies in the eyes' field, out from under them as the live picture goes.
            # (Until then at full brightness whenever the eyes were not long shut, with no drain by age and no lid)
            if has_picture and (long_shut or shut_lit >= 0.018):
                age_sun = t - anim.time_of(mem_frame, self.fps)
                sun_grey, sun_bright = grey_of(age_sun), age_fade(age_sun)[0]
            else:
                sun_grey, sun_bright = 1.0, MEM_AGE_BRIGHT
            sw.set(self.m_sun.node_tree, MEM_BRIGHT_PATH, 0, f, sun_bright)
            sw.set(self.m_sun.node_tree, GREY_PATH, 0, f, sun_grey)
            sw.set(self.m_sun.node_tree, UNWIPE_PATH, 0, f, round((1.0 - stand_of(live)) * 500.0) / 500.0)
            # the sounds' rings (rung 2p): one per tenth of a second of a sound, as bright as the sound is loud (s_, the
            # peak of its stand-in waveform in that tenth) times the gate the engine gives it (how far it is attended, its
            # fade past the farther ear, and his awareness)
            shades = getattr(fs, "wave_colours", None) or [mats.RADAR] * len(fs.waves)
            wave_room = getattr(fs, "wave_room", None) or [None] * len(fs.waves)
            for o, (c, r, s_, gate), shade, placed in zip(self.waves, fs.waves, shades, wave_room):
                if gate > 1e-4:
                    if placed is not None:
                        # the ring's centre stands where a hit of the eyes' picture on the sound's source would stand: on
                        # its line from the eyes at its believed distance (flat against the sky until the far field has
                        # resolved), pressed toward the glass beyond the knee; and the ring's radius is scaled with it,
                        # so that it comes to his ears when the engine says the sound does. One placing for every point
                        # (the audit of 2026-11-15: a far sound's rings started 6 m from his head, short of their source)
                        src_room, r_room, d_judged = placed
                        to_src = Vector(src_room) - Vector(eye_room)
                        if to_src.length > 1e-6 and d_judged > 1e-6:
                            x_ring = engine.believed(to_src.length, resolve) * fs.scale
                            d_ring = x_ring if x_ring <= knee else knee + span * (1.0 - math.exp(-(x_ring - knee) / span))
                            c = eye_pos + (fs.M.to_3x3() @ to_src).normalized() * d_ring
                            r = r_room * d_ring / d_judged
                    baker.set_vec(o, "location", f, c)
                    baker.set_vec(o, "scale", f, (r, r, r))
                    # the ring's colour: its source's own shade of the radar's green
                    sw.set_prop(o, "col", f, list(shade), anim.CONSTANT)
                sw.set_prop(o, "att", f, (s_ * gate) if gate > 1e-4 else 0.0)
            # the senses on the simulated body (rung 2p): the table's row for this frame
            if 1 <= f <= self.n_frames:
                row_ = table[f - 1]
                for part, (colr, strength, tint) in getattr(fs, "sense_light", {}).items():
                    i = tags.PART_INDEX.get(part)
                    if i is None:
                        continue
                    row_[i, :3] = colr
                    row_[i, 3] = min(1.0, float(strength))
                    row_[n_parts + i, 0] = float(tint)
                organs = getattr(fs, "organs", {})
                for part, key in (("chest", "torso"), ("heart", "heart"), ("lung_l", "lung"), ("lung_r", "lung")):
                    row_[n_parts + tags.PART_INDEX[part], 1] = float(organs.get(key, 1.0))
                row_[n_parts + tags.PART_INDEX["chest"], 2] = float(organs.get("clear", 0.0))
                for part, (colr, strength) in getattr(fs, "outline", {}).items():
                    i = tags.PART_INDEX.get(part)
                    if i is None:
                        continue
                    row_[2 * n_parts + i, :3] = colr
                    row_[2 * n_parts + i, 3] = min(1.0, float(strength))
                for part, (colr, level) in getattr(fs, "touch", {}).items():
                    i = tags.PART_INDEX.get(part)
                    if i is None:
                        continue
                    row_[3 * n_parts + i, :3] = colr
                    row_[3 * n_parts + i, 3] = min(1.0, float(level))
                for part, (warm_l, cool_l) in getattr(fs, "temperature", {}).items():
                    i = tags.PART_INDEX.get(part)
                    if i is None:
                        continue
                    row_[4 * n_parts + i, 0] = min(1.0, float(warm_l))
                    row_[4 * n_parts + i, 1] = min(1.0, float(cool_l))
                    row_[4 * n_parts + i, 3] = 1.0
                # the flash of the part a spark comes from, in the same field's third number
                for part, level in getattr(fs, "spark_part", {}).items():
                    i = tags.PART_INDEX.get(part)
                    if i is None:
                        continue
                    row_[4 * n_parts + i, 2] = min(1.0, float(level))
                    row_[4 * n_parts + i, 3] = 1.0
            # the touch's lightning: from the part toward the head, in the model
            for o, (knots, prog, att, colr, began) in zip(self.bolts, getattr(fs, "lightning", [])):
                ng_b = bpy.data.node_groups[o["nodes"]]
                if att > 1e-4:
                    for k_, knot in enumerate(knots):
                        for ax, val in zip("XYZ", knot):
                            swf.set(ng_b, bolt_paths[f"K{k_}{ax}"], 0, f, float(val), anim.CONSTANT)
                    sw.set(ng_b, bolt_paths["Progress"], 0, f, float(prog), anim.CONSTANT)
                    swf.set(ng_b, bolt_paths["Width"], 0, f, LIGHTNING_WIDTH * fs.scale)
                    swf.set(ng_b, bolt_paths["Jag"], 0, f, LIGHTNING_JAG * fs.scale)
                    swf.set(ng_b, bolt_paths["Pull"], 0, f, LIGHTNING_PULL * fs.scale)
                    # one throw for the spark's whole life: the frame it began at
                    sw.set(ng_b, bolt_paths["Seed"], 0, f, float(began), anim.CONSTANT)
                    sw.set_prop(o, "col", f, list(colr))
                sw.set_prop(o, "att", f, float(att))
            # the gravity arrow inside the simulated skull: at the head's centre, along where the inner ear says down is
            # (the engine's plumb line), ARROW_LEN head radii long, as bright as balance is attended: a solid thing
            base, tip, plumb_a = fs.plumb
            d_arrow = (Vector(tip) - Vector(base))
            d_arrow = d_arrow.normalized() if d_arrow.length > 1e-9 else Vector((0.0, 0.0, -1.0))
            # it is there as far as balance is attended and he is aware, and grows in from nothing: never see-through
            a_arrow = float(plumb_a) * aw
            there = min(max(a_arrow / ARROW_SHOW, 0.0), 1.0)
            there = there * there * (3.0 - 2.0 * there)
            arrow_len = ARROW_LEN * figure.HEAD_RADIUS * fs.scale * there
            head_model = fs.M @ head_c_room
            baker.set_vec(self.arrow, "location", f, head_model - d_arrow * (arrow_len * 0.5))
            # its broad face turned about its length toward the rendering camera, and ARROW_TURN on from there so one of
            # its sides shows; looked at nearly along its length it keeps the face it had (the turn would spin there)
            to_cam = Vector(pos) - head_model
            face = to_cam - d_arrow * to_cam.dot(d_arrow)
            if face.length > 0.15 * max(to_cam.length, 1e-9) or arrow_face is None:
                if face.length < 1e-9:
                    face = d_arrow.orthogonal()
                arrow_face = face.normalized()
            else:
                keep = arrow_face - d_arrow * arrow_face.dot(d_arrow)
                arrow_face = keep.normalized() if keep.length > 1e-6 else d_arrow.orthogonal().normalized()
            turned = (Matrix.Rotation(ARROW_TURN, 3, d_arrow) @ arrow_face).normalized()
            side = d_arrow.cross(turned).normalized()
            baker.set_vec(self.arrow, "rotation_quaternion", f, Matrix((side, d_arrow, side.cross(d_arrow))).transposed().to_quaternion())
            w_arrow = ARROW_WIDTH * fs.scale * there
            baker.set_vec(self.arrow, "scale", f, (w_arrow, arrow_len, w_arrow))
            sw.set_prop(self.arrow, "att", f, min(a_arrow, 1.0))
            # the ripple: its crests run from the tail to the point
            swf.set(self.ng_arrow, ARROW_PHASE_PATH, 0, f, ARROW_PULSE * t)
            sw.set(self.m_outline.node_tree, mats.WAVE_T_PATH, 0, f, t)   # the body senses' waver
            if self.contact is not None:
                # where the sun stands, for what its rays reach on the skin (ContactBody's sun)
                ng_c = bpy.data.node_groups[self.contact["nodes"]]
                for ax, val in zip("XYZ", room.sun_direction(self.spec, room.sun_elevation_at(self.spec, t))):
                    sw.set(ng_c, f'nodes["Sun{ax}"].outputs[0].default_value', 0, f, float(val))
        sw.finish()
        swf.finish()
        # the sense table written and read back as the surfaces' picture, and a plain summary beside it
        _write_exr(self.sense_path, table)
        self.sense_img.filepath = str(self.sense_path)
        self.sense_img.source = "FILE"
        self.sense_img.reload()
        summary = {}
        for fs in states:
            rec = {}
            lit = {p: round(float(v[1]), 3) for p, v in getattr(fs, "sense_light", {}).items() if v[1] > 0.01}
            out = {p: round(float(v[1]), 3) for p, v in getattr(fs, "outline", {}).items() if v[1] > 0.01}
            bolts = [round(float(b[2]), 2) for b in getattr(fs, "lightning", []) if b[2] > 0.01]
            rings = sum(1 for w in fs.waves if w[3] > 0.01)
            organs = {k: round(float(v), 3) for k, v in getattr(fs, "organs", {}).items() if abs(v - 1.0) > 1e-3}
            flash = getattr(fs, "flash", (0.0, None))[0]
            if lit:
                rec["light"] = lit
            if out:
                rec["outline"] = out
            temp = {p: [round(float(v[0]), 3), round(float(v[1]), 3)] for p, v in getattr(fs, "temperature", {}).items() if max(v) > 0.01}
            if temp:
                rec["temperature"] = temp
            spark = {p: round(float(v), 4) for p, v in getattr(fs, "spark_part", {}).items() if v > 1e-4}
            if spark:
                rec["spark"] = spark
            if bolts:
                rec["lightning"] = bolts
            if rings:
                rec["rings"] = rings
            if organs:
                rec["organs"] = organs
            if flash > 0.01:
                rec["flash"] = round(float(flash), 3)
            if fs.plumb[2] > 0.15:
                rec["balance"] = round(float(fs.plumb[2]), 3)
            if rec:
                summary[str(fs.frame)] = rec
        import json as _json
        (self.sense_path.parent / "senses_frames.json").write_text(_json.dumps(summary, indent=0), encoding="utf-8")

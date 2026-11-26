"""Dressed wall pieces: one story tall, one grid cell wide, for buildings that are meant to be looked at.

Street side: a plinth with the turquoise band, a stone course under the roof line with a painted zigzag
(ground floor) or a plain cornice (upper floors), and round-arched openings framed in cut stone.
Room side: a wooden rail at dado height.
Openings: a doorway, a window with a lattice, or an arcade bay that stands on two stone piers."""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Vector

from . import wall as plain_wall

K = C.KIT["wall2"]
HALF, T = C.CELL / 2, C.WALL_T / 2
CUT = {"cut": True}
STONE = {"cut": True, "tone": 3}      # cut stone is paler than the plaster round it
ARC = 10                # straight pieces in half a circle


def _arc(r, spring, a0, a1, n=ARC):
    """Points on a round arch of radius r that springs at height `spring`, from angle a0 to a1 (degrees)."""
    return [(r * math.cos(math.radians(a0 + (a1 - a0) * k / n)), spring + r * math.sin(math.radians(a0 + (a1 - a0) * k / n)))
            for k in range(n + 1)]


def _courses(p, upper, gaps=()):
    """What every dressed wall carries: plinth, course under the roof line, rail on the room side.
    `gaps` are (x0, x1) stretches at the foot left open (a doorway)."""
    spans, x = [], -HALF
    for a, b in sorted(gaps):
        if a - x > 0.05:
            spans.append((x, a))
        x = b
    if HALF - x > 0.05:
        spans.append((x, HALF))
    for a, b in spans:
        if not upper:
            p.box((a, -T - K["plinth_out"], 0), (b, -T, K["plinth_h"]), "plaster", group="wall", band=True, extra=CUT)
        p.box((a, T, K["rail_z"]), (b, T + K["rail_out"], K["rail_z"] + K["rail_h"]), "wood", group="rail", grain="x",
              extra=CUT)
    z0, z1 = K["cornice"] if upper else K["frieze"]
    out = K["course_out"]
    course = p.box((-HALF, -T - out, z0), (HALF, -T, z1), "stone", group="course", extra=STONE)
    if not upper:
        teeth, m = K["teeth"], 0.13
        points = [(-HALF + k * C.CELL / (2 * teeth), -T - out, z0 + m if k % 2 == 0 else z1 - m) for k in range(2 * teeth + 1)]
        p.mark(course, "-y", points, width=0.1, family="band")


def _stone_arch(p, r, R, z0, spring, band):
    """The cut-stone frame of an opening: two jambs and the arch over them, as one horseshoe."""
    out = K["trim_out"]
    profile = [(R, z0)] + _arc(R, spring, 0, 180) + [(-R, z0), (-r, z0)] + _arc(r, spring, 180, 0) + [(r, z0)]
    pid = p.extrude(profile, T + out, "stone", group="trim", band=band, extra=STONE)
    stones = K["voussoirs"]
    for y, facet in ((-T - out, "-y"), (T + out, "+y")):
        for k in range(1, stones):                                   # joints between the arch stones
            a = math.radians(180 * k / stones)
            p.mark(pid, facet, [(r * math.cos(a), y, spring + r * math.sin(a)), (R * math.cos(a), y, spring + R * math.sin(a))],
                   tone=-3, width=0.05)
        z = z0 + K["jamb_course"]
        while z < spring + 0.05:                                     # level joints up the jambs
            for s in (-1, 1):
                p.mark(pid, facet, [(s * r, y, z), (s * R, y, z)], tone=-3, width=0.05)
            z += K["jamb_course"]
    return pid


def _lattice(p, r, z0, spring):
    """Mashrabiya: two sets of diagonal bars filling the arched opening, the second just behind the first."""
    bar, gap, m = K["bar"], K["bar_gap"], 0.12

    def inside(x, z):
        if abs(x) > r + m or z < z0 - m:
            return False
        return z <= spring or x * x + (z - spring) ** 2 <= (r + m) ** 2

    centre = Vector((0.0, 0.0, (z0 + spring + r) / 2))
    reach = r + (spring + r - z0) / 2
    for s, (dx, dz) in enumerate(((1, 1), (1, -1))):
        d = Vector((dx, 0, dz)).normalized()
        n = Vector((-d.z, 0, d.x))
        y = -T + K["bar_inset"] + s * (bar + 0.05)
        k = -int(reach / gap)
        while k * gap <= reach:
            o = centre + n * (k * gap)
            ts = [t / 20.0 for t in range(int(-reach * 30), int(reach * 30)) if inside(o.x + d.x * t / 20.0, o.z + d.z * t / 20.0)]
            if ts and ts[-1] - ts[0] > 0.5:
                mid, half = o + d * ((ts[0] + ts[-1]) / 2), (ts[-1] - ts[0]) / 2
                p.box((-half, -bar / 2, -bar / 2), (half, bar / 2, bar / 2), "darkwood", group=f"lattice{s}", grain="x",
                      frame=frame_axes((mid.x, y, mid.z), d, (0, 1, 0)), extra={"chunk": "window"})
            k += 1


def build(p, opening=None, upper=False, beams=True):
    band = not upper
    p.seams = [(0, -HALF), (0, HALF), (2, 0.0), (2, C.STORY)]
    if opening is None:
        p.box((-HALF, -T, 0), (HALF, T, C.STORY), "plaster", group="wall", band=band, extra=CUT)
        _courses(p, upper)
    else:
        o = K["openings"][("upper_" if upper else "") + opening]
        r, spring = o["w"] / 2, o["spring"]
        R = r + o["trim"]
        if opening == "door":
            profile = [(-HALF, 0), (-HALF, C.STORY), (HALF, C.STORY), (HALF, 0), (R, 0)] + _arc(R, spring, 0, 180) + [(-R, 0)]
            p.extrude(profile, T, "plaster", group="wall", band=band, extra=CUT)
            _stone_arch(p, r, R, 0.0, spring, band)
            _courses(p, upper, gaps=[(-R, R)])
        else:                                                        # window: the wall is two halves round the hole
            sill, sill_h = o["sill"], K["sill_h"]
            for s in (-1, 1):
                profile = ([(-HALF, 0), (-HALF, C.STORY), (0, C.STORY)] + _arc(R, spring, 90, 180, ARC // 2)
                           + [(-R, sill - sill_h), (0, sill - sill_h), (0, 0)])
                p.extrude([(s * -x, z) for x, z in profile] if s > 0 else profile, T, "plaster", group="wall", band=band,
                          extra=CUT)
            p.seams.append((0, 0.0))
            p.box((-R, -T - K["sill_out"], sill - sill_h), (R, T + 0.1, sill), "stone", group="sill", extra=STONE)
            _stone_arch(p, r, R, sill, spring, False)
            _lattice(p, r, sill, spring)
            _courses(p, upper)
    if beams and opening != "door":
        plain_wall._beams(p)


def arcade(p):
    """An open bay: a round arch on two stone piers with capitals. Piers of neighbouring bays join into columns."""
    o = K["openings"]["arcade"]
    r, spring = o["w"] / 2, o["spring"]
    R, depth, cap_h = r + o["trim"], T + o["pier_out"], o["cap_h"]
    for s in (-1, 1):
        xa, xb = sorted((s * r, s * HALF))
        pier = p.box((xa, -depth, 0), (xb, depth, spring - cap_h), "stone", group=f"pier{s}", band=True, extra=STONE)
        z = K["jamb_course"]
        while z < spring - cap_h - 0.3:
            for y, facet in ((-depth, "-y"), (depth, "+y")):
                p.mark(pier, facet, [(xa, y, z), (xb, y, z)], tone=-3, width=0.05)
            p.mark(pier, "-x" if s > 0 else "+x", [(s * r, -depth, z), (s * r, depth, z)], tone=-3, width=0.05)
            z += K["jamb_course"]
        xa, xb = sorted((s * (r - 0.16), s * HALF))
        p.box((xa, -depth - 0.16, spring - cap_h), (xb, depth + 0.16, spring), "stone", group=f"cap{s}", extra=STONE)
    profile = [(-HALF, spring), (-HALF, C.STORY), (HALF, C.STORY), (HALF, spring)] + _arc(R, spring, 0, 180)
    p.extrude(profile, T, "plaster", group="wall", extra=CUT)
    ring = _arc(R, spring, 0, 180) + _arc(r, spring, 180, 0)
    out = K["trim_out"]
    pid = p.extrude(ring, T + out, "stone", group="trim", extra=STONE)
    stones = K["voussoirs"] + 4
    for y, facet in ((-T - out, "-y"), (T + out, "+y")):
        for k in range(1, stones):
            a = math.radians(180 * k / stones)
            p.mark(pid, facet, [(r * math.cos(a), y, spring + r * math.sin(a)), (R * math.cos(a), y, spring + R * math.sin(a))],
                   tone=-3, width=0.05)
    z0, z1 = K["frieze"]
    course = p.box((-HALF, -T - K["course_out"], z0), (HALF, -T, z1), "stone", group="course", extra=STONE)
    teeth, m = K["teeth"], 0.13
    p.mark(course, "-y", [(-HALF + k * C.CELL / (2 * teeth), -T - K["course_out"], z0 + m if k % 2 == 0 else z1 - m)
                          for k in range(2 * teeth + 1)], width=0.1, family="band")
    p.seams = [(0, -HALF), (0, HALF), (2, 0.0), (2, C.STORY)]
    plain_wall._beams(p)


def corner(p, upper=False):
    """The post where two dressed walls meet: a pilaster with a stone cap that the wall courses die into."""
    a, more = K["corner_half"], K["corner_cap"]
    z0, z1 = K["cornice"] if upper else K["frieze"]
    if upper:
        p.box((-a, -a, 0), (a, a, z0), "plaster", group="wall", extra=CUT)
    else:
        foot = a + K["plinth_out"] * 0.6
        p.box((-foot, -foot, 0), (foot, foot, K["plinth_h"]), "plaster", group="wall", band=True, extra=CUT)
        p.box((-a, -a, K["plinth_h"]), (a, a, z0), "plaster", group="shaft", extra=CUT)
    p.box((-a - more, -a - more, z0), (a + more, a + more, z1), "stone", group="cap", extra=STONE)
    if z1 < C.STORY - 0.01:
        p.box((-a, -a, z1), (a, a, C.STORY), "plaster", group="top", extra=CUT)
    p.seams = [(2, 0.0), (2, C.STORY)]

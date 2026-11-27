"""Green things for the streets: a cypress in a stone ring, a palm in a raised bed with shrubs under it,
and a plant in a pot to stand by a door."""
import math
import random

from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix, Vector

CUT = {"cut": True}


def _clump(p, at, r, mat, name, rng, flat=0.75):
    profile = [(r * math.sin(math.radians(k)), -flat * r * math.cos(math.radians(k))) for k in (20, 55, 90, 125, 160)]
    frame = Matrix.Translation(at) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z") @ Matrix.Rotation(rng.uniform(-0.4, 0.4), 4, "X")
    p.lathe(profile, 8, mat, grain=None, group=name, frame=frame, smooth=True, extra={"tone": rng.randint(-1, 1)})


def cypress(p):
    """A cypress: a dark flame of foliage down to knee height, in a ring of stone. It hides whoever stands behind it."""
    p.lathe([(2.3, 0.0), (2.3, 0.9), (2.45, 0.9), (2.45, 1.15), (1.75, 1.15), (1.75, 0.0)], 12, "stone", closed=True,
            grain=None, group="ring", band=True, extra=CUT)
    p.lathe([(1.75, 0.05), (1.75, 0.95)], 12, "darkwood", grain=None, group="soil")
    p.lathe([(0.34, 0.9), (0.26, 2.2)], 8, "wood", grain="z", group="trunk")
    p.lathe([(0.7, 1.7), (1.9, 2.6), (2.2, 4.6), (1.95, 7.6), (1.3, 10.6), (0.6, 12.8), (0.12, 14.2)], 10, "leaf",
            grain=None, group="flame", smooth=True, extra={**CUT, "tone": -2})
    rng = random.Random(3)
    for i in range(9):                                                  # tufts breaking the outline
        z = rng.uniform(2.6, 11.5)
        reach = 2.15 - 0.15 * max(z - 5, 0) + rng.uniform(-0.2, 0.1)
        turn = rng.uniform(0, 6.28)
        _clump(p, (reach * math.cos(turn), reach * math.sin(turn), z), rng.uniform(0.6, 0.95), "leaf", f"tuft{i}", rng, 1.2)


def palm_bed(p):
    """A date palm in a raised stone bed, flowering shrubs round its foot. The bed fills most of a grid cell."""
    a, h = 3.0, 1.5
    p.box((-a, -a, 0), (a, a, h), "stone", bevel=0.08, group="bed", band=True, extra=CUT)
    p.box((-a - 0.14, -a - 0.14, h), (a + 0.14, a + 0.14, h + 0.3), "stone", bevel=0.05, group="rim", extra={**CUT, "tone": 3})
    p.box((-a + 0.4, -a + 0.4, h + 0.3), (a - 0.4, a - 0.4, h + 0.42), "darkwood", group="soil")
    # the trunk: stacked rings, leaning a little as it climbs
    z, x = h + 0.42, 0.0
    for i in range(7):
        rise = 1.25
        p.lathe([(0.5, 0.0), (0.62, rise * 0.75), (0.5, rise)], 8, "wood", grain="z", group=f"ring{i}",
                frame=Matrix.Translation((x, 0.1 * i, z)), extra={"tone": (i % 3) - 1})
        z += rise - 0.06
        x += 0.14
    crown = Vector((x, 0.7, z))
    rng = random.Random(4)
    for i in range(9):                                                  # fronds: long leaves arching out and down
        turn = 2 * math.pi * i / 9 + rng.uniform(-0.2, 0.2)
        out, length, droop = Vector((math.cos(turn), math.sin(turn), 0)), rng.uniform(4.6, 5.8), rng.uniform(2.2, 3.4)
        side = Vector((-out.y, out.x, 0))
        rings = []
        for k in range(6):
            s = k / 5
            mid = crown + out * (length * s) + Vector((0, 0, 1.3 * math.sin(math.pi * s * 0.6) - droop * s * s))
            w = 0.75 * math.sin(math.pi * (0.12 + 0.88 * s) ) + 0.05
            rings.append([tuple(mid - side * w), tuple(mid + Vector((0, 0, 0.1))), tuple(mid + side * w),
                          tuple(mid - Vector((0, 0, 0.08)))])
        p.loft(rings, "leaf", group=f"frond{i}", soft=True, extra={"tone": rng.randint(-1, 1)})
    for i, (sx, sy) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (-1, 0))):
        _clump(p, (sx * 1.9 + rng.uniform(-0.2, 0.2), sy * 1.9 + rng.uniform(-0.2, 0.2), h + 1.5), rng.uniform(1.2, 1.5),
               "bloom" if i in (1, 4) else "leaf", f"shrub{i}", rng)


def potted(p):
    """A plant in a clay pot, for a doorstep or a windowsill."""
    p.lathe([(0.5, 0.0), (0.62, 0.15), (0.8, 1.0), (0.86, 1.25), (0.72, 1.25), (0.66, 1.05)], 10, "clay", grain=None,
            group="pot", smooth=True, extra=CUT)
    rng = random.Random(6)
    for i, (x, y, z, r, mat) in enumerate(((0.0, 0.0, 2.3, 0.85, "leaf"), (0.5, 0.2, 1.8, 0.6, "leaf"), (-0.45, -0.25, 1.9, 0.6, "leaf"),
                                         (0.1, -0.5, 2.6, 0.5, "bloom"), (-0.3, 0.45, 2.75, 0.45, "bloom"), (0.35, 0.4, 3.0, 0.45, "leaf"))):
        _clump(p, (x, y, z), r, mat, f"clump{i}", rng)

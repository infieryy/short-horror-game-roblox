"""Shared cloth toolkit: awnings, stall roofs and hanging cloths are made of strips.

A strip is a thin closed sheet that follows a path. Stripes are strips side by side in two
colours, so the pattern is modelled, never painted."""
import math

from mathutils import Vector

COLOURS = ("canvas", "redcloth")


def strip(p, path, x0, x1, thickness, mat, group=None, extra=None, pleat=(0.0, 0.0)):
    """A sheet from x0 to x1 following `path`, a list of (y, z) points. Strokes run along the path.
    `pleat` pushes the x0 edge and the x1 edge along Y by different amounts, for a folded sheet."""
    rings = []
    for k, (y, z) in enumerate(path):
        ay, az = path[max(k - 1, 0)]
        by, bz = path[min(k + 1, len(path) - 1)]
        along = Vector((by - ay, bz - az)).normalized()
        out = Vector((-along.y, along.x)) * (thickness / 2)                 # across the sheet
        fold = 0.0 if k == 0 else 1.0                                       # folds open out below the top edge
        y0, y1 = y + pleat[0] * fold, y + pleat[1] * fold
        rings.append([(x0, y0 - out.x, z - out.y), (x1, y1 - out.x, z - out.y),
                      (x1, y1 + out.x, z + out.y), (x0, y0 + out.x, z + out.y)])
    start, end = Vector(path[0]), Vector(path[-1])
    grain = "z" if abs(end.y - start.y) > abs(end.x - start.x) else "y"     # which way the cloth hangs
    return p.loft(rings, mat, group=group or mat, grain=grain, extra={"cut": True, **(extra or {})})


def sag(a, b, drop, steps=6):
    """Path from a to b (both (y, z)) that hangs `drop` studs in the middle."""
    return [(a[0] + (b[0] - a[0]) * k / steps, a[1] + (b[1] - a[1]) * k / steps - drop * math.sin(math.pi * k / steps))
            for k in range(steps + 1)]


def stripes(p, path, x0, x1, count, thickness=0.07, lod=False):
    """`count` strips side by side, alternating colours, each sagging a little differently."""
    width = (x1 - x0) / count
    for i in range(count):
        mat = COLOURS[i % 2]
        dip = 0.04 * ((i * 7) % 3 - 1)                                       # no two stripes hang quite alike
        strip(p, [(y, z - dip * math.sin(math.pi * k / (len(path) - 1))) for k, (y, z) in enumerate(path)],
              x0 + i * width, x0 + (i + 1) * width, thickness, mat)


def pleated(p, path, x0, x1, folds, depth, thickness, mat):
    """One sheet hanging in `folds` upright pleats, each `depth` studs deep."""
    width = (x1 - x0) / folds
    for i in range(folds):
        a, b = (depth if i % 2 else -depth) / 2, (-depth if i % 2 else depth) / 2
        strip(p, path, x0 + i * width, x0 + (i + 1) * width, thickness, mat, pleat=(a, b))

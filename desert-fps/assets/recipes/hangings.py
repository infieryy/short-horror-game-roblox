"""What hangs on the tea house: its sign, a banner and the bougainvillea that grows over a wall top.
The sign and the banner carry painted emblems (lines in a second colour)."""
import math
import random

from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix

from . import drape


def sign(p):
    """A board on an iron arm, square to the wall, with a tea glass painted on both faces.
    The origin is on the wall face at the arm."""
    p.box((-0.3, -0.06, -0.55), (0.3, 0.0, 0.3), "iron", group="plate")
    p.box((-0.05, -2.9, -0.02), (0.05, -0.06, 0.08), "iron", group="arm")
    a, b = (-0.06, -0.5), (-0.9, -0.02)                                # brace, as (y, z)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    p.box((-length / 2, -0.035, -0.035), (length / 2, 0.035, 0.035), "iron", group="brace",
          frame=frame_axes((0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (0, b[0] - a[0], b[1] - a[1]), (1, 0, 0)))
    for y in (-2.4, -1.0):
        p.box((-0.03, y - 0.03, -0.45), (0.03, y + 0.03, -0.02), "iron", group="link")
    p.box((-0.09, -2.75, -2.6), (0.09, -0.65, -0.45), "wood", bevel=0.03, grain="y", group="board")
    cy = -1.7
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.09, sx * 0.12))
        face = p.box((xa, -2.6, -2.45), (xb, -0.8, -0.6), "canvas", group=f"face{sx}")
        facet, x = ("+x", xb) if sx > 0 else ("-x", xa)

        def line(points, family, width, closed=False):
            p.mark(face, facet, [(x, y, z) for y, z in points], width=width, closed=closed, family=family)

        line([(cy - 0.5, -1.25), (cy - 0.42, -1.75), (cy - 0.2, -1.95), (cy + 0.2, -1.95), (cy + 0.42, -1.75),
              (cy + 0.5, -1.25)], "redcloth", 0.1, closed=True)
        line([(cy - 0.65, -2.12), (cy + 0.65, -2.12)], "redcloth", 0.09)
        line([(cy + 0.5, -1.35), (cy + 0.75, -1.42), (cy + 0.75, -1.65), (cy + 0.45, -1.72)], "redcloth", 0.08)
        for dy in (-0.18, 0.14):
            line([(cy + dy, -1.1), (cy + dy + 0.1, -0.98), (cy + dy - 0.04, -0.86), (cy + dy + 0.08, -0.74)], "band", 0.07)


def _board(p):
    """The hanging board every trade sign shares: iron arm and brace, two links, a wooden board square to the
    wall with a canvas face on each side. Returns [(face part, facet, x of the face)]."""
    p.box((-0.3, -0.06, -0.55), (0.3, 0.0, 0.3), "iron", group="plate")
    p.box((-0.05, -2.9, -0.02), (0.05, -0.06, 0.08), "iron", group="arm")
    a, b = (-0.06, -0.5), (-0.9, -0.02)
    length = math.hypot(b[0] - a[0], b[1] - a[1])
    p.box((-length / 2, -0.035, -0.035), (length / 2, 0.035, 0.035), "iron", group="brace",
          frame=frame_axes((0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (0, b[0] - a[0], b[1] - a[1]), (1, 0, 0)))
    for y in (-2.4, -1.0):
        p.box((-0.03, y - 0.03, -0.45), (0.03, y + 0.03, -0.02), "iron", group="link")
    p.box((-0.09, -2.75, -2.6), (0.09, -0.65, -0.45), "wood", bevel=0.03, grain="y", group="board")
    faces = []
    for sx in (-1, 1):
        xa, xb = sorted((sx * 0.09, sx * 0.12))
        face = p.box((xa, -2.6, -2.45), (xb, -0.8, -0.6), "canvas", group=f"face{sx}")
        faces.append((face, "+x" if sx > 0 else "-x", xb if sx > 0 else xa))
    return faces


EMBLEMS = {
    # each: (points as (y, z) round the board's middle at (-1.7, -1.5), colour family, line width, closed)
    "pot": [([(-0.42, 0.55), (-0.3, 0.3), (-0.62, -0.1), (-0.5, -0.6), (0.5, -0.6), (0.62, -0.1), (0.3, 0.3), (0.42, 0.55)],
             "redcloth", 0.11, True),
            ([(-0.5, -0.05), (-0.25, 0.1), (0.0, -0.05), (0.25, 0.1), (0.5, -0.05)], "band", 0.08, False),
            ([(-0.55, -0.75), (0.55, -0.75)], "redcloth", 0.09, False)],
    "cloth": [([(-0.65, 0.55), (0.65, 0.55)], "redcloth", 0.12, False),
              ([(-0.55, 0.45), (-0.55, -0.7), (0.55, -0.7), (0.55, 0.45)], "indigo", 0.1, False),
              ([(-0.55, 0.1), (-0.28, -0.1), (0.0, 0.1), (0.28, -0.1), (0.55, 0.1)], "saffron", 0.09, False),
              ([(-0.55, -0.3), (-0.28, -0.5), (0.0, -0.3), (0.28, -0.5), (0.55, -0.3)], "redcloth", 0.09, False)],
    "drop": [([(0.0, 0.7), (0.36, 0.05), (0.42, -0.3), (0.26, -0.6), (0.0, -0.7), (-0.26, -0.6), (-0.42, -0.3), (-0.36, 0.05)],
              "indigo", 0.12, True),
             ([(0.0, 0.25), (0.16, -0.25), (0.0, -0.42), (-0.16, -0.25)], "band", 0.14, True),
             ([(-0.6, -0.85), (-0.3, -0.75), (0.0, -0.85), (0.3, -0.75), (0.6, -0.85)], "indigo", 0.08, False)],
    "bread": [([(-0.62, -0.15), (-0.45, 0.3), (0.0, 0.48), (0.45, 0.3), (0.62, -0.15), (0.45, -0.5), (-0.45, -0.5)],
               "saffron", 0.12, True),
              ([(-0.3, 0.25), (-0.15, -0.3)], "redcloth", 0.08, False), ([(0.0, 0.32), (0.1, -0.3)], "redcloth", 0.08, False),
              ([(0.3, 0.25), (0.35, -0.25)], "redcloth", 0.08, False)],
}


def sign(p, emblem):
    """A trade sign: the hanging board with one emblem painted on both faces (a pot, a cloth, a drop, a loaf).
    The origin is on the wall face at the arm."""
    cy, cz = -1.7, -1.52
    for face, facet, x in _board(p):
        for points, family, width, closed in EMBLEMS[emblem]:
            p.mark(face, facet, [(x, cy + y, cz + z) for y, z in points], width=width, closed=closed, family=family)


def sign_dye(p):
    """The dyers' sign: a framed panel flat on a wall with three hanging flasks of dye painted on it, as on the
    concept's Dye Works. The origin is on the wall face, at the middle of the panel."""
    w, h = 2.7, 1.9
    p.box((-w - 0.2, -0.16, -h - 0.2), (w + 0.2, 0.0, h + 0.2), "wood", bevel=0.04, grain="x", group="frame")
    face = p.box((-w, -0.21, -h), (w, -0.16, h), "canvas", group="face")
    y = -0.21

    def line(points, family, width, closed=False, tone=None):
        if family:
            p.mark(face, "-y", [(x, y, z) for x, z in points], width=width, closed=closed, family=family)
        else:
            p.mark(face, "-y", [(x, y, z) for x, z in points], width=width, closed=closed, tone=tone)

    line([(-w + 0.4, h - 0.35), (w - 0.4, h - 0.35)], None, 0.09, tone=-5)                 # the rod they hang from
    for cx, family in ((-1.6, "redcloth"), (0.0, "saffron"), (1.6, "indigo")):
        cz = -0.45
        line([(cx, h - 0.35), (cx, cz + 1.05)], None, 0.05, tone=-5)                         # cord
        for radius, width in ((0.62, 0.2), (0.34, 0.26), (0.1, 0.2)):                         # the body, filled in rings
            ring = [(cx + radius * math.cos(math.radians(a)), cz + radius * 1.1 * math.sin(math.radians(a)))
                    for a in range(0, 360, 30)]
            line(ring, family, width, closed=True)
        line([(cx - 0.16, cz + 0.6), (cx - 0.13, cz + 1.0)], family, 0.12)                    # the neck
        line([(cx + 0.16, cz + 0.6), (cx + 0.13, cz + 1.0)], family, 0.12)
        line([(cx - 0.26, cz + 1.05), (cx + 0.26, cz + 1.05)], family, 0.11)                  # the lip


def banner(p):
    """A long red banner on a pole, flat against the wall, with a brass-yellow emblem.
    The origin is on the wall face at the pole."""
    w, drop = 1.0, 5.2
    p.box((-w - 0.25, -0.3, -0.08), (w + 0.25, -0.14, 0.08), "wood", bevel=0.03, grain="x", group="pole")
    for sx in (-1, 1):
        p.box((sx * (w + 0.12) - 0.04, -0.14, -0.04), (sx * (w + 0.12) + 0.04, 0.0, 0.04), "iron", group="bracket")
    cloth = drape.strip(p, [(-0.22, -0.02), (-0.17, -drop * 0.5), (-0.2, -drop)], -w, w, 0.07, "redcloth", group="cloth")
    drape.strip(p, [(-0.2, -drop), (-0.2, -drop - 0.32)], -w, w, 0.07, "canvas", group="hem")
    y, zc = -0.26, -drop * 0.42

    def line(points, width, closed=False):
        p.mark(cloth, "-y", [(x, y, z) for x, z in points], width=width, closed=closed, family="brass")

    for size, width in ((0.62, 0.11), (0.3, 0.09)):
        line([(0, zc + size * 1.3), (size, zc), (0, zc - size * 1.3), (-size, zc)], width, closed=True)
    for sx in (-1, 1):
        line([(sx * (w - 0.16), -0.35), (sx * (w - 0.16), -drop + 0.3)], 0.07)
    n = 8
    line([(-w + 0.25 + k * (2 * w - 0.5) / n, -drop + (0.75 if k % 2 else 0.45)) for k in range(n + 1)], 0.07)
    line([(-w + 0.25 + k * (2 * w - 0.5) / n, -0.9 + (0.0 if k % 2 else 0.3)) for k in range(n + 1)], 0.07)


L, B = "leaf", "bloom"


def bougainvillea(p):
    """Small clumps of flower and leaf spilling over a wall top and down its face, wide at the top and
    thinning out below. The origin is on the top front edge of the wall; the wall is on the +Y side."""
    rng = random.Random(5)
    for i in range(64):
        t = rng.random() ** 1.3                                        # 0 = on the wall top, 1 = the lowest trail
        down, half = t ** 1.5 * 3.6, 3.3 * (1 - 0.8 * t)
        on_top = down < 0.25
        x = rng.uniform(-half, half)
        y = rng.uniform(-0.1, 0.45) if on_top else rng.uniform(-0.6, -0.42)
        z = rng.uniform(0.12, 0.42) if on_top else -down
        r = rng.uniform(0.38, 0.66)
        mat = B if rng.random() < 0.8 else L
        profile = [(r * math.sin(math.radians(a)), -0.6 * r * math.cos(math.radians(a))) for a in (20, 55, 90, 125, 160)]
        frame = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z")
                 @ Matrix.Rotation(rng.uniform(-0.5, 0.5), 4, "X"))
        p.lathe(profile, 8, mat, grain=None, group=f"clump{i}", frame=frame, smooth=True, extra={"tone": rng.randint(-1, 1)})

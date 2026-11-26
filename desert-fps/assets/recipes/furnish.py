"""What stands in the tea house: a rug, a low table laid for tea, a built-in bench with cushions, a wall
shelf of jars and the counter with its samovar. Patterns are painted lines in a second colour."""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix

CUT = {"cut": True}


def _turned(p, profile, at, mat, group, scale=1.0, segments=10, **more):
    """A small turned object (a jar, a cup) standing at `at`; the profile is (radius, height above `at`)."""
    return p.lathe([(r * scale, z * scale) for r, z in profile], segments, mat, grain=None, group=group, smooth=True,
                   frame=Matrix.Translation(at), **more)


CUP = [(0.07, 0.0), (0.11, 0.08), (0.13, 0.18), (0.1, 0.16)]
JAR = [(0.18, 0.0), (0.3, 0.15), (0.32, 0.45), (0.2, 0.62), (0.23, 0.72)]
BOWL = [(0.16, 0.0), (0.34, 0.2), (0.36, 0.3), (0.3, 0.26)]
TIN = [(0.22, 0.0), (0.22, 0.5), (0.1, 0.58), (0.06, 0.7)]


def rug(p):
    w, d, t = 3.0, 2.0, 0.07
    pid = p.box((-w, -d, 0), (w, d, t), "redcloth", group="rug")

    def border(inset, family, width):
        p.mark(pid, "+z", [(-w + inset, -d + inset, t), (w - inset, -d + inset, t), (w - inset, d - inset, t),
                           (-w + inset, d - inset, t)], width=width, closed=True, family=family)

    border(0.22, "canvas", 0.14)
    border(0.5, "band", 0.09)
    for cx in (-1.45, 0.0, 1.45):
        for size, family, width in ((0.62, "canvas", 0.12), (0.3, "band", 0.1)):
            p.mark(pid, "+z", [(cx - size, 0, t), (cx, size * 1.3, t), (cx + size, 0, t), (cx, -size * 1.3, t)],
                   width=width, closed=True, family=family)
    for sx in (-1, 1):                                                 # a zigzag across each end
        x, n = sx * (w - 0.85), 10
        p.mark(pid, "+z", [(x + (0.13 if k % 2 else -0.13), -d + 0.75 + k * (2 * d - 1.5) / n, t) for k in range(n + 1)],
               width=0.08, family="canvas")
        for k in range(12):                                            # fringe
            y = -d + (k + 0.5) * 2 * d / 12
            xa, xb = sorted((sx * w, sx * (w + 0.24)))
            p.box((xa, y - 0.05, 0), (xb, y + 0.05, 0.03), "canvas", group="fringe", detail=True)


def tea_table(p):
    p.lathe([(0.55, 0.0), (0.6, 0.12), (0.3, 0.45), (0.3, 0.75), (0.5, 0.95)], 8, "darkwood", grain="z", group="leg",
            extra=CUT)
    p.lathe([(1.2, 0.95), (1.3, 1.0), (1.3, 1.12), (1.22, 1.16)], 8, "wood", grain=None, group="top", extra=CUT)
    p.lathe([(0.82, 1.16), (0.9, 1.26), (0.84, 1.26), (0.78, 1.2)], 12, "brass", grain=None, group="tray")
    pot = (-0.2, 0.1, 1.2)
    _turned(p, [(0.2, 0.0), (0.36, 0.12), (0.4, 0.32), (0.26, 0.54), (0.12, 0.6), (0.17, 0.67), (0.06, 0.76)], pot,
            "brass", "pot")
    p.box((-0.24, -0.045, -0.045), (0.24, 0.045, 0.045), "brass", group="spout",
          frame=frame_axes((pot[0] + 0.45, pot[1], 1.55), (1, 0, 0.8), (0, 1, 0)))
    p.box((pot[0] - 0.52, pot[1] - 0.04, 1.4), (pot[0] - 0.36, pot[1] + 0.04, 1.75), "brass", group="handle")
    for i, (x, y) in enumerate(((0.45, -0.3), (0.5, 0.25), (0.1, -0.5))):
        _turned(p, CUP, (x, y, 1.2), "band", f"cup{i}", segments=8)


def _pillow(p, centre, size, mat, group, turn=0.0, tilt=0.0, tone=0):
    """A stuffed cushion `size` (long, deep, high), lying along its length."""
    rings_n, around = (5, 8) if p.lod else (7, 12)
    rings = []
    for k in range(rings_n):
        t = k / (rings_n - 1)
        swell = math.sin(math.pi * t) ** 0.5
        a, b = size[1] / 2 * (0.72 + 0.28 * swell), size[2] / 2 * (0.45 + 0.55 * swell)
        ring = []
        for j in range(around):
            ang = 2 * math.pi * j / around
            c, s = math.cos(ang), math.sin(ang)
            ring.append(((t - 0.5) * size[0], math.copysign(abs(c) ** 0.6, c) * a, math.copysign(abs(s) ** 0.6, s) * b))
        rings.append(ring)
    frame = (Matrix.Translation(centre) @ Matrix.Rotation(math.radians(turn), 4, "Z")
             @ Matrix.Rotation(math.radians(tilt), 4, "X"))
    p.loft(rings, mat, group=group, frame=frame, soft=True, extra={"tone": tone})


def divan(p):
    """A plaster bench one grid cell long, built against a wall (the wall is on the +Y side)."""
    h = 1.25
    p.box((-3.9, -1.2, 0), (3.9, 1.2, h), "plaster", bevel=0.08, group="bench", extra={**CUT, "tone": 1})
    p.box((-3.9, -1.27, h - 0.32), (3.9, -1.2, h - 0.06), "wood", grain="x", group="trim", extra=CUT)
    _pillow(p, (0, -0.1, h + 0.22), (7.5, 2.0, 0.5), "redcloth", "seat")
    for i, x in enumerate((-2.85, -0.95, 0.95, 2.85)):
        _pillow(p, (x, 0.74, h + 1.02), (1.7, 0.55, 1.25), ("band", "canvas")[i % 2], f"back{i}", tilt=-12,
                tone=(i * 2) % 3 - 1)


def shelf(p):
    """Two boards on brackets with jars, bowls and tea tins. The origin is on the wall face, under the lower board."""
    for i, z in enumerate((0.0, 1.75)):
        p.box((-2.4, -0.9, z), (2.4, 0.0, z + 0.14), "wood", bevel=0.02, grain="x", group=f"board{i}", extra=CUT)
        for sx in (-2.1, 2.1):
            p.box((sx - 0.07, -0.75, z - 0.5), (sx + 0.07, 0.0, z), "darkwood", grain="z", group="bracket")
    rows = [(0.14, [(-1.9, JAR, "clay", 1.0), (-1.2, TIN, "brass", 1.0), (-0.5, JAR, "band", 0.9), (0.3, BOWL, "clay", 1.0),
                    (1.0, JAR, "clay", 1.2), (1.8, TIN, "band", 0.9)]),
            (1.89, [(-1.7, BOWL, "band", 1.0), (-0.9, JAR, "clay", 1.0), (0.0, JAR, "band", 1.15), (0.9, TIN, "brass", 1.0),
                    (1.7, JAR, "clay", 0.95)])]
    for r, (z, things) in enumerate(rows):
        for i, (x, profile, mat, scale) in enumerate(things):
            _turned(p, profile, (x, -0.45, z), mat, f"thing{r}{i}", scale)


def counter(p):
    """The tea counter: plank front, dark top, a samovar, a tray of cups and a bowl."""
    p.box((-2.55, -0.75, 0), (2.55, 0.75, 0.25), "stone", group="kick", extra=CUT)
    body = p.box((-2.5, -0.7, 0.25), (2.5, 0.7, 2.7), "wood", grain="z", group="body", extra=CUT)
    for k in range(1, 10):
        x = -2.5 + 0.5 * k
        for y, facet in ((-0.7, "-y"), (0.7, "+y")):
            p.mark(body, facet, [(x, y, 0.3), (x, y, 2.65)], tone=-3, width=0.045)
    p.box((-2.5, -0.76, 2.15), (2.5, -0.7, 2.42), "band", group="strip")
    p.box((-2.75, -0.95, 2.7), (2.75, 0.95, 2.95), "darkwood", bevel=0.04, grain="x", group="top", extra=CUT)
    top = 2.95
    _turned(p, [(0.3, 0.0), (0.34, 0.1), (0.2, 0.25), (0.42, 0.5), (0.46, 1.05), (0.3, 1.35), (0.14, 1.45), (0.2, 1.57),
                (0.07, 1.75)], (-1.7, 0.0, top), "brass", "samovar", segments=12)
    p.box((-1.7 - 0.04, -0.62, top + 0.55), (-1.7 + 0.04, -0.42, top + 0.63), "brass", group="tap")
    for s in (-1, 1):
        xa, xb = sorted((-1.7 + s * 0.44, -1.7 + s * 0.6))
        p.box((xa, -0.04, top + 0.7), (xb, 0.04, top + 1.0), "brass", group="ears")
    p.lathe([(0.62, top), (0.7, top + 0.08), (0.64, top + 0.08), (0.6, top + 0.04)], 12, "brass", grain=None, group="tray",
            frame=Matrix.Translation((0.2, 0.0, 0.0)))
    for i, (x, y) in enumerate(((0.0, -0.2), (0.4, -0.25), (0.45, 0.2), (0.0, 0.25))):
        _turned(p, CUP, (x, y, top + 0.04), "band", f"cup{i}", segments=8)
    _turned(p, BOWL, (1.75, 0.1, top), "clay", "bowl", 1.5)

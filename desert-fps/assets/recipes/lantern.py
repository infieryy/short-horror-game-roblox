"""Lantern: an iron frame round a box of warm glass. One hangs on a chain from a ceiling or a beam (the
origin is where the chain is fixed); the other hangs from an iron arm on a wall (the origin is on the
wall face). The glass is a part of its own, so the game can make it glow."""
import math

from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix


def build(p, wall=False):
    oy, top, chain = (-1.15, -0.1, 0.45) if wall else (0.0, 0.0, 1.5)
    if wall:
        p.box((-0.3, -0.06, -0.6), (0.3, 0.0, 0.25), "iron", group="plate")
        p.box((-0.05, oy - 0.12, -0.1), (0.05, -0.06, 0.0), "iron", group="arm")
        a, b = (-0.06, -0.52), (oy + 0.25, -0.1)                        # the brace under the arm, as (y, z)
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        frame = frame_axes((0, (a[0] + b[0]) / 2, (a[1] + b[1]) / 2), (0, b[0] - a[0], b[1] - a[1]), (1, 0, 0))
        p.box((-length / 2, -0.035, -0.035), (length / 2, 0.035, 0.035), "iron", group="brace", frame=frame)
    zt = top - chain                                                   # top of the cap
    p.box((-0.035, oy - 0.035, zt), (0.035, oy + 0.035, top), "iron", group="chain")
    square = Matrix.Translation((0, oy, 0)) @ Matrix.Rotation(math.radians(45), 4, "Z")
    p.lathe([(0.1, zt), (0.2, zt - 0.06), (0.78, zt - 0.36), (0.78, zt - 0.44)], 4, "iron", grain=None, group="cap",
            frame=square)
    g, z1 = 0.42, zt - 0.44
    z0 = z1 - 1.15
    p.box((-g, oy - g, z0), (g, oy + g, z1), "glow", group="glass", extra={"chunk": "glass"})
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * 0.46 - 0.05, oy + sy * 0.46 - 0.05, z0), (sx * 0.46 + 0.05, oy + sy * 0.46 + 0.05, z1), "iron",
                  group="bars")
    zm = (z0 + z1) / 2
    for s in (-1, 1):
        ya, yb = sorted((oy + s * g, oy + s * (g + 0.05)))
        p.box((-g, ya, zm - 0.04), (g, yb, zm + 0.04), "iron", group="rails")
        xa, xb = sorted((s * g, s * (g + 0.05)))
        p.box((xa, oy - g, zm - 0.04), (xb, oy + g, zm + 0.04), "iron", group="rails")
    p.box((-0.52, oy - 0.52, z0 - 0.12), (0.52, oy + 0.52, z0), "iron", bevel=0.02, group="base")
    p.lathe([(0.03, z0 - 0.5), (0.12, z0 - 0.36), (0.07, z0 - 0.24), (0.2, z0 - 0.12)], 6, "brass", grain=None,
            group="drop", frame=Matrix.Translation((0, oy, 0)))

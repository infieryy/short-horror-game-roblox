"""Sack pile: seven grain sacks stacked three high. Low cover: it blocks movement, not the view.
Each sack is a pillow: fat in the middle, pinched flat at both ends."""
import math

import config as C
from mathutils import Matrix

K = C.KIT["sacks"]

# where each sack lies: x, y, layer, turn about Z in degrees, tilt in degrees
PILE = [(-1.5, -1.0, 0, 4, 0), (1.5, -0.95, 0, -5, 0), (-1.45, 1.0, 0, -3, 0), (1.55, 1.05, 0, 6, 0),
        (-0.95, 0.05, 1, 86, 0), (0.98, 0.0, 1, 95, 0), (0.05, 0.05, 2, 8, 5)]


def _sack(p, frame, tone, lod):
    rings_n, around = (6, 6) if lod else (9, 12)
    length, hw, hh = K["len"], K["w"] / 2, K["h"] / 2
    rings = []
    for k in range(rings_n):
        t = k / (rings_n - 1)
        swell = math.sin(math.pi * t)
        a = hw * (0.7 + 0.3 * swell ** 0.6)                    # the ends stay wide...
        b = hh * max(0.13, swell ** 0.55)                      # ...but go flat, like a sewn seam
        ring = []
        for j in range(around):
            ang = 2 * math.pi * j / around
            c, s = math.cos(ang), math.sin(ang)
            ring.append(((t - 0.5) * length, math.copysign(abs(c) ** 0.75, c) * a, math.copysign(abs(s) ** 0.75, s) * b))
        rings.append(ring)
    p.loft(rings, "burlap", frame=frame, soft=True, extra={"cut": True, "tone": tone})


def build(p):
    for index, (x, y, layer, turn, tilt) in enumerate(PILE):
        z = K["h"] * (0.46 + 0.8 * layer)
        frame = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(turn), 4, "Z")
                 @ Matrix.Rotation(math.radians(tilt), 4, "Y"))
        _sack(p, frame, (index * 2) % 3 - 1, p.lod)

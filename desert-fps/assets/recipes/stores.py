"""Stores: things kept in a pile.

bolts: dyed cloth rolled into bolts and stacked crosswise on a pallet, taller than a player. One grid cell.
It blocks the way and the view, in a dyer's yard or indoors."""
import math

from build import frame_axes  # build loads bpy before mathutils

DYES = ("redcloth", "saffron", "plum", "indigo", "canvas", "band")
GOODS = ("saffron", "redcloth", "leaf")


def baskets(p):
    """Three baskets of goods in a row: spice, dried peppers, greens. For a stall counter or a doorstep."""
    from mathutils import Matrix
    for i, x in enumerate((-1.25, 0.0, 1.25)):
        frame = Matrix.Translation((x, 0.12 * (i - 1), 0.0))
        p.lathe([(0.36, 0.0), (0.56, 0.5), (0.6, 0.62), (0.5, 0.62), (0.47, 0.5)], 10, "rope", grain=None, group=f"basket{i}",
                frame=frame, extra={"cut": True})
        p.lathe([(0.5, 0.5), (0.36, 0.78), (0.14, 0.95)], 8, GOODS[i], grain=None, group=f"heap{i}", frame=frame, smooth=True)


def bolts(p):
    half, r = 2.9, 0.56
    p.box((-half, -half, 0.0), (half, half, 0.22), "wood", grain="x", group="deck", extra={"cut": True})
    for i, x in enumerate((-2.2, 0.0, 2.2)):
        p.box((x - 0.3, -half, 0.22), (x + 0.3, half, 0.5), "darkwood", grain="y", group=f"runner{i}", extra={"cut": True})
    z, n = 0.5, 0
    for layer, count in enumerate((4, 4, 4, 3, 3, 2)):
        length = 5.4 - 0.25 * layer
        spread = (count - 1) * 1.2 / 2
        for k in range(count):
            off = -spread + k * 1.2 + (0.12 if (layer + k) % 2 else -0.08)
            # the frame's Z (X cross Y) runs along the bolt: east for even layers, north for odd ones
            if layer % 2 == 0:
                frame = frame_axes((-length / 2, off, z + r), (0, 1, 0), (0, 0, 1))
            else:
                frame = frame_axes((off, -length / 2, z + r), (0, 0, 1), (1, 0, 0))
            p.lathe([(r * 0.86, 0.0), (r, 0.12), (r, length - 0.12), (r * 0.86, length)], 10, DYES[n % len(DYES)], grain="z",
                    group=f"bolt{n}", frame=frame, smooth=True, extra={"tone": (n * 2) % 3 - 1})
            n += 1
        z += 2 * r * 0.93

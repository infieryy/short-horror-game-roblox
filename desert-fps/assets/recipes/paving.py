"""Paving: what the town stands on, one grid cell at a time. Not breakable.

Every stone is painted in its own tone of its colour family, with a cut joint round it, so a street reads
as laid stone by stone. The piece itself is one flat slab: the stones are paint, not geometry.

    flags    street paving: big uneven flagstones, a few creamier ones among the pink
    tiles    indoor floors: square clay tiles with a small turquoise tile set in at every crossing
    bricks   courts, yards and squares: paving bricks laid in pairs, basket-weave
    dyed     the dyers' yard: flagstones splashed with the four dyes
    drift    sand blown against the foot of a wall (the origin is on the wall face, at the ground)
"""
import math
import random

import config as C

K = C.KIT["ground"]
HALF = C.CELL / 2
SEAMS = [(0, -HALF), (0, HALF), (1, -HALF), (1, HALF)]


def _slab(p, mat):
    t = K["t"]
    return p.box((-HALF, -HALF, 0), (HALF, HALF, t), mat, group="ground"), t


def _stone(stones, p, pid, z, corners, tone, family=None, joint=0.06):
    stones.append({"poly": [(x, y, z) for x, y in corners], "tone": tone, "family": family})
    if joint:
        p.mark(pid, "+z", [(x, y, z) for x, y in corners], tone=-3, width=joint, closed=True)


def _flag_stones(rng, rows):
    """Uneven flagstones: rows of different depths, stones of different widths, the cuts a little askew."""
    depths = [rng.uniform(0.8, 1.25) for _ in range(rows)]
    scale = C.CELL / sum(depths)
    y, out = -HALF, []
    for depth in depths:
        y1 = y + depth * scale
        widths = []
        while sum(widths) < C.CELL:
            widths.append(rng.uniform(1.5, 3.3))
        cuts = [-HALF]
        for width in widths:
            cuts.append(cuts[-1] + width * C.CELL / sum(widths))
        cuts[-1] = HALF
        leans = [0.0] + [rng.uniform(-0.16, 0.16) for _ in cuts[1:-1]] + [0.0]
        for (a, la), (b, lb) in zip(zip(cuts, leans), zip(cuts[1:], leans[1:])):
            out.append([(a - la, y), (b - lb, y), (b + lb, y1), (a + la, y1)])
        y = y1
    return out


def flags(p, seed=1, rows=4, splashes=False):
    pid, t = _slab(p, "paving")
    rng = random.Random(seed)
    stones = []
    for corners in _flag_stones(rng, rows):
        cream = rng.random() < 0.22                              # now and then a creamier stone among the pink
        _stone(stones, p, pid, t, corners, rng.randint(-5, 4) if not cream else rng.randint(-2, 2), "stone" if cream else None, joint=0.08)
    if splashes:                                                 # spilt dye, soaked into the stones
        for family in ("redcloth", "indigo", "saffron", "plum"):
            for _ in range(2):
                cx, cy, r = rng.uniform(-3.0, 3.0), rng.uniform(-3.0, 3.0), rng.uniform(0.45, 1.15)
                turn = rng.uniform(0, 6.28)
                blot = [(cx + r * rng.uniform(0.6, 1.0) * math.cos(turn + k * math.pi / 5) * 1.3,
                         cy + r * rng.uniform(0.6, 1.0) * math.sin(turn + k * math.pi / 5)) for k in range(10)]
                stones.append({"poly": [(x, y, t) for x, y in blot], "tone": rng.randint(-1, 1), "family": family, "soft": 0.55})
    p.parts[pid]["stones"] = stones
    p.seams = SEAMS


def tiles(p):
    pid, t = _slab(p, "clay")
    rng = random.Random(4)
    n, stones = 4, []
    side = C.CELL / n
    for j in range(n):
        for i in range(n):
            x, y = -HALF + i * side, -HALF + j * side
            _stone(stones, p, pid, t, [(x, y), (x + side, y), (x + side, y + side), (x, y + side)],
                   (2 if (i + j) % 2 else -2) + rng.randint(-1, 1), joint=0.06)
    d = 0.27                                                     # the small turquoise tiles at the crossings
    for j in range(n + 1):
        for i in range(n + 1):
            x, y = -HALF + i * side, -HALF + j * side
            corners = [(x, y - d), (x + d, y), (x, y + d), (x - d, y)]
            corners = [(min(max(cx, -HALF), HALF), min(max(cy, -HALF), HALF)) for cx, cy in corners]
            stones.append({"poly": [(cx, cy, t) for cx, cy in corners], "tone": rng.randint(-1, 1), "family": "band"})
    p.parts[pid]["stones"] = stones
    p.seams = SEAMS


def bricks(p):
    pid, t = _slab(p, "paving")
    rng = random.Random(6)
    n, stones = 4, []
    side = C.CELL / n
    for j in range(n):
        for i in range(n):
            x, y = -HALF + i * side, -HALF + j * side
            for k in range(2):                                   # a pair of bricks, turned every other block
                if (i + j) % 2:
                    corners = [(x, y + k * side / 2), (x + side, y + k * side / 2), (x + side, y + (k + 1) * side / 2),
                               (x, y + (k + 1) * side / 2)]
                else:
                    corners = [(x + k * side / 2, y), (x + (k + 1) * side / 2, y), (x + (k + 1) * side / 2, y + side),
                               (x + k * side / 2, y + side)]
                cream = rng.random() < 0.3
                _stone(stones, p, pid, t, corners, rng.randint(-4, 3), "stone" if cream else None, joint=0.06)
    p.parts[pid]["stones"] = stones
    p.seams = SEAMS


def drift(p):
    """A low bank of sand, deepest in the middle, thinning to nothing at both ends and at the front."""
    length, depth, height, steps = 6.6, 1.9, 0.5, 9
    rings = []
    for k in range(steps):
        s = k / (steps - 1)
        fat = max(math.sin(math.pi * s) ** 0.7, 0.04)
        x = (s - 0.5) * length + 0.25 * math.sin(3.1 * s)
        d, h = depth * (0.35 + 0.65 * fat), height * fat
        rings.append([(x, 0.0, 0.0), (x, 0.0, h), (x, -d * 0.45, h * 0.55), (x, -d, 0.0)])
    p.loft(rings, "sand", group="sand", soft=True)

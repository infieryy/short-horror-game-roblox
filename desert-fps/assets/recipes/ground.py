"""Ground: one grid cell of flagstone paving. Not breakable. The joints between the stones are painted."""
import random

import config as C

K = C.KIT["ground"]
HALF = C.CELL / 2


def joints(p, pid, z, seed=7):
    """Paint the joints of a cell of flagstones on the top face (at height z) of part `pid`."""
    rng = random.Random(seed)
    rows = K["stones"]
    depth = C.CELL / rows
    for j in range(rows):
        y0 = -HALF + j * depth
        if j:                                               # the joint under this row, wandering a little
            xs = [-HALF + k * C.CELL / 6 for k in range(7)]
            p.mark(pid, "+z", [(x, y0 + rng.uniform(-0.07, 0.07), z) for x in xs], tone=-3, width=0.06)
        x = -HALF + rng.uniform(1.2, 2.6) * (0.5 if j % 2 else 1.0)
        while x < HALF - 0.8:
            lean = rng.uniform(-0.12, 0.12)
            p.mark(pid, "+z", [(x - lean, y0 + 0.04, z), (x + lean, y0 + depth - 0.04, z)], tone=-3, width=0.06)
            x += rng.uniform(1.5, 2.9)


def build(p):
    t = K["t"]
    pid = p.box((-HALF, -HALF, 0), (HALF, HALF, t), "paving", group="ground")
    joints(p, pid, t)
    p.seams = [(0, -HALF), (0, HALF), (1, -HALF), (1, HALF)]

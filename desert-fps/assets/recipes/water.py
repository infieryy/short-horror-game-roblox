"""Water for the Cistern Hall. The water is painted, flat and matte like everything else; it does not move.

spout    a stone spout on a wall, a sheet of water falling from it into a trough at its foot
         (the origin is on the wall face, at the ground)
"""
from . import drape

CUT = {"cut": True}


def spout(p):
    # the back: a stone slab on the wall with a panel of turquoise tile, as round a fountain
    p.box((-1.5, -0.2, 2.2), (1.5, 0.0, 6.8), "stone", bevel=0.05, group="back", extra={**CUT, "tone": 3})
    panel = p.box((-1.05, -0.26, 2.9), (1.05, -0.2, 6.2), "band", group="panel")
    teeth = 6
    p.mark(panel, "-y", [(-1.05 + k * 2.1 / (2 * teeth), -0.26, 5.75 if k % 2 == 0 else 6.05) for k in range(2 * teeth + 1)],
           width=0.08, family="canvas")
    p.box((-0.28, -0.85, 4.55), (0.28, -0.26, 5.0), "stone", bevel=0.04, group="lip", extra={**CUT, "tone": 2})
    # the falling water: a thin sheet from the lip into the trough
    drape.strip(p, [(-0.8, 4.7), (-0.98, 4.3), (-1.08, 3.0), (-1.1, 1.36)], -0.2, 0.2, 0.06, "water", group="fall")
    # the trough: a block of stone with a raised rim and the water lying in it
    p.box((-1.8, -2.0, 0.0), (1.8, 0.0, 1.2), "stone", bevel=0.06, group="trough", band=True, extra=CUT)
    for lo, hi, name in (((-1.8, -2.0, 1.2), (1.8, -1.72, 1.5), "front"), ((-1.8, -0.28, 1.2), (1.8, 0.0, 1.5), "rear"),
                         ((-1.8, -1.72, 1.2), (-1.52, -0.28, 1.5), "left"), ((1.52, -1.72, 1.2), (1.8, -0.28, 1.5), "right")):
        p.box(lo, hi, "stone", group=f"rim_{name}", extra={**CUT, "tone": 2})
    p.box((-1.52, -1.72, 1.2), (1.52, -0.28, 1.36), "water", group="pool", extra=CUT)

"""Roof / floor slab: one grid cell. A flat earth roof you can walk on, carried on three round beams
that line up with the beam ends on the wall pieces. Its top sits a hair above the wall tops it covers."""
import config as C
from build import frame_axes  # build loads bpy before mathutils

K = C.KIT["roof"]
HALF = C.CELL / 2


def build(p):
    p.box((-HALF, -HALF, 0), (HALF, HALF, K["t"]), "plaster", group="roof", extra={"cut": True})
    r, inner = K["beam_r"], HALF - C.WALL_T / 2
    for i in range(K["beams"]):
        x = -HALF + (i + 0.5) * C.CELL / K["beams"]
        frame = frame_axes((x, inner, -K["beam_drop"] + r), (1, 0, 0), (0, 0, 1))        # local Z runs along -Y
        p.lathe([(r, 0.0), (r, 2 * inner)], 10, "wood", frame=frame, grain="z", extra={"cut": True})
    p.seams = [(0, -HALF), (0, HALF), (1, -HALF), (1, HALF)]

"""Hanging cloth: a red sheet with a pale hem, slung over a pole that spans one grid cell between two
walls. Players walk through it; it only blocks the view."""
import config as C
from build import frame_axes  # build loads bpy before mathutils

from . import drape

K = C.KIT["cloth"]
HALF = C.CELL / 2


def build(p):
    z, hw, t = K["pole_z"], K["w"] / 2, K["t"]
    p.lathe([(0.17, 0.0), (0.17, C.CELL)], 8, "wood", grain="z", extra={"cut": True},
            frame=frame_axes((-HALF, 0, z), (0, 1, 0), (0, 0, 1)))
    for sx in (-1, 1):                                          # rope ties holding the sheet on the pole
        p.lathe([(0.3, 0.0), (0.3, 0.3)], 8, "rope", group="tie", detail=True,
                frame=frame_axes((sx * (hw - 0.5) - 0.15, 0, z), (0, 1, 0), (0, 0, 1)))
    bottom, hem = z - K["drop"], 1.3
    # a flap over the pole, then the sheet hanging in upright folds, then the pale hem
    drape.strip(p, [(0.24, z - 0.7), (0.25, z + 0.05), (0.0, z + 0.25), (-0.24, z + 0.06)], -hw, hw, t, "redcloth",
                group="flap")
    drape.pleated(p, [(-0.24, z + 0.06), (-0.26, z - 0.6), (-0.26, bottom + hem)], -hw, hw, K["folds"], K["fold_out"],
                  t, "redcloth")
    drape.pleated(p, [(-0.26, bottom + hem), (-0.26, bottom)], -hw, hw, K["folds"], K["fold_out"], t, "canvas")
    p.seams = [(0, -HALF), (0, HALF)]

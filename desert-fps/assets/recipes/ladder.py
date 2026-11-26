"""Ladder: two poles and round rungs lashed on with rope. Stands upright against a wall and reaches
a little above the roof edge of a one-story building."""
import config as C
from build import frame_axes  # build loads bpy before mathutils

K = C.KIT["ladder"]
CUT = {"cut": True}


def build(p):
    h, half, rail = K["h"], K["w"] / 2, K["rail"] / 2
    for side in (-1, 1):
        x = side * (half - rail)
        p.lathe([(rail * 1.08, 0.0), (rail, 0.6), (rail * 0.92, h - 0.08), (rail * 0.8, h)], 8, "darkwood",
                frame=frame_axes((x, 0, 0), (1, 0, 0), (0, 1, 0)), grain="z", extra=CUT)
    r = K["rung_h"] / 2
    z = 1.3
    while z < h - 0.6:
        frame = frame_axes((-half - 0.12, -rail - r * 0.6, z), (0, 1, 0), (0, 0, 1))      # local Z runs along +X
        p.lathe([(r, 0.0), (r, K["w"] + 0.24)], 6, "wood", frame=frame, grain="z", extra=CUT)
        for side in (-1, 1):
            x = side * (half - rail)
            p.box((x - rail - 0.04, -rail - 2 * r - 0.03, z - 0.14), (x + rail + 0.04, rail + 0.03, z + 0.14),
                  "rope", bevel=0.06, group="lash", detail=True)
        z += K["rung_gap"]

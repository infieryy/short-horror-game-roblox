"""Market stall: four posts on turquoise stone feet, a striped cloth roof sloping to the front with a
hanging valance, and a plank counter with a red runner. High cover: it blocks movement and most of the view."""
import config as C
from build import frame_axes  # build loads bpy before mathutils

from . import drape

K = C.KIT["stall"]
CUT = {"cut": True}


def build(p):
    hw, hd, post = K["w"] / 2, K["d"] / 2, K["post"] / 2
    tops = {-1: K["front_h"], 1: K["back_h"]}                  # front is -Y
    for sy in (-1, 1):
        for sx in (-1, 1):
            x, y = sx * (hw - post), sy * (hd - post)
            p.box((x - 0.36, y - 0.36, 0), (x + 0.36, y + 0.36, 0.6), "stone", bevel=0.06, band=True, extra=CUT)
            p.box((x - post, y - post, 0.6), (x + post, y + post, tops[sy]), "wood", bevel=0.04, grain="z", extra=CUT)
        # the pole the cloth lies on, along X
        frame = frame_axes((-hw - 0.3, sy * (hd - post), tops[sy] - 0.02), (0, 1, 0), (0, 0, 1))
        p.lathe([(0.15, 0.0), (0.15, K["w"] + 0.6)], 8, "wood", frame=frame, grain="z", extra=CUT)

    # roof: from the back pole down to the front pole, then the valance hanging off the front edge
    # (the cloth clears the poles: parts that are cut into shards may not run through each other)
    back, front = (hd - post + 0.35, K["back_h"] + 0.27), (-hd + post - 0.45, K["front_h"] + 0.27)
    path = drape.sag(back, front, 0.16)
    path += [(front[0] - 0.07, front[1] - 0.2), (front[0] - 0.1, front[1] - K["valance"])]
    drape.stripes(p, path, -hw - 0.35, hw + 0.35, K["stripes"])

    # counter along the front
    y0, y1, top = -hd + 0.5, -hd + 0.5 + K["counter_d"], K["counter_h"]
    x0, x1 = -hw + 0.75, hw - 0.75
    p.box((x0 - 0.15, y0 - 0.12, top - 0.24), (x1 + 0.15, y1 + 0.12, top), "wood", bevel=0.04, grain="x", extra=CUT)
    boards = 7
    for i in range(boards):
        a = x0 + i * (x1 - x0) / boards
        p.box((a + 0.02, y0, 0.12), (a + (x1 - x0) / boards - 0.02, y0 + 0.14 + (0.03 if i % 2 else 0), top - 0.24),
              "darkwood", grain="z", extra={"tone": -1 if i % 2 else 0, **CUT})
    for x in (x0 + 0.12, x1 - 0.12):
        p.box((x - 0.14, y1 - 0.3, 0), (x + 0.14, y1, top - 0.24), "wood", bevel=0.03, grain="z", extra=CUT)
    # runner over the counter, hanging down the front
    drape.strip(p, [(y1 - 0.2, top + 0.045), (y0 - 0.14, top + 0.045), (y0 - 0.21, top - 0.1), (y0 - 0.22, top - 1.25)],
                -1.2, 1.2, 0.06, "redcloth", group="runner")

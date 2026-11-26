"""Parapet: the low wall round a roof, one grid cell wide. Plain, or with square merlons.
It stands on top of a wall piece, so it has no plinth and no turquoise band."""
import config as C

K = C.KIT["parapet"]
HALF, T = C.CELL / 2, C.WALL_T / 2
CUT = {"cut": True}


def build(p, merlons=False):
    h, cap = K["h"], K["cap_h"]
    p.wall([-HALF, HALF], [0.0, h], lambda z: -T, lambda z: T, band=False, extra=CUT)
    p.box((-HALF, -T - K["cap_out"], h), (HALF, T + K["cap_out"], h + cap), "plaster", group="coping", extra=CUT)
    if merlons:
        w = K["merlon_w"] / 2
        for i in range(K["merlons"]):
            x = -HALF + (i + 0.5) * C.CELL / K["merlons"]
            p.box((x - w, -T, h + cap - 0.02), (x + w, T, h + cap + K["merlon_h"]), "plaster", bevel=0.07,
                  group="merlon", extra=CUT)
    p.seams = [(0, -HALF), (0, HALF), (2, 0.0)]


def build_corner(p):
    """The post where two runs of parapet meet at a roof corner."""
    a = T + K["cap_out"] + K["post_out"]
    p.box((-a, -a, 0), (a, a, K["h"] + K["cap_h"] + K["post_up"]), "plaster", bevel=0.07, group="wall",
          extra=CUT)
    p.seams = [(2, 0.0)]


def pierced(p):
    """A terrace balustrade: the same low wall with a row of small openings to look and shoot through."""
    h, cap, o = K["h"], K["cap_h"], K["pierced"]
    xs, holes = [-HALF], []
    for i in range(o["count"]):
        x = -HALF + (i + 0.5) * C.CELL / o["count"]
        xs += [x - o["w"] / 2, x + o["w"] / 2]
        holes.append((2 * i + 1, 1))
    xs.append(HALF)
    p.wall(xs, [0.0, o["z0"], o["z1"], h], lambda z: -T, lambda z: T, holes, band=False, extra=CUT)
    p.box((-HALF, -T - K["cap_out"], h), (HALF, T + K["cap_out"], h + cap), "stone", group="coping", extra=CUT)
    p.seams = [(0, -HALF), (0, HALF), (2, 0.0)]

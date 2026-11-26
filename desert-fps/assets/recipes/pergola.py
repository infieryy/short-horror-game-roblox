"""Pergola: one grid cell of shade for a roof terrace. Four posts, two beams, a row of slats and three
lengths of cloth thrown over them."""
import config as C

from . import drape

K = C.KIT["pergola"]
CUT = {"cut": True}


def build(p):
    h, post, a = K["h"], K["post"] / 2, K["inset"]
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((sx * a - post, sy * a - post, 0), (sx * a + post, sy * a + post, h), "wood", bevel=0.04, grain="z",
                  extra=CUT)
    for sy in (-1, 1):
        p.box((-4.2, sy * a - 0.22, h), (4.2, sy * a + 0.22, h + 0.45), "darkwood", bevel=0.04, grain="x", extra=CUT)
    n = K["slats"]
    for i in range(n):
        x = -3.5 + i * 7.0 / (n - 1)
        p.box((x - 0.14, -4.0, h + 0.45), (x + 0.14, 4.0, h + 0.7), "wood", grain="y", group=f"slat{i}", extra=CUT)
    top = h + 0.8
    path = [(-4.5, h - 0.2), (-4.15, top), (-2.0, top - 0.04), (0.0, top - 0.05), (2.0, top - 0.04), (4.15, top),
            (4.5, h - 0.2)]
    for x0, x1, mat in ((-3.3, -1.3, "canvas"), (-1.0, 1.0, "redcloth"), (1.3, 3.3, "canvas")):
        drape.strip(p, path, x0, x1, 0.07, mat, group=f"cloth{x0}")

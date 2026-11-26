"""Plank bridge: a board walk one grid cell long, between two roofs. Two joists carry loose boards
laid across them at slightly different heights."""
import config as C

K = C.KIT["plank"]
HALF = C.CELL / 2
CUT = {"cut": True}


def build(p):
    jw, jh = K["joist"]
    for side in (-1, 1):
        y = side * K["joist_y"]
        p.box((-HALF, y - jw / 2, 0), (HALF, y + jw / 2, jh), "darkwood", grain="x", extra=CUT)
    n, half = K["boards"], K["w"] / 2
    width = C.CELL / n
    for i in range(n):
        x0 = -HALF + i * width
        lift = 0.03 if i % 2 else 0.0
        over = 0.12 if i % 3 == 1 else 0.0                      # some boards stick out further than others
        p.box((x0 + 0.03, -half - over, jh - 0.01 + lift), (x0 + width - 0.03, half + over * 0.5, jh + K["board_t"] + lift),
              "wood", bevel=0.025, grain="y", extra={"tone": -1 if i % 2 else 0, **CUT})
    p.seams = [(0, -HALF), (0, HALF)]

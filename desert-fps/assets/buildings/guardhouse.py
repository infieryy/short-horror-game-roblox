"""The Guard House: one square hall where the gate guard eats, sleeps and keeps its arms, in the Gate Quarter.

Its walls come straight from the town plan (plan/town.py, rows 29-31, columns 9-11): 3 x 3 cells, a door at
two opposite corners. The plan lets a player walk through every cell, so everything keeps to the walls.

    the hall   the duty desk under the arms shelf, two bunks, the guards' stores, a rug in the middle
    the roof   a shaded lookout behind battlements

`python -m buildings.town` writes out/buildings/guardhouse.json with the rest of the town."""
from buildings.layout import FLOOR, ROOM, SLAB, STORY, Layout, footprint, shell

RECT = (29, 9, 31, 11)
TITLE = "GuardHouse"
G = FLOOR - 0.05


def placements():
    lay = Layout()
    rows, cell = footprint(rect=RECT)
    rooms = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch in ROOM]
    up = STORY + FLOOR

    for r, c in rooms:
        lay.at("paving_tiles", r, c, -0.49)
    edges, posts = shell(lay, rows, cell, dress={(1, 0, "W"): "shutter", (2, 1, "S"): "shutter"},
                         pilasters=[(0, 1), (0, 2), (3, 1), (3, 2), (1, 0), (2, 0), (1, 3), (2, 3)])
    for r, c in rooms:
        lay.at("floor", r, c, SLAB)
    for (r, c, side) in edges:
        lay.edge("parapet_crenel", r, c, side, STORY)
    for x, y in posts:
        lay.put("parapet_corner", x, y, STORY)

    # ---------------------------------------------------------------- the hall
    lay.against("counter", 0, 1, "N", 1.45, G)                          # the duty desk, the arms shelf over it
    lay.on_wall("shelf", 0, 1, "N", 5.4)
    lay.against("divan", 1, 2, "E", 1.7, G)                             # two bunks
    lay.against("divan", 1, 0, "W", 1.7, G)
    lay.against("crate", 2, 1, "S", 2.3, G, -1.6)                       # the guards' stores, under the window
    lay.against("barrel", 2, 1, "S", 2.1, G, 1.8)
    lay.at("pot_tall", 0, 0, G, 0, dx=-2.4, dy=2.4)                     # the water jar
    lay.at("pot_round", 2, 2, G, 0, dx=2.4, dy=-2.4)
    lay.at("rug", 1, 1, G, 0)
    for r, c in ((0, 0), (1, 1), (2, 2)):
        lay.at("lantern", r, c, 10.4)

    # ---------------------------------------------------------------- outside
    for r, c, side, along in ((0, 2, "N", -3.4), (0, 2, "E", 3.4), (2, 0, "W", 3.4), (2, 0, "S", -3.4)):
        lay.on_wall("lantern_wall", r, c, side, 8.6, along=along, outside=True)
    for r, c, side in ((0, 1, "N"), (1, 2, "E")):                       # the guard's colours
        lay.on_wall("banner", r, c, side, 9.7, outside=True)

    # ---------------------------------------------------------------- the roof: a shaded lookout
    lay.at("pergola", 1, 1, up)
    lay.at("rug", 1, 1, up)
    lay.against("crate", 0, 0, "N", 2.4, up, -1.6)
    lay.against("barrel", 0, 0, "N", 2.2, up, 1.7)
    lay.against("stack_crates", 2, 2, "S", 2.7, up)
    lay.against("divan", 2, 0, "W", 2.1, up)
    return lay.items

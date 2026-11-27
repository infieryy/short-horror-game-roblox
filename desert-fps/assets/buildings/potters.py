"""The Potters' Workshop: a U of open workrooms round the kiln yard, in the Potters' Quarter.

Its walls come straight from the town plan (plan/town.py, rows 4-7, columns 28-31): 4 x 4 cells, the yard
open to the south. You can walk through every room.

    north wing   the throwing room: the workbench under its shelf of finished pots
    west wing    the glaze store: a rack and crates fill its middle (the plan's high cover)
    east wing    drying and packing
    the yard     the kiln with its fire lit, racks of pots waiting to be fired, pots drying along the walls
    the roof     more pots drying in the sun

`python -m buildings.town` writes out/buildings/potters.json with the rest of the town."""
from buildings.layout import FLOOR, ROOM, SLAB, STEP, STORY, Layout, footprint, shell

RECT = (4, 28, 7, 31)
TITLE = "PottersWorkshop"
G = FLOOR - 0.05


def placements():
    lay = Layout()
    rows, cell = footprint(rect=RECT)
    rooms = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch in ROOM]
    yard = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch not in ROOM]
    up = STORY + FLOOR

    for r, c in rooms:
        lay.at("paving_tiles", r, c, -0.49)
    for r, c in yard:
        lay.at("paving_bricks", r, c, -0.49)
    shutters = [(0, 1, "N"), (0, 2, "S"), (2, 0, "W")]
    edges, posts = shell(lay, rows, cell, dress={key: "shutter" for key in shutters}, pilasters=[(0, 2), (2, 0), (2, 4)])
    for r, c in rooms:
        lay.at("floor", r, c, SLAB)
    for (r, c, side) in edges:
        dr, dc = STEP[side]
        to_yard = (r + dr, c + dc) in yard
        lay.edge("parapet_pierced" if to_yard else "parapet_plain", r, c, side, STORY)
    for x, y in posts:
        lay.put("parapet_corner", x, y, STORY)

    # ---------------------------------------------------------------- north wing: the throwing room
    lay.against("counter", 0, 2, "N", 1.45, G)                          # the workbench
    lay.on_wall("shelf", 0, 2, "N", 5.4)
    lay.at("pot_tall", 0, 3, G, 0, dx=2.4, dy=2.4)                      # finished jars in the corner
    lay.at("vase", 0, 3, G, 0, dx=0.4, dy=2.8)
    for along in (-2.0, 0.0):                                           # bowls under the window
        lay.against("vase", 0, 1, "N", 1.6, G, along)
    lay.at("barrel", 0, 0, G, 0, dx=2.4, dy=-2.3)                       # the clay barrel, by the door

    # ---------------------------------------------------------------- west wing: the glaze store
    lay.against("pot_rack", 2, 0, "W", 1.65, G)                         # with the crates, the plan's high cover
    lay.at("stack_crates", 2, 0, G, 90, dx=1.6)
    lay.at("barrel", 1, 0, G, 0, dx=-2.3, dy=-1.9)

    # ---------------------------------------------------------------- east wing: drying and packing
    lay.against("pot_rack", 2, 3, "E", 1.65, G)
    lay.on_wall("shelf", 2, 3, "W", 5.2)
    lay.at("baskets", 3, 3, G, 0, dx=0.6, dy=-2.9)
    lay.at("vase", 3, 3, G, 0, dx=2.8, dy=-2.7)

    for r, c in ((0, 0), (0, 2), (3, 0), (1, 3), (3, 3)):
        lay.at("lantern", r, c, 10.4)

    # ---------------------------------------------------------------- the yard
    lay.at("kiln", 1, 1, G, 0)                                          # its mouth looks down the yard
    lay.at("pot_rack", 3, 2, G, 0, dy=2.9)                              # two racks and a stack of crates: high cover
    lay.at("pot_rack", 3, 2, G, 180, dy=1.0)
    lay.at("stack_crates", 3, 2, G, 0, dy=-2.0)
    for piece, gap, along in (("pot_round", 2.0, -2.3), ("pot_tall", 2.0, 0.2), ("vase", 1.6, 2.5)):
        lay.against(piece, 1, 2, "N", gap, G, along)                    # pots drying along the workroom wall
    for along in (-1.5, 1.4):
        lay.against("pot_tall", 2, 1, "W", 2.0, G, along)
    lay.against("baskets", 2, 2, "E", 1.5, G, -0.8)
    lay.against("vase", 2, 2, "E", 1.6, G, 2.4)

    # ---------------------------------------------------------------- outside
    lay.on_wall("sign_pot", 3, 0, "S", 9.6, along=3.0, outside=True)
    for r, c, side, along in ((3, 0, "S", -3.4), (0, 0, "N", -3.4), (1, 3, "E", 3.4), (3, 0, "W", 3.4)):
        lay.on_wall("lantern_wall", r, c, side, 8.6, along=along, outside=True)
    for r, c, side in ((1, 0, "E"), (3, 3, "W")):                       # and two that light the yard
        lay.on_wall("lantern_wall", r, c, side, 8.6, along=3.3, outside=True)
    lay.on_wall("banner", 2, 3, "E", 9.7, outside=True)

    # ---------------------------------------------------------------- the roof: pots drying in the sun
    lay.against("pot_rack", 0, 1, "N", 1.8, up)
    for piece, gap, along in (("pot_tall", 2.1, -1.9), ("pot_round", 2.1, 0.6), ("vase", 1.7, 2.6)):
        lay.against(piece, 0, 3, "E", gap, up, along)
    for along in (-1.5, 1.5):
        lay.against("pot_tall", 2, 0, "W", 2.1, up, along)
    lay.against("pot_rack", 2, 3, "E", 1.8, up)
    for along in (-2.3, -0.4, 1.8):
        lay.against("vase", 3, 3, "S", 1.7, up, along)
    lay.against("baskets", 3, 0, "W", 1.5, up)
    return lay.items

"""The town wall: two stories of plaster and battlements all the way round, so that from no street and no roof
a player sees past the edge of the town. It stands in the ring of cells the plan keeps solid (plan/town.py).

A panel of wall fills every cell of the ring, its face half a stud into the street like the face of a house.
Square towers stand through it at the corners and along each side, never evenly spaced, and the town gate is
in the south wall at the end of the street through the Gate Quarter, between two of them.

`python -m buildings.town` writes out/buildings/townwall.json with the rest of the town."""
from buildings.layout import CELL, Layout

TITLE = "TownWall"
PANEL_IN = 1.25              # the middle of a wall panel, in from the street edge of its cell
TOWER_IN = 2.7               # a tower stands this far in, so its face is proud of the wall's
GATE = 8                     # the gate's column in the south wall: the street past the gatehouse ends at it
# Cells along each side that get a tower (the corners always do).
TOWERS = {"N": (7, 15, 24, 31), "S": (GATE - 2, GATE + 2, 17, 26, 33), "W": (6, 14, 21, 30), "E": (9, 17, 25, 33)}


def placements(n):
    lay = Layout()
    span, last = n * CELL, (n - 1) * CELL
    # (how far along the side, how far in from the street edge) -> where on the plan, for each side; and the
    # turn that makes a piece's front look into the town
    sides = {
        "N": (lambda along, depth: (along, -(CELL - depth)), 0),
        "S": (lambda along, depth: (along, -(last + depth)), 180),
        "W": (lambda along, depth: (CELL - depth, -along), 90),
        "E": (lambda along, depth: (last + depth, -along), -90),
    }
    for side, (where, turn) in sides.items():
        for cell in range(1, n - 1):
            piece = "towngate" if side == "S" and cell == GATE else "townwall"
            lay.put(piece, *where((cell + 0.5) * CELL, PANEL_IN), 0.0, turn)
        for cell in TOWERS[side]:
            lay.put("townwall_tower", *where((cell + 0.5) * CELL, TOWER_IN), 0.0, turn)
    for x in (CELL - TOWER_IN, last + TOWER_IN):                         # the four corner towers
        for y in (-(CELL - TOWER_IN), -(last + TOWER_IN)):
            lay.put("townwall_tower", x, y, 0.0, 0)
    assert span == 320, "the wall is laid out for the 40-cell town"
    return lay.items

"""The tea house: the pilot building. A building recipe places kit pieces on the grid, story by story.

Plan (cells are 8 studs; column 0 is west, row 0 is north):

    row 0   hall   hall*  hall   wing        hall*  = the inside stairs (no floor above them)
    row 1   hall   ATRIUM hall   wing        ATRIUM = open through both stories, under the dome
    row 2   hall   hall   hall   wing
    row 3   porch  porch  porch  stairs      porch  = open arcade; outside stairs go up to the wing roof

Ground floor: the hall round an arcaded atrium, the counter on the west wall, the porch in front.
Upper floor: a gallery round the atrium with balustrades, doors onto the porch roof and the wing roof.
Roof: parapet, and the dome over the atrium.

Positions are in studs, x east, y north, z up, measured from the building's north-west corner at street
level; turns are degrees about the up axis. `python buildings/teahouse.py` writes out/buildings/teahouse.json,
which build/pack.py turns into the game's BuildingData module, and assets/preview.py renders the same list."""
import json
import os

CELL, STORY = 8.0, 12.0
SLAB = 11.0                       # a floor slab sits between the walls, its top a hair above them
FLOOR = 0.06                      # walking height above a story line
SIDE = {"N": (0.5, 0.0, 180), "S": (0.5, 1.0, 0), "E": (1.0, 0.5, 90), "W": (0.0, 0.5, -90)}
BACK_TO = {"N": 0, "S": 180, "E": -90, "W": 90}      # turn that puts a piece's back against that side

HALL = [(r, c) for r in range(3) for c in range(3)]
PORCH = [(3, c) for c in range(3)]
WING = [(r, 3) for r in range(3)]
ATRIUM, STAIRWELL = (1, 1), (0, 1)


def placements():
    out = []

    def put(piece, x, y, z=0.0, turn=0.0):
        out.append({"piece": piece, "pos": [round(x, 3), round(y, 3), round(z, 3)], "turn": turn})

    def edge(piece, r, c, side, z=0.0, flip=False):
        """A piece one cell wide on one edge of cell (r, c), its front facing out of the cell."""
        fx, fy, turn = SIDE[side]
        put(piece, (c + fx) * CELL, -(r + fy) * CELL, z, turn + (180 if flip else 0))

    def centre(r, c):
        return (c + 0.5) * CELL, -(r + 0.5) * CELL

    def against(piece, r, c, side, gap, z=0.0, along=0.0):
        """A piece with its back to one wall of cell (r, c): `gap` studs from the wall line to its origin."""
        x, y = centre(r, c)
        dx, dy = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}[side]
        reach = CELL / 2 - gap
        put(piece, x + dx * reach - dy * along, y + dy * reach + dx * along, z, BACK_TO[side])

    def on_wall(piece, r, c, side, z, along=0.0, outside=False):
        """A piece that hangs on a wall face of cell (r, c): inside the cell, or on the street side."""
        x, y = centre(r, c)
        dx, dy = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}[side]
        reach = CELL / 2 + (0.5 if outside else -0.5)
        turn = SIDE[side][2] if outside else BACK_TO[side]
        put(piece, x + dx * reach - dy * along, y + dy * reach + dx * along, z, turn)

    # ---------------------------------------------------------------- ground floor
    for r, c in HALL + PORCH + WING + [(3, 3)]:
        put("ground", *centre(r, c), -0.49)
    ground = {
        (0, 0, "N"): "window", (0, 1, "N"): "plain", (0, 2, "N"): "window",
        (0, 0, "W"): "plain", (1, 0, "W"): "plain", (2, 0, "W"): "window",
        (0, 2, "E"): "plain", (1, 2, "E"): "door", (2, 2, "E"): "plain",
        (2, 0, "S"): "window", (2, 1, "S"): "door", (2, 2, "S"): "window",
        (3, 0, "S"): "arcade", (3, 1, "S"): "arcade", (3, 2, "S"): "arcade", (3, 0, "W"): "arcade", (3, 2, "E"): "arcade",
        (0, 3, "N"): "plain", (0, 3, "E"): "window", (1, 3, "E"): "door", (2, 3, "E"): "window", (2, 3, "S"): "plain",
    }
    for (r, c, side), kind in ground.items():
        edge("wall2_" + kind, r, c, side)
    for x, y in ((0, 0), (32, 0), (32, -24), (24, -32), (0, -32), (24, -24), (0, -24)):
        put("corner2", x, y)
    # the atrium: an arcade on every side, fronts facing in
    for side in "NSEW":
        edge("wall2_arcade", *ATRIUM, side, flip=True)
    for x, y in ((8, -8), (16, -8), (8, -16), (16, -16)):
        put("corner2", x, y)
    # stairs: inside against the north wall, climbing east; outside against the porch, climbing north to the wing roof
    put("stairs_narrow", 12, -2.5, 0, -90)
    put("stairs_narrow", 30, -28, 0, 0)

    # ---------------------------------------------------------------- upper floor
    for r, c in HALL + PORCH + WING:
        if (r, c) not in (ATRIUM, STAIRWELL):
            put("floor", *centre(r, c), SLAB)
    upper = {
        (0, 0, "N"): "upper_window", (0, 1, "N"): "upper", (0, 2, "N"): "upper_window",
        (0, 0, "W"): "upper_window", (1, 0, "W"): "upper", (2, 0, "W"): "upper_window",
        (0, 2, "E"): "upper_window", (1, 2, "E"): "upper_door", (2, 2, "E"): "upper_window",
        (2, 0, "S"): "upper_window", (2, 1, "S"): "upper_door", (2, 2, "S"): "upper_window",
    }
    for (r, c, side), kind in upper.items():
        edge("wall2_" + kind, r, c, side, STORY)
    for x, y in ((0, 0), (24, 0), (24, -24), (0, -24)):
        put("corner2_upper", x, y, STORY)
    # balustrades: round the atrium and the stairwell inside, round the two terraces outside
    for r, c, side in ((1, 1, "W"), (1, 1, "E"), (1, 1, "S"), (0, 1, "W")):
        edge("parapet_pierced", r, c, side, STORY + FLOOR)
    for r, c, side in ((3, 0, "S"), (3, 1, "S"), (3, 2, "S"), (3, 0, "W"), (3, 2, "E"),
                       (0, 3, "N"), (0, 3, "E"), (1, 3, "E"), (2, 3, "E")):
        edge("parapet_pierced", r, c, side, STORY)
    for x, y in ((0, -32), (24, -32), (32, 0), (32, -24)):
        put("parapet_corner", x, y, STORY)

    # ---------------------------------------------------------------- roof
    for r, c in HALL:
        put("dome" if (r, c) == ATRIUM else "floor", *centre(r, c), 2 * STORY - (STORY - SLAB))
    for c in range(3):
        edge("parapet_plain", 0, c, "N", 2 * STORY)
        edge("parapet_crenel", 2, c, "S", 2 * STORY)
    for r in range(3):
        edge("parapet_plain", r, 0, "W", 2 * STORY)
        edge("parapet_plain", r, 2, "E", 2 * STORY)
    for x, y in ((0, 0), (24, 0), (24, -24), (0, -24)):
        put("parapet_corner", x, y, 2 * STORY)

    # ---------------------------------------------------------------- dressing: ground floor
    put("counter", 3.4, -12, FLOOR - 0.05, 90)                         # along the west wall, facing the room
    on_wall("shelf", 1, 0, "W", 5.2, along=-2.5)
    on_wall("shelf", 1, 0, "W", 5.2, along=2.5)
    against("divan", 0, 0, "W", 1.7)
    against("divan", 2, 0, "W", 1.7, along=0.6)
    against("divan", 0, 2, "E", 1.7)
    against("divan", 2, 2, "E", 1.7)
    for x, y, turn in ((12, -12, 0), (4.6, -4.9, 90), (19.4, -4.6, 0), (19.2, -20, 90), (5.0, -20.4, 0)):
        put("rug", x, y, FLOOR - 0.05, turn)
    for x, y in ((12, -12), (19.2, -4.4), (19.0, -20), (5.2, -20.2), (4.6, -5.2)):
        put("tea_table", x, y, FLOOR - 0.05, 20)
    for x, y in ((4, -4), (20, -4), (4, -20), (20, -20), (20, -12), (12, -20)):
        put("lantern", x, y, 10.4)
    for c in range(3):                                                 # the porch
        put("lantern", (c + 0.5) * CELL, -28, 10.4)
    put("pot_tall", 9.2, -25.6)
    put("pot_round", 14.9, -25.4)
    put("sacks", 28, -4.2, 0, 90)
    put("barrel", 26.2, -21.6)
    put("barrel", 28.6, -22.2)
    put("crate", 30, -20.6, 0, 15)
    on_wall("shelf", 1, 3, "W", 5.2)

    # ---------------------------------------------------------------- dressing: upper floor and terraces
    up = STORY + FLOOR
    against("divan", 0, 0, "N", 1.7, up)
    against("divan", 1, 0, "W", 1.7, up)
    against("divan", 0, 2, "E", 1.7, up)
    against("divan", 2, 0, "S", 1.7, up)
    against("divan", 2, 2, "S", 1.7, up)
    for x, y, turn in ((4.8, -5.2, 0), (20, -12, 90), (12, -20.4, 0)):
        put("rug", x, y, up, turn)
    for x, y in ((4.8, -5.4), (20, -12), (4.6, -20), (19.4, -20)):
        put("tea_table", x, y, up, 35)
    for x, y in ((4, -12), (20, -4), (4, -20), (20, -20)):
        put("lantern", x, y, 2 * STORY - 1.6)
    for r in (0, 1):                                                   # the wing roof: a shaded terrace
        put("pergola", *centre(r, 3), up)
    put("rug", 28, -8, up, 90)
    put("tea_table", 28, -8, up)
    against("divan", 0, 3, "N", 1.7, up)
    put("pot_round", 30.6, -22, up)
    put("vase", 26.2, -22.6, up)
    put("rug", 12, -28, up)                                           # the porch roof
    put("tea_table", 5, -28, up)
    put("pot_tall", 22, -30.4, up)

    # ---------------------------------------------------------------- what hangs outside
    put("sign_tea", 8, -32.5, 9.6)
    put("lantern_wall", 16, -32.5, 8.6)
    for along in (-3.4, 3.4):                                          # either side of the front door
        on_wall("lantern_wall", 2, 1, "S", 8.6, along=along, outside=True)
    for x in (8, 16):
        put("banner", x, -24.5, STORY + 10.6)
    put("banner", -0.5, -12, STORY + 10.6, -90)
    put("bougainvillea", 20, -32.5, STORY + 3.0)                       # over the porch balustrade
    put("bougainvillea", 32.5, -20, STORY + 3.0, 90)                   # over the wing balustrade
    put("bougainvillea", 4, 0.5, 2 * STORY + 3.0, 180)
    on_wall("lantern_wall", 1, 3, "E", 8.6, along=3.6, outside=True)
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(here, "..", "out", "buildings")
    os.makedirs(folder, exist_ok=True)
    data = {"name": "teahouse", "title": "TeaHouse", "size": [32, 32], "placements": placements()}
    with open(os.path.join(folder, "teahouse.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    counts = {}
    for item in data["placements"]:
        counts[item["piece"]] = counts.get(item["piece"], 0) + 1
    print(len(data["placements"]), "pieces:", ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))

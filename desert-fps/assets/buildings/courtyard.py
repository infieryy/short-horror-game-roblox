"""The Courtyard House: a family house of long rooms round a court with two orange trees and a well.

Its walls are raised straight from the town plan (plan/town.py, "Courtyard House"), so the doors, windows
and the court are exactly what the planner and the bots tested: 7 x 9 cells, a ring of rooms two cells deep.

    north wing   the reception room, and the kitchen under the loft in the north-east corner
    west wing    the family's sitting room
    east wing    the store
    south wing   the guest room, by the street door
    loft         one upper room over the kitchen, its door onto the roof

The plan lets a player walk through every room cell, so nothing stands in the middle of one: furniture keeps
within three studs of a wall. `python buildings/courtyard.py` writes out/buildings/courtyard.json."""
import json
import os

from buildings.layout import FLOOR, SLAB, STEP, STORY, ROOM, Layout, footprint, shell

NAME = "Courtyard House"
LOFT = {(0, 5), (0, 6), (1, 5), (1, 6)}
G = FLOOR - 0.05                 # what stands on the paving


def placements():
    lay = Layout()
    rows, cell = footprint(NAME)
    rooms = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch in ROOM]
    court = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch not in ROOM]

    # ---------------------------------------------------------------- shell, from the plan
    for r, c in rooms + court:
        lay.at("ground", r, c, -0.49)
    # Blank walls in the plan get closed shutters here and there, and pilasters break the long fronts.
    shutters = [(0, 1, "N"), (0, 3, "N"), (1, 0, "W"), (5, 0, "W"), (7, 0, "W"), (8, 1, "S"), (8, 3, "S"), (8, 5, "S"),
                (3, 6, "E"), (2, 1, "E"), (6, 1, "E"), (2, 5, "W"), (6, 5, "W")]
    pilasters = [(0, 2), (0, 5), (9, 2), (9, 5), (3, 0), (6, 0), (2, 7), (5, 7), (7, 7)]
    edges, posts = shell(lay, rows, cell, dress={key: "shutter" for key in shutters}, pilasters=pilasters)
    for r, c in rooms:
        lay.at("floor", r, c, SLAB)

    # the roof: a plain parapet to the street, a balustrade to the court, battlements on the loft only
    for (r, c, side) in edges:
        if (r, c) in LOFT:
            continue
        dr, dc = STEP[side]
        inside = 0 <= r + dr < len(rows) and 0 <= c + dc < len(rows[0])
        lay.edge("parapet_pierced" if inside else "parapet_plain", r, c, side, STORY)
    for x, y in posts:
        if not (x >= 40 and y >= -16):
            lay.put("parapet_corner", x, y, STORY)

    # ---------------------------------------------------------------- the loft over the kitchen
    for (r, c, side), kind in {(0, 5, "N"): "_window", (0, 6, "N"): "", (0, 6, "E"): "_window", (1, 6, "E"): "",
                               (1, 6, "S"): "_window", (1, 5, "S"): "", (0, 5, "W"): "", (1, 5, "W"): "_door"}.items():
        lay.edge("wall2_upper" + kind, r, c, side, STORY)
        lay.edge("parapet_crenel", r, c, side, 2 * STORY)
    for x in (40, 56):
        for y in (0, -16):
            lay.put("corner2_upper", x, y, STORY)
            lay.put("parapet_corner", x, y, 2 * STORY)
    for r, c in LOFT:
        lay.at("floor", r, c, STORY + SLAB)
    up = STORY + FLOOR
    lay.against("divan", 1, 6, "E", 1.7, up)
    lay.at("rug", 0, 5, up, 0, dx=4, dy=-4)
    lay.at("tea_table", 0, 6, up, 0, dx=2.2, dy=2.2)
    lay.at("pot_round", 0, 5, up, 0, dx=-2.5, dy=2.5)
    lay.on_wall("lantern_wall", 1, 5, "S", STORY + 8.6)

    # ---------------------------------------------------------------- north wing: reception room and kitchen
    for c in (0, 3, 4):
        lay.against("divan", 0, c, "N", 1.7, G)
    lay.against("divan", 1, 0, "W", 1.7, G)
    lay.at("tea_table", 0, 1, G, 20, dy=2.2)
    lay.at("vase", 0, 1, G, 0, dx=2.7, dy=2.8)
    lay.put("rug", 32, -6.6, G, 0)
    lay.put("rug", 7, -10, G, 90)
    lay.on_wall("shelf", 1, 2, "S", 5.2)
    lay.against("counter", 1, 6, "E", 1.45, G)
    lay.on_wall("shelf", 1, 6, "E", 5.4)
    lay.on_wall("shelf", 0, 5, "N", 5.2)
    lay.at("pot_tall", 0, 6, G, 0, dx=2.5, dy=2.5)
    lay.at("barrel", 0, 5, G, 0, dx=-2.2, dy=2.2)

    # ---------------------------------------------------------------- west wing: the family's sitting room
    for r in (2, 3, 5):
        lay.against("divan", r, 0, "W", 1.7, G)
    lay.at("tea_table", 4, 0, G, 40, dx=-2.2)
    lay.at("pot_round", 4, 0, G, 0, dx=-2.6, dy=2.7)
    lay.put("rug", 6.6, -24, G, 90)
    lay.put("rug", 6.6, -44, G, 90)
    lay.on_wall("shelf", 3, 1, "E", 5.2)

    # ---------------------------------------------------------------- east wing: the store
    for dy in (2.2, -0.6):
        lay.at("barrel", 3, 6, G, 0, dx=2.2, dy=dy)
    lay.at("pot_tall", 3, 6, G, 0, dx=2.5, dy=-3.0)
    lay.on_wall("shelf", 4, 6, "E", 5.2)
    lay.at("pot_round", 4, 6, G, 0, dx=2.5, dy=1.0)
    lay.at("vase", 4, 6, G, 0, dx=2.7, dy=-1.4)
    lay.against("counter", 6, 6, "E", 1.45, G)
    lay.on_wall("shelf", 6, 6, "E", 5.4)
    lay.on_wall("shelf", 3, 5, "W", 5.2)
    lay.put("rug", 48, -36, G, 90)

    # ---------------------------------------------------------------- south wing: the guest room
    for c in (3, 4):
        lay.against("divan", 8, c, "S", 1.7, G)
    lay.against("divan", 8, 0, "W", 1.7, G)
    lay.against("divan", 7, 0, "W", 1.7, G)
    lay.at("tea_table", 8, 5, G, 15, dy=-2.2)
    lay.at("tea_table", 8, 1, G, 55, dy=-2.2)
    lay.at("pot_tall", 8, 6, G, 0, dx=2.5, dy=-2.5)
    lay.at("vase", 8, 6, G, 0, dx=0.4, dy=-2.9)
    lay.put("rug", 32, -65.4, G, 0)
    lay.put("rug", 7, -62, G, 90)
    lay.on_wall("shelf", 7, 2, "N", 5.2)
    # on the roof of the south wing: a shaded place to sit, for the skyline
    for c in (3, 4):
        lay.at("pergola", 8, c, up, dy=0.3)
    lay.put("rug", 32, -67.5, up, 0)

    # twelve hanging lanterns, the only lamps in the house that cast shadows
    for r, c in ((0, 1), (0, 4), (1, 6), (1, 0), (3, 1), (5, 0), (7, 1), (8, 4), (7, 6), (5, 6), (3, 5), (1, 3)):
        lay.at("lantern", r, c, 10.4)

    # ---------------------------------------------------------------- the court
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "T":
                lay.at("tree", r, c, G)
            elif ch == "c":
                lay.at("well", r, c, G)
    lay.at("pot_tall", 2, 2, G, 0, dx=-2.6, dy=2.6)
    lay.at("pot_round", 2, 2, G, 0, dx=-0.8, dy=2.8)
    lay.at("vase", 2, 4, G, 0, dx=2.7, dy=2.7)
    lay.at("pot_round", 6, 4, G, 0, dx=2.6, dy=-2.6)
    lay.at("pot_tall", 6, 4, G, 0, dx=0.8, dy=-2.8)
    for r, c, side in ((1, 2, "S"), (1, 4, "S"), (7, 2, "N"), (7, 4, "N"), (3, 1, "E"), (5, 1, "E"), (3, 5, "W"), (5, 5, "W")):
        lay.on_wall("lantern_wall", r, c, side, 8.6, outside=True)
    lay.put("bougainvillea", 36, -16.5, STORY + 3.0, 0)                 # over the balustrades
    lay.put("bougainvillea", 16.5, -44, STORY + 3.0, 90)

    # ---------------------------------------------------------------- the roof: washing, stores, a place to sit
    # (nobody can climb up here yet; it is what you see from the street and from other roofs)
    lay.at("tree", 2, 0, up)
    lay.at("tree", 6, 6, up)
    lay.at("rack_saffron", 1, 1, up)
    lay.at("rack_red", 1, 3, up)
    lay.at("rack_plum", 4, 5, up, 90)
    lay.at("sacks", 0, 0, up, 0, dy=1.0)
    for dx in (-1.5, 1.2):
        lay.at("barrel", 0, 3, up, 0, dx=dx, dy=2.2)
    lay.at("crate", 0, 4, up, 0, dx=2.0, dy=1.8)
    lay.at("crate", 0, 4, up + 3.0, 25, dx=2.0, dy=1.8)
    lay.against("divan", 4, 0, "W", 1.9, up)                            # the sitting corner on the west wing
    lay.at("rug", 4, 1, up, 90, dx=-1.5)
    lay.at("tea_table", 5, 0, up, 30, dx=-2.0, dy=1.0)
    lay.at("pot_round", 3, 0, up, 0, dx=-2.5, dy=-1.5)
    lay.at("vase", 5, 0, up, 0, dx=-2.6, dy=-2.4)
    for dy in (1.6, -1.2):                                              # over the store, more stores
        lay.at("barrel", 3, 6, up, 0, dx=2.2, dy=dy)
    lay.at("crate", 4, 6, up, -8, dx=2.0)
    lay.at("pot_tall", 2, 6, up, 0, dx=2.5, dy=2.4)
    lay.at("bolts", 5, 5, up, 15)
    lay.at("tea_table", 8, 3, up, 0, dx=0.5)                            # under the pergolas
    lay.at("vase", 8, 4, up, 0, dx=2.4, dy=-2.4)
    lay.at("pot_round", 8, 4, up, 0, dx=1.0, dy=-2.7)
    lay.at("sacks", 8, 1, up, 90, dx=-1.0)
    lay.at("barrel", 8, 0, up, 0, dx=-2.2, dy=-2.2)
    lay.at("pot_tall", 8, 6, up, 0, dx=2.4, dy=-2.4)
    lay.at("pot_round", 7, 6, up, 0, dx=2.5, dy=1.0)
    lay.on_wall("lantern_wall", 1, 5, "W", STORY + 8.6, along=3.0, outside=True)
    lay.on_wall("lantern_wall", 1, 6, "S", STORY + 8.6, along=3.0, outside=True)

    # ---------------------------------------------------------------- outside
    for r, c, side in ((0, 2, "N"), (8, 2, "S")):                       # the two street doors
        for along in (-3.4, 3.4):
            lay.on_wall("lantern_wall", r, c, side, 8.6, along=along, outside=True)
    for r, c, side in ((2, 6, "E"), (7, 6, "E"), (6, 0, "W")):
        lay.on_wall("lantern_wall", r, c, side, 8.6, along=3.4, outside=True)
    for r, c, side in ((0, 0, "N"), (0, 4, "N"), (4, 0, "W"), (8, 4, "S"), (8, 6, "S"), (4, 6, "E")):
        lay.on_wall("banner", r, c, side, 9.7, outside=True)
    return lay.items


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(here, "..", "out", "buildings")
    os.makedirs(folder, exist_ok=True)
    data = {"name": "courtyard", "title": "CourtyardHouse", "size": [56, 72], "placements": placements()}
    with open(os.path.join(folder, "courtyard.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    counts, triangles = {}, 0
    for item in data["placements"]:
        counts[item["piece"]] = counts.get(item["piece"], 0) + 1
        with open(os.path.join(here, "..", "out", item["piece"], "report.json")) as fh:
            triangles += json.load(fh)["triangles"]
    print(len(data["placements"]), "pieces,", triangles, "triangles:", ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))

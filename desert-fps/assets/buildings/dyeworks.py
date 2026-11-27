"""The Dye Works: an L of workshops round a yard of dye vats, with dyed cloth drying on racks in the yard and
on the roof, and the dyers' sign of three flasks on the wall (reference/zones/dye-works.webp).

Its walls and everything that stands in the yard come straight from the town plan (plan/town.py, "Dye Works"):
8 x 9 cells. A vat in the plan is a vat here, a hanging cloth is a rack of dyed cloth, high cover is a stack
of cloth bolts, low cover is a pile of sacks.

    top bar    the dye kitchen: shelves of dye jars, a work counter, a stack of bolts
    leg        the finishing room and the store
    office     one upper room over the south end of the leg, its door onto the roof

`python -m buildings.dyeworks` writes out/buildings/dyeworks.json."""
import json
import os

from buildings.layout import FLOOR, SLAB, STEP, STORY, ROOM, Layout, footprint, shell

NAME = "Dye Works"
OFFICE = {(7, 5), (7, 6), (7, 7), (8, 5), (8, 6), (8, 7)}
G = FLOOR - 0.05                 # what stands on the paving
VATS = ("vat", "vat_indigo", "vat_saffron", "vat_plum")
RACKS = ("rack_saffron", "rack_plum", "rack_red")


def placements():
    lay = Layout()
    rows, cell = footprint(NAME)
    rooms = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch in ROOM]
    up = STORY + FLOOR

    # ---------------------------------------------------------------- shell, from the plan
    # clay tiles indoors; brick in the yard, and stones splashed with dye round every vat
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            near_vat = any(cell(r + dr, c + dc) == "w" for dr in (-1, 0, 1) for dc in (-1, 0, 1))
            lay.at("paving_tiles" if ch in ROOM else "paving_dyed" if near_vat else "paving_bricks", r, c, -0.49,
                   0 if ch in ROOM else (r * 3 + c) % 4 * 90)
    shutters = [(0, 4, "N"), (0, 6, "N"), (2, 7, "E"), (5, 7, "E"), (3, 5, "W"), (5, 5, "W")]
    pilasters = [(0, 4), (0, 6), (3, 8), (6, 8)]
    edges, posts = shell(lay, rows, cell, dress={key: "shutter" for key in shutters}, pilasters=pilasters)
    for r, c in rooms:
        lay.at("floor", r, c, SLAB)
    # the roof: a plain parapet to the street, a balustrade to the yard, battlements on the office only
    for (r, c, side) in edges:
        if (r, c) in OFFICE:
            continue
        dr, dc = STEP[side]
        inside = 0 <= r + dr < len(rows) and 0 <= c + dc < len(rows[0])
        lay.edge("parapet_pierced" if inside else "parapet_plain", r, c, side, STORY)
    for x, y in posts:
        if not (x >= 40 and y <= -56):
            lay.put("parapet_corner", x, y, STORY)

    # ---------------------------------------------------------------- the office over the south end
    for (r, c, side), kind in {(7, 5, "N"): "", (7, 6, "N"): "_door", (7, 7, "N"): "", (8, 5, "S"): "_window", (8, 6, "S"): "",
                               (8, 7, "S"): "_window", (7, 5, "W"): "", (8, 5, "W"): "_window", (7, 7, "E"): "_window",
                               (8, 7, "E"): ""}.items():
        lay.edge("wall2_upper" + kind, r, c, side, STORY)
        lay.edge("parapet_crenel", r, c, side, 2 * STORY)
    for x in (40, 64):
        for y in (-56, -72):
            lay.put("corner2_upper", x, y, STORY)
            lay.put("parapet_corner", x, y, 2 * STORY)
    for r, c in OFFICE:
        lay.at("floor", r, c, STORY + SLAB)
    lay.against("divan", 8, 6, "S", 1.7, up)
    lay.put("rug", 52, -62.5, up, 0)
    lay.at("tea_table", 7, 7, up, 0, dx=2.2, dy=2.2)
    lay.against("counter", 7, 5, "W", 1.45, up)                          # the dyer's desk, his ledgers over it
    lay.on_wall("shelf", 7, 5, "W", STORY + 5.4)
    lay.on_wall("lantern_wall", 8, 7, "E", STORY + 8.6)

    # ---------------------------------------------------------------- what the plan puts in the yard and the rooms
    vats = racks = 0
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "w":
                lay.at(VATS[vats % len(VATS)], r, c, G)
                vats += 1
            elif ch == "k":                                             # down the west side they hang in one line
                lay.at(RACKS[racks % len(RACKS)], r, c, G, 90 if c == 0 or racks % 2 else 0)
                racks += 1
            elif ch in "CQ":
                lay.at("bolts", r, c, G, (r * 37 + c * 11) % 4 * 90)
            elif ch == "c":
                lay.at("sacks", r, c, G, 20)
            elif ch == "q":
                lay.at("counter", r, c, G, 90)

    # ---------------------------------------------------------------- the dye kitchen (top bar)
    for c in (3, 5):
        lay.on_wall("shelf", 0, c, "N", 5.2)
    for dx in (-1.4, 1.3):
        lay.at("barrel", 0, 6, G, 0, dx=dx, dy=2.2)
    lay.against("counter", 1, 7, "E", 1.45, G)
    lay.on_wall("shelf", 1, 7, "E", 5.4)
    lay.on_wall("shelf", 1, 2, "W", 5.2)
    lay.at("pot_tall", 1, 2, G, 0, dx=-2.5, dy=-2.3)
    lay.at("pot_round", 1, 2, G, 0, dx=-2.5, dy=2.0)
    lay.on_wall("shelf", 2, 3, "S", 5.2)
    lay.at("vase", 2, 3, G, 0, dx=2.2, dy=-2.7)
    lay.at("pot_tall", 0, 7, G, 0, dx=2.5, dy=2.5)
    lay.at("rug", 1, 3, G, 0)

    # ---------------------------------------------------------------- the finishing room and the store (leg)
    for r in (4, 6):
        lay.on_wall("shelf", r, 5, "W", 5.2)
    for dy in (2.2, -0.8):
        lay.at("barrel", 3, 7, G, 0, dx=2.2, dy=dy)
    lay.at("pot_round", 5, 7, G, 0, dx=2.5, dy=1.6)
    lay.at("vase", 5, 7, G, 0, dx=2.7, dy=-1.2)
    lay.against("counter", 8, 7, "E", 1.45, G)
    lay.on_wall("shelf", 8, 7, "E", 5.4)
    lay.at("barrel", 8, 5, G, 0, dx=-2.2, dy=-2.2)
    lay.at("pot_tall", 7, 7, G, 0, dx=2.5, dy=2.3)
    lay.at("rug", 5, 6, G, 90)

    for r, c in ((0, 3), (0, 5), (1, 7), (2, 3), (1, 2), (3, 6), (5, 6), (6, 6), (8, 5), (8, 7)):
        lay.at("lantern", r, c, 10.4)

    # ---------------------------------------------------------------- on the walls outside
    lay.on_wall("sign_dye", 2, 3, "S", 6.2, outside=True)               # facing the yard, as in the concept
    lay.on_wall("sign_dye", 0, 5, "N", 6.2, outside=True)               # and the street
    for r in (4, 6):
        lay.on_wall("awning", r, 5, "W", 6.0, outside=True)
    for r, c, side, along in ((0, 2, "N", 3.4), (0, 2, "W", -3.4), (6, 7, "E", 3.4), (8, 6, "S", 3.4), (2, 4, "S", 3.4),
                              (7, 5, "W", 3.4)):
        lay.on_wall("lantern_wall", r, c, side, 8.6, along=along, outside=True)
    for r, c, side in ((0, 3, "N"), (8, 5, "S")):                       # one banner by each street door
        lay.on_wall("banner", r, c, side, 9.7, outside=True)

    # ---------------------------------------------------------------- the roof, in two uses
    # The drying roof over the dye kitchen: two long lines of cloth.
    for c, piece in ((3, "rack_plum"), (4, "rack_saffron"), (5, "rack_red")):
        lay.at(piece, 0, c, up, 0, dy=0.6)
    for c, piece in ((3, "rack_red"), (4, "rack_plum"), (5, "rack_saffron")):
        lay.at(piece, 2, c, up, 0, dy=-0.6)
    # Finished cloth waiting by the office door: a stack of bolts on each side of it.
    lay.at("bolts", 6, 5, up, 0, dy=-0.6)
    lay.at("bolts", 6, 7, up, 90, dy=-0.6)
    lay.on_wall("lantern_wall", 7, 6, "N", STORY + 8.6, along=3.0, outside=True)
    lay.put("bougainvillea", 28, -24.5, STORY + 3.0, 0)                 # over the yard balustrade
    return lay.items


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(here, "..", "out", "buildings")
    os.makedirs(folder, exist_ok=True)
    data = {"name": "dyeworks", "title": "DyeWorks", "size": [64, 72], "placements": placements()}
    with open(os.path.join(folder, "dyeworks.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    counts, triangles = {}, 0
    for item in data["placements"]:
        counts[item["piece"]] = counts.get(item["piece"], 0) + 1
        with open(os.path.join(here, "..", "out", item["piece"], "report.json")) as fh:
            triangles += json.load(fh)["triangles"]
    print(len(data["placements"]), "pieces,", triangles, "triangles:", ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))

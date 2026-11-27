"""The Cistern Hall: a pillared hall over the town's water (reference/zones/cistern.webp). Two channels of
water run between the rows of pillars, fed by spouts in the north wall; the well head stands over the middle;
the keepers' room is at the south end.

Its walls, pillars and channels come straight from the town plan (plan/town.py, "Cistern Hall"): 8 x 7 cells.

    the hall           channels, pillars, the spouts, the well head, jars waiting to be filled
    the keepers' room  the counter where water is paid for, barrels and jars ready to go out
    the roof           three rain tanks

`python -m buildings.cistern` writes out/buildings/cistern.json."""
import json
import os

from buildings.layout import FLOOR, SLAB, STEP, STORY, ROOM, Layout, footprint, shell

NAME = "Cistern Hall"
G = FLOOR - 0.05                 # what stands on the paving
STREET = ("paving_a", "paving_b", "paving_c")


def placements():
    lay = Layout()
    rows, cell = footprint(NAME)
    rooms = [(r, c) for r, row in enumerate(rows) for c, ch in enumerate(row) if ch in ROOM]
    up = STORY + FLOOR

    # ---------------------------------------------------------------- floors: tiles, the two channels, street outside
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "u":
                lay.at("paving_channel", r, c, -0.49)
            elif ch in ROOM:
                lay.at("paving_tiles", r, c, -0.49)
            else:
                lay.at(STREET[(r * 2 + c) % 3], r, c, -0.49, (r + c) % 4 * 90)

    # ---------------------------------------------------------------- shell, from the plan
    shutters = [(0, 1, "N"), (0, 5, "N"), (1, 0, "W"), (3, 0, "W"), (4, 1, "S"), (6, 2, "S"), (6, 6, "S")]
    edges, posts = shell(lay, rows, cell, dress={key: "shutter" for key in shutters}, pilasters=[(0, 2), (0, 5)])
    for r, c in rooms:
        lay.at("floor", r, c, SLAB)
    for (r, c, side) in edges:
        lay.edge("parapet_plain", r, c, side, STORY)
    for x, y in posts:
        lay.put("parapet_corner", x, y, STORY)

    # ---------------------------------------------------------------- the hall
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch == "p":
                lay.at("pillar", r, c, G)
            elif ch == "Q":                                             # the well head, over the middle of the cistern
                lay.at("well", r, c, G)
            elif ch == "c":                                             # outside: the trough for animals
                lay.at("vat_indigo", r, c, G)
    for c in (2, 4):                                                    # spouts in the north wall feed the channels
        lay.on_wall("spout", 0, c, "N", G)
    for dx, piece in ((-2.5, "pot_tall"), (0.0, "pot_round"), (2.4, "pot_tall")):     # jars waiting to be filled
        lay.at(piece, 4, 1, G, 0, dx=dx, dy=-2.6)

    # ---------------------------------------------------------------- the keepers' room
    lay.against("counter", 6, 6, "E", 1.45, G)                          # where the water is paid for
    lay.on_wall("shelf", 6, 6, "E", 5.4)
    for dy in (1.4, -1.4):                                              # filled and ready to go out
        lay.at("barrel", 6, 2, G, 0, dx=-2.2, dy=dy)
    for dx, piece in ((-1.2, "pot_round"), (1.4, "pot_tall")):
        lay.at(piece, 6, 3, G, 0, dx=dx, dy=-2.6)

    for r, c in ((0, 1), (0, 5), (2, 1), (2, 4), (2, 6), (4, 2), (4, 5), (6, 3), (6, 5)):
        lay.at("lantern", r, c, 10.4)

    # ---------------------------------------------------------------- outside
    for r, c, side, along in ((0, 0, "N", 3.4), (0, 6, "N", -3.4), (4, 0, "W", 3.4), (6, 4, "S", 3.4), (2, 7, "E", 3.4)):
        lay.on_wall("lantern_wall", r, c, side, 8.6, along=along, outside=True)
    for r, c, side in ((0, 3, "N"), (6, 3, "S")):                       # one banner on each street front
        lay.on_wall("banner", r, c, side, 9.7, outside=True)

    # ---------------------------------------------------------------- the roof: three tanks that catch the rain
    for c in (2, 3, 4):
        lay.at("vat_indigo", 2, c, up)
    return lay.items


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    folder = os.path.join(here, "..", "out", "buildings")
    os.makedirs(folder, exist_ok=True)
    data = {"name": "cistern", "title": "CisternHall", "size": [64, 56], "placements": placements()}
    with open(os.path.join(folder, "cistern.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    counts, triangles = {}, 0
    for item in data["placements"]:
        counts[item["piece"]] = counts.get(item["piece"], 0) + 1
        with open(os.path.join(here, "..", "out", item["piece"], "report.json")) as fh:
            triangles += json.load(fh)["triangles"]
    print(len(data["placements"]), "pieces,", triangles, "triangles:", ", ".join(f"{n} {k}" for k, n in sorted(counts.items())))

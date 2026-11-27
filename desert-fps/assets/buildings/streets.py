"""What stands in the streets: every cover spot, tree, cloth line, well and way up of the plan (plan/town.py),
outside the buildings that dress their own yards.

The plan gives each spot a kind (high cover, low cover, cloth, tree, well, pillar, ladder, stairs, plank).
What is built there is chosen by where it is, so that it says what the place is for: stalls round the market
well and all facing it, a water cart loading at the well, the dyers' cloth across the east entrance of the
square, pots waiting for the kiln in the Potters' Quarter, carts and a trough by the stable and the gate,
seats outside the Tea House. HIGH, LOW and TREES list every spot; a spot the plan has and this file does not
name stops the build.

A high-cover group fills its cell and stands taller than a player, as the plan's sight lines assume; a
low-cover group blocks the way but not the view. Racks of cloth are walked through.

`python -m buildings.town` writes out/buildings/streets.json with the rest of the town."""
import math

from buildings.layout import CELL, FLOOR, OUT, SIDE, STEP, STORY, Layout

TITLE = "Streets"
G = FLOOR - 0.05
FACE = {side: SIDE[side][2] for side in "NESW"}          # the turn that makes a piece's front look that way
CLIMB = {"N": 0, "W": 90, "S": 180, "E": -90}            # the turn that makes stairs climb that way

# ---------------------------------------------------------------- high cover: (row, column) -> (group, facing)
HIGH = {
    # the north lane and the Watchtower Quarter
    (3, 13): ("crates", "S"),             # the watch's supplies, stacked at the corner of the lane
    (6, 13): ("cart", "N"),               # their supply cart
    (14, 5): ("cart", "W"),               # a cart being unloaded at the Courtyard House's north door
    (16, 2): ("barrels", "E"),            # the oil seller's stock, by the west wall
    # round the Tea House
    (8, 22): ("stall", "W"),              # the baker's bread stall, facing the Tea House door
    (9, 25): ("crates", "E"),             # flour for the bakery
    (12, 24): ("cart", "E"),              # a carter resting on the street to the square
    # the Potters' Quarter
    (13, 26): ("stall", "S"),             # the potters' guild sells from a stall at its corner
    (12, 31): ("potstack", "S"),          # pots packed for market
    (16, 37): ("crates", "W"),
    # the Market Square: stalls face the well
    (14, 20): ("stall", "S"),
    (15, 18): ("stall", "E"),
    (15, 23): ("crates", "S"),            # the merchants' goods, still packed
    (16, 21): ("stall", "S"),
    (17, 15): ("stall", "E"),
    (18, 19): ("cart", "N"),              # the water carrier's cart, loading at the well
    (18, 22): ("stall", "W"),
    (19, 16): ("bolts", "E"),             # the cloth merchant's bolts
    (20, 18): ("stall", "N"),
    (20, 23): ("stall", "N"),
    (21, 21): ("crates", "N"),
    (22, 15): ("cart", "E"),
    (23, 17): ("stall", "N"),
    (23, 20): ("barrels", "N"),           # the oil seller's barrels
    (20, 10): ("stall", "S"),             # a stall at the end of the row of shops
    (17, 26): ("bolts", "W"),             # cloth from the Dye Works, waiting to be carried in
    (24, 25): ("cart", "W"),
    (23, 38): ("crates", "W"),
    # between the square and the south quarters
    (26, 6): ("crates", "E"),             # the carpenter's timber, crated
    (27, 18): ("barrels", "S"),           # water barrels waiting outside the Cistern Hall
    (27, 37): ("crates", "W"),
    # the Gate Quarter
    (29, 15): ("stall", "E"),             # the water seller's stall, facing the Cistern Hall
    (31, 12): ("cart", "S"),              # the guard's cart
    (33, 7): ("cart", "N"),               # a carter's cart in the stable yard
    (35, 7): ("barrels", "E"),            # goods held at the gatehouse for the toll
    (37, 13): ("crates", "N"),
    (38, 11): ("cart", "W"),              # a cart just in through the gate
    # the Weavers' Quarter
    (30, 26): ("bolts", "W"),
    (31, 37): ("crates", "W"),
    (33, 33): ("bolts", "S"),
    (35, 30): ("cart", "E"),              # the weavers' cart, loaded for market
}
# ---------------------------------------------------------------- low cover
LOW = {
    (3, 26): ("pots", "S"),               # jars waiting for the kiln
    (6, 33): ("sacks", "E"),              # sacks of clay
    (7, 27): ("pots", "E"),               # pots set out by the workshop door
    (8, 16): ("seats", "E"),              # seats outside the Tea House
    (9, 7): ("trough", "N"),              # the water trough in the watch's yard
    (11, 32): ("baskets", "N"),
    (17, 17): ("baskets", "E"),           # baskets of fruit in the square
    (20, 13): ("sacks", "E"),             # grain at the west entrance of the square
    (20, 20): ("sacks", "N"),             # the grain seller, by the well
    (21, 25): ("boxes", "W"),
    (23, 11): ("boxes", "N"),
    (31, 6): ("trough", "N"),             # the horses' trough, by the stable
    (31, 29): ("baskets", "S"),           # baskets of wool
}
# ---------------------------------------------------------------- trees: an orange tree unless listed here
TREES = {
    (4, 21): "cypress", (13, 1): "cypress", (10, 36): "cypress", (34, 15): "cypress", (38, 27): "cypress",
    (30, 2): "cypress", (25, 22): "cypress",
    (5, 26): "palm_bed", (11, 15): "palm_bed", (22, 18): "palm_bed", (32, 4): "palm_bed", (33, 28): "palm_bed",
    (26, 30): "palm_bed", (1, 32): "palm_bed",
}
RACKS = ("rack_saffron", "rack_red", "rack_plum")


def rel(lay, piece, r, c, turn, dx=0.0, dy=0.0, z=G, spin=0.0):
    """A piece of a group: (dx, dy) studs from the middle of the cell in the group's own frame, which is
    turned `turn` degrees with the group."""
    a = math.radians(turn)
    lay.at(piece, r, c, z, turn + spin, dx=dx * math.cos(a) - dy * math.sin(a), dy=dx * math.sin(a) + dy * math.cos(a))


def group(lay, kind, r, c, face):
    """One cover group. In its own frame the group's front looks south."""
    turn = FACE[face]
    put = lambda piece, dx=0.0, dy=0.0, spin=0.0: rel(lay, piece, r, c, turn, dx, dy, G, spin)
    if kind == "stall":                                                 # the stall, its baskets behind the counter
        put("stall", dy=-0.9)
        put("baskets", -1.0, 3.0)
    elif kind == "cart":                                                # the shafts point the way it faces
        put("cart", 0.0, 1.64, -90)
        put("baskets", -2.7, -0.4, 90)
    elif kind == "crates":
        put("stack_crates", dy=1.95)
        put("stack_crates", dy=-1.85, spin=180)
    elif kind == "barrels":                                             # crates behind, three barrels in front
        put("stack_crates", dy=2.1)
        for dx in (-2.5, 0.0, 2.5):
            put("barrel", dx, -1.5)
    elif kind == "bolts":
        put("bolts")
    elif kind == "potstack":                                            # two racks of pots back to back, crates before them
        put("pot_rack", dy=3.0)
        put("pot_rack", dy=1.1, spin=180)
        put("stack_crates", dy=-1.9)
    elif kind == "pots":
        for piece, dx, dy in (("pot_tall", -1.6, 1.4), ("pot_tall", 1.5, 1.7), ("pot_round", -0.2, -0.6),
                              ("pot_round", 1.9, -1.3), ("vase", -2.2, -1.7), ("vase", 0.4, -2.5)):
            put(piece, dx, dy)
    elif kind == "sacks":
        put("sacks", dy=0.9)
        put("baskets", 0.3, -2.4)
    elif kind == "baskets":
        put("baskets", -0.4, 1.3)
        put("baskets", 0.5, -0.2, 14)
        put("pot_round", -1.6, -2.1)
        put("vase", 1.9, -2.2)
    elif kind == "boxes":
        put("crate", -1.5, 0.7)
        put("crate", 1.7, -1.0, 20)
        put("barrel", -1.3, -2.3)
        put("barrel", 1.7, 2.2)
    elif kind == "seats":                                               # a tea table between two divans
        put("tea_table")
        put("divan", dy=2.5)
        put("divan", dy=-2.5, spin=180)
    elif kind == "trough":
        put("vat_indigo")
    else:
        raise KeyError(kind)


def placements(grid, skip):
    """`skip(r, c)` is true for cells a building dresses for itself."""
    lay = Layout()
    n = len(grid)
    walk = lambda r, c: 0 <= r < n and 0 <= c < n and grid[r][c] in ".vLs=kABdiWu"
    found = {"C": set(), "c": set(), "T": set()}
    racks = 0
    for r in range(n):
        for c in range(n):
            ch = grid[r][c]
            if skip(r, c) or ch in ".123":
                continue
            if ch == "C":
                found["C"].add((r, c))
                assert (r, c) in HIGH, f"high cover at {(r, c)} has no entry in HIGH"
                group(lay, HIGH[(r, c)][0], r, c, HIGH[(r, c)][1])
            elif ch == "c":
                found["c"].add((r, c))
                assert (r, c) in LOW, f"low cover at {(r, c)} has no entry in LOW"
                group(lay, LOW[(r, c)][0], r, c, LOW[(r, c)][1])
            elif ch == "T":
                found["T"].add((r, c))
                lay.at(TREES.get((r, c), "tree"), r, c, G, (r * 37 + c * 53) % 4 * 90)
            elif ch == "k":
                # cloth hangs across the way people walk: north-south if the street runs east-west
                across = not (walk(r - 1, c) and walk(r + 1, c)) and walk(r, c - 1) and walk(r, c + 1)
                lay.at(RACKS[racks % 3], r, c, G, 90 if across else 0)
                racks += 1
            elif ch == "w":
                lay.at("well", r, c, G)
            elif ch == "P":                                             # a pillar of the arcade, a lantern on its north face
                lay.at("pillar", r, c, 0.0)
                x, y = Layout.centre(r, c)
                lay.put("lantern_wall", x, y + 1.25, 8.6, FACE["N"])
            elif ch == "L":                                             # a ladder against every house beside it
                for side, (dr, dc) in STEP.items():
                    rr, cc = r + dr, c + dc
                    if grid[rr][cc] in "123" and 0 < rr < n - 1 and 0 < cc < n - 1:
                        x, y = Layout.centre(r, c)
                        dx, dy = OUT[side]
                        back = {"N": "S", "S": "N", "E": "W", "W": "E"}[side]
                        for story in range(int(grid[rr][cc])):
                            lay.put("ladder", x + dx * (CELL / 2 - 1.5), y + dy * (CELL / 2 - 1.5), story * STORY, FACE[back])
            elif ch == "s":                                             # stairs up to the first one-story roof beside them
                for side in "NSWE":                                     # the order the plan looks in (plan/routes.py)
                    rr, cc = r + STEP[side][0], c + STEP[side][1]
                    if grid[rr][cc] == "1":
                        lay.at("stairs", r, c, 0.0, CLIMB[side])
                        break
            elif ch == "=":                                             # a plank from roof to roof
                level = walk(r, c - 1) and walk(r, c + 1)               # open to east and west: the roofs are north and south
                lay.at("plank", r, c, STORY + FLOOR - 0.75, 90 if level else 0)
    for kind, table in (("C", HIGH), ("c", LOW), ("T", TREES)):
        extra = set(table) - found[kind]
        assert not extra, f"entries for {kind} spots the plan does not have: {sorted(extra)}"
    return lay.items

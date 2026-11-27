"""The houses of the town: every solid block of the plan (plan/town.py) raised as a real, closed house.

The plan tests them as solid boxes, so they stay shut: walls all round, a door that is closed, shutters, and a
flat roof behind a parapet. What makes them a village is that no two are alike. Each has an entry in HOUSES:
who lives or works there, its own shade of plaster, its door, its sign, what is drying or stored on its roof,
and what stands outside it. A house is hollow, so it can be shot open and brought down (Destruction/Structure):
tiles on the ground, a floor slab per story, and a few things inside that say whose house it is.

Where the plan gives a roof a ladder, stairs or a plank, the parapet is left open there and the roof is kept
clear to walk on. Goods that stand in the street keep off the cells the route tests walk through.

`python -m buildings.town` writes every house with the rest of the town (out/buildings/house_*.json)."""
import random

from buildings.layout import BACK_TO, CELL, FLOOR, OUT, ROOM, SIDE, SLAB, STEP, STORY, Layout

G = FLOOR - 0.05                  # what stands on the paving
SIDES = "NESW"

# Every house its own shade of the one wall family: the painted plaster multiplied by this colour.
TINTS = {
    "peach": None,                # as painted
    "rose": (255, 228, 232),
    "apricot": (255, 238, 208),
    "clay": (244, 220, 204),
    "sand": (250, 242, 218),
    "blush": (255, 220, 216),
    "dusk": (236, 222, 238),
    "ochre": (250, 228, 190),
    "terracotta": (240, 206, 190),
    "lilac": (242, 230, 250),
}
TINTED = ("wall2", "corner2", "parapet")

# What a roof is used for: things set down one to a roof cell, in this order, against the parapet.
THEMES = {
    "washing": ["rack", "baskets", "rack", "pots", "rack", "vases"],
    "garden": ["tree", "plants", "pots", "plants", "bench", "plants"],
    "pots": ["potrack", "pots", "jars", "potrack", "vases", "pots"],
    "cloth": ["bolts", "rack", "loom", "baskets", "rack", "bolts"],
    "store": ["crates", "barrels", "sacks", "crate", "barrels", "crates"],
    "sitting": ["pergola", "bench", "pots", "plants", "bench", "bed"],
    "lookout": ["crate", "barrels", "crates", "jars"],
    "sleeping": ["bed", "bench", "bed", "pots", "bed", "vases"],
    "drying": ["mat", "baskets", "sacks", "mat", "vases", "baskets"],
    "tanks": ["tank", "barrels", "jars", "barrels", "vases"],
    "kitchen": ["barrels", "baskets", "jars", "vases", "barrels"],
    "shops": ["crates", "rack", "pots", "barrels", "rack", "baskets"],
    "bare": ["plants"],
}
# Roof things that fill the middle of a cell; on a roof players walk on, they give way to pots.
MIDDLE = {"tree", "bolts", "pergola", "tank", "bed", "mat", "sacks", "crates"}
# Goods in the street that reach no further than 2.6 studs from the wall line: they may stand where bots walk.
SHALLOW = {"plants", "plant", "baskets", "vases", "potrack"}

# The houses, keyed by their first plan cell (the northernmost row, then the westernmost cell in it).
#   tint      one of TINTS                     parapet   plain, crenel or pierced
#   doors     sides with a street door         leaf      door2_<leaf>: wood or teal
#   front     side that is a row of shop fronts: every bay a shutter under an awning
#   ground    shutters on the ground floor: blank, few, shutters or all      upper   the same, upstairs
#   lit       upper windows left open with a lantern burning inside
#   sign      a trade sign by the first door   banners   cloth banners on blank walls
#   vine      bougainvillea over the parapet   pilasters a post at every bay of the ground floor
#   roof      what the roof is used for (THEMES); terrace is the same for the lower roofs of a stepped house
#   goods     what stands outside against the walls
#   inside    what is found inside if the house is shot open
HOUSES = {
    # ---------------------------------------------------------------- the north lane
    (1, 9): dict(title="CharcoalShed", what="the charcoal burner's shed", tint="clay", doors="S", ground="blank",
                 roof="store", goods=("barrels", "crate"), inside="store"),
    (1, 18): dict(title="TeaMerchantsHouse", what="the tea merchant's house, behind the tea garden", tint="apricot",
                  doors="S", leaf="teal", parapet="pierced", ground="shutters", upper="shutters", lit=2, sign="tea",
                  vine=1, roof="sitting", goods=("plants", "bench"), inside="home"),
    (3, 30): dict(title="ClayStore", what="the potters' clay store", tint="terracotta", doors="N", ground="blank",
                  roof="pots", goods=("jars",), inside="store"),
    # ---------------------------------------------------------------- the Watchtower Quarter
    (4, 3): dict(title="Watchtower", what="the watchtower", tint="sand", doors="E", parapet="crenel", ground="blank",
                 upper="few", lit=1, banners=2, roof="lookout", goods=("barrels",), inside="watch"),
    (4, 6): dict(title="Barracks", what="the barracks: an L of two stories", tint="peach", doors="SE", pilasters=True,
                 ground="few", upper="shutters", lit=1, banners=2, roof="sleeping", goods=("bench", "barrels", "crate"),
                 inside="watch"),
    (5, 11): dict(title="WatchmansHouse", what="the watchman's house", tint="blush", doors="E", leaf="teal", ground="few",
                  roof="garden", goods=("plants", "bench"), inside="home"),
    (7, 3): dict(title="Quartermaster", what="the quartermaster's store; a ladder goes up to its roof", tint="sand",
                 doors="S", parapet="crenel", ground="blank", roof="store", goods=("crate", "barrels"), inside="store"),
    (9, 9): dict(title="CaptainsHouse", what="the captain's house", tint="lilac", doors="S", leaf="teal",
                 parapet="pierced", pilasters=True, ground="shutters", upper="shutters", lit=2, banners=1,
                 roof="sitting", goods=("plants", "bench"), inside="home"),
    (11, 3): dict(title="Armourer", what="the armourer's workshop", tint="clay", doors="S", ground="few", upper="few",
                  roof="washing", goods=("crate", "barrels"), inside="shop"),
    (8, 1): dict(title="OilStore", what="the lamp-oil store, against the town wall", tint="ochre", doors="E",
                 ground="blank", roof="tanks", goods=("jars", "barrels"), inside="store"),
    # ---------------------------------------------------------------- round the Tea House
    (4, 16): dict(title="TeaStore", what="the tea store and packing rooms, across the lane from the Tea House",
                  tint="sand", doors="S", parapet="pierced", pilasters=True, ground="shutters", awnings=2, roof="drying",
                  goods=("baskets", "crate", "vases"), inside="store"),
    (4, 22): dict(title="Inn", what="the inn: a tall house with a low porch", tint="rose", doors="S", leaf="teal",
                  parapet="pierced", ground="shutters", upper="all", lit=2, banners=1, vine=1, roof="garden",
                  terrace="sitting", goods=("bench", "plants"), inside="home"),
    (7, 14): dict(title="ScribesHouse", what="the scribe's house, narrow and tall", tint="dusk", doors="E", leaf="teal",
                  ground="few", upper="shutters", lit=2, roof="garden", goods=("bench",), inside="home"),
    (8, 23): dict(title="Bakery", what="the bakery", tint="apricot", doors="S", ground="shutters", awnings=1,
                  sign="bread", roof="kitchen", goods=("baskets", "vases"), inside="shop"),
    # ---------------------------------------------------------------- the Potters' Quarter
    (4, 34): dict(title="MasterPotter", what="the master potter's house", tint="ochre", doors="W", ground="few",
                  upper="shutters", lit=1, sign="pot", roof="pots", goods=("pots", "potrack"), inside="pots"),
    (6, 38): dict(title="GlazeStore", what="the glaze store, against the town wall", tint="clay", doors="W",
                  ground="blank", roof="kitchen", goods=("jars",), inside="store"),
    (8, 33): dict(title="DryingLoft", what="the drying loft; a ladder goes up to its roof, where pots dry", tint="peach",
                  doors="S", ground="few", roof="pots", goods=("pots", "vases"), inside="pots"),
    (9, 28): dict(title="PottersGuild", what="the potters' guild hall, and its shop at the south end",
                  tint="terracotta", doors="WE", pilasters=True, ground="shutters", awnings=2, upper="shutters", lit=2,
                  sign="pot", roof="pots", terrace="pots", goods=("pots", "potrack", "jars"), inside="pots"),
    (11, 34): dict(title="GlazeMixer", what="the glaze mixer's shed", tint="sand", doors="N", ground="blank",
                   roof="kitchen", goods=("jars", "vases"), inside="store"),
    # ---------------------------------------------------------------- round the Courtyard House and the west lane
    (12, 7): dict(title="Cobbler", what="the cobbler's shop", tint="rose", doors="S", ground="shutters", awnings=1,
                  roof="sleeping", goods=("bench",), inside="shop"),
    (14, 11): dict(title="ShopRow", what="a row of six lock-up shops facing the market street", tint="sand", doors="W",
                   front="E", pilasters=True, ground="blank", sign="cloth", roof="shops",
                   goods=("baskets", "potrack", "vases", "plants"), inside="shop"),
    (22, 1): dict(title="GardenersShed", what="the gardener's shed, against the town wall", tint="blush", doors="E",
                  ground="blank", roof="garden", goods=("plants", "baskets"), inside="store"),
    (25, 4): dict(title="Carpenter", what="the carpenter's workshop", tint="clay", doors="S", ground="few", roof="store",
                  goods=("crate", "bench"), inside="shop"),
    (26, 8): dict(title="Farrier", what="the farrier's forge", tint="terracotta", doors="E", ground="blank",
                  roof="store", goods=("barrels", "crate"), inside="store"),
    # ---------------------------------------------------------------- the Market Square
    (14, 14): dict(title="MarketKiosk", what="the sherbet seller's kiosk; stairs go up to its roof terrace",
                   tint="peach", doors="S", leaf="teal", parapet="pierced", ground="shutters", awnings=1, sign="drop",
                   roof="sitting", goods=("vases",), inside="shop"),
    (22, 23): dict(title="WeighHouse", what="the weigh house", tint="ochre", doors="N", parapet="pierced",
                   pilasters=True, ground="few", banners=2, roof="store", goods=("crate", "baskets"), inside="store"),
    (25, 14): dict(title="Arcade", what="the arcade: six cloth merchants' shops behind the pillars", tint="peach",
                   doors="S", front="N", parapet="pierced", pilasters=True, ground="few", sign="cloth", vine=1,
                   roof="shops", goods=("baskets", "vases"), inside="shop"),
    (26, 13): dict(title="Grocer", what="the grocer's", tint="apricot", doors="E", ground="shutters", awnings=1,
                   sign="bread", roof="drying", goods=("baskets", "vases"), inside="shop"),
    # ---------------------------------------------------------------- round the Dye Works and the east lane
    (19, 36): dict(title="MordantStore", what="the dyers' mordant store, built onto the Dye Works", tint="dusk",
                   doors="E", ground="blank", roof="cloth", goods=("barrels",), inside="store"),
    (25, 29): dict(title="DyersHouse", what="the dyer's house", tint="lilac", doors="S", leaf="teal", ground="few",
                   upper="all", lit=1, banners=1, roof="cloth", goods=("bench",), inside="home"),
    (25, 34): dict(title="WoolStore", what="the wool store", tint="sand", doors="N", ground="blank", roof="drying",
                   goods=("baskets",), inside="store"),
    # ---------------------------------------------------------------- the Gate Quarter
    (28, 6): dict(title="CustomsHouse", what="the customs house, on the street to the gate", tint="dusk", doors="E",
                  parapet="crenel", pilasters=True, ground="few", upper="shutters", lit=2, banners=2, roof="lookout",
                  goods=("crate", "barrels"), inside="shop"),
    (29, 3): dict(title="FodderBarn", what="the fodder barn", tint="sand", doors="E", ground="blank", roof="store",
                  goods=("crate",), inside="stable"),
    (33, 3): dict(title="CartersLodge", what="the carters' lodging house", tint="clay", doors="ES", ground="few",
                  upper="few", lit=1, banners=1, roof="washing", goods=("bench", "barrels"), inside="home"),
    (33, 9): dict(title="Stable", what="the stable; stairs go up to its hay roof", tint="ochre", doors="W",
                  ground="blank", roof="store", goods=("barrels",), inside="stable"),
    (36, 7): dict(title="Gatehouse", what="the gatehouse, beside the town gate", tint="sand", doors="E",
                  parapet="crenel", ground="blank", upper="few", lit=1, banners=2, roof="lookout", goods=("barrels",),
                  inside="watch"),
    # ---------------------------------------------------------------- round the Cistern Hall and the south lane
    (31, 14): dict(title="WaterCarriers", what="the water carriers' house", tint="blush", doors="E", ground="few",
                   sign="drop", roof="tanks", goods=("barrels", "jars"), inside="store"),
    (35, 16): dict(title="Shrine", what="a wayside shrine: one small whitewashed room", tint="peach", doors="N",
                   leaf="teal", parapet="crenel", ground="blank", banners=1, roof="bare", goods=("plants",),
                   inside="empty"),
    (36, 23): dict(title="WashHouse", what="the wash house, by the overflow pool", tint="dusk", doors="W", leaf="teal",
                   ground="shutters", roof="washing", goods=("baskets", "vases"), inside="store"),
    # ---------------------------------------------------------------- the Weavers' Quarter
    (28, 28): dict(title="WeaversWorkshop", what="the weavers' workshop; a plank crosses to its roof", tint="rose",
                   doors="WN", pilasters=True, ground="shutters", awnings=1, sign="cloth", roof="cloth",
                   goods=("loom", "baskets"), inside="loom"),
    (29, 32): dict(title="CardersHouse", what="the carder's house; a ladder goes up to its roof", tint="peach",
                   doors="E", ground="few", roof="washing", goods=("baskets",), inside="home"),
    (32, 30): dict(title="MasterWeaver", what="the master weaver's house", tint="lilac", doors="NE", leaf="teal",
                   parapet="pierced", ground="shutters", upper="shutters", lit=2, vine=1, roof="cloth",
                   goods=("loom", "bench"), inside="loom"),
    (34, 35): dict(title="SpinnersCottage", what="the spinner's cottage", tint="blush", doors="W", ground="few",
                   roof="cloth", goods=("baskets", "plants"), inside="home"),
    (37, 31): dict(title="WeaversShed", what="the weavers' shed, against the town wall", tint="apricot", doors="N",
                   ground="blank", roof="cloth", goods=("loom",), inside="loom"),
}
DEFAULTS = dict(leaf="wood", parapet="plain", front="", pilasters=False, ground="few", upper="few", lit=0, sign=None,
                banners=0, vine=0, awnings=0, terrace=None, goods=(), inside="home")
EVERY = {"blank": 0, "few": 3, "shutters": 2, "all": 1}


def blocks(grid):
    """The solid blocks inside the town wall: lists of plan cells, each list one house, in reading order."""
    n, seen, out = len(grid), set(), []
    for r in range(1, n - 1):
        for c in range(1, n - 1):
            if grid[r][c] in "123" and (r, c) not in seen:
                stack, cells = [(r, c)], []
                seen.add((r, c))
                while stack:
                    a, b = stack.pop()
                    cells.append((a, b))
                    for da, db in STEP.values():
                        aa, bb = a + da, b + db
                        if 1 <= aa < n - 1 and 1 <= bb < n - 1 and grid[aa][bb] in "123" and (aa, bb) not in seen:
                            seen.add((aa, bb))
                            stack.append((aa, bb))
                out.append(sorted(cells))
    return out


class House:
    def __init__(self, grid, cells, spec, taken, routes):
        self.grid, self.n = grid, len(grid)
        self.r0, self.c0 = min(r for r, _ in cells), min(c for _, c in cells)
        self.rows, self.columns = max(r for r, _ in cells) - self.r0 + 1, max(c for _, c in cells) - self.c0 + 1
        self.height = {(r - self.r0, c - self.c0): int(grid[r][c]) for r, c in cells}     # stories, by its own cells
        self.spec = {**DEFAULTS, **spec}
        self.tint = TINTS[self.spec["tint"]]
        self.taken, (self.walked, self.roof_walked) = taken, routes
        self.rng = random.Random(self.spec["title"])
        self.lay = Layout()
        self.clear = []                         # street cell sides where no sand is banked: [row, column, dr, dc]
        self.used = set()                       # wall edges of the ground floor that carry something already

    # ------------------------------------------------------------ the plan round the house
    def char(self, r, c):
        rr, cc = r + self.r0, c + self.c0
        return self.grid[rr][cc] if 0 <= rr < self.n and 0 <= cc < self.n else "2"

    def border(self, r, c):
        rr, cc = r + self.r0, c + self.c0
        return rr <= 0 or cc <= 0 or rr >= self.n - 1 or cc >= self.n - 1

    def beyond(self, r, c, side):
        dr, dc = STEP[side]
        return r + dr, c + dc

    def street(self, r, c, side):
        """The plan cell on the far side of a wall, in town coordinates."""
        rr, cc = self.beyond(r, c, side)
        return rr + self.r0, cc + self.c0

    def walls(self, story):
        """The outside wall edges of one story (0 is the ground floor): [(r, c, side)] in a fixed order."""
        out = []
        for side in SIDES:
            for (r, c), tall in sorted(self.height.items()):
                if tall <= story:
                    continue
                far = self.beyond(r, c, side)
                if self.height.get(far, 0) > story:
                    continue                                    # the house goes on
                if self.border(*far) and story < 2:
                    continue                                    # the town wall stands there
                if story == 0 and self.char(*far) in ROOM:
                    continue                                    # the room next door has its wall there
                out.append((r, c, side))
        return out

    def rims(self, level):
        """The roof edges that get a parapet, for the roofs `level` stories up, and the edges left open because
        a ladder, stairs or a plank comes up there."""
        closed, opened = [], []
        for side in SIDES:
            for (r, c), tall in sorted(self.height.items()):
                if tall != level:
                    continue
                far = self.beyond(r, c, side)
                if self.height.get(far, 0) >= level or (self.border(*far) and level <= 2):
                    continue
                if level == 1 and self.char(*far) in ROOM:
                    continue                                    # the room next door has its parapet there
                way_up = level == 1 and self.char(*far) in "Ls="
                (opened if way_up else closed).append((r, c, side))
        return closed, opened

    @staticmethod
    def corners(edges, every=False):
        """Grid corners (row, column) where a run of wall turns; with `every`, each end of every bay too."""
        level, upright = set(), set()
        for r, c, side in edges:
            if side in "NS":
                y = r + (side == "S")
                level |= {(y, c), (y, c + 1)}
            else:
                x = c + (side == "E")
                upright |= {(r, x), (r + 1, x)}
        return sorted(level | upright if every else level & upright)

    # ------------------------------------------------------------ placing
    def outside(self, piece, r, c, side, gap, z=G, along=0.0):
        """A piece in the street with its back to the wall on one side of cell (r, c): `gap` from the wall line."""
        x, y = Layout.centre(r, c)
        dx, dy = OUT[side]
        reach = CELL / 2 + gap
        self.lay.put(piece, x + dx * reach - dy * along, y + dy * reach + dx * along, z, SIDE[side][2])

    def pick(self, edges, count, skip=()):
        """`count` of the edges, spread round the house, always the same for the same house."""
        free = [edge for edge in edges if edge not in skip]
        if not free or count <= 0:
            return []
        step = max(len(free) // count, 1)
        start = self.rng.randrange(step)
        return free[start::step][:count]

    # ------------------------------------------------------------ the shell
    def shell(self):
        lay, spec = self.lay, self.spec
        tallest = max(self.height.values())
        for (r, c), tall in sorted(self.height.items()):
            lay.at("paving_tiles", r, c, -0.49)
            for story in range(tall):
                lay.at("floor", r, c, story * STORY + SLAB)

        # the ground floor: doors, shop fronts, shutters
        ground = self.walls(0)
        open_street = [edge for edge in ground if self.char(*self.beyond(*edge)) == "."]
        self.doors = []
        for side in spec["doors"]:
            choices = [edge for edge in open_street if edge[2] == side and edge not in self.doors]
            assert choices, f"{spec['title']}: no wall on side {side} faces open street"
            self.doors.append(choices[len(choices) // 2])
        fronts = [edge for edge in ground if edge[2] in spec["front"] and edge not in self.doors]
        rest = [edge for edge in ground if edge not in self.doors and edge not in fronts]
        shuttered = set(fronts)
        if EVERY[spec["ground"]]:
            shuttered |= set(rest[self.rng.randrange(EVERY[spec["ground"]])::EVERY[spec["ground"]]])
        for edge in ground:
            kind = "door" if edge in self.doors else "shutter" if edge in shuttered else "plain"
            lay.edge("wall2_" + kind, *edge)
        for edge in self.doors:
            lay.edge("door2_" + spec["leaf"], *edge)
            self.used.add(edge)
            self.clear.append([*self.street(*edge), -STEP[edge[2]][0], -STEP[edge[2]][1]])
        for y, x in self.corners(ground, spec["pilasters"]):
            lay.put("corner2", x * CELL, -y * CELL)

        # awnings: over every shop front that opens on clear street, and over a few other shutters
        shaded = [edge for edge in fronts if edge in open_street]
        shaded += self.pick([edge for edge in sorted(shuttered - set(fronts)) if edge in open_street], spec["awnings"])
        for edge in shaded:
            lay.on_wall("awning", *edge, 6.0, outside=True)
        self.shuttered = shuttered

        # upstairs: shutters, and a few windows left open with a lamp burning inside
        self.blank = [edge for edge in ground if edge not in shuttered and edge not in self.doors]
        for story in range(1, tallest):
            edges, z = self.walls(story), story * STORY
            lit = self.pick(edges, spec["lit"] if story == 1 or tallest == 3 and story == 2 else 0)
            closed = set()
            if EVERY[spec["upper"]]:
                closed = set(edges[self.rng.randrange(EVERY[spec["upper"]])::EVERY[spec["upper"]]])
            for edge in edges:
                kind = "_window" if edge in lit else "_shutter" if edge in closed else ""
                lay.edge("wall2_upper" + kind, *edge, z)
            for r, c, _ in lit:
                lay.at("lantern", r, c, z + 10.4)
                lay.items[-1]["shadow"] = False                         # nobody gets in there: its light is all that shows
            for y, x in self.corners(edges):
                lay.put("corner2_upper", x * CELL, -y * CELL, z)
            if story == tallest - 1:
                self.high_blank = [(edge, z) for edge in edges if edge not in lit and edge not in closed]

        # parapets, left open where there is a way up
        self.roofs = {}
        for level in sorted(set(self.height.values())):
            closed, opened = self.rims(level)
            z = level * STORY
            for edge in closed:
                lay.edge("parapet_" + spec["parapet"], *edge, z)
            for y, x in self.corners(closed):
                lay.put("parapet_corner", x * CELL, -y * CELL, z)
            self.roofs[level] = (closed, opened)

    # ------------------------------------------------------------ what hangs on the walls
    def dress(self):
        lay, spec = self.lay, self.spec
        first = self.doors[0]
        if spec["sign"]:
            lay.on_wall("sign_" + spec["sign"], *first, 9.6, along=3.0, outside=True)
        for index, edge in enumerate(self.doors):                       # a lantern by every door, two where there is no sign
            sides = (-3.4,) if spec["sign"] and index == 0 else (-3.4, 3.4) if index == 0 else (3.4,)
            for along in sides:
                lay.on_wall("lantern_wall", *edge, 8.6, along=along, outside=True)
        free = [edge for edge in self.blank if edge not in self.used]
        for edge in self.pick(free, spec["banners"]):
            lay.on_wall("banner", *edge, 9.7, outside=True)
            self.used.add(edge)
        if spec["banners"] and max(self.height.values()) > 1:           # and one high up, where the town can see it
            for edge, z in self.pick(self.high_blank, 1):
                lay.on_wall("banner", *edge, z + 9.7, outside=True)
        top = max(self.height.values())
        closed, _ = self.roofs[top]
        for edge in self.pick([e for e in closed if self.char(*self.beyond(*e)) == "."], spec["vine"]):
            lay.on_wall("bougainvillea", *edge, top * STORY + 3.0, outside=True)

    # ------------------------------------------------------------ goods in the street
    def goods(self):
        ground = [edge for edge in self.walls(0) if edge not in self.used]
        self.rng.shuffle(ground)
        for kind in self.spec["goods"]:
            door = self.street(*self.doors[0])
            if kind == "plants" and door not in self.taken:             # a plant in a pot on each side of the door
                self.outside("potted_plant", *self.doors[0], 1.6, G, -3.1)
                self.outside("potted_plant", *self.doors[0], 1.6, G, 3.1)
                self.taken.add(door)
                continue
            for edge in ground:
                cell = self.street(*edge)
                if self.char(*self.beyond(*edge)) != "." or cell in self.taken:
                    continue
                if cell in self.walked and kind not in SHALLOW:
                    continue
                if kind in ("bench", "loom", "potrack") and edge in self.shuttered:
                    continue                                    # nothing tall in front of a window
                self.stand(kind, edge)
                self.taken.add(cell)
                self.used.add(edge)
                ground.remove(edge)
                self.clear.append([*cell, -STEP[edge[2]][0], -STEP[edge[2]][1]])
                break

    def stand(self, kind, edge):
        put = lambda piece, gap, along=0.0: self.outside(piece, *edge, gap, G, along)
        if kind == "plants":
            put("potted_plant", 1.6, -2.7)
            put("potted_plant", 1.6, 2.7)
        elif kind == "plant":
            put("potted_plant", 1.6, 2.8)
        elif kind == "baskets":
            put("baskets", 1.4, -0.7)
            put("vase", 1.5, 2.6)
        elif kind == "vases":
            for along in (-2.4, -0.5, 1.7):
                put("vase", 1.5, along)
        elif kind == "pots":
            put("pot_tall", 1.9, -1.9)
            put("pot_round", 1.95, 0.7)
            put("vase", 1.5, 2.6)
        elif kind == "jars":
            put("pot_tall", 1.9, -1.6)
            put("pot_tall", 1.9, 1.5)
        elif kind == "barrels":
            put("barrel", 2.05, -1.5)
            put("barrel", 2.05, 1.3)
        elif kind == "crate":
            put("crate", 2.25, -1.3)
            put("barrel", 2.05, 1.9)
        elif kind == "bench":
            put("divan", 1.95)
        elif kind == "loom":
            put("loom", 1.75)
        elif kind == "potrack":
            put("pot_rack", 1.65)
        else:
            raise KeyError(kind)

    # ------------------------------------------------------------ the roofs
    def roof(self):
        top = max(self.height.values())
        racks = ["rack_saffron", "rack_red", "rack_plum"]
        self.rng.shuffle(racks)
        for level, (closed, opened) in self.roofs.items():
            theme = self.spec["roof"] if level == top or not self.spec["terrace"] else self.spec["terrace"]
            z = level * STORY + FLOOR
            cells = [cell for cell, tall in sorted(self.height.items()) if tall == level]
            walked = bool(opened) or any((r + self.r0, c + self.c0) in self.roof_walked for r, c in cells)
            kept = {(r, c) for r, c, _ in opened}                       # where you step onto the roof: left clear
            things = iter(THEMES[theme] * 3)
            spots = [cell for cell in cells if cell not in kept]
            if len(spots) > 3:                                          # a big roof is not filled from end to end
                self.rng.shuffle(spots)
                spots = sorted(spots[: max(3, (len(spots) * 2 + 2) // 3)])
            for r, c in spots:
                sides = [side for (rr, cc, side) in closed if (rr, cc) == (r, c)]
                thing = next(things)
                if walked and thing in MIDDLE or not sides and thing not in ("bed", "mat", "tree", "bolts"):
                    thing = "pots" if sides else "bed"
                self.set_down(thing, r, c, sides, z, racks)

    def set_down(self, thing, r, c, sides, z, racks):
        lay = self.lay
        side = sides[self.rng.randrange(len(sides))] if sides else "N"
        against = lambda piece, gap, along=0.0: lay.against(piece, r, c, side, gap, z, along)
        # how far a thing in the middle of the cell must move to clear the parapets it stands by
        shift = lambda by: (sum(-OUT[s][0] for s in sides) * by, sum(-OUT[s][1] for s in sides) * by)
        opposite = ("N" in sides and "S" in sides) or ("E" in sides and "W" in sides)
        if thing == "pergola" and opposite:
            thing = "bench"
        if thing == "tank" and opposite:
            thing = "barrels"
        if thing == "rack":
            racks.append(racks.pop(0))
            against(racks[0], 1.5)
        elif thing == "baskets":
            against("baskets", 1.5, -0.6)
            against("vase", 1.7, 2.6)
        elif thing == "pots":
            against("pot_tall", 2.1, -1.9)
            against("pot_round", 2.1, 0.6)
            against("vase", 1.7, 2.6)
        elif thing == "jars":
            against("pot_tall", 2.1, -1.5)
            against("pot_tall", 2.1, 1.5)
        elif thing == "vases":
            for along in (-2.3, -0.4, 1.8):
                against("vase", 1.7, along)
        elif thing == "plants":
            against("potted_plant", 1.9, -2.2)
            against("potted_plant", 1.9, 2.0)
        elif thing == "bench":
            against("divan", 2.1)
        elif thing == "potrack":
            against("pot_rack", 1.8)
        elif thing == "loom":
            against("loom", 1.9)
        elif thing == "crates":
            against("stack_crates", 2.7)
        elif thing == "crate":
            against("crate", 2.4, -1.6)
            against("barrel", 2.2, 1.7)
        elif thing == "barrels":
            against("barrel", 2.2, -1.45)
            against("barrel", 2.2, 1.45)
        elif thing == "sacks":
            against("sacks", 2.9)
        elif thing == "tree":
            dx, dy = shift(0.3)
            lay.at("tree", r, c, z, self.rng.choice((0, 90, 180, 270)), dx=dx, dy=dy)
        elif thing == "bolts":
            lay.at("bolts", r, c, z, self.rng.choice((0, 90)))
        elif thing == "tank":
            dx, dy = shift(0.35)
            lay.at("vat_indigo", r, c, z, 0, dx=dx, dy=dy)
        elif thing == "pergola":
            dx, dy = shift(0.5)
            lay.at("pergola", r, c, z, 0, dx=dx, dy=dy)
            lay.at("rug", r, c, z, 0, dx=dx, dy=dy)
            lay.at("tea_table", r, c, z, 25, dx=dx + 0.4, dy=dy - 0.3)
        elif thing == "bed":
            lay.at("rug", r, c, z, 90 if side in "EW" else 0)
            lay.at("vase", r, c, z, 0, dx=-2.4 if "E" in sides else 2.4, dy=-2.4 if "N" in sides else 2.4)
        elif thing == "mat":                                            # dates and figs drying on a mat
            lay.at("rug", r, c, z, 90 if side in "EW" else 0)
            lay.at("baskets", r, c, z + 0.07, 90 if side in "EW" else 0, dx=0.0, dy=0.4)
        else:
            raise KeyError(thing)

    # ------------------------------------------------------------ what is inside
    def inside(self):
        lay, kind = self.lay, self.spec["inside"]
        cells = sorted(self.height)
        (r, c), walls = cells[0], [side for (rr, cc, side) in self.walls(0) if (rr, cc) == cells[0]]
        wall = walls[0] if walls else "N"
        if kind == "home":
            lay.at("rug", r, c, G)
            lay.against("divan", r, c, wall, 1.9, G)
        elif kind == "store":
            lay.at("stack_crates", r, c, G, 20, dx=0.3, dy=-0.2)
            lay.against("barrel", r, c, wall, 2.1, G, 2.0)
        elif kind == "shop":
            lay.against("counter", r, c, wall, 1.6, G)
        elif kind == "loom":
            lay.at("loom", r, c, G, 90)
            lay.against("baskets", r, c, wall, 1.5, G, 1.5)
        elif kind == "pots":
            lay.against("pot_rack", r, c, wall, 1.7, G)
            lay.at("pot_tall", r, c, G, 0, dx=-1.0, dy=-1.6)
        elif kind == "stable":
            lay.at("stack_crates", r, c, G, 70)
            lay.against("barrel", r, c, wall, 2.1, G, -1.8)
        elif kind == "watch":
            lay.at("stack_crates", r, c, G, 10)
            lay.against("divan", r, c, wall, 1.9, G)

    def build(self):
        self.shell()
        self.dress()
        self.goods()
        self.roof()
        self.inside()
        if self.tint:
            for item in self.lay.items:
                if item["piece"].startswith(TINTED):
                    item["tint"] = list(self.tint)
        return self.lay.items


def build_all(grid, taken, routes):
    """Every house: [(recipe name, row, column, data, clear, spec)]."""
    out, seen = [], set()
    for cells in blocks(grid):
        key = cells[0]
        assert key in HOUSES, f"the house at plan cell {key} has no entry in HOUSES"
        seen.add(key)
        house = House(grid, cells, HOUSES[key], taken, routes)
        items = house.build()
        name = f"house_{key[0]:02d}_{key[1]:02d}"
        data = {"name": name, "title": house.spec["title"], "size": [house.columns * CELL, house.rows * CELL],
                "placements": items}
        out.append((name, house.r0, house.c0, house.rows, house.columns, data, house.clear, house.spec, len(cells)))
    assert seen == set(HOUSES), f"HOUSES has entries for no house: {sorted(set(HOUSES) - seen)}"
    return out

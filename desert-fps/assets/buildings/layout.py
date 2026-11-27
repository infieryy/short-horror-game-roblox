"""Shared tools for building recipes: placing kit pieces on the grid, and raising a building's shell
straight from the town plan so that what is built is what the planner tested.

Positions are studs east, north and up from the building's north-west corner at street level (north is +y,
so rows of the plan run towards -y). Turns are degrees about the up axis. A cell is (row, column) inside the
building's own rectangle."""
import json
import os

CELL, STORY = 8.0, 12.0
SLAB = 11.0                       # a floor slab sits between the walls, its top a hair above them
FLOOR = 0.06                      # walking height above a story line
SIDE = {"N": (0.5, 0.0, 180), "S": (0.5, 1.0, 0), "E": (1.0, 0.5, 90), "W": (0.0, 0.5, -90)}
BACK_TO = {"N": 0, "S": 180, "E": -90, "W": 90}      # turn that puts a piece's back against that side
STEP = {"N": (-1, 0), "S": (1, 0), "E": (0, 1), "W": (0, -1)}
OUT = {"N": (0, 1), "S": (0, -1), "E": (1, 0), "W": (-1, 0)}           # the same directions in studs (x, y)

ROOM = set("idWpqQu")             # plan/planner.py and plan/town.py: cells with thin walls round them
SOLID = set("123")
HERE = os.path.dirname(os.path.abspath(__file__))


class Layout:
    def __init__(self):
        self.items = []

    def put(self, piece, x, y, z=0.0, turn=0.0):
        self.items.append({"piece": piece, "pos": [round(x, 3), round(y, 3), round(z, 3)], "turn": turn})

    def edge(self, piece, r, c, side, z=0.0, flip=False):
        """A piece one cell wide on one edge of cell (r, c), its front facing out of the cell."""
        fx, fy, turn = SIDE[side]
        self.put(piece, (c + fx) * CELL, -(r + fy) * CELL, z, turn + (180 if flip else 0))

    @staticmethod
    def centre(r, c):
        return (c + 0.5) * CELL, -(r + 0.5) * CELL

    def at(self, piece, r, c, z=0.0, turn=0.0, dx=0.0, dy=0.0):
        """A piece in cell (r, c), `dx` studs east and `dy` studs north of its middle."""
        x, y = self.centre(r, c)
        self.put(piece, x + dx, y + dy, z, turn)

    def against(self, piece, r, c, side, gap, z=0.0, along=0.0):
        """A piece with its back to one wall of cell (r, c): `gap` studs from the wall line to its origin."""
        x, y = self.centre(r, c)
        dx, dy = OUT[side]
        reach = CELL / 2 - gap
        self.put(piece, x + dx * reach - dy * along, y + dy * reach + dx * along, z, BACK_TO[side])

    def on_wall(self, piece, r, c, side, z, along=0.0, outside=False):
        """A piece that hangs on a wall face of cell (r, c): inside the cell, or on the far side of that wall."""
        x, y = self.centre(r, c)
        dx, dy = OUT[side]
        reach = CELL / 2 + (0.5 if outside else -0.5)
        turn = SIDE[side][2] if outside else BACK_TO[side]
        self.put(piece, x + dx * reach - dy * along, y + dy * reach + dx * along, z, turn)


def footprint(name):
    """A building's cells as the town plan has them: (rows of characters, look-up for any cell by its place in
    the building, including the cells just outside it)."""
    with open(os.path.join(HERE, "..", "..", "plan", "out", "town.json")) as fh:
        town = json.load(fh)
    r0, c0, r1, c1 = next(b["rect"] for b in town["buildings"] if b["name"] == name)
    grid = town["grid"]

    def cell(r, c):
        rr, cc = r + r0, c + c0
        return grid[rr][cc] if 0 <= rr < len(grid) and 0 <= cc < len(grid) else "2"

    return [grid[r][c0:c1 + 1] for r in range(r0, r1 + 1)], cell


def wall_kind(here, beyond):
    """What stands on the edge between a room cell and the cell beyond it (plan/planner.py, edge())."""
    if beyond in ROOM:
        return None
    if beyond in SOLID:
        return "plain"
    return {"d": "door", "W": "window"}.get(here, "plain")


def shell(lay, rows, cell, wall="wall2_", corner="corner2", z=0.0, dress=None, pilasters=()):
    """Stands the walls and corner posts round every room cell, as the plan draws them. Returns the wall
    edges as {(r, c, side): kind} and the posts as [(x, y)], so a recipe can stand parapets on them.
    `dress` swaps a blank wall for another piece that blocks movement and sight just the same
    ({(r, c, side): "shutter"}). `pilasters` are extra posts along a straight run, as grid corners (row, column)."""
    edges = {}
    for r, row in enumerate(rows):
        for c, ch in enumerate(row):
            if ch not in ROOM:
                continue
            for side, (dr, dc) in STEP.items():
                kind = wall_kind(ch, cell(r + dr, c + dc))
                if kind:
                    edges[(r, c, side)] = kind
    for key, kind in (dress or {}).items():
        assert edges.get(key) == "plain", f"{key} is not a blank wall in the plan"
        edges[key] = kind
    for (r, c, side), kind in edges.items():
        lay.edge(wall + kind, r, c, side, z)
    # a post wherever a run of wall turns a corner
    level, upright = set(), set()          # grid corners touched by a wall running east-west / north-south
    for r, c, side in edges:
        if side in "NS":
            y = r + (side == "S")
            level |= {(y, c), (y, c + 1)}
        else:
            x = c + (side == "E")
            upright |= {(r, x), (r + 1, x)}
    posts = [(x * CELL, -y * CELL) for y, x in sorted((level & upright) | set(pilasters))]
    for x, y in posts:
        lay.put(corner, x, y, z)
    return edges, posts

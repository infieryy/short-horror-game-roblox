"""Desert Village, plan v2: one compact town.

    python town.py        # out/town.json, out/town.png, out/town-<arena>.png; adds the town to plan.json and routes.json

The town is 40 x 40 cells (320 studs) inside its wall: a market square with the well in the middle, one
landmark building on each side of it (Tea House north, Dye Works east, Cistern Hall south, Courtyard House
west) and a quarter of four small houses in every corner.

Duels still use one part of town per round. An ARENA is a band of the town three blocks long: two corner
quarters with a landmark between them. The streets out of the band are closed for the round. Bands overlap,
so every building is fought over in two arenas.

Fairness comes from the street plan: you only draw the north-west quarter. The other three are its mirror
images, so in every arena spawn A and spawn B get the same routes, cover and timings. What a building is
(tea house or cistern hall, trees or dye vats) may differ between the mirrored halves as long as it blocks
movement and sight in the same cells.

It uses the v1 planner's legend, walking model and checks (planner.py, zones.py).
"""
import json
import os

from PIL import Image, ImageDraw, ImageFont

import planner as P
import routes as R
import zones as Z

SIZE = 40
HALF = SIZE // 2

# The north-west quarter: rows 0-19, columns 0-19. Column 19 and row 19 lie against the mirror lines.
QUARTER = [
    "22222222222222222222",   # town wall
    "2...............2222",   # north lane                         | yard wall behind the landmark
    "2........11........T",   # a shed pinches the lane: no view from one corner yard to the other
    "2........11.C....T..",
    "2...222..222........",   # corner quarter: four houses, a cross of alleys between them
    "2...222..222...WiWid",   # landmark on the north side: a hall with doors north, west (two) and south
    "2...222..222...iiQii",
    "2..............diiiQ",   # alley, lined up with the hall's west doors
    "2.....L........diqiQ",
    "2.11222..222...iQiii",   # the same pinch in the west lane
    "2.11222..222...WWiid",
    "2...222..222....Csc.",   # forecourt; stairs to the hall roof, boxed in so they are entered from the foot
    "2...............k...",   # street along the square, a line of washing across it
    "2.......C.......k...",
    "2...iiiddiii..11c...",   # landmark on the west side: rooms round a court | kiosk at the corner of the square
    "2...iddddddi..11s...",
    "22..Wd..c.dWkk..cC..",
    "22T.id.T..di....C...",
    "22..id....dd......C.",
    "22..dd..T.dd...C...C",   # west door, court, east door, market square, the well under its canopy
]

BUILDINGS = [  # name, job, (row0, col0, row1, col1) in town cells, inclusive
    ("Tea House", "tea hall with an atrium; the pilot building", (5, 15, 10, 24)),
    ("Cistern Hall", "pillared hall over the town's water", (29, 15, 34, 24)),
    ("Courtyard House", "rooms and arcades round a court with trees", (14, 4, 25, 11)),
    ("Dye Works", "workshops round a yard of dye vats", (14, 28, 25, 35)),
    ("Market Square", "the well, stalls, a kiosk at each corner", (14, 14, 25, 25)),
    ("Watchtower Quarter", "four houses, the watchtower on one", (4, 4, 11, 11)),
    ("Potters' Quarter", "four houses, kilns and pots", (4, 28, 11, 35)),
    ("Gate Quarter", "four houses by the town gate", (28, 4, 35, 11)),
    ("Weavers' Quarter", "four houses, looms and cloth", (28, 28, 35, 35)),
]

# An arena is a band of town. Spawns are (row, col) cells; B is A mirrored.
ARENAS = {
    "teahouse": {"name": "Tea House", "spawns": "west / east", "rect": (0, 0, 13, 39), "A": [(1, 1), (2, 1), (1, 2)]},
    "cistern": {"name": "Cistern Hall", "spawns": "west / east", "rect": (26, 0, 39, 39), "A": [(38, 1), (37, 1), (38, 2)]},
    "courtyard": {"name": "Courtyard House", "spawns": "north / south", "rect": (0, 0, 39, 13), "A": [(1, 1), (1, 2), (2, 1)]},
    "dyeworks": {"name": "Dye Works", "spawns": "north / south", "rect": (0, 26, 39, 39), "A": [(1, 38), (1, 37), (2, 38)]},
    "market": {"name": "Market Square", "spawns": "west / east", "rect": (11, 0, 28, 39), "A": [(19, 2), (20, 2), (19, 3), (20, 3)]},
}
MIRROR = {"teahouse": "ew", "cistern": "ew", "market": "ew", "courtyard": "ns", "dyeworks": "ns"}


def town_grid():
    top = [row + row[::-1] for row in QUARTER]
    grid = [list(r) for r in top + top[::-1]]
    assert len(grid) == SIZE and all(len(r) == SIZE for r in grid)
    # The east yard is the Dye Works: vats and racks of cloth where the west court has planters and trees.
    for r in range(14, 26):
        for c in range(28, 36):
            grid[r][c] = {"T": "C", "c": "w"}.get(grid[r][c], grid[r][c])
    for row in grid:
        assert not set(row) - set(Z.LEGEND), set(row) - set(Z.LEGEND)
    return grid


def mirror(key, cell):
    r, c = cell
    return (r, SIZE - 1 - c) if MIRROR[key] == "ew" else (SIZE - 1 - r, c)


def arena_grid(town, key):
    """The town as one arena sees it: everything outside its band walled off, its spawns marked.
    Returns (grid, barriers): barriers are the street cells just outside the band that get closed."""
    spec = ARENAS[key]
    r0, c0, r1, c1 = spec["rect"]
    inside = lambda r, c: r0 <= r <= r1 and c0 <= c <= c1
    grid = [[town[r][c] if inside(r, c) or town[r][c] in P.DIGITS else "2" for c in range(SIZE)] for r in range(SIZE)]
    barriers = []
    for r in range(SIZE):
        for c in range(SIZE):
            if inside(r, c) or town[r][c] not in P.GROUND_WALK:
                continue
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < SIZE and 0 <= cc < SIZE and inside(rr, cc) and town[rr][cc] in P.GROUND_WALK \
                        and P.move_ok(town[r][c], town[rr][cc]):
                    barriers.append([r, c])
                    break
    for cell in spec["A"]:
        assert grid[cell[0]][cell[1]] == ".", (key, cell)
        grid[cell[0]][cell[1]] = "A"
        b = mirror(key, cell)
        assert grid[b[0]][b[1]] == ".", (key, b)
        grid[b[0]][b[1]] = "B"
    return grid, barriers


# ---------------------------------------------------------------- analysis (the v1 planner does the work)
_v1_build_zone = P.build_zone


def _build_zone(key):
    spec = Z.ZONES[key]
    return [list(row) for row in spec["grid"]] if "grid" in spec else _v1_build_zone(key)


P.build_zone = _build_zone


def analyse_all(town):
    out = {}
    for key, spec in ARENAS.items():
        grid, barriers = arena_grid(town, key)
        zone_key = "town_" + key
        Z.ZONES[zone_key] = {"name": spec["name"], "spawns": spec["spawns"], "grid": grid}
        g, m, lanes, tA, tB = P.analyse(zone_key)
        # how even the race is: at every spot both teams can reach within 12 s, who gets there first and by how much
        mid = min((node for node in tA if node in tB), key=lambda node: (abs(tA[node] - tB[node]), max(tA[node], tB[node])))
        m["contest_gap_s"] = round(abs(tA[mid] - tB[mid]), 2)
        m["walkable_cells"] = sum(1 for row in g for ch in row if ch in P.GROUND_WALK)
        m["unreachable"] = [[r, c] for r in range(SIZE) for c in range(SIZE) if g[r][c] in P.GROUND_WALK and (0, r, c) not in tA]
        out[key] = {"grid": g, "metrics": m, "lanes": lanes, "barriers": barriers, "routes": R.routes_for(zone_key)}
    return out


# ---------------------------------------------------------------- pictures
PX = 22
MARK = {"C": ("C", (120, 78, 52)), "c": ("c", (150, 104, 70)), "k": ("~", (190, 70, 110)), "w": ("o", (70, 150, 170)),
        "T": ("T", (70, 130, 70)), "L": ("L", (60, 60, 60)), "s": ("s", (60, 60, 60)), "Q": ("Q", (120, 78, 52)),
        "q": ("q", (150, 104, 70)), "p": ("P", (90, 60, 48)), "P": ("P", (90, 60, 48)), "A": ("A", (40, 90, 200)),
        "B": ("B", (200, 60, 50)), "d": ("", None), "W": ("", None)}


def draw(grid, path, title, lanes=(), rect=None, barriers=(), labels=True):
    font, small = ImageFont.load_default(size=13), ImageFont.load_default(size=11)
    top = 34
    im = Image.new("RGB", (SIZE * PX, SIZE * PX + top), (250, 244, 236))
    d = ImageDraw.Draw(im)
    d.text((8, 8), title, font=ImageFont.load_default(size=16), fill=(60, 40, 30))
    for r in range(SIZE):
        for c in range(SIZE):
            ch = grid[r][c]
            x, y = c * PX, r * PX + top
            d.rectangle((x, y, x + PX - 1, y + PX - 1), fill=P.COL.get(ch, (233, 207, 168)))
            if ch in MARK and MARK[ch][0]:
                d.text((x + PX / 2, y + PX / 2), MARK[ch][0], font=font, anchor="mm", fill=MARK[ch][1])
    for r in range(SIZE):                                   # room walls, doors left open, windows dashed
        for c in range(SIZE):
            for dr, dc in ((0, 1), (1, 0)):
                rr, cc = r + dr, c + dc
                if rr >= SIZE or cc >= SIZE:
                    continue
                kind = P.edge(grid[r][c], grid[rr][cc])
                if kind in ("none", "open"):
                    continue
                x0, y0 = cc * PX, rr * PX + top
                x1, y1 = (x0, y0 + PX) if dc else (x0 + PX, y0)
                d.line((x0, y0, x1, y1), fill=(96, 56, 44) if kind == "wall" else (150, 190, 200), width=3)
    for r, c in barriers:
        x, y = c * PX, r * PX + top
        d.rectangle((x + 2, y + 2, x + PX - 3, y + PX - 3), outline=(200, 60, 160), width=2)
    if rect:
        r0, c0, r1, c1 = rect
        d.rectangle((c0 * PX, r0 * PX + top, (c1 + 1) * PX - 1, (r1 + 1) * PX + top - 1), outline=(200, 60, 160), width=3)
    for i, lane in enumerate(lanes):
        pts = [((node[2] + 0.5) * PX + (i - 1) * 3, (node[1] + 0.5) * PX + top + (i - 1) * 3) for node in lane["path"]]
        d.line(pts, fill=P.LANE_COL[i % 3], width=3)
    if labels:
        for name, _, (r0, c0, r1, c1) in BUILDINGS:
            x, y = (c0 + c1 + 1) / 2 * PX, (r0 + r1 + 1) / 2 * PX + top
            box = d.textbbox((x, y), name, font=small, anchor="mm")
            d.rectangle((box[0] - 3, box[1] - 2, box[2] + 3, box[3] + 2), fill=(255, 250, 240))
            d.text((x, y), name, font=small, anchor="mm", fill=(60, 40, 30))
    im.save(path)


def main():
    town = town_grid()
    arenas = analyse_all(town)
    rows = ["".join(r) for r in town]
    draw(town, os.path.join(P.OUT, "town.png"), "Desert Village v2: the compact town (1 cell = 8 studs)")
    for key, a in arenas.items():
        m = a["metrics"]
        title = (f"{ARENAS[key]['name']} arena: meet {m['meet_s']} s, first sight {m['first_sight_s']} s, "
                 f"longest view {m['longest_sightline_studs']} studs")
        draw(a["grid"], os.path.join(P.OUT, f"town-{key}.png"), title, a["lanes"], ARENAS[key]["rect"], a["barriers"],
             labels=False)

    data = {"cell_studs": P.CELL, "story_studs": P.STORY, "size": SIZE, "grid": rows,
            "buildings": [{"name": n, "job": j, "rect": list(rect)} for n, j, rect in BUILDINGS],
            "arenas": {key: {"name": ARENAS[key]["name"], "spawns": ARENAS[key]["spawns"], "rect": list(ARENAS[key]["rect"]),
                             "spawn_a": [list(c) for c in ARENAS[key]["A"]],
                             "spawn_b": [list(mirror(key, c)) for c in ARENAS[key]["A"]],
                             "barriers": a["barriers"], "metrics": a["metrics"]} for key, a in arenas.items()}}
    with open(os.path.join(P.OUT, "town.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    # the game reads the town next to the v1 zones: plan.json -> PlanData.towns.town, routes.json -> RouteData.towns.town
    for name, value in (("plan.json", {"grid": rows, "arenas": data["arenas"]}),
                        ("routes.json", {key: a["routes"] for key, a in arenas.items()})):
        path = os.path.join(P.OUT, name)
        with open(path) as fh:
            whole = json.load(fh)
        whole["towns"] = {"town": value}
        with open(path, "w") as fh:
            json.dump(whole, fh, indent=1)

    for key, a in arenas.items():
        m = a["metrics"]
        lanes = " / ".join(f"{l['time_s']}{'*' if l['uses_roofs'] else ''}" for l in m["lanes"])
        bad = [k for k, ok in m["checks"].items() if not ok]
        print(f"{key:10s} meet {m['meet_s']:5.2f}  sight {m['first_sight_s']}  view {m['longest_sightline_studs']:3d}  "
              f"lanes {lanes}  gap {m['contest_gap_s']}  unreachable {m['unreachable_cells']}  "
              f"cells {m['walkable_cells']}  routes {len(a['routes'])}  {'FAIL ' + ','.join(bad) if bad else 'ok'}")


if __name__ == "__main__":
    main()

"""Desert Village, plan v2: one compact, uneven town built for the hunt.

    python town.py        # out/town.json, out/town.png, out/town-<arena>.png; adds the town to plan.json and routes.json

The town is 40 x 40 cells (320 studs) inside its wall: a market square in the middle, a landmark building
on each side of it (Tea House north, Dye Works east, Cistern Hall south, Courtyard House west) and a
quarter of small houses in every corner. Nothing in it is mirrored: every block has its own shape.

A duel uses one part of town per round. An ARENA is a band of the town three blocks long; the streets out
of the band are closed for the round. Bands overlap, so every building is fought over in two arenas.

The owner's brief for the layout: "give each player (when they spawn) enough options that it's actually a
hunt to find the player and a little bit tense (valorant kind of but for duels)". So an arena is judged on:
  options   how many separate places a player can be 4 and 7 seconds after spawning
  fronts    how many separate places the two can run into each other at the same moment
  seen      how much of the arena one spot can see: nowhere to stand and watch everything
  loose ends  walkable cells with one way in: few, so there is always another way round
Without a mirror, fairness is measured: each side reaches about half the ground first, has as many options,
and the spawns are picked by search (the pair of spots that balances the arena best).

It uses the v1 planner's legend, walking model and checks (planner.py, zones.py), with one correction:
a flight of stairs is entered from its foot only, the way a real flight is.
"""
import json
import math
import os

from PIL import Image, ImageDraw, ImageFont

import planner as P
import routes as R
import zones as Z

SIZE = 40

# Each row: west lane (2) | west block (9) | street (2) | middle block (11) | street (3) | east block (8) | east lane (3).
# The town wall closes it in on all four sides.
ROWS = [
    # north lane: a shed, the house behind the tea garden and a potter's store pinch it
    ("..", "......11.", "..", "....2222...", "...", "....T...", "..."),
    ("..", "......11.", "..", "....2222...", "...", "........", "..."),
    ("..", ".........", ".C", "......k....", ".c.", "..11....", "..."),
    # Watchtower Quarter | Tea House (the real building: hall, wing, porch, outside stairs) | Potters' Quarter
    ("..", "33.2222..", "..", "..11111T122", "...", "diiW..22", "..."),
    ("..", "33.2222.1", "..", "..111....22", ".T.", "WC.d..22", "..."),
    ("..", ".....22.1", ".C", "...........", "...", "Q..i.c..", "..1"),
    ("..", "11L..22..", "..", "2..WiWQ....", "..c", "d.CW....", "..1"),
    ("1.", "11.......", "..", "2.ciiid.C11", "...", ".....11L", "..."),
    ("1.", "111.c.222", "..", "2..WdWQ..11", "C..", "22.T.11.", "..."),
    ("..", "......222", "T.", "......s....", "...", "22......", "T.."),
    ("..", "222.T....", "..", ".T......kk.", "...", "22..c.11", "..."),
    # street
    ("..", "....11...", "..", "..........C", "...", "...C....", "..."),
    ("T.", "....k....", ".k", "......T....", ".Ck", "........", "..."),
    # Courtyard House | Market Square | Dye Works
    ("..", "..C.....1", "..", "11....C....", "...", "........", "..."),
    ("..", "iidiiiW.1", "..", "11s.C....C.", "...", "k.diiiiW", "..."),
    (".C", "iiidiii.1", "..", ".......C...", "...", "k.iiQiii", ".C."),
    ("..", "ii...id.1", "k.", ".C.c......k", ".C.", "..WidiQi", "..."),
    ("..", "Wi.T.ii.1", "..", ".....Cw.C.k", "...", "w..k.dii", "..."),
    ("..", "id.c.di.1", "..", "k.C........", "...", "..w..iqW", "1.."),
    ("..", "ii...iWCT", ".c", "k...C.c..C.", "...", ".w..kiii", "1.."),
    ("..", "diT..ii..", "..", ".......C...", "c..", "...k.iid", "..."),
    ("1.", "iiidiid..", "..", ".C..T....11", "...", "k.c..dii", "..."),
    ("1.", "Widiiii.c", "..", "...C..C..11", "..T", "k....idi", "..C"),
    ("..", ".........", "..", ".P.P.P.....", "C..", "...T....", "..."),
    ("..", ".11......", "..", "111111..T..", "...", ".22...11", "..."),
    # street
    ("..", "...C.1...", ".1", "........k..", "...", "..T.....", "..."),
    ("..", ".....1...", ".1", "....C......", ".k.", "........", ".C."),
    # Gate Quarter | Cistern Hall | Weavers' Quarter
    ("..", "...22....", "..", "...diiQiid.", "...", "111.....", "..."),
    ("..", "11.22.Wid", "..", ".C.ipiiipi.", "...", "111=11.k", "..."),
    (".T", "11....iii", "..", "...Wiipiiid", ".C.", "....11.k", "..."),
    ("..", "...c..diW", "C.", "11.ipiiipii", "...", ".c..L...", ".C."),
    ("..", ".T.......", "..", "11.diiiiiiW", "...", "..22..T.", "..."),
    ("..", "222.C.11.", "..", ".....dipid.", "..k", "T.22.C..", "..."),
    ("..", "222...11s", "..", ".T.c.iidii.", "...", "..222..1", "..."),
    ("..", "....C....", "..", "..1........", "...", "..C....1", "..."),
    # south lane: the gatehouse, the cistern's overflow pool, a weaver's shed
    ("..", "....2....", "..", "....vvv..11", "...", "........", "..."),
    ("..", "....2....", ".C", "....vvv..11", "...", "...11...", "..."),
    ("..", "........C", "..", "...........", "..T", "...11...", "..."),
]
WIDTHS = (2, 9, 2, 11, 3, 8, 3)

BUILDINGS = [  # name, job, (row0, col0, row1, col1) in town cells, inclusive
    ("Tea House", "tea hall with an atrium; the pilot building, at its real size", (7, 17, 10, 20)),
    ("Cistern Hall", "pillared hall over the town's water", (28, 17, 34, 24)),
    ("Courtyard House", "rooms round a court with trees", (15, 3, 23, 9)),
    ("Dye Works", "an L of workshops round a yard of vats", (15, 28, 23, 35)),
    ("Market Square", "the well, stalls, a kiosk, an arcade", (14, 14, 25, 24)),
    ("Watchtower Quarter", "the tower, an L-shaped house, a small house", (4, 3, 11, 11)),
    ("Potters' Quarter", "a U of workshops round the kiln yard", (4, 28, 11, 35)),
    ("Gate Quarter", "guard house, stable, the gatehouse", (28, 3, 35, 11)),
    ("Weavers' Quarter", "three houses, a plank between two roofs", (28, 28, 35, 35)),
]

# An arena is a band of town. Each team's spawn is picked by search from its yard (row0, col0, row1, col1).
ARENAS = {
    "teahouse": {"name": "Tea House", "spawns": "west / east", "rect": (0, 0, 13, 39),
                 "yard_a": (1, 1, 11, 2), "yard_b": (1, 36, 11, 38)},
    "cistern": {"name": "Cistern Hall", "spawns": "west / east", "rect": (26, 0, 39, 39),
                "yard_a": (28, 1, 38, 2), "yard_b": (28, 36, 38, 38)},
    "courtyard": {"name": "Courtyard House", "spawns": "north / south", "rect": (0, 0, 39, 13),
                  "yard_a": (1, 1, 3, 13), "yard_b": (36, 1, 38, 13)},
    "dyeworks": {"name": "Dye Works", "spawns": "north / south", "rect": (0, 25, 39, 39),
                 "yard_a": (1, 25, 3, 38), "yard_b": (36, 25, 38, 38)},
    "market": {"name": "Market Square", "spawns": "west / east", "rect": (12, 0, 27, 39),
               "yard_a": (12, 1, 27, 2), "yard_b": (12, 36, 27, 38)},
}

TARGETS = {
    "options_4s_min": 3,          # separate places a player can be 4 s after spawning
    "options_7s_min": 4,
    "fronts_min": 4,              # separate places both can arrive at the same moment
    "seen_max": 0.30,             # no spot sees more than this share of the arena's ground
    "first_share": (0.44, 0.56),  # share of the ground team A reaches first
    "options_gap_max": 1,         # how many more options one team may have than the other
}
FRONT_WINDOW = 0.5                # seconds apart that still counts as "the same moment"
SIDES = R.SIDES                   # the order the graybox builder looks for the roof a flight serves


def town_grid():
    assert len(ROWS) == SIZE - 2
    grid = [list("2" * SIZE)]
    for i, row in enumerate(ROWS):
        assert tuple(len(part) for part in row) == WIDTHS, (i + 1, [len(part) for part in row])
        grid.append(list("2" + "".join(row) + "2"))
    grid.append(list("2" * SIZE))
    for row in grid:
        assert not set(row) - set(Z.LEGEND), set(row) - set(Z.LEGEND)
    return grid


# ---------------------------------------------------------------- stairs are entered from the foot
def stairs_ends(g, r, c):
    """For a stairs cell: (the roof cell the flight serves, the street cell at its foot)."""
    n = len(g)
    for dr, dc in SIDES:
        rr, cc = r + dr, c + dc
        if 0 <= rr < n and 0 <= cc < n and P.height(g[rr][cc]) == 1:
            return (rr, cc), (r - dr, c - dc)
    return None, None


_v1_neighbors = P.neighbors


def neighbors(g, node):
    layer, r, c = node
    for nxt, cost in _v1_neighbors(g, node):
        nl, nr, nc = nxt
        if layer == 0 and nl == 0:
            if g[nr][nc] == "s" and stairs_ends(g, nr, nc)[1] != (r, c):
                continue
            if g[r][c] == "s" and stairs_ends(g, r, c)[1] != (nr, nc):
                continue
        elif layer == 0 and g[r][c] == "s" and stairs_ends(g, r, c)[0] != (nr, nc):
            continue
        elif nl == 0 and g[nr][nc] == "s" and stairs_ends(g, nr, nc)[0] != (r, c):
            continue
        yield nxt, cost


P.neighbors = neighbors
_v1_build_zone = P.build_zone


def _build_zone(key):
    spec = Z.ZONES[key]
    return [list(row) for row in spec["grid"]] if "grid" in spec else _v1_build_zone(key)


P.build_zone = _build_zone


# ---------------------------------------------------------------- arenas
def in_rect(rect, r, c):
    return rect[0] <= r <= rect[2] and rect[1] <= c <= rect[3]


def arena_base(town, key):
    """The town as one arena sees it: everything outside its band walled off.
    Returns (grid, barriers): barriers are the street cells just outside the band that get closed."""
    rect = ARENAS[key]["rect"]
    grid = [[town[r][c] if in_rect(rect, r, c) or town[r][c] in P.DIGITS else "2" for c in range(SIZE)] for r in range(SIZE)]
    barriers = []
    for r in range(SIZE):
        for c in range(SIZE):
            if in_rect(rect, r, c) or town[r][c] not in P.GROUND_WALK:
                continue
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if 0 <= rr < SIZE and 0 <= cc < SIZE and in_rect(rect, rr, cc) and town[rr][cc] in P.GROUND_WALK \
                        and P.move_ok(town[r][c], town[rr][cc]):
                    barriers.append([r, c])
                    break
    return grid, barriers


def clusters(g, cells):
    """Groups of ground cells you can walk between without leaving the group. Two cells with a wall between
    them are different places, however close."""
    left, groups = set(cells), []
    while left:
        stack, group = [left.pop()], []
        while stack:
            r, c = stack.pop()
            group.append((r, c))
            for (layer, rr, cc), _ in P.neighbors(g, (0, r, c)):
                if layer == 0 and (rr, cc) in left:
                    left.remove((rr, cc))
                    stack.append((rr, cc))
        groups.append(group)
    return groups


def options(g, dist, seconds):
    """How many separate places a player can be `seconds` after spawning."""
    ring = [(r, c) for (layer, r, c), t in dist.items() if layer == 0 and seconds - 0.5 <= t <= seconds + 0.5]
    return len(clusters(g, ring))


def ground_times(g, sources):
    dist, _ = P.dijkstra(g, [(0, *cell) for cell in sources])
    return dist


def pick_spawns(g, key):
    """The pair of spots, one in each yard, that splits the arena most evenly while both teams still have
    their options and cannot see each other. Each spawn is two cells: the spot and the open cell beside it."""
    spec = ARENAS[key]

    def spots(yard):
        out = []
        for r in range(yard[0], yard[2] + 1):
            for c in range(yard[1], yard[3] + 1):
                if g[r][c] != ".":
                    continue
                beside = next(((r + dr, c + dc) for dr, dc in ((0, 1), (1, 0), (0, -1), (-1, 0))
                               if in_rect(yard, r + dr, c + dc) and g[r + dr][c + dc] == "."), None)
                if beside:
                    out.append(((r, c), beside))
        return out

    ground = [(r, c) for r in range(SIZE) for c in range(SIZE) if g[r][c] in P.GROUND_WALK]
    times = {}
    for spot, beside in spots(spec["yard_a"]) + spots(spec["yard_b"]):
        times[spot] = ground_times(g, (spot, beside))
    best = None
    for a, a2 in spots(spec["yard_a"]):
        ta = times[a]
        for b, b2 in spots(spec["yard_b"]):
            tb = times[b]
            if (0, *b) not in ta:
                continue
            first = sum(1 for cell in ground if ta.get((0, *cell), 1e9) < tb.get((0, *cell), 1e9))
            share = first / len(ground)
            cross = ta[(0, *b)]
            oa, ob = (options(g, ta, 4), options(g, ta, 7)), (options(g, tb, 4), options(g, tb, 7))
            gap = abs(oa[0] - ob[0]) + abs(oa[1] - ob[1])
            # an even split and a meeting inside the time limit first; then more options, a smaller gap
            # between the teams, a longer way across
            score = (abs(share - 0.5) > 0.04, cross / 2 > P.TARGETS["meet_max"] - 0.3, -min(oa[0], ob[0], 4), -min(oa[1], ob[1], 5),
                     gap, abs(share - 0.5), -cross)
            if best is None or score < best[0]:
                best = (score, (a, a2), (b, b2))
    return best[1], best[2]


def hunt(g, tA, tB):
    """The measures the brief asks for. tA, tB: travel times from each spawn (planner nodes)."""
    ground = [(r, c) for r in range(SIZE) for c in range(SIZE) if g[r][c] in P.GROUND_WALK and (0, r, c) in tA]
    front = [cell for cell in ground if abs(tA[(0, *cell)] - tB.get((0, *cell), 1e9)) <= FRONT_WINDOW]
    fronts = clusters(g, front)
    # what each spot can see
    sees = {cell: 0 for cell in ground}
    for i, a in enumerate(ground):
        for b in ground[i + 1:]:
            if P.los(g, a, b):
                sees[a] += 1
                sees[b] += 1
    share = {cell: n / (len(ground) - 1) for cell, n in sees.items()}
    watch = max(share, key=share.get)
    loose = 0
    for r, c in ground:
        ways = sum(1 for nxt, _ in P.neighbors(g, (0, r, c)) if nxt[0] == 0 and (nxt[1] == r or nxt[2] == c))
        if g[r][c] in "sL":
            ways += 1                                    # the way up
        loose += ways <= 1
    first = sum(1 for cell in ground if tA[(0, *cell)] < tB.get((0, *cell), 1e9))
    return {
        "options_a": [options(g, tA, 4), options(g, tA, 7)], "options_b": [options(g, tB, 4), options(g, tB, 7)],
        "fronts": len(fronts),
        "front_cells": [list(cell) for cell in front],
        "front_spread_studs": round(max((math.hypot(a[0] - b[0], a[1] - b[1]) for a in front for b in front), default=0) * P.CELL),
        "seen_mean": round(sum(share.values()) / len(share), 3), "seen_max": round(share[watch], 3), "seen_max_cell": list(watch),
        "loose_ends": loose,
        "first_share_a": round(first / len(ground), 3),
    }


def analyse_all(town):
    out = {}
    for key, spec in ARENAS.items():
        grid, barriers = arena_base(town, key)
        spawn_a, spawn_b = pick_spawns(grid, key)
        for cell in spawn_a:
            grid[cell[0]][cell[1]] = "A"
        for cell in spawn_b:
            grid[cell[0]][cell[1]] = "B"
        zone_key = "town_" + key
        Z.ZONES[zone_key] = {"name": spec["name"], "spawns": spec["spawns"], "grid": grid}
        g, m, lanes, tA, tB = P.analyse(zone_key)
        m.update(hunt(g, tA, tB))
        T = TARGETS
        m["checks"].update({
            "options": min(m["options_a"][0], m["options_b"][0]) >= T["options_4s_min"]
                       and min(m["options_a"][1], m["options_b"][1]) >= T["options_7s_min"],
            "fronts": m["fronts"] >= T["fronts_min"],
            "seen": m["seen_max"] <= T["seen_max"],
            "even": T["first_share"][0] <= m["first_share_a"] <= T["first_share"][1]
                    and abs(m["options_a"][0] - m["options_b"][0]) <= T["options_gap_max"],
        })
        m["walkable_cells"] = sum(1 for row in g for ch in row if ch in P.GROUND_WALK)
        out[key] = {"grid": g, "metrics": m, "lanes": lanes, "barriers": barriers, "routes": R.routes_for(zone_key),
                    "spawn_a": [list(c) for c in spawn_a], "spawn_b": [list(c) for c in spawn_b]}
    return out


# ---------------------------------------------------------------- pictures
PX = 22
MARK = {"C": ("C", (120, 78, 52)), "c": ("c", (150, 104, 70)), "k": ("~", (190, 70, 110)), "w": ("o", (70, 150, 170)),
        "T": ("T", (70, 130, 70)), "L": ("L", (60, 60, 60)), "s": ("s", (60, 60, 60)), "Q": ("Q", (120, 78, 52)),
        "q": ("q", (150, 104, 70)), "p": ("P", (90, 60, 48)), "P": ("P", (90, 60, 48)), "A": ("A", (40, 90, 200)),
        "B": ("B", (200, 60, 50)), "=": ("=", (120, 78, 52))}


def draw(grid, path, title, lanes=(), rect=None, barriers=(), front=(), labels=True):
    font, small = ImageFont.load_default(size=13), ImageFont.load_default(size=11)
    top = 34
    im = Image.new("RGB", (SIZE * PX, SIZE * PX + top), (250, 244, 236))
    d = ImageDraw.Draw(im)
    d.text((8, 8), title, font=ImageFont.load_default(size=15), fill=(60, 40, 30))
    for r in range(SIZE):
        for c in range(SIZE):
            ch = grid[r][c]
            x, y = c * PX, r * PX + top
            d.rectangle((x, y, x + PX - 1, y + PX - 1), fill=P.COL.get(ch, (233, 207, 168)))
    for r, c in front:                                      # where the two can arrive at the same moment
        x, y = c * PX, r * PX + top
        d.rectangle((x, y, x + PX - 1, y + PX - 1), fill=(250, 226, 130))
    for r in range(SIZE):
        for c in range(SIZE):
            ch = grid[r][c]
            if ch in MARK:
                d.text((c * PX + PX / 2, r * PX + top + PX / 2), MARK[ch][0], font=font, anchor="mm", fill=MARK[ch][1])
    for r in range(SIZE):                                   # room walls, doors left open, windows pale
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
        title = (f"{ARENAS[key]['name']} arena: {m['options_a'][1]} and {m['options_b'][1]} places to be after 7 s, "
                 f"{m['fronts']} places to collide (yellow), meet {m['meet_s']} s")
        draw(a["grid"], os.path.join(P.OUT, f"town-{key}.png"), title, a["lanes"], ARENAS[key]["rect"], a["barriers"],
             m["front_cells"], labels=False)

    data = {"cell_studs": P.CELL, "story_studs": P.STORY, "size": SIZE, "grid": rows, "targets": TARGETS,
            "buildings": [{"name": n, "job": j, "rect": list(rect)} for n, j, rect in BUILDINGS],
            "arenas": {key: {"name": ARENAS[key]["name"], "spawns": ARENAS[key]["spawns"], "rect": list(ARENAS[key]["rect"]),
                             "spawn_a": a["spawn_a"], "spawn_b": a["spawn_b"], "barriers": a["barriers"],
                             "metrics": a["metrics"]} for key, a in arenas.items()}}
    with open(os.path.join(P.OUT, "town.json"), "w") as fh:
        json.dump(data, fh, indent=1)
    # the game reads the town next to the v1 zones: plan.json -> PlanData.towns.town, routes.json -> RouteData.towns.town
    slim = {key: {k: v for k, v in a.items() if k != "metrics"} for key, a in data["arenas"].items()}
    for name, value in (("plan.json", {"grid": rows, "arenas": slim}), ("routes.json", {key: a["routes"] for key, a in arenas.items()})):
        path = os.path.join(P.OUT, name)
        with open(path) as fh:
            whole = json.load(fh)
        whole["towns"] = {"town": value}
        with open(path, "w") as fh:
            json.dump(whole, fh, indent=1)

    for key, a in arenas.items():
        m = a["metrics"]
        lanes = "/".join(f"{l['time_s']:.0f}{'*' if l['uses_roofs'] else ''}" for l in m["lanes"])
        bad = [k for k, ok in m["checks"].items() if not ok]
        print(f"{key:9s} A{a['spawn_a'][0]} B{a['spawn_b'][0]} meet {m['meet_s']:.1f} sight {m['first_sight_s']} view {m['longest_sightline_studs']} "
              f"lanes {lanes} | options A{m['options_a']} B{m['options_b']} fronts {m['fronts']} ({m['front_spread_studs']} studs apart) "
              f"seen {m['seen_mean']:.2f}/{m['seen_max']:.2f}@{m['seen_max_cell']} loose {m['loose_ends']} A first {m['first_share_a']:.2f} "
              f"unreach {m['unreachable_cells']} | {'FAIL ' + ','.join(bad) if bad else 'ok'}")


if __name__ == "__main__":
    main()

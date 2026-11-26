"""Desert Village grid planner.

Reads the zone layouts in zones.py, builds each full zone from its top half
(180-degree rotation, so both teams get identical routes), checks fairness and
renders the plan.

    python3 planner.py            # validate, render, export
    python3 planner.py market     # only one zone

Outputs go to ./out: one PNG per zone, town-overview.png, plan.json, metrics.md
"""
import heapq
import json
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

import zones as Z

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")

# ---------------------------------------------------------------- constants
CELL = Z.CELL_STUDS          # studs per grid cell
WALK = Z.WALK_SPEED          # studs / s
STORY = Z.STORY_STUDS        # studs per story
CLIMB = Z.CLIMB_SPEED        # studs / s on ladders
SIZE = Z.ZONE_CELLS

DIGITS = set("123")
ROOM = set("idWpqQ")                       # interior cells (thin walls drawn around them)
GROUND_WALK = set(".idWsL=vABk")           # walkable at ground level
SIGHT_BLOCK = DIGITS | set("CPTkQp")       # cells that block eye-level sight
SHALLOW = set("v")

TARGETS = {
    "meet_min": 6.0, "meet_max": 10.0,    # seconds until both teams can reach the same spot
    "first_sight_min": 3.5,               # seconds: no spawn-to-spawn or near-spawn sight
    "sightline_max": 200,                 # studs (25 cells)
    "lanes_min": 3,
}


# ---------------------------------------------------------------- zone build
def build_zone(key):
    spec = Z.ZONES[key]
    half = spec["half"]
    assert len(half) == SIZE // 2, f"{key}: need {SIZE // 2} rows, got {len(half)}"
    for i, row in enumerate(half):
        assert len(row) == SIZE, f"{key} row {i}: {len(row)} chars: {row!r}"
        bad = set(row) - set(Z.LEGEND)
        assert not bad, f"{key} row {i}: unknown chars {bad}"
    bottom = []
    for row in reversed(half):
        bottom.append(row[::-1].replace("A", "B"))
    grid = list(half) + bottom
    return [list(r) for r in grid]


def height(ch):
    if ch in DIGITS:
        return int(ch)
    if ch in ROOM or ch == "=":
        return 1
    return 0


def edge(a, b):
    """Kind of the boundary between two orthogonally adjacent cells."""
    ar, br = a in ROOM, b in ROOM
    if ar == br:
        return "none"
    r, o = (a, b) if ar else (b, a)
    if o in DIGITS:
        return "wall"
    if r == "d":
        return "open"
    if r == "W":
        return "window"
    return "wall"


def move_ok(a, b):
    return edge(a, b) in ("none", "open")


def sight_ok(a, b):
    return edge(a, b) in ("none", "open", "window")


# ---------------------------------------------------------------- graph
def neighbors(g, node):
    """Yield (next_node, cost_seconds). node = (layer, r, c); layer 0 ground, >0 roof height."""
    layer, r, c = node
    n = len(g)
    here = g[r][c]
    if layer == 0:
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < n and 0 <= cc < n):
                continue
            t = g[rr][cc]
            if t not in GROUND_WALK:
                continue
            if dr and dc:
                a, b = g[r + dr][c], g[r][c + dc]
                if a not in GROUND_WALK or b not in GROUND_WALK:
                    continue
                if not (move_ok(here, a) and move_ok(a, t) and move_ok(here, b) and move_ok(b, t)):
                    continue
                dist = math.sqrt(2)
            else:
                if not move_ok(here, t):
                    continue
                dist = 1.0
            cost = dist * CELL / WALK
            if t in SHALLOW or here in SHALLOW:
                cost *= 1.6
            yield (0, rr, cc), cost
        # vertical links
        if here in "Ls":
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                rr, cc = r + dr, c + dc
                if not (0 <= rr < n and 0 <= cc < n):
                    continue
                h = height(g[rr][cc])
                if h == 0:
                    continue
                if here == "L":
                    yield (h, rr, cc), h * STORY / CLIMB + 0.4
                elif h == 1:
                    yield (1, rr, cc), 0.6
        if here == "=":
            pass  # plank: ground below is plain street; roof link handled from roof side
    else:
        h = layer
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < n and 0 <= cc < n):
                continue
            if height(g[rr][cc]) != h:
                continue
            if dr and dc and (height(g[r + dr][c]) != h or height(g[r][c + dc]) != h):
                continue
            yield (h, rr, cc), (math.sqrt(2) if dr and dc else 1.0) * CELL / WALK
        # back down a ladder / stairs
        for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            rr, cc = r + dr, c + dc
            if not (0 <= rr < n and 0 <= cc < n):
                continue
            t = g[rr][cc]
            if t == "L":
                yield (0, rr, cc), h * STORY / CLIMB * 0.6 + 0.3
            elif t == "s" and h == 1:
                yield (0, rr, cc), 0.6


def dijkstra(g, sources, penalty=None):
    dist, prev = {}, {}
    pq = []
    for s in sources:
        dist[s] = 0.0
        heapq.heappush(pq, (0.0, s))
    while pq:
        d, u = heapq.heappop(pq)
        if d > dist.get(u, 1e18):
            continue
        for v, w in neighbors(g, u):
            if penalty:
                w *= penalty.get((v[1], v[2]), 1.0)
            nd = d + w
            if nd < dist.get(v, 1e18):
                dist[v] = nd
                prev[v] = u
                heapq.heappush(pq, (nd, v))
    return dist, prev


def path_to(prev, node):
    out = [node]
    while node in prev:
        node = prev[node]
        out.append(node)
    return out[::-1]


def path_time(g, path):
    t = 0.0
    for a, b in zip(path, path[1:]):
        for v, w in neighbors(g, a):
            if v == b:
                t += w
                break
    return t


# ---------------------------------------------------------------- sight
def los(g, a, b):
    """Eye-level line of sight between centres of ground cells a and b."""
    (r0, c0), (r1, c1) = a, b
    x0, y0, x1, y1 = c0 + 0.5, r0 + 0.5, c1 + 0.5, r1 + 0.5
    dx, dy = x1 - x0, y1 - y0
    r, c = r0, c0
    sx = 1 if dx > 0 else -1
    sy = 1 if dy > 0 else -1
    tdx = abs(1 / dx) if dx else 1e18
    tdy = abs(1 / dy) if dy else 1e18
    tmx = (1 - (x0 % 1) if dx > 0 else (x0 % 1)) * tdx if dx else 1e18
    tmy = (1 - (y0 % 1) if dy > 0 else (y0 % 1)) * tdy if dy else 1e18
    if not dx:
        tmx = 1e18
    if not dy:
        tmy = 1e18
    while (r, c) != (r1, c1):
        cur = g[r][c]
        if abs(tmx - tmy) < 1e-9:
            # passing exactly through a corner: need one clear L path
            ok = False
            for (ra, ca) in ((r, c + sx), (r + sy, c)):
                mid = g[ra][ca]
                nxt = g[r + sy][c + sx]
                if mid in SIGHT_BLOCK:
                    continue
                if sight_ok(cur, mid) and sight_ok(mid, nxt):
                    ok = True
                    break
            r, c = r + sy, c + sx
            tmx += tdx
            tmy += tdy
        elif tmx < tmy:
            nxt = g[r][c + sx]
            ok = sight_ok(cur, nxt)
            c += sx
            tmx += tdx
        else:
            nxt = g[r + sy][c]
            ok = sight_ok(cur, nxt)
            r += sy
            tmy += tdy
        if not ok:
            return False
        if (r, c) != (r1, c1) and g[r][c] in SIGHT_BLOCK:
            return False
    return True


# ---------------------------------------------------------------- analysis
def analyse(key):
    g = build_zone(key)
    n = len(g)
    A = [(0, r, c) for r in range(n) for c in range(n) if g[r][c] == "A"]
    B = [(0, r, c) for r in range(n) for c in range(n) if g[r][c] == "B"]
    assert A and B, f"{key}: missing spawns"
    tA, _ = dijkstra(g, A)
    tB, _ = dijkstra(g, B)

    ground = [(r, c) for r in range(n) for c in range(n) if g[r][c] in GROUND_WALK]
    unreachable = [p for p in ground if (0, *p) not in tA]

    # meet time: earliest moment both teams can stand on the same spot
    meet, meet_node = 1e18, None
    for node, ta in tA.items():
        tb = tB.get(node)
        if tb is None:
            continue
        m = max(ta, tb)
        if m < meet:
            meet, meet_node = m, node

    # sight: all ground pairs
    reach = [p for p in ground if (0, *p) in tA]
    first_sight, first_pair = 1e18, None
    longest, longest_pair = 0.0, None
    for i in range(len(reach)):
        a = reach[i]
        ta = tA[(0, *a)]
        tb_a = tB.get((0, *a), 1e18)
        for j in range(i + 1, len(reach)):
            b = reach[j]
            d = math.hypot(a[0] - b[0], a[1] - b[1])
            t1 = max(ta, tB.get((0, *b), 1e18))
            t2 = max(tA[(0, *b)], tb_a)
            tmin = min(t1, t2)
            if d * CELL <= longest and tmin >= first_sight:
                continue
            if not los(g, a, b):
                continue
            if d * CELL > longest:
                longest, longest_pair = d * CELL, (a, b)
            if tmin < first_sight:
                first_sight = tmin
                first_pair = (a, b) if t1 <= t2 else (b, a)

    # lanes: diverse routes from A to B
    lanes = []
    penalty = {}
    for _ in range(6):
        dist, prev = dijkstra(g, A, penalty)
        goal = min((nd for nd in B if nd in dist), key=lambda nd: dist[nd])
        p = path_to(prev, goal)
        cells = {(nd[1], nd[2]) for nd in p}
        if all(len(cells & l["cells"]) / len(cells) < 0.6 for l in lanes):
            lanes.append({"path": p, "cells": cells, "time": path_time(g, p),
                          "roof": any(nd[0] > 0 for nd in p)})
        for (r, c) in cells:
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    penalty[(r + dr, c + dc)] = penalty.get((r + dr, c + dc), 1.0) * 4.0
        if len(lanes) >= 3:
            break

    counts = {k: sum(row.count(k) for row in g) for k in "cCkTwvLs="}
    m = {
        "key": key,
        "name": Z.ZONES[key]["name"],
        "spawns": Z.ZONES[key]["spawns"],
        "meet_s": round(meet, 2),
        "meet_cell": meet_node and [meet_node[1], meet_node[2], meet_node[0]],
        "first_sight_s": round(first_sight, 2) if first_pair else None,
        "first_sight_pair": first_pair,
        "longest_sightline_studs": round(longest),
        "longest_pair": longest_pair,
        "lanes": [{"time_s": round(l["time"], 2), "uses_roofs": l["roof"]} for l in lanes],
        "unreachable_cells": len(unreachable),
        "cover_low": counts["c"], "cover_high": counts["C"],
        "cloth": counts["k"], "ladders": counts["L"], "stairs": counts["s"], "planks": counts["="],
    }
    checks = {
        "meet": TARGETS["meet_min"] <= meet <= TARGETS["meet_max"],
        "first_sight": first_sight >= TARGETS["first_sight_min"],
        "sightline": longest <= TARGETS["sightline_max"],
        "lanes": len(lanes) >= TARGETS["lanes_min"],
        "reachable": not unreachable,
    }
    m["checks"] = checks
    return g, m, lanes, tA, tB


# ---------------------------------------------------------------- render
COL = {
    ".": (233, 207, 168), "A": (233, 207, 168), "B": (233, 207, 168),
    "i": (214, 176, 150), "d": (214, 176, 150), "W": (214, 176, 150),
    "p": (110, 74, 58), "q": (214, 176, 150), "Q": (214, 176, 150),
    "1": (196, 128, 100), "2": (160, 96, 76), "3": (122, 70, 56),
    "c": (233, 207, 168), "C": (233, 207, 168), "w": (233, 207, 168),
    "v": (143, 211, 207), "P": (110, 74, 58), "T": (233, 207, 168),
    "k": (233, 207, 168), "L": (233, 207, 168), "s": (222, 190, 150),
    "=": (233, 207, 168), "X": (233, 207, 168),
}
LANE_COL = [(58, 123, 213), (46, 160, 90), (190, 70, 160)]


def font(size, bold=False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    return ImageFont.truetype(os.path.join("/usr/share/fonts/truetype/dejavu", name), size)


def draw_grid(d, g, ox, oy, s, detail=True):
    n = len(g)
    for r in range(n):
        for c in range(n):
            ch = g[r][c]
            x, y = ox + c * s, oy + r * s
            d.rectangle([x, y, x + s, y + s], fill=COL[ch])
            m = max(1, s // 6)
            if ch == "c":
                d.rectangle([x + m, y + m, x + s - m, y + s - m], fill=(170, 126, 72))
            elif ch == "C":
                d.rectangle([x + 1, y + 1, x + s - 1, y + s - 1], fill=(94, 67, 38))
            elif ch in "qQ":
                f = (170, 126, 72) if ch == "q" else (94, 67, 38)
                d.rectangle([x + m, y + m, x + s - m, y + s - m], fill=f)
            elif ch == "w":
                d.ellipse([x + 1, y + 1, x + s - 1, y + s - 1], fill=(79, 179, 176))
            elif ch == "T":
                d.ellipse([x, y, x + s, y + s], fill=(111, 154, 61))
            elif ch == "k":
                for i in range(0, s, max(2, s // 4)):
                    d.line([x + i, y, x + i, y + s], fill=(178, 74, 138), width=max(1, s // 8))
            elif ch == "L" and detail:
                d.line([x + s * .3, y, x + s * .3, y + s], fill=(110, 70, 40), width=2)
                d.line([x + s * .7, y, x + s * .7, y + s], fill=(110, 70, 40), width=2)
                for k in range(1, 4):
                    d.line([x + s * .3, y + s * k / 4, x + s * .7, y + s * k / 4], fill=(110, 70, 40), width=2)
            elif ch == "s" and detail:
                for k in range(1, 4):
                    d.line([x, y + s * k / 4, x + s, y + s * k / 4], fill=(170, 130, 95), width=1)
            elif ch == "=":
                for k in range(0, s, max(3, s // 4)):
                    d.rectangle([x + 1, y + k, x + s - 1, y + k + max(1, s // 8)], fill=(150, 100, 60))
            elif ch == "X":
                for k in range(-s, s, max(3, s // 3)):
                    d.line([x + k, y, x + k + s, y + s], fill=(200, 60, 50), width=max(1, s // 10))
            elif ch in "AB" and detail:
                f = (58, 123, 213) if ch == "A" else (213, 85, 58)
                d.ellipse([x + m, y + m, x + s - m, y + s - m], fill=f)
    if detail:
        for i in range(n + 1):
            d.line([ox + i * s, oy, ox + i * s, oy + n * s], fill=(0, 0, 0, 18), width=1)
            d.line([ox, oy + i * s, ox + n * s, oy + i * s], fill=(0, 0, 0, 18), width=1)
    # walls / windows / doors on edges
    ww = max(2, s // 7)
    for r in range(n):
        for c in range(n):
            for dr, dc in ((0, 1), (1, 0)):
                rr, cc = r + dr, c + dc
                if rr >= n or cc >= n:
                    continue
                k = edge(g[r][c], g[rr][cc])
                if k == "none":
                    continue
                if dc:
                    seg = [ox + cc * s, oy + r * s, ox + cc * s, oy + (r + 1) * s]
                else:
                    seg = [ox + c * s, oy + rr * s, ox + (c + 1) * s, oy + rr * s]
                if k == "wall":
                    d.line(seg, fill=(60, 35, 30), width=ww)
                elif k == "window":
                    d.line(seg, fill=(60, 35, 30), width=ww)
                    d.line(seg, fill=(150, 210, 235), width=max(1, ww - 2))
    # height labels on building mass
    if detail and s >= 16:
        f = font(max(8, s // 2))
        for r in range(n):
            for c in range(n):
                if g[r][c] in DIGITS and (r + c) % 3 == 0:
                    d.text((ox + c * s + s / 2, oy + r * s + s / 2), g[r][c], fill=(255, 235, 215), font=f, anchor="mm")


def render_zone(g, m, lanes):
    s = 26
    n = len(g)
    pad = 30
    panel = 430
    W, H = pad * 2 + n * s + panel, pad * 2 + n * s + 60
    img = Image.new("RGB", (W, H), (250, 244, 236))
    d = ImageDraw.Draw(img, "RGBA")
    ox, oy = pad, pad + 40
    d.text((pad, 14), f"{m['name']}  ({m['spawns']} spawns)", fill=(60, 35, 30), font=font(22, True))
    draw_grid(d, g, ox, oy, s)
    # lanes
    for li, lane in enumerate(lanes):
        col = LANE_COL[li % 3]
        pts = [(ox + c * s + s / 2 + (li - 1) * 3, oy + r * s + s / 2 + (li - 1) * 3) for (_, r, c) in lane["path"]]
        d.line(pts, fill=col + (220,), width=4, joint="curve")
        for (lay, r, c), (x, y) in zip(lane["path"], pts):
            if lay > 0:
                d.ellipse([x - 3, y - 3, x + 3, y + 3], fill=(255, 255, 255), outline=col)
    # first sight + longest sightline
    if m["first_sight_pair"]:
        (a, b) = m["first_sight_pair"]
        d.line([ox + a[1] * s + s / 2, oy + a[0] * s + s / 2, ox + b[1] * s + s / 2, oy + b[0] * s + s / 2],
               fill=(230, 40, 40, 200), width=2)
    if m["longest_pair"]:
        (a, b) = m["longest_pair"]
        x0, y0 = ox + a[1] * s + s / 2, oy + a[0] * s + s / 2
        x1, y1 = ox + b[1] * s + s / 2, oy + b[0] * s + s / 2
        steps = int(math.hypot(x1 - x0, y1 - y0) / 8)
        for k in range(0, steps, 2):
            d.line([x0 + (x1 - x0) * k / steps, y0 + (y1 - y0) * k / steps,
                    x0 + (x1 - x0) * (k + 1) / steps, y0 + (y1 - y0) * (k + 1) / steps], fill=(40, 40, 40, 190), width=2)
    # panel
    px = ox + n * s + 24
    y = oy
    f, fb = font(15), font(15, True)

    def line(txt, ok=None, bold=False):
        nonlocal y
        colr = (60, 35, 30) if ok is None else ((40, 140, 70) if ok else (200, 60, 40))
        d.text((px, y), txt, fill=colr, font=fb if bold else f)
        y += 22

    ck = m["checks"]
    line("Fairness checks", bold=True)
    line(f"Meet time: {m['meet_s']} s  (target {TARGETS['meet_min']:.0f}-{TARGETS['meet_max']:.0f})", ck["meet"])
    fs = m["first_sight_s"]
    line(f"First sight: {fs} s  (min {TARGETS['first_sight_min']})", ck["first_sight"])
    line(f"Longest sightline: {m['longest_sightline_studs']} studs (max {TARGETS['sightline_max']})", ck["sightline"])
    line(f"Lanes: {len(m['lanes'])} (min {TARGETS['lanes_min']})", ck["lanes"])
    line(f"Unreachable cells: {m['unreachable_cells']}", ck["reachable"])
    line("Both teams: identical (rotated layout)", True)
    y += 10
    line("Lanes A -> B", bold=True)
    for li, l in enumerate(m["lanes"]):
        d.rectangle([px, y + 5, px + 18, y + 11], fill=LANE_COL[li])
        d.text((px + 26, y), f"{l['time_s']} s{'  (via roofs)' if l['uses_roofs'] else ''}", fill=(60, 35, 30), font=f)
        y += 22
    y += 10
    line("Cover", bold=True)
    line(f"Low {m['cover_low']}   High {m['cover_high']}   Cloth {m['cloth']}")
    line(f"Ladders {m['ladders']}   Stairs {m['stairs']}   Planks {m['planks']}")
    y += 10
    line("Overlay", bold=True)
    d.line([px, y + 8, px + 24, y + 8], fill=(230, 40, 40), width=2); d.text((px + 30, y), "earliest sight contact", fill=(60, 35, 30), font=f); y += 22
    d.line([px, y + 8, px + 24, y + 8], fill=(40, 40, 40), width=2); d.text((px + 30, y), "longest sightline", fill=(60, 35, 30), font=f); y += 22
    d.ellipse([px + 8, y + 4, px + 16, y + 12], fill=(255, 255, 255), outline=(58, 123, 213)); d.text((px + 30, y), "lane on a roof", fill=(60, 35, 30), font=f); y += 30
    y = legend(d, px, y, f, fb)
    d.text((pad, H - 26), f"1 cell = {CELL} studs   zone = {n}x{n} cells = {n * CELL} studs   walk {WALK} studs/s",
           fill=(120, 100, 90), font=font(13))
    for i in range(0, n, 4):
        d.text((ox + i * s + 2, oy - 14), str(i), fill=(150, 130, 120), font=font(10))
        d.text((ox - 18, oy + i * s + 2), str(i), fill=(150, 130, 120), font=font(10))
    return img


def legend(d, px, y, f, fb):
    d.text((px, y), "Legend", fill=(60, 35, 30), font=fb)
    y += 24
    items = [(".", "street / open ground"), ("i", "interior (enterable)"), ("1", "building, 1 story (roof walkable)"),
             ("2", "building, 2 stories"), ("3", "tower, 3 stories"), ("c", "low cover (crates, sacks)"),
             ("C", "high cover (blocks sight)"), ("k", "hanging cloth (walk through, blocks sight)"),
             ("w", "water / vat / well (blocks movement)"), ("v", "shallow water (slow)"), ("P", "pillar"),
             ("T", "tree"), ("L", "ladder"), ("s", "stairs"), ("=", "plank / bridge (walk under + on top)"),
             ("X", "zone barrier"), ("A", "spawn A"), ("B", "spawn B")]
    for ch, txt in items:
        g = [[ch]]
        draw_grid(d, g, px, y, 16)
        d.text((px + 26, y), txt, fill=(60, 35, 30), font=f)
        y += 20
    d.line([px, y + 8, px + 16, y + 8], fill=(60, 35, 30), width=3); d.text((px + 26, y), "wall (gap = door)", fill=(60, 35, 30), font=f); y += 20
    d.line([px, y + 8, px + 16, y + 8], fill=(60, 35, 30), width=4); d.line([px, y + 8, px + 16, y + 8], fill=(150, 210, 235), width=2)
    d.text((px + 26, y), "window", fill=(60, 35, 30), font=f)
    return y + 20


def reserve_block():
    n = SIZE
    g = [["2"] * n for _ in range(n)]
    for r in range(1, n - 1):
        for c in range(1, n - 1):
            g[r][c] = "1" if ((r // 5) + (c // 5)) % 2 else "2"
    for i in range(n):
        for j in range(12, 16):
            g[i][j] = "."
            g[j][i] = "."
    for i in range(1, n - 1):
        for j in (5, 22):
            if g[i][j] != ".":
                g[i][j] = "."
            if g[j][i] != ".":
                g[j][i] = "."
    return g


def render_town(built):
    s = 9
    n = SIZE
    ring = 3
    T = 3 * n + 2 * (ring + 1)
    town = [["."] * T for _ in range(T)]
    for i in range(T):
        town[0][i] = town[T - 1][i] = town[i][0] = town[i][T - 1] = "2"
    labels = []
    for key, (gr, gc) in Z.TOWN.items():
        g = built[key] if key in built else reserve_block()
        if key not in built:
            g = [[("." if ch == "X" else ch) for ch in row] for row in g]
        r0, c0 = ring + 1 + gr * n, ring + 1 + gc * n
        for r in range(n):
            for c in range(n):
                ch = g[r][c]
                if ch in "AB" or ch == "X":
                    ch = "."
                town[r0 + r][c0 + c] = ch
        labels.append((key, r0, c0))
    # town gate in the outer wall below the Gate district
    gr, gc = Z.TOWN["gate"]
    gx = ring + 1 + gc * n + 12
    for c in range(gx, gx + 4):
        town[T - 1][c] = "."
    pad = 30
    W, H = T * s + pad * 2, T * s + pad * 2 + 50
    img = Image.new("RGB", (W, H), (250, 244, 236))
    d = ImageDraw.Draw(img, "RGBA")
    d.text((pad, 12), "Desert Village - town overview", fill=(60, 35, 30), font=font(22, True))
    ox, oy = pad, pad + 36
    draw_grid(d, town, ox, oy, s, detail=False)
    f = font(15, True)
    for key, r0, c0 in labels:
        x0, y0 = ox + c0 * s, oy + r0 * s
        d.rectangle([x0, y0, x0 + n * s, y0 + n * s], outline=(60, 35, 30, 160), width=2)
        name = Z.ZONES[key]["name"] if key in Z.ZONES else Z.RESERVE[key]
        tag = "" if key in Z.ZONES else "  (reserve)"
        if key == "cistern":
            tag = "  (underground)"
        tw = d.textlength(name + tag, font=f)
        d.rectangle([x0 + 6, y0 + 6, x0 + 14 + tw, y0 + 28], fill=(255, 250, 242, 225))
        d.text((x0 + 10, y0 + 8), name + tag, fill=(60, 35, 30), font=f)
    d.text((pad, H - 22), f"{T}x{T} cells = {T * CELL} studs across, incl. ring road and town wall. "
           "Each round uses one zone; the others are closed.", fill=(120, 100, 90), font=font(13))
    return img


# ---------------------------------------------------------------- main
def main(only=None):
    os.makedirs(OUT, exist_ok=True)
    keys = [only] if only else list(Z.ZONES)
    built, metrics = {}, []
    for key in keys:
        g, m, lanes, _, _ = analyse(key)
        built[key] = g
        metrics.append(m)
        render_zone(g, m, lanes).save(os.path.join(OUT, f"zone-{key}.png"))
        flag = "OK " if all(m["checks"].values()) else "FIX"
        bad = [k for k, v in m["checks"].items() if not v]
        print(f"{flag} {key:10s} meet {m['meet_s']:5.2f}s  first sight {m['first_sight_s']}s  "
              f"longest {m['longest_sightline_studs']} studs  lanes {[l['time_s'] for l in m['lanes']]}  {bad or ''}")
    if only:
        return
    render_town(built).save(os.path.join(OUT, "town-overview.png"))
    plan = {
        "cell_studs": CELL, "story_studs": STORY, "zone_cells": SIZE,
        "legend": Z.LEGEND, "town": Z.TOWN, "reserve": Z.RESERVE,
        "zones": {k: {"name": Z.ZONES[k]["name"], "spawns": Z.ZONES[k]["spawns"],
                      "level": Z.ZONES[k].get("level", "surface"),
                      "grid": ["".join(r) for r in built[k]]} for k in built},
    }
    with open(os.path.join(OUT, "plan.json"), "w") as fh:
        json.dump(plan, fh, indent=1)
    with open(os.path.join(OUT, "metrics.json"), "w") as fh:
        json.dump(metrics, fh, indent=1, default=str)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)

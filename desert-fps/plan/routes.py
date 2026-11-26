"""Exports the routes the planner timed, so bots can walk the same routes in the graybox.

    python routes.py

Writes out/routes.json. Per zone, each route is a list of [layer, row, col] nodes
(layer 0 = ground, 1+ = roof height in stories) with the planner's time for it:
  - the lanes from spawn A to spawn B
  - each team's run to the meet point
  - one climb per ladder or stairs cell, from the nearer spawn
"""
import json
import os

import planner as P

# Same order the graybox builder uses to pick which wall a ladder stands against.
SIDES = ((-1, 0), (1, 0), (0, -1), (0, 1))


def routes_for(key):
    g, m, lanes, tA, tB = P.analyse(key)
    n = len(g)
    dist = {"A": tA, "B": tB}
    prev = {}
    for team in "AB":
        spawns = [(0, r, c) for r in range(n) for c in range(n) if g[r][c] == team]
        prev[team] = P.dijkstra(g, spawns)[1]

    out = []

    def add(name, team, node):
        out.append({"name": name, "from": team, "plan_s": round(dist[team][node], 2),
                    "path": [list(p) for p in P.path_to(prev[team], node)]})

    for i, lane in enumerate(lanes):
        out.append({"name": f"lane {i + 1}, A to B", "from": "A", "plan_s": round(lane["time"], 2),
                    "path": [list(p) for p in lane["path"]]})

    r, c, layer = m["meet_cell"]
    for team in "AB":
        add(f"{team} to meet point", team, (layer, r, c))

    for r in range(n):
        for c in range(n):
            ch = g[r][c]
            if ch not in "Ls":
                continue
            seen = set()
            for dr, dc in SIDES:
                rr, cc = r + dr, c + dc
                if not (0 <= rr < n and 0 <= cc < n):
                    continue
                h = P.height(g[rr][cc])
                if h == 0 or h in seen or (ch == "s" and h != 1):
                    continue
                seen.add(h)
                top = (h, rr, cc)
                team = "A" if tA.get(top, 1e18) <= tB.get(top, 1e18) else "B"
                kind = "ladder" if ch == "L" else "stairs"
                add(f"{team} up the {kind} at row {r}, col {c} ({h}-story roof)", team, top)
    return out


def main():
    routes = {"zones": {key: routes_for(key) for key in P.Z.ZONES}}
    with open(os.path.join(P.OUT, "routes.json"), "w") as fh:
        json.dump(routes, fh, indent=1)
    for key, items in routes["zones"].items():
        print(f"{key:10s} {len(items)} routes")


if __name__ == "__main__":
    main()

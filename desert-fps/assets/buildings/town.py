"""Writes the whole town from the plan: every recipe that is generated, and the list of what stands where.

    python -m buildings.town          (from assets/)

    out/buildings/house_<row>_<column>.json   one per house (buildings/houses.py)
    out/buildings/potters.json, guardhouse.json, streets.json, townwall.json
    out/town.json                     which recipe stands at which plan cell, and where no sand is banked
    out/town-houses.md                the houses in a table, for the docs

The four large buildings keep their own recipes (teahouse.py, courtyard.py, dyeworks.py, cistern.py); this only
lists them. build/pack.py packs out/town.json as Town/TownData; Town/TownBuilder stands everything."""
import json
import os

from buildings import guardhouse, houses, potters, streets, walls
from buildings.layout import CELL, HERE, route_cells, town_plan

OUT = os.path.join(HERE, "..", "out")
# The plan's name for each large building, and its recipe.
DESIGNED = {"Tea House": "teahouse", "Courtyard House": "courtyard", "Dye Works": "dyeworks", "Cistern Hall": "cistern"}


def triangles(items):
    total = 0
    for item in items:
        with open(os.path.join(OUT, item["piece"], "report.json")) as fh:
            total += json.load(fh)["triangles"]
    return total


def write(name, title, size, items):
    with open(os.path.join(OUT, "buildings", name + ".json"), "w") as fh:
        json.dump({"name": name, "title": title, "size": size, "placements": items}, fh, indent=1)


def main():
    plan = town_plan()
    grid = plan["grid"]
    n = len(grid)
    entries, clear, table, total = [], [], [], {"pieces": 0, "triangles": 0}

    def add(recipe, row, column, rows, columns, paves=False, pieces=0, tris=0):
        entries.append({"recipe": recipe, "row": row, "column": column, "rows": rows, "columns": columns, "paves": paves})
        total["pieces"] += pieces
        total["triangles"] += tris

    # the large buildings, as they are
    rects = []
    for building in plan["buildings"]:
        recipe = DESIGNED.get(building["name"])
        if recipe:
            r0, c0, r1, c1 = building["rect"]
            rects.append((r0, c0, r1, c1))
            with open(os.path.join(OUT, "buildings", recipe + ".json")) as fh:
                items = json.load(fh)["placements"]
            add(recipe, r0, c0, r1 - r0 + 1, c1 - c0 + 1, True, len(items), triangles(items))

    # the two small buildings you can walk into
    for module, recipe in ((potters, "potters"), (guardhouse, "guardhouse")):
        r0, c0, r1, c1 = module.RECT
        rects.append(module.RECT)
        items = module.placements()
        write(recipe, module.TITLE, [(c1 - c0 + 1) * CELL, (r1 - r0 + 1) * CELL], items)
        add(recipe, r0, c0, r1 - r0 + 1, c1 - c0 + 1, True, len(items), triangles(items))
        print(f"{recipe:22s} {len(items):4d} pieces {triangles(items):7d} triangles")

    # the houses
    for old in os.listdir(os.path.join(OUT, "buildings")):
        if old.startswith("house_"):
            os.remove(os.path.join(OUT, "buildings", old))
    taken = set()                                # street cells that have goods standing in them already
    for name, row, column, rows, columns, data, no_sand, spec, cells in houses.build_all(grid, taken, route_cells()):
        items = data["placements"]
        write(name, data["title"], data["size"], items)
        tris = triangles(items)
        add(name, row, column, rows, columns, False, len(items), tris)
        clear += [f"{r}:{c}:{dr}:{dc}" for r, c, dr, dc in no_sand]
        stories = sorted({int(grid[row + r][column + c]) for r in range(rows) for c in range(columns)
                          if grid[row + r][column + c] in "123"})
        table.append(f"| {spec['title']} | {spec['what']} | {cells} | {'/'.join(map(str, stories))} | {spec['tint']} | "
                     f"{spec['roof']}{' + ' + spec['terrace'] if spec['terrace'] else ''} | {len(items)} | {tris} |")

    # the streets and the wall: one recipe each, laid from the town's north-west corner
    inside = lambda r, c: any(r0 <= r <= r1 and c0 <= c <= c1 for r0, c0, r1, c1 in rects)
    for recipe, title, items in (("streets", streets.TITLE, streets.placements(grid, inside)),
                                 ("townwall", walls.TITLE, walls.placements(n))):
        write(recipe, title, [n * CELL, n * CELL], items)
        add(recipe, 0, 0, n, n, False, len(items), triangles(items))
        print(f"{recipe:22s} {len(items):4d} pieces {triangles(items):7d} triangles")

    with open(os.path.join(OUT, "town.json"), "w") as fh:
        json.dump({"buildings": entries, "clear": sorted(set(clear))}, fh, indent=1)
    with open(os.path.join(OUT, "town-houses.md"), "w") as fh:
        fh.write("| House | What it is | Cells | Stories | Plaster | Roof | Pieces | Triangles |\n|---|---|---|---|---|---|---|---|\n")
        fh.write("\n".join(table) + "\n")
    house_tris = sum(int(line.split("|")[-2]) for line in table)
    print(f"{len(table)} houses, {house_tris} triangles; {len(taken)} street cells with goods; {len(clear)} wall feet kept clear of sand")
    print(f"the town: {len(entries)} recipes, {total['pieces']} pieces, {total['triangles']} triangles")


if __name__ == "__main__":
    main()

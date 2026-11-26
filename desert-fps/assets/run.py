"""Run recipes: build -> unwrap -> bake guides -> paint -> check -> export (+ low-detail mesh).

    python3 run.py                 # every piece
    python3 run.py crate barrel    # some pieces
"""
import json
import os
import sys
import time
import zlib

from PIL import Image

import config as C
from build import Piece
from paint import Painter
from recipes import RECIPES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def make(name):
    t0 = time.time()
    fn, options = RECIPES[name]
    folder = os.path.join(OUT, name)
    os.makedirs(folder, exist_ok=True)

    piece = Piece(name)
    fn(piece, **options)
    layout = piece.finalize()
    tris, problems = piece.check()
    painter = Painter(piece, piece.bake(), C.SEED + zlib.crc32(name.encode()) % 1000)
    texture = os.path.join(folder, name + ".png")
    Image.fromarray(painter.run()).save(texture)
    piece.export(folder, texture)

    low = Piece(name, lod=True)
    fn(low, **options)
    low.finalize(layout)
    low_tris, low_problems = low.check()
    low.export(folder, texture, "_low")

    report = {"piece": name, "triangles": tris, "triangles_low": low_tris, "strokes": painter.strokes,
              "px_per_stud": round(piece.density, 1), "islands": len(piece.islands),
              "problems": problems + [f"low-detail: {q}" for q in low_problems], "seconds": round(time.time() - t0, 1)}
    with open(os.path.join(folder, "report.json"), "w") as fh:
        json.dump(report, fh, indent=1)
    return report


if __name__ == "__main__":
    names = sys.argv[1:] or list(RECIPES)
    failed = False
    for name in names:
        r = make(name)
        failed |= bool(r["problems"])
        print(f"{'FIX' if r['problems'] else 'OK '} {name:12s} {r['triangles']:5d} tris ({r['triangles_low']} low)  "
              f"{r['strokes']:5d} strokes  {r['px_per_stud']} px/stud  {r['seconds']}s  {'; '.join(r['problems'])}")
    sys.exit(1 if failed else 0)

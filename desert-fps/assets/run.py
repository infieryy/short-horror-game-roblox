"""Run recipes: build -> cut into chunks -> unwrap -> bake guides -> paint -> check -> export.

    python3 run.py                 # every piece
    python3 run.py crate barrel    # some pieces

Per piece, out/<piece>/ gets: the whole mesh, a low-detail mesh, the breakable chunks
(chunks/, jagged shards), one texture shared by all of them, <piece>.break.json and report.json.
"""
import json
import os
import sys
import time
import zlib

from PIL import Image

import chunks as chunker
import config as C
from build import Piece
from paint import Painter
from recipes import RECIPES

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def make(name):
    t0 = time.time()
    fn, options = RECIPES[name]
    spec = C.BREAK["pieces"][name]
    folder = os.path.join(OUT, name)
    sub = "parts" if spec["mode"] == "parts" else "chunks"
    chunk_folder = os.path.join(folder, sub)
    os.makedirs(chunk_folder, exist_ok=True)
    for old in os.listdir(chunk_folder):
        os.remove(os.path.join(chunk_folder, old))

    piece = Piece(name)
    fn(piece, **options)
    pieces, union, points = chunker.split(piece, spec)
    layout = union.finalize()                      # the texture is laid out and painted on the cut-up piece
    painter = Painter(union, union.bake(), C.SEED + zlib.crc32(name.encode()) % 1000)
    texture = os.path.join(folder, name + ".png")
    Image.fromarray(painter.run()).save(texture)

    piece.finalize(layout)
    tris, problems = piece.check()
    piece.export(folder, texture)

    low = Piece(name, lod=True)
    fn(low, **options)
    if spec["mode"] == "shatter":                  # shards are short-lived debris: cut them from the low-detail mesh
        pieces, _, _ = chunker.split(low, spec, points)
    low.finalize(layout)
    low_tris, low_problems = low.check()
    problems += [f"low-detail: {q}" for q in low_problems]
    low.export(folder, texture, "_low")

    files = []
    for key, chunk, _ in pieces:
        chunk.finalize(layout)
        chunk_tris, chunk_problems = chunk.check()
        problems += [f"chunk {key}: {q}" for q in chunk_problems]
        chunk.export(chunk_folder, texture)
        files.append((chunk_tris, f"{sub}/{chunk.name}.fbx"))
    manifest = chunker.manifest(piece, spec, pieces, files)
    with open(os.path.join(folder, f"{name}.{'parts' if sub == 'parts' else 'break'}.json"), "w") as fh:
        json.dump(manifest, fh, indent=1)

    report = {"piece": name, "triangles": tris, "triangles_low": low_tris, "strokes": painter.strokes,
              "px_per_stud": round(union.density, 1), "break_mode": spec["mode"], "chunks": len(pieces),
              "chunk_triangles": sum(t for t, _ in files), "problems": problems, "seconds": round(time.time() - t0, 1)}
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
              f"{r['chunks']} {r['break_mode']} ({r['chunk_triangles']} tris)  {r['strokes']:5d} strokes  "
              f"{r['px_per_stud']} px/stud  {r['seconds']}s  {'; '.join(r['problems'])}")
    sys.exit(1 if failed else 0)

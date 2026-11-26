"""Pre-cut a piece into jagged, breakable shards.

Real-time cutting is too heavy for Roblox, so every break line is cut ahead of time.
The piece is cracked like something hit it: random points are scattered through it and
each shard is the region closest to one point, so shards come out angular, uneven in
size, and with slanted break faces.
 - parts marked `cut` are sliced along the cracks and every cut face is filled in;
 - other parts (beam ends, studs, jamb blocks) stay whole and ride the shard they sit in;
 - parts tagged with a `chunk` name break on their own (a window lattice, a lintel).
Cut faces get an inside material (mud brick, raw wood) and are painted like everything else.
All shards share the piece's one texture.
"""
import zlib

import bpy  # must load before bmesh and mathutils
import bmesh
import numpy as np
from mathutils import Matrix, Vector

import config as C
from build import Piece

AXIS = {"x": 0, "y": 1, "z": 2}
EPS = 1e-3


def _layers(bm):
    return bm.faces.layers.int["part"], bm.faces.layers.int["kind"], bm.loops.layers.uv["canvas"]


def _copy(src, faces, dst, chunk_index=0):
    (sp, sk, sc), (dp, dk, dc) = _layers(src), _layers(dst)
    dchunk = dst.faces.layers.int["chunk"]
    vmap = {}
    for f in faces:
        verts = []
        for v in f.verts:
            if v not in vmap:
                vmap[v] = dst.verts.new(v.co)
            verts.append(vmap[v])
        nf = dst.faces.new(verts)
        nf[dp], nf[dk], nf[dchunk] = f[sp], f[sk], chunk_index
        for a, b in zip(f.loops, nf.loops):
            b[dc].uv = a[sc].uv


def _empty():
    bm = bmesh.new()
    bm.faces.layers.int.new("part")
    bm.faces.layers.int.new("kind")
    bm.faces.layers.int.new("chunk")
    bm.loops.layers.uv.new("canvas")
    return bm


def _bounds(faces):
    cos = [v.co for f in faces for v in f.verts]
    return Vector([min(c[k] for c in cos) for k in range(3)]), Vector([max(c[k] for c in cos) for k in range(3)])


def crack_points(name, lo, hi, spec):
    """Scatter the points the shards grow from. Kept apart so no shard is a sliver; for walls and
    doors (`through`) they sit near the middle of the thickness, and `slant` pushes them off it so
    the break faces lean instead of cutting straight through."""
    rng = np.random.default_rng(zlib.crc32(name.encode()) + spec.get("seed", 0))
    size, count = hi - lo, spec["shards"]
    through = AXIS.get(spec.get("through"))
    spans = [size[k] for k in range(3) if k != through]
    apart = spec.get("apart", 0.7) * (float(np.prod(spans)) / count) ** (1.0 / len(spans))
    points = []
    while len(points) < count:
        for _ in range(200):
            p = Vector([lo[k] + rng.random() * size[k] for k in range(3)])
            if through is not None:
                p[through] = (lo[through] + hi[through]) / 2 + rng.uniform(-1, 1) * spec.get("slant", 0.0)
            flat = lambda v: Vector([v[k] for k in range(3) if k != through])
            if all((flat(p) - flat(q)).length >= apart for q in points):
                points.append(p)
                break
        else:
            apart *= 0.9
    return points


def _slice(shell, planes, core_pid, touched):
    """Keep the part of a closed shell inside one shard's region; fill every cut face.
    planes: (neighbour index, point on plane, normal pointing out of the region)."""
    tb = shell.copy()
    lp, lk, _ = _layers(tb)
    for other, co, no in planes:
        if not tb.faces:
            break
        dist = [(v.co - co).dot(no) for v in tb.verts]
        if max(dist) <= EPS:
            continue
        if min(dist) >= -EPS:
            tb.clear()
            break
        bmesh.ops.bisect_plane(tb, geom=tb.verts[:] + tb.edges[:] + tb.faces[:], dist=1e-5, plane_co=co,
                               plane_no=no, clear_outer=True)
        tb.normal_update()
        on_plane = lambda geom: all(abs((v.co - co).dot(no)) < 1e-4 for v in geom.verts)
        # a face already lying in the cut plane and facing into this region belongs to the neighbour
        inward = [f for f in tb.faces if on_plane(f) and f.normal.dot(no) < 0]
        if inward:
            bmesh.ops.delete(tb, geom=inward, context="FACES")
        edges = [e for e in tb.edges if on_plane(e) and len(e.link_faces) == 1]
        if edges:
            fill = bmesh.ops.triangle_fill(tb, use_beauty=True, use_dissolve=True, edges=edges)
            for g in fill["geom"]:
                if isinstance(g, bmesh.types.BMFace):
                    g[lp], g[lk] = core_pid, 0
    # neighbours = the regions whose cut face is still there after all the later cuts
    for other, co, no in planes:
        if any(f[lp] == core_pid and all(abs((v.co - co).dot(no)) < 1e-4 for v in f.verts) for f in tb.faces):
            touched.add(other)
    return tb


def split(piece, spec, points=None):
    """Returns (shards, union, points). shards: list of (id, Piece, info). union holds every shard's
    faces in one Piece, which is what gets unwrapped and painted."""
    src = piece.bm
    sp, _, _ = _layers(src)
    shells = {}
    for f in src.faces:
        shells.setdefault(f[sp], []).append(f)
    if points is None:
        lo, hi = _bounds([f for pid, faces in shells.items() if piece.parts[pid].get("cut") for f in faces])
        points = crack_points(piece.name, lo, hi, spec)
    regions = [[(j, (p + q) / 2, (q - p).normalized()) for j, q in enumerate(points) if j != i]
               for i, p in enumerate(points)]
    name_of = lambda i: f"s{i:02d}"

    cores = {}

    def core(pid):
        mat = C.CORE[piece.parts[pid]["mat"]]
        if mat not in cores:
            piece.parts.append({"mat": mat, "group": f"core:{mat}", "grain": None, "frame": Matrix.Identity(4),
                                "band": False, "core": True})
            cores[mat] = len(piece.parts) - 1
        return cores[mat]

    bins = {}          # shard id -> {"bm", "volume": {material: studs3}, "touched": neighbour shard indexes}

    def add(key, tb, mat, touched=()):
        volume = abs(tb.calc_volume())
        if not tb.faces or volume < 1e-5:
            return
        entry = bins.setdefault(key, {"bm": _empty(), "volume": {}, "touched": set()})
        _copy(tb, tb.faces, entry["bm"])
        entry["volume"][mat] = entry["volume"].get(mat, 0.0) + volume
        entry["touched"] |= set(touched)

    for pid, faces in shells.items():
        part = piece.parts[pid]
        shell = _empty()
        _copy(src, faces, shell)
        lo, hi = _bounds(faces)
        mid = (lo + hi) / 2
        if part.get("chunk"):
            add(part["chunk"], shell, part["mat"])
        elif not part.get("cut"):
            nearest = min(range(len(points)), key=lambda i: (points[i] - mid).length)
            add(name_of(nearest), shell, part["mat"])
        else:
            for i, planes in enumerate(regions):
                touched = set()
                tb = _slice(shell, planes, core(pid), touched)
                add(name_of(i), tb, part["mat"], touched)
                tb.free()
        shell.free()

    union = Piece(piece.name, lod=piece.lod)
    union.parts, union.seams = piece.parts, piece.seams
    shards = []
    for number, key in enumerate(sorted(bins)):
        entry = bins[key]
        bmesh.ops.recalc_face_normals(entry["bm"], faces=entry["bm"].faces[:])
        shard = Piece(f"{piece.name}_{key}", lod=piece.lod)
        shard.parts, shard.seams = piece.parts, piece.seams
        _copy(entry["bm"], entry["bm"].faces, shard.bm)
        _copy(entry["bm"], entry["bm"].faces, union.bm, chunk_index=number)
        lo, hi = _bounds(entry["bm"].faces)
        shards.append((key, shard, {"lo": lo, "hi": hi, "volume": sum(entry["volume"].values()),
                                    "material": max(entry["volume"], key=entry["volume"].get),
                                    "volumes": entry["volume"],
                                    "adjacent": {name_of(j) for j in entry["touched"]} & set(bins)}))
        entry["bm"].free()
    return shards, union, points


def manifest(piece, spec, shards, files):
    """Everything the game needs to break this piece: one box with health per shard,
    which shards touch, and which ones stand on the ground."""
    def roblox(v):                                   # Blender (x, y, z up) -> Roblox (x, y up, z)
        return [round(v.x, 3), round(v.z, 3), round(-v.y, 3)]

    rules, out = C.BREAK, []
    for (key, shard, info), (tris, file) in zip(shards, files):
        lo, hi = info["lo"], info["hi"]
        extent = hi - lo
        hp = sum(rules["hp_per_stud3"][m] * v for m, v in info["volumes"].items())
        touches = [name for name, (axis, value) in zip(("left", "right", "bottom", "top"), piece.seams)
                   if abs((lo if name in ("left", "bottom") else hi)[axis] - value) < 0.05]
        out.append({
            "id": key, "mesh": file, "center": roblox((lo + hi) / 2),
            "size": [round(extent.x, 3), round(extent.z, 3), round(extent.y, 3)],
            "material": info["material"], "health": max(rules["hp_min"], int(round(hp / 5.0)) * 5),
            "collision": "Hull", "grounded": lo.z < 0.05, "touches": touches, "triangles": tris,
            "neighbors": set(info["adjacent"]),
        })
    # parts that break on their own (lattice, lintel) lean on whatever their box overlaps
    for a, (ka, _, ia) in zip(out, shards):
        for b, (kb, _, ib) in zip(out, shards):
            if a is b or (ka.startswith("s") and kb.startswith("s") and ka[1:].isdigit() and kb[1:].isdigit()):
                continue
            if all(min(ia["hi"][k], ib["hi"][k]) - max(ia["lo"][k], ib["lo"][k]) > -0.05 for k in range(3)):
                a["neighbors"].add(kb)
    for entry in out:
        entry["neighbors"] = sorted(entry["neighbors"])
    return {
        "piece": piece.name, "mode": spec["mode"],
        "coords": "Roblox studs, Y up, relative to the piece origin (bottom centre). center = shard bounding-box centre.",
        "health": sum(c["health"] for c in out) if spec["mode"] == "shatter" else None,
        "chunks": out,
    }

"""Geometry side of a recipe: build closed solids, unwrap them, bake paint guides, export.

A recipe calls Piece.box / Piece.lathe / Piece.wall. Every part is a closed shell.
UVs are plain projections of each part's faces ("facets"), measured in studs, so
 - paint strokes can be placed in real sizes, and
 - the low-detail mesh reuses the same texture without re-painting.
"""
import math
import os

import bpy  # must load before bmesh and mathutils
import bmesh
import numpy as np
from mathutils import Matrix, Vector
from mathutils.bvhtree import BVHTree

import config as C

# facet -> (U, V) in the part's own frame. Seen from outside, U points right and V points up.
FACETS = {
    "-y": (Vector((1, 0, 0)), Vector((0, 0, 1))), "+y": (Vector((-1, 0, 0)), Vector((0, 0, 1))),
    "+x": (Vector((0, 1, 0)), Vector((0, 0, 1))), "-x": (Vector((0, -1, 0)), Vector((0, 0, 1))),
    "+z": (Vector((1, 0, 0)), Vector((0, 1, 0))), "-z": (Vector((1, 0, 0)), Vector((0, -1, 0))),
}
GRAIN = {"x": Vector((1, 0, 0)), "y": Vector((0, 1, 0)), "z": Vector((0, 0, 1))}


def _facet(n):
    best, name = -1.0, None
    for axis, comp in (("y", n.y), ("x", n.x), ("z", n.z)):      # tie order keeps bevels with the front
        if abs(comp) > best + 1e-4:
            best, name = abs(comp), ("+" if comp > 0 else "-") + axis
    return name


def frame_axes(origin, x_dir, y_dir):
    """Local frame from an origin and its X and Y directions (Z = X cross Y)."""
    x, y = Vector(x_dir).normalized(), Vector(y_dir).normalized()
    m = Matrix((x, y, x.cross(y))).transposed().to_4x4()
    m.translation = Vector(origin)
    return m


class Piece:
    def __init__(self, name, lod=False):
        self.name, self.lod = name, lod
        self.bm = bmesh.new()
        self.l_part = self.bm.faces.layers.int.new("part")
        self.l_kind = self.bm.faces.layers.int.new("kind")       # 1 = canvas coords stored on the loops
        self.l_chunk = self.bm.faces.layers.int.new("chunk")     # which breakable chunk a face belongs to
        self.l_cuv = self.bm.loops.layers.uv.new("canvas")
        self.parts = []
        self.serial = 0          # counts every part a recipe asks for, so names match in the low-detail build
        self.islands = []
        self.layout = None
        self.seams = []          # (axis, value): planes where this piece meets its neighbours; no edge highlight there
        self.marks = []          # painted detail lines, see mark()
        self.sockets, self.joints = [], []      # attachment points and moving parts (guns)
        self.scale = C.DETAIL_SCALE.get(name.split("_")[0], C.DETAIL_SCALE.get(name, 1.0))   # 1 = building-sized

    # ------------------------------------------------------------ parts
    def _part(self, mat, group, grain, frame, band, extra=None):
        self.parts.append({"mat": mat, "group": group or f"{mat}#{self.serial}", "grain": grain,
                           "frame": frame or Matrix.Identity(4), "band": band, **(extra or {})})
        return len(self.parts) - 1

    def _merge(self, tb, pid, explicit=False):
        bmesh.ops.recalc_face_normals(tb, faces=tb.faces[:])
        if tb.calc_volume(signed=True) < 0:
            bmesh.ops.reverse_faces(tb, faces=tb.faces[:])
        frame = self.parts[pid]["frame"]
        cl = tb.loops.layers.uv.get("canvas")
        vmap = {v: self.bm.verts.new(frame @ v.co) for v in tb.verts}
        for f in tb.faces:
            nf = self.bm.faces.new([vmap[v] for v in f.verts])
            nf[self.l_part] = pid
            if explicit and cl and f.tag:
                nf[self.l_kind] = 1
                for src, dst in zip(f.loops, nf.loops):
                    dst[self.l_cuv].uv = src[cl].uv
        tb.free()

    def box(self, lo, hi, mat, bevel=0.0, group=None, grain=None, frame=None, band=False, detail=False, extra=None):
        """Axis-aligned box in the part's frame. `detail` parts are left out of the low-detail mesh."""
        self.serial += 1
        if detail and self.lod:
            return
        pid = self._part(mat, group, grain, frame, band, extra)
        lo, hi = Vector(lo), Vector(hi)
        size, mid = hi - lo, (lo + hi) / 2
        tb = bmesh.new()
        bmesh.ops.create_cube(tb, size=1.0)
        for v in tb.verts:
            v.co = Vector((v.co.x * size.x, v.co.y * size.y, v.co.z * size.z)) + mid
        if bevel > 0 and not self.lod:
            bmesh.ops.bevel(tb, geom=tb.edges[:], offset=bevel, segments=1, affect="EDGES", profile=0.5)
        self._merge(tb, pid)
        return pid

    def extrude(self, profile, half, mat, bevel=0.0, segments=1, group=None, grain=None, frame=None, band=False,
                detail=False, extra=None):
        """Side-profile shape: an (x, z) outline pushed through the thickness (-half..half on Y),
        with the edges of both faces rounded by `bevel`."""
        self.serial += 1
        if detail and self.lod:
            return
        pid = self._part(mat, group, grain, frame, band, extra)
        tb = bmesh.new()
        front = [tb.verts.new((x, -half, z)) for x, z in profile]
        back = [tb.verts.new((x, half, z)) for x, z in profile]
        caps = [tb.faces.new(front), tb.faces.new(back[::-1])]
        for i in range(len(profile)):
            j = (i + 1) % len(profile)
            tb.faces.new((front[i], back[i], back[j], front[j]))
        bmesh.ops.recalc_face_normals(tb, faces=tb.faces[:])
        if bevel > 0 and not self.lod:
            bmesh.ops.bevel(tb, geom=[e for f in caps for e in f.edges], offset=bevel, segments=segments,
                            affect="EDGES", profile=0.5, clamp_overlap=True)
        self._merge(tb, pid)
        return pid

    def lathe(self, profile, segments, mat, closed=False, r_ref=None, group=None, grain="z", frame=None,
              band=False, detail=False, extra=None, smooth=False):
        """Revolve (radius, height) points around the frame's Z axis. Open profiles get flat caps.
        `smooth` shades the sides as one round surface (a barrel) instead of flat facets (staves)."""
        self.serial += 1
        if detail and self.lod:
            return
        if self.lod:
            segments = max(6, segments // 2)
        pid = self._part(mat, group, grain, frame, band, {**(extra or {}), "smooth": smooth})
        r_ref = r_ref or max(r for r, _ in profile)
        tb = bmesh.new()
        cl = tb.loops.layers.uv.new("canvas")
        n = len(profile)
        arc = [0.0]
        for a, b in zip(profile, profile[1:] + (profile[:1] if closed else [])):
            arc.append(arc[-1] + math.hypot(b[0] - a[0], b[1] - a[1]))
        rings = [[tb.verts.new((r * math.cos(2 * math.pi * i / segments), r * math.sin(2 * math.pi * i / segments), z))
                  for i in range(segments)] for r, z in profile]
        for j in range(n if closed else n - 1):
            j1 = (j + 1) % n
            for i in range(segments):
                i1 = (i + 1) % segments
                f = tb.faces.new((rings[j][i], rings[j][i1], rings[j1][i1], rings[j1][i]))
                f.tag = True
                u0, u1 = 2 * math.pi * i / segments * r_ref, 2 * math.pi * (i + 1) / segments * r_ref
                for loop, uv in zip(f.loops, ((u0, arc[j]), (u1, arc[j]), (u1, arc[j + 1]), (u0, arc[j + 1]))):
                    loop[cl].uv = uv
        if not closed:
            tb.faces.new(rings[0][::-1])
            tb.faces.new(rings[-1])
        self._merge(tb, pid, explicit=True)
        return pid

    def wall(self, xs, zs, yf, yb, holes=(), mat="plaster", group="wall", band=True, extra=None):
        """One closed wall shell on a grid of x/z break lines. yf(z), yb(z) give the front and back
        surface; `holes` are grid cells (i, j) left open (windows, doorways)."""
        pid = self._part(mat, group, None, None, band, extra)
        tb = bmesh.new()
        F = [[tb.verts.new((x, yf(z), z)) for x in xs] for z in zs]
        B = [[tb.verts.new((x, yb(z), z)) for x in xs] for z in zs]
        nx, nz, hole = len(xs) - 1, len(zs) - 1, set(holes)

        def solid(i, j):
            return 0 <= i < nx and 0 <= j < nz and (i, j) not in hole

        for j in range(nz):
            for i in range(nx):
                if not solid(i, j):
                    continue
                tb.faces.new((F[j][i], F[j][i + 1], F[j + 1][i + 1], F[j + 1][i]))
                tb.faces.new((B[j][i + 1], B[j][i], B[j + 1][i], B[j + 1][i + 1]))
                if not solid(i - 1, j):
                    tb.faces.new((F[j][i], F[j + 1][i], B[j + 1][i], B[j][i]))
                if not solid(i + 1, j):
                    tb.faces.new((F[j][i + 1], B[j][i + 1], B[j + 1][i + 1], F[j + 1][i + 1]))
                if not solid(i, j - 1):
                    tb.faces.new((F[j][i], B[j][i], B[j][i + 1], F[j][i + 1]))
                if not solid(i, j + 1):
                    tb.faces.new((F[j + 1][i], F[j + 1][i + 1], B[j + 1][i + 1], B[j + 1][i]))
        bmesh.ops.delete(tb, geom=[v for v in tb.verts if not v.link_faces], context="VERTS")
        self._merge(tb, pid)
        return pid

    def mark(self, pid, facet, points, tone=-3, width=0.01, closed=False):
        """Paint a detail line on one face of a part (a panel line, a slot, an engraving).
        points are world positions; the line is drawn on the part's `facet` ("-y", "+z", ...)."""
        if pid is not None:
            self.marks.append({"pid": pid, "facet": facet, "points": [Vector(q) for q in points], "tone": tone,
                               "width": width, "closed": closed})

    # ------------------------------------------------------------ unwrap
    def finalize(self, layout=None):
        """Assign every face to an island (group, material, facet), pack the islands, write UVs.
        Pass the high-detail layout to make a low-detail mesh share its texture."""
        bm = self.bm
        bm.verts.ensure_lookup_table()
        bm.faces.ensure_lookup_table()
        bm.faces.index_update()
        bm.normal_update()
        found, self.face_island = {}, {}
        for f in bm.faces:
            part = self.parts[f[self.l_part]]
            if f[self.l_kind] == 1:
                facet, coords = "lathe", [tuple(l[self.l_cuv].uv) for l in f.loops]
            else:
                inv = part["frame"].inverted()
                facet = _facet(inv.to_3x3() @ f.normal)
                U, V = FACETS[facet]
                coords = [((inv @ l.vert.co).dot(U), (inv @ l.vert.co).dot(V)) for l in f.loops]
            key = (part["group"], part["mat"], facet)
            isl = found.setdefault(key, {"key": key, "part": part, "facet": facet, "faces": [], "coords": {}})
            isl["faces"].append(f)
            isl["coords"][f.index] = coords
        for isl in found.values():
            pts = [c for cs in isl["coords"].values() for c in cs]
            isl["min"] = (min(p[0] for p in pts), min(p[1] for p in pts))
            isl["size"] = (max(p[0] for p in pts) - isl["min"][0], max(p[1] for p in pts) - isl["min"][1])
        if layout is None:
            keys = list(found)
            side, pos = _shelf_pack([found[k]["size"] for k in keys])
            layout = {"side": side, "islands": {k: {"min": found[k]["min"], "pos": p} for k, p in zip(keys, pos)}}
        self.layout = layout
        self.density = C.TEX / layout["side"]
        uv = bm.loops.layers.uv.new("UVMap")
        self.l_uv = uv
        self.islands = []
        for key, isl in found.items():
            place = layout["islands"][key]
            isl["id"] = len(self.islands)
            isl["origin_px"] = (place["pos"][0] * self.density, place["pos"][1] * self.density)
            for f in isl["faces"]:
                self.face_island[f.index] = isl["id"]
                for loop, (cu, cv) in zip(f.loops, isl["coords"][f.index]):
                    loop[uv].uv = ((cu - place["min"][0] + place["pos"][0]) / layout["side"],
                                   (cv - place["min"][1] + place["pos"][1]) / layout["side"])
            frame3 = isl["part"]["frame"].to_3x3()
            isl["U"], isl["V"] = (None, None) if isl["facet"] == "lathe" else tuple(frame3 @ a for a in FACETS[isl["facet"]])
            grain = isl["part"]["grain"]
            isl["grain_world"] = frame3 @ GRAIN[grain] if grain else None
            self.islands.append(isl)
        return layout

    # ------------------------------------------------------------ checks
    def check(self):
        """The rules every piece must pass before it may go to Roblox."""
        bm, problems = self.bm, []
        open_edges = sum(1 for e in bm.edges if len(e.link_faces) != 2)
        if open_edges:
            problems.append(f"{open_edges} open edges (not a closed solid)")
        if bm.calc_volume(signed=True) <= 0:
            problems.append("inside-out faces")
        tris = sum(len(f.verts) - 2 for f in bm.faces)
        if tris > C.TRI_LIMIT:
            problems.append(f"{tris} triangles is over Roblox's {C.TRI_LIMIT} limit")
        budget = C.TRI_BUDGET.get(self.name)
        if budget and not self.lod and tris > budget:
            problems.append(f"{tris} triangles is over this piece's budget of {budget}")
        # flicker: two shells showing the same plane in the same place
        planes = {}
        for f in bm.faces:
            n = f.normal
            key = (round(n.x, 2), round(n.y, 2), round(n.z, 2), round(n.dot(f.verts[0].co) * 20 / self.scale))
            planes.setdefault(key, []).append(f)
        triangles = {}
        for tri in bm.calc_loop_triangles():
            triangles.setdefault(tri[0].face, []).append([loop.vert.co for loop in tri])
        flicker, shells, self.flickers = 0, {}, []
        for f in bm.faces:
            shells.setdefault(f[self.l_part], []).append(f)
        solids = {}

        def inside(pid, point):
            """Is the point inside this part's closed shell? (count crossings along a skew ray)"""
            if pid not in solids:
                verts = list({v for f in shells[pid] for v in f.verts})
                index = {v: k for k, v in enumerate(verts)}
                co = [v.co.copy() for v in verts]
                lo = Vector([min(c[k] for c in co) for k in range(3)])
                hi = Vector([max(c[k] for c in co) for k in range(3)])
                solids[pid] = (lo, hi, BVHTree.FromPolygons(co, [[index[v] for v in f.verts] for f in shells[pid]]))
            lo, hi, tree = solids[pid]
            if any(point[k] < lo[k] or point[k] > hi[k] for k in range(3)):
                return False
            direction, crossings, origin = Vector((0.3713, 0.6217, 0.6891)), 0, point
            while True:
                hit = tree.ray_cast(origin, direction, 1000.0)
                if hit[0] is None:
                    return crossings % 2 == 1
                crossings += 1
                origin = hit[0] + direction * 1e-4

        def visible(point, n, own):
            return not any(inside(pid, point + n * 0.01 * self.scale) for pid in shells if pid not in own) \
                and not any(inside(pid, point + n * 0.002 * self.scale) for pid in own)

        for key, faces in planes.items():
            if len({f[self.l_part] for f in faces}) < 2:
                continue
            n = Vector(key[:3])
            a = n.orthogonal().normalized()
            b = n.cross(a)
            polys = [(f[self.l_part], [(co.dot(a), co.dot(b)) for co in tri], n.dot(tri[0]))
                     for f in faces for tri in triangles[f]]
            for i in range(len(polys)):
                for j in range(i + 1, len(polys)):
                    if polys[i][0] == polys[j][0]:
                        continue
                    shared = _overlap(polys[i][1], polys[j][1], 2e-3 * self.scale ** 2)
                    if not shared:
                        continue
                    own = (polys[i][0], polys[j][0])
                    spots = [a * shared[0] + b * shared[1] + n * polys[k][2] for k in (i, j)]
                    if all(visible(spot, n, own) for spot in spots):      # if one is buried, nothing fights
                        flicker += 1
                        self.flickers.append((self.parts[own[0]]["group"], self.parts[own[1]]["group"],
                                              tuple(round(c, 2) for c in spots[0])))
        if flicker:
            problems.append(f"{flicker} overlapping coplanar faces (would flicker)")
        if self.density < 24:
            problems.append(f"texture density only {self.density:.0f} px per stud")
        return tris, problems

    # ------------------------------------------------------------ paint guides
    def bake(self):
        """Rasterise the mesh into texture space: which island, where in the world, how occluded,
        and where the protruding edges run."""
        T, bm, uv = C.TEX, self.bm, self.l_uv
        island = np.full((T, T), -1, np.int32)
        pos = np.zeros((T, T, 3), np.float32)
        nrm = np.zeros((T, T, 3), np.float32)
        chunk = np.zeros((T, T), np.int32)
        for tri in bm.calc_loop_triangles():
            f = tri[0].face
            p = np.array([tri[k][uv].uv for k in range(3)], np.float64) * T
            w = np.array([tri[k].vert.co for k in range(3)], np.float64)
            x0, x1 = max(int(p[:, 0].min() - 1), 0), min(int(p[:, 0].max() + 2), T)
            y0, y1 = max(int(p[:, 1].min() - 1), 0), min(int(p[:, 1].max() + 2), T)
            if x0 >= x1 or y0 >= y1:
                continue
            X, Y = np.meshgrid(np.arange(x0, x1) + 0.5, np.arange(y0, y1) + 0.5)
            area = (p[1, 0] - p[0, 0]) * (p[2, 1] - p[0, 1]) - (p[2, 0] - p[0, 0]) * (p[1, 1] - p[0, 1])
            if abs(area) < 1e-9:
                continue
            bary, inside = [], np.ones(X.shape, bool)
            for k in range(3):
                a, b = p[(k + 1) % 3], p[(k + 2) % 3]
                e = ((b[0] - a[0]) * (Y - a[1]) - (b[1] - a[1]) * (X - a[0])) / area
                bary.append(e)
                inside &= e * abs(area) / max(math.hypot(b[0] - a[0], b[1] - a[1]), 1e-9) >= -0.75
            sel = (slice(y0, y1), slice(x0, x1))
            island[sel][inside] = self.face_island[f.index]
            pos[sel][inside] = (bary[0][..., None] * w[0] + bary[1][..., None] * w[1] + bary[2][..., None] * w[2])[inside]
            nrm[sel][inside] = np.array(f.normal)
            chunk[sel][inside] = f[self.l_chunk]
        shade = self._contact_shade(island, pos, nrm, chunk)
        for isl in self.islands:
            if isl["part"].get("core"):          # cut faces are open air once exposed
                shade[island == isl["id"]] = 0.0
        return {"island": island, "pos": pos, "ao": shade, "edges": self._edges()}

    def _contact_shade(self, island, pos, nrm, chunk):
        """Shade where surfaces meet. Only parts of the same chunk shade each other: a neighbouring
        chunk can be destroyed, and must not leave its shadow painted on the wall."""
        T, step = C.TEX, C.AO_STEP
        groups, trees = {}, {}
        for f in self.bm.faces:
            groups.setdefault(f[self.l_chunk], []).append(f)
        for cid, faces in groups.items():
            verts = list({v for f in faces for v in f.verts})
            index = {v: k for k, v in enumerate(verts)}
            trees[cid] = BVHTree.FromPolygons([v.co.copy() for v in verts], [[index[v] for v in f.verts] for f in faces])
        rng = np.random.default_rng(1)
        # cosine-weighted hemisphere directions in tangent space
        u, v = (np.arange(C.AO_RAYS) + 0.5) / C.AO_RAYS, rng.permutation(C.AO_RAYS) / C.AO_RAYS
        r, phi = np.sqrt(u), 2 * np.pi * v
        hemi = np.stack([r * np.cos(phi), r * np.sin(phi), np.sqrt(1 - u)], 1)
        ys, xs = np.nonzero(island[::step, ::step] >= 0)
        P, N = pos[::step, ::step][ys, xs].astype(np.float64), nrm[::step, ::step][ys, xs].astype(np.float64)
        helper = np.where(np.abs(N[:, 2:3]) < 0.9, [[0, 0, 1.0]], [[1.0, 0, 0]])
        Tn = np.cross(helper, N)
        Tn /= np.linalg.norm(Tn, axis=1, keepdims=True)
        Bn = np.cross(N, Tn)
        dirs = hemi[None, :, 0:1] * Tn[:, None] + hemi[None, :, 1:2] * Bn[:, None] + hemi[None, :, 2:3] * N[:, None]
        origins = (P + N * 0.012 * self.scale).tolist()
        dirs = dirs.tolist()
        owner = chunk[::step, ::step][ys, xs].tolist()
        occ = np.zeros(len(origins), np.float32)
        D = C.AO_DIST * self.scale
        for i, o in enumerate(origins):
            total, cast = 0.0, trees[owner[i]].ray_cast
            for d in dirs[i]:
                hit = cast(o, d, D)
                if hit[0] is not None:
                    total += 1.0 - hit[3] / D
            occ[i] = total / C.AO_RAYS
        small = np.zeros((T // step, T // step), np.float32)
        weight = np.zeros_like(small)
        small[ys, xs], weight[ys, xs] = occ, 1.0
        full = lambda a: _blur(np.repeat(np.repeat(_blur(a, 1), step, 0), step, 1), 1)
        return np.clip(full(small) / np.maximum(full(weight), 1e-4), 0, 1)

    def _edges(self):
        """Protruding (convex) edges, as pixel segments per island."""
        T, uv, out = C.TEX, self.l_uv, {}
        for e in self.bm.edges:
            angle = e.calc_face_angle_signed(0.0) if len(e.link_faces) == 2 else 0.0
            if angle < math.radians(28):
                continue
            if any(all(abs(v.co[axis] - value) < 1e-4 for v in e.verts) for axis, value in self.seams):
                continue
            if any(self.parts[f[self.l_part]].get("core") for f in e.link_faces):
                continue                         # a break line is not an edge until the piece breaks
            if angle < math.radians(50) and all(f[self.l_kind] == 1 and self.parts[f[self.l_part]].get("smooth")
                                                for f in e.link_faces):
                continue                         # facets of a round surface are not edges
            for f in e.link_faces:
                loops = {l.vert: l for l in f.loops}
                a, b = loops[e.verts[0]][uv].uv, loops[e.verts[1]][uv].uv
                mid = sum((l[uv].uv for l in f.loops), Vector((0.0, 0.0))) / len(f.loops)   # which side is the face
                out.setdefault(self.face_island[f.index], []).append((a.x * T, a.y * T, b.x * T, b.y * T,
                                                                     mid.x * T, mid.y * T, angle))
        return out

    # ------------------------------------------------------------ export
    def to_object(self, texture_path=None):
        bm = self.bm.copy()
        part, kind = bm.faces.layers.int["part"], bm.faces.layers.int["kind"]
        for f in bm.faces:
            f.smooth = f[kind] == 1 and bool(self.parts[f[part]].get("smooth"))
        for e in bm.edges:                       # a round surface stays round, but its rims stay crisp
            if len(e.link_faces) == 2 and abs(e.calc_face_angle_signed(0.0)) > math.radians(50):
                e.smooth = False
        bm.loops.layers.uv.remove(bm.loops.layers.uv["canvas"])
        bmesh.ops.triangulate(bm, faces=bm.faces[:])
        mesh = bpy.data.meshes.new(self.name)
        bm.to_mesh(mesh)
        bm.free()
        obj = bpy.data.objects.new(self.name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        if texture_path:
            mesh.materials.append(matte_material(self.name, texture_path))
        return obj

    def export(self, out_dir, texture_path, suffix=""):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        obj = self.to_object(texture_path)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        base = os.path.join(out_dir, self.name + suffix)
        bpy.ops.wm.obj_export(filepath=base + ".obj", export_selected_objects=True, export_materials=False,
                              forward_axis="NEGATIVE_Z", up_axis="Y")
        bpy.ops.export_scene.fbx(filepath=base + ".fbx", use_selection=True, global_scale=0.01,
                                 axis_forward="-Z", axis_up="Y", path_mode="STRIP", mesh_smooth_type="FACE")
        return base


def matte_material(name, texture_path):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    bsdf = nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 1.0
    for spec in ("Specular IOR Level", "Specular"):
        if spec in bsdf.inputs:
            bsdf.inputs[spec].default_value = 0.0
    tex = nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(texture_path, check_existing=True)
    links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat


def _overlap(p, q, min_area=2e-3):
    """Centre of the area two convex polygons share, or None if they only touch."""
    def area(poly):
        return sum(poly[k][0] * poly[(k + 1) % len(poly)][1] - poly[(k + 1) % len(poly)][0] * poly[k][1]
                   for k in range(len(poly))) / 2

    if abs(area(p)) < 1e-12 or abs(area(q)) < 1e-12:
        return None
    if area(q) < 0:
        q = q[::-1]
    out = p
    for k in range(len(q)):
        (ax, ay), (bx, by) = q[k], q[(k + 1) % len(q)]
        side = lambda pt: (bx - ax) * (pt[1] - ay) - (by - ay) * (pt[0] - ax)
        clipped = []
        for m in range(len(out)):
            c, d = out[m], out[(m + 1) % len(out)]
            sc, sd = side(c), side(d)
            if sc >= 0:
                clipped.append(c)
            if (sc > 0 > sd) or (sc < 0 < sd):
                t = sc / (sc - sd)
                clipped.append((c[0] + (d[0] - c[0]) * t, c[1] + (d[1] - c[1]) * t))
        out = clipped
        if len(out) < 3:
            return None
    if abs(area(out)) < min_area:
        return None
    return sum(pt[0] for pt in out) / len(out), sum(pt[1] for pt in out) / len(out)


def _blur(a, passes):
    for _ in range(passes):
        a = (np.roll(a, 1, 0) + 2 * a + np.roll(a, -1, 0)) / 4
        a = (np.roll(a, 1, 1) + 2 * a + np.roll(a, -1, 1)) / 4
    return a


def _shelf_pack(sizes):
    """Pack rectangles (studs) into the smallest square. Returns (side, positions)."""
    order = sorted(range(len(sizes)), key=lambda i: -sizes[i][1])

    def attempt(side):
        margin = 2.0 * C.PAD * side / C.TEX
        x = y = margin
        row, pos = 0.0, {}
        for i in order:
            w, h = sizes[i]
            if w + 2 * margin > side:
                return None
            if x + w + margin > side:
                x, y, row = margin, y + row + margin, 0.0
            pos[i] = (x, y)
            x, row = x + w + margin, max(row, h)
        return pos if y + row + margin <= side else None

    lo = max(max(w, h) for w, h in sizes)
    hi = lo * 16
    for _ in range(40):
        mid = (lo + hi) / 2
        if attempt(mid):
            hi = mid
        else:
            lo = mid
    pos = attempt(hi)
    return hi, [pos[i] for i in range(len(sizes))]

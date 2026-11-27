"""Paint side of a recipe. Follows the look rules:

1. one colour family per material          5. every part gets its own mix
2. every surface starts as one flat colour  6. turquoise only as a band at the bottom
3. strokes all lean the same way            7. no painted shadows; lavender where light can't reach
4. each stroke is ONE step lighter/darker   8. two glazes: pale on edges, dark in corners
"""
import colorsys
import math

import numpy as np
from PIL import Image, ImageDraw

import brush
import config as C
from build import FACETS
from mathutils import Vector


def rgb(hls):
    h, l, s = hls
    return np.array(colorsys.hls_to_rgb((h % 360) / 360.0, l, s), np.float32)


def step(color, n, fam, gain=1.0):
    """Move a colour n small steps lighter (+) or darker (-), staying inside its family."""
    n = n * gain
    h, l, s = colorsys.rgb_to_hls(*[float(c) for c in np.clip(color, 0, 1)])
    h *= 360.0
    lo, hi = fam["h"]
    if not (lo - 20 <= h <= hi + 20):                # paint under the stroke belongs to another family
        return color + (1.0 - color) * 0.06 * n if n > 0 else color * (1.0 + 0.06 * n)
    return rgb((min(max(h + n * fam["hue_step"], lo), hi),
                min(max(l + n * fam["step"], fam["l"][0]), fam["l"][1]),
                min(max(s, fam["s"][0]), fam["s"][1])))


class Painter:
    def __init__(self, piece, maps, seed):
        self.piece, self.maps = piece, maps
        self.rng = np.random.default_rng(seed)
        self.px = piece.density                     # pixels per stud
        self.pps = piece.density * piece.scale      # pixels per stud of brush size (small objects get a finer brush)
        self.canvas = np.zeros((C.TEX, C.TEX, 3), np.float32)
        self.strokes = 0
        self.mixes = {}
        style = C.STYLE.get(piece.name, C.STYLE.get(piece.name.split("_")[0], {}))
        self.gain = style.get("step_gain", 1.0)
        self.G = {**C.GLAZE, **style.get("glaze", {})}
        self.extra_layers = style.get("extra_layers", {})
        self.round_shine = style.get("round_shine", 0.0)
        # cut faces: paint the island's whole rectangle, so the low-detail shards (slightly different
        # outlines) never reach an unpainted texel
        for isl in piece.islands:
            if isl["part"].get("core"):
                x0, y0 = (int(v) - 2 for v in isl["origin_px"])
                x1, y1 = (int(o + s * self.px) + 3 for o, s in zip(isl["origin_px"], isl["size"]))
                block = self.maps["island"][max(y0, 0):y1, max(x0, 0):x1]
                block[block < 0] = isl["id"]

    def mix(self, group, family):
        """Every part gets its own mix of its family (pinker here, creamier there)."""
        key = (group, family)
        if key not in self.mixes:
            fam = C.PALETTE[family]
            if key in C.SHARED_MIX:
                self.mixes[key] = rgb(C.SHARED_MIX[key])
            else:
                h, l, s = fam["bases"][self.rng.integers(len(fam["bases"]))]
                self.mixes[key] = rgb((h + self.rng.uniform(-1.2, 1.2), l + self.rng.uniform(-0.012, 0.012), s))
        return self.mixes[key]

    def layers(self, zone, clip, layers, fam, angle, jitter):
        ys, xs = np.nonzero(zone)
        if not len(ys):
            return
        area = len(ys) / self.pps ** 2
        rng, pps = self.rng, self.pps
        for L in layers:
            count = int(L["per_stud2"] * area + rng.random())
            for k in rng.integers(0, len(ys), count):
                cx, cy = xs[k] + rng.random(), ys[k] + rng.random()
                sign = -1 if rng.random() < L.get("dark", 0.5) else 1
                color = step(self.canvas[ys[k], xs[k]], sign * L.get("step", 1), fam, self.gain)
                a = math.radians(angle + rng.uniform(-1, 1) * L.get("jitter", jitter))
                brush.stroke(self.canvas, clip, cx, cy, rng.uniform(*L["len"]) * pps, rng.uniform(*L["wid"]) * pps,
                             a, color, rng.uniform(*L["opacity"]), rng, round_=L.get("round", 0.0),
                             bend=rng.uniform(-0.12, 0.12))
            self.strokes += count

    def island(self, isl):
        mask_b = self.maps["island"] == isl["id"]
        if not mask_b.any():
            return
        mask = mask_b.astype(np.float32)
        part, family = isl["part"], isl["part"]["mat"]
        spec, fam = C.PAINT[family], C.PALETTE[family]
        spec = {**spec, "layers": spec["layers"] + self.extra_layers.get(family, [])}
        base = step(self.mix(part["group"], family), part.get("tone", 0), fam)
        self.canvas[mask_b] = base
        if part.get("staves") and isl["facet"] == "lathe":
            self.staves(isl, mask_b, base, fam, part["staves"])
        if part.get("stones") and isl["facet"] == "+z":
            self.stones(isl, mask_b, base, fam, part["stones"])

        if isl["grain_world"] is not None:
            g = isl["grain_world"]
            gu, gv = (0.0, 1.0) if isl["U"] is None else (g.dot(isl["U"]), g.dot(isl["V"]))
            if math.hypot(gu, gv) < 0.4:             # looking at the cut end of the wood
                self.layers(mask_b, mask, [spec.get("end_grain", spec["layers"][-1])], fam, 0, 180)
            else:
                self.layers(mask_b, mask, spec["layers"], fam, math.degrees(math.atan2(gv, gu)), spec["lean_jitter"])
        else:
            self.layers(mask_b, mask, spec["layers"], fam, spec.get("lean", 42), spec["lean_jitter"])

        if part.get("staves") and isl["facet"] == "lathe":
            self.stave_seams(isl, mask, fam, part["staves"])
        if self.round_shine and part.get("smooth") and isl["facet"] == "lathe":
            self.shine(isl, mask, fam)
        if part["band"] and family in ("plaster", "stone"):
            self.band(isl, mask_b)

    def stones(self, isl, mask_b, base, fam, stones):
        """Each paving stone is its own piece with its own tone: fill its outline before the strokes go on.
        A stone may be of another colour family (a creamier slab, an inset tile, a splash of dye); `soft`
        lets the paint underneath show through (a stain)."""
        part = isl["part"]
        place = self.piece.layout["islands"][isl["key"]]
        inv, (U, V) = part["frame"].inverted(), FACETS[isl["facet"]]
        for index, stone in enumerate(stones):
            points = [(isl["origin_px"][0] + ((inv @ Vector(q)).dot(U) - place["min"][0]) * self.px,
                       isl["origin_px"][1] + ((inv @ Vector(q)).dot(V) - place["min"][1]) * self.px) for q in stone["poly"]]
            sheet = Image.new("L", (C.TEX, C.TEX), 0)
            ImageDraw.Draw(sheet).polygon(points, fill=1)
            inside = mask_b & (np.asarray(sheet) > 0)
            family = stone.get("family")
            colour = step(self.mix(f"{part['group']}/{family}", family), stone["tone"], C.PALETTE[family]) if family \
                else step(base, stone["tone"], fam)
            cover = stone.get("soft", 1.0)
            self.canvas[inside] += (colour - self.canvas[inside]) * cover

    def _stave_edges(self, isl, count):
        x0 = isl["origin_px"][0]
        return [x0 + isl["size"][0] * self.px * k / count for k in range(count + 1)]

    def staves(self, isl, mask_b, base, fam, count):
        """Each stave of a barrel is its own board with its own mix."""
        edges = self._stave_edges(isl, count)
        cols = np.arange(C.TEX)[None, :] + 0.5
        for a, b in zip(edges, edges[1:]):
            self.canvas[mask_b & (cols >= a) & (cols < b)] = step(base, int(self.rng.integers(-2, 3)), fam)

    def stave_seams(self, isl, mask, fam, count):
        rng, pps = self.rng, self.pps
        y0, height = isl["origin_px"][1], isl["size"][1] * self.px
        for x in self._stave_edges(isl, count):
            t = 0.0
            while t < height:
                seg = rng.uniform(0.5, 1.4) * pps
                cy = y0 + min(t + seg / 2, height)
                iy, ix = min(int(cy), C.TEX - 1), min(max(int(x), 0), C.TEX - 1)
                brush.stroke(self.canvas, mask, x, cy, seg * 1.15, rng.uniform(0.035, 0.06) * pps, math.pi / 2,
                             step(self.canvas[iy, ix], -3, fam), rng.uniform(0.6, 0.85), rng)
                self.strokes += 1
                t += seg

    def band(self, isl, mask_b):
        """Turquoise band at the foot of the wall with a hand-painted, wandering top edge."""
        spec, fam = C.PAINT["band"], C.PALETTE["band"]
        z = self.maps["pos"][..., 2]
        rng, pps = self.rng, self.pps
        near = mask_b & (z < C.BAND_H + spec["ragged"])
        if not near.any():
            return
        solid = mask_b & (z < C.BAND_H - spec["ragged"])
        one = np.ones(3, np.float32)
        tmp = np.zeros(mask_b.shape + (3,), np.float32)
        ys, xs = np.nonzero(near & ~solid & (z < C.BAND_H))
        for k in rng.integers(0, max(len(ys), 1), int(len(ys) / pps ** 2 * 14) if len(ys) else 0):
            brush.stroke(tmp, mask_b.astype(np.float32), xs[k], ys[k], rng.uniform(0.3, 0.7) * pps,
                         rng.uniform(0.3, 0.6) * pps, math.radians(rng.uniform(0, 180)), one, 1.0, rng, round_=0.9)
        alpha = np.clip(np.maximum(tmp[..., 0], solid), 0, 1) * mask_b      # soft, wandering top edge
        zone = alpha > 0.5
        band_base = self.mix(isl["part"]["group"], "band")
        plaster = self.canvas.copy()
        self.canvas += (band_base - self.canvas) * alpha[..., None]
        self.layers(zone, alpha, spec["layers"], fam, spec["lean"], spec["lean_jitter"])
        # a little plaster showing through where the paint has worn thin
        ys, xs = np.nonzero(zone)
        chips = int(spec["chips"] * len(ys) / pps ** 2)
        for k in rng.integers(0, max(len(ys), 1), chips):
            worn = plaster[ys[k], xs[k]] * 0.55 + self.canvas[ys[k], xs[k]] * 0.45
            brush.stroke(self.canvas, alpha, xs[k], ys[k], rng.uniform(0.1, 0.3) * pps, rng.uniform(0.08, 0.2) * pps,
                         math.radians(rng.uniform(0, 180)), worn, rng.uniform(0.5, 0.8), rng, round_=0.9)
        self.strokes += chips

    def shine(self, isl, mask, fam):
        """A round part catches the light along one line: brush a highlight there, a dark line under it."""
        rng, frame = self.rng, isl["part"]["frame"].to_3x3()
        light = (-0.25, -0.55, 0.8)                       # up, and toward the side the player sees
        facing = lambda axis: sum(frame[k][axis] * light[k] for k in range(3))
        turn = math.atan2(facing(1), facing(0)) % (2 * math.pi)
        width, height = isl["size"][0] * self.px, isl["size"][1] * self.px
        pale = rgb(C.PALE)
        for offset, lighter, wide in ((0.0, True, 0.11), (0.3, False, 0.05)):
            x = isl["origin_px"][0] + ((turn / (2 * math.pi) + offset) % 1.0) * width
            t = 0.0
            while t < height:
                seg = rng.uniform(0.25, 0.7) * height
                cy = isl["origin_px"][1] + min(t + seg / 2, height)
                under = self.canvas[min(int(cy), C.TEX - 1), min(max(int(x), 0), C.TEX - 1)]
                color = under + (pale - under) * self.round_shine if lighter else step(under, -3, fam, self.gain)
                brush.stroke(self.canvas, mask, x + rng.uniform(-1, 1), cy, seg * 1.1, max(2.0, wide * width),
                             math.pi / 2, color, rng.uniform(0.55, 0.85), rng, round_=0.2)
                self.strokes += 1
                t += seg * rng.uniform(0.8, 1.1)

    def marks(self):
        """Detail lines a recipe asked for: a dark stroke, and a thin light one beside it so it reads as cut in."""
        rng, piece = self.rng, self.piece
        islands = {isl["key"]: isl for isl in piece.islands}
        for m in piece.marks:
            part = piece.parts[m["pid"]]
            key = (part["group"], part["mat"], m["facet"])
            if key not in islands:
                continue
            isl, place, fam = islands[key], piece.layout["islands"][key], C.PALETTE[part["mat"]]
            clip = (self.maps["island"] == isl["id"]).astype(np.float32)
            if m["facet"] == "lathe":
                pts = [(isl["origin_px"][0] + turn * isl["size"][0] * self.px,
                        isl["origin_px"][1] + (along - place["min"][1]) * self.px) for turn, along in m["points"]]
            else:
                inv, (U, V) = part["frame"].inverted(), FACETS[m["facet"]]
                pts = [(isl["origin_px"][0] + ((inv @ q).dot(U) - place["min"][0]) * self.px,
                        isl["origin_px"][1] + ((inv @ q).dot(V) - place["min"][1]) * self.px) for q in m["points"]]
            if m["closed"]:
                pts.append(pts[0])
            width = max(1.6, m["width"] * self.px)
            for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
                length, angle = math.hypot(x1 - x0, y1 - y0), math.atan2(y1 - y0, x1 - x0)
                pieces = max(1, int(length / (width * 9)))
                for k in range(pieces):
                    a, b = k / pieces, (k + 1) / pieces
                    cx, cy = x0 + (x1 - x0) * (a + b) / 2, y0 + (y1 - y0) * (a + b) / 2
                    under = self.canvas[min(max(int(cy), 0), C.TEX - 1), min(max(int(cx), 0), C.TEX - 1)]
                    if m.get("family"):                   # a pattern line in its own colour
                        other = C.PALETTE[m["family"]]
                        color = step(self.mix(part["group"] + "/pattern", m["family"]), int(rng.integers(-1, 2)), other)
                        brush.stroke(self.canvas, clip, cx, cy, length * (b - a) * 1.1 + width * 0.6,
                                     width * rng.uniform(0.9, 1.15), angle + rng.uniform(-0.03, 0.03), color,
                                     rng.uniform(0.85, 0.97), rng, rag=0.06, round_=0.3)
                        self.strokes += 1
                        continue
                    seg = length * (b - a) * 1.25 + width
                    brush.stroke(self.canvas, clip, cx, cy, seg, width * rng.uniform(0.85, 1.2), angle + rng.uniform(-0.03, 0.03),
                                 step(under, m["tone"], fam, self.gain), rng.uniform(0.75, 0.95), rng, rag=0.08)
                    brush.stroke(self.canvas, clip, cx + width * 0.9 * math.sin(angle), cy - width * 0.9 * math.cos(angle) - 0.4,
                                 seg * 0.9, width * 0.6, angle, step(under, 3, fam, self.gain), rng.uniform(0.35, 0.6), rng, rag=0.2)
                    self.strokes += 2

    def glazes(self):
        """Dark glaze settles where surfaces meet (toward lavender, never gray);
        pale glaze stays on protruding edges."""
        G, rng, pps = self.G, self.rng, self.pps
        covered = self.maps["island"] >= 0
        mask = covered.astype(np.float32)
        occ = np.where(covered, self.maps["ao"], 0.0)
        lav, pale = rgb(C.LAVENDER), rgb(C.PALE)
        ys, xs = np.nonzero(occ > 0.12)
        if len(ys):
            weight = occ[ys, xs].astype(np.float64) ** 2
            count = int(G["shade_per_stud2"] * weight.sum() / pps ** 2)
            for k in rng.choice(len(ys), count, p=weight / weight.sum()):
                under = self.canvas[ys[k], xs[k]]
                o = float(occ[ys[k], xs[k]])
                dark = under * (1.0 - 0.045 * G["shade_steps"])
                color = dark + (lav * dark.mean() / lav.mean() - dark) * G["shade_mix"]
                size = rng.uniform(*G["shade_size"]) * pps
                brush.stroke(self.canvas, mask, xs[k] + rng.random(), ys[k] + rng.random(), size * rng.uniform(1.0, 2.0),
                             size, math.radians(rng.uniform(0, 180)), color, min(0.2 + 0.6 * o, 0.85), rng, round_=0.9)
            self.strokes += count
        dark_spec = G.get("edge_dark")
        for isl_id, segments in self.maps["edges"].items():
            clip = (self.maps["island"] == isl_id).astype(np.float32)
            fam = C.PALETTE[self.piece.islands[isl_id]["part"]["mat"]]
            for x0, y0, x1, y1, fx, fy, sharp in segments:
                length = math.hypot(x1 - x0, y1 - y0)
                if length < G["edge_min"] * pps:
                    continue
                # a rounded edge is several shallow folds: each gets a broken line, not a solid one
                cover = min(1.0, max(0.25, (math.degrees(sharp) - 25.0) / 20.0))
                angle = math.atan2(y1 - y0, x1 - x0)
                nx, ny = -(y1 - y0) / length, (x1 - x0) / length            # points into the face
                if nx * (fx - (x0 + x1) / 2) + ny * (fy - (y0 + y1) / 2) < 0:
                    nx, ny = -nx, -ny
                t = 0.0
                while t < length:
                    seg = rng.uniform(*G["edge_len"]) * pps
                    m = min(t + seg / 2, length) / length
                    cx, cy = x0 + (x1 - x0) * m, y0 + (y1 - y0) * m
                    wid = rng.uniform(*G["edge_wid"]) * pps
                    if dark_spec and rng.random() < dark_spec["cover"] * cover:      # dark stroke just inside the edge
                        dx, dy = cx + nx * wid * dark_spec["inset"], cy + ny * wid * dark_spec["inset"]
                        under = self.canvas[min(max(int(dy), 0), C.TEX - 1), min(max(int(dx), 0), C.TEX - 1)]
                        brush.stroke(self.canvas, clip, dx, dy, min(seg, length) * 1.1, rng.uniform(*dark_spec["wid"]) * pps,
                                     angle, step(under, -dark_spec["steps"], fam, self.gain), rng.uniform(0.5, 0.8), rng)
                        self.strokes += 1
                    if rng.random() < G["edge_cover"] * cover:
                        iy, ix = min(max(int(cy), 0), C.TEX - 1), min(max(int(cx), 0), C.TEX - 1)
                        under = step(self.canvas[iy, ix], G.get("edge_steps", 0), fam, self.gain)
                        color = under + (pale - under) * G["edge_mix"]
                        brush.stroke(self.canvas, clip, cx, cy, min(seg, length) * 1.15, wid * 2,
                                     angle, color, rng.uniform(0.6, 0.9), rng, round_=0.3)
                        self.strokes += 1
                    t += seg

    def run(self):
        for isl in self.piece.islands:
            self.island(isl)
        self.marks()
        self.glazes()
        covered = self.maps["island"] >= 0
        out = brush.pad(self.canvas, covered, C.PAD * 2)
        return np.flipud((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))

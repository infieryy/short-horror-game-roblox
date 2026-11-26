"""Paint side of a recipe. Follows the look rules:

1. one colour family per material          5. every part gets its own mix
2. every surface starts as one flat colour  6. turquoise only as a band at the bottom
3. strokes all lean the same way            7. no painted shadows; lavender where light can't reach
4. each stroke is ONE step lighter/darker   8. two glazes: pale on edges, dark in corners
"""
import colorsys
import math

import numpy as np

import brush
import config as C


def rgb(hls):
    h, l, s = hls
    return np.array(colorsys.hls_to_rgb((h % 360) / 360.0, l, s), np.float32)


def step(color, n, fam):
    """Move a colour n small steps lighter (+) or darker (-), staying inside its family."""
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
        self.pps = piece.density                    # pixels per stud
        self.canvas = np.zeros((C.TEX, C.TEX, 3), np.float32)
        self.strokes = 0
        self.mixes = {}

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
                color = step(self.canvas[ys[k], xs[k]], 1 if rng.random() < 0.5 else -1, fam)
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
        base = step(self.mix(part["group"], family), part.get("tone", 0), fam)
        self.canvas[mask_b] = base
        if part.get("staves") and isl["facet"] == "lathe":
            self.staves(isl, mask_b, base, fam, part["staves"])

        if isl["grain_world"] is not None:
            g = isl["grain_world"]
            gu, gv = (0.0, 1.0) if isl["U"] is None else (g.dot(isl["U"]), g.dot(isl["V"]))
            if math.hypot(gu, gv) < 0.4:             # looking at the cut end of the wood
                self.layers(mask_b, mask, [spec["end_grain"]], fam, 0, 180)
            else:
                self.layers(mask_b, mask, spec["layers"], fam, math.degrees(math.atan2(gv, gu)), spec["lean_jitter"])
        else:
            self.layers(mask_b, mask, spec["layers"], fam, spec.get("lean", 42), spec["lean_jitter"])

        if part.get("staves") and isl["facet"] == "lathe":
            self.stave_seams(isl, mask, fam, part["staves"])
        if part["band"] and family in ("plaster", "stone"):
            self.band(isl, mask_b)

    def _stave_edges(self, isl, count):
        x0 = isl["origin_px"][0]
        return [x0 + isl["size"][0] * self.pps * k / count for k in range(count + 1)]

    def staves(self, isl, mask_b, base, fam, count):
        """Each stave of a barrel is its own board with its own mix."""
        edges = self._stave_edges(isl, count)
        cols = np.arange(C.TEX)[None, :] + 0.5
        for a, b in zip(edges, edges[1:]):
            self.canvas[mask_b & (cols >= a) & (cols < b)] = step(base, int(self.rng.integers(-2, 3)), fam)

    def stave_seams(self, isl, mask, fam, count):
        rng, pps = self.rng, self.pps
        y0, height = isl["origin_px"][1], isl["size"][1] * pps
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

    def glazes(self):
        """Dark glaze settles where surfaces meet (toward lavender, never gray);
        pale glaze stays on protruding edges."""
        G, rng, pps = C.GLAZE, self.rng, self.pps
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
        for isl_id, segments in self.maps["edges"].items():
            clip = (self.maps["island"] == isl_id).astype(np.float32)
            for x0, y0, x1, y1 in segments:
                length = math.hypot(x1 - x0, y1 - y0)
                if length < G["edge_min"] * pps:
                    continue
                angle = math.atan2(y1 - y0, x1 - x0)
                t = 0.0
                while t < length:
                    seg = rng.uniform(*G["edge_len"]) * pps
                    if rng.random() < G["edge_cover"]:
                        m = min(t + seg / 2, length) / length
                        cx, cy = x0 + (x1 - x0) * m, y0 + (y1 - y0) * m
                        iy, ix = min(max(int(cy), 0), C.TEX - 1), min(max(int(cx), 0), C.TEX - 1)
                        under = self.canvas[iy, ix]
                        color = under + (pale - under) * G["edge_mix"]
                        brush.stroke(self.canvas, clip, cx, cy, min(seg, length), rng.uniform(*G["edge_wid"]) * pps * 2,
                                     angle, color, rng.uniform(0.5, 0.85), rng, round_=0.3)
                        self.strokes += 1
                    t += seg

    def run(self):
        for isl in self.piece.islands:
            self.island(isl)
        self.glazes()
        covered = self.maps["island"] >= 0
        out = brush.pad(self.canvas, covered, C.PAD * 2)
        return np.flipud((np.clip(out, 0, 1) * 255 + 0.5).astype(np.uint8))

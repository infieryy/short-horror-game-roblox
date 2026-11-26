"""Flat-brush engine. Every stroke is numbers: centre, length, width, angle, colour, opacity.

A stroke is a solid body made of thin bristle strands; each strand starts and stops at its
own random point, so the two ends look dragged and soft instead of cut.
No noise, no gradients: only strokes.
"""
import math

import numpy as np


def _smooth(x, width):
    t = np.clip(x / width, 0.0, 1.0)
    return t * t * (3.0 - 2.0 * t)


def stroke(canvas, mask, cx, cy, length, width, angle, color, opacity, rng,
           round_=0.0, rag=0.14, taper=0.18, strand_px=2.5, bend=0.0):
    """Paint one stroke into canvas (H,W,3 float32), clipped by mask (H,W float32). Pixels, y up."""
    H, W = mask.shape
    c, s = math.cos(angle), math.sin(angle)
    hl, hw = length / 2.0, width / 2.0
    ex = abs(hl * c) + abs(hw * s) + 2.0
    ey = abs(hl * s) + abs(hw * c) + 2.0
    x0, x1 = max(int(cx - ex), 0), min(int(cx + ex) + 1, W)
    y0, y1 = max(int(cy - ey), 0), min(int(cy + ey) + 1, H)
    if x0 >= x1 or y0 >= y1:
        return
    X = (np.arange(x0, x1, dtype=np.float32) + 0.5 - cx)[None, :]
    Y = (np.arange(y0, y1, dtype=np.float32) + 0.5 - cy)[:, None]
    sl = X * c + Y * s
    tl = -X * s + Y * c
    if bend:
        tl = tl - bend * width * ((sl / hl) ** 2 - 0.33)
    K = max(2, int(width / strand_px))
    k = np.clip(((tl / width + 0.5) * K).astype(np.int32), 0, K - 1)
    r0 = rng.random(K) * rag * length
    r1 = rng.random(K) * rag * length
    if round_ > 0.0:
        edge = 1.0 - np.sqrt(np.clip(1.0 - (2.0 * (np.arange(K) + 0.5) / K - 1.0) ** 2, 0.0, 1.0))
        r0 = r0 + round_ * edge * hl
        r1 = r1 + round_ * edge * hl
    strand = (0.84 + 0.16 * rng.random(K)).astype(np.float32)
    soft = max(1.5, taper * length)
    a = _smooth(sl + hl - r0[k].astype(np.float32), soft) * _smooth(hl - r1[k].astype(np.float32) - sl, soft)
    a *= np.clip(hw - np.abs(tl) + 0.5, 0.0, 1.0)
    a *= strand[k] * opacity
    a *= mask[y0:y1, x0:x1]
    region = canvas[y0:y1, x0:x1]
    region += (color - region) * a[..., None]


def pad(image, covered, iterations):
    """Grow painted colour outward into empty texels so mip-maps never show a seam."""
    img = image.copy()
    cov = covered.copy()
    for _ in range(iterations):
        acc = np.zeros_like(img)
        cnt = np.zeros(cov.shape, np.float32)
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            acc += np.roll(img * cov[..., None], (dy, dx), (0, 1))
            cnt += np.roll(cov.astype(np.float32), (dy, dx), (0, 1))
        grow = (~cov) & (cnt > 0)
        img[grow] = acc[grow] / cnt[grow][:, None]
        cov = cov | grow
    return img

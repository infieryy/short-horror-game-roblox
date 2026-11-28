"""Draws the shot effects as flipbook sheets: python flipbooks.py   (writes out/fx_*.png and out/preview*.png)

Second drawing, from scratch. The first was soft shapes filled by depth, and it read as clip art: the owner,
"The VFX is still really bad. Redraw the flipbooks from scratch ... use multiple valorant references".

What Riot's frames show (REFERENCE.md has them one by one) is flat, hard-edged, angular drawing: every shape is
a cluster of long tapered blades, each blade a different length, filled in flat bands that go pale yellow in
the middle, yellow, orange, and red at the tips. Light is a separate flat disc behind. Nothing is a gradient.
So everything here is polygons: a blade is a four-cornered kite, a burst is blades round a lump, and the
colour bands are the same burst drawn again shorter and thinner inside itself.

Sheets (1024 x 1024, 16 frames of 256, read left to right, top to bottom):
    fx_muzzle   the flash at the muzzle
    fx_spark    where a shot lands: a white star, then a puff
    fx_body     a hit on a body
    fx_head     a hit on a head
And fx_tracer (256 x 32): the tracer's line across its width.
"""
import math
import os

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
FRAME = 256
SUPER = 4
W = FRAME * SUPER

WHITE = (255, 252, 214)
PALE = (255, 240, 150)
HOT = (255, 246, 178)
YELLOW = (255, 224, 84)
AMBER = (255, 178, 40)
ORANGE = (255, 126, 26)
FLAME = (248, 82, 34)
RED = (228, 44, 42)
CRIMSON = (178, 22, 46)
SALMON = (244, 108, 84)
SMOKE = (234, 228, 222)


def px(point):
    return ((point[0] + 1) * 0.5 * W, (1 - point[1]) * 0.5 * W)


def mask(polys, blur=0.0, grow=0.0, holes=()):
    """The polygons as one shape. `grow` fattens it, `blur` softens its edge (both in frame units, where the
    frame is 2 across), `holes` are polygons cut out of it."""
    image = Image.new("L", (W, W), 0)
    draw = ImageDraw.Draw(image)
    for poly in polys:
        points = [px(p) for p in poly]
        draw.polygon(points, fill=255)
        if grow > 0:
            draw.line(points + points[:2], fill=255, width=max(1, int(round(grow * W))), joint="curve")
    for poly in holes:
        draw.polygon([px(p) for p in poly], fill=0)
    if blur > 0:
        image = image.filter(ImageFilter.GaussianBlur(blur * W / 2))
    return image


class Frame:
    def __init__(self):
        self.rgb = np.zeros((W, W, 3), np.float32)  # premultiplied
        self.alpha = np.zeros((W, W), np.float32)

    def lay(self, shape, colour, alpha=1.0):
        m = np.asarray(shape, np.float32) * (alpha / 255.0)
        self.rgb = self.rgb * (1 - m[..., None]) + np.asarray(colour, np.float32) * m[..., None]
        self.alpha = self.alpha * (1 - m) + m

    def image(self, bleed=ORANGE):
        a = self.alpha.reshape(FRAME, SUPER, FRAME, SUPER).mean(axis=(1, 3))
        c = self.rgb.reshape(FRAME, SUPER, FRAME, SUPER, 3).mean(axis=(1, 3))
        straight = np.where(a[..., None] > 1e-3, c / np.maximum(a[..., None], 1e-3), np.asarray(bleed, np.float32))
        out = np.dstack([straight, a * 255]).round().clip(0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")


def kite(origin, degrees, length, width, start=0.0, tail=0.0, shoulder=0.24, lean=0.0, skew=1.0):
    """A blade: a point at its tail, widest a quarter of the way along, a long taper to a point. `start`
    moves all of it out along its own direction (a blade that has left the burst)."""
    a = math.radians(degrees)
    dx, dy = math.cos(a), math.sin(a)
    nx, ny = -dy, dx
    ox, oy = origin[0] + dx * start, origin[1] + dy * start
    sx, sy = ox + dx * length * shoulder, oy + dy * length * shoulder
    return [
        (ox - dx * tail, oy - dy * tail),
        (sx + nx * width, sy + ny * width),
        (ox + dx * length + nx * lean, oy + dy * length + ny * lean),
        (sx - nx * width * skew, sy - ny * width * skew),
    ]


def lump(origin, radius, seed, corners=11):
    """An uneven many-cornered middle for a burst."""
    rng = np.random.default_rng(seed)
    points = []
    for index in range(corners):
        a = 2 * math.pi * (index + rng.uniform(-0.25, 0.25)) / corners
        r = radius * rng.uniform(0.78, 1.12)
        points.append((origin[0] + math.cos(a) * r, origin[1] + math.sin(a) * r))
    return points


def disc(origin, radius, squash=1.0, corners=40):
    return [
        (origin[0] + math.cos(2 * math.pi * i / corners) * radius, origin[1] + math.sin(2 * math.pi * i / corners) * radius * squash)
        for i in range(corners)
    ]


def burst(frame, origin, blades, bands, size=1.0, core=0.0, seed=1, apart=0.0, only=None):
    """Blades round a lump, drawn once for each colour band, outermost first. A band is (colour, how long,
    how wide, how big the lump, alpha), each a share of the full burst. `apart` is how far the blades have
    left the middle, as a share of their own length."""
    for colour, long, wide, middle, alpha in bands:
        polys = []
        for degrees, length, width in blades:
            if only and not only(degrees):
                continue
            reach = length * size
            polys.append(kite(origin, degrees, reach * long, width * size * wide, start=reach * apart + reach * (1 - long) * 0.12))
        if core > 0 and middle > 0:
            polys.append(lump(origin, core * size * middle, seed))
        frame.lay(mask(polys), colour, alpha)


def at(stage, keys, values):
    return float(np.interp(stage, keys, values))


# ---------------------------------------------------------------------------------------------------------
# The flash. Riot's frames of it (clip 1 frames 33 to 36, clip 2 frames 18 to 20, and the concept sheet's
# rifles): a cluster of blades with one thin one standing far above the rest, a long level beam, and a flat
# orange disc of light behind; the blades are pale in the middle and go orange then red to their tips. On the
# third frame the blades have left the middle and are orange; on the fourth a few salmon ones are left, to
# the forward side, with a thin pale arc in the air.
RIFLE = [
    (88, 0.92, 0.05), (124, 0.62, 0.11), (150, 0.44, 0.075), (200, 0.66, 0.1), (232, 0.42, 0.085),
    (266, 0.36, 0.07), (54, 0.5, 0.09), (16, 0.36, 0.075), (320, 0.33, 0.07), (104, 0.46, 0.06),
    (72, 0.4, 0.065), (176, 0.5, 0.07), (140, 0.56, 0.06), (216, 0.36, 0.06),
]


def muzzle(index):
    frame = Frame()
    stage = index / 15 * 4
    size = at(stage, [0, 0.27, 1, 2, 3, 4], [0.78, 1.0, 0.96, 0.8, 0.6, 0.45])
    hot = at(stage, [0, 1.3, 2.2, 3], [1, 1, 0.4, 0])
    beam = at(stage, [0, 0.3, 1.4, 2.4, 3.3, 4], [0.7, 1, 0.95, 0.6, 0.22, 0])
    light = at(stage, [0, 0.4, 1.5, 2.6, 3.4], [0.75, 1, 0.85, 0.4, 0])
    apart = at(stage, [0, 1.7, 2.4, 4], [0, 0, 0.16, 0.42])
    fade = at(stage, [0, 2.8, 4], [1, 1, 0.3])
    rng = np.random.default_rng(100 + index)
    blades = [(a + rng.uniform(-1.5, 1.5), l * rng.uniform(0.93, 1.07), w) for a, l, w in RIFLE]
    if light > 0:
        frame.lay(mask([disc((-0.04, 0.02), 0.6)], blur=0.1), FLAME, 0.4 * light)
        frame.lay(mask([disc((-0.04, 0.02), 0.46)], blur=0.07), ORANGE, 0.5 * light)
        frame.lay(mask([disc((-0.02, 0.01), 0.3)], blur=0.05), AMBER, 0.55 * light)
    if beam > 0.02:
        left, right = -0.98 * beam, 0.4 * beam
        for colour, long, thick in ((FLAME, 1, 0.085), (ORANGE, 0.94, 0.064), (YELLOW, 0.82, 0.042), (PALE, 0.6, 0.022)):
            if colour in (YELLOW, PALE) and hot < 0.5:
                continue
            t = thick * (0.45 + 0.55 * beam)
            frame.lay(mask([[(left * long, 0), (-0.06, t), (right * long, 0), (-0.06, -t)]]), colour)
    if hot > 0.6:
        bands = [(FLAME, 1, 1, 1, 1), (ORANGE, 0.9, 0.84, 0.94, 1), (YELLOW, 0.72, 0.68, 0.84, 1), (PALE, 0.5, 0.5, 0.68, 1)]
        burst(frame, (0, 0), blades, bands, size, core=0.3, seed=7)
        frame.lay(mask([lump((0, 0), 0.13 * size, 9)], blur=0.02), HOT, 0.92)
    elif hot > 0.05:
        bands = [(FLAME, 1, 1, 0, 1), (ORANGE, 0.86, 0.8, 0, 1), (YELLOW, 0.5, 0.5, 0, 1)]
        burst(frame, (0, 0), blades, bands, size, apart=apart)
        frame.lay(mask([lump((0, 0), 0.14 * size, 7)]), ORANGE)
        frame.lay(mask([lump((0, 0), 0.08 * size, 9)]), YELLOW)
    else:
        forward = lambda degrees: 95 < degrees < 265
        bands = [(SALMON, 1, 1, 0, fade), (ORANGE, 0.6, 0.55, 0, fade)]
        burst(frame, (0, 0), blades, bands, size, apart=apart, only=forward)
    if 2.8 < stage:
        ring = Image.new("L", (W, W), 0)
        x0, y0 = px((-0.62, 0.7))
        x1, y1 = px((0.2, -0.12))
        ImageDraw.Draw(ring).arc([x0, y0, x1, y1], 195, 285, fill=255, width=int(0.009 * W))
        frame.lay(ring.filter(ImageFilter.GaussianBlur(0.005 * W)), WHITE, 0.16 * at(stage, [2.8, 3.2, 4], [0, 1, 0.2]))
    return frame.image(ORANGE)


# ---------------------------------------------------------------------------------------------------------
# Where the shot lands (clip 1 frames 33 to 35, clip 2 frames 18 to 22): at once, a small hard white star of
# uneven points; then a pale round puff with the star's middle still in it, which opens into a ring and goes.
STAR = [(82, 0.46, 0.085), (150, 0.31, 0.075), (213, 0.40, 0.08), (288, 0.28, 0.075), (8, 0.36, 0.08), (120, 0.2, 0.06), (330, 0.2, 0.06), (250, 0.19, 0.055)]


def spark(index):
    frame = Frame()
    rng = np.random.default_rng(31)
    if index >= 2:
        reach = at(index, [2, 6, 15], [0.2, 0.44, 0.62])
        show = at(index, [2, 4, 8, 14], [0.0, 0.58, 0.4, 0.0])
        blobs, inner = [disc((0, 0), reach * 0.6)], []
        for k in range(7):
            a = 2 * math.pi * (k + rng.uniform(-0.3, 0.3)) / 7 + 0.3
            r = reach * rng.uniform(0.3, 0.52)
            d = reach * rng.uniform(0.5, 0.7)
            blobs.append(disc((math.cos(a) * d, math.sin(a) * d), r))
            inner.append(disc((math.cos(a) * d - 0.035, math.sin(a) * d + 0.035), r * 0.62))
        hole = at(index, [5, 10, 15], [0.0, 0.52, 0.95]) * reach
        holes = [lump((0.03, -0.02), hole, 40 + index // 2, corners=9)] if hole > 0.01 else []
        for k in range(5):
            a = 2 * math.pi * k / 5 + 0.9 + rng.uniform(-0.4, 0.4)
            r = at(index, [6, 15], [0.0, 0.42]) * reach * rng.uniform(0.6, 1.2)
            if r > 0.01:
                holes.append(lump((math.cos(a) * reach * 0.85, math.sin(a) * reach * 0.85), r, 50 + k, corners=8))
        frame.lay(mask(blobs, blur=0.022, holes=holes), SMOKE, show)
        frame.lay(mask(inner, blur=0.022, holes=holes), WHITE, show * 0.5)
    size = at(index, [0, 1, 3, 6, 9], [0.75, 1.0, 0.82, 0.42, 0.0])
    if size > 0.02:
        bands = [((255, 232, 140), 1, 1, 1, 1), (WHITE, 0.88, 0.8, 0.86, 1)]
        burst(frame, (0, 0), STAR, bands, size, core=0.12, seed=3)
    for k, degrees in enumerate((40, 135, 250, 330, 195)):
        out = at(index, [1, 12], [0.2, 0.8 + 0.05 * k])
        long = at(index, [1, 4, 12], [0.0, 0.1, 0.0])
        if long > 0.005:
            frame.lay(mask([kite((0, 0), degrees, long, 0.014, start=out)]), PALE, 0.9)
    return frame.image(SMOKE)


# ---------------------------------------------------------------------------------------------------------
# A hit on a body (clip 3 frames 26 to 28, and the two stills of it): a compact burst of blades, pale in the
# middle, orange, red at the rim, there for three frames, then its blades fly apart. (The dark squares round
# it in Riot's stills are the debug crosshair, not the effect: the first drawing here took them for blobs.)
BODY = [
    (78, 0.66, 0.12), (128, 0.5, 0.12), (168, 0.6, 0.11), (212, 0.46, 0.12), (250, 0.58, 0.12),
    (296, 0.48, 0.12), (338, 0.62, 0.11), (22, 0.48, 0.12), (102, 0.42, 0.09), (190, 0.42, 0.09),
    (274, 0.4, 0.09), (0, 0.42, 0.09), (52, 0.42, 0.09), (232, 0.4, 0.085), (148, 0.4, 0.08), (316, 0.4, 0.08),
]


def body(index):
    frame = Frame()
    size = at(index, [0, 1, 2, 6, 15], [0.6, 1.0, 1.06, 1.0, 0.8])
    apart = at(index, [6, 9, 15], [0.0, 0.5, 1.5])
    shrink = at(index, [6, 15], [1.0, 0.3])
    fade = at(index, [9, 15], [1.0, 0.45])
    light = at(index, [0, 1, 6, 11], [0.6, 1, 0.8, 0])
    rng = np.random.default_rng(200 + index // 2)
    blades = [(a + rng.uniform(-2, 2), l * rng.uniform(0.94, 1.06) * shrink, w * (0.3 + 0.7 * shrink) ** 1.5) for a, l, w in BODY]
    if light > 0:
        frame.lay(mask([disc((0, 0), 0.66)], blur=0.1), RED, 0.5 * light)
        frame.lay(mask([disc((0, 0), 0.48)], blur=0.07), FLAME, 0.5 * light)
    if index <= 6:
        bands = [(RED, 1, 1, 1, 1), (FLAME, 0.92, 0.88, 0.95, 1), (ORANGE, 0.82, 0.78, 0.9, 1), (YELLOW, 0.64, 0.64, 0.8, 1), (PALE, 0.46, 0.5, 0.68, 1)]
        burst(frame, (0, 0), blades, bands, size, core=0.36, seed=11)
        frame.lay(mask([lump((0, 0), 0.15 * size, 13)], blur=0.025), HOT, 0.92)
    elif index <= 9:
        bands = [(RED, 1, 1, 1, 1), (FLAME, 0.9, 0.84, 0.8, 1), (ORANGE, 0.72, 0.7, 0.55, 1), (YELLOW, 0.4, 0.45, 0, 1)]
        burst(frame, (0, 0), blades, bands, size, core=0.12 * (8 - index) / 2 if index < 8 else 0, seed=11, apart=apart)
    else:
        bands = [(RED, 1, 1, 0, fade), (FLAME, 0.78, 0.72, 0, fade), (ORANGE, 0.45, 0.45, 0, fade)]
        burst(frame, (0, 0), blades, bands, size, apart=apart)
    return frame.image(FLAME)


# ---------------------------------------------------------------------------------------------------------
# A hit on a head (clip 1 frames 36 to 43, and the still of frame 36 at six times its size). It is not a
# flame. It is a hard-edged pale fan thrown UP from the hit: pointed at its foot, widening to shoulders that
# flick out into a short spike each side, with a tall spike in the middle. A thin orange line edges it and a
# tight red light hugs that. From the second frame a white jagged star sits on the hit itself, with dark red
# blades behind it to the sides, and a flat salmon patch lies behind everything. The fan grows taller, then
# narrows to a streak and is gone; the star goes last.
FOOT = (0.0, -0.5)
UNIT = 1.1  # the fan's height on its first frame, in frame units

GLINT = [(226, 0.4, 0.075), (314, 0.42, 0.075), (182, 0.36, 0.065), (358, 0.37, 0.065), (270, 0.24, 0.065), (136, 0.27, 0.065), (44, 0.27, 0.065), (92, 0.2, 0.06)]
SHARDS = [(196, 0.62, 0.08), (344, 0.64, 0.08), (158, 0.54, 0.07), (22, 0.56, 0.07), (238, 0.4, 0.065), (302, 0.4, 0.065)]


def fan(tall, wide, split, lean=0.0):
    """The fan's outline. `tall` is its height and `wide` its half-width at the shoulders, in frame units;
    `split` (0 to 1) is how far the side spikes stand out from the middle one."""
    fx, fy = FOOT
    def p(x, y):
        return (fx + x * wide + lean * y, fy + y * tall)
    side = 0.56 + 0.08 * split
    return [
        p(0.0, -0.1),
        p(-0.26, 0.05), p(-0.5, 0.22), p(-0.84, 0.45),
        p(-1.04 - 0.14 * split, side + 0.04),  # the left flick
        p(-0.62, 0.53), p(-0.4, 0.62), p(-0.2, 0.8),
        p(0.04, 1.0),  # the tall one
        p(0.22, 0.78), p(0.42, 0.6), p(0.6, 0.52),
        p(0.94 + 0.14 * split, side + 0.02),  # the right flick
        p(0.78, 0.42), p(0.48, 0.2), p(0.25, 0.04),
    ]


def scaled(poly, about, k):
    return [(about[0] + (x - about[0]) * k, about[1] + (y - about[1]) * k) for x, y in poly]


def head(index):
    frame = Frame()
    stage = index / 2.0  # 0 to 7.5, through Riot's eight frames
    tall = UNIT * at(stage, [0, 1, 2, 3, 4, 5, 6, 7], [0.9, 1.0, 1.12, 1.28, 1.3, 1.3, 1.1, 0.7])
    wide = at(stage, [0, 1, 2, 3, 4, 5, 6, 7], [0.32, 0.42, 0.44, 0.4, 0.3, 0.19, 0.07, 0.02])
    split = at(stage, [0, 1, 2, 4, 6], [0.3, 0.8, 1.0, 0.6, 0.0])
    there = at(stage, [0, 6, 6.8, 7.2], [1, 1, 0.7, 0])
    patch = at(stage, [0, 0.5, 4, 6, 7.5], [0.7, 1, 1, 0.75, 0.0])
    star = at(stage, [0.4, 1, 2, 4.5, 5.5, 6.4], [0.0, 0.9, 1.0, 0.9, 0.6, 0.0])
    shards = at(stage, [0.4, 1, 3, 4.5], [0.0, 1.0, 0.9, 0.0])
    lift = at(stage, [0, 3, 6], [0.0, 0.0, 0.12])  # late on, the fan's foot leaves the hit
    middle = (FOOT[0], FOOT[1] + 0.36)
    if patch > 0:
        frame.lay(mask([lump(middle, 0.6, 21, corners=14)], blur=0.035), (238, 84, 60), 0.62 * patch)
    if shards > 0.02:
        bands = [(CRIMSON, 1, 1, 0, 0.95), (RED, 0.82, 0.66, 0, 1)]
        burst(frame, FOOT, SHARDS, bands, shards, apart=0.1)
    if there > 0:
        shape = fan(tall, wide, split, lean=0.03)
        shape = [(x, y + lift) for x, y in shape]
        frame.lay(mask([shape], grow=0.1, blur=0.04), (255, 52, 56), 0.9 * there)
        frame.lay(mask([shape], grow=0.045, blur=0.012), FLAME, there)
        frame.lay(mask([shape], grow=0.02), ORANGE, there)
        frame.lay(mask([shape]), YELLOW, there)
        frame.lay(mask([scaled(shape, (FOOT[0], FOOT[1] + 0.4 * tall + lift), 0.84)]), PALE, there)
        frame.lay(mask([scaled(shape, (FOOT[0], FOOT[1] + 0.3 * tall + lift), 0.52)], blur=0.03), HOT, 0.85 * there)
    if star > 0.02:
        bands = [((255, 226, 120), 1.08, 1.1, 1.1, 1), (WHITE, 1, 1, 1, 1)]
        burst(frame, FOOT, GLINT, bands, star, core=0.12, seed=5)
    for k, (degrees, speed) in enumerate(((70, 1.0), (112, 0.8), (38, 0.7), (150, 0.6), (95, 1.2), (20, 0.5))):
        out = at(stage, [1.5, 7.5], [0.25, 0.25 + 0.75 * speed])
        long = at(stage, [1.5, 3, 7.5], [0.0, 0.11, 0.0])
        if long > 0.005:
            colour = PALE if k % 2 == 0 else ORANGE
            frame.lay(mask([kite((FOOT[0], FOOT[1] + 0.2), degrees, long, 0.016, start=out)]), colour, 0.95)
    return frame.image(SALMON)


def tracer():
    """The line across its width: Riot's is a strong yellow, pale in the very middle, orange at its edges."""
    height, width = 32, 256
    y = np.abs((np.arange(height) + 0.5) / height * 2 - 1)[:, None] * np.ones((1, width))
    rgb = np.zeros((height, width, 3), np.float32)
    alpha = np.zeros((height, width), np.float32)
    for colour, reach, soft in ((ORANGE, 0.92, 0.2), (YELLOW, 0.62, 0.12), (PALE, 0.26, 0.1)):
        m = np.clip((reach - y) / soft, 0, 1)
        rgb = rgb * (1 - m[..., None]) + np.asarray(colour, np.float32) * m[..., None]
        alpha = alpha * (1 - m) + m
    straight = np.where(alpha[..., None] > 1e-3, rgb / np.maximum(alpha[..., None], 1e-3), np.asarray(ORANGE, np.float32))
    return Image.fromarray(np.dstack([straight, alpha * 255]).round().clip(0, 255).astype(np.uint8), "RGBA")


EFFECTS = {"fx_muzzle": muzzle, "fx_spark": spark, "fx_body": body, "fx_head": head}


def main():
    os.makedirs(OUT, exist_ok=True)
    grounds = {"preview": (196, 124, 62), "preview_dark": (58, 52, 70)}  # Riot's brick wall, and shade
    cell = 192
    previews = {name: Image.new("RGB", (cell * 16, cell * len(EFFECTS) + 60), ground) for name, ground in grounds.items()}
    for row, (name, draw) in enumerate(EFFECTS.items()):
        sheet = Image.new("RGBA", (FRAME * 4, FRAME * 4), (0, 0, 0, 0))
        for index in range(16):
            frame = draw(index)
            sheet.paste(frame, ((index % 4) * FRAME, (index // 4) * FRAME))
            small = frame.resize((cell, cell), Image.LANCZOS)
            for preview in previews.values():
                preview.paste(small, (index * cell, row * cell), small)
        sheet.save(os.path.join(OUT, name + ".png"))
        print("wrote", name)
    line = tracer()
    line.save(os.path.join(OUT, "fx_tracer.png"))
    wide = line.resize((cell * 8, 12), Image.LANCZOS)
    for name, preview in previews.items():
        preview.paste(wide, (40, cell * len(EFFECTS) + 24), wide)
        preview.save(os.path.join(OUT, name + ".png"))
    print("wrote fx_tracer and the previews")


if __name__ == "__main__":
    main()

"""The sky: one big picture painted stroke by stroke, then cut into the six faces of a box.

    python sky.py          # out/sky/sky.png (the whole picture) and out/sky/sky_<face>.png
    python sky.py test     # out/sky/test_<face>.png: labelled faces, to check which way Roblox turns each one

The picture is the whole sphere laid flat: left to right is once round the horizon, bottom to top is from
straight down to straight up. It is the concept's golden-hour sky (reference/sky/sky-clouds.webp): violet
overhead, pink lower down, peach at the horizon, peach clouds with salmon undersides. Below the horizon
it is sand, for wherever the map does not cover the view.
Every stroke is numbers, as for the kit: where, how long, how wide, what angle, what colour.
No noise, no gradients: the change from violet to peach is bands of long ragged strokes laid over each other.
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

import brush

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out", "sky")
W, H = 4096, 2048              # the flat picture
FACE = 1024                    # one face of the box (Roblox's largest texture)
PPD = H / 180.0                # pixels per degree
SEED = 23

# Which way each face of Roblox's sky box looks, and where the right and top edges of its picture point.
# Found in Studio with `python sky.py test` (labelled faces, looked at along every axis): Roblox's "Rt" face
# is on the -X side and "Lf" on +X, and the top and bottom faces lie a quarter turn from the usual layout.
FACES = {
    "Ft": ((0, 0, -1), (1, 0, 0), (0, 1, 0)),
    "Bk": ((0, 0, 1), (-1, 0, 0), (0, 1, 0)),
    "Rt": ((-1, 0, 0), (0, 0, -1), (0, 1, 0)),
    "Lf": ((1, 0, 0), (0, 0, 1), (0, 1, 0)),
    "Up": ((0, 1, 0), (0, 0, -1), (1, 0, 0)),
    "Dn": ((0, -1, 0), (0, 0, -1), (-1, 0, 0)),
}

VIOLET, MAUVE, ROSE = (138, 129, 198), (176, 146, 206), (214, 158, 200)
PINK, BLUSH, PEACH, PALE = (245, 176, 190), (253, 186, 170), (253, 193, 152), (254, 208, 172)
SAND = (250, 178, 132)
CLOUD_SHADE, CLOUD, CLOUD_LIGHT, CLOUD_TOP = (238, 150, 140), (253, 188, 150), (254, 212, 178), (255, 230, 205)
WISP = (250, 190, 176)


def rgb(c):
    return np.array(c, np.float32) / 255.0


def row(elevation):
    return (elevation / 180.0 + 0.5) * H


class Sky:
    def __init__(self):
        self.canvas = np.empty((H, W, 3), np.float32)
        self.canvas[:] = rgb(VIOLET)
        self.canvas[:int(row(-1.0))] = rgb(SAND)
        self.mask = np.ones((H, W), np.float32)
        self.rng = np.random.default_rng(SEED)
        self.count = 0

    def stroke(self, x, y, length, width, angle, color, opacity, round_=0.3, rag=0.2):
        """One stroke; drawn again a full turn to either side so the picture joins up left to right."""
        seed = int(self.rng.integers(1 << 30))
        for shift in (-W, 0, W):
            brush.stroke(self.canvas, self.mask, x + shift, y, length, width, angle, color, opacity,
                         np.random.default_rng(seed), round_=round_, rag=rag)
        self.count += 1

    def band(self, low, high, color, count, lean=0.0):
        rng = self.rng
        for _ in range(count):
            self.stroke(rng.uniform(0, W), row(rng.uniform(low, high)), rng.uniform(25, 70) * PPD, rng.uniform(3, 7) * PPD,
                        math.radians(lean + rng.uniform(-5, 5)), rgb(color), rng.uniform(0.55, 0.9), rag=0.28)

    def texture(self, low, high, count, lean):
        """Strokes one small step lighter or darker than the paint under them."""
        rng = self.rng
        for _ in range(count):
            x, e = rng.uniform(0, W), rng.uniform(low, high)
            under = self.canvas[min(int(row(e)), H - 1), int(x) % W]
            color = under * 0.965 if rng.random() < 0.5 else under + (1.0 - under) * 0.12
            self.stroke(x, row(e), rng.uniform(6, 18) * PPD, rng.uniform(1.0, 3.0) * PPD,
                        math.radians(lean + rng.uniform(-10, 10)), color, rng.uniform(0.35, 0.6))

    def cloud(self, lon, elevation, width):
        """A pile of round dabs with a flat foot: salmon underneath, peach body, pale where the sun catches it."""
        rng = self.rng
        stretch = 1.0 / math.cos(math.radians(elevation))        # the flat picture is stretched sideways higher up
        cx, cy, w = lon / 360.0 * W, row(elevation), width * PPD
        h = 0.42 * w
        puffs = []
        for _ in range(int(rng.integers(40, 70))):
            t = rng.uniform(-1, 1)
            top = (1 - abs(t) ** 1.6) * h * rng.uniform(0.35, 1.0)
            puffs.append((t * w / 2, rng.uniform(0, top), h * rng.uniform(0.14, 0.3) * (1 - 0.4 * abs(t)), top))

        def dab(px, py, r, color):
            self.stroke(cx + px * stretch, cy + py, 2.3 * r * stretch, 2 * r, rng.uniform(-0.5, 0.5), rgb(color),
                        rng.uniform(0.9, 1.0), round_=0.95, rag=0.05)

        for px, py, r, _ in puffs:
            dab(px + 0.15 * r, py - 0.35 * r, r * 1.05, CLOUD_SHADE)
        for px, py, r, _ in puffs:
            dab(px, py, r, CLOUD)
        for px, py, r, top in puffs:
            if py > 0.3 * top:
                dab(px - 0.2 * r, py + 0.3 * r, r * 0.7, CLOUD_LIGHT)
        for px, py, r, top in puffs:
            if py > 0.5 * top and rng.random() < 0.35:
                dab(px - 0.3 * r, py + 0.45 * r, r * 0.4, CLOUD_TOP)

    def paint(self):
        rng = self.rng
        self.band(26, 46, MAUVE, 220)
        self.band(16, 32, ROSE, 240)
        self.band(8, 22, PINK, 260)
        self.band(3, 12, BLUSH, 260)
        self.band(-1, 6, PEACH, 240)
        self.band(-1, 3, PALE, 150)
        for _ in range(320):                                     # the sand below the horizon
            under = rgb(SAND) * rng.uniform(0.96, 1.03)
            self.stroke(rng.uniform(0, W), row(rng.uniform(-70, -1.5)), rng.uniform(15, 50) * PPD, rng.uniform(2, 6) * PPD,
                        math.radians(rng.uniform(-4, 4)), np.clip(under, 0, 1), rng.uniform(0.5, 0.85))
        self.texture(2, 74, 1700, 18)
        for _ in range(40):                                      # long thin streaks of cloud
            e = rng.uniform(15, 55)
            self.stroke(rng.uniform(0, W), row(e), rng.uniform(20, 50) * PPD, rng.uniform(0.8, 1.8) * PPD,
                        math.radians(12 + rng.uniform(-6, 6)), rgb(WISP), rng.uniform(0.5, 0.75), round_=0.6)
        clouds = [(rng.uniform(0, 360), 7 + 31 * rng.random() ** 1.5, rng.uniform(14, 34)) for _ in range(16)]
        clouds += [(rng.uniform(0, 360), rng.uniform(6, 42), rng.uniform(4, 9)) for _ in range(26)]
        for lon, elevation, width in sorted(clouds, key=lambda c: -c[1]):       # nearer the horizon = painted later
            self.cloud(lon, elevation, width)
        return self

    def image(self):
        return np.flipud((np.clip(self.canvas, 0, 1) * 255 + 0.5).astype(np.uint8))


def directions(face):
    forward, right, up = (np.array(v, np.float64) for v in FACES[face])
    a = (np.arange(FACE) + 0.5) / FACE * 2 - 1
    d = forward[None, None, :] + a[None, :, None] * right[None, None, :] - a[:, None, None] * up[None, None, :]
    return d / np.linalg.norm(d, axis=2, keepdims=True)


def cut(picture, face):
    """One face of the box, looked up in the flat picture (top row of `picture` is straight up)."""
    d = directions(face)
    lon = np.arctan2(d[..., 0], -d[..., 2])                      # 0 looks along -Z, a quarter turn on is +X
    lat = np.arcsin(np.clip(d[..., 1], -1, 1))
    x = (lon / (2 * math.pi) + 0.5) * W - 0.5
    y = (0.5 - lat / math.pi) * H - 0.5
    x0, y0 = np.floor(x).astype(int), np.clip(np.floor(y).astype(int), 0, H - 2)
    fx, fy = (x - x0)[..., None], np.clip(y - y0, 0, 1)[..., None]
    p = picture.astype(np.float32)
    top = p[y0, x0 % W] * (1 - fx) + p[y0, (x0 + 1) % W] * fx
    bottom = p[y0 + 1, x0 % W] * (1 - fx) + p[y0 + 1, (x0 + 1) % W] * fx
    return (top * (1 - fy) + bottom * fy + 0.5).astype(np.uint8)


def axis_name(v):
    return next(("+" if s > 0 else "-") + "XYZ"[k] for k, s in enumerate(v) if s)


def test_faces():
    """Each face says its own name and, along every edge, which way that edge points."""
    font = ImageFont.load_default(size=44)
    colours = {"Ft": (200, 80, 80), "Bk": (80, 160, 80), "Rt": (80, 100, 200), "Lf": (200, 170, 60), "Up": (160, 90, 190),
               "Dn": (70, 170, 170)}
    for face, (forward, right, up) in FACES.items():
        im = Image.new("RGB", (256, 256), colours[face])
        draw = ImageDraw.Draw(im)
        draw.text((128, 128), face, font=font, anchor="mm", fill="white")
        draw.text((128, 26), axis_name(up), font=font, anchor="mm", fill="black")
        draw.text((128, 230), axis_name([-c for c in up]), font=font, anchor="mm", fill="black")
        draw.text((218, 128), axis_name(right), font=font, anchor="mm", fill="black")
        draw.text((38, 128), axis_name([-c for c in right]), font=font, anchor="mm", fill="black")
        im.save(os.path.join(OUT, f"test_{face}.png"))


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    if sys.argv[1:] == ["test"]:
        test_faces()
        sys.exit()
    sky = Sky().paint()
    picture = sky.image()
    Image.fromarray(picture).save(os.path.join(OUT, "sky.png"))
    for face in FACES:
        Image.fromarray(cut(picture, face)).save(os.path.join(OUT, f"sky_{face}.png"))
    print(sky.count, "strokes")

"""Draws the shot effects as flipbook sheets: python flipbooks.py   (writes out/fx_*.png and out/preview.png)

Every sheet is drawn to match Valorant frame for frame, from Riot's own material (see REFERENCE.md beside
this file for what each frame of it shows). Nothing of Riot's is copied into the sheets: the shapes are
drawn here, to the reference's shapes, colours, sizes and timing.

The method is the owner's stylized VFX skill: build the effect, take every frame, pack 16 frames 4x4, play
the sheet on a Roblox particle. The skill builds and films in Unreal; there is none here, so the frames are
drawn directly, which also gives a clean cutout without filming on black and on white.

Sheets (1024 x 1024, 16 frames of 256, read left to right, top to bottom):
    fx_muzzle   the flash: a thin-spiked star with a tall upright spike, an orange glow, and a red beam
                across it that outlives the star
    fx_spark    where a shot lands: a small white star, then a grey puff
    fx_body     a hit on a body: a pale core in orange, ringed with crimson blobs
    fx_head     a hit on a head: a pale flame that stands up from the hit, reddens and is eaten away, with a
                white four-pointed glint at its foot
And fx_tracer (256 x 32): the tracer's line, pale in the middle and orange at its edges.
"""
import os

import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
FRAME = 256
SUPER = 2

WHITE = (255, 255, 250)
PALE = (255, 244, 198)
YELLOW = (255, 216, 96)
ORANGE = (255, 142, 40)
RED = (236, 66, 36)
CRIMSON = (188, 26, 44)
SALMON = (255, 132, 100)
PINK = (238, 82, 96)
GREY = (226, 222, 228)


def lattice(rng, size):
    return rng.random((size + 1, size + 1))


def value_noise(x, y, grid):
    n = grid.shape[0] - 1
    xi, yi = np.floor(x).astype(int), np.floor(y).astype(int)
    fx, fy = x - xi, y - yi
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    xi, yi = xi % n, yi % n
    a, b = grid[yi, xi], grid[yi, xi + 1]
    c, d = grid[yi + 1, xi], grid[yi + 1, xi + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(x, y, grids):
    total, weight, scale = 0.0, 0.0, 1.0
    for index, grid in enumerate(grids):
        total += value_noise(x * scale + index * 7.3, y * scale + index * 3.1, grid) / scale
        weight += 1 / scale
        scale *= 2
    return total / weight


def mix(a, b, t):
    return tuple(a[i] + (b[i] - a[i]) * t for i in range(3))


class Canvas:
    """One frame: coordinates from -1 to 1, y up. Layers of colour are laid over one another, soft-edged."""

    def __init__(self, width=FRAME, height=FRAME):
        w, h = width * SUPER, height * SUPER
        xs = (np.arange(w) + 0.5) / w * 2 - 1
        ys = 1 - (np.arange(h) + 0.5) / h * 2
        self.x, self.y = np.meshgrid(xs * (width / height), ys)
        self.pixel = 2 / h
        self.rgb = np.zeros((h, w, 3))  # premultiplied
        self.alpha = np.zeros((h, w))
        self.size = (width, height)

    def polar(self, ox=0.0, oy=0.0):
        return np.hypot(self.x - ox, self.y - oy), np.arctan2(self.y - oy, self.x - ox)

    def lay(self, colour, alpha):
        alpha = np.clip(alpha, 0, 1)
        self.rgb = np.asarray(colour)[None, None, :] * alpha[..., None] + self.rgb * (1 - alpha[..., None])
        self.alpha = alpha + self.alpha * (1 - alpha)

    def edge(self, field, soft=1.5):
        """1 inside a shape (field > 0), 0 outside, over `soft` pixels."""
        return np.clip(field / (self.pixel * soft) + 0.5, 0, 1)

    def fill(self, field, stops, opacity=1.0):
        """Fills a shape with colours by how deep inside it a point is: stops is [(depth, colour)], rising."""
        inside = self.edge(field) * opacity
        for index, (depth, colour) in enumerate(stops):
            if index == 0:
                self.lay(colour, inside)
            else:
                before = stops[index - 1][0]
                self.lay(colour, inside * np.clip((field - before) / max(depth - before, 1e-6), 0, 1))

    def glow(self, colour, distance, reach, strength):
        """A soft light that is `strength` at distance 0 and gone by about twice `reach`."""
        self.lay(colour, strength * np.exp(-((np.maximum(distance, 0) / reach) ** 2)))

    def image(self):
        w, h = self.size
        alpha = self.alpha.reshape(h, SUPER, w, SUPER).mean(axis=(1, 3))
        rgb = self.rgb.reshape(h, SUPER, w, SUPER, 3).mean(axis=(1, 3))
        straight = np.where(alpha[..., None] > 1e-4, rgb / np.maximum(alpha[..., None], 1e-4), ORANGE)
        out = np.dstack([straight, alpha * 255]).round().clip(0, 255).astype(np.uint8)
        return Image.fromarray(out, "RGBA")


def star(r, a, angles, lengths, widths, body):
    """How far inside a star a point is: a round body with a pointed spike at each angle."""
    reach = np.full(r.shape, body)
    for angle, length, width in zip(angles, lengths, widths):
        off = np.abs((a - angle + np.pi) % (2 * np.pi) - np.pi)
        reach = np.maximum(reach, body + length * np.clip(1 - off / width, 0, 1) ** 1.5)
    return reach - r


def tongue(c, ox, oy, angle, length, width, belly=0.3):
    """How far inside a flame's tongue a point is: it starts at a point, swells, and ends in a point."""
    u = (c.x - ox) * np.cos(angle) + (c.y - oy) * np.sin(angle)
    v = np.abs(-(c.x - ox) * np.sin(angle) + (c.y - oy) * np.cos(angle))
    s = np.clip(u / length, 0, 1)
    profile = np.where(s < belly, (s / belly) ** 0.7, ((1 - s) / (1 - belly)) ** 1.25)
    return np.where((u >= 0) & (u <= length), width * profile - v, -1.0)


def ease(t):
    return 1 - (1 - t) ** 3


def muzzle(frame):
    rng = np.random.default_rng(7)
    grids = [lattice(rng, 8) for _ in range(3)]
    c = Canvas()
    r, a = c.polar()
    t = frame / 15
    # Reference: the star is whole on the first frame; on the second the glow is at its widest and a red beam
    # lies across the muzzle; on the third the star has shrunk and the beam is shorter; then only a few orange
    # points are left. Sixteen frames here cover those four.
    stage = frame / 4.0  # 0..4 through the reference's frames
    size = np.interp(stage, [0, 0.5, 1.5, 2.5, 3.5, 4], [0.8, 1.0, 0.95, 0.55, 0.25, 0.0])
    halo = np.interp(stage, [0, 1, 1.6, 2.6, 3.4, 4], [0.45, 0.8, 0.85, 0.5, 0.12, 0.0])
    beam = np.interp(stage, [0, 0.8, 1.5, 2.6, 3.5, 4], [0.25, 0.9, 0.95, 0.6, 0.2, 0.0])
    wobble = fbm(c.x * 4 + 1.0, c.y * 4 + stage, grids) - 0.5
    # the glow
    c.glow(RED, r, 0.5 * (0.6 + 0.4 * halo), 0.4 * halo)
    c.glow(ORANGE, r, 0.3 * (0.6 + 0.4 * halo), 0.95 * halo)
    c.glow(YELLOW, r, 0.14 * (0.6 + 0.4 * halo), 0.9 * halo)
    # the beam: thin, long, level, redder than the rest
    if beam > 0.02:
        length, thick = 0.92 * beam, 0.035 * (0.5 + 0.5 * beam)
        # longer to one side: on the reference it runs out to the left of the muzzle
        reach = np.where(c.x < 0, length, length * 0.45)
        level = thick * np.clip(1 - np.abs(c.x) / reach, 0, 1) ** 0.8 - np.abs(c.y)
        c.glow(RED, -level, 0.035, 0.5 * beam)
        c.fill(level, [(0, RED), (0.012, ORANGE), (0.024, YELLOW)])
    # the star: thin spikes of uneven length, the upright one much the tallest
    if size > 0.02:
        angles = np.array([1.5, -1.78, 0.78, 2.28, -0.5, 3.45, 2.9])
        lengths = np.array([0.64, 0.34, 0.26, 0.44, 0.22, 0.5, 0.18]) * size
        widths = np.array([0.2, 0.26, 0.34, 0.26, 0.36, 0.22, 0.4])
        field = star(r, a, angles, lengths, widths, 0.15 * size) + wobble * 0.05
        c.glow(ORANGE, -field, 0.05, 0.75)
        c.fill(field, [(0, RED), (0.012, ORANGE), (0.035, YELLOW), (0.075, PALE), (0.16, WHITE)])
    return c.image()


def spark(frame):
    rng = np.random.default_rng(13)
    grids = [lattice(rng, 8) for _ in range(3)]
    c = Canvas()
    r, a = c.polar()
    t = frame / 15
    lump = fbm(c.x * 3.5 + 2.0, c.y * 3.5 - t * 2.0, grids) - 0.5
    # the puff: grey, half see-through, a ring more than a ball, growing, then eaten away
    if frame >= 3:
        grow = ease((frame - 3) / 12)
        radius = 0.2 + 0.4 * grow
        puff = 0.16 * (1 - 0.3 * grow) - np.abs(r - radius * 0.75) + lump * 0.2
        puff = puff - np.clip(lump + 0.5 - (0.95 - 0.8 * grow), 0, 1) * 0.8
        c.lay(GREY, c.edge(puff, 6) * 0.5 * (1 - grow) ** 0.6)
    # the star: white, six thin spikes, there from the first frame and smaller each frame after the third
    size = np.interp(frame, [0, 1, 3, 9, 12], [0.7, 1.0, 0.9, 0.4, 0.0])
    if size > 0.02:
        angles = np.array([0.4, 1.5, 2.6, 3.7, 4.75, 5.8])
        lengths = np.array([0.34, 0.26, 0.3, 0.28, 0.22, 0.3]) * size
        field = star(r, a, angles, lengths, np.full(6, 0.2), 0.07 * size)
        c.glow(PALE, -field, 0.04, 0.45)
        c.fill(field, [(0, PALE), (0.015, WHITE)])
    return c.image()


def body(frame):
    rng = np.random.default_rng(29)
    grids = [lattice(rng, 8) for _ in range(3)]
    c = Canvas()
    r, a = c.polar()
    t = frame / 15
    lump = fbm(c.x * 3.5 + 5.0, c.y * 3.5 + t * 1.5, grids) - 0.5
    count = 7
    angles = np.linspace(0, 2 * np.pi, count, endpoint=False) + rng.uniform(-0.3, 0.3, count)
    sizes = rng.uniform(0.09, 0.15, count)
    out = np.interp(frame, [0, 2, 6, 15], [0.2, 0.36, 0.44, 0.62])
    live = np.interp(frame, [0, 2, 7, 15], [0.6, 1.0, 0.9, 0.0])
    c.glow(RED, r, 0.34, 0.4 * live)
    # crimson blobs round the rim, drifting out and shrinking
    for angle, size in zip(angles, sizes):
        ox, oy = np.cos(angle) * out, np.sin(angle) * out
        blob = size * (0.35 + 0.65 * live) - np.hypot(c.x - ox, c.y - oy) + lump * 0.05
        c.fill(blob, [(0, (140, 16, 38)), (0.03, CRIMSON), (0.08, RED)])
    # the burst: orange with a pale middle, whole for the first frames and then cut
    burst = np.interp(frame, [0, 1, 5, 7, 9], [0.6, 1.0, 1.0, 0.5, 0.0])
    if burst > 0.02:
        spikes = np.linspace(0, 2 * np.pi, 9, endpoint=False) + 0.2
        field = star(r, a, spikes, np.full(9, 0.1) * burst, np.full(9, 0.3), 0.27 * burst) + lump * 0.05
        c.fill(field, [(0, RED), (0.02, ORANGE), (0.07, YELLOW), (0.14, PALE)])
    return c.image()


FOOT = -0.8  # where the hit is, in a head sheet's frame: the flame stands on it


def head(frame):
    rng = np.random.default_rng(41)
    grids = [lattice(rng, 8) for _ in range(3)]
    holes = [lattice(rng, 8) for _ in range(3)]
    c = Canvas()
    t = frame / 15
    # Reference, eight frames: the flame is whole at once, pale with an orange edge and a red glow; it grows
    # a little, then stretches upward and turns orange, then salmon, while holes eat it into a hooked wisp;
    # a white four-pointed glint sits at its foot from the third frame to the sixth.
    stage = frame / 2.0  # 0..7.5 through the reference's frames
    tall = np.interp(stage, [0, 1, 3, 5, 7.5], [1.15, 1.3, 1.55, 1.68, 1.7])
    wide = np.interp(stage, [0, 1, 3, 5, 7.5], [0.25, 0.28, 0.23, 0.16, 0.08])
    eaten = np.interp(stage, [0, 2.5, 4, 6, 7.5], [0.0, 0.0, 0.35, 0.75, 1.0])
    cool = np.interp(stage, [0, 2, 3.5, 5, 7.5], [0.0, 0.0, 0.5, 0.85, 1.0])
    lump = fbm(c.x * 3.0 + 1.0, c.y * 3.0 - stage * 0.5, grids) - 0.5
    hole = fbm(c.x * 3.6 + 4.0, c.y * 2.4 - stage * 0.6 + 2.0, holes)
    up = np.pi / 2
    field = tongue(c, 0, FOOT, up, tall, wide, 0.5)
    field = np.maximum(field, tongue(c, -0.05, FOOT + 0.28, up + 0.44, tall * 0.5, wide * 0.6, 0.45))
    field = np.maximum(field, tongue(c, 0.05, FOOT + 0.24, up - 0.48, tall * 0.46, wide * 0.6, 0.45))
    field = field + lump * (0.05 + 0.1 * eaten)
    field = field - np.clip(hole - (0.78 - 0.62 * eaten), 0, 1) * 1.5
    rim = mix(ORANGE, PINK, cool)
    middle = mix(YELLOW, SALMON, cool)
    core = mix(PALE, SALMON, cool)
    c.glow(mix(RED, PINK, cool), -field, 0.1, 0.8 * (1 - 0.5 * eaten))
    c.fill(field, [(0, mix(RED, PINK, cool)), (0.012, rim), (0.03, middle), (0.07, core), (0.22, mix(WHITE, SALMON, cool))])
    # the glint at the foot
    glint = np.interp(stage, [1.5, 2.2, 5, 6], [0.0, 1.0, 1.0, 0.0])
    if glint > 0.02:
        r, a = c.polar(0, FOOT + 0.04)
        angles = np.array([0.785, 2.356, 3.927, 5.498])
        field = star(r, a, angles, np.full(4, 0.2) * glint, np.full(4, 0.16), 0.035 * glint)
        c.glow(PALE, -field, 0.03, 0.5)
        c.fill(field, [(0, PALE), (0.01, WHITE)])
    return c.image()


def tracer():
    c = Canvas(256, 32)
    across = np.abs(c.y)
    c.lay(ORANGE, np.clip(1 - across / 0.95, 0, 1) ** 1.5 * 0.9)
    c.lay(YELLOW, np.clip(1 - across / 0.5, 0, 1) ** 1.2)
    c.lay(PALE, np.clip(1 - across / 0.22, 0, 1))
    return c.image()


EFFECTS = {"fx_muzzle": muzzle, "fx_spark": spark, "fx_body": body, "fx_head": head}


def main():
    os.makedirs(OUT, exist_ok=True)
    wall = (196, 124, 62)  # the brick wall behind the reference frames
    cell = 160
    preview = Image.new("RGB", (cell * 16, cell * len(EFFECTS) + 60), wall)
    for row, (name, draw) in enumerate(EFFECTS.items()):
        sheet = Image.new("RGBA", (FRAME * 4, FRAME * 4), (0, 0, 0, 0))
        for index in range(16):
            frame = draw(index)
            sheet.paste(frame, ((index % 4) * FRAME, (index // 4) * FRAME))
            small = frame.resize((cell, cell), Image.LANCZOS)
            preview.paste(small, (index * cell, row * cell), small)
        sheet.save(os.path.join(OUT, name + ".png"))
        print("wrote", name)
    line = tracer()
    line.save(os.path.join(OUT, "fx_tracer.png"))
    wide = line.resize((cell * 6, 14), Image.LANCZOS)
    preview.paste(wide, (40, cell * len(EFFECTS) + 22), wide)
    preview.save(os.path.join(OUT, "preview.png"))
    print("wrote fx_tracer and the preview")


if __name__ == "__main__":
    main()

"""Clay pots: a tall jar with two handles, a round jar with a turquoise glaze, and a narrow-necked vase.
Each is a profile turned on a wheel; the patterns are painted lines, the glaze is a second thin shell."""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils

SEGMENTS = 14
CUT = {"cut": True}


def _along(profile, index):
    """Distance along a profile up to one of its points (what p.mark wants on a turned surface)."""
    return sum(math.hypot(b[0] - a[0], b[1] - a[1]) for a, b in zip(profile[:index], profile[1:index + 1]))


def _zigzag(p, pid, low, high, teeth, tone=4):
    """A zigzag round the pot between two heights along the profile, with a line above and below it."""
    points = [(k / (2 * teeth), high if k % 2 else low) for k in range(2 * teeth + 1)]
    p.mark(pid, "lathe", points, tone=tone, width=0.035)
    for along in (low - 0.07, high + 0.07):
        p.mark(pid, "lathe", [(k / SEGMENTS, along) for k in range(SEGMENTS + 1)], tone=tone, width=0.03)


def tall(p):
    profile = [(0.45, 0.0), (0.62, 0.12), (1.0, 0.9), (1.12, 1.6), (0.98, 2.2), (0.62, 2.65), (0.52, 2.85),
               (0.66, 3.1), (0.7, 3.2), (0.56, 3.2), (0.44, 2.95)]
    body = p.lathe(profile, SEGMENTS, "clay", grain=None, smooth=True, extra=CUT)
    _zigzag(p, body, _along(profile, 3) + 0.05, _along(profile, 4) - 0.05, 8)
    handle = [(0.5, 2.92), (0.95, 2.97), (1.3, 2.72), (1.36, 2.3), (1.08, 1.82), (0.9, 1.95), (1.15, 2.3),
              (1.11, 2.6), (0.9, 2.76), (0.5, 2.72)]
    for x_dir in ((1, 0, 0), (-1, 0, 0)):
        p.extrude(handle, 0.1, "clay", bevel=0.035, group="handle", extra=CUT,
                  frame=frame_axes((0, 0, 0), x_dir, (0, x_dir[0], 0)))


def round_(p):
    profile = [(0.5, 0.0), (0.75, 0.1), (1.15, 0.7), (1.2, 1.15), (1.0, 1.65), (0.72, 1.9), (0.8, 2.08),
               (0.66, 2.08), (0.6, 1.9)]
    # the glazed lower half and the bare clay above it are two solids that meet on a level plane
    p.lathe(profile[:3] + [(1.19, 1.0)], SEGMENTS, "band", grain=None, smooth=True, group="glaze", extra=CUT)
    p.lathe([(1.19, 1.0)] + profile[3:], SEGMENTS, "clay", grain=None, smooth=True, extra=CUT)


def vase(p):
    profile = [(0.35, 0.0), (0.5, 0.1), (0.8, 0.6), (0.82, 0.95), (0.6, 1.45), (0.3, 1.8), (0.27, 2.1), (0.4, 2.3),
               (0.3, 2.3), (0.2, 2.1)]
    # clay foot, glazed belly, clay neck: three solids that meet on level planes
    glaze = [(0.52, 0.13), (0.8, 0.6), (0.82, 0.95), (0.67, 1.3)]
    p.lathe(profile[:2] + glaze[:1], SEGMENTS, "clay", grain=None, smooth=True, group="foot", extra=CUT)
    shell = p.lathe(glaze, SEGMENTS, "band", grain=None, smooth=True, group="glaze", extra=CUT)
    p.lathe(glaze[-1:] + profile[4:], SEGMENTS, "clay", grain=None, smooth=True, extra=CUT)
    low, high = _along(glaze, 1) + 0.02, _along(glaze, 2) - 0.02            # a row of diamonds round the belly
    for k in range(7):
        a, b = k / 7, (k + 1) / 7
        p.mark(shell, "lathe", [(a, (low + high) / 2), ((a + b) / 2, high), (b, (low + high) / 2), ((a + b) / 2, low)],
               tone=5, width=0.03, closed=True)

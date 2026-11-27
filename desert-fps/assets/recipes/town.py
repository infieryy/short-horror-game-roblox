"""Pieces that make the town a town: its wall, a tower, the gate, house doors, and the working gear of
its trades (a potter's kiln and drying rack, a weaver's loom, a carter's cart, a stack of crates)."""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix

from . import sacks as sack_pile
from .wall2 import _arc

HALF = C.CELL / 2
CUT = {"cut": True}
W = C.KIT["townwall"]


def _battlements(p, x0, x1, y0, y1, z, count, name="merlon"):
    """Square merlons in a row along X, standing on height z."""
    step = (x1 - x0) / count
    for i in range(count):
        x = x0 + (i + 0.5) * step
        p.box((x - W["merlon_w"] / 2, y0, z), (x + W["merlon_w"] / 2, y1, z + W["merlon_h"]), "plaster", bevel=0.07,
              group=f"{name}{i}", extra=CUT)


def wall(p):
    """The town wall, one grid cell long and two stories high. The front (-Y) faces the town."""
    t, top = W["t"] / 2, W["h"] - W["cap_h"]
    body = p.box((-HALF, -t, 0), (HALF, t, top), "plaster", group="wall", band=True, extra=CUT)
    p.box((-HALF, -t - W["cap_out"], top), (HALF, t + W["cap_out"], W["h"]), "stone", group="cap", extra={**CUT, "tone": 2})
    _battlements(p, -HALF, HALF, -t, t, W["h"], 3)
    course = p.box((-HALF, -t - 0.2, W["course_z"]), (HALF, -t, W["course_z"] + 0.6), "stone", group="course",
                   extra={**CUT, "tone": 3})
    teeth, m = 8, 0.13
    p.mark(course, "-y", [(-HALF + k * C.CELL / (2 * teeth), -t - 0.2, W["course_z"] + (m if k % 2 == 0 else 0.6 - m))
                          for k in range(2 * teeth + 1)], width=0.1, family="band")
    for face, y in (("-y", -t), ("+y", t)):                             # an arrow slit, painted
        p.mark(body, face, [(-0.22, y, 18.0), (0.22, y, 18.0), (0.22, y, 20.6), (-0.22, y, 20.6)], tone=-6, width=0.16,
               closed=True)
    p.seams = [(0, -HALF), (0, HALF), (2, 0.0)]


def tower(p):
    """A square tower of the town wall: taller than the wall, battlements all round."""
    a, top = W["tower_half"], W["tower_h"] - W["cap_h"]
    body = p.box((-a, -a, 0), (a, a, top), "plaster", group="wall", band=True, extra=CUT)
    p.box((-a - 0.3, -a - 0.3, top), (a + 0.3, a + 0.3, W["tower_h"]), "stone", group="cap", extra={**CUT, "tone": 2})
    z = W["tower_h"]
    _battlements(p, -a - 0.3, a + 0.3, -a - 0.3, -a + 1.0, z, 3, "front")
    _battlements(p, -a - 0.3, a + 0.3, a - 1.0, a + 0.3, z, 3, "rear")
    for sx, name in ((-1, "left"), (1, "right")):                       # the two sides, between the corner merlons
        xa, xb = sorted((sx * (a + 0.3), sx * (a - 1.0)))
        p.box((xa, -W["merlon_w"] / 2, z), (xb, W["merlon_w"] / 2, z + W["merlon_h"]), "plaster", bevel=0.07,
              group=f"{name}0", extra=CUT)
    for face, sx, sy in (("-y", 0, -1), ("+y", 0, 1), ("-x", -1, 0), ("+x", 1, 0)):
        for z0 in (9.0, 21.0):
            pts = [(-0.22, z0), (0.22, z0), (0.22, z0 + 2.6), (-0.22, z0 + 2.6)]
            p.mark(body, face, [((u if sy else sx * a), (sy * a if sy else u), w) for u, w in pts], tone=-6, width=0.16,
                   closed=True)
    p.seams = [(2, 0.0)]


def gate(p):
    """The town gate: the wall with a great arch in it, shut by a pair of plank doors. One grid cell."""
    t, top = W["t"] / 2, W["h"] - W["cap_h"]
    r, spring = W["gate_w"] / 2, W["gate_spring"]
    R = r + 0.7
    profile = [(-HALF, 0), (-HALF, top), (HALF, top), (HALF, 0), (R, 0)] + _arc(R, spring, 0, 180, 12) + [(-R, 0)]
    p.extrude(profile, t, "plaster", group="wall", band=True, extra=CUT)
    frame = [(R, 0)] + _arc(R, spring, 0, 180, 12) + [(-R, 0), (-r, 0)] + _arc(r, spring, 180, 0, 12) + [(r, 0)]
    arch = p.extrude(frame, t + 0.18, "stone", group="arch", band=True, extra={**CUT, "tone": 3})
    for y, facet in ((-t - 0.18, "-y"), (t + 0.18, "+y")):
        for k in range(1, 13):
            a = math.radians(180 * k / 13)
            p.mark(arch, facet, [(r * math.cos(a), y, spring + r * math.sin(a)), (R * math.cos(a), y, spring + R * math.sin(a))],
                   tone=-3, width=0.06)
    doors = p.extrude([(-r, 0)] + _arc(r, spring, 180, 0, 12) + [(r, 0)], t - 0.5, "wood", group="doors", grain="z", extra=CUT)
    for y, facet in ((-(t - 0.5), "-y"), (t - 0.5, "+y")):
        p.mark(doors, facet, [(0, y, 0.05), (0, y, spring + r - 0.05)], tone=-5, width=0.1)
        for k in range(1, 8):
            x = -r + k * 2 * r / 8
            if k != 4:
                p.mark(doors, facet, [(x, y, 0.1), (x, y, spring + r * 0.6)], tone=-3, width=0.05)
    for z in (2.0, 6.5):                                                # iron straps, proud of both faces
        p.box((-r + 0.15, -(t - 0.5) - 0.06, z), (r - 0.15, t - 0.5 + 0.06, z + 0.5), "iron", group=f"strap{z}")
    p.box((-HALF, -t - W["cap_out"], top), (HALF, t + W["cap_out"], W["h"]), "stone", group="cap", extra={**CUT, "tone": 2})
    _battlements(p, -HALF, HALF, -t, t, W["h"], 3)
    p.seams = [(0, -HALF), (0, HALF), (2, 0.0)]


def door(p, paint="wood"):
    """A house door: an arched leaf of planks that fills the doorway of a dressed wall, shut. Painted or bare.
    It stands on the wall line like the wall piece it belongs to."""
    o = C.KIT["wall2"]["openings"]["door"]
    r, spring, half = o["w"] / 2 - 0.02, o["spring"], 0.14
    leaf = p.extrude([(-r, 0)] + _arc(r, spring, 180, 0) + [(r, 0)], half, paint, group="leaf",
                     grain="z" if paint == "wood" else None, extra=CUT)
    for y, facet in ((-half, "-y"), (half, "+y")):
        for k in range(1, 8):
            x = -r + k * 2 * r / 8
            p.mark(leaf, facet, [(x, y, 0.08), (x, y, spring + math.sqrt(max(r * r - x * x, 0)) - 0.08)], tone=-3, width=0.05)
    for z in (1.3, 4.6):
        p.box((-r + 0.2, -half - 0.05, z), (r - 0.2, half + 0.05, z + 0.34), "iron", group=f"strap{z}")
    p.box((r - 0.75, -half - 0.16, 3.2), (r - 0.45, -half - 0.05, 3.5), "brass", group="knob", detail=True)


def crates(p):
    """Three crates, two with a third on top: cover a head taller than a player."""
    spots = [((-1.6, 0.1, 0.0), 4), ((1.55, -0.15, 0.0), -3), ((0.1, 0.0, 3.0), 14)]
    for i, ((x, y, z), turn) in enumerate(spots):
        frame = Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(turn), 4, "Z")
        box = p.box((-1.5, -1.5, 0.0), (1.5, 1.5, 3.0), "wood", bevel=0.04, grain="z", group=f"crate{i}", frame=frame,
                    extra={**CUT, "tone": i - 1})
        for facet, flat in (("-y", lambda u, w: (u, -1.5, w)), ("+y", lambda u, w: (u, 1.5, w)),
                            ("-x", lambda u, w: (-1.5, u, w)), ("+x", lambda u, w: (1.5, u, w))):
            rim = [(-1.22, 0.28), (1.22, 0.28), (1.22, 2.72), (-1.22, 2.72)]
            p.mark(box, facet, [frame @ Matrix.Translation(flat(u, w)).translation for u, w in rim], tone=-3, width=0.11,
                   closed=True)
            p.mark(box, facet, [frame @ Matrix.Translation(flat(u, w)).translation for u, w in ((-1.2, 0.3), (1.2, 2.7))],
                   tone=-3, width=0.11)


def cart(p):
    """A carter's two-wheeled cart, loaded with sacks under a canvas tilt. As long as a grid cell is wide."""
    bed_z = 1.9
    p.box((-2.6, -1.3, bed_z), (2.6, 1.3, bed_z + 0.25), "wood", grain="x", group="bed", extra=CUT)
    for sy in (-1, 1):
        ya, yb = sorted((sy * 1.3, sy * 1.42))
        p.box((-2.6, ya, bed_z + 0.25), (2.6, yb, bed_z + 1.1), "wood", grain="x", group=f"side{sy}")
        wheel = frame_axes((-0.4, sy * 1.62, 1.35), (1, 0, 0), (0, 0, 1))     # the wheel's axle runs along Y
        disc = p.lathe([(0.22, -0.1), (1.35, -0.1), (1.35, 0.1), (0.22, 0.1)], 12, "darkwood", closed=True, grain=None,
                       group=f"wheel{sy}", frame=wheel)
        p.lathe([(0.3, -0.2), (0.3, 0.2)], 8, "iron", grain=None, group=f"hub{sy}", frame=wheel)
        del disc
    p.box((-2.6, -1.3, bed_z + 0.25), (-2.48, 1.3, bed_z + 1.1), "wood", grain="y", group="tail")
    for sy in (-1, 1):                                                  # the shafts, running forward and down a little
        p.box((0.0, -0.09, -0.09), (3.4, 0.09, 0.09), "darkwood", grain="x", group=f"shaft{sy}",
              frame=frame_axes((2.5, sy * 1.0, bed_z + 0.1), (1, 0, -0.14), (0, 1, 0)))
    p.box((5.6, -1.1, 1.36), (5.86, 1.1, 1.5), "darkwood", grain="y", group="yoke")
    for i, (x, y, layer, turn) in enumerate(((-1.3, -0.1, 0, 90), (0.7, 0.0, 0, 86), (-0.4, 0.0, 1, 4))):
        frame = (Matrix.Translation((x, y, bed_z + 0.25 + 0.5 + 0.8 * layer)) @ Matrix.Rotation(math.radians(turn), 4, "Z"))
        scale = Matrix.Diagonal((0.82, 0.82, 0.9, 1.0))
        sack_pile._sack(p, frame @ scale, i - 1, p.lod)
    # the tilt: canvas over three hoops, open at both ends
    hoop_r, z0 = 1.42, bed_z + 1.1
    outer = [(hoop_r * math.cos(math.radians(a)), z0 + 3.3 * math.sin(math.radians(a))) for a in range(0, 181, 20)]
    inner = [(1.34 * math.cos(math.radians(a)), z0 + 3.22 * math.sin(math.radians(a))) for a in range(180, -1, -20)]
    p.extrude(outer + inner, 1.9, "canvas", group="tilt", frame=frame_axes((-0.7, 0, 0), (0, 1, 0), (-1, 0, 0)))


def kiln(p):
    """A potter's kiln: a beehive of mud brick with the fire showing in its mouth and a short chimney."""
    body = p.lathe([(3.0, 0.0), (3.05, 1.2), (2.9, 3.4), (2.35, 5.4), (1.4, 6.7), (0.75, 7.1)], 14, "adobe", grain=None,
                   group="dome", smooth=True, extra=CUT)
    for along in (1.2, 2.4, 3.6, 4.9, 6.2):
        p.mark(body, "lathe", [(k / 14, along) for k in range(15)], tone=-2, width=0.05)
    p.lathe([(0.75, 7.05), (0.7, 8.3), (0.5, 8.3), (0.5, 7.05)], 8, "adobe", closed=True, grain=None, group="chimney",
            extra={"tone": -2})
    # the mouth: a stone arch standing out of the dome, the fire glowing inside it
    r, spring = 0.75, 1.3
    arch = [(r + 0.4, 0)] + _arc(r + 0.4, spring, 0, 180, 8) + [(-r - 0.4, 0), (-r, 0)] + _arc(r, spring, 180, 0, 8) + [(r, 0)]
    mouth = frame_axes((0, -2.95, 0.04), (1, 0, 0), (0, 1, 0))
    p.extrude(arch, 0.45, "stone", group="mouth", frame=mouth, extra={"tone": 2})
    p.extrude([(-r, 0)] + _arc(r, spring, 180, 0, 8) + [(r, 0)], 0.3, "glow", group="fire", frame=mouth,
              extra={"chunk": "fire"})
    p.box((-1.5, -4.3, 0.0), (1.5, -3.45, 0.25), "stone", bevel=0.04, group="hearth")


def pot_rack(p):
    """A potter's drying rack: three boards on four posts, crowded with pots. One grid cell wide, taller than a player."""
    for sx in (-2.9, 2.9):
        for sy in (-0.7, 0.7):
            p.box((sx - 0.14, sy - 0.14, 0), (sx + 0.14, sy + 0.14, 6.6), "darkwood", grain="z", group="posts")
    jar = [(0.2, 0.0), (0.34, 0.16), (0.36, 0.5), (0.22, 0.7), (0.26, 0.8)]
    bowl = [(0.18, 0.0), (0.38, 0.22), (0.4, 0.33), (0.33, 0.29)]
    tall = [(0.2, 0.0), (0.3, 0.25), (0.3, 0.7), (0.16, 0.95), (0.2, 1.08)]
    n = 0
    for level, z in enumerate((0.9, 2.9, 4.9)):
        p.box((-3.1, -0.9, z), (3.1, 0.9, z + 0.16), "wood", grain="x", group=f"board{level}", extra=CUT)
        for i in range(5):
            x = -2.4 + i * 1.2 + (0.15 if level % 2 else -0.1)
            profile, mat = ((jar, "clay"), (tall, "clay"), (bowl, "band"), (jar, "clay"), (tall, "band"))[(i + level * 2) % 5]
            scale = 1.5 if profile is not tall else 1.4
            p.lathe([(r * scale, w * scale) for r, w in profile], 8, mat, grain=None, group=f"pot{n}", smooth=True,
                    frame=Matrix.Translation((x, 0.25 if i % 2 else -0.2, z + 0.16)), extra={"tone": n % 3 - 1})
            n += 1


def loom(p):
    """A weaver's upright loom with a half-finished cloth on it, and the weaver's bench."""
    for sx in (-1, 1):
        p.box((sx * 2.7 - 0.2, -0.2, 0.3), (sx * 2.7 + 0.2, 0.2, 7.0), "darkwood", bevel=0.03, grain="z", group=f"post{sx}", extra=CUT)
        p.box((sx * 2.7 - 0.22, -1.0, 0), (sx * 2.7 + 0.22, 1.0, 0.3), "wood", grain="y", group=f"foot{sx}")
    for z, name in ((6.5, "top"), (0.9, "cloth_beam")):
        p.lathe([(0.2, 0.0), (0.2, 5.9)], 8, "wood", grain="z", group=name, frame=frame_axes((-2.95, 0, z), (0, 1, 0), (0, 0, 1)))
    # the warp, and the cloth woven so far in three bands
    p.box((-2.4, -0.03, 3.6), (2.4, 0.03, 6.4), "canvas", group="warp")
    for i, (z0, z1, mat) in enumerate(((1.0, 1.9, "redcloth"), (1.9, 2.7, "saffron"), (2.7, 3.6, "indigo"))):
        p.box((-2.4, -0.06, z0), (2.4, 0.06, z1), mat, group=f"cloth{i}")
    p.box((-1.6, -2.0, 1.25), (1.6, -1.2, 1.45), "wood", bevel=0.03, grain="x", group="bench")
    for sx in (-1.3, 1.3):
        p.box((sx - 0.1, -1.9, 0), (sx + 0.1, -1.3, 1.25), "darkwood", grain="z", group="bench_legs")

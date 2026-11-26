"""Assault rifle. Proportions follow a real wooden-furniture, curved-magazine service rifle
(about 880 mm long), thickened a little so it reads on screen, then painted in the game's style.

Every shape below is a side-view outline in millimetres: x runs from the back of the receiver
toward the muzzle, z is height above the bore. The barrel points along +X; the piece origin is
the top of the pistol grip. Magazine, bolt and trigger are separate parts so they can be animated.
"""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix

K = C.KIT["rifle"]
S = K["length"] / 880.0                  # studs per millimetre
ORIGIN = (55.0, -45.0)                   # mm: top of the pistol grip


def pt(x, z):
    return ((x - ORIGIN[0]) * S, (z - ORIGIN[1]) * S)


def outline(points):
    return [pt(x, z) for x, z in points]


def half(width_mm):
    """Half thickness in studs for a real width in millimetres."""
    return width_mm * S * K["chunky"] / 2


def along_barrel(x, z, y=0.0):
    """Frame for lathed parts: local Z points toward the muzzle."""
    px, pz = pt(x, z)
    return frame_axes((px, y, pz), (0, 1, 0), (0, 0, 1))


def side(y):
    return Matrix.Translation((0, y, 0))


def build(p):
    steel, wood = "gunmetal", "wood"
    mm = S

    # receiver, dust cover, sights
    p.extrude(outline([(0, 12), (0, -45), (258, -45), (266, -30), (266, 12)]), half(33), steel, bevel=2 * mm, grain="x")
    p.extrude(outline([(12, 12), (12, 24), (22, 33), (232, 33), (246, 22), (246, 12)]), half(30), steel,
              bevel=6 * mm, segments=2, grain="x", extra={"tone": 1})
    p.extrude(outline([(248, 12), (248, 44), (262, 48), (304, 42), (304, 12)]), half(15), steel, bevel=1.5 * mm, grain="x")

    # stock, brass butt plate, pistol grip
    p.extrude(outline([(2, 6), (2, -40), (-40, -50), (-150, -92), (-238, -122), (-246, -118), (-246, -22),
                       (-150, -8), (-50, 4)]), half(30), wood, bevel=7 * mm, segments=2, grain="x", extra={"tone": -1})
    p.extrude(outline([(-244, -19), (-244, -121), (-254, -121), (-254, -19)]), half(31), "brass", bevel=1.5 * mm)
    p.extrude(outline([(34, -43), (84, -43), (78, -70), (62, -150), (20, -146), (26, -110), (36, -75)]), half(26), wood,
              bevel=6 * mm, segments=2, grain="z", extra={"tone": -1})

    # three stiffening ribs across the dust cover, and a raised rib along each side of the magazine
    for x in (60, 120, 180):
        p.extrude(outline([(x, 30), (x, 35.5), (x + 14, 35.5), (x + 14, 30)]), half(27), steel, bevel=1.5 * mm,
                  extra={"tone": 1})

    # trigger guard and trigger
    p.extrude(outline([(84, -45), (84, -52), (96, -86), (150, -86), (160, -45), (155, -45), (146, -81), (99, -81),
                       (89, -52), (89, -45)]), half(9), steel, grain="x")
    p.extrude(outline([(108, -44), (118, -44), (114, -60), (108, -74), (104, -72), (108, -60)]), half(5), steel,
              extra={"chunk": "trigger", "tone": 2})

    # curved magazine: an arc that leans toward the muzzle
    radius, width, top = 330.0, 64.0, 182.0
    angles = [math.radians(-1.5 + 38.5 * k / 9) for k in range(10)]
    arc = lambda r, a: (top + radius - r * math.cos(a), -45 - r * math.sin(a))
    rear = [arc(radius + width / 2, a) for a in angles]
    front = [arc(radius - width / 2 + 4 * k / 9, a) for k, a in enumerate(angles)]
    p.extrude(outline(rear + front[::-1]), half(27), steel, bevel=3 * mm, grain="z",
              extra={"chunk": "magazine", "tone": 1})
    rib_a = [arc(radius + 8, a) for a in angles[2:9]]
    rib_b = [arc(radius - 8, a) for a in angles[2:9]]
    p.extrude(outline(rib_a + rib_b[::-1]), half(27) + 2.2 * mm, steel, bevel=1.2 * mm, grain="z",
              extra={"chunk": "magazine", "tone": 1})

    # handguards with brass ferrules, and the steel that shows between them
    p.extrude(outline([(266, 4), (266, -36), (280, -42), (392, -42), (410, -30), (410, 4)]), half(42), wood,
              bevel=7 * mm, segments=2, grain="x")
    p.extrude(outline([(274, 9), (274, 32), (284, 39), (388, 39), (400, 30), (400, 9)]), half(32), wood,
              bevel=7 * mm, segments=2, grain="x")
    p.extrude(outline([(264, 2), (264, 12), (412, 12), (412, 2)]), half(24), steel, grain="x")
    p.extrude(outline([(261, 7), (261, -38), (269, -38), (269, 7)]), half(44), "brass", bevel=1.5 * mm)
    p.extrude(outline([(407, 7), (407, -34), (417, -34), (417, 7)]), half(44), "brass", bevel=1.5 * mm)

    # barrel, gas tube and block, cleaning rod, front sight, muzzle
    r = 9.5 * mm * K["chunky"]
    p.lathe([(r, 0), (r, (640 - 258) * mm)], 12, steel, frame=along_barrel(258, 0), smooth=True)
    p.lathe([(r * 0.9, 0), (r * 0.9, (432 - 262) * mm)], 8, steel, frame=along_barrel(262, 25), smooth=True)
    p.extrude(outline([(414, -15), (414, 28), (430, 36), (446, 36), (452, 10), (452, -15)]), half(20), steel,
              bevel=2 * mm, grain="x")
    p.lathe([(r * 0.32, 0), (r * 0.32, (626 - 418) * mm)], 6, steel, frame=along_barrel(418, -16), smooth=True,
            extra={"tone": 2})
    p.extrude(outline([(566, -15), (566, 14), (574, 22), (590, 22), (596, 10), (596, -15)]), half(15), steel,
              bevel=1.5 * mm, grain="x")
    p.extrude(outline([(580, 20), (580, 46), (584, 46), (584, 20)]), half(3), steel)
    for sy in (-1, 1):
        p.extrude(outline([(572, 20), (570, 50), (576, 56), (590, 56), (595, 50), (592, 20)]), 1.6 * mm, steel,
                  frame=side(sy * half(10)))
    p.lathe([(r * 1.2, 0), (r * 1.25, 20 * mm), (r * 1.0, 28 * mm)], 12, steel, frame=along_barrel(640, 0), smooth=True)

    # bolt carrier and charging handle on the right side (-Y)
    cover = half(30)
    bx0, bz0 = pt(150, 13)
    bx1, bz1 = pt(236, 26)
    p.box((bx0, -cover - 3.5 * mm, bz0), (bx1, -cover + 6 * mm, bz1), steel, grain="x",
          extra={"chunk": "bolt", "tone": 3})
    hx, hz = pt(198, 19)
    p.lathe([(5 * mm, 0), (5.5 * mm, 22 * mm), (4 * mm, 26 * mm)], 8, steel,
            frame=frame_axes((hx, -cover - 3 * mm, hz), (1, 0, 0), (0, 0, 1)), extra={"chunk": "bolt", "tone": 3})

    # selector lever and rivets
    body = half(33)
    p.extrude(outline([(150, -8), (150, -18), (236, -24), (252, -14), (240, -6)]), 1.6 * mm, steel, grain="x",
              frame=side(-body - 1.6 * mm), extra={"tone": 2})
    for x, z in ((18, -8), (18, -34), (128, -38), (250, -32), (236, 0)):
        rx, rz = pt(x, z)
        for sy in (-1, 1):
            p.lathe([(3.6 * mm, 0), (3.2 * mm, 1.6 * mm)], 6, "brass", group="rivet", grain=None, detail=True,
                    frame=frame_axes((rx, sy * body, rz), (1, 0, 0), (0, 0, -sy)))

    # turquoise cloth wrapped round the lower handguard, with a loose end
    grip = half(42)
    for x0, x1, extra in ((322, 334, 2.5), (334, 347, 4.5), (347, 359, 2.0)):
        p.extrude(outline([(x0, 6 + extra), (x0, -43 - extra), (x1, -43 - extra), (x1, 6 + extra)]),
                  grip + extra * mm, "cloth", bevel=2.5 * mm, segments=2)
    p.extrude(outline([(339, -44), (351, -44), (358, -92), (344, -86)]), 1.4 * mm, "cloth", frame=side(-grip * 0.5))

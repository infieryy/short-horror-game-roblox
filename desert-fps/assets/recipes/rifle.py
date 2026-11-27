"""Assault rifle. Proportions follow a real wooden-furniture, curved-magazine service rifle
(about 880 mm long). Barrel along +X; the origin is the top of the pistol grip.

Parts: body, cover, stock, grip, handguard, barrel, muzzle, magazine, bolt, trigger, selector.
"""
import math

import config as C
from build import frame_axes
from .gun import MM, Gun

K = C.KIT["rifle"]
ORIGIN = (55.0, -45.0)                   # mm: top of the pistol grip


def build(p):
    g = Gun(p, ORIGIN, K["chunky"])
    steel, wood = "gunmetal", "wood"

    # body: receiver, rear sight, trigger guard, rivets
    receiver = g.shape("body", steel, [(0, 12), (0, -45), (258, -45), (266, -30), (266, 12)], 33, bevel=2)
    g.shape("body", steel, [(248, 12), (248, 44), (262, 48), (304, 42), (304, 12)], 15, bevel=1.5)
    g.shape("body", steel, [(84, -45), (84, -52), (96, -86), (150, -86), (160, -45), (155, -45), (146, -81), (99, -81),
                            (89, -52), (89, -45)], 9)
    for x, z in ((18, -8), (18, -34), (128, -38), (250, -32), (236, 0)):
        for side in (-1, 1):
            g.stud("body", "brass", x, z, side, 33)

    # dust cover with three stiffening ribs
    cover = g.shape("cover", steel, [(12, 12), (12, 24), (22, 33), (232, 33), (246, 22), (246, 12)], 30, bevel=6,
                    segments=2, tone=1)
    for x in (60, 120, 180):
        g.shape("cover", steel, [(x, 30), (x, 35.5), (x + 14, 35.5), (x + 14, 30)], 27, bevel=1.5, tone=1)

    # stock with a brass butt plate; pistol grip
    stock = g.shape("stock", wood, [(2, 6), (2, -40), (-40, -50), (-150, -92), (-238, -122), (-246, -118), (-246, -22),
                                    (-150, -8), (-50, 4)], 30, bevel=7, segments=2, tone=-1)
    g.shape("stock", "brass", [(-244, -19), (-244, -121), (-254, -121), (-254, -19)], 31, bevel=1.5)
    grip = g.shape("grip", wood, [(34, -43), (84, -43), (78, -70), (62, -150), (20, -146), (26, -110), (36, -75)], 26,
                   bevel=6, segments=2, grain="z", tone=-1)

    g.shape("trigger", steel, [(108, -44), (118, -44), (114, -60), (108, -74), (104, -72), (108, -60)], 5, tone=2)

    # curved magazine: an arc that leans toward the muzzle, with a raised rib along each side
    radius, width, top = 330.0, 64.0, 182.0
    angles = [math.radians(-1.5 + 38.5 * k / 9) for k in range(10)]
    arc = lambda r, a: (top + radius - r * math.cos(a), -45 - r * math.sin(a))
    rear = [arc(radius + width / 2, a) for a in angles]
    front = [arc(radius - width / 2 + 4 * k / 9, a) for k, a in enumerate(angles)]
    magazine = g.shape("magazine", steel, rear + front[::-1], 27, bevel=3, grain="z", tone=1)
    rib = [arc(radius + 8, a) for a in angles[2:9]] + [arc(radius - 8, a) for a in angles[2:9]][::-1]
    g.shape("magazine", steel, rib, 27 + 4.4 / K["chunky"], bevel=1.2, grain="z", tone=1)

    # handguard: two wooden halves with brass ferrules, steel between them, a turquoise cloth wrap
    lower = g.shape("handguard", wood, [(266, 4), (266, -36), (280, -42), (392, -42), (410, -30), (410, 4)], 42,
                    bevel=7, segments=2)
    upper = g.shape("handguard", wood, [(274, 9), (274, 32), (284, 39), (388, 39), (400, 30), (400, 9)], 32,
                    bevel=7, segments=2)
    g.shape("handguard", steel, [(264, 2), (264, 12), (412, 12), (412, 2)], 24)
    g.shape("handguard", "brass", [(261, 7), (261, -38), (269, -38), (269, 7)], 44, bevel=1.5)
    g.shape("handguard", "brass", [(407, 7), (407, -34), (417, -34), (417, 7)], 44, bevel=1.5)
    for x0, x1, extra in ((322, 334, 2.5), (334, 347, 4.5), (347, 359, 2.0)):
        g.shape("handguard", "cloth", [(x0, 6 + extra), (x0, -43 - extra), (x1, -43 - extra), (x1, 6 + extra)],
                42 + 2 * extra / K["chunky"], bevel=2.5, segments=2, grain=None)
    g.plate("handguard", "cloth", [(339, -44), (351, -44), (358, -92), (344, -86)], -1, 21, 2.8, grain=None, sink=1.4)

    # barrel group: barrel, gas tube and block, cleaning rod, hooded front sight
    g.tube("barrel", steel, 258, 640, 0, 9.5, segments=12)
    g.tube("barrel", steel, 262, 432, 25, 8.5, segments=8)
    g.shape("barrel", steel, [(414, -15), (414, 28), (430, 36), (446, 36), (452, 10), (452, -15)], 20, bevel=2)
    g.tube("barrel", steel, 418, 626, -16, 3.0, segments=6, tone=2)
    g.shape("barrel", steel, [(566, -15), (566, 14), (574, 22), (590, 22), (596, 10), (596, -15)], 15, bevel=1.5)
    g.shape("barrel", steel, [(580, 20), (580, 46), (584, 46), (584, 20)], 3, grain=None)
    for side in (-1, 1):
        g.plate("barrel", steel, [(572, 20), (570, 50), (576, 56), (590, 56), (595, 50), (592, 20)], side, 10, 3.2,
                grain=None, sink=1.6)
    g.muzzle("muzzle", steel, 640, 668, 0, 9.5, 5.0, 12, flare=1.22)

    # bolt carrier and charging handle on the right side (-Y); selector lever
    cover_half = g.half(30)
    (bx0, bz0), (bx1, bz1) = g.pt(150, 13), g.pt(236, 26)
    p.box((bx0, -cover_half - 3.5 * MM, bz0), (bx1, -cover_half + 6 * MM, bz1), steel, grain="x",
          extra={"chunk": "bolt", "tone": 3})
    hx, hz = g.pt(198, 19)
    p.lathe([(5 * MM, 0), (5.5 * MM, 22 * MM), (4 * MM, 26 * MM)], 8, steel, smooth=True,
            frame=frame_axes((hx, -cover_half - 3 * MM, hz), (1, 0, 0), (0, 0, 1)), extra={"chunk": "bolt", "tone": 3})
    g.plate("selector", steel, [(150, -8), (150, -18), (236, -24), (252, -14), (240, -6)], -1, 33, 3.2, tone=2)

    # ---- painted detail: lines too small to be worth modelling
    g.line(receiver, [(8, -3), (254, -3)])                                             # rail under the dust cover
    g.line(receiver, [(238, 8), (238, -42)])                                           # front trunnion
    g.line(receiver, [(30, 8), (30, -42)], width=1.6)
    g.line(receiver, [(168, -12), (212, -12), (217, -19), (212, -27), (168, -27), (163, -19)], closed=True)   # dimple
    for x, z in ((100, -22), (126, -30), (60, -20)):                                   # pins
        g.line(receiver, [(x - 3, z), (x, z + 3), (x + 3, z), (x, z - 3)], closed=True, width=1.6)
    g.line(cover, [(20, 17), (240, 17)], width=1.6)
    g.line(cover, [(146, 11), (242, 11), (242, 28), (146, 28)], sides=("-y",), closed=True, tone=-5)   # ejection port
    for a in (math.radians(4), math.radians(33.5)):                                    # magazine lip and floor plate
        g.line(magazine, [arc(radius + width / 2 - 3, a), arc(radius - width / 2 + 5, a)])
    g.line(magazine, [arc(radius - 22, a) for a in angles[2:9]], width=1.6, tone=-3)
    g.line(stock, [(-168, -50), (-120, -40), (-118, -48), (-166, -58)], closed=True, tone=-6, width=2.6)   # sling slot
    g.line(stock, [(-10, -8), (-110, -22), (-232, -44)], width=1.5, tone=-3)
    g.line(stock, [(-20, -30), (-120, -62), (-232, -100)], width=1.5, tone=-3)
    g.line(stock, [(-236, -24), (-236, -116)], width=1.8)
    g.line(lower, [(276, -15), (402, -15)], tone=-5, width=2.4)                        # finger groove
    g.line(lower, [(282, -30), (394, -30)], width=1.5, tone=-3)
    g.line(upper, [(282, 22), (392, 22)], width=1.6)
    for k in range(6):                                                                 # hatching on the grip
        z = -62 - k * 13
        g.line(grip, [(34 - k * 2.2, z), (70 - k * 2.6, z - 9)], width=1.5, tone=-4)

    # ---- attachment points and moving parts
    g.socket("muzzle", 668, 0)
    g.socket("optic", 130, 36)
    g.socket("underbarrel", 340, -44, up=(0, 0, -1))
    g.socket("side", 402, -16, side=1, on=42)                      # the lower handguard's left face, ahead of the wrap
    g.socket("magazine", 182, -45, forward=(0.2, 0, -1))
    g.socket("stock", 0, -18, forward=(-1, 0, 0))
    g.socket("aim_rear", 290, 46)
    g.socket("aim_front", 582, 46)
    g.joint("bolt", "slide", 198, 19, (-1, 0, 0), 70)
    g.joint("trigger", "hinge", 112, -44, (0, 1, 0), 15)
    g.joint("selector", "hinge", 240, -12, (0, 1, 0), 20)
    g.joint("magazine", "detach", 182, -45, (0.35, 0, -1), 0)

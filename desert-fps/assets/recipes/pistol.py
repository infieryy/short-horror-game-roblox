"""Sidearm: a large-frame, gas-operated magnum pistol in the style of the Desert Eagle
(about 273 mm long, 150 mm tall). Barrel along +X; the origin is the top of the grip.

What makes the shape: a long fixed barrel with a flat, ribbed top that narrows upward, a short
slide block at the rear whose arms run forward under the barrel, a deep frame and a big grip.

Parts: body (frame), slide, barrel, grip (panels), magazine, trigger, hammer, charm (cloth wrap).
"""
import config as C
from .gun import MM, Gun

K = C.KIT["pistol"]
ORIGIN = (30.0, -44.0)                   # mm: top of the grip, under the slide


def build(p):
    g = Gun(p, ORIGIN, K["chunky"])
    steel, wood = "gunmetal", "wood"

    # body: frame with a long beavertail, raked grip core, squared trigger guard, slide stop
    frame = g.shape("body", steel, [(-18, -24), (-12, -14), (-4, -12), (100, -12), (100, -22), (250, -22), (254, -26),
                                    (246, -40), (152, -40), (150, -47), (84, -47), (6, -38), (-10, -32)], 30, bevel=2)
    g.shape("body", steel, [(2, -34), (80, -46), (62, -132), (-16, -132), (-15, -96), (-7, -52)], 28, bevel=5,
            segments=2, grain="z")
    g.shape("body", steel, [(84, -47), (150, -47), (154, -52), (149, -86), (104, -93), (68, -91), (70, -86), (104, -88),
                            (145, -82), (149, -52), (88, -52)], 10)
    g.plate("body", steel, [(96, -15), (96, -21), (124, -22), (130, -18), (122, -14)], 1, 30, 3.0, tone=3)

    # slide: rear block with the sight and safety, and the arms that run forward under the barrel
    block = g.shape("slide", steel, [(0, -12), (0, 17), (5, 22), (100, 22), (104, 19), (104, -12)], 32, bevel=2.5, tone=2)
    arms = g.shape("slide", steel, [(100, -12), (252, -12), (256, -15), (256, -22), (100, -22)], 32, bevel=2, tone=2)
    g.shape("slide", steel, [(6, 21), (6, 28), (20, 28), (23, 21)], 15, bevel=1, tone=1)
    for side in (-1, 1):
        g.plate("slide", steel, [(14, 6), (14, -3), (34, -5), (41, 1), (31, 8)], side, 32, 3.0, tone=4)

    # barrel: longer than the frame, wide below, narrow flat top, brass front sight, open muzzle
    lower = g.shape("barrel", steel, [(104, -12), (104, 8), (264, 8), (268, 4), (268, -9), (264, -12)], 30, bevel=3, tone=1)
    upper = g.shape("barrel", steel, [(104, 8), (104, 19), (262, 19), (266, 15), (266, 8)], 17, bevel=4, segments=2, tone=1)
    g.shape("barrel", "brass", [(249, 18), (252, 26), (260, 26), (264, 18)], 5, bevel=0.8)
    g.muzzle("barrel", steel, 262, 273, -1, 8.5, 5.2, 4.5, tone=2)

    # wooden grip panels with a brass screw; turquoise cloth tied round the grip
    panel = [(6, -48), (70, -56), (56, -124), (-10, -124), (-9, -94), (-3, -58)]
    panels = [g.plate("grip", wood, panel, side, 28, 5.0, bevel=1.5, grain="z", tone=-1, sink=1.0) for side in (-1, 1)]
    for side in (-1, 1):
        g.stud("grip", "brass", 30, -88, side, 28 + 8 / K["chunky"], radius=4.2, height=1.8)
    g.shape("charm", "cloth", [(-15, -106), (66, -106), (64, -113), (-15, -113)], 28 + 11 / K["chunky"], bevel=2,
            segments=2, grain=None)
    g.shape("charm", "cloth", [(-15, -113), (64, -113), (62, -120), (-16, -120)], 28 + 13.5 / K["chunky"], bevel=2,
            segments=2, grain=None)
    g.plate("charm", "cloth", [(-18, -112), (-11, -112), (-14, -146), (-25, -140)], -1, 8, 2.8, grain=None, sink=1.4)

    # trigger, hammer, magazine (the body hides inside the grip; the brass base plate shows)
    g.shape("trigger", steel, [(112, -47), (122, -47), (119, -62), (113, -76), (108, -74), (112, -62)], 6, tone=3)
    g.shape("hammer", steel, [(-12, -14), (-1, -14), (-1, 6), (-6, 13), (-14, 12), (-12, 5), (-7, 0)], 8, bevel=1, tone=3)
    g.shape("magazine", steel, [(8, -52), (58, -58), (54, -132), (-8, -132)], 20, grain="z")
    g.shape("magazine", "brass", [(-20, -132), (66, -132), (68, -141), (-22, -141)], 29, bevel=2)

    # ---- painted detail
    for k in range(7):                                                                 # slide serrations
        g.line(block, [(10 + k * 6, -8), (15 + k * 6, 17)], tone=-5, width=1.8)
    g.line(block, [(52, 6), (96, 6), (96, 19), (56, 19)], sides=("-y",), closed=True, tone=-6)   # ejection port
    g.line(arms, [(106, -17), (250, -17)], width=1.5)
    g.line(lower, [(110, -3), (260, -3)], tone=-5, width=2.2)                          # the long flat along the barrel
    g.line(lower, [(112, 4), (150, 4)], width=1.4, tone=-3)
    for x in range(116, 250, 11):                                                      # ribbed top
        g.across(upper, x, 19, 5.5, tone=-5, width=2.4)
    for x in (180, 194, 208):                                                          # accessory notches
        g.line(frame, [(x, -25), (x, -38)], width=2.2, tone=-5)
    g.line(frame, [(137, -31), (140, -28), (143, -31), (140, -34)], closed=True, width=1.6)   # takedown pin
    g.line(frame, [(20, -19), (92, -19)], width=1.4, tone=-3)
    for pid, facet in zip(panels, ("-y", "+y")):                                       # diamond checkering
        for k in range(-2, 8):
            z = -50 - k * 11
            g.line(pid, [(-12, z - 10), (72, z + 14)], sides=(facet,), width=1.2, tone=-4)
            g.line(pid, [(-12, z + 14), (72, z - 10)], sides=(facet,), width=1.2, tone=-3)

    # ---- attachment points and moving parts
    g.socket("muzzle", 273, -1)
    g.socket("optic", 180, 19)
    g.socket("underbarrel", 200, -40, up=(0, 0, -1))
    g.socket("magazine", 24, -132, forward=(-0.2, 0, -1))
    g.socket("aim_rear", 13, 28)
    g.socket("aim_front", 256, 26)
    g.joint("slide", "slide", 50, 5, (-1, 0, 0), 58)
    g.joint("trigger", "hinge", 117, -47, (0, 1, 0), 12)
    g.joint("hammer", "hinge", -3, -14, (0, 1, 0), 50)
    g.joint("magazine", "detach", 24, -132, (-0.2, 0, -1), 0)

"""Karambit, traced from a reference photo: a long sickle blade that is wide at the base,
a handle with a hooked guard and two deep finger grooves, inlaid grip panels, jimping on the
spine, and a finger ring at the pommel (about 190 mm from ring to tip).

The outlines below are pixel positions measured on the reference (1580 px wide), turned into
millimetres by ref(). The blade points along +X with its tip dipping; the handle runs back and
down to the ring; the origin is the palm.
Built with the same toolkit and scale as the guns. Parts: blade, handle, ring, charm.
"""
import math

import config as C
from build import frame_axes
from .gun import MM, Gun

K = C.KIT["knife"]
PX = 0.128                               # millimetres per reference pixel
RING = (1390, 800)                       # reference pixel of the ring's centre
TURN = math.radians(0)                   # extra tilt, if the knife should sit at another angle than the photo


def ref(px, py):
    """Reference pixel -> side-view millimetres (ring centre at 0, 0; mirrored so the blade points +X)."""
    x, z = (RING[0] - px) * PX, (RING[1] - py) * PX
    return (x * math.cos(TURN) - z * math.sin(TURN), x * math.sin(TURN) + z * math.cos(TURN))


def refs(points):
    return [ref(px, py) for px, py in points]


ORIGIN = ref(1100, 390)                  # the palm, between the two finger grooves

# blade stations from the guard to the tip: (spine pixel, edge pixel)
BLADE = [((850, 118), (775, 430)), ((740, 101), (712, 380)), ((620, 93), (640, 332)), ((500, 98), (555, 300)),
         ((390, 122), (450, 285)), ((290, 170), (330, 293)), ((195, 238), (215, 323)), ((110, 320), (120, 366)),
         ((32, 416), (30, 420))]
SPINE, EDGE, GRIND = 4.2, 0.5, 0.36      # mm thick at spine and edge; where the grind starts (0 spine .. 1 edge)
HANDLE_WIDTH = 14.0                      # mm



def scoop(a, deepest, b, steps=7):
    """Points on the round cut through three reference pixels (a finger groove), without the end points."""
    (ax, ay), (bx, by), (cx, cy) = a, deepest, b
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax * ax + ay * ay) * (by - cy) + (bx * bx + by * by) * (cy - ay) + (cx * cx + cy * cy) * (ay - by)) / d
    uy = ((ax * ax + ay * ay) * (cx - bx) + (bx * bx + by * by) * (ax - cx) + (cx * cx + cy * cy) * (bx - ax)) / d
    radius = math.hypot(ax - ux, ay - uy)
    start, mid, end = (math.atan2(q[1] - uy, q[0] - ux) for q in (a, deepest, b))
    unwrap = lambda angle, base: angle + 2 * math.pi * round((base - angle) / (2 * math.pi))
    mid = unwrap(mid, start)
    end = unwrap(end, mid)
    return [(ux + radius * math.cos(start + (end - start) * k / steps), uy + radius * math.sin(start + (end - start) * k / steps))
            for k in range(1, steps)]


GROOVE_2 = scoop((1178, 610), (1105, 472), (1030, 492))      # nearer the ring
GROOVE_1 = scoop((1030, 492), (955, 355), (870, 402))        # nearer the blade
HANDLE = ([(862, 110), (905, 110), (935, 135), (1000, 180), (1085, 240), (1120, 250), (1180, 275), (1260, 340),
           (1340, 425), (1395, 500), (1450, 575), (1500, 645), (1535, 690),               # spine side, guard to ring
           (1480, 700), (1400, 690), (1310, 690), (1250, 715), (1215, 652), (1178, 610)]  # over the ring
          + GROOVE_2 + [(1030, 492)] + GROOVE_1 +
          [(870, 402), (850, 425), (800, 455), (762, 445), (760, 380), (768, 300), (775, 240),    # lower spur, guard face
           (792, 218), (760, 200), (752, 180), (772, 165), (838, 118)])                   # notch and upper prong
FRONT_PANEL = [(884, 152), (1030, 258), (1010, 300), (945, 372), (880, 386), (872, 300)]
REAR_PANEL = [(1050, 283), (1120, 290), (1200, 318), (1290, 390), (1370, 480), (1385, 520), (1330, 520), (1250, 480),
              (1190, 470), (1140, 420), (1085, 380), (1045, 330)]


def build(p):
    g = Gun(p, ORIGIN, K["chunky"])
    between = lambda a, b, t: (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)

    # blade: flat near the spine, then one long grind down to the edge; thinner toward the tip
    rings = []
    for k, (s_px, e_px) in enumerate(BLADE):
        thin = 1.0 - 0.6 * k / (len(BLADE) - 1)
        spine, edge = g.half(SPINE) * thin, g.half(EDGE)
        (sx, sz), (gx, gz), (ex, ez) = ref(*s_px), ref(*between(s_px, e_px, GRIND)), ref(*e_px)
        rings.append([g.at(sx, sz, -spine), g.at(gx, gz, -spine * 0.94), g.at(ex, ez, -edge),
                      g.at(ex, ez, edge), g.at(gx, gz, spine * 0.94), g.at(sx, sz, spine)])
    blade = p.loft(rings, "steel", grain="x", extra={"chunk": "blade", "tone": -3})

    # handle: dark frame (the same dark metal as the guns) with warm wooden grip panels and brass pins
    handle = g.shape("handle", "gunmetal", refs(HANDLE), HANDLE_WIDTH, bevel=3.0, segments=2)
    front = [g.plate("handle", "wood", refs(FRONT_PANEL), side, HANDLE_WIDTH, 2.4, bevel=1.0, sink=0.6) for side in (-1, 1)]
    rear = [g.plate("handle", "wood", refs(REAR_PANEL), side, HANDLE_WIDTH, 2.4, bevel=1.0, sink=0.6) for side in (-1, 1)]
    for px, py in ((946, 268), (1125, 345), (1300, 445)):
        for side in (-1, 1):
            g.stud("handle", "brass", *ref(px, py), side, HANDLE_WIDTH + 3.6 / K["chunky"], radius=3.0, height=1.4)

    # finger ring at the pommel
    cx, cz = g.pt(0, 0)
    ring = [(12.8, -3.2), (18.0, -3.2), (19.2, -1.8), (19.2, 1.8), (18.0, 3.2), (12.8, 3.2)]
    p.lathe([(r * MM, h * MM * K["chunky"]) for r, h in ring], 20, "steel", closed=True, smooth=True, grain=None,
            frame=frame_axes((cx, 0, cz), (1, 0, 0), (0, 0, 1)), extra={"chunk": "ring"})

    # charm: turquoise cloth knotted on the ring, two loose ends
    g.shape("charm", "cloth", [(-9, -11.5), (8, -11.5), (7, -22), (-8, -22)], 10, bevel=1.5, segments=2, grain=None)
    g.plate("charm", "cloth", [(-7, -20), (0, -20), (3, -62), (-6, -58)], -1, 4, 2.6, grain=None, sink=1.3)
    g.plate("charm", "cloth", [(-2, -20), (4, -20), (13, -50), (6, -53)], 1, 4, 2.6, grain=None, sink=1.3)

    # ---- painted detail
    along = lambda share, stations=BLADE[:-1]: [ref(*between(s, e, share)) for s, e in stations]
    g.line(blade, along(GRIND), tone=-8, width=2.2)                                    # where the grind starts
    g.line(blade, along(0.14, BLADE[2:-1]), tone=-6, width=1.6)                        # swedge near the spine
    for share, tone in ((0.62, 4), (0.86, 5)):                                         # light on the ground bevel
        g.line(blade, along(share, BLADE[1:-1]), tone=tone, width=2.4)
    g.line(blade, refs([(640, 190), (700, 250), (740, 330), (752, 400)]), tone=-5, width=1.6)   # plunge line at the base
    for pid, facet in zip(front, ("-y", "+y")):                                        # ribbed front panel
        for px in range(880, 1040, 13):
            g.line(pid, refs([(px, 130), (px, 400)]), sides=(facet,), tone=-6, width=1.8)
    for pid, facet in zip(rear, ("-y", "+y")):                                         # checkered rear panel
        for px in range(900, 1520, 22):
            g.line(pid, refs([(px, 240), (px + 200, 560)]), sides=(facet,), tone=-5, width=1.5)
            g.line(pid, refs([(px + 140, 240), (px - 120, 560)]), sides=(facet,), tone=-5, width=1.5)
    for a, b, teeth in (((944, 142), (1080, 237), 9), ((1402, 512), (1496, 640), 8)):   # jimping on the spine
        length = math.hypot(b[0] - a[0], b[1] - a[1])
        inward = (-(b[1] - a[1]) / length * 20, (b[0] - a[0]) / length * 20)
        for k in range(teeth):
            start = between(a, b, k / (teeth - 1))
            g.line(handle, refs([start, (start[0] + inward[0], start[1] + inward[1])]), tone=-6, width=1.6)

    # ---- attachment points and moving parts
    g.socket("blade_base", *ref(790, 280))
    g.socket("blade_tip", *ref(30, 418), forward=(0.6, 0, -0.8))
    g.socket("ring", 0, 0, forward=(0, 1, 0))
    g.socket("charm", 0, -19, forward=(0, 0, -1))
    g.joint("knife", "hinge", 0, 0, (0, 1, 0), 360)         # the spin round the finger

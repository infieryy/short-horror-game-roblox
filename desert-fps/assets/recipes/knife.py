"""Karambit: a hooked, claw-shaped blade, a curved handle, and a finger ring at the pommel
(about 205 mm from ring to tip). The blade points along +X and hooks downward; the origin is
the middle of the handle, where the palm sits.

Built with the same toolkit and scale as the guns. Parts: body (ring, guard, pins), blade,
handle, charm (cloth tied through the ring).
"""
import config as C
from build import frame_axes
from .gun import MM, Gun

K = C.KIT["knife"]
ORIGIN = (66.0, 30.0)                    # mm: middle of the handle

# The blade as stations from the guard to the tip: (spine point, edge point), side view, mm.
BLADE = [((112, 45), (113, 20)), ((135, 43), (130, 16)), ((157, 34), (144, 8)), ((175, 19), (157, -5)),
         ((186, -1), (167, -20)), ((191, -22), (177, -34)), ((189, -41), (187, -43))]
SPINE, EDGE, GRIND = 4.2, 0.5, 0.48      # mm thick at the spine and at the edge; where the grind starts (0 spine .. 1 edge)


def build(p):
    g = Gun(p, ORIGIN, K["chunky"])
    steel, wood = "steel", "wood"

    # blade: flat near the spine, then ground down to the edge; thinner toward the tip
    rings, grind_line = [], []
    for k, ((sx, sz), (ex, ez)) in enumerate(BLADE):
        thin = 1.0 - 0.55 * k / (len(BLADE) - 1)
        spine, edge = g.half(SPINE) * thin, g.half(EDGE)
        gx, gz = sx + (ex - sx) * GRIND, sz + (ez - sz) * GRIND
        grind_line.append((gx, gz))
        rings.append([g.at(sx, sz, -spine), g.at(gx, gz, -spine * 0.94), g.at(ex, ez, -edge),
                      g.at(ex, ez, edge), g.at(gx, gz, spine * 0.94), g.at(sx, sz, spine)])
    blade = p.loft(rings, steel, grain="x", extra={"chunk": "blade", "tone": 1})

    # handle: curved wooden grip with finger grooves
    handle = g.shape("handle", wood, [(8, 12), (34, 33), (64, 44), (98, 47), (110, 45), (110, 22), (98, 22), (84, 17),
                                      (70, 18), (58, 12), (46, 4), (34, 2), (24, -8), (14, -12)], 15, bevel=4,
                     segments=2, tone=-1)

    # body: finger ring, brass guard, brass pins
    cx, cz = g.pt(0, 0)
    ring = [(11.5, -3.2), (16.2, -3.2), (17.4, -1.8), (17.4, 1.8), (16.2, 3.2), (11.5, 3.2)]
    p.lathe([(r * MM, h * MM * K["chunky"]) for r, h in ring], 18, steel, closed=True, smooth=True, grain=None,
            frame=frame_axes((cx, 0, cz), (1, 0, 0), (0, 0, 1)))
    g.shape("body", "brass", [(106, 49), (117, 47.5), (120, 34), (117, 19), (106, 19.5)], 18, bevel=2)
    for x, z in ((36, 16), (64, 30), (92, 34)):
        for side in (-1, 1):
            g.stud("body", "brass", x, z, side, 15, radius=3.4, height=1.4)

    # charm: turquoise cloth knotted on the ring, two loose ends
    g.shape("charm", "cloth", [(-9, -12), (7, -12), (6, -20), (-8, -20)], 9, bevel=1.5, segments=2, grain=None)
    g.plate("charm", "cloth", [(-7, -18), (0, -18), (3, -58), (-6, -54)], -1, 4, 2.6, grain=None, sink=1.3)
    g.plate("charm", "cloth", [(-2, -18), (4, -18), (13, -47), (6, -50)], 1, 4, 2.6, grain=None, sink=1.3)

    # ---- painted detail
    g.line(blade, grind_line[:-1], tone=-6, width=1.8)                                 # where the grind starts
    for share, tone in ((0.66, 5), (0.84, 4)):                                          # light catching the ground bevel
        g.line(blade, [(sx + (ex - sx) * share, sz + (ez - sz) * share) for (sx, sz), (ex, ez) in BLADE[:-1]],
               tone=tone, width=2.4)
    g.line(blade, [(118, 40), (140, 38), (159, 29.5), (172, 17)], tone=-4, width=1.3)   # fuller along the spine
    g.line(blade, [(118, 33), (124, 36), (130, 33), (124, 30)], closed=True, width=1.0, tone=-4)   # maker's mark
    for (x0, z0), (x1, z1) in (((84, 18), (80, 30)), ((58, 13), (52, 26)), ((34, 3), (27, 14))):    # finger grooves
        g.line(handle, [(x0, z0), (x1, z1)], tone=-5, width=1.8)
    g.line(handle, [(16, 12), (40, 31), (66, 40), (104, 43)], width=1.0, tone=-3)

    # ---- attachment points and moving parts
    g.socket("blade_base", 113, 33)
    g.socket("blade_tip", 188, -42, forward=(0.1, 0, -1))
    g.socket("ring", 0, 0, forward=(0, 1, 0))
    g.socket("charm", 0, -17, forward=(0, 0, -1))
    g.joint("knife", "hinge", 0, 0, (0, 1, 0), 360)         # the spin round the finger

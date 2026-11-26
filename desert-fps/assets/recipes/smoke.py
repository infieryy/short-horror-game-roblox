"""Smoke grenade, after the standard military smoke canister (about 60 mm across, 150 mm tall
with its fuze): a can with rolled rims, a fuze on top, a safety lever that runs over the fuze and
down the side, and a pull pin with a ring.

The can stands along +Z; the lever is on the +X side and the pin's ring hangs on the -Y side.
The origin is the middle of the can, where the hand closes round it.
Built with the same toolkit and scale as the guns. Parts: body, fuze, lever, pin.
"""
import math

import config as C
from build import frame_axes
from .gun import MM, Gun

K = C.KIT["smoke"]
ORIGIN = (0.0, 57.0)                     # mm: middle of the can
CAN_R, CAN_H = 30.0, 115.0               # mm
BAND = (74.0, 98.0)                      # mm: the painted colour band (tells you what the can does)
LEVER = [(-11, 148), (13, 148), (24, 142.5), (32.6, 129), (33.2, 112), (33.2, 52), (35.6, 43)]   # its centre line


def ribbon(points, thick):
    """A bent strip: the outline `thick` mm wide around a centre line."""
    left, right = [], []
    for k, (x, z) in enumerate(points):
        ax, az = points[max(k - 1, 0)]
        bx, bz = points[min(k + 1, len(points) - 1)]
        length = math.hypot(bx - ax, bz - az)
        nx, nz = -(bz - az) / length * thick / 2, (bx - ax) / length * thick / 2
        left.append((x + nx, z + nz))
        right.append((x - nx, z - nz))
    return left + right[::-1]


def build(p):
    g = Gun(p, ORIGIN, K["chunky"])
    upright = lambda x, z, y=0.0: frame_axes(g.at(x, z, y), (1, 0, 0), (0, 1, 0))      # local Z is up

    # body: the can with a rolled rim at each end, and the painted band
    profile = [(27.5, 0), (30.6, 2.5), (30.6, 5), (CAN_R, 7), (CAN_R, 108), (30.6, 110), (30.6, 112.5), (27.5, CAN_H)]
    can = p.lathe([(r * MM, z * MM) for r, z in profile], 16, "gunmetal", smooth=True, frame=upright(0, 0))
    p.lathe([(30.7 * MM, 0), (30.7 * MM, (BAND[1] - BAND[0]) * MM)], 16, "band", smooth=True, grain=None,
            frame=upright(0, BAND[0]))

    # fuze: threaded neck and the striker housing
    p.lathe([(10 * MM, 0), (10 * MM, 9 * MM)], 10, "brass", smooth=True, frame=upright(0, CAN_H - 1), extra={"chunk": "fuze"})
    g.shape("fuze", "brass", [(-12, 123), (-12, 140), (-5, 146.5), (10, 146.5), (14, 140), (14, 123)], 17, bevel=1.6)

    # lever: one bent strip of steel over the fuze and down the side of the can
    g.shape("lever", "steel", ribbon(LEVER, 2.2), 15, grain="z", tone=2)

    # pin through the housing, with its pull ring hanging on the right side
    px, pz = g.pt(3, 135)
    p.lathe([(1.7 * MM, 0), (1.7 * MM, 30 * MM)], 6, "steel", smooth=True,
            frame=frame_axes((px, 15 * MM, pz), (1, 0, 0), (0, 0, 1)), extra={"chunk": "pin"})
    tube, loop = 1.5, 11.0
    circle = [(loop + tube * math.cos(2 * math.pi * k / 6), tube * math.sin(2 * math.pi * k / 6)) for k in range(6)]
    cx, cz = g.pt(3, 135 - loop)
    p.lathe([(r * MM, h * MM) for r, h in circle], 14, "steel", closed=True, smooth=True, grain=None,
            frame=frame_axes((cx, -13.5 * MM, cz), (1, 0, 0), (0, 0, 1)), extra={"chunk": "pin"})

    # ---- painted detail
    hop = lambda z: (z + 1.6) * MM               # height on the can -> distance along its profile
    for z in (20, 62):                                                                 # pressed rings round the can
        p.mark(can, "lathe", [(0.0, hop(z)), (1.0, hop(z))], tone=-5, width=1.8 * MM)
    p.mark(can, "lathe", [(0.31, hop(8)), (0.31, hop(106))], tone=-4, width=1.4 * MM)   # the can's seam
    for turn in (0.08, 0.58):                                                          # stencilled bars, no lettering
        for z, reach in ((50, 0.11), (42, 0.07), (34, 0.09)):
            p.mark(can, "lathe", [(turn, hop(z)), (turn + reach, hop(z))], tone=6, width=3.2 * MM)
    top = g.pt(0, CAN_H)[1]
    for k in range(4):                                                                 # vents in the lid
        a = math.pi / 4 + k * math.pi / 2
        hole = [(17 * MM * math.cos(a) + 3.4 * MM * math.cos(b), 17 * MM * math.sin(a) + 3.4 * MM * math.sin(b), top)
                for b in (i * math.pi / 3 for i in range(6))]
        p.mark(can, "+z", hole, tone=-8, width=2.6 * MM, closed=True)

    # ---- attachment points and moving parts
    g.socket("smoke", 0, CAN_H, forward=(0, 0, 1), up=(1, 0, 0))
    g.joint("pin", "detach", 3, 135, (0, -1, 0), 0)
    g.joint("lever", "hinge", -11, 148, (0, 1, 0), 100)

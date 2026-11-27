"""Attachments for the guns. Each is a piece of its own, built with the guns' toolkit and at their scale,
and goes on a gun at one of its sockets (muzzle, optic, underbarrel).

An attachment's origin is where it meets the gun: the back face of a muzzle device on the bore's axis, the
underside of an optic's base, the top of whatever hangs under the barrel. x runs toward the muzzle and z up,
as on the guns. An optic has a socket "eye": the middle of what the shooter looks through.
One part each: body.
"""
import math

import config as C
from build import frame_axes
from .gun import MM, Gun

CHUNKY = C.KIT["att"]["chunky"]


def along(g, x, z):
    """A frame whose Z runs toward the muzzle, at x, z (mm): for parts turned round the bore."""
    px, pz = g.pt(x, z)
    return frame_axes((px, 0, pz), (0, 1, 0), (0, 0, 1))


def rings(p, pid, distances, tone=-5, width=1.6):
    """Painted rings round a turned part, at these distances (mm) along its profile."""
    for d in distances:
        p.mark(pid, "lathe", [(0.0, d * MM), (1.0, d * MM)], tone=tone, width=width * MM)


def suppressor(p):
    """A sound suppressor: a can 150 mm long that screws on over the muzzle."""
    g = Gun(p, (0.0, 0.0), CHUNKY)
    radius = 17.0
    step = math.hypot(0.38 * radius * CHUNKY, 4)                   # the shoulder between the collar and the can
    can = g.tube("body", "gunmetal", 0, 150, 0, radius, segments=14,
                 profile=[(0.62, 0), (0.62, 6), (1.0, 10), (1.0, 150)])
    g.muzzle("body", "gunmetal", 150, 166, 0, radius, 5.5, 10)
    rings(p, can, [6 + step + d for d in (26, 30, 70, 74, 114, 118)])
    for turn in (0.12, 0.62):                                       # wrench flats on the collar
        p.mark(can, "lathe", [(turn, 1 * MM), (turn + 0.1, 1 * MM), (turn + 0.1, 5 * MM), (turn, 5 * MM)], tone=4,
               width=1.2 * MM, closed=True)
    g.socket("mount", 0, 0, forward=(-1, 0, 0))


def compensator(p):
    """A muzzle brake: a short ported sleeve that sends gas up and to the sides."""
    g = Gun(p, (0.0, 0.0), CHUNKY)
    radius = 13.0
    sleeve = g.tube("body", "steel", 0, 42, 0, radius, segments=12, profile=[(0.76, 0), (0.76, 5), (1.0, 8), (1.0, 42)])
    g.muzzle("body", "steel", 42, 58, 0, radius, 5.5, 12, flare=1.14)
    step = math.hypot(0.24 * radius * CHUNKY, 3)
    for turn in (0.17, 0.25, 0.33, 0.67, 0.75, 0.83):               # ports: three a side, toward the top
        for d in (14, 26):
            p.mark(sleeve, "lathe", [(turn - 0.025, (5 + step + d) * MM), (turn + 0.025, (5 + step + d) * MM)],
                   tone=-8, width=5.5 * MM)
    rings(p, sleeve, [5 + step + 2], tone=-4)
    g.socket("mount", 0, 0, forward=(-1, 0, 0))


def reddot(p):
    """A reflex sight: a base that clamps on, an emitter at the back, an open window to look through.
    Half as big again as a real one, so the window reads from behind the rifle. The emitter is kept low:
    seen from the eye it lies in front of the window, and one as tall as a real one hides the window's lower half."""
    g = Gun(p, (0.0, 0.0), CHUNKY)
    steel = "gunmetal"
    k = 1.5
    big = lambda points: [(x * k, z * k) for x, z in points]
    wide = 24 * k
    base = g.shape("body", steel, big([(-24, 0), (-24, 7), (24, 7), (24, 0)]), wide, bevel=1.5)
    g.shape("body", steel, big([(-22, 7), (-22, 11.5), (-11, 11.5), (-6, 7)]), 16 * k, bevel=1.0, tone=1)   # emitter
    for side in (-1, 1):                                                                              # window posts
        g.plate("body", steel, big([(5, 5), (7, 36), (15, 36), (19, 5)]), side, wide, 3.4 * k, bevel=0.8, sink=1.7 * k)
    g.shape("body", steel, big([(6, 33.5), (6, 38), (16, 38), (16, 33.5)]), wide + 4.6 * k / CHUNKY, bevel=1.2)   # top
    for side in (-1, 1):
        g.stud("body", "brass", -16 * k, 9.3 * k, side, 16 * k, radius=2.8)                           # adjusters
        g.stud("body", "brass", 0, 3.5 * k, side, wide, radius=3.0)                                   # clamp screws
    g.line(base, big([(-20, 3.5), (20, 3.5)]), width=1.6)
    g.socket("mount", 0, 0, up=(0, 0, -1))
    g.socket("eye", 11 * k, 21 * k)


def scope(p):
    """A short two-power sight: a fat tube on two rings, open from end to end so the target shows through.
    Nothing may reach into the bore (12.5 mm round the axis, times CHUNKY): the eye looks down it, and the top
    of a ring's foot or the underside of the turret shows there as clutter. They end inside the tube's wall."""
    g = Gun(p, (0.0, 0.0), CHUNKY)
    steel = "gunmetal"
    axis = 31.0
    g.shape("body", steel, [(-34, 0), (-34, 7), (34, 7), (34, 0)], 22, bevel=1.5)                    # base
    for x in (-21, 23):                                                                              # the two rings' feet
        g.shape("body", steel, [(x - 6, 7), (x - 6, 15), (x + 6, 15), (x + 6, 7)], 13, bevel=1.0, tone=1)
        for side in (-1, 1):
            g.stud("body", "brass", x, 12, side, 13, radius=2.8)
    r = lambda mm: mm * MM * CHUNKY
    bore = r(12.5)
    profile = [(bore, 0), (r(17.5), 0), (r(17.5), 15 * MM), (r(15), 23 * MM), (r(15), 60 * MM), (r(18.5), 72 * MM),
               (r(18.5), 92 * MM), (bore, 92 * MM)]
    tube = p.lathe(profile, 14, steel, closed=True, smooth=True, frame=along(g, -45, axis))
    start = (17.5 - 12.5) * CHUNKY                                  # the profile begins by crossing the eyepiece's rim
    rings(p, tube, [start + 5, start + 11, start + 15 + 8.4 + 14, start + 15 + 8.4 + 23], tone=-5)
    rings(p, tube, [start + 15 + 8.4 + 37 + 12.5 + 10], tone=5, width=2.2)     # a pale band round the front bell
    px, pz = g.pt(2, axis + 16)                                     # the turret on top
    p.lathe([(7 * MM, 0), (7 * MM, 6 * MM), (5.5 * MM, 8 * MM)], 8, "brass", smooth=True,
            frame=frame_axes((px, 0, pz), (1, 0, 0), (0, 1, 0)))
    g.socket("mount", 0, 0, up=(0, 0, -1))
    g.socket("eye", 0, axis)


def foregrip(p):
    """A vertical grip for the left hand, in the rifle's own wood, on a steel clamp."""
    g = Gun(p, (0.0, 0.0), CHUNKY)
    clamp = g.shape("body", "gunmetal", [(-18, 0), (-18, -9), (18, -9), (18, 0)], 30, bevel=1.5)
    grip = g.shape("body", "wood", [(-11, -9), (-14, -74), (-9, -81), (9, -81), (14, -74), (11, -9)], 26, bevel=6,
                   segments=2, grain="z", tone=-1)
    g.shape("body", "brass", [(-12.5, -9), (-12.5, -14), (12.5, -14), (12.5, -9)], 28, bevel=1.2)   # ferrule
    for side in (-1, 1):
        g.stud("body", "brass", 0, -4.5, side, 30, radius=3.0)
    for k in range(5):                                                                               # finger grooves
        z = -26 - k * 11
        g.line(grip, [(-12, z), (12, z - 3)], width=1.6, tone=-4)
    g.line(clamp, [(-15, -4.5), (15, -4.5)], width=1.2)
    g.socket("mount", 0, 0)


def laser(p):
    """A laser pointer: a small box under the barrel with its lens at the front."""
    g = Gun(p, (0.0, 0.0), CHUNKY)
    box = g.shape("body", "gunmetal", [(-24, 0), (-24, -21), (17, -21), (23, -15), (23, 0)], 22, bevel=2)
    g.muzzle("body", "brass", 21, 28, -10.5, 6.0, 3.4, 4)                                           # the lens
    for side in (-1, 1):
        g.stud("body", "brass", -14, -6, side, 22, radius=2.6)
    g.shape("body", "steel", [(-10, -21), (-10, -24), (4, -24), (4, -21)], 12, bevel=0.8, tone=2)   # the switch
    g.line(box, [(-20, -12), (12, -12)], width=1.3)
    g.line(box, [(-4, -3), (-4, -19)], width=1.3, tone=-3)
    g.socket("mount", 0, 0)
    g.socket("beam", 28, -10.5)

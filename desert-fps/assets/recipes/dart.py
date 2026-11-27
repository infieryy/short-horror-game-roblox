"""Recon dart: a thrown sensor that sticks in a wall and looks for enemies. A steel point, a brass collar, a
fat sensor head with a turquoise glass band round it (the part that sees), a thin shaft and four fins.

It flies along +X. The origin is the tip of the point, the part that goes into the wall, so a dart is put in
the world by its tip. Built with the guns' toolkit and at their scale. One part: body.
"""
import config as C
from build import frame_axes
from .gun import MM, Gun

K = C.KIT["util"]
LENGTH = 250.0                           # mm from the tail to the tip
HEAD = (-150.0, -62.0)                   # mm: where the sensor head starts and ends
GLASS = (-124.0, -92.0)                  # mm: the glass band on it
FIN = [(-248, 8), (-248, 36), (-222, 36), (-186, 8)]   # one fin, above the shaft


def build(p):
    g = Gun(p, (0.0, 0.0), K["chunky"])
    steel, dark = "steel", "gunmetal"

    # shaft and tail cap
    shaft = g.tube("body", dark, -LENGTH, HEAD[0], 0, 7.0, segments=8,
                   profile=[(1.3, 0), (1.3, 9), (1.0, 12), (1.0, LENGTH + HEAD[0])])
    # Each round part starts a millimetre inside the one behind it: two end faces in one plane would flicker.
    # sensor head: swells from the shaft, holds the glass, narrows to the collar
    long = HEAD[1] - HEAD[0] + 1
    head = g.tube("body", dark, HEAD[0] - 1, HEAD[1], 0, 20.0, segments=12,
                  profile=[(0.36, 0), (0.86, 11), (1.0, 23), (1.0, long - 26), (0.8, long - 10), (0.46, long)])
    g.tube("body", "band", GLASS[0], GLASS[1], 0, 21.0, segments=12, tone=2)                 # the glass band
    for x in (GLASS[0] - 5, GLASS[1] - 2):                                                   # brass rims either side
        g.tube("body", "brass", x, x + 7, 0, 22.0, segments=12)
    # collar and point
    g.tube("body", "brass", HEAD[1] - 1, -40, 0, 9.5, segments=10, profile=[(1.0, 0), (1.0, 17), (0.8, 23)])
    g.tube("body", steel, -41, 0, 0, 7.0, segments=8, profile=[(1.0, 0), (0.86, 11), (0.08, 41)])

    # fins: one pair upright, one pair flat
    both = FIN + [(x, -z) for x, z in reversed(FIN)]
    fins = g.shape("body", steel, both, 3.2, bevel=0.6, tone=1)
    p.extrude(g.outline(both), g.half(3.2), steel, bevel=0.6 * MM, frame=frame_axes((0, 0, 0), (1, 0, 0), (0, 0, 1)),
              extra={"tone": 1})

    # ---- painted detail
    for d in (30, 36, 60, 66):                                                               # rings on the shaft
        p.mark(shaft, "lathe", [(0.0, d * MM), (1.0, d * MM)], tone=-5, width=1.6 * MM)
    for turn in (0.0, 0.25, 0.5, 0.75):                                                      # vents in the head
        p.mark(head, "lathe", [(turn + 0.04, 58 * MM), (turn + 0.2, 58 * MM)], tone=-7, width=3.0 * MM)
    for z in (16, 24):                                                                       # ribs on the fins
        g.line(fins, [(-246, z), (-214 + (36 - z) * 1.2, z)], width=1.2, tone=-4)
        g.line(fins, [(-246, -z), (-214 + (36 - z) * 1.2, -z)], width=1.2, tone=-4)

    g.socket("tip", 0, 0)
    g.socket("eye", (GLASS[0] + GLASS[1]) / 2, 0)

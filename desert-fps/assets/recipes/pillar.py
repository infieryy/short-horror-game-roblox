"""Pillar: a stone column one story tall. Square base with the turquoise band, eight-sided shaft,
stepped capital."""
import config as C

K = C.KIT["pillar"]
CUT = {"cut": True}


def build(p):
    b, c, top = K["base"], K["cap"], C.STORY
    p.box((-b, -b, 0), (b, b, K["base_h"]), "stone", bevel=0.1, band=True, extra=CUT)
    p.box((-b + 0.22, -b + 0.22, K["base_h"] - 0.02), (b - 0.22, b - 0.22, K["base_h"] + 0.3), "stone", bevel=0.06,
          band=True, extra=CUT)
    r = K["shaft_r"]
    p.lathe([(r, K["base_h"] + 0.25), (r * 0.93, top - K["cap_h"] - 0.3)], K["segments"], "stone", grain=None,
            band=True, extra=CUT)
    p.box((-c + 0.2, -c + 0.2, top - K["cap_h"] - 0.35), (c - 0.2, c - 0.2, top - K["cap_h"] + 0.02), "stone",
          bevel=0.06, extra=CUT)
    p.box((-c, -c, top - K["cap_h"]), (c, c, top), "stone", bevel=0.1, extra=CUT)
    p.seams = [(2, 0.0), (2, top)]

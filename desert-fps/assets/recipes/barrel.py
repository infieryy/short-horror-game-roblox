"""Barrel: 16 flat staves, three iron hoops, a lid set down inside the rim."""
import math

import config as C

K = C.KIT["barrel"]


def _radius(z):
    return K["r_end"] + (K["r_mid"] - K["r_end"]) * math.sin(math.pi * z / K["h"])


def build(p):
    h, rim = K["h"], 0.13
    profile = [(_radius(h * k / 6), h * k / 6) for k in range(7)]
    profile += [(K["r_end"] - rim, h), (K["r_end"] - rim, h - 0.16)]
    p.lathe(profile, K["segments"], "wood", r_ref=K["r_mid"], grain="z", extra={"staves": K["segments"], "tone": -1, "cut": True})
    p.lathe([(K["r_end"] - rim + 0.03, h - 0.3), (K["r_end"] - rim + 0.03, h - 0.12)], K["segments"], "wood", grain="x", extra={"cut": True})
    hh = K["hoop_h"] / 2
    for z in K["hoops"]:
        r = max(_radius(z - hh), _radius(z), _radius(z + hh))      # sit on the staves, never inside them
        p.lathe([(r, z - hh), (r + 0.07, z - hh), (r + 0.07, z + hh), (r, z + hh)],
                K["segments"], "iron", closed=True, grain=None, extra={"cut": True})

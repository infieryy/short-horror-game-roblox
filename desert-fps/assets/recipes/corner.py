"""Corner post: closes the notch where two wall pieces meet at a grid corner. One story tall,
with the same plinth and turquoise band as the walls. The upper-story post has neither."""
import math

import config as C
from mathutils import Matrix

K, W = C.KIT["corner"], C.KIT["wall"]


def build(p, upper=False):
    # a square post is a lathe with four sides, turned so its faces line up with the walls
    r, out = K["half"] * math.sqrt(2), (K["half"] + W["plinth_out"]) * math.sqrt(2)
    profile = [(out + 0.04, 0.0), (out, W["plinth_h"]), (r, W["plinth_h"] + W["plinth_chamfer"]), (r, C.STORY)]
    if upper:
        profile = [(r, 0.0), (r, C.STORY)]
    p.lathe(profile, 4, "plaster", group="wall", grain=None, band=not upper,
            frame=Matrix.Rotation(math.pi / 4, 4, "Z"), extra={"cut": True})
    p.seams = [(2, 0.0), (2, C.STORY)]

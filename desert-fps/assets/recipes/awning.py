"""Awning: a striped cloth on two poles, held off a wall by brackets and struts. The piece origin is on
the wall face at the foot of the brackets; the cloth slopes out and down towards -Y."""
import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Vector

from . import drape

K = C.KIT["awning"]
CUT = {"cut": True}


def build(p):
    hw, out, top, low = K["w"] / 2, K["out"], K["top"], K["top"] - K["drop"]
    for sx in (-1, 1):
        x = sx * (hw - 0.3)
        p.box((x - 0.26, -0.2, 0), (x + 0.26, 0.0, top + 0.35), "wood", bevel=0.04, grain="z", extra=CUT)
        # strut from the foot of the bracket out to the front pole
        a, b = Vector((x, -0.18, 0.3)), Vector((x, -out + 0.05, low - 0.1))
        mid, half = (a + b) / 2, (b - a).length / 2
        p.box((-half, -0.11, -0.11), (half, 0.11, 0.11), "darkwood", grain="x", extra=CUT,
              frame=frame_axes(mid, b - a, (1, 0, 0)))
    for y, z in ((-0.36, top), (-out, low)):                   # wall pole and front pole, along X
        p.lathe([(0.14, 0.0), (0.14, K["w"] + 0.5)], 8, "wood", grain="z", extra=CUT,
                frame=frame_axes((-hw - 0.25, y, z), (0, 1, 0), (0, 0, 1)))
    path = drape.sag((-0.3, top + 0.25), (-out - 0.2, low + 0.25), 0.14)
    path += [(-out - 0.32, low + 0.06), (-out - 0.35, low + 0.25 - K["valance"])]
    drape.stripes(p, path, -hw - 0.1, hw + 0.1, K["stripes"])

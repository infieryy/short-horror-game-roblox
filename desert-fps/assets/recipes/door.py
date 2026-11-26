"""Door leaf: planks, iron straps with studs, ring handle, ledgers and a brace on the back."""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Vector

K = C.KIT["door"]


def build(p):
    w, h, t = K["w"], K["h"], K["t"] / 2
    plank = w / K["planks"]
    for i in range(K["planks"]):
        p.box((-w / 2 + i * plank, -t, 0), (-w / 2 + (i + 1) * plank, t, h), "darkwood", bevel=0.035, grain="z")
    for z in K["strap_z"]:
        p.box((-w / 2 + 0.05, -t - 0.05, z), (w / 2 - 0.05, -t + 0.02, z + K["strap_h"]), "iron")
        for i in range(K["planks"]):
            x = -w / 2 + (i + 0.5) * plank
            p.box((-0.06, -0.06, 0), (0.06, 0.06, 0.045), "iron", group="stud", detail=True,
                  frame=frame_axes((x, -t - 0.05, z + K["strap_h"] / 2), (1, 0, 0), (0, 0, 1)))
        p.box((-w / 2 + 0.1, t - 0.02, z - 0.1), (w / 2 - 0.1, t + 0.09, z + K["strap_h"] + 0.1), "darkwood",
              bevel=0.025, grain="x")
    # brace on the back, between the two ledgers
    a = Vector((-w / 2 + 0.35, 0, K["strap_z"][0] + K["strap_h"] + 0.1))
    b = Vector((w / 2 - 0.35, 0, K["strap_z"][1] - 0.1))
    d = (b - a).normalized()
    mid = (a + b) / 2
    half = (b - a).length / 2
    p.box((-half, 0, -0.16), (half, 0.085, 0.16), "darkwood", grain="x",
          frame=frame_axes((mid.x, t - 0.02, mid.z), d, (0, 1, 0)))
    # ring handle
    ring, tube, n = 0.3, 0.045, 6
    profile = [(ring + tube * math.cos(2 * math.pi * k / n), tube * math.sin(2 * math.pi * k / n)) for k in range(n)]
    hx, hz = w / 2 - 0.62, 3.7
    p.lathe(profile, 12, "iron", closed=True, grain=None, frame=frame_axes((hx, -t - 0.07, hz), (1, 0, 0), (0, 0, 1)))
    p.box((hx - 0.09, -t - 0.16, hz + ring - 0.1), (hx + 0.09, -t + 0.02, hz + ring + 0.14), "iron")

"""Wall pieces: one story tall, one grid cell wide. Plain, with a window, or with a doorway."""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Vector

K = C.KIT["wall"]
HALF, T = C.CELL / 2, C.WALL_T / 2


def _front(z):
    """Front surface: a slightly battered plinth that the turquoise band is painted on."""
    if z <= K["plinth_h"]:
        return -T - K["plinth_out"] - 0.03 * (1 - z / K["plinth_h"])
    return -T


def _beams(p):
    b = K["beams"]
    length = 0.25 + T + b["out"]
    r = b["radius"]
    for i in range(b["count"]):
        x = -HALF + (i + 0.5) * C.CELL / b["count"]
        frame = frame_axes((x, 0.25, b["z"]), (1, 0, 0), (0, 0, 1))          # local Z points out of the wall
        p.lathe([(r * 0.96, 0.0), (r, 0.3), (r, length - 0.06), (r - 0.06, length)], b["segments"], "wood",
                frame=frame, grain="z")


def _window(p, x0, x1, z0, z1):
    w = K["window"]
    for lo_z, hi_z in ((z1 - 0.05, z1 + w["board_h"]), (z0 - w["board_h"], z0 + 0.05)):
        p.box((x0 - w["board_over"], -T - w["board_out"], lo_z), (x1 + w["board_over"], -T + 0.1, hi_z),
              "wood", bevel=0.03, grain="x", extra={"chunk": "window"})
        for sx in (x0 - w["board_over"] + 0.22, x1 + w["board_over"] - 0.22):
            mid = (lo_z + hi_z) / 2
            p.box((-0.07, -0.07, 0), (0.07, 0.07, 0.05), "iron", group="stud", detail=True, extra={"chunk": "window"},
                  frame=frame_axes((sx, -T - w["board_out"], mid), (1, 0, 0), (0, 0, 1)))
    # mashrabiya lattice: two sets of diagonal bars, the second 1/20 stud behind the first
    cx, cz, m = (x0 + x1) / 2, (z0 + z1) / 2, 0.22
    reach = (x1 - x0 + z1 - z0) / 2
    for s, (dx, dz) in enumerate(((1, 1), (1, -1))):
        d = Vector((dx, 0, dz)).normalized()
        n = Vector((-d.z, 0, d.x))
        y = -T + w["inset"] + s * (w["bar"] + 0.05)
        k = -int(reach / w["bar_gap"])
        while k * w["bar_gap"] <= reach:
            o = Vector((cx, 0, cz)) + n * (k * w["bar_gap"])
            lo, hi = -1e9, 1e9                                   # clip the bar's line to the opening (+ margin)
            for oc, dc, a, b in ((o.x, d.x, x0 - m, x1 + m), (o.z, d.z, z0 - m, z1 + m)):
                t0, t1 = sorted(((a - oc) / dc, (b - oc) / dc))
                lo, hi = max(lo, t0), min(hi, t1)
            if hi - lo > 0.5:
                mid = o + d * ((lo + hi) / 2)
                half = (hi - lo) / 2
                p.box((-half, -w["bar"] / 2, -w["bar"] / 2), (half, w["bar"] / 2, w["bar"] / 2), "darkwood",
                      group=f"lattice{s}", grain="x", frame=frame_axes((mid.x, y, mid.z), d, (0, 1, 0)),
                      extra={"chunk": "window"})
            k += 1


def _doorway(p, x0, x1, z1):
    d = K["door"]
    block_h = (z1 - 0.06) / d["jamb_blocks"]        # the lintel rests on the jambs
    for side, edge in ((-1, x0), (1, x1)):
        xa, xb = sorted((edge - side * 0.06, edge + side * d["jamb_w"]))
        for i in range(d["jamb_blocks"]):
            p.box((xa, -T - d["jamb_out"], i * block_h - (0.06 if i == 0 else 0)), (xb, T + d["jamb_out"], (i + 1) * block_h), "stone",
                  bevel=0.08, band=True)
    p.box((x0 - d["lintel_over"], -T - d["jamb_out"] - 0.05, z1 - 0.06),
          (x1 + d["lintel_over"], T + d["jamb_out"] + 0.05, z1 + d["lintel_h"]), "wood", bevel=0.05, grain="x",
          extra={"chunk": "lintel"})


def build(p, opening=None, beams=True):
    zs = {0.0, K["plinth_h"], K["plinth_h"] + K["plinth_chamfer"], C.STORY}
    xs, holes = [-HALF, HALF], []
    if opening == "window":
        w = K["window"]
        x0, x1, z0, z1 = -w["w"] / 2, w["w"] / 2, w["sill"], w["sill"] + w["h"]
    elif opening == "door":
        d = K["door"]
        x0, x1, z0, z1 = -d["w"] / 2, d["w"] / 2, 0.0, d["h"]
    if opening:
        xs = [-HALF, x0, x1, HALF]
        zs |= {z0, z1}
    zs = sorted(zs)
    if opening:
        holes = [(1, j) for j in range(len(zs) - 1) if z0 <= zs[j] and zs[j + 1] <= z1]
    p.wall(xs, zs, _front, lambda z: T, holes, extra={"cut": True})
    p.seams = [(0, -HALF), (0, HALF), (2, 0.0), (2, C.STORY)]
    if beams:
        _beams(p)
    if opening == "window":
        _window(p, x0, x1, z0, z1)
    elif opening == "door":
        _doorway(p, x0, x1, z1)

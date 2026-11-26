"""Stairs: one grid cell, climbing one story towards +Y. A solid stepped block of plaster with the
turquoise band, and a stone tread on every step."""
import config as C
from build import frame_axes  # build loads bpy before mathutils

K = C.KIT["stairs"]
HALF = C.CELL / 2
CUT = {"cut": True}


def build(p):
    n = K["steps"]
    run, rise = C.CELL / n, C.STORY / n
    frame = frame_axes((0, 0, 0), (0, 1, 0), (-1, 0, 0))            # X of the profile is the way up the stairs
    profile = [(-HALF, 0.0)]
    for i in range(n):
        profile += [(-HALF + i * run, (i + 1) * rise), (-HALF + (i + 1) * run, (i + 1) * rise)]
    profile.append((HALF, 0.0))
    p.extrude(profile, HALF, "plaster", group="wall", band=True, frame=frame, extra=CUT)
    for i in range(n):
        x0, z = -HALF + i * run, (i + 1) * rise
        p.box((x0 - K["tread_over"], -HALF + K["tread_in"], z), (x0 + run, HALF - K["tread_in"], z + K["tread_t"]),
              "stone", bevel=0.03, group="tread", frame=frame, extra=CUT)
    p.seams = [(2, 0.0)]

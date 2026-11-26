"""Stairs: one grid cell long, climbing one story towards +Y. A solid stepped block of plaster with the
turquoise band, and a stone tread on every step. The full flight fills its cell; the narrow one is half
as wide, so it can stand along a wall and leave the other half of the cell to walk past."""
import config as C
from build import frame_axes  # build loads bpy before mathutils

K = C.KIT["stairs"]
HALF = C.CELL / 2
CUT = {"cut": True}


def build(p, narrow=False):
    n = K["steps"]
    half = K["narrow_w"] / 2 if narrow else HALF
    run, rise = C.CELL / n, C.STORY / n
    frame = frame_axes((0, 0, 0), (0, 1, 0), (-1, 0, 0))            # X of the profile is the way up the stairs
    profile = [(-HALF, 0.0)]
    for i in range(n):
        profile += [(-HALF + i * run, (i + 1) * rise), (-HALF + (i + 1) * run, (i + 1) * rise)]
    profile.append((HALF, 0.0))
    p.extrude(profile, half, "plaster", group="wall", band=True, frame=frame, extra=CUT)
    for i in range(n):
        x0, z = -HALF + i * run, (i + 1) * rise
        p.box((x0 - K["tread_over"], -half + K["tread_in"], z), (x0 + run, half - K["tread_in"], z + K["tread_t"]),
              "stone", bevel=0.03, group="tread", frame=frame, extra=CUT)
    p.seams = [(2, 0.0)]

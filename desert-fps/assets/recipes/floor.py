"""Floors you can look up at, and the dome.

floor: one grid cell of upper floor or roof terrace. Flagstones on top; underneath, planks on three
square beams, so a room has a real ceiling. Sits on the wall tops like the plain roof slab.
dome: the same cell with a round opening, a drum on it and a plaster dome with a brass finial. From the
room below you look up into the dome."""
import math

import config as C
from build import frame_axes  # build loads bpy before mathutils

from . import ground

K = C.KIT["floor"]
D = C.KIT["dome"]
HALF = C.CELL / 2
CUT = {"cut": True}
SEAMS = [(0, -HALF), (0, HALF), (1, -HALF), (1, HALF)]


def build(p):
    t, planks = K["t"], K["planks_t"]
    top = p.box((-HALF, -HALF, planks), (HALF, HALF, t), "paving", group="top", extra=CUT)
    ground.joints(p, top, t, seed=3)
    under = p.box((-HALF, -HALF, 0), (HALF, HALF, planks), "wood", group="planks", grain="x", extra=CUT)
    boards = K["boards"]
    for k in range(1, boards):
        y = -HALF + k * C.CELL / boards
        p.mark(under, "-z", [(-HALF, y, 0), (HALF, y, 0)], tone=-3, width=0.05)
    w, drop = K["beam_w"] / 2, K["beam_drop"]
    for i in range(K["beams"]):
        x = -HALF + (i + 0.5) * C.CELL / K["beams"]
        p.box((x - w, -HALF, -drop), (x + w, HALF, 0), "darkwood", group=f"beam{i}", grain="y", extra=CUT)
    p.seams = SEAMS


def dome(p):
    t, r_in, r_out, h = D["slab_t"], D["r_in"], D["r_out"], D["drum_h"]
    n = D["segments"]
    arc = [(r_in * math.cos(math.radians(180 * k / 12)), r_in * math.sin(math.radians(180 * k / 12))) for k in range(13)]
    half = [(-HALF, 0), (-HALF, HALF), (HALF, HALF), (HALF, 0)] + arc
    flat = frame_axes((0, 0, t / 2), (1, 0, 0), (0, 0, 1))            # the outline lies flat; thickness is up
    for s in (1, -1):
        p.extrude([(x, s * z) for x, z in half], t / 2, "paving", group="slab", frame=flat, extra=CUT)
    drum = p.lathe([(r_out, t), (r_out, t + h), (r_in, t + h), (r_in, t)], n, "plaster", closed=True, grain=None,
                   group="drum", smooth=True, extra={**CUT, "tone": 1})
    # blind arches round the drum: painted, not cut
    around, half, foot, spring = 2 * math.pi * r_out, 0.7, 1.2, h - D["cornice_h"] - 1.9
    for k in range(8):
        c = (k + 0.5) / 8
        arch = [(c + half * math.cos(math.radians(a)) / around, spring + half * math.sin(math.radians(a)))
                for a in range(180, -1, -30)]
        p.mark(drum, "lathe", [(c - half / around, foot)] + arch + [(c + half / around, foot)], tone=-4, width=0.1,
               closed=True)
    a, b = t + h - D["cornice_h"], t + h
    ring = p.lathe([(r_out + D["cornice_out"], a), (r_out + D["cornice_out"], b), (r_out, b), (r_out, a)], n, "stone",
                   closed=True, grain=None, group="cornice", extra=CUT)
    teeth = n
    p.mark(ring, "lathe", [(k / (2 * teeth), 0.1 if k % 2 == 0 else D["cornice_h"] - 0.1) for k in range(2 * teeth + 1)],
           width=0.09, family="band")
    # the shell: outside curve up to a small hole at the top, inside curve back down
    zd, steps = t + h, 9
    ao, bo, ai, bi, hole = D["shell_r"], D["shell_h"], r_in, D["inner_h"], D["hole"]
    top_o, top_i = math.acos(hole / ao), math.acos(hole / ai)
    profile = [(ao * math.cos(top_o * k / steps), zd + bo * math.sin(top_o * k / steps)) for k in range(steps + 1)]
    profile += [(ai * math.cos(top_i * k / steps), zd + bi * math.sin(top_i * k / steps)) for k in range(steps, -1, -1)]
    p.lathe(profile, n, "plaster", closed=True, grain=None, group="dome", smooth=True, extra={**CUT, "tone": 3})
    zt = zd + bo * math.sin(top_o)
    p.lathe([(hole - 0.05, zt - 1.9), (hole - 0.05, zt), (0.7, zt + 0.25), (0.36, zt + 0.6), (0.55, zt + 1.05),
             (0.16, zt + 1.8), (0.04, zt + 2.6)], 8, "brass", grain=None, group="finial", smooth=True)
    p.seams = SEAMS + [(1, 0.0)]


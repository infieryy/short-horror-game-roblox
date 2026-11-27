"""Tree: a small orange tree in a stone planter, for courts and yards. One grid cell. The planter and the
trunk are what you walk round; the crown is overhead, a cluster of leaf clumps with a few fruit."""
import math
import random

from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix

CUT = {"cut": True}


def build(p):
    a, h = 1.7, 1.6
    p.box((-a, -a, 0), (a, a, h), "stone", bevel=0.08, group="planter", band=True, extra=CUT)
    p.box((-a - 0.12, -a - 0.12, h), (a + 0.12, a + 0.12, h + 0.3), "stone", bevel=0.05, group="rim", extra={**CUT, "tone": 3})
    p.box((-a + 0.35, -a + 0.35, h + 0.3), (a - 0.35, a - 0.35, h + 0.42), "darkwood", group="soil")
    p.lathe([(0.5, h + 0.42), (0.4, 3.2), (0.34, 5.2), (0.28, 6.8)], 8, "wood", grain="z", group="trunk", extra=CUT)
    for i, (turn, lift) in enumerate(((20, 38), (140, 44), (255, 35))):          # three boughs
        direction = Matrix.Rotation(math.radians(turn), 3, "Z") @ Matrix.Rotation(math.radians(-lift), 3, "Y")
        along = direction @ Matrix.Identity(3).col[0]
        frame = frame_axes((0, 0, 5.6 + 0.4 * i), tuple(along), (-along.y, along.x, 0))
        p.box((0.0, -0.13, -0.13), (2.6, 0.13, 0.13), "wood", grain="x", group=f"bough{i}", frame=frame)
    rng = random.Random(9)
    centre = 8.7
    for i in range(30):
        # clumps scattered through a flattened ball; more of them near the outside
        u, turn = rng.uniform(-1, 1), rng.uniform(0, 2 * math.pi)
        reach = rng.uniform(0.45, 1.0) ** 0.6
        flat = math.sqrt(1 - u * u) * reach
        x, y, z = 3.1 * flat * math.cos(turn), 3.1 * flat * math.sin(turn), centre + 2.0 * u * reach
        r = rng.uniform(0.95, 1.5)
        profile = [(r * math.sin(math.radians(k)), -0.75 * r * math.cos(math.radians(k))) for k in (20, 55, 90, 125, 160)]
        frame = (Matrix.Translation((x, y, z)) @ Matrix.Rotation(rng.uniform(0, 6.28), 4, "Z")
                 @ Matrix.Rotation(rng.uniform(-0.4, 0.4), 4, "X"))
        p.lathe(profile, 8, "leaf", grain=None, group=f"clump{i}", frame=frame, smooth=True, extra={"tone": rng.randint(-1, 1)})
    for i in range(9):                                                  # oranges, hanging under the crown's edge
        turn = rng.uniform(0, 2 * math.pi)
        reach = rng.uniform(2.0, 3.3)
        at = (reach * math.cos(turn), reach * math.sin(turn), centre - rng.uniform(1.2, 2.2))
        p.lathe([(0.24 * math.sin(math.radians(k)), -0.24 * math.cos(math.radians(k))) for k in (25, 90, 155)], 6, "glow",
                grain=None, group=f"fruit{i}", frame=Matrix.Translation(at), smooth=True, detail=True)

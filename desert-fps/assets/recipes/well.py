"""Well: a ring of stone blocks with a turquoise foot, two posts, a log across them with the rope
wound round it, and a bucket hanging over the shaft. The joints between the blocks are painted."""
import config as C
from build import frame_axes  # build loads bpy before mathutils

K = C.KIT["well"]
CUT = {"cut": True}


def build(p):
    r0, r1, h, n = K["r_in"], K["r_out"], K["h"], K["segments"]
    lip = 0.32
    ring = p.lathe([(r1, 0.0), (r1, h - lip), (r1 + 0.1, h - lip), (r1 + 0.1, h), (r0 - 0.1, h), (r0 - 0.1, h - lip),
                    (r0, h - lip), (r0, 0.0)], n, "stone", closed=True, grain=None, extra=CUT)
    # block joints on the outside: two level courses, upright joints staggered from course to course
    courses = [0.0, (h - lip) * 0.36, (h - lip) * 0.7, h - lip]
    for along in courses[1:-1]:
        p.mark(ring, "lathe", [(k / n, along) for k in range(n + 1)], tone=-3, width=0.045)
    for c, (a, b) in enumerate(zip(courses, courses[1:])):
        for k in range(0, n, 2):
            turn = (k + (c % 2)) / n
            p.mark(ring, "lathe", [(turn, a + 0.03), (turn, b - 0.03)], tone=-3, width=0.045)
    # the painted foot: a skirt outside the ring, so the two never share a face
    p.lathe([(r1 + 0.1, 0.0), (r1 + 0.1, 0.5), (r1 + 0.01, 0.62), (r1 + 0.01, 0.0)], n, "band",
            closed=True, grain=None, group="foot", extra=CUT)

    mid, top = (r0 + r1) / 2, h + K["post_h"]
    for sx in (-1, 1):
        p.box((sx * mid - 0.22, -0.22, h - 0.05), (sx * mid + 0.22, 0.22, top), "wood", bevel=0.04, grain="z", extra=CUT)
    z = K["beam_z"]
    p.lathe([(0.25, 0.0), (0.27, 0.3), (0.27, 2 * mid + 0.9), (0.25, 2 * mid + 1.2)], 10, "wood", grain="z", extra=CUT,
            frame=frame_axes((-mid - 0.6, 0, z), (0, 1, 0), (0, 0, 1)))
    p.lathe([(0.3, 0.0), (0.36, 0.08), (0.36, 1.02), (0.3, 1.1)], 10, "rope", group="coil",
            frame=frame_axes((-0.55, 0, z), (0, 1, 0), (0, 0, 1)))
    bucket_top = h + 1.9
    p.box((-0.045, -0.4, bucket_top + 0.25), (0.045, -0.31, z), "rope", group="line")
    p.box((-0.34, -0.39, bucket_top + 0.2), (0.34, -0.32, bucket_top + 0.3), "iron", group="bail", detail=True)
    p.lathe([(0.4, bucket_top - 0.85), (0.52, bucket_top), (0.44, bucket_top), (0.38, bucket_top - 0.6)], 10, "wood",
            grain="z", frame=frame_axes((0, -0.35, 0), (1, 0, 0), (0, 1, 0)), extra={"staves": 10, "tone": -1})
    p.lathe([(0.5, bucket_top - 0.2), (0.545, bucket_top - 0.2), (0.545, bucket_top - 0.08), (0.515, bucket_top - 0.08)],
            10, "iron", closed=True, grain=None, group="hoop", frame=frame_axes((0, -0.35, 0), (1, 0, 0), (0, 1, 0)))

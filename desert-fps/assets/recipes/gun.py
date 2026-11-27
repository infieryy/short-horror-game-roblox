"""Shared toolkit for firearms. Every gun is modular:

 - it is built as named parts (body, stock, grip, barrel, muzzle, magazine, bolt or slide, trigger...)
   and each part is exported as its own mesh, so it can be animated, rigged or swapped for an attachment;
 - sockets mark where attachments go (muzzle, optic, underbarrel, side, magazine) and where the sights line up;
 - joints say how the moving parts move (slide, hinge, detach).

Shapes are side-view outlines in millimetres taken from the real gun: x runs toward the muzzle,
z is height above the bore. All guns share one scale (config.GUN_MM), so they are in proportion
to each other. `chunky` thickens a gun a little over the real widths so it reads on screen.
"""
import config as C
from build import frame_axes  # build loads bpy before mathutils
from mathutils import Matrix

MM = C.GUN_MM


class Gun:
    def __init__(self, piece, origin, chunky):
        self.p, self.origin, self.chunky = piece, origin, chunky

    # ---- millimetres to studs
    def pt(self, x, z):
        return ((x - self.origin[0]) * MM, (z - self.origin[1]) * MM)

    def at(self, x, z, y=0.0):
        px, pz = self.pt(x, z)
        return (px, y, pz)

    def outline(self, points):
        return [self.pt(x, z) for x, z in points]

    def half(self, width):
        """Half thickness in studs for a real width in millimetres."""
        return width * MM * self.chunky / 2

    @staticmethod
    def _tags(part, tone, more=None):
        tags = dict(more or {})
        if part != "body":
            tags["chunk"] = part
        if tone:
            tags["tone"] = tone
        return tags

    # ---- shapes
    def shape(self, part, mat, points, width, bevel=0.0, segments=1, grain="x", tone=0):
        """A side outline pushed through `width` mm, centred on the gun."""
        return self.p.extrude(self.outline(points), self.half(width), mat, bevel=bevel * MM, segments=segments,
                              grain=grain, extra=self._tags(part, tone))

    def plate(self, part, mat, points, side, on, thick, bevel=0.0, grain="x", tone=0, sink=0.0):
        """A thin outline lying on one side (-1 right, +1 left) of a part that is `on` mm wide."""
        centre = side * (self.half(on) + (thick / 2 - sink) * MM)
        return self.p.extrude(self.outline(points), thick * MM / 2, mat, bevel=bevel * MM, grain=grain,
                              frame=Matrix.Translation((0, centre, 0)), extra=self._tags(part, tone))

    def tube(self, part, mat, x0, x1, z, radius, segments=10, tone=0, profile=None, smooth=True, out=0.0):
        """A round part along the barrel, `out` mm to the left of the gun's middle. profile: optional
        (radius factor, mm from x0) points."""
        r = radius * MM * self.chunky
        points = [(r * k, d * MM) for k, d in profile] if profile else [(r, 0), (r, (x1 - x0) * MM)]
        px, pz = self.pt(x0, z)
        return self.p.lathe(points, segments, mat, smooth=smooth, extra=self._tags(part, tone),
                            frame=frame_axes((px, out * MM, pz), (0, 1, 0), (0, 0, 1)))

    def muzzle(self, part, mat, x0, x1, z, radius, bore, depth, flare=1.0, tone=0, out=0.0):
        """The open end of a barrel: a ring from x0 to x1 with a dark bore `depth` mm inside it, `out` mm to
        the left of the gun's middle."""
        r, b, length = radius * MM * self.chunky, bore * MM * self.chunky, (x1 - x0) * MM
        px, pz = self.pt(x0, z)
        self.p.lathe([(b, 0), (r * flare, 0), (r * flare, length * 0.7), (r, length), (b, length)], 12, mat, closed=True,
                     smooth=True, extra=self._tags(part, tone), frame=frame_axes((px, out * MM, pz), (0, 1, 0), (0, 0, 1)))
        px, pz = self.pt(x1 - depth - 1.0, z)
        self.p.lathe([(b * 1.03, 0), (b * 1.03, 1.0 * MM)], 12, "bore", grain=None, extra=self._tags(part, 0),
                     frame=frame_axes((px, out * MM, pz), (0, 1, 0), (0, 0, 1)))

    def stud(self, part, mat, x, z, side, on, radius=3.6, height=1.6):
        """A rivet or screw head on one side of a part that is `on` mm wide."""
        px, pz = self.pt(x, z)
        return self.p.lathe([(radius * MM, 0), (radius * 0.9 * MM, height * MM)], 6, mat, group="rivet", grain=None,
                            detail=True, extra=self._tags(part, 0),
                            frame=frame_axes((px, side * self.half(on), pz), (1, 0, 0), (0, 0, -side)))

    # ---- painted detail
    def line(self, pid, points, sides=("-y", "+y"), tone=-4, width=2.0, closed=False):
        """A painted line on the side faces of a part (panel line, slot, hatching)."""
        for facet in sides:
            self.p.mark(pid, facet, [self.at(x, z) for x, z in points], tone, width * MM, closed)

    def across(self, pid, x, z, reach, facet="+z", tone=-4, width=2.0):
        """A painted line across the top (or bottom) of a part, `reach` mm to each side."""
        self.p.mark(pid, facet, [self.at(x, z, -reach * MM), self.at(x, z, reach * MM)], tone, width * MM)

    # ---- rigging
    def socket(self, name, x, z, forward=(1, 0, 0), up=(0, 0, 1), side=0, on=0.0, out=0.0):
        """A named point for attachments and aiming. On the gun's middle, or with `side` (+1 left, -1 right) on
        the face of a part that is `on` mm wide, `out` mm beyond it."""
        self.p.sockets.append({"name": name, "position": self.at(x, z, side * (self.half(on) + out * MM)),
                               "forward": forward, "up": up})

    def joint(self, part, kind, x, z, axis, amount):
        """How a part moves. kind: "slide" (amount in mm along axis), "hinge" (degrees about axis),
        "detach" (pulls out along axis)."""
        self.p.joints.append({"part": part, "type": kind, "pivot": self.at(x, z), "axis": axis,
                              "amount": amount * MM if kind == "slide" else amount,
                              "unit": {"slide": "studs", "hinge": "degrees", "detach": "direction"}[kind]})

"""Crate: frame boards, inset planks at two depths, one diagonal brace per face, corner studs."""
import math

import config as C
from build import FACETS, frame_axes  # build loads bpy before mathutils
from mathutils import Matrix

K = C.KIT["crate"]
CUT = {"cut": True}        # sliced along the break lines


def build(p):
    s, o, w = K["size"], K["frame_out"], K["frame_w"]
    h = s / 2
    p.box((-h + o, -h + o, 0), (h - o, h - o, s - o), "darkwood", extra=CUT)
    # dark sticks along the cube's edges close the tiny gaps where three bevelled boards meet
    a, b = h - o - 0.05, h - 0.035
    for sx in (-1, 1):
        for sy in (-1, 1):
            p.box((min(sx * a, sx * b), min(sy * a, sy * b), 0.035), (max(sx * a, sx * b), max(sy * a, sy * b), s - 0.035), "darkwood", extra=CUT)
        p.box((min(sx * a, sx * b), -b, s - o - 0.05), (max(sx * a, sx * b), b, s - 0.035), "darkwood", extra=CUT)
        p.box((-b, min(sx * a, sx * b), s - o - 0.05), (b, max(sx * a, sx * b), s - 0.035), "darkwood", extra=CUT)
    # X faces span the full cube; Y faces and the top stop short so no two boards share a plane
    faces = [("+x", (h - o, 0, h), h, h), ("-x", (-h + o, 0, h), h, h),
             ("+y", (0, h - o, h), h - o, h), ("-y", (0, -h + o, h), h - o, h),
             ("+z", (0, 0, s - o), h - o, h - o)]
    for index, (facet, origin, ea, eb) in enumerate(faces):
        U, V = FACETS[facet]
        face = frame_axes(origin, U, V)

        def board(lo, hi, extra=None, **kw):
            p.box(lo, hi, "wood", frame=face, extra={**CUT, **(extra or {})}, **kw)

        board((-ea, -eb, 0), (ea, -eb + w, o), bevel=0.03, grain="x")
        board((-ea, eb - w, 0), (ea, eb, o), bevel=0.03, grain="x")
        board((-ea, -eb + w, 0), (-ea + w, eb - w, o), bevel=0.03, grain="y")
        board((ea - w, -eb + w, 0), (ea, eb - w, o), bevel=0.03, grain="y")
        inner = 2 * (ea - w)
        for i in range(K["planks"]):
            x0 = -ea + w + i * inner / K["planks"]
            board((x0, -eb + w, 0), (x0 + inner / K["planks"], eb - w, o * (0.38 if i % 2 else 0.24)), grain="y",
                  extra={"tone": -3})
        flip = -1 if index % 2 else 1
        dx, dy = inner, 2 * (eb - w)
        angle = math.atan2(dy, dx * flip)
        brace = face @ Matrix.Rotation(angle, 4, "Z")
        p.box((-math.hypot(dx, dy) / 2 - 0.15, -0.17, 0), (math.hypot(dx, dy) / 2 + 0.15, 0.17, o * 0.74), "wood",
              frame=brace, grain="x", extra={"tone": -1, **CUT})
        for sx in (-1, 1):
            for sy in (-1, 1):
                stud = face @ Matrix.Translation((sx * (ea - w / 2), sy * (eb - w / 2), o - 0.02))
                p.box((-0.06, -0.06, 0), (0.06, 0.06, 0.065), "iron", group="stud", frame=stud, detail=True)

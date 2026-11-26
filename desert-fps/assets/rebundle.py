"""Rewrite the Roblox files of finished pieces from their .obj meshes, without rebuilding or repainting.

    python3 rebundle.py                 # every piece in out/
    python3 rebundle.py crate barrel    # some pieces

Per piece, rewrites every .fbx next to its .obj and writes <piece>.bundle.fbx: the whole mesh, the
low-detail mesh and every shard or part as separate objects in one file, so the piece is one upload.

Use this instead of run.py when only the export settings changed: run.py repaints, and a repaint on
another machine is not pixel-identical (the texture layout shifts with tiny rounding differences).
"""
import os
import sys

import bpy

from build import matte_material, write_fbx

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")


def load(path, material):
    bpy.ops.wm.obj_import(filepath=path, forward_axis="NEGATIVE_Z", up_axis="Y")
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)   # bake the importer's axis turn
    obj.name = obj.data.name = os.path.splitext(os.path.basename(path))[0]
    obj.data.materials.clear()
    obj.data.materials.append(material)
    return obj


def rebundle(name):
    folder = os.path.join(OUT, name)
    paths = [os.path.join(folder, name + ".obj"), os.path.join(folder, name + "_low.obj")]
    for sub in ("chunks", "parts"):
        if os.path.isdir(os.path.join(folder, sub)):
            paths += sorted(os.path.join(folder, sub, f) for f in os.listdir(os.path.join(folder, sub))
                            if f.endswith(".obj"))
    bpy.ops.wm.read_factory_settings(use_empty=True)
    material = matte_material(name, os.path.join(folder, name + ".png"))
    objects = [load(path, material) for path in paths]
    for path, obj in zip(paths, objects):
        write_fbx(path[:-4] + ".fbx", [obj])
    write_fbx(os.path.join(folder, name + ".bundle.fbx"), objects)
    return len(objects)


if __name__ == "__main__":
    names = sys.argv[1:] or sorted(n for n in os.listdir(OUT) if os.path.isfile(os.path.join(OUT, n, n + ".obj")))
    for name in names:
        print(f"{name:12s} {rebundle(name)} meshes")

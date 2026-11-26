"""Render the finished pieces together and put the render next to the concept art.

    python3 preview.py            # out/preview.png and out/compare.png
"""
import math
import os

import bpy
from mathutils import Vector
from PIL import Image

import config as C
from build import matte_material

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
REF = os.path.join(HERE, "..", "reference")

# piece, position (studs), rotation about Z (degrees)
SCENE = [
    ("wall_plain", (-8, 0, 0), 0), ("wall_window", (0, 0, 0), 0), ("wall_door", (8, 0, 0), 0),
    ("door", (8 - 1.95 + 1.6, -1.15, 0), -42),
    ("crate", (-6.5, -4.2, 0), 18), ("barrel", (-3.2, -3.4, 0), 0), ("barrel", (-9.6, -3.0, 0), 40),
    ("crate", (2.6, -4.6, 0), -12),
]
CAMERAS = {"preview": ((7.5, -27, 7.5), (0.2, 0, 5.2), 38), "front": ((-4, -30, 6), (-4, 0, 6), 50),
           "close": ((-1.5, -11, 4.2), (-4.5, 0, 3.4), 35)}


def load(name):
    folder = os.path.join(OUT, name)
    bpy.ops.wm.obj_import(filepath=os.path.join(folder, name + ".obj"), forward_axis="NEGATIVE_Z", up_axis="Y")
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)   # bake the importer's axis turn
    obj.data.materials.clear()
    obj.data.materials.append(matte_material(name, os.path.join(folder, name + ".png")))
    return obj


def render(camera, path, size=(1600, 900), samples=48):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, pos, rot in SCENE:
        obj = load(name)
        obj.location, obj.rotation_euler = pos, (0, 0, math.radians(rot))
    bpy.ops.mesh.primitive_plane_add(size=400)
    ground = bpy.data.materials.new("ground")
    ground.use_nodes = True
    bsdf = ground.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = (0.85, 0.52, 0.40, 1)
    bsdf.inputs["Roughness"].default_value = 1.0
    bpy.context.object.data.materials.append(ground)
    # late-afternoon sun, slightly dim; lavender-blue ambient for the shade
    bpy.ops.object.light_add(type="SUN", rotation=(math.radians(52), 0, math.radians(-38)))
    sun = bpy.context.object.data
    sun.energy, sun.color, sun.angle = 3.0, (1.0, 0.93, 0.82), math.radians(2)
    world = bpy.data.worlds.new("sky")
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.62, 0.60, 0.95, 1)
    world.node_tree.nodes["Background"].inputs["Strength"].default_value = 0.32
    scene.world = world
    eye, target, lens = CAMERAS[camera]
    bpy.ops.object.camera_add(location=eye)
    cam = bpy.context.object
    cam.rotation_euler = (Vector(target) - Vector(eye)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    scene.camera = cam
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.render.resolution_x, scene.render.resolution_y = size
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)


def compare(render_path, out_path):
    """Concept art on the left, our render on the right: same artist, same day?"""
    ours = Image.open(render_path).convert("RGB")
    concept = Image.open(os.path.join(REF, "concept", "02-market-street-level.webp")).convert("RGB")
    kit = Image.open(os.path.join(REF, "kit", "walls.webp")).convert("RGB")
    h = ours.height
    left_w = int(concept.width * (h / 2) / concept.height)
    sheet = Image.new("RGB", (left_w + ours.width, h), (250, 244, 236))
    sheet.paste(concept.resize((left_w, h // 2)), (0, 0))
    kit = kit.resize((left_w, int(kit.height * left_w / kit.width)))
    sheet.paste(kit, (0, h // 2 + (h // 2 - kit.height) // 2))
    sheet.paste(ours, (left_w, 0))
    sheet.save(out_path)


if __name__ == "__main__":
    render("preview", os.path.join(OUT, "preview.png"))
    render("close", os.path.join(OUT, "preview-close.png"))
    compare(os.path.join(OUT, "preview.png"), os.path.join(OUT, "compare.png"))

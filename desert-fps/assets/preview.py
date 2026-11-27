"""Render the finished pieces together and put the render next to the concept art.

    python3 preview.py            # out/preview.png, out/preview-close.png, out/compare.png, out/broken.png
    python3 preview.py building props   # out/preview-building.png, out/preview-props.png (any camera name)
"""
import json
import math
import os

import bpy
from mathutils import Matrix, Vector
from PIL import Image

import config as C
from build import matte_material
from buildings import cistern, courtyard, dyeworks, teahouse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
REF = os.path.join(HERE, "..", "reference")

# piece, position (studs), rotation about Z (degrees), options
#   {"blast": [(x, height, radius)]}  build the piece from its shards, minus those a blast would remove
#   {"without": [shard ids]}          leave these out too
#   {"explode": distance}             show the shards pushed apart
SCENES = {
    "whole": [
        ("wall_plain", (-8, 0, 0), 0, {}), ("wall_window", (0, 0, 0), 0, {}), ("wall_door", (8, 0, 0), 0, {}),
        ("door", (8 - 1.95 + 1.6, -1.15, 0), -42, {}),
        ("crate", (-6.5, -4.2, 0), 18, {}), ("barrel", (-3.2, -3.4, 0), 0, {}), ("barrel", (-9.6, -3.0, 0), 40, {}),
        ("crate", (2.6, -4.6, 0), -12, {}),
    ],
    "broken": [
        ("wall_plain", (-8, 0, 0), 0, {"blast": [(0.5, 6.5, 3.0)]}),
        ("wall_window", (0, 0, 0), 0, {"blast": [(3.2, 10.5, 2.4)], "without": ["window"]}),
        ("wall_door", (8, 0, 0), 0, {"blast": [(-2.8, 10.0, 2.6)]}),
        ("door", (8 - 1.95 + 1.6, -1.15, 0), -42, {"blast": [(0.3, 5.0, 1.5)]}),
        ("crate", (-7.2, -4.6, 0), 18, {"explode": 0.55}), ("barrel", (-2.6, -4.0, 0), 0, {"explode": 0.5}),
        ("crate", (3.0, -4.6, 0), -12, {}),
    ],
}



def _cell(walls, cx=0.0, cy=0.0, z=0.0):
    """Four wall pieces round one grid cell: (south, east, north, west), fronts facing out."""
    spots = (((cx, cy - 4, z), 0), ((cx + 4, cy, z), 90), ((cx, cy + 4, z), 180), ((cx - 4, cy, z), -90))
    return [(name, pos, rot, {}) for name, (pos, rot) in zip(walls, spots) if name]


# One room built from the kit, to check that the pieces fit each other: ground, walls, corner posts,
# roof slab, parapets, stairs up one side, a ladder up the other, a pillar and a plank bridge beside it.
SCENES["building"] = (
    [("ground", (8 * i, 8 * j, -0.49), 0, {}) for i in range(-2, 3) for j in range(-2, 2)]
    + _cell(("wall_door", "wall_window", "wall_plain", "wall_window"))
    + [("corner", (x, y, 0), 0, {}) for x in (-4, 4) for y in (-4, 4)]
    + [("roof", (0, 0, 12 - C.KIT["roof"]["t"] + 0.06), 0, {})]
    + _cell(("parapet_crenel", "parapet_plain", "parapet_plain", "parapet_crenel"), z=12)
    + [("parapet_corner", (x, y, 12), 0, {}) for x in (-4, 4) for y in (-4, 4)]
    + [("stairs", (8, 0, 0), 90, {}), ("ladder", (-4.9, 1.5, 0), -90, {}),
       ("pillar", (-12, -9, 0), 0, {}), ("pillar", (-12, 1, 0), 0, {}),
       ("plank", (-12, -4, 12), 90, {})]
)
# The cover pieces and props in a row.
SCENES["props"] = [
    ("stall", (-11, 0, 0), 0, {}), ("awning", (-2.5, 2, 3.5), 0, {}), ("wall_plain", (-2.5, 2.5, 0), 0, {}),
    ("cloth", (6, 1, 0), 0, {}), ("well", (14.5, 0, 0), 0, {}),
    ("sacks", (-9, -7, 0), 0, {}), ("pot_tall", (-3.5, -6, 0), 0, {}), ("pot_round", (-0.5, -6.5, 0), 0, {}),
    ("vase", (2, -6, 0), 0, {}), ("crate", (6, -6.5, 0), 20, {}), ("barrel", (10, -6, 0), 0, {}),
]
# The pilot building, from its own recipe (buildings/teahouse.py).
SCENES["teahouse"] = [(item["piece"], tuple(item["pos"]), item["turn"], {}) for item in teahouse.placements()]
# The floor pieces side by side, with a wall and a drift of sand, to judge them before they are uploaded.
SCENES["paving"] = (
    [(("paving_a", "paving_b", "paving_c")[(i * 2 + j) % 3], (8 * i, 8 * j, -0.49), 90 * ((i + 2 * j) % 4), {})
     for i in range(-3, 0) for j in range(-1, 2)]
    + [("paving_tiles", (8 * i, 8 * j, -0.49), 0, {}) for i in range(0, 2) for j in range(-1, 2)]
    + [("paving_bricks", (8 * i, 8 * j, -0.49), 0, {}) for i in range(2, 4) for j in range(-1, 1)]
    + [("paving_dyed", (8 * i, 8, -0.49), 90 * i, {}) for i in range(2, 4)]
    + [("wall2_plain", (-16, 12, 0), 0, {}), ("wall2_shutter", (-8, 12, 0), 0, {}), ("sand_drift", (-16, 11.3, 0.01), 0, {}),
       ("vat_indigo", (24, 8, 0.01), 0, {}), ("tea_table", (4, 0, 0.01), 0, {})]
)
SCENES["cistern"] = [(item["piece"], tuple(item["pos"]), item["turn"], {}) for item in cistern.placements()]
# The town's newer pieces in two rows, to judge them before they are uploaded.
SCENES["newkit"] = [
    ("townwall", (-28, 14, 0), 0, {}), ("towngate", (-20, 14, 0), 0, {}), ("townwall", (-12, 14, 0), 0, {}),
    ("townwall_tower", (-4, 12, 0), 0, {}), ("wall2_door", (8, 12, 0), 0, {}), ("door2_teal", (8, 12, 0), 0, {}),
    ("wall2_door", (16, 12, 0), 0, {}), ("door2_wood", (16, 12, 0), 0, {}), ("wall2_upper_shutter", (24, 12, 0), 0, {}),
    ("sign_pot", (5.5, 11.4, 9.5), 0, {}), ("sign_cloth", (13.5, 11.4, 9.5), 0, {}), ("sign_drop", (19, 11.4, 9.5), 0, {}),
    ("sign_bread", (27, 11.4, 9.5), 0, {}),
    ("stack_crates", (-26, 0, 0), 0, {}), ("cart", (-17, 0, 0), 20, {}), ("kiln", (-7, 0, 0), 0, {}), ("pot_rack", (2, 1, 0), 0, {}),
    ("loom", (10, 1, 0), 0, {}), ("cypress", (18, 1, 0), 0, {}), ("palm_bed", (27, 1, 0), 0, {}),
    ("potted_plant", (5.5, -5, 0), 0, {}), ("baskets", (10, -5, 0), 0, {}),
] + [("paving_a", (8 * i, 8 * j, -0.49), 0, {}) for i in range(-4, 5) for j in range(-1, 2)]
SCENES["dyeworks"] = [(item["piece"], tuple(item["pos"]), item["turn"], {}) for item in dyeworks.placements()]
SCENES["courtyard"] = [(item["piece"], tuple(item["pos"]), item["turn"], {}) for item in courtyard.placements()]
# guns: (centre x, centre height, span) in studs, used to frame the camera
GUNS = {"rifle": (0.57, 0.0, 3.5), "pistol": (0.35, -0.05, 1.7), "knife": (0.15, -0.14, 1.45), "smoke": (0.02, 0.07, 1.6)}
CAMERAS = {"preview": ((7.5, -27, 7.5), (0.2, 0, 5.2), 38), "close": ((-1.5, -11, 4.2), (-4.5, 0, 3.4), 35),
           "broken": ((5.5, -27, 8.5), (0.0, 0, 5.0), 38),
           "building": ((24, -34, 21), (0.5, -1, 6.5), 38), "building-back": ((-26, 30, 19), (-1, 0, 6.5), 38),
           "props": ((3, -30, 9), (2, -2, 3.6), 38), "props-close": ((-6, -19, 5), (-5, -3, 2.6), 38),
           "teahouse": ((60, -96, 36), (15, -16, 11.5), 38), "teahouse-street": ((-6, -52, 5.5), (16, -22, 11), 24),
           "teahouse-back": ((-34, 34, 30), (14, -12, 10), 38), "teahouse-hall": ((12, -22.6, 5.2), (12, -9, 9.5), 14),
           "teahouse-gallery": ((3.4, -21, 17.4), (15, -9, 17.5), 14), "teahouse-terrace": ((31, -1.5, 17.6), (22, -22, 14), 16),
           "courtyard": ((120, -150, 75), (28, -34, 6), 38), "courtyard-court": ((27, -52.5, 5.2), (30, -22, 7.5), 14),
           "courtyard-room": ((3.6, -12.5, 5.2), (40, -5, 5.5), 14),
           "paving": ((4, -34, 30), (4, 2, 0), 38), "newkit": ((0, -62, 22), (0, 4, 8), 38), "cistern": ((110, -130, 70), (30, -26, 5), 38),
           "cistern-hall": ((4.5, -20.5, 5.4), (40, -17, 5.0), 14), "dyeworks": ((-70, -150, 80), (30, -36, 6), 38), "dyeworks-yard": ((3, -68, 5.2), (30, -30, 7.5), 14)}


def render_gun(name):
    """Side view, two three-quarter views, and the parts pulled apart."""
    cx, cz, span = GUNS[name]
    h = 1.6 + cz
    views = {"side": ((cx, -2.6 * span, h), (cx, 0, h), 85, {}, (1600, 640)),
             "front": ((cx + 0.87 * span, -0.74 * span, h + 0.26 * span), (cx, 0, h), 50, {}, (1600, 900)),
             "left": ((cx - 0.85 * span, 0.97 * span, h + 0.31 * span), (cx, 0, h), 55, {}, (1600, 900)),
             "parts": ((cx, -3.6 * span, h), (cx, 0, h), 85, {"explode": 0.55}, (1600, 800))}
    for view, (eye, target, lens, options, size) in views.items():
        SCENES["gun"] = [(name, (0, 0, 1.6), 0, options)]
        CAMERAS["gun"] = (eye, target, lens)
        render("gun", "gun", os.path.join(OUT, f"{name}-{view}.png"), size=size)


# Which socket of a gun each attachment goes on, and guns dressed with them to look at.
FITS = {"att_suppressor": "muzzle", "att_compensator": "muzzle", "att_reddot": "optic", "att_scope": "optic",
        "att_foregrip": "underbarrel", "att_laser": "underbarrel"}
FITTED = {"rifle-quiet": ("rifle", ["att_suppressor", "att_reddot", "att_foregrip"]),
          "rifle-long": ("rifle", ["att_compensator", "att_scope", "att_laser"]),
          "pistol-quiet": ("pistol", ["att_suppressor", "att_reddot", "att_laser"])}


def render_fitted(tag):
    """A gun with attachments on its sockets: a side view and a three-quarter view."""
    gun, attachments = FITTED[tag]
    with open(os.path.join(OUT, gun, gun + ".parts.json")) as fh:
        sockets = {s["name"]: s["position"] for s in json.load(fh)["sockets"]}
    cx, cz, span = GUNS[gun]
    span *= 1.15                                                    # a suppressor makes it longer
    cx += 0.08 * span
    h = 1.6 + cz
    scene = [(gun, (0, 0, 1.6), 0, {})]
    for name in attachments:
        x, y, z = sockets[FITS[name]]                               # the parts data is in Roblox axes: y is up
        scene.append((name, (x, -z, 1.6 + y), 0, {}))
    views = {"side": ((cx, -2.6 * span, h), (cx, 0, h), 85, (1600, 640)),
             "front": ((cx + 0.87 * span, -0.74 * span, h + 0.26 * span), (cx, 0, h), 50, (1600, 900))}
    for view, (eye, target, lens, size) in views.items():
        SCENES["gun"] = scene
        CAMERAS["gun"] = (eye, target, lens)
        render("gun", "gun", os.path.join(OUT, f"fitted-{tag}-{view}.png"), size=size)


def load(name, mesh=None):
    folder = os.path.join(OUT, name)
    bpy.ops.wm.obj_import(filepath=os.path.join(folder, (mesh or name) + ".obj"), forward_axis="NEGATIVE_Z", up_axis="Y")
    obj = bpy.context.selected_objects[0]
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)   # bake the importer's axis turn
    obj.data.materials.clear()
    obj.data.materials.append(matte_material(name, os.path.join(folder, name + ".png")))
    return obj


def place(name, pos, rot, options):
    turn = Matrix.Rotation(math.radians(rot), 4, "Z")
    if not options:
        objects = [(load(name), Vector((0, 0, 0)))]
    else:
        folder = os.path.join(OUT, name)
        data = next(f for f in os.listdir(folder) if f.endswith((".break.json", ".parts.json")))
        with open(os.path.join(folder, data)) as fh:
            listing = json.load(fh)
        chunks = listing.get("chunks") or listing["parts"]
        middle = sum((Vector(c["center"]) for c in chunks), Vector()) / len(chunks)
        objects = []
        for c in chunks:
            if c["id"] in options.get("without", []) or any(
                    math.hypot(c["center"][0] - x, c["center"][1] - h) < r for x, h, r in options.get("blast", [])):
                continue
            away = Vector(c["center"]) - middle                      # manifest is in Roblox axes (Y up)
            push = Vector((away.x, -away.z, max(away.y, 0))) * options.get("explode", 0.0)
            objects.append((load(name, c["mesh"][:-4]), push))
    for obj, push in objects:
        obj.location = Vector(pos) + turn @ push
        obj.rotation_euler = (0, 0, math.radians(rot))


def render(scene_name, camera, path, size=(1600, 900), samples=48):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    for name, pos, rot, options in SCENES[scene_name]:
        place(name, pos, rot, options)
        if name.startswith("lantern"):                              # lamps really light up
            turn = Matrix.Rotation(math.radians(rot), 4, "Z")
            at = Vector(pos) + turn @ Vector((0, -1.15, -2.7) if name == "lantern_wall" else (0, 0, -3.7))
            bpy.ops.object.light_add(type="POINT", location=at)
            lamp = bpy.context.object.data
            lamp.energy, lamp.color, lamp.shadow_soft_size = 350.0, (1.0, 0.72, 0.42), 0.5
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
    import sys
    scenes = [name for name in sys.argv[1:] if name in CAMERAS and name.split("-")[0] in SCENES]
    if scenes:                                  # python3 preview.py building building-back props
        for name in scenes:
            render(name.split("-")[0], name, os.path.join(OUT, f"preview-{name}.png"))
        sys.exit()
    fitted = [name for name in sys.argv[1:] if name in FITTED]
    if fitted:                                  # python3 preview.py rifle-quiet rifle-long pistol-quiet
        for name in fitted:
            render_fitted(name)
        sys.exit()
    guns = [name for name in sys.argv[1:] if name in GUNS]
    if guns:
        for name in guns:
            render_gun(name)
        sys.exit()
    render("whole", "preview", os.path.join(OUT, "preview.png"))
    render("whole", "close", os.path.join(OUT, "preview-close.png"))
    render("broken", "broken", os.path.join(OUT, "broken.png"))
    compare(os.path.join(OUT, "preview.png"), os.path.join(OUT, "compare.png"))

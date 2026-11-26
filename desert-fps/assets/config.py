"""All numbers for the asset kit live here: scale, texture, palette, paint rules, piece sizes.

1 Blender unit = 1 stud. Pieces snap to the plan grid (8-stud cells, 12-stud stories).
"""

# ---------------------------------------------------------------- scale
CELL = 8.0            # studs, plan grid cell = width of one wall piece
STORY = 12.0          # studs, height of one story
WALL_T = 1.0          # studs, wall thickness

GUN_MM = 3.3 / 880.0  # studs per millimetre for every gun: an 880 mm rifle is 3.3 studs long

# ---------------------------------------------------------------- texture
TEX = 1024            # px, texture size per piece (phone-friendly)
PAD = 6               # px of padding around every UV island
DENSITY_MIN = 24      # px per stud: run.py fails a piece whose texture is coarser than this...
DENSITY_MIN_PIECE = {"stairs": 22}    # ...except the biggest solid in the kit, which just misses it
AO_STEP = 2           # compute contact shade on every Nth texel
AO_RAYS = 16
AO_DIST = 0.45        # studs: only close contact darkens ("corners and cracks")
SEED = 11

# ---------------------------------------------------------------- palette
# Measured from reference/kit and reference/concept. Colours are (hue deg, lightness, saturation).
# Every material has ONE family; strokes may only move inside its ranges.
PALETTE = {
    "plaster": {"h": (13, 25), "l": (0.655, 0.775), "s": (0.78, 0.98), "step": 0.016, "hue_step": 1.2,
                "bases": [(21, 0.725, 0.95), (19, 0.715, 0.93), (23, 0.74, 0.96), (16, 0.705, 0.86)]},
    "band":    {"h": (146, 168), "l": (0.50, 0.63), "s": (0.15, 0.30), "step": 0.018, "hue_step": -1.5,
                "bases": [(160, 0.565, 0.24), (156, 0.575, 0.21)]},
    "stone":   {"h": (16, 27), "l": (0.70, 0.83), "s": (0.68, 0.95), "step": 0.016, "hue_step": 0.6,
                "bases": [(22, 0.765, 0.90), (24, 0.78, 0.88)]},
    "wood":    {"h": (13, 24), "l": (0.42, 0.64), "s": (0.40, 0.72), "step": 0.022, "hue_step": 0.6,
                "bases": [(18, 0.545, 0.52), (20, 0.57, 0.58), (16, 0.52, 0.48)]},
    "darkwood": {"h": (11, 19), "l": (0.31, 0.53), "s": (0.24, 0.42), "step": 0.022, "hue_step": 0.4,
                 "bases": [(15, 0.455, 0.33), (14, 0.43, 0.30), (16, 0.48, 0.35)]},
    "iron":    {"h": (0, 14), "l": (0.28, 0.45), "s": (0.08, 0.20), "step": 0.02, "hue_step": 0.5,
                "bases": [(5, 0.37, 0.14), (8, 0.40, 0.13)]},
}
# weapons
PALETTE["gunmetal"] = {"h": (250, 285), "l": (0.18, 0.48), "s": (0.05, 0.16), "step": 0.02, "hue_step": 0.0,
                       "bases": [(268, 0.285, 0.10), (262, 0.30, 0.09)]}
PALETTE["brass"] = {"h": (36, 47), "l": (0.46, 0.68), "s": (0.46, 0.70), "step": 0.022, "hue_step": 0.5,
                    "bases": [(42, 0.57, 0.58), (40, 0.55, 0.56)]}
PALETTE["cloth"] = {"h": (150, 172), "l": (0.44, 0.62), "s": (0.22, 0.40), "step": 0.02, "hue_step": -1.2,
                    "bases": [(163, 0.53, 0.32), (159, 0.55, 0.30)]}

PALETTE["steel"] = {"h": (238, 275), "l": (0.40, 0.84), "s": (0.05, 0.16), "step": 0.02, "hue_step": 0.0,
                    "bases": [(256, 0.52, 0.11), (250, 0.53, 0.10)]}
PALETTE["bore"] = {"h": (255, 285), "l": (0.05, 0.13), "s": (0.05, 0.16), "step": 0.012, "hue_step": 0.0,
                   "bases": [(270, 0.085, 0.10)]}

# what shows when a part is cut open
PALETTE["adobe"] = {"h": (17, 27), "l": (0.44, 0.60), "s": (0.30, 0.48), "step": 0.02, "hue_step": 0.6,
                    "bases": [(22, 0.525, 0.40), (20, 0.54, 0.38)]}
PALETTE["rawwood"] = {"h": (22, 32), "l": (0.62, 0.78), "s": (0.46, 0.66), "step": 0.02, "hue_step": 0.6,
                      "bases": [(27, 0.70, 0.56), (25, 0.68, 0.54)]}
CORE = {"plaster": "adobe", "stone": "adobe", "wood": "rawwood", "darkwood": "rawwood", "iron": "iron"}

# map props, measured from reference/props and reference/kit/awnings
PALETTE["canvas"] = {"h": (30, 38), "l": (0.77, 0.89), "s": (0.72, 0.98), "step": 0.014, "hue_step": 0.5,
                     "bases": [(34, 0.855, 0.94), (33, 0.84, 0.90)]}
PALETTE["redcloth"] = {"h": (3, 12), "l": (0.55, 0.74), "s": (0.60, 0.90), "step": 0.018, "hue_step": 0.5,
                       "bases": [(9, 0.655, 0.76), (6, 0.64, 0.70)]}
PALETTE["burlap"] = {"h": (22, 32), "l": (0.58, 0.78), "s": (0.48, 0.86), "step": 0.02, "hue_step": 0.6,
                     "bases": [(28, 0.71, 0.72), (26, 0.69, 0.66)]}
PALETTE["clay"] = {"h": (13, 24), "l": (0.55, 0.74), "s": (0.64, 0.92), "step": 0.018, "hue_step": 0.8,
                   "bases": [(17, 0.66, 0.78), (20, 0.68, 0.84)]}
PALETTE["rope"] = {"h": (24, 31), "l": (0.60, 0.80), "s": (0.52, 0.80), "step": 0.02, "hue_step": 0.4,
                   "bases": [(27, 0.72, 0.72)]}
PALETTE["paving"] = {"h": (14, 28), "l": (0.73, 0.85), "s": (0.68, 0.95), "step": 0.014, "hue_step": 0.8,
                     "bases": [(24, 0.80, 0.88), (19, 0.78, 0.85), (26, 0.815, 0.90)]}
CORE.update({"canvas": "canvas", "redcloth": "redcloth", "burlap": "burlap", "clay": "clay", "rope": "rope",
             "paving": "adobe", "band": "adobe"})

LAVENDER = (268, 0.66, 0.42)      # the only shade colour; never gray
PALE = (30, 0.90, 0.85)           # light-catching glaze on protruding edges

BAND_H = 2.2          # studs: turquoise band height on ground-floor walls

# ---------------------------------------------------------------- paint rules
# Stroke sizes in studs. `per_stud2` = strokes per square stud of surface.
# Every stroke is ONE step lighter or darker than the paint under it.
PAINT = {
    "plaster": {
        "lean": 42, "lean_jitter": 8,           # all strokes lean up and to the right
        "layers": [
            {"per_stud2": 0.20, "len": (4.0, 9.0), "wid": (0.9, 1.9), "opacity": (0.35, 0.55), "round": 0.15},
            {"per_stud2": 9.0, "len": (0.4, 1.0), "wid": (0.32, 0.75), "opacity": (0.55, 0.9), "round": 0.9, "jitter": 35},
            {"per_stud2": 1.6, "len": (1.2, 3.2), "wid": (0.2, 0.48), "opacity": (0.35, 0.6), "round": 0.2},
            {"per_stud2": 7.0, "len": (0.3, 0.9), "wid": (0.07, 0.16), "opacity": (0.5, 0.85), "round": 0.1},
        ],
    },
    "band": {
        "lean": 42, "lean_jitter": 10,
        "layers": [
            {"per_stud2": 9.0, "len": (0.3, 0.8), "wid": (0.25, 0.55), "opacity": (0.5, 0.85), "round": 0.9, "jitter": 35},
            {"per_stud2": 6.0, "len": (0.5, 1.6), "wid": (0.1, 0.25), "opacity": (0.45, 0.75), "round": 0.2},
        ],
        "ragged": 0.42,      # studs the top edge wanders up and down
        "chips": 0.45,       # plaster showing through, dabs per square stud of band
    },
    "stone": {
        "lean": 42, "lean_jitter": 10,
        "layers": [
            {"per_stud2": 7.0, "len": (0.3, 0.8), "wid": (0.22, 0.5), "opacity": (0.5, 0.8), "round": 0.9, "jitter": 35},
            {"per_stud2": 8.0, "len": (0.3, 0.9), "wid": (0.06, 0.14), "opacity": (0.5, 0.8), "round": 0.1},
        ],
    },
    "wood": {
        "lean_jitter": 3,                        # strokes follow the grain
        "layers": [
            {"per_stud2": 5.0, "len": (1.0, 2.6), "wid": (0.16, 0.36), "opacity": (0.45, 0.75), "round": 0.15},
            {"per_stud2": 16.0, "len": (0.5, 1.6), "wid": (0.035, 0.08), "opacity": (0.5, 0.85), "round": 0.0},
        ],
        "end_grain": {"per_stud2": 40.0, "len": (0.1, 0.24), "wid": (0.07, 0.15), "opacity": (0.5, 0.8), "round": 0.9},
    },
    "iron": {
        "lean_jitter": 6,
        "layers": [
            {"per_stud2": 14.0, "len": (0.2, 0.7), "wid": (0.06, 0.16), "opacity": (0.45, 0.75), "round": 0.4},
        ],
    },
}
PAINT["darkwood"] = PAINT["wood"]
PAINT["gunmetal"] = {
    "lean": 0, "lean_jitter": 6,
    "layers": [
        {"per_stud2": 5.0, "len": (0.8, 2.2), "wid": (0.14, 0.32), "opacity": (0.4, 0.7), "round": 0.2},
        {"per_stud2": 12.0, "len": (0.25, 0.8), "wid": (0.05, 0.12), "opacity": (0.45, 0.8), "round": 0.3},
    ],
}
PAINT["steel"] = PAINT["gunmetal"]
PAINT["brass"] = PAINT["iron"]
PAINT["bore"] = {"lean": 0, "lean_jitter": 90,     # the dark inside of a barrel
                 "layers": [{"per_stud2": 8.0, "len": (0.2, 0.5), "wid": (0.1, 0.2), "opacity": (0.4, 0.7), "round": 0.9}]}
PAINT["cloth"] = {
    "lean": 80, "lean_jitter": 10,               # strokes run along the wraps
    "layers": [
        {"per_stud2": 10.0, "len": (0.4, 1.2), "wid": (0.08, 0.2), "opacity": (0.45, 0.8), "round": 0.3},
    ],
}
PAINT["adobe"] = {                              # mud brick: dabs, plus thin level lines for the brick courses
    "lean": 0, "lean_jitter": 4,
    "layers": [
        {"per_stud2": 14.0, "len": (0.25, 0.6), "wid": (0.2, 0.42), "opacity": (0.5, 0.85), "round": 0.9, "jitter": 60},
        {"per_stud2": 5.0, "len": (0.5, 1.4), "wid": (0.035, 0.07), "opacity": (0.5, 0.8), "round": 0.0},
    ],
}
PAINT["rawwood"] = {                            # splintered wood: short strokes in every direction
    "lean": 0, "lean_jitter": 90,
    "layers": [
        {"per_stud2": 30.0, "len": (0.12, 0.4), "wid": (0.05, 0.13), "opacity": (0.5, 0.85), "round": 0.5},
    ],
}

PAINT["canvas"] = {                             # cloth: long soft strokes along the drape, then thin fold lines
    "lean_jitter": 5,
    "layers": [
        {"per_stud2": 3.0, "len": (1.2, 3.0), "wid": (0.25, 0.55), "opacity": (0.35, 0.6), "round": 0.3},
        {"per_stud2": 7.0, "len": (0.6, 1.8), "wid": (0.05, 0.11), "opacity": (0.4, 0.7), "round": 0.1},
    ],
}
PAINT["redcloth"] = PAINT["canvas"]
PAINT["burlap"] = {                             # sacking: short dabs both ways, like a coarse weave
    "lean": 10, "lean_jitter": 80,
    "layers": [
        {"per_stud2": 10.0, "len": (0.3, 0.8), "wid": (0.2, 0.42), "opacity": (0.45, 0.8), "round": 0.9},
        {"per_stud2": 14.0, "len": (0.25, 0.7), "wid": (0.04, 0.09), "opacity": (0.45, 0.8), "round": 0.1},
    ],
}
PAINT["clay"] = {                               # thrown pots: strokes run round the pot
    "lean": 3, "lean_jitter": 6,
    "layers": [
        {"per_stud2": 8.0, "len": (0.5, 1.6), "wid": (0.2, 0.45), "opacity": (0.45, 0.8), "round": 0.5},
        {"per_stud2": 10.0, "len": (0.4, 1.2), "wid": (0.05, 0.1), "opacity": (0.45, 0.8), "round": 0.1},
    ],
}
PAINT["rope"] = {                               # short slanted dabs: the twist of the strands
    "lean": 55, "lean_jitter": 8,
    "layers": [
        {"per_stud2": 40.0, "len": (0.12, 0.3), "wid": (0.05, 0.1), "opacity": (0.5, 0.85), "round": 0.4},
    ],
}
PAINT["paving"] = {                             # flagstones: flat dabs, no lean
    "lean": 20, "lean_jitter": 70,
    "layers": [
        {"per_stud2": 6.0, "len": (0.4, 1.1), "wid": (0.3, 0.7), "opacity": (0.4, 0.75), "round": 0.9},
        {"per_stud2": 5.0, "len": (0.3, 0.9), "wid": (0.06, 0.14), "opacity": (0.45, 0.75), "round": 0.1},
    ],
}

GLAZE = {
    "shade_per_stud2": 260.0,  # dark glaze dabs per square stud of fully occluded surface
    "shade_size": (0.05, 0.16),
    "shade_steps": 2,          # each dab is this many steps darker than the paint under it...
    "shade_mix": 0.16,         # ...and moves this far toward lavender
    "edge_cover": 0.7,         # share of every protruding edge that catches light
    "edge_len": (0.3, 0.9),
    "edge_wid": (0.05, 0.10),
    "edge_mix": 0.2,
    "edge_min": 0.25,          # studs: shorter edges (studs, tiny parts) get no highlight
}
# groups whose base colour is fixed for the whole kit, so neighbouring pieces match (measured from the concept walls)
SHARED_MIX = {("wall", "plaster"): (21.5, 0.735, 0.95), ("wall", "band"): (160, 0.565, 0.24)}

# ---------------------------------------------------------------- kit sizes (studs)
KIT = {
    "wall": {
        "plinth_out": 0.14, "plinth_h": 2.0, "plinth_chamfer": 0.2,
        "beams": {"count": 3, "z": 10.4, "radius": 0.3, "out": 0.95, "segments": 10},
        "window": {"w": 3.0, "sill": 4.2, "h": 4.2, "board_h": 0.5, "board_over": 0.45, "board_out": 0.14,
                   "bar": 0.13, "bar_gap": 0.62, "inset": 0.35},
        "door": {"w": 4.0, "h": 7.6, "jamb_w": 0.7, "jamb_out": 0.2, "jamb_blocks": 4,
                 "lintel_h": 0.75, "lintel_over": 0.9},
    },
    "door": {"w": 3.9, "h": 7.5, "t": 0.28, "planks": 6, "strap_z": (1.3, 6.2), "strap_h": 0.36},
    "crate": {"size": 3.0, "frame_w": 0.42, "frame_out": 0.13, "planks": 3},
    # guns: `chunky` thickens one a little over the real widths so it reads on screen
    "rifle": {"chunky": 1.2},
    "pistol": {"chunky": 1.15},
    "knife": {"chunky": 1.3},
    "smoke": {"chunky": 1.0},
    "barrel": {"h": 3.6, "r_end": 1.0, "r_mid": 1.22, "segments": 16, "hoops": (0.5, 1.8, 3.1), "hoop_h": 0.22},
    # --- the rest of the building kit. Everything snaps to the 8-stud cell and the 12-stud story.
    "corner": {"half": 0.75},                       # post that closes the notch where two walls meet
    "pillar": {"base": 1.25, "base_h": 1.3, "shaft_r": 0.85, "cap": 1.15, "cap_h": 0.9, "segments": 8},
    "parapet": {"h": 2.6, "cap_h": 0.4, "cap_out": 0.16, "merlons": 3, "merlon_w": 1.4, "merlon_h": 1.3,
                "post_out": 0.06, "post_up": 0.3},        # the corner post: a little wider and taller than the run
    "roof": {"t": 1.06, "beams": 3, "beam_r": 0.3, "beam_drop": 0.6},   # 0.06 proud of the wall tops it covers
    "stairs": {"steps": 8, "tread_t": 0.12, "tread_over": 0.1, "tread_in": 0.05, "narrow_w": 4.0},
    "ladder": {"h": 12.8, "w": 2.2, "rail": 0.3, "rung_gap": 1.4, "rung_h": 0.22},
    "plank": {"w": 6.0, "boards": 8, "board_t": 0.22, "joist": (0.36, 0.5), "joist_y": 2.2},
    "ground": {"t": 0.5, "stones": 4},
    # --- cover and props
    "stall": {"w": 6.4, "d": 4.4, "front_h": 6.0, "back_h": 7.2, "post": 0.4, "stripes": 8, "valance": 0.75,
              "counter_h": 2.9, "counter_d": 1.7},
    "awning": {"w": 6.4, "out": 3.4, "top": 3.4, "drop": 1.5, "stripes": 8, "valance": 0.7},
    "cloth": {"w": 6.6, "pole_z": 9.6, "drop": 8.4, "t": 0.07, "folds": 9, "fold_out": 0.3},
    "sacks": {"len": 3.0, "w": 1.9, "h": 1.0},
    "well": {"r_in": 1.75, "r_out": 2.45, "h": 2.5, "segments": 16, "post_h": 4.6, "beam_z": 6.5},
    "vat": {"r_in": 2.75, "r_out": 3.35, "h": 1.7, "segments": 16},
}

# ---------------------------------------------------------------- small objects
# Brush sizes, shading reach and flicker tolerance are tuned for buildings. A piece listed here
# uses them scaled down (0.2 = a brush one fifth the size).
DETAIL_SCALE = {"rifle": 0.2, "pistol": 0.12, "knife": 0.1, "smoke": 0.1,
                "pot": 0.45, "vase": 0.4, "sacks": 0.7, "ladder": 0.6, "well": 0.7, "vat": 0.7, "stall": 0.7, "awning": 0.7}

# ---------------------------------------------------------------- per-piece style
# Extra hand-painted detail for pieces seen up close. Everything here adds to the shared rules.
#   step_gain     how much bigger one "step lighter or darker" is (more contrast between strokes)
#   glaze         overrides for GLAZE. edge_steps: the highlight is first that many steps lighter in the
#                 material's own colour, then edge_mix toward pale. edge_dark adds a thin dark stroke
#                 just inside every highlighted edge.
#   extra_layers  more stroke layers per material: `step` = how many steps, `dark` = share of darker strokes
#   round_shine   brushed highlight along round parts (a barrel); 0 = none
STYLE = {
    "rifle": {
        "step_gain": 1.5,
        "glaze": {"edge_steps": 5, "edge_mix": 0.22, "edge_cover": 0.95, "edge_wid": (0.03, 0.055),
                  "edge_len": (0.25, 0.9), "edge_min": 0.1,
                  "edge_dark": {"steps": 3, "cover": 0.7, "wid": (0.02, 0.035), "inset": 2.0}},
        "extra_layers": {
            "wood": [       # dark grain lines, then a few pale scuffs
                {"per_stud2": 7.0, "len": (1.0, 3.2), "wid": (0.028, 0.05), "opacity": (0.6, 0.9), "step": 3, "dark": 1.0},
                {"per_stud2": 2.0, "len": (0.4, 1.0), "wid": (0.05, 0.09), "opacity": (0.5, 0.8), "step": 3, "dark": 0.0, "jitter": 20},
            ],
            "gunmetal": [   # grime dabs, then bright scratches
                {"per_stud2": 2.5, "len": (0.2, 0.5), "wid": (0.1, 0.2), "opacity": (0.3, 0.5), "round": 0.9, "step": 2, "dark": 1.0, "jitter": 90},
                {"per_stud2": 5.0, "len": (0.3, 1.2), "wid": (0.02, 0.04), "opacity": (0.5, 0.85), "step": 5, "dark": 0.0, "jitter": 35},
            ],
            "cloth": [      # folds
                {"per_stud2": 8.0, "len": (0.5, 1.4), "wid": (0.03, 0.05), "opacity": (0.55, 0.85), "step": 3, "dark": 0.8},
            ],
        },
        "round_shine": 0.4,
    },
}

STYLE["pistol"] = STYLE["rifle"]
STYLE["knife"] = {**STYLE["rifle"], "extra_layers": {**STYLE["rifle"]["extra_layers"],
                                                     "steel": STYLE["rifle"]["extra_layers"]["gunmetal"]}}

STYLE["smoke"] = STYLE["knife"]

# Pale cloth and sacking show the dark corner glaze as stains, so they get much less of it.
STYLE["cloth"] = {"glaze": {"shade_per_stud2": 30.0}}
STYLE["sacks"] = {"glaze": {"shade_per_stud2": 90.0, "shade_mix": 0.1}}

# ---------------------------------------------------------------- destruction
# Pieces are pre-cut into jagged shards (see chunks.py).
# mode "chunks":  every shard has its own health and stays until it is destroyed (walls, doors).
# mode "shatter": the piece has one health; when it breaks it is swapped for its shards (props).
# shards   how many pieces it cracks into
# through  walls and doors: the cracks run through this axis (the thickness)
# slant    studs: how far the break faces lean instead of cutting straight through
# apart    0-1: higher = more even shard sizes, lower = a mix of big slabs and small bits
# seed     change it to get a different crack pattern
# Health numbers are placeholders until weapon damage exists.
BREAK = {
    "hp_per_stud3": {"plaster": 12, "stone": 16, "adobe": 12, "wood": 7, "darkwood": 7, "rawwood": 7, "iron": 30,
                     "canvas": 2, "redcloth": 2, "burlap": 4, "clay": 6, "rope": 3, "paving": 16, "band": 6},
    "hp_min": 10,
    "pieces": {
        "wall_plain": {"mode": "chunks", "shards": 12, "through": "y", "slant": 0.9, "apart": 0.55},
        "wall_window": {"mode": "chunks", "shards": 12, "through": "y", "slant": 0.9, "apart": 0.55},
        "wall_door": {"mode": "chunks", "shards": 11, "through": "y", "slant": 0.9, "apart": 0.55},
        "wall_upper": {"mode": "chunks", "shards": 12, "through": "y", "slant": 0.9, "apart": 0.55},
        "wall_upper_window": {"mode": "chunks", "shards": 12, "through": "y", "slant": 0.9, "apart": 0.55},
        "door": {"mode": "chunks", "shards": 6, "through": "y", "slant": 0.25, "apart": 0.5},
        "crate": {"mode": "shatter", "shards": 8, "apart": 0.5},
        "barrel": {"mode": "shatter", "shards": 7, "apart": 0.5},
        "corner": {"mode": "chunks", "shards": 4, "apart": 0.6},
        "corner_upper": {"mode": "chunks", "shards": 4, "apart": 0.6},
        "pillar": {"mode": "chunks", "shards": 5, "apart": 0.6},
        "parapet_plain": {"mode": "chunks", "shards": 5, "through": "y", "slant": 0.4, "apart": 0.55},
        "parapet_crenel": {"mode": "chunks", "shards": 5, "through": "y", "slant": 0.4, "apart": 0.55},
        "parapet_corner": {"mode": "chunks", "shards": 2, "apart": 0.6},
        "roof": {"mode": "chunks", "shards": 7, "through": "z", "slant": 0.4, "apart": 0.55},
        "stairs": {"mode": "chunks", "shards": 6, "apart": 0.6},
        "stairs_narrow": {"mode": "chunks", "shards": 6, "apart": 0.6, "seed": 4},
        "ladder": {"mode": "shatter", "shards": 5, "apart": 0.5},
        "plank": {"mode": "shatter", "shards": 6, "apart": 0.5},
        "stall": {"mode": "shatter", "shards": 10, "apart": 0.5},
        "awning": {"mode": "shatter", "shards": 5, "apart": 0.5},
        "cloth": {"mode": "shatter", "shards": 4, "apart": 0.5},
        "sacks": {"mode": "shatter", "shards": 6, "apart": 0.5},
        "well": {"mode": "shatter", "shards": 10, "apart": 0.5},
        "vat": {"mode": "shatter", "shards": 8, "apart": 0.5},
        "pot_tall": {"mode": "shatter", "shards": 5, "apart": 0.5},
        "pot_round": {"mode": "shatter", "shards": 5, "apart": 0.5},
        "vase": {"mode": "shatter", "shards": 4, "apart": 0.5},
        # mode "parts": not breakable. Only splits off the parts a recipe tags, so they can be animated.
        "ground": {"mode": "parts"},
        "rifle": {"mode": "parts"},
        "pistol": {"mode": "parts"},
        "knife": {"mode": "parts"},
        "smoke": {"mode": "parts"},
    },
}

# ---------------------------------------------------------------- budgets (triangles)
TRI_LIMIT = 20000      # Roblox hard limit per mesh
TRI_BUDGET = {"wall_plain": 400, "wall_window": 1200, "wall_door": 800, "door": 1200, "crate": 1600, "barrel": 900,
              "rifle": 6000, "pistol": 3000, "knife": 2500, "smoke": 1500}

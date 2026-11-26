"""Recipe registry: piece name -> (build function, options)."""
from . import barrel, crate, door, wall

RECIPES = {
    "wall_plain": (wall.build, {}),
    "wall_window": (wall.build, {"opening": "window"}),
    "wall_door": (wall.build, {"opening": "door"}),
    "door": (door.build, {}),
    "crate": (crate.build, {}),
    "barrel": (barrel.build, {}),
}

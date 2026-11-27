# Rebuilding the Studio place

The place can be rebuilt from an empty baseplate by running these in order, in Studio in edit mode (command bar, or an MCP `execute_luau`).

| Step | Script | What it does |
|---|---|---|
| 1 | `01_install_modules.luau` | Installs every project script and data module: `DesertFps` folders in ServerStorage, ReplicatedStorage, ServerScriptService and StarterPlayerScripts |
| 2 | `02_build_market.luau` | Optional. Builds the Market Square graybox in `Workspace.Graybox_market`, in the same place as the town's Market Square; step 6 removes it again |
| 3 | `03_lighting.luau` | Sets the lighting and post effects |
| 4 | `04_import_meshes.luau` | Loads the uploaded kit into `ServerStorage.DesertFps.Meshes` and checks every mesh against its data |
| 5 | `05_kit_showcase.luau` | Stands the kit, two characters and the weapons outside the town wall in `Workspace.KitShowcase`. It is also a firing range |
| 6 | `06_build_map.luau` | Builds the whole town out of kit pieces in `Workspace.Map`: nine districts, ring road, town wall (about 20,800 pieces, 7 seconds) |
| 7 | `07_build_teahouse.luau` | Optional. Stands the tea house alone on a paved yard outside the old town's south wall, for looking at it. Step 10 moves it into the town |
| 8 | `08_sky.luau` | Sets the painted sky (six faces cut from one painting by `assets/sky.py`) |
| 9 | `09_graybox_town.luau` | Builds the compact town (plan v2) as gray boxes in `Workspace.Graybox_town`, west of the old town |
| 10 | `10_build_town.luau` | Builds the whole compact town from its recipes: every building and house, the street dressing and the town wall in `Workspace.Buildings`, paving in `Workspace.TownGround`, unseen walls behind the town wall in `Workspace.TownEdge`. Of the gray boxes only the slab is left. Players spawn in front of the Tea House. About 2 seconds |
| 11 | `11_import_animations.luau` | Loads the twenty weapon animations into `ReplicatedStorage.DesertFpsAnimations`. Copy `animations/*.rbxmx` into Studio's content folder first (the script says where) |

`tests/time_market_routes.luau` runs on the server during a playtest. It walks bots along the planner's Market Square routes and writes the timings to the `RouteTiming` attribute on Workspace. `tests/time_all_routes.luau` does the same for every zone and writes a summary to `RouteSummary`.

`tests/climb_stairs.luau` walks a bot up every flight of stairs in the town and onto each roof it should reach.

`tests/time_town_routes.luau` walks bots along the planner's routes in every arena of the compact town's graybox; the summary lands in `TownRouteSummary`.

`tests/walk_teahouse.luau` walks bots through the tea house: in at each door, up both flights of stairs, out onto both terraces. The result lands in the `TeaHouseWalk` attribute on Workspace.

`tests/test_collapse.luau` runs on the server during a playtest, with `DevConfig.TestHooks` on. It shoots out the ground walls of one end of the Captain's House and all of the Watchtower's and returns how many pieces are left standing (49 of 72, and 2 of 68).

`tests/test_weapons.luau` runs on the client during a playtest, with `DevConfig.TestHooks` and `DevConfig.Dummies` on. It shoots the target dummies with the rifle and the pistol and returns six checks that should all start "ok".

`tests/test_attachments.luau` runs on the client during a playtest, with `DevConfig.TestHooks` on, from the spawn. It fits every attachment on the rifle and the pistol and returns 38 checks that should all start "ok": the numbers each one changes, what is refused, the magazine's rounds, the compensator's climb, every sight on the line of sight, the laser's dot and beam. It takes 80 seconds, longer than one MCP call may run: start it in a `task.spawn` and read the result from `shared` afterwards.

`tests/test_utility.luau` runs on the client during a playtest, with `DevConfig.TestHooks` and `DevConfig.Dummies` on, from the spawn. It throws recon darts and returns 15 checks that should all start "ok": what is refused, the charge and the weapon put away, the three pulses and who they outline, a dart shot down, none left, a charge coming back. It takes up to 50 seconds: start it in a `task.spawn` too.

`tests/test_wallbang.luau` runs on the server during a playtest. It stands walls, doors, a crate and other pieces in the air above the town, traces shots through them and returns 12 checks that should all start "ok": what the rifle, the pistol and the knife go through and how much force is left.

`tests/measure_views.luau` runs on the client during a playtest. It stands the player at seven viewpoints and returns draw calls, triangles on screen, drawing time and frames a second for each. Set the graphics level by hand first.

`tests/measure_collapse.luau` runs on the server during a playtest, with `DevConfig.TestHooks` on. It brings a whole building down at once and returns the server's frame times, the physics step, and how many pieces moved and touched.

The old town (`Workspace.Map`) and the kit showcase were deleted from the place on 2026-11-27. `break_wall.luau`, `climb_stairs.luau`, `time_all_routes.luau` and `time_market_routes.luau` need them: run steps 5 and 6 first, or import `backups/old_town_and_showcase.rbxm` into Workspace.

`tests/break_wall.luau` runs on the server during a playtest. It damages a wall through its crack stages until it crumbles, bursts a crate and sets off a blast, and returns a list of checks that should all be `ok = true`.

## Uploading the kit

Step 4 reads the asset ids in `../game/ServerStorage/DesertFps/Assets/AssetIds.luau`. Each piece is two uploads from `../assets/out/<piece>/`: `<piece>.bundle.fbx` as a Model and `<piece>.png` as an Image. They were uploaded through the Studio MCP (`open_cloud_invoke`, `POST /assets/v1/assets`), which only reads files from a folder approved in Studio under Assistant, Settings, MCP Permissions. After re-uploading a piece, put its new ids in `AssetIds.luau`, run `pack.py`, then steps 1 and 4.

## Where the code lives

The Luau sources are in `../game/`, in a folder tree that mirrors the place. Do not edit `01_install_modules.luau` by hand; it is generated.

After changing anything under `game/`, or re-running the planner:

```bash
python ../plan/routes.py
```

```bash
python pack.py
```

`pack.py` rewrites `01_install_modules.luau` and the files in `out/` (the same scripts as model files, for importing with an MCP tool). Each file is named after the place it is imported into, for example `StarterPlayer.StarterPlayerScripts.rbxmx`. Importing adds a second `DesertFps` folder, so delete the old one first. In ServerStorage, move `DesertFps.Meshes` out before deleting and back in after, or run step 4 again.

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
| 7 | `07_build_teahouse.luau` | Stands the pilot building, the tea house, on its own paved yard outside the south wall: `Workspace.Buildings.TeaHouse` (193 pieces). Players spawn in front of it |

`tests/time_market_routes.luau` runs on the server during a playtest. It walks bots along the planner's Market Square routes and writes the timings to the `RouteTiming` attribute on Workspace. `tests/time_all_routes.luau` does the same for every zone and writes a summary to `RouteSummary`.

`tests/climb_stairs.luau` walks a bot up every flight of stairs in the town and onto each roof it should reach.

`tests/walk_teahouse.luau` walks bots through the tea house: in at each door, up both flights of stairs, out onto both terraces. The result lands in the `TeaHouseWalk` attribute on Workspace.

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

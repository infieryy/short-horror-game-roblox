# Rebuilding the Studio place

The place can be rebuilt from an empty baseplate by running these in order, in Studio in edit mode (command bar, or an MCP `execute_luau`).

| Step | Script | What it does |
|---|---|---|
| 1 | `01_install_modules.luau` | Installs every project script and the map plan under `ServerStorage.DesertFps` |
| 2 | `02_build_market.luau` | Builds the Market Square graybox in `Workspace.Graybox_market` |

`tests/time_market_routes.luau` runs on the server during a playtest. It walks bots along the planner's routes and writes the timings to the `RouteTiming` attribute on Workspace.

## Where the code lives

The Luau sources are in `../game/`, in a folder tree that mirrors the place. Do not edit `01_install_modules.luau` by hand; it is generated.

After changing anything under `game/`, or re-running the planner:

```bash
python ../plan/routes.py
```

```bash
python pack.py
```

`pack.py` rewrites `01_install_modules.luau` and `out/<Service>.rbxmx` (the same scripts as a model file, for importing with an MCP tool).

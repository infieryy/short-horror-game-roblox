-- Builds the compact town (plan v2) from its recipes: every building and house, the street dressing, the
-- town wall, the paving and the dev spawn. Run in Studio in edit mode, after 01_install_modules.luau and
-- 04_import_meshes.luau. Safe to re-run: what is there is replaced.
--   Workspace.Buildings.<Name>   Workspace.TownGround   Workspace.TownEdge   Workspace.Graybox_town (its slab only)
-- What stands where is Town/TownData, written by `python -m buildings.town` in assets/ and packed by pack.py.
-- To rebuild only some recipes after changing them: TownBuilder.build({ "house_04_03", "streets" }).
local ServerStorage = game:GetService("ServerStorage")

local TownBuilder = require(ServerStorage.DesertFps.Town.TownBuilder)

local pieces = TownBuilder.build()

game:GetService("ChangeHistoryService"):SetWaypoint("Build the compact town")
return pieces

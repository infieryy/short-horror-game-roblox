-- Builds the compact town (plan v2, plan/town.py) as plain gray boxes: Workspace.Graybox_town.
-- Run in Studio in edit mode, after 01_install_modules.luau. Safe to re-run: the town that is there is replaced.
-- It stands west of the old town, 320 studs across. Bots walk it with tests/time_town_routes.luau.
local ServerStorage = game:GetService("ServerStorage")

local GrayboxBuilder = require(ServerStorage.DesertFps.Graybox.GrayboxBuilder)

-- The middle of the town, on the ground.
local MIDDLE = CFrame.new(-700, 1, 0)

local _, counts = GrayboxBuilder.build("town", workspace, MIDDLE)

game:GetService("ChangeHistoryService"):SetWaypoint("Graybox the compact town")
return counts

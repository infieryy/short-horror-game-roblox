-- Builds the Market Square graybox from the installed plan.
-- Run in Studio in edit mode, after 01_install_modules.luau. Safe to re-run: it replaces the old graybox.
local ServerStorage = game:GetService("ServerStorage")

-- The baseplate template's spawn sits where the market well goes; the graybox brings its own spawns.
local templateSpawn = workspace:FindFirstChild("SpawnLocation")
if templateSpawn then
	templateSpawn:Destroy()
end

local GrayboxBuilder = require(ServerStorage.DesertFps.Graybox.GrayboxBuilder)
local model, counts = GrayboxBuilder.build("market")

game:GetService("ChangeHistoryService"):SetWaypoint("Build Market Square graybox")
return { model = model:GetFullName(), counts = counts }

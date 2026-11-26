-- Builds the whole town out of kit pieces: Workspace.Map (all nine districts, the ring road and the town wall).
-- Run in Studio in edit mode, after 04_import_meshes.luau. Safe to re-run: what is there is replaced.
-- It places about 20,000 pieces and takes a few minutes; progress is on Workspace's "MapBuild" attribute.
-- To rebuild only some districts, pass their names: MapBuilder.build({ "market", "ring" }).
local ServerStorage = game:GetService("ServerStorage")

-- The gray boxes have done their job; 02_build_market.luau brings them back if they are wanted again.
local graybox = workspace:FindFirstChild("Graybox_market")
if graybox then
	graybox:Destroy()
end

-- Each client only loads the part of town around it: its own zone and the edges of the ones next door.
workspace.StreamingEnabled = true
workspace.StreamingMinRadius = 192
workspace.StreamingTargetRadius = 384

local MapBuilder = require(ServerStorage.DesertFps.Map.MapBuilder)
workspace:SetAttribute("MapBuild", "building")
local counts = MapBuilder.build()
workspace:SetAttribute("MapBuild", "done")

game:GetService("ChangeHistoryService"):SetWaypoint("Build the town")
return counts

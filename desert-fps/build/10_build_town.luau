-- Builds the compact town (plan v2): the real buildings that have a recipe, and gray boxes for the rest.
-- Workspace.Graybox_town and Workspace.Buildings.<Name>. Run in Studio in edit mode, after
-- 04_import_meshes.luau. Safe to re-run: what is there is replaced.
-- Which buildings are real is in game/ServerStorage/DesertFps/Town/TownConfig.luau.
local ServerStorage = game:GetService("ServerStorage")

local TownBuilder = require(ServerStorage.DesertFps.Town.TownBuilder)

local pieces = TownBuilder.build()

-- Players spawn on the street in front of the Tea House, looking at it (DevConfig.SpawnPath points here).
local buildings = workspace.Buildings
local old = buildings:FindFirstChild("Spawn")
if old then
	old:Destroy()
end
local spawn = Instance.new("SpawnLocation")
spawn.Name = "Spawn"
spawn.Anchored = true
spawn.CanCollide = false
spawn.Transparency = 1
spawn.Neutral = true
spawn.Size = Vector3.new(6, 1, 6)
spawn.CFrame = TownBuilder.cellCorner(13, 19) * CFrame.new(0, 0.5, 0) * CFrame.Angles(0, 0, 0)
spawn.Parent = buildings

game:GetService("ChangeHistoryService"):SetWaypoint("Build the compact town")
return pieces

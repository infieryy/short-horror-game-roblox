-- Stands the pilot building, the tea house, on a paved yard of its own outside the town's south wall:
-- Workspace.Buildings.TeaHouse. Run in Studio in edit mode, after 04_import_meshes.luau. Safe to re-run:
-- the building that is there is replaced.
-- The piece list comes from assets/buildings/teahouse.py (packed as BuildingData by build/pack.py).
local ServerStorage = game:GetService("ServerStorage")

local BuildingBuilder = require(ServerStorage.DesertFps.Buildings.BuildingBuilder)

-- The building's own north-west corner at street level, turned so that its front (the porch) faces west,
-- into the afternoon sun.
local ORIGIN = CFrame.new(182, 0.05, 420) * CFrame.Angles(0, -math.pi / 2, 0)
-- Cells of paving round the building.
local YARD = 4

local buildings = workspace:FindFirstChild("Buildings")
if not buildings then
	buildings = Instance.new("Folder")
	buildings.Name = "Buildings"
	buildings.Parent = workspace
end
local old = buildings:FindFirstChild("TeaHouse")
if old then
	old:Destroy()
end

local model, counts = BuildingBuilder.build("teahouse", ORIGIN, buildings)
BuildingBuilder.pave(model, ORIGIN, YARD)

-- Players spawn in the yard, looking at the porch (DevConfig.SpawnPath points here).
local spawn = Instance.new("SpawnLocation")
spawn.Name = "Spawn"
spawn.Anchored = true
spawn.CanCollide = false
spawn.Transparency = 1
spawn.Neutral = true
spawn.Size = Vector3.new(6, 1, 6)
spawn.CFrame = ORIGIN * CFrame.new(12, 0.5, 54)
spawn.Parent = model

game:GetService("ChangeHistoryService"):SetWaypoint("Build the tea house")
return counts

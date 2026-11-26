-- Break test: Workspace.BreakTest, beside the kit showcase.
-- Run on the SERVER during a playtest (Run mode is enough) so unsupported shards actually fall.
-- In edit mode it shows the same holes, but a shard that would fall stays hanging in the air.
--   1. the blasts from assets/out/broken.png (the "broken" scene in assets/preview.py)
--   2. a blast across the foot of a plain wall, which leaves the top with nothing under it
local ServerStorage = game:GetService("ServerStorage")

local Breakable = require(ServerStorage.DesertFps.Destruction.Breakable)
local BreakData = require(ServerStorage.DesertFps.Assets.BreakData)

-- piece, position, turn about Y in degrees, blast point (relative to the piece), blast radius
local SCENE = {
	{ "wall_plain", Vector3.new(-8, 0, 0), 0, Vector3.new(0.5, 6.5, 0), 3.0 },
	{ "wall_window", Vector3.new(0, 0, 0), 0, Vector3.new(3.2, 10.5, 0), 2.4 },
	{ "wall_door", Vector3.new(8, 0, 0), 0, Vector3.new(-2.8, 10.0, 0), 2.6 },
	{ "door", Vector3.new(7.65, 0, 1.15), -42, Vector3.new(0.3, 5.0, 0), 1.5 },
	{ "wall_plain", Vector3.new(-20, 0, 0), 0, Vector3.new(0, 1.5, 0), 4.5 },
}
local NAMES = { "ReferenceBlast", "WindowWall", "DoorWall", "Door", "FootBlast" }

local showcase = workspace:FindFirstChild("KitShowcase")
local origin = (if showcase then showcase.WorldPivot else CFrame.new(0, 0.05, 180)) * CFrame.new(-44, 0, 0)

local old = workspace:FindFirstChild("BreakTest")
if old then
	old:Destroy()
end
local folder = Instance.new("Folder")
folder.Name = "BreakTest"
folder.Parent = workspace

local results = {}
for index, entry in SCENE do
	local piece, position, turn, blastAt, radius = entry[1], entry[2], entry[3], entry[4], entry[5]
	local at = origin * CFrame.new(position) * CFrame.Angles(0, math.rad(turn), 0)
	local model = Breakable.place(piece, at, folder)
	model.Name = NAMES[index]
	local removed, dropped = Breakable.blast(model, at * blastAt, radius)
	table.insert(results, { name = model.Name, removed = removed, dropped = dropped })
end

-- broken.png also has the window lattice shot out.
for _, shard in BreakData.wall_window.chunks do
	if shard.id == "window" then
		local at = folder.WindowWall.WorldPivot * Vector3.new(shard.center[1], shard.center[2], shard.center[3])
		Breakable.blast(folder.WindowWall, at, 0.1)
	end
end

return results

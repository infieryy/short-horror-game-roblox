-- Break test for one plain wall. Run on the SERVER during a playtest (Run mode is enough),
-- so the unsupported shards actually fall.
-- Stands two walls outside the graybox and blasts them:
--   1. the blast from assets/out/broken.png (assets/preview.py: x 0.5, height 6.5, radius 3)
--   2. a blast across the foot of the wall, which leaves the top with nothing under it
local ServerStorage = game:GetService("ServerStorage")

local Breakable = require(ServerStorage.DesertFps.Destruction.Breakable)

local old = workspace:FindFirstChild("BreakTest")
if old then
	old:Destroy()
end
local folder = Instance.new("Folder")
folder.Name = "BreakTest"
folder.Parent = workspace

local results = {}
local function test(name: string, origin: CFrame, blastAt: Vector3, radius: number)
	local wall = Breakable.place("wall_plain", origin, folder)
	wall.Name = name
	local removed, dropped = Breakable.blast(wall, origin * blastAt, radius)
	table.insert(results, { name = name, removed = removed, dropped = dropped })
end

test("ReferenceBlast", CFrame.new(-10, 0, 140), Vector3.new(0.5, 6.5, 0), 3)
test("FootBlast", CFrame.new(10, 0, 140), Vector3.new(0, 1.5, 0), 4.5)
return results

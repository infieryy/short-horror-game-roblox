-- Test: buildings come down when what holds them up is destroyed (Destruction/Structure).
-- Run on the server during a playtest, with DevConfig.TestHooks on (the command bar gets its own copies of
-- the modules, so the test reaches the running game through ServerStorage.DesertFps.DevDamage).
-- It destroys ground-floor walls and counts what is left standing:
--   1. the west end of the Captain's House (two cells, two stories): that end falls, the rest stands
--   2. every ground wall of the Watchtower (three stories): the whole tower falls
-- Returns the counts. With DevConfig.RebuildSeconds set, everything stands again that many seconds later.
local ServerStorage = game:GetService("ServerStorage")

local hook = ServerStorage.DesertFps.DevDamage :: BindableFunction

local function standing(model: Instance): number
	local count = 0
	for _, piece in (model :: any).Structure:GetChildren() do
		if (piece:GetAttribute("Health") or 0) > 0 then
			count += 1
		end
	end
	return count
end

-- Destroys the ground-floor walls of `model` whose origin is inside the box (studs, world X and Z).
local function shootOut(model: Instance, x0: number, x1: number, z0: number, z1: number): number
	local destroyed = 0
	for _, piece in (model :: any).Structure:GetChildren() do
		local at = piece.WorldPivot.Position
		local wall = string.sub(piece.Name, 1, 5) == "wall2" and at.Y < 3
		if wall and at.X >= x0 - 0.6 and at.X <= x1 + 0.6 and at.Z >= z0 - 0.6 and at.Z <= z1 + 0.6 then
			local part = piece:FindFirstChildWhichIsA("BasePart", true)
			if part and (piece:GetAttribute("Health") or 0) > 0 then
				hook:Invoke(part, 1e6)
				destroyed += 1
			end
		end
	end
	return destroyed
end

local buildings = workspace.Buildings
local report = {}

local captain = buildings.CaptainsHouse
local before = standing(captain)
local walls = shootOut(captain, -788, -780, -88, -72) -- plan cells (9, 9) and (10, 9)
task.wait(5)
table.insert(report, `Captain's House: {before} pieces, {walls} ground walls of the west end destroyed, {standing(captain)} left standing`)

local tower = buildings.Watchtower
before = standing(tower)
walls = shootOut(tower, -1e6, 1e6, -1e6, 1e6)
task.wait(6)
table.insert(report, `Watchtower: {before} pieces, all {walls} ground walls destroyed, {standing(tower)} left standing`)

return table.concat(report, "\n")

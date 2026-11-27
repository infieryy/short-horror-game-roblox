-- Test: the marks shots leave. Run on the CLIENT during a playtest. It stands a plank, a wall, a stone and a
-- bush of its own in the air far above the town, seen by this client alone, works out the path of a shot
-- through each with the function the weapons use, and has Client/BulletMarks draw what the shot leaves. Then
-- it takes everything away again. Takes about two seconds. Returns one line per check, each starting "ok" or
-- "WRONG":
--   a shot through a plank leaves a way in on the near face and a way out on the far face, each looking out
--   the rifle goes through the wall (in, out); the pistol is stopped by it (a chip, no hole)
--   stone is chipped; leaves are not marked, only shaken
--   every mark throws up dust
--   a mark moves with what it is on
--   a wall that cracks (it is swapped for its shards, a little out of place) keeps its marks, on the shards
--   a mark goes when what it is on goes for good
--   there are never more marks than MarkConfig.Most
-- That the weapon in hand leaves these when it is fired, and that a second player sees them, is checked by
-- firing it: DevWeapon's "state" has the marks this client has drawn.
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.DesertFps
local Penetration = require(Shared.Weapons.Penetration)
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local BulletMarks = require(Shared.Client.BulletMarks)
local Config = require(Shared.Client.MarkConfig)

local RIFLE, PISTOL = WeaponConfig.Weapons.rifle.Pierce, WeaponConfig.Weapons.pistol.Pierce
local HIGH = 700 -- studs above the town

local lines = {}
local function check(right: boolean, what: string)
	table.insert(lines, (if right then "ok     " else "WRONG  ") .. what)
end

local stage = Instance.new("Folder")
stage.Name = "MarksTest"
stage.Parent = workspace
local drawn = Instance.new("Folder")
drawn.Name = "MarksTestDrawn"
drawn.Parent = workspace
local marks = BulletMarks.new(drawn)
local everything = RaycastParams.new()
everything.FilterType = Enum.RaycastFilterType.Exclude
everything.FilterDescendantsInstances = {}

-- Stands a slab of kit piece `piece` (what it is made of goes by that name), `thick` studs along Z, at stand
-- number `place`.
local function stand(place: number, piece: string, thick: number): BasePart
	local model = Instance.new("Model")
	model.Name = piece
	model:SetAttribute("Piece", piece)
	local slab = Instance.new("Part")
	slab.Name = "Whole"
	slab.Anchored = true
	slab.Size = Vector3.new(6, 6, thick)
	slab.Position = Vector3.new(place * 40, HIGH, 0)
	slab.Parent = model
	model.Parent = stage
	return slab
end

-- A shot along +Z through the middle of the slab: its path, and what it leaves.
local function shoot(slab: BasePart, pierce: number): (Penetration.Path, { Penetration.Mark })
	local path = Penetration.trace(slab.Position - Vector3.zAxis * 10, Vector3.zAxis, 40, pierce, everything)
	local left = Penetration.marks(path)
	marks:leave(left)
	return path, left
end

local function near(a: number, b: number, by: number): boolean
	return math.abs(a - b) <= by
end

-- The marks fixed to a part, by the face they are on: a shot along +Z goes in at the near (-Z) face.
local function drawnOn(slab: BasePart): { [string]: BasePart }
	local found = {}
	for _, child in drawn:GetChildren() do
		local weld = child:FindFirstChildOfClass("WeldConstraint")
		if child.Name == "BulletMark" and child:IsA("BasePart") and weld and weld.Part0 == slab then
			found[if child.Position.Z < slab.Position.Z then "near" else "far"] = child
		end
	end
	return found
end

-- How many balls of dust are in the air.
local function balls(): number
	local count = 0
	for _, child in drawn:GetChildren() do
		if child.Name ~= "BulletMark" then
			count += 1
		end
	end
	return count
end

local plank = stand(1, "door2_wood", 0.3)
local wall = stand(2, "wall2_plain", 1)
local stone = stand(3, "townwall", 3)
local bush = stand(4, "tree", 4)
task.wait() -- the slabs are there for a cast from the next step on

local _, left = shoot(plank, RIFLE)
local on = drawnOn(plank)
local lift = Config.Lift + Config.LiftSpread
check(
	#left == 2
		and on.near ~= nil
		and on.far ~= nil
		and near(on.near.Position.Z, plank.Position.Z - 0.15, lift + 0.011)
		and near(on.far.Position.Z, plank.Position.Z + 0.15, lift + 0.011)
		and on.near.CFrame.LookVector.Z < -0.99
		and on.far.CFrame.LookVector.Z > 0.99,
	("a plank: %d marks, one on each face, each looking out of it"):format(#left)
)
check(balls() == 2, ("each throws up dust: %d balls"):format(balls()))
local state = marks:state()
check(
	state.total == 2 and state["in"] == 1 and state.out == 1,
	("that is a way in and a way out: %d in, %d out"):format(state["in"] or 0, state.out or 0)
)

shoot(wall, RIFLE)
state = marks:state()
check(state["in"] == 2 and state.out == 2 and not state.stop, "the rifle goes through the wall: a way in and a way out")
shoot(wall, PISTOL)
state = marks:state()
check(state.stop == 1 and state["in"] == 2, ("the pistol is stopped by it: %d chip, no new hole"):format(state.stop or 0))

shoot(stone, RIFLE)
check(marks:state().stop == 2, "stone is chipped")

local ballsBefore = balls()
local total = marks:state().total
local path = shoot(bush, RIFLE)
check(
	#path.pierced == 1 and marks:state().total == total and balls() - ballsBefore == 2,
	("leaves: gone through, not marked, shaken (%d balls)"):format(balls() - ballsBefore)
)

-- A mark is fixed to what it is on.
local was = on.near.Position
plank.CFrame += Vector3.new(0, 5, 0)
for _ = 1, 3 do
	RunService.Heartbeat:Wait()
end
check(
	near((on.near.Position - was).Y, 5, 0.01),
	("a mark moves with what it is on: %.2f studs of 5"):format((on.near.Position - was).Y)
)

-- The wall cracks: the whole of it goes, and its shards stand in its place a moment later, a little out of
-- place. Its marks (a way in, a way out, a chip) move onto them.
local piece = wall.Parent :: Instance
local frame, size = wall.CFrame, wall.Size
total = marks:state().total
wall:Destroy()
task.delay(0.05, function()
	local shards = Instance.new("Folder")
	shards.Name = "Shards"
	local shard = Instance.new("Part")
	shard.Name = "a"
	shard.Anchored = true
	shard.Size = size
	shard.CFrame = frame * CFrame.new(0.03, 0, 0.05)
	shard.Parent = shards
	shards.Parent = piece
end)
task.wait(Config.Settle + 0.2)
local shard = piece:FindFirstChild("a", true) :: BasePart
local moved = drawnOn(shard)
check(
	marks:state().total == total
		and moved.near ~= nil
		and moved.far ~= nil
		and near(moved.near.Position.Z, shard.Position.Z - 0.5, lift + 0.011)
		and near(moved.far.Position.Z, shard.Position.Z + 0.5, lift + 0.011),
	("a wall that cracks keeps its marks, on its shards: %d of %d"):format(marks:state().total, total)
)

total = marks:state().total
piece:Destroy();
(plank.Parent :: Instance):Destroy()
task.wait(Config.Settle + 0.2)
check(marks:state().total == total - 5, ("a mark goes when what it is on goes for good: %d fewer"):format(total - marks:state().total))

for _ = 1, Config.Most + 10 do
	shoot(stone, RIFLE)
end
check(marks:state().total == Config.Most, ("never more than %d marks: %d"):format(Config.Most, marks:state().total))

stage:Destroy()
drawn:Destroy()
return table.concat(lines, "\n")

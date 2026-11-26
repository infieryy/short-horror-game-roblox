-- Break test: Workspace.BreakTest, beside the kit showcase.
-- Run on the SERVER during a playtest (Run mode is enough), then read what it returns. Every "ok" should be true.
--   a wall stays complete, cracks in stages as it loses health, and crumbles when the health runs out
--   a crate bursts when its health runs out, not before
--   a blast takes apart a piece it reaches and leaves alone one it does not
local ServerStorage = game:GetService("ServerStorage")

local Breakable = require(ServerStorage.DesertFps.Destruction.Breakable)
local DestructionConfig = require(ServerStorage.DesertFps.Destruction.DestructionConfig)

local showcase = workspace:FindFirstChild("KitShowcase")
local origin = (if showcase then showcase.WorldPivot else CFrame.new(0, 0.05, 180)) * CFrame.new(-60, 0, 0)

local old = workspace:FindFirstChild("BreakTest")
if old then
	old:Destroy()
end
local folder = Instance.new("Folder")
folder.Name = "BreakTest"
folder.Parent = workspace

local function stand(piece: string, x: number): Model
	return Breakable.place(piece, origin * CFrame.new(x, 0, 0), folder)
end
-- A shot into the front of a piece, at `height`.
local function shoot(model: Model, height: number, amount: number)
	local part = model:FindFirstChild("Whole") or model.Shards:GetChildren()[1]
	Breakable.damage(part, amount, model.WorldPivot * Vector3.new(0, height, 0.5), model.WorldPivot.LookVector)
end
local function shards(model: Model): number
	local found = model:FindFirstChild("Shards")
	return if found then #found:GetChildren() else 0
end

local results = {}

local wall = stand("wall_plain", 0)
local full = wall:GetAttribute("Health")
shoot(wall, 6, full * 0.2)
table.insert(results, { step = "wall at 80%", ok = wall:FindFirstChild("Whole") ~= nil and wall:GetAttribute("Cracks") == nil })
shoot(wall, 6, full * 0.2)
table.insert(results, { step = "wall at 60%: first cracks", ok = wall:GetAttribute("Cracks") == 1 and shards(wall) == 12 })
shoot(wall, 6, full * 0.3)
table.insert(results, { step = "wall at 30%: wider cracks", ok = wall:GetAttribute("Cracks") == 2 and shards(wall) == 12 })
shoot(wall, 6, full * 0.3)
table.insert(results, { step = "wall at 0: crumbles", ok = wall:GetAttribute("Health") == 0 and shards(wall) == 12 })

local crate = stand("crate", 12)
shoot(crate, 1.5, crate:GetAttribute("Health") - 1)
table.insert(results, { step = "crate with 1 health left", ok = crate:FindFirstChild("Whole") ~= nil })
shoot(crate, 1.5, 1)
table.insert(results, { step = "crate at 0: bursts", ok = crate:GetAttribute("Health") == 0 and shards(crate) == 8 })

local near, far = stand("wall_door", 24), stand("barrel", 40)
local blastAt = near.WorldPivot * Vector3.new(0, 6, 2)
table.insert(results, { step = "blast reaches the door wall", ok = Breakable.blast(near, blastAt, 4) })
table.insert(results, { step = "blast does not reach the barrel", ok = not Breakable.blast(far, blastAt, 4) })

-- Everything that came apart should be lying on the ground soon after, and gone once the rubble time is up.
task.wait(DestructionConfig.Crumble.chunks.Stagger + 2)
local highest = 0
for _, model in { wall, crate, near } do
	for _, part in model.Shards:GetChildren() do
		highest = math.max(highest, origin:PointToObjectSpace(part.Position).Y)
	end
end
table.insert(results, { step = "rubble is on the ground", ok = highest < 4, highest = highest })
task.wait(DestructionConfig.DebrisLifetime)
table.insert(results, { step = "rubble is cleared away", ok = wall.Parent == nil and crate.Parent == nil and near.Parent == nil })
table.insert(results, { step = "untouched barrel still stands", ok = far.Parent ~= nil and far:FindFirstChild("Whole") ~= nil })

return results

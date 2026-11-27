--!strict
-- Pre-cut destruction for map pieces. Server only.
-- A piece has one health and is always complete: it stands as one whole part, walls and doors crack along
-- their cuts as they take damage, and when the health runs out the whole piece comes apart into its shards.
-- Walls and doors ("chunks" in the break data) sag and fall, starting where they were hit; crates and
-- barrels ("shatter") burst. The rubble lies for a while, fades and is removed.
-- Shard layout and health come from assets/out/<piece>/<piece>.break.json. Its per-shard support data
-- (grounded, neighbors, touches) is not used: a piece never stands with parts missing.
-- What a piece was holding up comes down after it: see Structure, which listens to Breakable.Crumbled.

local Debris = game:GetService("Debris")
local PhysicsService = game:GetService("PhysicsService")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Config = require(script.Parent.DestructionConfig)
local BreakData = require(script.Parent.Parent.Assets.BreakData)

local Breakable = {}

Breakable.Tag = "Breakable"
-- Called with every piece as it comes apart, whatever took it down.
Breakable.Crumbled = {} :: { (model: Model) -> () }

type ShardData = { id: string, center: { number }, size: { number }, health: number }
type PieceData = { piece: string, mode: string, health: number?, chunks: { ShardData } }

local random = Random.new()

for _, group in { Config.DebrisGroup, Config.CharacterGroup } do
	if not PhysicsService:IsCollisionGroupRegistered(group) then
		PhysicsService:RegisterCollisionGroup(group)
	end
end
PhysicsService:CollisionGroupSetCollidable(Config.DebrisGroup, Config.CharacterGroup, false)

local function pieceData(piece: string): PieceData
	local data = BreakData[piece]
	assert(data, `no break data for piece "{piece}"`)
	return data
end

-- A crate or barrel carries its health in the data; a wall or door is as strong as its shards together.
local function fullHealth(data: PieceData): number
	if data.health then
		return data.health
	end
	local total = 0
	for _, shard in data.chunks do
		total += shard.health
	end
	return total
end

local function meshTemplates(piece: string): Instance?
	local node: Instance? = game:GetService(Config.MeshFolder[1])
	for i = 2, #Config.MeshFolder do
		node = node and node:FindFirstChild(Config.MeshFolder[i])
	end
	return node and node:FindFirstChild(piece)
end

local function standIn(size: Vector3): Part
	local part = Instance.new("Part")
	part.Size = size
	part.Color = Config.StandInColor
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part:SetAttribute("StandIn", true)
	return part
end

local function vector(values: { number }): Vector3
	return Vector3.new(values[1], values[2], values[3])
end

-- The box around every shard, relative to the piece origin (bottom centre).
local function pieceBounds(data: PieceData): (Vector3, Vector3)
	local lo = Vector3.new(math.huge, math.huge, math.huge)
	local hi = -lo
	for _, shard in data.chunks do
		local centre, half = vector(shard.center), vector(shard.size) / 2
		lo = lo:Min(centre - half)
		hi = hi:Max(centre + half)
	end
	return lo, hi
end

-- A house's own shade of plaster: the painted texture multiplied by `tint`.
local function paint(part: BasePart, tint: Color3?)
	local appearance = part:FindFirstChildOfClass("SurfaceAppearance")
	if tint and appearance then
		appearance.Color = tint
	end
end

-- The shards of a piece, built in place of the whole part the first time they are needed.
local function shardsOf(model: Model, data: PieceData): Instance
	local shards = model:FindFirstChild("Shards")
	if shards then
		return shards
	end
	local templates = meshTemplates(data.piece)
	local shardTemplates = templates and templates:FindFirstChild("Shards")
	local tint = model:GetAttribute("Tint") :: Color3?

	local built = Instance.new("Folder")
	built.Name = "Shards"
	for _, shard in data.chunks do
		local template = shardTemplates and shardTemplates:FindFirstChild(shard.id)
		local part: BasePart = if template and template:IsA("BasePart")
			then template:Clone()
			else standIn(vector(shard.size))
		part.Name = shard.id
		part.Anchored = true
		part.CFrame = model.WorldPivot * CFrame.new(vector(shard.center))
		paint(part, tint)
		part.Parent = built
	end
	local whole = model:FindFirstChild("Whole")
	if whole then
		whole:Destroy()
	end
	built.Parent = model
	return built
end

-- Opens the cracks of a damaged piece: every shard is pushed and turned a little out of place.
-- A shard leans the same way at every stage, only further.
local function crack(model: Model, data: PieceData, stage: number)
	local shards = shardsOf(model, data)
	local amount = Config.CrackStages[stage]
	for index, shard in data.chunks do
		local part = shards:FindFirstChild(shard.id)
		if part and part:IsA("BasePart") then
			local lean = Random.new(index)
			part.CFrame = model.WorldPivot
				* CFrame.new(vector(shard.center) + lean:NextUnitVector() * amount.Shift)
				* CFrame.fromAxisAngle(lean:NextUnitVector(), math.rad(amount.Tilt))
		end
	end
	model:SetAttribute("Cracks", stage)
end

-- Lets a shard go: it is thrown, tumbles, lies as rubble, fades and is removed.
local function fall(part: BasePart, velocity: Vector3)
	if not part.Parent then
		return
	end
	part.Anchored = false
	if RunService:IsRunning() then
		part:SetNetworkOwner(nil)
	end
	part.AssemblyLinearVelocity = velocity
	part.AssemblyAngularVelocity = random:NextUnitVector() * Config.Tumble
	local fade = TweenInfo.new(
		Config.DebrisFade,
		Enum.EasingStyle.Linear,
		Enum.EasingDirection.Out,
		0,
		false,
		Config.DebrisLifetime - Config.DebrisFade
	)
	TweenService:Create(part, fade, { Transparency = 1 }):Play()
end

-- Takes the whole piece apart. `push` is added to the shards nearest `point`, fading out with distance;
-- `blast` throws them away from `point` the same way.
local function crumble(model: Model, data: PieceData, point: Vector3, push: Vector3, blast: number)
	local how = (Config.Crumble :: any)[data.mode]
	local lo, hi = pieceBounds(data)
	local middle = model.WorldPivot * ((lo + hi) / 2)
	local reach = (hi - lo).Magnitude

	model:SetAttribute("Health", 0)
	for _, name in { "Ramp", "Climb" } do
		local unseen = model:FindFirstChild(name)
		if unseen then
			unseen:Destroy()
		end
	end
	for _, part in shardsOf(model, data):GetChildren() do
		if part:IsA("BasePart") then
			part.CollisionGroup = Config.DebrisGroup
			part.CanQuery = false
			part.CanTouch = false

			local near = 1 - math.clamp((part.Position - point).Magnitude / reach, 0, 1)
			local away, outward = part.Position - point, part.Position - middle
			local velocity = (push + (if away.Magnitude > 1e-3 then away.Unit else Vector3.zero) * blast) * near
				+ (if outward.Magnitude > 1e-3 then outward.Unit else Vector3.zero) * how.Outward
				+ random:NextUnitVector() * Vector3.new(1, 0, 1) * how.Scatter
			task.delay((1 - near) * how.Stagger, fall, part, velocity)
		end
	end
	Debris:AddItem(model, how.Stagger + Config.DebrisLifetime)
	for _, heard in Breakable.Crumbled do
		task.spawn(heard, model)
	end
end

-- The breakable piece a part belongs to, if it has not crumbled yet.
function Breakable.modelOf(part: Instance): Model?
	local model = part:FindFirstAncestorWhichIsA("Model")
	while model and model:GetAttribute("Piece") == nil do
		model = model:FindFirstAncestorWhichIsA("Model")
	end
	if model and (model:GetAttribute("Health") :: number) <= 0 then
		return nil
	end
	return model
end

-- Stands a whole, undamaged piece with its bottom centre at `origin`. `tint` gives it a house's own shade.
function Breakable.place(piece: string, origin: CFrame, parent: Instance?, tint: Color3?): Model
	local data = pieceData(piece)
	local templates = meshTemplates(piece)
	local template = templates and templates:FindFirstChild("Whole")

	local whole: BasePart, offset: Vector3
	if template and template:IsA("BasePart") then
		whole = template:Clone()
		offset = template:GetAttribute("Offset") :: Vector3
	else
		local lo, hi = pieceBounds(data)
		whole = standIn(hi - lo)
		offset = (lo + hi) / 2
	end
	whole.Name = "Whole"
	whole.Anchored = true
	whole.CFrame = origin * CFrame.new(offset)

	local model = Instance.new("Model")
	model.Name = piece
	model.WorldPivot = origin
	model:SetAttribute("Piece", piece)
	model:SetAttribute("Health", fullHealth(data))
	if tint then
		model:SetAttribute("Tint", tint)
		paint(whole, tint)
	end
	model:AddTag(Breakable.Tag)
	whole.Parent = model

	local rampSize = (Config.Ramps :: any)[piece]
	if rampSize then
		whole.CanCollide = false
		-- a wedge is tallest at its back (+Z); the pieces climb towards their own -Z
		local ramp = Instance.new("WedgePart")
		ramp.Name = "Ramp"
		ramp.Anchored = true
		ramp.Transparency = 1
		ramp.CanQuery = false
		ramp.Size = rampSize
		ramp.CFrame = origin * CFrame.new(0, rampSize.Y / 2, 0) * CFrame.Angles(0, math.pi, 0)
		ramp.Parent = model
	end
	local climb = (Config.Climbs :: any)[piece]
	if climb then
		local truss = Instance.new("TrussPart")
		truss.Name = "Climb"
		truss.Anchored = true
		truss.Transparency = 1
		truss.CanQuery = false
		truss.Size = climb.Size
		truss.CFrame = origin * CFrame.new(climb.Offset)
		truss.Parent = model
	end
	model.Parent = parent or workspace
	return model
end

-- Brings a standing piece down because nothing holds it up any more: it comes apart from the bottom.
function Breakable.collapse(model: Model)
	if model.Parent == nil or (model:GetAttribute("Health") :: number) <= 0 then
		return
	end
	local data = pieceData(model:GetAttribute("Piece") :: string)
	local lo, hi = pieceBounds(data)
	local foot = model.WorldPivot * Vector3.new((lo.X + hi.X) / 2, lo.Y, (lo.Z + hi.Z) / 2)
	crumble(model, data, foot, Vector3.zero, 0)
end

-- A shot that landed on `part` at `point`, travelling along the unit vector `direction`.
-- Returns whether the part belonged to a breakable piece.
function Breakable.damage(part: BasePart, amount: number, point: Vector3, direction: Vector3): boolean
	local model = Breakable.modelOf(part)
	if not model then
		return false
	end
	local data = pieceData(model:GetAttribute("Piece") :: string)
	local health = (model:GetAttribute("Health") :: number) - amount
	if health <= 0 then
		crumble(model, data, point, direction * Config.ShotPush, 0)
		return true
	end
	model:SetAttribute("Health", health)

	if data.mode == "chunks" then
		local left, stage = health / fullHealth(data), 0
		for index, entry in Config.CrackStages do
			if left <= entry.At then
				stage = index
			end
		end
		if stage > ((model:GetAttribute("Cracks") :: number?) or 0) then
			crack(model, data, stage)
		end
	end
	return true
end

-- An explosion at `point`. A piece with any shard centred within `radius` comes apart at once, thrown away
-- from the blast. Returns whether it did.
function Breakable.blast(model: Model, point: Vector3, radius: number): boolean
	if (model:GetAttribute("Health") :: number) <= 0 then
		return false
	end
	local data = pieceData(model:GetAttribute("Piece") :: string)
	for _, shard in data.chunks do
		if ((model.WorldPivot * vector(shard.center)) - point).Magnitude <= radius then
			crumble(model, data, point, Vector3.zero, Config.BlastPush)
			return true
		end
	end
	return false
end

return Breakable

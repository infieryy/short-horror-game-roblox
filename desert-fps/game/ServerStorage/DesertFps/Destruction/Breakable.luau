--!strict
-- Pre-cut destruction for map pieces. Server only.
-- A piece stands as one whole part until it is first hit, then is swapped for its shards.
-- Shard layout and the support graph come from assets/out/<piece>/<piece>.break.json.

local Debris = game:GetService("Debris")

local Config = require(script.Parent.DestructionConfig)
local BreakData = require(script.Parent.Parent.Assets.BreakData)

local Breakable = {}

type ShardData = {
	id: string,
	center: { number },
	size: { number },
	grounded: boolean,
	neighbors: { string },
}
type PieceData = { piece: string, mode: string, chunks: { ShardData } }

local function pieceData(piece: string): PieceData
	local data = BreakData[piece]
	assert(data, `no break data for piece "{piece}"`)
	-- TODO: "shatter" pieces (crate, barrel) have one health and burst into loose debris; not built yet.
	assert(data.mode == "chunks", `piece "{piece}" breaks by "{data.mode}", only "chunks" is supported so far`)
	return data
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

-- Stands a whole, undamaged piece with its bottom centre at `origin`.
function Breakable.place(piece: string, origin: CFrame, parent: Instance?): Model
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
	whole.Parent = model
	model.Parent = parent or workspace
	return model
end

-- Swaps the whole part for the shards. Does nothing if the piece is already in shards.
function Breakable.shatter(model: Model)
	local whole = model:FindFirstChild("Whole")
	if not whole then
		return
	end
	local piece = model:GetAttribute("Piece") :: string
	local templates = meshTemplates(piece)
	local shardTemplates = templates and templates:FindFirstChild("Shards")

	local shards = Instance.new("Folder")
	shards.Name = "Shards"
	for _, shard in pieceData(piece).chunks do
		local template = shardTemplates and shardTemplates:FindFirstChild(shard.id)
		local part: BasePart = if template and template:IsA("BasePart")
			then template:Clone()
			else standIn(vector(shard.size))
		part.Name = shard.id
		part.Anchored = true
		part.CFrame = model.WorldPivot * CFrame.new(vector(shard.center))
		part.Parent = shards
	end
	whole:Destroy()
	shards.Parent = model
end

-- Removes every shard whose centre is within `radius` of `point`, then lets go of every shard
-- that no longer has a chain of neighbours down to the ground.
-- Returns how many shards were removed and how many fell.
function Breakable.blast(model: Model, point: Vector3, radius: number): (number, number)
	local piece = model:GetAttribute("Piece") :: string
	local data = pieceData(piece)

	local whole = model:FindFirstChild("Whole")
	if whole and whole:IsA("BasePart") then
		-- Leave an untouched piece whole unless the blast reaches one of its shards.
		local reaches = false
		for _, shard in data.chunks do
			if ((model.WorldPivot * vector(shard.center)) - point).Magnitude <= radius then
				reaches = true
				break
			end
		end
		if not reaches then
			return 0, 0
		end
		Breakable.shatter(model)
	end

	local shards = model:FindFirstChild("Shards")
	if not shards then
		return 0, 0
	end

	local removed = 0
	local standing: { [string]: BasePart } = {}
	for _, part in shards:GetChildren() do
		if part:IsA("BasePart") then
			if (part.Position - point).Magnitude <= radius then
				part:Destroy()
				removed += 1
			else
				standing[part.Name] = part
			end
		end
	end

	-- Flood out from the shards that stand on the ground.
	local byId: { [string]: ShardData } = {}
	local supported: { [string]: boolean } = {}
	local queue: { string } = {}
	for _, shard in data.chunks do
		byId[shard.id] = shard
		if shard.grounded and standing[shard.id] then
			supported[shard.id] = true
			table.insert(queue, shard.id)
		end
	end
	-- TODO: a shard that touches a neighbouring piece (`touches` in the break data) should also count as held up.
	local head = 1
	while head <= #queue do
		for _, neighbour in byId[queue[head]].neighbors do
			if standing[neighbour] and not supported[neighbour] then
				supported[neighbour] = true
				table.insert(queue, neighbour)
			end
		end
		head += 1
	end

	local dropped = 0
	local fallen = model:FindFirstChild("Fallen")
	for id, part in standing do
		if not supported[id] then
			if not fallen then
				fallen = Instance.new("Folder")
				fallen.Name = "Fallen"
				fallen.Parent = model
			end
			part.Parent = fallen
			part.Anchored = false
			Debris:AddItem(part, Config.DebrisLifetime)
			dropped += 1
		end
	end
	return removed, dropped
end

return Breakable

--!strict
-- What holds what up. Server only.
-- Every piece under a registered root (Workspace.Buildings) stands on the ground or is held by other pieces:
-- a floor by the walls under it, an upper wall by the wall or the floor below, a lantern by its ceiling, a
-- sign by its wall. When a piece is destroyed, whatever it was the last thing holding comes down too, and so
-- on up the building. Breakable pieces crumble into their shards; loose pieces (lanterns, signs, banners,
-- rugs) drop and lie as rubble. A shot knocks a loose piece down directly.
-- The links are worked out once, from the boxes round the pieces as they stand (Config.Structure).

local CollectionService = game:GetService("CollectionService")
local Debris = game:GetService("Debris")
local TweenService = game:GetService("TweenService")

local Config = require(script.Parent.DestructionConfig)
local BreakData = require(script.Parent.Parent.Assets.BreakData)
local Breakable = require(script.Parent.Breakable)

local Structure = {}

local Rules = Config.Structure

type Entity = {
	piece: string,
	lo: Vector3,
	hi: Vector3,
	instance: Instance, -- the Breakable model, lamp model or loose part standing there now
	home: Instance, -- the folder it stands in
	breakable: boolean,
	bearing: boolean, -- can hold other pieces up
	span: boolean, -- a floor or roof slab
	hold: string, -- how it is held: "rests", "fixed" or "hangs"
	grounded: boolean,
	holders: { Entity }, -- pieces that can hold it up
	beside: { Entity }, -- for a span: the spans next to it
	holds: { Entity }, -- pieces it can hold up (holders and beside, the other way round)
	down: boolean,
	back: number, -- for a loose piece that is down: when it may be put back (os.clock)
}

local random = Random.new()
local byInstance: { [Instance]: Entity } = {}
local bySlot: { [string]: Entity } = {}
local roots: { Instance } = {}
-- Seconds until a destroyed piece is stood up again (a testing aid, DevConfig.RebuildSeconds); nil in a real round.
local rebuildSeconds: number? = nil

local function startsWith(piece: string, names: { string }): boolean
	for _, name in names do
		if string.sub(piece, 1, #name) == name then
			return true
		end
	end
	return false
end

-- The box in the world round a box in a piece's own space.
local function worldBox(cf: CFrame, lo: Vector3, hi: Vector3): (Vector3, Vector3)
	local centre, half = cf * ((lo + hi) / 2), (hi - lo) / 2
	local x, y, z = cf.XVector, cf.YVector, cf.ZVector
	local reach = Vector3.new(
		math.abs(x.X) * half.X + math.abs(y.X) * half.Y + math.abs(z.X) * half.Z,
		math.abs(x.Y) * half.X + math.abs(y.Y) * half.Y + math.abs(z.Y) * half.Z,
		math.abs(x.Z) * half.X + math.abs(y.Z) * half.Y + math.abs(z.Z) * half.Z
	)
	return centre - reach, centre + reach
end

local pieceBoxes: { [string]: { Vector3 } } = {}

-- The box round every shard of a breakable piece, relative to its origin.
local function pieceBox(piece: string): (Vector3, Vector3)
	local box = pieceBoxes[piece]
	if not box then
		local lo = Vector3.new(math.huge, math.huge, math.huge)
		local hi = -lo
		for _, shard in BreakData[piece].chunks do
			local centre = Vector3.new(shard.center[1], shard.center[2], shard.center[3])
			local half = Vector3.new(shard.size[1], shard.size[2], shard.size[3]) / 2
			lo, hi = lo:Min(centre - half), hi:Max(centre + half)
		end
		box = { lo, hi }
		pieceBoxes[piece] = box
	end
	return box[1], box[2]
end

local function partsOf(instance: Instance): { BasePart }
	local parts = {}
	if instance:IsA("BasePart") then
		table.insert(parts, instance)
	end
	for _, part in instance:GetDescendants() do
		if part:IsA("BasePart") then
			table.insert(parts, part)
		end
	end
	return parts
end

local function slot(piece: string, at: Vector3): string
	return `{piece}@{math.round(at.X * 10)},{math.round(at.Y * 10)},{math.round(at.Z * 10)}`
end

local function newEntity(piece: string, instance: Instance, lo: Vector3, hi: Vector3, breakable: boolean, groundY: number): Entity
	local hold = if startsWith(piece, Rules.Fixed) then "fixed" elseif startsWith(piece, Rules.Hangs) then "hangs" else "rests"
	return {
		piece = piece,
		lo = lo,
		hi = hi,
		instance = instance,
		home = instance.Parent :: Instance,
		breakable = breakable,
		bearing = breakable and startsWith(piece, Rules.Bearing),
		span = breakable and startsWith(piece, Rules.Spans),
		hold = hold,
		grounded = hold == "rests" and lo.Y <= groundY + Rules.GroundReach,
		holders = {},
		beside = {},
		holds = {},
		down = false,
		back = 0,
	}
end

-- Whether `under` can hold `over` up, given that they touch. `lapped`: one lies over the other.
local function canHold(under: Entity, over: Entity, lapped: boolean): boolean
	if not under.bearing or over.grounded then
		return false
	elseif over.hold == "fixed" then
		return true
	elseif over.hold == "hangs" then
		return under.hi.Y >= over.hi.Y - Rules.Lower
	end
	return lapped and under.lo.Y < over.lo.Y - Rules.Lower
end

local function link(a: Entity, b: Entity)
	local over = a.hi:Min(b.hi) - a.lo:Max(b.lo) -- how far the boxes overlap on each axis; negative is a gap
	if over.Y < -Rules.Touch or math.min(over.X, over.Z) < -Rules.Touch then
		return
	end
	local shared = math.max(over.X, over.Z) >= Rules.Share -- side by side along an edge, or one over the other
	local lapped = shared and math.min(over.X, over.Z) >= Rules.Overlap
	for _, pair in { { a, b }, { b, a } } do
		local under, top = pair[1], pair[2]
		if canHold(under, top, lapped) then
			table.insert(top.holders, under)
			table.insert(under.holds, top)
		end
	end
	if shared and a.span and b.span and math.abs(a.lo.Y - b.lo.Y) < Rules.Lower then
		table.insert(a.beside, b)
		table.insert(b.beside, a)
		table.insert(a.holds, b)
		table.insert(b.holds, a)
	end
end

-- How firmly a piece stands: 0 on the ground or on a standing piece; for a slab held only by the slabs beside
-- it, how many slabs away the nearest wall-borne one is; nil if nothing holds it. `footingOf` gives the same
-- for another piece. One slab beside it is not enough: it hangs between two.
local function footing(entity: Entity, footingOf: (Entity) -> number?): number?
	if entity.grounded then
		return 0
	end
	for _, holder in entity.holders do
		if footingOf(holder) ~= nil then
			return 0
		end
	end
	local nearest: number?, next: number? = nil, nil
	for _, other in entity.beside do
		local far = footingOf(other)
		if far and far < Rules.SpanReach then
			if nearest == nil or far < nearest then
				nearest, next = far, nearest
			elseif next == nil or far < next then
				next = far
			end
		end
	end
	return if next then next + 1 else nil
end

-- Works out the footing of every piece in `pieces`, given the footing of the pieces outside it.
local function footings(pieces: { Entity }, outside: (Entity) -> number?): { [Entity]: number }
	local found: { [Entity]: number } = {}
	local inside: { [Entity]: boolean } = {}
	for _, entity in pieces do
		inside[entity] = true
	end
	local function footingOf(entity: Entity): number?
		return if inside[entity] then found[entity] else outside(entity)
	end
	local changed = true
	while changed do
		changed = false
		for _, entity in pieces do
			if found[entity] ~= 0 then
				local firm = footing(entity, footingOf)
				if firm and (found[entity] == nil or firm < found[entity]) then
					found[entity] = firm
					changed = true
				end
			end
		end
	end
	return found
end

-- Whether a piece has anything at all left to hold it (used when one piece is stood up again).
local function hasHold(entity: Entity): boolean
	if entity.grounded then
		return true
	end
	for _, holder in entity.holders do
		if not holder.down then
			return true
		end
	end
	for _, other in entity.beside do
		if not other.down then
			return true
		end
	end
	return false
end

-- Lets a loose piece go: a copy of it falls, lies as rubble and fades; the piece itself is put away.
local function drop(entity: Entity)
	local standing = entity.instance
	if standing.Parent == nil then
		return
	end
	local rubble = standing:Clone()
	standing.Parent = nil
	local parts = partsOf(rubble)
	local first = parts[1]
	if not first then
		return
	end
	local fade = TweenInfo.new(Config.DebrisFade, Enum.EasingStyle.Linear, Enum.EasingDirection.Out, 0, false, Config.DebrisLifetime - Config.DebrisFade)
	for index, part in parts do
		part.CollisionGroup = Config.DebrisGroup
		part.CanCollide = true
		part.CanQuery = false
		part.CanTouch = false
		if index > 1 then
			local weld = Instance.new("WeldConstraint")
			weld.Part0 = first
			weld.Part1 = part
			weld.Parent = part
		end
	end
	rubble.Parent = workspace
	for _, part in parts do
		part.Anchored = false
		TweenService:Create(part, fade, { Transparency = 1 }):Play()
	end
	first:SetNetworkOwner(nil)
	first.AssemblyAngularVelocity = random:NextUnitVector() * Config.Tumble / 2
	Debris:AddItem(rubble, Config.DebrisLifetime)
end

local function putBack(entity: Entity)
	if entity.down and not entity.breakable and entity.home.Parent and os.clock() >= entity.back and hasHold(entity) then
		entity.down = false
		entity.instance.Parent = entity.home
	end
end

local function bringDown(entity: Entity)
	if entity.breakable then
		Breakable.collapse(entity.instance :: Model)
	else
		drop(entity)
	end
end

-- `gone` has just come down. Works out what it was the last thing holding and brings that down too.
local function settle(gone: Entity)
	-- everything that leaned on it, directly or through other pieces
	local affected: { [Entity]: boolean } = {}
	local queue: { Entity } = {}
	local function reach(from: Entity)
		for _, held in from.holds do
			if not held.down and not affected[held] then
				affected[held] = true
				table.insert(queue, held)
			end
		end
	end
	reach(gone)
	local index = 1
	while index <= #queue do
		reach(queue[index])
		index += 1
	end

	-- which of those still stand; everything else that is not down already stands as before
	local firm = footings(queue, function(entity: Entity): number?
		return if entity.down then nil else 0
	end)

	local from = (gone.lo + gone.hi) / 2
	for _, entity in queue do
		if firm[entity] == nil then
			entity.down = true
			local away = ((entity.lo + entity.hi) / 2 - from).Magnitude
			task.delay(away / Rules.Speed, bringDown, entity)
		end
	end
end

local function onCrumbled(model: Model)
	local entity = byInstance[model]
	if entity and not entity.down then
		entity.down = true
		settle(entity)
	end
end

-- A destroyed piece has been stood up again (the dev rebuild): it takes its old place in the structure.
local function onPlaced(model: Instance)
	if not model:IsA("Model") or byInstance[model] then
		return
	end
	local entity = bySlot[slot(model:GetAttribute("Piece") :: string, model.WorldPivot.Position)]
	if not entity or not entity.down then
		return
	end
	byInstance[entity.instance] = nil
	entity.instance = model
	byInstance[model] = entity
	entity.down = false
	if not hasHold(entity) then
		-- what held it is still down: it falls again, and is tried again later
		entity.down = true
		task.defer(bringDown, entity)
		return
	end
	for _, held in entity.holds do
		putBack(held)
	end
end

-- A shot landed on `part`. A loose piece (a lantern, a sign, a banner) is knocked down. Returns whether it was.
function Structure.knock(part: BasePart): boolean
	local entity = byInstance[part] or (part.Parent and byInstance[part.Parent])
	if not entity or entity.breakable or entity.down or startsWith(entity.piece, Rules.Unshakable) then
		return false
	end
	entity.down = true
	entity.back = if rebuildSeconds then os.clock() + rebuildSeconds else math.huge
	drop(entity)
	if rebuildSeconds then
		task.delay(rebuildSeconds + 0.1, putBack, entity)
	end
	return true
end

-- Takes every piece under `root` into the structure. `groundY` is street level. Pieces that nothing holds
-- as they are built (a rule does not cover them) are treated as standing on the ground, so they never fall
-- by themselves; the count of those comes back by piece name, with the number of pieces and links.
function Structure.register(root: Instance, groundY: number): { pieces: number, links: number, unheld: { [string]: number } }
	local entities: { Entity } = {}
	for _, instance in root:GetDescendants() do
		local parent = instance.Parent :: Instance
		if instance:IsA("Model") and instance:GetAttribute("Piece") ~= nil then
			if (instance:GetAttribute("Health") :: number) > 0 then
				local piece = instance:GetAttribute("Piece") :: string
				local lo, hi = worldBox(instance.WorldPivot, pieceBox(piece))
				local entity = newEntity(piece, instance, lo, hi, true, groundY)
				bySlot[slot(piece, instance.WorldPivot.Position)] = entity
				table.insert(entities, entity)
			end
		elseif (instance:IsA("Model") and parent.Name == "Lamps") or (instance:IsA("BasePart") and parent.Name == "Dressing") then
			if not startsWith(instance.Name, Rules.Ground) then
				local lo = Vector3.new(math.huge, math.huge, math.huge)
				local hi = -lo
				for _, part in partsOf(instance) do
					local a, b = worldBox(part.CFrame, -part.Size / 2, part.Size / 2)
					lo, hi = lo:Min(a), hi:Max(b)
				end
				table.insert(entities, newEntity(instance.Name, instance, lo, hi, false, groundY))
			end
		end
	end

	-- pieces that share a grid cell are tried against each other
	local cell = 8
	local buckets: { [number]: { Entity } } = {}
	for _, entity in entities do
		byInstance[entity.instance] = entity
		for x = math.floor((entity.lo.X - Rules.Touch) / cell), math.floor((entity.hi.X + Rules.Touch) / cell) do
			for z = math.floor((entity.lo.Z - Rules.Touch) / cell), math.floor((entity.hi.Z + Rules.Touch) / cell) do
				local key = x * 65536 + z
				local bucket = buckets[key]
				if not bucket then
					bucket = {}
					buckets[key] = bucket
				end
				table.insert(bucket, entity)
			end
		end
	end
	local tried: { [Entity]: { [Entity]: boolean } } = {}
	local links, done = 0, 0
	for _, bucket in buckets do
		for i = 1, #bucket - 1 do
			local a = bucket[i]
			local seen = tried[a]
			if not seen then
				seen = {}
				tried[a] = seen
			end
			for j = i + 1, #bucket do
				local b = bucket[j]
				if not seen[b] and not (tried[b] and tried[b][a]) then
					seen[b] = true
					local before = #a.holders + #b.holders + #a.beside
					link(a, b)
					links += #a.holders + #b.holders + #a.beside - before
				end
			end
		end
		done += 1
		if done % 200 == 0 then
			task.wait()
		end
	end

	-- a piece that nothing holds as built is pinned to the ground rather than left to fall at the first shot
	local unheld: { [string]: number } = {}
	local firm = footings(entities, function(): number?
		return nil
	end)
	for _, entity in entities do
		if firm[entity] == nil then
			entity.grounded = true
			unheld[entity.piece] = (unheld[entity.piece] or 0) + 1
		end
	end

	table.insert(roots, root)
	return { pieces = #entities, links = links, unheld = unheld }
end

-- Starts listening: pieces that crumble bring down what they held. Call once, before any register().
function Structure.start(rebuild: number?)
	rebuildSeconds = rebuild
	table.insert(Breakable.Crumbled, onCrumbled)
	CollectionService:GetInstanceAddedSignal(Breakable.Tag):Connect(function(model)
		for _, root in roots do
			if model:IsDescendantOf(root) then
				onPlaced(model)
				return
			end
		end
	end)
end

return Structure

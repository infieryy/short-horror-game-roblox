--!strict
-- Where every character's parts were over the last moment, and whether a shot hit them.
-- A shooter sees the others a little in the past, so the server cannot test a shot against where a target is
-- now. It keeps each tracked character's hit boxes for CombatConfig.Rewind.Keep seconds and tests a shot
-- against those, as boxes of its own: nothing in the world is moved back.

local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local CombatConfig = require(ReplicatedStorage:WaitForChild("DesertFps").Combat.CombatConfig)

local Hitboxes = {}

type Snapshot = { at: number, frames: { [string]: CFrame }, halves: { [string]: Vector3 } }
local tracked: { [Model]: { Snapshot } } = {}

-- How far along the ray (from `origin`, along unit `direction`) it enters the box, if it does.
local function enters(origin: Vector3, direction: Vector3, frame: CFrame, half: Vector3): number?
	local o, d = frame:PointToObjectSpace(origin), frame:VectorToObjectSpace(direction)
	local near, far = 0, math.huge
	for _, axis in { "X", "Y", "Z" } do
		local from, along, reach = (o :: any)[axis], (d :: any)[axis], (half :: any)[axis]
		if math.abs(along) < 1e-8 then
			if math.abs(from) > reach then
				return nil
			end
		else
			local a, b = (-reach - from) / along, (reach - from) / along
			near, far = math.max(near, math.min(a, b)), math.min(far, math.max(a, b))
			if near > far then
				return nil
			end
		end
	end
	return near
end

local function snapshot(character: Model, at: number): Snapshot
	local frames, halves = {}, {}
	for name in CombatConfig.Zones do
		local part = character:FindFirstChild(name)
		if part and part:IsA("BasePart") then
			frames[name] = part.CFrame
			halves[name] = part.Size / 2
		end
	end
	return { at = at, frames = frames, halves = halves }
end

function Hitboxes.track(character: Model)
	tracked[character] = {}
end

function Hitboxes.untrack(character: Model)
	tracked[character] = nil
end

-- The part of `character` the ray hits and how far along, looking at where the character was from `since`
-- until now. `claimed` is the part the shooter says it hit: if the ray hit that part at any of those moments,
-- that is the answer. Otherwise it is the first part the ray meets at the latest moment it meets any.
function Hitboxes.cast(
	character: Model,
	origin: Vector3,
	direction: Vector3,
	range: number,
	since: number,
	claimed: string?,
	margin: number?
): (string?, number?)
	local history = tracked[character]
	if not history then
		return nil, nil
	end
	local grow = Vector3.one * (margin or CombatConfig.HitMargin)
	local fallbackPart, fallbackDistance
	for index = #history, 1, -1 do
		local moment = history[index]
		if moment.at < since then
			break
		end
		if claimed and moment.frames[claimed] then
			local distance = enters(origin, direction, moment.frames[claimed], moment.halves[claimed] + grow)
			if distance and distance <= range then
				return claimed, distance
			end
		end
		if not fallbackPart then
			for name, frame in moment.frames do
				local distance = enters(origin, direction, frame, moment.halves[name] + grow)
				if distance and distance <= range and (not fallbackDistance or distance < fallbackDistance) then
					fallbackPart, fallbackDistance = name, distance
				end
			end
		end
	end
	return fallbackPart, fallbackDistance
end

function Hitboxes.start()
	RunService.Heartbeat:Connect(function()
		local now = os.clock()
		for character, history in tracked do
			if character.Parent == nil then
				tracked[character] = nil
				continue
			end
			table.insert(history, snapshot(character, now))
			while history[1] and history[1].at < now - CombatConfig.Rewind.Keep do
				table.remove(history, 1)
			end
		end
	end)
end

return Hitboxes

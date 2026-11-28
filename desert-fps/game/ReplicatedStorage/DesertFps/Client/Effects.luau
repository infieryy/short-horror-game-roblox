--!strict
-- How shots look on this client: the flash at a muzzle, the tracer, sparks off the town, and the burst of a
-- hit on a body. Client/EffectConfig says how each looks. All of it is two things: streaks (a tapered beam
-- that flies: a tracer, a spark, a shard) and flashes (a star of beams round a bright core, for an instant).

local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Config = require(script.Parent.EffectConfig)

local Effects = {}

type Pair = { number }
-- A streak in flight: its beam between a tail and a head, where and how fast it set off, how it falls, how
-- long the streak is and how long it lasts, and how far it may go (a tracer stops where its shot does).
type Streak = {
	beam: Beam,
	tail: Attachment,
	head: Attachment,
	from: Vector3,
	velocity: Vector3,
	gravity: number,
	long: number,
	wide: number,
	life: number,
	reach: number?,
	age: number,
}
-- A spike of a flash is drawn twice: wide in the flash's edge colour, and narrower and hot inside that, so
-- that it keeps its colour against a sunlit wall instead of washing out to white.
type Flash = { part: BasePart, spikes: { { beam: Beam, inner: Beam, tip: Attachment } }, core: BasePart, light: PointLight, shown: number }

-- The most spikes a flash has, the forward one apart.
local SPIKES = 6

local random = Random.new()
local parent: Instance? = nil
local host: BasePart? = nil -- holds the ends of every streak
local flying: { Streak } = {}
local resting: { Streak } = {}
local flashes: { Flash } = {}
local shown: { [string]: number } = {} -- how often each effect has been shown, for tests

local function between(pair: Pair): number
	return random:NextNumber(pair[1], pair[2])
end

local function count(what: string)
	shown[what] = (shown[what] or 0) + 1
end

local function unseen(part: BasePart)
	part.Anchored = true
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
	part.CastShadow = false
end

-- A beam that is wide at one end and a point at the other, glowing: a spike, a spark, a shard.
local function taper(from: Attachment, to: Attachment): Beam
	local beam = Instance.new("Beam")
	beam.Attachment0 = from
	beam.Attachment1 = to
	beam.FaceCamera = true
	beam.Segments = 1
	beam.LightEmission = 0.7
	beam.LightInfluence = 0
	beam.Brightness = 2
	beam.Enabled = false
	return beam
end

-- A unit vector within `cone` degrees of `along`.
local function within(along: Vector3, cone: number): Vector3
	local frame = CFrame.lookAlong(Vector3.zero, along, if math.abs(along.Y) > 0.99 then Vector3.xAxis else Vector3.yAxis)
	local off = math.rad(random:NextNumber(0, cone))
	local round = random:NextNumber(0, math.pi * 2)
	return (frame * CFrame.Angles(0, 0, round) * CFrame.Angles(off, 0, 0)).LookVector
end

-- Sends a streak off from `from` at `velocity`. Its head is `hot` and `wide`, its tail `cool` and a point;
-- `clear` makes the tail fade to nothing as well (a tracer), where a spark or a shard is solid to its tip.
-- `glow` is how much it adds its light to what is behind it, 0 to 1: something hot glows; something with a
-- colour of its own must not, or a sunlit wall behind it washes the colour out to white.
local function streak(
	from: Vector3,
	velocity: Vector3,
	long: number,
	wide: number,
	life: number,
	gravity: number,
	hot: Color3,
	cool: Color3,
	clear: boolean,
	glow: number,
	reach: number?
)
	local anchor = host :: BasePart
	local it = table.remove(resting)
	if not it then
		local tail, head = Instance.new("Attachment"), Instance.new("Attachment")
		tail.Parent, head.Parent = anchor, anchor
		local beam = taper(tail, head)
		beam.Width0 = 0
		beam.Parent = anchor
		it = { beam = beam, tail = tail, head = head } :: any
	end
	local made = it :: Streak
	made.from, made.velocity, made.gravity = from, velocity, gravity
	made.long, made.wide, made.life, made.reach, made.age = long, wide, life, reach, 0
	made.beam.Color = ColorSequence.new(cool, hot)
	-- A tracer is clear at its tail and solid over its leading half.
	made.beam.Transparency = if clear
		then NumberSequence.new({ NumberSequenceKeypoint.new(0, 1), NumberSequenceKeypoint.new(0.5, 0.25), NumberSequenceKeypoint.new(1, 0) })
		else NumberSequence.new(0.15, 0)
	made.beam.Width1 = wide
	made.beam.LightEmission = glow
	made.beam.Brightness = 1 + glow
	made.tail.WorldPosition, made.head.WorldPosition = from, from
	made.beam.Enabled = true
	table.insert(flying, made)
end

local function fly(dt: number)
	for index = #flying, 1, -1 do
		local it = flying[index]
		it.age += dt
		local t = math.min(it.age, it.life)
		local gone = it.velocity.Magnitude * t
		local over = it.age >= it.life
		if it.reach then
			-- A tracer: straight, and it stops where its shot did. Its tail catches up, and then it is over.
			local along = it.velocity.Unit
			local head = math.min(it.velocity.Magnitude * it.age, it.reach)
			local tail = math.clamp(it.velocity.Magnitude * it.age - it.long, 0, it.reach)
			it.head.WorldPosition = it.from + along * head
			it.tail.WorldPosition = it.from + along * tail
			over = tail >= it.reach
		else
			local down = Vector3.new(0, -it.gravity, 0)
			local at = it.from + it.velocity * t + down * (t * t / 2)
			local heading = it.velocity + down * t
			it.head.WorldPosition = at
			it.tail.WorldPosition = at - heading.Unit * math.min(it.long, gone)
			-- It thins to nothing as it dies.
			it.beam.Width1 = it.wide * (1 - t / it.life)
		end
		if over then
			it.beam.Enabled = false
			table.remove(flying, index)
			table.insert(resting, it)
		end
	end
end

-- `where` is where the effects are drawn. Call once.
function Effects.start(where: Instance)
	parent = where
	local anchor = Instance.new("Part")
	anchor.Name = "Streaks"
	anchor.Transparency = 1
	anchor.Size = Vector3.one * 0.2
	unseen(anchor)
	anchor.Parent = where
	host = anchor
	RunService.RenderStepped:Connect(fly)
end

local function newFlash(): Flash
	local part = Instance.new("Part")
	part.Name = "Flash"
	part.Transparency = 1
	part.Size = Vector3.one * 0.2
	unseen(part)
	local middle = Instance.new("Attachment")
	middle.Parent = part
	local spikes = {}
	for _ = 1, SPIKES + 1 do
		local tip = Instance.new("Attachment")
		tip.Parent = part
		local beam, inner = taper(middle, tip), taper(middle, tip)
		beam.Width1, inner.Width1 = 0, 0
		beam.LightEmission = 0.25
		inner.ZOffset = 0.02
		beam.Parent, inner.Parent = part, part
		table.insert(spikes, { beam = beam, inner = inner, tip = tip })
	end
	local core = Instance.new("Part")
	core.Shape = Enum.PartType.Ball
	core.Material = Enum.Material.Neon
	unseen(core)
	local light = Instance.new("PointLight")
	light.Shadows = false
	light.Enabled = false
	light.Parent = part
	part.Parent = parent
	return { part = part, spikes = spikes, core = core, light = light, shown = 0 }
end

-- A star of a flash at `frame`, looking along it: spikes to the sides and a longer one forward, `size` times
-- as big as EffectConfig.Muzzle makes it. With `lit` it lights what is near.
local function flash(frame: CFrame, size: number, hot: Color3, edge: Color3, lit: boolean)
	local how = Config.Muzzle
	local it: Flash? = nil
	for _, each in flashes do
		if each.shown == 0 then
			it = each
			break
		end
	end
	if not it then
		it = newFlash()
		table.insert(flashes, it)
	end
	local made = it :: Flash
	made.shown += 1
	local showing = made.shown
	made.part.CFrame = frame
	local sides = random:NextInteger(how.Spikes[1], how.Spikes[2])
	local turn = random:NextNumber(0, math.pi * 2)
	for index, spike in made.spikes do
		local beam, inner = spike.beam, spike.inner
		beam.Color = ColorSequence.new(edge)
		beam.Transparency = NumberSequence.new(0.05, 0.3)
		inner.Color = ColorSequence.new(hot)
		inner.Transparency = NumberSequence.new(0, 0.2)
		local wide = 0
		if index == 1 then
			spike.tip.Position = Vector3.new(0, 0, -between(how.Forward) * size)
			wide = how.ForwardWide * size
		elseif index - 1 <= sides then
			local angle = turn + (index - 1 + random:NextNumber(-0.25, 0.25)) / sides * math.pi * 2
			spike.tip.Position = Vector3.new(math.cos(angle), math.sin(angle), -0.15) * between(how.Long) * size
			wide = between(how.Wide) * size
		end
		beam.Width0, inner.Width0 = wide, wide * how.Inner
		beam.Enabled, inner.Enabled = wide > 0, wide > 0
	end
	made.core.Color = hot
	made.core.Size = Vector3.one * how.Core * size
	made.core.CFrame = frame
	made.core.Parent = made.part
	made.light.Color = how.Light.Color
	made.light.Range = how.Light.Range
	made.light.Brightness = how.Light.Brightness
	made.light.Enabled = lit
	task.delay(how.Time, function()
		if made.shown ~= showing then
			return
		end
		for _, spike in made.spikes do
			spike.beam.Enabled, spike.inner.Enabled = false, false
		end
		made.core.Parent = nil
		made.light.Enabled = false
		made.shown = 0
	end)
end

-- A shot leaves the muzzle at `frame`, which looks along the barrel. `weapon` is its name; `quiet` is a
-- weapon that hides its shot (a wisp of smoke and no flash); `mine` is the player's own, seen from behind it.
function Effects.muzzle(frame: CFrame, weapon: string, quiet: boolean, mine: boolean)
	local how = Config.Muzzle
	local size = ((how.Size :: any)[weapon] or 1) * (if mine then how.Mine else 1)
	if quiet then
		local wisp = Instance.new("Part")
		wisp.Shape = Enum.PartType.Ball
		wisp.Material = Enum.Material.SmoothPlastic
		wisp.Color = how.Quiet.Color
		wisp.Transparency = how.Quiet.Start
		wisp.Size = Vector3.one * how.Quiet.From * size
		unseen(wisp)
		wisp.CFrame = frame
		wisp.Parent = parent
		TweenService:Create(wisp, TweenInfo.new(how.Quiet.Time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
			Size = Vector3.one * how.Quiet.To * size,
			Position = (frame * CFrame.new(0, 0, -how.Quiet.To * size)).Position,
			Transparency = 1,
		}):Play()
		Debris:AddItem(wisp, how.Quiet.Time)
		count("wisp")
		return
	end
	flash(frame, size, how.Hot, how.Edge, true)
	count("flash")
end

-- The tracer of a shot from `from` that ended at `to`.
function Effects.tracer(from: Vector3, to: Vector3)
	local how = Config.Tracer
	local reach = (to - from).Magnitude
	if reach < how.Least then
		return
	end
	streak(from, (to - from).Unit * how.Speed, how.Long, how.Wide, reach / how.Speed + 1, 0, how.Hot, how.Tail, true, how.Glow, reach)
	count("tracer")
end

-- Sparks off the town where a shot left a mark of that kind, out of the surface along `normal`. `chip` is
-- the colour of what the surface is made of; with none the sparks are hot.
function Effects.sparks(at: Vector3, normal: Vector3, kind: string, chip: Color3?)
	local how = Config.Sparks
	local what = (how :: any)[kind]
	if not what then
		return
	end
	local colour = chip or how.Hot
	local glow = if chip then 0 else how.Glow
	for _ = 1, random:NextInteger(what.Count[1], what.Count[2]) do
		streak(at, within(normal, how.Cone) * between(what.Speed), between(how.Long), how.Wide, between(what.Life), how.Gravity, colour, colour, false, glow)
	end
	count("sparks")
end

-- A shot landed on a body at `at`, in that zone (CombatConfig.Zones' names: "head", or anything else for
-- the rest), travelling along `along`. Shards burst back the way it came.
function Effects.struck(at: Vector3, zone: string, along: Vector3)
	local all = Config.Struck
	local how = if zone == "head" then all.head else all.body
	local back = if along.Magnitude > 0.5 then -along.Unit else Vector3.yAxis
	for _ = 1, random:NextInteger(how.Count[1], how.Count[2]) do
		streak(at, within(back, all.Cone) * between(how.Speed), between(how.Long), between(how.Wide), between(how.Life), all.Gravity, how.Hot, how.Edge, false, how.Glow)
	end
	if zone == "head" then
		flash(CFrame.lookAlong(at, back), all.head.Flash, how.Hot, how.Edge, false)
	end
	count(if zone == "head" then "head" else "body")
end

-- How often each effect has been shown, and how many streaks are in flight, for tests.
function Effects.state(): { [string]: number }
	local counts = table.clone(shown)
	counts.flying = #flying
	return counts
end

return Effects

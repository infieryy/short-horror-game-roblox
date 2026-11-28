--!strict
-- How shots look on this client: the flash at a muzzle, the tracer, the spark where a shot lands, and the
-- burst of a hit on a body or a head. Each but the tracer is a flipbook: sixteen drawn frames on one image,
-- played once on a single particle (assets/vfx/flipbooks.py draws them, to Valorant's frames; Client/
-- EffectConfig says which image, how big and for how long).

local ContentProvider = game:GetService("ContentProvider")
local Debris = game:GetService("Debris")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")

local Config = require(script.Parent.EffectConfig)

local Effects = {}

-- Something that shows flipbooks at a place: a point with a particle emitter for each kind of flipbook it
-- has shown, and a light. `follow` says where it is now, while it shows (a flash stays on its barrel, a hit
-- on the body it landed on). `busy` is until when.
type Rig = {
	part: BasePart,
	point: Attachment,
	emitters: { [string]: ParticleEmitter },
	light: PointLight,
	follow: (() -> CFrame?)?,
	busy: number,
}
type Line = { beam: Beam, from: Attachment, to: Attachment, busy: number }

local parent: Instance? = nil
local rigs: { Rig } = {}
local lines: { Line } = {}
local shown: { [string]: number } = {} -- how often each effect has been shown, for tests

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

-- An image in EffectConfig is an asset's number, or (to try a sheet out in Studio before it is uploaded) a
-- whole content address such as rbxasset://claude_fx/fx_muzzle.png.
local function content(id: number | string): string
	return if type(id) == "string" then id else "rbxassetid://" .. id
end

local function step()
	local now = os.clock()
	for _, rig in rigs do
		if rig.busy > now and rig.follow then
			local frame = rig.follow()
			if frame then
				rig.part.CFrame = frame
			end
		end
	end
	for _, line in lines do
		if line.busy ~= 0 and line.busy <= now then
			line.beam.Enabled = false
			line.busy = 0
		end
	end
end

-- `where` is where the effects are drawn. Call once.
function Effects.start(where: Instance)
	parent = where
	RunService.RenderStepped:Connect(step)
	-- Fetched now: a flipbook whose image has not arrived when it is played shows nothing at all.
	task.spawn(function()
		ContentProvider:PreloadAsync({
			content(Config.Muzzle.Image),
			content(Config.Tracer.Image),
			content(Config.Spark.Image),
			content(Config.Struck.body.Image),
			content(Config.Struck.head.Image),
		})
	end)
end

local function freeRig(): Rig
	local now = os.clock()
	for _, rig in rigs do
		if rig.busy <= now and not rig.light.Enabled then
			return rig
		end
	end
	local part = Instance.new("Part")
	part.Name = "Effect"
	part.Transparency = 1
	part.Size = Vector3.one * 0.2
	unseen(part)
	local point = Instance.new("Attachment")
	point.Parent = part
	local light = Instance.new("PointLight")
	light.Shadows = false
	light.Enabled = false
	light.Parent = part
	part.Parent = parent
	local rig: Rig = { part = part, point = point, emitters = {}, light = light, follow = nil, busy = 0 }
	table.insert(rigs, rig)
	return rig
end

-- Plays the flipbook `how` (an EffectConfig entry: Image, Time, Glow, Near) once at `frame`, `size` studs
-- across its frame. `kind` names it. Returns the rig it plays on.
local function play(kind: string, how: any, frame: CFrame, size: number, follow: (() -> CFrame?)?): Rig
	local rig = freeRig()
	local emitter = rig.emitters[kind]
	if not emitter then
		emitter = Instance.new("ParticleEmitter")
		emitter.Texture = content(how.Image)
		emitter.FlipbookLayout = Enum.ParticleFlipbookLayout.Grid4x4
		emitter.FlipbookMode = Enum.ParticleFlipbookMode.OneShot
		emitter.Lifetime = NumberRange.new(how.Time)
		emitter.Rate = 0
		emitter.Speed = NumberRange.new(0)
		emitter.Rotation = NumberRange.new(0)
		emitter.RotSpeed = NumberRange.new(0)
		emitter.Transparency = NumberSequence.new(0)
		emitter.LightEmission = how.Glow
		emitter.LightInfluence = 0
		emitter.ZOffset = how.Near or 0
		emitter.LockedToPart = true
		emitter.Enabled = false
		emitter.Parent = rig.point
		rig.emitters[kind] = emitter
	end
	rig.part.CFrame = frame
	rig.follow = follow
	rig.busy = os.clock() + how.Time
	emitter.Size = NumberSequence.new(size)
	emitter:Emit(1)
	count(kind)
	return rig
end

-- A shot leaves the muzzle at `frame`, which looks along the barrel. `weapon` is its name; `quiet` is a
-- weapon that hides its shot (a wisp of smoke and no flash); `follow` says where the muzzle is from then on,
-- so that the flash stays on a barrel that kicks.
function Effects.muzzle(frame: CFrame, weapon: string, quiet: boolean, follow: (() -> CFrame?)?)
	local how = Config.Muzzle
	if quiet then
		local smoke = how.Quiet
		local wisp = Instance.new("Part")
		wisp.Shape = Enum.PartType.Ball
		wisp.Material = Enum.Material.SmoothPlastic
		wisp.Color = smoke.Color
		wisp.Transparency = smoke.Start
		wisp.Size = Vector3.one * smoke.From
		unseen(wisp)
		wisp.CFrame = frame
		wisp.Parent = parent
		TweenService:Create(wisp, TweenInfo.new(smoke.Time, Enum.EasingStyle.Quad, Enum.EasingDirection.Out), {
			Size = Vector3.one * smoke.To,
			Position = (frame * CFrame.new(0, 0, -smoke.To)).Position,
			Transparency = 1,
		}):Play()
		Debris:AddItem(wisp, smoke.Time)
		count("wisp")
		return
	end
	-- The flash stands upright on the screen whichever way the barrel points: only where it is follows.
	local rig = play("flash", how, frame, (how.Size :: any)[weapon] or how.Size.rifle, follow)
	rig.light.Color = how.Light.Color
	rig.light.Range = how.Light.Range
	rig.light.Brightness = how.Light.Brightness
	rig.light.Enabled = true
	task.delay(how.Light.Time, function()
		rig.light.Enabled = false
	end)
end

-- The tracer of a shot from `from` that ended at `to`: a line all the way, there for an instant.
function Effects.tracer(from: Vector3, to: Vector3)
	local how = Config.Tracer
	if (to - from).Magnitude < how.Least then
		return
	end
	local line: Line? = nil
	for _, each in lines do
		if each.busy == 0 then
			line = each
			break
		end
	end
	if not line then
		local host = Instance.new("Part")
		host.Name = "Tracer"
		host.Transparency = 1
		host.Size = Vector3.one * 0.2
		unseen(host)
		local a, b = Instance.new("Attachment"), Instance.new("Attachment")
		a.Parent, b.Parent = host, host
		local beam = Instance.new("Beam")
		beam.Attachment0, beam.Attachment1 = a, b
		beam.Texture = content(how.Image)
		beam.TextureMode = Enum.TextureMode.Stretch
		beam.TextureLength = 1
		beam.TextureSpeed = 0
		beam.FaceCamera = true
		beam.Segments = 1
		beam.LightEmission = how.Glow
		beam.LightInfluence = 0
		beam.Width0, beam.Width1 = how.Wide, how.Thin
		beam.Transparency = NumberSequence.new(0, how.Fade)
		beam.Parent = host
		host.Parent = parent
		line = { beam = beam, from = a, to = b, busy = 0 }
		table.insert(lines, line)
	end
	local made = line :: Line
	made.from.WorldPosition, made.to.WorldPosition = from, to
	made.beam.Enabled = true
	made.busy = os.clock() + how.Time
	count("tracer")
end

-- A shot landed at `at`, on anything: a small spark, at once, that stays where it is.
function Effects.landed(at: Vector3)
	play("spark", Config.Spark, CFrame.new(at), Config.Spark.Size)
end

-- The body part nearest a point, if one is within reach of it.
local function bodyPartAt(at: Vector3): BasePart?
	local best: BasePart?, nearest = nil, math.huge
	for _, part in workspace:GetPartBoundsInRadius(at, Config.Struck.Reach) do
		local model = part:FindFirstAncestorWhichIsA("Model")
		if model and model:FindFirstChildOfClass("Humanoid") then
			local away = (part.Position - at).Magnitude
			if away < nearest then
				best, nearest = part, away
			end
		end
	end
	return best
end

-- The server says a shot landed on a body at `at`, in that zone ("head", or anything else for the rest).
-- The burst stays on the part of the body it landed on, as that moves.
function Effects.struck(at: Vector3, zone: string)
	local head = zone == "head"
	local how = if head then Config.Struck.head else Config.Struck.body
	-- The head's flame stands on the hit: the hit is at the foot of its frame, not its middle.
	local lift = Vector3.new(0, (how.Foot or 0) * how.Size / 2, 0)
	local on = bodyPartAt(at)
	local follow: (() -> CFrame?)? = nil
	if on then
		local held = on.CFrame:PointToObjectSpace(at)
		follow = function(): CFrame?
			return if on.Parent then CFrame.new(on.CFrame:PointToWorldSpace(held) + lift) else nil
		end
	end
	play(if head then "head" else "body", how, CFrame.new(at + lift), how.Size, follow)
end

-- How often each effect has been shown, and how many are showing now, for tests.
function Effects.state(): { [string]: number }
	local counts = table.clone(shown)
	local now, showing = os.clock(), 0
	for _, rig in rigs do
		if rig.busy > now or rig.light.Enabled then
			showing += 1
		end
	end
	for _, line in lines do
		if line.busy ~= 0 then
			showing += 1
		end
	end
	counts.showing = showing
	return counts
end

return Effects

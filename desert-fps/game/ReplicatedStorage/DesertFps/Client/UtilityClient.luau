--!strict
-- The player's side of the utility: the key that throws it, the dart in flight, its pulses, and the outlines
-- of whoever the player's own dart saw. The server decides where a dart goes and what it sees
-- (UtilityService); this shows it.

local ContextActionService = game:GetService("ContextActionService")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local TweenService = game:GetService("TweenService")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("DesertFps")
local Config = require(script.Parent.Parent.Utility.UtilityConfig)
local HudConfig = require(script.Parent.HudConfig)

local UtilityClient = {}

-- A piece is modelled pointing along +X; this turns a frame that looks along a direction into the piece's.
local AIM = CFrame.Angles(0, math.pi / 2, 0)
local Look = Config.Look

-- What the weapons lend it: the display, where to draw, and the player's hands.
export type Hands = {
	hud: any,
	effects: Instance,
	-- Whether the player can throw now: alive, a weapon in hand, nothing else going on.
	free: () -> boolean,
	-- Puts the weapon away for `seconds`, calls `released` if the player is still alive then, and draws the
	-- weapon again.
	lower: (seconds: number, released: () -> ()) -> (),
}

local hands: Hands
local left: { [string]: number } = {}
local throwing = false
-- Whoever the player's darts saw: their outline, and when it ends.
local outlined: { [Model]: { highlight: Highlight, ends: number } } = {}

local function remote(name: string): RemoteEvent
	return Shared:WaitForChild("Remotes"):WaitForChild(name) :: RemoteEvent
end

local function show(name: string)
	local what = (Config.Utilities :: any)[name]
	local key = UserInputService:GetStringForKeyCode(what.Key)
	hands.hud:setUtility(table.find(Config.Loadout, name), what.Title, if key == "" then what.Key.Name else key, left[name] or 0)
end

-- Throws the utility of that name, as its key does. False if it cannot be thrown now.
function UtilityClient.use(name: string): boolean
	local what = (Config.Utilities :: any)[name]
	if not what or throwing or (left[name] or 0) < 1 or not hands.free() then
		return false
	end
	throwing = true
	hands.lower(what.ThrowTime, function()
		local camera = workspace.CurrentCamera
		remote("UseUtility"):FireServer(name, camera.CFrame.Position, camera.CFrame.LookVector)
		-- The server says how many are left; until it does, this is one fewer.
		left[name] = math.max((left[name] or 1) - 1, 0)
		show(name)
	end)
	task.delay(what.ThrowTime, function()
		throwing = false
	end)
	return true
end

-- What the player carries and who is outlined now, for tests.
function UtilityClient.state(): { left: { [string]: number }, outlined: { Model } }
	local seen = {}
	for character in outlined do
		table.insert(seen, character)
	end
	return { left = table.clone(left), outlined = seen }
end

-- A copy of a utility's model for this client alone, as big as it is in the game.
local function copy(what: any): Model
	local model = (Shared:WaitForChild("UtilityModels") :: Instance):WaitForChild(what.Model):Clone() :: Model
	for _, part in model:GetChildren() do
		if part:IsA("BasePart") then
			part.Size *= what.Size
		end
	end
	return model
end

local function place(model: Model, frame: CFrame, size: number)
	for _, part in model:GetChildren() do
		if part:IsA("BasePart") then
			part.CFrame = frame * CFrame.new((part:GetAttribute("Offset") :: Vector3) * size)
		end
	end
end

-- A dart in flight: drawn here from where it started and how fast, for as long as the server said it flies.
-- The dart that is stuck afterwards is the server's own.
local function fly(name: string, origin: Vector3, velocity: Vector3, seconds: number)
	local what = (Config.Utilities :: any)[name]
	if not what then
		return
	end
	local model = copy(what)
	local started = os.clock()
	local down = Vector3.new(0, -what.Gravity, 0)
	local function at(t: number): CFrame
		return CFrame.lookAlong(origin + velocity * t + down * (t * t / 2), velocity + down * t) * AIM
	end
	place(model, at(0), what.Size)
	model.Parent = hands.effects
	local flying: RBXScriptConnection
	flying = RunService.RenderStepped:Connect(function()
		local t = os.clock() - started
		if t >= seconds then
			flying:Disconnect()
			model:Destroy()
		else
			place(model, at(t), what.Size)
		end
	end)
end

-- A pulse: a bubble of the dart's light that grows and fades.
local function pulse(at: Vector3)
	local bubble = Instance.new("Part")
	bubble.Shape = Enum.PartType.Ball
	bubble.Material = Enum.Material.Neon
	bubble.Color = Look.Light
	bubble.Transparency = 0.45
	bubble.Anchored = true
	bubble.CanCollide = false
	bubble.CanQuery = false
	bubble.CanTouch = false
	bubble.CastShadow = false
	bubble.Size = Vector3.one * 0.4
	bubble.Position = at
	bubble.Parent = hands.effects
	local grow = TweenInfo.new(Look.PulseTime, Enum.EasingStyle.Quad, Enum.EasingDirection.Out)
	TweenService:Create(bubble, grow, { Size = Vector3.one * Look.PulseSize, Transparency = 1 }):Play()
	task.delay(Look.PulseTime, bubble.Destroy, bubble)
end

-- The player's dart saw these: each is outlined, through walls, for `seconds`.
local function reveal(seen: { Model }, seconds: number)
	local ends = os.clock() + seconds
	for _, character in seen do
		if typeof(character) ~= "Instance" or not character:IsDescendantOf(workspace) then
			continue -- gone since the server looked
		end
		local mark = outlined[character]
		if not mark then
			local highlight = Instance.new("Highlight")
			highlight.Adornee = character
			highlight.DepthMode = Enum.HighlightDepthMode.AlwaysOnTop
			highlight.FillColor = Look.Enemy
			highlight.OutlineColor = Look.Enemy
			highlight.Parent = hands.effects
			mark = { highlight = highlight, ends = ends }
			outlined[character] = mark
		end
		mark.ends = math.max(mark.ends, ends)
	end
	if #seen > 0 then
		hands.hud:notice(`{#seen} REVEALED`, HudConfig.Accent)
	end
end

-- Outlines fade at their end, and go with whoever wore them.
local function fade()
	local now = os.clock()
	for character, mark in outlined do
		local remaining = mark.ends - now
		if remaining <= 0 or not character:IsDescendantOf(workspace) then
			mark.highlight:Destroy()
			outlined[character] = nil
		else
			local gone = 1 - math.clamp(remaining / Look.Fade, 0, 1)
			mark.highlight.OutlineTransparency = gone
			mark.highlight.FillTransparency = Look.Fill + (1 - Look.Fill) * gone
		end
	end
end

function UtilityClient.start(lent: Hands)
	hands = lent
	for _, name in Config.Loadout do
		local what = (Config.Utilities :: any)[name]
		left[name] = 0
		show(name)
		ContextActionService:BindAction("Utility_" .. name, function(_, state)
			if state == Enum.UserInputState.Begin then
				UtilityClient.use(name)
			end
			return Enum.ContextActionResult.Sink
		end, false, what.Key)
	end

	remote("UtilityState").OnClientEvent:Connect(function(name: string, now: number)
		left[name] = now
		show(name)
	end)
	remote("UtilityThrown").OnClientEvent:Connect(fly)
	remote("UtilityPulse").OnClientEvent:Connect(pulse)
	remote("Reveal").OnClientEvent:Connect(reveal)
	remote("Spotted").OnClientEvent:Connect(function()
		hands.hud:notice("SPOTTED", HudConfig.Harm)
	end)
	RunService.RenderStepped:Connect(fade)
end

return UtilityClient

--!strict
-- First-person weapon: shows it in front of the camera, reads the trigger, tells the server about each shot
-- and plays the shot locally (kick, bolt, tracer). The server decides what a shot hits and breaks.
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage:WaitForChild("DesertFps")
local WeaponConfig = require(Shared:WaitForChild("Weapons"):WaitForChild("WeaponConfig"))
local fireRemote = Shared:WaitForChild("Remotes"):WaitForChild("FireWeapon") :: RemoteEvent

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera
local weaponName = WeaponConfig.Default
local weapon = (WeaponConfig :: any)[weaponName]

-- Weapons are modelled pointing along +X; the camera looks along -Z.
local AIM = CFrame.Angles(0, math.pi / 2, 0)

player.CameraMode = Enum.CameraMode.LockFirstPerson

local effects = Instance.new("Folder")
effects.Name = "WeaponEffects"
effects.Parent = camera

local model = Shared:WaitForChild("WeaponModels"):WaitForChild(weaponName):Clone() :: Model
local muzzle = model:GetAttribute("Socket_muzzle") :: Vector3
-- Every part with where it sits from the weapon origin, and how far its joint slides when the weapon cycles.
local parts: { { part: BasePart, offset: Vector3, slide: Vector3 } } = {}
for _, part in model:GetChildren() do
	if part:IsA("BasePart") then
		table.insert(parts, {
			part = part,
			offset = part:GetAttribute("Offset") :: Vector3,
			slide = (part:GetAttribute("Slide") :: Vector3?) or Vector3.zero,
		})
	end
end
model.Parent = effects

local crosshair = Instance.new("ScreenGui")
crosshair.Name = "Crosshair"
crosshair.IgnoreGuiInset = true
crosshair.ResetOnSpawn = false
local dot = Instance.new("Frame")
dot.AnchorPoint = Vector2.new(0.5, 0.5)
dot.Position = UDim2.fromScale(0.5, 0.5)
dot.Size = UDim2.fromOffset(4, 4)
dot.BackgroundColor3 = Color3.new(1, 1, 1)
dot.BorderSizePixel = 0
local outline = Instance.new("UIStroke")
outline.Color = Color3.new(0, 0, 0)
outline.Transparency = 0.4
outline.Parent = dot
dot.Parent = crosshair
crosshair.Parent = player:WaitForChild("PlayerGui")

local triggerHeld = false
local lastShot = 0
local kick = 0 -- 1 right after a shot, settling back to 0

local function alive(): boolean
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	return humanoid ~= nil and humanoid.Health > 0
end

-- Where the weapon origin is this frame.
local function weaponFrame(): CFrame
	return camera.CFrame
		* CFrame.new(weapon.ViewOffset + Vector3.new(0, 0, weapon.KickBack * kick))
		* CFrame.Angles(math.rad(weapon.KickPitch * kick), 0, 0)
		* AIM
end

local function tracer(from: Vector3, to: Vector3)
	local line = Instance.new("Part")
	line.Anchored = true
	line.CanCollide = false
	line.CanQuery = false
	line.CanTouch = false
	line.CastShadow = false
	line.Material = Enum.Material.Neon
	line.Color = weapon.TracerColor
	line.Size = Vector3.new(weapon.TracerWidth, weapon.TracerWidth, (to - from).Magnitude)
	line.CFrame = CFrame.lookAt((from + to) / 2, to)
	line.Parent = effects
	task.delay(weapon.TracerTime, line.Destroy, line)
end

local function shoot()
	local origin, direction = camera.CFrame.Position, camera.CFrame.LookVector
	fireRemote:FireServer(origin, direction)

	-- Guess the hit locally for the tracer; the server's own ray is the one that counts.
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { player.Character :: Instance, effects }
	local hit = workspace:Raycast(origin, direction * weapon.Range, params)
	tracer(weaponFrame() * muzzle, if hit then hit.Position else origin + direction * weapon.Range)
	kick = 1
end

ContextActionService:BindAction("FireWeapon", function(_, state)
	triggerHeld = state == Enum.UserInputState.Begin
	return Enum.ContextActionResult.Sink
end, true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)

RunService:BindToRenderStep("DesertFpsWeapon", Enum.RenderPriority.Camera.Value + 1, function(dt: number)
	local now = os.clock()
	if triggerHeld and alive() and now - lastShot >= weapon.FireInterval then
		lastShot = now
		shoot()
	end
	kick *= math.exp(-weapon.Recover * dt)

	local frame = weaponFrame()
	for _, entry in parts do
		entry.part.CFrame = frame * CFrame.new(entry.offset + entry.slide * kick)
	end
end)

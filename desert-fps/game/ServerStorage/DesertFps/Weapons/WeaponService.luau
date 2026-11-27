--!strict
-- Server side of the weapons. Every player carries WeaponConfig.Default (no loadouts yet).
-- The client only says where it fired from and in which direction. The server checks that claim against the
-- fire rate and the shooter's position, then does the hit itself.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("DesertFps")
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local DesertFps = (ServerStorage :: any).DesertFps
local Breakable = require(DesertFps.Destruction.Breakable)
local Structure = require(DesertFps.Destruction.Structure)
local PartsData = require(DesertFps.Assets.PartsData)

local WeaponService = {}

type Gunner = { shots: number, at: number }
local gunners: { [Player]: Gunner } = {}

local function vector(values: { number }): Vector3
	return Vector3.new(values[1], values[2], values[3])
end

local function isFinite(v: Vector3): boolean
	return v.X == v.X and v.Y == v.Y and v.Z == v.Z and v.Magnitude < 1e6
end

-- The model clients show in first person: every part of the weapon, with what the client needs to pose it
-- copied out of the parts data (which never leaves the server).
local function buildModel(name: string, parent: Instance)
	local data = PartsData[name]
	local model = Instance.new("Model")
	model.Name = name
	for _, socket in data.sockets do
		model:SetAttribute("Socket_" .. socket.name, vector(socket.position))
	end
	for _, template in DesertFps.Meshes[name].Parts:GetChildren() do
		local part = template:Clone() :: BasePart
		part.Anchored = true
		part.CanCollide = false
		part.CanQuery = false
		part.CanTouch = false
		part.CastShadow = false
		part.Parent = model
	end
	for _, joint in data.joints do
		local part = model:FindFirstChild(joint.part)
		if part and joint.type == "slide" then
			part:SetAttribute("Slide", vector(joint.axis) * joint.amount)
		end
	end
	model.Parent = parent
end

-- Whether the player may fire now. Shots refill at the weapon's fire rate, up to BurstAllowance at once.
local function takeShot(player: Player, interval: number): boolean
	local now = os.clock()
	local gunner = gunners[player]
	if not gunner then
		gunner = { shots = WeaponConfig.BurstAllowance, at = now }
		gunners[player] = gunner
	end
	gunner.shots = math.min(WeaponConfig.BurstAllowance, gunner.shots + (now - gunner.at) / interval)
	gunner.at = now
	if gunner.shots < 1 then
		return false
	end
	gunner.shots -= 1
	return true
end

local function onFire(player: Player, origin: unknown, direction: unknown)
	if typeof(origin) ~= "Vector3" or typeof(direction) ~= "Vector3" then
		return
	end
	if not isFinite(origin) or not isFinite(direction) or math.abs(direction.Magnitude - 1) > 0.01 then
		return
	end
	local weapon = (WeaponConfig :: any)[WeaponConfig.Default]
	if not takeShot(player, weapon.FireInterval) then
		return
	end

	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local head = character and character:FindFirstChild("Head")
	if not (character and humanoid and humanoid.Health > 0 and head and head:IsA("BasePart")) then
		return
	end
	if (origin - head.Position).Magnitude > WeaponConfig.MaxOriginOffset then
		return
	end

	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { character }
	-- The muzzle may not be on the far side of something from the shooter's head.
	if workspace:Raycast(head.Position, origin - head.Position, params) then
		return
	end

	local hit = workspace:Raycast(origin, direction.Unit * weapon.Range, params)
	if hit and hit.Instance:IsA("BasePart") then
		if not Breakable.damage(hit.Instance, weapon.Damage, hit.Position, direction.Unit) then
			Structure.knock(hit.Instance) -- a lantern, a sign, a banner: shot down
		end
		-- TODO: damage to players, once teams and rounds exist.
	end
	-- TODO: show the shot (tracer, weapon in hand) to the other players.
end

function WeaponService.start()
	local models = Instance.new("Folder")
	models.Name = "WeaponModels"
	buildModel(WeaponConfig.Default, models)
	models.Parent = Shared

	local remotes = Instance.new("Folder")
	remotes.Name = "Remotes"
	local fire = Instance.new("RemoteEvent")
	fire.Name = "FireWeapon"
	fire.Parent = remotes
	remotes.Parent = Shared

	fire.OnServerEvent:Connect(onFire)
	Players.PlayerRemoving:Connect(function(player)
		gunners[player] = nil
	end)
end

return WeaponService

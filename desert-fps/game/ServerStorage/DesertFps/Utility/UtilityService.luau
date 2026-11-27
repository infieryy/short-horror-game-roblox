--!strict
-- Server side of the utility: who has how many charges, where a thrown dart goes, and what it sees.
-- A client says "I throw this, from here, that way". The server checks the claim (alive, a charge left, the
-- throw starts at the thrower's head) and decides the rest itself: the flight, where the dart sticks, each
-- pulse and who it shows. Only the thrower is told who was seen.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("DesertFps")
local Config = require(Shared.Utility.UtilityConfig)
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local DesertFps = (ServerStorage :: any).DesertFps
local Combat = require(DesertFps.Combat.Combat)
local KitModels = require(DesertFps.Assets.KitModels)
local WeaponService = require(DesertFps.Weapons.WeaponService)

local UtilityService = {}

-- The flight is worked out in steps this long.
local STEP = 1 / 60
-- A piece is modelled pointing along +X; this turns a frame that looks along a direction into the piece's.
local AIM = CFrame.Angles(0, math.pi / 2, 0)
-- Where a dart looks for someone: any of these in the clear and they are seen.
local SEEN_AT = { "Head", "UpperTorso", "HumanoidRootPart" }

-- Charges left, and how many more are on their way back.
type Carried = { left: number, coming: number }
type Device = { owner: Player, model: Model, stuckTo: BasePart, eye: Vector3, out: boolean }

local carried: { [Player]: { [string]: Carried } } = {}
local lastAsk: { [Player]: number } = {}
local devices: { [BasePart]: Device } = {}
local remotes: { [string]: RemoteEvent } = {}
local models: Folder -- what clients show in flight: one model for each utility's piece
local placed: Folder -- the darts that are stuck in the town

local function isFinite(v: Vector3): boolean
	return v.X == v.X and v.Y == v.Y and v.Z == v.Z and v.Magnitude < 1e6
end

local function tell(player: Player, name: string)
	local mine = carried[player] and carried[player][name]
	if mine then
		remotes.UtilityState:FireClient(player, name, mine.left)
	end
end

-- What a dart flies through and sees past: bodies, and other darts.
local function world(): RaycastParams
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	local ignore: { Instance } = Combat.all()
	table.insert(ignore, placed)
	params.FilterDescendantsInstances = ignore
	return params
end

-- Where something thrown from `origin` at `velocity` first meets the world: after how long, what it met and
-- where, and which way it was going. Nil if it meets nothing in time.
local function flight(origin: Vector3, velocity: Vector3, gravity: number, most: number): (number?, RaycastResult?, Vector3?)
	local params = world()
	local position, elapsed = origin, 0
	while elapsed < most do
		local after = velocity - Vector3.new(0, gravity * STEP, 0)
		local move = (velocity + after) / 2 * STEP
		local hit = workspace:Raycast(position, move, params)
		if hit then
			return elapsed + STEP * hit.Distance / move.Magnitude, hit, velocity.Unit
		end
		position, velocity, elapsed = position + move, after, elapsed + STEP
	end
	return nil, nil, nil
end

local function remove(device: Device)
	if device.out then
		return
	end
	device.out = true
	for part, other in devices do
		if other == device then
			devices[part] = nil
		end
	end
	device.model:Destroy()
end

-- One pulse: everyone else the dart has a clear line to, within its reach.
local function pulse(device: Device, what: any)
	local params = world()
	local seen: { Model } = {}
	local theirs = device.owner.Character
	for _, character in Combat.all() do
		if character == theirs or not character:IsA("Model") then
			continue
		end
		for _, name in SEEN_AT do
			local part = character:FindFirstChild(name)
			if part and part:IsA("BasePart") then
				local to = part.Position - device.eye
				if to.Magnitude <= what.Radius and not workspace:Raycast(device.eye, to, params) then
					table.insert(seen, character)
					break
				end
			end
		end
	end
	remotes.UtilityPulse:FireAllClients(device.eye)
	if device.owner.Parent then
		remotes.Reveal:FireClient(device.owner, seen, what.Reveal)
	end
	for _, character in seen do
		local spotted = Players:GetPlayerFromCharacter(character)
		if spotted then
			remotes.Spotted:FireClient(spotted)
		end
	end
end

-- Stands the dart where it landed: its tip in the surface, leaning the way it came in.
local function stick(owner: Player, name: string, hit: RaycastResult, heading: Vector3)
	local what = (Config.Utilities :: any)[name]
	local source = models:FindFirstChild(what.Model) :: Instance
	local into = (heading - hit.Normal * 0.6).Unit
	local frame = CFrame.lookAlong(hit.Position, into) * AIM
	local model = Instance.new("Model")
	model.Name = name
	local device: Device = {
		owner = owner,
		model = model,
		stuckTo = hit.Instance,
		eye = frame * ((source:GetAttribute("Socket_eye") :: Vector3) * what.Size) + hit.Normal * 0.05,
		out = false,
	}
	for _, template in source:GetChildren() do
		if template:IsA("BasePart") then
			local part = template:Clone()
			part.Size *= what.Size
			part.CFrame = frame * CFrame.new((template:GetAttribute("Offset") :: Vector3) * what.Size)
			part.CanQuery = true -- so that it can be shot down
			part.CastShadow = true
			part.Parent = model
			devices[part] = device
			model.PrimaryPart = model.PrimaryPart or part
		end
	end
	-- Its light shows where it is, to friend and enemy alike.
	local lamp = Instance.new("Attachment")
	lamp.Parent = model.PrimaryPart
	lamp.WorldPosition = device.eye
	local light = Instance.new("PointLight")
	light.Color = Config.Look.Light
	light.Range = Config.Look.LightRange
	light.Brightness = 2
	light.Shadows = false
	light.Parent = lamp
	model.Parent = placed

	task.delay(what.Arm, function()
		for _ = 1, what.Pulses do
			-- A dart whose wall has come down goes with it.
			if device.out or not device.stuckTo:IsDescendantOf(workspace) then
				break
			end
			pulse(device, what)
			task.wait(what.Every)
		end
		task.wait(what.Linger)
		remove(device)
	end)
end

local function onUse(player: Player, name: unknown, origin: unknown, direction: unknown)
	if typeof(name) ~= "string" or typeof(origin) ~= "Vector3" or typeof(direction) ~= "Vector3" then
		return
	end
	if not isFinite(origin) or not isFinite(direction) or math.abs(direction.Magnitude - 1) > 0.01 then
		return
	end
	local what = (Config.Utilities :: any)[name]
	local mine = carried[player] and carried[player][name]
	local now = os.clock()
	if not (what and mine) or now - (lastAsk[player] or 0) < WeaponConfig.AskInterval then
		return
	end
	lastAsk[player] = now

	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local head = character and character:FindFirstChild("Head")
	if not (character and humanoid and humanoid.Health > 0 and head and head:IsA("BasePart")) then
		return
	end
	if mine.left < 1 then
		tell(player, name) -- the client thinks it has one left
		return
	end
	-- As for a shot: it starts at the thrower's head, and not on the far side of something from it.
	if (origin - head.Position).Magnitude > WeaponConfig.MaxOriginOffset then
		return
	end
	if workspace:Raycast(head.Position, origin - head.Position, world()) then
		return
	end
	-- Hands that throw do not shoot: the weapon is drawn again.
	if not WeaponService.lower(player, 0) then
		return
	end

	mine.left -= 1
	mine.coming += 1
	tell(player, name)
	task.delay(what.Recharge, function()
		if carried[player] and carried[player][name] == mine and mine.coming > 0 then
			mine.coming -= 1
			mine.left = math.min(what.Charges, mine.left + 1)
			tell(player, name)
		end
	end)

	local velocity = direction.Unit * what.Speed
	local after, hit, heading = flight(origin, velocity, what.Gravity, what.FlightMost)
	-- Everyone sees it fly. Each client draws the flight itself from where it starts and how fast.
	remotes.UtilityThrown:FireAllClients(name, origin, velocity, after or what.FlightMost)
	if after and hit and heading then
		task.delay(after, function()
			if hit.Instance:IsDescendantOf(workspace) then
				stick(player, name, hit, heading)
			end
		end)
	end
end

-- A full set of charges, at every spawn.
local function stock(player: Player)
	local mine = {}
	for _, name in Config.Loadout do
		mine[name] = { left = (Config.Utilities :: any)[name].Charges, coming = 0 }
	end
	carried[player] = mine
	for _, name in Config.Loadout do
		tell(player, name)
	end
end

function UtilityService.start()
	models = Instance.new("Folder")
	models.Name = "UtilityModels"
	for _, what in Config.Utilities :: { [string]: any } do
		KitModels.view(what.Model, models)
	end
	models.Parent = Shared

	placed = Instance.new("Folder")
	placed.Name = "Utilities"
	placed.Parent = workspace

	-- From a client: UseUtility. To clients: UtilityState (their charges), UtilityThrown and UtilityPulse
	-- (for everyone to see), Reveal (who the thrower's dart saw), Spotted (to whoever was seen).
	local folder = Shared:WaitForChild("Remotes")
	for _, name in { "UseUtility", "UtilityState", "UtilityThrown", "UtilityPulse", "Reveal", "Spotted" } do
		local remote = Instance.new("RemoteEvent")
		remote.Name = name
		remote.Parent = folder
		remotes[name] = remote
	end
	remotes.UseUtility.OnServerEvent:Connect(onUse)

	-- A shot or a slash that lands on a dart knocks it out.
	table.insert(WeaponService.Struck, function(part: BasePart): boolean
		local device = devices[part]
		if device then
			remove(device)
		end
		return device ~= nil
	end)

	local function onPlayer(player: Player)
		player.CharacterAdded:Connect(function()
			stock(player)
		end)
		if player.Character then
			stock(player)
		end
	end
	Players.PlayerAdded:Connect(onPlayer)
	for _, player in Players:GetPlayers() do
		onPlayer(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		carried[player] = nil
		lastAsk[player] = nil
	end)
end

return UtilityService

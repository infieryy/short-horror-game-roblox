--!strict
-- Server side of the weapons: what each player carries, and what their shots do.
-- A client says what it does (fire, reload, switch weapon, walk, aim) and where a shot went. The server checks
-- each claim against what the player holds, the fire rate, the ammunition and where the shooter stands, and
-- decides the hit itself: on a character through Hitboxes, on the town through Breakable.

local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("DesertFps")
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local Ballistics = require(Shared.Weapons.Ballistics)
local CombatConfig = require(Shared.Combat.CombatConfig)
local DesertFps = (ServerStorage :: any).DesertFps
local Breakable = require(DesertFps.Destruction.Breakable)
local Structure = require(DesertFps.Destruction.Structure)
local PartsData = require(DesertFps.Assets.PartsData)
local Combat = require(DesertFps.Combat.Combat)
local Hitboxes = require(DesertFps.Combat.Hitboxes)

local WeaponService = {}

-- Weapons are modelled pointing along +X; a hand holds a tool pointing along -Z.
local AIM = CFrame.Angles(0, math.pi / 2, 0)

type Slot = { weapon: string, magazine: number, reserve: number }
type Rate = { left: number, at: number }
type Gunner = {
	slots: { [string]: Slot },
	current: string,
	readyAt: number, -- when the weapon in hand can be used (os.clock)
	reloadEnds: number?,
	reloads: number, -- a reload only finishes if this has not moved on since it began
	walking: boolean,
	aiming: boolean,
	rates: { [string]: Rate },
}
local gunners: { [Player]: Gunner } = {}

local remotes: { [string]: RemoteEvent } = {}

local function vector(values: { number }): Vector3
	return Vector3.new(values[1], values[2], values[3])
end

local function isFinite(v: Vector3): boolean
	return v.X == v.X and v.Y == v.Y and v.Z == v.Z and v.Magnitude < 1e6
end

local function unseen(part: BasePart)
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
end

-- The model clients show in first person: every part of the weapon, with what the client needs to pose it
-- copied out of the parts data (which never leaves the server).
local function viewModel(name: string, parent: Instance)
	local data = PartsData[name]
	local model = Instance.new("Model")
	model.Name = name
	for _, socket in data.sockets do
		model:SetAttribute("Socket_" .. socket.name, vector(socket.position))
	end
	for _, template in DesertFps.Meshes[name].Parts:GetChildren() do
		local part = template:Clone() :: BasePart
		part.Anchored = true
		part.CastShadow = false
		unseen(part)
		part.Parent = model
	end
	for _, joint in data.joints do
		local part = model:FindFirstChild(joint.part)
		if part and joint.type == "slide" then
			part:SetAttribute("Slide", vector(joint.axis) * joint.amount)
		elseif part and joint.type == "detach" then
			part:SetAttribute("Detach", vector(joint.axis).Unit)
		end
	end
	model.Parent = parent
end

-- The weapon everyone else sees in the player's hand: a Tool, so the character holds it out by itself.
local function handModel(name: string): Tool
	local tool = Instance.new("Tool")
	tool.Name = name
	tool.CanBeDropped = false
	tool.ManualActivationOnly = true
	tool.Grip = (WeaponConfig.Weapons :: any)[name].Hand
	local handle = Instance.new("Part")
	handle.Name = "Handle"
	handle.Size = Vector3.one * 0.2
	handle.Transparency = 1
	handle.Massless = true
	unseen(handle)
	handle.Parent = tool
	for _, template in DesertFps.Meshes[name].Parts:GetChildren() do
		local part = template:Clone() :: BasePart
		part.Anchored = false
		part.Massless = true
		unseen(part)
		local weld = Instance.new("Weld")
		weld.Part0 = handle
		weld.Part1 = part
		weld.C0 = AIM * CFrame.new(part:GetAttribute("Offset") :: Vector3)
		weld.Parent = part
		part.Parent = tool
	end
	return tool
end

local function weaponOf(gunner: Gunner): (any, Slot)
	local slot = gunner.slots[gunner.current]
	return (WeaponConfig.Weapons :: any)[slot.weapon], slot
end

local function humanoidOf(player: Player): (Model?, Humanoid?)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if character and humanoid and humanoid.Health > 0 then
		return character, humanoid
	end
	return nil, nil
end

-- Whether a request of this kind is within its rate: one every `interval` seconds, `burst` at once.
local function within(gunner: Gunner, kind: string, interval: number, burst: number): boolean
	local now = os.clock()
	local rate = gunner.rates[kind]
	if not rate then
		rate = { left = burst, at = now }
		gunner.rates[kind] = rate
	end
	rate.left = math.min(burst, rate.left + (now - rate.at) / interval)
	rate.at = now
	if rate.left < 1 then
		return false
	end
	rate.left -= 1
	return true
end

local function asks(gunner: Gunner, kind: string): boolean
	return within(gunner, kind, WeaponConfig.AskInterval, WeaponConfig.AskBurst)
end

-- Tells the player what they carry. Only they are told: nobody else learns how many rounds they have left.
local function tell(player: Player, gunner: Gunner)
	remotes.State:FireClient(player, { current = gunner.current, slots = gunner.slots })
end

local function pace(gunner: Gunner, humanoid: Humanoid)
	humanoid.WalkSpeed = Ballistics.pace(weaponOf(gunner), gunner.walking, gunner.aiming)
end

-- Puts the weapon of the current slot in the player's hand.
local function hold(player: Player, gunner: Gunner)
	local character, humanoid = humanoidOf(player)
	if not (character and humanoid) then
		return
	end
	for _, child in character:GetChildren() do
		if child:IsA("Tool") then
			child:Destroy()
		end
	end
	local weapon, slot = weaponOf(gunner)
	handModel(slot.weapon).Parent = character
	gunner.readyAt = os.clock() + weapon.EquipTime - WeaponConfig.Grace
	pace(gunner, humanoid)
end

local function interruptReload(gunner: Gunner)
	gunner.reloads += 1
	gunner.reloadEnds = nil
end

local function arm(player: Player, character: Model)
	local loadout = WeaponConfig.Loadout :: any
	local slots = {}
	for _, name in WeaponConfig.Slots do
		local weapon = (WeaponConfig.Weapons :: any)[loadout[name]]
		slots[name] = { weapon = loadout[name], magazine = weapon.Magazine or 0, reserve = weapon.Reserve or 0 }
	end
	local gunner: Gunner = {
		slots = slots,
		current = WeaponConfig.Slots[1],
		readyAt = 0,
		reloads = 0,
		walking = false,
		aiming = false,
		rates = {},
	}
	gunners[player] = gunner
	Combat.enlist(character, loadout.armor)
	hold(player, gunner)
	tell(player, gunner)
end

-- Whether a knife coming along `direction` comes from behind the victim.
local function fromBehind(victim: Model, direction: Vector3): boolean
	local root = victim:FindFirstChild("HumanoidRootPart")
	return root ~= nil and root:IsA("BasePart") and root.CFrame.LookVector:Dot(direction) > 0.5
end

local function onFire(player: Player, origin: unknown, direction: unknown, target: unknown, claimed: unknown)
	if typeof(origin) ~= "Vector3" or typeof(direction) ~= "Vector3" then
		return
	end
	if not isFinite(origin) or not isFinite(direction) or math.abs(direction.Magnitude - 1) > 0.01 then
		return
	end
	local gunner = gunners[player]
	local character = humanoidOf(player)
	local head = character and character:FindFirstChild("Head")
	if not (gunner and character and head and head:IsA("BasePart")) then
		return
	end

	local weapon, slot = weaponOf(gunner)
	local gun = weapon.Kind == "gun"
	local now = os.clock()
	if now < gunner.readyAt or gunner.reloadEnds then
		return
	end
	if gun and slot.magazine < 1 then
		tell(player, gunner) -- the client thinks it has rounds left
		return
	end
	if not within(gunner, "fire", weapon.FireInterval, WeaponConfig.BurstAllowance) then
		return
	end
	if (origin - head.Position).Magnitude > WeaponConfig.MaxOriginOffset then
		return
	end
	local world = RaycastParams.new()
	world.FilterType = Enum.RaycastFilterType.Exclude
	world.FilterDescendantsInstances = Combat.all()
	-- The shot may not start on the far side of something from the shooter's head.
	if workspace:Raycast(head.Position, origin - head.Position, world) then
		return
	end

	direction = direction.Unit
	if gun then
		slot.magazine -= 1
	end
	local wall = workspace:Raycast(origin, direction * weapon.Range, world)
	local reach = if wall then wall.Distance else weapon.Range
	local finish = origin + direction * reach

	local part: string?, distance: number?
	if typeof(target) == "Instance" and target ~= character and Combat.is(target) then
		part, distance = Hitboxes.cast(
			target :: Model,
			origin,
			direction,
			reach,
			now - CombatConfig.Rewind.Reach,
			if typeof(claimed) == "string" then claimed else nil,
			if gun then nil else CombatConfig.MeleeMargin
		)
	end
	if part and distance then
		local victim = target :: Model
		local zone = (CombatConfig.Zones :: any)[part]
		local amount = if gun
			then Ballistics.damage(weapon, zone, distance)
			elseif fromBehind(victim, direction) then weapon.BackDamage
			else weapon.Damage
		local dealt, killed = Combat.damage(victim, amount, { attacker = player, weapon = slot.weapon, zone = zone, from = origin })
		finish = origin + direction * distance
		remotes.Hit:FireClient(player, zone, dealt, killed)
	elseif wall and wall.Instance:IsA("BasePart") then
		if not Breakable.damage(wall.Instance, weapon.WallDamage, wall.Position, direction) then
			Structure.knock(wall.Instance) -- a lantern, a sign, a banner: shot down
		end
	end
	-- Everyone else sees the shot.
	for _, other in Players:GetPlayers() do
		if other ~= player then
			remotes.Shot:FireClient(other, player, slot.weapon, origin, finish)
		end
	end
end

local function onReload(player: Player)
	local gunner = gunners[player]
	if not (gunner and humanoidOf(player) and asks(gunner, "reload")) then
		return
	end
	local weapon, slot = weaponOf(gunner)
	if weapon.Kind ~= "gun" or gunner.reloadEnds or os.clock() < gunner.readyAt then
		return
	end
	if slot.magazine >= weapon.Magazine or slot.reserve < 1 then
		return
	end
	gunner.reloads += 1
	local mine = gunner.reloads
	local seconds = weapon.ReloadTime - WeaponConfig.Grace
	gunner.reloadEnds = os.clock() + seconds
	task.delay(seconds, function()
		if gunners[player] ~= gunner or gunner.reloads ~= mine then
			return -- died, or switched weapon meanwhile
		end
		local rounds = math.min(weapon.Magazine - slot.magazine, slot.reserve)
		slot.magazine += rounds
		slot.reserve -= rounds
		gunner.reloadEnds = nil
		tell(player, gunner)
	end)
end

local function onEquip(player: Player, slotName: unknown)
	local gunner = gunners[player]
	if typeof(slotName) ~= "string" or not (gunner and humanoidOf(player) and asks(gunner, "equip")) then
		return
	end
	if not gunner.slots[slotName] or slotName == gunner.current then
		return
	end
	gunner.current = slotName
	gunner.aiming = false
	interruptReload(gunner)
	hold(player, gunner)
	tell(player, gunner)
end

local function onStance(player: Player, walking: unknown, aiming: unknown)
	local gunner = gunners[player]
	local _, humanoid = humanoidOf(player)
	if typeof(walking) ~= "boolean" or typeof(aiming) ~= "boolean" then
		return
	end
	if not (gunner and humanoid and asks(gunner, "stance")) then
		return
	end
	gunner.walking, gunner.aiming = walking, aiming
	pace(gunner, humanoid)
end

local function onPlayer(player: Player)
	player.CharacterAdded:Connect(function(character)
		-- The body is not all there the moment the character is.
		character:WaitForChild("Humanoid")
		character:WaitForChild("Head")
		arm(player, character)
	end)
	if player.Character then
		arm(player, player.Character)
	end
end

function WeaponService.start()
	local models = Instance.new("Folder")
	models.Name = "WeaponModels"
	for name in WeaponConfig.Weapons do
		viewModel(name, models)
	end
	models.Parent = Shared

	local folder = Instance.new("Folder")
	folder.Name = "Remotes"
	-- From a client: FireWeapon, Reload, Equip, Stance. To clients: State, Hit, Hurt, Shot, Killed.
	for _, name in { "FireWeapon", "Reload", "Equip", "Stance", "State", "Hit", "Hurt", "Shot", "Killed" } do
		local remote = Instance.new("RemoteEvent")
		remote.Name = name
		remote.Parent = folder
		remotes[name] = remote
	end
	folder.Parent = Shared

	remotes.FireWeapon.OnServerEvent:Connect(onFire)
	remotes.Reload.OnServerEvent:Connect(onReload)
	remotes.Equip.OnServerEvent:Connect(onEquip)
	remotes.Stance.OnServerEvent:Connect(onStance)

	table.insert(Combat.Hurt, function(victim, amount, hit)
		local hurt = Players:GetPlayerFromCharacter(victim)
		if hurt then
			remotes.Hurt:FireClient(hurt, hit.from, amount)
		end
	end)
	table.insert(Combat.Died, function(victim, hit)
		local dead = Players:GetPlayerFromCharacter(victim)
		local humanoid = victim:FindFirstChildOfClass("Humanoid")
		remotes.Killed:FireAllClients(
			if hit.attacker then hit.attacker.DisplayName else "",
			if dead then dead.DisplayName elseif humanoid then humanoid.DisplayName else victim.Name,
			(WeaponConfig.Weapons :: any)[hit.weapon].Title,
			hit.zone == "head"
		)
	end)

	Players.PlayerAdded:Connect(onPlayer)
	for _, player in Players:GetPlayers() do
		onPlayer(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		gunners[player] = nil
	end)
end

return WeaponService

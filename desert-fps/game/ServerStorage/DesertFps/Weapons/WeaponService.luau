--!strict
-- Server side of the weapons: what each player carries, and what their shots do.
-- A client says what it does (fire, reload, switch weapon, walk, aim, fit an attachment) and where a shot
-- went. The server checks each claim against what the player holds, the fire rate, the ammunition and where
-- the shooter stands, and decides the hit itself: on a character through Hitboxes, on the town through
-- Breakable. A weapon's numbers are the ones it has with its attachments on (Attachments.build).

local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local ServerStorage = game:GetService("ServerStorage")

local Shared = ReplicatedStorage:WaitForChild("DesertFps")
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local Ballistics = require(Shared.Weapons.Ballistics)
local Penetration = require(Shared.Weapons.Penetration)
local AttachmentConfig = require(Shared.Weapons.AttachmentConfig)
local Attachments = require(Shared.Weapons.Attachments)
local CombatConfig = require(Shared.Combat.CombatConfig)
local SoundConfig = require(Shared.Sound.SoundConfig)
local DesertFps = (ServerStorage :: any).DesertFps
local Breakable = require(DesertFps.Destruction.Breakable)
local Structure = require(DesertFps.Destruction.Structure)
local KitModels = require(DesertFps.Assets.KitModels)
local Combat = require(DesertFps.Combat.Combat)
local Hitboxes = require(DesertFps.Combat.Hitboxes)

local WeaponService = {}

-- Called when a shot or a slash lands on something in the world that is not a body, before the town is asked:
-- the first to answer true has taken the hit (the recon dart, which is knocked out).
WeaponService.Struck = {} :: { (part: BasePart, by: Player) -> boolean }

-- Weapons are modelled pointing along +X; a hand holds a tool pointing along -Z.
local AIM = CFrame.Angles(0, math.pi / 2, 0)

-- attachments: socket -> attachment name
type Slot = { weapon: string, magazine: number, reserve: number, attachments: Attachments.Chosen }
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
-- What each player has put on the weapon of each slot. It outlives the body: dying does not strip a weapon.
local fitted: { [Player]: { [string]: Attachments.Chosen } } = {}
-- The models clients show, which the hand models are made from too: the weapons', the attachments'.
local weaponModels: Folder, attachmentModels: Folder

local remotes: { [string]: RemoteEvent } = {}

local function isFinite(v: Vector3): boolean
	return v.X == v.X and v.Y == v.Y and v.Z == v.Z and v.Magnitude < 1e6
end

local function unseen(part: BasePart)
	part.CanCollide = false
	part.CanQuery = false
	part.CanTouch = false
end

-- The weapon everyone else sees in the player's hand, with what is attached to it: a Tool, so the character
-- holds it out by itself.
local function handModel(name: string, attached: Attachments.Chosen): Tool
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

	local source = weaponModels:FindFirstChild(name) :: Instance
	local fitting = Attachments.fitting(source, attachmentModels, attached)
	local function add(template: BasePart, at: Vector3, size: Vector3)
		local part = template:Clone()
		part.Size = size
		part.Anchored = false
		part.Massless = true
		part.CastShadow = true
		local weld = Instance.new("Weld")
		weld.Part0 = handle
		weld.Part1 = part
		weld.C0 = AIM * CFrame.new(at)
		weld.Parent = part
		part.Parent = tool
	end
	for _, template in source:GetChildren() do
		if template:IsA("BasePart") then
			local size, at = template.Size, template:GetAttribute("Offset") :: Vector3
			local stretch = fitting.stretch[template.Name]
			if stretch then
				size, at = Attachments.stretched(size, at, stretch)
			end
			add(template, at, size)
		end
	end
	for _, each in fitting.adds do
		add(each.template, each.at, each.size)
	end
	-- Where shots leave the weapon, looking along the barrel, for clients to draw the flash and the tracer
	-- from (Client/Effects).
	local muzzle = fitting.points.muzzle or source:GetAttribute("Socket_muzzle")
	if typeof(muzzle) == "Vector3" then
		local mark = Instance.new("Attachment")
		mark.Name = "Muzzle"
		mark.CFrame = AIM * CFrame.new(muzzle) * AIM:Inverse()
		mark.Parent = handle
	end
	-- Where a laser's beam leaves the weapon, looking along the barrel, for clients to draw it from
	-- (Client/LaserSight).
	if fitting.points.beam then
		local emitter = Instance.new("Attachment")
		emitter.Name = "Laser"
		emitter.Position = AIM * fitting.points.beam
		emitter.Parent = handle
	end
	return tool
end

-- The numbers of the weapon in hand, as it is fitted, and its slot.
local function weaponOf(gunner: Gunner): (any, Slot)
	local slot = gunner.slots[gunner.current]
	return Attachments.build(slot.weapon, slot.attachments), slot
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

-- Tells everyone near enough to hear it that `player` made a noise with the weapon in hand: "Quiet" (a shot
-- from a weapon that hides its shots), "Draw" or "Reload". `sound` is the sound it makes (SoundConfig), which
-- says how far it carries; nobody further off is told, so the noise gives nothing away to them.
local function heard(player: Player, weaponName: string, what: string, sound: string?, seconds: number?)
	local entry = if sound then (SoundConfig.Sounds :: any)[sound] else nil
	local root = player.Character and player.Character:FindFirstChild("HumanoidRootPart")
	if not (entry and root and root:IsA("BasePart")) then
		return
	end
	for _, other in Players:GetPlayers() do
		local theirs = other.Character and other.Character:FindFirstChild("HumanoidRootPart")
		if other ~= player and theirs and theirs:IsA("BasePart") and (theirs.Position - root.Position).Magnitude <= entry.Far then
			remotes.Heard:FireClient(other, player, weaponName, what, sound, seconds)
		end
	end
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
	handModel(slot.weapon, weapon.Attached).Parent = character
	gunner.readyAt = os.clock() + weapon.EquipTime - WeaponConfig.Grace
	pace(gunner, humanoid)
	heard(player, slot.weapon, "Draw", weapon.Sounds.Draw)
end

local function interruptReload(gunner: Gunner)
	gunner.reloads += 1
	gunner.reloadEnds = nil
end

local function arm(player: Player, character: Model)
	local loadout = WeaponConfig.Loadout :: any
	local kept = fitted[player] or {}
	fitted[player] = kept
	local slots = {}
	for _, name in WeaponConfig.Slots do
		kept[name] = kept[name] or {}
		local weapon = Attachments.build(loadout[name], kept[name])
		slots[name] = {
			weapon = loadout[name],
			magazine = weapon.Magazine or 0,
			reserve = weapon.Reserve or 0,
			attachments = kept[name],
		}
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
	-- The shot's way through the town: what it goes through, what stops it. Bodies are tested apart.
	local path = Penetration.trace(origin, direction, weapon.Range, weapon.Pierce or 0, world)
	local finish, ends = path.finish, path.reach

	local part: string?, distance: number?
	if typeof(target) == "Instance" and target ~= character and Combat.is(target) then
		part, distance = Hitboxes.cast(
			target :: Model,
			origin,
			direction,
			path.reach,
			now - CombatConfig.Rewind.Reach,
			if typeof(claimed) == "string" then claimed else nil,
			if gun then nil else CombatConfig.MeleeMargin
		)
	end
	if part and distance then
		local victim = target :: Model
		local zone = (CombatConfig.Zones :: any)[part]
		-- What the shot went through on its way has taken some of its force.
		local force = Penetration.left(path, distance)
		local amount = if gun
			then Ballistics.damage(weapon, zone, distance) * force
			elseif fromBehind(victim, direction) then weapon.BackDamage
			else weapon.Damage
		local dealt, killed = Combat.damage(
			victim,
			amount,
			{ attacker = player, weapon = slot.weapon, zone = zone, from = origin, through = force < 1 }
		)
		finish, ends = origin + direction * distance, distance
		remotes.Hit:FireClient(player, zone, dealt, killed, finish)
		-- Everyone else sees the hit burst where it landed, whatever the weapon hides.
		for _, other in Players:GetPlayers() do
			if other ~= player then
				remotes.Struck:FireClient(other, finish, zone)
			end
		end
	end
	-- Everything it went through before it ended is struck, and whatever stopped it, each with the force the
	-- shot still had there.
	local function strike(struck: Instance, force: number, at: Vector3)
		if not struck:IsA("BasePart") then
			return
		end
		for _, taker in WeaponService.Struck do
			if taker(struck, player) then
				return
			end
		end
		if not Breakable.damage(struck, weapon.WallDamage * force, at, direction) then
			Structure.knock(struck) -- a lantern, a sign, a banner: shot down
		end
	end
	for _, each in path.pierced do
		if each.enter < ends then
			strike(each.part, each.before, each.at)
		end
	end
	if path.stopped and path.reach <= ends then
		strike(path.stopped.Instance, path.force, path.stopped.Position)
	end
	-- Everyone else sees the shot, unless the weapon hides it, and what it left on the town, which nothing
	-- hides. (The shooter has drawn both already. What the shot broke is gone, and is not marked.)
	local marks = if gun then Penetration.marks(path, ends) else {}
	for _, other in Players:GetPlayers() do
		if other ~= player then
			if not weapon.Silent then
				remotes.Shot:FireClient(other, player, slot.weapon, origin, finish)
			end
			if #marks > 0 then
				remotes.Marks:FireClient(other, marks)
			end
		end
	end
	-- A shot that is hidden is still heard, near by.
	if weapon.Silent then
		heard(player, slot.weapon, "Quiet", weapon.Sounds.Fire)
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
	heard(player, slot.weapon, "Reload", weapon.Sounds.MagazineIn, weapon.ReloadTime)
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

-- Puts an attachment on a socket of the weapon in a slot, or with no name takes off what is there.
local function onAttach(player: Player, slotName: unknown, socket: unknown, name: unknown)
	local gunner = gunners[player]
	if typeof(slotName) ~= "string" or typeof(socket) ~= "string" or not (name == nil or typeof(name) == "string") then
		return
	end
	if not (gunner and humanoidOf(player) and asks(gunner, "attach")) then
		return
	end
	local slot = gunner.slots[slotName]
	if
		not slot
		or not table.find(AttachmentConfig.Sockets, socket)
		or slot.attachments[socket] == name
		or (name ~= nil and Attachments.fits(slot.weapon, name :: string) ~= socket)
	then
		tell(player, gunner) -- the client shows a fitting before it is answered: this puts it right
		return
	end
	slot.attachments[socket] = name :: any
	-- Rounds a smaller magazine cannot hold go back to the reserve.
	local weapon = Attachments.build(slot.weapon, slot.attachments)
	local over = slot.magazine - (weapon.Magazine or 0)
	if over > 0 then
		slot.magazine -= over
		slot.reserve += over
	end
	if slotName == gunner.current then
		-- The weapon in hand is drawn again: fitting something is not free in a fight.
		gunner.aiming = false
		interruptReload(gunner)
		hold(player, gunner)
	end
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

-- The body every client copies for the arms in front of its camera (Client/Viewmodel): a plain R15 one, so
-- the arms are the same size and shape for everyone and the animations fit. Each client gives its copy its own
-- skin and shirt.
local function viewArms(parent: Instance)
	-- A body makes its own torso and head solid whatever they are told, and these arms hang where the player's
	-- own body is: they would throw it across the town. So they are in a group that touches nothing.
	local group = WeaponConfig.ViewArms.Group
	PhysicsService:RegisterCollisionGroup(group)
	for _, other in PhysicsService:GetRegisteredCollisionGroups() do
		PhysicsService:CollisionGroupSetCollidable(group, other.name, false)
	end

	-- The body the animations were made on (the kit's R15, the classic block proportions). Left to itself a
	-- new body has arms a twentieth longer, and a hand that the animation put on the weapon then misses it
	-- by a sixth of a stud.
	local classic = Instance.new("HumanoidDescription")
	classic.BodyTypeScale = 0
	classic.ProportionScale = 0
	local arms = Players:CreateHumanoidModelFromDescription(classic, Enum.HumanoidRigType.R15)
	arms.Name = "ViewArms"
	for _, each in arms:GetDescendants() do
		if each:IsA("LuaSourceContainer") or each:IsA("Decal") then
			each:Destroy()
		elseif each:IsA("BasePart") then
			each.CollisionGroup = group
		end
	end
	arms.Parent = parent
end

-- The player's hands do something else for `seconds` (throw a dart): the weapon in hand cannot be used for
-- that long, and then has to be drawn again. A reload under way is lost. False if the player holds nothing.
function WeaponService.lower(player: Player, seconds: number): boolean
	local gunner = gunners[player]
	local _, humanoid = humanoidOf(player)
	if not (gunner and humanoid) then
		return false
	end
	gunner.aiming = false
	interruptReload(gunner)
	local drawn = os.clock() + seconds + weaponOf(gunner).EquipTime - WeaponConfig.Grace
	gunner.readyAt = math.max(gunner.readyAt, drawn)
	pace(gunner, humanoid)
	return true
end

function WeaponService.start()
	weaponModels = Instance.new("Folder")
	weaponModels.Name = "WeaponModels"
	for name in WeaponConfig.Weapons do
		KitModels.view(name, weaponModels)
	end
	weaponModels.Parent = Shared
	attachmentModels = Instance.new("Folder")
	attachmentModels.Name = "AttachmentModels"
	for _, what in AttachmentConfig.Attachments :: { [string]: any } do
		if what.Model then
			KitModels.view(what.Model, attachmentModels)
		end
	end
	attachmentModels.Parent = Shared
	task.spawn(viewArms, Shared)

	local folder = Instance.new("Folder")
	folder.Name = "Remotes"
	-- From a client: FireWeapon, Reload, Equip, Stance, Attach. To clients: State, Hit, Hurt, Shot, Marks, Heard, Struck, Killed.
	for _, name in { "FireWeapon", "Reload", "Equip", "Stance", "Attach", "State", "Hit", "Hurt", "Shot", "Marks", "Heard", "Struck", "Killed" } do
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
	remotes.Attach.OnServerEvent:Connect(onAttach)

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
			hit.zone == "head",
			hit.through == true
		)
	end)

	Players.PlayerAdded:Connect(onPlayer)
	for _, player in Players:GetPlayers() do
		onPlayer(player)
	end
	Players.PlayerRemoving:Connect(function(player)
		gunners[player] = nil
		fitted[player] = nil
	end)
end

return WeaponService

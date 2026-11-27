--!strict
-- The player's side of the weapons: reads the keys, plays the weapon in first person, and tells the server what
-- the player does. It works out where each shot goes (the aim, the recoil, how still the player stands) and
-- shows it at once; the server decides what the shot hit.
local ContextActionService = game:GetService("ContextActionService")
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")
local StarterGui = game:GetService("StarterGui")
local UserInputService = game:GetService("UserInputService")

local Shared = ReplicatedStorage:WaitForChild("DesertFps")
local WeaponConfig = require(Shared:WaitForChild("Weapons"):WaitForChild("WeaponConfig"))
local Ballistics = require(Shared.Weapons:WaitForChild("Ballistics"))
local CombatConfig = require(Shared:WaitForChild("Combat"):WaitForChild("CombatConfig"))
local Viewmodel = require(Shared:WaitForChild("Client"):WaitForChild("Viewmodel"))
local Hud = require(Shared.Client:WaitForChild("Hud"))
local CharacterAnimator = require(Shared.Client:WaitForChild("CharacterAnimator"))
local remotes = Shared:WaitForChild("Remotes")

local function remote(name: string): RemoteEvent
	return remotes:WaitForChild(name) :: RemoteEvent
end

-- How fast the view catches up with the recoil (per second).
local VIEW_FOLLOW = 30
-- A spray starts to settle once the trigger has been off for this many shots' worth of time.
local SETTLE_AFTER = 1.5

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera
local random = Random.new()

player.CameraMode = Enum.CameraMode.LockFirstPerson
StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Backpack, false)
StarterGui:SetCoreGuiEnabled(Enum.CoreGuiType.Health, false)

local effects = Instance.new("Folder")
effects.Name = "WeaponEffects"
effects.Parent = camera

local viewmodel = Viewmodel.new(Shared:WaitForChild("WeaponModels"), effects)
local hud = Hud.new(player:WaitForChild("PlayerGui"), camera)
local animator: any = nil -- the animations of the body the player has now

type Slot = { weapon: string, magazine: number, reserve: number }
local slots: { [string]: Slot } = {}
local current: string? = nil
local weapon: any = nil -- the numbers of the weapon in hand

local triggerHeld, triggerFresh = false, false -- fresh: pulled since the last shot
local aimHeld, walkHeld = false, false
local drawnAt = 0
local lastShot = 0
local reloadFrom: number? = nil
local slashFrom: number? = nil
local spray = 0 -- shots fired in the spray so far
local recoilUp, recoilRight = 0, 0 -- where the spray has pushed the shots, in degrees off the aim
local viewUp, viewRight = 0, 0 -- how much of that the view has climbed
local kicked = CFrame.identity -- that climb as it was last put on the camera
local kick = 0 -- 1 right after a shot, settling to 0: the weapon's own jolt
local aim = 0 -- 0 at the hip, 1 at the eye
local walked = 0
local stanceTold = ""
local lastStray = 0 -- how far the last shot was free to stray (for tests)

local function body(): (Model?, Humanoid?, BasePart?)
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	local root = character and character:FindFirstChild("HumanoidRootPart")
	if character and humanoid and humanoid.Health > 0 and root and root:IsA("BasePart") then
		return character, humanoid, root
	end
	return nil, nil, nil
end

local function ready(): boolean
	return weapon ~= nil and os.clock() - drawnAt >= weapon.EquipTime
end

local function refresh()
	if not current then
		return
	end
	hud:setRounds(weapon.Title, if weapon.Kind == "gun" then slots[current] else nil)
	local titles = {}
	for name, slot in slots do
		titles[name] = (WeaponConfig.Weapons :: any)[slot.weapon].Title
	end
	hud:setSlots(WeaponConfig.Slots, titles, current)
end

-- The weapon of that slot is now the one in hand.
local function take(slotName: string)
	current = slotName
	weapon = (WeaponConfig.Weapons :: any)[slots[slotName].weapon]
	drawnAt = os.clock()
	reloadFrom, slashFrom = nil, nil
	spray, recoilUp, recoilRight = 0, 0, 0
	viewmodel:show(slots[slotName].weapon)
	hud:setCrosshair(true)
	if animator then
		animator:hold(weapon.Animations)
	end
	refresh()
end

local function equip(slotName: string)
	if body() and slots[slotName] and slotName ~= current then
		take(slotName)
		remote("Equip"):FireServer(slotName)
	end
end

local function reload()
	if not (current and body() and weapon.Kind == "gun" and ready()) or reloadFrom then
		return
	end
	local slot = slots[current]
	if slot.magazine < weapon.Magazine and slot.reserve > 0 then
		reloadFrom = os.clock()
		remote("Reload"):FireServer()
		if animator then
			animator:play("Reload")
		end
	end
end

local function tracer(from: Vector3, to: Vector3, view: any)
	if not view.TracerTime or (to - from).Magnitude < 0.5 then
		return
	end
	local line = Instance.new("Part")
	line.Anchored = true
	line.CanCollide = false
	line.CanQuery = false
	line.CanTouch = false
	line.CastShadow = false
	line.Material = Enum.Material.Neon
	line.Color = view.TracerColor
	line.Size = Vector3.new(view.TracerWidth, view.TracerWidth, (to - from).Magnitude)
	line.CFrame = CFrame.lookAt((from + to) / 2, to)
	line.Parent = effects
	task.delay(view.TracerTime, line.Destroy, line)
end

-- What a shot from `origin` along `direction` looks to have hit from here, and whose body if anyone's. A knife
-- sweeps a ball of `radius` along the line instead. The server's own test is the one that counts.
local function claim(character: Model, origin: Vector3, direction: Vector3, range: number, radius: number?): (RaycastResult?, Model?, string?)
	local params = RaycastParams.new()
	params.FilterType = Enum.RaycastFilterType.Exclude
	params.FilterDescendantsInstances = { character, effects }
	local hit = if radius
		then workspace:Spherecast(origin, radius, direction * range, params)
		else workspace:Raycast(origin, direction * range, params)
	if not hit then
		return nil, nil, nil
	end
	local model = hit.Instance:FindFirstAncestorOfClass("Model")
	while model and not model:FindFirstChildOfClass("Humanoid") do
		model = model:FindFirstAncestorOfClass("Model")
	end
	local part = if model and (CombatConfig.Zones :: any)[hit.Instance.Name] then hit.Instance.Name else nil
	return hit, model, part
end

local function shoot(character: Model, humanoid: Humanoid, root: BasePart)
	local slot = slots[current :: string]
	local velocity = root.AssemblyLinearVelocity
	local aiming = aim > 0.5
	local up, right = Ballistics.recoil(weapon, spray, aiming)
	lastStray = Ballistics.spread(weapon, {
		speed = Vector3.new(velocity.X, 0, velocity.Z).Magnitude / weapon.RunSpeed,
		airborne = humanoid.FloorMaterial == Enum.Material.Air,
		walking = walkHeld,
		aiming = aiming,
		spray = spray,
	})
	-- The camera is the bare aim here: the view's climb is put on it after this, each frame.
	local origin = camera.CFrame.Position
	local direction = Ballistics.direction(camera.CFrame, up, right, lastStray, random)
	local hit, target, part = claim(character, origin, direction, weapon.Range)
	remote("FireWeapon"):FireServer(origin, direction, target, part)

	slot.magazine -= 1
	spray += 1
	recoilUp, recoilRight = up, right
	kick = 1
	if animator then
		animator:play("Fire")
	end
	tracer(viewmodel:socket("muzzle") or origin, if hit then hit.Position else origin + direction * weapon.Range, weapon.View)
	refresh()
end

local function slash(character: Model)
	local origin, direction = camera.CFrame.Position, camera.CFrame.LookVector
	local _, target, part = claim(character, origin, direction, weapon.Range, CombatConfig.MeleeMargin)
	remote("FireWeapon"):FireServer(origin, direction, target, part)
	slashFrom = os.clock()
	if animator then
		animator:play("Fire")
	end
end

local function pullTrigger(now: number, character: Model, humanoid: Humanoid, root: BasePart)
	if not ready() or reloadFrom or now - lastShot < weapon.FireInterval then
		return
	end
	-- Held down, the next shot is due one interval after the last was due, not after the frame that fired it:
	-- otherwise a weapon fires slower the lower the frame rate.
	local due = if now - lastShot < weapon.FireInterval * 2 then lastShot + weapon.FireInterval else now
	if weapon.Kind == "melee" then
		lastShot = due
		slash(character)
	elseif slots[current :: string].magazine > 0 then
		if weapon.Auto or triggerFresh then
			lastShot = due
			shoot(character, humanoid, root)
		end
	elseif triggerFresh then
		reload() -- pulling the trigger on an empty magazine
	end
	triggerFresh = false
end

local function ease(x: number): number
	return x * x * (3 - 2 * x)
end

-- Before the camera is worked out: take the view's climb back off it, so it does not pile up.
RunService:BindToRenderStep("DesertFpsBareAim", Enum.RenderPriority.Camera.Value - 1, function()
	camera.CFrame *= kicked:Inverse()
	kicked = CFrame.identity
end)

RunService:BindToRenderStep("DesertFpsWeapon", Enum.RenderPriority.Camera.Value + 1, function(dt: number)
	local now = os.clock()
	local character, humanoid, root = body()
	if not (character and humanoid and root and current) then
		return
	end
	local slot = slots[current]

	if reloadFrom and now - reloadFrom >= weapon.ReloadTime then
		-- The server does the same sum and says so; this is so the next shot does not wait for it.
		local rounds = math.min(weapon.Magazine - slot.magazine, slot.reserve)
		slot.magazine += rounds
		slot.reserve -= rounds
		reloadFrom = nil
		refresh()
	end
	if triggerHeld then
		pullTrigger(now, character, humanoid, root)
	end

	-- Recoil: a pause ends the spray, the shots come back down, and the view follows a share of it all.
	local recoil = weapon.Recoil
	if recoil then
		if now - lastShot > recoil.Reset then
			spray = 0
		end
		if now - lastShot > weapon.FireInterval * SETTLE_AFTER then
			local settle = math.exp(-recoil.Recover * dt)
			recoilUp, recoilRight = recoilUp * settle, recoilRight * settle
		end
	end
	local share = if recoil then recoil.View else 0
	local follow = 1 - math.exp(-VIEW_FOLLOW * dt)
	viewUp += (recoilUp * share - viewUp) * follow
	viewRight += (recoilRight * share - viewRight) * follow
	kicked = CFrame.Angles(0, math.rad(-viewRight), 0) * CFrame.Angles(math.rad(viewUp), 0, 0)
	camera.CFrame *= kicked

	-- Aiming down the sights, and how fast the player moves.
	local sights = weapon.Aim
	local aiming = aimHeld and sights ~= nil and ready() and not reloadFrom
	aim = math.clamp(aim + (if aiming then dt else -dt) / (if sights then sights.Time else 0.1), 0, 1)
	local hip = WeaponConfig.FieldOfView
	local eye = if sights then math.deg(2 * math.atan(math.tan(math.rad(hip / 2)) / sights.Zoom)) else hip
	camera.FieldOfView = hip + (eye - hip) * ease(aim)
	UserInputService.MouseDeltaSensitivity = camera.FieldOfView / hip
	local stance = `{walkHeld}{aiming}`
	if stance ~= stanceTold then
		stanceTold = stance
		remote("Stance"):FireServer(walkHeld, aiming)
	end
	humanoid.WalkSpeed = Ballistics.pace(weapon, walkHeld, aiming) -- the server sets the same; this is at once

	local velocity = root.AssemblyLinearVelocity
	local speed = Vector3.new(velocity.X, 0, velocity.Z).Magnitude
	if humanoid.FloorMaterial ~= Enum.Material.Air then
		walked += speed * dt
	end
	kick *= math.exp(-(weapon.View.Recover or 16) * dt)
	if slashFrom and now - slashFrom >= weapon.View.SlashTime then
		slashFrom = nil
	end
	viewmodel:update({
		camera = camera.CFrame,
		aim = aim,
		kick = kick,
		draw = math.clamp((now - drawnAt) / weapon.EquipTime, 0, 1),
		reload = if reloadFrom then (now - reloadFrom) / weapon.ReloadTime else nil,
		slash = if slashFrom then (now - slashFrom) / weapon.View.SlashTime else nil,
		walked = walked,
		moving = speed / weapon.RunSpeed,
	})

	hud:setVitals(humanoid.Health, (character:GetAttribute("Armor") :: number?) or 0)
	hud:setReload(if reloadFrom then (now - reloadFrom) / weapon.ReloadTime else nil)
end)

local function held(state: Enum.UserInputState): boolean
	return state == Enum.UserInputState.Begin
end

ContextActionService:BindAction("FireWeapon", function(_, state)
	triggerHeld = held(state)
	triggerFresh = triggerHeld
	return Enum.ContextActionResult.Sink
end, true, Enum.UserInputType.MouseButton1, Enum.KeyCode.ButtonR2)
ContextActionService:BindAction("AimWeapon", function(_, state)
	aimHeld = held(state)
	return Enum.ContextActionResult.Sink
end, false, Enum.UserInputType.MouseButton2, Enum.KeyCode.ButtonL2)
ContextActionService:BindAction("Walk", function(_, state)
	walkHeld = held(state)
	return Enum.ContextActionResult.Sink
end, false, Enum.KeyCode.LeftShift)
ContextActionService:BindAction("ReloadWeapon", function(_, state)
	if held(state) then
		reload()
	end
	return Enum.ContextActionResult.Sink
end, true, Enum.KeyCode.R, Enum.KeyCode.ButtonX)
local slotKeys = { Enum.KeyCode.One, Enum.KeyCode.Two, Enum.KeyCode.Three }
ContextActionService:BindAction("PickWeapon", function(_, state, input)
	local index = table.find(slotKeys, input.KeyCode)
	if held(state) and index and WeaponConfig.Slots[index] then
		equip(WeaponConfig.Slots[index])
	end
	return Enum.ContextActionResult.Sink
end, false, table.unpack(slotKeys))

-- The server says what the player carries: at spawn, after a reload, after a switch.
remote("State").OnClientEvent:Connect(function(state: { current: string, slots: { [string]: Slot } })
	slots = state.slots
	if state.current ~= current then
		take(state.current)
	else
		refresh()
	end
end)
remote("Hit").OnClientEvent:Connect(function(zone: string, _, killed: boolean)
	hud:hit(zone, killed)
end)
remote("Hurt").OnClientEvent:Connect(function()
	hud:hurt()
end)
remote("Killed").OnClientEvent:Connect(function(killer: string, victim: string, weaponTitle: string, head: boolean)
	hud:killed(killer, victim, weaponTitle, head)
end)
-- Someone else's shot: a line from the weapon in their hand to where it ended.
remote("Shot").OnClientEvent:Connect(function(shooter: Player, weaponName: string, origin: Vector3, finish: Vector3)
	local tool = shooter.Character and shooter.Character:FindFirstChildOfClass("Tool")
	local handle = tool and tool:FindFirstChild("Handle")
	local from = if handle and handle:IsA("BasePart") then handle.Position else origin
	tracer(from, finish, (WeaponConfig.Weapons :: any)[weaponName].View)
end)

-- The player's own body is unseen in first person, but a tool in its hand is not: the weapon would show twice.
local function hideHeld(character: Model)
	local function hide(tool: Instance)
		if tool:IsA("Tool") then
			for _, part in tool:GetDescendants() do
				if part:IsA("BasePart") then
					part.LocalTransparencyModifier = 1
				end
			end
		end
	end
	for _, child in character:GetChildren() do
		hide(child)
	end
	character.ChildAdded:Connect(hide)
end

local function onCharacter(character: Model)
	hideHeld(character)
	local humanoid = character:WaitForChild("Humanoid") :: Humanoid
	animator = CharacterAnimator.new(character)
	if current then
		animator:hold(weapon.Animations) -- the weapon was in hand before the body was ready
	end
	humanoid.Died:Once(function()
		animator = nil
		current = nil
		triggerHeld, aimHeld = false, false
		viewmodel:show(nil)
		hud:setCrosshair(false)
		hud:setReload(nil)
	end)
end
player.CharacterAdded:Connect(onCharacter)
if player.Character then
	onCharacter(player.Character)
end

-- A hook for test scripts, which cannot press keys (DevConfig.TestHooks):
--   ReplicatedStorage.DesertFps.DevWeapon:Invoke("trigger" | "aim" | "walk", held)   ("equip", slot)   ("reload")
--   ("state") returns what the weapon is doing.
local function testHook()
	if Shared:FindFirstChild("DevWeapon") or not Shared:GetAttribute("TestHooks") then
		return
	end
	local hook = Instance.new("BindableFunction")
	hook.Name = "DevWeapon"
	hook.OnInvoke = function(what: string, value: any): any
		if what == "trigger" then
			triggerHeld, triggerFresh = value, value
		elseif what == "aim" then
			aimHeld = value
		elseif what == "walk" then
			walkHeld = value
		elseif what == "equip" then
			equip(value)
		elseif what == "reload" then
			reload()
		elseif what == "state" and current then
			return {
				slot = current,
				weapon = slots[current].weapon,
				magazine = slots[current].magazine,
				reserve = slots[current].reserve,
				ready = ready(),
				reloading = reloadFrom ~= nil,
				spray = spray,
				recoilUp = recoilUp,
				recoilRight = recoilRight,
				viewUp = viewUp,
				stray = lastStray,
				aim = aim,
			}
		end
		return nil
	end
	hook.Parent = Shared
end
Shared:GetAttributeChangedSignal("TestHooks"):Connect(testHook)
testHook()

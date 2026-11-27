-- Test: what the attachments do. Run on the CLIENT during a playtest, with DevConfig.TestHooks on, standing
-- where the rifle has a clear view (the spawn). It fits things through ReplicatedStorage.DesertFps.DevWeapon
-- (a test cannot press keys) and reads back what the server answered: the client's own guess is replaced by
-- the server's word within a moment. Takes about 80 seconds. Returns one line per check, each starting "ok"
-- or "WRONG":
--   every attachment changes the numbers AttachmentConfig says it does, on the rifle and on the pistol
--   what does not go on a weapon, or on that socket, or does not exist, is refused, also when the request
--     is sent straight to the server
--   the weapon everyone sees carries a part for each attachment that has a model
--   an extended magazine is filled by a reload, and its extra rounds go back to the reserve when it comes off
--   a compensator lowers the climb of a spray
--   aiming brings the sight in use onto the line of sight: the iron sights, the red dot, the scope
--   a laser shows its dot and a beam to it from the laser, only while it is on the weapon, and the weapon
--     everyone sees says where its beam starts
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.DesertFps
local hook = Shared:WaitForChild("DevWeapon") :: BindableFunction
local AttachmentConfig = require(Shared.Weapons.AttachmentConfig)
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local camera = workspace.CurrentCamera
local player = Players.LocalPlayer

-- Long enough for the server's answer, and for the weapon to be drawn again.
local ANSWER = 0.5
local DRAWN = 1.3
local AIM = CFrame.Angles(0, math.pi / 2, 0) -- as in Client/Viewmodel

local lines = {}
local function check(right: boolean, what: string)
	table.insert(lines, (if right then "ok     " else "WRONG  ") .. what)
end

local function near(a: number, b: number): boolean
	return math.abs(a - b) < 1e-3 * math.max(1, math.abs(b))
end

local function state(): any
	return hook:Invoke("state")
end

local function fit(socket: string, name: string?)
	hook:Invoke("attach", { socket = socket, name = name })
	task.wait(ANSWER)
end

local function strip()
	for _, socket in AttachmentConfig.Sockets do
		if state().attachments[socket] then
			fit(socket, nil)
		end
	end
end

-- A number of the weapon in hand, by a path like "Recoil.Sway".
local function number(numbers: any, path: string): any
	local value = numbers
	for _, name in string.split(path, ".") do
		value = if typeof(value) == "table" then value[name] else nil
	end
	return value
end

-- The parts of the weapon in the character's hand, which the server makes and everyone sees.
local function partsInHand(): number
	local tool = player.Character and player.Character:FindFirstChildOfClass("Tool")
	local count = 0
	for _, part in if tool then tool:GetChildren() else {} do
		if part:IsA("BasePart") and part.Name ~= "Handle" then
			count += 1
		end
	end
	return count
end

-- How far the sight in use is from where aiming should bring it, in studs, and how far the barrel points from
-- where the eye looks, in degrees: the worst of a second of looking.
local function sightError(weaponName: string, sight: Vector3, numbers: any): (number, number)
	local rig = (camera :: any).WeaponEffects.ViewArms
	local handle = rig[weaponName].Handle
	local goal = Vector3.new(0, -(numbers.View.SightDrop or 0), -numbers.View.SightDistance)
	local off, turned = 0, 0
	local till = os.clock() + 1
	while os.clock() < till do
		RunService.RenderStepped:Wait()
		local frame = camera.CFrame:ToObjectSpace(handle.CFrame * AIM)
		off = math.max(off, (frame * sight - goal).Magnitude)
		turned = math.max(turned, math.deg(math.acos(math.clamp(-frame.XVector.Z, -1, 1))))
	end
	return off, turned
end

local function socketOf(model: Instance, name: string): Vector3
	return model:GetAttribute("Socket_" .. name) :: Vector3
end

-- 1. What each attachment changes, on each weapon it goes on, and that the server agrees.
for _, slotName in { "primary", "secondary" } do
	hook:Invoke("equip", slotName)
	task.wait(DRAWN)
	strip()
	local weaponName = state().weapon
	local plain = (WeaponConfig.Weapons :: any)[weaponName]
	local bare = partsInHand()
	for name, what in AttachmentConfig.Attachments :: { [string]: any } do
		local changes = what.Fits[weaponName]
		fit(what.Socket, name)
		local now = state()
		if not changes then
			check(now.attachments[what.Socket] == nil, `{weaponName}: {name} does not go on it, and is refused`)
			continue
		end
		local right = now.attachments[what.Socket] == name
		for path, factor in changes.Scale or {} do
			right = right and near(number(now.numbers, path), number(plain, path) * factor)
		end
		for path, amount in changes.Add or {} do
			right = right and near(number(now.numbers, path), number(plain, path) + amount)
		end
		for path, value in changes.Set or {} do
			if typeof(value) ~= "table" then
				right = right and number(now.numbers, path) == value
			end
		end
		check(right, `{weaponName}: {name} is on, and changes what AttachmentConfig says`)
		task.wait(DRAWN - ANSWER)
		check(
			partsInHand() == bare + (if what.Model then 1 else 0),
			`{weaponName}: with {name} the weapon in hand has {partsInHand()} parts ({bare} bare)`
		)
		fit(what.Socket, nil)
	end
end

-- 2. Requests that make no sense, sent straight to the server: it must leave the weapon as it is.
hook:Invoke("equip", "primary")
task.wait(DRAWN)
strip()
local attach = Shared.Remotes.Attach :: RemoteEvent
local before = partsInHand()
attach:FireServer("primary", "optic", "suppressor") -- the wrong socket
attach:FireServer("primary", "muzzle", "no such thing")
attach:FireServer("primary", "barrel", "suppressor") -- no such socket
attach:FireServer("no such slot", "muzzle", "suppressor")
attach:FireServer("melee", "muzzle", "suppressor") -- nothing goes on the knife
attach:FireServer("primary", "muzzle", 7)
attach:FireServer({}, nil, nil)
task.wait(DRAWN)
local after = state()
check(
	next(after.attachments) == nil and partsInHand() == before,
	"seven requests that make no sense leave the rifle bare"
)

-- 3. The extended magazine: a reload fills it; taken off, the rounds it held extra go back to the reserve.
fit("magazine", "magazine")
task.wait(DRAWN)
local fitted = state()
check(fitted.magazine == 25 and fitted.numbers.Magazine == 35, `a longer magazine holds 35, and starts with the 25 that were in`)
hook:Invoke("reload")
task.wait(fitted.numbers.ReloadTime + ANSWER)
local full = state()
check(full.magazine == 35 and full.reserve == 65, `a reload fills it: {full.magazine} in, {full.reserve} in reserve`)
fit("magazine", nil)
local back = state()
check(back.magazine == 25 and back.reserve == 75, `taken off: {back.magazine} in, {back.reserve} in reserve`)
task.wait(DRAWN)

-- 4. The compensator: the tenth shot of a spray leaves 0.78 as high.
local function climb(): number
	hook:Invoke("trigger", true)
	local highest = 0
	local till = os.clock() + 1.05
	while os.clock() < till do
		RunService.RenderStepped:Wait()
		highest = math.max(highest, state().recoilUp)
	end
	hook:Invoke("trigger", false)
	task.wait(1)
	hook:Invoke("reload")
	task.wait(WeaponConfig.Weapons.rifle.ReloadTime + ANSWER)
	return highest
end
local plainClimb = climb()
fit("muzzle", "compensator")
task.wait(DRAWN)
local lowerClimb = climb()
check(
	plainClimb > 7 and near(lowerClimb, plainClimb * 0.78),
	("a spray climbs %.2f degrees bare and %.2f with a compensator"):format(plainClimb, lowerClimb)
)
fit("muzzle", nil)
task.wait(DRAWN)

-- 5. Aiming: the sight in use comes onto the line of sight, and the barrel points where the eye looks.
local models, attachments = Shared.WeaponModels, Shared.AttachmentModels
local function aimed(slotName: string, weaponName: string, optic: string?)
	hook:Invoke("equip", slotName)
	task.wait(DRAWN)
	if state().attachments.optic ~= optic then
		fit("optic", optic)
		task.wait(DRAWN)
	end
	local weapon = models[weaponName]
	local sight = socketOf(weapon, "aim_rear")
	if optic then
		local piece = attachments[(AttachmentConfig.Attachments :: any)[optic].Model]
		sight = socketOf(weapon, "optic") + socketOf(piece, "eye")
	end
	hook:Invoke("aim", true)
	task.wait(1.2)
	local off, turned = sightError(weaponName, sight, state().numbers)
	hook:Invoke("aim", false)
	task.wait(0.5)
	check(
		off < 0.01 and turned < 0.5,
		("%s, %s: the sight is %.4f studs from the line of sight, the barrel %.2f degrees off"):format(
			weaponName,
			optic or "iron sights",
			off,
			turned
		)
	)
end
aimed("primary", "rifle", nil)
aimed("primary", "rifle", "reddot")
aimed("primary", "rifle", "scope")
aimed("secondary", "pistol", "reddot")
fit("optic", nil)

-- 6. The laser's dot.
hook:Invoke("equip", "primary")
task.wait(DRAWN)
fit("optic", nil)
local effects = (camera :: any).WeaponEffects
local function light(): (Instance?, Beam?)
	local dot = effects:FindFirstChild("LaserDot")
	return dot, if dot then dot:FindFirstChildOfClass("Beam") else nil
end
check(light() == nil, "no laser, no light")
fit("side", "laser")
task.wait(DRAWN)
local dot, beam = light()
check(
	dot ~= nil and beam ~= nil and beam.Enabled and beam.Attachment0 ~= nil and beam.Attachment0.Name == "Laser",
	"a laser on the rifle shows its dot, and a beam to it from the laser"
)
local inHand = player.Character and player.Character:FindFirstChildOfClass("Tool")
check(
	inHand ~= nil and inHand:FindFirstChild("Laser", true) ~= nil,
	"the weapon everyone sees says where its beam starts"
)
fit("side", nil)
task.wait(DRAWN)
check(light() == nil, "taken off, the light goes")

return table.concat(lines, "\n")

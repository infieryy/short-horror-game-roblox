-- Test: the game's sounds. Run on the CLIENT during a playtest, with DevConfig.TestHooks and
-- DevConfig.Dummies on, from a fresh spawn with the rifle in hand. It cannot hear: it checks that every sound
-- can be fetched, and that each is played when and where it should be, by what Client/Sounds says it has
-- played. It fires, reloads and throws through ReplicatedStorage.DesertFps.DevWeapon, and walks the player
-- about. Takes about 40 seconds: start it in a task.spawn and read the result afterwards. Returns one line
-- per check, each starting "ok" or "WRONG":
--   every sound in SoundConfig can be fetched and has a length
--   every sound a weapon, an attachment, a mark, the dart, the footsteps or the display names is in SoundConfig
--   running is heard as steps and Roblox's own footsteps are not; walking is not heard; a landing is
--   a shot is heard; a suppressed shot is another sound; an empty weapon clicks
--   a reload is heard as its magazine out, its magazine in and its bolt, in that order
--   drawing a weapon is heard, and the knife's slash
--   a shot is heard where it lands: one sound where it goes through, another where it is stopped
--   a shot to a dummy's head is heard as one, and so is the kill
--   the dart is heard thrown, stuck and pulsing, where it is
local Players = game:GetService("Players")
local ContentProvider = game:GetService("ContentProvider")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.DesertFps
local hook = Shared:WaitForChild("DevWeapon") :: BindableFunction
local SoundConfig = require(Shared.Sound.SoundConfig)
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local AttachmentConfig = require(Shared.Weapons.AttachmentConfig)
local UtilityConfig = require(Shared.Utility.UtilityConfig)
local MarkConfig = require(Shared.Client.MarkConfig)
local Penetration = require(Shared.Weapons.Penetration)
local BulletMarks = require(Shared.Client.BulletMarks)
local Sounds = require(Shared.Client.Sounds)

local player = Players.LocalPlayer
local camera = workspace.CurrentCamera
local rifle, pistol, knife = WeaponConfig.Weapons.rifle, WeaponConfig.Weapons.pistol, WeaponConfig.Weapons.knife

local lines = {}
local function check(right: boolean, what: string)
	table.insert(lines, (if right then "ok     " else "WRONG  ") .. what)
end

local function frames(count: number)
	for _ = 1, count do
		RunService.RenderStepped:Wait()
	end
end

-- How often a sound has been played.
local function played(name: string): number
	return Sounds.state().played[name] or 0
end

-- How often each of these sounds is played while `act` runs.
local function during(names: { string }, act: () -> ()): { number }
	local before = {}
	for index, name in names do
		before[index] = played(name)
	end
	act()
	local counts = {}
	for index, name in names do
		counts[index] = played(name) - before[index]
	end
	return counts
end

local function tap()
	hook:Invoke("trigger", true)
	frames(2)
	hook:Invoke("trigger", false)
end

-- 1. Every sound can be fetched.
local ids, failed, seen = {}, {}, {}
for name, entry in SoundConfig.Sounds :: { [string]: any } do
	if #entry.Takes == 0 then
		table.insert(failed, name .. " has no take")
	end
	for _, take in entry.Takes do
		if not seen[take.Id] then
			seen[take.Id] = true
			table.insert(ids, { name = name, id = take.Id })
		end
	end
end
local waiting = #ids
for _, each in ids do
	task.spawn(function()
		local sound = Instance.new("Sound")
		sound.SoundId = "rbxassetid://" .. each.id
		ContentProvider:PreloadAsync({ sound }, function(_, status)
			if status ~= Enum.AssetFetchStatus.Success then
				table.insert(failed, `{each.name} {each.id}: {status.Name}`)
			end
		end)
		local started = os.clock()
		while not sound.IsLoaded and os.clock() - started < 10 do
			task.wait(0.1)
		end
		if not (sound.IsLoaded and sound.TimeLength > 0) then
			table.insert(failed, `{each.name} {each.id}: no length`)
		end
		sound:Destroy()
		waiting -= 1
	end)
end
while waiting > 0 do
	task.wait(0.2)
end
check(#failed == 0, ("all %d recordings can be fetched and have a length%s"):format(#ids, if #failed > 0 then ": " .. table.concat(failed, "; ") else ""))

-- 2. Every sound that is named exists.
local missing = {}
local function named(name: any, by: string)
	if typeof(name) == "string" and not (SoundConfig.Sounds :: any)[name] then
		table.insert(missing, `{by}: {name}`)
	end
end
for weapon, config in WeaponConfig.Weapons :: { [string]: any } do
	for _, name in config.Sounds do
		named(name, weapon)
	end
end
for attachment, what in AttachmentConfig.Attachments :: { [string]: any } do
	for _, changes in what.Fits do
		for path, value in changes.Set or {} do
			if string.find(path, "^Sounds%.") then
				named(value, attachment)
			end
		end
	end
end
for material, look in MarkConfig.Materials :: { [string]: any } do
	for _, name in look.Sound or {} do
		named(name, material)
	end
end
for _, name in UtilityConfig.Sounds do
	named(name, "utility")
end
for _, name in SoundConfig.Cues do
	named(name, "cue")
end
named(SoundConfig.Footsteps.Step, "footsteps")
named(SoundConfig.Footsteps.Land, "footsteps")
check(#missing == 0, "every sound that is named is in SoundConfig" .. (if #missing > 0 then ": " .. table.concat(missing, "; ") else ""))

-- 3. Roblox's own.
local character = player.Character :: Model
local humanoid = character:FindFirstChildOfClass("Humanoid") :: Humanoid
local root = character:FindFirstChild("HumanoidRootPart") :: BasePart
-- Roblox puts its own sounds in every body; it is its script that plays them, and that is stood in for.
local theirs = root:FindFirstChild("Running") :: Sound?
local theirsHeard = false

-- 4. Shots. Aimed at the sky, so that nothing answers.
hook:Invoke("equip", "primary")
task.wait(1.2)
camera.CFrame = CFrame.lookAlong(camera.CFrame.Position, Vector3.new(0, 1, -0.2).Unit)
frames(3)
local shot = during({ rifle.Sounds.Fire, "Rifle Shot Quiet" }, function()
	tap()
	task.wait(0.4)
end)
check(shot[1] == 1 and shot[2] == 0, ("a rifle shot is heard: %d, and %d of the quiet one"):format(shot[1], shot[2]))

hook:Invoke("attach", { socket = "muzzle", name = "suppressor" })
task.wait(1.6)
shot = during({ rifle.Sounds.Fire, "Rifle Shot Quiet" }, function()
	tap()
	task.wait(0.4)
end)
check(shot[1] == 0 and shot[2] == 1, ("suppressed, it is the quiet one: %d, and %d of the loud one"):format(shot[2], shot[1]))
hook:Invoke("attach", { socket = "muzzle" })
task.wait(1.6)

-- The magazine is emptied; the next pull of the trigger clicks and starts a reload.
hook:Invoke("trigger", true)
local emptying = os.clock()
while hook:Invoke("state").magazine > 0 and os.clock() - emptying < 5 do
	task.wait(0.1)
end
hook:Invoke("trigger", false)
task.wait(0.5)
local order = {}
local cues = { rifle.Sounds.Empty, rifle.Sounds.MagazineOut, rifle.Sounds.MagazineIn, rifle.Sounds.Bolt }
local before = {}
for index, name in cues do
	before[index] = played(name)
end
tap()
local reloading = os.clock()
while os.clock() - reloading < rifle.ReloadTime + 0.5 do
	for index, name in cues do
		if played(name) > before[index] then
			before[index] = played(name)
			table.insert(order, name)
		end
	end
	task.wait()
end
check(
	table.concat(order, ", ") == table.concat(cues, ", "),
	"an empty rifle clicks, and its reload is heard in order: " .. table.concat(order, ", ")
)
check(hook:Invoke("state").magazine == rifle.Magazine, "and the reload still fills the magazine")

-- 5. Drawing, and the knife.
local draw = during({ pistol.Sounds.Draw }, function()
	hook:Invoke("equip", "secondary")
	task.wait(0.8)
end)
check(draw[1] == 1, ("drawing the pistol is heard: %d"):format(draw[1]))
local blade = during({ knife.Sounds.Draw, knife.Sounds.Fire }, function()
	hook:Invoke("equip", "melee")
	task.wait(0.7)
	tap()
	task.wait(0.5)
end)
check(blade[1] == 1 and blade[2] == 1, ("the knife is heard drawn and slashing: %d, %d"):format(blade[1], blade[2]))

-- 6. Where a shot lands. Slabs of this client's own, far above the town.
local stage = Instance.new("Folder")
stage.Name = "SoundTest"
stage.Parent = workspace
local drawn = Instance.new("Folder")
drawn.Parent = stage
local marks = BulletMarks.new(drawn)
local everything = RaycastParams.new()
everything.FilterType = Enum.RaycastFilterType.Exclude
everything.FilterDescendantsInstances = {}
local function stand(place: number, piece: string, thick: number): BasePart
	local model = Instance.new("Model")
	model.Name = piece
	model:SetAttribute("Piece", piece)
	local slab = Instance.new("Part")
	slab.Name = "Whole"
	slab.Anchored = true
	slab.Size = Vector3.new(6, 6, thick)
	slab.Position = Vector3.new(place * 40, 800, 0)
	slab.Parent = model
	model.Parent = stage
	return slab
end
local wall = stand(1, "wall2_plain", 1)
task.wait()
local look = MarkConfig.Materials.plaster.Sound
local function shootWall(pierce: number)
	local path = Penetration.trace(wall.Position - Vector3.zAxis * 10, Vector3.zAxis, 40, pierce, everything)
	marks:leave(Penetration.marks(path))
end
local landed = during({ look.Through, look.Stopped }, function()
	shootWall(rifle.Pierce)
end)
local where = Sounds.state().at[look.Through]
check(
	landed[1] == 1 and landed[2] == 0 and where ~= nil and (where - (wall.Position - Vector3.zAxis * 0.5)).Magnitude < 0.1,
	("a shot through a wall is heard once, where it went in: %d through, %d stopped"):format(landed[1], landed[2])
)
landed = during({ look.Through, look.Stopped }, function()
	shootWall(pistol.Pierce)
end)
check(landed[1] == 0 and landed[2] == 1, ("a shot the wall stops sounds different: %d stopped, %d through"):format(landed[2], landed[1]))
stage:Destroy()

-- 7. A hit. One rifle shot to the head of a dummy with no armor kills it.
local function dummy(kind: string): Model
	while true do
		for _, model in workspace:WaitForChild("Dummies"):GetChildren() do
			local theirs = model:FindFirstChildOfClass("Humanoid")
			local still = model:FindFirstChild("HumanoidRootPart")
			if
				theirs
				and still
				and theirs.Health >= theirs.MaxHealth
				and string.find(theirs.DisplayName, kind, 1, true)
				and (still :: BasePart).AssemblyLinearVelocity.Magnitude < 1
				and model:FindFirstChild("Head")
			then
				return model :: Model
			end
		end
		task.wait(0.3)
	end
end
hook:Invoke("equip", "primary")
task.wait(1.2)
local head = dummy("no armor"):FindFirstChild("Head") :: BasePart
local hit = during({ SoundConfig.Cues.Head, SoundConfig.Cues.Kill, SoundConfig.Cues.Hit }, function()
	camera.CFrame = CFrame.lookAt(camera.CFrame.Position, head.Position)
	frames(3)
	tap()
	task.wait(0.6)
end)
check(hit[1] == 1 and hit[2] == 1 and hit[3] == 0, ("a shot to the head that kills is heard as both: %d head, %d kill"):format(hit[1], hit[2]))

-- 8. The dart, thrown at the ground ahead.
local dart = UtilityConfig.Utilities.recon
local heard = UtilityConfig.Sounds
camera.CFrame = CFrame.lookAlong(camera.CFrame.Position, Vector3.new(0, -0.5, -1).Unit)
frames(3)
local thrown = during({ heard.Throw, heard.Stick, heard.Pulse }, function()
	hook:Invoke("utility", "recon")
	task.wait(dart.ThrowTime + 1.5 + dart.Arm + dart.Every * dart.Pulses)
end)
local stuck = workspace:WaitForChild("Utilities"):FindFirstChildWhichIsA("Model", true)
local pulsed = Sounds.state().at[heard.Pulse]
check(
	thrown[1] == 1 and thrown[2] == 1 and thrown[3] == dart.Pulses,
	("the dart is heard thrown, stuck and pulsing: %d, %d, %d pulses"):format(thrown[1], thrown[2], thrown[3])
)
check(
	pulsed ~= nil and (pulsed - root.Position).Magnitude > 3 and (pulsed - root.Position).Magnitude < 60,
	("its pulse is heard where the dart is: %.0f studs off%s"):format(
		if pulsed then (pulsed - root.Position).Magnitude else -1,
		if stuck then "" else " (the dart is gone by now)"
	)
)

-- 9. Steps. The player is run, walked and jumped: this goes after the keys are read, so it wins.
local way: Vector3? = nil
RunService:BindToRenderStep("SoundTestMove", Enum.RenderPriority.Input.Value + 1, function()
	if way then
		player:Move(way, false)
	end
end)
local feet = SoundConfig.Footsteps
task.wait(dart.Linger + 1)
local steps = during({ feet.Step }, function()
	way = Vector3.new(0, 0, 1)
	local started = os.clock()
	while os.clock() - started < 1.5 do
		theirsHeard = theirsHeard or (theirs ~= nil and theirs.IsPlaying)
		task.wait()
	end
	way = Vector3.zero
	task.wait(0.5)
end)
check(steps[1] >= 3 and steps[1] <= 7, ("a second and a half of running is heard as steps: %d"):format(steps[1]))
check(not theirsHeard, "and Roblox's own footsteps are not")
hook:Invoke("walk", true)
steps = during({ feet.Step }, function()
	way = Vector3.new(0, 0, -1)
	task.wait(1.5)
	way = Vector3.zero
	task.wait(0.5)
end)
hook:Invoke("walk", false)
check(steps[1] == 0, ("walking is not heard: %d steps"):format(steps[1]))
local land = during({ feet.Land }, function()
	humanoid:ChangeState(Enum.HumanoidStateType.Jumping)
	task.wait(1.5)
end)
check(land[1] == 1, ("a landing is heard: %d"):format(land[1]))
way = nil
RunService:UnbindFromRenderStep("SoundTestMove")

return table.concat(lines, "\n")

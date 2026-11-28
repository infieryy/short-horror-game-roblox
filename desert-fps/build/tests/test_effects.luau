-- Test: how shots look. Run on the CLIENT during a playtest, with DevConfig.TestHooks and DevConfig.Dummies
-- on, from a fresh spawn with the rifle in hand. It cannot see: it checks that each effect is shown when it
-- should be, by what Client/Effects says it has shown. Takes about 12 seconds. Returns one line per check,
-- each starting "ok" or "WRONG":
--   a shot shows a flash at the muzzle and a tracer; a suppressed shot shows a wisp and no flash
--   the flash is gone a moment later, and every streak has landed
--   a shot that marks the town throws sparks; cloth throws none
--   a shot to a dummy's body bursts as a body hit, one to its head as a head hit
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.DesertFps
local hook = Shared:WaitForChild("DevWeapon") :: BindableFunction
local Effects = require(Shared.Client.Effects)
local Config = require(Shared.Client.EffectConfig)
local BulletMarks = require(Shared.Client.BulletMarks)
local Penetration = require(Shared.Weapons.Penetration)
local WeaponConfig = require(Shared.Weapons.WeaponConfig)

local camera = workspace.CurrentCamera
local lines = {}
local function check(right: boolean, what: string)
	table.insert(lines, (if right then "ok     " else "WRONG  ") .. what)
end
local function frames(count: number)
	for _ = 1, count do
		RunService.RenderStepped:Wait()
	end
end
local function tap()
	hook:Invoke("trigger", true)
	frames(2)
	hook:Invoke("trigger", false)
end
-- How often each of these effects is shown while `act` runs.
local function during(names: { string }, act: () -> ()): { number }
	local before = Effects.state()
	act()
	local after = Effects.state()
	local counts = {}
	for index, name in names do
		counts[index] = (after[name] or 0) - (before[name] or 0)
	end
	return counts
end

hook:Invoke("equip", "primary")
task.wait(1.2)
camera.CFrame = CFrame.lookAlong(camera.CFrame.Position, Vector3.new(0, 0.2, -1).Unit)
frames(3)
local shot = during({ "flash", "tracer", "wisp" }, function()
	tap()
	frames(1)
end)
check(shot[1] == 1 and shot[2] == 1 and shot[3] == 0, ("a shot shows a flash and a tracer: %d, %d"):format(shot[1], shot[2]))
task.wait(Config.Muzzle.Time + 0.6)
local lit = 0
for _, light in camera:GetDescendants() do
	if light:IsA("PointLight") and light.Enabled then
		lit += 1
	end
end
check(lit == 0 and Effects.state().flying == 0, ("a moment later the flash is out and nothing is in flight: %d lit, %d flying"):format(lit, Effects.state().flying))

hook:Invoke("attach", { socket = "muzzle", name = "suppressor" })
task.wait(1.6)
shot = during({ "flash", "wisp" }, function()
	tap()
	task.wait(0.3)
end)
check(shot[1] == 0 and shot[2] == 1, ("suppressed, it is a wisp of smoke and no flash: %d wisp, %d flash"):format(shot[2], shot[1]))
hook:Invoke("attach", { socket = "muzzle" })
task.wait(1.6)

-- Marks: a slab of plaster and one of cloth, this client's own, far above the town.
local stage = Instance.new("Folder")
stage.Parent = workspace
local marks = BulletMarks.new(stage)
local everything = RaycastParams.new()
everything.FilterType = Enum.RaycastFilterType.Exclude
everything.FilterDescendantsInstances = {}
local function sparksOff(piece: string, place: number): number
	local model = Instance.new("Model")
	model.Name = piece
	model:SetAttribute("Piece", piece)
	local slab = Instance.new("Part")
	slab.Anchored = true
	slab.Size = Vector3.new(6, 6, 1)
	slab.Position = Vector3.new(place * 40, 900, 0)
	slab.Parent = model
	model.Parent = stage
	task.wait()
	return during({ "sparks" }, function()
		local path = Penetration.trace(slab.Position - Vector3.zAxis * 10, Vector3.zAxis, 40, WeaponConfig.Weapons.rifle.Pierce, everything)
		marks:leave(Penetration.marks(path))
	end)[1]
end
local offWall, offCloth = sparksOff("wall2_plain", 1), sparksOff("rack_red", 2)
check(offWall == 2 and offCloth == 0, ("a shot through a wall throws sparks going in and coming out, cloth none: %d, %d"):format(offWall, offCloth))
stage:Destroy()

-- Hits. The server says where each landed.
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
local target = dummy("heavy")
local hit = during({ "body", "head" }, function()
	camera.CFrame = CFrame.lookAt(camera.CFrame.Position, (target:FindFirstChild("UpperTorso") :: BasePart).Position)
	frames(3)
	tap()
	task.wait(0.6)
end)
check(hit[1] == 1 and hit[2] == 0, ("a shot to the body bursts as a body hit: %d"):format(hit[1]))
hit = during({ "body", "head" }, function()
	camera.CFrame = CFrame.lookAt(camera.CFrame.Position, (target:FindFirstChild("Head") :: BasePart).Position)
	frames(3)
	tap()
	task.wait(0.6)
end)
check(hit[2] == 1 and hit[1] == 0, ("a shot to the head bursts as a head hit: %d"):format(hit[2]))

return table.concat(lines, "\n")

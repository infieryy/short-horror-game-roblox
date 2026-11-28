-- Test: how shots look. Run on the CLIENT during a playtest, with DevConfig.TestHooks and DevConfig.Dummies
-- on, from a fresh spawn with the rifle in hand. It cannot see: it checks that each effect is shown when it
-- should be, by what Client/Effects says it has shown. Takes about 12 seconds. Returns one line per check,
-- each starting "ok" or "WRONG":
--   a shot shows a flash at the muzzle and a tracer; a suppressed shot shows a wisp and no flash
--   a moment later nothing is still showing
--   a shot that lands on the town shows a spark there; one into the sky shows none
--   a shot to a dummy's body bursts as a body hit, one to its head as a head hit
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.DesertFps
local hook = Shared:WaitForChild("DevWeapon") :: BindableFunction
local Effects = require(Shared.Client.Effects)
local Config = require(Shared.Client.EffectConfig)

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
local shot = during({ "flash", "tracer", "wisp", "spark" }, function()
	tap()
	frames(1)
end)
check(
	shot[1] == 1 and shot[2] == 1 and shot[3] == 0 and shot[4] == 0,
	("a shot into the sky shows a flash and a tracer, and no spark: %d, %d, %d"):format(shot[1], shot[2], shot[4])
)
task.wait(Config.Muzzle.Time + 0.6)
local lit = 0
for _, light in camera:GetDescendants() do
	if light:IsA("PointLight") and light.Enabled then
		lit += 1
	end
end
check(lit == 0 and Effects.state().showing == 0, ("a moment later nothing is still showing: %d lit, %d showing"):format(lit, Effects.state().showing))

hook:Invoke("attach", { socket = "muzzle", name = "suppressor" })
task.wait(1.6)
shot = during({ "flash", "wisp" }, function()
	tap()
	task.wait(0.3)
end)
check(shot[1] == 0 and shot[2] == 1, ("suppressed, it is a wisp of smoke and no flash: %d wisp, %d flash"):format(shot[2], shot[1]))
hook:Invoke("attach", { socket = "muzzle" })
task.wait(1.6)

-- A shot at the ground in front lands, and shows a spark where it does.
camera.CFrame = CFrame.lookAlong(camera.CFrame.Position, Vector3.new(0, -0.45, -1).Unit)
frames(3)
shot = during({ "spark" }, function()
	tap()
	task.wait(0.3)
end)
check(shot[1] == 1, ("a shot that lands shows a spark: %d"):format(shot[1]))

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

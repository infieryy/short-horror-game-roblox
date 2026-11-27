-- Test: what each weapon does to the target dummies. Run on the CLIENT during a playtest, with
-- DevConfig.TestHooks and DevConfig.Dummies on. It aims the camera at a dummy, pulls the trigger through
-- ReplicatedStorage.DesertFps.DevWeapon (a test cannot press keys), and reads the dummy's armor and health
-- back, which only the server changes. Takes about 25 seconds. Returns one line per check, each starting
-- "ok" or "WRONG":
--   rifle: one shot to the head kills, with or without heavy armor; four to the body kill through heavy armor
--   pistol: two shots to the head kill through heavy armor
--   a reload fills the magazine from the reserve
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local hook = ReplicatedStorage.DesertFps:WaitForChild("DevWeapon") :: BindableFunction
local camera = workspace.CurrentCamera
local dummies = workspace:WaitForChild("Dummies")

-- Seconds between shots: longer than any weapon's spray lasts, so every shot is a first shot.
local PAUSE = 0.5

local function frames(count: number)
	for _ = 1, count do
		RunService.RenderStepped:Wait()
	end
end

-- A standing dummy of that kind at full health, waiting for one to come back if it has just been killed.
local function dummy(kind: string): Model
	while true do
		for _, model in dummies:GetChildren() do
			local humanoid = model:FindFirstChildOfClass("Humanoid")
			local still = model:FindFirstChild("HumanoidRootPart")
			if
				humanoid
				and still
				and humanoid.Health >= humanoid.MaxHealth
				and string.find(humanoid.DisplayName, kind, 1, true)
				and (still :: BasePart).AssemblyLinearVelocity.Magnitude < 1
				and model:FindFirstChild("Head")
			then
				return model :: Model
			end
		end
		task.wait(0.3)
	end
end

-- Shots at that part until the dummy is dead, up to `most`. Returns how many it took, or nil.
local function shotsToKill(model: Model, partName: string, most: number): number?
	local humanoid = model:FindFirstChildOfClass("Humanoid") :: Humanoid
	for shot = 1, most do
		local part = model:FindFirstChild(partName)
		if not (part and part:IsA("BasePart")) then
			return nil
		end
		camera.CFrame = CFrame.lookAt(camera.CFrame.Position, part.Position)
		frames(3)
		hook:Invoke("trigger", true)
		frames(2)
		hook:Invoke("trigger", false)
		task.wait(PAUSE)
		if humanoid.Health <= 0 then
			return shot
		end
	end
	return nil
end

local report = {}
local function check(what: string, got: any, want: any)
	table.insert(report, `{if got == want then "ok" else "WRONG"}: {what}: {got} (should be {want})`)
end

hook:Invoke("equip", "primary")
task.wait(1)
check("rifle shots to the head, no armor", shotsToKill(dummy("no armor"), "Head", 3), 1)
check("rifle shots to the head, heavy armor", shotsToKill(dummy("heavy"), "Head", 3), 1)
check("rifle shots to the body, heavy armor", shotsToKill(dummy("heavy"), "UpperTorso", 8), 4)

hook:Invoke("equip", "secondary")
task.wait(0.8)
check("pistol shots to the head, heavy armor", shotsToKill(dummy("heavy"), "Head", 5), 2)

local before = hook:Invoke("state")
hook:Invoke("reload")
task.wait(2)
local after = hook:Invoke("state")
check("pistol magazine after a reload", after.magazine, 12)
check("rounds taken from the reserve", before.reserve - after.reserve, 12 - before.magazine)

hook:Invoke("equip", "primary")
return table.concat(report, "\n")

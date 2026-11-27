-- Test: the recon dart. Run on the CLIENT during a playtest, with DevConfig.TestHooks and DevConfig.Dummies
-- on, standing at the spawn with the rifle in hand and a clear view of the dummy with no armor. It throws
-- through ReplicatedStorage.DesertFps.DevWeapon (a test cannot press keys) and watches what the server sends
-- and what it stands in Workspace.Utilities. Takes about 50 seconds: start it in a task.spawn and read the
-- result afterwards. Returns one line per check, each starting "ok" or "WRONG":
--   requests that make no sense, sent straight to the server, throw nothing and cost nothing
--   a throw costs a charge, puts the weapon away for a moment, and the dart sticks where it lands
--   it pulses three times, each pulse outlines the dummy it can see, and then it is gone and so is the outline
--   a dart that is shot is gone at once and pulses no more
--   with no charge left nothing is thrown, by the key or by a request sent straight to the server
--   a used charge comes back
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")
local RunService = game:GetService("RunService")

local Shared = ReplicatedStorage.DesertFps
local hook = Shared:WaitForChild("DevWeapon") :: BindableFunction
local Config = require(Shared.Utility.UtilityConfig)
local WeaponConfig = require(Shared.Weapons.WeaponConfig)
local remotes = Shared.Remotes
local camera = workspace.CurrentCamera
local placed = workspace:WaitForChild("Utilities")
local dart = Config.Utilities.recon

local lines = {}
local function check(right: boolean, what: string)
	table.insert(lines, (if right then "ok     " else "WRONG  ") .. what)
end

local function state(): any
	return hook:Invoke("state")
end

local function charges(): number
	return state().utility.left.recon
end

local function frames(count: number)
	for _ = 1, count do
		RunService.RenderStepped:Wait()
	end
end

local function look(at: Vector3)
	camera.CFrame = CFrame.lookAt(camera.CFrame.Position, at)
	frames(3)
end

-- The dummy with no armor, standing and whole.
local function dummy(): Model
	while true do
		for _, model in workspace.Dummies:GetChildren() do
			local humanoid = model:FindFirstChildOfClass("Humanoid")
			if humanoid and humanoid.Health > 0 and string.find(humanoid.DisplayName, "no armor", 1, true) then
				return model :: Model
			end
		end
		task.wait(0.3)
	end
end

-- What the server says while a test watches.
local pulses, reveals = 0, {} :: { { Model } }
remotes.UtilityPulse.OnClientEvent:Connect(function()
	pulses += 1
end)
remotes.Reveal.OnClientEvent:Connect(function(seen: { Model })
	table.insert(reveals, seen)
end)

-- Waits for a dart to stand in the town, up to `seconds`.
local function landed(seconds: number): Model?
	local till = os.clock() + seconds
	while os.clock() < till do
		local model = placed:FindFirstChildOfClass("Model")
		if model then
			return model
		end
		task.wait(0.05)
	end
	return nil
end

local target = dummy()
local root = target:FindFirstChild("HumanoidRootPart") :: BasePart
-- The paving a few studs this side of the dummy: a dart there sees it.
local ground = root.Position - Vector3.new(0, 3, 0) + (camera.CFrame.Position - root.Position).Unit * 6
hook:Invoke("equip", "primary")
task.wait(1.3)
check(charges() == dart.Charges, `{charges()} darts at the start`)

-- 1. Requests that make no sense.
local use = remotes.UseUtility :: RemoteEvent
local eye, ahead = camera.CFrame.Position, camera.CFrame.LookVector
use:FireServer("recon", eye + Vector3.new(0, 500, 0), ahead) -- from far above the thrower
use:FireServer("recon", eye, ahead * 3) -- not a direction
use:FireServer("no such thing", eye, ahead)
use:FireServer("recon", "here", ahead)
use:FireServer("recon", eye, Vector3.new(0 / 0, 0, 0))
task.wait(dart.FlightMost / 3)
check(
	placed:FindFirstChildOfClass("Model") == nil and charges() == dart.Charges,
	"five requests that make no sense throw nothing and cost nothing"
)

-- 2. A throw.
look(ground)
pulses, reveals = 0, {}
check(hook:Invoke("utility", "recon") == true, "the dart can be thrown")
task.wait(dart.ThrowTime + 0.1)
check(state().ready == false, "the weapon is away right after the throw")
local first = landed(dart.FlightMost)
check(first ~= nil and charges() == dart.Charges - 1, `it stands where it landed, and {charges()} are left`)
task.wait(WeaponConfig.Weapons.rifle.EquipTime)
check(state().ready == true, "the weapon is back once it has been drawn")

-- 3. Its pulses, and who they show.
task.wait(dart.Arm + dart.Every * (dart.Pulses - 1) + 0.3)
local shown = false
for _, character in state().utility.outlined do
	shown = shown or character == target
end
local everyPulse = #reveals == dart.Pulses
for _, seen in reveals do
	everyPulse = everyPulse and table.find(seen, target) ~= nil
end
check(pulses == dart.Pulses, `it pulsed {pulses} times`)
check(everyPulse and shown, `every pulse saw the dummy in front of it ({#reveals} told), and it is outlined`)
task.wait(dart.Linger + dart.Reveal + Config.Look.Fade + 0.4)
check(
	placed:FindFirstChildOfClass("Model") == nil and #state().utility.outlined == 0,
	"then the dart is gone, and the outline with it"
)

-- 4. A dart that is shot.
look(ground)
pulses = 0
hook:Invoke("utility", "recon")
local second = landed(dart.ThrowTime + dart.FlightMost)
task.wait(WeaponConfig.Weapons.rifle.EquipTime + 0.2)
local body = second and second.PrimaryPart
if body then
	look(body.Position)
	hook:Invoke("trigger", true)
	frames(2)
	hook:Invoke("trigger", false)
end
task.wait(0.4)
local before = pulses
check(body ~= nil and placed:FindFirstChildOfClass("Model") == nil, "a shot knocks the dart out")
task.wait(dart.Every * dart.Pulses)
check(pulses == before and pulses < dart.Pulses, `and it pulses no more ({pulses} before it was hit)`)

-- 5. None left.
check(charges() == 0, "no darts are left")
check(hook:Invoke("utility", "recon") == false, "so the key throws nothing")
use:FireServer("recon", camera.CFrame.Position, camera.CFrame.LookVector)
check(landed(1) == nil, "and neither does a request sent straight to the server")

-- 6. A charge comes back.
local till = os.clock() + dart.Recharge + 2
while charges() == 0 and os.clock() < till do
	task.wait(0.5)
end
check(charges() >= 1, `a dart is back within {dart.Recharge} seconds of being thrown`)

return table.concat(lines, "\n")

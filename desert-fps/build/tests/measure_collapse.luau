-- Measures what a building costs as it comes down. Run on the SERVER during a playtest, with
-- DevConfig.TestHooks on (the test reaches the running game through ServerStorage.DesertFps.DevDamage).
-- It destroys every ground-floor wall of the building at once, which brings all of it down, and watches the
-- server while the rubble falls: frame time, the physics step, how many pieces move, how many contacts.
-- Returns the report. With DevConfig.RebuildSeconds set, the building stands again that many seconds later.
local RunService = game:GetService("RunService")
local ServerStorage = game:GetService("ServerStorage")
local Stats = game:GetService("Stats")

local BUILDING = "Watchtower" -- any model in Workspace.Buildings; CourtyardHouse is the largest
local WATCH = 8 -- seconds; rubble lies for DestructionConfig.DebrisLifetime

local hook = ServerStorage.DesertFps.DevDamage :: BindableFunction
local structure = (workspace.Buildings[BUILDING] :: any).Structure

local function standing(): number
	local count = 0
	for _, piece in structure:GetChildren() do
		if (piece:GetAttribute("Health") or 0) > 0 then
			count += 1
		end
	end
	return count
end

local frames = {}
local moving, physics, contacts = 0, 0, 0
local watching = RunService.Heartbeat:Connect(function(step)
	table.insert(frames, step * 1000)
	moving = math.max(moving, Stats.MovingPrimitivesCount)
	physics = math.max(physics, Stats.PhysicsStepTime * 1000)
	contacts = math.max(contacts, Stats.ContactsCount)
end)
task.wait(1)

local before, walls = standing(), 0
for _, piece in structure:GetChildren() do
	local wall = string.sub(piece.Name, 1, 4) == "wall" and piece.WorldPivot.Position.Y < 3
	if wall and (piece:GetAttribute("Health") or 0) > 0 then
		local part = piece:FindFirstChildWhichIsA("BasePart", true)
		if part then
			hook:Invoke(part, 1e6)
			walls += 1
		end
	end
end
task.wait(WATCH)
watching:Disconnect()

local total, slow = 0, 0
for _, frame in frames do
	total += frame
	if frame > 33.4 then
		slow += 1
	end
end
table.sort(frames)
return string.format(
	"%s: %d pieces, %d ground walls destroyed, %d left standing. Server: %.1f ms a frame on average, "
		.. "%.0f ms for the slowest in a hundred, %.0f ms the worst, %d frames over 33 ms. "
		.. "At the peak: %d pieces moving, %d contacts, %.1f ms physics step.",
	BUILDING,
	before,
	walls,
	standing(),
	total / #frames,
	frames[math.ceil(#frames * 0.99)],
	frames[#frames],
	slow,
	moving,
	contacts,
	physics
)

-- Measures what the town costs to draw from fixed viewpoints. Run on the CLIENT during a playtest.
-- It stands the player at each viewpoint, turns the camera, waits for the picture to settle and reads the
-- engine's own counters: draw calls, triangles on screen, the processor time spent on drawing, frames a second.
-- Set the graphics level first (Studio settings, Rendering, Quality Level): on Automatic a slow machine drops
-- to level 1 and the numbers mean little. Studio caps the frame rate at 60.
-- Takes about half a minute. Returns the report.
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")
local Stats = game:GetService("Stats")

local SETTLE, SAMPLE = 3, 2 -- seconds

-- { what, where the player stands, what the camera looks at }
local VIEWS = {
	{ "spawn, looking south to the market", Vector3.new(-704, 4, -52), Vector3.new(-704, 6, 40) },
	{ "market middle, looking west", Vector3.new(-704, 4, -4), Vector3.new(-860, 6, -4) },
	{ "market middle, looking north", Vector3.new(-704, 4, -4), Vector3.new(-704, 6, -160) },
	{ "watchtower roof, looking across the town", Vector3.new(-832, 42, -124), Vector3.new(-600, 0, 100) },
	{ "south-east street, looking north-west", Vector3.new(-556, 4, 140), Vector3.new(-860, 6, -160) },
	{ "gate street, looking north", Vector3.new(-792, 4, 140), Vector3.new(-792, 6, -160) },
	{ "sky only", Vector3.new(-704, 4, -4), Vector3.new(-704, 500, -5) },
}

local camera = workspace.CurrentCamera
local character = Players.LocalPlayer.Character
local root = character.HumanoidRootPart

local function sample(): string
	local frames, seconds, worst = 0, 0, 0
	local cpu, draws, triangles = 0, 0, 0
	while seconds < SAMPLE do
		local step = RunService.RenderStepped:Wait()
		frames += 1
		seconds += step
		worst = math.max(worst, step)
		cpu += Stats.RenderCPUFrameTime
		draws += Stats.SceneDrawcallCount
		triangles += Stats.SceneTriangleCount
	end
	return string.format(
		"%d draw calls, %d triangles, %.1f ms of processor time drawing, %.0f frames a second (worst frame %.0f ms)",
		draws / frames,
		triangles / frames,
		cpu / frames * 1000,
		frames / seconds,
		worst * 1000
	)
end

local report = {}
root.Anchored = true
for _, view in VIEWS do
	character:PivotTo(CFrame.new(view[2]))
	-- After the camera scripts, so the weapon's first-person camera does not turn it back.
	RunService:BindToRenderStep("MeasureLook", Enum.RenderPriority.Last.Value + 1, function()
		camera.CFrame = CFrame.lookAt(camera.CFrame.Position, view[3])
	end)
	task.wait(SETTLE)
	table.insert(report, `{view[1]}: {sample()}`)
	RunService:UnbindFromRenderStep("MeasureLook")
end
root.Anchored = false

return table.concat(report, "\n")

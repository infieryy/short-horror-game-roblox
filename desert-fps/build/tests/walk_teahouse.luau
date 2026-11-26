-- Walks bots through the tea house: in at each door, up both flights of stairs, out onto both terraces.
-- Run on the SERVER during a playtest (Run mode is enough), after 07_build_teahouse.luau. It takes about
-- 25 seconds; the result lands in Workspace's "TeaHouseWalk" attribute as JSON, one line per route.
-- Waypoints are in the building recipe's own measure: studs east, north and up from its north-west corner.
local HttpService = game:GetService("HttpService")
local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local ROUTES = {
	{ name = "front door to the atrium", path = { { 12, -40, 0 }, { 12, -28, 0 }, { 12, -20, 0 }, { 12, -12, 0 } } },
	{ name = "inside stairs to the gallery", path = { { 12, -12, 0 }, { 5.8, -12, 0 }, { 5.8, -5, 0 }, { 8.3, -2.5, 0 },
		{ 16.6, -2.5, 12 }, { 19, -4, 12 } } },
	{ name = "gallery to the porch roof", path = { { 19, -4, 12 }, { 20, -17.8, 12 }, { 12, -17.8, 12 }, { 12, -22, 12 },
		{ 12, -28, 12 } } },
	{ name = "outside stairs to the wing roof", path = { { 26, -37, 0 }, { 30, -33, 0 }, { 30, -23.4, 12 }, { 28, -18, 12 } } },
	{ name = "wing roof into the gallery", path = { { 28, -18, 12 }, { 27, -12, 12 }, { 22, -12, 12 }, { 19, -12, 12 } } },
	{ name = "wing door to the atrium", path = { { 38, -12, 0 }, { 28, -12, 0 }, { 20, -12, 0 }, { 12, -12, 0 } } },
}
local BOT_GROUP = "RouteBots"
local REACH, HEIGHT, STEP_TIMEOUT = 1.5, 2.5, 12

local house = workspace.Buildings.TeaHouse
local origin = house:GetAttribute("Origin") :: CFrame

local function world(point: { number }): Vector3
	return (origin * CFrame.new(point[1], point[3], -point[2])).Position
end

local function walk(route): string
	local bot = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R15)
	bot.Name = "RouteBot"
	for _, part in bot:GetDescendants() do
		if part:IsA("BasePart") then
			part.CollisionGroup = BOT_GROUP
		end
	end
	bot:PivotTo(CFrame.new(world(route.path[1]) + Vector3.new(0, 4, 0)))
	bot.Parent = workspace
	local humanoid = bot:FindFirstChildOfClass("Humanoid") :: Humanoid
	local root = bot:WaitForChild("HumanoidRootPart") :: BasePart
	task.wait(1.5)

	local started, status = time(), "ok"
	for i = 2, #route.path do
		local target = world(route.path[i])
		local stepStarted = time()
		while true do
			humanoid:MoveTo(target)
			RunService.Heartbeat:Wait()
			local feet = root.Position.Y - root.Size.Y / 2 - humanoid.HipHeight
			local flat = Vector3.new(root.Position.X - target.X, 0, root.Position.Z - target.Z).Magnitude
			if flat < REACH and math.abs(feet - target.Y) < HEIGHT then
				break
			end
			if time() - stepStarted > STEP_TIMEOUT then
				status = `stuck before point {i} of {#route.path}, feet at {math.round(feet * 10) / 10}`
				break
			end
		end
		if status ~= "ok" then
			break
		end
	end
	bot:Destroy()
	return `{route.name}: {status} ({math.round((time() - started) * 10) / 10} s)`
end

workspace:SetAttribute("TeaHouseWalk", nil)
task.spawn(function()
	if not PhysicsService:IsCollisionGroupRegistered(BOT_GROUP) then
		PhysicsService:RegisterCollisionGroup(BOT_GROUP)
	end
	PhysicsService:CollisionGroupSetCollidable(BOT_GROUP, BOT_GROUP, false)
	local lines, pending = table.create(#ROUTES), #ROUTES
	for index, route in ROUTES do
		task.spawn(function()
			local ok, result = pcall(walk, route)
			lines[index] = if ok then result else `{route.name}: error {result}`
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait(0.25)
	end
	workspace:SetAttribute("TeaHouseWalk", HttpService:JSONEncode(lines))
end)
return "started"

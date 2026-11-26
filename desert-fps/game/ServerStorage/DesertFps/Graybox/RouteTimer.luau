--!strict
-- Walks bots along the planner's own routes through a built graybox and times them,
-- to check the planner's estimates (plan/routes.py exports the routes).
-- Server only; call during a playtest.

local PhysicsService = game:GetService("PhysicsService")
local Players = game:GetService("Players")
local RunService = game:GetService("RunService")

local GrayboxBuilder = require(script.Parent.GrayboxBuilder)

local RouteTimer = {}

export type Route = {
	name: string,
	from: string,
	plan_s: number,
	path: { { number } }, -- { layer, row, column } per node
}

export type Result = {
	name: string,
	status: string,
	plan: number,
	seconds: number?,
	studs: number?,
}

local BOT_GROUP = "RouteBots"
local REACH = 1.5 -- studs from a node, measured flat, that counts as reaching it
local FEET_TOLERANCE = 2
local STEP_TIMEOUT = 15

local function makeBot(position: Vector3): (Model, Humanoid, BasePart)
	local bot = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R15)
	bot.Name = "RouteBot"
	for _, part in bot:GetDescendants() do
		if part:IsA("BasePart") then
			part.CollisionGroup = BOT_GROUP
		end
	end
	bot:PivotTo(CFrame.new(position + Vector3.new(0, 4, 0)))
	bot.Parent = workspace
	local humanoid = bot:FindFirstChildOfClass("Humanoid") :: Humanoid
	local root = bot:WaitForChild("HumanoidRootPart") :: BasePart
	return bot, humanoid, root
end

local function walk(model: Model, route: Route): Result
	local story = model:GetAttribute("StoryStuds") :: number
	local function nodePosition(node: { number }): Vector3
		return GrayboxBuilder.cellToWorld(model, node[2], node[3], node[1] * story)
	end

	local result: Result = { name = route.name, status = "ok", plan = route.plan_s }
	local bot, humanoid, root = makeBot(nodePosition(route.path[1]))
	task.wait(1.5) -- let the bot land and settle

	local onStairs = RaycastParams.new()
	onStairs.FilterType = Enum.RaycastFilterType.Exclude
	onStairs.FilterDescendantsInstances = { bot }

	local studs = 0
	local started = time()
	for i = 2, #route.path do
		local target = nodePosition(route.path[i])
		studs += (target - nodePosition(route.path[i - 1])).Magnitude
		-- Halfway up a flight of stairs the feet are between two levels: any height from the node before
		-- to the node after counts.
		local low, high = target.Y, target.Y
		for _, near in { route.path[i - 1], route.path[i + 1] } do
			local y = nodePosition(near).Y
			low, high = math.min(low, y), math.max(high, y)
		end
		local stepStarted = time()
		while true do
			humanoid:MoveTo(target)
			RunService.Heartbeat:Wait()
			local feet = root.Position.Y - root.Size.Y / 2 - humanoid.HipHeight
			local flat = Vector3.new(root.Position.X - target.X, 0, root.Position.Z - target.Z).Magnitude
			if flat < REACH and feet > low - FEET_TOLERANCE and feet < high + FEET_TOLERANCE then
				break
			end
			-- A route that only crosses a stairs cell is up on the flight at this point.
			if flat < REACH then
				local under = workspace:Raycast(root.Position, Vector3.new(0, -8, 0), onStairs)
				local standsOn = under and under.Instance
				-- a graybox wedge is called Stairs; a kit flight is a mesh inside a model called stairs
				if standsOn and (standsOn.Name == "Stairs" or (standsOn.Parent :: Instance).Name == "stairs") then
					break
				end
			end
			if time() - stepStarted > STEP_TIMEOUT then
				local node = route.path[i]
				result.status = `stuck before node {i} of {#route.path} (layer {node[1]}, row {node[2]}, col {node[3]})`
				break
			end
		end
		if result.status ~= "ok" then
			break
		end
	end

	result.seconds = math.round((time() - started) * 100) / 100
	result.studs = math.round(studs)
	bot:Destroy()
	return result
end

-- Runs every route at once (bots pass through each other) and returns when all have finished.
function RouteTimer.run(model: Model, routes: { Route }): { Result }
	if not PhysicsService:IsCollisionGroupRegistered(BOT_GROUP) then
		PhysicsService:RegisterCollisionGroup(BOT_GROUP)
	end
	PhysicsService:CollisionGroupSetCollidable(BOT_GROUP, BOT_GROUP, false)

	local results: { Result } = table.create(#routes)
	local pending = #routes
	for index, route in routes do
		task.spawn(function()
			local ok, outcome = pcall(walk, model, route)
			results[index] = if ok
				then outcome
				else { name = route.name, status = "error: " .. tostring(outcome), plan = route.plan_s }
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait(0.25)
	end
	return results
end

return RouteTimer

-- Walks a bot up every flight of stairs in the town and onto each roof it should reach.
-- Run on the SERVER during a playtest (Run mode is enough); it takes about 15 seconds.
-- Returns one line per flight that failed, and how many passed.
-- (The route timing test cannot do this: it walks straight from cell to cell, and a flight of stairs
-- can only be entered from its low end.)
local Players = game:GetService("Players")

local STORY = 12
local failures, passed, pending = {}, 0, 0

local function feet(bot: Model): number
	local root = bot.HumanoidRootPart
	return root.Position.Y - root.Size.Y / 2 - bot.Humanoid.HipHeight
end

-- Walks to a point (given in the flight's own space); true if the bot gets there at about that height.
local function walk(bot: Model, pivot: CFrame, point: Vector3, seconds: number): boolean
	local target = pivot * point
	local deadline = time() + seconds
	while time() < deadline do
		bot.Humanoid:MoveTo(target)
		task.wait(0.1)
		local at = bot.HumanoidRootPart.Position
		local flat = Vector3.new(at.X - target.X, 0, at.Z - target.Z).Magnitude
		if flat < 1.5 and math.abs(feet(bot) - target.Y) < 2 then
			return true
		end
	end
	return false
end

for _, district in workspace.Map:GetChildren() do
	local stairs = district:FindFirstChild("Stairs")
	for _, flight in if stairs then stairs:GetChildren() else {} do
		pending += 1
		task.spawn(function()
			local pivot = flight.WorldPivot -- foot of the flight in the middle of its cell; it climbs towards its -Z
			local name = `{district.Name} stairs at {math.round(pivot.X)}, {math.round(pivot.Z)}`
			-- which neighbouring cells have a one-story roof: straight ahead, left and right
			local roofs = {}
			for label, offset in { ahead = Vector3.new(0, 0, -8), left = Vector3.new(-8, 0, 0), right = Vector3.new(8, 0, 0) } do
				local hit = workspace:Raycast(pivot * (offset + Vector3.new(0, 40, 0)), Vector3.new(0, -40, 0))
				if hit and math.abs(hit.Position.Y - pivot.Y - STORY) < 1.5 then
					roofs[label] = offset
				end
			end
			for label, offset in roofs do
				local bot = Players:CreateHumanoidModelFromDescription(Instance.new("HumanoidDescription"), Enum.HumanoidRigType.R15)
				for _, part in bot:GetDescendants() do
					if part:IsA("BasePart") then
						part.CollisionGroup = "RouteBots"
					end
				end
				bot:PivotTo(pivot * CFrame.new(0, 4, 3.5)) -- on the lowest steps
				bot.Parent = workspace
				task.wait(1)
				local ok = walk(bot, pivot, Vector3.new(0, STORY, -3.5), 6)
				if ok and label ~= "ahead" then
					ok = walk(bot, pivot, Vector3.new(offset.X * 0.45, STORY, -3.5), 3) -- along the top step
				end
				ok = ok and walk(bot, pivot, offset + Vector3.new(0, STORY, if label == "ahead" then 0 else -3.5), 4)
				if ok then
					passed += 1
				else
					table.insert(failures, `{name}: no way onto the roof {label}`)
				end
				bot:Destroy()
			end
			pending -= 1
		end)
	end
end
while pending > 0 do
	task.wait(0.25)
end
return { passed = passed, failures = failures }

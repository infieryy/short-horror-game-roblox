-- Walks bots along the planner's routes in every zone of the built town and times them.
-- Run on the SERVER during a playtest (Run mode is enough). It takes about 35 seconds; the summary lands
-- in Workspace's "RouteSummary" attribute as JSON: per zone, how many routes passed, the ones that did not,
-- and the worst gap between the planner's time and the bot's.
-- A route that enters a stairs cell from the side fails here: the bots walk straight from cell to cell and a
-- flight can only be entered from its low end. tests/climb_stairs.luau covers the stairs properly.
local HttpService = game:GetService("HttpService")
local ServerStorage = game:GetService("ServerStorage")

local RouteTimer = require(ServerStorage.DesertFps.Graybox.RouteTimer)
local RouteData = require(ServerStorage.DesertFps.Plan.RouteData)

workspace:SetAttribute("RouteSummary", nil)
task.spawn(function()
	local summary, pending = {}, 0
	for key, routes in RouteData.zones do
		pending += 1
		task.spawn(function()
			local passed, failures, worst = 0, {}, 0
			for _, result in RouteTimer.run(workspace.Map.Zones[key], routes) do
				if result.status == "ok" then
					passed += 1
					worst = math.max(worst, math.abs(result.seconds - result.plan) / result.plan)
				else
					table.insert(failures, `{result.name}: {result.status}`)
				end
			end
			summary[key] = { passed = passed, of = #routes, worstPercent = math.round(worst * 1000) / 10, failures = failures }
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait(0.25)
	end
	workspace:SetAttribute("RouteSummary", HttpService:JSONEncode(summary))
end)
return "started"

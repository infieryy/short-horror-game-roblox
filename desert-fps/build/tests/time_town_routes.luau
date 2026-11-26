-- Walks bots along the planner's routes in every arena of the compact town's graybox and times them.
-- Run on the SERVER during a playtest (Run mode is enough), after 09_graybox_town.luau. It takes about
-- 40 seconds; the summary lands in Workspace's "TownRouteSummary" attribute as JSON: per arena, how many
-- routes passed, the ones that did not, the worst gap between the planner's time and the bot's, and how far
-- apart the two teams' runs to the meet point were (the town is mirrored, so that should be next to nothing).
local HttpService = game:GetService("HttpService")
local ServerStorage = game:GetService("ServerStorage")

local RouteTimer = require(ServerStorage.DesertFps.Graybox.RouteTimer)
local RouteData = require(ServerStorage.DesertFps.Plan.RouteData)

workspace:SetAttribute("TownRouteSummary", nil)
task.spawn(function()
	local summary, pending = {}, 0
	for key, routes in RouteData.towns.town do
		pending += 1
		task.spawn(function()
			local passed, failures, worst = 0, {}, 0
			local meet = {}
			for _, result in RouteTimer.run(workspace.Graybox_town, routes) do
				if result.status == "ok" then
					passed += 1
					worst = math.max(worst, math.abs(result.seconds - result.plan) / result.plan)
					if string.find(result.name, "to meet point", 1, true) then
						table.insert(meet, result.seconds)
					end
				else
					table.insert(failures, `{result.name}: {result.status}`)
				end
			end
			summary[key] = {
				passed = passed,
				of = #routes,
				worstPercent = math.round(worst * 1000) / 10,
				meetSeconds = meet,
				failures = failures,
			}
			pending -= 1
		end)
	end
	while pending > 0 do
		task.wait(0.25)
	end
	workspace:SetAttribute("TownRouteSummary", HttpService:JSONEncode(summary))
end)
return "started"

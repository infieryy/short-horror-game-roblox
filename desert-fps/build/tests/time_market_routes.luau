-- Walks bots along the planner's Market Square routes and times them.
-- Run on the SERVER during a playtest (Run mode is enough). The result lands in
-- workspace's "RouteTiming" attribute as JSON when every bot has finished (about 25 s).
local HttpService = game:GetService("HttpService")
local ServerStorage = game:GetService("ServerStorage")

local RouteTimer = require(ServerStorage.DesertFps.Graybox.RouteTimer)
local RouteData = require(ServerStorage.DesertFps.Plan.RouteData)

workspace:SetAttribute("RouteTiming", nil)
task.spawn(function()
	local results = RouteTimer.run(workspace:WaitForChild("Graybox_market"), RouteData.zones.market)
	workspace:SetAttribute("RouteTiming", HttpService:JSONEncode(results))
end)
return "started"

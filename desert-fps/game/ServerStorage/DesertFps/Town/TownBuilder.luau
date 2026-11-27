--!strict
-- Builds the compact town: real buildings where a recipe exists, gray boxes for the rest.
--   Workspace.Graybox_town        the gray-box town, bare ground where the real buildings stand
--   Workspace.Buildings.<Name>    the real buildings (see Buildings/BuildingBuilder)
-- Both use the plan's grid, so the route tests walk straight through the real buildings.

local DesertFps = script.Parent.Parent
local BuildingBuilder = require(DesertFps.Buildings.BuildingBuilder)
local BuildingData = require(DesertFps.Buildings.BuildingData)
local GrayboxBuilder = require(DesertFps.Graybox.GrayboxBuilder)
local PlanData = require(DesertFps.Plan.PlanData)
local Config = require(script.Parent.TownConfig)

local TownBuilder = {}

-- Where a plan cell's north-west corner is, at street level.
function TownBuilder.cellCorner(row: number, column: number): CFrame
	local cell = PlanData.cell_studs
	local half = #PlanData.towns.town.grid * cell / 2
	return Config.Middle * CFrame.new(column * cell - half, 0, row * cell - half)
end

-- Builds (or rebuilds) the whole town. Returns how many pieces each real building took.
function TownBuilder.build(): { [string]: number }
	local blank = {}
	for _, entry in Config.Buildings do
		table.insert(blank, { entry.Row, entry.Column, entry.Row + entry.Rows - 1, entry.Column + entry.Columns - 1 })
	end
	GrayboxBuilder.build("town", workspace, Config.Middle, blank)

	local buildings = workspace:FindFirstChild("Buildings")
	if not buildings then
		buildings = Instance.new("Folder")
		buildings.Name = "Buildings"
		buildings.Parent = workspace
	end
	local pieces: { [string]: number } = {}
	for _, entry in Config.Buildings do
		local data = BuildingData[entry.Recipe]
		local old = buildings:FindFirstChild(data.title or entry.Recipe)
		if old then
			old:Destroy()
		end
		local origin = TownBuilder.cellCorner(entry.Row, entry.Column) * CFrame.new(0, Config.Lift, 0)
		local _, counts = BuildingBuilder.build(entry.Recipe, origin, buildings)
		local total = 0
		for _, n in counts do
			total += n
		end
		pieces[entry.Recipe] = total
	end
	return pieces
end

return TownBuilder

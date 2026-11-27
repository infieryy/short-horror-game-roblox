--!strict
-- Builds the compact town: real buildings where a recipe exists, gray boxes for the rest.
--   Workspace.Graybox_town        the gray-box town, bare ground where the real buildings stand
--   Workspace.Buildings.<Name>    the real buildings (see Buildings/BuildingBuilder)
--   Workspace.TownGround          flagstone paving on every street, yard and unbuilt room cell
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

-- Pieces placed between two yields, so Studio stays responsive.
local BATCH = 200

-- Lays a flagstone piece on every cell that is not under a solid box and not paved by a real building.
-- Each one is turned a quarter, half or three quarters round, always the same for the same cell, so the
-- one painted tile does not read as a pattern.
local function pave(blank: { { number } }): number
	local settings = Config.Paving
	local old = workspace:FindFirstChild(settings.Folder)
	if old then
		old:Destroy()
	end
	local ground = Instance.new("Folder")
	ground.Name = settings.Folder

	local template = (DesertFps :: any).Meshes[settings.Piece].Whole :: BasePart
	local offset = CFrame.new(template:GetAttribute("Offset") :: Vector3)
	local cell = PlanData.cell_studs
	local laid = 0
	for r, row: string in PlanData.towns.town.grid do
		for c = 1, #row do
			local row0, column0 = r - 1, c - 1
			if tonumber(string.sub(row, c, c)) then
				continue -- a solid building stands here
			end
			local built = false
			for _, rect in blank do
				if row0 >= rect[1] and row0 <= rect[3] and column0 >= rect[2] and column0 <= rect[4] then
					built = true
					break
				end
			end
			if built then
				continue
			end
			local part = template:Clone()
			part.Name = settings.Piece
			part.CastShadow = false
			local quarter = (row0 * 7919 + column0 * 104729) % 4
			part.CFrame = TownBuilder.cellCorner(row0, column0)
				* CFrame.new(cell / 2, Config.Lift + settings.Drop, cell / 2)
				* CFrame.Angles(0, quarter * math.pi / 2, 0)
				* offset
			part.Parent = ground
			laid += 1
			if laid % BATCH == 0 then
				task.wait()
			end
		end
	end
	ground.Parent = workspace
	return laid
end

-- Builds (or rebuilds) the whole town. Returns how many pieces each real building took, and the paving.
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
	pieces.paving = pave(blank)
	return pieces
end

return TownBuilder

--!strict
-- Builds the compact town from its recipes. Studio, in edit mode.
--   Workspace.Buildings.<Name>    every building, the street dressing and the town wall (Buildings/BuildingBuilder)
--   Workspace.TownGround          paving on every street and yard, sand against the walls
--   Workspace.TownEdge            unseen walls behind the town wall, so nobody leaves through a hole in it
--   Workspace.Graybox_town        only its floor slab is left: the route tests measure from it
-- What stands where is TownData (assets/buildings/town.py writes it from the plan); every recipe uses the
-- plan's grid, so the route tests walk straight through the real town.

local DesertFps = script.Parent.Parent
local BuildingBuilder = require(DesertFps.Buildings.BuildingBuilder)
local BuildingData = require(DesertFps.Buildings.BuildingData)
local GrayboxBuilder = require(DesertFps.Graybox.GrayboxBuilder)
local PlanData = require(DesertFps.Plan.PlanData)
local Config = require(script.Parent.TownConfig)
local TownData = require(script.Parent.TownData)

local TownBuilder = {}

type Entry = { recipe: string, row: number, column: number, rows: number, columns: number, paves: boolean? }

-- Where a plan cell's north-west corner is, at street level.
function TownBuilder.cellCorner(row: number, column: number): CFrame
	local cell = PlanData.cell_studs
	local half = #PlanData.towns.town.grid * cell / 2
	return Config.Middle * CFrame.new(column * cell - half, 0, row * cell - half)
end

-- Pieces placed between two yields, so Studio stays responsive.
local BATCH = 200

local SIDES = { { dr = -1, dc = 0 }, { dr = 1, dc = 0 }, { dr = 0, dc = -1 }, { dr = 0, dc = 1 } }
local ROOMS = "idWpqQu"

local function fresh(name: string): Folder
	local old = workspace:FindFirstChild(name)
	if old then
		old:Destroy()
	end
	local folder = Instance.new("Folder")
	folder.Name = name
	return folder
end

-- Paves every cell that no building paves for itself: flagstones in the streets, brick in the Market Square,
-- water in the pool. Each piece is turned a quarter, half or three quarters round, always the same for the
-- same cell, so the painted stones do not read as a pattern. Then banks sand against the foot of some of the
-- walls that face a street, but not where a door opens or goods stand (TownData.clear).
local function pave(): (number, number)
	local settings = Config.Paving
	local ground = fresh(settings.Folder)

	local grid: { string } = PlanData.towns.town.grid
	local cell = PlanData.cell_studs
	local function at(row0: number, column0: number): string
		local row = grid[row0 + 1]
		return if row then string.sub(row, column0 + 1, column0 + 1) else ""
	end
	local paved: { Entry } = {}
	for _, entry: Entry in TownData.buildings do
		if entry.paves then
			table.insert(paved, entry)
		end
	end
	local function built(row0: number, column0: number): boolean
		for _, entry in paved do
			if row0 >= entry.row and row0 < entry.row + entry.rows and column0 >= entry.column and column0 < entry.column + entry.columns then
				return true
			end
		end
		return false
	end
	local clear: { [string]: boolean } = {}
	for _, key in TownData.clear do
		clear[key] = true
	end
	local function lay(piece: string, cf: CFrame)
		local template = (DesertFps :: any).Meshes[piece].Whole :: BasePart
		local part = template:Clone()
		part.Name = piece
		part.CastShadow = false
		part.CFrame = cf * CFrame.new(template:GetAttribute("Offset") :: Vector3)
		part.Parent = ground
	end

	local square = settings.Square.Rect
	local laid, drifts = 0, 0
	for row0 = 0, #grid - 1 do
		for column0 = 0, #grid[1] - 1 do
			local here = at(row0, column0)
			if tonumber(here) or built(row0, column0) then
				continue -- a house or the town wall stands here, or a building that paves itself
			end
			local hash = row0 * 7919 + column0 * 104729
			local inSquare = row0 >= square[1] and row0 <= square[3] and column0 >= square[2] and column0 <= square[4]
			local piece = if here == "v"
				then settings.Pool
				elseif inSquare then settings.Square.Piece
				else settings.Street[hash % #settings.Street + 1]
			local middle = TownBuilder.cellCorner(row0, column0) * CFrame.new(cell / 2, Config.Lift, cell / 2)
			lay(piece, middle * CFrame.new(0, settings.Drop, 0) * CFrame.Angles(0, (hash // 7 % 4) * math.pi / 2, 0))
			laid += 1

			if here == "." then
				for index, side in SIDES do
					local beyond = at(row0 + side.dr, column0 + side.dc)
					-- a blank or windowed wall: a house, the town wall, or a room with no door on this side
					local wall = tonumber(beyond) ~= nil
						or (built(row0 + side.dr, column0 + side.dc) and beyond ~= "d" and string.find(ROOMS, beyond, 1, true) ~= nil)
					if wall and (hash + index * 31) % settings.Sand.OneIn == 0 and not clear[`{row0}:{column0}:{side.dr}:{side.dc}`] then
						local out = settings.Sand.WallOut
						local slide = ((hash // 3 + index) % 5 - 2) * 0.3
						-- the drift's back is to the wall; its front (+Z) looks back into the street
						lay(
							settings.Sand.Piece,
							middle
								* CFrame.new(side.dc * (cell / 2 - out), 0.02, side.dr * (cell / 2 - out))
								* CFrame.Angles(0, math.atan2(-side.dc, -side.dr), 0)
								* CFrame.new(slide, 0, 0)
						)
						drifts += 1
					end
				end
			end
			if laid % BATCH == 0 then
				task.wait()
			end
		end
	end
	ground.Parent = workspace
	return laid, drifts
end

-- Unseen walls round the town, just behind the town wall and higher than anything a player can stand on.
local function edge()
	local settings = Config.Edge
	local folder = fresh(settings.Folder)
	local span = #PlanData.towns.town.grid * PlanData.cell_studs
	local out = span / 2 - settings.Thickness / 2 -- the outer edge of the ring of cells the town wall stands in
	for _, side in SIDES do
		local wall = Instance.new("Part")
		wall.Name = "Edge"
		wall.Anchored = true
		wall.Transparency = 1
		wall.CanQuery = false
		wall.CastShadow = false
		local along = Vector3.new(math.abs(side.dr) * span, settings.Height, math.abs(side.dc) * span)
		wall.Size = along + Vector3.new(math.abs(side.dc), 0, math.abs(side.dr)) * settings.Thickness
		wall.CFrame = Config.Middle * CFrame.new(side.dc * out, settings.Height / 2, side.dr * out)
		wall.Parent = folder
	end
	folder.Parent = workspace
end

-- Builds (or rebuilds) the town. `only` names the recipes to rebuild, leaving the rest standing; left out,
-- everything is rebuilt, with the ground. Returns how many pieces each recipe took.
function TownBuilder.build(only: { string }?): { [string]: number }
	local size = #PlanData.towns.town.grid
	local pieces: { [string]: number } = {}
	if not only then
		-- the gray boxes are gone; the slab under the town stays for the route tests
		GrayboxBuilder.build("town", workspace, Config.Middle, { { 0, 0, size - 1, size - 1 } })
	end

	local buildings = workspace:FindFirstChild(Config.Folder)
	if not buildings then
		buildings = Instance.new("Folder")
		buildings.Name = Config.Folder
		buildings.Parent = workspace
	end
	local wanted: { [string]: boolean } = {}
	for _, entry: Entry in TownData.buildings do
		local data = BuildingData[entry.recipe]
		assert(data, `TownData names a recipe "{entry.recipe}" that is not in BuildingData`)
		wanted[data.title or entry.recipe] = true
		if only and not table.find(only, entry.recipe) then
			continue
		end
		local old = buildings:FindFirstChild(data.title or entry.recipe)
		if old then
			old:Destroy()
		end
		local origin = TownBuilder.cellCorner(entry.row, entry.column) * CFrame.new(0, Config.Lift, 0)
		local _, counts = BuildingBuilder.build(entry.recipe, origin, buildings)
		local total = 0
		for _, n in counts do
			total += n
		end
		pieces[entry.recipe] = total
		task.wait()
	end
	if not only then
		for _, child in buildings:GetChildren() do
			if child:IsA("Model") and not wanted[child.Name] then
				child:Destroy() -- a building the town no longer has
			end
		end
		pieces.paving, pieces.sand = pave()
		edge()

		local spawn = buildings:FindFirstChild("Spawn") or Instance.new("SpawnLocation")
		spawn.Name = "Spawn"
		spawn.Anchored = true
		spawn.Transparency = 1
		spawn.CanCollide = false
		spawn.Neutral = true
		spawn.Duration = 0
		spawn.Size = Vector3.new(6, 0.2, 6)
		local cell = PlanData.cell_studs
		spawn.CFrame = TownBuilder.cellCorner(Config.DevSpawn.Row, Config.DevSpawn.Column) * CFrame.new(cell / 2, 0.3, cell / 2)
		spawn.Parent = buildings
	end
	return pieces
end

return TownBuilder

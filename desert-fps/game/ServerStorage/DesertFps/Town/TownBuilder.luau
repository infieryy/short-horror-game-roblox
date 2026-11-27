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

local SIDES = { { dr = -1, dc = 0 }, { dr = 1, dc = 0 }, { dr = 0, dc = -1 }, { dr = 0, dc = 1 } }
local ROOMS = "idWpqQ"

-- Paves every cell that is not under a solid box and not paved by a real building: flagstones in the
-- streets, brick in the Market Square. Each piece is turned a quarter, half or three quarters round, always
-- the same for the same cell, so the painted stones do not read as a pattern. Then banks sand against the
-- foot of some of the walls that face a street.
local function pave(blank: { { number } }): (number, number)
	local settings = Config.Paving
	local old = workspace:FindFirstChild(settings.Folder)
	if old then
		old:Destroy()
	end
	local ground = Instance.new("Folder")
	ground.Name = settings.Folder

	local grid: { string } = PlanData.towns.town.grid
	local cell = PlanData.cell_studs
	local function at(row0: number, column0: number): string
		local row = grid[row0 + 1]
		return if row then string.sub(row, column0 + 1, column0 + 1) else ""
	end
	local function built(row0: number, column0: number): boolean
		for _, rect in blank do
			if row0 >= rect[1] and row0 <= rect[3] and column0 >= rect[2] and column0 <= rect[4] then
				return true
			end
		end
		return false
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
				continue -- a solid building stands here, or a real one that paves itself
			end
			local hash = row0 * 7919 + column0 * 104729
			local inSquare = row0 >= square[1] and row0 <= square[3] and column0 >= square[2] and column0 <= square[4]
			local piece = if inSquare then settings.Square.Piece else settings.Street[hash % #settings.Street + 1]
			local middle = TownBuilder.cellCorner(row0, column0) * CFrame.new(cell / 2, Config.Lift, cell / 2)
			lay(piece, middle * CFrame.new(0, settings.Drop, 0) * CFrame.Angles(0, (hash // 7 % 4) * math.pi / 2, 0))
			laid += 1

			if here == "." then
				for index, side in SIDES do
					local beyond = at(row0 + side.dr, column0 + side.dc)
					local real = built(row0 + side.dr, column0 + side.dc)
					-- a blank or windowed wall: a gray box, the town wall, or a real building's wall that has no door here
					local wall = tonumber(beyond) ~= nil or (real and beyond ~= "d" and string.find(ROOMS, beyond, 1, true) ~= nil)
					if wall and (hash + index * 31) % settings.Sand.OneIn == 0 then
						local out = if real then settings.Sand.WallOut else 0.02
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
	pieces.paving, pieces.sand = pave(blank)
	return pieces
end

return TownBuilder

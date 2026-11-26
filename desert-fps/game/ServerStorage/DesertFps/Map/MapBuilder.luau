--!strict
-- Builds the town out of kit pieces from the grid plan: Workspace.Map.
--   Map.<district>.<kind>   the pieces, by district ("ring" is the ring road and the town wall)
--   Map.Zones.<zone>        one model per duel zone: where it is, its spawns and its barriers
-- Every piece that can break is stood up through Breakable, so the whole town can be shot down.
-- Which piece stands where is in MapConfig; what the plan's characters mean is in Plan/PlanGrid.

local Config = require(script.Parent.MapConfig)
local DesertFps = script.Parent.Parent
local BreakData = require(DesertFps.Assets.BreakData)
local Breakable = require(DesertFps.Destruction.Breakable)
local PlanData = require(DesertFps.Plan.PlanData)
local PlanGrid = require(DesertFps.Plan.PlanGrid)

local MapBuilder = {}

type Side = { name: string, dr: number, dc: number }
type Edges = { [number]: { [string]: boolean } } -- [story or roof height][edge] = something stands on it
type Ctx = {
	town: PlanGrid.Town,
	cell: number,
	story: number,
	origin: CFrame,
	map: Instance,
	only: { [string]: boolean }?,
	districtNames: { [number]: string },
	folders: { [string]: Instance },
	counts: { [string]: number },
	placed: number,
	walls: Edges,
	parapets: Edges,
}

local SIDES: { Side } = PlanGrid.SIDES
local isRoom, solidStoreys, storeys, edgeKind = PlanGrid.isRoom, PlanGrid.solidStoreys, PlanGrid.storeys, PlanGrid.edgeKind
-- Pieces placed between two yields. Studio stays responsive while the town goes up.
local BATCH = 200

local function at(ctx: Ctx, r: number, c: number): string?
	local row = ctx.town.grid[r + 1]
	return row and row[c + 1]
end

-- Which district a cell belongs to; the town wall and ring road are "ring".
local function districtOf(ctx: Ctx, r: number, c: number): string
	local n, first = PlanData.zone_cells, PlanGrid.RING + 1
	local gr, gc = (r - first) // n, (c - first) // n
	if gr < 0 or gc < 0 or gr > 2 or gc > 2 then
		return "ring"
	end
	return ctx.districtNames[gr * 3 + gc]
end

local function wanted(ctx: Ctx, r: number, c: number): boolean
	return ctx.only == nil or ctx.only[districtOf(ctx, r, c)] == true
end

-- A point in the town: x studs east of its west edge, z studs south of its north edge, y above the street.
local function world(ctx: Ctx, x: number, y: number, z: number): CFrame
	local half = ctx.town.size * ctx.cell / 2
	return ctx.origin * CFrame.new(x - half, y, z - half)
end

local function cellCentre(ctx: Ctx, r: number, c: number, y: number): CFrame
	return world(ctx, (c + 0.5) * ctx.cell, y, (r + 0.5) * ctx.cell)
end

-- Turns a piece so its front (+Z) looks along (dx, dz).
local function facing(dx: number, dz: number): CFrame
	return CFrame.Angles(0, math.atan2(dx, dz), 0)
end

-- The same choice for the same cell on every build.
local function pick(r: number, c: number, salt: number, choices: number): number
	return (r * 7919 + c * 104729 + salt * 31337) % choices
end

local function folderFor(ctx: Ctx, district: string, kind: string): Instance
	local key = district .. "/" .. kind
	local folder = ctx.folders[key]
	if not folder then
		local parent = ctx.map:FindFirstChild(district)
		if not parent then
			parent = Instance.new("Folder")
			parent.Name = district
			parent.Parent = ctx.map
		end
		folder = Instance.new("Folder")
		folder.Name = kind
		folder.Parent = parent
		ctx.folders[key] = folder
	end
	return folder
end

local function count(ctx: Ctx, what: string)
	ctx.counts[what] = (ctx.counts[what] or 0) + 1
	ctx.placed += 1
	if ctx.placed % BATCH == 0 then
		task.wait()
	end
end

-- Stands one kit piece with its origin at `cf`. Returns its mesh part.
local function stand(ctx: Ctx, district: string, kind: string, piece: string, cf: CFrame): BasePart
	local parent = folderFor(ctx, district, kind)
	local part: BasePart
	if BreakData[piece] then
		part = (Breakable.place(piece, cf, parent) :: any).Whole
	else
		local template = (DesertFps :: any).Meshes[piece].Whole
		part = template:Clone()
		part.Name = piece
		part.CFrame = cf * CFrame.new(template:GetAttribute("Offset"))
		part.Parent = parent
	end
	count(ctx, piece)
	return part
end

-- A plain part where the kit has no piece yet.
local function standIn(ctx: Ctx, district: string, kind: string, name: string, size: Vector3, cf: CFrame, color: Color3): Part
	local part = Instance.new("Part")
	part.Name = name
	part.Anchored = true
	part.Size = size
	part.CFrame = cf
	part.Color = color
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part:SetAttribute("StandIn", true)
	part.Parent = folderFor(ctx, district, kind)
	count(ctx, name)
	return part
end

local function edgeKey(r: number, c: number, side: Side): string
	if side.name == "N" then
		return `H:{r}:{c}`
	elseif side.name == "S" then
		return `H:{r + 1}:{c}`
	elseif side.name == "W" then
		return `V:{r}:{c}`
	end
	return `V:{r}:{c + 1}`
end

local function mark(edges: Edges, level: number, key: string)
	local set = edges[level]
	if not set then
		set = {}
		edges[level] = set
	end
	set[key] = true
end

-- A piece one cell wide standing on a cell's edge, front facing out of the cell.
local function onEdge(ctx: Ctx, r: number, c: number, side: Side, y: number, kind: string, piece: string)
	local x, z = (c + 0.5 + side.dc * 0.5) * ctx.cell, (r + 0.5 + side.dr * 0.5) * ctx.cell
	stand(ctx, districtOf(ctx, r, c), kind, piece, world(ctx, x, y, z) * facing(side.dc, side.dr))
end

local function isTownWall(ctx: Ctx, r: number, c: number): boolean
	local last = ctx.town.size - 1
	return r == 0 or c == 0 or r == last or c == last
end

local function buildGround(ctx: Ctx)
	for r = 0, ctx.town.size - 1 do
		for c = 0, ctx.town.size - 1 do
			if wanted(ctx, r, c) and solidStoreys(at(ctx, r, c)) == 0 then
				local turn = CFrame.Angles(0, pick(r, c, 1, 4) * math.pi / 2, 0) -- so the paving does not repeat
				local tile = stand(ctx, districtOf(ctx, r, c), "Ground", "ground", cellCentre(ctx, r, c, -Config.PavingThickness) * turn)
				tile.CastShadow = false -- flat on the ground: nothing to shade, and thousands fewer shadow casters
			end
		end
	end
end

local function buildWalls(ctx: Ctx)
	local W = Config.Wall
	for r = 0, ctx.town.size - 1 do
		for c = 0, ctx.town.size - 1 do
			local ch = at(ctx, r, c)
			if not (ch and wanted(ctx, r, c)) then
				continue
			end
			local height = solidStoreys(ch)
			for index, side in SIDES do
				local other = at(ctx, r + side.dr, c + side.dc)
				if height > 0 then
					-- a solid building shows a wall wherever it stands taller than its neighbour
					for level = solidStoreys(other) + 1, height do
						local piece = W.Upper
						if level == 1 then
							piece = W.Ground
						elseif
							not isTownWall(ctx, r, c)
							and storeys(other) < level
							and pick(r, c, index * 10 + level, W.UpperWindowOneIn) == 0
						then
							piece = W.UpperWindow
						end
						onEdge(ctx, r, c, side, (level - 1) * ctx.story, "Walls", piece)
						mark(ctx.walls, level, edgeKey(r, c, side))
					end
				elseif isRoom(ch) then
					local kind = edgeKind(ch, other)
					local piece = if kind == "wall" then W.Ground elseif kind == "open" then W.Door elseif kind == "window" then W.Window else nil
					if piece then
						onEdge(ctx, r, c, side, 0, "Walls", piece)
						mark(ctx.walls, 1, edgeKey(r, c, side))
					end
				end
			end
		end
	end
end

-- A post wherever pieces along a row and pieces along a column meet at a grid corner.
local function buildPosts(ctx: Ctx, edges: Edges, kind: string, pieceFor: (level: number) -> string, height: (level: number) -> number)
	for level, set in edges do
		for vr = 0, ctx.town.size do
			for vc = 0, ctx.town.size do
				local along = set[`H:{vr}:{vc - 1}`] or set[`H:{vr}:{vc}`]
				local across = set[`V:{vr - 1}:{vc}`] or set[`V:{vr}:{vc}`]
				if along and across then
					local last = ctx.town.size - 1
					local district = districtOf(ctx, math.min(vr, last), math.min(vc, last))
					stand(ctx, district, kind, pieceFor(level), world(ctx, vc * ctx.cell, height(level), vr * ctx.cell))
				end
			end
		end
	end
end

local function buildRoofs(ctx: Ctx)
	for r = 0, ctx.town.size - 1 do
		for c = 0, ctx.town.size - 1 do
			local ch = at(ctx, r, c)
			if not (ch and wanted(ctx, r, c)) then
				continue
			end
			local district = districtOf(ctx, r, c)
			local height = solidStoreys(ch)
			local solid = height > 0
			local ceiling = (Config.Covered :: any)[district]
			if height == 0 and isRoom(ch) then
				height = 1
			elseif height == 0 and ceiling then
				height = ceiling
				local lamp = Config.CoveredLamp
				if r % lamp.Every == 0 and c % lamp.Every == 0 then
					local holder = standIn(ctx, district, "Lamps", "Lamp", Vector3.one, cellCentre(ctx, r, c, ceiling * ctx.story - 2.5), lamp.Color)
					holder.Transparency = 1
					holder.CanCollide = false
					holder.CanQuery = false
					local light = Instance.new("PointLight")
					light.Range, light.Brightness, light.Color = lamp.Range, lamp.Brightness, lamp.Color
					light.Parent = holder
				end
			end
			if height > 0 then
				local slab = stand(ctx, district, "Roofs", "roof", cellCentre(ctx, r, c, height * ctx.story - Config.RoofDrop))
				-- the walls of a solid building already throw its shadow; only roofs over rooms need to
				slab.CastShadow = not solid
			elseif ch == "=" then
				-- a plank bridge runs between the roofs it joins
				local alongX = storeys(at(ctx, r, c - 1)) > 0 or storeys(at(ctx, r, c + 1)) > 0
				local turn = if alongX then CFrame.identity else CFrame.Angles(0, math.pi / 2, 0)
				stand(ctx, district, "Roofs", "plank", cellCentre(ctx, r, c, ctx.story - Config.PlankRise) * turn)
			end
		end
	end
end

-- Parapets stand on the edge of every roof that looks down on its neighbour, except where a ladder
-- or stairs come up.
local function buildParapets(ctx: Ctx)
	for r = 0, ctx.town.size - 1 do
		for c = 0, ctx.town.size - 1 do
			local ch = at(ctx, r, c)
			if not (ch and wanted(ctx, r, c)) then
				continue
			end
			local height = if isRoom(ch) then 1 else solidStoreys(ch)
			for _, side in SIDES do
				local other = at(ctx, r + side.dr, c + side.dc)
				-- The top step of a flight is one stud deep, right at the end of its cell: a parapet that
				-- ends or runs past there would block the step sideways onto the roof. So no parapet where
				-- a stairs cell is next to this cell along the edge, or next to the cell the edge faces.
				local beside = false
				for _, way in { -1, 1 } do
					local dr, dc = way * side.dc, way * side.dr -- one cell along the edge
					beside = beside or at(ctx, r + dr, c + dc) == "s" or at(ctx, r + side.dr + dr, c + side.dc + dc) == "s"
				end
				if height > 0 and storeys(other) < height and other ~= "L" and other ~= "s" and not beside then
					onEdge(ctx, r, c, side, height * ctx.story, "Parapets", (Config.Parapet :: any)[height])
					mark(ctx.parapets, height, edgeKey(r, c, side))
				end
			end
		end
	end
end

local function standLayout(ctx: Ctx, r: number, c: number, layout: { { any } })
	local centre = cellCentre(ctx, r, c, 0)
	for _, entry in layout do
		stand(ctx, districtOf(ctx, r, c), "Props", entry[1], centre * CFrame.new(entry[2]) * CFrame.Angles(0, math.rad(entry[3]), 0))
	end
end

-- Greedy merge of matching cells into rectangles: (first row, first column, last row, last column).
local function rectangles(ctx: Ctx, matches: (r: number, c: number) -> boolean): { { number } }
	local size = ctx.town.size
	local used: { [number]: boolean } = {}
	local rects = {}
	local function free(r: number, c: number): boolean
		return not used[r * size + c] and matches(r, c)
	end
	for r = 0, size - 1 do
		for c = 0, size - 1 do
			if free(r, c) then
				local c1 = c
				while c1 + 1 < size and free(r, c1 + 1) do
					c1 += 1
				end
				local r1 = r
				while r1 + 1 < size do
					local whole = true
					for cc = c, c1 do
						whole = whole and free(r1 + 1, cc)
					end
					if not whole then
						break
					end
					r1 += 1
				end
				for rr = r, r1 do
					for cc = c, c1 do
						used[rr * size + cc] = true
					end
				end
				table.insert(rects, { r, c, r1, c1 })
			end
		end
	end
	return rects
end

-- A ladder cell gets a ladder against every building it touches, as the planner assumes.
local function buildLadder(ctx: Ctx, r: number, c: number)
	local L, district = Config.Ladder, districtOf(ctx, r, c)
	for _, side in SIDES do
		local height = storeys(at(ctx, r + side.dr, c + side.dc))
		if height > 0 then
			local out = ctx.cell / 2 - L.FromWall
			local foot = cellCentre(ctx, r, c, 0) * CFrame.new(side.dc * out, 0, side.dr * out)
			for level = 1, height do
				-- the ladder's back is to the wall
				stand(ctx, district, "Ladders", L.Piece, foot * CFrame.new(0, (level - 1) * ctx.story, 0) * facing(-side.dc, -side.dr))
			end
			-- The ladder piece is only the look; this is what a player climbs.
			local reach = ctx.cell / 2 - 0.5 - L.Truss / 2
			local truss = Instance.new("TrussPart")
			truss.Name = "Climb"
			truss.Anchored = true
			truss.Transparency = 1
			truss.Size = Vector3.new(L.Truss, height * ctx.story, L.Truss)
			truss.CFrame = cellCentre(ctx, r, c, height * ctx.story / 2) * CFrame.new(side.dc * reach, 0, side.dr * reach)
			truss.Parent = folderFor(ctx, district, "Ladders")
		end
	end
end

local function buildProps(ctx: Ctx)
	for r = 0, ctx.town.size - 1 do
		for c = 0, ctx.town.size - 1 do
			local ch = at(ctx, r, c)
			if not (ch and wanted(ctx, r, c)) then
				continue
			end
			local district = districtOf(ctx, r, c)
			if ch == "c" then
				standLayout(ctx, r, c, Config.LowCover[pick(r, c, 2, #Config.LowCover) + 1])
			elseif ch == "C" and (Config.Stalls :: any)[district] then
				-- a stall looks at the middle of its district
				local place = ctx.town.districts[district]
				local dx = place.column + PlanData.zone_cells / 2 - (c + 0.5)
				local dz = place.row + PlanData.zone_cells / 2 - (r + 0.5)
				local look = if math.abs(dx) > math.abs(dz) then facing(math.sign(dx), 0) else facing(0, math.sign(dz))
				stand(ctx, district, "Props", "stall", cellCentre(ctx, r, c, 0) * look)
			elseif ch == "C" or ch == "Q" then
				standLayout(ctx, r, c, Config.HighCover[pick(r, c, 3, #Config.HighCover) + 1])
			elseif ch == "q" then
				standLayout(ctx, r, c, Config.InteriorLowCover[pick(r, c, 4, #Config.InteriorLowCover) + 1])
			elseif ch == "p" or ch == "P" then
				stand(ctx, district, "Props", "pillar", cellCentre(ctx, r, c, 0))
			elseif ch == "k" then
				-- cloths in a line hang along the line; a single one hangs across the street
				local line = at(ctx, r - 1, c) == "k" or at(ctx, r + 1, c) == "k"
				local across = storeys(at(ctx, r, c - 1)) == 0 and storeys(at(ctx, r, c + 1)) == 0
				local turn = if line or (across and at(ctx, r, c - 1) ~= "k" and at(ctx, r, c + 1) ~= "k") then facing(1, 0) else CFrame.identity
				stand(ctx, district, "Props", "cloth", cellCentre(ctx, r, c, 0) * turn)
			elseif ch == "T" then
				local T = Config.Tree
				standIn(ctx, district, "Props", "Tree", T.Trunk, cellCentre(ctx, r, c, T.Trunk.Y / 2), T.TrunkColor)
				local crown = standIn(ctx, district, "Props", "Tree", Vector3.one * T.Crown, cellCentre(ctx, r, c, T.Trunk.Y + T.Crown / 4), T.CrownColor)
				crown.Shape = Enum.PartType.Ball
			elseif ch == "L" then
				buildLadder(ctx, r, c)
			elseif ch == "s" then
				-- A flight is entered from open ground and climbs away from it: towards a roof where it can,
				-- and along the street where the roofs are only to its sides (its top step reaches them both).
				local function open(side: Side): boolean
					local behind = at(ctx, r - side.dr, c - side.dc)
					return behind ~= nil and storeys(behind) == 0 and string.find("cCwPT", behind, 1, true) == nil
				end
				-- Of the ways it could run, it takes the one entered from nearest the middle of its district.
				-- A zone's two halves are each other turned half round, so both teams get the same stairs.
				local place = ctx.town.districts[district]
				local middleR, middleC = place.row + PlanData.zone_cells / 2 - 0.5, place.column + PlanData.zone_cells / 2 - 0.5
				local climb: Side? = nil
				for _, needsRoof in { true, false } do
					local nearest = math.huge
					for _, side in SIDES do
						if open(side) and (not needsRoof or storeys(at(ctx, r + side.dr, c + side.dc)) == 1) then
							local away = math.abs(r - side.dr - middleR) + math.abs(c - side.dc - middleC)
							if away < nearest then
								climb, nearest = side, away
							end
						end
					end
					if climb then
						break
					end
				end
				if climb then
					-- the low end of the piece is its front
					stand(ctx, district, "Stairs", "stairs", cellCentre(ctx, r, c, 0) * facing(-climb.dc, -climb.dr))
				end
			end
		end
	end

	local function middle(rect: { number }, y: number): CFrame
		return world(ctx, (rect[2] + rect[4] + 1) / 2 * ctx.cell, y, (rect[1] + rect[3] + 1) / 2 * ctx.cell)
	end
	for _, rect in rectangles(ctx, function(r, c)
		return at(ctx, r, c) == "w" and wanted(ctx, r, c)
	end) do
		local district = districtOf(ctx, rect[1], rect[2])
		stand(ctx, district, "Props", if (Config.Wells :: any)[district] then Config.Well else Config.Vat, middle(rect, 0))
	end
	for _, rect in rectangles(ctx, function(r, c)
		return at(ctx, r, c) == "v" and wanted(ctx, r, c)
	end) do
		local S = Config.ShallowWater
		local size = Vector3.new((rect[4] - rect[2] + 1) * ctx.cell, S.Height, (rect[3] - rect[1] + 1) * ctx.cell)
		local sheet = standIn(ctx, districtOf(ctx, rect[1], rect[2]), "Water", "ShallowWater", size, middle(rect, S.Height / 2), S.Color)
		sheet.Transparency = S.Transparency
		sheet.CanCollide = false
		sheet.CanQuery = false
		-- TODO: slow players wading through by SlowFactor once movement code exists.
		sheet:SetAttribute("SlowFactor", S.SlowFactor)
	end
end

-- One model per duel zone. Its pivot is the middle of the zone at street level, so a cell of the zone's
-- own plan can be found with GrayboxBuilder.cellToWorld.
local function buildZones(ctx: Ctx)
	local zones = ctx.map:FindFirstChild("Zones")
	if not zones then
		zones = Instance.new("Folder")
		zones.Name = "Zones"
		zones.Parent = ctx.map
	end
	local n = PlanData.zone_cells
	for key, place in ctx.town.districts do
		if not place.zone or (ctx.only and not ctx.only[key]) then
			continue
		end
		local old = (zones :: Instance):FindFirstChild(key)
		if old then
			old:Destroy()
		end
		local model = Instance.new("Model")
		model.Name = key
		model.WorldPivot = world(ctx, (place.column + n / 2) * ctx.cell, 0, (place.row + n / 2) * ctx.cell)
		model:SetAttribute("Zone", key)
		model:SetAttribute("ZoneCells", n)
		model:SetAttribute("CellStuds", ctx.cell)
		model:SetAttribute("StoryStuds", ctx.story)

		local grid = PlanData.zones[key].grid
		local function inZone(r: number, c: number): string
			return string.sub(grid[r - place.row + 1], c - place.column + 1, c - place.column + 1)
		end
		for r = place.row, place.row + n - 1 do
			for c = place.column, place.column + n - 1 do
				local ch = inZone(r, c)
				if ch == "A" or ch == "B" then
					local size = Config.Spawn.Size
					local spawn = Instance.new("SpawnLocation")
					spawn.Name = "Spawn" .. ch
					spawn.Anchored = true
					spawn.Size = size
					spawn.Transparency = 1
					spawn.CanCollide = false
					spawn.CanQuery = false
					spawn.Neutral = true
					spawn.Duration = 0
					spawn:SetAttribute("Team", ch)
					local position = cellCentre(ctx, r, c, size.Y / 2).Position
					local centre = model.WorldPivot.Position
					spawn.CFrame = CFrame.lookAt(position, Vector3.new(centre.X, position.Y, centre.Z))
					spawn.Parent = model
				end
			end
		end
		for _, rect in rectangles(ctx, function(r, c)
			local inside = r >= place.row and r < place.row + n and c >= place.column and c < place.column + n
			return inside and inZone(r, c) == "X"
		end) do
			local barrier = Instance.new("Part")
			barrier.Name = "Barrier"
			barrier.Anchored = true
			barrier.Size = Vector3.new((rect[4] - rect[2] + 1) * ctx.cell, Config.Barrier.Height, (rect[3] - rect[1] + 1) * ctx.cell)
			barrier.CFrame = world(ctx, (rect[2] + rect[4] + 1) / 2 * ctx.cell, Config.Barrier.Height / 2, (rect[1] + rect[3] + 1) / 2 * ctx.cell)
			barrier.Transparency = 1
			barrier.CanCollide = false
			barrier.CanQuery = false
			barrier:SetAttribute("Closed", false)
			barrier.Parent = model
		end
		model.Parent = zones
	end
end

-- Builds the town, or only the districts named in `only` ("ring" is the ring road and town wall).
-- Rebuilding a district replaces it. Returns how many of each piece were placed.
function MapBuilder.build(only: { string }?, parent: Instance?): { [string]: number }
	local container = parent or workspace
	local map = container:FindFirstChild("Map")
	if not map then
		map = Instance.new("Folder")
		map.Name = "Map"
		map.Parent = container
	end
	local town = PlanGrid.town()

	local ctx: Ctx = {
		town = town,
		cell = PlanData.cell_studs,
		story = PlanData.story_studs,
		origin = Config.Origin,
		map = map :: Instance,
		only = nil,
		districtNames = {},
		folders = {},
		counts = {},
		placed = 0,
		walls = {},
		parapets = {},
	}
	local first = PlanGrid.RING + 1
	for key, place in town.districts do
		ctx.districtNames[(place.row - first) // PlanData.zone_cells * 3 + (place.column - first) // PlanData.zone_cells] = key
	end
	if only then
		ctx.only = {}
		for _, name in only do
			(ctx.only :: any)[name] = true
		end
	end
	for _, folder in (map :: Instance):GetChildren() do
		if folder.Name ~= "Zones" and (ctx.only == nil or ctx.only[folder.Name]) then
			folder:Destroy()
		end
	end

	buildGround(ctx)
	buildWalls(ctx)
	buildPosts(ctx, ctx.walls, "Walls", function(level)
		return if level == 1 then Config.Corner.Ground else Config.Corner.Upper
	end, function(level)
		return (level - 1) * ctx.story
	end)
	buildRoofs(ctx)
	buildParapets(ctx)
	buildPosts(ctx, ctx.parapets, "Parapets", function()
		return Config.Parapet.Corner
	end, function(level)
		return level * ctx.story
	end)
	buildProps(ctx)
	buildZones(ctx)
	return ctx.counts
end

return MapBuilder

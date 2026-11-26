--!strict
-- Builds one duel zone from the grid plan as gray boxes.
-- The meaning of every grid character mirrors plan/planner.py; change them together.

local Config = require(script.Parent.GrayboxConfig)
local PlanData = require(script.Parent.Parent.Plan.PlanData)

local GrayboxBuilder = {}

type Style = { Color: Color3, Transparency: number?, CanCollide: boolean? }
type Rect = { r0: number, c0: number, r1: number, c1: number }
type Ctx = {
	grid: { string },
	n: number,
	cell: number,
	story: number,
	origin: CFrame,
	model: Model,
	folders: { [string]: Folder },
	counts: { [string]: number },
}

local ROOM_CELLS = "idWpqQ"
local SIDES = {
	{ name = "N", dr = -1, dc = 0 },
	{ name = "S", dr = 1, dc = 0 },
	{ name = "W", dr = 0, dc = -1 },
	{ name = "E", dr = 0, dc = 1 },
}

local function isRoom(ch: string?): boolean
	return ch ~= nil and string.find(ROOM_CELLS, ch, 1, true) ~= nil
end

local function solidStoreys(ch: string?): number
	if ch == "1" then
		return 1
	elseif ch == "2" then
		return 2
	elseif ch == "3" then
		return 3
	end
	return 0
end

-- Walkable roof height of a cell, in storeys (planner.height).
local function storeys(ch: string?): number
	local solid = solidStoreys(ch)
	if solid > 0 then
		return solid
	end
	if isRoom(ch) or ch == "=" then
		return 1
	end
	return 0
end

-- What stands on the edge between a room cell and its neighbour (planner.edge).
local function edgeKind(room: string, other: string?): string
	if other == nil then
		return "wall"
	elseif isRoom(other) then
		return "none"
	elseif solidStoreys(other) > 0 then
		return "solid" -- the neighbouring building is the wall
	elseif room == "d" then
		return "open"
	elseif room == "W" then
		return "window"
	end
	return "wall"
end

local function cellAt(ctx: Ctx, r: number, c: number): string?
	if r < 0 or c < 0 or r >= ctx.n or c >= ctx.n then
		return nil
	end
	return string.sub(ctx.grid[r + 1], c + 1, c + 1)
end

local function folderFor(ctx: Ctx, kind: string): Folder
	local folder = ctx.folders[kind]
	if not folder then
		folder = Instance.new("Folder")
		folder.Name = kind
		folder.Parent = ctx.model
		ctx.folders[kind] = folder
	end
	return folder
end

-- Zone space: X runs east from the west edge, Z runs south from the north edge, Y is up from the floor top.
local function toWorld(ctx: Ctx, x: number, y: number, z: number): CFrame
	local half = ctx.n * ctx.cell / 2
	return ctx.origin * CFrame.new(x - half, y, z - half)
end

local function place(ctx: Ctx, part: BasePart, kind: string, styleName: string, lo: Vector3, hi: Vector3)
	local style: Style = (Config.Styles :: any)[styleName]
	part.Name = kind
	part.Anchored = true
	part.Size = hi - lo
	part.CFrame = toWorld(ctx, (lo.X + hi.X) / 2, (lo.Y + hi.Y) / 2, (lo.Z + hi.Z) / 2)
	part.Color = style.Color
	part.Transparency = style.Transparency or 0
	part.CanCollide = style.CanCollide ~= false
	part.Material = Enum.Material.SmoothPlastic
	part.TopSurface = Enum.SurfaceType.Smooth
	part.BottomSurface = Enum.SurfaceType.Smooth
	part.Parent = folderFor(ctx, kind)
	ctx.counts[kind] = (ctx.counts[kind] or 0) + 1
end

local function box(ctx: Ctx, kind: string, styleName: string, lo: Vector3, hi: Vector3): Part
	local part = Instance.new("Part")
	place(ctx, part, kind, styleName, lo, hi)
	return part
end

-- A box of a given footprint standing in the middle of a cell.
local function boxInCell(ctx: Ctx, kind: string, styleName: string, r: number, c: number, size: Vector3, baseY: number?): Part
	local cx, cz = (c + 0.5) * ctx.cell, (r + 0.5) * ctx.cell
	local y0 = baseY or 0
	return box(
		ctx,
		kind,
		styleName,
		Vector3.new(cx - size.X / 2, y0, cz - size.Z / 2),
		Vector3.new(cx + size.X / 2, y0 + size.Y, cz + size.Z / 2)
	)
end

-- Greedy merge of matching cells into rectangles, so a building is a few parts, not one per cell.
local function mergeRects(n: number, matches: (r: number, c: number) -> boolean): { Rect }
	local used: { boolean } = table.create(n * n, false)
	local rects: { Rect } = {}
	local function free(r: number, c: number): boolean
		return not used[r * n + c + 1] and matches(r, c)
	end
	for r = 0, n - 1 do
		for c = 0, n - 1 do
			if free(r, c) then
				local c1 = c
				while c1 + 1 < n and free(r, c1 + 1) do
					c1 += 1
				end
				local r1 = r
				while r1 + 1 < n do
					local rowFree = true
					for cc = c, c1 do
						if not free(r1 + 1, cc) then
							rowFree = false
							break
						end
					end
					if not rowFree then
						break
					end
					r1 += 1
				end
				for rr = r, r1 do
					for cc = c, c1 do
						used[rr * n + cc + 1] = true
					end
				end
				table.insert(rects, { r0 = r, c0 = c, r1 = r1, c1 = c1 })
			end
		end
	end
	return rects
end

local function rectBox(ctx: Ctx, kind: string, styleName: string, rect: Rect, y0: number, y1: number): Part
	return box(
		ctx,
		kind,
		styleName,
		Vector3.new(rect.c0 * ctx.cell, y0, rect.r0 * ctx.cell),
		Vector3.new((rect.c1 + 1) * ctx.cell, y1, (rect.r1 + 1) * ctx.cell)
	)
end

local function buildFloor(ctx: Ctx)
	local span = ctx.n * ctx.cell
	box(ctx, "Floor", "Floor", Vector3.new(0, -Config.FloorThickness, 0), Vector3.new(span, 0, span))
end

local function buildSolids(ctx: Ctx)
	for level = 1, 3 do
		local digit = tostring(level)
		local rects = mergeRects(ctx.n, function(r, c)
			return cellAt(ctx, r, c) == digit
		end)
		for _, rect in rects do
			rectBox(ctx, "Building", "Solid" .. digit, rect, 0, level * ctx.story):SetAttribute("Storeys", level)
		end
	end
end

-- One thin wall piece along a cell edge. `along` is the run of the wall, `across` its thickness.
-- An opening (door or window) is cut as a gap between [gap0, gap1] along the run.
local function wallPiece(
	ctx: Ctx,
	alongAxis: string,
	a0: number,
	a1: number,
	t0: number,
	t1: number,
	kind: string,
	mid: number
)
	local top = ctx.story - Config.RoofThickness
	local function piece(name: string, style: string, lo: number, hi: number, y0: number, y1: number, inset: number?): Part?
		if hi - lo < 0.05 or y1 - y0 < 0.05 then
			return nil
		end
		local u0, u1 = t0 + (inset or 0), t1 - (inset or 0)
		if alongAxis == "X" then
			return box(ctx, name, style, Vector3.new(lo, y0, u0), Vector3.new(hi, y1, u1))
		end
		return box(ctx, name, style, Vector3.new(u0, y0, lo), Vector3.new(u1, y1, hi))
	end

	if kind == "wall" then
		piece("Wall", "Wall", a0, a1, 0, top)
	elseif kind == "open" then
		local g0, g1 = mid - Config.Door.Width / 2, mid + Config.Door.Width / 2
		piece("Wall", "Wall", a0, g0, 0, top)
		piece("Wall", "Wall", g1, a1, 0, top)
		piece("Wall", "Wall", g0, g1, Config.Door.Height, top)
	elseif kind == "window" then
		local g0, g1 = mid - Config.Window.Width / 2, mid + Config.Window.Width / 2
		piece("Wall", "Wall", a0, g0, 0, top)
		piece("Wall", "Wall", g1, a1, 0, top)
		piece("Wall", "Wall", g0, g1, 0, Config.Window.Sill)
		piece("Wall", "Wall", g0, g1, Config.Window.Head, top)
		-- The plan lets you see through a window but not walk through it.
		local inset = (t1 - t0 - Config.Window.PaneThickness) / 2
		piece("WindowPane", "WindowPane", g0, g1, Config.Window.Sill, Config.Window.Head, inset)
	end
end

local function buildRooms(ctx: Ctx)
	local roofs = mergeRects(ctx.n, function(r, c)
		return isRoom(cellAt(ctx, r, c))
	end)
	for _, rect in roofs do
		rectBox(ctx, "Roof", "Roof", rect, ctx.story - Config.RoofThickness, ctx.story)
	end

	local t = Config.WallThickness
	local clear = ctx.story - Config.RoofThickness
	for r = 0, ctx.n - 1 do
		for c = 0, ctx.n - 1 do
			local ch = cellAt(ctx, r, c)
			if ch and isRoom(ch) then
				local x0, z0 = c * ctx.cell, r * ctx.cell
				local x1, z1 = x0 + ctx.cell, z0 + ctx.cell
				local kinds: { [string]: string } = {}
				for _, side in SIDES do
					kinds[side.name] = edgeKind(ch, cellAt(ctx, r + side.dr, c + side.dc))
				end
				local function built(side: string): boolean
					return kinds[side] ~= "none" and kinds[side] ~= "solid"
				end
				-- North and south walls run the full cell; east and west walls stop short of them,
				-- so no two wall faces share a plane at the corners.
				local trimN = if built("N") then t else 0
				local trimS = if built("S") then t else 0
				if built("N") then
					wallPiece(ctx, "X", x0, x1, z0, z0 + t, kinds.N, (x0 + x1) / 2)
				end
				if built("S") then
					wallPiece(ctx, "X", x0, x1, z1 - t, z1, kinds.S, (x0 + x1) / 2)
				end
				if built("W") then
					wallPiece(ctx, "Z", z0 + trimN, z1 - trimS, x0, x0 + t, kinds.W, (z0 + z1) / 2)
				end
				if built("E") then
					wallPiece(ctx, "Z", z0 + trimN, z1 - trimS, x1 - t, x1, kinds.E, (z0 + z1) / 2)
				end

				if ch == "p" then
					local size = Config.InteriorPillar
					boxInCell(ctx, "Pillar", "Pillar", r, c, Vector3.new(size.X, clear, size.Z))
				elseif ch == "q" then
					boxInCell(ctx, "LowCover", "LowCover", r, c, Config.InteriorLowCover)
				elseif ch == "Q" then
					boxInCell(ctx, "HighCover", "HighCover", r, c, Config.InteriorHighCover)
				end
			end
		end
	end
end

local function buildStreetProps(ctx: Ctx)
	for r = 0, ctx.n - 1 do
		for c = 0, ctx.n - 1 do
			local ch = cellAt(ctx, r, c)
			if ch == "c" then
				boxInCell(ctx, "LowCover", "LowCover", r, c, Config.LowCover)
			elseif ch == "C" then
				boxInCell(ctx, "HighCover", "HighCover", r, c, Config.HighCover)
			elseif ch == "P" then
				boxInCell(ctx, "Pillar", "Pillar", r, c, Config.Pillar)
			elseif ch == "k" then
				local cloth = Config.Cloth
				boxInCell(
					ctx,
					"Cloth",
					"Cloth",
					r,
					c,
					Vector3.new(ctx.cell, cloth.Height - cloth.Clearance, cloth.Thickness),
					cloth.Clearance
				)
			elseif ch == "T" then
				local tree = Config.Tree
				boxInCell(ctx, "Tree", "TreeTrunk", r, c, tree.Trunk)
				local d = tree.CanopyDiameter
				local canopy = boxInCell(ctx, "Tree", "TreeCanopy", r, c, Vector3.new(d, d, d), tree.Trunk.Y - d / 4)
				canopy.Shape = Enum.PartType.Ball
			end
		end
	end

	for _, rect in mergeRects(ctx.n, function(r, c)
		return cellAt(ctx, r, c) == "w"
	end) do
		rectBox(ctx, "Water", "Water", rect, 0, Config.Water.Height)
	end
	for _, rect in mergeRects(ctx.n, function(r, c)
		return cellAt(ctx, r, c) == "v"
	end) do
		-- TODO: slow players standing in ShallowWater by SlowFactor once movement code exists.
		rectBox(ctx, "ShallowWater", "ShallowWater", rect, 0, Config.ShallowWater.Height):SetAttribute(
			"SlowFactor",
			Config.ShallowWater.SlowFactor
		)
	end
	for _, rect in mergeRects(ctx.n, function(r, c)
		return cellAt(ctx, r, c) == "="
	end) do
		rectBox(ctx, "Plank", "Plank", rect, ctx.story - Config.RoofThickness, ctx.story)
	end
end

-- A ladder cell gets one truss per roof height it borders, standing against that building.
local function buildLadders(ctx: Ctx)
	local w = Config.Ladder.Width
	for r = 0, ctx.n - 1 do
		for c = 0, ctx.n - 1 do
			if cellAt(ctx, r, c) == "L" then
				local seen: { [number]: boolean } = {}
				for _, side in SIDES do
					local h = storeys(cellAt(ctx, r + side.dr, c + side.dc))
					if h > 0 and not seen[h] then
						seen[h] = true
						local cx = (c + 0.5 + side.dc * 0.5) * ctx.cell - side.dc * w / 2
						local cz = (r + 0.5 + side.dr * 0.5) * ctx.cell - side.dr * w / 2
						local truss = Instance.new("TrussPart")
						place(
							ctx,
							truss,
							"Ladder",
							"Ladder",
							Vector3.new(cx - w / 2, 0, cz - w / 2),
							Vector3.new(cx + w / 2, h * ctx.story, cz + w / 2)
						)
						truss:SetAttribute("Storeys", h)
					end
				end
			end
		end
	end
end

-- A stairs cell is a ramp up to the first 1-storey roof it borders.
local function buildStairs(ctx: Ctx)
	for r = 0, ctx.n - 1 do
		for c = 0, ctx.n - 1 do
			if cellAt(ctx, r, c) == "s" then
				for _, side in SIDES do
					if storeys(cellAt(ctx, r + side.dr, c + side.dc)) == 1 then
						local x0, z0 = c * ctx.cell, r * ctx.cell
						local wedge = Instance.new("WedgePart")
						place(
							ctx,
							wedge,
							"Stairs",
							"Stairs",
							Vector3.new(x0, 0, z0),
							Vector3.new(x0 + ctx.cell, ctx.story, z0 + ctx.cell)
						)
						-- A wedge is tallest at its back face (+Z); turn the back toward the roof.
						local toRoof = ctx.origin:VectorToWorldSpace(Vector3.new(side.dc, 0, side.dr))
						wedge.CFrame = CFrame.lookAt(wedge.Position, wedge.Position - toRoof)
						break
					end
				end
			end
		end
	end
end

local function buildBarriers(ctx: Ctx)
	for _, rect in mergeRects(ctx.n, function(r, c)
		return cellAt(ctx, r, c) == "X"
	end) do
		rectBox(ctx, "Barrier", "Barrier", rect, 0, Config.Barrier.Height)
	end
end

local function buildSpawns(ctx: Ctx)
	for r = 0, ctx.n - 1 do
		for c = 0, ctx.n - 1 do
			local ch = cellAt(ctx, r, c)
			if ch == "A" or ch == "B" then
				local cx, cz = (c + 0.5) * ctx.cell, (r + 0.5) * ctx.cell
				local size = Config.Spawn.Size
				local spawn = Instance.new("SpawnLocation")
				place(
					ctx,
					spawn,
					"Spawn" .. ch,
					"Spawn" .. ch,
					Vector3.new(cx - size.X / 2, 0, cz - size.Z / 2),
					Vector3.new(cx + size.X / 2, size.Y, cz + size.Z / 2)
				)
				spawn.Neutral = true
				spawn.Duration = 0
				spawn:SetAttribute("Team", ch)
				-- Face the middle of the zone.
				local centre = toWorld(ctx, ctx.n * ctx.cell / 2, size.Y / 2, ctx.n * ctx.cell / 2).Position
				spawn.CFrame = CFrame.lookAt(spawn.Position, Vector3.new(centre.X, spawn.Position.Y, centre.Z))
			end
		end
	end
end

-- World position of the middle of a cell in a built zone, `height` studs above the floor.
function GrayboxBuilder.cellToWorld(model: Model, r: number, c: number, height: number?): Vector3
	local n = model:GetAttribute("ZoneCells") :: number
	local cell = model:GetAttribute("CellStuds") :: number
	local half = n * cell / 2
	return (model.WorldPivot * CFrame.new((c + 0.5) * cell - half, height or 0, (r + 0.5) * cell - half)).Position
end

-- Builds (or rebuilds) a zone under `parent`. Returns the model and how many parts of each kind it made.
function GrayboxBuilder.build(zoneKey: string, parent: Instance?): (Model, { [string]: number })
	local zone = PlanData.zones[zoneKey]
	assert(zone, `no zone "{zoneKey}" in the plan`)
	local container = parent or workspace

	local name = "Graybox_" .. zoneKey
	local old = container:FindFirstChild(name)
	if old then
		old:Destroy()
	end

	local model = Instance.new("Model")
	model.Name = name
	model.WorldPivot = Config.Origin
	model:SetAttribute("Zone", zoneKey)
	model:SetAttribute("ZoneCells", PlanData.zone_cells)
	model:SetAttribute("CellStuds", PlanData.cell_studs)
	model:SetAttribute("StoryStuds", PlanData.story_studs)

	local ctx: Ctx = {
		grid = zone.grid,
		n = PlanData.zone_cells,
		cell = PlanData.cell_studs,
		story = PlanData.story_studs,
		origin = Config.Origin,
		model = model,
		folders = {},
		counts = {},
	}
	assert(#ctx.grid == ctx.n, `zone "{zoneKey}" has {#ctx.grid} rows, expected {ctx.n}`)

	buildFloor(ctx)
	buildSolids(ctx)
	buildRooms(ctx)
	buildStreetProps(ctx)
	buildLadders(ctx)
	buildStairs(ctx)
	buildBarriers(ctx)
	buildSpawns(ctx)

	model.Parent = container
	return model, ctx.counts
end

return GrayboxBuilder

--!strict
-- What the characters of the grid plan mean, and the whole town as one grid.
-- This mirrors plan/planner.py (height, edge, reserve_block, render_town); change them together.

local PlanData = require(script.Parent.PlanData)

local PlanGrid = {}

export type Grid = { { string } } -- [row][column], both from 1; rows run north to south

PlanGrid.ROOM_CELLS = "idWpqQu" -- "u" is shallow water indoors (plan/town.py)
PlanGrid.SIDES = {
	{ name = "N", dr = -1, dc = 0 },
	{ name = "S", dr = 1, dc = 0 },
	{ name = "W", dr = 0, dc = -1 },
	{ name = "E", dr = 0, dc = 1 },
}
-- Cells of ring road between the town wall and the districts.
PlanGrid.RING = 3

function PlanGrid.isRoom(ch: string?): boolean
	return ch ~= nil and string.find(PlanGrid.ROOM_CELLS, ch, 1, true) ~= nil
end

function PlanGrid.solidStoreys(ch: string?): number
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
function PlanGrid.storeys(ch: string?): number
	local solid = PlanGrid.solidStoreys(ch)
	if solid > 0 then
		return solid
	end
	if PlanGrid.isRoom(ch) or ch == "=" then
		return 1
	end
	return 0
end

-- What stands on the edge between a room cell and its neighbour (planner.edge).
function PlanGrid.edgeKind(room: string, other: string?): string
	if other == nil then
		return "wall"
	elseif PlanGrid.isRoom(other) then
		return "none"
	elseif PlanGrid.solidStoreys(other) > 0 then
		return "solid" -- the neighbouring building is the wall
	elseif room == "d" then
		return "open"
	elseif room == "W" then
		return "window"
	end
	return "wall"
end

local function square(n: number, fill: string): Grid
	local grid: Grid = table.create(n)
	for r = 1, n do
		grid[r] = table.create(n, fill)
	end
	return grid
end

-- Placeholder housing for a district with no duel layout yet (planner.reserve_block).
local function reserveBlock(n: number): Grid
	local grid = square(n, "2")
	for r = 1, n - 2 do
		for c = 1, n - 2 do
			grid[r + 1][c + 1] = if (r // 5 + c // 5) % 2 == 1 then "1" else "2"
		end
	end
	for i = 0, n - 1 do
		for j = 12, 15 do
			grid[i + 1][j + 1] = "."
			grid[j + 1][i + 1] = "."
		end
	end
	for i = 1, n - 2 do
		for _, j in { 5, 22 } do
			grid[i + 1][j + 1] = "."
			grid[j + 1][i + 1] = "."
		end
	end
	return grid
end

export type Town = {
	grid: Grid,
	size: number, -- cells across
	-- every district: its name, whether it is a duel zone, and the row and column (from 0) of its north-west cell
	districts: { [string]: { zone: boolean, row: number, column: number } },
}

-- The whole town as one grid: the town wall, the ring road and the 3 x 3 districts.
-- Spawns and zone barriers are streets here; they belong to the zones, not to the town.
function PlanGrid.town(): Town
	local n, ring = PlanData.zone_cells, PlanGrid.RING
	local size = 3 * n + 2 * (ring + 1)
	local grid = square(size, ".")
	for i = 1, size do
		grid[1][i], grid[size][i], grid[i][1], grid[i][size] = "2", "2", "2", "2"
	end

	local districts = {}
	for key, place in PlanData.town do
		local zone = PlanData.zones[key]
		local row, column = ring + 1 + place[1] * n, ring + 1 + place[2] * n
		local block = if zone then nil else reserveBlock(n)
		for r = 1, n do
			for c = 1, n do
				local ch = if zone then string.sub(zone.grid[r], c, c) else (block :: Grid)[r][c]
				if ch == "A" or ch == "B" or ch == "X" then
					ch = "."
				end
				grid[row + r][column + c] = ch
			end
		end
		districts[key] = { zone = zone ~= nil, row = row, column = column }
	end

	-- the town gate: a gap in the south wall below the Gate district
	local gate = ring + 1 + PlanData.town.gate[2] * n + 12
	for c = gate, gate + 3 do
		grid[size][c + 1] = "."
	end
	return { grid = grid, size = size, districts = districts }
end

return PlanGrid

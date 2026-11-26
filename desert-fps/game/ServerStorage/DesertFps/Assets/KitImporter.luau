--!strict
-- Loads the uploaded kit pieces into ServerStorage.DesertFps.Meshes, where Breakable, the map builder and
-- the weapons pick them up. Studio only, in edit mode (build/04_import_meshes.luau runs it).
--   Meshes.<piece>.Whole, .Low          the whole mesh and its low-detail version
--   Meshes.<piece>.Shards.<shard id>    pieces that break (walls, stairs, props, ...)
--   Meshes.<piece>.Parts.<part id>      pieces that do not break (weapons, the ground)
-- Every mesh gets the piece's texture as a SurfaceAppearance colour map, and an "Offset" attribute:
-- where its centre sits relative to the piece origin. It stops if a mesh is not where its data says.

local DesertFps = script.Parent.Parent
local AssetIds = require(script.Parent.AssetIds)
local BreakData = require(script.Parent.BreakData)
local PartsData = require(script.Parent.PartsData)

local KitImporter = {}

-- Studs a mesh may sit from the centre its data gives.
local TOLERANCE = 0.01
-- Collision of the whole and low-detail mesh, where the default (a rough set of blocks) will not do.
local PRECISE, HULL = Enum.CollisionFidelity.PreciseConvexDecomposition, Enum.CollisionFidelity.Hull
local FIDELITY = {
	wall_door = PRECISE, -- the opening has to stay open
	wall_window = PRECISE,
	wall_upper_window = PRECISE,
	well = PRECISE,
	vat = PRECISE,
	stall = PRECISE,
	awning = PRECISE,
	stairs = HULL, -- one smooth ramp to walk up
}
-- Pieces players pass straight through. Shots still hit them.
-- (A ladder is climbed on the TrussPart the map builder stands with it.)
local WALK_THROUGH = { cloth = true, ladder = true }

local function import(piece: string, ids: { Model: number, Texture: number }, meshes: Instance): { meshes: number, worstOffset: number }
	local fixed = PartsData[piece] ~= nil -- does not break
	local data = BreakData[piece] or PartsData[piece]
	assert(data, `no break or parts data for "{piece}"`)
	local entries = data.chunks or data.parts
	local centres: { [string]: Vector3 } = {}
	for _, entry in entries do
		centres[entry.id] = Vector3.new(entry.center[1], entry.center[2], entry.center[3])
	end

	local model = game:GetObjects(`rbxassetid://{ids.Model}`)[1] :: Model
	local pivot = model:GetPivot()

	local folder = Instance.new("Folder")
	folder.Name = piece
	local group = Instance.new("Folder")
	group.Name = if fixed then "Parts" else "Shards"
	group.Parent = folder

	local worst = 0
	for _, part in model:GetDescendants() do
		if not part:IsA("MeshPart") then
			continue
		end
		local offset = pivot:ToObjectSpace(part.CFrame)
		assert(offset.Rotation:FuzzyEq(CFrame.identity, 1e-4), `{part.Name} arrived turned`)
		part:SetAttribute("Offset", offset.Position)
		part.Anchored = true
		part.CFrame = CFrame.new(offset.Position)

		local appearance = Instance.new("SurfaceAppearance")
		appearance.ColorMap = `rbxassetid://{ids.Texture}`
		appearance.Parent = part

		if part.Name == piece or part.Name == piece .. "_low" then
			part.CollisionFidelity = if fixed then Enum.CollisionFidelity.Box else FIDELITY[piece] or Enum.CollisionFidelity.Default
			part.CanCollide = not WALK_THROUGH[piece]
			part.Name = if part.Name == piece then "Whole" else "Low"
			part.Parent = folder
		else
			local id = part.Name:sub(#piece + 2)
			assert(centres[id], `{part.Name} is not in the data for "{piece}"`)
			worst = math.max(worst, (offset.Position - centres[id]).Magnitude)
			part.CollisionFidelity = if fixed then Enum.CollisionFidelity.Box else HULL
			part.Name = id
			part.Parent = group
		end
	end
	model:Destroy()

	assert(folder:FindFirstChild("Whole") and folder:FindFirstChild("Low"), `"{piece}" has no whole or low mesh`)
	assert(#group:GetChildren() == #entries, `"{piece}": {#group:GetChildren()} meshes for {#entries} data entries`)
	assert(worst <= TOLERANCE, `"{piece}": a mesh sits {worst} studs from its data centre`)

	local old = meshes:FindFirstChild(piece)
	if old then
		old:Destroy()
	end
	folder.Parent = meshes
	return { meshes = #group:GetChildren() + 2, worstOffset = math.round(worst * 1e4) / 1e4 }
end

-- Imports every piece in AssetIds, or only the ones named. A piece that is already there is replaced.
function KitImporter.run(only: { string }?): { [string]: { meshes: number, worstOffset: number } }
	local meshes = DesertFps:FindFirstChild("Meshes")
	if not meshes then
		meshes = Instance.new("Folder")
		meshes.Name = "Meshes"
		meshes.Parent = DesertFps
	end
	local report = {}
	for piece, ids in AssetIds :: { [string]: { Model: number, Texture: number } } do
		if only == nil or table.find(only, piece) then
			report[piece] = import(piece, ids, meshes :: Instance)
			task.wait()
		end
	end
	game:GetService("ChangeHistoryService"):SetWaypoint("Import kit meshes")
	return report
end

return KitImporter

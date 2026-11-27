--!strict
-- Stands a designed building from its recipe. Server or Studio edit mode.
-- A building recipe is a program in assets/buildings/<name>.py that places kit pieces on the grid, story by
-- story, inside and out; build/pack.py packs its piece list as BuildingData. This module only stands the list:
--   <parent>.<Name>.Structure   pieces that break (walls, floors, furniture), one Breakable model each
--   <parent>.<Name>.Dressing    pieces that do not break (paving, rugs, banners, plants)
--   <parent>.<Name>.Lamps       lanterns: the frame, the glowing glass and its light
--   <parent>.<Name>.Fills       soft lights with no lamp to see
-- Positions in the data are studs east, north and up from the building's north-west corner at street level.

local DesertFps = script.Parent.Parent
local BreakData = require(DesertFps.Assets.BreakData)
local Breakable = require(DesertFps.Destruction.Breakable)
local BuildingData = require(script.Parent.BuildingData)
local Config = require(script.Parent.BuildingConfig)

local BuildingBuilder = {}

type Placement = { piece: string, pos: { number }, turn: number, tint: { number }? }

-- Pieces placed between two yields, so Studio stays responsive.
local BATCH = 60

local function folder(name: string, parent: Instance): Folder
	local made = Instance.new("Folder")
	made.Name = name
	made.Parent = parent
	return made
end

local function meshes(piece: string): Instance
	local found = (DesertFps :: any).Meshes:FindFirstChild(piece)
	assert(found, `kit piece "{piece}" is not imported (run build/04_import_meshes.luau)`)
	return found
end

-- A copy of one mesh of a piece, standing where the piece's origin is `cf`.
local function copy(template: BasePart, cf: CFrame, name: string, parent: Instance): BasePart
	local part = template:Clone()
	part.Name = name
	part.CFrame = cf * CFrame.new(template:GetAttribute("Offset") :: Vector3)
	part.Parent = parent
	return part
end

-- A lantern is two meshes: the iron frame, and the glass, which glows and carries the light.
local function standLamp(piece: string, cf: CFrame, parent: Instance)
	local parts = meshes(piece):FindFirstChild("Parts") :: Instance
	local lamp = Instance.new("Model")
	lamp.Name = piece
	local body = copy(parts:FindFirstChild("body") :: BasePart, cf, "Frame", lamp)
	body.CanCollide = false
	local glass = copy(parts:FindFirstChild("glass") :: BasePart, cf, "Glass", lamp)
	glass.CanCollide = false
	glass.CastShadow = false
	local appearance = glass:FindFirstChildOfClass("SurfaceAppearance")
	if appearance then
		appearance:Destroy()
	end
	glass.Material = Enum.Material.Neon
	glass.Color = Config.Lamp.GlassColor
	local light = Instance.new("PointLight")
	light.Color = Config.Lamp.LightColor
	light.Brightness = Config.Lamp.Brightness
	light.Range = Config.Lamp.Range
	light.Shadows = Config.Lamp.Shadows[piece]
	light.Parent = glass
	lamp.PrimaryPart = body
	lamp.Parent = parent
end

-- Builds one building with its north-west corner at `origin` (its -Z is north). Returns the model and
-- how many of each piece went into it.
function BuildingBuilder.build(name: string, origin: CFrame, parent: Instance?): (Model, { [string]: number })
	local data = BuildingData[name]
	assert(data, `no building recipe called "{name}"`)

	local model = Instance.new("Model")
	model.Name = data.title or name
	model:SetAttribute("Building", name)
	model:SetAttribute("Origin", origin)
	local structure, dressing, lamps = folder("Structure", model), folder("Dressing", model), folder("Lamps", model)

	local counts: { [string]: number } = {}
	for index, item: Placement in data.placements do
		local piece = item.piece
		local cf = origin * CFrame.new(item.pos[1], item.pos[3], -item.pos[2]) * CFrame.Angles(0, math.rad(item.turn), 0)
		if Config.Lamp.Pieces[piece] then
			standLamp(piece, cf, lamps)
		elseif BreakData[piece] then
			local tint = item.tint and Color3.fromRGB(item.tint[1], item.tint[2], item.tint[3])
			local placed = Breakable.place(piece, cf, structure, tint)
			if Config.NoShadow[piece] then
				for _, part in placed:GetDescendants() do
					if part:IsA("BasePart") then
						part.CastShadow = false
					end
				end
			end
			local glow = Config.Glow[piece]
			local whole = placed:FindFirstChild("Whole")
			if glow and whole and whole:IsA("BasePart") then
				-- a fire: the light sits in the mesh, so it goes out when the piece breaks
				local ember = Instance.new("Attachment")
				ember.Name = "Glow"
				ember.CFrame = whole.CFrame:ToObjectSpace(cf * CFrame.new(glow.At))
				local light = Instance.new("PointLight")
				light.Color = glow.Color
				light.Brightness = glow.Brightness
				light.Range = glow.Range
				light.Shadows = false
				light.Parent = ember
				ember.Parent = whole
			end
		else
			copy(meshes(piece):FindFirstChild("Whole") :: BasePart, cf, piece, dressing).CastShadow = not Config.NoShadow[piece]
		end
		counts[piece] = (counts[piece] or 0) + 1
		if index % BATCH == 0 then
			task.wait()
		end
	end

	if data.fills then
		local fillFolder = folder("Fills", model)
		for _, item in data.fills do
			local holder = Instance.new("Part")
			holder.Name = "Fill"
			holder.Anchored = true
			holder.CanCollide = false
			holder.CanQuery = false
			holder.CanTouch = false
			holder.Transparency = 1
			holder.Size = Vector3.new(0.4, 0.4, 0.4)
			holder.CFrame = origin * CFrame.new(item.pos[1], item.pos[3], -item.pos[2])
			local light = Instance.new("PointLight")
			light.Color = Config.Fill.LightColor
			light.Brightness = Config.Fill.Brightness
			light.Range = Config.Fill.Range
			light.Shadows = false
			light.Parent = holder
			holder.Parent = fillFolder
		end
	end

	model.Parent = parent or workspace
	return model, counts
end

-- Paves the ground round a building: every cell from `margin` cells outside its footprint that the
-- building does not pave itself. `size` is the footprint in studs (east, south).
function BuildingBuilder.pave(model: Model, origin: CFrame, margin: number)
	local data = BuildingData[model:GetAttribute("Building") :: string]
	local cell = Config.Cell
	local template = meshes("ground"):FindFirstChild("Whole") :: BasePart
	local yard = folder("Yard", model)
	local own: { [string]: boolean } = {}
	for _, item: Placement in data.placements do
		if item.piece == "ground" then
			own[`{math.floor(item.pos[1] / cell)}:{math.floor(-item.pos[2] / cell)}`] = true
		end
	end
	local columns, rows = data.size[1] / cell, data.size[2] / cell
	for c = -margin, columns + margin - 1 do
		for r = -margin, rows + margin - 1 do
			if not own[`{c}:{r}`] then
				copy(template, origin * CFrame.new((c + 0.5) * cell, Config.PavingY, (r + 0.5) * cell), "ground", yard)
			end
		end
	end
end

return BuildingBuilder

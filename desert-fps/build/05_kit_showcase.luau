-- Stands the imported kit next to the map: Workspace.KitShowcase. It is both the look check and the firing range.
-- Run in Studio in edit mode, after 01_install_modules.luau, 03_lighting.luau and 04_import_meshes.luau.
-- Safe to re-run.
-- The pieces are laid out like the "whole" scene in assets/preview.py and the group is turned so the sun
-- falls on it from the same side as in that render (assets/out/compare.png). Walls, door, crates and barrels
-- are placed through Breakable, so they break in a playtest. Two default characters stand by the plain wall
-- and in the doorway for scale, the weapons sit in the air to the right, and players spawn on the pad in
-- front (DevConfig.SpawnPath).
-- Further right stand the rest of the kit: one room built from the structural pieces (the "building" scene
-- in assets/preview.py), then the cover pieces and props in a row (its "props" scene).
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local Meshes = ServerStorage.DesertFps.Meshes
local Breakable = require(ServerStorage.DesertFps.Destruction.Breakable)
local BreakData = require(ServerStorage.DesertFps.Assets.BreakData)

-- Outside the map (it spans 112 studs each way from the origin), just above the baseplate.
local POSITION = Vector3.new(0, 0.05, 180)
-- Towards the sun in assets/preview.py, in Roblox axes with the walls facing +Z.
local PREVIEW_SUN = Vector3.new(-0.485, 0.616, 0.621)
-- piece, position, turn about Y in degrees: preview.py's "whole" scene, (x, y, z) there is (x, z, -y) here
local LAYOUT = {
	{ "wall_plain", Vector3.new(-8, 0, 0), 0 },
	{ "wall_window", Vector3.new(0, 0, 0), 0 },
	{ "wall_door", Vector3.new(8, 0, 0), 0 },
	{ "door", Vector3.new(7.65, 0, 1.15), -42 },
	{ "crate", Vector3.new(-6.5, 0, 4.2), 18 },
	{ "barrel", Vector3.new(-3.2, 0, 3.4), 0 },
	{ "barrel", Vector3.new(-9.6, 0, 3.0), 40 },
	{ "crate", Vector3.new(2.6, 0, 4.6), -12 },
	-- more to shoot at
	{ "wall_plain", Vector3.new(-22, 0, 0), 0 },
	{ "crate", Vector3.new(-20, 0, 5), 30 },
	{ "barrel", Vector3.new(-24, 0, 4), 0 },
	{ "barrel", Vector3.new(12, 0, 5.5), 15 },
	{ "rifle", Vector3.new(17, 4, 0.5), 0 },
	{ "pistol", Vector3.new(21.5, 4, 0.5), 0 },
	{ "knife", Vector3.new(17, 2, 0.5), 0 },
	{ "smoke", Vector3.new(21.5, 2, 0.5), 0 },
}

-- Four wall pieces round one grid cell, fronts facing out: south (towards the spawn), east, north, west.
local function cell(pieces: { string }, centre: Vector3)
	local sides = { { Vector3.new(0, 0, 4), 0 }, { Vector3.new(4, 0, 0), 90 }, { Vector3.new(0, 0, -4), 180 },
		{ Vector3.new(-4, 0, 0), -90 } }
	for index, piece in pieces do
		table.insert(LAYOUT, { piece, centre + sides[index][1], sides[index][2] })
	end
end

-- One room built from the structural pieces, to see that they fit each other.
local ROOM = Vector3.new(46, 0, 0)
local ROOF_TOP = 12 -- one story
for i = -2, 2 do
	for j = -2, 1 do
		table.insert(LAYOUT, { "ground", ROOM + Vector3.new(8 * i, 0.01 - 0.5, 8 * j), 0 })
	end
end
cell({ "wall_door", "wall_window", "wall_plain", "wall_window" }, ROOM)
cell({ "parapet_crenel", "parapet_plain", "parapet_plain", "parapet_crenel" }, ROOM + Vector3.new(0, ROOF_TOP, 0))
for _, x in { -4, 4 } do
	for _, z in { -4, 4 } do
		table.insert(LAYOUT, { "corner", ROOM + Vector3.new(x, 0, z), 0 })
		table.insert(LAYOUT, { "parapet_corner", ROOM + Vector3.new(x, ROOF_TOP, z), 0 })
	end
end
for _, entry in {
	{ "roof", Vector3.new(0, ROOF_TOP - 1, 0), 0 }, -- its top stands 0.06 above the wall tops it covers
	{ "stairs", Vector3.new(8, 0, 0), 90 },
	{ "ladder", Vector3.new(-4.9, 0, -2.4), -90 },
	{ "pillar", Vector3.new(-12, 0, 9), 0 },
	{ "pillar", Vector3.new(-12, 0, -1), 0 },
	{ "plank", Vector3.new(-12, ROOF_TOP, 4), 90 },
} do
	table.insert(LAYOUT, { entry[1], ROOM + entry[2], entry[3] })
end

-- The cover pieces and props in a row.
local PROPS = Vector3.new(84, 0, 0)
for _, entry in {
	{ "stall", Vector3.new(-11, 0, 0), 0 },
	{ "wall_plain", Vector3.new(-2.5, 0, -2.5), 0 },
	{ "awning", Vector3.new(-2.5, 3.5, -2), 0 }, -- on the face of that wall, above its plinth
	{ "cloth", Vector3.new(6, 0, -1), 0 },
	{ "well", Vector3.new(14.5, 0, 0), 0 },
	{ "sacks", Vector3.new(-9, 0, 7), 0 },
	{ "pot_tall", Vector3.new(-3.5, 0, 6), 0 },
	{ "pot_round", Vector3.new(-0.5, 0, 6.5), 0 },
	{ "vase", Vector3.new(2, 0, 6), 0 },
} do
	table.insert(LAYOUT, { entry[1], PROPS + entry[2], entry[3] })
end
-- Where the characters stand: beside the plain wall, and in the doorway (4 x 7.6 studs).
local CHARACTERS = { Vector3.new(-13.5, 0, 0.5), Vector3.new(8.05, 0, 0) }
local GROUND = { Size = Vector3.new(146, 1, 44), Centre = Vector3.new(37, 0, 6), Color = Color3.fromRGB(237, 191, 170) }
local SPAWN = { Position = Vector3.new(0, 0, 20), Size = Vector3.new(6, 0.2, 6) }
local SKIN = Color3.fromRGB(163, 162, 165)

local function heading(v: Vector3): number
	return math.atan2(v.X, v.Z)
end

local old = workspace:FindFirstChild("KitShowcase")
if old then
	old:Destroy()
end

local sun = Lighting:GetSunDirection()
local origin = CFrame.new(POSITION) * CFrame.Angles(0, heading(sun) - heading(PREVIEW_SUN), 0)

local showcase = Instance.new("Model")
showcase.Name = "KitShowcase"
showcase.WorldPivot = origin

local ground = Instance.new("Part")
ground.Name = "Ground"
ground.Anchored = true
ground.Size = GROUND.Size
ground.Color = GROUND.Color
ground.Material = Enum.Material.SmoothPlastic
ground.TopSurface = Enum.SurfaceType.Smooth
ground.CFrame = origin * CFrame.new(GROUND.Centre - Vector3.new(0, GROUND.Size.Y / 2, 0))
ground.Parent = showcase

-- Faces the walls (a SpawnLocation's front is -Z, and so is the way to the walls from here).
local spawn = Instance.new("SpawnLocation")
spawn.Name = "Spawn"
spawn.Anchored = true
spawn.Neutral = true
spawn.Duration = 0
spawn.Size = SPAWN.Size
spawn.Color = GROUND.Color
spawn.Material = Enum.Material.SmoothPlastic
spawn.TopSurface = Enum.SurfaceType.Smooth
spawn.CFrame = origin * CFrame.new(SPAWN.Position + Vector3.new(0, SPAWN.Size.Y / 2, 0))
spawn.Parent = showcase

for _, entry in LAYOUT do
	local piece, position, turn = entry[1], entry[2], entry[3]
	local at = origin * CFrame.new(position) * CFrame.Angles(0, math.rad(turn), 0)
	if BreakData[piece] then
		Breakable.place(piece, at, showcase)
	else
		local part = Meshes[piece].Whole:Clone()
		part.Name = piece
		part.CFrame = at * CFrame.new(part:GetAttribute("Offset"))
		part.Parent = showcase
	end
end

local description = Instance.new("HumanoidDescription")
for _, limb in { "Head", "Torso", "LeftArm", "RightArm", "LeftLeg", "RightLeg" } do
	(description :: any)[limb .. "Color"] = SKIN
end
for index, position in CHARACTERS do
	local character = Players:CreateHumanoidModelFromDescription(description, Enum.HumanoidRigType.R15)
	character.Name = "Character" .. index
	for _, part in character:GetDescendants() do
		if part:IsA("BasePart") then
			part.Anchored = true
		end
	end
	character.Parent = showcase
	-- Face away from the walls, feet on the ground.
	character:PivotTo(origin * CFrame.new(position) * CFrame.Angles(0, math.pi, 0))
	local box, size = character:GetBoundingBox()
	local feet = origin:PointToObjectSpace(box.Position).Y - size.Y / 2
	character:PivotTo(character:GetPivot() + origin.UpVector * -feet)
end

showcase.Parent = workspace
game:GetService("ChangeHistoryService"):SetWaypoint("Build kit showcase")
return { origin = tostring(origin), children = #showcase:GetChildren() }

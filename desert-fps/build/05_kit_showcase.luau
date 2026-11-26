-- Stands the imported kit next to the map for checking scale and look: Workspace.KitShowcase.
-- Run in Studio in edit mode, after 03_lighting.luau and 04_import_meshes.luau. Safe to re-run.
-- The pieces are laid out like the "whole" scene in assets/preview.py and the group is turned so the sun
-- falls on it from the same side as in that render (assets/out/compare.png).
-- Two default characters stand by the plain wall and in the doorway, and the weapons sit on a shelf.
local Lighting = game:GetService("Lighting")
local Players = game:GetService("Players")
local ServerStorage = game:GetService("ServerStorage")

local Meshes = ServerStorage.DesertFps.Meshes

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
	{ "rifle", Vector3.new(17, 4, 0.5), 0 },
	{ "pistol", Vector3.new(21.5, 4, 0.5), 0 },
	{ "knife", Vector3.new(17, 2, 0.5), 0 },
	{ "smoke", Vector3.new(21.5, 2, 0.5), 0 },
}
-- Where the characters stand: beside the plain wall, and in the doorway (4 x 7.6 studs).
local CHARACTERS = { Vector3.new(-13.5, 0, 0.5), Vector3.new(8.05, 0, 0) }
local GROUND = { Size = Vector3.new(64, 1, 40), Color = Color3.fromRGB(237, 191, 170) }
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
ground.CFrame = origin * CFrame.new(4, -GROUND.Size.Y / 2, 2)
ground.Parent = showcase

for _, entry in LAYOUT do
	local piece, position, turn = entry[1], entry[2], entry[3]
	local part = Meshes[piece].Whole:Clone()
	part.Name = piece
	part.CFrame = origin
		* CFrame.new(position)
		* CFrame.Angles(0, math.rad(turn), 0)
		* CFrame.new(part:GetAttribute("Offset"))
	part.Parent = showcase
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
return { origin = tostring(origin), parts = #showcase:GetChildren() }

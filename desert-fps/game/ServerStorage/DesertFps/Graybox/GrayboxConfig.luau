--!strict
-- Every number the graybox builder uses. Cell and story sizes come from the plan itself.

local function gray(v: number): Color3
	return Color3.fromRGB(v, v, v)
end

return {
	-- Centre of the zone, at the top of its floor. The floor slab sits on the template baseplate (top at Y = 0).
	Origin = CFrame.new(0, 1, 0),

	FloorThickness = 1,
	RoofThickness = 1,
	WallThickness = 1,

	-- Openings are centred on their cell edge. Sizes match the kit pieces (wall_door, wall_window).
	Door = { Width = 4, Height = 7.6 },
	Window = { Width = 4, Sill = 3, Head = 7.5, PaneThickness = 0.2 },

	-- Footprint (X, Z) and height (Y) in studs.
	LowCover = Vector3.new(6, 3.5, 6),
	HighCover = Vector3.new(7, 8, 7),
	InteriorLowCover = Vector3.new(6, 3, 6),
	InteriorHighCover = Vector3.new(6, 8, 6),
	InteriorPillar = Vector3.new(4, 0, 4), -- height is the room's clear height
	Pillar = Vector3.new(5, 12, 5),
	Water = { Height = 3 },
	ShallowWater = { Height = 0.2, SlowFactor = 1.6 },
	Cloth = { Height = 10, Thickness = 0.2, Clearance = 1 },
	Tree = { Trunk = Vector3.new(3, 12, 3), CanopyDiameter = 12 },
	Ladder = { Width = 2 },
	Barrier = { Height = 24 },
	Spawn = { Size = Vector3.new(6, 0.2, 6) },

	Styles = {
		Floor = { Color = gray(196) },
		Solid1 = { Color = gray(168) },
		Solid2 = { Color = gray(146) },
		Solid3 = { Color = gray(124) },
		Roof = { Color = gray(178) },
		Wall = { Color = gray(206) },
		WindowPane = { Color = Color3.fromRGB(150, 200, 210), Transparency = 0.7 },
		LowCover = { Color = Color3.fromRGB(150, 138, 120) },
		HighCover = { Color = Color3.fromRGB(112, 100, 86) },
		Pillar = { Color = gray(110) },
		Water = { Color = Color3.fromRGB(96, 160, 165) },
		ShallowWater = { Color = Color3.fromRGB(130, 195, 195), Transparency = 0.4, CanCollide = false },
		Cloth = { Color = Color3.fromRGB(170, 90, 140), Transparency = 0.15, CanCollide = false },
		TreeTrunk = { Color = Color3.fromRGB(110, 90, 70) },
		TreeCanopy = { Color = Color3.fromRGB(120, 150, 90), CanCollide = false },
		Ladder = { Color = Color3.fromRGB(120, 85, 55) },
		Stairs = { Color = gray(186) },
		Plank = { Color = Color3.fromRGB(150, 115, 80) },
		Barrier = { Color = Color3.fromRGB(205, 70, 60), Transparency = 0.5 },
		SpawnA = { Color = Color3.fromRGB(58, 123, 213), CanCollide = false },
		SpawnB = { Color = Color3.fromRGB(213, 85, 58), CanCollide = false },
	},
}

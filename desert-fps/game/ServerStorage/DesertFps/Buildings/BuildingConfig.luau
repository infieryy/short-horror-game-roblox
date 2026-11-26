--!strict
return {
	-- Studs per grid cell, as in the plan and the building recipes.
	Cell = 8,
	-- Where a paving piece's origin sits so that its top is just above street level (as in the recipes).
	PavingY = -0.49,

	-- Lanterns really light up: the glass glows and carries a point light.
	Lamp = {
		Pieces = { lantern = true, lantern_wall = true },
		GlassColor = Color3.fromRGB(255, 206, 122),
		LightColor = Color3.fromRGB(255, 190, 120),
		Brightness = 0.7,
		Range = 20,
		Shadows = true,
	},
}

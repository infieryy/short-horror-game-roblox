--!strict
return {
	-- Studs per grid cell, as in the plan and the building recipes.
	Cell = 8,
	-- Where a paving piece's origin sits so that its top is just above street level (as in the recipes).
	PavingY = -0.49,

	-- Lanterns really light up: the glass glows and carries a point light.
	-- The lamps are what makes a room warm. Roblox's shade light leaks through walls and roofs this thin, so
	-- without them a room takes the violet of the shade outside (Lighting.OutdoorAmbient), not Lighting.Ambient.
	-- On low graphics the lamps cast no shadows and shine through walls, so every lamp in reach adds up.
	-- Brightness and Range are set for that case: a lamp lights its own cell and little more.
	Lamp = {
		Pieces = { lantern = true, lantern_wall = true },
		GlassColor = Color3.fromRGB(255, 186, 92),
		LightColor = Color3.fromRGB(255, 176, 122),
		Brightness = 0.62,
		Range = 13,
		-- A lamp that casts shadows is the dearest thing in a room to draw. Hanging lanterns cast them; wall
		-- lanterns do not (most hang outside in sunlight, where their shadows cannot be seen anyway).
		Shadows = { lantern = true, lantern_wall = false },
	},
	-- Pieces too small or too flat for their shadow to be missed. They cast none.
	NoShadow = { rug = true, banner = true, sign_tea = true, tea_table = true, shelf = true, vase = true, pot_round = true },
	-- A fill is a soft light with no lamp to see, where a recipe asks for one (daylight under a dome).
	Fill = {
		LightColor = Color3.fromRGB(255, 176, 122),
		Brightness = 0.5,
		Range = 22,
	},
}

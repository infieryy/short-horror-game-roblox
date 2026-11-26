--!strict
-- Which kit piece stands where when the town is built from the plan. Sizes of the pieces themselves
-- live in assets/config.py.
return {
	-- The middle of the town at street level: the top of the paving. Walls stand on this.
	Origin = CFrame.new(0, 0.5, 0),
	-- The paving piece's top is this far above its own origin.
	PavingThickness = 0.5,
	-- A roof slab's origin sits this far below the top of the story it closes.
	RoofDrop = 1,
	-- A plank bridge's walking surface is this far above its own origin.
	PlankRise = 0.75,

	Wall = {
		Ground = "wall_plain",
		Door = "wall_door",
		Window = "wall_window",
		Upper = "wall_upper",
		UpperWindow = "wall_upper_window",
		-- One upper wall in this many, facing a street, gets a window. The town wall gets none.
		UpperWindowOneIn = 4,
	},
	Corner = { Ground = "corner", Upper = "corner_upper" },
	-- Parapet by the height of the roof it stands on, in stories.
	Parapet = { [1] = "parapet_plain", [2] = "parapet_crenel", [3] = "parapet_crenel", Corner = "parapet_corner" },

	-- Districts under a ceiling, and how many stories up it is (the Cistern is the underground zone).
	Covered = { cistern = 1 },
	-- A warm lamp under the ceiling, one every this many cells each way.
	CoveredLamp = { Every = 4, Range = 30, Brightness = 1.6, Color = Color3.fromRGB(255, 196, 140) },

	-- Cover. Each entry is one way to fill a cell: pieces with their place in the cell (studs from its
	-- middle) and their turn in degrees. Cells pick one by position, so the layout is the same every build.
	LowCover = {
		{ { "sacks", Vector3.new(0, 0, 0), 0 } },
		{ { "crate", Vector3.new(-1.6, 0, -0.5), 12 }, { "barrel", Vector3.new(1.9, 0, 0.8), 0 } },
		{ { "crate", Vector3.new(-1.6, 0, 0.5), -8 }, { "crate", Vector3.new(1.7, 0, -0.4), 20 } },
		{ { "sacks", Vector3.new(0, 0, 0), 90 } },
	},
	-- High cover has to block the view, so it is stacked above eye level.
	HighCover = {
		{
			{ "crate", Vector3.new(-1.6, 0, -1.6), 5 },
			{ "crate", Vector3.new(1.6, 0, -1.5), -7 },
			{ "crate", Vector3.new(-1.5, 0, 1.6), -4 },
			{ "crate", Vector3.new(1.6, 0, 1.6), 9 },
			{ "crate", Vector3.new(-1.4, 3.05, -1.4), 14 },
			{ "crate", Vector3.new(1.4, 3.05, 1.3), -11 },
		},
		{
			{ "crate", Vector3.new(-1.6, 0, -1.5), -6 },
			{ "crate", Vector3.new(1.6, 0, -1.6), 8 },
			{ "crate", Vector3.new(0, 3.05, -1.5), 3 },
			{ "barrel", Vector3.new(-1.7, 0, 1.6), 0 },
			{ "barrel", Vector3.new(1.5, 0, 1.7), 30 },
			{ "sacks", Vector3.new(0, 3.6, 1.6), 0 },
		},
	},
	-- Districts where high cover in the street is a market stall facing the middle of the district.
	-- A stall is open between counter and roof, so it hides less than the plan assumes.
	Stalls = { market = true },
	InteriorLowCover = {
		{ { "crate", Vector3.new(-0.9, 0, 0), 10 }, { "pot_tall", Vector3.new(1.9, 0, 0.6), 0 } },
		{ { "sacks", Vector3.new(0, 0, 0), 0 } },
		{ { "barrel", Vector3.new(-1.3, 0, 0.2), 0 }, { "pot_round", Vector3.new(1.3, 0, -0.4), 0 }, { "vase", Vector3.new(1.6, 0, 1.6), 0 } },
	},

	-- Water. A block of "w" cells is a well in a district listed under Wells, a dye vat elsewhere.
	Wells = { market = true },
	Well = "well",
	Vat = "vat",
	-- Shallow water has no kit piece: a flat sheet over the paving. Players wade through it.
	ShallowWater = { Height = 0.25, SlowFactor = 1.6, Color = Color3.fromRGB(104, 158, 146), Transparency = 0.35 },
	-- Trees have no kit piece yet: a plain trunk and crown stand in.
	Tree = {
		Trunk = Vector3.new(1.6, 9, 1.6),
		Crown = 9,
		TrunkColor = Color3.fromRGB(150, 98, 72),
		CrownColor = Color3.fromRGB(122, 140, 92),
	},

	Ladder = {
		Piece = "ladder",
		FromWall = 0.9, -- studs from the wall's centre line to the ladder
		Truss = 2, -- the climbable part: studs wide and deep, standing against the wall face
	},
	Spawn = { Size = Vector3.new(6, 0.2, 6) },
	-- Zone barriers stay open and unseen until a round closes them.
	Barrier = { Height = 24 },
}

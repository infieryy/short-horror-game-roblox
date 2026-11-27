--!strict
-- The compact town (plan v2, plan/town.py): where it stands and which of its buildings are built for real.
-- Everything else is still gray boxes.
return {
	-- The middle of the town; Y is the top of the street.
	Middle = CFrame.new(-700, 1, 0),
	-- Studs a real building's paving stands above the gray floor, so the two never show in the same plane.
	Lift = 0.02,

	-- The streets and yards are paved with kit pieces (Workspace.TownGround), so the real buildings stand on
	-- the ground they were painted for. Cells under a solid gray box are left out.
	Paving = {
		Folder = "TownGround",
		Drop = -0.49,
		-- Streets: three layouts of flagstones, mixed and turned so no pattern shows.
		Street = { "paving_a", "paving_b", "paving_c" },
		-- The Market Square is laid in brick ({ row0, column0, row1, column1 } of plan/town.py).
		Square = { Piece = "paving_bricks", Rect = { 14, 14, 25, 24 } },
		-- Open water in the plan (the cistern's overflow pool).
		Pool = "paving_pool",
		-- Sand blows against the foot of walls: against one wall face in every OneIn, picked by the cell.
		Sand = { Piece = "sand_drift", OneIn = 3, WallOut = 0.66 },
	},

	-- Buildings with a recipe (assets/buildings/<recipe>.py). Row and Column are the plan cell of the building's
	-- north-west corner, Rows and Columns its size; all four are the building's rectangle in plan/town.py.
	Buildings = {
		{ Recipe = "teahouse", Row = 7, Column = 17, Rows = 4, Columns = 4 },
		{ Recipe = "courtyard", Row = 15, Column = 3, Rows = 9, Columns = 7 },
		{ Recipe = "dyeworks", Row = 15, Column = 28, Rows = 9, Columns = 8 },
		{ Recipe = "cistern", Row = 28, Column = 17, Rows = 7, Columns = 8 },
	},
}

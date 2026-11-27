--!strict
-- The compact town (plan v2, plan/town.py): where it stands and what it stands on.
-- Which buildings it has and where is TownData, written by assets/buildings/town.py.
return {
	-- The middle of the town; Y is the top of the street.
	Middle = CFrame.new(-700, 1, 0),
	-- Studs the buildings' own paving stands above the slab under the town, so the two never show in one plane.
	Lift = 0.02,
	-- Where the buildings go, under Workspace.
	Folder = "Buildings",

	-- The streets and yards are paved with kit pieces (Workspace.TownGround).
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
		-- A wall's face stands WallOut studs out from the line between two cells.
		Sand = { Piece = "sand_drift", OneIn = 3, WallOut = 0.66 },
	},

	-- Unseen walls behind the town wall. The town wall can be shot down like everything else; these cannot.
	Edge = { Folder = "TownEdge", Thickness = 2, Height = 80 },

	-- Where a player spawns while there are no rounds (DevConfig.SpawnPath points at it): a plan cell.
	DevSpawn = { Row = 13, Column = 19 },
}

--!strict
return {
	-- Where the imported meshes live: <MeshFolder>.<piece>.Whole and <MeshFolder>.<piece>.Shards.<shard id>.
	-- A piece with no meshes there is built from gray boxes the size of each shard, so the logic can be tested.
	MeshFolder = { "ServerStorage", "DesertFps", "Meshes" },
	StandInColor = Color3.fromRGB(200, 150, 130),

	-- Walls and doors show damage before they go: once the share of health left drops to At, the piece is
	-- swapped for its shards, each pushed Shift studs and turned Tilt degrees out of place, so cracks open
	-- along the cuts. Nothing is missing until the piece crumbles.
	CrackStages = {
		{ At = 0.66, Shift = 0.05, Tilt = 1 },
		{ At = 0.33, Shift = 0.12, Tilt = 2.5 },
	},

	-- How a piece comes apart when its health runs out, by break mode.
	--   Stagger  seconds over which the shards let go, starting where the piece was hit
	--   Outward  studs per second each shard is thrown away from the middle of the piece
	--   Scatter  studs per second of random sideways push
	Crumble = {
		chunks = { Stagger = 0.45, Outward = 0, Scatter = 3 }, -- walls and doors sag and fall
		shatter = { Stagger = 0, Outward = 14, Scatter = 0 }, -- crates and barrels burst
	},
	-- Extra push on the shards nearest the hit (studs per second): along a shot, and away from a blast.
	ShotPush = 12,
	BlastPush = 30,
	-- How fast rubble spins (radians per second).
	Tumble = 5,

	-- Seconds rubble lies around, the last DebrisFade of them fading out.
	DebrisLifetime = 6,
	DebrisFade = 1,

	-- Pieces players walk up. A character cannot climb the 1.5-stud steps of the mesh itself, so the mesh
	-- does not collide and an unseen ramp of this size (wide, high, long) stands in it until the piece breaks.
	Ramps = { stairs = Vector3.new(8, 12, 8), stairs_narrow = Vector3.new(4, 12, 8) },

	-- Collision groups. Rubble does not shove players around, and shots pass through it.
	DebrisGroup = "Debris",
	CharacterGroup = "Characters",
}

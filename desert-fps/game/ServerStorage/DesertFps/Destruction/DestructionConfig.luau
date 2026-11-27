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
	-- Pieces stronger than their size says: health is multiplied by this. A house door is a thin leaf, but the
	-- plan counts a house as closed; at four times its health it takes a second and a half of rifle fire to
	-- shoot open, a third of what the wall beside it takes.
	Tough = { door2_wood = 4, door2_teal = 4 },
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
	-- Pieces players climb. A ladder's rungs are too thin to climb, so the mesh does not collide and an unseen
	-- truss of this size stands at Offset from the piece's origin until the piece breaks. The ladder stands
	-- 1.5 studs out from the wall line, so the truss fills the 2 studs between the wall line and the street.
	Climbs = { ladder = { Size = Vector3.new(2, 12, 2), Offset = Vector3.new(0, 6, -0.5) } },

	-- What holds what up (Structure). A piece stands while it rests on the ground or on a standing piece.
	-- The links are worked out from the boxes round the pieces as they are built.
	Structure = {
		-- Two pieces touch if they are no further apart than Touch. One rests on the other only if it also
		-- lies over it: by at least Overlap one way and Share the other. (A floor does not rest on the wall of
		-- the next cell by its corner, nor an upper wall on the wall of the next bay by its end.)
		Touch = 0.15,
		Overlap = 0.3,
		Share = 0.8,
		-- A piece rests on a touching piece that starts at least this much lower.
		Lower = 0.5,
		-- How far above the ground a piece may start and still stand on it.
		GroundReach = 0.6,
		-- Pieces that can hold others up, by the start of their name. (Corner posts do not: a wall or a floor
		-- with nothing but a post under it comes down.)
		Bearing = { "wall", "pillar", "floor", "roof", "parapet", "town", "stairs" },
		-- Floors and roofs also hold each other up sideways: a slab with no wall under it stands while two of
		-- the slabs beside it stand, no more than SpanReach slabs from one that rests on a wall. So the end of
		-- a house comes down when its walls go, and the middle of a hall does not.
		Spans = { "floor", "roof" },
		SpanReach = 3,
		-- Pieces fixed to a wall instead of standing: they stay while any bearing piece they touch stays.
		-- Looked up before Hangs ("lantern_wall" is fixed, "lantern" hangs). A corner post goes with its walls.
		Fixed = { "door", "shelf", "sign", "banner", "lantern_wall", "spout", "bougainvillea", "awning", "cloth", "corner" },
		-- Pieces that hang: held by a bearing piece that reaches at least as high as they do.
		Hangs = { "lantern" },
		-- The ground itself. It is not part of any structure.
		Ground = { "paving", "sand", "ground" },
		-- Loose pieces a shot does not knock down.
		Unshakable = { "rug" },
		-- How fast a collapse runs through a building from the piece that went (studs per second).
		Speed = 45,
	},

	-- Collision groups. Rubble does not shove players around, and shots pass through it.
	DebrisGroup = "Debris",
	CharacterGroup = "Characters",
}

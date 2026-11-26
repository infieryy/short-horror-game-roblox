--!strict
return {
	-- Where the imported meshes live: <MeshFolder>.<piece>.Whole and <MeshFolder>.<piece>.Shards.<shard id>.
	-- A piece with no meshes there is built from gray boxes the size of each shard, so the logic can be tested.
	MeshFolder = { "ServerStorage", "DesertFps", "Meshes" },

	-- Seconds a fallen shard lies around before it is removed.
	DebrisLifetime = 8,

	StandInColor = Color3.fromRGB(200, 150, 130),
}

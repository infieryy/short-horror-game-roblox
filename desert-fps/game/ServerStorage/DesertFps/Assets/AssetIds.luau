--!strict
-- Roblox asset ids of the uploaded kit, one entry per piece in assets/out.
--   Model    <piece>.bundle.fbx: the whole mesh, the low-detail mesh and every shard or part
--   Texture  <piece>.png: the painted colour map all of those meshes share
-- build/04_import_meshes.luau turns these into ServerStorage.DesertFps.Meshes.
return {
	wall_plain = { Model = 135688760968419, Texture = 138862098007028 },
	wall_window = { Model = 84401295749564, Texture = 75786669681463 },
	wall_door = { Model = 134685181880905, Texture = 96011352369868 },
	door = { Model = 79949303134565, Texture = 120854672972528 },
	crate = { Model = 120166642128370, Texture = 128550663157206 },
	barrel = { Model = 101362585656532, Texture = 127482096828316 },
	rifle = { Model = 118729713583609, Texture = 98441666077201 },
	pistol = { Model = 87247004083333, Texture = 102072335700837 },
	knife = { Model = 102511369777617, Texture = 76665044243244 },
	smoke = { Model = 70814577468884, Texture = 135660649189835 },
}
